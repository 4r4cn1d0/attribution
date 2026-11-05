# The OLMo 3 probe kit (`runkit/family-probe-olmo3/`)

A copy of `runkit/family-probe/` (the family-probe kit that ran both 7–8B probes) with one new probe entry,
`olmo3-7b`, for OLMo 3 7B Instruct's Gate A (the readiness scout's kit route, 1 Nov 2026; O3A §16.1–16.2, §16.8;
MC §6.3; CM §2.6). The original kit is not edited (Gate B pins its fixture path). Written 4 Nov 2026 (track O3C).

## What differs from the original kit

| File | Change |
|---|---|
| `probes.py` | entry `olmo3-7b`: open repository `allenai/Olmo-3-7B-Instruct` @ `6e5971d9…`, three shard pins (MC §1), patterns `WEIGHTS + chat_template.jinja` (B2), no audit tokenizer, `prepared-kt-dolly-olmo3`, rung ladders (`rungs`: 1e-4, 5e-5, 2e-5 × mb2, mb1-gc, mb2-g16; recipes dated 20261104), the lock pin (B1), the preflight script name (B3), cap 7.0 h, wait 5,400 s, 60/30 GB. `recipes(..., rung)`, `lock_of`, `preflight_script_of`. The five earlier entries are unchanged. |
| `probe_constants.py` | `SEED` and `RUNG` per working copy; `prepared-kt-dolly-olmo3`; `MAX_PRICE` 1.85 (the planning rate). |
| `plan_tool.py` | `SEED = pc.SEED`; the Gate A shape refusals (`gate_a_shape`); the rung in the ladder and the plan name. |
| `pack_setup.py` | the probe's lock packed by hash as `requirements.lock` (the kit's copy must equal its pin and the frozen record); the probe's preflight script packed and required; `--dry-run`; the pod bootstrap checks the lock's hash. |
| `setup/preflight_probe.py` | the preflight script comes from `probe.json` (`preflight_script`). |
| `host.py` | `MAX_PRICE` 10.0 with the finite-price refusal (the user's 9 Oct rule); `pull-states HOST CHECKPOINT` (an archive without a file is refused and not kept). |
| `finisher.py` | after the light check and before the stop: `pull-states HOST e1` + `states_tool.py check` (`STATE_PULLS`); the result is `finished.json`'s `states` entry; a failed pull or check leaves `review-needed-stopped`; the `states-*.tar` is never removed (fix round 1, D2). |
| `budget.py` | `MAX_PRICE` 1.85. The reserve stays $6. |
| `fetch_tokenizers_mac.py` | the `olmo3` family (seven files, blob ids from the 1 Nov receipt). |
| new | `setup/requirements-olmo3.lock` (the kit's copy, SHA-256 `e4aedff8…`), `control_token_count_olmo3.py`, `states_tool.py`, `gate_a/gate_a_common_olmo3.py` (+ its test), `tests/`. |

Two locks ride in the bundle: `bundle_files()` packs every `.lock` under the two engine folders, so the engine's
`experiments/minimal_safety/requirements.lock` (4.56.2) is a bundle member too; the pod installs only
`/workspace/attribution-headroom/requirements.lock`, which is the OLMo 3 lock from the setup archive, hash-checked by the
generated bootstrap before `setup_and_fetch_probe.sh`.

## The Gate A shape (O3A §16.2, R1–R5)

| Working copy (`tmp/family-probe-s78-olmo3-7b-…`) | `SEED` | `RUNG` | `plan_tool.py` | What runs |
|---|---|---|---|---|
| `-probe` | 1101 | 1 | `init` | R1: the untuned unit + seed 1101 at 1e-4 (cap 7.0 h) |
| `-rung2` | 1101 | 2 | `init --reuse-baseline UNIT` | R3: seed 1101 at 5e-5, fine-tune only |
| `-rung3` | 1101 | 3 | `init --reuse-baseline UNIT` | R4: seed 1101 at 2e-5, fine-tune only |
| `-seed1102`, `-seed1103` (`-rung<r>-seed<s>` at rung 2 or 3) | 1102 / 1103 | the chosen rung | `init --reuse-baseline UNIT` | R5 (and P0's TOO CLOSE seed 1102) |

`UNIT` is the probe pod's sealed `1101-a0-init-a1`. Every other combination is refused with a fixed message.
The reuse ladder keeps only the memory candidate whose evaluation config equals the baseline's (the kit's rule).

## Runbook (one working copy per pod; every command prints hashes or a fixed message)

Preconditions: track A's `scripts/cuda_preflight_olmo3.py` and `scripts/tests/`, track B's
`experiments/safety_selection/configs/study-kt-data-dolly-olmo3.json` and `tmp/kt-prepared/prepared-kt-dolly-olmo3/`,
the nine recipes and this kit are committed by explicit path (KD8/T3; the pack refuses any untracked file under
`experiments/` or `scripts/`); the engine's `test_ss_family_codec.py` knows the `study-kt-olmo3-` prefix (fix round 1, D3).

```
# 0. once: the prepared set (track B) and the lead's pins
cp -R runkit/family-probe-olmo3 tmp/family-probe-s78-olmo3-7b-probe && cd tmp/family-probe-s78-olmo3-7b-probe
# set PROBE = "olmo3-7b", PREPARED_MANIFESTS["prepared-kt-dolly-olmo3"] = <manifest.sha256>, SEED, RUNG in probe_constants.py
# 1. pack (no network; refuses an uncommitted file under experiments/ or scripts/, a wrong lock hash, a missing preflight)
python3.11 -B pack_setup.py --dry-run          # the checks and the file list, nothing written
python3.11 -B pack_setup.py                    # prints probe, git_commit, engine_sha256, lock_sha256, bundle and setup hashes
python3.11 -B plan_tool.py init                # or: init --reuse-baseline <path to 1101-a0-init-a1>
python3.11 -B budget.py check 7.0 1.85         # the guard: $6 + 7.0 h x $1.85 = $18.95 must stay free (exit 0 or 3)
# 2. launch as a background job (never foreground; one finisher per kit)
nohup python3.11 -B launch.py olmo3-7b-1101 > launch.log 2>&1 &
nohup caffeinate -i python3.11 -B finisher.py > finisher.log 2>&1 &
python3.11 -B status.py                        # local records only
# 3. hosts/olmo3-7b-1101/finished.json: verified-and-stopped means the light check passed AND the finisher pulled and
#    checked the e1 states before the stop ("states": {"e1": {"pulled": true, "verified": true, "file": "states-e1-<stamp>.tar", ...}};
#    the check record retrieved/olmo3-7b-1101/states-e1-check-<stamp>.json says "states verified: 1 units": the e1 unit;
#    the untuned unit saved states/init/ only and is "not saved")
python3.11 -B states_tool.py check olmo3-7b-1101 e1    # optional: re-check the pulled tar against each unit's COMPLETE.json
# if "states".e1.verified is false (review-needed-stopped): the states are still on the pod's volume. The user starts the
# stopped pod (the console, or a zero-GPU resume on the user's yes, as stage 1 did on 30 Oct; the kit has no start command), then
python3.11 -B host.py get olmo3-7b-1101 && python3.11 -B host.py pull-states olmo3-7b-1101 e1 \
    && python3.11 -B states_tool.py check olmo3-7b-1101 e1; python3.11 -B host.py stop olmo3-7b-1101
python3.11 -B control_token_count_olmo3.py --unit retrieved/olmo3-7b-1101/tree/round1/1101-a0-init-a1 \
    --unit retrieved/olmo3-7b-1101/tree/round1/1101-a0-e1-a1 --out control-tokens-1101.json
# the reading: scripts/family_probe_reading.py without --family (O3A §16.1); the 3-seed read with
# gate_a/gate_a_common_olmo3.py --plan olmo3-B|olmo3-B5e5|olmo3-B2e5 once the lead has recorded its pins
```

The state rule (`states_tool.py rule`): the finisher pulls light, pulls and checks the e1 states while the pod still
has its SSH address, then stops; a failed pull or check is repeated by hand once the user has started the pod; the
pulled `states-e1-*.tar` (never removed by the finisher) goes into the next verified backup; a stopped pod is deleted
only after that backup is verified and the user says yes to that pod by name. The kit has no delete and no start command.
