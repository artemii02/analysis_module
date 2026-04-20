from __future__ import annotations

import pytest

from interview_analysis.exceptions import ConflictError
from interview_analysis.repositories.job_store import InMemoryAssessmentJobStore



def test_job_store_is_idempotent_for_same_request_id() -> None:
    store = InMemoryAssessmentJobStore()

    first_job, created_first = store.register('req-1', 'session-1', 'fingerprint-a')
    second_job, created_second = store.register('req-1', 'session-1', 'fingerprint-a')

    assert created_first is True
    assert created_second is False
    assert first_job.job_id == second_job.job_id



def test_job_store_rejects_request_id_reuse_with_different_payload() -> None:
    store = InMemoryAssessmentJobStore()
    store.register('req-1', 'session-1', 'fingerprint-a')

    with pytest.raises(ConflictError):
        store.register('req-1', 'session-1', 'fingerprint-b')
