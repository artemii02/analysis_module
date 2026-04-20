from __future__ import annotations

from interview_analysis.core.topic_catalog import topic_label
from interview_analysis.models import AssessmentReport, QuestionAnalysisContext, QuestionFeedback
from interview_analysis.repositories.content_repository import JSONContentRepository
from interview_analysis.services.llm.base import BaseLLMProvider
from interview_analysis.services.preprocessor import normalize_answer
from interview_analysis.services.report_builder import ReportBuilder
from interview_analysis.services.retrieval import SimpleKnowledgeRetriever


class AnalysisPipeline:
    def __init__(
        self,
        repository: JSONContentRepository,
        retriever: SimpleKnowledgeRetriever,
        llm_provider: BaseLLMProvider,
        report_builder: ReportBuilder,
    ) -> None:
        self.repository = repository
        self.retriever = retriever
        self.llm_provider = llm_provider
        self.report_builder = report_builder

    def analyze(self, request) -> AssessmentReport:
        contexts: list[QuestionAnalysisContext] = []
        for item in request.items:
            question = self.repository.get_question(
                item.question_id,
                request.scenario.specialization,
                request.scenario.grade,
            )
            rubric = self.repository.get_rubric(
                item.question_id,
                request.scenario.specialization,
                request.scenario.grade,
            )
            retrieved_chunks = self.retriever.retrieve(request.scenario, item, question)
            normalized_answer = normalize_answer(item.answer_text)
            contexts.append(
                QuestionAnalysisContext(
                    scenario=request.scenario,
                    session_item=item,
                    question=question,
                    rubric=rubric,
                    retrieved_chunks=retrieved_chunks,
                    normalized_answer=normalized_answer,
                )
            )

        assessments = self.llm_provider.assess_batch(contexts)
        feedback_items: list[QuestionFeedback] = []
        for context, assessment in zip(contexts, assessments, strict=True):
            feedback_items.append(
                QuestionFeedback(
                    item_id=context.session_item.item_id,
                    question_id=context.session_item.question_id,
                    question_text=context.session_item.question_text,
                    topic=topic_label(context.question.topic),
                    score=assessment.score,
                    criterion_scores=assessment.criterion_scores,
                    summary=assessment.summary,
                    strengths=assessment.strengths,
                    issues=assessment.issues,
                    covered_keypoints=assessment.covered_keypoints,
                    missing_keypoints=assessment.missing_keypoints,
                    detected_mistakes=assessment.detected_mistakes,
                    recommendations=assessment.recommendations,
                    context_snippets=context.retrieved_chunks,
                )
            )

        versions = self.repository.build_version_info(
            model_version=self.llm_provider.model_version,
            prompt_version=self.llm_provider.prompt_version,
        )
        return self.report_builder.build(
            request_id=request.request_id,
            session_id=request.session_id,
            client_id=request.client_id,
            specialization=request.scenario.specialization.value,
            grade=request.scenario.grade.value,
            feedback_items=feedback_items,
            versions=versions,
        )
