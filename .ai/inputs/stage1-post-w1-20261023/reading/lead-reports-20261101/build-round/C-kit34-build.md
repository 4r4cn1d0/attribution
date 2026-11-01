# C-kit34: kit round 34, B14's similarity pass as a kit job (build report)

Written by the track C-kit34 builder for the lead (GI VIII), 1 Nov 2026, finished about 08:10 UTC (clock read with
`date -u` at 08:09:28 UTC). Model identity is the launcher's record, not this text.

Worktree: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/ws-c`
(detached at 55d5f8b). Nothing is committed, synced or launched. The round report is
`research/experiments/2026-10-24-stage1-runkit/kit-round-34.json` in that worktree (`ed52022b…`).

## 1. Result in short

- **New job kind J22, `similarity`.** It runs `scripts/stage1_s1/overlap_similarity.py` (B14) once on theta0.
  Engine X only. Recipe REC only. Unit-free. Counted 0.
- **New block `sim`.** One launch, one pod (`sim-1`), the pass alone. Own funding group `sim`. The §36
  start-from-the-balance funding record is accepted.
- **Inputs by SHA-256.** Script `f8305c71…` and settings `27db4c3f…` (new `S1_CODE` pins). Prepared manifest
  `9ed61826…`. Dev bank `1438ff51…`. Add sets S1 `904a0cf1…`, S3 `a2f18a3d…`, S4 `24aed3fb…`.
- **What the pod returns.** `job-0/similarity/similarity.json` (B14's output) and `job-0/similarity-record.json`
  (the runner's text-free record).
- **Checks on the Mac.** The finisher's light check and `record-done` check both files against the pins.
  `record-done` prints the path and SHA-256 that the strata step needs.
- **Money.** Cap 1.5 h. Guard $8.78. Need **$10.98** (base $8.78, contingency $2.20). Expected (E) $0.60–0.90.
- **Tests.** Kit suite 671 → **735 passed**. Reading-input suite with the new rules file: 195 passed.
- **Mutants.** 36 new near mutants; all 36 killed in a narrowed pre-check. 3 retargeted mutants killed by the
  official runner. The full official run is the lead's background job.

## 2. Files changed (all in the worktree)

| File | Old SHA-256 | New SHA-256 | What changed |
|---|---|---|---|
| `runkit/stage1-olmo/stage1_rules.py` | `bde78fab…` | `4005cb4e…` | J22 in `KINDS`/`KIND_IDS`, `UNMEASURED_KINDS`, `UNITLESS_KINDS`; `SIM_S` = 600 s and its upper (1.5 x); block `sim` in `BLOCKS`, `FUNDING_BLOCK`, `HOST_PREFIX`, `BLOCK_KINDS`; B14's two `S1_CODE` pins; `SIM_*` pins; shared checks `similarity_problems`, `similarity_record_doc`, `similarity_record_problem`, `canonical_bytes`, `hex64` |
| `runkit/stage1-olmo/plan_tool.py` | `f18bb834…` | `27e299b5…` | `similarity_entry` (inputs by SHA-256; add sets bound like edits and checked against the trained S-arm runs); block-`sim` shape check; engine X and recipe REC (`RECORDED_RECIPE`) and no arm/seed for the kind; re-check at release; `record-done` checks the output and prints it |
| `runkit/stage1-olmo/setup/job_runner_stage1.py` | `37e8e81a…` | `ba0a761a…` | the command; `similarity_pins`/`similarity_args` (plan pins against the pack); sealed paths; the record writer `similarity_record`; ledger stage `scoring` |
| `runkit/stage1-olmo/finisher.py` | `5d24290f…` | `f474cabe…` | `similarity_check` in the light check |
| `runkit/stage1-olmo/README.md` | `11677460…` | `d136f8b5…` | "Round 34" section |
| `runkit/stage1-olmo/tests/test_round34.py` | new | `9a4814d0…` | 63 tests |
| `runkit/stage1-olmo/tests/test_stage1_runkit.py` | `f48e3bdb…` | `64e5f179…` | J22 in the per-kind table; `S1_CODE` has 13 entries; `FINISHER_34` |
| `runkit/stage1-olmo/tests/test_stage1_runner.py` | `691e5201…` | `659714b2…` | Pod fixture (B14's synthetic inputs, `sim_entry`, fake output); J22 in `all_hosts` and the dry-run table; `SCRIPT_MODULE`, `recipe_pins`; the sim pod in the pull test |
| `runkit/stage1-olmo/tests/test_g1_yoext.py` | `508975d9…` | `909d7dad…` | `S1_CODE` has 13 entries |
| `runkit/stage1-olmo/tests/mutants_b15.json` | `508c7fa5…` | `a5735871…` | 382 → 418 entries; 3 retargeted; note |
| `research/experiments/2026-10-24-stage1-runkit/run_mutants_b15.py` | `46164513…` | `57f239bf…` | `TESTS` adds `tests/test_round34.py` |
| `research/experiments/2026-10-24-stage1-runkit/kit-round-34.json` | new | `ed52022b…` | round report |

Full hashes are in `kit-round-34.json` (`changed_files`). Unchanged on purpose: `seal.py`, `host.py`,
`launch.py`, `orchestrate.py`, `pack_setup.py`, `budget.py`, `backup_records_stage1.py`,
`judge_units_stage1.py`, `status.py`. Each is generic for a new block and a unit-free kind (checked by reading
the code and by tests).

## 3. Design

### 3.1 The job and its block

- **Kind J22** (`stage1_rules.KIND_IDS`; J19 is the judge launch, J20/J21 LN-15e).
- **Timing.** Measured upper `SIM_S` = 600 s (E: five times the design report's "about 1–2 min"; marked
  unmeasured). Upper = `DIAG_UPPER_FACTOR` x 600 = 900 s (the kit's wide-cap rule for untimed passes). Start
  requirement 900 + 1,800 = 2,700 s.
- **Block `sim`.** Exactly `{"launches": [{"hosts": [[{"kind": "similarity"}]]}]}`. Any other shape refuses
  (two jobs, two pods, two launches, a judge launch, a deal). A similarity job in any other block refuses
  (`BLOCK_KINDS`). Blocks A and B are sealed, so the pass cannot join them.
- **Gates that apply unchanged.** G3 (Gate B's final record; the plan-A/B record re-derived), G1 (S1-0 exists),
  the $10/h create limit, the budget guard (or the recorded guard-off decision), the in-pod cap timer, the
  environment comparison with Gate B's reference, the per-job gate, stop-never-delete, the re-run rule.

### 3.2 Money (by hand, and tested)

| Item | Value |
|---|---|
| Cap | 42 min + 2,700 s = 5,220 s, up to 0.25 h → **1.5 h** |
| Guard | $6 + 1.5 x $1.85 = $8.775 |
| Upper spend | (2,520 + 600) / 3,600 x $1.79 = **$1.5513** |
| Need | base $8.78 (8.775 half up), 1.25 x → **$10.98**; contingency **$2.20** |
| One re-run on a new pod | $1.5513 (paid; a second is not) |
| Worst case at the cap | 1.5 h x $1.79 = $2.69 |
| Expected (E) | 20–30 min, $0.60–0.90 (W1-18's one-job pod: 23 min, $0.69) |

The live balance was $29.94 at 31 Oct 22:13 UTC (FOCUS); idle charge about $0.04–0.05/h. The pod fits above the
$10 alert line.

### 3.3 Inputs by SHA-256 (`plan_tool.similarity_entry`)

Derived at init-block and again at release (a changed entry refuses at release). The job record carries:

- `script`, `settings`: B14's files at their new `S1_CODE` pins. The X pack carries `S1_CODE` itself, so no
  `code` entry is needed. Both pins equal this repository's files and the bytes at `S1_COMMIT` 3ea5ae1 and at the
  S1 merge 3417f12 (checked with `git show … | shasum`).
- `manifest_sha256`: `PREPARED_MANIFESTS` (`9ed61826…`).
- `dev_bank`: `SIM_DEV_BANK` (`banks/dev.jsonl`, `1438ff51…`). Source: the prepared manifest's own entry (I read
  that one entry; I did not open any bank).
- `add_sets`: `SIM_ADD_SETS`. Each pin equals the SHA-256 that its add-edit record names
  (`.ai/inputs/stage1-commitments-20261016/add-s{1,3,4}/add_edit_record.json`, read by key). Each add set must
  also be:
  - one file for its arm in the kit's edit sources (MAN1, Gate B's MANIFEST, the recorded sealed records);
  - on disk at the pin;
  - the file the arm trained on: every S1/S3/S4 arm run in plan.json that names an edit names this one, and at
    least one such run is complete.

The last check is the $0 decisive check on the real state: `init-block sim --dry-run` refuses if the pins differ
from what the arms trained on.

### 3.4 On the pod (`job_runner_stage1.py`)

One step, receipt `job-0-similarity`:

```
venv/bin/python scripts/stage1_s1/overlap_similarity.py --prepared data/kt-prepared/prepared-kt-dolly-olmo2 \
  --recipe experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json \
  --add-set S1 edits/904a0cf1….edit.json 904a0cf1… --add-set S3 edits/a2f18a3d….edit.json a2f18a3d… \
  --add-set S4 edits/24aed3fb….edit.json 24aed3fb… --out job-0/similarity
```

The runner's environment sets `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `CUDA_VISIBLE_DEVICES=0`,
`TOKENIZERS_PARALLELISM=false`, `HF_HUB_OFFLINE=1`, `PYTHONPATH`, and removes token variables (unchanged).

Before the step (nothing runs otherwise):
1. `similarity_args`: the plan's entry names the script, settings and dev bank at the kit's paths and exactly
   the add sets S1, S3, S4, each pin a SHA-256; every file it names is packed at that pin.
2. The sealed-file check (`sealed_paths`) covers the script, its settings, `s1common.py`, `limits_common.py`,
   `labels.json` (the registry its settings check reads), the manifest, the dev bank and the three edit files.

After the step (`similarity_record`), the runner writes `job-0/similarity-record.json` once (exclusive create,
canonical JSON):
- `output` {path, sha256} (hashed by the runner);
- `printed_sha256`: the SHA-256 the script printed (`wrote similarity.json into job-0/similarity (H)` in
  `job-0-similarity/process.log`);
- `script_sha256`, `settings_sha256`, `inputs` (the provenance's hashes only; a non-hash value becomes null);
- `counts` (prompts, rows per add set);
- `problems`: every field off `stage1_rules`' pins (including REC's config SHA-256 from plan.json's recipes) and
  a printed SHA-256 that is missing or differs.

A record with a problem makes the job a crash; the record says why. The ledger puts the step under `scoring`.
No similarity value is read: only kind, version, provenance hashes and counts.

### 3.5 On the Mac

- **Pull:** unchanged. `job-0/…`, `job-0-similarity/…`, `job-done/`, `JOB-DONE.json` are all under `job-*` and
  existing items (tested by running the sim pod).
- **Light check:** `finisher.similarity_check` runs `stage1_rules.similarity_record_problem` on every complete
  similarity job: both files in the pulled tree at the SHA-256 that JOB-DONE.json lists, not symbolic links; the
  record equals the record rebuilt from the pulled similarity.json; no problem. A failure gives
  `review-needed-stopped`. The pod is stopped in every case (unchanged).
- **record-done:** the same check (refuses, nothing recorded); then prints
  `similarity: [{job, path, sha256, record_sha256}]`.
- **Re-run:** a crashed pass goes through `defer sim-1` → `sim-2`, paid from the `sim` contingency (tested).
- **Seal:** not needed (no outcome). `seal.py block sim` would work but would class similarity.json "sealed"
  by name only.

## 4. Alternatives I rejected

1. **One-off pod (route ii)** and **the Mac (route iii)**: rejected by the design report and the lead's ruling
   (lost safeguards; the loaders refuse non-CUDA; weights absent).
2. **Add the pass to block A or B:** both are sealed; `gate_order` refuses a second plan of a block, and a new
   host would change a sealed block after its seal.
3. **A separate kit copy (`tmp/stage1-olmo-sim`)** to keep `stage1_rules.py` unchanged for the reading: against
   the task (sync into `tmp/stage1-olmo`); duplicates plan.json's G3 records; more operator steps. Its only gain
   is small: the reading's tables do not change, and its suite passes with the new file (§6).
4. **Pins in a new dict instead of `S1_CODE`:** needs a `pack_setup.py` change and breaks the kit rule that
   every S1 file the runner uses is an `S1_CODE`/`D2_CODE` pin (`test_every_s1_package_file_the_runner_uses_is_pinned`).
5. **The runner compares packed files with `stage1_rules`' pins directly:** the kit's pattern (D-2, C3) checks the
   pod against plan.json's pins, which plan_tool derives from the rules. The rules' pins are enforced on the
   output by the record (pod) and again by the finisher and record-done. A hand-edited plan.json therefore
   cannot give a complete job. (The subprocess dry-run tests also cannot patch the rules module.)
6. **Upper 0.5 h like W1-18** (cap 1.75 h, need $11.55): wider than the estimate needs. With 1.5 h the runner's
   gate still holds after the full 42-min overhead (2,880 s left ≥ 2,700 s).
7. **A G5-like order gate** (blocks A and B sealed before `sim`): no source sets an order. I check content
   instead: the add sets must be the files the arms trained on.
8. **Change `seal.py` READABLE_PATTERNS:** not needed; keeping `seal.py` byte-identical keeps one fewer hash to
   update in the reading runbook and the second stamp.

## 5. Mutation entries

**New (36, part "kit round 34 …"):** `B15-34-kind-id`, `-upper-factor`, `-measured`, `-unmeasured`, `-unitless`,
`-funding-group`, `-block-kinds-sim`, `-block-kinds-a`, `-problems-code`, `-problems-inputs`,
`-problems-input-none`, `-problems-prompts`, `-problems-rows`, `-printed`, `-record-equal`, `-record-symlink`,
`-runner-entry`, `-runner-stale`, `-runner-sealed-paths`, `-runner-record-crash`, `-runner-record-exclusive`,
`-runner-recipe`, `-runner-stage`, `-shape`, `-engine`, `-recipe`, `-no-arm`, `-entry-pin`, `-entry-disk`,
`-entry-trained`, `-entry-complete`, `-build-entry`, `-release-check`, `-record-done-check`,
`-record-done-print`, `-light-check`.

**Retargeted (3; this round moved their find text; same meaning; each marked `retargeted`):**
`B15-r-o-only-unit`, `B15-8-runner-settings-unpinned`, `B15-g-no-recorded-recipe`.

All 418 find texts occur exactly once (checked after the round).

**What I ran:**

| Run | How | Baseline | Result | Evidence |
|---|---|---|---|---|
| Pre-check 1 | the kit's runner loaded by path, unchanged except `TESTS` narrowed to `tests/test_round34.py` (scratch wrapper `builds/tmp/ckit34_precheck.py`) | 63 passed | 18/18 killed | `builds/reports/C-kit34-mutants-precheck-1.json` |
| Pre-check 2 | same | 63 passed | 18/18 killed | `builds/reports/C-kit34-mutants-precheck-2.json` |
| Retargeted | the round's runner, all eight test files | 735 passed in 115.07 s | 3/3 killed | `builds/reports/C-kit34-mutants-retargeted.json` |

The pre-check is **not** the spec run: it narrows the test list. The official run of the 36 new ids (and NEAR) is
the lead's background job (commands in §7, step 2).

## 6. Commands I ran (exit codes; all in the worktree unless noted)

Python: `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B`,
`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, a fresh `--basetemp` under `builds/tmp/`, deleted after
each run. `STAGE1_ENGINE_Y_TREE=/Users/spiderishi/Coding/attribution/tmp/engine-y-34bfd288` for the kit suite.

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | kit suite, before any change | 0 | 671 passed in 40.45 s |
| 2 | kit suite after the core edits | 1 | 4 failed, 667 passed (expected: two pinned `S1_CODE` counts, the per-kind table, the finisher's documented-changes test); fixed in the tests |
| 3 | kit suite after the test updates | 0 | 672 passed (160 s; load average about 11 from other tracks) |
| 4 | `test_stage1_runner.py` with durations | 0 | 187 passed in 23.13 s |
| 5 | `test_round34.py` (first) | 1 | 3 failed, 56 passed (a dotted-key helper; the mid-host sealed check needs the preflight patched as the kit's own tests do); fixed |
| 6 | `test_round34.py` | 0 | 63 passed (twice) |
| 7 | kit suite | 0 | 735 passed in 119.52 s |
| 8 | mutation pre-check, two batches | 0, 0 | 36/36 killed |
| 9 | official runner, 3 retargeted ids | 0 | 3/3 killed; baseline 735 passed |
| 10 | `reading_input` tests: oext_settings, items, hb, hb_claim | 0 | 128 passed in 75.14 s (basetemp 1.3 GB, deleted) |
| 11 | `reading_input/tests/test_builder.py` | 0 | 67 passed in 68.71 s (basetemp 1.4 GB, deleted) |
| 12 | `scripts/stage1_s1/tests/test_oext_unit_contract.py`, `test_s1_repin_tool.py` | 0 | 69 passed |
| 13 | kit suite, final tree | 0 | **735 passed in 52.82 s** |
| 14 | one command used `timeout` | 127 | not on macOS; rerun without it |

Other read-only commands: `git status`, `git log`, `git diff`, `git show <commit>:<file> \| shasum`, `git ls-files`
(see §9), `shasum -a 256` on kit code and B14 files, key-only Python reads of the W1 manifest, the three add-edit
records and the prepared manifest's dev-bank entry, `date -u`, `uptime`.

## 7. The lead's commands

Run from the main checkout `/Users/spiderishi/Coding/attribution` unless a step says `cd $KIT`.

```zsh
ROOT=/Users/spiderishi/Coding/attribution; cd $ROOT || exit 1
PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
KIT=$ROOT/tmp/stage1-olmo
B14=$ROOT/.ai/inputs/stage1-post-w1-20261023/reading/b14     # my suggestion; any post-W1 records folder works
date -u
```

### Step 1: merge the round (by explicit paths)

Copy the 12 files of §2 from the worktree into the checkout and commit them by explicit paths. Then:

```zsh
shasum -a 256 runkit/stage1-olmo/{stage1_rules,plan_tool,finisher}.py runkit/stage1-olmo/setup/job_runner_stage1.py \
  runkit/stage1-olmo/README.md runkit/stage1-olmo/tests/{test_round34,test_stage1_runkit,test_stage1_runner,test_g1_yoext}.py \
  runkit/stage1-olmo/tests/mutants_b15.json research/experiments/2026-10-24-stage1-runkit/{run_mutants_b15.py,kit-round-34.json}
# each must equal the new SHA-256 of §2 / kit-round-34.json
```

### Step 2: suite and mutants (background jobs)

```zsh
STAGE1_ENGINE_Y_TREE=$ROOT/tmp/engine-y-34bfd288 PYTHONDONTWRITEBYTECODE=1 $PY -B -m pytest -q -p no:cacheprovider \
  --basetemp=<new scratch folder> runkit/stage1-olmo/tests            # expect 735 passed
IDS=$($PY -B -c "import json;d=json.load(open('runkit/stage1-olmo/tests/mutants_b15.json'));print(','.join(m['id'] for m in d['mutants'] if m['id'].startswith('B15-34-') or m['id'] in ('B15-r-o-only-unit','B15-8-runner-settings-unpinned','B15-g-no-recorded-recipe')))")
STAGE1_ENGINE_Y_TREE=$ROOT/tmp/engine-y-34bfd288 PYTHONDONTWRITEBYTECODE=1 $PY -B \
  research/experiments/2026-10-24-stage1-runkit/run_mutants_b15.py $ROOT <new scratch outside ROOT> \
  <out>/kit-round-34-mutation-report.json "$IDS"                       # expect 39 killed, not_as_expected []
# NEAR (optional): git archive 55d5f8b runkit/stage1-olmo | tar -x -C <scratch>/kit33, then
#   ... run_mutants_b15.py $ROOT <scratch2> <out2>.json NEAR --near <scratch>/kit33/runkit/stage1-olmo
```

The reading-input suite and B16's should also run on the merged tree (the builder loads `stage1_rules.py`; see §8).

### Step 3: sync into the live kit

```zsh
cd $ROOT
# before: the live copies must still be round 33's (the old hashes of §2)
shasum -a 256 $KIT/{stage1_rules,plan_tool,finisher}.py $KIT/setup/job_runner_stage1.py $KIT/README.md
#   expect bde78fab… f18bb834… 5d24290f… 37e8e81a… 11677460…
for f in stage1_rules.py plan_tool.py finisher.py setup/job_runner_stage1.py README.md; do
  cp -p runkit/stage1-olmo/$f $KIT/$f; done
# if the live copy keeps tests/ (round 33 synced them):
for f in test_round34.py test_stage1_runkit.py test_stage1_runner.py test_g1_yoext.py mutants_b15.json; do
  cp -p runkit/stage1-olmo/tests/$f $KIT/tests/$f; done
shasum -a 256 $KIT/{stage1_rules,plan_tool,finisher}.py $KIT/setup/job_runner_stage1.py $KIT/README.md
#   expect 4005cb4e… 27e299b5… f474cabe… ba0a761a… d136f8b5…
```

### Step 4: pack engine X (after every reading-prep track that touches `scripts/` or `experiments/` is committed)

`pack_setup.py` refuses while an engine or script file is uncommitted, and never overwrites a pack.

```zsh
cd $KIT
git -C $ROOT status --porcelain -- experiments scripts      # must print nothing
mv setup/packed-stage1-X setup/packed-stage1-X.before-round34-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p $B14
cat > $B14/pack_inputs_X_round34.json <<'EOF'
{"kind": "stage1 pack inputs", "engine": "X", "inputs": [], "code": [],
 "utc": "<date -u>", "recorded_by": "the lead (GI VIII)",
 "note": "kit round 34: B14's similarity pass (block sim) needs no named input; S1_CODE, the prepared set and the sealed records' edit files are packed by the kit's own pins"}
EOF
H=$(shasum -a 256 $B14/pack_inputs_X_round34.json | cut -c1-64)
python3.11 pack_setup.py X --inputs $B14/pack_inputs_X_round34.json --inputs-sha256 $H
$PY -I -B -c "import json;f=json.load(open('setup/packed-stage1-X/sealed-files.json'))['files'];\
print([f.get(k) for k in ('scripts/stage1_s1/overlap_similarity.py','scripts/stage1_s1/settings/overlap_similarity.json',\
'data/kt-prepared/prepared-kt-dolly-olmo2/banks/dev.jsonl')]);\
print([k[6:18] for k in f if k.startswith('edits/') and k[6:70] in ('904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10','a2f18a3d3df75691e8cd89975f6a8de36902c166767b9bd37d979d71b832476d','24aed3fbe6ff8111c81ff26cb7812b13ae50c158f78fada7c7520d33519ac53e')])"
# expect f8305c71…, 27db4c3f…, 1438ff51… and the three edit prefixes
```

Pack before `init-block`: release binds the host to the current pack's `sealed_files_sha256`.

### Step 5: the block's records and the dry run ($0; the decisive check on the real plan.json)

```zsh
cd $KIT
printf '%s\n' '{"launches": [{"hosts": [[{"kind": "similarity"}]]}]}' > $B14/jobs_block_sim.json
# the user's §36 decision record, exactly as block B's group funding record names it (prints path and sha256 only)
$PY -I -B -c "import json;p=json.load(open('plan.json'));print([(b,p['blocks'][b]['funding'].get('user_decision')) for b in ('certify','B') if b in p['blocks']])"
$PY -B plan_tool.py init-block sim --jobs $B14/jobs_block_sim.json --dry-run
# expect: funding_block sim, need_usd 10.98, base_need_usd 8.78, contingency_usd 2.2,
#         pods [{launch 0, cap_hours 1.5, guard_usd 8.78, counted 0, jobs ["similarity:None:None"]}]
# a refusal "B14's add set …" means the pins differ from the files the S arms trained on: stop and decide
date -u
cat > $B14/funding_block_sim.json <<'EOF'
{"block": "sim", "amount_usd": 10.98, "utc": "<date -u, UTC, not in the future>",
 "source": "user rule: start from the balance",
 "user_words": "no just start it now ill fund it when i feel like this is a rule",
 "recorded_by": "the lead (GI VIII)",
 "user_decision": {"path": "<as printed above>", "sha256": "<as printed above>"}}
EOF
$PY -B plan_tool.py init-block sim --jobs $B14/jobs_block_sim.json --funding $B14/funding_block_sim.json
# expect hosts ["sim-1"], released ["sim-1"]
$PY -B orchestrate.py check-plan sim-1        # expect {"host": "sim-1", "jobs": 1, "ok": true}
```

Optional $0 risk check before money: the design report's step A Mac pre-check
(`reading-prep/1b-b14-similarity.md` §8 A). It reads the dev bank and edit files in memory and prints counts and hash
prefixes. I did not run it (hard rule 2).

### Step 6: launch (both as background jobs; never foreground)

```zsh
cd $KIT
source <the secrets file>                     # RUNPOD_OPERATOR_API_KEY
python3.11 budget.py                           # the live balance; the pod needs $8.78 free above the guard's rule
# background job 1 (one finisher only; check first: pgrep -fl 'finisher.py')
caffeinate -i python3.11 finisher.py > finisher-sim-$(date -u +%Y%m%dT%H%M%SZ).log 2>&1
# background job 2
python3.11 launch.py sim-1 > launch-sim-$(date -u +%Y%m%dT%H%M%SZ).log 2>&1     # exit 0 when pod.json exists
```

The log names match the backup's `launch*.log` and `finisher*.log` globs. The in-pod timer stops the pod at 1.5 h
at the latest; the runner shortens it to 1 h after the job; the finisher stops it after the pull.

### Step 7: after the finisher's `finished` line

```zsh
cd $KIT
$PY -I -B -c "import json;print(json.load(open('hosts/sim-1/finished.json'))['status'])"   # verified-and-stopped
$PY -B plan_tool.py record-done sim-1
# prints {"host": "sim-1", "statuses": ["complete"], "similarity": [{"job": 0, "path":
#   "tmp/stage1-olmo/retrieved/sim-1/tree/job-0/similarity/similarity.json", "sha256": H_SIM, "record_sha256": …}]}
$PY -B seal.py status | grep -E '^sim-1|^block sim|estimated'
date -u
```

If the job crashed: `record-done sim-1` (records the crash), read `retrieved/sim-1/tree/job-0-similarity/process.log`
(B14 refusals name ids only) and the record's `problems`. A re-run is `defer sim-1` (to `sim-2`, paid $1.55 of the
$2.20 contingency), `orchestrate.py check-plan sim-2`, then step 6 with `sim-2`. A deterministic refusal (codec,
token audit) repeats: use the design report's fallbacks instead (route ii, then `--no-overlap`).

### Step 8: the strata (Mac, $0; after track B's D-6 lands)

```zsh
cd $ROOT
SIM_JSON=tmp/stage1-olmo/retrieved/sim-1/tree/job-0/similarity/similarity.json   # record-done's printed path
H_SIM=<record-done's printed sha256>
cp -p $SIM_JSON $B14/similarity.json && shasum -a 256 $B14/similarity.json        # must equal H_SIM
PYTHONDONTWRITEBYTECODE=1 $PY -B scripts/stage1_s1/overlap_strata.py strata --similarity $B14/similarity.json \
  --similarity-sha256 $H_SIM --out $B14/strata
shasum -a 256 $B14/strata/strata.json; date -u
```

Then both SHA-256 values into FOCUS and the second stamp, commit by explicit paths, the backup, and (on the user's
yes) delete the stopped `sim-1` pod after the backup.

## 8. Open points for the lead

1. **The reading's rules file changes.** The input builder loads `runkit/stage1-olmo/stage1_rules.py` by default and
   records its SHA-256. This round changes it (`bde78fab…` → `4005cb4e…`) and `plan_tool.py` (`f18bb834…` →
   `27e299b5…`). The 1d runbook draft lists both as "never" changing (its §0 table, step 0.1, R1b's expected line):
   update them. `seal.py` (`d6ddc8ef…`) and `judge_units_stage1.py` (`53f3c65b…`) are unchanged. The builder's
   tables do not change (REJUDGED_PINS, REUSED_SEEDS, block_runs, the judge constants and the O-ext pins are
   untouched), and the reading-input suite passed with the new file (195). The second stamp must bind the new
   files. This follows from running the pod through the kit before the reading.
2. **First CUDA run of B14.** The script's CUDA path and the real OLMo-2 template are untested (SIM:43-44). The
   design report's $0 pre-check lowers the risk of a post-load refusal.
3. **Pack order.** `pack_setup.py X` refuses uncommitted `scripts/`/`experiments/` changes; pack after the other
   tracks' commits. The new pack carries no named inputs (none needed for the sim host). A later X host (stage 1b)
   will need its own pack anyway.
4. **The §36 decision record** lies under `.ai/inputs/stage1-post-w1-20261023/block-b/`. Take its path and
   SHA-256 from block B's group funding record (step 5 prints only that field). I did not open it.
5. **D-6 before the strata.** The pod does not depend on D-6; `overlap_strata.py strata` does (the strata record
   carries the strata settings' hash). Order: pod → D-6 merged → strata → FOCUS → stamp.
6. **Reading `retrieved/`.** The strata step reads the sim host's similarity.json under `retrieved/` (record-done
   prints its path). The lead's new blinding note adds `retrieved/` to the never-open list for agents; the copy in
   step 8 is a single by-hash read of a non-outcome file by the lead.
7. **Kit round 35 numbering.** Stage 1b's scouting reports named "kit round 34" and J22 for the pilot. The lead's
   ruling moved stage 1b to round 35, so that round takes J23 and a block name other than `sim`.
8. **The runner's `NEW` selection** still means `B15-31-`; use explicit ids (step 2), as round 33 did.
9. **Seal of `sim`:** not required. If the lead seals it anyway, similarity.json is classed "sealed" by name only.

## 9. Hard-rule log

- **One breach of the letter of rule 1.** While checking which add-edit records the worktree tracks, I ran
  `git ls-files .ai/inputs/stage1-post-w1-20261023/block-b | head -3`. It printed three file names under `block-b/`
  (a fingerprint record and two billing files). No file there was opened, hashed or read; no value was printed. No
  other forbidden path was listed, opened or hashed.
- Not opened: `tmp/stage1-olmo/plan.json`, `hosts/`, `judges*/`, `seals/`, `retrieved/`, any unit, eval, answer,
  label or cache file, any COMPLETE.json, the selector or hidden bank, any "plant" or "decoy" path. The live kit was
  read for code only (hashes of top-level `.py`, `setup/*`, `judge_pod_stage1/bundle.py`, `README.md`).
- Read by key: the W1 manifest (roles and SHA-256 of `scripts/stage1/` entries; no add-set entry exists), the three
  add-edit records (kind, edits' file, arm, sha256), the prepared manifest's dev-bank entry (one hash).
- No git state change, no commit, no network, no install, no pod, no API call. No real-data command (no reading,
  builder, overlap, judge, seal, kit or launch command on real state). Every pytest basetemp was deleted.

## 10. Acceptance criteria

| Criterion | Status |
|---|---|
| Kind with the next KIND_IDS id | passed (J22) |
| One-host block, own funding, §36 record | passed (tested with a synthetic decision record) |
| Runner command: engine X, REC, settings and inputs by SHA-256 | passed (exact argv tested; parsed by B14's own parser; REC's config SHA-256 = the settings' pin by engine X's code) |
| What the pod returns (output and record) | passed (synthetic pod) |
| Light check and pull | passed (synthetic trees; pull list covers every path) |
| Cap and price figures | passed (by hand and in tests) |
| plan_tool support to add the host | passed (init-block, refusals, release re-check, defer) |
| Pack inputs | passed in tests (synthetic pack; check-plan on a round-33 and a round-34 pack); real pack not run |
| Existing safeguards reused | passed (timers, finisher, secret scan, light check, record-done, contingency) |
| Kit suite | passed (735) |
| Near mutants | 36 added; pre-check 36/36 killed; official spec run not run here |
| Real pod, real plan.json, real pack | not tested (the lead's steps 4–7; the dry run in step 5 is the $0 check) |
