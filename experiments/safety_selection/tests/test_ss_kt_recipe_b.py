"""Kill-test recipe B (Qi et al. adapted to LoRA): it changes only the stated fields of the Stage 0 recipe, and its
checkpoints fall on the steps the amendment records. Not a scientific result."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from experiments.safety_selection.config import load_recipe
from experiments.safety_selection.stream import StreamPlan

CONFIGS = Path(__file__).resolve().parents[1] / "configs"


def test_recipe_b_changes_only_batch_and_lr():
    base = load_recipe(CONFIGS / "study-kt-instruct-r64-mb4-20261006.json")
    b = load_recipe(CONFIGS / "study-kt-instruct-r64-b128-qi-20261007.json")
    assert b["name"] == "study-kt-instruct-r64-b128-qi-20261007"
    assert (b["train"]["micro_batch"], b["train"]["grad_accum"], b["train"]["lr"]) == (4, 32, 0.0001)
    undo = json.loads(json.dumps(b))
    undo["name"], undo["purpose"] = base["name"], base["purpose"]
    undo["train"].update(grad_accum=base["train"]["grad_accum"], lr=base["train"]["lr"])
    assert undo == base


def test_recipe_b_checkpoint_steps_on_the_kill_test_dolly_rows():
    b = load_recipe(CONFIGS / "study-kt-instruct-r64-b128-qi-20261007.json")
    plan = StreamPlan(seed=1101, corpus=tuple(f"r{i:04d}" for i in range(4800)), removed=frozenset(),
                      micro_batch=b["train"]["micro_batch"], grad_accum=b["train"]["grad_accum"])
    assert plan.steps_per_epoch == 38
    steps = {c["name"]: plan.checkpoint(Fraction(*c["epochs"]))["step"] for c in b["train"]["checkpoints"]}
    assert steps == {"q": 10, "e1": 38, "e3": 114}
