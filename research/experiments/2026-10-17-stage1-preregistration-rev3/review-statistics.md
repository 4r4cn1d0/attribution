# Statistics review: stage-1 pre-registration revision 3

**Status.** An adversarial statistics review for the main-study lead (GI VI). It is not a decision and it adopts nothing. It changes no frozen Gate B/C rule, no sealed record, not D5 = (a) and no user decision. Each fix below is a recommendation for the lead. Where a fix touches a decided text, the review says which text and who decides.

- **Reviewed file.** `stage1-preregistration-DRAFT-rev3.md` in this folder (SHA-256 `b31696deadc339ce`, 1,073 lines), called **REV3** below. Main checkout at HEAD `3536776` (R: `git rev-parse` at 14:32 UTC).
- **Written** 2026-10-17, about 14:15–14:40 UTC, by an Opus worker for GI VI. Clock checked with `date -u` at 14:16, 14:30, 14:32 and 14:36 UTC (the last at the end of writing).
- **Scope (from the brief).** HB-C's estimator, SE and df; Φ's error control with R1.3 as intersection–union nodes (proved and simulated); the D1 layout's pairs per contrast; the dominance test's three bounds; the labels' mutual exclusivity; the O bank's power at 500 prompts under both caps.
- **Data rules kept.** I opened no `selector.jsonl`, no `hidden/`, no held-out file, no `rows.jsonl`, no `groups.json` and no file with row, prompt, answer or anchor text. Every check below is a planning computation with no data input. The reused AMD code reads only `sim_w2_results.json` (a fitted bank summary and noise values).
- **No repo edit, commit, pod, spend or download.** Files written: this file and the `stat_review_*` scripts and outputs in this folder (§9).

**Labels.** **R** = read in a source (named). **M** = computed by a script named here ("M (here)"), or by a source's script ("M (VR-B)", "M (AMD)"). **E** = a planning estimate (basis named). **I** = inference or judgement. A Monte Carlo rate carries its Monte Carlo SE (MC SE) where it matters.

**Severity.** **MAJOR** = a rule text gives a wrong error rate or cannot be applied as written; fix before the W1 record. **MINOR** = a wrong or missing number, a gap, or a fix that makes a rule safer. **NIT** = wording.

---

## 0. Short answer

**What holds (M (here) unless marked).**
1. **HB-C's estimator is right.** Inside one cluster under D1 every arm runs at 1102–1107, and the 1101 cells sit alone at their seed. So the paired mean on the common seeds equals the REML/GLS estimate, and V_seed = (σ̂²_c + σ̂²_m)/J is its exact variance under the model (§1.1). The prompt part has no double count, and the Satterthwaite form is correct (§1.1).
2. **HB-C is near nominal under D1.** Worst-contrast size 4.5–4.9% at 5% and 0.65–0.74% at Φ's start level 0.75% (MC SE 0.15 and 0.06 points), in five noise worlds; 0.955% for a contrast of an arm with twice the SD at ρ = 0.76 (§1.2).
3. **Φ with R1.3's IUT nodes controls the family-wise error at 5%.** A short proof (§2.1); the shortcut equals the brute-force closed test (0 mismatches in 3,000 cases); family-wise error 0.3–4.9% in 27 named configurations and 3.8–4.4% for the five worst of 300 random configurations; zero impossible co-rejections (§2.2).
4. **The D1 pair counts in REV3 are right:** 6 pairs for every primary contrast, 3 for "block A only", 9 under plan B (§3).
5. **The headline word is unique and "worse" appears exactly when an adverse rejection exists** (420 logically possible test states enumerated; §5).

**What needs a fix.**

| Id | Sev. | REV3 place | Finding (one line) | Fix (one line) |
|---|---|---|---|---|
| ST-1 | MAJOR | §5.3, curve matched on L | The τ_L switch (λ\*_m = 1 if L̂(m) − L̂(a0) ≤ τ_L) uses a point estimate. Near the switch the U bound passes at its null up to 43–46% (I: two of three assumed curve shapes), not ≤ 5%. "Each test is then conservative" is false there | Switch to λ\* = 1 only when L is shown feasible (upper 90% end ≤ τ_L); read λ_lo at the upper 95% bound of L(m) − L(a0) and λ_hi at the lower bound. Then ≤ 4.0% in every simulated case |
| ST-2 | MAJOR | §3.6 LN-20 | LN-20 is right, and its fallback is not safe. AMD §A.8's θ0 form rejects 10.4% at a one-sided 5% level when ρ = 0.76, and 1.6–1.8% at F_k's 0.375% level with an item part equal to the seed part. The in-model cross-cluster form rejects 10.1% (two-sided 5%) in a two-cluster world. LN-20's forms stay at 4.8–5.2% | Adopt LN-20 at W1. Keep AMD §A.8 only as a printed sensitivity, not as the fallback |
| ST-3 | MAJOR | §3.2, §3.6 | The REML floor is "0.01 pp²". The L refit is in nats, where the a0 seed variance is about 5.6 × 10⁻⁶ nats². A literal floor of 0.01 puts every L variance at the floor, and L's SE becomes about 0.058 nats, 8.6 × τ_L | Give each endpoint its own floor (recommended: U, O 0.01 pp²; L 10⁻⁸ nats², the same ratio to the expected variance) |
| ST-4 | MINOR | §4.2 "Checks" | The cited family-wise checks (4.89%; 4.67–4.94%) are for the standard F_k edge with one-part O and L nodes, not for the graph in force. Also, "a single U node reaches the full 5%" is false under R1.3: F_k and O_k can never both reject, so U_k can reach at most 1.23% | Cite §2 of this review; state the maximum reachable levels (U 1.23%, O 0.30%, L 0.78%, F 0.64%) |
| ST-5 | MINOR | §3.3, §4.2 | "HB-C's P4 under D1 is not computed" is wrong: VR-B computed it. HB-C's df is about 5.5, not 8 | Replace with the M values of §1.3 |
| ST-6 | MINOR | §3.5 plan B | The full-corpus cluster has two arms (S1, S4). Their REML variances are not identified, only their sum. P6 then reduces to the paired t with 8 df. The a0 parts of L_k need a rule, because a0 is outside the fit | Write both rules (§3.3) |
| ST-7 | MINOR | §4.8 | "Confirmed" holds at ≤ 2.5% only on fresh prompts. A fresh-seed reading of the dev bank keeps the selected contrast's arm × prompt part | "Confirmed" is read on the hidden subsample only; the dev-bank reading is reported |
| ST-8 | MINOR | §4.3, §6.4 | "O_k rejects ⇒ infeasible state" and "F_k and O_k never both reject" need one estimate, one SE and one df for F_k, O_k's θ0 part and the printed state | Write that as a rule |
| ST-9 | MINOR | §4.5 | A significant adverse U shift inside ±5 pp: FR-19 gives "worse (U)". MSG-09's literal text ("a significant difference below δ … not as a label") gives a note only | FR-19 governs (a user decision). Read MSG-09 as the favourable case. Print the note beside "worse (U)" too |
| ST-10 | MINOR | §6.2, §6.4 | The O power rests on dev-like discordance. PHTest is a pseudo-harmful bank, so the discordance may be 30–40%. Branch 128 can add up to about 6 pp. "Worse (O)" power under R1.3 is not stated | Print the wider table (§6) and the "worse (O)" power |
| ST-11 | MINOR | §1.3 block A only | HB-C at 3 seeds: 1.5 residual df per arm, an arm at the floor in 98% of fits, df about 2, MDE 12.7 pp at the best noise | State these planning values in the block-A text |
| ST-12 | MINOR | §5.3 | The 3-seed fallback makes "beats" descriptive, so family 1b has no test then. λ = 1 (a0) and λ = 0 (θ0) need their variance forms | Write both (§4) |
| ST-13 | MINOR | §6.3 LN-12 | LN-12's fallback ("PHTest O at 1104–1107 only") makes an unbalanced J × P table. It leaves 2 seeds if R_4 and R_5 are reused | Use one seed set for all 500 prompts (§6.5) |
| ST-14 | MINOR | §3.2 | Floor events are frequent under HB-C (57–64% of D1 fits; about 17% per contrast) and harmless. The stop rule never meets 10⁻⁶ for a floored arm | State the expected rate; stop on the arms above the floor, or at 25 steps |
| ST-15 | NIT | §3.2, §3.4, §9.3, §4.6 | The prompt formula hard-codes 200 and 199; S-b2x's seed structure is unstated; Λ_tok's interval is not a formula; "best feasible repair" mixes error controls | §7 |

**A simpler alternative to raise (I).** The per-contrast paired t (J − 1 = 5 df; AMD's analysis "(b)") is exact under normality and needs no REML, no floor and no information matrix. At Φ's start level, its MDE is 6.7–7.4% above HB-C's under D1 (§1.3). LW-01 decided HB-C, and this review does not reopen it. I recommend the paired t as a printed sensitivity ("S-p"). It costs $0, and LN-20 already uses it for the cross-cluster pairs.

---

## 1. HB-C: estimator, SE and df (REV3 §3.1–§3.3, §3.6)

### 1.1 Derivation check (I, with the algebra stated)

- **Estimator.** Under D1, the full-corpus cluster has a0 at 1101–1107 and S1, S3, S4 at 1102–1107; the removal cluster has R at 1101–1107 and A1, L1, H1 at 1102–1107. The 1101 cells are alone at their (cluster, seed) level, so their seed effect absorbs them (leverage 1). The rest of each cluster is a complete 4 × 6 table. In a complete two-way table with fixed seed effects and one variance per arm, the GLS normal equations give μ̂_a = ȳ_a· − s̄̂ for every arm, whatever the weights. So μ̂_c − μ̂_m = ȳ_c· − ȳ_m·, the paired mean on 1102–1107. REV3's Λ̂_k is the REML/GLS estimate, not an approximation to it.
- **Seed part.** In the model, the seed effect cancels in U(c, j) − U(m, j). So Var(Λ̂_k) from the seed level is exactly (σ²_c + σ²_m)/J_k. V_seed,k = (σ̂²_c + σ̂²_m)/J_k is the plug-in value. Correct.
- **Prompt part.** Write D(j, p) = Λ + a_j + b_p + e_jp: a_j is the seed part of the difference, b_p is the arm × prompt part, and e_jp is the rest. Then E[MS_P] = σ²_e + J σ²_b and E[MS_E] = σ²_e, so (MS_P − MS_E)/(J P) estimates σ²_b/P. The cell-level residual already holds σ²_e/P and not b_p, because b̄ is constant over seeds and goes into μ_a. So V_prompt adds σ²_b/P only, with no double count. Correct.
- **df.** df_seed = 2V²_seed/Var̂(V_seed), with Var̂ from the inverse REML information on the σ² scale (AMD §A.4; the planning code `reml_hetero` returns that scale, R: code read). q = Σ (c_i MS_i)²/ν_i with c = ±1/(P J) and ν = (P − 1) and (P − 1)(J − 1). This is the standard Satterthwaite form. Correct.
- **HB-C factorizes.** No parameter is shared between the clusters. So "the eight σ²_a by REML" is two independent 4-arm fits with 15 residual df each, 3.75 per arm (M: VR-B design summary, and here). B16 may fit them apart. (NIT.)

### 1.2 Operating characteristics under D1 (M (here): `stat_review_hbc.py`, 20,000 replicates per world, seed-level cells; no arm × prompt term, so this is the seed part only, like S-0)

| World | Size at 5%, worst contrast | Size at 0.75%, worst | Median df P1 / P4 | Fits with an arm at the floor | Paired t (5 df): worst at 5% / 0.75% |
|---|---|---|---|---|---|
| Pair SD 1.84 pp (one shift, ρ 0.76) | 4.54% | 0.700% | 5.53 / 5.56 | 57.9% | 5.05% / 0.820% |
| Pair SD 3.75 pp (one shift, ρ 0) | 4.80% | 0.715% | 5.57 / 5.53 | 57.0% | 5.20% / 0.865% |
| Pair SD 4.5 pp (ρ 0) | 4.88% | 0.645% | 5.55 / 5.54 | 57.1% | 5.33% / 0.785% |
| Two clusters (shared 0.3, cluster 0.4) | 4.82% | 0.735% | 5.54 / 5.54 | 57.7% | 5.33% / 0.925% |
| A1 SD × 2, ρ 0 | 4.90% | 0.740% | 5.91 / 5.54 | 61.6% | 5.21% / 0.815% |
| S1 SD × 2, ρ 0.76 | 5.20% | **0.955%** | 5.54 / 5.46 | 64.3% | 5.06% / 0.835% |

(MC SE about 0.15 points at 5% and 0.06 points at 0.75%. The paired t is exact; its worst-of-six values show the selection effect of a maximum.)

- HB-C is near nominal. The one excess is the noisy-S1 world at 0.75% (0.955%; about 3 MC SE above 0.75%). This matches AMD §J.2's known slight excess for a noisy arm's own contrast. Φ's 5% is "approximate" to this degree, as REV3 §4.2 says.
- **Floor events (ST-14).** One arm of a given contrast is at the 0.01 pp² floor in about 17% of fits. Both arms are at the floor in none of 80,000 fits. Given one arm at the floor, the contrast's size is 5.13–5.28% at 5% and 0.69–0.77% at 0.75%; given none, 4.28–4.43% and 0.53–0.57% (M (here): `stat_review_hbc_floor.py`). So floor events are harmless, but they are not rare. Over all eight arms, 57–64% of fits show one. AMD §A.3 expected "about a quarter" under HB, and that does not transfer to HB-C. The record should say "expected in about half of all fits; no action".
- **The REML stop rule (ST-14).** For an arm at the floor, Fisher scoring keeps proposing a step below the floor, so "the largest step is below 10⁻⁶" never holds, and the routine stops at 25 steps (R: the planning code). Write: "stop when the largest step among arms above the floor is below 10⁻⁶, or after 25 steps".

### 1.3 Power under D1 (ST-5)

| | P1 / P4 / P5 MDE, 80%, at Φ's start level 0.75% | Holm MDE (as VR-B) | 80% "better" effect (Φ rejection and Λ̂ ≥ 5) | Paired-t MDE at 0.75% |
|---|---|---|---|---|
| Pair SD 1.84 | 3.85 / 3.87 / 3.84 | 3.76 / 3.79 / 3.75 | 5.64 / 5.65 / 5.64 | 4.11 / 4.15 / 4.11 |
| Pair SD 3.75 | 7.89 / 7.88 / 7.87 | 7.73 / 7.71 / 7.70 | 7.94 / 7.92 / 7.92 | 8.44 / 8.44 / 8.44 |
| Pair SD 4.5 (the plan-A cut) | 9.46 / 9.46 / 9.45 | 9.26 / 9.26 / 9.25 | 9.47 / 9.47 / 9.45 | 10.13 / 10.16 / 10.10 |
| Two clusters | 4.31 / 4.32 / 4.31 | 4.21 / 4.22 / 4.22 | 5.73 / 5.73 / 5.73 | 4.63 / 4.64 / 4.60 |

(M (here). VR-B's own D1 HB-C rows agree: Holm 3.76 / 3.77 / 3.78, 7.72 / 7.72 / 7.69 and 4.20 / 4.23 / 4.21; R: `verify/verify_hbc_out.txt`.)

- **REV3 §3.3 says "HB-C's P4 under D1 is not computed".** It was computed (VR-B, above). Under D1, P4 equals P1 to within 0.03 pp. Replace the sentence and add the rows. The "better" 80% effect under HB-C is 5.64 / 7.94 / 9.47 pp at pair SD 1.84 / 3.75 / 4.5, and REV3's "8–12% higher (I)" can become these M values. At pair SD ≥ 3.75, the "better" effect equals the MDE, because the MDE is above 5 pp.
- **df.** HB-C's median df is about 5.5 (10th percentile 5.0), not 8. So REV3 §4.2's "at about 8 df this raises the U MDE by 1.6%" becomes "at about 5.5 df, 2.0%" (M (here): t quantiles; 1.65% at 8 df).
- These are seed-part values. The arm × prompt term adds 13–22% in AMD's G1 and G2 scenarios (R: AMD §A.9).
- **P(equivalent | true 0) under HB-C D1** (M (here)): grade 1 / grade 2 = 1.00 / 0.99 at pair SD 1.84; 0.88 / 0.38 at 3.32; 0.77 / 0.25 at 3.75; 0.54 / 0.11 at 4.5 (P4 within 0.01). The plan-A/B record can print these.

---

## 2. Φ with R1.3 as intersection–union nodes (REV3 §4.1–§4.3)

### 2.1 Proof that Φ controls the family-wise error at 5% (I; standard results)

Let each node's p-value be valid: P(p ≤ u) ≤ u for every u ∈ [0, 1] when the node's null is true.

1. **The IUT p-value is valid for the union null.** O_k's null is A ∪ B, with A = {O(m) − O(c) ≤ 0} and B = {O(m) − O(θ0) ≤ τ_O\*}. If A is true, P(max(p_A, p_B) ≤ u) ≤ P(p_A ≤ u) ≤ u. The same holds if B is true. L_k is the same with τ_L against a0.
2. **The shortcut is a closed test.** Bretz, Maurer, Brannath and Posch (2009) show that the graph's sequential rule equals the closed test whose local test of an intersection H_J rejects when some i ∈ J has p_i ≤ α w_i(J), with Σ_{i∈J} w_i(J) ≤ 1. For the in-force graph (F_k → L_k 1): the weights sum to 1 and every row sums to 1 (exact fractions). On a 2-contrast copy (8 nodes), every intersection's weights sum to at most 1, the weights only grow as nodes leave (0 violations), and the shortcut equals the brute-force closed test in 3,000 of 3,000 random cases (M (here)).
3. **Bound.** Let T be the set of true nulls in the true state. A false rejection needs the closed test to reject H_T. So P(false rejection) ≤ Σ_{i∈T} P(p_i ≤ α w_i(T)) ≤ α Σ_{i∈T} w_i(T) ≤ α. The bound needs no assumption on the dependence.
4. **Logical links do not break it.** F_k's null (O(m) − O(θ0) ≥ 5) and O_k's B part (≤ 5) can both hold only at the boundary or together with A. Restricted intersections can only make the procedure conservative.

So Φ's 5% is exact if the component p-values are exact. It is approximate because HB-C's Satterthwaite t is approximate (§1.2), as REV3 already says.

### 2.2 Simulation of the graph in force (M (here): `stat_review_phi_iut.py`; z-level; 100,000 replicates per named configuration)

Model: per contrast, a U statistic (two-sided), the O comparator part and θ0 part, and the L comparator part and a0 part (one-sided, adverse positive). For P4 the two L parts are one estimate, shifted by τ_L/SE = 4.9. **F_k uses O_k's θ0-part estimate:** p_F = 1 − p_θ0. Three correlation sets: independent; "base" (U and the comparator parts: +0.5 for P1–P3, which share R; +0.5 for P5 with P6; −0.5 for P4 with P5 and P6; θ0 and a0 parts +0.3 across contrasts; +0.6 between the two parts of one node; +0.3 for other pairs inside a contrast); "strong" (base × 1.4, shrunk to stay positive definite).

| Configuration (truth in SE units) | Independent | Base | Strong |
|---|---|---|---|
| G0 global: U null; O, L, F at their boundaries | 4.45% | 4.13% | 4.16% |
| G1 U false; comparator parts at the boundary, other parts far false (IUT least favourable) | 1.87% | 1.87% | 1.76% |
| G2 U false; θ0 and a0 parts at the boundary, comparator parts false; F at the boundary | **4.92%** | 4.47% | 4.64% |
| G3 U false; F false (feasible arms); L comparator part at the boundary (the F → L edge feeds L) | 3.55% | 3.05% | 3.21% |
| G4 U false; F false; L a0 part at the boundary | 3.98% | 3.66% | 3.62% |
| G5 U and F false; L false except L_1 at its comparator boundary | 0.75% | 0.81% | 0.80% |
| G6 all false except O_1 (comparator boundary) | 0.32% | 0.30% | 0.29% |
| G7 U null; F false; O and L at the boundary | 4.36% | 4.03% | 4.21% |
| G8 three U false (their O false), three U null (their F false); L at the boundary | 2.64% | 2.62% | 2.54% |

(MC SE 0.02–0.07 points.) **Random search** (base set): 300 random mixtures of boundary, deep-null and false states at 4,000 replicates each. The largest was 5.05% (MC SE about 0.34). Re-run at 100,000 replicates, the five largest gave 3.81–4.37% (MC SE 0.06). **Logical checks over every run:** 0 replicates with F_k and O_k both rejected; 0 with O_k rejected while the per-comparison state is not "infeasible"; 0 with F_k rejected while the state is not "feasible".

(The numpy build prints spurious "encountered in matmul" warnings on this Mac. I checked that the correlated draws are finite and reproduce the target correlations within 0.012; R: run log.)

### 2.3 What changes in REV3 §4.2 (ST-4)

- **"Checks (M (AMD NUM; VR-B))".** 4.89% and 4.67–4.94% were computed with the standard F_k row (F_k → O_k 1/2, L_k 1/2) and with O_k and L_k as one-part tests (R: `verify/verify_extra.py` part C, `graph_spec`; the F statistics were separate draws with correlation 0.3). They do not test the graph in force. Replace them with §2.1–§2.2.
- **"A single U node reaches the full 5% level once the other 23 nodes are rejected."** That cannot happen under R1.3. p_F + p_θ0 = 1, so F_k and O_k never both reject, and at least one node per contrast always keeps weight. The largest local level each node can ever reach in the graph in force is: **U_k 1.229% (two-sided); O_k 0.302%; L_k 0.776%; F_k 0.639%** (M (here): `stat_review_phi_maxlevels.py`, maximised over all 2⁶ choices of F or O per contrast). Two consequences:
  1. Each contrast's test needs to be valid only up to these levels, not up to 5%. HB-C's behaviour at 0.75% (§1.2) is the check that matters.
  2. Later U steps get much less α than under Holm. With five other U nodes rejected (and their F_k), the last U node is tested at 0.98–1.15%, where Holm would test it at 5% (M (here)). REV3's "costs only the second and later U rejections" is true, but the size of that cost should be stated. UW-04 adopted these weights, so this is a fact for the record, not a change.
- **LN-22 (optional) has a mirror case.** After F_k rejects, O_k can never reject, but it still receives weight: L_k → O_k 1/2, and the re-routed U_k share. After U_k, F_k and L_k reject, O_k holds 0.553% that no test can use (M (here)). The F_k → L_k 1 edge closes only one of the three routes. Validity is not affected. I agree with REV3's "no change", because a fixed graph cannot know which of F_k and O_k will be rejected.
- **Plan-B Φ (LN-21).** The exact checks pass (weights sum to 1; every row sums to 1; start levels U 1.5%, O and L 0.083%; M (here), reproducing REV3).

---

## 3. The D1 layout: pairs per contrast (REV3 §1.2–§1.3, §3.5)

### 3.1 Counts (M (here): from the seed lists; the design objects in `stat_review_hbc.py`)

| Reading | Contrast | Common seeds | Pairs J | HB-C residual df per arm |
|---|---|---|---|---|
| Plan A, D1 | P1, P2, P3 (R against A1, L1, H1) | 1102–1107 | 6 | 3.75 |
| | P4 (a0 against S1) | 1102–1107 | 6 | 3.75 |
| | P5, P6 (S1 against S3, S4) | 1102–1107 | 6 | 3.75 |
| | a0 and R at 1101 | alone at their (cluster, seed) | — | 0 (absorbed) |
| Block A only | every contrast | 1102–1104 | 3 | 1.5 |
| Plan B | P1, P3 (R against A1, H1) | 1102–1110 | 9 | 5.33 (3 arms, 16 df) |
| | P6 (S1 against S4) | 1102–1110 | 9 | not identified (§3.3) |
| Cross-cluster pairs (LN-20 item 2) | a removal arm against a0 | 1102–1107 | 6 | — (paired, 5 df) |
| θ0 contrasts (LN-20 item 1) | method arm; a0 or R | its own seeds | 6; 7 | — (5; 6 df) |
| References (ambitious default) | m against SP, scaling, Safe LoRA (a0 1101–1107) | 1102–1107 | 6 | — |
| References (3-seed fallback) | m against a0 1101–1103 transforms | 1102–1103 | 2 | — (S-aW, descriptive) |
| Token axis | Ḡ_600 = U(a0) − U(R) | 1101–1107 | 7 | — (cross-cluster) |
| R_tok | Ḡ_m − Ḡ_Rtok,m | 1102–1104 | 3 | — |

REV3's statements hold: 50 cells, 44 new, 6 reused; every primary contrast has 6 pairs; block A only gives 3. Statistically, REV3's seed-complete block layout and D0's per-block counts (the fallback) give the same 3 pairs in block A. The layout choice moves one R run between blocks and changes no estimate (I).

### 3.2 Block A only (ST-11; M (here))

HB-C at 3 seeds has 1.5 residual df per arm. In 98% of fits some arm is at the floor. The median df is 2.0. The test is conservative: size 2.9–3.9% at 5% and 0.27–0.37% at 0.75%. The MDE at 0.75% is 12.7 pp at pair SD 1.84. At pair SD 3.75 it is above 25 pp (Holm: 24.8 pp). The paired t (2 df) is exact, but its MDE is larger (15.4 pp at 1.84). So HB-C stays valid in block A, and it is the better choice there. **A "block A only" reading can say "better" only if the pair SD is near the wave-0a value and the effect is at least about 13 pp.** REV3 already prints block A's MDE; add these planning values to the text.

### 3.3 Plan B (ST-6; I, with proof)

- **The two-arm cluster.** Under plan B the full-corpus cluster holds only S1 and S4 (a0 is outside the fit; LW-31). With seed fixed effects, every REML error contrast in that cluster is a function of d_j = y(S1, j) − y(S4, j) alone. So the likelihood depends on σ²_S1 + σ²_S4 only, and the split between the two arms is not identified. The information matrix is singular along (1, −1). The contrast's variance needs only the sum. So **P6 under HB-C equals the paired t on 9 pairs with 8 df.** Write that into §3.5, so that B16 neither fails nor prints an arbitrary split. REV3 §3.8 already lists the "two-arm case" test.
- **The a0 parts.** a0 is outside the plan-B fit, but L_k's a0 part (L(m) − L(a0) ≤ τ_L) and the feasibility states still need a0. Recommended (I): use the pair's own paired variance on the common seeds 1102–1107 (6 pairs, 5 df) plus the item part, which is LN-20 item 2's form.

---

## 4. The dominance test's three bounds (REV3 §5.3)

**What holds (I).**
- **"m beats r" is an IUT.** Its null is the union {U(m) − U(r) ≥ 0} ∪ {O(m) − O(r) ≥ 5} ∪ {L(m) − L(r) ≥ τ_L}. Requiring each one-sided 5% bound gives a valid 5% test. D_k (beats every built reference) takes the largest component p-value. Holm over D_1…D_6 is valid.
- **"m beats r" and "r beats m" are exclusive.** Both would need upper(U(m) − U(r)) < 0 and upper(U(r) − U(m)) < 0, which cannot hold together, because the U margin is 0. The O and L margins are positive, so non-inferiority in both directions can hold, and that is harmless.
- **The cross-cluster form** (a removal arm against a full-corpus reference: the pair's own variance, J − 1 df) is valid; the part-D numbers in §7 (ST-2) support it.

**ST-1 (MAJOR): the curve matched on task loss is not conservative near the τ_L switch.** REV3 reads λ\*_m at L̂(m) and sets λ\*_m = 1 if L̂(m) − L̂(a0) ≤ τ_L, so the U bound is then tested against a0 itself. If the true rise is just above τ_L, the rule's own target is the curve point at that rise, which has lower U than a0. But L̂ falls at or below τ_L in about 46% of draws (SE_L = 0.00137 nats ≈ τ_L/4.9). In those draws the U bound is tested against a0 instead.

Size of the effect (I for the curve shapes, M (here) for the rates): L rise(λ) = 0.5548 (1 − λ)^p nats and U drop(λ) = 45 (1 − λ) pp. At the boundary of the U bound's null against the rule's target point (a valid one-sided 5% test gives ≤ 5%), the largest pass rates are:

| L curve shape | Target U drop at the switch | As written: largest pass rate (pair SD 1.83 / 3.75) | Fixed rule (pair SD 1.83 / 3.75) |
|---|---|---|---|
| p = 1 | 0.56 pp | 8.5% / 4.6% | 1.3% / 1.3% |
| p = 1.5 | 2.40 pp | 43.4% / 21.7% | 3.9% / 2.0% |
| p = 2 | 5.00 pp | 46.0% / 43.6% | 4.0% / 3.8% |

(The same values hold with and without λ = 0.9 on the grid. Source: `stat_review_curve_labels.py`, 400,000 draws per point.)

The curve's shape is unknown before stage 1. A slowly rising L near λ = 1 (p ≥ 1.5) is plausible, because τ_L is only 1.2% of the θ0-to-a0 gain (R: REV3 §6.7). The fault is a jump in the target: the reference point moves from a0 to the matched point at a threshold that a point estimate decides.

**Recommended rule text (I; for LN-15b):** "λ\*_m = 1 only if L(m) − L(a0) is shown feasible at τ_L (the upper end of its two-sided 90% interval is at most τ_L). Otherwise read λ_lo on the curve at the upper end of that interval, and λ_hi at its lower end." This keeps the "matched on task loss" idea. It makes the bracket conservative in at least 95% of draws, and it costs little: a repair whose true rise is τ_L/2 still switches to λ\* = 1 in 79% of draws (E: Φ(2.45 − 1.645)). Under this text the test's level is at most the U bound's 5% plus a 5% chance of a wrong bracket, and the simulated level stays ≤ 4.0%. Say "approximately 5%" in the record.

**ST-12 (MINOR): two gaps in the variance text.**
1. The curve's end points: λ = 1 is a0, which the reference fit leaves out, and λ = 0 is θ0, which has no seed. Write: "against AS(1) = a0, use the primary fit (a full-corpus arm) or the cross-cluster pair form (a removal arm); against AS(0) = θ0, use LN-20 item 1".
2. The 3-seed fallback: REV3 says "beats" is then descriptive. Say what follows for family 1b: "Under the fallback, family 1b is not tested, and no sentence says that a data repair dominates or beats model-level repair." The rule in §5.2 ("only if a data repair dominates in family 1b") then blocks the claim, and the reader should be told why.

---

## 5. The labels' mutual exclusivity (REV3 §4.5–§4.6)

**Enumeration (M (here): `stat_review_curve_labels.py` part 2).** States: U (none, favourable, adverse) × Λ̂ (≥ 5, between 0 and 5, < 0) × grade 1 × grade 2 × O_k × L_k × F_k × the O state (3) × coherence (3). The logical exclusions: grade 2 ⇒ grade 1; grade 1 ⇒ Λ̂ < 5; F_k and O_k not both; O_k ⇒ "infeasible"; F_k ⇒ "feasible". That leaves 420 states.
- Exactly one headline word per state: yes. "Worse" iff U, O or L rejects adversely: yes. Word counts: worse 288, equivalent 72, inconclusive 48, better 12.
- "Better" with an equivalence grade: 0 states. This cannot happen, because the upper 90% end below 5 forces Λ̂ < 5.
- Allowed co-occurrences, both printed as REV3 says: "worse (U)" with an equivalence grade (60 states); "worse (O or L)" with a U part that reads "better" (18 states); the favourable "significant, below the smallest effect of interest" note with grade 1 (60 states).
- Coherence flags and feasibility never change the word: confirmed by construction.

**ST-8 (MINOR): one SE for three outputs.** "F_k and O_k never both reject" and "O_k rejects ⇒ the printed state is 'infeasible'" both rest on p_F + p_θ0 = 1. That identity holds only if F_k, O_k's θ0 part and the printed state use one estimate, one SE and one df. With a 2× SE difference, the implication fails in 2,988 of 200,000 draws (M (here)). LN-20 item 1 already names all three uses ("O feasibility; R1.3's θ0 part; the selector screen's O"). Write it as a rule: "F_k, O_k's θ0 part, the per-comparison O state and the screen use one estimate, one SE and one df; the same holds for L_k's a0 part and the L state." It must hold under LN-20's fallback too.

**ST-9 (MINOR): a conflict between two decided texts.** A U contrast that is significant in the adverse direction with |Λ̂| < 5 pp (the 90% interval inside ±5): FR-19 (the user, 8 Oct) gives "worse (U)", with no size condition. MSG-09 (the lead, 17 Oct) reads literally "a significant difference below δ is printed in the row as 'significant, below the smallest effect of interest', not as a label". REV3 applies MSG-09 to the favourable direction only. That follows the precedence of REV3 §0.3 (a user decision first). The reading is not written down. Recommended (I): REQ-21 (h) records "MSG-09 restates UW-08's row note for the favourable direction; FR-19 governs the adverse direction". The row also prints the note beside "worse (U)" when |Λ̂| < 5 pp, so that a reader sees the size. The word does not change.

**NIT (ST-15).** "The best feasible repair" (REV3 §4.6) joins a Φ-controlled U claim, a Φ-controlled O claim (F_k), a per-comparison L state and a report-only separation rule. Its error rate is not 5%. One sentence in §4.6 should say so.

---

## 6. The O bank's power at 500 prompts under both caps (REV3 §6.2–§6.5)

Method (E, normal approximation; `stat_review_o_power.py`): q = the share of prompts on which the arm's flag and θ0's differ. Item part √((q − Δ²)/P); seed part σ_s²/J with J − 1 df (LN-20); Satterthwaite df. The calculation reproduces AMD §E.3 at P = 500 (1.00 / 0.97 / 0.80 per comparison; 0.99 / 0.80 / 0.43 inside Φ, at q = 5 / 10 / 20%; REV3 prints 0.81 for the second Φ value).

### 6.1 Feasibility, an arm at θ0's level (Δ = 0), P = 500, J = 6

| Seed SD of O; extra discordance from the cap | Per comparison (5%), q = 5 / 10 / 20 / 30 / 40% | Inside Φ (F_k at 0.375%), same q |
|---|---|---|
| 0 pp; Branch full | 1.00 / 0.97 / 0.80 / 0.65 / 0.55 | 0.99 / 0.80 / 0.43 / 0.26 / 0.18 |
| 1.15 pp; Branch full | 1.00 / 0.96 / 0.78 / 0.64 / 0.54 | 0.96 / 0.75 / 0.40 / 0.25 / 0.17 |
| 1.15 pp; Branch 128, +3 pp | 0.98 / 0.91 / 0.74 / 0.61 / 0.51 | 0.84 / 0.61 / 0.34 / 0.22 / 0.16 |
| 1.15 pp; Branch 128, +6 pp | 0.94 / 0.85 / 0.69 / 0.57 / 0.49 | 0.70 / 0.51 / 0.30 / 0.20 / 0.15 |

- **The seed part costs little at 500 prompts** (0.80 → 0.75 at q = 10% inside Φ), as REV3 says.
- **The discordance is the open quantity (ST-10).** REV3's planning values assume that PHTest prompts "behave like dev prompts". PHTest was built from prompts that models refuse wrongly, so θ0's refusal there, and an arm's departure from it, may be much larger than on the dev 100 (I; UNVERIFIED until θ0's 500-bank run). At q = 30–40%, F_k inside Φ succeeds for an arm at θ0's level with probability 0.17–0.26. "Within the over-refusal limit" sentences would then be rare even for good add arms.
- **The cap (I).** Branch full adds no flag noise. Under Branch 128, W1-18's bar lets up to 3 of 100 flags per unit change. If those changes fall on different prompts for the arm and for θ0, the discordance rises by up to about 6 pp. At q = 10% inside Φ, that lowers the power from 0.75 to 0.51–0.61. If the changes fall on the same prompts (late refusals cut in both), the rise is near 0. LN-14's PHTest transfer report measures this for θ0. Recommended: the cap record prints the measured flag-change share per source, and the plan-A/B record prints F_k's planning power at the measured q.
- **The REQ-19-type 6-seed O MDE at 500 prompts** (one-sided 5%, 80%): 4.71 pp at the dev-like q = 16.8%, 6.21 pp at q = 30% and 7.14 pp at q = 40% (P = 100: 10.34 pp at 16.8%; REQ-19 measured 11.04 pp; R: FO-05). So the 500-prompt bank brings the MDE below 5 pp only if the PHTest discordance is below about 19%.
- **τ_O = 2 pp** stays out of reach: 0.56 / 0.38 / 0.25 per comparison at q = 5 / 10 / 20%. REV3's "below the bank's resolution" is correct.

### 6.2 R1.3 "worse (O)" (the θ0 part; the comparator part assumed to pass)

| True excess over θ0, Δ | 7.5 | 10 | 15 | 20 pp |
|---|---|---|---|---|
| Start level 0.042% (U_k not rejected), q = Δ | 0.08 | 0.55 | 1.00 | 1.00 |
| After U_k, 0.135%, q = Δ | 0.14 | 0.69 | 1.00 | 1.00 |
| After U_k, 0.135%, q = Δ + 10 pp | 0.04 | 0.30 | 0.94 | 1.00 |
| Per comparison 5%, q = Δ | 0.63 | 0.97 | 1.00 | 1.00 |
| P = 100, after U_k, q = Δ | 0.02 | 0.08 | 0.38 | 0.74 |

(E; seed SD 1.15 pp.) REV3 does not state this. Under R1.3, "worse (O)" needs a true excess well above θ0 + 5 pp. It is likely only from about θ0 + 15 pp. An arm 2.5 pp above the bar reads "worse (O)" with probability 0.08–0.18 inside Φ. That is the intended price of R1.3 (no false "worse (O)" for an arm that returns to θ0's level). The paper should say it in one sentence. AMD §E.3's "worse (O)" power of "about 1.00 on 500" is for a +10 pp rise against the comparator, so it measures the comparator part only (I).

### 6.3 The bank is a 4:1 mix of two sources (MINOR; I)

The prompts-random SE treats the 500 prompts as one sample. They are two fixed strata (100 dev, 400 PHTest) with equal prompt weights (LN-24). If the contrast's mean differs between the sources, MS_P absorbs that difference, so the SE is slightly conservative. The inference reaches "new prompts from this 4:1 mix", not from either source alone. Recommended: one sentence in §6.2. Per-source O is already reported (ADD-7.4).

### 6.4 "Worse (L)" reach (MINOR; E)

For a removal arm, L_k's a0 part is a cross-cluster pair with 5 df (LN-20). The one-sided t quantile is 5.51 at 0.135% and 7.15 at 0.042% (M (here)). So "worse (L)" needs L(m) − L(a0) above τ_L + 5.5 SE, about 0.0143 nats if σ = s. That is 2.1 × τ_L. Under the 2-df caveat of REV3 §6.7 it may be much more or much less. One sentence in §6.7.

### 6.5 LN-12's fallback makes an unbalanced table (ST-13)

The fallback reads: "P1–P3's O contrasts on the 400 PHTest prompts use seeds 1104–1107 only". Then the dev-100 prompts have 6 seeds and the PHTest prompts 4, and the J × P table behind the item part is not balanced. If R_4 and R_5 are reused (LW-32) and not regenerated, only 1106–1107 remain. Recommended (I): under the fallback, P1–P3's O comparator part uses one seed set for all 500 prompts: the R seeds with 500-bank answers, among 1104–1107. The record prints J. If fewer than 3 seeds remain, the O comparator part of P1–P3 is "not tested", and O_k's IUT cannot reject.

---

## 7. Smaller points

- **ST-3 (MAJOR), the L floor.** REV3 §3.2 fixes "floor 0.01 pp²", and §3.6 refits HB-C on L, whose cells are in nats. s² = (0.0023749)² = 5.6 × 10⁻⁶ nats² (R: REV3 §6.7). A floor of 0.01 would floor every L arm, and the L contrast's SE would be about √(0.02/6) = 0.058 nats, 8.6 × τ_L. Every L state would read "undetermined", and "worse (L)" could never reject. Recommended: endpoint floors fixed now. U and O: 0.01 pp². L: 10⁻⁸ nats² (0.18% of s², near U's ratio of 0.01 to about 7 pp²). A relative floor, 10⁻³ × that endpoint's pooled residual mean square, is an equal option.
- **ST-2, details.** M (here), `stat_review_hbc.py` parts C and D, 20,000 replicates.
  - θ0 contrast, one-sided rates at the boundary null (nominal 5% and 0.375%). AMD §A.8 form: ρ = 0 and no item part 1.47% / 0.00% (conservative); ρ = 0.5, item = seed part 7.4–7.7% / 1.05–1.15%; ρ = 0.76, no item part 10.4–10.5% / 0.45–0.47%; ρ = 0.76, item = seed 9.6–9.8% / 1.62–1.79%; ρ = 0.76, item = 4 × seed 6.5–6.6% / 0.63–0.79%. LN-20's form: 4.8–5.2% / 0.29–0.52% throughout.
  - Cross-cluster pair (A1 against a0), two-sided: the in-model form is 1.9% at 5% if one shift holds, and 10.1% at 5% (0.98% at 0.75%) in the two-cluster world. The pair's own form is 4.9–5.1% (0.68–0.79%).
  - So the fallback "AMD §A.8 as written, with the omission stated" is liberal by up to 2× at the per-comparison level and up to 4.8× at F_k's level, exactly in the high-coupling world that wave 0a suggests (ρ 0.76; R: REV3 §12.1). At 500 O prompts with dev-like discordance, the item part is about 15 × the seed part (I: 3.35 against 0.22 pp²), so the excess is small for O there. For L, and for O at low discordance, it is not small. Adopt LN-20, and keep AMD §A.8 only as a printed sensitivity.
  - LN-20 costs no df: 5 (or 6) df against the in-model 3.4–5.5.
- **ST-7, confirmation.** FR-16 and LS-18 decide "confirmed" by "the primary model on the fresh seeds". US-09 (a) reads both banks (R: CONS). On the dev bank, the fresh seeds are new but the 200 prompts are the ones whose arm × prompt part helped pick the contrast (the pick rule takes the largest |t|). That part stays, so a null contrast is "confirmed" there with probability above 2.5% (I; the size depends on σ²_b, which adds 13–22% to the MDE in AMD's G1 and G2). Recommended: "confirmed" is decided on the hidden subsample only, and the dev-bank reading is printed as "same prompts as the selection".
- **ST-15, the prompt formula.** REV3 §3.2 writes 200 prompts, 199 df and 199 (J − 1) df. For O (P = 500) and L (200 rows) write P, P − 1 and (P − 1)(J − 1).
- **ST-15, S-b2x.** REV3 §3.4 says "seed-blocked, one pooled residual". Say whether the seed effect is one shift (HB's structure; 36 residual df under D1) or one per cluster (30 df).
- **ST-15, Λ_tok's interval.** REV3 §9.3: the curve mixes R_600 at 1101–1107 with R_1200 and R_2400 at 1102–1104, and "its interval from S-tok" is not a formula. Recommended: compute Λ_tok and its interval on the common seeds 1102–1104 (every arm in the combination paired), report only.
- **Directional errors.** The wrong-sign rate (0.05–0.98%) was simulated on the standard graph (R: VR-B part C3). The U nodes are the same in the graph in force, so I expect the same values (I). Not re-run.

---

## 8. Limits and what I did not check

- The HB-C simulations are seed-level (normal cells, no arm × prompt term). The prompt part's estimator was checked by algebra (§1.1), not by an answer-level run. AMD's answer-level runs cover HB, not HB-C.
- The Φ simulation is z-level. It tests the graph and the IUT logic, not HB-C's t-approximation; §1.2 covers that separately.
- The curve shapes in §4 and the discordance values in §6 are assumptions (I). The rates under them are M.
- I did not read B16 (not built) or the built selector code. I did not run AMD's or VR-B's scripts. I reused their routines read-only (`reml_hetero`, `Design`, the t functions) through `stat_review_hbc.py`.
- The O power is a normal approximation. It ignores flag changes between an arm's six seeds (conservative for the item part) and the U–O correlation.
- Not checked: the selector's statistics (§7 of REV3), the planted-sweep rules (§8), and costs. The brief did not ask for them.

---

## 9. Record

**Commands run (venv Python 3.11.15 with numpy 2.2.6, `-I -B`, unless marked).**

| Command | Exit | Notes |
|---|---|---|
| `date -u` (14:16, 14:30, 14:32 and 14:36 UTC) | 0 | clock |
| `git -C <main> rev-parse --short HEAD` | 0 | `3536776` |
| `shasum -a 256` of REV3 and of my files | 0 | REV3 `b31696deadc339ce` |
| `stat_review_phi_iut.py` | 0 | 301 s; spurious matmul warnings, checked (§2.2) |
| `stat_review_hbc.py --reps 20000` | 0 | 466 s |
| `stat_review_hbc_floor.py --reps 20000` | 0 | add-on |
| `stat_review_o_power.py` (system `python3 -I -B`) | 1, then 0 | first run: a math-domain error at t = 0 in my t tail; fixed, then re-run |
| `stat_review_curve_labels.py` | 0, 0 | the second run after the two-SE example changed from 1.6× to 2× (1.6× could not break the implication) |
| `stat_review_phi_maxlevels.py` | 0, 0 | the second run added the "realistic sequence" lines |
| inline diagnostics (finite draws; per-arm θ0-contrast counts) | 0 | not saved; they confirmed the saved results |
| reads: REV3 (full), AMD (full), the ledger rows, VR-B's `verify_hbc_out.txt` and the Part C code, the AUDIT §3 table, CONS US-09 and LS-18 | 0 | — |

**Files written (this folder only).** `review-statistics.md` (this file) and:

| File | SHA-256 (first 16) |
|---|---|
| `stat_review_phi_iut.py` → `_out.txt`, `_results.json`, `_run.log` | `042316dc0d3f09ab` → `461ee08ce4e65627`, `a13f26a24e5a4659`, `d8ee06ae923b7806` |
| `stat_review_phi_maxlevels.py` → `_out.txt` | `5138848157949210` → `c7ff8ed478664a37` |
| `stat_review_hbc.py` → `_out.txt`, `_results.json`, `_run.log` | `aa2e64995f83215c` → `a8e343cca3853471`, `52a7fc14309dd9d2`, `a99c363ddba71138` |
| `stat_review_hbc_floor.py` → `_out.txt`, `_results.json`, `_run.log` | `de498d29fa825aee` → `c1e047b7e2766a52`, `db3814ce37f6eaba`, `ee3263b753b39fdf` |
| `stat_review_o_power.py` → `_out.txt`, `_results.json` | `884f4bd4dcd5b266` → `7af943d7e5bc1dba`, `bdf2f26a0600b4b3` |
| `stat_review_curve_labels.py` → `_out.txt`, `_results.json` | `798110d84b592b6d` → `74ec74c0069f7a9b`, `a5d431e2b1034030` |

`review-consistency.md` in this folder is another worker's file. I did not open or change it beyond its first three lines.

**Acceptance against the brief.**

| Brief item | Status |
|---|---|
| HB-C's estimator, SE and df | done: derived (§1.1), simulated under D1 and block A (§1.2–§1.3, §3.2); findings ST-3, ST-5, ST-14 |
| Φ's error control with R1.3 as an IUT node, proved or simulated | done: both (§2.1–§2.2); ST-4 |
| The D1 layout's pairs per contrast | done (§3.1); ST-6, ST-11 |
| The dominance test's three bounds | done (§4); ST-1, ST-12 |
| The labels' mutual exclusivity | done (§5); ST-8, ST-9 |
| The O bank's power at 500 prompts with both caps | done (§6); ST-10, ST-13 |
| Write `review-statistics.md` here; no repo edit; no data | done |

**Unresolved concerns for the lead.**
1. ST-1 and ST-2 change recommended rule texts (LN-15b, LN-20). Both are lead items at W1, at $0.
2. ST-3 needs a number for the L floor before B16 is built (S1). The rule text belongs in the W1 record.
3. ST-9 needs the lead's written reading of MSG-09 against FR-19. Changing FR-19 itself would be a user decision; this review does not propose that.
4. The O bank's real discordance on PHTest decides whether F_k can ever be shown inside Φ (§6.1). It is known only after θ0's and a0's 500-bank runs (block A).
5. The Φ weights (UW-04) give later U steps at most about 1.2% (two-sided). This is a user-adopted design, stated here as a fact (§2.3); no change proposed.
