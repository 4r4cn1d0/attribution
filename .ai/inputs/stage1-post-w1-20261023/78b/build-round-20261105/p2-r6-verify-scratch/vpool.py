"""Hash pool of git blobs at a revision (read-only; prints counts only).

Usage: python -I -B vpool.py REPO REV OUT.tsv
Skips any path with 'hidden' or 'selector', any .jsonl under .ai/ or research/,
and any non-code data file under .ai/ or research/ whose basename names judges,
answers, generations, samples or prompts (except the text-free anchor record).
Never prints file content.
"""
import hashlib
import re
import subprocess
import sys

repo, rev, out = sys.argv[1], sys.argv[2], sys.argv[3]
PREFIXES = [
    "scripts", "runkit/stage1-78b", "runkit/stage1-olmo", "experiments/safety_selection",
    "research", ".ai/inputs/stage1-post-w1-20261023", ".ai/inputs/stage1-commitments-20261016",
    ".ai/inputs/gate-b-anchors-20261008", ".ai/inputs/gate-b-sealed-20261008",
    ".ai/inputs/scale-78b-length-rules-llama3-20261105", ".ai/inputs/scale-78b-r-draws-olmo2-20261105",
    ".ai/inputs/scale-78b-s1-llama3-20261105", ".ai/inputs/scale-78b-sealed-llama3-20261105",
    ".ai/briefs", "writing/paper", "README.md",
]
BAD = re.compile(r"judge|answer|generation|sample|prompt", re.I)
CODE = (".py", ".md", ".sh", ".js", ".toml", ".txt")


def skip(p):
    low = p.lower()
    if "hidden" in low or "selector" in low:
        return True
    if low.startswith((".ai/", "research/")):
        if low.endswith(".jsonl"):
            return True
        base = low.rsplit("/", 1)[-1]
        if base == "anchor_prompts.sealed.json":
            return False
        if not base.endswith(CODE) and BAD.search(base):
            return True
    return False


ls = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "-z", rev, "--"] + PREFIXES,
                    check=True, capture_output=True).stdout
entries = []
for rec in ls.split(b"\0"):
    if not rec:
        continue
    meta, path = rec.split(b"\t", 1)
    mode, typ, oid = meta.split()
    if typ != b"blob":
        continue
    entries.append((oid.decode(), path.decode()))
keep = [(o, p) for o, p in entries if not skip(p)]
skipped = len(entries) - len(keep)
proc = subprocess.Popen(["git", "-C", repo, "cat-file", "--batch"], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE)
rows = []
for oid, path in keep:
    proc.stdin.write((oid + "\n").encode())
    proc.stdin.flush()
    header = proc.stdout.readline().split()
    size = int(header[2])
    data = proc.stdout.read(size)
    proc.stdout.read(1)
    rows.append((hashlib.sha256(data).hexdigest(), path))
proc.stdin.close()
proc.wait()
with open(out, "w") as fh:
    for h, p in rows:
        fh.write(f"{h}\t{p}\n")
print(f"blobs {len(entries)} hashed {len(rows)} skipped {skipped}")
