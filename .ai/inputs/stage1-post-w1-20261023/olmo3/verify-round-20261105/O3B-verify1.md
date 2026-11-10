# O3B verify 1: adversarial check of track B (data config, codec, prepared set, draft pre-run record)

Started 2026-11-05 09:03 UTC. Verifier: an independent worker (model identity is recorded by the launcher, not here).
Scratch: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/verify-O3B/
Combined worktree under check: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/ws-all (expected at e89d74f)

Status: DONE 2026-11-05 09:15 UTC. Verdict: **defects** (one cross-track defect D1; track B's own files verified). See the Verdict section at the end.

## Plan
1. Read O3B-data-build.md, O3B-input-choices-and-predictions-DRAFT.md, the readiness scout, O3A addendum (+ MC, CM), FOCUS OLMo 3 lines, olmo3 records.
2. Data config diff vs the OLMo-2 data config, re-derived.
3. Chat-template blob hash vs cached chat_template.jinja.
4. Engine config checks on the data config.
5. Re-run scripts/family_codec_check.py with the stated end, stops, pad, header.
6. Prepared set: hashes, manifest key reads, rows per unit, token audit, built from this exact config.
7. Draft pre-run record vs O3A lines it cites, word for word.
8. Verdict.

## Steps done

### Step 1 (09:03-09:11 UTC; clock read 09:03:20 at the start, 09:11:02 before step 6b): sources read
Read: O3B-data-build.md, O3B-input-choices-and-predictions-DRAFT.md (committed copies), B-olmo3-readiness.md sections 0-2, O3A lines 175-220, 280-320, 380-415, CM lines 80-125 and 190-212, FOCUS lines 76-78 (4 Nov) and 97-98 (1 Nov 09:45, 09:20), the olmo3 records (receipt, env smoke, user yes build, user yes restore, lock). ws-all is at e89d74f with 42 untracked files (the three tracks'), no tracked file edited (git status --short shows only `??` lines).

### Step 3 (09:03-09:11 UTC): the chat-template blob (PASS)
`shasum -a 256` and `git hash-object` on `~/.cache/huggingface/hub/models--allenai--Olmo-3-7B-Instruct/snapshots/6e5971d9eba42665f5bd5a0fcf047f299ce1dccc/chat_template.jinja`: SHA-256 `f5186d42d99c8a0445d37fd8a6c7ccf07fe3e24a29ce622d8bd245da9507b12b`, blob `a21396285102846aa0787dd598623e7b8dbb2b67`. Both equal the amendment text in `study-kt-data-dolly-olmo3.json` and the receipt. The other six files' SHA-256 and blob ids also equal the receipt (checked all seven).

### Step 2 (09:03-09:11 UTC): the data config diff, re-derived (PASS)
Scratch `verify-O3B/diff_configs.py` (recursive key diff, run with `-I`). `study-kt-data-dolly-olmo3.json`: 5,703 B, SHA-256 `fa41873d3411d43bf638d46c6409a5502c28503ab35d3ee5a35dcf9867332f6a` (as the report). Differences from `study-kt-data-dolly-olmo2.json`, exactly six paths: `/name`, `/purpose`, `/amendments` (the OLMo-2 text kept byte for byte as item 0, one 2026-11-04 item added), `/eligibility/forbidden_substrings` (the OLMo-2 five plus `<function`, `</function`, in that order), `/tokenizer/repo_id`, `/tokenizer/revision`. Key order identical. `exclude_lines`, `construction_sha256`, `retokenize`, `banks_from`, `source`, `units`, `seed_namespaces`, `end_of_turn_token`, limits: unchanged. Against the base `study-kt-data-dolly.json` the diff is exactly what the engine's family-config test expects with extra `["<|", "|||", "<function", "</function"]`.

### Step 4 (09:03-09:11 UTC): the engine's own config checks (PASS)
Scratch `verify-O3B/engine_checks.py`: `load_data_config` accepts the file under `tmp/olmo3-venv` (transformers 4.57.1) and under the main venv (4.56.2), exit 0 both. The assertions of `test_ss_family_recipes.py::test_each_family_data_config_is_the_dolly_config_with_only_the_listed_fields_changed` re-run for `olmo3` with the four extras: PASS in both environments. Negative control: a copy with a bad revision raises `ConfigError` (so the validator does check). No `__pycache__` written under ws-all.

### Step 5 (09:03-09:11 UTC): `scripts/family_codec_check.py` re-run (PASS, with `--dolly` this time)
Command (ws-all, `tmp/olmo3-venv`, offline, exit 0; output `verify-O3B/codec-check-olmo3-dolly-tf4571.json`): `--tokenizer <cache snapshot 6e5971d9…> --end '<|endoftext|>' --stop '<|endoftext|>' --stop '<|im_end|>' --pad '<|pad|>' --header '<|im_start|>assistant\n' --dolly tmp/kt-sources/kill-test/databricks-dolly-15k.jsonl`.
Result equals the report on every field it gives: `own_template_reads_clock` false, `clean_up_tokenization_spaces_in_config` false, eos 100257, stops [100257, 100265], pad 100277, `all_special_ids` 2, `added_special` 8, `special_ids` 8, `unk_token_id` 100257, suffix `<|im_start|>assistant\n`, `header_check` passed, chat tokens 100257/100264/100265, `template_tokens_one_turn` 37, `prompt_tokens_empty_user` 36, 0 decode round-trip failures.
The Dolly pass the builder could not run (the source was restored by the lead on 4 Nov): 15,011 rows; 15 over the row limit; 36 over the prompt limit; `control_or_empty` []; `separate_not_joint` []; 0 response round-trip failures. Lines 10024 and 12405 (the `exclude_lines`) are in neither over-limit list, consistent with the amendment ("this tokenizer would keep" them) and with the engine's refusal rule at `prepare_task.py:309` not firing.

### Step 6a (09:03-09:11 UTC): the prepared set by hash and by key (PASS so far)
- `tmp/kt-prepared/prepared-kt-dolly-olmo3/manifest.json`: SHA-256 `8a196f6d17888d6f4b2f466cdf63cb944315b135ac761fb22876ebb43c125239` = `manifest.sha256`.
- `auditor/construction.json`: `2f5802f5896915b4edb813ca2aa7bf1983d0eb5bd9fa7062da3055f3b84f483d` = OLMo-2's = `prepared-kt-dolly`'s = the config's `expected.construction_sha256`.
- `engine/groups.json` `ab055eb8…` byte-equal to OLMo-2's (the same units). `banks/selector.jsonl` `ea89b9f2…` and `hidden/hidden.jsonl` `0fb47595…` byte-equal to the v3 source and to the config's `banks_from.files` (hashes only; never opened). `banks/dev.jsonl` differs (retokenized, `a248ac50…`), 657 lines. `train_rows.jsonl` 4,800 lines, `query_rows.jsonl` 200.
- Manifest by key (scratch `verify-O3B/manifest_keys.py`, prints no row text): `rows_per_unit` 600; 8 units × 600 rows; `corpus` rows 4,800, queries 200; `token_audit.pairs` n 5,000, max 2,139, over_2048 1, `separate_vs_joint_encoding_mismatches` 0, `mismatched_ids` []; `bank_import.largest_prompt_tokens` 345 (OLMo-2: 320); `tokenizer` repo/revision/blobs equal the receipt. Key-by-key diff against OLMo-2's manifest: only the data-config fields that step 2 lists, `data_config_sha256`, the tokenizer blobs, the token statistics and the four re-encoded files differ. Nothing else.
- Cross-check of the builder's proxy: per-unit token sums (OLMo 3 minus OLMo-2) total 118,966 over 4,800 rows; with a rows at +24 and b at +25, a+b=4,800 gives a=1,034, b=3,766, the report's numbers exactly; the 200 query rows (47/153) give 4,953, and 118,966+4,953 = 123,919 = 5,000 × (233.2092−208.4254). So the proxy's counts are the manifest's.
- `prepare_receipt.json`: code identity `472fc7f6…` (engine X, 29 files), inputs the restored Dolly and v3 paths, 2026-11-04T13:26:56 UTC.

### Step 6b (09:11:02-09:12:09 UTC): the prepared set rebuilt from this exact config, both environments (PASS)
`python -B -m experiments.safety_selection prepare-task --data-config experiments/safety_selection/configs/study-kt-data-dolly-olmo3.json --sources-root tmp/kt-sources/kill-test --banks-from tmp/v3-prepared/prepared-v3-inj05 --out <scratch>` from ws-all, offline, once under the main venv (transformers 4.56.2; 34 s; exit 0) and once under `tmp/olmo3-venv` (4.57.1; 33 s; exit 0). Both print `manifest_sha256` `8a196f6d17888d6f4b2f466cdf63cb944315b135ac761fb22876ebb43c125239`, equal to the placed set's; every one of the eight data files hashes equal to the placed set's (construction `2f5802f5…`, dev `a248ac50…`, selector `ea89b9f2…`, groups `ab055eb8…`, query `74a01059…`, train `7f5e8005…`, hidden `0fb47595…`, x0 `469af894…`). So the build is deterministic, the two transformers versions tokenize identically, and the FOCUS 13:28 claim ("both give manifest 8a196f6d…") is reproduced. Both scratch copies were deleted right after hashing (they held the never-open banks).
"Built from this exact data config": `manifest["data_config"] == json.load(ws-all/…/study-kt-data-dolly-olmo3.json)` is True, and `manifest["data_config_sha256"]` `672c6aa0…` equals `config_sha256(file)` (the engine's canonical-JSON hash, `config.py:643`; the file-bytes hash `fa41873d…` is a different quantity, as expected).

### Step 6c (before 09:13 UTC): the forbidden strings and the dev bank, by key (PASS)
`bank_import`: `retokenized` [`banks/dev.jsonl`], `not_audited` [selector, hidden], `forbidden_substring_items` {} (no dev item holds any forbidden string, the two new ones included), `token_hash_changed_items` 657 (all dev items, as the tokenizer changed), `largest_prompt_tokens` 345, `source_manifest_sha256` `bd1e40df…`. `eligibility.by_category.excluded_by_reason` has no forbidden-substring reason in any category; `excluded_line` 1 in closed_qa and 1 in information_extraction (= the two `exclude_lines`); `expected_counts` "matched". Dolly line counts holding `<function`, `</function`, `<functions>`, `<|extra_id`: 0, 0, 0, 0 (counts only). So D-O6 changes no row, as the amendment and CM:95 state.
Recipe/data agreement (scratch `verify-O3B/embedded_config.py`): all nine `study-kt-olmo3-7b-*-20261104.json` recipes load, and each agrees with the data config on (repo_id, revision, end_of_turn_token, max_train_tokens, max_prompt_tokens), with stops `['<|endoftext|>', '<|im_end|>']`, pad `<|pad|>`, header `'<|im_start|>assistant\n'`, no `model.tokenizer` field. `jobs.py:241-244` compares exactly (repo_id, revision, end_of_turn_token), so no job refusal against this data config.

### Step 6d (before 09:11 UTC): the engine's three test files in the COMBINED worktree (ONE FAILURE; see defect D1)
Same command as the builder's step 5 (main venv, `-p no:cacheprovider`, fresh basetemp, deleted after): `test_ss_family_recipes.py`, `test_ss_family_codec.py`, `test_ss_kt_data.py` in ws-all: **1 failed, 109 passed in 4.99 s** (the builder reported 110 passed in ws-b, which held only the data config). The failure is `test_ss_family_codec.py::test_the_recipe_accepts_the_header_field_and_every_existing_recipe_still_validates`, line 161.

### Step 7 (09:13 UTC): the draft pre-run record against the lines it cites
Checked every citation of `O3B-input-choices-and-predictions-DRAFT.md` (committed copy SHA-256 `294a5f6e…`, byte-equal to the scratch copy) against the printed lines of O3A, CM and FOCUS:
- Line 3, FOCUS 09:20 quote "The input choices and the pre-set answers P0–P4 are the lead's: the draft's recommended answers, recorded before the first fine-tune." — word for word at FOCUS:98. "Yes, build it" — word for word in `user_yes_build_olmo3_20261103.json`.
- Line 17: model and revision (O3A:183) exact; "transformers 4.57.1" is the lock's value (O3A:185 says 4.57.x; the lock file pins 4.57.1): consistent.
- IC-1: "Keep the template's default system block in every prompt" — word for word at O3A:187; CM:203 D-O1 recommended; the system-block text equals CM:94 and the cached template's literal; "Stripping it is an engine change" at O3A:187; CM:210 D-O8 recommended "add nothing". The one-turn wrapper 37/36 equals my codec re-run; "OLMo-2's was 11" is CM 2.4's figure (not CODEC's; see note N2).
- IC-2: values at O3A:187 exact; CM:204 D-O2 recommended, and its known limit quoted in substance; the template's final assistant turn ends with `eos_token` (checked in the cached jinja: `{%- else -%}{{- eos_token -}}`), earlier turns with `<|im_end|>` + newline; the stop-reason report at O3A:187 and CM:197 (check 4). The unk-token statement is at CM:92, not CM:91 (a blank line): note N1.
- D-O6 paragraph: CM:208, O3A:186, CM:95 exact.
- Section 2 reason and framing: O3A:211 word for word in substance ("costs a day or more", "about 7 days", "change no bar", the five F lines, "P1 and P3 apply earlier user acceptances; two of the rules applied were recorded as loosenings (F L140, L318)", "discloses each use, as for Llama"). P0 = O3A:212 (F L314, "at most one per rung", "$4–5 each"). P1 = O3A:213 in every clause, including the [V] rung-3 case and the low-edge recommendation "accept, with the disclosure 'at the low edge'" and its reason (F L101). P2 = O3A:214. P3 = O3A:215 (decision 25; ARC d ≤ 0.03 and task learned, F L140). P4 = O3A:216 ("review, not adjustment", F L291). Rung steps R1–R5 = O3A:196-204; the other-bars paragraph = O3A:206 (definite FAIL → L1 via P4 without the remaining seeds; TOO CLOSE → P3's kinds; other → the user).
- Predictions: every range, point and basis phrase equals O3A:310-313; "proposed values for the lead to edit" is O3A:309's wording; lead item 8 at O3A:409 says "By 31 Oct. The predictions of §16.9". User items at O3A:392 (input choices) and O3A:393 (P1–P4 plus P0 and the low-edge case) cited correctly.
- Section 4: C1 on the live balance = FOCUS:98 and O3A:283, 287; "level 0 at 13 Nov 23:59 UTC" = FOCUS:98. The record authorizes no spend and changes no bar: consistent with the money rules and O3A:211.
No misquotation found. One citation is off by one line (N1).

## Defects

### D1 (cross-track; not in track B's files; matters for the records and the merge): the engine's own suite fails in the combined worktree
- **What:** `experiments/safety_selection/tests/test_ss_family_codec.py::test_the_recipe_accepts_the_header_field_and_every_existing_recipe_still_validates` iterates every `configs/*.json` of kind `safety-selection recipe` and asserts, at line 161, that `assistant_header` is present **only** in recipes whose file name starts with `study-kt-olmo2-` or `study-kt-llama3` (the "family prefix" tuple at line 159), then at line 165 that the family count is `59 + gate_b_s.exists()`. Track C's nine `study-kt-olmo3-7b-*-20261104.json` recipes carry `assistant_header` (they must; the data config's amendment and CM:89 require it) but do not match the prefix tuple, so the assertion fails on the first of them.
- **Reproduction:** in ws-all (e89d74f + the 42 files), `PYTHONDONTWRITEBYTECODE=1 <main venv>/python -B -m pytest -q -p no:cacheprovider --basetemp=<fresh> experiments/safety_selection/tests/test_ss_family_codec.py::test_the_recipe_accepts_the_header_field_and_every_existing_recipe_still_validates`. Expected (the builders' reports): pass. Actual: `AssertionError: assert ('assistant_header' in {'architecture': 'Olmo3ForCausalLM', 'assistant_header': '<|im_start|>assistant\n', …}) is False`, 1 failed in 0.04 s. The three-file run gives 1 failed, 109 passed.
- **Why no builder saw it:** track B ran the three files in ws-b (data config only: 110 passed, true there); track C ran `test_ss_family_recipes.py` and `test_ss_probe_runkit.py` only (181 passed); track A ran the whole suite in ws-a (no recipes: 1,114 passed). Nobody ran `test_ss_family_codec.py` with the recipes present. The data config is not the cause: its kind is `safety-selection task data config`, which the loop skips.
- **Why it matters:** FOCUS 4 Nov 11:18 plans "merge, the lead's suites"; after the merge the engine's suite fails, and the fix is an edit of an engine test file (two lines: the prefix tuple at :159 and the count at :165, since adding `study-kt-olmo3-` to the tuple makes the count 68 + S) — an edit O3A:300-304 and the pack rule constrain until Gate B's last kit pod, or by explicit-path commit when no pack is in progress — or the recipes stay outside `experiments/` as drafts (O3A:302), which changes track C's kit paths. This is the lead's ruling to make; it is not a track B fix. It does not touch the probe's correctness (the test is bookkeeping over config files), the frozen rules or the money rules.

## Notes (minor; no action needed for correctness)
- N1. The draft record's IC-2 cites "CM:91" for "`<|endoftext|>` is also the unknown token … the case the engine already allows for OLMo-2"; CM:91 is blank, the statement is CM:92 (the `single_token_id` bullet). A one-character fix at commit time.
- N2. The draft record's IC-1 labels "OLMo-2's was 11" as "Measured (CODEC)"; the 11 comes from CM 2.4 (the 17 Oct estimate), not from the 4 Nov codec check, which was run on OLMo 3 only. The number is not in doubt; the label is.
- N3. The builder's step 1 could not run the codec check's `--dolly` pass (the source was off the Mac). It can now, and passes (step 5 above: 15 rows over the row limit, 36 over the prompt limit, 0 control/empty, 0 separate-vs-joint, 0 round-trip failures). The lead may add it to the records; the prepared set's construction equality already proves the unit result.
- N4. The committed copy of `O3B-data-build.md` still reads "step 3 … not done" and open point 1 "needs two inputs restored"; both are overtaken by the lead's 4 Nov 13:26 UTC build (FOCUS 13:28), which this report reproduces bit for bit. The copy is a point-in-time record; no edit needed, but a reader should pair it with the FOCUS entry.
- N5. P1's low-edge case: O3A:213 said "the user decides it explicitly"; the record adopts the draft's recommendation under the lead's 1 Nov 09:20 ruling that P0–P4 are "the draft's recommended answers". The ruling's wording covers it, and the record says so at its line 3 and §2. Stated here so the lead commits it knowingly.
- N6. The O3B report's open point 3 (the `test_ss_family_recipes.py:102` parametrization does not cover `olmo3`) stands; D1 is a second, failing, test in the same situation. Whatever the lead rules for one applies to both.

## Verdict
**defects** (one, D1, cross-track). Track B's own deliverables are correct on every check this report ran: the data config differs from OLMo-2's in exactly the listed fields and passes the engine's validator and the family-config assertions in both environments; the pinned template blob equals the cache (SHA-256 and git blob); the codec check reproduces, now with the Dolly pass; the prepared set's manifest `8a196f6d…` and construction `2f5802f5…` hold, the set embeds this exact config, and a rebuild from the same command reproduces every file bit for bit under 4.56.2 and 4.57.1; the draft record quotes O3A, CM and FOCUS faithfully. The one defect is that the engine's `test_ss_family_codec.py` fails once the three tracks' files sit together, which no builder ran, and whose fix needs the lead's ruling (an engine test edit under the pack rule, or recipe placement).

## Commands run (all foreground; longest 34 s)
1. `shasum -a 256` and `git hash-object` on the seven cached OLMo 3 files (exit 0).
2. `verify-O3B/diff_configs.py` under `tmp/olmo3-venv` with `-I` (exit 0).
3. `verify-O3B/engine_checks.py` under both venvs (exit 0, 0).
4. `scripts/family_codec_check.py … --dolly …` under `tmp/olmo3-venv`, offline (exit 0; output `verify-O3B/codec-check-olmo3-dolly-tf4571.json`).
5. `verify-O3B/manifest_keys.py`, `verify-O3B/bank_keys.py` (key reads; exit 0; the shell's `grep -c` exit 1 = zero matches).
6. `shasum -a 256` over the prepared sets' files, the v3 source banks and Dolly (hashes only).
7. pytest on the three test files in ws-all, main venv, fresh basetemp (exit 1: 1 failed, 109 passed); the single failing test with `--tb=long` (exit 1); basetemps deleted.
8. `verify-O3B/embedded_config.py` under `tmp/olmo3-venv` (exit 0).
9. `prepare-task` rebuilds under the main venv and under `tmp/olmo3-venv` into scratch (exit 0, 0); outputs hashed and deleted.
Nothing written outside `verify-O3B/` and this report; ws-all, the main checkout, the engine, the kits and every record untouched; no git state changed; no network.

## Scratch files kept (evidence)
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/verify-O3B/`: `diff_configs.py`, `engine_checks.py`, `manifest_keys.py`, `bank_keys.py`, `embedded_config.py`, `codec-check-olmo3-dolly-tf4571.json`.
