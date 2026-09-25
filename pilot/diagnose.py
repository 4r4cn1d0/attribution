"""Mechanism diagnostic of the v1 headroom run: which coupling decision loses variance, and why.

    python -m pilot.diagnose --input research/pilot/runs/20260924T150726Z --output research/pilot/diagnostics-v1

The frozen manifest (SHA256 fixed below) is read from the run directory's grandparent. Every H1/H2
manifest cell must have one completed record whose stored checks all passed, whose target equals
its manifest entry and whose values read here are finite JSON numbers of v1's type; H4 cells must
have none. Anything else is rejected before analysis.

Every H1/H2 record's stored variances must follow pilot.pair's convention on its stored moments,
and its headroom block (best method and variance, oracle and terminal variances, nondegenerate flag,
ratios) must equal pilot.headroom's definitions on those variances, within 1e-15 (ties at the
minimum allowed). H1 is otherwise checked from stored values only: the 'ordered' key orders the
terminal scores, so 'ordered' must equal the oracle and the terminal-OT bound. Every H2 cell is
recomputed with the public process and couplings APIs. With x suppressed, y ordinary, C[a][b] the
oracle value of child pair (U_a x, U_b y) with one event left, pi* an optimal root plan and, for
ordinary method m, root plan pi^m and last-step second moments W^m,

    E_m[Y^2] - V* = R0(m) + R1(m),   R0 = sum (pi^m - pi*) C,   R1 = sum pi^m (W^m - C).

R0 is the root decision's regret, and also the entire regret of 'm at the root, sorted at the last
step'; R1 is the last decision's. Means are coupling-invariant, so second-moment regret equals
variance regret. C is recomputed by merging quantile functions and V* by enumerating every transport
basis, neither with an LP solver; method moments come from an own depth-first enumeration, and the
terminal-OT second moment from the two exact terminal laws. All are compared with the stored values
at 1e-12 absolute, as are the stored oracle and terminal means with the recomputed delta. Plans are
used as checked, never renormalised. Mechanism covariates (stochastic order and Monge property of C
in key and child-mean order, action agreement, residuals without fixed_label, allocation counts) are
properties of the same trees or re-summaries of stored variances; no new coupling rule is evaluated.

Writes diagnostics.json, h2_cells.csv and h2_groups.csv into --output only when every check passes;
never writes into --input. Exit status: 0 on success; 1 on rejected input or a failed check (JSON on
stdout with "ok": false, nothing written); 2 for argparse errors.
"""

from __future__ import annotations

import argparse
import csv
import functools
import hashlib
import io
import itertools
import json
import math
import os
import platform
import re
import resource
import statistics
import sys
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from numpy.typing import NDArray

from .couplings import distribution, fixed_label, independent, maximal, ordered, shared_gumbel, transport
from .pair import ORDINARY_METHODS
from .process import Config, State, canonical_config, initial_state, intervention_pair, probs, score, successors

__all__ = [
    "Tree", "MethodTerms", "quantile_pairs", "w2_squared", "vertex_minimum", "order_status",
    "monge_violation", "build_tree", "continuation_costs", "method_terms", "load_run", "run", "main",
]

EXPECTED_MANIFEST_SHA256 = "62f7bcc4d85d291bca20234b68fe3c3d287bdc2401afeaa4c1022f7dc1c57999"
MANIFEST_NAME = "headroom-manifest-v1.json"
WITNESSES = ("27f1126e6c329784", "d7fbdd78951f35b0", "24a16ed9956c3de3")
PARTNERS = {"A1": ("A2", "A3"), "A2": ("A1", "A3"), "A3": ("A1", "A2"), "B1": ("B2",), "B2": ("B1",)}
TOL = 1e-12            # absolute, second-moment units: the pilot's fixed check tolerance
LAW_TOL = 1e-15        # recomputed versus stored root laws (same function on the same states)
MIN_ENTRY = -1e-14     # smallest allowed plan entry, as in pilot.couplings
ORDER_TOL = 1e-12      # CDF comparison slack for stochastic order
MONGE_TOL = 1e-15      # a positive 2x2 interaction above this is a Monge violation
ZERO_FRACTION = 1e-6   # regret below this fraction of the best ordinary variance counts as zero
NONDEGENERATE = 1e-14  # the pilot's nondegenerate best-variance threshold
VARIANCE_ROUNDOFF = 1e-14  # pilot.pair: second - mean**2 in [-1e-14, 0) is stored as 0; lower is invalid
# Stored variances and headroom fields against v1's float64 expressions on the same stored values
# (reproduced exactly on v1 data); variance units, ratios relative to max(1, |value|).
SUMMARY_TOL = 1e-15
SUMMARY_CHECKS = ("stored_variance_vs_moments", "stored_best_variance_vs_six_methods",
                  "stored_headroom_vs_oracle_and_terminal", "stored_nondegenerate_and_ratios")
RATIOS = ("oracle_variance_reduction", "oracle_suboptimality_estimate_over_best_variance")
RMSE_TARGETS = (0.02, 0.01, 0.005)
OUTPUTS = ("diagnostics.json", "h2_cells.csv", "h2_groups.csv")
SOURCES = ("__init__.py", "process.py", "couplings.py", "exact.py", "pair.py", "headroom.py")
RUN_FILES = ("metadata.json", "summary.json", "metrics.json", "cells.csv", "groups.csv", "slots.csv",
             "independent-witness-checks.json")
CELL_FILE = re.compile(r"[0-9a-f]{16}\.json")
KEY_RULES = ("ordered", "distance")  # rules that evaluate all K candidate successors per step
# The five rules other than fixed_label: a descriptive sensitivity subset, not a relabelling-invariant
# class ('ordered' breaks key ties by action ID; 'distance' keeps the LP's pick among tied optima).
WITHOUT_FIXED_LABEL = tuple(m for m in ORDINARY_METHODS if m != "fixed_label")


# ----------------------------------------------------------------------------- numerical pieces


def quantile_pairs(p: Sequence[float], s: Sequence[float], q: Sequence[float],
                   t: Sequence[float]) -> list[tuple[float, int, int]]:
    """Segments (mass, i, j) of the sorted coupling of law p on atoms s with law q on atoms t.

    One uniform u passes through both inverse CDFs; atoms ascend with ties by index. Breakpoints
    are compensated cumulative sums and zero-length segments are dropped. Nothing is renormalised:
    if the two totals differ by rounding, the unmatched tail is left out.
    """
    op = sorted(range(len(s)), key=lambda i: (s[i], i))
    oq = sorted(range(len(t)), key=lambda j: (t[j], j))
    cp = [math.fsum(p[i] for i in op[:n + 1]) for n in range(len(op))]
    cq = [math.fsum(q[j] for j in oq[:n + 1]) for n in range(len(oq))]
    out, prev, i, j = [], 0.0, 0, 0
    while i < len(op) and j < len(oq):
        cut = min(cp[i], cq[j])
        if cut > prev:
            out.append((cut - prev, op[i], oq[j]))
            prev = cut
        i += cp[i] <= cut
        j += cq[j] <= cut
    return out


def w2_squared(p: Sequence[float], s: Sequence[float], q: Sequence[float], t: Sequence[float]) -> float:
    """Integral over u of (F^-1(u) - G^-1(u))**2: the minimum E[(S - T)**2] over couplings."""
    return math.fsum(m * (s[i] - t[j]) ** 2 for m, i, j in quantile_pairs(p, s, q, t))


def sorted_plan(p: Sequence[float], s: Sequence[float], q: Sequence[float],
                t: Sequence[float]) -> NDArray[np.float64]:
    """Matrix form of :func:`quantile_pairs`."""
    plan = np.zeros((len(p), len(q)))
    for m, i, j in quantile_pairs(p, s, q, t):
        plan[i, j] += m
    return plan


@functools.lru_cache(maxsize=None)
def _bases(k: int) -> tuple[tuple[tuple[int, ...], NDArray[np.float64]], ...]:
    """Every support of 2k - 1 cells with independent transport constraints, with its pseudo-inverse."""
    rows = np.zeros((2 * k, k * k))
    for n in range(k * k):
        rows[n // k, n] = rows[k + n % k, n] = 1.0
    out = []
    for support in itertools.combinations(range(k * k), 2 * k - 1):
        m = rows[:, support]
        if np.linalg.matrix_rank(m) == 2 * k - 1:
            out.append((support, np.linalg.pinv(m)))
    return tuple(out)


def vertex_minimum(p: Sequence[float], q: Sequence[float], cost: Any) -> float:
    """min over plans with marginals p and q of sum(plan * cost), by enumerating every basis.

    No LP solver: each of the candidate bases (81 for K=3) gives one basic solution; the feasible
    ones (constraint residual and negativity within 1e-12) are the vertices, and how many there are
    depends on p and q. They are costed with fsum. Raises ValueError if none is feasible.
    """
    k = len(p)
    c = np.asarray(cost, dtype=np.float64).ravel()
    rhs = np.concatenate((np.asarray(p, dtype=np.float64), np.asarray(q, dtype=np.float64)))
    rows = np.zeros((2 * k, k * k))
    for n in range(k * k):
        rows[n // k, n] = rows[k + n % k, n] = 1.0
    best = math.inf
    for support, pinv in _bases(k):
        x = pinv @ rhs
        if x.min() >= -TOL and np.abs(rows[:, support] @ x - rhs).max() <= TOL:
            best = min(best, math.fsum((x * c[list(support)]).tolist()))
    if best == math.inf:
        raise ValueError("no feasible transport vertex")
    return best


def order_status(lo: tuple[Any, Any], hi: tuple[Any, Any]) -> str:
    """Stochastic order of two one-step terminal laws (weights, atoms) whose keys satisfy lo <= hi.

    'ordered': hi's law first-order dominates lo's (CDF of hi <= CDF of lo + 1e-12 everywhere).
    'weights': not ordered, yet every action's atom from hi is >= its atom from lo, so equal
    weights would be ordered and the failure needs the action-probability difference.
    'atoms': not ordered and some action's atom is reversed (non-comonotone same-action atoms).
    This names the pattern only: the weights may differ as well, so it does not isolate a causal
    effect of successor geometry from changing probabilities.
    """
    p_lo, s_lo = (np.asarray(v, dtype=np.float64) for v in lo)
    p_hi, s_hi = (np.asarray(v, dtype=np.float64) for v in hi)
    for z in sorted(set(s_lo.tolist()) | set(s_hi.tolist())):
        if math.fsum(p_hi[s_hi <= z].tolist()) > math.fsum(p_lo[s_lo <= z].tolist()) + ORDER_TOL:
            return "weights" if bool(np.all(s_hi >= s_lo)) else "atoms"
    return "ordered"


def monge_violation(cost: Any, rows: Sequence[int], cols: Sequence[int]) -> float:
    """Largest positive adjacent 2x2 interaction M[i,j] + M[i+1,j+1] - M[i,j+1] - M[i+1,j] of the
    cost with rows and columns in the given orders (0.0 if Monge; adjacent minors suffice)."""
    m = np.asarray(cost, dtype=np.float64)[np.ix_(list(rows), list(cols))]
    minors = m[:-1, :-1] + m[1:, 1:] - m[:-1, 1:] - m[1:, :-1]
    return max(0.0, float(minors.max()))


def _interactions(cost: Any) -> list[list[float]]:
    """All 2x2 interactions in label order, rows (a, a') x columns (b, b'), a < a' and b < b'.

    They are the part of a cost invariant to adding row-only and column-only terms."""
    m = np.asarray(cost, dtype=np.float64)
    pairs = list(itertools.combinations(range(len(m)), 2))
    return [[float(m[a, b] + m[a2, b2] - m[a, b2] - m[a2, b]) for b, b2 in pairs] for a, a2 in pairs]


# ----------------------------------------------------------------------------- the H = 2 tree


@dataclass(frozen=True)
class Tree:
    """Everything below one H=2 intervention pair: x suppressed, y ordinary, weight-1 future events.

    px, py are the root laws; xs[a] = U_a(x); P[a] the law at xs[a]; xs2[a][c] = U_c(U_a(x));
    s[a, c] its score. Likewise ys, Q, ys2 and t for the ordinary world."""

    config: Config
    x: State
    y: State
    px: NDArray[np.float64]
    py: NDArray[np.float64]
    xs: tuple[State, ...]
    ys: tuple[State, ...]
    P: tuple[NDArray[np.float64], ...]
    Q: tuple[NDArray[np.float64], ...]
    xs2: tuple[tuple[State, ...], ...]
    ys2: tuple[tuple[State, ...], ...]
    s: NDArray[np.float64]
    t: NDArray[np.float64]


def build_tree(config: Config, pre_state: State, action: int, alpha: float) -> Tree:
    """Exact H=2 tree from `intervention_pair`; laws are validated, never renormalised."""
    x, y = intervention_pair(config, pre_state, action, alpha)
    xs, ys = successors(config, x), successors(config, y)
    xs2 = tuple(successors(config, u) for u in xs)
    ys2 = tuple(successors(config, v) for v in ys)
    return Tree(config, x, y, distribution("p(x)", probs(config, x)), distribution("p(y)", probs(config, y)),
                xs, ys, tuple(distribution("p(U_a x)", probs(config, u)) for u in xs),
                tuple(distribution("p(U_b y)", probs(config, v)) for v in ys), xs2, ys2,
                np.array([[score(config, w) for w in row] for row in xs2]),
                np.array([[score(config, w) for w in row] for row in ys2]))


def continuation_costs(tree: Tree) -> NDArray[np.float64]:
    """C[a][b]: minimum last-step E[Y**2] below child pair (U_a x, U_b y), by quantile merging."""
    k = tree.config.n_actions
    return np.array([[w2_squared(tree.P[a], tree.s[a], tree.Q[b], tree.t[b]) for b in range(k)]
                     for a in range(k)])


def _keys(config: Config, states: Sequence[State]) -> list[float]:
    """The 'ordered' baseline's keys: targets (family A) or the successor's q-coordinate (B)."""
    if config.family == "A":
        return list(config.targets)
    return [float(np.dot(config.q, s.theta)) for s in states]


def _order(keys: Sequence[float]) -> list[int]:
    return [int(i) for i in np.argsort(np.asarray(keys, dtype=np.float64), kind="stable")]


def _rule(method: str, config: Config, p: NDArray[np.float64], q: NDArray[np.float64],
          us: Sequence[State], vs: Sequence[State]) -> NDArray[np.float64]:
    """Checked plan of ordinary `method` at one pair node, with pilot.pair's rule for each method."""
    if method == "independent":
        return independent(p, q).matrix
    if method == "fixed_label":
        return fixed_label(p, q).matrix
    if method == "maximal":
        return maximal(p, q).matrix
    if method == "shared_gumbel":
        return shared_gumbel(p, q).matrix
    if method == "ordered":
        return ordered(p, q, _keys(config, us), _keys(config, vs)).matrix
    if method == "distance":
        cost = [[math.fsum((a - b) ** 2 for a, b in zip(u.theta, v.theta)) for v in vs] for u in us]
        return transport(p, q, cost).matrix
    raise ValueError(f"unknown method {method!r}; expected one of {ORDINARY_METHODS}")


@dataclass(frozen=True)
class MethodTerms:
    """Exact moments and regret split of one plan tree (children: visited child pair -> plan).

    agree_mass / agree_second_moment cover paths with equal actions in both worlds at both steps."""

    method: str
    root: NDArray[np.float64]
    children: dict[tuple[int, int], NDArray[np.float64]]
    second_moment: float
    mean: float
    r0: float
    r1: float
    agree_mass: float
    agree_second_moment: float


def _terms(method: str, tree: Tree, root: NDArray[np.float64],
           child_rule: Callable[[int, int], NDArray[np.float64]], C: NDArray[np.float64],
           v_star: float) -> MethodTerms:
    second, first, excess, agree_mass, agree_second = [], [], [], [], []
    children = {}
    for a, b in zip(*np.nonzero(root)):  # like pilot.pair: every nonzero entry is visited
        a, b = int(a), int(b)
        child = child_rule(a, b)
        diff = np.subtract.outer(tree.s[a], tree.t[b])
        w = math.fsum((child * (diff * diff)).ravel().tolist())
        mass = float(root[a, b])
        second.append(mass * w)
        first.append(mass * math.fsum((child * diff).ravel().tolist()))
        excess.append(mass * (w - float(C[a, b])))
        if a == b:
            agree_mass.append(mass * math.fsum(np.diag(child).tolist()))
            agree_second.append(mass * math.fsum((np.diag(child) * np.diag(diff) ** 2).tolist()))
        children[(a, b)] = child
    r0 = math.fsum([*(root * C).ravel().tolist(), -v_star])
    return MethodTerms(method, root, children, math.fsum(second), math.fsum(first), r0,
                       math.fsum(excess), math.fsum(agree_mass), math.fsum(agree_second))


def method_terms(method: str, tree: Tree, C: NDArray[np.float64], v_star: float) -> MethodTerms:
    """Ordinary `method` at both decisions of the H=2 tree, with R0 and R1 against (C, V*)."""
    cfg = tree.config
    root = _rule(method, cfg, tree.px, tree.py, tree.xs, tree.ys)
    return _terms(method, tree, root,
                  lambda a, b: _rule(method, cfg, tree.P[a], tree.Q[b], tree.xs2[a], tree.ys2[b]), C, v_star)


def hybrid_terms(root_method: str, tree: Tree, C: NDArray[np.float64], v_star: float) -> MethodTerms:
    """`root_method` at the root, then the production 'ordered' plan at the last step.

    Its regret equals R0(root_method) exactly when 'ordered' keys order the terminal scores."""
    cfg = tree.config
    root = _rule(root_method, cfg, tree.px, tree.py, tree.xs, tree.ys)
    return _terms(f"{root_method}+ordered", tree, root,
                  lambda a, b: _rule("ordered", cfg, tree.P[a], tree.Q[b], tree.xs2[a], tree.ys2[b]), C, v_star)


def _same_plans(u: MethodTerms, v: MethodTerms) -> bool:
    """Equal root plans and equal plans at every child pair carrying root mass (1e-12)."""
    if np.abs(u.root - v.root).max() > TOL:
        return False
    for key in set(u.children) | set(v.children):
        if key in u.children and key in v.children:
            if np.abs(u.children[key] - v.children[key]).max() > TOL:
                return False
        elif abs(float((u.root if key in u.children else v.root)[key])) > TOL:
            return False
    return True


def _agreement(root: NDArray[np.float64], children: dict[tuple[int, int], NDArray[np.float64]],
               tree: Tree) -> dict[str, float]:
    total = [float(root[a, b]) * math.fsum((plan * np.subtract.outer(tree.s[a], tree.t[b]) ** 2).ravel().tolist())
             for (a, b), plan in children.items()]
    mass = [float(root[a, a]) * math.fsum(np.diag(plan).tolist()) for (a, b), plan in children.items() if a == b]
    agree = [float(root[a, a]) * math.fsum((np.diag(plan) * (tree.s[a] - tree.t[a]) ** 2).tolist())
             for (a, b), plan in children.items() if a == b]
    second = math.fsum(total)
    return {"second_moment": second, "agree_mass": math.fsum(mass), "mismatch_mass": 1.0 - math.fsum(mass),
            "agree_second_moment": math.fsum(agree), "mismatch_second_moment": second - math.fsum(agree)}


# ----------------------------------------------------------------------------- input validation


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f"unreadable JSON {path}: {exc}") from exc


def _number(value: Any) -> bool:
    """A finite real JSON number: not a bool, null, string, NaN or Infinity."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _invalid_stored_values(result: dict[str, Any]) -> list[str]:
    """Stored fields read here that lack v1's type: finite numbers, a known method name, a bool
    flag, and ratios that are finite numbers when that flag is true and null otherwise."""
    def get(*path: str) -> Any:
        node: Any = result
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
        return node

    blocks = [("ordinary", m) for m in ORDINARY_METHODS] + [("oracle",), ("terminal_lower_bound",)]
    numbers = [(*b, f) for b in blocks for f in ("mean", "second_moment", "variance")] + [
        ("oracle", "suboptimality_estimate"), ("marginal_truth", "delta"), ("marginal_truth", "action_probability"),
        ("headroom", "best_ordinary_variance"), ("headroom", "oracle_variance"),
        ("headroom", "terminal_lower_bound_variance")]
    bad = [".".join(p) for p in numbers if not _number(get(*p))]
    if get("headroom", "best_ordinary_method") not in ORDINARY_METHODS:
        bad.append("headroom.best_ordinary_method")
    flag = get("headroom", "nondegenerate")
    if not isinstance(flag, bool):
        bad.append("headroom.nondegenerate")
    bad += [f"headroom.{k}" for k in RATIOS
            if not (_number(get("headroom", k)) if flag is True else get("headroom", k) is None)]
    return bad


def _check_record(cell: dict[str, Any], record: Any) -> None:
    cid = cell["cell_id"]
    if not isinstance(record, dict) or record.get("target") != cell:
        raise ValueError(f"{cid}: record target differs from its manifest entry")
    if record.get("status") != "completed":
        raise ValueError(f"{cid}: status {record.get('status')!r}, expected 'completed'")
    result = record.get("result")
    checks = result.get("checks") if isinstance(result, dict) else None
    if not (isinstance(checks, dict) and checks and all(v is True for v in checks.values())
            and result.get("ok") is True):
        raise ValueError(f"{cid}: record is not ok or a stored check failed")
    dim = 1 if cell["family"].startswith("A") else 2
    expected = {"structure": cell["family"], "beta": float(cell["beta"]), "eta": float(cell["eta"]),
                "theta0": [float(cell["initial_coordinate"])] + [0.0] * (dim - 1),
                "action": cell["action"], "alpha": float(cell["alpha"]), "H": cell["H"],
                "offsets": [0.0, 0.0, 0.0], "mu": 0.0, "weight_decay": 0.0,
                "q": [1.0] + [0.0] * (dim - 1)}
    stored = result.get("cell")
    wrong = sorted(k for k, v in expected.items() if not isinstance(stored, dict) or stored.get(k) != v)
    if wrong:
        raise ValueError(f"{cid}: stored cell differs from its manifest entry in {wrong}")
    bad = _invalid_stored_values(result)
    if bad:
        raise ValueError(f"{cid}: stored values missing, non-finite or of the wrong type: {bad[:5]}")


def load_run(input_dir: str | Path, manifest_path: str | Path | None = None,
             expected_sha256: str = EXPECTED_MANIFEST_SHA256
             ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    """(manifest cells, completed records by cell id, input provenance), or ValueError."""
    run_dir = Path(input_dir)
    if not run_dir.is_dir():
        raise ValueError(f"input {run_dir} is not a directory")
    manifest_file = Path(manifest_path) if manifest_path is not None else run_dir.parent.parent / MANIFEST_NAME
    if not manifest_file.is_file():
        raise ValueError(f"manifest {manifest_file} not found")
    digest = _sha256(manifest_file)
    if digest != expected_sha256:
        raise ValueError(f"manifest SHA256 {digest} != expected {expected_sha256}")
    metadata = _read_json(run_dir / "metadata.json")
    if not isinstance(metadata, dict) or metadata.get("manifest_sha256") != digest:
        raise ValueError("run metadata does not record this manifest's SHA256")
    cells = _read_json(manifest_file).get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("manifest has no cells")
    ids = [c.get("cell_id") for c in cells]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate cell ids in the manifest")
    stray = sorted({p.name[:-5] for p in run_dir.iterdir() if CELL_FILE.fullmatch(p.name)} - set(ids))
    if stray:
        raise ValueError(f"records not in the manifest: {stray[:5]}")
    records: dict[str, dict[str, Any]] = {}
    lines = []
    for cell in cells:
        path = run_dir / f"{cell['cell_id']}.json"
        if cell.get("H") not in (1, 2):
            if path.exists():
                raise ValueError(f"{cell['cell_id']}: unexpected record for an unrun H={cell.get('H')} cell")
            continue
        if not path.is_file():
            raise ValueError(f"{cell['cell_id']}: missing record")
        raw = path.read_bytes()
        try:
            record = json.loads(raw)
        except ValueError as exc:
            raise ValueError(f"{cell['cell_id']}: unreadable record: {exc}") from exc
        _check_record(cell, record)
        records[cell["cell_id"]] = record
        lines.append(f"{cell['cell_id']} {hashlib.sha256(raw).hexdigest()}\n")
    provenance = {
        "run_directory": str(run_dir),
        "manifest": {"path": str(manifest_file), "sha256": digest},
        "files": {name: _sha256(run_dir / name) for name in RUN_FILES if (run_dir / name).is_file()},
        "records": len(records),
        "records_digest": hashlib.sha256("".join(sorted(lines)).encode()).hexdigest(),
        "records_digest_rule": "SHA256 of sorted lines '<cell_id> <SHA256 of record bytes>\\n'",
        "unrun_cells_without_records": sum(c.get("H") not in (1, 2) for c in cells),
        "run_source_hashes": metadata.get("source_hashes", {}),
    }
    return cells, records, provenance


# ----------------------------------------------------------------------------- per-cell analysis


class _Worst:
    """Largest discrepancy seen per named check."""

    def __init__(self) -> None:
        self.values: dict[str, float] = {}

    def add(self, name: str, value: float) -> None:
        value = float(value)
        if not math.isfinite(value):
            value = math.inf
        self.values[name] = max(self.values.get(name, -math.inf), value)


def _setup(cell: dict[str, Any]) -> tuple[Config, State, int, float]:
    config = canonical_config(cell["family"], float(cell["beta"]), float(cell["eta"]))
    theta = (float(cell["initial_coordinate"]),) + (0.0,) * (config.dim - 1)
    return config, initial_state(config, theta), int(cell["action"]), float(cell["alpha"])


def _allocation(variance: float, rmse: float) -> int:
    return max(1, math.ceil(variance / (rmse * rmse)))


def _residual(plan: NDArray[np.float64], p: NDArray[np.float64], q: NDArray[np.float64]) -> float:
    rows = [math.fsum([*row, -a]) for row, a in zip(plan.tolist(), p.tolist())]
    cols = [math.fsum([*col, -b]) for col, b in zip(plan.T.tolist(), q.tolist())]
    return max(abs(v) for v in rows + cols)


def _v1_variance(mean: float, second: float) -> float:
    """pilot.pair's convention: second - mean**2, with roundoff down to -1e-14 stored as 0 (inf below)."""
    variance = second - mean * mean
    return variance if variance >= 0.0 else 0.0 if variance >= -VARIANCE_ROUNDOFF else math.inf


def _stored_summaries(result: dict[str, Any], worst: _Worst) -> None:
    """One record's stored variances and headroom block against v1's definitions (pilot.pair,
    pilot.headroom) evaluated on its own stored values; inf marks a wrong flag or null ratio.

    The stored best method may be any method within SUMMARY_TOL of the minimum variance (v1
    takes the first listed among ties); the best variance must be that method's."""
    blocks = [result["ordinary"][m] for m in ORDINARY_METHODS] + [result["oracle"], result["terminal_lower_bound"]]
    for b in blocks:
        worst.add("stored_variance_vs_moments", abs(b["variance"] - _v1_variance(b["mean"], b["second_moment"])))
    head, oracle_block = result["headroom"], result["oracle"]
    v_best, v_orc = head["best_ordinary_variance"], oracle_block["variance"]
    worst.add("stored_best_variance_vs_six_methods",
              abs(v_best - min(result["ordinary"][m]["variance"] for m in ORDINARY_METHODS)))
    worst.add("stored_best_variance_vs_six_methods",
              abs(result["ordinary"][head["best_ordinary_method"]]["variance"] - v_best))
    worst.add("stored_headroom_vs_oracle_and_terminal", abs(head["oracle_variance"] - v_orc))
    worst.add("stored_headroom_vs_oracle_and_terminal",
              abs(head["terminal_lower_bound_variance"] - result["terminal_lower_bound"]["variance"]))
    nondegenerate = v_best > NONDEGENERATE
    worst.add("stored_nondegenerate_and_ratios", 0.0 if head["nondegenerate"] is nondegenerate else math.inf)
    expected = dict(zip(RATIOS, (1.0 - v_orc / v_best, oracle_block["suboptimality_estimate"] / v_best)
                        if nondegenerate else (None, None)))
    for key, value in expected.items():
        stored = head.get(key)
        worst.add("stored_nondegenerate_and_ratios",
                  (0.0 if value is stored else math.inf) if value is None or stored is None
                  else abs(stored - value) / max(1.0, abs(value)))


def analyze_h2(cell: dict[str, Any], record: dict[str, Any], worst: _Worst,
               detail: bool = False) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """(CSV row, optional example detail) for one completed H=2 record; discrepancies go to `worst`."""
    result = record["result"]
    stored_oracle = result["oracle"]
    config, pre, action, alpha = _setup(cell)
    tree = build_tree(config, pre, action, alpha)
    C = continuation_costs(tree)
    v_star = vertex_minimum(tree.px, tree.py, C)
    k = config.n_actions

    worst.add("root_law_vs_stored", max(np.abs(tree.px - np.array(stored_oracle["root_p"])).max(),
                                        np.abs(tree.py - np.array(stored_oracle["root_q"])).max()))
    worst.add("continuation_cost_vs_stored_lp", float(np.abs(C - np.array(stored_oracle["root_cost"])).max()))
    worst.add("vertex_optimum_vs_stored_oracle", abs(v_star - stored_oracle["second_moment"]))
    stored_plan = np.array(stored_oracle["root_plan"], dtype=np.float64)
    worst.add("stored_root_plan_marginals", _residual(stored_plan, tree.px, tree.py))
    worst.add("stored_root_plan_below_min_entry", max(0.0, MIN_ENTRY - float(stored_plan.min())))
    worst.add("stored_root_plan_cost_vs_vertex_optimum",
              abs(math.fsum((stored_plan * C).ravel().tolist()) - v_star))
    mean_x = math.fsum((tree.px[:, None] * np.array(tree.P) * tree.s).ravel().tolist())
    mean_y = math.fsum((tree.py[:, None] * np.array(tree.Q) * tree.t).ravel().tolist())
    delta = result["marginal_truth"]["delta"]
    worst.add("delta_vs_stored", abs((mean_x - mean_y) - delta))
    worst.add("action_probability_vs_stored",
              abs(float(probs(config, pre)[action]) - result["marginal_truth"]["action_probability"]))
    stored_terminal = result["terminal_lower_bound"]
    for stored in (stored_oracle, stored_terminal):  # means are coupling-invariant
        worst.add("oracle_and_terminal_mean_vs_delta", abs(stored["mean"] - (mean_x - mean_y)))
    leaves_x, leaves_y = (tree.px[:, None] * np.array(tree.P)).ravel(), (tree.py[:, None] * np.array(tree.Q)).ravel()
    worst.add("terminal_second_moment_vs_quantile_merge",
              abs(w2_squared(leaves_x, tree.s.ravel(), leaves_y, tree.t.ravel()) - stored_terminal["second_moment"]))

    terms = {m: method_terms(m, tree, C, v_star) for m in ORDINARY_METHODS}
    oracle_second = stored_oracle["second_moment"]
    for m, tm in terms.items():
        stored = result["ordinary"][m]
        worst.add("method_second_moment_vs_stored", abs(tm.second_moment - stored["second_moment"]))
        worst.add("method_mean_vs_stored", abs(tm.mean - stored["mean"]))
        worst.add("method_mean_vs_delta", abs(tm.mean - delta))
        worst.add("decomposition_vs_stored_regret",
                  abs(tm.r0 + tm.r1 - (stored["second_moment"] - oracle_second)))
        worst.add("negative_regret_term", max(0.0, -tm.r0, -tm.r1))
    worst.add("ordered_last_step_regret", abs(terms["ordered"].r1))  # fact 1: must vanish
    hybrid = hybrid_terms("maximal", tree, C, v_star)  # direct enumeration of the identity R0 = regret
    worst.add("maximal_then_ordered_regret_vs_R0",
              abs(hybrid.second_moment - v_star - terms["maximal"].r0))

    headroom = result["headroom"]
    best, v_best = headroom["best_ordinary_method"], headroom["best_ordinary_variance"]
    v_orc = headroom["oracle_variance"]
    nondegenerate = bool(headroom["nondegenerate"])
    order_x, order_y = _order(_keys(config, tree.xs)), _order(_keys(config, tree.ys))
    status_x = [order_status((tree.P[order_x[i]], tree.s[order_x[i]]), (tree.P[order_x[i + 1]], tree.s[order_x[i + 1]]))
                for i in range(k - 1)]
    status_y = [order_status((tree.Q[order_y[i]], tree.t[order_y[i]]), (tree.Q[order_y[i + 1]], tree.t[order_y[i + 1]]))
                for i in range(k - 1)]
    statuses = status_x + status_y
    order_class = ("ordered" if all(v == "ordered" for v in statuses)
                   else "atoms" if "atoms" in statuses else "weights")
    violation = monge_violation(C, order_x, order_y)
    # Children whose one-step laws are totally ordered can only be ordered by their means.
    means_x = [math.fsum((tree.P[a] * tree.s[a]).tolist()) for a in range(k)]
    means_y = [math.fsum((tree.Q[b] * tree.t[b]).tolist()) for b in range(k)]
    law_x, law_y = _order(means_x), _order(means_y)
    law_sortable = all(order_status((tree.P[law_x[i]], tree.s[law_x[i]]), (tree.P[law_x[i + 1]], tree.s[law_x[i + 1]]))
                       == "ordered" for i in range(k - 1)) and all(
        order_status((tree.Q[law_y[i]], tree.t[law_y[i]]), (tree.Q[law_y[i + 1]], tree.t[law_y[i + 1]]))
        == "ordered" for i in range(k - 1))
    mean_violation = monge_violation(C, law_x, law_y)
    if law_sortable:  # fact 3: stochastically ordered children make C Monge in that order
        worst.add("law_order_monge_when_children_sortable", mean_violation)
    if mean_violation <= MONGE_TOL and (law_x, law_y) in (([0, 1, 2], [0, 1, 2]), ([2, 1, 0], [2, 1, 0])):
        # Label order (or both reversed) is the Monge order, so the label-CDF root plan is optimal.
        worst.add("label_order_monge_implies_fixed_label_root_optimal", abs(terms["fixed_label"].r0))
    min_r0 = min(tm.r0 for tm in terms.values())
    hybrid_method = min(ORDINARY_METHODS, key=lambda m: terms[m].r0)  # cellwise, in hindsight
    without_method = min(WITHOUT_FIXED_LABEL, key=lambda m: terms[m].r0)
    oracle_children = {(int(a), int(b)): sorted_plan(tree.P[a], tree.s[a], tree.Q[b], tree.t[b])
                       for a, b in zip(*np.nonzero(stored_plan))}
    oracle_split = _agreement(stored_plan, oracle_children, tree)
    worst.add("oracle_split_second_moment_vs_vertex_optimum", abs(oracle_split["second_moment"] - v_star))
    maximal_split = _agreement(terms["maximal"].root, terms["maximal"].children, tree)

    def fraction(value: float) -> float | None:
        return value / v_best if nondegenerate else None

    def over(r0: float) -> float | None:  # oracle's variance reduction relative to 'm then sorted'
        return r0 / (v_orc + r0) if nondegenerate and v_orc + r0 > 0.0 else (0.0 if nondegenerate else None)

    gap = v_best - v_orc
    without_best = min(WITHOUT_FIXED_LABEL, key=lambda m: result["ordinary"][m]["variance"])  # stored values only
    v_without = result["ordinary"][without_best]["variance"]
    row: dict[str, Any] = {
        "cell_id": cell["cell_id"], "structure": cell["family"], "beta": cell["beta"], "eta": cell["eta"],
        "theta0": cell["initial_coordinate"], "action": cell["action"], "alpha": cell["alpha"],
        "delta": delta, "action_probability": result["marginal_truth"]["action_probability"],
        "nondegenerate": nondegenerate, "best_method": best, "best_variance": v_best,
        "oracle_variance": v_orc, "terminal_lb_variance": headroom["terminal_lower_bound_variance"],
        "headroom": headroom["oracle_variance_reduction"],
        "without_fixed_label_best_method": without_best,
        "without_fixed_label_headroom": 1.0 - v_orc / v_without if v_without > NONDEGENERATE else None,
        "tv_root": 0.5 * math.fsum(np.abs(tree.px - tree.py).tolist()),
        "displacement": math.sqrt(math.fsum((np.subtract(tree.x.theta, tree.y.theta) ** 2).tolist())),
    }
    for m in ORDINARY_METHODS:
        row[f"{m}_variance"] = result["ordinary"][m]["variance"]
        row[f"{m}_R0"] = terms[m].r0
        row[f"{m}_R1"] = terms[m].r1
    row.update({
        "best_R0": terms[best].r0, "best_R1": terms[best].r1,
        "ordered_R0_fraction": fraction(terms["ordered"].r0),
        "maximal_R0_fraction": fraction(terms["maximal"].r0),
        "maximal_then_sorted_headroom": over(terms["maximal"].r0),
        "hybrid_method": hybrid_method, "hybrid_min_R0": min_r0, "hybrid_headroom": over(min_r0),
        "hybrid_capture": (1.0 - min_r0 / gap) if nondegenerate and gap > ZERO_FRACTION * v_best else None,
        "without_fixed_label_hybrid_method": without_method,
        "without_fixed_label_hybrid_headroom": over(terms[without_method].r0),
        "monge_violation": violation, "monge_holds": violation <= MONGE_TOL,
        "order_x": "|".join(status_x), "order_y": "|".join(status_y), "order_class": order_class,
        "children_law_sortable": law_sortable,
        "key_order_is_law_order": order_x == law_x and order_y == law_y,
        "monge_violation_mean_order": mean_violation, "monge_holds_mean_order": mean_violation <= MONGE_TOL,
        "label_order_is_mean_order": (law_x, law_y) in (([0, 1, 2], [0, 1, 2]), ([2, 1, 0], [2, 1, 0])),
        "maximal_mismatch_mass": maximal_split["mismatch_mass"],
        "maximal_mismatch_share": (maximal_split["mismatch_second_moment"] / maximal_split["second_moment"]
                                   if maximal_split["second_moment"] > 0.0 else None),
        "oracle_mismatch_mass": oracle_split["mismatch_mass"],
        "oracle_mismatch_share": (oracle_split["mismatch_second_moment"] / oracle_split["second_moment"]
                                  if oracle_split["second_moment"] > 0.0 else None),
        "distance_matches_maximal": _same_plans(terms["distance"], terms["maximal"]),
        "distance_matches_ordered": _same_plans(terms["distance"], terms["ordered"]),
    })
    for e in RMSE_TARGETS:
        row[f"n_best_rmse_{e}"] = _allocation(v_best, e) if nondegenerate else None
        row[f"n_oracle_rmse_{e}"] = _allocation(v_orc, e) if nondegenerate else None
    if not detail:
        return row, None

    distance_cost = [[math.fsum((a - b) ** 2 for a, b in zip(u.theta, v.theta)) for v in tree.ys] for u in tree.xs]
    info = {
        "cell_id": cell["cell_id"], "target": cell,
        "stored": {"headroom": headroom["oracle_variance_reduction"], "best_method": best,
                   "best_variance": v_best, "oracle_variance": v_orc,
                   "terminal_lower_bound_variance": headroom["terminal_lower_bound_variance"],
                   "variances": {m: result["ordinary"][m]["variance"] for m in ORDINARY_METHODS},
                   "oracle_root_plan": stored_oracle["root_plan"]},
        "root": {"theta_suppressed": list(tree.x.theta), "theta_ordinary": list(tree.y.theta),
                 "p_suppressed": tree.px.tolist(), "p_ordinary": tree.py.tolist(),
                 "tv": row["tv_root"], "displacement": row["displacement"]},
        "successors_suppressed": [list(u.theta) for u in tree.xs],
        "successors_ordinary": [list(v.theta) for v in tree.ys],
        "keys_suppressed": _keys(config, tree.xs), "keys_ordinary": _keys(config, tree.ys),
        "key_order_suppressed": order_x, "key_order_ordinary": order_y,
        "child_laws_suppressed": [p.tolist() for p in tree.P], "child_laws_ordinary": [q.tolist() for q in tree.Q],
        "child_scores_suppressed": tree.s.tolist(), "child_scores_ordinary": tree.t.tolist(),
        "child_mean_scores_suppressed": means_x, "child_mean_scores_ordinary": means_y,
        "child_mean_order_suppressed": law_x, "child_mean_order_ordinary": law_y,
        "order_status_suppressed": status_x, "order_status_ordinary": status_y,
        "continuation_cost_C": C.tolist(), "V_star_second_moment": v_star,
        "monge_violation_key_order": violation,
        "interactions_label_order": {"oracle_C": _interactions(C), "distance_cost": _interactions(distance_cost)},
        "methods": {m: {"root_plan": terms[m].root.tolist(), "second_moment": terms[m].second_moment,
                        "R0": terms[m].r0, "R1": terms[m].r1,
                        "R0_fraction_of_best": fraction(terms[m].r0), "R1_fraction_of_best": fraction(terms[m].r1)}
                    for m in ORDINARY_METHODS},
        "agreement_split": {"maximal": maximal_split, "oracle_one_optimal_plan": oracle_split},
        "row": row,
    }
    return row, info


# ----------------------------------------------------------------------------- summaries


def _clean(values: Iterable[Any]) -> list[float]:
    return [float(v) for v in values if v is not None]


def _max(values: Iterable[Any]) -> float | None:
    vals = _clean(values)
    return max(vals) if vals else None


def _median(values: Iterable[Any]) -> float | None:
    vals = _clean(values)
    return statistics.median(vals) if vals else None


def _group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nd = [r for r in rows if r["nondegenerate"]]
    hr = [r["headroom"] for r in nd]
    share = [r["best_R0"] / (r["best_R0"] + r["best_R1"]) for r in nd
             if r["best_R0"] + r["best_R1"] > ZERO_FRACTION * r["best_variance"]]
    ratio = [r["n_best_rmse_0.01"] / r["n_oracle_rmse_0.01"] for r in nd]
    return {
        "cells": len(rows), "nondegenerate": len(nd),
        "headroom_max": _max(hr), "headroom_median": _median(hr),
        "headroom_ge_1pct": sum(h >= 0.01 for h in hr), "headroom_ge_5pct": sum(h >= 0.05 for h in hr),
        "headroom_ge_10pct": sum(h >= 0.10 for h in hr),
        "tv_root_median": _median(r["tv_root"] for r in rows), "tv_root_max": _max(r["tv_root"] for r in rows),
        "monge_holds": sum(r["monge_holds"] for r in rows),
        "order_class_ordered": sum(r["order_class"] == "ordered" for r in rows),
        "order_class_weights": sum(r["order_class"] == "weights" for r in rows),
        "order_class_atoms": sum(r["order_class"] == "atoms" for r in rows),
        "cells_with_best_regret": len(share), "best_regret_root_share_median": _median(share),
        "best_regret_root_share_min": min(share) if share else None,
        "best_regret_root_share_max": _max(share),
        "ordered_root_optimal": sum(r["ordered_R0_fraction"] <= ZERO_FRACTION for r in nd),
        "agreement_root_optimal": sum(r["maximal_R0_fraction"] <= ZERO_FRACTION for r in nd),
        "headroom_over_maximal_then_sorted_max": _max(r["maximal_then_sorted_headroom"] for r in nd),
        "headroom_over_best_hybrid_max": _max(r["hybrid_headroom"] for r in nd),
        "headroom_over_best_without_fixed_label_hybrid_max": _max(r["without_fixed_label_hybrid_headroom"] for r in nd),
        "without_fixed_label_headroom_max": _max(r["without_fixed_label_headroom"] for r in nd),
        "without_fixed_label_headroom_ge_20pct": sum((r["without_fixed_label_headroom"] or 0.0) >= 0.2 for r in nd),
        "monge_in_child_mean_order": sum(r["monge_holds_mean_order"] for r in rows),
        "label_order_is_child_mean_order": sum(r["label_order_is_mean_order"] for r in rows),
        "hybrid_capture_median": _median(r["hybrid_capture"] for r in nd),
        "hybrid_capture_min": min(_clean(r["hybrid_capture"] for r in nd), default=None),
        "maximal_mismatch_mass_median": _median(r["maximal_mismatch_mass"] for r in rows),
        "maximal_mismatch_share_median": _median(r["maximal_mismatch_share"] for r in rows),
        "allocation_ratio_rmse_0.01_median": _median(ratio), "allocation_ratio_rmse_0.01_max": _max(ratio),
        "allocation_ratio_rmse_0.01_ge_2": sum(x >= 2.0 for x in ratio),
    }


def _grouped(rows: list[dict[str, Any]], keys: Sequence[str]) -> list[dict[str, Any]]:
    groups: dict[tuple, list[dict[str, Any]]] = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    return [{**dict(zip(keys, key)), **_group(members)} for key, members in sorted(groups.items())]


def _allocation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nd = [r for r in rows if r["nondegenerate"]]
    out: dict[str, Any] = {"cells": len(nd),
                           "variance_ratio_max": _max(r["best_variance"] / r["oracle_variance"]
                                                      for r in nd if r["oracle_variance"] > 0.0)}
    for e in RMSE_TARGETS:
        ratio = [r[f"n_best_rmse_{e}"] / r[f"n_oracle_rmse_{e}"] for r in nd]
        out[f"rmse_{e}"] = {"ratio_median": _median(ratio), "ratio_max": _max(ratio),
                            "cells_ratio_gt_1": sum(x > 1.0 for x in ratio),
                            "cells_ratio_ge_2": sum(x >= 2.0 for x in ratio),
                            "n_best_median": _median(r[f"n_best_rmse_{e}"] for r in nd),
                            "n_best_max": _max(r[f"n_best_rmse_{e}"] for r in nd)}
    return out


def _process_calls(records: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Exact-enumeration process calls (stored) against a paired sample's (derived) at H = 2."""
    exact = {json.dumps(r["result"]["marginal_truth"]["operations"], sort_keys=True)
             for r in records.values() if r["target"]["H"] == 2}
    ops = json.loads(exact.pop()) if len(exact) == 1 else None
    h, k = 2, 3
    per_pair = {"agreement_rules": {"methods": [m for m in ORDINARY_METHODS if m not in KEY_RULES],
                                    "probs": 2 * h, "apply_event": 2 + 2 * h, "score": 2},
                "key_rules": {"methods": list(KEY_RULES), "probs": 2 * h, "apply_event": 2 + 2 * h * k, "score": 2}}
    b_full = [r for r in rows if r["nondegenerate"] and r["structure"].startswith("B") and r["alpha"] == 1]
    out: dict[str, Any] = {
        "kind": "operation counts (derivation), not timings; coupling construction, random draws and "
                "LP solves are excluded from the per-pair counts",
        "exact_enumeration_H2_stored": ops, "exact_enumeration_consistent_across_cells": ops is not None,
        "paired_sample_H2_derived": per_pair,
        "per_pair_rule": "2 intervention updates; per step and world 1 probs call and 1 update "
                         "(K candidate updates for ordered/distance); 2 terminal scores",
        "assumptions": "every paired sample rebuilds the intervention pair and each state on its path (no "
                       "reuse across pairs; reusing shared root work lowers per-pair counts and raises the "
                       "break-even); break-even compares apply_event counts only; sample counts are the "
                       "allocation counts, with their assumptions",
    }
    if ops is not None:
        for name, cost in per_pair.items():
            n_even = ops["apply_event"] / cost["apply_event"]
            out[f"{name}_break_even_pairs_by_updates"] = n_even
            out[f"{name}_B_alpha1_cells_where_best_needs_more_pairs_at_rmse_0.01"] = sum(
                r["n_best_rmse_0.01"] > n_even for r in b_full)
        out["B_alpha1_nondegenerate_cells"] = len(b_full)
    return out


def _root_rules(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Per structure, over nondegenerate cells with >= 1% headroom: for each ordinary root rule m, the
    cells where the fixed schedule 'm at the root, sorted at the last step' attains the oracle (R0(m)
    <= 1e-6 of the best ordinary variance) and the oracle's largest remaining variance reduction over
    it. 'some_root_rule_optimal' and the 'best_hybrid' residuals take the best rule per cell, in
    hindsight: an envelope, not a selection policy."""
    out: dict[str, Any] = {}
    for structure in sorted({r["structure"] for r in rows}):
        cells = [r for r in rows if r["structure"] == structure and r["nondegenerate"] and r["headroom"] >= 0.01]
        entry: dict[str, Any] = {
            "cells": len(cells),
            "some_root_rule_optimal": sum(r["hybrid_min_R0"] <= ZERO_FRACTION * r["best_variance"] for r in cells),
            "residual_over_best_hybrid_max": _max(r["hybrid_headroom"] for r in cells),
            "residual_over_best_without_fixed_label_hybrid_max": _max(r["without_fixed_label_hybrid_headroom"]
                                                                      for r in cells),
            "without_fixed_label_residual_ge_1pct": sum(r["without_fixed_label_hybrid_headroom"] >= 0.01 for r in cells),
            "children_law_sortable": sum(r["children_law_sortable"] for r in cells),
            "monge_in_child_mean_order": sum(r["monge_holds_mean_order"] for r in cells),
            "label_order_is_child_mean_order": sum(r["label_order_is_mean_order"] for r in cells),
            "label_order_is_child_mean_order_and_monge": sum(r["label_order_is_mean_order"] and r["monge_holds_mean_order"]
                                                             for r in cells)}
        for m in ORDINARY_METHODS:
            residual = [r[f"{m}_R0"] / (r["oracle_variance"] + r[f"{m}_R0"])
                        if r["oracle_variance"] + r[f"{m}_R0"] > 0.0 else 0.0 for r in cells]
            entry[m] = {"root_optimal": sum(r[f"{m}_R0"] <= ZERO_FRACTION * r["best_variance"] for r in cells),
                        "residual_headroom_max": _max(residual)}
        out[structure] = entry
    return out


def _sortability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Nondegenerate cells by (children's laws totally ordered, key order equals that order)."""
    out = {}
    for sortable in (True, False):
        for matches in (True, False):
            m = [r for r in rows if r["nondegenerate"] and r["children_law_sortable"] is sortable
                 and r["key_order_is_law_order"] is matches]
            out[f"sortable={sortable},key_is_law_order={matches}"] = {
                "cells": len(m), "headroom_max": _max(r["headroom"] for r in m),
                "headroom_ge_1pct": sum(r["headroom"] >= 0.01 for r in m)}
    return out


def _in_timing_panel(cell: dict[str, Any]) -> bool:
    """H=2 half of PILOT_SPEC's prespecified B timing panel (fixed before v1)."""
    return (cell["family"] in ("B1", "B2") and cell["beta"] in (1, 8) and cell["eta"] in (0.1, 0.4)
            and cell["initial_coordinate"] == 0 and cell["alpha"] == 1 and cell["H"] == 2)


def _controls(witness: dict[str, Any], cells: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    """Cells differing from the witness in exactly one of beta, structure (same family) or alpha at
    H=2, plus its H=1 twin; the rule was fixed in ALTERNATIVES.md before any diagnostic output."""
    factors = ("family", "beta", "eta", "initial_coordinate", "action", "alpha", "H")
    out = []
    for cell in cells:
        diff = [f for f in factors if cell[f] != witness[f]]
        if diff == ["beta"]:
            out.append((f"control: beta {cell['beta']}", cell))
        elif diff == ["family"] and cell["family"] in PARTNERS[witness["family"]]:
            out.append((f"control: structure {cell['family']}", cell))
        elif diff == ["alpha"]:
            out.append((f"control: alpha {cell['alpha']}", cell))
        elif diff == ["H"] and cell["H"] == 1:
            out.append(("control: H1 twin", cell))
    return out


def _h1_identity(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ordered_gap, terminal_gap, headroom = [], [], []
    for rec in records.values():
        if rec["target"]["H"] != 1:
            continue
        r = rec["result"]
        ordered_gap.append(abs(r["ordinary"]["ordered"]["second_moment"] - r["oracle"]["second_moment"]))
        terminal_gap.append(abs(r["oracle"]["second_moment"] - r["terminal_lower_bound"]["second_moment"]))
        headroom.append(r["headroom"]["oracle_variance_reduction"])
    return {"cells": len(ordered_gap), "max_abs_ordered_minus_oracle_second_moment": _max(ordered_gap),
            "max_abs_oracle_minus_terminal_ot_second_moment": _max(terminal_gap),
            "max_stored_headroom": _max(headroom), "tolerance": TOL,
            "passed": bool(ordered_gap) and max(ordered_gap) <= TOL and max(terminal_gap) <= TOL}


def _source_hashes() -> dict[str, str]:
    here = Path(__file__).resolve().parent
    return {f"pilot/{name}": _sha256(here / name) for name in (*SOURCES, "diagnose.py")}


# ----------------------------------------------------------------------------- driver


def _check_paths(input_dir: Path, output_dir: Path) -> None:
    src, dst = input_dir.resolve(), output_dir.resolve()
    if dst == src or src in dst.parents:
        raise ValueError(f"output {dst} must not be the input run directory or inside it")
    if dst.exists() and not dst.is_dir():
        raise ValueError(f"output {dst} exists and is not a directory")


def _csv(rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def _write(path: Path, text: str) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def run(input_dir: str | Path, output_dir: str | Path, manifest_path: str | Path | None = None,
        expected_sha256: str = EXPECTED_MANIFEST_SHA256, witnesses: Sequence[str] = WITNESSES,
        write: bool = True) -> dict[str, Any]:
    """Validate, analyse and (when every check passes and `write`) write the outputs; returns the report."""
    wall, cpu = time.perf_counter(), time.process_time()
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    _check_paths(input_dir, output_dir)
    cells, records, provenance = load_run(input_dir, manifest_path, expected_sha256)
    by_id = {c["cell_id"]: c for c in cells}
    sources = _source_hashes()
    run_sources = provenance.pop("run_source_hashes")
    sources_match = all(sources.get(k) == v for k, v in run_sources.items()) and bool(run_sources)

    example_roles: dict[str, list[str]] = {}
    for wid in witnesses:
        if wid not in records:
            raise ValueError(f"witness {wid} has no completed record")
        example_roles.setdefault(wid, []).append("witness")
        for role, cell in _controls(by_id[wid], [by_id[c] for c in records]):
            example_roles.setdefault(cell["cell_id"], []).append(f"{role} of {wid}")

    worst = _Worst()
    for rec in records.values():  # H1 and H2: the stored summaries used below
        _stored_summaries(rec["result"], worst)
    rows, details = [], {}
    for cid, rec in records.items():
        if rec["target"]["H"] != 2:
            continue
        row, info = analyze_h2(by_id[cid], rec, worst, detail=cid in example_roles)
        rows.append(row)
        if info is not None:
            details[cid] = info
    if not rows:
        raise ValueError("no completed H=2 records")

    h1 = _h1_identity(records)
    tolerances = {name: TOL for name in worst.values}
    tolerances.update(dict.fromkeys(SUMMARY_CHECKS, SUMMARY_TOL))
    tolerances["root_law_vs_stored"] = tolerances["action_probability_vs_stored"] = LAW_TOL
    tolerances["stored_root_plan_below_min_entry"] = 0.0
    tolerances["law_order_monge_when_children_sortable"] = MONGE_TOL
    checks = {name: {"max": value, "tolerance": tolerances[name], "passed": bool(value <= tolerances[name])}
              for name, value in sorted(worst.values.items())}
    checks["h1_ordered_equals_oracle_equals_terminal_ot"] = {
        "max": max(h1["max_abs_ordered_minus_oracle_second_moment"] or 0.0,
                   h1["max_abs_oracle_minus_terminal_ot_second_moment"] or 0.0),
        "tolerance": TOL, "passed": h1["passed"]}
    checks["sources_match_run_metadata"] = {"max": None, "tolerance": None, "passed": sources_match}
    monge_rows = [r for r in rows if r["nondegenerate"] and r["monge_holds"]]
    monge_gap = _max(max(r["ordered_R0"], r["best_variance"] - r["oracle_variance"]) for r in monge_rows)
    checks["monge_in_key_order_implies_zero_regret"] = {  # absolute second-moment units
        "max": monge_gap, "tolerance": TOL, "passed": monge_gap is None or monge_gap <= TOL}
    ok = all(c["passed"] for c in checks.values())

    nd = [r for r in rows if r["nondegenerate"]]
    fails = [r for r in nd if not r["monge_holds"]]
    compact_keys = ("structure", "beta", "eta", "theta0", "action", "alpha", "headroom", "best_method",
                    "without_fixed_label_headroom", "without_fixed_label_best_method", "tv_root", "best_R0",
                    "best_R1", "without_fixed_label_hybrid_method", "without_fixed_label_hybrid_headroom",
                    "hybrid_headroom",
                    "monge_holds", "monge_holds_mean_order", "order_class", "children_law_sortable",
                    "key_order_is_law_order", "label_order_is_mean_order", "maximal_mismatch_mass",
                    "maximal_mismatch_share", "distance_matches_maximal")
    compact = []
    for cid, roles in example_roles.items():
        if cid in details:
            compact.append({"roles": roles, "cell_id": cid, "H": 2,
                            **{k: details[cid]["row"][k] for k in compact_keys}})
        else:
            r = records[cid]["result"]
            compact.append({"roles": roles, "cell_id": cid, "H": 1,
                            "headroom": r["headroom"]["oracle_variance_reduction"],
                            "best_method": r["headroom"]["best_ordinary_method"]})
    examples = []
    for cid, roles in example_roles.items():
        cell = by_id[cid]
        if cid in details:
            examples.append({"roles": roles, **details[cid]})
        else:  # H=1 twin: stored values only
            r = records[cid]["result"]
            examples.append({"roles": roles, "cell_id": cid, "target": cell,
                             "stored": {"headroom": r["headroom"]["oracle_variance_reduction"],
                                        "best_method": r["headroom"]["best_ordinary_method"],
                                        "ordered_variance": r["ordinary"]["ordered"]["variance"],
                                        "oracle_variance": r["oracle"]["variance"],
                                        "terminal_lower_bound_variance": r["terminal_lower_bound"]["variance"]}})
    report: dict[str, Any] = {
        "schema_version": 1, "tool": "python -m pilot.diagnose", "ok": ok,
        "scope": "Post hoc diagnosis of the completed v1 H1/H2 grid; recomputes H<=2 values only; no "
                 "fitting, no new horizons, no new method evaluation. Not fresh confirmation.",
        "conventions": "Conditional estimand; Y = suppressed minus ordinary; zero-based actions; "
                       "intervention_pair then weight-1 events on the full State; plans checked, never renormalised.",
        "inputs": provenance,
        "sources": {"hashes": sources, "prior_modules_match_run_metadata": sources_match},
        "environment": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__,
                        "platform": platform.platform()},
        "tolerances": {"absolute": TOL, "root_law": LAW_TOL, "monge": MONGE_TOL, "stochastic_order_cdf": ORDER_TOL,
                       "zero_regret_fraction_of_best_variance": ZERO_FRACTION, "nondegenerate": NONDEGENERATE,
                       "stored_summaries": SUMMARY_TOL},
        "definitions": {
            "m_then_sorted": "ordinary rule m at the root, terminal-score sort at the last step: one fixed schedule, "
                             "whose regret is R0(m)",
            "hybrid_and_best_hybrid": "the best of the six 'm then sorted' schedules chosen per cell in hindsight "
                                      "(minimum R0): an envelope, not a selection policy or a fresh evaluation",
            "without_fixed_label": "the five ordinary rules other than fixed_label: a descriptive sensitivity subset, "
                                   "not a relabelling-invariant class ('ordered' breaks key ties by action ID, "
                                   "'distance' keeps the LP's pick among tied optima); fixed_label stays in the "
                                   "v1 comparator and the gate is unchanged",
            "order_class": "over each world's adjacent children in key order: 'ordered' if every pair is "
                           "stochastically ordered; 'atoms' if a failing pair has a same-action atom reversed; "
                           "else 'weights' (failing pairs have comonotone atoms, so equal weights would be "
                           "ordered). A pattern, not a causal attribution to geometry or to probability change",
        },
        "checks": checks,
        "h1_identity": h1,
        "h2": {
            "cells": len(rows), "nondegenerate": len(nd),
            "by_structure_alpha": _grouped(rows, ("structure", "alpha")),
            "by_family_beta": _grouped([{**r, "family": r["structure"][0]} for r in rows], ("family", "beta")),
            "monge_crosstab": {
                "holds": {"cells": len(monge_rows), "headroom_max": _max(r["headroom"] for r in monge_rows),
                          "ordered_R0_fraction_max": _max(r["ordered_R0_fraction"] for r in monge_rows)},
                "fails": {"cells": len(fails), "headroom_max": _max(r["headroom"] for r in fails),
                          "headroom_ge_1pct": sum(r["headroom"] >= 0.01 for r in fails),
                          "ordered_root_optimal_anyway": sum(r["ordered_R0_fraction"] <= ZERO_FRACTION for r in fails)},
                "by_order_class": {cls: {"cells": len(m), "headroom_max": _max(r["headroom"] for r in m),
                                         "headroom_ge_1pct": sum(r["headroom"] >= 0.01 for r in m)}
                                   for cls in ("ordered", "weights", "atoms")
                                   for m in [[r for r in nd if r["order_class"] == cls]]},
                "by_children_law_order": _sortability(rows),
            },
            "root_rules_in_headroom_cells": _root_rules(rows),
            "cells_residual_over_best_hybrid_ge_1pct": [
                {k: r[k] for k in ("cell_id", "structure", "beta", "eta", "theta0", "action", "alpha", "headroom",
                                   "best_method", "hybrid_method", "hybrid_headroom",
                                   "without_fixed_label_hybrid_method", "without_fixed_label_hybrid_headroom",
                                   "order_class", "children_law_sortable", "key_order_is_law_order",
                                   "monge_holds_mean_order", "tv_root")}
                for r in sorted(nd, key=lambda r: -r["hybrid_headroom"]) if r["hybrid_headroom"] >= 0.01],
            "cells_without_fixed_label_headroom_ge_20pct": [
                {k: r[k] for k in ("cell_id", "structure", "beta", "eta", "theta0", "action", "alpha", "headroom",
                                   "best_method", "without_fixed_label_headroom", "without_fixed_label_best_method")}
                for r in sorted(nd, key=lambda r: -(r["without_fixed_label_headroom"] or 0.0))
                if (r["without_fixed_label_headroom"] or 0.0) >= 0.2],
            "cells_residual_over_without_fixed_label_hybrid_ge_1pct": [
                {k: r[k] for k in ("cell_id", "structure", "beta", "eta", "theta0", "action", "alpha", "headroom",
                                   "best_method", "without_fixed_label_hybrid_method",
                                   "without_fixed_label_hybrid_headroom", "monge_holds_mean_order",
                                   "label_order_is_mean_order")}
                for r in sorted(nd, key=lambda r: -r["without_fixed_label_hybrid_headroom"])
                if r["without_fixed_label_hybrid_headroom"] >= 0.01],
            "ties": {
                "distance_equals_maximal_all_nodes": {s: sum(r["distance_matches_maximal"] for r in rows if r["structure"] == s)
                                                      for s in sorted({r["structure"] for r in rows})},
                "distance_equals_ordered_all_nodes": {s: sum(r["distance_matches_ordered"] for r in rows if r["structure"] == s)
                                                      for s in sorted({r["structure"] for r in rows})},
                "cells_per_structure": {s: sum(r["structure"] == s for r in rows) for s in sorted({r["structure"] for r in rows})},
            },
            "cells_headroom_ge_5pct": [
                {k: r[k] for k in ("cell_id", "structure", "beta", "eta", "theta0", "action", "alpha", "headroom",
                                   "best_method", "best_R0", "best_R1", "hybrid_method", "hybrid_headroom",
                                   "maximal_then_sorted_headroom", "without_fixed_label_hybrid_headroom",
                                   "monge_violation",
                                   "order_class", "children_law_sortable", "key_order_is_law_order",
                                   "monge_holds_mean_order", "label_order_is_mean_order", "tv_root")}
                for r in sorted(nd, key=lambda r: -r["headroom"]) if r["headroom"] >= 0.05],
            "allocation_bound": {
                "definition": "N = max(1, ceil(V / rmse^2)) paired samples for the best ordinary and the oracle "
                              "variance; the ratio bounds the oracle's sample-count gain only under the assumptions "
                              "below. Not a measured practical method",
                "assumptions": ["estimator: average of N independent unbiased paired samples, V known",
                                "both couplings in the same admissible class (co-adapted couplings of current "
                                "states), where the oracle has the least V",
                                "equal cost per paired sample and negligible setup cost for both",
                                "integer N: small N can turn a variance ratio below 2 into 2:1 (N from 2 to 1)"],
                "not_a_bound_on": ["other estimators, including exact enumeration and Rao-Blackwellisation",
                                   "wall time", "methods with different per-pair or setup costs"],
                "all_nondegenerate": _allocation_summary(rows),
                "B_alpha_1": _allocation_summary([r for r in rows if r["structure"].startswith("B") and r["alpha"] == 1]),
                "B_timing_panel_H2_half": _allocation_summary([r for r in rows if _in_timing_panel(by_id[r["cell_id"]])]),
            },
            "process_calls": _process_calls(records, rows),
        },
        "example_selection": "Witnesses: the three maxima named in the brief (selected after v1). Controls: every "
                             "completed H=2 cell differing from a witness in exactly one of beta, structure "
                             "(B1<->B2; A2->A1,A3) or alpha, plus the H=1 twin; rule fixed in ALTERNATIVES.md "
                             "before any diagnostic output.",
        "examples_compact": compact,
        "examples": examples,
        "outputs": list(OUTPUTS),
    }
    report["resources"] = {
        "wall_seconds": time.perf_counter() - wall, "cpu_seconds": time.process_time() - cpu,
        "peak_rss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "peak_rss_unit": "bytes" if sys.platform == "darwin" else "KiB",
        "note": "Diagnostic run only (excludes interpreter start-up); not an estimator timing.",
    }
    if ok and write:
        output_dir.mkdir(parents=True, exist_ok=True)
        _write(output_dir / "h2_cells.csv", _csv(rows))
        _write(output_dir / "h2_groups.csv", _csv(_grouped(rows, ("structure", "alpha", "beta"))))
        _write(output_dir / "diagnostics.json", json.dumps(report, indent=1, allow_nan=False) + "\n")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pilot.diagnose",
                                     description="Mechanism diagnostic of the v1 headroom run.")
    parser.add_argument("--input", required=True, help="run directory with the v1 cell records")
    parser.add_argument("--output", required=True, help="directory for the diagnostic outputs")
    args = parser.parse_args(argv)
    try:
        report = run(args.input, args.output)
    except Exception as exc:  # noqa: BLE001 - every failure must surface as JSON plus exit 1
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    failed = sorted(name for name, c in report["checks"].items() if not c["passed"])
    print(json.dumps({"ok": report["ok"], "failed_checks": failed, "h2_cells": report["h2"]["cells"],
                      "written": list(OUTPUTS) if report["ok"] else [],
                      "wall_seconds": report["resources"]["wall_seconds"],
                      "cpu_seconds": report["resources"]["cpu_seconds"]}, allow_nan=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
