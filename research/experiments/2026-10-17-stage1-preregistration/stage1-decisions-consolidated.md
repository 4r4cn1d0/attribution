# Stage-1 decisions: one consolidated list (DRAFT for the main-study lead; revision 2)

**Status.** DRAFT for the main-study lead (General Implementation VI). It adopts nothing. It authorizes no run, spend, download, commit or agreement. It changes no frozen Gate B or Gate C rule, no sealed ranking, not D5 = (a), and no user decision recorded in FOCUS. Where a draft proposes to change a user decision, the item stays USER and the current rule stays in force until the user decides.

**Written** 2026-10-17 from about 00:30 to 00:55 UTC (17 Oct IST; clock checked with `date -u` at 00:30, 00:40, 00:46 and 00:54 UTC) by an Opus worker. **Revision 2** (from 01:20 UTC; clock checked with `date -u` at 01:20, 01:27 and 01:31 UTC) applies the checked fixes of `review-consistency.md` (RC-01 to RC-35) and, where the same text sits here, of `review-statistics.md` (S-1 to S-26), by another Opus worker. The section "Review fixes" at the end lists each change and each rejection. Item ids stay; new items take new ids, and a moved item leaves a pointer. Read-only on the repository. The only file written is this one. The folder also holds other workers' files (`w1_extract_numbers.py` and `.out`, `w1-builder-extract.md`, `stage1-preregistration-DRAFT.md`). I did not change them, and I read only `w1_extract_numbers.*`.

**Data rules kept.** I opened no `selector.jsonl`, no `hidden/`, no held-out file, and no wave-0b `rows.jsonl` or `groups.json`. I did not open `rankings-SEALED.json` (I computed its SHA-256 only). This file holds no row, prompt, answer, anchor or lexicon text. §10 lists the Gate B values that I saw while reading the sources.

## How to read this list

- **Labels for numbers.** **R** = read in a source (the source follows). **M** = measured or computed from records, or by me (the source or "this list" follows). **E** = an estimate (the basis follows). **I** = inference or judgement. A number inside a cited rule takes that rule's source as its R label.
- **Who decides.** **USER** = the user decides: it changes a user decision or a frozen input, costs new money that no approved plan holds, needs a download or an agreement, or changes a scientific target. **USER-CONFIRM** = the recommended default is an "ambitious default with a pre-set fallback" ladder. It rests on the user's relayed standing rule ("keep the more ambitious one always but always open to fallbacks"). The lead's chat has not confirmed that rule (UW-01). Until it does, treat each USER-CONFIRM item as a USER question, with the default as the recommendation and the fallback as the answer if the user is silent. **LEAD** = the lead decides. "After GPT" marks a consequential trade-off that the lead raises to GPT first.
- **Deadlines.** **W1** = before Gate B wave 1 (it enters the W1 record, REQ-20 and REQ-21). **W1-P** = W1, and before REQ-18's predictions are frozen. **S1** = before the stage-1 freeze. **Later** = after S1 (the next paper revision, the 7–8B pre-registration, or stage 2). The latest starts "27 Oct" (W1) and "3 Nov" (S1 block A) come from the re-plan PROPOSAL §5, which is not adopted (I: planning dates only).
- **Order.** §1 USER and USER-CONFIRM items due at W1 or W1-P. §2 LEAD items due at W1 or W1-P. §3 USER and USER-CONFIRM items due at S1. §4 LEAD items due at S1. §5 later items (all classes).
- **Ids.** UW = user, W1. LW = lead, W1. US = user, S1. LS = lead, S1. LA = later. Each item names its source items, so the same question asked in two drafts is one item here.

**Source short names** (main checkout `/Users/spiderishi/Coding/attribution`, branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD `3db753e` at 00:30 UTC; SHA-256 prefixes: M, `shasum -a 256` at 00:30 UTC). Line numbers are at these hashes. **At revision 2 (RC-29):** HEAD is `5957a37`. It adds one FOCUS line (the entry "BACKUP: the Mac-only model weights and states …", 17 Oct 01:05 UTC) at line 74 and changes no other source here (R: `git diff 3db753e 5957a37 --stat`). FOCUS's SHA-256 is now `1587b549813792e1`. So every "FOCUS:NN" pointer here with NN ≥ 74 is at `23e3da8f…`; at `1587b549…` add 1. The records should cite FOCUS entries by title (ADD §3 (3)).

| Name | File | SHA-256 prefix |
|---|---|---|
| FOCUS | `research/FOCUS.md` | `23e3da8f893e8135` |
| PLAN-S | `research/review/2026-10-08-sharpened-direction-DRAFT.md` (approved 8 Oct as the basis of the stage-1 pre-registration) | `6ff3ff2b15bc4295` |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md`, revision 5, frozen | `5c97cce78cfad2c1` |
| W0 | `research/experiments/2026-10-16-gate-b-wave0-outputs/` (sealed rankings `rankings-SEALED.json`, not opened) | `d6d5cd6bc1dc660c` |
| BRIEF | `.ai/briefs/stage1-commitments-build-20261016.md`, revision 1 | `12cbf46318728d32` |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` (§1–§5, binding) | `114776482a3287dd` |
| A | Draft A: `research/experiments/2026-10-17-stage1-prereg-references/stage1-prereg-references-DRAFT.md`, revision 2 | `5835caaea2204674` |
| A-RV | Draft A's `reverify-report.md` (R1–R14 open; applied here, §8) | `b61e86756f0207c3` |
| B | Draft B: `research/experiments/2026-10-17-stage1-analysis-model/stage1-analysis-model-DRAFT.md`, revision 2 | `c8cd8eabd4302ecf` |
| B-VR | Draft B's `verify-report.md` (applied in B revision 2; V-3 open to GPT) | `8126a089751da486` |
| B-CK2, B-CK3, B-CK11 | Draft B's check notes `check-W2-W5.md`, `check-W3-W4-W12-W13.md`, `check-W11-other.md` | `50c28526…`, `792b7be7…`, `0e424ceb…` |
| C | Draft C: `research/experiments/2026-10-17-stage1-review-b-rulings/review-b-rulings-DRAFT.md` (verified; VF tags applied) | `79d49e929a28bde2` |
| C-VR | Draft C's `verify-report.md` | `6fc384fee400cb73` |
| C-OR, C-TM, C-EM | Draft C's check notes `check-overrefusal-endpoints.md`, `check-threat-model-add-repairs.md`, `check-endpoints-anchors-models.md` | `a6db155c…`, `30a219d4…`, `739b74af…` |
| MRA, MRB | `writing/paper/2026-10-17-mock-review-A-methods.md`, `…-B-safety.md` | `ff0e4382…`, `4dfab435…` |
| SWEEP | `writing/paper/2026-10-17-lit-sweep.md` | `3c19fc11…` |
| REPLAN | `writing/paper/2026-10-17-icml-replan-PROPOSAL.md` (a proposal, not adopted) | `e8768298…` |
| PAPER | `writing/paper/2026-10-08-icml-draft.md`, revision 6 (decisions list :213–:245) | `024942b54a6242dd` |
| LLB, ALP, HR | `research/review/2026-10-17-stage2-design-notes/`: `llama-gate-b-lite-rules.md`, `alpaca-design-note.md`, `second-rater-and-human-label-check.md` | `4f1cff0b…`, `9e8b349c…`, `29b781eb…` |
| Y, P78, KCR, XL | `research/review/2026-10-17-icml-78b-prep/`: `engine-round-Y-design.md`, `78b-preregistration-DRAFT.md`, `78b-kit-cap-rule.md`, `32b-70b-design.md` | `63e83bc1…`, `e6a73c92…`, `9884bd17…`, `2ba8426c…` |

SS = `experiments/safety_selection/` (A-RV R12). θ0 = the untuned model. FRE = one full run equivalent.

---

## 0. Counts and index

**Counts by class (M: this list, revision 2; recounted after RC-05, RC-07, RC-11, RC-12, RC-14 and S-3).**

| Class | Due W1 | of which W1-P | Due S1 | Later | Total |
|---|---|---|---|---|---|
| USER | 20 | 0 | 17 | 11 | **48** |
| of which with a USER-CONFIRM ladder (marked "USER (ladder USER-CONFIRM)") | 1 | 0 | 5 | 1 | **7** |
| USER-CONFIRM | 2 | 0 | 1 | 1 | **4** |
| LEAD | 35 | 6 | 23 | 3 | **61** |
| **All** | **57** | **6** | **41** | **15** | **113** |

Revision 1 counted 104 items (USER 38, USER-CONFIRM 12, LEAD 54). The changes: UW-07 split into UW-07a and UW-07b (RC-05); LA-11 moved to UW-20 and LA-09's status part to UW-21 (RC-11); six RB items now read "USER (ladder USER-CONFIRM)" as RB marks them, and UW-16 reads USER (RC-12; LA-04 by the same rule, an extension here); LW-31 to LW-35, LS-22 and LS-23 are new (RC-07, RC-14, S-3). Items that rest on the relayed rule: the 4 USER-CONFIRM items plus the 7 ladders = 11.

Closed items that I checked and do not count are in §6. Items that I left out as outside stage 1 are in §9.

**Index.**

| Id | Item | Class | Deadline |
|---|---|---|---|
| UW-01 | Confirm the relayed standing rule | USER | W1 |
| UW-02 | The primary variance model (HB against the approved unpaired analysis) | USER | W1 |
| UW-03 | Seed layout D1 (R_1108 → a0_1107) | USER | W1 |
| UW-04 | The testing family (Φ, or Holm plus O and L families; BRIEF U4) | USER | W1 |
| UW-05 | The "worse" rule for O and task loss (R1.3) | USER | W1 |
| UW-06 | One primary over-refusal bar τ_O\* = 5 pp | USER | W1 |
| UW-07a | O-ext from N or F (BRIEF U8) | USER (ladder USER-CONFIRM) | W1 (answer); S1 (runs) |
| UW-07b | Allow H, a draw from the hidden remainder (reverses an 8 Oct rule) | USER | W1 |
| UW-08 | The label order (BRIEF U4) | USER | W1 |
| UW-09 | The skill measure (BRIEF U6) | USER | W1 |
| UW-10 | H1 under recipe bt (BRIEF U5, E6) | USER | W1 |
| UW-11 | The deviations the user should see (BRIEF U7) | USER | W1 |
| UW-12 | The reading of "frozen once" (BRIEF U9) | USER | W1 |
| UW-13 | The margin for other families (δ_fam) | USER | W1 |
| UW-14 | The title word "Compute-Matched" (PAPER decision 26) | USER-CONFIRM | W1 |
| UW-15 | The wording of headline item (2) (F1) | USER | W1 |
| UW-16 | A second, benign-topic plant (F10) | USER | W1 (before the T1 commit) |
| UW-17 | A prompt-only classifier score (R8.6) | USER | W1 |
| UW-18 | An exception for REQ-23, only if it is late (U-19) | USER | W1 |
| UW-19 | Freeze the Llama Gate B-lite rules with the W1 record (LLB U0–U8) | USER | W1 |
| UW-20 | Two more plant locations (F9; was LA-11) | USER-CONFIRM | W1 (rule); stage 1b (funding) |
| UW-21 | The status of OLMo-1B's stage 1 under the re-plan's option B (was part of LA-09) | USER | W1; at the latest S1 |
| LW-01 | HB or HB-C | LEAD (after GPT) | W1 |
| LW-02 | Analysis-model details A2, A3, A5, B3, C1 | LEAD | W1 |
| LW-03 | The error model for O (conflict C-i) | LEAD | W1, before REQ-19 runs |
| LW-04 | Run REQ-19 and record its outputs | LEAD | W1 |
| LW-05 | Three $0 checks on existing answers | LEAD | W1 |
| LW-06 | The feasibility estimator and one bound convention | LEAD | W1 |
| LW-07 | The comparator for τ_L | LEAD (after GPT) | W1 |
| LW-08 | The blinding line, REQ-21 (m) | LEAD | W1 |
| LW-09 | Arms that fail the coherence screen | LEAD | W1 |
| LW-10 | The plant's analysis rules and wording | LEAD | W1 |
| LW-11 | The placement statistic for planted menus (C-k) | LEAD | W1-P |
| LW-12 | Additions to REQ-17's settings | LEAD | W1-P |
| LW-13 | The SE inside REQ-16's screen | LEAD | W1-P |
| LW-14 | How REQ-18's predictions are scored; Llama's replay | LEAD | W1-P |
| LW-15 | The contents of C-lean (LQ27) | LEAD | W1-P |
| LW-16 | The cost-unit definitions | LEAD | W1-P |
| LW-17 | The token-matching ruling (LQ47) | LEAD | W1 |
| LW-18 | Build REQ-12 and REQ-13 before wave 1? (BRIEF U2) | LEAD | W1 |
| LW-19 | How candidate additions enter the W1 record | LEAD | W1 |
| LW-20 | Build REQ-23 (per-row content-classifier scorer) | LEAD | W1 |
| LW-21 | A1's justification and the scored-only variants V1, V2a | LEAD | W1 |
| LW-22 | What must land before the T1 commit | LEAD | W1 (now) |
| LW-23 | HarmBench rules HB-1 to HB-3 | LEAD | W1 |
| LW-24 | Other report-only endpoint rules | LEAD | W1 |
| LW-25 | SR and S6 construction details (conditional) | LEAD | W1 |
| LW-26 | Texts the W1 record must carry | LEAD | W1 |
| LW-27 | Engine round Y: build it now in a workspace? | LEAD | W1 |
| LW-28 | Who builds B10–B17 and Y | LEAD | W1 / S1 |
| LW-29 | Model-agnostic Part C scripts: when? | LEAD | W1 |
| LW-30 | A W1 paragraph for the human label check | LEAD | W1 |
| LW-31 | Plan-B seed lists and plan-B statistics | LEAD | W1 |
| LW-32 | Reuse of R_4 and R_5 if Gate B's extension runs them | LEAD | W1 |
| LW-33 | S-a's prompt term for O against θ0 (its exact form) | LEAD | W1 |
| LW-34 | REQ-21's record file name | LEAD | W1 |
| LW-35 | Block A stays sealed until block B | LEAD | W1 |
| US-01 | References on all six a0 seeds (B's package) | USER-CONFIRM | S1 |
| US-02 | References in block A or block B (UQ8) | USER | S1 |
| US-03 | A second Safe LoRA point (UQ9) | USER | S1 |
| US-04 | The base-model download for Safe LoRA (UQ1) | USER | S1 |
| US-05 | B+Qi's form (UQ3) | USER | S1 |
| US-06 | Candidate new references (UQ7, U-11) | USER | S1 |
| US-07 | Stage 1's funding event and the freeze | USER | S1 |
| US-08 | Certification pods before a funding event | USER | S1 |
| US-09 | What the confirmation units read | USER | S1 |
| US-10 | SR and S6 add arms (U-6) | USER (package USER-CONFIRM); option (b) USER at W1 | S1 |
| US-11 | B↓LR as a sixth reference (U-5) | USER (ladder USER-CONFIRM) | S1 |
| US-12 | In-domain refusal (U-4) | USER (ladder USER-CONFIRM) | S1 |
| US-13 | Access and download for the StrongREJECT evaluator (U-7) | USER | S1 |
| US-14 | The prefill probe (U-8) | USER (scope USER-CONFIRM) | S1 |
| US-15 | HarmBench's test classifier (U-9) | USER (ladder USER-CONFIRM) | S1 |
| US-16 | V2a's spend (U-10) | USER | S1 |
| US-17 | A norm-matched control for Safe LoRA (UQ6) | USER | S1 |
| US-18 | If the B+Qi engine change is late | USER | S1 |
| LS-01 | The engine round for B+Qi and its merge point | LEAD | S1 |
| LS-02 | What the engine certificate checks | LEAD | S1 |
| LS-03 | Which runs use the new engine | LEAD | S1 |
| LS-04 | Regenerated a0 adapters: acceptance and failure path | LEAD | S1 |
| LS-05 | How references are read | LEAD | S1; rule text W1 (S-2) |
| LS-06 | The rule "a data repair beats a reference" | LEAD | S1; rule text W1 (S-2) |
| LS-07 | Safe LoRA's settings | LEAD | S1 |
| LS-08 | "Reproduce exactly" for B10's certification | LEAD | S1 |
| LS-09 | B+Qi's settings | LEAD | S1 |
| LS-10 | B+Qi's binding check | LEAD | S1 |
| LS-11 | B+Qi's seeds | LEAD | S1 |
| LS-12 | Four jobs per pod in stage 1 | LEAD | S1 |
| LS-13 | Charging rules | LEAD | S1 |
| LS-14 | "Agree" between the cost conventions; the cost sentences | LEAD | S1 |
| LS-15 | The c0 job | LEAD | S1 |
| LS-16 | Record corrections (LQ23) | LEAD | S1 |
| LS-17 | The actor column and the per-actor report | LEAD | S1; "too close to call" rule text W1 (S-2) |
| LS-18 | The confirmation rules and the hidden subsample | LEAD | S1; pick rule and "confirmed" text W1 (S-2) |
| LS-19 | The overlap control's test | LEAD | S1; rule text W1 (S-2, S-25) |
| LS-20 | Human-check add-ons | LEAD | S1 |
| LS-21 | The stage-1 kit and new configs under `experiments/` | LEAD | S1 |
| LS-22 | X′ (or Y) integration after `--final`'s lexicon-pin procedure | LEAD | S1 |
| LS-23 | Recipe G: reuse the 8 Oct units or re-run | LEAD | S1 |
| LA-01 | Llama base download for Safe LoRA (UQ2) | USER | Later |
| LA-02 | Paper decision 10: the five actors (U-20) | USER | Later |
| LA-03 | Self-replay and task-format safety data (U-13) | USER | Later |
| LA-04 | OLMo 3 at 7–8B (U-14) | USER (ladder USER-CONFIRM) | Later |
| LA-05 | A transfer test for the dataset publisher (U-15) | USER | Later |
| LA-06 | B↓LR at 7–8B (U-16) | USER | Later |
| LA-07 | Second rater and human label check (U-17; HR) | USER | Later |
| LA-08 | A Qwen2.5-7B rung probe (U-18) | USER | Later |
| LA-09 | The re-plan's option B, its 7–8B scope part (PAPER decision 28; the 1B status part is UW-21) | USER-CONFIRM | Later |
| LA-10 | 7–8B Part 1 decisions other than the 1B part of S | USER | Later |
| LA-11 | Moved to UW-20 (RC-11 (c)); not counted | — | — |
| LA-12 | A public deposit and the data release | USER | Later |
| LA-13 | Paper-text rulings for the next revision | LEAD | Later |
| LA-14 | 7–8B preparation rulings | LEAD | Later |
| LA-15 | Stage-2 rules that reuse stage-1 rules | LEAD | Later |
| LA-16 | Alpaca's scope and Gate B-lite on Alpaca | USER | Later |

---

## 1. USER and USER-CONFIRM items due at W1

### UW-01. Confirm the relayed standing rule
- **Question.** Does the user confirm, in the lead's chat, the rule "keep the more ambitious one always but always open to fallbacks"?
- **Options.** (a) Confirm it. (b) Decline it. (c) Confirm it with limits (for example, only for items at $0, or only for items that need no download).
- **Recommended default.** None: only the user can answer. Until then, every USER-CONFIRM item is a USER question. Its "ambitious default" is then only a recommendation, and its pre-set fallback applies if the user is silent at the item's deadline (B:10; C:19).
- **Effect.** 4 items here are USER-CONFIRM, and 7 USER items carry a USER-CONFIRM ladder (M: this list, revision 2; RC-12). PAPER decisions 26 and 28 (the title; the re-plan's option B) also rest on the rule (PAPER:240, :242; C:19).
- **Cost.** $0.
- **Decides:** USER. **Deadline:** W1 (UW-07a's ladder, UW-14 and UW-20 are due at W1).
- **Sources.** C U-0 (:117), Q6 (:558); B:10, §J item 11 (:644); the merge brief.

### UW-02. The primary variance model
- **Question.** Does the primary analysis pair the arms by seed, and so replace PLAN-S:102 ("Seeds are not paired")?
- **Options.** (a) HB: the mean of the seed-matched differences; one residual variance per arm, fitted by REML; a crossed prompt part; Satterthwaite df (B §A.2–§A.5). (b) HB-C: HB with one seed effect per design cluster (LW-01). (c) S-a: the approved unpaired analysis, variance pooled over the 8 arms, with Welch (S-aW) as its sensitivity (PLAN-S:102). (d) S-b2x: seed-blocked with one pooled residual. It has more power, but it fails when arms differ in seed variance; B does not recommend it.
- **Recommended default.** (a) or (b) as primary, with S-a and S-aW reported (B §A.10). P78 recommends the same seed-blocked form at both model sizes (P78 §4). **Current rule in force until the user decides:** (c).
- **Silent default.** (c) is primary. HB (or HB-C) is a pre-registered sensitivity. The W1 record states S-a's simulated failure with unequal arm variances (B:215): 11.8–12.4% family-wise with one arm at 3 × the seed SD (M: B SIM; M: `review_stats_sim_out.txt` Part H). The label row then carries the flag "rests on equal arm variances (S-aW does not reject)" where S-a rejects and S-aW does not (DRAFT §3.2; S-8). The 42 df are nominal (DRAFT §3.2; S-13).
- **Numbers.** HB stays near nominal in all 19 simulated scenarios: family-wise 3.0–4.6% against 5% nominal (M: B SIM). S-a reaches 11.8% family-wise when one arm's seed SD is three times larger (M: B SIM, scenario H2). P1's MDE at 80%: HB 3.5 pp at the wave-0a pair SD of 1.83 pp and 7.1 pp at a pair SD of 3.75 pp; at 3.75 pp, S-a gives 5.2 pp and Welch 6.1 pp (M: B SIM). So HB wins on power only when the same-seed correlation is high. That choice was made after the wave-0a values were seen (B §K.3). The ρ of 0.76 rests on 3 seed pairs; with a true ρ of 0, a sample correlation this large occurs with probability 0.45 (M: `review_stats_arith_out.txt`). At B's scenario N2 (the coupling that the sampling streams measure well: pair SD 3.32 pp, ρ 0.21) the P1 / P4 MDE is S-a 5.1 / 5.4, S-aW 6.0 / 6.6 and HB 6.4 / 7.2 pp (M: B SIM §A.9; S-6).
- **Why USER here.** B recommends [LEAD], because the adopted text does not name the variance model (B:215). But PLAN-S:102 is part of the plan that the user approved "as drafted as the basis" (FOCUS:236), and P78 marks the same choice [USER] (P78:161, :386). This merge keeps the approved text in force until the user decides.
- **Cost.** $0 (the code is B16, an S1 build item).
- **Decides:** USER. **Deadline:** W1 (REQ-21 (b)).
- **Sources.** B §A (:55–:236), §H A1 (:580), §I row 1 (:614); B-VR V-1, V-2; P78 §4 (:138–:161), [USER] 1 (:386); PLAN-S:102; B-CK2 §8 (:263–:281).

### UW-03. Seed layout D1
- **Question.** Move R's eighth run (seed 1108) to a0 at seed 1107, so that P4 gets a sixth seed pair?
- **Options.** (a) D1: a0 at 1101–1107 and R at 1101–1107, 50 runs. (b) D0, as approved: a0 at 1101–1106 and R at 1101–1108 (FOCUS:242). Under plan B with D1: R at 1101–1110, and two runs are not spent.
- **Recommended default.** (a), but only if UW-02 picks a paired model. If UW-02 keeps S-a, (b). **Silent default:** (b).
- **Numbers.** Under HB, P4's MDE falls from 4.0 to 3.5 pp at wave-0a noise, and from 8.0 to 7.1 pp at a pair SD of 3.75 pp (M: B SIM). Under S-a, P1's MDE moves from 5.2 to 5.3 pp (M: B SIM).
- **Cost.** $0: the same 50 runs (R: B:117). Plan B under D1 saves about $3 (E: B:131).
- **Decides:** USER (it changes a user-approved seed list). **Deadline:** W1 (REQ-21 (d)).
- **Sources.** B §A.6 (:109–:131), §H A4 (:584); P78 §4 "Seed layout" (:160), [LEAD] 10 (:409); B-CK2 §8 item 4 (:278); FOCUS:242; PLAN-S:116.

### UW-04. The testing family (BRIEF U4, family part)
- **Question.** Does one closed graphical family Φ replace "Holm over P1–P6 at 5%", and, if not, how are the O and task-loss "worse" tests grouped?
- **Options.** (a) Φ: 24 nodes, that is U_k (two-sided), O_k and L_k (one-sided, adverse) and F_k ("feasible at τ_O\* = 5 pp") per contrast. Start weights: 0.15 per U_k, 0.1/12 per O_k and L_k, 0 per F_k (B §B.2). (b) The frozen Holm over P1–P6 for U, plus one Holm family of six for O and one for L, each at 5%, each in a per-contrast variance form (Welch under S-a; the HB form under HB; DRAFT §4.3, S-1); an F family, the fourth, only if UW-06 passes. (c) One Holm family of 18 (A:427, its alternative). (d) A fixed sequence (MRA W4). B-CK3 shows that a gatekeeper never tests the side effects of a repair that is not better on U.
- **Recommended default.** (a) (B). **Current rule in force until the user decides:** Holm over P1–P6 (FOCUS:241; D5 = (a), FOCUS:78). **Silent default:** (b).
- **Sub-choice inside (b).** One-sided adverse tests (B:290), or two-sided tests where an adverse rejection gives "worse" (A:427). (I) The user's 18:31 rule says "each in its harmful direction" (FOCUS:215). That fits one-sided tests.
- **Numbers.** Φ lowers the first U step from 0.833% (Holm) to 0.75%, so the U MDE rises by about 1.6% (M: B NUM). Φ's family-wise rate is 4.7–4.9% under correlated statistics (M: B-VR). Under (b), the chance of at least one false "worse" is up to about 11% (R: B-CK3 §3.2, via B:290). MRA W4 gives up to about 14% for three adverse families (R: A:482).
- **Cost.** $0.
- **Decides:** USER (Φ changes a frozen input; BRIEF lists U4 as a user decision). The lead may close the O and L Holm families part (not Φ) by the route in UW-08 (RC-13). **Deadline:** W1 (REQ-21 (b), (c)).
- **Sources.** B §B.1–§B.2 (:240–:292), §H B1 (:589); A §L.6 LQ43 (:427), §N item 2 (:482); BRIEF U4 (:192), D5-2 row (:174); B-CK3 §3.4–§3.5 (:198–:252); MRA W4 (:111).

### UW-05. The "worse" rule for O and task loss
- **Question.** Should "worse on O" (or on task loss) also need the arm to be infeasible against θ0 (or a0)?
- **Options.** (a) Keep the user's 18:31 rule: any significantly adverse contrast against the comparator gives "worse" (FOCUS:215). (b) R1.3: adverse on O = O-infeasible at τ_O\* against θ0 AND significantly above the comparator; adverse on L = L-infeasible at τ_L against a0 AND significantly above the comparator (C R1.3). (c) Margins m_O and m_L on the comparator test (B-CK3 §3.5; B withdrew it in favour of (b)). (d) MRB §8.3: no "worse (O)" unless O is above θ0 by more than τ_O. (e) For the coherence screen (RC-02): label a failing repair "worse (answers do not end)" and read a failing comparator's contrasts "inconclusive" (B §F items 3–4). In force: the tested label stays, with the flags "fails answers end" and "comparator fails answers end" (LW-09).
- **Recommended default.** (b): B and C agree. **Current rule in force until the user decides:** (a).
- **Silent default.** (a) stays the label rule. (b) at τ_O\* = 5 pp is committed as a pre-registered sensitivity label; a yes to (b) fixes τ_O\* = 5 pp for R1.3 whatever UW-06 says (RC-17 (a)). The user may switch to (b) until the earlier of S1 and the first read of any Gate B wave-1 arm's O or task loss; between that read and S1, only with a record of every Gate B O and L value read before it, as a disclosed deviation (S-2). After S1, no switch is allowed (C R1.5; B:305). For (e): flags only.
- **Why it matters.** θ0 refuses 17 of the 100 dev over-refusal prompts, and the Gate A a0 seeds refuse 4, 6 and 4 (R: Gate A counts, via C:162). So an add arm that returns to θ0's level is feasible but reads "worse (O)" under (a) (R: MRB §8.3). The same holds for task loss: with the seed SD at s, a rise of half τ_L reads "worse (L)" with probability 0.34–0.55 at Holm's first step (M: `review_stats_arith_out.txt`, `review_fixes_numbers_out.txt`; S-10).
- **Cost.** $0.
- **Decides:** USER (it narrows a user decision). **Deadline:** W1 (REQ-21 (c)).
- **Sources.** C R1.3 (:185–:193), R1.5 (:197), U-1 (:118), C-j (:509); B §B.3 (:294–:306), §H B2 (:590); A §N item 2 (:482); B-CK3 §3.5 item 2 (:250); C-OR D1 (:334).

### UW-06. One primary over-refusal bar
- **Question.** Make τ_O = 5 pp the one primary bar (the F_k node and the R1.3 test), with 2 and 10 pp still reported?
- **Options.** (a) τ_O\* = 5 pp. (b) No primary τ_O: the grid {2, 5, 10} pp stays as approved, each point reported (FOCUS:245).
- **Recommended default.** (a). The value equals Gate B's frozen G4 bar, θ0 + 5 = 22 of 100 (R: PREREG §3). G4 itself does not change (C VF-14). **Silent default:** (b). Then the F_k nodes leave Φ, and R1.3 at 5 pp stays a sensitivity label (B:598).
- **Numbers.** τ_O = 2 pp needs about 770–3,100 paired prompts for 80% power (R: B-CK3 §4.4, via B:513).
- **Cost.** $0.
- **Decides:** USER (it makes one point of a user-approved grid a test bar). **Deadline:** W1 (REQ-21 (e)).
- **Sources.** B §E.1 (:491), §H E1 (:598); C R1.4 (:195), U-2 (:119); B-CK3 §4.7 option 2 (:336); C-OR D2 (:335).

### UW-07a. O-ext from N or F (BRIEF U8) (split from UW-07 in revision 2; RC-05)
- **Question.** If REQ-19 shows a 6-seed O MDE above 5 pp under the error model of LW-03, does stage 1 add 400 over-refusal prompts from a new public source, as the 8 Oct rule allows?
- **Options.** **N:** 400 harmless PHTest rows, a download that the user approves (R: C R5b.2); contamination with OLMo's post-training data is UNVERIFIED. **F:** the dev 100 only; every O sentence says "on these 100 prompts", and τ_O = 2 and 5 pp are stated as unresolved for new prompts. A's form (A:383): a new public source, or "O-ext as post-Gate-B exploratory". H is not an option here (UW-07b).
- **Recommended default (ambitious; rests on UW-01).** N: 500 prompts (dev 100 + 400 from N) as the primary O bank, with source weights fixed in advance (B §E.3; C R5b.2). Fallback: F. **Silent default at the W1 commit:** F, as BRIEF U8's second branch; a later O-ext is post-Gate-B exploratory (C VF-8).
- **Numbers.** The 6-seed O MDE is about 11–12 pp with prompts random, and about 2 pp seed-only (M: C-OR §4; B:496). These are two-sided 5%, 80% MDEs; the one-sided NI form gives 10.2 pp (R: C `ni_power.out`; S-26). With 500 prompts, the smallest τ_O with 80% non-inferiority power falls from 10.2 to 4.6 pp (M: C-OR §5.3). An add arm at θ0's level is shown feasible inside Φ with probability 0.06–0.33 on 100 prompts and 0.43–0.99 on 500 (M: B NUM; an optimistic normal approximation).
- **Cost.** N: $10–27 for 72 units at a 128-token cap, if LW-05's truncation check passes; $40–70 if it fails and the 2,048-token cap stays (E: C R5b.2, from C-OR §5.4). About +25% if SR, S6 and B↓LR also run (E: C:336). B's coarser range is $28–90 (E: B:519). F: $0. LW-05's $0 checks run before this item is decided, whatever the answer (RC-19).
- **Decides:** USER (ladder USER-CONFIRM): N needs a download that the user approves in any case (RC-12). **Deadline:** W1 for the answer; S1 for the runs.
- **Sources.** BRIEF U8 (:196); A §L.3 LQ37 and UQ4 (:383), §Q.1 (:508); B §E.2–§E.3 (:493–:520), §H E3 (:600); C R5b.2 (:331–:340), U-3 (:120); C-OR D4 (:337); PLAN-S:197; FOCUS:245.

### UW-07b. Allow H, a draw from the hidden over-refusal remainder (split from UW-07 in revision 2; RC-05)
- **Question.** Does the user change the 8 Oct rule "then from a new public source (a download the user approves), never from the hidden remainder" (R: FOCUS:245; PLAN-S:197) to allow H?
- **Options.** **H:** a sealed, stratified, counts-only draw of 400 prompts from the hidden over-refusal remainder (100 XSTest-safe, 300 OR-Bench-Hard), run by the lead; 969 prompts stay hidden (M: C:332). (b) Keep the rule.
- **Recommended default.** None. B §E.3 and C R5b.2 put H first in their ladders, but H reverses a user rule, so it cannot be a ladder default (RC-05). **Current rule in force until the user decides:** H is not allowed. **Silent default:** H is not allowed.
- **Cost.** As N in UW-07a.
- **Decides:** USER. **Deadline:** W1 (with UW-07a).
- **Sources.** As UW-07a; FOCUS:245; PLAN-S:197.

### UW-08. The label order (BRIEF U4, order part)
- **Question.** When the U result and a side-effect result disagree, which word heads the label row?
- **Options.** (a) "Worse" first, naming the measure; then "better"; then "equivalent" with its grade; then "inconclusive". The full row is always printed, so "worse (O)" never hides a U benefit (A LQ44; B §B.5). (b) A compound label, for example "better on U; worse on O" (B-CK3 §3.5 item 3).
- **Recommended default.** (a). The row also prints "significant, below the SESOI" when the U test rejects with an estimate under 5 pp (MRB W8; B:321). Revision 2 of the pre-registration DRAFT (§4.5) makes the headline steps a partition: the coherence screen gives flags, not a word (LW-09); "significant, below the SESOI" is added in the "equivalent" and "inconclusive" steps; a "worse (U)" contrast that is also equivalent prints both; and a "worse (O)" or "worse (L)" word prints the U part beside it, for example "worse (L); U part: better" (S-9, S-10, RC-32).
- **Why USER.** BRIEF lists U4 as a user decision (:192). A kept it [LEAD] under the user's 16 Oct "stop asking me for approval", but A cited the wrong precedent (A-RV R4). The lead may close U4 (the label order and the O and L Holm families, not Φ), U5 (keep, the approved default), U6 and U9 by recording in the W1 FOCUS entry that the 16 Oct instruction covers them, as the D5 entry did for U2 and U3 (R: FOCUS 'D5 DECIDED: (a)'; ADD line 7). Φ (UW-04 (a)) and R1.3 (UW-05 (b)) stay USER in any case (RC-13; one text in all three files).
- **Cost.** $0.
- **Decides:** USER. **Deadline:** W1 (REQ-21 (c)).
- **Sources.** A §L.6 LQ44 (:429–:439); B §B.5 (:317–:329), §H B4 (:592); BRIEF U4 (:192); A-RV R4 (:100–:103); B-CK3 §3.5 item 3 (:251); MRA W12 (:236); MRB W8 (:180).

### UW-09. The skill measure (BRIEF U6)
- **Question.** Keep held-out task loss on all 200 task rows as the skill limit, with ARC report-only?
- **Options.** (a) Yes, as PLAN-S:192–193 says. (b) Another measure.
- **Recommended default.** (a). It is the approved text, so it is also the silent default. The lead may close this item by the route in UW-08 (RC-13).
- **Cost.** $0.
- **Decides:** USER (BRIEF U6). **Deadline:** W1 (REQ-21 (e)).
- **Sources.** BRIEF U6 (:194); A §L.5 LQ42 (:421); A-RV R4 (:100–:103); PLAN-S:192–193.

### UW-10. H1 under recipe bt (BRIEF U5, E6)
- **Question.** Keep, drop or promote the length rule H1 trained under the token-mean loss (recipe bt)?
- **Options.** (a) Keep it as secondary arm 5, at 3 seeds (PLAN-S:163, approved). (b) Drop it. (c) Promote "H1 and R under the token-mean loss" into the primary family (MRB W4). (c) changes the approved primary family, and no draft costs or wires it.
- **Recommended default.** (a), the approved plan, which is also the silent default. (I) The bt run showed that the token-mean loss alone does not lower erosion (FOCUS:198). ADD §5 item 1's token-axis report answers part of MRB W4.
- **Cost.** (a): 3 runs inside stage 1c's "up to $45–80" (E: PLAN-S:225). (c): 12 runs, about $17.5; $19.8 with 3 pods; $24.8 × 1.25 (M: this list, at 1 FRE = $1.46 and 26 min of overhead per pod, both from A §C.2–§C.3).
- **Decides:** USER (BRIEF U5). The lead may close it with (a), the approved default, by the route in UW-08 (RC-13); (c) stays USER in any case. **Deadline:** W1 (REQ-21 (g)).
- **Sources.** BRIEF U5 (:193); PLAN-S:163; FOCUS:198; MRB W4 (:115–:128); ADD §5 item 1 (:320).

### UW-11. The deviations the user should see (BRIEF U7)
- **Question.** Does the user accept four recorded deviations from PLAN-S: S1's pool wording, L1's layer-scan statistic, L1's two-sided score, and L1's scaling of the post-sublayer norm outputs?
- **Options.** (a) Accept: they enter REQ-21 (i). (b) Object: the affected settings change before wave 1.
- **Recommended default.** (a). ADD L3 and L4 already build on them (ADD:54–:73). The fourth has no real alternative, because OLMo-2's norms cancel LARF's weight scaling (BRIEF:195).
- **Cost.** $0.
- **Decides:** USER. **Deadline:** W1 (REQ-21 (i)).
- **Sources.** BRIEF U7 (:195), REQ-21 (i) (:121); ADD L3–L4 (:54–:73).

### UW-12. The reading of "frozen once" (BRIEF U9)
- **Question.** Confirm that "the representation module is frozen once" means that Gate C's script stays pinned and that REQ-3 is a new module with a byte-equality test at Gate C's settings?
- **Options.** (a) Confirm. (b) Another reading.
- **Recommended default.** (a). The build follows it (BRIEF REQ-3, :73).
- **Cost.** $0.
- **Decides:** USER (BRIEF marks it "not recorded as answered"). The lead may close it with (a) by the route in UW-08 (RC-13). **Deadline:** W1.
- **Sources.** BRIEF U9 (:197), REQ-3 (:73); FOCUS:251.

### UW-13. The margin for other families
- **Question.** Fix now that a second family's margin is δ_fam = 5 × E_fam / 45.11 pp, that is 0.1108 × its Gate A mean E?
- **Options.** (a) Yes; the absolute 5 pp is reported beside it. (b) 5 pp absolute in every family, as now.
- **Recommended default.** (a) (B). **Silent default:** (b).
- **Numbers.** δ = 5 pp is 11.1% of OLMo's mean E of 45.11 pp (M: B NUM). The rule gives 2.2 pp at E = 20 pp and 6.1 pp at E = 55 pp (M: B NUM).
- **Cost.** $0.
- **Decides:** USER (it fixes a stage-2 rule). **Deadline:** W1 (B's deadline). PLAN-S:243 asked for the comparison scale before Llama's formal Gate A; that point has passed (R: LLB §14).
- **Sources.** B §C.3 (:378–:382), §H C2 (:595); PLAN-S:243; LLB §14 (:307); MRA W5 (:123).

### UW-14. The title word "Compute-Matched" (PAPER decision 26)
- **Question.** Does the title keep "Compute-Matched", when the removals match rows and the design adds a token-axis analysis, but no arm matches tokens or GPU-seconds?
- **Options.** (a) Keep it, if LW-17 records that ADD §5 item 1's token-axis report is "a token-matched analysis beside the row-matched one". (b) Use the pre-set fallback title, alternative 5: "A Cost-Accounted Comparison of Data Repairs". (c) Keep it and add token-matched removal arms (new arms and money). The builder extract costs R_tok for A1, L1 and H1 at 9 runs, about $13.1, $15.5 with pod overhead, $19.3 × 1.25 (M: `w1_extract_numbers.out`; EXTR W1-03; RC-14); a USER item, because it adds arms and money.
- **Recommended default.** PAPER records (a) as "resolved by the user's rule (17 Oct, relayed)" (PAPER:240). That rests on UW-01. So, until the user confirms, (a) is a recommendation, and (b) is the fallback "only if token matching cannot be done". **Silent default (RC-33):** the pre-registration carries the token-axis analysis (LQ47) in any case; the title is a paper item and stays as PAPER has it until the user confirms UW-01 or decides.
- **Cost.** $0 for (a) and (b).
- **Decides:** USER-CONFIRM. **Deadline:** W1 (ADD §5 item 1 flags it in REQ-21 (a)).
- **Sources.** PAPER decision 26 (:240); ADD §5 item 1 (:320); A §C.1 LQ47 (:302); A-RV N2 (:127); MRA W8 (:177); SWEEP §0 item 3.

### UW-15. The wording of headline item (2)
- **Question.** Change the user-adopted headline item (2) to "does each diagnostic find a concentrated, harmful-prompt cause"?
- **Options.** (a) Yes (F1). (b) Keep the 8 Oct wording.
- **Recommended default.** (a) (B F1; C VF-19). The factual fix ("PKU red-team prompts with PKU-safe, non-refusing answers", not "benign-looking") is the lead's (LW-10). B marks this item USER-CONFIRM. It is a wording change of a user decision, not a ladder, so this list marks it USER (I).
- **Why.** The plant shares its source and its answer type with the anchors' positive side. Its share of its cell grows from 6.2% to 100% over the three menu sizes (R: B-CK11 §2.2, §6).
- **Cost.** $0.
- **Decides:** USER. **Deadline:** W1 (REQ-21 (a)).
- **Sources.** B §G F1 (:555), §H G1 (:603); C R8.5 (:414); B-CK11 §4 F1 (:143); FOCUS:240.

### UW-16. A second, benign-topic plant (F10)
- **Question.** Add a second plant whose prompts look benign and whose answers carry a known eroding signal?
- **Options.** (a) Add it. It needs new text (authored, or a download that the user approves), its own pilot and its own sweep, and it widens the control's scientific target. (b) Not now: keep the current plant with F1's limited claim (UW-15). Any later benign plant is post-Gate-B exploratory.
- **Recommended default.** The drafts disagree. B: ambitious default (a), with (b) automatic if its rules are not committed by W1 (B:568). C: (b), "not now" (C U-12). This list recommends (b) (I). The reasons: the deadline is before the T1 commit, because REQ-8's settings are in the T1 bundle (C VF-19); new text or a download is needed; and the slack before wave 1 is $8.03 (M: $91.94 balance minus $83.91 need, FOCUS:76, :77). If the user confirms UW-01 and funds it, B's ladder applies instead.
- **Cost.** $15–30 (E: pilot $4–7 plus sweep $11–23; B-CK11 F10).
- **Decides:** USER: it widens a scientific target (R: B §H G3, "[USER] (target)"), so it is not a ladder item (RC-12). If the user confirms UW-01 and funds it, B's ladder is the recommendation. **Deadline:** W1, and in practice before the T1 commit (LW-22).
- **Sources.** B §G F10 (:568), §H G3 (:605); C R8.5 (:414), U-12 (:129); B-CK11 F10 (:160); FOCUS:251.

### UW-17. A prompt-only classifier score (R8.6)
- **Question.** Also score each row's prompt alone with Qwen3Guard, in REQ-23's pass?
- **Options.** (a) Yes. (b) No.
- **Recommended default.** (b) (C U-12).
- **Cost.** About +$0.5 in the same pass (E: C-EM §4.4).
- **Decides:** USER. **Deadline:** W1 (REQ-23's settings hash is a W1 item).
- **Sources.** C R8.6 (:416), U-12 (:129); C-EM D15 (:304).

### UW-18. An exception for REQ-23, only if it is late (U-19)
- **Question.** Only if REQ-23 (the per-row content-classifier scorer) is not committed at W1: may it be recorded as post-Gate-B exploratory, as the 9 Oct item (9) allows for DataShield-style and Self-Inf-N-style?
- **Options.** (a) No: build it, and wave 1 waits for it (9 Oct item (6)). (b) Yes: extend item (9) to it.
- **Recommended default.** (a). The script is small (C R8.1).
- **Cost.** $0 to build; about $1 to run later on a stage-1 pod (E: C-EM §4.2).
- **Decides:** USER (conditional). **Deadline:** W1.
- **Sources.** C R0.2 (:152), R8.1 (:403–:406), U-19 (:136); FOCUS:125 items (6), (9).

### UW-19. Freeze the Llama-3.2-1B Gate B-lite rules with the W1 record
- **Question.** Does the user answer the Llama note's U0–U8 now, so that the Llama rules and Llama's held-out selector predictions freeze with the stage-1 commitments, blind to every OLMo unit outcome?
- **Options.** (a) Freeze at W1 with the note's defaults: U0 scope "K − LC" if stage 2 is funded at about the re-plan's level, else "W0"; U1 Llama-anchored G1 bars (capped ≤ 7%, screen ≤ 14%), chosen after Llama's Gate A was read, and disclosed; U2 cut the length control; U3 one transfer contrast if OLMo reads LOCALIZED; U4 stop after wave 0a if Llama's noise gate fails; U5 Gate B-lite has its own funding event; U6 the order of Llama and Alpaca; U7 a Llama stratum in any second-rater read; U8 carry 8.57 pp as an exploratory floor. (b) Freeze later. Then the transfer test and every cross-family comparison are labelled "post-OLMo-outcome".
- **Recommended default.** (a) (LLB L1). Two cautions. U0 = W0 drops the held-out selector test on Llama that the adopted design names (FOCUS:240; PLAN-S:132). U6 "Llama first" would reverse the user's 9 Oct rule "Alpaca right after Gate B" (FOCUS:155); that rule stays in force until the user decides.
- **Cost.** $0 to freeze. Gate B-lite spend about $34–67 at full scope, or $12–22 at W0 (E: LLB §12, via U5).
- **Decides:** USER. **Deadline:** W1; at the latest, before the first OLMo wave-1 outcome is read and before Llama's anchor job (LLB §14).
- **Sources.** LLB §14 (:305–:321), §15 (:323–:338), §16 U0–U8 (:343–:351), L1 (:354); PLAN-S:132, :243; FOCUS:155, :240.

### UW-20. Two more plant locations (F9) (was LA-11; moved in revision 2, RC-11 (c))
- **Question.** Commit now, as conditional rule text, two more sealed plant locations that run if stage 1b is funded?
- **Options.** (a) Yes: the draw labels and the location rule go into the conditional W1 text (LW-19), and the runs wait for the user's yes and the stage-1b funding event. (b) No: F6's $0 relocation replay gives the scorer-side spread, and the paper says that the runs side has one location.
- **Recommended default (ambitious; rests on UW-01).** (a) if the 1b funding covers it; fallback (b). If the rule text is not committed at W1, a later F9 is post-Gate-B exploratory, because the plant is committed before wave 1 (R: FOCUS 8 Oct 13:53 UTC).
- **Cost.** About $34–70 (E: B-CK11 §2.4).
- **Decides:** USER-CONFIRM (B §H G2). **Deadline:** W1 for the conditional rule text (R: B §H G2, "W1 (rule); funding later"); the stage-1b funding event for the runs.
- **Sources.** B §G F9 (:567), §H G2 (:604); B-CK11 §2.4 (:115); DRAFT FC-13; EXTR W1-10.

### UW-21. The status of OLMo-1B's stage 1 under the re-plan's option B (split from LA-09 in revision 2, RC-11 (d))
- **Question.** If the user adopts the re-plan's option B, which calls "OLMo-1B's stage 1 as development" (R: PAPER decision 28), does OLMo-2-1B's P1–P6 stay the confirmatory primary family pre-registered here?
- **Options.** (a) It stays confirmatory, as pre-registered (D5 = (a); FOCUS:240–:241). (b) It becomes development.
- **Recommended default.** **Current rule in force:** (a). **Silent default:** (a), confirmatory. An answer at the 20 Nov gate (LA-09) would come after stage-1 outcomes may exist, and could reclassify a pre-registered primary family then, so this part is due earlier (I).
- **Cost.** $0.
- **Decides:** USER: (b) would change D5 = (a)'s primary family, and PAPER's "resolved by the user's rule" rests on UW-01. **Deadline:** W1 (REQ-21 (a)); at the latest S1, before any newly run stage-1 cell's outcome is read.
- **Sources.** PAPER decision 28 (:242); REPLAN §5 (block A by 3 Nov); FOCUS:78, :240–:241; DRAFT FC-18.

---

## 2. LEAD items due at W1

### LW-01. HB or HB-C (only if UW-02 picks a paired model)
- **Question.** Does the paired model use one seed shift for all eight arms (HB), or one shift per design cluster, {a0, S1, S3, S4} and {R, A1, L1, H1} (HB-C)?
- **Options.** (a) HB primary, HB-C as the sensitivity S-HBC (B's author). (b) HB-C primary, HB as the sensitivity (B's verifier leans here).
- **Recommended default.** Raise it to GPT before the W1 record. Whichever is primary, the other is pre-registered.
- **Numbers.** If one shift holds for all arms, HB-C costs 8–12% on the MDE. If the two clusters move apart, HB's SE is 1.35–1.50 × the true SD, and the P1 / P4 / P5 MDEs are 4.2 / 5.0 / 4.2 pp for HB-C against 5.0 / 6.1 / 5.5 pp for HB (M: B-VR, `verify_hbc.py`). Gate B has no add arm, so it cannot show which case holds (B:207).
- **Cost.** $0.
- **Decides:** LEAD, after GPT. **Deadline:** W1.
- **Sources.** B §A.10 (:207), §H A9 (:581); B-VR V-3, §7 (:172–:187).

### LW-02. The analysis-model details that B leaves to the lead
- **Question.** Confirm B's items A2, A3, A5, B3 and C1?
- **Options.** Confirm each, or edit it.
  - A2: the crossed prompt part in U's variance. Without it, false positives reached 8.0% and 14.6% in the two arm × prompt scenarios (M: B SIM).
  - A3: the reported sensitivities S-a, S-aW, S-HBC, S-b2x, S-HB0, S-G (coherent-only U and both G3 corners, among them "Controversial counted Unsafe", B-CK11 §5 Q7) and S-HB-tok (ADD §5 item 1). A label from S-a that differs is printed beside the primary label.
  - A5: the plan-A/B record prints the predicted P1 and P4 MDEs at the read σ̂ (about 3.5 pp at 1.83 pp and 8.5 pp at 4.5 pp under HB; M: B SIM), the "better" 80% effect and P(equivalent | 0). Under S-a the values are printed at ρ ∈ {0, 0.67, 0.76}, because σ̂ is a pair SD and S-a's SE uses the per-arm SD; plan A bounds HB's power but not S-a's (DRAFT §3.5; S-7). No rule changes. The option to move the plan-A cut stays withdrawn (B V-10).
  - Added in revision 2 (from the statistics review; [LEAD] W1): the O and L "worse" tests use a per-contrast variance form, Welch under S-a (S-1); S-a's equal-variance flag (S-8); "df 42 (nominal)" (S-13); the "better" label's 80% effect beside each test MDE (S-5). Text in DRAFT §3.2, §3.5, §4.3.
  - B3: equivalence grade 1 (the 90% interval inside ±5 pp, per comparison; the frozen rule) and grade 2 (the 98.33% interval, familywise; a new report).
  - C1: δ stays 5 pp, stated as "about 11% of the measured erosion" (11.1%; M: B NUM).
- **Recommended default.** Confirm all (B). If UW-02 keeps S-a, A2, A3 and A5 apply to the HB sensitivity.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 (REQ-21 (b), (c), (d), (f)).
- **Sources.** B §H A2, A3, A5, B3, C1 (:582–:594), §A.7 (:133–:145), §A.11 (:217–:222), §B.4 (:308–:315), §C.1 (:357–:369); B-CK11 §5 (:170–:187).

### LW-03. The error model for O (conflict C-i)
- **Question.** Are prompts random in O's inference, as for U, or is O read on these 100 prompts only (bank-conditional)?
- **Options.** (a) Prompts random: the same crossed model as U (B §E.2; C R1.8). (b) Bank-conditional: seed noise only, and every O sentence says "on these 100 prompts" (B-CK3 §4.7 option 1). A LQ36 takes O's SE "from the arm's seeds", which is (b).
- **Recommended default.** (a): B and C agree, and both endpoints then have one scope. The seed-only value is reported beside every O number.
- **Consequence.** (a) gives a 6-seed O MDE of about 11–12 pp, so U8 opens (UW-07a, UW-07b). (b) gives about 2 pp, so U8 stays closed (M: C-OR §4; B-CK3 §4.5).
- **Blinding.** The Gate A counts that set this consequence were known when the drafts chose (a). The grounds for (a) do not use them. REQ-21 (m) records the order of events (B V-2; LW-08).
- **Cost.** $0.
- **Under S-a (S-18).** U has no prompt term, so U and the O "worse" test are bank-conditional, while O feasibility stays prompt-random; every U and O sentence names its scope, and the confirmation is read as a test on new prompts (DRAFT §6.4). The exact S-a form of the prompt term is LW-33.
- **Decides:** LEAD. **Deadline:** W1, before REQ-19 runs. It also fixes REQ-16's O SE (LW-13).
- **Sources.** B §E.2 (:493–:498), §H E2 (:599), §I C-i (:620); C R1.8 (:203–:207), R5b.1 (:325–:329), C-i (:508), AMD-2 (:516); B-CK3 §4.5, §4.7 (:317, :332–:341); A LQ36 (:380); C-OR U-1 (:391).

### LW-04. Run REQ-19 and record its outputs
- **Question.** Run REQ-19 (the $0 O MDE and τ_L check) before wave 1, in both O conventions, and record its numbers?
- **Options.** (a) Run it now. (b) Run it later; then UW-07a and UW-07b cannot be answered at W1.
- **Recommended default.** (a), after LW-03 is fixed. REQ-19 prints the O MDE paired by prompt and seed-only. The value that matches LW-03 decides U8. The lead records a reading of PLAN-S:197's undefined "planning at f = 1" in REQ-21 (h); the builder does not guess it. REQ-19's τ_L must equal the recorded numbers: s = 0.0023749 nats, τ_L = 2√2 × s = 0.0067171 nats, and the 6-against-6 SE 0.0013711 nats (M: A §L.4 and TLC; re-run byte-identical by A-RV).
- **Cost.** $0 (Mac).
- **Decides:** LEAD. **Deadline:** W1.
- **Sources.** A LQ37, LQ41 (:383, :418), §L.4 (:385–:418); C R5b.1 (:325–:329); B §A.12 REQ-19 row (:233); C-OR U-5 (:398); ADD L16 (:287–:293); BRIEF REQ-19 (:115).

### LW-05. Three $0 checks on existing answers, before U8 is decided
- **Question.** Run C's three Mac checks: the 128-token truncation check, judge–lexicon agreement, and the partial-refusal counts?
- **Options.** (a) Run them. (b) Skip them; then O-ext (N, or H if UW-07b allows it) must keep the 2,048-token cap (UW-07a's higher cost). RC-19: check (1) sets that cost, which the user needs for UW-07a, so the checks run whatever the answer.
- **Recommended default.** (a), with both sides on one device. Pre-set bar for the truncation check: at least 97 of 100 flags agree in each unit, and no unit's count moves by more than 2 (R: C-OR §5.5). If a checked unit is a Gate B unit, REQ-21 (m) lists it.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1.
- **Sources.** C R5b.3 (:342–:347), R5b.5 (:351); C-OR D5 (:338).

### LW-06. The feasibility estimator and one bound convention
- **Question.** How is feasibility at τ_O and τ_L estimated, and what does "upper 90%" mean everywhere?
- **Options.** (a) C R1.1 with R1.2: O(m) = Ref(m) − Ref(θ0), paired by prompt; L(m) = ℓ̄(m) − ℓ̄(a0); "feasible" if the upper end of the two-sided 90% interval is at most τ; "infeasible" if the lower end is above τ; else "undetermined". REQ-16's screen uses the same bound. (b) A LQ36 and LQ39: the one-sided upper 90% bound, with the point estimate beside it.
- **Recommended default.** (a): B and C agree, and it matches the TOST interval. Reject a non-inferiority test against each arm's comparator (C R1.7): a full return to θ0 is +12.3 pp against a0, so it fails even at τ = 10 pp (M: C-OR §2.5).
- **Correction applied (A-RV R3; replaced in revision 2 by RC-04).** On the point estimate τ_O binds only above 19, 22 or 27 of 100 (M: 17 + τ). With a seed-only SE (at least 1.53 pp; R: A-RV R3) a one-sided 90% bound adds about 2.0–2.3 pp (M: A-RV R3), and the upper end of the two-sided 90% interval adds about 2.5–3.1 pp (M: `review_fixes_numbers_out.txt`). Under the prompts-random model in force for O (SE 4.0–4.2 pp at 100 prompts; M: C-OR §4), the upper end of the two-sided 90% interval adds about 6.6–6.9 pp (M: 1.645 × 4.0–4.2), so an arm at θ0's level is "undetermined" at τ_O = 2 and 5 on 100 prompts.
- **Cost.** $0.
- **Decides:** LEAD (the user fixed θ0 and the grid, not the estimator; C:179). **Deadline:** W1 (REQ-21 (e), (h); REQ-16).
- **Sources.** C R1.1, R1.2, R1.7 (:172–:183, :201), C-b (:501); B §E.4 (:522–:526), §I (:617); A LQ36, LQ39 (:380, :416), §L.1 (:376); A-RV R3 (:95–:98).

### LW-07. The comparator for τ_L (raise to GPT)
- **Question.** Is task-loss feasibility read against a0, as PLAN-S:124 says, or against each arm's dose-matched comparator?
- **Options.** (a) Against a0. ℓ̄(m) − ℓ̄(R) is reported beside every removal arm. If R itself fails τ_L, the text says that the 600-row dose costs more task loss than τ_L. (b) Against each arm's comparator. (b) changes the approved PLAN-S:124, so it would become a USER item.
- **Recommended default.** (a), and raise the choice to GPT before the W1 record (A LQ38; B E4; C Q1). It is consequential: a 600-row removal trains 33 steps, not 38 (R: PLAN-S:102), so every removal arm may fail τ_L by dose alone.
- **Blinding warning.** The Llama note's authors saw the OLMo R arms' task-loss differences over the same-seed a0 (LLB §15 item 8), and I read that line. A's LQ40 asks who saw any arm's task loss before LQ38 is fixed. REQ-21 (m) must list these readers (LW-08). This list does not repeat the values.
- **Cost.** $0.
- **Decides:** LEAD, after GPT. **Deadline:** W1 (REQ-21 (e)).
- **Sources.** A LQ38, LQ40 (:415, :417); B §E.4 (:526), §H E4 (:601); C C-c (:502), AMD-7 (:521), Q1 (:553); C-OR U-3 (:393); LLB §15 (:323–:338); PLAN-S:124.

### LW-08. The blinding line, REQ-21 (m)
- **Question.** What exact text does REQ-21 (m) carry about the Gate B and stage-1 values that each writer saw before the W1 choices were made?
- **Options.** (a) One text built from every draft's list. (b) One paragraph per draft.
- **Recommended default.** (a). Start from B §K.3's proposed text and add:
  1. ADD §3 (4)'s list: r_j, σ̂_gate 1.83 pp, Gate B's P4 prediction (not stage-1 P4; RC-30), the P(LOCALIZED) lookup, the re-costing figures, and the sealed rankings, scores, picks and ρ values.
  2. A §B's per-writer table, with the re-verify worker added as a writer (A-RV N6).
  3. The six reused primary cells whose values were read: a0 and R at 1101–1103 (B §K.3).
  4. Every choice made after which values: the paired model, the size of D1's gain, the REQ-17 ρ grid, the O error model, the arm-pooled coherence bar, and the withdrawn plan-A cut (B §K.3).
  5. One wave-0a R arm's aggregate summary, with its over-refusal count, seen by the review-B workers (C R0.3).
  6. The OLMo R arms' answers-end counts and task-loss differences, used by the Llama note (LLB §14), and seen by me (task-loss differences only; LW-07; §10).
  7. L3 confirmed after the seal, and the labels named after the seal (ADD L3 (2), L13 (7)).
  8. T1 kept so far (nobody read wave-0b's `rows.jsonl`; FOCUS:77), and T2 not met (ADD §3 (4)).
  9. Added in revision 2: the writers of the two reviews and of this revision, with what each saw (DRAFT §12.2); the choices after values that the statistics review adds (DRAFT §12.3 items (10)–(13); S-14); and §12.4's rule for inference rules written after the W1 commit (S-2).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1.
- **Sources.** A §B (:446–:473), LQ40 (:417), LQ46 (:473); A-RV N6 (:131); B §K.3 (:679–:685), §H M (:606); C R0.3 (:154–:158); ADD §3 (4) (:300), L3 (:58), L13 (7) (:228); BRIEF T1, T2 (:62–:63); LLB §14 (:316); FOCUS:77, :82.

### LW-09. Arms that fail the coherence screen
- **Question.** How does stage 1 label an arm whose answers fail the coherence screen?
- **Options.** (a) B §F: Gate A's bar (at most 5% capped, at most 10% failing the screen) applied to an arm's sampled answers pooled over its seeds; no arm and no seed is dropped; a failing comparator makes its contrasts "inconclusive (comparator fails answers end)"; coherent-only U is reported. (b) The same with a per-seed bar. It is stricter, and it fires on seed noise.
- **Recommended default.** (a), with one change (RC-02): the tested label stays; a failing repair or comparator gets the flag "fails answers end" (or "comparator fails answers end") beside the word, not a fifth label and not a new word. The user's "worse" label means a significantly adverse contrast (FOCUS:215), so a new "worse" reason would widen a user decision, and "inconclusive" in place of a tested label would change it too. "Worse" or "inconclusive" for coherence joins UW-05 as a USER question (option (e)). Revision 1 proposed the word "fails answers end" in place of the label; RC-02 notes that this is a fifth headline word, so revision 2 makes it a flag.
- **Numbers.** The a0 seeds fail the screen on 7.0%, 4.7% and 3.7% of answers (R: B-CK3 §5.2). Per seed, P(a unit is over 10%) is 0.2–6.6%, so over about 50 units P(at least one fails) is 10–97% (M: B §F).
- **Notes.** The pooled bar departs from PREREG G1's per-run use; Gate B itself does not change (B V-14). It was chosen after a0's screen rates were read, so REQ-21 (m) says so.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 (REQ-21 (c)).
- **Sources.** B §F (:534–:548), §H F (:602); B-CK3 §5.4 (:382); MRA W13; PREREG §3 G1.

### LW-10. The plant's analysis rules and wording
- **Question.** Adopt B's plant fixes F2 and F4–F8, and C's R8.2, R8.3 and R8.5, before any plant draw is computed?
- **Options.** Adopt each, or edit it.
  - F2 and R8.2: compute the planted-cell ranks of every text-only scorer (L1, H1, H2a/b, DataShield-style, the classifier) in the REQ-3 pass, and publish them before the pilot as "construction checks". Only A1 and Self-Inf-N-style count toward "finds a known cause".
  - F4: the exact dilution-matched decomposition, P(first among m competitors) = C(N − r, m) / C(N − 1, m). "Diagnosis scales with M" may cite only the options effect at a fixed share.
  - F5: Λ per planted row, with its interval, labelled a per-row average.
  - F6: a $0 relocation replay over every eligible 37-row leaf (about 64; I: B-CK11 F6).
  - F7: a scored-only refusal decoy of 37 S-pool rows in a second sealed leaf. It needs append-only decoy labels before any plant draw. The label form is open (RC-21): B §G F7 names one label, `stage1-plant-decoy-v1`; the builder extract names three (`stage1-plant-decoy-rows-v1`, `-unit-v1`, `-leaf-v1`; EXTR §5). The lead fixes one form before the append; recommended (I): the decoy labels of EXTR §5. Whether A1's pass can score rows outside its corpus is UNVERIFIED.
  - The pilot interval (S-17): seed-paired on 1101–1103 (J = 3, 2 df), with a prompt part only under HB; every main-sweep arm is also reported against Gate A's a0 at the same seed, and contrasts against a0_plant carry "comparator selected by the pilot gate" (DRAFT §8.2, §8.6).
  - F8: if the pilot stops, still publish F2's ranks.
  - R8.3: record the prediction "the classifier ranks the planted leaf first at M = 128", with its pre-set reading.
  - R8.5: reject MRB's He-style plant (A1 would find it by construction). Correct the wording to "PKU red-team prompts with PKU-safe, non-refusing answers", not "benign-looking" (B-CK11 N5).
  - B-CK11 N6: the runs-only replay states that, at M = 32 and 128, the competitors' Λ come from a model.
- **Recommended default.** Adopt all. They change no T1 file, plant row, cell, draw or seed (B:554).
- **Cost.** $0.
- **Decides:** LEAD (the headline wording is UW-15). **Deadline:** W1 (REQ-21 (g), (j), (k); REQ-8; `labels.json`).
- **Sources.** B §G (:552–:572), §H G1 (:603); C R8.2, R8.3, R8.5 (:408–:414), C-f (:505); B-CK11 §3 N2, N5, N6 (:129–:135), §4 (:137–:168).

### LW-11. The placement statistic for planted menus (conflict C-k)
- **Question.** Which measured statistic places a diagnostic on the planted-menu prediction grid?
- **Options.** (a) ADD L15 (7) as written: the plant's top-k hit at each M. (b) B F3: the row AUC of the plant rows against the Dolly rows, with a bootstrap 90% interval; the top-k hit is secondary. The row AUC is the grid's own parameter (AUC = Φ(μ/√2), ADD L15 (6)).
- **Recommended default.** (b): a single top-k hit fits every grid point at M = 8 (R: B-CK11 §2.3). (b) edits the lead's own L15 (7). Also add the content classifier as a named diagnostic in the planted-menu predictions; its c_d enters as a point on the c_d/c0 curve, placed by its measured cost (C R8.4).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1-P.
- **Sources.** B §G F3 (:557); C R8.4 (:412), C-k (:510); ADD L15 (6), (7) (:271–:279); B-CK11 N3 (:131).

### LW-12. Additions to REQ-17's settings
- **Question.** Add three noise inputs to the selector's generative model before its predictions freeze?
- **Options.** Add each, or not.
  - B A7: draw cell noise as a shared seed shift plus an arm-specific shift, with the same-seed correlation ρ on a fixed grid {0, 0.67}, plus a 2 × SD sensitivity for one option. 0.67 is PREREG §2's pre-Gate-B "low" scenario, not a fit to wave 0a. L15 (1)'s per-arm SDs of 2.65 and 3.85 pp stay (R: ADD:249).
  - B-CK11 N4: cell-level heterogeneity τ for the planted menus, as a sensitivity, by a rule fixed now.
  - C's REQ-17 row: O's noise inputs, that is the prompt-clustered SE against θ0 (3.98–4.22 pp at 100 prompts; M: C-OR §4) and the U–O correlation, scaled to 500 prompts if O-ext runs.
- **Recommended default.** Add all three. A7 edits the lead's L15 (1), and it was proposed after the noise gate, so REQ-21 (m) lists it. Until the lead adopts A7, the builder's default is L15 (1) (ρ grid {0}), with {0, 0.67} behind a switch; choosing the rule by an average over ρ is a new rule that only comes with A7 (EXTR W1-14 item 4; RC-18).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1-P.
- **Sources.** B §A.12 REQ-17 row (:230), §H A7 (:587), §I (:624); B-CK11 N4 (:132); C §4 REQ-17 row (:472); ADD L15 (1) (:247–:252).

### LW-13. The SE inside REQ-16's feasibility screen
- **Question.** Does REQ-16's screen take O's and L's SE from the HB form (prompt part included), with LW-06's bound?
- **Options.** (a) Yes (B A8). This edits ADD L16's scope sentence ("still estimated from the replay's pooled residuals"). (b) Keep L16's sentence as written.
- **Recommended default.** (a), with O against θ0 and O's SE convention from LW-03 (C's REQ-16 row).
- **Cost.** $0.
- **Decides:** LEAD (it edits the lead's own L16). **Deadline:** W1-P.
- **Sources.** B §A.12 REQ-16 row (:231), §H A8 (:588), §I (:625); C §4 REQ-16 row (:471); ADD L16 (:292).

### LW-14. How REQ-18's predictions are scored, and Llama's replay
- **Question.** Fix now how REQ-18's predictions are scored, and check that the frozen Llama cell rules ask only for trials that Gate B-lite runs?
- **Options.** Scoring: (a) per unit, by a proper scoring rule (Brier and log scores; the regret's place in its predictive interval), labelled "a consistency check with one menu"; (b) pass or fail on one realized menu. Llama trials: if a frozen rule asks for a trial that Gate B-lite does not run (for example φ < 1, or a promoted unit outside wave 2), choose (i) restrict the Llama predictions to wave-1 quantities; (ii) pre-register extra Llama wave-2 runs (+0–4 runs); or (iii) score only the feasible cells.
- **Recommended default.** (a) and (i) (B-CK11; LLB L5). Also test the pick rule ("at least 2 full-run seeds") against Llama's seed map; fix the truth (the empirical-Bayes-shrunk G over all Gate B-lite seeds); and state the noise mismatch: Llama's seed SD of U is 4.34 pp, above OLMo's high case of 3.85 pp (R: LLB §15 item 7, :334).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1-P.
- **Sources.** B-CK11 §5 W14 (:170–:187); B §B.6 order 5 (:341); LLB §15 (:323–:338), L5 (:358); PLAN-S:132; BRIEF REQ-18 (:111).

### LW-15. The contents of C-lean (A LQ27)
- **Question.** Does the lean evaluation C-lean also hold the task-loss pass and the 100 greedy over-refusal answers that the selector's screen needs?
- **Options.** (a) Yes. A lean R arm is then about 870 s ≈ 0.30 FRE; the 100 over-refusal answers take about 330–371 s and their guard about 17 s (E: A §C.5; range corrected by A-RV R7). (b) No, as PLAN-S:202 words it: about 480 s ≈ 0.16 FRE, and the screen uses O and L at their full-evaluation cost.
- **Recommended default.** (a) (A). (I) (a) adds to PLAN-S:202's wording but does not contradict it. If the lead reads it as a change to the approved plan, it becomes a USER item.
- **Numbers.** c0 under (b) is about $0.24 at $1.79/h, below PLAN-S:202's "about $0.3–0.6"; c0 under (a) is about $0.43, inside it (M: A-RV N4).
- **Cost.** $0 now. It sets the c0 job (LS-15).
- **Decides:** LEAD. **Deadline:** W1-P.
- **Sources.** A §C.5 (:326–:329), §Q.1 W1-P table (:510–:516); A-RV R7, N4 (:113, :129); PLAN-S:202.

### LW-16. The cost-unit definitions
- **Question.** Confirm the cost units that REQ-18's curves in c_d/c0 use?
- **Options.** Confirm each, or edit it.
  - LQ25: 1 FRE = 2,934 s, the median job slot of the three wave-0a R arms (about $1.46 at $1.79/h; M: A §C.3). Pod overhead is excluded and reported apart. It is fixed at the W1-P commit from the three wave-0a ledgers and never re-estimated. PLAN-S D3 freezes the other cost rules (LQ30, LQ32–LQ35) and does not change FRE or the prices (RC-08: revision 1 said "fixed at D3", which comes after the predictions that use it).
  - LQ26: C-full's stage list: every in-job stage, among them greedy generation of all 468 evaluation prompts (R: `runner.py`:627, corrected by A-RV R1). HarmBench and Granite pods, pod overhead, backups and storage are reported apart.
  - LQ28: the lean per-answer prices are frozen at the W1-P commit from the wave-0a ledgers and never re-estimated (RC-08).
  - LQ29: c0 = one real job: a cold start, full training of an R arm, and exactly the C-lean evaluation of LW-15.
  - LQ31: the unit is 1 FRE under C-full and the measured c0 under C-lean.
- **Recommended default.** Confirm all, and tag LQ25, LQ26 and LQ28 W1-P, as A-RV N1 recommends: under LQ31, 1 FRE is the C-full unit of REQ-18's curves.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1-P.
- **Sources.** A §C.3–§C.6 (:314–:334), §Q.1 notes (:518); A-RV R1, N1 (:85–:88, :126); ADD L15 (3) (:261–:265); FOCUS:78 (U3 (a)).

### LW-17. The token-matching ruling (A LQ47)
- **Question.** Record that ADD §5 item 1 (a token-axis dose analysis, report only, and no token-matched arm) is the ruling that PAPER decision 26 asks for, and say whether it counts as "a token-matched analysis beside the row-matched one"?
- **Options.** (a) Yes, it counts; then UW-14 (a) stands as the recommendation. (b) It does not count; then the title goes back to the user as a plain USER item (A-RV N2). (c) Rule otherwise, for example token-matched removal arms (new arms; no draft costs them).
- **Recommended default.** (a). The cost section's sentence on "compute-matched" must agree (A §C.10). MRA W8's point (charging 1 FRE of training under-charges the add arms, which train about 15% more steps) gets one sentence (A §N item 4).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 (A-RV R8: the record is REQ-21, a W1 record).
- **Sources.** A §C.1 LQ47 (:302), §C.10 (:364–:367), §N items 1, 4 (:481, :484); A-RV R8, N2 (:114, :127); ADD §5 item 1 (:320); PAPER decision 26 (:240); MRA W8 (:177).

### LW-18. Build REQ-12 and REQ-13 before wave 1? (BRIEF U2)
- **Question.** At the named point after Part G, does the lead build DataShield-style (REQ-12) and Self-Inf-N-style (REQ-13), or record them as post-Gate-B exploratory?
- **Options.** (a) Build both. (b) Build one. (c) Build none; REQ-21 (l) records them as post-Gate-B exploratory before wave 1.
- **Recommended default.** Decide by plan usage at that point (ADD L1). The user has not answered U2 ("is extra plan usage on?"; FOCUS:96, :125 item (8)), and the D5 entry keeps the brief's default (FOCUS:78). If the user answers U2 before that point, the lead uses the answer.
- **Cost.** About 3–5 h of build effort (E: BRIEF:153); $0 marginal for Self-Inf-N-style scoring (R: BRIEF REQ-13).
- **Decides:** LEAD (under the user's 9 Oct item (9)). **Deadline:** W1 (REQ-21 (l) before the wave-1 launch).
- **Sources.** ADD L1 (:21); BRIEF U2 (:190), REQ-12–REQ-13 (:95–:97), "Lead steps" (:165); FOCUS:78, :96, :125 item (9).

### LW-19. How candidate additions enter the W1 record
- **Question.** Commit every candidate addition's outcome-free rule text now as a conditional item, and let none of them hold wave 1 except REQ-23?
- **Options.** (a) Yes (C R0.1, R0.2). (b) Commit only items that the user has already approved; the rest become post-Gate-B exploratory if added later.
- **Recommended default.** (a). The text says "runs only after the user's yes and a funding event". The items: SR, S6, B↓LR, SRJ, the prefill probe and its headroom reading, V1, V2a, O-ext N (H only if the user says yes to UW-07b), in-domain refusal, HB-4, F9's extra plant locations, and the references on six seeds (US-01). The yes must come before any newly run stage-1 cell's outcome is read (C VF-7; RC-15: six of the 50 primary cells are reused units whose values were read, so "any stage-1 outcome" is already false). **The reading of PLAN-S:239 (RC-28), recorded in REQ-21 (h):** a conditional item whose outcome-free rule text is committed before wave 1 is not "added later"; a yes after Gate B's verdict is disclosed for each item, and the item stays outside P1–P6. The W1 record shows the reading to the user. If the lead does not accept it, each such item that the user approves after a Gate B unit outcome is labelled post-Gate-B exploratory. Label names go into the rule text, and each `labels.json` entry is appended with the code that uses it, because L13 (3)'s test fails on an unused entry (C VF-5). REQ-23 is a listed commitment, so wave 1 waits for it (C VF-4; UW-18).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 (REQ-20; REQ-21 (g), (j), (l)).
- **Sources.** C R0.1, R0.2 (:145–:152), §4 REQ-2 row (:468); FOCUS:125 items (6), (9); FOCUS:251; BRIEF "Inputs fixed" (:20).

### LW-20. Build REQ-23, the per-row content-classifier scorer
- **Question.** Add REQ-23 to the W1 build: a pinned Part C script that writes per-row normalized Unsafe scores (prompt and response) by read-only use of `GuardScorer.label_scores`, for the 4,800 rows and the 75 plant rows?
- **Options.** (a) Build it in the single builder session (ADD L1; C VF-16). (b) Do not build it; then UW-18 applies.
- **Recommended default.** (a). It fills a gap: PLAN-S §5.4 and §6 score "the classifier", but no REQ makes per-row classifier scores, and Gate C keeps unit means only (R: C-EM §4).
- **Cost.** $0 to build; about $1 to run (E: C R8.1). The run is part of the approved plan (the content classifier is a planned scorer, PLAN-S:168, and every scorer is charged in full, PLAN-S:203). It is paid from stage 1's funding event (US-07), never from the Gate B balance or on a Gate B kit pod (BRIEF T4). No separate USER item (RC-20).
- **Decides:** LEAD. **Deadline:** W1 (code and settings hash).
- **Sources.** C R8.1 (:403–:406), §4 REQ-23 row (:485); C-EM D13 (:302); PLAN-S:168, :181.

### LW-21. A1's justification and two scored-only variants
- **Question.** Keep A1 as built, record why, and fix the rule texts of V1 and V2a?
- **Options.** (a) C R7.1, R7.4 and R7.5. Keep A1; REQ-21 (h) records the justification. V1 = A1's score with `adam_score` in place of the cosine, from the stored values; a Part G report (new REQ-25), never an arm. V2a = a0-1101's own sampled answers to the 64 anchor prompts as the harmful side, scored only, with the pre-set reading "if its top 600 has a Jaccard below 1/3 with A1's, the claim bound is mandatory and V2a is the first secondary arm if funded". (b) Drop V1 or V2a.
- **Recommended default.** (a). V1's rule text must reach the record before the lead's first real read of `rows.jsonl` (C VF-18). If it lands later, REQ-21 (m) says so and V1 is labelled post-T1. The T1 A1 contract does not change. V2a's spend is US-16.
- **Cost.** V1 $0; V2a $5.6–7.1 (E: C-EM §3.3).
- **Decides:** LEAD. **Deadline:** W1 (V1 before the first real `rows.jsonl` read).
- **Sources.** C R7.1, R7.4, R7.5 (:371–:393), §4 REQ-25 row (:487); C-EM D10, D11 (:299–:300); ADD §5 item 2 (:321).

### LW-22. What must land before the T1 commit
- **Question.** Does anything still need to land before the lead commits the T1 bundle? (RC-25: its verification returned fix_required, one blocking defect, and the lead ruled the fixes (ADD §4, 16 Oct 21:20 UTC); that the fixes are applied and checked again is not recorded in FOCUS at `5957a37`, UNVERIFIED here.)
- **Options.** (a) Commit T1 now. No plant change is recommended (UW-16 (b)). F7's decoy label is appended later, before any plant draw (append-only, ADD L13 (7)). V1's rule text goes into the REQ-21 draft before the first real `rows.jsonl` read. (b) Hold T1 until UW-16 is answered.
- **Recommended default.** (a), unless the user picks UW-16 (a): a plant change after T1 re-opens T1 (C VF-19). Add ADD §4 item 8's scope note to the T1 commit message: the golden test and the A1 contract are defined on engine X, and after engine round Y they need a new pin.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1, now. At 00:30 UTC on 17 Oct the T1 bundle was not committed in the main checkout (R: `git log`; no `scripts/stage1/`).
- **Sources.** C Q12 (:564), VF-18, VF-19 (:621–:622); ADD §1 L1 (:23–:39), §4 (:303–:314); FOCUS:75.

### LW-23. HarmBench in stage 1: HB-1 to HB-3
- **Question.** Adopt C's HarmBench rules?
- **Options.** Adopt each, or edit it. HB-1: stage 1 uses the Gate B HarmBench pipeline byte for byte, named "HarmBench's Mistral-7B validation classifier, which reads the first 512 classifier tokens of each answer". HB-2: per-arm reports (the clipped share; E_HB and Λ_HB on the 35 HarmBench prompts beside all 200; agreement and κ with Qwen3Guard per bank; Λ_HB on unclipped answers only; greedy beside sampled). HB-3: the claim rule gates on all 200 prompts; the 35-prompt subset has an SE about 2.4 times larger (E: C R5c.3).
- **Recommended default.** Adopt all. MRB W15's premise (no window) is refuted (R: `scripts/gate_b_mac_judges/harmbench_files.py`, via C:355).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 (rule text); S1 (computed by the stage-1 reading B16).
- **Sources.** C R5c.1–R5c.3 (:357–:361); C-OR D7 (:340); FOCUS:244.

### LW-24. Other report-only endpoint rules
- **Question.** Fix now the rule texts of the report-only endpoints that C and B-CK11 propose?
- **Options.** Adopt or edit each.
  - SRJ, the StrongREJECT evaluator: secondary and report-only; the reference "last 512 tokens" truncation is primary; harm density reported; its first check scores θ0 and the Gate A a0 seeds only, with the reading "if |E_SRJ| is less than twice the a0 seed SD, report it once as descriptive"; it runs only after US-13 (C R5a.1, R5a.3).
  - The prefill probe's design (prefixes P-a and P-b; greedy; 512 new tokens; the recovery share; the Gate B HarmBench pipeline unchanged), as a conditional item (C R5a.4).
  - In-domain refusal's rule text, as a conditional item (C R5b.4; US-12).
  - Selectivity stays report-only (C R1.6). Partial refusals are reported per arm (C R5b.5).
  - "Controversial counted Unsafe" is carried from Gate B as a sensitivity corner (B-CK11 §5 Q7).
  - The length-reweighted U is labelled a decomposition with a fixed reference length distribution, never "the effect adjusted for length" (B-CK11 §5 Q15).
- **Recommended default.** Adopt all. None changes a primary test.
- **Cost.** $0 for the texts.
- **Decides:** LEAD. **Deadline:** W1 (REQ-21 (e), (f)).
- **Sources.** C R1.6 (:199), R5a.1 (:288–:295), R5a.3 (:299–:305), R5a.4 (:307–:312), R5b.4 (:349), R5b.5 (:351), §4 REQ-21 (f) row (:479); B-CK11 §5 (:170–:187); ADD §5 item 3 (:322).

### LW-25. SR and S6 construction details (conditional on US-10)
- **Question.** Fix SR's and S6's construction details in their conditional rule text?
- **Options.** Adopt C R4.4, or edit it. SR uses S4's 48 kept rows and their untuned refusals. A sealed draw gives 24 rows with k = 0 and 24 with k uniform on [1, min(100, |h|)]. The prefix h is the same PKU record's unsafe response, read by the row's `line`. Prefix checks and a near-duplicate check run; a failing row gets k = 0, counted. S6 copies S4's first kept row 48 times with distinct ids. Deviation tables go into REQ-21 (h). REQ-6 records each S-pool row's PKU `line` and its unsafe companion's index, text-free (UNVERIFIED whether it already does). REQ-7 tests that S6's copies differ only in their ids.
- **Recommended default.** Adopt (C; C-TM A3, A5).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 (conditional rule text); S1 (code: new REQ-24, and SR's engine field).
- **Sources.** C R4.4 (:261–:268), §4 REQ-6, REQ-7, REQ-24 rows (:469–:470, :486); C-TM A3–A5 (:329–:331).

### LW-26. Texts the W1 record must carry
- **Question.** Put these fixed texts into the W1 record?
- **Items.** Q-P1, B+Qi's erosion lies nearer recipe B's than recipe G's (SPEC F4 as a B+Qi prediction risk; REQ-21 (i)). ADD §4 item 8's scope note. REQ-21 (h)'s readings of ambiguous phrases: the bound convention (LW-06), "f = 1" (LW-04), the H2a reading (ADD L6), L4's deviation line, A1's justification (LW-21), and SR's and S6's deviation tables (LW-25). The word "pre-specified", not "pre-registered", until REQ-20's manifest and REQ-21 are committed (B-CK11 §5 W1).
- **Recommended default.** Yes.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1.
- **Sources.** A §R.2.10 Q-P1 (:272), §Q.1 (:505); ADD L4 (:66), L6 (:106), §4 item 8 (:314); B-CK11 §5 (:170–:187); BRIEF REQ-21 (h), (i) (:121).

### LW-27. Engine round Y: build it now in a workspace?
- **Question.** Build engine round Y (Y1 the confirmation role, Y2 sealed bank subsamples, Y3 B+Qi, Y4 the certification tools) now in a hand-made workspace, and freeze it by hash before the merge?
- **Options.** (a) Yes. T4's text covers engine files, not workspace copies (Y decision 3). (b) Build it only after Gate B's last kit pod (REPLAN:116).
- **Recommended default.** (a) (Y). Y3 is due at the stage-1 freeze, and the slack is about 0–4 days (E: Y §0, §8). Whether a commit on a side branch is allowed under T4 is the lead's reading.
- **Cost.** $0 to build.
- **Decides:** LEAD. **Deadline:** W1 (Y's schedule starts the brief on 18–19 Oct; I).
- **Sources.** Y §0 (:21–:38), §4.3 (:181–:190), §8 (:280–:309), decision 3 (:335); BRIEF T4 (:65); REPLAN §5 (:95–:120).

### LW-28. Who builds B10–B17 and Y, and in which brief
- **Question.** Name the builders and the briefs for the S1 build items and for Y?
- **Options.** (a) Y's decisions 8 and 18: Specialized Implementation builds Y, and B12 and B17 move into Y; B10, B11 and B14–B16 stay in the S3 brief; the lead's read-only workflow verifies; if one chat builds both, the order against S3 is fixed. (b) A LQ1 as written: one S1 build brief for B10–B12 and B14–B17, after Gate B's last kit pod for B12.
- **Recommended default.** (a). It keeps FOCUS's rule that Specialized builds Safe LoRA's work with tests, reviewed before use (FOCUS:154), or the record states the change (A LQ1).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 for Y's brief (18–19 Oct; I); S1 for the S3 brief.
- **Sources.** A §0 LQ1 (:92); Y decisions 8, 18 (:340, :350); FOCUS:154.

### LW-29. Model-agnostic Part C scripts: when?
- **Question.** Make the stage-1 Part C scripts (and the builders) work for any model and manifest inside the W1 build, or later as new files?
- **Options.** (a) Later, as new files after the W1 commit, with a 1B parity test; the 1B scripts in REQ-21 stay unchanged (Y decision 12; P78 [LEAD] 8). (b) Inside the W1 build now. It changes REQ-3 and REQ-10 and adds work on wave 1's critical path. ALP L-7 asks to parameterize the builders by manifest "now", or to build Alpaca twins later.
- **Recommended default.** (a): wave 1 waits for the W1 build (FOCUS:125 item (6)).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 (it sets the W1 build scope).
- **Sources.** Y decision 12 (:344); P78 §12 [LEAD] 8 (:407); ALP L-7 (:857); REPLAN §5 prep item 2 (:115).

### LW-30. A W1 paragraph for the human label check
- **Question.** Commit a one-paragraph human-label-check (HLC) commitment in REQ-21 before Gate B wave 1, with the full protocol before block A?
- **Options.** (a) Yes (HR HD8 (a)). (b) Its own record before block A only; it is then labelled post-Gate-B and report-only.
- **Recommended default.** (a). It adopts no spend; the spend items are LA-07.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1.
- **Sources.** HR §13 HD8 (:394); PAPER decision 24 (:238).

### LW-31. Plan-B seed lists and plan-B statistics (new in revision 2; RC-07, S-15)
- **Question.** Fix the plan-B seeds and the plan-B form of the statistics before wave 1?
- **Options.** (a) The DRAFT's lists (§1.3): A1 and H1 1102–1110; S1 and S4 1102–1110; R 1101–1112, with draws d = 9–12 by the same frozen rule as d = 6–8 (`gate-b-random-removal-v1`, draw d at seed 1100 + d; R: BRIEF REQ-4; PREREG §1); a0 1101–1106 (needed for G_m, the τ_L comparator and the references; I). Under seed layout D1 (UW-03): R 1101–1110 (R: B §H A4). Statistics: S-a and HB fit the five plan-B primary arms only (48 cells, 43 df under S-a; M: `review_fixes_numbers_out.txt`); a0 stays outside the pool; three-member families; the familywise equivalence grade at α/3 per side (96.67%; M: `review_fixes_numbers_out.txt`). (b) Other lists.
- **Recommended default.** (a). The seed rule must be committed before wave 1 (R: FOCUS 8 Oct 13:53 UTC; PLAN-S:211). Building the d = 9–12 files at W1 is optional, because the draws are outcome-free.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 (REQ-21 (d)).
- **Sources.** PLAN-S:118; B §A.6, §H A4; BRIEF REQ-4; DRAFT §1.3, G-2; EXTR G-1.

### LW-32. Reuse of R_4 and R_5 (new in revision 2; RC-14)
- **Question.** If Gate B's extension runs R_4 and R_5 (same sealed edits, same seeds, engine X), does stage 1 reuse them as R at 1104–1105?
- **Options.** (a) Reuse (DRAFT §1.2; G-3). (b) Run new units.
- **Recommended default.** (a). Their values are read before S1, and whether they exist depends on Gate B's TOO CLOSE verdict, so REQ-21 (m) lists them (DRAFT §12.3 item (13); S-14).
- **Cost.** $0 if reused.
- **Decides:** LEAD. **Deadline:** W1.
- **Sources.** DRAFT §1.2, Appendix C G-3.

### LW-33. S-a's prompt term for O against θ0 (new in revision 2; RC-14, S-20)
- **Question.** Under S-a, how does the prompt-clustered SE of O(m) − O(θ0) enter the feasibility bound?
- **Options.** (a) V = s²_pool,O/J_m + max(0, MS_P − MS_E)/(P·J_m), from the J_m × P table of y(m, j, p) − y(θ0, p), with Satterthwaite df (DRAFT §6.4; S-20). (b) The prompt-clustered SE of the seed-averaged per-prompt differences only (revision 1's text), which omits the seed term (about 1% of the variance at the Gate A values; I).
- **Recommended default.** (a).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1, before REQ-19 runs.
- **Sources.** DRAFT §6.4, Appendix C G-4.

### LW-34. REQ-21's record file name (new in revision 2; RC-14)
- **Question.** Keep the name `research/experiments/2026-10-16-stage1-commitments.md` (BRIEF REQ-21)?
- **Recommended default.** Keep it: 20261016 is a task id, and the record's header gives the real `date -u` time (R: ADD L2).
- **Cost.** $0. **Decides:** LEAD. **Deadline:** W1.
- **Sources.** BRIEF REQ-21; ADD L2; DRAFT Appendix C G-6.

### LW-35. Block A stays sealed until block B (new in revision 2; S-3)
- **Question.** Seal block A's outcomes until block B is complete?
- **Options.** (a) After block A, read only its cost ledgers, completion records and adapter fingerprints; seal its U, HB, O, task-loss and coherence outputs by SHA-256 until block B is complete or a recorded decision ends stage 1 without block B; the block-B funding decision and the "stop and ask" report use no block-A outcome; if block B never runs, analyse block A alone with every label marked "block A only (3 seeds per method arm)" and its MDE printed. (b) No seal.
- **Recommended default.** (a). PLAN-S:76 says block A is kept "but no claim is read before block B, because 3 seeds cannot give equivalence bounds", and PLAN-S:232 says every block starts on a funding event, never on an outcome, and only complete blocks are analysed. Without a seal, the block-B funding decision could follow block A's outcomes (S-3). REQ-21 (h) records (a) as the reading of the two lines.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** W1 (rule text).
- **Sources.** PLAN-S:76, :232; FOCUS 8 Oct 13:53 UTC ("stop and ask after every stage"); DRAFT §1.3, §11.

---

## 3. USER and USER-CONFIRM items due at S1

### US-01. References on all six a0 seeds (B's package)
- **Question.** Run the eval-only references (safety prefix, adapter scaling, Safe LoRA) on all six a0 adapters with a λ = 0.9 point, and recipe G and B+Qi at seeds 1102–1107?
- **Options.** (a) Ambitious default: SP, scaling (0.75, 0.5) and Safe LoRA at a0 1101–1106 (1101–1107 under D1); λ = 0.9 added; recipe G at 1102–1107 (the 8 Oct units at 1102–1103 reused if allowed); B+Qi at 1102–1107. (b) Fallback: the approved references, that is SP, scaling and Safe LoRA at a0 1101–1103 and recipe G at 3 seeds (FOCUS:243, :151–:154); their "beats" tests use unpaired Welch and are descriptive.
- **Recommended default.** (a) if the user confirms UW-01, with (b) if block B is funded without this increment. **Current rule in force until the user decides:** (b). Recipe G at 6 seeds changes FOCUS:243's "recipe G at 3 seeds".
- **Numbers.** With 3-seed references, MRA computes a 6-against-3 MDE of about 5.4 pp (R: A §N item 3).
- **Cost.** Six seeds +$22.4–24.8; λ = 0.9 +$11.5–12.9; recipe G at 1104–1107 +$8.0–8.3; about $42–46 in all, with pod overhead and × 1.25 (M: B NUM). Under D1, +$7.5–8.3 and +$1.7–1.8 more (M: B NUM).
- **Decides:** USER-CONFIRM. **Deadline:** S1 (at the block-B funding event). Its rule text enters the W1 record only if the lead fixes the reference tests with the family (B §0 row D).
- **Sources.** B §D.1 (:417–:424), §D.6 (:460–:477), §H D2 (:597), §I (:616); A §R.0.8 (:136), LQ14 (:195), §N item 3 (:483); MRA W3 (:97); MRB W2 (:83).

### US-02. References in block A or block B (A UQ8)
- **Question.** Keep every reference in seed block B, as PLAN-S:222–223 says, or move SP, scaling and Safe LoRA into block A?
- **Options.** (a) Block B, as approved. (b) Block A: 12 eval-only jobs (15 with US-03) plus 3 regeneration jobs on 4–5 pods.
- **Recommended default.** (a). The reason for (b): without block B the paper has no "beats model-level repair" sentence (A, RQ concern (f)).
- **Cost.** (b): about $20–25, or $25–31 × 1.25 (C: A FIX; A-RV M4 checked $19.80–24.65 and $24.75–30.81).
- **Decides:** USER. **Deadline:** S1.
- **Sources.** A §R.0.8 (:136), UQ8 (:570); A-RV M4 (:45); PLAN-S:222–223.

### US-03. A second Safe LoRA point (A UQ9)
- **Question.** Add Safe LoRA at K = 12 (10.7% of the 112 adapted matrices) beside K = 39 (34.8%)?
- **Options.** (a) No: K = 39 only. (b) Yes.
- **Recommended default.** (a). The reason for (b): the paper's two fractions come from two models, and our fraction may not transfer.
- **Cost.** (b): 3 evaluations, about 2.8 FRE, $4.1; $4.8 with one pod's overhead; about $6.1 × 1.25 (C: A FIX; "$4.8" corrected from "$4.9" by A-RV R6; M: this list, $4.85).
- **Decides:** USER. **Deadline:** S1.
- **Sources.** A §R.1.3 row 10 (:166), UQ9 (:176), §C.9 (:356); A-RV R6 (:112).

### US-04. The base-model download for Safe LoRA (A UQ1)
- **Question.** Approve the download of `allenai/OLMo-2-0425-1B` at `a1847dff` (Hugging Face; 5.94 GB; Apache-2.0; not gated) onto the stage-1 pod at setup, with nothing downloaded to the Mac?
- **Options.** (a) The user approves the named download. (b) The lead records that the user's 16 Oct "stop asking me for approval" covers it.
- **Recommended default.** (a). By precedent the user approves each new model download (RS C2, via A:178), and the lead read the 16 Oct instruction as "do the planned steps" (FOCUS:76).
- **Cost.** $0 (pod download time only).
- **Decides:** USER. **Deadline:** S1, before any Safe LoRA run.
- **Sources.** A §R.1.3 row 3 (:159), UQ1 (:178); FOCUS:76; PREREG:97–98.

### US-05. B+Qi's form (A UQ3)
- **Question.** Keep B+Qi as decided (recipe B with Qi et al.'s token-wise loss, no warmup, AdamW β1 0.9, constant LR), now that its weaker form is known?
- **Options.** (a) Keep it. (b) Also add a secondary "G+Qi" arm (recipe G plus the loss, 3 seeds). (c) If the binding check (LS-10) shows that B+Qi equals recipe B by construction, the lead proposes a change (for example Qi et al.'s β1 0.5, or G+Qi), and the user decides at the freeze.
- **Recommended default.** (a); no change without the user. C adds that B+Qi without warmup may be weaker than Qi et al.'s reference (C AMD-6, R5a.6).
- **Numbers.** With β1 0.9, the step-1 gradient keeps about 47%, 30% and 16% of the momentum at steps 2, 3 and 5; with β1 0.5, 33%, 14% and 3% (E: A §R.2.4, from QI FQ3).
- **Cost.** (b): about 3.2 FRE, about $6–7 (E: A UQ3).
- **Decides:** USER (the user approved the arm and "no warmup"; FOCUS:125 item (10), :225). **Deadline:** S1 (at the freeze).
- **Sources.** A §R.2.4 (:222–:228), UQ3 (:228), §R.2.8 (:267); C R5a.6 (:319), AMD-6 (:520); FOCUS:125, :148, :225.

### US-06. Candidate new references (A UQ7; C U-11)
- **Question.** Does the "opening hold" first-token loss, or the post-hoc one-shot patch ("Safety at One Shot"), become a reference arm?
- **Options.** (a) No change: the one-example patch stays "bounded in text, not built" (D5 = (a), FOCUS:78). (b) Add the opening hold; its citation is fetched by the OpenReview API first, and B+Qi's role is read again. (c) Add the one-shot patch as an S1 reference, using the options in BRIEF's D5-7 row for (b) and (c) (A-RV R14), or as a W1 rule if its example is chosen from our data.
- **Recommended default.** (a) until the user decides (ADD §5 item 4). One new fact for the decision: an API customer can start a job from a fine-tuned model, so the patch is in closed customers' menus (R: C-TM §2.1).
- **Cost.** Not costed; engine support UNVERIFIED (C R4.8).
- **Decides:** USER (a scope addition). **Deadline:** S1 (W1 if a patch example is chosen from our data).
- **Sources.** A §R.0.1 (:110), UQ7 (:569); A-RV R14 (:120); C R4.8 (:280), U-11 (:128); ADD §5 item 4 (:323); PAPER decision 27 (:241); BRIEF D5-7 row (:179).

### US-07. Stage 1's funding event and the freeze
- **Question.** At the stage-1 freeze, which money counts as stage 1's funding event for seed blocks A and B (and for stages 1b and 1c)?
- **Options.** No draft gives options. (I) The lead proposes a definition at the freeze, for example a named top-up or grant payment in the account, read before each block's launch.
- **Recommended default.** None recorded; the user's 9 Oct list left it open (FOCUS:125 item (8)). Every stage and block starts on a funding event, never on an outcome (FOCUS:253). References sit in block B, so without block B the paper has no "beats model-level repair" sentence (A UQ5). The freeze itself is the user's step, and it shows the user every S1 [LEAD] choice (A UQ5).
- **Cost.** Stage 1 about $56–98 (E: PLAN-S:230). The balance was $91.94 at 19:07 UTC on 16 Oct, and wave 1 needs $83.91 of it (R: FOCUS:76, :77).
- **Decides:** USER. **Deadline:** S1.
- **Sources.** A UQ5 (:567); FOCUS:125 item (8), :253; C VF-7 (:149); PLAN-S:222–223, :230.

### US-08. Certification pods before a funding event
- **Question.** May the X → Y (or X′) certification pods run before a funding event?
- **Options.** (a) Yes. (b) No: they wait for stage 1's funding event.
- **Recommended default.** None recorded; Y calls it "the user's open ruling" (Y decision 14; PLANF:234 item 14).
- **Cost.** About $3.0–3.7 at 1B (E: Y §0).
- **Decides:** USER. **Deadline:** S1 (certification comes before the stage-1 freeze).
- **Sources.** Y §0 (:34), decision 14 (:346).

### US-09. What the confirmation units read
- **Question.** Do the confirmation units read both the hidden subsample and the dev bank, as FOCUS:252 says?
- **Options.** (a) Both banks, as adopted. (b) The hidden read only. (c) The hidden read plus a lean dev read.
- **Recommended default.** (a), the adopted text, until the user decides. Y gives no recommendation.
- **Cost.** Reading both banks adds about 0.6–0.85 FRE per unit at 7–8B (E: Y §0); under option B, +$73–200 (E: Y decision 5). At 1B the added share is smaller (I).
- **Decides:** USER (it changes an adopted design point). **Deadline:** S1 (the confirmation rule is committed before stage 1; FOCUS:252).
- **Sources.** Y §0 (:35), decision 5 (:337); FOCUS:252; PLAN-S:215.

### US-10. SR and S6 add arms (C U-6)
- **Question.** Add a recovery-style add arm (SR) and a one-shot-style add arm (S6), 48 rows and 6 seeds each, in a new family P7 = SR − S4 and P8 = S6 − S4?
- **Options.** (a) Both, in the new family, read after the primary family at its own 5%; P1–P6 and their MDE do not change. (b) Both inside the primary family; P1–P6's MDE rises to about 5.1 pp for removals and 5.5 pp for adds (R: C-TM §3.6). (c) S6 only. (d) Neither.
- **Recommended default (ambitious; rests on UW-01).** (a), with C R4.3's pre-set fallbacks: money short → S6 only; SR's engine field not verified at S1 → SR as a 3-seed secondary arm with one-sided bounds; plan B → P7 and P8 do not run; S4 cannot fill 48 rows → SR on S1's rows. If SR runs, the prefill probe covers SR, S4 and a0 (C R4.5).
- **Notes.** (b) changes the primary family and D5 = (a)'s "Holm over 6" (R: FOCUS "D5 DECIDED: (a)", 16 Oct 12:15 UTC), so it is USER and needs the user's answer by W1 (RC-12). S6 touches US-06. SR needs a loss-free prefix field in the engine round that carries B+Qi (C VF-15).
- **Cost.** About $12–14 each (E: C-TM §3.7).
- **Decides:** USER (package USER-CONFIRM), as C U-6 marks it (RC-12); option (b) USER. **Deadline:** S1 (the yes, before any newly run stage-1 cell's outcome is read; RC-15); W1 only for option (b). The conditional rule text is the lead's, at W1 (LW-19, LW-25).
- **Sources.** C R4.1–R4.5 (:247–:270), U-6 (:123), AMD-5 (:519); B §B.6 family 1c (:337); C-TM A1, A2, P1 (:327–:333).

### US-11. B↓LR as a sixth reference (C U-5)
- **Question.** Add recipe B at LR 5e-5 on the unchanged data (B↓LR) as a sixth reference on OLMo-2-1B?
- **Options.** (a) 6 seeds. (b) 3 seeds. (c) No.
- **Recommended default (ambitious; rests on UW-01).** (a), with fallback (b) if money is short. Build: a config whose diff against recipe B is the `lr` key only, committed by explicit path after Gate B's last kit pod (C R3.5, VF-17); seeds 1101–1106 (the a0 seeds; C R3.5) or 1102–1107 (B §D.1 table), decided with LS-11 after UW-02, by the same reason as B+Qi's seeds (RC-22). B↓LR is read on the frontier matched on task loss, because it will likely fail τ_L (C R3.4; B AMD-4).
- **Cost.** About $12–14 at 6 seeds, $6–7 at 3 (E: C-TM §2.5).
- **Decides:** USER (ladder USER-CONFIRM), as C U-5 marks it (RC-12). **Deadline:** S1 (references are S1 items).
- **Sources.** C R3.4, R3.5 (:228–:235), U-5 (:122), AMD-4 (:518); B §B.6 AMD-4 (:347); C-TM T2, T3 (:323–:324).

### US-12. In-domain refusal (C U-4)
- **Question.** Measure greedy refusal on the 200 Dolly task prompts (128-token cap; lexicon and Qwen3Guard), report only?
- **Options.** (a) Run it. (b) State it as a limitation.
- **Recommended default (ambitious; rests on UW-01).** (a), fallback (b). Teacher-forced task loss cannot see a model that refuses ordinary requests at generation time (C R5b.4).
- **Cost.** About $5–13 for 72 units (E: C-OR §5.6).
- **Decides:** USER (ladder USER-CONFIRM), as C U-4 marks it (RC-12). **Deadline:** S1 (the run); its rule text is in LW-24 at W1.
- **Sources.** C R5b.4 (:349), U-4 (:121); C-OR D6 (:339).

### US-13. Access and download for the StrongREJECT evaluator (C U-7)
- **Question.** Request Gemma access, accept the Gemma terms, and approve a download of about 5.1 GB (the `google/gemma-2b` base and the `qylu4156/strongreject-15k-v1` adapter) for SRJ?
- **Options.** (a) Approve. (b) Skip SRJ; the harm-weighted point becomes a limitation.
- **Recommended default.** (a) (C). The adapter card states no licence (R: C R5a.2). The user should know this before accepting.
- **Cost.** $0 on the Mac; about $2–4 for the 72 stage-1 units on planned judge pods (E: C-EM §1.4).
- **Decides:** USER. **Deadline:** S1, before any SRJ score.
- **Sources.** C R5a.2 (:297), U-7 (:124); C-EM D2 (:291).

### US-14. The prefill probe (C U-8)
- **Question.** Run the prefill headroom check, and then the probe at which scope?
- **Options.** The headroom check: θ0 and a0-1101, prefixes P-a and P-b at k = 5 and 20, one pod job. Its pre-set reading: if θ0's recovery share is within 10 pp of a0-1101's, the probe has no headroom at 1B and is reported once as a limitation. The scope: full (3 settings on every unit), reduced (1 setting on every unit, or 3 settings on about 25 units), or none.
- **Recommended default (ambitious; rests on UW-01).** The headroom check, then the full scope; fallback the reduced scope; a limitation if there is no headroom.
- **Cost.** Headroom check $1.1–1.6; then $26–39 (full) or $9–14 (reduced) (E: C-EM §2.4–§2.5).
- **Decides:** USER (scope USER-CONFIRM), as C U-8 marks it (RC-12). **Deadline:** S1.
- **Sources.** C R5a.4, R5a.5 (:307–:317), U-8 (:125); C-EM D6–D8 (:295–:297).

### US-15. HarmBench's test classifier as a sensitivity (C U-9)
- **Question.** Run `cais/HarmBench-Llama-2-13b-cls` as a report-only sensitivity on each primary unit's 200 greedy answers?
- **Options.** (a) Run it, after its own parity or known-answer rule. (b) Skip it.
- **Recommended default (ambitious; rests on UW-01).** (a), fallback (b). C's view: it has the lowest value per dollar in that draft, so skip it first if money is short.
- **Cost.** A download of about 26 GB plus pod minutes; run time UNVERIFIED (R/E: C R5c.4).
- **Decides:** USER (ladder USER-CONFIRM), as C U-9 marks it (RC-12). **Deadline:** S1 (download, parity rule and run); its rule text is conditional at W1 (LW-19).
- **Sources.** C R5c.4 (:363), U-9 (:126); C-OR D8 (:341).

### US-16. V2a's spend (C U-10)
- **Question.** Spend money for V2a's scored-only pass, and later for V2a as a 3-seed arm if its pre-set reading fires?
- **Options.** (a) Run V2a on a planned stage-1 pod. (b) Report counts only.
- **Recommended default.** (a) (C).
- **Cost.** $5.6–7.1 for the pass; $5–6 for the 3-seed arm (E: C-EM §3.3).
- **Decides:** USER. **Deadline:** S1 (the pass); later (the arm).
- **Sources.** C R7.5, R7.6 (:387–:395), U-10 (:127).

### US-17. A norm-matched control for Safe LoRA (A UQ6, LQ15)
- **Question.** Add a control that scales the same K matrices' updates by ρ_i without turning them, to separate "direction" from "shrinkage"?
- **Options.** (a) Offer it as secondary, only if funded. (b) Do not offer it.
- **Recommended default.** (a) (A LQ15).
- **Cost.** About 2.8 FRE at K = 39, about $4 (E: A §R.1.9).
- **Decides:** USER (spend). **Deadline:** S1.
- **Sources.** A §R.1.9 (:204), UQ6 (:568).

### US-18. If the B+Qi engine change is late
- **Question.** Only if X′ (B+Qi) cannot be certified by stage-1 block A: amend FOCUS:225 to "B+Qi committed before block B"?
- **Options.** (a) Amend it. (b) Do not amend it; the stage-1 freeze waits for X′.
- **Recommended default.** No amendment unless X′ is late (Y §8, "If Y is late"). Block A can run on X either way.
- **Cost.** $0.
- **Decides:** USER (conditional). **Deadline:** S1.
- **Sources.** Y §8 (:303–:309), decision 1 (:333); FOCUS:225.

---

## 4. LEAD items due at S1

### LS-01. The engine round for B+Qi, and its merge point
- **Question.** In which engine round does B+Qi enter, and when does that round merge into the working branch?
- **Options.** (a) Y's plan: one round Y (Y1–Y4) with the pre-set split rule (if Y1 and Y2 lag, freeze Y3 + Y4 + Y2's dev path as X′ for the stage-1 freeze); merge after Gate B `--final`, its backups and pods C1–C3 (Y decisions 1, 2). (b) A LQ19: X′ merges after Gate B's last kit pod, with any other engine change, under one certificate.
- **Recommended default.** (a). With Y in the tree, the reading's own test fails during the `--final` procedure (R: Y §4.3).
- **Cost.** Pods about $3.0–3.7 at 1B (E: Y §0); US-08 decides whether they may run before a funding event.
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §R.2.7 LQ19 (:264); Y §0 (:21–:38), §4.3 (:181–:190), decisions 1, 2 (:333–:334).

### LS-02. What the engine certificate checks
- **Question.** Which units and checks certify the engine change for stage 1?
- **Options.** (a) A LQ20: recipe B a0@1101 train-only reproduces X's q and e1 fingerprints; B+Qi train-only twice; B+Qi's step 1; plus one re-evaluation of an X unit on X′, with equal U labels and an equal task loss. (b) Y's pods C1–C3 on one pod: a complete-unit determinism control, a B+Qi smoke test and the c0 lean job. C1's unit is an R_1101 replicate after `--final` in its own run root, recorded as outside Gate B (or a paired X/Y run of a new unit, about +$1.5). Named non-insert edits of training-only symbols are accepted if the goldens and C1 are bit-identical (Y decisions 16, 17).
- **Recommended default.** (b), which includes (a)'s evaluation part. C1 is not an attempt of R_1 under PREREG:108.
- **Cost.** LQ20's extra evaluation about 0.93 FRE ≈ $1.36, and its certificate pod about $2.7–2.8 (C: A FIX; "$2.7–2.8" corrected from "$2.7–2.9" by A-RV R6). Y's C1–C3 pod about $3.0–3.7 (E: Y §0).
- **Decides:** LEAD. A-RV N5 notes that a strict reading could make LQ20's $1.36 a USER spend; it is part of a planned certificate. **Deadline:** S1.
- **Sources.** A §R.2.7 LQ20 (:265); A-RV R6, N5 (:112, :130); Y §5 (:192–:243), decisions 16, 17 (:348–:349); PREREG:108.

### LS-03. Which runs use the new engine
- **Question.** After certification, do all pods use the new engine, and how are the Gate B tests that need the live engine X handled?
- **Options.** Runs: (a) every pod launched after certification (one engine in the tree); (b) only B+Qi, c0 and confirmation. Tests: (a) rewrite them to read the stored X records; (b) keep them X-only and run them at a Gate B tag.
- **Recommended default.** Runs (a) and tests (a) (Y decisions 6, 7). If block A must start before certification, it runs on X.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** Y decisions 6, 7 (:338–:339), §8 (:303–:309).

### LS-04. Regenerated a0 adapters: acceptance and failure path (A LQ4)
- **Question.** Accept a regenerated a0 e1 adapter only if its fingerprint equals the Gate A unit's, and what happens if it does not?
- **Options.** (a) A's rule: the eval-only references at that seed wait; a0 at that seed is re-run with a full evaluation from PLAN-S:233's contingency; the record states the change. (b) For seed 1101, copy the retrain's e1 state from the stopped pod w0b-2 (its only copy; FOCUS:77), under the same fingerprint rule.
- **Recommended default.** (a), with the engine named (A-RV R2): the re-run uses the stage-1 engine (X′ after the merge) and is accepted under LS-02's certificate, or the record states how X is kept for this case. (b) stays an option while w0b-2 exists; a pull needs a pod start and the user's go (R: FOCUS "BACKUP: the Mac-only model weights and states …", 17 Oct 01:05 UTC; RC-26), so (b) is a USER item when it is used. Deleting w0b-2 needs the user's yes (FOCUS:125 item (4)). A retrain takes 0.077 h (M: FOCUS:77), so V2a alone does not justify keeping w0b-2 (C R7.5).
- **Cost.** About $0.14 per regenerated seed (M: A §C.9, 0.077 h at $1.79/h).
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §R.0.7 LQ4 (:134); A-RV R2 (:90–:93); PLAN-S:233; FOCUS:77; C R7.5 (:392).

### LS-05. How references are read
- **Question.** Confirm that references carry no label, are read descriptively with 90% intervals, keep their seeds under plan B, and have report-only limits?
- **Options.** Confirm A LQ2, LQ6 and LQ45, or edit them.
- **Recommended default.** Confirm. The dominance tests of the repairs against the references are LS-06.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** S1; the rule text of LQ2 (role) and LQ45 (limits) at W1, so that it is not written after Gate B outcomes (S-2; DRAFT §12.4).
- **Sources.** A §R.0.2 LQ2 (:112), §R.0.8 LQ6 (:136), §L.7 LQ45 (:442); PLAN-S:119.

### LS-06. The rule "a data repair beats a reference"
- **Question.** Which test says that a data repair beats a reference, and that it dominates them all?
- **Options.** (a) B §D: "m beats r" if the upper ends of the two-sided 90% intervals are below 0 for U(m) − U(r), below 5 pp for O(m) − O(r), and below τ_L for L(m) − L(r). Pairs are matched by seed (HB form, with a0 left out of the fit); pairs that cross the two design clusters use the pair's own variance. The adapter-scaling curve is read at conservative grid points (U against λ_lo, O against λ_hi). "Dominates" = beats every built reference, an intersection–union test, in family 1b (Holm over six at 5%). B↓LR, if added, uses the point rule (B AMD-4). (b) A LQ3: unpaired, pooled variance, with O and L "≤ 0, or its 90% interval contains 0".
- **Recommended default.** (a): a missing difference is not evidence of no harm (B §D.7), and wave 0a measures a pairing gain (B-CK2 §3). (a)'s paired form depends on UW-02; under S-a, the reference tests use S-aW, per pair, for U, O and L (B §D.6; DRAFT §5.3; RC-16, S-1). **Revision 2 edits (DRAFT §5.3):** the O margin is m_O = 5 pp, fixed for this rule whatever UW-06 decides, not τ_O\* (RC-17 (b); S-4); the curve point is λ\*_m = 1 if L̂(m) − L̂(a0) ≤ τ_L, which removes a knife-edge at L̂(m) = L̂(a0), and the record prints L(m) − L(AS(λ_hi)) because item 3 has no curve point (S-4); the power line separates HB with 5 pairs (3.4–4.3 pp at pair SD 1.83; E: B §D.5) from S-a with 3-seed references (6 against 3, Welch: 5.7 pp one-sided 5%, 9.1 pp at family 1b's first step; M: `review_fixes_numbers_out.txt`; S-19). Its rule text enters the W1 record (S-2; B §0 row D allows it).
- **Numbers.** With +6 pp over each of five references, the IUT passes per comparison with probability 0.81–0.87 (R: B-CK3 §2.3, via B §D.5). In family 1b it is lower, so "dominates" will be rare (B §D.5).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** rule text W1 (S-2), else S1.
- **Sources.** B §D.1–§D.5 (:408–:458), §D.7 (:479–:481), §H D1 (:596), §B.6 (:331–:347); A §R.0.4 LQ3 (:120–:128); B-CK3 §2.4 (:91); FOCUS:153, :243.

### LS-07. Safe LoRA's settings
- **Question.** Confirm Safe LoRA's settings before any Safe LoRA outcome?
- **Options.** Confirm or edit: the rule top-K at the one pre-registered point K = 39 (LQ9; the second point is US-03); the fast-form operator C only, no Ĉ arm, all 112 matrices ranked together, float64 cosines with no rounding, ties by name, exactly K (LQ10); the $0 weight-only check on the pod's CPU before the first evaluation, with report-only flags and no stop rule (LQ13); the record that B10's script, not the existing eval-state job, hosts Safe LoRA (LQ12; Y decision 15); whether SL's full read with VR counts as the lead's read of the paper (LQ24).
- **Recommended default.** Confirm all. If Safe LoRA had to go through eval-state itself, it would be an engine change and would join Y before Y freezes (Y decision 15).
- **Cost.** Default: 1 point × 3 seeds, about 2.8 FRE, $4.1; $4.8 with one pod; × 1.25 $6.1 (C: A FIX; A-RV R6).
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §R.1.3–§R.1.5 (:153–:193), §R.3 LQ24 (:287); Y decision 15 (:347); FOCUS:151–:154.

### LS-08. "Reproduce exactly" for B10's certification (A LQ11)
- **Question.** What does "reproduce a0's Gate A U exactly" mean when B10's script is certified (K = 0, λ = 1, no prefix)?
- **Options.** (a) The same Qwen3Guard label on each of the certified seed's 600 sampled answers; on any difference, stop every eval-only reference until the cause is known. (b) Another tolerance.
- **Recommended default.** (a).
- **Cost.** Shared with B10's certification pod.
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §R.1.4 LQ11 (:190); PLAN-S:155.

### LS-09. B+Qi's settings
- **Question.** Confirm B+Qi's computation and its names?
- **Options.** Confirm or edit: reference log-probabilities computed online in each micro-batch with the adapter disabled (LQ16); the token term w_t·NLL_t with the 10⁻³ floor and the per-example-mean reduction, and the recipe file's name (LQ17); the β values, the loss form and the objective text as recipe data, so that the settings do not hold up Y's freeze (Y decision 11); a0 as the comparator for reported differences, shown beside recipe G (LQ22).
- **Recommended default.** Confirm all.
- **Cost.** About 1.04–1.05 FRE per seed (E: A §R.2.11).
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §R.2.5 LQ16, LQ17 (:250–:251), §R.2.9 LQ22 (:269); Y decision 11 (:343).

### LS-10. B+Qi's binding check (A LQ21)
- **Question.** Fix the two numbers of the outcome-free binding check before the certificate run?
- **Options.** A's proposal: the constraint binds if the mean weight at t = 2–5 falls below about 0.5 by step 3; B+Qi equals recipe B by construction if it stays near 1 for most of the 38 steps. Or other numbers, fixed before the run.
- **Recommended default.** Fix A's numbers before the run. The lead does not drop or change the arm on this check; a change goes to the user (US-05 (c)).
- **Cost.** $0 (inside the certificate run).
- **Decides:** LEAD. **Deadline:** S1, before the certificate run.
- **Sources.** A §R.2.8 LQ21 (:267).

### LS-11. B+Qi's seeds (A LQ18)
- **Question.** Run B+Qi at seeds 1101–1106 (paired with a0's seeds) or at 1102–1107 (paired with the method arms)?
- **Options.** (a) 1101–1106 (A's proposal). (b) 1102–1107 (B's reference package, US-01).
- **Recommended default.** Decide after UW-02. Under an unpaired analysis the choice changes no inference (A). Under HB, (b) gives 6 pairs with the method arms and (a) gives 5 (B §D.1).
- **Cost.** $0 (the same 6 runs).
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §R.2.6 LQ18 (:253); B §D.1 table (:423).

### LS-12. Four jobs per pod in stage 1 (A LQ7)
- **Question.** Keep the cap of 4 jobs per pod for stage 1, and count eval-only reference jobs as arms?
- **Options.** (a) Yes. (b) Ask the user.
- **Recommended default.** (a). The user fixed 4 "for the whole Gate B path" only (FOCUS:125 item (1)). This extends the rule and changes nothing decided. KCR KD2 notes that the lead may read the 16 Oct "go ahead" as covering it, or ask.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §R.0.9 LQ7 (:138); KCR KD2 (:263); FOCUS:125.

### LS-13. Charging rules
- **Question.** Confirm how references, the shared representation pass, one-off costs and A1 are charged?
- **Options.** Confirm or edit.
  - LQ8: a reference is charged what a practitioner who already has a0 pays on top of it; a0's regeneration is a study cost, reported apart.
  - LQ33: each scorer that uses the shared representation pass is charged the whole pass, with the shared split as a second number.
  - LQ34: one-off per-dataset costs (the content classifier, the anchor job) are charged in full to the first menu that uses them, and reported apart.
  - LQ35: name A1's stages in the w0b-2 ledger, and state whether the a0 retrain is A1's cost. The diagnostics took 3.04 h against a frozen upper of 2.0 h, and the retrain 0.077 h (M: FOCUS:77).
  - One sentence on MRA W8 (A §N item 4).
- **Recommended default.** Confirm all.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** S1 (the cost conventions freeze at D3, before stage 1).
- **Sources.** A §R.0.10 LQ8 (:140), §C.8 LQ33–LQ35 (:340–:342), §N item 4 (:484); PLAN-S:203–:204, :212.

### LS-14. "Agree" between the two cost conventions, and the cost sentences
- **Question.** Confirm what "a claim stands only where both conventions agree" means, and the fixed sentences of the cost section?
- **Options.** A LQ32: a Δ claim needs the same sign under both conventions at the stated B, and an interval that crosses 0 under either means "not shown"; a c\* claim needs the same grid bracket; V_max is reported under both, and a sentence uses the smaller. A §C.10's three sentences: generation is about 80% of an arm's time; no 7–8B claim from 1B ratios; money and FRE are kept apart.
- **Recommended default.** Confirm. The "compute-matched" sentence must agree with LW-17.
- **Numbers.** Generation is 80–82% of the engine-ledger total in the three wave-0a R arms, or 79–81% of the job slot (M: A §C.2; checked by A-RV n3).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §C.7 LQ32 (:337), §C.10 (:364–:367); PLAN-S:202.

### LS-15. The c0 job (A LQ30)
- **Question.** On which arm does the one real lean job that measures c0 run?
- **Options.** (i) A cost-only lean job on Gate B's R_1 edit at seed 1101. It is not an attempt of R_1 under PREREG:108; only its ledger is read; its evaluation files are sealed by hash and never read. (ii) A lean job on a Gate A a0 seed (for example 1101), under the same seal (A-RV R5). It trains 38 steps, not 33: about +25–33 s, that is about 3–4% of c0 under LW-15 (a) or 5–7% under (b) (E: A §C.6; A-RV N3).
- **Recommended default.** A gives none. Both options need B17, the lean-evaluation job (A-RV R13). Y puts the c0 job on its C1 pod (Y §0).
- **Cost.** About $0.3–0.6 (E: PLAN-S:202).
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §C.6 LQ30 (:333); A-RV R5, R13, N3 (:105–:108, :119, :128); Y §0 (:30); PLAN-S:202.

### LS-16. Record corrections (A LQ23)
- **Question.** Carry A's six record corrections into FOCUS and the records?
- **Options.** Yes, or edit. They are: Safe LoRA is evaluated by B10's script; Safe LoRA's fast form also rescales the update; the two methods' repositories carry Apache-2.0 and MIT; SPEC §6.2 and F3 details; Qi et al.'s warmup ablation is Table 5 in arXiv v1, not "Table 9"; and the record of whether SL counts as the lead's read (LS-07).
- **Recommended default.** Yes, in the W1 FOCUS entry or at S1.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** A §R.3 (:279–:287).

### LS-17. The actor column and the per-actor report
- **Question.** Add an "Actor" column to Table 1 and a per-actor report rule?
- **Options.** (a) C R3.1–R3.2: five actors (a closed-service customer with data only; one with hyperparameter control; the service provider; an open-weights developer; the dataset publisher). Each actor's menu is fixed before any newly run stage-1 cell's outcome is read (RC-15's wording, extended here). The best data arm and the best reference per actor are named among feasible arms. The text says "too close to call" unless B's separation test separates them: two arms are separated only if their paired contrast's two-sided 90% interval excludes 0, and the named best is reported beside its contrast against the runner-up (B AMD-3). (b) No column.
- **Recommended default.** (a). It adds no α claim. Paper decision 10's wording stays the user's (LA-02).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** S1; the "too close to call" rule text at W1 (S-2).
- **Sources.** C R3.1, R3.2 (:217–:224), AMD-3 (:517); B §B.6 AMD-3 (:345); C-TM T1 (:322).

### LS-18. The confirmation rules and the hidden subsample
- **Question.** Fix, before stage 1, the rule that picks at most 2 contrasts per family for confirmation, the meaning of "confirmed", and the content of the sealed hidden subsample?
- **Options.** The pick rule: one rule committed before stage 1 (FOCUS:252); no draft writes it yet. "Confirmed": B's proposal, that is the 95% interval excludes 0 in the same direction and the label agrees, by HB on the fresh seeds (B §B.6). The subsample: (a) 200 harm prompts, no over-refusal, no ARC, one id set shared across families (Y decision 4, recommended); (b) also 100 hidden over-refusal prompts, which needs the user under FOCUS:245 and :252.
- **Recommended default.** Write the pick rule; adopt B's "confirmed" rule; subsample (a), sealed by the stage-1 freeze. **The DRAFT's placeholder (revision 2; RC-23):** the two primary contrasts with the largest |t| of the primary U test, among contrasts whose U part reads better or worse (U) at the primary read; ties to the lower P index; none if no contrast has either U word. Under subsample (a) an O or L label cannot be confirmed on the hidden prompts, so the rule picks on U only. A false "confirmed" for a null contrast has probability at most 2.5%, so at most 5% for two (S-22). The pick rule and "confirmed" text go into the W1 record (S-2).
- **Cost.** $0.
- **Decides:** LEAD (subsample option (b) is USER; what the units read is US-09). **Deadline:** rule text W1 (S-2), else S1; the subsample by S1.
- **Sources.** FOCUS:252; B §B.6 row 2 (:338); B-CK11 §5 Q10 (:170–:187); Y decision 4 (:336); PLAN-S:215, :227.

### LS-19. The overlap control's test
- **Question.** Give the rule "the add effect must hold on the lower-similarity half" a test, or mark it report-only?
- **Options.** (a) A test fixed now, for example the same sign and a one-sided 90% bound above 0 (B-CK11 §5 Q12). (b) Report only.
- **Recommended default.** (a), with the DRAFT's text (§9.4; S-25): "holds" = the add contrast on the lower-similarity half has the same sign as on all prompts and its 90% interval excludes 0; else the text says "not shown on the less similar half". Its rule text goes into the W1 record (S-2); B14 builds the strata at S1.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** rule text W1 (S-2), else S1.
- **Sources.** B-CK11 §5 (:170–:187); PLAN-S:172; BRIEF "Out of scope" (:11); DRAFT §9.4.

### LS-20. Human-check add-ons (HR HD6)
- **Question.** Does the human label check's sealed draw include add-on strata (the references, Llama, the Alpaca a0)?
- **Options.** (a) None at the block-A draw; a second draw only if the budget allows, decided now. (b) Include them now.
- **Recommended default.** (a) (HR), decided at the freeze, not after outcomes.
- **Cost.** The rater time per item is not measured yet (HR §5.3).
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** HR §13 HD6 (:392); LLB U7 (:350); ALP U-6 (:844).

### LS-21. The stage-1 kit and new configs under `experiments/`
- **Question.** When do new configs (B+Qi's recipe, B↓LR, V2a's recipe S′) enter `experiments/`, and which kit shell runs stage 1?
- **Options.** Configs: (a) by an explicit-path commit after Gate B's last kit pod, never untracked under `experiments/` while a Gate B pack may run (C R3.5, VF-17; BRIEF T3); (b) as committed additions earlier (KCR KD8: T4's letter allows them, but a recovery re-pack would carry them). Kit: the B15 stage-1 kit as one shell that also serves 7–8B and 32B (KCR KD10 route (ii); XL D14), or separate kits.
- **Recommended default.** Configs (a). The kit shell is chosen when block 0's date is set (KCR KD10, "the rule now, the kit later").
- **Cost.** $0 now.
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** C R3.5 (:235), VF-17 (:620); KCR KD8, KD10 (:269, :271); XL D14 (:274); BRIEF T3, T4 (:64–:65).

### LS-22. X′ (or Y) integration after `--final`'s lexicon-pin procedure (new in revision 2; RC-14)
- **Question.** Does the engine merge wait for the end of Gate B's `--final` procedure, not only for Gate B's last kit pod?
- **Options.** (a) Yes: the P5 lexicon-pin procedure re-runs every sealed Gate B phase with a new reading SHA-256 (R: FOCUS 16 Oct 11:08 UTC), and an engine merge in the tree during that procedure breaks a reading test (R: Y §4.3). (b) After the last kit pod only (A LQ19 as written).
- **Recommended default.** (a). It agrees with LS-01 (a).
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** DRAFT Appendix C G-5; Y §4.3 (:181–:190); FOCUS 16 Oct 11:08 UTC.

### LS-23. Recipe G: reuse the 8 Oct units or re-run (new in revision 2; RC-14)
- **Question.** Does the recipe G reference reuse the 8 Oct units at 1101–1103, or re-run them?
- **Options.** (a) Reuse, if the engine and evaluation match (A RQ §1.4). (b) Re-run.
- **Recommended default.** A leaves it open; decide at S1 with US-01 (recipe G at 1102–1107 under B's package reuses 1102–1103 if allowed).
- **Cost.** $0 for (a); about $4.4 for 3 new runs (E: 3 × 1 FRE at $1.46).
- **Decides:** LEAD. **Deadline:** S1.
- **Sources.** DRAFT §5.1; A RQ §1.4; B §D.1 table.

---

## 5. Later items

### LA-01. Llama base download for Safe LoRA in stage 2 (A UQ2)
- **Question.** Approve the gated `meta-llama/Llama-3.2-1B` base download (2.47 GB; R: A §R.1.11) for Safe LoRA on Llama?
- **Options.** Approve, with the HF token reaching the pod only through ssh stdin (a FOCUS precedent); or no Safe LoRA on Llama.
- **Recommended default.** Ask at stage 2.
- **Cost.** $0 (pod download time).
- **Decides:** USER. **Deadline:** later (stage 2).
- **Sources.** A §R.1.11 UQ2 (:208).

### LA-02. Paper decision 10: the five actors (C U-20)
- **Question.** Replace the single "user" in the paper's §6 with the five actors?
- **Options.** (a) Adopt. (b) Keep the current §6 wording; Table 1 still gets the column (LS-17).
- **Recommended default.** (a) (C).
- **Cost.** $0.
- **Decides:** USER (an author decision). **Deadline:** later (next paper revision).
- **Sources.** C R3.3 (:226), U-20 (:137); PAPER decision 10 (:224).

### LA-03. Self-replay and task-format safety data (C U-13)
- **Question.** Add self-replay of safety SFT rows, or task-format safety data, as add repairs?
- **Options.** (a) Not now: cited limitations. (b) Add them.
- **Recommended default.** (a). Both add a new safety data source, and the user's 9 Oct rule keeps PKU-SafeRLHF as the add repairs' data (FOCUS:155).
- **Cost.** About $6–7 at 3 seeds plus a download (E: C R4.7).
- **Decides:** USER. **Deadline:** later.
- **Sources.** C R4.7 (:274–:278), U-13 (:130).

### LA-04. OLMo 3 at 7–8B (C U-14)
- **Question.** Probe OLMo 3 7B Instruct in 7–8B block 0, and then choose its role?
- **Options.** (a) A third 7–8B family, about $255–385. (b) Instead of OLMo-2-7B, about +$30–60 net. (c) Option C's single 7–8B family. (d) A limitation only, $0 (E: C-EM §5.2). The 32B tier may also weigh Olmo 3.1 32B Instruct (C R9.6; not costed).
- **Recommended default.** C's lead recommendation: (b) if the probe reads partial and option B is funded. Under the relayed rule the ladder is (a), then (b), then (d). (b) and (c) also need OLMo 3's own noise block if chosen by the 20 Nov rule (C VF-9). No stage-1 change (C R9.1).
- **Cost.** Probe $8–26 plus $2–6 for judges and a certificate; the noise block $17–33 (E: C-EM §5.2; C VF-9).
- **Decides:** USER (ladder USER-CONFIRM), as C U-14 marks it (revision 2, by RC-12's rule). **Deadline:** later: 9 Nov (probe and noise block), 20 Nov (choice) (I: REPLAN dates).
- **Sources.** C R9.3, R9.4, R9.6 (:432–:446), U-14 (:131); C-EM D16 (:305).

### LA-05. A transfer test for the dataset publisher (C U-15)
- **Question.** Train Llama-3.2-1B on the OLMo-selected removal sets (A1, L1) at 3 seeds?
- **Options.** (a) Decide with the stage-2 pre-registration. (b) No.
- **Recommended default.** (a). Whether Dolly row ids carry across the two tokenizers' prepared sets is UNVERIFIED.
- **Cost.** About $12–14 (E: C R3.7).
- **Decides:** USER. **Deadline:** later (stage 2).
- **Sources.** C R3.7 (:239), U-15 (:132).

### LA-06. B↓LR at 7–8B (C U-16)
- **Question.** Run B↓LR on both 7–8B families?
- **Options.** (a) Decide at the 20 Nov gate, with fresh seeds disjoint from the side paper's. (b) No.
- **Recommended default.** (a).
- **Cost.** About $45–58 for both families (E: C-TM §2.5).
- **Decides:** USER. **Deadline:** later (20 Nov; I).
- **Sources.** C R3.8 (:241), U-16 (:133); C-TM T4 (:325).

### LA-07. Second rater and human label check (C U-17; HR)
- **Question.** Run Part 1 (a second rater on the 50 items of the 9 Oct sheet) and Part 2 (a human label check on the compared arms), and with which raters?
- **Options.** HR's decisions HD1–HD5, HD7 and HD9–HD12: the rater route; Part 2's design A, B or C; the delivery of the sheet; the ethics route; the release of ratings without text; whether a report-only check is enough. Also LLB U7 (a Llama stratum), ALP U-6 (an Alpaca stratum) and PAPER decision 24.
- **Recommended default.** HR's: Part 1 yes after the lead's $0 steps; a paid freelance annotator; Part 2 design B if BlueDot funds it, else A; an encrypted offline file; the disclosure ethics route; ratings released without text; report-only.
- **Cost.** Part 1 about $25–50; Part 2 about $220–330 per paid rater, $440–650 for two (E: HR §5.3).
- **Decides:** USER. **Deadline:** later (Part 1 any time; Part 2 after Part 1's time per item). The W1 paragraph is LW-30.
- **Sources.** HR §13 (:383–:402); C R5a.7 (:321), U-17 (:134); PAPER decision 24 (:238).

### LA-08. A Qwen2.5-7B rung probe (C U-18)
- **Question.** Run a one-seed Qwen2.5-7B probe at LR 2e-5?
- **Options.** (a) No. (b) Yes.
- **Recommended default.** (a). It would reverse the user's 9 Oct scope ("Qwen stays out of the repair study"; FOCUS:159).
- **Cost.** About $3–4 (E: C-EM §5.3).
- **Decides:** USER. **Deadline:** later.
- **Sources.** C RQ.4 (:458), U-18 (:135); FOCUS:159.

### LA-09. The re-plan's option B (PAPER decision 28), its scope part
- **Question.** Adopt the re-plan's option B (P1–P6 and the references on OLMo-2-7B and Llama-3.1-8B; Llama-1B as a replication), with option C as the fallback? **Revision 2 (RC-11 (d)):** the part that sets the status of OLMo-1B's stage 1 ("development") is UW-21, due at W1 (at the latest S1); this item keeps the 7–8B scope part.
- **Options.** (a) B staged, with C as the fallback. (b) C now. (c) A. (d) Keep the adopted design.
- **Recommended default.** **Current rule in force:** OLMo-2-1B's P1–P6 is the primary study (FOCUS:240–:241; D5 = (a), FOCUS:78). The re-plan is a proposal (REPLAN:1). PAPER marks option B "resolved by the user's rule" (PAPER:242), which rests on UW-01. Until the user confirms, the W1 record does not adopt option B's roles for the 1B stages.
- **Cost.** Option B's new money about $1,090–1,660; option C's about $680–1,070 (E: REPLAN §6). No grant is awarded yet (R: FOCUS:90).
- **Decides:** USER-CONFIRM. **Deadline:** later (the 20 Nov gate; I: REPLAN §5).
- **Sources.** PAPER decision 28 (:242); REPLAN §6, §7 (:122–:157); C:19.

### LA-10. 7–8B Part 1 decisions other than the 1B part of S
- **Question.** Answer P78's other [USER] items before the 7–8B noise block launches?
- **Options.** P78 [USER] 2–12: H, the high-noise branch (a 10 pp SESOI at 7–8B, or P1, P3 and P6 at 12 seeds; either changes D5's SESOI at 7–8B); SR-2, a blinded re-check after block A; F, the family for option C (P78 proposes that it is fixed before Gate B wave-1 outcomes are read); TC, the transfer check; RP decision 5 (reuse the side units); N's money; the seed-rule thresholds; the pooled σ̂ under C.
- **Recommended default.** P78's recommendations (H: (b), else (a); SR-2 yes; F1, OLMo-2-7B, with the stated case for F2). F matters only under option C (LA-09).
- **Cost.** N about $26–32 with the allowance; the account must hold about $129 or more at launch for two parallel N pods (E: P78 §3.2).
- **Decides:** USER. **Deadline:** later (before N launches, latest about 9 Nov; F earlier as P78 proposes; I).
- **Sources.** P78 §12 [USER] 2–12 (:387–:397), §8 (:299–:327), §10 (:361–:373).

### LA-11. Two more plant locations (F9): moved to UW-20 in revision 2 (RC-11 (c)); the text below is revision 1's, kept for the record and not counted
- **Question.** Run the plant at two more sealed locations if stage 1b is funded?
- **Options.** (a) Yes. (b) No: F6's $0 relocation replay gives the scorer-side spread, and the paper says that the runs side has one location.
- **Recommended default (ambitious; rests on UW-01).** (a) if the 1b funding covers it; fallback (b). The extra draw labels go into the conditional W1 text (LW-19).
- **Cost.** About $34–70 (E: B-CK11 §2.4).
- **Decides:** moved (UW-20). **Deadline:** —.
- **Sources.** B §G F9 (:567), §H G2 (:604); B-CK11 §2.4 (:115).

### LA-12. A public deposit and the data release
- **Question.** Deposit the stage-1 protocol publicly (OSF or AsPredicted), and what does the paper release?
- **Options.** No draft gives options. A deposit is a public post, so it needs the user's approval (B-CK11 §5 W1). For the release, B-CK11 suggests plant rows as PKU ids only (PKU is CC-BY-NC); PAPER lists menus, seeds, outcome tables, costs and scores, answers to harm prompts or not, anchor text, and the planted rows' identifiers.
- **Recommended default.** None recorded; PAPER marks the release policy "[TO BE DECIDED]".
- **Cost.** $0.
- **Decides:** USER. **Deadline:** later.
- **Sources.** B-CK11 §5 (:170–:187); PAPER decision 31 (:245).

### LA-13. Paper-text rulings for the next revision
- **Question.** Apply the drafted paper texts in the next revision?
- **Items.** C R3.3 (the five-actor text; the decision is LA-02); R3.6 (side-paper citation rules; tell the GPT lead that the main study plans an OLMo-2-1B cell at LR 5e-5); R4.6 (citations, kept [CITE-CHECK] until fetched); R5a.6 (do not predict that B+Qi restores prefill robustness); R7.2 (rename A1 in claims and bound the claim); R7.3 (fix the false sentence on judge-filtered anchors at PAPER lines 525 and 697); R9.5 (limitation sentences); RQ.1–RQ.3 (the Qwen sentences); HR HD13 (the wording for paper decision 24); B-CK11 §5 W15, Q13 and Q14 (paper only); MRA W10 (one decision-tree figure of every fork, who decided it, when, and with what data visible).
- **Recommended default.** Apply.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** later (next paper revision).
- **Sources.** C §1 (:89–:107), R3.3–RQ.3; HR HD13 (:399); B-CK11 §5 (:170–:187); MRA W10 (:206–:220).

### LA-14. 7–8B preparation rulings
- **Question.** Adopt C's and P78's lead rulings for the 7–8B preparation?
- **Items.** C R9.1: no stage-1 change. C R9.2: prepare OLMo 3 in the 7–8B draft (a separate lock; the system message; where the safety prompt goes; a new sealed preparation, whose tokenizer download needs the user). P78 [LEAD] 14: commit the 7–8B scorer rules and their code hashes before any block-0 scorer output is read.
- **Recommended default.** Adopt.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** later (before 7–8B block 0, about 9 Nov; I).
- **Sources.** C R9.1, R9.2 (:424–:430); P78 §12 [LEAD] 14 (:413), §10 (:361–:373).

### LA-15. Stage-2 rules that reuse stage-1 rules
- **Question.** Fix how stage 2 reuses the stage-1 rules?
- **Items.** LLB L6: Llama's τ_L from Llama's own a0 by L16, 0.0030 nats against OLMo's 0.0067 (M: LLB §15 item 8, from Gate A losses). LLB L12: whether FOCUS:242's seed rule sets the Llama replication's seeds, and with which σ̂. LLB L13: keep "same sign, difference below the MDE", or add an equivalence interval. ALP L-6: L1's layer for Alpaca by a new sealed draw. ALP L-9: the Alpaca replication's place in the testing order.
- **Recommended default.** As each note recommends.
- **Cost.** $0.
- **Decides:** LEAD. **Deadline:** later (before Llama's wave 1, or Alpaca's first run).
- **Sources.** LLB L6, L12, L13 (:359, :365, :366); ALP L-6, L-9 (:855, :860).

### LA-16. Alpaca's scope and Gate B-lite on Alpaca
- **Question.** Which Alpaca package runs after Alpaca's Gate A, and does Alpaca get a Gate B-lite?
- **Options.** Scope (ALP U-4): Gate A only, about $12–13; the lean package, about $63–73; plan A, about $117–129 (E: ALP §9). Gate B-lite (ALP L-5, the lead's): none; wave 1 only, +$16, which gives the selector test a second menu (E: ALP L-5); waves 1 and 2.
- **Recommended default.** None given for U-4. Each step waits for a funding event, never an outcome. The note proposes deciding before Gate B wave 1 is read. **Current rule:** Alpaca runs right after Gate B (FOCUS:155); the dataset LR rule and the download wait for the user (ALP U-1, U-2).
- **Cost.** As above.
- **Decides:** USER (U-4; L-5 is the lead's). **Deadline:** later (proposed: before Gate B wave-1 outcomes are read).
- **Sources.** ALP U-4, L-5 (:840, :853); FOCUS:155.

---

## 6. Closed items (checked; not counted)

| Item | State | Source |
|---|---|---|
| BRIEF U1, D5 | Decided (a) by the lead under the user's delegation: P1–P6 primary; REQ-22 not built; the one-example patch bounded in text | FOCUS:78; ADD:7 |
| BRIEF U3, c0 for the predictions | Default (a) kept: predictions as curves in c_d/c0 | FOCUS:78 |
| BRIEF L1–L16 | Decided ("confirm with edit"), binding | ADD §2 (:15–:293); FOCUS:75 |
| ADD §3, §4, §5 items 1–3 and 5 | The lead's rulings, binding; §5 item 4 is US-06 | ADD:295–:324 |
| B+Qi without warmup; "G+Qi" renamed "B+Qi" | Decided; US-05 asks only whether to revisit it | FOCUS:125 item (10), :148–:149 |
| The noise-gate failure route (9 Oct item (7)) | Decided: (b), take the fallback | FOCUS:113 |
| Moving the plan-A cut to σ̂ ≤ 3.4 pp | Withdrawn: not blind (σ̂_gate was known) | B V-10, §H A6 (:586) |
| B-CK3's margins m_O, m_L for "worse" | Withdrawn by B in favour of R1.3 (UW-05 option (c)) | B §B.3 (:306) |
| MRB's selectivity as primary; non-inferiority against the comparator; "use all hidden banks"; a He-style plant; V2b | Rejected by C (R1.6, R1.7, R5b.2, R8.5, R7.5) | C §8 (:592) |

## 7. Conflicts between the sources, and where this list puts each one

| Conflict | The sides | Where here | Class |
|---|---|---|---|
| PLAN-S:102 against HB | Approved unpaired analysis; B (HB, [LEAD]); P78 (seed-blocked, [USER]) | UW-02, LW-01 | USER (current rule stays) |
| HB against HB-C | B's author; B's verifier | LW-01 | LEAD after GPT |
| Holm over 6 against Φ; A LQ43 against Φ | Frozen family; A (two families of six); B (Φ) | UW-04 | USER |
| The 18:31 "worse" rule against R1.3 or margins (C-j) | User rule; C R1.3; B-CK3 margins (withdrawn); MRB §8.3 | UW-05 | USER |
| BRIEF U4 and U6 marks (C-l; A-RV R4) | A ([LEAD] under the 16 Oct instruction); BRIEF (user); C ([USER] for amendments) | UW-04, UW-08, UW-09 | USER, unless the lead records its reading |
| O error model (C-i) | B and C (prompts random); B-CK3 and A LQ36 (bank-conditional) | LW-03 | LEAD |
| "Upper 90%" (C-b) | A LQ36, LQ39 (one-sided 90%); C R1.2 and B (two-sided 90% upper end) | LW-06 | LEAD |
| τ_L comparator (C-c; AMD-7) | PLAN-S:124 (a0); dose-matched R | LW-07 | LEAD after GPT |
| Placement statistic (C-k) | ADD L15 (7) (top-k hit); B F3 (row AUC) | LW-11 | LEAD |
| REQ-17 noise (ADD L15 (1)) and REQ-16 SE (ADD L16) | The lead's own rulings; B A7, A8 | LW-12, LW-13 | LEAD |
| The benign-topic plant F10 | B (ambitious: add); C (not now) | UW-16 | USER (a target change; RC-12); this list recommends "not now" |
| O-ext H against the 8 Oct rule "never from the hidden remainder" | B and C (H first in their ladders); the user rule | UW-07b | USER (current rule stays; RC-05) |
| F1's mark | B (USER-CONFIRM); C (USER) | UW-15 | USER |
| References' variance and O/L rule | A R.0.4 (unpaired; "≤ 0 or contains 0"); B §D (paired; non-inferiority) | LS-06 | LEAD |
| References' seeds | A R.0.8 (1101–1103); B D2 (all six) | US-01 | USER-CONFIRM (current rule stays) |
| B+Qi's seeds | A LQ18 (1101–1106); B D2 (1102–1107) | LS-11 | LEAD, after UW-02 |
| The engine merge point | A LQ19 (after the last kit pod); Y (after `--final` and C1–C3) | LS-01 | LEAD |
| Part C model-agnostic | Y and P78 (later, new files); ALP L-7 ("now" or twins later) | LW-29 | LEAD |
| "Worse (answers do not end)" | B §F (a new "worse" reason); the user's 18:31 meaning | LW-09 | LEAD with a flag, not a new word (RC-02); USER if "worse" or "inconclusive" (UW-05 (e)) |
| Option B roles for OLMo-1B's stage 1 | PAPER decision 28 (relayed rule); the adopted design and D5 = (a) | UW-21 (status, W1); LA-09 (scope, later) | USER for the status; USER-CONFIRM for the scope (current rule stays) |

## 8. Draft A re-verify items R1–R14: how this list applies them

| Item | Fix | Applied in |
|---|---|---|
| R1 | Cite `runner.py`:627, not :625; drop Fix-log item (6) | LW-16 (LQ26) |
| R2 | Name the engine in the a0 failure path (X′ after the merge, under the certificate, or say how X is kept) | LS-04 |
| R3 | The τ_O sentence holds for the point estimate only; under an upper bound τ_O binds about 2 pp lower | LW-06 |
| R4 | The precedent for keeping U4 and U6 [LEAD] is the D5 entry (FOCUS:78; ADD:7), not L1–L16; otherwise they are USER | UW-04, UW-08, UW-09 |
| R5 | LQ30 option (ii) gets the same seal as option (i) | LS-15 |
| R6 | "$4.9" → "$4.8"; "$2.7–2.9" → "$2.7–2.8" | US-03, LS-02, LS-07 |
| R7 | "330–370 s" → "330–371 s" | LW-15 |
| R8 | LQ47 is a W1 item; add it to the §C heading's exceptions | LW-17 |
| R9 | HEAD moved; it is `3db753e` at 00:30 UTC on 17 Oct | Source table |
| R10 | A's §P says "four" `date -u` checks; the header lists three | A's own text: fix when the lead edits A into the records |
| R11 | Two FOCUS line ranges were partial | This list cites FOCUS entries by line at `23e3da8f…` |
| R12 | Define SS = `experiments/safety_selection/` | Source notes |
| R13 | Both LQ30 options need B17 | LS-15 |
| R14 | UQ7: "the options in BRIEF's D5-7 row for (b) and (c)" | US-06 |

A's nine nits are R6–R14. Its five minor errors are R1–R5. A-RV's notes N1–N7 are used in LW-16 (N1), UW-14 and LW-17 (N2), LS-15 (N3), LW-15 (N4), LS-02 (N5) and LW-08 (N6). N7 (revision 1 is gone) needs no action.

## 9. Not included (outside stage 1)

These design-note items do not bear on stage 1, so this list leaves them out: KCR KD1, KD3–KD7, KD9 and KD11 (the 7–8B cap rule); XL D1–D13 and D15 (the 32B and 70B design); Y decisions 9, 10 and 13 (7–8B reuse, 32B, Alpaca's derived file); ALP U-1, U-2, U-3, U-5 and L-1 to L-4, L-8, L-10 to L-12 (Alpaca's preparation); LLB L2–L4 and L7–L11 (the Llama Gate B-lite design, frozen with UW-19); P78 [LEAD] 1–7, 9–13 and 15. The ICML fallback venue (FOCUS:74; REPLAN §7 item 12) is also left out.

## 10. Sources read, process and limits

**What I read.** FOCUS lines 1–260 (in full); PLAN-S (in full); BRIEF and ADD (in full); A, A-RV, B, C (in full); B-VR (§1–§3 and its finding table); the check notes' decision sections (B-CK2 §8, B-CK3 §3.5, §4.7, §6.4, B-CK11 §3–§6, C-OR §8, C-TM §5, C-EM §6); the design notes' decision and timing sections (LLB §14–§16, ALP §12, HR §13, Y §0, §4.3, §8, §10, P78 §4, §8, §10, §12, KCR §12, XL §10); REPLAN §5–§7; PAPER decisions 16–31; MRB W4, W10; MRA W10; W0's README and NOTES (searched only). I did not open PREREG beyond the lines that the drafts cite.

**Gate B values that I saw (for LW-08).** FOCUS's noise-gate and wave-0b entries (FOCUS:77, :82): r_j, σ̂_gate, P4, the P(LOCALIZED) lookup, the rankings as orders, the picks, the ρ values and the re-costing figures. A §B and §C.2: the wave-0a ledger seconds, job slots and pod overheads. B §K.3: the U values of a0 and R at 1101–1103. LLB §15 item 8: the OLMo R arms' task-loss differences over the same-seed a0. I did not see any sealed score, any Gate B arm's O, ARC or answer, or wave-0b's `rows.jsonl` or `groups.json`.

**Commands run (all exit 0).** `git branch --show-current`, `git log --oneline` (main checkout, read-only); `ls`, `wc -l`, `cat -n`, `sed -n`, `grep -n`, `awk`, `cut` over the sources; `shasum -a 256` over the sources; `date -u` (four times, the last at the end); one `python3 -I -c` arithmetic line for UW-10's cost and US-03's pod figure (no data read). One `Read` of C failed on size and I read it again in parts.

**Acceptance against the merge brief.**
- One list, de-duplicated, with id, question, options, default (ambitious and fallback where given), cost, class, deadline and source lines: done.
- USER W1 items first, then LEAD W1, then the rest: done (§1–§5).
- Draft A's R1–R5 and nine nits fixed while merging: done (§8); R10 is A's own text.
- Frozen rules, sealed rankings, D5 = (a) and user decisions unchanged; proposals to change them kept USER with the current rule in force: done (UW-02 to UW-07b, UW-10, UW-19, UW-21, US-01, US-09, LA-09).
- Items that rest on the relayed rule marked USER-CONFIRM: done (revision 2: 4 USER-CONFIRM items and 7 USER items with a USER-CONFIRM ladder; M: this list).
- Not tested: no script, simulation or cost in the drafts was re-run.

**Limits and unresolved concerns.**
1. **Classes.** I moved B's [LEAD] for the variance model (UW-02) and B's USER-CONFIRM for F1 (UW-15) to USER, and B's coherence "worse" to a flag (LW-09; revision 2, RC-02). Revision 2 also follows RB's double marks (RC-12) and makes UW-16 and UW-07b USER. The lead may disagree. Each item says why.
2. **UW-16.** The drafts disagree; this list recommends "not now". The deadline is the T1 commit, which is imminent (LW-22).
3. **Blinding.** LW-07's choice is now made after some readers, me included, saw the OLMo R arms' task-loss differences. REQ-21 (m) must say so.
4. **Load at W1.** 57 items are due at W1, 22 of them the user's (M: this list, revision 2; revision 1 had 49 and 19). Most W1 user items have a silent default that keeps the current rule, so wave 1 does not wait for them. The listed W1 build commitments (REQ-23 and the W1 build items) still hold wave 1.
5. **Line numbers** are at the hashes in the source table. FOCUS grows; cite its entries by title in the records (ADD §3 (3)).

---

## Review fixes (revision 2)

**What this is.** `review-consistency.md` (RC-01 to RC-35) reviewed this list beside the pre-registration DRAFT and the builder extract. `review-statistics.md` (S-1 to S-26) reviewed only the DRAFT; where the same rule sits here, its accepted fixes are carried so that the three files agree. Each finding was checked against the sources first (the source checks are listed in the DRAFT's "Review fixes" section). Nothing here changes a frozen Gate B/C rule, a sealed ranking, D5 = (a) or a user decision in FOCUS; where a finding would, the item stays USER with the current rule in force.

- **Written** 2026-10-17 from 01:20 to about 01:55 UTC by an Opus worker (clock checked with `date -u` at 01:20, 01:27, 01:31 and 01:48 UTC). Main checkout HEAD `5957a37`.
- **Ids.** No id was renumbered. New items: UW-07a and UW-07b (from UW-07), UW-20 (from LA-11), UW-21 (from LA-09), LW-31 to LW-35, LS-22, LS-23. LA-11 keeps a pointer and is not counted.

| Finding | Status here | Where |
|---|---|---|
| RC-01 | no change needed (UW-02 was already USER) | — |
| RC-02 | applied: the tested label stays, with a flag; "worse" or "inconclusive" for coherence is a USER option | LW-09; UW-05 option (e); §7 table |
| RC-03 | no change needed (LW-07, LW-08 item 6 and §10 already disclose); LW-08 item 9 points to the DRAFT's new rows | LW-08 |
| RC-04 | applied (changed: the two seed-only ranges are given apart, see the DRAFT's note) | LW-06 |
| RC-05 | applied: UW-07 split; N is the ambitious default; H is a separate USER question with no default | UW-07a, UW-07b; index; §0; §7 table |
| RC-06 | no change needed (US-08, US-09, US-18 exist) | — |
| RC-07 | applied | LW-31 |
| RC-08 | applied | LW-16 (LQ25, LQ28) |
| RC-09 | no change needed (LW-15 has the caveat) | — |
| RC-11 (c) | applied: F9 moved to W1 as conditional rule text | UW-20 (was LA-11) |
| RC-11 (d) | applied: the status part of option B split out, due at W1 | UW-21; LA-09 |
| RC-12 | applied: "USER (ladder USER-CONFIRM)" for UW-07a, US-10, US-11, US-12, US-14, US-15 as RB marks them; UW-16 USER; US-10 option (b) USER; §0 and UW-01 recounted. **Extended** to LA-04, because RB marks U-14 the same way ("[USER]; ladder [USER-CONFIRM]") | index; §0; UW-01; UW-16; US-10 to US-15; LA-04 |
| RC-13 | applied (one text in all three files) | UW-04; UW-08; UW-09; UW-10; UW-12 |
| RC-14 | applied: R_4/R_5 reuse, S-a's prompt term for O, REQ-21's file name, X′ after `--final`, recipe G reuse added; UW-14 (c) cites the builder extract's R_tok cost | LW-32, LW-33, LW-34, LS-22, LS-23; UW-14 |
| RC-15 | applied; extended to the actor menus | LW-19; US-10; LS-17 |
| RC-16 | no change needed in substance (LS-06 already said S-aW); LS-06 now says "per pair, for U, O and L" | LS-06 |
| RC-17 (a) | applied | UW-05 |
| RC-17 (b) | applied | LS-06 |
| RC-18 | applied | LW-12 |
| RC-20 | applied | LW-20 |
| RC-21 | applied | LW-10 |
| RC-22 | applied | US-11 |
| RC-23 | applied (the DRAFT's placeholder is quoted) | LS-18 |
| RC-25 | applied | LW-22 |
| RC-26 | applied | LS-04 |
| RC-28 | applied as a [LEAD] reading with its fallback | LW-19 |
| RC-29 | applied | source table note |
| RC-30 | applied ("Gate B's P4") | LW-08 item 1 |
| RC-33 | applied | UW-14 |
| RC-10, RC-19, RC-24, RC-27, RC-31, RC-32, RC-34, RC-35 | DRAFT or EXTR only (RC-19's checks were already unconditional in LW-05) | — |
| S-1, S-5, S-7, S-8, S-13 | carried | UW-02; UW-04 (b); LW-02 |
| S-2 | carried: rule texts due at W1 | UW-05; LS-05, LS-06, LS-17, LS-18, LS-19; index |
| S-3 | carried | LW-35 |
| S-4, S-19 | carried | LS-06 |
| S-6 | carried | UW-02 |
| S-10 | carried | UW-05 |
| S-15 | carried (a0 outside the plan-B pool; see the DRAFT's note) | LW-31 |
| S-17 | carried | LW-10 |
| S-18, S-20 | carried | LW-03; LW-33 |
| S-22, S-25, S-26 | carried | LS-18; LS-19; UW-07a |
| other S items | DRAFT only | — |

**Rejected here.** None of the RC findings that touch this list. The statistics review's rejected parts (S-9 steps 0a–0b, S-11's 12.5% as an exact bound, part of S-19) are listed in the DRAFT's "Review fixes" section; they do not touch this list's text.

**New points (not applied).** The DRAFT's N-1 (which act "approves" the W1 rules under PLAN-S:239) and N-2 (F9 and AMD D2 keep a single USER-CONFIRM mark) also apply here: UW-20 and US-01 stay USER-CONFIRM, as their source (B) marks them.

**Commands and files.** As listed in the DRAFT's "Review fixes" section. This file was edited by `python3 -I` exact-string replacements, each checked to match once.
