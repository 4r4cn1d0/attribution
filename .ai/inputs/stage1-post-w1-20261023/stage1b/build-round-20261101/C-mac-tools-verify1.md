# Track C-mac-tools: independent verification (verify1)

Verifier for the main-study lead; written 2026-11-01T23:05 UTC (`date -u` checked). Read-only on the builder's workspace
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/s1b/ws-c`
(detached at `0d25497`; `git status --porcelain` shows only `?? scripts/stage1_s1/stage1b_mac/`; unchanged by me). My own
files: `.../scratchpad/s1b/verify-C-mac-tools/` (`attack.py`, `attack-results.json`, `my_mutants.json`,
`mutation-verify-shard1.json`, `mutation-verify-own.json`) and this report.

Tags: (R) read in a source; (M) measured by a read-only command or a synthetic run; (I) inference; (E) estimate.
Line numbers are the worktree's at `0d25497` unless marked `@55d5f8b`.

## Verdict: DEFECTS (one that matters for blinding, in the runbook text; one minor test gap). The code is sound.

- The three tools do what section 40 points 4, 5 and 13(a) ask, by exact path and SHA-256, by key, printing hashes, exit
  codes and fixed messages only. My 52 adversarial synthetic cases (success, every refusal, malformed JSON, missing keys,
  unhashable values, raising or syntactically broken rules module, leaking or failing W1 stand-ins, invalid UTF-8,
  argparse errors, a late record-write failure) leaked no sentinel to stdout, stderr or the hash record, with one
  expected exception that is a design note (N2), not a defect.
- **D1 (blinding; the lead's runbook in the build report, not the code).** Build report §9 step 3 tells the lead that on
  exit 1 "the lead may read a log only if it is sure the W1 script's refusal names no leaf (RPR's messages can name a row
  id, never a cell ...)". That claim is false and the permission is unsafe (details below). The package README says the
  right thing ("never `ls` or `cat`"). Strike the sentence.
- **D2 (minor; a stated acceptance criterion not met).** The decoy-pool refusal has no test and no mutant; my mutant that
  drops its pin check survived the suite. The code itself checks it (construction_checks.py:157).

## 1. Hard-rule log

- Not opened, listed, grepped or hashed: `tmp/stage1-olmo/{hosts,judges,judges-pending,seals,retrieved}/`,
  `tmp/stage1-olmo/plan.json`, `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, `tmp/hlc*`,
  `tmp/stage1-mac-runs-20261023/`, `.ai/inputs/stage1-post-w1-20261023/{block-a,block-b}/`, `reading/run-20261101/`, any
  `units/` or `eval/` folder, any COMPLETE.json, edit, answer, label, guard-sample or judge-cache file, the banks, and
  every non-code file whose path holds "plant" or "decoy" (the two settings files included). READY lines 51-55 (which
  print lines of such files) were not read; of READY I read lines 222-230 only.
- Code read (carve-out): `scripts/stage1/{report_plant_ranks,score_datashield,score_l1_larf,s1common,build_plant,
  representation_pass,score_classifier,lexicon_pin,write_add_edit,build_s_pool,token_accounting,build_length_rules}.py`
  (the last six by AST import listing only), `scripts/stage1/tests/test_report_plant_ranks.py:186-198`,
  `scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py`, `scripts/stage1_s1/extract_a0_fingerprint.py`,
  `scripts/stage1_s1/reading_input/__main__.py` (grep), the kit's `seal.py`, `stage1_rules.py` (parts and AST),
  `plan_tool.py` (parts), `setup/job_runner_stage1.py` (parts), `experiments/safety_selection/{common,prepare,edits,
  textproc,config,sources}.py` (imports), the lead's `tools/ots_manifest.py` and `ots_check.py` (docstrings), and the
  whole new package.
- Records read: addendum §40 (lines 1377-1554) and ADD:618-640 `@55d5f8b` (`git show`); CHECK in full; FOCUS by grep and
  named entries; MAN1 by key only (Python: top-level keys, entry count, roles, the entries for the three scripts, their
  settings, s1common, build_plant, representation_pass, build_length_rules, labels.json); `scripts/stage1/README.md:68-80`;
  the kit README by grep; `.gitignore:1`. Folder names listed: `tmp/` (top), `tmp/kt-prepared/`,
  `.ai/inputs/stage1-post-w1-20261023/` (top), the lead's `tools/`.
- No builder, scorer, reading, kit, seal, pack, draw or launch command ran on real data. Every run used the builder's
  synthetic world plus my own sentinels, in temporary folders under the scratchpad, deleted after each run. The real
  settings file was not given to the switch check (its path holds "plant"); its default pin was checked against MAN1 by key.
- Git: `status`, `rev-parse`, `log`, `diff --stat`, `show` only. The main checkout is unchanged by me. No background job.

## 2. What the main checkout is at (M)

`/Users/spiderishi/Coding/attribution` is at `2ec7ce0` (branch `stageb-costs-and-recovery-safeguards-20261003`): one
commit on top of `0d25497`, changing `research/FOCUS.md` only (+1 line). The three W1 scripts, `s1common.py`,
`build_plant.py`, `representation_pass.py`, `build_length_rules.py`, `labels.json` and `runkit/stage1-olmo/stage1_rules.py`
are byte-identical between the worktree and main; the kit copy `tmp/stage1-olmo/stage1_rules.py` equals main's (`cmp`).
FOCUS is edited live in the main checkout (its line 143 changed between two of my reads), so FOCUS line numbers in any
report drift; I cite FOCUS entries by title.

## 3. What each tool opens or lists (traced in the code; confirmed by the synthetic runs)

**construction_checks** (in order): `--out` (`exists`, `is_dir`, `any(iterdir())`: a probe for the first entry, never
named, :171-176); `--record` (`exists`, :241); `--prepared` (`is_dir`, :243); `--rules` (read, executed by
`importlib`, :80-89); `--repo/<rules.MAN1_PATH>` (pinned at `rules.MAN1_SHA256`, parsed, :94); the three W1 scripts
(pinned at MAN1's entries, :101); `--repo/<rules.D2_REQ8_RECORD.path>`, `--plant-pool`, `--decoy-pool` (pinned at the
rules' pins, hashed only, never parsed, :154-157); `--kit/plan.json` (read, parsed by key, not pinned, :110); the seal at
`--kit/<plan.seals[BLOCK].path>` (pinned at `--expect-seal-sha256`, parsed by key, :116); the four pod files at
`--kit/retrieved/HOST/tree/job-I/{representation,l1-scan,classifier}/<file>` (pinned at the job's recorded `outputs`, then
matched to exactly one sealed seal entry of HOST at that path and hash, :128-143); `--l1`/`--datashield` if given
(PATH:SHA256, re-hashed, :162-168). Then it creates `--out/log/`, runs each step as a subprocess with stdout and stderr
captured to `--out/log/<step>.log` (:210-216), reads `--out/<step>/<file>` bytes to hash them (:228-234), creates
`--record`'s parent and writes the record by exclusive create (:283-284). `module_hashes()` globs the package's own folder
(common.py:75). No other path is touched; nothing else is listed. The W1 scripts, as subprocesses, read their own
settings by pin, `labels.json`, the prepared set (manifest, `engine/train_rows.jsonl`, `engine/groups.json`; the report
also P's text through `load_prepared`) and the given inputs, and write into `--out/<step>/` (R: RPR:288-394,
score_datashield:76-91, score_l1_larf:267-285, s1common.PreparedView:329-369).

**binding_check**: `--record` only (pinned at `--expect-record-sha256`, parsed, two keys of one `edits` entry read).
**switch_check**: `--settings` only (pinned at `--expect-sha256`, parsed, `kind`, `name` and `counting.selfinf_n_counts`
read). Importing `scripts.stage1.report_plant_ranks` for its constants opens no file (R: its module level inserts a
sys.path entry and imports `experiments.safety_selection.common` and `s1common`, both file-free at import).

Forbidden paths touched by the tools: `plan.json` (by key, not pinned; it only supplies the job index and the host's
status, and every file it points at must also be listed once in the lead-pinned seal at the same hash, so a wrong plan
cannot make a wrong file pass: :140-142), the seal (pinned by the lead), the four pod files (pinned twice), REQ-8's record
and the pools (pinned, hashed only), the report's settings (pinned, one key). That is what section 40 point 3 allows for
reviewed code. No folder under `retrieved/` or `seals/` is listed.

## 4. The kit's record shapes, checked against the code that writes them (R)

| What the runner assumes | Where the kit writes it |
|---|---|
| seal entries `{host, path, sha256, class}`, `path` relative to `retrieved/HOST/tree` | `seal.py:104, :113-116` |
| seal `kind` "stage1 block seal", `block`, `files` list | `seal.py:59, :137` |
| `plan.seals[BLOCK] = {path: "seals/block-BLOCK.json", sha256, ...}` | `seal.py:150` |
| `plan.hosts[HOST].done is True`, `.block` | `plan_tool.py:3625`, `:101` (seal's host filter) |
| `jobs[i].kind/status/outputs`, `pulled` absent unless `False` | `plan_tool.py:3604` (`outputs=outputs or None`), `:3622` (`pulled=False` only for unpulled unit jobs); the kit's own idiom `j.get("pulled") is not False` at `:1734` |
| `outputs` keys `job-I/<folder>/<file>` relative to the tree root, the pulled file re-hashed by record-done | `job_runner_stage1.py:923-934` (`output_files`, `str(p.relative_to(root))`), `:1103-1112`; `plan_tool.py:3583-3593` |
| job index I = the job's position in `hosts[HOST].jobs` | `job_runner_stage1.py:398, :401` (`out = f"job-{index}"`), `plan_tool.py:3575` (`enumerate`) |
| folders `representation` (main pass; `representation-s3-orig` beside it), `l1-scan`, `classifier` | `job_runner_stage1.py:434-438, :444-446, :447-453` |
| file names | `representation_pass.py:66-67`, `score_l1_larf.py:48`, `score_classifier.py:40` (a test holds them equal) |
| kinds `rep_pass`, `l1_scan`, `classifier` | `stage1_rules.py:542, :552` |
| `D2_REQ8_RECORD`, `D2_POOLS`, `MAN1_PATH`, `MAN1_SHA256` | `stage1_rules.py:383-386, :416-417` |
| MAN1 `entries` is a list of `{path, role, sha256, ...}`, 140 entries, no duplicate path | (M, by key) |

## 5. The builder's input-location findings, re-checked

| Input | My check |
|---|---|
| `--plant-record` at `.ai/inputs/stage1-commitments-20261016/plant/plant_record.json`, `cc04b663…` | (R) `stage1_rules.py:383-384`; FOCUS "STAGE-1 MAC RUNS DONE" (23 Oct 14:57 UTC) names the same path and hash; `build_plant.py:65, :460` writes `plant_record.json` into `--out`. Not a MAN1 entry (M: MAN1's 8 plant/decoy-named entries are settings, code and tests of W1). Correct. |
| `--plant-pool`, `--decoy-pool` under the 23 Oct build's `--full-out` in `tmp/stage1-mac-runs-20261023/` | (R) `build_plant.py:430-435` writes `plant.pool.json` and `decoy.pool.json` into `full`, :34-35 and the FOCUS entry put the text files there; pins `stage1_rules.py:385-386` (equal to the FOCUS entry "B15 BUILT; D-2 BUILT": plant `37739f40…`, decoy `d102b665…`). The folder name is not in a readable record; the lead supplies it; a wrong file refuses by hash. Correct. |
| `--rows`, `--summary`, the L1 scan, `--classifier` from a-8 | (R) FOCUS "BLOCK A: ALL 20 ARM RUNS COMPLETE": "diagnostics (a-1 J6, a-8 J5/J7/J8)"; the folders and records as in §4. The job indices are in plan.json (not opened); the runner finds them by key. Correct. |
| `--l1` (REQ-10's Mac score) | (R) FOCUS "USER TOP-UP FOR BLOCK A" (25 Oct 17:04 UTC): "L1 (REQ-10 score and remove-600 edit) ... all sealed by SHA-256 in the kit": the score output existed on the Mac by then; its SHA-256 is in the kit's sealed edit record (plan.json `records.sealed[*]` → a record under `block-a/`, not opened; `plan_tool.py:848-860`, `:3184`). The builder's finding and its open point 2 (locate it by key, or remake it) are right. The scorer is a pure function of the scan, the rows, the summary and the pinned settings (`score_l1_larf.py:239-285`; no time stamp in the output), so a remake should hash equal to the 25 Oct file if the Python and numpy versions are the same (`s1common.provenance` records them) - a free consistency check for the lead. |
| `--datashield` | (R) READY:226-228: "Not recorded in FOCUS: the Mac runs of DataShield-style (REQ-12)"; (M) no FOCUS entry names one. The runner makes it. Correct. |
| `--prepared` `tmp/kt-prepared/prepared-kt-dolly-olmo2` | (M) the folder exists; (R) `stage1_rules.py:805-806`; the report pins its manifest itself (RPR:298-299). Correct. |
| the W1 scripts and settings | (M) MAN1 by key: report `f5bbea25…`, datashield `6eb4f7ea…`, l1 `4996fd3b…` (role code), each equal to the file on disk in the worktree and in main; settings `c952eb72…`, `065e9656…`, `0d875213…` (role settings), each equal to the module's literal. MAN1 itself `f6283090…` = `stage1_rules.py:417`. Correct. |

**The report's own rules a-8's output must meet (R, RPR:260-269):** the summary must list pools `plant` and `decoy` with
`pinned_by == "pool pins"` at REQ-8's hashes. `representation_pass.pin_of` (:238-252) returns "pool pins" only for a
listed pool whose filled pin matches, which the D-2 route gives (`d2_representation_pass.py` runs the W1 pass with the
filled pins file; FOCUS "B15 BUILT; D-2 BUILT AND THE POOL PINS FILLED", 23 Oct 16:15 UTC, before block A). Under the D-2
fallback (`job_runner_stage1.py:312-313`) the pass would carry no plant pool and the report would refuse at the report
step. The runner cannot pre-check this without parsing a sealed file's values; the refusal goes to the log (N9).

## 6. The scorers' and the report's needs (R, by the import chain; M for the venv)

- `score_datashield.py`: standard library + the engine's `common` (+ `s1common` → engine `edits` → `textproc` →
  `minimal_safety.data`): no numpy, no torch. Reads the settings by pin, the prepared view, the summary, the rows file once.
- `score_l1_larf.py score`: the same, plus `lexicon_pin` (file-free at import) and `representation_pass` for
  `block_output_index` and `READS` (its module level imports no torch). The `scan` subcommand (GPU) is not used.
- `report_plant_ranks.py`: numpy (`auc_interval`), `load_prepared` (engine `prepare` → `config`, `sources`, `textproc`:
  no torch), `build_plant.place` (its imports: `build_s_pool`, `lexicon_pin`, `token_accounting`, `write_add_edit`: no
  torch), `build_length_rules`. The venv has numpy 2.2.6 (torch and transformers are present but not imported on this
  path). So: CPU, no model, no download. The builder's 1-5 min estimate is plausible (E): the placement on 4,800
  prompts (the 23 Oct build ran it on the Mac) and 6 scorers × 4 comparisons × 2,000 bootstrap replicates
  (`test_report_plant_ranks.py:188` asserts 2,000) over ~4,800 negatives, tens of seconds in numpy.

## 7. Section 40 compliance

- Point 4: the report runs WITHOUT `--counted` (`report_command`, :199-204; a test parses the argv with the real
  `report_plant_ranks.main` and a mutant that adds `--counted` is killed), into a folder whose name must hold "plant"
  (:173), after the two scorer outputs are made if not given (:263-272); the output is never parsed here, only hashed
  (:228-234); the text-free hash record (keys: block, commands, host, inputs, kind, modules, out_folder, outputs,
  pod_paths, python, report_without_counted, steps, utc, version, w1_scripts; M) goes outside the folder for the lead to
  commit and stamp. "Published before the pilot" = that committed, stamped SHA-256: as ruled.
- Point 5, second bullet: the binding check reads the record at the lead's pin and two keys of one `edits` entry, prints
  `match`/`no match` (exit 0/1) or a fixed refusal (exit 2). `build_plant.py:290-294` writes `{file: "edits/<name>.json",
  sha256, arm, ...}` and `:306-308` names `planted_k37`; `:438` the kind. As ruled.
- Point 13(a): the switch check follows the §35 point 1 pattern (`extract_a0_fingerprint.py`: pin, parse in memory, one
  key, nothing else printed); key path `counting.selfinf_n_counts` = RPR:228; default pin = RPR:62 = MAN1's entry (M). The
  W1 test `test_the_committed_settings` (:190) asserts the same key is `True`, so the lead's expected output is
  `selfinf_n_counts true`. As ruled.
- Point 3 (names): no path or file name of the package holds "plant" or "decoy" (M: `find | grep -i`); string constants
  and argparse flags inside the code do, as they must.
- Point 12 (order): the runner uses the repository's rules module by default, as the reading does
  (`reading_input/__main__.py:30, :42`); the checks run before round 35 merges, so the module is the stamped one; the
  record holds its SHA-256.

## 8. Argv against the real parsers and input rules (R)

Report (`RPR:406-416`): `--prepared` (Path), `--plant-record`, `--plant-pool`, `--decoy-pool`, `--rows`, `--summary`
(required PATH:SHA256), `--l1`, `--datashield`, `--classifier` (optional PATH:SHA256), `--counted` (append), `--out`,
`--settings` (default). The runner passes all nine plus `--out`, nothing else (M: A1's record). DataShield
(`:94-101`): `--prepared --rows --summary --out`; L1 (`:288-301`): `score --prepared --scan --rows --summary --out`. The
runner's lines parse with the real `main`s (the builder's `test_argv_compat.py`, which patches `s1common.load_settings`
to stop after argparse so no settings file is opened: R). Input rules the runner's outputs satisfy: the scorer outputs
score exactly P's training rows (`check_scores(scores, view.tokens)`, datashield:82, l1:275) as RPR:332/:340 require;
their `provenance.inputs.rows` is the rows file's SHA-256 (datashield:88, l1:281) as RPR:277 requires; `provenance.index`
and `.read` (l1:283) and `.l_hat` (datashield:90) are what RPR:334 and :342 read; the printed line `  <sha256>  <name>`
(each `main`, e.g. RPR:436) is what `printed_hash` parses (:219-225).

## 9. My adversarial runs (M; `attack.py`, 52 cases; results in `attack-results.json`)

Every case asserts that none of the builder's ten sentinels nor my fourteen (placed in the rules module, MAN1 entries,
plan.json job fields, `records.sealed`, block notes, seal entries of other hosts, a `not_pulled` unit, a W1 stand-in's
extra output file and extra stdout lines, argparse values) reaches stdout, stderr or the hash record.

- Runner, success (A1, A28 as `python -B -m ...` subprocess): exit 0; stdout lines begin only with `w1`, `input`, `step`,
  `output`, `record`; the record is text-free; the "plant" folder holds `datashield/`, `l1/`, `log/`, `report/`.
- Fixed refusals, nothing written (A2, A3, A5, A8, A9, A17, A18, A21-A26, A30, A31): malformed plan.json, a JSON list, a
  jobs dict, non-JSON seal bytes at the right hash, a missing seal file, a non-hex or sentinel `--expect-seal-sha256`,
  `--out` an existing file, a MAN1 entry without `sha256`, MAN1 `entries` a dict, `--l1` missing, `--plant-pool` a folder,
  `--host` a sentinel, a non-string seal path, the main rows file recorded with the s3-orig pass's hash, the classifier
  file sealed under another host only.
- Type-only messages (A4, A6, A7, A10, A11, A27): `plan.seals` a string, `outputs` a list, an unhashable seal path, a
  rules module that raises, a rules module with a SyntaxError, a W1 stand-in printing invalid UTF-8 - each
  "REFUSED: an unexpected <Type> (its message is withheld ...)".
- Capture (A13, A14, A15): stand-ins leaking sentinels on stdout and stderr: logs only; a failing report stand-in: exit 1,
  "FAILED: step report exited 2 ...", no record; a stand-in that writes an extra sentinel-named file into `report/` and
  prints decoy hash lines: exit 0, the extra file never named, the right hash taken.
- **A12 (the one leak, by design):** a rules module with a module-level `print("ZQX...")` reaches stdout. The runner
  executes `--rules` without a pin (it records the hash only). The real `stage1_rules.py` at `0d25497` (`4005cb4e…`) has
  only assignments, function defs, imports and a docstring at module level (M, AST), and the reading loads it the same
  way. See N2.
- A19: `--record` inside `--out` is accepted (the record is written inside the "plant" folder). A20: `--record`'s parent
  a file: exit 2 ("unexpected FileExistsError") AFTER the three steps ran, the "plant" folder filled, no record. A27:
  exit 2 after the datashield step wrote its output and before its log was written. See N1, N3.
- Binding check (12 cases): match (0), no match (1); fixed refusals for two entries for the file, a wrong record pin, a
  missing `kind`, a missing `edits`, entries without `sha256`, a sentinel as `sha256`, an upper-case `--edit-sha256`,
  malformed JSON, a sentinel `--edit-file`. A JSON text with the key `edits` twice (first right, second wrong) gives
  "no match" (`json.loads` keeps the last), not a refusal; moot under the pin (N4).
- Switch check (10 cases): true, false; fixed refusals for a wrong pin, a missing key, `counting` a list, the value 1,
  the value "true", a sentinel name, malformed JSON, a JSON list.

## 10. Suite and mutants (M; baseline first, same command, scratch outside the workspace, deleted after)

- `pytest -q -p no:cacheprovider --basetemp=<fresh>` on `scripts/stage1_s1/stage1b_mac/tests`: 53 passed in 0.7 s.
- The builder's runner on 10 of its 52 mutants (`--only CC-log-stdout-shown,CC-log-stderr-shown,CO-frame-type-only,
  CC-report-counted,CC-seal-entry-single,CC-pod-hash,CC-main-pass,BC-single-entry,BC-record-pin,SC-pin`): baseline pass
  (53 tests), 10/10 killed (1-6 failures each), "every mutant as expected", exit 0. Report
  `verify-C-mac-tools/mutation-verify-shard1.json`.
- Three mutants of my own (`my_mutants.json`): baseline pass (53); **all three SURVIVED**: `V-decoy-pool-pin` (the decoy
  pool read without its pin: D2), `V-seal-host-filter` (seal entries of every host pooled), `V-input-print-path` (the
  path printed beside each input hash). Report `mutation-verify-own.json`. The runner itself is the reading_extra runner
  with its tree renamed (M: `diff`), applying the rules the lead uses (baseline, no -x, JUnit counts, errors invalid).

## 11. Defects

**D1 (blinding; documentation: the lead's runbook in the build report §9 step 3; the code is unaffected).**
The sentence "the lead may read a log only if it is sure the W1 script's refusal names no leaf (RPR's messages can name a
row id, never a cell; `build_plant.py`'s placement refusal in RPR:361 names none)" is wrong and unsafe.
- Reproduction (R): `report_plant_ranks.py:115` `Refusal(f"cell {cell} has no scored row")` fires in `rank()`, which
  `placement_block` (:170) calls first on the planted leaf's own chain (unit, quartile, leaf: `chain(leaf)`), so the
  message can name the drawn leaf; `:82` names a cell of the placement; `:150` names `r`, the planted leaf's rank among
  the leaves with ties above it (`scorer_report`, :190), a construction-check result that must stay unopened. The log is
  the script's stderr verbatim (`construction_checks.run_step`, :214-215).
- Expected: no one reads a file under `--out` until the counted outputs are hashed or a final "stop" (section 40 point
  4; the package README already says "clear `--out` (`rm -rf`, never `ls` or `cat`) and run again"). Actual: the build
  report permits a conditional read that the lead cannot judge without reading.
- Fix: strike the sentence; on exit 1, `rm -rf --out`, re-check the inputs by hash through the records (the runner's
  stdout already names which step failed), run the W1 suites, and re-run. If a reason is needed, a reviewed key-only
  classifier can read the log and print only whether the last stderr line is one of an explicit whitelist of value-free
  RPR messages (never the line itself).

**D2 (minor; the task's "one mutant per refusal" and the builder's claim of it).** The refusal "the decoy pool does not
hash to its expected SHA-256" (`construction_checks.py:157`) has no test case and no spec entry (CC-pool-pin covers the
plant pool; the test covers a missing decoy pool, not one off its pin).
- Reproduction (M): mutant `V-decoy-pool-pin` (replace `read_pinned(decoy_pool, pools["decoy"], "the decoy pool")` by
  `read_bytes(decoy_pool, "the decoy pool")`): the suite passes (53), the mutant survives. Expected: killed.
- Consequence if the code ever regressed: a wrong decoy file would reach the report, which re-hashes it against the same
  pin and refuses (RPR:255-256, :308), but only after the two scorers ran. Fix: one test (`decoy_pool=world.pools["plant"][0]`
  expecting the fixed message) and one spec entry `CC-decoy-pin`.

## 12. Notes (minor; not defects)

- N1. "Exit 2 ⇒ nothing written" (docstring :36-37, README, build report) is not strict: a late failure after the steps
  (A20: the record's parent is a file → FileExistsError; A27: a W1 script printing invalid UTF-8 → UnicodeDecodeError
  before the log is written; a read-back mismatch) exits 2 with the "plant" folder filled. Harmless: a re-run refuses a
  non-empty `--out`, so the lead clears it anyway. Wording fix, or create `--record`'s parent before the steps and
  write the log in binary.
- N2. The rules module is executed unpinned (A12). The record holds its SHA-256; the lead can compare it with the
  stamped tree's. An optional `--expect-rules-sha256` would close it.
- N3. `--record` is not checked to lie outside `--out` or to be free of "plant" (A19): a record under a "plant" path
  could not be opened or committed under the path rule. One-line check.
- N4. `common.json_object` uses `json.loads` (duplicate keys: last wins); `s1common.strict_json` refuses them. Moot
  under the pins (the real record and settings are canonical JSON), but the stricter parser costs nothing.
- N5. Test strictness: `V-input-print-path` survived because the tests check each stdout line's first word and the
  absence of sentinels, not the exact shape `<head> <name> <sha256>`; `V-seal-host-filter` survived because no test
  lists the same relative path under another host with the same hash (A31 shows the real code refuses when the only
  entry is under another host). Suggest a per-line regex and one more seal case.
- N6. Runbook step 3's seal hash: the kit's own `seal.py status` prints "seal A: N files (M sealed), sha256 <full>"
  (`seal.py:221-222`); either that or the plan.json one-liner, both by key. FOCUS gives only `6c6267c8…`.
- N7. The runner pins the three W1 scripts only; the report's helpers (`s1common`, `build_plant`, `representation_pass`,
  `build_length_rules`, `labels.json`) are checked by nothing here, though all equal MAN1 today (M). The report's own
  provenance records `s1common_sha256` and the engine identity. Option: check every MAN1 "code" and "settings" entry
  under `scripts/stage1/` before the steps.
- N8. The report's settings carry `engine_x`; `s1common.check_settings` (:590-592) refuses a changed engine identity at
  the report step. The engine is frozen (rule 4), so this is only where a drift would show.
- N9. See §5: the D-2 route assumption is the report's to check, not the runner's; a fallback-route J5 output would be
  refused at the report step, after the scorers ran.
- N10. The hash record's `commands` hold the lead's paths (the `--full-out` folder, the prepared folder, the pod paths
  `a-8:job-I/...`): names chosen before the draw, no value.
- N11. `check_out_folder` probes `any(out.iterdir())` on the (expected absent or empty) "plant" folder; the first entry
  is never named; `s1common.write_new_files` makes the same probe.
- N12. The scorer outputs live inside the "plant" folder although they hold no plant information (scores of P's
  4,800 rows); the builder chose this as conservative. A later counted run can take them back as `PATH:SHA256`
  from the hash record. Fine.
- N13. The builder's PT line numbers (e.g. `edit_sources` "PT:862-868") are off by about 14 from the worktree's
  (`:848-860`); the content is as described.

## 13. Replies to the task's checks

- Trace every file opened or listed; none forbidden except by exact path and SHA-256; nothing lists a folder: §3. Yes,
  with plan.json read by key and cross-checked through the pinned seal, and the two probes of N11 and `module_hashes`.
- Blinding attacks on success, every refusal, malformed JSON, missing keys: §9; one expected leak (A12) that documents
  the unpinned rules module (N2).
- The runner's arguments against the real argparse and input rules: §8. Match.
- The input-location findings against the code and records: §5. The builder's findings hold; the L1 score's existence
  is confirmed by FOCUS's 25 Oct entry; DataShield-style has no recorded run.
- The binding check and the switch extractor on synthetic records, with two entries for the same file, a wrong pin and
  a missing key: §9, all refused with fixed messages.
- Suite and up to 10 mutants, baseline first: §10 (53 passed; 10/10 killed; my 3 extra mutants survived: D2, N5).

## 14. Commands run (all read-only on the repository; exit codes)

`git -C <ws-c> status --porcelain | rev-parse HEAD | diff --stat` (0); `git -C <main> rev-parse HEAD | branch --show-current |
log --oneline 0d25497..2ec7ce0f | diff --stat 0d25497 2ec7ce0f | show 55d5f8b:<addendum>` (0); `find`, `grep`, `sed`,
`wc`, `ls`, `cmp`, `shasum -a 256`, `date -u` (0; one `grep` on FOCUS exited 1 after printing: no match for one
alternative); Python AST listings of imports and top-level statements (0); Python reads of MAN1 by key (0); the suite
(53 passed, exit 0; basetemp deleted); the mutation runner, shard of 10 (exit 0) and my 3 (exit 1: three survivors;
scratch deleted); `attack.py` (exit 0; temporary folder deleted). No `__pycache__` left in the worktree (M: `find`).
