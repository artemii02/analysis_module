from __future__ import annotations

from fastapi.testclient import TestClient

from interview_analysis.main import app


API_HEADERS = {'X-API-Key': 'demo-api-key'}


def test_demo_page_is_available() -> None:
    client = TestClient(app)
    response = client.get('/demo')

    assert response.status_code == 200
    assert 'id="runButton"' in response.text
    assert 'window.__DEMO_CONFIG__ = {' in response.text
    assert '__DEMO_CONFIG_JSON__' not in response.text
    assert 'function resetReportView()' in response.text
    assert '[hidden] { display: none !important; }' in response.text
    assert 'model_version ||' in response.text
    assert 'questionsUrl' in response.text
    assert 'questionProfiles' in response.text
    assert 'Raw JSON' not in response.text
    assert 'feedback' not in response.text
    assert '<h2>JSON-' in response.text
    assert 'job ${escapeHtml' not in response.text


def test_demo_cases_endpoint_returns_seed_cases() -> None:
    client = TestClient(app)
    response = client.get('/demo/cases')

    payload = response.json()
    assert response.status_code == 200
    assert len(payload) >= 3
    assert any(item['case_id'] == 'backend_junior_good' for item in payload)


def test_question_bank_endpoint_returns_backend_junior_questions() -> None:
    client = TestClient(app)
    response = client.get(
        '/assessment/v1/questions?specialization=backend&grade=junior&limit=10',
        headers=API_HEADERS,
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload['status'] == 'ok'
    assert payload['specialization'] == 'backend'
    assert payload['grade'] == 'junior'
    assert payload['count'] == 10
    assert len(payload['items']) == 10
    assert payload['items'][0]['topic_label']


def test_health_endpoint_exposes_llm_runtime() -> None:
    client = TestClient(app)
    response = client.get('/assessment/v1/health')

    payload = response.json()
    assert response.status_code == 200
    assert payload['status'] == 'ok'
    assert 'llm_mode' in payload
    assert 'llm_model' in payload
