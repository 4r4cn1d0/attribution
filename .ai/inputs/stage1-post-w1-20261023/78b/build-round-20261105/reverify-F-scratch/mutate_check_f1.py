"""Re-verify F-1's tests: hand mutants of the fixed s1_olmo2_7b_check.py (main's cleanup) against the fixer's test file.
A scratch root with symlinks to the copy's folders and a COPY of scripts/scale78b with one mutant applied (the tests
write their scratch under <root>/tmp/..., here the copy's tmp through the symlink). Prints summaries and test names only.
Usage: MAIN -I -B mutate_check_f1.py <copy-of-worktree> <scratch>"""
import os
import pathlib
import shutil
import subprocess
import sys

WS = pathlib.Path(sys.argv[1]).resolve()
S = pathlib.Path(sys.argv[2]).resolve()
BEFORE = pathlib.Path(sys.argv[3]).resolve()          # the fixer's before-copy of the check script (the unfixed one)
MUT = S / "mut-f1"
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
# HOME is kept: the OLMo codec loads from the offline HF cache under it (a first run with HOME replaced failed every
# codec-using test with FileNotFoundError, a harness fault, not the script's).
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
TEST = "scripts/scale78b/tests/test_s1_olmo2_7b_check.py"
CHK = "scripts/scale78b/s1_olmo2_7b_check.py"
CREATED = "    created = not scratch.exists()"
EMPTY = "    was_empty_dir = scratch.is_dir() and not any(scratch.iterdir())"
IF_CREATED = "            if created and scratch.is_dir():"
RM_LIST = '                shutil.rmtree(scratch / "list")'
MUTANTS = [
    ("K0 the unfixed round-3 script (the fixer's before-copy)", None, str(BEFORE)),
    ("K1 created = True (every scratch counts as this run's)", CREATED, "    created = True"),
    ("K2 the old cleanup (remove whenever scratch is a folder)", IF_CREATED, "            if scratch.is_dir():"),
    ("K3 was_empty_dir = False (the elif never fires)", EMPTY, "    was_empty_dir = False"),
    ("K4 the elif removes the pre-existing empty folder itself", RM_LIST, "                shutil.rmtree(scratch)"),
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
        path = MUT / CHK
        if old is None:                                   # K0: the whole unfixed script in place of the fixed one
            shutil.copyfile(new, path)
            return
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1, f"{label}: anchor found {text.count(old)} times"
        path.write_text(text.replace(old, new), encoding="utf-8")


def run():
    r = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(S / "mut-tmp-f1"), str(MUT / TEST)],
                       cwd=str(MUT), capture_output=True, text=True, env=ENV)
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
    names = sorted({f.split("::")[-1].split("[")[0] for f in failed})
    print(f"{label}: {'KILLED' if killed else 'SURVIVED'} | {summary} | by {names} | errors {len(errors)}")
    if not killed:
        survivors.append(label)
shutil.rmtree(MUT)
shutil.rmtree(S / "mut-tmp-f1", ignore_errors=True)
print(f"survivors: {survivors if survivors else 'none'}")
