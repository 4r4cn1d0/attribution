"""The verifier's proposed mutants (written into the scratch source root src2 only; WS is never written)."""
import json, sys
root = sys.argv[1]
M = [
 ("V-w-label-from-file", "oext_78b.py", "unit: the O-ext path label is taken from the settings file itself, not from the file the index makes the run load (a label lie passes)",
  '             (ou, "OEXT_SETTINGS_PATH", fam.label(eval_role)),\n',
  '             (ou, "OEXT_SETTINGS_PATH", unit_doc["oext"]["settings"]["path"]),\n'),
 ("V-w-lean-label-from-file", "oext_78b.py", "lean: the copy's O-ext path label is taken from the lean settings file itself",
  '             (lej, "OEXT_SETTINGS_PATH", fam.label("oext_eval")),\n',
  '             (lej, "OEXT_SETTINGS_PATH", fam.file("lean_eval_job")[2]["oext"]["settings"]["path"]),\n'),
 ("V-w-restore-success-only", "oext_78b.py", "the globals are restored only when the call returns (not when it raises)",
  '    try:\n        for obj, name, value in pairs:\n            setattr(obj, name, value)\n        yield\n    finally:\n        for obj, name, value in reversed(saved):\n            setattr(obj, name, value)\n',
  '    for obj, name, value in pairs:\n        setattr(obj, name, value)\n    yield\n    for obj, name, value in reversed(saved):\n        setattr(obj, name, value)\n'),
 ("V-w-lean-no-manifest", "oext_78b.py", "lean: --prepared is not checked against the family's manifest",
  '    check_prepared(args, fam)\n    check_branch_flags(args, eval_doc, unit=False)\n',
  '    check_branch_flags(args, eval_doc, unit=False)\n'),
 ("V-w-lean-no-branch-flags", "oext_78b.py", "lean: the wrapper does not check Branch 128's flags (the 1B code checks again)",
  '    check_branch_flags(args, eval_doc, unit=False)\n', ''),
 ("V-w-lean-code", "oext_78b.py", "lean: the run files are not hashed against CODE",
  '    check_code(COMMAND_CODE["lean"])\n', ''),
 ("V-w-w1-code", "oext_78b.py", "w1_18: the run files are not hashed against CODE",
  '    check_code(COMMAND_CODE["w1_18"])\n', ''),
 ("V-w-unit-manifest-consistency", "oext_78b.py", "unit: the settings' manifest is not compared with the index's",
  '    if unit_doc["prepared"]["manifest_sha256"] != fam.manifest:\n', '    if False:\n'),
 ("V-m-form-roles", "make_oext_settings_78b.py", "RK OEXT_78B's form lists only oext_unit__F (not oext_eval__F, the W1-18 settings or lean_eval_job__F)",
  '    for role in ("limits_overrefusal_checks", "oext_eval", "oext_unit", "lean_eval_job"):\n',
  '    for role in ("oext_unit",):\n'),
 ("V-m-w1-manifest", "make_oext_settings_78b.py", "the W1-18 settings keep the 1B prepared manifest (Llama's would name OLMo's)",
  '        doc["prepared"]["manifest_sha256"] = self.pins["manifest_sha256"]\n        doc["prepared"]["path"] = self.pins["prepared_path"]\n',
  '        doc["prepared"]["path"] = self.pins["prepared_path"]\n'),
 ("V-m-w1-prepared-path", "make_oext_settings_78b.py", "the W1-18 settings keep the 1B prepared path (Llama's would read OLMo's set)",
  '        doc["prepared"]["path"] = self.pins["prepared_path"]\n', ''),
]
spec = {"kind": "scale78b oext mutation spec (verifier's proposed mutants; scratch only)", "note": "verifier", "mutants": [
    {"id": i, "file": fl, "describes": d, "find": fi, "replace": r} for i, fl, d, fi, r in M]}
src = {fl: open(f"{root}/scripts/scale78b/{fl}").read() for _, fl, _, _, _ in M}
for i, fl, _, fi, _ in M:
    assert src[fl].count(fi) == 1, (i, src[fl].count(fi))
open(f"{root}/scripts/scale78b/tests/oext/mutation_spec_oext_78b.json", "w").write(json.dumps(spec, indent=1) + "\n")
print(len(M), "mutants written")
