from __future__ import annotations

from interview_analysis.models import QuestionAnalysisContext, QuestionAssessment
from interview_analysis.services.grounded_assessment import build_grounded_assessment


class MockLLMProvider:
    model_version = 'mock-grounded-v2'
    prompt_version = 'mock-provider-grounded'

    def assess(self, context: QuestionAnalysisContext) -> QuestionAssessment:
        return build_grounded_assessment(context)

    def assess_batch(self, contexts: list[QuestionAnalysisContext]) -> list[QuestionAssessment]:
        return [self.assess(context) for context in contexts]
