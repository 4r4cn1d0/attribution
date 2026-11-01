# Stage-1 pre-registration: what the repository requires for the references, the cost conventions, τ_L, the labels and the S1 build items

Written 2026-10-16 from about 21:25 UTC (17 Oct 02:55 IST; clock checked with `date -u`) by an Opus worker for the main-study lead (General Implementation VI). This is a compilation. It decides nothing.

**Rules I kept.** I read the repository only. I made no edit, commit, push, pod, RunPod call, spend or download. I opened no `rows.jsonl`, `groups.json`, `selector.jsonl`, `hidden/` or held-out file. I read no row, prompt, answer or anchor text. For τ_L I read only numeric fields of the Gate A evaluation records (§3). I read no paper for this file. I did not read any Gate B arm's task loss.

**Labels.** **R** = I read it in the repository (`path:line`). **C** = I computed it here. **I** = my inference or proposal; its basis follows it. **UNVERIFIED** = not checked. Status words: **DECIDED** (a user or lead decision is recorded; who and when follow), **PROPOSED** (a default exists in a record, but nobody decided it), **OPEN** (no record decides it).

**Sources (main checkout, branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD `d79f641`).**

| Short name | File | SHA-256 prefix |
|---|---|---|
| FOCUS | `research/FOCUS.md` (last changed in 416b780; line numbers at this hash) | `23e3da8f893e8135` |
| PLAN-S | `research/review/2026-10-08-sharpened-direction-DRAFT.md` (the stage-1 plan; approved "as drafted as the basis for its pre-registration", FOCUS:236) | `6ff3ff2b15bc4295` |
| RS | `tmp/gi-v-stage1-plan/read-stage1.md` | `6b19b4c2967f2629` |
| SPEC | `tmp/gi-v-steps-4-9/stage1-method-specs.md` | `fceb7e1340932cc8` |
| SCOPE | `tmp/gi-v-steps-4-9/stage1-scope-table.md` | `f850d6a6f343bdde` |
| BRIEF | `.ai/briefs/stage1-commitments-build-20261016.md` (revision 1) | `12cbf46318728d32` |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` (now with §4, commits 7bce3bc and d79f641; FOCUS:75 records the earlier `b8a67719…`; §1–§3, which hold L1–L16, are unchanged) | `1d4e42a2092d2f3e` |
| PLANF | `tmp/gi-v-stage1-plan/PLAN-final.md` | `8e1cb364e21dbddd` |
| PAPER | `writing/paper/2026-10-08-icml-draft.md` (revision 5e; open-decision list) | `9e28e53179bb23a5` |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (Gate B/C, revision 5, frozen) | `5c97cce78cfad2c1` |
| REC | `experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json` (recipe B) | `a47138f2f4fb032a` |
| S | `experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json` (recipe S) | `464708c91cd4c297` |
| NGI | `tmp/gate-b-olmo/gate_b_inputs_noise_gate.json` (names the Gate A units) | `8b484bcf8e2abbeb` |

---

## 0. Short answer

1. **τ_L = 0.0067171 nats** (C). It is 2√2 × s, with s = 0.0023749 nats, the sample SD (ddof 1) of the three Gate A a0 units' mean task loss on all 200 task rows at e1. The 6-against-6 SE is 0.0013711. The files and their SHA-256 are in §3. A re-runnable script and its output are beside this file.
2. **References.** Five are mandatory: the safety prompt (SP), adapter scaling, recipe G, B+Qi and Safe LoRA (FOCUS:151, :243). B+Qi without warmup is DECIDED (FOCUS:125 item (10)). The one-example safety patch is DECIDED as text only (FOCUS:78). Most settings are still OPEN or only PROPOSED: the SP text, the scaling definition, the dominance test, recipe G reuse, B+Qi seeds and loss details, the Safe LoRA base model, projector and rule.
3. **Costs.** The rules exist (PLAN-S:199-205; FOCUS:246). The two conventions are not frozen. Their definitions have gaps (§2).
4. **Labels and seeds.** The primary family, Holm, the SESOI, the τ_O grid, the "worse" label and the seed rule are DECIDED. The label order (E5/U4), the Holm family of the O and task-loss contrasts, and several operational details are OPEN (§4).
5. **RS B10–B17.** None of B10, B11, B12, B14, B15, B16 or B17 is built (grep finds no code). B13 (the selector) is a W1 item inside the current build (§5).
6. **Main concerns (I), detail in §7:**
   - (a) τ_L is small. It is 0.43% of the a0 task loss. Recipe G's one seed sits about 10 τ_L above a0 (FOCUS:230). A 600-row removal may also exceed it. The comparator and the screen rule for τ_L must be fixed before anyone reads a stage-1 or Gate B arm's task loss.
   - (b) C-lean, as written, holds no over-refusal and no task-loss evaluation. The feasibility screen needs both. c0's "20% prompt subset" does not match C-lean's "200 harm prompts × 1 sample".
   - (c) "Below the adapter-scaling curve" has no operational test.
   - (d) The four labels do not form a complete decision table yet.
   - (e) B+Qi needs an engine change. By rule T4 it cannot enter main before Gate B's last kit pod. So the stage-1 freeze waits for that pod.
   - (f) The references run in seed block B only (PLAN-S:223). If block B is not funded, no sentence can say that a data repair beats model-level repair.
   - (g) a0's over-refusal is 11–13 pp below the untuned model's 17%. So τ_O (against the untuned model) binds only near 17%. A repair can be "worse" on O against its comparator and still pass τ_O.

---

## 1. Reference arms

### 1.1 The list and where it comes from

| Reference | First source | Later sources | Status |
|---|---|---|---|
| SP: a fixed safety instruction as a user-turn prefix, at evaluation only | PLAN-S:152 (NOV-9, PLAN-S:57) | FOCUS:243; FOCUS:151; RS A6 (RS:70) | DECIDED as a reference (user, 8 Oct 13:53 UTC, FOCUS:236); text OPEN |
| Adapter scaling: a0's adapter at λ = 0.75 and 0.5; curve λ ∈ {1, 0.75, 0.5, 0} | PLAN-S:111, :153 | FOCUS:243; RS A7 (RS:71) | DECIDED; the test that uses the curve is OPEN |
| Recipe G at 3 seeds: the "recipe-only fix" | PLAN-S:154 | FOCUS:243; FOCUS:158 (role since 9 Oct 09:29 UTC); RS A8 (RS:72) | DECIDED; reuse or re-run OPEN |
| B+Qi: Qi et al.'s constrained SFT on recipe B, 6 seeds, no novelty claim | FOCUS:225 (as "G+Qi", 8 Oct 17:36 UTC) | FOCUS:149 (moved to recipe B, 9 Oct 13:16 UTC); FOCUS:148; FOCUS:125 item (10); RS A9 (RS:73) | DECIDED, including "no warmup" |
| Safe LoRA (Hsu et al., arXiv 2405.16833): the fifth mandatory model-level reference | FOCUS:151-154 (the user, 9 Oct 10:01 UTC) | RS A10 (RS:74); SPEC §6 (SPEC:281-320); PAPER decision 19 (PAPER:195) | DECIDED as a reference; settings OPEN or PROPOSED |
| One-example safety patch ("Safety at One Shot", Zhang et al., ICLR 2026, per RESTART:161; I did not read it) | GPT restart plan, `research/experiments/2026-10-14-main-study-restart-plan-DRAFT.md`:84, :161 (not adopted) | SCOPE:63, :109 ([D5-7]); FOCUS:78 | DECIDED: bounded in text, not built (D5 = (a), FOCUS:78) |
| Curve end points: a0 (λ = 1) and the untuned model (λ = 0) | PLAN-S:111 | — | DECIDED (I: both units exist; §3 names them) |

Related but not mandatory (secondary arms, PLAN-S §5.3): H1 under recipe bt as a loss reference (PLAN-S:66, :163); the random dose curve R_1200 and R_2400 as each filter's "equivalent random dose" (PLAN-S:159). FAQ's main-track list asks for "stronger model-level references" without naming more (FOCUS:74; FOCUS:72).

### 1.2 SP (the safety prompt)

| Item | Source | Status | Text the pre-registration needs |
|---|---|---|---|
| Form: user-turn prefix; evaluation only; on a0 seeds 1101–1103 | PLAN-S:152; FOCUS:243 | DECIDED | Restate it. Say why there is no system turn: OLMo-2 has none (PLAN-S:152, citing EAL:66). |
| The instruction text | RS C1 (RS:113); RS A6 (RS:70) | OPEN. No record chooses a text (my grep of `research/`, `tmp/gi-v-*`, `tmp/gi-vi-*` and `.ai/briefs` finds none) | One published instruction, its source and its SHA-256. Fix it before any SP outcome. Keep the text out of git if it is long; pin it by hash. |
| Joining rule | none | OPEN | The exact separator between the prefix and the user text (I: one blank line). |
| Which banks get the prefix | none | OPEN | (I) Harm prompts and over-refusal prompts get it. State whether ARC and the 200 task-loss rows also get it. The prefix will likely raise O; that is part of the reference's cost. |
| Sampling seed of the 600 sampled answers | engine: each sample is seeded by (job seed, prompt id, sample index), `experiments/safety_selection/config.py`:29-32; `runner.py`:630-632 | OPEN | (I) Use the a0 unit's seed as the job seed, so SP shares a0's sampling streams. PREREG:121 found no common-random-number gain, so do not count on one. |
| Code | RS B10 (RS:100) | not built | The pinned script's name and SHA-256 (see §5). |

### 1.3 Adapter scaling

| Item | Source | Status | Text the pre-registration needs |
|---|---|---|---|
| λ = 0.75 and 0.5 on a0 seeds 1101–1103 | PLAN-S:153; FOCUS:243 | DECIDED | Restate it. |
| What "scaled" means | PLAN-S:153 ("a0's LoRA delta scaled by λ") | OPEN in detail | (I) Multiply the full LoRA update s·B·A (s = α/r = 128/64 = 2, REC lines 21-22) by λ in all 112 adapted matrices (7 modules × 16 blocks). Say that the base weights do not change. |
| The curve λ ∈ {1, 0.75, 0.5, 0} | PLAN-S:111 | DECIDED | (I) λ = 1 reuses the three Gate A a0 units. λ = 0 reuses the one untuned unit (`1101-a0-init-a1`). State both. |
| "Dominates" | PLAN-S:111 ("lower U at equal O and L"); FOCUS:243 ("below the adapter-scaling curve of U against over-refusal and task loss") | OPEN: no operational test | A rule that a script can apply. It must say: how the curve is drawn between the four λ points (I: linear in λ); how a repair is matched to the curve when O and L give different matched points (I: dominate only if U is lower at both matched points); whether the statement needs an interval or is descriptive; and what is reported when a repair's O or L lies outside the curve's range. |
| a0 adapters | FOCUS:94 ("Stage 1's adapter-scaling reference needs a0 adapters"); FOCUS:76-77 (a0-1101's retrain states exist only on the stopped pod w0b-2) | OPEN | The regeneration rule. PLAN-S:155: a deterministic train-only re-run (0.10–0.15 h). (I) Accept a regenerated adapter only if its e1 adapter fingerprint equals the Gate A unit's: 1101 `aad79060c52304ec…`, 1102 `7c9111c2093b00f2…`, 1103 `b1ad020bc8d1b1c1…` (R: each unit's `COMPLETE.json` `checkpoints.e1.adapter_fingerprint`). On the Mac the units hold only a 12 KB `state.json` per checkpoint, not weights (R: `ls`, `du`). FOCUS:77 records that the 1101 retrain on engine X matched both fingerprints. |
| Certification | PLAN-S:155 (λ = 1 and no prefix must reproduce a Gate A U exactly) | DECIDED in principle | Define "exactly" (I: the same Unsafe label on each of the 600 sampled answers, or at least the same count). Say what happens on a failure (I: stop; run no eval-only reference; report). Name the risk that sampling on another pod or GPU may not be bit-identical (I). |

### 1.4 Recipe G (the recipe-only fix)

| Item | Source | Status | Text the pre-registration needs |
|---|---|---|---|
| Role: the "recipe-only" fix and a robustness check; not the main recipe | FOCUS:158 | DECIDED | Restate it. |
| 3 seeds | FOCUS:243; PLAN-S:154 | DECIDED | Restate it. |
| Which runs | RS A8 (RS:72); PLANF:234 item 14 | OPEN | Either reuse the 8 Oct OLMo seeds 1101–1103 (engine e49a978c through the certificate 55253874 → e49a978c; run before this pre-registration) with a disclosure, or re-run them on engine X (about 3 pods; PLANF says about $7). (I) Reuse needs only the records. The seed-1101 G adapter is lost (FOCUS:94), but its readings survive. |
| Values already seen | FOCUS:230 (seed 1101: E +29.0 pp; task loss 2.100 → 1.612) | — | If reused, list every recipe-G value the authors saw. |
| Config | FOCUS:233 names `study-kt-olmo2-1b-r64-g-*-20261008` | not hashed here | The config file and its SHA-256. |
| Limits | §3 and §4 | OPEN | Say whether τ_L and τ_O apply to recipe G. (I) Its one-seed task loss is about 0.067 nats above the a0 mean, about 10 × τ_L. |

### 1.5 B+Qi (Qi et al.'s constrained SFT on recipe B)

| Item | Source | Status | Text the pre-registration needs |
|---|---|---|---|
| The arm: recipe B with Qi et al.'s constrained loss; 6 seeds; about $12; no novelty claim | FOCUS:225; FOCUS:149 | DECIDED | Restate it, and the rename from "G+Qi" (FOCUS:149). |
| No warmup | FOCUS:148 (the lead's proposal, 9 Oct 13:45 UTC); FOCUS:125 item (10) (the user's "take all recommendations", 9 Oct 19:37 UTC) | DECIDED | Restate it. RS E7 (RS:141) still lists it as open; RS was written before 19:37 UTC. |
| Loss and β schedule | SPEC:328-336, :349-358 | PROPOSED | β_1 = 0.5; β_t = 2 for t = 2–5; β_t = 0.1 for t > 5. t = 1 is the first response token after `<\|assistant\|>`. The end-of-turn target is the last t. π_aligned = the untuned model (the adapter off). |
| Token reduction | SPEC:355 | PROPOSED | (SPEC) The per-row mean over target tokens, then the mean over the step's rows, so recipe B's row weighting stays. The paper sums over tokens. Record it as a deviation. |
| Reference log-probabilities | SPEC:352 | PROPOSED | Precompute once per row before step 1 (float32 log-softmax), or compute online. Fix one. |
| Optimizer and schedule | REC lines 37-77; SPEC:337, :356 | DECIDED by "recipe B" | AdamW (0.9, 0.999), LR 1e-4 constant, batch 128, 38 steps, LoRA r64. Deviation table against Qi: AdamW (0.5, 0.999), LR 2e-5, batch 64, 10-step warmup, full fine-tuning. |
| Seeds | FOCUS:225 ("6 seeds") | OPEN: which 6 | (I) 1101–1106, like a0 (B+Qi uses no scorer built on a0-1101 states), or 1102–1107, like the method arms. |
| Engine change | `experiments/safety_selection/config.py`:33-36, :539-540 (`train.loss_weighting` accepts only `"token_mean"`); FOCUS:225 (committed before stage 1 is frozen); BRIEF:65 (T4: no engine change before Gate B's last kit pod) | not built (RS B12) | The new engine identity X′, its certificate and its determinism re-run (about $1–2; RS D5, RS:128). The tests SPEC:362-365 lists: the first step's gradient equals recipe B's; β → 0 gives recipe B; large β gives 2·max(Δ, 0); the reference log-probabilities reproduce. |
| Prediction risk | SPEC F4 (SPEC:42; Qi et al.'s warmup ablation is Table 5 in arXiv v1, not "Table 9" as FOCUS:70 says) | to record | (SPEC) Without warmup, B+Qi may land near recipe B, because our loss plateaus by step 2–3 of 38 (FOCUS:73 item 5). Write this as a prediction. |
| How it is reported | PAPER:198 ("report it beside recipe G") | OPEN in detail | Its comparator (I: a0) and that the comparison is descriptive (PLAN-S:119). |

### 1.6 Safe LoRA (the fifth mandatory reference)

FOCUS:154 lists what must be fixed "before any Safe LoRA run": the unaligned model, the exact projection, the layer rule and its threshold, the seeds and the engine work. The threshold comes "from the paper's rule or a fixed default, never tuned on stage-1 outcomes". The lead reads the paper in full first.

| Item | Source | Status | Text the pre-registration needs |
|---|---|---|---|
| Aligned model | REC lines 6-7; SPEC:304 | DECIDED | `allenai/OLMo-2-0425-1B-Instruct` at `48d788ec…` (the untuned model). |
| Unaligned model | FOCUS:154; RS B11 (RS:101); RS C2 (RS:114); SPEC:305 | OPEN | `allenai/OLMo-2-0425-1B` (base) at a pinned revision, with its SHA-256 per file. No config pins it today (RS:101). The download needs the user's approval (RS E9, RS:143). (I) The lead decides whether the user's "stop asking me for approval" (FOCUS:76) covers a model download, and records the decision. |
| Projector | SPEC F3 (SPEC:41); SPEC:286, :308 | PROPOSED | The fast form C = V Vᵀ / ‖V‖_F, applied without forming C. Reason (SPEC): the exact projector V(VᵀV)⁻¹Vᵀ is the identity for a square full-rank V and is not defined for `down_proj`. **UNVERIFIED (I):** the fast form's output grows with ‖V‖_F, so it is not a projector. The paper reader should check §3.4 before this is fixed. |
| "Layer" and ΔW | SPEC:306-307 | PROPOSED | Each of the 112 adapted matrices is one "layer". ΔW = s·B·A with s = 2. |
| Selection rule and threshold | SPEC:310, :318 | PROPOSED; the lead proposes and the user sees it at the freeze | (a) Top-K at 35%, K = 39 of 112 (SPEC's default). (b) τ = 0.35 as written; it may project 0 or all 112 matrices on our model. (c) Two points, 11% (K = 12) and 35% (K = 39), as a small curve; about +3 evaluations. Ties and the similarity formula (paper Eq. 3) must be fixed too. |
| Seeds | FOCUS:154; SPEC:312 | DECIDED unless the pre-registration says otherwise | a0 seeds 1101–1103 (the adapter-scaling seeds). They need the regenerated a0 adapters (§1.3). |
| Engine work | FOCUS:154; RS B11 | not built | A post-hoc state transform, evaluated by the existing eval-state job (RS:152 cites `runner.py`:745-760). Built with tests and reviewed before use. |
| Certification | SPEC:314 | PROPOSED | With K = 0 the path reproduces a0's Gate A U exactly (as §1.3). |
| What is reported | SPEC:313 | PROPOSED | Per matrix: the similarity, projected or not, ‖CΔW‖_F / ‖ΔW‖_F; and how many matrices τ = 0.35 would project. |
| The lead's full read of the paper | FOCUS:154 | OPEN: no record of it | SPEC read PDF pp. 3–8 only (SPEC:17). |
| Stage 2 | FOCUS:154; RS C2 | OPEN | `Llama-3.2-1B` base for the second family; access is UNVERIFIED (RS:114). |
| Claim | FOCUS:153 ("if Safe LoRA wins, that is reported"); PAPER:229 risk 25 | DECIDED | Restate it. |

### 1.7 The one-example safety patch

| Item | Source | Status | Text the pre-registration needs |
|---|---|---|---|
| Not built; bounded in text | FOCUS:78 (D5 = (a), the lead on the user's delegation, 16 Oct 12:15 UTC) | DECIDED | One related-work sentence and one limitation sentence. The reason (FOCUS:78: money and build time). No sentence may say that a data repair beats this patch. |
| The paper | RESTART:161 (official abstract re-read by the GPT lead) | not read by me | Its citation. Whoever writes the sentence reads the paper first (FOCUS:19's rule). |

### 1.8 Rules that apply to every reference

| Item | Source | Status | Text the pre-registration needs |
|---|---|---|---|
| Role: support for primary claims, not in the Holm family | SCOPE §1 tier table ("PRIMARY-SUPPORT"); PLAN-S:119 ("Everything else is descriptive") | DECIDED | Restate it. |
| Claim rules | PLAN-S:95 ("data repair beats model-level repair" only if it beats §5.2's references); FOCUS:153 (a data repair "dominates" only if it beats the free references on U, over-refusal and task loss); FOCUS:243 (only below the adapter-scaling curve); PLAN-S:250 and PAPER:136 (a free fix that wins is a valid answer) | DECIDED in words; OPEN as a test | One rule that covers all five references, not only the scaling curve. It must say how "beats" is read for each reference (I: the same matched-point rule as §1.3, applied to each reference's (U, O, L)). |
| Code path | PLAN-S:155 | DECIDED | SP, scaling and Safe LoRA go through one pinned "evaluate a saved adapter" script outside the engine identity. Recipe G and B+Qi are training arms. |
| Judges and measures | PLAN-S §7 (PLAN-S:185-197); FOCUS:244 | DECIDED for arms | (I) State that U, HB, O, task loss and ARC are measured the same way on every reference. |
| Seed block | PLAN-S:223 (the references are in block B) | DECIDED | What the paper says if block B is never funded (I: no "beats model-level repair" sentence). |
| Cost | PLAN-S:78 ("'free' arms charged"); PLAN-S:203 | DECIDED | Each reference's cost under both conventions (§2). Say whether the a0 regeneration (0.10–0.15 h) is charged; (I) report it apart, because a practitioner already has the adapter. |
| Blinding | ADD §3 item (4) (ADD:300) | OPEN for the S1 items | These settings are fixed after Gate B's noise gate and rankings were seen (FOCUS:77, :82). The pre-registration lists the Gate B values the authors saw, as REQ-21 (m) does for the W1 items. |

---

## 2. Cost conventions (C-full and C-lean) and how diagnostics are charged

| Item | Source | Status | Text the pre-registration needs |
|---|---|---|---|
| Log every arm and diagnostic in GPU-seconds by stage: setup, training, greedy generation, sampled generation, judging, scoring, pod overhead | PLAN-S:200; FOCUS:246 | DECIDED | Restate it. The stage-1 kit (B15) must write these stages. |
| 1 FRE per family = the median measured time of that family's R arms | PLAN-S:201; FOCUS:246 | DECIDED in words; OPEN in detail | Which R arms (I: Gate B's wave-0a R_1–R_3, stage 1's 8 R seeds, or both). Which stages count (pod overhead or not). Whether FRE is fixed before stage 1 or computed after it. |
| **C-full** = training plus the full evaluation as run | PLAN-S:202 | DECIDED in words; not frozen | The exact stage list. Say whether Qwen3Guard judging, the HarmBench and Granite judge pods, ARC, the task-loss pass and pod overhead are in it. |
| **C-lean** = training plus 200 harm prompts × 1 sample, priced from the ledgers' per-answer time | PLAN-S:202 | DECIDED in words; not frozen | Which ledger gives the per-answer time. Whether guard time is in it. **Gap (I):** as written C-lean has no over-refusal answers and no task-loss pass, but the selector's feasibility screen needs O and L (PLAN-S:127). Add them, or say how the screen works under C-lean. |
| c0 = measured on one real lean job: full training, a 20% prompt subset, cold start; about $0.3–0.6 | PLAN-S:202; FOCUS:246; in block A (PLAN-S:222) | DECIDED in words; not run; job not built (RS B17) | **Gap (I):** "a 20% prompt subset" does not match C-lean's "200 harm prompts × 1 sample". Reconcile the two. Say which arm and seed the lean job uses. |
| Predictions as curves in c_d/c0 | FOCUS:78 (U3 (a)); BRIEF:191; FOCUS:24 | DECIDED | The measured c0 only places the result on the curve. |
| Δ, V_max and c* under both conventions; a claim stands only where both agree | PLAN-S:202; FOCUS:246 | DECIDED in words | Define "agree" (I: the same sign of Δ at the stated budget, and c* in the same grid bracket). |
| B and c_d in units of c0, under both conventions; the c_d/c0 grid includes 0; if B − c_d < 2c0 the diagnostic policy picks keep; B = 2 is a boundary cell | ADD L15 (3) (ADD:261-265) | DECIDED | Restate it. |
| Charge every pool filter, untuned-answer generation, anchor job and scorer in full; write "≈ 0" only below 0.01 FRE | PLAN-S:203; FOCUS:24 ("the classifier included") | DECIDED | Add the missing allocation rules (OPEN): (i) the shared representation pass serves L1, S3, DataShield-style and the Gate C reproduction (SPEC F5, SPEC:43; BRIEF REQ-3) — charge each scorer the whole pass, or split it; (ii) one-off costs per dataset (the classifier, FOCUS:31; the anchor job) against per-menu costs; (iii) whether the a0 retrain that A1's gradients need (wave 0b: 0.077 h, FOCUS:77) is A1's cost. |
| A1 is priced only from the wave-0b ledger | PLAN-S:204; FOCUS:246 | DECIDED | The stages of the w0b-2 ledger that are A1's. FOCUS:77 gives only the total: diagnostics 3.04 h (frozen upper 2.0 h). |
| Self-Inf-N-style: $0 marginal, and the full charge (q's share of the wave-0b gradient pass); both reported | BRIEF REQ-13 (BRIEF:97); SPEC:257 | DECIDED for the build | Restate it, if the scorer is built (FOCUS:125 item (9)). |
| "Inline" cost only as a labelled model estimate; speed-ups are a separate engine round | PLAN-S:204 | DECIDED | Restate it. |
| No 1B cost ratio is claimed for 7–8B | PLAN-S:205; FOCUS:246 | DECIDED | Restate it. |
| Say that generation is about 81% of an arm, so "compute-matched" is mostly evaluation cost | FOCUS:73 item 5; PLAN-S:19, :30 | DECIDED | One sentence in the cost section. |
| Freeze the conventions before stage 1, after re-costing from the anchor-pod and wave-0 ledgers (D3) | PLAN-S:212; RS A13 (RS:77) | OPEN (Gate B's money re-costing is done, FOCUS:77; the FRE conventions are not frozen) | The frozen conventions and the ledgers used, by SHA-256. |
| Money rates (separate from FRE) | FOCUS:77 ($1.79/h spend); FOCUS:134 ($10/h price limit; guard plans $1.85/h) | DECIDED | Keep money and FRE apart in the text. |

**Measured cost facts the text can cite (R).** One Gate A arm: training 245 s, greedy generation 1,750 s, sampled generation 761 s, guard and scoring 293 s, about 3,115 s in all (PLAN-S:30). Gate B re-costing: pod overhead ≤ 26.0 min, arm ≤ 49.0 min, $1.79/h (FOCUS:77). Wave 0b: setup 16.6 min, retrain 0.077 h, diagnostics 3.04 h (FOCUS:77). The classifier: about 58 min for 9,788 rows with eager attention, to be re-measured with SDPA (FOCUS:31). Per-scorer estimates (I, SPEC): L1 about 0.05–0.15 FRE plus a scan of 0.03–0.1 FRE (SPEC:98); S3 0.2–0.6 FRE at a 512-token cap, up to 1.2 FRE (SPEC:159); DataShield-style 0.05–0.15 FRE (SPEC:215); Safe LoRA about 0.9 FRE per seed for its evaluation (SPEC:298); B+Qi about 1.0 FRE per seed (SPEC:345).

---

## 3. τ_L (L16)

### 3.1 The requirement

- ADD L16 (ADD:287-293): τ_L = 2√2 × s, fixed before wave 1, never re-estimated. s = the sample SD (ddof 1), over seeds 1101–1103, of each Gate A a0 unit's mean per-example query loss on all 200 task rows at e1. Each unit is named by SHA-256. Record s, τ_L and the 6-against-6 SE (s × √(1/3)). Only the threshold is frozen; the SE inside the selector's "upper 90% L" screen comes from the replay's pooled residuals. Record the 2-df risk.
- Earlier forms: FOCUS:245 ("2 SE of a seed-to-seed difference in held-out task loss on all 200 rows"); PLAN-S:124 (an inference, "fixed before wave 1"); BRIEF REQ-19 (BRIEF:115).
- The loss definition: "the training loss (per-example mean NLL over the response and end-of-turn targets) of each task row" (R: `experiments/safety_selection/prepare_task.py`:81-84). The engine writes one record per task row with only `query_id`, `input_tokens`, `target_tokens`, `token_sha256` and `loss` (R: `runner.py`:675-677). So the file holds no text.
- Status: the rule is DECIDED (L16, 16 Oct 19:46 UTC). The numbers below are mine (C). The lead's REQ-19 run is still to make the record of them.

### 3.2 The files (R; SHA-256 computed here)

Root: `/Users/spiderishi/Coding/attribution/tmp/`. NGI names exactly these three units as `gate_a/1101`, `gate_a/1102`, `gate_a/1103`, and the untuned unit as `gate_a/untuned` (R).

| Unit | Path (under the root) | Mean task loss (200 rows) | `eval/<ck>/query_loss.jsonl` SHA-256 | `eval/<ck>/summary.json` SHA-256 | `COMPLETE.json` SHA-256 |
|---|---|---|---|---|---|
| a0 1101, e1 | `family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1` | 1.5424909447459505 | `a539638fc5c7f5b98594094690b114fb5714343e4f497451301cce9630a189d1` | `f331eadee052f8f1c45403b7f19b7da7f1cfa1153d2b450285d3e777ca11171a` | `8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9` |
| a0 1102, e1 | `family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1` | 1.5472398312762379 | `2f73f77c40b161572572d8d18b317d21c26738bf2aed1e337b4ed7b7645f3e20` | `0918dc486803a0d3357d43e3fca323b9a29c6ae1379741486b03aa7bd36294f0` | `857f78bc0f49cc8a4902fbb6211f463daa7c7f44086257c4d752409a30ba0b25` |
| a0 1103, e1 | `family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1` | 1.5449415715783834 | `eba947241293ed571f7bb5ce507b59af98911cd411be323f9a8c901a1ae79612` | `7d24950cb2ad221dfcd0e27c0c40cc6745c52dcaac4612a966474310d85cf918` | `7be58eaa9c5be7b8f94668109efd6aae075b1d001e0d2b1fb8be814556899cbd` |
| untuned, init (report only) | `family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1` | 2.0996905191242696 | `02963ba5559077dfae9dd48a29ac5470507d05d48377966195545a8d979d27a6` | `7b40ea1c99bbfffdbc1711008f4fd10ba83cb5bca782c473fb6c16ee20f80801` | `b5083ce9d9f26efe92f9872fdbf9376a521a5d99d1b70cc2bd460987cdcc9474` |

**Checks (R, C).**
- Each mean I recomputed from the 200 per-row losses equals `summary.json` `query_loss.mean` and `COMPLETE.json` `evaluation.query_loss.mean` bit for bit. n = 200 in each.
- All four units hold the same 200 query ids. All have `query_bank_sha256` = `ab31576dab2f7bd530268a38146ce9339342ed7e7c77cf58127df579ea22ee87`.
- The three a0 units: arm a0, kind run-one, role development, split dev, target e1, seeds 1101/1102/1103. Recipe hash `9e9bde6f2f328760…`, which is REC's config hash (R: `research/side-notes/causal-study-20261012/protocol.json`:132-134 pairs it with REC's file hash `a47138f2…`). Engine `552538748acec1a8…`; manifest `9ed61826…`; training identity `f46279e5830f4777…`.
- The 1101 e1 unit resumed from the untuned unit (`resumed_from_complete_sha256` = `b5083ce9…`). The 1102 and 1103 units trained from init in one job each.

### 3.3 The numbers (C)

| Quantity | Value (nats) |
|---|---|
| Mean of the three a0 means | 1.5448907825335239 |
| s (sample SD, ddof 1) | 0.002374850619448416 |
| SE of one seed-to-seed difference, √2 × s | 0.0033585459546340963 |
| **τ_L = 2√2 × s** | **0.0067170919092681925** |
| SE of a 6-against-6 contrast, s × √(1/3) | 0.0013711206444236926 |
| 2-df risk: 95% interval for σ/s | 0.5207 to 6.2847 (χ²₂ quantiles; matches ADD:293's 0.52–6.28) |
| 2-df risk: P(s < 0.5σ) | 0.2212 (matches ADD:293's 0.22) |

**Context (C, R; report only, not part of the rule).**
- τ_L is 0.43% of the a0 mean task loss. It is 1.2% of the untuned-to-a0 gain (2.0997 − 1.5449 = 0.5548).
- Recipe G's seed 1101 had task loss 1.612 (FOCUS:230). That is 0.067 above the a0 mean, about 10 × τ_L (one seed, another recipe).
- Per-row view: the SE of the mean per-row difference between two a0 seeds is 0.0026–0.0031 nats (three pairs). So the row-by-seed noise alone is about the size of √2 × s. This agrees with s; it does not test it.

### 3.4 Text the pre-registration needs for τ_L

- The rule (L16) and the three numbers above, with the unit files by SHA-256.
- "Never re-estimated", and the scope: only the threshold is frozen.
- The 2-df risk line (ADD:293).
- **OPEN (I), to fix before anyone reads a stage-1 or Gate B arm's task loss:**
  1. The comparator. PLAN-S:124 says "the task-loss increase over a0". A 600-row removal trains 33 steps, not 38 (PLAN-S:102). So R itself may exceed τ_L. Say whether removal arms are judged against a0 (as written) or against R (dose-matched), and what the text says if R fails τ_L.
  2. The estimate compared with τ_L in the paper's "within the limits" sentences: the point estimate, or the upper 90% bound (the selector screen uses the upper 90%, PLAN-S:127).
  3. Whether τ_L applies to the references (recipe G, B+Qi, SP, scaling, Safe LoRA).
  4. I did not read any Gate B R-arm task loss, so this choice can still be made blind to it.

---

## 4. τ_O, the "worse" label, the SESOI, Holm and the seed rule

| Item | Source | Status | Text the pre-registration needs |
|---|---|---|---|
| **O** = the "Refusal: Yes" share (Qwen3Guard) on the 100 dev over-refusal prompts, greedy; lexicon refusal as a check; reported by source (XSTest-safe, OR-Bench-hard) | PLAN-S:191, :110 | DECIDED | Restate it. (I) State how an invalid answer counts; Gate B counts it as not refused (FOCUS:66 item (4)). |
| O against the untuned model (a0 reported) | FOCUS:236, :245; PLAN-S:105, :123 | DECIDED | The sign: ΔO = O(arm) − O(untuned). Values (R, `summary.json` `overrefusal` counts only): untuned 17/100; a0 4/100, 6/100, 4/100 (seeds 1101–1103). So a0 is 11–13 pp below the untuned model. |
| **τ_O grid {2, 5, 10} pp** above the untuned model's refusal; the chosen repair and V reported at each point | FOCUS:236, :245; PLAN-S:123 | DECIDED | Restate it. Say which estimate meets τ_O in the paper's sentences (point or upper 90%; the screen uses the upper 90%, PLAN-S:127). |
| O-ext only if the $0 check shows a 6-seed MDE for O above 5 pp; then from a new public source (a download the user approves), never the hidden remainder | FOCUS:245; PLAN-S:197; BRIEF REQ-19, U8 (BRIEF:196) | OPEN: the check is not run (BRIEF:45) | The check's result and the U8 answer. (I) A rough range from unit-level binomial noise (p 0.05–0.17, n = 100) gives an MDE of about 3.4–6.1 pp for a 6-against-6 contrast. It straddles 5 pp, so REQ-19's paired check decides. |
| **"Worse" label**: a contrast significantly adverse at the 5% Holm level, on U, O or task loss, each in its adverse direction | FOCUS:215 (the user, 8 Oct 18:31 UTC); wording "adverse" (FOCUS:138 item 3(a)) | DECIDED | Restate it with "adverse". |
| The Holm family of the O and task-loss contrasts | PLANF:143 item (b); BRIEF U4 (BRIEF:192) | OPEN (needed by W1) | Only the six U contrasts form a defined family (PLAN-S:114-115). Say whether O and L contrasts form their own families of 6, or join the U family. |
| Label order when endpoints disagree (better on U, worse on O or L) | PAPER decision 12 (PAPER:188); RS A3, E5 (RS:67, :139); BRIEF U4 | OPEN (needed by W1) | A complete decision table (I). Its order of checks, for example worse → better → equivalent → inconclusive. It must also cover "Holm rejects but the point estimate is below 5 pp", and say how a label meets τ_O and τ_L (PLANF:143 item (b)). |
| **SESOI 5 pp** on U (about 11% of E); TOST per contrast; 4 pp as a sensitivity | FOCUS:241; FOCUS:78; PLAN-S:115 | DECIDED | Restate it. Say that equivalence uses the unadjusted 90% CI (PLAN-S:115: "TOST per contrast"). Say that O and L have no SESOI. |
| Labels: better (Holm rejects and the point estimate ≥ 5 pp); equivalent (90% CI inside ±5 pp); inconclusive otherwise; plus worse | PLAN-S:115; FOCUS:215 | DECIDED | See the decision table above. |
| **Holm**: P1 A1 − R; P2 L1 − R; P3 H1 − R; P4 S1 − a0 (two-sided); P5 S3 − S1; P6 S4 − S1; U; two-sided; 5% | FOCUS:241; FOCUS:78; PLAN-S:114 | DECIDED | The test: seed-level U (600 sampled answers per arm-seed), seeds not paired, variance pooled over all stage-1 arms with its df stated, Welch as a sensitivity (PLAN-S:102). Under plan B the family is P1, P3 and P6 (PLAN-S:118). |
| P4's stated reason | SPEC F1 (SPEC:39); BRIEF U7 (a) (BRIEF:195) | OPEN: wording | (SPEC) DataRx does not state that its random arm is refusal-only. Correct "S1 = the DataRx random arm's pool type" (FOCUS:241). P4 stays two-sided. |
| Testing order: (1) the primary family; (2) confirmation; (3) the Llama replication; (4) the planted sweep; (5) the predictions; each later family at its own 5% | PLAN-S:119 | DECIDED (approved with PLAN-S) | Restate it. |
| Power | PLAN-S:117 | report | MDE after Holm's first step: 5.0 / 7.2 pp (removal) and 5.3 / 7.7 pp (add), at per-arm SD 2.65 / 3.85 pp; TOST power at a true 0: 0.94 / 0.55. (I) At central noise the first-step MDE equals the SESOI. PAPER:120 waits for the final MDE from Gate B's pooled noise. |
| **Seed rule**: method arms 1102–1107 (no scorer built on a0-1101 states is evaluated at 1101); R 1101–1108; a0 1101–1106 | FOCUS:242; PLAN-S:116 | DECIDED | Restate it. Add the reuse: Gate A a0 1101–1103 (PLAN-S:233; FOCUS:77 records the wave-0b fingerprint check passed; the engine-X certificate condition I did not re-check) and Gate B's R_1–R_3 at 1101–1103 (BRIEF REQ-21 (d)). R_d runs at seed 1100 + d (BRIEF:121; ADD L5). |
| Blinded rule on Gate B's final pooled σ̂: ≤ 4.5 pp plan A; 4.5–6.0 pp plan B (P1, P3, P6 at 9 seeds; R 12; S1 9); > 6.0 pp no stage 1, review | FOCUS:242; PLAN-S:118 | DECIDED | Name the exact quantity: PREREG §3 defines "Final σ̂ = max(√P, σ_eval)" (PREREG:128) and, after an extension, σ̂_x (PREREG:255). Say which one, and whether the plain or the fallback σ̂ (PREREG:129) governs. Name the extra seeds under plan B. The noise gate's σ̂_gate (1.83 pp, 2 df; FOCUS:77) is not this value. |
| Seed blocks: outcome-free; each starts on a funding event; only complete blocks are analysed; block A = primary arms at 1102–1104, a0 1104, R to 1105, diagnostics, c0 job; block B = 1105–1107, a0 1105–1106, R to 1108, the references | FOCUS:242; PLAN-S:222-223, :232 | DECIDED; "funding event" OPEN | Define "funding event" (FOCUS:125 item (8) is still open; RS A19, E10). Give plan B's blocks. |
| Reference seeds | §1 | partly OPEN | SP, scaling, Safe LoRA: a0 1101–1103. Recipe G: 1101–1103. B+Qi: 6 seeds, which ones OPEN. |
| Other seed rules already fixed by the lead | ADD §3 (ADD:297-299) | DECIDED | The L8 octile seeds by Gate B's wave rule; the plant's main arms at 1101–1103 paired with a0_plant. |

---

## 5. RS items B10–B17

RS lists B10–B12 and B14–B17 with deadline S1 (before the stage-1 freeze) and B13 with deadline W1 (RS:89-107). BRIEF:11 puts B10–B12 and B14–B17 out of the current build. My grep of `experiments/`, `scripts/`, `runkit/` and the builder's `scripts/stage1/` finds no code for any of them (patterns: safe_lora, adapter_scale, constrained loss, softplus, similarity strata, lean evaluation, prompt subset). No S1 build brief exists in `.ai/briefs/` (PLANF:135 step S2).

| # | Item (RS line) | Status | Text the pre-registration needs |
|---|---|---|---|
| B10 | The pinned "evaluate a saved adapter" script: regenerate each a0 adapter by a train-only re-run (fingerprint checked); apply the user-turn prefix or the scale λ; the engine's loaders, codec, generation and guard; certified once (RS:100; PLAN-S:155) | not built. The eval-state job exists (RS:152). No prefix or scaling code. The template code handles only Qwen's system turn (RS:100) | The script's name and SHA-256; the regeneration and fingerprint rule (§1.3); the prefix rule (§1.2); the scaling rule (§1.3); the certification and its failure action; the cost record. |
| B11 | The Safe LoRA transform, evaluated by the eval-state job; the base-model pins (RS:101) | not built; no base model pinned | Every §1.6 setting; the script's SHA-256; the base model's revision and file hashes; the tests (K = 0 reproduces a0). |
| B12 | B+Qi constrained loss: an engine change, committed before stage 1 is frozen (RS:102; FOCUS:225) | not built; `train.loss_weighting` accepts only `"token_mean"` (config.py:539-540) | The loss text (§1.5); the config key and the B+Qi config's SHA-256; engine X′ and its certificate; the determinism re-run; the T4 timing (after Gate B's last kit pod, BRIEF:65). |
| B13 | Selector simulation and replay, one code path, and the generative model (RS:103) | deadline W1; in the current build as REQ-16 to REQ-18 (BRIEF:107-111; ADD L15). The builder workspace holds only the T1 bundle today (`s1common.py`, `write_score_edit.py`, `labels.json`, settings, tests) | REQ-21 (k): the spec, REQ-17's settings hash, the frozen per-cell rules and REQ-18's predictions file hash; the recorded deviation that the runs-only rule was frozen later than FOCUS:247 says (BRIEF:121 (k)). |
| B14 | The similarity-strata script for the overlap control (RS:104; PLAN-S:172) | not built | The embedding (I: one read and layer of the shared representation pass, REQ-3), the similarity, the split (I: the median), and what "the add effect must hold on the lower-similarity half" means as a rule (a sign, an interval or a test) and what it does to a label. |
| B15 | The stage-1 run kit: seed blocks, add arms, eval-only reference jobs, the B+Qi recipe, at most 4 arms per pod, the funding need per block, judge pods (RS:105) | not built | The job kinds; the per-pod and per-arm caps; the price limit ($10/h, FOCUS:134) and guard rate ($1.85/h); the funding rule per block with the contingency inside (PLANF:143 item (d)); interleaving of arms across pods within a block (PLAN-S:232); the outcome-free re-run rule for invalid runs. |
| B16 | The stage-1 frozen reading: Holm, TOST, the four labels and their order, the blinded seed rule, the τ grids, the judge claim rule, the dominance curve, both cost conventions (RS:106) | not built | Its SHA-256 in the pre-registration, and the rule that every reported number comes from it, never by hand (as PREREG:230 does for Gate B). It needs §1.3's dominance test, §4's decision table and §2's conventions in exact form first. |
| B17 | The lean-evaluation job for c0: full training, a 20% prompt subset, cold start (RS:107; PLAN-S:202) | not built. RS marks engine support UNVERIFIED. My grep of `config.py` and `runner.py` found no prompt-subset option (only a checkpoint subset, `runner.py`:1307); this is not a full check | The lean job's definition, reconciled with C-lean (§2); how it runs without changing engine X (I: a pinned script outside the identity, like B10). |

### 5.1 Other RS items with the S1 deadline (short)

| RS item | Status now | Where above |
|---|---|---|
| A6 SP; C1 its text | text OPEN | §1.2 |
| A7 adapter scaling | DECIDED; test OPEN | §1.3 |
| A8 recipe G reuse | OPEN | §1.4 |
| A9 B+Qi; E7 warmup | DECIDED (FOCUS:125 (10)); details PROPOSED | §1.5 |
| A10 Safe LoRA; C2 and E9 base models | OPEN or PROPOSED | §1.6 |
| A13 cost accounting; D3 c0 job | conventions not frozen; c0 not run | §2 |
| A17 held-out confirmation rule (at most 2 contrasts per family, by a rule committed before stage 1; FOCUS:252) | OPEN (rule not written) | not in this file's scope |
| A18 families and testing order | text exists (PLAN-S:119) | §4 |
| A19 money; E10 funding event and the freeze | OPEN (FOCUS:125 item (8)) | §4 |
| D2 B10 certification pod; D5 B+Qi certificate | not run (code missing) | §1.3, §1.5 |
| E1 decision 24: a second rater or a larger human read | OPEN (PAPER:200) | not in this file's scope |

---

## 6. Decisions still needed (consolidated)

Deadline W1 = before Gate B wave 1. S1 = before the stage-1 freeze. "Lead" = the lead decides, since the user said "stop asking me for approval" (FOCUS:76); the user still sees each choice at the freeze.

| # | Decision | Deadline | Who | Default in the records |
|---|---|---|---|---|
| 1 | U4: the label order, and the Holm family of the O and L contrasts | W1 | Lead (user sees it) | none |
| 2 | U8: O-ext, after REQ-19's $0 check | W1 | Lead; a download needs the user | none |
| 3 | U6: the skill measure (task loss as the limit; ARC report-only) | W1 | Lead | PLAN-S:192-193 |
| 4 | τ_L's comparator, compared estimate and scope (§3.4) | before any arm's task loss is read | Lead; raise to GPT | none (I) |
| 5 | The SP text and joining rule | S1 | Lead | none |
| 6 | The scaling definition and the dominance test | S1 | Lead | none |
| 7 | Recipe G: reuse with disclosure, or re-run on engine X | S1 | Lead (user sees it) | none |
| 8 | B+Qi seeds, token reduction, reference log-probs | S1 | Lead | SPEC §7.4 |
| 9 | Safe LoRA base model and its download; projector; rule (top-K 35% or alternatives) | S1 | Lead; download needs the user's approval unless the lead rules otherwise | SPEC §6.4: fast form C; K = 39 |
| 10 | The C-full and C-lean stage lists; FRE's source; the c0 job; the shared-pass allocation; "agree" | S1 (D3) | Lead | none |
| 11 | "Funding event" and plan B's blocks | S1 | User (FOCUS:125 item (8)) | none |
| 12 | Which σ̂ the seed rule reads (final σ̂ or σ̂_x; plain or fallback) | S1 | Lead | none |

---

## 7. Concerns, weak assumptions and the smallest checks (I)

1. **τ_L may make most arms infeasible.** τ_L is 0.0067 nats. Recipe G's one seed is about 10 τ_L above a0. A 12.5% data removal may also move task loss by more than 0.0067 (I; not checked, because checking would read Gate B or stage-1 outcomes). This is a consequential tradeoff for GPT. The smallest decisive step is to fix the comparator rule now, blind. A second option is to report τ_L's binding share in a pre-registered sensitivity, not to change τ_L.
2. **The 2-df s.** With P = 0.22, s is below half of σ (ADD:293). L16 accepts this risk. The per-row view (§3.3) agrees with s; it does not confirm σ.
3. **C-lean and the screen.** The selector screen needs O and L. C-lean as written prices neither. Fix the definition before the predictions are frozen (they use both conventions, ADD L15 (3)).
4. **c0's two definitions** (a "20% prompt subset" against "200 harm prompts × 1 sample"). One must give way before B17 is built.
5. **Dominance has no test.** "Below the curve" in a 3-measure space (U, O, L) is not a rule yet. Without it, the paper's F1 and F2 sentences (PAPER:133-136) cannot be filled by a frozen reading.
6. **Certification "exactly".** Bit-equal reproduction of a Gate A U across engine versions and pods may fail for reasons unrelated to the code (I). Define the criterion and the failure path first.
7. **Timing.** B+Qi needs engine X′ in main, and T4 forbids engine changes before Gate B's last kit pod (BRIEF:65). FOCUS:225 needs the change committed before the stage-1 freeze. So the freeze waits for Gate B's last kit pod.
8. **References in block B only.** If block B is not funded, the comparison with model-level fixes is missing. FAQ's main-track list for ICML 2027 asks for stronger model-level references (FOCUS:74).
9. **O's reference point.** O is read against the untuned model (17%), while a0 is at 4–6%. τ_O therefore binds only for arms that over-refuse more than the untuned model. The "worse" label on O uses each arm's comparator. Both facts need one clear sentence each, or readers will mix them.
10. **Safe LoRA's fast form.** If the fast form is not scale-free (I), K and the merged update's size interact. The paper reader should check §3.4 and Eq. 3 before the rule is fixed.
11. **A record that is out of date.** RS lists E7 (B+Qi's warmup) as open (RS:141). FOCUS:125 item (10) closed it on 9 Oct 19:37 UTC. Cite FOCUS, not RS, in the pre-registration.
12. **Outside this file's scope, noticed once.** PLAN-S:243 says Llama's Gate B-lite rules and comparison scale are pre-registered before Llama's formal Gate A. Llama's Gate A seeds 1102–1103 ran on 9 Oct (FOCUS:119-120). FOCUS has no "Gate B-lite" entry (grep). The stage-2 pre-registration should record this order.

---

## 8. Process

- **Commands run (all exit 0 unless noted).** `date -u` (4 times); `git branch`, `git log`, `git status`, `git show --stat`, `git diff` (read only) in the main checkout; `wc`, `ls`, `du`, `grep`, `sed`, `shasum -a 256` on the records named above; one `grep --include=*.py` failed in zsh because of the unquoted glob and was redone with quotes; Python 3 reads with `-I` of: the four units' `job.json` and `COMPLETE.json` (named keys only), `eval/<ck>/query_loss.jsonl` (`query_id`, `loss`), `eval/<ck>/summary.json` (`query_loss` and the numeric `overrefusal` counts), NGI (paths only), `protocol.json` (one hash pair) and two engine-identity files (key names only); my script `tau_l_check.py` (exit 0).
- **Files written (only here).** This file; `tau_l_check.py` (SHA-256 `20b21e5d467e7b22…`), which recomputes §3 from the same records; `tau_l_check.out.json` (`d822ba18e39d4ab5…`), its output. All under `.claude/worktrees/kind-hawking-a6ce04/tmp/gi-vi-parallel/prereg-references/` (git-ignored by `tmp/`).
- **Not opened.** `rows.jsonl`, `groups.json`, `selector.jsonl`, `hidden/`, held-out files; every `generations.jsonl`, `samples.jsonl`, `guard*.jsonl`, `harm_*.jsonl` and `arc_utility.jsonl`; any Gate B wave-0a or wave-0b arm record; any paper.
- **Limits.** Line numbers are at the hashes above; FOCUS grows. Facts marked (I) are mine. The O MDE range in §4 is a rough unit-level estimate, not REQ-19's paired check.
