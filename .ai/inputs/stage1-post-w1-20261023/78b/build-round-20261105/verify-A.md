# Verify report, track A = T2: the 7-8B cap rule and its measured basis

Status: DONE. Verdict **VERIFIED_WITH_MINOR** (no blocker, no major; six minor items, three observations).
Report finished 2026-11-05 14:34 UTC (`date -u` read at 14:33:31 UTC right before; the skeleton was written at
14:19 UTC after a `date -u` at 14:19:36). Verifier: the Fable adversarial verifier of track A.
Builder's worktree (read-only for me): `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-a`
(detached at fb51421). My scratch: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/verify-A-scratch/`.
I edited none of the builder's files (their seven SHA-256 values are identical before and after my runs, M §3 row 3).
No git state changed anywhere. No pod, spend, network, install, download, agent or message. The main checkout was
read by absolute path only; no forbidden folder or text file was opened (only the nine allow-listed timing names,
printed as counts and numbers).

Tags: M measured (command given), R read (path:line), E estimate (basis), I inference.

## 1. Files changed

None in the worktree. New files, all mine, under `…/scratchpad/b78/reports/`: this report;
`verify-A-scratch/{recompute_constants.py, golden_independent.py, audit_derive.py, hand_mutants.py, trap_test.py,
stage_gaps.py}` (scripts); `verify-A-scratch/{basis-rederived.json, mutants-builder-rerun.json, mut/hand-mutants.json,
suite-run.txt, runner-run.txt, recompute-run.txt, golden-run.txt, trap-run.txt, audit-run.txt}` (evidence). The scratch
copies (the mutation repos, the fake kits, pytest basetemps) were deleted after their runs; 220 KB remain.

## 2. What I verified and how (alternatives considered)

1. **Constants from the raw files (independent of the builder's code).** `recompute_constants.py` is my own reader: it
   opens only `finished.json`, `create-result.json`, `verification.json`, `BOOTSTRAP-READY.json`, `PREFLIGHT-DONE.json`,
   `JOB-DONE.json`, `ledger.jsonl`, `progress.jsonl` of the 17 kits KCR:9 names (138 opens, 8 distinct names) and
   recomputes each family's maxima: training s/step (whole run / steps), the first greedy batch, the slowest capped
   32-row batch after the first (greedy and sampled, by the ledger's stage windows), the early stages, outer − Σ stage
   seconds − the other unit's stages, the fine-tune-only job maximum, the preflight maxima, the smallest padded tokens
   per step. Alternative: trust test 2 (it compares the constants with the basis file the same code wrote). Rejected:
   a shared bug in derive would pass test 2.
2. **Golden numbers (independent arithmetic).** `golden_independent.py` imports nothing from the kit; it computes
   GEN_ALLCAP, upper_M, requirements, 1-4 arm caps, guards, spend uppers, per-arm costs, the block-0 need and the
   two-33-step Llama cap from (a) KCR §4's printed constants and (b) the basis file's maxima, with its own half-up
   cents and 0.25 h round-up.
3. **The derivation's privacy with my own hook and my own traps.** `audit_derive.py` installs a `sys.addaudithook`
   before importing the builder's derive, runs it on the real root and lists every open under `tmp/`. `trap_test.py`
   builds a synthetic kit (the builder's `fake_kit` helper is used only to make the fixture) and plants eleven trap files
   the builder did not plant (`create-secrets.json`, `pod.json`, `orchestrate.jsonl`, `records.jsonl`, `steps.jsonl`,
   `plan.json`, `eval/verification.json`, `cuda-preflight-1/eval-sample/generations.jsonl`,
   `cuda-preflight-1/verification.json`, `verified.jsonl`, `KIT-README.md`), each holding a marker string.
4. **Can each test fail?** `hand_mutants.py` copies the kit into a scratch repo (symlinks for everything else), applies
   one replacement to the copy, runs the builder's suite, restores the copy and checks its hash. 20 mutants of my own
   (not in the builder's spec: half-even cents, `j < k−1`, `min` for the first batch, `finite` without `isfinite`, a zero
   speed field passing, the `rows == 32` filter dropped, START_MARGIN 1,700, margin 1.14, SCORE 1,240, 32 batches, the
   floor ignored, a strict guard, no remaining-time decrement in the dry run, a stripped GPU name, 5 arms allowed, s_obs
   without the floor at 1, the E cap without the overhead, the hold reason changed, derive without the sampled series,
   derive's outside without the other unit) plus 8 of the builder's spec entries re-run by hand. I also ran the
   builder's runner once on their spec (their claim: 35/35 killed).
5. **Edge inputs by hand** (`PY -B -c`, §3 row 7): NaN, inf, zero, negative, bool, string, None in the speed factor,
   the requirement, the floor, `train_scale`, `s_obs`, `job_decision`, `gate`, `launch_allowed`, `cents`, `round_up_s`.
6. **Readings against the rulings and the check:** KD4's reason string (ruling 11 KD4, R: lead-rulings-part1:162-163,
   the string that governs over the check's C8 wording); KD7's prefix against `budget.py:39` `KITS_GLOB` (R); KD6's E caps
   and their sources (RP:43's 1.9-2.3x, R: 2026-10-17-icml-replan-PROPOSAL.md:43; `stage1_rules.py:87-119` and
   `:107` for 3,600 / 7,560 / 3,600 / 2,012 / 2,400 / 900 / 600 / 88.02 s, R); the copied helpers against
   `stage1_rules.py:1049-1077, 1107-1109, 1183-1210, 1236-1238` (R: `round_up_s`, `pod_sizes`, `cents`,
   `launch_pod_spend_usd`, `funding_need_usd`, `gate` are verbatim copies; `guard_usd` adds the hold term, which is 0).

## 3. Commands run, with exit status (all foreground, all under 10 s)

PY1 = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python`; PY2 =
`/Users/spiderishi/Coding/attribution/.venv/bin/python`; WS = the builder's worktree; S = my scratch folder.

| # | Command (abridged) | Exit |
|---|---|---|
| 1 | `date -u` (14:19:36 and 14:33:31 UTC) | 0 |
| 2 | `git -C WS status --porcelain` (x3, also `--ignored`) -> `?? runkit/stage1-78b/` only; `git -C WS rev-parse HEAD` -> fb51421 | 0 |
| 3 | `shasum -a 256` of the seven kit files before and after every run: `56ea39a9…` rules, `fc92a568…` basis, `e020931f…` derive, `5205bc07…` README, `f077815b…` tests, `5fade2c0…` spec, `0d742104…` runner; identical | 0 |
| 4 | `sed -n`, `grep -n`, `ls -d`, `find -maxdepth` (names only) over the rulings, plan, check, KCR, RP:43, `stage1_rules.py`, `budget.py`, `common.py`, the 27 `tmp/family-probe-sp-*` folder names, one kit's file names | 0 |
| 5 | the builder's suite in WS: `PYTHONDONTWRITEBYTECODE=1 PY1 -B -m pytest -p no:cacheprovider -q -rfE --basetemp S/… runkit/stage1-78b/tests/test_rules_78b.py` -> **20 passed in 0.18 s** (`S/suite-run.txt`; a first run gave 20 passed in 0.20 s) | 0 |
| 6 | `PY2 -I -B WS/runkit/stage1-78b/rules_78b.py golden` and `e-caps` | 0 |
| 7 | `PY2 -B -c` edge probes (§6 items 1, 4; §8) and a second probe (`check_keys` scope, `block0_report` values, 4 arms + evalonly refuses, 3 arms + evalonly cap 10.25 h) | 0 |
| 8 | `PY2 -I -B` inline: the basis file's families block and the 17 units' numeric summary | 0 |
| 9 | `PY2 -I -B S/recompute_constants.py` (`S/recompute-run.txt`): 17 of 18 constants EQUAL; OLMo OUTSIDE_MAX_S mine 108.637 vs 108.638 (§8 obs. 1) | 1 |
| 10 | `PY2 -I -B S/golden_independent.py` (`S/golden-run.txt`): ALL GOLDEN CHECKS PASS | 0 |
| 11 | `PYTHONDONTWRITEBYTECODE=1 PY2 -B S/audit_derive.py S/basis-rederived.json` (`S/audit-run.txt`): 155 opens, 9 distinct allow-listed names, 17 kits, 0 outside the allow-list, 0 forbidden parts; SHA-256 `fc92a568…` == pin == worktree bytes | 0 |
| 12 | `PYTHONDONTWRITEBYTECODE=1 PY1 -B S/trap_test.py S/trap` (`S/trap-run.txt`): 18 opens, 9 names, my traps opened: none; marker text in output: False; `check_path` refused 9 of 11 trap paths (§6 item 6 names the two it allows) | 0 |
| 13 | `PYTHONDONTWRITEBYTECODE=1 PY1 -B S/hand_mutants.py S/mut` (`S/mut/hand-mutants.json`): baseline 20 passed; **27 killed, 1 survived** (`V-sobs-rows-filter-off`); 0 invalid | 0 (the script's own exit; verdicts in the file) |
| 14 | the builder's runner: `PY1 -B WS/runkit/stage1-78b/tests/run_mutants_78b.py WS S/mut-builder2 S/mutants-builder-rerun.json ALL` (`S/runner-run.txt`): baseline exit 0, **35 killed**, 0 survived, 0 invalid | 0 |
| 15 | `PY2 -I -B S/stage_gaps.py`: unit 1103's ledger stage order and gaps (generate -> sample gap 0.09 s; train segments gap 6.91 s; before load_guard 8.87 s) | 0 |
| 16 | `git -C /Users/spiderishi/Coding/attribution status --porcelain -- runkit experiments scripts` -> nothing | 0 |
| 17 | `find WS/runkit WS/experiments -name __pycache__ -o -name .pytest_cache` -> nothing; `rm -rf` of my scratch copies only | 0 |

Not run: the engine suite (`experiments/safety_selection/tests`, `--ignore` the fixture test). Reason: no file under
`experiments/` differs from HEAD in the worktree (row 2) and test 14 checks the engine identity `472fc7f6…` through the
engine's own `code_identity()` (R: `common.py:31-36` hashes every `safety_selection/*.py` and the reused modules), so
the suite would test nothing this track touched. Its command is in §7 for the lead's merge-time check.

## 4. Evidence paths

- My recompute: `S/recompute-run.txt` (per-unit numbers for all 17 units; per-family maxima against the builder's).
- My golden derivation: `S/golden-run.txt` (both arithmetics; cap slack; block 0; the 7.0 h Llama case).
- My audit hook over derive: `S/audit-run.txt`; the re-derived basis `S/basis-rederived.json` (SHA-256 `fc92a568…`).
- My trap test: `S/trap-run.txt`. My hand mutants: `S/mut/hand-mutants.json`. The builder's runner re-run:
  `S/mutants-builder-rerun.json`, `S/runner-run.txt`. The suite: `S/suite-run.txt`.
- The builder's own evidence, read: `…/scratchpad/b78/reports/mutants-all.json` (counts {killed: 35}, baseline 0, 35
  results; matches my re-run).

## 5. Acceptance criteria (the builder's list, re-checked by me)

| Criterion | My result | Evidence |
|---|---|---|
| KCR tests 1-15 pass | **passed** | row 5: 20 passed (tests 1-16 incl. 02b/05b/15b on the real root, no skips) |
| Golden caps 4.25/6.5/8.5/10.5 h and 4.5/7.25/9.75/12.5 h; guards and spends to the cent; block 0 need $56.06 | **passed** (independently) | row 10: caps, guards $13.86/18.03/21.73/25.43 and $14.33/19.41/24.04/29.13, spends $5.12/$16.18 and $6.27/$20.80, per-arm $5.12/4.40/4.17/4.05 and $6.27/5.56/5.32/5.20 (= KCR §8 rule column), block 0 guard $44.85 / spend $33.30 / need $56.06, Llama two 33-step arms 7.0 h |
| Golden requirements 12,243/12,365 and 12,499/12,613 s | **passed as the builder states it** | row 10: KCR's printed constants reproduce the integers exactly; the live rule gives 12,244.15/12,365.42 and 12,498.05/12,612.47 (+1.15/+0.42; −0.95/−0.53 s). I agree with the builder's choice (the exact maxima) and with raising the convention to the lead (§7 job 2) |
| Every measured unit below upper_M(38) | **passed** | test 3 (row 5); my recompute: slowest OLMo 6,450 s and Llama 8,466 s against 10,565.4 / 10,812.5 s; the two-unit pods 6,876 / 10,452 s also below |
| The basis hash is pinned | **passed** | `BASIS_SHA256 = fc92a568…`; my hook run re-derives the same bytes from the real root (row 11); test 2 refuses a changed copy |
| Each constant equals the maximum recomputed from the 17 units | **passed** (17 of 18 bit-equal at the printed precision; OLMo OUTSIDE_MAX_S differs by 0.001 s from my sum, a rounding-order artifact, §8 obs. 1) | row 9 |
| The copied helpers equal the stage-1 kit's | **passed** | test 9 (row 5); the sources are verbatim copies (R, §2 item 6); my edge probes: `cents` 18.025 -> 18.03, 2.675 -> 2.68, 0.005 -> 0.01, −2.675 -> −2.68; `round_up_s` 899.9999994 -> 900, 900.0000006 -> 1,800, 0 -> 0 |
| `git status --porcelain` lists only new files under `runkit/stage1-78b/` | **passed** | row 2 (three times, incl. `--ignored`); no bytecode (row 17) |
| KCR test 13 / KCR:226 mutants die, killed only on a real failure | **passed** | row 14: 35/35 killed, baseline 0; my own 28 hand mutants: 27 killed by real failures, 1 survived (§6 item 2) |
| Test 14 adapted (engine X, stage-1 pins, no Gate B import, no bytecode) | **passed** | row 5; my grep: `gate-b-olmo` / `gateb` appear only in the docstring; `sys.path` absent; stage-1 pins `d52614e4…` / `f4760c08…` equal the main checkout's files (row 3 of the builder's, re-hashed by me) |
| Test 15: derive opens allow-listed names only; no string longer than a hash | **passed** (with my own hook and traps) | rows 11-12 |
| Zero-hold reason string (KD4) | **passed** | `rules_78b.py:64-65` equals ruling 11 KD4 byte for byte (R: lead-rulings-part1:162-163); test 10 pins it; my mutant `V-hold-reason-changed` died |
| Working-copy prefix vs `budget.py` KITS_GLOB (KD7, C7) | **passed** | `family-probe-s78-` matches `family-probe-*` (R: budget.py:39); test 11 runs the stage-1 `budget.py` unchanged inside such a copy |
| KD6 explicit caps with sources | **passed** | every `e_upper_s` entry carries a basis string; the 2.3 factor is RP:43's (R); the 1B seconds equal `stage1_rules.py:87-119, :107` (R); `rep_pass` pinned at KD6's 16.5 h; `retrain` 4.5 h inside M3's 4-5 h; `e-caps` table equals the README's |
| No import from `runkit/gate-b-olmo/` or `tmp/gate-b-olmo/` | **passed** | test 14 (AST imports: stdlib only); my grep |
| Engine suite | **not tested** (by the builder and by me; reason in §3) | — |

## 6. Defects (none blocking; all minor)

1. **`s_obs_from_progress` passes silently on rows without `capped` / `rows` keys** (`rules_78b.py:406`:
   `int(row.get("capped", 0))`, `int(row.get("rows", 0))`). M: rows `[{kind: generate, batch: 0, elapsed_s: 1.0},
   {…, batch: 1, elapsed_s: 5000.0}]` return s_obs = 1.0 with no `Refused`, so a 5,000 s batch is not seen. KCR test 5
   asks that "a missing or empty progress file refuses"; a present file in a drifted format disables KD11's check
   without a word. Likelihood is low (engine X is pinned; derive's `r["capped"]` would KeyError at KD9), so minor.
   Fix: refuse when any `generate` row lacks `capped` or `rows` (or when no 32-row batch was seen at all).
2. **Test gap: the `rows == GENERATION_BATCH` filter is unpinned.** M: my mutant `V-sobs-rows-filter-off` (the filter
   replaced by `True`) survives all 20 tests. The mutation only raises s_obs (the safe direction), and on the 17 real
   files s_obs stays 1.0 either way, so the rule is unaffected; but KCR:113's "32-row" clause has no test. Fix: a test-5
   case with a slow capped 20-row last batch that must not raise s_obs (or drop the clause deliberately).
3. **`check_keys` does not check the manifest or the evaluation bank.** R: `rules_78b.py:280-288` checks recipe,
   engine and GPU only (KCR §4's three keys, so the spec is met). But BATCHES = 34 and GEN_ALLCAP assume the 468/600
   bank at batch 32 and cap 2,048, and KCR:147 says "the basis holds only if the evaluation bank is unchanged (refuse
   otherwise)"; `MANIFESTS` is recorded (test 2) but unused by any gate. Fix: add `manifest_sha256` (and the bank sizes
   from the plan) to `check_keys`.
4. **`launch_allowed(NaN, cap)` raises `decimal.InvalidOperation`, not `Refused`** (`rules_78b.py:493`). M. The
   direction is safe (nothing launches), but the caller sees a foreign exception. Fix: `finite()` the balance first.
5. **A no-op assertion in test 3** (`test_rules_78b.py:185-187`: `assert … <= upper + 1e-6 or True`). It can never
   fail and reads as a check. Fix: remove the `or True` (the inequality then holds by construction) or delete the lines.
6. **`check_path` is wider than the nine names derive opens.** M (my trap test): it allows any `create-*.json`
   (`create-secrets.json` passed the gate) and an allowed name in any non-forbidden folder
   (`cuda-preflight-1/verification.json` passed). derive never opens either (my hook: nine names only), and the plan's
   privacy rule itself says `create-*.json`, so this is a hardening note. Fix: list `create-intent.json` and
   `create-result.json` exactly, or check the path's parent too.

## 7. Jobs for the lead

1. Merge decision: the seven files are fit to merge as they stand; items 1-6 above are one-line fixes for the fix round.
2. Name the constants convention once (Part 1 / the KCR errata), as the builder asks: the rule's constants are the
   basis file's 3-dp maxima; KCR's printed requirement integers differ by at most 1.2 s; caps, guards and spends are
   identical. My recompute confirms the caps' slack to the next 0.25 h step is about 300 s on both families (§8 obs. 2).
3. At merge: the builder's guard commands and suite (build-A.md §6 jobs 2-4); optionally the engine suite:
   `cd /Users/spiderishi/Coding/attribution && PYTHONDONTWRITEBYTECODE=1 PY1 -B -m pytest -p no:cacheprovider -q
   experiments/safety_selection/tests --ignore=experiments/safety_selection/tests/test_ss_gateb_runkit.py`.
4. T4: pass `preflight_fields(PREFLIGHT_DONE, verification)` (the merged three fields) to `job_decision`; M: none of
   the 17 `PREFLIGHT-DONE.json` files holds `untuned_projected_s` (my recompute, row 9), so the raw document refuses.
   Consider giving `job_decision` a `verification` parameter in the fix round.

## 8. Unresolved concerns and observations

1. **The 3-dp maxima carry ±1 ms rounding-order noise.** M (row 9): OLMo OUTSIDE_MAX_S is 108.638 in the basis
   (derive rounds at each stage accumulation and again on the sum), 108.637 when each stage total is rounded once,
   108.636 from the raw sum; Llama's 162.778 sits 0.001 s below the raw sum 162.779. So "no constant sits below a
   measurement" holds to the file's rounding convention, not to the millisecond. Immaterial: the outer job time is in
   whole seconds and the margins are 300-1,800 s. The basis is reproducible byte for byte, which is what the pin needs.
2. **Cap slack.** M (row 10): the 4-arm worst sums are 37,497.9 s (OLMo) and 44,700.2 s (Llama) against caps of
   37,800 and 45,000 s: about 300 s each. A KD9 re-measure that raises a family's requirement plus three measured uppers
   by more than that moves the 4-arm cap to 10.75 / 12.75 h (+$0.46 on the guard). Not a defect; a note for KD9.
3. **The first sampled batch's "seconds" include the generate -> sample stage gap.** M (row 15): 0.09 s on unit 1103;
   s_obs = 1.0 on all 17 real files (test 05b), so it does not bind. The builder's statement is right.
4. The builder's concerns 1-6 (build-A.md §7) stand; I add nothing to them beyond items 1-6 above.
5. `STAGE1_1B_ESTIMATES_S["untuned_answers"]` (7,560 s) is defined but unused by `e_upper_s` (M, `inspect`): dead
   data, harmless.
