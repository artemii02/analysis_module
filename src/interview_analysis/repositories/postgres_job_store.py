from __future__ import annotations

from pathlib import Path
from threading import Lock
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from interview_analysis.core.serialization import report_from_primitive, to_primitive, utcnow_iso
from interview_analysis.exceptions import ConflictError, IntegrationError, JobNotFoundError
from interview_analysis.models import AssessmentJob, AssessmentReport, JobStatus


class PostgresAssessmentJobStore:
    backend_name = "postgres"

    def __init__(self, dsn: str, schema_path: Path) -> None:
        self.dsn = dsn
        self.schema_sql = schema_path.read_text(encoding="utf-8")
        self._init_lock = Lock()
        self._initialized = False
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with self._init_lock:
            if self._initialized:
                return
            try:
                with psycopg.connect(self.dsn, autocommit=True) as connection:
                    for statement in self.schema_sql.split(";"):
                        statement = statement.strip()
                        if statement:
                            connection.execute(statement)
            except psycopg.Error as exc:
                raise IntegrationError(
                    "Failed to initialize PostgreSQL schema.",
                    code="DATABASE_INIT_ERROR",
                    details={"reason": str(exc)},
                ) from exc
            self._initialized = True

    def register(self, request_id: str, session_id: str, fingerprint: str) -> tuple[AssessmentJob, bool]:
        now = utcnow_iso()
        generated_job_id = str(uuid4())
        with self._connect() as connection:
            inserted = connection.execute(
                """
                INSERT INTO assessment_jobs (
                    job_id, request_id, session_id, status, fingerprint, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (request_id) DO NOTHING
                RETURNING *
                """,
                (
                    generated_job_id,
                    request_id,
                    session_id,
                    JobStatus.CREATED.value,
                    fingerprint,
                    now,
                    now,
                ),
            ).fetchone()
            if inserted is not None:
                connection.commit()
                return self._row_to_job(inserted), True

            existing = connection.execute(
                "SELECT * FROM assessment_jobs WHERE request_id = %s",
                (request_id,),
            ).fetchone()
            connection.commit()

        if existing is None:
            raise IntegrationError(
                "Failed to register assessment job in PostgreSQL.",
                code="DATABASE_WRITE_ERROR",
            )
        if existing["fingerprint"] != fingerprint:
            raise ConflictError(
                "The same request_id was already used with a different payload.",
                details={"request_id": request_id, "job_id": existing["job_id"]},
            )
        return self._row_to_job(existing), False

    def get(self, job_id: str) -> AssessmentJob:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM assessment_jobs WHERE job_id = %s",
                (job_id,),
            ).fetchone()
            connection.commit()
        if row is None:
            raise JobNotFoundError(job_id)
        return self._row_to_job(row)

    def mark_processing(self, job_id: str) -> AssessmentJob:
        return self._update_job(
            job_id,
            status=JobStatus.PROCESSING.value,
            error_code=None,
            error_message=None,
        )

    def mark_ready(self, job_id: str, report: AssessmentReport) -> AssessmentJob:
        return self._update_job(
            job_id,
            status=JobStatus.READY.value,
            error_code=None,
            error_message=None,
            report_json=Jsonb(to_primitive(report)),
        )

    def mark_error(self, job_id: str, error_code: str, error_message: str) -> AssessmentJob:
        return self._update_job(
            job_id,
            status=JobStatus.ERROR.value,
            error_code=error_code,
            error_message=error_message,
        )

    def healthcheck(self) -> dict[str, str]:
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1")
                connection.commit()
        except psycopg.Error as exc:
            raise IntegrationError(
                "PostgreSQL healthcheck failed.",
                code="DATABASE_UNAVAILABLE",
                details={"reason": str(exc)},
            ) from exc
        return {
            "backend": self.backend_name,
            "status": "ok",
        }

    def _update_job(
        self,
        job_id: str,
        status: str,
        error_code: str | None,
        error_message: str | None,
        report_json: Jsonb | None = None,
    ) -> AssessmentJob:
        now = utcnow_iso()
        with self._connect() as connection:
            row = connection.execute(
                """
                UPDATE assessment_jobs
                   SET status = %s,
                       updated_at = %s,
                       error_code = %s,
                       error_message = %s,
                       report_json = COALESCE(%s, report_json)
                 WHERE job_id = %s
             RETURNING *
                """,
                (status, now, error_code, error_message, report_json, job_id),
            ).fetchone()
            connection.commit()
        if row is None:
            raise JobNotFoundError(job_id)
        return self._row_to_job(row)

    def _connect(self):
        self.ensure_schema()
        try:
            return psycopg.connect(self.dsn, row_factory=dict_row)
        except psycopg.Error as exc:
            raise IntegrationError(
                "Cannot connect to PostgreSQL.",
                code="DATABASE_UNAVAILABLE",
                details={"reason": str(exc)},
            ) from exc

    def _row_to_job(self, row: dict) -> AssessmentJob:
        raw_report = row.get("report_json")
        report = report_from_primitive(raw_report) if raw_report is not None else None
        return AssessmentJob(
            job_id=row["job_id"],
            request_id=row["request_id"],
            session_id=row["session_id"],
            status=JobStatus(row["status"]),
            fingerprint=row["fingerprint"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_code=row.get("error_code"),
            error_message=row.get("error_message"),
            report=report,
        )