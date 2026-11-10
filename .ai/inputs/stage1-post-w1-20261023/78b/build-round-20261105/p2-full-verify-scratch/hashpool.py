"""Build a SHA-256 pool: K5W files (ws-k3) for the kit and scale78b, HEAD blobs elsewhere.

Prints counts only. Writes pool.tsv (sha256, source, path) next to this script.
Excludes any path containing 'hidden' or 'selector.jsonl'. Prints no file content.
"""
import hashlib
import os
import subprocess
import sys

MAIN = "/Users/spiderishi/Coding/attribution"
WSK3 = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pool.tsv")

HEAD_DIRS = [
    "scripts", "experiments/safety_selection", "runkit/stage1-olmo", "runkit/stage1-78b",
    ".ai/inputs/stage1-commitments-20261016", ".ai/inputs/scale-78b-sealed-llama3-20261105",
    ".ai/inputs/scale-78b-r-draws-olmo2-20261105", ".ai/inputs/scale-78b-length-rules-llama3-20261105",
    ".ai/inputs/scale-78b-s1-llama3-20261105", ".ai/inputs/gate-b-anchors-20261008",
    ".ai/inputs/gate-b-sealed-20261008", ".ai/inputs/stage1-post-w1-20261023/78b",
    "research/experiments", "research/review/2026-10-17-icml-78b-prep", "reading",
]


def bad(p):
    return "hidden" in p or "selector.jsonl" in p


def main():
    rows = []
    # K5W working-tree files
    for top in ("scripts/scale78b", "runkit/stage1-78b"):
        for dp, dn, fn in os.walk(os.path.join(WSK3, top)):
            dn[:] = [d for d in dn if d != "__pycache__"]
            for f in fn:
                full = os.path.join(dp, f)
                rel = os.path.relpath(full, WSK3)
                if bad(rel) or os.path.islink(full):
                    continue
                with open(full, "rb") as fh:
                    rows.append((hashlib.sha256(fh.read()).hexdigest(), "K5W", rel))
    # HEAD blobs
    ls = subprocess.run(["git", "-C", MAIN, "ls-tree", "-r", "HEAD", "--"] + HEAD_DIRS,
                        capture_output=True, text=True, check=True).stdout.splitlines()
    ents = []
    for line in ls:
        meta, path = line.split("\t", 1)
        mode, typ, oid = meta.split()
        if typ != "blob" or bad(path):
            continue
        ents.append((oid, path))
    p = subprocess.Popen(["git", "-C", MAIN, "cat-file", "--batch"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE)
    for oid, path in ents:
        p.stdin.write((oid + "\n").encode())
        p.stdin.flush()
        hdr = p.stdout.readline().split()
        size = int(hdr[2])
        data = p.stdout.read(size)
        p.stdout.read(1)
        rows.append((hashlib.sha256(data).hexdigest(), "HEAD", path))
    p.stdin.close()
    p.wait()
    with open(OUT, "w") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("pool rows", len(rows), "K5W", sum(1 for r in rows if r[1] == "K5W"),
          "HEAD", sum(1 for r in rows if r[1] == "HEAD"))


if __name__ == "__main__":
    main()
