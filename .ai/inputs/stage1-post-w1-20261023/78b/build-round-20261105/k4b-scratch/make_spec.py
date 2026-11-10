import json, pathlib, sys
kit = pathlib.Path(sys.argv[1])
R, S, P, K, J = "rules_78b.py", "stage1_rules.py", "plan_tool.py", "pack_setup.py", "setup/job_runner_stage1.py"
M = []
def m(id_, part, describes, file, find, replace):
    M.append({"id": id_, "part": part, "describes": describes, "file": file, "find": find, "replace": replace})
# ----- rules_78b.py -----
m("K4b-m-untuned-one-call", "PP2", "the untuned pod's E cap covers the S4 call only", R,
  "        upper = WIDE_CAP_FACTOR * (s3_call + s4_call)\n", "        upper = WIDE_CAP_FACTOR * s4_call\n")
m("K4b-m-untuned-s3-chunks", "PP2", "the S3 call counts one chunk fewer", R,
  "        s3_call = first + (s3_chunks - 1) * batch + ends\n", "        s3_call = first + (s3_chunks - 2) * batch + ends\n")
m("K4b-m-pins-rep-no-s3orig", "A13", "rep_pass no longer needs the s3_orig pool pin", R,
  '"rep_pass": ("RECIPE_S", "ANCHOR_BANK", "S3_ORIG_POOL"), ', '"rep_pass": ("RECIPE_S", "ANCHOR_BANK"), ')
m("K4b-m-pins-a1-no-unit", "A13", "a1_pass no longer needs the retrain unit pin", R,
  '    "a1_pass": ("RECIPE_S", "ANCHOR_BANK", "RETRAIN_UNIT"),\n', '    "a1_pass": ("RECIPE_S", "ANCHOR_BANK"),\n')
m("K4b-m-pins-o-only-none", "M1", "o_only needs no O-ext pin", R,
  '    "o_only": ("OEXT_78B",), "c0"', '    "o_only": (), "c0"')
m("K4b-m-pins-c0-no-source", "A13", "c0 needs no C0_SOURCE", R,
  '"c0": ("OEXT_78B", "C0_SOURCE"),', '"c0": ("OEXT_78B",),')
m("K4b-m-pins-l1-none", "A1", "l1_scan needs no anchor bank pin", R,
  '    "l1_scan": ("ANCHOR_BANK",), "classifier"', '    "l1_scan": (), "classifier"')
m("K4b-m-pins-y-no-engine-pin", "A13", "a job on engine Y needs no ENGINE_Y", R,
  '    return SC_KIND_PINS[kind] + (("ENGINE_Y",) if engine == "Y" else ())\n', '    return SC_KIND_PINS[kind]\n')
m("K4b-m-after-retrain-free", "A2", "the retrain needs no anchor job before it", R,
  '"retrain": ("anchor",), "a1_pass"', '"retrain": (), "a1_pass"')
m("K4b-m-after-a1-no-retrain", "A2", "A1's pass needs no retrain before it", R,
  '"a1_pass": ("anchor", "retrain")}', '"a1_pass": ("anchor",)}')
m("K4b-m-after-rep-no-untuned", "A2", "rep_pass needs no untuned pass before it", R,
  '"rep_pass": ("anchor", "untuned_answers"),', '"rep_pass": ("anchor",),')
m("K4b-m-order-off", "A2", "the order check never refuses", R,
  "    if before:\n        return (f\"{kind} comes after", "    if False:\n        return (f\"{kind} comes after")
m("K4b-m-engine-x-retrain-any", "ruling 10", "the X retrain needs no complete Y retrain", R,
  '    if kind == "retrain" and engine == "X" and "Y" not in tuple(retrain_engines):\n',
  '    if False and kind == "retrain" and engine == "X" and "Y" not in tuple(retrain_engines):\n')
m("K4b-m-engine-a1-any", "ruling 10, EYD:81", "A1's pass runs on any engine", R,
  '    if kind == "a1_pass" and engine not in tuple(retrain_engines):\n', '    if False:\n')
m("K4b-m-engine-x-only-off", "PP16", "the wrapper kinds run on Y at planning", R,
  '    if kind in X_ONLY_KINDS and engine != "X":\n        return f"{kind} runs on engine X only (PP4, PP16)"\n',
  '    if False:\n        return f"{kind} runs on engine X only (PP4, PP16)"\n')
m("K4b-m-recipe-s-disagree-ok", "A1", "the two RECIPE_S places may disagree", R,
  "    if layer != kit:\n        raise Refused(f\"recipe S_78 for {family}: rules_78b.RECIPE_S",
  "    if False:\n        raise Refused(f\"recipe S_78 for {family}: rules_78b.RECIPE_S")
m("K4b-m-engine-sha-y-null-ok", "A13", "engine Y's identity is returned while null", R,
  "        if ENGINE_Y is None or not isinstance(ENGINE_Y, str) or not CONFIG_SHA256.match(ENGINE_Y):\n",
  "        if False:\n")
m("K4b-m-state-kinds-no-regenerate", "PP14", "a regenerate pod keeps no states", R,
  '                  "regenerate": "keeps the regenerated a0 unit\'s e1 state (I: a train-only job like the retrain)"}',
  '                  }')
m("K4b-m-pod-keeps-states-always", "PP14", "every scorer pod is said to keep states", R,
  '"keeps_states": keeps is not None,', '"keeps_states": True,')
m("K4b-m-pod-need-no-contingency", "M3", "the pod's need alone without the contingency", R,
  '    pod["engine"] = engine\n    pod["need_usd_alone"] = funding_need_usd([[pod]], CONTINGENCY_FACTOR)["need_usd"]\n',
  '    pod["engine"] = engine\n    pod["need_usd_alone"] = funding_need_usd([[pod]], 1.0)["need_usd"]\n')
m("K4b-m-lines-no-idle", "PP14", "a scorer pod prints no idle-storage line", R,
  '            f"${pod[\'need_usd_alone\']:.2f}",\n            f"idle storage {host}',
  '            f"${pod[\'need_usd_alone\']:.2f}"] + [] and [\n            f"idle storage {host}')
# ----- stage1_rules.py -----
m("K4b-m-pin-wrapper", "item 3", "the wrapper's pin is another hash", S,
  '    WRAPPER: "108f44257cb967a3594e7a865879a668a3de830c4385b75bf50de1db29322fbf",',
  '    WRAPPER: "208f44257cb967a3594e7a865879a668a3de830c4385b75bf50de1db29322fbf",')
m("K4b-m-pin-s1common", "item 3", "s1common's pin is another hash", S,
  '    "scripts/stage1/s1common.py": "930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552",',
  '    "scripts/stage1/s1common.py": "030c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552",')
m("K4b-m-pin-lexicon-dropped", "item 3", "the lexicon the 1B scripts read is not packed", S,
  '    "scripts/stage1/lexicon/lexicon.json": "bbbc71e9eebb62876430ffb5e0f54113c3818984b8369924b7bd2212c4c1ca17",\n', '')
m("K4b-m-host-prefix", "item 2", "the scorer block's hosts take another prefix", S,
  '"sc": f"{FAMILY}-sc"} if FAMILY else {}', '"sc": f"{FAMILY}-scorer"} if FAMILY else {}')
m("K4b-m-l1-command-name", "item 1", "l1_scan's settings waits are read under another command name", S,
  '"l1_scan": "scan",', '"l1_scan": "l1_scan",')
m("K4b-m-settings-waits-skip", "A13", "a null settings pin is never reported", S,
  "            if node is None:\n                out.append((f\"{script}: {dotted}\"", "            if False:\n                out.append((f\"{script}: {dotted}\"")
m("K4b-m-input-s1-as-s3", "PP2", "the s1 loss input takes the s3_safe pin", S,
  '"loss:s1": (lists.get("s1") or {}).get("sha256"),', '"loss:s1": (lists.get("s3_safe") or {}).get("sha256"),')
m("K4b-m-code-anchor-none", "item 3", "the anchor job seals no script", S,
  '    if kind == "anchor":\n        return [ANCHOR_SCRIPT]\n', '    if kind == "anchor":\n        return []\n')
m("K4b-m-folder-input-none", "item 1", "the retrain unit is read as a file", S,
  'SC_FOLDER_INPUTS = frozenset({"retrain_unit"})', 'SC_FOLDER_INPUTS = frozenset()')
# ----- plan_tool.py -----
m("K4b-m-plan-order-off", "A2", "init never checks A2's order", P,
  "    problem = r78.sc_order_problem(kind, done)           # A2's order first, PP16, the pins (A13), then ruling 10\n",
  "    problem = None\n")
m("K4b-m-plan-pins-off", "A13", "init never checks the pins", P,
  "        r78.sc_pins_or_refuse(family, kind, engine, pins78)\n", "        pass\n")
m("K4b-m-plan-x-only-first-off", "PP16", "init checks the X-only rule after the pins", P,
  '    if kind in r78.X_ONLY_KINDS or engine not in ("X", "Y"):\n', '    if False:\n')
m("K4b-m-plan-engine-dyn-off", "ruling 10", "init never checks the retrain's and A1's engines", P,
  '    problem = r78.sc_engine_problem(kind, engine, engines_unit if kind == "a1_pass" else engines_all)\n',
  '    problem = None\n')
m("K4b-m-plan-a1-unit-any", "PP3", "A1's engine is any complete retrain's, whatever the unit pin", P,
  '    engines_unit = [j["engine"] for _, j in retrains if j.get("complete_sha256") == unit_pin]\n',
  '    engines_unit = [j["engine"] for _, j in retrains]\n')
m("K4b-m-plan-two-jobs", "KD6", "a scorer pod may hold two jobs", P,
  "            if not (isinstance(jobs, list) and len(jobs) == 1):\n", "            if not isinstance(jobs, list):\n")
m("K4b-m-plan-dup-ok", "A8", "a kind may be planned twice", P,
  '    if status not in ("absent", "crashed", "deferred", "not_started"):\n', "    if False:\n")
m("K4b-m-plan-settings-waits-off", "A13", "the scorer layer's settings waits are not read", P,
  "        if waits:\n            fail(f\"{where}: {kind}: the scorer layer's settings wait", "        if False:\n            fail(f\"{where}: {kind}: the scorer layer's settings wait")
m("K4b-m-plan-funding-below-ok", "M3", "a funding record below the part's need is accepted", P,
  '    funding = funding_record(args.funding, r78.SC_BLOCK)\n    if not funding["amount_usd"] >= need["need_usd"]:\n',
  '    funding = funding_record(args.funding, r78.SC_BLOCK)\n    if False:\n')
m("K4b-m-plan-part-start-off", "A2", "a new part's first launch is not marked", P,
  '**({"part_start": True} if k == 0 else {})})', '**({})})')
m("K4b-m-plan-block-copy-off", "KD7", "a copy plans another block than its own", P,
  "    if block != rules.KIT_BLOCK:                         # KD7: one block per working copy\n",
  "    if False:\n")
m("K4b-m-plan-unreleased-ok", "A2", "a new part is planned over an unreleased launch", P,
  '    elif b["released"] < len(b["launches"]):\n', '    elif False:\n')
m("K4b-m-release-recheck-off", "A13", "the release does not compare the pins with init's", P,
  '        if again["inputs"] != job["inputs"] or again.get("recipe_s78") != job.get("recipe_s78") or \\\n',
  '        if False and again["inputs"] != job["inputs"] or again.get("recipe_s78") != job.get("recipe_s78") or \\\n')
m("K4b-m-release-input-unpacked-ok", "item 3", "an input not packed at its pin is released", P,
  "            if rel is None or got != pin:\n", "            if False:\n")
m("K4b-m-release-code-unchecked", "item 3", "the packed scorer code is not checked at release", P,
  "            if files.get(rel) != pin:\n                fail(f\"{name}: the packed {rel} is not at its pin",
  "            if False:\n                fail(f\"{name}: the packed {rel} is not at its pin")
m("K4b-m-release-s78-config-unchecked", "A1", "the S_78 config's engine hash is not checked at release", P,
  "            if config != values[\"RECIPE_S\"]:\n                fail(f\"{s_path}: its config_sha256",
  "            if False:\n                fail(f\"{s_path}: its config_sha256")
m("K4b-m-release-s78-packed-unchecked", "A1", "the packed S_78 file is not checked at release", P,
  "            if files.get(s_path) != mac.sha(ENGINE_ROOT / s_path):\n", "            if False:\n")
m("K4b-m-done-wrapper-whole", "item 4", "record-done prints the whole wrapper summary", P,
  "            calls[pathlib.PurePosixPath(folder).name] = {k: got.get(k) for k in (\"exit_code\", \"fallback_fired\", \"kept\",\n",
  "            calls[pathlib.PurePosixPath(folder).name] = dict(got) or {k: got.get(k) for k in (\"exit_code\", \"fallback_fired\", \"kept\",\n")
m("K4b-m-done-no-sc-ok", "item 4", "a complete scorer job without the runner's record is accepted", P,
  "    if not isinstance(sc, dict) or sc.get(\"kind\") != job[\"kind\"]:\n", "    if False:\n")
m("K4b-m-done-hash-unchecked", "item 4", "a non-hash value is printed as a hash", P,
  "            if SHA_RE.fullmatch(str(sc[key])) is None:\n", "            if False:\n")
m("K4b-m-done-wrapper-types-unchecked", "item 4", "the wrapper summary's types are not checked at record-done", P,
  "            if not isinstance(got, dict) or type(got.get(\"exit_code\")) is not int or \\\n",
  "            if False and not isinstance(got, dict) or False and type(got.get(\"exit_code\")) is not int or False and \\\n")
# ----- pack_setup.py -----
m("K4b-m-pack-input-pin-unchecked", "item 3", "an input off its pin is packed", K,
  "        if digest != pins[name]:\n", "        if False:\n")
m("K4b-m-pack-null-pin-ok", "A13", "an input whose pin is null is packed", K,
  "        if pins[name] is None:\n", "        if False:\n")
m("K4b-m-pack-unknown-name-ok", "item 3", "an input of no scorer kind is packed", K,
  "        if name not in pins:\n", "        if False:\n")
m("K4b-m-pack-code-none", "item 3", "the scorer code is not packed", K,
  "    out = {rel: (ROOT / rel, pin) for rel, pin in sorted(rules.SCORER_PINS.items())}\n", "    out = {}\n")
m("K4b-m-pack-sc-off", "item 3", "the scorer block's pack carries no scorer part", K,
  "    if rules.KIT_BLOCK == r78.SC_BLOCK:                  # K4b: the scorer block's code, inputs and S_78 config\n",
  "    if False:\n")
m("K4b-m-pack-s78-config-unchecked", "A1", "the S_78 config is packed whatever its engine hash", K,
  "    if config != values[\"RECIPE_S\"]:\n        raise SystemExit(f\"{rel}: its config_sha256",
  "    if False:\n        raise SystemExit(f\"{rel}: its config_sha256")
m("K4b-m-pack-folder-complete-unchecked", "item 3", "a unit folder is packed whatever its COMPLETE.json", K,
  '            if not src.is_dir() or not (src / "COMPLETE.json").is_file() or sha(src / "COMPLETE.json") != digest:\n',
  '            if not src.is_dir():\n')
m("K4b-m-pack-code-bad-ok", "item 3", "the dry pack reports changed scorer code without refusing", K,
  "    if bad:\n        raise SystemExit(f\"{len(bad)} scorer file(s) missing", "    if False:\n        raise SystemExit(f\"{len(bad)} scorer file(s) missing")
# ----- job runner -----
m("K4b-m-runner-s4-exit3-crash", "Part 1 §10", "the S4 call's exit 3 is a crash", J,
  '        s4_few = kind == "untuned_answers" and name.endswith("-untuned-s4") and done.returncode == 3\n',
  "        s4_few = False\n")
m("K4b-m-runner-s3-exit3-ok", "PP2", "the S3 call's exit 3 is accepted too", J,
  '        s4_few = kind == "untuned_answers" and name.endswith("-untuned-s4") and done.returncode == 3\n',
  '        s4_few = kind == "untuned_answers" and done.returncode == 3\n')
m("K4b-m-runner-wrapper-exit-unchecked", "item 4", "the wrapper record's exit code is not compared with the step's", J,
  '            if got["exit_code"] != exits[', '            if False and got["exit_code"] != exits[')
m("K4b-m-runner-wrapper-type-unchecked", "item 4", "the wrapper record's counts are not type-checked", J,
  "        if out[key] is not None and type(out[key]) is not WRAPPER_RECORD_KEYS[key]:\n", "        if False:\n")
m("K4b-m-runner-top-dose-text", "item 4", "a top_dose that is not a dose name is recorded", J,
  '    if out["top_dose"] is not None and not (out["top_dose"].startswith("s4") and len(out["top_dose"]) <= 12\n',
  '    if False and not (out["top_dose"].startswith("s4") and len(out["top_dose"]) <= 12\n')
m("K4b-m-runner-record-kind-unchecked", "item 4", "any JSON is read as a wrapper record", J,
  '    if not isinstance(doc, dict) or doc.get("kind") != "scale78b scorer wrapper record":\n',
  "    if not isinstance(doc, dict):\n")
m("K4b-m-runner-input-pin-unchecked", "item 1", "an input off the plan's pin runs", J,
  "        if packed != pin:\n", "        if False:\n")
m("K4b-m-runner-s78-pin-unchecked", "A1", "a job's S_78 config is not compared with RECIPE_S", J,
  '    if s78.get("config_sha256") != pin or ((plan.get("recipes") or {}).get(path) or {}).get("config_sha256") != pin:\n',
  "    if False:\n")
m("K4b-m-runner-one-job-unchecked", "KD6", "a scorer pod with two jobs runs", J,
  '    if len(h["jobs"]) != 1:\n        raise Unrunnable(f"job {index} ({kind}): a scorer-block pod holds one job (KD6)")\n',
  '    if False:\n        raise Unrunnable(f"job {index} ({kind}): a scorer-block pod holds one job (KD6)")\n')
m("K4b-m-runner-s4-call-with-losses", "PP2", "the S4 call also takes a loss", J,
  '"--list", f"s4={ps(\'list:s4\')}", "--out"', '"--list", f"s4={ps(\'list:s4\')}", "--loss", f"s1={ps(\'loss:s1\')}", "--out"')
m("K4b-m-runner-classifier-main-recipe", "PP4", "the classifier runs under the main config", J,
  '[*wrap, "classifier", "--family", family, "--prepared", p, "--recipe", rec,',
  '[*wrap, "classifier", "--family", family, "--prepared", p, "--recipe", rules.REC,')
m("K4b-m-runner-a1-one-state", "PP3", "A1's pass reads the e1 state only", J,
  '*[a for c in ("q", "e1") for a in ("--a0-state", f"{c}={state}")]', '*[a for c in ("e1",) for a in ("--a0-state", f"{c}={state}")]')
m("K4b-m-runner-retrain-shared-registry", "ruling 10", "the retrain writes the arms' registry", J,
  'RETRAIN_ROOT, f"{RETRAIN_ROOT}/registry.jsonl",', 'RETRAIN_ROOT, f"{ROUND}/registry.jsonl",')
m("K4b-m-runner-sobs-after-scorer", "KD11", "a scorer job is read for s_obs", J,
  '        if result["status"] == "complete" and job["kind"] not in BLOCK0_KINDS:   # K4b: no s_obs after a scorer job\n',
  "        if False:\n")
m("K4b-m-runner-s3orig-missing-ok", "PP2", "an S3 call without its s3_orig pool is complete", J,
  '        if summary["s3_orig_pool_sha256"] is None:\n', "        if False:\n")
m("K4b-m-runner-route-off", "item 1", "a scorer-block job takes block 0's route", J,
  '    if plan["hosts"][host].get("block") == r78.SC_BLOCK:   # K4b: the scorer block\'s single-job pods\n',
  "    if False:\n")
m("K4b-m-runner-sealed-paths-off", "item 3", "a scorer job's code and inputs are not sealed paths", J,
  '    if job.get("kind") in r78.SC_KINDS and (h or {}).get("block") == r78.SC_BLOCK:   # K4b\n', "    if False:\n")
m("K4b-m-runner-key-main-recipe", "A1, PP4", "an S_78 job's key check reads the main config", J,
  '        key = (job.get("recipe_s78") or {}).get("config_sha256") if job.get("recipe") == "S" else recipe   # K4b (A1)\n',
  "        key = recipe\n")
m("K4b-m-runner-preflight-s78-unchecked", "A1", "the pod's S_78 config is not checked at the preflight", J,
  '                s78.get("config_sha256") == r78.RECIPE_S[family], "the S_78 config differs from its pin (A1)"\n',
  '                s78.get("config_sha256") == r78.RECIPE_S[family] or True, "the S_78 config differs from its pin (A1)"\n')
m("K4b-m-runner-engine-pin-any", "A13", "the host's engine identity is not checked", J,
  '    assert h["engine_sha256"] == engine_pin(h["engine"]), "the host\'s engine is not a pinned engine (G4)"\n',
  "    pass\n")
bad = []
for x in M:
    n = (kit / x["file"]).read_text().count(x["find"])
    if n != 1:
        bad.append((x["id"], n))
ids = [x["id"] for x in M]
assert len(ids) == len(set(ids))
print("mutants", len(M), "bad", bad)
spec = {"kind": "stage1-78b scorer-block mutation spec (K4b)",
        "note": "each mutant's find text occurs exactly once in its file; runner: tests/run_mutants_scorer_78b.py (test_scorer_block_78b.py)",
        "mutants": M}
if not bad:
    (kit / "tests" / "mutation_spec_scorer_78b.json").write_text(json.dumps(spec, indent=1) + "\n")
