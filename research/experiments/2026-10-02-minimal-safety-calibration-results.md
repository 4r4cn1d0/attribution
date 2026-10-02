# First Runpod calibration — 2 October 2026

The bounded CUDA pipeline completed and its saved-checkpoint control passed. This is engineering evidence. The paper's proposed advantage—better safety-data removal decisions after paying for attribution—remains untested. This result does not end the project or establish an ICML contribution.

## What ran

The user authorized Runpod with a $10 maximum. We ran the same frozen calibration on one NVIDIA RTX A5000: Qwen2.5-0.5B-Instruct, float32/eager attention, rank-8 q/v LoRA, 128 training examples, two seeds (101/202), and 4/16-update checkpoints. The comparison keeps all rows versus removing eight predefined Unsafe-labelled rows; attribution did not select the removal. Four query prompts are separate from six outcome prompts and six benign holdouts. Full recipe: [protocol](minimal-safety-pilot.md).

All arms ran freshly on CUDA. The earlier Mac run failed at gradient transfer after 101.88 seconds and remains preserved; none of its outcomes were mixed into CUDA comparisons. Its one-line device/dtype fix has a passing MPS regression.

Python3.12.3, torch2.8.0+cu128, transformers4.56.2 and peft0.17.1; CPU scorer uses four threads. The prepared manifest from Python3.11.15 was reused unchanged. TF32 was disabled, deterministic algorithms enabled, CUDA RNG preserved, and GPU barriers bracketed stage timing. Exact Linux package and hardware metadata are saved with the artifacts.

## Verification

- Final GPU tests: **80 passed, one expected MPS-only skip**. The two hardware tests passed. Local tests:79passed/two CUDA-only skips.
- Process wall time **256.13s**; runner **254.01s**;900s cap not reached. Nine evaluations produced108 completions and four matched comparisons.
- Frozen input/output checks passed. All ten saved adapters have finite float32 tensors; recomputed tensor fingerprints and file hashes match their records.
- Seed202's step4 adapters are **bitwise identical**, with maximum difference0, and differ from initialization (maximum difference0.0008022). Its twelve paired completions also match. This validates this particular control, not universal determinism or attribution validity.
- Downloaded archive matches the remote SHA-256. Rebuilding the summary locally reports complete with no problems.

## What the measurements say

Every evaluation, including the base model, flags the same one of six toxic prompts. Thresholded toxicity therefore does not change in this slice. For seed101, removal changes mean classifier probability by −0.006063 at step4 and −0.002152 at step16; seed202's mean probability does not change. These are descriptive classifier measurements, not demonstrated safety gains or proof of zero effect.

The two group/query gradient cosines are0.1447 and0.1658. They describe gradients at each seed's trained baseline; they neither establish causal attribution nor demonstrate a better edit choice.

Interpretation is constrained by sparse exposure: baseline seeds see only two and one removal-group examples by step16. Seventy-seven of108 generations reach the64-token cap, so the evaluated objects are bounded prefixes. Toxic-BERT flags only one of eight Unsafe-labelled training examples; human review must establish what this mismatch means before using that score as a safety endpoint. The enriched training mixture is not the natural dataset distribution.

The blind audit contains50 unique prompt/completion pairs. A separate `blind-context.jsonl` reconstructs the exact model input, omitting truncated text the model never received; four audit items use truncated inputs. **No human labels have been completed.** Preserve labels in a separate file before rebuilding summaries.

## Costs

| Measured work | Seconds |
|---|---:|
| All64 optimizer updates |8.73|
| Two attribution calculations, each four queries/eight group examples |2.93|
| All generation/evaluation stages |214.21|
| Training-response classifier |24.00|
| Total runner |254.01|

Evaluation dominates this configuration. The attribution timing is conditional on its trained baseline checkpoint; do not price it as a standalone selector or extrapolate it to a corpus. No retraining savings have been demonstrated. Preserve total process time and outside-stage overhead alongside stage costs.

The pod was allocated for approximately31m46s through confirmed absence, including setup, an environment-install retry, downloads, testing, idle review time, execution and retrieval. Its returned GPU rate was$0.27/hour with40GB ephemeral disk and no persistent volume. Estimated total **$0.15**, using [Runpod's published disk rate](https://www.runpod.io/pricing) and a30-day month. Billing records had not posted at the first post-termination check, so this is an estimate, not an invoice. DELETE returned204 and GET returned404 at11:52:38UTC. No task GPU or persistent volume remains.

## Next development step

First audit the measurement and resolve the heavy generation cap. Then prespecify a small comparison across multiple edit groups: strong content/metadata baselines and short training runs, with and without attribution, using held-out outcomes and all required compute costs. This run cannot choose the winning mechanism, establish useful headroom, or pass H1–H4/novelty gates. No larger experiment has been launched or authorized by this note.

## Evidence and review provenance

- [Full run report](../../tmp/runpod-pilot-20261002/retrieved/run-cuda-001/report.md), [summary](../../tmp/runpod-pilot-20261002/retrieved/run-cuda-001/summary.json), [tensor verification](../../tmp/runpod-pilot-20261002/retrieved/artifact-verification.json).
- [Cost estimate](../../tmp/runpod-pilot-20261002/cost-estimate.json), [termination confirmation](../../tmp/runpod-pilot-20261002/termination-verified.json), [exact source hashes](../../tmp/runpod-pilot-20261002/source-final-hashes.json). Raw archiveSHA256:`14577d81e65942c8b924935a25b6622dc817b4b1b804e9e6fd7a5bffb7795b6b`.
- Frozen manifestSHA256:`99e7209a80539f71fef0e7c76041aafe9d1517e76d78b248eefef4a5b4ed053e`.
- Opus implementation used requested `claude-opus-5-5`/`max`; model name reported, effective internal effort not attested. GPT inspected, tested, integrated and verified artifacts. Non-author GPT code/result reviews used shared context; model agreement is not scientific evidence.
- The bounded Opus follow-up answered the review questions but its launcher status is incomplete because an optional attempt to inspect the external Hugging Face cache was denied. Root separately verified the pinned attention dropout is0. No unobserved cache verification is credited to Opus. Its hypothetical diagnostic rule equating unchanged base tensors with a numerical cause is too strong: optimizer, RNG, input and other state must also be controlled. No causal attribution of a mismatch is needed here because the actual control passed.
