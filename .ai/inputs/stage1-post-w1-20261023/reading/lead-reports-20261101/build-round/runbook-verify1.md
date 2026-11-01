# Verification of the final reading runbook and its script (round 1)

- **Written** 2026-11-01, about 16:20 UTC (clock checked with `date -u` at 16:08:40, 16:09:11, 16:09:51, 16:11:13 and
  16:17:12 UTC), by an independent verifier for the main-study lead (GI VIII); the launcher records the model.
- **Files verified:** `builds/runbook/reading-runbook.md` (SHA-256 `ad0c9dcd6a3f34fc…`, 858 lines) and
  `builds/runbook/reading.zsh` (`21ab92f3f377d822…`, 326 lines), the bytes the builder's report names. Builder's report:
  `builds/reports/runbook-build.md`. Rulings read first: `builds/lead-rulings-20261101.md`.
- **Where I wrote:** `builds/verify-runbook/v1/` (the dry run's scripts, consoles, ledgers, logs, records and diffs; the
  bulky synthetic copies are deleted, 7.2 MB kept) and this report. Nothing else was written; no checkout or worktree
  was edited; no git command changed state (read-only `log`, `status`, `show`, `rev-parse`, `ls-files` only).
- **Data rules kept.** I opened, hashed, grepped or listed nothing under `tmp/stage1-olmo/{hosts,judges,judges-pending,
  seals,retrieved}`, `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, `tmp/hlc-inputs/`,
  `block-a/`, `block-b/`, no `plan.json` of the live kit, no unit, eval, answer, label, guard, cache or COMPLETE.json
  file, no bank, no path with "plant" or "decoy", and not `similarity.json`, `strata.json` or `overlap_inputs.json`. No
  reading, builder, overlap, HarmBench-claim, judge, seal, kit, draw or launch command ran on real data or the real kit
  state: every run was on a synthetic world made by the builder's own test fixture. No network, install, pod or API
  call; no background job; every command finished in the foreground (the longest, the `ri` suite, in 2 min 1 s).
  Section 8 lists three disclosures (names only).

## Verdict: defects (one; the script itself passed every check)

One defect, in the runbook's fill instructions, not in the script: the `[FILL-0]` marker tells the lead to write
values into the runbook that exist only after the runbook is committed and pinned by the second stamp (its own
SHA-256, the manifest's SHA-256 and anchor, the anchoring block height). Followed as written, the fill changes a
pinned file after step 0.6, and the script's R0 stops the reading (S1) or the lead re-stamps (section 2, D1; a
reproduction at R0 is included). The fix is two sentences. Everything else I could check holds: every command matches
the tools' real interfaces, every expected line matches the code that prints it, every one of the 73 hashes in
section 2 of the runbook matches the worktrees or the main checkout, the step order is the plan's, the stop rules
match the drafts and the rulings, no step opens a never-open path outside the readers' route, nothing prints an
outcome early, and the script ran end to end on a synthetic world in both modes (section 3), with every identity and
provenance check true against the tools' real outputs. Fourteen minor points are notes (section 4).

## 1. What I checked and how (M unless marked)

| Check | Result |
|---|---|
| Every command in `reading.zsh` against `argparse`/`__main__` of the tool in its worktree: `reading_input` (ws-a), `reading` (B16, main), `reading_input.hb_claim` (main = ws-a), `reading_input.sg_coherent` (ws-a), the five `reading_extra` readers (ws-d1), `hlc_draw draw`/`check` (ws-d2), `overlap_strata.py report` (main, = ws-b) | every option exists and is spelled as the tool takes it; `--out` is created exclusively by every tool; exit codes 0/2 (draw `check` 0/1/2) as the runbook's exit table says |
| Runbook section 3 and step 0.4 commands: the three `run_mutants.py` (`--spec --scratch --report --python --timeout --only`), `run_mutants_b14.py` (passes argv to the T1 runner, reads `--report`), `run_mutants_b15.py` (positional `source scratch out select`), `commitments.py check --repo`, `overlap_inputs.py --kit --strata --strata-sha256 --out`, `overlap_inputs_check.py --file --kit --strata`, pytest `-q -p no:cacheprovider --basetemp` | all as the tools take them |
| Every expected line against the print that makes it: the builder's `summary_lines` (ws-a `RI/__main__.py:72-106`), B16's `wrote … (<16 hex>); headline: …`, `hb_claim.py:286-287`, `sg_coherent.py:433-434`, `RX/common.py:102-104` plus `cap_reports` "LN-14 transfer bar" and `stage3_pick` "stage-3 pick", `HD/__main__.py` `_head` and `<path>: match`, `overlap_strata.py:511-517`, `seal.py:191,222`, the writer's and checker's lines | all match; the nine identity substrings of `lines_check` are substrings of the builder's real lines (confirmed in the dry run, section 3) |
| The provenance blocks the `prov` helper expects, against the code that writes them: B16 `reading.py:577-578` after `_strip` (:539-542), `hb_claim.py:245-255`, `sg_coherent.py:382-400`, `RX/common.py:64-74` with `finish` called by each reader, `cap_reports.py:310-312` and `cost_table.py:520-523` (`provenance.kit = {plan_sha256, seals{A,B}}`), the `inputs` keys (`sources.json`; `tables.json`, `reading.json`; `reading.json`; `reading.json`; none) | all match; each reader calls `common.finish` (= `_strip`), so `modules` never holds `__init__.py` and `b16_modules` holds the 11 modules plus `settings/reading.json` |
| The step-2 comparison's pops against the record's real keys (`build.py` `_record`, `__main__.py:123-130`, `hb.py:233-237`, `coherent.py:54-56`): `overlap`, `output_sha256`, `hb.output_sha256`, `coherent.output_sha256`, the two documents' `input_sha256`; no timestamp or path anywhere in the four documents | correct; nothing else differs between the pre-run and step 2 (true in the dry run) |
| B14's report byte-identity (step 1 against R1a): `report()` and `s1common.provenance` hold no time, no output path (`:557-571`); `write_new_files` makes its folder | deterministic (static; not run, section 7) |
| Hashes: every file in runbook section 2 recomputed from ws-a (reading_input changed/new), ws-d1, ws-d2, the main checkout (unchanged, B's and C's merged files), the live kit's four code files; ws-b and ws-c compared with main | 73 of 73 match; ws-b = main and ws-c = main for every file named; `builds/verify-runbook/v1/hashes.py` |
| B16's settings pin: `SETTINGS_SHA256` in `settings.py:7` = the file's hash `fef3b6f5…` | equal |
| Spec entry counts: reading_input 47 (0 survivors), reading_extra 62 (`RX-common-exclusive` survives), hlc_draw 65, b14 150, b15 418, near set 69 (`77c3def1…`, committed under `build-round/`), b16 117; the 39 round-34 ids | as the runbook says |
| Order: R0, R1a, R1b, 1 (B14), 2 (build), 3 (B16, provenance, re-run), 4 (claim reader), 4b (D-5 reader), 4c (five readers), 5 (draw, check) | the plan's order (PLAN:37-49 at `55d5f8b`); B16 before every reader; the draw after the reading; LR R6.3 and R4.4 ("after the input build, B16 and the claim reader") |
| Stop rules against E-39 §39 8(a)-(h), E-D5-D6 item 8 and last fallback (c), E-records-verify3 D1 and note 3, LR R6.1, R6.5 | S1-S9 as drafted with the three 8(d) changes; the (c) route at the pre-run with the restart clause of note 3; the references line not an identity line; the count lines logged (note N1 on step 5's citation) |
| Never-open paths: which step opens what | R1a/1: B14's tool on the units (the plan's step 1); R1b/2: the builder (the plan's step 2); 4c: `cap_reports` and `cost_table` only inside the script after the input build (LR R4.4); 5: the draw (the plan's step 5); R0 and step 0.6 hash `plan.json` and the two seal files (as the first stamp's manifest did, FOCUS:75); step 0.7 tests existence only (LR R4.5); step 0.2 is optional and walks no folder (note N9); `retrieved/` is never listed; `tmp/hlc-inputs/` is only passed to the draw |
| Nothing prints an outcome early: every tool's stdout goes to a step log; the console holds times, step names, ledger lines (hashes, exit codes, booleans), count-line names, STOP lines; R1a's stdout is discarded | confirmed in the dry run: both consoles hold no word or number of the reading (M, `v1/console-2026119{8,9}.txt`) |
| `zsh -n reading.zsh` (zsh 5.9); `ast.parse` of its five heredocs and of the runbook's writer and extractor | exit 0; parse |
| FOCUS:74 at `55d5f8b`: "`tmp/stage1-olmo/retrieved/` joins the never-open list" | the runbook's citation holds |
| Suites in the worktrees: `reading_extra` 120 passed (21 s), `hlc_draw` 123 passed (22 s), `reading_input` 284 passed (121 s; basetemp 2.8 GB, deleted) | the runbook's expected counts (`rx` 120, `hlc` 123 + 3, `ri` 284) hold for the parts I ran |

## 2. The defect

### D1. `[FILL-0]` names values that cannot be written into the pinned runbook (runbook lines 43, 148, 368)

- **What the runbook says.** The markers table (line 43): `[FILL-0]` is "the second stamp's date `STAMP`, the SHA-256
  of this runbook and of the script after the commit, the manifest's SHA-256 and its anchor", filled by "the lead, at
  step 0.6". The pins table's last row (line 148) carries `[FILL-0]` for "this runbook; `reading.zsh`; the second
  manifest". Step 0.3's block has `H=FILL-0` (line 368), the anchoring block's height, known only after the second
  stamp anchors.
- **What step 0.6 says.** "Commit first, by explicit paths: … this runbook (final, at `$RD/reading-runbook-$STAMP.md`),
  the script …. Then write the manifest." The manifest names both files (`named`, writer lines 424-425), and "Nothing
  that the manifest names may change after this point; the script's R0 stops on any change" (line 482).
- **The conflict.** A file cannot hold its own SHA-256; the manifest's SHA-256, its anchor and `H` exist only after
  the manifest is written and anchored, which is after the runbook is committed and pinned. Filling them changes the
  pinned runbook. Then either R0 stops (S1, a false stop with the anchor already waited for) or the lead makes a new
  second stamp and waits again; and if the lead fills and does not re-stamp, the stamp no longer binds the final
  runbook (plan 1e: "a second stamp of the final reading code and the runbook").
- **Reproduction (M, synthetic).** On the dry run's pinned copy: one line appended to
  `$RD/reading-runbook-20261199.md` after the manifest was written, then the script's R0 heredoc (its lines 179-195,
  verbatim) on the same manifest:
  `{"code_clean": true, "files_differ": [".ai/inputs/stage1-post-w1-20261023/reading/reading-runbook-20261199.md"], "kit_same": true, "pass": false, …}`.
  Restored: `"files_differ": [], "pass": true`. In the script this `pass: false` is `fail R0 "… differs from the second
  stamp (S1)"`, exit 1 (the STOP path was also seen live, section 3, run 2).
- **Severity.** Medium, procedural. It cannot change a value and cannot show an outcome (R0 catches it); it costs a
  stamp cycle and an anchor wait, or leaves the stamp not binding the final runbook. It is the one place where the
  runbook contradicts itself.
- **Fix.** Split the marker: `STAMP` (lines 168, 260) and `OTS` (line 271) are filled before the commit; the runbook's
  and script's SHA-256, the manifest's SHA-256 and anchor, and the height `H` are never written into the committed
  runbook: they go into FOCUS, `TS/stamp-anchor-reading-$STAMP.json` and the third stamp's manifest (as step 6 item 4
  already says). Change line 43 to say so, drop `[FILL-0]` from line 148 ("never; recorded in FOCUS"), and make
  line 368 read the height from the anchor record or from a shell variable set at the prompt.

## 3. The dry run on a synthetic world (the script was never run before)

- **World.** The builder's own fixture, ws-a `reading_input/tests/synth_kit.py`: `make(root, "plan_a", seed=0,
  hb=True)` (50 cells, 48 judged units in block B, HarmBench pods for both blocks, the two seals, B14's strata and a
  report in B14's format, the pins and a rules module). No caps and no cost ledgers (`extra_kit.with_caps` does not
  remap the HarmBench cache, so `hb=True` and caps cannot be combined; the two readers that need them refuse, which is
  the never-stop path the script must take). The draw's inputs are absent, so the draw refuses.
- **ROOT.** `builds/verify-runbook/v1/root/`: the main checkout's `scripts/` and `experiments/safety_selection/` code
  (`rsync`, excluding `__pycache__`, tests of the engine, and any name with plant, decoy, hidden or selector, never
  printed), ws-a's `reading_input/`, ws-d1's `reading_extra/`, ws-d2's `hlc_draw/` on top; the five kit code files the
  manifest names; the synthetic kit at `tmp/stage1-olmo/`; the synthetic rules module at
  `runkit/stage1-olmo/stage1_rules.py` and the kit's copy; placeholders for the addendum, the study plan, the S1
  record, `b14/inputs/overlap_inputs.json` and `b14/similarity.json`; the strata at `b14/strata/strata.json`; a `.git`
  folder and a `.gitignore` with `tmp/` (the draw's HLC 9 check). A stand-in `git` (`v1/bin/git`, first on PATH)
  answers `rev-parse` with fixed strings and `status` with nothing; it touches no repository.
- **Script copies** (`v1/reading-dry-20261199.zsh`, mode coherent; `…20261198.zsh`, mode no-coherent; made by
  `v1/make_copies.py`, which asserts each replaced line matches once): 7 lines differ from `reading.zsh`
  (`v1/diff-coherent-copy.txt`): `ROOT`, `PY` (pinned to the real venv, since the script derives it from `ROOT`),
  `STAMP`, `SCR`, `STRATA_SHA`, and the two B14 lines (R1a and step 1), where `overlap_strata.py report` is replaced
  by a copy of the synthetic report (no B14 inputs exist for this world; `mkdir -p` added, as `write_new_files` makes
  its folder). Every other byte is the original's. The manifests were written by the runbook's own step-0.6 writer
  (lines 426-474, verbatim, `v1/manifest_writer.py`): 72 files each.
- **Run 1, mode coherent** (`v1/console-20261199.txt`, `02f7a899…`; ledger `f5482267…`; 2026-11-01 16:09:51-16:10:01
  UTC): **exit 0, `READING STEPS R0-5 DONE`**. R0 pass (all five true). R1a copy. R1b: the real builder with
  `--hb-out` and `--coherent-out`, exit 0, four `wrote` lines; `lines_check`: `identity_lines 9, missing_identity [],
  pass true`, five count lines missing as expected on a synthetic world (the references, the not-pulled, block B's
  judged count, the two record counts). Step 1 copy; `cmp` equal. Step 2: the real builder with the four B14 options,
  `overlap: strata 310fa190…, report e074bb2c…`; `lines_check` pass; the comparison
  `{"coherent_counts_without_input_hash": true, "hb_tables_without_input_hash": true, "sources_without_overlap_and_output_hashes": true, "tables_without_overlap": true, "pass": true}`.
  Step 3: B16 exit 0; `prov` all true (`modules` against the 11 pinned modules plus the settings pin, `settings_sha256`,
  `input_sha256`, kind, reading, Python/numpy); the re-run byte-identical (`cmp`). Step 4: the claim reader exit 0;
  `prov` all true. Step 4b: `sg_coherent` exit 0; `prov` all true. Step 4c: `cap_reports` exit 2
  (`REFUSED: A1 1102: the O-ext summary states no route per source`), logged, the reading went on; `fk_power`,
  `stage3_pick`, `sa_shift` exit 0 with `prov` all true; `cost_table` exit 2 (`REFUSED: a-2 job 0: a complete, pulled
  job whose cost ledger is not in block A's seal`), logged. Step 5: exit 1 (my root lacked `experiments/minimal_safety`,
  an import of the engine's `common.py`; added afterwards), logged as "the draw refused … not run at the reading".
  The console holds no outcome word or number; the headline words are in `logs/3-b16.txt` only.
- **The draw's own refusal path (M, by hand, after the module was added):** the step-5 command on this world:
  `REFUSED: the 9 Oct key: missing or not a regular file`, exit 2, nothing written (no sealed folder, no manifest).
- **Run 2, mode no-coherent** (`v1/console-20261198.txt`; ledger `ccfe2383…`): **exit 0**. R1b and step 2 without
  `--coherent-out`; `identity_lines 8`; the builder prints `coherent-only counts: not built (no --coherent-out)`;
  `${COH_PRE[2]}` and `${COH_RUN[2]}` vanish as intended; step 4b is a ledger line
  `{"exit": 0, "note": "not run: D-5 went to its last fallback (c) at the pre-run (mode no-coherent)", "step": "4b-sg-coherent"}`;
  the rest as run 1. `reading-dry-20261198.zsh bogus`: `usage: reading.zsh [coherent | no-coherent]`, exit 2.
- **The STOP path** (seen live in an earlier attempt, before my stand-in made its folder): step 1's copy failed, the
  ledger line `{"exit": 1, "step": "1-b14"}`, then `STOP at step 1: B14 refused after its pre-run passed (S2: no verdict
  printed)`, `date -u`, exit 1, nothing after it ran.
- **Step 6's extractor** (runbook lines 594-669, verbatim, `v1/extractor.py`) on both run folders: exit 0 each; the
  record has every key; the words table prints four columns (B16's word, its U-part words, the claim reader's word,
  S-G coherent's word or "S-G coherent: not computed"); `cap_reports` and `cost_table` print as `not_computed` with
  their REFUSED line; the draw prints as `not_run` with the log's last line; run 2's record carries the (c) wording
  with the ledger note. A second run on the same folder: `FileExistsError` (the exclusive create).
- **Negative tests of the helpers** (`v1/neg/`, the Python bodies verbatim): `prov` with the `kit` spec on a synthetic
  block equal to the manifest's values: pass; with one wrong seal: `kit: false, pass: false`, exit 1; with one wrong
  B16 module hash: `b16_modules: false`, exit 1. `lines_check` with a wrong overlap line: `missing_identity` names it,
  exit 1. So no check is vacuous.

## 4. Notes (minor; not defects)

1. **Step 5's never-stop cites §39 8(d)(i)**, which names steps 4b and 4c only (E-39:168-171). Step 5's behaviour
   (logged; the record says "not run at the reading") rests on E-misc B's ruling 3 wording, not on 8(d)(i). Nothing
   follows step 5, so the exemption changes only the exit code and the last console lines. Cite E-misc B 3, or add
   step 5 to 8(d)(i) in the records.
2. **The state section is one commit stale.** HEAD is `c21dccb` (a test change under `scripts/stage1_s1/tests/`):
   `scripts/stage1_s1` is `46bdebf8`, not `2f7236be`; the other seven tree ids are as stated. The manifest, not this
   section, is the pin.
3. **"About 90 files"** (step 0.6): the writer's file set gives 72 on the dry run's tree and about 73 on the real one.
4. **Step 0.5's rehearsal cannot run the script unedited:** `PY`, `KIT`, `RD`, `RUN`, `M2` derive from `ROOT`; R0 runs
   `git` in `ROOT`; the draw needs a `.git` folder and a `.gitignore` with `tmp/`. Say that the rehearsal runs a copy
   with the settings block edited (`ROOT`, `PY`, `STAMP`, `SCR`, `STRATA_SHA`) and either a checkout or a stand-in
   `git`; my copies and `make_copies.py` under `v1/` are a worked example (section 3).
5. **`extra` prints "provenance check exit 1 … its output is not used"** after a reader refused (there is no output).
   Noise only; the extractor's branch picks the REFUSED line.
6. **Step 5's console line says "the draw refused (exit N)"** for any non-zero exit, a crash included (exit 1 in run
   1); the record's reason is then the log's last line. "did not run (exit N)" would be exact.
7. **The extractor copies B16's `headline, headline_cells, rows, phi, best_feasible_repair, references,
   overlap_control, label_suffix, notes`** but not `sensitivities` or `actors` (the same list as R1D:698). The rows
   carry each contrast's sensitivity part, and `reading.json` is committed with `$RUN`, so nothing is lost; the
   record would be more complete with both blocks.
8. **Change 7's wording "each bound to `reading.json` by SHA-256":** `cap_reports` is bound to `sources.json` and
   `cost_table` to `plan.json` and the seals (D1's design, verified D1V3); `fk_power`, `stage3_pick` and `sa_shift` are
   bound to `reading.json`. Wording only; the `prov` specs are right.
9. **Step 0.2 (optional)** parses both seal records in a heredoc and hashes every listed sealed file by its exact path
   (counts only; no walk, per LR R3.1). It is R1D's step with the walk removed; the builder's open point 4 asks the
   lead to confirm it fits the never-open list. I take no position; it is not on the script's path.
10. **The count line "judges B: … 71 units"** is the builder's count of the units the reading needs (on the synthetic
    world it printed 48); a wrong inference is logged, never a stop (§39 8(a)).
11. **The step-5 ledger line hashes the sealed key and weights files** (reads their bytes, prints the SHA-256 the draw
    already printed and the text-free manifest holds). No content; fine.
12. **R1D's provenance defect is real** (change 10): R1D's `want` holds every manifest entry under
    `scripts/stage1_s1/reading/` (`__init__.py`, `__main__.py`, `mutation/*`, `settings/reading.json`), so
    `p["modules"] == want` is false on a correct B16 output; the final `prov` passes on a real one (section 3).
13. **The `ledger` file is appended, not created exclusively** (one JSON line per step, by design); every other
    output is an exclusive create or a `noclobber` `>`.
14. **The no-coherent record's (c) text names "run-attempt1's log"** as the source of the pre-run's refusal; the
    runbook's S2 says `$RD/run-$STAMP-attempt1/`. Consistent, provided the lead keeps that copy as S2 says.

## 5. Acceptance criteria (the builder's brief)

| Criterion | State |
|---|---|
| Final runbook and script in `builds/runbook/` | passed |
| D-5 VERIFIED: step 4b runs `sg_coherent`; `cost_table` VERIFIED after fix round 2: it runs in step 4c | passed (runbook sections 0, 4, 6; script steps 4b, 4c; both ran in the dry run) |
| Every track's open points: A's `--coherent-out`, new stdout lines, step 4b; B's writer and checker in place of step 0.4 and the hash table; C's never-changes hashes and the similarity steps; D1's step 4c; D2's step 5 with `OCT9KEY`, `V3`, `mkdir -p $RUN/hlc` | passed (section 9 of the runbook; the hashes and commands checked here) |
| The record drafts: the pre-run with the same options and `--no-overlap`; the step-2 comparison without the counts document's hashes; S1-S9 with §39 8(d)'s exceptions; D-5 item 8's wording when a reader refuses | passed (the comparison and the wording seen in the dry run) |
| LR R3.1, R4.4, R4.5 | passed (`retrieved/` never listed; the readers' exception at 4c only; step 0.7 tests existence only) |
| Hashes from the worktrees for changed and new files, the main checkout for unchanged ones | passed (73 of 73) |
| `[FILL-<name>]` markers for later values | **failed in part**: D1 (`[FILL-0]` mixes pre-commit and post-commit values) |
| `reading.zsh` stops only on identity lines; logs every step's exit code; prints no outcome value; writes every output under `$RUN` by exclusive create | passed (both dry runs; note 13 on the ledger) |
| R1D's structure kept; "Changes from R1D" | passed (20 changes, each with a source I could find) |
| `zsh -n` | passed |
| Matches the surrounding code and records | passed by reading (usage header, plain comments, `REFUSED`/exit 2 as the tools, canonical JSON, `open(..., "x")`) |
| Plain, short sentences | passed by reading |

## 6. Replies to the builder's open points

1. Fill before the commit: `STAMP`, `STRATA_SHA`, `OTS`, `CHK` yes; the rest of `[FILL-0]` no (D1).
2. The mode argument: sound. The bytes stay pinned; the mode is in the ledger's first line and the console; S2's
   attempt-1 copy keeps the first run's logs. The (c) route is chosen by R1b's stderr, as E-D5-D6 item 8 says.
3. R1D's provenance checks: confirmed wrong (note 12).
4. Step 0.2: note 9; for the lead.
5. The manifest's named records: the writer refuses an uncommitted tracked named file and a missing one (a
   `FileNotFoundError` traceback for an unfilled `FILL-S1-RECORD`); fill or drop before step 0.6.
6. `kit.seals` of `cap_reports` and `cost_table`: both write exactly A and B for plan_a (`cap_reports.py:265,311` from
   the record's `kit.seals`; `cost_table.py:522` from `READING_BLOCKS["plan_a"]`); `prov`'s `kit` check passes on a
   block shaped so (section 3's negative tests).
7. The count lines: agreed; logged, never a stop (note 10).
8. The brief's state line: agreed; one further commit since (note 2).
9. Not tested by the builder: the dry run now covers the script end to end on synthetic data in both modes, the
   extractor, and the draw's refusal path; still untested: B14's `report` inside the script (section 7).

## 7. Not verified, and limits

- `overlap_strata.py report` never ran inside the script (no B14-compatible synthetic kit exists beside the builder's
  world; B's fixtures satisfy B14 but not the builder). Its byte-identity between R1a and step 1 rests on the static
  reading of `report()` and `s1common.provenance` (no time, no path) and on B's verified suite.
- The draw's success path and `check` did not run (the builder's world lacks the draw's inputs; the draw's own world
  is a different kit); its refusal path and the script's handling of a non-zero exit did.
- `cap_reports` and `cost_table` ran only to their refusals (no caps, no ledgers in the world); their `prov` `kit`
  check was tested on a synthetic block, not on a real output.
- The real kit, the real stamps, the `ots` client, the durations marked E, and the count lines' values on the real
  kit are untested by rule or by nature.
- The `s1`, `w1`, `engx`, `kit` and `judges` suites and every mutation spec were not run here (the lead's background
  runs; each is longer than my limit or outside my scope).

## 8. Commands run (exit 0 unless noted) and disclosures

- `date -u` (five times). Reads of the runbook, the script, the builder's report, the rulings, R1D (committed copy),
  E-39, E-D5-D6, E-misc, E-plan-updates, E-records-verify3, FOCUS:70-80 and PLAN:28-56 at `55d5f8b` (`git show`),
  and the code named in section 1 (worktrees and `git show 55d5f8b:`).
- `git -C main` `log`, `status --porcelain` (code paths; clean), `show --stat c21dccb`, `rev-parse {HEAD,0435c3b,55d5f8b}:<tree>`,
  `ls-files …/lead-reports-20261101/build-round` (names only); `git status --porcelain` in the five worktrees.
- `shasum -a 256` / Python SHA-256 of every file in runbook section 2 (code, settings, specs), the live kit's four
  code files, the near set, the two files under verification and my evidence files.
- `zsh -n` on the script and both copies; `ast.parse` on the heredocs.
- pytest in the worktrees on fresh basetemps under `builds/tmp/`, each deleted after: `reading_extra` 120 passed,
  `hlc_draw` 123 passed, `reading_input` 284 passed (2.8 GB basetemp).
- The dry run (section 3): `build_world.py`, `make_copies.py`, the manifest writer twice, the script copies twice
  (exit 0, exit 0; one earlier attempt exit 1 at R0 from my `PY` path, one exit 1 at step 1 from my stand-in: both my
  setup, both fixed), the draw by hand (exit 2, a refusal), the extractor three times (0, 0, and the exclusive-create
  refusal), the negative helper tests (exits as expected), the D1 reproduction. `rm -r` of the bulky synthetic copies
  and the scratch folders by explicit paths.
- **Disclosures (names only, no content):** (1) `ls` of the top level of `experiments/safety_selection` and
  `experiments/minimal_safety` (code folders; not on the never-open list) to decide what to copy; (2) `rsync` of code
  folders with `--exclude` patterns for plant, decoy, hidden and selector names, so no such file was read or listed;
  (3) `git ls-files` of the committed `build-round/` folder printed file names (as LR R3.5 records for track C). No
  sealed file, unit, bank or outcome was opened, hashed or listed.
