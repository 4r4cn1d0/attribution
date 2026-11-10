# R3 reviewer brief: K3's safety lens (adversarial; fresh eyes)

Read first: `B/lead/r3-common.md`. Its paths and hard rules bind you, with one change: you write only your report and
scratch, never a worktree. For probes, copy files into your scratch with `cp -pR` and change the copy.

- **Target:** WS = `B/ws-k3v2`, a frozen copy of K3's final work. Its changes against d7eb772 are in
  `git -C WS status` and `git -C WS diff` (read-only commands).
- **What else to read:** the builder's report `R/r3-k3.md`, its brief `B/lead/r3-k3-brief.md`, the lead's rulings
  `B/lead/rulings-set20-draft.md` (sets 20-24), and the first verifier's report `R/r3-k3-verify.md`. A second
  verifier re-checks correctness and the earlier findings, so your lens is safety only.
- **Your report:** `R/r3-k3-safety.md`; scratch `R/r3-k3-safety-scratch/` only.

## Job: try to break the safety rules in K3's new code (item 13, its fixes and R-59 to R-78)
1. **Blinding.**
   - No new Mac-side path prints or writes an outcome value (U, HarmBench, O, L, coherence, judge verdicts), error paths
     included. This covers block B's planner and release checks, `record-y-measured` and the pack.
   - The certification check reads only the report's verdict field.
   - The terms records carry no outcome value.
   - Probe with planted sentinel values in fixture outputs.
2. **Secrets.** The Llama token path is used for the W1-18 pod's Llama tokenizer (R-66) and for Safe LoRA's base model
   (R-71). Check that:
   - neither download can run without that path;
   - the HF token is never written to plan.json, job.json, logs, records or packed files, beyond what the frozen 1B
     token path does;
   - the pack's secret scan covers every newly packed file (the safety-prompt file, the refs settings, the terms
     records, the source units).
3. **Sealed files.**
   - The S1 edit and the R_d edits are taken by exact path and pin only; no sealed file's content is read on the Mac.
   - `source_unit` packs only the files that COMPLETE.json lists (R-76).
4. **Money.**
   - Every new kind has a cap: `b10_certify`'s E cap, and the reference kinds with the O-ext ×1.5 term.
   - In-pod stop timers still apply.
   - No new path creates or extends a pod without the budget check.
   - Block 0's printout, caps and funding need are unchanged.
5. **Stop, never delete.** No new code path deletes a pod, a unit's states or a record.
6. **Refusals fail closed.** Every new pin (`REFS_78B`, `Y_MEASURED_RECORD`, the base-model revisions) refuses while it
   is null. A missing or wrong pod file refuses on the pod (R-75).

Write mutants for the riskiest safety checks, and run them with the same command as the baseline. Any survivor is a
finding; an error is an invalid run.

## Report
- A findings table: id, severity (major / minor / nit), R: path:line, what, evidence (M / R), the fix.
- Then the verdict: VERIFIED, VERIFIED_WITH_MINOR or NOT_VERIFIED.
- Be economical: the riskiest parts first.
