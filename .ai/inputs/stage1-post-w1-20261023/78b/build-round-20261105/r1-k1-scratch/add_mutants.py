import json, pathlib, sys
kit = pathlib.Path(sys.argv[1])
spec_path = kit / "tests" / "mutation_spec_rules_78b.json"
spec = json.loads(spec_path.read_text())
RK, SR = "rules_78b.py", "stage1_rules.py"
M = []
def m(i, part, desc, file, find, replace):
    M.append({"id": i, "part": part, "describes": desc, "file": file, "find": find, "replace": replace})
# item 1: tables and edits
m("K1R-m-block-a-no-r5", "item 1", "block A without R_5 at 1105", RK, "BLOCK_A_R_SEEDS = (1104, 1105) ", "BLOCK_A_R_SEEDS = (1104,) ")
m("K1R-m-b9-seeds-1109", "item 1", "plan B9's method seeds 1105-1109", RK, '"B9": tuple(range(1105, 1111))', '"B9": tuple(range(1105, 1110))')
m("K1R-m-b-r-at-first-seed", "item 1", "block B's R also at its first seed (R_5 again)", RK,
  '[("R", s) for s in seeds if s != seeds[0]]', '[("R", s) for s in seeds]')
m("K1R-m-b-a0-two-seeds", "item 1", "block B's a0 at 1105-1106 only", RK, "BLOCK_B_A0_SEEDS = (1105, 1106, 1107) ", "BLOCK_B_A0_SEEDS = (1105, 1106) ")
m("K1R-m-r-d6-from-seal", "item 1", "R_d6 bound from SEAL, not stage 1's r-draws", RK, "(6, _R_OLMO_STAGE1,", "(6, _R_OLMO_SEAL,")
m("K1R-m-null-method-edit-accepted", "item 1", "a null method edit accepted", RK,
  "    if pin is None:\n        raise Refused(f\"{arm}'s edit for {family} is null",
  "    if pin is None:\n        pin = {\"path\": \"tmp/null.json\", \"sha256\": \"0\" * 64, \"rows\": ARM_EDIT[arm][1] or 48}\n    if False:\n        raise Refused(f\"{arm}'s edit for {family} is null")
m("K1R-m-stopped-keeps-l1", "item 1, 14", "a stopped family keeps L1", RK, 'STOP_DROPPED_ARMS = ("A1", "L1", "S3")', 'STOP_DROPPED_ARMS = ("A1", "S3")')
m("K1R-m-stop-drop-off", "item 1, 14", "a stopped family keeps A1, L1 and S3", RK,
  "    if family_stopped(family):\n        runs = [r for r in runs if r[0] not in STOP_DROPPED_ARMS]",
  "    if False:\n        runs = [r for r in runs if r[0] not in STOP_DROPPED_ARMS]")
m("K1R-m-gate-hash-unchecked", "O14", "the plan code read from bytes that are not the pinned gate record", RK,
  "hashlib.sha256(data).hexdigest() != pin[\"sha256\"]:", "False:")
m("K1R-m-gate-null-passes", "O14", "GATE_78B null passes", RK,
  "    if pin is None:\n        raise Refused(f\"the gate record pin GATE_78B is null",
  "    if pin is None:\n        return json.loads(data)\n        raise Refused(f\"the gate record pin GATE_78B is null")
m("K1R-m-gate-c-both-families", "O14", "option C runs both families", RK,
  'GATE_OPTIONS = {"B": ("olmo2-7b", "llama31-8b"), "C": ("olmo2-7b",)}', 'GATE_OPTIONS = {"B": ("olmo2-7b", "llama31-8b"), "C": ("olmo2-7b", "llama31-8b")}')
m("K1R-m-gate-family-unchecked", "O14", "block A's init ignores the gate's families", RK,
  '    if family not in doc["families"]:\n        raise Refused(f"the gate chose', '    if False:\n        raise Refused(f"the gate chose')
# item 2: the deal
m("K1R-m-deal-p1", "item 2", "P = 1 in the deal", RK, "    p = len(pod_sizes(len(ordered)))\n    pods = [ordered[i::p] for i in range(p)]",
  "    p = 1\n    pods = [ordered[i::p] for i in range(p)]")
m("K1R-m-deal-seed-major", "item 2", "seed-major order in the deal", RK,
  "key=lambda r: (AB_ARM_ORDER.index(r[0]), r[1]))\n    if len(set(ordered))", "key=lambda r: (r[1], AB_ARM_ORDER.index(r[0])))\n    if len(set(ordered))")
m("K1R-m-deal-5-per-pod", "item 2", "5 arms per pod", RK, "    p = len(pod_sizes(len(ordered)))\n", "    p = -(-len(ordered) // 5)\n")
m("K1R-m-sr78-deal-n-for-ab", "item 2", "the kit copy deals blocks A and B as N", SR,
  "    if block in (\"A\", \"B\"):\n        try:\n            return r78.deal_ab(runs)", "    if False:\n        try:\n            return r78.deal_ab(runs)")
# item 3: steps
m("K1R-m-dose-38", "item 3, O1", "dose 38 steps", RK, '"a0": 38, "dose": 39}', '"a0": 38, "dose": 38}')
m("K1R-m-rows-check-skipped", "item 3, O1", "the rows check skipped (a named arm's derived steps not compared)", RK,
  "    if arm in ARM_STEPS and derived != ARM_STEPS[arm]:", "    if False:")
m("K1R-m-steps-floor", "O1", "steps = floor(rows / 128)", RK, "    return -(-rows // ROWS_PER_STEP)", "    return rows // ROWS_PER_STEP")
m("K1R-m-s4-top-range-off", "O1", "s4_top accepts any kept count", RK,
  '    if arm == "s4_top" and not S4_TOP_MIN <= edit_rows <= S4_TOP_MAX:', "    if False:")
m("K1R-m-sr78-dose-38", "item 3", "the kit copy's DOSE_STEPS dose 38", SR, '"dose": r78.STEPS["dose"]}', '"dose": r78.STEPS["add"]}')
# item 4: train_scale
m("K1R-m-train-scale-missing-passes", "item 4", "a missing padded-token count passes (train_scale 1)", RK,
  "        if padded_tokens_per_step is None:\n            raise Refused(f\"{arm} at {seed}: its padded tokens",
  "        if False:\n            raise Refused(f\"{arm} at {seed}: its padded tokens")
m("K1R-m-requirements-drop-padded", "item 4", "requirements() drops the job's padded tokens", RK,
  "s, 1.0, preflight,\n                                     job.get(\"padded_tokens_per_step\")",
  "s, 1.0, preflight,\n                                     None")
m("K1R-m-sr78-job-record-drops-padded", "item 4", "the kit copy's job_record drops the padded tokens", SR,
  "arm, seed, padded_tokens_per_step, n_points=n,", "arm, seed, None, n_points=n,")
# item 5b: the O-ext term
m("K1R-m-oext-x1", "5b", "the O-ext term x 1.0", RK, "OEXT_TERM_FACTOR = 1.5 ", "OEXT_TERM_FACTOR = 1.0 ")
m("K1R-m-oext-a0-arm-off", "5b", "the a0_arm O-ext step dropped", RK,
  'OEXT_CAP_KINDS = frozenset({"arm", "a0_arm", "ref_train"})', 'OEXT_CAP_KINDS = frozenset({"arm", "ref_train"})')
m("K1R-m-oext-measured-ignored", "5b", "the measured O-ext value ignored", RK,
  "    if measured is not None:\n        if finite(measured) <= 0:", "    if False:\n        if finite(measured) <= 0:")
m("K1R-m-oext-measured-upper-no-term", "5b", "the measured upper of an O-ext job without its term", RK,
  "        measured = measured_upper_s(family, kind) + (oext_term_s(family) if oext else 0.0)",
  "        measured = measured_upper_s(family, kind)")
m("K1R-m-requirements-drop-oext", "5b", "requirements() drops the O-ext term", RK,
  "job.get(\"padded_tokens_per_step\"), job.get(\"oext\", False) is True))\n", "job.get(\"padded_tokens_per_step\"), False))\n")
m("K1R-m-decision-drop-oext", "5b", "the runner's gate drops the O-ext term", RK,
  "job.get(\"padded_tokens_per_step\"), job.get(\"oext\", False) is True)\n    reason", "job.get(\"padded_tokens_per_step\"), False)\n    reason")
m("K1R-m-oext-refs-off", "5b, O12", "ref_eval's points without the O-ext term", RK,
  "                 + n_points * (evalonly_upper_s(family) + oext_term_s(family)))\n        basis = (\"E: the evaluation-only",
  "                 + n_points * evalonly_upper_s(family))\n        basis = (\"E: the evaluation-only")
m("K1R-m-oext-batches-12", "5b", "the PHTest pass in 12 batches", RK, "    batches = -(-OEXT_PHTEST_PROMPTS // GENERATION_BATCH)",
  "    batches = OEXT_PHTEST_PROMPTS // GENERATION_BATCH")
m("K1R-m-block0-gets-oext", "5b", "block 0's arms carry the O-ext term", RK,
  'STEPS["a0"] if arm == "a0" else STEPS["remove"], arm, seed))', 'STEPS["a0"] if arm == "a0" else STEPS["remove"], arm, seed, oext=True))')
m("K1R-m-block-job-no-oext", "5b", "a block A/B edit arm without its O-ext step", RK,
  'job = job_record(family, "arm", edit["steps"], arm, seed, padded_tokens_per_step, oext=True)',
  'job = job_record(family, "arm", edit["steps"], arm, seed, padded_tokens_per_step, oext=False)')
m("K1R-m-check-keys-oext-bank-any", "5b", "check_keys accepts any O-ext bank", RK,
  '        if oext_bank != OEXT_78B[family]["inputs"]["oext_bank"]:', "        if False:")
m("K1R-m-check-keys-oext-kind-any", "5b", "check_keys lets a kind without O-ext name an O-ext bank", RK,
  '        if kind not in OEXT_BANK_KINDS:\n            raise Refused(f"{kind} has no O-ext step: it names', '        if False:\n            raise Refused(f"{kind} has no O-ext step: it names')
# 5c: w1_18, branches
m("K1R-m-w1-18-not-first", "5c", "W1-18 not first (planned after a 500-bank job)", RK,
  "    before = sorted({k for k in planned_kinds if k in BANK500_KINDS})", "    before = []")
m("K1R-m-w1-18-c-both", "5c, O4", "under [C] both families' W1-18 units", RK,
  'W1_18_FAMILIES = {"B": ("olmo2-7b", "llama31-8b"), "C": ("olmo2-7b",)}', 'W1_18_FAMILIES = {"B": ("olmo2-7b", "llama31-8b"), "C": ("olmo2-7b", "llama31-8b")}')
m("K1R-m-w1-18-one-record", "5c, O4", "one W1-18 record for both families", RK,
  '"records": {f: f"w1_18_record__{f}.json" for f in fams}', '"records": {f: "w1_18_record.json" for f in fams}')
m("K1R-m-w1-18-not-x-only", "5c", "w1_18 allowed on engine Y", RK, '"classifier", "c0", "w1_18"})', '"classifier", "c0"})')
m("K1R-m-w1-18-cap-no-factor", "5c", "the W1-18 E cap without the 1.5 factor", RK,
  '        upper = WIDE_CAP_FACTOR * STAGE1_1B_ESTIMATES_S["w1_18"]', '        upper = STAGE1_1B_ESTIMATES_S["w1_18"]')
m("K1R-m-branch-switch-allowed", "5c", "a branch switch allowed", RK, "    if not same:\n        return (f\"{old_doc.get('family')}'s branch",
  "    if False:\n        return (f\"{old_doc.get('family')}'s branch")
m("K1R-m-branch-128-by-default", "5c", "the default record may name Branch 128", RK,
  '        if doc["branch"] != BRANCH_DEFAULT or doc["w1_18_record_sha256"] is not None:', "        if False:")
m("K1R-m-bank500-block0-arms", "5c", "block 0's arms read the 500 bank", RK,
  'kind in ("arm", "a0_arm") and block in BANK500_BLOCKS)', 'kind in ("arm", "a0_arm"))')
m("K1R-m-bank500-no-record-passes", "5c", "a 500-bank job before the branch record", RK,
  "    if branch_doc is None:\n        return (f\"{kind} in block {block} reads the 500 bank", "    if False:\n        return (f\"{kind} in block {block} reads the 500 bank")
m("K1R-m-flag-dropped-on-c0", "5f", "--w1-18-record dropped on c0", RK,
  '    return {"w1_18_record": branch_doc["w1_18_record_sha256"], "dev100_source": bool(regenerated)}',
  '    return {"w1_18_record": None if kind == "c0" else branch_doc["w1_18_record_sha256"], "dev100_source": bool(regenerated)}')
m("K1R-m-dev100-on-theta0", "5f", "--dev100-source on theta0 (every O-ext command)", RK,
  '"dev100_source": bool(regenerated)}', '"dev100_source": True}')
# 5e and the seed key
m("K1R-m-seed-key-seed-only", "seed key", "a unit found by its seed alone", RK, '        if u["arm"] == arm and u["seed"] == seed:', '        if u["seed"] == seed:')
m("K1R-m-n-units-not-listed", "5e", "N's units not among o_only_with_regenerate's", RK,
  '        out += [{"arm": a, "seed": s, "source": "n"} for a, s in block0_runs(family)]', "        out += []")
m("K1R-m-n-regen-without-edit", "5e", "N's R regenerated without its sealed edit", SR,
  '((REGEN_EDIT.format(seed=seed),) if arm == "R" else ())', "()")
m("K1R-m-acceptance-against-side", "5e", "N's unit accepted against the side unit", SR,
  '    if _unit_source(kind, seed, arm) == "n":\n        names', "    if False:\n        names")
m("K1R-m-n-units-null-passes", "5e", "N's regeneration without the N_UNITS pin", RK, '        pins = pins + ("N_UNITS",)', "        pins = pins")
m("K1R-m-n-units-path-loose", "5e", "an N unit's path outside block 0's copy", RK,
  '        if not _plain_rel(u["path"], f"tmp/{WORKING_COPY_PREFIX}{family}-0/"):', '        if not _plain_rel(u["path"]):')
# item 7: re-judge pins
m("K1R-m-rejudged-no-theta0", "item 7", "block A's re-judge list without theta0", RK,
  '    out.append({"name": "theta0 (untuned)", "arm": "a0", "seed": 1101, "target": "init", **units["untuned"]})', "    pass")
m("K1R-m-rejudged-null-passes", "item 7", "a judge launch with N's entries null", RK, "    if null:\n        raise Refused(f\"block {block}'s re-judged", "    if False:\n        raise Refused(f\"block {block}'s re-judged")
m("K1R-m-sr78-rejudged-a-empty", "item 7", "the kit copy's REJUDGED_PINS['A'] empty", SR,
  '"A": r78.rejudged_pins(FAMILY, "A") if _KIT else ()', '"A": ()')
# O6 and item 14: the anchor stops
m("K1R-m-anchor-any-exit-1", "O6", "any exit 1 is a harmful-pair stop", RK,
  "    if exit_code == ANCHOR_EXIT_ERROR and isinstance(message, str) and ANCHOR_HARMFUL_RE.match(message.strip()):",
  "    if exit_code == ANCHOR_EXIT_ERROR:")
m("K1R-m-anchor-crash-is-stop", "O6", "any other exit is a stop", RK, '    return "crash"\n\n\ndef anchor_stop_record', '    return "few_safe"\n\n\ndef anchor_stop_record')
m("K1R-m-anchor-job-done-unchecked", "O6", "the stop record need not name the anchor job's JOB-DONE.json", RK,
  '    if job_done_sha256 is not None and doc["job_done_sha256"] != job_done_sha256:', "    if False:")
m("K1R-m-stopped-plans-l1-scan", "item 14", "a stopped family plans l1_scan", RK,
  'STOP_REFUSED_KINDS = frozenset({"rep_pass", "l1_scan", "classifier", "a1_pass", "anchor"})',
  'STOP_REFUSED_KINDS = frozenset({"rep_pass", "classifier", "a1_pass", "anchor"})')
m("K1R-m-main-retrain-without-stop", "item 14", "the retrain under MAIN_F without a stop record", RK,
  '    if kind == "retrain" and family_stopped(family):\n        if recipe_sha256', '    if kind == "retrain":\n        if recipe_sha256')
m("K1R-m-stopped-retrain-any-recipe", "item 14", "a stopped family's retrain under any recipe", RK,
  '        if recipe_sha256 != CONFIGS[family]["main"][1]:\n            raise Refused(f"the retrain on {family}',
  '        if False:\n            raise Refused(f"the retrain on {family}')
m("K1R-m-stopped-retrain-needs-s", "item 14", "a stopped family's retrain still waits on RECIPE_S", RK,
  '    if family is not None and kind == "retrain" and family_stopped(family):', "    if False:")
m("K1R-m-stop-order-anchor-needed", "item 14", "a stopped family's retrain still waits on a complete anchor job", RK,
  '        if kind == "retrain" and family_stopped(family):\n            return None', "        if False:\n            return None")
m("K1R-m-decision-stopped-retrain-s", "item 14", "the runner's gate demands S_78 for the stopped family's retrain", RK,
  '    if job["kind"] in S78_KINDS and not (job["kind"] == "retrain" and family_stopped(family)):', '    if job["kind"] in S78_KINDS:')
m("K1R-m-sc-recipe-stopped-s", "item 14", "the stopped family's retrain carries recipe S", RK,
  '    if kind == "retrain" and family_stopped(family):\n        return "B"', '    if kind == "retrain" and family_stopped(family):\n        return "S"')
m("K1R-m-sr78-retrain-job-stopped-s", "item 14", "the kit copy's retrain_job refuses on a stopped family", SR,
  "    if r78.family_stopped(fam):", "    if False:")
# item 6's ref_train (the cap term's kind)
m("K1R-m-ref-train-any-recipe", "5b, item 6", "ref_train accepts the main config", RK,
  '    elif kind in G_KINDS:\n        if recipe_sha256 != pin_or_refuse("RECIPE_G", family):', '    elif False:\n        if recipe_sha256 != pin_or_refuse("RECIPE_G", family):')
m("K1R-m-ref-train-decision-unpinned", "5b, item 6", "the runner's gate runs ref_train with RECIPE_G null", RK,
  '    if job["kind"] in G_KINDS:\n        pin_or_refuse("RECIPE_G", family)', '    if False:\n        pin_or_refuse("RECIPE_G", family)')
# 5d: the wrapper path; the blocks
m("K1R-m-oext-script-1b", "5d", "OEXT_UNIT_SCRIPT back to the 1B script", RK, "OEXT_UNIT_SCRIPT = OEXT_WRAPPER_78B ", 'OEXT_UNIT_SCRIPT = "scripts/stage1_s1/oext_unit.py" ')
m("K1R-m-sr78-blocks-no-b", "item 1", "the kit copy's BLOCKS without B", SR, 'BLOCKS = ("0", "sc", "A", "B") ', 'BLOCKS = ("0", "sc", "A") ')
ids = {x["id"] for x in spec["mutants"]}
assert not ids & {x["id"] for x in M}
for x in M:
    text = (kit / x["file"]).read_text()
    n = text.count(x["find"])
    assert n == 1, (x["id"], n)
spec["mutants"].extend(M)
spec["note"] += (" R1 K1 (8 Nov): the block A/B rules layer adds the K1R-m-* mutants (the block tables and edits, the deal, "
                 "GXB O1's steps, train_scale's input, the O-ext cap term, W1-18 and the branch rules, the (arm, seed) key "
                 "and N_UNITS, block A's re-judge list, GXB O6's anchor stops and the stopped family's MAIN_F retrain, "
                 "ref_train under RECIPE_G, the wrapper path, GXB O14's gate record); the block-table tests run inside "
                 "test_rules_78b.py's test_23, so this runner's one file kills them.")
spec_path.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
print(len(M), "added;", len(spec["mutants"]), "in all")
print(",".join(x["id"] for x in M))
