"""Fix round F-4: the verifier's eleven hand mutants of noise_reading.py (verify-F section 6, the same anchors and
replacements), run against the committed noise tests, the RV2-2 file and the NEW guard-field test file. The harness is
the verifier's form: a scratch root with symlinks to the worktree's folders (read only) and a COPY of scripts/scale78b
with one mutant applied; nothing is written into the worktree. Prints summaries and test names only.
Usage: python -I -B mutate_f4.py <worktree> <scratch>"""
import pathlib
import shutil
import subprocess
import sys

WS = pathlib.Path(sys.argv[1]).resolve()
S = pathlib.Path(sys.argv[2]).resolve()
MUT = S / "mut-f4"
PY = "/Users/spiderishi/Coding/attribution/.venv/bin/python"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(S)}
TESTS = ["scripts/scale78b/tests/test_noise_reading.py", "scripts/scale78b/tests/test_noise_reading_rv2_2.py",
         "scripts/scale78b/tests/test_noise_reading_guard_fields.py"]
NR = "scripts/scale78b/noise_reading.py"
NEW = "test_noise_reading_guard_fields.py"
REF = '    reference = units[("a0", SEEDS[0])]'
DIFF = '    differs = {f"{role}@{s}": environment_differs(u, reference) for (role, s), u in units.items()}'
ENV_ANY = "    environment = any(differs.values())"
FALLBACK = '    fallback = environment or fingerprint == "differs"'
CMP = '    out = sorted(k for k in set(reference["fields"]) | set(unit["fields"]) if reference["fields"].get(k) != unit["fields"].get(k))'
GUARD = '    if unit["guard"] is not None and reference["guard"] is not None and unit["guard"] != reference["guard"]:'
MUTANTS = [
    ("V1 reference a0@1103", REF, '    reference = units[("a0", SEEDS[2])]'),
    ("V2 reference R@1101", REF, '    reference = units[("R", SEEDS[0])]'),
    ("V3 reference = the first unit read (equivalent)", REF, "    reference = next(iter(units.values()))"),
    ("V4 environment = all(...)", ENV_ANY, "    environment = all(differs.values())"),
    ("V5 fallback ignores the environment trigger", FALLBACK, '    fallback = fingerprint == "differs"'),
    ("V6 environment_differs drops the field cudnn", CMP,
     '    out = sorted(k for k in set(reference["fields"]) | set(unit["fields"]) if k != "cudnn" and reference["fields"].get(k) != unit["fields"].get(k))'),
    ("V7 environment_differs drops the field gpu", CMP,
     '    out = sorted(k for k in set(reference["fields"]) | set(unit["fields"]) if k != "gpu" and reference["fields"].get(k) != unit["fields"].get(k))'),
    ("V8 guard comparison inverted (== for !=)", GUARD,
     '    if unit["guard"] is not None and reference["guard"] is not None and unit["guard"] == reference["guard"]:'),
    ("V8b guard never compared (branch removed)", GUARD, "    if False:"),
    ("V8c guard compared even when one side has none", GUARD, '    if unit["guard"] != reference["guard"]:'),
    ("V9 per-role reference", DIFF,
     '    differs = {f"{role}@{s}": environment_differs(u, units[(role, SEEDS[0])]) for (role, s), u in units.items()}'),
    ("V10 only a0 differences trigger", ENV_ANY, '    environment = any(v for k, v in differs.items() if k.startswith("a0"))'),
    ("V11 the reference left out of the dict", DIFF,
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
    r = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(S / "mut-tmp-f4")]
                       + [str(MUT / p) for p in TESTS], cwd=str(MUT), capture_output=True, text=True, env=ENV)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    summary = lines[-1] if lines else ""
    failed = sorted({l.split(" - ")[0][len("FAILED "):] for l in lines if l.startswith("FAILED ")})
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
    by_new = sorted({f.split("::")[-1].split("[")[0] for f in failed if NEW in f})
    by_other = sorted({f.split("::")[-1].split("[")[0] for f in failed if NEW not in f})
    print(f"{label}: {'KILLED' if killed else 'SURVIVED'} | {summary} | by the new file {by_new} | by the other files {by_other} | errors {len(errors)}")
    if not killed:
        survivors.append(label)
shutil.rmtree(MUT)
shutil.rmtree(S / "mut-tmp-f4", ignore_errors=True)
print(f"survivors: {survivors if survivors else 'none'}")
