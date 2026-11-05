# Build report, track A = T2: the 7-8B cap rule and its measured basis

Status: DONE (report finished 2026-11-05 14:16 UTC; `date -u` read at 14:15:48 UTC right before). Worker: the Fable
builder of track A. Worktree: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-a`
(detached at fb51421; `git status --porcelain` prints only `?? runkit/stage1-78b/`). No git state changed anywhere. No
pod, spend, network, install, download, agent or message. The main checkout was read by absolute path only.

Governing texts read in full: the lead's Part 1 rulings (ruling 11, KD1-KD11; KD4's reason string), the readiness
plan's T2 and §5.11, the check (C7, C8, C11, C14, M3), KCR in full, P78 §3.2 and §9.1 EM-2, the stage-1 kit's
`stage1_rules.py` (docstring, constants, lines 874-1247: the helpers), `budget.py` (full), `plan_tool.py` (the
funding-need calls), `README.md` (Money), `tests/mutants_b15.json` (the spec form) and
`research/experiments/2026-10-24-stage1-runkit/run_mutants_b15.py` (the runner form).

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference.

## 1. Files changed (all new, all under `runkit/stage1-78b/` in the worktree; none has a stage-1 kit name)

| File | Lines | What |
|---|---|---|
| `runkit/stage1-78b/rules_78b.py` | 744 | The constants block and the rule (upper_M, requirement, s_pod, F_pre, s_obs, caps, pod_sizes, guard with the zero hold, spend, funding need, keys, kinds, the KD6 E caps, the job runner's gate `job_decision`/`pod_dry_run`, `block0_report` for M3, `golden_table`). Commands `golden`, `block0`, `e-caps`. SHA-256 `56ea39a9…`. |
| `runkit/stage1-78b/measured-basis-78b.json` | 6,438 | The text-free timing record of the 17 units. SHA-256 `fc92a568b0556f7718a1c27e488e62072df758942deef0ad7dee6d9d80cddc40`, pinned as `BASIS_SHA256`. |
| `runkit/stage1-78b/derive_78b_basis.py` | 417 | Writes the basis from the kits under `--root` (read-only). Allow-listed names only; forbidden path parts refused; no output string longer than a hash; deterministic; `--extra-unit FAMILY:FOLDER` for KD9. SHA-256 `e020931f…`. |
| `runkit/stage1-78b/tests/test_rules_78b.py` | 789 | KCR §10 tests 1-15 with the brief's adaptations, plus 02b (byte-for-byte re-derivation), 05b (s_obs on the real progress files), 15b (the derivation on the real root under an audit hook) and 16 (no bytecode). SHA-256 `f077815b…`. |
| `runkit/stage1-78b/tests/mutation_spec_rules_78b.json` | 88 | 35 mutants: KCR test 13 / KCR:226's ten, plus tests 2, 4-10, 12, 15 and KD2/KD6 mutants, in the stage-1 spec form. |
| `runkit/stage1-78b/tests/run_mutants_78b.py` | 150 | The runner (the stage-1 `run_mutants_b15.py` form: baseline first; killed only by a real failure; errors invalid). |
| `runkit/stage1-78b/README.md` | 141 | The files, the rule, the constants and both arithmetics, the rulings baked in, the E-cap table, the commands, what T4 calls, limits. |

Evidence outside the worktree (scratch, not for merge): this report; `…/scratchpad/b78/reports/mutants-all.json`
(the last mutation run); `…/scratchpad/b78/tools/keys.py` (the key-tree printer used to inspect record structures
without printing text).

## 2. Alternatives considered and why this one

1. **The constants: KCR's printed values or the exact basis maxima.** KCR §4 prints 24.26 / 314.0 / 240.9 / 20 / 109
   (OLMo) and 22.89 / 246.9 / 250.3 / 20 / 163 (Llama). The basis maxima are 24.2545 / 314.049 / 240.945 / 19.877 /
   108.638 and 22.8848 / 246.86 / 250.305 / 19.703 / 162.778 (M). With KCR's values, BATCH_MAX and FIRST_BATCH_MAX sit
   0.045-0.049 s below a measurement, and s_obs on unit 1103 and s_pod on the slowest pods come out 1.0002, not 1
   (KCR tests 4 and 5 say "s = 1 on every measured pod/unit"); KCR test 2 says each constant equals the maximum from
   the basis. I chose the exact maxima: tests 2, 4 and 5 then hold literally and no constant is below a measurement.
   The cost: the rule's requirements are 12,244.15 / 12,365.42 s (OLMo 33 / 38) and 12,498.05 / 12,612.47 s (Llama)
   against KCR's 12,243 / 12,365 / 12,499 / 12,613, at most 1.2 s apart because KCR rounded each constant before
   summing. Every cap, guard and spend upper is the same to the cent. Test 1 holds both arithmetics: KCR's printed
   constants reproduce KCR's integers exactly through the same functions (`KCR_PRINTED`, `upper_m_of`), and the live
   rule's caps/guards/spends equal KCR §7-§8. Not forced; reported here (§5).
2. **Training per step.** The slowest single ledger segment (24.886 s, the 10-step first segment holds a warm-up) or the
   whole run over its steps (24.2545 s). KCR's "training per step" is the whole run (its 24.26 is this value, rounded
   up). Chosen: the whole run; the segment maximum is kept in the basis (`train_s_per_step_segment_max`).
3. **The batch-seconds convention.** The first derivation measured a sampled series' first batch from the sample
   stage's `start_s`; the rule's in-pod check cannot read the ledger, so it uses the previous `generate` row. I made
   the derivation use the same differences (the very first batch from the generate stage's start) so `s_obs` on the
   real `progress.jsonl` files equals 1 exactly and the two measure one quantity. The maxima did not move.
4. **E caps as fixed hours or as formulas.** Chosen: formulas from the M constants where a kind's work is known
   (batches x BATCH_MAX, 38 x TRAIN_STEP_MAX) plus an E part, with the stage-1 wide-cap factor 1.5 on the E parts;
   `rep_pass` pinned by KD6's 16.5 h; `retrain` a 3 h upper (4.5 h cap, inside the check's M3 "4-5 h"). Each entry
   carries its basis string. These are judgment calls; see §7.
5. **Test 14's "runkit/stage1-olmo/ unchanged against HEAD".** A git check depends on other people's uncommitted
   files, so the test pins the SHA-256 of the two stage-1 files this kit reads (`stage1_rules.py` `d52614e4…`,
   `budget.py` `f4760c08…` at fb51421); the git check is the lead's guard command (§6).
6. **The mutation runner.** The stage-1 `run_mutants_b15.py` is hard-wired to `runkit/stage1-olmo` and its nine test
   files, so a compact copy of its form for this folder was written rather than editing it.
7. **Test 13 and masking.** The first mutation run killed four mutants only through test 13's "find text occurs once"
   check (a mutated source trivially fails it). I removed that assertion (the runner already reports such a mutant
   INVALID) and re-ran; the four then died by tests 4 and 15, and one real survivor appeared (`T2-m-req-no-floor`:
   the s_obs default of 1 masked `max(1, s)`), which a new assertion (both factors below 1) now kills.
8. **Recipe S_78.** Not added to `RECIPE_ALLOW`: its `config_sha256` does not exist yet (T6a). A one-line edit with
   its test when it does (README).

## 3. Commands run, with exit status (all foreground; the main checkout read by absolute path)

PY1 = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python` (pytest 8.4.2); PY2 =
`/Users/spiderishi/Coding/attribution/.venv/bin/python`. WS = the worktree above.

| # | Command (abridged) | Exit |
|---|---|---|
| 1 | `date -u` (13:33:57, 14:11:51, 14:12:26, 14:13:28, 14:14:15, 14:15:48 UTC) | 0 |
| 2 | `ls`, `wc -l`, `grep`, `sed -n`, `shasum -a 256` over the governing files, the stage-1 kit, the configs and both prepared manifests (read-only) | 0 |
| 3 | `PY2 -I -B …/tools/keys.py <record files>`: key trees of `finished.json`, `create-*.json`, `BOOTSTRAP-READY.json`, `JOB-DONE.json`, `PREFLIGHT-DONE.json`, `verification.json`, `ledger.jsonl`, `progress.jsonl` of unit sp-olmo2-7b-1103 (numbers, hashes, short names; long strings as `<str n>`) | 0 |
| 4 | `PY1 -B` one-off: the engine's `config_sha256` of the 14 OLMo-2-7B / Llama-3.1-8B configs and `code_identity()` (M: engine `472fc7f6…`; main configs `18cc31d7…`, `74758af1…`; G `01259f28…`, `442f133f…`) | 0 |
| 5 | `PY2 -I -B WS/runkit/stage1-78b/derive_78b_basis.py --root /Users/spiderishi/Coding/attribution/tmp --out WS/runkit/stage1-78b/measured-basis-78b.json` — first run: `RecordRefused` (the GPU name has a space; the string check was then allowed one space) | 1 |
| 6 | the same derive, three later runs (per-step definition changed; batch convention unified; a lenient recipe label): hashes `0405…` -> `bae1…` -> `fc92a568…` (final); two re-checks to a scratch path confirmed the final hash unchanged | 0 |
| 7 | `PY2 -I -B WS/runkit/stage1-78b/rules_78b.py golden` / `e-caps` / `block0` | 0 |
| 8 | `PYTHONDONTWRITEBYTECODE=1 PY1 -B -m pytest -p no:cacheprovider -q -rfE --basetemp <scratch> WS/runkit/stage1-78b/tests/test_rules_78b.py` — run 1: 6 failed / 14 passed; run 2 (same, --tb=short): 6 / 14; run 3: 2 / 18; run 4: 1 / 19 | 1 |
| 9 | the same suite, runs 5-8 (after the fixes): **20 passed** each (0.15-0.20 s; tests 02b, 05b, 15b ran against the real root, no skips) | 0 |
| 10 | `PY1 -B WS/runkit/stage1-78b/tests/run_mutants_78b.py WS <scratch> <out.json> BASELINE` (before the test-15 fix: baseline failed, stopped) | 2 |
| 11 | the runner, `ALL`, run 1: 35 killed, but 4 only by test 13 (masked) | 0 |
| 12 | the runner, `ALL`, run 2 (test 13's find-once check removed): 34 killed, 1 survived (`T2-m-req-no-floor`) | 1 |
| 13 | the runner, `ALL`, run 3 (test 4 extended): **35 killed, 0 survived, 0 invalid**, baseline `20 passed`; 7 s wall | 0 |
| 14 | `git status --porcelain` in WS (after every write): `?? runkit/stage1-78b/` only; `find runkit experiments -name __pycache__`: nothing | 0 |
| 15 | `rm -rf` of the runner's scratch copies and pytest basetemps under the scratchpad (not the worktree) | 0 |

Not run: the engine suite (`experiments/safety_selection/tests`, `--ignore` the git-ignored fixture test); this track
changes no engine file and test 14 checks the engine identity directly. The full mutation run took 7 s, so it was run
here (§3 row 13) rather than left to the lead's background shell; the command is in §6 for the lead's own run.

## 4. Evidence paths

- The basis: `WS/runkit/stage1-78b/measured-basis-78b.json` (SHA-256 `fc92a568b0556f7718a1c27e488e62072df758942deef0ad7dee6d9d80cddc40`).
- The mutation run: `…/scratchpad/b78/reports/mutants-all.json` (baseline `20 passed in 0.15s`; 35 killed; each mutant's failing test, before/mutated/restored hashes; 2026-11-05T14:14 UTC).
- The suite's commands and results: §3 rows 8-9. The golden table: `rules_78b.py golden` (§3 row 7); its values in §5.
- The measured inputs (read-only, by absolute path): `/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-{olmo2-7b,llama31-8b}-*/` as KCR:9 names them (the 17 kits in `derive_78b_basis.UNIT_KITS`).

## 5. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Tests 1-15 pass | **passed** | §3 row 9: 20 passed (tests 1-16 incl. 02b/05b/15b), `PY1 -B -m pytest … test_rules_78b.py` |
| Golden numbers: caps 4.25 / 6.5 / 8.5 / 10.5 h (OLMo) and 4.5 / 7.25 / 9.75 / 12.5 h (Llama); guards and spend uppers to the cent, half-up | **passed** | test 1; `golden`: guards $13.86 / 18.03 / 21.73 / 25.43 and $14.33 / 19.41 / 24.04 / 29.13; spend 1 arm $5.12 / $6.27, 4 arms $16.18 / $20.80 ($4.05 / $5.20 per arm); block 0 guard $44.85, spend $33.30, need $56.06 (KCR:177); Llama two 33-step arms 7.0 h (KCR §7 note) |
| Golden numbers: requirements 12,243 / 12,365 s (OLMo) and 12,499 / 12,613 s (Llama) | **passed from KCR's printed constants; the live rule differs by <= 1.2 s (reported, not forced)** | test 1: `upper_m_of(KCR_PRINTED[f], steps) + 1800` rounds to 12,243 / 12,365 / 12,499 / 12,613 exactly; the live rule (exact basis maxima) gives 12,244.15 / 12,365.42 / 12,498.05 / 12,612.47 (`golden`). Both derivations: KCR summed rounded constants; the rule sums the maxima. upper_M(38): 10,565.42 vs KCR 10,565; 10,812.47 vs 10,813. GEN_ALLCAP 8,265.23 vs 8,264; 8,510.37 vs 8,510 |
| Every measured unit is below upper_M(38) | **passed** | test 3: outer job <= upper_M(38) for all 17 (slowest 6,450 vs 10,565.4; 8,466 vs 10,812.5; the two pods with the untuned evaluation 6,876 and 10,452 also below); each unit's own all-capped time <= upper_M(38) |
| The basis hash is pinned | **passed** | `BASIS_SHA256 = fc92a568…`; test 2 (pin equal; a changed copy refuses); test 02b re-derives byte for byte from the real root |
| The copied helpers equal the stage-1 kit's | **passed** | test 9: `round_up_s`, `cents`, `funding_need_usd` (4 launch paths x 2 factors), `pod_sizes` (n = 1..40), `guard_usd`, `hours`, `gate` equal `stage1_rules` loaded by path; the money constants equal; the one deliberate difference `POD_OVERHEAD_S` 48 vs 42 min asserted |
| `git status --porcelain` lists only new files under `runkit/stage1-78b/` | **passed** | §3 row 14 |
| KCR test 2: each constant equals the maximum recomputed from the basis; SCORE_ALLCAP >= 3 x scoring max and >= the fit | **passed** | test 2: all eight constants per family equal (abs 1e-9); SCORE_ALLCAP 1,250 >= 985.5 / 1,223.0 and >= the Llama fit 1,163.2 s (KCR: about 1,160) and the OLMo mixed fit 1,157.6 s (KCR said about 1,190; §7) |
| KCR tests 4-12, 15 | **passed** | s_pod = 1 on all 17 preflights, 1.1 / 1.12 on synthetic slow pods, refusal above 1.15 and on bad fields; s_obs = 1 on all 17 real progress files and on the rebuilt rows, 2.3x defers, the first batch excluded; F_pre binds on a synthetic pod and never lowers (KCR's 8,301 / 9,393 s maxima reproduced within 1 s); keys (mb4 rung, other-LR recipe, another engine, another GPU refuse; G passes; the config hashes recomputed with the engine's `config_sha256`); kinds; cap structure (j < k, round-up, pod_sizes, > 4 refuses); the zero hold at the cent; KITS_GLOB and the lock with the stage-1 `budget.py` run unchanged inside a `family-probe-s78-*` copy; the job runner's dry run on a fake `PREFLIGHT-DONE.json` (defers job 4 of 4 at 30,000 s left; refuses missing/NaN fields, a 1.16 pod, 7.99 GB free); the audit hook saw only allow-listed names on the fake kit with traps and on the real root |
| KCR test 13 / KCR:226 mutants die | **passed (M)** | §3 row 13: 35 / 35 killed by real tests, baseline 20 passed, no invalid run; `mutants-all.json` |
| KCR test 14 (what stays frozen now) | **passed** | test 14: engine identity `472fc7f6…` from the engine's own `code_identity()`; the stage-1 files' pins; stdlib-only imports, nothing from the Gate B kit, no `sys.path` edit; no `__pycache__` under this kit, the stage-1 kit or `experiments/safety_selection/` after the suite |

## 6. Jobs for the lead

1. **Merge by explicit paths** (seven new files): `runkit/stage1-78b/{rules_78b.py,measured-basis-78b.json,derive_78b_basis.py,README.md}` and `runkit/stage1-78b/tests/{test_rules_78b.py,mutation_spec_rules_78b.json,run_mutants_78b.py}`.
2. **Guard commands after the merge** (git state, so not tests): `git status --porcelain -- experiments scripts runkit/stage1-olmo` (must print nothing) and `git diff --quiet HEAD -- runkit/stage1-olmo`.
3. **The suite in the main checkout:** `cd /Users/spiderishi/Coding/attribution && PYTHONDONTWRITEBYTECODE=1 PY1 -B -m pytest -p no:cacheprovider -q -rfE runkit/stage1-78b/tests/test_rules_78b.py` (about 1 s; tests 02b/05b/15b read `tmp/family-probe-sp-*`).
4. **The mutation run (about 10 s; a new scratch folder outside the checkout):** `PY1 -B /Users/spiderishi/Coding/attribution/runkit/stage1-78b/tests/run_mutants_78b.py /Users/spiderishi/Coding/attribution /Users/spiderishi/Coding/attribution/tmp/mut-78b-<date> /Users/spiderishi/Coding/attribution/tmp/mut-78b-<date>.json ALL` (expected: baseline exit 0, 35 killed).
5. **Record the constants convention** in Part 1 / the KCR errata: the rule's constants are the exact basis maxima; KCR §4's printed requirement integers differ by <= 1.2 s; caps, guards and spends are identical.
6. **T6a / T4:** when the recipe-S_78 configs exist, append their `config_sha256` to `RECIPE_ALLOW` (one line) and extend test 7; before the retrain and the A1 pass run.
7. **T4's job runner:** pass the preflight's `verification.json` `cap_projection` block to `preflight_fields` (M: `PREFLIGHT-DONE.json` holds `training_s` and `ms_per_step_full` but not `untuned_projected_s`; KCR:110's "the fields already exist in PREFLIGHT-DONE.json" is right for two of the three). Call `check_keys` before the pod, `job_decision` before each job, `s_obs_from_progress` after each arm; `cap_hours`/`pod_spend_usd`/`funding_need_usd`/`block0_report` in the plan (README "What the T4 job runner calls").
8. **KD9 on the first engine-Y pod:** `derive_78b_basis.py --root … --out NEW.json --extra-unit FAMILY:/abs/path/to/tmp/family-probe-s78-<family>-<block>`, record the step, copy over the basis, set `BASIS_SHA256` and any constant that moved, add Y to `ENGINES`, re-run the suite (README, KD9).
9. **Optional:** the engine suite with `--ignore=experiments/safety_selection/tests/test_ss_gateb_runkit.py` at merge time (not needed for this track; the lead's standard check).

## 7. Unresolved concerns

1. **The <= 1.2 s requirement difference against KCR's printed integers** (§2 item 1, §5). Either convention is
   defensible; the rule keeps the exact maxima so that tests 2, 4 and 5 hold literally. The lead should name the
   convention once (job 5).
2. **The E caps are judgment calls** (KD6 asks for them). The scorer kinds scale 1B estimates by 2.3 (RP:43) and 1.5;
   `anchor` does not read the anchor bank's size; `retrain` carries a 3 h upper (4.5 h cap) because engine Y is
   unmeasured at 7-8B; `ref_train_bqi` doubles the training term for Y. Each runs alone, so a cap that is too wide only
   reserves money at the guard; a cap that is too tight stops the pod mid-job. The first run of each kind measures it.
3. **OLMo's scoring fit.** KCR §4 said "about 1,190 s" with Llama's guard slopes and OLMo's own harm fit; the basis
   gives 1,157.6 s (Llama guard 149.1 + guard-on-samples 299.9, OLMo harm 670.8, fixed 37.8). Llama's own fit gives
   1,163.2 s (KCR: about 1,160). Both are below SCORE_ALLCAP 1,250 s; the 32 s gap on OLMo is not explained here (the
   fit's inputs are stated in the basis: `scoring_fit`).
4. **PREFLIGHT-DONE.json lacks `untuned_projected_s`** (job 7); the rule's `preflight_fields` reads it from the
   verification block, so T4 must pass that document. A missing field refuses, as Gate B's rule does.
5. **Tests 02b, 05b and 15b read the main checkout's `tmp/` by absolute path** and skip elsewhere. In the lead's
   checkout they ran (no skips). On another machine the basis file still carries every value they check.
6. **The GPU-name string** in the basis holds one space (`NVIDIA A100-SXM4-80GB`); the output check allows at most one
   space in a string of <= 64 characters. Everything else is a hash, a name, a stage or a UTC stamp.
7. **The kit route's name collision rule.** No file here has a stage-1 kit name; `tests/run_mutants_78b.py` and the
   spec are new names. T4's copy of the stage-1 kit's `tests/mutants_b15.json` and test files will sit beside them.
