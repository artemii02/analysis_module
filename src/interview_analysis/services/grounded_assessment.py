from __future__ import annotations

from dataclasses import dataclass

from interview_analysis.core.topic_catalog import topic_label
from interview_analysis.models import QuestionAnalysisContext, QuestionAssessment
from interview_analysis.services.preprocessor import normalize_answer, significant_tokens


LOW_SIGNAL_EXACT = {
    '-', '--', '---', '.', '..', '...', '?', '??', '???',
    'хз', 'xs', 'idk', 'n/a', 'na', 'none', 'null',
}
LOW_SIGNAL_PHRASES = {
    'не знаю',
    'без понятия',
    'понятия не имею',
    'затрудняюсь ответить',
    'затрудняюсь',
    'не помню',
    'не уверен',
    'не могу ответить',
    'сложно сказать',
    'не в курсе',
    'не разбираюсь',
}
EXAMPLE_MARKERS = ('например', 'на практике', 'в продакшене', 'production', 'кейс')


@dataclass(frozen=True, slots=True)
class GroundedSignals:
    low_signal: bool
    answer_tokens: set[str]
    covered_keypoints: list[str]
    missing_keypoints: list[str]
    detected_mistakes: list[str]
    terminology_ratio: float
    coverage_ratio: float
    depth_ratio: float
    has_examples: bool
    has_structure: bool



def build_grounded_assessment(context: QuestionAnalysisContext) -> QuestionAssessment:
    signals = collect_grounded_signals(context)
    display_topic = topic_label(context.question.topic)

    if signals.low_signal:
        criterion_scores = {
            'correctness': 0,
            'completeness': 0,
            'clarity': 4,
            'practicality': 0,
            'terminology': 0,
        }
        return QuestionAssessment(
            score=_weighted_score(criterion_scores, context.rubric.criteria),
            criterion_scores=criterion_scores,
            summary='Ответ слишком короткий и не содержит содержательного технического разбора.',
            strengths=[],
            issues=[
                'Ответ является формальной заглушкой и не раскрывает вопрос.',
                f"Тема '{display_topic}' не раскрыта.",
            ],
            covered_keypoints=[],
            missing_keypoints=context.rubric.keypoints[:3],
            detected_mistakes=[],
            recommendations=_recommendations_for_low_signal(context, display_topic),
        )

    criterion_scores = _criterion_scores_from_signals(signals)
    strengths = [f'Корректно затронут пункт: {item}' for item in signals.covered_keypoints[:2]]
    if signals.has_examples and signals.coverage_ratio >= 0.25:
        strengths.append('В ответе есть попытка связать теорию с практическим примером.')

    issues = [f'Не раскрыт пункт: {item}' for item in signals.missing_keypoints[:3]]
    issues.extend(signals.detected_mistakes[:2])
    if not strengths and not issues:
        issues.append('Ответ слишком общий и требует большей технической конкретики.')

    recommendations = list(dict.fromkeys(context.rubric.recommendation_hints))
    if signals.coverage_ratio < 0.5:
        recommendations.append(f"Повторить тему '{display_topic}' и закрыть пропущенные ключевые пункты.")
    if signals.terminology_ratio < 0.2:
        recommendations.append('Добавить корректную терминологию и ключевые технические понятия по теме.')
    if signals.has_examples is False and signals.coverage_ratio >= 0.25:
        recommendations.append('Добавить практический пример применения или разбора кейса.')

    summary = (
        f'Покрыто {len(signals.covered_keypoints)} из {len(context.rubric.keypoints)} ключевых пунктов. '
        f"Основной резерв улучшения находится в теме '{display_topic}'."
    )
    return QuestionAssessment(
        score=_weighted_score(criterion_scores, context.rubric.criteria),
        criterion_scores=criterion_scores,
        summary=summary,
        strengths=strengths[:3],
        issues=issues[:4],
        covered_keypoints=signals.covered_keypoints,
        missing_keypoints=signals.missing_keypoints,
        detected_mistakes=signals.detected_mistakes,
        recommendations=recommendations[:4],
    )



def collect_grounded_signals(context: QuestionAnalysisContext) -> GroundedSignals:
    normalized = normalize_answer(context.session_item.answer_text)
    low_signal = is_low_signal_answer(normalized)
    answer_tokens = set(significant_tokens(context.session_item.answer_text))

    covered_keypoints: list[str] = []
    missing_keypoints: list[str] = []
    for keypoint in context.rubric.keypoints:
        keypoint_tokens = set(significant_tokens(keypoint))
        overlap = len(answer_tokens & keypoint_tokens)
        ratio = overlap / max(len(keypoint_tokens), 1)
        if overlap >= min(2, len(keypoint_tokens)) or ratio >= 0.5 or (len(keypoint_tokens) <= 3 and overlap == len(keypoint_tokens)):
            covered_keypoints.append(keypoint)
        else:
            missing_keypoints.append(keypoint)

    detected_mistakes: list[str] = []
    for pattern in context.rubric.mistake_patterns:
        if pattern.trigger_terms and all(term.casefold() in normalized for term in pattern.trigger_terms):
            detected_mistakes.append(pattern.message)

    tag_tokens = set()
    for tag in context.question.tags:
        tag_tokens.update(significant_tokens(tag))

    terminology_ratio = len(answer_tokens & tag_tokens) / max(len(tag_tokens), 1) if tag_tokens else 0.0
    coverage_ratio = len(covered_keypoints) / max(len(context.rubric.keypoints), 1)
    depth_ratio = min(len(answer_tokens) / 24, 1.0)
    has_examples = any(marker in normalized for marker in EXAMPLE_MARKERS)
    has_structure = any(marker in context.session_item.answer_text for marker in (':', '-', '\n'))

    return GroundedSignals(
        low_signal=low_signal,
        answer_tokens=answer_tokens,
        covered_keypoints=covered_keypoints,
        missing_keypoints=missing_keypoints,
        detected_mistakes=detected_mistakes,
        terminology_ratio=terminology_ratio,
        coverage_ratio=coverage_ratio,
        depth_ratio=depth_ratio,
        has_examples=has_examples,
        has_structure=has_structure,
    )



def is_low_signal_answer(normalized_answer: str) -> bool:
    normalized = normalize_answer(normalized_answer)
    stripped = normalized.strip(' .,!?:;-_/|')
    if not stripped:
        return True
    if stripped in LOW_SIGNAL_EXACT:
        return True
    if any(phrase in normalized for phrase in LOW_SIGNAL_PHRASES):
        return True
    tokens = significant_tokens(normalized)
    return len(tokens) == 0 or (len(tokens) <= 2 and len(stripped) <= 16)



def should_skip_llm(context: QuestionAnalysisContext) -> bool:
    signals = collect_grounded_signals(context)
    return signals.low_signal or len(signals.answer_tokens) <= 2



def _criterion_scores_from_signals(signals: GroundedSignals) -> dict[str, int]:
    correctness = round(signals.coverage_ratio * 80 + signals.terminology_ratio * 10 - len(signals.detected_mistakes) * 15)
    completeness = round(signals.coverage_ratio * 82 + signals.depth_ratio * 12)
    clarity = round(signals.depth_ratio * 45 + (20 if signals.has_structure else 0) + (8 if len(signals.answer_tokens) >= 8 else 0))
    practicality = round(signals.coverage_ratio * 35 + signals.depth_ratio * 15 + (35 if signals.has_examples else 0))
    terminology = round(signals.terminology_ratio * 80 + min(len(signals.answer_tokens), 10) * 1.2)

    if signals.coverage_ratio < 0.15:
        correctness = min(correctness, 18)
        completeness = min(completeness, 15)
        practicality = min(practicality, 10)
    if signals.terminology_ratio < 0.1:
        terminology = min(terminology, 12)

    return {
        'correctness': _clamp(correctness),
        'completeness': _clamp(completeness),
        'clarity': _clamp(clarity),
        'practicality': _clamp(practicality),
        'terminology': _clamp(terminology),
    }



def _recommendations_for_low_signal(context: QuestionAnalysisContext, display_topic: str) -> list[str]:
    recommendations = list(dict.fromkeys(context.rubric.recommendation_hints))
    recommendations.append('Нужно дать предметный ответ по существу вопроса, а не короткую заглушку.')
    recommendations.append(f"Повторить тему '{display_topic}' и базовые термины по ней.")
    return recommendations[:4]



def _weighted_score(criterion_scores: dict[str, int], criteria: list) -> int:
    if not criteria:
        return 0
    weighted_total = 0.0
    total_weight = 0.0
    for criterion in criteria:
        weighted_total += criterion_scores.get(criterion.name, 0) * criterion.weight
        total_weight += criterion.weight
    if total_weight <= 0:
        return 0
    return round(weighted_total / total_weight)



def _clamp(value: int) -> int:
    return max(0, min(100, value))
