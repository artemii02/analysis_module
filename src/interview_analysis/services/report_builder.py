from __future__ import annotations

from collections import defaultdict
import logging
from statistics import mean
from time import perf_counter

from interview_analysis.core.serialization import utcnow_iso
from interview_analysis.core.topic_catalog import topic_label
from interview_analysis.models import (
    AssessmentReport,
    QuestionFeedback,
    TopicSummary,
    VersionInfo,
)


logger = logging.getLogger(__name__)


CRITERION_GUIDANCE = {
    'correctness': 'Проверить техническую корректность формулировок и убрать неточные или спорные утверждения.',
    'completeness': 'Строить ответ полнее: дать определение, ключевые различия, ограничения и итог.',
    'clarity': 'Структурировать ответ короткими логическими блоками и явно разделять основные тезисы.',
    'practicality': 'Добавлять практический сценарий применения, ограничения и последствия выбранного решения.',
    'terminology': 'Использовать точные технические термины и корректные названия сущностей по теме.',
}


class ReportBuilder:
    def build(
        self,
        request_id: str,
        session_id: str,
        client_id: str,
        specialization: str,
        grade: str,
        feedback_items: list[QuestionFeedback],
        versions: VersionInfo,
    ) -> AssessmentReport:
        started = perf_counter()
        logger.info(
            'report.build.started request_id=%s session_id=%s items=%s specialization=%s grade=%s',
            request_id,
            session_id,
            len(feedback_items),
            specialization,
            grade,
        )
        overall_score = round(mean(item.score for item in feedback_items))
        criterion_scores = _aggregate_criterion_scores(feedback_items)
        grouped: dict[str, list[QuestionFeedback]] = defaultdict(list)
        for item in feedback_items:
            grouped[item.topic].append(item)

        topic_summaries: list[TopicSummary] = []
        for topic, items in grouped.items():
            strengths = _deduplicate(
                strength
                for item in items
                for strength in item.strengths
            )[:3]
            gaps = _deduplicate(
                gap
                for item in items
                for gap in (item.issues + item.missing_keypoints)
            )[:4]
            topic_summaries.append(
                TopicSummary(
                    topic=topic,
                    average_score=round(mean(item.score for item in items)),
                    strengths=strengths,
                    gaps=gaps,
                )
            )

        topic_summaries.sort(key=lambda item: item.average_score)
        recommendations = _build_session_recommendations(
            feedback_items=feedback_items,
            topic_summaries=topic_summaries,
            criterion_scores=criterion_scores,
            overall_score=overall_score,
        )
        weakest_topic = topic_summaries[0].topic if topic_summaries else "unknown"
        logger.info(
            'report.build.aggregates request_id=%s overall_score=%s criterion_scores=%s weakest_topics=%s recommendations=%s',
            request_id,
            overall_score,
            criterion_scores,
            [topic_label(item.topic) for item in topic_summaries[:2]],
            recommendations,
        )
        summary = (
            f"Сформирован пост-сессионный отчёт по {len(feedback_items)} вопросам. "
            f"Средний балл по сессии: {overall_score}/100. "
            f"Наибольшее внимание стоит уделить теме '{topic_label(weakest_topic)}'."
        )

        report = AssessmentReport(
            request_id=request_id,
            session_id=session_id,
            client_id=client_id,
            specialization=specialization,
            grade=grade,
            overall_score=overall_score,
            criterion_scores=criterion_scores,
            summary=summary,
            questions=feedback_items,
            topics=topic_summaries,
            recommendations=recommendations,
            versions=versions,
            generated_at=utcnow_iso(),
        )
        logger.info(
            'report.build.completed request_id=%s session_id=%s overall_score=%s topics=%s recommendations=%s duration_ms=%s',
            request_id,
            session_id,
            report.overall_score,
            len(report.topics),
            len(report.recommendations),
            _duration_ms(started),
        )
        return report


def _aggregate_criterion_scores(feedback_items: list[QuestionFeedback]) -> dict[str, int]:
    if not feedback_items:
        return {}
    criterion_names = list(feedback_items[0].criterion_scores.keys())
    return {
        criterion_name: round(mean(item.criterion_scores.get(criterion_name, 0) for item in feedback_items))
        for criterion_name in criterion_names
    }


def _build_session_recommendations(
    *,
    feedback_items: list[QuestionFeedback],
    topic_summaries: list[TopicSummary],
    criterion_scores: dict[str, int],
    overall_score: int,
) -> list[str]:
    recommendations: list[str] = []
    weakest_questions = sorted(feedback_items, key=lambda item: item.score)[:3]
    weakest_topics = topic_summaries[:2]
    weakest_criteria = sorted(criterion_scores.items(), key=lambda item: item[1])[:2]

    recommendations.append(_score_band_recommendation(overall_score, weakest_topics))

    for criterion_name, score in weakest_criteria:
        if score < 75:
            recommendations.append(CRITERION_GUIDANCE[criterion_name])

    for feedback in weakest_questions:
        recommendations.extend(feedback.recommendations[:2])
        for keypoint in feedback.missing_keypoints[:1]:
            recommendations.append(
                f"Повторить пункт '{keypoint}' на вопросе '{_short_question(feedback.question_text)}'."
            )
        for issue in feedback.issues[:1]:
            recommendations.append(issue)

    for topic in weakest_topics:
        display_topic = topic_label(topic.topic)
        if topic.average_score < 40:
            recommendations.append(
                f"Вернуться к базе по теме '{display_topic}' и заново разобрать определения, ключевые различия и типовые сценарии."
            )
        elif topic.average_score < 70:
            recommendations.append(
                f"Усилить тему '{display_topic}': довести ответы до структуры 'определение - детали - практический пример'."
            )
        else:
            recommendations.append(
                f"Для темы '{display_topic}' добавить больше граничных случаев, ограничений и практических нюансов."
            )

    return _deduplicate(recommendations)[:6]


def _score_band_recommendation(overall_score: int, weakest_topics: list[TopicSummary]) -> str:
    weakest_topic = topic_label(weakest_topics[0].topic) if weakest_topics else 'ключевым темам'
    if overall_score < 30:
        return (
            f"Сначала закрыть фундаментальные пробелы по теме '{weakest_topic}', "
            "после чего повторно пройти базовые вопросы без подсказок."
        )
    if overall_score < 60:
        return (
            f"Сфокусироваться на слабой теме '{weakest_topic}' и довести ответы до уверенного среднего уровня "
            "по полноте и корректности."
        )
    if overall_score < 80:
        return (
            f"Доработать тему '{weakest_topic}' до уверенного уровня: добавить больше точности, структуры и практических деталей."
        )
    return (
        f"Сохранить общий уровень по сессии и точечно углубить тему '{weakest_topic}' через сложные кейсы и пограничные сценарии."
    )


def _short_question(question_text: str, limit: int = 72) -> str:
    normalized = ' '.join(question_text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."


def _deduplicate(values) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result


def _duration_ms(started_at: float) -> int:
    return round((perf_counter() - started_at) * 1000)
