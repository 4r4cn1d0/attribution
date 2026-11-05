"""Check the Part 1 draft's blinding line (section 0) against FOCUS entries. Prints only
found/not-found per substring with a short context window (counts and labels only; no prompt text)."""
import sys

path = "/Users/spiderishi/Coding/attribution/research/FOCUS.md"
lines = open(path, encoding="utf-8").read().split("\n")

checks = {
    "THE STAGE-1 READING IS DONE": [
        "2026-11-01T21:38", "+6.33", "+2.03", "0.28", "2.31", "+0.11", "+18.28", "15.97", "8.89",
        "0.8", "13.0", "12.4", "3.0", "B14", "LN-14", "P6", "+30.1", "infeasible", "undetermined",
        "+7.08", "+5.82", "+8.34", "adapter-scaling", "no O or L node", "coherence flag", "Words",
        "F_k", "S-a", "cost table", "S1 and S3", "transfer",
    ],
    "GATE B CLOSED": [
        "2026-10-23T05:26", "TOO CLOSE", "1.83", "1.28", "2.16", "1.905", "2.5", "1.06", "5.6", "1.35", "2.65",
        "rank", "label",
    ],
    "STAGE 1b'S PILOT SAYS STOP": ["2026-11-02T03:25", "+3.94", "5 pp"],
    "STAGE 1b'S CONSTRUCTION CHECKS OPENED AND PUBLISHED AFTER THE FINAL STOP": [
        "2026-11-02T03:25", "first", "AUC", "DataShield", "H2a", "H2b", "L1", "H1", "classifier", "menu",
    ],
    "THE 7-8B READINESS PLAN IS BACK": ["2026-11-05T09:33"],
}

for title, subs in checks.items():
    hits = [i for i, ln in enumerate(lines, 1) if title in ln]
    print(f"\n=== {title!r}: lines {hits}")
    if not hits:
        continue
    ln = lines[hits[0] - 1]
    print(f"  length {len(ln)} chars")
    for s in subs:
        k = ln.find(s)
        if k < 0:
            print(f"  MISSING  {s!r}")
        else:
            ctx = ln[max(0, k - 45):k + len(s) + 45].replace("\n", " ")
            print(f"  found    {s!r}: ...{ctx}...")
