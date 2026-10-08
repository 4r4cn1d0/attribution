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
| `parity.py`, `PARITY.md` | Mac | The Mac-versus-pod parity check and its pre-set rule. |
| `../tests/test_judge_pod.py` | Mac (minimal venv) | 162 tests with fakes. |

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
| 7 | **A pod may still run.** A stop was not confirmed (`STOP-NOT-CONFIRMED` names the pod ids and the real name); or the create reply was lost, was a 5xx error or was interrupted, and no listing showed a pod, which RunPod may still list (`CHECK-CONSOLE` names the pod name); or no listing worked. | Check the RunPod console now and stop any pod of that name by hand. Its timer stops it at the cap at the latest. |

`parity.py` exits 0 (PASS), 1 (FAIL) or 2 (refused). `judge_pod.py bundle` exits 0 or 2.

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

## Tests

```zsh
setopt interactivecomments
S='<scratch>'
cd /private/tmp && PYTHONDONTWRITEBYTECODE=1 "$PY" -B -m pytest -q -p no:cacheprovider --basetemp="$S/bt" "$K/tests"
```

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
