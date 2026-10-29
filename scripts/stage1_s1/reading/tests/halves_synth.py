"""Synthetic inputs for section 9.4's overlap control (tests only; no real data; every draw is seeded).

U item i has the prompt id f"p{i:03d}", so sorted ids (the strata's order) are the item order. The strata record is
B14's own (``overlap_strata.strata`` on a synthetic similarity record), and the report is built in B14's format with
B14's own ``cell_u``, ``contrast`` and ``verdict`` (exact fractions of the Unsafe counts); both carry their SHA-256
under B14's canonical JSON, as the B16 input builder will copy them.

The halves world: per full-corpus arm a, seed j and prompt p, rate = (base_level - effect[a][half(p)] + shift_j +
e(a, j) + base_p + b(a, p)) / 100 and the share is Binomial(3, rate) / 3. effect[a0] = 0, so the true U(c) - U(m) on
a half is effect[m][half] - effect[c][half] (the prompts are drawn afresh, so this is the population value the
"prompts random" item part aims at).
"""

from __future__ import annotations

import json

import numpy as np

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import s1common as s1
from scripts.stage1_s1 import overlap_strata as b14
from scripts.stage1_s1.reading.settings import design

FULL = ("a0", "S1", "S3", "S4")


def pid(i: int) -> str:
    return f"p{i:03d}"


def similarity(rng, items=200, tie_block=0):
    """prompt id -> S; ``tie_block`` prompts share the value at B14's boundary (ties go to the higher half)."""
    s = rng.uniform(0.2, 0.9, items)
    if tie_block:
        b = np.sort(s)[items // 2]
        near = np.argsort(np.abs(s - b))[:tie_block]
        s[near] = b
    return {pid(i): float(s[i]) for i in range(items)}


def positions(ids):
    return [int(p[1:]) for p in ids]


def counts(shares):
    return {pid(i): (int(round(3 * v)), 3) for i, v in enumerate(shares)}


EDIT = {"S1": "1" * 64, "S3": "3" * 64, "S4": "4" * 64}
PLAN = {"plan_a": "d1_plan_a", "plan_a_block_a_only": "block_a_only", "plan_b": "plan_b"}


def b14_settings():
    settings, digest = s1.load_settings(b14.SETTINGS_PATH, b14.SETTINGS_SHA256, b14.SETTINGS_NAME)
    return settings, digest


def similarity_record(sims: dict, settings: dict) -> bytes:
    """A synthetic B14 similarity record (canonical bytes) for add set -> {prompt id: S}."""
    ids = sorted(next(iter(sims.values())))
    sets = {m: {"edit_sha256": EDIT[m], "arm": "edit-" + EDIT[m], "row_ids": ["r0"],
                "per_prompt": {pid: {"s_max": float(v), "nearest": "r0"} for pid, v in s.items()}} for m, s in sims.items()}
    doc = {"kind": "stage1 overlap similarity", "version": 1, "eval": {"prompt_ids": ids},
           "model": {"hidden_state_index": 16, "read": "last prompt position"},
           "provenance": {"settings_sha256": settings["similarity_settings_sha256"]}, "add_sets": sets}
    return canonical_json(doc)


def strata_doc(sims: dict) -> dict:
    """B14's own strata record (overlap_strata.strata) for these similarities, parsed."""
    settings, digest = b14_settings()
    data = similarity_record(sims, settings)
    return json.loads(b14.strata(data, sha256_bytes(data), settings, digest))


def report_doc(u_json: dict, dsg, reading: str, strata: dict, strata_sha: str) -> dict:
    """An overlap report in B14's format (overlap_strata.report's keys and blocks), built with B14's own cell_u,
    contrast and verdict from the input's U shares, for the reading's B14 seed plan; units and provenance are
    synthetic placeholders (B16 does not read them)."""
    settings, _ = b14_settings()
    rep = settings["report"]
    plan = rep["seed_plans"][PLAN[reading]]
    seeds = plan["seeds"]
    cells = {arm: {j: counts(u_json[arm][str(j)]) for j in seeds} for arm in ["a0"] + plan["add_sets"]}
    out_sets = {}
    for name in plan["add_sets"]:
        block = strata["add_sets"][name]
        halves = {"all": strata["prompt_ids"], "lower": block["lower"], "higher": block["higher"]}
        results = {h: b14.contrast(cells["a0"], cells[name], seeds, ids, rep["minimum"]) for h, ids in halves.items()}
        table = {arm: {str(j): {h: (b14.cell_u(cells[arm][j], ids) if ids else None) for h, ids in halves.items()}
                       for j in seeds} for arm in ("a0", name)}
        out_sets[name] = {"arm": block["arm"], "edit_sha256": block["edit_sha256"],
                          "half_sizes": {h: len(ids) for h, ids in halves.items()},
                          "ties_at_boundary": block["ties_at_boundary"], "cells_u_pp": table, "contrasts": results,
                          "verdict": {**b14.verdict(results["all"], results["lower"], rep["texts"]), "role": rep["s_p"]["label"]}}
    return {"kind": b14.REPORT_KIND, "version": 1, "requirement": settings["requirement"], "outcome": rep["outcome"],
            "contrast": rep["contrast"], "variance_model": rep["variance_model"], "interval": rep["interval"],
            "holds_rule": rep["holds"], "s_p": rep["s_p"], "primary_model": rep["primary_model"],
            "seed_plan": PLAN[reading], "seeds": seeds, "strata_sha256": strata_sha, "units": {}, "add_sets": out_sets,
            "strata_add_sets_not_in_plan": sorted(set(strata["add_sets"]) - set(plan["add_sets"])),
            "provenance": {"synthetic": True}}


def overlap_block(doc: dict, sims: dict) -> dict:
    """The input's overlap block from per-add-set similarities (add set -> {prompt id: S}): B14's strata record and a
    B14-format report, each with its SHA-256 under B14's canonical JSON."""
    dsg = design(doc["reading"])
    strata = strata_doc({m: sims[m] for m in ("S1", "S3", "S4") if m in sims})
    strata_sha = sha256_bytes(canonical_json(strata))
    report = report_doc(doc["endpoints"]["U"]["cells"], dsg, doc["reading"], strata, strata_sha)
    return {"strata_sha256": strata_sha, "report_sha256": sha256_bytes(canonical_json(report)),
            "strata": strata, "report": report}


def rehash(block: dict) -> dict:
    """The block with both SHA-256 taken again after an edit (the report's strata_sha256 too): a forgery re-hashed
    throughout, for the tests that show the printed SHA-256 then differ from B14's."""
    block["strata_sha256"] = sha256_bytes(canonical_json(block["strata"]))
    block["report"]["strata_sha256"] = block["strata_sha256"]
    block["report_sha256"] = sha256_bytes(canonical_json(block["report"]))
    return block


def world_cells(rng, dsg, lower_mask, effect_lower, effect_higher, base_level=50.0, shift=2.0, arm_sd=None,
                prompt_sd=4.0, items=200, arms=FULL):
    """{(arm, seed): shares} of the halves world for the given arms (the full-corpus cluster by default)."""
    arm_sd = arm_sd or {"a0": 1.5, "S1": 2.5, "S3": 1.0, "S4": 3.0}
    seeds = sorted({j for a in arms for j in dsg.seeds[a]})
    s = {j: rng.normal(0, shift) for j in seeds}
    base = rng.uniform(-12, 12, items)
    out = {}
    for a in arms:
        b = rng.normal(0, prompt_sd, items) if prompt_sd > 0 else np.zeros(items)
        eff = np.where(lower_mask, effect_lower.get(a, 0.0), effect_higher.get(a, 0.0))
        for j in dsg.seeds[a]:
            rate = np.clip((base_level - eff + s[j] + rng.normal(0, arm_sd.get(a, 1.5)) + base + b) / 100.0, 0.0, 1.0)
            out[(a, j)] = rng.binomial(3, rate, size=items) / 3.0
    return out


def with_world(doc: dict, cells: dict) -> dict:
    """The document with its U cells of these arms replaced by the world's (all seeds of each arm)."""
    for (a, j), shares in cells.items():
        doc["endpoints"]["U"]["cells"][a][str(j)] = [float(v) for v in shares]
    return doc
