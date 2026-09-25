# Why ordinary couplings nearly match the oracle: v1 mechanism diagnostic

Date: 2026-09-24. Task: mechanism-diagnostic-v1. This is a post hoc diagnosis of the
completed v1 H1/H2 grid (campaign `20260924T150726Z`) and cannot serve as fresh
confirmation. The frozen gate result stands: no B-family cell reached 20%.

Revised 2026-09-24 after review. Stored variances and headroom summaries are now validated.
The wording now limits four claims to their evidence: the allocation setting, the 'atoms'
class, hindsight envelopes and the rules other than `fixed_label`. No numerical finding
changed.

**Evidence:**
- [diagnostics.json](diagnostics.json): checks, summaries, examples, hashes and resources.
- [h2_cells.csv](h2_cells.csv): every H=2 cell with its six-method R0/R1 split.
- [h2_groups.csv](h2_groups.csv): summaries by structure × alpha × beta.
- [ALTERNATIVES.md](ALTERNATIVES.md): the pre-code plan, its post hoc addendum and a dated
  clarification after review.
- Code and tests: `pilot/diagnose.py` and `pilot/tests/test_diagnose.py`.

**Inputs:**
- The manifest SHA256 `62f7bcc4…c57999` was verified and matches the run metadata.
- There are 1,440 completed records, with records digest `4dc049a3…043ad9`.
- None of the 720 H=4 targets has a record.
- Prior module hashes equal those in the run metadata.

**Run:** `python -m pilot.diagnose --input research/pilot/runs/20260924T150726Z --output research/pilot/diagnostics-v1`
exited 0 after 6.24 s wall time and 6.04 s CPU, with 115 MB peak RSS. These figures cover
the diagnostic process only. Runs of the pre-review version took 5.7–8.9 s; the variation
is machine load. The `pilot/diagnose.py` SHA256 is `c1b8ea47…95cd`.

## Decision summary

1. **H=1 cannot show headroom here (identity).** Sorting by the `ordered` key sorts the
   terminal scores, so `ordered` equals both the oracle and terminal OT. Half the
   completed grid could never reach the gate.
2. **At H=2 the oracle can beat `ordered` only at the root decision.** This requires the
   root continuation cost to fail the Monge property in the key order (identity).
   - That failure occurred in 100 of 656 nondegenerate cells; 47 of them have ≥1%
     headroom.
   - In every one of those 47, the children's one-step terminal laws have crossing CDFs.
   - Every beta=0 cell has zero headroom. In this grid, headroom requires the policy to
     react to the intervention.
3. **B1 (at most 18.5%): no single ordinary rule is right at both decisions.** Terminal
   sorting is exact at the last step. At the root, the successor's first coordinate
   misorders the children's continuation means. The hypothesis is that the unread
   coordinate drives the next policy.
   - Choosing the root rule per cell in hindsight, some ordinary root rule followed by
     terminal sorting attains the oracle in 23 of 24 B1 cells with ≥1% headroom.
   - One fixed schedule, the label-order CDF root (`fixed_label`) plus terminal sorting,
     attains it in 21 of the 24 and leaves at most 6.3% in the other 3. Label order also
     equals the children's mean order in 21 of the 24; in 11 of them, the Monge property
     in that order forces this. No single schedule has been shown to match the oracle
     across the grid; this one leaves up to 39.8% in A2.
4. **A2/A3 (at most 25.4%/11.7%): the children's continuation laws cross.** In family A
   every such failure needs the difference in policy weights (identity). The oracle pairs
   children crosswise; in 6 of 13 A2 cells none of the six ordinary root rules matches
   it. The proposed projected rule is identical to `ordered` in family A (THEORY §2), so it
   cannot capture this headroom.
5. **The variance savings do not support an asymptotic 2x gain at equal cost.** Assume
   equal cost per pair, negligible setup, and averages of independent unbiased paired
   samples in the allowed class. The oracle's variance ratio is
   at most 1.34 (1.23 in B), and at RMSE 0.01 its sample-count ratio has median 1.0 and
   maximum 1.3. This is not a practical impossibility result. It does not cover other
   estimators or methods with different per-pair or setup costs, and integer rounding
   alone gives 2:1 at RMSE 0.02 in two cells (§2.4).
6. **Decision: stop this mechanism in this domain; no v2 is proposed (§4).**

## 1. Method and validation

For ordinary method m, the second-moment regret over the oracle splits into two decisions:

E_m[Y²] − V* = R0(m) + R1(m), with R0 = Σ(π^m − π*)C and R1 = Σ π^m(W^m − C).

- C_ab is the oracle value of child pair (U_a x, U_b y) with one event left; it equals the
  stored `root_cost`.
- W^m is m's last-step second moment.
- Means do not depend on the coupling, so this is also the variance regret.
- R0 is unchanged by adding row-only or column-only terms to C. Only the 2x2
  interactions C_ab + C_a'b' − C_ab' − C_a'b affect the choice of plan.
- R0(m) is exactly the regret of the schedule "m at the root, terminal-score sort at the
  last step".

Validation uses independent routes. The table reports the maximum absolute discrepancy
over all 720 H=2 cells × 6 methods, with tolerance 1e-12 unless a row states otherwise:

| Check (route) | Max |
| --- | ---: |
| C vs stored LP `root_cost` (quantile merge, no LP) | 1.7e-17 |
| V* vs stored oracle E[Y²] (81 candidate transport bases, feasible ones costed; no solver) | 2.8e-17 |
| Stored root plan: marginals / cost vs V* | 2.2e-16 / 2.8e-17 |
| Method E[Y²] and E[Y] vs stored (own enumeration, public couplings API) | 0 / 0 |
| Oracle and terminal-OT E[Y] vs δ; terminal-OT E[Y²] vs quantile merge | 3.1e-16; 1.7e-17 |
| Stored action probability vs recomputed (tolerance 1e-15) | 0 |
| R0+R1 vs stored (E_m[Y²] − V*); negative R0 or R1 | 3.0e-17; 2.1e-17 |
| `ordered` last-step regret (identity); maximal-then-`ordered` enumeration vs R0 | 1.5e-18; 3.7e-18 |
| H=1 `ordered` vs oracle vs terminal OT, 720 stored cells | 6.9e-18 |
| Monge in key order ⇒ zero regret (556 cells); label-order Monge ⇒ optimal `fixed_label` root | 1.9e-17; 2.1e-17 |
| All 1,440 H1/H2 records (tolerance 1e-15): stored variances vs pilot.pair's convention on the stored moments; best method and variance, oracle and terminal variances, flag and ratios vs pilot.headroom's definitions, ties at the minimum allowed | 0 |

The full suite passed: 179 tests (126 for the v1 modules, 53 for the diagnostic, 22 of
them added in this revision). The diagnostic tests cover:
- quantile W2 and vertex optima against the LP;
- stochastic order implying Monge implying an optimal sorted root, with the real A2
  counterexample;
- K=3 uniqueness of maximal agreement, with a K=4 counterexample;
- a tied-key example in which `ordered` is not relabelling-equivariant;
- live-cell identities against `pilot.pair`;
- rejection of the corrupted inputs below.

The diagnostic rejects inconsistent inputs before writing anything:
- missing, failed or mismatched records;
- stray or H=4 records;
- a wrong manifest hash;
- an output directory inside the input directory;
- stored values that are missing, non-finite or of the wrong type;
- stored variances or headroom fields that differ from v1's definitions. Examples are
  `headroom.oracle_variance` = 0, a best method above the minimum, and a zeroed method
  variance; each was accepted before this revision.

A stored moment altered by 1e-9 fails the recomputation checks, and the diagnostic then
writes nothing.

## 2. Findings

### 2.1 Identities behind the zeros and ties

- **Last step.** With one event left the oracle sorts terminal scores, and so does
  `ordered`. Hence V_ordered − V* = R0(ordered) at H=2.
- **Root.** Suppose each world's children have one-step laws stochastically ordered by the
  key. Then every interaction −2∫(ΔF⁻¹)(ΔG⁻¹) is ≤ 0, C is Monge in key order, and the
  sorted root is optimal.
  - Monge held in 556 of 656 nondegenerate cells, including every A1 and B2 cell. The
    largest headroom among those 556 cells is 1.5e-13.
- **Maximal = distance.** For K=3, the plan that keeps the maximal diagonal is unique, so
  distance transport equals maximal whenever its LP keeps the full diagonal.
  - This happened at every node in 338 of 720 cells (122 of 144 in B1), including witness 1.
  - The tie is structural and is not evidence of a mechanism.
- **Distance = `ordered` in family A.** With scalar successors, squared distance is Monge
  in target order, so the two plans coincide in 432 of 432 cells. The same held
  (measured) in all 144 B2 cells.
- **Terminal OT is noncausal.** It can go lower (witness 1: 2.35e-4 vs the oracle's
  5.04e-4). Finite path laws can be coupled offline, but that generally falls outside the
  allowed co-adapted online class, which preserves each world's transition law conditional
  on the joint past.

### 2.2 Where headroom lives

The 47 cells with ≥1% headroom are 13 in A2, 10 in A3 and 24 in B1. A1 and B2 have none.

- **Crossing CDFs in every headroom cell.** None of the 247 cells whose children are
  totally stochastically ordered has headroom. In every such cell, the key order matched
  the stochastic order.
- **Beta=0 control.**
  - All 164 nondegenerate cells have zero headroom, and TV = 0 at every node.
  - By beta = 0/1/3/8, the maximum headroom is 0/0/20.4/25.4% in family A and
    0/11.2/14.9/18.5% in family B.

**B1: the key misorders continuation means (hypothesis: feedback through the unread coordinate).**

Witness 1 (`27f1126e6c329784`) shows the mechanism:

| Suppressed-world child | θ | Policy | Continuation mean |
| --- | --- | --- | ---: |
| 1 | (0.020, −0.400) | 0.88 on action 0 | 0.595 |
| 2 | (0.157, 0.137) | spread (0.30, 0.25, 0.45) | 0.573 |

Their key order is 0.020 < 0.157, the reverse of their mean order.

- **`ordered`** loses at the root: R0 = 4.76e-4, which is 77% of V_best.
- **Maximal, distance and `fixed_label`** choose the oracle root, with R0 ≈ 0.
  - They lose at the last step instead: R1 = 1.14e-4, which is the whole 18.5%.
  - In label order all nine 2x2 interactions of C are negative. In key order (1, 2, 0),
    the largest adjacent interaction is +3.1e-3.
- **Controls.** Headroom was:
  - 0 at beta 0 and beta 1, 10.2% at beta 3;
  - 3.3% at alpha 1;
  - 0 for B2, and 0 for the H=1 twin.
- **Witness 2 (`d7fbdd78951f35b0`):** 14.1%, all at the last step. The label-CDF root is
  optimal.

Across the 24 B1 cells with ≥1% headroom:
- With the root rule chosen per cell in hindsight, some root rule followed by terminal
  sorting attains the oracle in 23 cells (at most 3.3% remains). This envelope is not a
  selection policy.
- The single fixed schedule `fixed_label` plus terminal sort attains it in 21 cells and
  leaves at most 6.3% in the other 3. Label order equals the children's mean order in 21
  of the 24 cells, but in only 27 of all 144 B1 cells. In 11 cells C is also Monge in that
  order, which forces an optimal `fixed_label` root.
- Without `fixed_label`, the best of the other five root rules, chosen per cell, leaves up
  to 26.9%, and at least 1% in 14 cells.
- Where the best method loses:
  - at alpha 0.25, mostly at the last step (median root share 0.08);
  - at alpha 1, mostly at the root (median root share 0.81).

**A2/A3: continuation laws cross.**

- **Family A.** Each child's next-step atoms move monotonically with its position, so
  every order failure is of the 'weights' kind: with equal weights the children would be
  ordered. This is an identity. It classifies the failure and is not a causal attribution;
  no 'atoms' case occurs.
- **Witness 3 (`24a16ed9956c3de3`).** It suppresses an action with p = 0.039, and the two
  worlds' root laws are nearly disjoint (TV 0.90).
  - The suppressed children at −0.24 and 0.16 have means 0.475 and 0.471. The higher
    child puts 0.74 of its policy on the action that moves it down.
  - Their CDFs cross, and the measured C fails Monge in both position and mean order.
    Crossing alone does not imply that failure: 309 non-sortable cells still have Monge
    costs in key order.
  - The oracle pairs children crosswise: C01 + C10 = 0.0034, versus C00 + C11 = 0.0114.
  - All the loss is at the root (R0 = 3.13e-4, R1 = 0). The best of the six root rules
    followed by terminal sorting, chosen in hindsight, still leaves 23.3%.
  - Controls: A1 0; beta 0 and beta 1 both 0; beta 3 20.4%, not recovered by any of the
    six root rules with terminal sorting; alpha 0.25 2.9%, all at the last step; A3 3.75%.

### 2.3 What the evidence separates

| Candidate cause | Evidence |
| --- | --- |
| Action-probability change | Necessary in this grid: every beta=0 cell has zero headroom. Family-A failures are weights-only by identity. |
| Same-action atom reversals without probability change | Not sufficient here: 13 beta=0 B1 cells show them, all with zero headroom. Where probabilities also change, the 'atoms' class does not separate geometry from probability effects. |
| Terminal ordering | At the last step, the terminal sort is exact; non-sorting rules lose all of R1. At the root, the key is a myopic proxy for continuation-law order. |

- **Paths with mismatched actions** carry most of maximal's second moment wherever the
  policy reacts. In witness 1 they hold 23% of the mass and 83% of E[Y²].
- **One optimal oracle plan** mismatches more (28%) but pairs outcomes by terminal score.
  With LP ties this split may differ, but its cost does not.
- **Not separated:** within B1, probability changes versus geometry. No counterfactual
  dynamics were run.

### 2.4 Magnitude and practical room

The **allocation count** N = max(1, ceil(V/e²)) is the number of independent unbiased
paired samples whose average reaches RMSE e when the variance V is known. The oracle
minimizes V within the same admissible co-adapted class, so these counts bound savings
from changing the coupling within that estimator class. This sample-count comparison
does not require equal computational costs. Translating it into a runtime comparison
additionally requires comparable per-pair costs and negligible setup. It does not bound
other estimators such as exact enumeration or Rao-Blackwellisation, and no wall-time
improvement has been measured.

| Cells | Max variance ratio | RMSE 0.01 ratio: median / max | Median N_best at 0.01 |
| --- | ---: | ---: | ---: |
| All 656 nondegenerate | 1.341 | 1.0 / 1.3 | 1 |
| B, alpha 1 (136) | 1.164 | 1.0 / 1.11 | 1 |
| H=2 half of prespecified B timing panel (20) | 1.164 | 1.0 / 1.1 | 1 |

No cell reaches 2 at RMSE 0.01 or 0.005. At 0.02, two cells show 2.0 only because the
ceiling turns N from 2 into 1.

**Operation counts** are derivations, not timings:
- **Exact enumeration** of both worlds at H=2 costs 26 updates, 9 policy evaluations and
  18 scores, with variance 0.
- **One paired sample** costs 6 updates (agreement rules) or 14 (key rules), plus 4 policy
  evaluations and 2 scores.
  - These counts exclude coupling construction, LP solves and random draws.
  - They assume each pair rebuilds the intervention pair and every state on its path.
    Reusing shared root work would lower them and shrink the cell counts below.
- **Consequence at RMSE 0.01** (136 nondegenerate B cells at alpha 1):
  - in 46 cells the best coupling needs ≥2 pairs, so enumeration uses fewer updates than
    key-rule sampling;
  - in 18 cells it needs ≥5 pairs, so enumeration uses fewer updates than even
    agreement-rule sampling.

### 2.5 Sensitivity to excluding `fixed_label`

The v1 denominator includes the label-CDF coupling, whose plan depends on the arbitrary
action order.
- **What changes.** Against the other five single rules, B1 cell `e7b022b4357178a5`
  (beta 8, eta 0.4, θ0 0, action 2, alpha 1) has 26.9% headroom instead of 11.9%.
- **Where it holds.** Only one B cell reaches 20% on this basis; the A2 maxima do not
  change.
- **What it is.** This is a descriptive sensitivity computed from stored variances. It does
  not re-evaluate the gate or justify dropping `fixed_label` from the v1 comparator.
- **The other five rules are not relabelling-invariant either.** `ordered` breaks key ties
  by action ID; in a tied-key example in the tests, a label swap changes its plan by 0.3.
  `distance` keeps the LP's pick among tied optima. No permutation sweep was run.
- **It does not favour the adaptive rule.** In that same cell, label-CDF plus terminal
  sort attains the oracle exactly. A development-selected action permutation, which the
  spec prescribes for stage 2, would restore that plan.
- **For any future version.** Headroom must be measured against permutation-selected and
  time-inhomogeneous ordinary schedules.

## 3. Status of each claim

- **Identities (derived, checked numerically):**
  - H=1: `ordered` = oracle = terminal OT.
  - H=2: `ordered` is exact at the last step; the R0/R1 split; R0(m) equals the schedule
    regret.
  - Stochastic order implies Monge implies an optimal sorted root.
  - K=3 agreement is unique.
  - Family A: distance = `ordered`, and order failures are weights-only.
  - The projected rule equals `ordered` in family A (THEORY §2, not re-derived here).
- **Measurements (v1 grid, post hoc):**
  - All counts, maxima, controls and witness numbers above.
  - The allocation counts, in the paired-sample setting of §2.4.
  - The sensitivity to excluding `fixed_label`.
  - The best-of-six root-rule envelopes, which are chosen per cell in hindsight.
- **Hypotheses:**
  - B1's root misordering is caused by policy feedback through the unread coordinate.
  - A2's crossing laws come from misaligned feedback under large perturbations.
- **Untested:**
  - Everything about H≥3.
  - Whether the schedules found here generalize to fresh cells.
  - Whether any single, globally chosen permutation or schedule matches the oracle across
    the grid.
  - Other scalar keys or policies, including sorting children by their means.
  - How the projected rule performs in family B.
  - Any practical timing.

## 4. Decision and next step

**Recommendation: stop the adaptive/projected coupling mechanism in this domain. No v2 is
proposed.** The mechanism does make directional predictions, but they point against the
proposed method:

1. **B1.** A fixed label-order CDF root plus a terminal sort attains the oracle in both B1
   witnesses and in 21 of the 24 B1 cells with ≥1% headroom. Choosing among the six root
   rules per cell in hindsight raises this to 23 of 24. No single, globally chosen
   permutation or schedule has been shown to match the oracle across the grid. An adaptive
   rule would have to beat such schedules, not only v1's single rules.
2. **Family A.** The specified projected rule equals `ordered` there, and it loses at the
   root where continuation laws cross. In witness 3, C is Monge in neither position nor
   child-mean order, so neither order is guaranteed to be optimal. Sorting by child means,
   other scalar keys and other policies were not evaluated.
3. **Growth with horizon is untested.** The H≤2 results do not establish whether gains
   accumulate at longer horizons. In the large-sample approximation, a 2x runtime gain
   from variance reduction alone would require at least 50% reduction at equal per-pair
   cost and negligible setup. Integer sample counts can behave differently (§2.4).
   The current evidence does not justify overriding the frozen gate to run H=4.

**What would change this:**
- a pre-registered computation on fresh cells (not v1) at H≥3;
- showing the oracle beating the best two-rule schedule by ≥50% variance in most B cells,
  where the candidate schedules include permutation-selected CDF roots;
- together with a practical rule that keeps that gain after overhead, against exact
  enumeration (26 updates at H=2, 242 at H=4).

I do not recommend running it here, because enumeration stays cheap wherever the oracle
is computable. Continuing the idea elsewhere is the lead's decision. That would need a new frozen
spec, a regime where enumeration is infeasible, and a comparator frontier that includes
permutation-selected CDF couplings, terminal-sort schedules and partial enumeration.

## 5. Limitations

- **Selection.** Witnesses are the v1 maxima named in the brief. The controls follow a
  one-factor rule fixed before any diagnostic output, and the whole H=2 grid is
  summarized.
- **Added after seeing output.** The analyses in the ALTERNATIVES.md addendum were added
  after the first diagnostic output.
- **Revision after review.** The stored-summary validation and the wording corrections
  were added after review. ALTERNATIVES.md records them in a dated clarification. They
  changed no v1 value and no diagnostic number.
- **Horizon.** The exact analysis covers one non-final decision. The H=2 root analysis also
  describes the penultimate decision at any horizon. Earlier decisions have Bellman
  continuation costs that are not W2, and they were not analysed.
- **Shared plan code.** Ordinary plans are rebuilt with v1's plan constructors, so the
  moment comparison cannot detect a defect shared with them. The earlier 65-digit witness
  checks covered those constructors.
- **Numerical precision.** Arithmetic is float64 with fixed tolerances; results are not
  certified bounds.
- **No timings.** Operation counts are derivations, not measured times.
