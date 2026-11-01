"""review_stats_arith.py: small closed-form numbers for review-statistics.md (no data read). numpy + sim_w2 t helpers (read-only)."""
import importlib.util, math, pathlib, sys
sys.dont_write_bytecode = True
p = pathlib.Path("/Users/spiderishi/Coding/attribution/research/experiments/2026-10-17-stage1-analysis-model/sim_w2.py")
spec = importlib.util.spec_from_file_location("sim_w2_ro", p); W = importlib.util.module_from_spec(spec); spec.loader.exec_module(W)
import numpy as np
tq = W.t_ppf
N = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
s = 0.002374850619448416; tauL = 2 * math.sqrt(2) * s
print("t one-sided a/6 at 42 df:", round(tq(1 - 0.05 / 6, 42), 4), " t 0.95 42:", round(tq(0.95, 42), 4), " t 0.975 42:", round(tq(0.975, 42), 4))
for lab, se in (("6 vs 6 (P4-P6 form)", s * math.sqrt(1/3)), ("6 vs 8 (P1-P3 form)", s * math.sqrt(1/6 + 1/8))):
    for mult in (1.0, 2.0):
        se_m = se * mult
        crit = tq(1 - 0.05 / 6, 42) * se_m
        pw = [W.t_sf(np.array([(crit - f * tauL) / se_m]), 42)[0] for f in (0.5, 0.75, 1.0)]
        print(f"L worse, {lab}, sigma = {mult} s: Holm step-1 one-sided threshold {crit:.5f} nats = {crit / tauL:.2f} tau_L; "
              f"P(worse (L)) at 0.5/0.75/1.0 tau_L: " + "/".join(f"{x:.2f}" for x in pw))
# n = 3 sample correlation under rho = 0
r = 0.758
print("P(|r| >= 0.758 | rho = 0, n = 3) =", round(1 - 2 / math.pi * math.asin(r), 3), "; one-sided", round(0.5 - math.asin(r) / math.pi, 3))
# per-arm SD ratio a0 vs R from 3 seeds: F(2,2) tail
a0 = np.array([46.7, 46.8, 51.3]); R = a0 - np.array([0.67, 2.50, 4.33])
F = a0.var(ddof=1) / R.var(ddof=1)
print("a0 SD", round(a0.std(ddof=1), 3), "R SD", round(R.std(ddof=1), 3), "F", round(F, 2), "P(F(2,2) >= F) =", round(1 / (1 + F), 3))
# 6-vs-3 reference contrast at per-arm SD 2.65, unpaired
se63 = 2.65 * math.sqrt(1/6 + 1/3)
for lab, q in (("one-sided 5% (the 'beats' rule)", tq(0.95, 42)), ("two-sided 5%", tq(0.975, 42)), ("one-sided alpha/6 (family 1b step 1)", tq(1 - 0.05 / 6, 42))):
    print(f"6-vs-3 MDE80 {lab}: {(q + tq(0.8, 42)) * se63:.2f} pp (SE {se63:.3f})")
# confirmation: two contrasts, each 95% two-sided, direction fixed in advance
print("confirmation: P(false 'confirmed') per null contrast 2.5%; two contrasts union", 2 * 2.5, "%")
# familywise TOST interval under plan B
print("plan B familywise equivalence interval: 1 - 2*0.05/3 =", round(100 * (1 - 2 * 0.05 / 3), 2), "%")
# false-equivalent bound per comparison over six
print("false 'equivalent (per comparison)' at the boundary: union over 6 =", 30, "%; independence", round(100 * (1 - 0.95 ** 6), 1), "%")
# S-a at the plan-A cut: per-arm SD = sigma_pair / sqrt(2 (1 - rho)); P1 (R 8 vs A1 6, 6 common seeds)
for rho in (0.0, 0.67, 0.76):
    sd = 4.5 / math.sqrt(2 * (1 - rho))
    se_hat = sd * math.sqrt(1/8 + 1/6)                 # what S-a estimates (pooled within-arm variance)
    se_true = sd * math.sqrt(7/24 - rho / 4)           # true SD of the unpaired difference with shared seeds
    half = tq(0.95, 42) * se_hat
    peq = 0.0 if half >= 5 else 2 * N((5 - half) / se_true) - 1
    print(f"plan-A cut sigma_pair 4.5, rho {rho}: per-arm SD {sd:.2f}; S-a SE {se_hat:.2f}; 90% half-width {half:.2f}; "
          f"P(equivalent | 0) ~ {peq:.2f} (SE noise ignored)")
