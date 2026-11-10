# R3 reviewer brief: the integration lens (adversarial; fresh eyes)

Read first: `B/lead/r3-common.md`. Its paths and hard rules bind you, with one change: you write only your report and
scratch, never a worktree. For probes, copy files into your scratch with `cp -pR` and change the copy.

- **Target:** WS = `B/ws-r3m`, a merged copy: d7eb772 plus K3's final changes (`B/ws-k3v2`) plus Track P's final
  changes (`B/ws-p`). The tracks touch disjoint files. `git -C WS status` and `git -C WS diff` (read-only) show the
  whole round.
- **What else to read:** the reports `R/r3-k3.md`, `R/r3-p.md`, `R/r3-k3-verify.md` and `R/r3-p-verify.md`; the
  briefs `B/lead/r3-k3-brief.md` and `B/lead/r3-p-brief.md`; the lead's rulings `B/lead/rulings-set20-draft.md`
  (sets 20-25).
- **Other reviewers:** a second verifier re-checks K3's correctness, and a safety reviewer checks blinding, secrets and
  money. Your lens is the seams between the tracks, and between this round's code and earlier rounds'.
- **Your report:** `R/r3-integration.md`; scratch `R/r3-integration-scratch/` only.

## Job: find what breaks only when the two tracks' code sits together
1. **The merged suites, under the network-deny sandbox.**
   - The 7-8B kit suite. K3 reports 668 or more.
   - scale78b. Track P reports 781 passed, 2 skipped; it needs `tmp/kt-prepared` copied into WS's tmp with `cp -pR`
     and checked by shasum.
   - The stage-1 kit's 762. It needs `tmp/engine-y-34bfd288` copied in the same way.
   - The engine family tests' 95.

   Any failure is a finding. Name the test and the cause.
2. **W1-18's files list.** Track P's longer `W1_18_78B` form (the two frozen readers) goes through K3's pack, RK's
   check and K3's runner. Probe it: the pod's packed file list includes both readers, and the runner's command reads
   them.
3. **The padded-tokens record.** Write Track P's tool output on a fixture, then read it through K3's
   `plan_tool.padded_tokens` and through block A and B init with a filled `PADDED_TOKENS_78B` fixture. Check that the
   caps use it (train_scale).
4. **The shared anchor-stop fixture.** The same file must be read by Track S's reader (as Track P aligned it), by RK's
   checker, by K2's writer form and by K3's runner (`anchor_stop_or_refuse`).
5. **check-plan on the Mac** (R-75), across every pod kind in the merged code, with nothing unpacked.
6. **Every pin fill procedure the reports document** (for example R-21's W1-18 record folder, R-57's padded-tokens
   folder, `REFS_78B`, `Y_MEASURED_RECORD`) must be accepted by every reader across the tracks. Probe each on a copy.
7. **Earlier rounds' contracts.** The scorer block's and block 0's plan.json are byte for byte (test_42), and the
   R-53 record name holds.

Write mutants on any seam you find untested, and run them with the same command as the baseline. Any survivor is a
finding; an error is an invalid run.

## Report
- A findings table: id, severity (major / minor / nit), R: path:line, what, evidence (M / R), the fix.
- Then the verdict: VERIFIED, VERIFIED_WITH_MINOR or NOT_VERIFIED.
- Be economical: run the merged suites first.
