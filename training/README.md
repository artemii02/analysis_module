# Training

This directory contains dataset preparation, evaluation, and fine-tuning helpers.

## Main scripts

- `training/scripts/generate_seed_dataset.py`
- `training/scripts/validate_dataset.py`
- `training/scripts/export_sft_dataset.py`
- `training/scripts/finetune_lora.py`
- `training/scripts/benchmark_runtime.py`

## Typical flow

1. `python training/scripts/generate_seed_dataset.py`
2. `python training/scripts/validate_dataset.py`
3. `python training/scripts/export_sft_dataset.py`
4. `pip install -e .[training]`
5. `python training/scripts/finetune_lora.py --config training/configs/lora_config.example.json`
6. `python training/scripts/benchmark_runtime.py`
