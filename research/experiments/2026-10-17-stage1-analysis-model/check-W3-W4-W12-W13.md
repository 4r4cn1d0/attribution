# Check of mock-review weaknesses W3, W4, W12 and W13 against the design records

- **For:** the main-study lead (GI VI). Read-only check by an Opus worker. No repository edit, commit, pod, spend or download.
- **Clock:** `date -u` gave Fri 16 Oct 2026 22:37 UTC (17 Oct IST) before this file was written.
- **Scope:** the stage-1 design on OLMo-2-1B, recipe B, Dolly: removal arms A1, L1, H1 (600 rows); add arms S1, S3, S4 (48 rows); primary family P1–P6; U on 600 sampled answers; Holm over 6 at 5%; SESOI 5 pp by TOST; seeds 1102–1107 (method), R 8, a0 6; τ_O grid 2/5/10 pp; the "worse" label.
- **Labels.** **R** = read in a record (path:line). **M** = computed here from records (script and output named in §6). **I** = inference or proposal. **E** = planning estimate under stated assumptions.
- **Files not opened:** `selector.jsonl`, `hidden/`, held-out files, wave-0b `rows.jsonl` and `groups.json`, the Gate B wave-0a R arms' answer or guard records. No prompt, answer or prompt id is printed anywhere.

**Short names** (main checkout `/Users/spiderishi/Coding/attribution`, HEAD 32827af at read time; SHA-256 first 16):

| Name | File | SHA-256 |
|---|---|---|
| FOCUS | `research/FOCUS.md` | `23e3da8f893e8135` |
| PLAN-S | `research/review/2026-10-08-sharpened-direction-DRAFT.md` | `6ff3ff2b15bc4295` |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (rev. 5, frozen) | `5c97cce78cfad2c1` |
| BRIEF | `.ai/briefs/stage1-commitments-build-20261016.md` | `12cbf46318728d32` |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` | `114776482a3287dd` |
| MOCK | `writing/paper/2026-10-17-mock-review-A-methods.md` | `ff0e4382d542f85e` |
| PAPER | `writing/paper/icml/main.tex` (revision 6) | `0b9e49881a37e0d4` |
| NG | `research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-post-wave0b.json` | `889f574967cfffa4` |

---

## 1. Verdicts

| # | Verdict | In one line |
|---|---|---|
| **W3** | **holds** | "Dominates" and "beats the references" have three different wordings and no estimator, test, α, margin or multiplicity rule. Not testable as written. Two parts of the reviewer's fix are wrong: it is not "about $0" (about +$22–25 at measured rates), and pairing the references with a0 alone gains little power. |
| **W4** | **holds** | The labels use about 12 kinds of test, but only the six U tests have a stated family. The false-"worse" rate of the current plan is about **11%** under its most literal reading (6.9–13.2% under other Holm readings; 43% if the over-refusal and task-loss tests are per comparison). One closed family (§3.4) brings it to about 3% and moves the primary MDE by about 1%. |
| **W12** | **holds** | With 100 greedy prompts, τ_O = 2 pp cannot be resolved for a claim about over-refusal in general: it needs about 800–3,100 prompts. It can be resolved for a claim about these 100 prompts only. REQ-19's O-ext trigger gives opposite answers under these two readings, so the reading must be fixed first. |
| **W13** | **holds** | No stage-1 record has a rule for arms that fail the answers-end screen. Only the paper has one ("not read", PAPER:666-668), which drops the arm after its outcome is seen. Gate B already labels such failures (TOO CLOSE) and never drops them. A $0 rule fixes this (§5.4). |

---

## 2. W3: "beats the five references"

### 2.1 What the records say (R)

There are three different definitions:

1. **Below the adapter-scaling curve.**
   - FOCUS:243: a data repair "dominates" only if it lies below the adapter-scaling curve of U against over-refusal and task loss.
   - PLAN-S:111: the same, with "(lower U at equal O and L)".
   - PAPER:536-539: "a lower F than the curve at equal O and L", with λ ∈ {1, 0.75, 0.5, 0}.
2. **Beats the free references on U, O and L.** FOCUS:153 (the Safe LoRA decision): a data repair "dominates" only if it beats the free references on U, over-refusal and task loss.
3. **Beats five references.** PAPER:286-291: "dominant only if it beats five references that change no data": safety prompt (SP), adapter scaling (AS), Safe LoRA (SL), recipe G, B+Qi.

Other wording:
- PLAN-S:95 and FOCUS:255 (do not claim) and PLAN-S:156 / PAPER:736-737 ("states plainly whether any data repair beats these references").
- Abstract FINDING 2 (PAPER:217): "how the **best** data repair compares with the references".

Seeds (R): SP, AS at λ 0.75 and 0.5, and SL at a0 seeds 1101–1103 (PLAN-S:152-153; FOCUS:154). Recipe G at 3 seeds (FOCUS:243). B+Qi at 6 (FOCUS:225).

### 2.2 Is it defined? Is it testable? (R, I)

No. These parts are missing or in conflict:

1. **Which references.** Definition 1 uses only the AS curve. Definitions 2 and 3 use all references. Recipe G and B+Qi need training, so they are not "free" in the sense of FOCUS:153. They are free only in the sense of "no data change".
2. **"Beats" for a point reference** (SP, SL, G, B+Qi) has no definition at all.
3. **"At equal O and L" is over-determined.** The AS curve has one parameter (λ). A repair's (O, L) pair will not lie on it. No matching or interpolation rule exists.
4. **No test.** There is no estimator, α, sidedness, margin, CI method or seed rule.
5. **No rule across repairs.** "The best data repair" (FINDING 2) is picked on the same data. That is a winner's-curse selection. No rule names which repairs are compared.
6. **The O axis inherits W12.** O is measured on 100 prompts, so "no worse O than the reference" is coarse.

### 2.3 Power (E, M)

Assumptions: per-arm seed SD σ = 2.65 pp (PLAN-S:117); one-sided 5%; 80% power; normal approximation. A post-hoc reference at seed j is ref_j = a0_j − d_j. The SD of d_j (transform effect plus sampling) is σ_d = 2.1 pp (PREREG's σ_eval planning value) or 3.0 pp.

| Design for "m beats r" | SE of contrast (pp) | MDE (pp) |
|---|---|---|
| Current: m 6 seeds vs r 3 seeds, r's seed SD = σ | 1.87 | 4.7 |
| Current, r's seed SD = √(σ² + σ_d²) | 2.23–2.55 | 5.6–6.3 |
| W3 fix: r on all 6 a0 seeds, paired with a0; m not paired | 1.75–1.96 | 4.4–4.9 |
| Fix, and m also seed-paired with a0, ρ = 0.5 | 1.38–1.63 | 3.4–4.1 |
| Fix, and m also seed-paired with a0, ρ = 0.76 | 1.14–1.44 | 2.8–3.6 |
| Recipe G: 3 seeds / 6 seeds | 1.87 / 1.53 | 4.7 / 3.8 |

Why the fix alone gains little: m − ref = (m − a0) + d. Pairing makes d precise, but m − a0 still carries both arms' full seed noise. The large gain needs m paired with a0 by seed. That is W2's within-seed correlation ρ. It is not established: σ̂_gate = 1.83 against √2 × 2.65 = 3.75 gives ρ̂ ≈ 0.76, but each SD has 2 df. The F ratio 4.2 on (2, 2) df gives p ≈ 0.19 (M; NG `plain.sd_r_pp`). PLAN-S:102 says seeds are not paired (correlation −0.08).

**Intersection–union test (IUT) power** (M; 400,000 replicates; all five references one-sided at 5%; m's mean shared):

| True advantage of m | Current design | W3 fix |
|---|---|---|
| +4 pp over each of the five | 0.32 | 0.43 |
| +6 pp over each | 0.81 | 0.87 |
| +4 pp over SP, +12 pp over the others | 0.69 | 0.74 |
| +6 pp over SP, +12 pp over the others | 0.94 | 0.96 |

If the binding reference is recipe G (3 seeds, a training arm), the fix gives no gain. In the current-design rows, the three post-hoc references share a0 seeds 1101–1103. The simulation treats them as independent, so it slightly under-states the current joint power.

### 2.4 A testable rule (I; proposal for the stage-1 pre-registration)

1. **Point references** (SP, SL, recipe G, B+Qi). Repair m *beats* r only if all three hold:
   - U: the one-sided 95% upper bound of U(m) − U(r) < 0;
   - O: the one-sided 95% upper bound of O(m) − O(r) < m_O (proposal: m_O = the primary τ_O, §4.6);
   - L: the one-sided 95% upper bound of L(m) − L(r) < τ_L.
2. **The AS curve: match on task loss.** This removes the over-determination.
   - λ\*_m is the λ at which the piecewise-linear L_AS(λ) on the λ grid equals L̂(m). If L̂(m) ≤ L̂(a0), then λ\*_m = 1.
   - U_AS(λ\*_m) and O_AS(λ\*_m) are read off the same interpolation.
   - m beats AS only if the one-sided 95% upper bounds of U(m) − U_AS(λ\*_m) and of O(m) − O_AS(λ\*_m) − m_O are both below 0.
   - The CI comes from a seed bootstrap: resample a0 seeds together with their own transforms; resample m's seeds independently; solve λ\* again in each draw (10,000 draws).
   - Report matching on O as a sensitivity.
3. **Dominates** = beats all five (IUT). Each part is at one-sided 5%. No adjustment is needed inside one repair.
4. **Across repairs.** The six dominance claims enter the closed family of §3.4 as nodes D_k (§3.4, extension). For every repair, "which references it beats" is reported per comparison. FINDING 2 names the repairs by this rule, never "the best".
5. **Grid.** The repairs' L will lie near a0's, so λ\* will usually fall between 0.75 and 1. The AS curve is steepest in U there, and linear interpolation over that gap is weak. Add λ = 0.9 (6 more evaluations, §2.5).

### 2.5 Cost of the post-hoc references on all six a0 adapters, paired by seed (M)

Basis (R and M):
- the three wave-0a R arms' ledgers (timing fields only): job slots 48.9, 49.0 and 43.5 min; training 216–220 s;
- 1 FRE = 2,934 s (the median slot);
- $1.79/h; at most 4 arms per pod (Gate B's kit constant; the stage-1 kit is not built);
- pod overhead 18.9–26.0 min (recost NOTES);
- contingency × 1.25.

An evaluation-only state is the slot minus training: **2,714 s = 0.925 FRE = $1.35** (49 min gives $1.46). Generation is about 80% of an arm, so "evaluation only" is not cheap. C-lean (200 harm prompts × 1 sampled answer at 1.06 s + 0.16 s guard, plus a 15 s load) is **260 s = 0.089 FRE ≈ 0.54 c0 = $0.13** per state.

| Plan | Evaluated states | C-full FRE | Money, measured–49 min | With pod overhead, × 1.25 | C-lean FRE |
|---|---|---|---|---|---|
| Current (3 seeds: SP 3, AS 6, SL 3) | 12 | 11.1 | $16.2–17.5 | $22.4–24.8 | 1.06 |
| W3 fix (6 seeds: SP 6, AS 12, SL 6) | 24 | 22.2 | $32.4–35.1 | $44.7–49.7 | 2.13 |
| Fix + λ = 0.9 | 30 | 27.7 | $40.5–43.9 | $56.2–62.6 | 2.66 |
| Fix + λ = 0.9 + a second SL point | 36 | 33.3 | $48.6–52.6 | $67.1–74.5 | 3.19 |
| **Increment, fix − current** | **+12** | **+11.1** | **+$16.2–17.5** | **+$22.4–24.8** | **+1.06** |

- A missing a0 adapter must be regenerated by a train-only run: 0.077 h measured (wave 0b), about $0.14 per seed. FOCUS:94 says seeds 1102 and 1103 may need this. Seeds 1104–1106 are trained by stage 1 anyway.
- If the reference evaluations go into the stage-1 a0 pods, the pod overhead mostly goes away.
- The test needs the full-precision U (600 answers) and O. So the C-lean figure is the cost-axis entry, not the money spent.

### 2.6 Where I disagree with the review

- **"Cheapest fix (about $0, evaluation only)" (MOCK:104) is wrong at measured rates.** One evaluation is 0.93 FRE. The 12 added states cost about $22–25 with overhead and contingency. "About $0" holds only in C-lean accounting.
- **"Paired with a0 by seed … shrinks the variance a lot" (MOCK:105) is true only for the reference's own effect, ref − a0.** For m − ref, the SE falls from 1.87 to about 1.75 pp, a 6% gain, and that gain comes from 6 seeds, not from pairing. A large gain needs m paired too (ρ > 0, W2).
- **The reviewer's 6-vs-3 MDE of 5.4 pp is two-sided** ((t₀.₉₇₅,₄₂ + t₀.₈) × 1.87). "Beats" is one-sided: 4.7 pp. The Bonferroni-over-5 figure (6.7 pp) is not needed, because the IUT needs no adjustment (the reviewer says so too).

**Smallest decisive check before the freeze ($0):** estimate ρ and the variance components from the existing Gate A/B units (W2's fix). That alone decides whether a seed-paired m-vs-reference analysis is worth pre-registering.

---

## 3. W4: multiplicity

### 3.1 Every test the stage-1 claims use (R)

| Claim | Test now | Sided | Family / α | Status | Source |
|---|---|---|---|---|---|
| better / worse on U (P1–P6) | pooled-variance t, df ≈ 42 | two-sided | Holm over 6, 5% | fixed | PLAN-S:114 ("Holm at 5% two-sided"); FOCUS:241 |
| "better" also needs Λ̂ ≥ 5 pp | point-estimate filter | – | – | fixed | PLAN-S:115; PAPER:521-524 |
| equivalent | TOST, 90% CI inside ±5 pp | two one-sided at 5% | per contrast, not adjusted | fixed | PLAN-S:115 ("TOST per contrast") |
| 4 pp margin | sensitivity | – | – | fixed | PLAN-S:115 |
| worse on O (vs comparator) | significance "in its harmful direction", no margin | one-sided (I) | "5% Holm level"; which family is **open** | open (U4) | FOCUS:215; BRIEF:192 |
| worse on L (vs comparator) | as for O | one-sided (I) | open | open (U4) | FOCUS:215; BRIEF:192 |
| feasible on O (vs untuned) | O ≤ O_untuned + τ_O at τ_O ∈ {2, 5, 10} | point estimate or bound: **not stated** | – | open | FOCUS:245; PLAN-S:123 |
| feasible on L | ΔL vs a0 ≤ τ_L = 2√2·s | **not stated** | – | τ_L fixed | ADD L16 |
| selector screen | upper 90% bound of O or L vs τ | one-sided | – | fixed (a different rule from the labels) | BRIEF REQ-16 |
| beats / dominates references | **none** (§2) | – | – | undefined | §2.1 |
| harm wording (claim rule) | same sign, at least half the size | point estimates | – | fixed | FOCUS:244; PLAN-S:108 |
| add effect on the less similar half | "must hold" | **not stated** | – | undefined | PLAN-S:172; PAPER:712-713 |
| secondary arms | one-sided upper bounds only | one-sided | – | fixed | PLAN-S:158 |
| confirmation (≤ 2 contrasts) | **not stated** | – | own 5% | open | FOCUS:252; PLAN-S:119 |
| Llama replication | "same sign, difference below its MDE" | – | own 5% | fixed (W9 disputes) | PLAN-S:119 |
| plant pilot | one-sided 90% lower bound > 5 pp | one-sided | own | fixed | PLAN-S:179 |
| decision-value predictions | scored on Llama's menu | – | own 5% | fixed (W14 disputes) | PLAN-S:119, :132 |
| answers end (coherence) | **none for stage 1** (§5) | – | – | undefined | PAPER:666-668 |

Sidedness: PLAN-S:114 makes all six U tests two-sided. PAPER:703-705 names P4's sidedness only, which invites the reviewer's reading that the others are one-sided. That is a paper-wording defect, not a design gap.

### 3.2 False-"worse" rate of the current plan (M)

**Set-up.** 200,000 replicates. Stage-1 seeds (R 8, a0 6, six arms × 6; df 42). Normal seed noise, pooled variance per endpoint. Every contrast uses its own comparator: P1–P3 share R; P4, P5 and P6 share S1. The rate does not depend on the SDs under a null. Readings of "at the 5% Holm level":

| Reading | Global null (no effect anywhere) | U–O correlation −0.5 | Realistic mix (I) |
|---|---|---|---|
| **R1 (most literal):** U from the two-sided Holm-6; O and L each a one-sided Holm-6 family | **11.1%** (U 2.4, O 4.6, L 4.5) | 11.0% | 10.2% |
| R2: O and L two-sided Holm-6, adverse side read | 6.9% | 6.9% | 6.0% |
| R3: one Holm over 18 one-sided adverse tests | 4.7% | 4.6% | 3.8% |
| R4: O and L per comparison, one-sided 5% | **43.5%** | 43.7% | 39.8% |
| R5: three one-sided Holm-6 families (U adverse as its own family) | 13.2% | 13.0% | 11.0% |

- The realistic mix: P1, P3 at +2 pp; P2 at 0; S1, S3 and S4 restore 10 pp, so P4 = +10 and P5 = P6 = 0. Add arms raise O by 8 pp, so P4's "worse on O" is true and P5's and P6's are false. L shows no effect.
- The Monte Carlo SE is at most 0.11 pp.
- The reviewer's "up to 1 − 0.95³ ≈ 14%" (MOCK:120) is about right as a Holm-reading upper bound. The real risk is R4, which the records do not exclude (U4 open).

**Other error rates of the current plan** (M, reading R1). Configuration: every |Λ_k| on the ±5 pp equivalence boundary (P1–P3 at +5, P4 at +10, P5 and P6 at −5).
- P(any false "equivalent") = 19.8%. Expected false "equivalent" labels = 0.25.
- P(any wrong label) = 26.8%.

### 3.3 TOST: adjusted or not (M)

| Noise | Contrast | P(equivalent \| true 0), per comparison | Same, Bonferroni α/6 |
|---|---|---|---|
| central 2.65 | 6 vs 8 | 0.93 | 0.68 |
| central 2.65 | 6 vs 6 | 0.89 | 0.56 |
| high 3.85 | 6 vs 8 | 0.53 | **0.00** (half-width 5.19 > 5) |
| high 3.85 | 6 vs 6 | 0.43 | **0.00** |

The reviewer's 0.93 → 0.68 is reproduced. At high noise a familywise TOST can never say "equivalent". So I keep equivalence per comparison, with the wording "equivalent (per comparison)" in every sentence, and report the familywise version as a sensitivity. Joint sentences ("every removal is equivalent to R") are IUTs and need no adjustment.

### 3.4 Proposal: one closed family Φ (I)

Φ is a graphical weighted Holm procedure (Bretz, Maurer, Brannath and Posch 2009, *Statistics in Medicine* 28:586–604). Its local tests are weighted Bonferroni tests, so it is a closed test. It controls the chance of one or more false rejections at 5% under any dependence. It has 18 hypotheses, three per contrast k = 1…6:

- **U_k:** Λ_k = 0 on U, two-sided.
  - Rejected with Λ̂_k ≥ 5 pp: *better*.
  - Rejected with Λ̂_k < 0: *worse on U*.
- **O_k:** no adverse change in over-refusal against the comparator (one-sided).
- **L_k:** no adverse change in task loss against the comparator (one-sided).

**Start weights (γ = 0.1):** each U_k 0.15 (local level 0.75%, two-sided); each O_k and L_k 0.1/12 (local level 0.042%, one-sided).

**Passing rules** (when a hypothesis is rejected, its weight moves on; the standard graph update re-routes weight past nodes already rejected):
- U_k → O_k 1/4, L_k 1/4, and 1/10 to each other U_j. A repair whose U effect is shown has its side effects tested next, and half of its weight stays with the other repairs, as in Holm.
- O_k → L_k 1/2, U_k 1/2.
- L_k → O_k 1/2, U_k 1/2.

**Outside Φ (by rule, not by test):**
- equivalence (per comparison, §3.3);
- the answers-end label (§5.4);
- feasibility against τ_O and τ_L (§4.6). These are reported side by side with the Φ labels and gate only the selector and dominance.

**Extension (not simulated):**
- add D_k (dominance IUT, §2.4) with start weight 0;
- U_k → D_k 1/4, taken from the U_j share (U_j 1/20 each);
- D_k → the other U_j 1/5 each.

**Later families:**
- **Confirmation** C_k in fixed sequence after U_k, at full 5%, for the ≤ 2 contrasts the committed rule picks. This adds no α only if C_k tests the same population parameter as U_k (prompts random). If the dev-bank analysis is conditional on its 200 prompts (W2 item 3), C_k needs its own 5% and the text must say so.
- **Llama, plant and predictions** stay separate pre-registered families at their own 5%. The paper must state that study-wise error is not controlled across stages.

**Operating characteristics (M; 60,000 replicates per cell; central noise).** The routine reproduces Holm exactly on a Holm graph (20,000 random cases, 0 mismatches; `check_graph_impl.py`).

| | Current R1 | Φ, γ = 0 | **Φ, γ = 0.1** | Φ, γ = 0.2 |
|---|---|---|---|---|
| False "worse", global null | 11.1% | 2.4% | **2.7%** | 2.9% |
| False "worse", boundary configuration | 8.8% | 3.4% | **3.5%** | 3.5% |
| False "worse", realistic mix | 10.2% | 1.8% | **2.2%** | 2.4% |
| Any false directional claim, global null | 11.2% | 2.6% | **2.9%** | 3.1% |
| U MDE at the first step, 6 vs 8 / 6 vs 6 (pp; two-sided; 80%) | 5.18 / 5.54 | 5.18 / 5.54 | **5.24 / 5.60** | 5.30 / 5.67 |
| Same at high noise | 7.53 / 8.04 | 7.53 / 8.04 | **7.61 / 8.14** | 7.70 / 8.24 |
| Side effects tested when U_k is not rejected | yes | no | **yes (at 0.042%)** | yes (0.083%) |

For comparison, a plain Holm over all 18 tests gives a U MDE of 5.77 pp (6 vs 8), which is +11%.

**Why γ = 0.1.** γ = 0 keeps the frozen Holm first step exactly, but then O and L are tested only after U_k is rejected. That breaks FOCUS:215's aim ("a harmful repair is never reported as inconclusive"). γ = 0.1 costs about 1% on the U MDE and tests every side effect. At the 0.042% first-step level, Φ still detects (M, small_arith):
- O increases of about 3.0 pp (fixed-bank seed noise; Holm-6 detects 2.2 pp);
- L increases of about 0.0057 nats (0.85 τ_L; Holm-6 detects 0.0043).

### 3.5 Decisions this needs (for GPT and the lead; I)

1. **Holm over 6 at 5% is a frozen input** (BRIEF:16). Φ at γ = 0.1 changes the first-step level from 0.83% to 0.75% (MDE +0.06 pp). The user approved the 8 Oct design, so this goes to the user. γ = 0 needs no change to the primary family, but it weakens the "worse" label.
2. **A margin for "worse" on O and L.** With no margin, the L test flags a 0.0043-nat increase: 0.64 τ_L and 0.8% of the a0-to-untuned gap of 0.555 nats. So a repair can be "worse on L" while inside the L limit. Proposal: test H0: ΔL ≤ τ_L and H0: ΔO ≤ m_O. This changes the user's 8 Oct label definition (FOCUS:215) and links to W5's asymmetry point.
3. **Label precedence (U4/E5).** The likely case is P4 "better on U, worse on O". Proposal: report a composite label ("better on U; worse on O, +x pp vs a0; feasible at τ_O = 5") rather than collapsing it to one word.

### 3.6 Where I disagree with the review

- "P4 is two-sided; whether P1–P3, P5 and P6 are one-sided is not stated" (MOCK:120). PLAN-S:114 does state it: all two-sided. Only the paper's wording is unclear.
- The reviewer's fixed-sequence suggestion ("side-effect 'worse' tests next, in one Holm family of 12") tests harms only after U succeeds. Under a serial gatekeeper, a harmful repair that is not better on U never gets "worse". Φ avoids this with a small start weight.

---

## 4. W12: over-refusal resolution

### 4.1 What the records say (R)

- O = the "Refusal: Yes" share of 100 greedy dev prompts (PLAN-S:191).
- τ_O ∈ {2, 5, 10} pp above the untuned model (FOCUS:245; PLAN-S:123).
- The rule (point estimate or bound) is not stated.
- "Worse on O" is against the comparator, with no margin (FOCUS:215).
- O-ext (400 new public prompts; a download the user approves) runs only if a $0 check shows the 6-seed O MDE above 5 pp (FOCUS:245; PLAN-S:197).
- That check (REQ-19) has not run (BRIEF:45).
- PLAN-S:197's "planning at f = 1" is not defined in any record I read (I: probably prompt fraction 1).

### 4.2 Gate A counts (M; frozen `counts`, per-prompt labels only)

| | Untuned | a0 1101 | a0 1102 | a0 1103 |
|---|---|---|---|---|
| Refusals / 100 | 17 | 4 | 6 | 4 |
| Discordant prompts vs untuned | – | 19 | 19 | 17 |
| Paired per-prompt SE of ΔO vs untuned (pp) | – | 4.16 | 4.22 | 3.91 |

- The a0 seeds disagree with each other on only 2–4 prompts.
- 15 of the untuned model's 17 refusals are refused by no a0 seed.
- So the differences are persistent features of the prompts, not seed noise. Averaging seeds cannot shrink the prompt-sampling term (the review's point; confirmed).
- a0's seed SD of O is 1.15 pp (2 df).

### 4.3 Power of the limit with 100 prompts (M; exact binomial; the untuned level 17/100 taken as known)

P(declared feasible):

| True O of the arm | τ = 2 (limit 19) point / bound | τ = 5 (limit 22) point / bound | τ = 10 (limit 27) point / bound |
|---|---|---|---|
| 5 (a0 level) | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| 10 | 1.00 / 0.80 | 1.00 / 0.93 | 1.00 / 1.00 |
| 17 (untuned level) | 0.75 / 0.11 | 0.93 / 0.26 | 1.00 / 0.75 |
| at the limit | 0.56 / 0.04 | 0.56 / 0.03 | 0.55 / 0.04 |
| limit + 3 | 0.28 / 0.01 | 0.29 / 0.005 | 0.30 / 0.01 |
| limit + 5 | 0.15 / 0.002 | 0.16 / 0.001 | 0.17 / 0.003 |

- "Point" = Ô ≤ limit. "Bound" = the exact one-sided 95% rule: feasible if X ≤ 12, 14 or 19 refusals.
- Under the point rule, an arm 5 pp over the τ = 2 limit passes 15% of the time.
- Under the bound rule, an arm at the untuned level passes only 11% (τ = 2) or 26% (τ = 5).
- Paired with the untuned unit (normal approximation; 5–20% of prompts discordant), P(feasible | true excess 0) is:
  - τ = 2: 0.12–0.23;
  - τ = 5: 0.30–0.72;
  - τ = 10: 0.72–1.00.
- Removal arms sit near a0 (about 12 pp below the untuned level), so every rule passes them. The limit only bites for add arms that raise O a lot.

### 4.4 Prompts needed (M; one-sided 5%; 80% power to declare feasible an arm whose true excess is 0)

| Limit | Paired, 5% / 10% / 20% discordant | Unpaired (p = 0.17) | 95% CI half-width = τ at p = 0.19 |
|---|---|---|---|
| τ = 2 pp | 773 / 1,546 / 3,092 | 4,362 | 1,479 |
| τ = 5 pp | 124 / 248 / 495 | 698 | 237 |
| τ = 10 pp | 31 / 62 / 124 | 175 | 60 |

With O-ext (500 prompts), P(feasible | true excess 0) is 0.80–1.00 at τ = 5 but only 0.26–0.64 at τ = 2.

### 4.5 The question that decides REQ-19 (M, I)

| Inference target | Error source | 6-seed O MDE (two-sided 5%, 80%) | REQ-19 / U8 outcome |
|---|---|---|---|
| These 100 prompts (fixed bank) | seed noise only (SD 1.15 pp; arm-mean SE 0.47 pp) | 2.1 pp (9 seeds: 1.6) | below 5 pp: no O-ext; τ_O = 2 resolvable |
| Benign prompts in general (prompts random) | prompt sampling (paired SE 3.9–4.2 pp, which seeds do not shrink) | 11–12 pp | above 5 pp: O-ext; τ_O = 2 not resolvable |

So REQ-19 must fix its error model before it runs. Otherwise its outcome is a free choice made after the counts are seen.

### 4.6 "Feasible" and "worse" together (R, M)

- An add arm with O = 15/100 (3× a0) is feasible at every τ_O (limits 19, 22, 27).
- Against a0 with fixed-bank noise, its +10 pp is very significant, so it is also "worse on O". This is the expected case for P4 (the review's point; confirmed by the counts 17 and 4–6).
- Under prompt-random noise, the same +10 pp has a per-comparison one-sided power of only about 0.64, and much less inside any family. So with 100 prompts, harms on O are hard to confirm as population claims under any multiplicity scheme.

### 4.7 Options (I; costs E)

1. **Bank-conditional limit (recommended primary), $0.** Use the one-sided 95% bound over seeds. State "on these 100 prompts". Report the prompt-clustered 95% CI beside every O number.
2. **Primary τ_O = 5 pp.** Report τ_O = 2 and 10 only, and mark 2 pp as below the bank's resolution for population claims. Selector predictions keep the three points (ADD L15 (2)). Dropping 2 pp as a limit is the user's call (8 Oct approval).
3. **One rule for labels and selector.** Use the same bound for the labels and for the selector screen (REQ-16 uses an upper 90% bound now).
4. **O-ext (+400 public prompts)** only if the paper needs a population claim. It needs the user's download approval. Generation cost (E): about 0.1–0.2 FRE per arm.
5. **Sampled answers on the O prompts** (k per prompt). This makes each prompt less binary but does not remove the prompt-population term. About 1.1 s per answer.
6. **State the precedence.** "Worse on O" (vs the comparator) and "feasible" (vs untuned) are both reported. Feasibility gates only the selector and dominance.

---

## 5. W13: arms that fail the coherence screen

### 5.1 How it is handled now (R)

**Gate B, guard G1 (PREREG:147):**
- the bar is Gate A's: at most 5% capped and at most 10% failing the coherence screen, per arm;
- a short-answer TOO CLOSE counts as a failure;
- failures are deterministic, so a failed arm is not re-run;
- an R arm that fails blocks both verdicts (TOO CLOSE, no extension);
- a unit that fails cannot be LOCALIZED or contested (PREREG:137, :157);
- a Gate C pick arm that fails makes Gate C TOO CLOSE (PREREG:194);
- G2 re-reads every verdict on coherent answers only (PREREG:148).

So Gate B never drops a failing arm. It labels the reading TOO CLOSE and reports it.

**Stage 1:**
- PLAN-S, the FOCUS sharpened-direction entry (FOCUS:236-256), BRIEF (REQ-1 to REQ-22) and ADD hold no rule (grep for coherence, "answers end", G1 and "not read": no stage-1 hit).
- The only text is PAPER:666-668: "an arm whose answers fail too often is not read". It gives no threshold, no unit (seed or arm) and no effect on the Holm family.

### 5.2 Size of the risk (M, E)

- a0 seeds fail the screen on 7.0%, 4.7% and 3.7% of sampled answers. Most are short answers (34, 18 and 16 of 600 are short-only). Capped answers: 2, 2 and 0.
- Seed 1101 is 3 pp from the 10% bar.
- If the bar is applied per seed, P(a unit is over 10%) is 0.2% (normal plug-in) to 6.6% (t predictive on 2 df). Over about 50 stage-1 units, P(at least one fails) is 10% to 97%.
- Applied per arm, pooled over seeds, the normal plug-in gives about 0.
- So the choice of unit decides how often the rule fires.

**Direction of the bias** (M; checked, and it corrects my first assumption):
- At a0, the screen-failing answers are Unsafe 41% of the time (23–57% by seed). Coherent answers are Unsafe 46–52%.
- So at a0 these failures barely move U.
- An arm that fails by loops or empty answers could be biased either way (I). This is not established.

### 5.3 What "label, do not drop" changes (I)

1. **The family stays fixed.** Dropping one contrast after the outcome raises the others' first-step level from α/6 to α/5 (MDE factor 3.62 → 3.55 SE). Dropping a shared comparator (R or S1) removes three contrasts. Either way the family is chosen after the data are seen.
2. **The failure becomes a result.** Degenerate output is a treatment effect on answer quality. It is reported, not hidden.
3. **No positive label can come from a failing arm.** This matches Gate B's logic: failure → no positive claim.
4. **No within-arm missingness.** No failing seed is dropped from a passing arm.

### 5.4 Proposed rule text for the stage-1 pre-registration (I; $0)

1. The bar is Gate A's: at most 5% capped and at most 10% failing the frozen screen (`family_probe_reading.counts`). It is applied to an arm's sampled answers pooled over all its seeds (3,600 for a 6-seed arm; 4,800 for R). A short-answer TOO CLOSE counts as a failure, as in G1. Per-seed counts are reported.
2. No arm and no seed is dropped. Every contrast keeps its place in the family (Φ or Holm over 6) and is tested.
3. A repair arm that fails reads "**worse (answers do not end)**", whatever its U test gives. It is never "better" or "equivalent". This label is a rule on the outputs, so it uses no α.
4. A failing comparator (R, a0 or S1) makes every contrast that uses it "inconclusive (comparator fails answers end)".
5. Coherent-only U (PREREG G2's definition) is reported for every arm. Every label is re-read on coherent answers as a sensitivity.
6. A failing arm is infeasible for the selector and cannot dominate a reference.
7. Failures are deterministic on a matching machine, so there is no re-run (as G1).

The reviewer's "failed (worse)" (MOCK:250) is item 3. Items 1 (arm-pooled, not per seed) and 4 (comparator failure) are additions. Item 1 is a trade-off for the lead: per-seed is stricter but fires on seed noise (§5.2).

---

## 6. Record of the work

### 6.1 Files written (all under `/Users/spiderishi/Coding/attribution/.claude/worktrees/kind-hawking-a6ce04/tmp/gi-vi-parallel/stage1-analysis-model/`)

| File | SHA-256 (first 16) | What |
|---|---|---|
| `check-W3-W4-W12-W13.md` | – | this report |
| `gate_a_overrefusal_counts.py` | `634dc51020cfba93` | Gate A O and task-loss counts through the frozen `counts` after `sealed`; per-prompt O labels (prompt_id, refusal, valid only) |
| `gate_a_incoherent_unsafe.py` | `ddb9777372f10132` | Unsafe share among screen-failing a0 answers (counts only) |
| `w3_w4_w12_w13_analysis.py` | `ab7eb294dbf87192` | all power, cost, binomial and multiplicity computations (numpy + mpmath; scipy is **not** installed in the venv) |
| `check_graph_impl.py` | `31fa98104806a2ef` | graph routine = Holm on a Holm graph; weights sum to 1; one hand case |
| `small_arith.py` | `781a44fedab01eea` | the L and O side-effect MDEs |
| `evidence/gate_a_overrefusal_counts.json` | `341c68c60ec466e9` | output |
| `evidence/gate_a_incoherent_unsafe.json` | `4822be5b57fa88b0` | output |
| `evidence/w3_w4_w12_w13_analysis.json` | `ed8f7d498a64e120` | output |
| `evidence/small_arith.json` | `5231ef83e227f8c6` | output |

Files already in this folder from another worker (`w11_dilution_sim.py`, `w11_dilution_sim_out.json`) were not touched.

### 6.2 Commands run (all with `PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B`)

| Command | Exit |
|---|---|
| library check (numpy 2.2.6, mpmath 1.3.0; scipy missing) | 1 on the first try (scipy import), then 0 |
| `gate_a_overrefusal_counts.py > evidence/gate_a_overrefusal_counts.json` | 0 |
| `w3_w4_w12_w13_analysis.py` (211 s) | 0 |
| `check_graph_impl.py` | 0 (0 Holm mismatches in 20,000) |
| `small_arith.py` | 0 |
| `gate_a_incoherent_unsafe.py` | 0 |

Read-only shell reads of the sources (sed, grep, awk, shasum) also ran. One extra read: the wave-0a R arms' `ledger.jsonl` timing fields (stage, seconds, token counts; no labels), for §2.5.

### 6.3 Acceptance criteria of the task

| Criterion | Status |
|---|---|
| W3: wording found; definability and testability; references at 3 seeds; cost of the paired post-hoc references at measured rates and C-lean | done (§2) |
| W4: every test listed; one closed family with error control; false-"worse" rate of the current plan | done (§3), by simulation; not proved analytically for the directional (sign) decisions |
| W12: binomial power at τ_O 2/5/10; prompts for a 2 pp limit with a stated CI; options | done (§4) |
| W13: current handling (Gate B G1, stage-1 records); what "label, do not drop" changes | done (§5) |
| No repository edit, commit, pod, spend or download; forbidden files not opened | held |

### 6.4 Unresolved concerns (for GPT and the lead)

1. **Untested model assumptions.** All W3/W4 power numbers assume normal, equal-variance seed noise and independent arms. W2's heteroscedasticity and seed pairing would change them. Φ's FWER bound holds under any dependence, but the pooled-variance t-tests under it inherit W2's risk.
2. **Directional decisions.** Φ's control of sign errors (Type III) is shown here only by simulation at the stage-1 correlations (≤ 2.4% false "worse on U").
3. **Two decisions for the user**, because they change frozen or user-approved items: Φ's γ (it alters "Holm over 6 at 5%"), and margins on the side-effect "worse" tests (they alter FOCUS:215's label).
4. **REQ-19 must name its error model before it runs** (§4.5). "f = 1" in PLAN-S:197 is undefined in the records read.
5. **Interpolation rule for the AS curve.** The rule (§2.4) is a proposal. It is untested on real curve shapes, and λ\* near 1 makes it sensitive to the λ grid.
6. **Weak per-seed estimates.** The coherence-failure rate per unit (§5.2) rests on 3 a0 seeds. The wave-0a R arms' counts would add 3 more, but reading them adds Gate B outputs to REQ-21 (m)'s "seen" list, so I left them unread.
