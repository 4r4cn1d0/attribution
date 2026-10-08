"""Checkpoint-gradient attribution features on the a0 trajectory (torch).

Two precisely named variants share one backward pass per query row and per removed row at
each a0 checkpoint c (the row's own mean response-target NLL l_i, i.e. the per-example training loss; under the
token mean the row's share of its step is weighted, see "Loss weighting"; LoRA parameters in sorted-name order;
gradients moved to CPU float64 before any aggregation):

- ``checkpoint_gradsim``: g_Q,c = mean over the supplied query rows of their gradients;
  cos_i,c = <g_i,c, g_Q,c> / (||g_i,c|| ||g_Q,c||); group score = mean over checkpoints of
  (mean over the group's rows of cos_i,c). Scale-free per row, so it ignores group size.
- ``adam_diag_preconditioned_dot``: s_i,c = lr_c * <g_Q,c, g_i,c / (sqrt(vhat_c) + eps)>,
  vhat_c = exp_avg_sq_c / (1 - beta2 ** step_c) per LoRA element from the saved AdamW state at
  c; group score = SUM over the group's rows and SUM over checkpoints.

Sign: positive means a small (preconditioned) descent step on the row would, to first order,
lower the mean query loss, i.e. the row locally supports the query responses; dropping that
step would raise the query loss by about s_i,c (first order, at that checkpoint only).

Limits, by construction: not exact LESS (no projection, cosine of Adam directions or warmup
model), TracIn (no per-step sum; steps between checkpoints ignored), SOURCE or an influence
function, and not a finite-removal estimator. Momentum, gradient clipping, the reshuffled
retained order after removal and every later trajectory change are ignored. Both are
HEURISTICS for the engine's actual intervention, fixed-epoch removal, which deletes rows so
every epoch and the total number of steps shrink and batch composition changes; that is not
the fixed-step, renormalized mean-objective perturbation under which a first-order removal
derivative would be a summed score, and no centered or renormalizing correction is applied
as if it fixed this. With a constant rate the three checkpoints get equal weight whatever the steps between them:
an unequally spaced sum, not an integral over training or a finite-removal theorem (under a warmup schedule each
checkpoint's rate is its interval's mean, see "Learning-rate schedules"). Missing or
zero-step optimizer state raises; nothing is fabricated. Dot products, norms and
preconditioned norms are saved as diagnostics, not extra tuned features; which variant is
primary is frozen in development, never chosen on held-out data.

Loss weighting (GI III round 5). With the default per-example mean, a row's share of its optimizer step is (1/E)
times the gradient of its own loss l_i, the same for every row. With the token mean (``train.loss_weighting``) it is
(n_i / N_step) grad l_i: relative to the per-example mean, row i weighs w_i = n_i * E_step / N_step (n_i its target
tokens; E_step and N_step the examples and target tokens of its step). ``step_weights`` takes each row's step in the
FIRST epoch of the a0 plan (every row trains exactly once per epoch; later epochs reshuffle, so their w_i differ and
are not used). ``adam_diag_preconditioned_dot`` multiplies each row's score by w_i (it is linear in the row's
gradient). ``checkpoint_gradsim`` is a cosine, unchanged by any positive factor on the row, so it needs no weight.
The query side keeps the evaluation's query-loss definition (a per-row mean), as before.

Learning-rate schedules (GI III rounds 5 and 6). ``adam_diag_preconditioned_dot`` multiplies by lr_c. With "constant"
it is the AdamW rate saved with the state at checkpoint c (the peak), as before. With a warmup schedule the saved state
keeps the peak (the runner sets each step's rate only during its update), so the runner passes the INTERVAL MEAN
(``interval_rates``): the checkpoint term at c stands for the updates since the previous attribution checkpoint, so
lr_c = the mean scheduled rate (``engine.learning_rate``) over steps s_prev + 1 .. s_c, where s_prev is the previous
attribution checkpoint's step (0 for the first). The end-point rate of step s_c alone would nearly drop a checkpoint
where a cosine ends (round-5 review). The rates are written to groups.json and the job result (``learning_rates``).
``checkpoint_gradsim`` has no learning rate.

The gradient passes compute each query row's training loss as a by-product; it is recorded
(``query.losses``, ``query.mean_loss``) with the same definition and one-row forward as the
evaluation query loss, so a policy that bought these passes need not buy that forward work
again, and must not be charged for it twice.
"""

from __future__ import annotations

import math
from statistics import fmean
from typing import Any, Callable, Sequence

import torch

from .engine import Named, StateError, ZeroGradientError, example_loss_and_gradient, preserved_rng
from .textproc import TrainExample

__all__ = ["GRADSIM", "ADAM", "DEFINITIONS", "SIGN", "ROW_WEIGHTING", "adam_inverse_preconditioner",
           "gradsim_score", "adam_proxy_score", "checkpoint_scores", "aggregate_groups", "step_weights",
           "interval_rates"]

GRADSIM = "checkpoint_gradsim"
ADAM = "adam_diag_preconditioned_dot"
DEFINITIONS = {
    GRADSIM: "mean over checkpoints of the group's mean per-row cosine between the row's "
             "response-loss LoRA gradient and the mean query-row gradient",
    ADAM: "sum over checkpoints and group rows of lr * <mean query gradient, row gradient / "
          "(sqrt(bias-corrected AdamW second moment) + eps)>",
}
ROW_WEIGHTING = ("token_mean: each row's Adam-proxy score is multiplied by w_i = n_i * E_step / N_step, its weight "
                 "in its first-epoch a0 step relative to the per-example mean; GradSim (a cosine) is unchanged")
SIGN = ("positive: a small descent step on the row lowers the mean query loss to first order "
        "(the row supports the query responses); local, noncausal, not a removal estimate")


def adam_inverse_preconditioner(tensors: dict[str, torch.Tensor], names: Sequence[str],
                                beta2: float, eps: float) -> tuple[torch.Tensor, int]:
    """1 / (sqrt(exp_avg_sq / (1 - beta2**step)) + eps) per LoRA element (float64, sorted-name
    order) and the common AdamW step. Missing state, unequal or non-positive steps refuse."""
    parts, steps = [], set()
    for name in names:
        try:
            second, step = tensors[f"exp_avg_sq/{name}"], tensors[f"step/{name}"]
        except KeyError as exc:
            raise StateError(f"no AdamW second moment/step for {name}") from exc
        value = float(step.reshape(-1)[0])
        if value < 1 or value != int(value):
            raise StateError(f"{name}: AdamW step {value} is not a positive integer")
        steps.add(int(value))
        parts.append(second.reshape(-1).to(torch.float64))
    if len(steps) != 1:
        raise StateError(f"LoRA parameters have different AdamW steps {sorted(steps)}")
    step = steps.pop()
    second = torch.cat(parts)
    if not bool(torch.isfinite(second).all()) or bool((second < 0).any()):
        raise StateError("AdamW second moments must be finite and non-negative")
    vhat = second / (1.0 - beta2 ** step)
    return 1.0 / (vhat.sqrt() + eps), step


def interval_rates(rate: Callable[[int], float], steps: dict[str, int]) -> dict[str, dict]:
    """lr_c per checkpoint: the mean of ``rate(step)`` over steps s_prev + 1 .. s_c, the checkpoints taken in step
    order (s_prev = 0 for the first); module doc. A checkpoint at step 0 or two at one step refuse."""
    out, previous = {}, 0
    for name, step in sorted(steps.items(), key=lambda item: item[1]):
        if step <= previous:
            raise ValueError(f"checkpoint {name} at step {step} has no updates since step {previous}")
        rates = [rate(s) for s in range(previous + 1, step + 1)]
        out[name] = {"lr": math.fsum(rates) / len(rates), "first_step": previous + 1, "last_step": step,
                     "rule": "mean scheduled rate over the updates since the previous attribution checkpoint"}
        previous = step
    return out


def step_weights(plan: Any, target_tokens: dict[str, int], rows: Sequence[str]) -> dict[str, float]:
    """w_i = n_i * E_step / N_step for each row, from its step in the plan's first epoch (module doc)."""
    order, size = plan.epoch_order(0), plan.effective_batch
    weight = {}
    for start in range(0, len(order), size):
        step = order[start:start + size]
        total = sum(target_tokens[r] for r in step)
        for r in step:
            weight[r] = target_tokens[r] * len(step) / total
    missing = [r for r in rows if r not in weight]
    if missing:
        raise ValueError(f"{len(missing)} attributed rows are not in the plan's first epoch")
    return {r: weight[r] for r in rows}


def gradsim_score(row: torch.Tensor, query_mean: torch.Tensor) -> float:
    norm_row, norm_query = float(row.norm()), float(query_mean.norm())
    if norm_row == 0.0 or norm_query == 0.0:
        raise ZeroGradientError("cosine with a zero gradient is undefined")
    return float(row @ query_mean) / (norm_row * norm_query)


def adam_proxy_score(row: torch.Tensor, query_mean: torch.Tensor, inverse: torch.Tensor,
                     lr: float) -> float:
    if not row.shape == query_mean.shape == inverse.shape:
        raise ValueError("gradient and preconditioner sizes differ")
    return lr * float((row * inverse) @ query_mean)


def checkpoint_scores(model: Any, named: Named, queries: Sequence[TrainExample],
                      rows: Sequence[TrainExample], *, inverse: torch.Tensor, lr: float,
                      pad_id: int, device: str, chunk: int,
                      check: Callable[[str], None] | None = None,
                      weights: dict[str, float] | None = None) -> dict:
    """Per-row features at one checkpoint. Eval mode and RNG states are restored afterwards;
    gradients come from autograd.grad, so weights, ``.grad`` and optimizer are untouched. Each
    query's and row's (finite) training loss from the same forward pass is recorded."""
    check = check or (lambda what: None)
    if not queries or not rows:
        raise ValueError("need at least one query row and one removed row")
    was_training = model.training
    model.eval()
    try:
        with preserved_rng(device):
            total, query_norms, query_losses = None, {}, {}
            for ex in queries:
                check(f"query gradient {ex.row_id}")
                loss, g = example_loss_and_gradient(model, named, ex, pad_id=pad_id, device=device,
                                                    chunk=chunk)
                query_norms[ex.row_id] = float(g.norm())
                query_losses[ex.row_id] = loss
                total = g if total is None else total + g
            query_mean = total / len(queries)
            out_rows = {}
            for ex in rows:
                check(f"row gradient {ex.row_id}")
                loss, g = example_loss_and_gradient(model, named, ex, pad_id=pad_id, device=device,
                                                    chunk=chunk)
                out_rows[ex.row_id] = {
                    "cosine": gradsim_score(g, query_mean), "dot": float(g @ query_mean),
                    "grad_norm": float(g.norm()), "loss": loss,
                    "adam_score": adam_proxy_score(g, query_mean, inverse, lr),
                    "preconditioned_grad_norm": float((g * inverse).norm())}
                if weights is not None:          # the token mean (module doc): the Adam proxy follows the step weight
                    out_rows[ex.row_id]["weight"] = weights[ex.row_id]
                    out_rows[ex.row_id]["adam_score"] *= weights[ex.row_id]
    finally:
        model.train(was_training)
    return {"query": {"n": len(queries), "mean_gradient_norm": float(query_mean.norm()),
                      "example_gradient_norms": query_norms, "losses": query_losses,
                      "mean_loss": fmean(query_losses.values()),
                      "inverse_preconditioner": {"min": float(inverse.min()),
                                                 "max": float(inverse.max()),
                                                 "mean": float(inverse.mean())}},
            "rows": out_rows}


def aggregate_groups(per_checkpoint: dict[str, dict], groups: dict[str, Sequence[str]]) -> dict:
    """Group scores: GradSim = mean over checkpoints of the group's mean cosine; Adam proxy =
    sum over checkpoints of the group's summed row scores. Per-checkpoint parts and
    diagnostics (dot sums and means, gradient norms, cosine range) are kept."""
    names = list(per_checkpoint)
    out = {}
    for gid, members in groups.items():
        parts = {}
        for c in names:
            rows = [per_checkpoint[c]["rows"][m] for m in members]
            cosines = [r["cosine"] for r in rows]
            parts[c] = {"mean_cosine": fmean(cosines), "min_cosine": min(cosines),
                        "max_cosine": max(cosines),
                        "adam_sum": math.fsum(r["adam_score"] for r in rows),
                        "dot_sum": math.fsum(r["dot"] for r in rows),
                        "dot_mean": fmean(r["dot"] for r in rows),
                        "grad_norm_mean": fmean(r["grad_norm"] for r in rows)}
        out[gid] = {"size": len(members),
                    GRADSIM: fmean(parts[c]["mean_cosine"] for c in names),
                    ADAM: math.fsum(parts[c]["adam_sum"] for c in names),
                    "per_checkpoint": parts}
    return out
