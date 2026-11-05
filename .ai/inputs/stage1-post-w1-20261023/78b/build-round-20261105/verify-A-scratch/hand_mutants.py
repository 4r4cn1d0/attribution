"""Verifier's hand mutants: copy the builder's kit into a scratch repo (symlinks for everything else), apply ONE
text replacement to the COPY, run the builder's suite there, restore. The builder's files are never touched. Mutants
include ones NOT in the builder's spec, to probe whether the tests can fail. Killed = pytest exit 1 with FAILED and no
ERROR; survived = exit 0; else invalid."""
import hashlib, json, os, pathlib, shutil, subprocess, sys

WS = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-a")
SCR = pathlib.Path(sys.argv[1])
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
KIT_REL = pathlib.Path("runkit/stage1-78b")

MUTANTS = [
    # id, file, find, replace, in_builder_spec
    ("V-cents-half-even", "rules_78b.py", "rounding=ROUND_HALF_UP)", "rounding=ROUND_HALF_EVEN)", False),
    ("V-j-lt-k-minus-1", "rules_78b.py", 'for j in jobs[:k]) + need[k]', 'for j in jobs[:max(k - 1, 0)]) + need[k]', False),
    ("V-first-min", "rules_78b.py", 'return max(c["FIRST_BATCH_MAX_S"], c["BATCH_MAX_S"]) + (BATCHES - 1)', 'return min(c["FIRST_BATCH_MAX_S"], c["BATCH_MAX_S"]) + (BATCHES - 1)', False),
    ("V-finite-no-isfinite", "rules_78b.py", "or not math.isfinite(value):\n        raise Refused(f\"a required field", "or False:\n        raise Refused(f\"a required field", False),
    ("V-speed-zero-passes", "rules_78b.py", "if training_s <= 0 or ms_full <= 0:", "if training_s < 0 or ms_full < 0:", False),
    ("V-sobs-rows-filter-off", "rules_78b.py", 'and int(row.get("rows", 0)) == GENERATION_BATCH:', 'and True:', False),
    ("V-start-margin-1700", "rules_78b.py", "START_MARGIN_S = 1800 ", "START_MARGIN_S = 1700 ", False),
    ("V-margin-1.14", "rules_78b.py", "MEASURED_MARGIN = 1.15 ", "MEASURED_MARGIN = 1.14 ", False),
    ("V-score-1240", "rules_78b.py", "SCORE_ALLCAP_S = 1250.0 ", "SCORE_ALLCAP_S = 1240.0 ", False),
    ("V-batches-minus-2", "rules_78b.py", "+ (BATCHES - 1) * c[\"BATCH_MAX_S\"]", "+ (BATCHES - 2) * c[\"BATCH_MAX_S\"]", False),
    ("V-floor-ignored", "rules_78b.py", "        need = max(need, sanity_floor_s(family, preflight, steps, kind))\n", "        need = need\n", False),
    ("V-launch-strict", "rules_78b.py", "    return free - need >= floor\n", "    return free - need > floor\n", False),
    ("V-dryrun-no-decrement", "rules_78b.py", '            left = left - job["measured_upper_s"]\n', '            left = left\n', False),
    ("V-gpu-strip", "rules_78b.py", "    if gpu_name != GPU_NAME:\n", "    if str(gpu_name).strip() != GPU_NAME:\n", False),
    ("V-max-arms-allow-5", "rules_78b.py", "    if arm_count(jobs) > MAX_ARMS_PER_POD_78B:\n", "    if arm_count(jobs) > MAX_ARMS_PER_POD_78B + 1:\n", False),
    ("V-sobs-default-not-1", "rules_78b.py", '    return max(1.0, slowest / f["BATCH_MAX_S"])\n', '    return slowest / f["BATCH_MAX_S"]\n', False),
    ("V-e-cap-no-overhead", "rules_78b.py", "    return hours(round_up_s(POD_OVERHEAD_S + e_upper_s(family, kind, n_points)[\"upper_s\"] + START_MARGIN_S))\n", "    return hours(round_up_s(e_upper_s(family, kind, n_points)[\"upper_s\"] + START_MARGIN_S))\n", False),
    ("V-hold-reason-changed", "rules_78b.py", "its last judge pods deleted 31 Oct\")", "its last judge pods deleted 30 Oct\")", False),
    ("V-derive-sampled-dropped", "derive_78b_basis.py", 'capped32 = [b for b in greedy[1:] + sampled if', 'capped32 = [b for b in greedy[1:] if', False),
    ("V-derive-outside-no-other", "derive_78b_basis.py", '"outside_s": round(outer_s - ledger["sum_stage_s"] - other_stage_s, 3),', '"outside_s": round(outer_s - ledger["sum_stage_s"], 3),', False),
    # the builder's own spec entries, re-run by hand
    ("B-j-le-k", "rules_78b.py", 'for j in jobs[:k]) + need[k]', 'for j in jobs[:k + 1]) + need[k]', True),
    ("B-round-down", "rules_78b.py", "    return math.ceil(round(seconds, 6) / CAP_STEP_S) * CAP_STEP_S\n", "    return math.floor(round(seconds, 6) / CAP_STEP_S) * CAP_STEP_S\n", True),
    ("B-s-pod-only", "rules_78b.py", "    s = max(1.0, finite(s_pod), finite(s_obs))\n", "    s = max(1.0, finite(s_pod))\n", True),
    ("B-overhead-42", "rules_78b.py", "POD_OVERHEAD_S = 48 * 60 ", "POD_OVERHEAD_S = 42 * 60 ", True),
    ("B-33-batches", "rules_78b.py", "BATCHES = GREEDY_BATCHES + SAMPLED_BATCHES", "BATCHES = GREEDY_BATCHES + SAMPLED_BATCHES - 1", True),
    ("B-pin-ignored", "rules_78b.py", "    if digest != BASIS_SHA256:\n", "    if False and digest != BASIS_SHA256:\n", True),
    ("B-derive-outside-ledger-end", "derive_78b_basis.py", '        "outside_s": round(outer_s - ledger["sum_stage_s"] - other_stage_s, 3),\n', '        "outside_s": round(outer_s - ledger["ledger_end_s"] - other_stage_s, 3),\n', True),
    ("B-derive-allowlist-off", "derive_78b_basis.py", '    if path.name not in ALLOWED_NAMES and not (path.name.startswith("create-") and path.suffix == ".json"):\n', "    if False:\n", True),
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
            shutil.copytree(e, repo / "runkit" / e.name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            (repo / "runkit" / e.name).symlink_to(e.resolve())
    return repo


def run(repo, n):
    cmd = [PY, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfE", "--basetemp", str(SCR / f"pt-{n}"),
           str(KIT_REL / "tests" / "test_rules_78b.py")]
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    d = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=600)
    shutil.rmtree(SCR / f"pt-{n}", ignore_errors=True)
    lines = (d.stdout + d.stderr).splitlines()
    failed = [x[len("FAILED "):].split(" - ")[0].split("::")[-1] for x in lines if x.startswith("FAILED ")]
    errors = [x for x in lines if x.startswith("ERROR ")]
    tail = [x for x in lines if x.strip()][-1:] or [""]
    return d.returncode, failed, len(errors), tail[0][-120:]


def main():
    repo = prepare()
    kit = repo / KIT_REL
    code, failed, errs, tail = run(repo, 0)
    print(json.dumps({"baseline": {"exit": code, "tail": tail}}))
    if code != 0:
        return 2
    results = []
    for n, (mid, fname, find, repl, in_spec) in enumerate(MUTANTS, start=1):
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
        results.append({"id": mid, "in_builder_spec": in_spec, "verdict": v, "exit": code, "failed": failed[:6], "errors": errs, "tail": tail})
        print(json.dumps(results[-1]))
    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(json.dumps({"counts": counts}))
    (SCR / "hand-mutants.json").write_text(json.dumps(results, indent=1) + "\n")
    # the builder's kit in the worktree is unchanged (hash check against the copy's restored bytes is above; here the originals)
    return 0


if __name__ == "__main__":
    sys.exit(main())
