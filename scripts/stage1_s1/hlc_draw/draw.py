"""The human-label-check draw itself (LN-31, LN-34; HLC 4.1-4.4, 8): exclusions, cells, the sealed walk, the repeats
and the three output documents. The rule is the settings' (settings/hlc_draw.json, loaded only at its pin):

- **Exclusions** (HLC 4.1, 8), counted under the first reason that applies: the 9 Oct sheet's answers ("oct9"); every
  answer to a prompt that the minors rule excludes ("minors": SimpleSafetyTests' Child Abuse area, rule a; a term or
  age pattern in the prompt's text together with a sexual source category or a sexual Qwen3Guard category of any
  population answer to it, sampled or greedy, rule b); an unscored answer ("unscored": the engine's two not-scored
  reasons); any other answer with no valid guard label ("no_label").
- **Cells** (HLC 4.2): per unit, harm cells Unsafe, Controversial, Safe (the valid safety label) and benign cells Yes,
  No (the valid refusal label), with the step's quotas (per seed for a fine-tuned arm, one column for theta0).
- **The walk**: per cell, the eligible answers sorted by (prompt id, sample index) and shuffled by
  random.Random(derive_seed(freeze_date, "hlc-v1", "<arm>/<seed>/<block>/<cell>")). The cell's target is its quota
  plus the inflow, cut to the distinct prompts not yet used inside the arm; the Unsafe cell's target is split between
  the HarmBench sub-cells (``hb_split``, HLC 4.2). One pass over the sealed order takes an answer when its prompt is not
  yet used inside the arm, its sub-cell's target is not met, and the targets still unmet stay reachable from the
  answers after it (``reachable``), so every target is met exactly; the shortfall goes to the next cell of the seed.
- **Repeats** (HLC 4.4): random.Random(derive_seed(freeze_date, "hlc-v1-repeats", "harm")).sample(the harm item ids,
  sorted, n).
- **Outputs**: the key (every drawn item: arm, seed, unit, prompt id, sample index, cell, Qwen3Guard safety, categories
  and refusal, HarmBench label, output tokens, capped, rank in its cell's sealed order, repeat flag) and the weights
  file (per cell and sub-cell: eligible, available answers and prompts, target, drawn and the sampling fraction
  drawn/eligible; the exclusions per unit), both sealed; the manifest (text-free: totals, hashes, the seed tags, the
  inputs by SHA-256), readable. No document holds a text field; every document is canonical JSON, so a second process
  re-making it from the same inputs gets the same bytes.
"""

from __future__ import annotations

import itertools
import math
import platform
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import scripts.stage1_s1.reading_input as ri
from experiments.safety_selection.common import derive_seed
from scripts.stage1_s1.hlc_draw import inputs as inp
from scripts.stage1_s1.reading.settings import Refusal, canonical_json, strict_json
from scripts.stage1_s1.reading_input.sources import read_bytes, sha256_bytes

HERE = Path(__file__).resolve().parent
SETTINGS_PATH = HERE / "settings" / "hlc_draw.json"
SETTINGS_SHA256 = "1d3eabe38e9b5d069623ba17bcef3f2d939d0abf309c5d7f06473847179a8c2d"
SETTINGS_KIND = "stage1 human label check draw settings"
SETTINGS_NAME = "hlc_draw"
KEY_KIND = "stage1 human label check key"
WEIGHTS_KIND = "stage1 human label check weights"
MANIFEST_KIND = "stage1 human label check draw manifest"
REASONS = ("oct9", "minors", "unscored", "no_label")           # the settings' exclusions.order, checked on load
STEPS = ("0", "1", "2", "3")


# ----- settings -----------------------------------------------------------------------------------------------------


def load_settings(path: Path = SETTINGS_PATH, expected_sha256: str = SETTINGS_SHA256) -> dict:
    """The settings, refused unless the file hashes to the pin, names itself and is canonical JSON with the shape the
    draw reads (every step with a per-seed quota for each seed of each cell)."""
    data = read_bytes(Path(path), "the draw settings")
    digest = sha256_bytes(data)
    if digest != expected_sha256:
        raise Refusal(f"the draw settings hash to {digest[:16]}, the pin is {expected_sha256[:16]}")
    doc = strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != SETTINGS_KIND or doc.get("name") != SETTINGS_NAME \
            or doc.get("version") != 1:
        raise Refusal("not the version-1 human-label-check draw settings")
    if canonical_json(doc) != data:
        raise Refusal("the draw settings are not canonical JSON")
    cells = [*doc["cells"]["harm"], *doc["cells"]["benign"]]
    seeds = doc["seeds"]
    if sorted(seeds) != sorted(doc["arms"]) or any(len(s) != 3 or s != sorted(s) for s in seeds.values()):
        raise Refusal("the draw settings do not give each arm its three seeds in ascending order")
    if sorted(doc["sizes"]["steps"]) != list(STEPS) or tuple(doc["exclusions"]["order"]) != REASONS:
        raise Refusal("the draw settings do not hold steps 0-3 and the exclusion order")
    for step in doc["sizes"]["steps"].values():
        if sorted(step["per_seed"]) != sorted(cells) or sorted(step["theta0"]) != sorted(cells) \
                or any(len(q) != 3 for q in step["per_seed"].values()):
            raise Refusal("a reduction step of the draw settings has no quota for every cell and seed")
    return doc


_SETTINGS: dict | None = None


def settings() -> dict:
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = load_settings()
    return _SETTINGS


# ----- exclusions ---------------------------------------------------------------------------------------------------


def minors_rule(bank: inp.Bank, units: list, cfg: dict) -> dict:
    """{"rule_a": sorted prompt ids, "rule_b": sorted prompt ids} of HLC 8 (module doc); prompts of both blocks."""
    m = cfg["exclusions"]["minors"]
    terms = [re.compile(r"(?<![a-z0-9])" + re.escape(inp.norm(t)) + r"(?![a-z0-9])") for t in m["terms"]]
    ages = [re.compile(p) for p in m["age_patterns"]]
    marker = m["sexual_marker"]
    seen: dict = {}                                # prompt id -> every Qwen3Guard category of the population's answers
    for u in units:
        for a in [*u.harm, *u.benign]:
            seen.setdefault(a.prompt_id, set()).update(a.categories)
        for pid, cats in u.greedy_harm.items():      # the greedy answers to the harm prompts (rule b's "its answers")
            seen.setdefault(pid, set()).update(cats)
    rule_a, rule_b = [], []
    for pid in [*sorted(bank.harm), *sorted(bank.benign)]:
        source, category = bank.category[pid]
        category = inp.norm(category or "")
        if source == m["rule_a"]["source"] and category == m["rule_a"]["category"]:
            rule_a.append(pid)
            continue
        text = inp.norm(bank.harm.get(pid, bank.benign.get(pid)))
        if not (any(t.search(text) for t in terms) or any(p.search(text) for p in ages)):
            continue
        if marker in category or any(marker in c.lower() for c in seen.get(pid, ())):
            rule_b.append(pid)
    return {"rule_a": rule_a, "rule_b": rule_b}


def answer_key(a: inp.Answer) -> tuple:
    """The sort key of an answer inside its unit: (prompt id, sample index; a greedy answer has -1)."""
    return a.prompt_id, -1 if a.sample_index is None else a.sample_index


def exclusions(units: list, oct9: set, minors: dict, cfg: dict) -> dict:
    """{unit label: {answer key: reason}} by the first reason that applies (module doc)."""
    not_scored = set(cfg["exclusions"]["unscored"]["reasons"])
    out_of = {*minors["rule_a"], *minors["rule_b"]}
    out: dict = {}
    for u in units:
        mine = out.setdefault(u.label, {})
        for a in [*u.harm, *u.benign]:
            if a.block == inp.HARM and (u.folder.complete_sha256, a.prompt_id, a.sample_index) in oct9:
                mine[answer_key(a)] = "oct9"
            elif a.prompt_id in out_of:
                mine[answer_key(a)] = "minors"
            elif a.label is None:
                mine[answer_key(a)] = "unscored" if a.reason in not_scored else "no_label"
    return out


# ----- the walk -----------------------------------------------------------------------------------------------------


def cell_seed(cfg: dict, unit: inp.Unit, block: str, cell: str) -> int:
    """derive_seed(freeze_date, "hlc-v1", "<arm>/<seed>/<block>/<cell>"); theta0: "theta0/<block>/<cell>"."""
    tags = cfg["seed_tags"]
    part = f"{unit.arm}/{block}/{cell}" if unit.seed is None else f"{unit.arm}/{unit.seed}/{block}/{cell}"
    return derive_seed(tags["freeze_date"], tags["draw"], part)


def sealed_order(keys, seed: int) -> list:
    """random.Random(seed).shuffle(sorted(keys)) (s1common.sealed_order's form)."""
    out = sorted(keys)
    random.Random(seed).shuffle(out)
    return out


def hb_split(n: int, a_yes: int, a_no: int, p_yes: int, p_no: int, p_all: int, minimum: int) -> tuple[int, int]:
    """The Unsafe cell's HarmBench split (the settings' harmbench_split rule): (y, m) with y + m = min(n, p_all).
    ``a_yes`` and ``a_no`` count the available answers of each sub-cell (they set the proportion); ``p_yes``, ``p_no``
    and ``p_all`` count the distinct available prompts that hold one (one answer per prompt can be drawn, so any (y, m)
    with y <= p_yes, m <= p_no and y + m <= p_all can be drawn, and no other)."""
    total = min(n, p_all)
    if total <= 0:
        return 0, 0
    lo, hi = max(min(minimum, p_yes), total - p_no), min(p_yes, total - min(minimum, p_no))
    if lo > hi:                                  # both minimums do not fit: the prompt counts alone bound the split
        lo, hi = max(0, total - p_no), min(p_yes, total)
    y = math.floor(Fraction(total * a_yes, a_yes + a_no) + Fraction(1, 2))
    y = min(max(y, lo), hi)
    return y, total - y


def reachable(keys, sub_of: dict, need: dict, used) -> bool:
    """Whether every target in ``need`` (sub-cell -> answers still to take) can be met from ``keys`` with one key per
    prompt and no prompt of ``used``. Hall's condition: for every set of sub-cells with a target, the sum of their
    targets is at most the number of unused prompts that hold a key of one of them."""
    held: dict = {}
    for key in keys:
        if key[0] not in used:
            held.setdefault(sub_of[key], set()).add(key[0])
    open_subs = sorted(s for s, q in need.items() if q > 0)
    for size in range(1, len(open_subs) + 1):
        for group in itertools.combinations(open_subs, size):
            if sum(need[s] for s in group) > len(set().union(*(held.get(s, set()) for s in group))):
                return False
    return True


def walk(order: list, sub_of: dict, targets: dict, used: set) -> list:
    """The keys taken from a cell's sealed ``order``, in that order: a key is taken when its prompt is not yet used
    inside the arm, its sub-cell's target is not yet met, and the targets still unmet stay reachable from the keys
    after it (``reachable``). Targets that ``order`` can meet at the start are each met exactly (so a prompt that holds
    answers of both HarmBench sub-cells cannot use up the scarcer sub-cell's minimum, HLC 4.2), by the keys that come
    first in the sealed order among those that allow it. The taken prompts join ``used``."""
    need = dict(targets)
    if not reachable(order, sub_of, need, used):
        raise Refusal("a cell's targets cannot be met from its answers (the draw's split or cut is wrong)")
    taken = []
    for n, key in enumerate(order):
        sub = sub_of[key]
        if key[0] in used or need[sub] == 0:
            continue
        need[sub] -= 1
        if reachable(order[n + 1:], sub_of, need, used | {key[0]}):
            taken.append(key)
            used.add(key[0])
        else:
            need[sub] += 1
    return taken


def quotas_of(cfg: dict, step: str, unit: inp.Unit) -> dict:
    sizes = cfg["sizes"]["steps"][step]
    if unit.seed is None:
        return dict(sizes["theta0"])
    position = cfg["seeds"][unit.arm].index(unit.seed)
    return {cell: q[position] for cell, q in sizes["per_seed"].items()}


def item_id(unit: inp.Unit, a: inp.Answer) -> str:
    tail = "greedy" if a.sample_index is None else str(a.sample_index)
    prefix = "h" if a.block == inp.HARM else "b"
    return prefix + sha256_bytes(f"{unit.folder.complete_sha256}|{a.prompt_id}|{tail}".encode())[:16]


def _item(unit: inp.Unit, a: inp.Answer, cell: str, sub: str, rank: int) -> dict:
    return {"item": item_id(unit, a), "block": a.block, "arm": unit.arm, "seed": unit.seed, "unit": unit.label,
            "complete_sha256": unit.folder.complete_sha256, "prompt_id": a.prompt_id, "sample_index": a.sample_index,
            "cell": cell, "sub_cell": sub,
            "qwen3guard": {"safety": a.safety, "categories": list(a.categories), "refusal": a.refusal},
            "harmbench": a.harmbench, "output_tokens": a.output_tokens, "capped": a.capped, "rank": rank,
            "repeat": False}


def allocate(units: list, excluded: dict, cfg: dict, step: str) -> tuple[list, list, list]:
    """(items in draw order, the cells' records, the sub-cells' records): the walk of every cell (module doc)."""
    split = cfg["harmbench_split"]
    used_by_arm: dict = {}
    items, cells, subs = [], [], []
    for unit in units:
        used = used_by_arm.setdefault(unit.arm, set())
        quota = quotas_of(cfg, step, unit)
        gone = excluded.get(unit.label, {})
        for block, answers in ((inp.HARM, unit.harm), (inp.BENIGN, unit.benign)):
            carry = 0
            for cell in cfg["cells"][block]:
                n = quota[cell] + carry
                eligible = {answer_key(a): a for a in answers if a.label == cell and answer_key(a) not in gone}
                order = sealed_order(eligible, cell_seed(cfg, unit, block, cell))
                if block == inp.HARM and cell == split["cell"]:
                    names = [f"{cell}/{s}" for s in split["sub_cells"]]           # "yes", then "no"
                    sub_of = {k: names[0] if a.harmbench == "yes" else names[1] for k, a in eligible.items()}
                else:
                    names, sub_of = [cell], {k: cell for k in eligible}
                free = [k for k in eligible if k[0] not in used]       # available: prompt unused inside the arm
                avail = Counter(sub_of[k] for k in free)
                prompts = {s: len({k[0] for k in free if sub_of[k] == s}) for s in names}
                p_all = len({k[0] for k in free})
                if len(names) == 2:
                    y, m = hb_split(n, avail[names[0]], avail[names[1]], prompts[names[0]], prompts[names[1]], p_all,
                                    split["minimum"])
                    target = {names[0]: y, names[1]: m}
                else:
                    target = {cell: min(n, p_all)}
                taken = walk(order, sub_of, target, used)
                rank = {k: r for r, k in enumerate(order)}
                drawn = Counter(sub_of[k] for k in taken)
                for k in taken:
                    items.append(_item(unit, eligible[k], cell, sub_of[k], rank[k]))
                cells.append({"unit": unit.label, "arm": unit.arm, "seed": unit.seed, "block": block, "cell": cell,
                              "quota": n, "inflow": carry, "available_prompts": p_all, "drawn": len(taken),
                              "shortfall": n - len(taken)})
                for sub, q in target.items():
                    e = sum(1 for k in eligible if sub_of[k] == sub)
                    subs.append({"unit": unit.label, "arm": unit.arm, "seed": unit.seed, "block": block, "cell": cell,
                                 "sub_cell": sub, "eligible": e, "available": avail[sub],
                                 "available_prompts": prompts[sub], "target": q, "drawn": drawn[sub],
                                 "fraction": str(Fraction(drawn[sub], e)) if e else None})
                carry = n - len(taken)
    ids = [i["item"] for i in items]
    if len(set(ids)) != len(ids):
        raise Refusal("two drawn items share one item id")
    return items, cells, subs


def repeats(items: list, cfg: dict, step: str) -> list:
    """The hidden repeats (module doc), in their sealed draw order."""
    ids = sorted(i["item"] for i in items if i["block"] == inp.HARM)
    tags = cfg["seed_tags"]
    n = min(cfg["sizes"]["steps"][step]["repeats"], len(ids))
    return random.Random(derive_seed(tags["freeze_date"], tags["repeats"], inp.HARM)).sample(ids, n)


# ----- the run (draw and check share it) ----------------------------------------------------------------------------


@dataclass
class Result:
    key: bytes
    weights: bytes
    manifest: bytes
    totals: dict
    kit: dict                                     # plan.json and seal SHA-256, for the printed lines
    inputs: dict                                  # the pinned inputs' SHA-256, for the printed lines
    settings_sha256: str


def _modules(package: Path) -> dict:
    return {p.name: sha256_bytes(p.read_bytes()) for p in sorted(package.glob("*.py"))}


DEPENDENCIES = ("scripts.stage1_s1.reading.settings", "experiments.safety_selection.common", derive_seed.__module__)


def _dependencies() -> dict:
    """The SHA-256 of the other modules whose code the draw runs (canonical and strict JSON, derive_seed), by name."""
    return {name: sha256_bytes(Path(sys.modules[name].__file__).read_bytes()) for name in sorted(set(DEPENDENCIES))}


def run(kit_root: Path, repo: Path, rules, rules_sha256: str, oct9_path: Path, bank_manifest: Path, bank_path: Path,
        auditor_path: Path, step: str, cfg: dict | None = None) -> Result:
    """Every input in the order of inputs.py's module doc, then the draw; nothing is written here."""
    cfg = cfg or settings()
    if step not in cfg["sizes"]["steps"]:
        raise Refusal(f"the reduction step {step} is not one of the settings' steps {', '.join(STEPS)}")
    kit = inp.open_kit(kit_root, cfg)                       # plan A; seals A and B (block B complete) first
    oct9_data = inp.pinned_bytes(oct9_path, cfg["exclusions"]["oct9"]["key_sha256"], "the 9 Oct key")
    bank = inp.read_bank(bank_manifest, bank_path, auditor_path, cfg)
    units = inp.population(kit, repo, rules, cfg)           # the first unit folder opened
    for u in units:
        inp.read_answers(u, bank)
    hb_source = inp.harmbench(kit, units, rules, cfg)
    oct9 = inp.read_oct9(oct9_data, units, cfg)
    minors = minors_rule(bank, units, cfg)
    excluded = exclusions(units, oct9, minors, cfg)
    items, cells, subs = allocate(units, excluded, cfg, step)
    reps = repeats(items, cfg, step)
    shown_twice = set(reps)
    for i in items:
        i["repeat"] = i["item"] in shown_twice
    settings_sha = sha256_bytes(canonical_json(cfg))
    reasons = Counter(r for per in excluded.values() for r in per.values())
    per_unit = {u.label: {r: sum(1 for x in excluded[u.label].values() if x == r) for r in REASONS} for u in units}
    key = canonical_json({
        "kind": KEY_KIND, "version": 1, "settings_sha256": settings_sha, "reduction_step": int(step),
        "rule": cfg["draw_rule"], "seed_tags": cfg["seed_tags"],
        "units": {u.label: {"arm": u.arm, "seed": u.seed, "source": u.source, "path": u.path, "target": u.target,
                            "complete_sha256": u.folder.complete_sha256, "files": dict(sorted(u.folder.read.items()))}
                  for u in units},
        "items": items, "repeats": reps})
    weights = canonical_json({
        "kind": WEIGHTS_KIND, "version": 1, "settings_sha256": settings_sha, "reduction_step": int(step),
        "fraction_rule": "fraction = drawn / eligible per sub-cell (seed x Qwen3Guard label x HarmBench label for "
                         "the Unsafe cell; seed x label otherwise); eligible = the sub-cell's answers after the "
                         "exclusions, available = those whose prompt was not yet used inside the arm when the cell "
                         "started, available_prompts = their distinct prompts (per cell: of all its sub-cells), "
                         "target = what the walk was set to take (always taken); the analysis weights each answer by "
                         "the inverse fraction (HLC 4.2)",
        "cells": cells, "sub_cells": subs,
        "exclusions": {"per_unit": per_unit, "minors_prompts": minors, "order": list(REASONS)}})
    harm = sum(1 for i in items if i["block"] == inp.HARM)
    totals = {"units": len(units), "items": {"harm": harm, "benign": len(items) - harm, "all": len(items)},
              "repeats": len(reps),
              "excluded": {"oct9_answers": reasons["oct9"], "minors_answers": reasons["minors"],
                           "minors_prompts": {"rule_a": len(minors["rule_a"]), "rule_b": len(minors["rule_b"])},
                           "unscored_answers": reasons["unscored"], "answers_without_a_label": reasons["no_label"]}}
    kit_rec = {"plan_sha256": kit.plan_sha256, "plan_code": kit.plan_code(),
               "seals": {b: kit.seal(b).sha256 for b in cfg["blocks"]["sealed_before_any_unit_is_opened"]}}
    pinned = {"oct9_key": sha256_bytes(oct9_data), **bank.hashes}
    manifest = canonical_json({
        "kind": MANIFEST_KIND, "version": 1, "protocol": cfg["protocol"], "requirement": cfg["requirement"],
        "deadline": cfg["deadline"], "settings_sha256": settings_sha, "reduction_step": int(step),
        "cut": cfg["sizes"]["steps"][step]["cut"],
        "tool": {"modules": _modules(HERE), "reading_input_modules": _modules(Path(ri.__file__).resolve().parent),
                 "dependencies": _dependencies(), "rules_sha256": rules_sha256, "python": platform.python_version()},
        "kit": kit_rec,
        "inputs": {"units": {u.label: {"source": u.source, "complete_sha256": u.folder.complete_sha256,
                                       "files": dict(sorted(u.folder.read.items()))} for u in units},
                   "harmbench": hb_source, **pinned},
        "seed_tags": cfg["seed_tags"], "totals": totals,
        "outputs": {"key": {"file": cfg["outputs"]["key"], "sha256": sha256_bytes(key)},
                    "weights": {"file": cfg["outputs"]["weights"], "sha256": sha256_bytes(weights)}},
        "not_built": cfg["not_built"],
        "rule": "text-free: totals and SHA-256 values only, no count per arm, seed or cell (HLC 4.3 item 3)"})
    return Result(key, weights, manifest, totals, kit_rec, {**pinned, "harmbench_cache": hb_source["cache_sha256"]},
                  settings_sha)
