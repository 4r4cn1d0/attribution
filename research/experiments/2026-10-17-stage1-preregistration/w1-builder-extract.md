# W1 builder extract: what the stage-1 commitments builder must build or record before Gate B wave 1, from drafts A, B and C and the addendum §5

**Status: DRAFT for the main-study lead (General Implementation VI). It adopts nothing.** It authorizes no run, spend, download or build start. It changes no frozen Gate B or Gate C rule, no sealed ranking, not D5 = (a), and no user decision recorded in FOCUS. The lead accepts, edits or rejects each item, then passes the accepted items to the builder as an amendment to the brief.

- **Written** 2026-10-17 from about 00:27 to 00:50 UTC (17 Oct, about 06:00 IST) by an Opus worker in the merge workflow. Clock checked with `date -u` at 00:26, 00:37, 00:41 and 00:47 UTC. **Revision 2** (from 01:20 UTC; clock checked at 01:20, 01:27 and 01:31 UTC) applies the checked fixes of `review-consistency.md` (RC-01 to RC-35) and, where the same text sits here, of `review-statistics.md` (S-1 to S-26), by another Opus worker; see "Review fixes" at the end. The numbers that revision 2 adds come from `review_fixes_numbers.py` (output `review_fixes_numbers_out.txt`); `w1_extract_numbers.py` and its output are unchanged.
- **Read-only on the repository.** I wrote files only in this folder. I made no repository edit, commit, pod, spend or download. I opened no `selector.jsonl`, no `hidden/`, no held-out file and no wave-0b `rows.jsonl` or `groups.json`. I opened no Gate B arm. This file holds no row, prompt, answer, anchor or lexicon text.
- **What it is.** For each requirement that drafts A, B, C or the addendum §5 add or change before W1: the requirement; the REQ that it changes; the mark; whether it waits for the user (and, if so, what the builder builds now); the tests. The lead's text items for REQ-21 (c), (e), (i) and (m) are in §6.

**Labels.** **R** = read in a source (source follows). **M** = computed here (`w1_extract_numbers.py`, this folder, output `w1_extract_numbers.out`), or computed in the cited source (named). **E** = estimate (basis follows). **I** = inference, proposal or judgement.

**Marks.** **[BINDING]** = the lead already ruled (ADD; the brief as amended). **[LEAD]** = the lead decides; the draft's default is the build default. **[USER]** = the user decides (a user decision changes, new money, a download, a scope or target change); the rule now in force stays until the user answers. **[USER-CONFIRM]** = the item uses the relayed standing rule "ambitious default, pre-set fallback" ("keep the more ambitious one always but always open to fallbacks"; R: PAPER decisions 26 and 28; Draft B header; Draft C "Labels"). The lead's chat has not confirmed that rule. So each [USER-CONFIRM] item is a [USER] question, with the ambitious option as the recommendation and the rule in force kept until the user answers.

**Deadlines.** **W1** = before Gate B wave 1 (latest start 27 Oct; R: REPLAN §5 via Drafts B and C; REPLAN is a proposal, not adopted, so the date is a planning date, I). **W1-P** = W1, and before REQ-18's predictions freeze. **T1+** = before the lead's first real read of wave-0b `rows.jsonl`, which follows the T1 commit. **S1** = before the stage-1 freeze.

## Short names

| Name | File (main checkout, branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD `3db753e` at 00:41 UTC) | SHA-256 prefix |
|---|---|---|
| FOCUS | `research/FOCUS.md` | `23e3da8f893e8135` |
| PLAN-S | `research/review/2026-10-08-sharpened-direction-DRAFT.md` | `6ff3ff2b15bc4295` |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (revision 5, frozen) | `5c97cce78cfad2c1` |
| BRIEF | `.ai/briefs/stage1-commitments-build-20261016.md` (revision 1) | `12cbf46318728d32` |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` (§1–§5) | `114776482a3287dd` |
| A | `research/experiments/2026-10-17-stage1-prereg-references/stage1-prereg-references-DRAFT.md` (revision 2) | `5835caaea2204674` |
| A-RV | `…/2026-10-17-stage1-prereg-references/reverify-report.md` (R1–R14, N1–N7) | `b61e86756f0207c3` |
| B | `research/experiments/2026-10-17-stage1-analysis-model/stage1-analysis-model-DRAFT.md` (revision 2) | `c8cd8eabd4302ecf` |
| B-VR | `…/2026-10-17-stage1-analysis-model/verify-report.md` | `8126a089751da486` |
| CK-3, CK-11 | `…/stage1-analysis-model/check-W3-W4-W12-W13.md`, `…/check-W11-other.md` | `792b7be7b802ca33`, `0e424cebb1fda4dc` |
| C | `research/experiments/2026-10-17-stage1-review-b-rulings/review-b-rulings-DRAFT.md` (verified) | `79d49e929a28bde2` |
| C-VR | `…/2026-10-17-stage1-review-b-rulings/verify-report.md` | `6fc384fee400cb73` |
| SWEEP | `writing/paper/2026-10-17-lit-sweep.md` | `3c19fc119216ea3e` |
| PAPER | `writing/paper/2026-10-08-icml-draft.md` (revision 6) | `024942b54a6242dd` |
| T1 | the T1 bundle in the lead's workspace `tmp/claude-workspaces/stage1-commitments-build-20261016/workspace/scripts/stage1/` (not yet committed in the main checkout at 00:41 UTC; R: `git log`): `labels.json` `3830fabd59f8c5de`, `settings/build_plant.json` `06f70d98af8ac16d`, `settings/write_score_edit.json` `9fc5f359133e76fd` | as listed |
| P | the prepared set `tmp/kt-prepared/prepared-kt-dolly-olmo2` (manifest `9ed61826…`, R: BRIEF) | — |

Reference only (later stages): `research/review/2026-10-17-stage2-design-notes/` (Llama Gate B-lite `4f1cff0becdaaee9`; second rater `29b781eb44918201`), `research/review/2026-10-17-icml-78b-prep/` (engine round Y `63e83bc19fc90e98`; 7–8B pre-registration `e6a73c92ef97e107`), the mock reviews and the re-plan PROPOSAL.

---

## 0. Short answer

1. **The T1 bundle stays frozen.** Its verification returned fix_required, one blocking defect, and the lead ruled the fixes (ADD §4, 16 Oct 21:20 UTC); that they are applied and checked again is not recorded in FOCUS at `5957a37` (UNVERIFIED here; RC-25). Every item below adds new files and appends labels. None edits `s1common.py`, `write_score_edit.py`, `labels.json`'s T1 entries or the two T1 settings files (R: ADD L1, §4 items 1 and 5). Where a draft needs a T1 helper to do more, a new module does it (§1).
2. **Binding now (ADD §5): five builds.** A token-accounting report for every arm (W1-01); the token-axis dose rule and function (W1-02); the q-only against e1-only score-stability report (W1-04 a); the untuned-refusal stratifier (W1-05); the untuned per-token loss of the added rows in REQ-9's pod pass (W1-06).
3. **Wave 1 waits for one draft item unless the user decides otherwise:** the per-row content-classifier scorer, REQ-23 (Draft C R8.1, VF-4). It fills a gap in a scorer that PLAN-S §5.4 lists, so the user's 9 Oct item (6) applies. Only the user can give it the item (9) exception (C U-19).
4. **The selector files (REQ-16 to REQ-18) change most** (Drafts A, B, C): the screen's bound convention, its SE form and its O error model; a shared seed shift with ρ ∈ {0, 0.67} behind a switch (default ρ = 0, which is L15 (1), until the lead adopts A7; RC-18); a 2× noise sensitivity; the cost model of both conventions with C-lean's contents and c0's definition; both planted placement statistics; the classifier as a named planted diagnostic. All are W1-P. Where the drafts disagree, the builder builds a settings switch, and the default is the rule in force (§8).
5. **REQ-19 changes in four ways:** both O error models with one named decider, a required "f" reading, an input allow-list that refuses any Gate B arm, and a known-answer check of τ_L = 0.0067170919092681925 nats (R: A §L.4; M: reproduced here).
6. **Eleven new labels are proposed** (§5), each appended in the same commit as the code that uses it (L13 (3); C VF-5). Five more names (SR, S6, O-ext H, V2a) go into the W1 text only. Their entries come with their S1 code.
7. **Items that wait for the user, with the build default:** R_tok token-matched random removal (W1-03; [USER], new arms and money; default: not built; ADD §5 item 1 is in force); two more plant locations (W1-10; [USER-CONFIRM]; default: conditional draws only if the lead adopts them); the O-ext H draw (W1-19; [USER]; default: not built, so the dev 100 stays); the S6 arm (W1-12; default: only the duplicate-row test). In every case the rule in force stays until the user answers. The decoy (W1-09) does not wait for the user: it is [LEAD], $0 and scored only, and its default is to build it.
8. **REQ-21 (m) cannot use the brief's template sentence** "this text uses no wave-0a or wave-0b value". FRE and the selector cost model use wave-0a ledger timings, and several choices were made after Gate B values were seen (§6.4).

---

## 1. Rules for every item

1. **New files only, under `scripts/stage1/`** (BRIEF "W1 code rules", Constraints). No file in `experiments/`, `runkit/`, SEAL, ANCH or an existing `scripts/*.py` changes. Engine X stays `472fc7f6…` (R: BRIEF; ADD §4 item 8).
2. **T1 is frozen.** Later REQ-2 needs go in a new module (R: ADD L1). The T1 writer's scorer menu is closed: `write_score_edit.json` names only `l1`, `datashield` and `selfinf_n` beside A1 (R: T1 settings, read between 00:26 and 00:47 UTC). So every new selected set (the classifier, the A1 variants, R_tok) is made by its own script with its own tie label, by read-only use of `s1common.select_top`.
3. **Labels.** Each new label matches `^stage1-[a-z0-9]+(-[a-z0-9]+)*-v[1-9][0-9]*$`, has one owning script, records its parts, id domain and `named_in: "registry, after the seal"` (R: ADD L13 (1)–(2)). It is appended in the same commit as the code that uses it, because the scan test fails on an unused entry (R: ADD L13 (3); C VF-5). The T1 entries stay byte-identical (R: ADD L1). Each settings file names only the entries it uses (R: ADD §4 item 1). Code refers to labels by key, never by a literal (R: ADD L13 (3)).
4. **Data rules.** Synthetic fixtures only in tests. Text-bearing outputs only under `tmp/`, each with a text-free sealed record (R: BRIEF "Data rules"). Never filter a pool by Qwen3Guard (R: FOCUS 8 Oct 13:53 UTC, "Judge rule").
5. **Tests and mutants** follow the brief's runner rules: an unmutated baseline with the same command; a kill only by a real test failure; errors and timeouts are invalid runs (R: BRIEF "Mutation requirements"; ADD §4 item 6).
6. **Conditional items.** An item that runs only after a user's yes is committed as a conditional rule with the text "runs only after the user's yes and a funding event, before any newly run stage-1 cell's outcome is read" (R: C R0.1, VF-7; RC-15: six of the 50 primary cells are reused units whose values were read, so "any stage-1 outcome" is already false). REQ-21 (h) records the reading of PLAN-S:239 for these items: a conditional item whose outcome-free rule text is committed before wave 1 is not "added later"; a yes after Gate B's verdict is disclosed for each item, and the item stays outside P1–P6; if the lead does not accept the reading, each such item approved after a Gate B unit outcome is labelled post-Gate-B exploratory (RC-28). An item not ready at the W1 commit goes to REQ-21 (l) with the label "post-Gate-B exploratory" if it is added later (R: C R0.2; FOCUS 8 Oct 13:53 UTC).
7. **CUDA paths stay untested on the Mac.** Each new pod path says so (R: BRIEF Constraints).

## 2. Checkpoints, in time order

| # | Checkpoint | What must exist first | Source |
|---|---|---|---|
| K1 | Before the T1 commit | nothing new; the decoy and F9 labels are appended later, with `build_plant.py`, so T1 is not reopened | ADD L1; C VF-19 (a plant change reopens T1; the decoy and F9 do not change T1's plant rule or settings, I) |
| K2 | Before the lead's first real read of `rows.jsonl` (T1+) | W1-04's code and settings (score stability; V1 if adopted). If it lands later, REQ-21 (m) says so and the report is labelled post-T1 | ADD §5 item 2; C R7.4, VF-18 |
| K3 | Before any plant draw is computed | W1-09's decoy labels (and W1-10's, if adopted), appended with `build_plant.py` | B §G F7; ADD L13 (7) |
| K4 | Before REQ-19 runs | the O error model for the labels, REQ-16 and REQ-19 (C-i); the written "f" reading; W1-16's code | B §E.2; C R5b.1, VF-2; CK-3 §4.5 |
| K5 | Before REQ-17's settings and REQ-18's predictions freeze (W1-P) | W1-13, W1-14, W1-15; Draft A's LQ27, LQ29, LQ31 (and LQ25, LQ26, LQ28 by A-RV N1) | A "Where each part goes"; ADD L15 (3) |
| K6 | Before the W1 commit | REQ-23 (W1-07) or the user's item (9) extension; every other W1 item built or listed in REQ-21 (l); REQ-20's manifest; REQ-21's text | FOCUS 9 Oct 19:37 UTC items (6), (9); C VF-4 |

---

## 3. Register

| ID | Item | REQ changed | Source | Mark | Build now | Deadline |
|---|---|---|---|---|---|---|
| W1-01 | Token accounting of every arm's edit | new REQ-27 (a) (Part G report + new module); reads REQ-4, -5, -7, -8, -14, -15 outputs | ADD §5 item 1 | [BINDING] | yes | W1 |
| W1-02 | Token-axis dose: exact rule and pure function | new REQ-27 (b); REQ-21 (b), (f), (h) | ADD §5 item 1; A LQ47; A-RV N2, R8 | [BINDING]; the axis reading [LEAD] | rule text: yes (must); code: yes (should) | W1 |
| W1-03 | R_tok, token-matched random removal for A1, L1, H1 | new REQ-30 | PAPER decision 26; SWEEP entry 6; A LQ47 | [USER] (new arms and money; RC-14) and [LEAD] (LQ47) | no (ADD §5 item 1 in force); conditional build only if the lead amends LQ47 | W1, or exploratory |
| W1-04 | A1 report-only variants: (a) q-only against e1-only; (b) V1, Adam-preconditioned | REQ-25 | ADD §5 item 2; C R7.4 | (a) [BINDING]; (b) [LEAD] | yes, both | T1+ (K2) |
| W1-05 | Untuned-refusal stratifier | new REQ-28 | ADD §5 item 3 (a) | [BINDING] | yes | W1 (rule must; code should) |
| W1-06 | Untuned per-token loss of the added rows | REQ-9 | ADD §5 item 3 (b) | [BINDING] | yes | W1 |
| W1-07 | Per-row content-classifier scorer | REQ-23 (new, Part C) | C R8.1–R8.4, VF-4 | [LEAD]; run paid from stage 1's funding event, no separate [USER] item (RC-20); exception [USER] (U-19) | yes; wave 1 waits for it | W1 (K6) |
| W1-08 | Plant construction checks and the plant-rank report | REQ-3 settings; new REQ-29 | B §G F2–F6, F8; C R8.2, R8.3; ADD §3 (2) | [LEAD] | yes | W1 (rule must; code should) |
| W1-09 | Scored-only refusal decoy | REQ-8 (new settings file), REQ-6, REQ-3, REQ-23 | B §G F7 | [LEAD] | yes | W1 (K3) |
| W1-10 | Two more plant locations | REQ-8 (new settings file) | B §G F9 | [USER-CONFIRM] | draws only, as a conditional item, if the lead adopts them; else not built | W1, or exploratory |
| W1-11 | S-pool record: PKU `line` and companion index | REQ-6 | C R4.4 | [LEAD] | yes | W1 |
| W1-12 | Duplicate-row add test (for S6) | REQ-7 | C R4.4 | arm [USER]; test [LEAD] | the test only | W1 |
| W1-13 | Feasibility screen: bound, SE form, O error model, τ_L reference, coherence gate | REQ-16 | A LQ36, LQ39; B §A.12, §F; C R1.1, R1.2, R1.8 | [LEAD] (conflicts, §8) | yes, with switches | W1-P (K5) |
| W1-14 | Generative model: seed coupling, 2× noise, O and L noise, cost model | REQ-17 | B §A.12 (A7); A §C.5–§C.6; C R1.8, R5b.2 | [LEAD] (edits L15 (1)) | yes | W1-P (K5) |
| W1-15 | Predictions: c0 and C-lean, units, placement statistics, classifier | REQ-18 | A LQ27, LQ29, LQ31; B §G F3; C R8.4, VF-12 | [LEAD] | yes | W1-P (K5) |
| W1-16 | Limit checks: O MDE in two error models, f, allow-list, τ_L known answer, NI planning report | REQ-19 | A §L.3–§L.4, LQ37–LQ41; B §E.2; C R5b.1; ADD L16 | [LEAD]; U8 [USER] | yes | W1, before REQ-19 runs (K4) |
| W1-17 | Manifest: conditional flag, not-built entries | REQ-20 | C R0.1, R0.2 | [LEAD] | yes | W1 |
| W1-18 | Over-refusal checks on existing answers | new Mac script (lead's run) | C R5b.3 | [LEAD], run before U8 is decided, whatever the answer (RC-19) | yes (the script) | W1, before U8 |
| W1-19 | O-ext H counts-only sealed draw | REQ-26 (new; lead's run) | C R5b.2; B §E.3 | [USER] (it reverses "never from the hidden remainder") | no (fallback F in force) | W1, or exploratory |
| G-1 | Gap found while merging: R draws d = 9–12 for plan B | REQ-4 | PLAN-S:118; B §A.6 | [LEAD] (I) | the seed list is a W1 item (REQ-21 (d)); building the d = 9–12 files at W1 is optional (RC-07) | W1 (seed list); files any time (outcome-free) |

REQ numbers 23–26 are Draft C's provisional numbers (R: C §4). Numbers 27–30 are proposed here (I). The lead assigns the final numbers.

---

## 4. The items

### W1-01. Token accounting of every arm's edit [BINDING]

- **Requirement.** For every stage-1 edit file, record without text: the rows removed, added or rewritten; their **target tokens** (response + end-of-turn tokens; R: `prepare_task.py`:395); their **total row tokens** (prompt_tokens + target_tokens; R: `prepare_task.py`:383); each as a share of P's corpus total; the same per unit and per category; and the optimizer steps of the edited corpus. Steps = ⌈rows / 128⌉ (I as a rule; M: 4,800 rows → 38, 4,200 → 33, 4,848 → 38, matching R: PLAN-S:102–103). Arms: R_d, R_1200, R_2400, R+S1, H1, H2a, H2b, the 8 octiles, the 8 controls, A1, L1, DataShield-style and Self-Inf-N-style if built, S1, S3, S4, SD-600 (removed k rows, and the rewritten rows' tokens before and after), the plant edits, and R_tok if built. The content classifier's scored-only set is reported the same way. Steps per arm answer PAPER risk 30 and SWEEP's design action 1 (R).
- **Why a new module.** T1's `PreparedView` keeps only `row_id` and `target_tokens` (R: `s1common.py`:324–351). P's training rows also carry `prompt_tokens` (R: the key list of one row, read between 00:26 and 00:37 UTC; values not printed). ADD L1 puts later REQ-2 needs in a new module.
- **Build.** (1) `scripts/stage1/token_accounting.py`: a text-free view of P (manifest pinned; keeps `row_id`, `prompt_tokens`, `target_tokens`; drops the text fields at once, as T1 does). (2) `scripts/stage1/report_token_accounting.py`: reads each edit file and each add or rewrite record by SHA-256 and writes one canonical, text-free table with provenance. For add rows, the token counts come from REQ-7's sealed record. REQ-7 keeps both `prompt_tokens` and `target_tokens` as kept fields (T1 `sealed_record` allows this; R: `s1common.py`:432–475).
- **REQ changed.** New REQ-27 (a). It reads, and does not change, REQ-4, -5, -7, -8, -14 and -15. REQ-21 (b), (f) cite its table (R: ADD §5 item 1).
- **User decision.** None.
- **Tests (synthetic P).** Sums and shares equal hand values; the steps rule gives 38, 33, 38 at 4,800, 4,200, 4,848 rows; a rewrite reports tokens before and after; an id outside P refuses; a wrong manifest hash refuses; two runs give identical bytes; a byte scan finds no fixture text. **Mutants:** total tokens = target tokens only; shares against the edited corpus instead of P; steps by floor.

### W1-02. Token-axis dose: the exact rule and a pure function [BINDING; axis reading LEAD]

- **Requirement (rule text in REQ-21 (b), (f); I as the exact form).** Place each removal filter on the random dose curve along a token axis, beside the row axis of PLAN-S §5.3 item 1 (R: ADD §5 item 1).
  1. Curve points: (0, 0) for a0, and (T̄_n, Ḡ_n) for n = 600, 1,200, 2,400. T̄_n = the mean removed token mass over the R draws run at dose n (R_600 at seeds 1101–1108; R_1200 and R_2400 at d = 2–4, seeds 1102–1104; R: PLAN-S:116; ADD L5). Ḡ_n = the dose's restoration U(a0) − U(R_n) by the stage-1 reading's primary estimator (HB or S-a, §8 row 1).
  2. For filter m with removed mass T_m and restoration Ḡ_m: the **token-equivalent random dose** T*_m = the first T, from 0 upwards, where the piecewise-linear curve reaches Ḡ_m; "0" if Ḡ_m ≤ 0; "beyond the curve" if Ḡ_m exceeds every point. Also the ratio T*_m / T_m.
  3. The **token-matched contrast** Λ_tok,m = Ḡ_m − G_R(T_m), with G_R linear between the curve points. If T_m > T̄_2400, it is "beyond the curve" (no extrapolation).
  4. Axes: total row tokens (default, I: training compute scales with every processed token); target tokens (sensitivity); rows (PLAN-S §5.3 item 1). The lead records the axis reading in REQ-21 (h) [LEAD].
  5. Report only. No label, no α claim. Its interval comes from the stage-1 reading (Draft B's S-HB-tok, R: B §A.7). H1 likely removes fewer tokens than R_600 (I: it removes the 600 shortest answers), so H1's Λ_tok rests on the unmeasured segment from (0, 0) to (T̄_600, Ḡ_600). The record says so. This is the reason for W1-03.
- **Build.** `scripts/stage1/dose_axis.py`: one pure function for items 2–3 on all three axes; no randomness; no file input. Code at W1 is recommended (I: it is small, and its hash then fixes the rule). The reading (B16, S1) calls it.
- **REQ changed.** New REQ-27 (b); REQ-21 (b), (f), (h). LQ47 is a **W1** item (A-RV R8): the lead records ADD §5 item 1 as its ruling (R: A §C.1).
- **User decision.** The title. PAPER decision 26 keeps "Compute-Matched" if removals are token-matched **or** a token-matched analysis is pre-registered beside the row-matched one (R: PAPER:240). The lead states whether Λ_tok counts as that analysis (A-RV N2). Recommended reading (I): yes, if the W1 text defines Λ_tok exactly as above. If the lead rules no, the title goes back to the user ([USER-CONFIRM]: decision 26 rests on the relayed rule; R: PAPER:22, :240). **Silent default (RC-33):** this pre-registration carries the token-axis analysis (LQ47) in any case; the title is a paper item and stays as PAPER has it until the user confirms the standing rule or decides.
- **Tests.** Interpolation equal to hand values; the first crossing on a non-monotone synthetic curve; Ḡ_m ≤ 0 gives 0; above every point gives "beyond the curve"; T_m = 0 gives Λ_tok = Ḡ_m; on the row axis, the dose points give the row doses exactly. **Mutants:** the last crossing; extrapolation past T̄_2400; target tokens as the default axis.

### W1-03. R_tok, token-matched random removal for A1, L1, H1 [USER; LEAD LQ47] (conditional)

- **Rule in force.** ADD §5 item 1: "No new arm now". The token-axis analysis (W1-02) is the fallback that is already binding.
- **Mark (revision 2; RC-14).** [USER]: it adds new arms and money, and it edits the lead's ADD §5 item 1 ("No new arm now"), so the lead must amend LQ47 and the user must say yes. Revision 1 marked it [USER-CONFIRM].
- **Proposal (I), if the lead amends LQ47 and the user agrees.** For filter m ∈ {A1, L1, H1} with removed mass T_m (on the W1-02 axis): per unit g, walk g's rows in the sealed order of label `random_removal.rtok`, parts (m, d, g); stop at the row that crosses T_m / 8; keep that row only if it brings the unit's mass closer to T_m / 8 (a tie keeps it). This keeps R's per-unit stratification and changes only the dose (I). Draws d = 2–4 at seeds 1100 + d (the secondary-arm seed rule; R: ADD L5; BRIEF REQ-21 (g)). Secondary arms, one-sided bounds only (R: PLAN-S §5.3). The contrast is Ḡ_m − Ḡ_Rtok,m on the common seeds. It never enters P1–P6 (D5 = (a)).
- **Timing.** H1's file can be built at $0 now (its T_m comes from P). A1's comes after the T1 A1 run; L1's after REQ-10's pod output. The same frozen code builds all three.
- **Cost (E).** 9 runs ≈ $13.1; with 3 pods' overhead ≈ $15.5; × 1.25 ≈ $19.3 (M: script; inputs R: A §C.2–§C.3: 1 FRE = 2,934 s, $1.79/h, 26.0 min per pod).
- **Build now (default).** Nothing. If the lead amends LQ47 before W1, build `scripts/stage1/build_r_tok.py` with its settings and label, committed as a conditional item (§1 item 6). If it is not committed at W1, any later R_tok is post-Gate-B exploratory.
- **Tests (if built).** Each unit's mass lies within half of its crossing row's mass of T_m / 8; the order follows the label; T_m above a unit's mass refuses; the files differ by d; `parse_edit` round trip; no text. **Mutants:** a global (not per-unit) draw; always including the crossing row; the wrong axis.

### W1-04. A1 report-only variants [(a) BINDING; (b) LEAD]

- **(a) One-shot score stability (R: ADD §5 item 2).** From the same wave-0b attributes unit as A1, with the same input checks as T1's A1 path (complete; engine X; recipe S; query bank `anchors-2cf96336…`; each a0 source's `complete_sha256`; R: BRIEF REQ-14; T1 settings): a_i^q = cosine_H(i, q) − cosine_S(i, q) and a_i^e1 likewise. Report the Spearman ρ of a^q against a^e1 over all 4,800 rows (average ranks for ties), and the Jaccard overlap of the two top-600 sets. Also check that (a^q + a^e1)/2 equals T1's a_i within 1e-12 (the T1 tolerance; R: BRIEF REQ-14), and report each set's Jaccard with A1's T1 set.
- **(b) V1, Adam-preconditioned (R: C R7.4).** The same bi-anchored score with `adam_score` in place of the cosine, mean over q and e1. Report its top-600 Jaccard with A1, L1, H1 and the classifier (as each exists), and the Spearman ρ of its 8 unit means against A1's unit means (both from rows). Call it "Adam-preconditioned", never "LESS" (R: C R7.4: equality with LESS is UNVERIFIED).
- **Never an arm.** The T1 A1 contract does not change (R: ADD §5 item 2; C R7.4).
- **Build.** `scripts/stage1/report_a1_variants.py` and its settings. Top-600 sets use `s1common.select_top` with the new label `a1_variants.ties`, parts (variant) ∈ {q, e1, adam}. The T1 key `a1.ties` belongs to the T1 writer, and two scripts may not share a label (R: ADD L13 (3)). The T1 writer exposes `check_attributes_unit` and `a1_scores` (R: `write_score_edit.py`:59, :108). Import `check_attributes_unit` read-only for the unit checks. The per-checkpoint values need their own row parser, so add a cross-test: on the T1 fixtures, (a^q + a^e1)/2 equals `a1_scores`'s output (I).
- **REQ changed.** REQ-25 (C §4), widened to hold (a). REQ-21 (g), (h); (m) states whether this code was committed before the first real read of `rows.jsonl` (K2).
- **User decision.** None.
- **Tests (T1's synthetic attributes fixtures).** Spearman and Jaccard equal hand values; ties follow the sealed rank; the mean identity holds; V1 reads only `adam_score`; a missing checkpoint refuses; a wrong engine, recipe or query bank refuses; no text. **Mutants:** e1 read as q; Pearson instead of Spearman; V1 from the cosine; 599 rows in a set.

### W1-05. Untuned-refusal stratifier [BINDING]

- **Requirement (R: ADD §5 item 3 (a)).** For each dev evaluation prompt (200 harm, 100 over-refusal), record whether the untuned model's greedy answer is REFUSAL-OPENING by the pinned lexicon (REQ-1). Use only the untuned unit's existing evaluation records. It serves only as a stratifier of the prompt-flip reports (S1 reading).
- **Build.** `scripts/stage1/report_untuned_refusal_strata.py` and settings. Input: the Gate A untuned unit `family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1`, `COMPLETE.json` `b5083ce9…` (R: A §L.4), checked by the frozen `family_probe_reading.sealed` (read-only use, as `gate_a_overrefusal_counts.py`:26–31 does). Output: prompt id → class, and counts per bank; text-free. The lead runs it on the Mac at $0. It reads no stage-1 or Gate B outcome.
- **REQ changed.** New REQ-28; REQ-21 (f).
- **User decision.** None. O-ext prompts, if they run, get their stratum from O-ext's own untuned run (S1; I).
- **Tests.** A synthetic eval folder; classes by hand; a wrong `COMPLETE.json` hash refuses; a lexicon hash other than `bbbc71e9…` refuses; a byte scan finds no answer text. **Mutants:** sampled answers in place of greedy; an unpinned lexicon.

### W1-06. REQ-9: the untuned model's per-token loss on the added rows [BINDING]

- **Requirement (R: ADD §5 item 3 (b)).** In REQ-9's existing pod pass (no new pod): the untuned model's mean per-token NLL (and its exp, the perplexity) on each added row, teacher-forced, over the response and end-of-turn targets (the engine's training-loss definition; R: A §L.4 citing `prepare_task.py`:81–84), encoded by `encode_train` under recipe S's limits.
- **Which rows.** S1's 48 (prompt, PKU-safe response); every row of the S3 subset with its safe response, plus S1's rows outside the subset (R: ADD L10 (2)), so that S3's 48 are covered whatever SAS picks; S4's 48 kept rows (prompt, untuned answer). Per-arm means for S3 are computed later on the Mac, by id.
- **REQ changed.** REQ-9 (settings: a `loss_rows` list by SHA-256; output: per row id, n_target, mean NLL; text-free); REQ-21 (f).
- **User decision.** None.
- **Tests (tiny OLMo-2 fixture, CPU).** The value equals the engine's `_target_nll` mean on the same encoding (R: A §R.2.5 row 3, `engine.py`:218–245); a LoRA fixture with a non-zero B gives the base model's loss (adapter disabled); determinism twice; `encode_train` refusals are counted; no text. CUDA: untested. **Mutants:** a token sum instead of the mean; the adapter left on; prompt tokens counted.

### W1-07. REQ-23: the per-row content-classifier scorer [LEAD; wave 1 waits]

- **Requirement (R: C R8.1–R8.4).** A Part C script outside the engine identity. It writes each row's normalized Unsafe label-sequence score on (prompt, response) by read-only use of `GuardScorer.label_scores` (R: `SS/scoring.py`:100, :183), as the pinned Gate C classifier scores rows (R: `scripts/gate_c_classifier.py`:6–10, :55). Unscored rows are counted, never imputed. Rows: all 4,800 dev rows once; the 75 plant rows once; the 37 decoy rows if W1-09 is built.
- **Selection.** Its top 600 is "scored only" (R: PLAN-S §5.4). The T1 writer cannot take it (§1 item 2). So this script selects the set with the new label `classifier.ties` and writes no edit file.
- **Gate C consistency (I).** On a CPU fixture, the per-unit means of its scores equal the pinned Gate C classifier's per-unit means through both code paths (the pattern of REQ-3's Gate C byte test). The lead checks real-data equality after the pod run. That check is not a W1 condition.
- **Run.** On a stage-1 pod, about $1 (E: C R8.1, from CK-EM §4.2). The content classifier is a planned scorer (R: PLAN-S:168) and every scorer is charged in full (R: PLAN-S:203), so the run is part of the approved plan. It is paid from stage 1's funding event, never from the Gate B balance or on a Gate B kit pod (R: BRIEF T4; C VF-4). No separate [USER] item (RC-20).
- **REQ changed.** New REQ-23; REQ-18 (W1-15); REQ-21 (g), (j); REQ-20.
- **User decision.** One only: the item (9) exception (U-19) if the code is not ready at W1 (the run's money comes with stage 1's funding event; RC-20). Then wave 1 waits (R: FOCUS 9 Oct 19:37 UTC item (6); C VF-4). Optional prompt-only score (C R8.6): [USER], about +$0.5 (E: C R8.6); default not built.
- **Tests (a fake GuardScorer).** Scores pass through unchanged; unscored rows are counted; a wrong guard revision refuses (recipe S pins `6ec42827da0c…`; R: C R5b.3); pools by SHA-256; top 600 with sealed ties; determinism; no text. **Mutants:** unscored rows set to 0; per-unit selection; the prompt-only score in place of (prompt, response).

### W1-08. Plant construction checks and the plant-rank report [LEAD]

- **Requirement (R: B §G F2–F6, F8; C R8.2, R8.3; ADD §3 (2); CK-11 §4).**
  1. **REQ-3's settings** add the plant pool (37 and 75 rows) and, if built, the decoy pool, as pool files by SHA-256 (REQ-3 already allows a pool file; R: BRIEF REQ-3). The pod pass then logs per-row features for L1 and DataShield-style on those rows.
  2. **A new Part G report, `scripts/stage1/report_plant_ranks.py`.** For each text-only scorer (L1, H1, H2a, H2b, DataShield-style if built, the classifier): the planted cell's rank at M = 8, 32 and 128 on the planted corpus (cell score = the mean of its rows' scores, as ADD L15 (6)); beside it, the same unit's rank without the plant (R: ADD §3 (2)); the row AUC of the plant rows against all Dolly rows of the planted corpus and against the drawn unit's Dolly rows, with a bootstrap 90% interval over rows (label `plant.auc_boot`); the dilution table C(N − r, m) / C(N − 1, m) at each cell size (F4); the relocation replay over every eligible 37-row leaf with no oversize row (F6); the decoy's rank and AUC beside the plant's (F7, if built).
  3. **Labels in the output.** "Construction check". These ranks never count toward "finds a known cause". Only A1 and Self-Inf-N-style, scored on a0_plant (S1), count (R: B F2; C R8.2).
  4. **Publication.** The table is published before the plant pilot, and also if the pilot stops (F8).
- **REQ changed.** REQ-3 (settings only); new REQ-29; REQ-21 (g), (j). REQ-21 (j) carries C R8.3's prediction: "the classifier ranks the planted leaf first at M = 128" (I: the plant's prompts come from a harm dataset; R: C R8.3).
- **User decision.** None for the checks. Which statistic places the planted predictions is W1-15's question (§8 row 7). This report computes both.
- **Build now.** The rule text (must, W1). The code (should, W1; I: it costs $0 and is outcome-free). The lead runs it on the Mac after REQ-3's and REQ-23's pod outputs exist.
- **Tests (a synthetic planted corpus with known scores).** Ranks equal hand values at each M; AUC by hand (Mann–Whitney, ties count 0.5); the bootstrap is fixed by its label; the F4 formula equals a brute-force count on a small N; the replay covers every eligible leaf and no oversize leaf; the same-unit rank without the plant; no text. **Mutants:** max aggregation in place of the mean; ties counted 0 in the AUC; oversize leaves in the replay.

### W1-09. The scored-only refusal decoy [LEAD]

- **Requirement (R: B §G F7; CK-11 F7).** A sealed draw of 37 S-pool rows (PKU-safe, refusal-opening answers to PKU red-team prompts) outside S1, the S3 subset, the S4 list (512; R: ADD L11) and the plant rows. It sits in a 37-row, no-oversize leaf of a unit other than the plant's, for the rank replay only. It is never trained and has no edit file. Reading (R: B F7): a scorer that ranks the decoy as high as the plant is topic-driven.
- **Build.** `build_plant.py` (REQ-8; not written yet) also loads a new settings file, `settings/build_plant_extra.json`, beside the T1 `build_plant.json`, which it still loads with its literal pin (R: ADD §4 item 5). New labels: `plant.decoy_rows` (the 37 rows, in sealed order), `plant.decoy_unit` (one of the 7 other units), `plant.decoy_leaf` (the leaf, by the plant's own leaf-rule text; R: ADD §4 item 3). It writes the decoy pool under `tmp/` and a text-free record. REQ-6's stop rule counts the decoy's 37 rows among the lists that the S-pool must fill (I).
- **A1's decoy rank.** Whether the attribution pass can score rows outside its corpus is UNVERIFIED (R: CK-11 F7). Default: A1's decoy result is reported as "not done".
- **REQ changed.** REQ-8 (new settings file, three labels); REQ-6 (stop count); REQ-3 and REQ-23 (pool input); REQ-29 (report).
- **User decision.** None (it is $0 and scored only; R: B §H G1).
- **Tests.** Exactly 37 rows; disjoint from S1, the S3 subset, the S4 list, the plant rows and the anchors; another unit than the plant's; no oversize row in the leaf; determinism; no text. Most important: T1's `build_plant.json` stays byte-identical, and the plant's own draws are the same with and without the decoy. **Mutants:** decoy rows that overlap S4; the decoy in the plant's unit; the decoy drawn under a plant label.

### W1-10. Two more plant locations [USER-CONFIRM] (conditional)

- **Rule in force.** One plant location. F6's relocation replay gives the scorer-side spread at $0 (R: B §G F6, F9).
- **Proposal (R: B §G F9; CK-11 §2.4).** Two more real plant locations, run if stage 1b is funded; about $34–70 (E: CK-11 §2.4). The plant is committed before wave 1 (R: FOCUS 8 Oct 13:53 UTC; PLANF:123). So the locations must be drawn by a W1 rule, or a later F9 is post-Gate-B exploratory.
- **Build now (default).** Only if the lead adopts F9 as a conditional item: the draws by new labels `plant.extra_unit` and `plant.extra_leaf`, parts (location ∈ {2, 3}). Units are drawn without replacement from those other than the main plant's unit (I). Each leaf follows the plant's leaf-rule text. The edit files come from REQ-8's own edit rules. Nothing runs without the user's yes and the 1b funding event. If not adopted, list F9 in REQ-21 (l).
- **Tests (if built).** Three distinct units; each leaf is eligible; T1's plant draws unchanged; each edit parses with the stated corpus size.

### W1-11. REQ-6: the S-pool record holds each row's PKU `line` and companion index [LEAD]

- **Requirement (R: C R4.4, §4).** The text-free S-pool record adds, per row: the PKU file id, the row's `line`, the index of the response taken, and the index of its unsafe companion response. Read them by `line` from the same hash-checked bytes, after `parse_pku`, as ADD L8 reads the response ids. Refuse any index that is not the integer 0 or 1 (R: ADD L8). It costs nothing now and serves SR (S1) and V2a (C R7.5). Whether the record already holds these fields is UNVERIFIED (R: C §8).
- **Tests.** A synthetic PKU fixture: the fields equal hand values; a bad index refuses; no text.

### W1-12. REQ-7: a duplicate-row add test (for S6) [arm USER; test LEAD]

- **Requirement (R: C R4.4, §4).** REQ-7 can write 48 rows that are byte-identical apart from distinct `add-` ids, and `parse_edit` accepts them. A test checks it. The S6 arm itself is [USER] (C U-6; the package ladder is [USER-CONFIRM]).
- **Why now (I).** Whether the engine's add edit accepts duplicate texts is UNVERIFIED. This test is the smallest decisive check for S6's feasibility.
- **Build now.** The test only. S6's settings and label (`stage1-s6-v1`) come with S6's writer, if the user approves the arm (C VF-5).

### W1-13. REQ-16: the feasibility screen [LEAD; conflicts in §8]

| # | Change | Rule in force | Draft proposal | Build |
|---|---|---|---|---|
| 1 | Bound convention for "upper 90%" | BRIEF REQ-16 "upper 90%", unspecified (R) | B and C: the upper end of the two-sided 90% interval, one-sided 95% (R: C R1.2; B §A.12). A: a one-sided 90% bound (R: A LQ36, LQ39) | a settings key `screen_upper_quantile`; default 0.95 (two of three drafts; the lead records the reading in REQ-21 (h)) |
| 2 | O's error model | none fixed (R: CK-3 §4.1) | prompt-clustered (B §E.2; C R1.8); seed-only (CK-3 §4.7 option 1; A LQ36 "from the arm's seeds") | a settings key; default prompt-clustered; it must equal REQ-19's decider (K4) |
| 3 | The SE form | pooled residuals of the replay (R: ADD L16 scope sentence) | the HB form: per-option seed variance plus a crossed prompt (or task-row) part (R: B §A.12, A8; it edits L16, B V-13) | both forms behind a switch; default = the lead's ruling in the merged record; if there is none at K5, ADD L16 |
| 4 | τ_L reference | a0 (R: PLAN-S:124; C R1.1) | dose-matched R reported beside it for removal options (B §E.4; A LQ38, to GPT) | compute both; the screen uses the settings' reference, default a0 |
| 5 | Coherence gate | none | an option that fails the arm-pooled answers-end bar is infeasible (R: B §F item 6) | a boolean per option; default no option fails in the simulation |

- O stays against the untuned model θ0 (decided; R: FOCUS 8 Oct 13:53 UTC). The pick rule does not change (R: BRIEF REQ-16).
- **Tests.** Each switch both ways on a hand boundary case (for example, quantile 0.90 against 0.95 flips one option); the HB form on a two-option table equals (b)'s estimate and variance with seed df J − 1 (R: B §A.12, V-5); the prompt part on and off; a failing option is never picked; the τ_L reference switch. **Mutants:** the 0.90 quantile when 0.95 is set; the prompt part dropped; the coherence gate removed.

### W1-14. REQ-17: the generative model [LEAD; edits ADD L15 (1)]

1. **Seed coupling (R: B §A.12, H A7).** Cell noise = a shared seed shift s_j plus an option-specific shift, with same-seed correlation ρ ∈ {0, 0.67}. **Builder default (RC-18):** the settings' ρ grid is {0}, which equals L15 (1) (in force); {0, 0.67} sits behind a switch until the lead adopts A7 (A7 edits L15 (1) and is [LEAD] W1-P; DRAFT §7.4). 0.67 is PREREG §2's pre-Gate-B "low" scenario, not a fitted value (R: B §A.12). Per-option SD σ stays 2.65 pp central and 3.85 pp as a sensitivity (R: ADD L15 (1); PLAN-S:117). Shared SD = σ√ρ; option-specific SD = σ√(1 − ρ). Pair SD at σ = 2.65: 3.748 pp (ρ = 0), 2.153 pp (ρ = 0.67); at σ = 3.85: 5.445 and 3.128 pp (M). **Never** σ̂_gate, the wave-0a ρ̂ or its CRN value (R: ADD L15 (1); B §A.12).
2. **CRN (R: ADD L15 (4)).** The shared shift is drawn from a new label `selector.seed_shift`, parts (replicate), by seed index. So the T1 stream `selector.noise` keeps its meaning (I). Noise = σ(√ρ·z_s + √(1 − ρ)·z_e), with the same z for both ρ values, both policies and both grids.
3. **The 2× sensitivity (R: B §A.12).** One non-keep option per replicate, drawn by a new label `selector.hetero`, parts (replicate), gets total SD 2σ with the shared part unchanged, the convention of B's simulator (R: `sim_w2.py`:684). Its option-specific SD is 5.300 pp (ρ = 0) or 4.836 pp (ρ = 0.67) at σ = 2.65 (M). Report only.
4. **The frozen rule.** In force (L15 (1)): the per-cell rule and k maximise E[G(pick)] with equal weight per (shape, size) grid point, at ρ = 0. **A [LEAD] proposal (I), only with A7 (RC-18):** average with equal weight over (shape, size, ρ). This is a new rule: no draft states it, and L15 (1) does not average over ρ. The 3.85 pp and 2× cases never choose the rule. Results per ρ are reported. Alternative under A7: choose at ρ = 0 only (conservative).
5. **O noise (R: C R1.8, §4 REQ-17; CK-3 §4.2).** The SE of O(option) − O(θ0) follows the error model of W1-13 row 2. Prompt-clustered default: 3.9–4.2 pp at 100 prompts (R: CK-3 §4.2, M there; C gives 3.98–4.22 from CK-OR §4). Seed part: a0's O SD 1.15 pp (R: CK-3 §4.2; 2 df). Bank size 100 is in force. A 500-prompt run (dev 100 + 400 via N) is a sensitivity only if the user approves O-ext before K5 (CONS UW-07a; B §E.3; [USER-CONFIRM] ladder). H is not an option unless the user changes the 8 Oct rule (CONS UW-07b; RC-05). The U–O correlation comes from Gate A's a0 seeds and the untuned unit (R: BRIEF REQ-17). It rests on 3 seeds (I: weak; §10).
6. **L noise.** Seed SD s = 0.0023749 nats and τ_L = 0.0067171 nats (R: A §L.4; W1-16). The true L effects default to 0 (R: ADD L15 (2)). See §10 item 6 on the dose problem.
7. **Cost model per convention (R: A §C.2–§C.6; ADD L15 (3)).** C-full: unit 1 FRE = 2,934 s (R: A §C.3, LQ25); training 219.7 s = 7.49% of the unit (M). C-lean (a), A's default (LQ27): c0 ≈ 870 s (E: A §C.5; 869.9 s, A-RV M5), training 25.3% (M); (a) adds to PLAN-S:202's wording ("training plus 200 harm prompts × 1 sample") but does not contradict it, and it closes the gap with PLAN-S:127's screen, which needs O and L; REQ-21 (h) records (a) as that reading; [LEAD] as a reading, [USER] if the lead reads it as a change, with (b) in force (RC-09); its 100 greedy over-refusal answers take 330–371 s by arm (R: A-RV R7, which corrects A's 330–370 s). C-lean (b): c0 ≈ 480 s, training 45.8% (M). A ψ-trial costs setup + training + ψ × evaluation; a φ-trial costs setup + φ × training + evaluation (I, from PLAN-S §4.5 and §8). B and c_d are in units of c0 under both conventions; the c_d/c0 grid includes 0; B − c_d < 2c0 picks keep; B = 2 is a boundary cell (R: ADD L15 (3)).
8. **Inputs.** Pre-Gate-B records only, each by path and SHA-256 (R: BRIEF T2). The cost figures use the wave-0a ledgers, which are Gate B values; REQ-21 (m) names them (R: A §B).
- **REQ changed.** REQ-17 and its settings; REQ-21 (k), (m).
- **Tests.** Zero noise picks the true best (as before); at ρ = 0 the model equals L15's; an equal shift on every option leaves the pick unchanged; CRN holds across ρ (identical z); the 2× option is drawn by its label and is never keep; the rule follows the criterion that the settings name (L15 (1) by default; the ρ average only with A7); the code refuses a ρ grid other than the settings' grid (RC-18); cost sums equal hand values. **Mutants:** ρ taken from σ̂_gate; the shift drawn per option (no coupling); the 2× applied to keep; the rule chosen at one ρ.

### W1-15. REQ-18: the predictions [LEAD]

1. **Re-run on W1-14's model.** REQ-18 is not built yet, so it is built on the new model (R: B §A.12).
2. **c0 and C-lean (W1-P; R: A §C.5–§C.6, LQ27, LQ29, LQ31; A-RV N1).**
   - C-lean contents, default LQ27 (a): training + 200 harm prompts × 1 sampled answer with its guard + the task-loss pass + the 100 greedy over-refusal answers with their guard. The alternative (b) is C-lean as written in PLAN-S:202. (a) is a [LEAD] reading that closes the gap between PLAN-S:127 and PLAN-S:202, recorded in REQ-21 (h); it becomes [USER], with (b) in force, if the lead reads it as a change to the approved plan (RC-09).
   - c0 = one real job: a cold start, the full training of an R arm, and exactly the C-lean evaluation of LQ27 (LQ29). Under LQ30 (ii), read "an a0 arm" (an S1 choice).
   - Units: 1 FRE under C-full; the measured c0 under C-lean (LQ31). Predictions are curves in c_d/c0, and the measured c0 only places the result on them (R: FOCUS D5 entry, U3 (a)).
   - By A-RV N1, LQ25 (FRE), LQ26 (C-full's stages) and LQ28 (the lean prices) also fix what the curves mean. So they are W1-P too [LEAD]. 1 FRE = 2,934 s and the lean per-answer prices are fixed at the W1-P commit from the three wave-0a ledgers and never re-estimated; PLAN-S D3 freezes the other cost rules (LQ30, LQ32–LQ35) and does not change FRE or the prices (RC-08).
   - Every cell is reported under both conventions (R: PLAN-S:202).
3. **Placement statistic (§8 row 7).** L15 (7)'s planted top-k hit is in force (R: ADD). B §G F3 makes row AUC primary [LEAD; it edits L15 (7); C C-k]. Build both: per grid point, the simulated 90% range of the top-k hit and of the empirical row AUC (37 or 75 plant rows), from the T1 stream `selector.plant`. The settings name the primary; default L15 (7) until the lead adopts F3.
4. **The classifier as a named planted-menu diagnostic (R: C R8.4, VF-12).** Its predictions run over L15 (6)'s row-AUC grid like every diagnostic's; the quality is never fitted. Its c_d enters later as a point on the c_d/c0 curve, placed by its measured cost.
5. **τ_O.** Predictions at each τ_O ∈ {2, 5, 10} (R: ADD L15 (2)). If the user approves τ_O\* = 5 pp (C U-2; B E1), the record names it primary. That is text only.
6. **Reference note (I).** The Llama Gate B-lite note says REQ-16's "≥ 2 full-run seeds" pick may force "keep" on Llama's seed map, and asks for a check before the freeze (R: `llama-gate-b-lite-rules.md`:331). It is not a draft item; the lead may add it.
- **Tests.** A re-run reproduces `predictions.json`; c\* is the first crossing (R: ADD L15 (5)); both conventions and both placement statistics are present; the classifier row is present; units are stated. **Mutants:** one convention only; a fitted placement statistic; the classifier left out.

### W1-16. REQ-19: the limit checks [LEAD; U8 USER]

1. **Input allow-list (I, from A LQ40).** The settings list exactly the Gate A a0 units 1101–1103 at e1 and the untuned unit, with their paths and `COMPLETE.json`, `summary.json` and `query_loss.jsonl` SHA-256 (R: A §L.4 table). Any other unit refuses. No Gate B arm's O or task loss may be read before LQ38, LQ39 and the O error model are fixed (R: A LQ40).
2. **O counts.** Per unit "Refusal: Yes" of 100: 17 (untuned), 4, 6, 4 (a0 1101–1103) (R: A §L.1; CK-3 §4.2). Per-prompt flags come from each unit's eval `guard.jsonl`, kind "overrefusal", fields `prompt_id`, `refusal` and `valid` only, after `family_probe_reading.sealed` (R: `gate_a_overrefusal_counts.py`:1–5, :26–31).
3. **O MDE in two error models (R: B §E.2, §A.8; C R5b.1; CK-3 §4.5).** The 6-seed and 9-seed MDE of O(m) − O(θ0), two-sided 5%, 80% power: (a) prompts random (B §A.8's HB form: a seed part from the a0 seed SD plus a crossed prompt part from the 3 × 100 table); (b) seed only. Expected: about 11–12 pp and about 2.1 pp (1.6 at 9 seeds) (R: CK-3 §4.5, M there). Also report the 6-against-6 comparator contrast's MDE (I).
4. **The decider.** A settings key `u8_decider` names the error model fixed at K4. Default: prompts random (R: B E2; C R1.8, R5b.1). Under that default U8 opens (R: CK-3 §4.5).
5. **"f".** PLAN-S:197's "planning at f = 1" is not defined in the records (R: C R5b.1; CK-3 §4.1, which guesses "prompt fraction 1", I). The settings carry a required field with the lead's written definition. The script refuses if it is empty (C: "do not guess").
6. **NI planning report (R: B §E.3; C R1.1, R5b.2; report only).** P(declared feasible) for an arm at true excess 0 against θ0, at τ_O ∈ {2, 5, 10}, at 100 prompts (and 500 via N if O-ext is considered; RC-05), under the decider's error model and REQ-16's bound. Also the smallest τ_O with 80% NI power: 10.2 pp at 100 and 4.6 pp at 500 (R: C R5b.2, from CK-OR §5.3).
7. **τ_L exactly by ADD L16.** s = the sample SD (ddof 1), over seeds 1101–1103, of each unit's mean per-example query loss on all 200 task rows at e1; τ_L = 2√2·s; the 6-against-6 SE = s·√(1/3). **Known-answer check:** s = 0.002374850619448416, τ_L = 0.0067170919092681925, SE = 0.0013711206444236926 nats (R: A §L.4, TLC; M: τ_L and SE reproduced from s here). A mismatch stops with counts only (R: A LQ41).
8. **The 2-df record (R: ADD L16; corrected by S-12).** The 95% interval for σ/s is 0.5207–6.2847 and P(s < 0.5σ) = 0.2212 (M; ADD gives 0.52–6.28 and 0.22). ADD L16's "in that case about 12–24% of null arms fail the L screen" gives the rates at s = 0.5σ exactly, not given s < 0.5σ: at s = 0.5σ, 22% of null 6-against-6 arms fail under the R1.2 bound (13% under a one-sided 90% bound); averaged over s < 0.5σ, about 52% (40%); averaged over all s, about 14% (10%) (M: `review_stats_sim_out.txt` Part E, SE on 42 df). The rule does not change. τ_L is 2√6 ≈ 4.90 times the 6-against-6 SE when σ = s (M). Scope: only τ_L is frozen; the screen's SE comes from W1-13 row 3 (R: ADD L16; B V-13).
- **REQ changed.** REQ-19; REQ-21 (e), (h).
- **User decision.** U8 is the user's (R: BRIEF U8). The default if the user is silent at W1: F, the dev 100, with every O sentence "on these 100 prompts" (R: C U-3, VF-8; B E3). H reverses the user's "never from the hidden remainder" rule, so H is [USER] in any case and never a ladder default (R: C R5b.2; CONS UW-07b; RC-05). The 500-prompt ladder (dev 100 + 400 via N) is [USER-CONFIRM] (B §E.3; CONS UW-07a).
- **Tests.** Synthetic records with hand values (R: BRIEF REQ-19); both error models on a hand 3 × 10 table; the decider switch; an empty "f" refuses; a Gate B unit path refuses; the τ_L known answer passes and a changed s fails; ddof 1. **Mutants:** a one-sided α; τ_L without √2 (both in BRIEF); the prompt part dropped from model (a); the allow-list removed.

### W1-17. REQ-20: the manifest [LEAD]

- **Requirement (R: C R0.1, R0.2, §4).** Every new artifact gets an entry. A `conditional` flag carries the condition text of §1 item 6. Every listed item that is not built at W1 gets a `not_built` entry with its reason and the label "post-Gate-B exploratory". Each appended label is listed with `named_in: "registry, after the seal"` (R: ADD L13 (7)).
- **Tests (a temporary git repository).** A conditional entry passes; a conditional entry without its condition text refuses; a `not_built` entry without the label refuses; the brief's refusals stay.

### W1-18. Over-refusal checks on existing answers [LEAD] (run before U8 is decided, whatever the answer; RC-19)

- **Requirement (R: C R5b.3).** On the Mac, $0, one device for both sides: (1) the 128-token truncation check on the dev-100 greedy answers of the 11 recorded OLMo-2-1B units (bar: at least 97 of 100 flags agree per unit, and no unit's count moves by more than 2); (2) judge–lexicon agreement per unit and source; (3) partial refusals. These units are Gate A and development units only (R: C-VR §2 (d)).
- **Why it is not conditional (revision 2; RC-19).** Check (1) sets N's cost ($10–27 at a 128-token cap against $40–70 at 2,048; E: C U-3, from CK-OR §5.4), which the user needs to answer U8. Checks (2) and (3) also feed O reporting (R: C R5b.3, R5b.5). DRAFT §6.5 and CONS LW-05 run all three before U8 is decided. Revision 1 made them conditional on H or N.
- **Build now (default).** The Mac script (the lead runs it at $0, before U8 is decided). R5b.5's per-arm partial-refusal report is stage-1 reading code (S1); its rule text goes into REQ-21 (e) at W1.

### W1-19. REQ-26: O-ext H's counts-only sealed draw [USER] (default not built)

- **Rule in force.** No O-ext. If the user is silent at W1, F applies (R: BRIEF U8; C VF-8).
- **If the user changes the 8 Oct rule and picks H before W1 (R: C R5b.2; CONS UW-07b; RC-05).** A sealed, stratified draw of 400 prompts from the hidden over-refusal remainder (100 XSTest-safe, 300 OR-Bench-hard; 969 stay hidden; R/M: C R5b.2). The lead runs it, counts only, as the L9 precedent (R: ADD L9). The builder's tests use a synthetic hidden split; the builder never runs it on real data. Label `oext.h` (`stage1-oext-h-v1`, parts (source)), appended with the code.
- **If the user picks N.** A download that the user approves, plus a near-duplicate check against every bank (R: C R5b.2). The builder writes the check after the approval.

### G-1. Gap found while merging: R draws d = 9–12 for plan B [LEAD] (optional; I)

Plan B runs R at 12 seeds (R: PLAN-S:118), and B's seed layout D1 uses R 1101–1110 (R: B §A.6, §H A4). REQ-4 builds d = 6–8 only (R: BRIEF REQ-4). **The seed list is a W1 item (REQ-21 (d); DRAFT §1.3; CONS LW-31; RC-07):** A1, H1, S1 and S4 at 1102–1110; R 1101–1112 by the same frozen rule (`gate-b-random-removal-v1`, draw d at seed 1100 + d); a0 1101–1106. Building the d = 9–12 files at W1 is optional, because draws by the frozen builder are outcome-free whenever they are made (I). Building them now costs nothing and keeps every R draw in one commit. Tests: as REQ-4's (75 rows per unit; distinct by d).

### Text-only W1 items with S1 code (the builder builds nothing now)

SR, S6, B↓LR, SRJ, the prefill probe and its headroom reading, HB-4, in-domain refusal and V2a: each needs a conditional rule text in REQ-21 at W1 and code at S1 (R: C R0.1, VF-7, §4). Their label names appear in the text only. The registry entries come with their S1 code (R: C VF-5).

---

## 5. New labels for `labels.json` (append-only; T1 entries unchanged)

| Key | Label | Parts | Owning script | Item | Status |
|---|---|---|---|---|---|
| `a1_variants.ties` | `stage1-a1-variants-ties-v1` | (variant) | `scripts/stage1/report_a1_variants.py` | W1-04 | build (q, e1: BINDING; adam: LEAD) |
| `classifier.ties` | `stage1-classifier-ties-v1` | — | `scripts/stage1/score_classifier_rows.py` | W1-07 | build |
| `plant.auc_boot` | `stage1-plant-auc-boot-v1` | (scorer, comparison) | `scripts/stage1/report_plant_ranks.py` | W1-08 | build |
| `plant.decoy_rows` | `stage1-plant-decoy-rows-v1` | — | `scripts/stage1/build_plant.py` | W1-09 | build (K3) |
| `plant.decoy_unit` | `stage1-plant-decoy-unit-v1` | — | `scripts/stage1/build_plant.py` | W1-09 | build (K3) |
| `plant.decoy_leaf` | `stage1-plant-decoy-leaf-v1` | — | `scripts/stage1/build_plant.py` | W1-09 | build (K3) |
| `selector.seed_shift` | `stage1-selector-seed-shift-v1` | (replicate) | `scripts/stage1/selector/simulate.py` | W1-14 | build |
| `selector.hetero` | `stage1-selector-hetero-v1` | (replicate) | `scripts/stage1/selector/simulate.py` | W1-14 | build |
| `plant.extra_unit` | `stage1-plant-extra-unit-v1` | (location) | `scripts/stage1/build_plant.py` | W1-10 | only if F9 is adopted |
| `plant.extra_leaf` | `stage1-plant-extra-leaf-v1` | (location) | `scripts/stage1/build_plant.py` | W1-10 | only if F9 is adopted |
| `random_removal.rtok` | `stage1-random-removal-tok-v1` | (arm, d, g) | `scripts/stage1/build_r_tok.py` | W1-03 | only if LQ47 is amended |

**The decoy label form is open (RC-21).** Draft B §G F7 names one label, `stage1-plant-decoy-v1`; this table names three. The lead fixes one form before the append (labels are append-only and sealed; R: ADD L13 (7)). Recommended (I): the three labels above, one draw per label with one owner each, as the plant's own rows, unit and leaf labels are drawn.

**Named in the W1 text only; entries with their S1 code (R: C §4, VF-5):** `stage1-sr-k0-v1`, `stage1-sr-k-v1`, `stage1-s6-v1` (S6 alternative (a)), `stage1-oext-h-v1` (W1 if H is chosen), and V2a's split-half label (a name such as `stage1-v2a-split-v1`, I). REQ-21 (m) states that every label above was named after the seal and that no draw was computed before its commit (R: ADD L13 (7)).

**Checks the builder runs after each append (R: ADD L1, L13, §4 item 1).** The T1 entries are byte-identical; each settings file's `label_entries` still match; the golden A1 test passes; the scan finds no unused entry, no literal and no shared label.

---

## 6. The lead's REQ-21 text items (c), (e), (i) and (m)

The lead writes these, not the builder (R: BRIEF REQ-21). Each line says what the text must contain because of the drafts. The rule in force is named first.

### 6.1 (c) Labels, the "worse" family and the label order

1. **The four labels** are decided: better, equivalent, worse, inconclusive (R: FOCUS 8 Oct 18:31 UTC). "Better" is unchanged: the family rejects, and the point estimate is ≥ 5 pp (R: PLAN-S:115; B §B.5).
2. **The "worse" family for O and task loss (U4).** In force: the 18:31 UTC text, "significantly harmful at the 5% Holm level … each in its harmful direction" (R: FOCUS). The proposals:
   - A LQ43: two more Holm families of six, two-sided, each against the U contrast's comparator (R).
   - B §B.2: one closed graphical family Φ (24 nodes). It is [USER], because it changes "Holm over 6" (R: B §B.2, V-1). Silent default: Holm over P1–P6 as frozen; O and L as one-sided Holm families of six at 5% each, each in a per-contrast variance form (Welch under S-a, the HB form under HB; DRAFT §4.3; S-1); F as a fourth family only if τ_O\* is approved (RC-17 (c)); the paper states the false-"worse" rate: about 11% under the global null with equal variances, at most 15% by a union bound, and 9.4–12.8% with the add arms back near θ0's over-refusal (R: B §B.2, from CK-3 §3.2; DRAFT §4.3; S-11).
   - Sidedness differs: A is two-sided, B one-sided adverse. The lead records the reading in (h) [LEAD].
3. **The O and L "worse" rule.** In force: the 18:31 UTC rule. Proposal: C R1.3 / B §B.3 (adverse only if also NI-infeasible against θ0 at τ_O\* or against a0 at τ_L, and worse than the comparator) [USER] (C U-1). Fallback if the user is silent (C R1.5): the 18:31 rule stays primary, and R1.3 at τ_O\* = 5 pp is a pre-registered sensitivity label; a yes to R1.3 fixes τ_O\* = 5 pp for R1.3 whatever the τ_O\* question gets (RC-17 (a)). The user may switch until the earlier of S1 and the first read of any Gate B wave-1 arm's O or task loss; between that read and S1, only with a record of every Gate B O and L value read before it, as a disclosed deviation (S-2); never after S1 or after any **newly run** stage-1 cell is read; the reused a0 and R cells are already known (R: C VF-6; B §B.3 note).
4. **The order and the row (A LQ44; B §B.5) [LEAD].** The headline word: any "worse" first, naming the measure; then "better"; then "equivalent" with its grade; then "inconclusive". The full label row is always printed. Two equivalence grades: grade 1, per comparison (the frozen TOST); grade 2, familywise (the 98.33% interval) (R: B §B.4). **Revision 2 (DRAFT §4.5; S-9, S-10, RC-02, RC-32):** the steps are a partition: the coherence screen gives flags, not a word; "significant, below the SESOI" is added in the "equivalent" and "inconclusive" steps; a "worse (U)" contrast that is also equivalent prints both; a "worse (O)" or "worse (L)" word prints the U part beside it, for example "worse (L); U part: better". B16 (S1) implements it; no W1 build change.
5. **Coherence (B §F) [LEAD].** The Gate A bar (≤ 5% capped, ≤ 10% failing the frozen screen) applies to an arm's answers pooled over its seeds; a short-answer TOO CLOSE counts as a failure, as in G1 (R: B §F item 1). This departs from PREREG G1's per-run use; it applies to stage-1 labels only, and Gate B stays as frozen (R: B §F item 1, V-14). No arm or seed is dropped. **Revision 2 (RC-02; DRAFT §3.7 items 3–4):** a failing repair keeps the label that its tests give, and its headline word carries the flag "fails answers end"; the text never calls it better or equivalent without the flag. A failing comparator adds the flag "comparator fails answers end" to each contrast that uses it, and the tested label stays. **[USER] proposal (B §F items 3–4):** label a failing repair "worse (answers do not end)" and read a failing comparator's contrasts "inconclusive". Silent: the flag rule. Reason: the user's "worse" means a significantly harmful contrast at the 5% Holm level (R: FOCUS 8 Oct 18:31 UTC), and a screen failure is not one.
6. **Marking (A-RV R4; RC-13).** BRIEF lists U4 as a user decision (R: BRIEF:192). Draft A keeps LQ43–LQ44 [LEAD] under the 16 Oct instruction; the real precedent is the D5 entry and ADD line 7 (R: A-RV R4). Draft C recommends [USER] for R1.3 and R1.4 (R: C C-l). The lead may close U4 (the label order and the O and L Holm families, not Φ), U5 (keep, the approved default), U6 and U9 by recording in the W1 FOCUS entry that the 16 Oct instruction covers them, as the D5 entry did for U2 and U3 (R: FOCUS 'D5 DECIDED: (a)'; ADD line 7). Φ (FC-4) and R1.3 (FC-5) stay [USER] in any case (RC-13; one text in all three files). Otherwise U4 (LQ43–LQ44), U5, U6 (LQ42) and U9 are [USER] W1 items, with the proposals as defaults.

### 6.2 (e) The limits

1. **Decided:** O against θ0, with a0 reported; the τ_O grid {2, 5, 10} pp; τ_L = 2 SE of a seed-to-seed difference, fixed before W1 (R: FOCUS 8 Oct 13:53 UTC).
2. **τ_O\* = 5 pp as the primary bar** [USER] (C U-2; B E1). Silent default: no primary τ_O, and Φ's F nodes leave the family (R: B §B.2, V-1).
3. **Feasibility = an NI bound** against θ0 (O) and a0 (L): feasible, infeasible or undetermined at each grid point [LEAD] (R: C R1.1). The bound convention [LEAD] (§8 row 2). The O error model [LEAD, before REQ-19 runs] (§8 row 3).
4. **The binding sentence, corrected (A-RV R3; replaced in revision 2 by RC-04).** "On the point estimate τ_O binds only above 19, 22 or 27 of 100 (M: 17 + τ). With a seed-only SE (at least 1.53 pp; R: RV R3) a one-sided 90% bound adds about 2.0–2.3 pp (M: RV R3; 1.96 pp at z, M: `w1_extract_numbers.out`), and the upper end of the two-sided 90% interval adds about 2.5–3.1 pp (M: `review_fixes_numbers_out.txt`, z to t at 5 df). Under the prompts-random model in force for O (SE 4.0–4.2 pp at 100 prompts; M: CK-OR §4), the upper end of the two-sided 90% interval adds about 6.6–6.9 pp (M: `review_fixes_numbers_out.txt`, 1.645 × 4.0–4.2), so an arm at θ0's level is 'undetermined' at τ_O = 2 and 5 on 100 prompts." Revision 1's sentence used the seed-only SE, against the prompts-random model that all three files recommend for O. In A §N item 2, write "so it passes τ_O on the point estimate".
5. **REQ-19's outputs** (W1-16): the O MDE under both error models and the decider; then the U8 answer. Under prompts random U8 opens (R: CK-3 §4.5). The options: N [USER, a download], F; the ladder N → F is [USER-CONFIRM] (CONS UW-07a); H is a separate [USER] question, because it reverses the 8 Oct rule "never from the hidden remainder", and it is not a ladder default (CONS UW-07b; RC-05); silent → F (R: C U-3, VF-8; B §E.3).
6. **τ_L = 0.0067171 nats**, with the exact L16 rule, its scope sentence and the 2-df caveat (W1-16 items 7–8). LQ41: REQ-19's record must equal these numbers (R: A §L.4).
7. **The τ_L reference (A LQ38; B §E.4; C Q1, AMD-7).** In force: a0 (R: PLAN-S:124). A 600-row removal trains 33 steps, not 38 (R: C Q1), so every removal arm may fail τ_L by dose alone. L(m) − L(R) is reported beside L(m) − L(a0) for every removal arm. The choice goes to GPT before the W1 commit. A change of PLAN-S:124's reference goes to the user (I).
8. **The estimate compared with τ_L (A LQ39)** uses the same bound convention as O.
9. **Who has seen any task loss (A LQ40).** No writer of Drafts A, B or C read any Gate B arm's task loss (R: A §B; B §K.3; C §8). The authors of the Llama Gate B-lite note and the CONS writer did: the note used the OLMo R arms' task-loss differences over the same-seed a0 and their answers-end counts, and the CONS writer read the task-loss differences (R: CONS LW-07, LW-08 item 6; RC-03). By I these are the wave-0a R_1–R_3 units. This extract does not repeat them. Its first writer searched the stage-2 notes for W1, REQ and label lines only (§11) and states no read of these values; this revision's writer did not open the note. Also, the reused stage-1 cells a0 1101–1103 are Gate A units, and their task losses were read to compute τ_L (R: A §L.4; B §K.3). The record says both. The lead states its own reads. Then (m).
10. **The skill measure (U6):** held-out task loss on all 200 rows is the limit; ARC is report-only (R: PLAN-S:192–193; A LQ42). The marking question of 6.1 item 6 applies.
11. **Conditional and report-only items:** in-domain refusal (C R5b.4) [USER], conditional; partial refusals per arm, report (C R5b.5); selectivity, report only (C R1.6); C R1.7 rejects NI against the comparator; Gate B's Ref, G4 and HarmBench definitions are unchanged (R: C VF-14).

### 6.3 (i) Deviations the user sees, and SPEC F4 as a B+Qi risk

1. U7 (a)–(d), as in BRIEF:195 (R).
2. **Q-P1** (R: A §R.2.10): "B+Qi's erosion E lies nearer recipe B's than recipe G's. Basis: no warmup, β1 0.9, a constant peak LR, and a fit mostly done by step 2–3 (SPEC F4; QI FQ3)."
3. Plant cell sizes other than 150 and 37–38 are a PLAN-S deviation (R: ADD L12 (7)).
4. **New lines to show the user, if the lead adopts them [LEAD]:**
   - HB replaces PLAN-S:102's "seeds are not paired". It is a [USER] item (DRAFT FC-2; CONS UW-02; RC-01). If the user is silent, S-a stays primary and HB is a pre-registered sensitivity (R: B §A.10, V-1).
   - The arm-pooled coherence bar (6.1 item 5).
   - REQ-16's SE form, an edit of ADD L16 (B V-13), and REQ-17's ρ grid, an edit of ADD L15 (1) (B H A7).
   - F3 as the placement statistic, an edit of L15 (7) (B §G F3).
5. **Lines that stay [USER] questions, with the rule in force named:** Φ (in force: Holm over 6); R1.3 (in force: the 18:31 rule); τ_O\* (in force: no primary τ_O); D1, R_1108 → a0_1107 (in force: D0; R: B §A.6); δ_fam (in force: 5 pp absolute; R: B §C.3); F1, the wording of headline item (2), [USER] (C R8.5, VF-19; Draft B marks it [USER-CONFIRM], B §G F1) (in force: the 8 Oct wording); F10, a second plant (in force: none) [USER].

### 6.4 (m) The blinding line

**The brief's template sentence must change.** "This text uses no wave-0a or wave-0b value" (R: BRIEF REQ-21 (m)) is false now. FRE, the per-answer prices and REQ-17's cost model use the wave-0a ledgers (R: A §B, "Settings in this file that use a Gate B value"). Several choices were made after Gate B values were seen (below). T2 cannot be met as written (R: ADD §3 (4)).

The record must hold (each part cites its source):
1. **The seen Gate B values** (R: ADD §3 (4)): r_j, σ̂_gate, Gate B's P4 prediction (not stage-1 P4; RC-30), the P(LOCALIZED) lookup, the re-costing figures, and the sealed rankings, scores, picks and ρ values. Draft B adds SD(U(R_j)), the implied same-seed ρ and the per-answer coupling (R: B §K.3).
2. **Six of the 50 primary cells are reused units whose values were read:** a0 1101–1103 (Gate A) and R_1–R_3 (wave 0a, through r_j and Gate A) (R: B §K.3; B-VR §5.1 item 4).
3. **Per writer:** A §B's table, plus a row for A-RV (R: A-RV N6); rows for the Llama Gate B-lite note's authors (the OLMo R arms' task-loss differences and answers-end counts) and for the CONS writer (FOCUS 16 Oct entries; the R arms' task-loss differences) (R: CONS LW-07, LW-08 item 6; RC-03); rows for the two reviews of the merge and for this revision's writer (DRAFT §12.2); B §K.3's paragraph as written; C R0.3's three facts, including that one wave-0a R arm's aggregate counts, its over-refusal count among them, were printed in a check note and read by C's writers (R: C R0.3, VF-3); the builder's own list, including that it confirmed L3 after seeing the seal (R: ADD L3 (2)); the lead's own reads.
4. **Choices made after values were seen** (R: B §K.3; B-VR §5.1 item 6): HB over the approved unpaired model (its power case leans on the wave-0a ρ̂; HB is expected to read P4 about 0.3 pp more in S1's favour than S-a); REQ-17's ρ grid, proposed after the noise gate with values from PREREG §2; the O error model, fixed when the Gate A counts had already shown that prompts random opens O-ext; the arm-pooled coherence bar, after a0's screen rates were read; the withdrawn plan-A cut option.
5. **Labels and readings named after the seal:** every label of §5 and the T1 labels marked "registry, after the seal" (R: ADD L13 (7)); the plant R600/R150 parts reading (R: ADD §4 item 2).
6. **The T1 and K2 timing:** nobody read `rows.jsonl` before the T1 commit (R: ADD L1; FOCUS 16 Oct 13:21 UTC); whether W1-04's code was committed before the first real read (R: C VF-18).
7. **This extract's writer** read FOCUS's 16 Oct entries (the noise-gate values, the sealed rankings, picks and ρ, the re-costing figures) and Drafts A, B and C, which print the a0 and R_1–R_3 U values and the Gate A O counts. It also read T1's label keys and settings keys (no data) and the key names of one prepared row (no values). It read no CK-EM, no Gate B arm's O, task loss, ARC or answer, and no `rows.jsonl` or `groups.json`. **This revision's writer** (review fixes) read the two reviews, the three merge files and the source lines named in "Review fixes"; it saw the Gate B values of DRAFT §12.1 through those files, no Gate B arm's O, task loss, ARC or answer, no CK-EM and not the Llama note.

### 6.5 Other REQ-21 letters the drafts touch (pointers)

| Letter | What the drafts add |
|---|---|
| (a) | The title question (W1-02; PAPER decision 26) [USER-CONFIRM if the token-axis analysis does not count]; F1's headline wording [USER] (it changes the user's 8 Oct headline text; §6.3 item 5; DRAFT FC-11; RC-12); the status of OLMo-1B's stage 1 under the re-plan's option B [USER] (CONS UW-21; RC-11 (d)) |
| (b) | The token reports (W1-01, W1-02); the primary model (HB or S-a; HB-C to GPT, B §A.10); Φ or Holm (6.1); δ = 5 pp kept, about 11% of E (R: B §C.1) [LEAD]; the later families 1b, 1c and the testing order (B §B.6) |
| (d) | Seed layout D1 [USER]; the plan-B seed lists and plan-B statistics [LEAD] (G-1; CONS LW-31; RC-07, S-15); block A sealed until block B [LEAD] (CONS LW-35; S-3); HB's predicted MDE printed in the plan-A/B record (B H A5) [LEAD], with S-a's values at ρ ∈ {0, 0.67, 0.76} (S-7); for reference, the 7–8B draft asks for the same paired-scale choice at 1B before W1 (R: `78b-preregistration-DRAFT.md`:156, :386) |
| (f) | The token reports; the add-on reports (W1-05, W1-06); HB-1 to HB-3; the SRJ rule and its readings (C R5a.1, R5a.3, R5a.5; VF-25) |
| (g) | Every conditional rule text (C R0.1; §4 text-only items); the decoy (W1-09); the classifier scored only (W1-07); V1 (W1-04); R_tok if adopted |
| (h) | Readings: the bound convention; "f"; the token axis; Φ sidedness; the H2a rule's departure from "at least one line" (R: ADD L6); SR's and S6's deviation tables (C R4.4); A1's justification (C R7.1); C-lean's contents (a) (RC-09); PLAN-S:76 with PLAN-S:232 for block A (S-3); PLAN-S:239 for conditional items (RC-28) |
| (j) | `predictions.json` by SHA-256; C R8.3's classifier prediction; B F2's construction checks named as checks, not predictions |
| (l) | §7's list |

---

## 7. Not built before W1 (REQ-21 (l); REQ-20 `not_built`), unless the lead or the user decides otherwise

| Item | Reason | Label if added later |
|---|---|---|
| R_tok (W1-03) | ADD §5 item 1: no new arm; [USER] (new arms and money) | post-Gate-B exploratory |
| F9 two more plant locations (W1-10), if not adopted | [USER-CONFIRM]; 1b funding | post-Gate-B exploratory (F6 replay stands) |
| F10 benign-topic plant | [USER]; new text or a download; a target change (B §G F10; C U-12) | post-Gate-B exploratory |
| O-ext H draw (W1-19) or N's check | [USER]; F in force | post-Gate-B exploratory |
| The prompt-only classifier score (C R8.6) | [USER] | post-Gate-B exploratory |
| REQ-12 DataShield-style, REQ-13 Self-Inf-N-style, if usage is short | FOCUS 9 Oct 19:37 UTC item (9) | post-Gate-B exploratory (recorded before W1) |
| The sweep's "attribution score along a safety direction" | ADD §5 item 3: not pre-registered | post-Gate-B exploratory |

---

## 8. Conflicts the builder must not settle (it builds a switch; the default is the rule in force or the lead's ruling)

| # | Question | Options | Builder default | Who decides |
|---|---|---|---|---|
| 1 | Primary analysis model | S-a (PLAN-S:102) / HB (B) / HB-C (B-VR) | no W1 builder impact (B16 is S1); REQ-17's shared shift sits behind the row-6 switch | the user (DRAFT FC-2; CONS UW-02; RC-01); HB or HB-C goes to GPT only if the user adopts pairing (B H A9) |
| 2 | "Upper 90%" | one-sided 90% (A) / one-sided 95% (B, C) | 0.95 | [LEAD] |
| 3 | O error model | prompts random (B, C) / bank-conditional (CK-3; A LQ36) | prompts random | [LEAD], before REQ-19 runs (K4) |
| 4 | Screen SE form | pooled residuals (ADD L16) / HB form (B) | ADD L16 if there is no ruling at K5 | [LEAD] |
| 5 | τ_L reference | a0 (PLAN-S:124) / dose-matched R | a0; R reported beside | GPT; the user if PLAN-S changes |
| 6 | REQ-17 coupling | independent (L15 (1)) / ρ ∈ {0, 0.67} (B) | ρ grid {0} (= L15 (1), in force); {0, 0.67} behind a switch; the rule chosen by L15 (1)'s criterion; the ρ average only with A7 (RC-18) | [LEAD] (A7, W1-P) |
| 7 | Planted placement | top-k hit (L15 (7)) / row AUC (B F3) | both computed; L15 (7) primary until adopted | [LEAD] |
| 8 | Token axis | total row tokens / target tokens | total row tokens; target as a sensitivity | [LEAD] (REQ-21 (h)) |
| 9 | "Worse" O/L rule and family | 18:31 + Holm (in force) / A LQ43 / B Φ / C R1.3 | none at W1 (B16 is S1) | [USER] for Φ and R1.3 |

---

## 9. Draft A's re-verify items (R1–R14) and where each lands

| Item | Fix (R: A-RV) | Touches W1? | Where it lands |
|---|---|---|---|
| R1 | cite `runner.py`:627, not :625; delete Fix-log item (6) | yes (C-full's stage list feeds REQ-17's cost model) | the W1 record's cost-model citation; A §C.4 |
| R2 | name the engine in R.0.7's failure path (X′ after the merge) | no (S1) | the S1 text, inside LQ4 |
| R3 | τ_O binds about 2 pp lower under the bound | yes | 6.2 item 4 |
| R4 | the precedent for keeping U4 and U6 [LEAD] is the D5 entry and ADD line 7 | yes | 6.1 item 6; 6.2 item 10 |
| R5 | LQ30 (ii) also seals its evaluation files | no (S1) | the S1 text, inside LQ30 |
| R6 | $4.9 → $4.8; $2.7–2.9 → $2.7–2.8 | no (S1 money) | A §R.1.3, §R.1.10, §R.2.7, §R.2.11, §C.9, §Q.2 |
| R7 | 330–370 s → 330–371 s | yes (REQ-17 cost input) | W1-14 item 7 |
| R8 | LQ47 is W1; add it to §C's heading exceptions | yes | W1-02 |
| R9 | HEAD moved (now `3db753e`) | text | the merged record's source table |
| R10 | the clock count (three checks, not four) | no | the A header |
| R11 | full FOCUS line spans, or "lines of the cited items" | no | the A key table |
| R12 | define SS or drop it | no | A §R.1.4 |
| R13 | "(needs B17)" applies to both LQ30 options | no (S1) | A §Q.2 |
| R14 | UQ7: "the options in BRIEF's D5-7 row for (b) and (c)" | no (S1) | A UQ7 |
| N1 | LQ25, LQ26 and LQ28 are W1-P | yes | W1-15 item 2 |
| N2 | the title depends on LQ47's ruling | yes | W1-02 |
| N4 | c0 (b) ≈ $0.24 is below PLAN-S's $0.3–0.6 (a check) | yes (c0's definition) | REQ-21 (k) note |
| N6 | add an RV row to the blinding table | yes | 6.4 item 3 |

---

## 10. Weak assumptions, decisive checks and open concerns

1. **The engine accepts 48 identical add rows** (S6). UNVERIFIED. Check: W1-12's `parse_edit` test.
2. **The attribution pass can score rows outside its corpus** (the decoy for A1). UNVERIFIED (R: CK-11 F7). Default: report "not done".
3. **REQ-6 already holds the PKU `line` and companion index.** UNVERIFIED (R: C §8). W1-11 adds them in any case.
4. **T1's A1 checks can be imported read-only** (`check_attributes_unit`, R: `write_score_edit.py`:59). The T1 files are chmod a-w, which allows import (I). If an import side effect blocks it, W1-04 re-implements the checks, and the cross-test is the safeguard (I).
5. **H1's token-matched reading rests on an unmeasured segment** of the dose curve (W1-02 item 5). Counterexample (I): if random removal restores nothing below 600 rows (the loss plateaus by step 2–3; R: FOCUS 8 Oct 15:59 UTC item (5)), the line from (0, 0) to R_600 overstates G_R(T_H1) and understates H1's Λ_tok. Only R_tok_H1 measures it (W1-03).
6. **The selector's true L effects default to 0** (R: ADD L15 (2)). But every 600-row removal option trains 33 steps, not 38, so its true L effect against a0 may not be 0 (R: C Q1; A LQ38). Under the a0 reference the screen may then be optimistic for removal options. Proposal (I): a sensitivity with every removal option at a +1 τ_L true L effect, report only; the lead decides (DRAFT §7.4 lists it as a REQ-17 sub-question). Some writers of W1 inputs saw the OLMo R arms' task-loss differences (CONS LW-07; RC-03), so the size of this sensitivity must not come from them.
7. **The method menu crosses B's design clusters.** It holds keep, R, A1, L1, H1, S1, S3 and S4. If GPT rules HB-C (B H A9), one shared seed shift in REQ-17 is the wrong model for that menu. Then a two-cluster shift would be the matching sensitivity (I). The category menu (eight 600-row removals) is one cluster, so it is not affected.
8. **The U–O correlation rests on 3 Gate A seeds** (BRIEF REQ-17). It is close to no information (I). Proposal (I): fix it to a small grid in the settings, for example {0, 0.5}, as a sensitivity. This is a new design element, so it needs the lead.
9. **The T1 bundle is not committed** in the main checkout (R: `git log` at 00:41 UTC). The hashes here are the workspace's, read between 00:26 and 00:41 UTC. The T1 commit's hashes govern.
10. **The REPLAN dates (27 Oct, 3 Nov) come from a proposal** that is not adopted (R: Drafts B and C cite REPLAN §5). The K-checkpoints do not depend on them.
11. **Load (I).** Fifteen of the twenty items are small. The largest are W1-07 (a Part C script and its fake-guard tests), W1-14 and W1-15 (inside the selector build) and W1-08. C R0.2's rule protects wave 1: an item that is not ready goes to REQ-21 (l), except REQ-23.

---

## 11. Process record

**Read (main checkout, read-only).** BRIEF (all); ADD (all); A (all); A-RV (all); B (all); B-VR (all); C (all); C-VR (all); CK-3 §4–§5; CK-11 §4 (headings and F1–F10); FOCUS lines 1–90, 120–130, 212–218, 236–258; PLAN-S lines 100–132, 155–182, 195–205; the stage-2 and 7–8B notes (a Python search for W1, REQ and label lines only); PAPER, SWEEP and the mock reviews (a Python search for token-matching lines only); T1's label keys, owners and parts, and its settings keys and scorer entries (no data); `s1common.py` (function list, `PreparedView`, `sealed_record`); `write_score_edit.py` (function list and its tie-label lines); `gate_a_overrefusal_counts.py` header; `scripts/gate_c_classifier.py` header; the engine's `prompt_tokens` and `target_tokens` definitions; the key names of one row of P's `engine/train_rows.jsonl` (no values printed). I did not read PREREG, SPEC, RS, CK-EM, CK-OR or CK-TM in full.

**Commands run (all exit 0 unless stated).**
- `date -u` (00:26, 00:37, 00:41, 00:47 UTC); `git branch --show-current`, `git log`, `git rev-parse`, `git status --porcelain` (main checkout, read-only).
- `ls`, `wc`, `sed -n`, `grep` over the sources above. One `grep -o` with a long pattern failed with a ugrep "exceeds complexity limits" error; I re-ran the search in `python3 -I`.
- `python3 -I` one-liners: the T1 label registry (keys, labels, parts, owners, `named_in`), the T1 writer settings (keys, scorers, label entries), and one prepared row's key names.
- `shasum -a 256` of every cited source and of the T1 files.
- `python3 -I w1_extract_numbers.py > w1_extract_numbers.out` (twice; the second run after adding the τ_O bound offsets).

**Files written (this folder only).** `w1-builder-extract.md` (this file); `w1_extract_numbers.py` (SHA-256 `3693369433143dce…`) and its output `w1_extract_numbers.out` (`d62a12c682eea41f…`). I did not change any draft, record or repository file.

**Acceptance against the task.**
- Passed: each item gives the requirement, the REQ it changes, its mark, the user dependency with a build default, and its tests (§3, §4); REQ-17's noise model (W1-14), REQ-18's c0 and C-lean (W1-15), REQ-19's limits (W1-16); REQ-21 (c), (e), (i), (m) (§6); the token-axis dose (W1-02), the score-stability report (W1-04), the add-on reports (W1-05, W1-06); new labels (§5); new edit builders (W1-03, W1-09, W1-10, G-1). Draft A's R1–R14 are mapped (§9). Numbers carry R, M, E or I labels.
- Not tested: no code was written or run for any REQ; every test above is a specification. The real-data runs are the lead's.
- Unresolved: §8 rows 1–9 and §10 items 5–8.

---

## Review fixes (revision 2)

**What this is.** `review-consistency.md` (RC-01 to RC-35) reviewed this extract beside the pre-registration DRAFT and the decisions list (CONS). `review-statistics.md` (S-1 to S-26) reviewed only the DRAFT; where the same rule sits here, its accepted fixes are carried. Each finding was checked against the sources first (the DRAFT's "Review fixes" section lists the source checks). Nothing here changes a frozen Gate B/C rule, a sealed ranking, D5 = (a) or a user decision in FOCUS. The builder defaults stay "the rule in force" (§0 item 4).

- **Written** 2026-10-17 from 01:20 to about 01:55 UTC by an Opus worker (clock checked with `date -u` at 01:20, 01:27, 01:31 and 01:48 UTC). Main checkout HEAD `5957a37`.
- **Numbers.** New M values come from `review_fixes_numbers.py` (output `review_fixes_numbers_out.txt`) or the review scripts' outputs. `w1_extract_numbers.py` and `.out` are unchanged (their SHA-256s in §11 still hold), so RC-04's "add the two prompts-random offsets to the EXTR script" is met by the new script instead, to leave the first writer's evidence file as it was.

| Finding | Status here | Where |
|---|---|---|
| RC-01 | applied | §6.3 item 4; §8 row 1 |
| RC-02 | applied | §6.1 items 4–5 |
| RC-03 | applied | §6.2 item 9; §6.4 item 3; §10 item 6 |
| RC-04 | applied (changed: the two seed-only ranges are given apart) | §6.2 item 4 |
| RC-05 | applied ("500 via N"; H is a separate USER question); also §6.2 item 5 and W1-16's "User decision", which carried the same H → N → F ladder | W1-14 item 5; W1-16 item 6 and "User decision"; W1-19; §6.2 item 5 |
| RC-07 | applied | G-1; register |
| RC-08 | applied | W1-15 item 2 |
| RC-09 | applied | W1-14 item 7; W1-15 item 2 |
| RC-12 | applied | §6.5 row (a) |
| RC-13 | applied | §6.1 item 6 |
| RC-14 | applied: W1-03 is [USER] (new arms and money) | W1-03; register; §0 item 7; §7 |
| RC-15 | applied | §1 item 6 |
| RC-17 (a), (c) | applied | §6.1 items 2–3 |
| RC-18 | applied | W1-14 items 1 and 4, tests; §8 row 6; §0 item 4 |
| RC-19 | applied | W1-18; register; §7 (row removed) |
| RC-20 | applied | W1-07; register |
| RC-21 | applied (the lead picks one form; this file's three labels recommended) | §5 |
| RC-25 | applied | §0 item 1 |
| RC-28 | applied | §1 item 6; §6.5 row (h) |
| RC-30 | applied | §6.4 item 1 |
| RC-33 | applied | W1-02 "User decision" |
| other RC items | DRAFT or CONS only | — |
| S-1, S-11 | carried | §6.1 item 2 |
| S-2, S-10 (window) | carried | §6.1 item 3 |
| S-9, S-10 (headline), with RC-02 and RC-32 | carried (pointer to DRAFT §4.5) | §6.1 item 4 |
| S-3, S-7, S-15 | carried (rule-text pointers) | §6.5 row (d) |
| S-12 | carried | W1-16 item 8 |
| other S items | DRAFT only; none changes a W1 build item here | — |

**Rejected here.** None. The parts of the statistics review that were rejected (S-9 steps 0a–0b, S-11's 12.5% as an exact bound, part of S-19) do not touch this extract.

**Builder impact of revision 2 (I).** No new build item. Two defaults change: REQ-17's ρ grid defaults to {0} with {0, 0.67} behind a switch (W1-14), and W1-18's Mac script is built and run before U8 whatever the answer. W1-03 stays not built. The block-A seal (S-3) is rule text for REQ-21 now and a stage-1 kit item (B15) at S1.

**Commands and files.** As listed in the DRAFT's "Review fixes" section. This file was edited by `python3 -I` exact-string replacements, each checked to match once.
