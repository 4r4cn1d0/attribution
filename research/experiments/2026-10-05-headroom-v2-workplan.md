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

- [x] Brief `.ai/briefs/headroom-v2-engine-20261005.md` built by the Specialized chat, reviewed and integrated (`5efc765`; engine `0d55658c…`). Tests: 269 engine tests passed (plus 3 CUDA-only skips), 172 Stage B, 260 durability.

## Phase 4: runs (within the D7 budget rule: the most the balance allows, with a $6 reserve)

- [x] A validation pod (val05): the new fixture and the measurement checks.
- [x] Calibration: a0 at 5% (val05) and at 10% (cal10, still evaluating). **5% chosen.**
- [~] The lead pod: row scores, removal files, rewrites, all edit files for k = 507.
- [ ] The positive control: rewrite-k507 and random-rewrite-k507 at seed 1101 (paired with calibration's a0), then seed 1102, then a0 seed 1102, as the balance allows.
- [ ] Then the decision-study design (FOCUS.md stage 1).

## Pending, waiting on results (added 6 Oct, user's request)

- [ ] **Outreach email drafts (a subagent; drafts only, the user sends).**
  - **Trigger:** the v2 positive-control result plus the Mac second-judge check. For Grosse, preferably also the cheap ranking-and-timing check (classifier vs RepSim/DRA vs gradient similarity, with timings), which is not yet scheduled.
  - **Recipients:**
    - Jiaqi W. Ma (Pan et al. and DATE-LM): a seed-repeated replication of their removal comparison;
    - Roger Grosse: how to charge EK-FAC/SOURCE's one-off cost against extra runs at matched compute;
    - EleutherAI (Bergson): attribution for LoRA models.
  - **Each email:** about 150 words, one concrete development result, one specific question, a link to the design. Verify affiliations and contacts from public pages. Save the drafts under `writing/outreach/`, and offer Gmail drafts.

## Log

- 5 Oct, 14:30 UTC: plan started. Round 1 is closing ($41.98 of the $46 cap).
- 5 Oct, 14:45 UTC: round 1 closed at about $42.3 (balance $35.57). The noise analysis says to use about 5 seeds and larger effects. Candidate data and judges are verified. The OLMo token check is done.
- 5 Oct, 15:05 UTC: literature check done (Fraser et al. 2025; Larsen 2025). Headroom v2 amendment drafted, estimated at $55–85 (a cheaper variant $45–65), which needs a top-up. Waiting on the user's decisions D1–D7.
- 5 Oct, about 20:45 local: the user approved D1–D6. Budget: no top-up ("do the max you can with the funding… not lose anything"), so Part 7 of the draft plans within the balance and holds a $6 reserve.
  - Round-1 model states: the two a0 adapters were backed up (591 MB, verified) and the other 69 files (about 18 GB) deleted, at the user's choice.
  - The v2 sources are downloaded and pinned (contents unread).
  - A local second-judge check (Granite Guardian 3.3 8B, Q4_K_M via llama.cpp on the Mac) is set up, waiting for the model download.
- 5 Oct, 18:23–19:02 UTC: validation pod val05 (A100 SXM).
  - **The preflight passed with `pc2-mb4`** (SDPA, micro-batch 4 × 2). `pc2` (micro-batch 8) ran out of CUDA memory.
  - Every check passed: the fixture is exact, batched equals single for greedy and sampled answers, and the trained rows are separated from padding.
  - Expected fixture `5e81e8c8…`.
  - Measured: training is 3,996 steps at about 0.94 s per step (about 68 minutes). The evaluation upper bound is 8,301 s.
- 5 Oct, 19:07 UTC: cal10 created on its second try (no A100 was free at first). Its preflight matched the fixture on a second machine.
- 5 Oct, 19:06 and 19:32 UTC: operator leases moved the stop times to 23:15 (val05) and 23:40 (cal10), so a long evaluation cannot be cut off. The finisher still stops each pod when its job ends. `budget.py` does not yet count leases (the patch was refused by the permission classifier; the user has to decide).
- 5 Oct, 20:58 UTC: **calibration result, val05** (a0, 5% injection, seed 1101, e3; development banks; Qwen3Guard):
  - harm bank: **74.5% unsafe greedy (149/200), 76.3% sampled (458/600)**; mean continuous unsafe score 0.75;
  - answers end: 1 of 200 greedy and 3 of 600 sampled answers hit the cap;
  - ARC accuracy **0.841** (159/189);
  - over-refusal: 2 refusals out of 100 (35 of those 100 answers were judged unsafe; the bank has borderline OR-Bench prompts);
  - ToxicChat development: 25 of 72 unsafe (round-1 a0: 14 and 11).

  **The setting works at 5%, so k = 507.** The job took 114.6 minutes from start to finish. The record was verified and the pod stopped.
- 5 Oct, 21:07 UTC: the lead pod was created (role `lead`, prepared-v3-inj05, cap 4.5 h; the guard allowed it with a $28.07 balance). cal10 continues as a dose-response point.
- 5 Oct, 21:31 UTC: **calibration result, cal10** (a0, 10% injection = 1,015 rows, seed 1101, e3; development banks; Qwen3Guard):
  - harm bank: **81.0% unsafe greedy (162/200), 83.5% sampled (501/600)**; mean continuous unsafe score 0.82;
  - capped answers: 4 of 200 greedy, 0 of 600 sampled;
  - ARC 0.831; over-refusal 3 of 100 (39 judged unsafe); ToxicChat 27 of 72 unsafe.

  **The dose response flattens:** 5% gives 74.5% and 10% gives 81.0% (greedy). The job took 116.0 minutes; the record was verified and the pod stopped. The 5% choice stands.
