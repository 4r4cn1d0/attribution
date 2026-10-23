"""The one input schema of the stage-1 reading. Anything else is refused.

The input is one JSON object, text-free, with numeric tables only:

    {"kind": "stage1 reading input", "version": 1,
     "reading": "plan_a" | "plan_a_block_a_only" | "plan_b",
     "endpoints": {
        "U": {"cells": {arm: {seed: [200 prompt shares in [0, 1]]}}},
        "O": {"cells": {arm: {seed: [500 flags 0/1]}}, "theta0": [500 flags 0/1]},
        "L": {"cells": {arm: {seed: [200 losses >= 0, nats]}}}},
     "coherence": {arm: {seed: {"answers": n, "capped": c, "failing": f}}},
     "u_variants": {"coherent" | "g3_unscored_unsafe" | "g3_controversial_unsafe": cells like U}      (optional)
     "token_axis": {"axis": "total_tokens" | "target_tokens" | "rows",                                  (optional)
                    "masses": {"600": T, "1200": T, "2400": T}, "removed": {removal arm: T_m},
                    "dose_cells": {"R_1200": {seed: [200 shares]}, "R_2400": {seed: [200 shares]}}},
     "references": [{"name": str, "kind": "point", "cells": {"U": cells, "O": cells, "L": cells}},        (optional)
                    {"name": str, "kind": "curve", "points": {"0.9": {"U":..,"O":..,"L":..}, "0.75": .., "0.5": ..},
                     "theta0": {"U": [200 shares], "L": [200 losses]}}]}

Seeds are JSON keys, so they are strings of the integer seed, in plain ASCII decimal form ("1102"; no leading zero,
no other digits). A reference's name is a short ASCII identifier that is not an arm, a dose cell (R_1200, R_2400),
theta0 or "sum". The version is the integer 1. The arms and seeds of every endpoint must equal
the sealed design of the named reading (REV3 1.2-1.3; LN-01, LN-02), except that the O endpoint may hold a subset
of R's seeds (LN-12: the reused R units may lack 500-bank answers; J is printed). Every item vector has the
endpoint's item count. No key outside this schema, no text value, no NaN, no infinity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

from scripts.stage1.dose_axis import AXES, DOSES
from scripts.stage1_s1.reading.settings import Refusal, design, settings

INPUT_KIND = "stage1 reading input"
TOP_KEYS = {"kind", "version", "reading", "endpoints", "coherence", "u_variants", "token_axis", "references"}
REQUIRED = {"kind", "version", "reading", "endpoints", "coherence"}
COHERENCE_KEYS = {"answers", "capped", "failing"}
REFERENCE_KINDS = ("point", "curve")
CURVE_POINTS = ("0.9", "0.75", "0.5")
SEED_RANGE = range(1101, 1111)


@dataclass(frozen=True)
class Reference:
    name: str
    kind: str                                    # "point" or "curve"
    tables: dict                                  # point: endpoint -> {(name, seed): items}; curve: lambda -> endpoint -> {...}
    seeds: tuple[int, ...]
    theta0: dict | None = None                    # curve only: {"U": items, "L": items} of theta0 (AS(0))


@dataclass(frozen=True)
class Input:
    reading: str
    tables: dict                                  # endpoint -> {(arm, seed): np.ndarray(items)}
    theta0_o: np.ndarray
    coherence: dict                               # arm -> {seed: (answers, capped, failing)}
    variants: dict = field(default_factory=dict)  # name -> {(arm, seed): items}
    token_axis: dict | None = None
    references: tuple = ()


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


SEED_KEY = re.compile(r"11(0[1-9]|10)")       # the plain ASCII decimal seed: no sign, no leading zero, no other digits


def _seed(text, where: str) -> int:
    """The seed key must be the plain decimal seed as a string ('1102'): '01102', ' 1102' and non-ASCII digits are
    refused, so no two keys can name one cell (verify-code F2: an alias overwrote a real R cell on the O endpoint)."""
    if not isinstance(text, str) or SEED_KEY.fullmatch(text) is None:
        raise Refusal(f"{where}: the seed key {text!r} is not a seed 1101-1110 as a plain decimal string")
    return int(text)


def reserved_names(cfg: dict) -> frozenset:
    """Names a reference may not take: every design arm, the dose cells R_1200 and R_2400, theta0 and the
    two-arm fit's key (verify-code F3: a reference named like an arm crashed the fit or replaced the arm's cells)."""
    return frozenset(cfg["arms"]) | frozenset(f"R_{n}" for n in DOSES) | frozenset({"theta0", "sum"})


def _items(values, count: int, kind: str, where: str) -> np.ndarray:
    if not isinstance(values, list) or len(values) != count:
        raise Refusal(f"{where}: needs a list of {count} item values")
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise Refusal(f"{where}: an item value is not a number")
    arr = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(arr)):
        raise Refusal(f"{where}: an item value is not finite")
    if kind == "U" and (arr.min() < 0.0 or arr.max() > 1.0):
        raise Refusal(f"{where}: a U share is outside [0, 1]")
    if kind == "O" and not np.all((arr == 0.0) | (arr == 1.0)):
        raise Refusal(f"{where}: an O flag is not 0 or 1")
    if kind == "L" and arr.min() < 0.0:
        raise Refusal(f"{where}: a loss is negative")
    return arr


def _cells(cells, arms_seeds: dict, count: int, kind: str, where: str, loose_arms=()) -> dict:
    """cells: {arm: {seed: [items]}} against the expected {arm: seeds}; arms in loose_arms may hold a subset."""
    if not isinstance(cells, dict) or set(cells) != set(arms_seeds):
        raise Refusal(f"{where}: the arms are not exactly {sorted(arms_seeds)}")
    out = {}
    for arm, by_seed in cells.items():
        if not isinstance(by_seed, dict) or not by_seed:
            raise Refusal(f"{where}: arm {arm} is not a non-empty object of seeds")
        seeds = sorted(_seed(s, f"{where} arm {arm}") for s in by_seed)
        expected = sorted(arms_seeds[arm])
        if seeds != expected and not (arm in loose_arms and set(seeds) <= set(expected)):
            raise Refusal(f"{where}: arm {arm} has the seeds {seeds}, the sealed design has {expected}")
        for text, values in by_seed.items():
            out[(arm, int(text))] = _items(values, count, kind, f"{where} arm {arm} seed {text}")
    return out


def _coherence(doc, arms_seeds: dict) -> dict:
    if not isinstance(doc, dict) or set(doc) != set(arms_seeds):
        raise Refusal(f"coherence: the arms are not exactly {sorted(arms_seeds)}")
    out = {}
    for arm, by_seed in doc.items():
        if not isinstance(by_seed, dict) or sorted(_seed(s, "coherence") for s in by_seed) != sorted(arms_seeds[arm]):
            raise Refusal(f"coherence: arm {arm} does not hold exactly the sealed seeds")
        out[arm] = {}
        for text, counts in by_seed.items():
            if not isinstance(counts, dict) or set(counts) != COHERENCE_KEYS:
                raise Refusal(f"coherence: arm {arm} seed {text} is not {{answers, capped, failing}}")
            a, c, f = counts["answers"], counts["capped"], counts["failing"]
            if not all(_is_int(v) for v in (a, c, f)) or a <= 0 or not (0 <= c <= a) or not (0 <= f <= a):
                raise Refusal(f"coherence: arm {arm} seed {text}: counts must be integers with 0 <= capped, failing <= answers > 0")
            out[arm][int(text)] = (a, c, f)
    return out


def _mass(value, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or value <= 0:
        raise Refusal(f"{where}: a token mass must be a positive finite number")
    return float(value)


def _token_axis(doc, dsg, items: int, common: tuple[int, ...]) -> dict:
    if not isinstance(doc, dict) or set(doc) != {"axis", "masses", "removed", "dose_cells"}:
        raise Refusal("token_axis: needs exactly {axis, masses, removed, dose_cells}")
    if doc["axis"] not in AXES:
        raise Refusal(f"token_axis: the axis is not one of {AXES}")
    if not isinstance(doc["masses"], dict) or set(doc["masses"]) != {str(n) for n in DOSES}:
        raise Refusal(f"token_axis: masses needs the doses {DOSES} as string keys")
    masses = {n: _mass(doc["masses"][str(n)], f"token_axis masses {n}") for n in DOSES}
    if not (masses[600] < masses[1200] < masses[2400]):
        raise Refusal("token_axis: the dose masses must rise with the dose")
    if not isinstance(doc["removed"], dict) or not doc["removed"] or not set(doc["removed"]) <= set(dsg.removal_arms):
        raise Refusal(f"token_axis: removed names arms outside the design's removal arms {dsg.removal_arms}")
    removed = {arm: _mass(v, f"token_axis removed {arm}") for arm, v in doc["removed"].items()}
    expected = {f"R_{n}": list(common) for n in DOSES[1:]}
    cells = _cells(doc["dose_cells"], expected, items, "U", "token_axis dose_cells")
    for arm in expected:
        if sorted(s for a, s in cells if a == arm) != list(common):
            raise Refusal(f"token_axis: {arm} needs exactly the common seeds {list(common)}")
    return {"axis": doc["axis"], "masses": masses, "removed": removed, "cells": cells}


def _reference_tables(doc, name: str, counts: dict, where: str):
    if not isinstance(doc, dict) or set(doc) != set(counts):
        raise Refusal(f"{where}: needs the endpoints {sorted(counts)} exactly")
    seeds = None
    tables = {}
    for endpoint, cells in doc.items():
        if not isinstance(cells, dict) or len(cells) < 2:
            raise Refusal(f"{where} {endpoint}: a reference needs at least two seeds")
        these = sorted(_seed(s, f"{where} {endpoint}") for s in cells)
        if seeds is None:
            seeds = these
        elif these != seeds:
            raise Refusal(f"{where}: the endpoints hold different seed sets")
        tables[endpoint] = _cells({name: cells}, {name: these}, counts[endpoint], endpoint, f"{where} {endpoint}")
    return tables, tuple(seeds)


def _references(doc, counts: dict, reserved: frozenset) -> tuple:
    if not isinstance(doc, list) or not doc:
        raise Refusal("references: a non-empty list")
    out, names = [], set()
    for i, ref in enumerate(doc):
        where = f"references[{i}]"
        if not isinstance(ref, dict) or not isinstance(ref.get("name"), str) or ref["name"] in names:
            raise Refusal(f"{where}: needs a distinct string name")
        if not ref["name"].replace("-", "").replace("_", "").replace("+", "").isalnum() or len(ref["name"]) > 40 \
                or not ref["name"].isascii():
            raise Refusal(f"{where}: the name is not a short ASCII identifier")
        if ref["name"] in reserved:
            raise Refusal(f"{where}: the name {ref['name']!r} is an arm, a dose cell, theta0 or a fit key; a reference needs its own name")
        names.add(ref["name"])
        if ref.get("kind") == "point":
            if set(ref) != {"name", "kind", "cells"}:
                raise Refusal(f"{where}: a point reference has exactly {{name, kind, cells}}")
            tables, seeds = _reference_tables(ref["cells"], ref["name"], counts, where)
            out.append(Reference(ref["name"], "point", tables, seeds))
        elif ref.get("kind") == "curve":
            if set(ref) != {"name", "kind", "points", "theta0"} or not isinstance(ref["points"], dict) \
                    or set(ref["points"]) != set(CURVE_POINTS):
                raise Refusal(f"{where}: a curve reference has {{name, kind, points, theta0}} with the points {CURVE_POINTS} "
                              "(lambda 1 is a0 from the primary tables; lambda 0 is theta0: its U and L items under theta0)")
            if not isinstance(ref["theta0"], dict) or set(ref["theta0"]) != {"U", "L"}:
                raise Refusal(f"{where}: theta0 needs exactly {{U, L}} item lists (its O flags are the O endpoint's)")
            theta0 = {e: _items(ref["theta0"][e], counts[e], e, f"{where} theta0 {e}") for e in ("U", "L")}
            tables, seeds = {}, None
            for lam in CURVE_POINTS:
                t, s = _reference_tables(ref["points"][lam], ref["name"], counts, f"{where} point {lam}")
                if seeds is not None and s != seeds:
                    raise Refusal(f"{where}: the curve's points hold different seed sets")
                tables[float(lam)], seeds = t, s
            out.append(Reference(ref["name"], "curve", tables, seeds, theta0))
        else:
            raise Refusal(f"{where}: the kind is not one of {REFERENCE_KINDS}")
    return tuple(out)


def validate(doc) -> Input:
    """The checked input, or a Refusal that names the first failing check."""
    if not isinstance(doc, dict) or not set(doc) <= TOP_KEYS or not REQUIRED <= set(doc):
        raise Refusal(f"the input must hold the keys {sorted(REQUIRED)} and only keys of {sorted(TOP_KEYS)}")
    if doc["kind"] != INPUT_KIND or not _is_int(doc["version"]) or doc["version"] != 1:
        raise Refusal(f"not a version-1 {INPUT_KIND!r} (the version is the integer 1)")
    cfg = settings()
    dsg = design(doc["reading"]) if isinstance(doc["reading"], str) else None
    if dsg is None:
        raise Refusal("the reading is not a string")
    arms_seeds = {arm: list(dsg.seeds[arm]) for arm in dsg.arms}
    ep = doc["endpoints"]
    if not isinstance(ep, dict) or set(ep) != set(cfg["endpoints"]):
        raise Refusal(f"endpoints: needs exactly {list(cfg['endpoints'])}")
    counts = {e: int(cfg["endpoints"][e]["items"]) for e in cfg["endpoints"]}
    tables = {}
    for endpoint in cfg["endpoints"]:
        block = ep[endpoint]
        keys = {"cells", "theta0"} if endpoint == "O" else {"cells"}
        if not isinstance(block, dict) or set(block) != keys:
            raise Refusal(f"endpoints {endpoint}: needs exactly {sorted(keys)}")
        loose = ("R",) if endpoint == "O" else ()
        tables[endpoint] = _cells(block["cells"], arms_seeds, counts[endpoint], endpoint, f"endpoints {endpoint}", loose)
    theta0 = _items(ep["O"]["theta0"], counts["O"], "O", "endpoints O theta0")
    coherence = _coherence(doc["coherence"], arms_seeds)
    variants = {}
    if "u_variants" in doc:
        if not isinstance(doc["u_variants"], dict) or not doc["u_variants"] \
                or not set(doc["u_variants"]) <= set(cfg["u_variants"]):
            raise Refusal(f"u_variants: a non-empty object with names among {cfg['u_variants']}")
        for name, cells in doc["u_variants"].items():
            variants[name] = _cells(cells, arms_seeds, counts["U"], "U", f"u_variants {name}")
    token_axis = None
    if "token_axis" in doc:
        token_axis = _token_axis(doc["token_axis"], dsg, counts["U"], tuple(cfg["token_axis"]["common_seeds"]))
    references = _references(doc["references"], counts, reserved_names(cfg)) if "references" in doc else ()
    return Input(reading=doc["reading"], tables=tables, theta0_o=theta0, coherence=coherence, variants=variants,
                 token_axis=token_axis, references=references)
