"""W1-08 (REQ-29; REV3 sections 8.4-8.5; LW-10 F2, F4, F6, F7, F8): the plant-rank report. Mac, $0, report only; the
lead runs it after REQ-3's and REQ-23's pod outputs exist. It prints counts and hashes only.

    python scripts/stage1/report_plant_ranks.py --prepared P --plant-record PATH:SHA256 --plant-pool PATH:SHA256 \
        --decoy-pool PATH:SHA256 --rows PATH:SHA256 --summary PATH:SHA256 [--l1 PATH:SHA256] \
        [--datashield PATH:SHA256] [--classifier PATH:SHA256] [--counted NAME=PATH:SHA256 ...] --out DIR

**Cells.** REQ-8's own placement (build_plant.place on P, rerun here; it must reproduce the plant record's cell sizes):
M = 8 the units, M = 32 the quartiles, M = 128 the leaves. The planted corpus (k = 37) is P with the drawn leaf's
Dolly rows replaced by the first 37 plant rows, so the planted cell at M = 128 is the 37 plant rows and its quartile
and unit hold them. A cell's score is the mean of its rows' scores (math.fsum / count; ADD L15 (6)); a cell's rank is
1 + the number of cells with a strictly larger score, and the cells with an equal score are reported as ties.

**Per scorer:**
- the planted cell's rank at M = 8, 32 and 128 on the planted corpus and, beside it, the same cell's rank without the
  plant (on P);
- the row AUC of the plant rows against all Dolly rows of the planted corpus and against the drawn unit's Dolly rows
  (Mann-Whitney: a tie counts 0.5), each with a bootstrap 90% interval: resampling within the plant rows and within the
  Dolly rows, the generator of registry key plant.auc_boot with parts (scorer, comparison), the replicate count and the
  quantile rule of the settings;
- F4, the dilution table: N = the number of M = 128 leaves, r = the planted leaf's rank among them with ties counted
  above it (1 + larger + equal), and for each menu M, m = M - 1 competitors: P(first among m competitors) =
  C(N - r, m) / C(N - 1, m), the options effect at the leaf's fixed share, beside the observed rank at M (diluted);
- F6, the relocation replay: the same 37 plant rows placed in every eligible leaf (exactly 37 rows, no oversize row),
  each leaf's ranks at the three menus, and per menu the share of leaves ranked first and the mean rank;
- F7, the decoy beside the plant: the decoy rows placed in their own sealed leaf (REQ-8's record), their cell ranks and
  AUCs (with intervals; comparisons decoy_all_dolly and decoy_unit_dolly).

**Roles (MSG-06; ADD-8.2; LW-10 F2, F8).** The text-only scorers (L1, H1, H2a, H2b, DataShield-style, the content
classifier) are construction checks: their planted ranks are fixed when the plant is drawn, published before the pilot,
and never count toward "finds a known cause". Only the training-signal diagnostics scored on a0_plant count: A1, and
Self-Inf-N-style while the settings' switch says REQ-13 was committed at W1. With the switch off, Self-Inf-N-style
leaves both the scorer list and the counting rule, and a --counted selfinf_n input refuses. A counted scorer's input is
a T1 scorer output over the planted corpus's ids exactly (an S1 run); without it the report says "not run (S1)". Its
replay, decoy and no-plant ranks are not defined (its scores depend on the training corpus).

**Scores of the plant and decoy rows.** L1 and DataShield-style: from REQ-3's rows file, at the index and read that the
scorer output's provenance names (its dev scores must be reproduced exactly from the same file first). H1 = minus the
target tokens, H2b = the target tokens: REQ-3's n_tokens - n_prompt (a dev row's must equal P's target_tokens). H2a =
1 or 0 by REQ-5's pinned rule, on the response text of P and of the two pool files (read in memory only). The
classifier: REQ-23's output (an unscored row is left out of its cell means and AUCs and counted). REQ-3's plant and
decoy pools must be pinned by the pool pins and must be the plant record's pools.
"""

from __future__ import annotations

import argparse
import math
import sys
from bisect import bisect_left, bisect_right
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "report_plant_ranks.json"
SETTINGS_SHA256 = "c952eb7275b4e73a8078c72d10f96cacdee6f4d3135e9a27fc1bd84c1480f973"
SETTINGS_NAME = "report_plant_ranks"
OUTPUT = "plant_ranks.json"
AUC_KEY = "plant.auc_boot"
MENUS = (8, 32, 128)


# ----- the pure core ----------------------------------------------------------------------------------------------


def levels_of(units: dict[str, list[str]], cells: dict[str, list[str]]) -> dict[int, dict[str, list[str]]]:
    """{8: the units, 32: the quartiles g/qj, 128: the leaves g/qj/ri} (with 8 units; REQ-8 fixes the shape): each
    unit splits into 4 quartiles and each quartile into 4 leaves, and every menu partitions the same rows."""
    out = {8: {g: sorted(rows) for g, rows in units.items()},
           32: {c: sorted(rows) for c, rows in cells.items() if c.count("/") == 1},
           128: {c: sorted(rows) for c, rows in cells.items() if c.count("/") == 2}}
    for coarse, fine in ((8, 32), (32, 128)):
        for cell, rows in out[coarse].items():
            parts = [c for c in out[fine] if c.rsplit("/", 1)[0] == cell]
            if len(parts) != 4 or sorted(r for c in parts for r in out[fine][c]) != rows:
                raise s1.Refusal(f"cell {cell} is not split into 4 cells of the next menu that hold its rows")
    if len(out[32]) != 4 * len(out[8]) or len(out[128]) != 4 * len(out[32]):
        raise s1.Refusal("a cell of a finer menu lies outside the coarser menu's cells")
    return out


def chain(leaf: str) -> dict[int, str]:
    """The leaf's cell at each menu: its unit, its quartile, itself."""
    unit, quartile, _ = leaf.split("/")
    return {8: unit, 32: f"{unit}/{quartile}", 128: leaf}


def mean_of(rows, scores: dict[str, float]):
    values = [scores[r] for r in rows if r in scores]
    return math.fsum(values) / len(values) if values else None


def means(levels: dict, scores: dict[str, float]) -> dict[int, dict[str, float | None]]:
    return {m: {c: mean_of(rows, scores) for c, rows in levels[m].items()} for m in MENUS}


def relocated(levels: dict, base: dict, scores: dict[str, float], leaf: str, new_rows: list[str]) -> dict:
    """The cell means after the leaf's rows are replaced by new_rows (only the leaf's three cells change)."""
    gone = set(levels[128][leaf])
    out = {m: dict(base[m]) for m in MENUS}
    for m, cell in chain(leaf).items():
        out[m][cell] = mean_of([r for r in levels[m][cell] if r not in gone] + list(new_rows), scores)
    return out


def rank(cell_means: dict[str, float | None], cell: str) -> dict:
    mine = cell_means[cell]
    if mine is None:
        raise s1.Refusal(f"cell {cell} has no scored row")
    others = [v for c, v in cell_means.items() if c != cell and v is not None]
    larger, equal = sum(v > mine for v in others), sum(v == mine for v in others)
    return {"rank": 1 + larger, "ties": equal, "cells": len(others) + 1, "mean": mine,
            "first": larger == 0 and equal == 0}


def auc(positives: list[float], negatives: list[float]) -> float:
    """P(a positive scores above a negative), a tie counting 0.5 (Mann-Whitney)."""
    if not positives or not negatives:
        raise s1.Refusal("an AUC needs rows on both sides")
    neg = sorted(negatives)
    wins = math.fsum(bisect_left(neg, x) + bisect_right(neg, x) for x in positives) / 2.0
    return wins / (len(positives) * len(neg))


def auc_interval(positives: list[float], negatives: list[float], replicates: int, level: float, *parts) -> list[float]:
    """The bootstrap interval of the AUC: resample within each side, the generator of plant.auc_boot with parts."""
    import numpy

    rng = s1.numpy_generator(AUC_KEY, *parts)
    pos, neg = numpy.asarray(positives, dtype=float), numpy.asarray(negatives, dtype=float)
    values = numpy.empty(replicates)
    for b in range(replicates):
        p = pos[rng.integers(0, len(pos), len(pos))]
        n = numpy.sort(neg[rng.integers(0, len(neg), len(neg))])
        values[b] = (numpy.searchsorted(n, p, "left") + numpy.searchsorted(n, p, "right")).sum() / (2.0 * len(n) * len(p))
    tail = (1.0 - level) / 2.0
    lo, hi = numpy.quantile(values, [tail, 1.0 - tail])
    return [float(lo), float(hi)]


def dilution(n: int, r: int, m: int) -> float:
    """F4: P(the item of rank r among n is first among m competitors drawn from the other n - 1) = C(n-r, m) / C(n-1, m)."""
    if not 1 <= r <= n or not 0 <= m <= n - 1:
        raise s1.Refusal(f"the dilution needs 1 <= r <= n and 0 <= m <= n - 1 (n {n}, r {r}, m {m})")
    return math.comb(n - r, m) / math.comb(n - 1, m)


def _auc_block(positives, negatives, settings, scorer, comparison) -> dict:
    boot = settings["bootstrap"]
    return {"auc": auc(positives, negatives), "positives": len(positives), "negatives": len(negatives),
            "interval": auc_interval(positives, negatives, boot["replicates"], boot["level"], scorer, comparison)}


def placement_block(levels: dict, base: dict, scores: dict, leaf: str, rows: list[str], settings: dict, scorer: str,
                    prefix: str, without: bool) -> dict:
    """Ranks at each menu after rows replace the leaf's, the AUCs against all Dolly rows and the unit's Dolly rows."""
    moved = relocated(levels, base, scores, leaf, rows)
    gone = set(levels[128][leaf])
    unit = chain(leaf)[8]
    positives = [scores[r] for r in rows if r in scores]
    dolly_all = [scores[r] for c in levels[8].values() for r in c if r not in gone and r in scores]
    dolly_unit = [scores[r] for r in levels[8][unit] if r not in gone and r in scores]
    return {"leaf": leaf, "unit": unit, "rows": len(rows), "scored_rows": len(positives),
            "ranks": {str(m): {"with_rows": rank(moved[m], cell), "without_rows": rank(base[m], cell) if without else None}
                      for m, cell in chain(leaf).items()},
            "auc": {f"{prefix}all_dolly": _auc_block(positives, dolly_all, settings, scorer, f"{prefix}all_dolly"),
                    f"{prefix}unit_dolly": _auc_block(positives, dolly_unit, settings, scorer, f"{prefix}unit_dolly")},
            "moved_means": moved}


def scorer_report(name: str, scores: dict[str, float], levels: dict, leaf: str, plant: list[str], decoy: dict | None,
                  eligible: list[str], settings: dict, counted: bool) -> dict:
    gone = set(levels[128][leaf])
    corpus = [r for c in levels[8].values() for r in c if not (counted and r in gone)] + list(plant)
    if not counted and decoy is not None:
        corpus += decoy["ids"]
    base = means(levels, scores)
    planted = placement_block(levels, base, scores, leaf, plant, settings, name, "", without=not counted)
    leaves = planted.pop("moved_means")[128]
    r = rank(leaves, leaf)
    n_leaves = len(levels[128])
    planted["dilution"] = {"n_leaves": n_leaves, "r_ties_above": r["rank"] + r["ties"],
                           "menus": {str(m): {"cells": len(levels[m]), "m": len(levels[m]) - 1,
                                              "p_first_fixed_share": dilution(n_leaves, r["rank"] + r["ties"],
                                                                              len(levels[m]) - 1),
                                              "observed_first": planted["ranks"][str(m)]["with_rows"]["first"]}
                                     for m in MENUS}}
    out = {"role": "counts toward finds a known cause" if counted else "construction check (never counts)",
           "unscored_ids": sum(1 for r in corpus if r not in scores), "planted": planted}
    if counted:
        out["replay"] = out["decoy"] = "not defined: a counted scorer's scores depend on the training corpus"
        return out
    replay = []
    for cell in eligible:
        moved = relocated(levels, base, scores, cell, plant)
        ranks = {str(m): rank(moved[m], c) for m, c in chain(cell).items()}
        replay.append({"leaf": cell, "ranks": {m: x["rank"] for m, x in ranks.items()},
                       "first": {m: x["first"] for m, x in ranks.items()}})
    out["replay"] = {"leaves": len(replay), "per_leaf": replay,
                     "summary": {str(m): {"share_first": sum(x["first"][str(m)] for x in replay) / len(replay),
                                          "mean_rank": math.fsum(x["ranks"][str(m)] for x in replay) / len(replay)}
                                 for m in MENUS} if replay else None}
    if decoy is None:
        out["decoy"] = "not built"
    else:
        block = placement_block(levels, base, scores, decoy["leaf"], decoy["ids"], settings, name, "decoy_", without=True)
        block.pop("moved_means")
        out["decoy"] = block
    return out


def eligible_leaves(levels: dict, oversize_rows, size: int) -> list[str]:
    """F6: every leaf with exactly `size` rows and no oversize row."""
    bad = set(oversize_rows)
    return sorted(c for c, rows in levels[128].items() if len(rows) == size and not set(rows) & bad)


def report(*, scores: dict[str, dict[str, float]], counted: dict[str, dict[str, float]], levels: dict, leaf: str,
           plant: list[str], decoy: dict | None, oversize_rows, settings: dict) -> dict:
    """The report body from the per-scorer scores (pure; no file input)."""
    eligible = eligible_leaves(levels, oversize_rows, settings["k"])
    switch = settings["counting"]["selfinf_n_counts"]
    counting = [s for s in settings["counting"]["scorers"] if s != "selfinf_n" or switch]
    if set(counted) - set(counting):
        raise s1.Refusal(f"a counted input is not on the counting list {counting} (the Self-Inf-N switch: {switch})")
    body = {"construction_checks": {}, "counting": {"scorers": counting, "selfinf_n_counts": switch,
                                                   "rule": settings["counting"]["rule"], "results": {}}}
    for name in settings["construction_checks"]:
        body["construction_checks"][name] = ("not run" if name not in scores else
                                             scorer_report(name, scores[name], levels, leaf, plant, decoy, eligible,
                                                           settings, counted=False))
    for name in counting:
        body["counting"]["results"][name] = ("not run (S1)" if name not in counted else
                                             scorer_report(name, counted[name], levels, leaf, plant, None, eligible,
                                                           settings, counted=True))
    body["eligible_leaves"] = len(eligible)
    return body


# ----- reading the inputs -----------------------------------------------------------------------------------------


def read_pinned(pair: tuple[Path, str], what: str) -> bytes:
    path, digest = pair
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {digest}")
    return data


def rep_lines(rows: tuple[Path, str], summary_doc: dict, record: dict, settings: dict) -> dict[str, dict]:
    if summary_doc.get("kind") != "stage1 representation pass" or summary_doc["rows"]["sha256"] != rows[1]:
        raise s1.Refusal("the rows file is not the one REQ-3's summary names")
    if summary_doc["provenance"]["settings_sha256"] != settings["pins"]["representation_pass_settings_sha256"]:
        raise s1.Refusal("REQ-3's summary was not made with the pinned REQ-3 settings")
    pools = {p["name"]: p for p in summary_doc["pools"]}
    for name in ("plant", "decoy"):
        entry = pools.get(name)
        if entry is None or entry["pinned_by"] != "pool pins" or entry["sha256"] != record["pools"][name]["sha256"]:
            raise s1.Refusal(f"REQ-3's pool {name} is not the plant record's pool pinned by the pool pins")
    return {line["id"]: line for line in s1.iter_jsonl_bytes(read_pinned(rows, "REQ-3's rows file"), "REQ-3's rows file")}


def rep_scores(out_doc: dict, scorer: str, rows_sha: str, lines: dict, ids: list[str], value) -> dict[str, float]:
    """A REQ-3-derived scorer's values for ids, after its dev scores are reproduced exactly from the same rows file."""
    if out_doc.get("kind") != "stage1 scorer output" or out_doc.get("scorer") != scorer:
        raise s1.Refusal(f"the {scorer} input is not a T1 scorer output of scorer {scorer}")
    if out_doc["provenance"]["inputs"].get("rows") != rows_sha:
        raise s1.Refusal(f"the {scorer} output was not made from this REQ-3 rows file")
    for rid, score in out_doc["scores"].items():
        if rid not in lines or lines[rid]["source"] != "dev" or value(lines[rid]) != score:
            raise s1.Refusal(f"the {scorer} output's dev scores are not reproduced from REQ-3's rows (row {rid})")
    missing = [r for r in ids if r not in lines]
    if missing:
        raise s1.Refusal(f"{len(missing)} plant or decoy rows have no REQ-3 line (first: {missing[0]})")
    return {**out_doc["scores"], **{r: value(lines[r]) for r in ids}}


def build(*, prepared_root: Path, plant_record: tuple[Path, str], plant_pool: tuple[Path, str],
          decoy_pool: tuple[Path, str], rows: tuple[Path, str], summary: tuple[Path, str],
          l1: tuple[Path, str] | None, datashield: tuple[Path, str] | None, classifier: tuple[Path, str] | None,
          counted: dict[str, tuple[Path, str]], settings: dict, settings_sha256: str) -> dict[str, bytes]:
    from experiments.safety_selection.prepare import load_prepared
    from scripts.stage1 import build_length_rules as bl
    from scripts.stage1 import build_plant as bp
    from scripts.stage1 import representation_pass as rp

    s1.check_settings(settings, SETTINGS_NAME)
    manifest = settings["pins"]["prepared_manifest_sha256"]
    view = s1.PreparedView(prepared_root, manifest)
    record = s1.strict_json(read_pinned(plant_record, "the plant record"))
    if record.get("kind") != "stage1 plant record" or record["provenance"]["inputs"].get("prepared_manifest") != manifest:
        raise s1.Refusal("the plant record is not REQ-8's record on this prepared set")
    plant_ids = record["plant_rows"]["ids"][:settings["k"]]
    decoy = {"leaf": record["decoy"]["leaf"]["cell"], "ids": list(record["decoy"]["ids"])}
    pools = {}
    for name, pair, want in (("plant", plant_pool, plant_ids), ("decoy", decoy_pool, decoy["ids"])):
        doc = rp.read_pool(*pair)
        if pair[1] != record["pools"][name]["sha256"] or not set(want) <= {i["id"] for i in doc["items"]}:
            raise s1.Refusal(f"the {name} pool is not the plant record's {name} pool")
        pools[name] = {i["id"]: i for i in doc["items"]}
    extra_ids = plant_ids + decoy["ids"]
    summary_doc = s1.strict_json(read_pinned(summary, "REQ-3's summary"))
    lines = rep_lines(rows, summary_doc, record, settings)

    def target(line):
        return line["n_tokens"] - line["n_prompt"]
    for rid, tokens in view.tokens.items():
        if rid not in lines or target(lines[rid]) != tokens:
            raise s1.Refusal(f"REQ-3's token counts disagree with P's target tokens (row {rid})")
    missing = [r for r in extra_ids if r not in lines]
    if missing:
        raise s1.Refusal(f"{len(missing)} plant or decoy rows have no REQ-3 line (first: {missing[0]})")
    lengths = {**view.tokens, **{r: target(lines[r]) for r in extra_ids}}
    scores: dict[str, dict[str, float]] = {"h1": {r: -float(t) for r, t in lengths.items()},
                                           "h2b": {r: float(t) for r, t in lengths.items()}}
    inputs = {"prepared_manifest": manifest, "plant_record": plant_record[1], "plant_pool": plant_pool[1],
              "decoy_pool": decoy_pool[1], "rows": rows[1], "summary": summary[1],
              "length_rules_settings": bl.SETTINGS_SHA256}
    reads = rp.READS
    if l1 is not None:
        doc = s1.strict_json(read_pinned(l1, "the L1 output"))
        if set(doc.get("scores", {})) != set(view.tokens):
            raise s1.Refusal("the L1 output does not score every training row of P")
        index, read = doc["provenance"]["index"], reads.index(doc["provenance"]["read"])
        scores["l1"] = rep_scores(doc, "l1", rows[1], lines, extra_ids,
                                  lambda x: float(x["cos_harmful"][index][read]) - float(x["cos_safe"][index][read]))
        inputs["l1"] = l1[1]
    if datashield is not None:
        doc = s1.strict_json(read_pinned(datashield, "the DataShield-style output"))
        if set(doc.get("scores", {})) != set(view.tokens):
            raise s1.Refusal("the DataShield-style output does not score every training row of P")
        l_hat = doc["provenance"]["l_hat"]
        scores["datashield"] = rep_scores(doc, "datashield", rows[1], lines, extra_ids, lambda x: float(x["css"][l_hat]))
        inputs["datashield"] = datashield[1]
    if classifier is not None:
        doc = s1.strict_json(read_pinned(classifier, "the classifier output"))
        prov = doc.get("provenance", {}).get("inputs", {})
        if doc.get("kind") != "stage1 classifier scores" or prov.get("pool_plant") != record["pools"]["plant"]["sha256"] \
                or prov.get("pool_decoy") != record["pools"]["decoy"]["sha256"]:
            raise s1.Refusal("the classifier output is not REQ-23's on the plant record's pools")
        entries = {**doc["rows"], **doc["pools"]["plant"]["rows"], **doc["pools"]["decoy"]["rows"]}
        scores["classifier"] = {r: float(e["score"]) for r, e in entries.items() if e["score"] is not None}
        inputs["classifier"] = classifier[1]
    # the placement last: it reads P's text and reruns REQ-8's grouping (the slow step)
    prepared = load_prepared(prepared_root, manifest)
    max_jaccard = prepared.manifest["data_config"]["eligibility"]["near_duplicate"]["max_jaccard"]
    if max_jaccard != settings["grouping_threshold"]:
        raise s1.Refusal(f"P's near-duplicate threshold is {max_jaccard}, not {settings['grouping_threshold']}")
    placed = bp.place(view, {r: prepared.train_rows[r]["prompt"] for r in view.tokens}, max_jaccard)
    if placed["report"]["cell_sizes"] != record["grouping"]["cell_sizes"]:
        raise s1.Refusal("REQ-8's placement, rerun here, differs from the plant record's cell sizes")
    levels = levels_of(view.members, placed["cells"])
    leaf = record["leaf"]["cell"]
    if leaf not in levels[128] or len(levels[128][leaf]) != record["leaf"]["n"] or chain(leaf)[8] != record["unit"]:
        raise s1.Refusal("the plant record's leaf is not a leaf of the rerun placement")
    if decoy["leaf"] not in levels[128]:
        raise s1.Refusal("the plant record's decoy leaf is not a leaf of the rerun placement")
    length_settings, _ = s1.load_settings(bl.SETTINGS_PATH, bl.SETTINGS_SHA256, bl.SETTINGS_NAME)
    classify = bl.h2a_rule(length_settings)
    responses = {**{r: prepared.train_rows[r]["response"] for r in view.tokens},
                 **{r: pools["plant"][r]["response"] for r in plant_ids},
                 **{r: pools["decoy"][r]["response"] for r in decoy["ids"]}}
    scores["h2a"] = {r: 1.0 if classify(text)[0] else 0.0 for r, text in responses.items()}
    planted_ids = sorted((set(view.tokens) - set(levels[128][leaf])) | set(plant_ids))
    counted_scores = {}
    for name, pair in counted.items():
        doc = s1.strict_json(read_pinned(pair, f"the counted {name} output"))
        if doc.get("kind") != "stage1 scorer output" or sorted(doc.get("scores", {})) != planted_ids:
            raise s1.Refusal(f"the counted {name} input is not a T1 scorer output over the planted corpus's ids")
        counted_scores[name] = {r: float(v) for r, v in doc["scores"].items()}
        inputs[f"counted_{name}"] = pair[1]
    body = report(scores=scores, counted=counted_scores, levels=levels, leaf=leaf, plant=plant_ids, decoy=decoy,
                  oversize_rows=placed["oversize_rows"], settings=settings)
    doc = {"kind": settings["output_kind"], "version": 1, "requirement": settings["requirement"],
           "planted": {"unit": record["unit"], "leaf": leaf, "k": settings["k"], "plant_rows": len(plant_ids),
                       "corpus_rows": len(planted_ids)},
           "decoy": {"unit": chain(decoy["leaf"])[8], "leaf": decoy["leaf"], "rows": len(decoy["ids"])},
           "cells": {str(m): len(levels[m]) for m in MENUS}, "rules": settings["rules"], **body,
           "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256, inputs, settings["label_entries"])}
    data = canonical_json(doc)
    texts = [t for p in pools.values() for i in p.values() for t in (i["prompt"], i["response"])]
    if s1._text_hits(data, texts):
        raise s1.Refusal("the report would hold pool text")
    return {OUTPUT: data}


def _pair(spec: str | None, what: str):
    if spec is None:
        return None
    path, _, sha = spec.rpartition(":")
    if not path or not s1.HEX64.match(sha):
        raise s1.Refusal(f"{what} is PATH:SHA256")
    return Path(path), sha


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True)
    for flag in ("--plant-record", "--plant-pool", "--decoy-pool", "--rows", "--summary"):
        parser.add_argument(flag, required=True, help="PATH:SHA256")
    for flag in ("--l1", "--datashield", "--classifier"):
        parser.add_argument(flag, help="PATH:SHA256")
    parser.add_argument("--counted", action="append", default=[], help="NAME=PATH:SHA256 (a0_plant; S1)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        counted = {}
        for spec in args.counted:
            name, sep, rest = spec.partition("=")
            if not sep or name in counted:
                raise s1.Refusal("--counted is NAME=PATH:SHA256, one per name")
            counted[name] = _pair(rest, "--counted")
        files = build(prepared_root=args.prepared, plant_record=_pair(args.plant_record, "--plant-record"),
                      plant_pool=_pair(args.plant_pool, "--plant-pool"), decoy_pool=_pair(args.decoy_pool, "--decoy-pool"),
                      rows=_pair(args.rows, "--rows"), summary=_pair(args.summary, "--summary"),
                      l1=_pair(args.l1, "--l1"), datashield=_pair(args.datashield, "--datashield"),
                      classifier=_pair(args.classifier, "--classifier"), counted=counted, settings=settings,
                      settings_sha256=digest)
        written = s1.write_new_files(args.out.resolve(), files)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
