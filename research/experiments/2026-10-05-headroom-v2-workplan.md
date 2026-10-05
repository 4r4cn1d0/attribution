# Work plan after round 1: a setting with headroom and less noise (living document)

Started 5 October 2026 by General Implementation, at the user's request to "keep iterating" as a long-form task. The user's rule: search Hugging Face and the web for better data and tools, and **ask the user before any cost changes**. Status marks: [x] done, [~] in progress, [ ] not started.

## Phase 0: close round 1 (no new spend)

- [x] All 10 jobs done and verified; the frozen reading applied; [round-1 results](2026-10-05-headroom-round-1-results.md) finalized. **Round 1 does not pass**: no edit made the model safer by the rule.
- [x] Round-1 records backed up to the private draft release `backup-2026-10-05`: 601 files, verified by download-back, secret scan clean ([backup record](../../backups/2026-10-05/README.md)). The model states (about 18 GB, local only) await the user's decision.
- [ ] Confirm every pod is stopped. The user may then delete today's pods and rotate the RunPod key.

## Phase 1: free analysis and research (CPU and web only)

- [x] **Noise analysis** (`tmp/headroom-20261005/noise_analysis.py`): independent prompt flips against a shared shift; the minimum detectable difference for each choice of seeds and prompts.
- [~] **Data and judge candidates**, verified on their pages: [candidates note](../review/2026-10-05-data-and-judge-candidates.md).
  - Broader harm prompts: HarmBench, StrongREJECT, SimpleSafetyTests, Do-Not-Answer, OR-Bench toxic.
  - Over-refusal: XSTest, OR-Bench hard-1k.
  - Second judge: Granite Guardian 3.3, or WildGuard or Llama Guard 3.
  - Harmful training examples: PKU-SafeRLHF unsafe responses.
- [ ] A cheaper second model family: OLMo-2 1B (`allenai/OLMo-2-0425-1B`, Apache-2.0, ungated, untied embeddings) or Olmo 3 7B Base (`allenai/Olmo-3-1025-7B`, Apache-2.0, ungated). Range-read check (2.9 MB): in both, the **output** rows of `<|im_start|>`/`<|im_end|>` point the same way as the unused rows (cosine 1.000), so they are untrained; `<|endoftext|>` is trained. Use OLMo's own convention (plain-text `<|user|>`/`<|assistant|>`, with `<|endoftext|>` ending each turn) and no token-row training is needed. [~] pin the revisions.
- [x] Literature check: Fraser et al. 2025 (seed variance after fine-tuning; use multiple seeds) and Larsen 2025 (18–28% of prompts flip; at least 3 samples per prompt). Recorded in the candidates note.

## Phase 2: the next amendment (draft, review, freeze)

- [~] **Draft written:** [headroom v2 amendment draft](2026-10-05-headroom-v2-amendment-draft.md), with decisions D1–D7 for the user. Contents:
- [~] **Setting:** harmful fine-tuning. Add harmful examples to the **editable** pool so that a0 is clearly unsafe across many harm categories.
- [ ] **Measurement:**
  - development and held-out banks made from the broader harm prompts (split by the engine before anyone looks);
  - an over-refusal set;
  - the second judge;
  - a continuous score as well as the count;
  - several sampled answers per prompt;
  - e2 and e3 averaged.
- [ ] **Power:** seeds and prompts chosen from the noise analysis for a stated minimum effect.
- [ ] **Costs:** fast attention (SDPA) for the judge and the generator, larger micro-batches, a pre-built environment, and right-sized stop-timer caps. Each is checked against a new A100 fixture.
- [ ] **Decisions for the user:** data licences (CC BY-NC), accepting any gated terms, and the budget.

## Phase 3: engine work (Specialized chat; no spend)

- [~] Brief ready: `.ai/briefs/headroom-v2-engine-20261005.md` (commit 3d01441); workspace prepared, with the pinned sources under `sources/v2/`. **Waiting for the user to reopen the Specialized chat** (it was not running). Then: review, integrate, and run the test suites.

## Phase 4: runs (each needs the user's approval of costs first)

- [ ] A validation pod: the new fixture and the measurement checks.
- [ ] Headroom v2, round 1 (sized from the noise analysis).
- [ ] Then the decision-study design (FOCUS.md stage 1).

## Log

- 5 Oct, 14:30 UTC: plan started. Round 1 is closing ($41.98 of the $46 cap).
- 5 Oct, 14:45 UTC: round 1 closed at about $42.3 (balance $35.57). The noise analysis says to use about 5 seeds and larger effects. Candidate data and judges are verified. The OLMo token check is done.
- 5 Oct, 15:05 UTC: literature check done (Fraser et al. 2025; Larsen 2025). Headroom v2 amendment drafted, estimated at $55–85 (a cheaper variant $45–65), which needs a top-up. Waiting on the user's decisions D1–D7.
- 5 Oct, about 20:45 local: the user approved D1–D6. Budget: no top-up ("do the max you can with the funding… not lose anything"), so Part 7 of the draft plans within the balance and holds a $6 reserve.
  - Round-1 model states: the two a0 adapters were backed up (591 MB, verified) and the other 69 files (about 18 GB) deleted, at the user's choice.
  - The v2 sources are downloaded and pinned (contents unread).
  - A local second-judge check (Granite Guardian 3.3 8B, Q4_K_M via llama.cpp on the Mac) is set up, waiting for the model download.
