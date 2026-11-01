"""Verify pass: recompute the review-B draft's money totals (section 6) and two power figures.
Inputs are the estimates the draft and its check notes state (E); no data file is read."""
import math
from statistics import NormalDist

N = NormalDist()

def add(items):
    return (sum(lo for lo, hi in items.values()), sum(hi for lo, hi in items.values()))

# Per-unit add-ons quoted for 72 stage-1 units (CK-OR 5.4, 5.6; CK-EM 1.4, 2.4)
oext = (10.0, 27.0)       # O-ext, +400 prompts, 128-token cap
indomain = (5.0, 13.0)    # in-domain refusal, 200 Dolly prompts, 128-token cap
srj_pod = (2.0, 4.0)      # SRJ on the planned judge pods
prefill_full = (26.0, 39.0)
prefill_red1 = (9.0, 13.0)  # reduced: 1 setting on every unit

def scale(r, f):
    return (r[0] * f, r[1] * f)

amb = {
    "B_lowLR_6seeds": (12.0, 14.0),
    "SR_6seeds": (12.0, 14.0),
    "S6_6seeds": (12.0, 14.0),
    "Oext_H": oext,
    "in_domain": indomain,
    "SRJ_pods": srj_pod,
    "prefill_headroom": (1.1, 1.6),
    "prefill_full": prefill_full,
    "V2a": (5.6, 7.1),
    "classifier_pass": (1.0, 1.0),
}
addon18 = [scale(x, 18 / 72) for x in (oext, indomain, prefill_full, srj_pod)]
amb["addons_18_new_units"] = (sum(a[0] for a in addon18), sum(a[1] for a in addon18))
lo, hi = add(amb)
print(f"ambitious defaults at 1B: ${lo:.1f}-{hi:.1f}  (add-ons for 18 new units ${amb['addons_18_new_units'][0]:.1f}-{amb['addons_18_new_units'][1]:.1f})")
amb_mac = dict(amb); amb_mac["SRJ_pods"] = (0.0, 0.0)
addon18m = [scale(x, 18 / 72) for x in (oext, indomain, prefill_full)]
amb_mac["addons_18_new_units"] = (sum(a[0] for a in addon18m), sum(a[1] for a in addon18m))
lo2, hi2 = add(amb_mac)
print(f"  same with SRJ on the Mac: ${lo2:.1f}-{hi2:.1f}")

mini = {
    "Oext_H": oext,
    "prefill_headroom": (1.1, 1.6),
    "prefill_reduced": prefill_red1,
    "SRJ_mac": (0.0, 0.0),
    "B_lowLR_6seeds": (12.0, 14.0),
    "S6_6seeds": (12.0, 14.0),
    "classifier_pass": (1.0, 1.0),
}
addon12 = [scale(x, 12 / 72) for x in (oext, prefill_red1)]
mini["addons_12_new_units"] = (sum(a[0] for a in addon12), sum(a[1] for a in addon12))
lo3, hi3 = add(mini)
print(f"minimum useful set: ${lo3:.1f}-{hi3:.1f}")
print(f"ratios to stage 1 ($56-98): minimum {lo3/98:.2f}-{hi3/56:.2f}; ambitious {lo/98:.2f}-{hi/56:.2f}")

# Re-runs of reused units without a local adapter (CK-OR 5.4: about $0.14 per unit; CK-EM 2.4: $0.15-0.3 with setup)
print(f"train-only re-runs of about 8 reused units: ${8*0.14:.1f}-{8*0.3:.1f}")

# O-ext at the full 2,048 cap if the truncation check fails (CK-OR 5.4: +1,469 prompts cost $146-256 for 72 units)
print(f"O-ext H at the 2,048 cap: ${146*400/1469:.0f}-{256*400/1469:.0f}")

# OLMo 3 noise block if it must be read before the 20 Nov gate: 5 arms (a0 1102-1103, R_1-R_3)
print(f"OLMo 3 noise block, 5 arms: ${5*2.8*1.2:.0f}-{5*3.6*1.2:.0f} (REPLAN arm rate x1.2); "
      f"${5*30/6:.0f}-{5*40/6:.0f} (REPLAN noise-block rate)")
print(f"(b) against (a): {30/255:.2f}-{60/385:.2f} of the cost")

# MDE checks for R4.2 (per-arm SD 2.65 pp, 6 vs 6 add contrast, 6 vs 8 removal, Holm first step, 80% power)
sd = 2.65
for fam in (6, 8, 2):
    z = N.inv_cdf(1 - 0.05 / (2 * fam)) + N.inv_cdf(0.8)
    print(f"Holm over {fam}: add MDE {z*sd*math.sqrt(2/6):.2f} pp; removal MDE {z*sd*math.sqrt(1/6+1/8):.2f} pp")

# R1.8: point estimate needed for O-infeasible at 5 pp with prompt-clustered SE 4.1 pp
print(f"O-infeasible at 5 pp needs a point estimate above {5 + 1.645*4.1:.1f} pp")
print(f"HB subset SE ratio sqrt(200/35) = {math.sqrt(200/35):.2f}")
