import json, pathlib
spec_p = pathlib.Path("tests/mutation_spec_rules_78b.json"); spec = json.loads(spec_p.read_text())
by = {m["id"]: m for m in spec["mutants"]}
RK, SR = "rules_78b.py", "stage1_rules.py"
def retarget(i, find, replace):
    by[i]["find"], by[i]["replace"] = find, replace
retarget("K1R-m-s4-top-range-off", '    if arm == "s4_top" and not s4_top_rows_ok(edit_rows):', "    if False:")
retarget("K1R-m-check-keys-oext-bank-any", '        if oext_bank != pin["inputs"]["oext_bank"]:', "        if False:")
retarget("K1R-m-bank500-no-record-passes", '    if BRANCH_78B[family] is None:\n        return (f"{kind} in block {block} reads the 500 bank',
         '    if False:\n        return (f"{kind} in block {block} reads the 500 bank')
retarget("K1R-m-plan-b-sr2-hashes-optional", '            if not _hex(doc[key]):\n                return f"SR-2 is adopted, so {key} must be a SHA-256"',
         '            if False:\n                return f"SR-2 is adopted, so {key} must be a SHA-256"')
retarget("K1R-m-plan-b-ignores-gate-families",
         '    doc = gate_record_or_refuse(data)\n    if block == "A" and doc["provisional_plan"] == "review":',
         '    doc = {"families": FAMILIES, "option": "B", "provisional_plan": "A"} if block == "B" else gate_record_or_refuse(data)\n    if block == "A" and doc["provisional_plan"] == "review":')
M = []
def m(i, part, desc, find, replace, file=RK):
    M.append({"id": i, "part": part, "describes": desc, "file": file, "find": find, "replace": replace})
# K1V-1, K1V-6: the stop record's form and its read
m("K1V-m-stop-kind-old", "K1V-1", "the stop record's old kind string", 'ANCHOR_STOP_KIND = "scale-78b anchor stop"', 'ANCHOR_STOP_KIND = "stage1-78b anchor stop"')
m("K1V-m-stop-value-old", "K1V-1", "the exit-3 stop value of round 1", 'STOP_FEW_SAFE = "safe_anchors_below_64"', 'STOP_FEW_SAFE = "few_safe"')
m("K1V-m-stop-field-old", "K1V-1", "the field stop instead of stop_kind", 'ANCHOR_STOP_KEYS = ("kind", "version", "family", "stop_kind",', 'ANCHOR_STOP_KEYS = ("kind", "version", "family", "stop",')
m("K1V-m-stop-unread-passes", "K1V-6", "a pinned stop marks the family stopped unread",
  '    if _ANCHOR_STOPS_READ.get(family) != pin["sha256"]:\n        raise Refused(f"ANCHOR_STOP', '    if False:\n        raise Refused(f"ANCHOR_STOP')
m("K1V-m-stop-read-unchecked", "K1V-6", "the pinned stop record's form unchecked", "lambda d: anchor_stop_problem(d, family, job_done_sha256))", "lambda d: None)")
m("K1V-m-stop-exit-type", "K1V-7", "the stop record's exit code not type-checked",
  '    if doc["stop_kind"] not in ANCHOR_STOPS or not _int(doc["exit_code"]) \\', '    if doc["stop_kind"] not in ANCHOR_STOPS \\')
# K1V-2: the dose table
m("K1V-m-dose-192-adds-top", "K-5", "n >= 192 also plans s4_top", '    if kept >= S4_KEEP:\n        return ("S4_96", "S4_192")', '    if kept >= S4_KEEP:\n        return ("S4_96", "S4_192", "s4_top")')
m("K1V-m-dose-97-191-192", "K-5", "97-191 plans S4_192 instead of s4_top", '    if kept > S4_DOSE_96:\n        return ("S4_96", "s4_top")', '    if kept > S4_DOSE_96:\n        return ("S4_96", "S4_192")')
m("K1V-m-dose-96-adds-top", "K-5", "n = 96 also plans s4_top", '    if kept == S4_DOSE_96:\n        return ("S4_96",)', '    if kept == S4_DOSE_96:\n        return ("S4_96", "s4_top")')
m("K1V-m-dose-48-top", "K-5", "n = 48 plans s4_top", '    if kept > S4_MIN_KEPT:\n        return ("s4_top",)', '    if kept >= S4_MIN_KEPT:\n        return ("s4_top",)')
m("K1V-m-dose-below-48-passes", "K-5", "fewer than 48 kept is no build stop", '    if kept < S4_MIN_KEPT:\n        raise Refused(f"{kept} kept S4 rows', '    if False:\n        raise Refused(f"{kept} kept S4 rows')
m("K1V-m-dose-top-pin-rows-unchecked", "K-5", "a filled s4_top pin's rows not held to the kept count",
  '            if "s4_top" in dose_arms and isinstance(top, dict) and top.get("rows") != kept:', "            if False:")
# K1V-3, R-1: PLAN_B and the gate
m("K1V-m-plan-b-reason-unchecked", "K-6", "no reason needed without SR-2", '        if doc["sr2_reason"] not in SR2_REASONS:', "        if False:")
m("K1V-m-plan-b-basis-any-option", "K-6", "the plan's basis not held to the option", '        if option is not None and doc["plan_basis"] != PLAN_BASES.get(option):', "        if False:")
m("K1V-m-plan-b-hashes-without-sr2", "K-6", "blinded_sigma hashes allowed without SR-2",
  '            if doc[key] is not None:\n                return f"SR-2 is not adopted, so {key} must be null"', '            if False:\n                return f"SR-2 is not adopted, so {key} must be null"')
m("K1V-m-plan-b-no-option", "K-6", "block B's init passes no option", 'plan_b_record_or_refuse(plan_b_data, doc["option"])', "plan_b_record_or_refuse(plan_b_data)")
m("K1V-m-review-plans-a", "R-1", "block A plans under a review provisional plan", '    if block == "A" and doc["provisional_plan"] == "review":', "    if False:")
m("K1V-m-gate-version-type", "K1V-7", "the gate's version not type-checked",
  '    if doc["kind"] != GATE_RECORD_KIND or doc["version"] != 1 or type(doc["version"]) is not int:', '    if doc["kind"] != GATE_RECORD_KIND or doc["version"] != 1:')
# K1V-5, R-4: the pinned branch
m("K1V-m-bank500-unpinned-bytes", "K1V-5", "a 500-bank job accepts bytes that are not the pinned branch record",
  '    try:\n        branch_record_or_refuse(family, branch_bytes)\n    except Refused as exc:', '    try:\n        pass\n    except Refused as exc:')
m("K1V-m-flags-unpinned", "K1V-5", "the flags read an unpinned branch document", '    branch_doc = branch_record_or_refuse(family, branch_bytes)', "    branch_doc = json.loads(branch_bytes)")
m("K1V-m-branch-version-type", "K1V-7", "the branch record's version not type-checked",
  '    if doc["kind"] != BRANCH_RECORD_KIND or doc["version"] != 1 or not _int(doc["version"]) or doc["family"] != family:',
  '    if doc["kind"] != BRANCH_RECORD_KIND or doc["version"] != 1 or doc["family"] != family:')
m("K1V-m-branch-switch-branch-only", "K1V-7", "the switch check compares family and branch only",
  'for k in ("family", "branch", "source", "w1_18_record_sha256"))', 'for k in ("family", "branch"))')
m("K1V-m-oext-kinds-no-branch", "R-4", "the scorer block's O-ext kinds do not wait on BRANCH_78B",
  '    if kind in SC_BRANCH_KINDS:\n        pins = pins + ("BRANCH_78B",)', '    if False:\n        pins = pins + ("BRANCH_78B",)')
# K1V-8, K1V-9, K1V-13 / R-3
m("K1V-m-n-units-import-raises", "K1V-8", "a malformed N_UNITS pin raises at import",
  "        n = None                                         # K1V-8", "        raise Refused(str(n_units_problem(n, family)))  # K1V-8")
m("K1V-m-rejudged-malformed-unnamed", "K1V-8", "the judge launch does not name a malformed N_UNITS",
  '    if block == "A" and n is not None and n_units_problem(n, family):', "    if False:")
m("K1V-m-missing-arm-passes", "K1V-9", "a missing arm names the side unit by default",
  '        if arm is None:\n            raise ValueError("o_only_with_regenerate names its unit', '        if False:\n            raise ValueError("o_only_with_regenerate names its unit', SR)
m("K1V-m-block0-new-keys", "R-3", "block 0's job records gain the two new keys", "    if oext or padded_tokens_per_step is not None:", "    if True:")
# R-5
m("K1V-m-index-any-family", "R-5", "an O-ext pin accepts another family's or engine's index", "    if (fam, eng) != (family, engine):", "    if False:")
m("K1V-m-index-count-any", "R-5", "an O-ext pin may name two indexes", "    if len(indexes) != 1:", "    if len(indexes) < 1:")
m("K1V-m-index-no-wrapper", "R-5", "an O-ext pin need not pin the wrapper",
  '    if OEXT_WRAPPER_78B not in oext["files"]:\n        return f"its files do not pin', '    if False:\n        return f"its files do not pin')
m("K1V-m-index-not-checked", "R-5", "OEXT_78B's index not checked at planning", '    if oext is not None and oext_index_problem(oext, family, "X"):', "    if False:")
m("K1V-m-y-pin-engine-x", "R-5", "OEXT_78B_Y checked for engine X's index", '    problem = oext_form_problem(value, family, "Y")', '    problem = oext_form_problem(value, family, "X")')
m("K1V-m-check-keys-y-reads-x", "R-5", "check_keys reads OEXT_78B for an engine-Y job",
  'name, pin = (f"OEXT_78B[{family!r}]", OEXT_78B[family]) if engine == "X" else \\', 'name, pin = (f"OEXT_78B[{family!r}]", OEXT_78B[family]) if True else \\')
# K1V-7 probes
m("K1V-m-edit-pin-any-suffix", "K1V-7", "an edit pin of any suffix", 'and pin["path"].endswith(".json")):', "):")
m("K1V-m-files-form-any-dir", "K1V-7", "W1_18_78B files outside scripts/", '        if not _plain_rel(path, "scripts/"):', "        if not _plain_rel(path):")
m("K1V-m-n-units-keys-loose", "K1V-7", "an N unit with extra keys", "        if not isinstance(u, dict) or set(u) != keys:", "        if not isinstance(u, dict) or not keys <= set(u):")
m("K1V-m-n-units-r-only", "K1V-7", "N_UNITS needed for R units only (Llama's N a0-1103 not)",
  '    if family is not None and arm is not None and sc_unit_source(family, kind, arm, seed) == "n":',
  '    if family is not None and arm is not None and arm == "R":')
assert not {x["id"] for x in M} & set(by)
spec["mutants"].extend(M)
for x in spec["mutants"]:
    n = pathlib.Path(x["file"]).read_text().count(x["find"])
    assert n == 1, (x["id"], n)
spec["note"] += (" R1 K1 fix round (8 Nov): 5 K1R find texts re-targeted after the fixes (same mutations); K1V-m-* added "
                 "for K1V-1..K1V-13, GXB K-5, K-6, R-1, R-3, R-4, R-5 and the verifier's 7 surviving probes.")
spec_p.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
print(len(M), len(spec["mutants"]))
print(",".join(x["id"] for x in M))
