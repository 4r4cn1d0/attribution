"""Re-verifier's second-pass proposed mutants (scratch source root only). Each find text must occur once."""
import json, sys
from pathlib import Path
ws, out = Path(sys.argv[1]), Path(sys.argv[2])
W, M = "oext_78b.py", "make_oext_settings_78b.py"
muts = [
 ("RV2-m-w1-side-job", M, "W1_18_78B's side units lose their job.json pins",
  '"job_sha256": u["job_sha256"]}', '"job_sha256": None}'),
 ("RV2-m-w1-side-family", M, "W1_18_78B lists OLMo's side units for every family",
  'limits = s1.strict_json(files[file_name("limits_overrefusal_checks", family)])',
  'limits = s1.strict_json(files[file_name("limits_overrefusal_checks", "olmo2-7b")])'),
 ("RV2-w-w1-record-ignored", W, "check on the W1 index ignores a given W1-18 record",
  '        if record is not None:\n            raise Refused("the W1-18 pod\'s index holds no O-ext settings',
  '        if False:\n            raise Refused("the W1-18 pod\'s index holds no O-ext settings'),
 ("RV2-w-null-identity-waits", W, "an index with no engine identity and no ENGINE_Y wait reports waits",
  '                if not any(w["pin"] == "ENGINE_Y" and role in w["roles"] for w in idx.doc["waits"]):',
  '                if False:'),
]
spec = {"kind": "scale78b oext mutation spec (re-verifier second-pass proposals)", "note": "scratch only", "mutants": []}
for mid, fname, desc, find, rep in muts:
    n = (ws / "scripts/scale78b" / fname).read_text().count(find)
    assert n == 1, (mid, n)
    spec["mutants"].append({"id": mid, "file": fname, "describes": desc, "find": find, "replace": rep})
out.write_text(json.dumps(spec, indent=1) + "\n")
print(len(spec["mutants"]), "mutants; every find text once")
