from __future__ import annotations

from pathlib import Path

from interview_analysis.core.config import Settings
from interview_analysis.models import AssessmentRequest, ExecutionMode, Grade, ScenarioContext, SessionItem, Specialization
from interview_analysis.repositories.content_repository import JSONContentRepository
from interview_analysis.repositories.job_store import InMemoryAssessmentJobStore
from interview_analysis.services.analysis_pipeline import AnalysisPipeline
from interview_analysis.services.assessment_service import AssessmentService
from interview_analysis.services.llm.mock_provider import MockLLMProvider
from interview_analysis.services.metrics import MetricsRegistry
from interview_analysis.services.report_builder import ReportBuilder
from interview_analysis.services.retrieval import SimpleKnowledgeRetriever


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / 'src' / 'interview_analysis'



def build_service() -> AssessmentService:
    settings = Settings(
        app_name='Test Analysis Module',
        api_prefix='/assessment/v1',
        api_key='demo-api-key',
        llm_mode='mock',
        job_store_backend='memory',
        database_url='postgresql://analysis:analysis@localhost:5432/analysis_module',
        ollama_url='http://localhost:11434/api/generate',
        ollama_model='qwen2.5-coder:7b-instruct',
        request_timeout_seconds=30,
        knowledge_limit=3,
        hard_timeout_seconds=30,
        max_answer_length=4000,
        max_session_items=20,
        data_dir=PACKAGE_DIR / 'data',
        prompt_path=PACKAGE_DIR / 'prompts' / 'report_system_prompt.txt',
        db_schema_path=PACKAGE_DIR / 'db' / 'schema.sql',
        demo_cases_path=PACKAGE_DIR / 'demo' / 'demo_cases.json',
        demo_template_path=PACKAGE_DIR / 'demo' / 'demo.html',
    )
    repository = JSONContentRepository(settings.data_dir)
    pipeline = AnalysisPipeline(
        repository=repository,
        retriever=SimpleKnowledgeRetriever(repository, limit=3),
        llm_provider=MockLLMProvider(),
        report_builder=ReportBuilder(),
    )
    return AssessmentService(
        pipeline=pipeline,
        job_store=InMemoryAssessmentJobStore(),
        metrics=MetricsRegistry(),
        settings=settings,
    )



def test_pipeline_builds_report_from_mock_provider() -> None:
    service = build_service()
    request = AssessmentRequest(
        request_id='req-001',
        session_id='session-001',
        client_id='backend-service',
        mode=ExecutionMode.SYNC,
        scenario=ScenarioContext(
            specialization=Specialization.BACKEND,
            grade=Grade.JUNIOR,
            topics=['http_api', 'sql_performance'],
        ),
        items=[
            SessionItem(
                item_id='item-1',
                question_id='backend_junior_rest_methods',
                question_text='Чем отличаются методы GET, POST, PUT и DELETE в REST API?',
                answer_text='GET читает данные и не должен менять состояние. POST обычно создает ресурс. PUT заменяет ресурс полностью и идемпотентен. DELETE удаляет ресурс. Например, CRUD API часто строят именно так.',
            ),
            SessionItem(
                item_id='item-2',
                question_id='backend_junior_sql_index',
                question_text='Что такое индекс в SQL-базе данных и когда он помогает?',
                answer_text='Индекс — это дополнительная структура, которая ускоряет поиск по WHERE и JOIN. Он особенно полезен для часто фильтруемых полей, но требует места и замедляет INSERT и UPDATE.',
            ),
        ],
    )

    submission = service.register_request(request)
    report = service.process_sync(submission.job.job_id, request)

    assert report.overall_score >= 60
    assert set(report.criterion_scores) == {'correctness', 'completeness', 'clarity', 'practicality', 'terminology'}
    assert len(report.questions) == 2
    assert report.versions.rubric_version == 'rubrics-2026.03-demo'
    assert any(item.covered_keypoints for item in report.questions)
    assert report.recommendations



def test_pipeline_rejects_too_long_answer() -> None:
    service = build_service()
    request = AssessmentRequest(
        request_id='req-002',
        session_id='session-002',
        client_id='backend-service',
        mode=ExecutionMode.SYNC,
        scenario=ScenarioContext(
            specialization=Specialization.BACKEND,
            grade=Grade.JUNIOR,
        ),
        items=[
            SessionItem(
                item_id='item-1',
                question_id='backend_junior_rest_methods',
                question_text='Q',
                answer_text='a' * 5001,
            )
        ],
    )

    try:
        service.register_request(request)
    except Exception as exc:  # pragma: no cover - simple smoke assertion
        assert exc.__class__.__name__ == 'InvalidInputError'
    else:  # pragma: no cover
        raise AssertionError('Expected InvalidInputError for oversized answer')



def test_pipeline_rejects_more_than_twenty_items() -> None:
    service = build_service()
    items = [
        SessionItem(
            item_id=str(index),
            question_id='backend_junior_rest_methods',
            question_text='Чем отличаются методы GET, POST, PUT и DELETE в REST API?',
            answer_text='GET читает ресурс. POST создает ресурс. PUT заменяет ресурс. DELETE удаляет ресурс.',
        )
        for index in range(21)
    ]
    request = AssessmentRequest(
        request_id='req-003',
        session_id='session-003',
        client_id='backend-service',
        mode=ExecutionMode.SYNC,
        scenario=ScenarioContext(
            specialization=Specialization.BACKEND,
            grade=Grade.JUNIOR,
        ),
        items=items,
    )

    try:
        service.register_request(request)
    except Exception as exc:  # pragma: no cover - simple smoke assertion
        assert exc.__class__.__name__ == 'InvalidInputError'
    else:  # pragma: no cover
        raise AssertionError('Expected InvalidInputError for more than 20 items')