from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from interview_analysis.core.config import get_settings


router = APIRouter()


@router.get('/demo', response_class=HTMLResponse)
def demo_page() -> HTMLResponse:
    settings = get_settings()
    html_template = settings.demo_template_path.read_text(encoding='utf-8')
    config_payload = {
        'apiKey': settings.api_key,
        'reportUrl': f'{settings.api_prefix}/report',
        'questionsUrl': f'{settings.api_prefix}/questions',
        'casesUrl': '/demo/cases',
    }
    rendered = html_template.replace(
        '__DEMO_CONFIG_JSON__',
        json.dumps(config_payload, ensure_ascii=False),
    )
    return HTMLResponse(rendered)


@router.get('/demo/cases')
def demo_cases() -> list[dict]:
    settings = get_settings()
    return json.loads(settings.demo_cases_path.read_text(encoding='utf-8'))