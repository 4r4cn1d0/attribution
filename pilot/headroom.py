"""Exact headroom of one cell; prints one JSON object to stdout.

    python -m pilot.headroom --structure B1 --beta 8 --eta 0.4 --theta0 0.4 --action 2 --alpha 1 --H 2

--structure (alias --family) names a canonical config A1, A2, A3, B1 or B2 with offsets 0,
mu = weight decay = 0 and q = e1. --theta0 c starts at theta = (c,) for A and (c, 0) for B with
zero momentum and counter. --action is ZERO-based. H counts future events after the observed one;
H > 4 (K**(2H) > 3**8 paired leaves) is rejected before any enumeration starts.

Exit status: 0 when every check passes; 1 when a check fails or the computation raises (the
JSON then has "ok": false and "error"); 2 for argparse errors. Variance ratios are reported only
when the best ordinary variance exceeds 1e-14 (the pilot's nondegenerate threshold), else null.
Ordering checks use the fixed tolerance 1e-12. LP gap estimates are float64 diagnostics, not
certificates: they never widen that tolerance. The oracle's (in second-moment units) fail a
separate check above 1e-12 in magnitude; the 'distance' baseline's are reported only.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from collections.abc import Sequence
from typing import Any

from .exact import attribution
from .pair import ORDINARY_METHODS, oracle, pair_moments, supported_horizon, terminal_ot
from .process import canonical_config, initial_state

__all__ = ["run", "main"]

MASS_TOL = 1e-12
MEAN_TOL = 1e-10
ORDER_TOL = 1e-12
GAP_TOL = 1e-12
RESIDUAL_TOL = 1e-12
MIN_ENTRY = -1e-14
NONDEGENERATE_VARIANCE = 1e-14
STRUCTURES = ("A1", "A2", "A3", "B1", "B2")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m pilot.headroom",
                                     description="Exact single-cell coupling headroom (JSON).")
    parser.add_argument("--structure", "--family", dest="structure", required=True, choices=STRUCTURES)
    parser.add_argument("--beta", type=float, required=True)
    parser.add_argument("--eta", type=float, required=True)
    parser.add_argument("--theta0", type=float, required=True, help="initial coordinate c")
    parser.add_argument("--action", type=int, required=True, help="observed action, zero-based")
    parser.add_argument("--alpha", type=float, required=True)
    parser.add_argument("--H", type=int, required=True, help="future events after the observed one")
    return parser


def _timed(fn: Any, *args: Any) -> tuple[Any, float]:
    start = time.perf_counter()
    return fn(*args), time.perf_counter() - start


def run(structure: str, beta: float, eta: float, theta0: float, action: int, alpha: float,
        H: int) -> dict[str, Any]:
    """All reference numbers and checks for one cell, as a JSON-ready dict."""
    wall, cpu = time.perf_counter(), time.process_time()
    config = canonical_config(structure, beta, eta)
    horizon = supported_horizon(config, H)  # before any exponential enumeration
    theta = (float(theta0),) + (0.0,) * (config.dim - 1)
    pre = initial_state(config, theta)
    cell = (config, pre, action, alpha, horizon)
    truth, truth_seconds = _timed(attribution, *cell)
    methods = {m: pair_moments(m, *cell) for m in ORDINARY_METHODS}
    best = oracle(*cell)
    lower = terminal_ot(*cell)

    delta = truth.delta
    diagnostics = [m.diagnostics for m in methods.values()] + [best.diagnostics, lower.diagnostics]
    residual = max(d.max_marginal_residual for d in diagnostics)
    entries = [d.min_entry for d in diagnostics if d.min_entry is not None]
    min_entry = min(entries) if entries else None
    max_gap = max(d.max_gap_estimate for d in diagnostics)
    mean_error = max(abs(r.mean - delta) for r in (*methods.values(), best, lower))
    checks = {
        "marginal_mass": all(abs(law.mass - 1.0) <= MASS_TOL for law in (truth.suppressed, truth.ordinary)),
        "pair_means_equal_delta": all(abs(r.mean - delta) <= MEAN_TOL for r in methods.values()),
        "oracle_mean_equals_delta": abs(best.mean - delta) <= MEAN_TOL,
        "terminal_mean_equals_delta": abs(lower.mean - delta) <= MEAN_TOL,
        "marginal_residuals": residual <= RESIDUAL_TOL,
        "min_entries": min_entry is None or min_entry >= MIN_ENTRY,
        "oracle_gap_estimates": (best.diagnostics.max_gap_estimate <= GAP_TOL
                                 and abs(best.suboptimality_estimate) <= GAP_TOL),
        "oracle_le_every_ordinary": all(best.second_moment <= r.second_moment + ORDER_TOL
                                        for r in methods.values()),
        "terminal_le_oracle": lower.second_moment <= best.second_moment + ORDER_TOL,
        "h1_oracle_equals_terminal":
            horizon != 1 or abs(best.second_moment - lower.second_moment) <= ORDER_TOL,
    }

    best_method = min(ORDINARY_METHODS, key=lambda m: methods[m].variance)  # ties: first listed
    best_variance = methods[best_method].variance
    nondegenerate = best_variance > NONDEGENERATE_VARIANCE
    headroom = {
        "best_ordinary_method": best_method,
        "best_ordinary_variance": best_variance,
        "oracle_variance": best.variance,
        "terminal_lower_bound_variance": lower.variance,
        "nondegenerate": nondegenerate,
        "oracle_variance_reduction": 1.0 - best.variance / best_variance if nondegenerate else None,
        "oracle_suboptimality_estimate_over_best_variance":
            best.suboptimality_estimate / best_variance if nondegenerate else None,
    }
    return {
        "cell": {"structure": structure, "family": config.family, "beta": config.beta,
                 "eta": config.eta, "theta0": list(theta), "action": action,
                 "action_indexing": "zero-based", "alpha": float(alpha), "H": horizon,
                 "offsets": list(config.offsets), "mu": config.mu,
                 "weight_decay": config.weight_decay, "q": list(config.q)},
        "marginal_truth": {
            "delta": delta, "sign": "suppressed minus ordinary",
            "suppressed_mean": truth.suppressed.mean, "ordinary_mean": truth.ordinary.mean,
            "suppressed_second_moment": truth.suppressed.second_moment,
            "ordinary_second_moment": truth.ordinary.second_moment,
            "suppressed_mass": truth.suppressed.mass, "ordinary_mass": truth.ordinary.mass,
            "action_probability": truth.action_probability, "seconds": truth_seconds,
            "operations": dataclasses.asdict(truth.operations)},
        "ordinary": {m: dataclasses.asdict(r) for m, r in methods.items()},
        "oracle": dataclasses.asdict(best),
        "terminal_lower_bound": dataclasses.asdict(lower),
        "headroom": headroom,
        "numerics": {"max_marginal_residual": residual, "min_entry": min_entry,
                     "max_gap_estimate": max_gap,
                     "oracle_suboptimality_estimate": best.suboptimality_estimate,
                     "max_variance_correction": max(r.variance_correction
                                                    for r in (*methods.values(), best, lower)),
                     "max_abs_mean_error": mean_error},
        "checks": checks,
        "ok": all(checks.values()),
        "seconds": time.perf_counter() - wall,
        "cpu_seconds": time.process_time() - cpu,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = run(args.structure, args.beta, args.eta, args.theta0, args.action, args.alpha, args.H)
        text = json.dumps(result, allow_nan=False)
    except Exception as exc:  # noqa: BLE001 - every failure must surface as JSON plus exit 1
        print(json.dumps({"cell": vars(args), "ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    print(text)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
