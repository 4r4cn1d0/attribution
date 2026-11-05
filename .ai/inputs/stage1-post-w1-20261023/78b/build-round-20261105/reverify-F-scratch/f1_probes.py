"""Re-verify F-1: try to make s1_olmo2_7b_check.py remove a folder it did not create. Every probe runs the fixed CLI
(main) from the read-only copy of the worktree, with --scratch-tmp arranged under this scratch folder. Prints exit codes,
the REFUSED line, the CLI's record/verdict lines and folder listings (names only; never a file's content).
Usage: MAIN -I -B f1_probes.py <copy-of-worktree> <scratch> <edit-path>"""
import contextlib
import io
import os
import pathlib
import shutil
import subprocess
import sys
import time

COPY = pathlib.Path(sys.argv[1]).resolve()
S = pathlib.Path(sys.argv[2]).resolve()
EDIT = sys.argv[3]
sys.path.insert(0, str(COPY))
from scripts.scale78b import s1_olmo2_7b_check as C  # noqa: E402

ROOT = S / "f1"
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir()
PY = sys.executable
ENV = {"PATH": "/usr/bin:/bin", "HOME": str(S), "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}


def tree(p) -> str:
    p = pathlib.Path(p)
    if p.is_symlink():
        return f"SYMLINK->{os.readlink(p)}" + ("" if p.exists() else " (dangling)")
    if not p.exists():
        return "ABSENT"
    if p.is_file():
        return f"FILE({p.stat().st_size}B)"
    return "DIR[" + ",".join(sorted(str(q.relative_to(p)) for q in p.rglob("*"))) + "]"


def run(label, argv, watch):
    before = {k: tree(k) for k in watch}
    err, out = io.StringIO(), io.StringIO()
    t0 = time.time()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        try:
            code = C.main(argv)
        except BaseException as exc:                         # noqa: BLE001 - report, never hide
            code = f"EXCEPTION {type(exc).__name__}"
    after = {k: tree(k) for k in watch}
    print(f"== {label}: exit {code} ({time.time() - t0:.1f}s)")
    for line in err.getvalue().splitlines():
        print("   stderr:", line[:220])
    for line in out.getvalue().splitlines():
        if line.startswith(("record", "verdict")):
            print("   stdout:", line[:200])
    for k in watch:
        print(f"   {pathlib.Path(k).relative_to(S)}: before {before[k]} | after {after[k]}")
    return code


# (a) a pre-existing EMPTY --scratch-tmp: must survive (empty afterwards: the recovered list this run wrote is removed)
a = ROOT / "a" / "tmp" / "scratch"
a.mkdir(parents=True)
run("(a) pre-existing empty folder, real edit", ["--edit", EDIT, "--scratch-tmp", str(a), "--out", str(ROOT / "a" / "record.json")],
    [a, ROOT / "a" / "record.json"])

# (b) a pre-existing NON-EMPTY --scratch-tmp: refused, survives with its file
b = ROOT / "b" / "tmp" / "scratch"
b.mkdir(parents=True)
(b / "keep.json").write_bytes(b"{}")
run("(b) pre-existing non-empty folder", ["--edit", EDIT, "--scratch-tmp", str(b), "--out", str(ROOT / "b" / "record.json")],
    [b, ROOT / "b" / "record.json"])

# (c) a SYMLINK to a non-empty folder
c_target = ROOT / "c" / "tmp" / "target"
c_target.mkdir(parents=True)
(c_target / "keep.json").write_bytes(b"{}")
c_link = ROOT / "c" / "tmp" / "link"
c_link.symlink_to(c_target)
run("(c) symlink to a non-empty folder", ["--edit", EDIT, "--scratch-tmp", str(c_link), "--out", str(ROOT / "c" / "record.json")],
    [c_link, c_target, ROOT / "c" / "record.json"])

# (d) a SYMLINK to an empty folder
d_target = ROOT / "d" / "tmp" / "target"
d_target.mkdir(parents=True)
d_link = ROOT / "d" / "tmp" / "link"
d_link.symlink_to(d_target)
run("(d) symlink to an empty folder", ["--edit", EDIT, "--scratch-tmp", str(d_link), "--out", str(ROOT / "d" / "record.json")],
    [d_link, d_target, ROOT / "d" / "record.json"])

# (e) a DANGLING symlink (its target absent)
e_target = ROOT / "e" / "tmp" / "gone"
(ROOT / "e" / "tmp").mkdir(parents=True)
e_link = ROOT / "e" / "tmp" / "link"
e_link.symlink_to(e_target)
run("(e) dangling symlink", ["--edit", EDIT, "--scratch-tmp", str(e_link), "--out", str(ROOT / "e" / "record.json")],
    [e_link, e_target, ROOT / "e" / "record.json"])

# (f1) a path that APPEARS during the run (deterministic): absent at the start; another party creates it with content
# while the check runs; the check then refuses. Does the cleanup remove the other party's folder?
f = ROOT / "f" / "tmp" / "scratch"
(ROOT / "f" / "tmp").mkdir(parents=True)
real_check = C.check


def intruding_check(*args, **kwargs):
    (f / "intruder").mkdir(parents=True)
    (f / "intruder" / "data.json").write_bytes(b"{}")
    raise C.s1.Refusal("simulated refusal after another party created the scratch path")


C.check = intruding_check
try:
    run("(f1) path appears during the run (another party's folder), then a refusal", ["--edit", EDIT, "--scratch-tmp", str(f)], [f])
finally:
    C.check = real_check

# (f2) the realistic form: two CLI runs on the same absent --scratch-tmp; the first with --keep (the operator wants the
# recovered list), the second without, started a little later.
g = ROOT / "g" / "tmp" / "shared"
(ROOT / "g" / "tmp").mkdir(parents=True)
script = COPY / "scripts/scale78b/s1_olmo2_7b_check.py"
p1 = subprocess.Popen([PY, "-I", "-B", str(script), "--edit", EDIT, "--scratch-tmp", str(g), "--keep", "--out", str(ROOT / "g" / "r1.json")],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV)
time.sleep(2.5)
p2 = subprocess.Popen([PY, "-I", "-B", str(script), "--edit", EDIT, "--scratch-tmp", str(g), "--out", str(ROOT / "g" / "r2.json")],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=ENV)
o1, e1 = p1.communicate(timeout=300)
o2, e2 = p2.communicate(timeout=300)
print(f"== (f2) two concurrent runs, same absent scratch; run 1 --keep: exit {p1.returncode}; run 2 (2.5 s later, no --keep): exit {p2.returncode}")
for tag, text in (("run1 stderr", e1), ("run2 stderr", e2)):
    for line in text.splitlines():
        print(f"   {tag}:", line[:220])
for tag, text in (("run1 stdout", o1), ("run2 stdout", o2)):
    for line in text.splitlines():
        if line.startswith(("record", "verdict")):
            print(f"   {tag}:", line[:200])
print(f"   g/tmp/shared after both: {tree(g)}")
print(f"   r1.json: {tree(ROOT / 'g' / 'r1.json')}; r2.json: {tree(ROOT / 'g' / 'r2.json')}")

# (g) --out INSIDE an absent --scratch-tmp
h = ROOT / "h" / "tmp" / "scratch"
(ROOT / "h" / "tmp").mkdir(parents=True)
run("(g) --out inside an absent --scratch-tmp", ["--edit", EDIT, "--scratch-tmp", str(h), "--out", str(h / "record.json")], [h, h / "record.json"])

# (h) --scratch-tmp names an existing FILE
i = ROOT / "i" / "tmp" / "scratch"
(ROOT / "i" / "tmp").mkdir(parents=True)
i.write_bytes(b"precious")
run("(h) --scratch-tmp is an existing file", ["--edit", EDIT, "--scratch-tmp", str(i), "--out", str(ROOT / "i" / "record.json")], [i])

# (i) a pre-existing empty folder with --keep: the recovered list stays
j = ROOT / "j" / "tmp" / "scratch"
j.mkdir(parents=True)
run("(i) pre-existing empty folder, --keep", ["--edit", EDIT, "--scratch-tmp", str(j), "--keep", "--out", str(ROOT / "j" / "record.json")], [j])

# (j) absent scratch under absent parents: what is left behind?
k = ROOT / "k" / "tmp" / "a" / "b" / "c"
(ROOT / "k" / "tmp").mkdir(parents=True)
run("(j) absent scratch under two absent parents", ["--edit", EDIT, "--scratch-tmp", str(k), "--out", str(ROOT / "k" / "record.json")],
    [k, ROOT / "k" / "tmp" / "a", ROOT / "k" / "tmp"])
print("done")
