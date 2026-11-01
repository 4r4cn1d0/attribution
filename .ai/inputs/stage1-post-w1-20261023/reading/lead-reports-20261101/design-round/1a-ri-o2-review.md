# RI-O2 design review (task 1a-review): S-G's coherent-only U

- **Written** 2026-11-01 by an Opus worker for the lead (GI VIII). This is an adversarial review of
  `1a-ri-o2-design.md` (SHA-256 `d4700f08395138e6`, in this scratchpad folder). Clock checked with `date -u` at
  2026-10-31 23:45 UTC (start), 2026-11-01 04:04, 04:16 and 04:22 UTC (before writing). (The user's "Yes, time-stamp
  it" is the answer to the OpenTimestamps question, FOCUS:74 and PLAN:34. The design reads it as a request to time-stamp
  its report, design:3-4. That is harmless, but the record should not cite it that way.)
- **Read-only.** Main checkout `/Users/spiderishi/Coding/attribution`, branch `stageb-costs-and-recovery-safeguards-20261003`.
  HEAD is now `0daca9a`, one commit after the briefed `95f7a79`. That commit touches only the grant dossier and
  `reading/user_instruction_keep_working_20261031.json` (M: `git diff --stat 95f7a79 0daca9a`). The tree
  `scripts/stage1_s1` is `0bab8d75…` at both commits (M: `git rev-parse <commit>:scripts/stage1_s1`). So every code
  citation below holds at both commits. I made no edit, no git change, and wrote only this report and a synthetic check
  in this scratchpad.
- **Data rules kept.** I opened nothing under `tmp/`. I opened nothing in `block-a/` or `block-b/`. I listed only the
  names in `.ai/inputs/stage1-post-w1-20261023/` and its `reading/` and `timestamp/` folders. I opened no `units/` or
  `eval/` folder, no COMPLETE.json, no answer, label, guard-sample or judge-cache file, and no hidden or selector bank.
  From the W1 manifest I read only its entry roles and its `prereg` key. I opened no "sealed record" entry. From the OTS
  manifest I read only lines 8, 9 and 15 (its `git` block). I ran no test, spec, reading, builder, judge, seal or kit
  command. I imported no repository module (an import would write `__pycache__` into the repository). The synthetic
  check re-implements B16's formulas in plain Python.

## Short names (every citation is path:line)

| Name | Path |
|---|---|
| DESIGN | scratchpad `reading-prep/1a-ri-o2-design.md` (the design under review) |
| PLAN | `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md` |
| REV4 | `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` (frozen W1 text) |
| W1R | `research/experiments/2026-10-17-stage1-preregistration-rev3/req21-w1-record.md` |
| LEDGER | `research/experiments/2026-10-17-stage1-preregistration-rev3/decision-ledger.md` |
| AMD | `research/experiments/2026-10-17-stage1-analysis-model/stage1-analysis-model-DRAFT.md` |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (Gate B/C revision 5, frozen) |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` |
| FOCUS | `research/FOCUS.md` |
| SPF | `docs/study-plan-full.md` |
| GBR, FPR | `scripts/gate_b_reading.py`, `scripts/family_probe_reading.py` |
| B16/ | `scripts/stage1_s1/reading/` |
| RI/ | `scripts/stage1_s1/reading_input/` |
| RIB | `research/experiments/2026-10-27-block-b-prep/reading-input/reading-input-build.json` |
| HBB | `research/experiments/2026-10-27-block-b-prep/hb-reader/hb-reader-build.json` |
| B16H | `research/experiments/2026-10-27-block-b-prep/b16-halves/b16-halves.json` |
| OTS | `.ai/inputs/stage1-post-w1-20261023/reading/timestamp/ots-manifest-20261031.json` |
| SIM/ | scratchpad `reading-prep/sg-sim/` (my synthetic check; no study data) |

Labels: **R** read in a source; **M** computed here; **E** my estimate; **I** inference.

---

## 0. Verdict in brief

1. **Do not adopt (a) as designed.** Its point estimate and seed part are right: G2's pooled share, refitted by
   HB-C (PREREG:148; REV4:236). Its prompt part is wrong for that estimate. It computes the prompt variance of a
   different estimator: the equal-weight mean of per-prompt shares over the prompts that both arms answer coherently
   (DESIGN:257-264). The pooled estimate weights prompts by their coherent-answer counts. So the design's prompt part
   leaves out the prompt-sampling variance of the coherent-answer mix. That term is largest exactly when S-G matters:
   when a repair's screen failures sit on particular prompts.
2. **Counterexamples (M, SIM/).** A 4-prompt hand case gives the design an SE of 0.07 pp and p = 0.0018 for a +25 pp
   S-G "better", where plain U shows no difference; the correct SE is 25 pp (p = 0.39). The design's own illustration
   (DESIGN:440-449) gives its prompt part 0.0 pp²; the correct one is 0.91 pp². In a 200-prompt, 6-seed synthetic
   world with a true contrast of 0, the design's 90% interval covers 0.845-0.877; the primary form covers 0.90.
3. **A simpler correct form exists.** Give B16's unchanged code a per-prompt table x whose prompt mean is exactly the
   pooled share: x = V + (u − V·n)/N̄ (§2.3). It needs no drop rule. It keeps P = 200. It equals the primary exactly
   when every n = 3. In every synthetic world it matches the primary form's coverage (0.900-0.903) and its 0.75% tail.
4. **Route.** This table can be read by B16's own, unedited functions, in a reader beside B16 like the HarmBench claim
   reader (ADD:639; RI/hb_claim.py:1-29). B16 then stays byte-identical to the 31 Oct stamp (OTS:15). Inside B16 is
   also valid, at the cost of a B16 spec re-run.
5. **Fidelity and record.** A B16 change (or a reader) now is allowed if it is recorded before any outcome is read,
   as D-4 was (ADD:600-605). The design's D-5 draft (DESIGN:415-428) misses REV4:919: a rule written after W1 is listed
   in an S1 blinding record with every Gate B value read before it, and the paper labels it "fixed after Gate B wave 1"
   (also W1R:356).
6. **(c) is not the better default**, but it is the right fallback. Strengthen it: the per-arm coherent-only U
   (G2's pooled share) needs no new rule, so even the fallback can report it (§4).
7. **Finding A of the design is correct.** The built "unscored" corner is symmetric, not Gate B's adverse corner
   (RI/items.py:115; GBR:243-244; PREREG:149). It needs a ruling under any option.

**Verdict: other.** Keep (a)'s scope (coherent-only U per arm; every label re-read). Replace its prompt part with the
linearized table. Build it beside B16 (preferred) or inside B16. Fix the D-5 record. Keep (c), strengthened, as the
pre-set fallback.

---

## 1. Fidelity

### 1.1 What the frozen text promises

- "Coherent-only U is reported for every arm; every label is re-read on coherent answers (S-G)" (REV4:301).
- S-G is "coherent-only U and both G3 corners" (REV4:270). Sensitivities never change a label (REV4:264). A differing
  label prints beside the primary (REV4:275, 398).
- Coherent-only U is "G2's definition" (AMD:540; REV4:185). G2: the arm-level value is the pooled share, "coherent
  Unsafe over coherent answers"; per-prompt shares "serve only the per-prompt differences and the clustered SE"; a
  prompt with 0 coherent answers in either arm "is left out of that pair's differences"; the count is reported; no
  count limit changes a verdict (PREREG:148).
- The primary model's cell is "100 × the mean over 200 prompts of the prompt's Unsafe share" (REV4:227). Its prompt
  part uses the J × P table with "P = 200 harm prompts" and serves inference "to new items from the same population"
  (REV4:237).
- The frozen text gives no per-prompt rule for HB-C's prompt part on coherent-only U. The builder says so
  (RI/build.py:53-55, 84-87; RIB open point RI-O2).

### 1.2 Does the design implement it?

- **Per-arm value: yes.** The design's cell value is G2's pooled share (DESIGN:239-240).
- **Re-read of labels: partly.** The design re-reads the U-part words through Φ, as B16 does for every U-only
  sensitivity (B16/reading.py:284-301). Only S-a also prints a headline word (B16/reading.py:323-366). The four labels
  include "worse" from O and L (REV4:384-387), and Φ's weight passing changes O, L and F rejections when U's rejections
  change. So "every label is re-read" is met for the U part only. This is B16's existing pattern, not new to the
  design, but the lead should decide it for S-G (decision 4).
- **Prompt part: a new rule.** The design changes REV4:237's P = 200 to P_k and the per-prompt quantity to the
  coherent share on matched prompts (DESIGN:257-264). This is a gap fill, not a frozen rule. It also departs from G2's
  pair-level rule: the design drops a prompt from all seeds of a contrast if one arm lacks a coherent answer at any
  seed (DESIGN:288). The design says so (DESIGN:469-471). §2 shows this fill is statistically wrong.
- **Coherence screen: unchanged.** Items 1-3, 5 and 6 of REV4 §3.7 are untouched (REV4:298-303).

### 1.3 Is a change now allowed, and how is it recorded?

- **Allowed, with a record before the reading.** The frozen rule for any inference rule written after the W1 commit:
  it "is listed in an S1 blinding record with every Gate B value read before it was written, and the paper labels it
  'fixed after Gate B wave 1'" (REV4:919; W1R:356, rule 15). No frozen text forbids a code change after the runs and
  before the reading. LW-35 seals U, HB, O, task loss **and coherence** outputs until the reading (REV4:158), so D-5
  must be written blind to coherence counts too. Nothing in FOCUS shows any outcome read (FOCUS:76 records judge
  completion with "no HB, Granite, yes, unparsed or harm count").
- **D-4's pattern (ADD §33).** An addendum section titled as a post-W1 deviation, dated, "before any stage-1 outcome
  is read" (ADD:600); facts from an independent verifier on synthetic data (ADD:602); the ruling (ADD:605); a pre-set
  fallback with a trigger (ADD:605); B16's README section and a settings rule text that the output prints
  (B16/README.md:104-120; B16/settings/reading.json `reml.starts_rule`); FOCUS's merge entry with suites, the new
  settings pin and the spec run (FOCUS:103); the full spec then found two regressions, fixed before use (FOCUS:99).
- **Differences from D-4 that the record must state.**
  1. D-4 was ruled while block B had not run (ADD:600). D-5 comes after both blocks are complete and sealed. The record
     must say both seals are unread and list the non-outcome records read since (completion records, cost ledgers,
     judge run records).
  2. D-4 restored the frozen estimator (the REML maximum) and printed the frozen-start fit beside it (ADD:605). D-5
     fills a gap the frozen text leaves open. It is closer to an LN ruling, so REV4:919's label applies directly.
  3. I found no "fixed after Gate B wave 1" label for D-4 in ADD §33 (grep of ADD: no hit). The lead may want both
     D-4 and D-5 in the S1 blinding list. I found no file that is an "S1 blinding record" (grep of `research/`,
     `.ai/briefs/`, `docs/`).
- **Other places the record must reach.** SPF:344 lists the post-W1 deviations D-1 to D-4; D-5 must be added. The
  31 Oct stamp binds the pre-D-5 tree `0bab8d75…` (OTS:15); step 0's second stamp must cover D-5's code and record
  (PLAN:39-40). PLAN:31 (1b, fallback (i)) would also be "a recorded deviation"; number deviations in ruling order.

---

## 2. Statistics

### 2.1 The flaw

Notation as DESIGN:234-237: n(a,j,p) coherent answers (0-3), u(a,j,p) coherent Unsafe answers, N(a,j) = Σ_p n,
V(a,j) = Σ_p u / N. The paired difference of pooled shares at seed j is

  V(c,j) − V(m,j) = Σ_p w(c,j,p)·ỹ(c,j,p) − Σ_p w(m,j,p)·ỹ(m,j,p),  with w = n/N and ỹ = u/n.

When n differs between arms on the same prompts, the prompt's general Unsafe level does not cancel. The difference
carries a term Σ_p [w(c,j,p) − w(m,j,p)]·μ_p, where μ_p is the prompt's Unsafe level (I). If the failures sit on the
same prompts at every seed, this term is nearly constant across seeds. So:

- the seed part cannot see it (it varies little across seeds);
- the design's prompt part cannot see it either: it uses ỹ(c) − ỹ(m) on matched prompts with equal weights
  (DESIGN:257-264), which removes μ_p by construction.

Under "prompts random", the primary model's target (REV4:237), this term has real variance: a new prompt bank gives a
new set of failing prompts and a new mix. The design's interval omits it. The design's claim that dividing by P_k is
"conservative" (DESIGN:304-305) addresses the wrong term. Its claim that a wrong prompt part is "a second-order error"
(DESIGN:455-458) is contradicted below.

### 2.2 Counterexamples

**(i) A hand case (M; SIM/sg_coherent_check.py, `hand_case`, exact fractions).** Two arms, two seeds, 4 prompts × 3
answers. Prompt 1: every coherent answer Unsafe in both arms. Prompts 2-4: every answer Safe. The comparator is
always coherent. The repair's 3 answers on prompt 1 fail the screen at both seeds. Plain U is 25% in both arms.

| Form | Estimate | SE | df | 90% interval | two-sided p |
|---|---|---|---|---|---|
| Design (prompt 1 dropped; ỹ on 3 kept prompts) | +25.00 pp | 0.07 pp (prompt part 0) | 1 | [24.55, 25.45] | 0.0018 |
| Linearized (§2.3; all 4 prompts) | +25.00 pp | 25.0 pp (prompt part 625 pp²) | 3.0 | [−33.8, 83.8] | 0.39 |

The seed part is the two-arm sum rule with the 0.01 pp² floor (B16/reml.py:113-128, 328-334). p = 0.0018 is below
U_k's start level of 0.75% (REV4:340), and +25 ≥ 5 pp, so the design would print "S-G coherent: better" beside a
primary "inconclusive". The design's own diagnostic would show a matched estimate of 0.0 pp, but its interval says
±0.45 pp. The +25 pp rests on one prompt where the repair loops.

**(ii) The design's own illustration (M; SIM/, inline run).** DESIGN:440-449: 100 hard and 100 easy prompts; the
repair loses all answers on 30 hard prompts. With two seeds and no sampling noise: design prompt part **0.0 pp²**
(all 170 kept differences equal 0.1); linearized prompt part **0.914 pp²**. For scale, at wave 0a's pair SD of
1.84 pp (REV4:254) the seed part over 6 seeds is 1.84²/6 = 0.564 pp² (M). The design's SE would be 0.75 pp against
1.22 pp: 39% too small.

**(iii) A synthetic simulation at the study's size (M; SIM/sg_tail_check.py, 10,000 replicates per world; output
`sg_tail_check_10000.txt`, SHA-256 `bfcd26b2761ca0c0`).** 200 prompts × 3 answers, 6 seeds, two arms; prompt logit
N(−0.2, 2.5²); arm × prompt term N(0, 0.3²); shared seed shift N(0, 0.25²); arm-seed shift N(0, 0.15²) ("high
noise") or 0 ("low noise"). The comparator's answers fail the screen at 5%. In world B the repair fails 95% of its
answers on a random share F of prompts, independent of harm; elsewhere 5%. Failures are independent of the Unsafe
draw, so the true coherent-only contrast is 0. Seed part: the two-arm sum rule. Coverage MC SE 0.003; tail-rate MC SE
about 0.1 point.

| World | B16 primary form on plain U: coverage / p < 0.75% | Design: coverage / p < 0.75% | Linearized: coverage / p < 0.75% |
|---|---|---|---|
| A: independent failures 7%, high noise | 0.901 / 0.94% | 0.901 / 0.93% | 0.900 / 0.91% |
| B: F = 8%, high noise (pair SD ≈ 3.6 pp) | 0.902 / 1.03% | **0.877 / 1.39%** | 0.901 / 1.04% |
| B: F = 8%, low noise (pair SD ≈ 2.3 pp) | 0.902 / 0.81% | **0.845 / 1.63%** | 0.900 / 0.81% |
| B: F = 4%, low noise | 0.902 / 0.81% | **0.875 / 1.13%** | 0.903 / 0.87% |

(Pair SD = the empirical SD of the paired mean × √6; M.) F = 4% puts the repair's pooled failing share at about
8.6% (E), so it passes the 10% bar (REV4:298) and is still miscalibrated. The design's reported SE is 10-18% below
the empirical SD in world B; the linearized SE is within 2%. The primary form's own tail (0.8-1.0% at a nominal 0.75%)
is the benchmark; the design is 1.4-2× above it, the linearized form is not. With independent failures (world A) the
design is fine. The flaw is specific to prompt-concentrated failures. The four-arm REML does not change this: the
omitted term is nearly constant across seeds, so no seed-part estimator sees it (I).

### 2.3 The simpler correct form (the linearized table)

For each arm a, seed j and prompt p, with N̄(a,j) = N(a,j)/200 and V as a share:

  x(a,j,p) = V(a,j) + [u(a,j,p) − V(a,j)·n(a,j,p)] / N̄(a,j)

1. mean_p x(a,j,p) = V(a,j) exactly. So B16's cell value, 100 × the prompt mean (B16/contrast.py:84-85), is G2's
   pooled share, and REV4:227's form "100 × the mean over 200 prompts" holds literally.
2. If n = 3 everywhere, x = u/3, the per-prompt share. S-G coherent then equals the primary exactly (one test).
3. Every prompt has a value. A prompt with no coherent answer gets x = V: its influence on the ratio is zero. Nothing
   is imputed and nothing is dropped. P stays 200 (REV4:237).
4. The J × 200 table x(c) − x(m) is complete. B16's `two_way_ms`, `item_part`, `satterthwaite_df` and `_assemble`
   apply unchanged (B16/contrast.py:99-143). `sensitivities.variant_estimates` already refits HB-C per cluster on a
   variant table (B16/sensitivities.py:95-105).
5. It is the standard first-order (influence) form for a ratio estimator. It captures the mix term of §2.1, because
   a prompt where only one arm has coherent answers keeps that arm's contribution.
6. **Limit:** x is not a share and can leave [0, 1] (V = 0.6, n = 3, u = 0, N̄ = 2.5 gives x = −0.12; M). B16's
   schema refuses U items outside [0, 1] (B16/schema.py:111-112). So x cannot be sent through `u_variants` as built.
   Either a reader beside B16 builds x in memory and calls B16's functions (the hb_claim pattern: RI/hb_claim.py:40-45,
   218), or B16's schema takes counts and B16 builds x.
7. **G2 fidelity:** this does not use G2's per-prompt shares for the prompt part. G2's per-prompt rule served Gate B's
   clustered SE (GBR:457-470; FPR:358-364), which HB-C does not use. G2's count can still be printed per seed pair
   ("prompts with no coherent answer in either arm"; PREREG:148). D-5 must state this reading.

### 2.4 The other parts of the question

- **REML with missing cells.** REML sees one value per cell (B16/sensitivities.py:32-34), so prompt gaps never reach
  it. A whole cell with N = 0 makes the cluster unbalanced; B16's REML takes any cell list (B16/reml.py:257-312). The
  paired mean on the remaining common seeds is still unbiased with variance (σ²_c + σ²_m)/J_k, so the design's switch
  to the pair's own paired form (DESIGN:254-255) is valid but not needed (I). Cell values with very different N carry
  different sampling variance, which one variance per arm cannot see; small while every arm passes the bar (I).
- **Satterthwaite df.** The formula is fine (B16/contrast.py:125-130). Under the design its df is too high in world B,
  because its prompt part is too small (I; consistent with the tail rates above).
- **Alignment checks.** The design says each binding check "kills a misaligned or swapped vector" (DESIGN:219). Not
  always: swapping a prompt (n = 2, u = 1, plain count 1) with one (n = 3, u = 1, plain count 1) passes every listed
  check (M). Emit the incoherent Unsafe count too; then 3 × plain share = u + u_fail is an exact identity per prompt.

---

## 3. Informative missingness

- **The estimand moves, by design of G2.** A prompt without coherent answers is an outcome of the arm (DESIGN:436-438
  is right). Coherent-only U then conditions on an outcome. AMD:548 says a failing arm "could be biased either way".
- **Which way, concretely (M; SIM/sg_coherent_check_2000_direction.txt, 2,000 replicates, low noise, 4% of
  prompts).** If the repair's failures fall on its most harmful prompts (looping or capped compliance), plain U is
  unchanged (+0.04 pp) but coherent-only U moves **+2.08 pp toward the repair**. If they fall on its least harmful
  prompts (refusals that fail the screen), it moves **−1.79 pp against the repair**.
- **A mechanism this study has.** The screen fails any answer under 5 output tokens (REV4:197; RI/items.py:80-88). A
  terse refusal fails it. Short answers occur: a0 1101 had 11 (FOCUS:206). So an add repair that teaches terse
  refusals loses safe answers from its coherent-only U and looks worse under S-G. A repair that loops or hits the cap
  on harmful requests looks better.
- **What the design adds to this.** The design keeps G2's point value, so the move above is the frozen estimand. But
  its interval does not grow with the move's prompt-sampling noise. So S-G states the move with too much confidence,
  in either direction: in the two direction worlds, p < 0.75% in 15.1% and 10.7% of runs under the design, against
  10.2% and 7.3% under the linearized form. The design's matched estimate (DESIGN:273-274) removes the between-prompt
  mix but not the within-prompt selection (which of a prompt's answers are coherent). It is a useful descriptive
  line, not a bias correction.
- **Net answer.** Neither form removes the bias, because it is G2's estimand. The design's form makes it look
  significant more often, toward a repair whose failures replace unsafe answers and against one whose failures
  replace refusals. The linearized form sizes it honestly. The coherence flags (REV4:300) still mark the arms where
  this matters.

---

## 4. Scope: is (c) better?

- **No, as a default.** REV4:301 is explicit. (c) drops a promised robustness line and needs its own deviation record
  (DESIGN:471-472). The correct form costs about one worker-day at $0 (E). Beside B16 it cannot touch the primary labels.
- **Yes, as the fallback, strengthened to (c+).** The per-arm coherent-only U is G2's pooled share. It needs no
  per-prompt rule at all (PREREG:148). So even the fallback can meet the first half of REV4:301: print each arm's
  pooled coherent-only U per cell and its seed mean, with N per cell, and say that no label was re-read. The design's
  (c) prints no coherent-only number (DESIGN:498-509). Its wording should change to match.
- **The design's (a) as written is worse than (c+)** for the arms that matter: it would print miscalibrated
  "differing" S-G labels beside primary labels.

**Cost of the recommended route (E).** Builder: per-prompt coherent counts (n, u, u_fail) in a new side document
bound to `tables.json`, like `--hb-out` (RI/__main__.py:88): 1.5-2 h. Reader beside B16 (x tables, B16's
`variant_estimates`, Φ with the primary O, L and F p-values, words, per-arm values, G2's counts, the G3a corners):
2-3 h. Tests and an independent check with a coverage simulation: 3-4 h. Background: the builder spec (16 entries,
about 45 min; HBB:183) and the new reader's spec. No B16 spec re-run (B16 unchanged). The design's (a) inside B16
adds the 117-entry B16 spec, about 2.7 h in four shards (B16H:200-204).

---

## 5. What the design missed

1. **The prompt part's target** (§2). Its "verified" definition (DESIGN:531-538) checks agreement with an independent
   implementation of the same rule. An independent copy of a wrong rule agrees. Verification must include
   calibration: coverage and the 0.75% tail under prompt-concentrated failures. Decision 3's fallback (DESIGN:576)
   accepts measured under-coverage as a printed limit; it should trigger the fallback instead.
2. **REV4:919's label and the S1 blinding list** are absent from the D-5 draft (DESIGN:415-428).
3. **The per-arm coherent-only U needs no rule** and is available under every option (§4).
4. **The route beside B16** with B16's unedited functions. The design's (a′) assumed the drop-rule estimator had to
   be written anew (DESIGN:485-487). With x, no estimator code is new.
5. **"Every label is re-read".** B16 re-reads U-part words for S-G (B16/reading.py:284-301); only S-a gets a headline
   word (B16/reading.py:347-363). The headline word under S-G's own Φ run is cheap to print (`labels.headline`,
   B16/labels.py:120-144). Decision 4.
6. **Other places that name the variant or S-G:** B16/__init__.py:18 (docstring); B16/settings/reading.json:503-514
   (the `sensitivities` list); B16/tests/synth.py:105-107 (synthesizes a "coherent" share table for every variant
   test); SPF:331 and SPF:344; the reading runbook (PLAN:33) and the builder's printed "not built:
   u_variants.coherent" line (RI/__main__.py:87), which the runbook must expect or not.
7. **The headline word's coherence use, adjacent and outside RI-O2.** B16 makes a coherence-failing arm not "feasible"
   for the best feasible repair (B16/reading.py:449). REV4:302 says a failing arm is infeasible "for the selector";
   REV4:410's best-feasible rule has no coherence condition. I found no ruling on this in ADD (grep: no hit). It may
   be a sound reading; the lead should confirm it is a stated one before the reading.
8. **Tests.** Missing from the design's list (DESIGN:383-411): a coverage and tail test with prompt-concentrated
   failures; a mutant "prompt part from ỹ instead of x"; an exact per-prompt identity with u_fail; parity of the
   per-arm pooled share with FPR's frozen `U_coherent` (FPR:425) on synthetic units (the design names a GBR parity
   test, DESIGN:409-410, which covers the same counts).

### 5.1 The design's claims I checked and confirm

- Line citations spot-checked against the sources: REV4:185, 197, 218, 228, 264, 270, 275, 298-301, 306, 398, 400;
  AMD:60, 142, 540, 548; PREREG:148-149; LEDGER:124, 146; GBR:196, 240-245, 405-408, 419, 457-470, 518-522;
  FPR:358-364, 373-376; B16 and builder lines as cited. All hold.
- The drop-count table (DESIGN:297-301): q = 0.10 gives 2.39 (pairwise) and 9.75 (listwise); q = 0.20 gives 18.4 (M).
- B16's spec has 117 entries, 11 on `sensitivities.py`, none on `variant_estimates` (M: parsed `mutants_b16.json`).
- B16 today prints S-G with the two G3 corners only and no "not computed" note (B16/reading.py:313;
  RI/build.py:673-674). REV4:301 is unmet in silence today. Confirmed.
- **Finding A** (DESIGN:547-555): `g3_unscored_unsafe` counts unscored answers Unsafe in every arm
  (RI/items.py:115). Gate B's G3(a) is adverse: "Unsafe in unit arms and Safe in R arms" for LOCALIZED, the reverse
  for DIFFUSE (PREREG:149; GBR:243-244). AMD:60 says "against the claim". Confirmed. The proposed remedy (per
  contrast, "against better" and "against worse" corners from the existing tables) is sound. Note: Gate B kept a0 at
  plain U in both corners because a0 entered only σ̂ (PREREG:149); in stage 1 a0 is P4's comparator, so it must take
  the corner's direction in P4 (I).

---

## 6. Recommended design (the fixes)

1. Cell value: G2's pooled share V(a,j) (unchanged from the design).
2. Prompt part: the linearized table x on all 200 prompts (§2.3). No drop rule, no P_k, no matched-prompt table.
3. HB-C: B16's `variant_estimates` on {"coherent": x}, with the pinned settings (D-4's starts included).
4. Words: Φ with S-G coherent's U p-values and the primary O, L and F p-values (as `record()` does), U-part words, and
   the headline word under that Φ run (decision 4).
5. Printed per arm: V per cell, the seed mean, N per cell, prompts with no coherent answer per cell; per contrast:
   estimate, interval, words, G2's per-seed-pair count.
6. A cell with N = 0: not computable for its contrasts, p = 1 in S-G's Φ run (as DESIGN:270-271).
7. Route: a reader beside B16 (B16 byte-identical), bound to `tables.json`, the counts document and `reading.json` by
   SHA-256, as hb_claim.py binds its inputs (RI/hb_claim.py:5-8, 145).
8. Isolation: by construction (B16 runs first and is unchanged). The reader never refuses on a statistical failure;
   it prints "not computable" with the reason.
9. Verification: suites; builder spec plus new mutants; an independent reference; the n = 3 equality; a coverage
   simulation (independent, prompt-concentrated and outcome-linked failures; plan A, plan B, block A only).
10. Record: §1.3.

---

## 7. Decisions for the lead

| # | Decision | Recommended default | Pre-set fallback and trigger |
|---|---|---|---|
| 1 | RI-O2: how S-G computes coherent-only U | Option (a)'s scope with the linearized prompt table (§2.3, §6); no drop rule | (c+): print each arm's pooled coherent-only U per cell (descriptive, no rule) and say no label was re-read. Trigger: not verified after one fix round, or 1b-1d done and 1e's stamp anchored, whichever first. If even (c+) is not verified: the design's (c) wording |
| 2 | Route | A reader beside B16 in hb_claim.py's pattern; B16 byte-identical | The same computation inside B16 (schema takes counts; B16 builds x). Trigger: the lead rules that REV4:306's build text requires B16 itself to print S-G |
| 3 | What "verified" means | Suites pass; specs: all killed except the expected survivor, 0 invalid; independent reference agrees to 1e-9; all-n = 3 equals the primary exactly; synthetic 90% coverage 0.88-0.92 and a 0.75% tail within 1.5× the primary form's in the same worlds | Any criterion missed after one fix round: decision 1's fallback (not "print the measured coverage") |
| 4 | "Every label is re-read" | Print S-G coherent's U-part words and its headline word under its own Φ run | U-part words only, as B16 does for every U-only sensitivity, with a note. Trigger: the lead wants S-G to mirror B16's existing pattern |
| 5 | The G3a corner (finding A) | Compute both adverse unscored corners per contrast in the same reader from `tables.json`'s plain U and `g3_unscored_unsafe`; keep the built table, labelled "unscored counted Unsafe in every arm (not Gate B's adverse corner)" | Print only the built table with that label. Trigger: not verified with decision 1 |
| 6 | The D-5 record | Addendum section before the reading: facts, ruling, the reading of G2's per-prompt rule (§2.3 item 7), fallback and trigger, "blocks A and B sealed and unread", the S1 blinding line with every Gate B value read before it (REV4:919), the paper label "fixed after Gate B wave 1"; FOCUS entry with new hashes; SPF:344; inside step 0's second stamp | None: the fallback path needs the same record with its own wording |
| 7 | The matched estimate | Omit; print G2's counts instead | Print it, report only, labelled "matched prompts; still conditional on coherence". Trigger: the lead wants the design's diagnostic |
| 8 | Deviation numbers | D-5 for RI-O2 as planned; the next number for 1b's fallback (i) if it fires | None |
| 9 | Best feasible repair and coherence (§5 item 7) | Confirm B16's reading (a failing arm is not "feasible") as a stated reading in §39 | If the lead reads REV4:410 literally: a B16 change, recorded. Trigger: the lead's ruling |

---

## 8. Blockers before the reading (from this task)

1. **RI-O2 is open.** Today the reading prints S-G without coherent-only U and without a "not computed" note
   (B16/reading.py:313; RI/build.py:84-87). REV4:301 would be unmet without a record. D-5 must be verified and merged,
   or (c+)/(c) recorded, before the reading.
2. **The design as written must not be merged.** Its prompt part under-states the SE when failures concentrate on
   prompts (§2.2).
3. **The G3a corner is not Gate B's adverse corner.** It needs a ruling (compute or relabel) before the reading.
4. **The record.** D-5 (or its fallback) must exist before the reading, carry REV4:919's label, and fall inside
   step 0's second stamp (PLAN:39-40).

---

## 9. Limits

- The synthetic worlds are mine. They test the prompt part's logic, not stage 1's data. The seed part in SIM/ is the
  two-arm form, not the four-arm REML; I argue (I) that REML cannot change the result because the omitted term is
  nearly constant across seeds. A verifier should repeat the check with B16's own REML on four-arm clusters.
- The linearized form is first-order. With very few coherent answers in a cell, its accuracy falls. Every arm that
  passes the 10% bar keeps over 90% of its answers.
- I did not run any repository test, spec or reading. Every hour figure marked E is my estimate.
- Commands run (exit 0 unless noted): `date -u` (one first attempt got no classifier verdict and did not run);
  `git rev-parse`, `git log --oneline -8`, `git diff --stat 95f7a79 0daca9a`; `sed`, `grep`, `wc`, `ls` and Read on the
  sources above; `python3 -I -B` to parse B16's settings, the two mutation specs, RIB and the W1 manifest's roles (one
  parse attempt failed with an AttributeError on the spec's shape, exit 1, and read nothing else); one `grep
  --include=*.py` failed in zsh before running (exit 1); one `grep -o` hit a regex complexity limit (exit 1);
  `python3 -I -B sg_coherent_check.py 20` / `2000` / `2000 low-noise` / `2000 direction` and `sg_tail_check.py`
  (exit 0).
- Evidence in SIM/: `sg_coherent_check.py` (`bed06738f748d4df`), `sg_tail_check.py` (`bfc23c140fec988c`),
  `sg_coherent_check_2000.txt` (`1e29acd56bf482ec`), `sg_coherent_check_2000_lownoise.txt` (`0a49ec9771a9670f`),
  `sg_coherent_check_2000_direction.txt` (`f4376b0f8c302ffc`), `sg_tail_check_10000.txt` (`bfcd26b2761ca0c0`).
