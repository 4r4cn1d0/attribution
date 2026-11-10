"""Re-verify F-4: the verifier's two survivors (V6, V8) and my own hand mutants of noise_reading.py, against the committed
noise tests, the RV2-2 file and the fixer's new guard-field file. Harness form as before: a scratch root with symlinks to
the copy's folders and a COPY of scripts/scale78b with one mutant applied. Prints summaries and test names only.
Usage: SCI -I -B mutate_reverify_f4.py <copy-of-worktree> <scratch>"""
import pathlib
import shutil
import subprocess
import sys

WS = pathlib.Path(sys.argv[1]).resolve()
S = pathlib.Path(sys.argv[2]).resolve()
MUT = S / "mut-rf4"
PY = "/Users/spiderishi/Coding/attribution/.venv/bin/python"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(S)}
TESTS = ["scripts/scale78b/tests/test_noise_reading.py", "scripts/scale78b/tests/test_noise_reading_rv2_2.py",
         "scripts/scale78b/tests/test_noise_reading_guard_fields.py"]
NR = "scripts/scale78b/noise_reading.py"
NEW = "test_noise_reading_guard_fields.py"
ENV_ANY = "    environment = any(differs.values())"
CMP = '    out = sorted(k for k in set(reference["fields"]) | set(unit["fields"]) if reference["fields"].get(k) != unit["fields"].get(k))'
GUARD = '    if unit["guard"] is not None and reference["guard"] is not None and unit["guard"] != reference["guard"]:'
APPEND = '        out.append("guard")'
READ_GUARD = '    guard = assets.get("guard")'
FLAG = '"guard_record": u["guard"] is not None}'
MUTANTS = [
    ("V6 environment_differs drops the field cudnn (verifier)", CMP,
     '    out = sorted(k for k in set(reference["fields"]) | set(unit["fields"]) if k != "cudnn" and reference["fields"].get(k) != unit["fields"].get(k))'),
    ("V8 guard comparison inverted, == for != (verifier)", GUARD,
     '    if unit["guard"] is not None and reference["guard"] is not None and unit["guard"] == reference["guard"]:'),
    ("H1 guard compared on its repo only", GUARD,
     '    if unit["guard"] is not None and reference["guard"] is not None and unit["guard"].get("repo") != reference["guard"].get("repo"):'),
    ("H1b guard compared on its files only", GUARD,
     '    if unit["guard"] is not None and reference["guard"] is not None and unit["guard"].get("files") != reference["guard"].get("files"):'),
    ("H2 differing fields not sorted (set order)", CMP,
     '    out = [k for k in set(reference["fields"]) | set(unit["fields"]) if reference["fields"].get(k) != unit["fields"].get(k)]'),
    ("H3 guard put first, not last", APPEND, '        out.insert(0, "guard")'),
    ("H4 a guard-only difference does not set the environment trigger", ENV_ANY,
     '    environment = any(any(f != "guard" for f in v) for v in differs.values())'),
    ("H5 read_unit never reads the guard record (guard = None)", READ_GUARD, "    guard = None"),
    ("H6 guard_record flag inverted", FLAG, '"guard_record": u["guard"] is None}'),
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
    r = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(S / "mut-tmp-rf4")]
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
shutil.rmtree(S / "mut-tmp-rf4", ignore_errors=True)
print(f"survivors: {survivors if survivors else 'none'}")
