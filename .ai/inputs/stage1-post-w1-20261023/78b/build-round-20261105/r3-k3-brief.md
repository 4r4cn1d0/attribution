# R3 builder brief: K3, the kit's runner and pack for blocks A and B

Read first: `B/lead/r3-common.md` (its paths and hard rules bind you). Your worktree: WS = B/ws-k3, detached at
d7eb772. Your report: `R/r3-k3.md`; scratch `R/r3-k3-scratch/` only.

## Owned files (runkit/stage1-78b/)
- **Core:** `setup/job_runner_stage1.py` (RUN78), `pack_setup.py` (PACK), `setup/preflight_stage1.py`, `finisher.py`,
  `README.md`, `tests/test_kit_78b_runner.py`, new `tests/test_runner_ab_78b.py`, `tests/mutation_spec_runner_78b.json`.
- **Smallest changes, only for the items below:** `plan_tool.py`, `rules_78b.py`, `stage1_rules.py`, `orchestrate.py`,
  `host.py`, `launch.py`, `RULES-78B.md`, the other kit tests and mutation specs (each new rule gets mutants in the
  spec of the file it lives in).
- **Block 0's behaviour must not change:** its plan.json byte for byte (test_42), its printout, caps, funding need,
  pins and launch path.
- **Nothing under `scripts/`.** Track P owns `scripts/scale78b/oext_78b.py`, `make_oext_settings_78b.py` and Track S's
  tests in this round. Any change you need there is an open point for the lead.

## Read
- plan-ab.md §1 items 5 (5a, 5c, 5e, 5f), 6, X1, X2, X5, and §2's K3 row.
- GXB, all 19 sets.
- From BR:
  - `r2-k2.md` §7 and §9 and its follow-up's open points (what K2 left you);
  - `r2-k2-verify.md` (K2V-4, K2V-8) and `r2-k2-reverify2.md` (K2R2-1);
  - `r2-r.md` P1-P9 and §11.5 (the references' commands and the terms record);
  - `r1-o.md` §10-§11, `r1-o-reverify.md` §7 and `r1-o-reverify2.md` (W2-4, W2-5);
  - `r1-k1-reverify.md` (KR4, KR5) and `r1-s.md` (the anchor-stop reader).
- Part 2 §2-§4, §8, §15, §16.1 and AM1; DES (all sets).
- The 1B runner's forms that plan-ab item 5 names (RUN1B).

## Build (work in this order, so a stop leaves the most useful part done)
1. **The O-ext commands** (T-O3, R-5, R-18, R-20).
   - Form: `oext_78b.py <command> --family F --index PATH --index-sha256 H`, with the index from the job's
     `OEXT_78B[F]` (engine X) or `OEXT_78B_Y[F]` (engine Y) entry.
   - The `w1_18` kind takes its files from `W1_18_78B` (R-20), never from `OEXT_78B[F]`.
   - In the same change, rewrite the runner's O-ext command-line assertions in `test_scorer_block_78b.py` (R-18), so
     no scorer mutant survives.
2. **W1-18** (5c, K-3, O4, O10, R-53).
   - One pod, one W1-18 check per family, each with its own settings and record. Under [C], OLMo-2-7B's only.
   - The pod ships every file `W1_18_78B` lists. Accept any list in R-20's form `{files, side_units}`, each entry
     path + SHA-256: Track P adds the two frozen readers `scripts/family_probe_reading.py` and
     `scripts/killtest_stage0_reading.py` to that list this round (W2-5).
   - It also ships the lexicon files and judge config that Track O's O10 list names.
   - Each record comes back as `overrefusal_checks__<family>.json` (R-53).
3. **The pack's Mac checks before any O-ext pod** (R-6, R-9, R-23): `oext_78b.py check` on the pinned W1-18 record
   and on the side units' files. Refuse on any failure.
4. **N's seven units** (5e).
   - `o_only_with_regenerate` keyed by (arm, seed); the sealed R_d edit for R units.
   - Acceptance input `n_complete:{arm}:{seed}`.
   - Refuse while `N_UNITS[F]` is null.
5. **The two flags** (5f, R-47). `--w1-18-record` and `--dev100-source` take the 1B forms. R-47: a fixture test
   through the unchanged `oext_eval` must show whether a run under Branch full with a pinned failing W1-18 record needs
   the record at run time. Pass the flag exactly when the unchanged code needs it.
6. **The arm job's O-ext step** (5a, E3). For blocks A and B, the arm, a0_arm and ref_train jobs run `calibrate`, then
   the O-ext run on the job's e1 unit, in the 1B form. Use fallback E3 (b) only if (a) cannot be built, and say why.
7. **The anchor stop** (KR4, KR5, O6).
   - Before `check_keys` / `job_decision` for a stopped family's MAIN_F retrain pod, the runner calls
     `anchor_stop_or_refuse`.
   - The pack carries the stop record.
   - The anchor step's stderr is kept as a file of the pulled tree (name it in the README), so `record-anchor-stop`
     can read the exit-1 message.
   - A cross-track test reads the one shared fixture under `tests/fixtures/` through RK's checker, against K2's
     writer's form and `scripts/scale78b/blinded_sigma.py`'s reader (Track P aligns Track S's own fixture this round).
8. **R-16 / R-31:** move the seed-only call sites (`setup/job_runner_stage1.py:466`, `:483`; `pack_setup.py:432`) to
   the strict (arm, seed) form, then delete the seed-only form. test_41's list ends empty.
9. **R-44** (K2's open point 1): at the pack receipt, re-hash the packed bundle's members that the blinding record names,
   and compare them with the record.
10. **K2R2-1:** a leftover `<part>.new` refuses by name with a clear message, not with FileExistsError. Add a test.
11. **The S1 edit** (K-7): the pack reads OLMo-2-7B's S1 edit under `tmp/stage1-olmo/` only by exact path and SHA-256.
    Tests use fixtures; never open the file.
12. **Engine Y's pack** (X1, PP18, ADD A13, KD9).
    - The pack builds engine Y's bundle from the frozen tree (`tmp/engine-y-34bfd288`, by its pinned identity), and
      every Y kind refuses while `ENGINE_Y` is null.
    - The first Y pod (ruling 10's a0-1101 retrain) re-measures the basis (KD9) before Y carries a block. Build the
      kit's side of that: what the pod records, and the refusal of measured Y kinds until the re-measure is recorded.
    - Port the 1B kit's Y route (`runkit/stage1-olmo/`, read only). K3's Y pack must ship the unchanged `oext_unit.py`,
      not the 1B Y copy at its path, or the wrapper's `CODE` pin refuses it (BR/r1-o-verify.md P3).
13. **The references** (item 6, O2, R-34, R-35, R-37, R-38 amended, R-41, R-42; Track R's P7).
    - The commands run through `scripts/scale78b/refs_78b.py` (`eval_adapter` / `safe_lora` with
      `--family F --seed S --index … --index-sha256 …`).
    - A `b10_certify` kind per reference seed runs against that seed's a0 unit (R-35's table). Its report is the seed's
      `ref_eval` `--certification-report`. A failed certification stops every evaluation-only reference (P2 §16.1).
    - `ref_train` runs under RECIPE_G and `ref_train_bqi` on engine Y.
    - The 1B safety-prompt text file is packed by path and SHA-256 (`0fcc6beb…`).
    - The kit pin per (family, seed) `REFS_78B[F][S]` (null) takes the form Track R's maker prints with
      `--refs-78b F S`.
    - The wrapper's terms records come back with each output and are listed in the retrieval.
    - Block B's plan (`init-block B`) gains the reference jobs, each waiting for its seed's a0 unit and its
      certification. K2 planned only the arm runs, doses and judges.
14. **README.md:** the lean route for blocks A and B, the record steps (`record-gate-78b`, `record-plan-b-78b`, the
    branch and anchor-stop steps), and the new kinds and their pins.

## Acceptance
- **The 7-8B suite passes** under the network-deny sandbox (619 at d7eb772; give the counts before and after).
- **Other suites stay as they are:** the stage-1 kit's 762; scale78b's 698 passed, 2 skipped (run it; Track P's
  changes are not in your worktree); the engine family tests' 95 (`experiments/safety_selection/tests/test_ss_family_codec.py`,
  `test_ss_family_recipes.py`).
- **All four kit mutation specs:** every mutant killed, none invalid, in shards under 10 minutes. Add mutants for
  every new rule, and give the lead the full-run commands.
- **Block 0 is unchanged** in behaviour (see above). No token-shaped file is left in any basetemp.
- **The report** gives each item as done, partial or not done, with R: path:line and the test names. List what you
  leave to K4 (hardening) and every open point.
