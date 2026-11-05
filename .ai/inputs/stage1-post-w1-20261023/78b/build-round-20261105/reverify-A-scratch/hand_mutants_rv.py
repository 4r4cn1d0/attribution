"""Re-verifier's hand mutants on the FIX ROUND's changed code (none is in the fixer's spec). Copies the kit into a
scratch repo (symlinks for everything else), applies ONE replacement to the COPY, runs the fixer's suite there,
restores, re-hashes. The worktree is never written. Killed = pytest exit 1 with FAILED and no ERROR; survived =
exit 0; else invalid."""
import hashlib, json, os, pathlib, shutil, subprocess, sys

WS = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-a")
SCR = pathlib.Path(sys.argv[1])
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
KIT_REL = pathlib.Path("runkit/stage1-78b")
R, D = "rules_78b.py", "derive_78b_basis.py"

MUTANTS = [
    # ---- A-V1: batch_count / the drift refusal in s_obs_from_progress
    ("RV1-batch-count-bool-ok", R, "    if isinstance(value, bool) or type(value) is not int or value < 0:\n",
     "    if type(value) is not int or value < 0:\n"),
    ("RV1-batch-count-float-ok", R, "    if isinstance(value, bool) or type(value) is not int or value < 0:\n",
     "    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:\n"),
    ("RV1-batch-count-neg-ok", R, "    if isinstance(value, bool) or type(value) is not int or value < 0:\n",
     "    if isinstance(value, bool) or type(value) is not int or value < -1:\n"),
    ("RV1-s-obs-checks-rows-only", R, "    for row in rows:\n        batch_count(row, \"capped\")\n        batch_count(row, \"rows\")\n",
     "    for row in rows:\n        batch_count(row, \"rows\")\n"),
    ("RV1-s-obs-checks-later-rows-only", R, "    for row in rows:\n        batch_count(row, \"capped\")\n        batch_count(row, \"rows\")\n",
     "    for row in rows[1:]:\n        batch_count(row, \"capped\")\n        batch_count(row, \"rows\")\n"),
    # ---- A-V2: the 32-row clause
    ("RV2-rows-filter-ge-20", R, "        if row[\"capped\"] > 0 and row[\"rows\"] == GENERATION_BATCH:\n",
     "        if row[\"capped\"] > 0 and row[\"rows\"] >= 20:\n"),
    ("RV2-uncapped-32-rows-count", R, "        if row[\"capped\"] > 0 and row[\"rows\"] == GENERATION_BATCH:\n",
     "        if row[\"capped\"] >= 0 and row[\"rows\"] == GENERATION_BATCH:\n"),
    # ---- A-V3: check_keys (manifest, bank, kind)
    ("RV3-bank-float-ok", R, "        if type(bank[key]) is not int or bank[key] != value:\n",
     "        if not isinstance(bank[key], (int, float)) or bank[key] != value:\n"),
    ("RV3-manifest-case-insensitive", R, "    if manifest_sha256 != MANIFESTS[family]:\n",
     "    if str(manifest_sha256).strip().lower() != MANIFESTS[family]:\n"),
    ("RV3-kind-unchecked", R, "    family_of(family)\n    check_kind(kind)\n    if kind in S78_KINDS:\n",
     "    family_of(family)\n    if kind in S78_KINDS:\n"),
    ("RV3-arm-passes-under-s78", R, "    elif recipe_sha256 not in RECIPE_ALLOW[family]:\n",
     "    elif recipe_sha256 not in RECIPE_ALLOW[family] and recipe_sha256 != RECIPE_S.get(family):\n"),
    ("RV3-s78-kind-also-needs-allowlist", R, "    elif recipe_sha256 not in RECIPE_ALLOW[family]:\n",
     "    if recipe_sha256 not in RECIPE_ALLOW[family]:\n"),
    ("RV3-bank-subset-ok", R, "    if not isinstance(bank, dict) or set(bank) != set(BANK):\n",
     "    if not isinstance(bank, dict) or not set(bank) <= set(BANK):\n"),
    # ---- A-V4: launch_allowed
    ("RV4-launch-cap-price-unchecked", R, "    need = Decimal(repr(cents(finite(cap_h) * finite(price))))\n",
     "    need = Decimal(repr(cents(cap_h * price)))\n"),
    ("RV4-launch-returns-false", R, "    free = Decimal(repr(cents(finite(free_after_commitments_usd))))\n",
     "    try:\n        finite(free_after_commitments_usd); finite(cap_h); finite(price)\n    except Refused:\n        return False\n    free = Decimal(repr(cents(finite(free_after_commitments_usd))))\n"),
    # ---- A-V5: test 3's binding assertion (a code change it must catch)
    ("RV5-allcapped-first-plus-slow", D, "    first = max(unit[\"first_greedy_batch_s\"], slow)\n",
     "    first = unit[\"first_greedy_batch_s\"] + slow\n"),
    ("RV5-allcapped-outside-twice", D, "            + unit[\"outside_s\"])\n", "            + 2 * unit[\"outside_s\"])\n"),
    # ---- A-V6: check_path / in_place
    ("RV6-inplace-host-anywhere", D, "        return len(parents) >= 2 and parents[1] == \"hosts\"\n",
     "        return \"hosts\" in parents\n"),
    ("RV6-inplace-tree-anywhere", D, "        return len(parents) >= 3 and parents[0] == \"tree\" and parents[2] == \"retrieved\"\n",
     "        return \"tree\" in parents\n"),
    ("RV6-inplace-unit-round1-only", D,
     "        return len(parents) >= 5 and parents[1] == \"round1\" and parents[2] == \"tree\" and parents[4] == \"retrieved\"\n",
     "        return len(parents) >= 2 and parents[1] == \"round1\"\n"),
    ("RV6-inplace-no-place-true", D, "    return False\n\n\ndef check_path", "    return True\n\n\ndef check_path"),
    ("RV6-forbidden-parent-only", D, "    if any(part in FORBIDDEN_PARTS for part in path.parts):\n",
     "    if path.parent.name in FORBIDDEN_PARTS:\n"),
    ("RV6-forbidden-drops-units", D, "                             \"states\", \"judges\", \"seals\", \"units\"})",
     "                             \"states\", \"judges\", \"seals\"})"),
    ("RV6-open-record-skips-gate", D, "    path = check_path(path)\n    with open(path", "    path = pathlib.Path(path)\n    with open(path"),
    # ---- addendum A1: RECIPE_S
    ("RVA1-regex-upper-ok", R, "CONFIG_SHA256 = re.compile(r\"^[0-9a-f]{64}$\")", "CONFIG_SHA256 = re.compile(r\"^[0-9a-fA-F]{64}$\")"),
    ("RVA1-pin-shape-unchecked", R, "    if not isinstance(value, str) or not CONFIG_SHA256.match(value):\n", "    if False:\n"),
    ("RVA1-job-decision-gate-off", R, "    if job[\"kind\"] in S78_KINDS:\n        recipe_s_or_refuse(family)\n", "    pass\n"),
    ("RVA1-job-decision-retrain-only", R, "    if job[\"kind\"] in S78_KINDS:\n        recipe_s_or_refuse(family)\n",
     "    if job[\"kind\"] == \"retrain\":\n        recipe_s_or_refuse(family)\n"),
    ("RVA1-s78-kinds-retrain-only", R, "S78_KINDS = frozenset({\"retrain\", \"rep_pass\"})", "S78_KINDS = frozenset({\"retrain\"})"),
    ("RVA1-recipe-s-other-family", R, "    value = RECIPE_S[family]\n", "    value = RECIPE_S[family] or RECIPE_S[[f for f in RECIPE_S if f != family][0]]\n"),
    # ---- the T4 interface: preflight_fields / job_decision / pod_dry_run
    ("RVT4-cp-default-block", R, "    cap_projection = verification.get(\"cap_projection\")\n",
     "    cap_projection = verification.get(\"cap_projection\") or {\"untuned_projected_s\": 3600.0, \"training_s\": preflight_done.get(\"training_s\")}\n"),
    ("RVT4-ms-fallback-to-verification", R, "           \"ms_per_step_full\": finite(preflight_done.get(\"ms_per_step_full\")),\n",
     "           \"ms_per_step_full\": finite(preflight_done.get(\"ms_per_step_full\", (verification.get(\"full_length\") or {}).get(\"ms_per_step_full\"))),\n"),
    ("RVT4-training-fallback-to-cp", R, "    out = {\"training_s\": finite(preflight_done.get(\"training_s\")),\n",
     "    out = {\"training_s\": finite(preflight_done.get(\"training_s\", cap_projection.get(\"training_s\"))),\n"),
    ("RVT4-isclose-2pct", R, "rel_tol=1e-9, abs_tol=1e-6):\n", "rel_tol=0.02, abs_tol=1e-6):\n"),
    ("RVT4-preflight-done-list-ok", R, "    if not isinstance(preflight_done, dict):\n        raise Refused(\"no PREFLIGHT-DONE record\")\n",
     "    if not isinstance(preflight_done, (dict, list, str, float)):\n        raise Refused(\"no PREFLIGHT-DONE record\")\n    if not isinstance(preflight_done, dict):\n        preflight_done = {\"training_s\": TRAINING_FALLBACK, \"ms_per_step_full\": 1.0} if False else {}\n"),
    ("RVT4-dry-run-decrements-upper-s", R, "            left = left - job[\"measured_upper_s\"]\n", "            left = left - job[\"upper_s\"]\n"),
    ("RVT4-dry-run-no-cascade", R, "        if deferred:\n            d.update(action=\"defer\", reason=d[\"reason\"] or \"earlier job deferred\")\n", "        pass\n"),
    ("RVT4-free-space-before-fields", R, "    fields = preflight_fields(preflight_done, verification)\n    s_pod = speed_factor(family, fields)\n    if not free_space_ok(free_gb):\n",
     "    if not free_space_ok(free_gb):\n        raise Refused(\"free\")\n    fields = preflight_fields(preflight_done, verification)\n    s_pod = speed_factor(family, fields)\n    if False:\n"),
    ("RVT4-s-obs-defer-ignores-unmeasured", R, "    if s_obs_defers(s_obs):\n", "    if s_obs_defers(s_obs) and not job[\"unmeasured\"]:\n"),
    ("RVT4-decision-s-min", R, "            \"s\": max(1.0, s_pod, float(s_obs)), \"remaining_s\": remaining_s}\n",
     "            \"s\": max(1.0, s_pod), \"remaining_s\": remaining_s}\n"),
    # ---- round-1 behaviour the fix must not have moved (sanity)
    ("RVR-e-cap-retrain-2h", R, "        upper = 3.0 * 3600\n", "        upper = 2.0 * 3600\n"),
    ("RVR-counted-kinds-drop-a0", R, "COUNTED_KINDS = frozenset({\"arm\", \"a0_arm\", \"evalonly\",", "COUNTED_KINDS = frozenset({\"arm\", \"evalonly\","),
    ("RVR-block0-llama-3-arms", R, "    llama = arm_pod(\"llama31-8b\", [33, 33, 33, 38], [\"arm\", \"arm\", \"arm\", \"a0_arm\"])\n",
     "    llama = arm_pod(\"llama31-8b\", [33, 33, 38], [\"arm\", \"arm\", \"a0_arm\"])\n"),
]


def prepare():
    if SCR.exists():
        raise SystemExit("scratch exists")
    repo = SCR / "repo"
    (repo / "runkit").mkdir(parents=True)
    for e in sorted(WS.iterdir()):
        if e.name not in ("runkit", ".git"):
            (repo / e.name).symlink_to(e.resolve())
    for e in sorted((WS / "runkit").iterdir()):
        if e.name == KIT_REL.name:
            shutil.copytree(e, repo / "runkit" / e.name, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        else:
            (repo / "runkit" / e.name).symlink_to(e.resolve())
    return repo


def run(repo, n):
    cmd = [PY, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfE", "--basetemp", str(SCR / f"pt-{n}"),
           str(KIT_REL / "tests" / "test_rules_78b.py")]
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    d = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=600)
    shutil.rmtree(SCR / f"pt-{n}", ignore_errors=True)
    lines = (d.stdout + d.stderr).splitlines()
    failed = [x[len("FAILED "):].split(" - ")[0].split("::")[-1] for x in lines if x.startswith("FAILED ")]
    errors = [x for x in lines if x.startswith("ERROR ")]
    tail = [x for x in lines if x.strip()][-1:] or [""]
    return d.returncode, failed, len(errors), tail[0][-160:]


def main():
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (WS / KIT_REL).rglob("*") if p.is_file()}
    repo = prepare()
    kit = repo / KIT_REL
    code, failed, errs, tail = run(repo, 0)
    print(json.dumps({"baseline": {"exit": code, "tail": tail}}))
    if code != 0:
        return 2
    results = []
    for n, (mid, fname, find, repl) in enumerate(MUTANTS, start=1):
        target = kit / fname
        orig = target.read_bytes()
        text = orig.decode()
        if text.count(find) != 1:
            results.append({"id": mid, "verdict": "invalid", "reason": f"find occurs {text.count(find)}x"})
            print(json.dumps(results[-1])); continue
        target.write_bytes(text.replace(find, repl).encode())
        code, failed, errs, tail = run(repo, n)
        target.write_bytes(orig)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == hashlib.sha256(orig).hexdigest()
        v = "killed" if (code == 1 and failed and not errs) else "survived" if code == 0 else "invalid"
        results.append({"id": mid, "file": fname, "verdict": v, "exit": code, "failed": failed[:8], "errors": errs, "tail": tail})
        print(json.dumps(results[-1]))
    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (WS / KIT_REL).rglob("*") if p.is_file()}
    print(json.dumps({"counts": counts, "worktree_kit_unchanged": before == after}))
    (SCR / "hand-mutants-rv.json").write_text(json.dumps({"counts": counts, "worktree_kit_unchanged": before == after,
                                                           "results": results}, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
