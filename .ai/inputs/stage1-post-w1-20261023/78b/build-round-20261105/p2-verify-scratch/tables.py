"""Re-hash every file named in Part 2's section 1.17 tables (A: ws-m; B, C, D: git HEAD of the main checkout).

Prints one line per row: OK/BAD, the path, the text's hash, the measured hash. Text files under tmp/ are skipped
(not opened). Read-only: git show only.
"""
import hashlib
import re
import subprocess
import sys

PART2, WSM, MAIN = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(PART2, encoding="utf-8").read().splitlines()


def head_bytes(path):
    r = subprocess.run(["git", "-C", MAIN, "show", "HEAD:" + path], capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


table = None
rows = []
for i, ln in enumerate(lines, 1):
    m = re.match(r"\*\*Table ([ABCD])\.", ln)
    if m:
        table = m.group(1)
        continue
    if ln.startswith("### 1.18"):
        table = None
    if table and ln.startswith("| `"):
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) != 2:
            continue
        name_cell, hash_cell = cells
        hs = re.findall(r"[0-9a-f]{64}", hash_cell)
        p = re.match(r"`([^`]+)`", name_cell).group(1)
        rows.append((table, i, p, name_cell, hs))

bad = 0
for table, i, p, name_cell, hs in rows:
    if table == "A":
        path = WSM + "/scripts/scale78b/" + p
        try:
            got = sha(open(path, "rb").read())
        except OSError as e:
            got = "MISSING " + str(e)
        loc = "ws-m:scripts/scale78b/" + p
    else:
        if table == "C" and not p.startswith("scripts/"):
            rp = "scripts/stage1/settings/" + p
        else:
            rp = p
        b = head_bytes(rp)
        got = sha(b) if b is not None else "NOT-AT-HEAD"
        loc = "HEAD:" + rp
    if len(hs) != 1:
        print(f"SKIP L{i} {loc} ({len(hs)} hashes in cell)")
        continue
    ok = got == hs[0]
    bad += not ok
    print(f"{'OK ' if ok else 'BAD'} L{i} T{table} {loc} text={hs[0][:16]} got={got[:16] if len(got)==64 else got}")
print("rows", len(rows), "bad", bad)
