# Verification of the final reading runbook and its script (round 2, after fix round 1)

- **Written** 2026-11-01, finished about 17:10 UTC (clock checked with `date -u` at 16:56:26-16:57:04 UTC, the dry
  runs' own consoles, and at 17:08:14 UTC), by an independent verifier for the main-study lead (GI VIII); the launcher
  records the model.
- **Files verified:** `builds/runbook/reading-runbook.md` (SHA-256
  `a0753d008c835f6cbc1d1ea6ee2a88864f95be6f97c203713e189f97aefbd3dc`, 946 lines) and `builds/runbook/reading.zsh`
  (`a1b2d75980b2910208f0523693555a61838f09b1956c0c76dcf91b4f368e8fb7`, 338 lines): the bytes the builder's fix-round
  report names (`runbook-build.md`, "Fix round 1", "Files now"). Read first: `builds/lead-rulings-20261101.md`.
- **Where I wrote:** `builds/verify-runbook/v2/` (2.2 MB kept: the dry run's scripts, the six consoles, ledgers, logs,
  records, manifests, diffs and check outputs; the synthetic root, the caps world and the scratch folders, 128 MB, are
  deleted) and this report. No checkout or worktree was edited; no git command changed state (read-only `log`,
  `status`, `show`, `rev-parse`, `ls-files` only); nothing under `builds/runbook/` was touched.
- **Data rules kept.** I opened, hashed, grepped or listed nothing under `tmp/stage1-olmo/{hosts,judges,judges-pending,
  seals,retrieved}`, `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, `tmp/hlc-inputs/`,
  `block-a/`, `block-b/`; not the live kit's `plan.json`, no unit, eval, answer, label, guard, cache or COMPLETE.json
  file, no bank, no path with "plant" or "decoy", and not `similarity.json`, `strata.json` or
  `overlap_inputs.json`. No reading, builder, overlap, HarmBench-claim, judge, seal, kit, draw or launch command ran on
  real data or the real kit state: every run was on a synthetic world made by the builder's own test fixture, under
  `verify-runbook/v2/root/` (deleted). No network, install, pod or API call; no background job; every command finished
  in the foreground (the longest, B16's suite, in 2 min 48 s). Section 8 lists seven disclosures (names only).

Labels: (M) measured here; (R) read in a source; (I) inference.

## Verdict: verified

I found no defect that matters for the reading's correctness, the frozen rules, the lead's rulings or blinding. Every
command in the script and in the runbook's blocks matches the tools' real command lines; every expected line matches
the print that makes it; all 64 code, settings and spec hashes in section 2 of the runbook match the worktrees or the
main checkout (the three remaining hex strings are the two seals and the first manifest, cited from FOCUS); the step
order is the plan's (B14's report, the input build, B16, the claim reader, the D-5 reader, the five reading-time
readers, the draw); the stop rules match R1D's S1-S9 with the three changes of §39 8(d) and the (c) route of D-5
item 8; no step opens a never-open path outside the readers' route at 4c; nothing prints an outcome early. The script
ran end to end on a synthetic world in both modes, and three planted faults took the S1, S4 and S5 stop paths exactly
as the runbook says (section 3). Round 1's defect D1 is fixed as the fix round states (section 2). Six minor points are
notes (section 4), not defects.

## 1. What I checked and how (M unless marked)

| Check | Result |
|---|---|
| `reading.zsh` against `argparse` / `__main__` of each tool: `reading_input` (ws-a `__main__.py`: `--reading --kit --out --record --b14-strata --b14-report --expect-strata-sha256 --expect-report-sha256 --no-overlap --hb-out --coherent-out`), `reading` (B16 at `55d5f8b`: `--input --out`), `reading_input.hb_claim` (`--hb --reading --out`), `reading_input.sg_coherent` (ws-a: `--tables --counts --reading --out`), the five `reading_extra` readers (ws-d1: `cap_reports --kit --record`, `fk_power --input --reading`, `stage3_pick --reading`, `sa_shift --reading`, `cost_table --kit --reading` with `choices=sorted(READING_BLOCKS)`, each plus `main_frame`'s `--out`), `hlc_draw draw / check` (ws-d2: the positional command and `--kit --oct9-key --bank-manifest --bank --auditor --sealed --manifest`), `overlap_strata.py report` (main: `--strata --inputs --out [--data-root]`) | every option exists and is spelled as the tool takes it; every tool creates `--out` exclusively; exit 0/2 (draw `check` 0/1/2) as the runbook's exit table says |
| The runbook's other commands: the three `run_mutants.py` (`--spec --scratch --report --timeout --python --only`, lines 140-146 of each), `run_mutants_b14.py` (`--spec --scratch --report [--timeout]`, its docstring), `run_mutants_b15.py` (positional `source scratch out select`), `commitments.py check --repo`, `overlap_inputs.py --kit --strata --strata-sha256 --out`, `overlap_inputs_check.py --file --kit --strata`, `seal.py status`, the lead's `ots_check.py OUT_RECORD FILE` (reads `FILE.ots` beside, exclusive create), the requirements writer against `stamp-record-20261031.json`'s `tool.packages[name].{version,sha256}` | all as the tools take them; section 3's `T()` uses `${@:2}`, which zsh 5.9 slices as intended (`[b c]`) |
| Expected lines against the code that prints them: the builder's `summary_lines` (ws-a `__main__.py:72-106`), B16's `wrote … (<16 hex>); headline: …` (`__main__.py:35`), `hb_claim.py:286-287`, `sg_coherent.py:433-434`, `RX/common.py` `main_frame` (`wrote <file> sha256 <hex>` plus the words lines: `LN-14 transfer bar: …`, `stage-3 pick: …`), `HD/__main__.py` `_head` and `<path>: match`, `overlap_strata.py:511-517`, `seal.py:191,222`, the writer's and checker's lines | all match; the nine identity substrings of `lines_check` are substrings of the builder's real lines (`identity_lines 9, missing_identity []` in every coherent run; 8 in no-coherent); each `count_lines` entry is in the builder's format (14 entries) |
| The provenance blocks `prov` expects against the code that writes them: B16 `reading.py:577-578` after `_strip` (:539-542; `settings.py:160-165` `module_hashes`), `hb_claim.py:246-249`, `sg_coherent.py:383-387`, `RX/common.py` `provenance` and `finish` (= `_strip`), `cap_reports.py:310-311` and `cost_table.py:520-522` (`kit = {plan_sha256, seals{A,B}}` from the builder's `Kit`) | all match; `prov` passed on every real output in the dry run (B16, the claim reader, the D-5 reader, three readers) and, on a caps world, on real `cap_reports` and `cost_table` outputs with the `kit` spec (section 3, run 7) |
| The step-2 comparison's pops against the records' real keys: a deep diff of the pre-run and step-2 documents by key path | tables: `/overlap` only; sources: `/coherent/output_sha256`, `/hb/output_sha256`, `/output_sha256`, `/overlap`; hb_tables: `/input_sha256`; coherent_counts: `/input_sha256`. Exactly the popped keys, nothing else (the same in all four coherent runs; three sources keys in no-coherent) |
| The D-5 (c) route's trigger text: every refusal of `coherent.check` (ws-a `coherent.py:68-102`) | each message begins `the coherent-only counts` (`where = f"the coherent-only counts of {arm} {j}"`, :83); `build()` runs the check after B16's schema check (:702, :713), so the script's "stderr begins `REFUSED: the coherent-only counts`" is exact |
| Hashes: every file in runbook section 2 recomputed from ws-a (reading_input changed and new), ws-d1, ws-d2, the main checkout (B16, the unchanged reading_input files, B's and C's merged files, W1 files, the bars file, the specs) and the live kit's four code files; ws-b and ws-c compared with main (`v2/hashes.py`) | 64 of 64 found in the runbook's text; ws-b = main and ws-c = main for all 10 files compared; the runbook's hex strings with no file here are exactly `68e75447…`, `6c6267c8…`, `b4e11dc9…` (the first manifest and the two seals, cited from FOCUS) |
| Spec entry counts and survivors | reading_input 47 (0 survivors), reading_extra 62 (`RX-common-exclusive`), hlc_draw 65, b14 150, b15 418, b16 117, the near set 69 at `77c3def1…`: as the runbook says |
| B16's settings pin `fef3b6f5…` = `settings.py:21` = the file's hash | equal |
| The state section: HEAD `c21dccb`; code paths clean; the seven tree ids; the venv `3.11.15 2.2.6`; zsh 5.9 | all as section 1 says |
| Order: R0, R1a, R1b, 1 (B14), 2 (build), 3 (B16, provenance, re-run), 4 (claim reader), 4b (D-5 reader), 4c (five readers), 5 (draw, check) | PLAN:37-49 at `55d5f8b` (1 B14, 2 build, 3 B16, 4 claim reader, 5 draw); B16 before every reader; the draw after the reading (LR R5.5); 4c after the input build, B16 and the claim reader (LR R4.4, R6.3) |
| Stop rules against R1D:718-738 (committed copy `9ae23f5e…`), E-39 §39 8(a)-(h), E-D5-D6 item 8 and last fallback (c), LR R6.1, R6.5 | S1 gains the 4b/4c exception (8(d)(i)) and the step-5 exception (rev4:762; E-misc B ruling 3, both hold at their lines); S2 gains the attempt copy and the (c) route; S3, S4, S6-S9 as drafted; S5 gains the 4b/4c logging; the references line is not an identity line; the count lines are logged. The script's `fail` calls name S1, S2, S4, S5, S6 at the steps the rules name |
| Never-open paths: what each step opens | R1a/1: B14's tool on the units (the plan's step 1); R1b/2: the builder (step 2); 4c: `cap_reports` and `cost_table` only inside the script after the input build (LR R4.4); 5: the draw (step 5); R0 and step 0.6 hash `plan.json` and the two seal records, as the first manifest did (FOCUS:75 at `55d5f8b` names `seals/block-A.json` and `seals/block-B.json`); step 0.7 tests `is_file()` by exact path (LR R4.5) and reads only `plan.json`'s job records (`status`, `pulled`, `outputs`, `done`: the kit's own field names, `plan_tool.py:941,1734`, `job_runner_stage1.py:880-882`); step 0.2 is optional and walks no folder; `retrieved/` is never listed; `tmp/hlc-inputs/` is only passed to the draw |
| Nothing prints an outcome early | every tool's stdout goes to its step log; the console holds dates, the mode line, ledger JSON lines (step, exit, hashes, a note), the two 4c notes, the step-5 note, `DONE` and the ledger's hash (M: every non-JSON console line of run 20261299 listed in `v2/analyze.out`); none of the eight outcome words of the logs and outputs (`better`, `worse (U)`, `inconclusive`, `equivalent (per comparison)`, `harm`, `restored refusal`, `no restored refusal shown`, `holds on the less similar half`) and no U estimate string appears in any of the six consoles; R1a's stdout is discarded |
| `zsh -n reading.zsh`; `ast.parse` of its 5 heredocs; `zsh -n` of the runbook's 10 zsh blocks and `ast.parse` of its 5 heredocs (`v2/extract_blocks.py`) | all exit 0 / parse |
| Suites in the worktrees and the main checkout, each on a fresh basetemp under `builds/tmp/`, deleted after | `reading_extra` 120 passed (21 s); `hlc_draw` 123 passed (22 s); `reading_input` 284 passed (118 s; basetemp 2.8 GB); B16 261 passed (168 s): the runbook's `rx`, `hlc` (its 123 part), `ri` and `b16` counts hold |

## 2. Round 1's defect D1, re-checked

- The markers table splits `[FILL-STAMP]` (filled before the commit: Block R, section 3's `checks-$STAMP`, the script's
  `STAMP=FILL-STAMP`) from a "never filled here" row (the two files' SHA-256, the manifest's SHA-256 and anchor); the
  pins table's last rows carry no marker; step 0.3 reads the height from the proof by the lead's `ots_check.py` and
  types none; steps 0.6 and 6 say the post-commit values go to the manifest, FOCUS and
  `TS/ots-check-reading-$STAMP.json`. `[FILL-0]` survives only in two historical sentences (lines 50 and 915). (M, grep.)
- The reproduction still holds the other way: run 20261295 (section 3) appended one byte to the pinned runbook copy
  after the manifest was written; R0 printed `"files_differ": [".ai/…/reading-runbook-20261295.md"], "pass": false`
  and the script stopped with `STOP at step R0: … (S1)`, exit 1, two ledger lines, nothing after. So an edit after step
  0.6 is caught, and the runbook no longer asks for one.
- The `ots` client's folder `$OTSDIR` lies outside `$SCR` (Block R), so R0's empty-`$SCR` check
  (`test -z "$(ls -A "$SCR")"`) is not tripped by it.

## 3. The dry run on a synthetic world

- **World.** The builder's own fixture, ws-a `reading_input/tests/synth_kit.py`: `make(root, "plan_a", seed=0,
  hb=True)` (50 cells, HarmBench pods for both blocks, the two seals, B14's strata `310fa190…` and a report in B14's
  format `e074bb2c…`, the same hashes as round 1's and the fix round's worlds: the fixture is deterministic). No caps
  and no cost ledgers, so `cap_reports` and `cost_table` refuse (the never-stop path); the draw's inputs are absent, so
  the draw refuses (its never-stop path).
- **ROOT** `v2/root/` (deleted after): the main checkout's `experiments/safety_selection`, `experiments/minimal_safety`,
  `scripts/stage1`, the two frozen readers, every top-level entry of `scripts/stage1_s1` except `reading_input` and
  `tests`, and `runkit/stage1-olmo/{seal,plan_tool,judge_units_stage1}.py` and `tests` by symlink; ws-a's
  `reading_input/`, ws-d1's `reading_extra/` and ws-d2's `hlc_draw/` by copy; the synthetic kit at `tmp/stage1-olmo/`
  with the three kit code files beside it; the synthetic rules module at `runkit/stage1-olmo/stage1_rules.py` and in
  the kit; placeholders for the addendum, the study plan, the S1 record, `b14/inputs/overlap_inputs.json` and
  `b14/similarity.json`; a `.git` folder and a `.gitignore` with `tmp/`. A stand-in `git` (`v2/bin/git`) answers
  `rev-parse` with fixed strings and `status` with nothing.
- **Copies** (`v2/make_copies.py`, each replaced line asserted to match once): 7 lines differ from `reading.zsh`
  (`v2/diff-coherent-copy.txt`): `ROOT`, `PY`, `STAMP`, `SCR`, `STRATA_SHA`, and the two B14 lines (R1a and step 1),
  where `overlap_strata.py report` is replaced by a copy of the synthetic report (no B14-compatible synthetic kit exists
  beside the builder's world). Three variants add one planted fault each: step 4b's `--counts` at a missing file;
  `STRATA_SHA` all zeros; step 3's provenance check expecting `reading=plan_b`. The manifests were written by the
  runbook's own step-0.6 writer, extracted verbatim (`v2/blocks/manifest_writer.py`): `"files": 72` each; the pinned
  runbook and script copies sat at `$RD/reading-runbook-$STAMP.md` and `$RD/reading-$STAMP.zsh`.

| Run | Mode, fault | Exit | Ledger | What happened |
|---|---|---|---|---|
| 20261299 | coherent | **0, `READING STEPS R0-5 DONE`** | 29 lines, every step 0 except `4c-cap_reports` 2, `4c-cost_table` 2 (their provenance lines 1, `not run: the reader wrote no output (its exit 2)`), `5-hlc-draw` 2 | R0 all true; R1b `identity_lines 9`; step 1 `cmp` equal; step 2 `overlap: strata 310fa190…, report e074bb2c…`, the comparison all true; B16 `prov` all true, the re-run byte-identical (equal SHA-256); the claim reader, the D-5 reader, `fk_power`, `stage3_pick`, `sa_shift` `prov` all true; the console holds no outcome word or number |
| 20261298 | no-coherent | **0, DONE** | 28 lines; `4b-sg-coherent` 0 with the note `not run: D-5 went to its last fallback (c) at the pre-run (mode no-coherent)` | `identity_lines 8`; the builder printed `coherent-only counts: not built (no --coherent-out)`; `${COH_PRE[2]}` and `${COH_RUN[2]}` vanish as intended; no `sg/` output |
| 20261297 | coherent; 4b's counts file missing | **0, DONE** | 29 lines; `4b-sg-coherent` 2 (`REFUSED: an unexpected FileNotFoundError (its message is withheld…)`), `4b-provenance` 1 "not run" | no `4b-provenance.txt`, `sg/` empty; the record prints D-5 item 8's wording with the reader's REFUSED line |
| 20261296 | coherent; wrong `STRATA_SHA` | **1** | 8 lines, `2-builder` 2 | R1b (no overlap) and step 1 passed; the builder refused at step 2 (`B14's strata file hashes to 310fa190…, the sealed value is 0000…`); `STOP at step 2: the builder refused (S4)`; nothing after; the console shows no value |
| 20261295 | coherent; one byte appended to the pinned runbook after the manifest | **1** | 2 lines, `R0-pins` 1 | `STOP at step R0: … differs from the second stamp (S1)` (section 2) |
| 20261294 | coherent; step 3's `prov` expects `plan_b` | **1** | 12 lines, `3-provenance` 1 | `3-provenance.txt`: `"reading": false, "pass": false`, every other check true; `STOP at step 3: B16's provenance is not the pinned input, code, settings or Python (S5)`; nothing after |
| 7 (`v2/caps_check.py`) | a caps world (`synth_kit` `hb=False` + `extra_kit.with_caps`) and `extra_kit.cost_kit(…, "plan_a")`, by hand | — | — | `cap_reports` exit 0 (`LN-14 transfer bar: passes`), `cost_table` exit 0; the script's `prov` body verbatim with `reading=plan_a modules=…reading_extra/:* b16 [input:sources.json=…] kit` against a manifest of that kit: **all true** for both; against the other kit's manifest `kit: false`; with `tables.json` as the sources input `input:sources.json: false`. Their `kit.seals` hold exactly A and B. The extractor's key lists for both readers: no key missing from the real outputs. The step-0.7 pre-check on the cost kit: `present 57 = jobs_complete_pulled 57, missing [], pass true`, exit 0; on the ledger-less synthetic kit: `missing` lists 70 host:job labels, exit 1 |

- Also: `reading-dry-20261299.zsh bogus` → `usage: reading.zsh [coherent | no-coherent]`, exit 2; a second start with
  the run folder present → `STOP at step R0: … run-20261299 exists`, exit 1, before any step. The extractor
  (`v2/blocks/extractor.py`, verbatim) on the three finished runs: exit 0 each, the words table in four columns (the
  no-coherent and the refused-4b runs print `S-G coherent: not computed`), `copied_from_b16` with `sensitivities` and
  `actors`, `mode` from the ledger, the (c) wording naming `run-20261298-attempt1/logs/R1b-builder-prerun.txt`; a second
  run on the same folder: `FileExistsError` (the exclusive create). The step-0.2 seal check on the synthetic kit:
  `listed 367 / 726, same = listed, differs 0, missing 0`, exit 0 (the record layout of `seal.py:115,130,150`).
- **Negative tests of the helpers** (`v2/neg/`, the Python bodies verbatim): `lines_check` with a wrong overlap line
  names it in `missing_identity`, exit 1; with a `--outs` file whose hash is not the printed one, likewise; `prov` with
  one wrong B16 module hash in the manifest: `modules: false` only, exit 1; the claim reader's output with the wrong
  reading file bound: `reading_sha256: false` only; a missing output: `file: false`, exit 1. No check is vacuous.
- `zsh`'s `noclobber` refuses a second `>` to an existing file (exit 1, the first content kept); `>| /dev/null` and
  `> /dev/null` both work (M), so the script's `>|` at R1a is safe either way.

## 4. Notes (minor; not defects)

1. **`[FILL-SIM-PATH]` has no slot.** It is defined in the markers table (line 43) and listed to fill at step 0.6
   (line 433), but no body line carries it (M: two occurrences, both these). Nothing is lost (the path goes to FOCUS,
   LR R3.1); either drop it from the fill list or give it a slot.
2. **S2's "delete the empty `$RUN`".** After a stop at R1a or R1b the run folder holds `logs/`, the ledger and the
   empty subfolders. Say "copy the run folder's logs and ledger to `$RD/run-$STAMP-attempt1/`, then delete `$RUN`";
   the ledger of the attempt is worth keeping beside the logs. The first attempt's console file is overwritten by the
   second attempt's redirect, so the copy (or a move) must come first, as S2 already orders.
3. **Step 0.7 is weaker than `cost_table`'s own check,** by R4.5's own words ("existence only"): a ledger that exists
   on disk but is not listed in the seal, or not classed readable, still makes `cost_table` refuse at 4c
   (`cost_table.py:246-253`). On the real kit the seals were written from the pulled trees, so a ledger on disk at seal
   time is in the seal; the gap is a ledger written after the seal. Report only either way.
4. **`prov` checks no `kind` for the five readers** (each has its own KIND; the extractor copies by key). A `kind=`
   spec per reader would be one word each.
5. **Step 0.3's `grep -c BitcoinBlockHeaderAttestation` on `ots info`** is untested here (the first stamp's records
   hold no `ots info` output); `ots_check.py` reads the attestations from the proof itself, so the grep is only a
   convenience line.
6. **Step 0.2 (optional)** hashes every sealed file by its exact path from the seal records (no walk): consistent with
   LR R3.1's letter; the lead's call, as the builder's F.7 point 5 and round 1's note 9 say.

## 5. Acceptance criteria (the builder's brief)

| Criterion | State |
|---|---|
| Final runbook and script in `builds/runbook/` | passed |
| D-5 VERIFIED: step 4b runs `sg_coherent`; `cost_table` VERIFIED after fix round 2: it runs in step 4c | passed (sections 0, 4, 6 of the runbook; the script's 4b and 4c; both ran in the dry run, `cost_table` on the caps world) |
| Every track's open points: A's `--coherent-out`, new stdout lines, step 4b; B's writer and checker in place of step 0.4 and the hash table; C's never-changes hashes and the similarity steps; D1's step 4c; D2's step 5 with `OCT9KEY`, `V3`, `mkdir -p $RUN/hlc` | passed (runbook section 9; the hashes and commands checked here) |
| The record drafts: the pre-run with the same options and `--no-overlap`; the step-2 comparison without the counts document's hashes; S1-S9 with §39 8(d)'s exceptions; D-5 item 8's wording when a reader refuses | passed (the deep diff shows the pops are exactly the differing keys; the wording seen in run 20261297's record) |
| LR R3.1, R4.4, R4.5 | passed (`retrieved/` never listed; the readers' exception at 4c only; step 0.7 existence only) |
| Hashes from the worktrees for changed and new files, the main checkout for unchanged ones | passed (64 of 64) |
| `[FILL-<name>]` markers for later values; no post-commit value written into the pinned runbook | passed (note 1 on one unused marker) |
| `reading.zsh` stops only on identity lines; logs every step's exit code; prints no outcome value; writes every output under `$RUN` by exclusive create | passed (six runs; the ledger created once then appended, as stated) |
| R1D's structure kept; "Changes from R1D" with sources | passed (28 changes; the fix round's 21-28 each match a round-1 note or D1) |
| `zsh -n` | passed |
| Matches the surrounding code and records | passed by reading (usage header, `REFUSED: …` and exit 2 in the writer, canonical JSON, `open(…, "x")`) |
| Plain, short sentences | passed by reading |

## 6. Replies to the builder's open points (F.7)

1. Step 5 in §39 8(d)(i): the lead's call; the two sources hold as cited (rev4:762 at `55d5f8b`: LW-30, "it adopts
   no spend"; E-misc B ruling 3, line 143: "No step 5 at the reading").
2. `make_copies.py`: my `v2/make_copies.py` matches the fixed script (7 lines, each matched once) and adds the three
   fault variants.
3. The check record's name: the lead's call; the tool takes any `OUT_RECORD` path.
4. `$OTSDIR` outside `$SCR`: right, since R0 requires `$SCR` empty (section 2).
5. Step 0.2: note 6.
6. Not tested: unchanged in kind (B14's `report` inside the script; the draw's success path and `check`; the count
   lines' values; the `ots` client). This round adds the S4 and S5 stop paths, the re-run refusal, and `prov`'s `kit`
   branch on real `cap_reports` and `cost_table` outputs.

## 7. Not verified, and limits

- `overlap_strata.py report` never ran inside the script (a copy of the synthetic report stood in at R1a and step 1,
  as in both earlier dry runs). Its byte-identity between R1a and step 1 rests on `report()`'s provenance holding no
  time or output path (`overlap_strata.py:474`, `s1common.provenance`) and on B's verified suite.
- The draw's success path and `check` did not run (the builder's world lacks the draw's inputs; its own world is a
  different kit); its refusal path and the script's handling of a non-zero exit did.
- `cap_reports` and `cost_table` ran to success only by hand on the caps worlds (run 7), not inside the script; inside
  the script they ran to their refusals.
- The real kit, the real stamps, the `ots` client, the durations marked E and the count lines' values on the real kit
  are untested by rule or by nature. The `s1`, `w1`, `engx`, `kit` and `judges` suites and every mutation spec were not
  run here (the lead's background runs).

## 8. Commands run (exit 0 unless noted) and disclosures

- `date -u` (three times, and the dry runs' own). Reads of the runbook, the script, the builder's report with its fix
  round, round 1's report, the rulings, E-39, E-D5-D6, E-misc, E-records-verify3, R1D's committed copy (markers, pre-runs,
  S1-S9), FOCUS:70-80 and PLAN:28-56 at `55d5f8b`, rev4:400, :762-763, :886-887, ADD:375 (`git show`), the lead's
  `ots_check.py`, the first stamp's check and stamp records (keys only), and the code named in section 1 (the worktrees
  and `git show 55d5f8b:`).
- `git -C main` `log`, `status --porcelain` (code paths; clean before and after), `rev-parse HEAD:<tree>` (7 trees),
  `ls-files` of `lead-reports-20261101/tools/` and `timestamp/` (names); `git status --porcelain` in the five worktrees
  (the tracks' file names).
- `v2/hashes.py` (`/usr/bin/python3 -I -B`): 64 files; `shasum -a 256` of the two files under verification, the
  consoles and the ledgers.
- `zsh -n` on the script and the six copies; `v2/extract_blocks.py` on the runbook (10 blocks `zsh -n`, 5 heredocs
  parsed); `ast.parse` of the script's 5 heredocs.
- pytest on fresh basetemps under `builds/tmp/`, each deleted after: `reading_extra` 120, `hlc_draw` 123, `reading_input`
  284, B16 261 passed.
- The dry run: `build_root.zsh`, `build_world.py`, `make_copies.py`, `run_all.zsh` (six manifests, six runs: exits
  0, 0, 0, 1, 1, 1 as planned), `analyze.py`, the extractor four times (0, 0, 0, and the exclusive-create refusal), the
  usage and re-run refusals (2, 1), the seal check and ledger pre-check on the synthetic kit (0, 1), `caps_check.py`
  (one earlier attempt failed on import order: a symlinked module's own `sys.path` insert resolved `scripts.stage1_s1`
  from the main checkout; fixed by importing the dry-run root's packages first; no data read), the negative helper
  tests (`v2/neg/`), the `noclobber` test. `rm -r` of the synthetic root, the caps world, the scratch folders and the
  pytest basetemps by explicit paths.
- **Disclosures (names only, no content; no sealed file, unit, bank or outcome was opened, hashed or listed):**
  (1) symlinks from the dry-run root to the main checkout's `experiments/safety_selection`, `experiments/minimal_safety`,
  `scripts/stage1`, two frozen reader scripts, the top-level entries of `scripts/stage1_s1` (less `reading_input` and
  `tests`) and `runkit/stage1-olmo/{seal,plan_tool,judge_units_stage1}.py` and `tests`: nothing was read or listed by
  me through them; Python imported only what the tools import; the manifest writer hashed only its listed code files,
  as it would on the real tree. (2) `ls` of `experiments/` (four folder names), `scripts/stage1_s1/`,
  `runkit/stage1-olmo/`, ws-a's `reading_input/tests/`, ws-d1's `reading_extra/` and ws-d2's `hlc_draw/` (code and
  test names; no name with plant, decoy, hidden or selector among them). (3) `rsync` of the three packages (code and
  tests) from the worktrees into the dry-run root. (4) `git ls-files` of two committed records folders (names).
  (5) FOCUS lines 70-80 at `55d5f8b`, cut to 900 characters per line, to read the never-open sentence (a record file,
  not sealed). (6) `git show HEAD:` of the first stamp's check record and stamp record (committed records, no
  outcome). (7) `grep -n` over `plan_tool.py`, `seal.py` and `job_runner_stage1.py` in the repository (kit code) for
  the plan record's field names.
