"""Hash pool at a commit: SHA-256 of git blobs under the cited folders. Prints counts only; writes path<TAB>sha."""
import hashlib, subprocess, sys
REPO = "/Users/spiderishi/Coding/attribution"
rev, out = sys.argv[1], sys.argv[2]
ROOTS = ("scripts/", "runkit/stage1-78b/", "runkit/stage1-olmo/", "experiments/safety_selection/",
         "research/experiments/", ".ai/inputs/stage1-post-w1-20261023/78b/", ".ai/inputs/scale-78b-",
         ".ai/inputs/stage1-commitments-20261016/", ".ai/inputs/gate-b-anchors-20261008/out/anchor_prompts.sealed.json")
BAD = ("judge", "answer", "generation", "sample", "prompt")
names = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only", rev], capture_output=True, text=True,
                       check=True).stdout.splitlines()
keep, skipped = [], 0
for p in names:
    if not p.startswith(ROOTS):
        continue
    low = p.lower()
    if "hidden" in low or "selector" in low:
        skipped += 1; continue
    if p.startswith(".ai/") and any(b in p.rsplit("/", 1)[-1].lower() for b in BAD) \
            and not p.endswith("anchor_prompts.sealed.json"):
        skipped += 1; continue
    keep.append(p)
with open(out, "w") as fh:
    for p in keep:
        data = subprocess.run(["git", "-C", REPO, "show", f"{rev}:{p}"], capture_output=True, check=True).stdout
        fh.write(f"{p}\t{hashlib.sha256(data).hexdigest()}\n")
print("rows", len(keep), "skipped", skipped)
