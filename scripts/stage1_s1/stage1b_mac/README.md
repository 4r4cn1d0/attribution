# scripts/stage1_s1/stage1b_mac: the Mac-side stage-1b tools

New files only (addendum section 40; no path or file name here holds the plant's name, so the code may be read).
Each tool prints SHA-256 values, exit codes and fixed messages; never a value, a unit, a leaf, a cell or a row id.
The W1 scripts it runs (`scripts/stage1/report_plant_ranks.py`, `score_datashield.py`, `score_l1_larf.py`) are
pinned by the W1 manifest and never edited; the kit's rules module is executed by path and never edited.

| Tool | Rule | Reads | Prints |
|---|---|---|---|
| `construction_checks` | section 40 point 4: the construction checks run after the stage-1 reading, by the plant-rank report without `--counted`, into a "plant" folder; the output is committed and time-stamped by SHA-256, unopened | the kit's `plan.json` and the block seal by key; pod a-8's J5, J7 and J8 outputs by exact path and SHA-256; REQ-8's record and the two pools at the rules' pins (hashed only); the W1 manifest by key, and every W1 file the report can execute or read (code, settings, pinned inputs under `scripts/stage1/`) at its entry | each input's and output's SHA-256, each step's exit code, the hash record's path and SHA-256; on a failed step, its reason only when it is one of the pinned W1 scripts' value-free refusal lines |
| `binding_check` | section 40 point 5: REQ-8's record lists, for `edits/planted_k37.json`, the SHA-256 the lead computed from the edit file | the record, at the pin the lead gives, by key | `match` (exit 0) or `no match` (exit 1) |
| `switch_check` | section 40 point 13(a): the plant-rank report counts Self-Inf-N-style only while its settings' switch says REQ-13 was committed at W1 | the report's settings at its own pin, one key | the settings' SHA-256 and `selfinf_n_counts true` or `false` |

## The lead's runbook (in order; every command at $0)

1. **The binding check.** `H_EDIT=$(shasum -a 256 <full-out>/edits/planted_k37.json | cut -c1-64)` (the `--full-out`
   folder of the 23 Oct plant build under git-ignored `tmp/stage1-mac-runs-20261023/`; `shasum` shows the hash and
   the path, no byte). Then, with the record's pin from `runkit/stage1-olmo/stage1_rules.py` `D2_REQ8_RECORD`:

       PY -B -m scripts.stage1_s1.stage1b_mac.binding_check \
           --record .ai/inputs/stage1-commitments-20261016/plant/plant_record.json \
           --expect-record-sha256 <D2_REQ8_RECORD.sha256> --edit-sha256 $H_EDIT

   `match` and exit 0; the pair (path, `$H_EDIT`) is what round 35's sealed edit record carries for `a0_plant`.
2. **The switch check.** `PY -B -m scripts.stage1_s1.stage1b_mac.switch_check` (defaults: the report's settings path
   and its `SETTINGS_SHA256`). Expect `selfinf_n_counts true` (the W1 test `test_the_committed_settings` asserts the
   same value, so the two readings agree).
3. **The construction-check runner.** The seal's SHA-256 by key: `PY -c 'import json; print(json.load(open("tmp/stage1-olmo/plan.json"))["seals"]["A"]["sha256"])'`
   (FOCUS, 27 Oct 14:14 UTC: `seals/block-A.json` `6c6267c8…`; the kit's own `seal.py status` prints the same value
   on its line `seal A: ... sha256 <full>`, beside one line per host). The rules module's SHA-256:
   `shasum -a 256 runkit/stage1-olmo/stage1_rules.py` (code; the stamped tree's value). Then:

       PY -B -m scripts.stage1_s1.stage1b_mac.construction_checks \
           --repo /Users/spiderishi/Coding/attribution --kit /Users/spiderishi/Coding/attribution/tmp/stage1-olmo \
           --block A --host a-8 --expect-seal-sha256 <seal sha256> --expect-rules-sha256 <rules sha256> \
           --prepared /Users/spiderishi/Coding/attribution/tmp/kt-prepared/prepared-kt-dolly-olmo2 \
           --plant-pool <full-out>/plant.pool.json --decoy-pool <full-out>/decoy.pool.json \
           --out /Users/spiderishi/Coding/attribution/tmp/stage1b/plant-construction-checks \
           --record /Users/spiderishi/Coding/attribution/.ai/inputs/stage1-post-w1-20261023/stage1b/construction-checks-hashes.json

   It makes `datashield/datashield_scores.json` and `l1/l1_scores.json` inside `--out` (give `--l1 PATH:SHA256` or
   `--datashield PATH:SHA256` instead when an output made from a-8's rows file already exists), then
   `report/plant_ranks.json`. Exit 0 and `record <path> <sha256>` end the run. On exit 2 nothing was written (the
   message names the check that failed; no value). On exit 1 a step failed: stdout names the step, and stderr's
   `reason:` line holds the W1 script's refusal only when it is one of the pinned scripts' value-free lines (a
   message the code raises as one string literal, such as `REFUSED: the rows file is not the one REQ-3's summary
   names (nothing written)`); any other last line is withheld. Never read a log or any file under `--out`: clear
   `--out` (`rm -rf`, never `ls` or `cat`), fix the input the step and the reason name (re-check it by hash through
   the records), and run again. Nothing under `--out` is opened until the counted outputs are hashed or a final
   "stop".
4. **Commit the hash record** (`git add` the exact path; it is text-free: hashes, exit codes, commands, counts and
   names; its path holds neither protected word, by the runner's own check).
5. **Time-stamp it:** `ots stamp .ai/inputs/stage1-post-w1-20261023/stage1b/construction-checks-hashes.json` with the
   scratch venv's opentimestamps client (as the 31 Oct stamp), keep the `.ots` beside it, `ots upgrade` later and
   check it without a node with `reading/lead-reports-20261101/tools/ots_check.py`. "Published before the pilot" is
   that committed, stamped SHA-256 (section 40 point 4).

Tests: `PYTHONDONTWRITEBYTECODE=1 <venv python> -B -m pytest -q -p no:cacheprovider --basetemp=<scratch>
scripts/stage1_s1/stage1b_mac/tests` (synthetic worlds only: `tests/synth_world.py`; the W1 stand-ins leak sentinels
on request, so the capture is tested; no folder on the basetemp path may hold "plant" or "decoy", since the runner
refuses a record path that does). Mutation: `mutation/run_mutants.py --spec mutation/mutants_stage1b_mac.json
--scratch <outside the workspace> --report <file> [--only id,id]` (the reading_extra runner on this tree; a mutant id
becomes a folder name, so none holds either word).
