# O3A-fix1: fix round for track A (the OLMo 3 preflight and its tests)

Builder: the fix-round builder (a Fable 5.1 subagent; the launcher records routing).
Started 2026-11-05 09:27 UTC; finished 09:39 UTC (clock read with `date -u` at 09:27, 09:36, 09:37, 09:37 and 09:39).
Subject: the three defects and nine notes of O3A-verify1.md, in the combined worktree
/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/ws-all (detached at e89d74f; 13 untracked entries before and after, `git diff --stat` empty, no bytecode written into it outside tmp/).
Files in scope: scripts/cuda_preflight_olmo3.py and scripts/tests/ only. Two files changed; three untouched.
Scratch (kept as evidence): /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/fix-O3A/ (read_chat_rows.py, count_recipes.py, simulate_lineage.py, cuda_preflight_olmo3.diff, test_cuda_preflight_olmo3.diff, rule-check-tiny/rule-check.json, tiny/config.json, wrong/config.json). Every pytest basetemp was under scratchpad/o3/tmp/bt-fixA-* and was deleted after its run.

## Status: ALL THREE DEFECTS ADDRESSED (D1 and D3 fixed in the script; D2 is the lead's, reproduced and its fix checked). Notes N2, N3, N5, N6, N8 fixed. Nothing is committed (not authorized).

## Hashes (SHA-256)

| File | Before | After |
|---|---|---|
| scripts/cuda_preflight_olmo3.py | f80389bc5c602cabe9ff83dabfcf7197238c450b6d853851cb7eebec9857b625 (446 lines) | 3f7edd2127a4ee514566b93b1ec30fd8455d8d1c9b7f940ef76770db1f4210a0 (467 lines) |
| scripts/tests/test_cuda_preflight_olmo3.py | 7a45f602d7512f8bdb41c16d192e552339500f12be04e116db93ea761a146112 (297 lines) | 4c5bc46a0afd25ef9191075d35bfdfb90517e6c7f18ac80c45f48b617fca5af4 (368 lines) |
| scripts/tests/conftest.py | c8e33a2604ea48d9a82ae07541551c119d12775625e72b19863b70a6974c8b53 | unchanged |
| scripts/tests/olmo3_tiny.py | a399b2fe1f9f8e070ea3329b62123dfa29f6229425417473e5de3648b61f72cf | unchanged |
| scripts/tests/test_olmo3_engine_tiny.py | 283fc74222eed9c6f5ee3c794bd15d1e0da36faed7afc8341d5120eb4ce497e0 | unchanged |
| scripts/cuda_preflight_family.py (reference, never edited) | b142f3fd5a06ea063356ae4b6cb30e4728a12dc829b4cb99f9ddf795ab4bb569 | unchanged; `cmp` against the main checkout's: byte-equal |

The "before" hashes equal the track A report's table and the untouched copies in ws-a (re-hashed at 09:37). The unified diffs of the two changed files against ws-a's copies are in the scratch folder (73 and 119 changed lines).

The kit's fixture pins `script_sha256`: the new value 3f7edd21... is what the first pod will record. Track C's kit does not hold the hash in a file (the verifier's table, "kit contract": the pin is `equal_keys` in plan_tool.py against the first host's own record), so no kit file changes with it.

## Defects

### D1 (records: the threshold reasoning cited a wrong maximum). FIXED in the docstring.

- Re-checked from the 37 fixture records' `chat_rows` (python -I, numbers only; scratch read_chat_rows.py): Qwen2.5-7B output `<|im_start|>` 0.9353 and `<|im_end|>` 0.9335 (six fixtures); Llama-3.1-8B output 0.7374-0.8684; OLMo-2-7B output 0.4614; OLMo-2-1B output 0.2229; every input side at most 0.0414. The verifier's numbers hold; "at most 0.87" was wrong.
- Changed: module docstring step 2, "Why 0.99": now "at most 0.935 on the output side (Qwen2.5-7B's `<|im_start|>` 0.9353 and `<|im_end|>` 0.9335, the ChatML tokens OLMo 3 also trains; Llama-3.1-8B 0.74-0.87; OLMo-2-7B 0.46; OLMo-2-1B 0.22; every input side at most 0.04)"; the bfloat16 figure now "at most about 1e-5 (measured 1.3e-6 at d = 4096)", the verifier's measurement.
- Not changed (not mine to edit): the committed track A report's "Why 0.99" and rejected alternative 4 in /Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/olmo3/build-round-20261104/O3A-env-preflight-build.md. The correction for the lead's record: the margin below 0.99 is 0.055 (from Qwen2.5-7B), not 0.12; a 0.9 threshold would have refused the Qwen2.5-7B recipe that ran; 0.99 still separates every recorded case.

### D2 (the combined build's engine suite is not green). THE LEAD'S; reproduced, the fix checked, not applied.

- Reproduced in ws-all under both environments: `experiments/safety_selection/tests/test_ss_family_codec.py::test_the_recipe_accepts_the_header_field_and_every_existing_recipe_still_validates` fails at line 161 (`('assistant_header' in {... 'architecture': 'Olmo3ForCausalLM' ...}) is False`); 1 failed in 0.05 s (O3) and 0.04 s (MAIN).
- The file is under experiments/safety_selection/ (hard rule 4; outside this round's two files), so it is not edited here. The fix checked by a scratch count (count_recipes.py) over ws-all's configs: with `"study-kt-olmo3-"` added to the prefix tuple at line 159, 69 family recipes = 59 + 9 + S (Gate B's recipe S exists in ws-all), and no recipe's `assistant_header` or `guard_over_limit` field disagrees with the extended rule. So the lead's edit is two tokens: the tuple `("study-kt-olmo2-", "study-kt-llama3", "study-kt-olmo3-")` at line 159 and `68 + gate_b_s.exists()` at line 165 (with "9 OLMo 3 b/b2e5/b5e5 x mb2/mb1-gc/mb2-g16 (4 Nov)" added to its comment). As the verifier says, the test is outside the 29-file engine identity, so engine X does not move.

### D3 (the input-side reference check would refuse every candidate on the real model). FIXED: the cosine rule decides the output side only.

- The verifier's lineage evidence re-read from the fixture records: OLMo-2 input padding rows at median norm 0.889 (1B, d = 2,048) and 1.263 (7B, d = 4,096), that is 0.02 * sqrt(d) (0.905 and 1.280), the per-element initialisation; `cosine_to_padding_mean` -0.0088 / +0.0286 against `max_cosine_to_padding` +0.0414 / +0.0386 (unequal, so the rows are not mutually parallel); on the output side the two are equal (0.2228 / 0.2229 and 0.4614 / 0.4614: parallel). Llama's reserved and Qwen's padding input rows sit at median norm 0.0000 (no direction; through F.normalize's eps they read non-parallel). No recorded family has a clean input-side reference, and the 5 Oct read of OLMo 3 7B Base is of the output rows only (workplan line 19). An unused input row gets no gradient and keeps its random initialisation, so this is expected, not an accident of OLMo-2.
- The rule as fixed (`chat_rows_report_cosine`; the verifier's option (a)): per side the record now carries `rule` (`SIDE_RULES`: `used_output` "cosine", `used_input` "bit_identity") and `distinct`. The output side must have a clean reference (smallest pairwise cosine of the seven rows at least COSINE_SAME); if not, that side's `distinct` is null, `chat_rows_distinct` is null with the note ("the output comparison rows are not mutually parallel ... no clean unused-row reference on the output side, so the recipe is not used"), and the family `verdict_of` refuses the recipe as before. With a clean output reference, a chat row is distinct on the output side when its largest cosine to any comparison row is at most 0.99. On the input side the family's bit-identity rule decides (no chat row bit-identical to a comparison row), exactly what the family preflight did there; the cosines (`comparison_min_pairwise_cosine`, `comparison_rows_parallel`, `same_way_as_a_comparison_row`, `distance_to_nearest_comparison_row`) and the norms are recorded for reading, not used. `chat_rows_distinct` = both sides' `distinct`. `comparison_rule()` now records `side_rules` and the rule text per side. `bit_identical_rule` is kept on both sides.
- Why option (a) and not the verifier's option (b) (a side without a clean reference excluded, cosine on any side that has one): on the input side a never-seen row can only be at its initialisation, so a parallel input reference would mean a degenerate initialisation (zero or constant rows), where a cosine says nothing either; the adaptive branch would never carry information and would never have run in any recorded family. Option (a) is one rule per side, stated in the record. If the lead wants the cosine rule on the input side whenever its reference is clean, it is a three-line change in `chat_rows_report_cosine` (`if report["comparison_rows_parallel"] or report["rule"] == "cosine"`), before the first pod.
- Decisive check (scratch simulate_lineage.py; the lineage's expected real state at d = 4,096 in bfloat16, as the pod reads the rows): seven unused input rows at N(0, 0.02) (median norm 1.275), seven unused output rows parallel up to bfloat16 rounding (smallest pairwise cosine 0.999999), three trained chat rows (output cosines 0.4601, 0.935, 0.93 as OLMo-2-7B's and Qwen2.5-7B's records; input rows random at a trained norm). Result: input `rule` bit_identity, not parallel (min pairwise -0.032, max cosines 0.017-0.025), `distinct` True; output `rule` cosine, parallel, `distinct` True; `chat_rows_distinct` True, no note. The same state under the old rule reads null (the input side is not parallel). With `<|im_end|>`'s output row laid along the unused rows: False. So the fix removes the refusal path on the expected state and keeps the catch the rule exists for. This is a simulation from the lineage's records, not a measurement on OLMo 3's weights (none on the Mac); the first pod's record is the first real reading.
- The diff pin is untouched: `main` is unchanged, `test_main_is_the_family_main_with_the_comparison_step_replaced` still passes with the same nine lines.

## Notes

- N2 (the test compared the family file with itself): FIXED. Line 212 now asserts `Path(o3.pf.__file__).resolve() == FAMILY`: the family module the script imported is the sibling file, not another copy on sys.path. The byte-equality with the main checkout's family preflight was re-done by `cmp` here (equal).
- N3 (the `--rule-check` form made the out folder before the architecture refusal): FIXED. `create_run_dir` now runs after the config check; the test asserts `not (tmp_path / "wrong-out").exists()`; a direct run with an Olmo2Config refused with exit 2 and made no folder. Docstring step 3 now says "(or, in the second form, a config)".
- N5 (a constant change after the first pod needs a new fixture): FIXED in the docstring: "fixed here before the first pod: the kit's fixture pins this file's `script_sha256`, so a later change of the rule or its constant needs a new fixture".
- N6 (an opposite row reads distinct): stated in the docstring ("an opposite row, cosine -1, reads distinct"); the rule is unchanged (largest cosine).
- N8 ("the chat rows" should say "the output rows"): FIXED in the docstring, with the workplan line number.
- N1 (the 1,114 double-count), N4 (F.normalize's eps on tiny norms), N7 (the float32 edge), N9 (the kit needs Python 3.10+): records or other tracks; nothing to change in these two files. N4 is now part of the D3 reasoning in the docstring (rows at norm 0.0 have no direction).

## Tests (scripts/tests/test_cuda_preflight_olmo3.py)

Changed: the module docstring; `test_the_cosine_rule_passes_distinct_rows_and_records_the_family_rule` (asserts `SIDE_RULES`, `comparison_rule()["side_rules"]`, per-side `rule` and `distinct`); `test_a_parallel_chat_row_fails_although_it_is_not_bit_identical` (adds the same parallel row on the input side: True, `same_way_as_a_comparison_row` recorded True, and the bit-identical input row: False with `used_input.distinct` False); `test_the_edges_of_the_chat_row_rule` (per-side cosines, `used_input.distinct` True); `test_the_edges_of_the_reference_rule` (both sides' parallelism, the output side's `distinct`); new `test_only_the_output_side_needs_a_clean_reference` (random input rows with parallel output rows: True, no note; input rows at norm 1e-21 and 0: True; a tied output row with random input rows: False; parallel input with random output rows: null with the output-side note); `test_random_or_zero_comparison_rows_give_null` (the input side reads bit identity); the N2 line; the `--rule-check` test (per-side fields in rule-check.json, `side_rules`, the N3 assertion); `test_the_rule_on_the_tiny_models_real_rows` (random: null; output rows made parallel with the input left random: True; `<|im_end|>`'s output row along them: False; restored; input rows made parallel and `<|im_start|>`'s input row along them: True, recorded; bit-identical: False).

## Commands run (with exit codes)

All Python with `-B` and PYTHONDONTWRITEBYTECODE=1, HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 where a library loads; pytest `-q -p no:cacheprovider --basetemp=<scratchpad>/o3/tmp/bt-fixA-*` (deleted after each run); cwd = ws-all. O3 = /Users/spiderishi/Coding/attribution/tmp/olmo3-venv/bin/python (transformers 4.57.1, peft 0.17.1, torch 2.8.0); MAIN = /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python (transformers 4.56.2). No network, no install, no pod, no git state change, no edit outside the two files; nothing under a forbidden path opened (the only tmp/ files read: the 37 tmp/family-probe-*/expected-fixture-probe.json records, `chat_rows` keys and numbers only, with python -I; the cached OLMo 3 tokenizer and config.json).

| Step | Command | Result |
|---|---|---|
| 0 | Read of the verifier's report, the script, the four test files, the track A report, the family's `comparison_rows`, `chat_rows_report`, `stop_verdict`, `verdict_of`, the engine's `token_row_report`, CM D-O4, workplan line 19, test_ss_family_codec.py:150-166; shasum of the six files; `git status --short`, `git log -1` | exit 0; hashes equal the track A table |
| 1 | O3 `-I` read_chat_rows.py (37 fixture records, chat_rows numbers) | exit 0; the numbers above (D1, D3 confirmed) |
| 1 | O3 and MAIN pytest of the one D2 test in ws-all | 1 failed each (line 161); basetemps deleted |
| 1 | O3 `-I` count_recipes.py | 69 = 59 + 9 + S; no field disagrees; exit 0 |
| 2-3 | Edits to the two files (Edit tool) | - |
| 4 | O3 `pytest scripts/tests` | 30 passed in 9.75 s; exit 0 |
| 4 | MAIN `pytest -rs scripts/tests` | 20 passed, 3 skipped ("transformers has no olmo3 model code") in 5.59 s; exit 0 |
| 4 | O3 `scripts/cuda_preflight_olmo3.py --rule-check` on the scratch tiny config and the cached snapshot with the OLMo 3 codec flags | exit 0; rule-check.json: Olmo3ForCausalLM, extra_id x7, `side_rules` recorded, input rule bit_identity (min pairwise -0.3593, not parallel, `distinct` True, max cosines 0.049-0.391), output rule cosine (min pairwise -0.2847, not parallel, `distinct` null), `chat_rows_distinct` null with the output-side note; `script_sha256` 3f7edd21..., `family_script_sha256` b142f3fd... |
| 4 | O3 the same with an Olmo2Config | exit 2, the fixed message, no out folder (N3) |
| 4 | O3 simulate_lineage.py (d = 4,096, bfloat16) | `chat_rows_distinct` True; null under the old rule; False with a tied output row; exit 0 |
| 5 | shasum after; `git status --short` (13 entries), `git diff --stat` (empty); find for bytecode outside tmp/ (none); `cmp` of the family preflight against the main checkout's (equal); `diff -u` of the two files against ws-a's copies | exit 0 |

## Acceptance criteria

- Every defect fixed or shown wrong with a check: D1 FIXED (docstring; the committed report's correction stated for the lead); D3 FIXED (the rule; the decisive simulation; the tests); D2 NOT MINE (reproduced; the lead's two-token fix checked by count).
- Notes addressed where cheap: N2, N3, N5, N6, N8 FIXED; N1, N4, N7, N9 nothing to change here.
- Affected tests re-run under both environments: PASSED (30 under 4.57.1; 20 + 3 skipped under 4.56.2).
- Hard rules: no forbidden path opened, no network, no install, no pod, no git state change, no edit of the main checkout, the engine, the family preflight or any frozen record; every command foreground and under 10 minutes (the longest 9.75 s); basetemps deleted.

## Open points for the lead

1. **D-O4 is still the lead's ruling.** The rule as fixed: cosine on the output side (clean reference required, else null), bit identity on the input side (cosines recorded). The alternative (the cosine rule also on the input side whenever its reference is clean) is a three-line change; neither the records nor the gradient argument give it a case where it would carry information. Whichever is chosen must be fixed before the first pod (the fixture pins `script_sha256`, now 3f7edd21...).
2. **D2 is a test edit under experiments/safety_selection/tests/** (two tokens at lines 159 and 165), to be committed by explicit path together with track C's nine recipes; outside this round's scope and the never-edit rule.
3. **The committed track A report** (O3A-env-preflight-build.md) still says "at most 0.87" and "0.12 above"; the correct margin is 0.055 (Qwen2.5-7B). A one-line erratum in the lead's record is enough; the script's docstring is now right.
4. **The first pod is the first real reading** of OLMo 3's rows. The record will show, per side, `comparison_min_pairwise_cosine`, `comparison_rows_parallel`, `rule`, `distinct` and each chat row's `max_cosine_to_padding`, `norm` and `bit_identical_to_a_padding_row`; the expected shape is the simulation's (input not parallel at norm about 1.28; output parallel; chat output rows well below 0.99).

## Log (as it happened)

- 09:27 UTC: report started; hashes before taken.
- 09:30 UTC: step 1 done. D1 and D3 re-checked from the 37 fixture records' chat_rows (python -I, numbers only). The verifier's numbers hold.
- 09:31 UTC: D2 reproduced in ws-all under both environments; the proposed fix's count checked (69).
- 09:33 UTC: step 2, the script edited (the rule, the docstring, the rule-check folder order).
- 09:35 UTC: step 3, the tests edited (one new test; eight changed).
- 09:36 UTC: step 4, scripts/tests under O3 (30 passed) and MAIN (20 passed, 3 skipped); the rule-check form run directly (exit 0; the wrong config exit 2 with no folder).
- 09:37 UTC: hashes after; worktree state unchanged apart from the two files (13 untracked entries, no diff, no bytecode); the family preflight byte-equal to the main checkout's; diffs against ws-a written; the lineage simulation run (True; null under the old rule; False with a tied output row).
- 09:39 UTC: this report finished.
