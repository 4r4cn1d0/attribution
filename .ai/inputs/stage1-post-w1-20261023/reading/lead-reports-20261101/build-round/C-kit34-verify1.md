# C-kit34 verification 1: kit round 34 (J22 `similarity`, block `sim`)

Written by the independent adversarial verifier of track C-kit34 for the lead (GI VIII), 1 Nov 2026, finished
about 09:56 UTC (clock read with `date -u` at 09:55:09 UTC). Model identity is the launcher's record, not this text.

- Checked: the worktree `builds/ws-c` (detached at 55d5f8b; `git diff` and `git status --porcelain`: 10 modified
  files and 2 new files, exactly the 12 files of the build report's §2), the build report `C-kit34-build.md`
  (`539d3b3a…`) and the design report `reading-prep/1b-b14-similarity.md` (`c03f6746…`).
- Sources read: REV4 §9.4 and §12; ADD §17, §25, §36–38; FOCUS (main checkout 38e160d; only FOCUS changed since
  55d5f8b); NEXT; the 1d runbook draft; the critic; and track E's drafts (`E-misc.md`, `E-40.md`).
- Every claim below was checked against code or by a command I ran. Nothing in `builds/ws-c` was edited.

## 1. Verdict

**Verified.** I found no defect that matters for the reading's correctness, the frozen rules or blinding.

- **The command.** The new kind runs B14's pinned script once, on engine X with REC. Its inputs are given by
  SHA-256 and checked on the pod before the step.
- **No other output can complete.** An output that is not on `stage1_rules`' pins is a crash. The pod checks it,
  then the finisher, then record-done.
- **Safeguards.** Every existing safeguard is kept.
- **Existing kinds.** Their behaviour is unchanged, except for one extra plan.json read in the finisher's light
  check (note N2).
- **Money.** The figures match the design report.
- **Sealed state.** The round's code touches none.
- **The test that matters most.** B14's real `run()` (on B14's own synthetic fixture) writes an output that the
  kit's checks accept with no problem (§2.7).

Notes N1–N11 follow. N1 is procedural. The lead should decide it before running steps 7–8 of the build report.

## 2. What I checked

### 2.1 Every changed code path (diff read line by line)

| File | Change | Effect on existing kinds |
|---|---|---|
| `stage1_rules.py` | `similarity` appended to `KINDS` (J22), `UNMEASURED_KINDS`, `UNITLESS_KINDS`. Block `sim` added to `BLOCKS`, `FUNDING_BLOCK`, `HOST_PREFIX`, `BLOCK_KINDS`. Two `S1_CODE` pins; the `SIM_*` constants; a `similarity` branch before the `raise` in `measured_upper`/`upper_s`; new functions. | None. I loaded the 55d5f8b and round-34 files side by side (`verify-C-kit34/builder_values.py`). `REJUDGED_PINS`, the `JUDGE*` constants, `REUSED_SEEDS`, `TRAINING_IDENTITY_RECIPES`, `RECIPE_NAMES`/`RECIPE_PINS`, `S1_OEXT_Y`, `PREPARED_MANIFESTS`, `ENGINES` and `TRAINING_IDENTITY` are equal. `block_runs` is equal for plans A and B × blocks A, B and C. `S1_CODE` only gains two entries. The old `KIND_IDS`, `BLOCK_KINDS` and `FUNDING_BLOCK` entries are equal. `job_record` is equal for every old kind. |
| `plan_tool.py` | `RECORDED_RECIPE["similarity"] = "B"`; `similarity` in `no_arm`; an engine-X check; `similarity_entry`; the block-`sim` shape check and `rec["similarity"]` in `build_block`; a re-check in `release_hosts`; the similarity part of `record_done`. | None. Every addition is guarded by `kind == "similarity"` or `block == "sim"`. `default_recipe`/`recipe_of` still give the old values for the old kinds. Block ordering (`planned_parts` `seq` default, `group_jobs`) keeps the old relative order. |
| `setup/job_runner_stage1.py` | `SCRIPTS["similarity"]`; `similarity_pins`/`similarity_args`; a `similarity` branch in `job_commands` and `sealed_paths`; `("-similarity", "scoring")` appended to the end of `STEP_STAGE`; `similarity_record`; a `similarity` branch inside the unit-free branch of `run_job`. | None. No old step name contains `-similarity`, and `stage_of` takes the first suffix that matches. |
| `finisher.py` | `similarity_check`, called from `light_check`. | One extra `plan.json` read for every host, a sim host or not (N2). |
| `README.md`, the tests, `mutants_b15.json`, `run_mutants_b15.py`, `kit-round-34.json` | documentation, tests, spec, runner `TESTS` | The changed existing tests only update counts and tables (`S1_CODE` 11 → 13, the J22 row, `FINISHER_34`). The 3 retargeted mutants keep their meaning (§2.7). |

The unchanged generic code handles block `sim` correctly:
- `gate_order`: G3, and no plan "none".
- `gate_g1`/`g4`, the funding record under §36 (`funding_rule_decision` re-hashes the decision record).
- `release_hosts`: binds the current pack's `sealed_files_sha256`, registers REC.
- `defer`/`move_open`/`place`/`pay_reruns`: contingency `sim`; the moved job keeps its `similarity` entry, because
  `_strip` keeps it.
- `host.py` `PULL_ITEMS` (`job-*`), `status.py`, `seal.py status`, `backup_records_stage1.py`: `UNITLESS_KINDS`
  outputs, and `setup/packed-*` also covers the renamed old pack.
- `orchestrate.py check-plan`: the runner's dry run plus `sealed_paths`.
- The reading-input builder's `Kit.hosts(block)` and track B's `overlap_inputs.py` skip hosts of block `sim` and jobs
  of kind `similarity`, so a `sim-1` host in plan.json does not reach the reading.

### 2.2 The pod's command and its inputs

| Item | Checked how | Result |
|---|---|---|
| argv | `job_commands`; the round's tests `test_the_runner_runs_b14_on_the_pins…` and the dry-run table, both by hand | `venv/bin/python scripts/stage1_s1/overlap_similarity.py --prepared data/kt-prepared/prepared-kt-dolly-olmo2 --recipe <REC> --add-set S1 edits/<S1>.edit.json <S1> --add-set S3 … --add-set S4 … --out job-I/similarity`. This is the design report's §8 C command, except `-B` and the extra environment (N4). B14's own parser parses it (`test_every_jobs_argv_parses_with_its_targets_own_parser`). |
| Script and settings pins `f8305c71…`, `27db4c3f…` | `shasum` of the files at 55d5f8b and `git show` at 3ea5ae1 (S1_COMMIT) and 3417f12 | equal at all three |
| Prepared manifest `9ed61826…` and dev bank `1438ff51…` | `shasum` of `tmp/kt-prepared/prepared-kt-dolly-olmo2/manifest.json` (= `manifest.sha256`); one key of it (`files["banks/dev.jsonl"]`) | equal |
| Add sets S1 `904a0cf1…`, S3 `a2f18a3d…`, S4 `24aed3fb…` | the three add-edit records, read by key; `shasum` of `tmp/stage1-mac-runs-20261023/add-s{1,3,4}/add_s*.json` | equal (each record names its file with `arm` = `edit-<SHA-256>`) |
| B14's provenance keys | B14's code, and B14's real run (§2.7) | `prepared/manifest.json`, `prepared/banks/dev.jsonl`, `recipe`, `add/S1`, `add/S3`, `add/S4`. These are exactly `similarity_inputs`. |
| Packed? | `pack_setup.stage1_code` packs `S1_CODE` on X. `s1_settings_engine` needs `engine_x` = `ENGINES["X"]`: true. `labels.json`, `s1common.py` and `limits_common.py` are MAN1 or `STAGE1_PINS` entries. The edits come from the recorded sealed records. The prepared folder is packed in full. | yes |
| Model on the pod | `download_models_stage1.py` always fetches the policy (only the base model is optional) | yes |
| transformers 4.56.2 (B14's settings pin) | `experiments/minimal_safety/requirements.lock:29` | equal |

### 2.3 "Cannot run anything else"

- **The script and recipe are fixed.** The script is the constant `SIM_SCRIPT`. `--recipe` is always `rules.REC`, not
  the plan's recipe. The job record admits recipe `B` only, engine X only, and no arm or seed. Block `sim` admits
  exactly one launch of one pod holding one similarity job.
- **Before the step.** `similarity_args` refuses unless plan.json's entry names the kit's paths, exactly S1/S3/S4,
  and hex SHA-256 pins. Every file must also be listed in `sealed-files.json` at that pin. `sealed_check` re-hashes
  each listed file before the job.
- **After the step.** A hand-edited plan.json (for example two add-set pins swapped) would make B14 run on other
  bytes. The record then compares the output's provenance with the pod's `stage1_rules` (`SIM_ADD_SETS`, `S1_CODE`,
  `PREPARED_MANIFESTS`, `SIM_DEV_BANK`, and REC's config hash from plan.json). Any difference is a crash. The finisher
  and record-done repeat the check. So no other input can produce a `complete` job.
- **plan.json's entry.** `similarity_entry` re-derives it from the rules at init and again at release. It also
  checks the add sets against the files the S-arm runs trained on.
- **Run once.** The pass runs at most once successfully:
  - `gate_order` refuses a second block `sim`;
  - `defer` moves only crashed, deferred or not-started jobs;
  - the contingency pays one re-run ($2.20 against $1.5513 each).

### 2.4 Safeguards kept

- **Pod and runner.** The in-pod cap timer (1.5 h), the runner's per-job gate (2,700 s needed; 2,880 s are left
  after the full 42-min overhead), the shortening of the stop to 1 h after the job, the token-free environment
  (`CUBLAS_WORKSPACE_CONFIG`, `HF_HUB_OFFLINE`), and the preflight with REC are all kept.
- **Pod checks.** The environment comparison with Gate B's reference (strict), sealed-files, the engine identity and
  the recipe pins are kept.
- **Finisher.** The light pull, the secret scan, the light check (now with `similarity_check`) and the stop are kept,
  and the pod is never deleted.
- **Mac records.** record-done (with the similarity check), `defer` from the contingency, the operator-action log and
  the backup are kept.
- **No deletion.** The round adds no deletion. The record is written with an exclusive create.

### 2.5 Money (by hand; equal to the code and the build report)

| Item | Value |
|---|---|
| Upper / start requirement | 1.5 × 600 = 900 s / 900 + 1,800 = 2,700 s |
| Cap | 2,520 + 2,700 = 5,220 s → up to 900-s steps → 5,400 s = **1.5 h** |
| Guard | $6 + 1.5 × $1.85 = **$8.775** |
| Upper spend | (2,520 + 600) / 3,600 × $1.79 = **$1.5513** |
| Need | base `cents(8.775)` = $8.78; 1.25 × $8.78 = $10.975 → **$10.98**; contingency **$2.20** (pays 1 re-run, not 2) |
| Design report | cost about $0.60–0.75 (E), worst about $2.7–3.1 at a cap of about 1.5–1.75 h. The round has cap 1.5 h, worst 1.5 × $1.79 = **$2.685**, and E $0.60–0.90: consistent. |

### 2.6 Sealed state and blinding

- **No sealed or outcome path.** The round's code reads none:
  - no `seals/`, `judges*/`, other hosts' `retrieved/` trees, unit, eval, guard or answer file;
  - B14 reads only the dev bank, among the banks.
- **What `similarity_entry` reads.** plan.json's job records: kind, arm, status and edit SHA-256. It also reads the
  edit sources that `resolve_edit` already reads at every arm release (MAN1, Gate B's MANIFEST, the recorded sealed
  records), and it hashes the three add-set files.
- **No similarity value in the kit's records.** The runner's record, the JOB-DONE `why` strings, the finisher's
  tails and record-done's print carry only hashes, counts and field names. A similarity value is not a stage-1
  outcome.
- **The OTS stamp.** The first OTS manifest (`reading/timestamp/ots-manifest-20261031.json`, key `git.trees`) binds
  `runkit/stage1-olmo` at tree `24cf7425…`. Round 34 changes that tree, so the second stamp must bind round 34's tree
  (N3).

### 2.7 Tests and probes I ran

| Run | Result |
|---|---|
| Kit suite in `ws-c` (`runkit/stage1-olmo/tests`, `STAGE1_ENGINE_Y_TREE` set, fresh basetemp, deleted) | **735 passed** in 38.74 s, exit 0 |
| `scripts/stage1_s1/reading_input/tests` + `test_oext_unit_contract.py` + `test_s1_repin_tool.py` + `test_oext_unit_y.py` in `ws-c` (they load the round-34 rules; basetemp 2.7 GB, deleted) | **272 passed** in 74.68 s, exit 0 |
| `verify-C-kit34/check_mutants.py`: all 418 spec entries | every find text occurs exactly once; every mutated `.py` compiles; 36 `B15-34-*` ids; the 3 new retargets keep their meaning (o_only alone removed; the oext_unit.json pin removed; J5's "S" dropped) |
| Official runner `run_mutants_b15.py` (all 8 test files) on 6 new ids | baseline 735 passed. **Killed: B15-34-problems-inputs, -record-equal, -runner-entry, -runner-stale.** I stopped the run at the 10-minute limit before B15-34-entry-trained and -light-check (N9). Evidence: `verify-C-kit34/mut-report-6.json`. |
| `verify-C-kit34/e2e_probe.py` (synthetic): **B14's real `run()`** on B14's own fixture (tiny CPU model) → the kit's `similarity_problems`, the runner's `similarity_record` with the stdout line exactly as `main()` prints it, and the Mac's `similarity_record_problem`, with the pins pointed at the fixture | problems `[]`; record written, no problem; Mac check `None`. With the real counts (200) left in: `['eval.prompts']`, as expected. |
| same probe, log variants | a progress bar ending in `\r` before the line: **accepted** (`read_text` translates `\r`); a warning written without a newline before the line: **crash** (N5) |
| `verify-C-kit34/finisher_probe.py` (synthetic tree of a non-sim host), round 33 vs round 34 | round 33: light check ok with plan.json readable or truncated; round 34: ok when readable, **raises `JSONDecodeError` when plan.json is truncated** (N2) |
| `verify-C-kit34/builder_values.py` | every rules value the reading builder and the B14 inputs writer read is equal at 55d5f8b and in round 34 (§2.1) |
| `kit-round-34.json` `changed_files` | every old and new SHA-256 equals the HEAD blob and the worktree file |
| Live kit `tmp/stage1-olmo` code files | `stage1_rules.py` `bde78fab`, `plan_tool.py` `f18bb834`, `finisher.py` `5d24290f`, `setup/job_runner_stage1.py` `37e8e81a`, `README.md` `11677460`: equal to the repository copies. Step 3's "before" check holds now. |

## 3. Defects

None that matter for the reading's correctness, the frozen rules or blinding.

## 4. Notes (minor; most important first)

**N1. Steps 7–8 of the build report open files under `tmp/stage1-olmo/retrieved/` by hand. Decide this before running
them.**
- **The rule.** `retrieved/` is on the never-open list (FOCUS line numbers at 38e160d):
  - FOCUS:77: it "joins the never-open list";
  - FOCUS:76 (the 04:55 rulings): "`tmp/stage1-olmo/retrieved/` never opened";
  - track E's draft §40 point 3 (`E-40.md`:67-69): "Never opened by hand or by a helper … Only reviewed code reads
    them, by key". E's own check (`E-records-build.md` D2) confirmed that the rule has no time limit.
- **What the steps do.**
  - Step 7, on a crash: "read `retrieved/sim-1/tree/job-0-similarity/process.log`". The builder did not flag this.
  - Step 8: `cp -p $SIM_JSON $B14/similarity.json && shasum -a 256 …`, where `$SIM_JSON` is under
    `retrieved/sim-1/`. The builder flagged this as open point 6 and accepted it as a by-hash read.
- **Effect.** Neither file holds a stage-1 outcome, so blinding in substance is intact. But following the steps as
  written breaks the letter of the recorded list.
- **A compliant route ($0, no code change).**
  - Take the path and SHA-256 that record-done prints. That is reviewed code, and it already re-checked both files.
  - Run `overlap_strata.py strata --similarity <that path> --similarity-sha256 <that SHA-256>` in place. The strata
    step re-hashes the file itself and refuses another SHA-256.
  - On a crash, read only `record-done`'s statuses and the record's `problems`, both written by reviewed code.
- **Optional small kit change.** A reviewed export, for example record-done copying `similarity.json` and its record
  by SHA-256 to a records folder outside `retrieved/`. This would give the second stamp (which, by E's plan updates,
  must bind `similarity.json`) a stampable copy without a by-hand read. The runner could also copy B14's
  `REFUSED: …` line, which names ids only, into the job's `why`. Otherwise the lead records an explicit exception for
  these two non-outcome files.

**N2. The finisher's light check now reads plan.json for every host.**
- **Where.** `finisher.similarity_check` calls `plan()` whenever the pulled JOB-DONE.json parses, before it looks for
  a similarity job. Round 33's `light_check` read no plan.json.
- **Reproduction.** `finisher_probe.py` with a truncated plan.json (as during a non-atomic `save_plan` by a concurrent
  plan_tool command): round 33 returns the unit's result; round 34 raises `JSONDecodeError`.
- **Effect.** Inside `finish()` this becomes `finisher-error-stopped`. The pod is still stopped, and record-done
  re-checks. For the sim launch only the sim host is watched, so the risk is small.
- **Fix.** Read `plan()` only after a complete similarity job is found.

**N3. The reading's kit hashes change.**
- **What changes.** `stage1_rules.py` `bde78fab` → `4005cb4e` and `plan_tool.py` `f18bb834` → `27e299b5`. The 1d
  runbook draft (lines 62, 106, 220-229) lists both as "never" changing. The first OTS stamp binds the
  `runkit/stage1-olmo` tree `24cf7425…`.
- **Who flagged it.** The builder (open point 1) and track E's `E-misc.md` §A 2b. I add the OTS fact.
- **A record claim that is not true yet.** E's §39 2b says round 34 comes "with a test that compares each [builder
  value] with its value at `55d5f8b`".
  - Round 34 adds no such test, and I found none in any track's worktree.
  - Older kit tests pin some of these values by hand (for example `block_runs` in `test_stage1_runkit.py:1100-1129`,
    and the judge constants).
  - My `builder_values.py` shows that every value is equal.
  - Either add the dedicated test to round 34 (load the 55d5f8b rules by `git show` and compare the named values) or
    reword the clause in §39.

**N4. The argv is not "exactly" the design report's §8 C command.**
- **Differences.** It has no `-B`, and the runner sets `OMP_NUM_THREADS=4`, `MKL_NUM_THREADS=4`, `PYTHONPATH` and
  `HF_HUB_OFFLINE=1` besides the three variables the design names.
- **Why this does not matter.** This is the kit's form for every step. `-B` only suppresses `.pyc` files, which
  nothing hashes or pulls. The thread count can change the last bits of the float64 CPU cosines, but the pass runs
  once and its output is sealed by SHA-256. Record it as the run's fixed environment.

**N5. The printed-SHA-256 rule can turn a good run into a crash in one log case.**
- **The rule.** The runner needs exactly one line matching `^wrote similarity\.json into job-I/similarity (H)$` in
  the merged stdout and stderr log.
- **Reproduction.** `e2e_probe.py` with a warning written without a trailing newline just before the line: the
  output is on the pins, but the record lists "the SHA-256 the script printed is missing or not the file's", and the
  job crashes.
- **Likelihood.** Low. Python warnings and logging end in `\n`. A `\r` progress bar is accepted, and this load path
  (a single safetensors file, offline) shows no bar. But a crash would repeat on the paid re-run.
- **Possible fix.** Match the line anywhere in a line (`re.search(r"wrote similarity\.json into (\S+) \(([0-9a-f]{64})\)\s*$", …)`),
  or record a missing printed line without crashing when the file's SHA-256 checks out.

**N6. The design report's $0 Mac pre-check is part of its default route.**
- The design report (§7) and E's plan updates make the pre-check (step A) part of the default route. The build
  report calls it "optional".
- A deterministic post-load refusal (codec, token audit, block count) would cost the pod. By the re-run rule it would
  also cost a second pod from the contingency.
- Recommend running step A before step 6.

**N7. Re-run advice for a deterministic refusal.**
- **What step 7 says.** For a deterministic refusal, "use the design report's fallbacks instead (route ii, then
  `--no-overlap`)".
- **Why route (ii) does not help.** It runs the same code on the same inputs, so the refusal repeats there too.
- **What applies.** After a deterministic B14 refusal, the last resort applies (`--no-overlap`), or a recorded fix of
  B14.

**N8. The README and round report say "No similarity value is read or printed by the kit".**
- This is true of the kit's code.
- B14's own stdout, in the pulled `job-0-similarity/process.log`, prints each add set's `s_max` minimum and maximum.
  These are not outcomes.

**N9. Mutant status.**
- I ran 4 of the 36 new ids under the official runner with all 8 test files: all killed. I stopped before the other
  two I had selected, to keep within the 10-minute rule.
- The rest rely on the builder's narrowed pre-check (test_round34.py only, 36/36 killed). Under the full test list,
  an ERROR in another file would make a mutant INVALID.
- The official run of the 36 new ids, the 3 retargets and NEAR remains the lead's background job (build report §7,
  step 2).

**N10. Optional hardening.**
- `similarity_problems` does not check `provenance.engine_identity_sha256` = `ENGINES["X"]`. The preflight's engine
  identity and B14's settings check enforce this indirectly.
- Problem strings embed provenance input key names from the output. B14 scans its output bytes for every text before
  writing, so no text can reach them.

**N11. Hard-rule log of the builder.**
- The builder self-reported one `git ls-files … block-b | head -3`, which printed three file names under `block-b/`.
  Names only, no content.
- Nothing in the round depends on it.

## 5. The builder's task, criterion by criterion (my status)

| Criterion | Status |
|---|---|
| Kind with the next KIND_IDS id (J22), unit-free, engine X, recipe REC | passed (code and tests) |
| One-host block `sim`, own funding group, §36 record | passed (code; tested with a synthetic decision record) |
| Runner command with the pinned settings and inputs by SHA-256 | passed (argv; pins verified against files and records; B14's real output accepted, §2.7). The argv differs from the design's literal form only as in N4. |
| What the pod returns (`similarity.json` and its record) | passed |
| Light check and pull | passed; one side effect on other hosts (N2) |
| Cap and price figures vs the design report | passed (§2.5) |
| plan_tool support (init, refusals, release re-check, defer, record-done) | passed |
| Pack inputs | passed in code (S1_CODE pins; X settings engine pin; empty inputs record accepted). The real pack is not run. |
| Existing safeguards kept; existing kinds unchanged | passed, except N2 |
| Kit suite | passed (735, my run) |
| Near mutants | 36 added, find texts valid. 4 re-run by me and killed. Full official run not run (N9). |
| Round report `kit-round-34.json` | present; hashes correct |
| The lead's commands (sync, add the host, launch in background) | correct, except the by-hand `retrieved/` reads of steps 7–8 (N1) and the wording points N6–N7 |
| Real pod, real plan.json, real pack | not tested (hard rule 2); the step-5 dry run is the $0 check on the real state |

## 6. Commands I ran (exit status)

All with `/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -B` (or `-I -B`),
`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider` for pytest, and each basetemp a fresh folder under `builds/tmp/`,
deleted after the run.

1. `date -u` (several), `uptime`, `df -h`: 0.
2. `git -C builds/ws-c status --porcelain / diff / diff --stat / log / rev-parse`; `git -C <main> rev-parse / status / log / diff 55d5f8b 38e160d -- research/FOCUS.md / merge-base`; `git show <c>:<B14 files> | shasum` for 3ea5ae1, 3417f12 and 55d5f8b; `git -C ws-c archive 55d5f8b runkit/stage1-olmo | tar -x` into my scratch; `git -C ws-{a,b,d1,d2} status --porcelain`: all 0 and read-only. (One first try of the `git show` loop printed `bad substitution`, a zsh `$c:` modifier; I re-ran it with braces.)
3. Kit suite in ws-c: 0 (735 passed).
4. reading_input + 3 S1 test files in ws-c: 0 (272 passed).
5. `check_mutants.py`, `builder_values.py`, `e2e_probe.py`, `finisher_probe.py` (round 33 and round 34 copies): 0.
6. `run_mutants_b15.py ws-c <scratch> mut-report-6.json <6 ids> --timeout 300`. The tool moved it to the background
   when it passed the 10-minute foreground limit. **I stopped it at once** (TaskStop). No child process was left
   (`pgrep`). Its scratch (683 MB) was deleted. The report file holds 4 results.
7. Read-only key reads: the W1 manifest (roles; no add-set entry; none of the changed files is an entry); the three
   add-edit records; the prepared manifest's dev-bank entry; the OTS manifest's `git` block; `kit-round-34.json`;
   the builder's mutation evidence files. `shasum` of: B14's files, the prepared manifest, the three add-set files,
   and the five live-kit code files.

## 7. Hard-rule log

- **Not opened, listed or hashed.** Nothing under `tmp/stage1-olmo/hosts/`, `judges*/`, `seals/`, `retrieved/`, the
  judge-pod folders, `block-a/`, `block-b/`, any `units/` or `eval/` folder, any COMPLETE.json, answer, label,
  guard-sample or judge-cache file, the hidden or selector bank, `tmp/stage1-olmo/plan.json`, or any "plant" or
  "decoy" path.
- **Two things printed names only.**
  - `ls tmp/stage1-olmo/` printed the first 50 top-level names of the live kit, including the folder name `hosts`
    and log file names. No folder content was listed and no log was opened.
  - Printing the OTS manifest's kit paths showed the two seal-record paths
    (`tmp/stage1-olmo/seals/block-A.json`, `block-B.json`). They were not opened.
- **The background job.** The mutation command became a background job only through the tool's 10-minute auto-move.
  I stopped it at once.
- **No state change.** No git state change, no edit of the main checkout or of `builds/ws-c` (its `git status` is
  unchanged; no `.pyc` written), no network, no install, no pod, no API call. No reading, builder, overlap, judge,
  seal, kit or launch command ran on real data or the real kit state. B14's `run()` ran only on its own synthetic
  fixture.

## 8. Evidence paths

All under `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/verify-C-kit34/`:
- `e2e_probe.py`
- `finisher_probe.py`
- `builder_values.py`
- `check_mutants.py`
- `mut-report-6.json`
- `kit/` and `kit33/`: code copies of round 34 and round 33, with the probes' synthetic `plan.json` and `retrieved/a-9`
