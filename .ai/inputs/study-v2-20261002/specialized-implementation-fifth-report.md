# Stage B cost-accounting follow-up (F1, F2, C1): report from "Specialized Implementation"

Date: 2026-10-03. Workspace: `tmp/claude-workspaces/study-v2-policy-20261002/workspace`.

**Routing as observed here:** the harness states this session runs `claude-fable-5-1` (the user's `/model claude-fable-5-1` output is in this chat). I cannot observe the effort setting; you say the user set HIGH. This is not `claude-opus-5-5`/max, and my statement is not verification.

**Outcome:** F1, F2 and C1 are closed in the workspace. Package suite: **165 passed, 2 skipped, 0 failed** (exit 0). The 2 skips are torch-only (`test_dp_engine.py`, one test in `test_dp_outcomes.py`), so nothing here was checked against the real engine.

## Changed files (only files I own; nothing under `.ai/`, no README/protocol, no config)

| file | + / - lines | what changed |
|---|---|---|
| `costs.py` | +67 / -15 | `COST_CONTRACT` v3; `PHYSICAL_BOUNDARY`; `controller_unknown(record)`; open-session reason; `session_allocation` and `block_physical` treat an `open` session like a missing end record for completeness (its closed segments still counted, charged by owner); module doc |
| `controller.py` | +178 / -53 | `_session_records` marks the running session `"open": True`; result/abort cost objects carry `"snapshot": SNAPSHOT_NOTE`; `_durable_costs` (the read-only core of the old `started_block_costs`); new `recorded_block_costs(root, block, result=None)`; `_snapshot_check`; `_recorded_categories(..., require_attempts=)`; `study_evidence` returns `"recorded"`; `_sensitivity_costs` uses `controller_unknown`; module doc |
| `analysis.py` | +62 / -10 | `analyze(..., recorded=None)`; `_recorded_view`; per-block `cost_source` and `physical_incomplete_because`; top-level `costs.cost_source` and `costs.physical_controller_boundary`; module doc and note |
| `__main__.py` | +7 / -3 | `_analyze` passes `recorded=evidence["recorded"]`; headline adds `physical_controller_incomplete_because` |
| `tests/test_dp_controller.py` | +302 / -24 | C1 rewritten; L847 moved to recorded costs; 3 new tests (F1, F2, ownership edge); helpers `SlowResult`, `counted_receipts`, `session`, `open_session`; `make_study(study_class=)` |
| `tests/test_dp_costs.py` | +48 / -6 | open-marker unit test; `record(..., running=)` |
| `tests/test_dp_analysis.py` | +86 / -2 | 3 new tests for `recorded`; `recorded_costs` helper |

Unified diff against the fourth candidate: `<scratchpad>/stage-b-fifth.diff` (1315 lines); SHA-256 of the 7 files: `<scratchpad>/final-sha256.txt`; pristine copy of the fourth-candidate package: `<scratchpad>/orig/pkg`. `<scratchpad>` = `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution/243bb6cc-53ef-4581-a747-392d47528efe/scratchpad`.

## Design chosen: your A-F, with the optional hardening and two tightenings

I verified your findings 1-5 against the code and the fixture numbers (846 / 1521 / 1450, common 41 per session) before building on them.

- **A. Durable records are authoritative.** `recorded_block_costs` recomputes a result-bearing block's costs from attempt receipts, session start/end records, plans and lock. It returns the result's cost shape (`actual`, the two scopes, sensitivity, or `incurred` for an abort, plus `physical`), so the analysis code paths are unchanged. `started_block_costs` keeps its output shape.
- **B. The analysis uses recorded costs** for per-block costs, differences, T, the one-off margin, complete-case means and the physical total. Only `quoted` comes from `result.json`.
- **C. `result.json` keeps its cost object as a provisional snapshot** (`"snapshot"` label, session marked `open`). A controller-written snapshot is never complete in the physical seconds or in a scope charged its last session.
- **D. Ownership contract kept as is.** A missing end record flags the physical seconds and the scopes charged that session. See "Decision for the lead" below.
- **E. `COST_CONTRACT` v3; `ANALYSIS_PLAN_VERSION` stays v4.** Estimators, family and allocation are unchanged; only the source of the cost inputs moved, which the cost contract governs. Bumping the plan needs `config.py`, the example config and `test_dp_config.py`, which I would only touch on the lead's say.
- **F. Logging boundary** stated in `COST_CONTRACT`, `PHYSICAL_BOUNDARY`, the three module docs, and emitted in the report as `costs.physical_controller_boundary`. I added one item to your list: a re-entry that only returns an existing result opens no session, so its time is also outside.

What I decided differently from your proposal:

1. **Hardening implemented** (`_snapshot_check`, about 30 lines). When the session that wrote the result has its end record, the snapshot's per-policy seconds must equal the recomputed ones exactly, attempt and start-record seconds must be equal, and physical must not be below the snapshot; otherwise `VerificationError` (CLI exit 2). Exact equality held on every tree the suite analyzes.
2. **`recorded`, when given, must cover every result**, and each record carries `result_status`, which must match the result. This prevents a silent per-block fallback to a snapshot.
3. **C1 uses `SlowResult` (9 s) in session 2**, so recorded physical is 1459 (snapshot 1450) and the uncharged term in the reconciliation is non-zero. Your 846 / 1521 are confirmed.
4. **One extra test** pins the D edge so the lead can see the exact behaviour.

Alternatives rejected: (a) trust the snapshot, which is the defect; (c) a finalized sidecar, which only moves the boundary and still needs the recomputation after a crash; an end-record-existence check on top of the snapshot, which would still report physical seconds missing the result segment and would not reproduce the economics from durable records.

## Decision for the lead (D)

If the session without its end record is identifiably research-only or other-policy-only for both policies, T stays complete, because the prespecified ownership rule puts none of that session in the selection-plus-one-chosen-model subtotals. The physical seconds, research scope and whole-research totals are lower bounds and there is no physical total. `test_a_missing_end_record_flags_only_the_scopes_charged_that_session` pins this.

Making any missing end record remove T is a small change in `costs.session_allocation`: also flag `"primary"` in the two excluded-session branches. I did not make it because it amends the cost contract.

## How each defect is closed

- **F1.** The snapshot now says it is provisional and is flagged wherever the open session is charged. The end record holds the `result` segment; `recorded_block_costs` includes it. Test: `test_a_result_s_cost_snapshot_is_provisional_and_the_recorded_costs_hold_the_result_segment` (recorded physical = snapshot + 9 s; per-policy seconds exactly equal; attempts + owner segments tile the session; block physical + static = start record + end record span; CLI total = recorded block physical + static receipts; library fallback on the snapshot gives no margin and no total; an edited end record is refused).
- **F2.** `study_evidence` no longer trusts result costs. Test: `test_a_result_whose_session_end_record_is_missing_gets_no_complete_economic_reading` covers every expectation in your item 1, including nothing written, `result.json` bytes unchanged, Y and block statuses unchanged, and re-entry executing and writing nothing.
- **C1.** The fixture was wrong, not the code. The assertion is kept and corrected to `physical + static_total == S+ total + uncharged`, with static read from the actual static receipts (== 71), and static, screen, prerequisite, attempts, setup, controller and S-'s excluded overhead each asserted separately. Completeness is asserted on the recorded costs; the snapshot is provisional for S+ and complete for S-.

## Answers to GPT's four questions

1. **Weakest assumption.** That the time after each session's final clock read (writing the end record, lock release, process exit, GPU teardown) is immaterial. It is outside every controller total by construction and nothing in this suite measures it with the real engine. Second: the ownership rule for a session that lost its end record (D above).
2. **Simpler alternative rejected.** Keep reading the snapshot and only check that the end record exists (about 10 lines). Rejected because the physical total would still omit the result segment and the economic report would not be reproducible from durable records.
3. **Counterexamples that break or limit the design.**
   - An end record whose `result` segment is edited upward after the result passes `_snapshot_check` (physical may only grow). Nothing pins session records or final-operation receipts; the check detects inconsistency, not a determined edit (who could also edit `result.json`).
   - An earlier session's end record deleted after the result makes the analysis refuse (exit 2) rather than report lower bounds, because the snapshot saw that record. Only the last session's end can legitimately never have existed.
   - A slow end-record write or process exit is invisible to all controller totals.
   - Existing v2 trees are refused by contract (their snapshots claimed completeness).
4. **Check that would change my mind.** One real-engine block run under an external wall-clock wrapper: compare process wall time with `start.seconds + end.seconds`. If the gap is material against the T tolerance, an external process record is needed. Also: any false refusal by `_snapshot_check` on a legitimate real-engine tree would mean relaxing equality to a reported flag.

## Commands actually run (from the workspace root unless noted)

`PY=/Users/spiderishi/Coding/attribution/.venv/bin/python`; suite command: `PYTHONDONTWRITEBYTECODE=1 $PY -m pytest -q -rs -p no:cacheprovider --basetemp=<scratchpad>/pytest experiments/safety_decision_policy/tests`

| when | result | exit |
|---|---|---|
| baseline, before any edit | 1 failed, 157 passed, 2 skipped (the C1 test) | 1 |
| after source edits, before test edits | 2 failed, 156 passed, 2 skipped (C1 and the L847 assertion, as you predicted) | 1 |
| `test_dp_controller.py` alone after its edits | 30 passed | 0 |
| `test_dp_costs.py` + `test_dp_analysis.py` after their edits | 33 passed | 0 |
| **final full suite** | **165 passed, 2 skipped** | **0** |

Mutation checks, run on a scratch copy of `experiments/` in the scratchpad (workspace untouched), full suite each:

| mutation | failures |
|---|---|
| no `open` marker in `_session_records` | 3 (C1, L847 test, F1) |
| CLI `_analyze` without `recorded` | 3 (C1, F1, F2) |
| `block_physical` ignores unknown controller seconds | 7 |
| `_snapshot_check` never raises | 1 (F1 tamper case) |

Also run: read-only greps/reads, three patch scripts and one exploratory script from the scratchpad. No caches written: no `.pyc` newer than my start; the workspace's `.pytest_cache` dates from 2 Oct and is untouched.

**Not run / not tested:** `test_dp_engine.py` (no torch here; it has no cost assertions that I could find, but GPT should run it); the `simulate` CLI (not in my permitted commands; its path is the same `_analyze` the tests call); anything with the real engine, GPU or held-out data.

## Names for README.md and the protocol doc

- `controller.recorded_block_costs`, `study_evidence(...)["recorded"]`, `analyze(..., recorded=)`
- `controller.SNAPSHOT_NOTE`, `controller.RECORDED_SOURCE`; result cost key `"snapshot"`; session marker `"open"`
- `costs.PHYSICAL_BOUNDARY`, `costs.controller_unknown`, `COST_CONTRACT` v3
- report fields: per block `cost_source`, `physical_incomplete_because`; `costs.cost_source`, `costs.physical_controller_boundary`; CLI headline `physical_controller_incomplete_because`
- `started_block_costs` on a block with a result now says "its recorded costs are recorded_block_costs"
- stale text to fix: README L24 and L154 ("v2"), protocol doc L177 and L212

## Limitations and open items

- A block whose last session lost its end record keeps lower-bound economics permanently; nothing repairs it (by design: results and records are write-once).
- `_snapshot_check` is consistency detection, not tamper-proofing (see counterexamples).
- The cited non-author review `stage-b-fourth-review.md` does not exist in the repo; I worked from the defects as you and GPT stated them.
- A handful of new lines are 121-122 characters, in line with existing lines in those files; there is no linter config in the workspace.
- GPT runs the authoritative checks; treat the counts above as this session's observations only.
