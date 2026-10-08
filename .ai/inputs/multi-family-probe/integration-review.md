# Multi-family probe engine: integration review (rounds 2, 3 and 4)

Date: 8 October 2026. Reviewer: an Opus 5.5 integration subagent of the lead. No pod, RunPod, Hugging Face or held-out data was used. Nothing was staged, committed or pushed by the reviewer.

## Result

- **Integrated and green.** The main checkout holds the round-4 build. Identity `04eb83a3fca6fc77ae81d8975d52ae642f7efafb774759e01ca88b6c3fd51408`. Engine 559 passed, 5 skipped. Stage B 172 passed. Durability 260 passed. All exit 0.
- Already committed: the 8 changed tracked files, through `fd524f6`. That commit was a FOCUS.md edit made with `git commit -a`, and it took them in by accident. All 8 equal the round-2 hashes. Seven are engine files and are final. Round 4 later changed the eighth, README.md, again.
- Waiting for the lead's commit: README.md (modified) and 63 new files. Each of the 71 files equals the final manifest: the round-2 evidence with the round-3 and round-4 changes applied.

## Snapshots and evidence

- Round-2 snapshot: 02:38 IST, before round 3 began. All 69 files equal `round2-evidence.md`.
- Round-4 snapshot: 03:25 IST. Compared with the round-2 snapshot, the only differences are:
  - 5 changed files: `scripts/family_probe_reading.py`, `experiments/safety_selection/README.md`, `tests/test_ss_family_reading.py`, `tests/test_ss_family_codec.py`, `tests/test_ss_probe_runkit.py`;
  - 2 new files: `configs/family-probe-reading-amended-20261008.json` and `runkit/family-probe/second_judge_probe.py`;
  - `configs/study-kt-instruct-r16-b-20261008.json`, copied from the repo and equal to HEAD (`1157fc9d…`). It was not copied back.
- All 7 changed or new files equal the lead's hashes. No cache folder, empty folder or link exists.

## What was verified

1. **Scope.** Against `46064a7` there are 8 changed files and 63 new build files, all owned: `experiments/safety_selection/**`, new files in `scripts/`, `runkit/family-probe/`. The workspace also holds the r16 recipe, which equals HEAD. The 14 `reference/` files are workspace-only and are not integrated.
2. **Code identity.** `04eb83a3…` in both snapshots, at `fd524f6` alone, and in the main checkout. README.md, tests and configs are not part of the identity.
3. **Suites** (the brief's commands, `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

   | Where | Engine | Stage B | Durability |
   |---|---|---|---|
   | Round-2 snapshot | 531 passed, 3 skipped | 172 | 260 |
   | `fd524f6` alone (no new files) | 313 passed, 3 skipped | 172 | 260 |
   | Round 2 in the main checkout (before round 4) | **1 failed**, 530 passed, 3 skipped | 172 | 260 |
   | Round-4 snapshot | 559 passed, 5 skipped | 172 | 260 |
   | **Main checkout, final** | **559 passed, 5 skipped** | **172** | **260** |

   - Skips: 3 CUDA tests, and 2 real-Qwen ARC calibrations (see "Not verified").
   - The round-2 failure came from a name rule in `test_ss_family_codec.py`. The new Qwen recipe `study-kt-instruct-r16-b-20261008.json` matched it. Round 4 now decides by family prefix and asserts exactly 26 family recipes.
4. **Recipe identities.** Every recipe and data config at HEAD (18 and 5) has the same `config_sha256` and `training_identity` under the old engine and the new one. This includes the Qwen r16 recipe `86079a35…`. The other 29 config files are byte-identical.
5. **Round-3 reading amendment.** The amended bars file matches FOCUS.md "Amendment to the family-probe reading bars": 20–55 window, edge 2·SE, `arc_z` 1.96, short answers under 5 tokens, saturation above U_ft 0.75. In `scripts/family_probe_reading.py`:
   - prompt-clustered SE(U) uses the sample SD over √n (235–241);
   - edge band at 342–347;
   - paired ARC SE² = (b+c)/n² − (b−c)²/n³ at 351–364;
   - two-seed SE² = (SE₁² + SE₂²)/4 + SE₀² at 405, the 21:50 UTC clarification.
   - `second_judge_probe.py` runs locally only: no network, pod, subprocess or delete call.
6. **Pod safety** (read in the code; the kit files are unchanged since round 2):
   - #9 cap gate: `cuda_preflight_family.py:159-172`, `orchestrate.py:195-202, 281-285`, `job_runner_probe.py:50-58, 131-137`.
   - #10 stop: retried and confirmed. `host.py:125-141, 382-384`, `finisher.py:148-151, 188-209`, `orchestrate.py:308-311`.
   - #11 orphans: `host.py:151-161, 172-182, 205-215`.
   - #12 budget: an `flock` lock shared by the kits, and intents counted. `budget.py:25-34, 74-87`, `launch.py:127-135, 163-175`, `host.py:341-356`.
   - #13 finisher deadline: `finisher.py:64-81, 216`.
   - #14 sleep: `launch.py:178-180` (`caffeinate -i`), `orchestrate.py:109-112, 254-255`.
   - **No delete or terminate path.** The only RunPod writes are `POST /pods` and `POST /pods/{id}/stop`.

## Mutation runner: defect and correction

- **Defect (rounds 1 and 2).** `mutate.py` and `mutate2.py` gave pytest `--basetemp <root>/../mut-tmp/<name>`, and that parent folder did not exist. Every mutant stopped with a setup `FileNotFoundError` and was counted "killed". I reproduced this: 117 of 117 "1 error".
- With the parent folder created, round 2 gave 115 killed and 2 survivors:
  - `clock-guard-dict` is equivalent, because `str(dict)` contains the values;
  - `download-blob-check-off` showed that the blob-hash check was not tested.
- **Correction (round 4, `mutate_v2.py`).** The runner now:
  - creates the basetemp parent;
  - requires a clean baseline;
  - runs whole test files without `-x`;
  - reads JUnit results: killed only on a test failure, "invalid" on an error.
- Results, recounted from the jsonl files:
  - Set 2: 116 mutants, 115 killed, 1 survived (`clock-guard-dict`, equivalent), 0 invalid. Baseline 183 passed, 2 skipped, no failure or error.
  - Set 4 (rounds 3–4): 30 of 30 killed, 0 invalid. Baseline 61 passed, 2 skipped.
  - Every kill has at least one failing test and no errors.
  - `reading-arc-edge` was dropped, because the ARC rule became the interval rule (set-4 `arc-*` mutants).
- The blob gap is closed. `test_the_download_refuses_a_weight_whose_content_differs_from_its_blob_name` kills `download-blob-check-off`.
- **Re-run by the reviewer.** I ran 5 mutants on a copy of the round-4 snapshot, with a real basetemp parent and no `-x`. Four were drawn at random (seed 20261008), plus the blob mutant. All 5 died by test failure:
  - `reading-same-eval-off`: 1 failed;
  - `exclude-already-removed-off`: 1 failed;
  - `launch-no-scrub`: 1 failed;
  - `runner-over-limit-not-wired`: 1 failed;
  - `download-blob-check-off`: 2 failed.

## Per-item status (review findings 1–23, D1, rank-16, round-3 amendment)

"Killed" means killed by a real failure under the corrected runner. The item-to-mutant map is inferred from the mutant names.

| Item | Subject | Mutants | Result |
|---|---|---|---|
| 1 | Guard input over the limit for OLMo/Llama; scored both ways | 4 | killed |
| 2, 15 | Failed batch proof or tokenizer ends the candidate and skips later g16 ones | 4 | killed |
| 3, 4 | Reading ties `--manifest` and the family to the units | 2 | killed |
| 5 | Token scrub names from `HF_TOKEN_ENV` | 2 | killed |
| 6 | whoami-v2 read whole | 2 | killed |
| 7 | Gated step ignores a stale record | 2 | killed |
| 8 | HF endpoint pinned where the token is used | 3 | killed |
| 9 | Cap projection, cap gate, e1 refusal | 7 | killed |
| 10 | Stop retried and confirmed; in-pod timer as a second path | 5 | killed |
| 11 | Orphan pod after a failed create | 4 | killed |
| 12 | Shared budget lock; intents counted | 6 | killed |
| 13 | Finisher deadline | 2 | killed |
| 14 | caffeinate; final read after deadline | 3 | killed |
| 16–19 | Gate before `record_first`; model text is not a secret; started job not stopped; one launch per kit | 4 | killed |
| 20–23 | Reading: judge identity, seal and retry, same evaluation, bars pin | 5 | killed |
| D1 | Token removed from long-lived processes | 3 | killed |
| Rank 16 | r16 ladder for the 1B probes only | 2 | killed |
| Round 3 | Edge band, two-seed SE, saturation, ARC interval, short answers, cross extremes, verdict combine, second judge | 30 | killed |
| Weights | Blob-hash check of downloaded `.safetensors` | 1 | killed (round-4 test) |

## Not verified

- CUDA paths. The 3 CUDA tests were skipped. Nothing ran on a GPU.
- Real RunPod and Hugging Face calls. All kit tests use fakes.
- The Granite second judge was not run. It needs the local GGUF model, and its tests use fakes.
- `test_the_arc_rule_reproduces_the_qwen_calibrations_on_the_real_units` (2 cases) looks for units at `ROOT.parents[2]`. That is the main checkout's `tmp/` only when the code lives in the workspace. In the main checkout it resolves to `/Users/spiderishi`, so it always skips there. Round 3 reports that it ran in the workspace. Fix: use `ROOT / "tmp"` when that folder exists.

## Open limits

- Caps and projections are estimates. `projected_job_upper_s` rests on one preflight measurement and a 1,000 s overhead floor from the Qwen-7B check.
- The budget lock covers only family-probe kits. Pods of other kits are counted from the account listing, at their recorded cap or 15 h.
- Before the job starts, an unconfirmed stop is logged but not retried. If the 2-min timer move also fails, the pod runs to its cap.
- A create whose pod appears more than 60 s after a failed reply is found at the next launch round or the next launch. Until then its intent counts at $1.75/h.
- The finisher stays awake only if the operator starts it with `caffeinate -i`. This is documented but not enforced.
- On macOS, `ps -E` shows a process's start environment. A token removed later from `os.environ` stays visible there while the process lives.
- Cross-extreme bounds: an unscored answer is read as Unsafe and as Safe. If the two verdicts differ, the bar reads TOO CLOSE. This is per the amendment; how often it happens on OLMo/Llama is unknown.
- `clustered_se2` uses the sample SD (n − 1). The amendment says "SD"; n − 1 is slightly conservative.
- The displayed E interval (`family_probe_reading.py:426`) uses a fixed 2. The verdict uses `edge_se_multiple`, which is also 2.
- The `orchestrate.py` docstring names a `full` command that `main()` lacks.

## Round 5 (8 Oct): token mean, LR schedule, baseline reuse

Date: 8 October 2026, 04:34–05:01 IST. Reviewer: an Opus 5.5 integration subagent of the lead. No pod, RunPod, Hugging Face or held-out data was used. Nothing was staged, committed or pushed by the reviewer.

### Result

- **Integrated and green.** The main checkout holds the round-5 build. Identity `552538748acec1a8ffd1ee976b9eb3c3fdfe9ca01b8148ee8810291409357441` (was `04eb83a3…`). Engine 599 passed, 3 skipped (CUDA). Stage B 172 passed. Durability 260 passed. All exit 0.
- Waiting for the lead's commit: 15 changed files, 31 new files and this review file. Nothing else in the main checkout is changed.
- The build is integrated byte for byte as reviewed. **None of the should-fix items below is fixed yet.**

### Snapshot, preflight and copy

- Snapshot: `cp -a` of `tmp/claude-workspaces/token-mean-loss-20261008/workspace` at 04:34 IST. Against the workspace manifest (the 2,231 blobs of `42eb258`): 15 changed, 31 new, 0 deleted. No cache folder, `.pyc` or `.DS_Store`. All 46 SHA-256 values equal `round5-evidence.md`.
- Preflight: HEAD `a195979`, a descendant of `42eb258`. That commit adds only `research/review/2026-10-08-erosion-amplifiers-literature.md` (it was untracked before). `git diff 42eb258 HEAD` on the 46 paths is empty. The tree was clean (`tmp/` is ignored). Before the copy, the 15 changed files in the main checkout equalled the manifest, and none of the 31 new paths existed.
- Copy: `cp` of the 46 files from the snapshot. 46 of 46 hashes OK in the main checkout, again after all suites. File modes 644, as before. No new cache folder. The `__pycache__` folders from 2 October in `experiments/` are old, ignored and were not touched.

### Code identity and suites (main checkout)

Commands: `PYTHONDONTWRITEBYTECODE=1 <venv>/python -B -m pytest -q -rs -p no:cacheprovider --basetemp=<scratch>`, from the repo root.

| Suite | Paths | Result |
|---|---|---|
| Engine | `experiments/safety_selection/tests experiments/minimal_safety/tests` | **599 passed, 3 skipped**, exit 0 |
| Stage B | `experiments/safety_decision_policy/tests` | **172 passed**, exit 0 |
| Durability | `experiments/durability/tests` | **260 passed**, exit 0 (default pytest temp) |

- Skips: 3 CUDA tests only. The 2 real-Qwen ARC tests (`test_the_arc_rule_reproduces_the_qwen_calibrations_on_the_real_units`) now run and pass in the main checkout. The round-4 "Not verified" item about them is closed by the round-5 path fix.
- Durability with `--basetemp` under the reviewer scratch folder: 259 passed, 1 failed (`test_logs_and_acknowledgements_name_no_operation_arm_or_choice`). That scratch path contains `attribution-`, which the test forbids in the journal (`test_dur_stage_b.py:412-414`). This is old and not from round 5: the durability tree equals `42eb258`. With the default pytest temp folder: 260 passed.
- Code identity in the main checkout: `55253874…7441`. Changed identity files: `attribution.py`, `config.py`, `engine.py`, `runner.py`.

### Review lenses (4 of 4: pass with minor findings, no blocker)

**1. Loss and schedule math: pass-with-minor.**
- Should-fix: no test ties the rate used by `optimizer.step()` to the `lr` written to `steps.jsonl`. A mutant that applies the next step's rate (`runner.py:475`) passes every behavioural test. Fix: adopt the reviewer's spy test `test_runner_wiring_applied_rate_and_actual_rows` (scratch `r5/loss-lr/ws/.../test_review_token_mean_lr.py`) and add this mutant.
- Minor: `engine.py:276` computes `peak*k/warmup`; HF computes `peak*(k/warmup)`. They differ by up to 1 ulp when warmup is not a power of 2. Recipe G (warmup 4) is bit-identical. The docstring says "exactly", and the test tolerance (1e-12) cannot see the difference.
- Minor: all 12 G recipes list e3 checkpoints, but `schedule_until` is e1. A direct init→e3 job trains q and e1 before it refuses. An `attributes` job on a G recipe can never get its e3 state. The probe kit trains to e1 only, so the probes are not affected.
- Minor (design note): each arm's cosine horizon is its own plan's e1 (fixture: a0 15 steps, removal arm 13). This is the HF convention. GPT must confirm it before recipe G is used with removal or edit arms.
- Checked: the token-mean gradient equals an independent reference (relative error ≤ 4e-7, micro-batch 1–5) and HF's labels loss. Default path bit-identical to `04eb83a3` (88 tensors, `steps.jsonl`, fingerprints). Post-warmup rates bit-identical to transformers 4.56.2 (44,320 of 44,320). Resume is exact.

**2. Evaluation equivalence: pass-with-minor.**
- Should-fix: reuse does not compare the two units' `assets.json` (GPU, CUDA, cudnn, driver, packages, numeric settings, policy identity). See `family_probe_reading.py:207-215` and `plan_tool.py:74-91`. A pod-level numeric shift would be confounded with the treatment. Until fixed, diff the two `assets.json` environment blocks by hand before any reuse reading.
- Minor: `eval_config` leaves out `train.lm_head_chunk_tokens` and `train.gradient_checkpointing`, which evaluation reads (`runner.py:548, 611`; `loaders.py:184-186`). No exposure now: all 36 1B recipes have (1024, false).
- Minor: `evaluation_path.py:57-58` does not hash decorators of top-level functions, and a second definition with the same name hides the first.
- Minor: the allow-list is wider than its reason (`attribution.py` is `*`; `validate_recipe` and `accumulate_gradients` also run in evaluation jobs; some names do not exist). Each change in this pair was checked by hand and is harmless.
- Minor: `plan_tool` checks that `COMPLETE.json` exists, but not its contents or the baseline engine's certification. This is a cost risk, not a science risk.
- Checked: an independent AST diff gives exactly the certificate's changed symbols. The certificate regenerates byte-identical (`63700221…`). The evaluation code is byte-identical. Pairing the `04eb83a3` OLMo baseline with a `55253874` G fine-tune is safe on code, if the G pod reports `engine_sha256` = `55253874…` exactly and the `assets.json` hand diff shows no difference.

**3. Scope, identity and suites: pass-with-minor.**
- Should-fix: `family_probe_reading.py:201-215, 222` changed the default (non-reuse) path. An e1 unit with `resume_from` null and the init unit's recipe and engine is now accepted with `baseline_reuse: null`; `42eb258` refused it. Fix: record reuse whenever e1 does not resume from the init unit, and add a test.
- Minor: `family_probe_reading.py:202` now refuses a second seed's e1 unit that resumed from its own init unit. This fails closed, but only after the spend. Fix: check the resume target for the first seed only, or document it.
- Minor: the durability path test above (old; not from round 5).
- Minor: the evidence file lacks the suite commands and counts, and the 2 ARC tests depend on where the code sits. This section now records the counts.
- Minor: no recorded brief or FOCUS entry authorizes the LR schedule or the 12 `-g-` recipes (`brief-round5.md`; `FOCUS.md:65-68`).
- Minor: `cuda_preflight_family.py:331-336` does not apply the LR schedule, so the scheduled path never runs on a GPU before a pod job.
- Checked: 46 hashes; manifest equals `42eb258`. All 58 earlier configs keep their config hash and training identity under both engines. Goldens pass unchanged. Kit defaults (`RECIPE='b'`, r64) are unchanged.

**4. Mutation and attribution: pass-with-minor.**
- Should-fix: the Adam proxy uses the end-point rate of each checkpoint (`runner.py:900-903`). Under a cosine that ends at a checkpoint, that term is close to 0 (G: the e1 term weighs about 1/445 of q). Pre-register one rule before any scheduled-run attribution: (a) the mean rate over the interval, (b) a row-specific rate, or (c) the end-point rate, documented, with per-checkpoint parts reported.
- Should-fix: no test checks that the scheduled rate reaches `adam_score`, and the rate is not written to any output. Mutant X1 (rate computed but unused) survived 42 tests.
- Should-fix: no test or golden pins the default (per-example) attribution path. Mutant X2 (token-mean weights always on) survived. By reading, the default path is unchanged today.
- Minor: `w_i` comes from the first epoch only. Under the Gate B reshuffle this does not match the e3 objective (simulated 3-epoch mean / epoch 1: p5 0.87, p95 1.18).
- Minor: rows in an epoch's short last step are under-weighted by E_last/E (2.0 at 4,800 rows / 128).
- Minor: G recipes list e3 attribution checkpoints with `schedule_until` e1 (as lens 1).
- Minor: stale docstrings at `attribution.py:4, 26-27`. The group GradSim is an unweighted mean of row cosines by design.
- Minor: the builder's mutation baseline "3 skipped" is 1 CUDA test and 2 ARC location skips, not 3 CUDA tests.
- Checked: 33 of 33 builder mutants killed by failures inside a test, 0 errors. The reviewer re-ran 4 (2 drawn at random); all 4 were killed.

### Not verified

- CUDA paths: the 3 CUDA tests were skipped. Neither token mean nor the LR schedule has run on a GPU.
- The `assets.json` comparison for a real reuse pair. No G unit exists yet.
- The "38 steps of e1" figure in the G recipes' purpose text.
- The reviewers' extra tests and mutants (spy test, X1, X2, decorator and shadowing cases) ran only in their scratch copies. They are not in the repo.

### Open limits and decisions before any `-bt-` or `-g-` run

- Scope: the LR schedule and the 12 `-g-` recipes need a FOCUS entry and the user's approval first (`FOCUS.md:68`). The `-bt-` recipes need the same. As shipped they are opt-in: `RECIPE='b'` and `lr_schedule` constant are the defaults.
- To fix first: the 6 should-fix items above (applied-rate test; `assets.json` check; default-path reading pair rule; Adam-proxy rate rule; rate-used test and output; default attribution pin). Any engine edit changes the identity, so the evaluation certificate must then be regenerated and re-pinned (`family_probe_reading.py:79`).
- Decisions for GPT: `schedule_until` versus e3 checkpoints (a config refusal changes the 24 recipes' bytes); the per-arm cosine horizon; the Adam-proxy rate rule; the epoch weights for Gate B.
- Reuse tonight: the G pod must report `engine_sha256` = `55253874…` exactly, and the two units' `assets.json` must be diffed by hand.

## Round 6 (8 Oct): review fixes S1–S6 and M1–M8

Date: 8 October 2026, 09:50–09:56 UTC (15:20–15:26 IST). Reviewer: an Opus 5.5 integration subagent of the lead. No pod, RunPod, Hugging Face, GitHub or held-out data was used. Nothing was staged, committed or pushed by the reviewer.

### Result

- **Integrated and green.** The main checkout holds the round-6 build. Identity `e49a978c5fa27c3ba4bb1570ac8b24501e09bf8db5c35e31ffba90bf775cdc06` (was `55253874…`). Engine 756 passed, 3 skipped (CUDA). Stage B 172 passed. Durability 260 passed. All exit 0.
- Waiting for the lead's commit: 17 changed files, 8 new files and this review file. Nothing else in the main checkout is changed by this integration.
- The build is integrated byte for byte as reviewed. **None of the findings below is fixed yet.** One is should-fix (lens 2: the kit does not check the pod environment before spend).

### Snapshot, preflight and copy

- Snapshot: `cp -a` of `tmp/claude-workspaces/review-fixes-round6-20261008/workspace` at 09:50 UTC. The workspace `manifest.json` equals `git archive 8c026ee` (all 2,263 blobs). Against it: 17 changed, 8 new, 0 deleted. No cache folder, `.pyc` or `.DS_Store`. All 25 SHA-256 values match the prefixes in `round6-report.md`. The certificate (`ebc6b05a…0334`) and `family_probe_reading.py` (`88483401…a5ad5a`) match in full.
- Count correction: lens 1 wrote "18 modified, 7 added". The correct split is 17 changed and 8 new: none of the 8 new paths exists at `8c026ee` or `074d19f` (`git cat-file -e`).
- Preflight: HEAD `074d19f`, a descendant of `8c026ee`. Since `8c026ee`, the commits touch only `research/` and `.ai/handoffs/2026-10-06-general-implementation.md`. `git diff` and `git log 8c026ee..HEAD` on the 25 paths are empty. Before the copy, the 17 changed files equalled the manifest and `8c026ee`, and none of the 8 new paths existed. The tree was clean except one untracked file that is not part of this round: `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md`. It was not touched and is not in the add list.
- Copy: `cp` of the 25 files from the snapshot. 25 of 25 hashes OK in the main checkout, again after all suites. File modes 644. No new cache folder (84 before, 84 after; all old). The workspace still equals the snapshot.

### Code identity and suites (main checkout)

Commands: `PYTHONDONTWRITEBYTECODE=1 <venv>/python -B -m pytest -q -rs -p no:cacheprovider --basetemp=<scratch>/integrate-round6/bt-<suite>`, from the repo root. The logs record the commands (scratch `pre-gate-b/integrate-round6/suite-*.log`).

| Suite | Paths | Result |
|---|---|---|
| Engine | `experiments/safety_selection/tests experiments/minimal_safety/tests` | **756 passed, 3 skipped**, exit 0 |
| Stage B | `experiments/safety_decision_policy/tests` | **172 passed**, exit 0 |
| Durability | `experiments/durability/tests` | **260 passed**, exit 0 |

- Skips: 3 CUDA tests only. The 2 real-Qwen ARC tests run and pass here. 756 corrects the builder's 754 (taken before the last tests were added) and equals lens 1's corrected count.
- Durability ran with `--basetemp` under a scratch path that contains `attribution-`: 260 passed. M8 closes the round-5 path item.
- Code identity in the main checkout: `e49a978c…cdc06`. Changed identity files: `attribution.py`, `config.py`, `engine.py`, `jobs.py`, `runner.py`. The certificate pin at `family_probe_reading.py:88` is `ebc6b05a…`.

### Review lenses (3 of 3: pass with minor findings, no blocker)

**1. Scope, identity and suites: pass-with-minor.**
- Minor: `scripts/evaluation_path.py:125` (also :138, :171, :179, :214, :349) uses `str | None` without `from __future__ import annotations`, so the tool no longer imports under the system python3 (3.9.6), which its docstring names. Fix: add the import or name the venv python. Outside the identity.
- Minor: `jobs.py:157-161` (M1) calls `names.index(target)` before `run_one` checks for an unknown checkpoint (`runner.py:304`). On a warmup recipe an unknown target gives a bare `ValueError`, not `JobError`. It fails closed. Engine edit: later round.
- Minor: test gap in the S1 difference cases (`test_ss_family_reading.py:886-897`): `machine`, `deterministic_algorithms` and `cuda_env` have no case; the reviewer's mutants that ignore each one survive. Test-only fix.
- Minor: the builder's engine count (754 + 3) predates the last tests and the logs lack the commands. Final: 756 + 3 CUDA (confirmed above).
- Minor: S1 (`family_probe_reading.py:167-185`) reads only `assets.json['environment']`; the policy block is not compared and the report does not say so. The driver is recorded, not compared. GPT decides.
- Minor: the round-5 decision `schedule_until` (e1) versus the e3 attribution checkpoints of the 12 G recipes is not carried into the report's Unresolved list.
- Minor: work beyond the literal S/M list (the `global_writes` screen, the lock and pod-tree rules, the plan_tool check against `setup-receipt.json`, a third certificate pair). All tested and covered by mutants, but the brief text is not recorded. GI III to confirm these and S3 option (a).
- Checked: 25 paths; identity `e49a978c`; 75 configs keep their bytes, config hash and training identity under both engines; S5 golden regenerated from `8c026ee`; inventories and certificate regenerate byte-identical; 74 of 74 builder mutants killed on the final snapshot by the reviewer's own runner; M8 path independence.

**2. Reading and baseline reuse: pass-with-minor.**
- Should-fix: the kit never checks the S1 environment before money is spent. `plan_tool.baseline_record` (`plan_tool.py:94-119`) does not call `environment_of`, and no step compares the new pod with the baseline before calibrate. Fix: store the match record and lock SHA-256 in `plan.json`; compare after PREFLIGHT-DONE; stop the pod on a mismatch.
- Minor: the policy block is not compared (as lens 1). Fix: compare it without `trainable_parameters` (rank-dependent), or document why `eval_config` is enough.
- Minor: the same-run branch (`family_probe_reading.py:279-281`) compares no environments; an init unit copied to another pod is accepted. Fix: call `environments_match(..., one_pod_allowed=True)` there too.
- Minor: the compared lock is a full pip freeze that includes unpinned `setuptools`; a newer setuptools on a later pod would refuse every reuse. Fix: pin it, or leave pip/setuptools/wheel out of the compared freeze.
- Minor: `engine.py:__all__` is in `TRAINING_ONLY` and the certificate, but no pair changes it. Drop it or say it is unused.
- Minor: `tmp/family-probe-olmo2-1b/gate_a_olmo.py:75` pins the reading at `f69d853e`; after round 6 lands it refuses to re-run. Re-pinned in scratch: PASS, identical aggregate. Keep historical or re-pin with a note.
- Minor (old, not round 6): in two-seed mode the top-level `E_pp` is the first seed's E (`family_probe_reading.py:571-577`); the gate uses the mean. Rename or label it.
- Checked: the round-6 reading accepts tonight's OLMo Gate A units in every mode with identical numbers and verdicts; S1 perturbations refuse as designed; driver-only differences gave byte-identical CUDA preflight samples on 3 drivers; all 3 certificate pairs re-verified; a Gate B reuse simulation is accepted through `55253874→e49a978c`.

**3. Training and attribution: pass-with-minor.**
- Minor: `calibrate` (`runner.py:1199-1226`) does not check its whole chain; with a G recipe, plain calibrate trains q and e1 before it refuses at e3. The family-probe runner passes `--checkpoints e1` (safe); the kill-test runner calls plain calibrate. Fix in the next engine round; until then run G only with `--checkpoints` up to `schedule_until`.
- Minor: the 12 G configs have `schedule_until` e1 but attribution checkpoints `[q, e1, e3]`, so attribution can never run under G. Decide (a) a config refusal, (b) `['q','e1']`, or (c) G is probe-only, before G is used for Gate B or C.
- Minor: the M1 `ValueError` versus `JobError` for an unknown target (as lens 1).
- Minor: the deferred engine changes (run-time numeric/RNG guard; lock SHA-256 in `assets.json`) change the identity, and attribution refuses a0 states trained by other code (`runner.py:815-817`). Decide the order now, or accept retraining a0 seed 1101 to e3 (114 steps at 1B) before Gate C.
- Minor: the S5 golden does not pin the rest of the `attributes()` result dict or the token-mean constant (BT) path. Optional fix: add both to `attribution_digest.golden_record`.
- Checked: the default recipe-B training path is bit-identical to `8c026ee` (states, steps, fingerprints, saved tensors), and so is BT; the removal-arm golden is reproduced; M6 matches HF schedulers in 110 of 110 cases; S3 cannot move Gate C's decision under recipe B; M1 refuses a run-one job before the model loads.

### Not verified

- CUDA paths: the 3 CUDA tests were skipped. The scheduled path and the M7 preflight have not run on a GPU.
- Mutation testing was not re-run in the main checkout. Lens 1 ran 74 of 74 on the snapshot, whose 25 files are byte-identical to these.
- `evaluation_path.py` under the system python3 was not re-tested here.

### Open decisions for GPT before any Gate B pod spend

1. Lens 2 should-fix: an environment check before spend. Until it exists, diff the new pod's `assets.json` environment block and `environment-linux.lock` against the baseline by hand after PREFLIGHT-DONE and before calibrate.
2. Policy-identity scope for S1, and recording (not comparing) the driver.
3. G recipes: `schedule_until` versus e3 attribution checkpoints; the calibrate chain check.
4. The order of the deferred engine changes versus the Gate B a0 runs.
5. Pin `setuptools` (or exclude it from the compared freeze).
6. The `gate_a_olmo.py` reading pin.
7. Confirm S3 option (a) and the beyond-brief work; record the round-6 brief text beside the workspace.
