"""Attribution math on exact fixtures: the Adam-diagonal-preconditioned proxy against a closed
form on a quadratic problem (with real AdamW moments), its sign as a first-order prediction,
GradSim scale invariance, mean-versus-sum group aggregation (a ranking counterexample),
refusal of missing or zero-step optimizer state, and the per-checkpoint pass on the tiny
ENGINEERING FIXTURE model (weights, RNG, mode, .grad and optimizer untouched)."""

from __future__ import annotations

import math

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

from experiments.safety_selection import attribution as at  # noqa: E402
from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import textproc as tp  # noqa: E402

F64 = torch.float64


def test_adam_proxy_equals_its_closed_form_with_real_adamw_moments():
    theta = torch.nn.Parameter(torch.tensor([0.5, -1.0, 2.0], dtype=F64))
    a0 = torch.tensor([[1.0, 0.0, 2.0], [0.0, 1.0, -1.0]], dtype=F64)
    b0 = torch.tensor([1.0, -2.0], dtype=F64)
    a1 = torch.tensor([[0.5, 1.5, 0.0]], dtype=F64)
    b1 = torch.tensor([3.0], dtype=F64)
    lr, beta1, beta2, eps = 0.05, 0.9, 0.99, 1e-8
    optimizer = torch.optim.AdamW([theta], lr=lr, betas=(beta1, beta2), eps=eps, weight_decay=0.0)
    history = []
    for _ in range(3):  # three real AdamW steps on the training objective
        optimizer.zero_grad()
        (0.5 * ((a0 @ theta - b0) ** 2).sum() + 0.5 * ((a1 @ theta - b1) ** 2).sum()).backward()
        history.append(theta.grad.detach().clone())
        optimizer.step()
    inverse, step = at.adam_inverse_preconditioner(en.optimizer_tensors(optimizer, [("w", theta)]), ["w"],
                                                   beta2, eps)
    second = torch.zeros(3, dtype=F64)
    for g in history:
        second = beta2 * second + (1 - beta2) * g * g
    vhat = second / (1 - beta2 ** 3)
    assert step == 3
    assert torch.allclose(inverse, 1 / (vhat.sqrt() + eps), rtol=1e-12, atol=0)
    with torch.no_grad():
        query = theta.detach() - torch.tensor([1.0, 1.0, 0.0], dtype=F64)  # grad of 0.5||theta - q||^2
        row = a0.T @ (a0 @ theta.detach() - b0)  # grad of row 0's loss
    closed = lr * sum(float(query[k]) * float(row[k]) / (math.sqrt(float(vhat[k])) + eps) for k in range(3))
    assert at.adam_proxy_score(row, query, inverse, lr) == pytest.approx(closed, rel=1e-12)


def test_the_proxy_sign_predicts_the_first_order_query_loss_change_of_a_preconditioned_step():
    theta = torch.tensor([0.3, -0.2, 0.7], dtype=F64)
    target_query = torch.tensor([1.0, 0.5, 0.0], dtype=F64)
    inverse = torch.tensor([2.0, 0.5, 1.0], dtype=F64)
    lr = 1e-4

    def query_loss(t: torch.Tensor) -> float:
        return 0.5 * float(((t - target_query) ** 2).sum())

    signs = set()
    for target in ([2.0, 1.0, 0.0], [-1.0, -2.0, 1.5], [0.3, 1.0, 5.0]):
        row = theta - torch.tensor(target, dtype=F64)  # grad of the row loss 0.5||theta - target||^2
        score = at.adam_proxy_score(row, theta - target_query, inverse, lr)
        change = query_loss(theta - lr * row * inverse) - query_loss(theta)
        assert (score > 0) == (change < 0)
        assert change == pytest.approx(-score, rel=1e-3)
        signs.add(score > 0)
    assert signs == {True, False}


def test_gradsim_is_scale_free_and_groups_average_cosines_but_sum_adam_scores():
    query = torch.tensor([1.0, 0.0], dtype=F64)
    row = torch.tensor([3.0, 4.0], dtype=F64)
    assert at.gradsim_score(row, query) == pytest.approx(0.6)
    assert at.gradsim_score(10 * row, 0.1 * query) == pytest.approx(0.6)
    with pytest.raises(en.ZeroGradientError):
        at.gradsim_score(torch.zeros(2, dtype=F64), query)

    def record(cosine: float) -> dict:
        return {"cosine": cosine, "adam_score": 1.0, "dot": 1.0, "grad_norm": 1.0}

    rows = {**{f"big{i}": record(0.1) for i in range(64)}, **{f"small{i}": record(0.9) for i in range(8)}}
    per_checkpoint = {c: {"rows": rows} for c in ("q", "e1", "e3")}
    groups = {"big": [f"big{i}" for i in range(64)], "small": [f"small{i}" for i in range(8)]}
    out = at.aggregate_groups(per_checkpoint, groups)
    # The variants rank these removals oppositely: GradSim ignores size, the summed proxy grows with it.
    assert out["small"][at.GRADSIM] == pytest.approx(0.9) and out["big"][at.GRADSIM] == pytest.approx(0.1)
    assert out["big"][at.ADAM] == pytest.approx(192.0) and out["small"][at.ADAM] == pytest.approx(24.0)
    assert out["big"]["per_checkpoint"]["e1"]["dot_sum"] == pytest.approx(64.0)


def test_missing_unequal_or_zero_step_optimizer_state_is_refused():
    ones = torch.ones(2, dtype=F64)
    with pytest.raises(en.StateError, match="positive integer"):
        at.adam_inverse_preconditioner({"exp_avg_sq/w": ones, "step/w": torch.tensor([0.0])}, ["w"], 0.999, 1e-8)
    with pytest.raises(en.StateError, match="no AdamW"):
        at.adam_inverse_preconditioner({"step/w": torch.tensor([1.0])}, ["w"], 0.999, 1e-8)
    with pytest.raises(en.StateError, match="different AdamW steps"):
        at.adam_inverse_preconditioner({"exp_avg_sq/a": ones, "step/a": torch.tensor([2.0]),
                                        "exp_avg_sq/b": ones, "step/b": torch.tensor([3.0])},
                                       ["a", "b"], 0.999, 1e-8)
    with pytest.raises(en.StateError, match="non-negative"):
        at.adam_inverse_preconditioner({"exp_avg_sq/w": -ones, "step/w": torch.tensor([1.0])}, ["w"], 0.999, 1e-8)
    fresh = torch.optim.AdamW([torch.nn.Parameter(ones.clone())])
    assert en.optimizer_tensors(fresh, [("w", fresh.param_groups[0]["params"][0])]) == {}


def test_checkpoint_scores_match_manual_gradients_and_touch_nothing(tiny, codec):
    model, named = tiny
    examples = [tp.encode_train(codec, f"r-{i}", f"prompt {i}", f"response {'z' * i} {i} !", 256) for i in range(6)]
    optimizer = en.make_optimizer(named, {"lr": 0.01, "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.0})
    for batch in (examples[:3], examples[3:]):
        en.train_step(model, named, optimizer, batch, 2, 1.0, codec.pad_id, "cpu", 8)
    inverse, step = at.adam_inverse_preconditioner(en.optimizer_tensors(optimizer, named),
                                                   [n for n, _ in named], 0.999, 1e-8)
    assert step == 2
    model.train()
    before = (en.lora_fingerprint(named), en.optimizer_fingerprint(optimizer, named), en.rng_digest("cpu"))
    queries, rows = examples[:2], examples[2:]
    seen: list[str] = []
    out = at.checkpoint_scores(model, named, queries, rows, inverse=inverse, lr=0.01, pad_id=codec.pad_id,
                               device="cpu", chunk=8, check=seen.append)
    assert model.training and all(p.grad is None for _, p in named)
    assert (en.lora_fingerprint(named), en.optimizer_fingerprint(optimizer, named), en.rng_digest("cpu")) == before
    assert seen == [f"query gradient r-{i}" for i in (0, 1)] + [f"row gradient r-{i}" for i in (2, 3, 4, 5)]
    grads = {e.row_id: en.example_gradient(model, named, e, pad_id=codec.pad_id, device="cpu", chunk=8)
             for e in examples}
    query = (grads["r-0"] + grads["r-1"]) / 2
    for e in rows:
        g, rec = grads[e.row_id], out["rows"][e.row_id]
        assert rec["cosine"] == pytest.approx(float(g @ query / (g.norm() * query.norm())), rel=1e-9)
        assert rec["dot"] == pytest.approx(float(g @ query), rel=1e-9)
        assert rec["adam_score"] == pytest.approx(0.01 * float((g * inverse) @ query), rel=1e-9)
        assert rec["grad_norm"] == pytest.approx(float(g.norm()), rel=1e-12)
    assert out["query"]["mean_gradient_norm"] == pytest.approx(float(query.norm()), rel=1e-12)
    # The gradient passes' query losses are the forward-only query losses (charged once).
    forward = en.query_losses(model, queries, pad_id=codec.pad_id, device="cpu", chunk=8)
    assert [out["query"]["losses"][q.row_id] for q in queries] == pytest.approx(forward, rel=1e-6)
    assert out["query"]["mean_loss"] == pytest.approx(sum(forward) / len(forward), rel=1e-6)
    rows_forward = en.query_losses(model, rows, pad_id=codec.pad_id, device="cpu", chunk=8)
    assert [out["rows"][e.row_id]["loss"] for e in rows] == pytest.approx(rows_forward, rel=1e-6)
