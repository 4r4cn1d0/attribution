"""F-1 probe (f2), re-run with the real environment (HOME kept for the offline tokenizer cache): two CLI runs on the same
absent --scratch-tmp; run 1 with --keep (the operator wants the recovered list), run 2 without, started 2.5 s later.
Usage: MAIN -I -B f2_concurrent.py <copy-of-worktree> <scratch> <edit-path> [delay-seconds]"""
import os
import pathlib
import shutil
import subprocess
import sys
import time

COPY = pathlib.Path(sys.argv[1]).resolve()
S = pathlib.Path(sys.argv[2]).resolve()
EDIT = sys.argv[3]
DELAY = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5
PY = sys.executable
ENV = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
G = S / "f1" / f"g{DELAY:g}"
if G.exists():
    shutil.rmtree(G)
(G / "tmp").mkdir(parents=True)
shared = G / "tmp" / "shared"


def tree(p) -> str:
    p = pathlib.Path(p)
    if not p.exists():
        return "ABSENT"
    if p.is_file():
        return f"FILE({p.stat().st_size}B)"
    return "DIR[" + ",".join(sorted(str(q.relative_to(p)) for q in p.rglob("*"))) + "]"


script = COPY / "scripts/scale78b/s1_olmo2_7b_check.py"
t0 = time.time()
p1 = subprocess.Popen([PY, "-I", "-B", str(script), "--edit", EDIT, "--scratch-tmp", str(shared), "--keep", "--out", str(G / "r1.json")],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV)
time.sleep(DELAY)
p2 = subprocess.Popen([PY, "-I", "-B", str(script), "--edit", EDIT, "--scratch-tmp", str(shared), "--out", str(G / "r2.json")],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV)
o1, e1 = p1.communicate(timeout=300)
t1 = time.time() - t0
o2, e2 = p2.communicate(timeout=300)
t2 = time.time() - t0
print(f"== (f2) delay {DELAY}s: run 1 (--keep) exit {p1.returncode} at {t1:.1f}s; run 2 (no --keep) exit {p2.returncode} at {t2:.1f}s")
for tag, text in (("run1 stderr", e1), ("run2 stderr", e2)):
    for line in text.splitlines():
        print(f"   {tag}:", line[:200])
for tag, text in (("run1 stdout", o1), ("run2 stdout", o2)):
    for line in text.splitlines():
        if line.startswith(("record", "verdict")):
            print(f"   {tag}:", line[:160])
print(f"   shared scratch after both (run 1 asked --keep): {tree(shared)}")
print(f"   r1.json: {tree(G / 'r1.json')}; r2.json: {tree(G / 'r2.json')}")
