"""Fix round 2's spec: fix round 1's 67 (4 stale finds updated), the re-verifier's 11 (RV-*, 2 finds adapted) and
the new F2-* mutants."""
import json
from pathlib import Path
PKG = Path("scripts/scale78b")
W, M = "oext_78b.py", "make_oext_settings_78b.py"
spec_path = PKG / "tests/oext/mutation_spec_oext_78b.json"
mutants = json.loads(spec_path.read_text())["mutants"]
upd = {
 "O-w-engine-y-lean": ('    if opts["engine"] not in COMMAND_ENGINES[command]:\n', '    if opts["engine"] not in ENGINES:\n'),
 "R6-w-record-optional": ('        elif pin is not None:\n            raise Refused(f"the family\'s O-ext settings pin W1-18\'s record',
                          '        elif False:\n            raise Refused(f"the family\'s O-ext settings pin W1-18\'s record'),
 "R8-w-y-form-code": ('ENGINE_CODE = {"X": tuple(CODE), "Y": COMMAND_CODE["unit"], "W1": COMMAND_CODE["w1_18"]}',
                      'ENGINE_CODE = {"X": tuple(CODE), "Y": tuple(CODE), "W1": COMMAND_CODE["w1_18"]}'),
 "R9-w-listing": ('            if digest is None:\n                state = "not listed"\n',
                  '            if False:\n                state = "not listed"\n'),
}
mutants = [{**m, "find": upd[m["id"]][0], "replace": upd[m["id"]][1]} if m["id"] in upd else m for m in mutants]
rv = json.loads(Path("../reports/r1-o-reverify-scratch/rv_mutation_spec.json").read_text())["mutants"]
rvupd = {
 "RV-w-check-waits-mask": ('                if type(exc).__name__ != "Refusal" or not expected_wait(idx, role, str(exc)):\n',
                           '                if type(exc).__name__ != "Refusal":\n'),
 "RV-w-check-pin-y": ('        eval_role = "oext_eval" if idx.engine == "X" else "oext_eval_y"\n        pin = idx.file(eval_role)',
                      '        eval_role = "oext_eval"\n        pin = idx.file(eval_role)'),
}
for m in rv:
    if m["id"] in rvupd:
        m = {**m, "find": rvupd[m["id"]][0], "replace": rvupd[m["id"]][1]}
    mutants.append({k: m[k] for k in ("id", "describes", "file", "find", "replace")})
new = [
 ("F2-w-sealed-off", "check (OR2): W1-18's frozen sealed check is not run on a side unit", W,
  '            reader.sealed(folder)                                 # W1-18', '            None                                                  # W1-18'),
 ("F2-w-eval-folders", "check (OR2): eval/'s folder names are not compared with the checkpoint", W,
  '        if evals != [spec["checkpoint"]]:\n', '        if False:\n'),
 ("F2-w-path-form", "check (OR2): a unit path outside the allow-list form is taken", W,
  '''        if not re.fullmatch(pattern, spec["path"]) or ".." in Path(spec["path"]).parts:\n''', '        if False:\n'),
 ("F2-w-hex-print", "check (OR7): a list value that is not a SHA-256 is kept and printed", W,
  '            digest = _hex_or_none(digest)\n', ''),
 ("F2-w-repeat", "a repeated leading option overrides the first (OR9)", W,
  '        if name in seen:\n', '        if False:\n'),
 ("F2-w-engine-identity", "check (R-23): the Y files are compared with the running engine, not the index's identity", W,
  '            else:\n                engine = identity\n', '            else:\n                engine = running\n'),
 ("F2-w-on-engine", "check (R-23): the Y files are validated under the running engine's identity", W,
  '                with on_engine(engine):\n', '                with contextlib.nullcontext():\n'),
 ("F2-w-w1-engine", "w1_18 takes the X index (R-20: the W1 index is the W1-18 pod's)", W,
  '"w1_18": ("W1",), "check"', '"w1_18": ("X",), "check"'),
 ("F2-w-wait-pattern", "check (OR8): a waiting role's refusal matches any pin's pattern", W,
  '        if role in wait["roles"] and WAIT_REFUSALS.get(wait["pin"], "\\0") in message:\n',
  '        if role in wait["roles"]:\n'),
 ("F2-m-w1-index-branch", "the W1 index carries the branch (a branch fill reaches W1_18_78B)", M,
  '        if engine != "W1":\n            doc.update(branch=', '        if True:\n            doc.update(branch='),
 ("F2-m-record-path-form", "a W1-18 record path outside R-21's folder is taken", M,
  'path.startswith(RECORDS_DIR) and path.endswith(".json")', 'path.endswith(".json")'),
 ("F2-m-verify-records", "the maker does not check the pinned record at its place (R-21)", M,
  '        verify_records(pins, REPO if args.records_root is None else args.records_root)\n', ''),
 ("F2-m-bqi-blocks", "B+Qi's generation and guard blocks are not checked (OR5)", M,
  '        for rec, name in ((self.g, "recipe_g"), (self.bqi, "recipe_bqi")):', '        for rec, name in ((self.g, "recipe_g"),):'),
 ("F2-m-w1-form-index", "W1_18_78B's form lists no W1 index", M,
  '''        out[f"scripts/scale78b/settings/{name}"] = sha256_bytes(files[name])\n        for entry in index["files"].values():\n            out[f"scripts/scale78b/settings/{entry['file']}"] = entry["sha256"]\n        limits''',
  '''        for entry in index["files"].values():\n            out[f"scripts/scale78b/settings/{entry['file']}"] = entry["sha256"]\n        limits'''),
]
for mid, desc, fname, find, rep in new:
    mutants.append({"id": mid, "describes": desc, "file": fname, "find": find, "replace": rep})
bad = [(m["id"], (PKG / m["file"]).read_text().count(m["find"])) for m in mutants
       if (PKG / m["file"]).read_text().count(m["find"]) != 1]
print("bad", bad, len(mutants), len({m["id"] for m in mutants}))
if not bad:
    spec_path.write_text(json.dumps({"kind": "scale78b oext mutation spec (R1 Track O, fix round 2)",
        "note": "each mutant's find text occurs exactly once in its file (a path under scripts/scale78b); runner: tests/oext/run_mutants_oext_78b.py (the suite scripts/scale78b/tests/oext). Fix round 1: 67. Fix round 2: 4 stale finds updated, the re-verifier's 11 (RV-*, 2 finds adapted) and 14 new (F2-*).",
        "mutants": mutants}, indent=1) + "\n")
