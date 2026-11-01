"""Synthetic only: count, over made-up pilot tables, how often B16's paired form (REV4:675: seed part + prompt part)
and E-40 point 2's fallback (seed part only, t at 2 df) give different gate labels."""
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

rng = np.random.default_rng(11)
P, seeds = 200, [1101, 1102, 1103]
diff = {}
example = None
for rep in range(400):
    base = rng.integers(0, 4, size=P) / 3.0
    frac = rng.uniform(0.1, 0.5)
    amp = rng.uniform(0.1, 0.8)
    shift = np.where(rng.random(P) < frac, amp, 0.0)
    table = {}
    for j in seeds:
        noise = rng.normal(0, rng.uniform(0.05, 0.3), P)
        table[("a0", j)] = np.clip(np.round((base + rng.normal(0, 0.15, P)) * 3) / 3, 0, 1)
        table[("a0_plant", j)] = np.clip(np.round((base + shift + noise) * 3) / 3, 0, 1)
    try:
        ef = con.contrast_paired(table, "a0_plant", "a0", seeds, 100.0, with_item=True)
        es = con.contrast_paired(table, "a0_plant", "a0", seeds, 100.0, with_item=False)
    except Exception as exc:
        continue
    lf = ef.est - tdist.t_quantile(0.90, ef.df) * ef.se
    ls = es.est - tdist.t_quantile(0.90, es.df) * es.se
    key = (label(ef.est, lf), label(es.est, ls))
    diff[key] = diff.get(key, 0) + 1
    if key == ("stop", "go") and example is None:
        example = (round(ef.est, 3), round(ef.se, 3), round(ef.df, 2), round(lf, 3), round(es.se, 3), round(ls, 3))
print("label pairs (frozen form, seed-only fallback):", dict(sorted(diff.items())))
print("first example frozen 'stop' / fallback 'go' (Lambda, SE_full, df_full, LB_full, SE_seed, LB_seed):", example)
