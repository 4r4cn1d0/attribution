"""SHA-256 pool of git blobs at a revision, skipping forbidden names (never prints contents).

Usage: python3 -I -B pool.py REPO REV OUT.tsv
Skip rule: any path containing one of SKIP (case-insensitive) is not read; it is listed with hash "SKIPPED".
"""
import hashlib
import subprocess
import sys

repo, rev, out = sys.argv[1:4]
SKIP = ("tmp/", "selector", "hidden/", "judge", "answer", "generation", "sample", "prompt", "sealed", "backups/",
        "outputs/", "edit")
ls = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "-z", rev], capture_output=True, check=True).stdout
entries = []
for rec in ls.split(b"\0"):
    if not rec:
        continue
    meta, path = rec.split(b"\t", 1)
    mode, typ, sha = meta.split(b" ")
    if typ != b"blob":
        continue
    entries.append((sha.decode(), path.decode("utf-8", "surrogateescape")))
HARD = ("tmp/", "selector", "hidden/", "backups/", "outputs/")
def skip(p):
    q = p.lower()
    if any(k in q for k in HARD):
        return True
    if q.endswith(".py"):
        return False          # code files: hashed
    if "/settings/" in q and q.endswith(".json"):
        return False          # settings files: hash only (never printed)
    return any(k in q for k in SKIP)
keep = [(s, p) for s, p in entries if not skip(p)]
skipped = [(s, p) for s, p in entries if skip(p)]
proc = subprocess.Popen(["git", "-C", repo, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
rows = []
for s, p in keep:
    proc.stdin.write((s + "\n").encode()); proc.stdin.flush()
    header = proc.stdout.readline().split()
    size = int(header[2])
    data = proc.stdout.read(size); proc.stdout.read(1)
    rows.append((hashlib.sha256(data).hexdigest(), p))
proc.stdin.close(); proc.wait()
with open(out, "w", encoding="utf-8") as f:
    for h, p in rows:
        f.write(f"{h}\t{p}\n")
    for s, p in skipped:
        f.write(f"SKIPPED\t{p}\n")
print(f"blobs {len(entries)} hashed {len(keep)} skipped {len(skipped)}")
