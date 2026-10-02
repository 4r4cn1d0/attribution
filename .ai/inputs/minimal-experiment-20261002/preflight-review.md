# GPT preflight review, 2026-10-02

Read-only non-author reviewer: native GPT minimal_date_audit, shared project context. Reviewed current code, did not author it, run scientific training, or establish research validity. This is an interim review before author completion.

Reviewed hashes: model.py dd76db15892546717e13d648a585516e2d41077ba97eb064ed8fd8a49d3c4519; run.py a91bae0bfb8b2404d8d9cf1ffa95099fe517c6f8de26a844ee94a9391a5c4677; report.py 2beb6e05afe0587b8875536e8d366c8e778b3fd36eb07a5779fee66e8c1b832e.

Material findings:
- Guaranteed false-incomplete: execute finalizes success while prior status says running, which summarize interprets as interrupted.
- Cooperative cap guards absent from long uninterruptible sequences (loading/scoring/attribution/NLLs/individual generated tokens), no final cap check. Final base evaluation can overrun without incomplete reason after status bug fixed.
- Completeness requires only eval/attribution/content record presence, not checkpoint/init/tokenization/expected successful stage evidence. Both short records at step3 instead of4 with disjoint prompt IDs create an invalid comparison. Missing checkpoint records do not enter altered-file checks.
- read_jsonl silently ignores malformed newline-terminated final line; concrete input {"kind":"ok"}\nNOT_JSON\n returns only first row. Strict eval parsing and visible recovery needed.
- Human report omits per-seed attribution/init costs though JSON has them.

Other bounded observations:
- Prepared data have no duplicate data_id across roles; helper ignores source-ID collisions but this is latent for fixed slice, not a blocker.
- One of144 prepared prompts, train:10158, differs under chunked vs canonical chat-template encoding (354vs353tokens). It starts with newline whitespace. Root verified with the actual cached tokenizer. It is not in current sampled training trajectories, removal group, query or eval, so it does not affect this exact planned computation. No leading-whitespace response among144rows. Handle/record before expanded use, don't silently edit text/hashes.
- Frozen manifest1750688b5b606d119673817e8e6d5974f877ab3acabfaa3178b42c98af6eb911. Train128,holdout6,query4,eval6;20ref untouched. Exclusions8normalized train/ref overlaps,1emptyresponse,6train duplicates.
- Seed101 baseline sees1removed row by4steps and2by16; first divergence atstep1. Seed202 sees0by4 and1by16; first divergence atstep9. Seed202 short checkpoints should be identical under deterministic execution and equal init; check this after real run rather than silently accepting unexpected divergence.
- Planned64optimizersteps,9evaluations,108generations capped64tokens,24gradientexamples. No time estimate yet. Large truncation fractions or hitting generation caps constrain interpretation.

No real scientific optimization run has occurred at this review. Environment/model gradient sanity probes and data prep only. Root ran actual-tokenizer preflight and saved preflight-check.json; worker did not run these checks.
