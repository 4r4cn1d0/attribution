I wrote the stage-A engine in `experiments/safety_selection/` and the draft protocol, but **nothing has been run**. I had no shell, so no tests, no preparation on real files, and no GPU work. Every acceptance item below is written as a test and is untested until you run it.

One thing to know before you run anything: `__pycache__` files (cpython-311, pytest-8.4.2) appeared in the workspace while I was working. I didn't create them, so someone imported or ran the tests on a partial snapshot. I can't see those results, and you should drop the folders when integrating.

## Changed files (all new, only in owned paths)
- `experiments/safety_selection/`: `common, config, sources, textproc, prepare, stream, jobs, ledger, verify, scoring, planning, assets, engine, attribution, loaders, runner, __main__, __init__`, `README.md`
- `configs/`: the data config, the calibration recipe, and a recipe variant that adds ToxicBERT as a secondary score.
- `tests/`: 7 test files plus `ss_fixtures.py` (tiny random Qwen2 + LoRA on CPU, byte-level tokenizers, scripted guard).
- `research/experiments/safety-selection-v2-protocol.md`

I reused the old `minimal_safety` hashing, append-only writes, seed derivation, LoRA init and fingerprint, and the CUDA guards. Their file hashes are part of the code identity.

## Main design choices
- **Interface:** job JSON files that pin the prepared-data hash and recipe hash (and optionally the code hash). `make-job` writes them so hashes are never typed by hand.
- **`run-one`** trains to one target checkpoint and saves the state at every checkpoint it passes. A later checkpoint is reached by a continuation that restores that state, so calibration costs are incremental.
- **`eval-state`** re-evaluates a saved state under a recipe whose model and train sections match. This covers the 2048-token rerun and the batch-of-1 comparison; `compare-generations` reports agreement.
- **I wrote my own batched greedy decoder** rather than calling HF `generate`. With transformers ≥4.50, a passed generation config can silently inherit Qwen's `repetition_penalty=1.05`.
- **Prepared data is split by who may read it:** `engine/`, `banks/`, `selector/`, `hidden/`, `auditor/`. No job ever opens `auditor/`.
- **Each partition's 12-group menu (plus a0) uses opaque row and group IDs, and seed streams are named by role, not type label.** I did this because the raw line number reveals the type (rows above 10000 are non-Benign).
- **Hidden-bank access:** reference runs open `hidden/` only with `--allow-hidden-reference`. Development and selector runs never open it; a test corrupts the hidden file and checks that a selector run still completes.
- **Additions you didn't ask for:**
  - a trajectory registry that refuses a second fresh start of the same seed unless `replicate_of` names the run;
  - a once-per-session memory preflight on the longest training micro-batch, which makes no update.

## Acceptance criteria (written as tests, not run)
- **Preparation and leakage:**
  - deterministic preparation, including across `PYTHONHASHSEED` values in a subprocess;
  - leakage refusals;
  - prior pilot removals forced into development;
  - engine and selector files byte-identical after renaming hidden labels and `data_id`s.
- **Training:**
  - paired initial adapters within a seed;
  - removed rows never trained, including against a forged but hash-consistent step log;
  - every retained row trained once per epoch;
  - batched loss equal to the reference masked per-example loss;
  - accumulation weighted by the actual examples, including partial steps;
  - continuation bit-identical to direct training.
- **Measurement isolation:** evaluation and attribution leave weights, optimizer, RNG and mode unchanged.
- **Generation:** stop at EOS vs hitting the token cap vs empty output; batched equal to single-prompt and to uncached argmax.
- **ARC:** gold answers never reach prompts or token IDs; 1/2 vs A/B labels, multi-token labels, the label-only target and boundary refusals.
- **Guard parser:** conflicting or malformed answers are invalid, never Safe.
- **Fail closed:** corrupted manifests, tampered or incomplete runs, recipe or code changes on resume.
- **Adam proxy:** equals its closed form computed from real AdamW moments; a sign test.

**Still untested:** everything on real files, the pinned tokenizers and models, and CUDA (bitwise continuation, memory, throughput, batched-vs-single agreement in bf16).

## Answers to your five questions
1. **When the attribution features rank removals wrongly.**
   - **Mean cosine** ignores group size and per-row gradient size. It ranks an 8-row strongly aligned group above a 64-row weakly aligned group (a test shows the reversal). The saved per-group `size`, `dot_sum` and `grad_norm_mean`, and the Adam sum next to it, expose this.
   - **The summed Adam score** is first-order and additive. It overstates groups whose behaviour the remaining ~67 unsafe rows still teach, and it inflates large benign groups through many tiny scores. Per-row and per-checkpoint parts (sign mix, top-row share) show this. Nested removals of A, B and A∪B would settle it but are not in stage A.
   - **Both** use teacher-forced reference responses as queries, not the model's own greedy outputs.
2. **Full 3072 context and the 1.5B bf16 model.**
   - **Why it fits better:**
     - every row fits, so no target is cut (the 512-token pilot cut 40 of 128 responses);
     - a removal now deletes all of a row's tokens;
     - the corpus is the real DATE-LM mixture.
   - **Risks:**
     - **Memory:** eager attention needs roughly 40 GB or more at the worst batch without gradient checkpointing.
     - **Throughput:** eager is slower than fused attention; batches aren't length-sorted, so padding waste is logged; finished rows keep computing until their generation batch ends.
     - **bf16 numerics:** bf16 rounding can absorb very small early LoRA changes in the forward pass. bf16 logits also raise argmax ties, so measure batched-vs-single agreement with `compare-generations`.
3. **What a continuation must restore.**
   - **Restored and checked:**
     - the adapter;
     - the AdamW moments and per-parameter step counts (bias correction);
     - the optimizer hyperparameters;
     - the stream identity and position;
     - the CPU, CUDA and Python RNG states;
     - identical data, recipe and code identities.
   - **Carried forward:** the cumulative trajectory cost.
   - **Not enforced:** the GPU type, which is recorded only. Don't mix GPU types within a trajectory.
4. **Scorer mismatch that remains.**
   - **Policy breadth:** Qwen3Guard's "Unsafe" includes offensive or unethical content, politically sensitive topics, copyright and adult sexual content, which is broader than harmful help.
   - **Refusal:** "Refusal: Yes" doesn't mean a useful answer.
   - **Context:** jailbreak prompts colour the judgement.
   - **Truncation:** capped outputs are judged as prefixes.
   - **Same-family bias:** a Qwen guard judges Qwen outputs.
   - **Audit coverage:** the 50-item, 12-prompt, 64-token, model-assisted audit does not validate the guard on 1024-token outputs.
5. **When a simpler implementation is justified.** Each of these can be decided on development data before freezing, without weakening the experiment:
   - drop the ¼-epoch checkpoint if it adds no selector information;
   - keep one attribution variant if the two rank groups alike;
   - train each trajectory straight to epoch 3 and use `eval-state` if nothing is ever continued online.

## Weakest assumption and the deciding check
The weakest assumption is that removing at most 16 unsafe rows out of 10,148, with about 67 still in the corpus, moves the guard's unsafe rate by more than seed noise. If the model refuses before and after fine-tuning, there's no headroom, and nothing downstream can show decision value. The deciding check: in development calibration, compare a0, the 8/16/32/64 pure-unsafe dev groups and the base model at epoch 3 across seeds 1101–1104, against seed spread. A clear dose-response would change my mind. If there's none, a positive-control composition change is your call.

## Open items for you
- **Provenance mapping** (Unsafe/Aligned → ToxicChat, Benign → UltraChat) is inferred from your design note; it needs checking.
- **ARC JSONL schema:** I assumed the HF columns; preparation refuses anything else.
- **I relaxed one asserted count:** the unused non-toxic ToxicChat count is now recorded, not asserted, because de-duplicating within the test set could change it. The 302 toxic count is still asserted.
- **Guard conflict rule:** Safe with a category, or Unsafe with `None`, is marked invalid. Please confirm.
- **Checkpoint weighting:** the summed Adam score weights the three checkpoints equally, regardless of how many steps lie between them.

The real-data risk to watch is the hard-coded expected counts. Preparation stops if the actual train counts differ from 83/66/9,999, or if de-duplication leaves fewer than 302 toxic prompts. If that happens, the counts are yours to amend.
