# O3A-verify2: adversarial verification of the track A fix round (O3A-fix1)

Verifier: independent adversarial verifier (a Fable 5.1 subagent; the launcher records routing).
Started 2026-11-05 09:40 UTC; finished 09:51 UTC (clock read with `date -u` at 09:40, 09:43, 09:47 and 09:50).
Subject: the fix round O3A-fix1.md against the defects of O3A-verify1.md, checked in the combined worktree
/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/ws-all (detached at e89d74f; 13 untracked entries before and after; `git diff --stat` empty; no bytecode outside tmp/).
Scratch (kept as evidence): /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/verify-O3A-2/ (script.diff, tests.diff, read_fixture_numbers.py + fixture-numbers.txt, sim_d3.py + sim_d3.txt + sim_d3.json, tiny/config.json, wrong/config.json, rule-check-tiny/rule-check.json (new script), rule-check-tiny-old/rule-check.json (old script), scripts-tests-o3.txt, scripts-tests-main.txt). Every pytest basetemp was under scratchpad/o3/tmp/bt-v2-* and was deleted after its run. Nothing written outside this folder and this report; ws-all, ws-a and the main checkout untouched.

## Verdict: VERIFIED

Every defect that mattered is fixed as reported, the fix changed nothing else, and nothing regressed.

- **D1 (records, the threshold maximum): FIXED.** The docstring's numbers now equal the fixture records (largest output-side cosine 0.9353, Qwen2.5-7B; the largest input side 0.0414), re-read here with my own reader. The committed track A report's "0.87" is outside this round's files (the fix report's open point 3 for the lead).
- **D2 (the combined build's suite): NOT THIS ROUND'S, correctly.** The test is under experiments/safety_selection/tests/ (the never-edit rule); it still fails in ws-all at line 161 under both environments; the lead's two-token fix is confirmed by my own count (69 = 59 + 9 + S, no disagreeing recipe), and track C's fix round drafted the same patch.
- **D3 (the input-side reference check; the probe's money): FIXED and reproduced.** The old script (ws-a) reads null on the lineage's expected state (random input reference rows, parallel output rows); the new script reads True, with the family `verdict_of` giving `use_this_recipe` True; the catches (a chat output row along the unused rows, a bit-identical input row, no output reference) still refuse. The `--rule-check` form on the tiny model records per side `rule` and `distinct` as the fix report says, with the same measured numbers as before.
- **Nothing else changed.** Exactly two files differ from ws-a (hashes equal the fix report's "after" column); my diffs equal the fix report's diffs line for line; every hunk maps to D1, D3, N2, N3, N5, N6 or N8; `main` has no hunk (the diff pin holds); the three other track A files and the family preflight are unchanged (the family byte-equal to the main checkout's).
- **Nothing regressed.** scripts/tests: 30 passed under 4.57.1, 20 passed + 3 skipped under 4.56.2 (the fix report's counts); the first verifier's edge attacks give byte-identical output on the old and the new tree; the refusals (both forms) fire with the fixed message, now without a folder in the `--rule-check` form (N3); no engine test reads scripts/*.py, and the engine is untouched, so verify round 1's suite results stand.

## Plan

1. Hashes of the six files in ws-all against the fix report's table; the three untouched files and the family preflight unchanged; worktree state (git status, diff, bytecode).
2. Diffs of the two changed files against ws-a's copies; every hunk accounted for by the fix report (D1, D3, N2, N3, N5, N6, N8) and nothing else.
3. D1: the docstring numbers against the fixture records (read by key, numbers only).
4. D2: the failing test still fails in ws-all (the lead's; not in this round's files); the proposed count checked.
5. D3: reproduce the original failure path (random input rows with parallel output rows: null under the old rule, True under the new); the tiny-model --rule-check; the refusal paths; the diff pin.
6. Affected tests under both environments.
7. Worktree state after.

## Step 1: hashes and worktree state (done 09:42 UTC)

- ws-all: detached at e89d74f, `git diff --stat` empty, 13 untracked entries (the same 13 as verify round 1), no `__pycache__` outside tmp/.
- The six hashes in ws-all equal the fix report's "after" column: scripts/cuda_preflight_olmo3.py 3f7edd21... (467 lines), scripts/tests/test_cuda_preflight_olmo3.py 4c5bc46a... (368 lines); conftest.py c8e33a26..., olmo3_tiny.py a399b2fe..., test_olmo3_engine_tiny.py 283fc742... unchanged; scripts/cuda_preflight_family.py b142f3fd..., `cmp` byte-equal to the main checkout's.
- ws-a (the untouched copies): f80389bc... and 7a45f602..., the fix report's "before" column and the track A table.
- Every other untracked file in ws-all was compared with its builder tree (ws-a, ws-b, ws-c): the only other differences are five files under runkit/family-probe-olmo3/ (README.md, finisher.py, host.py, states_tool.py, tests/test_family_probe_olmo3.py), track C's fix round (O3C-fix1), not this one. Track A's fix touched exactly its two files.

## Step 2: the diffs (done 09:44 UTC)

- My `diff -u` of each changed file against ws-a's copy (verify-O3A-2/script.diff, 131 lines, 71 changed lines; tests.diff, 210 lines, 112 changed lines) equals the fix report's scratch diffs line for line with the header lines stripped.
- Script hunks, each accounted for: docstring step 2 (D1 numbers; D3 output/input reasoning; N5 the fixture pin; N6 the opposite row; N8 "output rows" with workplan line 19), docstring step 3 "(or, in the second form, a config)" (N3), the second-form paragraph "random output rows" (D3), `SIDE_RULES` (D3), `comparison_rule()` with `side_rules` and the new rule text (D3), `chat_rows_report_cosine` per-side `rule`/`distinct` and the output-side-only null (D3), `rule_check` with `create_run_dir` after the config check (N3). `main`, `extra_id_rows`, `pairwise_min_cosine`, `refuse_other_family`, `cli` and every import and constant other than `SIDE_RULES` are untouched.
- Test hunks, each accounted for: the module docstring; eight changed tests and one new test as the fix report lists them; the N2 line; the N3 assertion. Nothing else.

## Step 3: D1, the docstring numbers against the records (done 09:48 UTC)

- My own reader (verify-O3A-2/read_fixture_numbers.py; `python -I`, the `chat_rows` subtree by key, numbers only; output kept in fixture-numbers.txt) over the 35 fixture records that carry `chat_rows`: the largest output-side `max_cosine_to_padding` over every record is **0.9353** (Qwen2.5-7B, six records); Llama-3.1-8B 0.8684; OLMo-2-7B 0.4614; OLMo-2-1B 0.2229; the largest input side 0.0414. The fixed docstring's "at most 0.935 ... Llama-3.1-8B 0.74-0.87; OLMo-2-7B 0.46; OLMo-2-1B 0.22; every input side at most 0.04" is right; the old "at most 0.87" is gone from the script.
- The same read confirms D3's lineage evidence independently: on every OLMo-2 record the input padding rows sit at median norm 0.8890 (1B) / 1.2633 (7B), i.e. 0.02·sqrt(d) (0.9051 / 1.2800), and `cosine_to_padding_mean` differs from `max_cosine_to_padding` (not mutually parallel); on every output side the two are equal (parallel). Llama's and Qwen's input padding rows are at norm 0.0000.
- D1 FIXED in the script. The committed track A report still says 0.87 (the fix report's open point 3; not this round's file).

## Step 4: D2, the lead's test (done 09:46 UTC)

- `test_ss_family_codec.py::test_the_recipe_accepts_the_header_field_and_every_existing_recipe_still_validates` still fails in ws-all at line 161 under both environments (1 failed in 0.04 s each), as expected: the file is under experiments/safety_selection/tests/, outside this round's two files and the never-edit rule. `git diff --stat` is empty, so no fix round applied anything to it.
- The proposed two-token fix checked by my own count (keys and file names only): 60 recipes under the old prefixes, 69 under the extended tuple, Gate B's S exists, so 59 + 9 + S = 69; no recipe's `assistant_header`/`guard_over_limit` fields disagree with the extended rule. Track C's fix round drafted the same patch (reports/O3C-fix1-D3-test_ss_family_codec.patch: the tuple at line 159 and `59 + 9 + gate_b_s.exists()` at line 165). D2 remains the lead's commit, correctly scoped out of this round.

## Step 5: D3, the rule (done 09:49 UTC)

- verify-O3A-2/sim_d3.py loads the OLD script (ws-a, f80389bc...) and the NEW script (ws-all, 3f7edd21...) by path under distinct names (both bind the one cached family module from ws-all) and runs both on the same rows at d = 4096 in bfloat16 (ids remapped into a 16-row matrix; the rule indexes rows by id). Output in sim_d3.txt and sim_d3.json; every case as expected ("ALL CASES OK: True"):
  1. The lineage's expected state (seven input reference rows at N(0, 0.02); seven output reference rows parallel at norms 0.9-1.2; chat output rows at the records' maxima 0.46 / 0.935 / 0.934): **old null, new True**. New per side: input `rule` bit_identity, not parallel (min pairwise -0.033), `distinct` True; output `rule` cosine, parallel (min pairwise 0.999998), `distinct` True; no note; `bit_identical_rule` True. This is the original D3 failure reproduced on the old script and absent on the new.
  2. Input reference rows at norm 0 (Qwen's) and 1e-21 (Llama's): old null, new True.
  3. `<|im_end|>`'s output row laid along the unused rows (scaled, not bit-identical): new False (the catch the rule exists for is kept).
  4. Random output reference rows: new null with the output-side note.
  5. `<|im_start|>`'s input row bit-identical to an unused row: new False, `used_input.distinct` False, `bit_identical_rule` False.
  6. Parallel input references with `<|im_start|>`'s input row along them: old False, new True (recorded, not used: the fix's stated behaviour and the lead's open point 1).
  7. The output-side edges at d = 4096 in bf16: cosine 0.985 True, 0.995 False.
  8. Through the family `verdict_of` on a minimal report: `use_this_recipe` True on the lineage state under the new rule, False under the old, False with a tied output row, False with no output reference. So the pod path (`preflight_probe.py` reading `use_this_recipe`) now passes the expected state and still refuses the catches.
  9. bf16 rounding of parallel rows at norms 0.9-1.2: smallest pairwise cosine 0.999998 over 20 draws; the reference check has a margin of about 1e-2 over its own threshold.
- The `--rule-check` form on the tiny config with the cached tokenizer (exit 0; verify-O3A-2/rule-check-tiny/rule-check.json): `script_sha256` 3f7edd21..., `family_script_sha256` b142f3fd..., `side_rules` recorded, Olmo3ForCausalLM, 100,278 rows, extra_id x7 (100256, 100270-100275), codec eos 100257 stops [100257, 100265] pad 100277, LoRA r4 8,704; input `rule` bit_identity, not parallel (min pairwise -0.3593), `distinct` True; output `rule` cosine, not parallel (min pairwise -0.2847), `distinct` null; `chat_rows_distinct` null with the output-side note. The numbers equal the fix report's step 4. The old script on the same config gives the same per-token numbers and the same pairwise minima (only the keys `rule`/`distinct` and the note's text differ), so the recorded quantities did not move.
- The refusals: the `--rule-check` form with an Olmo2Config exits 2 with the fixed message and makes no folder (N3 fixed); the pod form with the OLMo-2-7B recipe exits 2 before any folder (unchanged).
- The first verifier's attack_rule.py (edge behaviours: bf16 deviation 1.3e-6, the normalize eps at norms 1e-21/1e-12/1e-9/0.89, a zero and an opposite chat row, a mixed reference, the float32 edge at 0.99, "input reference ok, output not": null) gives byte-identical output on the old and the new tree: nothing regressed at the edges.
- The diff pin: `main` has no hunk in the diff (the hunks are the docstring, the constants, `comparison_rule`, `chat_rows_report_cosine` and `rule_check`), and `test_main_is_the_family_main_with_the_comparison_step_replaced` passes.
- Residual, as the fix report states: this is a simulation from the lineage's records, not a reading of OLMo 3's weights (none on the Mac). The remaining way a candidate can read null is an output-side reference that is not parallel on the Instruct checkpoint, where the 5 Oct read of the Base (output rows, cosine 1.000) is the evidence; the fix removed the side that had evidence against it and kept the side that has evidence for it.

## Step 6: the affected tests (done 09:48 UTC)

- O3 (4.57.1): `pytest -q -p no:cacheprovider --basetemp=<fresh> -rs scripts/tests`: **30 passed in 8.89 s**, exit 0 (22 tests collected from test_cuda_preflight_olmo3.py, including the new `test_only_the_output_side_needs_a_clean_reference`; 8 from test_olmo3_engine_tiny.py).
- MAIN (4.56.2): **20 passed, 3 skipped in 5.63 s**, exit 0 (the skips: "transformers has no olmo3 model code", test_olmo3_engine_tiny.py:27 and test_cuda_preflight_olmo3.py:276 x2).
- Both equal the fix report's counts. The engine suites are unaffected by this round's files: no test under experiments/*/tests or scripts/stage1/tests globs or walks scripts/*.py (grep; the only globs are over scripts/*/settings/*.json), nothing imports scripts/cuda_preflight_olmo3.py, and the engine is untouched (`git diff --stat` empty, engine X unchanged), so verify round 1's suite results stand (D2 the one failure).
- Basetemps bt-v2-* deleted after each run.

## Step 7: worktree state after (done 09:50 UTC)

- ws-all: 13 untracked entries, `git diff --stat` empty, no `__pycache__` outside tmp/; the two changed files still 3f7edd21... and 4c5bc46a..., the family preflight b142f3fd...; no bt-v2-* basetemp left; the main checkout's scripts/ and test_ss_family_codec.py clean.

## Commands run (environments, exit codes)

All Python with `-B` and PYTHONDONTWRITEBYTECODE=1, HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 where a library loads; my own readers with `-I`; pytest `-q -p no:cacheprovider --basetemp=<scratchpad>/o3/tmp/bt-v2-*` (deleted after each run); cwd = ws-all unless stated. O3 = /Users/spiderishi/Coding/attribution/tmp/olmo3-venv/bin/python (transformers 4.57.1, peft 0.17.1, torch 2.8.0); MAIN = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (transformers 4.56.2). No network, no install, no pod, no git state change, no edit of ws-all, the main checkout, the engine, the family preflight or any record. Forbidden paths: none opened (the only tmp/ files read: the 35 tmp/family-probe-*/expected-fixture-probe.json records' `chat_rows` subtree by key, numbers only; the cached OLMo 3 config.json and tokenizer snapshot; the receipt's keys).

| Step | Command | Result |
|---|---|---|
| 1 | `git status --short`, `git log -1`, `git diff --stat`, `shasum -a 256` of six files in ws-all and ws-a, `cmp` family vs the main checkout, `find` for bytecode | 13 entries; e89d74f; empty; hashes as the fix report's table; byte-equal; none |
| 1 | `cmp` of every untracked file in ws-all against ws-a/ws-b/ws-c | 7 differ: the two track A files (this round) and five track C kit files (O3C-fix1) |
| 2 | `diff -u` of the two files against ws-a; `diff` of those against fix-O3A/*.diff with the header lines stripped | 131 / 210 lines; equal |
| 3 | O3 `-I` read_fixture_numbers.py | exit 0; output max 0.9353, input max 0.0414; OLMo-2 input rows non-parallel, output rows parallel |
| 4 | O3 and MAIN pytest of the one D2 test in ws-all | 1 failed each (line 161); exit 1 |
| 4 | O3 `-I` count by prefix | 60 old / 69 new; S exists; no disagreeing recipe |
| 5 | O3 sim_d3.py (PYTHONPATH=ws-all) | exit 0; ALL CASES OK (nine cases, listed in step 5) |
| 5 | O3 `scripts/cuda_preflight_olmo3.py --rule-check` on tiny/config.json with the cached snapshot and the OLMo 3 codec flags (PYTHONPATH=ws-all) | exit 0; the fix report's step 4 numbers; `script_sha256` 3f7edd21... |
| 5 | the same with wrong/config.json (an Olmo2Config) | exit 2, the fixed message, no out folder |
| 5 | the pod form with the OLMo-2-7B recipe | exit 2, the fixed message, no out folder |
| 5 | the old script (ws-a) `--rule-check` on the same tiny config | exit 0; identical token numbers and pairwise minima; only `rule`/`distinct` added and the note's text changed |
| 5 | verify-O3A/attack_rule.py on ws-all and on ws-a | identical output; exit 0 both |
| 6 | O3 `pytest -rs scripts/tests`; `--collect-only` | 30 passed in 8.89 s; 22 + 8 collected; exit 0 |
| 6 | MAIN `pytest -rs scripts/tests` | 20 passed, 3 skipped in 5.63 s; exit 0 |
| 6 | grep of experiments/*/tests and scripts/stage1/tests for globs or walks of scripts/ | only scripts/*/settings/*.json; nothing reads scripts/*.py or scripts/tests |
| 7 | state after (step 7) | unchanged |

## Acceptance criteria

- Each defect fixed as reported, the original failure reproduced on the fixed tree: D1 PASSED (the numbers re-read from the records); D3 PASSED (the old script nulls the lineage state, the new passes it; the catches kept); D2 NOT THIS ROUND'S (reproduced as still failing; the lead's fix confirmed by count).
- The fix changed nothing else (hashes and diffs against the fix report): PASSED (two files; every hunk accounted for; `main` untouched; the other four files unchanged).
- The affected tests run: PASSED (30 under 4.57.1; 20 + 3 skipped under 4.56.2; the counts of the fix report).
- No regression: PASSED (the edge attacks identical on both trees; the refusals; the recorded numbers unchanged; the engine suites not reachable by this round's files).
- Hard rules: no forbidden path opened, no network, no install, no pod, no git state change, no edit outside my scratch and this report; every command foreground and under 10 minutes (the longest 8.89 s); basetemps deleted.

## Notes (minor; not defects)

- V2-N1. A direct `python scripts/cuda_preflight_olmo3.py ...` from the repository root needs PYTHONPATH=<root> for `experiments` (the family preflight has the same import). The kit sets it (preflight_probe.py:108, job_runner_probe.py:126, pack_setup.py:175) and so does the test's `run()` helper; my first attempt without it failed before the script's own code ran. Nothing to change.
- V2-N2. Docstring step 2 says "median norm 0.889 and 1.263 = 0.02 * sqrt(d)"; the exact values are 0.905 and 1.280 (the records are 2 percent below). Cosmetic.
- V2-N3. The committed track A report (O3A-env-preflight-build.md) still cites "at most 0.87" and a 0.12 margin; the lead's one-line erratum (0.935; margin 0.055) is pending, as the fix report says. The old hash f80389bc... appears nowhere else (grep of the olmo3 records folder and the kit): no kit file pins it.
- V2-N4. The input-side cosines are recorded but unused; the fix report's open point 1 (the lead's D-O4 ruling, fixed before the first pod) stands. On the records and the gradient argument I see no case where the input-side cosine would carry a signal, so I have no objection to option (a).

## Unresolved

- As before: the output-side reference on the Instruct checkpoint is a prediction from the Base's 5 Oct read (output rows, cosine 1.000) and OLMo-2's records, not a reading of OLMo 3's weights. If the Instruct's unused output rows are not mutually parallel at 0.99, every candidate reads null and the first pod stops before its job, exactly the family rule's behaviour with no rows; the first pod's `chat_rows` record (per side `comparison_min_pairwise_cosine`, `comparison_rows_parallel`, `rule`, `distinct`) is the first real reading. The fix removed the side the records argue against and kept the side the records argue for; nothing cheaper than the first pod can settle it.

## Log (as it happened)

- 09:40 UTC: scratch folder made; report started.
- 09:42 UTC: step 1 (hashes, worktree state, the scan of every untracked file against the builder trees).
- 09:44 UTC: step 2 (the diffs read hunk by hunk against the fix report).
- 09:46 UTC: step 4 (D2 reproduced under both environments; the count; track C's patch read); the tiny and wrong configs written; the grep for engine tests that read scripts/.
- 09:47-09:48 UTC: step 3 (the fixture numbers), step 5 (sim_d3.py; the first verifier's attacks on both trees), step 6 (scripts/tests under both environments).
- 09:49 UTC: the three direct runs (rule-check tiny, the wrong config, the pod form) with PYTHONPATH; the old script on the same tiny config.
- 09:50 UTC: step 7 (state after); basetemps gone.
- 09:51 UTC: this report finished.
