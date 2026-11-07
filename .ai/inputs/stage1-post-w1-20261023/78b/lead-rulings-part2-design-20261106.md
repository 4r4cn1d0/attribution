# Lead rulings for Part 2's design (7-8B tier, 6 Nov 2026)

Recorded 2026-11-06T18:59 UTC by General Implementation X, the main-study lead, under the user's delegation (no
approval questions; the frozen money and blinding rules apply). Source: the read-only scout's decision memo
`.ai/inputs/stage1-post-w1-20261023/78b/build-round-20261105/scout-p2.md` (decision ids below are its ids). These
rulings govern Part 2 (`research/experiments/2026-11-06-78b-preregistration-part2.md`) and the kit's block A/B
build. They were made after the stage-1 reading and before any 7-8B repair outcome; none reads a 1B repair outcome
(ruling 16's labels apply where the memo marks one). Part 1 (frozen) and the rulings PP1-PP18 stand.

## The rulings (each adopts the memo's recommendation unless it says otherwise)

- **E1, the evaluation bank.** Stage 1's O set as it is, for both families: the family's dev 100 plus the same 400
  sealed PHTest prompts (record `a810574e…`). U and L need no new bank. Before the first Llama O pod, a $0 encode
  count of the 400 prompts on Llama's codec (counts only); if any fail, LN-24's shortfall rule fixes Llama's bank
  before any O answer exists.
- **E2, the answer-cap branch.** A 7-8B W1-18 check on the seven reused side units, by W1-18's frozen bar, per
  family, as the first O job: Branch 128 if every unit passes, else Branch full. Pre-set fallback: Branch full if
  the check cannot run, fails to finish, or is not built before the first O-ext pod.
- **E3, O in the arm's own job.** Block A and B arm jobs evaluate O-ext in the same job, as at 1B, at most 4 arms
  per pod, with an O-ext cap term (E, then measured from the pre-block-A O pods by a recorded lead step). Pre-set
  fallback: a separate O job per unit if the kit's in-job path is not verified before block A's first pod.
- **E4, `OEXT_78B`.** As the memo's list: a 7-8B O-ext unit runner (a wrapper over the unchanged S1 scripts where it
  can take the expected settings hash, else a copy with changed literal pins and a parity test), per-family
  settings, and the branch and W1-18 pins of E2.
- **E5, O and L for N and the reused units.** `o_only_with_regenerate` for the seven N units too (R regenerated with
  their sealed edits; acceptance against N's own COMPLETE.json), as LN-12 did at 1B; single-job pods until
  measured, then up to 4 per pod by a recorded lead step. L needs no job (it is in every unit's record).
- **F1, references.** The 6-seed set at 1102-1107 for every reference, money-contingent and outside the gate test;
  pre-set fallback the 3-seed set at 1102-1104. Order after the gate: the dose arm at 3 seeds, then the reference
  increment, then the dose arm's 6 seeds (this also answers the memo's open question on that order).
- **F2, each reference's settings.** As the memo's rows: the safety prompt as a user-turn prefix on both families;
  adapter scaling at λ {1, 0.9, 0.75, 0.5, 0} by fingerprint-accepted regeneration (Mac adapters as the LS-04
  fallback); Safe LoRA at K = 78 of 224 matrices (1B's share; labelled: chosen after the stage-1 reading, reads the
  rule's form only); recipe G on OLMo-2-7B's existing main-LR config, on Llama a new G config at LR 5e-5; B+Qi in
  1B's form on engine Y, unpaired if Y differs. The Llama base repository is gated: its access is checked by the
  Range precheck at the next Llama launch; if it fails, Llama's Safe LoRA is not run, stated.
- **J1, J2, judges.** HarmBench and Granite as the memo's (a), with HarmBench only for a block whose Granite launch
  fails its known-answer gate; A9's "report-only" holds for N's gate, and in the comparison R_1102 and R_1103's
  HarmBench files enter the claim rule like every cell. The reused units are re-judged on one device per contrast
  (about 9 extra units per family).
- **K1, K2.** The O limit as the memo's (a); τ_L computed by the lead on the Mac from losses only (OLMo now, Llama
  after N's record-done), entered into Part 2 and its blinding line.
- **K3, cost conventions.** Carry PR4 §10.1-§10.3. Rates $1.79 spend, $1.85 guard, $10/h limit, $6 reserve; the
  ×1.2 planning allowance and the ×1.25 contingency named apart; the three money figures never mixed (A17). Part 2
  states that the plan's B figure of about $640-900 already holds the dose arm, so the gate test's B figure without
  it is about $591-801; O-ext adds about $50-100 (Branch 128) or $200-355 (Branch full) over both families; idle
  storage is about $60-250, not $15-30. To keep idle storage down, the lead asks the user for deletion yeses by pod
  name in one list per block, right after each block's verified backup (C13 item 3).
- **The gate's "covers" test (an open question).** Ruling 9's test reads the expected spend (E) against the money
  in the account plus top-ups the user has stated; each launch then follows the user's start-from-the-balance rule
  and the kit's init-block funding record.
- **C1, the confirmation.** The frozen pick rule per family (P1 §13 item 5; PR4:428); candidates P1-P6 under plan A
  and P1, P3, P6 under B9 and H (b); each picked contrast's repair and comparator at seeds 9101-9106, read on the
  hidden subsample only, through the frozen readers (counts and hashes only).
- **A1, Alpaca.** Outside Part 2's frozen design. Part 2 holds only the home rule: (a) in this tier if the user
  gives both Alpaca items (the learning-rate rule extended to datasets, and the download approval) by about 20 Nov
  and the money after the gate covers every line above Alpaca in RP:138's cut order by about 1 Dec; else (b) on its
  own money later; else not run. Any Alpaca run gets its own pre-registration frozen before its first pod.
- **B1, blocks A and B in the kit.** Part 2 gives the kit what the memo lists (block tables per plan and family, the
  pod layout, the dose arms at 39 steps, the O-ext arm step and cap term, the reference kinds, the judge and
  re-judge lists, SR-2's blinding test). The kit build follows Part 2's text.
- **K4-K9.** As the memo's recommendations: block A's seal (K4); the S4 add-dose arm's reading with its pre-set
  fallbacks (K5); SR-2's error-rate simulation with a reading rule written before it runs (familywise rate above 6%
  at any simulated σ means SR-2 is not adopted and N decides alone; K6); `blinded_sigma.py` before block A's first
  pod and the reader's hash in Part 2 or a dated amendment before block B's outcomes are opened (K7); PR4 §11's stop
  rules carried with the memo's three edits (K8); Part 2's blinding line as the memo lists (K9).
- **B+Qi's certificate (an open question).** No separate certificate pod: the LS-10 binding numbers logged in the
  B+Qi runs are the record.
- **The memo's other open questions** (the MAIN_F generation and guard hashes against the 1B O-ext pins; the 400
  prompts' Llama encode count; the 200 hidden-subsample ids in Llama's prepared set; the Safe LoRA disk fit; the
  side units' stored dev-100 answers as W1-18 inputs) are $0 checks for the build rounds, counts and hashes only,
  through the frozen readers.

## What this means for money (told to the user in the lead's report)

The gate (ruling 9) now sees two more lines than Part 1's figures: O-ext (about $50-355 over both families,
depending on E2's branch) and more idle storage (about $60-250, cut by prompt deletion yeses). Part 1's plan-A
figure already includes the dose arm. If the money after N does not cover option B with these lines, ruling 9
gives option C on OLMo-2-7B.

## Rulings on Part 2's open items (recorded 2026-11-07T10:14 UTC)

The round-5 draft of Part 2 lists 30 open items in its §14, and its verifier asked for rulings. Item numbers below
are that list's. Items not named here are records or build steps the text already states.

- **Items 6 and 17, the S3 and S4 lists.** Stage 1's sealed `s3_safe` (861), `s3_subset` (855) and `s4_candidates`
  (512) lists are reused on both families. Before each family's untuned-answers pass, a $0 encode count of every
  list prompt under that family's codec and main-recipe limits runs (counts only, through the frozen code path). A
  prompt that fails is dropped by the list's own stage-1 rule; the counts go into Part 2 before any untuned answer
  exists.
- **Item 7, the anchor job's two stops.** If a harmful pair fails to encode, or fewer than 64 safe anchors are kept
  (exit 3), A1 is not run on that family, and P1 is not tested on that family. Part 2 states it. No re-draw and no
  script change.
- **Item 8, the classifier.** As at 1B (PR4 §9.2): scored only, no arm, and claims are limited to rank overlap.
- **Item 9, c0 and the O-ext kinds under Branch 128.** All three O-ext kinds take `--w1-18-record`, and the
  regenerated units also take `--dev100-source` (the verifier's D11). These are build items for the kit round.
- **Item 11, A1's golden test.** If `a1_pass` runs on engine Y, the golden test is re-run on Y, and its pin is
  re-taken by a recorded lead step before A1's edit is written.
- **Item 14, A1's one-category flag.** Reported only. No unit arm runs at 7-8B.
- **Item 15, [C] and the scorer pods.** The scorer pods run after the gate (CHECK C1), for the chosen option's
  families: both under [B], and OLMo-2-7B only under [C].
- **Item 16, ruling 10's branches and A1's states.** A1 uses the states of the retrain on the engine that the paired
  arms use. If Y equals X, that is Y's retrain. If Y differs and X equals the side unit, it is the X retrain (ruling
  10's second job). If X differs, ruling 7's fallback applies, A1 uses the X retrain's states, and that is labelled.
- **Item 18, a regenerated unit that differs.** As LS-04 at 1B: it is not used for O, its O is "not run", and that
  is stated.
- **Item 20, the S1 verdict record.** The lead re-runs the OLMo-2-7B S1 check with the merged script before block A.
  It reads stage 1's S1 edit by exact path and SHA-256, and counts only. The expected verdict is unchanged.
- **Item 22 and the verifier's D1.** Every [to be entered] value is entered before the freeze, before block A's
  first pod. A later value needs a dated amendment.
- **Item 23, `C0_SOURCE`.** The kit gets a Mac-side check at pack time (the packed source unit's e1 fingerprint
  against the pin), so a typo is refused before a paid pod starts. This is a build item.
- **Item 24, the O-ext cap terms.** (a) The arm's O-ext term is ×1.5 until measured, the kit's upper-factor form.
  (b) The references evaluate O-ext in their own jobs, as at 1B, and their caps carry the same term.
- **Item 25, the seal and τ_L.** Confirmed: Llama's a0-1103 task loss, read after N's record-done for τ_L, is the one
  named exception to block A's seal over N's L files.
- **Item 26, J2's re-judge list.** Exactly N's units, the reused a0 units and θ0, per family. That is 7 each:
  OLMo-2-7B 3 + 3 + 1; Llama-3.1-8B 4 + 2 + 1. The memo's "about 9" was an estimate.
- **Item 27, volume size.** The volumes stay 50 GB (KD5). Smaller volumes risk the free-space refusals that a 7-8B
  policy plus a guard model can trigger. The batched deletion yes is the idle-storage control.
- **Item 28, the overlap control.** The `similarity` kind is built if the block A/B kit build has room before block
  A's first pod. If not, Part 2 states "not run" (the pre-set fallback).
- **Item 30 and the verifier's D7 (b), the preamble.** Confirmed: where a design ruling is shorter than the memo's
  recommendation, the memo's other lines are adopted. The confirmation's reader is unbuilt; it is listed as unbuilt,
  and its hash goes in before the first confirmation outcome is opened.
- **The S4 dose's boundary cases.** At exactly 96 kept rows, S4_top is S4_96. At exactly 48, it is S4. No extra arm
  is formed in either case.
