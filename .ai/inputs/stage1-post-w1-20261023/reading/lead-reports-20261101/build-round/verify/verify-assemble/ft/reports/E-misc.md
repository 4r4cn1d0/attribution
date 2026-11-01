# Draft records: B14's scheduling gap and route, LN-31's late draw (D-7), and ADD:428's simulations

- **Status.** A draft for the lead (GI VIII), written 2026-11-01 by an Opus builder (track E-records); clock checked
  with `date -u` at 05:29 UTC. It adopts nothing until the lead commits it. It reads no stage-1 outcome.
- **Where it goes.** Points A and B fit addendum §39 (after the points of `E-39.md`); point C fits §39 or a FOCUS
  entry. Point A is not an inference rule; point B (D-7) is row 14 of the S1 blinding record.
- **Citations** are `path:line` at commit `55d5f8b`; short names as in `E-D5-D6.md`, plus: PLANS =
  `research/review/2026-10-08-sharpened-direction-DRAFT.md`; RULES = `runkit/stage1-olmo/stage1_rules.py`;
  SIM = `scripts/stage1_s1/overlap_similarity.py`; HLC =
  `research/review/2026-10-17-stage2-design-notes/second-rater-and-human-label-check.md`; NOTES =
  `/Users/spiderishi/Coding/attribution/.claude/worktrees/kind-hawking-a6ce04/tmp/claude-workspaces/stage1-integrate-20261017/notes/`
  (git-ignored; cited by path, SHA-256 and line; the lead commits copies of the two cited files with the records,
  LR R6.5). LR (the lead's rulings), the design round's committed copies (R1B, R1D, CRIT) and the build round's
  reports (CKB, CKV, D2B, D2V, EV2) are as in `E-D5-D6.md`'s table.
- **Fix round 2** (1 Nov): A takes LR R3 (the `retrieved/sim-1/` route, the new kit hashes, the equality checked by
  C's verifier, N5), B takes LR R5 (D-7's confirmed readings, limits, HLC 4.3 item 4, the inputs and step 5), C takes
  LR R6.5 (the committed copies) and the z-level script, and D records the build round's hard-rule notes (LR R6.4).

---

## A. B14's similarity pass: a scheduling gap, and the route

**Facts.**
- The pass was planned "on the pod": "untuned-model embeddings, on the pod" (PLANS:172); "θ0 embeddings, on the pod;
  B14 builds the strata at S1" (W1R:129). The rule text names no device and no block (REV4:757). The only timing rule
  is ADD:375: the SHA-256 of `strata.json` goes into FOCUS before any add-arm outcome is read.
- No block scheduled it. None of the kit's 20 job kinds runs it (RULES:505-509), and no block lists such a kind
  (RULES:619-625). The gap was first recorded on 31 Oct (FOCUS:76; PLAN:31).
- It reads only θ0, the 200 dev harm prompts and the three add sets, each by SHA-256, and no unit, `eval/` folder,
  guard file, seal or `plan.json` (R1B:76-93). So the strata are a fixed function of θ0 and these prompts and rows.
- The committed script cannot run on the Mac: it always uses the real loaders (SIM:421-426), which run only on CUDA
  ("the real loaders run only on CUDA; 'cpu' is for engineering fixtures, never a scientific fallback",
  `experiments/safety_selection/loaders.py:121-129`; `experiments/minimal_safety/model.py:377-385`).

**Ruling.**
1. **A scheduling gap, not a deviation.** The pass runs once, after both blocks and before any stage-1 outcome is
   read; the SHA-256 of `strata.json` goes into FOCUS before any add-arm outcome is read (ADD:375). Nothing measured
   changes, because no input of the pass depends on when it runs (the same pattern as c0's move, "a scheduling
   change inside block A, and nothing measured changes", ADD:522). W1R:129's "B14 builds the strata at S1" could not
   be met for the strata themselves: S1 is "before the stage-1 freeze, which comes before block A" (REV4:29), and two
   of the three add sets the strata need, S3 and S4, did not exist until after block A's diagnostics pod had started
   (S4's edit file dates from 25 Oct 15:42 UTC and S3's from 16:46 UTC; R1B:69-74, which reads W1R:129 as a build
   deadline, R1B:61). It is read as B14's code, built and verified at S1 (ADD:503: "B14 87/87"); the strata are built
   later from the same inputs. The ruling stands either way.
2. **Route: kit round 34 and one A100 pod.** Round 34 adds one job kind that runs the pinned SIM once (engine X,
   recipe REC, no unit, no measurement), with S1 code pins for SIM `f8305c71…` and its settings `27db4c3f…`, tests
   and mutants (R1B:179-183). The $0 Mac pre-check of the tokenizer and codec runs first (R1B:263-295). One A100 pod
   runs it from a background job, paid from the balance (KW:8): about $0.60-0.75, worst about $2.7-3.1 at the cap
   (R1B:186-189; estimates). D-6 lands before `strata` runs. Round 34 is built and verified (CKB; CKV; LR R3). It
   changes `stage1_rules.py` (`bde78fab…` → `4005cb4e…`) and `plan_tool.py` (`f18bb834…` → `27e299b5…`) (CKB:31-32);
   `seal.py` and `judge_units_stage1.py` are unchanged. The runbook's "never changes" list takes the two new hashes
   (LR R3.2).
2b. **Round 34 changes the rules file the reading loads.** Round 34 lands in the live kit `tmp/stage1-olmo/` to run
   its pod, and the runbook requires the repository and live copies of the kit files to be equal (R1D:220, :228-229),
   so it lands in `runkit/stage1-olmo/` too before the reading; the reading's builder loads that rules file by default
   (RI/__main__.py:27-28, :40; RI-O13, RIB:460-462). Round 34 leaves every value the builder and B14's inputs writer
   read unchanged: `block_runs` for blocks A, B and C, `REUSED_SEEDS`, `REJUDGED_PINS`, and the judge constants
   `JUDGES`, `JUDGE_INDEX`, `JUDGE_INDEX_KIND`, `JUDGE_INDEX_VERSION`, `JUDGE_FILE_PATTERN`, `JUDGE_NAMES` and
   `JUDGE_INDEX_ENTRY_KEYS` (RI/build.py:242-262, :537-557). **That equality was checked by C's verifier, not pinned
   by a test (LR R3.3):** the verifier loaded the `55d5f8b` and round-34 files side by side and found every such
   value equal (CKV:37, :137, :190); round 34 has no test that pins them, and this record's first draft was wrong to
   claim one. The runbook's pinned kit-pair hashes (R1D:228-229) and the second stamp take round 34's new hashes;
   otherwise the reading's R0 check stops before any value is shown (R1D:497-517), at the cost of a new second stamp.
3. **Seal, and how `retrieved/` is touched (LR R3.1).** The SHA-256 of `similarity.json` (equal to the one the pod
   prints) and then of `strata.json` go into FOCUS before any add-arm outcome is read (ADD:375), and both go into the
   second stamp. `retrieved/` is on the never-open list (FOCUS:74). The one exception: tools may read
   `tmp/stage1-olmo/retrieved/sim-1/` only by the exact path and SHA-256 that `record-done` prints (CKB:349-351,
   :365-367). `overlap_strata.py strata` runs in place on that path. A script copies `similarity.json` into the B14
   records folder with a SHA-256 check and prints only the hash. `similarity.json` holds no stage-1 outcome: it is
   training-row to evaluation-prompt similarity, with no model output. On a crash the lead may read sim-1's
   `process.log` (B14's own stdout, which names ids only; no model output; CKB:356-357) and records that read. The
   lead never lists `retrieved/`.
4. **The Mac route is dropped** (PLAN:31's fallback (i)): it would need new loader code that the engine forbids for
   scientific runs, a weights download of about 3 GB, and a deviation from "on the pod" (R1B:209-245).

**Pre-set fallback.** A one-off pod outside the kit with the same command and a written checklist (a self-stop
timer, the minimal bundle, hash checks, pull, stop; R1B:193-207). *Trigger:* round 34 is not verified (kit suite
and mutants) when the other builds are done, or the kit refuses for a reason that needs another round (R1B:253-254;
CRIT:348). **N5 accepted (LR R3.4):** C's verifier found that a warning written without a trailing newline just
before the pod's "wrote" line makes a good run a crash under the printed-SHA-256 rule (CKV:135, :201). The plan pays
one re-run (`defer sim-1` to `sim-2`, from the `sim` contingency, CKB:356-357); then this fallback's one-off pod with
the checklist; last resort `--no-overlap` ("not computed").

**Last resort.** `--no-overlap`, with D-6's fallback wording and this cause ("no strata: B14's similarity pass did
not complete"). *Trigger:* two pod attempts end without a written `similarity.json`, or the live balance is below
$6 + the pod's cap × $1.85 (R1B:255-256; CRIT:348).

---

## B. Post-W1 deviation D-7: LN-31's draw is built after its deadline (the number is the lead's, in ruling order; CRIT:243)

**Facts.**
- LW-30: "A one-paragraph commitment in REQ-21 before wave 1, with the full protocol before block A; it adopts no
  spend" (REV4:762). The draw "reads block-A guard files only after block B is complete, by a script that prints
  totals only" (LN-31, REV4:763).
- HLC:164: "Before the draw script reads any stage-1 guard file", the lead commits the frozen protocol, the draw
  script and its SHA-256, the seed tags, the §8 term list and the input files by SHA-256. HLC:168: "Freeze deadline
  (decision HD8): before the first stage-1 block-A pod launches, so the draw cannot depend on any stage-1 outcome."
- W1R:243 (item (f) rule 7) says the same: the full protocol, its draw script, seed tags and input hashes are
  committed before block A's first pod launches.
- The first block-A pod, s10-1, was created at 2026-10-25T11:04:34 UTC (FOCUS:125-126). HLC is still "DRAFT … Not
  frozen" (HLC:3), and at the design round no draw script existed (R1D:37, :831-834). No guard file has been read for
  the draw, and no stage-1 outcome has been read (blocks A and B sealed and unread, FOCUS:107, :77).
- Track D2 built the draw on 1 Nov (`scripts/stage1_s1/hlc_draw/`: the script, its settings with the seed tags and
  the term list, its tests and mutation spec; D2B:26-31, :43-56), after both seals and before any stage-1 outcome was
  read; it is verified after one fix round (D2V:13-16; LR R5, status line).

**Ruling D-7.**
1. LW-30's "full protocol before block A", HLC:164's and HLC:168's deadline and W1R:243 were missed: the deadline was
   before block A's first pod, 2026-10-25T11:04:34 UTC; the draw was written on 1 Nov, after both seals and before
   any stage-1 outcome was read (LR R5.4). This is recorded as post-W1 deviation D-7, and the paper states it with the
   date the protocol was committed.
2. The deadline's purpose, a draw that cannot depend on any stage-1 outcome, still holds if HLC:164's items are
   committed before any stage-1 outcome is read. **Default:** freeze the protocol (HLC revision 2's draw, adopted by
   LN-34, REV4:762) and commit it with the draw script and its SHA-256, the seed tags, the term list and the inputs by
   SHA-256 before the second stamp; test the script on synthetic data; a second process recomputes the draw and
   prints only "match" or "mismatch" and totals (HLC:167). The draw runs as the reading's step 5, after the reading,
   and prints totals only (REV4:763; HLC:165). No rater is recruited and nothing is spent (REV4:762; KW:9).
   - **The inputs "by SHA-256" (HLC:164)** are bound through block A's seal and `stage1_rules.REJUDGED_PINS`
     (COMPLETE.json and job.json SHA-256; COMPLETE.json lists every file's SHA-256), the 9 Oct key by its
     pre-registered SHA-256 and the bank by the data config's `banks_from`, as track D2 built it (D2B:37-41); the
     draw's manifest repeats them. So no sealed guard file is opened or hashed before the reading (EV2:150-152).
     Before step 5 the inputs are restored and pinned in `tmp/hlc-inputs/`: the 9 Oct key at
     `tmp/hlc-inputs/oct9/key.json` and the prepared-v3 set at `tmp/hlc-inputs/prepared-v3-inj05` (LR R5.5; paths
     named here, not opened). `tmp/hlc-inputs/` is on the never-open list for every helper.
   - **HLC 4.3 item 4, "a second, independent process" (LR R5.3):** the package's `check` re-runs the same code in a
     second process; it is not independently written code (D2B:250; D2V:80-83). This reading is recorded as part of
     D-7. Partial cover: the two verifiers' independent re-implementations reproduced the tool's draw item for item on
     synthetic draws (49 identical re-computations and an exhaustive check of 6,000 small cells, D2V:13-16).
   - **D2's suite is re-run after track A's merge** (the draw imports `reading_input`; D2B:248-249; LR R5.5).
2b. **Confirmed readings (LR R5.1; D2B:373-386).** Reading 4: the split counts prompts for the total, the bounds and
   the minimums, and answers for the proportion. Reading 7: the protective reading, under which rule b also reads the
   greedy harm answers' categories. Reading 11: the benign block is each population unit's own greedy over-refusal
   answers with their stored full-answer "Refusal" flag. Reading 12: theta0's Unsafe cell also takes the HarmBench
   split. Reading 13: a cell's target is cut to its distinct available prompts, and any rest flows to the next cell.
   The 106-term list and the 5 age patterns (D2B:357). The benign label is each unit's stored full-answer Refusal flag
   on its own greedy answers, which the paper states.
2c. **Limits recorded (LR R5.2).** The HarmBench minimum of HLC 4.2 is often lost across seeds in low-U arms, a
   consequence of HLC's fixed order and its no-prompt-twice rule: confirmed as reading 4, with its simulated size
   stated, about 6-13% of seed cells at U 0.03-0.05 and q 0.2 (D2V:52-66; the estimates lose precision, not
   validity). The weights file splits by HarmBench label only in the Unsafe cell, less fine than HLC:157's sentence
   (D2V:67-79): a recorded limit; the missing counts can be recomputed from the hashed inputs.
3. **Pre-set fallback.** No step 5 at the reading; the draw runs when the human label check is funded, and its code
   is labelled "written after the stage-1 reading and after HLC:168's deadline". *Trigger:* the draw is not verified
   when D-5, D-6 and B14's inputs writer are built (CRIT:351; R1D:787-789). Not triggered today: the draw is verified
   (D2V:13).

**S1 blinding line.** Written [FILL-time], after the W1 commit and after every Gate B value the S1 blinding record
lists. The human label check is report-only and exploratory (REV4:762); the record lists D-7 for completeness, and
the paper labels it "fixed after Gate B wave 1".

---

## C. ADD:428: B16's size, coverage and familywise-error simulations

**Facts.**
- ADD:428 (§16 point 4, 23 Oct 00:40 UTC): "The size, coverage and familywise-error simulations are not re-run on
  the final code; they run once more, at the S1 freeze."
- **The recorded run.** B16's statistics verifier ran them from 2026-10-22T22:07:04Z to 23:02:02Z on the build tree
  (`ws-b16`, 25 files equal to the build report's table) before B16's fix pass: NOTES `b16-verify-stats.json`
  (SHA-256 `65fe90c39b429b246168a4b93b8eb1ff2b5a2831615dc7be9b0d3a733976e5e3`; lines 5-6 the times, :9 the tree, :87
  `simulations`: `seed_level_size_and_coverage` :88, `item_level_coverage` :252, `phi_familywise_error` :279,
  `reml_kkt_scan` :371). Its readings: seed-level size under the built active set near nominal ("90% coverage
  89.8-90.1% mean, 89.1-90.1% worst contrast"; at 0.75% the worst world 0.98%); item-level 90% coverage 89.2-91.8%
  with the crossed item part; Φ's familywise error at the z level against the review's own generator, 0 mismatches
  over 108,000 p-vectors and "every value <= 5%" (:282-283, :352); end to end through whole readings, G0 plan A
  4.11% ± 0.47 and G0 plan B 5.20% ± 0.70 (:356, :358), so plan B's end-to-end rate is within Monte Carlo error of
  5%, not shown below it.
- **Not re-run on the committed code.** The fix pass (NOTES `b16-fix.json`, SHA-256
  `4090118e0616e62c23665f36b730d26e6440af935e08d524b74f188b9aeea600`, finished 2026-10-23T00:37:45Z) states at line
  269: "the verifiers' size and coverage simulations (sim_seed.py, sim_item.py, fwer_e2e.py) were not re-run; the
  stop-rule change can only move fits that were falsely converged, which the KKT and plan-B rechecks cover". B16 was
  committed after that pass (`2135c2d`, 2026-10-23T00:40:40Z).
- **No run at the S1 freeze is recorded.** In NOTES no other record names `sim_seed.py`, `sim_item.py` or
  `fwer_e2e.py` (M in round 1: a `grep -r` over that git-ignored folder that printed file names only; the folder is
  not on the never-open list, and the search is reported so the lead can judge it). The committed record folders hold
  the halves simulation (B16/README.md:100-102) and D-4's regression re-run (B16H:457 onward: whole readings; one
  flagged synthetic document, B16H:539, differs only in an S-start entry, not a label, B16H:243), neither a
  seed-level size or Φ familywise run. CRIT:188-197 found no record either.
- B16 changed after the run: the fix pass (B16/README.md:161-170), D-4 and the halves (FOCUS:104), and two mutation
  fixes with no behaviour change (FOCUS:99). Under D-5's route B16 does not change again.

**Ruling.**
1. **Cite that run** as the last size, coverage and familywise-error evidence for B16, with its limits: it ran on the
   22 Oct build before the fix pass; the fix pass covered its stop-rule change by the KKT and plan-B rechecks
   (`b16-fix.json`:269); D-4 changes a REML end point only where the pre-registered start stopped at a lower maximum
   (about 0.4% of plan-A fits, ADD:605; one synthetic block-A-only reading changed a label there, which is D-4's
   reason, ADD:605), and D-4's regression re-run flagged one synthetic document, an S-start entry and not a label
   (B16H:539, :243).
2. **Record the missed step.** FOCUS and the reading record's limits say: "B16's size, coverage and familywise-error
   simulations last ran on 22 Oct 2026 (22:07-23:02 UTC) on its build before the fix pass; the re-run planned at the
   S1 freeze (addendum §16 point 4) did not happen."
3. **Keep the evidence checkable (LR R6.5).** The lead commits copies of `b16-verify-stats.json` (SHA-256
   `65fe90c3…`) and `b16-fix.json` (`4090118e…`) from NOTES (in the lead's worktree `kind-hawking-a6ce04`) with the
   records, before the second stamp; today they are git-ignored files in one worktree's `tmp/`. The evidence
   folder's file list with SHA-256 values goes with them.

**Optional (not the default).** Re-run `sim_seed.py`, `sim_item.py`, `fwer_e2e.py` and `zphi.py` (NOTES
`b16-verify-stats-evidence/scripts/`; `zphi.py` made the z-level "every value <= 5%" reading of the facts above,
`b16-verify-stats.json`:279-283, :367, and exists at that folder, M: `test -e`) on the final tree as the lead's
background job at $0 before the second stamp. *Skip it when* the run would not finish before the second stamp
(CRIT:353).

---

## D. The build round's hard-rule notes, recorded as disclosures (LR R3.5, R6.4, R6.6)

None is a blinding breach; each is recorded so that the lead can judge it and the record is complete.

1. **Track C's `git ls-files` print (LR R3.5).** While checking which add-edit records the worktree tracks, C's
   builder ran `git ls-files .ai/inputs/stage1-post-w1-20261023/block-b | head -3`. It printed three file names
   under `block-b/` (a fingerprint record and two billing files): names only, no content, no value (CKB:404-406;
   CKV:246-248).
2. **Track D2's three 600 s overruns (LR R6.4).** Three shards of D2's mutation run (shards 2, 3b and 3c: 11, 4 and 3
   mutants) ran past the tool's 600 s limit, and the harness moved them to the background; the builder had not asked
   for background runs. Each finished with exit 0 before the builder went on, and the scratch folders were deleted
   (D2B:210-213). Most of the wall time was machine load outside pytest.
3. **Track E's round-1 `grep -r` over NOTES (LR R6.6).** To look for the simulation scripts' names, E's builder ran
   one `grep -r` over `tmp/claude-workspaces/stage1-integrate-20261017/notes/` (part C above). grep read the bytes
   and printed only matching file names; no content reached a model. The folder holds build, verify and kit reports
   of 17-27 Oct written by the lead's helpers, who never opened a sealed file, so there was no blinding breach.
   Recorded as a disclosure.
4. Two earlier notes stay where they are recorded: the runbook author's repository-wide `grep -rln` (§39 point 8(g))
   and the readiness scout's print of two plant settings lines (§40 point 10).
