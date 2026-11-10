"""The re-verifier's proposed mutants (scratch source root only, never WS). Checks each find text occurs once."""
import json, sys
from pathlib import Path
ws = Path(sys.argv[1]); out = Path(sys.argv[2])
W, M = "oext_78b.py", "make_oext_settings_78b.py"
muts = [
 ("RV-w-index-kind", W, "the index's kind and version are not checked",
  'or (doc.get("kind"), doc.get("version")) != (INDEX_KIND, INDEX_VERSION) or \\', 'or False or \\'),
 ("RV-w-index-engine", W, "the index's engine field is not checked (family only)",
  '(doc.get("family"), doc.get("engine")) != (family, engine)', 'doc.get("family") != family'),
 ("RV-w-check-code", W, "check: the run files are not hashed against CODE",
  '    check_code(ENGINE_CODE[idx.engine])\n    report = {', '    report = {'),
 ("RV-w-check-waits-mask", W, "check: a refusal of any role is reported as a wait (exit 0)",
  'if role not in waiting or type(exc).__name__ != "Refusal":', 'if type(exc).__name__ != "Refusal":'),
 ("RV-w-check-record-y", W, "check: the record is read under engine X's O-ext settings on a Y index",
  'eval_role = "oext_eval" if idx.engine == "X" else "oext_eval_y"\n    eval_path, eval_sha, eval_doc = idx.file(eval_role)',
  'eval_role = "oext_eval"\n    eval_path, eval_sha, eval_doc = idx.file(eval_role)'),
 ("RV-w-check-pin-y", W, "check: the record pin is read from engine X's O-ext settings on a Y index",
  'eval_role = "oext_eval" if idx.engine == "X" else "oext_eval_y"\n    pin = idx.file(eval_role)',
  'eval_role = "oext_eval"\n    pin = idx.file(eval_role)'),
 ("RV-w-side-job-fallback", W, "check: job.json named only by COMPLETE.json's job_sha256 is not found",
  'digest = marker.get("job_sha256")', 'digest = None'),
 ("RV-w-side-root", W, "check: a unit folder outside the data root is read",
  'if root not in folder.parents:\n            problems.append(f"{name}: its path leaves the data root")',
  'if False:\n            problems.append(f"{name}: its path leaves the data root")'),
 ("RV-w-side-complete-true", W, "check: a COMPLETE.json without complete=true is taken",
  'if not isinstance(listed, dict) or marker.get("complete") is not True:', 'if not isinstance(listed, dict):'),
 ("RV-w-record-units-count", W, "check: the record's units are compared by count, not by name",
  'if sorted(units) != sorted(w_doc["units"]):', 'if len(units) != len(w_doc["units"]):'),
 ("RV-m-check-always-ok", M, "maker --check never reports a file that differs from the derivation",
  '        if bad:\n            print(f"DIFFERS', '        if False:\n            print(f"DIFFERS'),
]
spec = {"kind": "scale78b oext mutation spec (re-verifier proposals)", "note": "scratch only", "mutants": []}
for mid, fname, desc, find, rep in muts:
    text = (ws / "scripts/scale78b" / fname).read_text()
    n = text.count(find)
    assert n == 1, (mid, n)
    spec["mutants"].append({"id": mid, "file": fname, "describes": desc, "find": find, "replace": rep})
out.write_text(json.dumps(spec, indent=1) + "\n")
print(len(spec["mutants"]), "mutants; every find text once")
