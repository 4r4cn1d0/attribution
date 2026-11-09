# Lead rulings for the 7-8B kit's block A and B build (GI XI, 8 Nov 2026)

Recorded 2026-11-08T14:13 UTC by General Implementation XI (GI XI), the main-study lead, under the user's delegation
(no approval questions for planned steps; the ambitious default with a pre-set fallback; the frozen money and
blinding rules apply). Source: the read-only planning scout's plan
`.ai/inputs/stage1-post-w1-20261023/78b/build-round-20261105/plan-ab.md` (PLAN-AB; copied into the records with this
round; its open items O1-O16 and simplifications S1-S3 are its ids). These rulings were made after the stage-1
reading and before any 7-8B scorer output or repair outcome; none reads a 1B repair outcome. Part 1 (frozen), Part 2
(the committed draft and its amendment 1), RUL, ADD, PP, DES (all four sets) and GXI stand. Where a ruling below
needs Part 2's text to change, the change is made in Part 2's draft parts at the next text round, before the freeze.

## The build's shape

- **B-1. Tracks and order.** PLAN-AB §2-§3 as written: round R1 = Tracks S (SR-2 statistics), O (the 7-8B O-ext
  layer), C (the $0 count tools) and K1 (the kit's rules layer), in parallel in separate worktrees, each followed by
  one adversarial verifier; then the lead's $0 checks; R2 = K2 (planning, judges, seal, the blinding record-done,
  `C0_SOURCE`'s release check) and Track R (reference settings); R3 = K3 (runner and pack, engine Y's pack); R4 =
  K4 (hardening, the K6v gaps); a fix round after any round that needs one. Every mutant killed; an error is an
  invalid run, never a kill.
- **B-2 (S1). One lean planning route** for blocks A and B, in the form of `init_block0` and `init_block_sc`, not the
  inherited 1B block-A route (its Gate B verdict, LN-12, cert and certify gates do not apply at 7-8B).
- **B-3 (S3). One O-ext wrapper**, `scripts/scale78b/oext_78b.py`, with three commands (`unit`, `lean`, `w1_18`)
  and one parity suite, if Track O's decisive check (PLAN-AB §4 item 5d) passes. Else the copy route of DES E4 (a
  copy with changed literal pins and a parity test).
- **B-4 (O15, S2 not adopted).** Part 2 §15's rule stands: items 1-11 are verified before block A's first pod,
  items 3 (the dose arms) and 6 (the references) included. Pre-set fallback: if block A's first pod is otherwise
  ready and items 3 or 6 are not verified, they move to "verified before block B's first pod", stated in Part 2 by
  a dated amendment; nothing else moves.
- **B-5 (O16).** The build is priced at about 57-95 builder h before block A (E: PLAN-AB §6), not SCOUT's 20-30 h.
  Part 2 §15's cost line takes the new estimate at the next text round.

## Rulings on PLAN-AB's open items

- **O1. Steps.** Every arm trains for ⌈rows / 128⌉ steps of its training rows: P1 §10's own rule ("128 rows per
  step"), which gives RK's `STEPS` (4,200 rows → 33, 4,800 and 4,848 → 38) and P1's 39 for S4_96 (4,896) and S4_192
  (4,992). So S4_top with n kept rows takes ⌈(4,800 + n) / 128⌉: 38 for n ≤ 64, 39 for n ≥ 65. Not a new decision.
  The kit derives each arm's steps from its edit file's resulting row count and refuses a named arm whose derived
  steps differ from RK's value.
- **O2 and X2. B10's certification.** Part 2 §16.1 carries B10's stop rule, and the frozen `eval_adapter.py` takes a
  certification report. So a 7-8B `b10_certify` kind is built in the 1B form: one per reference seed, against that
  seed's block-B a0 unit (its COMPLETE.json and its evaluation), before that seed's `ref_eval` and `safe_lora` pods.
  Its report is `ref_eval`'s `--certification-report`. A failed certification stops every evaluation-only reference
  (P2 §16.1). It is block-B work (Track R and K3). Part 2 §15 item 6 names it at the next text round.
- **O3. W1-18's settings.** `oext_eval.py:218-219`'s "never re-pinned" concerns the 1B W1-18 settings, and that file
  is never re-pinned. The 7-8B W1-18 check (DES E2) uses new per-family settings files under
  `scripts/scale78b/settings/`, made by a recorded step, bound by the wrapper route if it passes the decisive check,
  else by the copy route (DES E4). **No record may name a file it did not read:** a settings path label written into
  any record or output must be the path of the file the run actually loaded. If the wrapper route can pass the frozen
  validator (`oext_unit.py:146`'s path check) only by writing the 1B path label, the copy route is used.
- **O4.** Confirmed: one W1-18 pod (DESO2 item 37) runs one W1-18 check per family, each with its own settings and
  its own record, so each family's branch (DES E2) is read from its own record. Under [C], OLMo-2-7B's only.
- **O5.** Not adopted: W1-18 stays on its pod (DESO2 item 37). A Mac run would need the guard model's download (a
  user approval) and saves about $2-5 (E).
- **O6. The anchor job's stops.** A stop is recorded only from the frozen script's own signal: exit 3 for fewer than
  64 safe anchors (DESO item 7), and exit 1 with the `AnchorJobError` message "harmful prompt … does not encode" for
  a harmful pair (R: `scripts/make_anchor_answers.py:121`). Any other exit or message is a crash, handled by the kit's
  crash rule, never a stop. The stop record is text-free JSON: family, stop kind, exit code, the job's JOB-DONE.json
  SHA-256 and the stop line's ids and counts. Track C's count tool also counts the anchor list's encodes on the Mac
  ($0, counts only); that count informs the lead but decides nothing: the anchor job's result decides.
- **O7. Seals across working copies.** Each working copy seals its own outcome files in its own seal record; block
  A's seal record names the other copies' seal records (block 0's, the scorer block's) by SHA-256, so one check covers
  every file P2 §2.5 seals. Llama's a0-1103 task loss stays the one named exception (DESO item 25).
- **O8.** Noted only (about $1.4; E).
- **O9. τ_L.** Computed from task losses only, by Track C's losses-only reader, so P2 §0 item 10 stays "none read".
- **O10. K6v-5.** The lead's step: a dated erratum record beside `k6-fix.md` (the committed report is not edited).
- **O11.** Llama's new recipe-G config (LR 5e-5; DES F2) is written and its hash recorded before
  `OEXT_78B[llama31-8b]` is filled, so the pin is filled once.
- **O12.** The references' E caps carry the O-ext term (× 1.5; DESO item 24 (b)). The kit prints them; Part 2 takes
  the values before the freeze; they are E until measured.
- **O13.** The lead locates the sealed S lists by SHA-256 for the encode count; the tool reads them only by path and
  pinned hash.
- **O14 and X4. The gate record.** A new null pin `GATE_78B` (the gate record's path and SHA-256), filled by a
  recorded lead step after ruling 9's gate: option ([B] or [C]), families, plan (A, B9 or H (b)), the noise reading's
  and `blinded_sigma.py`'s output hashes, and the live balance. Block A's init reads its families; block B's init
  reads its plan. Before the fill, both refuse.
- **X1.** Engine Y's pack (and KD9's re-measure) is built in K3 before the scorer block's a0-1101 retrain on Y.
- **X3.** The 7-8B reference settings (eval_adapter, safe_lora at the family's block count and K = 78, the overlap
  settings) are Track R's.
- **The seed key (PLAN-AB summary).** `o_only_with_regenerate` and every unit input are keyed by (arm, seed), not by
  seed alone: on OLMo-2-7B, N's R_1101 and the side unit a0-1101 share seed 1101. A K1 fix with a test.

## Second set (recorded 2026-11-08T15:22 UTC): O14 corrected; Track S's open points

- **O14 corrected (two records, not one).** P1 §6.2-§6.4: N's σ̂_pool gives only a provisional plan at the gate;
  SR-2's σ̂_A, after block A, decides block B's design (both directions allowed); without SR-2, N's value decides
  under [B] and the chosen family's own σ̂_F (2 df) under [C] (R: P1 §6.2, §6.4). So:
  1. `GATE_78B` (filled after ruling 9's gate, before block A): option ([B] or [C]), families, N's provisional plan,
     the noise reading's output SHA-256 and the live balance. Block A's init reads its families (block A is the same
     in every plan; P1 §6.4).
  2. A second null pin, `PLAN_B_78B` (filled after block A's record-done and `blinded_sigma.py`, before block B):
     `blinded_sigma.py`'s output SHA-256 (σ̂_A and df only) and its inputs file's SHA-256, whether SR-2 is adopted
     (the blinding test verified and the simulation's reading), and block B's plan by P1 §6.1 (A, B9, H (b) or
     review). Block B's init reads its plan; a "review" plan plans nothing (P1 §6.1: the user decides).
- **S-1. The interaction scenario.** The builder's form (an independent arm × seed term on method-arm cells only), at
  two sizes, ρ = 0.5 and ρ = 1 (the term's variance as a share of the cell variance), beside the no-interaction case.
  The reading rule (DES K6) applies to every simulated scenario: a familywise rate above 6% at any simulated σ, with
  or without the interaction, means SR-2 is not adopted.
- **S-2. The claim test.** Holm on U at 5%, as a bound, adopted only if B16's claim (Φ over U, O, L, F) cannot pass
  without the U contrast passing its Holm test, so the U-only familywise rate bounds Φ's (I). Track S's verifier
  checks it with R cites; if it fails, the simulation simulates Φ's U part before the full run.
- **S-3. The prompt part.** Omitted (no prompt-level data exists before block A), stated as a limit in the settings
  and the output.
- **S-4.** Confirmed: under [B] one σ̂_A pooled over both families gives one plan for both (P1 §6.4); H is simulated as
  H (b) covered (the gate budgets H (b); P1 §6.4's money line).
- **S-5.** Confirmed: on a family whose anchor job stopped, the Holm family is the primary contrasts tested there
  (DESO2 item 36): P3, P4, P6 under plan A; P3, P6 under B9 and H (b).
- **S-6. A cell that did not run.** `blinded_sigma.py` drops a block-A cell only when it is A1, L1 or S3 on a family
  whose anchor job stopped, and the inputs name that family's anchor-stop record (GXB O6) by SHA-256. Any other
  missing cell refuses: block A must otherwise be complete.
- **S-7. Floors.** σ̂_A takes no floor (P2 §10.2 names none). The simulation's N stage computes σ̂_pool exactly as
  `scripts/scale78b/noise_reading.py` does, its σ_eval floor included (P1 §3.3), with a test that the two agree on
  the same cells.
- **S-8.** K2 and K3 confirm that the kit's block-A arm jobs write the unit form `read_unit` reads (a run-one e1 unit
  of the dev bank, split dev, role development), with a test.
- **S-9. The method edits' hashes.** `blinded_sigma.py`'s inputs file is written by the kit's block-A record-done step
  (K2) from its plan.json and pins, never by hand; its SHA-256 enters `PLAN_B_78B`.
- **S-10. The design that runs.** The full simulation runs now on the full design under [B] and [C] ($0). If an anchor
  stop becomes known before block A's first pod, it runs again on the reduced design (P2 §10.3, DESO3 V2), and that
  run's reading governs. The run that governs is the one on the design block A will run.

## Third set (recorded 2026-11-08T15:29 UTC): Track O's open points

- **T-O1. The hybrid route is accepted.** DES E4 allows "a wrapper over the unchanged S1 scripts where it can take the
  expected settings hash, else a copy with changed literal pins and a parity test", per script. Track O's decisive
  check (R1 report `r1-o.md`) found that every seam passes with module globals naming the file the run loads, except
  `scripts/stage1_s1/lean_eval_job.py:229`, a literal path check that a 7-8B lean settings file could pass only by
  naming a file it does not read (GXB O3 forbids it). So `unit` and `w1_18` run the unchanged 1B scripts through
  `scripts/scale78b/oext_78b.py`, and `lean` runs one parity-tested copy, `scripts/scale78b/lean_eval_job_78b.py` (the
  1B file with listed substitutions; a test rebuilds it byte for byte). `oext_eval.py` stays unchanged (P2 §4.4).
- **T-O2. Fill order.** θ0's job.json SHA-256 per family (measured by the lead by hash only), then the W1-18 pod, then
  each family's branch from its own record, then `OEXT_78B[F]`; for Llama-3.1-8B the new recipe-G config (GXB O11)
  goes before `OEXT_78B[llama31-8b]`. Each fill is a recorded lead step (DESO2 items 2 (a), 5).
- **T-O3. The kit's side.** RK's `OEXT_UNIT_SCRIPT` and `C0_SCRIPT` name the wrapper; a null `OEXT_78B_Y` pin per
  family joins RK (DESO2 item 24 (c)); the runner's O-ext commands become `oext_78b.py <command> --family F …`; under
  Branch 128 the family's W1-18 record joins the job's files list. K1 takes the pins; K3 the commands.
- **T-O4. Llama's θ0 unit.** It was made under the LR 1e-4 kit's recipe (`c5462c77…`; P1's table), not MAIN_F. θ0 is
  the untuned model, so the training LR does not touch its answers. It is used for W1-18 only if that recipe's
  generation and guard blocks hash to MAIN_F's (the C3 expression, PLAN-AB §5), measured by the lead before the
  W1-18 pod; if they differ, the lead stops and records the gap before any W1-18 pod.

## Fourth set (recorded 2026-11-08T15:43 UTC): K1's open points; the anchor-stop record's form

- **K-1.** K2 replaces `plan_tool.py`'s c0 script check (one wrapper path now serves c0 and the O-ext kinds) with a
  check of the command word (`lean` for c0, `unit` for `o_only`, `o_only_with_regenerate`; `w1_18` for W1-18) and
  re-targets the scorer mutant `K4bf-m-c0-needs-oext-script` at it. The mutant is not retired.
- **K-2.** K2's lean planning route (B-2) replaces the inherited 1B route for blocks A and B before any block-A copy
  exists (`plan_ab_checked`, N's deal, `units_of_block("A")`).
- **K-3. The W1-18 pod's home.** OLMo-2-7B's scorer-block copy. Under [B] it packs both families' W1-18 settings and
  side units; under [C] OLMo-2-7B's only. If any Llama file must come from the Hub on that pod, its launch follows
  the Llama token path (the user hands over the HF token; C13).
- **K-4.** N's seven `o_only_with_regenerate` pods are scorer-block pods: their idle-storage lines go into the scorer
  block's printout (K2). Block 0's printout stays as it is.
- **K-5. The dose arms when the fallback fires** are Part 2 §5's (with P1 §10 and DESO's boundary cases), not open:
  n ≥ 192 kept rows: S4_96 and S4_192; 97-191: S4_96 and S4_top (n); exactly 96: S4_96 only; 49-95: S4_top (n) only;
  exactly 48: no dose arm; fewer than 48: the untuned pass exits 3 (a build stop). K1's tables implement it, with a
  test per case.
- **K-6.** Accepted: when SR-2 is not adopted, `PLAN_B_78B`'s `blinded_sigma.py` hashes are null, and the record names
  the reason (the blinding test not verified, or the simulation's reading) and the plan from N's value under [B] or
  the chosen family's σ̂_F under [C] (P1 §6.2, §6.4).
- **K-7.** The pack (K3) reads OLMo-2-7B's S1 edit under `tmp/stage1-olmo/` by exact path and SHA-256 only; builders
  test with fixtures.
- **K-8.** Intended (DES E2: the branch is read before any O-ext pod). K2 adds the branch-record step; a test holds
  that the W1-18 hold never applies to block 0.
- **The anchor-stop record's form** (GXB O6, S-6): one text-free JSON form, kind `scale-78b anchor stop`, with the
  family, the stop kind (`safe_anchors_below_64` with exit 3, or `harmful_prompt_does_not_encode` with exit 1), the
  exit code, the job's JOB-DONE.json SHA-256 and the stop line's ids and counts. Track S's `blinded_sigma.py` reads
  this form; K2's writer writes it; both are tested against one shared fixture.

## Fifth set (recorded 2026-11-08T16:10 UTC): from K1's verifier (`r1-k1-verify.md`)

- **R-1. A "review" provisional plan.** P1 §6.1: under "review" there is no 7-8B primary family and the user decides
  the next step. So block A's init refuses when `GATE_78B`'s provisional plan is "review"; the lead reports it to the
  user, who decides (for example whether block A runs for SR-2's re-check). Nothing starts by default.
- **R-2. θ0's job.json pins (K1V-4).** K1 measured them by hash, and K1's verifier re-measured them independently
  (equal). They stay in the code; the merge's FOCUS entry records the fill as the lead's step with both measurements
  as its evidence (T-O2's recorded step).
- **R-3. Block 0's plan.json stays byte-identical (K1V-13).** The two new job keys are written only for blocks A and
  B; a test holds block 0's plan.json byte for byte against `3481d85`'s.
- **R-4. The O-ext command words (K1V-10).** Until K3 wires `oext_78b.py <command> --family F …`, no test asserts an
  O-ext command line; a test holds instead that every O-ext kind (c0, `o_only`, `o_only_with_regenerate`, `w1_18`)
  refuses to build its job while `OEXT_78B` or the family's branch record is null.

## Sixth set (recorded 2026-11-08T16:19 UTC): from Track O's verifier (`r1-o-verify.md`)

- **R-5. One index per family and engine (O1).** The single O-ext index covers both families and both engines, and the
  wrapper pins it by a literal, so any fill changes both families' `OEXT_78B[F]`, against T-O2's fill-once order. So:
  one index file per family for engine X and one per family for engine Y, each pinned only by the kit's
  `OEXT_78B[F]` or `OEXT_78B_Y[F]`; the wrapper holds no literal index hash and checks the index it is handed against
  the path and SHA-256 the job names. A fill on one family or engine changes only that family's (or engine's) index
  and pin; a test holds it, and the documented fill procedure leaves the suite green (O6).
- **R-6. A W1-18 record is checked on the Mac (O7).** Before any O-ext pod, the pack runs the wrapper's `check` on the
  pinned W1-18 record (the unchanged `oext_eval` reader: family, branch, settings), so a wrong pin refuses on the Mac.
- **R-7. W1-18's device (O8).** The 7-8B W1-18 settings name the pod's device (`cuda`).
- **R-8. `OEXT_78B_Y[F]`'s form (O9)** is defined and printed by the maker, like `OEXT_78B[F]`'s.
- **R-9. The side units' stored answers as W1-18's inputs** (Part 2 §14 item 29's last $0 check). The wrapper's `check`
  also confirms, for each listed side unit, that its COMPLETE.json (read by pin) lists every file W1-18 reads, by name
  and SHA-256 only; the lead runs it and records the result.

## Seventh set (recorded 2026-11-08T16:34 UTC): from Track S's verifier (`r1-s-verify.md`)

- **R-10. S-2 holds (M).** Track S's verifier showed from B16's code (R: `reading.py:237-242`, `labels.py:62-69`,
  `phi.py:5-7`, :47-66, :92-104) and 12,000 trials through `phi.run` that Φ cannot claim on U unless Holm on U rejects
  first. So the simulation's Holm-on-U familywise rate bounds Φ's U claims, and Φ's U part is not simulated.
- **R-11. The reading rule's familywise rate** is the rate of the U claims (Part 2 §10.3: "the HB-C analysis with
  Holm at 5%"). Φ's adverse O and L words ("worse (O)", "worse (L)") start at 0.5% of α inside their own contrasts
  and are not simulated; the settings and the output state this as a limit.
- **R-12. Unequal family noise (SV-3).** Under [B] the simulation's single true σ_pair for both families is listed as
  an approximation, and two more scenarios run at ρ = 0: Llama-3.1-8B's σ_pair at 1.5 and at 1/1.5 times
  OLMo-2-7B's (the grid's σ is OLMo-2-7B's; a value above the grid's top is capped there). The 6% rule applies to
  them too.
- **R-13. Engines per role (the verifier's point 3).** `blinded_sigma.py` takes the engine identity of each role (the
  reused a0 units, N's R units, block A) as `noise_reading.py` does, not one shared `reused` value.
- **R-14. The reading wrapper (the verifier's point 2).** The 7-8B reading wrapper (unbuilt; before block B's
  outcomes are opened, DES K7) keeps B16's Φ graph unchanged, and its tests hold that.
- **R-15. Df (the verifier's point 5).** The build gives 12 df per family on the full design (M: Track S's verifier, an
  exact two-way fit), not P78's "about 15". Part 2 §10.2 takes the measured 12 at the freeze; P1 §6.3's 30-df columns
  stay as P1's estimate (P1 is frozen).

## Eighth set (recorded 2026-11-08T17:19 UTC): K1's fix round

- **R-16. The seed-only unit form (K1V-9).** Accepted as K1 built it: strict (arm, seed) functions, and the seed-only
  form kept only at the four call sites a test lists (the runner, the pack and the planner, K2's and K3's files).
  K2 and K3 move those callers to the strict form and delete the seed-only form; the test's list is empty by K3's end
  (an acceptance item of both rounds).
- **R-17. R-4 corrected.** `w1_18` cannot wait on `OEXT_78B` or the branch record, because T-O2 fills both after the
  W1-18 pod. c0, `o_only` and `o_only_with_regenerate` wait on `OEXT_78B[F]` and `BRANCH_78B[F]`; `w1_18` waits on
  its own route pin `W1_18_78B`, as K1 built it.
- **R-18.** The runner's existing O-ext command-line assertions in `test_scorer_block_78b.py` stay until K3 rewrites
  those lines (removing them early could let scorer mutants survive); K3 lists them as an acceptance item.
- **R-19. Index names.** K1's pin form reads the index name `oext_index__<F>__<E>.json`; Track O's files are
  `OEXT-78B__<F>.json` and `OEXT-78B-Y__<F>.json`. Track O's names stand; K2 reconciles RK's form with them.

## Ninth set (recorded 2026-11-08T17:38 UTC): from Track O's re-verifier (`r1-o-reverify.md`)

- **R-20. The W1-18 pod's route (OR4).** The W1-18 pod does not take its index from `OEXT_78B[F]` (null until after
  W1-18, T-O2). It runs under its own route pin `W1_18_78B` (K1's): the wrapper's hash and, per family, the W1-18
  settings file and the side units, each by path and SHA-256. The maker prints that form; the lead fills it by a
  recorded step after θ0's job pins and before the W1-18 pod.
- **R-21. Where a W1-18 record lives (OR4).** Each family's W1-18 record, once retrieved from the pod, is committed
  under `.ai/inputs/stage1-post-w1-20261023/78b/w1-18/`. As at 1B, the family's O-ext eval settings pin it by SHA-256
  and kind, and its path is given at run time; `BRANCH_78B[F]` pins it by path and SHA-256. RK's form check accepts
  that one folder for the W1-18 record entry only; every other entry stays under `scripts/`.
- **R-22. Index names (OR3).** As R-19: Track O's `OEXT-78B__<F>.json` and `OEXT-78B-Y__<F>.json` stand. Because the
  merged suite runs Track O's forms through K1's RK, K1's form check is aligned with these names before R1 merges (a
  small K1 follow-up), not left to K2.
- **R-23. Y files on the Mac.** Once `ENGINE_Y` is filled, the wrapper's `check` validates the Y files with engine Y's
  identity, as it validates the X files with engine X's.

## Tenth set (recorded 2026-11-08T17:51 UTC): from K1's re-verifier (`r1-k1-reverify.md`)

- **R-24. Block B's plan is checked against its basis (KR1).** `PLAN_B_78B`'s plan must equal the plan its basis gives
  by P1 §6.1: with basis σ̂_A, the plan from the σ̂_A it records (`blinded_sigma.py`'s printed value; a variance
  estimate, not an outcome); with basis N's σ̂_pool, `GATE_78B`'s provisional plan; with basis σ̂_F under [C], the
  plan σ̂_F gives, which `GATE_78B` records beside the provisional plan under [C] (P1 §6.2). Any other plan refuses.
  This closes a money edge: a wrong record could plan 47 runs per family instead of 23 (about $198, E).
- **R-25. K1's follow-up before R1 merges:** R-24; R-22's index names; KR2's and KR7's untested checks with tests
  and mutants; KR3 (the seed-only scan covers every non-test kit file and any prefix); KR8 (`anchor_stop_or_refuse`
  always matches the record to its anchor job's JOB-DONE.json).
- **R-26. K2's and K3's acceptance items from this round:** KR4 (the runner and the pack read the stop record through
  `anchor_stop_or_refuse` before a stopped family's MAIN_F retrain pod, and the pack carries the record); KR5 (one
  shared stop-record fixture read by K2's writer, RK's checker and Track S's reader, with a cross-track test); KR6
  (K-1's command-word check reads `OEXT_WRAPPER_COMMANDS`); the inherited 1B branch record removed so `BRANCH_78B`
  is the only branch source, read by its bytes at its pin (K-8); the kept S4 count read from the untuned pass's dose
  record, not passed by a caller; R-16's call sites moved.

## Eleventh set (recorded 2026-11-08T17:51 UTC): from Track S's re-verifier (`r1-s-reverify.md`)

- **R-27. R-11 corrected (SR9).** Φ's adverse O and L words start at an absolute level of 0.5%, which is 10% of α
  (α = 5%), not "0.5% of α". The rest of R-11 stands. The settings file is still unrun, so its limit text is
  corrected before the full run.
- **R-28. Track S's follow-up before R1 merges:** SR9's text; SR1 (a test that each family's own σ reaches
  `run_chunk`, so R-12's ratio scenarios cannot silently become copies of "none"); SR2 (the summary's largest rate
  over both families and every scenario, tested under [B]); SR3 (the blinding test records every file write through
  an audit hook, not three folders); SR10 (an in-process `read()` error carries only its type and a fixed message);
  SR4-SR8's tests; and the re-verifier's 12 mutants in the spec. The full simulation runs after this follow-up, on
  its final settings.

## Twelfth set (recorded 2026-11-08T18:18 UTC): K1's follow-up

- **R-29. "Review" from σ̂_A.** P1 §6.4 applies §6.1's whole rule to σ̂_A, so the review ceiling applies to it too. RK
  takes §6.1's per-plan MDE factors from `scripts/scale78b/noise_reading.py`'s pinned values (1.4207, 1.0785 and
  0.9340 for A, B9 and H (b); review above 7.0388, 9.2721 and 10.7066 pp, so only H (b)'s can fire), and gives
  "review" for basis σ̂_A when σ̂_A is above 10.7066 pp. A test holds RK's plan, the ceiling included, equal to
  `noise_reading.py`'s seed rule on the same σ values (both sides of each boundary).

## Thirteenth set (recorded 2026-11-08T18:52 UTC): from K1's second re-verifier (`r1-k1-reverify2.md`)

K1 merges with round 1 as it stands. These are K2's acceptance items:

- **R-30 (KR2-1). Recorded values are read from their sources.** K2's record steps write `GATE_78B`'s provisional and
  σ̂_F plans from the noise reading's pinned output and `PLAN_B_78B`'s σ̂_A from `blinded_sigma.py`'s pinned output,
  never by hand; block B's init re-reads both outputs at their pins and refuses any recorded value that differs.
- **R-31 (KR2-2).** K2 deletes the seed-only unit form (R-16), so no scan of call forms is needed after K2; until then
  the scan is a guard with the gaps K1's re-verifier lists.
- **R-32 (KR2-3). `W1_18_78B`'s form** is R-20's: the wrapper's hash and, per family, the W1-18 settings file and the
  side units, each by path and SHA-256, as Track O's maker prints it (`{files, side_units}`); RK's check changes to
  accept that form. No fill happens before K2 merges.
- **R-33 (KR2-4, KR2-5).** RK's index and W1-18 record checks take exactly the standard names and folders; a W1-18
  record's SHA-256 must equal the branch record's `w1_18_record_sha256`; `plan_for_sigma` refuses (not raises) on a σ
  that is not a finite float.

## Fourteenth set (recorded 2026-11-08T22:40 UTC): from Track R's verifier (`r2-r-verify.md`)

- **R-34. θ0 and the O limit (P4).** θ0's O over the 500-prompt set comes from a fresh `o_only` pass that runs the
  untuned model under MAIN_F with the adapter disabled and reads no unit (P2 §1.14; P1 §14 item 3; M: Track R's
  verifier, a fixture through Track O's wrapper). So O(arm) and O(θ0) share MAIN_F's generation and guard on both
  families, and Llama's stored θ0 unit (recipe `c5462c77…`, LR 1e-4) is not on the O path. It is used only by W1-18
  (accepted under T-O4) and by B10's `check --untuned` and `compare --against untuned`, which no planned 7-8B run needs
  (P2 §3.1 counts no λ = 0 run). Ruled option (a), $0: the wrapper refuses those two commands at 7-8B by name; the
  scaling curve's λ = 0 end is θ0's own measurement from the `o_only` pass; stated as a limit.
- **R-35. Which a0 unit each reference seed's certification pins (P2).** The a0 unit trained at that seed under
  MAIN_F, with its own e1 evaluation: 1102 the reused side unit; 1103 the reused side unit on OLMo-2-7B and N's
  a0-1103 on Llama-3.1-8B (ruling 8); 1104 block A's a0; 1105-1107 block B's a0. GXB O2's "block-B a0 unit" is read
  as this table. One B10 settings file per seed (P1, forced by the frozen code) is accepted.
- **R-36. Seed 1101's fingerprints.** The maker takes full 64-hex values, filled by a recorded lead step from the unit's
  own records; the step's evidence includes that each value's first 16 hex equal P1 §2.1's prefix.
- **R-37. Safe LoRA's points (P3, RV-1).** Only `default` (K = 78) and `certify` run at 7-8B (P2 §3.2). The unchanged
  B11 validator needs an integer K for `conditional`, so its settings value is 0 (it maps nothing), and the wrapper
  refuses `conditional` by name; the kit plans neither `conditional` nor `k12` (sent to K2).
- **R-38. 1B prose in 7-8B records (RV-3).** A record may not state a false parameter. `safe_lora.py` writes its 1B K
  ("K = 39") into every V/V' record, so Track R takes the copy route for `safe_lora.py` (T-O1's precedent: a
  parity-tested copy with listed substitutions, the K text from the settings). `eval_adapter.py` stays unchanged (its
  self-hash certifies the 1B code that runs); its 1B terms ("Gate A", the θ0 role text) are named in the wrapper's own
  record beside each output, which says what each term means at 7-8B, and stated as a limit.
- **R-39.** `experiments/safety_selection/tests/test_ss_family_codec.py`'s config count takes +1 for Llama's new
  recipe-G config, in the same change (KD8). The file is outside engine X's identity (M: the verifier re-computed
  `472fc7f6…` with the new config); Track R may make that one-line change.

## Fifteenth set (recorded 2026-11-08T23:11 UTC): Track R's fix round

- **R-38 amended (no copy of `safe_lora.py`).** R-38's premise was wrong: the three "K = 39" texts in `safe_lora.py` are
  docstrings that reach no output; every text in its V/V' records comes from the settings (`:817-820`, `:673`,
  `:746-749`; M: Track R's marker test through the wrapper, records free of "K = 39", "39 of 112" and "Gate A"). So
  `safe_lora.py` runs unchanged through the wrapper, and the maker writes the 7-8B texts (K = 78 of 224, the certify
  and conditional status texts). The rest of R-38 (the wrapper's terms record beside each B10 output) stands; K3
  brings that record back with the outputs and lists it in the retrieval.
- **R-40.** The scale points (λ 0.9, 0.75, 0.5) are the same under F1's 3-seed fallback, which changes the seeds only.

## Sixteenth set (recorded 2026-11-08T23:32 UTC): from Track R's re-verifier (`r2-r-reverify.md`)

- **R-40 withdrawn.** It contradicts Part 2 §3.1-§3.2 (from DES F1 and SCOUT §2.1): the 3-seed fallback's grid is
  {1, 0.75, 0.5, 0}, so its planned scale points are 0.75 and 0.5, and λ 0.9 runs only under the 6-seed set. Track R's
  build follows Part 2. To match, the fallback's `allowed` scale points drop 0.9 too (RRV-1).
- **R-41 (RRV-2).** The wrapper writes a terms record only beside an output file the command itself created (it notes
  which outputs existed before the call); a refused command writes none.
- **R-42 (RRV-3).** The wrapper refuses λ = 0 by name at 7-8B (R-34: the curve's λ = 0 end is θ0's own measurement).

## Seventeenth set (recorded 2026-11-09T00:05 UTC): from K2's verifier (`r2-k2-verify.md`)

- **R-43 (K2V-1). Block B re-derives SR-2's status.** Block B's init (and release) re-derive SR-2's status from the
  pinned simulation records (the largest familywise rate against 6%, on the design that runs) and the blinding
  record, and refuse a `PLAN_B_78B` whose recorded status or plan differs.
- **R-44 (K2V-8). The blinding record's form.** It names by SHA-256 `scripts/scale78b/blinded_sigma.py`, record-done's
  code (`runkit/stage1-78b/plan_tool.py`) and the tests that hold both outputs byte for byte, with the commit at which
  they were verified. Block A's init and release refuse unless the record exists and its hashes equal the packed
  kit's files, so a later change to either code voids the verification (P1 §6.4: verified before block A's first
  pod, on the code that runs).
- **R-45 (K2V-4).** K2's deletion of the 1B branch record broke `orchestrate.py`'s `w1_18_hold`, so K2 fixes that one
  function (it reads `BRANCH_78B[F]` by its bytes at its pin), with a test, though the file is otherwise K3's.
- **R-46. The padded-tokens record (train_scale's input).** A text-free per-family record (kind, family, MAIN_F's
  hash, and per edit SHA-256: rows, steps and padded tokens per step), written by a frozen $0 Mac tool built in R3
  and pinned by a recorded lead step before block A; until then blocks A and B refuse (as K2 built).
- **R-47. `--w1-18-record` under Branch full.** K3 confirms by a fixture test through the unchanged `oext_eval` whether
  an O-ext run under Branch full with a pinned failing W1-18 record needs the record at run time; the flag is passed
  exactly when the unchanged code needs it.
- **R-48.** The `SR2_SIMULATION` pin K2 filled with the committed outputs' SHA-256 is recorded as the lead's fill step
  at R2's merge (FOCUS), with K2's verifier's recomputation (0.05145 and 0.05175) as its evidence.

## Eighteenth set (recorded 2026-11-09T04:19 UTC): from K2's re-verifier (`r2-k2-reverify.md`)

- **R-49 (K2R-1). The blinding record's hashes are checked wherever SR-2's status is used.** Block A's record-done and
  `blinded_sigma.py` run after block A's last release, so the four files the blinding record names are re-hashed and
  compared at `sr2_status`, `record-plan-b-78b`, block B's init and block B's release, as well as at block A's init
  and release. A change to any of them after the record voids SR-2's adoption (P1 §6.4: the code that runs).
- **R-50 (K2R-3). `blinded_sigma.py`'s output is re-derived.** `record-plan-b-78b` runs `blinded_sigma.read` itself
  (in process, through its guarded entry, SR10) on the kit-rebuilt inputs file, and refuses a pinned output whose σ̂_A
  or df differs. It prints σ̂_A and df only.
- **R-51 (K2R-2).** After the kit's own `requeue --rerun-mismatched` in block A, the replaced attempt is skipped (the
  kit's requeue record names it); two complete units for one run refuse only when no kit record explains them.
- **R-52 (K2R-4).** Tests and mutants for every family's block-A snapshot under [B] and for `kit_inputs_check`'s hash
  comparison.

## Nineteenth set (recorded 2026-11-09T10:12 UTC): R2's merge checks

- **R-53. The W1-18 record's file name.** R-21 named the folder, not the file, and the tracks chose differently: K2's
  RK expects `w1_18_record__<family>.json`, Track O's maker writes `overrefusal_checks__<family>.json` (after the 1B
  record kind, "stage1 over-refusal checks"). Track O's name stands; RK's standard name changes to it, with K2's tests
  and mutants. Found by the merged suite (10 scale78b tests failed in the main checkout, none in either worktree).
