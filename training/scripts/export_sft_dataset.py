from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_TRAIN = ROOT / "training" / "data" / "raw_train.jsonl"
DEFAULT_INPUT_EVAL = ROOT / "training" / "data" / "raw_eval.jsonl"
DEFAULT_OUTPUT_TRAIN = ROOT / "training" / "data" / "sft_train.jsonl"
DEFAULT_OUTPUT_EVAL = ROOT / "training" / "data" / "sft_eval.jsonl"

SYSTEM_PROMPT = (
    "Ты оцениваешь технический ответ кандидата и возвращаешь только валидный JSON "
    "со score, criterion_scores, summary, strengths, issues, covered_keypoints, "
    "missing_keypoints, detected_mistakes и recommendations."
)



def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]



def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")



def convert_record(record: dict) -> dict:
    user_payload = {
        "specialization": record["specialization"],
        "grade": record["grade"],
        "topic": record["topic"],
        "question_id": record["question_id"],
        "question_text": record["question_text"],
        "answer_text": record["answer_text"],
        "expected_keypoints": record["keypoints"],
        "recommendation_hints": record["recommendation_hints"],
    }
    return {
        "record_id": record["record_id"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            {"role": "assistant", "content": json.dumps(record["expected_feedback"], ensure_ascii=False)},
        ],
        "metadata": {
            "specialization": record["specialization"],
            "grade": record["grade"],
            "topic": record["topic"],
            "question_id": record["question_id"],
        },
    }



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-input", type=Path, default=DEFAULT_INPUT_TRAIN)
    parser.add_argument("--eval-input", type=Path, default=DEFAULT_INPUT_EVAL)
    parser.add_argument("--train-output", type=Path, default=DEFAULT_OUTPUT_TRAIN)
    parser.add_argument("--eval-output", type=Path, default=DEFAULT_OUTPUT_EVAL)
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    train_records = [convert_record(item) for item in load_jsonl(args.train_input)]
    eval_records = [convert_record(item) for item in load_jsonl(args.eval_input)]
    write_jsonl(args.train_output, train_records)
    write_jsonl(args.eval_output, eval_records)
    print(f"Exported {len(train_records)} train and {len(eval_records)} eval SFT records.")


if __name__ == "__main__":
    main()