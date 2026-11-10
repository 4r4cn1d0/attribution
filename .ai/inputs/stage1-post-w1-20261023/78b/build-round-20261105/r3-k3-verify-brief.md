# R3 verifier brief: K3 (adversarial), items 1-12 and 14

Read first: `B/lead/r3-common.md`. Its paths and hard rules bind you, with one change: you write only your report and
scratch, never a worktree. For probes, copy files into your scratch with `cp -pR` and change the copy.

- **Target:** WS = `B/ws-k3v`, a frozen copy of K3's work as of 2026-11-09T14:23 UTC. Its changes against d7eb772 are
  in `git -C WS status` and `git -C WS diff` (read-only commands). K3 goes on with item 13 in `B/ws-k3`, which is not
  yours.
- **Builder's report:** `R/r3-k3.md`. Its brief: `B/lead/r3-k3-brief.md`.
- **The lead's rulings since the build:** `B/lead/rulings-set20-draft.md`, sets 20-21.
- **Not findings** (the fix round or item 13 takes them): item 13; R-59, R-60, R-63, R-65, R-66, R-67.
- **Your report:** `R/r3-k3-verify.md`; scratch `R/r3-k3-verify-scratch/` only.

## Job: try to break items 1-12 and 14. Riskiest first:
1. **The wrapper's real interface.** Every O-ext command line the runner builds must parse and run under
   `scripts/scale78b/oext_78b.py`'s real command-line interface. Probe each built line with the wrapper's own argument
   parser and a fixture index. Also check the W1-18 command, its files list (R-20) and the record names (R-53).
2. **R-47.** Does a run under Branch full with a pinned failing W1-18 record need the record at run time? Answer it with
   your own fixture probe through the unchanged `oext_eval`, not the builder's test.
3. **Blinding.**
   - Nothing new prints or writes an outcome value (U, HarmBench, O, L, coherence) on any path, error paths included.
   - The anchor-stop read follows O6 and KR4.
   - Record-done's printout is unchanged.
4. **Block 0 and money.**
   - Block 0 is unchanged: plan.json byte for byte, its printout, caps and funding need.
   - Block A and B arm jobs that now carry the O-ext step also carry K1's ×1.5 cap term.
5. **N's regenerations.**
   - Sealed edits are taken only by pin, and acceptance is against `n_complete`.
   - Keys are (arm, seed): OLMo's R_1101 and a0-1101, which share seed 1101, give two separate pods.
6. **Engine Y.**
   - Y refuses while `ENGINE_Y` is null, and the frozen tree's identity is checked.
   - The unchanged `oext_unit.py` is packed.
   - `y-remeasure.json` is written, and measured kinds refuse until `Y_MEASURED`.
7. **The seed-only form** is gone: no caller is left anywhere in the kit.
8. **The pack's Mac checks** (R-6, R-9, R-23) refuse on any failure. The S1 edit is read by path and pin only.
   `--dev100-source`'s packed folder (R-61) is checked against RUN1B, and carries nothing the pod must not read.
9. **Mutants.**
   - The re-targeted older mutants (marked "note_r3") still test the same rule.
   - Run the scorer spec's 198 mutants that the builder did not re-run, in shards under 10 minutes.
   - Write at least 10 mutants of your own on the riskiest new code. Any survivor is a finding; an error is an invalid
     run, not a kill.
10. **Suites:** the 7-8B kit (639 claimed), the stage-1 kit (762) and the engine family tests (95), under the
    network-deny sandbox.

## Report
- A findings table: id, severity (major / minor / nit), R: path:line, what, evidence (M / R), the fix.
- Then the verdict: VERIFIED, VERIFIED_WITH_MINOR or NOT_VERIFIED.
- Be economical: the riskiest parts first.
