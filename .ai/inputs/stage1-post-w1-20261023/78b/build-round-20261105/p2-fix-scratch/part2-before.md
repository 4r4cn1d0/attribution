# 7-8B pre-registration, Part 2 (DRAFT, 6 Nov 2026): the scorer section; the other sections follow before block A

**Status: DRAFT. The scorer section (§1) is complete; every other section is marked "to be written before block A's first pod".** The scorer section is committed before any 7-8B scorer output is read (A10); the rest of Part 2 is written and the whole file frozen before block A's first pod. The freeze is as Part 1's: a commit by explicit path, its SHA-256 in FOCUS, `scripts/stage1/commitments.py check` (ADD A10; RUL ruling 14; P1 §14). This text authorizes no run and no spend: every 7-8B pod starts only on new money in the account (MONEY `lead_reading[0]`; RUL header). A later change to a committed part is a dated amendment in a new file, never an edit of this one.

Written 2026-11-06 (clock read with `date -u` at 14:24 and 14:33 UTC) by a Track P2 worker of round 4 of the 7-8B $0 build, for the main-study lead (General Implementation X), from the sources below. Read-only on the repository except this file. No pod, no spend, no network, no install, no download, no agent. No judge output, answer, generation, sample, prompt text, `selector.jsonl` or `hidden/` file was opened. **Nothing here is a new decision.** Where the rulings leave an item open, §14 names it and does not settle it.

**Labels.** **M** = measured (the command follows). **R** = read (path:line, or a FOCUS entry by title and recorded time). **E** = estimate (the basis follows). **I** = inference.

**Option marks** (as Part 1). **[B+C]** = shared by options B and C. **[B]** = only under B. **[C]** = only under C.

## Short names

Part 1's short names hold (P1 "Short names"). Added or restated here:

- **P1** = `research/experiments/2026-11-05-78b-preregistration-part1.md`, Part 1, frozen 5 Nov 2026 (SHA-256 `b682513f78c3a3f8a92045c97104876507a28abfc15b6b9e560cc2ee86706b12`; M: `shasum -a 256`, 6 Nov). **ERR** = its erratum 1, `…-part1-erratum-1.md` (`4d94162c355ad8b2…`; M).
- **RUL** = `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md` (`65e477b0ac1e772c…`; M). **ADD** = `…/78b/lead-rulings-part1-addendum-20261105.md`, at its freeze version `ff3498768bf3432f…` (M; ERR). **PP** = `…/78b/lead-rulings-part2-prep-20261105.md`, the lead's rulings PP1-PP16 for Part 2 and the kit (`47dc1e74b9a2c6dc…`; M). They govern this text; PP governs where it is later than RUL and ADD.
- **PLAN**, **CHECK**, **P78**, **KCR**, **PR4**, **DOSE**, **MONEY**, **SEAL**, **SS**, **BR**, **FOCUS** as P1 (PLAN `f39238d352ca3922…`; CHECK `1bc40aa4c842ff9b…`; P78 `e6a73c92ef97e107…`; KCR `9884bd17df4679d0…`; PR4 `7eccf9e9bed1e733…`; M, 6 Nov).
- **SC** = `scripts/scale78b/SCORERS-78B.md`, the scorer layer's own map (`8c92a892…`). **PINS** = `scripts/scale78b/settings/pins_78b.json` (`428b7577…`). **WRAP** = `scripts/scale78b/scorers_78b.py` (`108f4425…`). **MAKER** = `scripts/scale78b/make_scorer_settings_78b.py` (`7c8f2491…`). Full hashes in §1.17.
- **RK** = `runkit/stage1-78b/rules_78b.py`, the 7-8B kit's rules, at HEAD (`57ad4148…`; M).
- **HEAD** = commit `d203070` (`d2030706d93c7417…`), the base of this round. **WSM** = track M's worktree of round 4 (`…/scratchpad/b78/ws-m`, at HEAD plus track M's changes under `scripts/scale78b/`). The scale78b hashes in §1.17 are WSM's; the lead merges them by explicit path (track M's report, job 1).
- **F** = a family: `olmo2-7b` (OLMo-2-7B) or `llama31-8b` (Llama-3.1-8B). **MAIN_F** = F's main recipe. **S_78_F** = F's recipe S_78. **BANK_F** = F's anchor file. **P_F** = F's prepared set.
- **θ0** = the untuned model of a family (the policy with its adapter disabled).

---

## 0. Blinding line (EM-5; P1 §0's form)

**To be written before block A's first pod.** It adds N's values seen (r_F,j, σ̂_F, σ̂_pool, mean r_F, E of Llama a0-1103; P78 EM-5; P1 §0 last paragraph, §14 item 13), in P1 §0's form.

**What the scorer section's authors saw when it was written (6 Nov 2026).** P1 §0's list, unchanged, and these items since P1's freeze:

1. **Track F's S1 check on OLMo-2-7B** (PP5): all 48 S1 rows encode within the 7B main recipe's limit, and REQ-7's writer reproduces stage 1's `add_s1.json` exactly (verdict record `9b340bf5…`; R: PP5; M there). These are encode counts and hashes, not outcomes. **Use here:** §1.9.
2. **The rulings PP1-PP16** (5-6 Nov 2026). They read code, files, hashes, kind names, caps and the 1B settings' form (§1.18).

What the authors have **not** seen: any 7-8B scorer output (no anchor file, no untuned answer, no representation row, no scan, no score, no edit file of A1, L1, S3 or S4 at 7-8B exists); any value of N (N has not run). R: FOCUS "THE 7-8B KIT'S BLOCK-0 SUBSET IS MERGED", recorded 2026-11-06T13:31 UTC ("The balance read 6 Nov 07:30 UTC: $20.21, nothing running"; "No pod, no spend").

---

## 1. The scorer section [B+C] (complete; committed before any 7-8B scorer output is read)

### 1.0 What this section fixes

It fixes, per family, the rule, the code and the settings of every scorer that builds a 7-8B arm's edit file or feeds one: **A1, L1, H1, S1, S3, S4 and the dose lists S4_96 and S4_192**, and the pre-block-A kinds that serve them: the **anchor job**, the **untuned-answers pass**, **`rep_pass`**, **`a1_pass`**, the **L1 scan**, the **classifier** and **c0**, and the **untuned units' O and L evaluation** (CHECK M1). It names the engine for each kind, each kind's E cap, every pin that is still null with the event that fills it, and the SHA-256 of every script and settings file used. It is P1 §14 items 1-2 written out (P78:367, :413; CHECK C1, M4).

It does not fix: how the arms are read, the limits O and L and their bank, the references, the judges, the costs, the confirmation, Alpaca (§3-§11, to be written). The study question, the arms, U and the frozen 1B model are PR4's (P1 §1).

**Basis of the whole section (R: SC §1; P78:357; P1 §11).** The 1B scorer scripts under `scripts/stage1/` are model-agnostic in code (the layer count, hidden size and final norm come from the loaded model; the token limits from the recipe; the codec from the engine's loaders; R: `scripts/stage1/representation_pass.py:1-25`). What ties them to OLMo-2-1B is their settings files and each script's literal `SETTINGS_SHA256`. So the 7-8B layer copies no scoring code. It derives per-family settings in the 1B files' own schema and runs each unchanged 1B script's `main()` through one wrapper (§1.2). The 1B scripts stay byte for byte (§1.17 table B).

### 1.1 The shared inputs per family (R: PINS `families`; P1 §1, §2.1; M where marked)

| Item | OLMo-2-7B | Llama-3.1-8B |
|---|---|---|
| Model and revision | `allenai/OLMo-2-1124-7B-Instruct` @ `470b1fba1ae01581f270116362ee4aa1b97f4c84` | `meta-llama/Llama-3.1-8B-Instruct` @ `0e9e39f249a16976918f6564b8830bc894c89659` |
| `config.model_type` (transformers 4.56.2) | `olmo2` | `llama` |
| Blocks n; hidden size | 32; 4096 (R: SC §2, "read, never assumed") | 32; 4096 |
| Prepared set P_F; manifest | `tmp/kt-prepared/prepared-kt-dolly-olmo2`; `9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9` (the same set as OLMo-2-1B's) | `tmp/kt-prepared/prepared-kt-dolly-llama3`; `c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a` |
| Rows; units; rows per unit | 4,800; 8; 600 (M: track E's family tests, R: SC §2 `score_edit` row) | 4,800; 8; 600 |
| MAIN_F file; `config_sha256` | `experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json` (file bytes `e9e98e84…`, M); `18cc31d7117a2de7bc02382fe8a4d409fc43c91b434bf219a4808dfb26528d09` | `…/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json` (file bytes `3d437bd6…`, M); `74758af1791d9f7a8ce616adce7549b5b7b0619e55310158d7e21197ed129893` |
| Token limits (every recipe here) | `max_train_tokens` 3072, `max_prompt_tokens` 1536, generation batch 32, `max_new_tokens` 2048 (R: SC §2, M there) | the same |
| S_78_F | null until F's anchor job (ADD A1; RK `RECIPE_S`) | null until F's anchor job |
| BANK_F | null until F's anchor job | null until F's anchor job |
| Engine | X, `472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892` (M: `code_identity()` at HEAD) | the same |

### 1.2 The code: one wrapper over the unchanged 1B scripts (R: SC §1-§2; WRAP)

- **Form.** `python -I -B scripts/scale78b/scorers_78b.py KIND --family F <the 1B script's own arguments>`. The wrapper imports the 1B module, checks its SHA-256 against `STAGE1_CODE` (§1.17 table B), loads F's derived settings file through the pinned index `settings/PINS-78B.json` (`PINS_FILE_SHA256` = `a2132c9d…`), runs F's preflight, then the 1B script's own `main(argv + ["--settings", file])` with that module's `SETTINGS_SHA256` replaced for that one call and restored after it (the pattern of the 1B D-2 wrapper `scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py`; R: SC §1).
- **Kinds of the wrapper** (R: WRAP `KINDS`): `untuned_answers`, `rep_pass`, `l1_scan`, `l1_score`, `classifier`, `s3_score`, `score_edit` (`a1` or `scorer`), `add_edit`, `s_pool`.
- **Flags.** The wrapper adds `--settings` itself and refuses a caller's `--settings` and `--pool-pins`. Every `--` token must be a full flag name of the 1B script's command (`ALLOWED_FLAGS`), so an abbreviation such as `--li`, `--lo` or `--ou` refuses before anything runs (M: track M, 10 cases fail on HEAD's wrapper and pass on WSM's; mutants e1-e5 killed; R: MFIX item 3).
- **Settings.** MAKER derives `settings/<script>__<family>.json` (18 files) and `settings/PINS-78B.json` from the 1B settings files (each checked against MAKER's `BASE_SHA256`, §1.17 table C) and PINS. Each derived file keeps the 1B file's `kind`, `name`, `engine_x` and `label_entries`, so the frozen 1B `check_settings` accepts it under its 1B name, and adds a `family_78b` block (family, manifest, main recipe, the 1B file and its SHA-256, the null pins with their events). `MAKER --check` regenerates all 19 files and compares (M: track M, exit 0, "19 of 19 files equal their regeneration").
- **Tests.** M (track M, WSM, 6 Nov): `scripts/scale78b/tests` under the main environment 246 passed, 2 skipped (no scipy there); the noise and G1 tests under `.venv` 74 passed; `tests/scorers` 113 passed. CUDA paths and real 7-8B models are untested (tiny random CPU models only; R: MFIX §7 item 5).

### 1.3 The engine rule for the scorer kinds (PP4, PP16; ruling 10; ADD A13)

- **Wrapper kinds run on engine X.** Every wrapper kind runs on engine X (`472fc7f6…`): on the pod `untuned_answers`, `rep_pass`, `l1_scan`, `classifier`; on the Mac `l1_score`, `s3_score`, `score_edit`, `add_edit`, `s_pool`. Each derived settings file carries the 1B file's `engine_x`, and the frozen `check_settings` refuses another engine identity (R: `scripts/stage1/s1common.py:590-592`; M: track M's line test). A run on engine Y needs the settings re-derived for Y by a recorded step; none exists (PP4; PINS `shared.engine_rule_78b`).
- **The kit's X-only set (PP16).** `X_ONLY_KINDS` = `untuned_answers`, `o_only`, `regenerate`, `anchor`, `rep_pass`, `l1_scan`, `classifier`, `c0`. `engine_allowed` checks it first, before `ENGINE_Y` is filled. **State at HEAD (M: `grep X_ONLY`):** RK defines no `X_ONLY_KINDS`; `runkit/stage1-78b/stage1_rules.py:234` has `X_ONLY_KINDS = ()` and `plan_tool.py:729` reads it. The ruling is built in the kit's next round (§14 item 2).
- **The engine's own jobs.** The a0-1101 retrain and `a1_pass` follow ruling 10 and ADD A13, not PP4: the retrain runs first on engine Y; if Y's q and e1 fingerprints equal the side unit's, Y = X for that family; `a1_pass` runs on the engine that trained its states (EYD:81 via RUL; P1 §3.7; PP16). The fingerprint check is `scripts/scale78b/fingerprint_compare.py` (`b5bcb212…`).
- **The S_78 kinds (PP8; R: RK:141).** `S78_KINDS` = `retrain`, `rep_pass`, `a1_pass`, `classifier`. Each refuses while `RECIPE_S[F]` is null (R: RK `recipe_s_or_refuse`, :424-434).

### 1.4 The order of the scorer jobs, per family (ADD A2; PP1; CHECK C1)

Each pod kind below is a single-job pod with an explicit E cap (KD6; §1.15). "After" means the named output must exist first.

1. **No inputs from other 7-8B jobs:** the **untuned-answers pass** (two calls, PP2; §1.10, §1.11), the **anchor job** (§1.5), and the **untuned unit's O pass** (§1.14). PP1 lets the untuned-answers pass run before the anchor job.
2. **S_78_F** after the anchor job: `make_recipe_s78.py` writes it and the lead commits it by explicit path, then fills `RECIPE_S[F]` in RK and `recipe_s78`, `anchor_bank_sha256` in PINS (ADD A1; §1.16).
3. **The a0-1101 retrain** on engine Y under S_78_F (ruling 10, ADD A2, A8); the X retrain only if Y's fingerprints differ.
4. **`a1_pass`** after the retrain (§1.5). **`rep_pass`** after S_78_F and the untuned pass (for the `s3_orig` pool) (§1.6, §1.10). **`l1_scan`** after the anchor job (§1.6). **The classifier** after S_78_F (§1.12). **c0** (§1.13).
5. **Mac steps** after their pod inputs: `l1_score`, `score_edit` (L1 and A1), `s3_score`, the S3 pick, `add_edit` (S1, S3, S4, S4_96, S4_192).

Scorer outputs are read only after this section is committed (P1 §12; P78:367; CHECK M4).

### 1.5 A1 (per family; ADD A1, A2; PP3, PP8; P1 §3.7)

- **The anchor job (pod kind `anchor`; engine X, PP16).** `python3 scripts/make_anchor_answers.py --prompts <the sealed full anchor prompt list> --recipe MAIN_F --out <job>/anchors`, the pinned Gate B script unchanged (`5a686a82…`). The list is the sealed Gate C list, `78467c97c40e7e9f…` (text under `tmp/`; text-free record `.ai/inputs/gate-b-anchors-20261008/out/anchor_prompts.sealed.json`, `5d23fa2b…`). Rule (R: `scripts/make_anchor_answers.py:1-17`): θ0 answers every prompt greedily with MAIN_F's generation settings; a safe anchor is kept in list order when its answer ended at a stop token, MAIN_F's guard labels it Safe and `encode_train` accepts it; the safe set is the first 64 kept; the harmful set is the first 64 prompts with their unsafe responses; a harmful pair that `encode_train` refuses stops the job; fewer than 64 kept exits 3 with counts only. Outputs: `anchors.json` (text; to `tmp/`) and `anchors.sealed.json` (text-free; committed), whose `anchor_file_sha256` is BANK_F's hash. The anchor file holds F's own Safe answers, so it is per model (P78:377; ADD A1).
- **S_78_F (ADD A1).** `python3 -I -B scripts/scale78b/make_recipe_s78.py --family F --anchors-sha256 <anchor_file_sha256> --out experiments/safety_selection/configs/<name>.json` (`fcf01955…`). S_78_F = MAIN_F with exactly Gate B's recipe-S differences: `attribution.checkpoints` becomes [q, e1], `attribution.query_bank` becomes `anchors-<that SHA-256>`, and `name` and `purpose` change; every model, training, generation, guard and scoring key keeps MAIN_F's value, so S_78_F has MAIN_F's training identity (OLMo-2-7B `36738c38…`, Llama-3.1-8B `5b4451e1…`) (R: `make_recipe_s78.py:1-19`).
- **The a0-1101 retrain** (pod kind `retrain`): train only, recipe S_78_F, seed 1101, to q and e1; engine Y first (ruling 10; P1 §3.7). It gives A1's states.
- **`a1_pass`** (PP3, PP8): the engine's attributes job on the retrain's q and e1 states with BANK_F (the stage-1 kit's `a1_rescore` form: `make-job attributes --a0-state q=<retrain unit> --a0-state e1=<retrain unit> --groups <the 8 unit groups> --anchors BANK_F --pin-code`, then `attributes`; R: SC §2, `runkit/stage1-olmo/setup/job_runner_stage1.py:49-53`). It runs on the engine that trained the states (PP16; ruling 10). Cap: 16.5 h at most (KD6, PP8; §1.15).
- **A1's removal contract and k (R: `scripts/stage1/write_score_edit.py:1-28`; `scripts/stage1/settings/write_score_edit.json` `a1`; unchanged in `write_score_edit__F.json`).** Command: `scorers_78b.py score_edit --family F a1 --unit <the attributes unit folder> --prepared P_F --out out/a1-edit` (Mac; engine X).
  - The writer first checks the attributes unit: its own files verify; kind `attributes`, seed 1101, split `dev`, the pinned anchor bank (64 harmful, 64 safe), the 8 units; the unit's code identity equals the settings' `a1.attributes_unit.code_sha256` (R: `write_score_edit.py:93`); the recipe is S_78_F; both checkpoint sources name the pinned retrain.
  - Per row: a_i = the mean over c ∈ {q, e1} of (cos(row gradient, harmful-anchor mean gradient) − cos(row gradient, safe-anchor mean gradient)), read from the unit's `rows.jsonl` field `cosine` (variant `checkpoint_gradsim`; the Adam variant and every other field are never used).
  - Consistency: for each unit, the mean of its rows' a_i must equal `groups.json`'s `bi_anchored.checkpoint_gradsim` within 1e-12 absolute, or the writer refuses.
  - **k = 600.** The 600 rows with the largest a_i over all 4,800 training rows are removed (global, not per unit); ties by the sealed rank of registry key `a1.ties` over all row ids. 4,200 rows remain, 33 steps (P1 §1). If at least 50% of the selected rows are one category, A1 is also compared with that category's Gate B unit arm (the settings' `category_flag_rule`, PLAN-S:149).
  - Outputs: `a1_remove600.edit.json` (row ids only) and `a1_selection.json` (text-free).
- **What differs from 1B (R: PR4 §1.2; PINS).** At 1B, A1 was the sealed 600-row set from Gate B's wave-0b attributes unit (`5c0e53b7…`). At 7-8B each family's A1 is computed by the same contract from that family's own retrain and anchor file. Six pins of `write_score_edit__F.json` `a1.attributes_unit` are null until the pass (§1.16).
- **EM-3.** No scorer built on a0-1101 states is evaluated at 1101: A1 runs at the method seeds from 1102 (P1 §5, §11).

### 1.6 L1, LARF-style (per family; PP11, PP12; `scripts/stage1/score_l1_larf.py` unchanged)

- **The scan (pod kind `l1_scan`; engine X).** `scorers_78b.py l1_scan --family F --prepared P_F --recipe MAIN_F --anchors BANK_F --out <job>/l1-scan`. The rule is the 1B script's (R: `score_l1_larf.py:1-20`; `score_l1_larf__F.json` `scan`):
  - Scan prompts: BANK_F's 64 harmful anchor prompts and 64 Dolly training prompts (the sealed sample of key `l1.scan` over all training row ids, sorted).
  - θ0 (MAIN_F's policy, adapter disabled, no gradients) answers all 128 prompts greedily with `max_new_tokens` 32 and MAIN_F's stop tokens, in one call per configuration. A refusal is lexicon class REFUSAL-OPENING.
  - Scaling: forward hooks multiply the outputs of block l's named modules by (1 + α) and (1 − α), α ∈ {0.1, 0.2}. Every block is run and logged.
  - c+ and c− are the refusal counts over the 128 prompts; Δ_l(α) = c+ − c−; k_l = max over α of Δ_l(α)/α; l_s = argmax k_l over the eligible blocks, ties to the larger Δ_l(first α), then the lower index; if max k_l ≤ 0, l_s = the last block, recorded as "no signal". The hooks are removed after each configuration.
  - **First eligible block (PP11): `scan.first_block` = round(5 × n / 16) = 10 at n = 32**, so blocks 10-31 (22 blocks) are eligible. Same for both families.
  - **Scaled modules (PP12), by `config.model_type`:** OLMo-2-7B `olmo2`: `post_attention_layernorm`, `post_feedforward_layernorm` (stage 1's; UW-11 (d)). Llama-3.1-8B `llama`: `self_attn`, `mlp` (the attention and MLP sublayer outputs; the 1B settings file's own llama entry). Each family's settings file carries only its own entry, so the other family's model refuses at `scale_modules` (M: track M, `tests/scorers/test_l1_pins_78b.py`, tiny random 32-block Olmo2 and Llama models on CPU; the unchanged 1B `choose_layer` at n = 32 reads blocks 10-31).
- **The representation pass (pod kind `rep_pass`; engine X; S_78).** `scorers_78b.py rep_pass --family F --prepared P_F --recipe S_78_F --anchors BANK_F --pool s3_safe.pool.json:6801652c… --out <job>/representation`, then the `s3_orig` pass (`… --pools-only --pool s3_orig.pool.json:<the untuned pass's record names it> --out <job>/representation-s3-orig`) (R: SC §2; the stage-1 kit's two passes). One unbatched forward of θ0 per encoded row with `output_hidden_states=True`; index convention L4 (index 0 the embedding output; index i the output of block i − 1; index n the final-norm output); reads (a) end-of-turn, (b) last response token, (c) response mean, (d) last prompt token; per row and index the scalars cos_harmful and cos_safe against BANK_F's set means (R: `representation_pass.py:1-25`). It serves L1, S3, DataShield-style and the Gate C reproduction (PP3). Both pool pins of `representation_pools__F.json` are null: no plant or decoy pool at 7-8B (R: SC §2).
- **The score (Mac; `l1_score`).** `scorers_78b.py l1_score --family F --prepared P_F --scan l1_scan.json:SHA --rows representation_rows.jsonl:SHA --summary representation_pass.json:SHA --out out/l1-score`. For every training row, score = cos_harmful − cos_safe at hidden-state index l_s + 1 (index n when l_s = n − 1), read (a), float64 (R: `score_l1_larf.py:19-23`; settings `score`). The settings pin F's `rep_pass` settings file by SHA-256 (`pins.representation_pass_settings_sha256`).
- **The edit (Mac; `score_edit scorer`).** `scorers_78b.py score_edit --family F scorer --name l1 --scores l1_scores.json --scores-sha256 SHA --prepared P_F --out out/l1-edit`. **k = 600**: the 600 rows with the largest score are removed, global over all rows, ties by the sealed rank of `l1.ties` (R: `write_score_edit.py:3-7`). 33 steps.

### 1.7 H1 (per manifest; P1 §14 item 1; CHECK C6)

- **The rule** (stage 1's REQ-5, L7; `scripts/stage1/build_length_rules.py` `923dd321…`, settings `3800e52a…`): one length order of all 4,800 training rows by (target tokens ascending, then the sealed rank of registry key `length.order`); H1 = octile 0, the 600 rows with the fewest target tokens (R: `.ai/inputs/scale-78b-length-rules-llama3-20261105/README.md:13-19`). 33 steps.
- **OLMo-2-7B** uses stage 1's committed H1 file: `.ai/inputs/stage1-commitments-20261016/length-rules/edits/octile_0.json`, `f5b1762f662e931235f798497248b2f342e6d2b2011ce5a0bfecf53678b4def7` (M). Basis: the same manifest `9ed61826…`, so the same order (P78:377; P1 §14 item 1).
- **Llama-3.1-8B** uses the committed Llama set (ADD A3): `.ai/inputs/scale-78b-length-rules-llama3-20261105/out/edits/octile_0.json`, `9a01637ec63dc38f6e4dec646a0bc4b8c00c36521fa8831fe4fb87e8df3a1c5f`, MANIFEST `24c1305ab59e979f…` (M), built by `scripts/scale78b/build_h1_llama3.py` (`26f2f2a1…`, frozen since its commit, ADD A3). Its OLMo parity: the same script on the OLMo set gives stage 1's remove list exactly; on the Llama set H1 shares 599 of 600 rows with the OLMo H1 (R: its README:21-29; M there). It also serves Llama-3.2-1B (same manifest and tokenizer).

### 1.8 The S-pool (stage 1's sealed lists reused)

- **Rule.** Both families reuse stage 1's sealed prompt lists as they are (P1 §14 item 1: "the same 48 S-pool rows, re-bound to the family manifest"; CHECK C6; PINS `shared.sealed_lists_1b`). No per-family S-pool is built: `build_s_pool__F.json` exists but runs only if Part 2 says the S-pool is rebuilt per family, and it does not say so (R: PINS `sealed_lists_1b.note`; SC §2 last row).
- **The lists** (text under `tmp/`; each named on the command line by PATH:SHA-256; R: `.ai/inputs/stage1-commitments-20261016/s-pool/s_pool_record.json`, `bcca59ac0f8c15c3…`, M):
  - `s1.json` `389c20ad00261b1a…`: 48 rows (sealed order `stage1-s1-v1`).
  - `s3_safe.pool.json` `6801652cb506f962…`: 861 items, the S3 subset and S1's rows outside it, with the PKU-safe response.
  - `s3_subset.json` `dea5ec15a1f43e19…`: 855 prompts (deviation D-1: the record's `d1.k` 855 against `planned_s3_subset_size` 1,000; R: the record's `d1` block).
  - `s4_candidates.json` `798613c4e5d32caa…`: 512 prompts (sealed order `stage1-s4-v1`).
- The S-pool was built and filtered at 1B under OLMo-2-1B's limits (3072 / 1536; the record's `limits`). Whether every list prompt encodes under each 7-8B codec is not checked here (§14 item 6).

### 1.9 S1 (PP5)

- **OLMo-2-7B** reuses stage 1's committed S1 edit by hash: `add_s1.json`, `904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10` (text, in git-ignored `tmp/`; named in the committed record `.ai/inputs/stage1-commitments-20261016/add-s1/add_edit_record.json`, `311957a4…`, M). Basis (PP5): all 48 rows encode within the 7B main recipe's limit, and REQ-7's writer reproduces the file exactly (M: track F; verdict record `9b340bf504400576f116e394fa9dd669cff623c0a35e8bb34cdd1c2ee018d2ca`, unchanged after track M's fix, MFIX item 1). The check script is `scripts/scale78b/s1_olmo2_7b_check.py` (`4b8786f7…`).
- **Llama-3.1-8B** takes a new S1 edit: `add_s1.json`, `6942699398ade7f7ddb6f5b47b06e8b253de6ff9bbd142b8138acc061468dd0a`, 48 add rows on manifest `c52a50af…`, arm `edit-69426993…` (R: `.ai/inputs/scale-78b-s1-llama3-20261105/out/MANIFEST.json`, `a3986274…`, M). Built by the frozen `build_s1_llama3.py` (`a2b0a66c…`) with REQ-7's writer (`write_add_edit.py` `8b866b3d…`, imported unchanged) under MAIN_F's `max_train_tokens` 3072 (its settings re-bind the manifest to `c52a50af…` and the recipe to `74758af1…`; `write_add_edit_llama3.settings.json` `36a39481…`; record `add_edit_record.json` `1023b4e6…`; M). The text file lives in git-ignored `tmp/`, named by hash in the committed MANIFEST.
- The sealed S1 list was recovered byte for byte from the OLMo S1 edit; it is accepted because its bytes hash to the sealed pin `389c20ad…` (PP5).
- 4,848 rows, 38 steps (P1 §1, §10).

### 1.10 S3, DataRx-style (per model; CHECK C6; PP1, PP2)

- **y^orig (pod kind `untuned_answers`, call 1; engine X).** `scorers_78b.py untuned_answers --family F --recipe MAIN_F --recipe-s MAIN_F --list s3=s3_safe.pool.json:6801652c… --loss s1=s1.json:389c20ad… --loss s3_safe=s3_safe.pool.json:6801652c… --out <job>/untuned` (PP2). θ0's greedy answer to each S3 prompt at a 512-token cap; every answer is kept; capped answers are flagged; a y^orig that `encode_train` refuses leaves the SAS ranking and is counted (L14 (1)); the `s3_orig` pool holds the others with ids `<id>:orig` (R: `make_untuned_answers__F.json` `lists.s3`). This call cannot exit 3 (R: SC §2).
- **Recipe S of the pass (PP1).** The pass takes MAIN_F as `--recipe-s`. `make_untuned_answers.py` reads recipe S only for `model.max_train_tokens` and requires REC and S to agree on four model fields (R: `make_untuned_answers.py:82-93` via SC §4). S_78_F equals MAIN_F there, so the value is the same. **The recorded `recipe_s` hash is the main recipe's** (PP1).
- **The pools' features (`rep_pass`, §1.6)** on `s3_safe` and `s3_orig`.
- **The score (Mac; `s3_score`).** `scorers_78b.py s3_score --family F --rows …:SHA --summary …:SHA --s-pool-record s_pool_record.json:bcca59ac… --answers-record untuned_answers_record.json:SHA --out out/s3-score`. For a candidate x and response d: s^l(d) = cos(h^l, C_r^l) − cos(h^l, C_c^l) at read (a), hidden-state index l = 1..n; R(d) = the mean over l; **SAS(x) = R(x, y^safe) − R(x, y^orig)**. Only the S3 subset is ranked (R: `score_s3_datarx.py:1-21`).
- **The pick (Mac).** `scripts/stage1/write_score_add.py --scorer s3 …` unchanged (`482c3145…`, settings `0c1679b4…`; they pin no family value; R: SC §2): **k = 48**, the largest SAS, ties by the sealed rank of `s3.ties` (R: `write_score_add.py:1-12`).
- **The edit (Mac; `add_edit`).** `scorers_78b.py add_edit --family F --prepared P_F --recipe MAIN_F --list s3.json:SHA --full-out tmp/<…>/full --out out/add-s3` (PP1: the add-edit writer takes MAIN_F). 4,848 rows, 38 steps.

### 1.11 S4 and the add-dose lists S4_96, S4_192 (per model; P1 §10; ruling 12; PP2)

- **The pass (pod kind `untuned_answers`, call 2; engine X).** `scorers_78b.py untuned_answers --family F --recipe MAIN_F --recipe-s MAIN_F --list s4=s4_candidates.json:798613c4… --out <job>/untuned-s4`. The S4 list runs alone in this second call; the wrapper refuses `--list s4` beside another `--list` or a `--loss` (PP2). Basis: with one call, the pre-set dose fallback exits 3 in the unchanged 1B code and drops the S3 outputs (verify-E D1; PP2). The pod's E cap covers both calls (§1.15).
- **Keep rule (PR4 S4 row; L14 (2)).** θ0's greedy answers to the 512 prompts in S4's sealed order, in 32-prompt chunks, at MAIN_F's cap; an answer is kept only if it ended, its lexicon class is REFUSAL-OPENING, `answer.strip()` is non-empty and `encode_train(prompt, answer, max_train_tokens)` accepts; the first failing check is the drop reason. **`lists.s4.keep` = 192**: the 1B code stops after the chunk that holds the 192nd keep; the first 48 kept are the same rows a 48-keep run gives (M: `tests/scorers/test_scorers_78b_parity.py::test_the_first_keeps_do_not_depend_on_the_stop_rule`; R: SC §3).
- **The dose lists (the wrapper).** **S4 = the first 48 kept, S4_96 = the first 96, S4_192 = the first 192, nested prefixes of the kept order**: `doses/dose_s4.json`, `dose_s4_96.json`, `dose_s4_192.json`, plus the text-free `s4_doses_record.json` (SHA-256s, row counts, the nesting check) (R: `make_untuned_answers__F.json` `doses`; M: `test_s4_doses_78b.py`, 10 tests).
- **Pre-set fallback (DOSE `pre_set_fallbacks[0]`; ruling 12).** Fewer than 192 kept after all 512 prompts: the top dose is all kept rows, written as list `s4_top` (`dose_s4_top.json`) with its count in the record, `fallback_fired` true, exit 0; the smaller doses that are filled are written. Fewer than 48 kept: counts only, exit 3, no dose file (R: SC §3).
- **Sizing (E; M2).** At the 1B keep rate (57 of 64, 89%), 192 kept rows need about 216 candidates, 7 chunks of 32 (224 prompts); the list holds 2.37 times that (M: `candidates_needed(192, 57, 64)` = 216; R: settings `doses.sizing`). This count only sizes the fallback (P1 §13 item 9).
- **The edits (Mac; `add_edit`).** `--list dose_s4.json | dose_s4_96.json | dose_s4_192.json` (and `dose_s4_top.json` only if the fallback fires; its `rows` pin is null until the count is known) under MAIN_F. S4 4,848 rows → 38 steps; S4_96 4,896 → 39; S4_192 4,992 → 39 (P1 §10).
- **Documented quirks of the unchanged 1B code at keep 192 (R: SC §3, §6 items 5-6).** A keep after the 192nd is labelled `kept_after_the_48th` (a fixed string; read it as "after the 192nd"; `make_untuned_answers.py:171`). The W1-06 loss table's `s4` entry covers all 192 kept rows and is absent in the fallback case. In the fallback case the 1B record says `complete` false while `wrapper_78b_record.json` says `exit_code` 0 with `fallback_fired` true; the 7-8B kit reads the wrapper record.

### 1.12 The classifier (pod kind `classifier`; engine X; under S_78; PP4, PP8)

- `scorers_78b.py classifier --family F --prepared P_F --recipe S_78_F --anchors BANK_F --out <job>/classifier` (no `--pool`). The rule is REQ-23's (R: `scripts/stage1/score_classifier.py:1-17`): S_78_F's guard scores each dev row on (prompt, training response) with `GuardScorer.label_scores`, read-only, as the pinned Gate C classifier does; the score is the normalized Unsafe label-sequence score; an unscored row is counted, never imputed. Per unit: rows, scored, unscored, mean, SD, SE. The top 600 scored dev rows by score, ties by `classifier.ties`. **Scored only: no edit file is written.** Output `classifier_scores.json` (text-free).
- The classifier runs under S_78, as at 1B, so the kit lets it through the S_78 key check (PP4; RK:141 `S78_KINDS`). `score_classifier__F.json` pins `recipe_sha256` = S_78_F (null until filled). No plant or decoy pool at 7-8B.
- Its use in the 7-8B reports is not fixed here (§14 item 8).

### 1.13 c0 (pod kind `c0`; engine X; PP16)

- **Form (R: SC §2 `c0` row; RK `KIND_LABELS`, "c0 on an engine-X unit (B17's X-pin check)").** The engine's `make-job run-one` of F's R_1 at seed 1101 (its sealed R_d1 edit: OLMo-2-7B SEAL `out/edits/R_d1.json` `f7d7eb86…`; Llama-3.1-8B `.ai/inputs/scale-78b-sealed-llama3-20261105/out/edits/R_d1.json` `5cdedf22…`; M), train only, then the S1 package's `scripts/stage1_s1/lean_eval_job.py run --expect-adapter-fingerprint …` (R: `runkit/stage1-olmo/setup/job_runner_stage1.py:45-47` via SC).
- **What it is (PR4 §10.3, LS-15, LN-27).** A cost-measurement job: only its ledger is read; its evaluation files are sealed by hash and never read. It is not a scorer of any arm.
- **State at HEAD.** `lean_eval_job.json` allows only the 1B recipes (R: `scripts/stage1_s1/settings/lean_eval_job.json:38-39`), so the 1B lean job refuses the 7-8B recipes as it stands (§14 item 1). The c0 unit at 7-8B (R_1 at 1101) is SC's and the kit's form; no ruling text names it (§14 item 9).

### 1.14 The untuned units' O and L evaluation (CHECK M1; ruling 11; P1 §12, §14 item 3)

- **The need (CHECK M1).** Every arm needs O against the family's own untuned model and task loss L (PR4 §3.6's O set of 500 prompts). The side probes' untuned units (P1 §2.1) were evaluated with the family-probe bank (468 greedy + 600 samples + 189 ARC; KCR:70), not with stage 1's O set. So the kit runs the stage-1 kinds `o_only` / `regenerate` (and `untuned_answers`, §1.10-§1.11) for both untuned units before block A (ruling 11 KD10; P1 §12).
- **The job (pod kind `o_only`; engine X, PP16).** The S1 package's O-ext unit pass on θ0: `python -B scripts/stage1_s1/oext_unit.py run --untuned --prepared P_F --recipe MAIN_F --oext-bank F --oext-record F [--w1-18-record F] --out DIR` (R: `scripts/stage1_s1/oext_unit.py:1-35`; the stage-1 kit's `job_runner_stage1.py:19-23` via SC). Its O rules are `oext_eval.py`'s: the 500-prompt bank read by its pinned record, the cap branch, O with equal weight per prompt (R: `oext_unit.py:6-9`; PR4 §6.2 LN-24).
- **State at HEAD.** `oext_unit.json` pins the 1B prepared manifest `9ed61826…` and allows only the 1B recipes B `9e9bde6f…`, G `c004349c…` and S `ceffe0ef…` (R: `scripts/stage1_s1/settings/oext_unit.json:52-66`). So the pass refuses MAIN_F on both families, and P_F on Llama, as it stands. **No 7-8B route for this pass exists yet** (§14 item 1). The job runner's block-0 subset runs no O-ext step (R: `runkit/stage1-78b/setup/job_runner_stage1.py` module doc: "No O-ext step runs at 7-8B (N's gate and the seed rule read the engine's own U only, Part 1 §3)").
- **What this section does not fix.** The O bank of the 7-8B arms, whether the `arm` kind evaluates O and L in the same job, the τ_O grid and τ_L (S1B REQ-19 form, from the family's a0 seeds) belong to §4 (to be written; P1 §14 item 3).

### 1.15 The E caps of the scorer kinds (KD6; PP8, PP15; M: RK `e_pod(F, kind)` at HEAD, main environment)

Each kind runs alone on its pod with this cap until its first 7-8B run measures it; then the basis is updated by a recorded lead step (KD6). Guard = $6 + $1.85 × cap (KCR); spend upper = the E upper's pod time at $1.79/h with the 48 min overhead (RK).

| Kind | OLMo-2-7B cap (h) / guard / spend upper | Llama-3.1-8B cap (h) / guard / spend upper | Basis (R: RK `e_upper_s`, :848-935) |
|---|---|---|---|
| `untuned_answers` (both calls) | 3.0 / $11.55 / $4.46 | 3.25 / $12.01 / $4.56 | 16 chunks of 32 at the capped-batch maximum (M constants) × 1.5 |
| `o_only` | 3.75 / $12.94 / $5.46 | 3.75 / $12.94 / $5.58 | 600 prompts (the 500-prompt bank plus the dev 100) in 19 batches, guard at half the scoring allowance, × 1.5 |
| `regenerate` | 2.25 / $10.16 / $2.89 | 2.25 / $10.16 / $2.89 | a train-only a0 at 38 steps + 3 state writes, × 1.5 |
| `anchor` | 2.25 / $10.16 / $2.98 | 2.25 / $10.16 / $2.98 | the 1B 0.25 h upper × 2.3 × 1.5 |
| `rep_pass` (PP15) | 4.75 / $14.79 / $7.61 | 4.75 / $14.79 / $7.61 | the stage-1 kit's 1 h at 1B × 2.3 (RP:43) × 1.5 |
| `a1_pass` (PP8) | 16.5 / $36.53 / $28.64 | 16.5 / $36.53 / $28.64 | KD6's 16.5 h at most (RP:43's 6-11 h); job window 15.2 h |
| `l1_scan` | 4.75 / $14.79 / $7.61 | 4.75 / $14.79 / $7.61 | the 1B 3,600 s × 2.3 × 1.5 |
| `classifier` | 3.25 / $12.01 / $4.88 | 3.25 / $12.01 / $4.88 | the 1B 2,012 s × 2.3 × 1.5 |
| `c0` | 4.25 / $13.86 / $6.67 | 4.5 / $14.33 / $6.82 | the evalonly bound + 1.5 × 600 s, at least the 1B 2,400 s × 2.3 × 1.5 |
| `retrain` (A8) | 4.5 / $14.33 / $6.80 | 4.5 / $14.33 / $6.80 | a 3 h upper on engine Y (about 6 × the expected) |

All are E (the measured parts use the family's M constants; the scorer work is unmeasured at 7-8B). The kit's next round may change RK (PP14-PP16); the lead re-reads this table at the freeze (§14 item 3).

### 1.16 The pins that wait, and how a pin is filled (ADD A1, A13; R: SC §5; PINS)

| Pin (PINS unless named) | Event that fills it | Commands that refuse until then |
|---|---|---|
| `families.F.anchor_bank_sha256` | F's anchor job: `anchors.sealed.json` `anchor_file_sha256` of its committed record | `rep_pass`, `classifier`, `l1_scan`, `score_edit a1` |
| `families.F.recipe_s78.{path, config_sha256}` and RK `RECIPE_S[F]` | `make_recipe_s78.py` after the anchor job; the lead's commit (ADD A1, A2) | `rep_pass`, `classifier`, `score_edit a1`; RK's `retrain`, `a1_pass` |
| `families.F.a1_attributes_unit.{complete_sha256, retrain_complete_sha256}` and the a1 `code_sha256` | F's a0-1101 retrain under S_78_F, then `a1_pass` on its states; the engine that ran them (X, or Y after the certificate) | `score_edit a1` |
| `families.F.untuned_pass.*` | F's untuned-answers pass (record only; consumers take PATH:SHA-256 on the command line) | none |
| `lists.s4_top.rows` (derived) | only if the dose fallback fires: the kept count in `s4_doses_record.json` | `add_edit` of `s4_top` |
| RK `ENGINE_Y` | the lead, when the Y retrain is packed (A13) | E kinds on Y |
| `shared.l1_first_block` | **filled**: 10 (PP11) | none |

**How a pin is filled (R: SC §5).** Edit PINS; run `python -I -B scripts/scale78b/make_scorer_settings_78b.py` (it rewrites the 18 settings files and `PINS-78B.json` and prints the new `PINS_FILE_SHA256`); set that literal in WRAP; run `tests/scorers`; commit PINS, `settings/*.json`, `PINS-78B.json` and WRAP by explicit path (KD8). The derived files change only where the pin reaches (`test_the_two_families_differ_only_where_they_should`). So each fill changes the hashes of PINS, the reached settings files, `PINS-78B.json` and WRAP from those in §1.17; the rules, the 1B scripts and MAKER do not change. How Part 2 records these later hashes is §14 item 5.

### 1.17 Hashes (SHA-256; M: `shasum -a 256`, 6 Nov 2026)

**Table A. `scripts/scale78b/` (WSM, after track M; re-hashed by this track; all 48 files equal track M's `after.sha`, paths included; M: `diff`).**

| File | SHA-256 |
|---|---|
| `scorers_78b.py` (WRAP) | `108f44257cb967a3594e7a865879a668a3de830c4385b75bf50de1db29322fbf` |
| `make_scorer_settings_78b.py` (MAKER) | `7c8f249138b1083b54d7d7586907815db41b7cc65ef402e582aad108d48179f5` |
| `SCORERS-78B.md` (SC) | `8c92a892064d68bd1806ebc74d5f87c5e1c00f53b087bae7528eb6addc515563` |
| `make_recipe_s78.py` | `fcf0195587d8d3e6635aaa73e7a62776d6b14bf7de7dc90d5420143572d94900` |
| `fingerprint_compare.py` | `b5bcb212315646caaaff074a458dcc9e91fa4185e5497a8dd1b01e96f01d3646` |
| `s1_olmo2_7b_check.py` | `4b8786f7f9bd4008019aa59daf8587d096c20accace7efce70e9f41265366dc4` |
| `build_h1_llama3.py` (frozen, ADD A3) | `26f2f2a13c875364f333e0b0ad039505ac98ffee91ee85af00148356ba7f7df6` |
| `build_r_draws_78b.py` (frozen, ADD A3; not a scorer) | `18f2fec801c7643dee3f2f0c651a29b41db29d68baeb5185962799ec0fcd9ffa` |
| `noise_reading.py` (N's reader; not a scorer) | `94b679ffeee7656c5b8c6e97b2275bb05260b61cac50743f357ef8ce2c40d436` |
| `g1_check_78b.py` (not a scorer) | `251ddb32146ee71fc4519772729757572b132cdf09cb27849fa2a15fc91246aa` |
| `__init__.py` | `54e2663909e5fc4d8b27f1d3f473a019e14d2da5d4f88a54aa390e42a4de9fba` |
| `settings/PINS-78B.json` (= `PINS_FILE_SHA256` in WRAP:74) | `a2132c9d731bfa3d8176063961fc03f0cb55bc148d40ca6b7d5e2af76f783981` |
| `settings/pins_78b.json` (PINS) | `428b75778b75142b4e91fa7f980fe1cb9785b06987963447115f47e27e5efd8d` |
| `settings/make_untuned_answers__olmo2-7b.json` | `b489d00a6dce8a988c86c5045e2efe7776e3103e3317af7f69c1c39350f10a41` |
| `settings/make_untuned_answers__llama31-8b.json` | `2d32312156f16e6a074e41d06473665e5cba87f9da90b6411393669fed149d43` |
| `settings/representation_pass__olmo2-7b.json` | `492a190669198a39443f9b1f491a6182c9b096a9a0585ef440d027affa145238` |
| `settings/representation_pass__llama31-8b.json` | `d11187be40c51cb587f045f4b45e154ba3893b35210b815a5194844104969a20` |
| `settings/representation_pools__olmo2-7b.json` | `ff310c9c2a54053fe8da99120ea3f29c6b81e3280cec2d41b97cf5623d9c9c4d` |
| `settings/representation_pools__llama31-8b.json` | `9ae948b9a2150c018681a18e6e715050830987c03025e8580ca242cefc9edd54` |
| `settings/score_l1_larf__olmo2-7b.json` | `9f9089f167728ef2d1e3d4b75e525a2003408c732eec1641beed4fd783a97c24` |
| `settings/score_l1_larf__llama31-8b.json` | `0de7cfe5915eca98ad3a751704a4a0e9ebd96a635271beb3db0e8c9ac448befb` |
| `settings/score_classifier__olmo2-7b.json` | `c8f32cebe1fb9498153841c7f0c595f3895233ebb8c81dcdc4ed4495bd67beb3` |
| `settings/score_classifier__llama31-8b.json` | `4b1fcadc81a780cd3fbc74c2f5eeef8f2810f1e43ff09b21e89d1385823409f5` |
| `settings/score_s3_datarx__olmo2-7b.json` | `5203499c14575a048977a8c8d7426e60aa0aabd0e1ae5f5e565799f0ef506610` |
| `settings/score_s3_datarx__llama31-8b.json` | `784be58af9fd7c7d44cb934e8ca68ca7c57867f0b0f8172a100e008ab5c45c9f` |
| `settings/write_score_edit__olmo2-7b.json` | `56ccd80bb840f6a7abb3828f0bbc8fdae7ada4ab5b76ca32e8cd9493ad25f322` |
| `settings/write_score_edit__llama31-8b.json` | `6c132873622bad55ec33b507afc8ac34fcb8ca2343565e87279ae772c1a4244e` |
| `settings/write_add_edit__olmo2-7b.json` | `f6420d002ca6b4cc8d277ee3973f391eedadb162432ec7eabd9ff115312c7615` |
| `settings/write_add_edit__llama31-8b.json` | `e2fbabf43625c53a9dce96ef06190a1fc2a20c42b37dede3f305da1c3ad9ccf0` |
| `settings/build_s_pool__olmo2-7b.json` (not used; §1.8) | `9fefe991ad2b125536555d1415f0b311c2177c48f4573669f37a9f4e9d75b23f` |
| `settings/build_s_pool__llama31-8b.json` (not used; §1.8) | `38a3c7b4bd9704624f5dc7a734807025e9a9bb512711698e6d6aed15013456c9` |
| `tests/scorers/test_l1_pins_78b.py` | `a6ff1a3d7c65a4463369ee6ae59092d72580d80eb3bf68aed24681003cfacec3` |
| `tests/scorers/test_s4_doses_78b.py` | `860df90bbb4cfee1e9a9e0e014dc3c4114b44624d8e3200277933e6c7f3be7ad` |
| `tests/scorers/test_scorer_settings_78b.py` | `f743da3bee952a1c076b0c9e54ee519c6dc7e3ed3afef51b40cf512ee260d0b0` |
| `tests/scorers/test_scorers_78b_family.py` | `b8c7eade7820616bdb3ff47e27e21cb48920d2593cf65222457262b79ec35cbb` |
| `tests/scorers/test_scorers_78b_parity.py` | `df07dc2911b24a68dfbadd9b2c8ff83a501e8b42b80dea4628662481348a0b5b` |
| `tests/scorers/test_untuned_two_calls_78b.py` | `3940cfd07ccdbf64cf644ee646057ac85180f40ce8cf9c8aa5bbcb1bec397437` |
| `tests/scorers/conftest.py` | `3d7aa5822b18c5c5f8f1621099c4d6a6fe41ced8372783e390c084d296af8c44` |
| `tests/test_make_recipe_s78.py` | `c17d37bf295dafae7af86cbd4887545f9087d7626b356f2797900f949cfb3037` |
| `tests/test_fingerprint_compare.py` | `9ff4bd7a84cda83cf8dd67666f40920c422f024abbadcca8721fab4f1615664d` |
| `tests/test_s1_olmo2_7b_check.py` | `f1eb8bdd78b718ebc1797ef2e03f3172654f8484143d0e24adae38dbf84569fb` |
| `tests/test_build_h1_llama3.py` | `eb81b4113ba8e47b45b6b14e735a4b62c76597714d7c3ba977c1f6647331f26e` |
| `tests/conftest.py` | `7ec2fc8851938384dfaa3cace1dd7010a551d97703a9bbeb511e05a338eee729` |

The other test files of the folder (`test_build_r_draws_78b.py` `e739827…`, `test_g1_check_78b.py` `2760187e…`, `test_noise_reading.py` `6f301524…`, `test_noise_reading_guard_fields.py` `3987cf49…`, `test_noise_reading_rv2_2.py` `f588b5df…`) serve N's reader and the sealed sets; their full values are in the round's records (track M's `after.sha`).

**Table B. The 1B scripts the wrapper runs (HEAD `d203070`; M: `shasum -a 256` in a clean HEAD worktree and `git show HEAD:<path> | shasum -a 256` for three of them; each equals WRAP's `STAGE1_CODE`, R: WRAP:79-89).**

| File | SHA-256 |
|---|---|
| `scripts/stage1/s1common.py` | `930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552` |
| `scripts/stage1/make_untuned_answers.py` | `c37ac452b931c84ed28b45e9cfeed9cc9a07ec47ce5f1c6fd1bbef95086743c4` |
| `scripts/stage1/representation_pass.py` | `fb62bcaaaa35595a52de5a4217754cb390ffb4ba49e04dec6e515d7e3cebb8d9` |
| `scripts/stage1/score_l1_larf.py` | `4996fd3bfdd854ecd82630813f7f9b0dab88c4e7e26f81366c566b93c70e95e5` |
| `scripts/stage1/score_classifier.py` | `ee8ae89865e188a8e9f3430c9fbfbe129a415dcc9f3427111a7c77e02dc34549` |
| `scripts/stage1/score_s3_datarx.py` | `772e6ae546843b42c3a7564a644cffa269c38ffb30f4db0d59f0f405a9d5aace` |
| `scripts/stage1/write_score_edit.py` | `2721dbe7239e297b8771795efe04e280297e2e601d65499807f47be4ecf7ead5` |
| `scripts/stage1/write_add_edit.py` | `8b866b3d22bd0656bccd8dbb21ccabde3fda2726b85f149711455836928ad27c` |
| `scripts/stage1/build_s_pool.py` (not run; §1.8) | `cb2ca385a3917d0f4be041ae08b1e121bc67f82a7fc95165e33550f053f463df` |
| `scripts/stage1/write_score_add.py` (run directly, §1.10) | `482c314548328ee1c2be188140ceeb8e005767cf82d762a2cb0f5d28c7b8d330` |
| `scripts/stage1/build_length_rules.py` (H1's rule, §1.7) | `923dd3213efe6283efe9e9a53635fbf2aef554d55a82de594feb9e4366b68096` |
| `scripts/stage1/lexicon_pin.py` (REFUSAL-OPENING) | `bf4412211c5ff681f41c9ae40bfe8d5078964942fa034645daed96e1a0681634` |
| `scripts/stage1/labels.json` (the sealed registry: `a1.ties`, `l1.ties`, `l1.scan`, `s3.ties`, `length.order`, `classifier.ties`) | `260389f3fbfd8e7ff11ee06b5d5aba48e7d56b34140d9c9a634682125a86d570` |
| `scripts/make_anchor_answers.py` (the anchor job, §1.5) | `5a686a82eb80d0a6da3f4f232b31bcda7c7840ced0038f666fe2a0e4a4d34146` |
| `scripts/stage1_s1/oext_unit.py` (§1.14) | `ae2fb5b5fbea36cbd2b27c4eaa20f10504b9856961ae8ee100311c923876b8e3` |
| `scripts/stage1_s1/oext_eval.py` (§1.14) | `8c4290921f32a5b4596a0bc40235cc5cf1185f73eaabeaa625c43bd19ba77719` |
| `scripts/stage1_s1/lean_eval_job.py` (c0, §1.13) | `82461c13d91471729bb036da6565bcb0555885c4b2347d91cd93abcebd9ca46a` |

**Table C. The 1B settings files (HEAD; each equals MAKER's `BASE_SHA256`, R: MAKER:59-69, where listed).**

| File under `scripts/stage1/settings/` | SHA-256 |
|---|---|
| `make_untuned_answers.json` | `4bf2cc1a2493bc154d314105a085f0166933d1147a37e29fd42c7348ba9d9d8c` |
| `representation_pass.json` | `a555fd899bd2b5caf8d68fb62578ed2e943977341b5bf2dc2d688dcbd034600b` |
| `representation_pools.json` | `1451ba5ec435ecaafebd7749f44b6729e45f2157a69a62c55f35e2bbdbae826b` |
| `score_l1_larf.json` | `0d875213831d30456ffc02254cca839d78ae48da8d7ba35d037561b9d59a75cd` |
| `score_classifier.json` | `5807ec750c74137f3e5c466231de9e73a0cbb5fe5411f7be29a40bbed4c8e58a` |
| `score_s3_datarx.json` | `6382dcc663e80ecab332ecf96b7cba621e3e535408481e6ab83ca614bc2b502f` |
| `write_score_edit.json` | `9fc5f359133e76fd464b13ed34eb13eb74bf25d71edeb0add0c8d8eae992f9b5` |
| `write_add_edit.json` | `7cf7dd778e4852305d5ed902dfe75b7eece7bc07ffdc353bcf83cc3a7fd8f167` |
| `build_s_pool.json` | `6080487c8efa6682259ecd977f517a151a8e8aecf80d7aea45e6a23911a943a4` |
| `write_score_add.json` (not in `BASE_SHA256`; used unchanged) | `0c1679b47cdbdc340bfa7f959d94c818a84a144dff114991382349b621c5ba74` |
| `build_length_rules.json` (not in `BASE_SHA256`) | `3800e52ae3c7f4fd2c886f14ba973b814c98b735d4d166f50a7fc133358de5b3` |
| `scripts/stage1_s1/settings/oext_unit.json` (§1.14) | `3959eae7264f56f613f5d7cd54e69081d8985ef7cbce2962243f6685e3581189` |
| `scripts/stage1_s1/settings/oext_eval.json` (§1.14) | `2ad9893849248a8fb61d04cf7badbd7fb398915020f196904849d500df08f5a5` |
| `scripts/stage1_s1/settings/lean_eval_job.json` (§1.13) | `b0ab19ec28946334e4a033897c1097894fdf5797507f6a516614afc1c2c22acd` |

**Table D. Engine, kit and sealed inputs (HEAD; M).**

| Item | SHA-256 |
|---|---|
| Engine X identity (`experiments.safety_selection.common.code_identity()["sha256"]`, main environment, HEAD) | `472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892` |
| `runkit/stage1-78b/rules_78b.py` (RK; the E caps of §1.15) | `57ad4148ab781dd94a56d1fb6e765441a618c0c012fc6795d52239ccb15e3ba0` |
| `runkit/stage1-78b/measured-basis-78b.json` | `fc92a568b0556f7718a1c27e488e62072df758942deef0ad7dee6d9d80cddc40` |
| `.ai/inputs/stage1-commitments-20261016/s-pool/s_pool_record.json` | `bcca59ac0f8c15c354b9d9b124c1e17211c7e602800424f40292160934383c6f` |
| `.ai/inputs/stage1-commitments-20261016/add-s1/add_edit_record.json` | `311957a442009bbb71995690d9d031cd8dd0a6ced24982ee7655baae927a01ba` |
| `.ai/inputs/stage1-commitments-20261016/length-rules/edits/octile_0.json` (H1, OLMo) | `f5b1762f662e931235f798497248b2f342e6d2b2011ce5a0bfecf53678b4def7` |
| `.ai/inputs/scale-78b-length-rules-llama3-20261105/out/edits/octile_0.json` (H1, Llama) | `9a01637ec63dc38f6e4dec646a0bc4b8c00c36521fa8831fe4fb87e8df3a1c5f` |
| `.ai/inputs/scale-78b-length-rules-llama3-20261105/out/MANIFEST.json` | `24c1305ab59e979feb8eb88dc3977ada132cad082f41449d4acde20f2bcdda61` |
| `.ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py` | `a2b0a66c4e3f9f044ad5e2090cd58af195bcdfac3f372822eb1c14805495f5a3` |
| `.ai/inputs/scale-78b-s1-llama3-20261105/out/MANIFEST.json` | `a398627455a96356f590b884ea5acaeae4bedb60a2e44b2bc27a8008b83713e0` |
| `.ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json` (PP7) | `2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c` |
| `.ai/inputs/gate-b-anchors-20261008/out/anchor_prompts.sealed.json` | `5d23fa2bd02caa3b9d4cd537350e08684793d0e8711c9b2b94900154f45e2349` |
| The text files named by hash (in `tmp/`; not opened here): the anchor prompt list; `s1.json`; `s3_safe.pool.json`; `s4_candidates.json`; OLMo `add_s1.json`; Llama `add_s1.json` | `78467c97c40e7e9fd39e8061219517853e7292a25881700da5e9115604117b97`; `389c20ad00261b1a304d3dd9f14a113a0b05bcec63758262af1b1629d48e0480`; `6801652cb506f9626575f6e156e103682308830e4e5ef1cb299dd3fa00021fed`; `798613c4e5d32caaf51b255b2413395a1477b377f0b97f85933efdc5b35cf17d`; `904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10`; `6942699398ade7f7ddb6f5b47b06e8b253de6ff9bbd142b8138acc061468dd0a` (R: PINS, the s-pool record, PP5, the Llama S1 MANIFEST) |

### 1.18 Choices made after the stage-1 reading (ruling 16; ADD A16's form)

Every choice in this section was recorded on 5-6 Nov 2026, after the OLMo-2-1B stage-1 reading (P1 §0 item 1) and after stage 1b's construction checks (P1 §0 item 8). Each is listed with what it reads. **None reads a 1B repair outcome as its basis.**

1. **PP1** (the untuned pass and the add-edit writer take MAIN_F as recipe S; recorded 2026-11-05T18:12 UTC): reads `make_untuned_answers.py:84-93` and the recipe fields. A plumbing rule; the value of `max_train_tokens` is the same either way. Not a choice after a result.
2. **PP2** (two untuned-answers calls): reads the unchanged 1B code's exit-3 behaviour (verify-E D1). Not a choice after a result.
3. **PP3, PP8** (the kind names `rep_pass`, `a1_pass`; their caps; the S_78 kinds): read code and caps. Not a choice after a result.
4. **PP4, PP16** (engine X for the wrapper kinds; `X_ONLY_KINDS`): read `s1common.py:590-592` and the kit's rules. Not a choice after a result.
5. **PP5** (S1 reuse on OLMo-2-7B by hash; a new Llama S1 edit): reads encode counts and hashes (track F). Not a choice after a result.
6. **PP11** (L1's first scanned block 10 of 32; recorded 2026-11-06T07:30 UTC): **chosen after the stage-1 reading.** It reads the 1B rule's form only (`scan.first_block` 5 of 16, the same relative depth). The authors knew L1's 1B results when it was written: P2 = U(R) − U(L1) read *equivalent* (+2.03 pp) with L state *undetermined* (P1 §0 item 1), and L1 did not rank stage 1b's planted leaf (P1 §0 item 8). The rule does not read either value; PP11 states "the rule's 1B form, not L1's 1B result". Labelled, as PP11 itself labels it.
7. **PP12** (L1's modules per family; same record time): **chosen after the stage-1 reading**, with the same knowledge as item 6. OLMo-2-7B keeps stage 1's modules; Llama-3.1-8B takes the 1B settings file's llama entry, "written there for stage 2 before stage 1 ran" (PP12). It reads the 1B settings, not an outcome. Labelled. Track M's reading that each family's file carries its own entry only is a build choice under PP12 (§14 item 10).
8. **PP15** (`rep_pass`'s 4.75 h cap) and **PP14** (idle-storage lines): read the stage-1 kit's estimate and KCR's storage rate. Not a choice after a result.
9. **The S4 keep target 192 and the dose lists** (§1.11): ruling 12 (P1 §10, §13 item 1), already labelled in P1: added after the stage-1 reading because S4 was the best feasible repair at 1B. The 1B keep count (57 of 64) sizes the fallback only (P1 §13 item 9).
10. **Reusing stage 1's S-pool lists and H1's rule** (§1.7, §1.8): P1 §14 item 1 and CHECK C6, written before this section; they read files and manifests. Not a choice after a result.
11. **A1 per family by the frozen contract** (§1.5): ADD A1, A2 (P1 §13 item 10: build and process rulings). Not a choice after a result.

### 1.19 Limits of the scorer section

- **CUDA paths and real 7-8B models are untested** in the wrapper's tests (tiny random CPU models; R: MFIX §7 item 5). The first pod of each kind is the first real run.
- **Parity is of the plumbing**: the wrapper runs the 1B script's own `main()`, so the outputs are the 1B script's by construction; the untuned-answers parity through `main()` ran on the engine's tiny model, whose answers are all capped at the fixture's 5 new tokens (R: SC §6 item 7).
- **The Llama anchor job** encodes the 1B list's 64 harmful pairs with Llama's tokenizer; the pinned script stops if one does not encode under 3072 tokens (R: SC §6 item 8; `make_anchor_answers.py:117-121`). Low risk (I: the pairs encoded under OLMo's tokenizer with the same limit; the longest is 84 prompt tokens, 465 total; R: FOCUS "Gate C anchor-prompt list SEALED", recorded 2026-10-08T16:14 UTC). No fallback is ruled (§14 item 7).
- **The E caps are estimates** until each kind's first run (KD6; §1.15).
- **The scorer pods are not yet runnable** for `o_only` and `c0` (§1.13, §1.14), and the kit's runner at HEAD runs `arm` and `a0_arm` only (R: `runkit/stage1-78b/setup/job_runner_stage1.py` module doc). The scorer kinds' runner commands come with the kit's next rounds (T4; PLAN T4 step 3).

---

## 2. Arm rules outside the scorer section [B+C]

**To be written before block A's first pod.** The R and a0 rules are P1's (§3, §5); the arms run under the family's main config (P78:99). What remains for this section (P1 §14 items 1, 12): the edit files' binding to each family's manifest for block A and B (the Llama sealed set's R and unit files; OLMo's SEAL and R_d11-R_d16), the dose edits' hashes once written (§1.11), and the token-accounting line beside every arm (S1L §5 item 1 via P78:379).

## 3. References [B+C]

**To be written before block A's first pod.** P1 §14 item 4: the safety prompt; adapter scaling (OLMo-2-7B from the Mac adapters; Llama-3.1-8B from retrains); recipe G (OLMo-2-7B units in hand; Llama-3.1-8B 3 new runs); B+Qi (on Y after its basis is measured, KD6/KD9; unpaired and labelled if Y ≠ X); Safe LoRA.

## 4. Limits: O, τ_O, L, τ_L [B+C]

**To be written before block A's first pod.** P1 §14 item 3 and CHECK M1: O against the family's own untuned model on PR4 §3.6's 500-prompt O set; which evaluation bank the 7-8B arms use; whether the `arm` kind evaluates O and L in the same job or needs a separate job; the τ_O grid; τ_L from the family's a0 seeds (S1B REQ-19 form). The untuned units' O pass is in §1.14.

## 5. The S4 add-dose arm's reading [B+C; secondary]

**To be written before block A's first pod.** P1 §10 and §14 item 5: the O and L forms for AD1, AD2 and the dominance-rule question; the token-accounting line. The dose lists' construction is in §1.11.

## 6. Judges [B+C]

**To be written before block A's first pod.** P1 §14 item 6: HarmBench and Granite pods, one device per contrast; which arms and blocks are judged; the "harm" wording rule. Already settled (ADD A9): N's R arms are HarmBench-judged, report-only, with block A's judge pods; Llama a0-1103 gets the same judge files as block A's units on the same pods; no Granite judging for TC.

## 7. The coherence screen [B+C]

**To be written before block A's first pod.** The rule is settled (ADD A4, A11; P1 §14 item 7, §15): PR4 §3.7's pooled bar for the main study's arms; per-seed counts reported; a seed above 10% flagged; no arm or seed dropped; the frozen Gate B G1 code, report-only, for N's R arms. This section writes the form out and names the screen's code hash.

## 8. Cost conventions [B+C]

**To be written before block A's first pod.** P1 §14 item 8; PR4 §10.1-§10.4 (C-full, C-lean, c0's role, charging) carried to 7-8B. c0's job form is in §1.13.

## 9. The confirmation [B+C]

**To be written before block A's first pod.** P1 §14 item 9 and §13 item 5: at most 2 contrasts per family, chosen by the frozen stage-3 pick rule (the two primary contrasts with the largest |t| among those reading *better* or *worse*); engine Y; fresh seeds 9101-9999; the sealed 200-prompt hidden subsample; "confirmed" by the 95% interval on the hidden subsample only.

## 10. SR-2's error-rate check [B+C]

**To be written before block A's first pod.** P1 §14 item 10: a simulation that the variance-only interim re-estimate changes the error rate little (P78:204).

## 11. Alpaca's home

**To be written before block A's first pod.** P1 §14 item 11: [B] Llama-3.1-8B, reduced; [C] OLMo-1B (RP decision 7).

## 12. The Llama sealed set's manifest-named files

**To be written before block A's first pod.** P1 §14 item 12. S1 on the Llama manifest is built (§1.9) and H1 is in its own sealed folder (§1.7). The R and unit files (MANIFEST `2a1db220…`, PP7) shared with stage 2 are named here; S3, S4 and the dose edits are named by model (CHECK C6).

---

## 13. Change log against P1 §14 and P78 §11

| # | Source place | It said | This text says | Why |
|---|---|---|---|---|
| 1 | P1 §14 item 2 | the scorer rules committed with code hashes before any scorer output is read | §1, with the hashes of §1.17 | ADD A10; CHECK M4 |
| 2 | P1 §14 item 1, P78:377 | "L1 (the layer rule from the any-model Part C scripts)" | the unchanged 1B scripts through one wrapper; first block 10 of 32; modules per family | SC §1; PP11, PP12 |
| 3 | P1 §14 item 1 | "the S-pool and S1 (the same 48 S-pool rows, re-bound)" | S-pool lists reused as sealed; OLMo S1 reused by hash; Llama S1 new | PP5 |
| 4 | P1 §14 items 1-2 | "the per-family untuned-answers pass as the shared source of S3, S4, S4_96 and S4_192" | two calls per pod: S3 with the losses, then S4 alone with the doses | PP2 |
| 5 | P1 §3.7, §12 | the untuned pass's recipe not stated | MAIN_F as recipe S; the recorded `recipe_s` hash is MAIN_F's | PP1 |
| 6 | P1 §12 | "`rep_pass` (A1)" | `rep_pass` = REQ-3's representation pass; `a1_pass` = A1's attributes pass; each with its own cap | PP3, PP8, PP15 |
| 7 | P1 §12 | each scorer kind single-job with an explicit E cap | the caps per family at HEAD (§1.15) | KD6; RK |
| 8 | P1 §11 EM-1 | every 7-8B arm on X unless Y's certificate passed | the wrapper kinds on X only; the retrain and `a1_pass` by ruling 10 | PP4, PP16 |

## 14. Open items for the lead (gaps found while writing; this text decides none of them)

1. **No 7-8B route for the untuned units' O pass or for c0.** `oext_unit.json` pins the 1B manifest `9ed61826…` and allows only the 1B recipes B, G and S (R: `scripts/stage1_s1/settings/oext_unit.json:52-66`); `lean_eval_job.json` allows only the two 1B recipes (R: `…/lean_eval_job.json:38-39`). So `o_only` (§1.14) and `c0` (§1.13) refuse MAIN_F on both families as the S1 package stands (I from the pins; not run). CHECK M1 needs the O pass before block A. A route (for example a scale78b wrapper in WRAP's pattern, or re-derived settings) needs a build, a ruling and this section's text before its outputs are read.
2. **PP16 is not in the kit at HEAD.** RK has no `X_ONLY_KINDS`; `stage1_rules.py:234` has `X_ONLY_KINDS = ()` (M: `grep`). The kit's next round builds it. Part 2's freeze should name the kit's file hashes after that merge.
3. **The E caps (§1.15) are HEAD's RK.** If the kit's next round changes RK, the lead re-reads §1.15 at the freeze.
4. **The kit bundle must carry and pin WRAP and `settings/`** beside `scripts/stage1/` (R: SC §6 item 10). At HEAD nothing in `runkit/stage1-78b/` pins a scale78b hash (R: MFIX job 2; M there).
5. **How Part 2 records the hashes after a pin fill.** Each fill (anchor bank, S_78, A1's unit) changes PINS, the reached settings files, `PINS-78B.json` and WRAP (§1.16). Part 2 commits today's values. Whether each fill is a dated amendment to Part 2, or a recorded lead step in FOCUS with `MAKER --check` and the differ-only test as its evidence, is not ruled.
6. **The S-pool lists under the 7-8B codecs.** The lists were filtered at 1B under OLMo-2-1B's tokenizer at 3072 / 1536 (R: the s-pool record's `limits`). The 48 S1 rows encode on both families (PP5; the Llama S1 build). The 861 `s3_safe` and 512 `s4_candidates` prompts are not checked under the Llama codec (or under OLMo-2-7B's, if it differs; not checked here). A failing prompt would leave the S3 ranking or fail S4's keep rule; what the unchanged 1B pass does on a prompt that `encode_generation_prompt` refuses was not read here (I). A $0 encode count (counts only) on both codecs before the untuned pod would settle it.
7. **The Llama anchor job has no ruled fallback** if a harmful pair does not encode (§1.19).
8. **The classifier's use at 7-8B.** Ruling 11 lists the kind. PR4 §9.2 makes the 1B classifier "scored only (claims limited to rank overlap)". No 7-8B ruling names its reports.
9. **The c0 unit at 7-8B** (F's R_1 at 1101, train only, then the lean job) is SC's and the kit's form; no ruling text names it. At 1B LN-27 adopted option (i) on Y's C1 pod (PR4 §10.3); at 7-8B PP16 makes c0 X-only.
10. **PP12's one-entry-per-family files** are track M's reading of "per family" (MFIX §7 item 3). The values are the same either way.
11. **A1's golden test is defined on engine X** (R: `write_score_edit.py:29-30`; PR4 §1.5, ADD-4.8: "after Y they need a new pin"). The writer accepts a unit whose code identity equals the `code_sha256` pin (R: `write_score_edit.py:93`). If `a1_pass` runs on Y after the certificate, the re-pin of the golden test is not specified.
12. **Track M updated the text of `classifier_recipe_78b`** before copying it into settings (MFIX §7 item 4). The substance (classifier in `S78_KINDS`) is R at RK:141.
13. **PP4's cite.** PP4 cites `s1common.py:589-591`; the check is at 590-592 (M: track M's line test; MFIX job 3). PP is the lead's file.

---

*End of the scorer section's draft. The file is committed by the lead by explicit path; §0's N values and §2-§12 are added before the freeze.*
