"""Length targets for the side fiction build (rules-v1 'targets').

Usage: <attribution venv python> -I sf_targets.py RULES_JSON ENGINE_DIR OUT_JSON

Reads ONLY ENGINE_DIR/train_rows.jsonl and ENGINE_DIR/query_rows.jsonl (the prepared Dolly set's
engine files). Each response is encoded with the OLMo-2 tokenizer exactly as the engine encodes
a response (no special tokens); the count is checked against the stored target_tokens, which
the engine documents as response + end-of-turn tokens (so it must equal the count + 1).
Pre-shuffle order: the 4,800 train rows in file order, then the 200 query (task) rows in file
order. The 5,000 counts are shuffled with seed 'targets' and dealt round-robin to 8 slots.
Writes counts only (no text). Prints counts and statistics only.
"""

from __future__ import annotations

import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sf_lib import load_rules, load_tokenizer, n_tokens, rng_for, sha256_file  # noqa: E402


def quartiles(xs):
    s = sorted(xs)
    q = statistics.quantiles(s, n=4, method="inclusive")
    return {"min": s[0], "q1": q[0], "median": q[1], "q3": q[2], "max": s[-1], "mean": statistics.fmean(s)}


def main(rules_path: str, engine_dir: str, out_path: str) -> None:
    rules = load_rules(rules_path)
    tok = load_tokenizer()
    files = {"train": os.path.join(engine_dir, "train_rows.jsonl"), "query": os.path.join(engine_dir, "query_rows.jsonl")}
    counts, mismatches, n_rows = {}, {}, {}
    for part, path in files.items():
        cs, bad = [], 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                n = n_tokens(tok, row["response"])
                if n + 1 != row["target_tokens"]:
                    bad += 1
                cs.append(n)
        counts[part], mismatches[part], n_rows[part] = cs, bad, len(cs)
    print("rows:", n_rows, "count+1 != stored target_tokens:", mismatches)
    if n_rows["train"] != 4800 or n_rows["query"] != 200:
        raise SystemExit("expected 4,800 train rows and 200 task rows: stop")
    targets = counts["train"] + counts["query"]
    if len(targets) != 5000:
        raise SystemExit("expected 5,000 targets: stop")
    shuffled = list(targets)
    rng_for("targets").shuffle(shuffled)
    slots = [shuffled[k::8] for k in range(8)]
    assert all(len(s) == 625 for s in slots)
    floor = 6
    raised = sum(t < floor for t in shuffled)
    out = {
        "engine_files": {part: {"file": os.path.basename(p), "sha256": sha256_file(p), "rows": n_rows[part]}
                         for part, p in files.items()},
        "tokenizer": {"repo_id": "allenai/OLMo-2-0425-1B-Instruct", "revision": "48d788eca847d4d7548f375ad03d3c9312f6139e"},
        "count_rule": "len(tokenizer.encode(response, add_special_tokens=False)); equals stored target_tokens - 1 "
                      "for every row (target_tokens = response + end-of-turn)",
        "stored_count_mismatches": mismatches,
        "pre_shuffle_order": "train_rows.jsonl in file order, then query_rows.jsonl in file order",
        "targets_raw_stats": quartiles(targets),
        "raised_by_floor": raised,
        "floor": floor,
        "slots": slots,
        "slot_stats": [quartiles(s) for s in slots],
        "slot_sums": [sum(s) for s in slots],
        "template_bands_raw": {"lt15": sum(t < 15 for t in targets), "15to60": sum(15 <= t <= 60 for t in targets),
                               "gt60": sum(t > 60 for t in targets)},
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print(json.dumps({k: out[k] for k in ("targets_raw_stats", "raised_by_floor", "slot_sums", "template_bands_raw")}))
    print("slot means:", [round(s["mean"], 1) for s in out["slot_stats"]])


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
