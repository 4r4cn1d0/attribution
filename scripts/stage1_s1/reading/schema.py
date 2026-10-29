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
     "overlap": {"strata_sha256": hex, "report_sha256": hex,                                            (optional)
                 "strata": B14's strata.json document, "report": B14's overlap_report.json document}

The overlap block (REV4 9.4; addendum 11 point 11, 33 point 3): B14's two documents as B14 wrote them (ids, counts,
numbers, hashes and B14's rule texts; no prompt or response text), each bound by its SHA-256 under B14's canonical
JSON, the report made on this strata record (its strata_sha256), under the reading's B14 seed plan and with exactly
the reading's add arms. Every add set's halves must pass B14's split rule as the strata record states it; the U
endpoint's items are in the strata's prompt-id order, and the U table at each half's positions must reproduce the
report's cells_u_pp (a0 and the add arm, every common seed and half) to the settings' overlap.check_tolerance_pp.
B16 prints both SHA-256; the lead compares them with B14's sealed values.

Seeds are JSON keys, so they are strings of the integer seed, in plain ASCII decimal form ("1102"; no leading zero,
no other digits). A reference's name is a short ASCII identifier that is not an arm, a dose cell (R_1200, R_2400),
theta0 or "sum". The version is the integer 1. The arms and seeds of every endpoint must equal
the sealed design of the named reading (REV3 1.2-1.3; LN-01, LN-02), except that the O endpoint may hold a subset
of R's seeds (LN-12: the reused R units may lack 500-bank answers; J is printed). Every item vector has the
endpoint's item count. No key outside this schema, no text value (the overlap block's embedded B14 documents
excepted: B16 reads only their ids, counts, numbers and hashes and prints none of their strings), no NaN, no infinity.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

import numpy as np

from scripts.stage1.dose_axis import AXES, DOSES
from scripts.stage1_s1.reading.settings import Refusal, design, settings

INPUT_KIND = "stage1 reading input"
TOP_KEYS = {"kind", "version", "reading", "endpoints", "coherence", "u_variants", "token_axis", "references", "overlap"}
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
    overlap: dict | None = None                   # REV4 9.4: {"strata_sha256", "report_sha256", "add_sets": {m: {"lower", "higher"}}}


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


HEX64 = re.compile(r"[0-9a-f]{64}")
OVERLAP_KEYS = {"strata_sha256", "report_sha256", "strata", "report"}
OVERLAP_HALVES = ("all", "lower", "higher")
STRATA_KIND, REPORT_KIND = "stage1 overlap strata", "stage1 overlap report"


def b14_sha256(doc) -> str:
    """The SHA-256 of a B14 document as B14 wrote it: the engine's canonical JSON (sorted keys, 2-space indent,
    ensure_ascii off, UTF-8, trailing newline; experiments/minimal_safety/common.canonical_json)."""
    data = (json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _finite(value) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and bool(np.isfinite(value))


def _split(block, prompt_ids: list, where: str) -> tuple[list, list]:
    """One add set of B14's strata record against B14's split rule as the record states it (overlap_strata.split_halves:
    k = floor(n / 2), b = the (k + 1)-th smallest S, lower = {S < b}, ties at b to the higher half): the halves
    partition the prompts; n, k and the sizes are the record's; at most k prompts lie below b and at least k + 1 lie
    at or below it (lower_n + ties_at_boundary >= k + 1); higher_min = b and lower_max < b (None if the lower half is
    empty). Returns (lower ids, higher ids)."""
    if not isinstance(block, dict):
        raise Refusal(f"{where}: not an object")
    lower, higher = block.get("lower"), block.get("higher")
    if not (isinstance(lower, list) and isinstance(higher, list) and all(isinstance(p, str) for p in lower + higher)):
        raise Refusal(f"{where}: lower and higher must be lists of prompt ids")
    if set(lower) & set(higher) or sorted(lower + higher) != prompt_ids:
        raise Refusal(f"{where}: the two halves do not partition the strata's prompt ids")
    n, k = len(prompt_ids), len(prompt_ids) // 2
    ties, b = block.get("ties_at_boundary"), block.get("boundary")
    if (block.get("n"), block.get("k"), block.get("lower_n"), block.get("higher_n")) != (n, k, len(lower), len(higher)):
        raise Refusal(f"{where}: n, k, lower_n or higher_n is not the halves' own count")
    if not (_is_int(ties) and 1 <= ties <= len(higher)) or not _finite(b) or block.get("higher_min") != b:
        raise Refusal(f"{where}: the boundary, higher_min or ties_at_boundary is not a B14 split's")
    if len(lower) > k or len(lower) + ties < k + 1:
        raise Refusal(f"{where}: the lower half is not the lower-similarity half of B14's split rule "
                      f"(lower_n {len(lower)}, ties {ties}, k {k})")
    lower_max = block.get("lower_max")
    if (lower_max is not None or lower) and not (_finite(lower_max) and lower_max < b):
        raise Refusal(f"{where}: lower_max is not below the boundary")
    return lower, higher


def _cells_u_pp(doc, arm_m: str, dsg, table: dict, halves: dict, scale: float, tol: float, where: str) -> None:
    """B14's cells_u_pp of one add set (a0 and the add arm at their common seeds) against the U table at the
    halves' positions: every value must agree to tol pp (null exactly where a half is empty)."""
    arms = ("a0", arm_m)
    if not isinstance(doc, dict) or set(doc) != set(arms):
        raise Refusal(f"{where}: needs exactly the arms {list(arms)}")
    common = list(dsg.common_seeds("a0", arm_m))
    for arm in arms:
        by_seed = doc[arm]
        if not isinstance(by_seed, dict) or sorted(_seed(s, f"{where} {arm}") for s in by_seed) != common:
            raise Refusal(f"{where} {arm}: needs exactly the common seeds of a0 and {arm_m}, {common}")
        for text, values in by_seed.items():
            if not isinstance(values, dict) or set(values) != set(OVERLAP_HALVES):
                raise Refusal(f"{where} {arm} seed {text}: needs exactly {list(OVERLAP_HALVES)}")
            for half, idx in halves.items():
                given = values[half]
                if len(idx) == 0:
                    if given is not None:
                        raise Refusal(f"{where} {arm} seed {text}: the {half} half is empty, so its value must be null")
                    continue
                if isinstance(given, bool) or not isinstance(given, (int, float)) or not np.isfinite(given):
                    raise Refusal(f"{where} {arm} seed {text}: the {half} value is not a finite number")
                ours = scale * float(table[(arm, int(text))][idx].mean())
                if not abs(ours - float(given)) <= tol:
                    raise Refusal(f"{where} {arm} seed {text}: the U table at the {half} half's positions gives "
                                  f"{ours!r} pp, cells_u_pp says {given!r}; the positions do not match B14's halves")


def _overlap(doc, dsg, table: dict, items: int, cfg: dict) -> dict:
    """The overlap block (REV4 9.4; addendum 11 point 11, 33 point 3): B14's strata and report documents, each bound
    by its SHA-256 (B14's canonical JSON), the report made on this strata (its strata_sha256), under the reading's seed
    plan, with exactly the reading's add arms; every add set's halves pass B14's split rule; the U items follow the
    strata's prompt ids, which the report's cells_u_pp confirms at every seed and half to the settings' tolerance.
    Returns {"strata_sha256", "report_sha256", "add_sets": {m: {"lower": positions, "higher": positions}}}."""
    if not isinstance(doc, dict) or set(doc) != OVERLAP_KEYS:
        raise Refusal(f"overlap: needs exactly {sorted(OVERLAP_KEYS)}")
    for key in ("strata_sha256", "report_sha256"):
        if not isinstance(doc[key], str) or HEX64.fullmatch(doc[key]) is None:
            raise Refusal(f"overlap: {key} is not a lowercase hex SHA-256")
    strata, report = doc["strata"], doc["report"]
    if not isinstance(strata, dict) or strata.get("kind") != STRATA_KIND or strata.get("version") != 1:
        raise Refusal("overlap: strata is not a version-1 B14 strata record")
    if not isinstance(report, dict) or report.get("kind") != REPORT_KIND or report.get("version") != 1:
        raise Refusal("overlap: report is not a version-1 B14 overlap report")
    if b14_sha256(strata) != doc["strata_sha256"] or report.get("strata_sha256") != doc["strata_sha256"]:
        raise Refusal("overlap: the strata record does not hash to strata_sha256, or the report was made on another strata record")
    if b14_sha256(report) != doc["report_sha256"]:
        raise Refusal("overlap: the report does not hash to report_sha256")
    o = cfg["overlap"]
    expected = [arm for arm in dsg.arms if dsg.kind[arm] == "add"]
    plan = o["seed_plans"][dsg.reading]
    if report.get("seed_plan") != plan or report.get("seeds") != list(dsg.common_seeds("a0", expected[0])):
        raise Refusal(f"overlap: the report is not B14's seed plan {plan} at the common seeds of a0 and the add arms")
    sets = report.get("add_sets")
    if not isinstance(sets, dict) or set(sets) != set(expected):
        raise Refusal(f"overlap: the report's add sets are not exactly the design's add arms {expected}")
    prompt_ids = strata.get("prompt_ids")
    if not (isinstance(prompt_ids, list) and len(prompt_ids) == items and all(isinstance(p, str) for p in prompt_ids)
            and prompt_ids == sorted(set(prompt_ids))):
        raise Refusal(f"overlap: the strata's prompt ids are not {items} sorted distinct ids (the U item order)")
    position = {pid: i for i, pid in enumerate(prompt_ids)}
    scale, tol = float(cfg["endpoints"]["U"]["scale"]), float(o["check_tolerance_pp"])
    out = {}
    for m in expected:
        where = f"overlap {m}"
        block = (strata.get("add_sets") or {}).get(m)
        lower_ids, higher_ids = _split(block, prompt_ids, f"{where} strata")
        rep = sets[m]
        if not isinstance(rep, dict) or rep.get("arm") != block.get("arm") or \
                rep.get("half_sizes") != {"all": items, "lower": len(lower_ids), "higher": len(higher_ids)} or \
                rep.get("ties_at_boundary") != block.get("ties_at_boundary"):
            raise Refusal(f"{where}: the report's arm, half sizes or ties disagree with the strata record")
        lower = np.array(sorted(position[p] for p in lower_ids), dtype=int)
        higher = np.array(sorted(position[p] for p in higher_ids), dtype=int)
        halves = {"all": np.arange(items), "lower": lower, "higher": higher}
        _cells_u_pp(rep.get("cells_u_pp"), m, dsg, table, halves, scale, tol, f"{where} cells_u_pp")
        out[m] = {"lower": lower, "higher": higher}
    return {"strata_sha256": doc["strata_sha256"], "report_sha256": doc["report_sha256"], "add_sets": out}


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
    overlap = _overlap(doc["overlap"], dsg, tables["U"], counts["U"], cfg) if "overlap" in doc else None
    return Input(reading=doc["reading"], tables=tables, theta0_o=theta0, coherence=coherence, variants=variants,
                 token_axis=token_axis, references=references, overlap=overlap)
