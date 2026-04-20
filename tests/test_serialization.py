from __future__ import annotations

from interview_analysis.core.serialization import report_from_primitive, to_primitive
from interview_analysis.models import AssessmentReport, QuestionFeedback, RetrievedKnowledgeChunk, TopicSummary, VersionInfo



def test_report_serialization_roundtrip() -> None:
    report = AssessmentReport(
        request_id='req-1',
        session_id='session-1',
        client_id='client-1',
        specialization='backend',
        grade='junior',
        overall_score=82,
        criterion_scores={'correctness': 80, 'completeness': 85, 'clarity': 78, 'practicality': 81, 'terminology': 84},
        summary='summary',
        questions=[
            QuestionFeedback(
                item_id='item-1',
                question_id='q-1',
                question_text='question',
                topic='http_api',
                score=82,
                criterion_scores={'correctness': 80, 'completeness': 85, 'clarity': 78, 'practicality': 81, 'terminology': 84},
                summary='question summary',
                strengths=['s1'],
                issues=['i1'],
                covered_keypoints=['k1'],
                missing_keypoints=['k2'],
                detected_mistakes=[],
                recommendations=['r1'],
                context_snippets=[
                    RetrievedKnowledgeChunk(
                        chunk_id='chunk-1',
                        source_title='title',
                        source_url='https://example.local',
                        excerpt='excerpt',
                        score=0.95,
                    )
                ],
            )
        ],
        topics=[TopicSummary(topic='http_api', average_score=82, strengths=['s1'], gaps=['g1'])],
        recommendations=['r1'],
        versions=VersionInfo(
            model_version='mock-heuristic-v1',
            rubric_version='rubrics-2026.03-demo',
            kb_version='kb-2026.03-demo',
            questions_version='questions-2026.03-demo',
            prompt_version='mock-provider',
        ),
        generated_at='2026-03-16T12:00:00+00:00',
    )

    restored = report_from_primitive(to_primitive(report))

    assert restored.request_id == report.request_id
    assert restored.criterion_scores['correctness'] == 80
    assert restored.questions[0].criterion_scores['correctness'] == 80
    assert restored.versions.model_version == 'mock-heuristic-v1'