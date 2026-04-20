from __future__ import annotations

from threading import Lock
from uuid import uuid4

from interview_analysis.core.serialization import utcnow_iso
from interview_analysis.exceptions import ConflictError, JobNotFoundError
from interview_analysis.models import AssessmentJob, AssessmentReport, JobStatus


class InMemoryAssessmentJobStore:
    backend_name = "memory"

    def __init__(self) -> None:
        self._jobs_by_id: dict[str, AssessmentJob] = {}
        self._job_id_by_request_id: dict[str, str] = {}
        self._lock = Lock()

    def register(self, request_id: str, session_id: str, fingerprint: str) -> tuple[AssessmentJob, bool]:
        with self._lock:
            existing_job_id = self._job_id_by_request_id.get(request_id)
            if existing_job_id is not None:
                job = self._jobs_by_id[existing_job_id]
                if job.fingerprint != fingerprint:
                    raise ConflictError(
                        "The same request_id was already used with a different payload.",
                        details={"request_id": request_id, "job_id": job.job_id},
                    )
                return job, False

            now = utcnow_iso()
            job = AssessmentJob(
                job_id=str(uuid4()),
                request_id=request_id,
                session_id=session_id,
                status=JobStatus.CREATED,
                fingerprint=fingerprint,
                created_at=now,
                updated_at=now,
            )
            self._jobs_by_id[job.job_id] = job
            self._job_id_by_request_id[request_id] = job.job_id
            return job, True

    def get(self, job_id: str) -> AssessmentJob:
        with self._lock:
            job = self._jobs_by_id.get(job_id)
            if job is None:
                raise JobNotFoundError(job_id)
            return job

    def mark_processing(self, job_id: str) -> AssessmentJob:
        with self._lock:
            job = self._jobs_by_id.get(job_id)
            if job is None:
                raise JobNotFoundError(job_id)
            job.status = JobStatus.PROCESSING
            job.updated_at = utcnow_iso()
            job.error_code = None
            job.error_message = None
            return job

    def mark_ready(self, job_id: str, report: AssessmentReport) -> AssessmentJob:
        with self._lock:
            job = self._jobs_by_id.get(job_id)
            if job is None:
                raise JobNotFoundError(job_id)
            job.status = JobStatus.READY
            job.report = report
            job.updated_at = utcnow_iso()
            job.error_code = None
            job.error_message = None
            return job

    def mark_error(self, job_id: str, error_code: str, error_message: str) -> AssessmentJob:
        with self._lock:
            job = self._jobs_by_id.get(job_id)
            if job is None:
                raise JobNotFoundError(job_id)
            job.status = JobStatus.ERROR
            job.updated_at = utcnow_iso()
            job.error_code = error_code
            job.error_message = error_message
            return job

    def healthcheck(self) -> dict[str, str]:
        return {
            "backend": self.backend_name,
            "status": "ok",
        }