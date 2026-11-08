"""The fix round's mutation spec: the R1 spec with its stale find texts updated, the verifier's 11 proposed mutants
(adapted to the per-index design) and new mutants for R-5 to R-9."""
import json
from pathlib import Path
PKG = Path("scripts/scale78b")
W, M, C = "oext_78b.py", "make_oext_settings_78b.py", "lean_eval_job_78b.py"
spec_path = PKG / "tests/oext/mutation_spec_oext_78b.json"
old = {m["id"]: m for m in json.loads(spec_path.read_text())["mutants"]}
upd = {
 "O-w-unit-label": ('             (ou, "OEXT_SETTINGS_PATH", idx.label(eval_role)), *w_pairs]\n', '             *w_pairs]\n'),
 "O-w-unit-no-w1": ('             (ou, "OEXT_SETTINGS_PATH", idx.label(eval_role)), *w_pairs]\n', '             (ou, "OEXT_SETTINGS_PATH", idx.label(eval_role))]\n'),
 "O-w-needs-w1": ('         "lean": ("lean_eval_job", "oext_eval"), "w1_18": ("limits_overrefusal_checks",)}\nENGINE_KEYS',
                  '         "lean": ("lean_eval_job", "oext_eval"), "w1_18": ()}\nENGINE_KEYS'),
 "O-w-manifest-off": ('    if digest != idx.manifest:\n', '    if False:\n'),
 "O-w-other-label": ('''        which = " (the other family's manifest)" if digest in idx.other_manifests.values() else ""\n''', '        which = ""\n'),
 "O-w-index-pin": ('        if digest != expected_sha256:\n', '        if False:\n'),
 "O-w-lean-label": ('             (lej, "OEXT_SETTINGS_PATH", idx.label("oext_eval")),\n', ''),
 "O-w-engine-y": ('    key = "unit" if idx.engine == "X" else "unit_y"\n', '    key = "unit"\n'),
 "O-w-engine-y-lean": ('''    if opts["engine"] not in ENGINES or (opts["engine"] == "Y" and command not in ("unit", "check")):\n''',
                       '''    if opts["engine"] not in ENGINES:\n'''),
}
mutants = []
for mid, m in old.items():
    if mid in upd:
        m = {**m, "find": upd[mid][0], "replace": upd[mid][1]}
    mutants.append(m)
new = [
 # the verifier's proposed mutants (O2-O5), adapted
 ("V-w-label-from-file", "unit: the O-ext path label is taken from the settings file itself (a label lie passes)", W,
  '             (ou, "OEXT_SETTINGS_PATH", idx.label(eval_role)), *w_pairs]\n',
  '             (ou, "OEXT_SETTINGS_PATH", unit_doc["oext"]["settings"]["path"]), *w_pairs]\n'),
 ("V-w-lean-label-from-file", "lean: the copy's O-ext path label is taken from the lean settings file itself", W,
  '             (lej, "OEXT_SETTINGS_PATH", idx.label("oext_eval")),\n             (oe,',
  '             (lej, "OEXT_SETTINGS_PATH", strict_json(lean_path.read_bytes())["oext"]["settings"]["path"]),\n             (oe,'),
 ("V-w-restore-success-only", "the globals are restored only when the call returns (not when it raises)", W,
  '''    try:\n        for obj, name, value in pairs:\n            setattr(obj, name, value)\n        yield\n    finally:\n        for obj, name, value in reversed(saved):\n            setattr(obj, name, value)\n''',
  '''    for obj, name, value in pairs:\n        setattr(obj, name, value)\n    yield\n    for obj, name, value in reversed(saved):\n        setattr(obj, name, value)\n'''),
 ("V-w-lean-no-manifest", "lean: --prepared is not checked against the family's manifest", W,
  '    lean_path, lean_sha, _ = idx.file("lean_eval_job")\n    eval_path, eval_sha, eval_doc = idx.file("oext_eval")\n    check_prepared(args, idx)\n',
  '    lean_path, lean_sha, _ = idx.file("lean_eval_job")\n    eval_path, eval_sha, eval_doc = idx.file("oext_eval")\n'),
 ("V-w-lean-no-branch-flags", "lean: the wrapper does not check Branch 128's flags", W,
  '    check_branch_flags(args, eval_doc, unit=False)\n', ''),
 ("V-w-lean-code", "lean: the run files are not hashed against CODE", W,
  '    check_code(COMMAND_CODE["lean"])\n', ''),
 ("V-w-w1-code", "w1_18: the run files are not hashed against CODE", W,
  '    check_code(COMMAND_CODE["w1_18"])\n', ''),
 ("V-w-unit-manifest-consistency", "unit: the settings' manifest is not compared with the index's", W,
  '''    if unit_doc["prepared"]["manifest_sha256"] != idx.manifest:\n''', '    if False:\n'),
 ("V-m-form-roles", "a kit form lists only the unit settings file of its index", M,
  '    for entry in index["files"].values():\n        out[f"scripts/scale78b/settings/{entry',
  '    for entry in [e for r, e in index["files"].items() if r.startswith("oext_unit")]:\n        out[f"scripts/scale78b/settings/{entry'),
 ("V-m-w1-manifest", "the W1-18 settings keep the 1B prepared manifest", M,
  '''        doc["prepared"]["manifest_sha256"] = self.pins["manifest_sha256"]\n        doc["prepared"]["path"]''',
  '''        doc["prepared"]["path"]'''),
 ("V-m-w1-prepared-path", "the W1-18 settings keep the 1B prepared path", M,
  '''        doc["prepared"]["path"] = self.pins["prepared_path"]\n''', ''),
 # R-5
 ("R5-w-index-name", "the index's file name is not checked against the family and engine", W,
  '        if path.name != wanted:\n', '        if False:\n'),
 ("R5-w-index-content", "the index's family and engine fields are not checked", W,
  '''                (doc.get("family"), doc.get("engine")) != (family, engine):\n''', '''                False:\n'''),
 ("R5-m-waits-uncut", "an index's waits keep every role (another engine's included)", M,
  '            mine = [r for r in entry["roles"] if r in roles]\n', '            mine = list(entry["roles"])\n'),
 ("R5-m-index-shared", "each index records the shared pins (ENGINE_Y reaches the X indexes)", M,
  '''            doc["other_manifests"] = {f: m for f, m in manifests.items() if f != family}\n''',
  '''            doc["other_manifests"] = {f: m for f, m in manifests.items() if f != family}\n            doc["shared"] = dict(pins["shared"])\n'''),
 ("R5-m-index-all-families", "each index lists both families' files (one family's fill reaches the other's pin)", M,
  '''                "files": {role: {"file": file_name(role, self.family), "sha256": self.sha(role)} for role in roles},\n''',
  '''                "files": {role: {"file": file_name(role, self.family), "sha256": self.sha(role)} for role in roles},\n                "pins_families": copy.deepcopy(self.shared.get("_all", {})),\n'''),
 # R-6
 ("R6-w-record-not-read", "check: the record is not read by oext_eval's reader", W,
  '        report["w1_18_record"] = check_w1_18_record(idx, record)\n', '        report["w1_18_record"] = {"record_sha256": None}\n'),
 ("R6-w-record-units", "check: the record's units are not compared with the family's", W,
  '''    if sorted(units) != sorted(w_doc["units"]):\n''', '    if False:\n'),
 ("R6-w-record-optional", "check: a pinned record need not be given", W,
  '    elif pin is not None:\n        raise Refused(f"the family\'s O-ext settings pin W1-18\'s record', '    elif False:\n        raise Refused(f"the family\'s O-ext settings pin W1-18\'s record'),
 ("R6-w-no-validation", "check: the settings files are not run through the 1B validators", W,
  '                validate_one(idx, role, path, sha, doc)\n', '                pass\n'),
 # R-7, R-8
 ("R7-m-device", "the 7-8B W1-18 settings keep the 1B Mac device", M,
  'revision=guard["revision"], device="cuda")', 'revision=guard["revision"])'),
 ("R8-w-y-form-code", "OEXT_78B_Y's form lists the lean copy (engine X's files)", W,
  'ENGINE_CODE = {"X": tuple(CODE), "Y": COMMAND_CODE["unit"]}', 'ENGINE_CODE = {"X": tuple(CODE), "Y": tuple(CODE)}'),
 # R-9
 ("R9-w-listing", "check: a file W1-18 reads need not be listed", W,
  '            if not isinstance(digest, str) or not HEX64.match(digest):\n', '            if False:\n'),
 ("R9-w-hash", "check: a listed file is not hashed", W,
  '            elif sha256_file(folder / rel) != digest:\n', '            elif False:\n'),
 ("R9-w-complete-pin", "check: COMPLETE.json is not checked against its pin", W,
  '''        if sha256_bytes(data) != spec["complete_sha256"]:\n''', '        if False:\n'),
 ("R9-w-job-pin", "check: job.json is not checked against its pin", W,
  '''        elif job.get("sha256") != job_pin or job.get("state") != "listed":\n''', '        elif False:\n'),
 ("R9-w-exit", "check: side-unit problems do not refuse", W,
  '''    if data_root is not None and report["side_units"]["problems"]:\n''', '    if False:\n'),
]
for mid, desc, fname, find, rep in new:
    mutants.append({"id": mid, "describes": desc, "file": fname, "find": find, "replace": rep})
mutants = [m for m in mutants if m["id"] != "R5-m-index-all-families"]     # not a real fault form; dropped
bad = []
for m in mutants:
    n = (PKG / m["file"]).read_text().count(m["find"])
    if n != 1: bad.append((m["id"], n))
print("bad", bad)
spec = {"kind": "scale78b oext mutation spec (R1 Track O, fix round)",
        "note": "each mutant's find text occurs exactly once in its file (a path under scripts/scale78b); runner: tests/oext/run_mutants_oext_78b.py (the suite scripts/scale78b/tests/oext). Fix round: the R1 spec's stale finds updated (9), the verifier's 11 proposed mutants (V-*, adapted to the per-index design) and 15 new ones for R-5 to R-9.",
        "mutants": mutants}
if not bad:
    spec_path.write_text(json.dumps(spec, indent=1) + "\n")
print(len(mutants))
