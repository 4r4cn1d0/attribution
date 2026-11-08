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
