from __future__ import annotations

from collections import defaultdict
from statistics import mean

from interview_analysis.core.serialization import utcnow_iso
from interview_analysis.models import (
    AssessmentReport,
    QuestionFeedback,
    TopicSummary,
    VersionInfo,
)


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
        overall_score = round(mean(item.score for item in feedback_items))
        criterion_scores = _aggregate_criterion_scores(feedback_items)
        grouped: dict[str, list[QuestionFeedback]] = defaultdict(list)
        for item in feedback_items:
            grouped[item.topic].append(item)

        topic_summaries: list[TopicSummary] = []
        recommendations: list[str] = []
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
            recommendations.extend(item for feedback in items for item in feedback.recommendations)

        topic_summaries.sort(key=lambda item: item.average_score)
        recommendations = _deduplicate(recommendations)[:6]
        weakest_topic = topic_summaries[0].topic if topic_summaries else "unknown"
        summary = (
            f"Сформирован пост-сессионный отчёт по {len(feedback_items)} вопросам. "
            f"Средний балл по сессии: {overall_score}/100. "
            f"Наибольшее внимание стоит уделить теме '{weakest_topic}'."
        )

        return AssessmentReport(
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


def _aggregate_criterion_scores(feedback_items: list[QuestionFeedback]) -> dict[str, int]:
    if not feedback_items:
        return {}
    criterion_names = list(feedback_items[0].criterion_scores.keys())
    return {
        criterion_name: round(mean(item.criterion_scores.get(criterion_name, 0) for item in feedback_items))
        for criterion_name in criterion_names
    }


def _deduplicate(values) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result
