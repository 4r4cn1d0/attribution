# O3C-fix1: the fix round for track C (the OLMo 3 probe kit and recipes)

Builder: the fix-round builder for the main-study lead. Input: `O3C-verify1.md` (read in full) and `O3C-kit-recipes-build.md`.
Started 2026-11-05 09:23 UTC; finished 09:40 UTC (`date -u` at 09:23, 09:35, 09:36, 09:37 and 09:40:19 after the report was written; `git diff --stat HEAD` still empty then).
Worktree: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/ws-all` at e89d74f. Nothing committed, nothing stashed, no tracked file edited (`git diff --stat HEAD` empty; `git status --short` still the 42 untracked files, 13 lines).
Scratch: `…/scratchpad/o3/tmp/` (every pytest basetemp and the two scratch copies deleted after use; nothing left under it from this round).
Status: DONE for D1, D2 and notes 4, 5, 7. D3 is outside this track's files (hard rule 4; the verifier's own ownership line): a patch and its proof are delivered for the lead, not applied.

Labels: **M** = measured here (a command I ran, exit status given); **R** = read (path:line); **I** = inference.

## Summary

| Defect / note | What changed | Evidence |
|---|---|---|
| D1 `states_tool.py check` refuses the probe pod's two-unit tree | `verify()` records a unit that lists no `states/<checkpoint>/` file as `"not saved"` and skips it; refuses only when no unit lists the checkpoint, and when the tar holds a unit the tree does not seal with that checkpoint; the record (version 2) carries `verified_units`; the line counts verified units | M: kit test with the two-unit tree (init unit `states/init/` only, e1 unit `states/e1/`): `states verified: 1 units`, units `{"1101-a0-init-a1": "not saved", "1101-a0-e1-a1": {files 4, …}}`; refusals for a checkpoint no unit lists and for a stray unit |
| D2 `host.py pull-states` cannot run after the finisher's stop | The finisher pulls and checks the e1 states (`STATE_PULLS = ("e1",)`) right after the light check and before `stop_pod`, while the pod still has its SSH address; the result is `finished.json`'s `states` entry; a failed pull or check leaves `review-needed-stopped` with an alert; the `states-*.tar` is never removed; the by-hand route (a user-started pod, then `get`, `pull-states`, `check`, `stop`) is in the README and `states_tool.py rule` | M: kit tests: the call order `pull-light, pull-states, extend-cap, stop`; success `verified-and-stopped` with `states.e1.verified true`; a failed pull and a failed check both `review-needed-stopped`, the stop still last, the pulled tar kept |
| D3 the nine recipes turn `test_ss_family_codec.py` red | Not edited (engine test file; outside this track). Patch `reports/O3C-fix1-D3-test_ss_family_codec.patch` (SHA-256 `64673e40…`): the `study-kt-olmo3-` prefix and `59 + 9 + gate_b_s.exists()` | M: the count with the new tuple is 69 = 59 + 9 + 1 (Gate B's S exists), every recipe loads; on a scratch copy of the two engine packages the one test fails unpatched (the verifier's assertion) and passes patched; `git apply --check` in ws-all ok (not applied) |
| Note 7 an empty states pull is kept | `host.pull_states` refuses and does not keep an archive without a regular file (`tar_file_count`: GNU tar's zero-block archive reads as an empty file; a folder entry alone counts as empty) | M: kit test: the 10 KiB zero archive and a folder-only tar → exit 1, nothing kept, no `pulls.jsonl` line; a tar with one file → exit 0 and the record line |
| Note 4 two locks in the bundle | One README paragraph | R |
| Note 5 the pack's git check | The README's preconditions name `scripts/tests/`, the data config and the prepared set beside the recipes and the kit (explicit-path commit) | R |
| Notes 1, 2, 3, 6, 8 | No change (see "For the lead") | — |

## Hashes (SHA-256, worktree-relative)

| File | Before | After |
|---|---|---|
| runkit/family-probe-olmo3/states_tool.py | 29ff23cb2a88e4f6edb4c5141c10b64da426126aeb45a55521ccfeeb207a976e | 61802aeef424b164e27bb21c0b96fe8202f55e4d7dc9552dac1b22da7d06c933 |
| runkit/family-probe-olmo3/host.py | a909fc649d7bea787938894350fee19e42d7982d75da0119d45bf2f4d69280eb | f7f6ecd14497fa546186e151fae5e59be80a7a8518e284095cbc283a7437ea3d |
| runkit/family-probe-olmo3/finisher.py (was a byte-equal copy of the original kit's; now E) | 9a9a2b7f2dcaaeb5ce3b6c63cbd3ac3a1b610c67a807664294bcd00abe8fa510 | 026552173775146e5d4792b9ba5525d40530f9e331b6dcf3e76f51c2ad1ebfd6 |
| runkit/family-probe-olmo3/README.md | 50efd75180bc07b8f89d1811636b45f29ecffb312469e00a3036559762a28e9f | 25b3b9d38ef8c19c7d7a55f9191230f6a1a1e2f6a5382ddf0cd93bbb55da254d |
| runkit/family-probe-olmo3/tests/test_family_probe_olmo3.py | e6eef7c1bd3206188fb17c88874f9a49509cdbd36de50550cd7d6deeadc3f49b | 4d45e3382c843176fde9cb12d29ce01d469b5cc6ef58d1113e3f65e07b81c215 |
| experiments/safety_selection/tests/test_ss_family_codec.py (not edited; the patch is for the lead) | 4481dce697c9d774595beec1a4b1a6bd0cf3ccc274f894d9ff15e85a3f12529f | unchanged |
| reports/O3C-fix1-D3-test_ss_family_codec.patch (new, scratch) | — | 64673e40f491d94e938a6015720b43b85fb36fe362f6e9c99697e5795397dca8 |

No other file of ws-all changed: the nine recipes, `probes.py`, `plan_tool.py`, `pack_setup.py`, `budget.py`, `probe_constants.py`, `control_token_count_olmo3.py`, the Gate A copy and its test, `setup/*`, `fetch_tokenizers_mac.py` keep the hashes of the build report. The kit's file set is unchanged (no file added or removed; `test_the_kit_holds_its_files_and_every_script_compiles` unchanged). `runkit/family-probe/` (the original kit) untouched: `git status --porcelain -- runkit/family-probe` empty; its file set equals the main checkout's.

## D1. `states_tool.py check` and the probe pod's two units

**What was wrong (R, confirmed).** `verify()` raised for any unit whose COMPLETE.json lists no `states/<checkpoint>/` file. The probe pod's `round1/` holds the untuned unit, which saves `states/init/` only (`experiments/safety_selection/runner.py:441-447`: the `previous is None` path saves INIT and the `for name in names[...]` loop is empty for target init), and the e1 unit. So `check HOST e1` refused the real tree.

**What changed** (`states_tool.py`, `verify()` and `check()`; the module doc). A unit with no listed file of that checkpoint is recorded as `"not saved"` (`NOT_SAVED`) and skipped. Refusals: no sealed unit (as before); a seal that is not complete (as before); no unit of the tree lists the checkpoint (`no unit of the tree lists a states/<ckpt>/ file in its COMPLETE.json`); the tar holds a unit folder the tree does not verify with that checkpoint (`the tar holds states/<ckpt>/ of N unit(s) the tree does not seal with that checkpoint: …`; `check()` passes the unit names of the tar's members); a listed file missing or changed (as before). The record is version 2 with `verified_units`; the printed line counts verified units. The rule text names the finisher's pull (D2) and the by-hand route.

**Checks (M).** The kit test `test_the_states_check_skips_the_untuned_unit_and_refuses_a_tree_without_the_checkpoint` builds the probe pod's tree (`_probe_tree`: the untuned unit lists `eval/init/…`, `job.json`, `states/init/state.json` present and the three `states/init/*.safetensors` listed but absent, as the light pull leaves them; the e1 unit the same at e1) and runs the tool as a subprocess: `check … e1` → exit 0, `states verified: 1 units`, record units `{"1101-a0-init-a1": "not saved", "1101-a0-e1-a1": {"files": 4, "bytes": 81}}`, `verified_units` 1, `members` 4, the adapter present in the tree; `check … init` with an init tar → 1 unit; `check … q` → exit 2 (no unit lists q; no check record written); a second e1 tar under the init unit → exit 2 (the stray-unit refusal). The builder's one-unit test is unchanged and still passes. The verifier's `verify-O3C/d1/` folder re-run with the new tool (a scratch copy, deleted): exit 0, `states verified: 1 units` — but that folder, as the verifier left it, holds the e1 unit only (their second run removed the init unit), so the decisive two-unit check is the kit test above, not this re-run.

## D2. The state rule's pull after the finisher's stop

**What was wrong (R, confirmed).** `finisher.finish()` always ends in `stop_pod()`; `host.pull_states()` needs an SSH address from the live pod record (`connection()`), which a stopped pod has not; the kit has no start command. The README's step 3 could not run as written.

**The choice.** The verifier offered two routes: (a) the finisher pulls the states before the stop; (b) a `host.py start` plus `pull-states` plus `stop`. I took (a). Why: the pod is up, billed and reachable at that moment, so the pull costs only its transfer time (about 2 GB for one e1 unit, a few minutes at $1.85/h); it needs no new API path. Route (b) rejected: a start of a stopped pod is spend outside the kit's guard; stage 1's 30 Oct recovery was not a kit command but a GraphQL zero-GPU resume (`podResumeZeroGpu`, $0.895/h, `restart_to_pull_v2.py`) run on the user's explicit "Yes, zero-GPU pull" (R: FOCUS, the 30 Oct 11:15 record); this kit speaks REST v1, and I could not test a new start call without a network. The by-hand route stays open with the commands the kit has: the user starts the pod (the console, or stage 1's zero-GPU route on the user's yes), then `host.py get HOST` (refreshes the address), `host.py pull-states HOST e1`, `states_tool.py check HOST e1`, `host.py stop HOST`. The "no delete command" rule stays; "no start command" is now stated too.

**What changed** (`finisher.py`). `STATE_PULLS = ("e1",)` (the records name the a0 e1 adapters; init and q stay open). New `pull_states(host)`: for each checkpoint, `tool("pull-states", host, ckpt)` (the tar lands in `retrieved/HOST/`), then `check_states()` runs `states_tool.py check` as a subprocess (never in-process: its refusals are `SystemExit`, which `finish()`'s `except Exception` would not catch, and the stop must always be reached). It never raises; the entry `{"pulled", "verified", "file", "bytes", "sha256", "check" | "note"}` goes into `finished.json["states"][ckpt]`; a log event `states-verified` or `states-not-verified` (with the by-hand route as `alert`). In `finish()`, for roles `job`/`first`, after the light check: `record["states"] = pull_states(host)`; `ok = ok and all verified`; so `verified-and-stopped` now means the light check passed and the e1 states were pulled and verified; otherwise `review-needed-stopped`. The archive removal after a verified stop still matches `pull-*.tar` only; a comment says the `states-*.tar` is the backup copy and stays. The module doc describes the step. `host.py`'s doc says the finisher runs `pull-states` before its stop.

**Checks (M).** `test_the_finisher_pulls_and_checks_the_e1_states_before_the_stop`: a fake `host.py` (`tool`) whose `pull-states` writes the e1 tar and prints host.py's record line; `states_tool.py check` runs for real from the kit copy. Calls in order `pull-light, pull-states e1, extend-cap 120, stop`; `finished.json` `verified-and-stopped`, `stop_confirmed` true, `states.e1` pulled and verified with the file name and `states verified: 1 units`; the light tar removed, the states tar kept; the check record `not saved` / 4 files; events `states-verified, verified, finished`; no delete or terminate call. `test_a_failed_states_pull_or_check_is_recorded_and_the_pod_still_stops` (parametrized): a failed pull (ssh refused) → `review-needed-stopped`, `states.e1 = {pulled false, verified false, note "ssh: connect … Connection refused"}`; a failed check (a wrong adapter in the tar) → `pulled true, verified false`, the check's refusal text, the pulled tar kept for the lead; in both the stop is last, one `states-not-verified` alert names the by-hand route, and no archive is removed.

## D3. The engine's codec test and the nine recipes

**Confirmed (M).** With the recipes present, `test_the_recipe_accepts_the_header_field_and_every_existing_recipe_still_validates` fails on the first OLMo 3 recipe (the prefix tuple does not know `study-kt-olmo3-`). Not a recipe defect: the recipes must carry `assistant_header` and `guard_over_limit` (O3A §16.1, MC §6.3), and renaming them under an OLMo 2 prefix would be wrong.

**Not edited here.** `experiments/safety_selection/tests/test_ss_family_codec.py` is under `experiments/safety_selection/**/*.py` (hard rule 4) and outside this track's files (the verifier: "the lead assigns it"). Delivered instead:
- the patch `…/scratchpad/o3/reports/O3C-fix1-D3-test_ss_family_codec.patch` (two hunks: the tuple gains `"study-kt-olmo3-"` with a dated comment; the count becomes `59 + 9 + gate_b_s.exists()` with the nine named in the comment). `git apply --check` in ws-all: ok (nothing applied).
- the count (M, main environment, in-process): 89 recipe files; 60 match the old tuple (59 + Gate B's S, which exists); 69 match the new one; the two fields are present exactly on those 69 and absent from the rest; every recipe loads through `load_recipe`.
- the proof (M): a scratch copy of `experiments/safety_selection` and `experiments/minimal_safety` (the first attempt with the one package alone stopped at `ModuleNotFoundError: experiments.minimal_safety`, exit 4; redone with both); the one test unpatched: `1 failed` on the verifier's assertion (exit 1); the patch applied to the copy: `1 passed` (exit 0). The copy was deleted.
The verifier's note stands: test files are not in `code_identity()`, but the stage-1 pack bundles every `.py` under `experiments/safety_selection`, so the lead commits this edit by explicit path with the recipes, the kit, track A's script and tests, and track B's config (KD8/T3).

## Notes addressed and not

- Note 7 (an empty states pull): `host.pull_states` now refuses an archive without a regular file (`tar_file_count`; exit 1, a stderr line, nothing kept). Test `test_pull_states_refuses_an_archive_without_a_file`.
- Note 4 (two locks): one README paragraph, as the verifier suggested.
- Note 5 (the pack's git check): the README's new "Preconditions" line names every untracked file that must be committed by explicit path, and the D3 edit.
- Note 1 (cap 7.0 h on reuse hosts; O3A §1.2's fine-tune-only value 4.25 h): unchanged. A lower default cap is a sizing decision (a too-tight cap ends a pod before its seal); the builder's open point 7 and the verifier both leave it to the lead, who can set `cap_hours` in a seed copy's `probes.py`.
- Notes 2, 3, 6, 8: no change (the guard's constants are the brief's; `weight_bytes` is recorded and the pod checks hashes; the test count is outside track C).

## Commands run (every one in the foreground, under a minute; exit status)

| UTC | Command (from ws-all unless said) | Result |
|---|---|---|
| 09:23 | `date -u`; `git status --short`, `git rev-parse HEAD`; `shasum -a 256` of 19 kit files and the engine test; `ls` of the kit, the scratch and the reports | e89d74f; 42 untracked; the "before" hashes |
| 09:24–09:34 | reads (Read/sed/grep): O3C-verify1.md and O3C-kit-recipes-build.md whole; `states_tool.py`, `host.py`, `finisher.py`, `README.md`, the kit test whole; `test_ss_family_codec.py:1-40,120-200`; `test_ss_probe_runkit.py:84-93,780-850,1347-1370`; `runner.py:436-482`; `engine.py:89` (the four state files); `status.py`; `plan_tool.py:60-110`; the stage-1 kit's `host.py` def list (no start); FOCUS (research/FOCUS.md) the 30 Oct 11:15 record; O3A:400-412, the §1.2 cap lines; the scout's state-rule lines; the data config's `kind` | — |
| 09:34 | Edits: `states_tool.py` (3), `host.py` (3), `finisher.py` (6), `README.md` (4), the kit test (2) | — |
| 09:35 | `py_compile` of the four scripts (first try with `cfile=/dev/null` refused by py_compile: exit 1; redone with a scratch cfile): all compile | 0 |
| 09:35 | main env: `venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=<scratch>/pytest-fix1-kit-main runkit/family-probe-olmo3/tests` | **38 passed in 0.66 s**, exit 0; basetemp deleted; no `__pycache__` |
| 09:36 | OLMo 3 env (`tmp/olmo3-venv`, transformers 4.57.1, pytest 8.4.2): the same on `pytest-fix1-kit-o3` | **38 passed in 0.69 s**, exit 0; basetemp deleted |
| 09:36 | main env: `… test_ss_probe_runkit.py test_ss_family_recipes.py` (`pytest-fix1-runkit-main`) | 181 passed in 1.03 s, exit 0; basetemp deleted |
| 09:36 | the verifier's `verify-O3C/d1` copied to `tmp/fix1-d1`, `states_tool.py` replaced, `python3.11 -B states_tool.py check olmo3-7b-1101 e1` | exit 0, `states verified: 1 units` (the folder holds the e1 unit only, see D1); copy deleted |
| 09:36 | the D3 count (main env, in-process; the script in this report's D3 section) | 69 = 59 + 9 + 1; every recipe loads; exit 0 |
| 09:37 | `rsync` of `experiments/safety_selection` to `tmp/d3`; the one test unpatched | exit 4 (`ModuleNotFoundError: experiments.minimal_safety`); the copy redone with both packages |
| 09:37 | the patch written (`diff -u` of the test file against a patched copy); `git apply --check` in ws-all; `shasum` of the patch | ok; `64673e40…` |
| 09:37 | `tmp/d3` with both packages: the one test unpatched, then `patch -p1` with the lead's patch, then the one test | 1 failed (exit 1), then 1 passed (exit 0); copy and basetemps deleted |
| 09:37 | after hashes; `git status --short | wc -l` 13; `git diff --stat HEAD` empty; `git status --porcelain -- runkit/family-probe` empty; `git stash list` empty; no `__pycache__` under the kit; no basetemp under scratch; the original kit's file set equals the main checkout's; `date -u` 09:37:35 | — |

## Acceptance criteria

- D1 fixed, with the two-unit case in the test: PASSED.
- D2 fixed (the state rule executable on the probe pod and on reuse pods), the stop always reached, the states tar never removed, the choice stated in the README: PASSED.
- D3: NOT CHANGED in ws-all (outside this track; hard rule 4). The patch and its proof are ready for the lead: PASSED as a deliverable, FAILED as a green suite until the lead applies it.
- Notes addressed where cheap (4, 5, 7): PASSED. Notes 1, 2, 3, 6, 8: no change, stated.
- Affected tests re-run under both environments: PASSED (38 and 38; 181 for the engine's kit and recipe tests, main environment).
- No network, install, pod, API call, download, git state change, edit of the main checkout, the engine, the original kit or a frozen record; no COMPLETE.json, answer, label, judge, plant or decoy file, hidden or selector bank opened (the synthetic COMPLETE.json files of the tests are written and read by the tools under test only); the prepared set not touched: PASSED.

## For the lead (unresolved)

1. **D3 needs your edit** of `experiments/safety_selection/tests/test_ss_family_codec.py` (the patch above) in the same explicit-path commit as the recipes; until then the CPU suite is 1 failed, 1,107 passed, 5 skipped with the recipes present.
2. **`verified-and-stopped` changed meaning** for this kit's finisher: it now also requires the e1 states pulled and verified. `status.py` prints the status unchanged; `finished.json["states"]` says why a host is `review-needed-stopped`.
3. **The states pull bills pod time**: about 2 GB per e1 unit over SSH after the job (a few minutes at $1.85/h, under $0.15). The 7.0 h cap already carries the overhead term; a job that ends at the cap could lose the pull to the in-pod timer, exactly as the light pull could before.
4. **No start command.** A failed pull or check needs the user to start the stopped pod (spend; the console, or stage 1's zero-GPU route on the user's yes). If you want a kit command for that, it is a new REST path I could not test here.
5. **`STATE_PULLS = ("e1",)`**: init and q are left open by the records, as before (the builder's open point 8).
6. **Cap 7.0 h on reuse pods** (verifier note 1): unchanged; your call per seed copy.
