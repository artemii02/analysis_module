from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "src" / "interview_analysis" / "data"
OUTPUT_DIR = ROOT / "training" / "data"


PROFILES = [
    {"name": "strong", "split": "train", "score": 90, "covered_ratio": 1.0, "mistake": False},
    {"name": "medium", "split": "train", "score": 71, "covered_ratio": 0.5, "mistake": False},
    {"name": "weak", "split": "train", "score": 38, "covered_ratio": 0.25, "mistake": True},
    {"name": "eval", "split": "eval", "score": 78, "covered_ratio": 0.75, "mistake": False},
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


questions_payload = load_json(DATA_DIR / "questions.json")
rubrics_payload = load_json(DATA_DIR / "rubrics.json")
questions = {item["question_id"]: item for item in questions_payload["items"]}
rubrics = {item["question_id"]: item for item in rubrics_payload["items"]}



def build_answer(profile: dict, rubric: dict) -> tuple[str, list[str], list[str], list[str]]:
    keypoints = rubric["keypoints"]
    covered_count = max(1, round(len(keypoints) * profile["covered_ratio"]))
    covered = keypoints[:covered_count]
    missing = keypoints[covered_count:]

    answer_parts = []
    for keypoint in covered:
        answer_parts.append(keypoint)

    if profile["name"] == "strong":
        answer_parts.append("На практике я бы объяснил это через production-кейс и указал компромиссы решения.")
    elif profile["name"] == "medium":
        answer_parts.append("В целом понимаю идею, но часть нюансов нужно повторить и формализовать.")
    elif profile["name"] == "eval":
        answer_parts.append("Также добавил бы пример применения в реальном проекте и отметил возможные риски.")
    else:
        if rubric.get("mistake_patterns"):
            trigger_terms = rubric["mistake_patterns"][0]["trigger_terms"]
            answer_parts.append(" ".join(trigger_terms).capitalize() + ".")
        answer_parts.append("Подробные детали и ограничения сейчас вспомнить не могу.")

    detected_mistakes = []
    if profile["mistake"] and rubric.get("mistake_patterns"):
        detected_mistakes.append(rubric["mistake_patterns"][0]["message"])

    answer_text = " ".join(answer_parts)
    return answer_text, covered, missing, detected_mistakes



def build_expected_feedback(profile: dict, question: dict, rubric: dict, covered: list[str], missing: list[str], mistakes: list[str]) -> dict:
    base_score = profile["score"]
    criterion_scores = {
        "correctness": clamp(base_score + (4 if not mistakes else -8)),
        "completeness": clamp(base_score + (6 if len(missing) == 0 else -4)),
        "clarity": clamp(base_score + 3),
        "practicality": clamp(base_score + (5 if profile["name"] in {"strong", "eval"} else -6)),
        "terminology": clamp(base_score + (4 if profile["name"] != "weak" else -10)),
    }
    strengths = [f"Раскрыт пункт: {item}" for item in covered[:3]]
    if profile["name"] in {"strong", "eval"}:
        strengths.append("Есть попытка связать теорию с практическим сценарием.")

    issues = [f"Не раскрыт пункт: {item}" for item in missing[:3]]
    issues.extend(mistakes[:2])

    recommendations = list(dict.fromkeys(rubric.get("recommendation_hints", [])))
    if missing:
        recommendations.append(f"Повторить тему '{rubric['topic']}' и пройтись по всем keypoints.")
    if mistakes:
        recommendations.append("Отдельно проверить фактическую корректность формулировок и терминов.")

    return {
        "score": base_score,
        "criterion_scores": criterion_scores,
        "summary": f"Seed-оценка для вопроса '{question['question_id']}' и профиля '{profile['name']}'.",
        "strengths": strengths[:4],
        "issues": issues[:4],
        "covered_keypoints": covered,
        "missing_keypoints": missing,
        "detected_mistakes": mistakes,
        "recommendations": recommendations[:5],
    }



def clamp(value: int) -> int:
    return max(0, min(100, value))



def build_record(question_id: str, profile: dict) -> dict:
    question = questions[question_id]
    rubric = rubrics[question_id]
    answer_text, covered, missing, mistakes = build_answer(profile, rubric)
    expected_feedback = build_expected_feedback(profile, question, rubric, covered, missing, mistakes)
    return {
        "record_id": f"{question_id}__{profile['name']}",
        "split": profile["split"],
        "specialization": question["specialization"],
        "grade": question["grade"],
        "topic": question["topic"],
        "question_id": question_id,
        "question_text": question["question_text"],
        "answer_text": answer_text,
        "keypoints": rubric["keypoints"],
        "recommendation_hints": rubric.get("recommendation_hints", []),
        "expected_feedback": expected_feedback,
    }



def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")



def main() -> None:
    records: list[dict] = []
    for question_id in questions:
        for profile in PROFILES:
            records.append(build_record(question_id, profile))

    train_records = [item for item in records if item["split"] == "train"]
    eval_records = [item for item in records if item["split"] == "eval"]

    write_jsonl(OUTPUT_DIR / "raw_train.jsonl", train_records)
    write_jsonl(OUTPUT_DIR / "raw_eval.jsonl", eval_records)
    print(f"Generated {len(train_records)} train and {len(eval_records)} eval records.")


if __name__ == "__main__":
    main()