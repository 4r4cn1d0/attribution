# R3 builder brief: Track P, the padded-tokens tool and three small fixes (scripts/scale78b/)

Read first: `B/lead/r3-common.md` (its paths and hard rules bind you). Your worktree: WS = B/ws-p, detached at
d7eb772. Your report: `R/r3-p.md`; scratch `R/r3-p-scratch/` only.

## Owned files
- **New files** in `scripts/scale78b/`: the tool, its tests and its mutation spec, plus a runner in the form of
  `tests/run_mutants_c_78b.py`, or a spec that an existing runner takes unchanged. Say which.
- **Smallest changes, only for items 2-4:**
  - `scripts/scale78b/oext_78b.py` and `scripts/scale78b/make_oext_settings_78b.py`, with their tests and the O-ext
    mutation spec;
  - the Track S test file that holds Track S's own anchor-stop fixture.
- **Nothing under `runkit/`** (K3 owns the kit this round), `scripts/stage1*` or `experiments/`.

## Read
- GXB: O1, R-20, R-26 (KR5), R-32, R-46, R-53, and the fourth set's anchor-stop form.
- The record form and its reader (K2's): `MAIN/runkit/stage1-78b/plan_tool.py:3725-3732` and `:4009-4035`.
- The a0 basis: `MAIN/runkit/stage1-78b/rules_78b.py:288-310` (`A0_PADDED_TOKENS_PER_STEP`, KCR:104) and `:732-740`
  (`train_scale_of`).
- Part 2 §2.1.
- From BR:
  - `r1-c.md` (Track C's encode-count tool: the precedent for a counts-only Mac tool over sealed files by path and pin);
  - `r1-o.md` §10-§11 and `r1-o-reverify2.md` (W2-4, W2-5);
  - `r1-k1-reverify.md` (KR5) and `r2-k2.md` §7 (KR5's note).

## Build
1. **The padded-tokens tool** (R-46).
   - A frozen $0 Mac tool. Per family, it writes exactly the text-free record that K2's reader takes
     (`PADDED_TOKENS_KEYS`):
     - kind `stage1-78b padded tokens record`; version 1; family;
     - `edits` {edit SHA-256: padded tokens per step};
     - source, utc, recorded_by.
   - It reads each block A and B edit file by path and pinned SHA-256, under MAIN_F's training settings.
   - Padded tokens per step follow the way the engine pads and batches. Read the engine's code under
     `experiments/safety_selection/` and call its own functions where you can, as Track C did; cite path:line.
     Steps = ⌈rows / 128⌉ (GXB O1).
   - Counts and hashes only, and no text on any path (sentinel tests in every mode). Writes are atomic and once-only.
     A file whose SHA-256 differs from its pin is refused.
   - **Lead ruling P-1.** If the padded count depends on the seed (through the row order), an edit's value is the
     largest over seeds 1101-1107, and the record's `source` names the seeds and the rule. If it does not depend on
     the seed, say so, with the evidence.
   - **Lead ruling P-2. A check mode.** On the unedited training set, the tool recomputes the a0 value, so the lead can
     compare it with `A0_PADDED_TOKENS_PER_STEP` before any fill: 38,342.79 on OLMo-2-7B (1,457,026 padded tokens over
     38 steps) and 41,311.74 on Llama-3.1-8B (1,569,846 over 38 steps). Build and test it on fixtures, and give the
     lead the exact command. Do not run it on real data.
   - A test loads the tool's output through the kit's reader (`plan_tool.padded_tokens` or its form check, imported
     read-only) and passes.
2. **W2-4:** `oext_78b.py`'s `check` validates the W1-18 settings under engine X's identity (the engine W1-18 runs on),
   not the running engine's.
3. **W2-5:** the `files` part of the printed `W1_18_78B` adds `scripts/family_probe_reading.py` and
   `scripts/killtest_stage0_reading.py`, each by path and SHA-256 (the two frozen readers W1-18 loads by path and pin).
   Keep R-20's form `{files, side_units}`. K3's pack ships every listed file. If the kit's RK check of that form
   refuses the longer list in your worktree, do not change the kit: report it (K3 accepts any list this round).
4. **KR5:** align Track S's own anchor-stop fixture with the one shared form (the fourth set's form, as RK's checker
   accepts it), so Track S's reader is tested on the form K2's writer writes. K3 writes the cross-track test on the
   kit side.

## Acceptance
- **The scale78b suite passes** under the network-deny sandbox (698 passed, 2 skipped at d7eb772; give the counts
  before and after).
- **Mutation runners:** the O-ext, SR-2 and count-tool runners and your new spec. Every mutant is killed and none is
  invalid. Add mutants for the tool (each refusal, the steps rule, the seed rule, the a0 check) and for W2-4 and W2-5.
- **The 7-8B kit suite** still passes in your worktree (619).
- Give exact commands for the lead's full runs.
