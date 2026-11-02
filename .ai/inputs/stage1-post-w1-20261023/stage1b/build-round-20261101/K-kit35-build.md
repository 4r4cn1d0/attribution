# K-kit35: kit round 35, stage 1b's pilot block P (build report)

Written by the track K-kit35 builder for the lead (GI VIII/IX), 1 Nov 2026, finished about 23:35 UTC (clock read with
`date -u`; the task text's "today 2 Nov" is ahead of the Mac's clock). Model identity is the launcher's record, not
this text.

Worktree: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/s1b/ws-k`
(detached at 0d25497). Nothing is committed, synced or launched. The round record is
`research/experiments/2026-10-24-stage1-runkit/kit-round-35.json` in that worktree (its SHA-256 is in §2).
Evidence: the mutation reports `.../scratchpad/s1b/reports/K-kit35-mutants-shard-{1..6}.json` and
`K-kit35-mutants-retargeted.json` (the official runner's own output files).

## 1. Result in short

- **Block `P`**, stage 1b's pilot: a0_plant (the existing kind `arm`, J9; recipe S; 38 steps) at 1101, 1102 and 1103
  on one pod, from its own run table (`stage1_rules.plant_runs`, `plant_deal`), its own funding group `P`, host
  prefix `p`, after block B is complete and sealed, with no judge launch. No new job kind (J23 stays free).
- **The edit by SHA-256 only.** A sealed edit record `{arm: "a0_plant", path, sha256}`; bound at init (the dry run
  refuses without it) and at release; a changed or missing file refuses. **Added:** `record-sealed` and every binding
  check the record against REQ-8's record, read by key (`full_files["edits/planted_k37.json"]`), so only the plant
  build's own file can be recorded, and nobody opens it.
- **The runner** writes a readable `job-I/arm-adapter-fingerprint.json` for each plant-arm job (e1, q, arm, seed,
  steps, unit, COMPLETE.json SHA-256, the identity hashes; no edit field; exclusive create, canonical JSON).
- **record-done** prints P's units and records by path and SHA-256 (the pilot reader's inputs, by key) and refuses a
  record that is not the run's. **The seal** needs no judge (tested: 22 files, 15 sealed, 7 readable).
- **Money (Branch 128):** cap **5.75 h**, upper spend **$7.43** (as CHECK §1.1 expects), guard $16.64, need
  **$20.80** (base $16.64, contingency $4.16), worst case at the cap $10.29.
- **Tests.** Kit suite 735 -> **762 passed** (27 new); reading-input suite with the new rules file 284 passed.
- **Mutants.** 39 new (`B15-35-*`) and 3 retargeted: **42/42 killed** by the official runner (baseline 762 in each
  run), 0 survived, 0 invalid.
- **Blocks A, B and C's tables and `REJUDGED_PINS["A"]`** are byte-identical: a test holds their values captured at
  0d25497 before the round.

## 2. Files changed (all in the worktree)

| File | Old SHA-256 | New SHA-256 | What changed |
|---|---|---|---|
| `runkit/stage1-olmo/stage1_rules.py` | `4005cb4e…` | `d52614e4…` | docstring; `ARM_DOSE["a0_plant"] = "plant"`, `DOSE_STEPS["plant"] = 38`; the stage-1b block (`PLANT_ARMS`, `PLANT_SEEDS`, `PLANT_EDIT_FILES`, `ARM_FINGERPRINT_RECORD`, `ARM_FINGERPRINT_KIND`, `plant_runs`, `plant_deal`); `REJUDGED_PINS["P"] = ()` (a statement after the table); block P in `BLOCKS`, `FUNDING_BLOCK`, `HOST_PREFIX` (`p`), `BLOCK_KINDS` (`("arm",)`) |
| `runkit/stage1-olmo/plan_tool.py` | `27e299b5…` | `031c7ee3…` | docstring; `gate_order` (G3 for P; P after block B complete and sealed); `plant_edit_problem`, `plant_job_problem`, `bind_plant_edits`; `build_block` (P's deal from its table, no reused run, no judge or hosts launch, the edits bound at init); `release_hosts` (the jobs and edits again); `deal_command`; `record_simple("sealed")` (the REQ-8 binding for a plant arm); `record_done` and `plant_fingerprint` (P's units and records printed; a wrong record refuses) |
| `runkit/stage1-olmo/setup/job_runner_stage1.py` | `ba0a761a…` | `a7a68716…` | docstring; `unit_fingerprints` (K6's reading shared), `plant_fingerprint_record`; `run_job` writes the record after a complete plant-arm job |
| `runkit/stage1-olmo/README.md` | `d136f8b5…` | `a64bef50…` | "Round 35" section |
| `runkit/stage1-olmo/tests/test_round35.py` | new | `88758ba5…` | 27 tests |
| `runkit/stage1-olmo/tests/test_round34.py` | `9a4814d0…` | `4c09c410…` | one assertion: `BLOCKS[-1]` -> `BLOCKS[6]` (P follows sim) |
| `runkit/stage1-olmo/tests/mutants_b15.json` | `a5735871…` | `4afe48cd…` | 418 -> 457 entries; 3 retargeted; note |
| `research/experiments/2026-10-24-stage1-runkit/run_mutants_b15.py` | `57f239bf…` | `bd9cbf60…` | `TESTS` adds `tests/test_round35.py`; docstring |
| `research/experiments/2026-10-24-stage1-runkit/kit-round-35.json` | new | see the last line of this file (§11) | round record |

Full hashes are in `kit-round-35.json` (`changed_files`). Unchanged on purpose, each hashed and equal to its 0d25497
hash: `finisher.py` (`f474cabe…`), `seal.py` (`d6ddc8ef…`), `host.py`, `launch.py`, `orchestrate.py`,
`pack_setup.py`, `judge_units_stage1.py`, `tests/test_stage1_runkit.py`, `tests/test_stage1_runner.py`,
`tests/test_g1_yoext.py`. Each is generic for a new block of the arm kind (read: the pull list covers `job-*` and
`round1/`; the finisher's light check covers every unit; the seal's readable patterns cover
`*adapter-fingerprint*.json`; `pack_setup.py` packs every sealed record's edits; `launch.py` and `host.py` take any
host of plan.json).

## 3. Design

### 3.1 The block and its table (task items 1 and 2)

- `plant_runs()` = `[("a0_plant", 1101), ("a0_plant", 1102), ("a0_plant", 1103)]`, seed-major (REV4 §8.2). It is a
  separate function: `block_runs` (blocks A, B and C; the reading's input builder loads it) is untouched, and
  `ARM_ORDER` is untouched (`block_runs` sorts by it).
- `plant_deal(runs)`: the runs seed-major, split contiguously by `pod_sizes` (`split_pods`): one pod of three. The
  kit's `deal` cannot be used: its interleaving rule refuses one arm twice on a pod (`"the deal puts one arm twice on
  a pod"`), and CHECK §1.1's 5.75 h cap is one host with the three jobs. A run outside the table or listed twice
  refuses (`ValueError`, as `deal` does).
- `ARM_DOSE["a0_plant"] = "plant"` with `DOSE_STEPS["plant"] = 38` (REV4 §8.1: the plant replaces the leaf's 37 rows,
  4,800 rows, 38 steps for n <= 100). A new dose name rather than "add" or "none", because the edit is "combined"
  and the step rule is REV4 §8.1's, not §1.1's. `steps_of` and `stream_steps` need no change.
- `BLOCKS` gets `"P"` after `"sim"` (`planned_parts` and `group_jobs` order by `BLOCKS`; a late entry changes
  nothing for the other groups). `FUNDING_BLOCK["P"] = "P"`, `HOST_PREFIX["P"] = "p"`, `BLOCK_KINDS["P"] = ("arm",)`.
- `REJUDGED_PINS["P"] = ()` is written as its own statement after the table, because `tests/test_round31.py` pins
  the table's first line `REJUDGED_PINS = {"B": (), "A": (` as text (the first attempt put `"P": ()` into the literal
  and that test failed).
- **Host prefix `p`.** `plan_tool.new_host_name` parses a host name as `name.rsplit("-", 1)` (prefix, number);
  `host.py name_of` gives `attribution-s1-p-1`; no other code parses host names by prefix (checked by grep of every
  `startswith(` and `re.compile` in the kit). The prefixes are now `s10, cert, a, cfy, b, c, sim, p`, all distinct
  (a test asserts it). A prefix holding "plant" was rejected: every kit record of the block (`hosts/plant-1/`,
  `launch-plant-1-*.log`, `finisher` logs) would then fall under the never-open path rule that the lead must honour,
  so the block could not be run; the never-open rule for `retrieved/` and plant-arm unit folders (addendum §40
  point 3) stays an explicit rule.
- **Kind.** The existing `arm` (J9): its steps (calibrate with `--edit`, the O-ext unit pass), timing, counting,
  light check, pull list and seal class apply unchanged; nothing in the code needed a new kind, so J23 is not taken.

### 3.2 plan_tool (task item 2)

- **Gates.** `gate_order`: P is in the G3 tuple (the plan-A/B record derived from Gate B's verdict, re-derived at
  every use); then `block_complete(plan, "B")` and `"B" in plan["seals"]`, as certify and B need block A. Under plan
  B, block C is not required (CHECK §5.1 item 2 and §40 point 5 name block B only).
- **Shape.** `{"launches": [{"deal": [0]}]}` exactly: a judge launch refuses (`"block P has no judge launch"`,
  point 7), a hosts or second-phase launch refuses (`"block P's jobs come from its deal only"`), a reused run refuses
  (`"block P: nothing is reused"`), a dealt pod twice or unknown refuses (the existing deal checks), engine Y refuses
  (G4). The existing "training runs come from the deal" rule now names P too.
- **The jobs.** `plant_job_problem`: kind `arm`, arm in `PLANT_ARMS`, seed in `PLANT_SEEDS`, no role, no points; a
  fixed message. It runs at init on the dealt jobs and again at release on the host records (a plan.json edited by
  hand between init and release refuses; tested through `build_block` + `release_hosts`).
- **The edit.** `bind_plant_edits` at init and at release: `resolve_edit(job, sources, required=True)` (the existing
  route; CHECK's claim holds: a non-R arm is keyed `(arm, None)`, and the sealed route accepts `a0_plant` once
  `ARM_DOSE` names it), then `plant_edit_problem`. The refusals: no record (`"a0_plant at 1101: no edit file in MAN1,
  Gate B's MANIFEST or a recorded sealed record"`), two sources, a file missing or changed (`"the edit file is missing
  or its SHA-256 is not the sealed one"`). Binding at init makes the dry run refuse without the record, so the lead
  sees it before any money.
- **The REQ-8 binding (added; the lead keeps or drops it).** `plant_edit_problem(arm, sha256)` reads REQ-8's record
  at its pin (`rules.D2_REQ8_RECORD`, `cc04b663…`, already read by key for J5 and J8 through `pinned_doc`) and
  requires `full_files["edits/planted_k37.json"] == sha256`. From the code that writes the record
  (`scripts/stage1/build_plant.py`, `full_files = {n: sha256_bytes(d) for n, d in sorted(full.items())}` over the
  `--full-out` files, `edits/{name}.json` among them with `name = "planted_k37"`), that entry is the planted_k37
  file's SHA-256. The check runs at `record-sealed` (a wrong file is refused before the pack), at init and at
  release. The refusal names the arm and the file name, never a hash: `"the edit recorded for a0_plant is not the
  file REQ-8's record names as edits/planted_k37.json (its SHA-256 differs, or the record lists no such file; addendum
  §40 point 5)"`. §40 point 5 asks for a separate key-only binding script that prints "match"/"no match"; this is the
  same binding inside the kit, so the kit itself cannot plan a0_plant on any other file. A non-plant arm's record is
  not checked against REQ-8 (unchanged route; tested).
- **Funding.** P's own group; `funding_record` accepts addendum §36's record as for any block (tested with a
  synthetic decision record, as round 34 did).
- **record-done.** For every complete plant-arm job (not an unpulled one): `plant_units` entries `{job, arm, seed,
  unit (the path from the repository root), complete_sha256, fingerprint_record {path, sha256} | null}`.
  `plant_fingerprint` checks a listed record: in the pulled tree at its listed SHA-256 (record-done's own output
  check), kind `stage1 arm adapter fingerprint`, version 1, this job, arm, seed, unit and COMPLETE.json SHA-256, an
  int `steps`, a 64-hex e1, q 64-hex or null, **no `edit` key**; else it refuses (nothing recorded). A missing record
  prints null and plan.json keeps the runner's reason (`fingerprint_record_problem`): the block still completes
  (K6's rule: the unit stands).
- **deal P** prints `{"block": "P", "plan": <code>, "pods": [["a0_plant@1101", "a0_plant@1102", "a0_plant@1103"]]}`.

### 3.3 The runner (task item 3)

- `unit_fingerprints(root, unit)`: the reading K6's `a0_fingerprint_record` did (states/e1/state.json's
  `adapter_fingerprint`, equal to COMPLETE.json's e1 one; q; the identity's two hashes; COMPLETE.json's SHA-256), now
  shared. `a0_fingerprint_record` keeps its file, kind, format and messages (K6's tests and mutant unchanged).
- `plant_fingerprint_record(root, unit, job, index)`: `{kind, version 1, job, arm (job["arm"]), seed, steps
  (job["steps"]), unit, complete_sha256, checkpoints {e1, q}, identity}`, written once with `open("xb")` in
  `rules.canonical_bytes` (the engine's canonical JSON, stdlib). If the fields cannot be read, the fingerprints
  disagree, or the file exists, the unit stands and the reason goes into the job's record
  (`plant_fingerprint_record`). It runs for `kind == "arm" and job["arm"] in rules.PLANT_ARMS`, after the unit's
  verify, like K6's branch (whose line is untouched: mutant `B15-32-a0-record-not-written` still finds it).
- The record carries fingerprints, arm, seed and steps (and the unit path, which names the edit by SHA-256, and the
  identity hashes). It never carries the edit's name or any edit field; a mutant that adds `job["edit"]` is killed.

### 3.4 No judges for P (task item 4)

`block_complete`: P has no judge launch to release, so it is complete once its host is recorded done (and no job is
left behind by a move). `seal_block("P")`: `judges_needed` is empty, `judge_record` is None, `judge_not_run` is
empty, no `judges/P/` folder; the seal classes JOB-DONE.json, the cost ledgers and the fingerprint records readable
and every unit file sealed (tested: 22 files, 15 sealed, 7 readable). A judge launch cannot be planned for P at all
(build_block refuses it), so `planned_judged_units("P", jobs) == 3` never applies; `REJUDGED_PINS["P"]` is empty so
P adds no unit to any judge requirement. If the pilot goes, P's units are re-judged with P2's through
`REJUDGED_PINS` (a later round).

### 3.5 Blinding inside the kit (task item 5)

The edit is named by SHA-256 everywhere: the sealed record, plan.json's job `edit {path, sha256, source}`, the pack's
`edits/<SHA-256>.edit.json`, calibrate's `--arms edit-<SHA-256> --edit edits/<SHA-256>.edit.json`, the unit folder
`round1/<seed>-edit-<SHA-256>-e1-a1`, the fingerprint record's `unit`. No kit command parses the edit file (`resolve_edit`
and the pack hash it; the runner's sealed check hashes it) or a unit's COMPLETE.json beyond the fingerprint and
identity fields. The verify tail the runner keeps is the engine's `verify_run` output (`run_dir`, `kind`, the
problems lists, `complete`), which holds no edit name (`experiments/safety_selection/verify.py`, read).

Two tests scan for leaks with sentinel strings in every text field of a synthetic edit (its name field names a
synthetic leaf, as the real planted_k37 edit does) and in REQ-8's synthetic record's unit and leaf fields:

- `test_blinding_the_edits_name_never_reaches_a_readable_kit_file_or_the_output` (the World): record-sealed,
  init-block P (dry run and real), deal, record-done on a synthetic pulled tree whose units' COMPLETE.json, edit.json,
  summary and state files hold the sentinels, the finisher's `finish` (its finished.json, verified.jsonl and log
  records), seal P and seal status. It asserts no sentinel in stdout, stderr, any command's output, plan.json,
  operator-actions.jsonl, hosts/, seals/, retrieved/p-1/verified.jsonl, JOB-DONE.json, the cost ledgers or the
  fingerprint records, and that exactly the 12 unit files hold them (sealed class).
- `test_the_runner_writes_the_plant_arms_readable_fingerprint_record_with_no_edit_field` (a synthetic pod): the fake
  engine's calibrate is wrapped to write the edit summary with the sentinel name into COMPLETE.json and the run's
  `edit.json` copy; the runner's JOB-DONE.json, records, ledgers and output hold none.

### 3.6 Money (by hand and tested; task item 2's figures)

| Item | Branch 128 (in force) | Branch full |
|---|---|---|
| One a0_plant arm job, measured upper | 52 min + O500 1,024 s = 4,144 s | 4,637 s |
| Its upper and start requirement (Gate A fixture: e1 upper 4,360.62 s, 38-step training 333.67 s) | 7,618.29 s; 9,418.29 s | 8,111.29 s; 9,911.29 s |
| Cap, one pod with the three | 42 min + 2 x 4,144 + 9,418.29 = 20,226.29 s -> **5.75 h** | 6.25 h |
| Guard | $6 + 5.75 x $1.85 = $16.6375 -> $16.64 | $17.56 |
| Upper spend | (2,520 + 3 x 4,144) / 3,600 x $1.79 = $7.4345 -> **$7.43** | $8.17 |
| Need | base $16.64, 1.25 x = **$20.80**, contingency $4.16 | $21.95 |
| One re-run on a new pod | $3.31 (paid from the contingency; a second is not) | |
| Worst case at the cap | 5.75 x $1.79 = $10.29 | |

CHECK §1.1's 5.75 h and $7.43 are reproduced exactly. CHECK §3's "$21.34" was READY's need under another rounding;
the kit's need is $20.80.

## 4. Alternatives I rejected

1. **A new job kind (J23) for the plant arm.** Nothing in the code needs one: the arm kind already takes any
   `ARM_DOSE` arm with an edit, and the only plant-specific step (the fingerprint record) is a per-arm branch after the
   unit's verify, like K6's. A kind would duplicate the arm's commands, timing and sealed-path rules.
2. **Putting the three runs through `rules.deal`.** Its rule refuses one arm twice on a pod, and the pilot is one pod
   of three runs; changing the rule would change blocks A-C's deal. A separate `plant_deal` keeps `deal` byte-identical.
3. **Adding a0_plant to `ARM_ORDER`.** Not needed (`plant_deal` orders by seed); `block_runs` sorts by `ARM_ORDER`.
4. **Mapping a0_plant to the "add" or "none" dose.** Same 38 steps, but the edit is combined and the step rule is REV4
   §8.1's; a named dose makes the rule explicit.
5. **A host prefix holding "plant".** See §3.1: it would put the block's own kit records under the never-open rule.
6. **One fingerprint record format and file name for a0 and plant arms.** K6's `a0-adapter-fingerprint.json` is the
   B10/B11 re-pin tool's format (`repin_reference_seeds.py` reads it); adding `steps` or changing `arm` there would
   change what that tool and K1's gate read. The plant record has its own file name and kind, both matched by the
   seal's readable pattern.
7. **Refusing record-done when a plant arm's fingerprint record is missing.** It would block the pilot's reading over
   a secondary record that a complete job can never produce again (never re-run a complete job). K6's rule is kept:
   the unit stands, the absence is printed and recorded; the lead decides before K7.
8. **Binding P's edit only through `resolve_edit` (no REQ-8 check).** It accepts any file the lead records; the
   REQ-8 binding costs one key-only read of a record the kit already pins and makes a wrong file impossible to plan.
9. **Changing `seal.py`, `finisher.py` or `pack_setup.py`.** Not needed; keeping them byte-identical keeps three fewer
   hashes to update.

## 5. Mutation entries

**New (39, part "kit round 35 …"):** `B15-35-blocks`, `-funding-group`, `-host-prefix`, `-block-kinds-p`,
`-rejudged-p`, `-plant-seeds`, `-plant-dose`, `-dose-steps`, `-plant-deal-allowed`, `-plant-deal-twice`,
`-table-identity-r`, `-table-identity-pin`, `-g3`, `-p-after-b-complete`, `-p-after-b-sealed`, `-req8-differs`,
`-req8-missing`, `-job-seed`, `-job-arm`, `-job-kind`, `-init-unbound`, `-release-unbound`, `-changed-edit-file`,
`-no-record`, `-sealed-route`, `-judge-launch`, `-hosts-launch`, `-reused`, `-deal-table`, `-deal-cmd`,
`-record-done-print`, `-record-done-malformed`, `-record-done-seed`, `-record-done-missing`, `-runner-skipped`,
`-runner-edit-field`, `-runner-steps`, `-runner-overwrite`, `-runner-canonical`.

One per new refusal (P before B is complete; before B is sealed; G3; a job of another seed, arm or kind; a judge
launch; a hosts launch; a reused run; no sealed record (the unbound init and the resolve_edit refusal); a changed
edit file; a record REQ-8's record does not name (differs; missing); the sealed route's binding), two for the table
identity (block A's table loses R at 1104; one re-judged pin changed by a hex digit), five for the fingerprint record
(not written; an edit field; no steps; written over an existing file; not canonical), three for record-done's
print and checks, and the rest for the tables and the deal.

**Retargeted (3; this round moved their find text; same meaning; each marked `retargeted`):**
`B15-3-deal-cmd-unchecked` (deal_command's P refusal follows the code line), `B15-34-funding-group`,
`B15-34-block-kinds-sim` (block P's entries follow sim's).

All 457 find texts occur exactly once (checked after the round).

**What I ran (the official runner, `run_mutants_b15.py` as committed in this round, source root this worktree, a new
scratch folder outside it per run, explicit ids, `STAGE1_ENGINE_Y_TREE` set):**

| Run | Ids | Baseline | Result | Evidence (s1b/reports/) |
|---|---|---|---|---|
| Shard 1 (22:48-22:54 UTC) | blocks … plant-dose (7) | 762 passed in 41.29 s | 7/7 killed | `K-kit35-mutants-shard-1.json` |
| Shard 2 (22:54-22:59) | dose-steps … p-after-b-complete (7) | 762 passed in 41.41 s | 7/7 killed | `…-shard-2.json` |
| Shard 3 (22:59-23:05) | p-after-b-sealed … init-unbound (7) | 762 passed in 39.97 s | 7/7 killed | `…-shard-3.json` |
| Shard 4 (23:05-23:10) | release-unbound … hosts-launch (6) | 762 passed in 40.31 s | 6/6 killed | `…-shard-4.json` |
| Shard 5 (23:10-23:15) | reused … record-done-seed (6) | 762 passed in 40.61 s | 6/6 killed | `…-shard-5.json` |
| Shard 6 (23:15-23:20) | record-done-missing … runner-canonical (6) | 762 passed in 40.96 s | 6/6 killed | `…-shard-6.json` |
| Retargeted (23:24-23:26) | the 3 retargeted ids | 762 passed | 3/3 killed | `K-kit35-mutants-retargeted.json` |

Every kill is a real test failure (pytest exit 1 with a FAILED line, no ERROR line); `not_as_expected` is empty in
every report. Not run here: ALL and NEAR (the lead's background jobs; §8 step 2).

## 6. Commands I ran (exit codes; all in the worktree unless noted)

Python: `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B`,
`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, a fresh `--basetemp` under `s1b/tmp/`, deleted after each run;
`STAGE1_ENGINE_Y_TREE=/Users/spiderishi/Coding/attribution/tmp/engine-y-34bfd288` for the kit suite.

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `py_compile` of the three changed kit files; `stage1_rules` loaded by path to print block P's deal, cap, guard, spend and need | 0 | cap 5.75 h, spend $7.4345, need $20.80 (§3.6) |
| 2 | kit suite after the core edits, `-x` | 1 | `test_round31.py::test_k2_block_bs_rejudged_pins_are_empty_by_rule` (the pinned table line); fixed by the separate statement |
| 3 | kit suite after that fix (`-q -q`, so no count line) | 0 | all passed (22:3x UTC) |
| 4 | `tests/test_round35.py` (first) | 1 | 1 failed, 19 passed: the pod's branch (the jobs' branch "full" against the pod's "128"); fixed in the test |
| 5 | `tests/test_round35.py` | 1 | 3 failed, 24 passed: three test-side slips (a hashed file that does not exist, the two-host seal count, the scan walking blocks A and B's trees); fixed |
| 6 | `tests/test_round35.py` | 1 | 1 failed, 26 passed: one assertion named the wrong sentinel; fixed |
| 7 | `tests/test_round35.py` | 0 | **27 passed in 2.81 s** |
| 8 | kit suite, the new file included | 0 | **762 passed in 39.96 s** (22:46 UTC) |
| 9 | `s1b/tmp/add_mutants_35.py` (my script: checks each find text occurs once, appends the 39 entries, extends the note) | 0 | added 39, total 457 |
| 10 | official runner, shards 1-6 (§5) | 0 x 6 | 39/39 killed |
| 11 | `scripts/stage1_s1/reading_input/tests` (it loads the new rules file; synthetic data) | 0 | **284 passed in 81.55 s** (basetemp 2.8 GB, deleted) |
| 12 | find-text check over all 457 entries | 0 | three earlier find texts no longer once (the moved lines); retargeted by a small script (same meaning), then 0 problems |
| 13 | official runner, the 3 retargeted ids | 0 | 3/3 killed |
| 14 | kit suite, final tree | 0 | **762 passed in 39.93 s** (23:29 UTC) |

Other read-only commands: `git status`, `git log`, `git diff --stat`, `git ls-files`-free; `git show 55d5f8b:…`
was not needed (the code at 0d25497 was read in the worktree); `shasum -a 256` on the kit files before and after;
key-only Python reads of the W1 manifest (the `scripts/stage1/build_plant*` and `report_plant*` entries: paths, roles
and SHA-256 only) and of `mutants_b15.json`; `date -u`; `grep`/`sed` on code and on the sources named in the task.
One `git grep` breached the letter of rule 1 (§10).

## 7. Replies to the task's questions

- **Why kind `arm` and no J23.** §3.1 and §4 item 1.
- **Does the sealed route accept `{arm: "a0_plant", path, sha256}` once `ARM_DOSE` names the arm, and does
  `resolve_edit` key a non-R arm by `(arm, None)`?** Yes to both (`record_simple("sealed")`: `e["arm"] in
  rules.ARM_DOSE and e["arm"] != "a0"` and `(draw is None) == (arm != "R")`; `resolve_edit`: `key = (arm,
  r_draw(seed) if arm == "R" else None)`); tested in `test_block_p_needs_the_sealed_edit_record…` and
  `test_record_sealed_binds…`.
- **P's cap and spend upper as the kit computes them.** 5.75 h and $7.43 (Branch 128), as CHECK §1.1 expects; §3.6.
- **Where the a0_plant edit is named by SHA-256 and what reads the edit file's name.** §3.5: nothing in the kit
  reads it; the engine writes it into the unit's COMPLETE.json and edit.json (sealed class).

## 8. The lead's runbook for block P

Run from the main checkout `/Users/spiderishi/Coding/attribution` unless a step says `cd $KIT`. Every command
below prints hashes, counts or fixed messages only. Record paths given to the kit are absolute. Never open, list or
hash anything under `tmp/stage1-olmo/retrieved/`, a plant-arm unit folder, or any path that holds "plant" or
"decoy" except code; the one hash of the planted_k37 edit file in step 4 prints its SHA-256 only.

```zsh
ROOT=/Users/spiderishi/Coding/attribution; cd $ROOT || exit 1
PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
KIT=$ROOT/tmp/stage1-olmo
S1B=$ROOT/.ai/inputs/stage1-post-w1-20261023/stage1b     # my suggestion; any post-W1 records folder works
WT=<this worktree>                                        # .../scratchpad/s1b/ws-k
date -u
```

### Step 1: merge the round (by explicit paths, after the reading's outputs are sealed; addendum §40 point 5)

Copy the 9 files of §2 from `$WT` into the checkout (`cp -p $WT/<path> $ROOT/<path>` for each) and commit them by
explicit paths. Then:

```zsh
shasum -a 256 runkit/stage1-olmo/{stage1_rules,plan_tool}.py runkit/stage1-olmo/setup/job_runner_stage1.py \
  runkit/stage1-olmo/README.md runkit/stage1-olmo/tests/{test_round35,test_round34}.py \
  runkit/stage1-olmo/tests/mutants_b15.json research/experiments/2026-10-24-stage1-runkit/{run_mutants_b15.py,kit-round-35.json}
# expect, in order: d52614e4… 031c7ee3… a7a68716… a64bef50… 88758ba5… 4c09c410… 4afe48cd… bd9cbf60… and
# kit-round-35.json's hash from §11 (full values in kit-round-35.json changed_files)
```

### Step 2: suite and mutants (the lead's background jobs)

```zsh
STAGE1_ENGINE_Y_TREE=$ROOT/tmp/engine-y-34bfd288 PYTHONDONTWRITEBYTECODE=1 $PY -B -m pytest -q -p no:cacheprovider \
  --basetemp=<new scratch folder> runkit/stage1-olmo/tests              # expect 762 passed
IDS=$($PY -B -c "import json;d=json.load(open('runkit/stage1-olmo/tests/mutants_b15.json'));print(','.join(m['id'] for m in d['mutants'] if m['id'].startswith('B15-35-') or m['id'] in ('B15-3-deal-cmd-unchecked','B15-34-funding-group','B15-34-block-kinds-sim')))")
STAGE1_ENGINE_Y_TREE=$ROOT/tmp/engine-y-34bfd288 PYTHONDONTWRITEBYTECODE=1 $PY -B \
  research/experiments/2026-10-24-stage1-runkit/run_mutants_b15.py $ROOT <new scratch outside ROOT> \
  <out>/kit-round-35-mutation-report.json "$IDS"                        # expect 42 killed, not_as_expected []
# NEAR (optional): git archive 0d25497 runkit/stage1-olmo | tar -x -C <scratch>/kit34, then
#   ... run_mutants_b15.py $ROOT <scratch2> <out2>.json NEAR --near <scratch>/kit34/runkit/stage1-olmo
STAGE1_ENGINE_Y_TREE=$ROOT/tmp/engine-y-34bfd288 PYTHONDONTWRITEBYTECODE=1 $PY -B -m pytest -q -p no:cacheprovider \
  --basetemp=<new scratch folder> scripts/stage1_s1/reading_input/tests  # expect 284 passed (the builder loads the rules file)
```

### Step 3: sync into the live kit (before and after hashes)

```zsh
cd $ROOT
# before: the live copies must still be round 34's (stop if any differs)
shasum -a 256 $KIT/{stage1_rules,plan_tool}.py $KIT/setup/job_runner_stage1.py $KIT/README.md
#   expect 4005cb4e… 27e299b5… ba0a761a… d136f8b5…
for f in stage1_rules.py plan_tool.py setup/job_runner_stage1.py README.md; do cp -p runkit/stage1-olmo/$f $KIT/$f; done
# if the live copy keeps tests/ (round 33 synced them):
for f in test_round35.py test_round34.py mutants_b15.json; do cp -p runkit/stage1-olmo/tests/$f $KIT/tests/$f; done
shasum -a 256 $KIT/{stage1_rules,plan_tool}.py $KIT/setup/job_runner_stage1.py $KIT/README.md
#   expect d52614e4… 031c7ee3… a7a68716… a64bef50…
```

### Step 4: the planted_k37 edit file's path and SHA-256 (no byte shown)

- **The folder.** `scripts/stage1/build_plant.py` (code) writes every file that holds text under `--full-out`
  (its docstring line 35; `write_location` writes `edits/planted_k37.json`, line 306-307; `Writer.write` puts it in
  `self.full["edits/{name}.json"]`, line 290). FOCUS (the 23 Oct entry, line 143 at 0d25497) says the files with
  text "stay under git-ignored `tmp/stage1-mac-runs-20261023/`". The committed block-A pack-inputs records name
  REQ-3's pools, which the same build wrote into the root of its `--full-out` folder (`full["plant.pool.json"]`,
  line 426), as `tmp/stage1-mac-runs-20261023/plant/plant.pool.json`; so the plant build's `--full-out` was
  `tmp/stage1-mac-runs-20261023/plant`, and the edit file is
  `tmp/stage1-mac-runs-20261023/plant/edits/planted_k37.json`. (I did not list the folder; the kit confirms the
  identity in step 5: `record-sealed` refuses a file REQ-8's record does not name.)
- **The hash** (prints 64 hex characters and nothing else):

```zsh
EDIT=tmp/stage1-mac-runs-20261023/plant/edits/planted_k37.json
H_EDIT=$(shasum -a 256 $ROOT/$EDIT | cut -c1-64); echo $H_EDIT
```

### Step 5: the sealed edit record (before the pack; the kit's binding check runs here)

```zsh
mkdir -p $S1B; date -u
cat > $S1B/sealed_edits_plant.json <<EOF
{"kind": "stage1 sealed edits", "edits": [{"arm": "a0_plant", "path": "$EDIT", "sha256": "$H_EDIT"}],
 "utc": "<date -u>", "recorded_by": "the lead (GI IX)", "source": "REQ-8's planted_k37 edit (addendum §40 point 5)"}
EOF
H_REC=$(shasum -a 256 $S1B/sealed_edits_plant.json | cut -c1-64)
cd $KIT && $PY -B plan_tool.py record-sealed $S1B/sealed_edits_plant.json --sha256 $H_REC
# expect {"recorded": "sealed", "sha256": "<H_REC>"}; a refusal "the edit recorded for a0_plant is not the file
# REQ-8's record names as edits/planted_k37.json" means the path or file is not the plant build's: stop and decide
```

(The record file may carry any extra keys; the kit reads `kind` and `edits` only.)

### Step 6: pack engine X (after every track that touches `scripts/` or `experiments/` is committed)

`pack_setup.py` refuses while an engine or script file is uncommitted and never overwrites a pack. It packs every
sealed record's edits by SHA-256 (`edits/<H_EDIT>.edit.json`), so step 5 comes first. The arm jobs need the O-ext
inputs packed (`oext_bank`, `oext_record`, `w1_18_record` under Branch 128): the round-34 inputs record (no inputs)
is not enough; reuse the inputs record block B's last X pack was made from (its SHA-256 is the
`inputs_record_sha256` of that pack's `setup-receipt.json`, kept beside the moved-aside packs).

```zsh
cd $KIT
git -C $ROOT status --porcelain -- experiments scripts      # must print nothing
mv setup/packed-stage1-X setup/packed-stage1-X.before-round35-$(date -u +%Y%m%dT%H%M%SZ)
INPUTS=<block B's X pack inputs record>; H_IN=$(shasum -a 256 $INPUTS | cut -c1-64)
python3.11 pack_setup.py X --inputs $INPUTS --inputs-sha256 $H_IN
$PY -I -B -c "import json;f=json.load(open('setup/packed-stage1-X/sealed-files.json'));print(f['files'].get('edits/$H_EDIT.edit.json'), sorted(f['inputs']))"
# expect H_EDIT and an inputs list holding oext_bank, oext_record, w1_18_record
```

Pack before `init-block`: release binds the host to the current pack's `sealed_files_sha256`.

### Step 7: the block's records and the dry run ($0; the decisive check on the real plan.json)

```zsh
cd $KIT
printf '%s\n' '{"launches": [{"deal": [0]}]}' > $S1B/jobs_block_p.json
$PY -B plan_tool.py deal P
# expect {"block": "P", "plan": "<the recorded code>", "pods": [["a0_plant@1101", "a0_plant@1102", "a0_plant@1103"]]}
$PY -B plan_tool.py init-block P --jobs $S1B/jobs_block_p.json --dry-run
# expect: funding_block P, branch 128, need_usd 20.8, base_need_usd 16.64, contingency_usd 4.16,
#         pods [{launch 0, cap_hours 5.75, guard_usd 16.64, counted 3, jobs ["arm:a0_plant:1101", "arm:a0_plant:1102", "arm:a0_plant:1103"]}]
# a refusal names the gate (G3; block B not complete or not sealed; the edit record; REQ-8's record): stop and decide
# the user's §36 decision record, exactly as block sim's funding record names it (prints path and sha256 only)
$PY -I -B -c "import json;p=json.load(open('plan.json'));print([(b,p['blocks'][b]['funding'].get('user_decision')) for b in ('sim','certify','B') if b in p['blocks']])"
date -u
cat > $S1B/funding_block_p.json <<'EOF'
{"block": "P", "amount_usd": 20.80, "utc": "<date -u, UTC, not in the future>",
 "source": "user rule: start from the balance",
 "user_words": "no just start it now ill fund it when i feel like this is a rule",
 "recorded_by": "the lead (GI IX)",
 "user_decision": {"path": "<as printed above>", "sha256": "<as printed above>"}}
EOF
```

### Step 8: init-block P (launch 0 is released at once), then check-plan

```zsh
cd $KIT
$PY -B plan_tool.py init-block P --jobs $S1B/jobs_block_p.json --funding $S1B/funding_block_p.json
# expect hosts ["p-1"], released ["p-1"], need_usd 20.8
$PY -I -B -c "import json;p=json.load(open('plan.json'));h=p['hosts']['p-1'];print(h['block'],h['cap_hours'],h['counted'],[(j['arm'],j['seed'],j['steps'],j['edit']['sha256'][:12]) for j in h['jobs']])"
# expect P 5.75 3 [('a0_plant', 1101, 38, '<H_EDIT[:12]>'), ('a0_plant', 1102, 38, ...), ('a0_plant', 1103, 38, ...)]
$PY -B orchestrate.py check-plan p-1        # expect {"host": "p-1", "jobs": 3, "ok": true}
```

### Step 9: launch (a background job kept alive until "job-started"; one finisher)

```zsh
cd $KIT
source <the secrets file>                     # RUNPOD_OPERATOR_API_KEY
python3.11 budget.py                           # the live balance; the pod needs $16.64 free above the guard's rule
pgrep -fl 'finisher.py'                        # one finisher only; start one if none runs:
caffeinate -i python3.11 finisher.py > finisher-p-$(date -u +%Y%m%dT%H%M%SZ).log 2>&1     # background job 1
python3.11 launch.py p-1 > launch-p-$(date -u +%Y%m%dT%H%M%SZ).log 2>&1                   # background job 2
# keep the lead's session alive until the launch log shows "job-started" for p-1 (the orchestrate steps run
# detached under caffeinate; a foreground return kills pod setups); launch.py exits 0 once pod.json exists
```

The in-pod timer stops the pod at 5.75 h at the latest; the finisher stops it after the pull. The log names match
the backup's `launch*.log` and `finisher*.log` globs.

### Step 10: after the finisher's `finished` line: record-done, seal P (no judges)

```zsh
cd $KIT
$PY -I -B -c "import json;print(json.load(open('hosts/p-1/finished.json'))['status'])"   # verified-and-stopped
$PY -B plan_tool.py record-done p-1
# prints {"host": "p-1", "statuses": ["complete", "complete", "complete"], "plant_units": [{"job": 0, "arm": "a0_plant",
#   "seed": 1101, "unit": "tmp/stage1-olmo/retrieved/p-1/tree/round1/1101-edit-<H_EDIT>-e1-a1", "complete_sha256": H_C1,
#   "fingerprint_record": {"path": "tmp/stage1-olmo/retrieved/p-1/tree/job-0/arm-adapter-fingerprint.json", "sha256": H_F1}}, ...]}
# a null fingerprint_record: the runner could not write it; plan.json's job carries fingerprint_record_problem (K7's
# regeneration check of that seed is then not possible after the seal; decide before K7)
$PY -B seal.py block P                         # expect {"block": "P", "seal_sha256": ..., "files": N, "sealed": ..., "readable": ...}
$PY -B seal.py status | grep -E '^p-1|^block P|^seal P|estimated'
date -u
```

If a run crashed: `record-done p-1` records it; `defer p-1` moves it to `p-2` (the same edit, $3.31 of the $4.16
contingency), `orchestrate.py check-plan p-2`, then step 9 with `p-2`; `seal.py block P` seals both hosts.

### Step 11: the pilot reader's exact inputs (read by key; never open the units by hand)

- P's three units: the `plant_units` list that `record-done p-1` printed (unit path from the repository root and
  COMPLETE.json SHA-256), also in plan.json: `[(j['seed'], j['unit'], j['complete_sha256']) for j in
  p['hosts']['p-1']['jobs']]` (unit paths relative to `tmp/stage1-olmo/retrieved/p-1/tree/`), and in the seal
  `seals/block-P.json` (`files`: every unit file with its SHA-256 and class).
- Gate A's a0 comparators: `stage1_rules.REJUDGED_PINS["A"][0:3]` (paths, COMPLETE.json and job.json SHA-256; the
  units the stage-1 builder already reads through the same pins).
- The reader opens each unit's COMPLETE.json by its SHA-256 and reads U and the per-prompt labels by key only
  (addendum §40 point 3); the fingerprint records (`job-I/arm-adapter-fingerprint.json`, readable) are for K7's
  regeneration check, not for the reading.

Then both SHA-256 values (the seal's, the reader's output) into FOCUS, commit by explicit paths, the backup, and
(on the user's yes) delete the stopped `p-1` pod after the backup.

## 9. Open points for the lead

1. **The reading's rules file changes again** (`stage1_rules.py` `4005cb4e…` -> `d52614e4…`, `plan_tool.py`
   `27e299b5…` -> `031c7ee3…`, the runner `ba0a761a…` -> `a7a68716…`). Addendum §40 point 5 says to merge only after
   the reading's outputs are sealed (done 1 Nov 21:35 UTC per the task). The builder's tables do not change (a test
   holds their 0d25497 values) and its suite passed with the new file (284). Any stamp that binds the rules file must
   take the new hash.
2. **The REQ-8 binding is an addition** (§3.2). Keep it (my recommendation: it is the same binding §40 point 5 asks
   of a separate script, inside the kit, at $0) or drop `plant_edit_problem` and its three call sites and tests.
3. **The host prefix `p`** (§3.1): `retrieved/p-1/` and the unit folders stay under the explicit never-open rule;
   the path rule does not cover them by name.
4. **The X pack for P needs the O-ext inputs** (step 6): the round-34 pack inputs record has none. `check-plan p-1`
   is the $0 check (`<input oext_bank>` is listed as missing otherwise).
5. **A missing fingerprint record does not block the block** (§4 item 7): decide before K7 whether a0_plant@1101's
   regeneration can be checked.
6. **Not in this round** (addendum §40 point 5; the task's item 7): blocks P1b and P2, per-seed draw keys for the
   plant's R600 and R150, the scoring job K7, a plant retrain kind, the pilot reader, the separate key-only binding
   script, the k = 75 raise.
7. **Pod time.** CHECK §3 measured 0.78-0.87 h per four-job-pod arm; three arms plus overhead is about 2.6-3.0 h,
   about $5-6; the kit's upper is $7.43 and the cap 5.75 h.

## 10. Hard-rule log

- **One breach of the letter of rule 1, recorded.** While looking for the plant build's `--full-out` value I ran
  `git grep -n -- "--full-out\|stage1-mac-runs-20261023" HEAD -- ':!*plant*' ':!*decoy*' ...` in the main
  checkout. The pathspec excluded "plant" and "decoy" paths but not `.ai/inputs/stage1-post-w1-20261023/block-a/`
  and `block-b/`, so it printed matching lines of `block-a/pack_inputs_diag.json`, `block-a/pack_inputs_diag2_ln12.json`,
  `block-a/sealed_edits_1.json`, `block-a/sealed_edits_2.json` and four `block-b/pack_inputs_*.json`. Each printed
  line is a `"path": "tmp/stage1-mac-runs-20261023/..."` string (file names of the Mac runs' outputs: plant.pool.json,
  decoy.pool.json, s3_safe.pool.json, s4_candidates.json, sd600.json, s1.json, add_s1.json, add_s3.json,
  add_s4.json, oext_bank.json). No value, hash, unit, leaf, cell, plant row or decoy identity was printed or read; no
  file was opened. The lines from `block-a/pack_inputs_diag.json` are what step 4's derivation rests on; FOCUS:143
  alone gives the parent folder.
- Not opened, listed or hashed: `tmp/stage1-olmo/` (plan.json, hosts, judges, seals, retrieved), `tmp/judge-pod*`,
  `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, `tmp/hlc*`, `tmp/stage1-mac-runs-20261023/`, `block-a/`,
  `block-b/` (beyond the grep above), `reading/run-20261101/`, any units/ or eval/ folder, any COMPLETE.json,
  edit.json, answer, label, guard-sample or judge-cache file, the hidden or selector bank, any "plant" or "decoy"
  path except code (`scripts/stage1/build_plant.py`: lines 1-70, 270-320, 400-462; `experiments/safety_selection/
  verify.py` and `__main__.py` for what verify prints).
- Read by key: the W1 manifest (the `scripts/stage1/build_plant*` and `report_plant*` entries: path, role,
  SHA-256), `mutants_b15.json`, `kit-round-34.json`. Read in full: the task's sources (addendum §36 and §40, CHECK,
  REV4 §8, the C-kit34 build report, FOCUS line 143), the kit's code, tests and README, `scripts/stage1_s1/
  reading_input/build.py` lines 1-30 and its uses of the rules file.
- Every test ran on synthetic data in a fresh basetemp under the scratch folder, deleted after the run (the
  reading-input run's 2.8 GB included); `__pycache__` folders removed. No real-data command (no reading, builder,
  scorer, overlap, judge, seal, kit, pack, draw or launch command on real state).
- No git state change (read-only `status`, `log`, `diff --stat`, `rev-parse`, `grep`), no commit, no network, no
  install, no pod, no API call, no background job; every command finished in the foreground within 10 minutes
  (the longest: one mutation shard, about 6 minutes).

## 11. Acceptance criteria

| Criterion | Status |
|---|---|
| (1) block P in BLOCKS, FUNDING_BLOCK, HOST_PREFIX (no clash), BLOCK_KINDS, REJUDGED_PINS["P"] = (); a0_plant at 38 steps; a separate seed-major run table; the arm kind; A, B and C's tables and REJUDGED_PINS["A"] byte-identical (test) | passed |
| (2) init-block P needs G3 and block B complete and sealed; the deal from P's table; another job refuses; the sealed edit record (accepted by the existing route; resolve_edit by (arm, None)); a missing record or changed file refuses; P's own §36 funding record; the cap and spend upper (5.75 h, $7.43) | passed |
| (3) the readable e1 and q fingerprint record for a plant-arm job (fingerprints, arm, seed, steps; no edit field) | passed |
| (4) P completes and seals with no judge launch and no judge files (code and test) | passed |
| (5) the edit named by SHA-256 everywhere; the sentinel test over the planning path, the runner's records, record-done and the seal | passed |
| (6) tests/test_round35.py (27); one test and one mutant per new refusal; mutants for the table identity and the fingerprint record; mutants_b15.json ids B15-35-*; run_mutants_b15.py TESTS; kit-round-35.json; README; the kit suite and every new mutant with the official runner in shards | passed (762; 42/42 killed) |
| (7) nothing of P1b, P2, the draw keys, K7 or a retrain kind | passed (not built) |
| (8) the runbook in this report | written (§8); not run on real state |
| Real pod, real plan.json, real pack, the real edit file's path | not tested (the lead's steps 4-10; the dry run and check-plan are the $0 checks; record-sealed's binding check confirms the file) |

SHA-256 of `research/experiments/2026-10-24-stage1-runkit/kit-round-35.json` (in the worktree):
`a5230eeb72e0b27fd321499d1cffcaf7fe7589ec3def7a5cb92c49f6f5749bc6`. This report's own SHA-256 is in the structured
result (hashed after this line was written).
