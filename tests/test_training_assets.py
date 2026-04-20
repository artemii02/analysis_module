from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / 'training' / 'data' / 'raw_train.jsonl'



def test_training_seed_dataset_covers_all_specialization_grade_pairs() -> None:
    pairs: set[tuple[str, str]] = set()
    with TRAIN_PATH.open('r', encoding='utf-8') as handle:
        for line in handle:
            record = json.loads(line)
            pairs.add((record['specialization'], record['grade']))

    assert pairs == {
        ('backend', 'junior'),
        ('backend', 'middle'),
        ('frontend', 'junior'),
        ('frontend', 'middle'),
        ('devops', 'junior'),
        ('devops', 'middle'),
    }