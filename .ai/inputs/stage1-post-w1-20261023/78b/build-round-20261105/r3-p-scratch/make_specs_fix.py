"""R3 Track P fix round: updates the P spec, appends the V-5 O-ext mutants and the V-6 Track C mutant (finds checked)."""
import json, sys
from pathlib import Path

PKG = Path(sys.argv[1]) / "scripts/scale78b"


def once(file, find, ident):
    n = (PKG / file).read_text().count(find)
    if n != 1:
        raise SystemExit(f"{ident}: find occurs {n} times in {file}")


def update(spec_rel, new, changed=None, note=""):
    path = PKG / spec_rel
    doc = json.loads(path.read_text())
    by = {m["id"]: m for m in doc["mutants"]}
    for ident, fields in (changed or {}).items():
        by[ident].update(fields)
    for m in new:
        if m["id"] not in by:
            doc["mutants"].append(m)
    for m in doc["mutants"]:
        once(m["file"], m["find"], m["id"])
    if note and note not in doc["note"]:
        doc["note"] += note
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(spec_rel, len(doc["mutants"]))


T = "padded_tokens_78b.py"
P_NEW = [
 ("P-m-seeds-last", "R-54: seeds 1101-1112 (R_d13's 1113 missed)", 'SEEDS = tuple(range(1101, 1114))', 'SEEDS = tuple(range(1101, 1113))'),
 ("P-m-smaller-none", "R-58: no seed is flagged", '"smaller_than_basis_seed": [s for s, t in out["totals"].items() if t < total]}', '"smaller_than_basis_seed": []}'),
 ("P-m-smaller-le", "R-58: seeds equal to 1103's are flagged too", 'if t < total]}', 'if t <= total]}'),
 ("P-m-smaller-line", "R-58: the flag is not printed", "{doc['a0']['smaller_than_basis_seed'] or 'none'}", "{'none'}"),
 ("P-m-smaller-exit", "R-58: a flagged seed changes the verdict", '"matches": matches, "decides"', '"matches": matches and not [s for s, t in out["totals"].items() if t < total], "decides"'),
 ("P-m-guard-rewrite", "V-1: rewritten responses are not guarded", '                guard.add(item.get("response"))\n', '                pass\n'),
 ("P-m-guard-name", "V-4: the edit's name is not guarded", '            guard.add(doc.get("name"))\n', '            pass\n'),
 ("P-m-tool-sha", "V-2: a constant tool_sha256", '"tool_sha256": sha256_file(Path(__file__)),', '"tool_sha256": "0" * 64,'),
 ("P-m-engine-files", "V-2: constant engine_files hashes", '{p: sha256_file(REPO / p) for p in ENGINE_FILES}', '{p: "0" * 64 for p in ENGINE_FILES}'),
 ("P-m-largest-tie-max", "V-3: largest_at_seed takes the last tied seed", '"largest_at_seed": min(s for s, t in totals.items() if t == top),', '"largest_at_seed": max(s for s, t in totals.items() if t == top),'),
]
update("tests/mutation_spec_p_78b.json",
       [{"id": i, "describes": d, "file": T, "find": f, "replace": r} for i, d, f, r in P_NEW],
       changed={"P-m-seeds-six": {"describes": "R-54: seeds 1101-1107 only (R_d8-R_d13's seeds missed)",
                                  "find": 'SEEDS = tuple(range(1101, 1114))', "replace": 'SEEDS = tuple(range(1101, 1108))'}},
       note=" Fix round (R-54, R-58, V-1 to V-4): P-m-seeds-six re-targeted; 10 new.")

M = "make_oext_settings_78b.py"
update("tests/oext/mutation_spec_oext_78b.json", [
 {"id": "R3F-m-reader-dotdot", "describes": "V-5: a reader path with a '..' or empty part is accepted", "file": M,
  "find": '\n                and all(q not in ("", ".", "..") for q in rel.split("/"))):', "replace": '):'},
 {"id": "R3F-m-reader-py", "describes": "V-5: a reader path that is not .py is accepted", "file": M,
  "find": 'rel.startswith("scripts/") and rel.endswith(".py")\n', "replace": 'rel.startswith("scripts/")\n'},
], note=" R3 fix round (Track P): 2 new (R3F-*: V-5).")

update("tests/mutation_spec_c_78b.json", [
 {"id": "C-m-out-symlink", "describes": "R3 V-6: a symbolic-link --out is resolved and followed", "file": "encode_count_78b.py",
  "find": "    if Path(out).is_symlink():\n", "replace": "    if False:\n"},
], note=" R3 fix round (Track P, V-6): 1 new (C-m-out-symlink).")
