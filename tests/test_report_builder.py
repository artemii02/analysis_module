from __future__ import annotations

from interview_analysis.models import QuestionFeedback, VersionInfo
from interview_analysis.services.report_builder import ReportBuilder


def test_report_builder_personalizes_session_recommendations_by_score_band() -> None:
    builder = ReportBuilder()
    low_report = builder.build(
        request_id='req-low',
        session_id='session-low',
        client_id='client',
        specialization='backend',
        grade='junior',
        feedback_items=[
            _feedback(
                item_id='item-1',
                topic='http_api',
                score=14,
                question_text='Что такое REST и какие HTTP-методы ты используешь чаще всего?',
                missing_keypoints=['Различия между GET, POST, PUT и DELETE'],
                issues=['Ответ не раскрыл семантику HTTP-методов.'],
                recommendations=['Повторить семантику HTTP-методов и их назначение.'],
                criterion_scores={
                    'correctness': 15,
                    'completeness': 12,
                    'clarity': 20,
                    'practicality': 8,
                    'terminology': 10,
                },
            ),
            _feedback(
                item_id='item-2',
                topic='sql_performance',
                score=22,
                question_text='Когда индекс в SQL помогает, а когда мешает?',
                missing_keypoints=['Влияние индекса на INSERT и UPDATE'],
                issues=['Не объяснены минусы индексации.'],
                recommendations=['Разобрать плюсы и минусы индексов на SELECT и UPDATE.'],
                criterion_scores={
                    'correctness': 25,
                    'completeness': 20,
                    'clarity': 25,
                    'practicality': 15,
                    'terminology': 20,
                },
            ),
        ],
        versions=_versions(),
    )
    medium_report = builder.build(
        request_id='req-medium',
        session_id='session-medium',
        client_id='client',
        specialization='backend',
        grade='junior',
        feedback_items=[
            _feedback(
                item_id='item-1',
                topic='http_api',
                score=65,
                question_text='Что такое REST и какие HTTP-методы ты используешь чаще всего?',
                missing_keypoints=['Идемпотентность PUT и DELETE'],
                issues=['Не хватает пояснения по идемпотентности.'],
                recommendations=['Добавить пояснение по идемпотентности и безопасным методам.'],
                criterion_scores={
                    'correctness': 68,
                    'completeness': 60,
                    'clarity': 70,
                    'practicality': 58,
                    'terminology': 69,
                },
            ),
            _feedback(
                item_id='item-2',
                topic='sql_performance',
                score=72,
                question_text='Когда индекс в SQL помогает, а когда мешает?',
                missing_keypoints=['Селективность и составные индексы'],
                issues=['Недостаточно практических нюансов выбора индекса.'],
                recommendations=['Добавить примеры по селективности и составным индексам.'],
                criterion_scores={
                    'correctness': 74,
                    'completeness': 70,
                    'clarity': 75,
                    'practicality': 62,
                    'terminology': 72,
                },
            ),
        ],
        versions=_versions(),
    )

    assert low_report.recommendations != medium_report.recommendations
    assert any('фундаментальные пробелы' in item for item in low_report.recommendations)
    assert any('уверенного уровня' in item for item in medium_report.recommendations)
    assert any('HTTP API и REST-подход' in item for item in low_report.recommendations)
    assert any('идемпотентности' in item for item in medium_report.recommendations)


def test_report_builder_uses_human_readable_topic_in_summary() -> None:
    builder = ReportBuilder()
    report = builder.build(
        request_id='req-1',
        session_id='session-1',
        client_id='client',
        specialization='backend',
        grade='junior',
        feedback_items=[
            _feedback(
                item_id='item-1',
                topic='sql_performance',
                score=41,
                question_text='Когда индекс в SQL помогает, а когда мешает?',
                missing_keypoints=['Селективность и составные индексы'],
                issues=['Недостаточно практических нюансов выбора индекса.'],
                recommendations=['Добавить примеры по селективности и составным индексам.'],
                criterion_scores={
                    'correctness': 45,
                    'completeness': 38,
                    'clarity': 42,
                    'practicality': 36,
                    'terminology': 44,
                },
            ),
        ],
        versions=_versions(),
    )

    assert "SQL: индексы и производительность" in report.summary


def _feedback(
    *,
    item_id: str,
    topic: str,
    score: int,
    question_text: str,
    missing_keypoints: list[str],
    issues: list[str],
    recommendations: list[str],
    criterion_scores: dict[str, int],
) -> QuestionFeedback:
    return QuestionFeedback(
        item_id=item_id,
        question_id=f'q-{item_id}',
        question_text=question_text,
        topic=topic,
        score=score,
        criterion_scores=criterion_scores,
        summary='summary',
        strengths=['Кандидат корректно назвал базовые сущности.'] if score >= 60 else [],
        issues=issues,
        covered_keypoints=['Базовое определение'] if score >= 60 else [],
        missing_keypoints=missing_keypoints,
        detected_mistakes=[],
        recommendations=recommendations,
        context_snippets=[],
    )


def _versions() -> VersionInfo:
    return VersionInfo(
        model_version='hf-test-model',
        rubric_version='rubrics-test',
        kb_version='kb-test',
        questions_version='questions-test',
        prompt_version='prompt-test',
    )
