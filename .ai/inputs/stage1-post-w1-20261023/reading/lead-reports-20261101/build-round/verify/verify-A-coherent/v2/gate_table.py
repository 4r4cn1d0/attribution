"""Verifier 2 (re-verify of fix round 1): the R1.2(a) coverage gate table for plan A from the simulation evidence
files given on the command line. Per contrast-world: coverage, its MC SE, the tail ratio, replicates, whether the band
0.88-0.92 and the ratio <= 1.5 hold, and whether the 10,000-replicate rule is triggered (coverage within 0.0134 of a
band edge at 2,000 replicates, or a tail ratio above 1.3).

    python -B gate_table.py <label=file.json> ...
"""
from __future__ import annotations

import json
import sys

LO, HI, RATIO_MAX = 0.88, 0.92, 1.5
NEAR, RATIO_10K = 0.0134, 1.3


def rows_of(label: str, path: str):
    d = json.load(open(path))
    reading = d.get("reading") or "plan_a(my_sim)"
    worlds = d.get("worlds") or d.get("results") or {}
    out = []
    for wname, w in worlds.items():
        for cname, rec in (w.get("contrasts") or {}).items():
            c, p = rec["coherent"], rec["primary"]
            cov = c.get("coverage_90", c.get("coverage"))
            n = c.get("computable", c.get("n"))
            tail = c.get("tail_rate", c.get("tail"))
            ptail = p.get("tail_rate", p.get("tail"))
            ratio = rec.get("tail_ratio")
            if ratio is None and ptail:
                ratio = tail / ptail
            out.append({"label": label, "reading": reading, "world": wname, "contrast": cname, "n": n, "cov": cov,
                        "mc_se": (cov * (1 - cov) / n) ** 0.5, "tail": tail, "ptail": ptail, "ratio": ratio,
                        "pcov": p.get("coverage_90", p.get("coverage"))})
    return out


def main(argv):
    rows = []
    for arg in argv:
        label, path = arg.split("=", 1)
        rows += rows_of(label, path)
    print(f"{'label':<34} {'reading':<20} {'world':<12} {'k':<3} {'n':>6} {'cov':>7} {'mcSE':>6} {'pcov':>7} "
          f"{'tail':>7} {'ptail':>7} {'ratio':>6}  band  ratio  needs10k")
    n_met = n_total = 0
    for r in rows:
        band = LO <= r["cov"] <= HI
        rok = r["ratio"] is not None and r["ratio"] <= RATIO_MAX
        near = (r["cov"] - LO) < NEAR or (HI - r["cov"]) < NEAR
        needs = (r["n"] < 10000) and (near or (r["ratio"] is not None and r["ratio"] > RATIO_10K))
        n_total += 1
        n_met += band and rok
        print(f"{r['label']:<34} {r['reading']:<20} {r['world']:<12} {r['contrast']:<3} {r['n']:>6} {r['cov']:>7.4f} "
              f"{r['mc_se']:>6.4f} {r['pcov']:>7.4f} {r['tail']:>7.4f} {r['ptail']:>7.4f} "
              f"{(r['ratio'] if r['ratio'] is not None else float('nan')):>6.2f}  "
              f"{'ok' if band else 'OUT':<5} {'ok' if rok else 'OUT':<6} {'YES' if needs else '-'}"
              f"{'  <-- near edge' if near else ''}{'  <-- ratio>1.3' if r['ratio'] is not None and r['ratio'] > RATIO_10K else ''}")
    print(f"contrast-worlds {n_total}; meeting band and ratio {n_met}")


if __name__ == "__main__":
    main(sys.argv[1:])
