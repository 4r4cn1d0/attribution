"""review_fixes_numbers.py: arithmetic for the "Review fixes" sections of the three merge files (no data read).

Every input is a number printed in the merge files, the two reviews or their cited sources. It opens no evaluation
record. The Student t helpers come read-only from Draft B's sim_w2.py (numpy only; that venv has no scipy), loaded
by path as review_stats_arith.py loads them; no bytecode is written.

Run: PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B \
     review_fixes_numbers.py > review_fixes_numbers_out.txt
"""
import importlib.util, math, pathlib, sys
sys.dont_write_bytecode = True
p = pathlib.Path("/Users/spiderishi/Coding/attribution/research/experiments/2026-10-17-stage1-analysis-model/sim_w2.py")
spec = importlib.util.spec_from_file_location("sim_w2_ro", p)
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)
import numpy as np

tq = W.t_ppf
def tsf(x, df):
    return float(W.t_sf(np.array([x]), df)[0])

# RC-04: tau_O bound offsets. Seed-only SE floor 1.53 pp (R: RV R3); prompt-clustered SE 4.0-4.2 pp (M: CK-OR s4 via RB).
se_seed = 1.53
print("RC-04 seed-only offset, one-sided 90%: z", round(1.2816 * se_seed, 2), "; t(5 df)", round(tq(0.90, 5) * se_seed, 2))
print("RC-04 seed-only offset, upper end of two-sided 90% (R1.2): z", round(1.6449 * se_seed, 2), "; t(5 df)", round(tq(0.95, 5) * se_seed, 2))
print("RC-04 prompts-random offset, upper end of two-sided 90%, z:", round(1.6449 * 4.0, 2), "to", round(1.6449 * 4.2, 2))

# RC-10: PLAN-S's $56-98 carries 15% contingency; the same total at 1.25.
print("RC-10 stage-1 total at 1.25 instead of 1.15: $", round(56 * 1.25 / 1.15, 2), "to $", round(98 * 1.25 / 1.15, 2))

# RC-16 / S-19: m against a 3-seed reference, 6 against 3, per-arm SD 2.65 pp (PLAN-S:117), unpaired.
sd = 2.65
se63 = sd * math.sqrt(1 / 6 + 1 / 3)
a, b = 1 / 6, 1 / 3
df_w = (a + b) ** 2 / (a ** 2 / 5 + b ** 2 / 2)          # Welch-Satterthwaite df, equal true variances
for lab, alpha in (("one-sided 5%", 0.05), ("one-sided alpha/6 (family 1b step 1)", 0.05 / 6)):
    pooled = (tq(1 - alpha, 42) + tq(0.80, 42)) * se63
    welch = (tq(1 - alpha, df_w) + tq(0.80, df_w)) * se63
    print(f"RC-16/S-19 6-against-3 MDE80, {lab}: pooled 42 df {pooled:.2f} pp; Welch df {df_w:.2f} {welch:.2f} pp (SE {se63:.3f})")

# S-10 under S-1's per-contrast form: L 'worse' at Holm's first one-sided step (alpha/6), seed SD = s.
s = 0.002374850619448416
tauL = 2 * math.sqrt(2) * s
for lab, n1, n2 in (("6 vs 6 (P4-P6 form)", 6, 6), ("6 vs 8 (P1-P3 form)", 6, 8)):
    v1, v2 = 1 / n1, 1 / n2
    se = s * math.sqrt(v1 + v2)
    for dlab, df in (("pooled 42 df", 42.0), ("Welch", (v1 + v2) ** 2 / (v1 ** 2 / (n1 - 1) + v2 ** 2 / (n2 - 1)))):
        crit = tq(1 - 0.05 / 6, df) * se
        pw = [tsf((crit - f * tauL) / se, df) for f in (0.5, 0.75, 1.0)]
        print(f"S-10 L worse, {lab}, {dlab} (df {df:.2f}): threshold {crit / tauL:.2f} tau_L; P(worse (L)) at 0.5/0.75/1.0 tau_L "
              + "/".join(f"{x:.2f}" for x in pw))

# S-15 / RC-07: plan-B cells and S-a df; the familywise equivalence interval.
cells_b = 12 + 9 * 4                                   # R 12; A1, H1, S1, S4 at 9 (R: PLAN-S:118)
print("S-15 plan-B primary cells:", cells_b, "; S-a df over the five plan-B arms:", cells_b - 5)
print("S-15 plan-B familywise equivalence interval: ", round(100 * (1 - 2 * 0.05 / 3), 2), "%")

# S-11: union bound over the three 'worse' families when each family's tests are valid.
print("S-11 union bound, three families at 5% each:", 3 * 5, "%; with U's adverse tail counted as half of 5%:", 2.5 + 5 + 5, "%")

# S-17: the plant pilot's seed-paired one-sided 90% bound on 2 df.
print("S-17 t quantile, one-sided 90%, 2 df:", round(tq(0.90, 2), 3))
