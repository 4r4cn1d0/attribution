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
