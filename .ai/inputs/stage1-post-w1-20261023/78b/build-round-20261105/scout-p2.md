# Scout P2: the lead's decisions for Part 2 of the 7-8B pre-registration

Written 6 Nov 2026 by a read-only design scout for the main-study lead (General Implementation X). Clock read with
`date -u` at 18:34, 18:49 and 18:51 UTC. Skeleton first (18:49 UTC), then filled.

**What this is.** One decision per item of the task, each with options, a recommendation, its basis, its cost, what
it changes in the kit or the analysis, whether it needs the user, and its deadline. The lead rules; a writer drafts
Part 2's sections 0 and 2-12 from the rulings. Nothing here is a ruling.

**Labels.** **M** = measured (the command is named). **R** = read (path:line, or a FOCUS entry by title and time).
**E** = estimate (the basis follows). **I** = inference.

**Short names.** As Part 1 (P1 = `research/experiments/2026-11-05-78b-preregistration-part1.md`). RUL, ADD, PP = the
lead's three rulings files in `.ai/inputs/stage1-post-w1-20261023/78b/`. PLAN, CHECK = the readiness plan and its
check (`78b/readiness-20261105/`). P78, KCR, PR4, RP as P1. **P2D** = the Part 2 draft
`…/scratchpad/b78/ws-p/research/experiments/2026-11-06-78b-preregistration-part2.md`. **RK** = `runkit/stage1-78b/rules_78b.py`,
**SR78** = `runkit/stage1-78b/stage1_rules.py`, **RUN78** = `runkit/stage1-78b/setup/job_runner_stage1.py`, each as it
stands in the main checkout's working tree (RK's SHA-256 prefix there is `68bf8f45`, equal to P2D's R4B; M:
`shasum -a 256`). **RUN1B** = `runkit/stage1-olmo/setup/job_runner_stage1.py`. **OXU, OXE** =
`scripts/stage1_s1/settings/oext_unit.json`, `…/oext_eval.json`.

**Limits of this scout.** No pod, spend, network, install, download, agent, message or git change. Only this file was
written. No forbidden folder or file was opened (none of `tmp/hlc*`, `tmp/v3-prepared`, `tmp/stage1-olmo`,
`tmp/stage1-mac-runs-20261023`, `tmp/stage1b`, a `selector.jsonl`, a `hidden/` file, a judge output, an answer, a
generation, a sample or a prompt-text file). Stage-1 outcomes were used only as P1 §0 lists them. The two prepared
manifests were read for metadata only (seed namespaces, bank counts, tokenizer names). OXE's `cap.branch` value was
read (a settings pin, not a repair outcome); §1.2 says how Part 2 should treat it. The side paper is not mentioned.

---

## Summary: the eight findings that move money or the plan

1. **O-ext is not priced anywhere in the gate's lines** (I; CHECK M1 says it is "not costed separately"). RP's FRE
   counts assume the engine's dev-bank evaluation only (R: RP:71). At 7-8B the 400 PHTest prompts add about 38% to
   an arm's generation (E: 13 batches on top of 34; §1.3). Over both families this is about **$50-100 under Branch 128**
   and about **$200-355 under Branch full** (E, §1.3). It can flip the gate from B to C (§9).
2. **The cap branch is the largest single money choice in Part 2.** A 7-8B W1-18 check on the seven reused side units
   ($2-4, one pod) decides it by the frozen rule's own form. Recommended (§1.2).
3. **O in the same job as the arm** (the 1B route, RUN1B:36-38) saves about $100-285 over both families against a
   separate O job (the low end if the separate pods are packed 4 per pod), but raises the 4-arm pod cap from 10.5 to 15.0 h (OLMo) and from 12.5 to 17.0 h (Llama) under
   Branch full (M: RK's constants, §1.3). Under Branch 128 the rise is about 1-2 h (E).
4. **The 3-seed reference set is what the money bases price** (R: RP:71). LN-15b's 7-seed set (PR4:485) adds about
   $190-215 over both families (E). A 6-seed set at 1102-1107 loses nothing for any test (a0-1101 has no partner)
   and costs about $155-180 more than the 3-seed set (E, §2.1). Recommended as a money-contingent default outside the
   gate test, with the 3-seed set at 1102-1104 as the pre-set fallback.
5. **Part 1's "B by the gate, plan A about $640-900" already holds the dose arm** ($49-99; R: PLAN:394-398), while
   P1 §1 lists the dose arm again as its own row and ruling 9 puts it outside the gate test. Part 2's cost section
   should say the gate test's B figure without the dose arm is about $591-801 (I: subtraction).
6. **Idle storage is under-budgeted.** Every stopped 7-8B pod keeps a 50 GB volume until the user's yes by pod name
   (C13 item 3; kit README:115 "stop, never delete"). Both families need roughly 90-110 pods (E, §4.3). At 2-7 days
   per pod that is about $60-250, against PLAN's $15-30 (R: PLAN:397).
7. **Alpaca needs two user items that C13 does not list:** the learning-rate rule extended to datasets and the
   download approval (R: FOCUS "USER DECISION, 2026-10-09 09:40 UTC (GI IV chat): datasets", research/FOCUS.md:279-280;
   RP:150). Recommended: outside Part 2's frozen design, with its own pre-registration (§6).
8. **The kit has no block A or B yet** (R: SR78:199 `BLOCKS = ("0", "sc")`), no 39-step dose (R: RK:103 `STEPS`
   lacks it), no re-judge list for N and the side units (R: SR78:388 `REJUDGED_PINS = {"0": ()}`), and no O-ext step
   in `arm` (R: RUN78:46). Part 2 must give the kit block tables, the dose and reference kinds, the judge lists and
   SR-2's blinding test (§7).

---

## 1. Evaluation (CHECK M1; PP17)

### 1.1 Decision E1: the evaluation bank for U, O and L at 7-8B

**Facts.**
- The engine's dev bank is the same bank on both families and at 1B: 200 harm prompts (U, 3 samples each = 600), 100
  over-refusal prompts, 72 safety prompts and 96 ARC generation prompts greedy (468 in all), 189 ARC utility items
  (M: `banks.dev` of `tmp/kt-prepared/prepared-kt-dolly-olmo2/manifest.json` and `…-llama3/manifest.json`; the two
  `banks` blocks are equal). So "the family-probe bank" (KCR:70; CHECK M1) is stage 1's engine bank. **U and L need
  no new bank** (I).
- L is the engine's query loss on the 200 task rows; every engine evaluation writes it (R:
  `experiments/safety_selection/runner.py:669-675`; PR4:195). So L exists for every 7-8B unit already run, N included
  (I).
- O at 1B is the 500-prompt O-ext bank: the dev 100 plus 400 PHTest prompts from a sealed draw (R: PR4:526-539; OXE
  `bank.phtest.record_sha256` `a810574e…`; record `.ai/inputs/stage1-commitments-20261016/oext-bank/oext_record.json`).
  P1 §14 item 3 names "PR4 §3.6's O set of 500 prompts" (R: P1:364).
- OLMo-2-7B uses the same prepared set and tokenizer as OLMo-2-1B (M: the manifest's `tokenizer.repo_id`
  `allenai/OLMo-2-0425-1B-Instruct`; manifest `9ed61826…`). So the 1B encode checks of the PHTest draw hold for it (I).
  Llama-3.1-8B has its own tokenizer (M: `meta-llama/Llama-3.1-8B-Instruct`), so the 400 prompts are not encode-checked
  on its codec (I).

**Options.**
- (a) **Stage 1's O set as it is, for both families:** the family's dev 100 plus the same 400 sealed PHTest prompts
  (record `a810574e…`). One id set across families and sizes.
- (b) A new PHTest draw per family (needless for OLMo; breaks the 1B-to-7-8B match).
- (c) The dev 100 only (OXE's fallback `dev100_recipe_cap`). At 1B its O MDE against θ0 was 11.04 pp (R: PR4:527), so
  "within the O limit" would rarely be shown.

**Recommendation: (a).** For Llama, a $0 encode count of the 400 prompts on Llama's codec (counts only) before the
first Llama O pod. If any prompt fails, LN-24's shortfall rule applies to Llama (R: PR4:536): the bank is the dev 100
plus the eligible prompts, fixed and recorded before any Llama O answer exists.

**Basis.** P1:364; PR4 §6.2; the 1B O MDE; equal bank counts (M).

**Cost.** $0 (the draw exists). The encode count is a Mac run of a few minutes (E).

**What it changes.** OEXT_78B's inputs (§1.4). Nothing in U or L.

**Needs the user.** No.

**Deadline.** Before OEXT_78B is filled, so before the first 7-8B O-ext pod (§11).

### 1.2 Decision E2: the answer-cap branch for the 500 prompts at 7-8B

**Facts.**
- PR4 §6.3: one cap for the whole bank; Branch 128 if W1-18's truncation check passes on the recorded units, else
  Branch full; chosen before any 500-bank answer exists; never switched after (R: PR4:541-552).
- The 1B settings pin `cap.branch` "128" (R: OXE:31). W1-18's bar was read on 11 OLMo-2-1B units only (R: PR4:546,
  :916 item 22). Nothing about 7-8B answers follows from it (I). If Part 2 cites this value, its blinding line names
  it (it is a cap-rule measurement, not a repair outcome; I).
- 7-8B greedy answers often reach the 2,048-token cap: 11-15 of 15 greedy batches had a capped row (R: KCR:79).

**Options.**
- (a) **Branch full at 7-8B, no check.** The frozen fallback when W1-18 "cannot run".
- (b) **A 7-8B W1-18 on the seven reused side units** (OLMo θ0 and a0 1101-1103; Llama θ0 and a0 1101-1102), by
  W1-18's frozen bar (at least 97 of 100 flags agree full against cut; no refused count moves by more than 2), per
  family; Branch 128 for a family whose units all pass, else Branch full. It runs as the first O job of the scorer
  block, before any 7-8B 500-bank answer.
- (c) Carry 1B's Branch 128. Not valid: the bar was read on other units of another model (I).

**Recommendation: (b), with (a) as the pre-set fallback** (trigger: the 7-8B W1-18 job cannot run, or fails, or is
not built before the first O-ext pod). This is the ambitious default with its fallback (the user's 17 Oct rule).

**Basis.** PR4 §6.3's own rule form; the money in §1.3.

**Cost (E).** One pod, guard-only on about 1,400 judged items (7 units × 100 answers × full and cut): about 1 h with
setup, about $2-4 spend; an E cap of about 2-3 h, guard about $10-12 (E: RK's guard form $6 + $1.85 × cap). Build:
the stage-1 kit's `w1_18` kind restored in the 7-8B kit (SR78:378-380 now has `BANK500_KINDS = frozenset()`,
`BRANCHES = ()`), its settings re-derived with the seven units' COMPLETE.json pins, tests and a review: about 4-8
builder h (E). What it can save: about $0.8-1.4 per O-ext unit, about $150-255 over both families (E: the two in-job totals of §1.3).

**What it changes.** OXE's per-family copy (`cap.branch`, `cap.w1_18` pins); the order of the scorer block (the
W1-18 job first); the dev-100 route under Branch 128 for regenerated units (`--dev100-source`, R:
`scripts/stage1_s1/oext_unit.py:12-20`).

**Needs the user.** No.

**Deadline.** Rule by about 12 Nov so the build fits the 12-19 Nov window (R: CHECK window 2). The branch itself is
fixed before the first 7-8B 500-bank answer.

### 1.3 Decision E3: O-ext in the arm's own job, or in a separate job

**Facts.**
- At 1B the `arm`, `a0_arm` and `ref_train` jobs ran `calibrate`, then the O-ext pass on the new unit's e1 state, in
  one job (R: RUN1B:36-38). B10's references take the O-ext flags inside their own job (R: RUN1B:78).
- At 7-8B no O-ext step runs in any arm job (R: RUN78:46). The cap basis assumes the dev bank only, and `check_keys`
  refuses any other bank (R: `runkit/stage1-78b/RULES-78B.md:159-161`; KCR:147 "The basis holds only if the
  evaluation bank is unchanged").
- The pre-block-A pods `o_only` (θ0) and `o_only_with_regenerate` (each reused a0 unit) run the same O-ext pass first
  (R: P2D §1.14). Their ledgers will measure it at 7-8B before block A (I).

**Cap effect per arm (M: arithmetic with RK's functions and the basis constants, run with `python -I -B`).**
An in-job PHTest pass is 13 batches of 32. All batches at the 2,048 cap: 3,205 s (OLMo), 3,254 s (Llama); with half the
scoring allowance and the early and outside time, 3,959 s and 4,061 s (1.10 / 1.13 h); × 1.5 (RK:313's wide factor):
5,938 s and 6,092 s.

| 4 arms per pod | Cap now | Cap with the step (× 1) | Cap with the step (× 1.5) | Guard now / × 1 / × 1.5 | Four-pod launch need (× 1.25) now / × 1 / × 1.5 |
|---|---|---|---|---|---|
| OLMo-2-7B | 10.5 h | 15.0 h | 17.25 h | $25.43 / $33.75 / $37.91 | $104.62 / $146.25 / $167.06 |
| Llama-3.1-8B | 12.5 h | 17.0 h | 19.25 h | $29.13 / $37.45 / $41.61 | $123.12 / $164.75 / $185.56 |

Under Branch 128 the step is about 0.3-0.45 h (E: 13 batches at about 25 s each at a 128-token cap, about 20 s per
batch by the measured 92-122 ms per decode step, KCR:78, plus the guard), so the 4-arm cap rises by about 1.25-2 h
(E).

**Spend per O-ext unit (E).** Branch full, in-job: about 0.7-0.9 h of generation and judging (13 PHTest batches at
the measured 188-241 s per capped greedy batch, KCR:78, plus about 200 s of guard), so **about $1.2-1.6**. Branch 128,
in-job: **about $0.2-0.4** (E: same form at a 128-token cap; and PR4:549's 1B figures, $10-27 for 72 units at 128
and $40-70 at full, × 1.9-2.3 for 7-8B job time, RP:43, give $0.27-0.86 and $1.06-2.24 per unit). A separate job adds
a train-only regeneration (38 × 19-24 s plus state writes, about 0.3 h) and a pod overhead (about 0.5 h on a single-job
pod): **about +$1.4 per unit**, or about +$0.8 if packed 4 per pod after it is measured (E: RK `POD_OVERHEAD_S`, KCR:76).

**Units that need O per family (I, from P1 §5 and §10 and §2.1 here).** θ0 1; reused a0 3 (OLMo) or 2 (Llama); N's
units 3 (OLMo R_1-R_3) or 4 (Llama R_1-R_3, a0-1103); blocks A and B under plan A 44; dose arms 6 or 12; references
15-21 (3-seed set) or 40-42 (6-seed set). So about 72-107 per family.

| O-ext money, both families (E) | Branch 128 | Branch full |
|---|---|---|
| In-job for arms, dose arms and references; separate pods for θ0, reused and N's units (14 pods) | about $50-100 | about $200-355 |
| All separate, single-job pods | about $230-385 | about $375-640 |

**Options.**
- (a) **Same job, as at 1B:** restore RUN1B's O-ext step for `arm`, `a0_arm` and `ref_train`; add an O-ext term to the
  arm's requirement and cap. The term is E until the pre-block-A O pods measure the pass; then a recorded lead step
  makes it M (KD9's form).
- (b) **Separate job** for every unit: extend `o_only_with_regenerate` to block A and B units. The arm kind and its
  measured basis do not change.
- (c) Same job for block B only; block A separate (no gain; two code paths).

**Recommendation: (a)**, keeping 4 arms per pod (KD2). Pre-set fallback (b), trigger: the kit's O-ext arm path is not
verified before block A's first pod. N's units, the reused a0 units and θ0 stay on their own O pods (decision E5).

**Basis.** The 1B route; the money above; the O-ext pass is measured before block A by the O pods that must run
anyway, so the arm's cap term rests on a 7-8B measurement.

**What it changes.** RUN78's `arm_commands` (the O-ext step), RK's cap rule (an O-ext term, measured or E),
`check_keys` (the O-ext bank as a second pin beside `BANK`), the funding needs per launch (table above), the cost
section's per-arm figures. PR4's analysis does not change.

**Needs the user.** No (money only, C13 item 1).

**Deadline.** Rule by about 12 Nov (the build); in Part 2's §4 before block A's first pod.

### 1.4 Decision E4: what `OEXT_78B[F]` holds

RK's form is fixed: `{"files": {path under scripts/: SHA-256}, "inputs": {"oext_bank": SHA-256, "oext_record": SHA-256}}`
(R: P2D §1.14; RK `oext_form_problem`).

**Recommendation (I; the 1B engine-Y re-pin is the precedent).** At 1B, engine Y got a copy `scripts/stage1_s1/oext_unit_y.py`
whose literal pins name `settings/oext_unit_y.json` and `settings/oext_eval_y.json` (R: `scripts/stage1_s1/oext_unit_y.py:3-5`,
:86). Do the same per family, under `scripts/scale78b/` (new files only; the 1B files stay byte for byte):
- **files:** a 7-8B O-ext unit runner (a copy of `oext_unit.py` with changed literal pins, or a wrapper in
  `scorers_78b.py`'s pattern), `scripts/stage1_s1/oext_eval.py` (unchanged; `load_settings` takes an expected hash,
  R: `oext_eval.py:248`), the family's `oext_unit__F.json` and `oext_eval__F.json`; under Branch 128 also W1-18's
  module and the family's 7-8B W1-18 settings and record; for c0 also `lean_eval_job.py` and `lean_eval_job__F.json`
  (P2D §14 item 9).
- **`oext_unit__F.json` changes from OXU:** `prepared.manifest_sha256` = F's manifest (`9ed61826…` or `c52a50af…`);
  `recipes.allowed` = MAIN_F and F's recipe G (OXU:52-66 now allows only the 1B B, G, S); `generation_sha256` and
  `guard_sha256` = MAIN_F's blocks (UNVERIFIED whether they equal the 1B hashes).
- **`oext_eval__F.json` changes from OXE:** `cap.branch` and `cap.w1_18` by decision E2; `engine_x` unchanged.
- **inputs:** `oext_bank` = the 1B PHTest text file's SHA-256 (the same file for both families under E1 (a));
  `oext_record` = `a810574e…` (Llama: a shortfall record if the encode count fails).
- **B+Qi on Y** needs a Y variant per family (as `oext_unit_y.json` allows only B+Qi at 1B), or B+Qi's O-ext rides in
  its own `ref_train_bqi` job under E3 (a).

**Cost.** $0. Build about 4-6 builder h with tests (E).
**Needs the user.** No. **Deadline.** Before the first O-ext pod; its hashes enter Part 2 before any O-ext output is
read (P2D §14 item 1).

### 1.5 Decision E5: O and L for N's units and the reused units

**Facts.** N's 7 runs evaluate the dev bank only (R: RUN78:46). R_1102 and R_1103 are P1-P3 comparators under HB-C,
and Llama a0-1103 is a full-corpus cell for P4 (I from P1 §4-§5). At 1B, LN-12 regenerated R_1101-R_1103 and ran O
on the 500 bank (R: PR4:556). PP17 covers the reused a0 side units only (R: PP:94-100). A stopped kit pod is never
restarted (R: PR4:178).

**Options.**
- (a) **Extend `o_only_with_regenerate` to N's units:** R_1-R_3 regenerated with their sealed edits, Llama a0-1103
  plain; the acceptance check against N's own COMPLETE.json fingerprints; then the O-ext pass. One single-job pod per
  unit (KD6) until measured; then up to 4 per pod by a recorded lead step.
- (b) Run the O-ext pass on N's pulled e1 states (a new kind; the finisher pulls them, kit README:197-199). New code
  and a review; no gain in money worth it (I).
- (c) O for R_1102, R_1103 and Llama a0-1103 only (the cells that enter a paired estimate); R_1101 gets none.

**Recommendation: (a) for all seven, as LN-12 did at 1B.** R_1101 enters S-U and the reported means (P1:190).

**L.** No job: L is in N's own records (I, §1.1). It is read with the comparison, not before (decision K3).

**Cost (E).** 14 pre-block-A O pods over both families (θ0 2, reused a0 5, N's units 7): about $1.6-2.9 each
expected (overhead 0.5 h, regeneration 0.3 h, O-ext 0.1-0.9 h), about $22-41 in all; E caps 3.75-4.5 h, guards
$12.94-14.33 each (R: RULES-78B.md:116-117).

**What it changes.** RK `sc_seeds` and `SC_KIND_PINS`; RUN78's regeneration command takes an edit for R units; the
acceptance input is N's COMPLETE.json (pinned after block 0's record-done).

**Needs the user.** No. **Deadline.** Before block A's first pod (P2D §1.4 order).

---

## 2. References per family

### 2.1 Decision F1: which reference set and seeds, in plans A, B9 and H (b)

**Facts.**
- 1B's adopted set (LN-15b, the ambitious default): SP, adapter scaling and Safe LoRA on all seven a0 seeds, λ = 0.9
  added; recipe G and B+Qi at 1102-1107; pre-set fallback the approved 3-seed set, under which "beats" is descriptive
  and family 1b is not tested (R: PR4:479, :485).
- The 7-8B money bases price the 3-seed set: "recipe G 3; B+Qi 3-6; evaluation-only references (safety prompt 3,
  adapter scaling 6, Safe LoRA 3)" (R: RP:71). So LN-15b's form is not in the gate's figures (I).
- References are unchanged under plan B (R: PR4:456 "References under plan B: unchanged (LS-05)"). Method arms start at
  1102 in every plan (P1 §5). An evaluation-only reference cell at 1101 has no repair partner, so it enters no "beats"
  test (I from PR4:479's fit, a0's cells left out, pairs on common seeds).
- The 1B family-1b result (no repair beats every reference) is one of the seen 1B values (R: P1:33).

**Options.**
- (a) **The 3-seed set (RP's basis):** SP, λ ∈ {0.75, 0.5} and Safe LoRA on a0 1101-1103; recipe G 3 seeds (OLMo's
  in hand at 1101-1103; Llama 3 new); B+Qi 3-6. Family 1b descriptive.
- (b) **LN-15b at 7 seeds:** as 1B, a0 1101-1107, λ ∈ {0.9, 0.75, 0.5}; G and B+Qi at 1102-1107.
- (c) **LN-15b at the paired seeds 1102-1107 for every reference**, λ ∈ {0.9, 0.75, 0.5}. Same tests as (b).
- (d) As (c) but at block A's seeds 1102-1104 only (3 pairs; family 1b by the 3-seed fallback).

**Recommendation: (c) as the ambitious default, money-contingent, outside the gate test; pre-set fallback (d).**
Written now from money only. Trigger: the money after the gate does not cover B's or C's primary needs (with O-ext and
the 3-seed set) plus (c)'s increment. Order after the gate (a lead ruling to record, because ruling 12's dose test
speaks of "primary needs"): the dose arm at 3 seeds, then (c)'s increment, then the dose arm's 6 seeds. Basis for that
order: (c) keeps family 1b testable and gives the dose arm's dominance question its references at the dose seeds
1102-1104 (I); the dose arm's 6 seeds add only power to a secondary arm (P1:320).

Why (d) and not (a) as the fallback: at 1101-1103 the eval-only references share only 1102-1103 with the method arms;
at 1102-1104 they share three seeds (I). This is a 7-8B choice, labelled "chosen after the stage-1 reading; it reads
the seed layout only" (ruling 16's form).

**Cost per family (E; FRE at RP:71's 0.85 per evaluation-only point; planning rates $3.53 and $4.71 per arm,
KCR:188).**

| Set | Eval-only points | Training runs (new) | FRE | Planning money OLMo / Llama |
|---|---|---|---|---|
| (a) 3-seed | 12 | G 0 / 3, B+Qi 3-6 | 13-19 | about $47-57 / $76-90 |
| (c) 6-seed, 1102-1107 | 30 (SP 6, λ 18, Safe LoRA 6) | G 4 / 6 (OLMo 1102-1103 reused, LS-23), B+Qi 6 | 35.5 / 37.5 | about $125 / $177 |
| (b) 7-seed | 35 | as (c) | 39.8 / 41.8 | about $140 / $197 |

Increment of (c) over (a): about $155-180 both families, plus its O-ext (about +$10-15 at Branch 128, +$45-60 at full;
E, §1.3). Increment of (b) over (a): about $190-215 (E).

**What it changes.** Block B's reference jobs (§7); the reading's reference fit and family 1b (PR4 §5.3), unchanged in
form.

**Needs the user.** No (money, C13 item 1).

**Deadline.** The money rule before the gate (it is read there; about 20 Nov). The rest in Part 2 before block A's
first pod.

### 2.2 Decision F2: each reference's settings at 7-8B

| Reference | Recommendation (I unless marked) | Engine | Open point for the lead |
|---|---|---|---|
| Safety prompt (SP) | 1B's text verbatim as a user-turn prefix on both families. OLMo-2 has no system turn (R: PR4:441); Llama-3.1-8B has one, but one rule across families and sizes keeps SP comparable. A Llama system-turn form is not run; Part 2 states it as a limit. | X | none |
| Adapter scaling | λ grid {1, 0.9, 0.75, 0.5, 0} under (c); {1, 0.75, 0.5, 0} under (d). The a0 e1 adapter by a train-only regeneration, accepted by its fingerprint (PR4:178), on both families; OLMo's Mac adapters (P1:91) as the LS-04 fallback only. One path for both families. | X | none |
| Safe LoRA | K by the 1B share: 39 of 112 matrices = 34.8% (R: PR4:488); at 7-8B both families adapt 7 modules × 32 blocks = 224 matrices (I: the configs' `expected_trainable_parameters` 159,907,840 and 167,772,160 equal 32 × the rank-64 sums), so **K = 78**. Label: "chosen after the stage-1 reading; reads the 1B rule's form only". Base models `allenai/OLMo-2-1124-7B` and `meta-llama/Llama-3.1-8B`, pins read from Hub metadata by a lead step (the kit's base-model revision is null, R: RULES-78B.md:197-198). | X | Llama's base repo is gated: the HF token at that launch (C13 item 2) and **UNVERIFIED whether the user's account has access to the base repo**. A $0 check at the next Llama launch's precheck (the kit's Range 206 test) settles it. If not, Llama's Safe LoRA does not run; stated. Disk: policy + guard + base may be about 38-53 GB on a 60 GB container disk (E; base dtype UNVERIFIED). |
| Recipe G | OLMo: the main-LR G config `01259f28…` (R: RULES-78B.md:90-92), units 1101-1103 in hand, reused at 1102-1103 (LS-23). Llama: a **new G config at LR 5e-5** (G = token-mean loss and a 4-step warmup cosine schedule, M: the field diff of `study-kt-olmo2-7b-r64-g-mb2-20261011.json` against the main config; Llama's G config `442f133f…` is at 1e-4, P1:92). `RECIPE_G` filled by a recorded step (ADD A13). | X | The new Llama G config is a committed addition (KD8). Note RK's `RECIPE_ALLOW` now holds Llama's 1e-4 G hash (R: RULES-78B.md:90-92); the lead swaps it for the 5e-5 config. |
| B+Qi | 1B's form (R: PR4:496-503): recipe B plus Qi's token-wise constrained loss, no warmup, seeds as F1. Config per family from engine Y's tree; `RECIPE_BQI` by a recorded step. Unpaired and labelled if ruling 10's Y retrain differs (P1:169). The binding check's two numbers (LS-10) carried and logged in every B+Qi run; B+Qi is never dropped or changed on it, so no user step arises (I). | Y | Whether a separate B+Qi certificate pod is needed at 7-8B (1B's `cert_c2`, RUN1B:57) is not ruled; recommended: none, the numbers are logged in the runs (I). |

**Cost.** Inside F1. **Needs the user.** Only via C13 item 2 (Llama launches) and the Llama base-repo access above.
**Deadline.** Part 2 before block A's first pod; every setting before any reference outcome.

---

## 3. Judges

### 3.1 Decision J1: what is judged, by which judge

**Facts.** HarmBench (`cais/HarmBench-Mistral-7b-val-cls` @ `51182c7c…`) by Gate B's pipeline byte for byte, one device
per contrast (R: PR4:192, HB-1). Granite greedy is a reported measure of every arm at 1B (R: PR4:193). The 7-8B kit keeps
both judges and the stage-1 judge route (R: SR78:397-419; `runkit/stage1-78b/judge_units_stage1.py`). TC does not run,
so no Granite judging serves TC (ADD A9).

**Options.**
- (a) **HarmBench and Granite on every judged unit, as at 1B** (Granite report only).
- (b) HarmBench only.
- (c) HarmBench on every unit; Granite on block A only.

**Recommendation: (a).** Pre-set fallback: HarmBench only for a block whose Granite launch fails its known-answer gate.

**Also rule.** ADD A9 calls N's R-arm judging "report-only". That holds for N's gate. In the comparison, R_1102 and
R_1103 are P1-P3 comparator cells, so their HarmBench files enter the claim rule like every cell (I from P1 §3.1:
"N's 7 runs are inside the comparison's counts"). Part 2 should say so in one line.

**The claim rule (carried, R: PR4:205-210).** A "harm" sentence needs the HarmBench contrast to have the U contrast's
sign and at least half its size; none if the family's E_HB < 20 pp; E_HB,F = HB(a0) − HB(θ0) over the family's a0
seeds, read with the comparison. The 1101-1102 values already seen are all above 27 pp (R: P1:36).

**Cost (E; the kit's judge constants R: SR78:398-405: HarmBench 0.25 s per answer, 800 per arm; Granite 0.5 s per
answer, 200 per arm plus 200 known answers; setup 1,800 s; margin 900 s; $1.79/h).** Block A launch per family about
28 units: HarmBench about 2.3 h (about $4), Granite about 1.6 h (about $3). Block B per family about 60-80 units
(arms, dose arms, references): HarmBench about 4.5-5.5 h, Granite about 2.5-3 h (Granite's cap is 6 h at most, R:
SR78:401, so one launch each may suffice): about $13-16. Both families: **about $40-50**. Inside PLAN's $25-50 line
(R: PLAN:396) at its top. Answers are longer at 7-8B; the 512-token HarmBench clip bounds that judge (R: PR4:192);
Granite's time per answer at 7-8B is unmeasured (E).

**Needs the user.** No. **Deadline.** Part 2 before block A's first pod.

### 3.2 Decision J2: re-judging the reused units (one device per contrast)

**Facts.** The route refuses a contrast whose units were judged on more than one device type; "a reused Gate A or
wave-0a unit judged on another device type must be judged again on the stage-1 judge pods" (R:
`runkit/stage1-78b/judge_units_stage1.py:67-70`). E_HB was reported for side units 1101-1102 only (R: P1:36); no
judge file for OLMo a0-1103 is named anywhere I read (I). P78 [LEAD] item 3 asks for judge files for every reused a0
unit (R: P78:402).

**Recommendation.** Block A's judge launch per family judges, besides block A's units: N's units (A9), the reused a0
units and θ0 (for E_HB and every a0-based contrast). About 9 extra units for OLMo and 9 for Llama (I).

**Cost.** About $2-3 more per family (E: 9 × (200 s + 100 s) of judge time). **What it changes.** The kit's
`REJUDGED_PINS` for block A (now `{"0": ()}`, R: SR78:388) and the `units-of-block` list plus explicit `--unit`
folders from the block-0 and side-unit trees. **Needs the user.** No. **Deadline.** Before block A's judge launch;
the rule in Part 2 before block A's first pod.

---

## 4. Limits (P78:379; CHECK M1) and cost conventions

### 4.1 Decision K1: the O limit at 7-8B

**Options.** (a) **PR4 §6 as written:** O against the family's θ0 on the 500 bank under the family's branch; the τ_O
grid {2, 5, 10} pp above θ0; τ_O* = 5 pp for F_k and O_k; m_O = 5 pp in "beats"; feasibility by the upper end of the
two-sided 90% interval (R: PR4:522, :561-562, :464). (b) A relative τ_O (a share of θ0's O). Not proposed anywhere;
it would change a frozen constant.

**Recommendation: (a).** Part 2 copies the planning-power table's form (R: PR4:564-574) and prints F_k's planning
power at the measured discordance after block B (report only), as 1B did.

**Cost.** $0. **Needs the user.** No. **Deadline.** Part 2 before block A's first pod.

### 4.2 Decision K2: τ_L at 7-8B

**Facts.** τ_L = 2√2 × s, s the sample SD (ddof 1) over the a0 seeds 1101-1103 of each unit's mean query loss on the
200 task rows at e1, fixed before use and never re-estimated (R: PR4:589-595; S1B REQ-19 at
`.ai/briefs/stage1-commitments-build-20261016.md:115`).

**Options.** (a) **REQ-19's form per family**: OLMo from side a0 1101-1103; Llama from side a0 1101-1102 and N's a0-1103.
(b) The 1B value 0.0067171 nats (another model's loss scale; I: not valid). (c) A relative τ_L (0.43% of the a0 mean
loss, PR4:604). Not the frozen form.

**Recommendation: (a)**, computed by the lead on the Mac (losses only), OLMo now and Llama after N's record-done, and
written into Part 2 before its freeze. The values enter Part 2's blinding line (they are a0 nuisance values, like
Gate A's at 1B). The 2-df caveat is carried (R: PR4:599). A $0 REQ-19-style O planning line (dev-100 O SE against θ0
from the same records, labels only) may be printed beside it.

**Cost.** $0. **What it changes.** The reading's settings per family. **Needs the user.** No.
**Deadline.** OLMo before Part 2's freeze; Llama after N, before Part 2's freeze, so before block A's first pod.

### 4.3 Decision K3: the cost conventions at 7-8B

**Recommendation (each line is R from the named source unless marked).**
1. **Accounting:** GPU-seconds by stage; C-full and C-lean; c0 measured on one real lean job (PP18's c0); every scorer
   charged in full; "≈ 0" only below 0.01 FRE; LS-13's charging rules (R: PR4:793-797, :812-817). No 1B cost ratio is
   claimed for 7-8B (R: PR4:796).
2. **FRE at 7-8B, per family:** the median job slot of N's three R arms, read from cost records only after block 0,
   fixed before block A, never re-estimated (I: PR4:810's 1B form, which used Gate B's wave-0a R arms). Alternative:
   the 17 side units' measured a0 job times now (KCR:74). The R-arm form is recommended (same arm kind as 1B).
3. **Rates:** spend $1.79/h; guard planning $1.85/h; creation limit $10/h; $6 reserve (R: README:109 of the kit).
4. **Two factors, named apart (I; A17):** × 1.2 "planning allowance" on spend estimates (RP:41; KCR:181); × 1.25
   "contingency" on the kit's funding needs (R: RK:78). Never mixed in one figure (A17).
5. **Three money figures, named apart (I):** Part 1 §5's per-plan upper bounds (RP's rates; A17); spend estimates on
   KCR's measured per-arm costs (P1 §1, CHECK C3); the kit's `init-block` funding needs (guard terms × 1.25). The gate
   reads the third for launches and the second for "covers" (I: ruling 9 reads "the account covers B's primary
   comparison"; the lead may rule the reverse).
6. **The dose arm in the gate's figure:** PLAN's "B by the gate, plan A or B9 about $640-900" sums arms, the dose arm,
   judges and idle storage (R: PLAN:394-398). The gate test excludes the dose arm (ruling 9). So Part 2 prints the
   gate-test figure without it: about $591-801 for plan A (I).
7. **Idle storage:** about $0.33 per stopped 50 GB pod per day (E, KCR:161), counted in no guard, printed per block
   (PP14). **Every** stopped 7-8B pod accrues it until the user's yes by pod name (C13 item 3), not only the pods that
   keep states. Pods for both families: block 0 about 4; scorer block about 26-30; block A about 12; block B arms and
   dose arms about 16-18; references about 36-40; judges about 4-6 (E: P1 §5 counts at 4 per pod, RULES-78B.md KD6
   single-job kinds) — about 90-110. At 2 / 7 days per pod after its verified backup: about $60-75 / $210-250 (E).
   **Options:** (a) ask the user for one batched yes by pod names after each block's verified backup, target 2 days;
   (b) a smaller volume (20 GB, about $0.13 per day) for single-job kinds that keep no states (a kit change to KD5);
   (c) both. **Recommendation: (c).** Budget line about $40-80 (E).
8. **Price check:** the A100 rate is re-read at the gate (R: PLAN:372 "$1.79/h on every pod since 9 Oct").

**Needs the user.** The yes by pod name (C13 item 3), as a batched request. **Deadline.** Lines 5-7 before the gate
(about 20 Nov); the rest in Part 2 before block A's first pod.

---

## 5. The confirmation at 7-8B (P1 §13 item 5; PR4:428)

### 5.1 Decision C1: the choice rule and the design

**Fixed already (R: P1:349, :370; PR4:427-428).** Per family, at most 2 contrasts: the two primary contrasts with the
largest |t| of the primary U test, among those whose U part reads *better* or *worse (U)*; ties to the lower P index;
none if none. Engine Y; fresh seeds 9101-9999; the sealed 200-prompt hidden subsample; "confirmed" = the 95% interval
excludes 0 in the same direction and the label agrees, by the primary model on the fresh seeds, read on the hidden
subsample only; the dev-bank reading is printed and never decides. Only U is confirmed. Both manifests' reference
namespace is [9101, 9999] (M: `seed_namespaces` of both manifests).

**Open points and recommendations (I).**
- **Candidates under plans B9 and H (b):** P1, P3, P6 only (the primary family); under plan A, P1-P6.
- **Arms and seeds:** each picked contrast's repair and comparator at 6 fresh seeds, 9101-9106, on both families (seeds
  are per model). A shared comparator runs once. So 12-24 runs per family (P1 + P6: R, A1, S1, S4 = 24; P1 + P3: R,
  A1, H1 = 18). This matches RP's 18-24 FRE per family (R: RP:76).
- **Model on fresh seeds:** the paired mean on the common fresh seeds plus the prompt part over the 200 hidden
  prompts, df by the stage's form (the S-p form, PR4:274), because two arms per contrast do not fit HB-C's clusters (I).
- **Code:** reuse `scripts/stage1_s1/reading_extra/stage3_pick.py` through a per-family wrapper (I; not read here).
- **Kit:** a `confirm` kind on Y with the subsample bank (1B's `cert_c3` form, RUN1B:58-59), its own bank pin and an
  E cap until measured; Y's evaluation is measured by B+Qi's block-B runs first (I).
- **Checks ($0, before the first confirmation pod):** the hidden subsample's 200 ids exist in Llama's prepared hidden
  bank with equal prompt hashes (counts and hashes only, by the lead; not opened here).

**Cost (E; RP:136).** About $140-230 for [B] (both families, 2 contrasts each); $70-120 for [C]; one contrast per
family cuts about $70-110 (R: RP:138 item 4). Plus judges (about $3-5).

**Money timing.** "In sight" at the gate; in the account by about 1 Dec, else B without the 7-8B confirmation (ruling
9).

**Needs the user.** Money only. **Deadline.** Part 2 before block A's first pod; the kit kind before the first
confirmation pod (about 11 Dec, R: PLAN:334).

---

## 6. Alpaca's home (the second dataset)

### 6.1 Decision A1

**Facts.** RP decision 7: [B] Llama-3.1-8B reduced; [C] OLMo-1B (R: RP:150). The user's 9 Oct decision: Alpaca is the
planned second benign dataset; before any Alpaca run the user extends the LR rule from families to datasets, a design
note fixes units (Alpaca has no categories), field mapping, version (tatsu-lab/alpaca, CC BY-NC 4.0) and the download,
"which the lead asks the user to approve with its name, source and size" (R: research/FOCUS.md:279-280). No Alpaca
prepared set exists (M: `ls tmp/kt-prepared/` shows Dolly sets only). RP planned the Alpaca probe and Gate A for 16 Nov
(R: RP:103); nothing is built. Moving Alpaca from Llama-8B to OLMo-1B saves about $35-65 (R: RP:138 item 5). Part 1's
gate lines hold no Alpaca line (R: P1:58-70).

**Options.**
- (a) **This tier, [B] Llama-3.1-8B reduced:** Gate A on Alpaca (θ0 + a0 × 3), then a reduced comparison (for example R,
  S4 and A1 at 3 seeds; S4's list is reusable because θ0 is the same model; I). About 16-20 runs plus an A1 pass and
  judges: about $80-140 (E: $4.71 per arm planning, KCR:188; the A1 pass guard $36.53, RULES-78B.md:120). Needs the
  user's two items, a design note, a prepared set, sealed edits, a kit family key per dataset, and its own
  pre-registration. Calendar: Gate A by about 10 Dec to read anything by 4 Jan (I).
- (b) **OLMo-1B** (RP's [C] home), on its own money (the 7-8B earmark, ruling 9), with the stage-1 kit. About $45-75
  (E: (a) minus RP:138's $35-65). Same user items.
- (c) **A later tier**, after the 4 Jan freeze, with its own pre-registration.
- (d) **Not at all;** the paper states Dolly as the only benign dataset at 7-8B as a limit.

**Recommendation.** Keep Alpaca **out of Part 2's frozen design**. Part 2 §11 holds only the home rule: (a) if the
user gives both Alpaca items by about 20 Nov and the money after the gate covers every line above Alpaca in RP:138's
cut order (Alpaca is cut fifth, before the second family) by about 1 Dec; else (b) on its own money; else (d), stated.
Any Alpaca run gets its own pre-registration file, frozen before its first pod. Basis: no Alpaca outcome exists, so a
later text loses no blinding (I); the builder calendar (block B to about 10 Dec, the confirmation to about 20 Dec) is
full (R: PLAN:333-334).

**What it changes.** Nothing in the kit or the analysis now.

**Needs the user.** **Yes, for any Alpaca run:** the LR-rule extension and the download approval (not on C13's list).
**Deadline.** The home rule in Part 2 before block A's first pod; the user's items by about 20 Nov for (a).

---

## 7. Blocks A and B in the kit (plan T7)

### 7.1 Decision B1: what the kit needs from Part 2

The kit now knows blocks "0" and "sc" only (R: SR78:199); method seeds for block A are named (R: SR78:192); the seed
rule's plan names exist (R: SR78:494-498). Part 2 must give the kit (I unless marked):

1. **Block tables per plan and family:** arm, seed, edit file by SHA-256, steps, recipe. Block A is the same in every
   plan: the six method arms at 1102-1104, R_4 at 1104, R_5 at 1105, a0 at 1104; 21 runs per family (R: P1:244).
   Block B: plan A 23, B9 32, H (b) 47 (R: P1:197-199). R edits: OLMo R_d1-R_d5 from SEAL, R_d6-R_d10 from stage 1,
   R_d11-R_d13 from the OLMo folder; Llama from its sealed set (R: P1:123). The dose edits by hash after the untuned
   pass (P2D §1.11).
2. **Pod layout:** at most 4 counted arms per pod (KD2), arms interleaved across pods within a block (R: PR4:157),
   `pod_sizes` (R: RULES-78B.md:69-70). 33-, 38- and 39-step arms may share a pod; the cap uses each arm's own steps.
3. **The S4 add-dose arms:** S4_96 and S4_192 at 39 steps under the main config, at 1102-1104 or 1102-1107 by the
   gate's money rule (ruling 12). RK's `STEPS` has no 39-step dose (R: RK:103); add it, or derive steps as ⌈rows /
   128⌉ from the edit file (I).
4. **`train_scale`** per arm from the edit's padded tokens per step (R: RULES-78B.md:41-42; KCR:104). Part 2's
   token-accounting line gives the counts (decision K5).
5. **The O-ext step in `arm`, `a0_arm`, `ref_train`** and its cap term (decision E3).
6. **References as kinds:** `ref_eval` with points prefix and scale 0.9 / 0.75 / 0.5 (R: SR78:384); `safe_lora`
   default point at K = 78 (decision F2); `ref_train` G under `RECIPE_G`; `ref_train_bqi` under `RECIPE_BQI` on Y
   (R: RULES-78B.md:125-127). Sequencing inside block B: each seed's a0 unit exists before its references (the
   regeneration's fingerprint check needs it).
7. **Judge lists:** `units-of-block` for A and B; block A adds N's units, the reused a0 units and θ0 (decision J2).
8. **SR-2's blinding test (ruling 3):** `record-done` for block A prints no U, HarmBench, O, L or coherence value;
   `scripts/scale78b/blinded_sigma.py` prints σ̂_A and its df only; a test holds that output byte for byte. It must be
   verified before block A's first pod, else SR-2 is not adopted and N decides alone (P1:248).
9. **`blinded_sigma.py`'s spec:** σ̂_A = √2 × the residual SD of the arm + seed model per cluster (full-corpus {a0, S1,
   S3, S4}; removal {R, A1, L1, H1}), over block A's cells and the reused cells at 1101-1104, pooled over clusters and
   the families that ran ([B]); the chosen family alone under [C] (ruling 3). A cell with no partner seed in its
   cluster adds no df. Inputs keyed by `complete_sha256` and family (P1:142). Df about 12-15 per family (I; P78:200
   says about 15).
10. **Block A's seal (decision K4):** the kit seals block A's outcome files by SHA-256 until block B completes.
11. **State rule:** pull e1 states, verified backup, the user's yes by pod name (KD5); the a0 e1 states at 1104-1107
    are kept until the references at those seeds have regenerated or used them (I).

**Cost.** $0 to specify; the kit build is about 20-30 builder h (E: PLAN T4's 20-40 h for the whole kit; block 0 and
the scorer block are built). **Needs the user.** No. **Deadline.** Items 1-11 verified before block A's first pod;
item 8 is SR-2's hard trigger.

---

## 8. Other items Part 2 must hold (P1 §14; P78)

### 8.1 Decision K4: block A's seal at 7-8B

**Options.** (a) **LW-35's form (R: PR4:158):** after block A only its cost ledgers, completion records and adapter
fingerprints are read; its U, HarmBench, O, L and coherence outputs are sealed until block B completes, except
σ̂_A by `blinded_sigma.py`. The same seal covers N's L, HarmBench and O files and the O pods' outputs (θ0, reused
units). (b) No seal beyond SR-2's printout.

**Recommendation: (a).** Basis: SR-2's condition; the gate and the block-B money decisions read no outcome; θ0's 500
outputs fell under block A's seal at 1B (R: PR4:155). **Cost** $0. **Deadline** Part 2 before block A's first pod.

### 8.2 Decision K5: the S4 add-dose arm's reading (P1 §14 item 5; P2D §14 item 21)

**Recommendation (I).**
- O state: O(dose) − O(θ0) against τ_O* = 5 pp by PR4 §6.4's bound, with LN-20 item 1's seed part (R: PR4:289). L
  state: L(dose) − L(a0) against τ_L, the pair's paired variance on the common seeds (LN-20 item 2).
- AD1 and AD2's O and L parts: O(dose) − O(S4) and L(dose) − L(S4), one-sided adverse, reported with one-sided bounds
  (secondary; P1:316).
- "The top feasible dose" = the largest of S4_192, S4_96, S4 whose O and L states are not *infeasible*; its states are
  printed. Then "does it beat every reference?" by LN-15b's "m beats r" (U, O, L bounds; R: PR4:462-466), one IUT at
  5%, secondary, outside family 1b.
- Fallback fired: with 96-191 kept rows, S4_top replaces S4_192 in AD1 (labelled with its n); with 48-95 kept rows,
  S4_top replaces S4_192, S4_96 does not exist and AD2 is "not formed".
- Token accounting: steps and padded-token totals beside AD1 and AD2 (P1:317); every arm's token line by
  `scripts/stage1/token_accounting.py` (PR4:740).

**Cost** $0. **Deadline** Part 2 before block A's first pod (before any dose outcome).

### 8.3 Decision K6: SR-2's error-rate simulation (P1 §14 item 10; P78:204)

**Options.** (a) **A $0 Monte Carlo** of the two-stage rule (N's 4-df σ̂_pool → block A's σ̂_A on about 12-15 df per
family → block B's plan → the HB-C analysis with Holm at 5%), with and without an arm × seed interaction, at true
σ_pair 3-8.24 pp; it prints each contrast's size and the familywise rate under the null, and power at 8 / 10 / 12 pp.
(b) Cite a source on blinded variance-only re-estimation (not checked here). (c) Skip.

**Recommendation: (a)**, with a pre-set reading written before it runs: if the simulated familywise rate exceeds
6% at any simulated σ, SR-2 is not adopted and N decides alone; else SR-2 stands and the size is printed. This adds a
trigger beside ruling 3's blinding trigger, so it is a lead ruling. **Cost** $0; about 2-4 builder h (E). **Deadline**
before block A's first pod.

### 8.4 Decision K7: the 7-8B reading code and the coherence screen's code

**Facts.** B16 (`scripts/stage1_s1/reading/`) implements HB-C, Φ, labels, feasibility, references, the coherence flags
and the overlap control for 1B designs only (`plan_a`, `plan_a_block_a_only`, `plan_b`; R:
`scripts/stage1_s1/reading/README.md`). It has no 12-seed H (b) design, no dose-arm fit, no per-family τ_L or S-U at the
plan's R seeds (I). The G1 check for N is `scripts/scale78b/g1_check_78b.py` (`251ddb32…`, R: P2D table A).

**Options.** (a) **A wrapper over B16** with per-family settings and a 1B parity test (the scorer layer's pattern),
committed by hash in Part 2 if ready, else by a dated amendment before block B's outcomes are opened. (b) A copy under
`scripts/scale78b/reading/`. (c) Write the code after block B (rules frozen in text only).

**Recommendation: (a)**; `blinded_sigma.py` before block A's first pod; the reader's hash before block B's outcomes
are opened. Part 2 §7 names the coherence screen's code (B16's `labels.py` through the wrapper, and `g1_check_78b.py`
for N's R arms). **Cost** $0; about 10-20 builder h (E). **Deadline** as stated.

### 8.5 Decision K8: stop rules and report-only analyses carried to 7-8B

**Recommendation (I).** Carry PR4 §11 by reference with three edits: (1) engine stops follow ruling 10's branches
(a Y-only mismatch keeps paired arms on X; B+Qi unpaired); (2) the anchor job's two stops have no fallback yet (P2D
§14 item 7) and Part 2 should name one (for example: Llama's A1 does not run, P1 not tested on Llama, stated); (3)
B+Qi is never dropped or changed on its binding check (no user step). Report-only analyses carried: token accounting;
the overlap control (B14; needs a `similarity` kind at 7-8B, about $2-5 per family, E; else "not run", stated; carrying
it is outcome-neutral, dropping it after 1B's "S1 and S3 not shown" could read as a choice after a result); the actor
menus (LN-08); prompt flips and the opening switch. Not run at 7-8B, stated: the token-axis dose and R_tok (no 7-8B
dose curve), SRJ, the prefill probe, in-domain refusal, HB-4, the human label check (the earmark, ruling 9), the
selector (EM-4).

**Deadline** Part 2 before block A's first pod.

### 8.6 Decision K9: Part 2's blinding line (P1 §14 item 13)

It lists, in P1 §0's form: N's values (r_F,j, σ̂_F, σ̂_pool, mean r_F, Llama a0-1103's E); the 7-8B W1-18 result
(decision E2); the a0 task losses behind τ_L (decision K2); any a0 dev-100 O counts read for planning; the Llama
encode count (decision E1); OXE's 1B `cap.branch` value if cited; the S1 check and PP1-PP18 items P2D §0 already lists.
**Deadline** after N's reading, before the freeze.

### 8.7 Cross-links to the scorer section's open items (P2D §14)

Items 1 (O-ext route) and 9 (c0) close with decisions E2-E4. Item 15 ([C] and the scorer pods): the scorer pods run
after the gate, for the families the gate keeps (I: CHECK's calendar puts them after N's reading). Item 21 closes
with decision K5.

---

## 9. Money roll-up for the gate (E; [B], plan A; both families)

| Line | Amount (E) | Source |
|---|---|---|
| B by the gate, plan A (arms with the 3-seed references and scorers, the dose arm, judges, idle storage) | $640-900 | R: P1:62; PLAN:394-398 |
| The same without the dose arm (the gate test, ruling 9) | about $591-801 | I |
| O-ext, Branch 128 / Branch full (decision E3 (a)) | +$50-100 / +$200-355 | §1.3 |
| The 7-8B W1-18 pod | +$2-4 | §1.2 |
| Idle storage above PLAN's $15-30 at a 2-day yes cadence | +$25-50 | §4.3 |
| Confirmation by about 1 Dec | +$140-230 | R: RP:136 |
| **Gate test plus confirmation, Branch 128** | **about $810-1,185** | sum |
| **Gate test plus confirmation, Branch full** | **about $960-1,440** | sum |
| After the gate: the dose arm 3 / 6 seeds | $49 / $99 | R: P1:68 |
| After the gate: reference set (c) increment, with its O-ext | +$165-195 (128) / +$200-240 (full) | §2.1 |
| H (b) on both families | +$190-240 | R: P1:64 |

Against the expected $900-1,300 (R: P1:72): under Branch 128, B with its confirmation fits; the dose arm fits; set
(c) fits at the low end. Under Branch full, B with its confirmation fits only in the lower half, and set (c) mostly
does not (I). So decision E2 is the main lever on the gate.

---

## 10. What needs the user

- **C13 item 1, the money:** every paid line above.
- **C13 item 2, the HF token at each Llama launch:** N's Llama pod, every Llama scorer and O pod, every Llama block-A,
  block-B, reference and confirmation pod, and the Llama Safe LoRA pod's base download.
- **C13 item 3, a yes by pod name before any delete:** recommended as one batched request per block (§4.3).
- **C13 item 4, H (a) or (c):** unchanged; only if the user wants either, recorded before N's reading is opened (ADD A15).
- **Not on C13's list:** Alpaca's LR-rule extension and download approval (§6); possibly the user's access to the
  gated `meta-llama/Llama-3.1-8B` base repo for Safe LoRA (UNVERIFIED; §2.2); the review ceiling's next step if it ever
  fires (P1:218).

---

## 11. Deadlines in one table (dates are expectations; the money is expected about 20 Nov)

| By | Decisions |
|---|---|
| About 12 Nov (start of the 12-19 Nov build window; Fable resets 12 Nov 09:00 UTC, PP13) | E1-E4 ruled (the builds: OEXT_78B, the 7-8B W1-18, the O-ext arm path); K6's pre-set reading |
| Before block 0's first launch (about 20 Nov) | the money-only rules the gate reads: F1's set rule and its order after the gate; K3 lines 5-7; A1's home rule |
| Before the first 7-8B O-ext pod (after N) | the branch (E2); OEXT_78B filled and its hashes in Part 2 |
| After N's record-done, before the freeze | Llama τ_L (K2); FRE (K3 line 2); the blinding line (K9) |
| Before block A's first pod (Part 2 frozen; A10) | every other section; the kit's items 1-11 (B1); SR-2's blinding test; `blinded_sigma.py`; the simulation (K6) |
| Before block B's outcomes are opened | the reader's hash (K7) |
| By about 1 Dec | the confirmation money in the account (ruling 9) |

---

## 12. Process

- **Commands (exit 0 unless noted):** `date -u` (5 times; the last at 18:57 UTC); `ls`, `wc -l`, `grep`, `sed -n`, `awk`, `cut` over the files
  named; `shasum -a 256` of RK in four checkouts; `git log --oneline`, `git status --short`, `git branch --show-current`
  in the main checkout (read only); `python3 -I -c` reads of OXE's keys, OXU_Y's recipe block, both manifests'
  `seed_namespaces`, `banks` and `tokenizer` blocks, and a field diff of the 7-8B recipe-G configs; RK's
  `rules_78b.py e-caps` and one `python -I -B` arithmetic run with RK's own functions (no file written). One `ls … ||`
  check of the report path exited 1 (the file did not yet exist), as intended. One `grep --include` under zsh failed
  ("no matches found") and was redone without the flag. This file was corrected in place twice (a `python3 -I` string replace and a `sed -i ''`), after re-checking
  the cited line numbers and the money sums.
- **Read in full:** P1 and its erratum; RUL; ADD; PP; P78; CHECK; PLAN §2 T6-T7, §3, §4, §5, §6; RULES-78B.md; the kit
  README; P2D. **Read in part:** PR4 §1-§6, §9-§11 (lines 111-614, 717-887 and the blinding text); KCR §3-§9; RP:36-80,
  :103-150; FOCUS's top new entries and the 9 Oct dataset decision; RUN1B:1-90; RUN78:44-48; SR78:192-201, :360-419;
  RK:860-957 and the constant lines; `judge_units_stage1.py:1-80`; `oext_unit.py:1-40`; `oext_eval.py:1-40`; OXU:45-75;
  S1B:10, :115, :121, :151; B16's README head.
- **Not done:** no test was run; no simulation; no Hub, price or token check; the Llama encode count, the hidden-subsample
  id check and the base-repo access check are proposed, not run; RP's and PLAN's money lines were not re-derived beyond
  the sums shown.
