from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse

from interview_analysis.api.dependencies import get_service, verify_api_key
from interview_analysis.core.serialization import to_primitive
from interview_analysis.core.topic_catalog import topic_label
from interview_analysis.models import Grade, JobStatus, Specialization
from interview_analysis.schemas.api import (
    AssessmentRequestPayload,
    JobPayload,
    QuestionBankResponsePayload,
    ReportResponsePayload,
)


router = APIRouter()


@router.get('/questions', response_model=QuestionBankResponsePayload)
def list_questions(
    specialization: Literal['backend', 'frontend', 'devops'] = Query(default='backend'),
    grade: Literal['junior', 'middle'] = Query(default='junior'),
    limit: int = Query(default=10, ge=1, le=20),
    _: None = Depends(verify_api_key),
    service=Depends(get_service),
):
    repository = service.pipeline.repository
    items = repository.list_questions(
        Specialization(specialization),
        Grade(grade),
        limit=limit,
    )
    return {
        'status': 'ok',
        'specialization': specialization,
        'grade': grade,
        'count': len(items),
        'items': [_question_payload(item) for item in items],
    }


@router.post('/report', response_model=ReportResponsePayload | JobPayload)
def create_report(
    payload: AssessmentRequestPayload,
    background_tasks: BackgroundTasks,
    _: None = Depends(verify_api_key),
    service=Depends(get_service),
):
    request = payload.to_domain()
    submission = service.register_request(request)
    job = submission.job

    if request.mode.value == 'async':
        if job.status == JobStatus.READY and job.report is not None:
            return _report_payload(job)
        if submission.created_new or job.status == JobStatus.CREATED:
            background_tasks.add_task(service.process_async, job.job_id, request)
        return JSONResponse(status_code=202, content=_job_payload(job))

    report = service.process_sync(job.job_id, request)
    job = service.get_job(job.job_id)
    return _report_payload(job, report)


@router.get('/report/{job_id}/status', response_model=JobPayload)
def get_report_status(
    job_id: str,
    _: None = Depends(verify_api_key),
    service=Depends(get_service),
):
    job = service.get_job(job_id)
    return _job_payload(job)


@router.get('/report/{job_id}', response_model=ReportResponsePayload)
def get_report(
    job_id: str,
    _: None = Depends(verify_api_key),
    service=Depends(get_service),
):
    report = service.get_report(job_id)
    job = service.get_job(job_id)
    return _report_payload(job, report)



def _question_payload(question) -> dict:
    return {
        'question_id': question.question_id,
        'specialization': question.specialization.value,
        'grade': question.grade.value,
        'topic_code': question.topic,
        'topic_label': topic_label(question.topic),
        'question_text': question.question_text,
        'tags': question.tags,
        'version': question.version,
    }



def _job_payload(job) -> dict:
    return {
        'status': job.status.value,
        'job_id': job.job_id,
        'request_id': job.request_id,
        'session_id': job.session_id,
        'created_at': job.created_at,
        'updated_at': job.updated_at,
        'error_code': job.error_code,
        'error_message': job.error_message,
    }



def _report_payload(job, report=None) -> dict:
    resolved_report = report or job.report
    return {
        'status': 'ready',
        'job': _job_payload(job),
        'report': to_primitive(resolved_report),
    }
