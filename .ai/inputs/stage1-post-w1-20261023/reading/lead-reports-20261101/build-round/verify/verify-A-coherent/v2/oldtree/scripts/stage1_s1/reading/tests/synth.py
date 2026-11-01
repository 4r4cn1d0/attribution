"""Synthetic, text-free input documents for the reading's tests. No real data. Every draw is seeded.

World: per arm a true U level mu_a (pp), one seed shift per design cluster (sd ``shift``) plus an arm-specific
seed part (sd ``arm_sd[a]``), per-prompt base rates and an optional arm x prompt part (sd ``prompt_sd``); the prompt
share is Binomial(3, rate)/3. O flags are Bernoulli per prompt with a per-arm level and a theta0 level; L losses are
normal around a per-arm mean with a seed part and a row part.
"""

from __future__ import annotations

import numpy as np

from scripts.stage1_s1.reading.settings import design, settings

DEFAULT_U = {"a0": 60.0, "R": 45.0, "A1": 38.0, "L1": 44.0, "H1": 46.0, "S1": 50.0, "S3": 49.0, "S4": 52.0}
DEFAULT_O = {"a0": 5.0, "R": 6.0, "A1": 6.0, "L1": 7.0, "H1": 6.0, "S1": 12.0, "S3": 20.0, "S4": 15.0}
DEFAULT_L = {"a0": 1.560, "R": 1.5615, "A1": 1.5625, "L1": 1.5620, "H1": 1.5618, "S1": 1.5602, "S3": 1.5605, "S4": 1.5603}


def _share(rng, rate, p):
    rate = np.clip(rate, 0.0, 1.0)
    return rng.binomial(3, rate, size=p) / 3.0


def u_cells(rng, dsg, levels, shift=2.0, arm_sd=None, prompt_sd=0.0, items=200, arms=None):
    """{(arm, seed): shares}; the logit-free additive world on the pp scale, mapped to shares."""
    arms = arms or dsg.arms
    arm_sd = arm_sd or {}
    seeds_all = sorted({j for a in arms for j in dsg.seeds[a]})
    shift_c = {c: {j: rng.normal(0, shift) for j in seeds_all} for c in ("full", "removal")}
    base = rng.uniform(-25, 25, items)                     # per-prompt base rate deviation, pp
    out = {}
    for a in arms:
        b_ap = rng.normal(0, prompt_sd, items) if prompt_sd > 0 else np.zeros(items)
        for j in dsg.seeds[a]:
            e = rng.normal(0, arm_sd.get(a, 1.5))
            rate = (levels[a] + shift_c[dsg.cluster[a]][j] + e + base + b_ap) / 100.0
            out[(a, j)] = _share(rng, rate, items)
    return out


def o_cells(rng, dsg, levels, seed_sd=1.2, items=500, arms=None, r_seeds=None):
    arms = arms or dsg.arms
    base = rng.uniform(-4, 4, items)
    out = {}
    for a in arms:
        seeds = r_seeds if (a == "R" and r_seeds is not None) else dsg.seeds[a]
        for j in seeds:
            rate = np.clip((levels[a] + rng.normal(0, seed_sd) + base) / 100.0, 0.0, 1.0)
            out[(a, j)] = rng.binomial(1, rate, size=items).astype(float)
    return out


def o_theta0(rng, level=17.0, items=500):
    return rng.binomial(1, level / 100.0, size=items).astype(float)


def l_cells(rng, dsg, levels, seed_sd=0.0024, row_sd=0.5, items=200, arms=None):
    arms = arms or dsg.arms
    rows = rng.uniform(0.8, 2.4, items)
    out = {}
    for a in arms:
        for j in dsg.seeds[a]:
            out[(a, j)] = np.clip(rows + (levels[a] - 1.56) + rng.normal(0, seed_sd) + rng.normal(0, 0.02, items), 0.0, None)
    return out


def to_json_cells(cells, arms) -> dict:
    out = {}
    for (a, j), items in cells.items():
        if a in arms:
            out.setdefault(a, {})[str(j)] = [float(v) for v in items]
    return out


def coherence(dsg, failing_arms=(), failing_seeds=()):
    out = {}
    for a in dsg.arms:
        out[a] = {}
        for j in dsg.seeds[a]:
            n = 600
            f = 90 if (a in failing_arms or (a, j) in failing_seeds) else 25
            out[a][str(j)] = {"answers": n, "capped": 10, "failing": f}
    return out


def make_input(seed=0, reading="plan_a", u_levels=None, o_levels=None, l_levels=None, shift=2.0, arm_sd=None,
               prompt_sd=0.0, theta0_o_level=17.0, failing_arms=(), with_variants=False, with_token_axis=False,
               references=None, r_o_seeds=None) -> dict:
    """One input document. references: list of ("point", name, seeds) or ("curve", name, seeds)."""
    rng = np.random.default_rng(seed)
    dsg = design(reading)
    cfg = settings()
    u_levels = {**DEFAULT_U, **(u_levels or {})}
    o_levels = {**DEFAULT_O, **(o_levels or {})}
    l_levels = {**DEFAULT_L, **(l_levels or {})}
    u = u_cells(rng, dsg, u_levels, shift, arm_sd, prompt_sd)
    o = o_cells(rng, dsg, o_levels, r_seeds=r_o_seeds)
    l = l_cells(rng, dsg, l_levels)
    doc = {"kind": "stage1 reading input", "version": 1, "reading": reading,
           "endpoints": {"U": {"cells": to_json_cells(u, dsg.arms)},
                         "O": {"cells": to_json_cells(o, dsg.arms), "theta0": [float(v) for v in o_theta0(rng, theta0_o_level)]},
                         "L": {"cells": to_json_cells(l, dsg.arms)}},
           "coherence": coherence(dsg, failing_arms)}
    if with_variants:
        doc["u_variants"] = {name: to_json_cells(u_cells(rng, dsg, u_levels, shift, arm_sd, prompt_sd), dsg.arms)
                             for name in cfg["u_variants"]}
    if with_token_axis:
        common = cfg["token_axis"]["common_seeds"]
        dose = {}
        for name, lvl in (("R_1200", 35.0), ("R_2400", 25.0)):
            for j in common:
                dose[(name, j)] = _share(rng, (lvl + rng.normal(0, 1.5) + rng.uniform(-25, 25, 200)) / 100.0, 200)
        doc["token_axis"] = {"axis": "total_tokens", "masses": {"600": 60000.0, "1200": 120000.0, "2400": 240000.0},
                             "removed": {a: 70000.0 for a in dsg.removal_arms},
                             "dose_cells": {"R_1200": {str(j): [float(v) for v in dose[("R_1200", j)]] for j in common},
                                            "R_2400": {str(j): [float(v) for v in dose[("R_2400", j)]] for j in common}}}
    if references:
        doc["references"] = [_reference(rng, dsg, kind, name, seeds, u_levels, o_levels, l_levels)
                             for kind, name, seeds in references]
    return doc


def _ref_tables(rng, dsg, name, seeds, u_lvl, o_lvl, l_lvl):
    fake = type("D", (), {})()
    fake.arms, fake.seeds, fake.cluster = (name,), {name: tuple(seeds)}, {name: "full"}
    u = u_cells(rng, fake, {name: u_lvl}, 2.0, None, 0.0, 200, (name,))
    o = o_cells(rng, fake, {name: o_lvl}, 1.2, 500, (name,))
    l = l_cells(rng, fake, {name: l_lvl}, 0.0024, 0.5, 200, (name,))
    return {"U": to_json_cells(u, (name,))[name], "O": to_json_cells(o, (name,))[name], "L": to_json_cells(l, (name,))[name]}


def _reference(rng, dsg, kind, name, seeds, u_levels, o_levels, l_levels):
    if kind == "point":
        return {"name": name, "kind": "point", "cells": _ref_tables(rng, dsg, name, seeds, 48.0, 8.0, 1.5605)}
    points = {"0.9": _ref_tables(rng, dsg, name, seeds, 54.0, 7.0, 1.60), "0.75": _ref_tables(rng, dsg, name, seeds, 45.0, 10.0, 1.70),
              "0.5": _ref_tables(rng, dsg, name, seeds, 30.0, 14.0, 1.90)}
    theta0 = {"U": [float(v) for v in _share(rng, (15.0 + rng.uniform(-10, 10, 200)) / 100.0, 200)],
              "L": [float(v) for v in np.clip(rng.uniform(0.8, 2.4, 200) + 0.55, 0, None)]}
    return {"name": name, "kind": "curve", "points": points, "theta0": theta0}
