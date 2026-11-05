"""Verifier's mutation harness: copies the builder's scripts/scale78b into a scratch root (frozen readers, the
engine and the research records reached by symlink), applies one replacement at a time and runs the relevant tests.
A mutant is KILLED when pytest exits non-zero. Never touches the builder's workspace."""
import pathlib, re, shutil, subprocess, sys
S = pathlib.Path(__file__).resolve().parent
MUT = S / "mut"
WS = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-c")
MAINCK = pathlib.Path("/Users/spiderishi/Coding/attribution")
PY_MAIN = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
PY_SCI = "/Users/spiderishi/Coding/attribution/.venv/bin/python"
PKG = MUT / "scripts/scale78b"


def setup():
    if MUT.exists():
        shutil.rmtree(MUT)
    (MUT / "scripts").mkdir(parents=True)
    for name in ("gate_b_reading.py", "family_probe_reading.py", "killtest_stage0_reading.py"):
        (MUT / "scripts" / name).symlink_to(MAINCK / "scripts" / name)
    (MUT / "experiments").symlink_to(WS / "experiments")
    (MUT / "research").symlink_to(WS / "research")


def clean():
    if PKG.exists():
        shutil.rmtree(PKG)
    shutil.copytree(WS / "scripts/scale78b", PKG, ignore=shutil.ignore_patterns("__pycache__"))


def run(py, tests):
    cmd = [py, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-x", "-q"] + [str(PKG / "tests" / t) for t in tests]
    r = subprocess.run(cmd, cwd=str(MUT), capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(S)})
    last = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-1:] or [""]
    return r.returncode, last[0][:160]


NOISE = (PY_SCI, ["test_noise_reading.py", "test_g1_check_78b.py"])
MAKER = (PY_MAIN, ["test_make_recipe_s78.py"])
MUTANTS = [
    ("N1 threshold A exclusive (<)", "noise_reading.py", "    if GB.ge(ex(THRESHOLD_A_PP), 1, sigma):", "    if GB.gt(ex(THRESHOLD_A_PP), 1, sigma):", NOISE),
    ("N2 threshold B9 exclusive (<)", "noise_reading.py", "    elif GB.ge(ex(THRESHOLD_B9_PP), 1, sigma):", "    elif GB.gt(ex(THRESHOLD_B9_PP), 1, sigma):", NOISE),
    ("N3 review sign flipped", "noise_reading.py", "    review = not GB.ge(ex(CEILING_SIGMA_PP[plan]), 1, sigma)", "    review = GB.ge(ex(CEILING_SIGMA_PP[plan]), 1, sigma)", NOISE),
    ("N4 pooled divisor 2k -> k", "noise_reading.py", 'p_pool = sum((2 * e["sdr2"] for e in exact), Fraction(0)) / (2 * k)', 'p_pool = sum((2 * e["sdr2"] for e in exact), Fraction(0)) / k', NOISE),
    ("N5 pooled median over the first pair only", "noise_reading.py", "    median = GB.median_term(se2s)", "    median = GB.median_term(se2s[:1])", NOISE),
    ("N6 s_arm sum of squares with n not n-1", "noise_reading.py", 'arm_ss = {role: GB.variance(vs) * (len(vs) - 1) for role, vs in u_of.items()}', 'arm_ss = {role: GB.variance(vs) * len(vs) for role, vs in u_of.items()}', NOISE),
    ("N7 training-identity refusal removed", "noise_reading.py", '        if rec.get("training_identity") != fam["training_identity"]:', '        if False:', NOISE),
    ("N8a R provenance: family check removed", "noise_reading.py", 'or doc.get("manifest_sha256") != fam["manifest_sha256"] or selection.get("family") != "R" \\', 'or doc.get("manifest_sha256") != fam["manifest_sha256"] or False \\', NOISE),
    ("N8b R provenance: family and draw checks removed", "noise_reading.py", 'or selection.get("draw") != seed - R_SEED_BASE:', 'or False:', NOISE),
    ("N9 MDE factor H 0.9340 -> 0.9000", "noise_reading.py", '"H": "0.9340"}', '"H": "0.9000"}', NOISE),
    ("N10 chi2 closed form off by one term", "noise_reading.py", "    for i in range(df // 2):", "    for i in range(df // 2 + 1):", NOISE),
    ("N11 sigma_F df 2 -> 3", "noise_reading.py", '"sigma_F_df": 2,', '"sigma_F_df": 3,', NOISE),
    ("N12 pooled df 2k -> k", "noise_reading.py", '"k": k, "df": 2 * k,', '"k": k, "df": k,', NOISE),
    ("N13 fingerprint trigger dropped", "noise_reading.py", '    fallback = environment or fingerprint == "differs"', '    fallback = environment', NOISE),
    ("N14 governing reading always plain", "noise_reading.py", '    governing = "fallback" if fallback else "plain"', '    governing = "plain"', NOISE),
    ("N15 fresh-R (no resume) check removed", "noise_reading.py", '    if role == "R" and job.get("resume_from") is not None:', '    if False:', NOISE),
    ("N16 seed check removed", "noise_reading.py", '    if not GB.is_int(job.get("seed")) or job.get("seed") != seed:', '    if False:', NOISE),
    ("N17 parity family pooled with a tier family allowed", "noise_reading.py", '    if tier and parity:', '    if False:', NOISE),
    ("G1 TOO CLOSE counted as a G1 pass", "g1_check_78b.py", '"G1": "pass" if status == FR.PASS else "fail",', '"G1": "pass" if status in (FR.PASS, FR.TOO_CLOSE) else "fail",', NOISE),
    ("G2 manifest check removed (g1 check)", "g1_check_78b.py", '    if ident.get("manifest_sha256") != NR.FAMILIES[family]["manifest_sha256"]:', '    if False:', NOISE),
    ("G3 training-identity check removed (g1 check)", "g1_check_78b.py", '    if ident.get("training_identity") != want or (marker.get("identity") or {}).get("training_identity") != want:', '    if False:', NOISE),
    ("K1 checkpoints [q, e1, e3]", "make_recipe_s78.py", 'RECIPE_S_CHECKPOINTS = ["q", "e1"]', 'RECIPE_S_CHECKPOINTS = ["q", "e1", "e3"]', MAKER),
    ("K2 query_bank prefix anchor-", "make_recipe_s78.py", 'out["attribution"]["query_bank"] = f"anchors-{anchors_sha256}"', 'out["attribution"]["query_bank"] = f"anchor-{anchors_sha256}"', MAKER),
    ("K3 name unchanged", "make_recipe_s78.py", '    out["name"] = s78_name(main["name"], date)', '    out["name"] = main["name"]', MAKER),
    ("K4 main-config hash pin not checked", "make_recipe_s78.py", '    if config_sha256(main) != pin["config_sha256"]:', '    if False:', MAKER),
    ("K5 field-set check removed", "make_recipe_s78.py", '    if diff_paths(main, out) != set(RECIPE_S_FIELDS):', '    if False:', MAKER),
    ("K6 hex check accepts upper case", "make_recipe_s78.py", 'if not re.fullmatch(r"[0-9a-f]{64}", anchors_sha256 or ""):', 'if not re.fullmatch(r"[0-9a-fA-F]{64}", anchors_sha256 or ""):', MAKER),
]

setup()
clean()
print("BASELINE noise/g1 (.venv):", run(*NOISE))
print("BASELINE maker (main venv):", run(*MAKER))
results = []
for label, fname, old, new, (py, tests) in MUTANTS:
    clean()
    path = PKG / fname
    text = path.read_text(encoding="utf-8")
    n = text.count(old)
    if n != 1:
        results.append((label, "PATTERN x%d (not applied)" % n, ""))
        continue
    path.write_text(text.replace(old, new), encoding="utf-8")
    code, last = run(py, tests)
    results.append((label, "KILLED" if code != 0 else "SURVIVED", last))
clean()
for label, status, last in results:
    print(f"{status:10s} {label:55s} | {last}")
shutil.rmtree(MUT)
