"""Re-cost of the OLMo 3 7B Instruct work from the measured OLMo-2-7B basis.

Stdlib only. No file is read. Run: python3 -I -B recost_olmo3.py > recost_olmo3_out.txt

Every input is copied by hand from the cited section of
research/review/2026-10-17-icml-78b-prep/78b-kit-cap-rule.md (KCR, SHA-256 9884bd17df46...) or
writing/paper/2026-10-17-icml-replan-PROPOSAL.md (RP) or 78b-preregistration-DRAFT.md (P78).
M = measured there; E = estimate there or here.

Architecture scale factor: 1.00. OLMo 3 7B Instruct has the OLMo-2-7B shapes (32 layers, hidden 4,096,
MLP 11,008, 32/32 heads; model-check.md section 4), so per-step training and decode work are taken as equal (E).
The answer-length risk is shown as a separate sensitivity (every generation batch at the cap).
"""
import math
from decimal import Decimal, ROUND_HALF_UP

PRICE = 1.79          # $/h, A100-SXM4-80GB Secure, every 7-8B pod (M, KCR Sources)
GUARD_PRICE = 1.85    # $/h, the guard's planning price for a new pod (R, KCR section 1)
RESERVE = 6.00        # $ kept by the guard (R, KCR section 1)
HOLD = 83.91          # $ Gate B hold (KCR section 4, KD4)
ALLOW = 1.20          # +20% planning allowance (RP section 2.1)

# measured OLMo-2-7B times, minutes (M, KCR section 3)
FT_MED, FT_MAX, FT_MIN = 90.9, 107.5, 86.1   # fine-tune-only job (train 38 steps + one e1 evaluation), n = 8
A0U = 114.6                                  # job with the untuned evaluation too (seed-1101 a0 pod), n = 1
OVH_MED, OVH_MAX = 30.4, 41.8                # pod overhead = (create -> first confirmed stop) - job

# M-cap constants, seconds (KCR section 4; SCORE is E there)
TRAIN_STEP_MAX, FIRST, BATCH, SCORE, EARLY, OUTSIDE = 24.26, 314.0, 240.9, 1250.0, 20.0, 109.0
START_MARGIN = 1800.0
POD_OVERHEAD = 48 * 60.0
ARM_JOB_MAX = 6450.0
MU = 1.15 * ARM_JOB_MAX                       # MEASURED_UPPER = SPEND_UPPER per arm


def gen_allcap():
    return max(FIRST, BATCH) + 33 * BATCH


def upper_arm(steps):
    return steps * TRAIN_STEP_MAX + gen_allcap() + SCORE + EARLY + OUTSIDE


def upper_eval():                             # evaluation-only (untuned unit): upper_M without training
    return gen_allcap() + SCORE + EARLY + OUTSIDE


def req(upper):
    return upper + START_MARGIN


def round_up_q(hours):
    return math.ceil(hours * 4 - 1e-9) / 4


def cap_hours(jobs):
    """jobs: list of (requirement_s, measured_upper_s), in run order (KCR section 4 cap structure)."""
    best = 0.0
    for k in range(len(jobs)):
        best = max(best, POD_OVERHEAD + sum(j[1] for j in jobs[:k]) + jobs[k][0])
    return round_up_q(best / 3600)


def guard_need(caps):
    """$ needed in the account at the last launch when pods with these caps run together (all at $1.85/h, as
    KCR section 7 does), with the Gate B hold."""
    return RESERVE + HOLD + sum(c * GUARD_PRICE for c in caps)


def spend(minutes):
    return minutes / 60 * PRICE


def money(x):
    """Half-up cents, as the kits and KCR round."""
    return "$" + format(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ",")


def rng(lo, hi):
    return f"{money(lo)}-{money(hi)}"


out = []
p = out.append

# ---------------- per-pod basis ----------------
probe_exp = spend(OVH_MED + A0U)
probe_up = spend(OVH_MAX + A0U * FT_MAX / FT_MED)
ft_exp = spend(OVH_MED + FT_MED)
ft_up = spend(OVH_MAX + FT_MAX)
probe_long = spend(OVH_MED + (upper_arm(38) + upper_eval()) / 60)
ft_long = spend(OVH_MED + upper_arm(38) / 60)
arm4_exp = spend(OVH_MED + 4 * FT_MED) / 4
arm4_up = spend(OVH_MAX + 4 * FT_MAX) / 4
arm3_exp = spend(OVH_MED + 3 * FT_MED) / 3
arm3_up = spend(OVH_MAX + 3 * FT_MAX) / 3
arm4_long = spend(OVH_MED + 4 * upper_arm(38) / 60) / 4

p("== Basis (E from M; architecture factor 1.00) ==")
p(f"upper_M(38) = {upper_arm(38):,.0f} s; upper_M(33) = {upper_arm(33):,.0f} s; evaluation-only upper = {upper_eval():,.0f} s")
p(f"requirement arm(38) = {req(upper_arm(38)):,.0f} s ({req(upper_arm(38))/3600:.2f} h); evaluation-only = {req(upper_eval()):,.0f} s")
p(f"probe pod (untuned + seed 1101, rung 1): expected {money(probe_exp)} ({(OVH_MED + A0U)/60:.2f} h), "
  f"upper {money(probe_up)} ({(OVH_MAX + A0U*FT_MAX/FT_MED)/60:.2f} h); long-answer {money(probe_long)}")
p(f"fine-tune-only 1-arm pod: expected {money(ft_exp)} ({(OVH_MED + FT_MED)/60:.2f} h), upper {money(ft_up)} "
  f"({(OVH_MAX + FT_MAX)/60:.2f} h); long-answer {money(ft_long)}")
p(f"per arm, 3 per pod: expected {money(arm3_exp)}, upper {money(arm3_up)}")
p(f"per arm, 4 per pod: expected {money(arm4_exp)}, upper {money(arm4_up)}; long-answer {money(arm4_long)} "
  f"(x{arm4_long/arm4_exp:.2f})")
plan_lo, plan_hi = arm4_exp * ALLOW, arm4_up * ALLOW
p(f"planning per FRE (4 per pod, x1.2): {rng(plan_lo, plan_hi)}")

caps = {
    "probe pod (eval-only untuned, then a0 arm 38)": cap_hours([(req(upper_eval()), upper_eval()), (req(upper_arm(38)), MU)]),
    "fine-tune-only 1 arm": cap_hours([(req(upper_arm(38)), MU)]),
    "2 a0 arms": cap_hours([(req(upper_arm(38)), MU)] * 2),
    "N: 3 R arms (33 steps)": cap_hours([(req(upper_arm(33)), MU)] * 3),
    "4 arms (last at 38 steps)": cap_hours([(req(upper_arm(33)), MU)] * 3 + [(req(upper_arm(38)), MU)]),
}
p("")
p("== Caps (M-cap rule; E) and guard need with the Gate B hold ==")
for name, c in caps.items():
    p(f"{name}: cap {c:.2f} h; guard {money(RESERVE + c*GUARD_PRICE)}; account need alone {money(guard_need([c]))}")
p(f"family-probe kit route (12.5 h cap, M: side pods): guard {money(RESERVE + 12.5*GUARD_PRICE)}; "
  f"account need alone {money(guard_need([12.5]))}")
p(f"probe pod launched while both shared N pods run (8.5 h + 12.5 h): {money(guard_need([8.5, 12.5, caps['probe pod (eval-only untuned, then a0 arm 38)']]))}")
p(f"OLMo 3 N pod launched while both shared N pods run: {money(guard_need([8.5, 12.5, caps['N: 3 R arms (33 steps)']]))}")
p(f"two fine-tune-only Gate A pods in parallel (M-cap): {money(guard_need([4.25, 4.25]))}; one 2-arm pod: {money(guard_need([caps['2 a0 arms']]))}; "
  f"two family-probe pods: {money(guard_need([12.5, 12.5]))}")

# ---------------- Gate A paths ----------------
JUDGE = (2.0, 6.0)   # Granite (gating direction) + HarmBench (report-only) pods, 2-4 launches (E: PRE:315, FOCUS 10 Oct)
paths = {
    "G0 stop at rung 1 (weak or too little)": (0, 0),
    "G1 rung 1 (incl. TOO CLOSE then a partial two-seed mean)": (2, 2),
    "G2 rung 2": (3, 4),
    "G3 rung 3": (4, 6),
}
p("")
p("== Gate A paths: 1 probe pod + k fine-tune-only pods ==")
for name, (k_lo, k_hi) in paths.items():
    lo = probe_exp + k_lo * ft_exp
    hi = probe_up + k_hi * ft_up
    j_lo, j_hi = (1.0, 3.0) if k_hi == 0 else JUDGE
    p(f"{name}: k {k_lo}-{k_hi}; pods {rng(lo, hi)}; x1.2 {rng(lo*ALLOW, hi*ALLOW)}; with judges "
      f"{rng(lo*ALLOW + j_lo, hi*ALLOW + j_hi)}; long-answer pods up to {money(probe_long + k_hi*ft_long)}")
    hours_lo = (OVH_MED + A0U + k_lo * (OVH_MED + FT_MED)) / 60
    hours_hi = (OVH_MAX + A0U * FT_MAX / FT_MED + k_hi * (OVH_MAX + FT_MAX)) / 60
    p(f"    A100-hours {hours_lo:.1f}-{hours_hi:.1f}")
gA = {"lo": probe_exp * ALLOW + 0 + 1.0, "G1lo": (probe_exp + 2*ft_exp)*ALLOW + JUDGE[0],
      "G3hi": (probe_up + 6*ft_up)*ALLOW + JUDGE[1]}

# ---------------- N ----------------
n_lo, n_hi = 3 * arm3_exp, 3 * arm3_up
p("")
p("== N: R_1-R_3 at OLMo 3's rung, one 3-arm pod ==")
p(f"pods {rng(n_lo, n_hi)}; x1.2 {rng(n_lo*ALLOW, n_hi*ALLOW)}; A100-hours {(OVH_MED + 3*FT_MED)/60:.1f}-{(OVH_MAX + 3*FT_MAX)/60:.1f}")
p(f"combined layout after the rung is fixed: {{a0-1102, a0-1103, R_1, R_2}} + {{R_3}}: "
  f"{money(4*arm4_exp + ft_exp)} against separate 2 x 1-arm + 3-arm {money(2*ft_exp + 3*arm3_exp)} (expected)")

# ---------------- full comparison ----------------
rows = {
    "block 0b scorers (anchors, a0-1101 retrain, A1, L1, S3/S4 passes, c0)": (5.0, 9.0),
    "blocks A+B, plan A (44 runs; 45 with a0 1107)": (44.0, 45.0),
    "references: recipe G 3 (new)": (3.0, 3.0),
    "references: B+Qi 3-6": (3.0, 6.0),
    "references: eval-only 12 x 0.85 (safety prompt 3, adapter scaling 6, Safe LoRA 3)": (10.2, 10.2),
}
p("")
p("== Full comparison beyond Gate A and N (FRE x planning per FRE) ==")
tot_lo = tot_hi = 0.0
fre_lo = fre_hi = 0.0
for name, (a, b) in rows.items():
    lo, hi = a * plan_lo, b * plan_hi
    tot_lo += lo
    tot_hi += hi
    fre_lo += a
    fre_hi += b
    p(f"{name}: {a:g}-{b:g} FRE; {rng(lo, hi)}")
JUDGES_FULL = (6.0, 13.0)    # $0.1-0.2 per unit (RP 2.1) x about 62-65 units
STORAGE = (3.0, 10.0)        # E: KCR section 6, $0.33 per stopped 50 GB pod per day
p(f"judges {rng(*JUDGES_FULL)}; idle storage {rng(*STORAGE)}")
full_lo = tot_lo + JUDGES_FULL[0] + STORAGE[0]
full_hi = tot_hi + JUDGES_FULL[1] + STORAGE[1]
p(f"full comparison beyond Gate A and N: {fre_lo:g}-{fre_hi:g} FRE; {rng(full_lo, full_hi)}")
p(f"plan B9 adds 10 runs: {rng(10*plan_lo, 10*plan_hi)}; H(b) adds 26 runs: {rng(26*plan_lo, 26*plan_hi)}")
p(f"TC k=1 (3 runs): {rng(3*plan_lo + 0.7, 3*plan_hi + 1.7)}; k=2 (6 runs): {rng(6*plan_lo + 0.7, 6*plan_hi + 1.7)}")
p(f"confirmation 18-24 FRE (optional): {rng(18*plan_lo, 24*plan_hi)}")

# ---------------- levels ----------------
gA_lo = (probe_exp + 2*ft_exp)*ALLOW + JUDGE[0]     # G1 low
gA_hi = (probe_up + 6*ft_up)*ALLOW + JUDGE[1]       # G3 high
nA_lo, nA_hi = n_lo*ALLOW, n_hi*ALLOW
p("")
p("== Levels (cumulative) ==")
p(f"L1 Gate A only: {rng(gA_lo, gA_hi)} (G0 stop: {rng(probe_exp*ALLOW + 1.0, probe_up*ALLOW + 3.0)})")
p(f"L2 Gate A + N: {rng(gA_lo + nA_lo, gA_hi + nA_hi)}")
p(f"L3 full comparison, plan A: {rng(gA_lo + nA_lo + full_lo, gA_hi + nA_hi + full_hi)}")
p(f"L3 at plan B9: {rng(gA_lo + nA_lo + full_lo + 10*plan_lo, gA_hi + nA_hi + full_hi + 10*plan_hi)}")
p(f"L3 at H(b): {rng(gA_lo + nA_lo + full_lo + 26*plan_lo, gA_hi + nA_hi + full_hi + 26*plan_hi)}")
p(f"L3 step beyond L2 (plan A): {rng(full_lo, full_hi)}")
p(f"L4 = L3 + confirmation: {rng(gA_lo + nA_lo + full_lo + 18*plan_lo, gA_hi + nA_hi + full_hi + 24*plan_hi)}")

# ---------------- A100-hours ----------------
per_fre_lo = (OVH_MED + 4 * FT_MED) / 60 / 4
per_fre_hi = (OVH_MAX + 4 * FT_MAX) / 60 / 4
h_gA = ((OVH_MED + A0U + 2*(OVH_MED + FT_MED)) / 60, (OVH_MAX + A0U*FT_MAX/FT_MED + 6*(OVH_MAX + FT_MAX)) / 60)
h_n = ((OVH_MED + 3*FT_MED) / 60, (OVH_MAX + 3*FT_MAX) / 60)
h_score = (9.0, 20.0)   # E: A1 pass 6-11 h (RP 2.1) + overhead, plus anchors, retrain, L1, S3/S4, c0
p("")
p("== A100-hours (before the 20% allowance) ==")
p(f"per FRE at 4 per pod: {per_fre_lo:.2f}-{per_fre_hi:.2f} h")
arms_refs_lo = 44 + 3 + 3 + 10.2
arms_refs_hi = 45 + 3 + 6 + 10.2
h_ar = (arms_refs_lo * per_fre_lo, arms_refs_hi * per_fre_hi)
p(f"Gate A {h_gA[0]:.1f}-{h_gA[1]:.1f}; N {h_n[0]:.1f}-{h_n[1]:.1f}; scorers {h_score[0]:.0f}-{h_score[1]:.0f}; "
  f"blocks + references {h_ar[0]:.1f}-{h_ar[1]:.1f}")
p(f"L3 total {h_gA[0] + h_n[0] + h_score[0] + h_ar[0]:.0f}-{h_gA[1] + h_n[1] + h_score[1] + h_ar[1]:.0f} A100-hours")

print("\n".join(out))
