# The 7-8B kit (runkit/stage1-78b), block 0 (K1)

The run kit for the 7-8B tier of "Diagnose or Retrain?" (OLMo-2-7B and Llama-3.1-8B): the lead's Part 1 rulings
(`.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md`, ruling 11 KD1-KD11) and their addendum
(A1, A2, A8, A13), the readiness plan's T4. It is route (ii) of KD10: a copy of the stage-1 kit `runkit/stage1-olmo/`
(every tracked file, byte for byte, at the commit `COPY-MANIFEST.json` names; the original stays untouched, stage 1c
and stage 2 still read it) with per-family constants and the measured M-cap rule from `rules_78b.py` (T2;
`RULES-78B.md`). This round (K1) builds the block-0 subset: the kit shell, `plan_tool.py init-block 0`,
`pack_setup.py` for engine X, the family rule, the money printout. K2 built the job runner's 7-8B changes (`s_obs`
after each arm, the free-space check, the arm commands, the states pull). K3 built the gated-token launch path for
Llama (T4 step 2; the section "Launching block 0" below). The scorer kinds' jobs and the retrain pod's launch are the
next stages' (the K1 and K2 reports list what each inherits).

## One family, one block per working copy (KD7)

A working copy is `tmp/family-probe-s78-<family>-<block>/`, for example `tmp/family-probe-s78-olmo2-7b-0/` and
`tmp/family-probe-s78-llama31-8b-0/`. The folder's name IS the family: `stage1_rules.FAMILY` is read from it (or from
`kit-family.json`, which the pack writes for the pod; both must agree). Everything per family (the main config `REC`,
`PROBE_KEY`, the prepared set and its manifest, the sealed edit set, the fixture, the a0 side units, the models, the
training identity) comes from `rules_78b.KIT[family]`. A jobs file, a plan.json, an `--inputs` record or `--family`
that names the other family refuses; the committed `runkit/stage1-78b/` itself names no family and plans, packs and
launches nothing. The frozen stage-1 `budget.py` (`KITS_GLOB` `family-probe-*`) sees every 7-8B pod's cap (C7);
`budget.py` here is byte-identical to the stage-1 kit's.

## Block 0 = N (ruling 11)

| Family | Pod | Jobs | Cap | Spend upper |
|---|---|---|---|---|
| OLMo-2-7B | `olmo2-7b-0-1` | arm R_1, R_2, R_3 at seeds 1101-1103 (R_d at 1100 + d), 33 steps, main config `18cc31d7…` | 8.50 h | $12.50 |
| Llama-3.1-8B | `llama31-8b-0-1` | the same three plus a0_arm at 1103 (38 steps; ruling 8), main config `74758af1…` | 12.50 h | $20.80 |

In parallel, one launch: guard $44.85, need **$56.06** with the contingency 1.25 (KCR:177). The arms run under the
family's MAIN config, never a recipe-S sibling (P78:99). OLMo-2-7B's R_d1-R_d3 are Gate B's sealed edits
(`.ai/inputs/gate-b-sealed-20261008/out/edits/R_d{1,2,3}.json`, bound by path and SHA-256 from the set's MANIFEST,
pinned in `rules_78b.SEALED_SETS`). Llama-3.1-8B's come from `.ai/inputs/scale-78b-sealed-llama3-20261105/` (committed
at d422fca; MANIFEST `2a1db220…`, the pin the lead filled by PP7): R_d1-R_d3 = `5cdedf22…`, `8f9f3cd5…`, `edbc111b…`
at seeds 1101-1103. The two committed MANIFESTs have different forms (Gate B's `role: "edit"` entries, with M-family
edits at draws 1-2 of their own; the Llama set's descriptive role strings with a `seed` per R entry): the kit reads
both through `rules_78b.block0_r_edits`, by family "R" AND draw (RULES-78B.md, "The sealed edit sets"). Each edit file
must carry the family's prepared manifest (one key read; no row id).

    PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
    K=tmp/family-probe-s78-olmo2-7b-0            # the working copy (a copy of runkit/stage1-78b/ without tests/)
    $PY -B $K/pack_setup.py X --dry-run           # engine X 472fc7f6..., the main config, the prepared manifest, the sealed set
    $PY -B $K/pack_setup.py X                     # setup/packed-stage1-X/ (records HEAD; refused while experiments/ or scripts/ is dirty)
    $PY -B $K/plan_tool.py init-block 0 --jobs JOBS.json --dry-run
    $PY -B $K/plan_tool.py init-block 0 --jobs JOBS.json --funding FUNDING.json

`JOBS.json` is `{"family": "olmo2-7b", "launches": [{"hosts": [[{"kind": "arm", "arm": "R", "seed": 1101}, {"kind":
"arm", "arm": "R", "seed": 1102}, {"kind": "arm", "arm": "R", "seed": 1103}]]}]}`; Llama's adds `{"kind": "a0_arm",
"arm": "a0", "seed": 1103}`. Any other layout refuses. `init-block 0` prints, one per line, the need of N's pods
(both families), of this family's pod alone, of each family's retrain pod (ruling 10; addendum A2, A8: one single-job
pod per family, recipe S_78, after the anchor job; `rules_78b`'s retrain E cap 4.5 h) and of each scorer pod (the
check's C1 and M3; `rules_78b`'s E caps), then the JSON summary.

## The pre-block-A scorer block "sc" (K4b; ruling 11 KD6, KD10; the check's C1, M1, M3; A1, A2, A8, A13; PP1-PP16)

Its own working copy per family, `tmp/family-probe-s78-<family>-sc/` (KD7). Every pod holds ONE job of
`rules_78b.SC_KINDS` with its explicit E cap (KD6): `anchor` (`scripts/make_anchor_answers.py` under the main config),
`untuned_answers` (two wrapper calls, PP1, PP2: the S3 list with the losses, then the S4 list alone; one 6.0 h cap for
both), `o_only` (theta0's O-ext pass, M1), `o_only_with_regenerate` (PP17: a reused a0 side unit regenerated train
only, verified by the engine, checked against the side unit's COMPLETE.json fingerprints (q and e1 adapter and
optimizer, training identity, manifest; a unit that differs is complete with acceptance false and reason LS-04 and gets
no O-ext pass), then the O-ext pass on its e1 state; one pod per reused seed; there is no standalone `regenerate`
kind), `c0` (B17's X-pin check on N's R_1; unitless, PP18: its outputs under job-I/c0 are hashed, `c0_record.json`
named), `l1_scan`, `rep_pass` (REQ-3's two passes, S_78), `classifier` (S_78, PP4), `retrain` (a0-1101, S_78, engine Y
first, X only as ruling 10's pre-set second job) and `a1_pass` (on the engine that trained the retrain's states). Every
unit the runner records (the retrain, `a1_pass`'s attributes unit, the regenerated unit) is checked by the engine's
`verify` right after the step that writes it; a non-zero exit is a crash (round 4b, the core verifier's D2). The
wrapper kinds run `scripts/scale78b/scorers_78b.py` with `-I -B` (SCORERS-78B.md section 2's commands); the engine
kinds run the engine's `make-job` and `run-one` / `attributes`.

    K=tmp/family-probe-s78-olmo2-7b-sc
    $PY -B $K/pack_setup.py X --inputs PART1-INPUTS.json --inputs-sha256 H --dry-run     # the scorer code at its pins, the inputs
    $PY -B $K/pack_setup.py X --inputs PART1-INPUTS.json --inputs-sha256 H
    $PY -B $K/plan_tool.py init-block sc --jobs PART1.json --dry-run                     # each pod's need and idle line
    $PY -B $K/plan_tool.py init-block sc --jobs PART1.json --funding FUNDING.json

`PART1.json` is `{"family": "olmo2-7b", "launches": [{"hosts": [[{"kind": "anchor"}], [{"kind": "untuned_answers"}]]}]}`;
an inputs record is `{"kind": "stage1-78b pack inputs", "engine": "X", "family": F, "inputs": [{name, path, sha256}]}`
with the names of `stage1_rules.SC_INPUTS` (each SHA-256 its pin: the 1B sealed lists and the anchor prompt list from
`pins_78b.json` shared; the anchor bank, the s3_orig pool and the retrain unit from the family's `pins_78b.json` block;
N's R_1-1101 COMPLETE.json from `rules_78b.C0_SOURCE`; the O-ext bank and record from `rules_78b.OEXT_78B`; the reused
side unit's COMPLETE.json `side_complete:a0:<seed>` from `rules_78b.KIT[family]["a0_units"]`, ruling 7's pin).

- **A2's order, enforced by the planner.** `init-block sc` runs once per part. A kind is planned only when the kinds
  before it are recorded complete in the copy's plan (`rules_78b.SC_AFTER`): the anchor job before `l1_scan`,
  `classifier`, `rep_pass` and the retrain; the untuned pass before `rep_pass`; the retrain before `a1_pass`.
- **Pins (A13's pattern).** A job refuses at planning, at release and on the pod while a pin it needs is null
  (`rules_78b.SC_KIND_PINS`, `sc_missing_pins`; the scorer layer's own settings waits too): `RECIPE_S` (equal to
  `pins_78b.json` `recipe_s78`), the anchor bank, the s3_orig pool, the retrain unit, `ENGINE_Y` for a Y job,
  `OEXT_78B` (o_only, o_only_with_regenerate and c0: the O-ext pass at 7-8B needs re-derived settings, M1, PP17; its
  form is exactly `{"files": {path under scripts/: SHA-256}, "inputs": {"oext_bank": SHA-256, "oext_record": SHA-256}}`,
  validated) and `C0_SOURCE` (c0). All are null in the committed files; the tests fill them test-locally.
- **The anchor bank and s3_orig pins are this copy's recorded outputs** (round 4b, the core verifier's D5): a kind that
  reads them is planned only when the pin equals the SHA-256 a complete anchor (untuned) job of this copy's plan
  recorded (record-done keeps each scorer job's `scorer_record`, hashes only).
- **Between parts** the lead fills the next pins from `record-done`'s printout (`scorer_block`: the anchor file's
  SHA-256, the s3_orig pool's, the retrain's COMPLETE.json and fingerprints; hashes, counts, the wrapper's exit codes and
  fallback flags only), moves the earlier `setup/packed-stage1-X` aside and re-packs with the part's inputs record.
- **The bundle** carries `stage1_rules.SCORER_PINS` (38 files: the wrapper, its settings index, `pins_78b.json`, the 18
  settings files, the 1B scripts it imports with `labels.json` and the lexicon, the anchor job's script), each at its
  SHA-256; a changed file refuses at pack time and at release.
- **The pack's secret scan** (round 5, K5; the lead's R4 ruling) covers every file it ships except the prepared set's
  manifest-listed files: the engine files, the scorer code and scripts, the edit files under `edits/`, the configs,
  the named inputs under `inputs/` (non-binary files), the generated payloads (bundle manifest, sealed-files, probe,
  kit-family), the worker bootstrap and every member of `worker-setup-stage1.tar.gz`; a hit refuses with names and
  pattern names only. Under `data/` (the prepared set; round 6, K6, the lead's ruling on K5v-3) the pack scans every
  file that the set's `manifest.json` does not list in its `files` map (for example `prepare_receipt.json`, which the
  engine writes outside the manifest hash, and `manifest.json` and `manifest.sha256` themselves), skips `.DS_Store`
  and the other macOS metadata files by name (`pack_setup.MACOS_METADATA` and `._*` files: neither packed nor
  scanned), and keeps the files `manifest.json` lists outside the scan, because the manifest pins them. A listed file
  stays outside only at its listed SHA-256, and only while `manifest.json`'s own SHA-256 is the family's pin
  (`stage1_rules.PREPARED_MANIFESTS`); otherwise it is scanned too. A refusal that comes after the bundle is written
  (the bootstrap, the setup tar) leaves a partial `setup/packed-stage1-X/` with no `setup-receipt.json`; move it aside.
- **c0's expected fingerprint** (round 5, K5): the pod reads the e1 adapter fingerprint from the packed source unit's
  `COMPLETE.json` (re-hashed against its pin; the stage-1 kit's `@fingerprint` form) and refuses before any step when
  it differs from the plan's `expect_fingerprint` (`C0_SOURCE[family]["e1_fingerprint"]`). Round 6 (K6, the 7 Nov
  ruling on Part 2's item 23) adds the same check on the Mac: `pack_setup.py` (the pack and its dry run) reads the
  packed source unit's `checkpoints.e1.adapter_fingerprint` and refuses when it is missing or is not
  `C0_SOURCE[family]["e1_fingerprint"]`, so a typing error in the lead's step stops before any pod starts.
- **Engine Y.** The Y retrain is planned (with `ENGINE_Y` filled) but released only onto a `packed-stage1-Y` stage;
  `pack_setup.py` packs engine X only (Y's pack comes with KD9).

## Money (unchanged from the stage-1 kit)

Planning price $1.85/h at the guard, spend rate $1.79/h, create refused above $10.00/h, $6 reserve, contingency 1.25;
`GATE_B_HOLD_USD = 0` ("Gate B closed 23 Oct (FOCUS 'GATE B CLOSED', recorded 2026-10-23T05:26 UTC); its last judge
pods deleted 31 Oct", KD4). `init-block 0 --funding FILE` takes the stage-1 kit's funding record unchanged: {block
"0", amount_usd >= the need ($56.06), utc (UTC, not in the future), source "user RunPod top-up" or the user's rule
"user rule: start from the balance" with its decision record (addendum §36), user_words, recorded_by}. The user's
guard-off decision (`record-guard-off`) carries over: `launch.py` and `host.py extend-cap` go past the live-balance
guard's refusal with it (the balance is still read and logged); in-pod stop timers at the cap; stop, never delete.
Every pod starts on new money in the account (MONEY; the lead reports, never asks).

## Pins that are null until a recorded lead step (addendum A13)

`rules_78b.RECIPE_S` (each family's S_78, after its anchor job; A1), `RECIPE_G`, `RECIPE_BQI` (B+Qi; KCR:128),
`ENGINE_Y` (then the E-capped kinds outside `X_ONLY_KINDS` may run on Y; PP16: `untuned_answers`, `o_only`,
`o_only_with_regenerate` (PP17), `anchor`, `rep_pass`, `l1_scan`, `classifier` and `c0` run on X only, checked first in
`engine_allowed`) and `Y_MEASURED` (measured kinds on Y only after KD9's re-measure),
`probes.BASE_MODELS[*]["revision"]`. (`SEALED_SETS["llama31-8b"]["sha256"]` was filled by the lead's recorded step
PP7 with the committed MANIFEST's `2a1db220…`.) Every kind that needs one refuses until it is filled; the S_78 kinds
(`retrain`, `rep_pass`, `a1_pass`, `classifier`; PP8) refuse to run (`rules_78b.job_decision`, `check_keys`) through
`recipe_s_or_refuse`, and the retrain refuses to be planned (`stage1_rules.retrain_job`), while every pod's need still
prints (M3): `a1_pass` at A1's 16.5 h cap at most, `rep_pass` at its own 4.75 h E cap (the 1B 1 h estimate x 2.3 x
1.5, until measured), plus KD5's idle-storage line (about $0.33 per day per stopped 50 GB pod) and PP14's line for
each other block-0 pod that keeps states (the two retrain pods, the two a1_pass pods) with the block's total. PP16:
the wrapper kinds (`rules_78b.X_ONLY_KINDS`) run on engine X only, whatever `ENGINE_Y` holds.

## Launching block 0 (K3: the launch path; T4 step 2)

Every command below is run by the lead from the checkout root, each as a **background job** (memory: `launch.py` only
as a background job; a foreground return kills the pod setups), one working copy per family, in this order. `PY` is
the main environment's python (above). Nothing here is run by an agent: the budget check reads the live balance, the
launch creates a pod.

**Before any launch (both families):** merge and pack as the K1 and K2 reports say (`pack_setup.py X` again in a fresh
copy so the setup tar carries K2's runner and K3's `download_models_stage1.py`); `budget.py check` with the live
balance; the funding record (the block-0 need or the start-from-the-balance record).

    K=tmp/family-probe-s78-olmo2-7b-0                                           # OLMo-2-7B: open repositories
    $PY -B $K/pack_setup.py X --dry-run && $PY -B $K/pack_setup.py X
    $PY -B $K/plan_tool.py init-block 0 --jobs JOBS-olmo2-7b.json --dry-run
    $PY -B $K/plan_tool.py init-block 0 --jobs JOBS-olmo2-7b.json --funding FUNDING.json
    $PY -B $K/orchestrate.py check-plan olmo2-7b-0-1                            # $0: every job builds on the packed stage
    nohup $PY -B $K/launch.py olmo2-7b-0-1 > $K/launch-0.log 2>&1 &            # the pod; after-create runs detached

    K=tmp/family-probe-s78-llama31-8b-0                                         # Llama-3.1-8B: the gated policy
    $PY -B $K/pack_setup.py X --dry-run && $PY -B $K/pack_setup.py X           # the sealed-set pin 2a1db220... (PP7)
    $PY -B $K/plan_tool.py init-block 0 --jobs JOBS-llama31-8b.json --dry-run
    $PY -B $K/plan_tool.py init-block 0 --jobs JOBS-llama31-8b.json --funding FUNDING.json
    $PY -B $K/orchestrate.py check-plan llama31-8b-0-1
    # the user puts the HF token in THIS shell's environment first (C13): `source` the secrets file, or
    # `read -rs HF_TOKEN && export HF_TOKEN`; the launcher reads HF_TOKEN only (stage1_rules.TOKEN_ENV_NAMES[0]).
    nohup $PY -B $K/launch.py llama31-8b-0-1 > $K/launch-0.log 2>&1 &
    unset HF_TOKEN                                                              # the lead's shell forgets it too

The lead's steps at each Llama launch (C13: "the HF token in the Mac environment at each Llama launch"):

1. The user hands the token over (the secrets file, or typed into the lead's shell with `read -rs`); it is never pasted
   into a chat, a file under the checkout, a command line or a record. The user's 2026-10-07 decision stands: the token
   is not rotated to a read-only one; the launcher only warns on a wider scope (research/FOCUS.md "Token decision").
2. `launch.py llama31-8b-0-1` (background). Before any pod exists it runs the gated precheck: `HF_TOKEN` must be set;
   GET `whoami-v2` must answer 200 (the role and the scope names go to `hosts/llama31-8b-0-1/token-check.json`; a
   write role or a non-`.read` scope is a `token-scope-warning` line, not a refusal); every one of the policy's ten
   files must answer a Range request with 206. Any other status refuses before the budget check, so no pod waits idle.
   A request that gets no reply (DNS, a refused or reset connection, a timeout, a TLS or certificate failure) is a
   refusal line naming the failure's class and reason with the token scrubbed out, never a traceback; the token is
   removed from the launch process either way (verify-K-gated D4). The Authorization header follows a redirect only
   within the Hub's origin: another host, or https to http on the same host, loses it (D5). A token value with a
   space, a line break, a control or a non-ASCII character inside refuses before any request (http.client's header
   error would quote the whole value in a traceback; fix-K-gated F1); the pod's download script refuses such a line
   too.
3. `host.py reconcile`, `budget.py check` and `host.py create` run with a scrubbed environment (no token variable, no
   variable whose value looks like a token). Only the detached `orchestrate.py after-create` child keeps the
   environment; after bootstrap-ready it hands the token to `host.py gated-download` on stdin, which writes it to
   ssh's stdin, where `download_models_stage1.py --gated --token-stdin` reads it (memory only; `token=` to
   `snapshot_download`; afterwards: no stored login at the library's token path (`HF_TOKEN_PATH`, else
   `HF_HOME/token`, and its `stored_tokens`; the paths follow huggingface_hub 0.36.2's constants.py exactly, `HF_HOME`
   and `XDG_CACHE_HOME` included, D6), no token variable, a cache scan for token patterns in the library's cache
   (`HF_HUB_CACHE`, else `HUGGINGFACE_HUB_CACHE`, else `HF_HOME/hub`), the four safetensors SHA-256 pins,
   `gated-download-receipt.json` with ok false until every check passes; `HUGGINGFACE_CO_STAGING` set refuses). The
   preflight refuses to start without that receipt (its own token check reads the same paths). When the loop ends `launch.py` removes the token from its own environment; `orchestrate.py` does the
   same right after the hand-over.
4. The lead reads `token-check.json` (role, warnings, status codes), `hosts/llama31-8b-0-1/gated-download.json` (ok,
   exit, attempt) and `orchestrate.jsonl`'s `gated-download-finished` line, then `unset HF_TOKEN`. The lead recommends
   revoking the token after block 0's downloads (the 2026-10-07 entry's recommendation).
5. The records never hold the token: `secret_scan.scan_tree(<working copy>)` after the run must report no
   `secret_hits` (the kit's tests do this with a fake token: `tests/test_gated_78b.py`).

OLMo-2-7B's launch never touches the gated path: its download plan has no gated repository, `launch.py` reads no
token, and its orchestrate child is scrubbed like every other child. A `--gated` run on an OLMo plan refuses.

What the finisher adds (K2, K3): before the stop, `host.py pull-states HOST e1` tars every unit's `states/e1/` into
`retrieved/HOST/` (an archive without a file is refused and not kept) and `states_tool.py check` verifies it; nothing
is deleted by this kit (KD5: a delete waits for a verified backup and the user's yes by pod name).

## Tests

    cd <checkout> && PYTHONDONTWRITEBYTECODE=1 $PY -B -m pytest -p no:cacheprovider -q -rfE runkit/stage1-78b/tests

`tests/test_rules_78b.py` (T2's rule, with K1's D1-D7 and A13 cases), `tests/test_kit_78b_shell.py` (the constants
block, the family refusal, block 0's plan and caps, the need printout, the arm commands, the pack on both families),
`tests/test_stage1_runkit.py` (the stage-1 kit's money, funding and guard-off tests ported to block 0),
`tests/test_kit_78b_runner.py` and `tests/test_stage1_runner.py` (K2: the job runner, the preflight, the states tool,
the finisher, the backup), `tests/test_gated_78b.py` (K3: the gated path with fake tokens and no network, the
guard-off and $10/h tests ported to block 0, K6's exit code, pull-states, the pod-side download script; fix-K-gated:
`http_get`'s own wiring through a recorded real opener, the no-reply refusals, the after-download check, the
library's cache and token paths against a reloaded `huggingface_hub.constants`; verify-K-gated D1, D2, D4-D6; F1, a
token value a header cannot carry, and failure_text's two scrubs). The 1B
rounds' copied files (`test_round30a/31/33/34/35.py`, `test_g1_yoext.py`) are one-test pins of what has no subject
here; `test_stage1_judge_route.py` keeps the judge route's own tests. Mutation runs (the lead's background shell, or
in the foreground when under 10 minutes): `tests/run_mutants_78b.py` (T2 and K1), `tests/run_mutants_runner_78b.py`
(K2), `tests/run_mutants_gated_78b.py` (K3's 34 mutants, fix-K-gated's 15 `FG-m-*` and 11 `FX-m-*`).

## Tests never reach the network or a real process (PP10)

`tests/conftest.py` holds an autouse guard over every test in this folder: a real `subprocess` start (every
`subprocess.run` / `Popen` / `check_output` / `os.popen`, however early `subprocess.run` was bound), `os.system`,
`os.posix_spawn`, a socket `connect` and a `urllib` open each raise `NetworkOrProcessRefused` and fail the test at once;
fix-K-gated added `os.fork` / `os.forkpty` / `os.execv` / `os.execve` (so `os.spawn*` and `os.exec*`), the name
lookups `socket.getaddrinfo` / `gethostbyname` / `gethostbyname_ex` / `gethostbyaddr` (loopback names and None
pass) and `sendto` / `sendmsg` on an internet socket (`tests/test_pp10_guard.py`'s G1-G4 tests).
A test that needs such a path replaces the call with a fake first (the module's `subprocess` name, or the function's
`runner=` / `run=` / `get=`); a test that needs the kit's own interpreter or `git` as a real LOCAL child requests the
`local_processes` fixture, which permits those by path and nothing else (never `ssh`, `scp`, `gh`, `curl`,
`caffeinate`, `runpodctl`, a bare `python3`). `tests/test_pp10_guard.py` runs the K3 incident's path
(`host.gated_download` with no fake, `subprocess.run` bound at import) and shows it stops in the guard. The mutation
runners (`tests/run_mutants_*.py`) start pytest as plain processes; the guard is active inside those runs.
K4a added a process-wide layer under the fixture (DK-1): an audit hook installed when pytest imports conftest.py, so
collection, module-scoped fixtures, multiprocessing's spawn and direct os or C-level calls are refused too; the flag
it reads is the same exact-path list `local_processes` fills for one test (`tests/test_pp10_process_wide.py`). Run
mutants of conftest.py under `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'`.
