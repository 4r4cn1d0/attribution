# Stage B fifth candidate: review and integration record

3 October 2026. Written by the General Implementation session, acting as lead at the user's instruction (no GPT brief).

- Implementation: Specialized Implementation.
- Brief: `stage-b-fifth-brief.md`.
- Author report: `specialized-implementation-fifth-report.md`.
- Routing: `stage-b-fifth-routing.json`.
- Source pin: `stage-b-fifth-source.json`.

**Independence caveat.** I proposed the design in the brief. So this is a review of code written by another session and model, not an independent review of the design itself.

## What was checked

1. **Changed-file set.** Exactly 7 files changed from the fourth-candidate pin, and their hashes matched the author's list. The fourth-candidate verify copy, `tmp/study-v2-20261002/stage-b-fourth-verify`, was unchanged. I updated README.md and the protocol document myself.
2. **Line-by-line diff review** of costs.py, controller.py, analysis.py, __main__.py and the three test files, against the frozen fourth copy.
   - The open-session marker and `controller_unknown` replace every `controller is None` completeness check and keep the counted seconds.
   - `recorded_block_costs` and `_durable_costs` share one read-only core with `started_block_costs`; the output shape of `started_block_costs` is unchanged.
   - When recorded costs are supplied, `analyze` requires them for every result, with a matching status, and never mixes them with snapshot values.
3. **Exact-equality soundness of `_snapshot_check`.**
   - `canonical_json` is plain `json.dumps`, whose float repr round-trips exactly.
   - The snapshot and the recomputation sum the same multisets of floats with `math.fsum`.
   - After `_switch("result")`, only the uncharged `result` owner accrues.
4. **Tests in the pinned engine environment** (`tmp/minimal-experiment-20261002/venv`: torch 2.8.0, transformers 4.56.2, peft 0.17.1, numpy 2.2.6, pytest 8.4.2, matching `experiments/minimal_safety/requirements.lock`).
   - Run from the integrated project: 172 passed, exit 0 (`stage-b-fifth-tests.log`). The engine tests are included.
   - The 12 warnings are the known BLAS-reference warnings of `test_dp_ridge`.
   - In `.venv` without torch: 165 passed and 2 skipped (the torch-only tests).
5. **Synthetic `simulate`.** Exit 0, two complete blocks, physical total 19381.0 s, identical to the fourth candidate. Both blocks were read from recorded costs, and each snapshot was reproduced with 0 s beyond it (`stage-b-fifth-synthetic.log`).
6. **Adversarial tree shapes** that the tests do not route through `study_evidence`. All 9 pass (`stage-b-fifth-adversarial.log`; script `stage-b-fifth-adversarial-scenarios.py`). No legitimate tree was falsely refused. The shapes:
   - two blocks in one process with controller time;
   - a final-incomplete block;
   - identical choices;
   - a screen abort;
   - an interrupted block, resumed;
   - a refused block, resumed;
   - a hard kill, resumed;
   - a result-writing session 2 that lost its end record;
   - a complete block beside a started one.

   The two lost-end-record shapes report lower bounds and no physical total.
7. **Integration.**
   - The engine and dependency files in the workspace are byte-identical to the project's current files.
   - All 10 protocol links and the README links resolve in the project.
   - None of the 30 paths existed in the project, so the copy was a pure addition with any overwrite refused. Post-copy hashes are equal.
   - The test and `simulate` runs left the project's `experiments/`, `research/` and `.ai/inputs/` byte-identical.

## Findings

- No defect found in F1, F2 or C1 as implemented. Every acceptance criterion of the lead's brief that can be checked without the real engine holds.
- Documented behaviour, not a defect: an earlier session's end record deleted after the result makes the analysis refuse rather than report lower bounds. This is protocol open decision 15.

## Open and not tested

- **Open decisions 13–15** in the protocol:
  - 13: a missing end record removes T only where its session is charged to a subtotal;
  - 14: the size of the logging boundary has not been measured with the real engine;
  - 15: the strictness of the snapshot check.
- **Versions.** The cost contract is v3 and the analysis plan stays at v4; the lead confirms both.
- **Real engine.** Nothing here ran the real engine, a GPU or held-out data.
- **Permanence.** A block whose last session lost its end record keeps lower-bound economics permanently.
- **Missing file.** `stage-b-fourth-review.md`, cited by the lead's brief, is not in the repository.
- **Not yet done.** The integration is not committed, and `.ai/HANDOFF.md` has not been updated: the user's instruction for this task excluded editing it.
