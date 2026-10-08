"""The round-5 review's loss/LR checks (the reviewer's spy test, adopted in round 6 as S2; the integration review,
"Round 5 (8 Oct)", lens 1), now part of the engine suite.

(1) token-mean gradient for micro-batch sizes 1..5 equals an independent unbatched reference and HF's own
    labels-based single-batch loss (prompt and pad positions ignored); negative controls show the tolerance
    separates the per-micro-batch normaliser, the per-example mean and a normaliser without end-of-turn.
(2) the pad id does not change the token-mean gradient (padding excluded).
(3) runner wiring: each optimizer step calls train_step once with all of the step's actual rows (short final
    step included) and the token-mean weighting; the rate in the param groups at optimizer.step() equals the
    logged lr; step 1 (rate 0) leaves the adapter unchanged; the saved state keeps the peak.
(4) resume from q reproduces the direct run's per-step rates and its e1 state; a target past schedule_until
    refuses (round 6, M1: as a job error, before any training); a removal arm uses its own plan's horizon (HF's
    convention; an open design point for Gate B, config.py).
"""

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
from experiments.safety_selection.config import LOSS_TOKEN_MEAN  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402

TRAIN = {"lr": 0.01, "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.0}
LENGTHS = [3, 7, 50, 120, 200]          # deliberately unequal targets; N = 380


def answer(codec, rid: str, n_target: int, prompt: str = "a review prompt") -> tp.TrainExample:
    ex = tp.encode_train(codec, rid, prompt + rid, "q" * (n_target - 1), 1024)
    assert ex.n_target == n_target and ex.input_ids[-1] == codec.eos_id   # end-of-turn is the last target
    return ex


def flat_grad(named) -> torch.Tensor:
    return torch.cat([p.grad.reshape(-1) for _, p in named]).double().clone()


def warmed(codec):
    model = fx.tiny_lora_model(seed=3)
    named = en.lora_parameters(model)
    optimizer = en.make_optimizer(named, TRAIN)
    for k in range(3):                    # make LoRA B non-zero so every LoRA tensor has a gradient
        en.train_step(model, named, optimizer, [answer(codec, f"w{k}{j}", 4 + 9 * j) for j in range(4)], 2, 1.0,
                      codec.pad_id, "cpu", 16)
    model.zero_grad(set_to_none=True)
    return model, named


def unbatched_token_nll(model, ex: tp.TrainExample) -> torch.Tensor:
    ids = torch.tensor([list(ex.input_ids)])
    logits = en.causal_lm(model)(input_ids=ids).logits[0].float()
    return torch.nn.functional.cross_entropy(logits[ex.n_prompt - 1:-1], ids[0, ex.n_prompt:], reduction="none")


def hf_labels_loss(model, examples, pad_id: int) -> torch.Tensor:
    """HF's own causal-LM loss on ONE right-padded batch: labels -100 at prompt and pad positions, so HF averages
    over every target token of the step (its mean over non-ignored labels)."""
    width = max(len(e.input_ids) for e in examples)
    ids = torch.full((len(examples), width), pad_id, dtype=torch.long)
    mask = torch.zeros_like(ids)
    labels = torch.full_like(ids, -100)
    for i, e in enumerate(examples):
        n = len(e.input_ids)
        ids[i, :n] = torch.tensor(e.input_ids)
        mask[i, :n] = 1
        labels[i, e.n_prompt:n] = torch.tensor(e.input_ids[e.n_prompt:])
    return en.causal_lm(model)(input_ids=ids, attention_mask=mask, labels=labels).loss


def test_token_mean_gradient_is_independent_of_the_split_and_equals_direct_references(codec):
    model, named = warmed(codec)
    step = [answer(codec, f"s{j}", n) for j, n in enumerate(LENGTHS)]
    N = sum(e.n_target for e in step)
    assert N == sum(LENGTHS)

    nll = [unbatched_token_nll(model, e) for e in step]
    (torch.cat(nll).sum() / N).backward()
    g_ref = flat_grad(named)
    model.zero_grad(set_to_none=True)

    hf_labels_loss(model, step, codec.pad_id).backward()
    g_hf = flat_grad(named)
    model.zero_grad(set_to_none=True)

    # negative controls (what a wrong implementation would produce)
    nll = [unbatched_token_nll(model, e) for e in step]
    sum(x.mean() for x in nll).div(len(step)).backward()
    g_example = flat_grad(named)
    model.zero_grad(set_to_none=True)
    nll = [unbatched_token_nll(model, e) for e in step]
    (sum(x[:-1].sum() for x in nll) / (N - len(step))).backward()     # end-of-turn dropped from loss and normaliser
    g_no_eot = flat_grad(named)
    model.zero_grad(set_to_none=True)

    rel = lambda a, b: float((a - b).norm() / b.norm())  # noqa: E731
    report = {"N": N, "hf_vs_ref": rel(g_hf, g_ref), "example_mean_vs_ref": rel(g_example, g_ref),
              "no_end_of_turn_vs_ref": rel(g_no_eot, g_ref), "micro": {}}
    for micro in (1, 2, 3, 4, 5):
        model.zero_grad(set_to_none=True)
        values = en.accumulate_gradients(model, step, micro, codec.pad_id, "cpu", 16, en.TOKEN_MEAN)
        g = flat_grad(named)
        # per-micro-batch normaliser control: sum over micro-batches of (micro-batch token sum / micro-batch tokens)
        model.zero_grad(set_to_none=True)
        for s in range(0, len(step), micro):
            part = step[s:s + micro]
            torch.cat([unbatched_token_nll(model, e) for e in part]).sum().div(sum(e.n_target for e in part)).div(
                math.ceil(len(step) / micro)).backward()
        g_permb = flat_grad(named)
        model.zero_grad(set_to_none=True)
        report["micro"][micro] = {"engine_vs_ref": rel(g, g_ref), "per_microbatch_normaliser_vs_ref": rel(g_permb, g_ref)}
        assert rel(g, g_ref) < 1e-5, (micro, report)
        assert rel(g, g_hf) < 1e-5, (micro, report)
        assert values == pytest.approx([float(x.mean()) for x in nll], rel=1e-5)
        if micro not in (1, 5):                               # the control coincides only when every split is equal
            assert rel(g_permb, g_ref) > 1e-2, (micro, report)
    assert rel(g_hf, g_ref) < 1e-5
    assert rel(g_example, g_ref) > 1e-2 and rel(g_no_eot, g_ref) > 1e-4
    print(json.dumps({"review_token_mean_gradient": report}))


def test_padding_is_excluded(codec):
    model, named = warmed(codec)
    step = [answer(codec, f"p{j}", n) for j, n in enumerate([3, 90, 11, 200])]
    grads = []
    for pad in (codec.pad_id, 0, 65, 255):
        model.zero_grad(set_to_none=True)
        en.accumulate_gradients(model, step, 4, pad, "cpu", 16, en.TOKEN_MEAN)
        grads.append(flat_grad(named))
    for g in grads[1:]:
        assert float((g - grads[0]).norm() / grads[0].norm()) < 1e-6


G = {"train.loss_weighting": "token_mean", "train.loss": LOSS_TOKEN_MEAN, "train.lr_schedule": "warmup_cosine",
     "train.warmup_steps": 4, "train.schedule_until": "e1"}


@pytest.fixture(scope="module")
def genv(tmp_path_factory):
    import test_ss_runner as tr
    root = tmp_path_factory.mktemp("review-g")
    prepared_dir, digest = fx.prepare_dir(root / "prepared")
    recipe = fx.recipe(**G)
    return SimpleNamespace(root=root, prepared=prepared_dir, sha=digest, recipe=recipe, tr=tr,
                           session=runner.Session(recipe, fx.fixture_loaders()))


@pytest.fixture
def direct(genv):
    """The direct init -> e1 run (the spy test's own run when it ran first; made here when a test runs alone)."""
    if getattr(genv, "direct", None) is None:
        genv.direct = runner.run_one(genv.tr.run_job(genv, target_checkpoint="e1", evaluate_bank=None),
                                     prepared_dir=genv.prepared, out_dir=genv.root / "direct", session=genv.session)
    return genv.direct


def _steps(run) -> list[dict]:
    return [json.loads(line) for line in (Path(run["run_dir"]) / "steps.jsonl").read_text().splitlines()]


def _state(run, c) -> dict:
    return json.loads((Path(run["run_dir"]) / "states" / c / "state.json").read_text())


def test_runner_wiring_applied_rate_and_actual_rows(genv, monkeypatch):
    e = genv
    calls = []
    real = en.train_step

    def spy(model, named, optimizer, examples, micro, clip, pad, device, chunk, weighting=en.EXAMPLE_MEAN):
        record = {"rows": [x.row_id for x in examples], "weighting": weighting, "micro": micro,
                  "N": sum(x.n_target for x in examples)}
        original_step = optimizer.step

        def step_and_record(*a, **k):
            record["applied_lrs"] = sorted({g["lr"] for g in optimizer.param_groups})
            record["before"] = en.lora_fingerprint(named)
            out = original_step(*a, **k)
            record["after"] = en.lora_fingerprint(named)
            return out
        optimizer.step = step_and_record
        try:
            return real(model, named, optimizer, examples, micro, clip, pad, device, chunk, weighting)
        finally:
            del optimizer.step
            calls.append(record)
    monkeypatch.setattr(en, "train_step", spy)
    run = runner.run_one(e.tr.run_job(e, target_checkpoint="e1", evaluate_bank=None), prepared_dir=e.prepared,
                         out_dir=e.root / "spy", session=e.session)
    steps = _steps(run)
    peak = e.recipe["train"]["lr"]
    horizon = steps[-1]["step"]
    assert len(calls) == len(steps) == horizon
    for c, s in zip(calls, steps):
        assert c["rows"] == s["rows"] and c["weighting"] == en.TOKEN_MEAN and c["N"] == s["target_tokens"]
        assert c["applied_lrs"] == [s["lr"]], (s["step"], c["applied_lrs"], s["lr"])
        assert s["lr"] == en.learning_rate(peak, "warmup_cosine", 4, horizon, s["step"])
    assert calls[0]["applied_lrs"] == [0.0] and calls[0]["before"] == calls[0]["after"]   # step 1 runs at rate 0
    assert all(c["before"] != c["after"] for c in calls[1:])
    assert len(steps[-1]["rows"]) < max(len(s["rows"]) for s in steps)            # a short final step was trained
    for c in ("q", "e1"):
        assert _state(run, c)["param_groups"][0]["lr"] == peak
    e.direct = run
    print(json.dumps({"review_rates": [s["lr"] for s in steps], "rows_per_step": [len(s["rows"]) for s in steps]}))


def test_resume_from_q_reproduces_rates_and_state(genv, direct):
    e = genv
    short = runner.run_one(e.tr.run_job(e, target_checkpoint="q", evaluate_bank=None), prepared_dir=e.prepared,
                           out_dir=e.root / "short", session=e.session)
    cont = runner.run_one(e.tr.run_job(e, target_checkpoint="e1", evaluate_bank=None, resume_from=short["run_dir"]),
                          prepared_dir=e.prepared, out_dir=e.root / "cont", session=e.session)
    by_step = {s["step"]: s for s in _steps(direct)}
    resumed = _steps(short) + _steps(cont)
    assert [s["step"] for s in resumed] == sorted(by_step)
    for s in resumed:
        d = by_step[s["step"]]
        assert (s["lr"], s["rows"], s["loss"], s["example_losses"], s["grad_norm_preclip"]) == (
            d["lr"], d["rows"], d["loss"], d["example_losses"], d["grad_norm_preclip"]), s["step"]
    for key in ("adapter_fingerprint", "optimizer_fingerprint", "rng_fingerprint", "param_groups"):
        assert _state(cont, "e1")[key] == _state(direct, "e1")[key], key


def test_past_the_horizon_refuses_and_a_removal_arm_uses_its_own_horizon(genv, direct, monkeypatch):
    from experiments.safety_selection.jobs import JobError
    e = genv
    trained = []
    real = en.train_step
    monkeypatch.setattr(en, "train_step", lambda *a, **k: trained.append(1) or real(*a, **k))
    with pytest.raises(JobError, match="lies past the schedule's end"):          # a continuation past the horizon
        runner.run_one(e.tr.run_job(e, target_checkpoint="e3", evaluate_bank=None, resume_from=direct["run_dir"]),
                       prepared_dir=e.prepared, out_dir=e.root / "past", session=e.session)
    with pytest.raises(JobError, match="lies past the schedule's end"):          # a direct init -> e3 job
        runner.run_one(e.tr.run_job(e, target_checkpoint="e3", evaluate_bank=None), prepared_dir=e.prepared,
                       out_dir=e.root / "past-direct", session=e.session)
    assert trained == []                                                         # round 6, M1: nothing trained first
    monkeypatch.setattr(en, "train_step", real)
    view = load_prepared(e.prepared, e.sha, banks=("dev",))
    gid = max(sorted(view.groups["dev"]), key=lambda g: len(view.groups["dev"][g]))
    arm = runner.run_one(e.tr.run_job(e, target_checkpoint="e1", evaluate_bank=None, arm=gid), prepared_dir=e.prepared,
                         out_dir=e.root / "arm", session=e.session)
    steps = _steps(arm)
    horizon = steps[-1]["step"]
    assert horizon <= len(_steps(direct))
    assert [s["lr"] for s in steps] == [en.learning_rate(e.recipe["train"]["lr"], "warmup_cosine", 4, horizon, k)
                                        for k in range(1, horizon + 1)]
    print(json.dumps({"review_removal_arm": {"group": gid, "rows_removed": len(view.groups["dev"][gid]),
                                             "horizon": horizon, "a0_horizon": len(_steps(direct))}}))
