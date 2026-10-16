# 7–8B kits: a measured cap rule (DESIGN PROPOSAL, reviewed)

**Status: DESIGN ONLY. It adopts nothing and changes no file.** Written 2026-10-16 at about 21:45 UTC (17 Oct IST; clock checked with `date -u`) by an Opus worker for the main-study lead (GI VI). **Adversarial review and in-place revision: 2026-10-16, about 21:48–22:20 UTC (clock checked with `date -u` at 21:48 and 22:04 UTC), by a second Opus worker.** Read-only work: no run, spend, pod, download, commit or agent. The only file is this one. The review's corrections are in the text; §14 lists them.

**Scope.** The kit design for the repair comparison at 7–8B: OLMo-2-7B at LR 1e-4 (`study-kt-olmo2-7b-r64-b-mb2-20261008`) and Llama-3.1-8B at LR 5e-5 (`study-kt-llama31-8b-r64-b5e5-mb2-20261010`). The user has not chosen option B or C of the re-plan. This design covers what B and C share. Option-specific parts are marked **[B]** or **[C]**.

**Labels.** **M** = measured (source follows). **R** = read (path:line or URL). **E** = estimate (basis follows). **I** = inference.

**Sources.** RP = `writing/paper/2026-10-17-icml-replan-PROPOSAL.md`. RULES = `runkit/gate-b-olmo/gateb_rules.py`. PRE = `scripts/cuda_preflight_family.py`. ENG = `experiments/safety_selection/engine.py` (read only). FPK = `runkit/family-probe/`. SIDE = the side-project kits `tmp/family-probe-sp-olmo2-7b-{b-a0,b-seed110{2,3},b5e5-seed110{1,2,3},g-seed110{1,2,3}}` and `tmp/family-probe-sp-llama31-8b-{b-a0,b-seed110{2,3},b5e5-1101,b5e5-seed1102,g-seed110{1,2,3}}`. From each I read timing fields only: `hosts/*/{finished,create-result,create-intent,cap-override,verification}.json` and `stops.jsonl`, and `retrieved/*/tree/{BOOTSTRAP-READY,PREFLIGHT-DONE,JOB-DONE}.json`, the process receipts, and `round1/*-e1-a1/{ledger,progress}.jsonl` (seconds, counts, memory, token counts). I opened no answer, prompt, sample, eval or ssh file. All 7–8B pods were `NVIDIA A100-SXM4-80GB` at $1.79/h (M, `create-result.json` `costPerHr`; `create-intent.json` `gpuTypeIds`). All 17 measured units ran on engine X (M, `BOOTSTRAP-READY.json` `engine_sha256` = `472fc7f6…` in all 17).

## 0. Summary

- **The term that over-projects** is the capped-generation term of the preflight: `ms_per_step_full / 1000 × 2,049 × batches` (R, PRE:168), with `batches` = 15 greedy + 19 sampled = 34. It is 91% of the 7B projection. The family-probe kits also count it **twice** (`2 * evaluation_upper`, PRE:174), for an untuned evaluation that a fine-tune-only job never runs. For OLMo-2-7B the term is also built on a slow per-step time: the full-length check runs at the memory edge (204 allocator retries) and measures 269 ms per step, but real capped batches run at about 116 ms per step (M).
- **Why measured capped batches are a valid basis (R, added by the review).** The engine keeps a finished row in its batch, fed padding, until every row stops (ENG:543-563). So a batch with one capped row costs as much compute as a batch with 32 capped rows, and the KV cache is the same size. The slowest measured capped batch therefore bounds an all-capped batch of the same prompts.
- **Llama is different.** Its preflight per-step time (70–104 ms) is *below* the real one (105–122 ms; M). Its projection is close to the real time only because few sampled batches reach the cap. So the preflight is not a safe upper bound for either family.
- **Proposed rule ("M-cap").** A job's start requirement comes from a *measured physical upper bound*: all 34 generation batches at the slowest measured capped-batch time, the slowest measured training step, an all-capped scoring allowance (1,250 s, E), the measured time outside the ledger stages, plus the Gate B 30-minute start margin. The earlier jobs in the cap sum use 1.15 × the slowest measured job. The preflight stays as a **sanity floor**: it can raise the requirement on a slow pod (speed factor ≥ 1, and a typical-case floor), never lower it, and it refuses a pod slower than 1.15× every measured pod. **New (review):** after each arm, the job runner compares that arm's own batch times with the basis and raises or stops the later arms (§4, "in-pod speed check").
- **Numbers (M-based, E where marked; corrected by the review).** Per-arm start requirement: OLMo **3.43 h** (the Gate B rule fed with the 7B preflight gives 6.63 h); Llama **3.50 h** (Gate B rule 3.44 h). 4-arm caps: **OLMo 10.5 h, Llama 12.5 h** (Gate B rule: 13.75 h and 12.5 h). Guard per 4-arm pod: $25.43 and $29.13. The corrections changed only the 2-arm caps (§7).
- **Cost per arm at $1.79/h, 4 arms per pod (E: measured medians and maxima):** OLMo $2.94 expected, $3.52 at the measured maxima; Llama $3.93 and $4.52. The rule's spend upper is $4.05 and $5.20 per arm. Idle storage of stopped pods is extra (§6, §8).
- **Where it lives (revised by the review).** Build the rule first, alone: `runkit/stage1-78b/` with `rules_78b.py`, the basis file, its derivation script and tests. It imports nothing from the Gate B folders. The kit around it is a separate decision (KD10): a Gate B kit fork is more work than "a copy", because the Gate B kit has no gated-token path for Llama, no "train + evaluate a0" job kind, and 1B pins throughout (§5). Nothing in this design touches an engine file, a Gate B pinned script, `tmp/gate-b-olmo`, `runkit/gate-b-olmo`, a sealed file, a config, or `scripts/cuda_preflight_family.py` (§5).
- **Money for block 0 (E, added by the review).** With the Gate B hold, block 0 needs about $140 in the account ($83.91 hold + $56.06 block need), about $48 above the 16 Oct balance of $91.94.

## 1. How the cap rule works now (R)

**Gate B kit (`runkit/gate-b-olmo`).**
- Per job (RULES:131-141): an arm's `upper_s` = the fixture's `e1_upper_s` + `training_s × steps/38` + `OVERHEAD_FLOOR_S` (1,000 s) + `SAFETY_MARGIN_S` (900 s). The start requirement is `upper_s + START_MARGIN_S` (1,800 s; RULES:34, 144-145).
- On the pod (RULES:160-177): each job needs max(plan value, this pod's projection). The projection uses the pod's own preflight `cap_projection` block: `e1_upper_s`, `training_s`, `overhead_s`, `margin_s`. The orchestrator (orchestrate.py:262-271, first job) and the job runner (setup/job_runner_gateb.py:267, every job) apply it. A job that does not fit is deferred, with every later job (job_runner_gateb.py:17-19).
- Cap (RULES:206-213): the largest, over the jobs k, of 42 min (`POD_OVERHEAD_S`, RULES:33) + the measured uppers of the jobs before k (`MEASURED_UPPER_S`, RULES:41: arm 52 min, a **1B** value) + job k's requirement, rounded up to 0.25 h.
- Guard (RULES:242-244; budget.py:120-130): a pod starts only if balance − every running pod's remaining cap × its price − the new cap × $1.85 ≥ $6. A running pod with no known cap counts at 15 h (budget.py:24). The guard reads caps only from working copies named `family-probe-*` or `gate-b-olmo*` beside the kit (budget.py:39, 53-57).

**Family-probe kits (the side project's 7–8B pods).** The orchestrator starts the job only when `projected_job_upper_s` ≤ remaining − 30 min (FPK/orchestrate.py:47, 195-202). That value counts two whole evaluations (PRE:174). So each OLMo-7B pod had a 12.5 h cap for one job of about 1.5 h (M, SIDE `create-intent.json`; R, `tmp/family-probe-sp-olmo2-7b-b-seed1103/KIT-README.md`:25). Each Llama-8B pod had 8.5 h (M).

**Why 4-arm pods are blocked (I, from the rules above).**
- With the family-probe rule, the last of 4 OLMo arms needs 41,078 + 1,800 s ≈ 11.9 h left. A 4-arm pod would need a cap of about 0.6 + 3 × 2.06 + 11.9 ≈ 18.7 h, or about 48 h if every arm is planned from the projection (4 × 11.9 h).
- With the Gate B rule and its 1B `MEASURED_UPPER_S` (52 min), the OLMo cap comes out at 10 h (at 38 steps). But each 7B arm needs 6.63 h left at its start. After two real arms (about 3.5–4.1 h with setup), only about 6.2 h is left, so the third arm defers.
- With the Gate B rule and a 7–8B measured upper, the rule works, but the OLMo cap is 13.75 h (38-step requirement; 13.5 h if all four are 33-step removal arms) for a pod that runs about 7 h.

## 2. Why the preflight over-projects: the term

`cap_projection` (PRE:161-174):

```
evaluation_upper = ms_per_step_full / 1000 * 2049 * batches + other      # PRE:168, batches = ceil(468/32) + ceil(600/32) = 34
projected_job_upper_s = 2 * evaluation_upper + training + overhead + 900  # PRE:174
```

`ms_per_step_full` comes from the full-length check: 32 copies of the longest development generation prompt, no stop ids, every row to 2,048 new tokens, with the optimizer state and the guard resident. It takes max(whole-check seconds / 2,048, mean of the last 256 steps) (R, PRE:21-24, 140-158, 441-453).

**Decomposition, OLMo-2-7B seed 1103 (M, SIDE `hosts/sp-olmo2-7b-1103/verification.json`, `round1/1103-a0-e1-a1/{ledger,progress}.jsonl`).** Projection 41,078 s; real job 5,466 s (91.1 min).

| Part of the excess (35,612 s) | Seconds | Share | Basis |
|---|---|---|---|
| The second evaluation (untuned) that this fine-tune-only job does not run | 19,026 | 53% | M: `untuned_upper_s` = `e1_upper_s` |
| Per-step time: 269.0 ms in the check against 116.1 ms in real capped batches, all 34 batches at the cap | 10,654 | 30% | M: check `ms_per_step_full`; real = median capped 32-row batch 237.7 s / 2,048 steps |
| Batches assumed capped: in fact 13 of 15 greedy and 0 of 19 sampled batches reached the cap | 3,883 | 11% | M: progress `capped` > 0 per batch |
| Training: resume-check seconds × 38/3 = 1,126 s against 886 s real | 240 | 1% | M |
| Floors and margin (1,000 + 900 s against about 55 s outside the stages) | 1,845 | 5% | M; these are deliberate margins |

The parts sum to 35,648 s. The 36 s difference is the projected against the real scoring stages.

Under the Gate B rule (one evaluation), the same term (18,742 s) is 79% of the 23,852 s start requirement.

**Why OLMo's check is slow (I).** OLMo-2-7B has 32 key-value heads, so it has no grouped-query attention (R, https://huggingface.co/allenai/OLMo-2-1124-7B-Instruct/raw/main/config.json: `num_key_value_heads` 32, 32 layers, hidden 4,096). Its KV cache is about 0.5 MiB per token, 4× Llama-3.1-8B's (Llama-3.1-8B has 8 key-value heads; R, the public config mirror https://huggingface.co/unsloth/Llama-3.1-8B-Instruct/raw/main/config.json). The check's 32 × 2,368 tokens need about 37 GiB of cache. In every OLMo check the peak was 66.63 GB allocated and 84.49 GB reserved, which is 99.3% of the 85.09 GB the card reports (M, `environment.cuda.total_memory_bytes`), with **204 allocator retries**. Llama's check had 0 retries (M, all 17 `verification.json` files). Real generation peaks about 5 GB lower (61.22 GB allocated), because the check also holds the optimizer state and the longest prompt (320 tokens) in every row. The cause (allocator retries at the memory edge) is an inference; the retry counts and peaks are M.

**The first batch (M and I, added by the review).** The engine sorts prompts by length, shortest first (ENG:578). So the first greedy batch has the *shortest* prompts. On OLMo it is still the slowest batch (256–314 s against 188–241 s for the others); on Llama it is not (213–247 s against 215–250 s). So the extra first-batch time (about 60–75 s) is a start effect of each engine process, probably allocator work after training (I). Each arm runs in its own process (job_runner_gateb.py:9), so each arm pays it once. The bound counts it once per arm.

**Llama (M, `sp-llama31-8b-b5e5-1102`).** Projection 18,117 s; real job 7,416 s. Here the second evaluation is the main excess. The check's 104.3 ms per step is *below* the real 120.3 ms. If every batch reached the cap, real generation would take about 8,510 s against the projected 7,266 s. In the measured jobs 14–15 of 15 greedy and only 5–11 of 19 sampled batches reached the cap. The Gate B rule's requirement fed with this preflight (12,391 s) is about 220 s below the corrected all-capped bound (12,613 s, §4): it covers that risk only by using part of its 1,800 s start margin.

## 3. Measured 7–8B times (M, SIDE)

All are fine-tune-only a0 jobs: 38 training steps, then one e1 evaluation (468 greedy prompts, 600 samples, 189 ARC questions, batch 32, cap 2,048). No measured job is a repair arm. Recipes B (1e-4), B5e5 (5e-5) and G on each family.

| Measure | OLMo-2-7B (9 units) | Llama-3.1-8B (8 units) |
|---|---|---|
| Outer job time, fine-tune only (`finished.json`) | 86.1–107.5 min, median 90.9 (n = 8); main recipe B 1e-4: 91.1, 103.9 | 105.2–141.1 min, median 123.8 (n = 7); main recipe B5e5: 121.6, 123.6 |
| Job with the untuned evaluation too (seed 1101 a0 pods) | 114.6 min | 174.2 min |
| Pod overhead = (create → first confirmed stop) − job | 21.8–41.8 min, median 30.4 | 24.5–41.2 min, median 31.5 |
| Training per step (ledger) | 18.9–24.3 s (two speed clusters) | 18.7–22.9 s |
| One 32-row batch that reaches the cap | first greedy batch ≤ 314.0 s; others ≤ 240.9 s (92–118 ms per step) | ≤ 250.3 s (first ≤ 246.9 s; 105–122 ms per step) |
| Batches that reached the cap (any row capped) | greedy 11–15 of 15; sampled 0–4 of 19 | greedy 14–15 of 15; sampled 5–11 of 19 |
| Scoring and other evaluation stages (query loss, ARC, guard, harm scores) | 268–329 s | 317–408 s |
| Model load, tokenize, memory check, init | ≤ 20 s | ≤ 20 s |
| Outer job − ledger end (process start, verify) | ≤ 42 s | ≤ 102 s |
| **Outer job − sum of all ledger stage seconds** (also counts the time before the first stage, ≤ 33 s, and between stages, ≤ 47 s; review) | 36–109 s | 39–163 s |
| Preflight `training_s` / `ms_per_step_full` | 950–1,202 s / 236.1–269.0 ms | 948–1,262 s / 70.1–104.3 ms |

The two speed clusters show in the preflight too. OLMo pods with preflight `training_s` about 950 s ran 18.9–19.1 s per step and 189–191 s per capped batch. Pods at 1,126–1,202 s ran 23.3–24.3 s per step and 235–238 s per batch (M). Llama's fast pod (`training_s` 948 s) ran 18.7 s per step and 215 s per batch; the others ran 22.7–22.9 s and 243–248 s (M). So the preflight's `training_s` is a usable speed signal on both families, even though its absolute projection is not. Llama's `ms_per_step_full` is a weak signal: it reads 1.0–1.5× below the real per-step time (M).

## 4. The proposed rule (M-cap)

All constants are per family and key on an allow-list of recipe `config_sha256` values (the main recipe and recipe G; the basis also holds B at the other LR), the engine identity X (`472fc7f6…`) and the GPU name. Any other recipe, engine or GPU refuses.

**Per job (the start requirement).** For an arm of `steps` optimizer steps (removal 33, add 38, a0 38):

```
GEN_ALLCAP   = max(FIRST_BATCH_MAX, BATCH_MAX) + 33 × BATCH_MAX                  # all 34 batches at the cap
upper_M      = steps × TRAIN_STEP_MAX + GEN_ALLCAP + SCORE_ALLCAP + EARLY_MAX + OUTSIDE_MAX
requirement  = max( max(s_pod, s_obs) × upper_M + 1,800 ,  F_pre )               # 1,800 = Gate B's START_MARGIN_S
```

- **Values (M, §3; SCORE_ALLCAP is E).** OLMo: TRAIN_STEP_MAX 24.26 s, FIRST 314.0 s, BATCH 240.9 s, SCORE_ALLCAP 1,250 s, EARLY 20 s, OUTSIDE 109 s. So GEN_ALLCAP = 8,264 s, upper_M(38) = 10,565 s (2.93 h), requirement **12,365 s (3.43 h)**; 33 steps: 12,243 s (3.40 h). Llama: 22.89 s, 246.9 s, 250.3 s, 1,250 s, 20 s, 163 s. So GEN_ALLCAP = 8,510 s, upper_M(38) = 10,813 s (3.00 h), requirement **12,613 s (3.50 h)**; 33 steps: 12,499 s (3.47 h).
- **OUTSIDE_MAX (M; review).** The slowest measured value of (outer job − the sum of all ledger stage seconds). It covers process start, the time between stages and the end. The first draft used (outer − ledger end), which misses the time before and between stages (up to about 70 s).
- **SCORE_ALLCAP (E; review).** Scoring time rises with answer length. Linear fits on Llama's 8 units (guard about 68 s + 0.084 ms per greedy output token; guard on samples about 79 s + 0.18 ms per sampled token; harm scores about 65 s + 0.28 ms per output token; fixed stages ≤ 38 s) give about 1,160 s if all 1,068 answers reach 2,048 tokens. OLMo's own guard fits are confounded by its two speed clusters; with Llama's guard slopes and its own harm fit it gives about 1,190 s. The first draft's 3 × NONGEN_MAX (987 s for OLMo, 1,224 s for Llama) is below or at these values, so the review sets SCORE_ALLCAP = 1,250 s on both families. The fit extrapolates 3–10× beyond the measured token counts, so this stays an E.
- **Check against the records.** Every measured job is below upper_M: the slowest OLMo job is 6,450 s against 10,565 s; the slowest Llama job is 8,466 s against 10,813 s (M-based). For comparison, 1.5 × the slowest measured job would be 9,675 s and 12,699 s. That is the same size, but the physical bound has a mechanism, not a chosen factor.
- **Training length (I; review).** TRAIN_STEP_MAX is measured on the full a0 data (unit 1103: 1.457 M padded tokens in 38 steps; M, `states/e1/state.json` `trajectory_cost`). An arm that removes short rows (for example P3, the 600 shortest answers) has more padded tokens per step. Scale the training term by max(1, the arm's padded tokens per step / the a0's), computed on the Mac from token counts only. Training is about 9% of upper_M, so the effect is small.

**The preflight as a sanity floor (it can only raise the requirement).**
- **Speed factor:** `s_pod = max(1, pre.training_s / 1,202, pre.ms_per_step_full / 269.0)` for OLMo, and `max(1, pre.training_s / 1,262, pre.ms_per_step_full / 104.3)` for Llama. The divisors are the slowest measured preflight values (M). Every measured pod gets s = 1. A slower pod scales its requirement up. On Llama the `training_s` term carries the signal (§3).
- **Refusal:** if `s_pod > 1.15` (E: beyond the measured spread), the pod stops before any job and its jobs are requeued (pre-job path; the setup time, about 18–37 min or $0.55–1.10, is lost; E).
- **Typical-case floor:** `F_pre = pre.training_s × steps/38 + pre.untuned_projected_s + 1,000 + 900 + 1,800`. On every measured pod F_pre is below the requirement (largest at 38 steps: OLMo 8,301 s on `sp-olmo2-7b-b5e5-1102`, Llama 9,393 s on `sp-llama31-8b-1102`; M-based). It binds only on a pod whose evaluation stages are slow in a way the speed factor misses.
- **Missing or non-finite preflight fields refuse** (as Gate B: "none never fits"). The fields already exist in `PREFLIGHT-DONE.json`, so the preflight script does not change.
- **Not used as a floor:** the preflight's own `e1_upper_s`. A floor of max(M-cap, Gate B projection) would bring OLMo's 6.63 h back.

**In-pod speed check (new; review).** The preflight cannot see a slowdown inside real generation. The OLMo jobs reserve 84.49 of the card's 85.09 GB while they generate (M). If real generation ever ran at the check's 269 ms per step (2.3× the measured 116 ms), a typical OLMo arm would take about 3.1 h (E: the 1103 job with its 4,205 s of generation × 2.32), and an arm with every answer capped about 6 h, past its 3.43 h requirement; the pod timer would then stop the pod in the arm (I). No measured job shows this: all 9 OLMo jobs ran their capped batches at 92–118 ms per step after the first batch (M). The rule: after each arm, the job runner reads that arm's `progress.jsonl` (batch times and capped counts only) and sets `s_obs` = its slowest capped 32-row batch after the first / BATCH_MAX (at least 1). Later arms use max(s_pod, s_obs). If `s_obs > 1.15`, the later arms defer and the lead records the case. The check is kit code only.

**Per pod (the cap; same structure as RULES:206-213).**

```
cap = round_up_0.25h( max_k [ POD_OVERHEAD + Σ_{j<k} MEASURED_UPPER_j + requirement_k(s = 1) ] )
MEASURED_UPPER = SPEND_UPPER = 1.15 × ARM_JOB_MAX        # OLMo 7,418 s (2.06 h); Llama 9,736 s (2.70 h)
POD_OVERHEAD   = 48 min                                   # E: 1.15 × the largest measured 41.8 min (Gate B: 42 min)
```

- ARM_JOB_MAX is the slowest measured fine-tune-only job of the family over all three recipes (OLMo 6,450 s, Llama 8,466 s; M). I include recipe G because repair arms can change answer length. P3 (removal of the 600 shortest answers) may make answers longer (I).
- The cap is planned at s = 1. On a pod with 1 < s ≤ 1.15, the last arm may defer. A deferral costs about one pod overhead on its new pod (about $1; E) and loses no work. An arm that is longer than MEASURED_UPPER (for example one with many capped answers) also defers later arms; it is not stopped unless it passes the cap itself.
- Spend upper per pod = (48 min + n × SPEND_UPPER) × $1.79. The funding need per block uses Gate B's `funding_need_usd` formula unchanged (worst path, guard term $6 + $1.85 × caps, contingency 1.25).
- **Gate B hold (new, both options; simplified by the review):** a 7–8B launch is allowed only if free balance − every running commitment − new cap × $1.85 ≥ $6 + `GATE_B_HOLD_USD`. **Default: a fixed hold of $83.91** (the frozen wave-1 need; RP §4; FOCUS 16 Oct 13:21) in `rules_78b.py`, until the lead records Gate B's last kit pod as done. It needs no record to keep up to date, and it errs on the safe side as Gate B spends. Option: a hold that the lead lowers by a recorded step after each Gate B launch. Either way every Gate B launch stays above its frozen threshold. Gate B's wave-1 rule reads the lead's raw balance record (plan_tool.py:480-484, 636-643), so the lead should not run Gate B `init-wave 1` while a 7–8B pod runs, or should net the record (I).

**Job kinds.** The rule covers `arm` (train + e1) and `evalonly` (an e1-style evaluation of an untuned or saved state: upper_M without the training term; for example the references for safety prompt, adapter scaling and Safe LoRA). It refuses every other kind until that kind has a measured 7–8B basis: A1 diagnostics, anchors, L1/S3/S4 scorer passes, c0, and **B+Qi** (constrained SFT changes the training loss, so its training step is not measured; review). The first such job runs alone on its pod with an explicit E cap (for A1: 6–11 h, RP §2.1, × 1.5), and then the kind is measured (KD6).

## 5. Where it lives, and T4

**Step 1, now, $0 (shared by B and C; revised by the review): the rule alone.** `runkit/stage1-78b/` holds:
- `rules_78b.py`: the one constants block (§4); the functions upper/requirement/speed factor/s_obs/floor/cap/guard/spend/funding; `MAX_ARMS_PER_POD_78B = 4`; the GPU name; the recipe allow-list; `GATE_B_HOLD_USD`.
- `measured-basis-78b.json`: the text-free timing fields of the 17 units in §3 (seconds, counts, memory, token counts, hashes; no answer, prompt or row). `rules_78b.py` pins its SHA-256.
- `derive_78b_basis.py`: a Mac-side script. It reads only the timing fields listed under "Sources" and writes the basis file. It never opens `eval/`, `generations`, `samples`, `prompts`, `ssh/`, `selector.jsonl` or `hidden/`.
- `tests/` (§10). They stay under `runkit/`, not under `experiments/` or `scripts/`.
- It imports nothing from `runkit/gate-b-olmo/` or `tmp/gate-b-olmo/` (it holds its own copies of the few Gate B functions it needs, such as `round_up_s`, `cents` and `funding_need_usd`, with a test that they equal RULES' results on the same inputs; that test loads RULES by path with `PYTHONDONTWRITEBYTECODE=1`, so no `__pycache__` file appears in the Gate B folder).

**Step 2: the kit shell (KD10; the review found more work than the draft said).** The rule needs a kit that creates pods, runs jobs and pulls records. Three routes:
- **(i) A fork of `runkit/gate-b-olmo/`** (the draft's route; e61ffcf, 10 Oct, is the last commit to touch it; M, `git log`). It is not a byte copy plus an import swap. It needs these edits, each reviewed: the **gated-token path for Llama-3.1-8B** (the Gate B launcher was built without the gated-token checks, launch.py:1-2, and its download script keeps the gated path unused, download_models_gateb.py:3; FPK/launch.py:8-21 has the token checks and the hand-over that must come back; this is security work); a **train-plus-evaluate a0 kind** for Llama's third Gate A seed (the Gate B `retrain` runs no evaluation and the Gate B `arm` needs an edit file; job_runner_gateb.py:11-13); **every 1B and Gate B pin** (RULES:55-75, 89-116: REC, RECIPE_S, the fixture, PROBE_KEY, the prepared manifest, sealed files, waves, worst path, Granite, volume 20 GB) and plan_tool's wave path; **the recipe for arms**: the Gate B arm runs with recipe S (job_runner_gateb.py:11), and the pinned `scripts/make_gateb_recipe.py` is fixed to the 1B recipe (lines 20-22), so a 7–8B arm needs either a job-runner edit to pass the plain recipe or an added 7–8B config under `experiments/` (KD8). `budget.py` keeps `KITS_GLOB = ("family-probe-*", "gate-b-olmo*")`, the same `LOCK_NAME` and the same lock folder (`tmp/`), so 7–8B and Gate B launches serialize on one lock. `probes.py` rows for `olmo2-7b` and `llama31-8b` come from FPK/probes.py:38-46, 66-77 (weight pins, the gated flag).
- **(ii) The B15 stage-1 kit**, when it is built. 1B stage 1 needs it by about 3 Nov (RP §5), and it must run repair arms (removal and add edits, references) that the Gate B kit does not. It imports `rules_78b.py` for 7–8B models. This avoids two kit forks (I).
- **(iii) For block 0's Llama a0 seed 1103 only:** the family-probe kit, which ran all 17 measured units with the same procedure as seeds 1101–1102. One arm per pod (cap 8.5 h, guard $21.73; expected spend about $4.6, E). It needs no new kind.
- Working copies: `tmp/family-probe-s1-olmo2-7b-<block>/` and `tmp/family-probe-s1-llama31-8b-<block>/`. The `family-probe-` prefix makes Gate B's guard read their real caps (budget.py:39). With any other name, Gate B's guard still counts each running 7–8B pod, at the 15 h fallback (safe, but it over-reserves about $4.50–8 per pod at launch, more as the pod runs; E).

**Option-specific:**
- **[B and C]** Block 0: the 7–8B noise block (R_1–R_3 on each family), Llama-8B's third Gate A seed, both families. One working copy per family.
- **[B]** Blocks A and B, the references and the confirmation on both families. Alpaca on Llama-8B: the training term scales with its step count. The basis holds only if the evaluation bank is unchanged (refuse otherwise).
- **[C]** The same, on the one family that the family-choice rule picks. No Alpaca at 7–8B.
- **[B, C] confirmation:** engine round Y changes the engine identity, so the basis refuses until the first Y pod measures again, or until the lead records a carry-over.

**T4 confirmation.** The design changes **none** of these: any file under `experiments/` (engine X, configs, tests); any file under `scripts/` (`cuda_preflight_family.py`, which ships in the Gate B bundle, pack_setup.py:48, is read for its output fields only); the four Gate B pinned scripts (RULES:100-103); `runkit/gate-b-olmo/**`; `tmp/gate-b-olmo/**`; the sealed files (`.ai/inputs/gate-b-sealed-20261008/`, `tmp/gate-b-anchors/`, `tmp/gate-b-sealed/`); `tmp/family-probe-budget.lock` (opened for `flock` in append mode, content unchanged). It adds new files only (`runkit/stage1-78b/**`, later `tmp/family-probe-s1-*/**`). Gate B's `pack_setup.py` refuses while any file under `experiments/` or `scripts/` is uncommitted (pack_setup.py:195-199). So the build works in a copied workspace, and the lead integrates by explicit-path commits (stage-1 brief T3). It leaves no file in `experiments/` or `scripts/`. If a later step needs a 7–8B config (route (i) or stage 1), that is an **added** config under `experiments/`: commit it by explicit path, with the lead's consent (KD8). The new kit changes the *behaviour* of Gate B's guard (it now sees the 7–8B pods' caps), but no Gate B file; that is the intended effect.

## 6. Memory settings (M)

- Keep micro-batch 2 × accumulation 64 (128 rows per step) on both models, generation batch 32, cap 2,048, `sdpa`, no gradient checkpointing (R, the two recipes). The mb4 rung ran out of memory on both models; mb2 passed (M, `PREFLIGHT-DONE.json` `tried` of `sp-olmo2-7b-b2-1101` and `sp-llama31-8b-1101`).
- **OLMo-2-7B peaks (9 jobs):** training 61.11 GB allocated (63.91 GB reserved); greedy generation 61.22 GB allocated and **84.49 GB reserved, 99.3% of the card's 85.09 GB** (M, `total_memory_bytes`); full-length check 66.63 GB allocated, 204 allocator retries.
- **Llama-3.1-8B peaks (8 jobs):** training 63.43 GB (66.68 GB reserved); generation 36.49 GB allocated (84.37 GB reserved, cached training blocks); full-length check 38.49 GB, 0 retries.
- **4 arms per pod do not raise the peak (R):** the job runner starts one engine process per step (setup/job_runner_gateb.py:9), so each arm starts with an empty cache.
- **Risk:** OLMo runs at the card's limit. A pod with another driver or CUDA build could run out of memory, or slow down, in generation. The preflight's `generation_memory_ok` check runs on every pod and stops it before any job (R, PRE:21-26); the in-pod speed check (§4) catches a slowdown after one arm. I do not propose `expandable_segments` or other allocator settings: they change the environment against the measured records and the fixture.
- **Disk (E):** the weights live in the container's Hub cache (download_models_gateb.py:44-45; no `HF_HUB_CACHE` is set at create, M, `create-intent.json` `env_names`): 23.5 GB (OLMo + guard) or 24.9 GB (Llama + guard) in a 60 GB container disk. The states live on the volume. Each unit keeps three states (`init`, `q`, `e1`; M, `states/`), each with adapter, optimizer and RNG files (M, `state.json` `files`). Adapter plus Adam moments are about 1.9 GB per state (E: 160–168 M trainable fp32 parameters × 3; M, ledger `trainable_parameters`). The side kits used a 30 GB volume for one arm (M). For 4 arms I propose a 50 GB volume and a free-space check before each job (KD5).
- **Idle storage (R and E; review).** RunPod lists volume storage of a stopped pod at $0.20 per GB per month (twice the running rate; R, https://www.runpod.io/pricing, read 16 Oct). A stopped 50 GB pod costs about $0.33 per day (E). The states live only on the pod's volume: the finisher pulls a light tar without model states (finisher.py:7-8). If block A and B pods are kept stopped for their states, 10 such pods cost about $100 per month (E). The plan needs a state rule before block A (KD5): which states later steps need, and whether to pull them (about 5.8 GB per arm, E) or delete the pod after a verified light pull. The guard counts running pods only, so idle storage also slowly erodes the money above the Gate B hold.

## 7. Arms per pod, caps and the price limit

| Arms per pod | OLMo cap (Gate B rule) | OLMo guard | Llama cap (Gate B rule) | Llama guard |
|---|---|---|---|---|
| 1 | 4.25 h (7.50 h) | $13.86 | 4.50 h (4.25 h) | $14.33 |
| 2 | **6.50 h** (9.50 h) | **$18.03** | **7.25 h** (7.00 h) | **$19.41** |
| 3 | 8.50 h (11.50 h) | $21.73 | 9.75 h (9.75 h) | $24.04 |
| **4** | **10.50 h (13.75 h)** | **$25.43** | **12.50 h (12.50 h)** | **$29.13** |

(E, computed from §4 with the 38-step requirement for the last arm. "Gate B rule" = RULES with the 7B preflight of `sp-olmo2-7b-1103` or `sp-llama31-8b-b5e5-1102`, 42 min overhead and the same 1.15 × measured upper. Guard = $6 + cap × $1.85, half-up cents. Review: the 2-arm caps rose from 6.25 h and 7.00 h; with only 33-step arms the Llama 2-arm cap stays 7.00 h, and the Gate B rule's 4-arm OLMo cap is 13.5 h.)

- **Recommended: 4 arms per pod on both families** (the Gate B [D21] value; RULES:65). The user confirmed 4 for Gate B's path only, so the 7–8B value needs its own confirmation (KD2).
- The gain from 4 over 3 arms is small: about 2% per arm (§8). The cost: one pod failure exposes more finished work, because the finisher pulls only after the job runner ends (R, finisher.py:7-12). A crash inside the job runner still pulls; only a lost host loses records (I).
- **The $10/h limit** (RULES:47) is a create-time price limit per pod. One A100 at $1.79/h is far below it, so it does not limit arms per pod. It binds only for a multi-GPU pod: 5 × A100 = $8.95/h passes, 6 × A100 = $10.74/h fails (E, at $1.79 per GPU). RunPod's public page lists the A100 SXM 80GB at $1.79/hr on Secure Cloud (R, https://www.runpod.io/pricing, read 16 Oct; re-read by the review).
- **Block 0 example [B and C] (E):** an OLMo pod with R_1–R_3 (3 arms, cap 8.5 h) and a Llama pod with R_1–R_3 + a0 seed 1103 (4 arms, cap 12.5 h), in parallel. Guard $6 + 21 × $1.85 = $44.85; rule spend upper $12.50 + $20.80 = $33.30; expected spend $24.75; funding need 1.25 × $44.85 = **$56.06**, plus the Gate B hold. This agrees with RP §2.2's "about $30–40" for the noise block's spend. **With the hold (review):** the second launch passes the guard only if the balance is at least about $128.76 ($6 + $83.91 + 21 × $1.85), and the block's funding need with the hold is about $139.97, about $48 above the 16 Oct balance of $91.94 (E; before idle storage). The caps did not change in the review.

## 8. Cost per arm at $1.79/h (E)

Expected = median measured job and median measured pod overhead (§3). Upper = slowest measured job and largest measured overhead. Rule = the M-cap spend upper. Planning = expected × 1.2 (RP §2.1's allowance for failed pods and re-runs). Judge pods are extra (about $0.1–0.2 per arm; R, RP §2.1). Idle storage of stopped pods is extra (about $0.33 per pod per day at 50 GB; §6).

| Arms per pod | OLMo expected | OLMo upper | OLMo rule | OLMo planning | Llama expected | Llama upper | Llama rule | Llama planning |
|---|---|---|---|---|---|---|---|---|
| 1 | $3.62 | $4.45 | $5.12 | $4.34 | $4.63 | $5.44 | $6.27 | $5.56 |
| 2 | $3.17 | $3.83 | $4.40 | $3.80 | $4.16 | $4.82 | $5.56 | $4.99 |
| 3 | $3.01 | $3.62 | $4.17 | $3.62 | $4.01 | $4.62 | $5.32 | $4.81 |
| **4** | **$2.94** | **$3.52** | **$4.05** | **$3.53** | **$3.93** | **$4.52** | **$5.20** | **$4.71** |

- Main recipes only, 4 per pod: OLMo B 1e-4 $2.94–3.33; Llama B5e5 $3.86–3.92. These are inside RP §2.1's ranges ($2.8–3.6 and $3.3–4.1).
- Check against RP §3 (I): B's full 7–8B comparison at 65–72 (OLMo) and 69–76 (Llama) FRE × the 4-per-pod expected-to-upper costs = $462–597, or $555–716 with +20%. RP gives $520–710. (FRE counts scorer jobs such as A1 as run equivalents; an A1 pass is 6–11 h, so this check is loose; review.)
- Pod time at 4 arms (E): OLMo 6.6 h expected (7.9 h upper); Llama 8.8 h (10.1 h).

## 9. Bootstrap and download times at 7–8B (M, SIDE)

| Step | OLMo-2-7B (9 pods) | Llama-3.1-8B (8 pods) | 1B Gate B, for contrast |
|---|---|---|---|
| Weights | policy 14.61 GB (3 shards, open) + guard Qwen3Guard-Gen-4B 8.84 GB + tokenizer 0.01 GB | policy 16.07 GB (4 shards, gated) + guard 8.84 GB | policy 2.98 GB + guard 8.84 GB |
| Setup process (environment + open downloads; `setup-001`) | 145–775 s | 123–789 s | 290–774 s |
| Gated policy download | — | 27–72 s | — |
| Create → BOOTSTRAP-READY | 3.3–15.5 min | 3.2–14.6 min | 5.7–14.0 min |
| Preflight (one per pod) | 869–1,213 s (14.5–20.2 min) | 911–1,217 s | 496–520 s |
| Create → PREFLIGHT-DONE | 18.4–37.2 min | 19.8–35.9 min | 15.3–23.2 min |
| JOB-DONE → confirmed stop (pull, check, stop) | 1.7–3.6 min | 1.0–3.4 min | 1.8–2.4 min |

- The review re-checked the setup, create → BOOTSTRAP-READY, create → PREFLIGHT-DONE and JOB-DONE → stop rows (M, same files). It did not re-check the preflight-process row or the download sizes.
- The light pull is small (3.5 MB and 4.4 MB on the two 7–8B pods I checked; 10.3 MB for Gate B's 3-arm 1B pod; M, `pulls.jsonl`). It does not grow much with more arms, because model states stay on the pod (R, finisher.py:8).
- The slowest setups (about 13 min) dominate the overhead spread. The download speed varies by host, not by model (I).

## 10. Tests the new rule needs

All run on the Mac on CPU, with no pod and no network. Mutation runs follow the project's rule: kill a mutant only on a real test failure, never on an error, and run the baseline with the same command.

1. **Golden numbers:** `upper_M`, `requirement` (33 and 38 steps) and `cap_hours` (1–4 arms) equal the values in §4 and §7 for both families (review values: requirements 12,243 / 12,365 s and 12,499 / 12,613 s; caps 4.25 / 6.5 / 8.5 / 10.5 h and 4.5 / 7.25 / 9.75 / 12.5 h). Guards and spend uppers match to the cent (half-up).
2. **Basis pin:** `measured-basis-78b.json` matches its SHA-256 in `rules_78b.py`. Each constant equals the maximum recomputed from the basis file (TRAIN_STEP_MAX, FIRST/BATCH_MAX, EARLY, OUTSIDE_MAX as outer − Σ stage seconds, ARM_JOB_MAX, the preflight maxima). SCORE_ALLCAP ≥ 3 × the largest scoring time and ≥ the linear-fit all-capped value recomputed from the basis.
3. **Upper-bound property:** for every unit in the basis, outer job ≤ `upper_M(38)`, and the all-capped time (34 × that unit's own slowest capped batch + its training + SCORE_ALLCAP + its outside time) ≤ `upper_M(38)`.
4. **Speed factor:** s = 1 for every measured pod; s scales up on a synthetic slow pod; a faster pod never lowers the bound; `s > 1.15` refuses; a missing, zero, negative, NaN or infinite field refuses.
5. **In-pod speed check (review):** `s_obs` = 1 on every measured unit's `progress.jsonl`; a synthetic arm with 2.3× batch times raises the next arm's requirement and, above 1.15, defers the later arms; the first batch is excluded; a missing or empty progress file refuses the next arm.
6. **Sanity floor:** F_pre binds on a synthetic pod with a large `untuned_projected_s`, and never lowers the requirement. A mutant that uses `min` in place of `max` fails.
7. **Keys:** a recipe not on the allow-list (for example the mb4 rung), another engine identity, or another GPU name refuses; recipe G passes.
8. **Kinds:** `arm` and `evalonly` give their values; every other kind (A1, anchors, scorer passes, c0, B+Qi) refuses.
9. **Cap structure:** the sum is over j < k (a mutant with j ≤ k fails); rounding is up to 0.25 h; `pod_sizes` splits as Gate B's does (8 → 4 + 4, 6 → 3 + 3, 5 → 3 + 2); a pod with more than `MAX_ARMS_PER_POD_78B` arms refuses. The copied helpers equal RULES' results on the same inputs.
10. **Gate B hold:** the guard allows a launch exactly at $6 + hold and refuses one cent below; the default hold is $83.91.
11. **Cross-kit counting:** the working-copy name matches `family-probe-*`; this kit's `KITS_GLOB` finds Gate B's `hosts/*/pod.json`; both kits use one lock path.
12. **Job runner dry run:** on a fake `PREFLIGHT-DONE.json`, it computes s and the requirements, defers the right job when the remaining time is short, and refuses when the fields are absent. The free-space check refuses below the threshold.
13. **Mutants that must die:** margin 1.15 → 1.0; 34 batches → 33; the first-batch term dropped; SCORE_ALLCAP → 3 × NONGEN; OUTSIDE_MAX → outer − ledger end; `max(1, s)` → `s`; `max(s_pod, s_obs)` → `s_pod`; START_MARGIN removed; overhead 48 → 42 min; round-down.
14. **T4 guard test:** after the build, `git status --porcelain -- experiments scripts` prints nothing. The engine identity is still X. The git-tracked files of `runkit/gate-b-olmo/**`, the files of `tmp/gate-b-olmo/**` listed in its manifest, the four pinned scripts, `scripts/cuda_preflight_family.py` and the sealed files match their recorded hashes. No new `__pycache__` entry appears in a Gate B folder.
15. **Derivation privacy:** `derive_78b_basis.py` opens only allow-listed file names (a test with a trap file named `generations.jsonl` that must stay unopened). Its output contains no string field longer than a hash or a stage name.

## 11. Challenge: alternatives, weak points, failure cases, smallest check

**Simpler alternatives.**
1. *Keep the Gate B rule and change only the measured constants* (arm `MEASURED_UPPER_S`/`SPEND_UPPER_S` to 7–8B values). This is the least new logic. It works, but OLMo's caps are 13.75 h and its arms need 6.63 h left at start. For Llama it gives the same 4-arm cap as the M-cap, with a requirement about 220 s below the all-capped bound. This is the fallback if the build time is short.
2. *1.5 × the slowest measured job* in place of the physical bound. The numbers are almost the same (OLMo 9,675 s, Llama 12,699 s), but the factor has no mechanism behind it.
3. *One arm per pod* (as in the side project). No new rule is needed, but it costs about 18–23% more per arm (§8) and needs 4× as many launches.
4. *Rolling cap:* plan the cap for the first arms and extend it before each later arm (host.py extend-cap). This reserves less money, but it adds an operator step and a new failure mode (a refused extension). Not recommended.
5. *Multi-GPU pod* (for example 4 × A100 at $7.16/h, one arm per GPU). It shares one setup and is faster on the calendar. It needs new job-runner code, multi-GPU supply and per-GPU environment checks. Not recommended before stage 1.
6. *The rule now, the kit later (review; recommended).* Build only `rules_78b.py`, the basis and the tests now ($0, no kit file, no T4 contact). Choose the kit shell when block 0's date is set (KD10). This defers the expensive and security-relevant kit work until the user chooses B or C and money exists, and it lets the B15 stage-1 kit carry both sizes.

**Weak assumptions.**
- Repair arms behave like the measured a0 units. The requirement does not depend on this for generation (all batches are capped in it); the training term may (row lengths, §4), and the cap's sum term does. Longer earlier arms defer the last arm; nothing is killed unless an arm passes the cap.
- The measured pods are one GPU type in two speed clusters. A third, slower cluster is caught by the speed factor or refused. A slowdown that shows only in real generation is caught after one arm by the in-pod speed check, not before.
- The sampled batches in the basis had few rows still active late in a batch. The engine samples each active row in a Python loop (ENG:518-521), so an all-capped sampled batch does more host work per step: about 1–2 ms per step, about 60 s per job (I), inside the margins.
- The Gate B kit's pre-job steps at 7–8B take about as long as the side kits' steps. The 48 min overhead has 6 min of margin over the largest measured value.
- Only three OLMo units (B 1e-4) and two Llama units (B5e5) use the exact main recipe. The basis uses all three recipes per family, which is more conservative.
- The scoring allowance is an extrapolation (E, §4).

**Failure cases.**
- An arm whose every answer reaches the cap, on a pod at s = 1.15: the requirement still covers its generation (by construction); scoring is covered if the linear fit holds.
- Real generation at the check's slow per-step time (§4): the first such arm may pass its requirement and, with every answer capped, reach the pod's cap; the in-pod speed check defers the later arms.
- A lost heartbeat: no job starts (as in Gate B).
- An OLMo out-of-memory in generation on a different host build: that arm crashes and later arms do not start. The pull still runs.
- A full volume with 4 arms' states (E): the free-space check stops before the job.
- Stopped pods kept for their states: idle storage grows (§6).

**Smallest decisive check ($0).** Build `rules_78b.py` and the basis file, then run tests 1–3 on the Mac against the 17 measured units. Then block 0's two pods are the live check. Record per-arm job time, per-batch time and `s_obs`. If any arm exceeds 1.15 × ARM_JOB_MAX, any capped batch exceeds BATCH_MAX, or any scoring stage exceeds the fit by more than 20%, update the basis (a recorded lead step) before block A.

## 12. Decisions needed (for the lead; KD2 and KD10 also bear on the user)

Renamed from D1–D9 by the review, because "D5" is the user's repair-comparison decision in FOCUS.

1. **KD1 Rule:** the M-cap as in §4, or the simpler fallback (alternative 1: Gate B rule with 7–8B measured constants).
2. **KD2 Arms per pod at 7–8B:** 4 on both families (recommended; caps 10.5 h and 12.5 h), or 3 on Llama (cap 9.75 h). The user confirmed 4 for Gate B's path only (FOCUS 9 Oct 19:37 UTC). The lead may read the user's 16 Oct 19:06 UTC "go ahead" (FOCUS 19:08 UTC) as covering it, or ask.
3. **KD3 Margins (E values):** 1.15 on the measured job, SCORE_ALLCAP 1,250 s, 48 min pod overhead, refusal at s > 1.15 and at s_obs > 1.15.
4. **KD4 Gate B hold:** a fixed $83.91 until Gate B's last kit pod (recommended), or a lead-lowered hold; and no Gate B `init-wave 1` while a 7–8B pod runs.
5. **KD5 Volume and states:** 50 GB with a free-space check (E), against 30 GB as in the side kits; and the state rule (keep stopped, pull, or delete after a verified light pull), with an idle-storage allowance in each block's need.
6. **KD6 Unmeasured kinds** (A1, anchors, scorer passes, c0, B+Qi at 7–8B): a single-job pod with an explicit E cap, then measure.
7. **KD7 Working-copy names:** `tmp/family-probe-s1-*` so Gate B's guard sees the real caps (recommended), or another name and accept the 15 h fallback count.
8. **KD8 Added configs under `experiments/`** before Gate B's last kit pod (a 7–8B recipe for route (i), or for stage 1): allowed as committed additions, or wait.
9. **KD9 [B, C] Basis after engine round Y:** re-measure on the first Y pod (recommended), or a recorded carry-over.
10. **KD10 Kit shell (review):** build the rule alone now and choose later (recommended); a Gate B fork (with the gated-token path, the a0 kind and the re-pins, each reviewed); the B15 stage-1 kit; or, for block 0's Llama a0 seed only, the family-probe kit.
11. **KD11 In-pod speed check (review):** adopt `s_obs` as in §4 (recommended), or rely on the preflight and the cap alone.

## 13. Limits

- No repair arm has run at 7–8B. The basis is 17 a0 units on two recipes per family plus recipe G.
- The scoring allowance, the overhead margin, the volume size, the state sizes and the idle-storage figures are E.
- The cause of OLMo's slow check (memory pressure) is an inference. The cause of Llama's fast check is not shown (the real per-step callback only records the item and checks an optional wall limit; R, `experiments/safety_selection/ledger.py`:70-74; so it is not the cause).
- I did not run any code from the kits or the engine. All numbers come from reading the records and from arithmetic in scratch scripts. The review's cap and requirement arithmetic was done by hand after a disk-full error stopped the scratch scripts (it is shown in §4 and §7 and can be re-run by test 1).
- I did not check A100 supply for parallel pods. The public page lists the A100 SXM at $1.39/hr on Community Cloud only in its page data (R, re-read by the review); the kits used Secure Cloud.

## 14. Review changes (2026-10-16, about 21:48–22:20 UTC)

**Checked and confirmed (M or R):** every RULES, PRE, budget.py, plan_tool.py, finisher.py, pack_setup.py, family-probe orchestrator and KIT-README reference (two line ranges widened: orchestrate.py:262-271, plan_tool.py:480-484 added); the §2 decomposition (all five parts and the 35,648 s sum); every §3 value against the 17 units (including the medians 90.9 and 123.8 min, overheads 30.4 and 31.5 min, capped-batch counts, scoring ranges, the ≤ 42 s and ≤ 102 s end gaps); the §6 memory peaks, retries and the mb4 out-of-memory; the trainable parameter counts; engine X on all 17 units; the KV-head counts (two public config files); the $1.79/hr Secure Cloud price; every §7 Gate B-rule cap, every §8 cost and the block-0 money.

**Corrected:**
1. **Time outside the stages.** The bound missed the time before and between ledger stages (up to about 70 s). OUTSIDE_MAX = outer − Σ stage seconds: OLMo 109 s, Llama 163 s (M).
2. **Scoring allowance.** The first draft's linear-fit basis (about 830 s all-capped) did not reproduce: the review's fits give about 1,160–1,190 s, above OLMo's 3 × NONGEN (987 s). SCORE_ALLCAP = 1,250 s on both families (E).
3. **Numbers.** Requirements: OLMo 3.34 → 3.43 h, Llama 3.48 → 3.50 h. 2-arm caps: OLMo 6.25 → 6.50 h ($17.56 → $18.03), Llama 7.00 → 7.25 h ($18.95 → $19.41). The 1-, 3- and 4-arm caps, the guards for them, the per-arm costs and the block-0 money did not change.
4. **Card memory.** The card reports 85.09 GB (M), not "about 85.9 GB nominal"; the reserved peak is 99.3% of it.
5. **The Gate B-rule column** is at 38 steps; with four 33-step removal arms the Gate B rule's OLMo 4-arm cap is 13.5 h. Llama's Gate B-rule requirement is about 220 s below the all-capped bound.
6. **Decision names** D1–D9 → KD1–KD9, because D5 is the user's decision in FOCUS.

**Added:**
7. **Engine evidence (R):** finished rows stay in the batch (ENG:543-563), so capped-batch times are a valid all-capped basis; prompts are sorted shortest first (ENG:578), so the slow first OLMo batch is a per-process start effect; the per-row sampling loop (ENG:518-521) is a small unmeasured cost.
8. **In-pod speed check** (`s_obs`, KD11): the preflight cannot see a slowdown in real generation, and OLMo generates at 99.3% of the card.
9. **Hidden kit work** (KD10): the Gate B kit has no gated-token path for Llama (launch.py:1-2), no train-plus-evaluate a0 kind, 1B pins throughout, and arms that run with a recipe S made by a 1B-only pinned script. So "a byte copy" was wrong. Recommended: build the rule alone now; choose the kit shell later.
10. **Idle storage** (KD5): $0.20 per GB per month for a stopped pod's volume (R); about $0.33 per day per 50 GB pod (E); states live only on the pod.
11. **Gate B hold** simplified to a fixed $83.91 by default; block 0 then needs about $140 in the account, about $48 above the 16 Oct balance (E).
12. **Recipe allow-list** (recipe G passes), **B+Qi** refused until measured, a **training-length scale** for arms with longer rows, `__pycache__` and explicit-path rules for T4, and new tests 5 and 13 items.

**No conflict found** with T4 (new files only), the frozen Gate B pre-registration revision 5 (no Gate B rule, number or file changes; the hold protects its money rule), D5 = (a) (no estimand changes), or the user's FOCUS decisions (4 arms per pod and the $10/h limit kept; the $6 reserve and $1.85 planning price kept). One point needs care: the user confirmed 4 arms per pod for Gate B only (KD2).
