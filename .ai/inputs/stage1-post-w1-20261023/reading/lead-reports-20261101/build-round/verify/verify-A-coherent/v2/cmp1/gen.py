"""Synthetic, text-free B16 input documents with per-answer draws, and the matching coherent-only counts document
(the verifier's own generator; no study data). Every draw is seeded.

Per cell and prompt, 3 answers: a valid guard record with safety Unsafe w.p. pi (logit model), an invalid record
w.p. 1%, an unscored reason on most invalid records, Controversial on some valid Safe ones; each answer fails the
screen with a probability set by the scenario. U = Unsafe/3, g3_unscored_unsafe = (Unsafe or unscored)/3,
g3_controversial_unsafe = (valid Unsafe or Controversial)/3; coherence = (600, capped, failing); counts (n, u,
u_fail) as G2 defines them.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from scripts.stage1_s1.reading.settings import canonical_json, design
from scripts.stage1_s1.reading_input.coherent import RULE as COH_RULE  # fix round 1: coherent.check requires the rule text

P, A = 200, 3
O_LEVEL = {"a0": 5.0, "R": 6.0, "A1": 6.0, "L1": 7.0, "H1": 6.0, "S1": 12.0, "S3": 20.0, "S4": 15.0}
L_LEVEL = {"a0": 1.560, "R": 1.5615, "A1": 1.5625, "L1": 1.5620, "H1": 1.5618, "S1": 1.5602, "S3": 1.5605,
           "S4": 1.5603}


def sha(doc) -> str:
    return hashlib.sha256(canonical_json(doc)).hexdigest()


def expit(z):
    return 1.0 / (1.0 + np.exp(-z))


def make(reading: str, seed: int, mu: dict | None = None, fail: dict | None = None, empty_cells=(),
         concentrated: dict | None = None, linked: dict | None = None, base_fail: float = 0.05,
         all_coherent: bool = False, sd_e: float = 0.15, lowfail_cells: dict | None = None):
    """(tables_doc, counts_doc). ``fail``: arm -> base failing probability; ``empty_cells``: (arm, seed) whose answers
    all fail; ``concentrated``: arm -> (share of prompts, failing prob there), the same prompts at every seed;
    ``linked``: arm -> (P(fail | Unsafe), P(fail | Safe)); ``lowfail_cells``: (arm, seed) -> failing prob."""
    rng = np.random.default_rng(seed)
    dsg = design(reading)
    mu = {**{"a0": 0.5, "R": 0.0, "A1": -0.6, "L1": -0.1, "H1": 0.1, "S1": 0.2, "S3": -0.4, "S4": 0.25}, **(mu or {})}
    eta = rng.normal(-0.2, 2.5, P)
    seeds_all = sorted({j for a in dsg.arms for j in dsg.seeds[a]})
    shift = {cl: {j: rng.normal(0, 0.25) for j in seeds_all} for cl in ("full", "removal")}
    marked = {a: rng.random(P) < s for a, (s, _) in (concentrated or {}).items()}
    u_cells, g3u, g3c, o_cells, l_cells, coherence, counts = {}, {}, {}, {}, {}, {}, {}
    o_base = rng.uniform(-4, 4, 500)
    l_rows = rng.uniform(0.8, 2.4, P)
    for a in dsg.arms:
        gamma = rng.normal(0, 0.3, P)
        for j in dsg.seeds[a]:
            pi = expit(mu[a] + eta + gamma + shift[dsg.cluster[a]][j] + rng.normal(0, sd_e))
            unsafe_draw = rng.random((P, A)) < pi[:, None]
            invalid = rng.random((P, A)) < 0.01
            unsafe = unsafe_draw & ~invalid
            unscored = invalid & (rng.random((P, A)) < 0.7)
            controversial = ~unsafe_draw & ~invalid & (rng.random((P, A)) < 0.05)
            f = np.full((P, A), (fail or {}).get(a, base_fail))
            if a in (concentrated or {}):
                f = np.where(marked[a][:, None], concentrated[a][1], f)
            if a in (linked or {}):
                f1, f0 = linked[a]
                f = np.where(unsafe, f1, f0)
            if (a, j) in (lowfail_cells or {}):
                f = np.full((P, A), lowfail_cells[(a, j)])
            fails = rng.random((P, A)) < f
            if all_coherent:
                fails = np.zeros((P, A), bool)
            if (a, j) in empty_cells:
                fails = np.ones((P, A), bool)
            capped = fails & (rng.random((P, A)) < 0.4)
            u_cells.setdefault(a, {})[str(j)] = [int(k) / 3 for k in unsafe.sum(axis=1)]
            g3u.setdefault(a, {})[str(j)] = [int(k) / 3 for k in (unsafe | unscored).sum(axis=1)]
            g3c.setdefault(a, {})[str(j)] = [int(k) / 3 for k in (unsafe | controversial).sum(axis=1)]
            coherence.setdefault(a, {})[str(j)] = {"answers": P * A, "capped": int(capped.sum()),
                                                  "failing": int(fails.sum())}
            counts.setdefault(a, {})[str(j)] = {"n": [int(k) for k in (~fails).sum(axis=1)],
                                                "u": [int(k) for k in (unsafe & ~fails).sum(axis=1)],
                                                "u_fail": [int(k) for k in (unsafe & fails).sum(axis=1)]}
            rate = np.clip((O_LEVEL[a] + rng.normal(0, 1.2) + o_base) / 100.0, 0.0, 1.0)
            o_cells.setdefault(a, {})[str(j)] = [float(v) for v in rng.binomial(1, rate, 500)]
            l_cells.setdefault(a, {})[str(j)] = [float(v) for v in np.clip(
                l_rows + (L_LEVEL[a] - 1.56) + rng.normal(0, 0.0024) + rng.normal(0, 0.02, P), 0.0, None)]
    tables = {"kind": "stage1 reading input", "version": 1, "reading": reading,
              "endpoints": {"U": {"cells": u_cells},
                            "O": {"cells": o_cells,
                                  "theta0": [float(v) for v in rng.binomial(1, 0.17, 500)]},
                            "L": {"cells": l_cells}},
              "coherence": coherence,
              "u_variants": {"g3_unscored_unsafe": g3u, "g3_controversial_unsafe": g3c}}
    tables = json.loads(canonical_json(tables))
    cdoc = {"kind": "stage1 reading coherent-only counts", "version": 1, "reading": reading,
            "input_sha256": sha(tables), "rule": COH_RULE, "items": P, "samples_per_prompt": A,
            "cells": counts}
    return tables, json.loads(canonical_json(cdoc))
