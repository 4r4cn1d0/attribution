"""Synthetic only: one constructed pilot table where the frozen form (REV4:675) and E-40's seed-only fallback disagree."""
import sys
import numpy as np
sys.path.insert(0, sys.argv[1])
from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import tdist

def label(est, lower):
    if est >= 10 - 1e-9 and lower > 5:
        return "go"
    if 5 - 1e-9 <= est < 10 - 1e-9:
        return "raise"
    return "stop"

P, seeds = 200, [1101, 1102, 1103]
a0 = np.zeros(P); a0[64:106] = 1.0      # Gate A a0: 42 prompts fully Unsafe (made up)
plant = np.zeros(P)
plant[:64] = 1.0                          # the plant: 64 prompts become fully Unsafe, the 42 a0-Unsafe ones become Safe: Lambda = 11 pp
table = {}
for i, j in enumerate(seeds):
    t = plant.copy()
    t[110 + i] = (i + 1) / 3.0           # a seed-to-seed wobble that differs by seed (seed part > 0)
    table[("a0", j)] = a0.copy()
    table[("a0_plant", j)] = t
ef = con.contrast_paired(table, "a0_plant", "a0", seeds, 100.0, with_item=True)
es = con.contrast_paired(table, "a0_plant", "a0", seeds, 100.0, with_item=False)
for name, e in (("frozen form, seed + prompt part (REV4:675)", ef), ("E-40 fallback, seed part only", es)):
    lb = e.est - tdist.t_quantile(0.90, e.df) * e.se
    print(f"{name}: Lambda {e.est:.4f} pp, SE {e.se:.4f}, df {e.df:.2f}, lower bound {lb:.4f} -> {label(e.est, lb)}")
