"""The opt-in token-mean loss (GI III round 5; FOCUS.md decision 2026-10-07 22:05 UTC) on CPU: a step that mixes a
3-token and a 300-token answer gives different per-example and token-mean objectives and gradients; the token mean is
normalised by the step's total target tokens whatever the micro-batch split; the default path is the per-example mean
(the golden regressions pin it bit for bit); the recipe field and its loss text; the attribution step weights; and an
end-to-end fixture run whose steps and attribution follow the token mean."""

from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection import textproc as tp  # noqa: E402
from experiments.safety_selection.attribution import ROW_WEIGHTING, checkpoint_scores, step_weights  # noqa: E402
from experiments.safety_selection.config import (LOSS, LOSS_TOKEN_MEAN, ConfigError, config_sha256,  # noqa: E402
                                                 training_identity, validate_recipe)
from experiments.safety_selection.prepare import load_prepared  # noqa: E402
from experiments.safety_selection.stream import make_plan  # noqa: E402

TRAIN = {"lr": 0.01, "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.0}
TOKEN_RECIPE = {"train.loss_weighting": "token_mean", "train.loss": LOSS_TOKEN_MEAN}
# the fixture's recipe G: the token mean and HF's warmup cosine to e3 (45 fixture steps), so q, e1 and e3 are inside it
G_RECIPE = {**TOKEN_RECIPE, "train.lr_schedule": "warmup_cosine", "train.warmup_steps": 4, "train.schedule_until": "e3"}


def answer(codec, row_id: str, n_target: int) -> tp.TrainExample:
    """A training example whose targets (response plus end of turn) number exactly ``n_target``."""
    example = tp.encode_train(codec, row_id, "a fixture prompt", "z" * (n_target - 1), 1024)
    assert example.n_target == n_target
    return example


def reference_nll(model, example: tp.TrainExample) -> torch.Tensor:
    """The per-token target NLL of one example from an unbatched forward (float32)."""
    ids = torch.tensor([list(example.input_ids)])
    logits = en.causal_lm(model)(input_ids=ids).logits[0, example.n_prompt - 1:-1].float()
    return torch.nn.functional.cross_entropy(logits, ids[0, example.n_prompt:], reduction="none")


def grad(named) -> torch.Tensor:
    return torch.cat([p.grad.reshape(-1) for _, p in named]).clone()


def warm(model, named, codec) -> None:
    optimizer = en.make_optimizer(named, TRAIN)
    examples = [answer(codec, f"w{i}", 5 + 3 * i) for i in range(4)]
    en.train_step(model, named, optimizer, examples, 2, 1.0, codec.pad_id, "cpu", 16)


def test_a_3_and_a_300_token_answer_weigh_differently_under_the_two_objectives(tiny, codec):
    model, named = tiny
    warm(model, named, codec)
    short, long_ = answer(codec, "short", 3), answer(codec, "long", 300)
    nll = [reference_nll(model, e) for e in (short, long_)]
    example_mean = (nll[0].mean() + nll[1].mean()) / 2
    model.zero_grad(set_to_none=True)
    example_mean.backward()
    g_example = grad(named)
    again = [reference_nll(model, e) for e in (short, long_)]       # a fresh graph for the second objective
    token_mean = (again[0].sum() + again[1].sum()) / 303
    model.zero_grad(set_to_none=True)
    token_mean.backward()
    g_token = grad(named)
    assert not torch.allclose(g_example, g_token, rtol=1e-3)
    for micro in (1, 2):                                 # one normaliser for the whole step, whatever the split
        model.zero_grad(set_to_none=True)
        losses = en.accumulate_gradients(model, [short, long_], micro, codec.pad_id, "cpu", 16, en.TOKEN_MEAN)
        assert torch.allclose(grad(named), g_token, rtol=1e-5, atol=1e-7), micro
        assert losses == pytest.approx([float(nll[0].mean()), float(nll[1].mean())], rel=1e-5)
        model.zero_grad(set_to_none=True)
        en.accumulate_gradients(model, [short, long_], micro, codec.pad_id, "cpu", 16)
        assert torch.allclose(grad(named), g_example, rtol=1e-5, atol=1e-7), micro
    model.zero_grad(set_to_none=True)
    # the step objective: the short answer weighs 1/2 per-example but 3/303 under the token mean
    print(json.dumps({"fixture": "one step, a 3-token and a 300-token answer",
                      "example_mean_loss": float(example_mean), "token_mean_loss": float(token_mean),
                      "short_answer_weight": {"example_mean": 0.5, "token_mean": 3 / 303},
                      "gradient_relative_difference": float((g_example - g_token).norm() / g_token.norm())}))
    assert abs(float(example_mean) - float(token_mean)) > 1e-4


def test_train_step_reports_the_token_mean_and_refuses_an_unknown_weighting(tiny, codec):
    model, named = tiny
    optimizer = en.make_optimizer(named, TRAIN)
    batch = [answer(codec, "a", 3), answer(codec, "b", 40), answer(codec, "c", 300)]
    out = en.train_step(model, named, optimizer, batch, 2, 1.0, codec.pad_id, "cpu", 16, en.TOKEN_MEAN)
    assert out["loss"] == pytest.approx(math.fsum(l * e.n_target for l, e in zip(out["example_losses"], batch)) / 343)
    out = en.train_step(model, named, optimizer, batch, 2, 1.0, codec.pad_id, "cpu", 16)
    assert out["loss"] == pytest.approx(sum(out["example_losses"]) / 3)
    with pytest.raises(ValueError, match="unknown loss weighting"):
        en.accumulate_gradients(model, batch, 2, codec.pad_id, "cpu", 16, "per_token")


def test_the_recipe_field_its_loss_text_and_the_training_identity():
    base = fx.recipe()
    token = fx.recipe(**TOKEN_RECIPE)
    validate_recipe(base)
    validate_recipe(token)
    assert training_identity(token) != training_identity(base) and config_sha256(token) != config_sha256(base)
    for bad in ({"train.loss_weighting": "token_mean"},                                  # the old loss text
                {"train.loss_weighting": "example_mean", "train.loss": LOSS},              # only token_mean is a value
                {"train.loss_weighting": "example_mean", "train.loss": LOSS_TOKEN_MEAN},  # ... even with the right text
                {"train.loss_weighting": "token_mean", "train.loss": LOSS_TOKEN_MEAN + " "},
                {"train.loss": LOSS_TOKEN_MEAN}):                                          # the text without the field
        with pytest.raises(ConfigError):
            validate_recipe(fx.recipe(**bad))


def test_step_weights_follow_each_rows_first_epoch_step(tmp_path):
    rows = [f"r{k}" for k in range(7)]
    plan = make_plan(rows, [], 1101, 2, 2)                # 4 rows per step: steps of 4 and 3
    tokens = {r: 3 if k % 2 else 300 for k, r in enumerate(rows)}
    weights = step_weights(plan, tokens, rows)
    order = plan.epoch_order(0)
    for start in (0, 4):
        step = order[start:start + 4]
        total = sum(tokens[r] for r in step)
        for r in step:
            assert weights[r] == pytest.approx(tokens[r] * len(step) / total)
        assert sum(weights[r] for r in step) == pytest.approx(len(step))     # they average 1 within a step
    with pytest.raises(ValueError, match="not in the plan"):
        step_weights(plan, tokens, ["unknown"])


def test_the_adam_proxy_follows_the_weight_and_gradsim_does_not(tiny, codec):
    model, named = tiny
    warm(model, named, codec)
    queries, rows = [answer(codec, "q", 12)], [answer(codec, "x", 3), answer(codec, "y", 30)]
    inverse = torch.ones(sum(p.numel() for _, p in named), dtype=torch.float64)
    plain = checkpoint_scores(model, named, queries, rows, inverse=inverse, lr=0.01, pad_id=codec.pad_id,
                              device="cpu", chunk=16)
    weighted = checkpoint_scores(model, named, queries, rows, inverse=inverse, lr=0.01, pad_id=codec.pad_id,
                                 device="cpu", chunk=16, weights={"x": 0.25, "y": 1.75})
    for rid, w in (("x", 0.25), ("y", 1.75)):
        assert weighted["rows"][rid]["adam_score"] == pytest.approx(w * plain["rows"][rid]["adam_score"])
        assert weighted["rows"][rid]["cosine"] == plain["rows"][rid]["cosine"]
        assert weighted["rows"][rid]["weight"] == w and "weight" not in plain["rows"][rid]


@pytest.fixture(scope="module")
def token_env(tmp_path_factory):
    import test_ss_runner as tr
    root = tmp_path_factory.mktemp("token-mean")
    prepared_dir, digest = fx.prepare_dir(root / "prepared")
    recipe = fx.recipe(**G_RECIPE)
    e = SimpleNamespace(root=root, prepared=prepared_dir, sha=digest, recipe=recipe,
                        session=runner.Session(recipe, fx.fixture_loaders()))
    e.view = load_prepared(prepared_dir, digest, banks=("dev",))
    e.direct = runner.run_one(tr.run_job(e, target_checkpoint="e1", evaluate_bank=None), prepared_dir=prepared_dir,
                              out_dir=root / "direct", session=e.session)
    e.tr = tr
    return e


def to_e3(e) -> dict:
    """The e3 continuation of the direct run, made inside a test (a resume failure is a test failure, not a setup error)."""
    if not hasattr(e, "to_e3"):
        e.to_e3 = runner.run_one(e.tr.run_job(e, target_checkpoint="e3", evaluate_bank=None, resume_from=e.direct["run_dir"]),
                                 prepared_dir=e.prepared, out_dir=e.root / "e3", session=e.session)
    return e.to_e3


def test_an_end_to_end_token_mean_run_trains_and_attributes_with_its_weighting(token_env, monkeypatch):
    e = token_env
    full = load_prepared(e.prepared, e.sha)
    tokens = {rid: full.train_rows[rid]["target_tokens"] for rid in full.corpus}
    steps = [json.loads(line) for line in (Path(e.direct["run_dir"]) / "steps.jsonl").read_text().splitlines()]
    for s in steps:                                       # each step's reported loss is its token mean
        assert s["target_tokens"] == sum(tokens[r] for r in s["rows"])
        assert s["loss"] == pytest.approx(math.fsum(l * tokens[r] for l, r in zip(s["example_losses"], s["rows"]))
                                          / s["target_tokens"])
    to_e3(e)
    rates = []
    real = en.learning_rate
    monkeypatch.setattr(en, "learning_rate", lambda *a: rates.append(a) or real(*a))
    result = runner.attributes(e.tr.attr_job(e), prepared_dir=e.prepared, out_dir=e.root / "attr", session=e.session)
    peak = e.recipe["train"]["lr"]                            # the Adam proxy takes each checkpoint step's own rate
    assert rates == [(peak, "warmup_cosine", 4, 45, step) for step in (4, 15, 45)]
    folder = Path(result["run_dir"])
    groups = json.loads((folder / "groups.json").read_text())
    assert groups["row_weighting"] == ROW_WEIGHTING
    first_epoch = [s for s in steps if s["epoch"] == 0]
    expected = {r: tokens[r] * len(s["rows"]) / s["target_tokens"] for s in first_epoch for r in s["rows"]}
    for line in (folder / "rows.jsonl").read_text().splitlines():
        row = json.loads(line)
        for c, part in row["per_checkpoint"].items():
            assert part["weight"] == pytest.approx(expected[row["row_id"]]), (row["row_id"], c)


def test_a_scheduled_run_logs_each_rate_resumes_exactly_and_keeps_the_peak_in_its_state(token_env):
    e = token_env
    peak = e.recipe["train"]["lr"]
    e.short = runner.run_one(e.tr.run_job(e, target_checkpoint="q", evaluate_bank=None), prepared_dir=e.prepared,
                             out_dir=e.root / "short", session=e.session)
    e.cont = runner.run_one(e.tr.run_job(e, target_checkpoint="e1", evaluate_bank=None, resume_from=e.short["run_dir"]),
                            prepared_dir=e.prepared, out_dir=e.root / "cont", session=e.session)
    steps = [json.loads(line) for run in (e.direct, to_e3(e))
             for line in (Path(run["run_dir"]) / "steps.jsonl").read_text().splitlines()]
    assert [s["step"] for s in steps] == list(range(1, 46))
    assert [s["lr"] for s in steps] == [en.learning_rate(peak, "warmup_cosine", 4, 45, k) for k in range(1, 46)]
    assert steps[0]["lr"] == 0.0 and steps[4]["lr"] == peak
    for checkpoint, other in (("q", e.short), ("e1", e.cont)):      # q -> e1 resumes to the same adapter and AdamW state
        direct = json.loads((Path(e.direct["run_dir"]) / "states" / checkpoint / "state.json").read_text())
        resumed = json.loads((Path(other["run_dir"]) / "states" / checkpoint / "state.json").read_text())
        for key in ("adapter_fingerprint", "optimizer_fingerprint", "rng_fingerprint", "step"):
            assert direct[key] == resumed[key], (checkpoint, key)
        assert direct["param_groups"][0]["lr"] == peak          # the saved state keeps the recipe's peak
    cont = [json.loads(line) for line in (Path(e.cont["run_dir"]) / "steps.jsonl").read_text().splitlines()]
    assert [s["lr"] for s in cont] == [s["lr"] for s in steps if s["step"] in {c["step"] for c in cont}]


def test_training_past_the_schedules_last_step_refuses(token_env):
    import test_ss_runner as tr
    from experiments.safety_selection.runner import RunError
    e = token_env
    recipe = fx.recipe(**{**G_RECIPE, "train.schedule_until": "q"})
    session = runner.Session(recipe, fx.fixture_loaders())
    env = SimpleNamespace(**{**vars(e), "recipe": recipe})
    with pytest.raises(RunError, match="past the schedule's last step 4"):
        runner.run_one(tr.run_job(env, target_checkpoint="e1", evaluate_bank=None), prepared_dir=e.prepared,
                       out_dir=e.root / "past", session=session)


def test_the_scheduled_rate_is_the_one_applied(token_env):
    """At q the warmup-cosine run differs from the same recipe at a constant rate (its steps 1-4 run below the peak)."""
    e = token_env
    constant = fx.recipe(**TOKEN_RECIPE)
    env = SimpleNamespace(**{**vars(e), "recipe": constant})
    flat = runner.run_one(e.tr.run_job(env, target_checkpoint="q", evaluate_bank=None), prepared_dir=e.prepared,
                          out_dir=e.root / "constant-q", session=runner.Session(constant, fx.fixture_loaders()))
    state = lambda run: json.loads((Path(run["run_dir"]) / "states" / "q" / "state.json").read_text())  # noqa: E731
    assert state(flat)["step"] == state(e.direct)["step"] == 4
    assert state(flat)["adapter_fingerprint"] != state(e.direct)["adapter_fingerprint"]
    assert state(flat)["optimizer_fingerprint"] != state(e.direct)["optimizer_fingerprint"]
