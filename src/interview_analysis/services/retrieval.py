from __future__ import annotations

from textwrap import shorten

from interview_analysis.models import (
    QuestionDefinition,
    RetrievedKnowledgeChunk,
    ScenarioContext,
    SessionItem,
)
from interview_analysis.repositories.content_repository import JSONContentRepository
from interview_analysis.services.preprocessor import significant_tokens


class SimpleKnowledgeRetriever:
    def __init__(self, repository: JSONContentRepository, limit: int = 3) -> None:
        self.repository = repository
        self.limit = limit

    def retrieve(
        self,
        scenario: ScenarioContext,
        item: SessionItem,
        question: QuestionDefinition,
    ) -> list[RetrievedKnowledgeChunk]:
        chunks = self.repository.list_knowledge_chunks(question.specialization)
        query_tokens = set(significant_tokens(question.question_text))
        query_tokens.update(significant_tokens(item.answer_text))
        query_tokens.update(token.casefold() for token in question.tags)
        query_tokens.update(token.casefold() for token in scenario.topics)

        scored: list[RetrievedKnowledgeChunk] = []
        for chunk in chunks:
            chunk_tokens = set(significant_tokens(chunk.content))
            chunk_tokens.update(token.casefold() for token in chunk.tags)
            chunk_tokens.update(token.casefold() for token in chunk.topics)

            overlap = len(query_tokens & chunk_tokens)
            if overlap == 0 and question.topic not in chunk.topics:
                continue

            score = overlap / max(len(query_tokens), 1)
            if question.topic in chunk.topics:
                score += 0.35
            if any(tag.casefold() in chunk_tokens for tag in question.tags):
                score += 0.1

            scored.append(
                RetrievedKnowledgeChunk(
                    chunk_id=chunk.chunk_id,
                    source_title=chunk.source_title,
                    source_url=chunk.source_url,
                    excerpt=shorten(chunk.content, width=160, placeholder="..."),
                    score=round(score, 3),
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: self.limit]
