# R2 builder brief: K2, the kit's planning layer for blocks A and B

Read first: `B/lead/r1-common.md` (its paths and hard rules bind you; this round's worktree is WS = B/ws-k2, detached
at the R1 merge commit). Your report: `R/r2-k2.md`; scratch `R/r2-k2-scratch/` only.

## Owned files (runkit/stage1-78b/)
`plan_tool.py` (PT78), `judge_units_stage1.py`, `seal.py`, `states_tool.py` if it exists (else a new one), new
`tests/test_planning_ab_78b.py`, `tests/test_scorer_block_78b.py`, `tests/test_stage1_judge_route.py`,
`tests/mutation_spec_scorer_78b.json`. You may also change `rules_78b.py` and `stage1_rules.py` only for the items below
marked (RK), and any other kit test only by the smallest listed change. Never `setup/job_runner_stage1.py`,
`pack_setup.py`, `finisher.py`, `launch.py`, `host.py`, `setup/preflight_stage1.py` (K3's), and nothing under `scripts/`.

## Read
plan-ab.md §1 items 1, 5c, 7, 8, 10, 11, 12, 14 and §2's K2 row; the lead's build rulings
`R78/lead-rulings-ab-build-20261108.md`, ALL thirteen sets (they override the plan); `R/r1-k1.md` (what K1 built; the
rules you plan with); `R/r1-k1-reverify.md` and `R/r1-k1-reverify2.md` (open items for you); `R/r1-o.md` §10-§11 (the
O-ext wrapper's commands, indexes and `check`); `R/r1-s.md` (blinded_sigma's inputs file and the anchor-stop form);
Part 2 §2, §6, §10.1, §15 and AM1; DES (all sets).

## Build
1. **The lean planning route (B-2, K-2):** `init-block A` and `init-block B` in the form of `init_block0` /
   `init_block_sc`, replacing the inherited 1B route (`plan_ab_checked`, N's deal, `units_of_block("A")`) before any
   block-A copy exists. Block A's init reads `GATE_78B`'s families and refuses a "review" provisional plan (R-1);
   block B's init reads `PLAN_B_78B`'s plan and plans nothing under "review". Per-family copies (KD7).
2. **The record steps (R-30, O14, K-6):** `record-gate-78b` writes `GATE_78B`'s record from the noise reading's pinned
   output (provisional plan; σ̂_F's plan under [C]); `record-plan-b-78b` writes `PLAN_B_78B`'s record from
   `blinded_sigma.py`'s pinned output (σ̂_A, df, inputs hash) and the SR-2 status; never by hand. Block B's init re-reads
   both outputs at their pins and refuses a recorded value that differs (KR2-1).
3. **The blinding half of item 8 (the hard trigger):** block A's `record-done` prints no U, HarmBench, O, L or
   coherence value (only hashes, counts, exit codes), and writes `blinded_sigma.py`'s inputs file from plan.json and
   the kit's pins (S-9), in the form `blinded_sigma.py` reads (R/r1-s.md; engines per role, R-13; the stop record for a
   stopped family, S-6). A planted-sentinel test and a byte-for-byte test of record-done's whole printout. S-8: confirm
   (by a test on a fixture) that the block-A unit form is the one `blinded_sigma`'s `read_unit` reads.
4. **The branch-record step (K-8, R-21, K1V-5):** a step that writes `BRANCH_78B[F]` from the family's W1-18 record
   committed under `.ai/inputs/stage1-post-w1-20261023/78b/w1-18/` (by path and SHA-256; its SHA-256 equal to the
   record's `w1_18_record_sha256`, R-33); remove the inherited 1B branch record (`record_branch`, `gate_g1`,
   `branch_name`) so `BRANCH_78B` is the only branch source, read by its bytes at its pin; a test that the W1-18 hold
   never applies to block 0.
5. **The anchor-stop record step (item 14, O6, KR4/KR5):** a step that writes the stop record in the fourth set's
   form from the anchor job's JOB-DONE.json and exit (exit 3, or exit 1 with the harmful-pair message; anything else is
   a crash); one shared fixture under `runkit/stage1-78b/tests/fixtures/` read by your writer's tests and RK's checker;
   list for K3 the cross-track test with `scripts/scale78b/blinded_sigma.py`'s reader.
6. **Judges (item 7, J1, J2):** `units-of-block` for A and B; block A's re-judge list = N's units, the reused a0 units
   and θ0, 7 per family (REJUDGED_PINS), reaching N's units in block 0's copy (X5).
7. **Block A's seal (item 10, O7):** each copy seals its own outcome files; block A's seal record names block 0's and
   the scorer block's seal records by SHA-256; Llama's a0-1103 task loss stays the one exception (DESO item 25).
8. **The state rule (item 11):** pull e1 states, verified backup, the user's yes by pod name; the a0 e1 states at
   1104-1107 kept until the references at those seeds have used them.
9. **`C0_SOURCE`'s release-time check (item 12, K6v-4).**
10. **The c0 command-word check (K-1, KR6):** plan_tool checks c0 by its command word (`lean`), the O-ext kinds by
    `unit`, W1-18 by `w1_18`, reading RK's `OEXT_WRAPPER_COMMANDS`.
11. **Idle storage (K-4):** N's seven `o_only_with_regenerate` pods in the scorer block's idle-storage lines; block
    0's printout unchanged.
12. **The kept S4 count** from the untuned pass's dose record (`s4_doses_record.json`), not passed by a caller.
13. **R-16 / R-31:** move plan_tool's seed-only call site to the strict (arm, seed) form; the runner's and the pack's
    are K3's (list them); K3 deletes the seed-only form.
14. **(RK) R-32, R-33:** RK accepts `W1_18_78B` in R-20's form `{files, side_units}`; RK's index and W1-18 record
    checks take exactly the standard names and folders; `plan_for_sigma` refuses (not raises) on a σ that is not a
    finite float.
15. **K6v-1** (an unlisted binary data/ file test) and **K6v-6** (a fingerprint-prefix quote test).

## Acceptance
Block 0 unchanged in behaviour (its plan.json byte for byte, test_42; its printout, caps, funding need, pins, launch
path). The 7-8B suite under the network-deny sandbox (count before and after); the stage-1 kit's 762 unchanged; the
scale78b suite unchanged; all four kit mutation specs in shards under 10 minutes, every mutant killed, none invalid,
new mutants for every new rule; give the lead the full-run commands. List for K3 everything you leave to it.
