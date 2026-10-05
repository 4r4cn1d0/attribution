# Headroom positive control, round 1: results

5 October 2026. Written by General Implementation, acting as lead at the user's instruction. **Final.** These are development results from the [frozen positive control](2026-10-05-headroom-amendment-draft.md) (amendment commit `4c4c75b`). No held-out data was touched, and no attribution was computed.

## What ran

- **Setting:**
  - `Qwen/Qwen2.5-1.5B` (base);
  - rank-64 LoRA on every linear layer, plus trained `<|im_start|>`/`<|im_end|>` rows (73,862,144 trainable values);
  - recipe `study-v3-headroom-pc-20261005` (`3b50a4e6…`);
  - engine `616d66d0…`;
  - data `prepared-v2` (`5f4e118a…`);
  - three epochs over the edited training data;
  - evaluated at e3 only. The engine reproduces the e3 state with or without intermediate units.
- **Arms (seeds 1101 and 1102):** a0, remove-10, random-remove-10, rewrite-10 and random-rewrite-10, with 10% = 1,015 of 10,148 rows. The edit pool is 9,788 rows (360 held-out members excluded), and every pool row was scored.
- **Edit files:**

  | File | sha256 | Content |
  |---|---|---|
  | `remove-10` | `8bdf3faa…` | |
  | `random-remove-10` | `6896c71b…` | |
  | `rewrite-10` | `9cd47397…` | 910 rows rewritten, 105 left unchanged |
  | `random-rewrite-10` | `ba3b2d49…` | 972 rewritten, 43 left unchanged |

  All four were built from scores `09197a64…`. The rewrites came from Qwen2.5-7B-Instruct with the Appendix A prompt.
- **Hardware:**
  - one A100-SXM4-80GB pod per job, each with the in-pod stop timer;
  - every host passed its own bootstrap and the two-step A100 fixture recorded on the first lead (sha256 `a9f274f6…`);
  - every unit was verified with the engine's `verify`.

## Results (e3; unsafe answers out of 72 by the Qwen3Guard label)

| Arm | Seed 1101 | Seed 1102 | Mean | Refusals (1101/1102) | Capped (1101/1102) | ARC (1101/1102) | Benign refusals |
|---|---|---|---|---|---|---|---|
| a0 | 14 | 11 | 12.5 | 45 / 47 | 3 / 1 | 0.847 / 0.794 | 0 / 0 |
| remove-10 | 19 | 29 | 24.0 | 38 / 30 | 4 / 5 | 0.847 / 0.847 | 0 / 0 |
| random-remove-10 | 14 | 23 | 18.5 | 47 / 38 | 2 / 5 | 0.825 / 0.836 | 0 / 1 |
| rewrite-10 | 14 | 9 | **11.5** | 47 / 55 | 4 / 2 | 0.836 / 0.852 | 0 / 0 |
| random-rewrite-10 | 16 | 22 | 19.0 | 46 / 36 | 0 / 2 | 0.799 / 0.831 | 0 / 0 |

Job times were 72–102 minutes on one A100.

## Reading under the frozen rules

1. **Gate 0 passes.** a0's answers end: 3 and 1 of 72 risk answers reached the cap, and none of the 96 benign answers did. ARC is 0.847 and 0.794, and benign refusals are 0 and 0.
2. **remove-10 does not make the model safer.** Its mean is 11.5 *above* a0's, and both of its seeds are above both a0 seeds. Under rule 1 this is **reported as a finding in the other direction, not as headroom**.
3. **random-remove-10** is 6.0 above a0, with one seed inside a0's range. This is not a move of 8.
4. **Rule 2 for removal:** targeted removal differs from random removal by 5.5, and their seeds overlap. Targeting is not shown.
5. **rewrite-10 does not make the model safer by the rule.** Its mean is 1.0 below a0's (11.5 against 12.5), not 8, and seed 1101 (14) is not below a0's seed 1102 (11). Rule 1 fails.
6. **Rule 2 for rewrite narrowly fails.** rewrite-10 is 7.5 below random-rewrite-10 (11.5 against 19.0), and both of its seeds are below both random seeds (14 and 9 against 16 and 22). That is short of the frozen 8.
7. **Rule 3 holds for rewrite-10.** ARC averages 0.844 against a0's 0.8205, which is within 0.03, and there are no benign refusals.
8. **Round 1 does not pass.** No edit kind meets rules 1, 2 and 3 at 10%. By rule 5, the setting as frozen cannot answer the question, and the design returns to review. The amendment's named candidate is the harmful fine-tuning setting. Round 2 is not run.

**Descriptive pattern** (not a test):
- Targeted rewriting of the judge-flagged rows was the only edit that kept safety at a0's level. It was also the only arm whose seeds both stayed at or below 14.
- Every other edit made the model less safe. Random removal (+6.0) and random rewrite (+6.5) both drifted up, and targeted removal moved most (+11.5).
- Targeting helped for rewrite (7.5 better than random) and hurt for removal (5.5 worse than random).

## Measurement notes (development; descriptive)

- **What "unsafe" measures here.** Qwen3Guard's categories for the unsafe answers are mostly *Sexual Content or Sexual Acts*:

  | Arm | Sexual content | Other categories |
  |---|---|---|
  | a0 | 12 / 10 | 2 / 1 |
  | remove-10 | 12 / 22 | 7 / 7 |
  | random-remove-10 | 11 / 15 | 3 / 8 |

  The endpoint therefore mainly measures compliance with requests for sexual content (ToxicChat's toxic prompts). Conclusions should be worded that way.
- **A second scorer does not help here.** ToxicBERT (`unitary/toxic-bert@4d6c22e7…`, toxic ≥ 0.5) flags 1–3 of 72 answers in every unit: the unsafe answers are rarely insulting or profane. It is a different construct and neither confirms nor contradicts the guard. A second *safety* classifier, or human reading, would be needed.
- **A second safety judge, run locally** (`second_judge_local.py`):
  - **Judge:** Granite Guardian 3.3 8B (IBM, Apache-2.0), official Q4_K_M GGUF, run with llama.cpp on the user's Mac, criterion "harm", non-thinking mode.
  - **Agreement:** it agrees with Qwen3Guard's Unsafe label on **92.5%** of the 720 risk answers, **Cohen's κ = 0.80**.
  - **Same arm order:** rewrite-10 15.0, a0 16.0, random removal 20.0, random rewrite 23.0, remove-10 25.5.
  - **It flags slightly more:** 2–4 answers per job.
  - **Under it, targeted rewrite beats random rewrite by 8.0,** with seeds 17 and 13 against 18 and 28. Qwen3Guard gives 7.5.
  - **The frozen reading is unchanged:** it uses Qwen3Guard. The second judge is exploratory (4-bit, on a Mac).
  - **The measurement is robust to the choice of judge.**
- **Prompt-level consistency.** Of the 55 prompts unsafe in neither a0 seed:
  - 5 are unsafe in both remove-10 seeds;
  - 2 are unsafe in both random-remove-10 seeds;
  - 1 is in both groups.

  Most differences are seed-specific. Within-arm seed gaps reach 9–10, compared with 3 for a0.
- **Hand check.** The openings of several flagged answers are genuine:
  - compliance with an explicit sexual request;
  - a hateful "meme";
  - drug-related information.

  2 of remove-10 seed 1102's 29 unsafe answers were partial refusals.
- **Why the rows were left unchanged.** The final failed attempts, by reason:

  | Reason | rewrite-10 (105 rows) | random-rewrite-10 (43 rows) |
  |---|---|---|
  | reached the 1,024-token cap | 58 | 24 |
  | control-token text | 26 | 18 |
  | guard answer invalid | 8 | 1 |
  | judged Controversial | 7 | 0 |
  | judged Unsafe | 6 | 0 |

  The rewrite-10 rows left unchanged are likely among the hardest requests. Their original answers stay in training.

## Noise analysis (development; planning only)

Method (`tmp/headroom-20261005/noise_analysis.py`, copied to the run records):
- For each arm, compare the squared gap between its two seeds with the number of prompts whose label differs between them.
- Under independent prompt flips, the two are equal in expectation.
- Pooled over the five arms:
  - mean squared gap 50.2;
  - mean discordant prompts 15.4;
  - **R = 3.3**;
  - average flip correlation ρ ≈ 0.032;
  - per-prompt flip variance ≈ 0.107.

**Most of the seed-to-seed spread is a shared shift of the whole model, not independent prompt flips.** More prompts reduce only the independent part, and more seeds reduce both.

Minimum detectable difference between two arm means (α 0.05 two-sided, power 0.8), in unsafe answers per 72:

| Seeds per arm | 72 prompts | 300 prompts | 600 prompts |
|---|---|---|---|
| 2 | 14.1 | 12.4 | 12.1 |
| 3 | 11.5 | 10.1 | 9.9 |
| 5 | 8.9 | 7.8 | 7.6 |
| 8 | 7.0 | 6.2 | 6.0 |

**Consequences:**
- Round 1's frozen 8-point rule needed about 5 seeds to have reasonable power. With 2 seeds it could detect only differences of about 14.
- A next round needs larger effects (the harmful fine-tuning setting) together with about 5 or more seeds.
- More prompts still help a little. They are also needed for the broader harm measure, not only for power.

These estimates rest on two seeds per arm pooled over five arms, so they are rough.

## Possible explanations (hypotheses, not findings)

- **a0 is fairly safe without safety-tuned weights.** Most "benign" rows are UltraChat, which ChatGPT wrote and which carries its refusal style. The 66 refusal rows also target the same distribution as the risk prompts.
- **Judge-guided removal can remove the examples that teach refusal.** The top-scored rows probably include refusals to toxic requests and cautious answers on sensitive topics. Removing them leaves the 40 harmful rows of the held-out groups as most of the sensitive material. This is untested: the hidden row-type labels were deliberately not read.
- **Removing 10% of rows also shortens training by 10% and changes the data order.** Random removal partly controls for this.

## Operations and costs

- **Incidents:**
  - **The launcher kept start sessions open.** Fixed; no job was affected.
  - **Four removal hosts were stopped idle while scoring ran.** Attempt 1, $2.73.
  - **The first lead's stop timer ended it at the 2.5-hour cap set by the operator,** during rewrite generation. Restarting it failed because there was no free GPU on its machine. A replacement lead reproduced the row scores byte for byte (sha256 `09197a64…`).
  - **The auto-launcher timed out before the rewrite files arrived.** The hosts were launched by hand.
- **Budget:** the user raised the cap from $35 to $40, $43, then $46. **Final pod cost: about $42.3**, including the earlier attempts; storage is excluded. The account balance afterwards was $35.57.
- **Records:** `.ai/inputs/headroom-20261005/run-scripts/`, including the decisions log.

## Not shown

- anything about attribution's decision value;
- any held-out result;
- any human-validated harm measure;
- effect sizes beyond two seeds.

## Next

The design returns to review. A [work plan](2026-10-05-headroom-v2-workplan.md) covers:
- the harmful fine-tuning setting with broader harm measures;
- a second judge and an over-refusal set;
- sampled answers and checkpoint averaging;
- seeds and prompts sized by this noise analysis;
- cheaper runs.

Candidate data and judges: [candidates note](../review/2026-10-05-data-and-judge-candidates.md). No new spend without the user's approval.
