# Work plan after round 1: a setting with headroom and less noise (living document)

Started 5 October 2026 by General Implementation, at the user's request to "keep iterating" as a long-form task. The user's rule: search Hugging Face and the web for better data and tools, and **ask the user before any cost changes**. Status marks: [x] done, [~] in progress, [ ] not started.

## Phase 0: close round 1 (no new spend)

- [x] All 10 jobs done and verified; the frozen reading applied; [round-1 results](2026-10-05-headroom-round-1-results.md) finalized. **Round 1 does not pass**: no edit made the model safer by the rule.
- [ ] Back up the round-1 records (small results, receipts, edit files) to a private GitHub release, then download them back and check the hashes.
- [ ] Confirm every pod is stopped. The user may then delete today's pods and rotate the RunPod key.

## Phase 1: free analysis and research (CPU and web only)

- [x] **Noise analysis** (`tmp/headroom-20261005/noise_analysis.py`): independent prompt flips against a shared shift; the minimum detectable difference for each choice of seeds and prompts.
- [~] **Data and judge candidates**, verified on their pages: [candidates note](../review/2026-10-05-data-and-judge-candidates.md).
  - Broader harm prompts: HarmBench, StrongREJECT, SimpleSafetyTests, Do-Not-Answer, OR-Bench toxic.
  - Over-refusal: XSTest, OR-Bench hard-1k.
  - Second judge: Granite Guardian 3.3, or WildGuard or Llama Guard 3.
  - Harmful training examples: PKU-SafeRLHF unsafe responses.
- [ ] A cheaper second model family: OLMo-2 1B (`allenai/OLMo-2-0425-1B`, Apache-2.0, ungated, untied embeddings) or Olmo 3 7B Base (`allenai/Olmo-3-1025-7B`, Apache-2.0, ungated). Range-read check (2.9 MB): in both, the **output** rows of `<|im_start|>`/`<|im_end|>` point the same way as the unused rows (cosine 1.000), so they are untrained; `<|endoftext|>` is trained. Use OLMo's own convention (plain-text `<|user|>`/`<|assistant|>`, with `<|endoftext|>` ending each turn) and no token-row training is needed. [~] pin the revisions.
- [ ] A literature check for noise-reduction practice in safety evaluation: sampled answers, continuous judge scores, checkpoint averaging.

## Phase 2: the next amendment (draft, review, freeze)

- [ ] **Setting:** harmful fine-tuning. Add harmful examples to the **editable** pool so that a0 is clearly unsafe across many harm categories.
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

- [ ] A brief for the engine changes Phase 2 needs. Review, integrate, and run the test suites.

## Phase 4: runs (each needs the user's approval of costs first)

- [ ] A validation pod: the new fixture and the measurement checks.
- [ ] Headroom v2, round 1 (sized from the noise analysis).
- [ ] Then the decision-study design (FOCUS.md stage 1).

## Log

- 5 Oct, 14:30 UTC: plan started. Round 1 is closing ($41.98 of the $46 cap).
- 5 Oct, 14:45 UTC: round 1 closed at about $42.3 (balance $35.57). The noise analysis says to use about 5 seeds and larger effects. Candidate data and judges are verified. The OLMo token check is done.
