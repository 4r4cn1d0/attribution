Stage B cost-accounting follow-up (F1, F2, C1): implementation handed to Specialized Implementation by General Implementation, 2026-10-03

From: the "General Implementation" session (claude-opus-5-5, effort max) in /Users/spiderishi/Coding/attribution. The user explicitly asked me to route the intelligence-heavy part of this task to this chat. Report your actual model; do not claim to be claude-opus-5-5. GPT's brief pinned that model, and GPT's routing records must show the user's override.

Answers to the two points you raised with the user:
- Routing. The user set this chat to claude-fable-5-1 at HIGH effort; that is their choice, not the max that CLAUDE.md and AGENTS.md assume. CLAUDE.md is titled for Opus. Its worker rules (bounded scope, no agents, no commits, honest reporting) still apply; only the model line differs, and that difference is the user's routing decision. Your report must state the model you actually observe. If the user tells you otherwise in this chat, follow the user.
- Brief. Yes, .ai/briefs/stage-b-finalization-followup-20261003.md is the GPT lead's brief for this follow-up. The user pasted the matching task into General Implementation and asked that its hard part be done here. The scope is below. The user can confirm it in this chat.

## Rules (from the user and the project's AGENTS.md / CLAUDE.md)

- Read AGENTS.md and .ai/WORKFLOW.md first. Then read GPT's brief for this follow-up, .ai/briefs/stage-b-finalization-followup-20261003.md, for its acceptance criteria and four questions.
- You are a bounded worker. Do not:
  - launch agents or subagents, or invoke Claude or Codex;
  - commit, push, publish or install dependencies;
  - run GPU or cloud jobs, or access held-out data;
  - change the model, data, allocator or N.
- Do not edit .ai/HANDOFF.md or anything under .ai/. Preserve every earlier candidate, log and result (tmp/study-v2-20261002/**, .ai/inputs/**).
- Edit ONLY inside the prepared workspace, never the original tree:
  /Users/spiderishi/Coding/attribution/tmp/claude-workspaces/study-v2-policy-20261002/workspace
- Files you own (workspace-relative):
  - experiments/safety_decision_policy/{costs.py, controller.py, analysis.py, __main__.py}
  - experiments/safety_decision_policy/tests/{test_dp_costs.py, test_dp_controller.py, test_dp_analysis.py}
  - Touch config.py or configs/ only if strictly necessary, and say why.
- I own README.md and research/experiments/safety-selection-v2-decision-protocol.md. I will update both to match your final names after you report, so do not edit them.
- State of the workspace and evidence:
  - The workspace equals the fourth candidate byte for byte. I hashed all 30 files pinned in .ai/inputs/study-v2-20261002/stage-b-fourth-source.json: 0 mismatches.
  - The fourth candidate's report is .ai/inputs/study-v2-20261002/opus-policy-fourth-report.md.
  - Its test log is stage-b-fourth-tests.log: 164 passed, 1 failed.
  - The non-author review stage-b-fourth-review.md, which GPT's brief cites, does NOT exist anywhere in the repo. The defects below are as the user and GPT stated them.
- Tests: you may run the CPU-only package suite in the workspace. It uses synthetic engineering fixtures only. Write no caches into the workspace; from the workspace root:
  PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/.venv/bin/python -m pytest -q -rs -p no:cacheprovider --basetemp=<your scratchpad>/pytest experiments/safety_decision_policy/tests
  - .venv has numpy 2.4.6 and pytest 9.1.1 but no torch, so test_dp_engine.py will be skipped. Report skips as skips, not passes.
  - The user's instruction is: do not claim tests were run unless you actually ran them. Report exact commands and exit statuses.
  - GPT runs the authoritative checks.

## The task (the user's words, condensed)

- F1: a completed result can report its physical costs as complete, although its snapshot is taken before the session end record. Later controller time is missing from it.
- F2: a process can die after writing result.json and before writing the session end record. Public analysis then trusts the stale result costs and does not flag the missing record.
- Constraints on the fix:
  - Choose the smallest design that keeps scientific results immutable and makes the authoritative economic accounting reproducible from durable receipts.
  - A missing required session end must never yield a complete point estimate.
  - Add a regression that preserves result.json, removes its session end record, and checks that public analysis reports incomplete or unknown costs.
  - Account explicitly for the boundary around the final accounting and log writes.
- C1: fix the failing test_a_resumed_session_of_only_s_plus_work_is_not_charged_to_s_minus.
  - Its comparison omits 71 s of study-level static work: score_groups 50 s, export_view 1 s, relevance 20 s.
  - Reconcile it using the actual static receipts, and keep S+-only session costs out of S-'s policy ledger.
  - Do not delete the assertion.

## What I found in the code

Please verify this yourself. Line numbers refer to the workspace copy.

1. **F1 mechanism.**
   - controller.py `_block_result` (~L749) and `_abort_costs` (~L705) call `self._switch("result")`, then `self._session_records(block)` (~L515).
   - For the still-running session, which has no end record yet, `_session_records` substitutes the in-memory segments closed so far.
   - costs.py `block_physical` (~L503) therefore sees a dict, not None, and reports `timing_complete: True`.
   - Only afterwards does `_execute` write result.json (`_result`, ~L525). `run_block` (~L529) then calls `_end_session` (~L495). Its `_switch(None)` closes the `result` segment and writes session-<n>-end.json.
   - So result.json's `costs.physical` leaves out the `result` segment (the result computation and the result.json write), yet says complete.
2. **The omission does not affect the per-policy scopes in that snapshot.**
   - After `_switch("result")`, nothing switches owner again before `_end_session`.
   - `result` and `reuse` are UNCHARGED_OWNERS.
   - So when the end record exists, recomputing the per-policy scopes from it gives exactly the snapshot's values: the same floats summed with fsum, and canonical JSON round-trips floats exactly.
   - Only the physical seconds differ, by end["controller_seconds"]["result"].
3. **F2 mechanism.**
   - For a block with a result, `study_evidence` (~L1124) only calls `verified_result`; it never reads the block's sessions.
   - analysis.py reads `result["costs"]` in `_cost_values`, `_block_costs`, `_mean_subtotals`, `_physical_total` and the complete-case means. A missing end record is invisible there.
   - `run_block` on a block that has result.json returns `verified_result` without opening a session, so the missing end record is never repaired.
4. **C1 numbers.**
   - Session 1 runs:
     - the static work: 71 s = 50 + 1 + 20;
     - the screen: 7 × 100 s, plus a 30 s asset load recorded inside the first screen attempt;
     - S+'s prerequisite attempt 1, which fails (300 s);
     - attempt 2, a validation refusal, which is not counted.
   - Session 2 (a fresh FakeBackend) runs prerequisite attempt 3, which fails (300 s plus a 30 s load). The block then aborts (max_attempts is 2).
   - Block physical = attempts 730 + 630 = 1360, session starts 0, controller 0.
   - S+ whole = 71 + 700 + 600 + 60 = 1431.
   - Block physical excludes study-level static by design: see the `block_physical` docstring; the analysis adds the static work once. The per-policy ledgers do include static, in their `static` category.
   - So the fixture is wrong, not the code. The correct reconciliation is: block physical + static receipts total == S+ total + uncharged (result + reuse) seconds.
5. **Fake time in the tests.**
   - The fake clock advances only in `FakeBackend.execute`, so controller segments are 0 unless a test uses `SlowSteps` (test_dp_controller.py ~L108) or advances `backend.now` itself.
   - Nothing in `_block_result` calls the backend. To give the `result` segment nonzero time, a test needs something like a Study subclass whose `_result` advances `self.backend.now` before calling `super()._result(...)`.

## Proposed design

This is option (b) of GPT's brief, plus an honest snapshot. Challenge it. If you choose differently, explain why with a concrete counterexample.

**A. Durable records are authoritative.**
- Generalize the read-only core of `started_block_costs` so that `study_evidence` also recomputes the costs of every block that HAS a result.
- Inputs are the block's own durable records: attempt receipts, session start and end records, plans and lock.
  - `_recorded_categories` already recovers ownership.
  - The existing R2 test shows the recomputation reproduces the result's per-policy values.
- Expose it, e.g. as `recorded_block_costs(root, block)`, and return it in `study_evidence(...)["recorded"]` or similar.
- For a block with a result, an inventory operation (plans + lock + sensitivity) with no counted attempt should refuse with VerificationError, not be silently dropped. For started blocks, the existing filtering stays.
- Keep `started_block_costs`' output shape, unless you update its consumers and tests.

**B. The analysis uses the recorded costs.**
- They drive every economic reading of a block with a result: per-block costs, differences, T and the one-off margin, complete-case means and the physical total.
- Only the immutable quoted ledger (`costs.quoted`) still comes from result.json.
- Add an explicit parameter, e.g. `analyze(..., recorded=None)`, validate its contract and block, and have `__main__._analyze` pass it.
- Without recorded costs for a block, fall back to the result's own snapshot (see C).
- Label per block where its costs came from, e.g. `cost_source`.

**C. result.json stays immutable and keeps its cost object, labelled as a PROVISIONAL snapshot.**
- In `_session_records`, mark the running session as open, e.g. `"open": True`. Keep its closed-so-far segments, so the snapshot still records everything measured so far, once.
- In costs.py, treat an open session like a session without its end record, for completeness only:
  - give it a distinct reason string;
  - flag exactly the scopes that session is charged to, with the same branching as `_UNKNOWN_CONTROLLER` in `session_allocation`;
  - flag the physical seconds in `block_physical`;
  - flag `_sensitivity_costs` in controller.py the same way.
- Consequence: the snapshot's completeness flags equal what the recomputation would give if the end record were never written.
  - So even the library fallback path can never present a lower bound as complete.
  - The public path is complete exactly when the end record exists.

**D. F2 follows the existing ownership contract.**
- A missing end record flags the physical total and every scope charged that session.
- In the normal case, the session that wrote the result ran the policies' own work, so this removes T for the block.
- If that session was identifiably research-only or other-policy-only for both policies, T stays complete: by the prespecified ownership rule, T does not include that session. State this explicitly.
- Making any missing end remove T would be a one-line policy change, for the lead to decide.

**E. Versions.**
- Bump `COST_CONTRACT` to v3. The meaning of the result's cost object changes, and the analysis must refuse v2 results, whose snapshot claimed completeness.
- Keep ANALYSIS_PLAN_VERSION at v4 (still unconfirmed by the lead) unless you find a reason not to. Say which you chose.

**F. Logging boundary.** State it in the COST_CONTRACT text, the module docs and the label of the analysis' physical total.
- Each session's controller timer covers the span from PROCESS_START to the end record's final clock read (monotonic_end).
  - PROCESS_START is the start record's monotonic_start; the span is zero-length for a shared process.
  - Attempts (in their receipts) and owner segments (in the end record) tile that span. The `result` segment, covering the result computation and the result.json write, is included.
- Outside every controller-timed total, by construction:
  - interpreter start-up before PROCESS_START;
  - after the final clock read: assembling and writing the end record itself, returning, releasing the flock and process exit. A record cannot time its own write;
  - for a killed process, everything after its last durable record. Its controller seconds are unknown and its scopes are flagged;
  - in a shared process, the gap between one session's end and the next block's start. This already exists today; running one block per process avoids it.
- Only external process or provider records cover these. Provider billing stays separate and authoritative.
- This reconciles the user's "record every cost": every second between PROCESS_START and the final clock read is recorded exactly once. The only exclusion is this named, prospectively defined boundary.

**Simpler alternatives I rejected:**
- (a) Trust the snapshot: that is the defect itself.
- (c) A finalized economic sidecar written after the end record:
  - its own write falls outside every record, so the boundary only moves;
  - a crash between the end record and the sidecar needs the recomputation anyway;
  - so it adds a file and a failure mode without adding information.
- A hybrid that only checks for the end record (snapshot per-policy values plus an existence check): a smaller diff, but the economic report would not be reproduced from durable records.

**Optional hardening (your call):** keep it small, or skip it and list it as a limitation.
- When a recorded scope is complete, require the snapshot's per-policy totals to equal the recomputed ones exactly, and the recorded physical to be ≥ the snapshot physical.
- A mismatch means the records changed after the result, so refuse.
- The lock pins neither final-operation receipts nor session records. Without this check, edits to them after the result go unnoticed.

## Tests to add or update (precise expectations)

1. **F2 regression** (test_dp_controller.py).
   - Setup: a single-block study in its own fresh process, so setup is measured and the control is complete. Use SlowSteps so the session has nonzero controller seconds; the lower bound must visibly exclude them.
   - Control: the CLI `analyze` (`main(["analyze", ...])`; see the `cli_analyze` and `frozen_folder` helpers) reports block 0 complete, with a finite `cost_margin` and a non-null `physical_controller_seconds`.
   - Then copy the tree, keep result.json and delete blocks/0/sessions/session-1-end.json. CLI analyze must:
     - exit 0 and write nothing into the tree: tree_hashes and the result.json bytes unchanged;
     - report block 0 with `physical_seconds_are == "lower bound"`;
     - set `cost_margin`, `selection_cost_difference`, `one_off_cost_margin` and `difference` all to None;
     - label both policies' selection scope "lower bound", with a reason naming the missing end record;
     - report `physical_controller_seconds is None`;
     - report `physical_controller_seconds_recorded` == attempts + start records + static, with none of that session's controller seconds;
     - leave block 0 out of `endpoints.cost_margin.observed_blocks`;
     - keep its scientific endpoints unchanged (Y still observed).
   - Also check that `run_block` re-entry on that tree executes nothing and writes nothing.
2. **F1 regression.**
   - Setup: a complete block whose `result` segment takes nonzero fake time, e.g. a Study subclass that advances `backend.now` by 9 s in `_result`.
   - Expect:
     - result.json's `costs.physical.timing_complete is False` with the open-session reason, and its per-policy scopes flagged provisional;
     - the end record's `controller_seconds["result"] == 9`;
     - the recorded physical seconds are complete and == the snapshot physical + 9;
     - the recorded per-policy scope seconds == the snapshot values, exactly;
     - the CLI analyze physical total == the recorded block physical + the static receipts;
     - tiling: end.seconds == every non-refused attempt tagged with that session (static ones included, gross) + sum(end.controller_seconds).
3. **C1 correction** (the failing test).
   - Keep the physical assertion, corrected to: physical.seconds + static_total == S+.total_seconds + uncharged.
   - Read static_total from the actual static/*/attempt-*/receipt.json files, and assert it == 50 + 1 + 20.
   - Check the components separately:
     - the static category == static_total for both policies;
     - screen == 700 for both;
     - S+'s prerequisite seconds == 600, net;
     - physical.attempt_seconds == 1360, gross;
     - setup: S- == session 1's start + 30; S+ == both sessions' starts + 60;
     - S-'s `excluded_other_policy_overhead` == session 2's start + 30 + its charged controller seconds, with sessions [2];
     - S+ − S- == 600 + S-'s excluded overhead + session 1's S+ controller seconds.
   - Check completeness on the RECORDED costs:
     - S+'s snapshot is provisional, because session 2 was still open when it was taken;
     - S-'s snapshot stays complete, because session 2 is not charged to S-.
   - Strengthen the fixture with nonzero controller and session-start time, e.g. SlowSteps(verify=2, evaluation=3) in both sessions and advancing backend.now by 4 s before each run_block. With those values I expect:
     - each session's controller seconds: common = 41, S+ = 0, result = 0;
     - S- = 846 and S+ = 1521;
     - block physical 1450 = 1360 + 8 + 82, and physical + 71 = 1521.
     Compute the expectations from the records; do not rely on my arithmetic.
4. **Existing assertions that assumed a complete snapshot.**
   - test_dp_controller.py L804 (in the C1 test).
   - test_dp_controller.py L847: `result["costs"]["physical"]["timing_complete"] is True`, in the controller-seconds test.
   - Move those completeness checks to the recorded costs, and assert that the snapshot is provisional.
   - Every other existing test should pass unchanged; if one doesn't, explain why.
5. **Unit tests in test_dp_costs.py for the open marker.**
   - An open session's measured segments are counted once in block_physical and charged by owner.
   - It is flagged with the open reason for exactly the scopes it serves.
   - An open session that ran only the other policy's work leaves the bystander policy's scopes complete.
6. **test_dp_analysis.py.**
   - Recorded costs replace the snapshot:
     - a provisional snapshot plus complete recorded costs gives a margin computed from the recorded costs;
     - a complete-looking snapshot plus recorded costs with a missing end gives no margin and a null physical total.
   - Recorded costs of another contract or block, or for a block without a result, are refused.

## Report back

Send the report to the session "General Implementation" with SendMessage, and also keep the full report in your own reply. Include:
- the changed files (workspace-relative), with a short diff summary for each;
- the chosen design, the alternatives you considered, and why;
- answers to GPT's four questions: the weakest assumption; the simpler alternative you rejected and why; the exact counterexample that would break your design; the check that would change your mind;
- how F1, F2 and C1 are closed, or why one is not;
- every command you actually ran, with its exit status and the test summary line (passed, failed and skipped counts);
- remaining limitations, and anything you decided differently from this proposal.

After that, I will update README.md and the protocol doc to your final names and semantics, re-run the suite independently, and report to GPT.
