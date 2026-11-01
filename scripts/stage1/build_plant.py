"""REQ-8: the plant (RS B9; PLAN-S section 6) [D5-8], with the W1-09 decoy and the F9 locations (conditional).
Mac, CPU, $0; the lead runs it on the real files. It prints counts and hashes only.

Two settings files, each loaded by its literal SHA-256: T1's ``settings/build_plant.json`` (the rule, byte-identical
since T1: rows, the L12 grouping and placement, the draws, the edits, the stops) and ``settings/build_plant_extra.json``
(the W1-09 decoy, the F9 locations, the inputs T1 left to the command line, and the pair-enumeration method).

1. **Plant rows** (build_plant.json "rows"): a PKU response with is_safe true and lexicon class DIRECT, in a record whose
   other response is unsafe; REQ-6's filters 1-6 with REQ-6's labels (build_s_pool.run_filters); then
   overlap_with_an_s_pool_candidate (the normalized prompt of any REQ-6 candidate, recomputed from the same PKU rows),
   overlap_with_an_anchor_prompt, overlap_with_a_req6_list_prompt; then the first per normalized prompt. The sealed
   order plant.rows; the first 75 (the first 37 nested); fewer than 75: stop with counts. Row j is add-plant-NNN.
2. **Grouping** (L12): within each unit, a link between two rows whose normalized prompts have character 5-gram Jaccard
   >= the manifest's max_jaccard (which must be 0.5); single-linkage components; a component of more than 37 rows is
   oversize (its rows are singletons). Candidate pairs are enumerated by prefix filtering (each row's rarest-first
   shingle prefix of |A| - ceil(|A| / 2) + 1 shingles; a pair at Jaccard >= 0.5 shares a prefix shingle, so no pair is
   missed); every candidate pair's Jaccard is then computed exactly. Cross-unit pairs are counted only. The record
   publishes the component-size histogram per unit, every oversize component's size and cross-cell pair counts, and
   each other non-singleton component's size with its M = 32 and M = 128 cell (T1 placement.published).
3. **Placement**: quartiles by (target tokens, sealed rank plant.quartile_ties), quarters by the sealed order
   plant.quarters within each quartile; whole components into the current cell; cell j closes once the cells so far
   hold floor((j + 1) n / 4) rows, one cell per placement; an empty cell stops.
4. **Draws**: the unit (plant.unit), then the leaf (plant.leaf) among the unit's 37-row leaves with no oversize row,
   else its no-oversize leaves with the smallest |n - 37|; never a redraw.
5. **Edits** (relative to P; REQ-7's writer functions): planted_k37/k75 (combined), remove_cell_m8/m32/m128 (remove),
   r600_k<k>_d<d> and r150_k<k>_d<d> (combined; draw d at seed 1100 + d).
6. **The decoy** (W1-09): 37 S-pool rows outside S1, the S3 subset and the S4 candidates (sealed order plant.decoy_rows),
   placed for the rank replay in a leaf (plant.decoy_leaf, by the plant's leaf rule) of a unit other than the plant's
   (plant.decoy_unit). Never trained; no edit file; REQ-3's pool "decoy".
7. **F9** (only with --f9: the lead passes it only after the user's yes and stage 1b's funding event): locations 2 and 3,
   each a unit drawn without replacement from the units other than the plant's (plant.extra_unit, part = location) and
   a leaf by the plant's leaf rule (plant.extra_leaf, part = location); the same 75 plant rows and the same edit rules.

Writes the files that hold text (the plant rows, REQ-3's pools "plant" and "decoy", every edit with add rows) under
--full-out (inside a folder named tmp); the remove-only edits and the text-free record (plant_record.json) into --out.
Both folders must be absent or empty before anything is written.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import build_s_pool as bsp  # noqa: E402
from scripts.stage1 import lexicon_pin  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import token_accounting as ta  # noqa: E402
from scripts.stage1 import write_add_edit as wae  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "build_plant.json"
SETTINGS_SHA256 = "06f70d98af8ac16d79067863142a408f0e65862463305975579f075763f8687e"
SETTINGS_NAME = "build_plant"
EXTRA_PATH = HERE / "settings" / "build_plant_extra.json"
EXTRA_SHA256 = "df5f047275aecbe671b1e58762ecc9e19906b8a0f304c99b977ee6d3d9718dac"
EXTRA_NAME = "build_plant_extra"
RECORD = "plant_record.json"
K, K_RAISE, OVERSIZE, ROWS_PER_STEP = 37, 75, 37, 128


# ----- the near-duplicate grouping (L12) --------------------------------------------------------------------


def shingle_sets(prompts: dict[str, str]) -> dict[str, frozenset]:
    from experiments.safety_selection.prepare import _shingles
    from experiments.safety_selection.textproc import normalize

    return {row: _shingles(normalize(text)) for row, text in prompts.items()}


def jaccard(a: frozenset, b: frozenset) -> float:
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter)


def linked_pairs(sets: dict[str, frozenset], threshold: float) -> list[tuple[str, str]]:
    """Every pair (sorted ids) with Jaccard >= threshold, by prefix filtering (lossless) and an exact check."""
    if threshold != 0.5:
        raise s1.Refusal(f"the prefix length here is for a threshold of 0.5, not {threshold}")
    frequency = Counter(s for shingles in sets.values() for s in shingles)
    index: dict[str, list[str]] = {}
    pairs = set()
    for row in sorted(sets):
        ordered = sorted(sets[row], key=lambda s: (frequency[s], s))
        prefix = ordered[:len(ordered) - (len(ordered) + 1) // 2 + 1]
        seen = set()
        for shingle in prefix:
            for other in index.get(shingle, ()):
                if other not in seen:
                    seen.add(other)
                    if jaccard(sets[row], sets[other]) >= threshold:
                        pairs.add((other, row) if other < row else (row, other))
            index.setdefault(shingle, []).append(row)
    return sorted(pairs)


def components(members: list[str], pairs: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Single-linkage components: row -> its component's sorted members."""
    parent = {r: r for r in members}

    def find(r):
        while parent[r] != r:
            parent[r] = parent[parent[r]]
            r = parent[r]
        return r
    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    groups: dict[str, list[str]] = {}
    for r in members:
        groups.setdefault(find(r), []).append(r)
    return {r: sorted(groups[find(r)]) for r in members}


def walk(order: list[str], component_of: dict[str, list[str]], n: int) -> list[list[str]]:
    """build_plant.json "placement": whole components into the current cell; only the current cell can close."""
    cells, j, total, placed = [[], [], [], []], 0, 0, set()
    for row in order:
        if row in placed:
            continue
        component = component_of[row]
        placed |= set(component)
        cells[j] += component
        total += len(component)
        if j < 3 and total >= math.floor((j + 1) * n / 4):
            j += 1
    return [sorted(c) for c in cells]


def place(view: s1.PreparedView, prompts: dict[str, str], max_jaccard: float) -> dict:
    """The L12 grouping and the M = 32 and M = 128 cells of every unit, with the published counts."""
    sets = shingle_sets(prompts)
    pairs = linked_pairs(sets, max_jaccard)
    same = [(a, b) for a, b in pairs if view.unit_of[a] == view.unit_of[b]]
    cross = len(pairs) - len(same)
    all_ids = sorted(view.tokens)
    tie_rank = s1.sealed_rank(all_ids, "plant.quartile_ties")
    quarter_order = s1.sealed_order(all_ids, "plant.quarters")
    cells, oversize, component_of, histogram, groups = {}, [], {}, {}, []
    for g in view.units:
        members = sorted(view.members[g])
        comp = components(members, [(a, b) for a, b in same if view.unit_of[a] == g])
        sizes = Counter(len(c) for c in {tuple(c) for c in comp.values()})
        histogram[g] = {str(size): count for size, count in sorted(sizes.items())}
        for c in {tuple(c) for c in comp.values()}:
            if len(c) > OVERSIZE:
                oversize.append(list(c))
            elif len(c) > 1:
                groups.append(list(c))
        place_of = {r: (comp[r] if len(comp[r]) <= OVERSIZE else [r]) for r in members}
        component_of.update(comp)
        order = sorted(members, key=lambda r: (view.tokens[r], tie_rank[r]))
        quartiles = walk(order, place_of, len(members))
        for j, quartile in enumerate(quartiles):
            cells[f"{g}/q{j}"] = quartile
            inside = set(quartile)
            quarters = walk([r for r in quarter_order if r in inside], place_of, len(quartile))
            for i, quarter in enumerate(quarters):
                cells[f"{g}/q{j}/r{i}"] = quarter
    empty = sorted(c for c, rows in cells.items() if not rows)
    if empty:
        raise s1.Refusal(f"{len(empty)} cells are empty (first: {empty[0]}): stop with counts only")
    cell_of = {lvl: {r: c for c, rows in cells.items() if c.count("/") == lvl for r in rows} for lvl in (1, 2)}
    over = []
    for c in sorted(oversize):
        inside = set(c)
        cpairs = [(a, b) for a, b in same if a in inside and b in inside]
        over.append({"unit": view.unit_of[c[0]], "size": len(c),
                     "cross_cell_pairs_m32": sum(cell_of[1][a] != cell_of[1][b] for a, b in cpairs),
                     "cross_cell_pairs_m128": sum(cell_of[2][a] != cell_of[2][b] for a, b in cpairs)})
    # T1 placement.published: each (non-singleton, non-oversize) component's size and its cell; a component moves
    # whole, so one M = 32 cell and one M = 128 cell hold every row of it (an oversize component is listed above)
    placed_components = [{"unit": view.unit_of[c[0]], "size": len(c), "cell_m32": cell_of[1][c[0]],
                          "cell_m128": cell_of[2][c[0]]} for c in sorted(groups)]
    cut_points = {}
    for g in view.units:
        cut_points[g] = [{"cell": f"{g}/q{j}", "rows": len(cells[f"{g}/q{j}"]),
                          "first_target_tokens": min(view.tokens[r] for r in cells[f"{g}/q{j}"]),
                          "last_target_tokens": max(view.tokens[r] for r in cells[f"{g}/q{j}"])} for j in range(4)]
    return {"cells": cells, "oversize_rows": sorted(r for c in oversize for r in c), "report": {
        "links_within_units": len(same), "cross_unit_pairs": cross, "component_sizes": histogram,
        "components": placed_components, "oversize_components": over,
        "cell_sizes": {c: len(rows) for c, rows in sorted(cells.items())}, "quartile_cut_points": cut_points}}


def draw_leaf(view: s1.PreparedView, placed: dict, unit: str, key: str, *parts) -> dict:
    """build_plant.json "draws.leaf" in one unit, under the given key: the unit's 37-row leaves with no oversize row,
    else its no-oversize leaves with the smallest |n - 37|; the first in the sealed order."""
    bad = set(placed["oversize_rows"])
    leaves = {c: rows for c, rows in placed["cells"].items() if c.startswith(unit + "/") and c.count("/") == 2}
    eligible = {c: rows for c, rows in leaves.items() if not set(rows) & bad}
    if not eligible:
        raise s1.Refusal(f"unit {unit} has no eligible leaf (every leaf holds an oversize row): stop with counts only")
    exact = [c for c, rows in eligible.items() if len(rows) == K]
    if exact:
        branch, candidates = "37-row", exact
    else:
        best = min(abs(len(rows) - K) for rows in eligible.values())
        branch, candidates = "fallback", [c for c, rows in eligible.items() if abs(len(rows) - K) == best]
    cell = s1.sealed_order(candidates, key, *parts)[0]
    return {"unit": unit, "cell": cell, "rows": eligible[cell], "n": len(eligible[cell]), "branch": branch,
            "candidates": len(candidates)}


def decoy_unit_of(units: list[str], plant_unit: str) -> str:
    """W1-09: the first of the sealed order plant.decoy_unit over the units other than the planted unit."""
    return s1.sealed_order([g for g in units if g != plant_unit], "plant.decoy_unit")[0]


def extra_units_of(units: list[str], plant_unit: str, locations) -> dict:
    """F9: location l's unit is the first of the sealed order plant.extra_unit, part (l), over the units other than the
    planted unit's and the earlier locations' (without replacement)."""
    taken, out = {plant_unit}, {}
    for loc in locations:
        g = s1.sealed_order([u for u in units if u not in taken], "plant.extra_unit", loc)[0]
        taken.add(g)
        out[loc] = g
    return out


# ----- the plant rows -------------------------------------------------------------------------------------------


def plant_rows(sources_rows, classify, filter_inputs: dict, s_pool: dict, lists: dict, anchors: list[str]) -> dict:
    from experiments.safety_selection.textproc import normalize

    cands = bsp.candidates_of(sources_rows, classify, "DIRECT")
    result = bsp.run_filters(cands, **filter_inputs, stages=bsp.FILTERS[:-1])
    s_cands = bsp.candidates_of(sources_rows, classify)
    if not {i["id"] for i in s_pool["items"]} <= {bsp.uid(r) for r in s_cands}:
        raise s1.Refusal("the S-pool file names rows that are not REQ-6 candidates of these PKU files")
    s_prompts = {normalize(r["prompt"]) for r in s_cands}
    anchor_prompts = {normalize(a) for a in anchors}
    list_prompts = {normalize(i["prompt"]) for doc in lists.values() for i in doc["items"]}
    rows, counts, n_after = result["pool"], dict(result["filters"]), dict(result["n_after"])
    for stage, reason, banned in (("s_pool_overlap", "overlap_with_an_s_pool_candidate", s_prompts),
                                  ("anchor_overlap", "overlap_with_an_anchor_prompt", anchor_prompts),
                                  ("list_overlap", "overlap_with_a_req6_list_prompt", list_prompts)):
        kept = [r for r in rows if normalize(r["prompt"]) not in banned]
        counts[stage] = {"removed": len(rows) - len(kept), "by_reason": {reason: len(rows) - len(kept)} if len(rows) > len(kept) else {}}
        n_after[stage] = len(kept)
        rows = kept
    seen, kept = set(), []
    for r in rows:
        key = normalize(r["prompt"])
        if key not in seen:
            seen.add(key)
            kept.append(r)
    counts["first_per_prompt"] = {"removed": len(rows) - len(kept),
                                  "by_reason": {"duplicate_prompt": len(rows) - len(kept)} if len(rows) > len(kept) else {}}
    n_after["first_per_prompt"] = len(kept)
    if len(kept) < K_RAISE:
        raise s1.Refusal(f"{len(kept)} plant candidates remain after the exclusions, fewer than {K_RAISE}: stop with "
                         f"counts only ({n_after})")
    by_id = {bsp.uid(r): r for r in kept}
    order = s1.sealed_order(list(by_id), "plant.rows")[:K_RAISE]
    rows75 = [{"add_id": wae.add_id("plant", j), "source_id": rid, "prompt": by_id[rid]["prompt"],
               "response": by_id[rid]["response"]} for j, rid in enumerate(order, start=1)]
    return {"rows": rows75, "counts": counts, "n_after": n_after, "candidates": len(cands)}


# ----- edits ----------------------------------------------------------------------------------------------------


class Writer:
    """Edit files through REQ-7's functions: s1.edit_document, the engine's parse_edit, edited_corpus for add rows."""

    def __init__(self, view, tokens, codec, max_train_tokens, provenance):
        self.view, self.tokens, self.codec, self.max = view, tokens, codec, max_train_tokens
        self.stub, self.prov = view.engine_stub(), provenance
        self.full, self.out, self.entries = {}, {}, []

    def write(self, name: str, title: str, removed, adds: list[dict]) -> None:
        kind = "combined" if removed and adds else ("add" if adds else "remove")
        doc = s1.edit_document(name=title, edit_kind=kind, manifest_sha256=self.view.manifest_sha256,
                               remove=sorted(removed), add=[(a["add_id"], a["prompt"], a["response"]) for a in adds],
                               provenance={**self.prov, "edit": name})
        data, edit = s1.checked_edit(doc, self.stub)
        per_add = wae.encode_adds(doc, data, self.stub, self.codec, self.max) if adds else {}
        account = ta.account(self.tokens, removed=sorted(removed), added=per_add, rows_per_step=ROWS_PER_STEP)
        (self.full if adds else self.out)[f"edits/{name}.json"] = data
        self.entries.append({"file": f"edits/{name}.json", "sha256": sha256_bytes(data), "arm": edit.arm,
                             "edit_kind": kind, "removed": len(removed), "added": len(adds),
                             "final_rows": account["edited_corpus"]["rows"], "steps": account["edited_corpus"]["steps"],
                             "tokens": account})


def planted_members(view: s1.PreparedView, leaf: dict, k: int) -> dict[str, list[str]]:
    out = {g: sorted(view.members[g]) for g in view.units}
    out[leaf["unit"]] = sorted((set(view.members[leaf["unit"]]) - set(leaf["rows"]))
                               | {wae.add_id("plant", j) for j in range(1, k + 1)})
    return out


def write_location(writer: Writer, view, placed, leaf, rows75, suffix: str = "") -> None:
    unit, quartile = leaf["unit"], leaf["cell"].rsplit("/", 1)[0]
    for k in (K, K_RAISE):
        writer.write(f"planted_k{k}{suffix}", f"stage1 plant{suffix}: planted corpus at k = {k} (leaf {leaf['cell']})",
                     leaf["rows"], rows75[:k])
    writer.write(f"remove_cell_m128{suffix}", f"stage1 plant{suffix}: remove the planted cell at M = 128",
                 leaf["rows"], [])
    writer.write(f"remove_cell_m32{suffix}", f"stage1 plant{suffix}: remove the planted cell at M = 32",
                 placed["cells"][quartile], [])
    writer.write(f"remove_cell_m8{suffix}", f"stage1 plant{suffix}: remove the planted cell at M = 8",
                 view.members[unit], [])


def write_random(writer: Writer, view, leaf, rows75) -> dict:
    seeds = {}
    for k in (K, K_RAISE):
        members = planted_members(view, leaf, k)
        adds = {a["add_id"]: a for a in rows75[:k]}
        for d in (1, 2, 3):
            drawn600 = {r for g in view.units for r in s1.sealed_sample(members[g], 75, "plant.r600", d, g)}
            six = set(s1.sealed_sample(view.units, 6, "plant.r150_units", d))
            drawn150 = {r for g in view.units
                        for r in s1.sealed_sample(members[g], 19 if g in six else 18, "plant.r150", d, g)}
            for name, drawn in ((f"r600_k{k}_d{d}", drawn600), (f"r150_k{k}_d{d}", drawn150)):
                removed = set(leaf["rows"]) | {r for r in drawn if r not in adds}
                kept = [adds[a] for a in sorted(adds) if a not in drawn]
                writer.write(name, f"stage1 plant: {name} ({len(drawn)} rows drawn from the planted corpus)",
                             removed, kept)
                seeds[name] = 1100 + d
    return seeds


# ----- the build ------------------------------------------------------------------------------------------------


def read_text_file(path: Path, digest: str, kind: str, what: str) -> dict:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {digest}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != kind or not isinstance(doc.get("items"), list):
        raise s1.Refusal(f"{what} is not a {kind!r}")
    return {**doc, "sha256": digest}


def build(*, prepared_root: Path, config_path: Path, sources_root: Path, anchors_path: Path, rec_path: Path,
          recipe_path: Path, s_pool: tuple[Path, str], lists: dict[str, tuple[Path, str]], codec, settings: dict,
          extra: dict, settings_sha256: str, extra_sha256: str, f9: bool = False) -> tuple[dict, dict]:
    from experiments.safety_selection.config import config_sha256, load_recipe
    from experiments.safety_selection.prepare import load_prepared

    s1.check_settings(settings, SETTINGS_NAME)
    s1.check_settings(extra, EXTRA_NAME)
    pins, xpins = settings["inputs"], extra["inputs"]
    anch = bsp.load_anch(bsp.engine_root() / xpins["anch"]["path"], xpins["anch"]["sha256"])
    config, config_sha = bsp.anch_call(anch.load_config, config_path, pins["pku"]["config_sha256"])
    limits = bsp.recipe_limits(rec_path, xpins["rec_recipe_sha256"])
    recipe = load_recipe(recipe_path)
    if config_sha256(recipe) != xpins["recipe_sha256"]:
        raise s1.Refusal(f"recipe S hashes to {config_sha256(recipe)}, the settings pin {xpins['recipe_sha256']}")
    manifest_sha = settings["prepared"]["manifest_sha256"]
    view = s1.PreparedView(prepared_root, manifest_sha)
    view.check_shape(settings["prepared"]["rows"], settings["prepared"]["units"], settings["prepared"]["rows_per_unit"])
    tokens = ta.TokenView(prepared_root, manifest_sha)
    prepared = load_prepared(prepared_root, manifest_sha)
    max_jaccard = prepared.manifest["data_config"]["eligibility"]["near_duplicate"]["max_jaccard"]
    if max_jaccard != settings["near_duplicate_grouping"]["threshold"]["expected_value"]:
        raise s1.Refusal(f"P's near-duplicate threshold is {max_jaccard}, not 0.5: stop")
    prompts = {r: prepared.train_rows[r]["prompt"] for r in view.tokens}
    sources = bsp.anch_call(anch.read_sources, config, sources_root)
    evaluation = bsp.anch_call(anch.load_evaluation, prepared_root, manifest_sha)
    by_bank = bsp.evaluation_by_bank(prepared_root, manifest_sha, anch)
    if [f for b in bsp.BANK_NAMES for f in by_bank[b]] != evaluation["evaluation"]:
        raise s1.Refusal("the per-bank evaluation forms differ from ANCH's evaluation list")
    if evaluation["forms"] != xpins["expected_evaluation_forms"]:
        raise s1.Refusal(f"P has {evaluation['forms']} evaluation forms, the settings expect "
                         f"{xpins['expected_evaluation_forms']}")
    anchors = bsp.anchor_prompts(anchors_path, pins["anchor_prompts_sha256"], anch)
    pool_doc = read_text_file(*s_pool, "stage1 s-pool", "the S-pool file")
    list_docs = {name: read_text_file(*lists[name], wae.LIST_KIND, f"list {name}") for name in xpins["lists"]}
    pool_ids = {i["id"] for i in pool_doc["items"]}
    if any(not {i["id"] for i in d["items"]} <= pool_ids for d in list_docs.values()):
        raise s1.Refusal("a REQ-6 list names rows outside the S-pool file")
    lexicon = lexicon_pin.load()
    forbidden = sorted(set(config["eligibility"]["forbidden_substrings"]) | set(evaluation["forbidden"]))
    filter_inputs = {"forbidden": forbidden, "existing": evaluation["existing"], "anchors": anchors,
                     "evaluation": by_bank, "max_jaccard": config["injection"]["near_duplicate"]["max_jaccard"],
                     "codec": codec, "limits": limits}
    plant = plant_rows(sources["rows"], lexicon.classify, filter_inputs, pool_doc, list_docs, anchors)
    rows75 = plant["rows"]

    placed = place(view, prompts, max_jaccard)
    unit = s1.sealed_order(view.units, "plant.unit")[0]
    leaf = draw_leaf(view, placed, unit, "plant.leaf")

    inputs = {"prepared_manifest": manifest_sha, "data_config": config_sha, "anch": xpins["anch"]["sha256"],
              "anchor_prompts": pins["anchor_prompts_sha256"], "rec_recipe": xpins["rec_recipe_sha256"],
              "recipe_s": xpins["recipe_sha256"], "s_pool": pool_doc["sha256"], "build_plant_extra": extra_sha256,
              **{f"list_{n}": d["sha256"] for n, d in list_docs.items()},
              **{f"source_{k}": v for k, v in sorted(sources["hashes"].items())}}
    entries = {**settings["label_entries"], **extra["label_entries"]}
    prov = s1.provenance(Path(__file__).resolve(), settings_sha256, inputs, entries)
    writer = Writer(view, tokens, codec, recipe["model"]["max_train_tokens"], prov)
    write_location(writer, view, placed, leaf, rows75)
    seeds = write_random(writer, view, leaf, rows75)

    # the decoy (W1-09): never trained; no edit file
    used = set().union(*({i["id"] for i in d["items"]} for d in list_docs.values()))
    decoy_ids = s1.sealed_order(sorted(pool_ids - used), "plant.decoy_rows")[:extra["decoy"]["rows"]]
    if len(decoy_ids) < extra["decoy"]["rows"]:
        raise s1.Refusal(f"only {len(decoy_ids)} S-pool rows lie outside the lists: the decoy needs {extra['decoy']['rows']}")
    decoy_unit = decoy_unit_of(view.units, unit)
    decoy_leaf = draw_leaf(view, placed, decoy_unit, "plant.decoy_leaf")
    by_pool_id = {i["id"]: i for i in pool_doc["items"]}

    locations = {}
    if f9:
        for loc, g in extra_units_of(view.units, unit, extra["f9"]["locations"]).items():
            locations[str(loc)] = draw_leaf(view, placed, g, "plant.extra_leaf", loc)
            write_location(writer, view, placed, locations[str(loc)], rows75, f"_loc{loc}")

    full = dict(writer.full)
    full["plant_rows.json"] = canonical_json({"kind": "stage1 plant rows", "version": 1, "items": rows75})
    full["plant.pool.json"] = canonical_json({"kind": "stage1 text pool", "version": 1, "name": "plant",
                                              "items": [{"id": a["add_id"], "prompt": a["prompt"],
                                                         "response": a["response"]} for a in rows75]})
    full["decoy.pool.json"] = canonical_json({"kind": "stage1 text pool", "version": 1, "name": "decoy",
                                              "items": [{"id": i, "prompt": by_pool_id[i]["prompt"],
                                                         "response": by_pool_id[i]["response"]} for i in decoy_ids]})
    leaf_record = {k: v for k, v in leaf.items() if k != "rows"}
    record = {
        "kind": "stage1 plant record", "version": 1, "requirement": settings["requirement"],
        "plant_rows": {"candidates": plant["candidates"], "n_after_each_filter": plant["n_after"],
                       "filters": plant["counts"], "ids": [a["add_id"] for a in rows75],
                       "source_ids": [a["source_id"] for a in rows75]},
        "grouping": placed["report"], "unit": unit, "leaf": leaf_record,
        "corpus": {"planted_k37_rows": 4800 - leaf["n"] + K, "planted_k75_rows": 4800 - leaf["n"] + K_RAISE},
        "edits": writer.entries, "seeds": seeds,
        "decoy": {"ids": decoy_ids, "unit": decoy_unit, "leaf": {k: v for k, v in decoy_leaf.items() if k != "rows"},
                  "pool_sha256": sha256_bytes(full["decoy.pool.json"])},
        "f9": {"run": f9, "locations": {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in locations.items()}},
        "pools": {"plant": {"sha256": sha256_bytes(full["plant.pool.json"]), "items": len(rows75)},
                  "decoy": {"sha256": sha256_bytes(full["decoy.pool.json"]), "items": len(decoy_ids)}},
        "full_files": {n: sha256_bytes(d) for n, d in sorted(full.items())},
        "provenance": prov}
    out = dict(writer.out)
    out[RECORD] = canonical_json(record)
    texts = [t for a in rows75 for t in (a["prompt"], a["response"])] + \
        [t for i in decoy_ids for t in (by_pool_id[i]["prompt"], by_pool_id[i]["response"])]
    if any(s1._text_hits(data, texts) for data in out.values()):
        raise s1.Refusal("a text-free output would hold text")
    return full, out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for flag in ("--prepared", "--config", "--sources", "--anchors", "--rec", "--recipe", "--full-out", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--s-pool", required=True, help="PATH:SHA256 of REQ-6's s_pool.json")
    parser.add_argument("--list", action="append", default=[], help="NAME=PATH:SHA256 of a REQ-6 list")
    parser.add_argument("--f9", action="store_true", help="also the two F9 locations (only after the user's yes)")
    args = parser.parse_args(argv)
    folders = []
    try:
        settings, digest = s1.load_settings(SETTINGS_PATH, SETTINGS_SHA256, SETTINGS_NAME)
        extra, extra_digest = s1.load_settings(EXTRA_PATH, EXTRA_SHA256, EXTRA_NAME)
        path, _, sha = args.s_pool.rpartition(":")
        lists = {}
        for spec in args.list:
            name, _, rest = spec.partition("=")
            p, _, h = rest.rpartition(":")
            lists[name] = (Path(p), h)
        if set(lists) != set(extra["inputs"]["lists"]):
            raise s1.Refusal(f"give exactly the lists {sorted(extra['inputs']['lists'])}")
        folders = bsp.check_output_folders(wae.full_out_ok(args.full_out), args.out)
        full_out, out_dir = folders
        codec = bsp.real_codec(args.prepared, {"inputs": {"prepared_manifest_sha256": settings["prepared"]["manifest_sha256"]}})
        full, out = build(prepared_root=args.prepared, config_path=args.config, sources_root=args.sources,
                          anchors_path=args.anchors, rec_path=args.rec, recipe_path=args.recipe,
                          s_pool=(Path(path), sha), lists=lists, codec=codec, settings=settings, extra=extra,
                          settings_sha256=digest, extra_sha256=extra_digest, f9=args.f9)
        written = s1.write_new_files(full_out, full)
        written.update(s1.write_new_files(out_dir, out))
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} ({bsp.refusal_state(folders)})",
              file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
