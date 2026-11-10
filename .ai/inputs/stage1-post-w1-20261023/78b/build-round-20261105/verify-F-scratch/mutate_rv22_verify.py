"""Verifier's hand mutants for RV2-2 (noise_reading.py's environment reference and trigger), run against the committed
noise tests plus the builder's new RV2-2 test file. Harness: a scratch root with symlinks to the repo copy's folders and
a COPY of scripts/scale78b with one mutant applied. Prints summaries and test names only.
Usage: python -I -B mutate_rv22_verify.py <repo copy> <scratch>"""
import pathlib
import shutil
import subprocess
import sys

WS = pathlib.Path(sys.argv[1]).resolve()
S = pathlib.Path(sys.argv[2]).resolve()
MUT = S / "mut-rv22"
PY = "/Users/spiderishi/Coding/attribution/.venv/bin/python"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(S)}
TESTS = ["scripts/scale78b/tests/test_noise_reading.py", "scripts/scale78b/tests/test_noise_reading_rv2_2.py"]
NR = "scripts/scale78b/noise_reading.py"
OWN = {"test_an_environment_difference_on_the_reference_a0_1101_is_recorded_on_every_other_unit",
       "test_an_environment_difference_on_any_other_unit_is_recorded_on_that_unit_alone",
       "test_no_perturbation_records_nothing_and_the_plain_reading_governs"}
REF = '    reference = units[("a0", SEEDS[0])]'
DIFF = '    differs = {f"{role}@{s}": environment_differs(u, reference) for (role, s), u in units.items()}'
ENV_ANY = "    environment = any(differs.values())"
FALLBACK = '    fallback = environment or fingerprint == "differs"'
CMP = '    out = sorted(k for k in set(reference["fields"]) | set(unit["fields"]) if reference["fields"].get(k) != unit["fields"].get(k))'
GUARD = '    if unit["guard"] is not None and reference["guard"] is not None and unit["guard"] != reference["guard"]:'
MUTANTS = [
    ("V1 reference a0@1103 (re-verifier R4-a)", REF, '    reference = units[("a0", SEEDS[2])]'),
    ("V2 reference R@1101 (re-verifier R4-b)", REF, '    reference = units[("R", SEEDS[0])]'),
    ("V3 reference = the first unit read (a0@1101 by the loop order: expected EQUIVALENT)", REF, "    reference = next(iter(units.values()))"),
    ("V4 environment = all(...) instead of any(...)", ENV_ANY, "    environment = all(differs.values())"),
    ("V5 fallback ignores the environment trigger", FALLBACK, '    fallback = fingerprint == "differs"'),
    ("V6 environment_differs drops the field cudnn (no test perturbs it)", CMP,
     '    out = sorted(k for k in set(reference["fields"]) | set(unit["fields"]) if k != "cudnn" and reference["fields"].get(k) != unit["fields"].get(k))'),
    ("V7 environment_differs drops the field gpu", CMP,
     '    out = sorted(k for k in set(reference["fields"]) | set(unit["fields"]) if k != "gpu" and reference["fields"].get(k) != unit["fields"].get(k))'),
    ("V8 guard comparison inverted (== instead of !=)", GUARD,
     '    if unit["guard"] is not None and reference["guard"] is not None and unit["guard"] == reference["guard"]:'),
    ("V9 per-role reference (R units against R@1101)", DIFF,
     '    differs = {f"{role}@{s}": environment_differs(u, units[(role, SEEDS[0])]) for (role, s), u in units.items()}'),
    ("V10 only a0 differences trigger the environment flag", ENV_ANY,
     '    environment = any(v for k, v in differs.items() if k.startswith("a0"))'),
    ("V11 the reference is excluded from the dict (5 keys)", DIFF,
     '    differs = {f"{role}@{s}": environment_differs(u, reference) for (role, s), u in units.items() if (role, s) != ("a0", SEEDS[0])}'),
]


def setup(mutation=None):
    if MUT.exists():
        shutil.rmtree(MUT)
    (MUT / "scripts").mkdir(parents=True)
    for entry in sorted((WS / "scripts").iterdir()):
        if entry.name not in ("scale78b", "__pycache__"):
            (MUT / "scripts" / entry.name).symlink_to(entry)
    for name in ("experiments", "research", "tmp", "runkit"):
        (MUT / name).symlink_to(WS / name)
    (MUT / ".ai").mkdir()
    (MUT / ".ai" / "inputs").symlink_to(WS / ".ai" / "inputs")
    shutil.copytree(WS / "scripts/scale78b", MUT / "scripts/scale78b", ignore=shutil.ignore_patterns("__pycache__"))
    if mutation is not None:
        label, old, new = mutation
        path = MUT / NR
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1, f"{label}: anchor found {text.count(old)} times"
        path.write_text(text.replace(old, new), encoding="utf-8")


def run():
    r = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(S / "mut-tmp-rv22")]
                       + [str(MUT / p) for p in TESTS], cwd=str(MUT), capture_output=True, text=True, env=ENV)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    summary = lines[-1] if lines else ""
    failed = sorted({l.split("::")[-1].split(" - ")[0].split("[")[0] for l in lines if l.startswith("FAILED ")})
    errors = [l for l in lines if l.startswith("ERROR ")]
    return r.returncode, summary, failed, errors


setup()
code, summary, failed, errors = run()
print(f"BASELINE: exit {code} | {summary} | failed {failed} | errors {len(errors)}")
assert code == 0 and not failed and not errors, "the baseline must pass"
survivors = []
for label, old, new in MUTANTS:
    setup((label, old, new))
    code, summary, failed, errors = run()
    killed = bool(code != 0 and failed and not errors)
    own = sorted(set(failed) & OWN)
    committed_only = sorted(set(failed) - OWN)
    print(f"{label}: {'KILLED' if killed else 'SURVIVED'} | {summary} | by new RV2-2 tests {own} | by committed tests {committed_only} | errors {len(errors)}")
    if not killed:
        survivors.append(label)
shutil.rmtree(MUT)
print(f"survivors: {survivors if survivors else 'none'}")
