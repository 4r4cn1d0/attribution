import json, pathlib
spec_p = pathlib.Path("tests/mutation_spec_rules_78b.json"); spec = json.loads(spec_p.read_text())
RK = "rules_78b.py"
M = []
def m(i, part, desc, find, replace, file=RK):
    M.append({"id": i, "part": part, "describes": desc, "file": file, "find": find, "replace": replace})
m("KF-m-sigma-a-plan-any", "R-24", "basis sigma_A: any plan passes", "        if doc[\"plan\"] != sigma_plan:\n", "        if False:\n")
m("KF-m-sigma-a-threshold", "R-24", "the seed rule's 4.5 pp threshold moved", '    return "A" if sigma_pp <= 4.5 else "B9" if sigma_pp <= 6.0 else "H"',
  '    return "A" if sigma_pp < 4.5 else "B9" if sigma_pp <= 6.0 else "H"')
m("KF-m-sigma-a-unchecked-value", "R-24", "sigma_A_pp's value not checked",
  '        except Refused:\n            return "SR-2 is adopted, so sigma_A_pp is', '        except ZeroDivisionError:\n            return "SR-2 is adopted, so sigma_A_pp is')
m("KF-m-sigma-a-null-without-sr2", "R-24", "sigma_A_pp allowed without SR-2",
  '        if doc["sigma_A_pp"] is not None:\n            return "SR-2 is not adopted, so sigma_A_pp is null"', '        if False:\n            return "SR-2 is not adopted, so sigma_A_pp is null"')
m("KF-m-pool-plan-any", "R-24", "basis sigma_pool_N: any plan passes",
  '        if plan_b["plan_basis"] == PLAN_BASES["B"] and plan_b["plan"] != doc["provisional_plan"]:', "        if False:")
m("KF-m-sigma-f-plan-any", "R-24", "basis sigma_F: any plan passes",
  '        if plan_b["plan_basis"] == PLAN_BASES["C"] and plan_b["plan"] != doc["sigma_F_plan"]:', "        if False:")
m("KF-m-gate-c-no-sigma-f", "R-24", "the [C] gate need not record sigma_F's plan", '    if doc["option"] == "C" and doc["sigma_F_plan"] not in PLAN_B_CODES:', "    if False:")
m("KF-m-gate-b-sigma-f-any", "R-24", "the [B] gate may record a sigma_F plan", '    if doc["option"] == "B" and doc["sigma_F_plan"] is not None:', "    if False:")
m("KF-m-index-old-name", "R-22", "the index regex takes K1's old name",
  'OEXT_INDEX_RE = re.compile(r"^scripts/scale78b/settings/OEXT-78B(-Y)?__(olmo2-7b|llama31-8b)\\.json$")',
  'OEXT_INDEX_RE = re.compile(r"^scripts/scale78b/settings/(?:oext_index__|OEXT-78B(-Y)?__)(olmo2-7b|llama31-8b)(?:__[XY])?\\.json$")')
m("KF-m-index-y-as-x", "R-22", "a Y index read as engine X", '    eng = "Y" if y else "X"', '    eng = "X"')
m("KF-m-w1-18-records-many", "R-21", "several entries under the W1-18 folder", "    if len(records) > 1:", "    if len(records) > 9:")
m("KF-m-w1-18-record-any-form", "R-21", "any entry under the W1-18 folder", "            if not W1_18_RECORD_RE.match(path):", "            if False:")
m("KF-m-w1-18-folder-any", "R-21", "any .ai folder for the W1-18 record", 'W1_18_RECORD_DIR = ".ai/inputs/stage1-post-w1-20261023/78b/w1-18/"', 'W1_18_RECORD_DIR = ".ai/inputs/"')
m("KF-m-stop-needed-unchecked", "KR2", "the stop record's needed not checked",
  '        if not (isinstance(line, dict) and set(line) == {"kept", "needed"} and line["needed"] == ANCHOR_N_SAFE\n',
  '        if not (isinstance(line, dict) and set(line) == {"kept", "needed"}\n')
m("KF-m-stop-of-unchecked", "KR2", "the harmful counts' of not checked",
  '              and all(_int(line[k]) for k in line) and line["of"] == ANCHOR_N_HARMFUL\n', '              and all(_int(line[k]) for k in line)\n')
m("KF-m-stop-index-range", "KR2", "the prompt_index range not checked",
  '              and 0 <= line["prompt_index"] < ANCHOR_N_HARMFUL and line["position"] == line["prompt_index"] + 1):',
  '              and line["position"] == line["prompt_index"] + 1):')
m("KF-m-stop-jobdone-form", "KR2", "the stop record's job_done_sha256 form not checked",
  '    if not _hex(doc["job_done_sha256"]):\n        return "job_done_sha256 is not a SHA-256"', '    if False:\n        return "job_done_sha256 is not a SHA-256"')
m("KF-m-top-pin-any-arms", "KR7", "a filled s4_top pin is checked even where no s4_top runs",
  '            if "s4_top" in dose_arms and isinstance(top, dict) and top.get("rows") != kept:', '            if isinstance(top, dict) and top.get("rows") != kept:')
m("KF-m-branch-texts", "KR7", "the branch record's utc and recorded_by not checked",
  '    if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("utc", "recorded_by")):', "    if False:")
m("KF-m-stop-read-jobdone-optional", "KR8", "anchor_stop_or_refuse reads without the JOB-DONE hash",
  '    if not _hex(job_done_sha256):\n        raise Refused("the anchor job\'s JOB-DONE.json SHA-256 is required', '    if False:\n        raise Refused("the anchor job\'s JOB-DONE.json SHA-256 is required')
assert not {x["id"] for x in M} & {x["id"] for x in spec["mutants"]}
spec["mutants"].extend(M)
bad = [(x["id"], pathlib.Path(x["file"]).read_text().count(x["find"])) for x in spec["mutants"] if pathlib.Path(x["file"]).read_text().count(x["find"]) != 1]
assert not bad, bad
spec["note"] += " R1 K1 follow-up (8 Nov): KF-m-* for GXB R-21, R-22, R-24 and KR2, KR7, KR8."
spec_p.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
print(len(M), len(spec["mutants"]))
print(",".join(x["id"] for x in M))
