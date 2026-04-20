from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    api_prefix: str
    api_key: str
    llm_mode: str
    job_store_backend: str
    database_url: str
    ollama_url: str
    ollama_model: str
    request_timeout_seconds: int
    knowledge_limit: int
    hard_timeout_seconds: int
    max_answer_length: int
    max_session_items: int
    data_dir: Path
    prompt_path: Path
    db_schema_path: Path
    demo_cases_path: Path
    demo_template_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name="Interview Coach Analysis Module",
        api_prefix="/assessment/v1",
        api_key=os.getenv("ANALYSIS_API_KEY", "demo-api-key"),
        llm_mode=os.getenv("ANALYSIS_LLM_MODE", "mock").strip().lower(),
        job_store_backend=os.getenv("ANALYSIS_JOB_STORE_BACKEND", "memory").strip().lower(),
        database_url=os.getenv(
            "ANALYSIS_DATABASE_URL",
            "postgresql://analysis:analysis@localhost:5432/analysis_module",
        ),
        ollama_url=os.getenv("ANALYSIS_OLLAMA_URL", "http://localhost:11434/api/generate"),
        ollama_model=os.getenv("ANALYSIS_OLLAMA_MODEL", "qwen2.5:3b"),
        request_timeout_seconds=int(os.getenv("ANALYSIS_REQUEST_TIMEOUT_SECONDS", "300")),
        knowledge_limit=int(os.getenv("ANALYSIS_KNOWLEDGE_LIMIT", "1")),
        hard_timeout_seconds=int(os.getenv("ANALYSIS_HARD_TIMEOUT_SECONDS", "30")),
        max_answer_length=int(os.getenv("ANALYSIS_MAX_ANSWER_LENGTH", "4000")),
        max_session_items=int(os.getenv("ANALYSIS_MAX_SESSION_ITEMS", "20")),
        data_dir=PACKAGE_DIR / "data",
        prompt_path=PACKAGE_DIR / "prompts" / "report_system_prompt.txt",
        db_schema_path=PACKAGE_DIR / "db" / "schema.sql",
        demo_cases_path=PACKAGE_DIR / "demo" / "demo_cases.json",
        demo_template_path=PACKAGE_DIR / "demo" / "demo.html",
    )