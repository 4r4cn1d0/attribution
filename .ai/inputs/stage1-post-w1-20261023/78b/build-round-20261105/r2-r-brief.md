# R2 builder brief: Track R, the 7-8B reference settings (and Track O's follow-up)

Read first: `B/lead/r1-common.md` (its paths and hard rules bind you; this round's worktree is WS = B/ws-r, detached
at the R1 merge commit). Your report: `R/r2-r.md`; scratch `R/r2-r-scratch/` only.

## Owned files
New files under `scripts/scale78b/`: `refs_78b.py` (a wrapper over the unchanged `eval_adapter.py`, `safe_lora.py` and
`overlap_similarity.py`, or parity-tested copies where a seam would force a false label: the lead's T-O1 / O3 rule, as
Track O did), settings per family F (`eval_adapter__F.json`, `safe_lora__F.json`, `overlap_similarity__F.json` only if
the `similarity` kind is built), a maker or index if needed, `tests/refs/` with a mutation spec and runner. One new
recipe config: Llama-3.1-8B's recipe G at LR 5e-5 under `experiments/safety_selection/configs/` (DES F2; GXB O11).
For the follow-up only, Track O's files under `scripts/scale78b/` (`oext_78b.py`, `make_oext_settings_78b.py`, their
settings and `tests/oext/`). Nothing under `runkit/` (K2's and K3's), `scripts/stage1/`, `scripts/stage1_s1/`.

## Read
plan-ab.md §1 item 6, X2, X3 and §2's Track R; the lead's build rulings `R78/lead-rulings-ab-build-20261108.md` (all
thirteen sets; O2 on B10, O11, T-O1, O3, R-5, R-20 to R-23); Part 2 §3 (the references and their settings), §4.4,
§16.1 (B10's stop rule); DES F1, F2; the 1B settings and scripts (`scripts/stage1_s1/eval_adapter.py`, `safe_lora.py`,
`overlap_similarity.py` and their settings; their literal settings pins, R: eval_adapter.py:98, safe_lora.py:97,
overlap_similarity.py:69, and eval_adapter.py:1579-1590's self-hash rule); `R/r1-o.md` and its verifiers' reports (the
route Track O took and why).

## Build
1. **The decisive check first** (as Track O's): can the wrapper run each 1B script with per-family settings while
   every 1B file stays byte for byte and no record names a file it did not load? Report it at the top; choose the
   wrapper or the copy route per script, and say why.
2. **Settings per family:** `eval_adapter__F` (F's manifest, MAIN_F, the safety-prompt prefix as a user-turn prefix,
   the scale points λ 1, 0.9, 0.75, 0.5, 0 by fingerprint-accepted regeneration; DES F2); `safe_lora__F` (the family's
   block count and K = 78 of 224 matrices, 1B's share, DES F2; the base model pins null until the lead's Hub read);
   B10's certification settings in the 1B form (GXB O2: one certification per reference seed against that seed's
   block-B a0 unit; its report is `ref_eval`'s `--certification-report`).
3. **Llama's recipe-G config at LR 5e-5:** equal to the existing Llama G config
   (`study-kt-llama31-8b-r64-g-mb2-20261011.json`) except the learning rate (and any field the loader derives from it);
   a test that lists every differing field; its generation and guard blocks hash to the 1B pins (PLAN-AB §5 C3's
   expression). Then fill Llama's recipe G in Track O's O-ext settings (`oext_unit__llama31-8b`) through Track O's
   maker, as T-O2's step, on a copy in your tests only: the committed fill is the lead's recorded step.
4. **Track O's follow-up** (from `R/r1-o-reverify2.md`): W2-1 (after a branch fill, the printed `OEXT_78B[F]` and
   `OEXT_78B_Y[F]` forms include the W1-18 record entry, so no hand edit is needed; a test); W2-2 (the re-verifier's 3
   surviving mutants with their targeted tests); W2-3 (a fault after a null pin exits 2, not "waits").
5. The `similarity` kind's settings only if items 1-4 are done and verified with room to spare (DESO item 28); else
   say "not built".

## Acceptance
Parity on the 1B fixtures; every 1B file unchanged (`git diff --stat` empty for `scripts/stage1`, `scripts/stage1_s1`);
the scale78b suite under the network-deny sandbox (count before and after); every mutant killed in shards under 10
minutes, none invalid; the lead's full-run commands.
