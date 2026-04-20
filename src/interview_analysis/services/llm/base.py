from __future__ import annotations

from abc import ABC, abstractmethod

from interview_analysis.models import QuestionAnalysisContext, QuestionAssessment


class BaseLLMProvider(ABC):
    model_version: str
    prompt_version: str

    @abstractmethod
    def assess(self, context: QuestionAnalysisContext) -> QuestionAssessment:
        raise NotImplementedError

    def assess_batch(self, contexts: list[QuestionAnalysisContext]) -> list[QuestionAssessment]:
        return [self.assess(context) for context in contexts]
