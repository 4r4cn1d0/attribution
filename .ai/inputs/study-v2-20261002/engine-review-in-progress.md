# Stage A code review in progress

2 October 2026. The author is still implementing. This record is not clearance of
the unfinished package, and contains no scientific model outcomes.

## Non-author GPT data/stream review

Read-only reviewer examined common/config/sources/textproc/stream/prepare/ledger.
No tests, training or outcome reads were performed by that reviewer.

1. P2: ARC overlap checks compare the bare question, whereas model input contains
   the rendered question/choices and, for MC, an instruction. A training prompt
   identical to a rendered evaluation prompt can pass. Require checking bare and
   both rendered forms and actual emitted prompt overlap. Root checked all pinned
   ARC validation/test forms against all original DATE train/ref prompts: zero
   actual collisions. This is a preventive correctness fix, not discovered
   contamination of the current data. Receipt: public-metadata/rendered-overlap-audit.json.
2. P2 interface condition: the engine manifest includes construction seed and
   compositions, making opaque groups' hidden composition recoverable. Stage B
   must receive only a verified whitelisted selector view, never Prepared or the
   full manifest. Alternatively move recoverable construction data to auditor
   storage. The current manifest already names X0_STATIC as selector scope; no
   selector exists yet, so an actual feature leak has not been observed. Test the
   final boundary rather than claim filesystem security against an adversary.
3. Reviewer requested checking duplicate raw data_id with different prompts.
   Root checked all pinned DATE train/ref rows: zero duplicate data_id groups.
   No current-data defect exists on this point.
4. Shared shuffle/drop, partial batches, exposure counts and checkpoint rounding
   are consistent with fixed-epoch removal in the reviewed snapshot. No token
   target-boundary bug found. NaN config numbers are rejected by canonical hashes;
   entrypoints still need to hash/validate before expensive work.

Reviewed hashes:

```
common.py   614264aa9a8a09cb5d7f1531149e26a4d0951a196237ba5c7fc29dabbf07a034
config.py   411c7313466fd8277cff10de0b4c89b09479a002871a98003080646e1f2a7ebd
sources.py  ca01704ea4a896719eba71fa4e0cb4e538e7822c252c394263bca932eeb25893
textproc.py 39392aa11717e57a7debaa4cc6322684a3cb26503a46ac9914177da86413a19e
stream.py   a8ed245fafbd8cfe86db305c1cce47c7eade6f155926fd4ad769a92145d26ce1
prepare.py  5e5066cbcc87770af65ea7efd4f591fef12ac07b96dc0bdcad6bacd790e69e1e
ledger.py   9ffec2e64d4d51c3116fb6351f874fe448274384cd0a0d6bb617ad41798a5873
```

## Lead engine reproduction

P1 fail-closed violation in current engine._greedy_batch: it takes argmax without
checking decoder logits for nonfinite values. A CPU engineering fixture returning
all-NaN logits and using stop token 0 is accepted as an empty EOS completion.
Receipt: nonfinite-decoding-repro.json. This is **not** a claim that the pinned
scientific model has produced nonfinite activations. It demonstrates that a
numerical failure could become an apparently completed measurement. Check logits
before argmax on prefill and every decode step; similarly reject nonfinite
teacher-forced scores before completed output. Test NaN and infinity explicitly.

Other follow-up items for the author: continuous guard label-sequence scores for
the strong content baseline; real-data preparation; preserve the distinction
between deterministic fixed-batch execution and cross-batch numerical equivalence;
the final selector must not import construction information as features.

## Additional non-author review and lead verification

- P1: example_gradient accepts a finite gradient from an infinite loss. The lead
  reproduced logits[-Inf,theta], target0: infinite CE and returned gradient[1.0].
  target_logprobs also returns a nonfinite score. Receipt: nonfinite-loss-repro.json.
- P2: allocate_seeds constructs set(range(first,last+1)) for a membership count;
  a large valid namespace can exhaust memory even for one requested seed.
- P1: calibrate's reuse by seed/arm/checkpoint folder name ignores current
  manifest/recipe/code/evaluation identity. A new generation ceiling can silently
  reuse old outcomes. Compare complete requested/stored coordinates before reuse.
- P2: attribution does not enforce a common source code version and discards
  collected source adapter/optimizer/code receipts. Persist and validate them.
- P2: downloaded dependency chains require read-only path mapping; do not rewrite
  hashed jobs. Verify eval/attribution sources as well as run-one resume chains.
- Cost condition: stage/trajectory sums omit some setup, verification, saving and
  hashing. Stage B needs immutable external operation-time receipts plus charged
  setup/failures and the separate billable-process ledger.

The reviewer found no additional loss weighting, gradient formula, ARC tie or
guard-parser defect in the reviewed snapshots. These are code-review conclusions,
not test results or scientific evidence. Root ran the author's completed data and
stream tests during implementation:24 passed in0.32s; this is only a partial test
run, and the implementation is still changing.
