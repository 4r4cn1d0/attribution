"""Checkpoint-gradient attribution features on the a0 trajectory (torch).

Two precisely named variants share one backward pass per query row and per removed row at
each a0 checkpoint c (per-example response-only loss, the training loss; LoRA parameters in
sorted-name order; gradients moved to CPU float64 before any aggregation):

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
as if it fixed this. The three checkpoints get equal weight whatever the steps between them:
an unequally spaced sum, not an integral over training or a finite-removal theorem. Missing or
zero-step optimizer state raises; nothing is fabricated. Dot products, norms and
preconditioned norms are saved as diagnostics, not extra tuned features; which variant is
primary is frozen in development, never chosen on held-out data.

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

__all__ = ["GRADSIM", "ADAM", "DEFINITIONS", "SIGN", "adam_inverse_preconditioner",
           "gradsim_score", "adam_proxy_score", "checkpoint_scores", "aggregate_groups"]

GRADSIM = "checkpoint_gradsim"
ADAM = "adam_diag_preconditioned_dot"
DEFINITIONS = {
    GRADSIM: "mean over checkpoints of the group's mean per-row cosine between the row's "
             "response-loss LoRA gradient and the mean query-row gradient",
    ADAM: "sum over checkpoints and group rows of lr * <mean query gradient, row gradient / "
          "(sqrt(bias-corrected AdamW second moment) + eps)>",
}
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
                      check: Callable[[str], None] | None = None) -> dict:
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
