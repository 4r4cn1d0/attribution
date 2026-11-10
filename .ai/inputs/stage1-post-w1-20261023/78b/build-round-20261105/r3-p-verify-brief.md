# R3 verifier brief: Track P (adversarial)

Read first: `B/lead/r3-common.md`. Its paths and hard rules bind you, with one change: you write only your report and
scratch, never WS. For probes, copy WS (or the files you need) into your scratch with `cp -pR` and change the copy.

- **Target:** Track P's work in WS = `B/ws-p`. Its changes against d7eb772 are in `git -C WS status` and
  `git -C WS diff` (read-only commands). Its report is `R/r3-p.md`, and its brief `B/lead/r3-p-brief.md`.
- **Lead rulings since the build:** `B/lead/rulings-set20-draft.md` (R-54 to R-58). R-54 widens P-1's seeds to
  1101-1113; that change is for the fix round, so do not report the old seed list as a finding.
- **Your report:** `R/r3-p-verify.md`; scratch `R/r3-p-verify-scratch/` only.

## Job: try to break it
1. **The computation.** The padded tokens per step must equal the engine's real padding and batching. Check the engine
   code the tool cites (path:line). Write a probe that computes the value independently on a synthetic fixture, not
   with the tool's own helpers, and compare. Also check: steps = ⌈rows / 128⌉; the seed rule (P-1); the check mode
   (P-2: exit codes, and equality against the a0 basis).
2. **Blinding and safety.**
   - No text on any path: probe every mode, every error path and every write with sentinel strings.
   - A wrong SHA-256 is refused.
   - Writes are atomic and once-only.
   - The record form is exactly K2's reader's: load it through `plan_tool.padded_tokens`.
3. **W2-4 and W2-5.** Both must be correct and keep R-20's form `{files, side_units}`. The kit's RK check must accept
   the longer list: run the 7-8B kit suite in a copy.
4. **KR5.** Track S's fixture must equal the shared form, and Track S's reader must read the kit's shared fixture.
5. **Tests and mutants.**
   - Each new rule must have a mutant that kills it.
   - Write at least 8 mutants of your own (the tool, W2-4, W2-5) and run them with the same command as the baseline.
     Any survivor is a finding; an error is an invalid run, not a kill.
6. **Suites:** scale78b (757 passed, 2 skipped, as claimed) and the 7-8B kit suite (619), under the network-deny
   sandbox.

## Report
- A findings table: id, severity (major / minor / nit), R: path:line, what, evidence (M / R), the fix.
- Then the verdict: VERIFIED, VERIFIED_WITH_MINOR or NOT_VERIFIED.
- Usage is short this round, so be economical: target the risky parts first (the computation, the blinding, the reader
  form).
