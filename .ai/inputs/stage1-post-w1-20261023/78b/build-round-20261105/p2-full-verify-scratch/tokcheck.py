"""Check every hex hash token in Part 2 against the pool (pool.tsv). Prints tokens and paths only."""
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = sys.argv[1]
pool = defaultdict(set)
full = []
for line in open(os.path.join(HERE, "pool.tsv")):
    h, src, path = line.rstrip("\n").split("\t")
    full.append((h, src, path))

SHORT = {
    "WRAP": "scorers_78b.py", "MAKER": "make_scorer_settings_78b.py", "SC": "SCORERS-78B.md",
    "PINS": "pins_78b.json", "RK": "rules_78b.py", "SR78": "stage1_rules.py", "RUN78": "job_runner_stage1.py",
    "PT78": "plan_tool.py", "P1": "2026-11-05-78b-preregistration-part1.md", "ERR": "part1-erratum-1.md",
    "RUL": "lead-rulings-part1-20261105.md", "ADD": "lead-rulings-part1-addendum-20261105.md",
    "PP": "lead-rulings-part2-prep-20261105.md", "DES": "lead-rulings-part2-design-20261106.md",
    "SCOUT": "scout-p2.md", "PLAN": "78b-readiness.md", "CHECK": "78b-readiness-check.md",
    "P78": "78b-preregistration-DRAFT.md", "KCR": "78b-kit-cap-rule.md", "PR4": "stage1-preregistration-rev4.md",
    "OXU": "oext_unit.json", "OXE": "oext_eval.json",
}

tok_re = re.compile(r"(?<![0-9a-fA-F])([0-9a-f]{64}|[0-9a-f]{7,63}(?=…)|[0-9a-f]{7}(?=`))")
lines = open(TEXT, encoding="utf-8").read().split("\n")
n_tok = 0
unmatched = []
nameless = []
for i, ln in enumerate(lines, 1):
    for m in tok_re.finditer(ln):
        t = m.group(1)
        if not re.search(r"[a-f]", t) and len(t) < 12:
            continue
        n_tok += 1
        hits = [(h, s, p) for (h, s, p) in full if h.startswith(t)]
        if not hits:
            unmatched.append((i, t))
            continue
        names = {os.path.basename(p) for (_, _, p) in hits}
        ok = any(nm in ln for nm in names)
        if not ok:
            for k, v in SHORT.items():
                if re.search(r"\b" + re.escape(k) + r"\b", ln) and v in names:
                    ok = True
        if not ok:
            nameless.append((i, t, sorted({s + ":" + p for (_, s, p) in hits})[:4]))
print("tokens", n_tok, "unmatched", len(unmatched), "matched-without-name-in-line", len(nameless))
print("== unmatched (line, token)")
for i, t in unmatched:
    print(i, t)
print("== matched but no matching name in the line (line, token, files)")
for i, t, f in nameless:
    print(i, t, f)
