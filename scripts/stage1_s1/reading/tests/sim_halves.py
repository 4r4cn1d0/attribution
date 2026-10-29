"""Seeded simulation of section 9.4's HB-C of the halves (test tooling; synthetic data only; not collected by pytest).

    python -B scripts/stage1_s1/reading/tests/sim_halves.py --reps 1000 --out FILE      (from the workspace root)

Worlds (halves_synth.world_cells; prompts, similarities, seed effects and samples drawn afresh in every replicate,
so the targets are population values): the add arms' effect (U(a0) - U(m), pp) on the lower and the higher half;
the governing contrasts a0 - m on m's halves (addendum 33 point 1; one similarity for every add set). Per world and
contrast: the coverage of the 90% interval (HB-C and S-p) at the true value on the lower half and on all prompts,
the 'holds' rate under each, the mean df, the share of lower-half fits that stopped at the 25-step limit and the share
with an arm at the floor. Writes one JSON file (numbers only) and prints a summary.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
for p in (str(REPO), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import halves_synth as hs                                                    # noqa: E402
from scripts.stage1_s1 import overlap_strata as b14                          # noqa: E402
from scripts.stage1_s1.reading import overlap                                # noqa: E402
from scripts.stage1_s1.reading.settings import design, settings              # noqa: E402

E6 = {"S1": 6.0, "S3": 6.0, "S4": 6.0}
E0 = {"S1": 0.0, "S3": 0.0, "S4": 0.0}
E12 = {"S1": 12.0, "S3": 12.0, "S4": 12.0}
MIXED_L, MIXED_H = {"S1": 4.0, "S3": 9.0, "S4": 2.0}, {"S1": 8.0, "S3": 13.0, "S4": 6.0}
WORLDS = {
    "W1 effect 6 on both halves (plan A)": ("plan_a", E6, E6, 4.0),
    "W2 effect 0 on the lower half, 12 on the higher (plan A)": ("plan_a", E0, E12, 4.0),
    "W3 mixed effects, large arm x prompt part sd 10 (plan A)": ("plan_a", MIXED_L, MIXED_H, 10.0),
    "W4 effect 6 on both halves (block A only, J = 3)": ("plan_a_block_a_only", E6, E6, 4.0),
    "W5 effect 0 on the lower half, 12 on the higher (plan B)": ("plan_b", E0, E12, 4.0),
}


def truth(eff, c, m):
    return eff.get(m, 0.0) - eff.get(c, 0.0)


def run_world(reading, eff_lower, eff_higher, prompt_sd, reps, rng, cfg):
    dsg = design(reading)
    arms = tuple(a for a in hs.FULL if a in dsg.arms)
    names = [n for n, _, _ in overlap.contrasts(dsg, cfg)]
    acc = {n: {"cover_lower": {"HB-C": 0, "S-p": 0}, "cover_all": {"HB-C": 0, "S-p": 0}, "holds": {"HB-C": 0, "S-p": 0},
               "df_lower": {"HB-C": 0.0, "S-p": 0.0}, "not_computable": 0} for n in names}
    stopped, floored = 0, 0
    for _ in range(reps):
        split = b14.split_halves(hs.similarity(rng))
        lower, higher = np.array(hs.positions(split["lower"])), np.array(hs.positions(split["higher"]))
        mask = np.zeros(200, bool)
        mask[lower] = True
        table = hs.world_cells(rng, dsg, mask, eff_lower, eff_higher, prompt_sd=prompt_sd, arms=arms)
        ov = {"strata_sha256": "a" * 64, "report_sha256": "b" * 64,
              "add_sets": {m: {"lower": lower, "higher": higher} for m in overlap.add_sets(dsg)}}
        out = overlap.read_halves(ov, dsg, table, 100.0, 0.01, cfg)
        for key, rec in out["fits"].items():
            if key.endswith("lower"):
                stopped += not rec["full"]["converged"]
                floored += bool(rec["full"]["at_floor"])
        share_lower = len(lower) / 200.0
        for n, k in out["contrasts"].items():
            c, m = k["comparator"], k["repair"]
            t_low = truth(eff_lower, c, m)
            t_all = share_lower * t_low + (1 - share_lower) * truth(eff_higher, c, m)
            a = acc[n]
            for f in ("HB-C", "S-p"):
                low, alln = k["halves"]["lower"][f], k["halves"]["all"][f]
                if not low["computable"]:
                    a["not_computable"] += 1
                    continue
                lo, hi = low["interval_90"]
                a["cover_lower"][f] += lo <= t_low <= hi
                lo, hi = alln["interval_90"]
                a["cover_all"][f] += lo <= t_all <= hi
                a["df_lower"][f] += low["estimate"]["df"]
            a["holds"]["HB-C"] += k["verdict"]["holds"]
            a["holds"]["S-p"] += k["s_p_verdict"]["holds"]
    fits_lower = reps * len(overlap.add_sets(dsg))
    result = {"reading": reading, "effect_lower": eff_lower, "effect_higher": eff_higher, "prompt_sd": prompt_sd,
              "reps": reps, "lower_half_fits_stopped_at_25_steps": stopped / fits_lower,
              "lower_half_fits_with_an_arm_at_the_floor": floored / fits_lower, "contrasts": {}}
    for n, a in acc.items():
        c, m = next((c, m) for nn, c, m in overlap.contrasts(dsg, cfg) if nn == n)
        result["contrasts"][n] = {
            "true_lower": truth(eff_lower, c, m),
            "coverage_lower_90": {f: a["cover_lower"][f] / reps for f in ("HB-C", "S-p")},
            "coverage_all_90": {f: a["cover_all"][f] / reps for f in ("HB-C", "S-p")},
            "holds_rate": {f: a["holds"][f] / reps for f in ("HB-C", "S-p")},
            "mean_df_lower": {f: a["df_lower"][f] / reps for f in ("HB-C", "S-p")},
            "not_computable": a["not_computable"]}
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="seeded simulation of the HB-C halves (synthetic data only)")
    parser.add_argument("--reps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261027)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        print(f"REFUSED: {args.out} exists", file=sys.stderr)
        return 2
    cfg = settings()
    rng = np.random.default_rng(args.seed)
    start = time.monotonic()
    worlds = {}
    for name, (reading, low, high, sd) in WORLDS.items():
        t0 = time.monotonic()
        worlds[name] = run_world(reading, low, high, sd, args.reps, rng, cfg)
        worlds[name]["seconds"] = round(time.monotonic() - t0, 1)
        print(f"{name}: {worlds[name]['seconds']} s")
        for n, r in worlds[name]["contrasts"].items():
            print(f"  {n}: true lower {r['true_lower']:+.1f}; coverage lower HB-C {r['coverage_lower_90']['HB-C']:.3f} "
                  f"S-p {r['coverage_lower_90']['S-p']:.3f}; all HB-C {r['coverage_all_90']['HB-C']:.3f}; holds HB-C "
                  f"{r['holds_rate']['HB-C']:.3f} S-p {r['holds_rate']['S-p']:.3f}; mean df lower HB-C "
                  f"{r['mean_df_lower']['HB-C']:.2f} S-p {r['mean_df_lower']['S-p']:.2f}")
    doc = {"kind": "B16 halves simulation", "seed": args.seed, "reps": args.reps, "worlds": worlds,
           "seconds": round(time.monotonic() - start, 1), "numpy": np.__version__}
    args.out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.out} in {doc['seconds']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
