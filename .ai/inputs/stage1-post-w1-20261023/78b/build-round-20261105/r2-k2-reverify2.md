# R2 K2 second re-verification: the follow-up for K2R-1 to K2R-4 (GXB R-49 to R-52)

Started 2026-11-09 08:43 UTC; written 08:48-09:00 UTC (`date -u`). Target: B/ws-k2 after the follow-up. M: plan_tool.py
`591c2d58…`, tests/test_planning_ab_78b.py `8a61e255…`, tests/mutation_spec_scorer_78b.json `af8efa56…` (the builder's
table); orchestrate.py `6abdea19…` and every other kit file unchanged since the fix round (M: shasum; the pre-copies
in R/r2-k2-scratch/fupre/ hash to the fix round's values). My own diffs against fupre/: plan_tool.py 237 lines, the
test file 277 lines (R/r2-k2-reverify2-scratch/pt.diff, tp.diff). I edited nothing in ws-k2 or MAIN; ws-k2's `git
status` is as the builder left it, with no `__pycache__`, also after the in-process blinded_sigma read (M). Sandboxed
runs; no network, pod, spend or message. Tags: M measured (a command or a probe test), R read (path:line, WS), E
estimate, I inference.

## Verdict

**VERIFIED_WITH_MINOR.** K2R-1 to K2R-4 are closed: an edit of any of the four files after the blinding record
refuses at sr2_status, record-plan-b-78b, init-block B and release B, and still at block A's init and release (R-49);
record-plan-b-78b re-derives sigma_A and df with blinded_sigma.py's own read and refuses a wrong sigma, df, type or
script, printing sigma_A and df only, with no planted value on any path I tried (R-50); the part replacement takes
only a kit requeue record's cells and refuses every other change I made, and refuses while the merged inputs file
exists (R-51); the two test gaps have tests and killed mutants (R-52). No regression: block 0 byte for byte, the
blinding probes, K2V-1 to K2V-11 and my earlier probes behave as before or better. One new Minor item (K2R2-1).

## Defects

| Id | Severity | File:line (WS) | Defect | Failure scenario | Fix |
|---|---|---|---|---|---|
| K2R2-1 | Minor (robustness) | runkit/stage1-78b/plan_tool.py:4809-4812 (write_blinded_part: `open(new, "xb")` for `<part>.new`, then `os.replace`), called from record_done | A `<part>.new` file left by an interrupted replacement makes the next replacement raise an unhandled FileExistsError. record_done catches only SystemExit, so record-done ends in a traceback after plan.json was saved (the host recorded done) and before the operator log and the printout. | M (probe N4e): requeue --rerun-mismatched, re-run pulled, a stale `blinded-sigma-inputs-part__olmo2-7b.json.new` present: record-done crashed with FileExistsError; plan.json shows the host done; a later record-done of that host meets the same file and crashes the same way until it is removed (I). No value is printed (the error names a path only, I). | Remove a stale `.new` first (or write the temporary file under a unique name) and turn any OSError of the replacement into a names-only refusal; a test. |

## 1. K2R-1 / R-49 (closed)

M (R/r2-k2-reverify2-scratch/test_k2r2_probe.py, run in a scratch repo copy of ws-k2, sandboxed):
- N1 (four cases): after block A (OLMo-2-7B, [C]) and the merged inputs file, an edit of each file the record names
  (the A copy's plan_tool.py; scripts/scale78b/blinded_sigma.py; its test; runkit/stage1-78b/tests/
  test_planning_ab_78b.py) refuses at `sr2_status` itself and at record-plan-b-78b ("verified another ... the change
  voids the verification"), and no record is written.
- N2a: the block-B copy's own plan_tool.py edited: init-block B refuses ("than the one that runs here").
- N2b: blinded_sigma.py edited: init-block B refuses; restored, block B planned, then OLMo-2-7B's block-A
  plan_tool.py edited: release B refuses ("tmp/family-probe-s78-olmo2-7b-A/ (record-done's code)").
- N2c: block A's release still refuses an edit of the blinded_sigma test after init.
- My round-2 probes R4b and R4c, run again unchanged, now end in those refusals (they asserted acceptance).
- The builder's choice (files compared at block B only for a verified record; an unverified record adopts nothing)
  is held by its test and mutant K2FU-m-b-files-checked-unverified (killed, §5). The accepted limit (edit, run,
  restore) is a limit of any file hash (I).

## 2. R-50 (closed)

- R: `blinded_sigma_read` (plan_tool.py:3866-3900) loads the checkout's blinded_sigma.py by path only when it hashes
  to the record's, with bytecode off and the module not registered, and calls its guarded `read`; record-plan-b-78b
  (:4510-4515) compares sigma_A_pp, df and inputs_sha256 with their types and adds only {sigma_A_pp, df} to the
  printout (:4532).
- M (N3a): real units (Track S's fixture builder) for OLMo-2-7B's full design under [C], the real blinded_sigma.py:
  record-plan-b-78b through `main` adopts SR-2 and prints `blinded_sigma: {sigma_A_pp, df: 12}`; none of the
  fixture's U values (pp and share), residuals, arm means, seed means or the answer text (Track S's `sentinels`, plus
  ANSWER) is in stdout, stderr or the written record.
- M (N3b): an output with sigma one float step higher, df 13, df 12.0 or sigma as a string refuses (the first two by
  R-50's comparison, the last two by the output's form check). The string case's refusal quotes the given sigma; that is
  sigma_A, which blinded_sigma prints by design (P2 §10.1), not an outcome (I).
- M (N3c): a unit changed after the merge: the in-process read refuses through record-plan-b-78b with blinded_sigma's
  own text ("<unit>: 1 sealed file(s) missing or changed"), no planted value.
- The block-B tests stand in `blinded_sigma_read` and `kit_inputs` (R: tests/test_planning_ab_78b.py, `blinded_output`);
  the real read is held by the K2V-5 test (anchor-stopped, df 6) and my N3a (full design, df 12).
- A wrong script: the builder's test (a file of other bytes refuses "is not the file the blinding record verified");
  and blinding_files_check refuses an edited blinded_sigma.py before the read (N1). In a world without
  noise_reading.py beside the script, the load refuses by type only ("did not load (FileNotFoundError)", M: my old R5a
  and R7, which used hand-made outputs and fake units and now refuse).

## 3. R-51 cannot be abused (closed)

M (N4a-N4d), each with the kit's own `requeue --rerun-mismatched` (the environment mismatch stood in) unless noted:
- N4a: no requeue record, one block-A cell's attempt changed in plan.json: write-blinded-part refuses ("exists with
  other bytes").
- N4b: a requeue plus any one more change, made in plan.json: every block-A host's engine, block A's gate SHA-256,
  block A's design (a stop record named), or one more cell: the re-run's record-done keeps the written part and
  prints only what it waits for ("exists with other bytes ...").
- N4c/N4d (the real order): every host recorded, the merged inputs file written, then the requeue: write-blinded-
  inputs refuses while the re-run is open ("is not complete"); the re-run's record-done refuses to replace the part
  while the merged file exists; the old merged file no longer passes write-blinded-inputs; once the lead removes it,
  the part is replaced and the merge gives a new file. A second record-done finds the same bytes.
- The builder's test adds the other host, the other reason, the unnamed attempt and a hand-edited written part.
- Defect K2R2-1 is on this path (a stale temporary file).
- Note (I): at 7-8B this path rests on the 1B `import-reference` route (plan.json `reference`, null in the skeleton,
  R: :1697), which no ruling covers; until one does, R-51's path is dormant.

## 4. No regression

- Block 0 (M, round 1's block0_probe.py on the follow-up ws-k2): plan.json byte for byte equal to the bfda225 and
  3481d85 outputs for both families (14,114 B `f72de041…`, 14,613 B `f5ac8a95…`); the dry-run and real printouts and
  returns, the operator log, `deal 0` and a second release equal.
- My round-2 probes (test_k2r_probe.py, test_k2r_probe_b.py, re-run unchanged): 20 pass as before (K2V-1/R-43 R1a-R1g;
  K2V-2 R2a, R2b, R2d; K2V-4 R3a-R3c; R-44 R4a; K2V-3 R5b, R5c; the blinding plants R6a-R6c; the anchor-stopped read
  R6d). Five fail, each by the follow-up's fixes: R2c (it asserted the old "two complete units" refusal; R-51),
  R4b and R4c (they asserted acceptance; R-49), R5a and R7 (hand-made outputs on fake units; R-50 re-derives sigma).
- Weakened tests: none. The follow-up restores the round-1 assertion "verified another scripts/scale78b/blinded_sigma.py"
  and only rewords the R-44 match texts (R: tp.diff).

## 5. Suite and mutants (M)

- 7-8B suite under the network-deny sandbox, from ws-k2: **619 passed** in 36 s (08:49-08:50 UTC;
  R/r2-k2-reverify2-scratch/suite-78b.log), as the builder reports. No `__pycache__`; `git status` unchanged.
- Scorer spec (291 mutants, SHA-256 `af8efa56…`): the 20 added and 2 re-targeted mutants, with the builder's runner
  from ws-k2, three shards at once (08:47-08:50 UTC, each about 3 min; every baseline exit 0, 188 passed): **22 killed,
  0 survived, 0 invalid** (m0.json-m2.json). Each new find text occurs exactly once (M: count).
- Not re-run by me: the spec's other 269 mutants (I ran 55 of them in round 2, all killed) and the rules, runner and
  gated specs (the builder: rules 248 killed in this follow-up).

## Commands run (exit 0 unless noted)

`date -u`; reads (cat, sed, grep, diff, shasum, git status); a scratch repo copy of ws-k2 (the kit copied, the rest
linked) for test_k2r2_probe.py (first run 17 passed, 2 failed: N3b's string case asserted too much, since sigma_A may
be printed, and N4c ran write-blinded-inputs while the re-run was open, which the kit rightly refused; N4d replaces
N4c, 1 passed; N4e, the K2R2-1 probe, 1 passed) and for my round-2 probes (20 passed, 5 failed as §4 explains);
round 1's block0_probe.py; the 7-8B suite; the scorer runner, 3 shards. The scratch repo copy, the runner copies and
the pytest temp folders were deleted afterwards (kept: the probe file, the diffs, the shard lists, the result files
and logs, the block-0 summary).
