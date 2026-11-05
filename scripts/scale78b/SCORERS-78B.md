# The 7-8B scorer layer (`scripts/scale78b/scorers_78b.py` and `settings/`)

Track E of the 7-8B $0 build round (5 Nov 2026), for the main-study lead (General Implementation X). Sources: Part 1
of the 7-8B pre-registration (`research/experiments/2026-11-05-78b-preregistration-part1.md`, frozen 5 Nov 2026)
sections 2, 3.7, 10, 12 and 14; the lead's rulings and their addendum (A1, A2, A3, A13); the readiness plan T6 and its
check (C1, C6, M1, M2); P78:357 ("the any-model Part C scripts are new files under `scripts/scale78b/` with a 1B
parity test; the 1B scripts stay byte for byte"). Labels: M measured (the command), R read (path:line), E estimate
(basis), I inference. Nothing here is a run, a spend or a change to any 1B file.

## 1. What this is

The 1B scorer scripts under `scripts/stage1/` are model-agnostic in code (the layer count, hidden size and final norm
are read from the loaded model; the token limits from the recipe; the codec from the engine's loaders; R:
`scripts/stage1/representation_pass.py:84-93`, `settings/representation_pass.json` `model_agnostic`). What pins them to
OLMo-2-1B is their settings files (recipe, manifest, model, anchor bank, the S4 keep count) and each script's literal
`SETTINGS_SHA256`, which refuses any other settings file (R: `make_untuned_answers.py:360`, `representation_pass.py:429`,
`score_l1_larf.py:303`, `score_classifier.py:145`, `score_s3_datarx.py:141`, `write_score_edit.py:281`,
`write_add_edit.py:196`, `build_s_pool.py:444`).

So the 7-8B layer is three new files and a settings folder, and no copy of any scoring code:

| File | What it is |
|---|---|
| `settings/pins_78b.json` | The one place with every per-family value and every pin that is not known yet (null, with the event that fills it). |
| `make_scorer_settings_78b.py` | Derives `settings/<script>__<family>.json` (18 files) and `settings/PINS-78B.json` from the 1B settings files (hashed against its pins) and `pins_78b.json`. `--check` compares the committed files with their regeneration. |
| `settings/*.json` | The derived files, in the 1B files' own schema (`kind`, `name`, `engine_x`, `label_entries` unchanged, so the 1B `check_settings` accepts each on its 1B name), plus a `family_78b` block (family, manifest, main recipe, the 1B file it derives from and its SHA-256, `waits`: each null pin, its event and the commands that need it). |
| `scorers_78b.py` | The wrapper: `KIND --family F <the 1B script's own arguments>`. Imports the 1B module, hashes it against `STAGE1_CODE`, loads the family's settings by the index's pin, runs the family preflight, then the 1B script's own `main(argv + ["--settings", file])` with the module's `SETTINGS_SHA256` (and, for `rep_pass` and `classifier`, `representation_pass`'s pool-pins globals) replaced for that call only and restored afterwards: the pattern of the 1B D-2 wrapper `scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py` (R: its module doc and `run_base`). For `untuned_answers` it then derives the nested dose lists (Part 1 section 10). |
| `tests/scorers/` | 93 tests: the settings' derivation and schema, the nesting and sizing rules, parity on the 1B fixtures for all nine kinds, the family acceptances and refusals on the real prepared manifests, the null-pin refusals, and (fix round 3) the two untuned-answers calls end to end on a synthetic family with the S4 fallback firing, the PP2 refusal, the exit-3 record, the doses refusal after the pass, the repeated-flag rule. |

## 2. The map: kind -> 1B script, settings, inputs, what differs per family, what it waits for

Short names: F = `olmo2-7b` | `llama31-8b`; P_F = the family's prepared set (`tmp/kt-prepared/prepared-kt-dolly-olmo2`,
manifest `9ed61826…`, the same set as OLMo-2-1B's; `tmp/kt-prepared/prepared-kt-dolly-llama3`, `c52a50af…`; R: Part 1
section 2.1, `runkit/stage1-78b/rules_78b.py` MANIFESTS); MAIN_F = the family's main recipe
(`experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json`, config_sha256 `18cc31d7…`, model
`allenai/OLMo-2-1124-7B-Instruct` revision `470b1fba…`; `study-kt-llama31-8b-r64-b5e5-mb2-20261010.json`, `74758af1…`,
`meta-llama/Llama-3.1-8B-Instruct` revision `0e9e39f2…`; M: `config_sha256(load_recipe(...))` on 5 Nov 2026); S_78_F =
the family's recipe S_78 (null until the anchor job and `make_recipe_s78.py`; addendum A1); BANK_F = the family's
anchor file `anchors.json` (text, under tmp/) whose SHA-256 the anchor job's `anchors.sealed.json` records as
`anchor_file_sha256` (null until then). Every recipe, manifest, model and token limit is read by the 1B code from the
files given; the settings only pin the expected hashes. The token limits are the same in every recipe here
(`max_train_tokens` 3072, `max_prompt_tokens` 1536, generation batch 32, `max_new_tokens` 2048; M: the three recipes
printed on 5 Nov 2026), so the only per-family limit is the codec (the family's tokenizer).

| Kind (Part 1 section 12) | What runs | 1B script | Settings file | Inputs (each by PATH:SHA256 where the 1B script asks) | Differs per family | Waits for |
|---|---|---|---|---|---|---|
| `untuned_answers` (pod, E cap; **two calls per pod, PP2**) | call 1, the S3 list with the losses: `scorers_78b.py untuned_answers --family F --recipe MAIN_F --recipe-s MAIN_F --list s3=s3_safe.pool.json:6801652c… --loss s1=s1.json:389c20ad… --loss s3_safe=s3_safe.pool.json:6801652c… --out <job>/untuned`; call 2, the S4 list alone with the doses block: `scorers_78b.py untuned_answers --family F --recipe MAIN_F --recipe-s MAIN_F --list s4=s4_candidates.json:798613c4… --out <job>/untuned-s4`. The wrapper refuses `--list s4` beside another `--list` or a `--loss` (section 3: the unchanged 1B code's exit 3 keeps only `answers_*.json` and the record, so one call would lose `s3_orig.pool.json` when the S4 fallback fires; verify-E D1). The S3 call cannot exit 3. The pod's E cap covers both calls (verify-E C3; the kit round) | `make_untuned_answers.py` | `make_untuned_answers__F.json` (`doses.calls_78b` states the two calls) | the 1B sealed lists (text; under tmp/; hashes R: `.ai/inputs/stage1-commitments-20261016/s-pool/s_pool_record.json`); MAIN_F twice (PP1, section 4) | REC and S pins = MAIN_F (PP1); model and codec through the engine's loaders from MAIN_F; `lists.s4.keep` 192; the `doses` block (call 2 only) | nothing: both calls run first (section 4) |
| the anchor job (pod, E cap; "the anchor job's inputs") | `scripts/make_anchor_answers.py --prompts <the sealed full anchor prompt list, 78467c97…, text under tmp/> --recipe MAIN_F --out <job>/anchors` (the pinned Gate B script, unchanged; it reads the model from REC and requires `query_bank` "ref"; R: `scripts/make_anchor_answers.py:30, :107-110`) | `scripts/make_anchor_answers.py` | none (its constants are the list's pin and the counts 128/64/64) | the full anchor prompt list; MAIN_F | the model (through REC); `anchors.json` holds the family's own Safe answers (per model; P78:377); its record's `provenance.recipe_sha256` = MAIN_F's hash, which `make_recipe_s78.anchored_to` requires | nothing |
| then S_78_F | `make_recipe_s78.py --family F --anchors-sha256 <anchor_file_sha256> --out experiments/safety_selection/configs/<name>.json`; the lead commits it and fills `pins_78b.json` (section 5) | `scripts/scale78b/make_recipe_s78.py` (track C) | `pins_78b.json` `recipe_s78`, `anchor_bank_sha256` | the anchor record | per family | the anchor job |
| `rep_pass` (pod, E cap): REQ-3's representation pass for L1, S3, DataShield-style and the Gate C reproduction (PP3: A1's pass is `a1_pass`, the next row) | `scorers_78b.py rep_pass --family F --prepared P_F --recipe S_78_F --anchors BANK_F --pool s3_safe.pool.json:6801652c… --out <job>/representation`; then the s3_orig pass: `… --pools-only --pool s3_orig.pool.json:<the untuned pass's record names it> --out <job>/representation-s3-orig` (the stage-1 kit's two passes; R: `runkit/stage1-olmo/setup/job_runner_stage1.py:24-30`) | `representation_pass.py` | `representation_pass__F.json`; pool pins `representation_pools__F.json` (both pools null: no plant or decoy pool at 7-8B, EM-4) | P_F; S_78_F (its `attribution.query_bank` names BANK_F); BANK_F; the s3_safe pool; the family's s3_orig pool | manifest, model, recipe S_78, anchor bank; n layers and hidden size from the model (32 and 4096 for both families, read, never assumed) | the anchor job; S_78; the untuned pass (for s3_orig) |
| `a1_pass` (pod, its own E cap, 16.5 h at most; PP3; RP:43's 6-11 h): A1's attributes pass | the engine's attributes job on the family's a0-1101 retrain (S_78) with BANK_F: `make-job attributes --a0-state q=<retrain unit> --a0-state e1=<retrain unit> --groups <the 8 unit groups> --anchors BANK_F --pin-code`, then `attributes` (the stage-1 kit's `a1_rescore` form; R: `job_runner_stage1.py:49-53`) | the engine (no script here); its consumer is `write_score_edit.py a1` | `write_score_edit__F.json` (`a1.attributes_unit`: six null pins) | the retrain's q and e1 states; BANK_F; S_78_F | per family; the engine's own job, so ruling 10 and A13 govern its engine (X, or Y after the certificate; Part 1 section 3.7), not the wrapper kinds' engine-X rule (PP4) | the anchor job; S_78; the a0-1101 retrain |
| `l1_scan` (pod, E cap) | `scorers_78b.py l1_scan --family F --prepared P_F --recipe MAIN_F --anchors BANK_F --out <job>/l1-scan` (the wrapper prepends `scan`) | `score_l1_larf.py scan` | `score_l1_larf__F.json` | P_F (the sealed sample of 64 Dolly prompts, key `l1.scan`); MAIN_F; BANK_F (its 64 harmful prompts) | manifest, REC, anchor bank; `scan.first_block` null (Part 2's layer rule; the 1B value is 5 of 16); `scan.modules` by `model_type` (olmo2 and llama entries carried from the 1B file) | the anchor job; Part 2's L1 layer rule |
| `classifier` (pod, E cap; **under S_78**, PP4) | `scorers_78b.py classifier --family F --prepared P_F --recipe S_78_F --anchors BANK_F --out <job>/classifier` (no `--pool`). The kit's key check must let `classifier` through as an S_78 kind (`rules_78b.py` `S78_KINDS` holds `retrain` and `rep_pass` at HEAD 953f520; section 6 item 3; verify-E D3) | `score_classifier.py` | `score_classifier__F.json` (+ the pool pins file) | P_F; S_78_F (its guard); BANK_F | manifest, model, recipe S_78, anchor bank | the anchor job; S_78 |
| `c0` (pod; engine X) | the engine's `make-job run-one` of the family's R_1 at 1101 (its sealed `R_d1.json`), train only, then the S1 package's `scripts/stage1_s1/lean_eval_job.py run --expect-adapter-fingerprint …` (R: `job_runner_stage1.py:45-47`) | the engine and the S1 package (frozen; not this layer's) | none here | the family's sealed R_d1; MAIN_F; the O-ext inputs | per family | the kit round (track K) |
| `o_only` / `regenerate` for the untuned units (pod; CHECK M1) | the engine's `make-job run-one` (train only) and the S1 package's O-ext unit pass (`scripts/stage1_s1/oext_unit.py run --untuned` for the untuned unit; R: `job_runner_stage1.py:19-23`) | the engine and the S1 package | none here | MAIN_F; the O set (500 prompts) and L | per family; Part 2 names the evaluation bank (M1) | the kit round; Part 2 |
| Mac: `l1_score` | `scorers_78b.py l1_score --family F --prepared P_F --scan l1_scan.json:SHA --rows representation_rows.jsonl:SHA --summary representation_pass.json:SHA --out out/l1-score` | `score_l1_larf.py score` | `score_l1_larf__F.json` | the scan and the rep_pass outputs | manifest; `pins.representation_pass_settings_sha256` = the family's rep_pass settings file's SHA-256 | rep_pass; l1_scan |
| Mac: `score_edit scorer` (L1's edit) | `scorers_78b.py score_edit --family F scorer --name l1 --scores l1_scores.json --scores-sha256 SHA --prepared P_F --out out/l1-edit` | `write_score_edit.py scorer` | `write_score_edit__F.json` | `l1_scores.json` | manifest (rows 4800, units 8, rows per unit 600 on both sets; M: the family tests' CLI run on both copies) | l1_score |
| Mac: `score_edit a1` (A1's edit) | `scorers_78b.py score_edit --family F a1 --unit <the attributes unit folder> --prepared P_F --out out/a1-edit` | `write_score_edit.py a1` | `write_score_edit__F.json` | the A1 attributes unit | the six `a1.attributes_unit` pins (null) | A1's pass |
| Mac: `s3_score` | `scorers_78b.py s3_score --family F --rows …:SHA --summary …:SHA --s-pool-record s_pool_record.json:bcca59ac… --answers-record untuned_answers_record.json:SHA --out out/s3-score` | `score_s3_datarx.py` | `score_s3_datarx__F.json` | the rep_pass outputs (both pools listed); the 1B S-pool record; the family's untuned record | `pins.representation_pass_settings_sha256` | rep_pass (both passes); the untuned pass |
| Mac: the S3 pick | `scripts/stage1/write_score_add.py` unchanged (its settings pin no family value; R: `settings/write_score_add.json`) | `write_score_add.py` | the 1B file | `s3_scores.json`; the s3_safe pool | nothing | s3_score |
| Mac: `add_edit` (S1, S3, S4, S4_96, S4_192) | `scorers_78b.py add_edit --family F --prepared P_F --recipe MAIN_F --list <s1.json \| s3.json \| dose_s4.json \| dose_s4_96.json \| dose_s4_192.json>:SHA [--combine-with NAME=remove_edit:SHA] --full-out tmp/<…>/full --out out/add-<list>` | `write_add_edit.py` | `write_add_edit__F.json` (lists s1 48, s3 48, s4 48, s4_96 96, s4_192 192, s4_top null) | the lists (text; under tmp/) | manifest; recipe (MAIN_F, section 4); the codec = P_F's tokenizer from its manifest (offline cache) | the lists |
| Mac: `s_pool` (only if Part 2 rebuilds the S-pool per family) | `scorers_78b.py s_pool --family F --config experiments/safety_selection/configs/study-v3-data-inj05.json --sources <PKU root> --prepared P_F --anchors <the full anchor prompt list> --rec MAIN_F --full-out tmp/<…>/full --out out/s-pool` | `build_s_pool.py` | `build_s_pool__F.json` | the PKU sources; ANCH; the data config | manifest; REC; `expected_evaluation_forms` 11,954 carried (I; L9 (2) stops the run if the Llama banks differ) | Part 2's decision |

Each command line is the 1B script's own argument list after `KIND --family F` (R: each script's `main`); the wrapper
adds `--settings <the family's file>` itself and refuses a `--settings` of the caller's. `-I -B` as the brief says.

**Engine X (PP4; verify-E D2).** Every wrapper kind in this table (`untuned_answers`, `rep_pass`, `l1_scan`, `classifier`
on the pod; `l1_score`, `s3_score`, `score_edit`, `add_edit`, `s_pool` on the Mac) runs on engine X (`472fc7f6…`): each
derived settings file carries the 1B file's `engine_x`, and the frozen `check_settings` refuses another engine identity
(R: `scripts/stage1/s1common.py:589-591`). A run on engine Y needs the settings re-derived for Y (a new `engine_x`, a new
`PINS-78B.json`, a new `PINS_FILE_SHA256`) by a recorded step; none exists. The rule is written in `pins_78b.json`
`shared.engine_rule_78b` and in every settings file's `family_78b.engine_rule`. The engine's own jobs (the a0-1101
retrain, `a1_pass`) follow ruling 10 and A13 instead. The kit packs scorer pods with engine X; the Mac steps run on a
checkout whose engine identity is X.

## 3. The S4 add-dose arm (Part 1 section 10; CHECK M2)

- `lists.s4.keep` = 192 in `make_untuned_answers__F.json`: the 1B code stops after the chunk that holds the 192nd keep
  (`answer_list`, `keep_target`; R: `make_untuned_answers.py:157-178`), and the first 48 kept are the same rows a 48-keep
  run gives (each 32-prompt chunk is its own call; M: `tests/scorers/test_scorers_78b_parity.py::test_the_first_keeps_do_not_depend_on_the_stop_rule`,
  the 1B test's form at 6 against 2 on a 40-prompt list).
- The wrapper then derives `doses/dose_s4.json` (the first 48), `dose_s4_96.json`, `dose_s4_192.json` (nested prefixes
  of the kept order) from `answers_s4.json` and the record's kept flags, plus the text-free `s4_doses_record.json`
  (`nested_doses`, `build_doses`; M: `test_s4_doses_78b.py`, 10 tests). The fallback (DOSE `pre_set_fallbacks[0]`):
  fewer than 192 kept after 512 prompts gives `dose_s4_top.json`, all kept rows, named `s4_top`, with the count in the
  record, exit 0 with `fallback_fired` true; fewer than 48 kept: exit 3, no dose file.
- The S4 list runs alone in the pod's second call (PP2; section 2). In the fallback case the unchanged 1B code exits 3
  and keeps only `answers_s4.json` and the record (R: `make_untuned_answers.py:317-318`), so any other list in that call
  would lose its outputs; the S3 list's `s3_orig.pool.json` is the first call's and survives (M:
  `test_untuned_two_calls_78b.py::test_two_calls_the_s4_fallback_fires_and_the_s3_outputs_survive`, end to end through
  the wrapper on a synthetic family: the fallback fires in call 2, call 1's pool and record are untouched and the
  stage-1 kit's completeness check `stage1_rules.s3_orig_pin` accepts them). A refusal in the doses step comes after the
  1B pass has written: the wrapper prints `REFUSED after the 1B pass: the 1B outputs are written in <out>; the doses
  were not written (...)` and exits 2 (verify-E C4; tested).
- Sizing (the settings' `doses.sizing`; M: `candidates_needed(192, 57, 64)` = 216): at the 1B keep rate 57 of 64 (89%),
  192 kept rows need about 216 of the 512 candidates, 7 chunks of 32 (224 prompts); the list holds 2.37 times that.
- Known quirks of the unchanged 1B code at keep 192, documented in the settings: a keep after the 192nd is labelled
  `kept_after_the_48th` (a fixed string; R: `make_untuned_answers.py:171`); the W1-06 loss table's `s4` entry covers all
  192 kept rows, and is omitted in the fallback case (the 1B code's exit 3 drops it; R: `:300-304, :317-318`).
- `write_add_edit__F.json` takes each dose list by its `name` (s4, s4_96, s4_192; `s4_top` has `rows` null until the
  fallback count is known).

## 4. Two plumbing choices that are not scientific changes; the first is ruled (PP1), the second waits for Part 2

1. **The untuned-answers pass takes the family's main recipe as `--recipe-s` (ruled: PP1, 5 Nov 2026)** (`pins_78b.json`
   `shared.untuned_recipe_s` = "main"). `make_untuned_answers.py` reads recipe S only for `model.max_train_tokens` and
   requires REC and S to agree on the four model fields (R: `:82-93`); S_78 is MAIN_F with only the four recipe-S
   fields changed (R: `make_recipe_s78.py:5-10`, its test), so the value is the same. This lets the pass run before the
   family's anchor job (addendum A2 orders the anchor job, S_78, the retrain; the pass needs none of them). The recorded
   `recipe_s` hash is the main recipe's; Part 2 states this (PP1). The same holds for `write_add_edit__F.json`'s
   `recipe_sha256`. The key "s78" stays in the maker as the explicit alternative; using it would be a Part 2 change.
2. **`l1_scan`'s `scan.first_block` is null**, so the scan refuses until Part 2's L1 layer rule fills it (Part 1 section
   14 item 1). The 1B value is 5 of n = 16 blocks; at n = 32 the candidates are the same share (round(5 n / 16) = 10) or
   the same absolute 5. Not decided here. The `llama` modules entry (`self_attn`, `mlp`) is carried from the 1B file,
   where it is marked "stage 2 reading, not used in stage 1 … re-decided" in a 7-8B or Llama settings file; Part 2
   confirms or changes it before the Llama scan.

## 5. Which pins wait for which event, and how a pin is filled

| Pin (in `pins_78b.json`) | Event | Settings files it reaches | Commands that refuse until then |
|---|---|---|---|
| `families.F.anchor_bank_sha256` | F's anchor job: `anchors.sealed.json` `anchor_file_sha256` of its committed record | representation_pass, score_l1_larf, score_classifier, write_score_edit (a1 query_bank) | rep_pass, classifier, l1_scan, score_edit a1 |
| `families.F.recipe_s78.{path, config_sha256}` | `make_recipe_s78.py` after the anchor job, the lead's commit (A1, A2); the same value as `rules_78b.py` RECIPE_S[F] | representation_pass, score_classifier, write_score_edit (a1 recipe) | rep_pass, classifier, score_edit a1 |
| `shared.l1_first_block` | Part 2's L1 layer rule | score_l1_larf (both families) | l1_scan |
| `families.F.a1_attributes_unit.{complete_sha256, retrain_complete_sha256}` and the a1 `code_sha256` | F's a0-1101 retrain under S_78, A1's attributes pass on its states; the engine that ran them (X or Y) | write_score_edit | score_edit a1 |
| `families.F.untuned_pass.*` | F's untuned-answers pass (record only; the consumers take PATH:SHA256 on the command line) | none (the map's record) | none |
| `lists.s4_top.rows` (derived) | only if the dose fallback fires: the kept count in `s4_doses_record.json` | write_add_edit | add_edit of the list s4_top (the 1B writer refuses it) |

Filling a pin: edit `pins_78b.json`; run `python -I -B scripts/scale78b/make_scorer_settings_78b.py` (it rewrites the
18 settings files and `PINS-78B.json` and prints the new `PINS_FILE_SHA256`); set that literal in `scorers_78b.py`;
run `tests/scorers`; commit `pins_78b.json`, `settings/*.json`, `PINS-78B.json` and `scorers_78b.py` by explicit path
(KD8). The derived files change only where the pin reaches (the test `test_the_two_families_differ_only_where_they_should`
lists the per-family paths).

## 6. Concerns and limits (for the lead)

1. **Two kind names (ruled: PP3).** `rep_pass` is REQ-3's representation pass (`representation_pass.py`; L1's and S3's
   features; about 1 h at 1B, `DIAG_ESTIMATE_S`; R: `stage1_rules.py:87`, `job_runner_stage1.py:24-30`): this layer's
   `rep_pass` kind. `a1_pass` is A1's attributes pass on the a0-1101 retrain's q and e1 states (the engine's attributes
   job, the kit's `a1_rescore` form; RP:43's 6-11 h; the 16.5 h cap at most); this layer serves its consumer,
   `score_edit a1`. Each has its own E cap; both need S_78 and the anchor file. `rules_78b.py` (S78_KINDS, E_KINDS) and
   Part 2 use these names; at HEAD 953f520 `rules_78b.py` still calls A1's pass `rep_pass` (R: `:136`), so the kit round
   renames.
2. **Every wrapper kind runs on engine X (ruled: PP4; verify-E D2).** Stated after the table in section 2 and in
   `pins_78b.json` `shared.engine_rule_78b` (copied into every settings file's `family_78b.engine_rule`). A scorer pod
   packed with engine Y would refuse at `load_settings` after its bootstrap; a Mac kind refuses once the checkout's
   engine identity is not X. A Y run needs re-derived settings (a recorded step; none exists).
3. **The classifier runs under S_78, and the kit's key check must let it through (ruled: PP4; verify-E D3).** The map
   and the 1B kit run `score_classifier.py --recipe S_78` (R: `job_runner_stage1.py:450-456`); `score_classifier__F.json`
   pins `recipe_sha256` = S_78_F. `rules_78b.py check_keys` accepts S_78 only for `S78_KINDS` (R: `:325-337`), which hold
   `retrain` and `rep_pass` at HEAD 953f520 (R: `:136`); every other E kind must use an allow-list recipe (main or G).
   So the kit round adds `classifier` to `S78_KINDS` (or records the classifier job's key recipe as main while its
   command line passes S_78). `rules_78b.py` is tracked; not changed here.
4. **Two untuned-answers calls per pod (ruled: PP2; verify-E D1).** Section 2 and 3. For the kit round: the S3 call's
   outputs are `<job>/untuned/` (the stage-1 path of `s3_orig.pool.json`; the `s3_orig_pin` form applies to them), the
   S4 call's `<job>/untuned-s4/` (with `doses/`); in the fallback case the S4 call's 1B record says `complete` false,
   has no `s4.json` and no W1-06 `s4` entry, while `wrapper_78b_record.json` says `exit_code` 0 with
   `doses.fallback_fired` true; the pod's E cap covers both calls (C3).
5. The `kept_after_the_48th` label and the fallback's missing W1-06 rows (section 3) are what the unchanged 1B code
   gives at keep 192; a 1B edit is not allowed, so they are documented, not fixed.
6. The wrapper's exit code in the fallback case is 0 with `fallback_fired` true in `s4_doses_record.json` and
   `wrapper_78b_record.json`, while the 1B record says `complete` false (its exit 3); fewer than 48 kept gives exit 3 in
   both records (`wrapper_78b_record.json` `exit_code` equals the process exit code; tested). The 7-8B kit's runner reads
   the wrapper record (the stage-1 kit's J6 completeness check reads the 1B record; R: `stage1_rules.py:679`). A
   refusal in the doses step is printed as `REFUSED after the 1B pass: the 1B outputs are written in <out>; the doses
   were not written (...)`, exit 2, with no wrapper record (verify-E C4).
4. Parity is of the plumbing: the wrapper runs the 1B script's own `main()`, so the outputs are the 1B script's by
   construction; the tests show byte equality with the 1B functions on the 1B fixtures (the wall-clock fields are the
   stated exception, as in the 1B determinism tests). The untuned-answers parity through `main()` ran on the engine's
   tiny model, whose answers are all capped at the fixture's 5 new tokens (both routes keep 0, exit 3, same bytes);
   the keep path is covered by the API test with the 1B test's generator. CUDA paths are untested, as in the 1B scripts.
5. The anchor job for Llama-3.1-8B encodes the 1B list's 64 harmful (prompt, unsafe response) pairs with Llama's
   tokenizer; the pinned script stops if one does not encode under 3072 tokens (R: `make_anchor_answers.py:117-121`).
   Low risk (I: the 1B pairs encoded under OLMo's tokenizer with the same limit), but a stop would need a reviewed list.
6. `build_s_pool__F.json` carries the 1B `expected_evaluation_forms` (11,954); for the Llama manifest it is unverified
   (I). It matters only if Part 2 rebuilds the S-pool per family.
7. The 7-8B kit's bundle must carry `scripts/scale78b/scorers_78b.py` and `scripts/scale78b/settings/` to the pod and
   pin them (the stage-1 kit's `STAGE1_PINS` form; R: `stage1_rules.py:585-598`), beside `scripts/stage1/`.

## 7. Hashes (M: `shasum -a 256`, 5 Nov 2026, 18:31 UTC, after fix round 3, in the track E worktree at HEAD 953f520)

`scorers_78b.py` 11ebe5be4260ee6e143f4478004f55a97133a0e0b34243d431e6ea9d2d7623ce; `make_scorer_settings_78b.py`
607606d62cddd795b946d1df59ec255f87570c2a91882b34cf3edd76ce012a5c; `settings/pins_78b.json`
aef5b78b2ee6913a4fa9568a816b657e5763340c8d269332bee19917a1fc10b2; `settings/PINS-78B.json`
8b9d8146d24910b15a81469bd206eba27d911a07bfe38bca04b39b1740fc71d9 (the literal `PINS_FILE_SHA256`; it lists each
settings file's SHA-256). The round-3 values (before the fix) were 2d4b7fac…, 6d37770a…, cd3c0850…, cba2f0b2… (build-E).
The 1B scripts' hashes are `scorers_78b.py` STAGE1_CODE; the 1B settings files' are `make_scorer_settings_78b.py`
BASE_SHA256; neither changed. Any later edit of `scorers_78b.py` changes its hash, not the settings.

Tests: `PYTHONDONTWRITEBYTECODE=1 <main venv python> -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/scorers`
(93 passed in 21.5 s; M, 5 Nov 2026, fix round 3); the whole `scripts/scale78b/tests` folder: 158 passed, 2 skipped
(track C's scipy tests; M). `make_scorer_settings_78b.py --check`: 19 of 19 files equal their regeneration (M).
