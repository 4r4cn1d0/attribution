"""Track F mutation check for RV2-2: the two R4 survivors of the second re-verification (the environment reference set to
a0@1103 and to R@1101 in noise_reading.py) against the committed noise tests plus the new file
scripts/scale78b/tests/test_noise_reading_rv2_2.py. Harness as the re-verifier's: a scratch root reaches ws-f's engine,
research, tmp, stage-1 scripts and committed .ai/inputs folders by symlink; scripts/scale78b is COPIED and one mutant is
applied; the same pytest command runs on the baseline and each mutant. KILLED = pytest exit non-zero AND named failed
tests AND no errors; OWN = a test of the new file is among the failures. Prints summaries and test names only.
Usage: python -I -B mutate_rv2_2.py <ws-f>"""
import pathlib
import shutil
import subprocess
import sys

S = pathlib.Path(__file__).resolve().parent
MUT = S / "mut-rv2-2"
WS = pathlib.Path(sys.argv[1]).resolve()
PY_SCI = "/Users/spiderishi/Coding/attribution/.venv/bin/python"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(S)}
TESTS = ["scripts/scale78b/tests/test_noise_reading.py", "scripts/scale78b/tests/test_noise_reading_rv2_2.py"]
NR = "scripts/scale78b/noise_reading.py"
OWN = {"test_an_environment_difference_on_the_reference_a0_1101_is_recorded_on_every_other_unit",
       "test_an_environment_difference_on_any_other_unit_is_recorded_on_that_unit_alone"}
MUTANTS = [
    ("R4-a noise: the environment reference is a0@1103", '    reference = units[("a0", SEEDS[0])]', '    reference = units[("a0", SEEDS[2])]'),
    ("R4-b noise: the environment reference is R@1101", '    reference = units[("a0", SEEDS[0])]', '    reference = units[("R", SEEDS[0])]'),
    ("R4-c noise: the environment reference is a0@1102 (the committed test's own case)", '    reference = units[("a0", SEEDS[0])]', '    reference = units[("a0", SEEDS[1])]'),
    ("R4-d noise: every unit compared with itself (no reference)", "    differs = {f\"{role}@{s}\": environment_differs(u, reference) for (role, s), u in units.items()}",
     "    differs = {f\"{role}@{s}\": environment_differs(u, u) for (role, s), u in units.items()}"),
]


def setup(mutation=None):
    if MUT.exists():
        shutil.rmtree(MUT)
    (MUT / "scripts").mkdir(parents=True)
    for entry in sorted((WS / "scripts").iterdir()):
        if entry.name != "scale78b" and entry.name != "__pycache__":
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
    r = subprocess.run([PY_SCI, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(S / "mut-tmp-rv2-2")]
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
    killed = code != 0 and failed and not errors
    own = sorted(set(failed) & OWN)
    print(f"{label}: {'KILLED' if killed else 'SURVIVED'} | {summary} | failed {failed} | own {own} | errors {len(errors)}")
    if not killed or not own:
        survivors.append(label)
shutil.rmtree(MUT)
print(f"survivors: {survivors if survivors else 'none'}")
sys.exit(1 if survivors else 0)
