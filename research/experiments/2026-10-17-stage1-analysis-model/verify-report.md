# Verify report: the stage-1 analysis-model draft (revision 1)

**What this is.** An adversarial check of `stage1-analysis-model-DRAFT.md` revision 1 (SHA-256 prefix `e689d8e31b87f874`, byte copy kept as `verify/stage1-analysis-model-DRAFT-rev1-before-verify.md`). Written for the main-study lead (GI VI) by an Opus verify worker, 2026-10-16 23:42 UTC to 2026-10-17 00:24 UTC (clock checked with `date -u` at 23:42, 00:03, 00:12, 00:13, 00:23 and 00:24 UTC). The fixes below are applied to the draft in place (now revision 2); its new last section "Verify changes" lists each edit.

**Limits of this work.** Read-only on the repository. No repository edit, commit, pod, spend or download. I opened no `selector.jsonl`, no `hidden/`, no held-out file, no wave-0b `rows.jsonl` or `groups.json`, and no Gate B unit arm. I printed no prompt, answer or prompt id. I did not recompute Gate A counts from evaluation records: the draft's inputs (`sim_w2_results.json`, `evidence/gate_a_overrefusal_counts.json`) already hold them, and I used those files. I did not check the sibling drafts REF and RB beyond the rulings the draft cites (RB R1.1–R1.5, R1.8, R5b.1–R5b.2). I did not check the CK-2, CK-3 and CK-11 numbers that the draft only cites (R).

**Labels.** R = read in a source. M = measured or computed here (script named). E = estimate from a simulation. I = inference or judgement.

---

## 1. Verdict

- **The numbers hold.** The simulation re-runs byte for byte. Every number in the draft's tables that comes from SIM or NUM matches its output (M; §2). I found no arithmetic error.
- **The testing family Φ is valid as a procedure** (I, proof in §3.1; M, four checks in §3.2). Its error control is exact only for exact p-values. HB's p-values are near nominal, not exact (§3.3).
- **Four MAJOR findings** change rule text or the record (§6): missing silent defaults on [USER] items that change frozen inputs (V-1); an incomplete and partly false blinding line for REQ-21 (m) (V-2); the one-seed-shift assumption across the two arm clusters, which the draft's power claims rest on (V-3); and a matched-L reference rule that is not conservative for over-refusal (V-4).
- **No finding blocks the draft.** No frozen Gate B rule is changed. Each MAJOR finding has a fix that I applied. V-3 is also an open trade-off for GPT (§7).

---

## 2. Reproduction and number check

### 2.1 Re-runs (M)

| Run | Result |
|---|---|
| `stage1_model_sim.py --reps 20000`, a byte copy run in `verify/rerun/` (850 s) | `stage1_model_sim_results.json` **byte-identical** to the draft's (SHA-256 `ccf202311899370f`); the text output differs only in timing lines |
| `stage1_numbers.py`, a byte copy run in `verify/rerun/` | `evidence/stage1_numbers.json` **byte-identical** (`80ae7caa7406a7a6`); stdout identical |
| Input hashes | Every SHA-256 prefix in the draft's "Short names" table matches (FOCUS, PLAN-S, PREREG, both NG files, BRIEF, ADD, MRA, REF, CK-2, CK-3, CK-11, SIM and NUM with their outputs). RB is pinned by commit only; not hashed |
| Library claim | numpy 2.2.6 present; `import scipy` fails in the pinned venv (confirmed). The draft's own t/F/χ² functions pass their self-test (max error 2.36 × 10⁻⁶) |

### 2.2 Numbers checked against the outputs (M)

| Draft place | Claim | Check |
|---|---|---|
| §A.9 false-positive table | 13 scenarios × 6 analyses (FWER / worst single) | all 78 pairs match the output (rounded) |
| §A.9 note | N6 3.8 / 0.72; N8 4.0 / 0.84; D1 3.3–4.2 / 0.74–1.08 | match |
| §0, §A.10 | HB family-wise 3.0–4.6%, worst single 0.68–1.08% over 19 scenarios | match (3.00–4.64; 0.68–1.08) |
| §A.9 MDE table | 5 noise rows × 7 columns | all match |
| §A.6 D0/D1 table | 9 MDE triples; FW 3.5–4.0% and 3.6–4.2% | match |
| §A.4 | median df 8 (P1, p10 5.6) and 7 (P4) | match (N4: 8.0, 7.2; p10 5.6) |
| §A.3 | HB0 8.0% and 14.6% in G1, G2 | match (7.96, 14.62) |
| §A.9 | direct vs shift power 0.431/0.982/0.946 vs 0.433/0.986/0.947 | match |
| §A.9 rule of thumb | 1.9 × σ_pair for P1 and P5; 1.88–1.92 | P1 holds (1.88–1.92). **P5's ratio is 1.90–1.96**, outside the stated range (MINOR V-11) |
| §B.2 levels | 0.75%, 0.042%, 0.375%, 0.135%, 0.323%, 0.79% | match |
| §B.2 checks | weights 1; rows 1; Holm graph 5,000 / 5,000; FWER 4.89% and 4.91% | match |
| §B.2 | U MDE +1.6% at 8 df | match (factor 1.0165) |
| §B.2 | HB false "worse (U)" 1.6–2.3% | numbers match (1.56–2.33), but they come from **Holm over 6, not Φ**, and they are not a directional-error check (MINOR V-9) |
| §B.4, §C.4, §C.5 | equivalence grades, δ80, P(better), 5.65 pp, 0.64 / 0.63 / 0.76, 2.75 / 2.5 pp | match |
| §C.1–§C.3 | E 43.50 / 43.67 / 48.17; 45.11; 11.1%; 10.9%; 2.2 and 6.1 pp; 1.7 pp; 3.4 pp | match |
| §D.5 | 3.4–4.3 / 4.9–6.1; 3.1–3.9 / 4.3–5.4; 5.3–5.9 / 7.5–8.4 pp | match |
| §D.6 | $16.2–17.5 → $22.4–24.8; $5.4–5.9 → $7.5–8.3; $8.1–8.8 → $11.5–12.9; $5.8–5.9 → $8.0–8.3; $8.8 → $12.4–12.9; total $42–46 | match (I re-did the arithmetic by hand) |
| §E.3 | 0.33 / 0.14 / 0.06; 0.72 / 0.47 / 0.30; 0.99 / 0.81 / 0.43; 1.00 / 0.97 / 0.80; 0.95; 0.60; $28–90 | match (hand check of the normal formulas too) |
| §D.1 | τ_L = 0.0067171 nats | match (NUM) |
| §F | P(at least one of 50 units fails) 10–97% from 0.2–6.6% per unit | match (1 − (1 − p)^50) |
| §A.6, §A.9 | residual df by arm (a0 4.01, R 4.85, others 4.36); R_1108 leverage 1 | match (SIM design printout) |

### 2.3 Fresh-seed replication (M: `verify/verify_extra.py` part A, new random seeds, 20,000 replicates each)

HB's FWER / worst single at α/6 (draft value in brackets): N1 3.84 / 0.78 (3.81 / 0.74); N4 3.25 / 0.64 (3.51 / 0.68); H2 3.86 / 0.96 (4.23 / 1.04); H3 3.82 / 1.06 (3.77 / 1.06); X1 3.52 / 0.90 (3.78 / 1.04); D1-H4 3.25 / 1.09 (3.28 / 1.08); G2 4.48 / 0.92 (4.29 / 0.85). The differences are within about 2 Monte Carlo SE. The MDEs agree within 0.1 pp.

---

## 3. Error control of the testing family Φ

### 3.1 Proof (I; standard result, applied)

1. Φ is a graph in the sense of Bretz, Maurer, Brannath and Posch (2009, *Statistics in Medicine* 28:586–604): start weights w ≥ 0 with Σw = 1; transition weights G_ij ≥ 0, G_ii = 0, every row sum ≤ 1 (here every row sums to 1; M: NUM and my own check).
2. For every index set I, the graph's update rule gives weights w_j(I) ≥ 0 with Σ_{j∈I} w_j(I) ≤ 1. These weights grow when I shrinks. So the sequentially rejective rule is a shortcut of the closed test whose local test for H_I is the weighted Bonferroni test "reject H_I if p_j ≤ α w_j(I) for some j ∈ I" (Bretz et al. 2009).
3. Let T be the set of true nulls. A false rejection needs H_T rejected. If each p_j with j ∈ T is valid (P(p_j ≤ u) ≤ u), then P(reject H_T) ≤ Σ_{j∈T} α w_j(T) ≤ α. This uses no assumption on the dependence between the p-values. So FWER ≤ 5% for every configuration of true and false nulls.
4. The p-values Φ needs: U_k two-sided t; O_k, L_k one-sided t (under RB R1.3, the larger of two one-sided p-values, which is valid for the union null); F_k one-sided t. Each is exact only if the HB t-statistic has its stated t distribution. It does not, exactly (§3.3). So Φ's 5% is exact for exact p-values and approximate for HB's.
5. **One consequence the draft does not state.** A single U node can reach the full 5% level once the other 23 nodes are rejected (M: verified on the graph). So strong control in a partial-null case needs each contrast's test to be valid at 5%, not only at α/6.

### 3.2 Checks (M: `verify/verify_extra.py` part C, `verify/verify_fboundary.py`)

| Check | Result |
|---|---|
| My own graph code (independent of NUM's) against a brute-force closed test on a reduced 8-node copy of Φ (two contrasts, the same passing pattern), all 255 intersections | 0 mismatches in 3,000 random p-vectors; 0 violations of weight monotonicity |
| 24 nodes, correlated statistics (U1–U3 share R: +0.5; P4 against P5, P6: −0.5; P5–P6 +0.5; U, O, L, F of one contrast +0.3), global null | FWER 4.72% (MC SE 0.15) |
| All U false (6 SE); O, L, F true at the boundary | 4.67% |
| U1–U5 and F1–F5 false; the rest true | 4.91% |
| U, O, L all false; every F true at the boundary | 5.21% at 20,000 replicates (MC SE 0.16), re-run at 2 × 200,000: **4.94% and 4.86%** (MC SE 0.05; Bonferroni bound 5%) |
| Wrong-sign U claims (a rejected U_k whose sign is opposite to the true effect), true effects ±0.25, ±0.5, ±1 SE, with and without large effects elsewhere | 0.05–0.98% in all 9 configurations |

### 3.3 How close HB's p-values are to valid (M: SIM and `verify_extra.py` part A)

| Level a single contrast can reach | HB, worst contrast over the scenarios checked | Nominal |
|---|---|---|
| α/6 (Holm's and close to Φ's first U step) | 0.68–1.09% (H2, H3, D1-H4 highest) | 0.83% |
| 1% (Φ's U level after a few rejections) | up to 1.26% (D1-H4, P4–P6) | 1% |
| 5% (the last step under Holm or Φ) | up to 5.33% (H2, P1) | 5% |

So the partial-null FWER under Φ or Holm can reach about 5.3% when one noisy arm's contrast is the only true null (E). The excess is small, but "valid in all 19 scenarios" (§0) overstates it (MINOR V-8).

### 3.4 Equivalence outside Φ (I)

The draft's closure argument (§B.4) is right for the only construction that gives equivalence α for free: E_k tested at U_k's weight, which the closure allows because U_k and E_k are disjoint. Then every intersection that holds E_k keeps slot k's weight, so F_k, O_k and L_k get no weight from U_k unless E_k is also rejected. With its own weight, E_k would take α from the other nodes instead. The text should say both (NIT V-17). The 10% study-wise bound (5% for Φ, 5% for the Bonferroni equivalence grade) is a correct union bound.

---

## 4. Consistency with frozen rules, D5 = (a) and the lead's addendum

| Item | Source | Finding |
|---|---|---|
| Gate B rules (PREREG §2–§4) | R: PREREG | No Gate B rule is changed. The blinded seed rule is unchanged. τ_O\* = 5 pp reuses G4's value only. |
| PREREG §2 noise model | R: PREREG §2 ("U(arm, j) = μ_arm + s_j + e … s_j cancels in every c") | The frozen Gate B model is already HB's seed-blocked structure. This is the strongest outcome-free reason for pairing, and the draft does not cite it (fix in V-2). |
| G1 "answers end" | R: PREREG §3 G1 (per arm-run) | The draft's §F pools the bar over an arm's seeds. That is a departure from G1's per-run use. It may be right (R: CK-3 §5.2), but it must be called a departure (MINOR V-14). |
| D5 = (a) | R: FOCUS "D5 DECIDED: (a)"; BRIEF table D5-2 | (a) fixes "Holm over 6 at 5%" and says "(a) changes nothing frozen" and "the primary MDE stays". Φ changes D5-2's (a) column, and HB changes the primary MDE. The draft marks Φ [USER] but gives no silent default (MAJOR V-1). |
| The adopted 13:53 UTC design | R: FOCUS 8 Oct 13:53 UTC | It fixes the family, Holm at 5%, the 5 pp margin by TOST, the seeds and the blinded rule. It does not name the variance model. So HB is a refinement of the approved basis (PLAN-S:102), not of the user's adopted list (I). |
| ADD L15 (1) "never σ̂_gate" | R: ADD | The REQ-17 ρ grid {0, 0.67} uses PREREG's pre-Gate-B value, not σ̂_gate. But it was proposed after the noise gate was read, so REQ-21 (m) must list it (ADD §3 item 4; part of V-2). |
| ADD L16 scope | R: ADD L16 ("the SE inside REQ-16's 'upper 90% L' screen is still estimated from the replay's pooled residuals") | The draft's REQ-16 change (HB-form SE) edits this sentence. It must say so (MINOR V-13). |
| ADD §3 item (4) | R: ADD | REQ-21 (m) must list every Gate B value seen before the selector settings are frozen. The draft's K.3 list is incomplete (V-2). |
| ADD §5 item 1 | R: ADD | S-HB-tok is report-only, as ADD says. OK. |
| RB R1.3, R1.5 | R: RB | §B.3 states them correctly. Under R1.3 the edge F_k → O_k is dead weight (MINOR V-12). R1.5 lets the user switch "before any stage-1 unit outcome is read"; the reused a0 and R cells are already read, so the W1 record should say that "outcome" means a newly run cell (note added to the draft's §B.3). |
| The 18:31 UTC "worse" rule | R: FOCUS 8 Oct 18:31 UTC ("significantly harmful at the 5% Holm level") | The user's text names Holm. Φ replaces it, so [USER] is right. |

---

## 5. Outcome-dependence and the REQ-21 (m) record

The draft's author saw σ̂_gate 1.83 pp, r_j and the values derived from them. The question: does the choice of the paired model depend on them?

### 5.1 What the choice uses and does not use

1. **No estimator, test level, margin or label rule takes a Gate B number** (M: I read SIM, NUM and the rule text). D1 is outcome-free once HB is chosen: P4 gets a sixth pair at any noise level.
2. **HB's validity does not depend on ρ** (M: SIM, ρ = 0 to 0.76 with unequal arm variances; my PL scenario below). So choosing HB after seeing ρ̂ cannot raise the false-positive rate (I).
3. **HB's power advantage does depend on ρ** (M: `verify_extra.py` part A, fresh seeds). P1's MDE at 80%, Holm:

| Noise scenario | Known before Gate B? | HB | Welch (aW; the approved sensitivity, unpaired) | 8 Oct (a) (invalid with unequal arm variances) |
|---|---|---|---|---|
| PREREG §2 "low": σ_pair 2.15, no CRN (PL, new) | yes (PREREG §2) | **4.09** | 5.81 | 4.95 |
| PREREG §2 "central": per-arm 2.65, ρ = 0 (N1) | yes (PLAN-S:117) | 7.10 | **6.13** | 5.20 |
| Wave 0a: ρ 0.76, CRN 0.65 (N4) | no | **3.51** | 5.73 | 4.88 |

   - Over the pre-Gate-B planning grid the power case is split: HB wins at "low", Welch wins at "central". The only pre-Gate-B same-seed estimates were −0.08 (a per-prompt residual correlation, PREREG §2) and −0.88 (recipe B against recipe G at one seed, 2 df; R: CK-2 §3). Both pointed **against** a pairing gain. The wave-0a values (ρ̂ 0.76) are what make HB clearly the more powerful choice.
   - Without the wave-0a values, two arguments for HB remain. (a) Design: same-seed arms share the initialization, the row order and the sampling streams, and PREREG §2's own frozen model has a shared s_j. (b) Robustness: Welch fails in X1 (worst single 1.47–1.67% at α/6, 7.8% at 5% for P1), and HB does not.
   - **Conclusion (I).** The choice of HB over the approved unpaired analysis was made after seeing the noise-gate values, and its power case leans on them. This is a choice on a nuisance value, and it cannot raise the false-positive rate. It still must be recorded as such. The draft's K.3 says HB was "chosen on grounds that hold over the whole noise grid, including ρ = 0". That is true for validity and not true for power, and §A.10 does not list Welch as an alternative.
4. **The author also saw six of the 50 primary stage-1 cells.** a0 at 1101–1103 (Gate A: U 46.67, 46.83, 51.33%; O 4, 6, 4 of 100; task loss; screen rates) and R at 1101–1103 (Gate B wave 0a: U 46.0, 44.3, 47.0%, from r_j and Gate A) are reused in stage 1 (R: PLAN-S:233; BRIEF REQ-21 (d); `sim_w2_results.json` keys `U_a0`, `U_R`). The draft's K.3 says "no stage-1 value was read". That is false (MAJOR V-2).
5. **The choice of HB moves two seen cells out of the primary estimates.** HB never uses a0_1101 or R_1101 in an estimate; the approved analysis (S-a) does. Given the seen values, and the unseen seeds at the seen means, the expected difference S-a − HB is **−0.28 pp for P4** under D0 (−0.27 under D1) and **+0.04 pp for P1–P3** (M: `verify_extra.py` part D). So HB is expected to read P4 about 0.3 pp more in S1's favour than the approved analysis does. That is about 7% of HB's P4 MDE at wave-0a noise (4.0 pp). Small, but its direction is known, so it goes in the record.
6. **Other settings fixed after relevant values were seen.** (a) The REQ-17 ρ grid (after the noise gate; values from PREREG). (b) The O error model "prompts random": CK-3, RB and this draft knew from Gate A counts that it opens O-ext and that the seed-only model does not (R: CK-3 §4.5; the draft's own §E.2 warns of this). (c) The arm-pooled coherence bar, after a0_1101–1103's screen rates were read (Gate A; stage-1 comparator cells). (d) The option to move the plan-A cut to σ̂ ≤ 3.4 pp (§A.11), offered when σ̂_gate = 1.83 was known; the frozen rule says "frozen now" (R: PLAN-S:118). I recommend withdrawing that option (MINOR V-10).

### 5.2 Proposed REQ-21 (m) text for this draft (applied to the draft's §K.3)

> **(m) Blinding line, stage-1 analysis model and testing family.** This text was written after Gate B's wave-0a noise gate and the Gate C seal. Its authors saw: r_j = +0.67, +2.50, +4.33 pp; σ̂_gate 1.83 pp (fallback 2.16); σ_eval,0 1.28 pp (fallback 2.16); SD(U(R_j)) 1.35 pp (fallback √2·SD 1.91); the implied same-seed ρ 0.76 and per-answer coupling 0.65; the noise-gate P4 record (mean r 2.5 pp) and the P(LOCALIZED) lookup; the wave-0a ledger timings; the sealed unit-level scores, rankings, picks and ρ values. Six of the 50 primary stage-1 cells are reused units whose values were read: a0 at 1101–1103 (Gate A: U, O, task loss, screen rates) and R at 1101–1103 (Gate B wave 0a: U). No stage-1 method-arm cell exists. **Uses:** no estimator, level, margin or label rule takes any of these numbers. The choice of the seed-paired model (HB) over the approved unpaired model (PLAN-S:102) was made after seeing them. HB's error control holds from ρ = 0 to 0.76 and with unequal arm variances (simulated), so the choice cannot raise the false-positive rate. Its power advantage depends on ρ: at the pre-Gate-B planning values it is split (P1 MDE: HB 4.1 against Welch 5.8 pp at PREREG's low scenario; HB 7.1 against Welch 6.1 pp at ρ = 0). Given the seen cells, HB is expected to read P4 about 0.3 pp more in S1's favour than the approved analysis, and P1–P3 within 0.05 pp; the approved analysis is reported beside HB (S-a). The N4, N8, H3–H6, G1, G2 and X1 scenario calibrations, the size of D1's gain and the cost figures use wave-0a values. The REQ-17 ρ grid {0, 0.67} was proposed after the noise gate; its values come from PREREG §2. The O error model (prompts random) and the arm-pooled coherence bar were fixed after the Gate A over-refusal counts and screen rates were read (pre-Gate-B values).

---

## 6. Findings by severity, with the fix applied

| ID | Severity | Where | Finding | Fix applied to the draft |
|---|---|---|---|---|
| V-1 | **MAJOR** | §B.2, §H B1, C2, E1, A1 | [USER] items that change frozen or approved inputs have no default for a silent user. Φ replaces "Holm over 6 at 5%" (adopted 13:53 UTC; D5 = (a), D5-2). The draft gives only "fallback if the user declines". E1 (τ_O\*) has no fallback, though Φ's F nodes need it. C2 has no silent default. For A1 (HB replacing PLAN-S:102), the mark does not say what happens if the user is silent. The draft does this right for D1 and R1.3, so the register is inconsistent. | Silent defaults added: Φ → frozen Holm over P1–P6 plus the "worse" families; E1 → no primary τ_O, so F leaves Φ (the F_k edges reroute as stated); C2 → 5 pp absolute; A1 → the lead classifies it: [LEAD] (recommended, since the adopted text does not name the variance model), or [USER] with the approved analysis S-a as the silent default and HB as a pre-registered sensitivity. |
| V-2 | **MAJOR** | §K.3, §J.1, §A.10, §0 | The REQ-21 (m) blinding line says "no stage-1 value was read" (false: six reused cells were read). It omits SD(U(R_j)), U(R_j), the seen a0 values and the known-direction P4 shift. It says HB was chosen on grounds that hold at ρ = 0, which is true for validity but not for power (§5.1). §A.10 omits the approved Welch analysis as an alternative, the one that beats HB at ρ = 0. The outcome-free basis in PREREG §2's own noise model is not cited. | §K.3 replaced by the text of §5.2. §A.10: Welch added to the alternatives with its numbers; reason 1 now leads with the design and with PREREG §2, and marks the wave-0a evidence as seen after the fact. §0 trade-off paragraph and §J.1 reworded. |
| V-3 | **MAJOR** (open trade-off, §7) | §A.3, §A.10 item 3, §C.4, §J.4 | HB fits one seed shift for all eight arms. The design has two clusters: a0 and the add arms (a0's corpus plus 48 rows, 38 steps) and R and the removal arms (600 rows removed, 33 steps). Every primary contrast lies inside one cluster. Gate B measures only between-cluster (a0–R) and removal-cluster pairs. If each cluster has its own seed component, HB's SE is 1.35–1.50 × the true SD, so it loses power: P1 / P4 / P5 MDE 4.95 / 6.13 / 5.46 pp against 4.22 / 4.95 / 4.24 for HB-C (seed effects per cluster). If a sub-cluster shares a component (A1, L1, H1 without R; or S1, S3, S4 without a0), HB is slightly liberal: up to 5.4% at 5% and 0.93% at α/6, where HB-C gives 4.6–4.9% and 0.76%. Under exact additivity HB-C costs 8–12% on the MDE. Also, the arm × prompt part is invisible to Gate B's σ̂: the scenarios that add it to N4 (G1, G2) give HB MDEs 13–22% above N4's. So "its power is known in advance" (§A.10 item 3) is overstated. (M: `verify_hbc.py`, `verify_extra.py` part B; seed-level normal cells, 20,000 replicates.) | §A.10: HB-C added as an alternative, with the numbers; item 3 qualified. §A.7: HB-C added as a sensitivity (S-HBC). §J.4 extended. The choice HB or HB-C goes to GPT (§7). The draft keeps HB as its recommendation, with my disagreement stated. **Reference fits (§D.2):** a removal arm against a full-corpus reference crosses the clusters; there HB's one-sided 5% test rejects at 5.9% under the two-cluster case, against 4.8% for the pair's own paired t (M: `verify/verify_crosscluster.py`). §D.2 now uses the pair's own variance for such pairs ([LEAD], S1). |
| V-4 | **MAJOR** (rule text) | §D.3 | The matched-L rule compares m with AS(λ_lo) and calls the test conservative. Moving down the curve lowers U and raises over-refusal (a0 4–6/100 at λ = 1; θ0 17/100 at λ = 0). So AS(λ_lo) is harder to beat on U (conservative) but **easier** on O: "O(m) − O(r) < 5 pp" is easier when O(r) is higher (liberal). | U (item 1) is tested against AS(λ_lo); O (item 2) against AS(λ_hi), the smallest grid λ at or above λ\*_m. Both are then conservative. |
| V-5 | MINOR | §A.12 B16 test list | "HB = (b) when there are only two arms": with two arms the per-arm variances are not identified (singular REML information). Only their sum is. | Test reworded: the estimate and the variance equal (b)'s; the seed df equals J − 1; B16 must handle the non-identified split. |
| V-6 | MINOR | §A.3 | In about 25% of fits one arm's REML variance sits at the 0.01 pp² floor (3.2% of arm fits; M: `verify_floor.py`). In those fits the affected contrasts reject at 2.1–2.7% at α/6, but the exact paired t also rejects at 2.2–3.0% in the same fits (M: `verify_floorfix.py`). So the floor marks a sample with a low spread; it is not an HB failure. A shrinkage fix (HB-mod) was liberal up to 12% at 5% with one noisy arm, and a max-rule fix only cost power. No change to the estimator is needed. | Added to §A.3: a floor is expected in about a quarter of fits and is printed; there is no re-fit and no change of model after seeing it (a forking-path guard). |
| V-7 | MINOR | §A.12, §J | The draft's "every 'wave 0a' number is one plausible case" is right. The seen a0 and R per-seed SDs (2.65 and 1.35 pp, sample covariance 2.73 pp², larger than R's variance 1.81) cannot come from a shared shift with equal loadings. On 2 df this is noise, but it is the X1 kind of violation, so X1 is not a far-fetched case. | Sentence added to §J.1. |
| V-8 | MINOR | §0, §A.9, §A.10 item 2 | "Valid in all 19 simulated scenarios". The FWER numbers are complete-null values only. The worst single contrast is 30% over nominal at α/6, up to 1.26% at 1% and up to 5.33% at 5% (§3.3). Under Φ a single U node can reach 5%. | "Valid" → "near nominal", with the partial-null numbers. |
| V-9 | MINOR | §B.2 "Directional claims" | The 1.6–2.3% false "worse (U)" rate is from Holm over 6, under the complete null. That is a type I count split by sign, not a directional-error check. | Reworded; the wrong-sign simulation of §3.2 (0.05–0.98%) added, labelled z-level. |
| V-10 | MINOR | §A.11, §H A6 | The option to move the plan-A cut was offered when σ̂_gate = 1.83 was known. The rule says "frozen now". A change now is not blind. | Option withdrawn from the register; kept only as a note that it would be post-noise-gate and must be listed in (m). |
| V-11 | MINOR | §A.9 rule of thumb | P5's ratio is 1.90–1.96, not 1.88–1.92; P4's under D0 is 2.14–2.20. | Corrected. |
| V-12 | MINOR | §B.2 passing rules | Under RB R1.3 the edge F_k → O_k (½) is dead weight. If F_k is rejected (O − θ0 shown below 5), R1.3's O_k needs O − θ0 shown above 5. | Note added: under R1.3, F_k passes all its weight to L_k. The graph's validity does not change. [LEAD]. |
| V-13 | MINOR | §A.12 REQ-16 | The change edits ADD L16's scope sentence and is not marked as such. | Marked. |
| V-14 | MINOR | §F item 1 | The arm-pooled bar departs from PREREG G1's per-run use. Its choice followed the reading of a0_1101–1103's screen rates. | Called a departure; listed in (m). |
| V-15 | MINOR | §C.3 | "0.111 × E" in the text; the code uses 0.1108. A rule needs one exact constant. | "δ_fam = 5 × E_fam / 45.11", with 0.1108 beside it. |
| V-16 | MINOR | §D.6, §E.3, §B.6 | (a) Under D1, λ = 0.9 at a0_1107 is one more state and is not costed ($1.69–1.83 in a free slot of the λ = 0.9 pods, $2.39–2.80 on its own pod; M: arithmetic on NUM's basis). (b) §E.3's powers use a normal approximation without HB's seed part and its df of about 8, so they are optimistic. (c) Family 1c does not say which cells enter the HB fit for P7–P8. | (a) Cost line added. (b) Label added. (c) "The eight primary arms plus SR and S6, in a separate fit; the primary fit is unchanged." |
| V-17 | NIT | §B.4 | The closure argument holds for the shared-slot construction only (§3.4). The study-wise statement should say "type I errors; directional errors by simulation". | Clarified. |
| V-18 | NIT | Header, §K.4 | "Nobody has checked this draft yet"; revision number. | Revision 2; verify reference added. |

---

## 7. The open trade-off for GPT (I)

**HB (one seed shift for all arms) or HB-C (one seed shift per design cluster)?**

| | HB | HB-C |
|---|---|---|
| Exact additivity, ρ 0 / 0.67 / 0.76: P1 MDE | 7.11 / 4.08 / 3.47 pp | 7.69 / 4.42 / 3.77 pp (+8–9%; P4 +12%) |
| Two clusters (shared 0.3, each cluster 0.4 of the variance) | valid but SE/SD 1.35–1.50; MDE 4.95 / 6.13 / 5.46 | SE/SD 1.02–1.03; MDE 4.22 / 4.95 / 4.24 (−15 to −22%) |
| Sub-cluster structures | up to 5.4% at 5%, 0.93% at α/6 | up to 4.9% at 5%, 0.76% at α/6 |
| Residual df (D0) | 35 (about 4.4 per arm) | 29 (about 3.7 per arm) |
| Evidence for the needed assumption | Gate B has no add arm, so the add cluster's coupling to R is untested | assumes only within-cluster additivity |
| Outcome-free basis | PREREG §2 noise model | the design (row counts, step counts) |

(M: `verify_hbc.py`, D0 and D1, 20,000 replicates per row, seed-level normal cells.)

My view (I): HB-C fits the draft's own principle ("chosen because it is valid over the whole grid") better, and its basis is purely the design. HB is the better bet only if the add arms move with a0 the way R does. Gate B cannot tell us that. I disagree with the draft's choice at this point, mildly. Both are defensible. GPT should rule before the W1 record. Whichever is primary, the other is a pre-registered sensitivity. The draft keeps HB as its recommendation and now states this alternative.

---

## 8. Commands run (all Python with `PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B`, from `verify/` or `verify/rerun/`)

| Command | Exit |
|---|---|
| `import scipy` check | 1 (scipy missing, as the draft says) |
| `rerun/stage1_model_sim.py --reps 20000` (byte copy; 850 s) | 0 |
| `rerun/stage1_numbers.py` (byte copy) | 0 |
| `verify_extra.py --parts D`, `--parts C`, `--parts B` (`--reps 20000`; run twice, the final runs after the last script edit; seeded, identical) | 0 |
| `verify_extra.py --parts A --reps 20000` (first attempt stopped: my PL scenario was infeasible as written; fixed; second run 351 s) | 1, then 0 |
| `verify_hbc.py --reps 20000` (105 s) | 0 |
| `verify_floor.py`; `verify_floorfix.py` | 0; 0 |
| `verify_fboundary.py` (400,000 replicates) and two inline debugging runs of the same check | 0 |
| `verify_crosscluster.py` (20,000 replicates per case) | 0 |
| Shell reads: `ls`, `cat`, `sed`, `grep`, `awk`, `shasum`, `cmp`, `diff`, `git log`, `git status`, `date -u`; small `python3` JSON readers | 0 |

## 9. Files written (this folder only)

| File | SHA-256 (first 16) | What |
|---|---|---|
| `verify-report.md` | – | this report |
| `verify/rerun/` | byte copies: `581e9bd18de79336`, `9f7c4ab924af7cb2`, `5b3a85bed3ab90fb`, `2c8f432b7be70ab5` | the re-run copies and their outputs (results JSON `ccf202311899370f`; numbers JSON `80ae7caa7406a7a6`) |
| `verify/verify_extra.py` → `verify_extra_out_{A,B,C,D}.txt`, `verify_extra_results_{A,B,C,D}.json` | `ed8d29b2b08cb284` | parts A–D (§2.3, §3.2, §5.1, V-3) |
| `verify/verify_hbc.py` → `verify_hbc_out.txt`, `verify_hbc_results.json` | `ebf190de20674369` | HB against HB-C (V-3, §7) |
| `verify/verify_floor.py`, `verify/verify_floorfix.py` → outputs | `d61d230aa50e45f7`, `f00ebf6cf250d7e0` | REML floor events (V-6) |
| `verify/verify_fboundary.py` → `verify_fboundary_out.txt` | – | the 400,000-replicate boundary check |
| `verify/verify_crosscluster.py` → `verify_crosscluster_out.txt` | – | HB on a contrast that crosses the clusters (V-3, §D.2) |
| `verify/stage1-analysis-model-DRAFT-rev1-before-verify.md` | `e689d8e31b87f874` | the draft as received |
| `stage1-analysis-model-DRAFT.md` | changed in place (revision 2) | fixes V-1 to V-18, and a "Verify changes" section |

## 10. Acceptance against the verify brief

| Item | Status |
|---|---|
| Re-run the simulation code (read-only use) | done; byte-identical (§2.1) |
| Check every number | done for every SIM/NUM number (§2.2). Numbers cited from CK-2, CK-3, CK-11, REF and RB (R) were not re-derived, apart from spot checks (CK-2 §3, CK-3 §5.2) |
| Error control of the family: prove or simulate | proof (§3.1) and four simulation checks (§3.2); HB's approximation measured (§3.3) |
| Consistency with frozen Gate B rules, D5 = (a), the addendum | §4 |
| Outcome-dependence; how REQ-21 (m) records it | §5; text in §5.2, applied to the draft |
| Report with errors by severity and fixes; fixes applied; "Verify changes" section | §6; applied |
| Not tested | B16's real code; the REML routine on real stage-1 data; the cluster structure's real size (no data exists for the add arms) |
