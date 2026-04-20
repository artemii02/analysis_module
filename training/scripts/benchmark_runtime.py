from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "training" / "data" / "raw_eval.jsonl"
DEFAULT_OUTPUT = ROOT / "training" / "data" / "runtime_predictions.jsonl"
CRITERIA = ["correctness", "completeness", "clarity", "practicality", "terminology"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default="demo-api-key")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def call_runtime(record: dict, base_url: str, api_key: str) -> dict:
    payload = {
        "request_id": f"runtime-eval-{record['record_id']}",
        "session_id": f"eval-session-{record['record_id']}",
        "client_id": "training-evaluator",
        "mode": "sync",
        "scenario": {
            "specialization": record["specialization"],
            "grade": record["grade"],
            "topics": [record["topic"]],
            "report_language": "ru",
        },
        "items": [
            {
                "item_id": record["record_id"],
                "question_id": record["question_id"],
                "question_text": record["question_text"],
                "answer_text": record["answer_text"],
                "tags": [],
            }
        ],
    }
    request = urllib.request.Request(
        f"{base_url}/assessment/v1/report",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        report_payload = json.loads(response.read().decode("utf-8"))
    return {
        "record_id": record["record_id"],
        "predicted_feedback": report_payload["report"]["questions"][0],
    }


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_jsonl_by_id(path: Path, payload_key: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            result[record["record_id"]] = record[payload_key]
    return result


def mae(values: list[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def jaccard(left: list[str], right: list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    return round(len(left_set & right_set) / len(left_set | right_set), 3)


def quality_band(score_mae: float, covered_jaccard: float, missing_jaccard: float) -> str:
    if score_mae <= 8 and covered_jaccard >= 0.7 and missing_jaccard >= 0.7:
        return "high"
    if score_mae <= 15 and covered_jaccard >= 0.5 and missing_jaccard >= 0.5:
        return "acceptable"
    return "needs_improvement"


def main() -> None:
    args = parse_args()
    expected_records = load_jsonl(args.input)
    predictions = [call_runtime(record, args.base_url, args.api_key) for record in expected_records]
    write_jsonl(args.output, predictions)

    expected = load_jsonl_by_id(args.input, "expected_feedback")
    predicted = load_jsonl_by_id(args.output, "predicted_feedback")
    common_ids = sorted(expected.keys() & predicted.keys())
    if not common_ids:
        raise SystemExit("No matching record_id found between expected and predicted files.")

    score_errors: list[float] = []
    criterion_errors: dict[str, list[float]] = {criterion: [] for criterion in CRITERIA}
    coverage_overlaps: list[float] = []
    missing_overlaps: list[float] = []

    for record_id in common_ids:
        exp = expected[record_id]
        pred = predicted[record_id]
        score_errors.append(abs(exp["score"] - pred.get("score", 0)))
        for criterion in CRITERIA:
            criterion_errors[criterion].append(
                abs(exp["criterion_scores"][criterion] - pred.get("criterion_scores", {}).get(criterion, 0))
            )
        coverage_overlaps.append(jaccard(exp["covered_keypoints"], pred.get("covered_keypoints", [])))
        missing_overlaps.append(jaccard(exp["missing_keypoints"], pred.get("missing_keypoints", [])))

    score_mae = mae(score_errors)
    covered_jaccard = mae(coverage_overlaps)
    missing_jaccard = mae(missing_overlaps)

    print(f"records={len(common_ids)}")
    print(f"score_mae={score_mae}")
    for criterion in CRITERIA:
        print(f"{criterion}_mae={mae(criterion_errors[criterion])}")
    print(f"covered_keypoints_jaccard={covered_jaccard}")
    print(f"missing_keypoints_jaccard={missing_jaccard}")
    print(f"quality_band={quality_band(score_mae, covered_jaccard, missing_jaccard)}")
    print(f"predictions_saved_to={args.output}")


if __name__ == "__main__":
    main()
