# O3B-data build report (track B: blocker B2's rest and the lead's pre-run records)

Builder: a bounded Fable worker for the main-study lead (GI IX). Worktree `ws-b` (detached copy of the working branch at `5b5b07e`). Started 2026-11-04 (UTC; clock checked with `date -u` at each step below).

Status line (updated after every step): **done (2026-11-04 11:00 UTC): steps 1, 2 and 4 done; step 3's real build is blocked (both inputs are off this Mac; rule 2 forbids fetching them), its $0 proxy passed; step 5 (this report) done. Nothing committed (rule 3).**

If this run is cut off, continue from the first step marked "not started" or "in progress" below. Every command run is listed with its exit code.

## 0. Plan

| Step | What | State |
|---|---|---|
| 1 | Codec check: `scripts/family_codec_check.py` with OLMo 3's cached tokenizer under `tmp/olmo3-venv` (end `<\|endoftext\|>`, stops `<\|endoftext\|>` and `<\|im_end\|>`, pad `<\|pad\|>`, header `<\|im_start\|>assistant\n`), with `--dolly` | done (passed; `--dolly` not possible, see step 3) |
| 2 | Data config `experiments/safety_selection/configs/study-kt-data-dolly-olmo3.json` (the OLMo-2 config plus `<function`, `</function` forbidden; default system block kept; end `<\|endoftext\|>` with both stops; the jinja blob in the amendment text) | done |
| 3 | Prepared set `prepared-kt-dolly-olmo3` built with the engine's prepare command into `scratchpad/o3/tmp/prepared-kt-dolly-olmo3`; `construction_sha256` must equal `2f5802f5…`; report the manifest SHA-256, rows and tokens | blocked (inputs missing); proxy passed |
| 4 | Draft record `O3B-input-choices-and-predictions-DRAFT.md` (input choices, P0-P4, predictions, each with its source line) | done |
| 5 | Final report: files with SHA-256, design, rejected alternatives, commands, open points | done |

## 1. Sources read (paths absolute)

- Scout: `/Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/next-stages/B-olmo3-readiness.md` sections 1-2 (B2 at 2.2).
- O3A: `/Users/spiderishi/Coding/attribution/research/review/2026-10-17-olmo3-7b/olmo3-7b-addendum.md` lines 180-215 (16.1-16.2a), 300-320 (16.9), 380-415 (decisions).
- CM: `/Users/spiderishi/Coding/attribution/research/review/2026-10-17-olmo3-7b/compat-memory.md` lines 90-125 (2.2-2.4), 190-210 (checks, D-O1 to D-O8).
- FOCUS entries of 1 Nov 09:20 and 09:45 UTC (lines 94 and 93 of `research/FOCUS.md` in the main checkout at the time of reading).
- Records in `/Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/olmo3/`: `tokenizer-receipt-olmo3.json` (snapshot `~/.cache/huggingface/hub/models--allenai--Olmo-3-7B-Instruct/snapshots/6e5971d9eba42665f5bd5a0fcf047f299ce1dccc`; `chat_template.jinja` blob `a21396285102846aa0787dd598623e7b8dbb2b67`, SHA-256 `f5186d42…`), `env-smoke-20261101.json` (transformers 4.57.1; `Olmo3ForCausalLM` not a subclass of `Olmo2ForCausalLM`; tokenizer `GPT2TokenizerFast`, 100,278 tokens, pad `<|pad|>`, eos = bos `<|endoftext|>`, im_start 100264, im_end 100265).
- The OLMo-2 and Llama-3 data configs under `experiments/safety_selection/configs/`.

## 2. Step log

### Step 1: the codec check (done, 2026-11-04 10:52 UTC)

Command (from `ws-b`, exit 0; output saved at `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/tmp/codec-check-olmo3.json`):

```
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
/Users/spiderishi/Coding/attribution/tmp/olmo3-venv/bin/python -B scripts/family_codec_check.py \
  --tokenizer ~/.cache/huggingface/hub/models--allenai--Olmo-3-7B-Instruct/snapshots/6e5971d9eba42665f5bd5a0fcf047f299ce1dccc \
  --end '<|endoftext|>' --stop '<|endoftext|>' --stop '<|im_end|>' --pad '<|pad|>' --header '<|im_start|>assistant\n'
```

Result: `own_template_reads_clock` false; `clean_up_tokenization_spaces_in_config` false; eos 100257; stops [100257, 100265]; pad 100277; `all_special_ids` 2, `added_special` 8, `special_ids` 8; `unk_token_id` 100257 (= eos, the case the engine allows for OLMo-2); `generation_suffix` `<|im_start|>assistant\n`; **`header_check` passed**; chat tokens `<|endoftext|>` 100257, `<|im_start|>` 100264, `<|im_end|>` 100265; `template_tokens_one_turn` 37; `prompt_tokens_empty_user` 36; `decode_round_trip_failures` 0.

`--dolly` could not be given: the Dolly source is not on this Mac (step 3). The check's Dolly pass (rows over a limit, separate-vs-joint, response round trip) is therefore not run; the proxy of step 3 covers the 5,000 prepared rows instead.

Comparison with the 17 Oct estimate (CM 2.4): the wrapper was estimated at 35 tokens from the OLMo-2-1B proxy; measured now 37 per turn (36 for an empty user turn, so one more token per row than the estimate's +23/24 delta; see step 3's measured deltas).

### Step 2: the data config (done, 2026-11-04 10:56 UTC)

File: `ws-b/experiments/safety_selection/configs/study-kt-data-dolly-olmo3.json` (5,703 B, SHA-256 `fa41873d3411d43bf638d46c6409a5502c28503ab35d3ee5a35dcf9867332f6a`). Written by the scratch generator `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/tmp/make_olmo3_data_config.py` (exclusive create; exit 0 under the main environment; the written file re-validated under `tmp/olmo3-venv`, exit 0).

Content: the OLMo-2 config with these changes only: `name`; `purpose`; `amendments` (the inherited 2026-10-08 text, then a 2026-11-04 amendment that pins the jinja blob `a21396285102846aa0787dd598623e7b8dbb2b67` / SHA-256 `f5186d42…`, states the two input choices (default system block kept; end of turn `<|endoftext|>`), names the recipe's stops, pad and header, and explains the two new forbidden strings); `eligibility.forbidden_substrings` = the base list + `<|`, `|||`, `<function`, `</function`; `tokenizer` = `allenai/Olmo-3-7B-Instruct` at `6e5971d9…`, end of turn `<|endoftext|>`, limits 3,072 / 1,536 unchanged. `exclude_lines` [10024, 12405], `construction_sha256` `2f5802f5…` and `retokenize` [`banks/dev.jsonl`] are the OLMo-2 config's.

Checks run by the generator (all passed): `load_data_config` validates it; undoing name, purpose, amendments, tokenizer, the extra forbidden strings, `exclude_lines`, `construction_sha256` and `retokenize` gives `study-kt-data-dolly.json` back (the engine's own test for the OLMo-2 and Llama-3 configs, `test_ss_family_recipes.py:102-118`); and undoing name, purpose, amendments, tokenizer and the forbidden list gives the OLMo-2 config back.

Not done, by rule 4: the engine's parametrized test is not extended with `("olmo3", ["<|", "|||", "<function", "</function"])`; that is a one-line edit of `experiments/safety_selection/tests/test_ss_family_recipes.py:102` for the lead.

Note for track C: the data config holds only the end-of-turn token (`config.py:374-378`); stops, pad and the assistant header are recipe fields (`model.stop_tokens`, `model.pad_token`, `model.assistant_header`; `config.py:484-514`). A job refuses a recipe whose (repo, revision, end token) differs from the data config's.

### Step 3: the prepared set (blocked; proxy run instead)

**Blocked.** The engine's command is `python -m experiments.safety_selection prepare-task --data-config CONFIG --sources-root ROOT --banks-from PREPARED_V3 --out OUT` (`__main__.py:55-61`, `:198-217`). It needs two local inputs that the OLMo-2 set's receipt names (`tmp/kt-prepared/prepared-kt-dolly-olmo2/prepare_receipt.json`): the Dolly source `tmp/kt-sources/kill-test/databricks-dolly-15k.jsonl` (13,085,339 B, SHA-256 `2df90833…`) and the bank source `tmp/v3-prepared/prepared-v3-inj05/` (manifest SHA-256 `bd1e40df…`). Neither exists on this Mac any more (`ls` at 10:52 UTC: "No such file or directory" for both; a name search over the home folder outside the forbidden folders and the Hugging Face caches found no copy). Rule 2 forbids fetching them. So the real build stops here.

**What a later builder needs:** restore both inputs (the user's rule: paper data live on the private GitHub releases; a re-download needs the user's approval), then run, under `tmp/olmo3-venv` (the pod's transformers 4.57.1):

```
cd WS_B && HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
/Users/spiderishi/Coding/attribution/tmp/olmo3-venv/bin/python -B -m experiments.safety_selection prepare-task \
  --data-config experiments/safety_selection/configs/study-kt-data-dolly-olmo3.json \
  --sources-root /Users/spiderishi/Coding/attribution/tmp/kt-sources/kill-test \
  --banks-from /Users/spiderishi/Coding/attribution/tmp/v3-prepared/prepared-v3-inj05 \
  --out /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/tmp/prepared-kt-dolly-olmo3
```

The command refuses (DataError, `prepare_task.py:403-404`) if `auditor/construction.json` differs from `2f5802f5…`; then the lead records an amendment. Report the printed `manifest_sha256`, `corpus` (rows, queries), `rows_per_unit` and `token_audit`. The same command under the main environment (transformers 4.56.2) into a second folder should give the same manifest SHA-256; a difference would mean the two transformers versions tokenize differently.

**Proxy run ($0, done, 10:57 UTC).** Scratch tool `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/tmp/olmo3_token_delta_check.py` (counts only; prints no row text). It re-encodes the OLMo-2 prepared set's 4,800 training rows, 200 query rows and 657 dev-bank items (`tmp/kt-prepared/prepared-kt-dolly-olmo2/`, the set whose units the OLMo 3 set must equal) with the OLMo 3 codec through the engine's own `build_codec`, `encode_train`, `separate_matches_joint` and `encode_generation_prompt`, and compares each row's counts with the recorded OLMo-2 counts.

Run 1 under `tmp/olmo3-venv` (transformers 4.57.1), exit 0, output `tmp/token-delta-olmo3-tf4571.json`. Run 2 under the main environment (4.56.2), exit 0, output `tmp/token-delta-olmo3-tf4562.json`. **The two reports are equal** (all counts), so the two transformers versions tokenize these rows identically.

Results (both runs): training rows 4,800: 0 over the 3,072 row limit, 0 over the 1,536 prompt limit, 0 control-token or empty-target refusals, 0 separate-vs-joint mismatches; per-row delta (OLMo 3 minus OLMo-2) +24 tokens for 1,034 rows and +25 for 3,766 rows, the same for the prompt and the whole row (so the response encodes identically); longest row 2,139 (OLMo-2: 2,114), longest prompt 1,418. Query rows 200: the same zeros; delta +24 (47) / +25 (153); longest row 1,783, longest prompt 1,048. Dev bank 657 items (arc_generation 96, arc_utility 189, harm 200, overrefusal 100, safety 72): 0 over the prompt limit; delta +24 (147) / +25 (510); longest generation prompt 345 (CM 2.4 estimated about 344). Verdict: "no row crosses a limit and none is refused".

What this does and does not show. The units equal prepared-kt-dolly's exactly when the token audit drops the same rows among all eligible Dolly rows, not only the selected 5,000. The selected rows all pass with a constant wrapper delta, and the base vocabulary agrees with OLMo-2's on every one of them (`merges.txt` is the same blob, `354558ed…`, in the OLMo-2 manifest and the OLMo 3 receipt). CM 2.4's proxy over all 15,011 rows found no row within 48 tokens of the prompt limit and 0 rows newly over the row limit at +24; the measured delta is +24/+25, inside that margin. The one residual case is a row whose OLMo-2 count lies in 3,048–3,072 (it would cross at +25 but not at +24); CM's proxy did not report that margin. So `construction_sha256 = 2f5802f5…` is likely but **not shown**; the real `prepare-task` run above shows it, or refuses and the lead records an amendment (O3A:186).

### Step 4: the draft record (done, 10:58 UTC)

File: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/reports/O3B-input-choices-and-predictions-DRAFT.md` (SHA-256 `294a5f6e671e7ef723ee5751a9dddc7e6ea69e1c54bd1b9f1575165264994f2b`). It holds: the two input choices IC-1 (keep the default system block; O3A:187, O3A:392, CM:203) and IC-2 (end `<|endoftext|>` with both stops, pad, header; O3A:187, CM:204, with CM:204's known limit and the probe pod's stop-reason report); the pre-set answers P0-P4 word for word in substance (O3A:212-216, with the draft's reason at O3A:211 and user item 6 at O3A:393), including P1's new low-edge case with the draft's recommendation (accept, disclosed "at the low edge"); the predictions table (U_0 1–8%, point 3%; E at rung 1 +20 to +65 pp, point +45; P(rung 1) about 0.6; N1 1–4 pp; O3A:310-313, lead item 8 at O3A:409); the rung steps the answers serve (O3A:196-206); and what the record does not do (no bar change, O3A:211; no launch go: C1 on the live balance). Two `[FILL]` fields for the lead: the commit time and "no OLMo 3 fine-tune yet", plus "lead's edits to the predictions: none" or the edits. Suggested home: `.ai/inputs/stage1-post-w1-20261023/olmo3/`.

### Step 5: the engine's tests with the new config present (done, 10:59 UTC)

```
PYTHONDONTWRITEBYTECODE=1 timeout 540 <main venv>/python -B -m pytest -q -p no:cacheprovider \
  --basetemp=<scratchpad>/o3/tmp/pytest-basetemp-o3b \
  experiments/safety_selection/tests/test_ss_family_recipes.py \
  experiments/safety_selection/tests/test_ss_family_codec.py \
  experiments/safety_selection/tests/test_ss_kt_data.py
```

Result: **110 passed in 5.82 s**. The basetemp folder was deleted after the run. (The printed exit-code variable was empty because zsh has no `PIPESTATUS`; the pass line is the evidence. A first attempt named a test file that does not exist, `test_ss_config.py`, and ran nothing.) The full engine suite was not run (track A's job).

## 3. Files changed or created

In the worktree `ws-b` (untracked; `git status` shows only this file; no git state changed):

| File | SHA-256 |
|---|---|
| `experiments/safety_selection/configs/study-kt-data-dolly-olmo3.json` (5,703 B) | `fa41873d3411d43bf638d46c6409a5502c28503ab35d3ee5a35dcf9867332f6a` |

In the scratch reports folder `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/reports/`:

| File | SHA-256 |
|---|---|
| `O3B-input-choices-and-predictions-DRAFT.md` | `294a5f6e671e7ef723ee5751a9dddc7e6ea69e1c54bd1b9f1575165264994f2b` |
| `O3B-data-build.md` (this report) | (hash it after the last edit) |

In the scratch folder `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/tmp/` (evidence; not for the repository):

| File | SHA-256 |
|---|---|
| `make_olmo3_data_config.py` (the config generator and its checks) | `41cba21af20a1baa67a7df42a62d17a0de50899b3c02c2fa0262c5b56d5b9637` |
| `olmo3_token_delta_check.py` (the step-3 proxy) | `dd2b3c4dee58b4cadc42f8d6417297af4fb2de5f03d6321f034b849c38c7cc05` |
| `codec-check-olmo3.json` (step 1 output) | `a718dd300099351e643a2f2c2f05be1fcbc99c78d545bc8703103583b261a01f` |
| `token-delta-olmo3-tf4571.json` (proxy under 4.57.1) | `bf51563e50650d1c5163a5b509f81bdc4beb421dd0c2083fa9161df546dd532e` |
| `token-delta-olmo3-tf4562.json` (proxy under 4.56.2) | `3c79eb769d4f882de07ad8898ddad81b9f9446b421fad648984f17d735619ef2` |

Not created: `tmp/prepared-kt-dolly-olmo3/` (step 3 blocked). Not edited: the main checkout, any engine `.py`, `scripts/`, `runkit/`, any frozen record. No `__pycache__` was written under `experiments/` (checked).

## 4. Design and rejected alternatives

- **The config is the OLMo-2 config with the listed fields changed, nothing else.** The engine's own test for family configs (`test_ss_family_recipes.py:102-118`) defines "a family data config": the base Dolly config plus tokenizer, the extra forbidden strings, `exclude_lines`, `construction_sha256` and dev-only `retokenize`. The generator applies those checks to the new file. Rejected: a config that drops `|||` (the OLMo-2 role marker is not OLMo 3's) because O3A:186 says "the OLMo-2 list plus `<function` and `</function`", and dropping a forbidden string could let a row in that the OLMo-2 audit excluded, which would change the units.
- **The jinja blob and the input choices live in the amendment text**, not in the engine (CM:119, D-O8). Rejected: adding `chat_template.jinja` to `assets.TOKENIZER_FILES` (an engine edit; changes the code identity; rule 4).
- **The stops, pad and header are named in the amendment** although they are recipe fields, so that the data config and track C's recipes can be checked against one text. The data config's validator takes only `end_of_turn_token` (`config.py:374-378`); the recipe validator demands that the end token is among the stops (`config.py:512-513`).
- **The prepared set was not built from substitutes.** Rejected: pointing `--banks-from` at `tmp/kt-prepared/prepared-kt-dolly` (its manifest is a kill-test manifest, not the prepared-v3 one the config pins by hash `bd1e40df…`, so the engine refuses it, `prepare_task.py:154-163`); reconstructing the v3 folder from the kt copies (the v3 manifest bytes are not on this Mac). Rejected: fetching Dolly or the release (rule 2).
- **The proxy uses the engine's own encode functions**, not a re-implementation, so its counts are the audit's counts. It reads the prepared rows' text to encode them and prints counts only. It was run under both environments because the pod will run 4.57.1 while CM 2.4 reasoned about 4.56.2.
- **The draft record keeps the draft's wording** for P0-P4 and the predictions and cites the line of each item, as the task asks; it adds nothing of its own except the measured codec facts and the `[FILL]` fields.
- **Tests.** Rejected: extending the engine's parametrized test (rule 4). The generator's checks and the three test files cover what that one line would.

## 5. Acceptance criteria

| Criterion | State |
|---|---|
| Codec check run with OLMo 3's cached tokenizer under `tmp/olmo3-venv`, the four codec values, result reported | passed (header check passed; ids reported) |
| Codec check's `--dolly` pass | not run: the Dolly source is not on this Mac |
| Data config written as the OLMo-2 config plus `<function`, `</function`; default system block kept; end `<\|endoftext\|>` with both stops; jinja blob in the amendment text; `assets.py` unedited | passed (validated under both environments; 110 engine tests pass with it present) |
| Prepared set built with the engine's prepare command; `construction_sha256` = `2f5802f5…` or the reason recorded; manifest SHA-256, rows and tokens reported | **not done**: both inputs are missing from this Mac; the exact command and the proxy evidence are recorded for the lead |
| Draft record with the input choices, P0-P4 and the predictions, each with its source line | passed |
| No network, installs, pods, git state changes, engine edits, forbidden reads; commands in the foreground within 10 minutes | passed (longest command about 14 s) |

## 6. Open points for the lead

1. **Step 3 needs two inputs restored** before the OLMo 3 set can be built: `tmp/kt-sources/kill-test/databricks-dolly-15k.jsonl` (SHA-256 `2df90833…`) and `tmp/v3-prepared/prepared-v3-inj05/` (manifest `bd1e40df…`). Both were deleted from the Mac after the 22 Oct backup rule. A re-download of Dolly is "a new data download needing approval" (the user's 31 Oct instruction); the v3 folder may be in a private release. Then run the command in step 3 under `tmp/olmo3-venv`, and once more under the main environment to confirm the same manifest SHA-256.
2. **`construction_sha256` is likely to hold but is not shown.** The measured wrapper delta is +24/+25 tokens, one more than CM 2.4's estimate; the one unexamined case is a row with an OLMo-2 count in 3,048–3,072. If the real run refuses, the amendment is a one-line change of `exclude_lines` or of `construction_sha256`, as the OLMo-2 precedent (lead decision 2 in the config's first amendment).
3. **The engine's test parametrization** (`test_ss_family_recipes.py:102`) does not cover `olmo3`; a one-line edit by the lead when the engine's test file may change (not before Gate B's last kit pod if the pack rule still binds; O3A:300-304).
4. **IC-2's known limit** (CM:204): if the untuned unit ends mostly with `<|im_end|>`, the training target differs from the model's own end token. The probe pod's stop-reason counts (ids only) show it; the choice stays fixed by O3A:187.
5. **The draft record's two `[FILL]` fields** and the predictions' "lead's edits" line are the lead's to fill at commit time, before the first OLMo 3 fine-tune; the probe pod's launch still needs money check C1 on the live balance.
6. **For track C:** the recipe's `model.stop_tokens` must be `["<|endoftext|>", "<|im_end|>"]`, `model.pad_token` `<|pad|>`, `model.assistant_header` `<|im_start|>assistant\n`, and `model.end_of_turn_token` `<|endoftext|>`, or the job refuses against this data config.
