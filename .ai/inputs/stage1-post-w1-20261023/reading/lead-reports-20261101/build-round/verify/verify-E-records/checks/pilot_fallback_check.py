"""Synthetic only: B16's paired form (REV4:675, seed part + prompt part) against E-40 point 2's fallback (seed part
only, t(0.90, 2)) on one made-up pilot table, to show the two forms can give different gate labels."""
import sys
import numpy as np
sys.path.insert(0, sys.argv[1])
from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import tdist

rng = np.random.default_rng(7)
P, seeds = 200, (1101, 1102, 1103)
# per-prompt Unsafe shares k/3; the plant raises U by a prompt-specific amount (a strong arm x prompt part)
base = rng.integers(0, 4, size=P) / 3.0
shift = np.where(rng.random(P) < 0.35, 1.0, -0.2)          # prompt-concentrated plant effect
table = {}
for j in seeds:
    table[("a0", j)] = np.clip(np.round((base + rng.normal(0, 0.15, P)) * 3) / 3, 0, 1)
    table[("a0_plant", j)] = np.clip(np.round((base + shift * 0.6 + rng.normal(0, 0.15, P)) * 3) / 3, 0, 1)
e_full = con.contrast_paired(table, "a0_plant", "a0", list(seeds), 100.0, with_item=True)
e_seed = con.contrast_paired(table, "a0_plant", "a0", list(seeds), 100.0, with_item=False)
def lb(e):
    return e.est - tdist.t_quantile(0.90, e.df) * e.se
def label(est, lower):
    if est >= 10 and lower > 5:
        return "go"
    if 5 <= est < 10:
        return "raise"
    return "stop"
for name, e in (("frozen form (seed + prompt part)", e_full), ("E-40 fallback (seed part only)", e_seed)):
    print(f"{name}: Lambda {e.est:.3f} pp, SE {e.se:.3f}, df {e.df:.2f}, one-sided 90% lower bound {lb(e):.3f} -> {label(e.est, lb(e))}")
