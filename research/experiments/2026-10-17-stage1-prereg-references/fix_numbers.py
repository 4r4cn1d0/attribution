"""Arithmetic for the fix pass of stage1-prereg-references-DRAFT.md (verify report M5, M7, m1-m4, n2-n4).

Inputs are the numbers already in the draft's section C.2 (wave-0a ledger seconds and job slots),
PLAN-S:30 (Gate A arm training 245 s) and FOCUS (retrain 0.077 h; pod overhead 26.0 min; $1.79/h).
No file is read. Run: python3 -I fix_numbers.py
"""
import math
import statistics as st

RATE = 1.79 / 3600                      # dollars per second
OVH = 26.0 * 60                         # one pod's overhead, s (measured upper, FOCUS 16 Oct 13:21 UTC)
slots = [48.9, 49.0, 43.5]              # job slots, min
ledger = [2910, 2906, 2573]             # engine-ledger totals, s
train = [220.4, 219.7, 216.0]
greedy = [1737, 1694, 1555]             # greedy generation, s, 468 prompts each
sampled = [638, 685, 504]               # sampled generation, s, 600 answers each
guard_g = [82, 80, 79]                  # guard on 468 greedy answers
guard_s = [97, 97, 96]                  # guard on 600 sampled answers
N_GREEDY, N_SAMPLED = 468, 600

FRE = st.median(slots) * 60
usd = lambda s: s * RATE
p = lambda *a: print(*a)

p("FRE s", FRE, "$/FRE", round(usd(FRE), 4))

# n3: shares by denominator
p("training share of ledger %", [round(100 * t / l, 2) for t, l in zip(train, ledger)])
p("training share of job slot %", [round(100 * t / (s * 60), 2) for t, s in zip(train, slots)])
gen = [g + s for g, s in zip(greedy, sampled)]
p("generation share of ledger %", [round(100 * g / l, 2) for g, l in zip(gen, ledger)])
p("generation share of job slot %", [round(100 * g / (s * 60), 2) for g, s in zip(gen, slots)])

# M5: greedy per prompt, 100 over-refusal answers, their guard
per_g = [g / N_GREEDY for g in greedy]
p("greedy s/prompt", [round(x, 3) for x in per_g])
o_pass = [100 * x for x in per_g]
p("100 greedy over-refusal answers, s", [round(x, 1) for x in o_pass], "median arm", round(st.median(o_pass), 1))
o_guard = [100 * g / N_GREEDY for g in guard_g]
p("their guard, s", [round(x, 1) for x in o_guard], "median", round(st.median(o_guard), 1))
p("answers in full evaluation", N_GREEDY + N_SAMPLED, "200 sampled share %", round(100 * 200 / (N_GREEDY + N_SAMPLED), 2),
  "200 harm / 468 greedy %", round(100 * 200 / N_GREEDY, 1))

# C-lean pieces (median per-answer prices, as LQ28 proposes)
per_s = st.median([s / N_SAMPLED for s in sampled])
per_gs = st.median([g / N_SAMPLED for g in guard_s])
lean_eval = 200 * (per_s + per_gs)
LOAD, TASKLOSS = 15, 11
TR_R = st.median(train)
O_PASS = st.median(o_pass) + st.median(o_guard)
p("per sampled answer s", round(per_s, 4), "guard per answer s", round(per_gs, 4), "lean eval s", round(lean_eval, 1))
c0_b = TR_R + lean_eval + LOAD                              # C-lean as written (LQ27 b)
c0_a = TR_R + lean_eval + LOAD + TASKLOSS + O_PASS          # C-lean with task loss and O (LQ27 a)
p("c0 (b) s", round(c0_b, 1), "FRE", round(c0_b / FRE, 3))
p("c0 (a) s", round(c0_a, 1), "FRE", round(c0_a / FRE, 3))

# Safe LoRA and other eval-only states
ev_full = st.median([l - t for l, t in zip(ledger, train)]) + LOAD + 28   # the draft's form
ev_fre = ev_full / FRE
p("eval-only state C-full FRE", round(ev_fre, 4), "$", round(usd(ev_full), 3))
ev_lean_a = lean_eval + LOAD + TASKLOSS + O_PASS
ev_lean_b = lean_eval + LOAD
p("eval-only state C-lean (a) c0", round(ev_lean_a / c0_a, 3), "(b) c0", round(ev_lean_b / c0_b, 3))
regen = 0.077 * 3600
p("regen per seed FRE", round(regen / FRE, 4), "$", round(usd(regen), 3), "c0 (a)", round(regen / c0_a, 3),
  "c0 (b)", round(regen / c0_b, 3), "3 seeds $", round(3 * usd(regen), 3))
tr_max = 0.03 * FRE
p("transform < 0.03 FRE = s", round(tr_max, 1), "$", round(usd(tr_max), 3), "c0 (a)", round(tr_max / c0_a, 3),
  "c0 (b)", round(tr_max / c0_b, 3))
for pts in (1, 2):
    n = 3 * pts
    fre = n * ev_fre
    pods = math.ceil(n / 4)
    base = usd(n * ev_full)
    tot = base + pods * usd(OVH)
    pods_r = math.ceil((n + 3) / 4)
    tot_r = base + 3 * usd(regen) + pods_r * usd(OVH)
    p(f"Safe LoRA {pts} point(s): {fre:.2f} FRE; c0 (a) {n * ev_lean_a / c0_a:.2f}, (b) {n * ev_lean_b / c0_b:.2f}; "
      f"${base:.2f}; +{pods} pod ${tot:.2f}; x1.25 ${1.25 * tot:.2f} | with regen, {pods_r} pods ${tot_r:.2f}; x1.25 ${1.25 * tot_r:.2f}")
marg = usd(3 * ev_full) + usd(OVH)
p("UQ9 second point: 3 evals FRE", round(3 * ev_fre, 2), "$", round(usd(3 * ev_full), 2), "+1 pod", round(marg, 2),
  "x1.25", round(1.25 * marg, 2))

# Block move (UQ8): SP 3 + scaling 6 + Safe LoRA 3 or 6 evaluations, plus 3 regeneration jobs
for sl in (3, 6):
    n_ev = 3 + 6 + sl
    pods = math.ceil((n_ev + 3) / 4)
    tot = usd(n_ev * ev_full) + 3 * usd(regen) + pods * usd(OVH)
    p(f"block move with Safe LoRA {sl} evals: {n_ev} evals + 3 regen on {pods} pods ${tot:.2f}; x1.25 ${1.25 * tot:.2f}")

# B+Qi (a0 arm: 38 steps, training 245 s, PLAN-S:30)
TR_A0 = 245
for ref in (73, 110):
    full = (TR_A0 + ref + ev_full) / FRE
    la = (TR_A0 + ref + ev_lean_a) / c0_a
    lb = (TR_A0 + ref + ev_lean_b) / c0_b
    six = 6 * (TR_A0 + ref + ev_full)
    tot = usd(six) + 2 * usd(OVH)
    p(f"B+Qi ref {ref}s: {full:.3f} FRE/seed, $ {usd(full * FRE):.2f}; c0 (a) {la:.3f}, (b) {lb:.3f}; "
      f"6 seeds {6 * full:.2f} FRE, c0 (a) {6 * la:.2f}, (b) {6 * lb:.2f}; ${usd(six):.2f}; +2 pods ${tot:.2f}; x1.25 ${1.25 * tot:.2f}")
p("G+Qi 3 seeds approx FRE", round(3 * (TR_A0 + 110 + ev_full) / FRE, 2))

# m4: certificate pod with one extra evaluation-only job
for m in (45, 50):
    p(f"certificate {m} min ${usd(m * 60):.2f}; with one evaluation ${usd(m * 60 + ev_full):.2f}, {m + ev_full / 60:.1f} min")

# M7 option (ii): a0 trains 38 steps, not 33
d = TR_A0 - TR_R
p("a0 minus R training s", round(d, 1), "share of c0 (a) %", round(100 * d / c0_a, 1), "(b) %", round(100 * d / c0_b, 1))

# n1 and n2
p("tau_O binding O levels (untuned 17):", [17 + t for t in (2, 5, 10)])
p("rough O MDE low end pp", round(100 * 2.80 * math.sqrt(0.05 * 0.95 / 300), 2))

# m5 (c): GSM8k steps in Qi et al. (7,473 rows / batch 64 x 3 epochs) and the warmup share
steps = 7473 / 64 * 3
p("GSM8k steps", round(steps, 1), "10-step share %", round(100 * 10 / steps, 2), "ours 10/38 %", round(100 * 10 / 38, 1),
  "10/600 %", round(100 * 10 / 600, 2))
