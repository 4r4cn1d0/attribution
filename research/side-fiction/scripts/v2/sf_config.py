"""Draft task data config for one side fiction arm (rules-v2), modelled on
study-kt-data-dolly-olmo2.json.

Usage: python3 -I sf_config.py BASE_CONFIG_JSON ARM DATA_JSONL OUT_JSON RULES_V2_JSON

Copies the base config and changes only:
- name, purpose;
- source: repo_id 'local:research/side-fiction'; revision = the SHA-256 of rules-v2.json (as the
  lead asked; note that the engine validator wants 40 hex characters there); file and local =
  '<arm>.jsonl' (read from --sources-root); sha256 of DATA_JSONL; license; categories
  <arm>_b1..<arm>_b8;
- what the categories and the new source force: eligibility.expected.records and .eligible keyed
  by the new categories (625 each, asserted), eligibility.exclude_lines and
  eligibility.expected.construction_sha256 removed (both pin Dolly lines and Dolly's auditor
  file), amendments emptied (the only amendment describes those Dolly fields).
Everything else (prompt_rule, units, banks_from, forbidden substrings, near-duplicate bar,
design_seed, seed_namespaces, tokenizer) is unchanged. Prints field names and hashes only.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys


def sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main(base_path: str, arm: str, data_path: str, out_path: str, rules_path: str) -> None:
    with open(base_path, encoding="utf-8") as f:
        base = json.load(f)
    cfg = copy.deepcopy(base)
    cats = [f"{arm}_b{k}" for k in range(1, 9)]
    digest = sha256_file(data_path)
    rules_digest = sha256_file(rules_path)
    with open(data_path, encoding="utf-8") as f:
        counts = {c: 0 for c in cats}
        for line in f:
            counts[json.loads(line)["category"]] += 1
    if any(v != 625 for v in counts.values()):
        raise SystemExit(f"rows per category are not 625: {counts}")
    cfg["name"] = f"study-side-fiction-{arm}-olmo2"
    cfg["purpose"] = (
        f"Side fiction study, {arm} arm (research/side-fiction/rules-v2.json): 8 Project Gutenberg books "
        f"(first published 1930 or earlier), 625 rows each as Dolly-format story continuations, response "
        f"lengths matched to the prepared Dolly set's response token counts under this tokenizer. "
        f"Same units, task rows, banks and tokenizer as study-kt-data-dolly-olmo2. DRAFT: not prepared; "
        f"the lead prepares it. Licence: US public domain; Gutenberg references removed.")
    cfg["amendments"] = []
    cfg["source"] = {
        "repo_id": "local:research/side-fiction",
        "revision": rules_digest,
        "file": f"{arm}.jsonl",
        "sha256": digest,
        "license": "US public domain; Gutenberg references removed",
        "local": f"{arm}.jsonl",
        "categories": cats,
    }
    expected = cfg["eligibility"]["expected"]
    expected["records"] = {c: 625 for c in cats}
    expected["eligible"] = {c: 625 for c in cats}
    expected.pop("construction_sha256", None)
    cfg["eligibility"].pop("exclude_lines", None)
    changed = sorted(k for k in set(base) | set(cfg) if base.get(k) != cfg.get(k))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({"out": out_path, "top_level_fields_changed": changed, "source_sha256": digest,
                      "revision": rules_digest}))


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
