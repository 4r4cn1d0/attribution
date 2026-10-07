"""Count a recipe's LoRA values on a meta-device model built from a config.json (brief multi-family-probe-engine-20261007,
Item 3; standalone, outside the engine's code identity; no weights, nothing downloaded).

    python scripts/family_lora_count.py --config CONFIG_JSON --recipe RECIPE

Prints the architecture, the count, the recipe's expected count and whether they match; exits 1 on a mismatch.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.safety_selection.config import load_recipe  # noqa: E402


def lora_count(config_path: str, recipe: dict) -> tuple[str, int]:
    import peft
    import torch
    import transformers

    config = transformers.AutoConfig.from_pretrained(str(Path(config_path).parent), local_files_only=True)
    with torch.device("meta"):
        model = transformers.AutoModelForCausalLM.from_config(config)
    lora = recipe["model"]["lora"]
    wrapped = peft.get_peft_model(model, peft.LoraConfig(r=lora["r"], lora_alpha=lora["alpha"], lora_dropout=lora["dropout"],
                                                         target_modules=list(lora["target_modules"]), bias="none",
                                                         task_type="CAUSAL_LM"))
    count = sum(p.numel() for n, p in wrapped.named_parameters() if p.requires_grad)
    return type(model).__name__, count


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--recipe", required=True)
    a = ap.parse_args(argv)
    recipe = load_recipe(a.recipe)
    architecture, count = lora_count(a.config, recipe)
    expected = recipe["model"]["lora"]["expected_trainable_parameters"]
    out = {"config": a.config, "recipe": recipe["name"], "architecture": architecture,
           "recipe_architecture": recipe["model"]["architecture"], "lora_values": count, "expected": expected,
           "match": count == expected and architecture == recipe["model"]["architecture"]}
    print(json.dumps(out))
    return 0 if out["match"] else 1


if __name__ == "__main__":
    sys.exit(main())
