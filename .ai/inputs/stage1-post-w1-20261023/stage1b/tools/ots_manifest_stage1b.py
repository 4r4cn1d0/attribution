"""The manifest that stage 1b's OpenTimestamps stamp binds (addendum §40 points 4 and 12: the construction checks'
hash record and the pilot reader, frozen by hash and stamped before pilot block P launches). It lists, by SHA-256
only, the files named on the command line (each must be tracked by git and equal to HEAD's blob), git's ids for HEAD
and the stage-1 code trees, and the time. No file text, no outcome; it never opens a file whose path holds "plant" or
"decoy" (such files are refused, so a protected file can enter only through a record that holds its hash).
Exclusive create.

    PY -B ots_manifest_stage1b.py ROOT OUT PATH [PATH ...]
"""
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

root, out, paths = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3:]


def git(*args) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True).stdout


if not paths:
    sys.exit("refused: no file named")
files = []
for rel in paths:
    if "plant" in rel.lower() or "decoy" in rel.lower():
        sys.exit(f"refused: a path holding a protected word is never opened here ({len(rel)} characters)")
    work = (root / rel).read_bytes()
    try:
        at_head = git("show", f"HEAD:{rel}")
    except subprocess.CalledProcessError:
        sys.exit(f"refused: {rel} is not tracked at HEAD")
    if hashlib.sha256(work).hexdigest() != hashlib.sha256(at_head).hexdigest():
        sys.exit(f"refused: {rel} differs from HEAD")
    files.append({"path": rel, "sha256": hashlib.sha256(work).hexdigest(), "bytes": len(work)})

doc = {"kind": "stage1b OpenTimestamps manifest (addendum §40 points 4 and 12)", "version": 1,
       "utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "git_head": git("rev-parse", "HEAD").decode().strip(),
       "git_trees": {p: git("rev-parse", f"HEAD:{p}").decode().strip()
                     for p in ("scripts/stage1_s1", "scripts/stage1_s1/pilot_gate", "scripts/stage1_s1/stage1b_mac",
                               "scripts/stage1_s1/reading", "runkit/stage1-olmo")},
       "files": files}
with open(out, "x", encoding="utf-8") as handle:
    handle.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
print(json.dumps({"manifest": str(out), "files": len(files),
                  "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}))
