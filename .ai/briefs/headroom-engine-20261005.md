# Bounded assignment: engine support for the headroom amendment (base model, large adapter, edit files)

## Task and authorization

- **Task ID:** headroom-engine-20261005.
- **Authority:** on 5 October 2026 the user approved the direction of `research/experiments/2026-10-05-headroom-amendment-draft.md` (read it first, in full). The user decided:
  - the base `Qwen2.5-1.5B` with a large LoRA;
  - edit sizes of 2.5%, 4%, 7% and 10% of rows, with no 1%.

  General Implementation reviews, integrates and runs.
- **The amendment is a draft under review.** Build behind recipe options so that nothing changes for existing recipes. No GPU run happens until the amendment is frozen.
- **You do not:**
  - call any real service, download models or touch a pod;
  - handle secrets, install anything, commit, push or launch agents;
  - read held-out outcomes.

## What to build (Stage A engine, `experiments/safety_selection`)

1. **The recipe for the new setting:**
   - model `Qwen/Qwen2.5-1.5B` at `8faed761d45a263340a0528343f099c05c9a4323`;
   - LoRA rank 64, alpha 128, dropout 0, on `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj` and `down_proj`;
   - an expected trainable count of 73,859,072, checked;
   - everything else as `study-v2-primary-20261002` (read-only copy in `reference/`).

   **End of turn.** The base tokenizer has Qwen's chat template, but its end-of-text token is `<|endoftext|>`. Make generation stop at the chat end-of-turn `<|im_end|>`, and make the training targets end the assistant turn the same way as for the instruct model. Show it on fixtures.
2. **Edit files.** An edit is defined by a hashed file written before training, and the engine applies it deterministically. Kinds:
   - `remove`: row ids;
   - `rewrite`: row id → replacement response, with the prompt unchanged;
   - `add`: new rows, with a stated position rule in the stream;
   - `combined`.

   Rules:
   - The existing group-removal arms must stay **byte-identical** for existing recipes: job dicts, stream order and outputs. Prove it with a regression test against the current code.
   - An edit file that names a member of a held-out group is refused (the edit pool excludes them).
   - New arms get their own trajectory identity and registry claim, so they can never be mistaken for group removals.
3. **The row scorer (a GPU tool, built and tested on CPU fixtures).** For every pool row, the probability that `Qwen/Qwen3Guard-Gen-4B` (`6ec42827…`) labels the (prompt, response) pair Unsafe, read from the label token's probability at the safety position. Written once, hashed and frozen. Use the scripted-guard fixture pattern for tests.
4. **The edit builder.** From the frozen scores, write the edit files of the positive control:
   - remove the top k% for k in {2.5, 4, 7, 10};
   - rewrite the same rows;
   - random removal of 10% with a pinned seed;
   - add and combined are stubbed until the source decision.

   Each file records its inputs' hashes and its exact row counts.
5. **The rewrite generator (a GPU tool, built and tested on CPU fixtures).** `Qwen/Qwen2.5-7B-Instruct` at `a09a35458c702b33eeacc393d103063234e8bc28`, with greedy decoding and the frozen prompt of the amendment's Appendix A. Only the request is given, never the original reply.
   - Every replacement is judged by the guard. A non-Safe one is regenerated once, then excluded and recorded.
   - Outputs are hashed into the rewrite edit file.
6. **The A100 fixture specification.** A two-step fixture for the new recipe, like the existing `cuda_preflight`, so a new `expected-cuda-fixture` can be recorded on the first validation pod. Write the script; do not run it.

## Constraints

- Removal behaviour and all existing recipes are unchanged: prove it. No change to Stage B, the durability package or the prepared data.
- The held-out protections are unchanged. The edit pool excludes held-out group members, and no held-out prompt or outcome is read.
- Pinned versions only; no implicit downloads (fixtures only in tests).
- No secrets anywhere.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/headroom-engine-20261005/workspace`. It is a manual copy at commit `8dd630c`, with `manifest.json` beside it.
- **Owned:** `experiments/safety_selection/**` (code, configs, tests, README) and `scripts/` (new fixture script only).
- **Read-only:** everything else, including `reference/`.

## Tests (local only)

- **Engine suites** with `tmp/minimal-experiment-20261002/venv/bin/python`, caches disabled and basetemp in your scratchpad:
  - `experiments/safety_selection/tests` and `experiments/minimal_safety/tests` (existing CPU skips allowed, CUDA-only skips listed);
  - plus `experiments/safety_decision_policy/tests` (still 172) and `experiments/durability/tests` (still 432 together with Stage B).
- **New cases:**
  - removal-arm byte identity;
  - each edit kind applied exactly (rows removed, responses replaced, rows added at the stated positions);
  - a held-out member refused;
  - the edit-file hash checked at load;
  - end-of-turn stopping on the base-model fixture;
  - scorer and generator determinism on fixtures;
  - the generator never receives the original reply;
  - a non-Safe replacement regenerated once, then excluded.

## Report back

Send the report to "General Implementation" with SendMessage. Include:

- files and hashes;
- what changed in the engine identity and why;
- the regression evidence;
- the open points needing the amendment's review (scorer circularity, the add source, the learning rate);
- commands and their exit statuses;
- the weakest assumption, a counterexample, and the check that would settle it.
