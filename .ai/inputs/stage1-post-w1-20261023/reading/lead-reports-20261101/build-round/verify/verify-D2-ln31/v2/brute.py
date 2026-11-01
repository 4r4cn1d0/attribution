"""Exhaustive checks of the tool's hb_split and walk on random small Unsafe cells (my own generator):

1. the set of (y, m) that some selection with one answer per unused prompt can draw is exactly
   {y <= P_yes, m <= P_no, y + m <= P} (the bounds the split uses);
2. the split's (y, m) is drawable, sums to min(n, P), keeps min(2, P_yes) and min(2, P_no) whenever some drawable
   (y, m) with that sum keeps both, and is the drawable pair closest to floor(total * A_yes / A + 1/2) under that
   constraint;
3. the walk's selection meets the targets exactly and is the lexicographically first (by sealed-order positions)
   among all selections that meet them;
4. a whole cell taken from the walk never breaks HLC 4.2's minimum when the minimum is drawable.

    python -B brute.py N SEED
"""

import itertools
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2lib  # noqa: E402,F401

from scripts.stage1_s1.hlc_draw import draw as dr  # noqa: E402


def cell(rng):
    n_prompts = rng.randint(1, 7)
    keys, sub = [], {}
    for p in range(n_prompts):
        for k in range(3):
            if rng.random() < 0.55:
                key = (f"p{p}", k)
                keys.append(key)
                sub[key] = "U/yes" if rng.random() < rng.choice((0.2, 0.5, 0.8)) else "U/no"
    used = {f"p{p}" for p in range(n_prompts) if rng.random() < 0.2}
    rng.shuffle(keys)
    return keys, sub, used, rng.randint(0, 9)


def selections(keys, sub, used):
    """Every set of keys with distinct prompts outside ``used`` (as a tuple of positions)."""
    idx = [i for i, k in enumerate(keys) if k[0] not in used]
    out = []
    for r in range(len(idx) + 1):
        for combo in itertools.combinations(idx, r):
            ps = [keys[i][0] for i in combo]
            if len(set(ps)) == len(ps):
                out.append(combo)
    return out


def main():
    n_cases, seed = int(sys.argv[1]), int(sys.argv[2])
    rng = random.Random(seed)
    bad = 0
    checked = {"cells": 0, "minimum_drawable": 0}
    for case in range(n_cases):
        keys, sub, used, n = cell(rng)
        free = [k for k in keys if k[0] not in used]
        a_yes = sum(1 for k in free if sub[k] == "U/yes")
        a_no = len(free) - a_yes
        p_yes = len({k[0] for k in free if sub[k] == "U/yes"})
        p_no = len({k[0] for k in free if sub[k] == "U/no"})
        p_all = len({k[0] for k in free})
        sels = selections(keys, sub, used)
        drawable = {(sum(sub[keys[i]] == "U/yes" for i in c), sum(sub[keys[i]] == "U/no" for i in c)) for c in sels}
        bounds = {(y, m) for y in range(0, p_yes + 1) for m in range(0, p_no + 1) if y + m <= p_all}
        if drawable != bounds:
            bad += 1
            print("case", case, "drawable set differs from the bounds", sorted(drawable ^ bounds))
            continue
        y, m = dr.hb_split(n, a_yes, a_no, p_yes, p_no, p_all, 2)
        total = min(n, p_all)
        checked["cells"] += 1
        if y + m != total or (y, m) not in drawable:
            bad += 1
            print("case", case, "split not drawable or wrong total", (y, m), total)
            continue
        same_sum = [(yy, total - yy) for yy in range(total + 1) if (yy, total - yy) in drawable]
        keep = [(yy, mm) for yy, mm in same_sum if yy >= min(2, p_yes) and mm >= min(2, p_no)]
        if total and keep:
            checked["minimum_drawable"] += 1
        pool = keep or same_sum
        if total:
            y0 = math.floor(Fraction(total * a_yes, a_yes + a_no) + Fraction(1, 2))
            best = min(pool, key=lambda t: (abs(t[0] - y0), t[0]))
            if (y, m) not in pool or abs(y - y0) != abs(best[0] - y0):
                bad += 1
                print("case", case, "split", (y, m), "not the closest in", pool, "to", y0)
                continue
        targets = {"U/yes": y, "U/no": m}
        got = dr.walk(list(keys), sub, targets, set(used))
        meet = [c for c in sels if sum(sub[keys[i]] == "U/yes" for i in c) == y
                and sum(sub[keys[i]] == "U/no" for i in c) == m]
        first = min(meet)                         # combos are sorted tuples of positions: lexicographic order
        if [keys.index(k) for k in got] != list(first):
            bad += 1
            print("case", case, "walk", [keys.index(k) for k in got], "lexicographic first", first)
        if keep and (sum(sub[k] == "U/yes" for k in got) < min(2, p_yes) or
                     sum(sub[k] == "U/no" for k in got) < min(2, p_no)):
            bad += 1
            print("case", case, "minimum broken")
    print(f"cases {n_cases}; split cells {checked['cells']}; with a drawable minimum {checked['minimum_drawable']}; "
          f"failures {bad}")
    sys.exit(1 if bad else 0)


main()
