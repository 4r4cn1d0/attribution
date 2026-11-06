"""Write the re-verifier's own hand-mutant spec (K4bcr-*) and check each find text occurs exactly once."""
import json, pathlib, sys
kit = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2])
J, P, R, S, B = "setup/job_runner_stage1.py", "plan_tool.py", "rules_78b.py", "stage1_rules.py", "backup_records_stage1.py"
M = [
 ("R1", "D1/PP18", J, "runner hashes every out folder, not only job-I/ ones (unit folders hashed into outputs)",
  'folders = [f for f in out_dirs(commands) if f.startswith(f"job-{index}/")]', 'folders = out_dirs(commands)'),
 ("R2", "D1/PP18", P, "record-done: c0's record hash need not equal the hashed output",
  'if SHA_RE.fullmatch(str(sc.get("c0_record_sha256"))) is None or (r.get("outputs") or {}).get(rel) != sc["c0_record_sha256"]:',
  'if SHA_RE.fullmatch(str(sc.get("c0_record_sha256"))) is None:'),
 ("R3", "PP18", P, "c0 expects C0_SOURCE's COMPLETE.json hash as the adapter fingerprint",
  'job["expect_fingerprint"] = values["C0_SOURCE"]["e1_fingerprint"]', 'job["expect_fingerprint"] = values["C0_SOURCE"]["complete_sha256"]'),
 ("R4", "D2", P, "record-done: a unit kind need not name its unit",
  'if not r.get("unit") or SHA_RE.fullmatch(str(r.get("complete_sha256"))) is None or \\',
  'if SHA_RE.fullmatch(str(r.get("complete_sha256"))) is None or \\'),
 ("R5", "D2", J, "runner: a1_pass's attributes unit is not verified",
  'record.update(unit=unit, complete_sha256=sha(root / unit / "COMPLETE.json"), verified=verify_unit(root, unit, env))',
  'record.update(unit=unit, complete_sha256=sha(root / unit / "COMPLETE.json"), verified=verify_unit(root, unit, env) if kind != "a1_pass" else {"exit": 0, "tail": ""})'),
 ("R6", "PP17", J, "acceptance: a field missing on both sides counts as equal",
  '"equal": rules.hex64(src) is not None and src == got}', '"equal": src == got}'),
 ("R7", "PP17", J, "acceptance: a side fingerprint the regenerated unit omits is skipped",
  'if key in listed:', 'if key in listed and key in (regen_points.get(point) or {}):'),
 ("R8", "PP17", S, "every seed's side-unit input pin is seed 1101's",
  'table[SIDE_COMPLETE.format(seed=seed)] = A0_UNITS[seed]["complete_sha256"]',
  'table[SIDE_COMPLETE.format(seed=seed)] = A0_UNITS[1101]["complete_sha256"]'),
 ("R9", "PP17", P, "record-done: acceptance false with a reason other than LS-04 accepted",
  '(acc is False and r.get("reason") != "LS-04") or \\', 'False or \\'),
 ("R10", "PP17", J, "runner: any job-I file (the acceptance record) counts as O-ext output",
  'if not any(rel.startswith(f"job-{index}/oext/") for rel in record["outputs"]):',
  'if not any(rel.startswith(f"job-{index}/") for rel in record["outputs"]):'),
 ("R11", "PP17", R, "o_only does not wait on OEXT_78B",
  '"o_only": ("OEXT_78B",), "o_only_with_regenerate"', '"o_only": (), "o_only_with_regenerate"'),
 ("R12", "D4", R, "sc block: c0's pod keeps no states (block 0 still says it does)",
  'keeps = SC_STATE_KINDS.get(kind)', 'keeps = SC_STATE_KINDS.get(kind) if kind != "c0" else None'),
 ("R13", "D5", P, "a1_pass's ANCHOR_BANK pin not bound to the recorded anchor file",
  'if pin in r78.SC_KIND_PINS[kind]:                # the core verifier',
  'if pin in r78.SC_KIND_PINS[kind] and kind != "a1_pass":                # the core verifier'),
 ("R14", "D5", P, "rep_pass's pins not bound to the recorded outputs",
  'if pin in r78.SC_KIND_PINS[kind]:                # the core verifier',
  'if pin in r78.SC_KIND_PINS[kind] and kind != "rep_pass":                # the core verifier'),
 ("R15", "D6", R, "OEXT_78B files may be empty",
  'if not isinstance(files, dict) or not files:', 'if not isinstance(files, dict):'),
 ("R16", "D6", R, "OEXT_78B inputs need not be SHA-256 values",
  'if not all(isinstance(v, str) and CONFIG_SHA256.match(v) for v in inputs.values()):', 'if False:'),
 ("R17", "D8", B, "backup: only o_only_with_regenerate's scorer-unit outputs are checked (not a1_pass, retrain)",
  'scorer_unit = plan["hosts"][host].get("block") == "sc" and job.get("kind") not in rules.UNITLESS_KINDS',
  'scorer_unit = plan["hosts"][host].get("block") == "sc" and job.get("kind") == "o_only_with_regenerate"'),
 ("R18", "D8", P, "record-done: a1_pass is not a unit kind",
  'SC_UNIT_KINDS = ("retrain", "a1_pass", "o_only_with_regenerate")   # the job runner',
  'SC_UNIT_KINDS = ("retrain", "o_only_with_regenerate")   # the job runner'),
 ("R19", "A2", R, "rep_pass need not wait for the untuned pass",
  '"rep_pass": ("anchor", "untuned_answers"),', '"rep_pass": ("anchor",),'),
 ("R20", "A2", R, "l1_scan and classifier need not wait for the anchor job",
  'SC_AFTER = {"l1_scan": ("anchor",), "classifier": ("anchor",),', 'SC_AFTER = {"l1_scan": (), "classifier": (),'),
 ("R21", "PP17", J, "acceptance: the side unit need not list an e1 adapter fingerprint",
  'if rules.hex64((side_points.get("e1") or {}).get("adapter_fingerprint")) is None:', 'if False:'),
 ("R22", "PP17", J, "runner: the regenerated unit's fingerprints are not recorded",
  'SC_FINGERPRINT_KINDS = ("retrain", "o_only_with_regenerate")', 'SC_FINGERPRINT_KINDS = ("retrain",)'),
 ("R23", "D4/PP17", S, "block 0's need line drops the per-seed pod count",
  'each = f"{n_pods} pods, one per reused a0 seed, each: " if kind in r78.SC_PER_SEED_KINDS else ""', 'each = ""'),
]
spec = {"kind": "k4b-core-reverify hand mutants", "mutants": []}
bad = 0
for i, part, f, d, find, rep in M:
    n = (kit / f).read_text().count(find)
    if n != 1:
        print("BAD", i, n); bad += 1
    spec["mutants"].append({"id": f"K4bcr-{i}", "part": part, "describes": d, "file": f, "find": find, "replace": rep})
out.write_text(json.dumps(spec, indent=1) + "\n")
print(len(M), "mutants;", bad, "bad")
sys.exit(1 if bad else 0)
