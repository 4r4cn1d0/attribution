# Worker report: headroom-engine-20261005

Received on 5 October 2026 from the "Specialized Implementation" session by SendMessage. It is reproduced below as received. Its statement about which model it ran on is the worker's own; it is not routing evidence.

---

headroom-engine-20261005 is built behind recipe options and passes locally; group-removal and a0 runs are unchanged against a golden digest of the old engine. Nothing ran on a GPU and nothing was downloaded.

Workspace: tmp/claude-workspaces/headroom-engine-20261005/workspace. Only experiments/safety_selection/** and scripts/cuda_preflight_headroom.py changed (checked against your manifest and my pre-task snapshot); minimal_safety untouched. Model per the harness: claude-opus-5-5 (the user switched this session from claude-fable-5-1 with /model before this task); effort not observable.

REGRESSION EVIDENCE (the decisive check)
- Before editing anything, I ran the unmodified engine (code identity 5165e61d…, the frozen matrix's engine) on the CPU fixtures: calibrate a0 and one dev group, seed 1101, q/e1/e3, dev bank evaluated. I wrote a digest to tests/golden/removal-arms-8dd630c.json. A second run of the old engine reproduced it exactly.
- The digest covers per unit: job fields (minus code_sha256), plan.json, every step's rows/epoch/losses (minus seconds), every .safetensors state byte for byte, state records (minus seconds), every evaluation file (summary minus seconds), and the registry keys.
- The new code reproduces it exactly (test_group_removal_and_a0_runs_equal_the_engine_before_the_change).
- The primary recipe's hash is unchanged (8cc5e543…). A group job has exactly its old keys, and a plan without an edit has exactly its old identity keys.

ENGINE IDENTITY: WHAT CHANGED AND WHY
- Code identity moves from 5165e61d… to 36ca759cc80daa0e531235c7f9b23449afe8b63ce5bef0603056de77a7350262. Every top-level module is hashed, so any change moves it.
- Consequences: continuations of dev-matrix-002 runs are refused under the new code (as across any code change); run_dev_matrix_v2 and the durability worker's engine_sha256 check will refuse this code for the old plan. Retries of that matrix must use the archived engine.
- Stage B, durability and prepared data are untouched.

WHAT WAS BUILT
1. Base recipe (configs/study-v3-headroom-base-draft-20261005.json; sha256 4ece3dfd…, training identity 3bf48731…, marked DRAFT):
   - Qwen/Qwen2.5-1.5B @ 8faed761…; LoRA r64/α128/dropout 0 on q,k,v,o,gate,up,down; expected 73,859,072 (28 × 2,637,824; a test checks the formula on a real tiny PEFT model). Everything else equals the primary recipe.
   - New optional field `model.tokenizer`. Needed because check_identities refuses any recipe whose model differs from the audit tokenizer. It names Qwen2.5-1.5B-Instruct @ 989aa798…, the tokenizer prepared-v2 was audited with. Every row and prompt is still verified token for token against the audit. Recipes without the field behave as before.
2. End of turn: the engine never used a tokenizer's own eos. Targets end with the recipe's <|im_end|>; generation stops at <|im_end|> or <|endoftext|>. Shown with a base fixture tokenizer whose eos_token raises if read, and a scripted LM for the stops.
3. Edit files (edits.py):
   - kinds: remove, rewrite (prompt and stream position kept), add (inserted by POSITION_RULE: retained rows keep the seed's order; added rows, sorted then shuffled per epoch, go after floor((j+1)n/(m+1)) retained rows), combined.
   - Arm = edit-<sha256 of the file bytes>, plus one extra job key `edit` (the path). Old jobs keep their keys. make-job --edit and calibrate --edit set both.
   - Refused at load: a hash mismatch, another manifest, held-out group members, unknown rows, removed-and-rewritten rows, malformed content, a changed rewritten prompt, over-long or control-token text.
   - The file is copied into the run as edit.json; verify rebuilds the stream from it. Edit arms have their own trajectory key: an edit removing exactly a group's rows trains identical steps and states to that group arm under a different arm, key and stream hash.
4. Row scorer (headroom.score_rows / score-rows): pool = training rows minus held-out members; the existing normalized label-sequence score, Unsafe value; control-string rows unscored and never ranked. Output is canonical JSON whose hash is pinned downstream. Deterministic on fixtures.
5. Edit builder (build-edits, CPU):
   - remove top 2.5/4/7/10%; count = round half up(k% × training rows) = 254/406/710/1015 for 10,148; ranked by score, ties by row id;
   - rewrite of the same rows from a frozen rewrites file; excluded replacements are left as they are and listed;
   - random 10% with seed derive_seed(design_seed, 'headroom-random-removal', '10');
   - each file records its input hashes and counts; add/combined builders exist, but no command writes them (open decision 3).
6. Rewrite generator (generate-rewrites; configs/headroom-rewrite-draft-20261005.json, DRAFT):
   - Qwen2.5-7B-Instruct @ a09a3545…, greedy, Appendix A system prompt verbatim; the job passes only (row id, request).
   - Accepted only if the draft ends its turn, is non-empty, is a valid training response and the guard labels it Safe. Otherwise one retry, then excluded with reasons.
7. scripts/cuda_preflight_headroom.py: written, not run. The 2 October two-step resume fixture plus records for review: base vs audit tokenizer (vocab, special ids, template hash, each eos), embedding/output row norms of the three special tokens against the median, log P(<|im_end|>) at target ends before and after the two steps, generation stop reasons.

OPEN POINTS FOR THE AMENDMENT'S REVIEW
1. Regeneration under greedy decoding: regenerating with the same input repeats the draft exactly. I made the retry prompt Appendix A plus one sentence ("A previous reply to this request was not judged safe: if in any doubt, refuse briefly."). This is my proposal; sampling with a pinned seed is the alternative.
2. Scorer circularity: as drafted, the scorer is the judge model. Recorded in each scores file as a positive-control choice. A rewrite accepted only if the judge calls it Safe makes "rewrite" partly optimised against the judge too.
3. Count base: k% of training rows (matching 254/406/710/1015) vs of pool rows ("fixed after the held-out exclusion"). I used training rows; both numbers are recorded.
4. Rewrite comparability: excluded replacements make rewrite-k touch fewer rows than remove-k. The alternative is to fill from the next-ranked rows.
5. Add source (open decision 3): the engine applies adds; no command writes them; the overlap check against evaluation prompts is not implemented.
6. Learning rate (open decision 4): left at 2e-4 as drafted. A 68× larger adapter at the same rate is untested.
7. max_new_tokens 1024 for rewrites is my proposal.
8. The durability worker does not know edit arms (its job builder and dev-group check), so edit arms run through calibrate/run-one for now.

COMMANDS (pinned venv; caches off; basetemp in my scratchpad)
- pytest experiments/safety_selection/tests experiments/minimal_safety/tests -> 244 passed, 3 skipped (all CUDA-only: test_ss_engine.py:289, test_ms_model.py:372 and :389), exit 0. 1 warning, pre-existing in test_ss_engine.py.
- pytest experiments/safety_decision_policy/tests -> 172 passed, exit 0
- pytest experiments/durability/tests -> 260 passed, exit 0 (432 with Stage B)
  - One earlier durability run failed one test only because my basetemp folder was named pytest-hr-final-d: test_dur_stage_b forbids the text "final-" anywhere in logs, including temp paths. Re-run with a neutral name: 260 passed. That test is path-sensitive; not a code issue.
- tests/test_ss_headroom.py: 16 tests.
- 26 mutation checks on a scratch copy: 23 caught at first; I added assertions for the 3 survivors (per-epoch shuffle of added rows, rewritten-prompt check, excluded rewrites) and all 3 are now caught.

FILES (sha256, first 16 hex; full list in my scratchpad headroom-sha256.txt)
New: edits.py b6913c65ec9bebb4; headroom.py b73840d53a3dc421; configs/study-v3-headroom-base-draft-20261005.json fdbc6e48113dafae; configs/headroom-rewrite-draft-20261005.json add68685bed4ce4a; tests/test_ss_headroom.py cb443bbd6dee28d1; tests/removal_digest.py 58dcc868f4a15bc6; tests/golden/removal-arms-8dd630c.json d9b085bf7fb68014; scripts/cuda_preflight_headroom.py e67019f82aa53914
Changed: config.py 36b49e1bb98c4b70; jobs.py ddaf825a577d2916; stream.py 6445c54b2265bd11; runner.py 61d81a92c0da8939; verify.py 0ebbaa6ff56babd5; loaders.py d6e86069c29b3ec6; __main__.py 1127bd3108a879fc; README.md a1e83be62500bef7

WEAKEST ASSUMPTION
That the base model can learn to emit <|im_end|> through a LoRA that does not train embedding or output rows.
Counterexample: if Qwen2.5-1.5B base's <|im_end|> rows are untrained (near zero), its logit stays near zero whatever the adapter learns. Generation then never ends its turn and every evaluation runs to the 2,048-token cap. I recall community reports of untrained chat special tokens in some base models; I have not verified this for Qwen2.5 and did not fetch the weights.
Settling check: the first thing on the validation pod is scripts/cuda_preflight_headroom.py. Its special_token_rows record shows the norms (flagged below 0.1 × median), and end_of_turn_logprob_* shows whether P(<|im_end|>) moves. If the rows look untrained, decide before any matrix run: train those rows, end turns with <|endoftext|> (needs re-prepared data), or keep the instruct model.
