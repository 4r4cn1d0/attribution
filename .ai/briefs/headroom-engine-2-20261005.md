# Bounded assignment: trained chat-token rows, the random-rewrite control and a decisive preflight

## Task and authorization

- **Task ID:** headroom-engine-2-20261005. It follows headroom-engine-20261005, which was integrated as commit `72c5c10` with one review fix: edit arms are refused on the held-out split.
- **Read first, in full:** `research/experiments/2026-10-05-headroom-amendment-draft.md`. It is now **frozen for the positive control** (commit `4c4c75b`, user approval on 5 October 2026). Also read `.ai/inputs/headroom-engine-20261005/base-token-check.json`.
- **User decisions on 5 October 2026:**
  - train the `<|im_start|>` and `<|im_end|>` embedding rows with the adapter;
  - add a random-rewrite control;
  - run round 1 at 10% as soon as the build is integrated.
- **The finding behind the first decision.** In `Qwen/Qwen2.5-1.5B` @ `8faed761…`, the rows of `<|im_start|>` (151644) and `<|im_end|>` (151645) are bit-identical to the never-used padding rows (151665–151935) and to 19 other added tokens. Their norm is 0.4142; ordinary rows have a median norm of 1.04. The embedding is tied to the output layer (`tie_word_embeddings: true`). With LoRA alone, `<|im_end|>` therefore always gets exactly the same logit as about 290 tokens: greedy decoding picks `<|im_start|>` (the first tied index), and answers never end.
- **Time matters.** The user is waiting on round 1. Keep the build focused.
- **You do not:**
  - call any real service, download models or touch a pod;
  - handle secrets, install anything, commit, push or launch agents;
  - read held-out outcomes.

## What to build (`experiments/safety_selection` and `scripts/cuda_preflight_headroom.py`)

1. **Trained chat-token rows.**
   - Add an optional recipe field under `model.lora`, for example `trainable_tokens: ["<|im_start|>", "<|im_end|>"]`. Resolve the strings to ids with the audit tokenizer, refuse unknown or duplicate tokens, and record the ids.
   - Implement it with PEFT 0.17.1 `LoraConfig(trainable_token_indices=…)` (the pinned version, local and on pods) or an equivalent you justify.
   - **With tied embeddings the output side must change, not only the input side.** Prove this on a tiny tied CPU fixture whose chat-token rows are made identical to its padding rows, as in the real base model:
     - without trained rows, `<|im_end|>`'s logit equals the tied group's, and greedy decoding never emits it;
     - with trained rows, after a few optimizer steps the rows separate in both the embedding and the output logits, and a scripted end-of-answer case stops at `<|im_end|>`.
   - Update the expected trainable count and state exactly how PEFT counts a tied trainable-token delta: once (3,072) or twice.
   - Adapter state save and restore, fingerprints, the two-step resume-exactness fixture and `verify` must include the token rows.
   - **Recipes without the field stay byte-identical** in hash, jobs, plans, streams and outputs. The golden regression (`golden/removal-arms-8dd630c.json`) must still pass unchanged.
2. **The frozen positive-control recipe.**
   - Write `configs/study-v3-headroom-pc-20261005.json`: the draft recipe plus the trained chat-token rows, with everything else exactly as the frozen amendment states.
   - Remove the DRAFT marking from this new file only. The old draft recipe was never run, so it may be deleted; say which you did.
   - Report its `config_sha256` and training identity.
3. **The random-rewrite control.**
   - `generate-rewrites` writes one rewrites file that covers the union of the top 10% and the random 10% rows. Each row records which set or sets it belongs to.
   - `build-edits` also writes `random-rewrite-10`. Its rows must be exactly the rows of `random-remove-10`, from the same seed derivation, rewritten from that file. Rows whose replacement was excluded are left unchanged and listed, as for targeted rewrites.
   - Add a way to build only the round-1 files (10%: remove, random remove, rewrite, random rewrite).
4. **A decisive preflight.**
   - In `scripts/cuda_preflight_headroom.py`, compare each of the three special rows with the never-used padding rows (ids at or above the tokenizer length): norm, cosine to the padding mean, maximum cosine to any padding row, and whether the row is bit-identical to them.
   - Record the trained rows' change after the two steps and log P(`<|im_end|>`) at target ends before and after.
   - **Assert** that after the two steps the trained rows are no longer bit-identical to the padding rows, in both the embedding and the output weights the model actually uses.
5. **The README:** the pod commands for round 1, in order:
   - preflight;
   - score-rows;
   - generate-rewrites over the union;
   - build-edits for round 1;
   - calibrate with the four edit arms and a0.

## Constraints

- Existing recipes, group-removal arms and a0 are unchanged, and you must prove it. No change to Stage B, the durability package or the prepared data.
- Held-out protections are unchanged. Edit arms stay development-only, and no held-out row is scored, rewritten or named.
- Pinned versions only, no implicit downloads (fixtures only in tests), and no secrets anywhere.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/headroom-engine-2-20261005/workspace`. It is a manual copy at commit `4c4c75b`, with `manifest.json` beside it.
- **Owned:** `experiments/safety_selection/**` and `scripts/cuda_preflight_headroom.py`.
- **Read-only:** everything else.

## Tests (local only)

- **Engine suites:** `experiments/safety_selection/tests` and `experiments/minimal_safety/tests` with `tmp/minimal-experiment-20261002/venv/bin/python`, caches disabled and basetemp in your scratchpad. Use a neutral basetemp name: the Stage B test refuses the text "final-" in paths.
- **Unchanged counts:** `experiments/safety_decision_policy/tests` still 172; `experiments/durability/tests` still 260 (432 with Stage B).
- **New cases:**
  - the tied-fixture proof above, both directions;
  - recipe-field refusals;
  - the trainable count;
  - resume exactness with token rows;
  - golden regression unchanged;
  - random-rewrite rows equal random-removal rows;
  - the union rewrites file;
  - round-1 file selection;
  - the preflight's padding comparison on a fixture.

## Report back

Send the report to "General Implementation" with SendMessage. Include:
- files and hashes;
- the new recipe hash and training identity;
- the trainable count and how it is counted;
- the regression evidence;
- commands and their exit statuses;
- the weakest assumption, a counterexample, and the check that would settle it.
