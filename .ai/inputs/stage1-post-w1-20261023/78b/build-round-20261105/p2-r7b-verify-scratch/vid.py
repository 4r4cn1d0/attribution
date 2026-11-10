"""Engine identity from git blobs by code_identity()'s rule (no import of the engine). Usage: vid.py REPO REV"""
import hashlib, json, subprocess, sys
repo, rev = sys.argv[1:3]
def blob(p):
    return subprocess.run(["git", "-C", repo, "show", f"{rev}:{p}"], capture_output=True, check=True).stdout
names = subprocess.run(["git", "-C", repo, "ls-tree", "--name-only", rev, "experiments/safety_selection/"],
                       capture_output=True, check=True, text=True).stdout.split()
py = sorted(n.rsplit("/", 1)[1] for n in names if n.endswith(".py"))
files = {f"safety_selection/{n}": hashlib.sha256(blob(f"experiments/safety_selection/{n}")).hexdigest() for n in py}
for n in ("__init__.py", "common.py", "data.py", "ledger.py", "model.py", "plan.py", "text.py"):
    files[f"minimal_safety/{n}"] = hashlib.sha256(blob(f"experiments/minimal_safety/{n}")).hexdigest()
b = (json.dumps(files, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
print(rev, "py", len(py), "files", len(files), "identity", hashlib.sha256(b).hexdigest())
