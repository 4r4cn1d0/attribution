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

## Rulings on Part 2's open items, second set (recorded 2026-11-07T13:40 UTC)

After round 6 (the Part 2 re-verifier's R1-R10; the kit re-verifier's K6v-1-K6v-6). Item numbers are Part 2 §14's.
This file's header covers these rulings too (Part 2 item 35, confirmed): none reads a 1B repair outcome.

- **Item 36, the anchor job's stops, in full.** If a family's anchor job stops (a harmful pair fails to encode, or
  fewer than 64 safe anchors are kept), then on that family:
  1. There is no anchor bank and no S_78. So `rep_pass`, `l1_scan`, the classifier and `a1_pass` do not run.
     A1, L1 and S3 are not run, and every primary contrast that uses them is not tested there, stated.
     DataShield-style and the Gate C reproduction (`rep_pass`'s other uses) are not run there, stated.
  2. The a0-1101 retrain runs under the family's main config (the same training identity), on engine Y. It is
     ruling 10's certificate and ruling 7's confirming check of the side units. This is A2's rejected alternative,
     adopted only in this case, because S_78 cannot exist. It costs one retrain pod, as A2's route does.
  3. Engine Y's pack, KD9's re-measure, B+Qi on Y and the confirmation follow that certificate as ruling 10 says.
- **Items 2 (a) and 5, recording hashes.** Part 2's code hashes are re-taken at its freeze and before the first
  scorer pod. The scorer section's rules are fixed from its commit. A re-taken hash that differs is recorded in
  Part 2's change log with both values and the commit that changed it. Each pin fill (the anchor bank, S_78, A1's
  unit, the `s3_orig` pool, `OEXT_78B`, `C0_SOURCE`, `ENGINE_Y`) is a recorded lead step in FOCUS, with
  `make_scorer_settings_78b.py --check` and the differ-only test as its evidence. Part 2's tables take those values
  before the freeze; after the freeze, a dated amendment file holds them.
- **Item 9 (b), c0's state line.** Kept: c0 counts as state-keeping, with two more idle lines.
- **Item 24 (c), B+Qi's O-ext on Y.** E4's `OEXT_78B` files get a Y variant per family (the 1B `oext_unit_y.json`
  form), filled when `ENGINE_Y` is filled. B+Qi's O-ext runs on Y with it, also when B+Qi is unpaired.
- **Item 31, idle storage outside the printout.** The kit's lines stay for the pods that keep states. The lead's
  per-block deletion list names every stopped pod, so the user's yes covers them all.
- **Item 32, LN-14's θ0 transfer report.** Not run at 7-8B, stated (report-only at 1B; Branch 128 only).
- **Item 33, a reduced list after the encode count.** Only if a prompt fails. Then a new frozen-on-commit script
  under `scripts/scale78b/` writes the reduced list in its own sealed folder (A3's pattern, identity-based write
  guards). Its SHA-256 enters the settings' list pins and `SCORER_PINS` by a recorded lead step. The maker reads the
  reduced list's size (a maker change, built only if needed). The later prompts move to earlier chunks, stated.
- **Item 34, AD1 at the boundary.** At exactly 96 kept rows, AD1 is printed once, beside AD2, as equal to it. At
  exactly 48, AD1 is "not formed".
- **Item 37, W1-18.** One pod on all seven reused units (both families) as the scorer block's first O job, before
  any O-ext pod of either family. Under [C], OLMo-2-7B's units only. Branch full is the fallback for both families
  if it is not built or does not finish.
- **K6v-4, `C0_SOURCE` after a clean pack.** The kit also checks the packed source unit against `C0_SOURCE` at
  release time, so an edit after the pack is refused on the Mac too. This is a build item for the next kit round.

## Rulings on Part 2's open items, third set (recorded 2026-11-07T14:45 UTC)

After round 7a (its re-verifier's V1-V7). Part 2 is committed with its scorer section at this point; these rulings,
and V1-V7's text fixes, are written into Part 2 before its freeze.

- **V1, engine Y on a family whose anchor job stopped.** `ENGINE_Y` is filled when that family's main-config retrain
  is prepared (PP18's main clause). If Y differs, ruling 10's second job, the X retrain, also runs under the main
  config.
- **V2, SR-2 on a stopped family.** σ̂_A pools the block-A cells that run on that family. SR-2's error-rate
  simulation runs on the design that will run: the reduced design if a stop is known before the simulation runs.
- **Item 38, what the encode count covers.** Both `encode_generation_prompt` for every list prompt and `encode_train`
  for every `s3_safe` and S1 pair, at the family's main-recipe limits.
- **Item 33 (b) with V3, a reduced `s3_safe`.** The same frozen-on-commit script as item 33's reduced list writes a
  new s-pool record. The record's `lists.s3_subset.ids` and `lists.s1.ids` drop the same ids, because `s3_score`
  refuses an id without `s3_safe` features (R: `scripts/stage1/score_s3_datarx.py:101-105`). Its SHA-256 enters the
  settings' pins by a recorded lead step.
- **The three label lines** (Part 2 §1.18 item 15; §16.5 items 7, 10, 11) are confirmed: the anchor-stop fallback
  and LN-14's non-run were chosen after the stage-1 reading, which the authors had seen (P1:33).
