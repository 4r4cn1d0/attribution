# The 7-8B kit, part T2: the cap rule and its measured basis (`runkit/stage1-78b/`)

Built 5 Nov 2026 as track A of the $0 build round for the 7-8B tier (the lead's Part 1 rulings, ruling 11; the
readiness plan's T2; the check's C7, C8, C11, C14, M3), fixed the same day after the adversarial verifier's report
(A-V1..A-V6), the lead's addendum (A1: recipe S_78 after the anchor job; A5: the constants convention) and the T4
interface note (the job runner's two preflight documents). The rule is KCR's M-cap
(`research/review/2026-10-17-icml-78b-prep/78b-kit-cap-rule.md` §4, §7, §10) for OLMo-2-7B and Llama-3.1-8B.

This file is named `RULES-78B.md`, not `README.md`: T4 copies the stage-1 kit (`runkit/stage1-olmo/`) into this
folder, and that copy brings the stage-1 kit's own `README.md` with it. Nothing here has a name the stage-1 kit
already uses. Nothing here is a run, a spend or a change to any other file. Stdlib only.

Tags: M measured (the basis), R read (path:line), E estimate (basis stated), I inference.

## Files

| File | What it is |
|---|---|
| `rules_78b.py` | The one constants block and the rule: `upper_m_s`, `requirement_s`, `speed_factor` (s_pod), `sanity_floor_s` (F_pre), `s_obs_from_progress` (KD11), `cap_hours`, `pod_sizes`, `guard_usd`, `launch_allowed`, `pod_spend_usd`, `funding_need_usd`, the key check (`check_keys`), the recipe-S_78 pins (`RECIPE_S`, `recipe_s_or_refuse`), the kinds rule (`check_kind`, `E_KINDS`, `e_upper_s`, `e_cap_hours`; PP8: `a1_pass` and `rep_pass`), the sealed-set readers for both committed MANIFEST forms (`sealed_edit_entry`, `block0_r_edits`; D1), KD5's idle storage (`idle_storage`; D2), the job runner's gate (`preflight_fields`, `job_decision`, `pod_dry_run`), block 0's money (`block0_report`). Commands: `golden`, `block0`, `e-caps`, `kit`. |
| `measured-basis-78b.json` | The text-free timing record of the 17 measured units (nine OLMo-2-7B, eight Llama-3.1-8B; KCR:9): per unit the outer job, pod overhead, preflight speed fields, ledger stage seconds, every generation batch's seconds / rows / capped count, memory peaks, hashes; per family the maxima the constants equal; at the top the evaluation bank the units ran (cap 2,048 tokens, 468 greedy prompts, 600 harm samples, batch 32, 34 batches). SHA-256 pinned in `rules_78b.py` (`BASIS_SHA256`). |
| `derive_78b_basis.py` | Writes the basis from the kits under `--root` (read-only, absolute path). Opens only nine file names, each in its one place: `hosts/<host>/{verification.json, finished.json, create-intent.json, create-result.json}`, `retrieved/<host>/tree/{BOOTSTRAP-READY.json, PREFLIGHT-DONE.json, JOB-DONE.json}`, `retrieved/<host>/tree/round1/<unit>/{ledger.jsonl, progress.jsonl}`; refuses every other name (no `create-*` wildcard), an allowed name in any other folder, and any path with `eval`, `generations`, `samples`, `prompts`, `ssh`, `hidden`, `selector.jsonl`, `states`, `judges`, `seals`, `units` in it (A-V6). Output: numbers, hashes, names, UTC stamps; no string longer than a hash. Deterministic (no clock inside), so the hash can be pinned. `--extra-unit FAMILY:KIT_FOLDER` adds units (KD9). |
| `tests/test_rules_78b.py` | KCR §10 tests 1-15 with the brief's adaptations; the fix round's tests 05c, 05d, 07b, 10b, 12b and the A-V6 cases of test 15; K1's 07c, 08b, 08c; fix-K-core's 17, 17b (PP8), 18, 18b (D1: both MANIFEST forms; the committed sets by pin), 19 (D2); K4a's 20 (PP16: `X_ONLY_KINDS`), 21 (DK-3: the kit's stage1_rules kind sets), 22 (PP14: the idle-storage pods and lines); a last no-bytecode check. 36 tests. |
| `tests/mutation_spec_rules_78b.json` | KCR test 13 and KCR:226's mutants plus the fix round's (A-V1..A-V6, the RECIPE_S refusal, the job_decision missing-field refusal), K1's 13, fix-K-core's 16 (ids `FK-m-*`: D1, D2, PP7, PP8) and K4a's 23 (ids `K4-m-*`: PP16, DK-3, PP14): 103, in the stage-1 kit's spec form. |
| `tests/conftest.py` | PP10, two layers. K4a's process-wide layer (DK-1), installed at import and never removed: an audit hook that refuses, at collection, in every fixture scope and in C-level calls, a subprocess whose executable is not one `local_processes` allowed for the running test (exact path), `os.system`, `os.exec*`, `os.posix_spawn*`, `os.spawn*`, `os.fork*`, a socket connect / sendto / sendmsg to a non-loopback address, a non-loopback name lookup (getaddrinfo, gethostbyname*, gethostbyaddr, getnameinfo), every urllib open and http.client's connect to a non-loopback host; multiprocessing's spawn (`_posixsubprocess.fork_exec`, no audit event) and a host name given to `socket.socket`'s connect / sendto / sendmsg (resolved before the event) are refused beside it. The per-test autouse fixture (PP10's first form) refuses the same calls at the Python level with a message naming each, checks Popen's `executable=` and replaces getnameinfo. Not covered: ctypes or another C extension; a direct call of subprocess's private `_fork_exec`; a host name given to a bare `_socket.socket`. `tests/test_pp10_guard.py` proves the fixture on the K3 incident's path (host.gated_download's default runner); `tests/test_pp10_process_wide.py` proves the process-wide layer (fail-closed probes: events raised by hand, missing program paths, numeric or loopback addresses). |
| `tests/run_mutants_78b.py` | The mutation runner (the stage-1 kit's `run_mutants_b15.py` form: baseline first, killed only by a real failure, errors invalid). |

## The rule (KD1; KCR §4)

For an arm of `steps` optimizer steps (removal 33, add 38, a0 38), per family:

    GEN_ALLCAP  = max(FIRST_BATCH_MAX, BATCH_MAX) + 33 x BATCH_MAX            # all 34 generation batches at the cap
    upper_M     = steps x TRAIN_STEP_MAX x train_scale + GEN_ALLCAP + SCORE_ALLCAP (1,250 s, E) + EARLY_MAX + OUTSIDE_MAX
    requirement = max( max(s_pod, s_obs) x upper_M + 1,800 , F_pre )
    cap         = round up to 0.25 h of max_k [ 48 min + sum_{j<k} 1.15 x ARM_JOB_MAX + requirement_k(s = 1) ]
    guard       = $6 + hold ($0) + cap x $1.85;  spend upper = (48 min + n x 1.15 x ARM_JOB_MAX) x $1.79

`evalonly` is upper_M without the training term. s_pod = max(1, pre.training_s / PRE_TRAINING_S_MAX,
pre.ms_per_step_full / PRE_MS_PER_STEP_MAX) only raises the requirement; s_pod > 1.15 refuses the pod before any job
(KD3). F_pre = pre.training_s x steps/38 + pre.untuned_projected_s + 1,000 + 900 + 1,800 never lowers it. s_obs (KD11)
= the finished arm's slowest capped 32-row batch after the first / BATCH_MAX, at least 1; later arms use max(s_pod,
s_obs) and defer at s_obs > 1.15. `train_scale` = max(1, the arm's padded tokens per step / the a0's) from token counts
(KCR:104).

## The constants convention (the lead's addendum A5; a KCR erratum)

**The basis file governs.** The rule's constants are the exact maxima of `measured-basis-78b.json` (M; test 2 holds
each constant equal to the maximum recomputed from the unit records). KCR §4 printed the same maxima rounded, and its
printed requirements (12,243 / 12,365 s OLMo-2-7B at 33 / 38 steps; 12,499 / 12,613 s Llama-3.1-8B) round each
constant before summing; the rule gives 12,244.15 / 12,365.42 s and 12,498.05 / 12,612.47 s, at most 1.2 s apart.
Caps, guards and spends are identical to the cent (M: test 1 holds both arithmetics: `KCR_PRINTED` through the same
functions reproduces KCR's integers exactly; the live rule's caps, guards and spends equal KCR §7-§8). The exact
maxima are kept so that no constant sits below a measurement and s_pod = s_obs = 1 exactly on every measured pod and
unit (tests 2, 4, 5). A constant changes only when the basis changes (KD9), by a recorded lead step that re-pins
`BASIS_SHA256`.

**Constants (M).** OLMo-2-7B: TRAIN_STEP_MAX 24.2545 s, FIRST_BATCH_MAX 314.049 s, BATCH_MAX 240.945 s, EARLY_MAX
19.877 s, OUTSIDE_MAX 108.638 s, ARM_JOB_MAX 6,450 s, preflight divisors 1,202.05 s / 269.03 ms. Llama-3.1-8B:
22.8848 s, 246.86 s, 250.305 s, 19.703 s, 162.778 s, 8,466 s, 1,261.79 s / 104.32 ms. KCR §4 printed 24.26, 314.0,
240.9, 20, 109; 22.89, 246.9, 250.3, 20, 163.

**Golden numbers (test 1 = KCR §4, §7, §8, :177).** Caps for 1-4 arms: OLMo 4.25 / 6.5 / 8.5 / 10.5 h; Llama 4.5 /
7.25 / 9.75 / 12.5 h (7.0 h for two 33-step Llama arms). Guards: $13.86 / 18.03 / 21.73 / 25.43; $14.33 / 19.41 / 24.04 /
29.13. Spend uppers: 1 arm $5.12 / $6.27; 4 arms $16.18 / $20.80 ($4.05 / $5.20 per arm). Block 0 (N: OLMo 3 arms at
8.5 h, Llama 4 jobs at 12.5 h, one launch): guard $44.85, spend upper $33.30, need $56.06 with the contingency.

## The rulings this folder bakes in (ruling 11; the addendum)

- **KD1** the M-cap rule above. **KD2** `MAX_ARMS_PER_POD_78B = 4` on both families (caps 10.5 h / 12.5 h); the
  basis is the lead's ruling under the delegation (C11), not a user confirmation; `pod_sizes` splits as the stage-1 kit
  does (8 -> 4 + 4, 6 -> 3 + 3, 5 -> 3 + 2). **KD3** 1.15 on the measured job (`MEASURED_MARGIN`), SCORE_ALLCAP 1,250 s,
  48 min pod overhead, refusal at s_pod > 1.15 and deferral at s_obs > 1.15.
- **KD4** `GATE_B_HOLD_USD = 0`; `GATE_B_HOLD_REASON` = "Gate B closed 23 Oct (FOCUS 'GATE B CLOSED', recorded
  2026-10-23T05:26 UTC); its last judge pods deleted 31 Oct". The guard still carries the hold term, so a non-zero hold
  would bind (test 10).
- **KD5** `VOLUME_GB = 50`, `FREE_SPACE_MIN_GB = 8.0` (E: one arm's three states, about 5.8 GB, x 1.15 plus records);
  `job_decision` refuses a job below it or on an unreadable reading. The state rule (pull, verified backup, the
  user's yes by pod name, no delete command) is T4's `states_tool.py` port; the idle-storage line (D2) is
  `rules_78b.idle_storage` in `block0_report` and the last line of `stage1_rules.block0_need_report` (printed by
  `init-block 0`, kept in its summary JSON and plan.json): about $0.33 per day per stopped 50 GB pod that keeps its
  states ($0.20 per GB per month, KCR:161; E), N's 2 pods $0.67 per day, about $20 per month; counted in no guard.
  PP14 (K4a): then one line per other block-0 pod that keeps states after its jobs (`idle_storage_pods`,
  `idle_storage_lines`): each family's retrain pod (the a0-1101 retrain's q and e1 states for A1's pass) and each
  family's a1_pass scorer pod (`IDLE_SCORER_KINDS`: it holds those states; I, the lead names any other), $0.33 per
  day each, and the block's total (`idle_storage_all`: 6 pods, $2.00 per day, about $60 per month); the summary JSON
  holds `idle_storage_pods` and `idle_storage_all`.
- **KD6** every kind but `arm`, `a0_arm`, `evalonly` runs alone on a single-job pod with an explicit E cap (`e-caps`
  below) until its first 7-8B run measures it. **KD7** `WORKING_COPY_PREFIX = "family-probe-s78-"`; the stage-1 kit's
  `budget.py` `KITS_GLOB` (`family-probe-*`, `gate-b-olmo*`, `stage1-olmo*`) is unchanged and matches it, and both kits
  lock `tmp/family-probe-budget.lock` (test 11 exercises the stage-1 `budget.py` unchanged inside such a copy).
- **KD8 and addendum A1 (recipe S_78).** No config is added here. `RECIPE_ALLOW` holds each family's main config and
  recipe G by `config_sha256` (`18cc31d7…` / `01259f28…`; `74758af1…` / `442f133f…`): the measured kinds and the
  other E kinds run under these. `RECIPE_S = {"olmo2-7b": None, "llama31-8b": None}` pins each family's S_78 and is
  null until the family's anchor job has written `anchors.sealed.json`, `scripts/scale78b/make_recipe_s78.py` has
  written the config and the lead has committed it (KD8); the lead then fills the pin with that config's
  `config_sha256` (the engine's canonical hash) by a recorded step and the suite's test 7b is re-read against it.
  Until then `recipe_s_or_refuse(family)` raises `Refused`, and the kinds that need S_78 (`S78_KINDS`, the lead's
  PP3 / PP4 / PP8 = `retrain`, the a0-1101 retrain of ruling 10 / A2; `rep_pass`, REQ-3's representation pass
  (`scripts/stage1/representation_pass.py`); `a1_pass`, A1's attributes pass on the retrain's q and e1 states;
  `classifier`, under S_78 as at 1B) refuse through it at the runner's gate (`job_decision`) and at the pod's key
  check (`check_keys`). Planning never refuses on it: `job_record`, `e_pod`, `cap_hours` and `block0_report` print the
  retrain, rep_pass, a1_pass and classifier pods' money before S_78 exists (the check's M3).
- **KD9** the basis is re-measured on the first engine-Y pod before Y carries a block: `derive_78b_basis.py --root ROOT
  --out NEW.json --extra-unit FAMILY:/abs/path/to/tmp/family-probe-s78-<family>-<block>` (the unit's records must have
  the measured layout), then the lead records the step, copies NEW.json over `measured-basis-78b.json`, sets
  `BASIS_SHA256` and the constants that moved, adds engine Y's identity to `ENGINES`, and re-runs the suite.
- **KD10** route (ii): T4 copies the stage-1 kit here and imports this module for the per-family constants.
  **KD11** `s_obs_from_progress` reads a finished arm's `progress.jsonl` (batch seconds and capped counts only); a
  drifted record (a generate row without an integer `capped` or `rows`; no 32-row batch at all) refuses the next arm
  (A-V1), and only capped 32-row batches after the first count (A-V2).

## KD6: the E caps (single-job pods; `rules_78b.py e-caps`)

| Kind | OLMo cap / guard | Llama cap / guard | Basis (E unless marked) |
|---|---|---|---|
| `untuned_answers` (two calls, PP2; K4b) | 6.0 h / $17.10 | 6.0 h / $17.10 | the S3 call's 27 chunks (861 prompts at 512 tokens) and the S4 call's 16 chunks, each chunk at the capped-batch maximum measured at 2,048 tokens (M; an upper bound for the 512-token chunks), each call with its first batch and early/outside time (M), x 1.5 (was 3.0 h / 3.25 h for the S4 call alone) |
| `o_only` | 3.75 h / $12.94 | 3.75 h / $12.94 | 19 capped batches (M) + half the scoring allowance, x 1.5 |
| `o_only_with_regenerate` (PP17; no standalone `regenerate` kind) | 4.5 h / $14.33 | 4.5 h / $14.33 | the regeneration (38 x TRAIN_STEP_MAX (M) + three state writes, x 1.5; the engine's verify and the acceptance check inside that 1.5) + the o_only upper, on one pod |
| `anchor` | 2.25 h / $10.16 | 2.25 h / $10.16 | the 1B 0.25 h upper x 2.3 (RP:43) x 1.5 |
| `rep_pass` (REQ-3's representation pass; needs S_78; PP8) | 4.75 h / $14.79 | 4.75 h / $14.79 | the stage-1 kit's 1 h estimate at 1B (DIAG_ESTIMATE_S 3,600 s) x 2.3 (RP:43) x 1.5, until measured |
| `a1_pass` (A1's attributes pass; needs S_78; PP8) | 16.5 h / $36.53 | 16.5 h / $36.53 | KD6: 16.5 h at most (RP:43's 6-11 h x 1.5) |
| `l1_scan` | 4.75 h / $14.79 | 4.75 h / $14.79 | the 1B 3,600 s x 2.3 x 1.5 |
| `classifier` | 3.25 h / $12.01 | 3.25 h / $12.01 | the 1B 2,012 s x 2.3 x 1.5 |
| `c0` | 4.25 h / $13.86 | 4.5 h / $14.33 | the evalonly bound (M) + 1.5 x 600 s for the X-pin check |
| `retrain` (engine Y; needs S_78) | 4.5 h / $14.33 | 4.5 h / $14.33 | a 3 h upper, about 6 x the expected; the check's M3 names 4-5 h |
| `ref_train_bqi` (B+Qi, Y) | 6.5 h / $18.03 | 6.5 h / $18.03 | training x 1.5 (reference forward) x 2 (engine Y) + the evalonly bound (M) + the O-ext term (R1 K1; GXB O12; was 4.75 h / 5.0 h) |
| `safe_lora` (1 point) | 7.25 h / $19.41 | 7.25 h / $19.41 | regenerate + hash (1B 600 s x 2.3) + transform, x 1.5; + evalonly (M) and the O-ext term per point (R1 K1; was 5.5 h / 5.75 h) |
| `ref_eval` (1 point) | 6.75 h / $18.49 | 6.75 h / $18.49 | regenerate + 300 s scaling, x 1.5; + evalonly (M) and the O-ext term per point (R1 K1; was 5.0 h / 5.25 h) |
| `w1_18` (R1 K1; one pod, both families) | 2.25 h / $10.16 | 2.25 h / $10.16 | the 1B W1-18 upper 0.5 h (E there) x 1.5; guard-only, no size factor (I) |

`block0` prints N's two pods, each family's retrain pod and each scorer pod separately with its guard, spend upper and
need alone (the check's M3): retrain $14.33 guard / $6.80 spend / $17.91 need; the a1_pass pod $36.53 / $28.64 / $45.66;
the rep_pass pod $14.79 / $7.61 / $18.49; the other scorer pods $10.16-14.79 guard each; then KD5's idle-storage block
(D2: `idle_storage`, $0.33 per stopped 50 GB pod per day; N's 2 pods $0.67 per day, $20 per month), PP14's
`idle_storage_pods` (N's 2, the 2 retrain pods, the 2 a1_pass pods) and `idle_storage_all` ($2.00 per day).

## The sealed edit sets (ruling 14; PP7; the core verifier's D1)

`SEALED_SETS` pins each family's MANIFEST by SHA-256: OLMo-2-7B's is Gate B's set (`d76d8bf9…`), Llama-3.1-8B's the
set committed at d422fca (`2a1db220…`, filled by the lead's recorded step PP7). The two committed MANIFESTs have two
forms, and `sealed_edit_entry` / `block0_r_edits` read both: Gate B's marks every edit with `role == "edit"` and its
M-family edits carry draws 1-2 of their own, so an R edit is R_d by `family == "R"` AND `draw == d`, never by draw
alone; the Llama set's `role` is a descriptive string (never `"edit"`), each R entry carries `seed` = 1100 + d, and
a top-level `roles` map names each draw's block. Both put every edit under `edits/` with a `family`, an `arm` and a
64-hex `sha256`. `block0_r_edits(manifest)` returns draw -> {draw, seed, arm, path, sha256} for N's draws and refuses a
wrong seed, a draw listed twice or a missing draw; `plan_tool.edit_sources`, `plan_tool.man_arms` and
`pack_setup.sealed_set` read through it. Test 18b reads both committed files by pin and binds R_d1-R_d3 to
`f7d7eb86… / 913b7360… / cd8d3328…` (OLMo) and `5cdedf22… / 8f9f3cd5… / edbc111b…` (Llama) at seeds 1101-1103.

## The public functions the T4 kit calls (exact signatures and refusals)

Every refusal is `rules_78b.Refused` (a `ValueError`); the caller records the case and nothing runs. Nothing below
reads the clock, the network, a config file or a pod; the only file read is the pinned basis (`load_basis`).

**Before the pod (the plan and the launch).**

- `check_keys(family: str, kind: str, recipe_sha256: str, engine_sha256: str, gpu_name: str, manifest_sha256: str,
  bank: dict) -> None`. Refuses: an unknown family; an unknown kind (`check_kind`); for a kind in `S78_KINDS` a recipe
  other than `recipe_s_or_refuse(family)` (so a null pin refuses); for any other kind a recipe not on
  `RECIPE_ALLOW[family]` (the main config and recipe G; never S_78); an engine not in `ENGINES` (X only until KD9);
  a GPU name other than `"NVIDIA A100-SXM4-80GB"`; a manifest other than `MANIFESTS[family]`; a `bank` that is not
  exactly `BANK` = `{"cap_tokens": 2048, "greedy_prompts": 468, "harm_samples": 600, "generation_batch": 32}` (ints;
  no missing or extra key) (A-V3; KCR:147). T4 builds `bank` from the recipe config (`generation.max_new_tokens`,
  `generation.batch_size`) and the evaluation bank it packs (the family-probe bank's 468 greedy prompts and 600
  sampled harm answers); after the preflight the pod's `verification.json` repeats them
  (`full_length.max_new_tokens`, `full_length.batch`, `evaluation_timing.projection_to_dev_bank.stages.generate.bank_units`,
  `….sample.bank_units`; R: the measured files' key trees).
- `recipe_s_or_refuse(family: str) -> str`. The family's S_78 `config_sha256`. Refuses while `RECIPE_S[family]` is
  None (addendum A1) or not a 64-hex string; an unknown family refuses.
- `price_allowed(price) -> bool`: a finite price at or below `MAX_PRICE_USD` ($10/h); never raises.
- `launch_allowed(free_after_commitments_usd: float, cap_h: float, price: float = PLANNING_PRICE_USD) -> bool`: the
  guard, decided in cents: free − cap × price ≥ $6 + the hold ($0). Refuses (raises) a balance, cap or price that is
  not a finite number (A-V4).
- `guard_usd(cap_h: float) -> float` = $6 + hold + cap × $1.85. `cents(usd) -> float`, half-up.
- `job_record(family: str, kind: str, steps: int | None = None, arm: str | None = None, seed: int | None = None,
  padded_tokens_per_step: float | None = None, n_points: int = 1) -> dict`: one plan job (`upper_s`,
  `start_requirement_s`, `measured_upper_s`, `spend_upper_s`, `counted`, `unmeasured`). Refuses an unknown kind, an
  arm without its step count, `n_points < 1`. Never refuses on `RECIPE_S` (planning).
- `arm_pod(family: str, steps_list: list[int], kinds: list[str] | None = None) -> list[dict]`.
- `cap_hours(jobs: list[dict]) -> float`: the pod's cap (KCR §4). Refuses no jobs, more than 4 counted jobs (KD2), an
  E kind not alone (KD6), two families on one pod.
- `e_upper_s(family, kind, n_points=1) -> dict` (`upper_s`, `basis`), `e_cap_hours(family, kind, n_points=1) -> float`,
  `e_pod(family, kind, n_points=1) -> dict` (`cap_hours`, `guard_usd`, `spend_usd`, `upper_s`, `e_cap`). Refuse a kind
  not in `E_KINDS`.
- `pod_spend_usd(jobs) -> float`; `funding_need_usd(launches: list[list[dict]], factor: float = 1.0) -> dict`
  (`base_need_usd`, `need_usd`, `contingency_usd`, `terms_usd`; the stage-1 kit's rule unchanged); `pod_sizes(n) -> list[int]`;
  `block0_report() -> dict` (N's pods, the retrain pods, the scorer pods, each with guard / spend / need; `idle_storage`,
  KD5's block for N's pods kept stopped); `idle_storage(n_pods: int, volume_gb: int = VOLUME_GB) -> dict`
  (`usd_per_pod_day` 0.33, `usd_per_day`, `usd_per_month`, `basis`; refuses a non-integer or negative count);
  `sealed_edit_entry(entry) -> bool` and `block0_r_edits(manifest: dict, draws=BLOCK0_R_DRAWS) -> dict[int, dict]`
  (the sealed-set readers for both committed MANIFEST forms; refuse a wrong seed, a duplicate or a missing draw).
- `requirement_s(family, steps, kind="arm", s_pod=1.0, s_obs=1.0, preflight=None, padded_tokens_per_step=None) -> float`;
  `upper_m_s(family, steps, kind="arm", padded_tokens_per_step=None) -> float`; `measured_upper_s(family, kind="arm") -> float`;
  `evalonly_upper_s(family) -> float`; `steps_of(dose) -> int`. Refuse an unknown family, kind or dose, an E kind
  (use `e_upper_s`), a non-finite factor.
- `load_basis(path=None) -> dict`: refuses when the file's SHA-256 is not `BASIS_SHA256`.
- K1 (the kit's per-family constants block; plan T4 step 1; addendum A13): `KIT[family]` (`probe_key`, `rec` = the
  family's MAIN config (path, config_sha256), `prepared_name`, `manifest_sha256`, `training_identity`, `fixture`
  (the a0-1101 side unit's preflight verification.json by SHA-256), `a0_units` (P78 §2.1's seven side units by
  COMPLETE.json SHA-256), `instruct_model`, `base_model` (revision None until pinned), `volume_gb` 50,
  `max_arms_per_pod` 4, `block0` {host, runs, cap_hours}); `kit_of(family) -> dict`. The null-until-filled pins:
  `ENGINE_Y` (None), `Y_MEASURED` (False), `RECIPE_G`, `RECIPE_BQI` (None per family), `SEALED_SETS` (OLMo-2-7B's
  Gate B MANIFEST `d76d8bf9…`; Llama-3.1-8B's `.ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json`, sha256
  None). `pin_or_refuse(pin, family) -> str` (PINS: RECIPE_S, RECIPE_G, RECIPE_BQI; refuses a null or malformed pin,
  an unknown pin or family); `recipe_bqi_or_refuse(family)`; `engine_allowed(kind, engine_sha256) -> bool` (X always;
  Y: E_KINDS once `ENGINE_Y` is filled, measured kinds once `Y_MEASURED` is True; never raises);
  `sealed_set_or_refuse(family) -> {path, sha256}` (refuses a null pin); `block0_runs(family) -> [(arm, seed)]`
  (R_1-R_3 at 1101-1103; a0 at 1103 on Llama only; `R_SEED_BASE` 1100, `BLOCK0_R_DRAWS` (1, 2, 3), `A0_SEED_1103`);
  `block0_jobs(family) -> [job]` (cap 8.5 h / 12.5 h). `check_keys` now refuses `ref_train_bqi` under any recipe but
  `RECIPE_BQI` and takes its engine clause from `engine_allowed`; `job_record` refuses `n_points` that is not a
  positive integer for every kind (D2). `rules_78b.py kit` prints the block and the pins.

**On the pod (the job runner), before each job.**

- `preflight_fields(preflight_done: dict, verification: dict) -> dict`: `training_s` and `ms_per_step_full` from
  `PREFLIGHT-DONE.json`; `untuned_projected_s` from `verification.json`'s `cap_projection` block (M: none of the 17
  measured `PREFLIGHT-DONE.json` files holds it; there is no fallback to a field of that name there). Refuses: either
  document not a dict; no `cap_projection` dict; any of the three fields missing or not finite;
  `cap_projection.training_s` not equal to `PREFLIGHT-DONE` `training_s` (the two documents must be one preflight's).
- `speed_factor(family: str, preflight: dict) -> float` = s_pod on the fields above; refuses a missing or non-positive
  field and s_pod > 1.15 (the pod is refused before any job).
- `job_decision(family: str, preflight_done: dict, verification: dict, job: dict, remaining_s: float | None, free_gb,
  s_obs: float = 1.0) -> dict` → `{"action": "run" | "defer", "reason": None | "remaining" | "s_obs",
  "requirement_s", "s_pod", "s_obs", "s", "remaining_s"}`. Refuses: everything `preflight_fields` and `speed_factor`
  refuse; `free_gb` below `FREE_SPACE_MIN_GB` (8.0) or not a finite number (KD5); a job whose kind is in `S78_KINDS`
  while `RECIPE_S[family]` is None (addendum A1). `remaining_s` None defers (Gate B's "none never fits").
- `pod_dry_run(family: str, preflight_done: dict, verification: dict, jobs: list[dict], remaining_s: float, free_gb,
  s_obs: float = 1.0) -> list[dict]`: `job_decision` per job, the remaining time falling by each run job's measured
  upper; the first deferral defers every later job. Same refusals.
- `free_space_ok(free_gb) -> bool`: the free-space check (KD5); a missing or non-finite reading is not ok; never raises.

**After each arm.**

- `s_obs_from_progress(family: str, progress_rows: list) -> float`: the finished arm's slowest capped 32-row
  generation batch after the first, over BATCH_MAX, at least 1 (KD11; KCR:113). Refuses: no rows; fewer than two
  `generate` rows; a `generate` row without an integer `capped` or `rows` (A-V1); no 32-row batch at all (A-V1); a
  non-finite `elapsed_s`. 32-row batches present but none capped → 1.0 (nothing slow was seen).
- `s_obs_defers(s_obs) -> bool`: `s_obs > 1.15` (KD11).

## Commands (Mac, CPU, no pod, no network; `-B` always; `-I` when a script reads data files)

    PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python   # or .venv's python
    ROOT=<the checkout that holds runkit/stage1-78b>

    # the basis (reads the 17 kits read-only; prints the hash and the clock; the file is deterministic)
    $PY -I -B $ROOT/runkit/stage1-78b/derive_78b_basis.py --root /Users/spiderishi/Coding/attribution/tmp --out $ROOT/runkit/stage1-78b/measured-basis-78b.json

    # the rule's tables
    $PY -I -B $ROOT/runkit/stage1-78b/rules_78b.py golden
    $PY -I -B $ROOT/runkit/stage1-78b/rules_78b.py block0
    $PY -I -B $ROOT/runkit/stage1-78b/rules_78b.py e-caps
    $PY -I -B $ROOT/runkit/stage1-78b/rules_78b.py kit        # K1: the per-family constants block and the null pins

    # the suite (tests 02b, 05b and 15b read the 17 kits and skip when they are absent)
    cd $ROOT && PYTHONDONTWRITEBYTECODE=1 $PY -B -m pytest -p no:cacheprovider -q -rfE runkit/stage1-78b/tests/test_rules_78b.py

    # the mutation run (the lead's background shell; baseline first; SCRATCH must be a new folder outside ROOT)
    $PY -B $ROOT/runkit/stage1-78b/tests/run_mutants_78b.py $ROOT SCRATCH OUT.json BASELINE
    $PY -B $ROOT/runkit/stage1-78b/tests/run_mutants_78b.py $ROOT SCRATCH2 OUT.json ALL

    # the lead's separate guard commands (not tests: they read the working tree's git state)
    cd $ROOT && git status --porcelain -- experiments scripts runkit/stage1-olmo          # must print nothing
    cd $ROOT && git diff --quiet HEAD -- runkit/stage1-olmo && echo stage1-kit-unchanged

## Limits

- No repair arm has run at 7-8B; the basis is 17 a0 units on three recipes per family (KCR §13). SCORE_ALLCAP, the 48
  min overhead, the volume and free-space thresholds and every E cap are estimates with their bases stated.
- The E caps for the scorer kinds scale 1B estimates by RP:43's job-time ratio; they are placeholders until each
  kind's first 7-8B run (KD6), after which the lead records the measured value.
- `RECIPE_S` is null for both families (addendum A1): the retrain, the representation pass, the A1 pass and the
  classifier (`S78_KINDS`; PP8) refuse until the anchor job, the maker and the lead's commit and pin. `ENGINES` holds X only. The first Y pod (the retrain, ruling 10) passes `check_keys`
  once the lead fills `ENGINE_Y` (addendum A13; K1): E-capped kinds then run on Y, measured kinds only after KD9's
  re-measure sets `Y_MEASURED` (`engine_allowed`).
- `ref_train_bqi` runs under `RECIPE_BQI` only (K1, the re-verifier's D1; A1's pattern): `check_keys` and
  `job_decision` refuse it while the pin is null and under any other recipe; `job_record` still prices it (M3).

## R1 K1 (8 Nov 2026): blocks A and B, the rules layer

Built from PLAN-AB §2 Track K row K1 with the lead's build rulings (GXB, `.ai/inputs/stage1-post-w1-20261023/78b/
lead-rulings-ab-build-20261108.md`, both sets). `rules_78b.py` holds the rules; `stage1_rules.py` exposes them to the
copied modules by the stage-1 names. The callers (init-block A / B, the branch and stop records, the runner's commands,
the pack) are K2's and K3's; until then `plan_tool.py` still carries the inherited 1B route for blocks A and B.

- **Block tables** (Part 2 §2.2): `block_runs_78b(family, plan, block, dose_seeds)`: block A 21 runs per family (every
  plan); block B 23 / 32 / 47 (plan A / B9 / H (b)) plus the dose rows (6 or 12); A1, L1 and S3 dropped on a family
  whose anchor job stopped (12; 14 / 26 / 38). `stage1_rules.BLOCKS = ("0", "sc", "A", "B")` with `HOST_PREFIX`,
  `FUNDING_BLOCK`, `BLOCK_KINDS`.
- **Edits by path and SHA-256 only** (Part 2 §2.3): `R_DRAW_SOURCES[F][d]` for R_d4-R_d13 (three OLMo sources; the
  Llama set); `METHOD_EDITS[F][arm]` with H1 and S1 filled, A1, L1, S3, S4, S4_96, S4_192, s4_top null; `run_edit`
  refuses a null pin with its event (`METHOD_EDIT_EVENTS`).
- **Steps (GXB O1)**: ceil(rows / 128) of the arm's training rows (`steps_for_rows`, `arm_training_rows`,
  `arm_steps`); a named arm whose derived steps differ from `ARM_STEPS` refuses; `STEPS["dose"] = 39`; s4_top
  ceil((4,800 + n) / 128). **Dose arms (GXB K-5)**: `dose_arms_for(n)` from the kept S4 count: n >= 192 S4_96 and
  S4_192; 97-191 S4_96 and s4_top (n); 96 S4_96 only; 49-95 s4_top (n) only; 48 none; fewer than 48 the build stop;
  s4_top exists only for 49-95 and 97-191; `block_runs_78b(..., dose_seeds, kept)` takes n, never a list of arms.
- **Pods** (Part 2 §2.4): `deal_ab` (arm-major, seed-minor, run i to pod i mod P; at most 4; an arm twice refuses);
  each job carries its own steps, train_scale input (`padded_tokens_per_step`, required for edit arms) and O-ext term;
  `requirements()` and `job_decision` now read the job's own padded tokens and term.
- **The O-ext cap term** (DESO item 24; Part 2 §4.3; GXB O12): `oext_term_s` = 1.5 x (13 PHTest batches at the cap +
  half the scoring allowance + early and outside), 5,938 s OLMo / 6,092 s Llama, until `OEXT_TERM_MEASURED_S[F]` is
  filled; `job_record(..., oext=True)` for arm, a0_arm and ref_train (4-arm caps 17.25 h / 19.25 h; four-pod need
  $167.06 / $185.56); the references' E caps carry it per point. Block 0 never carries it. `check_keys(...,
  oext_bank=)` holds the O-ext bank against `OEXT_78B[F]`.
- **W1-18 and the branch** (DES E2; DESO2 item 37; GXB O4, K-3): kind `w1_18` (E, X only, the scorer block's first
  O job, in OLMo-2-7B's scorer-block copy, one record per family, [C] OLMo only; `W1_18_78B` null), `BRANCHES`,
  `BANK500_KINDS`, `bank500_job`, `branch_record_problem`. The branch is read only from the family's pinned record
  `BRANCH_78B[F]` (null until W1-18's record-done; K1V-5): `branch_record_or_refuse`, `bank500_problem`,
  `branch_switch_problem`, `oext_flags`; c0, o_only and o_only_with_regenerate wait on it (GXB R-4).
- **N's units, keyed by (arm, seed)** (DES E5; the seed key): `sc_units`, `sc_unit_source`, `N_UNITS[F]` (null until
  block 0's record-done), `n_unit_or_refuse`; `stage1_rules.sc_unit_input_names/sc_unit_input_pins(kind, ..., arm,
  seed)` refuse a missing arm (K1V-9); the seed-only `sc_input_names/sc_input_pins` stay only at the runner's, the
  pack's and the planner's four call sites until K2/K3 move them (test_41 lists them).
- **Block A's re-judge list** (DESO item 26): `rejudged_pins` / `rejudged_or_refuse`, 7 per family, N's null until N runs;
  the side units carry their job.json SHA-256 (M, 8 Nov; GXB R-2). A malformed N_UNITS pin refuses at use, never at
  import (K1V-8).
- **The gate and block B's plan** (GXB O14 corrected, K-6, R-1): `GATE_78B` (option, families, N's provisional plan,
  the noise reading, the balance; block A's init reads its families and refuses under a "review" provisional plan)
  and `PLAN_B_78B` (plan, `sr2_adopted`; adopted: basis sigma_A and blinded_sigma.py's output and inputs hashes; not
  adopted: `sr2_reason` and basis sigma_pool_N under [B] or sigma_F under [C], the hashes null; "review" plans
  nothing): both null, `block_init_or_refuse`. GXB R-24: the plan must be the one its basis gives by P1 §6.1:
  sigma_A, the plan of the record's `sigma_A_pp` (`plan_for_sigma`, the seed rule); sigma_pool_N, GATE_78B's
  provisional plan; sigma_F (only [C]), GATE_78B's `sigma_F_plan` (required under [C], null under [B]).
- **The anchor stops** (GXB O6; item 14; the fourth set's form, the one Track S reads): kind `scale-78b anchor stop`,
  `stop_kind` `safe_anchors_below_64` (exit 3) or `harmful_prompt_does_not_encode` (exit 1 with the AnchorJobError
  message; any other end is a crash), JOB-DONE.json SHA-256, `counts`: `anchor_exit_kind`, `anchor_stop_record`,
  `anchor_stop_problem`. `ANCHOR_STOP[F]` (null = no stop) marks a family stopped only after `anchor_stop_or_refuse`
  read the record at the pin (K1V-6); on a stopped family `STOP_REFUSED_KINDS` refuse for good and the retrain runs
  under MAIN_F (`sc_recipe`, `check_keys`, `sc_needed_pins`, `sc_order_problem`, `job_decision`); `ENGINE_Y`'s event
  carries AM1's stopped-family clause.
- **ref_train** (Part 2 §3.2): a measured kind under `RECIPE_G` only. **The wrapper path**: `OEXT_UNIT_SCRIPT`,
  `C0_SCRIPT` and `W1_18_SCRIPT` are Track O's `scripts/scale78b/oext_78b.py` (`OEXT_WRAPPER_COMMANDS`: unit, lean,
  w1_18; the runner's command lines are K3's). `OEXT_78B[F]` (engine X) and `OEXT_78B_Y[F]` (engine Y; null; filled
  after ENGINE_Y and RECIPE_BQI) each pin the wrapper and exactly their own family's and engine's O-ext index, by
  Track O's names `scripts/scale78b/settings/OEXT-78B__<F>.json` (X) and `OEXT-78B-Y__<F>.json` (Y) (GXB R-5, R-22);
  the family's W1-18 record may be the one entry under `.ai/inputs/stage1-post-w1-20261023/78b/w1-18/` (R-21).
- **Block 0** keeps 3481d85's plan.json byte for byte: the job keys `oext` and `padded_tokens_per_step` are written on
  block A and B jobs only (GXB R-3; test_42).

### K2's and K3's acceptance items from R1 (GXB R-16, R-26)

- **KR4, the pod side of a stop.** Once `ANCHOR_STOP[F]` is pinned, every process that calls `family_stopped` (the
  pod's `check_keys` and `job_decision`, the planner, the pack) refuses until it has read the stop record through
  `anchor_stop_or_refuse(family, bytes, job_done_sha256)`. K2's planner and K3's runner and pack call it before a
  stopped family's MAIN_F retrain pod (and any other job of that family), and the pack carries the record (by path and
  SHA-256) into the pod's setup.
- **KR5.** One shared stop-record fixture read by K2's writer, RK's `anchor_stop_problem` and Track S's reader, with a
  cross-track test.
- **KR6 / K-1.** The planner's c0 / O-ext script check becomes a check of the command word, read from
  `OEXT_WRAPPER_COMMANDS`; the scorer mutant K4bf-m-c0-needs-oext-script moves there.
- **K-8.** The inherited 1B branch record goes; `BRANCH_78B[F]` is the only branch source, read by its bytes at its pin.
- The kept S4 count for `block_runs_78b(..., kept)` comes from the untuned pass's dose record, not a caller.
- **R-16.** The four seed-only `sc_input_names` / `sc_input_pins` call sites (runner :466, :483; pack :432; planner
  :1306) move to `sc_unit_input_names` / `sc_unit_input_pins`, and the seed-only form is deleted; test_41's list is
  empty by K3's end.
- **R-18.** K3 rewrites the runner's O-ext command lines (`oext_78b.py <command> --family F ...`) and the scorer test's
  assertions on them.

