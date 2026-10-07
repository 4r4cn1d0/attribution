"""The opt-in learning-rate schedules (GI III round 5 addendum): engine.learning_rate equals HF transformers'
get_cosine_schedule_with_warmup and get_constant_schedule_with_warmup step for step; the values at step 1, the end
of the warmup, the middle and the last step of a 38-step run; "constant" is the peak; and the recipe fields."""

from __future__ import annotations

import json

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection.config import ConfigError, LOSS_TOKEN_MEAN, training_identity, validate_recipe  # noqa: E402

PEAK, WARMUP, TOTAL = 1e-4, 4, 38


def hf_rates(kind: str, peak: float = PEAK, warmup: int = WARMUP, total: int = TOTAL) -> list[float]:
    """The rate of each of ``total`` optimizer steps under HF's scheduler (step, then scheduler.step())."""
    param = torch.nn.Parameter(torch.zeros(1))
    optimizer = torch.optim.AdamW([param], lr=peak)
    make = {"warmup_cosine": lambda: transformers.get_cosine_schedule_with_warmup(optimizer, warmup, total),
            "warmup_constant": lambda: transformers.get_constant_schedule_with_warmup(optimizer, warmup)}[kind]
    scheduler = make()
    rates = []
    for _ in range(total):
        rates.append(optimizer.param_groups[0]["lr"])
        optimizer.step()
        scheduler.step()
    return rates


@pytest.mark.parametrize("kind", ["warmup_cosine", "warmup_constant"])
def test_the_schedule_is_hf_s_step_for_step(kind):
    ours = [en.learning_rate(PEAK, kind, WARMUP, TOTAL, step) for step in range(1, TOTAL + 1)]
    assert ours == pytest.approx(hf_rates(kind), rel=1e-12, abs=1e-18)


def test_the_values_at_step_1_the_warmup_end_the_middle_and_the_last_step(capsys):
    rate = lambda step: en.learning_rate(PEAK, "warmup_cosine", WARMUP, TOTAL, step)  # noqa: E731
    assert rate(1) == 0.0 and rate(4) == pytest.approx(0.75 * PEAK) and rate(5) == PEAK
    assert rate(19) == pytest.approx(PEAK * 0.5 * (1 + __import__("math").cos(__import__("math").pi * 14 / 34)))
    assert 0 < rate(38) < 0.01 * PEAK                         # HF reaches 0 only after the last step
    table = {step: rate(step) for step in (1, 2, 3, 4, 5, 6, 19, 38)}
    print(json.dumps({"lr_table_38_steps_warmup_4_peak_1e-4": table}))
    assert en.learning_rate(PEAK, "constant", 0, 0, 999) == PEAK
    for bad in ((PEAK, "warmup_cosine", 4, 38, 0), (PEAK, "warmup_cosine", 4, 38, 39), (PEAK, "warmup_cosine", 0, 38, 5),
                (PEAK, "linear", 4, 38, 5)):
        with pytest.raises(ValueError):
            en.learning_rate(*bad)


def test_the_schedule_fields_of_a_recipe():
    g = fx.recipe(**{"train.lr_schedule": "warmup_cosine", "train.warmup_steps": 4, "train.schedule_until": "e1"})
    validate_recipe(g)
    validate_recipe(fx.recipe(**{"train.lr_schedule": "warmup_constant", "train.warmup_steps": 2,
                                 "train.schedule_until": "q"}))
    assert training_identity(g) != training_identity(fx.recipe())
    for bad in ({"train.lr_schedule": "warmup_cosine"},                                                  # no fields
                {"train.lr_schedule": "warmup_cosine", "train.warmup_steps": 0, "train.schedule_until": "e1"},
                {"train.lr_schedule": "warmup_cosine", "train.warmup_steps": 4, "train.schedule_until": "e9"},
                {"train.lr_schedule": "linear", "train.warmup_steps": 4, "train.schedule_until": "e1"},
                {"train.warmup_steps": 4, "train.schedule_until": "e1"}):                                 # constant
        with pytest.raises(ConfigError):
            validate_recipe(fx.recipe(**bad))
    validate_recipe(fx.recipe(**{"train.loss_weighting": "token_mean", "train.loss": LOSS_TOKEN_MEAN,
                                 "train.lr_schedule": "warmup_cosine", "train.warmup_steps": 4, "train.schedule_until": "e1"}))
