"""Apply one hand mutant from a spec to a fresh copy of the kit and run the given pytest targets; print the output's
failure lines (synthetic test values only). Usage: PY -B one_mutant.py SOURCE_ROOT SCRATCH SPEC ID TARGET [TARGET...]
(ID "NONE" runs the targets unmutated)."""
import json
import os
import pathlib
import shutil
import subprocess
import sys

source, scratch, spec_path, mid = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4]
targets = sys.argv[5:]
if scratch.exists():
    raise SystemExit(f"{scratch} exists")
repo = scratch / "repo"
(repo / "runkit").mkdir(parents=True)
for entry in sorted(source.iterdir()):
    if entry.name not in ("runkit", ".git"):
        (repo / entry.name).symlink_to(entry.resolve())
for entry in sorted((source / "runkit").iterdir()):
    if entry.name == "stage1-78b":
        shutil.copytree(entry, repo / "runkit" / entry.name, symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    else:
        (repo / "runkit" / entry.name).symlink_to(entry.resolve())
kit = repo / "runkit" / "stage1-78b"
if mid != "NONE":
    m = next(x for x in json.loads(spec_path.read_text())["mutants"] if x["id"] == mid)
    target = kit / m["file"]
    text = target.read_text()
    assert text.count(m["find"]) == 1, mid
    target.write_text(text.replace(m["find"], m["replace"]))
env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
env["PYTHONDONTWRITEBYTECODE"] = "1"
cmd = [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "-rfE", "--basetemp",
       str(scratch / "pt"), *targets]
done = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=540)
lines = (done.stdout + done.stderr).splitlines()
keep = [x for x in lines if x.startswith(("E ", "FAILED", "ERROR")) or "Error" in x or "passed" in x or "failed" in x]
print("exit", done.returncode)
print("\n".join(keep[-40:]))
shutil.rmtree(scratch, ignore_errors=True)
