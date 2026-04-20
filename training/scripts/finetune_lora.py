from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "training" / "configs" / "lora_config.example.json"



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()



def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))



def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    try:
        from datasets import load_dataset
        from peft import LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from trl import SFTTrainer
    except ImportError as exc:
        raise SystemExit(
            "Training dependencies are missing. Install them with: pip install -e .[training]"
        ) from exc

    train_dataset = load_dataset("json", data_files=str(config["train_file"]), split="train")
    eval_dataset = load_dataset("json", data_files=str(config["eval_file"]), split="train")

    tokenizer = AutoTokenizer.from_pretrained(config["base_model"], trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        config["base_model"],
        trust_remote_code=True,
    )

    peft_config = LoraConfig(
        r=config["lora_r"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        target_modules=config["target_modules"],
        bias="none",
        task_type="CAUSAL_LM",
    )

    training_args = TrainingArguments(
        output_dir=config["output_dir"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        per_device_eval_batch_size=config["per_device_eval_batch_size"],
        learning_rate=config["learning_rate"],
        num_train_epochs=config["num_train_epochs"],
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=config["logging_steps"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        warmup_ratio=config["warmup_ratio"],
        fp16=config.get("fp16", False),
        bf16=config.get("bf16", False),
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
        max_seq_length=config["max_seq_length"],
    )
    trainer.train()
    trainer.save_model(config["output_dir"])
    tokenizer.save_pretrained(config["output_dir"])
    print(f"Training finished. Adapter saved to {config['output_dir']}")


if __name__ == "__main__":
    main()