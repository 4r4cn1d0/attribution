"""Independent rebuild of the lean copy: apply each edit by line, from the 1B file at MAIN's commit (git show)."""
import hashlib, subprocess, sys
MAIN = "/Users/spiderishi/Coding/attribution"
ws = sys.argv[1]
src = subprocess.run(["git", "-C", MAIN, "show", "3481d85:scripts/stage1_s1/lean_eval_job.py"], capture_output=True, check=True).stdout.decode()
copy = open(f"{ws}/scripts/scale78b/lean_eval_job_78b.py").read()
lines = src.split("\n")
# 1. head: the first line's docstring opening is replaced by the new head paragraph + the original line text
assert lines[0].startswith('"""B17: the lean-evaluation job')
head_end = copy.index("B17: the lean-evaluation job")
head = copy[:head_end]
new = [head + lines[0][3:]] + lines[1:]
out = "\n".join(new)
# 2-5 by exact find/replace, each counted once
edits = [
 ('oe = importlib.import_module(f"scripts.{HERE.name}.oext_eval")', 'oe = importlib.import_module("scripts.stage1_s1.oext_eval")'),
 ('(oe.OWNER, "scripts/stage1_s1/settings/oext_eval.json")', '(oe.OWNER, OEXT_SETTINGS_PATH)'),
 ('prog="python scripts/stage1_s1/lean_eval_job.py"', 'prog="python scripts/scale78b/lean_eval_job_78b.py"'),
]
for a, b in edits:
    assert out.count(a) == 1, a
    out = out.replace(a, b)
# comments on the import line
out = out.replace("# this package's own copy (also in the mirror)", "# 7-8B copy: the S1 package's file, unchanged")
anchor = 'SETTINGS_NAME = "lean_eval_job"\n'
assert out.count(anchor) == 1
out = out.replace(anchor, anchor + 'OEXT_SETTINGS_PATH = "scripts/stage1_s1/settings/oext_eval.json"   # 7-8B copy: set per family by oext_78b.py\n')
print("rebuilt == copy:", out == copy)
print("copy sha", hashlib.sha256(copy.encode()).hexdigest())
print("head lines", head.count("\n"))
# the remaining difference other than the head: lines diff count
import difflib
d = [l for l in difflib.unified_diff(src.split("\n"), copy.split("\n"), lineterm="", n=0) if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
print("changed lines (excluding head):", len([l for l in d if not l.startswith("+") or "B17" in l or not any(h in l for h in head.split("\n") if h)]))
