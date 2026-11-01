"""Synthetic per-answer worlds for verifier 2 (no study data; every draw seeded): a B16 input document (tables.json)
with U, both G3 tables and the coherence block built from the same answers, and the matching coherent-only counts
document. O, L and theta0 come from B16's own test generator (tests/synth.py).

Per answer: Unsafe ~ Bernoulli(expit(mu_a + eta_p + gamma_ap + s_cluster,j + e_aj)); it fails the screen with a
probability by scenario (per arm: independent, concentrated on a prompt set, linked to the prompt's harm, linked to
the answer's own label; a cell may fail every answer); a Safe answer is "unscored" with probability 3% (counted Unsafe
in g3_unscored_unsafe) and Controversial with 4%; half of the failing answers are capped.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

WS = Path(__file__).resolve().parents[2] / "ws-a"
sys.path.insert(0, str(WS / "scripts" / "stage1_s1" / "reading" / "tests"))

import synth  # noqa: E402  (B16's test generator: O, L, theta0)

from scripts.stage1_s1.reading.settings import design  # noqa: E402

P, A = 200, 3
MU = {"a0": 0.5, "R": 0.0, "A1": -0.3, "L1": 0.05, "H1": 0.1, "S1": 0.0, "S3": -0.1, "S4": 0.15}


def expit(z):
    return 1.0 / (1.0 + np.exp(-z))


def world(reading: str, seed: int, fail: dict | None = None, base_fail: float = 0.05, empty=(), mu=None,
          o_levels=None, l_levels=None, shift_sd=0.25, e_sd=0.15, eta_sd=2.5, kind: str = "", rule: str = "",
          no_g3=False) -> tuple[dict, dict]:
    """(tables_doc without nothing hashed, counts cells) for one world. ``fail``: {arm: spec}; spec is one of
    ("independent", rate), ("concentrated", share, hi, lo, per_seed), ("prompt-linked", top_share, hi, lo),
    ("answer-linked", f_unsafe, f_safe), ("refusal-linked", f_unsafe, f_safe). ``empty``: cells whose every answer
    fails."""
    rng = np.random.default_rng([seed, 7])
    dsg = design(reading)
    mu = {**MU, **(mu or {})}
    fail = fail or {}
    doc = synth.make_input(seed=seed, reading=reading, o_levels=o_levels, l_levels=l_levels)
    eta = rng.normal(-0.2, eta_sd, P)
    seeds_all = sorted({j for a in dsg.arms for j in dsg.seeds[a]})
    shift = {cl: {j: rng.normal(0.0, shift_sd) for j in seeds_all} for cl in ("full", "removal")}
    marked_fixed = {a: rng.random(P) < (fail[a][1] if fail.get(a, ("",))[0] == "concentrated" else 0.0)
                    for a in dsg.arms}
    u_cells, g3u, g3c, coh, cnt = {}, {}, {}, {}, {}
    for arm in dsg.arms:
        gamma = rng.normal(0.0, 0.3, P)
        spec = fail.get(arm)
        for j in dsg.seeds[arm]:
            pi = expit(mu[arm] + eta + gamma + shift[dsg.cluster[arm]][j] + rng.normal(0.0, e_sd))
            unsafe = rng.random((P, A)) < pi[:, None]
            if spec is None or spec[0] == "independent":
                rate = base_fail if spec is None else spec[1]
                f1 = f0 = np.full(P, rate)
            elif spec[0] == "concentrated":
                _, share, hi, lo, per_seed = spec
                marked = (rng.random(P) < share) if per_seed else marked_fixed[arm]
                f1 = f0 = np.where(marked, hi, lo)
            elif spec[0] == "prompt-linked":
                _, top, hi, lo = spec
                cut = np.quantile(eta + gamma, 1.0 - top)
                f1 = f0 = np.where(eta + gamma >= cut, hi, lo)
            elif spec[0] in ("answer-linked", "refusal-linked"):
                f1, f0 = np.full(P, spec[1]), np.full(P, spec[2])
            else:
                raise ValueError(spec)
            fails = rng.random((P, A)) < np.where(unsafe, f1[:, None], f0[:, None])
            if (arm, j) in empty:
                fails[:] = True
            unscored = (~unsafe) & (rng.random((P, A)) < 0.03)
            contro = (~unsafe) & (rng.random((P, A)) < 0.04)
            capped = fails & (rng.random((P, A)) < 0.5)
            k_unsafe = unsafe.sum(axis=1)
            u_cells.setdefault(arm, {})[str(j)] = [int(k) / 3 for k in k_unsafe]
            g3u.setdefault(arm, {})[str(j)] = [int(k) / 3 for k in (unsafe | unscored).sum(axis=1)]
            g3c.setdefault(arm, {})[str(j)] = [int(k) / 3 for k in (unsafe | contro).sum(axis=1)]
            coh.setdefault(arm, {})[str(j)] = {"answers": P * A, "capped": int(capped.sum()), "failing": int(fails.sum())}
            cnt.setdefault(arm, {})[str(j)] = {"n": [int(v) for v in (~fails).sum(axis=1)],
                                               "u": [int(v) for v in (unsafe & ~fails).sum(axis=1)],
                                               "u_fail": [int(v) for v in (unsafe & fails).sum(axis=1)]}
    doc["endpoints"]["U"]["cells"] = u_cells
    doc["coherence"] = coh
    if no_g3:
        doc["u_variants"] = {"g3_controversial_unsafe": g3c}
    else:
        doc["u_variants"] = {"g3_unscored_unsafe": g3u, "g3_controversial_unsafe": g3c}
    counts = {"kind": kind, "version": 1, "reading": reading, "input_sha256": None, "rule": rule, "items": P,
              "samples_per_prompt": A, "cells": cnt}
    return doc, counts
