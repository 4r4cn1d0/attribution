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
