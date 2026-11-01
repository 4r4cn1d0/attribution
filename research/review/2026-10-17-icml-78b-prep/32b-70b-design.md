# 32B and 70B check: design (DESIGN PROPOSAL)

**Status: DESIGN ONLY. It adopts nothing and changes no file.** Written 2026-10-16 at about 21:55 UTC (17 Oct IST; clock checked with `date -u`) by an Opus worker for the main-study lead (GI VI). **Revised in place after an adversarial review, 2026-10-16 at about 22:12 UTC (clock checked with `date -u`); the changes are listed in "Review changes" at the end.** Read-only work: no run, spend, pod, RunPod call, Hugging Face download, commit or agent. The only file changed is this one. It answers re-plan §5 item 5 ("32B/70B design").

**Scope.** The re-plan (RP) has no adopted option. The RP puts the 32B check in option B only ("32B headline check (B only, if funded)", R, RP:128; cut first, RP:138). What B and C share here is only the **$0 work** (this design, the S0 reads after approval, drafts kept outside the repo). The smoke test and every 32B tier are **[B]** spend. This design also proposes **[C-OLMo]** (C with OLMo-2-7B as its one 7–8B family) as a possible home for the 32B. That is new: the RP does not include it, so it is decision D13. **[C-Llama]** marks the case where the 32B is off-family.

**Labels.** **M** = measured (source path follows). **R** = read (path:line or URL). **E** = estimate (basis follows). **I** = inference. **U** = unverified assumption (the RP's label; it needs a check before use).

**Sources.** RP = `writing/paper/2026-10-17-icml-replan-PROPOSAL.md`. F = `research/FOCUS.md` at `19c2d28ccc`. At review time HEAD and origin are `1a5189b` (a paper commit), and FOCUS is the same file at both commits (M: `git diff --stat 19c2d28 HEAD -- research/FOCUS.md` is empty), so the F line numbers hold. STB = `.ai/briefs/stage1-commitments-build-20261016.md` (T3 at :64, T4 at :65). PACK = `runkit/gate-b-olmo/pack_setup.py`. Y = the sibling design `tmp/gi-vi-parallel/icml-78b-prep/engine-round-Y-design.md` (read only). LEDG = engine ledgers `tmp/<kit>/retrieved/<host>/tree/{round1/<unit>,cuda-preflight-1}/ledger.jsonl`; VER = the preflight reports `…/cuda-preflight-1/verification.json`; PROG = `…/round1/<unit>/progress.jsonl`. Kits read: `tmp/family-probe-olmo2-1b-g-seed1102`, `tmp/family-probe-sp-olmo2-7b-b-seed1103`, `tmp/family-probe-sp-llama31-8b-b5e5-seed1102`, `tmp/family-probe-sp-qwen25-7b-b-seed1102`, and the other `tmp/family-probe-sp-*7b*`/`*8b*` preflights. CAP = the sibling design `tmp/gi-vi-parallel/icml-78b-prep/78b-kit-cap-rule.md` (another worker, read only). I printed only numbers, stage names and ids from these files. I opened no data row, prompt, answer, anchor, `selector.jsonl` or `hidden/` file.

---

## 0. Summary

- **32B model:** `allenai/OLMo-2-0325-32B-Instruct` (Apache-2.0, not gated; 64 layers, hidden 5,120, 40 query heads and **8 key/value heads (GQA)**, context 4,096). It is the only 32B member of the OLMo-2 family. Llama 3.x has no model between 8B and 70B, so a 32B point exists for OLMo only (R, §2).
- **GPU:** one **H200 141 GB** per run. With **gradient checkpointing** and micro-batch 4 × accumulation 32, training needs about **79 GiB** and evaluation at generation batch 32 about **93 GiB** (E, §4). Without checkpointing, even micro-batch 1 needs about 134–143 GiB: no fit. A100/H100 80 GB, H100 NVL 94 GB and RTX PRO 6000 96 GB do not fit at batch 32 (E).
- **Engine:** single GPU only, bf16 base, no 4-bit path (M). **OLMo-2-32B needs no engine code change** (I): the bf16 + float32-LoRA path, the gradient-checkpointing path and the Olmo2 class already exist. It needs new recipe configs and a kit (new files only). No engine file, Gate B pinned script, Gate B kit file or sealed file changes (§8). **But the new configs and tests should not enter the repo's `experiments/` or `scripts/` before Gate B's last kit pod:** a Gate B re-pack bundles every `.py/.json/.md/.lock` file under `experiments/minimal_safety` and `experiments/safety_selection`, and refuses any uncommitted file under `experiments/` or `scripts/` (M, PACK:195-200, 220-223; STB:64). A committed new config is not an engine file, pinned script, kit file or sealed file, so T4's letter (STB:65) allows it; it would only ride, unused, in a recovery re-pack. Recommended: wait, and keep the drafts under `tmp/gi-vi-parallel/`. This is the same choice as the CAP design's KD8; decide both together (D15).
- **Kit:** the family-probe kit runs only the a0 fine-tune (plus the untuned unit) and one seed per pod (M, `runkit/family-probe/plan_tool.py:53`; each seed kit's `plan.json` has one host). So it can run Gate A (T1, on 3 pods), but not the S1 arms of T2/T3. Those need a kit with add/removal arms and several arms per pod: the kit shell that the 7–8B blocks will use (the CAP design's KD10; its route (ii) is the B15 stage-1 kit, with the cap rule in `runkit/stage1-78b/`). **Simpler: make the 32B a parameter set of that one kit** (GPU type, price, probe entry, ladder), not a second kit (§8, D14).
- **Time (E, scaled from M):** decode is overhead-bound at about **3.6–3.8 ms per layer per step** at batch 32 on all four measured models (M, PROG). So a 32B decode step is about 0.24 s (64 layers), about 2.1× OLMo-2-7B. A 32B train + evaluate job is about **3.2 h** (2.7–4.4 h). Generation is about 80% of it.
- **Price (E, RunPod public page "Updated October 8, 2026", read 16 Oct 2026):** H200 **$5.29/h** (Secure), B200 $7.99/h, B300 $8.99/h. All are under the user's $10/h limit. The RP planned the 32B at $3–4/h (U); the Secure price is 30–75% above that.
- **Cost of the 32B check (E, with the 20% allowance and the smoke test):** Gate A only (T1) **about $98** ($81–131) with two units per pod (stage-1 kit), or **about $104** ($86–140) on a family-probe copy (3 pods); Gate A + one 3-seed P4 contrast (T2) **about $165** ($137–223); Gate A + a 6-seed P4 contrast (T3) **about $300** ($250–408). A P3 or P6 contrast instead of P4 costs about $230–245 at T2 (§6). The RP's "+$110–230" should read about +$100–300 at Secure prices.
- **Money in the account is more than the spend.** The budget guard counts every running pod at its full remaining cap. Under the present cap rule a one-fine-tune 32B pod needs about $78–96 of free balance (E: a 12–15 h cap at $6/h + $6), so three parallel pods need about $230–290 at the third launch, for about $100 of spend (§6). A measured cap rule (CAP's M-cap) cuts this to about $35–40 per pod.
- **Smoke test [B]:** one H200 pod that runs the kit's preflight and then stops at the cap gate. About **$5–8**, cap upper $10.58. It measures memory, step time, determinism, host memory and the tokenizer (including the preflight's existing with/without-BOS record) before any scientific unit.
- **70B: drop it for ICML (agree with RP decision 9).** It is Llama only, needs a B300 (the pinned environment on its GPU generation is U), costs about **$225** for Gate A alone (E) and sits $1.01/h under the $10/h limit. Multi-GPU and QLoRA both need engine changes, and QLoRA also changes the experimental model.
- **The contrast is a scientific choice, not a cost setting.** F:257 (user-agreed) asks for "Gate A plus the most important comparison". P4 (S1 − a0) is the cheapest because it reuses the Gate A units, but it holds no diagnosis, so a P4-only 32B check says nothing about "diagnose or retrain". Under D5 (a) P1–P6 are co-primary, so no rule names one "most important" contrast. GPT or the user decides (D2).
- **1 Dec go/no-go:** go for the 32B only if new money covers it after every 7–8B and confirmation need (guard headroom included), the smoke test passed, Gate B's last kit pod is done, and the option is B (or C-OLMo, if D13 allows it) (§9). The earlier condition "7–8B block B started" is removed: the RP's latest start for block B is 3 Dec (RP:106), after the go date.

---

## 1. What the check is and what it can show

- F 8 Oct 12:53 (R, F:257) set the scale ladder: "a headline check (Gate A plus the most important comparison) at the largest single-GPU size: OLMo-2-32B on an H200 (141 GB) and, if funded, Llama-3.x-70B on a B300 (288 GB)", one GPU type per comparison, and "a small engine/kit round (GPU type, memory ladder, caps) and a cheap smoke test before any large spend".
- **Gate A at 32B** = the untuned 32B baseline unit (evaluation only) plus 3 recipe-B fine-tunes at e1 (seeds 1101–1103), read by the frozen family-probe bars (R, F:337–348): partial erosion 20 ≤ E ≤ 55 pp; answers end; ARC drop ≤ 0.03 and held-out task loss below the untuned model's; Granite agrees on the direction; for a 3-seed Gate A, E ≥ 2 × SD and every seed above baseline.
- **The contrast.** P1 (A1 − R) and P2 (L1 − R) need gradient or representation scorer passes. At 1B the A1 pass took 3.04 h (M, RP §2.1). At 32B it would take about 18–40 H200-hours (E: the 1B pass × 6–12 for compute, plus 11× larger float64 gradient vectors on the CPU; engine.py:675). That is more than the whole T3. The limit is time, not host memory: the query side is one mean gradient per anchor set and checkpoint (R, `experiments/safety_selection/attribution.py:8-9, 57-63`), and one float64 row gradient at 32B is about 4.3 GB (I: 536,870,912 × 8 bytes). The bi-anchored A1 also needs a safe-anchor set built from the untuned 32B's own answers (R, attribution.py:57-63), which is one more generation pass. So the 32B contrast must come from the scorer-free arms: P4 (S1 − a0, add 48 random PKU refusal rows), P3 (H1 − R, remove the 600 shortest answers; it also needs R arms) or P6 (S4 − S1; it needs a generation pass on the untuned 32B) (R, F:241).
- **What each scorer-free contrast can say (I).** P4 and P6 are add repairs with no diagnosis. P3 is the only scorer-free removal contrast, and its H1 is a length rule, not training-data attribution. So no affordable 32B contrast tests attribution itself. The 32B can show (a) whether the erosion stays partial at 32B (Gate A) and (b) whether one repair's direction and rough size carry over. The paper must say this plainly.
- **Units per contrast (I).** P4 reuses the 3 Gate A fine-tunes as its a0 arm, so it adds 3 units. P3 adds H1 × 3 and R × 3 (6 units). P6 adds S1 × 3 and S4 × 3 (6 units) and the S4 list's generation pass.
- **Power (E).** At 3 seeds per arm and a paired SD of 2–4 pp, a 95% interval half-width is about 5–10 pp (t with 2 df). So T2 resolves only a large effect. It is a direction-and-size check, **report-only**. T3 (6 seeds) gives about the 7–8B power (RP §2.2: MDE about 11–12 pp unpaired).
- **Option fit.** **[B]** the 32B continues OLMo's ladder (1B → 7B → 32B); this is the only option where the RP puts it (R, RP:128). **[C-OLMo]** the ladder fits the same way, but the RP does not fund a 32B under C; adding it there is decision D13. **[C-Llama]** the 32B is off-family: it has no full 7–8B comparison in its own family, so only T1 makes sense there, if anything.

## 2. Candidate models

| Model | Family fit | Licence, gating | Architecture | LoRA r64 values (7 targets) | Verdict |
|---|---|---|---|---|---|
| `allenai/OLMo-2-0325-32B-Instruct` | Same family as OLMo-2-0425-1B and 1124-7B; final post-training stage, fine-tuned from `-DPO` (R, model card) | Apache-2.0; no gating notice; the card notes that the post-training mix has third-party outputs under the Gemma Terms of Use (R, https://huggingface.co/allenai/OLMo-2-0325-32B-Instruct) | 64 layers, d 5,120, 40/8 heads (GQA), context 4,096 (R, OLMo 2 paper Table 3, https://arxiv.org/html/2501.00656). FFN 27,648 (U; the 32B total forces about 27,600, I). Untied head (U) | 64 × 64 × (2·10,240 + 2·6,144 + 3·32,768) = **536,870,912** (I, formula checked against the 7B, 8B and 13B recipe counts) | **Recommended** |
| `allenai/Olmo-3.1-32B-Instruct` | Next generation (Olmo 3), not OLMo-2 | Open (R, search result https://huggingface.co/allenai/olmo-3.1-32b-instruct) | Its card asks for transformers ≥ 4.57.0 (R); the pinned lock has transformers 4.56.2 (M, `experiments/minimal_safety/requirements.lock`) | — | Not recommended: new environment and a different family |
| `allenai/OLMo-2-1124-13B-Instruct` | Same family | Apache-2.0 (R, F:355) | 40 layers, d 5,120, MHA (R, Table 3) | 250,347,520 (M, its config) | **Cheap alternative** on the A100: configs, ladder and weight pins exist (M, `runkit/family-probe/probes.py` "olmo2-13b"); it never ran (M: no 13B kit in tmp/) |
| `meta-llama/Llama-3.1-70B-Instruct` | Same release as Llama-3.1-8B | Llama 3.1 Community License; gated (agree to share contact details) (R, https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct) | 80 layers, d 8,192, FFN 28,672, 64/8 heads (R, Llama 3 paper Table 3, https://arxiv.org/html/2407.21783); 70.55B values (I) | 80 × 10,354,688 = **828,375,040** (I) | Only if 70B is kept |
| `meta-llama/Llama-3.3-70B-Instruct` | Newer post-training (Dec 2024), not the 8B's release | Llama 3.3 Community License; gated (R, https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct) | Same architecture as 3.1-70B (R: card names 3.1-70B as base) | 828,375,040 (I) | Not recommended (breaks the 8B → 70B pairing) |

**Notes.**
- Access to each gated Meta repo is a separate request (U whether the user's 3.1-8B access covers 70B). Only the user can make that request.
- **The OLMo template differs.** The 1B tokenizer's chat template starts with `{{ bos_token }}` (BOS = `<|endoftext|>`; pad `<|pad|>`) (M, local HF cache `models--allenai--OLMo-2-0425-1B-Instruct/…/tokenizer_config.json`). The 32B card says its template has **no** leading BOS, unlike the other OLMo-2 models (R, model card). The 7B and 13B recipes pin the 1B snapshot as their tokenizer (M, configs `model.tokenizer`), because "OLMo-2 1B, 7B and 13B share identical tokenizer files" (R, F:363). That precedent does not hold for the 32B (I). Decision D3.
- **BOS evidence that already exists (M).** The family preflight records, as a report only, greedy 64-token answers and end-of-turn log-probabilities with and without the leading BOS whenever prompts start with BOS (`scripts/cuda_preflight_family.py:478-489`). At OLMo-2-7B (whose own template has the BOS) 2 of 3 greedy prefixes were the same (M, the 7B seed-1103 `verification.json`, `bos_record.greedy_same_64` = 2). So the BOS changes some outputs even for a model trained with it. Pinning the 1B template feeds the 32B a token that its card says its template does not use (R, model card), so the untuned 32B baseline may shift. This makes D3 a choice about the experimental model's input, for GPT or the user, and the smoke test's `bos_record` is useful engineering evidence for it (no harm score is read).
- Sequence limits fit the 4,096 context: training ≤ 3,072 tokens; generation ≤ 1,536 + 2,048 = 3,584 (M, recipe `max_train_tokens`, `max_prompt_tokens`, `max_new_tokens`).

## 3. Engine and environment facts that decide the design

| Fact | Label, source |
|---|---|
| Exactly one visible GPU: `configure_cuda` raises if `device_count() != 1`; kits export `CUDA_VISIBLE_DEVICES=0`; the bootstrap asserts one device | M, `experiments/minimal_safety/model.py:386-389`; `runkit/gate-b-olmo/setup/bootstrap_hr.sh:35` |
| Base must be bfloat16, LoRA float32; no 4-bit path; no bitsandbytes, DeepSpeed or vLLM in the lock | M, `experiments/safety_selection/config.py:503-504`; `loaders.py:164-165, 180-183`; `requirements.lock` |
| Gradient checkpointing is a recipe switch (`use_reentrant=False`); CPU-tested on tiny Olmo2 (MHA) and Llama (GQA) models | M, `loaders.py:184-186`; `tests/test_ss_family_models.py:78` |
| No gradient-checkpointed run has run on a GPU in this project (every 7–8B ladder stopped at mb2) | M, no `verification.json` under tmp/ has gradient checkpointing on (re-checked in review: 659 parsed as reports, 0 with it on) |
| The Adam state stays on the GPU during evaluation; the 4.0B guard (Qwen3Guard-Gen-4B) loads on the same GPU before generation | M, LEDG 7B: allocated 15.45 GiB after training, 22.98 GiB after `load_guard` |
| Generation: HF loop with a KV cache, left padding, one synchronising argmax (or per-row sampler) per step | M, `engine.py:487-564` |
| Engine identity 472fc7f6… hashes 29 `.py` files only (no configs, no tests) | M, `configs/engine-identity-472fc7f6.json`; VER 7B `source.files` lists 29 |
| Environment: torch 2.8.0 (cu128 wheels), transformers 4.56.2, peft 0.17.1; image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` | M, `requirements.lock`; `bootstrap_hr.sh:21`; `runkit/gate-b-olmo/host.py:55` |
| Kits hard-code `GPU = "NVIDIA A100-SXM4-80GB"`, `cloudType "SECURE"`, not interruptible | M, `runkit/family-probe/host.py:50, 198`; `orchestrate.py:44` |
| Create refuses a price above $10.00/h; the guard plans a new pod at **$1.85/h**; a running pod with no known cap counts at 15 h; the guard reads caps only from `tmp/family-probe-*` and `tmp/gate-b-olmo*` | M, `runkit/gate-b-olmo/gateb_rules.py:47-48`; `budget.py:24-25, 39, 79-90`; R, F:134 |
| The Gate B kit packs `scripts/cuda_preflight_{family,killtest,headroom_v3,headroom}.py` | M, `runkit/gate-b-olmo/pack_setup.py:48-49` |
| A Gate B pack also bundles **every** `.py`, `.json`, `.md` and `.lock` file under `experiments/minimal_safety/` and `experiments/safety_selection/` (configs and tests included), and refuses if `git status --porcelain -- experiments scripts` is not empty. The stage `gateb` is already packed (`tmp/gate-b-olmo/setup/packed-gateb/`) and the pack refuses to overwrite, so only a recovery re-pack is exposed | M, PACK:195-200, 220-223; `ls tmp/gate-b-olmo/setup/` |
| The family-probe kit runs the a0 arm only: one seed per host, with the untuned unit on the first host (`base_eval`) | M, `runkit/family-probe/plan_tool.py:53, 108`; `tmp/family-probe-sp-olmo2-7b-b-{a0,seed1102}/plan.json` (one host each) |
| Greedy answers depend on the generation batch: at OLMo-2-7B the preflight found `greedy_batch_equals_single` false (sampled answers: true) | M, 7B seed-1103 `verification.json` `verdict` |
| Host memory is not the limit: at 7B the policy load's peak RSS was 6.07 GiB while 14.19 GiB of weights sat on the GPU; a RunPod H200 pod lists 276 GB RAM and 24 vCPUs | M, LEDG 7B `load_policy`; R, https://www.runpod.io/pricing (read 16 Oct 2026) |

**Consequences (I).**
- 70B cannot run on one H200 in bf16. Multi-GPU and QLoRA are engine changes (above rows). QLoRA would also change the model under study (a quantized base), so it is a scientific choice for GPT, not a memory setting.
- A 2 × H200 pod costs $10.58/h (E, 2 × $5.29). The $10/h create limit blocks it.
- H200 (Hopper) runs CUDA 12.8 wheels (I). B200 is supported by cu128 wheels (I). **B300 (Blackwell Ultra) with torch 2.8 cu128 is U.** If it fails, 70B needs a new environment lock.
- Any change to the four preflight scripts above changes what a Gate B re-pack ships, so T4 forbids it. A 32B kit that needs a different preflight rule needs a **new** script file.
- **New files are not free either.** A new recipe config or test under `experiments/safety_selection/` is outside the engine identity, but a Gate B recovery re-pack would ship it (and an uncommitted one blocks the pack, T3). T4's letter does not name such a file. Recommended: nothing for the 32B goes into the repo's `experiments/` or `scripts/` before Gate B's last kit pod (D15, with CAP's KD8). A new folder under `runkit/` or `tmp/` is not checked or bundled by the pack.
- Generation batch is part of the measurement, not only a speed setting (row above). Batch 64 (D5) or the 13B fallback's batch 16 (D10) gives other greedy answers than batch 32 would.

## 4. Memory ladder

**Basis (M).** Peak memory per stage from LEDG and VER:

| Model (A100 80 GB, usable 79.25 GiB, M VER) | Weights + LoRA at load | Training activations at the longest micro-batch (peak − allocated) | Per token per layer | KV cache at batch 32, 2,048 new tokens |
|---|---|---|---|---|
| OLMo-2-1B, mb4 × 2,114 tokens, 16 layers | 2.95 GiB | 24.77 GiB | 197 KB | 9.5 GiB (MHA) |
| OLMo-2-7B, mb2 × 2,114, 32 layers | 14.19 GiB | 40.91 GiB | 325 KB | 37.6 GiB (MHA; 204 allocator retries, reserved 78.69 GiB) |
| Llama-3.1-8B, mb2 × 2,138, 32 layers | 15.59 GiB | 41.54 GiB | 326 KB | 9.5 GiB (GQA) |
| Qwen2.5-7B, mb2 × 2,137, 28 layers | 14.83 GiB | 39.66 GiB | 356 KB | 4.2 GiB (GQA) |
| mb4 at 7–8B (first ladder candidate) | — | failed at about 77–78 GiB | — | — |

**Activation model (E).** Bytes per token per layer ≈ α·hidden + β·FFN. The OLMo pair (1B, 7B) gives α 45, β 12.7. The GQA pair (Llama-8B, Qwen-7B) gives α 41, β 11.0. Each pair fixes its two values exactly (no degrees of freedom left), so the only check is that the two fits differ by about 13% at 32B, and both extrapolate past the largest measured FFN size (18,944). OLMo-2-32B: **515–585 KB** per token per layer. Llama-70B: **about 652 KB**. With gradient checkpointing: each layer's bf16 input (2·hidden bytes per token) + one layer's full activations + about 1 GiB for the lm_head chunk (`lm_head_chunk_tokens` 1,024) + 0.5 GiB. The KV formula (2 × layers × kv_heads × 128 × 2 bytes per token) matches the measured 7B and 8B peaks within 2% (M check).

**Static terms (I, from the parameter counts).** OLMo-2-32B: weights 60.04 GiB; LoRA 2.00; Adam 4.00; gradients 2.00; guard 7.49. Llama-70B: 131.42; 3.09; 6.17; 3.09; 7.49.

**Usable memory (E).** A100 79.25 GiB (M). H200 about 140 GiB, B200 about 178 GiB (read from the 141 GB and 180 GB listings, as the A100's "80 GB" reads 79.25 GiB). B300 about 268–279 GiB (U). RTX PRO 6000 about 94.5 GiB, H100 NVL about 93 GiB (E). **Rule proposed:** a setting passes only at peak reserved ≤ 90% of the device.

### 4.1 OLMo-2-32B (peaks in GiB, E)

| Setting | Training peak | Evaluation peak (Adam + guard + KV) | H200 (≈140) | B200 (≈178) | 94–96 GB cards | 80 GB cards |
|---|---|---|---|---|---|---|
| mb1, no checkpointing | 134–143 | — | **no** | yes, but needless | no | no |
| mb2 or more, no checkpointing | 200+ | — | no | no | no | no |
| mb1 + checkpointing | 72.0 | — | yes | yes | yes | no (≤ 9% margin) |
| mb2 + checkpointing | 74.4 | — | yes | yes | yes | no |
| **mb4 + checkpointing (recommended)** | **79.3** | — | **yes (43% margin)** | yes | yes | no |
| generation batch 16 | — | 83.4 | yes | yes | marginal (≈11%) | no |
| **generation batch 32 (recipe B)** | — | **92.6** | **yes (34% margin)** | yes | **no** (≤ 2%) | no |
| generation batch 64 | — | 111.1 | yes (21%) | yes | no | no |

**Recommended 32B ladder (preflight takes the first passing candidate):** `mb4-gc`, then `mb2-gc`, then `mb2-gc-eager`; generation batch 32 in all. Why mb4: training is also overhead-bound at 7–8B (about 11.5 ms per layer per micro-batch on all measured models, M: 886 s / 2,400 micro-batches / 32 layers at 7B; I). So fewer micro-batches train faster: mb4 ≈ 20–25 min, mb2 ≈ 38 min, mb1 ≈ 77 min at 32B (E). Effective batch stays 128 (4 × 32, as at 1B). The micro-batch split does not change the step objective (R, `engine.py:6-11`).

### 4.2 Llama-3.1-70B (peaks in GiB, E)

| Setting | Training peak | Evaluation peak | H200 (≈140) | B200 (≈178) | B300 (≈268–279) |
|---|---|---|---|---|---|
| static weights + LoRA + Adam | 143.8 (training) | 148.2 (evaluation) | **no** (static alone is over) | — | — |
| mb1, no checkpointing | 249 | — | no | no | marginal (at the 90% line) |
| mb1 / mb2 / mb4 + checkpointing | 149.4 / 153.3 / 161.1 | — | no | yes / yes / no | yes |
| generation batch 8 / 16 / 32 | — | 154.5 / 160.3 / 172.0 | no | yes / marginal / **no** | yes / yes / **yes** |

So 70B needs a **B300** to keep generation batch 32. A B200 forces batch ≤ 16, which doubles the generation batches.

## 5. Time: measured scaling and estimates

**Measured stage times (M, LEDG, one train + e1 job on an A100):**

| Stage | OLMo-2-1B (recipe G, mb4) | OLMo-2-7B (B, mb2) | Llama-3.1-8B (B 5e-5, mb2) |
|---|---|---|---|
| Training, 38 steps | 4.1 min | 14.8 min | 14.5 min |
| Greedy generation, 468 prompts | 30.1 min | 56.8 min | 58.3 min |
| Sampling, 600 answers | 12.8 min | 13.3 min | 43.3 min |
| Guard, harm scores, ARC, query loss | about 5 min | about 5 min | about 6 min |
| Job (outer), fine-tune only | 34–74 min (RP) | 86.1–107.5 min, 8 pods (M, `finished.json`) | 105.2–141.1 min, 7 pods |
| Job (outer), a0 pod that also ran the untuned unit | — | 114.6 min | 174.2 min |

**Real decode step in capped 32-row batches (M, PROG; median of capped batches ÷ 2,048 steps; re-computed in review):** OLMo-1B 59.3 ms (16 layers), OLMo-7B 116.0 ms (32), Llama-8B 120.3 ms (32), Qwen-7B 104.2 ms (28). That is **3.6–3.8 ms per layer** in every case, whatever the hidden size (2,048–4,096) or attention type. So decoding is bound by per-layer launch and Python overhead, not by GPU bandwidth (I; the bandwidth floor is about 10× lower). The preflight's full-length check over-states OLMo-7B (269 ms, with 204 allocator retries at the memory ceiling) and under-states Llama (104 ms) (M, VER; CAP §2 found the same).

**Steps per evaluation (M, PROG):** capped batches of 34: OLMo-7B 13, OLMo-1B 14, Llama-8B 21. In step-equivalents: about 36k (OLMo-7B), 43k (OLMo-1B), 51k (Llama-8B) of a 69.7k maximum (34 × 2,049).

**Estimates (E).**

| Item | OLMo-2-32B on H200 | Llama-70B on B300 | Basis |
|---|---|---|---|
| Decode step, batch 32 | 0.24 s (0.23–0.30) | 0.30 s (0.27–0.38) | 3.6–3.8 ms × 64 or 80 layers; the GPU part per layer is about 0.2–0.4 ms, hidden under the overhead; host CPU speed ±25% (U) |
| Generation per evaluation | 2.6 h (2.2–3.4); all-capped worst 4.6–5.8 h | 3.6 h (3.0–4.6); worst 5.8–7.4 h | step-equivalents above × step time; OLMo-like 36–43k for 32B, Llama-like 51k for 70B |
| Training (e1, 38 steps) | 0.4 h (0.33–0.75) | 0.5 h (0.35–1.0) | overhead-bound per layer-micro-batch × 1.5 for checkpointing, or compute at 30–40% of peak, whichever is larger |
| Other evaluation stages | 0.15 h | 0.15 h | guard is the same 4B model at all sizes (M: 266 s at 7B) |
| **Train + e1 job** | **3.2 h (2.7–4.4)** | **4.35 h (3.55–5.75)** | sum |
| Evaluation-only unit (untuned) | 2.75 h (2.35–3.65) | 3.75 h (3.15–4.9) | |
| Pod setup (bootstrap, 72 / 149 GB download and hash, preflight) | 1.0 h (0.75–1.3) | 1.25 h (1.0–1.5) | 7–8B setup 20–38 min (RP §2.1) + larger downloads + a slower full-length check |

**Ratio to 7–8B (E):** a 32B job is about 2.0× an OLMo-7B job; a 70B job about 2.1× a Llama-8B job. Generation is about 80% of a 32B job. Generation batch 64 would cut 32B generation by about 25–40% (E: half the batches, but more of them reach the cap), at the cost of an evaluation setting that differs from recipe B and gives other greedy answers (§3; decision D5).

**The untuned unit is probably over-costed (I).** At 7–8B the a0 pods that also ran the untuned unit took about 24 min (OLMo) and 50–69 min (Llama) more than a fine-tune-only pod (rows above), against about 75 min (OLMo) and 108 min (Llama) for an e1 evaluation (M, LEDG stage sums). Untuned answers end sooner. So the 2.75 h for the untuned 32B unit is a conservative upper; it may be about 1–1.5 h. That would lower T1 by about $8–11; the tiers keep the conservative figure.

## 6. Prices, caps and the $10/h limit

**Prices (E; R, https://www.runpod.io/pricing, page marked "Updated October 8, 2026", read 16 Oct 2026 about 21:35 UTC; no API price read).** On-demand, per GPU-hour:

| GPU | Memory | Secure | Community | Under $10/h? |
|---|---|---|---|---|
| A100 SXM | 80 GB | $1.79 (matches every pod since 9 Oct, M RP §2.1) | $1.39 | yes |
| H100 NVL | 94 GB | $3.19 | $2.59 | yes |
| RTX PRO 6000 | 96 GB | $2.49 | $1.69 | yes |
| **H200** | **141 GB** | **$5.29** | $3.59 | **yes** |
| B200 | 180 GB | $7.99 | $5.98 | yes |
| **B300** | **288 GB** | **$8.99** | $6.94 | **yes, by $1.01/h** |

Storage (R, same page): pod volume $0.10/GB-month running, $0.20 idle; container disk $0.10. A 32B pod with 160 GB volume costs about $1.05 per idle day (E), so delete it soon after the verified backup.

**Why the cheaper cards lose (E).** A 94–96 GB card must run generation at batch 16 (§4.1). Decoding is overhead-bound, so batch 16 roughly doubles generation time. At $2.49–3.19/h × about 2× the hours, it costs about as much as the H200, with a 10% memory margin.

**Caps and the guard (I, from §3 rows and CAP).**
- The family-probe cap gate counts two fully capped evaluations per job (R, `scripts/cuda_preflight_family.py:174`). At 0.24–0.30 s per step that is 10–12 h for one 32B job, against about 3.2 h real.
- The guard plans other kits' create-intents at $1.85/h (M, `budget.py:79-90`). A 32B intent priced at $1.85 is under-counted by Gate B's guard. The window is narrow, because one shared lock serializes every launch from check to create and a created pod then counts at its real price (M, budget.py docstring and `lock()`); it stays open only after a failed or unanswered create. Still, a 32B launch should never overlap a Gate B launch window.
- **Proposed 32B kit rules (the 32B parameter set only):** a create ceiling of **$6.00/h** for H200 (stricter than the user's $10/h) and the same $6.00/h as the kit's planning price. Caps from a measured upper bound (the CAP "M-cap" rule, applied to 32B rates after the smoke test), with one evaluation for fine-tune-only jobs.
- **Guard need per pod (E):** smoke pod cap 2.0 h → $12 + $6 reserve = $18. A one-fine-tune pod (family-probe copy): about 12–15 h cap under the present rule (setup and preflight 1.0–1.3 h + two fully capped evaluations 9.6–11.9 h + training, overhead and margins + 30 min) = **$78–96**. A 2-unit pod (stage-1 kit): about 25 h ($156) under the present rule, or about 14 h ($90) under a measured rule.
- **Parallel pods add up (I, from budget.py's rule).** The guard counts every running pod at its remaining cap. Three one-fine-tune 32B pods launched together need about **$230–290** of free balance at the third launch, against about $100 of spend. The same headroom is then not free for a 7–8B launch until the 32B pods stop. Two ways out: launch the 32B pods one after another (T1 then takes about 15–20 h of calendar time instead of about 7 h, E: pods of about 7, 4 and 4 h plus gaps), or use the measured cap rule with one evaluation per fine-tune-only job (about 5–6 h caps, about $35–40 per pod, E).

**Cost tiers (E; hours from §5; Secure prices; +20% allowance (RP §2.1); smoke test added).**

| Tier | Units (pods) | GPU-hours | GPU cost | With 20% + smoke |
|---|---|---|---|---|
| 32B smoke only | preflight, 1 pod | 1.0–1.5 | $5–8 (cap upper $10.58) | — |
| **32B T1: Gate A** | untuned + 3 seeds (2; stage-1 kit, 2 units per pod) | 14.4 (12.0–19.5) | $76 ($63–103) | **$98 ($81–131)** |
| 32B T1 on a family-probe copy | untuned + 3 seeds (3; one fine-tune per pod) | 15.4 (12.7–20.8) | $81 ($67–110) | $104 ($86–140) |
| **32B T2: T1 + S1 × 3 seeds** | 7 (3) | 25.0 (20.8–34.0) | $132 ($110–180) | **$165 ($137–223)** |
| 32B T3: T1 + 3 a0 + 6 S1 | 13 (5) | 46.2 (38.5–63.0) | $244 ($204–333) | $300 ($250–408) |
| 32B T2 with P3 (H1 − R) instead of P4 | T1 + 3 H1 + 3 R = 10 (4) | about 35.6 | about $188 | about $230 |
| 32B T2 with P6 (S4 − S1) instead of P4 | T1 + 3 S1 + 3 S4 = 10 (4), + the S4 list's generation pass (up to about 2 h) | about 37 | about $196 | about $245 |
| 32B T2 on Community H200 | 7 (3) | 25.0 | $90 | about $112 |
| 70B T1 on B300 | untuned + 3 seeds (2) | 19.3 (15.8–25.1) | $174 ($142–226) | $225 ($184–291) |
| 70B T2 on B300 | 7 (3) | 33.6 (27.4–43.9) | $302 ($247–395) | $379 ($310–493) |
| Alternative: OLMo-2-13B Gate A on A100 | 4 (2) | about 14–18 | about $25–32 | about $35–45 (E: 13B probe cap basis, `probes.py` docstring; generation batch 16) |

The RP §6 line "+$110–230 if an H200 bills $3–4/h (U)" becomes about **+$100–300 at the Secure H200 price (E)**. The dossier's "32B check $800" line (R, `research/grant/2026-10-05-grant-evidence-dossier.md:250`) would cover T3 with room, but it is a line in the "Recommended about $14k" ask (R, dossier:245), not money in hand: no grant is awarded (R, RP:13).

## 7. Smoke test at minimal cost

**Stage S0 on the Mac ($0; needs the user's approval for each Hugging Face access; no weights).**
1. Pin the revision (40-hex) of `allenai/OLMo-2-0325-32B-Instruct` and read the SHA-256 of every `.safetensors` file from the Hub's file metadata (as the 13B pins were made; M, `probes.py` "olmo2-13b").
2. Fetch `config.json` and the tokenizer files only. Run `scripts/family_lora_count.py` (meta device, no weights; outside the engine identity) to confirm 536,870,912. Confirm FFN size, the untied head and the pad token.
3. Run `scripts/family_codec_check.py` on the 32B tokenizer and on the 1B tokenizer. Report whether `tokenizer.json`, `vocab.json` and `merges.txt` are byte-identical and how the templates differ. This is evidence for D3; GPT or the user decides it (§10).
4. Write the new recipe configs (§8) and a tiny CPU test for an Olmo2 model with GQA and checkpointing (the present test has MHA only; M, `tests/test_ss_family_models.py:24-28`). Before Gate B's last kit pod, write them only under `tmp/gi-vi-parallel/` and run the test from there, never from the repo's `experiments/` (§3, T3/T4).
5. If D3 picks the 32B's own template: prepare a new prepared set with the same rows, audited token for token.

**Stage S1 on one H200 pod (Secure; cap 2.0 h; upper $10.58; expected $5–8).**
- Use the present kit mechanics: the cap gate refuses a job whose projected upper does not fit and then stops the pod (R, `runkit/family-probe/orchestrate.py:13-14`; the 8 Oct Llama attempt 3 stopped this way, R, F:211). So a 2.0 h cap gives a preflight-only run with no new code path.
- It measures, for the ladder (`mb4-gc`, `mb2-gc`, `mb2-gc-eager`): memory-preflight peak per candidate; the resume check (3 engineering steps; bitwise exact); the generation and sampling batch checks; the full-length check at batch 32 (ms per step, allocator retries, peak); the 80-prompt timed sample; the guard; peak host RAM; download and hash time; GPU name and total memory; the lock hash; the existing `bos_record` (a report, if D3 keeps the BOS template).
- **Pass:** a candidate passes with training peak reserved ≤ 90% of the device; the full-length check has zero allocator retries and peak reserved ≤ 90%; resume exact; both batch checks pass; LoRA count equals the recipe's; the tokenizer audit passes for the D3 rule; the lock hash equals the frozen lock's; peak host RAM ≤ 50% of the pod's RAM; measured step ≤ 0.35 s; the measured rates project T1 at ≤ its upper for the kit used (19.5 H200-hours with 2-unit pods, 20.8 with one fine-tune per pod).
- **Fail actions:** memory → next ladder rung, else no-go; step > 0.35 s → re-cost and ask; non-exact resume or a determinism error on Hopper attention → try the eager rung once, else no-go.
- **When:** after Gate B's last kit pod, from new money only. (The side-kit precedent, F:121, also allowed a slot before a Gate B launch; but the smoke pod's bundle needs the 32B recipe configs, which belong under the repo's `experiments/` and should wait for Gate B's last kit pod, §3 and D15; so in practice the smoke test comes after it.) Best before 1 Dec, so the go/no-go uses measured numbers. It is **[B]** spend (or [C-OLMo] under D13); under C as the RP defines it, skip it.
- **If the smoke test shows that an engine change is needed:** drop the 32B for ICML rather than open a second engine round in December (agrees with Y, decision 10).
- **70B smoke (only if D9 keeps 70B):** one B300 pod, cap 2.5 h, upper $22.48, expected $13–20. It adds a check that torch 2.8 cu128 runs on the B300 at all (U).

## 8. What code and files change (T4 check)

**Engine round Y: not needed for OLMo-2-32B (I).** All needed paths exist: one-GPU bf16 + float32 LoRA, checkpointing, sdpa or eager, the Olmo2 class with GQA (transformers 4.56.2 supports `num_key_value_heads`; the GQA path is CPU-tested on Llama, M). The RP's "any 32B/70B engine change after that pod" then applies only to 70B options below.

**Where files go, and when (review fix).** Before Gate B's last kit pod: drafts only under `tmp/gi-vi-parallel/icml-78b-prep/` (this folder). Recommended: nothing new in the repo's `experiments/` or `scripts/`, because a Gate B recovery re-pack would bundle a committed file and refuse an uncommitted one (§3; STB:64). T4's letter (STB:65) does not forbid a committed addition; D15 settles it together with CAP's KD8. After Gate B's last kit pod: the lead integrates the files below by explicit-path commits.

**New files (integrated only after Gate B's last kit pod):**
- Recipe configs, new names only, for example `experiments/safety_selection/configs/study-kt-olmo2-32b-r64-b-{mb4-gc,mb2-gc,mb2-gc-eager}-<date>.json`: recipe B with the 32B model, revision, `expected_trainable_parameters` 536,870,912, `gradient_checkpointing` true, generation batch 32, the D3 tokenizer rule. They are outside the engine identity (M, §3) but inside a Gate B pack's file set (M, PACK:220-223).
- **Kit (D14).** Recommended: no second kit. Add the 32B as a parameter set of the kit shell that the 7–8B blocks use (CAP KD10; route (ii) is the B15 stage-1 kit, which must run removal and add arms anyway, with CAP's cap rule from `runkit/stage1-78b/rules_78b.py`): GPU id, create ceiling and planning price $6.00, a probe entry "olmo2-32b" (repo, revision, pins, ladder, `container_disk_gb` 100, `volume_gb` 160, `preflight_wait_s` 5,400) and the measured cap rule. One kit is one review. (CAP found that a Gate B kit fork lacks a "train + evaluate a0" job kind, R, CAP:19, so that fork is not the base either.) Fallback, for T1 only: `runkit/family-probe-xl/`, a copy of `runkit/family-probe/` with the same changes (a0 only, one seed per pod; §3). In both, `GPU = "NVIDIA H200"` in the host, orchestrator and bootstrap checks (the exact RunPod GPU id is U; read it from the create path, not a price API).
- Working copies named `tmp/family-probe-…-olmo2-32b-{smoke,gatea}-…/` (or the CAP design's `tmp/family-probe-s1-…` pattern). The `family-probe-` prefix keeps them inside the shared guard's glob (M, `budget.py:39`), so their caps are seen.
- A new preflight script only if the 90% margin rule or the one-evaluation cap needs code: `scripts/cuda_preflight_xl.py` (new file). Never edit `scripts/cuda_preflight_{family,killtest,headroom_v3,headroom}.py`.
- A new CPU test file, for example `experiments/safety_selection/tests/test_ss_xl_models.py` (tests are outside the engine identity, but inside a Gate B pack's file set).
- A 32B pre-registration addendum (new document) and, if D3 picks the native template, a new prepared set under `tmp/kt-prepared/`.

**Untouched (confirmed for this design):** every engine `.py` file in the 472fc7f6 identity; `scripts/gate_b_reading.py`, `make_anchor_answers.py`, `gate_c_representation.py`, `gate_c_classifier.py`, `make_gateb_recipe.py`; `configs/evaluation-equivalence-gateb-20261008.json`; everything in `runkit/gate-b-olmo/` and `tmp/gate-b-olmo/`; the four packed preflight scripts; PRE revision 5; the sealed rankings; the environment lock; every existing config; and, until Gate B's last kit pod (recommended, D15), the whole of `experiments/` and `scripts/` (no new file either). This design and its review wrote only this file.

**70B only (if kept).** On a B300: no engine change, if the environment runs (U). On a B200: generation batch ≤ 16 (a recipe deviation) or an engine round-Y change that frees the Adam state and loads the guard after generation. On H200s: multi-GPU (changes `configure_cuda`, the loaders and the kits; blocked by $10/h for 2 × H200) or QLoRA (new dependency, config and loader changes, and a different experimental model). I do not recommend any of these for ICML.

## 9. Schedule and the 1 Dec go/no-go

**Order (dates are latest, E):**
1. Now → Gate B's last kit pod: $0 only. This design; S0 steps 1–3 after approval; draft the configs, kit and addendum outside the repo.
2. After Gate B's last kit pod and the first new money: build and review the 32B kit; run the smoke test (about $5–8).
3. **1 Dec: go/no-go** (below).
4. 7 Dec (RP §5): start the 32B T1 (2 pods on the stage-1 kit or 3 on a family-probe copy; about 7–10 calendar hours in parallel, or about 15–20 h one after another if guard headroom is short, §6). Then T2's S1 pod if the in-run rule allows. Finish by about 20 Dec, before the 4 Jan freeze. H200 pods do not compete with the 7–8B blocks for A100 supply; they compete for money, guard headroom, the shared launch lock and the operator's time.

**GO for T1 only if every point holds on 1 Dec (proposed):**
1. **Money.** New money only. Free balance after (a) every running or planned pod's committed upper, (b) the remaining 7–8B blocks, (c) the confirmation set-aside ($140–230 [B]; $70–120 [C]) and (d) 30 days of idle storage covers the tier: T1 ≥ about $100–105 (T2 about $165, T3 about $300). Each launch must also pass the guard (about $78–96 per one-fine-tune pod or $90–160 per 2-unit pod, §6), and the pods running in parallel must not leave the next planned 7–8B launch short of its own guard need. The 32B never uses Gate B's reserved need or 7–8B money (it is first in RP's cut order, RP:138).
2. **Smoke test passed** on the same GPU type and cloud type as the run (§7 pass list).
3. **Option.** B. C-OLMo only if the user extends the RP to it (D13). Under C-Llama: T1 at most, and only if money is plentiful.
4. **Calendar.** 7–8B block A launched and block B funded with its launch date fixed (RP:105-106 put their latest starts at 23 Nov and 3 Dec, so "block B started" cannot be required on 1 Dec); the tier fits before about 20 Dec.
5. **Rules.** Gate B's last kit pod is done (T4); the 32B kit is reviewed READY; the 32B addendum is frozen before the first 32B unit (bars, seeds 1101–1103, LR rule, contrast rule, report-only, one GPU type).
6. **Supply.** H200 Secure on demand at ≤ $6.00/h at launch (the kit refuses otherwise).

**Extra for T2 or T3:** the contrast and its seeds are fixed in the addendum before any 32B unit, and the in-run rule allows it: run the contrast only if 32B Gate A reads E ≥ 10 pp with answers that end (else stop and report Gate A).

**NO-GO** if any point fails. Then: no 32B spend; the paper's largest size is 7–8B and says so; this design waits for a funded extension (the dossier's 32B line; TAIF needs the funder's agreement, RP §6).

## 10. Decisions needed

1. **D1 Scope:** T2 if funded on 1 Dec, else T1 (recommended); T3 only with spare money; or no 32B.
2. **D2 Contrast and its rule (before any 32B unit; a scientific target, so GPT or the user decides):** (a) P4 (S1 − a0; no scorer; cheapest, about $165 at T2; it tests no diagnosis); (b) P3 (H1 − R; the only scorer-free removal contrast; about $230); (c) a rule fixed now: the P3/P4/P6 contrast with the largest standardized 7–8B effect. (c) is valid as "replicate the strongest" because the 32B units are new data (I), but by the RP schedule the 7–8B block A and B reads may not exist before the 32B addendum must freeze (about 5 Dec), so (c) needs a default (P4) if they are late. The worker's lean: (a) with (c)'s default rule, and the paper says the 32B check cannot test attribution. P1, P2, P5 are out at 32B for cost.
3. **D3 Template:** pin the 1B tokenizer and BOS template (the 7B/13B precedent; same token ids as 1B and 7B), or the 32B's own no-BOS template (new prepared set). The model card says the 32B template has no BOS (R), and the BOS changed 1 of 3 greedy prefixes even at 7B (M, §2). This touches what the model sees, so GPT or the user decides. The worker no longer recommends the 1B template by default; if it is kept, the smoke test's `bos_record` is reported with Gate A.
4. **D4 LR at 32B:** OLMo's 1e-4 by the per-family rule, no LR ladder, Gate A reported whatever it reads (recommended).
5. **D5 Settings:** mb4 × 32 with checkpointing and generation batch 32 (recommended), or batch 64 (about 25–40% less generation time; differs from recipe B's evaluation setting and gives other greedy answers, M §3).
6. **D6 Cloud type:** Secure $5.29/h (recommended; every kit uses it) or Community $3.59/h (about −32%; OLMo needs no token on the pod).
7. **D7 Kit price rule:** create ceiling and planning price $6.00/h for the 32B kit (inside the user's $10/h limit).
8. **D8 Smoke test [B]:** approve about $5–8 (cap $10.58) of new money after Gate B's last kit pod, before 1 Dec.
9. **D9 70B:** drop for ICML (recommended). If kept: `Llama-3.1-70B-Instruct` on a B300, a gated access request by the user, and a $13–20 smoke test after the 32B Gate A.
10. **D10 Fallback size:** OLMo-2-13B Gate A on the A100 (about $35–45; same GPU type as all other runs; the 13B probe entry, pins and its generation-batch-16 ladder already exist, M `runkit/family-probe/probes.py:47-58`) if H200s are not affordable or not available. Its batch 16 is a recipe deviation (other greedy answers, §3), and the 13B is a smaller step up from 7B.
11. **D11 Approvals:** the $0 Mac steps that read Hugging Face metadata, `config.json` and tokenizer files (no weights).
12. **D12** The 1 Dec go/no-go rule in §9.
13. **D13 Option home:** the 32B under B only, as the RP has it (RP:128) (recommended), or also under C-OLMo (new; it needs the same money test).
14. **D14 Kit:** the 32B as a parameter set of the kit shell the 7–8B blocks use (CAP KD10, route (ii), the B15 stage-1 kit) (recommended; one kit, removal and add arms, several arms per pod), or a separate `runkit/family-probe-xl/` (T1 only; a second kit to build and review in November).
15. **D15 Repo additions before Gate B's last kit pod:** none (recommended), or committed additions under `experiments/` (T4's letter allows them; a recovery re-pack would carry them). Decide together with the CAP design's KD8.

## 11. Limits and open concerns

- The decode model (overhead-bound, 3.6–3.8 ms per layer) comes from four A100 hosts. H200 and B300 host CPUs may differ by ±25% (U). The smoke test measures it.
- The activation model is two exact two-point fits (OLMo pair, GQA pair) that differ by about 13% at 32B, extrapolated past the measured FFN sizes. No checkpointed run has run on a GPU here (M). The 32B checkpointing peaks are E with about ±20% error; the margins are wide enough for that.
- 32B answer lengths are unknown. They drive generation between about 2.2 and 3.4 h per evaluation (5.8 h worst case).
- H200 and B200 usable memory are E. B300 memory and B300 support in the pinned environment are U.
- H200/B300 on-demand supply on Secure Cloud is U. Prices may change after 8 Oct (E).
- The OLMo-2-32B FFN size, shard count, head tying and pad token are U until S0.
- A 3-seed contrast resolves only large effects; T2 is report-only.
- Smaller choice I did not test: whether the frozen family-probe reading (`scripts/family_probe_reading.py`) accepts a new probe key unchanged (U; it pins only its bars file, M line 76).
- No affordable 32B contrast tests training-data attribution (§1). The 32B check supports a scale statement about erosion and one repair's direction only.
- The kit shell for T2/T3 depends on the CAP design's KD10, which is open. If no stage-1 kit with add arms exists by about 1 Dec, only T1 is possible.
- Builder and reviewer time for the 32B kit work is not costed; it falls in November with stage 1, the 7–8B kits and engine round Y (I).

## Review changes (adversarial review, 2026-10-16 about 22:12 UTC; clock checked with `date -u`)

**Checked and confirmed (no change).** Every F line cited (F:121, 134, 211, 241, 257, 337–348, 355, 363); the code lines (model.py:386-389; bootstrap_hr.sh:21, 35; config.py:503-504; loaders.py:164-165, 180-186; engine.py:6-11, 487-564, 675; test_ss_family_models.py:24-28, 78; gateb_rules.py:47-48; budget.py:24-25, 39, 79-90; pack_setup.py:48-49; cuda_preflight_family.py:174; family-probe host.py:50, orchestrate.py:13-14, 44; family_probe_reading.py:76; dossier:250); the lock (torch 2.8.0, transformers 4.56.2, peft 0.17.1, no bitsandbytes, DeepSpeed or vLLM); every LEDG memory and stage time; the decode medians and capped-batch counts (re-computed from PROG); the 7B full-length check (37.6 GiB above allocated, 204 retries, 269 ms); the mb4 failures at 7–8B (peak allocated 76.9 and 77.2 GiB); no `verification.json` under `tmp/` has gradient checkpointing on (M: 659 parsed as reports, 0 with it on; 4 files did not parse); the LoRA counts (32B, 70B, 13B); the static, activation, KV and peak arithmetic; every cost tier; the model card (Apache-2.0, no gating, no-BOS template, Gemma terms); the OLMo 2 paper's 32B shape; the Olmo 3.1 transformers note; the RunPod prices and "Updated October 8, 2026".

**Changed.**
1. **T3/T4 placement (most important).** The draft allowed new configs and tests under `experiments/` before Gate B's last kit pod "or at least" outside the untouched list. A Gate B re-pack bundles all of `experiments/minimal_safety` and `experiments/safety_selection` and refuses uncommitted files there and in `scripts/` (M, PACK). Now: drafts stay in this folder until Gate B's last kit pod (recommended); T4's letter allows a committed addition, so D15 decides, together with CAP's KD8 (§0, §3, §7, §8).
2. **Kit base.** The family-probe kit runs the a0 arm only, one seed per pod (M). T1 on it needs 3 pods (about $104, not $98), and T2/T3's S1 arms cannot run on it. Now: the 32B is a parameter set of the kit shell the 7–8B blocks use (CAP KD10), D14 (§0, §3, §6, §8).
3. **Option fit.** The RP funds the 32B under B only (RP:128). The draft's C-OLMo home is now marked new and put to the user (D13). The smoke test is marked [B] spend; only the $0 work is shared by B and C (header, §1, §7, §9).
4. **Go/no-go calendar.** "Block B started" on 1 Dec contradicts the RP's 3 Dec latest start. Now: block A launched, block B funded and dated (§9).
5. **Guard headroom.** Parallel 32B pods need about $230–290 of free balance under the present cap rule for about $100 of spend, and they hold it from 7–8B launches. Added to §0, §6 and the go rule.
6. **The contrast.** P4 holds no diagnosis, and no affordable 32B contrast tests attribution. D2 is now framed as a scientific choice for GPT or the user, with costs per contrast (P3 about $230, P6 about $245) and the timing problem of the "largest 7–8B effect" rule (§0, §1, §6, §10).
7. **D3 template.** Added the preflight's existing with/without-BOS record (at 7B the BOS changed 1 of 3 greedy prefixes, M). The worker no longer recommends the 1B template by default (§2, §7, §10).
8. **Generation batch.** Added the measured fact that greedy answers depend on the batch at 7B (M), which strengthens D5 and qualifies the 13B fallback (D10) (§3, §5, §10).
9. **Smaller fixes.** Job-time ranges split into fine-tune-only pods and a0 pods with the untuned unit (the 115 and 174 min uppers are a0 pods); decode medians 116.0 and 104.2 ms; the activation fit described as two exact two-point fits; the untuned 32B unit is probably over-costed (I); host memory checked (7B peak RSS 6.07 GiB, M; H200 pod 276 GB RAM, R) and added to the smoke pass list; A1 at 32B is limited by time, not memory; the T1 pass threshold follows the kit; the dossier's $800 line is an ask, not money; an engine need found by the smoke test drops the 32B (agrees with Y); the F commit note updated (HEAD `1a5189b`, FOCUS unchanged).

**Simpler alternatives weighed.** (a) No 32B, and OLMo-2-13B Gate A on the A100 (D10): cheapest and same GPU type, but a smaller step and a batch-16 deviation. (b) T1 only: answers the scale question reviewers ask most (does the erosion stay partial?) for about $100. (c) One kit for 7–8B and 32B (now recommended, D14). (d) Community Cloud: about −32%, but no pod in this project has used it (kept as D6).

**Not checked.** The OLMo-2-32B FFN size, head tying and shard count (they need the S0 reads, D11); H200 and B300 supply; whether the RunPod H200 GPU id is "NVIDIA H200"; CAP's KD10 outcome.
