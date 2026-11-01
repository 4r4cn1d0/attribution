# Engine round Y: design (PROPOSAL)

**Status: PROPOSAL. It adopts nothing and builds nothing.** Written 2026-10-16 from about 21:30 to 22:30 UTC (17 Oct IST; clock checked with `date -u` at 21:27 and 21:47 UTC) by an Opus worker for the main-study lead (General Implementation VI). **Reviewed and revised in place 2026-10-16, about 21:50–22:40 UTC (clock checked with `date -u` at 21:50 and 22:06 UTC) by a second, adversarial Opus worker.** Places that the review changed carry **[rev]**. §13 lists the changes. Read-only work: no run, spend, install, commit, push, pod, download or agent. The only file changed is this one.

**Scope.** The user has not chosen option B or C of the re-plan. This design covers what B and C share. Parts that apply to one option only are marked **[B]** or **[C]**.

**Labels.** **M** = measured (the source follows). **R** = read (path:line or URL). **E** = estimate (the basis follows). **I** = inference.

**Short names.** All paths are relative to `/Users/spiderishi/Coding/attribution` (branch `stageb-costs-and-recovery-safeguards-20261003`). **[rev]** HEAD is now `19c2d28`, equal to its origin (M: `git rev-parse`, 22:00 UTC). The first draft used `fc85fda`. The two newer commits add `writing/paper/2026-10-17-lit-sweep.md` and §5 of ADD; `research/FOCUS.md` did not change, so every F line number below still holds (M: `git diff --stat fc85fda 19c2d28`).
- RP = `writing/paper/2026-10-17-icml-replan-PROPOSAL.md`.
- F = `research/FOCUS.md` (entries by UTC time; line numbers at `fc85fda` = `19c2d28`).
- BR = `.ai/briefs/stage1-commitments-build-20261016.md` (revision 1). ADD = its addendum `…-lead-decisions.md`.
- PLAN-S = `research/review/2026-10-08-sharpened-direction-DRAFT.md`. PRE = `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (revision 5, `5c97cce7…`, M: `shasum`).
- PLANF = `tmp/gi-v-stage1-plan/PLAN-final.md`; RS = `tmp/gi-v-stage1-plan/read-stage1.md` (main checkout, git-ignored).
- SS = `experiments/safety_selection/`. EP = `scripts/evaluation_path.py`. READ = `scripts/gate_b_reading.py`.
- CERT-X = `SS/configs/evaluation-equivalence-gateb-20261008.json`. X = engine `472fc7f6…`. Y = the engine this round makes. **[rev]** X′ = PLANF's name for a B+Qi-only round (PLANF:137).
- LEDG = the three engine stage ledgers that RP names (RP:7); stage times below are my sums of their `seconds` fields (M).

---

## 0. Summary

- **What Y is.** One engine round. It is built in a separate, hand-made workspace. It goes into the working branch only after Gate B is fully read (`--final`) **[rev] and after its certification pods pass (§5.2)**. It holds only what must be inside the engine:
  - **Y1**, a *confirmation role*: sealed edit arms, R and a0 trained at fresh reference-namespace seeds on the development data.
  - **Y2**, *sealed bank-subsample files*: the 200-prompt hidden subsample for stage 3 (**[rev]** default: 200 harm prompts, as F:252 says; §3.3), and a development-bank subset for the lean c0 job (B17).
  - **Y3**, *B+Qi* (Qi et al.'s constrained loss, B12) as an opt-in recipe field.
  - **Y4**, the certification tools and records for X → Y.
- **What Y does not hold.** These stay outside the engine identity: 7–8B and 32B support (recipes, configs and kits; the engine already ran 7–8B), the Part C scorer scripts made model-agnostic, the safety prefix, adapter scaling and Safe LoRA (B10, B11; **[rev]** B11 needs the lead's check, §2 N6), Alpaca (a derived Dolly-format file), and speed-ups.
- **Bit-identical promise.** For every recipe, data config and job that exists at X, Y gives byte-identical outputs on the same pod environment, **training included**. This is stricter than X's certificate, which certified the evaluation path only. **[rev]** The promise is tested by goldens and pod C1. A *static* insert-only proof for every training symbol may not be possible (§1.2 items 1 and 1b); §5.4 fixes the rule for that case now.
- **Certification.** (1) Static: every changed engine symbol is new or insert-only (**[rev]** with a named, pre-set exception route for training-only symbols, §5.4). (2) CPU: golden digests written at X before any change; Y reproduces them. (3) CUDA: one 1B pod re-runs a complete unit as a determinism control, runs a short B+Qi smoke **[rev] and runs the c0 lean job (C3 moves onto this pod)**. [B]/[C]: one 7–8B re-run per reused side-project family.
- **[rev] Deadlines.** **Y3 (B+Qi) is due at the stage-1 freeze, not on 20 Nov.** F:225 says the B+Qi engine change "is committed before stage 1 is frozen", and PLANF puts its certification pods before the stage-1 freeze (PLANF:137-140, S4 → S5 → S6 → S7). In this schedule that leaves about 0–4 days of slack before stage-1 block A (latest start 3 Nov, RP:101). **Y1 and Y2's hidden path** are due by 20 Nov (the 7–8B pre-registration names them, RP:104).
- **[rev] Pre-set split rule.** Build Y1–Y4 in one workspace. If Y1 and Y2 are not verified when Y3 and Y4 are, freeze Y3 + Y4 (+ Y2's dev-source path, which the c0 job needs) as X′ for the stage-1 freeze, and certify Y1 + Y2's hidden path as a second strict round before 20 Nov (E: +1 determinism pod about $2.3, + one verification of 3 / 8.5 / 15 h). Reason: D5's own record counts "engine round Y before stage 1" as critical-path work to avoid (F:78 reason (2)).
- **Schedule (E).** Build and verify 18–27 Oct. Freeze Y by hash about 27 Oct. Certify on pods C1–C3 one day after Gate B `--final` (about 29–31 Oct if wave 1 starts on 27 Oct), then integrate. Certified about 30 Oct–2 Nov. **[rev]** If wave 1 starts earlier than 27 Oct, Gate B may finish before Y is frozen; then Y, not Gate B, sets the stage-1 freeze date (§8).
- **Cost (E).** Build $0. Pods about $3.0–3.7 at 1B (C1–C3 on one pod), plus about $3–4 per reused 7–8B family: [B] about $9–13, [C] about $6–8. **[rev]** Whether these pods may run before a funding event is the user's open ruling (PLANF:234 item 14). Gate B's reserved need is not touched.
- **A cost gap found (I, now with M basis) [rev].** Evaluating each confirmation unit on the hidden subsample *and* the dev bank (F:252) adds about **0.6–0.85 FRE per unit** at 7–8B. M: evaluation is 83–88% of a 7–8B job (LEDG: OLMo-2-7B 75.3 of 90.4 min; Llama-3.1-8B 107.3 of 122.1 min). RP's confirmation figure (36–48 FRE for [B], RP:76) appears to count one evaluation per unit (I), and PLAN-S priced both reads at only "1.25 × an arm" (PLAN-S:59). Both are low (§9.2).
- **T4.** Nothing here changes an engine file, Gate B pinned script, Gate B kit file or sealed file before Gate B's last kit pod. Y goes into the working branch later still, after `--final` and the certification pods (§4.3). **[rev]** RP says Y is *built* after that pod (RP:93, RP:116). This design builds it earlier, in a workspace. T4's text covers engine files, not workspace copies (BR:65), and the W3 build uses the same pattern (PLANF:118). The lead decides this reading (decision 3).

---

## 1. Challenge before building

### 1.1 Simpler alternatives

| # | Alternative | Saves | Why not chosen, or when to choose it |
|---|---|---|---|
| A0 | No confirmation engine work: fresh development-namespace seeds, labelled "not hidden-bank" (PLAN-S:277 item 11, its second option). **[rev]** That option reads "fresh-seed dev **and selector** confirmation". Under D5 the selector bank serves the later held-out selector study (F:78), so only the dev-bank form is still open | all of Y1 and Y2 | The dev prompts were used to choose the contrasts. Fresh seeds remove the seed part of the winner's curse, not the prompt part. F:252 adopts the hidden subsample. |
| A1 | **Y-zero**: no engine change for confirmation. A pinned script outside the identity (the B10 pattern, RS:100) trains development-role edit arms at fresh development seeds, then calls the engine's own evaluation function on the hidden subsample | the confirmation role and its review | It goes around the engine's access policy (R: SS/jobs.py:6-12). It must use development-namespace seeds, a deviation from F:252 ("fresh reference-namespace seeds"). It re-implements eval-state's records. **Choose it only if B+Qi leaves the engine plan.** Then no engine round is needed at all. |
| A2 | Two rounds: X′ for B+Qi before stage 1 (PLANF:137, "one certificate X → X′"), then Y for confirmation before stage 3 (PLAN-S:215). **[rev] This is the plan of record** (BR:11 "Engine round Y (stage 3…)"; PLANF:143 S6 checklist item (a), "engine round Y waits for stage 3") | **[rev]** Y1 and Y2 leave the stage-1 critical path | Two certificates, two determinism pods (+about $2.3, E), two verifications, and an engine join between stage 1 and stage 3. **[rev]** It is now the pre-set fallback (§0 split rule). |
| A3 | Everything in Y: prefix, scaling, Safe LoRA, 32B, speed-ups, an Alpaca parser | the outside scripts | The prefix changes prompt encoding, which is the evaluation path. A larger Y is slower to verify and holds up B+Qi. RS:100 and PLANF:137 already put B10 and B11 outside the engine package. |

**Chosen: one round with Y1–Y4, with the pre-set split rule of §0 [rev].** Reason (I): B+Qi forces an engine round, because a change to the training objective cannot live outside the engine without a copy of the training loop; F:225 already records it as "the engine change". Adding the confirmation role to the same round costs one more set of reviewed symbols, not another certificate or pod. **[rev]** But it puts Y1 and Y2 on the stage-1 critical path, which D5's record names as a cost (F:78 reason (2)). The split rule removes that risk if Y1 or Y2 run late.

### 1.2 Weak assumptions, and the check that settles each

1. **B+Qi fits as insert-only code behind one opt-in field.** Check: a $0 spike in the workspace, then `EP certify` in strict mode (§3.6). **[rev] Evidence against a pure insert-only fit:** (a) `validate_recipe` ends every recipe without `loss_weighting` with `_fixed(train["loss"], LOSS, …)` in an `else` branch (R: SS/config.py:539-543). An inserted line cannot let a new loss text pass that branch. §3.4 now keeps `train.loss` unchanged for this reason. (b) X itself removed 24 lines in runner.py (M: `git show --numstat c9aa7ca`: 129 added, 24 removed). REVIEWED entries are insert-only by test (R: SS/tests/test_ss_gateb_certificate.py:67-81), so those removals sat in TRAINING_ONLY symbols or imports (I). A new training objective will likely need the same.
1b. **[rev, new] Y1 and Y2 fit as insert-only code.** The role tables are one-line dict literals (R: SS/jobs.py:47-50), so a new role cannot join them without editing a line. `validate_job` refuses an unknown role and an unknown bank name (R: SS/jobs.py:111-114). `check_run_access` indexes the tables (R: :249-256). `run_one` passes the bank name to `load_prepared` (R: SS/runner.py:363-367), which refuses an unknown bank (R: SS/prepare.py:941-942), and prepare.py stays untouched. So each entry point needs an inserted early-return branch, as X did for anchor jobs (R: SS/jobs.py:143-144 → `_anchor_attributes_job`). Six symbols are touched: `validate_job`, `check_run_access`, `require_code_pin`, `check_attribution_access`, `run_one`, `eval_state`; the last two are evaluation-path symbols (REVIEWED in CERT-X, M). Check: the same $0 spike as item 1.
2. **Y reproduces X bit for bit on CUDA.** Check: pod C1 (§5.3). X's own training equivalence rested on the same kind of check: the wave-0b retrain's adapter fingerprints against P1101's (R: PRE:106). They were equal (R: F:77, 16 Oct 13:21, "fingerprint trigger false").
3. **200 hidden harm prompts (and, if decision 4 adds them, 100 hidden over-refusal prompts) encode under both family tokenizers within 1,536 prompt tokens.** The hidden part holds about 867 harm and about 1,369 over-refusal prompts (I from R: `SS/configs/study-v3-data-inj05.json` `eval_banks`: eligible 1,267 and 1,569, minus dev 200/100 and selector 200/100; "the hidden part is the rest", SS/config.py:64-65; the 1,536 limit, `max_prompt_tokens` in both family data configs). Check: the lead's counts-only encode run (§3.3). **[rev]** M: both family tokenizers are already in the Mac's Hugging Face cache at the pinned revisions (`models--allenai--OLMo-2-0425-1B-Instruct` snapshot `48d788ec…`, `models--meta-llama--Llama-3.1-8B-Instruct` snapshot `0e9e39f2…`, each with `tokenizer.json`), so the draw needs no download.
4. **A bank with no ARC items evaluates cleanly.** The evaluation filters items by kind (R: SS/runner.py:654-664). The summary for zero ARC items is not checked. Check: a CPU test.
5. **The side-project 7–8B units ran in the main kit's environment** (the 13 environment fields and the lock, R: PRE:107). Check: compare their `assets.json` environment blocks at $0, before decision 9.
6. **Rewriting four Gate B test lines from "the live engine" to "the stored X records" keeps their force.** Check: each rewritten test still fails on a forged stored record (a named mutant, §6.2).
7. **[rev, new] Building Y does not delay the stage-1 build or S3.** PLANF names the Specialized chat as the default builder of W3 and of S3 (PLANF:113; S3 row), and §7 names it for Y too. One builder works serially. Check: the lead's routing (decision 8) before the brief.

### 1.3 The smallest decisive check

Two $0 checks before the full build: (a) the spike of assumptions 1 **and 1b [rev]**; (b) the lead's counts-only encode run of assumption 3. If (a) fails for B+Qi, §5.4's training-only route applies. If (a) fails for Y1/Y2, use A2 (or A1) for confirmation.

---

## 2. The needs, and where each one goes

| # | Need | Source | In Y? | Where instead, or how | Needed by | Option |
|---|---|---|---|---|---|---|
| N1 | Confirmation role: sealed edit arms at fresh reference-namespace seeds, evaluated on a sealed hidden subsample and on the dev bank | R: F:252; today edit arms are dev-only (SS/jobs.py:23-24, :124-125) and only the reference role reads hidden (:47-50, :247-260) | **Y1** | — | named by the 7–8B pre-registration (20 Nov, RP:104); used from 14 Dec | B, C |
| N2 | The sealed 200-prompt hidden subsample, re-tokenized per family | R: F:252. The family data configs copy hidden "byte for byte and not re-audited" (`SS/configs/study-kt-data-dolly-olmo2.json` and `-llama3.json`, `amendments[0]`); the engine checks every prompt's token hash (SS/runner.py:574-578) | **Y2** (reader and access) | the draw is an outside script that the lead runs (§3.3) | sealed by the stage-1 freeze (decision 4) | [B] two family files; [C] one |
| N3 | The dev-bank read of the same units | R: F:252 | exists | eval-state on the dev bank (§3.2) | — | B, C; see §9.2 |
| N4 | The c0 lean job: full training, a 20% prompt subset (B17) | R: PLAN-S:202; RS:107 ("UNVERIFIED whether the engine can evaluate a prompt subset"). **[rev]** It cannot today: an evaluate bank must be one of the three banks (R: SS/jobs.py:113-114; SS/prepare.py:941-942). PLANF:137 planned B17 as a new file outside the engine package | **Y2** | the same file type with source = dev, plus a lean recipe (config only). **[rev]** This moves B17 (and B12) out of the S1 build list (PLANF:135-137): the S2 brief must drop them (decision 18) | **[rev]** stage-1 block A (PLAN-S:222 lists the c0 job there) | B, C |
| N5 | B+Qi, Qi et al.'s constrained SFT, without warmup (B12) | R: F:225 (approved), F:148; BR:21 item (10); RS:102 ("an engine change") | **Y3** | the numbers go in the recipe, not in code (decision 11) | **[rev]** the stage-1 freeze: F:225 "committed before stage 1 is frozen"; PLANF:138-140 (S5 certification pods before S6/S7). Used in 1B block B and 7–8B block B (3 Dec, RP:106) | B, C |
| N6 | Safety prefix, adapter scaling (B10), Safe LoRA (B11) | R: RS:100 (B10 "outside the engine identity"); PLANF:137 (B10, B11 "as new files outside the engine package"). **[rev]** RS:101 and F:154 (a user decision, 9 Oct) call B11 "a post-hoc state transform evaluated by the existing eval-state job". eval-state evaluates a stored run's checkpoint (R: SS/jobs.py:131-133; I), so a transformed adapter may need an engine path | no (**[rev]** if the lead confirms) | pinned scripts, certified once by λ = 1 and no prefix reproducing a Gate A U (RS:125, D2). **[rev]** If B11 must go through eval-state itself, it is an engine change and joins Y (decision 15) | stage-1 block B | B, C |
| N7 | 7–8B support | R: 7–8B recipes exist (`SS/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json`, `study-kt-llama31-8b-r64-b5e5-mb2-20261010.json`) and the side project ran them on X (RP:38-40, :71) | no | kits: a measured upper bound for the cap rule (the projection lives in the kit, R: `runkit/family-probe/setup/preflight_probe.py`; RP:113; the sibling note `78b-kit-cap-rule.md` in this folder) | 7–8B block 0 (9 Nov) | B, C |
| N8 | A1 at 7–8B | R: the attributes job needs a0 states "trained by the RUNNING code" (SS/runner.py:864-878) and an anchor file for that model (SS/jobs.py:193-195 checks the model) | no | run each A1 pass on the engine that trained its a0 states; split a long pass by `group_ids` (the job takes a group list, SS/jobs.py:139-142). E: 6–11 h per pass (RP:43) | 7–8B block 0 | B, C |
| N9 | 32B (OLMo-2-0325-32B-Instruct on an H200) | R: the model card names the model, its DPO parent and the Apache 2.0 licence; it does not state layers or tokenizer (https://huggingface.co/allenai/OLMo-2-0325-32B-Instruct; re-read by the reviewer, 22:0x UTC). I: SS has no GPU-type pin (grep of loaders.py, engine.py, runner.py). R: the 13B recipe shows the memory ladder (micro-batch 1, gradient checkpointing, generation batch 16; `study-kt-olmo2-13b-r64-b-mb1-gc-g16-20261008.json`) | no | a recipe, a kit, a smoke test; if the smoke test needs an engine change, decision 10 | 7 Dec (RP:107) | **[B] only** |
| N10 | Part C scripts work for any model | R: RP:114; BR REQ-3 and REQ-10 fix hidden-state indices 0…16 and OLMo-2's `post_attention_layernorm` / `post_feedforward_layernorm` hooks (BR:73, :91); tiny OLMo-2 and Llama configs exist (SS/tests/test_ss_family_models.py:24-52). M: the stage-1 workspace holds only the T1 bundle so far (no Part C file) | no | **[rev]** a generic version as new files after the W1 commit, under the 7–8B pre-registration; the OLMo-1B scripts stay as BR specifies (decision 12). Y's duty: keep the engine symbols those scripts import unchanged (§3.5) | before the first 7–8B scorer pass | B, C |
| N11 | The A1 writer's engine pin | R: ADD:314 item 8. M: the workspace's `scripts/stage1/settings/write_score_edit.json` pins `engine_x` = X | no | a new settings file per engine and model; the T1 file stays | first A1 pass on Y or at 7–8B | B, C |
| N12 | Alpaca | R: `parse_dolly` accepts any configured category list (SS/sources.py:252-270) | no, if … | the Alpaca note uses a derived Dolly-format file with sealed pseudo-units (I); otherwise its parser must join Y before Y freezes (decision 13) | Alpaca Gate A (16 Nov, RP:103) | B, C (model differs) |
| N13 | The later held-out selector study | R: F:78; BR:123 | no extra | Y1 is generic, so that study can use it | after a funding event | later |
| N14 | Gate B-lite transfer check at 7–8B | R: RP:91 | exists | group-removal arms on the dev split | after the 1B verdict | B, C |

---

## 3. Design of Y

### 3.1 Rules for every change

1. **Insert-only.** An existing symbol may only gain lines. No line is edited or removed. This is X's rule for reviewed symbols, and a test enforces it (R: SS/tests/test_ss_gateb_certificate.py:54-81). **[rev]** The only pre-set exception is §5.4's training-only route.
2. **New behaviour lives in new symbols inside existing engine files.** No new engine file: EP refuses "a file added or removed" (R: EP:33-34). The identity hashes every top-level `*.py` of SS plus seven `minimal_safety` modules, tests excluded (R: SS/common.py:24-36; M: recomputed `472fc7f6…` over 29 files).
3. **Every new path opens only on a new job key or a new optional recipe field.** No X-era job or config holds one, so their hashes and meaning stay. This is the engine's precedent for optional fields (R: SS/config.py:11-13). **[rev]** Because the role tables cannot gain a key (§1.2 item 1b), the new role is recognised by an inserted early branch in each entry point, before any line that reads the tables.
4. **Files that may change:** SS/jobs.py, SS/runner.py, SS/__main__.py, SS/config.py, SS/engine.py, and SS/README.md (README is outside the identity, R: SS/common.py:34). Every other SS file and the seven reused `minimal_safety` modules stay byte-identical (§4.1).
5. **No new process-global writes.** EP's `<global_writes>` and `<side_effect_free>` records must stay equal. They cannot be reviewed away (R: test_ss_gateb_certificate.py:84-108).
6. **Messages carry ids, counts and hashes only.** Never a prompt, answer or anchor text (the engine's rule, SS/README "Exit status").

### 3.2 Y1: the confirmation role

| Property | Value | Basis |
|---|---|---|
| Name | **[rev]** a new role with a distinct name (for example `edit_confirmation`). X already has a constant `CONFIRMATION_ROLES = ("selector", "reference")` (R: SS/jobs.py:50), and the new role is *not* added to it (a line edit). A role called plain `confirmation` that is not in `CONFIRMATION_ROLES` invites mistakes in code and records. The three X roles stay exactly as they are | R: SS/jobs.py:47-50 |
| Split | `dev`. In the kill-test data the held-out partition is empty, and edit arms are dev-only. (The X reference role uses split `heldout`, R: SS/jobs.py:47.) | R: SS/prepare_task.py:24; SS/jobs.py:124-125 |
| Seeds | the reference namespace 9101–9999, drawn with the existing `allocate_seeds(data_config, "reference", purpose, n, exclude=every seed in the registry)` | R: both family data configs `seed_namespaces`; SS/jobs.py:306-330; F:252 |
| Arms | a0, edit arms (`edit-<SHA-256>`), dev group arms | — |
| Banks | run-one: a subsample bank (§3.3) whose source is `hidden` (the primary read) or `dev`. eval-state from a stored confirmation run: `dev`, or a subsample bank. Never the full hidden bank. Never the selector bank. A hidden-sourced subsample also needs a new explicit switch, `--allow-hidden-subsample` | — |
| Code pin | required on every job, as for the selector and reference roles (**[rev]** by an inserted check in `require_code_pin`, not by joining `CONFIRMATION_ROLES`); eval-state also requires the source run's code identity to equal the running code | R: SS/jobs.py:262-267 |
| Attribution | refused on confirmation states, as for reference seeds | R: SS/jobs.py:275-277 |
| Registry | the trajectory key holds the role, so confirmation trajectories never collide with development ones. Also refuse a start when the registry holds any trajectory at the same seed under another role (a reference-role a0 at that seed trains the same kill-test data) | R: SS/jobs.py:284-303 |
| Refused before any model loads | a seed outside the reference namespace; the full hidden bank; the selector bank; a missing switch; a null code pin; an attributes job; a subsample file of another manifest | — |

**Order inside one confirmation unit (I).** run-one trains to e1 and evaluates the hidden subsample: the primary read, with no extra model load. Then an eval-state job evaluates the dev bank: the secondary read. Decision 5 may cut it (§9.2).

### 3.3 Y2: sealed bank-subsample files

**Precedent.** The Gate B anchor bank: the job names `anchors-<SHA-256>` and carries the file path, and the engine checks the file before any model loads (R: SS/jobs.py:150-218; reviewed in CERT-X).

**Job keys.** `evaluate_bank` = `subsample-<SHA-256 of the file's bytes>`, and one extra key `bank_file` = its path. Jobs without it keep their former keys. **[rev]** `validate_job` refuses any bank name outside the three banks (R: SS/jobs.py:113-114), and `load_prepared` refuses one too (R: SS/prepare.py:941-942), so a subsample job is validated by an inserted early branch, and `run_one` / `eval_state` open the *source* bank, then evaluate only the file's items. A named mutant checks that the full source bank is never evaluated (§6.2).

**The file** (canonical JSON):
- `kind` "safety-selection bank subsample", `version` 1;
- `tokenizer` {repo_id, revision}: must equal the data config's tokenizer. So one file serves the 1B and 7–8B models of one family: the OLMo-2-7B recipe uses the OLMo-2-1B tokenizer, and the Llama-3.2-1B recipe uses the Llama-3.1-8B one (R, re-checked: `model.tokenizer` in `study-kt-olmo2-7b-r64-b-mb2-20261008.json` and `study-kt-llama32-1b-r64-b5e5-mb4-20261008.json`);
- `source` {manifest_sha256, bank: "dev" or "hidden", bank_file_sha256};
- `draw` {label, script_sha256, settings_sha256} (provenance only);
- `items`: bank rows in the bank schema. For a hidden source, the token fields are recomputed with the family tokenizer;
- `counts` by kind.

**What the engine checks before any model loads.** The bytes hash to the bank id. The file is canonical. Kind, version and keys are the schema's. The tokenizer and the source manifest equal the job's. Every item id is in the source bank, and every non-token field equals that item's (for a dev source, the whole item is equal). No id repeats. The counts match. During evaluation the existing per-item token check runs (R: SS/runner.py:574-578). The source bank is opened through `load_prepared` (R: SS/prepare.py:937-963); the hidden bank opens only under the confirmation role with the switch.

**Who may use which file.** The development role: dev-sourced files only (the c0 lean job). The confirmation role: both sources. The selector and reference roles: none.

**The draw** (outside the engine: a new `scripts/stage3/make_bank_subsample.py` with a settings file and tests; the lead runs it; counts only; the near-duplicate precedent of the Gate C anchors, R: BR:43).
- **Contents [rev].** **Default: 200 harm prompts, no over-refusal and no ARC items.** F:252 says "a sealed 200-prompt hidden subsample" and PLAN-S:215 says the same. Over-refusal (O) and ARC then come from the dev read only. **Option, the user's call:** add 100 over-refusal prompts, 50 per source stratum (`xstest_safe`, `orbench_hard`, as in the dev bank, R: `study-v3-data-inj05.json` `per_source`). This makes the subsample 300 prompts, and F:245 says more over-refusal prompts come "never from the hidden remainder". That line is about the O measurement, but its words cover this draw (I). So the option needs an explicit ruling (decision 4). It also adds about one third more greedy generation to the primary read (E: prompt count).
- **Order:** per kind and stratum, the sorted hidden ids shuffled with `random.Random(derive_seed(<seed>, "stage3-hidden-subsample-v1", kind, stratum))`. Take items in that order that (a) **[rev]** pass the same per-prompt audit as the family dev bank's `banks_from.retokenize` step (the family data configs' `amendments[0]`: the family tokenizer, the prompt limit and the family's forbidden substrings) under every family tokenizer in scope, and (b) are not near-duplicates (the engine's character 5-gram Jaccard rule at the config's `max_jaccard`) of any S-pool, anchor, plant or Dolly training prompt. Count each skip by its reason.
- **One shared id set for all families,** so the hidden prompts are the same across families. One file per tokenizer family: [B] OLMo-2 and Llama-3; [C] the chosen family's file. Under [C], still draw the shared ids over both tokenizers ($0), so a later second family can reuse them.
- **Outputs:** the full file (with text) under `tmp/stage3-subsample/` (git-ignored; it goes to pods by hash, as the anchor list did, R: F 8 Oct 15:53). A text-free sealed record (ids, per-family token hashes, counts by reason, input hashes) under `.ai/inputs/stage3-subsample-<date>/`, committed.
- **Blinding:** nobody reads hidden text, or any hidden-subsample outcome, before the confirmation pre-registration is frozen. The pod smoke of this path uses a dev-sourced file (the c0 job, C3), never the hidden one.

### 3.4 Y3: B+Qi as an opt-in training field

- **Field:** `train.constrained_sft` (new, optional). It holds the per-position β values, the loss form as data, **[rev]** and a fixed objective text. The values come from S0's full read of Qi et al. (arXiv 2406.05946) (R: PLANF:134; RS:73 A9). This design does not fix them, and neither reviewer opened the paper. **No warmup** (the user's 9 Oct item (10), R: BR:21).
- **Loss text [rev].** The first draft said `train.loss` must read a new fixed text, as `LOSS_TOKEN_MEAN` does for the token mean (R: SS/config.py:102-105). That is not insert-only: `validate_recipe` fixes `train.loss` to `LOSS` in an `else` branch for every recipe without `loss_weighting` (R: SS/config.py:539-543). **Recommended:** `train.loss` keeps its X text (the base NLL term), and `train.constrained_sft.objective` holds the fixed text of the full objective, checked by an inserted line. The alternative (a new `train.loss` text) needs one non-insert edit of `validate_recipe`, a TRAINING_ONLY symbol in X (R: EP:74-77), under §5.4's route. The field enters the training identity with the train section.
- **Reference log-probabilities:** one no-gradient forward with the adapter disabled, on the same micro-batch. The initial adapter is zero (`lora_B = 0`, R: SS/README.md:165-166), so the adapter-off model is the aligned model.
- **Cost (E) [rev].** One more no-gradient forward per micro-batch: about +25–60% of training time (basis: a forward is about one third of a forward-backward step, less with gradient checkpointing; the upper end allows a second log-softmax over the vocabulary). Training is 4.1 min of a 1B job and 14.5–14.8 min of a 7–8B job (M: LEDG), so about +1–2.5 min and +4–9 min per arm.
- **Refusals:** `constrained_sft` together with `token_mean` or a warmup schedule, unless its settings define that case.
- **Memory preflight:** it includes the reference forward (R: SS/runner.py:172-197).

### 3.5 What Y leaves untouched inside the engine

- **Files:** `edits.py` (the stage-1 writers round-trip through `parse_edit`, R: BR REQ-2 (3)); `prepare.py`, `prepare_task.py`, `sources.py` (no re-preparation; every manifest stays); `textproc.py`, `loaders.py` (prompt encoding and model loading); `stream.py`, `ledger.py`, `verify.py`, `scoring.py`, `attribution.py`, `selector_view.py`, `headroom.py`, `planning.py`, `assets.py`, `common.py`, `__init__.py`. (M: these 17 plus the 5 changed files are the 22 SS `*.py` files.)
- **The import surface:** every SS symbol that `scripts/**`, `scripts/stage1/**` and `runkit/**` import keeps its exact text. A test lists them by AST and compares their hashes with X's stored inventory (`SS/configs/evaluation-path-symbols-v2-472fc7f6.json`).

### 3.6 Y4: certification tools and records

- **EP gains two insert-only options:** `--reviewed FILE` (reviewed entries for one engine pair, from a pinned JSON file) and `--strict` (no "training only" escape: every differing symbol must be new or insert-only, **[rev]** except entries named under §5.4's route). Its module-level `REVIEWED` (X's 12 entries, M: CERT-X) stays byte-identical.
- **New records** in `SS/configs/`: `engine-identity-<Y>.json`; `evaluation-path-symbols-v2-<Y>.json`; `reviewed-472fc7f6-to-<Y>.json`; `evaluation-equivalence-roundy-<date>.json`. The certificate holds three pairs: X → Y (strict), and 55253874 → Y and e49a978c → Y (X's evaluation-path rule). So every unit that a later reading may pair with a Y unit is covered. **[rev] Hidden work:** a symbol that both X and Y change (for example `validate_job`, `eval_state`, `_train_and_evaluate`, all REVIEWED in CERT-X) needs a composite entry for the e49a978c → Y pair: base at e49a978c, inserted lines = X's plus Y's, in order. Test that the composite entry equals the two single steps.
- **A bit-identity harness,** new `scripts/engine_bit_identity.py` (outside the identity). It runs fixture jobs on an X tree (extracted from the merge base with `git show`) and on Y, and compares their digests (the precedent: SS/tests/removal_digest.py:1-10).
- **Readings:** later readings pin the new certificate by SHA-256. CERT-X (`901695dc…`, M) stays as it is, for READ (R: READ:139-140, :838-847).

---

## 4. What stays bit-identical, and the T4 check

### 4.1 Bit-identical through Y

1. **Outputs.** For every recipe, data config and job kind that exists at X: the stream plan, per-step losses and gradient norms, the saved states (adapter, AdamW, RNG) byte for byte, every evaluation file byte for byte, and the registry keys. Only timed fields, paths and the code-identity record may differ (the digest definition, R: SS/tests/removal_digest.py:1-10, :18-19).
2. **Files.** Every SS file outside §3.1 item 4; the seven reused `minimal_safety` modules; every SS config, certificate and inventory that exists at X (including CERT-X `901695dc…` and `engine-identity-472fc7f6.json` `15578978…`, M: `shasum`); READ, `scripts/family_probe_reading.py`, `scripts/killtest_stage0_reading.py`; the four Gate B pinned scripts (make_anchor_answers `5a686a82…`, gate_c_representation `998231ea…`, gate_c_classifier `23a7f5f0…`, make_gateb_recipe `4823de42…`; M: `shasum`, equal to R: runkit/gate-b-olmo/gateb_rules.py:100-103); `runkit/gate-b-olmo/**`; `tmp/gate-b-olmo/**`; `.ai/inputs/gate-b-sealed-20261008/**` and `.ai/inputs/gate-b-anchors-20261008/**`; PRE; every prepared folder and its manifest; the stage-1 T1 bundle and every `scripts/stage1/**` file; EP's existing text.
3. **Identities.** Data identities (prepared manifests); the seed namespaces; the role table of the development, selector and reference roles.

### 4.2 Files Y adds and changes (none of them in the working branch before Gate B `--final`)

- **Adds:** `SS/tests/test_ss_roundy_*.py`; goldens `SS/tests/golden/*-472fc7f6.json`; the records of §3.6; `scripts/stage3/make_bank_subsample.py` with settings and tests; `scripts/engine_bit_identity.py`; a README section; **[rev]** a small certification kit for pods C1–C3 (new files under a new `runkit/` folder, not `runkit/gate-b-olmo/`; §5.3).
- **Changes (insert-only):** SS/jobs.py, runner.py, __main__.py, config.py, engine.py, README.md; EP.
- **Rewrites, lines only (decision 7):** `test_ss_gateb_certificate.py` (live symbols → X's stored inventory; its line 74 reads the live engine, R); `test_ss_baseline_reuse.py` (the Gate B pairs "for this engine" → X's stored identity); `test_ss_gateb_reading.py:1518` ("X is the workspace engine" → "X is the stored `engine-identity-472fc7f6.json`"); any other test that compares `code_identity()` with X (to check: `test_ss_gateb_runkit.py:1319-1344` builds a plan from the live identity; `test_ss_family_reading.py:823`).
- **Touches none of:** `tmp/gate-b-olmo`, `runkit/gate-b-olmo`, the Gate B pinned scripts, the sealed files, READ, CERT-X. **[rev]** M: neither READ nor the Gate B kit imports EP (grep), so EP's insert-only options cannot change a Gate B reading.

### 4.3 Why Y goes in after `--final`, not right after the last kit pod (I)

- READ's own test asserts that X is the workspace engine (R: SS/tests/test_ss_gateb_reading.py:1518). The P5 lexicon procedure at `--final` runs "the reading tests and a commit" (R: F:79, 16 Oct 11:08). With Y in the tree, that test fails in the middle of the procedure.
- `test_ss_baseline_reuse.py` says: "A later engine change fails here until it is certified again" (R: :3-4).
- The HarmBench pod and any Granite re-launch come after the last kit pod (R: PLANF:99 G12d). M: no HarmBench pod tool is in `runkit/gate-b-olmo/` (grep; only `backup_records_gateb.py` names HarmBench). I: such a pod may pack code from the tree.
- An engine edit in main during Gate B "would make later `init-wave` planning run on a different engine and a re-pack refuse" (R: PLANF:276; the pack asserts the packed code identity, R: runkit/gate-b-olmo/pack_setup.py:172-173, :188-201).

So the build happens in a hand-made workspace now. Integration waits for `--final`, its verified backups **[rev] and pods C1–C3**.

---

## 5. Certification

### 5.1 How X was certified (facts)

- **One round.** Every Gate B change went into one engine, frozen before the anchor job (R: PRE:100-105). X was integrated in commit `c9aa7ca` "from Specialized's verified final snapshot" (M: `git log`, 10 Oct 10:18 UTC).
- **Static.** EP hashes the text of every top-level symbol of every engine file and compares two engines (R: EP:1-40). A differing symbol passes only if it is in TRAINING_ONLY (each entry justified; a changed entry that writes process-global state refuses), a harmless import, or REVIEWED (exact text, pair-scoped, inserted lines only). CERT-X holds two pairs, 55253874 → X (6 changed files) and e49a978c → X (5), the TRAINING_ONLY lists and 12 REVIEWED entries (M: read of CERT-X, re-checked).
- **Tests.** `test_ss_gateb_certificate.py`: each REVIEWED symbol is its base plus inserted lines; REVIEWED is exactly what certify refuses without it; a record key cannot be REVIEWED; a hash mismatch refuses; TRAINING_ONLY equals round 6's; the tool runs under an older system python3 (R: :1-135). `test_ss_baseline_reuse.py`: the pinned certificates hold from stored inventories (R: :1-60). Readings pin their certificate by SHA-256 (R: READ:838-847; `scripts/family_probe_reading.py`:88).
- **Goldens.** Golden records were written from the base engine before the change (R: SS/tests/test_ss_attribution_result_golden.py:1-3; SS/tests/removal_digest.py:1-10).
- **CUDA.** Training equivalence 55253874 → X "rests on one check": the retrain's q and e1 adapter fingerprints against P1101's (R: PRE:106). They were equal (R: F:77).
- **Environment rule.** Every Gate B unit shares the 13 environment fields and the lock with R_1101 (R: PRE:107).
- **Re-checked today.** `python3 -I -B scripts/evaluation_path.py certify SS/configs/evaluation-path-symbols-v2-e49a978c.json` gives `evaluation_path_unchanged: true` and an empty `evaluation_path_symbols_changed` (M; the reviewer re-ran it at about 21:55 UTC with the same output). The recomputed code identity is `472fc7f6…` over 29 files (M; reviewer re-computed with the engine's `canonical_json` form).

### 5.2 The procedure for X → Y

| Step | What | Owner | Pass condition |
|---|---|---|---|
| Y-0 | Workspace: a hand-made copy of the working branch, with a SHA-256 manifest (memory `manual-workspace-preparation`) | lead | manifest recorded |
| Y-A0 | Golden digests written **at X**, before any engine edit: a0; a group arm; edit arms (remove, add, rewrite, combined); a continuation; eval-state; anchor-bank attributes; a token-mean + warmup-cosine recipe; the tiny OLMo-2 and Llama fixtures | builder | hand-over 1; the lead checks that the goldens name X |
| Y-B | Build Y1–Y4 under §3.1 | builder | — |
| Y-S | `EP certify --strict --reviewed …` for X → Y; the certificate for the three pairs | builder | every changed symbol is new or insert-only (or named under §5.4); records unchanged |
| Y-T | Tests (§6.1); the existing suites | builder | all pass; counts recorded; skips named |
| Y-M | Mutants (§6.2) | builder | each killed by a real test failure, or justified |
| Y-V | Independent verification (a read-only workflow), one fix round | lead | no blocking finding |
| Y-F | Freeze Y by hash (decision 3); a FOCUS record. **[rev]** Apply the §0 split rule here if Y1/Y2 are not verified | lead | Y's code identity recorded |
| Y-D | The hidden-subsample draw (§3.3), counts only; seal and commit the text-free record | lead | counts as planned; zero near-duplicates kept |
| Y-C **[rev] (moved before Y-I)** | After Gate B `--final` and its backups: pods C1–C3 pack Y from a side-branch worktree at the frozen hash, never from the working branch; C4 if decision 9 is "reuse" (later, in block 0) | lead | §5.3 |
| Y-I | After C1–C3 pass: integrate by explicit paths (memory `explicit-git-add-paths`); recompute Y's identity in the main checkout; re-run the suites | lead | identity equals the frozen hash |
| Y-R | FOCUS record: certificate SHA-256, pod results, the engine each later stage uses | lead | — |

**[rev] Why certify before integrating.** Every kit packs the main checkout's HEAD and asserts the packed engine identity (R: runkit/gate-b-olmo/pack_setup.py:172-173, :188-201; I: later kits copy this). If Y were integrated first and C1 then failed, "stage 1 stays on X" (§5.4) would need a revert commit before any X pod could pack. Certifying from a side-branch worktree keeps X in the working tree until Y passes. If the lead prefers integration first, pre-write the revert by explicit paths and record it in the brief.

### 5.3 Pods

| Pod | Model | What | Pass | Cost (E) |
|---|---|---|---|---|
| C1 (required) | OLMo-2-1B | Re-run one complete, environment-matched Gate B unit with evaluation (for example R_1101, as PLAN-S:215 names) on Y as `replicate_of` (the engine's determinism control, R: SS/jobs.py:290-303). **[rev]** The pod must carry that unit's registry line and run-folder string, or `replicate_of` refuses (R: SS/jobs.py:299-300); it uses recipe S and the Gate B manifest. PRE's rule "Never re-run a completed arm" (R: PRE:108) governs Gate B's attempts; this replicate runs after `--final` in its own run root that no Gate B reading opens. FOCUS records it as outside Gate B (decision 16) | adapter and optimizer fingerprints, `steps.jsonl`, every evaluation file and the summary without timings: byte-identical | ≤ 49 min arm + ≤ 26 min overhead (R: F:77, 16 Oct 13:21) ≈ 1.25 h ≈ $2.2 |
| C2 (required, same pod) | OLMo-2-1B | B+Qi to checkpoint q at seed 1101, training only | finite; at step 0 the reference log-probabilities equal the adapter-off forward; time recorded. No evaluation, so no outcome is read | +0.2 h ≈ $0.4 |
| C3 (required, **[rev] same pod**) | OLMo-2-1B | The c0 lean job on Y with a dev-sourced subsample file: the pod smoke of Y2 and the c0 measurement in one job. **[rev]** The first draft put C3 inside the 7–8B block 0 (9 Nov), which is after the planned certification date and on a pod of another model. On the C1 pod it is measured before stage-1 block A, which lists the c0 job (PLAN-S:222) | completes; evaluates only the listed items | +0.25 h ≈ $0.45 (E: 4.1 min training and about 20% of a 48 min evaluation, M: LEDG 1B) |
| C4 (only if decision 9 = reuse) | [B] OLMo-2-7B and Llama-3.1-8B; [C] the chosen family | Re-run one side-project a0 unit per reused family on Y as `replicate_of`, with full evaluation | as C1 | as one arm on a shared block-0 pod: OLMo $2.8–3.6, Llama $3.3–4.1 (RP:40); more on its own pod |

**[rev] Kit cost.** No kit exists for C1–C3. A small certification kit (registry carry-over, recipe S, the 13 environment fields, packing from a named commit) is about 2–4 h of build (E: the stage-1 kit B15 is a natural home) and $0.

### 5.4 Acceptance, and rules fixed now for a failure

**Accept Y when:** strict certify passes (with any §5.4 training-only entries named); the goldens reproduce; the suites pass with counts recorded; every named mutant is killed or justified; C1, C2 and C3 pass.

- **If C1 differs:** no Y unit is paired with an X unit. Y is not integrated; stage 1 stays on X. B+Qi runs with its own a0 at the same seeds on Y (E: +3–6 1B a0 runs, about $5–10). Confirmation is not affected, because it is self-contained on Y. The lead checks the environment fields first.
- **If C4 differs for a family:** do not reuse that family's side-project units. Run its a0 seeds on Y.
- **[rev] If strict certify fails only because B+Qi needs non-insert edits of TRAINING_ONLY symbols** (assumption 1; for example `validate_recipe`, `accumulate_gradients`, `_train_segment`): accept them by name, each with its reason, if every Y-A0 golden and C1 are bit-identical. This is the route X itself took for training equivalence (R: PRE:106; M: 24 removed runner.py lines in c9aa7ca). The first draft sent this case to "C1 differs" (own a0 runs). The lead chooses (decision 17).
- **If strict certify fails for an evaluation-path symbol:** treat it as "C1 differs".

---

## 6. Test and mutation plan

### 6.1 Tests (CPU; the tiny Qwen2, OLMo-2 and Llama fixtures; nothing downloaded)

- **Y1 access.** Each refusal of §3.2, raised before any model loads (a fixture loader that fails if called). Confirmation and development trajectory keys differ. A start at a seed already used by another role refuses. eval-state from a confirmation run refuses another code identity. Attribution on confirmation states refuses. **[rev]** The X role tables and `CONFIRMATION_ROLES` are byte-identical to X.
- **Y2 files.** Each check of §3.3 both ways: a changed byte; a non-canonical file; another tokenizer; another manifest; an id not in the source; a changed non-token field; a repeated id; wrong counts; the development role with a hidden source; a hidden source without the switch; the selector and reference roles. The existing token check catches a wrong token hash in a subsample item. A bank with harm items only, and one with harm and over-refusal items and no ARC, evaluate, and their summary keys are stated. The c0 path evaluates only the listed items. No error message holds fixture text (a scan for the fixture strings).
- **Y3 B+Qi.** The loss on a hand-computed two-token case. β applied at the right response position. The reference forward runs with the adapter off and no gradient. At step 0 every per-token log-ratio is 0. Undefined combinations refuse. The training identity changes with the field. A recipe without the field takes the X path (the harness).
- **Y4 bit identity.** Every Y-A0 golden reproduces byte for byte after the timed fields are stripped. The X-tree against Y-tree harness on the same fixtures.
- **Certificate.** Strict certify passes for X → Y. Each reviewed entry is insert-only. An edited line refuses. A new engine file refuses. A training-only change refuses in strict mode unless it is named under §5.4. The records are unchanged. X's stored certificate still certifies from stored inventories. The import-surface test (§3.5). **[rev]** Composite e49a978c → Y entries equal X's step followed by Y's step.
- **Gate B rewrites.** Each rewritten test passes, and fails on a forged stored record.
- **The draw script.** Deterministic twice; strata counts; skips counted by reason; one id set across tokenizers; a synthetic hidden fixture written by the test; no text in the record; a wrong manifest refuses.
- **Suites.** Engine + minimal_safety (1,191 passed, 3 skipped at the brief's HEAD, R: BR:46), Stage B 172, durability 260, judges 552 + 2 skipped, and the stage-1 suite: all as at the merge base, plus the new tests. Skips are not passes.

### 6.2 Named mutants (each must be killed by a real test failure)

- **Y1:** the role accepts a development seed; accepts the full hidden bank; accepts the selector bank; runs without the switch; runs with a null code pin; the role dropped from the trajectory key; attribution allowed on confirmation states; eval-state without the code-equality check; an edit arm on the held-out split accepted; **[rev]** the new role added to `CONFIRMATION_ROLES` or a role table.
- **Y2:** a changed byte accepted; a non-canonical file accepted; the tokenizer check removed; the manifest check removed; the membership check removed; the non-token field comparison removed; a repeated id accepted; counts not checked; the development role accepts a hidden source; the token check skipped for subsample items; **[rev]** a subsample job evaluates the whole source bank.
- **Y3:** β one position late; the β list reversed; the reference forward with the adapter on; a gradient through the reference; the log-ratio sign flipped; the constrained loss used when the field is absent; a warmup left on; the preflight without the reference forward.
- **Y4:** strict mode accepts an unnamed training-only change; an edited (not inserted) line accepted; a new engine file accepted; the harness ignores the saved states; the harness strips a field that is not timed; a rewritten Gate B test reads the live engine again.
- **Draw script:** a stratum one short (for example 199 harm, or 49 per over-refusal stratum if decision 4 adds them); the near-duplicate test at > instead of ≥; ids drawn per family instead of shared; a skip not counted; hidden text in the record; **[rev]** the dev bank's per-prompt audit skipped.

**Runner rules** (memory `mutation-runner-validity`; R: ADD:312 item 6): an unmutated baseline with exactly the runner's command and temp layout; whole test files, no `-x`; `--junitxml`; a per-mutant timeout; `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` stripped. A run is **invalid**, never a kill, on a collection, setup or teardown error, a timeout, an exit code outside 0–1, or a JUnit test count unlike the baseline's. Record the tested tree's {path: SHA-256}, the engine identity, the pytest version, each mutant's target-file hash before and after the patch, and the failing test names.

---

## 7. Who builds it

- **Builder (recommended): the Specialized Implementation chat.** It built engine X and its certificate (R: commit `c9aa7ca` message). Hard tasks are routed there, and its model and effort are not changed (memory `specialized-chat-routing`). Not the stage-1 builder session: ADD L1 binds it to the stage-1 build ("This session builds everything", R: ADD:19; F:75). The routing is the lead's and the user's call (decision 8). **[rev]** PLANF also names Specialized as the default builder of W3 and of S3 (R: PLANF:113, :136; BR "Who builds"). One chat builds serially, so Y competes with S3 for the same builder and for plan usage (RP:165 notes the usage is not checked). Y takes B12 and B17 out of S3 (decision 18), which shortens S3 by about 0.5–1.5 days + 2–4 h (R: RS:102, :107).
- **Workspace:** a hand-made copy of the working branch under `tmp/claude-workspaces/engine-round-y-<date>/`, with a SHA-256 manifest. Builder-owned: only the files of §4.2. Read-only: everything else.
- **The lead:** the decisions, the brief, the counts-only encode run and the draw, the verification workflow, the freeze record, pods C1–C4, the integration by explicit paths, the FOCUS records.
- **Hand-over points:** (1) after Y-A0, before any engine edit; (2) after the build, with suites and mutants; (3) after the fix round.
- **Effort (E) [rev]:** build 14 / 23 / 36 h (best / likely / slow); verification 3 / 8.5 / 15 h. Basis: X's engine part was 79 added lines in jobs.py and 153 changed lines in runner.py (129 added, 24 removed) with 12 reviewed symbols (M: `git show --numstat c9aa7ca`; CERT-X); round 5's token-mean option took 1.5 h (R: RS:102); B12 was estimated at 0.5–1.5 days (R: RS:102); B17 at 2–4 h (R: RS:107); verification as for the stage-1 build (R: PLANF:137). **[rev]** +2–4 h over the first draft for the six early-return entry points (§1.2 item 1b), the composite certificate entries and the certification kit.

---

## 8. Schedule against the re-plan

Dates are 2026. Re-plan dates are its latest starts (RP §5). Y's dates are **E**: build effort from §7; Gate B durations from PLANF:95-99 (wave 1 to verdict 5–12.5 h, extension 3–6 h, length control 2.5–4.7 h, HarmBench and `--final` 1–1.5 h), plus night pauses.

| Date | Y step | Re-plan step it serves |
|---|---|---|
| 17–18 Oct | The lead reads this design and takes the decisions. S0 (the Qi read) gives the shape of B+Qi's settings | — |
| 18–19 Oct | Brief; workspace; Y-A0 goldens | — |
| 19–25 Oct | Build Y1–Y4, tests, mutants (**[rev]** later if the same builder first finishes S3, §7) | — |
| 25–27 Oct | Verification and one fix round; freeze Y by hash (decision 3), or the §0 split | the stage-1 DRAFT can name Y's (or X′'s) hash |
| ≤ 27 Oct | — | Gate B wave 1 (RP:100) |
| about 28–30 Oct | — | Gate B wave 2, extension, length control, HarmBench, `--final` |
| `--final` + ≤ 1 day | **[rev]** Pods C1–C3 from the side-branch worktree; the subsample draw and seal | — |
| + ≤ 1 day | **[rev]** Integrate Y; certificate; suites | the stage-1 freeze (needs Y3 committed, F:225) |
| about 30 Oct–2 Nov | **Y certified** | 3 Nov: stage-1 block A (on Y if certified, else on X; decision 6) |
| 9 Nov | C4 inside 7–8B block 0 (**[rev]** C3 moved to the C1 pod) | 7–8B block 0 (RP:102) |
| 16 Nov | — | Alpaca Gate A (RP:103); needs no engine change if decision 13 holds |
| **20 Nov** | The 7–8B pre-registration names Y, the subsample record and the contrast choice rule. **Hard latest for Y1 and Y2's hidden path** | the B-or-C choice (RP:104) |
| 23 Nov / 3 Dec | B+Qi at 7–8B in block B | RP:105-106 |
| 14 Dec | Confirmation on Y | RP:108 |

**Slack (E) [rev].** For Y3 (B+Qi): about 0–4 days, from the expected certification (30 Oct–2 Nov) to stage-1 block A's latest start (3 Nov), because the stage-1 freeze needs Y3 committed (F:225) and is a user step "in the user's day" (PLANF:140). For Y1 and Y2's hidden path: about 18 days to 20 Nov. **The early-Gate-B case:** wave 1 waits only for the W1 build (W3 12 / 22 / 36 h + W4 3 / 8.5 / 15 h, R: PLANF:113-114) that started on 16 Oct, so wave 1 may start well before 27 Oct (I). Then Gate B may end before Y freezes (25–27 Oct), and Y sets the stage-1 date. The §0 split rule (X′ = Y3 + Y4 + Y2's dev path first) is the remedy.

**If Y is late (rules to fix now) [rev]:**
- After the stage-1 freeze is otherwise ready: apply the §0 split; X′ goes first.
- If even X′ is late for 3 Nov: block A runs on X; it needs nothing new except the c0 job, which then runs on X′ when certified. The stage-1 freeze still waits for X′, unless the user amends F:225 (for example: "B+Qi committed before block B"). That amendment is the user's call (decision 1).
- After 9 Nov: 7–8B block 0 runs on X. Its A1 pass then also runs on X (R: SS/runner.py:874-878). The 7–8B B+Qi arms later run on Y with their own a0.
- After 20 Nov: the 7–8B pre-registration cannot name a certified confirmation engine. Then confirmation uses Y-zero (§1.1 A1) with its deviation recorded, or slips.

---

## 9. Option-specific parts and money

### 9.1 What B and C share, and what differs

- **Shared:** all of Y1–Y4; pods C1–C3; the shared id draw; the schedule to 20 Nov.
- **[B]:** two family subsample files; C4 on both families if decision 9 is "reuse"; confirmation of at most 2 contrasts on each of two families (RP:75); 32B is possible (decision 10).
- **[C]:** one family file; C4 on one family. RP says the family is fixed before the noise block (RP:82); Y does not depend on that choice.
- **[A]** (not recommended by RP): confirmation at 1B, the same Y, the OLMo-2 file.

### 9.2 Money (all E)

- **Pods:** C1–C3 on one 1B pod about 1.7 h ≈ $3.0, or $3.7 with RP's +20% allowance (RP:41). [B] about $9–13; [C] about $6–8 with C4 (§5.3). **[rev]** May they run before a funding event? The user's open ruling (PLANF:234 item 14; no record of an answer in F, M: grep).
- **The second evaluation [rev].** RP counts confirmation at 36–48 FRE for [B] and 18–24 for [C] (R: RP:76). I: that is one evaluation per unit (2 contrasts that share R give 3 arms × 6 seeds = 18 units per family; 24 with a fourth arm), and RP's $140–230 (RP:108) matches 1.0 FRE per unit at $2.8–4.1 × 1.2. PLAN-S priced a unit with both reads at "1.25 × an arm" (R: PLAN-S:59; PLAN-S:227, $58–95 at 1B). **M basis:** evaluation is 83% (OLMo-2-7B, 75.3 of 90.4 min) and 88% (Llama-3.1-8B, 107.3 of 122.1 min) of a 7–8B job, and 92% of a 1B job (48.0 of 52.2 min) (LEDG stage sums). So a second full dev read adds about **0.85 FRE**. With the default 200-harm hidden read (§3.3), the primary read itself is about 0.15–0.2 FRE lighter than a full dev read (E: one third of greedy generation, 57–58 min, for the 100 over-refusal prompts), so the net addition is about **0.6–0.7 FRE**. Range used here: **+0.6 to +0.85 FRE per unit**.
  - **[B]:** +22–41 FRE, about **$73–200** (36 units × 0.6 FRE to 48 units × 0.85 FRE, at $2.8–4.1 per FRE, × 1.2).
  - **[C]:** +11–20 FRE, about **$36–100**.
  - At 1B ([A]), PLAN-S's $58–95 would rise by about 70% for the same reason (E).
- **Choices (decision 5):** (a) both reads, as F:252 says; (b) the hidden read only: RP's cost holds, but the paper cannot separate "new seeds" from "new prompts", and with the 200-harm default there is no O or ARC read at confirmation; (c) the hidden read plus a lean dev read (200 harm prompts, greedy only, PLAN-S:202's C-lean form): **[rev]** about +0.35–0.45 FRE per unit (E: 200/300 of greedy generation plus judging, LEDG), but it measures a different quantity (no sampled answers, no O), so it is not the same-measure comparison that (a) gives. Whatever is chosen, "drop the dev read" can go on RP's cut list (RP:138).

---

## 10. Decisions needed

1. **Scope [rev]:** one round Y with Y1–Y4 and the §0 split rule (recommended); or two rounds as planned (A2: X′ before the stage-1 freeze, Y before 20 Nov); or Y-zero for confirmation (only if B+Qi leaves the engine plan). If even X′ cannot be ready for 3 Nov: whether to amend F:225 to "B+Qi committed before block B" (the user's call).
2. **Merge point [rev]:** after Gate B `--final`, its backups **and pods C1–C3** (recommended), not only after the last kit pod.
3. **Build now in a workspace, and freeze by hash before the merge,** so the stage-1 freeze can name Y; and whether a commit on a side branch (not the working branch) is allowed under T4. **[rev]** RP says "build after Gate B's last kit pod" (RP:116); T4's text covers engine files only (BR:65). This is the lead's reading of T4.
4. **The hidden subsample [rev]:** 200 harm prompts, no over-refusal, no ARC, one id set shared across families (recommended; F:252, PLAN-S:215); or add 100 over-refusal prompts (50 per stratum), which needs the user's ruling under F:245 and F:252. Sealed by the stage-1 freeze (recommended) or by the 7–8B pre-registration.
5. **Confirmation reads:** both banks as F:252 says (about +0.6–0.85 FRE per unit, [B] +$73–200); the hidden read only; or hidden plus a lean dev read. This changes an adopted design point (F:252), so it is the user's call.
6. **Which runs use Y:** every pod launched after Y is certified (recommended: one engine in the tree, simple packing); or only B+Qi, c0 and confirmation (keeps the primary P1–P6 arms on X and outside Y's risk, but needs the stage-1 kit to pack from a named commit).
7. **Gate B tests that need the live engine to be X:** rewrite them to read the stored X records (recommended); or keep them X-only and run them at a Gate B tag.
8. **Builder:** Specialized Implementation (recommended) or another chat; verification by the lead's read-only workflow. **[rev]** Order against S3 if the same chat builds both.
9. **Reuse of the side-project 7–8B X units** (RP decision 5): if yes, a $0 environment comparison first, then pod C4 per reused family.
10. **32B [B only]:** no engine change in Y. If the 32B smoke test needs one, drop 32B for ICML (recommended) rather than run a second round in December.
11. **B+Qi interface:** the β values, the loss form and the objective text as recipe data (recommended), so S0's settings do not hold up Y's freeze; `train.loss` keeps its X text (§3.4).
12. **Part C model-agnostic [rev]:** a generic version as new files after the W1 commit, under the 7–8B pre-registration, with tests on the tiny OLMo-2 and Llama configs (recommended); or inside the W1 build now, which changes BR REQ-3 and REQ-10 and adds work on wave 1's critical path (wave 1 waits for the W1 build, BR:21 item (6)). The lead's call.
13. **Alpaca:** a derived Dolly-format file with sealed pseudo-units, so no engine change. The Alpaca note must decide this before Y freezes (about 27 Oct).
14. **[rev, new] Certification pods before a funding event** (about $3–4 at 1B): the user's open ruling (PLANF:234 item 14).
15. **[rev, new] Safe LoRA (B11):** confirm it uses the B10 pattern outside the engine (PLANF:137). If it must go through eval-state itself (F:154's wording), it is an engine change and joins Y before Y freezes.
16. **[rev, new] C1's unit:** an R_1101 replicate after `--final` in its own run root, recorded as outside Gate B (PRE:108's re-run rule governs Gate B attempts; PLAN-S:215 names this re-run); or a paired X/Y run of a new 1B unit on one pod (avoids re-running a Gate B arm, costs about +0.8 h ≈ +$1.5 and a two-tree kit).
17. **[rev, new] Training-only route:** accept named non-insert edits of TRAINING_ONLY symbols if goldens and C1 are bit-identical (recommended, X's route); or require separate a0 runs for B+Qi (about $5–10 at 1B, more at 7–8B).
18. **[rev, new] The S2 brief:** B12 and B17 leave the S1 build list (PLANF:135-137) and go into Y; B10, B11, B14–B16 stay in S3.

---

## 11. Limits and unresolved concerns

- I built nothing and ran no test suite. The only commands that touched engine code were the read-only EP `symbols` and `certify` runs and the identity recomputation (§12).
- I did not open Qi et al. The insert-only fit of B+Qi (assumption 1) is untested, and its loss form and constants are S0's.
- I did not open the hidden bank (by rule). Its per-stratum counts and the encode pass rates are unknown until the lead's counts-only run.
- The claim that Llama blocks have no post-sublayer norm, so LARF-style hooks need another module (N10), is I from the HF architecture. Check it on the tiny Llama config in `test_ss_family_models.py`.
- The model card does not state the 32B layer count, key/value heads or tokenizer. Nothing in this engine is tested on an H200.
- The dates depend on Gate B's wave-1 start and on night pauses. They are E. **[rev]** The early-Gate-B case (§8) is the more likely one (I), and it makes Y, not Gate B, the stage-1 bottleneck unless the split rule is used.
- Whether the HarmBench pod packs code from the tree is I (no tool for it was found in `runkit/gate-b-olmo/`, M: grep).
- My reading of RP's confirmation FRE as "one evaluation per unit" (§9.2) is I. RP's author should confirm it. **[rev]** The M ledger fractions make the gap real whichever reading is right; only its size depends on decision 4.
- The engine's registry has no lock and relies on one serialized scheduler (R: SS/jobs.py:26-31). Confirmation pods must keep one registry per pod, as Gate B does.
- **[rev]** The 0.6–0.85 FRE range assumes greedy time scales with prompt count; over-refusal answers may be shorter or longer than harm answers (not measured per kind).
- **[rev]** At about 21:58 UTC the Mac's disk was full (M: `df -h /` showed 100% and 118 MiB free; two Bash calls failed with ENOSPC). At 22:06 UTC 4.6 GiB were free (M). Pod retrievals and backups land in the main checkout's `tmp/`, so the lead should check free space before the next pod.

## 12. Process (for the lead)

- **Changed files:** this file only (first draft, then the review's in-place revision).
- **First draft, commands run (all exit 0):** `date -u` (twice); `git rev-parse`, `git status --porcelain`, `git log`, `git show --stat` in the main checkout; `sed`, `grep`, `ls`, `wc` and `python3 -I` reads of the files cited above (configs by keys and counts only); the code-identity recomputation (the first attempt used a non-canonical JSON form and gave another hash; the second, with the engine's `canonical_json` form, gave `472fc7f6…`); `python3 -I -B scripts/evaluation_path.py symbols` (output to my scratchpad) and `certify` against the e49a978c inventory; `shasum -a 256` of the certificates and identities; one WebFetch of the OLMo-2-32B model card.
- **[rev] Review, commands run:** `date -u` (21:50, 22:06 UTC); `git rev-parse`, `git status --porcelain`, `git log -3`, `git diff --stat fc85fda 19c2d28`, `git diff` of ADD, `git show --numstat c9aa7ca` (exit 0); `sed`/`grep`/`python3 -I` reads of FOCUS, BR, ADD, PLANF, RS, PLAN-S, PRE, SS/jobs.py, config.py, runner.py, prepare.py, prepare_task.py, common.py, sources.py, README.md, EP, READ, `scripts/family_probe_reading.py`, `runkit/gate-b-olmo/pack_setup.py`, `gateb_rules.py`, four SS test files, the stage-1 workspace's settings JSON (keys only), CERT-X (keys and counts only), the family data configs and four recipes (keys only); `python3 -I -B scripts/evaluation_path.py certify …e49a978c.json` (output unchanged); the code-identity recomputation (`472fc7f6…`, 29 files); `shasum -a 256` of the four pinned scripts and two certificates; stage-time sums of the three LEDG ledgers (stage names and seconds only); `ls` of the Hugging Face cache snapshot folders (file names only); `df -h /`. Two Bash calls failed with ENOSPC (disk full) and printed nothing. One WebFetch of the OLMo-2-32B model card.
- **Not opened:** `selector.jsonl`, `hidden/`, any held-out file, `rows.jsonl`, dataset rows, prompts, answers, anchor text, tokenizer contents, secrets.
- **Acceptance criteria of the task:** design written (passed); T4 statement per file (§4.2, passed); build nothing (passed); every claim labelled (passed, to my reading); the B/C split marked (passed). Review: each M and R claim checked against its source (passed for those listed in §13; line numbers corrected where they drifted). Nothing tested on hardware.
- **Questions from GPT:** none were asked in this brief.

## 13. Review changes

The review checked every M and R claim it could reach, the arithmetic, and the frozen rules. Most claims held: the CERT-X facts (2 pairs, 6 and 5 files, 12 REVIEWED), the certificate and pinned-script hashes, X's identity over 29 files, the `certify` output, the tokenizer fields of the 7B and Llama-1B recipes, the bank sizes, the seed namespaces, c9aa7ca's line counts and time, the 32B card, and the FRE and dollar arithmetic of §9.2's first form. Changes:

1. **HEAD** `fc85fda` → `19c2d28`; F line numbers unchanged (M).
2. **Deadline conflict (F:225, PLANF:137-140).** B+Qi must be committed before the stage-1 freeze, so Y3's slack is about 0–4 days, not 18. Added the pre-set split rule (§0, decision 1) because D5's record counts engine round Y before stage 1 as critical-path work (F:78).
3. **Hidden subsample size (F:252, F:245).** Default changed from 200 harm + 100 over-refusal to 200 harm prompts; the 100 over-refusal prompts are now a user option (decision 4).
4. **Insert-only feasibility.** New assumption 1b (role tables are one-line literals; three refusals in validate_job, check_run_access, load_prepared). Assumption 1 gained evidence (validate_recipe's else branch; X removed 24 runner.py lines). §3.4 keeps `train.loss` unchanged. New §5.4 training-only route (decision 17). Role renamed away from plain `confirmation` (it clashes with X's `CONFIRMATION_ROLES`).
5. **Certification order.** Pods C1–C3 now run from a side-branch worktree before integration, so a C1 failure leaves X in the working tree (packing reads HEAD, pack_setup.py:188-201). C3 moved onto the C1 pod; the first draft scheduled it on 9 Nov on a 7–8B pod, after its own acceptance date.
6. **C1 details.** Registry carry-over for `replicate_of`; PRE:108's re-run rule addressed (decision 16); a certification kit added to the cost (2–4 h).
7. **Cost gap re-based on M ledgers** (evaluation is 83–92% of a job) and on PLAN-S:59's 1.25× pricing. [B] +$73–200, [C] +$36–100; option (c) re-estimated at +0.35–0.45 FRE and marked as a different measure.
8. **Citations corrected.** RS:101 does not say "outside the engine identity" (PLANF:137 does); F:154 may need B11 inside the engine (decision 15). PLAN-S:277's second option includes the selector bank. B17 was planned outside the engine (PLANF:137); moving it in changes the S2 brief (decision 18). Several line ranges tightened.
9. **New decisions:** 14 (certification pods before funding, PLANF:234 item 14), 15–18 above. Decision 12 now defaults to a generic Part C after the W1 commit, to keep work off wave 1's critical path.
10. **Builder contention** with S3 (same default chat) and plan usage added (§1.2 item 7, §7); build effort raised to 14 / 23 / 36 h.
11. **Mac tokenizers are cached** at the pinned revisions (M), so the draw needs no download.
12. **Disk-full event** at about 21:58 UTC recorded for the lead (§11).
