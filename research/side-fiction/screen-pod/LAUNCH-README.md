# Fiction training-data screen: the launch folder

Written 9 October 2026, 11:05 UTC (clock checked), by the Side Project's Opus worker, for the lead (General
Implementation IV). Revised 9 October 2026, 17:53 UTC (clock checked): the screen's Granite part now uses the lead's
Granite pod mode, so there is one Granite-on-CUDA backend. Updated 17:56 UTC (clock checked) with the lead's Granite
parity result (PASS). It implements `research/side-fiction/SCREEN-SPEC.md` (SHA-256 `81dc487a…`, sections 1 to 8;
section 8 is this backend) in the Side Project's worktree.

**Hand-over: this folder goes to General Implementation V, the new lead** (the lead hand-over from General
Implementation IV, main commit `716d362`).

**Status: built and tested on the Mac with fakes and the real inputs. Nothing was launched.** No pod was made, no RunPod
API was called, nothing was downloaded from the Hub, no model was loaded and no GPU process was started. The lead
launches after the independent review.

The folder holds four things:

- `tool/`: the code;
- `tests/`: the tests;
- `sp_fiction_screen.sh`: the launch script, modelled on `hb_side_pod.sh`;
- `MANIFEST.sha256`: the SHA-256 of every file in the folder.

The development copy, which is identical, is `research/side-fiction/screen-pod/` in the worktree.

## What one launch does

- **Round 1.** One A100 pod runs these steps in order:
  1. The setup of the Qwen3Guard side: its venv and its 8.8 GB download.
  2. **The lead's Granite pod job, unchanged** (`pod_run_granite.sh`, the lead's `--judge granite` mode). It makes the
     Granite venv, builds llama-cpp-python 0.3.36 with CUDA from its pinned sdist, downloads and checks the GGUF, and
     checks the packages, the GPU offload, the files and the tokenizer fingerprint. Then it runs **the lead's
     known-answer gate** (200 Granite calls). No fiction row is judged before the gate passes.
  3. Granite Guardian 3.3 8B on the 10,000 fiction rows, with two passes per row: `harm` (the drop rule) and
     `sexual_content` (report only). Every call is the lead's `granite_pod.judge_triples`.
  4. Qwen3Guard-Gen-4B, through the engine's GuardScorer, on the 10,000 fiction rows and the 4,800 Dolly train rows.
- **Rounds 2 and 3.** The same steps on the `refill-rN.jsonl` that `sf_screen.py refill` wrote.
- **What the launch reuses.** The lead's code in `scripts/gate_b_mac_judges/` (commit `2694bd0`), by import and
  unchanged:
  - `podhost.py`: the budget lock and guard, reconcile, create with the in-pod timer and the lead's $10/h price limit
    (the screen adds no second limit), the orphan check, and the stop;
  - `judge_pod.py`'s helpers: the signals, the log, the fetch with retries, the salvage, and the known-answer block's
    summary and consistency check;
  - the Granite pod mode: `bundle.py` stages the Granite part of the screen's bundle, `pod_run_granite.sh` and
    `pod_job.py` run it on the pod, and `granite_pod.py` and `granite_files.py` hold the prompt, the call and the
    parse.
- **The pins on the lead's files.** All 19 lead files that the screen imports or ships are pinned by SHA-256 as
  committed in `2694bd0` (the main checkout's HEAD `019a72e` holds the same bytes). A changed file refuses with exit 2.
  Among them: `pod/granite_pod.py` `dc04e108…`, `granite_files.py` `200299af…`, `pod/pod_job.py` `f5ffe5d1…`,
  `pod/bundle.py` `144f3b18…`, `pod/judge_pod.py` `da91a0bf…`, `pod/podhost.py` `1eefa3a4…`,
  `pod/pod_run_granite.sh` `e3a51f36…`, `pod/granite-requirements.txt` `519ec520…`, `pod/granite-known-answers.json`
  `b5b2678e…` and `pod/PARITY.md` `c4fc455e…`.

## Names (all new; on 9 Oct no "sp-" name existed under `tmp/`)

| What | Round 1 | Round 2 / 3 |
|---|---|---|
| Tag | `sp-fiction-screen-r1` | `sp-fiction-screen-r2` / `-r3` |
| Pod name | `attribution-judge-sp-fiction-screen-r1` (podhost's prefix, unchanged) | `…-r2` / `…-r3` |
| Host records | `tmp/family-probe-sp-fiction-screen/hosts/sp-fiction-screen-r1/` | `hosts/sp-fiction-screen-r2/` … |
| Run folder | `tmp/family-probe-sp-fiction-screen/runs/sp-fiction-screen-r1/` | `runs/sp-fiction-screen-r2/` … |

- **The budget guard sees the host records.** Every kit's `budget.py` scans `tmp/family-probe-*/hosts/*/`, so the
  shared guard counts this pod: its create intent at $1.85/h until its cap, then its `pod.json` at its real price.
- **Every launch needs a new tag.** For a relaunch, set `TAG=sp-fiction-screen-r1b` before the script, for the
  launch and again for its `summarize`. To resume an exit-5 run, also set `RESUME=<old tag>`.
- **What the script prints.** Before it runs anything, the script prints the command, the round, `TAG`, `LIMIT` and
  `RESUME`. `LIMIT=N` (N rows of each source) is for dry checks only: the script refuses a launch with `LIMIT` set.

## Cap and cost (planning rate $1.85/h, reserve $1)

**Round 1** makes 20,200 Granite calls (the gate's 200 known answers, plus 2 × 10,000 rows) and judges 14,800
Qwen3Guard rows. The refactor does not change these numbers.

- **Cap.** The planning times give 3,600 s setup + 20,200 × 0.4 s + 14,800 × 0.25 s + 900 s margin = 16,280 s = 4.52 h.
  Rounded up to the next half hour, the cap is **5.0 h**.
- **Upper cost.** 5.0 h × $1.85 = **$9.25**. The guard therefore needs at least $10.25 free after the other pods'
  commitments.
- **Lowering the cap.** `--cap-hours` may lower it, but never below 4.52 h. The script does not pass it: run
  `screen_pod.py` directly if you need that.
- **Expected run time: 80 to 188 min.** That is about $2.40 to $5.60 at the A100's $1.79/h. The bundle record prints
  $2.47 to $5.79 at $1.85/h.

The estimate rests on token counts that were measured on the Mac with the real tokenizers (counts only):

- **Granite.** The templated input averages about 290 tokens (maximum 2,646; no row reaches the 8,000-token trim).
  The `sexual_content` call adds 101 tokens after the prefix it shares with the `harm` call. The counts now come from
  the lead's `granite_files.granite_input`, and they are the same as before.
- **Qwen3Guard.** The input averages 529 to 590 tokens (maximum 2,509). None is over the limit of 8,192, and none
  holds a control string.

From those counts, the estimates per item and for setup are:

- **Per item.** 0.12 to 0.30 s per Granite call on CUDA, and 0.08 to 0.17 s per Qwen3Guard row (gate A measured
  0.165 s at batch 8).
- **Setup.** 20 to 45 min: the guard venv and the 8.8 GB Qwen3Guard download, then the lead's Granite job (its venv,
  the llama.cpp CUDA build, the 4.9 GB GGUF, and the gate). Both venvs sit on the container disk. The new layout adds
  about 1 min: the Granite model loads twice (in the lead's gate and in the screen's Granite step), and the GGUF is
  hashed once more.

**Rounds 2 and 3.** The cap comes from the refill file's row count. Some examples:

| Refill rows | Cap | Upper cost |
|---|---|---|
| 15 (3 drops × 5 candidates) | 1.5 h | $2.78 |
| 1,000 | 2.0 h | $3.70 |
| 4,250 (850 drops × 5) | 3.0 h | $5.55 |

Each round runs the lead's gate again, because each round is a new pod with a new build.

## Commands for the lead (zsh; paste one block at a time)

Every block starts with `setopt interactivecomments` and holds no comment. Replace each quoted `'<...>'` placeholder;
an unreplaced one is refused.

**Block 1: the dry check of round 1.** It needs no network and makes no pod. It builds and checks the bundle and
prints the counts, the cap, the upper cost and the estimate. The bundle goes to `dry/sp-fiction-screen-r1/`. The
bundle's SHA-256 changes whenever the main checkout gets a new commit, because the job manifest records the engine's
git commit. The launch builds its own bundle again.

```zsh
setopt interactivecomments
K=/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-fiction-screen
cd "$K" && shasum -a 256 -c --quiet MANIFEST.sha256 && echo "manifest OK"
cd /private/tmp
date -u
bash "$K/sp_fiction_screen.sh" bundle 1
```

**Block 2: the round-1 launch.** Run it after the dry check looks right. The RunPod key comes from the secrets file
inside a subshell, and the HF token never reaches the launcher.

```zsh
setopt interactivecomments
K=/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-fiction-screen
cd /private/tmp
date -u
bash "$K/sp_fiction_screen.sh" launch 1
echo "exit $?"; date -u
```

**Block 3: the per-row files and the summary.** Run it after exit 0. It writes to the worktree's
`tmp/side-fiction/screen/`, the destination the spec names. `tmp/` is ignored by git there, and the step never
overwrites a file.

```zsh
setopt interactivecomments
K=/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-fiction-screen
bash "$K/sp_fiction_screen.sh" summarize 1
```

**Round 2.** The Side Project runs `sf_screen.py refill` on the Mac (CPU, no pod). It writes `refill-r2.jsonl` and its
report into the same screen folder:

```zsh
setopt interactivecomments
W=/Users/spiderishi/Coding/attribution/.claude/worktrees/peaceful-jepsen-8b8eee
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
S=$W/tmp/side-fiction/screen
cd /private/tmp
"$PY" -I -B "$W/research/side-fiction/scripts/v2/sf_screen.py" refill --screen "$S/round1-dark.jsonl" --screen "$S/round1-light.jsonl" --round 2
shasum -a 256 "$S/refill-r2.jsonl"
```

Then the lead runs the dry check and the launch with that SHA-256. The launcher also checks that
`refill-r2-report.json` names this file, its SHA-256 and its row count.

```zsh
setopt interactivecomments
K=/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-fiction-screen
R2='<the SHA-256 of refill-r2.jsonl>'
cd /private/tmp
bash "$K/sp_fiction_screen.sh" bundle 2 "$R2"
```

```zsh
setopt interactivecomments
K=/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-fiction-screen
R2='<the SHA-256 of refill-r2.jsonl>'
cd /private/tmp
bash "$K/sp_fiction_screen.sh" launch 2 "$R2"
echo "exit $?"
bash "$K/sp_fiction_screen.sh" summarize 2
```

**Round 3.** It runs only when `sf_screen.py finalize` stops because a dropped row has no clean candidate. The Side
Project then runs `refill` with these arguments:

- `--screen` with the two round-1 files;
- `--screen-refill "$S/round2-refill.jsonl"`;
- `--round 3 --offset 5 --k 10`.

The lead then repeats the two blocks above with `3` in place of `2`.

**The end.** The Side Project runs `sf_screen.py finalize` with these arguments:

- `--screen` with the two round-1 files;
- `--screen-refill` with each `roundN-refill.jsonl`.

It writes `tmp/side-fiction/final/`. Then this block writes `final-reads.json`. That file holds what the
pre-registration reads on the final training rows: the manipulation check, book concentration and the
sexual-content gate (§4).

```zsh
setopt interactivecomments
K=/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-fiction-screen
bash "$K/sp_fiction_screen.sh" final-reads
```

## The pod's layout

- **The bundle.** `bundle/gate_b/` is a bundle of the lead's Granite pod mode. The lead's own `bundle.stage_bundle`
  writes it on the Mac, with no requested unit and the known-answer gate on. It holds the lead's modules, the Mac's
  pinned Granite tokenizer folder (`granite-tokenizer/`), the gate's reference, unit and dev bank (`known/`), and the
  lead's own `job-manifest.json`. The screen's manifest records that manifest's SHA-256.
- **The lead's job.** `screen_run.sh` links `/workspace/judge/bundle` to `bundle/gate_b` and runs
  `bundle/gate_b/tool/pod/pod_run_granite.sh` in `/workspace/judge`, its default root, under one time limit of
  5,400 s. The lead's job writes its own `DONE.json`, `STEP` and `out/` there. `/workspace/screen/granite-job` links
  to that root, so the screen's status and fetch reach the lead's files.
- **A check of this layout on the Mac.** A test runs the lead's own `pod_job.py verify` through such a link, in an
  isolated stdlib interpreter. It accepts the bundle.

## What comes back, and where

- **Fetched by the launcher, automatically.** The files go to `runs/<tag>/fetched/`. Each one is checked against the
  SHA-256 computed on the pod, with 3 tries. The required files come first, in order:
  1. `DONE.json`;
  2. `out/run-record.json`;
  3. `out/ka.json`: the lead's gate block, its counts recounted, the gate's timing, the speed verdict, and the lead's
     exit code, step and build summary;
  4. `granite-job/out/run-record.json`: the lead's own run record (the gate block, the llama build, the files'
     SHA-256, the tokenizer fingerprint, the environment);
  5. `out/granite.jsonl` (per row and criterion: the label, attempts, the SHA-256 and token count of the text the
     model received, and the row's hashes);
  6. `out/qwen.jsonl` (per row: the safety label, categories, refusal flag and hashes).

  Then, best effort: the lead's `DONE.json`, `llama-build.json`, `gguf-check.json`, `environment-pod.lock`, `pip.log`
  and `llama-build.log` (all under `granite-job/`), and the guard's `download-check.json`, `environment-q.lock` and
  `pip.log`. No `job.log` is fetched.
- **Beside them.** The run folder also holds `screen-pod-result.json` (the exit code, the verification and the
  fetched hashes), `screen-pod-log.jsonl`, `bundle-record.json` and `rows-index.jsonl` (ids and hashes).
- **Copying back.** `summarize` reads the run folder and writes into `$W/tmp/side-fiction/screen/`:
  - `roundN-<source>.jsonl`: one line per row, in file order;
  - `roundN-summary.json`.

  No manual copy is needed. To keep the main checkout from writing into the worktree, run `tool/screen_pod.py
  summarize --from <run folder> --out <a folder of your choice>` instead, then `cp -n` the files into
  `$W/tmp/side-fiction/screen/`.
- **What a per-row line holds.**
  - Every line has `round`, `source`, `arm`, `line`, `row_id` and `response_sha256`.
  - Every line has `granite_harm` (Yes, No or invalid), `granite_harm_prob` (always null: the template gives no
    probability), `granite_sexual` and `drop`. Dolly rows have null in all four.
  - Every line has `qwen3guard_safety`, `qwen3guard_categories` and `qwen3guard_refusal`.
  - Round-1 fiction rows add `category`, and have no slot field: `sf_screen.py` then reads them as original-row labels.
  - Refill rows add `category`, `slot_arm`, `slot_line` and `rank`: `sf_screen.py` then reads them as candidate labels.
  - Dolly rows add `dolly_row_id`.
- **No text.** No output, log or record holds row, prompt, answer or judge-output text.

## What stops the job

| When | What | Exit |
|---|---|---|
| Before any pod | Any of these: a changed `SCREEN-SPEC.md` or `rules-v2.json`; a changed lead file (the 19 pins); a lead gate that is not the expected unit, reference and rule; an engine code identity other than the pinned `e49a978c…`; an input with another SHA-256 or row count; a Granite input above 8,160 tokens after the trim; a refill report not written by the pinned `sf_screen.py` (`165f1a30…`); uncommitted engine files; a secret pattern in the bundle; an existing tag folder; no RunPod key; `LIMIT` set on a launch (the script) | 2 |
| Budget | `budget.py check CAP 1.85` refuses (before the create), or `budget.py check 0 1.85` refuses right after it (the pod is stopped) | 3 |
| Create | RunPod refuses the create, or the pod's price is above the lead's $10/h limit or is not a number (the pod is stopped at once) | 4 |
| On the pod, setup | The guard venv or the Qwen3Guard download fails, or the lead's Granite job ends before its gate's verdict: its venv, pip, nvcc, the CUDA build, the GGUF download, or its own checks (the packages, the GPU offload, the files, the tokenizer fingerprint). `out/ka.json` records the lead's exit code and step. The pod is stopped. | 6 |
| On the pod, setup | **A setup step runs out of time.** The guard's steps run under `timeout -k 60`: the venv and freezes 600 s, the pip install 1,800 s, a torch install 2,400 s, the download 3,600 s. The lead's whole Granite job runs under one limit of 5,400 s (its own script has none). `DONE.json` then records exit 124 (137 when the step ignored SIGTERM). The pod is stopped through the normal path, not at the cap. | 6 |
| On the pod, before any fiction row | **THE KNOWN-ANSWER GATE FAILS** (see below). The lead's job exits 3 at its step `run`, and the screen's `ka` step exits 4. No row is screened, the pod is stopped, and nothing from the run is used. | **8** |
| On the pod, before any fiction row | **THE ROUND IS PROJECTED TOO SLOW.** The gate passes, but its measured seconds per answer × r is above 0.4 s, the cap's planning time per Granite call (pod step `ka`, exit 3). r is the round's mean tokens per Granite call divided by the known answers' mean template tokens: in round 1, 196.7 / 421.3, so r = 0.467. No row is screened and the pod is stopped. Decide the cap or the planning time before a relaunch. | **9** |
| The cap | The screen's steps and the lead's gate get SIGTERM 5 min before the cap; the partial caches are fetched. Resume with `RESUME=<old tag> TAG=<new tag>`. | 5 |
| A stop that is not confirmed, or a lost create reply | `STOP-NOT-CONFIRMED` or `CHECK-CONSOLE`: check the RunPod console now | 7 |

Exit codes 0 to 7 mean what they mean in `judge_pod.py`. Codes 8 and 9 are the screen's. A lead job that ends before
its gate's verdict exits 6 or 5, not 8, because nothing was compared. A verdict is only the lead's exit 0 at its step
`done` or exit 3 at its step `run`: pip's own exit 3 at the step `pip` is not a failed gate.

**The engine identity in the launch outputs.** Before any job starts, `bundle-record.json` (in `dry/<tag>/` and
`runs/<tag>/`) records the engine's code identity, which must be the pinned `e49a978c…`. It also records the SHA-256
of every shipped engine file and the engine files changed since commit `8801456` (from
`git diff --name-only 8801456 HEAD -- experiments/`). At 17:46 UTC on 9 Oct that list held four files: the Llama
recipe-B rung-2 config `study-kt-llama32-1b-r64-b5e5-mb4-20261008.json` and three test files. They are recorded, not
refused, and the code identity is still `e49a978c…`.

## The known-answer gate (the lead's)

The gate is the lead's `pod_job.known_answer_gate`. The lead's own job runs it on the pod in every launch, before any
fiction row. The screen does not judge any known answer itself, so the gate runs once.

- **The same unit and rule as the screen's former check.** Granite (`harm`) judges the 200 greedy harm answers of the
  OLMo-2-1B recipe-B seed-1101 e1 unit (`1101-a0-e1-a1`, COMPLETE.json `8f0fa83a…`), with the same model load,
  prompt, token check, call and parse as the fiction rows. The reference is the lead's `granite-known-answers.json`
  (`b5b2678e…`: prompt ids, answer SHA-256 and the Mac's labels, 93 yes and 107 no).
- **The rule, fixed before any run.** All 200 must be judged, at least 190 labels must equal the Mac's, and |pod yes −
  Mac yes| ≤ 5. A pod "unparsed" label counts as differing.
- **Checked when the bundle is built.** The builder refuses unless the lead's gate is exactly this unit, reference and
  rule (`granite_pod`'s constants and its `plan_known_answers`).
- **Where it is applied.**
  - On the pod, by the lead's job: a fail ends it with exit 3 before any requested work.
  - On the pod, by the screen's `ka` step: it checks that the lead's run record is a cuda Granite run of this bundle's
    `gate_b` with that exit code, recounts the block's counts from its own differing ids and flips against the
    reference, and applies the rule again. `granite` and `qwen` refuse unless `out/ka.json` holds a pass that its
    counts support.
  - On the Mac, by the launcher: the block in `ka.json` must be the one in the lead's fetched run record, it must pass
    the lead's consistency check (`judge_pod.known_answer_problem`), and its counts are recounted and the rule is
    applied again. A fail there is exit 8 too. `summarize` recounts a third time against the lead's pinned
    reference.
- **The gate's speed.** The lead's gate records no timing. The `ka` step reads it from the lead's `job.log`: from the
  `granite_precheck` line, logged right before the model loads, to the gate's last line. The stamps are to the
  second, and the interval includes the model load, so the measured time per answer errs high: the speed stop errs
  toward stopping.
- **Where it is recorded.** `out/ka.json` holds the lead's block (counts, flips, the differing ids, the verdict), the
  timing and the speed verdict. The run record, `screen-pod-result.json` (verification `ka`) and
  `roundN-summary.json` (`known_answer`) carry it too.

## The Granite backend (the lead's)

- **One path.** The screen calls `granite_pod.judge_triples([(row id, user turn, response)], criteria, session=...)`
  with one `GraniteSession` for the whole step. The session checks the tokenizer folder and the GGUF by SHA-256
  before any load, refuses a tokenizer whose fingerprint is not the Mac's (`5354502d…`), counts every input before
  the model loads (above 8,160 tokens refuses), loads the model once, and makes the lead's call and parse.
- **Before judging,** the step checks the packages (`granite_pod.require_granite_packages`) and that llama.cpp can
  offload to the GPU (`llama_info()["gpu_offload"]`). Otherwise it refuses and judges nothing.
- **The prompt.** The lead's `granite_files.granite_input` with `criteria_id` "harm" (its bytes pinned by the lead) or
  "sexual_content". The user turn is the engine's `render_user_text` (`instruction-blank-line-context`), imported
  unchanged. Per row, `harm` comes first, then `sexual_content`, so the second call can reuse the conversation's
  prefix.
- **The labels.** The lead's `yes`, `no` and `unparsed` become Yes, No and invalid.
- **What the screen adds.** One retry of an unparsed label (SCREEN-SPEC §2): a second `judge_triples` call. A label
  still unparsed is invalid, and the drop rule drops it. A call that raises ends the step (exit 1): no row is
  labelled invalid for an error.
- **The model, the build and the venv** are the lead's: `ibm-granite/granite-guardian-3.3-8b-GGUF@8c87479a`,
  `granite-guardian-3.3-8b-Q4_K_M.gguf`, SHA-256 `b4fa861b…`; llama-cpp-python 0.3.36 built on the pod from the PyPI
  sdist (`832db069…`) with `CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80"` and at most 16 build jobs; the
  Mac judge venv's 30 packages in `/root/granite-venv`.
- **Proof of the bytes.** In the Mac's judge venv (transformers 5.18.0, tokenizers 0.23.2, the pinned tokenizer
  folder, offline, no model), three paths built byte-identical prompt text: the triples path the pod runs
  (`judge_triples` through a real `GraniteSession`), the screen's own builder before the refactor (commit `e3ce85b`,
  file SHA-256 `501eb4a2…`), and `second_judge_probe.py` (`c51e466c…`). The cases were 6 synthetic fixtures (one
  trimmed), **all 10,000 real fiction rows** and all 200 known answers: `harm` identical on all three paths,
  `sexual_content` identical to the previous builder, and every `input_sha256` that `judge_triples` returned equal to
  the SHA-256 of the text the model received. The constructor and call arguments and the label parse are the
  probe's too.
- **Parity of the lead's path.** The lead's pre-set Granite parity rule is in `pod/PARITY.md` (SHA-256 `c4fc455e…`,
  recorded in `research/FOCUS.md` at `019a72e`): four OLMo-2-1B Gate A units, rule 0 (identical tokenizer fingerprint
  and every input SHA-256), then per unit at least 196 of 200 identical labels and |Δyes| ≤ 3. **The lead's Granite
  parity PASSED** on 9 Oct at 17:22 UTC (`research/FOCUS.md` commit `2837eaf`; pod `granite-parity-2`; report
  `tmp/judge-pod/granite-parity-2/granite-parity-report.json`, SHA-256 `6234328f…`):
  - rule 0 held: all 800 input SHA-256 identical, the tokenizer fingerprint `5354502d…` on both sides, and no
    token-count difference;
  - identical labels per unit: untuned 200/200 (5 yes on both sides), e1-1101 200/200 (93; this is the gate's own
    unit), e1-1102 199/200 (one no→yes: 86 on the Mac, 87 on the pod), e1-1103 200/200 (94);
  - the lead's FOCUS line gives about 0.3 s per item on that pod.

  Each pod builds llama.cpp again, so the screen still runs the lead's gate on every pod.

## Tests

```zsh
setopt interactivecomments
K=/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-fiction-screen
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
S=$(mktemp -d /private/tmp/sp-fiction-screen-tests.XXXXXX)
cd /private/tmp && PYTHONDONTWRITEBYTECODE=1 SCREEN_SLOW=1 "$PY" -B -m pytest -q -p no:cacheprovider --basetemp="$S/bt" "$K/tests"
rm -rf "$S"
```

- **No pod, no network, no model.** The tests use fakes for the pod host, the model (behind the lead's real
  `GraniteSession`) and the GuardScorer. The lead's real gate (`pod_job.py run` on the bundle's `gate_b`) and the
  lead's real `pod_run_granite.sh` (with fake binaries) run in the tests.
- **The real inputs.** Where the real inputs are on the Mac, the tests read them, but they write only labels, ids and
  hashes. Bundles go to pytest's temporary folder.
- **The real-tokenizer test.** It runs the Mac's judge venv in a subprocess, and reads the previous builder from git
  (commit `e3ce85b`, pinned by SHA-256).
- **`SCREEN_SLOW=1`.** This adds the full round trip through the real `sf_screen.py` (refill, then finalize), about 30
  s.

Results on 9 October 2026, after the refactor (clock checked):

- **The full suite.** 175 passed in the development copy (17:49 UTC) and 175 passed in this launch folder
  (17:52 UTC), with `SCREEN_SLOW=1`, about 2 min each, none skipped. After the parity update, the quick suite (no
  `SCREEN_SLOW`) passed again in both copies, 17:56 to 18:00 UTC: 174 passed and 1 skipped (the slow round trip).
- **The secret scan.** A separate scan of every file in both copies with the kits' patterns found nothing. The suite
  also scans the bundle and the outputs.
- **The byte identity** with all rows: 10,000 of 10,000 real rows and 200 of 200 known answers identical on the
  three paths (see above), and no row trimmed.
- **The dry bundle of round 1, rebuilt.** It holds 218 files plus its manifest (6.5 MB) and is deterministic (two
  builds, one SHA-256). Its secret scan is clean. Its `gate_b/` is the lead's bundle; it names the engine identity
  `e49a978c…`. Its token ratio is r = 0.467 (196.7 / 421.3), as before the refactor; the longest Granite input is
  2,686 tokens, and none is trimmed. Its own code verified it in the pod layout, and the lead's `pod_job.py verify`
  accepted its `gate_b/` through the `/workspace/judge/bundle` link, under the Mac's system Python 3.9.
- **A mutation check of 22 new rules.** Each mutant ran in its own copy, and the relevant test files ran with the
  same command as a clean baseline. All 22 were killed by real test failures:
  - the gate's exit 4, its recount and rule on the pod, the lead record's `gate_b`, the verdict only at the lead's
    step `run`, and a stopped lead job;
  - the GPU-offload check, the tokenizer fingerprint, the retry and the `harm`-then-`sexual_content` order;
  - the lead-file pins, the gate on, and the lead's rule;
  - the timing from the precheck line, and the projection by r;
  - the terminate command, the lead job's time limit, its exit code to `ka`, and the `gate_b` link;
  - the Mac's check of the block against the lead's record, the Mac's recount for exit 8, and `granite` without
    the gate.

## What could not be tested without a GPU or a pod (for the review)

**Nothing of this job ran on a pod.** The lead's Granite mode itself has run on a pod (its parity, above). The untested
pod-side steps of this job are:

- the RunPod API, ssh and scp;
- the lead's Granite job on a real pod: the CUDA build of llama-cpp-python, whether the image
  (`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`) carries `nvcc`, the apt fallback, pip wheel availability for
  Python 3.12, the GGUF download, the GPU offload, and the gate's agreement on this job's own pod (the lead's
  parity pod gave 200 of 200 on the gate's unit);
- the links `/workspace/judge/bundle` and `/workspace/screen/granite-job` on the pod's file system (tested on the
  Mac's);
- Qwen3Guard on CUDA through `configure_cuda`;
- the real timings (every time and cost figure above is an estimate);
- `pkill` on the pod.

## Open risks for the independent review

1. **CUDA against Metal on the known answers.**
   - The gate needs 190 of 200 labels to agree. The parity of the HarmBench judge (fp16) was 200 of 200.
   - Granite here runs at 4-bit, on other kernels, with a different prefix-cache history. The lead's Granite parity
     pod measured the agreement on 9 Oct: 799 of 800 labels identical over four units, and 200 of 200 on the gate's
     own unit (PASS). Each new pod has a new build, so the gate checks it again on every run.
   - A fail costs about $1 (setup plus 200 calls) and stops the round by design.
2. **The speed reading.** The gate's time comes from the lead's log stamps, to the second, and includes the model
   load. Over 200 answers that adds about 0.01 to 0.05 s per answer. The stop is at 0.4 / 0.467 = 0.86 s per answer,
   about 3 to 7 times the estimate and about 3 times the lead's parity pod (about 0.3 s per item), so a false stop is
   unlikely. If the lead's log format changes, the reading fails
   and the run stops (exit 9) rather than run untimed; the lead's files are pinned, so that needs a new review first.
3. **The retry.** The lead's API has no reset hook. A retry is the same call again, and llama.cpp may reuse the cached
   prefix, so a retry rarely changes an unparsed output. The old screen reset the model first.
4. **Build tools.** The sdist's build dependencies (scikit-build-core, cmake, ninja) come through pip's isolated build
   and are not hash-pinned (a pip limitation). The lead's `llama-build.log` records them, and its SHA-256 is in the
   lead's build record.
5. **Setup time and hangs.** Setup time is unmeasured for this job. The 5.0 h cap leaves about 1.8 h over the high
   estimate. The lead's job has one time limit (5,400 s), not one per step: a hang there costs at most 1.5 h.
6. **The run's outputs are only part of the screen.** Round 1's `reads` are a preview on the round-1 rows. The
   pre-registered reads are on the final rows (`final-reads`, after finalize).
7. **The pins.** The launcher pins these files:
   - `SCREEN-SPEC.md` at `81dc487a…` and `rules-v2.json` at `c23672cf…`;
   - the 19 lead files at `2694bd0`;
   - the engine code identity at `e49a978c…`;
   - the refill tool `sf_screen.py` at `165f1a30…`.

   If any of these changes, the launcher refuses until the build is checked against the new version.

## Residual risks (the independent review's note, 9 Oct, updated for the refactor)

- **CUDA against Metal: measured once, checked on every pod.** The lead's parity pod (the stricter PARITY.md rule)
  passed on 9 Oct: 799 of 800 identical labels and 800 of 800 identical inputs (FOCUS `2837eaf`). Each new pod builds
  llama.cpp again, so the lead's gate checks it on every pod: 190 of 200 identical and |Δyes| ≤ 5, or no row is
  screened.
- **No reference for `sexual_content`.** The known answers check `harm` only; the `sexual_content` pass (report only,
  and the drop rule only under rules-v3) has no known-answer reference on either device. Its prompt bytes equal the
  previous builder's on all 10,000 rows.
- **Watch Granite's speed.** `ka.json` (`timing`, `speed`), the log's `verified` line and `roundN-summary.json`
  record:
  - r and both token means (`bundle-record.json` shows them before any spend);
  - the pod's longest known-answer input in tokens (from the lead's log), a check on the bundle's count;
  - the measured seconds per known answer;
  - the projected seconds per Granite call and the projected Granite minutes of the round.

  Above 0.4 s per call projected, the job stops (exit 9). The projection scales the whole measured time by r. A fixed
  cost per call (generation, Python) does not shrink with fewer tokens, so the projection can be low. The poll's
  `progress` and `cap-risk` lines show the real rate.
- **Row text stays until cleanup.** It remains in these places until someone removes it:
  - `runs/<tag>/bundle.tar.gz` and `dry/<tag>/bundle.tar.gz` in this folder (the bundles carry the inputs);
  - the stopped pod's volume (`/workspace/screen/bundle/`), until the pod is deleted (a deletion needs the user's
    go);
  - the Hub cache on the container disk, which goes with the pod.

  Every output, log and record holds labels, ids, counts and hashes only. Delete the bundle tars once the screen is
  final and backed up.
