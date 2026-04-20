from __future__ import annotations

from fastapi import APIRouter, Depends

from interview_analysis.api.dependencies import get_service, verify_api_key
from interview_analysis.core.config import get_settings
from interview_analysis.schemas.api import HealthResponsePayload


router = APIRouter()


@router.get('/health', response_model=HealthResponsePayload)
def health(service=Depends(get_service)) -> dict:
    settings = get_settings()
    return {
        'status': 'ok',
        'service': settings.app_name,
        'llm_mode': settings.llm_mode,
        'llm_model': settings.ollama_model if settings.llm_mode == 'ollama' else 'mock-heuristic-v1',
        'api_prefix': settings.api_prefix,
        'job_store': service.health_snapshot(),
    }


@router.get('/metrics')
def metrics(
    _: None = Depends(verify_api_key),
    service=Depends(get_service),
) -> dict:
    return {
        'status': 'ok',
        'metrics': service.metrics_snapshot(),
        'job_store': service.health_snapshot(),
    }