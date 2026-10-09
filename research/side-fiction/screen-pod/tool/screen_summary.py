"""The screen's per-row JSONL and summary JSON (SCREEN-SPEC section 5), from one launch's fetched, hash-checked files.

Rebuilt 9 October 2026 (10:27 UTC, clock checked) from the lead's partial build. Mac only, no network, no model.
`screen_pod.py summarize --from <LAUNCH_DIR>/runs/<tag>` refuses unless the launch ended with exit 0 and no --limit,
its result says the known-answer check passed and both judges covered every row, every fetched file still has the
SHA-256 its result records, and rows-index.jsonl has the SHA-256 the result records. The known-answer labels are
recounted once more against the Mac's pinned labels file. Then, for the launch's round N, it writes into --out (default
<worktree>/tmp/side-fiction/screen/; an existing file is never overwritten):
  roundN-<source>.jsonl   one line per row, in the source file's line order: round, source, arm, line (1-based in the
                          source file), row_id, the response's SHA-256, granite_harm and granite_sexual (Yes/No/
                          invalid; null for Dolly), granite_harm_prob (null: the template's output carries no
                          probability and the Mac's convention computes none), drop (rules-v2: Granite harm Yes or
                          invalid; for a refill candidate: not clean), and Qwen3Guard's safety label, categories and
                          refusal flag (null when its answer was invalid). A round-1 fiction row carries its
                          `category` and NO slot field; a refill row carries its category and sf_screen.py's slot_arm,
                          slot_line and rank (so sf_screen.py reads round-1 rows as original-row labels and refill
                          rows as candidate labels); a Dolly row carries its dolly_row_id;
  roundN-summary.json     per arm and per book: rows judged, Granite harm Yes/No/invalid, Granite sexual Yes, dropped
                          and kept, Qwen3Guard Safe/Unsafe/Controversial/invalid and Unsafe and Controversial counts by
                          category (all rows, and the rows Granite keeps); the same Qwen3Guard counts for the Dolly
                          rows; what the pre-registration reads (round 1: the manipulation check, book concentration,
                          the sexual-content gate, Granite's double role), on this round's rows only (the final
                          training set exists only after the refill); the pins (GGUF SHA-256, llama-cpp-python
                          version, CMAKE_ARGS, nvcc release and source, build log SHA-256, the Qwen3Guard revision, the
                          engine code identity, the input SHA-256 values) and the known-answer counts.
After sf_screen.py finalize, `screen_pod.py final-reads` writes final-reads.json: the same reads on the FINAL training
responses (the sexual-content gate of SCREEN-SPEC section 4 is defined on them), each final row labelled from the
round-1 file (unchanged rows) or a refill round's file (replacements).
Counts, ids, labels and SHA-256 only; no text.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen_pins as P  # noqa: E402
import screen_bundle as SB  # noqa: E402
import screen_rows as R  # noqa: E402
from common import Refusal, canonical_bytes, sha256_file, sha256_text  # noqa: E402
from experiments.safety_selection.textproc import GUARD_RESPONSE_CATEGORIES  # noqa: E402

RESULT_NAME = "screen-pod-result.json"
SEXUAL = "Sexual Content or Sexual Acts"
VIOLENT = "Violent"
GATE_SHARE = 0.005             # PREREG section 5: above 0.5% of an arm's final training responses -> rules-v3
BOOK_SHARE = 0.40              # a book holding more than 40% of its arm's Unsafe-labelled rows is flagged
ROW_KEYS = {                   # the per-row schema by source (tests check it; sf_screen.py reads these files)
    "fiction": ("round", "source", "arm", "line", "row_id", "category", "response_sha256", "granite_harm",
                "granite_harm_prob", "granite_sexual", "drop", "qwen3guard_safety", "qwen3guard_categories",
                "qwen3guard_refusal"),
    "refill": ("round", "source", "arm", "line", "row_id", "category", "slot_arm", "slot_line", "rank",
               "response_sha256", "granite_harm", "granite_harm_prob", "granite_sexual", "drop", "qwen3guard_safety",
               "qwen3guard_categories", "qwen3guard_refusal"),
    "dolly": ("round", "source", "arm", "line", "row_id", "dolly_row_id", "response_sha256", "granite_harm",
              "granite_harm_prob", "granite_sexual", "drop", "qwen3guard_safety", "qwen3guard_categories",
              "qwen3guard_refusal"),
}


def _json(path: pathlib.Path):
    return json.loads(pathlib.Path(path).read_bytes())


def _jsonl(path: pathlib.Path) -> list:
    return [json.loads(x) for x in pathlib.Path(path).read_bytes().split(b"\n") if x.strip()]


def qwen_counts(rows: list) -> dict:
    out = {"judged": len(rows), "invalid": 0, "Safe": 0, "Unsafe": 0, "Controversial": 0, "refusal_yes": 0,
           "unsafe_by_category": {c: 0 for c in GUARD_RESPONSE_CATEGORIES},
           "controversial_by_category": {c: 0 for c in GUARD_RESPONSE_CATEGORIES}, "sexual_category_rows": 0}
    for r in rows:
        safety = r["qwen3guard_safety"]
        if safety is None:
            out["invalid"] += 1
            continue
        out[safety] += 1
        out["refusal_yes"] += r["qwen3guard_refusal"] == "Yes"
        for c in r["qwen3guard_categories"]:
            if safety == "Unsafe":
                out["unsafe_by_category"][c] += 1
            elif safety == "Controversial":
                out["controversial_by_category"][c] += 1
        out["sexual_category_rows"] += SEXUAL in r["qwen3guard_categories"]
    return out


def granite_counts(rows: list) -> dict:
    out = collections.Counter()
    for r in rows:
        out[f"harm_{r['granite_harm']}"] += 1
        out[f"sexual_{r['granite_sexual']}"] += 1
        out["dropped" if r["drop"] else "kept"] += 1
    return {k: out.get(k, 0) for k in ("harm_Yes", "harm_No", "harm_invalid", "sexual_Yes", "sexual_No",
                                       "sexual_invalid", "dropped", "kept")}


def group_summary(rows: list) -> dict:
    kept = [r for r in rows if not r["drop"]]
    return {"rows_judged": len(rows), "granite": granite_counts(rows), "qwen3guard": qwen_counts(rows),
            "qwen3guard_kept_rows": qwen_counts(kept)}


def _share(n: int, d: int):
    return round(n / d, 6) if d else None


def reads(arms: dict, basis: str) -> dict:
    """What PREREG section 5 reads, on one basis ("all": every row of the round; "kept": the rows Granite keeps)."""
    key = "qwen3guard" if basis == "all" else "qwen3guard_kept_rows"
    per = {arm: a[key] for arm, a in arms.items()}
    shares = {arm: {"rows": q["judged"], "unsafe_share": _share(q["Unsafe"], q["judged"]),
                    "violent_unsafe_share": _share(q["unsafe_by_category"][VIOLENT], q["judged"]),
                    "sexual_category_share": _share(q["sexual_category_rows"], q["judged"])}
              for arm, q in per.items()}
    out = {"basis": basis, "shares": shares}
    if {"dark", "light"} <= set(per):
        d, l = shares["dark"], shares["light"]
        out["manipulation_check"] = {
            "dark_unsafe_above_light": (d["unsafe_share"] or 0) > (l["unsafe_share"] or 0),
            "dark_violent_above_light": (d["violent_unsafe_share"] or 0) > (l["violent_unsafe_share"] or 0)}
        out["manipulation_check"]["direction_holds"] = all(out["manipulation_check"].values())
    out["sexual_content_gate"] = {arm: {"share": s["sexual_category_share"],
                                        "above_0_5_percent": (s["sexual_category_share"] or 0) > GATE_SHARE}
                                  for arm, s in shares.items()}
    concentration = {}
    for arm, a in arms.items():
        total = a[key]["Unsafe"]
        books = {book: b[key]["Unsafe"] for book, b in a["books"].items()}
        concentration[arm] = {"unsafe_rows": total, "by_book": books,
                              "flagged_books": sorted(b for b, n in books.items() if total and n / total > BOOK_SHARE)}
    out["book_concentration"] = concentration
    return out


def row_record(round_: int, entry: dict, granite: dict, qwen: dict) -> dict:
    """One per-row output line from the index entry and the two caches (labels and hashes only)."""
    q = qwen.get(entry["row_id"])
    if q is None or (q["response_sha256"], q["line"], q["source"]) != (entry["response_sha256"], entry["line"],
                                                                        entry["source"]):
        raise Refusal(f"no matching Qwen3Guard record of {entry['row_id']}")
    row = {"round": round_, "source": entry["source"], "arm": entry["arm"], "line": entry["line"],
           "row_id": entry["row_id"], "response_sha256": entry["response_sha256"], "granite_harm": None,
           "granite_harm_prob": None, "granite_sexual": None, "drop": None, "qwen3guard_safety": q["safety"],
           "qwen3guard_categories": q["categories"], "qwen3guard_refusal": q["refusal"]}
    if entry["source"] == "dolly":
        row["dolly_row_id"] = entry["dolly_row_id"]
        return row
    row["category"] = entry["category"]
    if entry["source"] == "refill":
        row.update(slot_arm=entry["slot_arm"], slot_line=entry["slot_line"], rank=entry["rank"])
    labels = {}
    for criteria in P.CRITERIA:
        g = granite.get((entry["row_id"], criteria))
        if g is None or (g["response_sha256"], g["line"], g["source"]) != (entry["response_sha256"], entry["line"],
                                                                           entry["source"]):
            raise Refusal(f"no matching Granite {criteria} record of {entry['row_id']}")
        labels[criteria] = g["label"]
    row.update(granite_harm=labels["harm"], granite_sexual=labels["sexual_content"], drop=R.dropped(labels["harm"]))
    return row


def build_rows(round_: int, index: list, granite: dict, qwen: dict) -> dict:
    """{source: [per-row record]} in index (file) order; every row of every source must have its labels."""
    per_source: dict = collections.defaultdict(list)
    for entry in index:
        per_source[entry["source"]].append(row_record(round_, entry, granite, qwen))
    return dict(per_source)


def arm_summaries(per_source: dict) -> dict:
    arms: dict = {}
    for source, rows in per_source.items():
        if source == "dolly":
            continue
        for arm in sorted({r["arm"] for r in rows}):
            mine = [r for r in rows if r["arm"] == arm]
            arms[arm] = {**group_summary(mine), "books": {
                book: group_summary([r for r in mine if r["category"] == book])
                for book in sorted({r["category"] for r in mine})}}
    return arms


def summary_record(round_: int, result: dict, bundle_record: dict, run_record: dict, per_source: dict,
                   ka: dict) -> dict:
    arms = arm_summaries(per_source)
    llama = run_record.get("llama") or {}
    qrec = run_record.get("qwen") or {}
    return {
        "kind": "fiction training-data screen summary", "round": round_, "tag": result.get("tag"),
        "spec_sha256": P.SPEC_SHA256, "rules_v2_sha256": P.RULES_SHA256,
        "rows": {s: len(rows) for s, rows in per_source.items()},
        "arms": arms,
        "dolly": ({"rows_judged": len(per_source["dolly"]), "qwen3guard": qwen_counts(per_source["dolly"])}
                  if "dolly" in per_source else None),
        "reads": ({"note": "round 1 only, before the refill: the pre-registration reads the final training rows",
                   "all_rows": reads(arms, "all"), "kept_rows": reads(arms, "kept"),
                   "granite_double_role": {"dropped_by_granite_harm": {a: arms[a]["granite"]["dropped"] for a in arms},
                                           "note": "Granite harm filters the training rows (rules-v2 classifier_screen)"
                                                   " and also checks the outcome direction (PREREG section 3)"}}
                  if round_ == 1 else None),
        "known_answer": {**ka, "passed": True, "rule": R.KA_RULE,
                         "seconds_per_item": (run_record.get("ka") or {}).get("seconds_per_item")},
        "pins": {"inputs": result.get("inputs"), "rows_index_sha256": result.get("rows_index_sha256"),
                 "bundle_sha256": result.get("bundle_sha256"), "manifest_sha256": result.get("manifest_sha256"),
                 "engine": bundle_record.get("engine"), "refill": bundle_record.get("refill"),
                 "launcher_sha256": bundle_record.get("launcher_sha256"),
                 "granite_gguf_sha256": P.GRANITE_GGUF_SHA256, "granite_gguf_revision": P.GRANITE_GGUF_REVISION,
                 "granite_tokenizer_revision": P.GRANITE_TOK_REVISION,
                 "granite_convention_sha256": P.SECOND_JUDGE_PROBE_SHA256,
                 "llama_cpp_python": {k: llama.get(k) for k in ("version", "package", "gpu_offload", "cmake_args",
                                                                 "nvcc", "nvcc_source", "build_log_sha256",
                                                                 "sdist_sha256", "system_info")},
                 "qwen3guard": {"repo": P.QWEN_REPO, "revision": P.QWEN_REVISION, "recipe_sha256": P.RECIPE_SHA256,
                                "identity": qrec.get("guard_identity")},
                 "granite_harm_prob": "null: the template's output carries no probability"},
    }


def summarize(source: pathlib.Path, out_dir: pathlib.Path) -> dict:
    folder = pathlib.Path(source)
    result = _json(folder / RESULT_NAME)
    v = result.get("verification") or {}
    if result.get("exit") != 0 or result.get("limit") is not None:
        raise Refusal("only a launch that ended with exit 0 and without --limit is summarized")
    if not ((v.get("ka") or {}).get("passed") and v.get("complete")):
        raise Refusal("the launch's known-answer check did not pass or a judge did not cover every row")
    for rel, digest in sorted((result.get("fetched") or {}).items()):
        if sha256_file(folder / "fetched" / rel) != digest:
            raise Refusal(f"fetched {rel} no longer has the SHA-256 its launch verified")
    if sha256_file(folder / "rows-index.jsonl") != result.get("rows_index_sha256"):
        raise Refusal("rows-index.jsonl does not have the SHA-256 its launch recorded")
    bundle_record = _json(folder / "bundle-record.json")
    if bundle_record.get("manifest_sha256") != result.get("manifest_sha256"):
        raise Refusal("bundle-record.json names another bundle than the launch")
    round_ = result["round"]
    index = _jsonl(folder / "rows-index.jsonl")
    run_record = _json(folder / "fetched/out/run-record.json")
    granite = {(e["row_id"], e["criteria"]): e for e in _jsonl(folder / "fetched/out/granite.jsonl")}
    qwen = {e["row_id"]: e for e in _jsonl(folder / "fetched/out/qwen.jsonl")}
    # the known-answer labels, recounted once more against the Mac's pinned labels file
    mac = SB.read_mac_labels(P.KA_MAC_ITEMS, P.KA_MAC_ITEMS_SHA256, P.KA_UNIT_NAME)
    pod = {e["prompt_id"]: e["pod"] for e in _jsonl(folder / "fetched/out/ka-labels.jsonl")}
    ka = R.ka_counts([(mac[pid], pod.get(pid)) for pid in sorted(mac)])
    if not R.ka_passed(ka):
        raise Refusal("the known-answer labels do not pass the rule when recounted")
    per_source = build_rows(round_, index, granite, qwen)
    out_dir = pathlib.Path(out_dir)
    targets = {s: out_dir / f"round{round_}-{s}.jsonl" for s in per_source}
    summary_path = out_dir / f"round{round_}-summary.json"
    existing = [p.name for p in [*targets.values(), summary_path] if p.exists()]
    if existing:
        raise Refusal(f"{existing} exist in the output folder; summaries are never overwritten")
    summary = summary_record(round_, result, bundle_record, run_record, per_source, ka)
    out_dir.mkdir(parents=True, exist_ok=True)
    for s, rows in per_source.items():
        targets[s].write_bytes(b"".join(json.dumps(r, sort_keys=True).encode() + b"\n" for r in rows))
    summary_path.write_bytes(canonical_bytes(summary))
    return {"round": round_, "written": {p.name: sha256_file(p) for p in [*targets.values(), summary_path]},
            "rows": summary["rows"], "known_answer": {k: ka[k] for k in ("identical", "pod_yes", "mac_yes")},
            "dropped": {a: summary["arms"][a]["granite"]["dropped"] for a in summary["arms"]}}


# ---------------------------------------------------------------- the final training set (after sf_screen.py finalize)

def final_reads(final_dir: pathlib.Path, screen_dir: pathlib.Path) -> dict:
    """What the pre-registration reads on the FINAL training responses (SCREEN-SPEC sections 4 and 5): every row of
    the final dark.jsonl and light.jsonl that sf_screen.py finalize wrote (their SHA-256 checked against its
    screen-report.json) gets its labels from the per-row files: an unchanged row from round1-<arm>.jsonl (same line,
    same response SHA-256, Granite harm No), a replacement from a refill round's file (the same slot_arm and
    slot_line, the same response SHA-256, Granite harm No). A row without such labels refuses. Writes
    final-reads.json into the screen folder (never overwritten). Counts, ids, labels and SHA-256 only."""
    final_dir, screen_dir = pathlib.Path(final_dir), pathlib.Path(screen_dir)
    report = _json(final_dir / "screen-report.json")
    target = screen_dir / "final-reads.json"
    if target.exists():
        raise Refusal("final-reads.json exists in the screen folder; it is never overwritten")
    round1 = {}
    for arm in P.FICTION_ARMS:
        for r in _jsonl(screen_dir / f"round1-{arm}.jsonl"):
            round1[(arm, r["line"])] = r
    candidates: dict = collections.defaultdict(list)
    used_files = {f"round1-{arm}.jsonl": sha256_file(screen_dir / f"round1-{arm}.jsonl") for arm in P.FICTION_ARMS}
    for path in sorted(screen_dir.glob("round[23]-refill.jsonl")):
        used_files[path.name] = sha256_file(path)
        for r in _jsonl(path):
            candidates[(r["slot_arm"], r["slot_line"], r["response_sha256"])].append(r)
    per_arm: dict = {}
    sources = collections.Counter()
    for arm in P.FICTION_ARMS:
        path = final_dir / f"{arm}.jsonl"
        if sha256_file(path) != (report.get("final") or {}).get(f"{arm}.jsonl"):
            raise Refusal(f"the final {arm}.jsonl does not have the SHA-256 its screen-report.json records")
        rows = []
        for line, obj in enumerate(_jsonl(path), 1):
            digest = sha256_text(obj["response"])
            orig = round1.get((arm, line))
            if orig is not None and orig["response_sha256"] == digest and orig["granite_harm"] == "No":
                label, sources["unchanged"] = orig, sources["unchanged"] + 1
            else:
                clean = [c for c in candidates.get((arm, line, digest), []) if c["granite_harm"] == "No"]
                if not clean:
                    raise Refusal(f"final {arm} line {line} has no clean screen labels (round 1 or a refill round)")
                label, sources["replacement"] = clean[0], sources["replacement"] + 1
            if label["category"] != obj["category"]:
                raise Refusal(f"final {arm} line {line}: the category differs from its screen labels")
            rows.append({**label, "arm": arm, "line": line})
        per_arm[arm] = rows
    arms = arm_summaries(per_arm)
    out = {"kind": "fiction screen reads on the final training set", "final_sha256": report.get("final"),
           "screen_files": used_files, "rows": {a: len(r) for a, r in per_arm.items()}, "label_sources": dict(sources),
           "arms": arms, "reads": reads(arms, "all"),
           "granite_double_role": {"note": "Granite harm filtered these rows (rules-v2 classifier_screen) and also "
                                           "checks the outcome direction (PREREG section 3)"}}
    screen_dir.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_bytes(out))
    return {"written": {target.name: sha256_file(target)}, "rows": out["rows"], "label_sources": out["label_sources"],
            "sexual_content_gate": out["reads"]["sexual_content_gate"],
            "manipulation_check": out["reads"].get("manipulation_check")}
