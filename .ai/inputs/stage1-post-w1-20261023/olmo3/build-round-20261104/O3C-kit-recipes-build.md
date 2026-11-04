# O3C-kit-recipes build report

Track: O3C-kit-recipes (the probe kit route and the recipes for OLMo 3 7B Instruct).
Worktree: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/ws-c (detached at 5b5b07e; nothing committed).
Scratch: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/tmp/ (the recipe generator, the Gate A copy's test output; every pytest basetemp deleted).
Started 2026-11-04 10:49 UTC; finished 11:15 UTC (clock checked with `date -u`).
Status: DONE for this track's scope. Not verified by an independent agent (the lead's verify round follows). Open points in §6.

## 1. What is built

(1) **The probe kit** `runkit/family-probe-olmo3/`: a copy of `runkit/family-probe/` (all 20 tracked files; `git status --porcelain -- runkit/family-probe` is empty, checked by a test) with the OLMo 3 entry `olmo3-7b` shaped as the OLMo-2-7B entry, the lock packed by hash, the probe's own preflight step, a 7.0 h cap, the Gate A shape in the plan tool, a `--dry-run` pack, tests (33 passed) and a README with the runbook.
(2) **The recipes**: nine files `experiments/safety_selection/configs/study-kt-olmo3-7b-r64-{b,b5e5,b2e5}-{mb2,mb1-gc,mb2-g16}-20261104.json` (3 rungs × the memory ladder), each the OLMo-2-7B candidate of 2026-10-08 with only the model fields of O3A §16.1 / CM §2.2, the LR and the name/purpose changed; all nine load through the engine's `load_recipe` (main environment), guard equal to recipe B's.
(3) **The ids-only control-token count** `runkit/family-probe-olmo3/control_token_count_olmo3.py`; **the Gate A tool copy** `runkit/family-probe-olmo3/gate_a/gate_a_common_olmo3.py` with plans `olmo3-B`, `olmo3-B5e5`, `olmo3-B2e5` (the recorded `tmp/gate-a-common-recipe/gate_a_common.py` 7faf2164… untouched); **the state rule** as `host.py pull-states` + `states_tool.py check` and the rule text, as far as the records define it.

## 2. Step log (every command, exit code)

| UTC | Command (from the worktree root unless said) | Exit |
|---|---|---|
| 10:49 | `date -u`; `ls` of the scratchpad, reports, ws-c; `git status --short`, `git log --oneline -1` (ws-c) | 0 |
| 10:49–10:56 | `sed -n`, `cat -n`, `grep -n`, `wc -l`, `diff`, `shasum -a 256` reads of: the readiness scout (§0–§4), O3A (whole), MC (whole), CM (whole), FOCUS (the OLMo 3 lines), the five `olmo3/` records, FPK's 13 scripts and 6 setup files, `experiments/safety_selection/tests/test_ss_probe_runkit.py` (index, lines 1–140, 238–350, 854–1000), `test_ss_family_recipes.py` (1–60), the OLMo-2-7B and Llama b/b5e5 recipe diffs, `study-kt-data-dolly-olmo2.json`, `scripts/family_probe_reading.py` (80–92, 137–160, 296–310, 380–440), `scripts/cuda_preflight_family.py` (1–60), KCR (grep KD5/KD7/KD10), `runkit/stage1-olmo/stage1_rules.py` (10–60, 393), `runkit/stage1-olmo/pack_setup.py` (grep lock), `tmp/gate-a-common-recipe/{gate_a_common.py,gate_a_common_test.py,README.md}` (main checkout, code only), the working copies' `plan_tool.py`/`probe_constants.py`/`host.py`/`budget.py` constants (`tmp/family-probe-*`, code only) | 0 (one `sed` with a bad address: 1, re-read) |
| 10:56 | `rsync -a --exclude __pycache__ runkit/family-probe/ runkit/family-probe-olmo3/`; `cp` of the lock record to `setup/requirements-olmo3.lock`; `cp` of the Gate A tool and its test into `gate_a/`; `shasum -a 256` of both copies (lock e4aedff8…, tool 7faf2164…) | 0 |
| 10:57–11:02 | Write/Edit: `probes.py`, `probe_constants.py`, `plan_tool.py`, `pack_setup.py`, `setup/preflight_probe.py`, `host.py`, `budget.py`, `fetch_tokenizers_mac.py` (see §4) | — |
| 11:04 | `venv/bin/python -B -I scratchpad/o3/tmp/make_olmo3_recipes.py <ws-c>` (the nine recipes, exclusive create) | 0 |
| 11:05 | `venv/bin/python -B` loading all nine with `load_recipe` + `config_sha256` (guard == B's; mb×acc == 128); `shasum -a 256` of the nine | 0 |
| 11:06 | `venv/bin/python -B -c "...code_identity()['sha256']"` → `472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892` (engine X unchanged at 5b5b07e) | 0 |
| 11:06–11:09 | Write: `control_token_count_olmo3.py`, `states_tool.py`; a Python patch of the Gate A copy and its test copy; `python3 -m py_compile` of every edited file (one IndentationError in the patched PLANS table, fixed; then all compile) | 0 after the fix |
| 11:09 | `python3.11 -B runkit/family-probe-olmo3/gate_a/gate_a_common_olmo3_test.py > scratchpad/o3/tmp/gate_a_olmo3_test-output.json` — first run: exit 1, R1–R3 needed the real 1B baseline under `tmp/` (absent in ws-c); the R cases were made synthetic (folders with a COMPLETE.json marker only); second run: **exit 0, `{"run": 21, "not_run": 5, "failed": 0}`** (the 5 not run are the P/I identity cases on real 1B units) | 1, then 0 |
| 11:11 | `venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=<scratch>/pytest-o3c-1 runkit/family-probe-olmo3/tests` — 29 passed, 4 failed (the copy's ROOT is the temp folder in two tests; the dry-pack output parse; the test file's own fake ssh key tripped the secret scan); fixed | 1 |
| 11:12 | the same, basetemp `pytest-o3c-3`: **33 passed in 0.48 s** | 0 |
| 11:13 | `... pytest -q -p no:cacheprovider --basetemp=<scratch>/pytest-o3c-4 experiments/safety_selection/tests/test_ss_family_recipes.py experiments/safety_selection/tests/test_ss_probe_runkit.py` (the engine's recipe test and the original kit's test, unchanged files): **181 passed in 1.40 s** | 0 |
| 11:13 | the real dry pack in ws-c (`pack.main(["--dry-run"])` with PROBE/PREPARED set in process): **refused, "engine files are not committed:" listing the nine untracked recipes** (the kit's own rule, as the original; see §6 point 2). Nothing written under `setup/` | AssertionError (expected) |
| 11:14 | `git status --porcelain`; `shasum -a 256` of every new file; `git status --porcelain -- runkit/family-probe` → 0 lines; `git diff --stat HEAD -- runkit/family-probe scripts experiments/safety_selection/*.py experiments/minimal_safety` → empty | 0 |

Every pytest basetemp folder was deleted after its run; every `__pycache__` under the kit removed. No network, no install, no pod, no git state change, no file of the main checkout touched.

## 3. Files changed (all new; worktree-relative; SHA-256)

Recipes (experiments/safety_selection/configs/):
- study-kt-olmo3-7b-r64-b-mb2-20261104.json 107152f73f58ac8e7ae33bd42252747d04374d9cd4ff760160664ec67f282fe7 (config_sha256 aa950474faf20db8793ef153afc9d20ea28cd175a410727b3808c8e4bfdc8408)
- study-kt-olmo3-7b-r64-b-mb1-gc-20261104.json 1b028adc203b54c05b56a5749e728ee85a3416e98c5fd01fd9af645fdf294776 (1273450a…)
- study-kt-olmo3-7b-r64-b-mb2-g16-20261104.json 42912c85c0b11ebc5e46e7e3f2e85d901a99d8a6248196bc13919a2a44b50ec5 (d715b016…)
- study-kt-olmo3-7b-r64-b5e5-mb2-20261104.json fee0c2c3c4d01f2a757e98be31051c95856f7b53af2c33aee9564731bfbb098a (321c7b1fbb96476d63d804361beeaeac96b449f5ac8ed6ad911351a27fb30347)
- study-kt-olmo3-7b-r64-b5e5-mb1-gc-20261104.json 64acdedc84a1f6e940d65a9514411a9f9d18a9eb8d7b531bacbdfa2d50840d8d (ea0a088c…)
- study-kt-olmo3-7b-r64-b5e5-mb2-g16-20261104.json 0c659bb4dfe15fce467e80bca571b4185b89d1e12eec6f82bf9520f863aca13a (a7da1ab8…)
- study-kt-olmo3-7b-r64-b2e5-mb2-20261104.json 895232eb13a25d9f944dbb8f32a593d98c5f0dc4339ce9d938b18ba2a989f2bc (ecc2e1c10bf151e9c12373bb495d6744fbff1616c87bca9a873fb51792bd7976)
- study-kt-olmo3-7b-r64-b2e5-mb1-gc-20261104.json f54d99d3655102fed7ffe30ff4b9eb2b98736e80b718af08b31e3ae7cdee1648 (d6ca3e8a…)
- study-kt-olmo3-7b-r64-b2e5-mb2-g16-20261104.json dccb73f9a0ddf5ed6f9e6ba37021a15f9a9e4ed4fc58345aee4fe1d7a069820f (ccbaa3f9…)

Kit (runkit/family-probe-olmo3/); E = edited against the original kit's file, U = unchanged copy, N = new:
- README.md N 50efd75180bc07b8f89d1811636b45f29ecffb312469e00a3036559762a28e9f
- probes.py E dd0507294091cddb8258211f9ffe5567e36da53825466c9fa5372057b6c3d6c5
- probe_constants.py E da6d0c0041c11df05be536f61541d3aec86e2ed90be65c556dfc2374d8b614a1
- plan_tool.py E 04cb07d423ee669a944172a408014f41879be53f7ac7a69097e9d0bed0d15cda
- pack_setup.py E b00f8c87051a402a52a23907e3ba52f043bc8a7d5007d633d45265e1aae1c15d
- host.py E a909fc649d7bea787938894350fee19e42d7982d75da0119d45bf2f4d69280eb
- budget.py E 05be8a5ce1620fd31048d2ce5d396dd989e3e57259209575b73dc5e4e6f38f09
- fetch_tokenizers_mac.py E 9e5237bea4a90e0d5ba237c192be24ee61190282e4f6461ec2ffb5b835fd3145
- setup/preflight_probe.py E dd39841a001c8ef831c6ca8eae5e34ffd110c4a88e8201a31d7db7c7d618bc8b
- setup/requirements-olmo3.lock N (a byte copy of the frozen record) e4aedff89a4bb0937f7e9f958beee8eb92f8e653a5b498d51e28da091c96ba66
- control_token_count_olmo3.py N 697d50ffde6ad089bbd9e187f6887afe0c227d28f4a4c9b323b52d8be9a6d43a
- states_tool.py N 29ff23cb2a88e4f6edb4c5141c10b64da426126aeb45a55521ccfeeb207a976e
- gate_a/gate_a_common_olmo3.py N (edited copy of 7faf2164…) 53f476375c95c205c04e92feb473af722d37071edf176ddb7ac1f6e727c69e28
- gate_a/gate_a_common_olmo3_test.py N (edited copy of b6a5bb36…) b3496836c1f104a13c5cb8e963768c12239dc46a06c333806c224423d3106ca0
- tests/test_family_probe_olmo3.py N e6eef7c1bd3206188fb17c88874f9a49509cdbd36de50550cd7d6deeadc3f49b
- U (byte-equal to runkit/family-probe/, checked by a test): account.py 8e3b8c4e…, finisher.py 9a9a2b7f…, launch.py e9e435e8…, orchestrate.py 30f9fbe0…, second_judge_probe.py c51e466c…, secret_scan.py 75baad4c…, status.py 13be95a6…, setup/bootstrap_hr.sh bdd16b0e…, setup/download_models_probe.py f790ee60…, setup/extend_cap.py 8af2f6cc…, setup/job_runner_probe.py 6bbe6f47…, setup/setup_and_fetch_probe.sh 70caf0d5…

Evidence in scratch: `scratchpad/o3/tmp/make_olmo3_recipes.py` (the generator), `scratchpad/o3/tmp/gate_a_olmo3_test-output.json` (21 run, 0 failed, 5 not run).

## 4. Design and rejected alternatives

**Kit route.** A copy at a new path, as the scout (§2.4) and O3A §16.8 recommend; the original kit is not edited (Gate B pins its fixture path, CM D-O7). Changes, file by file:
- `probes.py`: entry `olmo3-7b` = open repository `allenai/Olmo-3-7B-Instruct` @ `6e5971d9eba42665f5bd5a0fcf047f299ce1dccc`; `weight_pins` = the three shard LFS SHA-256 values of MC §1 with their byte sizes (`weight_bytes`, sum 14,596,063,712); download `patterns` = `WEIGHTS + ["chat_template.jinja"]` (blocker B2; `download_plan` takes an open entry's `patterns`); `audit_tokenizer` None (the model's own snapshot; CM §6 alternative 2 rejected the OLMo-2 pin); `prepared` `prepared-kt-dolly-olmo3`; `recipes` = rung 1's ladder and `rungs` = {1,2,3} → the memory ladder mb2, mb1-gc, mb2-g16 at b / b5e5 / b2e5 (CM D-O5; mb4 dropped, KCR §6); `lock` = {kit copy path, record path, SHA-256 e4aedff8…}; `preflight_script` `cuda_preflight_olmo3.py`; cap 7.0 h (O3A §1.2), wait 5,400 s, 60/30 GB (the OLMo-2-7B sizes). New helpers `recipes(probe, rank, recipe, rung)`, `lock_of`, `preflight_script_of`. The five earlier entries are equal to the original's (a test compares the dicts, the download plans and the ladders).
- `probe_constants.py`: `SEED` (1101) and `RUNG` (1) per working copy; `prepared-kt-dolly-olmo3` in `PREPARED_MANIFESTS`; `MAX_PRICE` 1.85 (the planning rate every working copy has used since 9 Oct; the tracked kit says 1.75).
- `plan_tool.py`: `SEED = pc.SEED` (the Gate A seed kits' change) and `BASELINE_SEED = 1101`; `gate_a_shape()` refuses, with fixed messages: a seed outside 1101–1103 (O3A §16.4); the untuned unit at any seed but 1101 or any rung but 1 (R1); a reuse host at seed 1101 and rung 1 for a probe with rungs (it is the probe pod's own unit; R3–R4 are rungs 2–3). The rung picks the ladder and goes into the plan (`rung`) and its name (`-rung2`, `-seed1102`). A reuse keeps only the candidates whose evaluation config equals the baseline's (the kit's existing rule; so a rung-2 reuse after an mb2 probe keeps `b5e5-mb2` only, tested).
- `pack_setup.py`: `lock_file()` packs the probe's lock as `requirements.lock` (the bundle and the setup archive, so `bootstrap_hr.sh` installs it unchanged) after checking the kit copy's SHA-256 against the pin and, when the record file is present, against the record; the generated pod bootstrap checks the same hash before `setup_and_fetch_probe.sh`, and `BOOTSTRAP-READY.json` records `lock_sha256`; `preflight_script()` packs the probe's script beside the four family scripts and refuses a missing one; `probe.json`, the bundle manifest and the receipt carry `preflight_script` and `lock_sha256`; `--dry-run` runs every check and prints the file list, writing nothing (an absent prepared set is noted, not fatal, in a dry run).
- `setup/preflight_probe.py`: the per-candidate command uses `probe.json`'s `preflight_script` (a plain file name under `scripts/`; `../` or a non-.py name refuses); the script must be in the bundle; `PREFLIGHT-DONE.json` records it.
- `host.py`: `MAX_PRICE` 10.0 with the finite-price refusal (the user's 9 Oct 15:29 UTC rule, as every working copy); `extend-cap` plans at `pc.MAX_PRICE`; new `pull-states HOST CHECKPOINT` (a tar of `round1/*/states/CHECKPOINT`, recorded in `pulls.jsonl` with its hash and kind).
- `budget.py`: `MAX_PRICE` 1.85. `RESERVE_USD` stays 6.0 (the tracked value and FOCUS's reserve).
- `fetch_tokenizers_mac.py`: an `olmo3` family (the six tokenizer/template files plus config.json, blob ids equal to the 1 Nov receipt's; a test compares them when the receipt is present).
- `control_token_count_olmo3.py` (O3A §16.1): per sealed unit and evaluation, the answers whose `output_ids` hold `<|im_start|>` 100264, the FIM ids 100258–100260, `<|endofprompt|>` 100276 or the four function tags 100266–100269; greedy = the harm rows of `generations.jsonl`, sampled = `samples.jsonl` (FPR's definition); reads `output_ids` and `kind` only; every file read must be listed in COMPLETE.json with its current hash; canonical JSON, exclusive create; exit 2 on a refusal. `<|im_end|>` is a stop and therefore absent from `output_ids` (as FPR says of EOS), so it is not in the set.
- `states_tool.py`: `check HOST CHECKPOINT` unpacks the newest states tar (members under `round1/*/states/CHECKPOINT/` only) into the light tree and verifies every state file a unit's COMPLETE.json lists; a stamped record (written once); `rule` prints the rule.
- `gate_a/gate_a_common_olmo3.py`: `ROOT = HERE.parents[2]`; the three plans built by `olmo3_plan(rung, …)` (family None, engine X, the mb2 recipe hash of each rung, manifest `tmp/kt-prepared/prepared-kt-dolly-olmo3/manifest.json`, the baseline = the probe pod's `1101-a0-init-a1`, rung 1 resumes from it and rungs 2–3 are fine-tune-only reuses, no certificate, the ARC layer adopted per FOCUS 9 Oct 15:23 UTC); `refuse_unset_pins()` refuses a plan whose manifest or baseline job.json SHA-256 is None (as they are now). Nothing else changed. The test copy: `import gate_a_common_olmo3`, synthetic R cases, the P/I cases reported "not run" when the real 1B units are absent, new O1–O3 cases.

**Recipes.** Generated from the OLMo-2-7B candidates (`study-kt-olmo2-7b-r64-b-{mb2,mb1-gc,mb2-g16}-20261008.json`) with exactly these model changes (a test asserts the changed-key set): `repo_id`, `revision`, `architecture` `Olmo3ForCausalLM`, `stop_tokens` `["<|endoftext|>", "<|im_end|>"]`, `assistant_header` `"<|im_start|>assistant\n"`, no `tokenizer` field (the model's own snapshot); `end_of_turn_token` `<|endoftext|>` and `pad_token` `<|pad|>` are the same as OLMo-2's; `expected_trainable_parameters` 159,907,840 (MC §4 arithmetic; see §6 point 3); `train.lr` 1e-4 / 5e-5 / 2e-5 by rung; the purpose text names O3A §16.1–16.2, the default system block (D-O1) and the lock. Date suffix 20261104, so the engine's `test_ss_family_recipes.py` glob (`*-20261008.json`, exactly twenty) is untouched (181 passed with the original kit's test file).

**Rejected.** (a) A stage-1 kit fork: bound to OLMo-2-1B's pins, lock hash and probe key (scout §2.4). (b) Editing `runkit/family-probe` in place (CM D-O7). (c) Packing the lock from `.ai/inputs/...` by path: the pack never ships `.ai`; a kit copy pinned by hash and checked against the record is explicit. (d) One probe key per rung (`olmo3-7b-rung2`…): three sets of pins and plan checks for one model; a `rungs` table on one entry keeps the pins once. (e) Keeping the tracked `MAX_PRICE` 1.75: every pod since 9 Oct ran under the $10/h create limit with $1.85/h planning (the working copies), and O3A's guard uses $1.85. (f) A `delete` command for the state rule: the records say "after a verified backup and the user's yes"; the kit keeps no delete path. (g) Counting `<|im_end|>` in the control-token set: it is a stop in every OLMo 3 recipe, so it never appears in `output_ids`.

## 5. Runbook for the lead (the probe pod; every command prints hashes or a fixed message)

Preconditions: track A's `scripts/cuda_preflight_olmo3.py` and track B's `study-kt-data-dolly-olmo3.json` + `tmp/kt-prepared/prepared-kt-dolly-olmo3/` merged; the nine recipes and the kit committed by explicit path (KD8/T3) while no stage-1 pack runs; money check C1 on the live balance (never stage 1b's money). Commands from the main checkout root, `python3.11 -B`.

```
# 0. the working copy (O3A §16.7's family-probe- prefix, so every budget guard sees the cap)
cp -R runkit/family-probe-olmo3 tmp/family-probe-s78-olmo3-7b-probe && cd tmp/family-probe-s78-olmo3-7b-probe
# edit probe_constants.py: PROBE = "olmo3-7b"; PREPARED_MANIFESTS["prepared-kt-dolly-olmo3"] = "<manifest.sha256>"; SEED = 1101; RUNG = 1
shasum -a 256 setup/requirements-olmo3.lock            # must print e4aedff89a4bb0937f7e9f958beee8eb92f8e653a5b498d51e28da091c96ba66
# 1. pack and check (no network)
python3.11 -B pack_setup.py --dry-run                  # the checks and the file list; refuses on a lock, pin, script or git problem
python3.11 -B pack_setup.py                            # prints probe, git_commit, engine_sha256 (472fc7f6...), lock_sha256 (e4aedff8...), bundle and setup hashes
shasum -a 256 setup/setup-receipt.json setup/probe.json setup/bundle-probe.tar.gz setup/worker-setup-probe.tar.gz
python3.11 -B setup/download_models_probe.py --dry-run --probe-file setup/probe.json   # the plan: policy (patterns include chat_template.jinja) and guard; nothing gated
python3.11 -B plan_tool.py init                        # prints {"recipe": null, "hosts": ["olmo3-7b-1101"], "rung": 1}
(mkdir -p /tmp/o3-dry && cp plan.json setup/probe.json /tmp/o3-dry/ && cd /tmp/o3-dry && python3.11 -B <kit>/setup/preflight_probe.py --dry-run)   # three commands naming scripts/cuda_preflight_olmo3.py
python3.11 -B budget.py check 7.0 1.85                 # exit 0 (allowed) or 3; prints balance, committed_upper_usd, new_pod_upper_usd 12.95, reserve 6.0
# 2. launch as a background job (foreground return kills the pod setup; one launch.py and one finisher per kit)
nohup python3.11 -B launch.py olmo3-7b-1101 > launch.log 2>&1 &
nohup caffeinate -i python3.11 -B finisher.py > finisher.log 2>&1 &
python3.11 -B status.py                                # local records only; orchestrate.jsonl events: checked, bootstrap-started, bootstrap-ready, preflight-finished, expected-fixture-recorded, job-started (or pre-job-failed / cap-insufficient, then the pod is stopped)
# 3. after hosts/olmo3-7b-1101/finished.json says "verified-and-stopped"
python3.11 -B host.py pull-states olmo3-7b-1101 e1 && python3.11 -B states_tool.py check olmo3-7b-1101 e1    # "states verified: 2 units"
python3.11 -B control_token_count_olmo3.py --unit retrieved/olmo3-7b-1101/tree/round1/1101-a0-init-a1 \
    --unit retrieved/olmo3-7b-1101/tree/round1/1101-a0-e1-a1 --out control-tokens-1101.json
# the one-seed read: scripts/family_probe_reading.py without --family (O3A §16.1); the lead records the manifest's and the
# baseline's pins in gate_a/gate_a_common_olmo3.py (MANIFEST_OLMO3_SHA256, the baseline job_sha256, and the recipe hashes if the
# preflight chose mb1-gc or mb2-g16); then, after seeds 1102-1103: gate_a_common_olmo3.py --plan olmo3-B [--partial]
```
Later hosts: a new copy per pod named `tmp/family-probe-s78-olmo3-7b-rung2`, `-rung3`, `-seed1102`, `-seed1103` (or `-rung<r>-seed<s>`), `SEED`/`RUNG` set, `plan_tool.py init --reuse-baseline tmp/family-probe-s78-olmo3-7b-probe/retrieved/olmo3-7b-1101/tree/round1/1101-a0-init-a1`; the same pack, check, launch and finisher steps. The Gate A copy's plan paths pin these names.

## 6. Open points for the lead

1. **Track A's preflight.** `scripts/cuda_preflight_olmo3.py` must take `--recipe RECIPE --prepared PREPARED --out FOLDER` and write `FOLDER/verification.json` with the family preflight's fields (`verdict.use_this_recipe`, `generation_memory_ok`, `batch_proof_ok`, `tokenizer_ok`, `init_equals_untuned`, `full_length.ms_per_step_full`, `cap_projection.*`), because `setup/preflight_probe.py` and the job runner read exactly those. Until it is merged, `pack_setup.py` refuses with "scripts/cuda_preflight_olmo3.py is missing".
2. **Commit by explicit path.** The nine recipes sit under `experiments/`; the kit's pack (and every stage-1 pack) refuses while they are uncommitted ("engine files are not committed", seen in the real dry run). KD8/T3: commit them, the kit and track A's script by explicit path when no stage-1 pack is in progress; never `git commit -a`.
3. **The LoRA count.** `expected_trainable_parameters` 159,907,840 is MC §4's arithmetic (the OLMo-2-7B shapes). Track A's meta-device count must confirm it; the engine refuses a mismatch at load, so a wrong value costs one pod setup.
4. **Pins to record** before the first pod: `PREPARED_MANIFESTS["prepared-kt-dolly-olmo3"]` (track B's `manifest.sha256`) in the working copy, and in the Gate A copy `MANIFEST_OLMO3_SHA256`; after the probe pod seals, the baseline's `job_sha256` and, if the preflight chose mb1-gc or mb2-g16, the three recipe hashes (now the mb2 ones). The tool refuses an OLMo 3 plan until the manifest and baseline pins are set.
5. **The shard pins** are MC §1's values (two summarizer reads agreed; not a byte-level read). The pod checks each shard's SHA-256 against its blob name and the pins before the preflight; a mismatch stops the pod (about $0.55–1.10 lost). A direct Hub API read of the three LFS hashes (O3A lead item 3) is still the cheaper check, if the lead allows one network read.
6. **Money constants.** I adopted the working copies' values (host create limit $10/h, planning $1.85/h, reserve $6). The lead confirms, or sets the reserve per the current rule (the 7–8B copies ran with $1 on an 8 Oct instruction).
7. **One cap per entry.** Every OLMo 3 host inherits `cap_hours` 7.0 from the entry; KCR's tight value for a fine-tune-only pod is 4.25 h. The lead may lower `cap_hours` in a seed copy's `probes.py` (the plan copies it at `init`); no per-role cap field was added.
8. **The state rule's gaps.** The records name the a0 e1 adapters only; whether init and q states are pulled, the backup's name, and who says yes per pod are open. The kit has no delete path.
9. **The Gate A copy's test** ran 21 of 26 cases here; the P/I cases need the real 1B units under `tmp/` (the main checkout). Run `python3.11 -B runkit/family-probe-olmo3/gate_a/gate_a_common_olmo3_test.py` once from the main checkout after the merge to get all 26 (it reads those units' identity and job records only).
10. **Working-copy names** are pinned in the Gate A plans (`tmp/family-probe-s78-olmo3-7b-probe`, `-rung2`, `-seed1102`, …). Use them or edit `olmo3_plan()`.
11. **Granite.** `second_judge_probe.py` (the Mac GGUF route) is an unchanged copy; O3A §16.2 expects Granite from a judge pod later. Not built here.
12. **P0–P4, the input choices and the predictions** are track B's draft for the lead to commit before the first fine-tune; the recipes fix the input choices as O3A recommends (default system block kept; end of turn `<|endoftext|>` with both stops).

## 7. Acceptance criteria

- Kit copy with the OLMo 3 entry shaped as the OLMo-2-7B entry (open repo, three shard pins, jinja pattern, lock by hash, preflight step, 7.0 h cap, Gate A shape): PASSED (tests `test_the_olmo3_entry_shape`, `test_the_five_earlier_entries_equal_the_original_kits`, `test_the_pack_checks_the_lock_by_hash_and_needs_the_preflight_script`, `test_the_preflight_wrapper_runs_the_probes_script`, `test_the_plan_tool_keeps_the_gate_a_shape`).
- Original kit unchanged: PASSED (`git status --porcelain -- runkit/family-probe` empty; `test_the_original_kit_is_unchanged`).
- Tests for the entry and its refusals: PASSED (33 passed).
- A dry pack: PASSED in the test with a stand-in script and a fake git (`test_the_dry_pack_lists_the_lock_and_the_script_and_writes_nothing`); the real dry run in ws-c refuses as designed (uncommitted recipes; track A's script absent). NOT TESTED: a real pack (needs the prepared set, the script and the commits).
- Nine recipes, new files only, loading with the engine: PASSED (9 `test_each_olmo3_recipe_is_recipe_b_with_the_olmo3_model_fields` cases; `test_ss_family_recipes.py` still 20 recipes at 20261008).
- Ids-only control-token count: PASSED on synthetic rows (no text printed; sealed-hash refusals).
- Gate A tool copy with the OLMo 3 keys, tests re-run: PASSED 21 run / 0 failed; 5 cases not runnable here (need the real 1B units).
- State rule: built as far as defined (pull, check, rule text); the gaps are in §6 point 8.
- Nothing run on a pod, no network, no install, no commit: PASSED.
