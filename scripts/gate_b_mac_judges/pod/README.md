# The HarmBench judge on one RunPod A100 (pod path)

Written 8 October 2026, 20:07 UTC (clock checked), by an Opus builder for the lead. Revised 8 October 2026, 21:00 UTC
(clock checked), after the review: stop safety (S1), one launch per tag and the budget guard's view (S2), fetch
retries (S3), orphan stops (S4), the price rule (S5), torch and the text path (S6), and zsh-safe commands (S7).
Revised again 8 October 2026, 21:59 UTC (clock checked), after the second review (F1 to F13): SIGQUIT and the
interrupt line, nohup, a dead terminal or pipe at exit, the fetch order, the salvage's time budget, orphan names, a
lost create reply, record appends, the budget check after the create (the lead's decision), smoke-run verdicts, the
parity cache check, and `setopt interactivecomments` in every zsh block.
Revised a third time 8 October 2026, 22:45 UTC (clock checked), after the third review (G1 to G6): a reconcile cut
short by a signal runs again in `finally`, an orphan stop on a full disk stays confirmed, a 5xx create reply counts as
lost (the lead's decision), a `budget.py` that hangs or cannot start is a refusal, the exit-4 row, and the limits the
lead decided to document (see "Limits").
Revised 9 October 2026, 13:05 UTC (clock checked): the judge selector `--judge harmbench|granite` and the Granite
judge on the pod (see "The Granite judge on the pod"). Without `--judge`, everything below is the HarmBench path as
before. Revised 9 October 2026, 13:59 UTC (clock checked), after the Granite review: the CUDA build's parallel jobs
are bounded at 16 and recorded with its seconds, the apt fallback adds the libcuda stub, a refused Granite download
still writes `out/gguf-check.json`, the pre-run refusals' exit-code text, and Granite tests for the salvage, the cap
constant, the run record's device and the download's checks. Revised 9 October 2026, 15:30 UTC (clock checked), the
second Granite round: the known-answer gate (on by default for `--judge granite`, exit 8 when it fails), the inputs
rows keyed per item, the Granite judge's criterion as a parameter (`granite_files.py`, default "harm") and the generic
entry point `granite_pod.judge_triples` (for the Side Project's screen), the run record's measured GGUF and GPU offload
in `parity.py granite`, and the review's test gaps (see "The Granite judge on the pod").
The user asked for this so that the HarmBench judge does not have to wait for the Mac GPU while AIMO runs.
Builder status: built and tested with fakes only. No pod, RunPod API call, Hub download, model load or GPU process was
started. The dev bank was never opened. Nothing here authorizes a run: the lead launches after review.

**Before the first launch, the lead records `PARITY.md`'s SHA-256 in `research/FOCUS.md`** (the builder does not edit
FOCUS). The pre-set parity rule is then fixed by that hash.

## What it does

`judge_pod.py launch` runs the existing HarmBench judge of `harmbench_files.py` on one A100 instead of the Mac's MPS.
It writes the same per-item cache that the Mac judge writes, so `write_files.py` turns it into the same judge files.
The scale of the speed-up:

- Gate B: about 29 arms × 800 answers.
- Tonight's side project: 5,600 items.
- The Mac measured 4.9 to 5.6 s per answer. The pod estimate is 0.06 to 0.12 s per answer (see "Time and cost").

| File | Runs on | Role |
|---|---|---|
| `pod_judge.py` | Mac (tests) and pod | The device-parametric judge. `"mps"` is `harmbench_files.harmbench_judge` itself, unchanged. `"cuda"` imports every pinned piece from `harmbench_files` and changes only the device. Also holds the snapshot pins (10 files, SHA-256), the package pins (and the refusal of sentencepiece and protobuf), the tokenizer fingerprint and the run-record environment. |
| `pod_job.py` | pod | Commands `verify`, `download`, `run`, `status` and `sums` (see below). |
| `bundle.py` | Mac and pod | Builds the bundle and its job manifest (Mac). Verifies the bundle and rebuilds `units.Unit` objects (pod). |
| `podhost.py` | Mac | The RunPod host layer, adapted from the kit's `host.py` (SHA-256 `29ac283b…`) and `orchestrate.py` (`30f9fbe0…`). Holds the budget lock and guard, reconcile, create (price check, pod timer), orphan stops, SSH, send, fetch and stop. Its records are in `tmp/family-probe-judge/hosts/judge-<tag>/`. |
| `judge_pod.py` | Mac | The lead's launcher (`bundle`, `launch`). A launch's folder is `tmp/judge-pod/<tag>`. |
| `pod_run.sh` | pod | The job under nohup: `venv`, `torch`, `pip`, `download`, then `run`. Writes `DONE.json` with the exit code and step. |
| `judge-requirements.txt` | pod | The judge's packages at the Mac venv's versions. `torch` comes from the image, or from the PyTorch cu128 index when the image's is missing or not 2.8.0. |
| `extend_cap.py` | pod | A verbatim copy of the kit's `setup/extend_cap.py` (`8af2f6cc…`), used only to shorten the pod timer when a stop is not confirmed. |
| `parity.py`, `PARITY.md` | Mac | The Mac-versus-pod parity check and its pre-set rule; `parity.py granite` and `PARITY.md` "Granite parity" for Granite (run under the judge venv). |
| `granite_pod.py` | Mac (tests, parity) and pod | The Granite judge on the pod: `granite_files.granite_judge` with the pod's paths, the GGUF, tokenizer, package and llama.cpp pins and checks, the inputs file, and the build steps (`fetch-sdist`, `llama-record`). |
| `pod_run_granite.sh` | pod | The Granite job under nohup: `venv` (its own), `pip`, `nvcc`, `llama` (the CUDA build), `download`, `run`. |
| `granite-requirements.txt` | pod | The Mac judge venv's 30 distributions at their versions (llama-cpp-python is built). |
| `../tests/test_judge_pod.py` | Mac (minimal venv) | 162 tests with fakes (the HarmBench path; unchanged). |
| `../tests/test_granite_pod.py` | Mac (minimal venv) | The Granite path's tests with fakes (see "Tests"). |

## The judge is unchanged; only the device differs

These parts are the same objects as in `harmbench_files.py` (identity tests) or the same syntax trees (syntax-tree
tests). `harmbench_files.py` itself is not changed. All 83 earlier tests pass as they were, including
`test_port_fidelity.py`.

- The revision `51182c7c…`.
- `load_template`: model-card template SHA-256 `c1c47e30…`.
- `load_tokenizer`: `tokenizer.model` SHA-256 `dadfd56d…`, LlamaConverter with legacy=True and add_prefix_space=True,
  truncation side right.
- `clip_generation`: 512 tokens with BOS.
- The 2048-token input cap, checked before the model loads.
- `label_from_token`: one decoded token, lower-cased; non-finite logits give `unparsed`.
- The model load: the same `from_pretrained` call (float16, `low_cpu_mem_usage=True`) with `device_map="cuda"` instead
  of `"mps"`, and the same "entirely float16 on one device" refusal.
- The judge's forward pass: every statement of the Mac `judge()`, with `ids.to(device)` and `torch.cuda.empty_cache()`
  every 25 items. Only the memory log line differs.

The pod also checks these things:

- **The snapshot.** The ten files (14.5 GB) are pinned by SHA-256. The pins were read on 8 Oct from the Mac's
  snapshot, whose blob names equal their content hashes. The pod refuses a missing, extra or different file.
- **The packages.** `transformers` 4.56.2, `tokenizers` 0.22.2, `huggingface_hub` 0.36.2, `safetensors` 0.8.0,
  `accelerate` 1.15.0, `numpy` 2.2.6 and `regex` 2026.9.29 must match exactly. `torch` must be 2.8.0 by its public
  version; the image's local label (for example `+cu128`) is recorded.
- **The text path.** The Mac venv has neither `sentencepiece` nor `protobuf`, so `harmbench_files.load_tokenizer`
  builds the tokenizer through its pure-Python SentencePiece reader. The pod refuses when either package is installed.
  The run record holds the tokenizer fingerprint: the SHA-256 of the built tokenizer's vocab and merges as canonical
  JSON. `parity.py` compares it with the Mac's.

The other differences from the Mac are recorded in the run record: the Linux build of the same package versions, the
image's Python and CUDA 12.8, whether the venv uses the image's site-packages, the attention implementation chosen by
default, and the torch matmul flags. The parity check measures their effect (`PARITY.md`).

## Flow of `launch`

0. **The tag.** The launch takes an exclusive, non-blocking lock on `tmp/judge-pod/<tag>.lock` and holds it to the
   end. A second launch with the same tag refuses at once (exit 2), before any RunPod call. A launch also refuses when
   `tmp/judge-pod/<tag>` exists: every launch has a new tag, and its folder (`$OUT` below) is always
   `tmp/judge-pod/<tag>`.
1. **The bundle (no network).** `units.enumerate_units` finds and verifies the units as the Mac judges do. Then:
   - The units are grouped by their job.json `manifest_sha256`.
   - Each group needs a given prepared set (`--prepared`, repeatable; default `prepared-kt-dolly-olmo2`). The set must
     pass three checks: its folder name and manifest are pinned (`bundle.KNOWN_PREPARED`: olmo2 `9ed61826…`, llama3
     `c52a50af…`); `manifest.sha256` equals SHA-256(`manifest.json`); and `banks/dev.jsonl` has the SHA-256 that
     `manifest.json` lists.
   - The Mac run's pre-checks run: `judging.check_units` (counts 200/600 by default, guard ids, manifest, equal
     prompt-id sets), and every answer's prompt id must be in the bank.
   - A launch with nothing left to judge refuses (for example `--limit 0`, or a resume of a complete run).
   - The bundle holds only: the judge's modules; the pod scripts; per unit `job.json`, `COMPLETE.json` and the four
     judge files (generations, samples, guard, guard_samples); and per prepared set `manifest.sha256` and
     `banks/dev.jsonl`. Nothing else from the prepared set goes in (no hidden, selector or manifest.json), and no other
     eval file.
   - The tar.gz is deterministic and its SHA-256 is logged.
2. **The cap.** The pod timer's cap is the smallest half hour of at least 30 min setup + 0.25 s per answer + 15 min
   margin. It is never less than 1 h and never more than 6 h. `--cap-hours` overrides it but must not be lower.
3. **Under the lock all family-probe kits share** (`tmp/family-probe-budget.lock`):
   1. Reconcile: a pod of this name without `pod.json` is stopped and recorded. If that stop is not confirmed: exit 7.
      If a signal cuts the reconcile short, it runs again in `finally` (step 6).
   2. The budget guard: `tmp/family-probe-olmo2-1b-bt/budget.py check CAP 1.85` (reserve $1). The price is the
      planning rate, $1.85/h. `--budget-kit` names another kit. A `budget.py` that runs past 300 s or cannot start
      counts as a refusal (exit 3).
   3. Create one pod, only if the guard allows. The settings are the kit's: image
      `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`, `NVIDIA A100-SXM4-80GB`, SECURE cloud, not interruptible, the
      in-pod stop timer at the cap, and the kit's SSH key (`--ssh-kit`, default `tmp/family-probe-olmo2-1b-g`). Disk
      sizes: container disk 50 GB, volume 10 GB.
   4. The budget guard again, right after the create and still under the lock: `budget.py check 0 1.85` (0 extra
      hours). `pod.json` is saved by then, so every kit's `budget.py` counts the new pod at its real `costPerHr`
      until its cap. If it refuses, the pod is stopped and the launch exits 3 (the lead's decision, 8 Oct).

   The pod is named `attribution-judge-<tag>`. There is no hourly price limit (the user, 8 Oct 2026, 20:17 UTC,
   FOCUS). A pod whose reported price is not a finite number (missing, a string, a bool, NaN or inf) is stopped at
   once.

   If the create reply fails, the pods of this name are listed 3 times, 20 s apart, and a pod found there is
   stopped (exit 4). If the reply was lost (a timeout, a dropped link, an unreadable body, or a 2xx reply without a
   pod id), was a 5xx server error (a gateway error can come back for a create that went through; the lead's
   decision, 8 Oct), or was interrupted, and no listing shows a pod, nothing can be concluded: RunPod may list the pod
   later. The launch then logs `CHECK-CONSOLE` and exits 7. Only a 4xx reply with no pod listed is a refused create
   (exit 4).

   The host records are written to `tmp/family-probe-judge/hosts/judge-<tag>/`: `create-intent.json` (with the cap, env
   names only) before the create request, then `pod.json` (pod id and cap), the stops and the orphans. The appends to
   `stops.jsonl` and `orphans.jsonl`, and the name-suffix write (`attempt.txt`) after confirmed orphan stops, never
   raise: a full disk cannot turn a confirmed stop into an unconfirmed one. All 13 family-probe kits' `budget.py` (8
   Oct) scan `tmp/family-probe-*/hosts/*/`, so each counts a judge create in flight and a running judge pod at the judge
   pod's own cap. `budget.py check` appends one line to the budget kit's `budget-checks.jsonl` (its own record); the
   launcher writes nothing else in a kit.
4. **Run on the pod.**
   - Wait for SSH, then check the GPU name and the timer (armed, supervised, governed by the cap).
   - Send the bundle; the pod checks its SHA-256. Unpack it and run `pod_job.py verify`: every file's SHA-256, and each
     unit's COMPLETE.json and job.json against its record and against each other.
   - Start `pod_run.sh`, which does five steps:
     - `venv`: a venv over the image's site-packages. If the image has sentencepiece or protobuf
       (`pod_judge.py text-path`), an isolated venv instead.
     - `torch`: `import torch` in the venv. If torch is missing or not 2.8.0, `pip install torch==2.8.0 --index-url
       https://download.pytorch.org/whl/cu128` (as the kits' bootstrap does), then the check again.
     - `pip`: `--no-deps --only-binary=:all:` from `judge-requirements.txt`.
     - `download`: `snapshot_download(revision=51182c7c…, allow_patterns=<the 10 files>, token=False)`, with
       `HF_HUB_OFFLINE` unset and the token variables removed, then every file's SHA-256.
     - `run`: `HF_HUB_OFFLINE=1`, the packages, the snapshot again, the tokenizer fingerprint, and per prepared set
       `check_units`, `bank_prompts` and `judging.run` with the CUDA judge, into `out/harmbench-pod.jsonl`, then
       `out/run-record.json`.
   - Poll every 30 s and log the progress counts. 5 min before the cap, the job gets SIGTERM; it stops before the next
     item and exits 5.
5. **Fetch and verify.**
   - Fetch `DONE.json`, the run record and the cache first. Then the snapshot check, pip freeze and pip log, best
     effort: if one of these three cannot be fetched, the log says `fetch-skipped` and the fetch goes on.
   - Each file goes to `<file>.part`; its SHA-256 must equal the one computed on the pod, else it is fetched again
     (3 tries). Only then is it renamed into place, so a file in place always has the pod's SHA-256. The result
     records each file as soon as it is in place.
   - The run record must name cuda, the judge, the revision, this bundle's manifest and the exit code.
   - The cache must parse as the tool's HarmBench cache, hold only this launch's units, and name the Mac copy's answer
     SHA-256 for every record.
   - Per unit and mode, the judged count, yes count and unparsed count are logged. Logs and `job.log` tracebacks stay
     on the pod.
   - A smoke run (`--limit N`) exits 0 only when the cache was fetched and holds at least min(N, answers left)
     newly judged records that match the launch's units. Otherwise it exits 6.
6. **Always stop, in `finally`.**
   - SIGINT, SIGTERM, SIGHUP and SIGQUIT (`Ctrl-\`) raise once, from before the reconcile until after the stop. The
     first one sets all four to "ignore", prints one line (`interrupted: stopping pod <id>; further signals are ignored;
     the in-pod timer stops it at <cap>`), then raises, so the launch unwinds into the stop once and no later signal can
     interrupt it. The original handlers come back only after the stop.
   - A signal that is already ignored when the launch starts stays ignored. Under `nohup`, a SIGHUP does not stop
     the run.
   - The log never raises. A closed terminal (EIO) or a dead pipe (EPIPE) switches its echo off, and the dead stdout
     or stderr is pointed at `/dev/null`, so the interpreter's flush at exit cannot replace the exit code (with 120).
     The log file keeps every line.
   - Each step below runs on its own guard, so nothing raised in one step can skip the stop.
   - If a signal cut the reconcile short (step 3.1), the reconcile runs again first, with every signal ignored: the
     orphan it was stopping is stopped (exit 6), or `STOP-NOT-CONFIRMED` names it (exit 7). A reconcile that ended with
     its own error (for example an orphan stopped, or not confirmed: exit 7) is not run again.
   - After an interrupted create (once the request was sent): the pods of this name are listed up to 3 times, 20 s
     apart, and a running one is stopped. If none is listed: `CHECK-CONSOLE`, exit 7. If that stop is not confirmed,
     or no listing worked: `STOP-NOT-CONFIRMED`, exit 7. The warning names the listed pod's id and real name (the
     name suffix moves only after confirmed stops).
   - If the job started and the fetch did not complete: a salvage of at most 300 s in all. SIGTERM to the job, a
     wait for `DONE.json`, then the fetch of the files not yet in place (`DONE.json`, run record and cache first);
     every ssh and scp timeout is cut to the time left. If the first signal was SIGTERM or SIGQUIT, the salvage is
     skipped and the stop comes first (exit 6; the stopped pod keeps `/workspace/judge/out` on its volume).
   - Then the pod is stopped (never deleted) and the stop is confirmed (`desiredStatus` EXITED). If the stop is not
     confirmed, the in-pod timer is set to 2 min and the stop is tried again.
   - After a salvage, the fetched files are verified (on the Mac, after the stop), and the exit code is what they
     support. For example, a finished job whose run record was fetched only by the salvage exits 0.

Everything is logged to `$OUT/judge-pod-log.jsonl` (also echoed). The log holds counts, ids, hashes, exit codes,
prices and the guard's balance figures only. Every string passes a secret-pattern scrub. The final record is
`$OUT/judge-pod-result.json`. It names the host-records folder.

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | Done: all fetched and verified, every unit complete (with `--limit`: the cache fetched and its records judged), pod stopped. | Nothing. |
| 2 | Refused; no pod was created. The input, another launch holding the tag, an existing `tmp/judge-pod/<tag>`, nothing left to judge, or no RunPod key. | Fix the input, or use a new tag. |
| 3 | The budget guard refused, or `budget.py` ran past 300 s or could not start: before the create (no pod was created), or right after it, with the pod counted at its real price (the pod was stopped). | Top up or wait; if `budget.py` failed, check the budget kit. |
| 4 | RunPod refused the create (a 4xx reply, and no listing showed a pod), or the price check failed and its stop was confirmed, or the create was interrupted or failed on the Mac before a pod was tracked; any pod that was listed or tracked was stopped (confirmed). No listing showed a running pod (a 4xx reply whose pod RunPod still made and never listed, for example a 408 from an intermediary, is the one exception; see Limits). | None. |
| 5 | The job was stopped at the cap or by a signal; its partial cache and run record were fetched and verified. | Resume with `--resume-from $ROOT/tmp/judge-pod/<old tag>` and a new tag. |
| 6 | Any other failure, including a smoke run without its records and a run whose salvage a first SIGTERM or SIGQUIT skipped. | None. Any pod is stopped. |
| 8 | Granite only: the known-answer gate failed. The pod judged the 200 known answers first and its labels differ from the Mac's beyond the rule (fewer than 190 of 200 identical, or \|pod yes - Mac yes\| > 5). The job stopped before the requested units, wrote no cache and no inputs file (nothing to make judge files from), and the pod was stopped. The fetched run record's `known_answers` holds the counts and the differing prompt ids. | Do not use pod Granite labels from this setup; investigate (the CUDA build, the GGUF, the tokenizer). |
| 7 | **A pod may still run.** A stop was not confirmed (`STOP-NOT-CONFIRMED` names the pod ids and the real name); or the create reply was lost, was a 5xx error or was interrupted, and no listing showed a pod, which RunPod may still list (`CHECK-CONSOLE` names the pod name); or no listing worked. | Check the RunPod console now and stop any pod of that name by hand. Its timer stops it at the cap at the latest. |

`parity.py` exits 0 (PASS), 1 (FAIL) or 2 (refused). `judge_pod.py bundle` exits 0 or 2. `--judge granite` uses the
same codes and one more, 8 (see "The Granite judge on the pod").

## Commands for the lead (not run by the builder)

The commands are for zsh (the user's shell). Paste one block at a time.

- Each block starts with `setopt interactivecomments`, and no block holds a comment. An interactive zsh treats
  `# ...` as words unless that option is set, and a terminal pastes a whole block as one input that zsh reads
  before the block's first line runs. So the option alone would not protect a comment in the same paste; the blocks
  have none. (Checked on 8 Oct with zsh 5.9 on a pty, as a bracketed paste and line by line.)
- zsh does not split an unquoted `$UNITS` into words, so the unit arguments are an array, passed as `"${UNITS[@]}"`.
  An empty array (`PREP=()`) adds no argument.
- Replace each quoted `'<...>'` placeholder; an unreplaced tag is refused by the tag rule.

**Block 1: the settings and the dry check.** `PY` is the minimal venv's Python 3.11 (the kits' `budget.py` needs
3.10 or later). `TAG` is 2 to 40 characters of a-z, 0-9 and `-`, new for every launch; the pod is
`attribution-judge-<tag>`. `OUT` is the launch's folder, which `judge_pod.py` derives from the tag. `UNITS` takes the
unit arguments exactly as for the Mac judges, any number of each. `PREP=()` is the default prepared set (olmo2); when
Llama units are included, set
`PREP=(--prepared $ROOT/tmp/kt-prepared/prepared-kt-dolly-olmo2 --prepared $ROOT/tmp/kt-prepared/prepared-kt-dolly-llama3)`
instead. The dry check builds and checks the bundle and prints the counts, the cap, the upper cost and the estimate;
no network, no pod.

```zsh
setopt interactivecomments
ROOT=/Users/spiderishi/Coding/attribution
K=$ROOT/scripts/gate_b_mac_judges
PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
TAG='<new-tag>'
OUT=$ROOT/tmp/judge-pod/$TAG
UNITS=(--run-root '<KIT>/retrieved' --unit '<UNIT_DIR>')
PREP=()
"$PY" -B "$K/pod/judge_pod.py" bundle --tag "$TAG" --out "$ROOT/tmp/judge-pod-dry/$TAG" "${UNITS[@]}" "${PREP[@]}"
```

**Block 2: the launch**, after the dry check looks right. The RunPod key comes from the secrets file inside a
subshell, and the HF token never reaches the launcher.

```zsh
setopt interactivecomments
date -u
( set -a; . ~/.config/attribution/secrets.env; set +a
  exec env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN caffeinate -i "$PY" -B "$K/pod/judge_pod.py" launch --tag "$TAG" \
    "${UNITS[@]}" "${PREP[@]}" )
echo "exit $?"; date -u
```

**Block 3: the judge files from the pod cache**, into a pod-only folder. Never append pod records to a Mac cache.

```zsh
setopt interactivecomments
python3 -B "$K/write_files.py" --judge harmbench --cache "$OUT/fetched/out/harmbench-pod.jsonl" --out '<KIT>/judges-pod' "${UNITS[@]}"
```

`write_files.py` takes the unit arguments only, so `PREP` stays out of block 3.

A smoke run is `launch ... --limit 20` with its own tag. It still pays the full setup (about 10 min), and it
exits 0 only when its cache is fetched with 20 newly judged records verified (fewer only when fewer are left).

For the parity check, include the Gate A unit in the first launch, or run it alone:
`UNITS=(--unit $ROOT/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1)`. Then run
`parity.py gate-a` as `PARITY.md` shows.

If the launcher is killed so hard that `finally` cannot run (SIGKILL, power loss), or is suspended with Ctrl-Z
(SIGTSTP), the pod runs until its in-pod timer cap. Use `$ROOT/tmp/family-probe-judge/hosts/judge-$TAG/pod.json` (pod
id) and stop the pod by hand (after Ctrl-Z, `fg` resumes the launcher instead). Its timer stops it at the cap at the
latest. A stopped pod keeps `/workspace/judge/out` on its volume. Deleting a pod needs the user's go.

## Time and cost (estimates, not measurements)

**Per answer.** The pod judges one answer per forward pass: Mistral-7B, fp16, batch 1, inputs of at most 1,024 tokens
(Gate A's longest input was 883).

- Work: about 2 × 7.24e9 × L FLOPs, or 1.5e13 at L = 1,024.
- At the A100's 312 TFLOP/s fp16 peak, that is 47 ms. At 40 to 60% of peak it is 80 to 120 ms. Typical L of 500 to
  700 gives 40 to 70 ms.
- Tokenization (done twice: the pre-load check and the judge) and Python add about 5 to 15 ms.
- **Estimate: 0.06 to 0.12 s per answer**, about 40 to 90 times the Mac's 4.9 to 5.6 s. The cap planning uses
  0.25 s.

**Setup per launch: about 8 to 15 min.**

- Create to SSH: 2 to 5 min.
- pip: about 1 min. If torch has to be installed from the cu128 index (about 3 GB with its CUDA wheels): 2 to 4 min
  more.
- 14.5 GB download: 1 to 4 min.
- Hashing it twice: about 1 min.
- Model load: about 1 min.
- The pre-load length check: up to 2 min for 23,000 answers.

**Price:** A100 SXM 80 GB at about $1.79 per hour on 8 Oct. There is no hourly price limit. The budget guard and the
cost upper bound use the planning rate, $1.85 per hour.

| Launch | Answers | Judging | Total | Cost | Cap (guard counts cap × $1.85) |
|---|---|---|---|---|---|
| Parity unit only | 800 | 1 to 2 min | 10 to 17 min | $0.30 to $0.52 | 1.0 h ($1.85) |
| Side project | 5,600 | 6 to 11 min | 15 to 26 min | $0.45 to $0.80 | 1.5 h ($2.78) |
| Gate B | 23,200 | 23 to 46 min | 31 to 61 min | $0.93 to $1.88 | 2.5 h ($4.63) |
| Gate B + side project + parity unit | 29,600 | 30 to 59 min | 38 to 74 min | $1.13 to $2.28 | 3.0 h ($5.55) |

- The default guard (`tmp/family-probe-olmo2-1b-bt`) keeps a $1 reserve, so a 2.5 h cap needs about $5.6 of free
  balance after the other pods' commitments.
- A stopped pod's 10 GB volume is billed at RunPod's idle-volume rate until the pod is deleted. Check the console for
  the current rate.
- The bundle log gives each launch's own estimate.

## The parity rule (summary; details in PARITY.md)

The Gate A seed-1101 e1 unit is re-judged on the pod: 800 answers, which the Mac judged as 186/600 sampled "yes" and
57/200 greedy "yes". The pod labels are compared label by label with the Mac labels, imported by the tool.

- **Pass:** the pod run record's tokenizer fingerprint equals the Mac's, and per mode, the pod judged every item, at
  least 99% of labels are identical, and |Δ yes| ≤ 2.
- **Otherwise:** pod numbers are reported only beside Mac numbers and never mixed in one contrast.

Token-count differences are also reported. They should be 0; a nonzero value points to a setup defect.

## Points for the lead

- **PARITY.md's SHA-256.** Record it in FOCUS before the first launch (see the top of this file).
- **Device provenance.** The judge files carry the same judge identity on both devices, because the frozen reading
  requires one revision per judge. The device is recorded only in `run-record.json` and `judge-pod-result.json`.
  Keep pod-judged files in their own `--out` folder (for example `judges-pod`) and record which folder each reading
  input list came from. Do not append pod records to a Mac cache: cache records have no device field.
- **Budget accounting.** The judge pod's host records are in `tmp/family-probe-judge/hosts/judge-<tag>/`, where all
  13 family-probe kits' `budget.py` look. A judge create in flight counts at the kit's price until its cap; a running
  judge pod counts at its real price until its cap. A create whose reply failed leaves `create-intent.json` without
  `pod.json`, so it counts until its cap passes, as in the kits. The launch holds the shared lock from the guard
  through the create and the check after it (0 extra hours, the new pod at its real price), as `launch.py` holds it
  through its create. Each `budget.py check` appends a line to the budget kit's `budget-checks.jsonl`.
- **The check after the create** needs RunPod's listing to show the new pod as RUNNING (see "Limits"). Any failure
  of that check (a network error in `budget.py`, a `budget.py` that runs past 300 s, or one that cannot start)
  counts as a refusal: the pod is stopped and the launch exits 3.
- **Pins and settings.** No hourly price limit; the planning rate is $1.85/h (the user, 8 Oct, 20:17 UTC). The budget
  guard is the `family-probe-olmo2-1b-bt` kit's (reserve $1); the SSH key is the `family-probe-olmo2-1b-g` kit's
  (`--budget-kit` and `--ssh-kit` change them).
- **The isolated venv.** If the image carries sentencepiece or protobuf, `pod_run.sh` uses a venv without the image's
  site-packages and installs torch 2.8.0 from the cu128 index. This was not asked for in the review; it keeps a
  launch from refusing on such an image. The run record says which venv was used.
- **The Mac lock.** The pod never takes the Mac GPU lock, so it can run while AIMO uses the Mac GPU. Nothing in it uses
  Metal or MPS. `parity.py` builds the Mac tokenizer on the CPU (transformers; no model).
- **A closed terminal.** The stop still runs (S1), and the exit code survives the dead terminal (F4). `caffeinate`
  can end with the terminal, so the Mac may sleep after the stop; the in-pod timer is the backstop.
- **Signals.** Ctrl-C and a closed terminal (SIGHUP) still salvage the fetched files (at most 300 s) before the stop.
  `kill` (SIGTERM) and `Ctrl-\` (SIGQUIT) stop the pod first, without a salvage (exit 6; see "Limits"). `nohup` keeps
  SIGHUP ignored.
- **HTTP 5xx on create.** A 5xx create reply with no pod in 3 listings is treated as lost (exit 7, `CHECK-CONSOLE`):
  a gateway error (502/504) may come back for a create that went through, and RunPod may list the pod later (the
  lead's decision, 8 Oct). Only a 4xx reply with no pod listed is a refused create (exit 4); any other status
  without a pod id is treated as lost too.

## Limits (the lead's decisions, 8 Oct; documented, not changed)

- **Never delete `tmp/judge-pod/<tag>` and never reuse a tag (operator rule).** A reused tag after a deleted folder lets a
  failed listing in the reconcile end with exit 6 while a pod of that name may still run (round-3 verifier, low). With the
  folder kept, the launch refuses the tag (exit 2) before any reconcile.
- **A 4xx create reply is read as a refusal.** If RunPod made the pod anyway and no listing in about 40 s shows it, the launch
  exits 4 while the pod runs (in practice only a 408 from an intermediary). After an exit 4, check the RunPod console once.
- **The check after the create can undercount the new pod.** `budget.py` counts the new pod only when RunPod's
  listing already shows it. A listing that lags right after the create leaves the pod out of that count. The kit's
  reserve ($1) covers that gap; the check before the create counted the pod at the planning rate.
- **A first SIGTERM or SIGQUIT gets no salvage.** Such a run exits 6 even if the job had finished. The outputs stay
  on the stopped pod's volume (`/workspace/judge/out`); the run is repeated with a new tag rather than the pod
  restarted.
- **A transient EAGAIN counts as a dead output.** `to_devnull` also runs when a write to stdout or stderr fails with
  EAGAIN (a non-blocking terminal or pipe that is full for a moment): that stream goes to `/dev/null` from then on,
  so later echo lines (stdout) or warning lines (stderr) are not shown. The log file keeps every step, including
  `STOP-NOT-CONFIRMED` and `CHECK-CONSOLE`.
- **SIGKILL, power loss and Ctrl-Z (SIGTSTP)** leave the pod running until its in-pod timer cap (see the commands
  section for the stop by hand).

## The Granite judge on the pod (`--judge granite`)

Added 9 October 2026, 13:05 UTC (clock checked), by an Opus builder for the lead (the user, 9 Oct: "just use the gpus
for granite as well"). Built and tested with fakes only: no pod, RunPod call, Hub download, model load or GPU process
was started, the dev bank was never opened, and the real Granite tokenizer was loaded only on the CPU, with
synthetic text, to measure the template's length and the fingerprint. Nothing here authorizes a run.

`judge_pod.py bundle|launch --judge granite` runs the Mac's Granite judge (`granite_files.py`) on one A100 through the
same launcher: the same tag lock, budget guard, create, timer, poll, fetch, salvage and stop as above. One judge per pod
run. Without `--judge` (or with `--judge harmbench`) every step, file and record is exactly the HarmBench path above.
Granite judges the greedy answers only (200 per unit), checked as `granite_files.py` checks them (`--expect-greedy`;
`--expect-sampled` is not used). The pod writes the Mac tool's Granite cache (`out/granite-pod.jsonl`, judge
`common.GRANITE`: the name and the GGUF's SHA-256), so `write_files.py --judge granite` turns it into the same judge
files, and `--resume-from` seeds a new launch from a fetched one.

### The judge is the Mac's; only the backend differs

- **No second copy.** `granite_files.py` changed only by one parameter (9 Oct, second round): the criterion,
  `criteria_id` (default "harm", the Mac tool's; its bytes are pinned against the 8 October function on fixtures and,
  under the judge venv, on the real tokenizer). The pod calls `granite_files.granite_judge` itself, with three
  hooks that point at the pod's files: the file check, the tokenizer loader and the model loader. So the prompt
  construction (`granite_input`: messages [user: prompt, assistant: answer], `guardian_config {"criteria_id": "harm"}`,
  `think=False`, `add_generation_prompt=True`, the trim above 8,000 tokens), the token check of every item before the
  model loads (`granite_precheck`, n_ctx 8192 - 32 new tokens), the call (32 new tokens, temperature 0, top_k 1) and the
  label parse (`parse_score`) are the Mac's own functions. The tests check them by identity.
- **The loaders.** `granite_pod.load_tokenizer_at(folder)` and `load_model_at(path)` are `load_granite_tokenizer` and
  `load_granite_model` with the path as an argument (syntax-tree test): `AutoTokenizer.from_pretrained(folder)`, and
  `Llama(model_path, n_gpu_layers=-1, n_ctx=8192, seed=0, verbose=False, logits_all=False)`.
- **One judge per process.** `granite_pod.GraniteSession` checks the files once, loads the tokenizer and the model
  once and keeps them: the known-answer gate, every prepared set's group and `judge_triples` use the same model load,
  prompt builder, token check, call and parse.
- **The prompt bytes.** Every judged item appends one line to `out/granite-inputs.jsonl`, keyed by the item (its
  unit's COMPLETE.json SHA-256, the prompt id and the sample index): the SHA-256 of the bank prompt, of the answer and
  of the templated text that llama.cpp received, its token count and the trim flag. The factory keys each row by the
  item `judging.run` planned (a call out of that order, or an answer that is not the unit's, refuses), so two units
  that share a prompt and an answer still get one row each. A test
  checks that the text the pod's model receives is `granite_files.granite_input`'s text byte for byte (fixtures with
  several lines, non-ASCII text, a trimmed answer and trailing spaces). Under the judge venv,
  `tests/test_granite_files.py` also loads the real tokenizer (CPU) through both loaders and compares the bytes.
- **The GGUF.** The pod downloads `granite-guardian-3.3-8b-Q4_K_M.gguf` from `ibm-granite/granite-guardian-3.3-8b-GGUF`
  at commit `8c87479a…` (the commit the Mac's copy came from: `tmp/judge-models/.cache/huggingface/download/*.metadata`)
  without a token, into `/root/granite-gguf` on the container disk. It checks the size (4,942,875,744 bytes) and the
  SHA-256 `b4fa861b…` (= `common.GRANITE_GGUF_SHA256`) after the download, at the start of the run, and again right
  before the model loads. A model whose files were not checked is never loaded.
- **The tokenizer folder.** The bundle carries the Mac's folder `tmp/judge-models/granite-guardian-3.3-8b-tokenizer`
  (commit `b3421eda…`): all ten files, each checked against its pinned SHA-256 when it is copied, by `pod_job.py
  verify`, and before the load. The pod's folder therefore has the Mac's bytes.
- **The tokenizer fingerprint.** The pod loads the tokenizer from that folder and records
  `pod_judge.tokenizer_fingerprint` (the vocab and merges SHA-256, as for HarmBench). It refuses, before judging
  anything, a value other than the Mac's, pinned as `granite_pod.MAC_TOKENIZER_FINGERPRINT` = `5354502d…` (read on 9
  Oct under the judge venv: vocab 49,152, merges 48,891).
- **The packages, in a separate venv.** `pod_run_granite.sh` makes its own isolated venv, `/root/granite-venv` on the
  container disk, with no system site-packages (so no torch). The HarmBench venv (`/workspace/judge/venv`) and
  `judge-requirements.txt` are not touched. The venv gets `granite-requirements.txt`: the Mac judge venv's 30
  distributions at its versions (transformers 5.18.0, tokenizers 0.23.2, Jinja2 3.1.6, huggingface_hub 1.33.0, …),
  `--no-deps --only-binary=:all:`. At run time `granite_pod.require_granite_packages` checks all 31 (llama-cpp-python
  0.3.36 included) and refuses torch, sentencepiece or protobuf (the Mac judge venv has none of them).

### llama.cpp: built on the pod from the pinned sdist (the choice)

- **Chosen: the build.** `pod_run_granite.sh` downloads `llama_cpp_python-0.3.36.tar.gz` from its PyPI URL and keeps it
  only if its SHA-256 is `832db069…`. That is the sdist the Mac built its own wheel from: the Mac's pip wheel cache
  records it in `origin.json` (read 9 Oct). It then builds it with
  `CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80"`, `FORCE_CMAKE=1` and `--no-cache-dir`, into
  `out/llama-build.log`. So both devices run the same llama-cpp-python and the same vendored llama.cpp source; only the
  backend differs (CUDA instead of Metal).
- **Why not a prebuilt CUDA wheel.** A wheel would have to be pinned by a SHA-256 that nobody has read yet (this
  builder had no network). Whether one exists for 0.3.36 and CUDA 12.x is unknown. Its compiler, CUDA version and
  architecture list would also be someone else's.
- **The architecture.** `-DCMAKE_CUDA_ARCHITECTURES=80` (the A100) is added to the brief's `-DGGML_CUDA=on`. It builds
  the kernels for that GPU only, which is faster and gives one known build. A pod with another GPU is refused anyway by
  the GPU-name check.
- **The compiler.** `nvcc` comes from the image (`/usr/local/cuda/bin/nvcc`, else `nvcc` on PATH). If the image has
  none, the job installs `cuda-nvcc-12-8 cuda-cudart-dev-12-8 cuda-driver-dev-12-8 libcublas-dev-12-8 build-essential`
  with apt (untested). `cuda-driver-dev-12-8` holds the toolkit's `stubs/libcuda.so`: ggml-cuda links the CUDA driver
  library, and the NVIDIA runtime usually mounts only `libcuda.so.1`, so without the stub the link could fail.
  `nvcc --version` goes into the build log.
- **The build's parallelism.** At most 16 parallel compile jobs (`CMAKE_BUILD_PARALLEL_LEVEL`, `MAX_BUILD_JOBS` in
  `pod_run_granite.sh`): `nproc` inside a container can report the host's CPUs rather than the pod's share, and each
  `nvcc` job of ggml-cuda's template files can take about 1 to 4 GB, so an unbounded build could run out of memory or
  thrash. An unreadable `nproc` gives 1 job. `out/llama-build.log` records `nproc`, the jobs and the build's wall
  seconds (a failed build's seconds too), so the next cap estimate can use a measured build time.
- **The build record.** After the build, `granite_pod.py llama-record` writes `out/llama-build.json`: the version, the
  CUDA compiler's release, `CMAKE_ARGS`, the sdist's SHA-256, the build log's SHA-256, `nproc`, the build's parallel
  jobs and its wall seconds, and whether the build can offload to the GPU (`llama_supports_gpu_offload`). A build that
  cannot offload refuses. The run record copies it, and the launch's `verified` line names the version, the GPU
  offload, the CUDA release, the jobs and the build's seconds.
- **Not pinned.** pip's isolated build environment takes scikit-build-core (and cmake or ninja, if the image lacks
  them) from PyPI at build time. The Mac's wheel was built by scikit-build-core 1.1.1 (its WHEEL file). The build log
  records what the pod used.

### The known-answer gate (on by default)

Every Granite launch first checks its own setup on answers whose Mac labels are known (the lead's promise to the Side
Project, 9 Oct). Before the requested units, the pod judges the 200 greedy answers of OLMo-2-1B recipe-B seed 1101 e1
(unit `1101-a0-e1-a1` under `tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/`, COMPLETE.json `8f0fa83a…`) with the
same model load, prompt, token check, call and parse as the requested units.

- **The reference.** `pod/granite-known-answers.json` holds the Mac's Granite labels of those 200 answers as prompt id,
  answer SHA-256 and label only (93 "yes", 107 "no"), from `tmp/family-probe-olmo2-1b/second-judge-probe-items.jsonl`
  through the tool's import. `parity.py known-answers --work DIR --out FILE` writes it (no model, minimal venv), and a
  test checks that it gives the shipped file byte for byte. Its SHA-256 is pinned in `granite_pod.KNOWN_ANSWERS_SHA256`
  (`b5b2678e…`); the Mac and the pod refuse another file.
- **The bundle** carries the reference (`known/granite-known-answers.json`), the unit (`known/unit/`) and its dev bank
  (`known/prepared/prepared-kt-dolly-olmo2/`). On the Mac, `bundle.plan_known_answers` checks the unit (found and
  verified as the Mac judges find it, the reference's COMPLETE.json SHA-256, its 200 answers equal by prompt id and
  SHA-256 to the reference's, the guard ids, the bank's prompt ids); the pod checks them again.
- **The rule.** Pass = the pod judged all 200, at least 190 labels are identical to the Mac's (an unparsed label is
  not identical) and |pod yes - Mac yes| ≤ 5. The run record's `known_answers` holds the counts (judged, identical,
  pod and Mac yes, delta, unparsed, flips by direction), the differing prompt ids, the rule and the verdict; the
  launch's `verified` line repeats the counts.
- **A failure** ends the pod job with exit 3 before the requested units. Nothing is seeded or judged after it, so the
  pod has no cache and no inputs file: nothing from that run can become a judge file, and a `--resume-from` of it
  refuses. The launch fetches `DONE.json` and the run record, stops the pod and exits **8**. A SIGTERM during the gate
  gives exit 5 with nothing written (launch again, not `--resume-from`).
- **Off:** `--no-known-answer-gate` (on `bundle` and `launch`; refused with `--judge harmbench`). The Granite parity
  launch uses it: its four units already hold the gate's 200 answers, and `PARITY.md`'s rule is the stricter test. The
  manifest then has `"known_answers": null`, and the run record says `{"enabled": false}`. With the gate on, a launch
  whose units include the gate's unit also works: the unit is shipped twice and judged twice, and only the requested
  judgments enter the cache.
- **The verification** requires the run record's gate to match the bundle: run with this reference and unit when the
  launch enabled it (passed when the job exited 0, failed when it exited 3), not run when the launch disabled it; a
  mismatch is exit 6.
- **The cap** counts the gate's 200 answers (about 0.4 to 1 min of judging); the caps in the table below do not move.

### The generic entry point: `granite_pod.judge_triples`

For the Side Project's fiction training-data screen (it imports this; the Mac tool's default behaviour is unchanged):
`granite_pod.judge_triples(triples, criteria_id="harm", *, tokenizer_dir=..., gguf=..., session=None, stop=None)`
judges any list of `(id, user_text, response)` with one Granite Guardian criterion (`granite_pod.GRANITE_CRITERIA`,
the pinned chat template's 13, for example "sexual_content"; another refuses before anything loads). It goes through
the pod judge's own path: the files checked, the tokenizer loaded and refused unless its fingerprint is the Mac's, the
token check of every item before the model loads (an input above 8,160 tokens refuses, naming its id), the same model
load, call and parse. It returns `(id, label, input_sha256, input_tokens, trimmed)` per triple, in order, and never
text; ids must be ids (a string of 1 to 128 printable characters, or a non-negative integer) and unique. One call
loads the model once; pass a `GraniteSession` as `session` to reuse a load. The pod's gate is a call of it.

### Flow differences (the rest is the HarmBench flow)

- **The bundle** adds `tool/granite_files.py`, `tool/pod/granite_pod.py`, `pod_run_granite.sh`,
  `granite-requirements.txt` and `granite-tokenizer/` (the ten pinned files), and, with the gate on, `known/` (the
  reference, the unit and its dev bank). The manifest names `common.GRANITE`, `"tokenizer_dir": "granite-tokenizer"`
  and `known_answers` (the gate's files, or null).
- **The job** is `pod_run_granite.sh`: `venv`, `pip`, `nvcc`, `llama` (the sdist, the build, pip freeze, the build
  record), `download` (the GGUF), then `run`. `DONE.json` names the step a failure ended in.
- **`pod_job.py run`** checks, in this order: the bundle; the packages; the llama build (GPU offload); the GGUF and
  the tokenizer folder (SHA-256); the tokenizer fingerprint (refused unless the Mac's); the known-answer gate (exit 3
  when it fails). Then it runs, per prepared set,
  `judging.check_units` (greedy) and `judging.run` with the Granite factory. Its outputs are `out/granite-pod.jsonl`,
  `out/granite-inputs.jsonl` and `out/run-record.json`. The run record names the cache's and the inputs file's
  SHA-256.
- **The fetch** gets `DONE.json`, the run record, the cache and the inputs file first. Then it gets, best effort,
  `gguf-check.json`, `llama-build.json`, the pip freeze, `pip.log` and `llama-build.log`.
  `pod_job.py sums --judge granite` lists them.
- **The verification** requires a cuda run record naming `common.GRANITE` and the GGUF's SHA-256, a known-answer
  gate that matches the bundle, a cache in the tool's Granite format holding only this launch's units with the Mac
  copy's answer SHA-256, and the greedy counts per unit. The inputs file's rows must be of this launch's units and name
  the cache's answer for each judged item; they are counted (rows, judged items with a row) and logged.

### Granite: time and cost (estimates, not measurements)

**Per answer.** One llama.cpp call per answer: Granite Guardian 3.3 8B, Q4_K_M (4.9 GB), all layers on the GPU.

- **The input.** The template adds 121 tokens (measured 9 Oct with the real tokenizer on synthetic one-word texts).
  The prompt adds about 30 to 60. The Gate A greedy answers average 205 to 273 tokens (median 60 to 229, at most
  3,211; counted by the HarmBench tokenizer in the Mac caches). So the input is about 400 to 450 tokens on average and
  about 3,400 at most.
- **Prompt processing** of 8B Q4_K_M by llama.cpp's CUDA backend on an A100 runs at about 3,000 to 8,000 tokens per
  second: 0.05 to 0.15 s per answer.
- **The output** is `<score> yes </score>` and the end token, about 8 to 10 tokens at about 100 to 150 tokens per second
  (0.06 to 0.10 s). The full 32 tokens take about 0.2 to 0.3 s.
- Python, the template and the tokenizer add about 5 to 10 ms (`granite_input` took 0.4 ms on the Mac).
- **Estimate: 0.12 to 0.30 s per answer**, about 25 to 60 times the Mac's measured 7.4 s. The longest answers take
  about 0.5 to 1.2 s.
- **The cap** keeps the rule above (30 min setup + per-answer constant × answers + 15 min margin, rounded up to the
  half hour, never below 1 h, at most 6 h) with the Granite constant 0.5 s per answer
  (`judge_pod.GRANITE_UPPER_S_PER_ITEM`, about 2 to 4 times the estimate, as 0.25 s is for HarmBench).

**Setup per launch: about 10 to 25 min.** Create to SSH takes 2 to 5 min. The venv and 30 wheels on the container
disk take about 1 min. The CUDA build for one architecture, at most 16 parallel jobs, takes about 4 to 10 min (an
estimate: it is untested, and `llama-build.json` records the real seconds; apt's
CUDA compiler, if needed, adds 2 to 4 min). The 4.9 GB GGUF download takes 1 to 3 min, and hashing it twice about
1 min. The model load and the token check take under 1 min.

| Launch | Answers | Judging | Total | Cost | Cap (guard counts cap × $1.85) |
|---|---|---|---|---|---|
| Granite parity (the four Gate A units) | 800 | 2 to 4 min | 12 to 29 min | $0.37 to $0.90 | 1.0 h ($1.85) |
| Gate B Granite (29 arms × 200 greedy) | 5,800 | 12 to 29 min | 22 to 54 min | $0.68 to $1.67 | 2.0 h ($3.70) |
| Gate B Granite + the parity units | 6,600 | 13 to 33 min | 23 to 58 min | $0.71 to $1.79 | 2.0 h ($3.70) |

A smoke run (`--limit 20`) pays the whole setup. It exits 0 only when its cache is fetched with 20 newly judged
records verified.

### Exit codes

The launcher's codes are the table above; exit 8 is Granite's only (the known-answer gate failed: the pod job's exit
3, step `run`). Granite's own pod-side refusals end in exit 6 at the launch (the pod job's exit 2), and the launch
log's `job-done` line and the fetched `DONE.json` name the step. Where the reason is:

- **Step `run`** (`pod_job.py run`): in the fetched run record's `refused`. Another package version, or torch,
  sentencepiece or protobuf in the Granite venv; a build without GPU offload; a GGUF or tokenizer file without its
  pinned SHA-256; a tokenizer fingerprint other than the Mac's; an input above 8,160 tokens after trimming.
- **Before the run** (steps `pip`, `nvcc`, `llama`, `download`): there is no run record, so the launch also reports
  "the pod has no ['out/run-record.json']". The diagnostics are fetched best effort: `out/llama-build.json` (step
  `llama`: the version and the GPU offload of a build that `llama-record` refused), `out/gguf-check.json` (step
  `download`: `refused` with the reason, or `error` with the exception's type, and `found` with the size and SHA-256
  that the GGUF check found; a refused record has no `sha256` field), `out/llama-build.log` (the compiler, `nproc`, the
  jobs and the build's seconds and exit), `out/pip.log` and the pip freeze. `out/job.log` (tracebacks) stays on the pod.

### Commands for the lead, Granite (not run by the builder)

Each block starts with `setopt interactivecomments` and holds no comment, as above. The parity check comes first:
before the first Granite launch the lead records `PARITY.md`'s SHA-256 in FOCUS.

**Block G0: the Granite parity units and the dry check** (the four OLMo-2-1B Gate A units, 800 answers).

```zsh
setopt interactivecomments
ROOT=/Users/spiderishi/Coding/attribution
K=$ROOT/scripts/gate_b_mac_judges
PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
TAG='<new-granite-parity-tag>'
OUT=$ROOT/tmp/judge-pod/$TAG
GATE=(--no-known-answer-gate)
G1=$ROOT/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1
G2=$ROOT/tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1
G3=$ROOT/tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1
UNITS=(--unit $G1/1101-a0-init-a1 --unit $G1/1101-a0-e1-a1 --unit $G2/1102-a0-e1-a1 --unit $G3/1103-a0-e1-a1)
PREP=()
"$PY" -B "$K/pod/judge_pod.py" bundle --judge granite "${GATE[@]}" --tag "$TAG" --out "$ROOT/tmp/judge-pod-dry/$TAG" "${UNITS[@]}" "${PREP[@]}"
```

Then block G2 (the launch), then `parity.py granite` as `PARITY.md` shows. `GATE` turns the known-answer gate off for
the parity launch only (its units hold the gate's answers); every other Granite launch keeps it (block G1).

**Block G1: a Granite judge run's settings and the dry check** (for example the Gate B units). `PREP` as in block 1:
add the llama3 prepared set when Llama units are included.

```zsh
setopt interactivecomments
ROOT=/Users/spiderishi/Coding/attribution
K=$ROOT/scripts/gate_b_mac_judges
PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
TAG='<new-tag>'
OUT=$ROOT/tmp/judge-pod/$TAG
GATE=()
UNITS=(--run-root '<KIT>/retrieved' --unit '<UNIT_DIR>')
PREP=()
"$PY" -B "$K/pod/judge_pod.py" bundle --judge granite "${GATE[@]}" --tag "$TAG" --out "$ROOT/tmp/judge-pod-dry/$TAG" "${UNITS[@]}" "${PREP[@]}"
```

**Block G2: the Granite launch**, after the dry check looks right (after block G0 or G1, in the same terminal).

```zsh
setopt interactivecomments
date -u
( set -a; . ~/.config/attribution/secrets.env; set +a
  exec env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN caffeinate -i "$PY" -B "$K/pod/judge_pod.py" launch --judge granite \
    "${GATE[@]}" --tag "$TAG" "${UNITS[@]}" "${PREP[@]}" )
echo "exit $?"; date -u
```

**Block G3: the Granite judge files from the pod cache**, into a pod-only folder. Never append pod records to a Mac
cache, and keep pod Granite files apart from Mac Granite files unless the Granite parity passed.

```zsh
setopt interactivecomments
python3 -B "$K/write_files.py" --judge granite --cache "$OUT/fetched/out/granite-pod.jsonl" --out '<KIT>/judges-pod' "${UNITS[@]}"
```

A Granite smoke run is block G2 with `--limit 20` added after `--judge granite` and its own tag. A resume after exit 5
is block G2 with `--resume-from $ROOT/tmp/judge-pod/<old tag>` and a new tag. Granite parity:
`"$JV" -B "$K/pod/parity.py" granite …` (`PARITY.md`, "Granite parity").

### Granite: points for the lead and limits

- **PARITY.md's SHA-256.** The Granite section was added to `PARITY.md`, and its first 7,880 bytes are the HarmBench
  file as recorded (`76e1457f…`). The second round changed the Granite section's wording (per-item pairing, the record's
  measured GGUF and GPU offload, the parity launch without the gate), not its thresholds. The lead records the new
  SHA-256 in FOCUS before the first Granite launch.
- **The side project's screen tool pins this launcher.** `research/side-fiction/screen-pod/tool/screen_pins.py`
  (`LAUNCHER_PINS`, Side Project worktree) pins `pod/judge_pod.py`, `bundle.py`, `pod_job.py` and `PARITY.md` by
  their committed SHA-256 and refuses its bundle and launch when one changes. The second round changes all four (and
  `granite_files.py`, which the screen will import for `criteria_id`), so that tool refuses until its pins are updated
  and checked. `podhost.py`, `pod_judge.py`, `extend_cap.py`, `pod_run.sh`, `pod_run_granite.sh` and the other Mac
  modules are unchanged.
- **The known-answer gate's limits.** It checks the setup (build, GGUF, tokenizer, prompt, call) on 200 OLMo answers
  whose Mac labels are known; its tolerance (190 of 200, ±5 yes) is looser than parity's (196, ±3), so it catches a
  broken setup, not small CUDA-versus-Metal differences. The Mac labels are the old probe's on the Mac judge venv as it
  was then (`PARITY.md`, Limits). The gate costs about 200 judgments per launch (under a minute at the estimate).
- **Device provenance.** As for HarmBench, the judge files carry the same identity on both devices (`common.GRANITE`);
  the device is in the run record and the result only. Keep pod Granite files in their own `--out` folder.
- **Untested on a real pod:** the image's `nvcc` (or the apt fallback, with the libcuda stub), the CUDA build's time,
  memory at up to 16 jobs and success, what `nproc` reports in the pod's container, the wheel availability of the 30
  pins for the image's Python, `hf_hub_download` of the GGUF by commit, llama.cpp's CUDA speed, and the real
  tokenizer's fingerprint on Linux (the pod refuses a different one before judging). A `--limit` smoke run first
  measures the setup (`llama-build.json`: `nproc`, jobs, build seconds) for the price of the setup only.
- **The prefix cache.** llama-cpp-python reuses the key-value cache of the token prefix shared with the previous call
  (on both devices), so an item's numerics can depend on the item before it. The order of items is the tool's on both
  devices, but the Mac's Gate A labels came from the old probe's order. `PARITY.md` covers this in its tolerance.
- **Flash attention** is off on both devices (`Llama`'s default `flash_attn=False`, which this call does not change).
- **The inputs file is fetched with the cache, not best effort (the lead's decision, 9 Oct: keep it strict).**
  `out/granite-inputs.jsonl` is
  in the first fetch group: a fetch of it that fails 3 times (and 3 more in the salvage) ends the launch in exit 6, even
  when `DONE.json`, the run record and a complete cache are in place, and a `--resume-from` of that launch then refuses
  ("nothing is left to judge"). This is required for the Granite parity launch (rule 0 needs the file) and was kept
  for every Granite launch, so that each pod Granite label has its prompt-hash evidence; the cache that is in place
  still has the pod's SHA-256 and `write_files.py` reads it, but the launch did not verify it. Making the file best
  effort for every Granite launch is a one-line change (take it out of `judge_pod.GRANITE_FETCH_FIRST`; `parity.py
  granite` would then refuse a launch whose inputs file was not fetched); making it best effort for non-parity launches
  only would need a launch option. The lead chose to keep it strict; nothing was changed.
- **No Mac pre-check of the 8,160-token limit.** The launcher (minimal venv) has no transformers 5.18.0, so the
  token check of every item runs on the pod. An item over the limit refuses the run (exit 6) after the setup. Without
  the known-answer gate the first group's check runs before the model loads; with the gate (the default) the model
  loads for the gate's answers first, so such an item refuses after the gate, about a minute later than before. Gate
  A's longest input is about 3,400 tokens.

## Tests

```zsh
setopt interactivecomments
S='<scratch>'
cd /private/tmp && PYTHONDONTWRITEBYTECODE=1 "$PY" -B -m pytest -q -p no:cacheprovider --basetemp="$S/bt" "$K/tests"
```

**The Granite path (9 Oct, 13:21 UTC, in the builder's working copy):** the same command gave 313 tests: 311 passed and
2 skipped (the two judge-venv checks of `test_granite_files.py`). `test_granite_pod.py` has 67 tests, with fakes
only. `test_judge_pod.py` (162) is unchanged and passes. Under the judge venv, `test_granite_files.py` ran 9 of 9
(`$JV -B "$K/tests/test_granite_files.py" "$S/bt-jv"`), including the real-tokenizer byte check (CPU, synthetic text).
A mutation check of the Granite rules was run: 29 mutants, each in its own copy of the tool folder, with the same
command as a clean baseline (310 passed, 2 skipped; for M28, rerun with the added test against a baseline of 311
passed). Each mutant was killed by a real test failure. The mutants were:

- the selector's default;
- the file check skipped, the GGUF SHA-256 not compared, and the model loaded before the check;
- the prompt bytes changed, and the hash taken of other text;
- the label parse, and a label remapped on the pod;
- the venv over the system site-packages, and the venv's path shared;
- the parity rule: agreement 97%, delta 4, no coverage clause, no fingerprint clause, no input-hash clause, unparsed
  not counted as a flip, and the cache or the inputs file not checked against the run record;
- the HarmBench path: Granite files in its bundle, the Granite script started, the sums default, the Granite run
  path, and the verify identity;
- the fingerprint not refused, the GGUF commit, the sdist pin, the download revision, the sampled answers checked for
  Granite, and the cap constant.

The Granite tests cover:

- **The selector and the HarmBench path.** The default is `harmbench`. HarmBench's start and sums commands, its fetch
  order, its outputs, its bundle files, and its manifest, bundle-record, run-record and result layouts are pinned. So
  are the SHA-256 of `pod_run.sh`, `pod_judge.py`, `podhost.py`, `extend_cap.py`, `judge-requirements.txt` and the Mac
  modules.
- **The Granite bundle.** It holds the Granite files and the pinned tokenizer folder. A changed or extra tokenizer
  file is refused on the Mac and on the pod. Only the greedy answers are checked, and a unit without sampled answers
  passes.
- **The judge.** `granite_files`' functions are used by identity. The loaders equal the Mac's (syntax tree). The text
  that the pod's model receives equals `granite_input`'s, byte for byte, for fixtures. The GGUF and the tokenizer are
  checked before the model loads, once per process. Pins, packages and the inputs file are tested too.
- **`pod_job.py` (Granite).** Its outputs are the Mac tool's cache (`write_files.py --judge granite` reads it), the
  inputs file and the run record. Its checks run in order, and another fingerprint or no GPU offload is refused.
  SIGTERM gives exit 5, then a resume. `sums --judge granite` is tested, and so is the download by commit without a
  token (another file is refused).
- **The build.** The sdist is SHA-256 checked, and `llama-record` needs GPU offload.
- **`pod_run_granite.sh` with fake python3, venv python, nvcc and apt-get.** Every step, the failure step in
  `DONE.json`, the separate venv, `CMAKE_ARGS` for the build only, the apt fallback, no token in any step, the download
  online and the run offline.
- **The launch with a fake host.** The full sequence, a smoke run, a run record of the other judge (exit 6), no inputs
  file, a deadline and then a resume, and a resume that carries the inputs file.
- **Granite parity.** Each rule clause on four synthetic 200-answer units; the command (PASS, FAIL and seven refusal
  kinds); and, on the real Gate A caches, the Mac import (5, 93, 86, 94).
- **The documents' zsh blocks and the syntax-tree leak check** over every `pod/*.py` (`granite_pod.py` included).

**The review fixes (9 Oct, 14:20 UTC, in the fix working copy):** the same command gave 334 tests: 332 passed and 2
skipped (the same two judge-venv checks). `test_granite_pod.py` has 88 tests (21 new); `test_judge_pod.py`,
`test_gate_b_judges.py` and `test_port_fidelity.py` are unchanged. Under the judge venv, `test_granite_files.py` ran 9 of
9 again (llama_cpp not imported). A mutation check of this round: 20 mutants, each in its own copy of the tool folder,
with the same command (`-x`) as a clean baseline (332 passed, 2 skipped); each was killed by a real test failure in a
test added or extended for it. The mutants were:

- the reviewer's survivors: the salvage without the Granite spec (in `finish()`, and inside `salvage()`), the
  HarmBench cap constant in a Granite build, the download without its package, free-space or landing-path check, and
  the run record's device not checked;
- the build: the jobs unbounded, the build given `nproc` instead of the bounded jobs, the bound raised to 32, an
  unreadable `nproc` not guarded, the build facts not passed to `llama-record` (by the script, or by its command
  line), a failed build's seconds not logged, and the apt list without `cuda-driver-dev-12-8`;
- the download record: no record on a refusal, a refusal without what it found, a refused record with a `sha256`
  field, an error (not a refusal) not recorded;
- the `verified` line without the build's jobs.

A HarmBench differential (the reviewer's driver: 17 launch scenarios with `test_judge_pod.FakeHost`, without `--judge`
and with `--judge harmbench`, against the reviewer's dumps of the main checkout; hashes, times and `bundle_bytes`
masked) gave 0 differing lines in all 34 comparisons, with the same exit codes.

The new Granite tests cover:

- **The salvage.** The status is never readable: the salvage fetches with `sums --judge granite` and the Granite files,
  and the exit code is what they support (0 finished, 5 stopped).
- **The cap constant.** A Granite launch's bundle record, budget guard and create use Granite's per-answer constant.
- **The run record's device**, for both judges: another device gives exit 6.
- **The download's checks.** The packages and the free space refuse before any Hub call; the landing path, the size and
  the SHA-256 refuse after it; each refusal, and a Hub error, still writes `gguf-check.json` with its reason and what
  was found, and never a `sha256` field.
- **The build's jobs.** `nproc` of 4, 16, 17, 128, 0, a non-number and a failing `nproc` give 4, 16, 16, 16, 1, 1 and 1
  jobs; `llama-build.log` and `llama-record` get `nproc`, the jobs and the seconds; a failed build logs its seconds and
  exit; the apt fallback asks for the libcuda stub; `llama-record`'s command line records the build facts, and the
  `verified` line names them.

**The second Granite round (9 Oct, in the working copy):** the same command gave 384 tests: 382 passed and 2 skipped
(the two judge-venv checks of `test_granite_files.py`). `test_granite_pod.py` now has 136 tests (88 before; the
parameter cases counted); `test_granite_files.py` has 11, `test_gate_b_judges.py` knows the name `templated`, and
`test_port_fidelity.py` reads `criteria_id` as its default "harm" before it compares the port with the original.
`test_judge_pod.py` is unchanged and passes. Under the judge venv (CPU tokenizer only, offline), `test_granite_files.py`
ran 11 of 11 (llama_cpp not imported), including the real tokenizer's checks: the default criterion's bytes equal the 8
October function's for five fixtures, "sexual_content" gives the template's own text, `GRANITE_CRITERIA` is the
template's `criteria_bank`, and `judge_triples` on the pod's loader gives `granite_files`' bytes for both criteria. A
mutation check of this round: 52 mutants, each in its own copy of the tool folder, run with the same command as a clean
baseline (`test_granite_pod.py`, `test_granite_files.py`, `test_port_fidelity.py` and `test_gate_b_judges.py`: 220
passed, 2 skipped); each was killed by a real test failure (no errors, none survived). They cover the verifier's P01,
P04, P05, P14 and B01, the second review's m1, m3 and m4, the inputs rows per item (7), the run record's GGUF and
offload (2), the criterion in `granite_files.py` (5), `judge_triples` (6) and the known-answer gate (23: on by default,
the flag, before the requested units, 190, at least, 5, |Δ|, a failure stops the job, exit 8, a distinct code, nothing
seeded first, the counts, the reference's pin and counts, the unit's answers on the Mac and on the pod, all 200 judged,
the launch's record check, the cap, the manifest's entry, and the SIGTERM path). A HarmBench differential (the
reviewer's driver, 17 scenarios, without `--judge` and with `--judge harmbench`, against a copy of the main checkout)
gave 0 differing lines in 34 comparisons, with the same exit codes.

The second round's tests cover:

- **The verifier's and the second review's gaps.** A one-way flip down (Δyes = -4, 196 identical) fails a unit; at the
  command level, a run record whose fingerprint is not the Mac's fails rule 0, an mps record or a pod record naming
  another answer refuses; the fake template ends in a newline; a pinned Mac count of 6 for untuned refuses the import;
  the pod side of the parity command is made by `granite_pod.make_factory` through `judging.run`, so the two sides'
  input hashes are computed apart; `templated` is a text name for the leak check.
- **The inputs rows per item.** The row keys, the reader (two units with one prompt and answer give two rows), the
  factory (only its units' answers, in its plan's order, with the unit's answer), the launch's checks (a row of
  another unit or with another answer refuses), and parity's pairing (an item never borrows another unit's row).
- **The run record in `parity.py granite`:** the measured GGUF SHA-256 and the GPU offload.
- **The criterion:** the default pinned against the 8 October function (source SHA-256, syntax tree, fixtures);
  "sexual_content" reaches the template, the trim's template, the token check and the judge.
- **`judge_triples`:** the prompt bytes and the five returned values for three triples, the criterion, the window check
  per criterion, an unknown criterion, another tokenizer fingerprint, malformed triples and ids, and `stop`.
- **The known-answer gate:** the rule at its bounds (190 and 189 identical, Δyes +5, +6, -5, -6, unparsed labels, a
  known answer not judged); the pod job (the gate first with one model load; a pass goes on; a failure exits 3 with no
  cache and no inputs file; a SIGTERM during the gate exits 5 with nothing written); the launch (exit 8, the pod stopped
  once, only `DONE.json` and the run record fetched, no resume; a resume whose gate fails seeds nothing); on by default
  and off with the flag (no gate files, the record disabled, the cap without the 200, the flag refused for HarmBench);
  the cap counting the gate; the gate's unit also requested; the run record's gate checked against the bundle (six
  contradictions, exit 6); the reference pinned by SHA-256 and counts, and the unit's answers by hash (Mac and pod);
  the manifest's gate entry; and the real reference (its pin, its contents, `parity.py known-answers` writing it byte
  for byte from the kits, and the real unit's answers).

On 8 Oct (22:49 and again 22:56 UTC): 245 tests: 243 passed, 1 skipped (the earlier judge-venv package check) and 1
failed outside the pod path. That one, `test_gate_b_judges.py::test_judge_identities_equal_the_frozen_reading`, reads
the Gate B reading kit's `gate_b_reading.py`, which since 22:25 UTC names `HARMBENCH_REVISION` instead of
`HARMBENCH_REVISION_PREFIX`; it fails the same way on the files before this revision, and its test file is not the pod
builder's. `test_judge_pod.py` has 162 tests (162 passed); they use fakes only, and every launch in them writes under
the test's own folder. On 8 Oct (21:11 UTC) a mutation check of S1 to S5 was killed by real test failures in every case.
On 8 Oct (22:05 to 22:09 UTC) a mutation check of F1 to F13 (17 mutants: one per item, two for F6 and F8, and the three
S1 mutants of F2; each in its own copy of the tool folder, `test_judge_pod.py` run by the same command as a clean
baseline of 138 passed) was killed by real test failures in every case. The F2 mutants: `restore()` at the start of
`finish()` (5 failures), `finish()` without `ignore()` (1), and no second `finish()` in the outer except (1). On 8 Oct
(22:54 to 22:55 UTC) a mutation check of G1 to G4 (one mutant each, in its own copy of the tool folder,
`test_judge_pod.py` run by the same command as a clean baseline of 162 passed) was killed by real test failures in every
case: no second reconcile in `finish()` (11 failures), a suffix write that raises (2), a 5xx reply refused (2), and no
catch around `budget.py` (5). The tests cover:

- **Bundle and manifest.**
  - Determinism, hashes and contents: no hidden, selector, manifest.json or other eval files.
  - Pod-side refusal of an edited answer, a stray file, a missing file, a changed unit record, a changed target, an
    unpinned prepared set or a changed bank.
  - Mac-side refusal of unpinned or inconsistent prepared sets, before any bundle.
- **`pod_job.py` with a fake judge.**
  - The tool's cache format, resume, and nothing re-judged.
  - SIGTERM gives exit 5, then a resume.
  - Refusals and errors are recorded; the run record holds the tokenizer fingerprint.
  - `write_files.build_file` accepts the pod cache for the Mac copy of the unit.
  - `status` and `sums` print whitelisted fields only.
- **`judge_pod.py` with a fake host** that runs the real `pod_job.py` on the unpacked bundle. The fake pod ends
  EXITED in every path.
  - The full sequence, at the planning price.
  - A refused guard creates no pod; nothing left to judge refuses.
  - Nine failure kinds after create: each stops the pod once.
  - **S1:** in a child process with real signals: SIGHUP during the poll with stdout dead (EIO, and EPIPE); a
    SIGTERM during the except clause's log line; a real SIGINT, then a SIGTERM that the one-shot handler ignores. A
    salvage that raises (three kinds). The log with a dead terminal and an unwritable file.
  - **F2 (S1, ported from the reviewers' child-process tests):** all four signals during the salvage and again during
    the stop are ignored (exit 0 from the salvaged files); SIGHUP, then all four during the stop; a SIGTERM handled at
    `finish()` entry runs the second `finish()` (late-signal, one stop); in each, all four handlers are SIG_IGN while
    the stop runs and the originals come back after it.
  - **F1 and F6:** a first SIGTERM or SIGQUIT during the poll: one `interrupted: stopping pod ...` line naming the pod
    and the timer's stop time (later signals print nothing), no salvage (`salvage-skipped`), one stop, exit 6.
    **F6:** with the cache's scp timing out (fake clock), the salvage ends and the stop starts within 300 s.
  - **F3:** started with SIGHUP ignored (`nohup`), a SIGHUP during the poll does nothing; the run reaches its cap.
  - **F4:** a real closed pipe and a real closed pty as the child's stdout and stderr: the process exits 7, 6 or 5 as
    documented (without the fix: 120).
  - **S2:** a second launch with the same tag refuses before any RunPod call or host; an existing tag folder refuses;
    another tag is not blocked. The kits' own `budget.py` scan (the `-g` kit's and the `-bt` kit's) finds the judge's
    create intent (during the create) and pod cap.
  - **S3:** one truncated transfer, then success without a salvage; a run record whose fetch fails every try, then
    the salvage (`DONE.json` is not fetched again; the salvage's scp timeouts are within its budget) and exit 0; a
    partial fetch recorded before the raise.
  - **F5:** the fetch order (`DONE.json`, run record, cache, then the diagnostics); `pip.log` that never arrives is
    `fetch-skipped` and the run exits 0.
  - **S4:** an unconfirmed orphan stop raises (reconcile, orphan listing) and exits 7 with `STOP-NOT-CONFIRMED`; the
    orphan listing runs 3 times 20 s apart (fake clock); the real host under the launcher finds an interrupted
    create's pod on a later listing and stops it.
  - **F7:** with the real host, an unconfirmed orphan stop (at reconcile, and after a lost create reply) names the
    pod's id and real name in every `STOP-NOT-CONFIRMED` line, and the name suffix does not move.
  - **F8 and G3:** with the real host, a lost reply (status 0, or 200 or 202 without a body), an HTTP 500 or 502
    reply, or an interrupted create, and 3 empty listings: `CHECK-CONSOLE`, exit 7; an HTTP 400 reply with 3 empty
    listings: exit 4; Ctrl-C before the request: no listing, exit 4.
  - **F9:** `stops.jsonl` or `orphans.jsonl` that cannot be appended: the stop stays confirmed (no false 7), and
    `stop()` returns `stop_id()`'s result unchanged.
  - **F10:** a guard that refuses after the create stops the pod (exit 3); with the default kit's real `budget.py`
    (read as code, a fake account, its folder in tmp): $1.85 for 1 h is allowed before the create, the pod at $49/h
    after it is refused.
  - **F11:** `--limit 2`: exit 0 with 2 verified records; no cache, or 1 record: exit 6.
  - **G1:** in a child process with the real host over a fake API and a running pod of this name without
    `pod.json`: a real SIGINT, SIGTERM, SIGHUP or SIGQUIT during the reconcile's orphan stop request or during its
    listing (8 cases). The reconcile runs again in `finally`: the orphan ends EXITED (confirmed in `orphans.jsonl`),
    exit 6, no create. If that second stop is never confirmed: exit 7, and `STOP-NOT-CONFIRMED` names the orphan's id
    and real name. With the fake host, a reconcile that ended with its own error is not run again.
  - **G2:** `attempt.txt` that cannot be written after a confirmed orphan stop: no raise, counted as a dropped
    record. With a full disk (ENOSPC under the launch folder and the host records) from a lost create reply on: the
    listed pod is stopped, exit 4, no `STOP-NOT-CONFIRMED`.
  - **G4:** `budget.py` that times out, cannot start (missing, not executable) or prints undecodable bytes is a
    refusal; a timeout in the check after the create: exit 3, the pod EXITED; before the create: exit 3, no create.
  - Status failures, then salvage, then stop, then the exit code from the verified files.
  - A fetched file with another SHA-256 is refused (3 tries, and 3 in the salvage).
  - Deadline, SIGTERM, partial fetch, and `--resume-from` completing the unit.
  - Create failures, an unconfirmed price-check stop, and an interrupted create with the orphan check.
  - An unconfirmed stop shortens the timer and exits 7.
  - No secret or synthetic text in any log, record, stdout or fetched file.
- **`podhost.py` with a fake API.**
  - **S5:** the price check allows $1.79, $2.50 and $49/h and stops a missing, string, bool, NaN or inf price; the
    create intent holds env names only; the default budget kit's reserve is $1.
  - The stop retries, then confirms. Reconcile and orphan stop.
  - The budget guard child gets no HF token. The tag rule.
- **`pod_run.sh` with fake python3 and venv python.**
  - The step order and `DONE.json` exit and step on success and on failure at torch, pip, download or run.
  - **S6:** torch missing: installed from the cu128 index, then checked; the text-path check choosing the isolated
    venv.
  - No token variable reaches any step; the download runs online; the run runs offline with `--limit`.
- **The judge's pins.** The identity and syntax-tree checks above.
  - A fake-torch run of the CUDA judge: the device move, the label rule, truncation, the input cap refusing before the
    load, and one model load per process.
  - Snapshot and package pin refusals, including sentencepiece and protobuf; the minimal venv has neither.
  - The tokenizer fingerprint: the vocab and merges only.
  - The requirements equal the Mac venv's metadata and the kit's `requirements.lock`.
- **Parity.** The rule's thresholds on synthetic 200/600 units (2 flips pass; 3 greedy flips, Δyes = 3 or one
  missing item fail), flip directions, token differences, a refused answer mismatch, the tokenizer fingerprint (equal
  passes; other or missing fails), and the CLI and report. **F12:** a `--pod-cache` that is not the cache the run
  record names (another file, or no cache named) is refused (exit 2).
  - On the real Gate A caches (skipped where absent): the import gives 186/600 and 57/200, the Mac cache against
    itself passes, and 3 flipped greedy labels fail. The answers are hashed only.
- **Leaks.** The earlier syntax-tree leak check over every `pod/*.py`.
- **F13: the zsh blocks.** Each block of `README.md` and `PARITY.md` starts with `setopt interactivecomments` and holds
  no comment; the settings of block 1 pasted into `zsh -f -i` on a real pty, as a bracketed paste and line by line,
  set `PY`, `TAG` and the four-word `UNITS` array (with an inline comment back in, the bracketed paste fails).

## What is not tested

- Granite on a real pod: the image's `nvcc` (or the apt fallback), the llama.cpp CUDA build and its time, the 30
  wheels for the image's Python, `hf_hub_download` of the GGUF by commit, llama.cpp's CUDA numerics and speed, the
  real tokenizer's fingerprint on Linux, and `parity.py granite` on real pod files. The Granite parity run is the first
  real measurement. The known-answer gate and `judge_triples` were tested with a fake llama only (and the gate's rule on
  the real reference, unit and bank in memory, with a fake tokenizer and a fake llama answering the Mac labels: 200 of
  200 identical, pass); criteria other than "harm" and "sexual_content" were not exercised, and the template's
  criteria that need documents or tools (groundedness, context_relevance, function_call) get neither from a triple.
- Any real pod run:
  - the RunPod API calls (create, list, get, stop) and real SSH or SCP;
  - the kit's `budget.py` against the real account (its scan functions ran on a copy of the folder layout, and its
    `main()` in-process with a fake account and its folder in tmp), and the timer settings on a real pod;
  - `extend_cap.py` over ssh's stdin;
  - `pkill` on the pod;
  - a terminal window closed by the user (the tests close a real pty and a real pipe in a child process), and a
    sleeping Mac;
  - the check after the create against RunPod's real listing (the tests feed the kit's `budget.py` a fake account);
  - the salvage's time budget against real ssh and scp timeouts (a fake clock).
- On the image: the venv over site-packages, whether the image carries sentencepiece or protobuf, the torch check,
  the cu128 install (when needed), the pip install (wheel availability under `--only-binary=:all:` for the image's
  Python), the Hub download (`token=False`, xet), and the 14.5 GB re-hash time.
- The tokenizer fingerprint of the real tokenizer (the tests use a fake tokenizer; the function reads the backend's
  `to_str()` model block).
- CUDA itself: numerics, speed, memory, and the default attention implementation. The parity check is the first real
  measurement.
- The real bundle: the builder never opened the dev bank, so no bundle was built from real units.
- The time and cost figures above are estimates.
