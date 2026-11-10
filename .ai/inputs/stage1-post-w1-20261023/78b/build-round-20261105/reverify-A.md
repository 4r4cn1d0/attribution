# Track A re-verification (fix round) — adversarial re-verifier

Status: DONE. Verdict **VERIFIED_WITH_MINOR** (no blocker, no major; six minor items: two false sentences in
RULES-78B.md and five test gaps where the code is right but untested; one consequential open decision for the lead,
the engine-Y key check, which the fixer also raised).

Report finished 2026-11-05 15:23 UTC (`date -u` read at 15:22:21 UTC right before; the skeleton was written at 15:11
UTC after a `date -u` at 15:11:41). Re-verifier: the Fable adversarial re-verifier of track A.

Worktree under review (read-only for me; detached at fb51421):
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-a`

My scratch: `…/scratchpad/b78/reports/reverify-A-scratch/` (100 KB after cleanup: `suite-run.txt`,
`mutants-spec-rerun.json`, `hand_mutants_rv.py`, `hand-mutants-run.txt`, `mut-hand/hand-mutants-rv.json`,
`real_units_check.py`, `real-units-check.txt`, `golden.json`, `block0.json`, `e-caps.json`; the scratch repos and
pytest basetemps were deleted).

I edited none of the fixer's files: the seven kit files' SHA-256 are identical before and after my runs (M, §8 rows
2 and 17; `bd785d45…` rules, `594f95cf…` derive, `9b097bba…` RULES-78B.md, `fc92a568…` basis, `bf226524…` tests,
`e7c8ae4c…` spec, `0d742104…` runner; `git status --porcelain` in ws-a prints `?? runkit/stage1-78b/` only). No git
state changed anywhere. No pod, spend, network, install, download, agent or message. The main checkout was read by
absolute path only; under its `tmp/` I opened only `PREFLIGHT-DONE.json`, `verification.json`, `finished.json` and
`JOB-DONE.json` of the 17 kits (numbers and key names printed, no text).

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference.

## 0. Verdict and what it rests on

- **The six round-1 defects A-V1..A-V6 are closed by code and by tests that fail without the fix** (§2): the fixer's
  `suite-before.txt` shows the 9 new or changed tests failing on the round-1 source; my re-run of the spec shows all 51
  mutants killed by the right tests (M); my own 43 hand mutants on the changed code kill 33 and the 10 survivors are
  equivalent mutants or test gaps, not code defects (§4).
- **Addendum A1 (RECIPE_S) and the T4 interface (job_decision with the verification document) hold** (§2 rows 7-8; six
  and seven of my own mutants each, all killed; 17 of 17 real units pass `job_decision` at s_pod 1.0 with the new
  signature, M).
- **Round-1 behaviour unchanged** (§7): caps 4.25 / 6.5 / 8.5 / 10.5 h and 4.5 / 7.25 / 9.75 / 12.5 h; block 0 guard
  $44.85, spend $33.30, need $56.06; the E-cap table's 13 rows equal RULES-78B.md (M).
- **Test 14's pins hold against the main checkout's current HEAD** (8d6b2e0e, three commits past fb51421, none touching
  `experiments/`, `scripts/` or `runkit/stage1-olmo`): `code_identity()` on the main checkout = `472fc7f6…`; the two
  stage-1 pins equal the main checkout's files; `git diff --quiet HEAD -- runkit/stage1-olmo` exits 0 (M, §6).
- **What is wrong (all minor, §9):** RULES-78B.md:226-227 says `check_keys` refuses `ref_train_bqi` until a recipe is
  pinned; the code passes it under the main config or G on engine X (M). RULES-78B.md:149-150 says `job_record` refuses
  `n_points < 1`; it does so for E kinds only (M). Five behaviours are right in the code but have no test: the
  `capped > 0` clause of s_obs (KCR:113), the full place chain for `ledger.jsonl` / `progress.jsonl`, the dry run's
  "first deferral defers the rest" rule, the `s` field of `job_decision`, and `a0_arm` counting toward KD2's 4.
- **The one consequential open item** (not a code error; the fixer's concern 1, confirmed M): with `ENGINES = {X}` the
  a0-1101 retrain of ruling 10 / A2 cannot pass `check_keys` on engine Y even after `RECIPE_S` is filled, and KD9's
  re-measure needs that very pod. The lead decides (§10 job 3).

## 1. Files I changed

Only this report and the files under `reverify-A-scratch/`. Nothing in ws-a, nothing in the main checkout.

## 2. Defect-by-defect check (A-V1..A-V6, addendum A1, the T4 interface)

Method. For each item: (a) read the code and the test; (b) check the fixer's "before" evidence (`fix-A-scratch/
suite-before.txt`, 14:56 UTC: 9 failed / 16 passed on the round-1 source, the failing tests named); (c) re-run the
fixer's spec mutants and read which test kills each (M, `mutants-spec-rerun.json`); (d) write my own hand mutants that
are NOT in the spec and run the suite on a scratch copy (M, `mut-hand/hand-mutants-rv.json`). "Killed by" names the test.

| Id | Closed by code (R) | Test that fails without the fix (M) | My hand mutants (M; killed by) | Verdict |
|---|---|---|---|---|
| **A-V1** s_obs passed silently on rows without `capped`/`rows` | `rules_78b.py:465-469`: `batch_count(row, "capped"/"rows")` on every generate row (non-negative int, not bool); refuses when no 32-row batch exists; `:473` reads `row["capped"]`, `row["rows"]` directly | test 05c: `suite-before.txt` FAILED (DID NOT RAISE); spec `T2-m-s-obs-missing-keys-pass`, `T2-m-s-obs-no-32-row-check-off` killed by 05c | `RV1-batch-count-float-ok`, `RV1-batch-count-neg-ok`, `RV1-s-obs-checks-rows-only`, `RV1-s-obs-checks-later-rows-only` all killed by 05c. `RV1-batch-count-bool-ok` survived: **equivalent** (`type(True) is not int` already refuses a bool; the `isinstance(value, bool)` clause is redundant, not a gap) | closed |
| **A-V2** the `rows == 32` filter unpinned | `:473` `row["capped"] > 0 and row["rows"] == GENERATION_BATCH` (unchanged clause) | test 05d (new): on unit 1103's rebuilt rows two slowed capped short batches (20, 24 rows) leave s_obs = 1.0; the same slowdown on a capped 32-row batch defers. The verifier's surviving mutant is now spec `T2-m-s-obs-rows-filter-off`, killed by 05d | `RV2-rows-filter-ge-20` killed by 05d. `RV2-uncapped-32-rows-count` (`capped >= 0`) **survived**: the `capped > 0` clause has no test (the mirror image of A-V2). Code right (M: a 4,999 s uncapped 32-row batch gives s_obs = 1.0); direction of the mutation is safe (only raises s_obs). Minor test gap, §9 D3 | closed; D3 |
| **A-V3** `check_keys` ignored the manifest and the bank | `:325-348`: 7 arguments; `check_kind`; S78_KINDS need `recipe_s_or_refuse`; others `RECIPE_ALLOW`; engine in `ENGINES`; GPU; `MANIFESTS[family]`; `bank` a dict with exactly BANK's keys, each an int equal to BANK's. Test 7 holds BANK equal to the basis file's top-level fields (M: `basis[k] == v` for the four keys; `batches_per_evaluation` 34) | test 7: `suite-before.txt` FAILED (no attribute BANK); spec `T2-m-keys-manifest-any`, `T2-m-keys-bank-any`, `T2-m-keys-bank-keys-any` killed by 07 | `RV3-bank-float-ok`, `RV3-manifest-case-insensitive`, `RV3-kind-unchecked`, `RV3-bank-subset-ok` killed by 07; `RV3-arm-passes-under-s78` killed by 07 and 07b; `RV3-s78-kind-also-needs-allowlist` killed by 07b. RULES-78B.md's key-tree claim about `verification.json` checked on the 17 real files (M): `full_length.max_new_tokens` 2048, `full_length.batch` 32, `…stages.generate.bank_units` 468, `…sample.bank_units` 600 on all 17, none missing | closed |
| **A-V4** `launch_allowed(NaN, cap)` raised `decimal.InvalidOperation` | `:569-570` `finite()` on the balance, the cap and the price | test 10b: `suite-before.txt` FAILED (`rules_78b.py:496: decimal.InvalidOperation`); spec `T2-m-launch-no-finite` killed by 10b | `RV4-launch-cap-price-unchecked` and `RV4-launch-returns-false` (returns False in place of Refused) killed by 10b | closed |
| **A-V5** the no-op assertion in test 3 | `test_rules_78b.py:190-194`: `assert at_max <= upper + 0.01` and `at_max > own - 1e-9`; no `or True` left (grep) | spec `T2-m-derive-allcapped-35` (35 batches in `all_capped_s`) killed by test 03; the fixer's scratch demonstration (old form passes an impossible bound, new form fails it) is consistent with the code I read | `RV5-allcapped-first-plus-slow` and `RV5-allcapped-outside-twice` (two other ways to inflate the unit's all-capped time) both killed by test 03: the assertion binds | closed |
| **A-V6** `check_path` wider than the nine names | `derive_78b_basis.py:55-63, 83-107`: `ALLOWED_NAMES` exact (no `create-*`), `PLACE_OF` one place per name, `in_place` checks the parent chain, gate order name -> place -> forbidden parts; test 15 asserts `ALLOWED_NAMES == frozenset(PLACE_OF)` and 9 names | test 15: `suite-before.txt` FAILED (no attribute PLACE_OF); spec `T2-m-derive-place-off`, `T2-m-derive-create-wildcard`, `T2-m-derive-name-and-place-off`, `T2-m-derive-forbidden-off` killed by 15 | `RV6-inplace-host-anywhere`, `RV6-inplace-tree-anywhere`, `RV6-forbidden-parent-only`, `RV6-forbidden-drops-units`, `RV6-open-record-skips-gate` killed by 15. `RV6-inplace-no-place-true` survived: **equivalent** (`check_path` refuses a name outside `ALLOWED_NAMES` before `in_place`, and the test holds the two sets equal, so the `return False` branch is unreachable through the gate). `RV6-inplace-unit-round1-only` **survived**: the `tree` / `retrieved` parts of the unit place are untested (code right, M: `/x/k/round1/u/ledger.jsonl` and `/x/k/other/h/tree/round1/u/progress.jsonl` refuse). Minor test gap, §9 D4 | closed; D4 |
| **Addendum A1** RECIPE_S | `rules_78b.py:135-137, 311-322`: `RECIPE_S` None per family; `S78_KINDS = {retrain, rep_pass}`; `recipe_s_or_refuse` refuses None or a non-64-hex pin; `job_decision:723-724` and `check_keys:333-335` refuse through it; planning (`job_record`, `e_pod`, `block0_report`) never refuses (M: the retrain pod prints 4.5 h / $14.33 / $6.80 / $17.91 with both pins None) | test 7b: `suite-before.txt` FAILED (no attribute RECIPE_S); spec `T2-m-recipe-s-none-passes`, `T2-m-s78-kinds-empty`, `T2-m-keys-s78-any-recipe` killed by 07b; the filled state is tested through `monkeypatch.setitem` and the kit folder's only `.json` stays the basis (test 7b's last line) | `RVA1-regex-upper-ok`, `RVA1-pin-shape-unchecked`, `RVA1-job-decision-gate-off`, `RVA1-job-decision-retrain-only`, `RVA1-s78-kinds-retrain-only`, `RVA1-recipe-s-other-family` all killed by 07b | closed |
| **T4 interface** job_decision and the verification document | `:692-754`: `preflight_fields(preflight_done, verification)`; `job_decision(family, preflight_done, verification, job, remaining_s, free_gb, s_obs=1.0)`; `pod_dry_run(…)`; no fallback for `untuned_projected_s`; the two documents must agree on `training_s` | tests 12 and 12b: `suite-before.txt` FAILED (TypeError on the old 5-argument call; Refused where a run was expected); spec `T2-m-preflight-untuned-fallback`, `T2-m-verification-optional`, `T2-m-preflight-one-preflight-off` killed by 12b. M on the 17 real pairs (my reader, `real-units-check.txt`): 0 of 17 `PREFLIGHT-DONE.json` hold `untuned_projected_s`; 17 of 17 have `cap_projection.training_s` equal to PREFLIGHT-DONE `training_s`; 17 of 17 `job_decision` -> `run` at s_pod 1.0 | `RVT4-cp-default-block`, `RVT4-isclose-2pct` killed by 12b; `RVT4-ms-fallback-to-verification`, `RVT4-training-fallback-to-cp`, `RVT4-dry-run-decrements-upper-s` killed by 12. Survivors: `RVT4-preflight-done-list-ok` and `RVT4-free-space-before-fields` **equivalent** (the same refusals, another order); `RVT4-s-obs-defer-ignores-unmeasured` **moot** (an E kind runs alone, KD6, so no earlier arm sets s_obs; the semantics are debatable, observation §11); `RVT4-dry-run-no-cascade` and `RVT4-decision-s-min` **test gaps** (code right, M: `pod_dry_run` on [38-step, 33-step] at 12,294 s left gives `defer/remaining` then `defer/earlier job deferred`; `d["s"]` = 1.1 at s_obs 1.10). Minor, §9 D5-D6 | closed; D5, D6 |
| **Rename** README -> RULES-78B.md | `grep -rn README runkit/stage1-78b/` leaves only RULES-78B.md:9-10 (the sentence that explains the name); `derive_78b_basis.py:28` and the test docstring say RULES-78B.md; `README.md` does not exist in the folder (M) | — | — | done |

## 3. Suite and mutation runner, run by me

- Suite (M, §8 row 5): **25 passed in 0.22 s** in ws-a; tests 02b, 05b, 15b ran on the real root (no skips); no
  `__pycache__` or `.pytest_cache` under `runkit/` or `experiments/` afterwards; `git status --porcelain` unchanged.
- The fixer's spec with the fixer's runner (M, §8 row 6; SCRATCH in my folder, SOURCE_ROOT = ws-a never written):
  baseline exit 0 (`25 passed`), **51 killed, 0 survived, 0 invalid**, 0 runs with an ERROR line; the spec's SHA-256
  `e7c8ae4c…` equals the one in the fixer's `fix-A-mutants.json`, whose counts (51 killed, baseline 0) my run reproduces.
  The killing test of each of the 17 new or replaced mutants is the one the fixer names in fix-A.md §2 (listed in §8).

## 4. My own hand mutants (43, none in the fixer's spec; `hand_mutants_rv.py`, `mut-hand/hand-mutants-rv.json`)

Baseline 25 passed; **33 killed, 10 survived, 0 invalid**; the worktree kit's hashes unchanged after the run (the
script checks). Per item they are listed in §2. The ten survivors:

| Survivor | Class | Why |
|---|---|---|
| `RV1-batch-count-bool-ok` | equivalent | `type(value) is not int` refuses a bool on its own |
| `RV6-inplace-no-place-true` | equivalent | unreachable through `check_path` (name gate first; `ALLOWED_NAMES == frozenset(PLACE_OF)` asserted) |
| `RVT4-preflight-done-list-ok` | equivalent | a non-dict document still refuses on its missing fields |
| `RVT4-free-space-before-fields` | equivalent | the same refusals in another order |
| `RVT4-s-obs-defer-ignores-unmeasured` | moot | an E kind runs alone (KD6); no earlier arm sets s_obs on its pod |
| `RV2-uncapped-32-rows-count` | test gap (D3) | the `capped > 0` clause of KCR:113 has no test; code right (M) |
| `RV6-inplace-unit-round1-only` | test gap (D4) | the `tree` / `retrieved` parts of the unit place have no test; code right (M) |
| `RVT4-dry-run-no-cascade` | test gap (D5) | "the first deferral defers every later job" has no test (test 12's cases are monotone); code right (M) |
| `RVT4-decision-s-min` | test gap (D6) | the returned `s` field (RULES-78B.md lists it) has no test; code right (M) |
| `RVR-counted-kinds-drop-a0` | test gap (D7), round-1 code | `a0_arm` counting toward KD2's 4 has no test (test 9 refuses 5 `arm`s only); code right (M: 4 arms + a0_arm and 4 arms + evalonly both refuse) |

## 5. RULES-78B.md "The public functions the T4 kit calls" vs the code

Signatures (M, `inspect.signature` on the 29 functions the section names, §8 row 9): **all 29 equal the text**, including
`check_keys(family, kind, recipe_sha256, engine_sha256, gpu_name, manifest_sha256, bank) -> None`,
`job_decision(family, preflight_done, verification, job, remaining_s, free_gb, s_obs=1.0)`, `pod_dry_run(…)`,
`preflight_fields(preflight_done, verification)`, `recipe_s_or_refuse(family) -> str`, `launch_allowed(…, price=1.85)`.
`job_decision`'s return keys equal the listed seven. Refusal claims, probed one by one (M):

- Right: `check_keys` (unknown family, unknown kind, S78 kinds under a null pin or another recipe, other kinds off the
  allow-list, engine, GPU, manifest, bank shape and values, a bool bank value refuses); `recipe_s_or_refuse`;
  `price_allowed` / `free_space_ok` never raise (a bool reads as not ok); `launch_allowed` raises Refused on a bad field;
  `cap_hours`'s four refusals; `preflight_fields`'s five; `speed_factor`; `job_decision` (KD5, A1, None remaining defers);
  `s_obs_from_progress`'s refusals and the "none capped -> 1.0" case; `s_obs_defers`.
- **False (D1):** RULES-78B.md:226-227 "`ref_train_bqi` has no pinned recipe here …; `check_keys` refuses it until one is
  pinned and measured (KCR:128)". M: `check_keys("olmo2-7b", "ref_train_bqi", <main config_sha256>, ENGINE_X, GPU, manifest,
  BANK)` **passes**. The code follows RULES-78B.md:130-132 ("for any other kind a recipe not on `RECIPE_ALLOW[family]`"),
  so the two sentences contradict each other; fix-A.md concern 4 repeats the false one.
- **False (D2):** RULES-78B.md:149-150 `job_record` "Refuses … `n_points < 1`". M: `job_record("olmo2-7b", "arm", 33,
  n_points=0)` returns a record; only E kinds refuse (through `e_upper_s`).
- The E-cap table (13 rows, both families' cap and guard) equals `rules_78b.py e-caps` (M); the A1 pod's
  $36.53 / $28.64 / $45.66 and the other scorer pods' $10.16-14.79 guards equal `block0` (M).

## 6. Test 14's pins vs the main checkout's current HEAD

- Main checkout HEAD **8d6b2e0e** (ws-a is detached at fb51421). `git log fb51421..HEAD`: three commits (ead1d7e, abf5aa1,
  8d6b2e0: FOCUS and the addendum records); `git diff --stat fb51421 HEAD -- experiments/safety_selection runkit/stage1-olmo
  experiments/minimal_safety scripts` prints nothing (M).
- Engine identity on the main checkout: `code_identity()["sha256"]` = **`472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892`**
  = `ENGINE_X` (M, §8 row 4; run from the main checkout with `-B`, no bytecode written).
- `runkit/stage1-olmo/stage1_rules.py` `d52614e4…` and `budget.py` `f4760c08…` in the main checkout equal `STAGE1_PINS`
  (M). `git -C /Users/spiderishi/Coding/attribution diff --quiet HEAD -- runkit/stage1-olmo` exits 0; `git status
  --porcelain -- runkit experiments scripts` there prints nothing (M).
- Test 14 in the worktree checks the worktree's own engine files (fb51421); the values above show the same pins hold at
  the current main HEAD, so the merge target is as test 14 assumes.

## 7. Round-1 regressions (golden caps, block 0)

`rules_78b.py golden` / `block0` / `e-caps` (M, `-I -B`, exit 0 each): caps OLMo 4.25 / 6.5 / 8.5 / 10.5 h, Llama 4.5 /
7.25 / 9.75 / 12.5 h; requirements 12,244.15 / 12,365.42 s and 12,498.05 / 12,612.47 s (addendum A5's convention);
guards $13.86 / 18.03 / 21.73 / 25.43 and $14.33 / 19.41 / 24.04 / 29.13; spend uppers $5.12 / 8.81 / 12.50 / 16.18 and
$6.27 / 11.11 / 15.95 / 20.80; block 0 pods (8.5 h, $12.50) and (12.5 h, $20.80), guard $44.85, spend upper $33.30, base
need $44.85, **need $56.06**; retrain pods 4.5 h / $14.33 / $6.80 / $17.91 both families. Test 1 pins all of these and
passed. My sanity mutants `RVR-e-cap-retrain-2h` and `RVR-block0-llama-3-arms` were killed (tests 07b/08 and 01).

## 8. Commands run, with exit status (all foreground, all under 60 s)

PY1 = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python`; PY2 =
`/Users/spiderishi/Coding/attribution/.venv/bin/python`; WS = ws-a; S = my scratch folder; MAIN = the main checkout.

| # | Command (abridged) | Exit |
|---|---|---|
| 1 | `date -u` (15:11:41, 15:13:59, 15:18:31, 15:22:07, 15:22:21 UTC) | 0 |
| 2 | `git -C WS status --porcelain` (x3) -> `?? runkit/stage1-78b/`; `git -C WS rev-parse HEAD` -> fb51421; `shasum -a 256` of the seven kit files before and after every run (identical); `ls WS/runkit/stage1-78b/README.md` -> no such file | 0 (ls 1, expected) |
| 3 | `git -C MAIN rev-parse HEAD` -> 8d6b2e0e; `git -C MAIN status --porcelain -- runkit experiments scripts` -> nothing; `shasum` of the two stage-1 files; `git -C MAIN diff --quiet HEAD -- runkit/stage1-olmo`; `git -C MAIN log --oneline fb51421..HEAD`; `git -C MAIN diff --stat fb51421 HEAD -- experiments/… runkit/stage1-olmo scripts` -> nothing | 0 |
| 4 | `cd MAIN && PYTHONDONTWRITEBYTECODE=1 PY1 -B -c "from experiments.safety_selection.common import code_identity; …"` -> `472fc7f6…` | 0 |
| 5 | `cd WS && PYTHONDONTWRITEBYTECODE=1 PY1 -B -m pytest -p no:cacheprovider -q -rfE --basetemp S/pt-suite runkit/stage1-78b/tests/test_rules_78b.py` -> **25 passed in 0.22 s** (`S/suite-run.txt`); `find runkit experiments -name __pycache__ -o -name .pytest_cache` -> nothing | 0 |
| 6 | `PY1 -B WS/runkit/stage1-78b/tests/run_mutants_78b.py WS S/mut-spec S/mutants-spec-rerun.json ALL` -> baseline exit 0, **51 killed, 0 survived, 0 invalid** | 0 |
| 7 | `PY2 -I -B WS/runkit/stage1-78b/rules_78b.py golden` / `block0` / `e-caps` -> `S/golden.json`, `S/block0.json`, `S/e-caps.json`; `PY2 -I -B -c` comparisons with KCR §7 / RULES-78B.md (§7, §5) | 0 |
| 8 | `PYTHONDONTWRITEBYTECODE=1 PY1 -B S/hand_mutants_rv.py S/mut-hand` -> baseline 25 passed; **33 killed, 10 survived, 0 invalid**; worktree kit unchanged (`S/hand-mutants-run.txt`, `S/mut-hand/hand-mutants-rv.json`) | 0 |
| 9 | `PYTHONDONTWRITEBYTECODE=1 PY2 -I -B S/real_units_check.py WS/runkit/stage1-78b` -> 17 units; 0 PREFLIGHT-DONE with `untuned_projected_s`; 17 equal `training_s`; 17 `run` at s_pod 1.0; the four verification key paths present on all 17 with values 2048 / 32 / 468 / 600 (`S/real-units-check.txt`) | 0 |
| 10 | `PY2 -I -B -c` signature listing (29 functions) and refusal probes (§5); the survivor probes (§4: KD2 with a0_arm / evalonly, the cascade, the `s` field, an uncapped slow batch, four unit-place paths) | 0 |
| 11 | `grep -rn README WS/runkit/stage1-78b/`; `grep -n "RULES-78B"` in derive and the test docstring; `sed -n` over KCR:111-114, :118-132, :145-148, the plan's T2 section and the check's item 2; `ls`, `tail` over `fix-A-scratch/` | 0 (grep 1 = nothing beyond the explaining sentence) |
| 12 | `PY2 -I -B -c` reading `fix-A-mutants.json` and my `mutants-spec-rerun.json` (counts, baseline, spec hash, killing tests per new mutant) | 0 |
| 13 | `rm -rf` of my scratch repos and pytest basetemps only (`S/pt-suite`, `S/mut-spec/repo`, `S/mut-hand/repo`, `pt-*`); a first attempt stopped on a zsh no-match glob and was redone with explicit paths; `du -sh S` -> 100 KB | 0 |

Not run: the engine suite (`experiments/safety_selection/tests`, `--ignore` the fixture test). Nothing under
`experiments/` or `scripts/` differs from HEAD in the worktree or in the main checkout (rows 2-3), and the engine
identity was checked directly (row 4). Its command stands in fix-A.md §5 for the lead's merge-time check.

## 9. Acceptance criteria and defects

### Acceptance (the fixer's list, re-checked)

| Criterion | My result | Evidence |
|---|---|---|
| All tests pass | **passed** | row 5: 25 passed, no skips |
| All mutants killed, zero invalid, baseline with the same command | **passed** | row 6: 51 / 51, baseline exit 0, 0 ERROR lines |
| Mutants added for A-V1..A-V4, the RECIPE_S refusal, the missing-field refusal | **passed** | spec: 2 + 1 + 3 + 1 + 3 + 3 (+ A-V5 1, A-V6 4 incl. the replacement); test 13 requires their ids; each killed by the test fix-A.md names (row 12) |
| Each fix has a test that fails on the old code and passes on the new | **passed** | `suite-before.txt` (9 FAILED, named) vs row 5; A-V2's "before" is the round-1 survivor now in the spec; A-V5's is the binding assertion, which my two extra mutants prove can fail |
| `git status --porcelain` in ws-a lists only `runkit/stage1-78b/` | **passed** | row 2 |
| BASIS_SHA256 unchanged | **passed** | `fc92a568…` in `rules_78b.py:152` and the file (row 2); test 02b re-derives it (row 5) |
| Addendum A1: RECIPE_S None per family, one refusal function, every S_78 kind refuses through it, both states tested without a config | **passed** | §2 row 7; six hand mutants killed |
| A-V3 in full: manifest and the evaluation bank the basis records | **passed** | §2 row 3; the bank equals the basis file's fields and the 17 real `verification.json` values (row 9) |
| T4 interface: explicit signature, the verification document, refusal on a missing field, tested | **passed** | §2 row 8; 17 real pairs (row 9) |
| README renamed, references updated, public functions and A5 convention added | **passed with two false sentences (D1, D2)** | §5 |
| Constants, caps, guards, spends unchanged | **passed** | §7 |
| Engine suite | **not tested** (reason in §8) | — |

### Defects (all minor; none changes a cap, a guard, a spend, a key gate or the derivation's privacy)

| Id | Severity | Where | What | Fix |
|---|---|---|---|---|
| **D1** | minor | `RULES-78B.md:226-227`; `fix-A.md` §6 item 4 | "`check_keys` refuses `ref_train_bqi` until one is pinned" is false: it passes under the main config or G on engine X (M). It contradicts RULES-78B.md:130-132, which the code follows. On engine Y it refuses through the engine clause, so B+Qi (ruling 10: on Y) is in practice blocked by `ENGINES`, not by a recipe pin | Either (a) the doc: "`ref_train_bqi` passes the recipe clause under main/G; its own config is not pinned; it is blocked on Y by `ENGINES` until KD9", or (b) the code, in A1's pattern: `RECIPE_BQI = None` per family and `ref_train_bqi` in a "needs its own pin" set, with a 7b-style test. (b) matches KCR:128 "B+Qi refused until measured" |
| **D2** | minor | `RULES-78B.md:149-150` | `job_record` "Refuses … `n_points < 1`" holds for E kinds only; `job_record("olmo2-7b", "arm", 33, n_points=0)` returns a record (M) | one sentence ("for an E kind"), or a `type(n_points) is not int or n_points < 1` check at the top of `job_record` |
| **D3** | minor (test gap) | `test_rules_78b.py` test 05 / 05d | the `capped > 0` clause of KCR:113 is unpinned: my `RV2-uncapped-32-rows-count` survived; code right (M) | one 05d case: a slow UNCAPPED 32-row batch leaves s_obs = 1.0 |
| **D4** | minor (test gap) | test 15's A-V6 list | the unit place's `tree` / `retrieved` parts are unpinned: `RV6-inplace-unit-round1-only` survived; code right (M) | add `root / "k/round1/u/ledger.jsonl"` and `root / "k/other/h/tree/round1/u/progress.jsonl"` to the bad list |
| **D5** | minor (test gap, round-1 rule) | test 12 | "the first deferral defers every later job" is unpinned: `RVT4-dry-run-no-cascade` survived (test 12's job lists are monotone); code right (M: [38, 33] at 12,294 s left -> defer, defer/"earlier job deferred") | one `pod_dry_run` case with a 38-step arm before a 33-step arm at a remaining time between their requirements |
| **D6** | minor (test gap) | test 12 | `job_decision`'s returned `s` field is unpinned: `RVT4-decision-s-min` survived; code right (M: s = 1.1 at s_obs 1.10) | assert `d["s"] == max(1, s_pod, s_obs)` in test 12 |
| **D7** | minor (test gap, round-1 code) | test 9 | `a0_arm` (and `evalonly`) counting toward KD2's 4 is unpinned: `RVR-counted-kinds-drop-a0` survived (test 9 refuses five `arm`s only); code right (M: 4 arms + a0_arm and 4 arms + evalonly refuse) | two `pytest.raises(Refused)` lines in test 9 (the verifier probed this by hand in round 1 but no test holds it) |

## 10. Jobs for the lead

1. **Merge decision.** The seven files are fit to merge as they stand (the fixer's explicit paths; `README.md` no longer
   exists in the folder). D1-D7 are one-line to ten-line follow-ups; D1 needs the lead's choice (doc or pin).
2. **At merge:** the fixer's guard commands, suite and mutation run (fix-A.md §5 items 2-4); expected 25 passed and
   51 killed / 0 invalid. Optionally the engine suite (fix-A.md §5 item 5).
3. **Decide the first engine-Y pod's key check before T4 builds the `retrain` kind.** M: with `RECIPE_S["olmo2-7b"]`
   filled (test-local) `check_keys("olmo2-7b", "retrain", <S_78>, <Y identity>, …)` refuses with "engine … has no
   measured basis". Ruling 10 / A2 put the a0-1101 retrain on Y under S_78, and KD9 re-measures on that pod, so KD9
   and A2 are circular as the rule stands. The fixer's option (a), an `ENGINE_Y` pin in the RECIPE_S pattern (None
   until the Y pack's identity is read by a recorded step; E kinds on Y once pinned; measured kinds on Y only after KD9
   adds Y to `ENGINES`), is the smaller change and keeps every refusal explicit. I agree with (a).
4. **A12 / KD1's fallback:** this re-check passes (all tests, all spec mutants, the six defects closed; minor items
   only). The fallback does not fire if T2 merges before 12 Nov; record the merge commit in FOCUS.
5. **When RECIPE_S is filled** (after each family's anchor job): test 7b's first assertion and its null-refusal loop need
   the lead's update for that family (the fixer's job 7).
6. **T4:** build `bank` from the recipe and the packed bank (600 = sampled answers, not 200 prompts); pass both preflight
   documents to `job_decision` / `pod_dry_run`; the 17 real `verification.json` files carry `full_length.max_new_tokens`,
   `full_length.batch` and the two `bank_units` (M), so the pod can rebuild `bank` from them after the preflight as
   RULES-78B.md:136-139 says.

## 11. Unresolved concerns and observations

1. **The engine-Y circularity** (§10 job 3) is the one consequential open item; it is a rulings-level decision, not a
   code error, and the fixer raised it first.
2. **`s_obs` on an E-kind job.** `job_decision` defers an E job at s_obs > 1.15 like an arm; my mutant that exempts E
   kinds survived because E kinds run alone (KD6), so the case never arises on a real pod. No change needed; noted so
   nobody reads the survivor as a defect.
3. **Out-of-order progress rows.** `s_obs_from_progress` ignores a negative batch difference (`max(slowest, …)` from 0):
   a reversed record would read s_obs = 1.0 (M, synthetic rows). derive checks batch order; the in-pod check does not.
   Low likelihood (engine X writes the rows in order; the 17 real files pass); a one-line `row["batch"]` order check
   would close it. Not in the fix list.
4. **`launch_allowed(44.85, -1.0)` returns True** (M): `finite()` accepts a negative cap. The plan's caps come from
   `cap_hours` (>= 0.25 h), so only a caller bug reaches it. Not in the fix list.
5. **A `job` dict without `kind`** raises KeyError in `job_decision`, not Refused (M). Job records come from
   `job_record`, which always sets it. Not in the fix list.
6. **The fixer's one-preflight check** (`cap_projection.training_s == PREFLIGHT-DONE training_s`) holds on all 17 real
   units (M, my reader). I agree it is cheap and refuses a mismatched pair; the fixer's note that a changed preflight
   script could trip it stands.
7. **Test 14 checks the worktree's engine files.** At the main checkout's current HEAD the same pins hold (§6). After
   the merge the suite runs in the main checkout, so the check is on the right files from then on.
8. The round-1 verifier's observations (verify-A §8) and the fixer's concerns 2-7 (fix-A.md §6) stand; I add nothing to
   them beyond D1-D7 and items 1-5 above.
