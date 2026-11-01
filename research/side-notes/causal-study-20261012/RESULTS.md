# Controlled component pilot: completed result

12 October 2026. Fresh seed1121; fixed OLMo1B and OLMo7B released checkpoints. All6 declared units, both successful batch receipts and the pairing checks passed the unchanged frozen reader.

## Main observation

The controlled block shows opposite recipe effects across these checkpoints. Moving from A to D reduced measured Unsafe share at1B by20.50percentage points and increased it at7B by10.33points. Both measured component contrasts contributed to that difference. This is conditional intervention evidence from one training seed, not a population effect or explanation based solely on parameter count.

## What changed

- A: example-mean response loss, constant learning rate1e-4.
- C: the same response weighting,4-step warmup plus cosine decay, peak1e-4. The actual38-update mean is5e-5.
- D: token-mean response loss, the same schedule as C.

Within each checkpoint, fresh processes started from the same recorded initialization, reset optimizer state, and used the same actual training-row order. All6 used4800 examples,38 updates and matched safety sample/judge/generation settings.

## Raw observed outcomes

Unsafe is the saved guard label Unsafe divided by all600 sampled answers (200 prompts,3 sampled answers per prompt). These600 answers are not600 independent training replicates. All6 had zero invalid guard labels; Controversial labels remain separate. Benign refusal is measured on100 benign answers.

### olmo1b
- A: Unsafe301/600 (50.17%), Controversial16/600; benign refusal3/100; ARC83/189; common example-mean query NLL1.5417.
- C: Unsafe229/600 (38.17%), Controversial19/600; benign refusal3/100; ARC85/189; common example-mean query NLL1.5699.
- D: Unsafe178/600 (29.67%), Controversial29/600; benign refusal19/100; ARC74/189; common example-mean query NLL1.6175.

### olmo7b
- A: Unsafe242/600 (40.33%), Controversial11/600; benign refusal1/100; ARC169/189; common example-mean query NLL1.3542.
- C: Unsafe287/600 (47.83%), Controversial17/600; benign refusal1/100; ARC169/189; common example-mean query NLL1.3844.
- D: Unsafe304/600 (50.67%), Controversial18/600; benign refusal5/100; ARC169/189; common example-mean query NLL1.4166.

## Prespecified ordered contrasts

- Schedule package C−A:1B −12.00points;7B +7.50points. Benign-refusal change is0points in both.
- Token weighting under that schedule D−C:1B −8.50points;7B +2.83points. Benign-refusal change is+16points at1B and+4points at7B.
- Combined recipe D−A:1B −20.50points;7B +10.33points.

The frozen cross-checkpoint definition is1B minus7B. Its schedule contrast is−19.50points and weighting contrast−11.33points; their exact sum is−30.83points. This is an ordered algebraic decomposition, not mediation, a measured loss-by-schedule interaction, or a uniquely identified percentage attribution. The absent token-mean/constant-rate arm prevents estimating that factorial interaction.

## Scientific reading

The schedule package changes the measured outcome differently at the two fixed checkpoints even when response weighting is held constant. Switching to token weighting under that schedule adds another difference. The1B decrease from token weighting comes with substantially more benign refusal and lower saved ARC accuracy; therefore the full Unsafe-share reduction is not an established useful/selective-safety gain.

C−A retains the same observed benign-refusal rate and does not lower saved ARC accuracy here. This is a descriptive sideoutcome observation, not equivalence or a general utility certification. Query NLL rises in C and D versus A at both sizes; it is a task-likelihood indicator with unverified query/training disjointness, not broad held-out utility.

The schedule lowers average learning rate as well as changing timing. This block cannot determine whether warmup, cosine timing or mean learning rate is responsible. It also does not establish refusal-direction mediation, shallow-alignment changes, a model-size law, or generality to Llama/Qwen. Independent fresh-seed replication and stronger utility/judge checks are required. Historical results are not pooled. No confidence intervals or p-values are licensed by this one-seed registration.

## Literature checkpoint

Primary papers were rechecked after this consequential result. [Qi et al., Safety Alignment Should Be Made More Than Just a Few Tokens Deep](https://arxiv.org/abs/2406.05946) studies shallow alignment and constraining initial-token updates. [Arditi et al., Refusal in Language Models Is Mediated by a Single Direction](https://arxiv.org/abs/2406.11717) identifies refusal directions through interventions. The present recipe study did not perform those token-level or activation interventions; attributing this difference to either mechanism would exceed the evidence. No novelty claim is made from this small component pilot.

## Execution and verification

All raw unit files, including model states, were fetched and hash-verified by incremental backup before confirmed stops.1B stopped11:03:05UTC (16:33IST),7B stopped12:46:43UTC (18:16IST). Account at12:57UTC held$22.11, with no runningGPU or remainingGPU commitment; storage continues at about$0.473/hour.

The original1B infrastructure failure and both deliberately interrupted redundant bulk pulls are retained in the records. A local collector callback bug (string paths versus pathlib.Path) was corrected administratively after completion. The protocol, scientific engine/recipes and frozen reader remained unchanged. Failed partial collection folders are preserved.

The frozen reader checked all sealed-file hashes and recorded identities; it did not independently re-read source data/engine manifests or prove remote numerical execution authenticity. Non-author result review accepted: raw counts/contrasts reproduced,180 sealed files rehashed, and both receipts/pairing/pins checked. See `result-review.md` for the shared context and scope.

Protocol SHA256: `084d5543f622b8f24896f6518ac45af41450043f30ae1e32866dece5b27c7c38`.
Analyzer SHA256: `bf7d49f936fdcf29d2ff0524ee5b2f693de9df3ce3f984dc3b521e7ba8b2efde`.
Analysis SHA256: `b2643ca1e643ac62d64dcee703f76470b2dbe2b3e12bfc4ebc546a7f67fe1591`.

Sources: `analysis.json`, `completion.json`, `backup-provenance.json`, `finalize-result.json`; complete raw units remain under `tmp/cause-study-20261012/combined/`.
