# Fix report, track A = T2: the 7-8B cap rule and its measured basis (fix round)

Status: DONE (report finished 2026-11-05 15:08 UTC; `date -u` read at 15:07:32 UTC right before; the skeleton was
written at 14:47 UTC). Worker: the Fable fixer of track A. Worktree:
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-a`
(detached at fb51421; `git status --porcelain` prints `?? runkit/stage1-78b/` only, before and after). No git state
changed anywhere (no add, commit, stash, checkout; the rename was a plain `mv` of an untracked file). No pod, spend,
network, install, download, agent or message. The main checkout was read by absolute path only; the only files opened
under its `tmp/` are the nine allow-listed timing names of the 17 measured kits (numbers and key names printed, no
text). Scratch (evidence, not for merge): `…/scratchpad/b78/reports/fix-A-mutants.json` and
`…/scratchpad/b78/reports/fix-A-scratch/{suite-before.txt, suite-after1.txt, suite-after2.txt, runner-run1.txt,
cmd-golden.txt, cmd-block0.txt, cmd-e-caps.txt}` (28 KB; the scratch repos and pytest basetemps were deleted).

Governing texts read: the lead's rulings (full), the addendum (full; A1, A5, A8 used), the readiness plan (T2, T4;
lines 1-483) and its check (full), build-A.md and verify-A.md (full), the kit's six round-1 files (full), the stage-1
kit's recipe pins (`stage1_rules.py:398-406`), the two main configs' `generation` blocks, and the key trees of two
real units' `PREFLIGHT-DONE.json` and `verification.json` (numbers only).

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference.

## 1. Files changed (all under `runkit/stage1-78b/` in the worktree; all untracked new files of round 1)

| File | Round 1 SHA-256 | Now | Lines | What changed |
|---|---|---|---|---|
| `rules_78b.py` | `56ea39a9…` | `bd785d45…` | 744 -> 832 | A-V1 (`batch_count`; the two drift refusals in `s_obs_from_progress`); A-V3 (`check_keys(family, kind, recipe, engine, gpu, manifest, bank)`; `BANK`, `GREEDY_PROMPTS`, `HARM_SAMPLES`); A-V4 (`finite()` in `launch_allowed`); A1 (`RECIPE_S`, `S78_KINDS`, `CONFIG_SHA256`, `recipe_s_or_refuse`; the gate in `job_decision`); the T4 interface (`preflight_fields(preflight_done, verification)`, `job_decision(family, preflight_done, verification, …)`, `pod_dry_run(…)`); `import re`; the docstring (keys, S_78, the two documents, the A5 convention). |
| `derive_78b_basis.py` | `e020931f…` | `594f95cf…` | 417 -> 440 | A-V6 (`PLACE_OF`, `in_place`; `check_path` with exact names, the place check, the forbidden parts; gate order name -> place -> forbidden); the docstring's `(README)` -> `(RULES-78B.md)`. The derivation itself is unchanged. |
| `RULES-78B.md` (was `README.md`) | `5205bc07…` | `9b097bba…` | 141 -> 227 | Renamed (item 5); the public functions the T4 kit calls with exact signatures and refusals; the A5 constants convention; A1 under KD8; A-V1/A-V2/A-V6 in the file table and KD11; the limits (RECIPE_S null, ENGINES X only, `ref_train_bqi`). |
| `tests/test_rules_78b.py` | `f077815b…` | `bf226524…` | 789 -> 1067 | New tests 05c (A-V1), 05d (A-V2), 07b (A1), 10b (A-V4), 12b (the T4 interface); test 3's binding assertion (A-V5); test 7 widened (A-V3; `keys_of` helper; the bank equals the basis); test 12 on the two documents (`fake_preflight_done` without `untuned_projected_s`, as the 17 real files; `fake_verification`); test 13's required ids; test 15's A-V6 cases; the docstring. |
| `tests/mutation_spec_rules_78b.json` | `5fade2c0…` | `e7c8ae4c…` | 88 -> 127 | 35 -> 51 mutants: 16 new (§2); `T2-m-derive-allowlist-off` replaced by `T2-m-derive-name-and-place-off` (its old find text no longer exists; see A-V6). |
| `measured-basis-78b.json` | `fc92a568…` | `fc92a568…` | unchanged | **BASIS_SHA256 unchanged** (no fix needed the basis). |
| `tests/run_mutants_78b.py` | `0d742104…` | `0d742104…` | unchanged | — |

Full hashes (M, `shasum -a 256`, 15:06 UTC): rules `bd785d4505eb3866ca63b1dcc86ace46d4ae75673a2c391469528d6050be531b`;
derive `594f95cf741cb80877750213e124f8af7c77c9a34bf83798eb9f370ab8fb5192`; RULES-78B
`9b097bba6040b50a3e19d220e08130726d3f70392610b490a2a1ff279bfb6a45`; tests
`bf2265245fcc98ee5ea4c7baf115fd1371b3d434f6a76ea5cd1d2db937199233`; spec
`e7c8ae4c4986448496b949f9f7337fc2b6cbb585f9d49a381cfc175de07a9a61`; basis
`fc92a568b0556f7718a1c27e488e62072df758942deef0ad7dee6d9d80cddc40`.

## 2. Per defect: what changed, why, and the evidence

Method (M). The new tests were written first and run against the round-1 source ("before": `suite-before.txt`,
14:56 UTC: **9 failed, 16 passed**); then the source was fixed and the suite re-run ("after": `suite-after2.txt`,
15:03 UTC: **25 passed**; a first after-run found two faults in my own new tests, §3 row 7, fixed before the source
was touched again). Each mutant below was killed in the runner's run of 15:05-15:06 UTC (`fix-A-mutants.json`:
baseline `25 passed`, 51 killed, 0 survived, 0 invalid); the killing test is the one the runner recorded.

| Id | What changed | Why this fix (the verifier's or a better one) | Before (M) | After (M) | Mutant(s) killed, by which test |
|---|---|---|---|---|---|
| **A-V1** `s_obs_from_progress` passed silently on rows without `capped`/`rows` | `batch_count(row, key)` requires a non-negative `int` (not bool) on every `generate` row; a record with no 32-row batch at all refuses; the loop reads `row["capped"]`/`row["rows"]` directly. | The verifier's fix, both clauses. A drifted record must not read as s_obs = 1 and switch KD11 off; "no 32-row batch" means the batch size changed and the basis does not apply. 32-row batches present but none capped still give 1.0 (nothing slow seen; a refusal there would stop real work for no safety reason). | test 05c `DID NOT RAISE Refused` at the verifier's rows `[{batch 0, 1.0 s}, {batch 1, 5000.0 s}]` (`suite-before.txt`) | 05c passes; 05b (the 17 real progress files) still 1.0 | `T2-m-s-obs-missing-keys-pass` (defaults 0 / 32), `T2-m-s-obs-no-32-row-check-off`: both by `test_05c` |
| **A-V2** the `rows == 32` filter was unpinned | Test 05d: on unit 1103's rebuilt rows, both short last batches (20 and 24 rows, made capped) slowed by 2,000 s each leave s_obs = 1.0; the same 2,000 s on a capped 32-row batch gives s_obs > 8.3 and defers. | The verifier's fix (the test-5 case with a slow capped short batch). The clause is KCR:113's; dropping it was not an option without the lead. | 05d is a test gap: the clause existed, so the test passes on the old code too; the gap shows as the verifier's hand mutant `V-sobs-rows-filter-off` surviving all 20 round-1 tests (verify-A §6.2) | the same mutation is now `T2-m-s-obs-rows-filter-off` and dies | `T2-m-s-obs-rows-filter-off` by `test_05d` |
| **A-V3** `check_keys` ignored the manifest and the evaluation bank (in full, item 3) | `check_keys(family, kind, recipe_sha256, engine_sha256, gpu_name, manifest_sha256, bank)`: the kind must be known; the recipe is the family's allow-list (main, G) for every kind except `S78_KINDS`, which need `recipe_s_or_refuse(family)`; the manifest must equal `MANIFESTS[family]`; `bank` must equal `BANK` exactly (`cap_tokens 2048, greedy_prompts 468, harm_samples 600, generation_batch 32`; ints; no missing or extra key). Test 7 holds `BANK` equal to the basis file's own top-level fields (`cap_tokens`, `greedy_prompts`, `harm_samples`, `generation_batch`) and `batches_per_evaluation` = `BATCHES` = 34 (M: the basis records them). | The verifier's fix plus the kind: the brief asks that every kind needing S_78 refuse through the one function, and the pod's key check is the natural second place (the runner's gate is the first). `kind` is required so an arm can never pass under S_78 (P78:99) and a retrain can never pass under the main config (ruling 10). | test 7: `AttributeError: no attribute 'BANK'`; the old 4-argument call | 25 passed; the other family's manifest, a 63-char manifest, cap 1,024, batch 16, 500 prompts, 200 samples, a missing or extra key, a float or string value all refuse | `T2-m-keys-manifest-any`, `T2-m-keys-bank-any`, `T2-m-keys-bank-keys-any`: all by `test_07_keys` (and `T2-m-keys-engine-any`, `T2-m-recipe-allow-other-lr` still die) |
| **A-V4** `launch_allowed(NaN, cap)` raised `decimal.InvalidOperation` | `finite()` on the balance, the cap and the price before the decimal arithmetic. | The verifier's fix. Raising `Refused` (not returning False) keeps the rule's own refusal type for a bad field, as every other gate does; `price_allowed` and `free_space_ok` return False because they are yes/no checks the plan calls on readings. | test 10b: `rules_78b.py:496: decimal.InvalidOperation` | 10b passes for NaN, ±inf, None, a string, a bool, a list, a dict, in each of the three positions | `T2-m-launch-no-finite` by `test_10b` |
| **A-V5** a no-op assertion in test 3 (`… or True`) | The assertion now binds: `at_max <= upper + 0.01` with the message, plus `at_max > own` (raising the batches to the maxima never lowers the time). The 0.01 s tolerance covers 38 × the 4-dp rounding of TRAIN_STEP_MAX (the old `1e-6` would have been too tight for the unit that defines the maximum). | The verifier's first option (remove `or True`), with the tolerance stated. | On a scratch copy (never the worktree): the old form with an impossible bound (`at_max <= -1e9 or True`) **passes** (`1 passed, 24 deselected`); | the fixed form with the same impossible bound **fails** (`AssertionError: ('sp-llama31-8b-1101', 10720.554, 10812.4734)`; `1 failed`). The worktree file's hash was unchanged by the demonstration (`bf226524…`). | `T2-m-derive-allcapped-35` (35 batches in `all_capped_s`) by `test_03` |
| **A-V6** `check_path` wider than the nine names | `ALLOWED_NAMES` exact (the `create-*` wildcard dropped) and `PLACE_OF`: each name is read from its one place (`hosts/<host>/`, `retrieved/<host>/tree/`, `retrieved/<host>/tree/round1/<unit>/`); gate order name -> place -> forbidden parts; `in_place` returns False for a name without a place. Test 15: the nine names in place pass; `create-secrets.json`, `create-intent.json.bak`, `tree/cuda-preflight-1/verification.json`, `tree/verification.json`, `hosts/<host>/ledger.jsonl`, `round1/ledger.jsonl`, a unit's `PREFLIGHT-DONE.json`, relative paths, and in-place paths whose kit root, host or unit folder is a forbidden word (`units/…`, `hosts/eval/…`, `retrieved/samples/…`, `round1/samples/…`, `round1/hidden/…`) all refuse before any open (the audit hook saw none). | Both of the verifier's options at once (exact names and the parent). The forbidden-word cases were added because, with a place check, the forbidden-parts gate binds only through a folder name, and its mutant must still die. | test 15: `AttributeError: no attribute 'PLACE_OF'` (the verifier's `cuda-preflight-1/verification.json` and `create-secrets.json` passed round 1's gate, verify-A §6.6) | 25 passed; 15b (the real root): every open is one of the nine names in place; 02b byte-for-byte unchanged | `T2-m-derive-place-off`, `T2-m-derive-create-wildcard`, `T2-m-derive-name-and-place-off` (replaces `T2-m-derive-allowlist-off`, whose find text no longer exists), `T2-m-derive-forbidden-off`: all by `test_15`. Note: a name-gate-only mutant is equivalent now (the place gate refuses the same paths), so it is not in the spec; the combined mutant is. |
| **Addendum A1** RECIPE_S pins (item 2) | `RECIPE_S = {"olmo2-7b": None, "llama31-8b": None}`; `S78_KINDS = {"retrain", "rep_pass"}`; `recipe_s_or_refuse(family) -> str` raises `Refused` while the pin is None or not a 64-hex `config_sha256`. `job_decision` calls it for a job whose kind is in `S78_KINDS`; `check_keys` requires the recipe to equal it for those kinds. Planning (`job_record`, `e_pod`, `cap_hours`, `block0_report`) never refuses on it, so `init-block 0` can print the retrain and A1 pods' need before S_78 exists (the check's M3). | The brief's design; the one addition is `kind` in `check_keys` so the refusal has two gates (the launch and the job). | test 7b: `AttributeError: no attribute 'RECIPE_S'` | 7b: both pins None refuse (`recipe_s_or_refuse`, `job_decision` for retrain and rep_pass, `check_keys` for those kinds under main or G); a test-local pin `"ab"*32` via `monkeypatch.setitem` is accepted by all three for that family only, arms still refuse under it, bad pins (empty, upper-case, 63/65 chars, an int, a path) refuse; no config file written (the kit folder's only `.json` stays the basis) | `T2-m-recipe-s-none-passes` (None -> an all-zero hash), `T2-m-s78-kinds-empty`, `T2-m-keys-s78-any-recipe`: all by `test_07b` |
| **T4 interface** (item 4) `job_decision` and the verification document | `preflight_fields(preflight_done, verification)`: `training_s`, `ms_per_step_full` from PREFLIGHT-DONE.json; `untuned_projected_s` from `verification["cap_projection"]` only (no fallback to a PREFLIGHT-DONE field of that name); a missing document, block or field refuses; `cap_projection.training_s` must equal PREFLIGHT-DONE's `training_s` (one preflight). `job_decision(family, preflight_done, verification, job, remaining_s, free_gb, s_obs=1.0)` and `pod_dry_run(family, preflight_done, verification, jobs, …)`: the document is positional and required (the old five-argument call raises `TypeError`). | Explicit as the brief asks. The one-preflight check is mine: both documents carry `training_s`, and on all 17 measured units the two are equal (M below), so it costs nothing on a real pod and refuses a mismatched pair. | test 12: `TypeError: pod_dry_run() got multiple values for argument 'remaining_s'`; test 12b: `Refused` raised where a run was expected (the old code read `untuned_projected_s` from the fake PREFLIGHT-DONE) | 12 and 12b pass. M on the real root (15:07 UTC, `PY2 -I -B`): 17 of 17 units have equal `training_s` and `ms_per_step_full` in both documents; 0 of 17 `PREFLIGHT-DONE.json` hold `untuned_projected_s`; `job_decision` on each unit's real pair returns `run` at s_pod 1.0 | `T2-m-preflight-untuned-fallback`, `T2-m-verification-optional`, `T2-m-preflight-one-preflight-off`: all by `test_12b` |
| **Rename** (item 5) | `README.md` -> `RULES-78B.md` (plain `mv`); references updated in `derive_78b_basis.py:28` and the test docstring; the file says why it is not `README.md` (T4's copy brings the stage-1 kit's README). New sections: "The public functions the T4 kit calls (exact signatures and refusals)" (before the pod; on the pod before each job; after each arm), "The constants convention (the lead's addendum A5)". | — | `grep -rn README runkit/stage1-78b/` printed two references | the only `README` left is the sentence that explains the name | — |

The `rules_78b.py golden` / `block0` / `e-caps` commands run (exit 0 each; `cmd-*.txt`): caps 4.25 / 6.5 / 8.5 / 10.5 h and
4.5 / 7.25 / 9.75 / 12.5 h; requirements 12,244.15 / 12,365.42 s and 12,498.05 / 12,612.47 s; block 0 guard $44.85,
spend $33.30, need $56.06; the retrain pods 4.5 h / $14.33 / $6.80 / $17.91 (unchanged from round 1; the money is
planned before S_78 exists).

## 3. Commands run, with exit status (all foreground, each under 15 s)

PY1 = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python` (pytest 8.4.2); PY2 =
`/Users/spiderishi/Coding/attribution/.venv/bin/python`; WS = the worktree; S = `…/scratchpad/b78/reports`.

| # | Command (abridged) | Exit |
|---|---|---|
| 1 | `date -u` (14:47:00, 14:56:11, 15:02:20, 15:03:10, 15:05:58, 15:06:09, 15:06:48, 15:07:32 UTC) | 0 |
| 2 | `git -C WS status --porcelain` (x4) -> `?? runkit/stage1-78b/` only; `git rev-parse HEAD` -> fb51421; `--ignored -- runkit experiments scripts` -> nothing else | 0 |
| 3 | `shasum -a 256`, `wc -l`, `ls`, `grep -rn README` over the kit, before and after | 0 |
| 4 | `PY2 -I -B` reads: the basis file's top-level fields, families block and one unit's key tree (numbers, hashes, key names); the two main configs' `generation` blocks; the key trees of `PREFLIGHT-DONE.json` and `hosts/<host>/verification.json` of `family-probe-sp-olmo2-7b-b-seed1103` and `…-llama31-8b-g-seed1101` (the first attempt used a wrong kit folder name: `FileNotFoundError`, exit 1, redone) | 1, then 0 |
| 5 | `grep -n RECIPE_S … runkit/stage1-olmo/stage1_rules.py` (the stage-1 pins, read only) | 0 |
| 6 | **before:** `PYTHONDONTWRITEBYTECODE=1 PY1 -B -m pytest -p no:cacheprovider -q -rfE --tb=line --basetemp S/fix-A-scratch/pt-before WS/runkit/stage1-78b/tests/test_rules_78b.py` (new tests, old source) -> 9 failed, 16 passed (`suite-before.txt`) | 1 |
| 7 | **after 1:** the same, fixed source -> 2 failed, 23 passed: my test 05d matched the second short batch by an elapsed time the first shift had moved (`StopIteration`); my test 07b fed the OLMo preflight to the Llama family (s_pod 2.579, refused). Both are test faults, fixed in the test file only (`suite-after1.txt`) | 1 |
| 8 | **after 2:** the same -> **25 passed in 0.21 s** (02b, 05b, 15b ran on the real root, no skips) (`suite-after2.txt`); final re-run at 15:06 -> 25 passed in 0.16 s | 0 |
| 9 | `PY1 -B WS/runkit/stage1-78b/tests/run_mutants_78b.py WS S/fix-A-scratch/mut1 S/fix-A-mutants.json ALL` -> baseline exit 0 (`25 passed`), **51 killed, 0 survived, 0 invalid**, 11 s wall (`runner-run1.txt`, `fix-A-mutants.json`) | 0 |
| 10 | The A-V5 demonstration on a scratch copy of the kit (symlinked repo under `S/fix-A-scratch/av5`; two `PY1 -` heredoc edits of the copy; `pytest -k test_03` twice): old form passes, fixed form fails (§2) | 0 / 1 as expected |
| 11 | `PY2 -I -B WS/runkit/stage1-78b/rules_78b.py golden` / `block0` / `e-caps` -> `cmd-*.txt` | 0, 0, 0 |
| 12 | `PY2 -I -B` over the 17 kits (allow-listed names only): the two-document consistency and `job_decision` on the real pairs (§2, T4 interface) | 0 |
| 13 | `find WS/runkit WS/experiments -name __pycache__ -o -name .pytest_cache` -> nothing | 0 |
| 14 | `mv WS/runkit/stage1-78b/README.md WS/runkit/stage1-78b/RULES-78B.md`; `rm -rf` of the scratch repos and pytest basetemps under `S/fix-A-scratch/` (28 KB of text evidence kept) | 0 |

Not run: the engine suite (`experiments/safety_selection/tests`, `--ignore` the fixture test). No file under
`experiments/` or `scripts/` differs from HEAD in the worktree (row 2), and test 14 checks the engine identity
`472fc7f6…` through the engine's own `code_identity()`; the command is in §5 for the lead's merge-time check.

## 4. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| All tests pass | **passed** | §3 row 8: 25 passed (the 20 of round 1, tests 3, 7, 12 changed; 5 new), no skips on this Mac |
| All mutants killed, zero invalid | **passed** | §3 row 9: 51 / 51 killed by real failures (exit 1, FAILED lines, 0 ERROR lines), baseline 25 passed; the killing tests per new mutant in §2 |
| Mutants added for every fix: A-V1, A-V2, A-V3, A-V4, the RECIPE_S refusal, the job_decision missing-field refusal | **passed** | A-V1: 2; A-V2: 1; A-V3: 3; A-V4: 1; RECIPE_S: 3; missing field / the two documents: 3; also A-V5: 1 and A-V6: 3 (one replacing the old allow-list mutant) = 16 new, 51 in all; test 13 requires their ids |
| Each fix has a test that fails before and passes after (both runs shown, M) | **passed** for A-V1, A-V3, A-V4, A1, the T4 interface (`suite-before.txt` / `suite-after2.txt`); for A-V2 the "before" is the surviving mutation (verify-A's own hand mutant), now killed; for A-V5 the before/after is the scratch-copy demonstration (§2); the rename has no test | §2 |
| `git status --porcelain` in ws-a lists only `runkit/stage1-78b/` | **passed** | §3 row 2 |
| BASIS_SHA256 unchanged | **passed** | `fc92a568…` in `rules_78b.py:152` and the file's bytes (§1); no fix needed the basis; 02b re-derives it byte for byte |
| Addendum A1: RECIPE_S None per family; one refusal function; every kind that needs S_78 refuses through it; both states tested without writing a config | **passed** | test 7b (§2) |
| A-V3 in full: manifest and the evaluation bank fields the basis records | **passed** | test 7 (§2); `BANK` equals the basis's own top-level fields |
| The T4 interface: job_decision takes the verification document; explicit signature; refuses on a missing field; tested | **passed** | tests 12, 12b; the 17 real pairs (§2) |
| README renamed to RULES-78B.md; every reference updated; the public functions, signatures, refusals and the A5 convention added | **passed** | §1; `grep` (§3 row 3) |
| The constants, caps, guards, spends unchanged | **passed** | §3 row 11; test 1 |
| Engine suite | **not tested** (reason in §3) | — |

## 5. Jobs for the lead

1. **Merge by explicit paths** (seven files; `README.md` no longer exists in the folder):
   `runkit/stage1-78b/{rules_78b.py,measured-basis-78b.json,derive_78b_basis.py,RULES-78B.md}` and
   `runkit/stage1-78b/tests/{test_rules_78b.py,mutation_spec_rules_78b.json,run_mutants_78b.py}`.
2. **Guard commands after the merge** (git state, not tests): `git status --porcelain -- experiments scripts runkit/stage1-olmo`
   (must print nothing) and `git diff --quiet HEAD -- runkit/stage1-olmo`.
3. **The suite in the main checkout** (about 1 s): `cd /Users/spiderishi/Coding/attribution && PYTHONDONTWRITEBYTECODE=1 PY1 -B -m pytest -p no:cacheprovider -q -rfE runkit/stage1-78b/tests/test_rules_78b.py` (expected 25 passed).
4. **The mutation run** (about 15 s; a new scratch folder outside the checkout): `PY1 -B /Users/spiderishi/Coding/attribution/runkit/stage1-78b/tests/run_mutants_78b.py /Users/spiderishi/Coding/attribution /Users/spiderishi/Coding/attribution/tmp/mut-78b-<date> /Users/spiderishi/Coding/attribution/tmp/mut-78b-<date>.json ALL` (expected: baseline exit 0, 51 killed, 0 invalid).
5. **Optional, at merge time:** the engine suite, `cd /Users/spiderishi/Coding/attribution && PYTHONDONTWRITEBYTECODE=1 PY1 -B -m pytest -p no:cacheprovider -q experiments/safety_selection/tests --ignore=experiments/safety_selection/tests/test_ss_gateb_runkit.py`.
6. **A12 / KD1's fallback:** this fix round's re-check passes (all tests, all mutants); the fallback does not fire if T2 merges before 12 Nov (the lead records the merge commit in FOCUS).
7. **When S_78 exists (A1, after each family's anchor job):** fill `RECIPE_S[family]` with the committed config's `config_sha256` by a recorded step; re-run the suite (test 7b reads the pin: with a filled pin the null-refusal assertions for that family will need the lead's one-line update to the test, or the family list in the test's first assertion; the test as written asserts both pins are None).
8. **Decide the first engine-Y pod's key check** (§6 item 1) before T4's `retrain` kind is built.
9. **T4:** call `check_keys(family, kind, recipe_sha256, engine_sha256, gpu_name, manifest_sha256, bank)` before the pod
   with `bank` built from the recipe (`generation.max_new_tokens`, `generation.batch_size`) and the packed bank (468
   greedy prompts, 600 sampled harm answers); call `job_decision(family, PREFLIGHT_DONE, VERIFICATION, job, remaining_s,
   free_gb, s_obs)` before each job, where VERIFICATION is the preflight's `verification.json` document (the same
   `cap_projection` block the 17 measured `hosts/<host>/verification.json` files hold); `s_obs_from_progress` after each
   arm. RULES-78B.md "The public functions the T4 kit calls" lists every signature and refusal.

## 6. Unresolved concerns

1. **The first engine-Y pod cannot pass `check_keys` as the rule stands.** `ENGINES = {"X": …}` and "Y joins after
   KD9's re-measure on the first Y pod" (round 1's design, kept). But ruling 10 / A2 runs the a0-1101 retrain on
   engine Y on its own pod, and that pod is KD9's first Y pod: `check_keys(…, engine_sha256=Y, …)` refuses it before
   KD9 can measure it (I). Not in the defect list, so not changed. Two ways out for the lead: (a) an `ENGINE_Y` pin
   like `RECIPE_S` (None until the Y pack's identity is read; E kinds accepted on Y once pinned; measured kinds on Y
   only after KD9 adds Y to `ENGINES`), a small follow-up in the same pattern; or (b) a recorded step that the retrain
   pod's launch skips the engine clause. I favour (a).
2. **`check_keys` now needs the bank from T4.** The values are the recipe's `generation.max_new_tokens` and
   `generation.batch_size` (R: both main configs; 2048 and 32) and the packed bank's sizes (468 greedy prompts; 600 =
   200 prompts x 3 sampled answers, `generation.harm_samples.count = 3`). If T4 passes the sampled *prompt* count (200)
   the check refuses; RULES-78B.md says which count it is.
3. **The one-preflight check in `preflight_fields`** is my addition: `cap_projection.training_s` must equal
   PREFLIGHT-DONE's `training_s` (`isclose`, rel 1e-9, abs 1e-6). On the 17 measured units the two are equal (M, §2);
   if a future preflight script version writes them differently, the refusal fires on a real pod. The lead can drop
   it by one line if the preflight script changes; the test 12b assertions that read it are marked.
4. **`ref_train_bqi` and the other E kinds under `check_keys`.** The E kinds other than `S78_KINDS` are checked
   against `RECIPE_ALLOW` (main, G). B+Qi's config is engine Y's and is not pinned here, so `ref_train_bqi` refuses the
   key check until a recipe is pinned (consistent with KCR:128, "B+Qi refused until measured"), and `anchor`,
   `untuned_answers`, `o_only`, `l1_scan`, `classifier`, `c0` are assumed to run under the family's main config (I).
5. **Test 7b asserts both pins are None.** It is the right test now; when the lead fills a pin (job 7) that one
   assertion and the per-family loop need the lead's update (or the pin is tested through a second test-local value).
6. **The verifier's observations stand** (verify-A §8: the ±1 ms rounding-order noise, the 300 s cap slack, the
   generate -> sample stage gap, the unused `STAGE1_1B_ESTIMATES_S["untuned_answers"]`); none was in the fix list and
   none was changed.
7. **The engine suite was not run** (§3). The round's rule allows it; nothing here touches `experiments/`.
