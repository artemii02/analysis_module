from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"


class JobStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Specialization(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    DEVOPS = "devops"


class Grade(str, Enum):
    JUNIOR = "junior"
    MIDDLE = "middle"


@dataclass(slots=True)
class ScenarioContext:
    specialization: Specialization
    grade: Grade
    scenario_id: str | None = None
    topics: list[str] = field(default_factory=list)
    report_language: str = "ru"


@dataclass(slots=True)
class SessionItem:
    item_id: str
    question_id: str
    question_text: str
    answer_text: str
    asked_at: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AssessmentRequest:
    request_id: str
    session_id: str
    client_id: str
    scenario: ScenarioContext
    items: list[SessionItem]
    mode: ExecutionMode = ExecutionMode.SYNC
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RubricCriterion:
    name: str
    weight: float
    description: str


@dataclass(slots=True)
class MistakePattern:
    trigger_terms: list[str]
    message: str


@dataclass(slots=True)
class QuestionDefinition:
    question_id: str
    specialization: Specialization
    grade: Grade
    topic: str
    question_text: str
    tags: list[str]
    version: str


@dataclass(slots=True)
class RubricDefinition:
    question_id: str
    specialization: Specialization
    grade: Grade
    topic: str
    criteria: list[RubricCriterion]
    keypoints: list[str]
    recommendation_hints: list[str]
    mistake_patterns: list[MistakePattern]
    version: str


@dataclass(slots=True)
class KnowledgeChunk:
    chunk_id: str
    specialization: Specialization
    topics: list[str]
    tags: list[str]
    content: str
    source_title: str
    source_url: str
    version: str


@dataclass(slots=True)
class RetrievedKnowledgeChunk:
    chunk_id: str
    source_title: str
    source_url: str
    excerpt: str
    score: float


@dataclass(slots=True)
class QuestionAnalysisContext:
    scenario: ScenarioContext
    session_item: SessionItem
    question: QuestionDefinition
    rubric: RubricDefinition
    retrieved_chunks: list[RetrievedKnowledgeChunk]
    normalized_answer: str


@dataclass(slots=True)
class QuestionAssessment:
    score: int
    criterion_scores: dict[str, int]
    summary: str
    strengths: list[str]
    issues: list[str]
    covered_keypoints: list[str]
    missing_keypoints: list[str]
    detected_mistakes: list[str]
    recommendations: list[str]


@dataclass(slots=True)
class QuestionFeedback:
    item_id: str
    question_id: str
    question_text: str
    topic: str
    score: int
    criterion_scores: dict[str, int]
    summary: str
    strengths: list[str]
    issues: list[str]
    covered_keypoints: list[str]
    missing_keypoints: list[str]
    detected_mistakes: list[str]
    recommendations: list[str]
    context_snippets: list[RetrievedKnowledgeChunk]


@dataclass(slots=True)
class TopicSummary:
    topic: str
    average_score: int
    strengths: list[str]
    gaps: list[str]


@dataclass(slots=True)
class VersionInfo:
    model_version: str
    rubric_version: str
    kb_version: str
    questions_version: str
    prompt_version: str


@dataclass(slots=True)
class AssessmentReport:
    request_id: str
    session_id: str
    client_id: str
    specialization: str
    grade: str
    overall_score: int
    criterion_scores: dict[str, int]
    summary: str
    questions: list[QuestionFeedback]
    topics: list[TopicSummary]
    recommendations: list[str]
    versions: VersionInfo
    generated_at: str


@dataclass(slots=True)
class AssessmentJob:
    job_id: str
    request_id: str
    session_id: str
    status: JobStatus
    fingerprint: str
    created_at: str
    updated_at: str
    error_code: str | None = None
    error_message: str | None = None
    report: AssessmentReport | None = None
