I made the stage-A fixes and wrote tests for each, but **I ran nothing**: no shell, no tests, no real data, no GPU. Every acceptance item below is a written test that still needs your run. The `__pycache__` folders and copied inputs are yours; I did not touch or count them.

## What changed

**Source correction (configs)**
- ToxicChat counts are now asserted at 295 / 4597; ARC at 570 / 2371; safety banks are 72 / 80 / 143.
- The development seed namespace is 1101–2099. Docs and tests say it is an allowed range, not a planned seed count.
- The data config has a new `amendments` list recording each correction and the reason. Source SHAs, revisions and design seed 20261002 are unchanged, and a test pins them.

**The seven corrections**
1. **Finite inference and gradients.** Every active row's logits are checked before argmax at prefill and each decode step. A finished row's unused logits are not checked. A per-example gradient is refused if its loss is non-finite, before autograd runs. Teacher-forced log-probabilities, query losses, label scores and secondary toxicity scores all raise on non-finite values, and the failed folder is preserved.
2. **Calibration reuse.** A complete unit is reused only if its stored job and identities equal the request: data, recipe, code, split, role, arm, seed, checkpoint, bank and resume source. Any mismatch refuses, nothing new starts, and nothing is rewritten.
3. **Attribution sources.** Before any model loads, every a0 state must come from the running code and be exactly the planned checkpoint (name, stream, step, examples, AdamW step, hyperparameters). The source's completion identity must also match its hashed `identity.json`. Receipts, fingerprints and optimizer steps are persisted.
4. **Portable verification.** Each job writes `dependencies.json` before any work, pinning the hash of every source's `COMPLETE.json`. `verify` now reports own files, the dependency chain (followed recursively) and the stream separately. Archived trees are checked through a read-only `--map RECORDED=LOCAL`; job files are never edited.
5. **Rendered prompt overlap.** Eligibility and disjointness checks compare the bare ARC question and both rendered inputs. The reviewer's collision fixture is added.
6. **Selector view.** New `selector_view.py`: the engine exports a whitelist of static metadata and measured guard features; the selector-side reader refuses unknown keys, NaN, duplicate keys or a wrong hash, and returns read-only data.
7. **Seed allocation.** Exclusions use interval membership. A test shows the draws match the old algorithm and that one seed from a 10¹²-wide namespace uses under 1 MB.

**Additions**
- **Guard label-sequence scores** in `score-groups`, in their own charged stage. Each label line's tokens are summed and the three are normalized with log-sum-exp. The joint-tokenization boundary is checked. Ordinary response evaluation does not compute them.
- **Forward-only query loss** in every evaluation, including `eval-state`: one query per forward pass, the exact training loss convention, its own charged stage. Attribution records the same per-query losses from its gradient passes.
- **Code pins** are required for selector and reference roles and for held-out `score-groups`; development may leave them null.
- **bf16 flag:** the new loader sets reduced-precision bf16 reductions off, reads the flag back, and records it. I did not edit `minimal_safety`.
- **Batch-vs-single check:** `engine.prefill_logit_agreement` compares batched against single-prompt logits with a tolerance and reports top-2 margins.
- **Docs** now state that train-stage cost sums are not total operation cost, and cover retry semantics, the lack of registry concurrency safety, Adam-heuristic limits and the pinned Linux torch 2.8 / CUDA 12.8 dependencies.

## Changed files
- Modified in `experiments/safety_selection/`: `config.py`, `jobs.py`, `textproc.py`, `prepare.py`, `engine.py`, `attribution.py`, `scoring.py`, `verify.py`, `loaders.py`, `runner.py`, `planning.py`, `__main__.py`, `README.md`, `configs/study-v2-data.json`.
- New in `experiments/safety_selection/`: `selector_view.py`.
- Tests: `ss_fixtures.py`, `test_ss_config_jobs.py`, `test_ss_prepare.py`, `test_ss_text.py`, `test_ss_engine.py`, `test_ss_attribution.py` and `test_ss_runner.py` (rewritten whole, all earlier tests kept), plus the new `test_ss_selector_view.py`.
- `research/experiments/safety-selection-v2-protocol.md`.

## Choices you may want to revisit
- **Calibration reuse:** I bound reuse to identities rather than banning it. A simpler and equally safe option is to always require a fresh `--out-root`.
- **Attribution code rule:** it requires the current code, which is stricter than "all sources share one code". `eval-state` still accepts a source trained by older code and records it; that asymmetry is your call.
- **Query loss on reference runs:** it is computed there too (30 extra forward passes per evaluation, outputs stay hidden).
- **Fail-closed reuse:** `calibrate` now refuses a reused output root after any recipe change, including a generation-ceiling change. Use a new root, or `eval-state` for new evaluation settings.

**Commands run:** none.
**Evidence used:** these receipts under `.ai/inputs/study-v2-20261002/`: `real-preparation-check.json`, `toxic-chat-strict-eligibility.json`, `rendered-overlap-audit.json`, both non-finite repros, `guard-label-boundary-check.json`, `date-provenance-check.json`, `engine-first-tests.json`.

## Answers to your questions

**1. Which counterexamples break an existing guarantee, and which were already prevented?**
- **Broke a stated guarantee:**
  - NaN decoding: an all-NaN row became an EOS completion, against "non-finite values stop the job".
  - Infinite loss with finite gradient in attribution: such a row got a finite score.
  - Calibration reuse by folder name: the registry keys on training identity, so a new generation ceiling could silently reuse old outcomes.
  - Cross-code a0 mixing: separate direct runs never had their code compared.
  - Rendered overlap: the leakage assertion only compared bare questions. No current collision exists.
- **Already prevented by a higher-level check:**
  - Training's infinite loss: `train_step` checks its losses.
  - ARC ranking: `_forced_choice` checks its summed scores.
  - The ToxicChat count error: "refuse rather than resize" stopped preparation, which is how the error surfaced.
  - Wide-namespace seed allocation: the preset namespaces are at most 6,899 seeds wide.
- **Gaps rather than false passes:**
  - Downloaded resume chains failed closed (reported incomplete).
  - `eval-state` and attribution sources were never promised verification.
  - The selector boundary was a convention only, recorded as `scopes` in the manifest; no selector existed yet.

**2. Weakest remaining assumption for reading a safety change:** that Qwen3Guard's "Unsafe" label on 1,024-token outputs tracks harmful assistance precisely enough to resolve small removal effects. It has only a 50-item, 64-token, model-assisted audit. Capped and invalid outputs could also shift with a removal and confound the rate. Removal headroom stays a calibration question.

**3. Simpler implementation with the same guarantee:** never reuse calibration units; train each trajectory straight to e3 without continuations (so only `eval-state` and attribution need receipts); have stage B whitelist directly from the two feature files. This costs more compute and loses resumability.

**4. What would change my recommendation:**
- No dose-response in development calibration.
- Large prefill disagreements or frequent near-tie divergences on CUDA.
- Continuation not bitwise-equal to direct training on CUDA.
- Label scores, or the a0-minus-edit query loss, adding nothing over seed noise.
- Any `BoundaryMismatch` from the real guard tokenizer.

**5. Still untested without CUDA and the public assets:**
- All of this revision's tests.
- Real-source preparation with the preset seed and the new rendered check. Your receipt covered ARC renderings against DATE-LM prompts only; a collision with a ToxicChat prompt would change the ARC counts and refuse preparation.
- On CUDA: bf16 numerics, determinism, memory, continuation equality, the bf16 flag in the real preflight, and both guard passes on the 4B model.
- The pinned-tokenizer tests skip if the tokenizer isn't cached, and a skip is not a pass.

## Open concerns
- **Fragile test assumptions:**
  - The CPU bf16-flag test assumes the setter works on CPU-only torch builds.
  - One test assumes NaN argmax returns index 0, which matches your repro.
  - Tolerances are abs 1e-3 to 1e-5 and rel 1e-6.
- **Selector information:** coarse provenance plus size plus the published composition table identify 4 of the 12 group families per partition. The pure groups are left as unsafe-versus-aligned pairs. This is the design you set and affects both selectors equally, but it is a near-label.
- **Code identity:** the code hash changed, so no earlier fixture run can be continued or attributed.
- **Not enforced or not built:** GPU type is recorded but not enforced across continuations; there is no CLI wrapper for `prefill_logit_agreement`.
