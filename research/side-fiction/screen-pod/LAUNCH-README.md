# Fiction training-data screen: the launch folder

Written 9 October 2026, 11:05 UTC (clock checked), by the Side Project's Opus worker, for the lead (General
Implementation IV). It implements `research/side-fiction/SCREEN-SPEC.md` (SHA-256 `19cae3e1…`, sections 1 to 7) in the
Side Project's worktree.

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
  1. The known-answer check (200 Granite calls).
  2. Granite Guardian 3.3 8B on the 10,000 fiction rows, with two passes per row: `harm` (the drop rule) and
     `sexual_content` (report only).
  3. Qwen3Guard-Gen-4B, through the engine's GuardScorer, on the 10,000 fiction rows and the 4,800 Dolly train rows.
- **Rounds 2 and 3.** The same steps on the `refill-rN.jsonl` that `sf_screen.py refill` wrote.
- **What the launch reuses.** The reviewed judge-pod launcher (`scripts/gate_b_mac_judges/pod/`), by import and
  unchanged:
  - `podhost.py`: the budget lock and guard, reconcile, create with the in-pod timer, the orphan check, and the stop;
  - `judge_pod.py`'s helpers: the signals, the log, the fetch with retries, and the salvage.
- **The pins on the launcher.** Every launcher module is pinned by SHA-256 as committed. A changed file refuses with
  exit 2.

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

## Cap and cost (planning rate $1.85/h, reserve $1)

**Round 1** makes 20,200 Granite calls (200 known answers, plus 2 × 10,000 rows) and judges 14,800 Qwen3Guard rows.

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
  The `sexual_content` call adds 101 tokens after the prefix it shares with the `harm` call.
- **Qwen3Guard.** The input averages 529 to 590 tokens (maximum 2,509). None is over the limit of 8,192, and none
  holds a control string.

From those counts, the estimates per item and for setup are:

- **Per item.** 0.12 to 0.30 s per Granite call on CUDA, and 0.08 to 0.17 s per Qwen3Guard row (gate A measured
  0.165 s at batch 8).
- **Setup.** 20 to 45 min: two venvs, the llama.cpp CUDA build, and 13.7 GB of downloads. On the 8 Oct judge pod, a
  pip install into `/workspace` took 14 min, so both venvs here sit on the container disk.

**Rounds 2 and 3.** The cap comes from the refill file's row count. Some examples:

| Refill rows | Cap | Upper cost |
|---|---|---|
| 15 (3 drops × 5 candidates) | 1.5 h | $2.78 |
| 1,000 | 2.0 h | $3.70 |
| 4,250 (850 drops × 5) | 3.0 h | $5.55 |

Each round runs the known-answer check again, because each round is a new pod with a new build.

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

## What comes back, and where

- **Fetched by the launcher, automatically.** The files go to `runs/<tag>/fetched/`. Each one is checked against the
  SHA-256 computed on the pod, with 3 tries. The required files come first, in order:
  1. `DONE.json`;
  2. `out/run-record.json`;
  3. `out/ka.json` and `out/ka-labels.jsonl` (the known-answer counts, then ids and labels);
  4. `out/granite.jsonl` (per row and criteria: the label, attempts, token count and hashes);
  5. `out/qwen.jsonl` (per row: the safety label, categories, refusal flag and hashes).

  Then, best effort: `download-check.json`, `llama-info.json` (the version, GPU offload, nvcc and the build log's
  SHA-256), the two `environment-*.lock` files, `pip.log` and `llama-build.log`.
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
| Before any pod | Any of these: a changed `SCREEN-SPEC.md`, `rules-v2.json` or reused launcher module; an input with another SHA-256 or row count; the known-answer unit or the Mac labels not as pinned; uncommitted engine files; a secret pattern in the bundle; an existing tag folder; no RunPod key | 2 |
| Budget | `budget.py check CAP 1.85` refuses (before the create), or `budget.py check 0 1.85` refuses right after it (the pod is stopped) | 3 |
| On the pod, setup | llama-cpp-python is not 0.3.36 built with GPU offload and the pinned CMAKE_ARGS, a pin fails, a download hash differs, or a step errors. The pod is stopped. | 6 |
| On the pod, before any fiction row | **The GPU-speed guard.** The first 5 known answers average more than 3 s each, which means llama.cpp is not on the GPU. The pod is stopped. | 6 |
| On the pod, before any fiction row | **THE KNOWN-ANSWER CHECK FAILS** (see below). No row is screened, the pod is stopped, and nothing from the run is used. | **8** |
| The cap | The job steps get SIGTERM 5 min before the cap; the partial caches are fetched. Resume with `RESUME=<old tag> TAG=<new tag>`. | 5 |
| A stop that is not confirmed, or a lost create reply | `STOP-NOT-CONFIRMED` or `CHECK-CONSOLE`: check the RunPod console now | 7 |

Exit codes 0 to 7 mean what they mean in `judge_pod.py`. Code 8 is new. A known-answer step that breaks, is refused
or is stopped before its verdict exits 6 or 5, not 8, because nothing was compared.

## The known-answer check

The check runs on the pod in every launch, before any fiction row:

- **Items and model.** Granite (`harm`) judges the 200 greedy harm answers of the OLMo-2-1B recipe-B seed-1101 e1
  unit (`tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1`). It uses the screen's own
  code and model.
- **Mac labels.** The Mac's Granite labelled the same unit in the kit's second-judge files:
  - `tmp/family-probe-olmo2-1b/second-judge-probe-items.jsonl`, SHA-256 `c2ef1130…`, which gives 93 yes, 107 no and
    0 unparsed;
  - `second-judge-probe-summary.json`, SHA-256 `be2b4286…`, which names the unit's `job.json`.

  Only the unit, prompt id, target and label fields are read; the `raw` field is never touched.
- **Same order and inputs as the Mac.** The answers are judged in prompt-id order, as the Mac judged them. The
  prompts come from the dev bank and the answers from the unit, both hash-checked. A test confirmed that the screen's
  inputs and prompt bytes equal the Mac probe's for all 200 items.
- **The rule, fixed before any run.** All 200 must be judged, at least 190 labels must equal the Mac's, and |pod yes −
  Mac yes| ≤ 5. A pod "invalid" label counts as differing.
- **Where it is applied.** On the pod: a fail exits the step with code 4, the job ends, and `granite` and `qwen`
  refuse unless `ka.json` holds a pass that its own counts support. On the Mac, again: the launcher recounts the
  fetched labels against its own copy of the Mac labels. A disagreement is a fail (exit 8). `summarize` recounts a
  third time against the pinned Mac file.
- **Where it is recorded.** `out/ka.json` holds the counts, flips, seconds per answer and verdict. The run record,
  `screen-pod-result.json` (verification `ka`) and `roundN-summary.json` (`known_answer`) carry it too.

## The Granite calling convention (unchanged from `second_judge_probe.py`, SHA-256 `c51e466c…`)

- **The model.** The same GGUF as the Mac: `ibm-granite/granite-guardian-3.3-8b-GGUF@8c87479a`,
  `granite-guardian-3.3-8b-Q4_K_M.gguf`, SHA-256 `b4fa861b…`. It is checked on the pod before it loads.
- **The tokenizer folder.** Its ten files are pinned, and they equal the Mac's copy.
- **The call.** `Llama(model_path, n_gpu_layers=-1, n_ctx=8192, seed=0, verbose=False, logits_all=False)`; the chat
  template with `guardian_config={"criteria_id": C}`, `think=False` and `add_generation_prompt=True`; the probe's
  trim above 8,000 tokens; `llm(text, max_tokens=32, temperature=0.0, top_k=1)`; and the last `<score>…</score>`.
- **What the screen adds.** One retry, after `llm.reset()`, of an invalid label. A label still invalid stays invalid,
  and the drop rule drops it.
- **The user turn.** The engine's `render_user_text` (`instruction-blank-line-context`), imported unchanged.
- **Proof of the bytes.** In the Mac's judge venv (transformers 5.18.0, tokenizers 0.23.2, the pinned tokenizer
  folder, offline, no model), the screen and `second_judge_probe.py` built byte-identical prompt text, constructor
  arguments and call arguments. The cases were 6 synthetic fixtures (one trimmed), **all 10,000 real fiction rows**
  and all 200 known answers (`tests/granite_parity_helper.py --rows 0`).
- **The build.** llama-cpp-python 0.3.36, as in the judge venv, from the PyPI sdist (SHA-256 `832db069…`,
  `--require-hashes`). It is built on the pod with `CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80"`, and the
  build log's SHA-256 is recorded.

## Tests

```zsh
setopt interactivecomments
K=/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-fiction-screen
PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
S=$(mktemp -d /private/tmp/sp-fiction-screen-tests.XXXXXX)
cd /private/tmp && PYTHONDONTWRITEBYTECODE=1 SCREEN_SLOW=1 "$PY" -B -m pytest -q -p no:cacheprovider --basetemp="$S/bt" "$K/tests"
rm -rf "$S"
```

- **No pod, no network, no model.** The tests use fakes for the pod host, the Granite judge and the GuardScorer.
- **The real inputs.** Where the real inputs are on the Mac, the tests read them, but they write only labels, ids and
  hashes. Bundles go to pytest's temporary folder.
- **The real-tokenizer test.** It runs the Mac's judge venv in a subprocess.
- **`SCREEN_SLOW=1`.** This adds the full round trip through the real `sf_screen.py` (refill, then finalize), about 30
  s.

Results on 9 October 2026 (development copy 11:21 UTC, launch folder 11:23 UTC; clock checked):

- **The full suite.** 148 passed in the development copy, and again in this launch folder, with `SCREEN_SLOW=1`
  (about 2.5 min each).
- **The Granite parity** with `--rows 0`: 10,000 of 10,000 real rows and 200 of 200 known answers byte-identical to
  `second_judge_probe.py`, and no row trimmed.
- **The dry bundle of round 1.** It holds 192 files (5.2 MB) and is deterministic. Its secret scan is clean. Its own
  code verified it in the pod layout under the Mac's system Python 3.9 (stdlib only).
- **A mutation check of 20 key rules.** Each mutant ran in its own copy, and the relevant test files ran with the
  same command as a clean baseline. All 20 were killed by real test failures. The mutated rules were:
  - the known-answer thresholds (190 and 5), its gate, its order, the Mac recount and exit 8;
  - the drop rule, the retry, `think=False` and the user turn;
  - the refill slot fields, and the round-1 rows carrying no slot key;
  - `CUBLAS_WORKSPACE_CONFIG`, the input hash check and the status `step` collision;
  - the guard answer staying out of the cache, the launcher and spec pins, the GPU-speed guard, and the
    `sexual_content` pass.

## What could not be tested without a GPU or a pod (for the review)

**Nothing on the pod ran.** The untested pod-side steps are:

- the RunPod API, ssh and scp;
- the CUDA build of llama-cpp-python, and whether the image (`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`)
  carries `nvcc`;
- the apt fallback for `nvcc`;
- pip wheel availability for Python 3.12 under `--only-binary=:all:`;
- the Hub downloads, the GGUF load and GPU offload;
- the real known-answer agreement of CUDA numerics with the Mac's Metal labels;
- Qwen3Guard on CUDA through `configure_cuda`;
- the real timings (every time and cost figure above is an estimate);
- `pkill` on the pod.

## Open risks for the independent review

1. **CUDA against Metal on the known answers.**
   - The rule needs 190 of 200 labels to agree. The parity of the HarmBench judge (fp16) was 200 of 200.
   - Granite here runs at 4-bit, on other kernels, with a different prefix-cache history. Agreement is likely but
     unmeasured.
   - A fail costs about $1 (setup plus 200 calls) and stops the round by design.
2. **`nvcc` on the image.**
   - If the image is not a CUDA devel image, the build first tries the CUDA 12.8 compiler packages from the image's
     apt sources (`cuda-nvcc-12-8`, `cuda-cudart-dev-12-8`, `libcublas-dev-12-8`, `cuda-driver-dev-12-8`,
     `build-essential`). These versions are unpinned, but `llama-info.json` records them (nvcc release, nvcc source).
   - If there are no CUDA apt sources, the job stops at `llama-build` (exit 6, about 10 min, about $0.30).
3. **Build tools.** The sdist's build dependencies (scikit-build-core, cmake, ninja) come through pip's isolated build
   and are not hash-pinned (a pip limitation). Their versions appear in `llama-build.log`, whose SHA-256 is recorded.
4. **Setup time and hangs.** Setup time is unmeasured for this job. The 5.0 h cap leaves about 1.8 h over the high
   estimate. A job that hangs without writing `DONE.json` runs until 5 min before the cap, as in the judge pod; the
   log's `cap-risk` line and the progress lines show it.
5. **The run's outputs are only part of the screen.** Round 1's `reads` are a preview on the round-1 rows. The
   pre-registered reads are on the final rows (`final-reads`, after finalize).
6. **The spec pin.** The launcher pins `SCREEN-SPEC.md` at `19cae3e1…` and `rules-v2.json` at `c23672cf…`. If either
   changes, the launcher refuses until the build is checked against the new version.
