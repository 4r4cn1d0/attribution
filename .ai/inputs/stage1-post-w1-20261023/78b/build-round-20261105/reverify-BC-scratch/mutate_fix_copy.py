"""Fix-round mutation check (the verifier's N4, N5, N6, N15, N17 and the D4 reorder), the verifier's harness form:
a scratch root reaches the frozen readers (main checkout), the engine, research and .ai (ws-c) by symlink; the
builder package is copied and ONE replacement applied; the same pytest command runs on the baseline and on each
mutant. KILLED = pytest exit non-zero AND the summary names failed tests (an error is an invalid run, not a kill).
Prints summary lines and failing test names only."""
import pathlib
import re
import shutil
import subprocess
import sys

S = pathlib.Path(__file__).resolve().parent
MUT = S / "mut-fix"
WS = pathlib.Path(sys.argv[1])
MAINCK = pathlib.Path("/Users/spiderishi/Coding/attribution")
PY_SCI = "/Users/spiderishi/Coding/attribution/.venv/bin/python"
TESTS = "scripts/scale78b/tests/test_noise_reading.py"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(S)}

MUTANTS = [
    ("N4 pooled divisor 2k -> k",
     'p_pool = sum((2 * e["sdr2"] for e in exact), Fraction(0)) / (2 * k)',
     'p_pool = sum((2 * e["sdr2"] for e in exact), Fraction(0)) / k'),
    ("N5 pooled median over the first pair only",
     "    median = GB.median_term(se2s)",
     "    median = GB.median_term(se2s[:1])"),
    ("N6 s_arm sum of squares with n not n-1",
     'arm_ss = {role: GB.variance(vs) * (len(vs) - 1) for role, vs in u_of.items()}',
     'arm_ss = {role: GB.variance(vs) * len(vs) for role, vs in u_of.items()}'),
    ("N15 fresh-R (no resume) check removed",
     '    if role == "R" and job.get("resume_from") is not None:',
     '    if False:'),
    ("N17 parity family pooled with a tier family allowed",
     '    if tier and parity:',
     '    if False:'),
    ("D4 duplicate-unit check removed",
     '            if key is not None and key in seen:',
     '            if False:'),
    ("D2 review decided by the old rounded ceiling (10.7062) instead of the factor",
     '    review = not GB.ge(2 * SESOI_PP, ex(MDE_FACTOR[plan]), sigma)',
     '    review = not GB.ge(ex({"A": "7.0390", "B9": "9.2718", "H": "10.7062"}[plan]), 1, sigma)'),
    ("A6 pooled takes the plain pairs even when the fallback governs",
     '            "_exact": {"sdr2": rd["sdr2"], "pair_se2": {k: v["se2"] for k, v in rd["pairs"].items()},',
     '            "_exact": {"sdr2": rd["sdr2"], "pair_se2": {k: v["se2"] for k, v in readings["plain"]["pairs"].items()},'),
]


def setup(mutation=None):
    if MUT.exists():
        shutil.rmtree(MUT)
    (MUT / "scripts").mkdir(parents=True)
    for name in ("gate_b_reading.py", "family_probe_reading.py", "killtest_stage0_reading.py"):
        (MUT / "scripts" / name).symlink_to(MAINCK / "scripts" / name)
    for name in ("experiments", "research", ".ai"):
        (MUT / name).symlink_to(WS / name)
    shutil.copytree(WS / "scripts/scale78b", MUT / "scripts/scale78b", ignore=shutil.ignore_patterns("__pycache__"))
    if mutation is not None:
        label, old, new = mutation
        path = MUT / "scripts/scale78b/noise_reading.py"
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1, f"{label}: anchor found {text.count(old)} times"
        path.write_text(text.replace(old, new), encoding="utf-8")


def run():
    r = subprocess.run([PY_SCI, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(S / "mut-tmp"),
                        str(MUT / TESTS)], cwd=str(MUT), capture_output=True, text=True, env=ENV)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    summary = lines[-1] if lines else ""
    failed = [l.split("::")[-1].split(" - ")[0] for l in lines if l.startswith("FAILED ")]
    errors = [l for l in lines if l.startswith("ERROR ")]
    kinds = sorted({("DID NOT RAISE" if "DID NOT RAISE" in l else "assert" if l.startswith("E       assert") or "AssertionError" in l
                     else "regex" if "Regex pattern" in l or "does not match" in l else None)
                    for l in lines} - {None})
    return r.returncode, summary, failed, errors, kinds


setup()
code, summary, failed, errors, kinds = run()
print(f"BASELINE: exit {code} | {summary} | failed {failed} | errors {len(errors)}")
assert code == 0 and not failed and not errors, "the baseline must pass before any mutant is read"
for label, old, new in MUTANTS:
    setup((label, old, new))
    code, summary, failed, errors, kinds = run()
    verdict = "KILLED" if (code != 0 and failed and not errors) else ("INVALID (errors)" if errors else "SURVIVED")
    print(f"{label}: {verdict} | {summary} | failed: {failed} | failure kinds: {kinds}")
shutil.rmtree(MUT)
shutil.rmtree(S / "mut-tmp", ignore_errors=True)
