# Track C-mac-tools: the Mac-side stage-1b tools (build report)

Status: DONE (2026-11-01T22:22 to 22:45 UTC; `date -u` checked). Worktree:
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/s1b/ws-c`
(detached at `0d25497`; `git status --short` shows only `?? scripts/stage1_s1/stage1b_mac/`). Nothing committed.

Tags: (R) read in a source; (M) measured here by a read-only command or a test; (I) my inference; (E) my estimate.
Line numbers are those of the worktree at `0d25497` unless marked `@55d5f8b`.

## 1. Hard-rule log

- Not opened, listed, grepped or hashed: `tmp/stage1-olmo/{hosts,judges,judges-pending,seals,retrieved}/`,
  `tmp/stage1-olmo/plan.json`, `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, `tmp/hlc*`,
  `tmp/stage1-mac-runs-20261023/`, `.ai/inputs/stage1-post-w1-20261023/{block-a,block-b}/`, `reading/run-20261101/`,
  `reading-20261101.console.txt`, any `units/` or `eval/` folder, any COMPLETE.json, edit, answer, label,
  guard-sample or judge-cache file, the banks, and every file whose path holds "plant" or "decoy" (the two settings
  files included). Code read under the carve-out: `scripts/stage1/build_plant.py`, `report_plant_ranks.py`,
  `score_datashield.py`, `score_l1_larf.py`, `score_classifier.py`, `representation_pass.py`, `s1common.py`,
  `tests/test_report_plant_ranks.py` (lines 1-230), the kit's `seal.py`, `plan_tool.py` (parts),
  `setup/job_runner_stage1.py` (parts), `stage1_rules.py` (parts), the D-2 wrappers, `extract_a0_fingerprint.py`,
  the reading_extra and reading_input packages (parts).
- Records read as text: addendum section 40 and the ADD:618-640 range at `55d5f8b` (the ADD:625 pattern), CHECK,
  READY, REV4:665-713, the W1 record items 17-25, FOCUS (grep and lines 118, 124, 127, 129, 131, 142), the kit README
  (parts), `scripts/stage1/README.md` (parts), the reading runbook and zsh transcript (a search for "prepared" only;
  no hit), the lead's `tools/ots_manifest.py` and `ots_check.py` docstrings. `MANIFEST.json` (W1) by key only.
- Folder names listed: `tmp/` (top level), `tmp/kt-prepared/`, `.ai/inputs/stage1-post-w1-20261023/` and its
  `reading/` (top level), the lead's notes folders by file name (`grep -l build_plant.py`; no file opened).
- No builder, scorer, reading, kit, seal, pack, draw or launch command ran on real data. Every test and every
  mutation run used synthetic data in a temporary folder with sentinel strings. No network, no install, no pod.
- No git command that changes state ran (`git status`, `git log`, `git show` only). The main checkout is unchanged.

## 2. What I changed (new files only; before: absent)

| File (under `scripts/stage1_s1/stage1b_mac/`) | SHA-256 after | Lines |
|---|---|---|
| `__init__.py` | `98d67ab124c59d8c3f09bc5f6b5f25a549bc27cfc210f16b6f5e5ee84fed226d` | 31 |
| `common.py` | `1ba389746fb44e4bdca320cb4bf1bda7d791c8e92cfb08909625f7883c5bcb3a` | 103 |
| `construction_checks.py` | `1e7f73a761adfa8dd40b2c07497f2ecf98e40ecf1266df8d2bd40f316c620009` | 339 |
| `binding_check.py` | `c33fee27d6e3d1e33c5af9c7d73f22d60c2e3c5b2f9f0eb42aeab41ca27f054c` | 69 |
| `switch_check.py` | `e00a8ce6b0e6d5c33352c990341e1fb5a45c10231ddbd9d66e6d490565fbed4c` | 61 |
| `README.md` | `eae1c95a40eef4818a101dc4071dc2fced4612324bf4ba7ddc68ef6758ac4fc4` | 53 |
| `mutation/run_mutants.py` | `5bf8c7e434332767623751a3c10f933568b89c569b72995e2b297d087cbb7cc2` | 216 |
| `mutation/mutants_stage1b_mac.json` | `5c104fc42e0fa6d1bbfe554b5a306c85d182030157811c429a838bd7d8d4ea56` | 421 (52 mutants) |
| `tests/conftest.py` | `ed7b76026087b5e111a9d3ef463d9d8b8a76201ae9a176440bfa6952ed6e03f5` | 12 |
| `tests/synth_world.py` | `aa71cc0b2e23c4b419493fdbd677405eb3cd81f4cb15afa04b8ce4c2987fa2d2` | 302 |
| `tests/test_construction_checks.py` | `83916cf5a00d1f81f4ef794deb192445585a03c56bedc65f95a1764bde773c58` | 326 |
| `tests/test_binding_check.py` | `30eb54749512a95b4d70a1f975363c7863f469111af579dd00c849f803a59f1f` | 108 |
| `tests/test_switch_check.py` | `4bb20f5145d44135c696fe2fa81134136153dfbe99f1103faaefbac4f2394ede` | 87 |
| `tests/test_argv_compat.py` | `92a3aba0395f357416c247e86122659525185acb8beb64af25e1beb5dc084c7d` | 100 |
| `tests/test_common.py` | `68c1972a9df12e6d1afccc71f06fd617e1b899d8e254a3b3f53708bfb28296bc` | 74 |

No file outside the package changed. No path or file name holds "plant" or "decoy" (M: `find | grep -i`). B16, the
input builder, the W1 code, the manifest's files, the engine and the kit are untouched. (Fix round 1 changed nine of
these files; their current SHA-256 values are in the "Changed files" table at the end of this report.)

## 3. What I found about each input (path rule, record, existence)

The runner resolves every input by exact path and SHA-256 and refuses on any mismatch or missing file.

| Input (report flag) | Where it lives | Where its expected SHA-256 is recorded | Exists? |
|---|---|---|---|
| `--plant-record` | `.ai/inputs/stage1-commitments-20261016/plant/plant_record.json` (committed; FOCUS:142 "`plant/plant_record.json` `cc04b663…`") | `runkit/stage1-olmo/stage1_rules.py:383-384` `D2_REQ8_RECORD` (path and `cc04b663…`); not a W1 manifest entry (M: MAN1's 7 "sealed record" entries name no plant file; the plant was built after W1) | yes (R; hashed by the runner, never parsed) |
| `--plant-pool`, `--decoy-pool` | `plant.pool.json` and `decoy.pool.json` under the 23 Oct build's `--full-out` folder, inside git-ignored `tmp/stage1-mac-runs-20261023/` (`build_plant.py:34-35`, :430-435 name them; FOCUS:142 "the files with text stay under git-ignored `tmp/stage1-mac-runs-20261023/`") | `stage1_rules.py:385-386` `D2_POOLS` (plant `37739f40…`, decoy `d102b665…`); the same values in REQ-8's record `pools.*.sha256` and in the filled pins file (RULES:381-382) | the folder is on the never-list list; the exact `--full-out` sub-folder name is not in FOCUS or the addendum (the lead ran the build and knows it). The runner takes the two paths from the lead and refuses any file off the pin, so a wrong path cannot pass. |
| `--rows`, `--summary` (REQ-3, J5) | the kit's pulled tree `tmp/stage1-olmo/retrieved/a-8/tree/job-I/representation/representation_rows.jsonl` and `representation_pass.json`: the job runner's `--out f"{out}/representation"` with `out = f"job-{index}"` (`setup/job_runner_stage1.py:401`, :434-438); the file names `representation_pass.py:66-67`; the s3-orig pools-only pass sits beside it under `job-I/representation-s3-orig/` (JR:436-438) and is not read | plan.json `hosts.a-8.jobs[I].outputs[rel]` (record-done keeps JOB-DONE.json's outputs: `plan_tool.py:3583-3611`; the runner hashed every file under the job's `--out` folders: JR:923-934, :1103-1112) and the block-A seal `seals/block-A.json` `files[{host, path, sha256, class}]` (`seal.py:113-116`; these names match no readable pattern, `seal.py:61`, so they are "sealed"); the seal's own SHA-256 in plan.json `seals.A.sha256` (`seal.py:150`; FOCUS:118 "`seals/block-A.json` `6c6267c8…`, 1,703 files") | yes (R): a-8 ran J5, J7 and J8 to completion and was recorded done (FOCUS:131 "`defer a-1` moved J5, J7 and J8 to a-8"; FOCUS:127 "Recorded done: a-8"; FOCUS:124 "a-8 J5/J7/J8"). The job index I is not known to me (plan.json not opened); the runner finds the one complete, pulled job of each kind by key. |
| the L1 scan (for the L1 score) | `job-I/l1-scan/l1_scan.json` (JR:444-446; `score_l1_larf.py:48` SCAN_FILE) | the same two records | yes (R, as above) |
| `--classifier` (REQ-23, J8) | `job-I/classifier/classifier_scores.json` (JR:447-453; `score_classifier.py:40` OUTPUT) | the same two records | yes (R) |
| `--l1` (REQ-10's score, Mac) | not located by a record I may read. The stage-1 L1 arm (block A: L1@1102 on a-6 → a-10, L1@1103 on a-7 → a-11, FOCUS:129, :127) trained on an edit the kit bound through a lead's sealed edit record (`plan_tool.py record-sealed`, PT:34, :3182-3192; `edit_sources` PT:848-860 reads `records.sealed[*]` → `edits[{arm, path, sha256}]`; line numbers corrected in fix round 1, verify1 N13), so an `l1_scores.json` made from a-8's J5 rows and J7 scan existed on the Mac by 25 Oct 17:09 UTC (I: a-1's J5 crashed, FOCUS:131, so a-8's are the only REQ-3 outputs; the L1 arms launched at 17:09-17:11, FOCUS:129). Its path and SHA-256 are in block A's records under `block-a/` (not opened) and in the L1 edit's provenance (not opened). READY:226-228 found no FOCUS entry naming the run either. | the report requires it to be made from the same rows file (`report_plant_ranks.py:277-278`) and to score every training row (:332-333) | **not located; the runner makes it** (default). See open point 2 for the optional consistency check. |
| `--datashield` (REQ-12, Mac) | no recorded Mac run (READY:227-228; M: FOCUS has no "datashield" entry) | — | **does not exist; the runner makes it** |
| `--prepared` | the Mac's `tmp/kt-prepared/prepared-kt-dolly-olmo2` (M: the folder name exists; the pod's `data/` "mirrors the checkout's tmp/", JR:127-128; `PREPARED_NAME`, RULES:805) | the report's settings pin `pins.prepared_manifest_sha256` (RPR:298-299; checked by the report itself) | yes (M: folder name only) |
| the W1 scripts and settings | `scripts/stage1/report_plant_ranks.py`, `score_datashield.py`, `score_l1_larf.py` and their settings | MAN1 by key (M): scripts `f5bbea25…`, `6eb4f7ea…`, `4996fd3b…` (role code); settings `c952eb72…` = RPR:62, `065e9656…` = `score_datashield.py:30`, `0d875213…` = `score_l1_larf.py:46` (role settings; each equal to the module's literal: a test holds this). MAN1 itself at RULES:416-417 (`f6283090…`). | yes |

**The report's own input rules the runner must satisfy (R, `report_plant_ranks.py`):** the plant record on this
prepared set (:300-302); the pools equal to the record's pools (:306-310); REQ-3's summary naming the rows file and
the pinned REQ-3 settings, and its plant and decoy pools pinned by the pool pins at the record's hashes (:260-269;
this is why only a-8's D-2 pass can serve); REQ-3's token counts equal to P's (:317-319); the L1 and DataShield-style
outputs made from the same rows file, with their dev scores reproduced exactly (:273-285, :330-344); the classifier
output on the record's pools (:345-350); the rerun placement equal to the record's cell sizes (:359-361). The
runner passes `--l1`, `--datashield` and `--classifier` always, and no `--counted` (a test and a mutant hold this).

## 4. The scorers' needs and the expected Mac run time (E unless marked)

- `score_datashield.py` (REQ-12): CPU; no model, no torch (R: its imports are argparse, math, sys, pathlib, the
  engine's `common` and `s1common`); it reads the rows JSONL once, the summary and the prepared view. Seconds.
- `score_l1_larf.py score` (REQ-10): CPU; no model (R: the score path reads the scan file, the rows file and the
  summary; `representation_pass` is imported for `block_output_index` and `READS` only, and that module imports no
  torch at the top). Seconds to a minute.
- `report_plant_ranks.py` (REQ-29): CPU, numpy. The slow parts: REQ-8's placement rerun on P's 4,800 prompts
  (character 5-gram Jaccard with prefix filtering, `build_plant.place`; the 23 Oct build ran it on the Mac inside the
  lead's session, FOCUS:142, no time recorded) and the bootstrap (replicates from the settings; the W1 test asserts
  2,000; 6 construction checks × 4 comparisons × 2,000 resamples of about 4,800 negatives). About 1-5 minutes in all;
  no GPU, no model download; memory tens of MB (the rows file: about 6,000 lines of 150 scalars each).
- The runner itself: hashing a few files; negligible.

## 5. Design (and the alternatives I rejected)

**The package** `scripts/stage1_s1/stage1b_mac/` (no "plant" or "decoy" in any path): `common.py` (a refusal with a
fixed message; reads that refuse a missing file, a folder or a symbolic link; the pin check; PATH:SHA256; an
exclusive create; the frame that prints a refusal, or only the type of any other error), the three tools, tests, a
mutation runner (the reading_extra runner with its tree changed) and its spec.

**(1) `construction_checks`** (section 40 point 4). Before anything runs: the output folder's own name holds "plant"
and the folder is absent or empty; the hash record does not exist; the prepared folder exists; the rules module
(default the repository's `runkit/stage1-olmo/stage1_rules.py`, executed by path as the reading does) holds the four
pins; MAN1 at `rules.MAN1_PATH` hashes to `rules.MAN1_SHA256` and the three W1 scripts on disk hash to their code
entries; REQ-8's record and the two pools hash to the rules' pins (never parsed); plan.json records the block's seal
at the lead's `--expect-seal-sha256`, the seal file hashes to it and is the kit's seal record of that block; the host
is a done host of the block; for each kind (rep_pass, l1_scan, classifier) exactly one complete, pulled job; its
`outputs` lists `job-I/<folder>/<file>` with a SHA-256; the pulled file hashes to it; the seal lists exactly one
sealed entry (host, path) at that SHA-256; a given `--l1`/`--datashield` is PATH:SHA256 and re-hashes. Then the
steps run as subprocesses (`sys.executable -B`, cwd `--repo`, `PYTHONDONTWRITEBYTECODE=1`), stdout and stderr into
`OUT/log/<step>.log` only; a non-zero exit stops the run (exit 1, no record); the output file must hash to the
SHA-256 the script printed. Printed: `w1 <script> <sha>`, `input <name> <sha>`, `step <name> exit <code>`,
`output <name> <sha>`, `record <path> <sha>`. The hash record (canonical JSON, exclusive create, parents created)
holds the inputs', outputs' and W1 scripts' SHA-256, the plan's and seal's SHA-256, the pod paths, the steps with
exit codes, the commands, `report_without_counted: true`, this package's module hashes, Python's version and the
time; no text of any input or output (the synthetic report output holds sentinels; the record holds none: tested).

Alternatives rejected: (a) the lead types PATH:SHA256 for a-8's four files (rejected: finding the job index means
listing `retrieved/`, which the never-open rule forbids; four typed hashes invite error); (b) importing the W1 scripts
in-process (rejected: their refusal messages can carry a row id, RPR:281, :284, :319, and their stdout would mix with
the runner's; a subprocess with a log isolates them); (c) writing the remade L1 and DataShield outputs outside the
"plant" folder (rejected: they are later inputs of the counted run and hold no plant information, but one protected
folder is simpler and conservative; the hash record names their SHA-256 so they can be re-given as PATH:SHA256);
(d) a settings file for the package (rejected: no tunable; the pins come from MAN1 and the rules); (e) the kit's
`tmp/stage1-olmo/stage1_rules.py` as the default rules (rejected: the reading uses the repository's; byte-equal today
per CHECK's source key; `--rules` can name either; the record holds its SHA-256).

**(2) `binding_check`** (section 40 point 5): the record at the pin the lead gives (`D2_REQ8_RECORD.sha256`), kind
"stage1 plant record" (`build_plant.py:438`), `edits` a list of objects (:291-294), exactly one entry whose `file` is
`edits/planted_k37.json` (:290, :307), its `sha256` 64 hex, compared with `--edit-sha256`; prints `match` (0) or
`no match` (1); seven fixed refusals (2). Nothing else of the record is read or printed (the record names the unit
and leaf: :442).

**(3) `switch_check`** (section 40 point 13(a); the ADD:625 pattern = section 35 point 1 at `55d5f8b`, implemented by
`scripts/stage1_s1/extract_a0_fingerprint.py`: one key, by pin, nothing else): the settings at the report's own
literal `SETTINGS_SHA256` (default) and path, kind "stage1 settings" and name "report_plant_ranks", the key path
`counting.selfinf_n_counts` (RPR:228) as a JSON boolean; prints the pin and `selfinf_n_counts true|false`. A test
holds the literal to MAN1's entry for the settings file (by key; the file is not opened by any test).

## 6. Tests (synthetic only) and what they show

`tests/synth_world.py` builds a repository with stand-ins for the three W1 scripts (they parse the real scripts'
argument shapes, re-hash their PATH:SHA256 inputs, write their output and print the `  <sha256>  <name>` line; by
environment variable they leak sentinels to stdout and stderr, fail with a sentinel refusal, or print a wrong hash),
a manifest that pins them, a rules module, REQ-8's record (unit, leaf, cell, decoy, edit name and arm as sentinels)
and the pools (sentinel text), and a kit (plan.json with host a-8's three jobs and another host's arm unit whose
COMPLETE.json names an edit; the block seal; the pulled tree with both representation folders). 53 tests:

- the run: three outputs, the record text-free, no `--counted`, the leaked sentinels in the logs only;
- given `--l1`/`--datashield`: only the report runs; the record says `made_here: false`;
- a failed step and a wrong printed hash: exit 1, no record, the stand-in's sentinel refusal in the log only;
- every refusal (18 cases), each with the fixed message, nothing written and no sentinel;
- the main representation pass is read, not the s3-orig pass; the job index comes from plan.json; the runner reads no
  unit folder and lists no tree (a stray folder and a removed host do not change the run);
- an unexpected error prints its type only;
- the command lines parsed by the real `report_plant_ranks.main`, `score_datashield.main` and `score_l1_larf.main`
  (their `s1common.load_settings` patched to stop right after argparse, so no settings file is opened); the file-name
  constants equal the W1 modules'; the W1 manifest's entries by key; a malformed line fails to parse;
- the binding check: match, no match (another edit's hash; a wrong hash), seven refusals;
- the switch check: both values, seven refusals, the default pin equal to MAN1's entry;
- the shared helpers (symbolic link, folder, missing file, pin, PATH:SHA256, exclusive create, the frame).

Every test asserts that no sentinel reaches stdout, stderr, a traceback, a refusal message or the hash record.

## 7. Commands run (all in the worktree; exit codes as shown)

`PY` = `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B` with
`PYTHONDONTWRITEBYTECODE=1`; `pytest -q -p no:cacheprovider --basetemp=<fresh folder under the scratchpad's s1b/tmp/>`
(each basetemp deleted after its run).

1. `PY -m pytest ... scripts/stage1_s1/stage1b_mac/tests` — first run: 45 passed, 1 failed (a binding-check refusal
   message of mine; fixed), exit 1. Then 46 passed (exit 0); after `test_common.py` and one more refusal test: 53
   passed (exit 0), and 53 passed again after each later test edit (three runs, exit 0).
2. `PY scripts/stage1_s1/stage1b_mac/mutation/run_mutants.py --spec ... --scratch <scratchpad>/s1b/tmp/mut-shardN
   --report <scratchpad>/s1b/reports/C-mac-tools-mutation-shardN.json --timeout 300 --only <ids>`, three shards (18, 20, 14
   mutants), each with its own baseline:
   - first attempt: every shard's baseline FAILED in the copy (exit 2, no mutant run): two tests resolved the
     repository root to the mutation copy, which holds `scripts/stage1_s1` only. Fixed in the tests
     (`synth_world.repo_root()` finds the workspace on sys.path).
   - second attempt: shard 1 18/18 killed (exit 0); shard 3 14/14 killed (exit 0); shard 2 19/20 killed, exit 1:
     `CC-seal-entry-single` SURVIVED (my duplicate-seal-entry case carried the same hash, and a second attempt left
     the entry classed "readable" from the previous case). The test now makes the seal ambiguous (a sound entry plus
     a second with another hash) after restoring the entry.
   - final (the committed tree): shard 1 18/18, shard 2 20/20, shard 3 14/14 killed; baselines pass with 53 tests;
     `every mutant as expected`, exit 0 each. Reports:
     `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/s1b/reports/C-mac-tools-mutation-shard{1,2,3}.json`.
3. Read-only: `git status --short`, `git log -1`, `git show 55d5f8b:<addendum>` (lines 618-640), `shasum -a 256` of
   the new files and of CHECK/READY (`570e98ff…`, `8d1f5366…`, as section 40 states), `ls`, `grep`, `sed`, `wc`,
   `find`, `date -u`, and Python reads of MAN1 by key. All exit 0 except three `grep` calls whose regex ugrep refused
   (repeated in Python).

## 8. The mutation entries (52; one per refusal or guarded behaviour; all killed)

construction_checks (34): CC-out-name, CC-out-not-empty, CC-record-exists, CC-prepared-dir, CC-rules-names,
CC-rules-form, CC-man1-pin, CC-man1-role, CC-w1-script-pin, CC-seal-expect, CC-seal-hash, CC-seal-kind,
CC-host-done, CC-host-block, CC-job-single, CC-job-status, CC-job-pulled, CC-outputs-list, CC-pod-hash,
CC-seal-entry-single, CC-seal-entry-class, CC-seal-entry-hash, CC-main-pass, CC-job-index, CC-req8-pin, CC-pool-pin,
CC-given-hash, CC-step-exit, CC-step-output, CC-report-counted, CC-log-stdout-shown, CC-log-stderr-shown,
CC-l1-subcommand, CC-output-name. common (4): CO-hashed-pair, CO-symlink, CO-exclusive, CO-frame-type-only.
binding_check (8): BC-kind, BC-edits-list, BC-single-entry, BC-sha-hex, BC-record-pin, BC-edit-hex, BC-match,
BC-exit. switch_check (6): SC-pin, SC-name, SC-key-path, SC-bool, SC-print, SC-hex.

Not mutated (equivalent or needing a disk fault): `read_pinned`'s malformed-pin branch (a mismatch refuses anyway);
`write_exclusive`'s read-back check. (Fix round 1 added 14 entries, 66 in all, listed in its section below.)

## 9. The lead's runbook (in order; $0; also in the package README)

`PY` as above, from the main checkout `/Users/spiderishi/Coding/attribution` after the package is merged there.

1. **The binding check.** `H_EDIT=$(shasum -a 256 <full-out>/edits/planted_k37.json | cut -c1-64)` — the
   `--full-out` folder of the 23 Oct build under `tmp/stage1-mac-runs-20261023/` (`shasum` shows the hash and the
   path, no byte; never `cat`, `less` or an editor). The record's pin: `D2_REQ8_RECORD["sha256"]` in
   `runkit/stage1-olmo/stage1_rules.py:384`.

       PY -m scripts.stage1_s1.stage1b_mac.binding_check \
           --record .ai/inputs/stage1-commitments-20261016/plant/plant_record.json \
           --expect-record-sha256 <D2_REQ8_RECORD.sha256> --edit-sha256 $H_EDIT

   Expect `match`, exit 0. The pair (that path, `$H_EDIT`) is what round 35's sealed edit record carries for
   `a0_plant` (section 40 point 5).
2. **The switch check.** `PY -m scripts.stage1_s1.stage1b_mac.switch_check` (defaults: the report's settings path
   and `SETTINGS_SHA256`). Expect `selfinf_n_counts true` (the W1 test `test_the_committed_settings` asserts the same
   value, RPR tests:214-219; the two readings should agree).
3. **The construction-check runner.** The seal's SHA-256 by key (never by opening the seal or listing `seals/`):
   `PY -c 'import json; print(json.load(open("tmp/stage1-olmo/plan.json"))["seals"]["A"]["sha256"])'` (it must start
   `6c6267c8`, FOCUS:118). Then:

       PY -m scripts.stage1_s1.stage1b_mac.construction_checks \
           --repo /Users/spiderishi/Coding/attribution --kit /Users/spiderishi/Coding/attribution/tmp/stage1-olmo \
           --block A --host a-8 --expect-seal-sha256 <that value> \
           --prepared /Users/spiderishi/Coding/attribution/tmp/kt-prepared/prepared-kt-dolly-olmo2 \
           --plant-pool <full-out>/plant.pool.json --decoy-pool <full-out>/decoy.pool.json \
           --out /Users/spiderishi/Coding/attribution/tmp/stage1b/plant-construction-checks \
           --record /Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/stage1b/construction-checks-hashes.json

   It prints the W1 pins, the inputs' hashes, `step datashield exit 0`, `step l1 exit 0`, `step report exit 0`, the
   three outputs' hashes and `record <path> <sha256>`. On exit 2 nothing was written (the message says which check
   failed; no value). On exit 1 a step failed: stdout names the step, and stderr's `reason:` line holds the W1
   script's refusal only when it is one of the pinned scripts' value-free lines (a message the code raises as one
   string literal); any other last line is withheld. **Never read a log or any file under `--out`** (fix round 1,
   verify1 D1: the earlier sentence here that allowed a conditional read was wrong; RPR:115 can name the drawn leaf's
   cell and RPR:150 its rank): clear `--out` with `rm -rf`, fix the input the step and the reason name (re-check it
   by hash through the records), and run again. Nothing under `--out` is opened until the counted outputs are hashed
   or a final "stop". Give `--expect-rules-sha256 $(shasum -a 256 runkit/stage1-olmo/stage1_rules.py | cut -c1-64)`
   (fix round 1, verify1 N2) so the rules module is pinned, not only recorded.
4. **Commit the hash record**: `git add .ai/inputs/stage1-post-w1-20261023/stage1b/construction-checks-hashes.json`
   (an explicit path; the file holds hashes, names, exit codes, commands and the time; no text of any input).
5. **Time-stamp it**: `ots stamp <that file>` with the scratch venv's opentimestamps client (as on 31 Oct; the
   `.ots` stays beside it, `ots upgrade` later); check without a node with
   `.ai/inputs/stage1-post-w1-20261023/reading/lead-reports-20261101/tools/ots_check.py OUT_RECORD <file>`.
   "Published before the pilot" is that committed, stamped SHA-256 (section 40 point 4). The next OTS manifest (if the
   lead extends `tools/ots_manifest.py`'s list) can carry the same SHA-256.

## 10. Acceptance criteria

- Passed: the package with the three tools, no "plant"/"decoy" path; hashes, exit codes and fixed messages only;
  exclusive creates; canonical JSON (the engine's `canonical_json`); the runner resolves every input by exact path
  and SHA-256 through the kit's records by key and the rules' pins; subprocess output captured, never shown; the hash
  record outside the "plant" folder; the report without `--counted`; synthetic tests with sentinels on success and on
  every refusal path (53 passed); the command lines parsed by the real parsers; a mutation spec with one mutant per
  refusal, run in three shards within the time limit (52/52 killed, baselines first with the same command).
- Not tested (by rule): any run on the real inputs; the real report's own input rules on the real files; the Mac run
  time (estimated only).

## 11. Open points for the lead

1. **The two pool paths.** The `--full-out` folder name of the 23 Oct build is not in any record I may read; the lead
   supplies the two paths. A wrong file refuses by hash (`D2_POOLS`), so nothing can run on the wrong pools.
2. **The existing L1 score.** By default the runner remakes `l1_scores.json` from a-8's J5 rows and J7 scan (a pure,
   deterministic function of those files and the pinned settings: `score_l1_larf.py:239-285`). If the lead wants the
   construction checks to use the very file the L1 arm's edit came from, locate it by key through block A's sealed
   edit record (`records.sealed[*]` in plan.json → that record's `edits[]` entry for arm `L1` → the edit file's
   provenance names the scorer output's SHA-256; the lead's Mac run folder holds the file) and pass it as
   `--l1 PATH:SHA256`; the report then checks it against a-8's rows itself (RPR:277-278). Both routes satisfy
   section 40; the remake avoids opening any block-A record. The same holds for DataShield-style (no earlier run).
3. **The seal hash:** `--expect-seal-sha256` must be the full value from plan.json `seals.A.sha256`; FOCUS:118 gives
   only `6c6267c8…`.
4. **Where `tmp/stage1b/` sits.** `tmp/` is git-ignored (`.gitignore:1`), so the "plant" folder is never committed;
   the hash record's folder `.ai/inputs/stage1-post-w1-20261023/stage1b/` is new (the runner creates it).
5. **The real report's run time** is an estimate (section 4); the runner has no timeout. If the placement rerun takes
   long, the lead waits; nothing is shown either way.
6. **`sys.executable`:** the runner runs the W1 scripts with the interpreter that runs it; use the venv python that
   has numpy (the report needs it; the scorers need only the standard library and the engine's `common`).
7. **The `--out` folder on a retry:** `rm -rf` it without listing it; the runner refuses a non-empty folder.
8. **Round 35 (track K):** the binding check's pair is the sealed edit record's `{arm: "a0_plant", path, sha256}`;
   the record build_plant writes lists the entry's `arm` as the engine's parsed arm name (`build_plant.py:291`,
   `edit.arm`), which the binding check does not read or compare (I do not know the mapping to `a0_plant`; the kit's
   record names the kit arm, CHECK:295-298).
9. **Scope.** Nothing here reads a unit folder, `retrieved/` beyond the three named files, a judge file or any
   outcome. The runner's reads of `plan.json` and `seals/block-A.json` are by key, as section 40 point 3 allows for
   reviewed code; the lead never lists those folders.

## 12. Replies to the brief's questions

- "whether the L1 and DataShield-style outputs already exist": L1 — in effect yes (the L1 arm's edit needed it) but
  its record is under `block-a/` (not opened) and FOCUS does not name it; DataShield-style — no. The runner makes
  both unless given.
- "what each scorer needs (a GPU or model, or only REQ-3's arrays) and how long it would take on the Mac": only
  REQ-3's arrays, the L1 scan and the prepared set; CPU; seconds for the scorers, about 1-5 minutes for the report
  (E; section 4).
- "where each input lives and where its expected SHA-256 is recorded": section 3.

Scratch folders used under the scratchpad's `s1b/tmp/` (`bt*`, `mut-shard*`) were deleted after their runs.

## Fix round 1 (2026-11-01T23:05 to 23:30 UTC; `date -u` checked; verify1 = `reports/C-mac-tools-verify1.md`)

Status: DONE. Both defects fixed; every note addressed except N8-N12 (no change needed; N9 is noted below). The
worktree is still detached at `0d25497`; `git status --porcelain` shows only `?? scripts/stage1_s1/stage1b_mac/`; no
git command changed state; nothing committed. Two sentences of this report were corrected in place (§3's `--l1` row,
N13; §9 step 3, D1), marked "fix round 1". The hard-rule log of section 1 holds; read in this round, as code or by
key: `s1common.py:83-120, :605-632` (the strict parser, `write_new_files`), the three W1 scripts' main frames
(RPR:406-440, `score_datashield.py:111-117`, `score_l1_larf.py:316-322`), every `Refusal(` line of the four modules
(grep), `seal.py:195-235`, `plan_tool.py` by grep (`edit_sources` :848, `records(plan)["sealed"]` :859, record-sealed
:34, :3182-3192), `stage1_rules.py:380-420`, `extract_a0_fingerprint.py:1-40`, the lead's two OTS tools' docstrings,
and MAN1 by key (top-level keys, roles, path prefixes, and whether each entry hashes on disk: counts only; the 8
entries whose path holds "plant" were not hashed by me).

### D1 (blinding; the runbook) - fixed

- The sentence in §9 step 3 that let the lead read a log "if it is sure the W1 script's refusal names no leaf" is
  struck (§9 step 3 and the README's step 3 now say: never read a log or any file under `--out`). The verifier is
  right (R, my grep): RPR:115 `Refusal(f"cell {cell} has no scored row")` fires in `rank()` on the planted leaf's own
  chain, RPR:82 names a placement cell, RPR:150 names `r`, the leaf's rank; the log is the script's stderr verbatim.
- So that the lead still learns why a step failed without opening anything, the runner now prints the reason itself,
  and only when it cannot hold a value. The three W1 main frames print a refusal as
  `REFUSED: <message> (nothing written)` and an OSError as `REFUSED: <type name> (nothing written)` (R: RPR:435,
  `score_datashield.py:114`, `score_l1_larf.py:319`). `construction_checks.value_free_messages` parses the pinned
  sources (the three scripts and `s1common.py`, each already hashed to its MAN1 entry; the bytes parsed are the bytes
  hashed) with `ast` and whitelists every `Refusal(...)` call whose one argument is a string literal (an f-string, a
  concatenation, a `%` or a variable is left out), plus the built-in OSError type names. `known_reason` returns the
  failed step's last non-blank stderr line only when it is in that set. stderr then shows
  `FAILED: step <name> exited <code>; its log stays in the output folder (never opened); no record written` and
  `reason: REFUSED: <literal> (nothing written)` or `reason: withheld (...)`. The set is fixed by the pinned code, not
  by any input, so no byte of a plant, decoy or outcome can reach it. On the real scripts (M, a test on the code):
  the literal lines are in (for example `the rows file is not the one REQ-3's summary names`, `REQ-8's placement,
  rerun here, differs from the plant record's cell sizes`, `the scan file is not an L1 layer scan`), the f-string
  ones are out (`has no scored row`, `hashes to`), and no whitelisted line holds a brace.
- Tests: the stand-ins now refuse through the same frame as the real scripts; `FAKE_FAIL` (a message built from
  sentinels) gives `withheld` with the sentinels in the log only; `FAKE_FAIL_FIXED` with `FAKE_LEAK` (sentinel lines
  on stdout and stderr, then one literal refusal) prints the literal line only; a whitelist test on the stand-ins and
  one on the real scripts. Mutants `CC-reason-unchecked` (the last line printed without the whitelist) and
  `CC-reason-literal-only` (non-literal messages whitelisted too): both killed.

### D2 (the decoy pool's pin had no test and no mutant) - fixed

`test_refuses_req8_record_or_a_pool_off_its_pin` now gives the plant pool as `--decoy-pool` and expects
`REFUSED: the decoy pool does not hash to its expected SHA-256`; spec entry `CC-second-pool-pin` (the verifier's
`V-decoy-pool-pin` edit; the id holds no protected word because an id becomes a folder name on the basetemp path,
which the fixed runner checks). Killed. The verifier's own three survivors, re-run with the same edits under ids free
of the words: 3/3 killed (`reports/C-mac-tools-fix1-mutation-verifier-own.json`).

### Notes addressed

- N1 (exit 2 after the steps): the record's folder is checked before anything runs (`the hash record's folder is not
  a folder`; mutant `CC-record-parent`) and created before the steps; the logs are written as bytes and the scripts'
  output decoded with replacement, so output that is not UTF-8 is logged and the run goes on (`FAKE_RAW`; mutant
  `CC-log-strict-text`); the docstrings say that only a disk fault at the record write can exit 2 after the steps.
- N2 (the rules module ran unpinned): `--expect-rules-sha256` (optional; refused when not 64 hex or off the pin;
  the record holds `rules_pinned`); mutants `CC-rules-pin`, `CC-rules-pin-hex`. The runbook gives it from
  `shasum -a 256 runkit/stage1-olmo/stage1_rules.py` (code).
- N3 (the record's path): refused when its resolved path holds "plant" or "decoy" (case-insensitive); mutant
  `CC-record-word`. A record inside `--out` is covered by the same rule, since `--out`'s own name must hold "plant":
  a separate "inside the output folder" check was dead code (my first suite run showed the word rule fires first),
  so it was dropped.
- N4 (repeated JSON keys): `common.json_object` parses with an `object_pairs_hook` and refuses `<what> repeats a key`
  (standard library, as the package's contract says); mutant `CO-repeated-key`.
- N5 (test strictness): every stdout line of every run must match the grammar
  `w1 <script> <sha>|input <name> <sha>|output <step> <sha>|record <path> <sha>|step <step> exit <code>`; a seal
  entry of another host at the same path and SHA-256 leaves the run unchanged, and the host's entry moved to another
  host refuses; mutants `CC-input-print-path`, `CC-seal-host-filter` (both killed; the verifier's two survivors too).
- N6: the README names the kit's `seal.py status` line `seal A: ... sha256 <full>` (`seal.py:221-222`) as the same
  value as the plan.json one-liner, which stays the primary way (status also prints one line per host).
- N7 (only the three scripts were pinned): every MAN1 entry under `scripts/stage1/` of role `code`, `settings` or
  `pinned input` is re-hashed before the steps (`a W1 file ...` refusals; an entry without a SHA-256 refuses); the
  record holds `w1_tree {entries, roles, sha256}` and `input w1_tree <sha>` is printed (the SHA-256 of the sorted
  (path, sha256) list). On the real MAN1 these are 36 + 31 + 2 = 69 entries (M, by key); the 62 tests, the mutation
  specs and the README are not run by the report and are not checked. (M) All 132 MAN1 entries whose path holds
  neither word hash on disk to their entries at `0d25497`; the other 8 (3 settings, 3 tests, 2 code) the runner
  hashes at run time. Mutants `CC-w1-tree-pin`, `CC-w1-tree-roles`, `CC-w1-entry-hex`.
- N8, N10, N11, N12: no change. N9: a J5 summary from the D-2 fallback route would be refused by RPR:269, an
  f-string (`REQ-3's pool {name} ...`), so the reason would be `withheld`; see open point 2 below.
- N13: §3's `--l1` row now cites `plan_tool.py` `edit_sources` :848-860 and record-sealed :34, :3182-3192 (R).

### Commands run (exit codes as shown; `PY` and the pytest options as in section 7)

1. `PY -m pytest ... --basetemp=<s1b/tmp/fix1-bt1> scripts/stage1_s1/stage1b_mac/tests`: 61 passed, 1 failed
   (the dead "inside the output folder" check: the word rule fired first), exit 1. After dropping that check:
   `--basetemp=<fix1-bt2>`: 62 passed, exit 0. Each basetemp deleted.
2. `PY scripts/stage1_s1/stage1b_mac/mutation/run_mutants.py --spec ... --scratch <s1b/tmp/fix1-mut-shardN>
   --report <s1b/reports/C-mac-tools-fix1-mutation-shardN.json> --timeout 300 --only <ids>`, three shards run
   together, each with its own baseline (62 tests, pass): shard 1 (22 `construction_checks` mutants) 22/22 killed;
   shard 2 (the other 12 `construction_checks`, 4 `common`, 8 `binding_check`) 24/24 killed; shard 3 (6
   `switch_check` and the 14 new mutants) 20/20 killed; "every mutant as expected", exit 0 each; scratch deleted.
   66 mutants in the spec, all killed (52 before, 14 added: `CC-second-pool-pin`, `CC-seal-host-filter`,
   `CC-input-print-path`, `CC-record-word`, `CC-record-parent`, `CC-rules-pin`, `CC-rules-pin-hex`,
   `CC-w1-tree-pin`, `CC-w1-tree-roles`, `CC-w1-entry-hex`, `CC-reason-unchecked`, `CC-reason-literal-only`,
   `CC-log-strict-text`, `CO-repeated-key`); the two `CC-log-*-shown` entries' find texts follow the new
   `run_step` return line.
3. The verifier's `my_mutants.json` with `V-decoy-pool-pin` renamed `V-second-pool-pin` (same edit): baseline pass
   (62), 3/3 killed, exit 0 (`reports/C-mac-tools-fix1-mutation-verifier-own.json`); scratch deleted.
4. Read-only: `git status --porcelain`, `git rev-parse HEAD`, `shasum -a 256`, `wc -l`, `find`, `grep`, `sed`,
   `ls`, `date -u` (all 0), Python reads of MAN1 by key (0). No `__pycache__` left; no path of the package holds
   "plant" or "decoy" (M).

### Changed files (before -> after SHA-256; lines)

| File (under `scripts/stage1_s1/stage1b_mac/`) | Before | After | Lines |
|---|---|---|---|
| `construction_checks.py` | `1e7f73a761adfa8dd40b2c07497f2ecf98e40ecf1266df8d2bd40f316c620009` | `9a03a5f3c632b54b9f531cac33ee7b991bb29b09a0f3af96f993cc6b564761c2` | 339 -> 435 |
| `common.py` | `1ba389746fb44e4bdca320cb4bf1bda7d791c8e92cfb08909625f7883c5bcb3a` | `61140654533421a2ebbc8eee029568814c7d526935d586818b0e5a91b79add18` | 103 -> 119 |
| `__init__.py` | `98d67ab124c59d8c3f09bc5f6b5f25a549bc27cfc210f16b6f5e5ee84fed226d` | `ed0b5bd726c5c361fbfddeeab41ba96d46a15d458cbcf15970302116f365056e` | 31 -> 33 |
| `README.md` | `eae1c95a40eef4818a101dc4071dc2fced4612324bf4ba7ddc68ef6758ac4fc4` | `975f726afce61f9f948d74869571d8319d87cad82a4f6167d314d6fafdf98a5b` | 53 -> 63 |
| `mutation/mutants_stage1b_mac.json` | `5c104fc42e0fa6d1bbfe554b5a306c85d182030157811c429a838bd7d8d4ea56` | `7ad3d2c08f81672de4ef52315a3e9a22b59ee64c3d8feeacbf24aeb6915c3033` | 421 -> 533 (52 -> 66 mutants) |
| `tests/synth_world.py` | `aa71cc0b2e23c4b419493fdbd677405eb3cd81f4cb15afa04b8ce4c2987fa2d2` | `34f92be90a0783b5d01b828f06ad88062baf1203a9b46a62b3adc238e7c65840` | 302 -> 361 |
| `tests/test_construction_checks.py` | `83916cf5a00d1f81f4ef794deb192445585a03c56bedc65f95a1764bde773c58` | `39879faed49f53e8cfc8b0c7dcf0027f4a46dca8c8fcdc88d8c41da05ef8a6d8` | 326 -> 459 |
| `tests/test_argv_compat.py` | `92a3aba0395f357416c247e86122659525185acb8beb64af25e1beb5dc084c7d` | `929155ad3d03a2ce1a70d4acd385f1f2031f21b3ef4a89a19df75944a5148f2b` | 100 -> 120 |
| `tests/test_common.py` | `68c1972a9df12e6d1afccc71f06fd617e1b899d8e254a3b3f53708bfb28296bc` | `d4175d7694aa490e6ff505573806c66654f7b6f42f0672bc57db4587b2a54089` | 74 -> 79 |

Unchanged: `binding_check.py` (`c33fee27…`), `switch_check.py` (`e00a8ce6…`), `mutation/run_mutants.py`
(`5bf8c7e4…`), `tests/conftest.py` (`ed7b7602…`), `tests/test_binding_check.py` (`30eb5474…`),
`tests/test_switch_check.py` (`4bb20f51…`). No file outside the package changed; the W1 code, the manifest's files,
B16, the input builder, the engine and the kit are untouched.

### Acceptance criteria after the fix round

- Passed: both defects fixed with a test and a mutant each; every note with a code change has a test and a mutant;
  no sentinel reaches stdout, stderr, a refusal, a traceback or the hash record on success, on a failed step (with
  and without a printable reason) and on every refusal path (62 tests); the runner's command lines still parse with
  the real W1 parsers; 66/66 mutants killed in three shards within the time limit, baselines first, the same command.
- Not tested (by rule): any run on the real inputs; the real report's refusals on the real files; the Mac run time.

### Open points for the lead (added or changed by this round)

1. **The reason line is a design choice.** It never opens a file: the runner decides in memory, from a finite set of
   strings fixed by the pinned code. If the lead prefers that nothing about a failed step is printed, the two
   `print(... "reason: ...")` lines in `construction_checks._run` can go (the tests `..._withholds_a_reason...` and
   `..._prints_that_line_only` and the two `CC-reason-*` mutants with them); the rest is unchanged.
2. **A `withheld` reason at the report step** (after both scorers passed) most likely means one of RPR's f-string
   input rules fired: :82, :115 (a placement cell), :150, :231, :254-256 (a hash), :269 (the D-2 route of a-8's J5
   pass, verify1 N9), :276-284 (a scorer output's provenance or a row id), :309, :319-322, :358, :379. The lead cannot
   learn which without another reviewed key-only reader; the safe move is to re-check the inputs by hash through the
   records and the a-8 J5 summary's route by key (`pools[*].pinned_by == "pool pins"`, RPR:260-269), then re-run.
3. **The basetemp path** of any test or mutation run must hold neither "plant" nor "decoy" (the record-path rule
   applies in the synthetic world too); a mutant id becomes a folder name, so the spec's ids avoid both words.
4. **N7's scope** pins 69 W1 files (code, settings, pinned inputs). A later legitimate change to any of them would
   make the runner refuse; that is the intended reading of "pinned; never edited".
