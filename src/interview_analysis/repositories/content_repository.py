from __future__ import annotations

import json
from pathlib import Path

from interview_analysis.exceptions import UnknownQuestionError
from interview_analysis.models import (
    Grade,
    KnowledgeChunk,
    MistakePattern,
    QuestionDefinition,
    RubricCriterion,
    RubricDefinition,
    Specialization,
    VersionInfo,
)


class JSONContentRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self._questions, self._questions_version = self._load_questions()
        self._question_text_index = self._build_question_text_index()
        self._rubrics, self._rubrics_version = self._load_rubrics()
        self._knowledge_chunks, self._kb_version = self._load_knowledge()

    def _load_questions(self) -> tuple[dict[str, QuestionDefinition], str]:
        payload = json.loads((self.data_dir / "questions.json").read_text(encoding="utf-8-sig"))
        questions: dict[str, QuestionDefinition] = {}
        for item in payload["items"]:
            questions[item["question_id"]] = QuestionDefinition(
                question_id=item["question_id"],
                specialization=Specialization(item["specialization"]),
                grade=Grade(item["grade"]),
                topic=item["topic"],
                question_text=item["question_text"],
                tags=item.get("tags", []),
                version=item["version"],
            )
        return questions, payload["version"]

    def _load_rubrics(self) -> tuple[dict[str, RubricDefinition], str]:
        payload = json.loads((self.data_dir / "rubrics.json").read_text(encoding="utf-8-sig"))
        rubrics: dict[str, RubricDefinition] = {}
        for item in payload["items"]:
            rubrics[item["question_id"]] = RubricDefinition(
                question_id=item["question_id"],
                specialization=Specialization(item["specialization"]),
                grade=Grade(item["grade"]),
                topic=item["topic"],
                criteria=[
                    RubricCriterion(
                        name=criterion["name"],
                        weight=criterion["weight"],
                        description=criterion["description"],
                    )
                    for criterion in item["criteria"]
                ],
                keypoints=item["keypoints"],
                recommendation_hints=item.get("recommendation_hints", []),
                mistake_patterns=[
                    MistakePattern(
                        trigger_terms=pattern["trigger_terms"],
                        message=pattern["message"],
                    )
                    for pattern in item.get("mistake_patterns", [])
                ],
                version=item["version"],
            )
        return rubrics, payload["version"]

    def _load_knowledge(self) -> tuple[list[KnowledgeChunk], str]:
        payload = json.loads((self.data_dir / "knowledge_base.json").read_text(encoding="utf-8-sig"))
        chunks: list[KnowledgeChunk] = []
        for item in payload["items"]:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=item["chunk_id"],
                    specialization=Specialization(item["specialization"]),
                    topics=item["topics"],
                    tags=item.get("tags", []),
                    content=item["content"],
                    source_title=item["source_title"],
                    source_url=item["source_url"],
                    version=item["version"],
                )
            )
        return chunks, payload["version"]

    def get_question(
        self,
        question_id: str,
        specialization: Specialization,
        grade: Grade,
    ) -> QuestionDefinition:
        question = self._questions.get(question_id)
        if question is None:
            raise UnknownQuestionError(question_id)
        if question.specialization != specialization or question.grade != grade:
            raise UnknownQuestionError(question_id)
        return question

    def resolve_question(
        self,
        question_id: str,
        question_text: str,
        specialization: Specialization,
        grade: Grade,
    ) -> QuestionDefinition:
        question = self._questions.get(question_id)
        if question is not None and question.specialization == specialization and question.grade == grade:
            return question

        normalized_text = _normalize_question_text(question_text)
        resolved_question = self._question_text_index.get((specialization, grade, normalized_text))
        if resolved_question is not None:
            return resolved_question
        raise UnknownQuestionError(question_id)

    def get_rubric(
        self,
        question_id: str,
        specialization: Specialization,
        grade: Grade,
    ) -> RubricDefinition:
        rubric = self._rubrics.get(question_id)
        if rubric is None:
            raise UnknownQuestionError(question_id)
        if rubric.specialization != specialization or rubric.grade != grade:
            raise UnknownQuestionError(question_id)
        return rubric

    def list_questions(
        self,
        specialization: Specialization,
        grade: Grade,
        limit: int | None = None,
    ) -> list[QuestionDefinition]:
        questions = [
            question
            for question in self._questions.values()
            if question.specialization == specialization and question.grade == grade
        ]
        questions.sort(key=lambda item: item.question_id)
        if limit is None:
            return questions
        return questions[:limit]

    def list_knowledge_chunks(self, specialization: Specialization) -> list[KnowledgeChunk]:
        return [
            chunk
            for chunk in self._knowledge_chunks
            if chunk.specialization == specialization
        ]

    def build_version_info(self, model_version: str, prompt_version: str) -> VersionInfo:
        return VersionInfo(
            model_version=model_version,
            rubric_version=self._rubrics_version,
            kb_version=self._kb_version,
            questions_version=self._questions_version,
            prompt_version=prompt_version,
        )

    def _build_question_text_index(self) -> dict[tuple[Specialization, Grade, str], QuestionDefinition]:
        index: dict[tuple[Specialization, Grade, str], QuestionDefinition] = {}
        for question in self._questions.values():
            index[
                (
                    question.specialization,
                    question.grade,
                    _normalize_question_text(question.question_text),
                )
            ] = question
        return index


def _normalize_question_text(value: str) -> str:
    return " ".join(value.strip().lower().replace("ё", "е").split())
