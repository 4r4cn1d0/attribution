import datetime as dt, hashlib, json, pathlib, subprocess, sys
root, kit, py, out, anchor1 = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3], pathlib.Path(sys.argv[4]), sys.argv[5]
named = [pathlib.Path(x) if pathlib.Path(x).is_absolute() else root / x for x in sys.argv[6:]]
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
git = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=True).stdout.strip()
tracked = [q.relative_to(root).as_posix() for q in named if not q.relative_to(root).as_posix().startswith("tmp/")]
if git("status", "--porcelain", "--", "scripts", "runkit", "experiments/safety_selection", *tracked):
    sys.exit("refused: a pinned path has an uncommitted change; commit it first (explicit paths)")
files = {}
for d in ("scripts/stage1_s1/reading", "scripts/stage1_s1/reading_input", "scripts/stage1_s1/reading_extra",
          "scripts/stage1_s1/hlc_draw"):
    for q in sorted((root / d).glob("*.py")):
        files[q.relative_to(root).as_posix()] = sha(q)
for rel in ("scripts/stage1_s1/reading/settings/reading.json", "scripts/stage1_s1/hlc_draw/settings/hlc_draw.json",
            "scripts/stage1_s1/overlap_strata.py", "scripts/stage1_s1/settings/overlap_strata.json",
            "scripts/stage1_s1/overlap_inputs.py", "scripts/stage1_s1/overlap_inputs_check.py",
            "scripts/stage1_s1/overlap_similarity.py", "scripts/stage1_s1/settings/overlap_similarity.json",
            "runkit/stage1-olmo/stage1_rules.py", "runkit/stage1-olmo/seal.py", "runkit/stage1-olmo/plan_tool.py",
            "runkit/stage1-olmo/judge_units_stage1.py", "scripts/family_probe_reading.py",
            "scripts/killtest_stage0_reading.py", "scripts/stage1/limits/limits_common.py", "scripts/stage1/s1common.py",
            "experiments/safety_selection/configs/family-probe-reading-amended-20261008.json",
            "scripts/stage1_s1/reading/mutation/mutants_b16.json", "scripts/stage1_s1/reading/mutation/run_mutants.py",
            "scripts/stage1_s1/reading_input/mutation/mutants_reading_input.json",
            "scripts/stage1_s1/reading_input/mutation/run_mutants.py",
            "scripts/stage1_s1/reading_extra/mutation/mutants_reading_extra.json",
            "scripts/stage1_s1/reading_extra/mutation/run_mutants.py",
            "scripts/stage1_s1/hlc_draw/mutation/mutants_hlc_draw.json", "scripts/stage1_s1/hlc_draw/mutation/run_mutants.py",
            "scripts/stage1_s1/mutation/mutants_b14.json", "runkit/stage1-olmo/tests/mutants_b15.json"):
    files[rel] = sha(root / rel)
for name in ("stage1_rules.py", "seal.py", "plan_tool.py", "judge_units_stage1.py"):
    files[f"tmp/stage1-olmo/{name}"] = sha(kit / name)
for q in named:
    files[q.relative_to(root).as_posix()] = sha(q)
trees = {t: git("rev-parse", f"HEAD:{t}") for t in ("scripts/stage1_s1", "scripts/stage1_s1/reading",
         "scripts/stage1_s1/reading_input", "scripts/stage1_s1/reading_extra", "scripts/stage1_s1/hlc_draw",
         "runkit/stage1-olmo", "scripts/stage1", "scripts/gate_b_mac_judges", "experiments/safety_selection")}
ver = subprocess.run([py, "-I", "-B", "-c", "import platform, numpy; print(platform.python_version(), numpy.__version__)"],
                     capture_output=True, text=True, check=True).stdout.split()
doc = {"kind": "stage1 outside time stamp manifest: the reading code and runbook (OpenTimestamps)", "version": 2,
       "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
       "git": {"head": git("rev-parse", "HEAD"), "trees": trees}, "files": files,
       "kit": {"plan_json_sha256": sha(kit / "plan.json"), "seal_A": sha(kit / "seals" / "block-A.json"),
               "seal_B": sha(kit / "seals" / "block-B.json")},
       "python": {"executable": py, "python": ver[0], "numpy": ver[1]},
       "first_stamp": {"manifest_sha256": "68e75447f7eca032039274bd64641d00625e70ca525f3131a2975c5aad0898c7",
                       "anchor": anchor1}}
with open(out, "x") as handle:
    handle.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
print(json.dumps({"written": str(out), "sha256": sha(out), "files": len(files), "head": doc["git"]["head"]}, sort_keys=True))
