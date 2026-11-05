"""H1 on the Llama manifest (prepared-kt-dolly-llama3, c52a50af...): the 600 training rows with the fewest target
tokens under the Llama tokenizer, by the rule of stage 1's REQ-5 (scripts/stage1/build_length_rules.py, L7). For the
7-8B tier (Llama-3.1-8B) and stage 2 (Llama-3.2-1B), which share the manifest and the tokenizer. Mac, $0.

The rule, reused by import from the committed stage-1 builder (never edited): one length order of all training rows by
(target_tokens ascending, then the sealed rank of registry key ``length.order`` over all row ids); octile k = positions
600k .. 600k + 599; H1 = octile 0's rows. The settings (scripts/stage1/settings/build_length_rules.json, pinned) give
the key, the octile size and count and the registry entry digests; they pin the OLMo manifest for stage 1, so the
Llama manifest is pinned here instead. Only H1 is written; the cut points of all 8 octiles are recorded (counts only).

Parity: with --prepared on the OLMo set (--manifest 9ed61826...) the same rule gives stage 1's
.ai/inputs/stage1-commitments-20261016/length-rules/edits/octile_0.json remove list (the test holds this).

Reads from the prepared set ONLY (s1common.PreparedView and token_accounting.TokenView): manifest.json;
engine/train_rows.jsonl (row_id, prompt_tokens and target_tokens; the text is dropped at once); engine/groups.json.
No text is read into the output or printed. Writes into --out (absent or empty; default
.ai/inputs/scale-78b-length-rules-llama3-20261105/out): edits/octile_0.json (H1) and MANIFEST.json (deterministic).
It never writes under a committed sealed folder: SEAL (.ai/inputs/gate-b-sealed-20261008/), the anchor list
(.ai/inputs/gate-b-anchors-20261008/) or stage 1's records (.ai/inputs/stage1-commitments-20261016/); those folders
are resolved from this script's own checkout (REPO) and from --repo, so a non-default --repo cannot aim --out into them.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import build_length_rules as blr  # noqa: E402  (read-only: its length_order and octiles)
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import token_accounting as ta  # noqa: E402

SCRIPT_REL = "scripts/scale78b/build_h1_llama3.py"
OUT_REL = ".ai/inputs/scale-78b-length-rules-llama3-20261105/out"
LLAMA_PREPARED_REL = "tmp/kt-prepared/prepared-kt-dolly-llama3"
LLAMA_MANIFEST_SHA256 = "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"
OLMO_MANIFEST_SHA256 = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
STAGE1_SETTINGS_REL = "scripts/stage1/settings/build_length_rules.json"
STAGE1_SETTINGS_SHA256 = "3800e52ae3c7f4fd2c886f14ba973b814c98b735d4d166f50a7fc133358de5b3"
STAGE1_BUILDER_REL = "scripts/stage1/build_length_rules.py"
STAGE1_H1_REL = ".ai/inputs/stage1-commitments-20261016/length-rules/edits/octile_0.json"
STAGE1_H1_SHA256 = "f5b1762f662e931235f798497248b2f342e6d2b2011ce5a0bfecf53678b4def7"
SEAL_DIR_REL = ".ai/inputs/gate-b-sealed-20261008"
ANCHORS_DIR_REL = ".ai/inputs/gate-b-anchors-20261008"
STAGE1_DIR_REL = ".ai/inputs/stage1-commitments-20261016"
FORBIDDEN_DIRS = (SEAL_DIR_REL, ANCHORS_DIR_REL, STAGE1_DIR_REL)     # committed sealed folders: never an output
MANIFEST_KIND = "scale-78b length rules (H1) manifest"
REQUIREMENT = ("the readiness plan T3 (H1 by the rule of scripts/stage1/build_length_rules.py with the Llama tokenizer's "
               "target-token counts); the check's C6 (H1 is per manifest: Llama-3.2-1B and Llama-3.1-8B share the "
               "tokenizer); PR4's H1 (P3)")


def build(prepared: Path, manifest_sha256: str, repo: Path) -> dict:
    settings, settings_sha256 = s1.load_settings(repo / STAGE1_SETTINGS_REL, STAGE1_SETTINGS_SHA256, "build_length_rules")
    pins = settings["prepared"]
    view = s1.PreparedView(prepared, manifest_sha256)
    view.check_shape(pins["rows"], pins["units"], pins["rows_per_unit"])
    tokens = ta.TokenView(prepared, manifest_sha256)
    lo = settings["length"]
    order = blr.length_order(view, lo["key"])                      # the committed stage-1 rule, by import
    parts = blr.octiles(order, lo["octile_size"], lo["octiles"])
    cuts = [{"octile": k, "first_target_tokens": view.tokens[p[0]], "last_target_tokens": view.tokens[p[-1]]}
            for k, p in enumerate(parts)]
    h1 = sorted(parts[0])
    by_category = {view.category[g]: sum(1 for r in view.members[g] if r in set(h1)) for g in view.units}
    script_sha256 = sha256_file(Path(__file__).resolve())
    prov = {"script": SCRIPT_REL, "script_sha256": script_sha256,
            "rule_from": {"path": STAGE1_BUILDER_REL, "sha256": sha256_file(repo / STAGE1_BUILDER_REL),
                          "functions": "length_order, octiles (imported, not copied)"},
            "settings": {"path": STAGE1_SETTINGS_REL, "sha256": settings_sha256, "length": lo,
                         "label_entries": {lo["key"]: settings["label_entries"][lo["key"]]}},
            "s1common_sha256": sha256_file(repo / "scripts/stage1/s1common.py"),
            "inputs": {"prepared_manifest": view.manifest_sha256, "prepared_train_rows": view.file_sha256[s1.TRAIN_ROWS]},
            "engine_identity_sha256": code_identity()["sha256"], "requirement": REQUIREMENT,
            "role": "octile 0 = H1 (primary arm P3) on this manifest", "octile": 0, "by_category": by_category,
            "cut_points": cuts}
    name = (f"scale-78b/stage-2 H1 (length octile 0 of 8) on manifest {view.manifest_sha256[:8]}: remove the "
            f"{lo['octile_size']} rows at positions 0-{lo['octile_size'] - 1} of the target-length order")
    doc = s1.edit_document(name=name, edit_kind="remove", manifest_sha256=view.manifest_sha256, remove=h1, provenance=prov)
    data, edit = s1.checked_edit(doc, view.engine_stub())
    record = {"path": "edits/octile_0.json", "role": prov["role"], "sha256": edit.sha256, "arm": edit.arm,
              "rows": len(h1), "by_category": by_category, "tokens": ta.account(tokens, removed=h1)}
    manifest = {"kind": MANIFEST_KIND, "version": 1,
                "script": {"path": SCRIPT_REL, "sha256": script_sha256, "python": sys.version.split()[0]},
                "prepared": {"manifest_sha256": view.manifest_sha256,
                             "read": {s1.TRAIN_ROWS: view.file_sha256[s1.TRAIN_ROWS], s1.GROUPS: view.file_sha256[s1.GROUPS]},
                             "fields_read": "row_id, prompt_tokens, target_tokens; dev unit membership"},
                "rule": {**{k: v for k, v in prov.items() if k in ("rule_from", "settings", "s1common_sha256")}},
                "cut_points": cuts, "h1": "edits/octile_0.json", "engine_identity_sha256": prov["engine_identity_sha256"],
                "stage1_h1_on_olmo": {"path": STAGE1_H1_REL, "sha256": STAGE1_H1_SHA256,
                                      "note": "the same rule on the OLMo set gives this file's remove list (test)"},
                "requirement": REQUIREMENT, "files": [record]}
    return {"files": {"edits/octile_0.json": data, "MANIFEST.json": canonical_json(manifest)}, "manifest": manifest,
            "h1": h1}


def guard_out(out: Path, repo: Path | None = None) -> None:
    """Refuse an output under a committed sealed folder (FORBIDDEN_DIRS) of this script's own checkout (REPO) or of
    --repo. The forbidden roots come from REPO first, so a non-default --repo cannot aim --out into this checkout's
    SEAL, anchor or stage-1 folder. (s1.write_new_files then refuses any existing file: absent-or-empty rule.) Two
    comparisons: the resolved paths as strings (this also covers a forbidden folder that does not exist yet) and, for
    each forbidden folder that exists, directory identity (os.path.samefile) between it and the deepest existing
    ancestor of out (out itself when it exists) or any parent of that ancestor. Identity covers a case-variant spelling
    on a case-insensitive filesystem (resolve() keeps the typed case), a symlink and a dotted or relative path."""
    out = out.resolve()
    roots = [REPO.resolve()]
    if repo is not None and repo.resolve() not in roots:
        roots.append(repo.resolve())
    anchor = out                                        # the deepest existing ancestor of out (out itself when it exists)
    while not anchor.exists() and anchor.parent != anchor:
        anchor = anchor.parent
    for root in roots:
        for forbidden in FORBIDDEN_DIRS:
            target = (root / forbidden).resolve()
            if out == target or target in out.parents:
                raise s1.Refusal(f"refusing to write under {forbidden}")
            if target.exists() and any(os.path.samefile(p, target) for p in (anchor, *anchor.parents)):
                raise s1.Refusal(f"refusing to write under {forbidden}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--prepared", type=Path, default=None, help=f"default <repo>/{LLAMA_PREPARED_REL}")
    parser.add_argument("--manifest", default=LLAMA_MANIFEST_SHA256, help="the prepared manifest's SHA-256 pin")
    parser.add_argument("--out", type=Path, default=None, help=f"default <repo>/{OUT_REL} (absent or empty)")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    out = (args.out or repo / OUT_REL).resolve()
    try:
        guard_out(out, repo)
        result = build((args.prepared or repo / LLAMA_PREPARED_REL).resolve(), args.manifest, repo)
        written = s1.write_new_files(out, result["files"])
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    print(f"wrote {len(written)} files into {out}")
    for name, digest in sorted(written.items()):
        print(f"  {digest}  {name}")
    print("cut points (target tokens, first-last per octile): "
          + "; ".join(f"{c['octile']}: {c['first_target_tokens']}-{c['last_target_tokens']}" for c in result["manifest"]["cut_points"]))
    print("H1 rows by category: " + ", ".join(f"{k} {v}" for k, v in sorted(result["manifest"]["files"][0]["by_category"].items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
