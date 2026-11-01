# Runbook track: the final reading runbook and its script (build report)

- **Written** 2026-11-01, finished about 15:50 UTC (clock checked with `date -u` at 15:21:00, 15:28:15, 15:32:29,
  15:41:23, 15:44:00 and 15:44:20 UTC), by the runbook builder for the main-study lead (GI VIII); the launcher
  records the model.
- **Where.** Only `scratchpad/builds/runbook/` (created): `reading-runbook.md` (858 lines, SHA-256
  `ad0c9dcd6a3f34fc0af9e1c7d9b1b0f193915fbcc69469bff7eb34e40b94f15a`) and `reading.zsh` (326 lines,
  `21ab92f3f377d822e0537063e423c6522edd094b23bb4c1c869519e9902bd001`), plus this report. No checkout or worktree was
  edited; no git command changed state.
- **Data rules kept.** I opened no stage-1 outcome, seal, host, judge, unit, answer, label, guard-sample, cache or
  COMPLETE.json file, no bank, no path with "plant" or "decoy", nothing under `tmp/stage1-olmo/{hosts,judges,
  judges-pending,seals,retrieved}`, `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`,
  `tmp/hlc-inputs/`, `block-a/` or `block-b/`, and not `tmp/stage1-olmo/plan.json`, `similarity.json`,
  `strata.json` or `overlap_inputs.json`. Every check ran on synthetic files only (section 5). No reading, builder,
  overlap, judge, seal, kit, draw or launch command on real data. No network, install, pod or API call. No background
  job. Section 7 lists three disclosures (names and code only).

## 1. Result in brief

1. **`reading-runbook.md`** keeps R1D's structure (sections 0-8 as the draft, plus section 9 "Changes from R1D",
   20 numbered changes with their sources). Every R1D gap RB1-RB11 is updated to the build round's state. It states
   **D-5 VERIFIED: step 4b runs `sg_coherent`** and **`cost_table` VERIFIED after fix round 2: it runs in step 4c**.
2. **`reading.zsh`** is the stamped script, steps R0-5. It stops only on identity lines (R0's pins; a refusal of
   B14, the builder, B16 or the claim reader; a provenance or hash mismatch at steps 3 and 4; a pre-run or re-run
   that is not byte-identical). Steps 4b (D-5's reader), 4c (the five reading-time readers) and 5 (D-7's draw) are
   logged and never stop it. Every step's exit code goes to the ledger (the mode too). It prints no outcome value:
   each tool's stdout goes to its step log, and the console holds names, times, hashes, booleans and STOP lines.
   `setopt noclobber` makes every `>` an exclusive create; the tools use `O_EXCL` themselves. `zsh -n`: exit 0.
3. **The rulings are built in:** R1b takes `--coherent-out` and `--no-overlap` in place of the B14 options; the
   step-2 comparison leaves out the counts document's hashes (LR R6.1); stop rules S1-S9 with the §39 8(d)
   exceptions; D-5 item 8's wording in the record when the reader refuses; `retrieved/` never listed (R3.1); the
   readers' never-open exception at 4c only (R4.4); the cost-ledger pre-check, existence by exact path (R4.5); step 5
   with `OCT9KEY=$ROOT/tmp/hlc-inputs/oct9/key.json`, `V3=$ROOT/tmp/hlc-inputs/prepared-v3-inj05` and
   `mkdir -p $RUN/hlc` (R5.5); the "never changes" list with round 34's hashes (R3.2); B's writer and checker in
   place of R1D's step 0.4 heredoc (R2.3).
4. **Hashes** come from the worktrees (ws-a, ws-d1, ws-d2 for the unmerged files; ws-b and ws-c equal the main
   checkout's, where D-6 and round 34 are merged at `53f746d`) and from the main checkout for unchanged files.
5. **Fill markers** (`[FILL-COMMIT]`, `[FILL-SIM-PATH]`, `[FILL-SIM-SHA256]`, `[FILL-STRATA-SHA256]`,
   `[FILL-B14IN-SHA256]`, `[FILL-0]`, `[FILL-S1-RECORD]`) carry the values known only later; the script holds
   `STAMP=FILL-0` and `STRATA_SHA=FILL-STRATA-SHA256`, filled before the commit the stamp binds.
6. **One defect found in R1D and corrected (change 10).** R1D's provenance checks at steps 3 and 4 compared B16's
   `provenance.modules` (and `b16_modules`) with every manifest entry under `scripts/stage1_s1/reading/`,
   `__init__.py` and `__main__.py` included. B16's `_strip` drops every key that starts with `_`
   (`B16/reading.py:539-542`; ACB §8 item 7; M on the real package: 12 keys after `_strip`), so the drafted check
   would have stopped a correct reading at step 3 under S5. The script's `prov` helper expects the 11 modules plus
   `settings/reading.json`, for B16 and for every reader's `b16_modules`, and a reader's own modules without
   `__init__.py`.

## 2. The files

| File | SHA-256 | What |
|---|---|---|
| `runbook/reading-runbook.md` | `ad0c9dcd6a3f34fc0af9e1c7d9b1b0f193915fbcc69469bff7eb34e40b94f15a` | the runbook: state, pins, suites and specs, the procedure (Block R, steps 0.1-0.8, the script's step table, step 6), stop rules, the outputs table, decisions, what was run, changes from R1D |
| `runbook/reading.zsh` | `21ab92f3f377d822e0537063e423c6522edd094b23bb4c1c869519e9902bd001` | the script: a module docstring with the usage line; settings; helpers `fail`, `ledger`, `lines_check`, `prov`, `extra`; steps R0, R1a, R1b (+ check), 1 (+ cmp), 2 (+ identity check, + same-as-pre-run), 3 (+ provenance, + re-run cmp), 4 (+ provenance), 4b, 4c (five readers), 5 (draw + check) |

## 3. Design choices, and the alternatives I rejected

- **The mode argument `coherent | no-coherent`.** D-5's (c) route is chosen at the pre-run only (E-D5-D6 item 8).
  A refused R1b writes nothing, so the pre-runs must restart without the option (E-records-verify3 note 3). An
  edit of the script would move its hash and need a new stamp; an environment variable would be invisible to the
  record. A positional argument keeps the bytes fixed and is written into the ledger's first line and the console.
  *Rejected:* a second script for the (c) route (two pins for one reading); editing the pinned script (a new stamp).
- **`setopt noclobber`** instead of wrapping every log write in a Python exclusive create: one line, the same
  effect for every `>`, tested (an overwrite is refused). The B14 pre-run's discarded stdout uses `>| /dev/null`.
- **One `prov` helper with a small spec** instead of one heredoc per step (R1D had two near-identical heredocs and
  would have needed seven): the same expectations for B16, the claim reader, the D-5 reader and the five readers,
  each shaped as its code writes the block (`RI/hb_claim.py:246-249`, `RI/sg_coherent.py:383-387`, `RX/common.py`,
  `B16/reading.py:577-578` after `_strip`).
- **Identity lines against count lines.** `lines_check` fails only on the identity lines (plan code and plan.json's
  SHA-256, the rules and B16 settings pins, both seals, the overlap line, each written file's SHA-256) and prints
  the count lines that are missing for review (§39 8(a); LR R6.5 on the references line). *Rejected:* R1D's strict
  list (a wrong inference would cost a new second stamp).
- **The script sets `ROOT`, `KIT`, `PY` itself** rather than sourcing `tmp/gi-vii-notes/blockB_S.zsh` (untracked,
  unpinned). The values are the same (M).
- **Step 0.2 without the `not_listed` walk.** R3.1: the lead never lists `retrieved/`; the seal check now hashes
  the listed files by their exact paths only. *Rejected:* keeping a count-only walk (it still walks the folder).
- **The extractor's branches** for an absent or failed 4b/4c/5 output distinguish "the reader refused" (its
  REFUSED line copied from the log) from "the provenance check failed" (the check's JSON), so the record never
  quotes a reader's headline line as a refusal (found and fixed while testing on synthetic logs).
- **The runbook does not repeat the script's text** (R1D embedded it): the script is one file the stamp pins, and
  the runbook's step table says what each step runs, prints, refuses, writes and who reads it. *Rejected:*
  duplicating 300 lines that could drift.

## 4. Inputs read (all read-only; no real data)

LR (all); R1D's committed copy; the build, verify and fix reports of tracks A-E under `builds/reports/`
(`A-coherent-build.md` with fix round 1, `A-coherent-verify2.md`, `B-b14-build.md`, `B-b14-verify1.md` by grep,
`C-kit34-build.md`, `C-kit34-verify1.md` by grep, `D1-readers-build.md` with fix rounds 1-2, `D1-readers-verify3.md`,
`D2-ln31-build.md` with fix round 1, `D2-ln31-verify2.md` by grep, `E-records-verify3.md` in part); the record drafts
`E-D5-D6.md`, `E-39.md`, `E-misc.md`, `E-plan-updates.md`, `E-S1-blinding.md` (header); `wf-final-digest.md` (head);
`merge-bc-20261101.json`. Code: ws-a `RI/__main__.py`, `sg_coherent.py`, `coherent.py`; ws-b `overlap_inputs.py`,
`overlap_inputs_check.py`; ws-c `plan_tool.py` (record-done), `seal.py` (layout), `setup/job_runner_stage1.py`
(the ledger name); ws-d1 `RX/README.md`, `common.py`, the readers' output blocks, `cost_table.py`'s ledger
enumeration; ws-d2 `HD/__init__.py`, `__main__.py`, `draw.py` (the manifest). At `55d5f8b` via `git show`:
`RI/__main__.py`, `B16/__main__.py`, `B16/settings.py:150-172`, `B16/reading.py:539-592`, `RI/hb_claim.py`,
`overlap_strata.py` (head and the command line), `seal.py` (head and status), FOCUS:72-80 (and line 74's
never-open text by a Python slice), rev4:299-303, :398-412, :757-764, :884-888, plan:36-50, the keep-working
record. `tmp/gi-vii-notes/blockB_S.zsh` (settings only).

## 5. Commands run (exit status)

| Command | Exit | Result |
|---|---|---|
| `date -u` (six times) | 0 | section header |
| `ls`, `wc`, `cat`, `sed -n`, `grep` on the reports and drafts; the Read tool on the larger reports | 0 | — |
| `git -C ROOT` log, status (code paths), `diff --quiet 55d5f8b HEAD -- scripts runkit experiments/safety_selection`, `diff --stat`, `rev-parse HEAD:<tree>` (7 trees), `ls-files .ai/inputs/stage1-post-w1-20261023/reading` (names only), `show 55d5f8b:<path>` | 0; the diff 1 | HEAD `0435c3b`; B's and C's 19 files changed since `55d5f8b`; no uncommitted code change |
| `git status --porcelain` in ws-a, ws-d1, ws-d2 (read-only) | 0 | only the tracks' files |
| `shasum -a 256` of the section-2 files in the five worktrees and the main checkout; the live kit's six top-level code files | 0 | section 2 of the runbook; repo and live kit copies equal |
| the venv's Python printing its own and numpy's version | 0 | 3.11.15, 2.2.6 |
| the venv's Python importing B16's `module_hashes` and `_strip` (code only) | 0 | 14 keys before, 12 after `_strip` |
| `zsh -n reading.zsh` (zsh 5.9) | 0 | — |
| `ast.parse` on the script's 5 heredocs (an extraction script in scratch) | 0 | 5 parsed |
| the helpers `ledger`, `lines_check`, `prov` and the step-2 comparison, sourced from the script and run on a synthetic world (fake manifest, fake files, fake outputs) | 0 where expected; 1 where a refusal was planted (a wrong seal; an absent file; a wrong overlap line) | as expected; `noclobber` refused an overwrite |
| `zsh -n` on the runbook's 10 zsh blocks; `ast.parse` on its 5 heredocs (three times, after each edit) | 0 | — |
| the ledger pre-check heredoc on two synthetic `plan.json` worlds | 0, 1 | pass; `missing ["a-1:0"]` |
| the extractor heredoc on three synthetic run folders (all passed; a refused `cost_table`; a failed 4b provenance check and a refused draw); a second run on an existing record | 0, 0, 0; 1 | the record and the words table; the failure wordings; the exclusive create refused |
| `rm -r` of the synthetic scratch `builds/tmp/runbook-check` (544 KB) | 0 | deleted; `builds/tmp/` holds only other tracks' files |

One command was never run: a scratch command that began with `rm -rf` of a scratch sub-folder was stopped by the
tool's own safety check (a variable in the path); I wrote a fresh folder instead and deleted the scratch at the end
by its explicit path.

## 6. Acceptance criteria (the brief)

| Criterion | State |
|---|---|
| `reading-runbook.md` and `reading.zsh` in `scratchpad/builds/runbook/` | passed |
| D-5 VERIFIED: step 4b runs `sg_coherent`; `cost_table` VERIFIED after fix round 2: it runs in step 4c | passed (runbook sections 0, 4, 6; the script's steps 4b and 4c) |
| Every track's open points taken: A's `--coherent-out`, new stdout lines and step 4b; B's writer and checker replacing step 0.4 and the hash table; C's never-changes hashes and the similarity steps; D1's step 4c; D2's step 5 with `OCT9KEY`, `V3` and `mkdir -p $RUN/hlc` | passed (section 9 of the runbook, changes 1-9) |
| The record drafts: the pre-run with the same options and `--no-overlap`; the step-2 comparison without the counts document's hashes; S1-S9 with the §39 8(d) exceptions; D-5 item 8's wording when a reader refuses | passed (changes 1-3, 12, 18) |
| LR: R3.1 never list `retrieved/`; R4.4 the readers' exception; R4.5 the cost-ledger pre-check | passed (changes 6-8) |
| Hashes from the worktrees for changed and new files, the main checkout for unchanged ones | passed (section 2) |
| `[FILL-<name>]` markers for the similarity path and SHA-256, the strata's SHA-256, the inputs file's SHA-256, the merge commit, the second manifest | passed (the markers table) |
| `reading.zsh` stops only on identity lines; logs every step's exit code; prints no outcome value; writes every output under `$RUN` with exclusive create | passed by reading and by the synthetic checks; the end-to-end run is the lead's rehearsal (step 0.5) |
| R1D's structure kept where nothing changed; a "Changes from R1D" section | passed (section 9: 20 changes with sources; the unchanged list) |
| `zsh -n` on `reading.zsh` | passed (exit 0) |
| Match the surrounding code and records (docstrings with usage lines, plain comments, naming, refusals with exit codes, canonical JSON and exclusive create) | passed by my reading: the script's header is a usage docstring; the heredocs print JSON only; the extractor writes with `open(out, "x")` and `sort_keys`; exit 0/1/2 as the neighbouring tools |
| Plain, short sentences | passed by my reading |
| Run on real data | not done, by rule |

## 7. Hard-rule log (disclosures; no breach of the letter that I know of)

1. `git ls-files .ai/inputs/stage1-post-w1-20261023/reading` printed file names, among them
   `reading/b14/similarity.json`, `reading/b14/strata/strata.json` and `reading/b14/inputs/overlap_inputs.json`.
   Names only; none opened, hashed or listed further. The folder is not on the never-open list.
2. `shasum -a 256` on the live kit's `tmp/stage1-olmo/{stage1_rules,seal,plan_tool,judge_units_stage1,finisher}.py`
   and `setup/job_runner_stage1.py`: code files only (hard rule 1: "Reading CODE is always fine"); track C hashed
   the same files.
3. FOCUS line 74 at `55d5f8b` was read through a Python slice around the word "never" (a record line, not sealed),
   to quote the never-open entry.

## 8. Open points for the lead

1. **Fill before the commit:** `STAMP` and `STRATA_SHA` in `reading.zsh`; the runbook's seven markers (its markers
   table says who fills each). The copy `$RD/reading-$STAMP.zsh` must be byte-identical to the filled
   `reading.zsh`, and the manifest names both files.
2. **The mode argument** is new against R1D's "one pre-committed script": confirm that the (c) route is run as
   `no-coherent` with the choice recorded in FOCUS and the ledger (section 4 of the runbook), rather than by a new
   stamp. The first attempt's console and logs are kept under `$RD/run-$STAMP-attempt1/`.
3. **R1D's provenance checks were wrong** (item 6 of section 1). If the lead's own copy of R1D's step-3 heredoc is
   used anywhere else, it needs the same correction.
4. **Step 0.2 parses the seal records** for paths and hashes (as the builder does at R1b) and hashes the listed
   files by exact path; it walks no folder. Confirm this fits the lead's reading of the never-open list; it is
   optional.
5. **The manifest's named records:** the addendum, the S1 blinding record `[FILL-S1-RECORD]` and
   `docs/study-plan-full.md` are named; the writer refuses an uncommitted tracked named file. Add or drop names
   before step 0.6.
6. **cap_reports' and cost_table's `kit.seals`** are expected to hold exactly A and B (the reading's blocks). If a
   reader writes another set, `prov` logs false (never a stop); the rehearsal shows it.
7. **The count lines** of R1b and step 2 (50 cells, 47 reference units, 71 judged units in block B, 51 HarmBench
   units, 50 x 200 counts) are inferences; a wrong one is logged under `missing_count_lines`, never a stop.
8. **The brief's state line is stale:** "the main checkout's code is unchanged since 55d5f8b" no longer holds
   (`53f746d` merged B and C; `b5e3c27` wrote the B14 records). The runbook cites `55d5f8b` for rule sources and
   takes the merged files' hashes from the worktrees, which equal the main checkout's (M).
9. **Not tested:** the script end to end; every tool on real data; the `ots` client on the second stamp; the
   durations marked E. The rehearsal (step 0.5) on the builder's `synth_kit` is the first run.

## 9. Replies to questions

No question from GPT or the lead reached me during this task.

## Fix round 1 (after `runbook-verify1.md`)

- **Written** 2026-11-01, finished about 16:40 UTC (clock checked with `date -u` at 16:22:54, 16:34:53-16:36:05,
  16:37:14 and 16:38:19 UTC), by the runbook builder; the launcher records the model.
- **Files now:** `runbook/reading-runbook.md` (946 lines, SHA-256
  `a0753d008c835f6cbc1d1ea6ee2a88864f95be6f97c203713e189f97aefbd3dc`) and `runbook/reading.zsh` (338 lines,
  `a1b2d75980b2910208f0523693555a61838f09b1956c0c76dcf91b4f368e8fb7`). Evidence of this round:
  `reports/runbook-fix1-dryrun/` (31 files, 1.3 MB: consoles, ledgers, records, extractor prints, the copy maker,
  the heredoc checker, the writer and extractor as extracted from the runbook, the refusal prints). The scratch
  world `builds/tmp/runbook-fix1/` (78 MB) is deleted.
- **Data rules kept** as in the build: nothing sealed or outcome-bearing was opened, hashed, grepped or listed; every
  run was on ws-a's synthetic `synth_kit` world; no real-data command, no network, install, pod or API call, no
  background job, no git write. Disclosures in F.6.

### F.1 The defect D1 (`[FILL-0]`): fixed

The verifier's reading is right: `[FILL-0]` asked for values that exist only after the commit and the anchor (the
runbook's and the script's SHA-256, the manifest's SHA-256 and anchor, the height `H`), so following it would edit a
pinned file after step 0.6 and make R0 stop (S1). The fix (runbook changes 21 and 22):

1. The markers table splits the marker: `[FILL-STAMP]` (the stamp's date label; filled before the commit, in Block R,
   section 3's `checks-$STAMP` and the script's `STAMP=FILL-STAMP`) against a "never filled here" row for the
   post-commit values, which go to the manifest, FOCUS and `TS/ots-check-reading-$STAMP.json`, bound by the third
   stamp (step 6 item 4). A sentence names R1D:28 as the source of the mixed marker.
2. The pins table's last row no longer carries a marker: plan.json, the runbook and the script are hashed by the
   writer at step 0.6 and re-checked by R0; the manifest's own SHA-256 and anchor are recorded in FOCUS.
3. Step 0.3 no longer types a height: it runs the lead's `RD/lead-reports-20261101/tools/ots_check.py` (the tool
   used for the first stamp; its record format is `TS/ots-check-20261101.json`), which reads every Bitcoin
   attestation out of the proof and writes its record by an exclusive create; a `curl` of both tips gives the
   confirmation margin. Step 0.6 and step 6 item 3 say the post-commit values are never written back.
4. Found while fixing D1 and fixed: the `ots` venv was made under `$SCR`, but R0 requires `$SCR` empty and the
   client must be kept until the third stamp is verified. It now lives in its own folder `$OTSDIR`
   (`/private/tmp/stage1-reading-ots`; Block R sets `OTS` and `OTSPY` from it), deleted after the third stamp.

### F.2 The notes taken (1-8, 13, 14) and the two left

| Note | What changed | Where |
|---|---|---|
| 1 (step 5's citation) | step 5's never-stop now cites rev4:762 (report-only) and E-misc B ruling 3; §39 8(d)(i) is cited for 4b and 4c only; section 7 asks the lead to add step 5 to 8(d)(i) in the records or keep the two sources | script header and step-5 comment; runbook S1, the step-5 table row, section 7, change 25 |
| 2 (state one commit stale) | HEAD `c21dccb`; `scripts/stage1_s1` `46bdebf8`; the commit named (one test file and three reports; no section-2 file); "the manifest, not this section, is the pin" | section 1; section 2's caption |
| 3 ("about 90 files") | `"files": 72` with the count's parts (33 + 27 + 4 + 8); the printed count is the record. M: all three dry-run manifests printed 72 | step 0.6 |
| 4 (the rehearsal cannot run the script unedited) | step 0.5 says the rehearsal runs an edited copy (`ROOT`, `PY`, `STAMP`, `SCR`, `STRATA_SHA`, the two B14 lines) with a stand-in `git`, and names the verifier's dry run as the worked example | step 0.5 |
| 5 (provenance noise after a refusal) | `extra` and step 4b skip `prov` when the reader exited non-zero (nothing was written); the ledger line `…-provenance` is exit 1 with `note=not run: the reader wrote no output (its exit N)`; no console line about a check of a missing file. The extractor's branches are unchanged (a refused reader prints its REFUSED line; M on run `20261197`) | script `extra`, step 4b; runbook table rows 4b and 4c, S1, change 24 |
| 6 ("the draw refused" for any exit) | the console says `the draw did not run (exit N; 2 = refused, nothing written; no outcome shown)` | script step 5; runbook table row 5 |
| 7 (`sensitivities`, `actors`) | both copied into the record's `copied_from_b16` (`B16/reading.py:586-587`); M: present in all three dry-run records | step 6's extractor; change 26 |
| 8 (change 7's wording) | each reader's own binding named (`reading.json` for three, `sources.json` for `cap_reports`, `plan.json` and the seals for `cost_table`) | change 7; the 4c table row |
| 13 (the ledger is appended) | the helper opens with `"x"` when the file does not exist and `"a"` after; the script header states the ledger is the one file written more than once | script `ledger` and header; change 27 |
| 14 ("run-attempt1's log") | the (c) wording names `run-<STAMP>-attempt1/logs/R1b-builder-prerun.txt` (M on run `20261198`: `run-20261198-attempt1/logs/R1b-builder-prerun.txt`) | step 6's extractor; change 26 |
| 9 (step 0.2) | no change: optional, not on the script's path; now listed under section 7 as the lead's call | section 7 |
| 10, 11, 12 | no change needed (count lines logged; the step-5 ledger line hashes two sealed files without content; R1D's provenance defect confirmed) | — |

Also from the verifier's replies: (5) the manifest writer now refuses a missing named file (an unfilled
`[FILL-S1-RECORD]`) and an uncommitted pinned path with `REFUSED: …` and exit 2, as the tools do (M: both refusals
tested, nothing written); (1) the fill-before-commit list is written out at step 0.6.

### F.3 The decisive check: the dry run repeated on the edited script

The verifier's world was mostly deleted (only the synthetic kit remained), so I rebuilt one under
`builds/tmp/runbook-fix1/`: code by symlink to the main checkout (`experiments/`, `scripts/stage1`, B16, the merged
`stage1_s1` files, `runkit/stage1-olmo`'s code and tests; nothing there was copied or listed), the three packages
copied from ws-a, ws-d1 and ws-d2, ws-a's `synth_kit` by the verifier's `build_world.py` (strata `310fa190…`,
report `e074bb2c…`, as in the verifier's run), the verifier's stand-in `git`, placeholders for the named records,
the manifest writer and the extractor extracted from the edited runbook (`check_blocks.py` style regex, asserted).
`make_copies.py` made three copies of `reading.zsh` (7 lines differ, the same seven as the verifier's; the third also
points step 4b's `--counts` at a missing file). Results (`reports/runbook-fix1-dryrun/`):

| Run | Mode | Manifest | Script | Ledger | Extractor |
|---|---|---|---|---|---|
| `20261199` | coherent | exit 0, 72 files | **exit 0, `READING STEPS R0-5 DONE`** (16:35:37-16:35:47 UTC) | 29 lines; `4c-cap_reports` 2, `4c-cost_table` 2 (their provenance lines exit 1 "not run"), `5-hlc-draw` 2, every other step 0 | exit 0 |
| `20261198` | no-coherent | exit 0, 72 files | **exit 0, DONE** | 28 lines (no `4b-provenance`; `4b-sg-coherent` 0 with the (c) note) | exit 0 |
| `20261197` | coherent, 4b forced to refuse | exit 0, 72 files | **exit 0, DONE** | 29 lines; `4b-sg-coherent` 2, `4b-provenance` 1 "not run: the reader wrote no output (its exit 2)" | exit 0; the record prints D-5 item 8's wording with the reader's own `REFUSED` line |

Checks on those runs (all held): the consoles hold only the mode line, `step 4c (…): exit 2, logged; report only…`
(two), the step-5 "did not run" line, `DONE`, JSON lines, dates and the ledger's hash; none of the 7 distinct words of
the records' headlines, sentences and U-part words appears in any console; `4b-provenance.txt` and `sg/` are absent
in run `20261197`; the normalized diff against the verifier's round-1 console (hashes, times, paths masked) differs
only by the two new notes and step 5's line (exit 2 here, since `experiments/minimal_safety` is reachable; the
verifier's root lacked it on its first run). R1b-check and 2-check: `identity_lines` 9 (8 in no-coherent),
`missing_identity []`, the same five count lines missing as in the verifier's run; the step-2 comparison all true.

### F.4 Commands run (exit 0 unless noted)

`date -u` (five); reads named in runbook section 8's fix-round row; `git -C ROOT` log, status (clean), rev-parse
`HEAD:<tree>` (`reading_extra` and `hlc_draw` fatal, as expected: not merged), `show --stat HEAD`, `show
55d5f8b:` B16's `reading.py:535-595` and `TS/stamp-record-20261031.json:1-45,37-39`, `show HEAD:` `ots_check.py`
and `ots-check-20261101.json` (head), `ls-files` of `TS/` and `lead-reports-20261101/tools/` (names only); `grep
FILL` on R1D's committed copy; `ls` of `builds/verify-runbook/v1/` and `du` (scratch); the Edit tool on the two
deliverables (33 edits); `zsh -n reading.zsh` (0, three times); `check_blocks.py` (5 + 5 heredocs parse; 10 zsh
blocks `zsh -n` 0; three times); the world build (`ln -s`, `rsync` of the three packages, `build_world.py`); the
manifest writer three times (0) and twice refusing (2, 2); the script copies three times (0, 0, 0; one earlier loop
failed at the writer with `FileNotFoundError` for `tmp/stage1-olmo/seal.py`, my root's omission, fixed by three
symlinks; the three runs of that loop stopped at R0 as designed, no manifest existed); the extractor three times (0);
the checks of F.3 (Python one-liners; one with an f-string typo, re-run); `cp` of the evidence; `rm -r` of
`builds/tmp/runbook-fix1` and of a check temp folder by explicit paths; `shasum -a 256` and `wc -l` of the two
files.

### F.5 Acceptance criteria after the fix round

| Criterion | State |
|---|---|
| D1 fixed: the markers split; no post-commit value is written into the pinned runbook | passed (F.1; the markers table; `[FILL-0]` survives only in two historical mentions) |
| Notes 1-8, 13, 14 taken | passed (F.2) |
| Notes 9-12 | 9 left to the lead (section 7); 10-12 no change needed |
| `reading.zsh` stops only on identity lines; logs every step's exit code; prints no outcome; exclusive creates | passed (F.3: three runs; the ledger created once then appended, stated) |
| `zsh -n`; heredocs parse; the runbook's zsh blocks parse | passed |
| R1D's structure; "Changes from R1D" updated | passed (changes 21-28 added) |
| Match the surrounding code and records | passed by reading (the writer's refusals now `REFUSED: …`, exit 2) |
| Run on real data | not done, by rule |

### F.6 Hard-rule log (disclosures; no breach of the letter that I know of)

1. Symlinks from the synthetic root to the main checkout's code folders (`experiments/`, `scripts/stage1`,
   `scripts/stage1_s1/{reading,settings,mutation,…}`, `runkit/stage1-olmo/{seal,plan_tool,judge_units_stage1}.py`,
   `runkit/stage1-olmo/tests`): no content was read or listed by me; Python imported only the modules the tools
   import, and the writer hashed only its listed code files, as it would on the real tree.
2. `git ls-files` of `TS/` and `lead-reports-20261101/tools/` printed file names (a records folder, not on the
   never-open list); the lead's `ots_check.py` and the first stamp's check record were read (records, no outcome).
3. The verifier's `build_world.py` printed the synthetic kit's entry names (synthetic; no real kit path).
4. `rsync` copied `reading_input/`, `reading_extra/` and `hlc_draw/` from the worktrees (code and their tests; no
   name with plant, decoy, hidden or selector exists in those packages' listings as copied; nothing printed).

### F.7 Open points for the lead (this round)

1. **Step 5 in §39 8(d)(i)** (verifier's note 1): add step 5 to the record, or keep the runbook's two sources
   (rev4:762; E-misc B ruling 3).
2. **The verifier's `make_copies.py`** matches the settings lines by prefix; the `STAMP` line now begins
   `STAMP=FILL-STAMP`; my adapted copy in `reports/runbook-fix1-dryrun/make_copies.py` matches the edited script.
3. **The second stamp's check record** is named `TS/ots-check-reading-$STAMP.json` (the lead's tool writes it);
   rename if the lead prefers the first stamp's `ots-check-<date>.json` pattern, in step 0.3 and the markers table.
4. **`$OTSDIR`** (`/private/tmp/stage1-reading-ots`) is kept until the third stamp is verified; it is outside `$SCR`
   so that R0's empty-`$SCR` check holds. The first stamp's client was not kept, so the install needs the lead's go.
5. **Step 0.2** stays optional and the lead's call (section 7).
6. **Not tested** (unchanged in kind): every tool on real data; `ots_check.py` on the second stamp; B14's `report`
   inside the script; the draw's success path; the count lines' values.
