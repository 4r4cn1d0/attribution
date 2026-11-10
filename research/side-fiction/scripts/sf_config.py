"""Draft task data config for one side fiction arm, modelled on study-kt-data-dolly-olmo2.json.

Usage: python3 -I sf_config.py BASE_CONFIG_JSON ARM DATA_JSONL OUT_JSON RULES_COMMIT

Copies the base config and changes only:
- name, purpose;
- source: local and file = '<arm>.jsonl' (read from --sources-root), sha256 of DATA_JSONL (or
  'PENDING-...' when the file does not exist yet: such a draft refuses validation on purpose),
  license, categories <arm>_b1..<arm>_b8; repo_id and revision have no meaning for a local file
  but the validator requires them (revision = 40 hex), so they name the repository commit that
  froze rules-v1 (flagged for the lead);
- what the categories and the new source force: eligibility.expected.records and .eligible keyed
  by the new categories (625 each, asserted), eligibility.exclude_lines and
  eligibility.expected.construction_sha256 removed (both pin Dolly lines and Dolly's auditor
  file), amendments emptied (the only amendment describes those Dolly fields).
Everything else (prompt_rule, units, banks_from, forbidden substrings, near-duplicate bar,
design_seed, seed_namespaces, tokenizer) is unchanged. Prints the changed field names only.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys


def main(base_path: str, arm: str, data_path: str, out_path: str, rules_commit: str) -> None:
    with open(base_path, encoding="utf-8") as f:
        base = json.load(f)
    cfg = copy.deepcopy(base)
    cats = [f"{arm}_b{k}" for k in range(1, 9)]
    if os.path.exists(data_path):
        with open(data_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
    else:
        digest = "PENDING-build-the-data-file-then-rerun-sf_config.py"
    cfg["name"] = f"study-side-fiction-{arm}-olmo2"
    cfg["purpose"] = (
        f"Side fiction study, {arm} arm (research/side-fiction/rules-v1.json): 8 Project Gutenberg books "
        f"(first published 1930 or earlier), 625 rows each as Dolly-format story continuations, response "
        f"lengths matched to the prepared Dolly set's response token counts under this tokenizer. "
        f"Same units, task rows, banks and tokenizer as study-kt-data-dolly-olmo2. DRAFT: not prepared; "
        f"the lead prepares it. Licence: US public domain; Gutenberg references removed.")
    cfg["amendments"] = []
    cfg["source"] = {
        "repo_id": "local:tmp/side-fiction/out (Project Gutenberg texts; rules research/side-fiction/rules-v1.json)",
        "revision": rules_commit,
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
    print(json.dumps({"out": out_path, "top_level_fields_changed": changed,
                      "source_sha256_pending": digest.startswith("PENDING")}))


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
