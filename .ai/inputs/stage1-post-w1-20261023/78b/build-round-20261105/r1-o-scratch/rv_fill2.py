"""The re-verifier's rv_fill.py (R/r1-o-reverify-scratch/rv_fill.py) for fix round 2: the documented fill done IN
PLACE in a scratch copy of WS (scripts/scale78b copied, every other entry linked read-only, the R-21 records folder a
real folder), from the pre-fill (all-null) state, the first STEPS of T-O2's fills cumulatively, each with the maker's
defaults (its own pins file and settings folder; a W1-18 record committed at its R-21 place before its branch fill),
then the whole scale78b suite in the copy.

    PY -B rv_fill2.py WS SCRATCH STEPS
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

WS, SCRATCH, STEPS = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), int(sys.argv[3])
if SCRATCH.exists():
    raise SystemExit(f"{SCRATCH} exists")
sys.path.insert(0, str(WS / "scripts/scale78b/tests/oext"))
import conftest  # noqa: F401,E402  (the path rule of Track O's tests)
import test_oext_78b_files as tf  # noqa: E402

repo = SCRATCH / "repo"
(repo / "scripts").mkdir(parents=True)
for entry in sorted(WS.iterdir()):
    if entry.name not in ("scripts", ".git", ".ai"):
        (repo / entry.name).symlink_to(entry.resolve())
for entry in sorted((WS / "scripts").iterdir()):
    if entry.name == "scale78b":
        shutil.copytree(entry, repo / "scripts/scale78b", symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    else:
        (repo / "scripts" / entry.name).symlink_to(entry.resolve())
tf.link_tree(WS / ".ai", repo / ".ai", Path(tf.mk.RECORDS_DIR).parts[1:])
env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
env["PYTHONDONTWRITEBYTECODE"] = "1"
settings, pins_path = repo / "scripts/scale78b/settings", repo / "scripts/scale78b/settings/oext_pins_78b.json"
pins = tf.all_null_pins()


def make():
    pins_path.write_bytes(tf.mk.dumps(pins))
    done = subprocess.run([sys.executable, "-B", "scripts/scale78b/make_oext_settings_78b.py"], cwd=repo, env=env,
                          capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-300:]


make()
names = []
for name, step in tf.T_O2[:STEPS]:
    step(pins, ctx=(settings, repo))
    make()
    names.append(name)
check = subprocess.run([sys.executable, "-B", "scripts/scale78b/make_oext_settings_78b.py", "--check"], cwd=repo,
                       env=env, capture_output=True, text=True, timeout=300)
done = subprocess.run([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfE", "--basetemp",
                       str(SCRATCH / "pt"), "scripts/scale78b/tests"], cwd=repo, env=env, capture_output=True,
                      text=True, timeout=560)
lines = [x for x in (done.stdout + done.stderr).splitlines() if x.strip()]
fails = [x for x in lines if x.startswith(("FAILED ", "ERROR "))]
track_o = [x for x in fails if "tests/oext/" in x]
print(f"steps {STEPS} {names}; maker --check exit {check.returncode}; suite: {lines[-1] if lines else ''}; "
      f"Track O failures {len(track_o)}; other failures {len(fails) - len(track_o)}")
for x in fails:
    print("  ", x[:200])
