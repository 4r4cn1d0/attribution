"""How often the tool's walk breaks HLC 4.2's "at least 2 of each where they exist" in a theta0-like Unsafe cell
(I: a simulation under stated assumptions; synthetic data only). Uses the tool's own allocate() with the real pinned
settings and theta0's real seed tag. Assumptions: 200 harm prompts x 3 samples; a prompt's Unsafe propensity is
Beta(0.2, b) with mean u (overdispersed: Unsafe answers cluster on prompts); each Unsafe answer is HarmBench "yes"
with probability q. A violation: drawn "yes" < min(2, the number of distinct prompts holding a "yes" Unsafe answer),
or the same for "no" (both minimums are feasible together when each sub-cell has 2 prompts of its own)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib  # noqa: E402,F401

from scripts.stage1_s1.hlc_draw import draw as dr  # noqa: E402
from scripts.stage1_s1.hlc_draw import inputs as inp  # noqa: E402

cfg = dr.load_settings()


class _F:
    complete_sha256 = "0" * 64


def one(rng, u: float, q: float, arm: str, seed):
    a, b = 0.2, 0.2 * (1 - u) / u
    p = rng.beta(a, b, size=200)
    label = "theta0" if seed is None else f"{arm} {seed}"
    unit = inp.Unit(label, arm, seed, "pinned", "x", None, "init" if seed is None else "e1")
    unit.folder = _F()
    yes_prompts, no_prompts = set(), set()
    for i in range(200):
        pid = f"p{i:03d}"
        for k in range(3):
            if rng.random() < p[i]:
                hbl = "yes" if rng.random() < q else "no"
                (yes_prompts if hbl == "yes" else no_prompts).add(pid)
                unit.harm.append(inp.Answer("harm", pid, k, "Unsafe", ("Violent",), "Unsafe", "No", None, 9, False, hbl))
            else:
                unit.harm.append(inp.Answer("harm", pid, k, "Safe", (), "Safe", "No", None, 9, False, "no"))
    unit.benign = [inp.Answer("benign", f"d{i:03d}", None, "No", (), "Safe", "No", None, 9, False) for i in range(100)]
    _, _, subs = dr.allocate([unit], {}, cfg, "0")
    s = {x["sub_cell"]: x for x in subs if x["cell"] == "Unsafe"}
    y, m = s["Unsafe/yes"]["drawn"], s["Unsafe/no"]["drawn"]
    # feasible minimum: both sub-cells can hold min(2, prompts) when they have enough prompts of their own
    only_yes, only_no = yes_prompts - no_prompts, no_prompts - yes_prompts
    need_y = min(2, len(yes_prompts))
    need_m = min(2, len(no_prompts))
    feasible = len(yes_prompts | no_prompts) >= need_y + need_m and \
        (len(only_yes) + len(yes_prompts & no_prompts) >= need_y) and (len(only_no) + len(yes_prompts & no_prompts) >= need_m)
    bad = feasible and (y < need_y or m < need_m)
    return bad, len(yes_prompts), sum(a.label == "Unsafe" for a in unit.harm)


def report(rng, cases):
    for arm, seed, u, n_sims in cases:
        for q in (0.2, 0.35, 0.5):
            res = [one(rng, u, q, arm, seed) for _ in range(n_sims)]
            bad = sum(r[0] for r in res)
            print(f"{arm} {'' if seed is None else seed} (u={u}, HarmBench yes share q={q}): {bad}/{n_sims} simulated "
                  f"cells break the minimum; median Unsafe answers {int(np.median([r[2] for r in res]))}, median yes "
                  f"prompts {int(np.median([r[1] for r in res]))}")


if __name__ == "__main__":
    if sys.argv[1:] == ["low-u"]:
        report(np.random.default_rng(7), (("S4", 1102, 0.03, 400), ("S4", 1102, 0.05, 400)))
    else:
        report(np.random.default_rng(20261101), (("theta0", None, 0.032, 400), ("S1", 1102, 0.10, 200),
                                                 ("S1", 1102, 0.30, 100)))
