# Check of mock review A, W11 (the planted-cause positive control), and of the review's other points

- **For:** the main-study lead (GI VI). Read-only check. No repo edit, commit, pod, spend or download.
- **Clock:** `date -u` gave Fri 16 Oct 2026 22:17 UTC before the work and 22:23 UTC before this file was written.
- **Labels.** **R** = I read it in the named file (path:line or section). **M** = I computed it here (a script in this folder, or arithmetic shown in the text). **I** = my inference. **E** = an outside claim that I did not check.
- **Not opened:** `selector.jsonl`, `hidden/`, any held-out file, wave-0b `rows.jsonl` and `groups.json`. No prompt, answer or anchor text was read or printed. I read code, settings, rule text, counts and the sealed unit-level scores only.

## 0. Short answer

1. **The circularity is real.** (R, I.) The plant and both anchor sets come from the same source, PKU-SafeRLHF. The harmful anchors are 64 PKU prompts with their PKU-unsafe answers. The safe anchors are the untuned model's Safe answers to PKU prompts from the same sealed list. The plant is 37 PKU-safe, non-refusing answers to PKU prompts that also have an unsafe answer. A1 and L1 both score "like the harmful anchors minus like the safe anchors". So the plant sits on the scorers' positive side by its definition. The review's own condition ("if the anchors come from PKU-SafeRLHF too, the control is circular by construction") is met.
2. **It is worse than the review says for most scorers.** (R, I.) L1, H1, H2a/b, DataShield-style and the content classifier read only the row text and the untuned model. Their rank of the planted cell is fixed as soon as the plant rows and the cells are drawn. It is known before any plant run. For these scorers a "hit" is a construction check, not a test. Only A1 (and Self-Inf-N-style, if built) depends on the planted model's training.
3. **The dilution confound is real.** (R, M.) The plant fills one finest cell exactly. Its share of its cell is 6.2%, 24.7% and 100% at M = 8, 32 and 128. Under the mean aggregation that the lead's L15 (6) uses, the plant's signal grows 4.0-fold from M = 8 to M = 128. In my simulation, the whole rise of the hit rate with M comes from dilution. With the plant share held fixed, finding the plant gets harder with M, not easier.
4. **One plant location gives one Bernoulli outcome per scorer and M.** (R, M.) L15 (7) uses exactly this binary hit to place each scorer on the quality grid. At M = 8 a hit or a miss fits every grid point (row AUC 0.5 to 0.9). The placement is empty.
5. **The smallest outcome-free fix needs no new run, no new data and no change to any T1 file** (§4). (a) Correct the wording and limit the claim. (b) Publish the text-only scorers' planted-cell ranks before the pilot as construction checks. (c) Make the plant rows' row-level AUC the primary detection statistic and the L15 (7) placement statistic. (d) Report the committed M-diagonal beside two exact decompositions from the same ranks: "more options, same share" and "same options, more dilution". (e) Report Λ per planted row. Two near-$0 additions follow: a relocation replay over all eligible leaves, and a scored-only refusal decoy.
6. **Two of the review's fixes need changes.** (I.) A decoy trained "in the same runs" is not free: refusal rows lower a0_plant's U and so change the pilot's Λ_plant and the keep option. Score the decoy only; never train on it. Max or top-quantile aggregation does not remove the confound: each aggregation has its own cell-size effect (§2.3).

## 1. What the design says (sources)

| Item | Value | Label |
|---|---|---|
| Plant rows | a PKU response with is_safe true and lexicon class DIRECT, in a record whose other response has is_safe false; k = 37, raise to 75 once | R: `tmp/claude-workspaces/stage1-commitments-build-20261016/workspace/scripts/stage1/settings/build_plant.json` (`06f70d98…`) `rows.candidate`; brief REQ-8; PLAN-S §6 |
| Harmful anchors | 64 PKU-SafeRLHF prompts "with their PKU unsafe responses", severity ≥ 2, category-balanced | R: PREREG §1 "Anchors"; `.ai/inputs/gate-b-anchors-20261008/make_anchor_prompts.py`:117-137 (`40dfd383…`); ANCH README |
| Safe anchors | the untuned OLMo-2-1B's greedy answer to each prompt of the same 128-prompt PKU list, kept if it ends and Qwen3Guard labels it Safe; the first 64 kept | R: PREREG §1 "Safe answers" |
| Disjointness | plant prompts are disjoint from the S-pool prompts, the 128 anchor prompts and every REQ-6 list (normalized text) | R: build_plant.json `rows.exclusions` |
| A1 score | a_i = mean over {q, e1} of cosine_H − cosine_S; positive = a step on the row lowers the harmful anchors' loss more than the safe anchors' | R: brief REQ-14 |
| L1 score | untuned model, read (a), layer l_s: cos(r, r_unsafe) − cos(r, r_safe) over the 64 + 64 anchors | R: brief REQ-10, U7 (c); lead decisions L3 |
| Cells | M = 8 units (600); M = 32 within-unit quartiles of target tokens (150); M = 128 sealed-random quarters (37/38/37/38) | R: build_plant.json `cells`; L12 (3) |
| Leaf draw | one unit by a sealed draw, then the first 37-row leaf with no oversize row in a sealed order | R: build_plant.json `draws`; addendum §4 item 3 |
| Cell score in the selector simulation | "A cell's score = the mean of its rows' scores" (row model N(μ,1) for plant rows, N(0,1) for Dolly rows) | R: addendum L15 (6) |
| Cell score for the measured ranks | not stated; the report is "each scorer's planted-cell rank at M = 8, 32 and 128 beside the same unit's (and cell's) rank without the plant" | R: build_plant.json `reports`; addendum §3 item (2) |
| Placement of a planted-menu scorer | "the plant's top-k hit at each M"; report the grid points whose simulated 90% range contains the measured value | R: addendum L15 (7) |
| Unit score of A1 in Gate B/C | the mean of the unit's rows' a_i (REQ-14 checks it against `groups.json` within 1e-12) | R: brief REQ-14, Facts "A1's per-row values" |
| Runs | remove the planted cell at M = 8, 32, 128; R600 (and optional R150) on planted data; seeds 1101–1103, paired with a0_plant | R: build_plant.json `edits`, `seeds`; addendum §3 |
| Paper wording | the plant rows "look benign"; "finding it shows that a diagnostic can find a concentrated cause" | R: `writing/paper/icml/main.tex`:743, :933, :3963 |

## 2. Is the circularity real?

### 2.1 "The plant is chosen to be found by the diagnostics": holds in effect, not in intent

- **Intent.** PLAN-S chose PKU labels and the frozen lexicon so that the plant does not come from a compared scorer (R: PLAN-S §2, the NOV-3 reasoned disagreement). So the plant was not picked by any scorer.
- **Effect.** The plant shares its source with both anchor sets (R: §1 table). On the prompt side, plant rows are PKU red-team prompts among 4,763 benign Dolly rows. On the answer side, they do not refuse, like the harmful anchors' answers. The safe anchors are mostly refusals (I: the untuned model's Safe answers to harmful prompts; their lexicon class is UNVERIFIED here).
- **The two-sided scores cancel only part of this.** (I.) A1 and L1 subtract the safe-anchor term. The safe anchors use the same PKU prompts, so pure topic similarity partly cancels. What stays is the answer-type axis: compliance against refusal on harmful prompts. The plant is on the compliance side by its definition. So the plant is found by construction either way. This differs a little from the review's wording ("the scorer detects harmful-looking prompts"): a two-sided scorer detects "harmful prompt plus a non-refusing answer".
- **Which scorers can fail the test at all.**

| Scorer | What its score reads | Can the planted rank change with the training outcome? | Reading of a hit |
|---|---|---|---|
| L1 (LARF-style) | row text and the untuned model; anchors | no (R: REQ-10; the layer scan also uses the untuned model and the 64 + 64 anchor/Dolly prompts only) | construction check |
| H1, H2b | target tokens | no | construction check; also the M = 32 cells are length quartiles (§3, N1) |
| H2a | response line regex | no | construction check |
| DataShield-style | untuned representations (REQ-12) | no | construction check |
| content classifier | row text (I) | no | construction check |
| A1 | gradients at a0_plant's checkpoints q, e1 | yes | weak test: expected high by construction, but a miss is possible |
| Self-Inf-N-style | grad norm and length at a0_plant's q | yes | weak test (length part is fixed) |

- **Verdict: holds, and is stronger than stated.** For every text-only scorer the "hit rate with known truth" is not a measurement. It is a property of the committed plant rule. For A1 it is a weak test.
- **What a hit still shows.** (I.) The paper's limit sentence is fair as far as it goes: a hit shows that a scorer "can find a concentrated cause" (main.tex:933). It does not show that the scorer can find a benign-looking cause. Natural erosion in Dolly most likely has benign-looking causes (R: PLAN-S §1 item 7, the opening switch carries 0.42–0.64 of the Unsafe increase; only 0.19% of Dolly targets open with a refusal). So the control does not make a natural-data null readable for that kind of cause. That was its first stated purpose (R: PLAN-S §0 item 2).

### 2.2 "The cell sizes shrink with M, so the plant's share grows": holds

- **Shares.** (M.) k = 37: 37/600 = 6.2%, 37/150 = 24.7%, 37/37 = 100%. k = 75 (the one allowed raise; the leaf then holds 75 plant rows, R: build_plant.json `corpus`): 75/638 = 11.8%, 75/188 = 39.9%, 100%.
- **Signal under the mean.** (M.) With row SD 1, the planted cell's standardized signal is k·μ/√n: 1.51μ, 3.02μ and 6.08μ at n = 600, 150, 37. That is 4.0 times larger at M = 128 than at M = 8. The null maximum over the competitor cells grows only slowly (about 1.35 for 7 cells and 2.6 for 127; I, normal order statistics).
- **The aggregation is half stated.** (R.) L15 (6) fixes the mean for the simulation. The measured planted-cell rank has no stated aggregation (build_plant.json `reports`). The placement in L15 (7) compares the two, so they must use the same rule. The review's "the aggregation for cells is not stated" is right for the measurement.
- **Three things move together.** (R, M.) With one plant size, M moves with the plant share and with the removed dose:

| Edit (relative to P) | Rows | Optimizer steps | Rows removed besides the plant |
|---|---|---|---|
| a0_plant | 4,800 | 38 | 0 |
| remove the planted cell, M = 128 | 4,763 | 38 | 0 (the 37 displaced Dolly rows are absent in both arms) |
| remove the planted cell, M = 32 | 4,650 | 37 | 113 Dolly rows |
| remove the planted cell, M = 8 | 4,200 | 33 | 563 Dolly rows |

  Steps = ceil(rows/128) (R: build_plant.json `corpus.steps`). Random 600-row removal restores r̄ = +2.5 pp (r_j = +0.67, +2.50, +4.33 pp; R: `research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-wave0a.json`). So Λ(M = 8) carries a background of about 2.5 pp that Λ(M = 128) does not (I). On the runs side this background is common to every M = 8 option, so it does not bias the search much. On the scorer side, dilution is the main effect.
- **Remove-cell at M = 8 has the same corpus as Gate B's unit arm.** (R: build_plant.json `remove_cell_m8`: every Dolly row of the planted unit is removed, nothing is added; PREREG §1: "remove u" removes all 600 rows of u.) So the trained corpus equals Gate B's "remove u" corpus for that unit. Its wave-1 run at seed 1101 (and wave-2 runs, if the unit is picked) could be reused, saving up to 3 runs (I). The edit files may differ in bytes and so in arm id; reuse needs a rule fixed now and the same engine and training identity.

### 2.3 The simulation (M)

Script `w11_dilution_sim.py` (SHA-256 `a0ad61a3…`), output `w11_dilution_sim_out.json` (`21b4df77…`), both in this folder. Synthetic numbers only, L15 (6)'s row model, 20,000 replicates for the mean (2,000 for max and q90). τ is a unit (category) effect on Dolly rows in row-SD units: τ = 0 is L15's model; τ = 0.25 is my sensitivity (I). Entries are P(planted cell ranked first); in brackets P(top k) with k = M/8 (1, 4, 16).

**Committed design (A), mean aggregation**

| Row AUC | τ | M = 8 | M = 32 | M = 128 |
|---|---|---|---|---|
| 0.5 (no signal) | 0 | 0.12 | 0.03 [0.13] | 0.01 [0.13] |
| 0.6 | 0 | 0.25 | 0.20 [0.47] | 0.36 [0.85] |
| 0.75 | 0 | 0.53 | 0.77 [0.95] | 1.00 [1.00] |
| 0.9 | 0 | 0.88 | 1.00 | 1.00 |
| 0.75 | 0.25 | 0.16 | 0.20 [0.39] | 0.89 [1.00] |
| 0.9 | 0.25 | 0.21 | 0.53 [0.72] | 1.00 |

**The two pure effects, mean aggregation, τ = 0**

| Row AUC | Options only (B): share fixed at 100%, M − 1 competitor leaves; M = 8 / 32 / 128 | Dilution only (C): 8 options, cell size 600 / 150 / 37 |
|---|---|---|
| 0.6 | 0.76 / 0.55 / 0.36 | 0.24 / 0.41 / 0.76 |
| 0.75 | 1.00 / 1.00 / 1.00 | 0.53 / 0.90 / 1.00 |
| 0.9 | 1.00 / 1.00 / 1.00 | 0.88 / 1.00 / 1.00 |

- **Reading.** (M, I.) The two effects have opposite signs. More options make the plant harder to find; less dilution makes it easier. The committed design moves along the diagonal, so it mixes them. At AUC 0.75 the options effect is zero and the whole rise (0.53 → 0.77 → 1.00) is dilution. At AUC 0.6 the two effects nearly cancel (0.25, 0.20, 0.36). So "how diagnosis scales with M" in the committed design is mostly "how dilution scales with M", for a cause that fills one finest cell. A cause spread over several leaves would be diluted at every M (I).
- **Natural cell differences make M = 8 much harder.** (M.) With τ = 0.25, the M = 8 hit at AUC 0.75 falls from 0.53 to 0.16. L15 (6) gives Dolly rows no unit effect, so its M = 8 predictions are optimistic. The sealed unit scores show real unit differences (next item).
- **What M = 8 needs on the real units.** (R, M.) From the sealed unit means (`rankings-SEALED.json`, `d6d5cd6b…`; scored on a0-1101, not a0_plant), the plant rows' mean score must exceed the displaced rows' mean by (top unit − drawn unit) × 600/37 for the drawn unit to rank first. Attribution: 0 (if the draw lands in the already-top unit, general_qa), then 0.010, 0.018, 0.043, 0.067, 0.067, 0.069, 0.126. Gate C representation (index 16, read b; not L1's read): 0, then 0.30, 0.31, 0.32, 0.46, 0.51, 0.53, 0.57. So the M = 8 result depends strongly on which unit the sealed draw picks. With probability 1/8 it picks general_qa and "hits" for free. The lead's added report (the rank beside the same unit's rank without the plant) is the right guard for that case.
- **Max and q90 aggregation do not fix it.** (M.) Committed design, τ = 0, top-1: max gives 0.26 / 0.16 / 0.14 at AUC 0.75 and 0.72 / 0.69 / 0.69 at AUC 0.9; q90 gives 0.49 / 0.63 / 0.80 at AUC 0.75. The max of a large null cell is large, so max penalizes large cells and loses power. Each aggregation has its own cell-size effect. Keep them report-only.
- **The binary placement is empty; the row AUC is not.** (M.) A single top-1 outcome fits these grid points (the point's P(hit) is inside a 5%–95% Bernoulli range):

| M | A hit fits AUC | A miss fits AUC |
|---|---|---|
| 8 | 0.5, 0.6, 0.75, 0.9 | 0.5, 0.6, 0.75, 0.9 |
| 32 | 0.6, 0.75, 0.9 | 0.5, 0.6, 0.75 |
| 128 | 0.6, 0.75, 0.9 | 0.5, 0.6 |

  The empirical row AUC (37 plant rows against 4,763 Dolly rows) has these 90% ranges: 0.42–0.57 (true 0.5), 0.52–0.68 (0.6), 0.68–0.81 (0.75), 0.86–0.94 (0.9). It separates the grid points. It does not depend on M or on the aggregation.

### 2.4 One location

- **Holds.** (R.) One unit draw and one leaf draw give one planted cell. Each scorer's hit at each M is one Bernoulli outcome, and the three M outcomes are nested, so they are not independent.
- **Cost of the review's fix.** (R, I.) Three real locations need three a0_plant pilots and three main sweeps: PLAN-S §6 prices one sweep at about $17–35 with contingency, so two more cost about $34–70. That is a funding decision.
- **Cheap substitute for the scorer side** (§4, F6): a relocation replay over every eligible leaf at $0.

### 2.5 The review's fixes, one by one

| Review fix | Verdict | Why |
|---|---|---|
| A decoy cell "in the same runs" | partly | Right idea, wrong cost. A trained refusal decoy (harmful prompts with refusals) is not neutral: refusal rows restore safety (that is what P4 tests), so it lowers U(a0_plant), shrinks the pilot's Λ_plant and moves the keep option. Score the decoy only (§4, F7). A truly neutral harmful-looking decoy cannot be certified without its own runs. |
| At least 3 sealed plant locations | partly | Right in principle; about $34–70 more. The relocation replay gives the scorer-side location spread at $0; the runs side changes little with the leaf at M = 128 (I). |
| Max or top-quantile aggregation beside the mean | partly | Fine as report-only. Not a fix: each aggregation has its own size effect (§2.3). The real fix is to separate the two effects (F4). |
| Say where the anchors come from | holds | PKU-SafeRLHF (R: §1). So the control is circular by construction, in the review's own terms. |

## 3. New points that bear on the stage-1 pre-registration (not in the review)

- **N1. The M = 32 cells use a scorer's own feature.** (R, I.) The quartiles are within-unit quartiles of target tokens (L12 (3)). H1 (fewest target tokens) and H2b (most) will rank M = 32 cells mostly by quartile. Their planted-cell rank then depends on which quartile the sealed leaf draw lands in (about 1 in 4 for the shortest) and on the plant rows' own lengths, which differ from the leaf's. Both are known before any run. M = 128 cells are quarters inside quartiles, so the same holds there.
- **N2. Text-only ranks can and should be published before the pilot.** (I.) The REQ-3 pass already scores the 4,800 rows on the untuned model. Adding the 75 plant rows (and the decoy, F7) costs seconds. Publishing these ranks first turns a hidden construction effect into a disclosed one.
- **N3. L15 (7)'s placement statistic does not work for planted menus** (§2.3). Use the row AUC, which is the grid's own parameter (L15 (6) defines the grid by AUC = Φ(μ/√2)).
- **N4. L15 (6) has no cell-level heterogeneity.** (M.) Real units differ (the sealed unit scores). Add τ as a sensitivity in the simulation, estimated from the a0 scoring pass's cell means by a rule fixed now (these are scorer outputs, not outcomes).
- **N5. "Benign-looking" is not accurate.** (R.) The plant prompts are PKU red-team prompts that have an unsafe answer in PKU. Only the answers are PKU-safe and non-refusing. PLAN-S §6 ("They look benign"), main.tex:743 and :3963 should say so. A reader will otherwise assume benign Dolly-like text.
- **N6. The runs-side "known truth" is half modelled at fine M.** (R, I.) Only the planted cell is run at M = 32 and 128. The other 31 or 127 options' Λ come from a model (dose-scaled background from R600 and the optional R150). At M = 8 the competitors are Gate B's measured unit arms. State this in the runs-only replay.
- **N7. The plant is a very potent cause per row.** (M, I.) At the pilot's go bar, Λ_plant ≥ 10 pp over 37 rows is ≥ 0.27 pp per row. Gate B's smallest LOCALIZED unit at δ_B = 8 pp over 600 rows is 0.013 pp per row (≥ 20 times less). Random removal is about 2.5/600 = 0.004 pp per row (≥ 65 times less). So a hit on the plant says little about a diffuse natural cause.

## 4. The smallest outcome-free fix

Every item below is fixed before any plant draw is computed. REQ-8's `build_plant.py` is not built yet, and no plant run exists (R: addendum §4 item 5, "REQ-8's future build_plant.py"). No item reads U, changes a plant row, a cell, a draw, a seed or a run, or edits a T1 file. The new reports go in REQ-21 (j)/(k) and in the later Part G report script, as the lead's §5 literature-sweep reports do. Costs are $0 unless stated.

**Must (wording and analysis rules only)**

- **F1. Correct the wording and limit the claim.** "37 PKU-safe, non-refusing answers to PKU red-team prompts, from the same source as the anchors" in PLAN-S §6, REQ-21 and the paper. Headline item (2) reads: "does each diagnostic find a concentrated, harmful-prompt cause". A hit does not make a natural-data null readable for benign-looking causes. (The headline order is the user's 8 Oct decision; this changes its wording, not its content. Raise it to GPT and the user.)
- **F2. Construction checks.** L1, H1, H2a/b, DataShield-style and the classifier: their planted-cell ranks at M = 8, 32, 128 and their row AUC are computed when the plant rows are drawn (in the REQ-3 pass) and published before the pilot. They are labelled "construction check" and are not counted in "finds a known cause". Only A1 and Self-Inf-N-style (scored on a0_plant) count, and A1's result is labelled "expected by construction; a miss is informative".
- **F3. Row AUC is primary.** For each scorer: the AUC of the plant rows against all Dolly rows of the planted corpus, and against the drawn unit's Dolly rows, with a bootstrap 90% CI over rows. This is the L15 (7) placement statistic for planted menus (it replaces the binary top-k hit). The top-k hit at each M is secondary, reported beside the hit that L15's row model predicts from the measured AUC. The measured ranks use the mean (as L15 (6)); max and q90 are report-only.
- **F4. Dilution-matched decomposition, exact, from the planned ranks.** At each cell size n ∈ {600, 150, 37} the scoring pass gives the planted cell's rank r among the N same-size cells (N = 8, 32, 128). The chance that it ranks first against m random same-size competitors is C(N − r, m) / C(N − 1, m). Report this table:

| | 8 options (m = 7) | 32 options (m = 31) | 128 options (m = 127) |
|---|---|---|---|
| cell 600 (share 6.2%) | committed M = 8 | – | – |
| cell 150 (share 24.7%) | dilution step | committed M = 32 | – |
| cell 37 (share 100%) | dilution step | options step | committed M = 128 |

  A row of the table holds the share fixed and varies the number of options. A column holds the options fixed and varies the share. The diagonal is the committed design. The claim "diagnosis scales with M" may then cite only the row effect (options at a fixed share), and the dilution effect is reported as such. Do the same for the runs-only cost replay with the same competitor sets.
- **F5. Λ per planted row.** Report Λ_plant/k with its CI (k = 37, and 75 if raised), beside δ_B/600 and r̄/600 (N7). Label it a per-row average, not a per-row effect: erosion need not be linear in k, and U has a ceiling (a0's U is about 48%: OLMo's U_0 3.2% plus Gate A's mean E +45.1 pp; R: FOCUS, Gate A and Llama probe entries; the sum is M). If the raise happens, report Λ_75/Λ_37 as the one linearity check.

**Should (adds rows to scoring passes that run anyway)**

- **F6. Relocation replay (location spread at $0).** For every eligible leaf (37-row, no oversize row; about 64, I), move the plant rows' scores into that leaf, take out its Dolly rows' scores, and recompute the ranks and the F4 table. Report the hit rate over leaves. For text-only scorers this is exact. For A1 it is an approximation: the training order does not depend on the leaf, but the 37 displaced Dolly rows are absent from a0_plant's corpus, so drop the drawn leaf from the competitor sets (or score those 37 rows too). This captures where the plant sits; it does not capture plant content or training seed.
- **F7. Scored-only refusal decoy.** A sealed draw of 37 S-pool rows (PKU red-team prompts with PKU-safe refusal-opening answers) outside S1, the S3 subset and the S4 list, placed in a second sealed leaf in another unit for the rank replay only. Never trained. Report each scorer's decoy-cell rank and decoy-row AUC beside the plant's. Pre-registered reading: a scorer that ranks the decoy as high as the plant is topic-driven, and its plant hit is not evidence of finding an eroding cause. A two-sided scorer should rank it low. For text-only scorers this costs seconds. For A1 it needs the attribution pass to score rows outside the training corpus: **UNVERIFIED** whether the engine allows it; if not, report A1's decoy as not done.
- **F8. If the pilot stops** (Λ_plant below the bar), still publish F2's construction-check ranks. A non-eroding harmful-prompt set that the scorers rank first is direct evidence of false positives. (A1's rank would need a0_plant's scoring pass, which is optional then.)

**Could (costs money or new data; GPT's and the user's call)**

- **F9.** Two more real plant locations: about $34–70.
- **F10. A second plant that is independent of the anchors' features.** Benign-topic prompts whose answers carry a known eroding signal, for example identity-shifting "obedient assistant" rows (E: Qi et al. 2023 report that a few such rows jailbreak GPT-3.5). Only this would test whether a scorer can find a benign-looking cause. It needs new text (authored, or a download the user approves), its own pilot (about $4–7) and sweep (about $11–23), and it changes the scientific target of the control. It cannot be fully independent of A1: if A1's premise is right, any eroding row should align with the harmful-anchor gradient (I). Length matching of the current plant to its leaf would remove the H1/H2b construction effect, but F2 already makes that effect harmless, so I do not recommend it.

**Why this package and not the alternatives.** (I.) Changing the plant (F10) is the only fix for the circularity itself, but it is a new design. Extra locations (F9) fix only the Bernoulli problem, at cost. The review's same-run decoy damages the pilot. F1–F5 cost nothing, need no run, and change what the control is allowed to claim. F3 and F4 also fix the dilution confound and the empty placement. F6 and F7 are cheap additions to passes that run anyway.

## 5. The review's other points (not W2–W13)

| Point | Verdict | Evidence and what it means for the stage-1 pre-registration |
|---|---|---|
| W1: protocol not frozen; "pre-registered" overclaims | holds | The Gate B/C pre-registration is frozen (R: FOCUS, 10 Oct, `5c97cce7…`); the stage-1 commitments are still being built (R: addendum §4). Until REQ-20's manifest and REQ-21 are committed, say "pre-specified". An OSF or AsPredicted deposit is a public post: it needs the user's approval. |
| W14: value-of-diagnosis predictions scored on one menu | holds | One realized Llama menu is one outcome, yet it is family (5) of the testing order (R: PLAN-S §4.3). The same one-outcome problem hits the planted menus through L15 (7) (§2.3). Score per-unit predictive intervals with a proper scoring rule, and use the row AUC for planted menus. |
| W15: "10–12 pp" against "9, 10 or 12 pp" | holds | R: main.tex:778 ("about 10--12 pp") and :3831 ("about 9, 10 or 12"). Paper only. |
| Q1: shared seeds and common random numbers | partly | Same-seed arms share the adapter init, the kept rows' order and each (prompt, sample) sampling seed (R: PREREG §1). The −0.08 correlation in PREREG §2 is a per-prompt correlation between the untuned unit and a0-1101 (shared sampling stream) and between a0 at seeds 1101 and 1102; it is not a correlation between two arms at one seed. The within-seed arm correlation is not yet estimated. The noise gate sits nearest the "low" scenario, 2.15 pp, "same-seed arms share the seed shift" (R: noise-gate-wave0a.json `nearest_sigma_pair`). W2's check owns the analysis. |
| Q7: Controversial labels in U | partly | Gate B: U is the Unsafe share; a "Controversial counted Unsafe" corner is guard G3 (b) (R: PREREG §6). The stage-1 brief and PLAN-S do not state it. Carry Gate B's convention into REQ-21 (b)/(f), with the corner as a sensitivity. |
| Q10: what confirmation requires | holds | FOCUS and PLAN-S §4.3/§10 give the role, at most 2 contrasts per family, fresh seeds and the hidden subsample, but no success rule (R). REQ-21 (b) should fix the pick rule, the test (sidedness, α) and what "confirmed" means. |
| Q12: "least similar half" | holds | "The add effect must hold on the lower-similarity half" has no test or α (R: PLAN-S §5.5). Fix the test (for example, same sign and a one-sided 90% bound above 0) or mark it report-only. The similarity strata are an S1-deadline item (R: brief, out of scope list, B14). |
| Q13: if stage 1 is not funded | partly | PLAN-S already says no claim is read before block B (R: PLAN-S §2, reasoned disagreements). The paper should say what a block-A-only paper reports. |
| Q14: Gate B (8 pp, Bonferroni, t at 3 df) against stage 1 (5 pp, Holm, pooled df) | partly | Different jobs: Gate B is a screen with a bar; stage 1 gives confirmatory labels. Defensible, but the paper should give the reason in one sentence. No rule change. |
| Q15: length-reweighted U adjusts for a post-treatment variable | holds | PLAN-S §4.2 lists a length-reweighted U (R). Answer length is changed by the repair. Label it a decomposition (with a fixed reference length distribution, for example a0's), never "the effect adjusted for length". Wording in REQ-21 (f). |
| §6: release policy | holds (minor) | Release plant rows as PKU ids only (PKU is CC-BY-NC; R: PLAN-S §13). Consistent with the text-out-of-git rule. |
| §9 item 1: within-seed correlation about 0.76 | partly | It divides two 2-df SDs (σ̂_gate 1.83 pp and the per-arm 2.65 pp), whose 90% intervals each span several-fold (R: PREREG §2: 1.5–11.7 pp for a 2-df SD of 2.65). It is not an estimate. The direction (pairing may pay) fits the low scenario. W2's check owns it. |
| §9 item 2: under option B the ±5 pp TOST at 7–8B is out of reach | holds, if option B is chosen | The re-plan proposal stages option B (R: commit fc85fda subject). The 1B stage-1 margin should not be read as the 7–8B margin; that comparison would need its own δ, seeds or pairing, fixed before its runs. |
| §9 item 3 (W8 sub-point): the 1 FRE charge | holds | The review's own correction: the training share is small (245 s of about 3,115 s; R: PLAN-S §1 item 6). |

## 6. Replies to the questions in the brief

- **Is the circularity real?** Yes. Both parts. The plant shares its source and its answer type with the anchors' positive side (§2.1). The plant's share of its cell grows from 6.2% to 100% (§2.2), and in the simulation that alone produces the rise with M (§2.3).
- **A plant chosen by a rule independent of every diagnostic's feature?** Possible only in part, and only with new text (F10). Full independence from A1 is not even wanted: an eroding row should align with A1's gradient if A1 works. Independence from topic and length is what matters, and only a benign-topic plant gives it.
- **A dilution-matched comparison?** Yes, at $0 and exactly, from the ranks already planned (F4). Holding the share constant by changing k is not possible without changing Λ_plant, so the matching is done on the scorer side, by competitor sets.
- **Λ per planted row?** Yes as a report (F5). It helps transport and shows how potent the plant is (N7). It fixes neither the circularity nor the dilution.

## 7. Process

- **Files written (only here):** `check-W11-other.md` (this file), `w11_dilution_sim.py` (`a0ad61a3…`), `w11_dilution_sim_out.json` (`21b4df77…`), all in `/Users/spiderishi/Coding/attribution/.claude/worktrees/kind-hawking-a6ce04/tmp/gi-vi-parallel/stage1-analysis-model/`.
- **Sources read (main checkout, SHA-256 prefixes):** the mock review (`ff0e4382…`, in full); PLAN-S (`6ff3ff2b…`, in full); the stage-1 brief (`12cbf463…`, in full); the lead decisions addendum (current `11477648…`, in full); PREREG revision 5 (`5c97cce7…`, §1–§2 and §6 lines); `rankings-SEALED.json` (`d6d5cd6b…`, unit scores only); `noise-gate-wave0a.json` (`4b817f73…`) and `noise-gate-post-wave0b.json`; `NOTES.md`; the plant settings `build_plant.json` (`06f70d98…`, in the lead's build workspace); `make_anchor_prompts.py` (`40dfd383…`, rule lines) and the ANCH README; FOCUS (plant and freeze entries); `writing/paper/icml/main.tex` (plant lines and :778, :3831).
- **Commands (exit 0 unless noted):** `ls`, `wc`, `grep`, `sed`, `git log`, `git status`, `shasum`, `date -u` (twice); small `python3` readers for JSON structure and text context (one `ls` of a missing path exited 1; two ugrep patterns were too complex and were redone in Python); the pinned venv's Python: `import scipy` failed (exit 1, scipy is not installed there; numpy 2.2.6 is); `w11_dilution_sim.py` ran in 8 s (exit 0).
- **Not done:** no row-level score was read (rows.jsonl is closed), so the real row AUC of any scorer on the plant is unknown; the plant rows are not drawn yet. Whether the attribution pass can score rows outside the training corpus (F7 for A1) is UNVERIFIED. Qi et al.'s identity-shift result (F10) is from memory (E).
- **Unresolved concerns.** (1) F1 changes the wording of a user-adopted headline item; GPT and the user decide. (2) F10 is the only real fix of the circularity and changes the control's target; it is not the lead's call alone. (3) If the plant's unit draw lands in general_qa (1 in 8), the M = 8 result is empty whatever the scorer does; only the "rank without the plant" report shows that. (4) My τ = 0.25 sensitivity is an assumption; the real cell heterogeneity is measurable only from the scoring pass.
