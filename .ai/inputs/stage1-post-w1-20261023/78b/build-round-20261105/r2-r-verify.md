# R2 Track R: adversarial verification (the 7-8B reference settings, Llama's recipe G at 5e-5, Track O's follow-up)

Written 2026-11-08, 22:29-22:33 UTC (`date -u` 22:29:44 and 22:33:04; work started 21:41:25). Status: **done**. Target: WS = `B/ws-r`
(detached at `bfda225`; MAIN's HEAD is `bfda225` too, M). I edited nothing in WS or MAIN (M: `git status --short` in WS
lists the same 47 entries before and after; no `__pycache__` was written). My files: this report and
`R/r2-r-verify-scratch/`. Tags: M measured (command or scratch file named), R read (path:line in WS), E estimate, I
inference. No pod, network, install, download, agent or message.

**Procedural slip (stated, not hidden):** early on I printed two 1B settings prose fields in full (`prefix.status` of
`scripts/stage1_s1/settings/eval_adapter.json`, and `adapter.acceptance_rule` / `key_rule` of `safe_lora.json`). They are
citations and naming rules, not prompt, answer or sealed text. After that I printed keys, sizes, hashes and token counts only.

## Verdict: DEFECTS

The core holds: no settings or script **path** label is false; the 1B files are byte for byte; parity on the 1B
fixtures; suite 610 passed, 57 skipped under the sandbox; 52 + 103 mutants killed. The defects are one moderate guard gap
(a Safe LoRA point that Part 2 does not carry can run through the wrapper) and five minor ones, two of them false
*values* in records (a stale registry record in 24 files; "K = 39" written into every 7-8B V/V' record).

| id | sev | file:line (WS) | defect | failure scenario | fix |
|---|---|---|---|---|---|
| RV-1 | moderate | `scripts/scale78b/refs_78b.py:106-108` (`SL_FLAGS["transform"]` takes `--point` with no value check); `make_refs_settings_78b.py:76-78`, `:308-310` (conditional K = 24) | The wrapper runs `safe_lora transform --point conditional` (K = 24). Part 2 §3.2 carries K = 78 only (P3 below). The 7-8B kit's `POINT_KINDS` lists `conditional` for `safe_lora` (R: `runkit/stage1-78b/stage1_rules.py:447`). The 1B runner refused only `k12`, not `conditional` (R: `runkit/stage1-olmo/setup/job_runner_stage1.py:557-558`). | A planner or a hand command naming `conditional` makes and evaluates a reference that is not pre-registered, and the wrapper exits 0 (M: probe P3, exit 0, the record holds the point `conditional`). | `refs_78b.py` refuses `--point` other than `default` and `certify` (exit 2, "not run at 7-8B: P2 §3.2 names K = 78 only"). Give the placeholder a status that says so. A null K is impossible (P3). A test and a mutant. |
| RV-2 | minor | `make_refs_settings_78b.py:170-175`, `:237-343` (`labels_sha256` copied from the 1B file); test `tests/refs/test_refs_78b_settings.py:149` holds it equal to the 1B value | All 24 derived B10 and B11 files record `labels_sha256` = `6d1415bd139c…` (the 1B file's). This field is "the record of the registry it was written on" (R: `scripts/stage1/s1common.py:26`). The files were written on registry `260389f3fbfd…` (M: `shasum` of `scripts/stage1/labels.json`; `s1.labels_sha256()`). Track O's files and the scorer maker record the current registry (M; R: `make_scorer_settings_78b.py:184`). | A false record value in every reference settings file. An audit that reads it dates the files to the 1B registry. No code reads it beyond its form, and it is outside the certified sections (R: `eval_adapter.py:149-150`). | `doc["labels_sha256"] = s1.labels_sha256()` in both derivations (the scorer maker's form). Change the test to hold that value. |
| RV-3 | minor | the 1B prose the maker keeps: `v_diagnostic.measure` (all 12 B11 files), `transform.points.certify.status`, B10 `certification.gate`; `untuned_unit.role` (`make_refs_settings_78b.py:257-260`) | `safe_lora.py vcheck` copies `v_diagnostic.measure` into its record (R: `safe_lora.py:817-820`). In every derived B11 file that text names "K = 39" and not "K = 78", while the default point is K = 78 (M: probe VD, 12 of 12 files). The certification report copies `certification.gate` (R: `eval_adapter.py:1573`), and the certify point's status goes into the B11 record (R: `safe_lora.py:673`). Both name 1B's "Gate A". The θ0 role text says "the lambda = 0 point's optional certification reference", which no 7-8B command can use (P4). | Each 7-8B V/V' record says it tested K = 39, while it tested the 78-matrix set. The records name a 1B stage. | Rewrite `v_diagnostic.measure`, the certify status, `certification.gate` and the θ0 role for 7-8B in the maker, as was done for the default and conditional statuses. Add a test that no derived text field that reaches an output names "K = 39" or "Gate A". The builder's Concern 1 left these unread. A keys-and-counts scan is enough to find them. |
| RV-4 | minor | `refs_78b.py:343-361` (`_set`, `with_placeholders`) | If the index lists a wait field that is absent from its file, `check` raises `KeyError`. It gives a traceback, not exit 2 with one JSON line. The docstring promises exit 2 for any refusal (R: `refs_78b.py:48-51`). This is the case Track O fixed in W2-3 (R: `oext_78b.py:549-550`; mutant `R2-w-absent-field`). | A stale or hand-edited index crashes the $0 check (M: probe ABS, `KeyError`). | `_set` refuses (`Refused`) when a parent or the key is absent. Add a test and a mutant. |
| RV-5 | minor | `make_refs_settings_78b.py:421-458` (`main` writes, never removes); P9 in R/r2-r.md §9 | P9 says the 3-seed fallback is "one pins edit and a maker run". In place, the maker writes the 3-seed files and leaves the 18 files of seeds 1105-1107. Then the committed-state consistency test fails (M: probe FB, 18 files left, `consistency` raises). | The documented fallback step leaves stale indexes the kit could still pin, and a red suite. | The maker removes (or refuses while present) `REFS-78B__*`, `eval_adapter__*__S` and `safe_lora__*__S` files of seeds outside the set. Add an in-place test. |
| RV-6 | minor | `refs_78b.py:109-110`, `:165`, `:221`, `:255-264`, `:305`, `:386` | 8 of my 12 extra refs mutants **survive** the builder's suite (M: `mut-xrefs2.json`, baseline 67 passed, 1 skipped). The surviving branches: compare's and evaluate's `--reference` rule, run's `--seed` rule, the B10-manifest-vs-index check, the index kind and version check, `check`'s binding check, the digit check on `--seed`, and the except branch. My 7 targeted tests kill 7 of them (M: `mut-xrefs3.json`). `RV-x-except-any` survives. I judge it equivalent, because the 1B mains catch their own refusals (I). Most of these branches repeat a refusal the 1B code makes later. `check`'s binding check and the `--seed` digit check do not. | A later edit removes one of these refusals with every test green. Without its binding check, the $0 Mac check misses a B10 file whose Safe LoRA pin is off the index. | Add `test_zz_rv_targeted.py`'s 7 tests (T1-T7, in scratch) and the 7 killed mutants to the refs spec. |

Not defects, but the lead should know (§P4, §P2): the builder's P4 gives the wrong cause for `compare --against
untuned`. P2's reading needs one correction for Llama at seed 1103.

## Check 1. No label lie, parity, the 1B files, the self-hash, the globals

- **1B files byte for byte.** M: `git diff --stat bfda225 -- scripts/stage1 scripts/stage1_s1 runkit` is empty. The six run
  modules hash to `CODE` (`refs_78b.py:81-88`) and equal MAIN's (`eval_adapter.py` `ae953129…`, `safe_lora.py`
  `5f6b7822…`; M `shasum`). The 1B settings equal `BASE` (`make_refs_settings_78b.py:80-85`; the test passes).
- **Path labels.** Every path a derived file or record names is a file the run loads. `oext.settings.path` is the
  family's `oext_eval__F.json`, loaded through the patched `oe.load_pinned_settings`. `external_transforms.safe_lora.settings.path` is
  read by `_pinned_file` (R: `eval_adapter.py:1032`, `:1066`). The provenance names `eval_adapter.py` /
  `safe_lora.py`, the files that run (R: `s1common.py:566`). The builder's test finds no 1B settings hash, path or
  `eval_adapter__` label in any output (M: suite). Unit `unit` texts are validated as text only and never written
  (R: `eval_adapter.py:302`; grep). The false **values** are RV-2 and RV-3.
- **Self-hash (`eval_adapter.py:1579-1590`).** It hashes the unchanged file with the settings literal zeroed, so it names
  the 1B bytes (M: identical SHA-256). The wrapper patches four globals for the call: `load_pinned_settings` (a partial of
  the original), `SETTINGS_PATH`, `SETTINGS_SHA256` and `OEXT_SETTINGS_PATH`, plus oext_eval's loader and path and W1-18's
  two globals (R: `refs_78b.py:290-297`, `:314-316`). The first three are the settings seam that the rule excludes by
  design. `OEXT_SETTINGS_PATH` is a path literal that the rule does not zero. It is bound by B10's own `oext.settings` pin,
  which is outside the certified sections at 1B too (R: `eval_adapter.py:149-150`). So a 7-8B certification certifies the
  1B code plus the settings seam that runs. **Limit (I):** neither the certification report nor job.json names
  `refs_78b.py`. A wrapper change between a seed's certification and its reference pods is caught only by the kit pin
  `REFS_78B[F][S]` (`code_pins`, `refs_78b.py:135-140`), not by `read_certification`.
- **Globals.** `patched` restores in `finally` (R: `oext_78b.py:396-406`). The builder's tests cover a run, a wrapper
  refusal, a 1B exit and argparse's `SystemExit`, for both scripts (M: suite). Every 1B call site loads with no argument
  (R: `eval_adapter.py:1868`, `:1880`; `safe_lora.py:884`), so the partials always receive the family file.
- **Parity.** The parity tests pass (M: suite). I read the comparison. job.json and the evaluation files must be equal
  byte for byte. "parsed" drops only wall-clock-like keys (R: `tests/oext/oext78_fixtures.py:197-210`), and "hashes" maps
  only the hashes of completion markers (`tests/refs/refs_fixtures.py:30-48`). I found no undeclared difference. Limit:
  the fixture B10 documents are `b10_fixtures`' single-seed form, not the derived 7-8B files. The derived files are
  checked by the validators and the consistency test, not run end to end.

## Check 2. Settings against Part 2 §3, DES F1, F2, GXB O2 (R: P2 §3.1-§3.2, DES:28-35)

- **B10 (`eval_adapter__F__S`).** Against the 1B file, only these differ (M: `diffkeys.py`, Llama 1105): the recipe
  (MAIN_F `74758af1…` / `18cc31d7…`, its training identity = RK KIT's), the manifest (`c52a50af…` / `9ed61826…`), the
  reference units {1101, S}, the untuned unit (θ0 = RK KIT `untuned`: `651f7f6d…` / `632fa4bd…`), certification seed S,
  the curve, the scale rule text, the prefix status text, the Safe LoRA pin, the O-ext pin and branch, and `requirement`.
  `expected_sampled_answers` stays 600 = 200 × 3 (M: consistency test). The prefix (text SHA-256 `0fcc6beb…`,
  separator, apply_to, guard_sees, length_rule) is the 1B one. That makes SP a user-turn prefix on both families, as in
  P2 §3.2. The length rule's 1536 / 3072 equal both 7-8B recipes' `max_prompt_tokens` / `max_train_tokens` (M).
  λ allowed {1, 0.9, 0.75, 0.5, 0}; planned {0.9, 0.75, 0.5}; curve {1, 0.9, 0.75, 0.5, 0}. Fallback: planned
  {0.75, 0.5}, curve {1, 0.75, 0.5, 0}, seeds 1102-1104 (M: tests). Nit: under the fallback, `allowed` still has 0.9,
  so a 0.9 point passes B10 there (`make_refs_settings_78b.py:75`, `:264`).
- **B11 (`safe_lora__F__S`).** 7 modules, 32 blocks, 224 matrices, rank 64, alpha 128, parameters 159,907,840 /
  167,772,160 (M: diff). 32 × the per-block rank-64 sums equals both counts (M: arithmetic; the shapes are I). K = 78 =
  224 × 39/112, certify 0. The aligned model is KIT's instruct model at its revision. The base repository is KIT's, with
  its revision, dtypes and files null and waiting on HUB_READ (M: pins and index). `accepted` holds seed S only.
- **Per-seed certification (P1): accept.** The frozen code forces it. `read_certification` takes only the settings' own
  certification seed (R: `eval_adapter.py:1637-1639`). The in-run gate needs seed = certification seed (`:1731`), and
  `certified_settings_sha256` includes that seed's pin (`:1593-1600`). So "one certification per reference seed" (GXB O2)
  needs one B10 file per seed. Each file pins only 1101 and S, so a seed's fill reaches its own index only (R-5's rule;
  M: the cascade tests). Forms per (F, S) give 12 kit pins.
- **Seed 1101's role in every file: right.** The untuned unit must be the init unit of a pinned reference seed
  (R: `eval_adapter.py:314-315`), so 1101 must be pinned. It is never the certification seed. No command can use it as a
  run seed (R: `refs_78b.py:74`, `:149-150`, `:248-264`), and only `check --reference 1101=…` reads it. Its pin is outside
  the certified sections, so its fill voids no certification. Cost: its e1 fingerprint wait blocks every B10 file of the
  family until the lead's read (builder P2). Note (I): P1 §2.1 already carries 16-hex 1101 prefixes (M there, P78:82),
  which the 1B validator accepts (`HEX_PREFIX` 16-64, R: `eval_adapter.py:113`). The maker demands 64 hex
  (`make_refs_settings_78b.py:203-204`). Whether a 16-hex prefix from the frozen P1 is enough is the lead's choice.
- **Which a0 unit each seed's certification pins:** see §P2.

## Check 3 (P3). The conditional Safe LoRA point

Part 2 §3.2 carries one Safe LoRA point: "K = 78 of 224 adapted matrices" (R: P2:531; §3.1's adopted set, P2:518). §3.1 counts "Safe LoRA 6", one
point × 6 seeds (P2:521). DES F2 says "Safe LoRA at K = 78 of 224 matrices" (DES:33). "conditional", "K = 24" and
"K = 12" occur in none of P2, AM1, DES or SCOUT (M: grep). PR4 §5.4 adopted K = 39 only (PR4:487). The 1B "conditional"
K = 12 ran "only if the user adds it" (R: `safe_lora.py:18-19`). So **K = 24 is a placeholder, not a pre-registered
value.** It cannot be null: the unchanged B11 validator needs `transform.points` to be exactly {default, conditional,
certify}, each with an integer K (R: `safe_lora.py:276-287`; `_int` refuses None, `:151-154`). So the refusal belongs in
the wrapper (RV-1). Also, B11's `check` always reports the conditional point (`CHECK_POINTS`, R: `safe_lora.py:102`,
`:804`). Whatever K the placeholder holds appears as a report-only row in every 7-8B check record. K = 0 would make that
row map nothing, as certify's does, which is closest to "null". The value is the lead's choice.

## Check 4 (P4, decisive). Llama's θ0 under MAIN_F

**Facts (M).** θ0's recipe `c5462c77…` and MAIN_F `74758af1…` differ only in `name`, `purpose` and `train.lr` (1e-4 vs
5e-5), in both the raw and the loaded configs. Their training identities differ: `f69cc0aef6c9…` vs `5b4451e1487f…`.
`training_identity` hashes `model` and `train` (R: `config.py:647-649`). Their generation and guard blocks are equal
(`5ddced7a…`, `a7f0755b…`), which is T-O4's result (R: `zero-checks-20261108/t-o4-llama-theta0-recipe-check.md`).

**`check --untuned`** refuses at `eval_adapter.py:1898-1900` → `read_untuned` (`:451-469`) → `_check_identity` (`:407-413`).
That check compares the settings' `regeneration.compare_identity` = [manifest_sha256, training_identity] (unchanged from
1B; R: diff) with MAIN_F's pins. The message is "the untuned unit: its identity differs from the settings in
['training_identity']". M: probe P4b builds a fixture init unit under a recipe that differs only in `train.lr`. The 1B
`read_untuned` refuses it, and the wrapper's `check --untuned` exits 2. The same unit under its own recipe passes (exit 0).
I: θ0's COMPLETE.json records its recipe's training identity. I did not open it. On OLMo, θ0 was made under MAIN_F
(`18cc31d7`, P1 §2.1), so the command passes there (I).

**`compare --against untuned`** refuses on **both** families, before identity matters. That differs from the builder's P4,
which names only Llama's identity.
1. The wrapper: `compare` is in `REFERENCED`, so `--reference` must hash to seed S's a0 pin (R: `refs_78b.py:255-264`).
   θ0's COMPLETE.json never does. M: probe P4a, exit 2, "seed 1102's pinned a0 unit is …".
2. The 1B code, if reached: `against == "untuned"` needs a scale-0 unit (`:1477-1479`), then `read_untuned` (Llama
   refuses on identity), then `reference["seed"] != job["seed"]` → "its sampling streams differ" (`:1481-1482`). θ0 is
   seed 1101's init unit, and every 7-8B reference unit is at S ∈ 1102-1107. So it refuses on both families (R).
3. Nothing planned needs it. P2 §3.1 counts λ 18 = 3 points × 6 seeds (0.9, 0.75, 0.5). The 7-8B kit has no `scale:0`
   (R: `runkit/stage1-78b/stage1_rules.py:447-448`). At 1B, `scale:0` ran inside `b10_certify` at the certification seed
   1101, which was also the untuned seed (R: `runkit/stage1-olmo/stage1_rules.py:616`; 1B settings: certification seed
   1101 = untuned seed). At 7-8B the certification seeds are 1102-1107, so that pairing no longer exists.

**Can a wrapper accept θ0 honestly?** `compare --against untuned`: **no.** The seed rule and the identity check are in the
1B code. Patching `read_untuned` or `_check_identity` would run code that the certification's `script_code_sha256` does not
describe, which is a false label. `check --untuned`: **only as the wrapper's own check, labelled as such**, never as the 1B
line `"pins": "ok"`. Options, undecided:
- (a) $0, no build: state a limit. At 7-8B the curve's λ = 0 end is θ0's own measurement (P1 §2.1's untuned unit), and
  the 1B optional λ = 0-vs-θ0 comparison is not run. Llama's θ0 is used under T-O4's condition. Reword the θ0 role text
  (RV-3).
- (b) $0 pods, about 1-2 builder h (E): add a θ0 check to `refs_78b.py check`. It checks the pinned COMPLETE.json, run-one,
  target init, a0/dev/1101/development, F's manifest, and a training identity equal to a pinned θ0 recipe (c5462c77)
  whose generation and guard blocks hash to MAIN_F's (T-O4). The output says `checked_by: refs_78b.py (T-O4)`. Add tests
  and mutants.
- (c) Pods: a λ = 0 unit at seed 1101 per family. That needs a regenerated a0-1101, a seed-1101 certification (a 1101 B10
  file) and scale 0. On Llama it also needs a new θ0 init unit under MAIN_F. E: about 2 extra evaluation-only pods per
  family plus one init unit on Llama, each under the ref_eval cap of 5.0 h / 5.25 h (P2 §3.2). It also makes 1101 a
  reference seed for one point, against P2 §3.1's "no reference cell at 1101".

## Check 5 (P5). The engine's recipe count test

- **Where:** `experiments/safety_selection/tests/test_ss_family_codec.py:150-165`. The count is
  `59 + 9 + gate_b_s.exists()` (:165). M: with the new config, 1 failed and 94 passed (`test_ss_family_codec.py`,
  `test_ss_family_recipes.py`). `test_every_earlier_recipe_keeps_its_loss_and_schedule` already exempts names with
  `-g5e5-` (R: `test_ss_family_recipes.py:193-197`), so the new name passes it.
- **Engine X's identity:** the rule is every `experiments/safety_selection/*.py` at the top level only (the glob does not
  recurse, so tests are excluded), plus 7 `minimal_safety` modules (R: `common.py:31-36`). I re-computed it without
  importing the engine (`R/r2-r-verify-scratch/engine_identity.py`): 29 files, **`472fc7f6d619bdee…`**, on WS (with the
  new config present) and on MAIN. That equals RK `ENGINE_X` (R: `rules_78b.py:111`). No test file and no config is in
  the identity.
- **Pins:** the test file's SHA-256 `8e635f76…` occurs only in round 7b's scratch hash listings (`p2-r7b-*-scratch/pool-*.tsv`),
  which are measurement records, not pins (M: grep over WS and MAIN `.ai`, `research`). No tracked file under
  `experiments/` changed (M: `git status`).
- **So:** adding the config changes no identity and no pinned hash. The count needs +1 in the lead's committed addition
  (KD8), as the builder says.

## Check 6. Llama's recipe-G config at 5e-5

M: `diff` of the raw files shows `name`, `purpose` and `lr` only, with key order and layout kept. The loaded recipes
differ in `name`, `purpose` and `train.lr` only, so the loader derives no other field. Against MAIN_F, the new config
differs exactly in the five G fields (loss, loss_weighting, lr_schedule, schedule_until, warmup_steps). OLMo's G config
differs from OLMo's main config in the same five, so the new config is "the 1B B → G change at the family's main LR".
Config SHA-256 is `81dd70687b72…`, file `3298dd92…`. Generation `5ddced7af22b968f…` and guard `a7f0755b795f0ac4…` equal
the 1B O-ext pins (`oext_unit.json` `recipes`). The builder's 4 tests pass. Passed.

## Check 7. Track O's follow-up (W2-1, W2-2, W2-3)

- **W2-1:** under 128, or full with a record, `form()` adds `{record_path: record_sha256}` (R: `make_oext_settings_78b.py:439-440`).
  `consistency()` and the cascade test hold the entry, and the X and Y forms pass RK's `oext_form_problem` (M: suite).
- **W2-2:** H3, H3b, C4 and I1 are present. The 3 RV2 mutants are in the spec and killed (M: shards).
- **W2-3:** a placeholder copy replaces message matching (R: `oext_78b.py:509-588`). The stale and absent-field cases
  refuse, a null that no wait names exits 2, and the F2 case exits 2 (M: suite). Two Track O tests changed their inputs to
  the stricter rule. The masking test now lists THETA0_JOB next to UNIT_JOB, because under the old rule UNIT_JOB's
  substring also masked θ0's refusal. I judge this a correct tightening, not a weakening.
- **No regression:** Track O's folder passes 145 cases (inside the 610). `make_oext_settings_78b.py --check` gives 18 files
  equal (M). Its spec gives 103 of 103 killed (M). My 3 extra Track O mutants are all killed (M: `mut-xoext2.json`).
  `c6a9a946…` (the old `oext_78b.py`) is pinned nowhere under `scripts`, `runkit` or `experiments` (M: grep). Passed.

## Check 8. Tests and mutants (all under `sandbox-exec -p "$SB"`)

- Suite: `scripts/scale78b/tests` in WS gives **610 passed, 57 skipped** in 77 s, exit 0 (M, 21:52-21:53 UTC). This equals
  the builder's count.
- Refs spec (`0b700da8…`), 2 shards of 26: **26 + 26 killed**, 0 survived, 0 invalid, 0 ERROR lines. Each shard's
  baseline was 67 passed, 1 skipped, and each shard took 5-6 min, run 3 in parallel (M: `mut-refs-{1,2}.json`).
- Track O spec (`a2679365…`), 7 shards (15 × 6 + 13): **103 killed**, 0 survived, 0 invalid, 0 ERROR lines. Each shard's
  baseline was 144 passed, 1 skipped, and each shard took 3-5 min (M: `mut-oext-{1..7}.json`).
- Mine: 12 refs and 3 Track O mutants (`rv_extra_spec_*.json`). 4 + 3 killed and 8 survived, so the refs spec has gaps
  (RV-6). My targeted tests kill 7 of the 8 (`mut-xrefs3.json`). One run of the Track O extras was invalid, because my
  first mirror lacked `.ai`, so the baseline failed and nothing ran. I re-ran it with `.ai` linked (`mut-xoext2.json`).
- Probes (`test_zz_rv_probes.py`, all pass on the builder's code): P4a, P4b, P3, LBL, VD, ABS, FB.

**The lead's full-run commands** (each about 20 min or less in one process; E from the shard times):
```
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'; PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
cd <WS> && sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests
sandbox-exec -p "$SB" $PY -B <WS>/scripts/scale78b/tests/refs/run_mutants_refs_78b.py <WS> <NEW_SCRATCH> <OUT>.json ALL --timeout 600
sandbox-exec -p "$SB" $PY -B <WS>/scripts/scale78b/tests/oext/run_mutants_oext_78b.py <WS> <NEW_SCRATCH> <OUT>.json ALL --timeout 600
```

## P2. Which a0 unit each reference seed's certification must pin

The 1B `b10_certify` passes `--seed S --reference gate_a_complete:S --gate-reference-eval gate_a_eval:S` (R:
`runkit/stage1-olmo/setup/job_runner_stage1.py:467-479`). B10 then regenerates the a0 adapter of seed S and compares it
by fingerprint with that seed's pinned reference (R: `eval_adapter.py:416-448`, `:472`, `:550`). It evaluates in certify mode and checks
each of the 600 sampled answers' gate labels against the reference unit's own `eval/e1/guard_samples.jsonl`, by the hash
its COMPLETE.json lists (`:1449-1576`). So the reference must be **the a0 unit trained at seed S under MAIN_F on F's
manifest and the settings' engine, with its own e1 evaluation**. At 1B those were the Gate A units at 1101-1103 and the
stage-1 a0 arm units at 1104-1107, whatever block made them (R: the 1B B11 `acceptance_rule`). The lead's reading ("the
a0 unit AT that seed") is right in principle, with one correction:

| seed | OLMo-2-7B | Llama-3.1-8B |
|---|---|---|
| 1102 | reused side unit (RK KIT `a0_units[1102]`, `43e8412d…`) | reused side unit (RK KIT `a0_units[1102]`, `b0c99f7b…`) |
| 1103 | reused side unit (RK KIT `a0_units[1103]`, `4b5bd06d…`) | **block 0's (N's) a0-1103** (ruling 8; RK KIT `block0.runs`, R: `rules_78b.py:199`, `:256`), not a side unit |
| 1104 | block A's a0 | block A's a0 |
| 1105-1107 | block B's a0 | block B's a0 |

GXB O2's literal "that seed's block-B a0 unit" fits 1105-1107 only. Before each certification, the lead's hash-only fill
of `REF_UNIT_S` should be followed by `refs_78b.py eval_adapter … check --reference S=<COMPLETE.json>` on the Mac. That
runs `read_reference`'s checks for $0: run-one, e1, a0/dev/S/development, MAIN_F identity, and the prefixes. Not checked
here (I): whether the side units' markers carry role "development" and list `eval/e1/guard_samples.jsonl`. I opened no
unit. Also (I): if a family's block A or B runs on engine Y (P2 §2.1), the regeneration on engine X matches a Y-trained a0
only if ruling 10's equality holds at the fingerprint level. And each seed's reference pods must match that seed's
certification environment (R: `eval_adapter.py:1654-1668`), which K3's pod choice must respect.

## Open points for the lead (I decide none)

1. RV-1/P3: the conditional placeholder value (24 or 0) and the wrapper refusal.
2. P4: option (a), (b) or (c).
3. P2: the table above (Llama 1103 = N's unit). Then the three known side-unit paths and markers (OLMo 1102-1103, Llama 1102)
   can be prefilled from RK KIT as 1101's were.
4. Whether a 16-hex 1101 prefix from P1 §2.1 may fill `REF_UNIT_1101` (the 1B validator accepts it; the maker does not).
5. P5: +1 in the count test with the KD8 commit.

## Commands run (exit status)

Reads (cat, sed, grep, git show/diff/log, shasum): exit 0. The suite, exit 0. Both `--check` runs, exit 0. `refs_78b.py check`
× 12, exit 0 each (`check-*.json`). Engine recipe tests, exit 1 (the expected count failure). The 9 builder shards, exit 0
each. Extras: xrefs2 exit 1 (survivors), xrefs3 exit 0 (summary exit 0, 1 survivor), xoext2 exit 0; the first xoext run
exit 2 (invalid baseline, my mirror). Probe runs: exit 1 twice while I fixed my own probe code, then exit 0. Mirrors and
pytest temp folders deleted. JSON results, specs and probe files kept (`R/r2-r-verify-scratch/`, 492 KB).

## P4 follow-up (the lead's question on the O limit; written 2026-11-08, 22:39 UTC)

**Answer: Llama's θ0 unit (`c5462c77`) is not on the O path, so its training-identity mismatch does not reach the O
limit.** θ0's O over the 500-prompt set is made fresh by an `o_only` pod. That pod runs the untuned model (adapter
disabled) under MAIN_F's recipe. It reads no θ0 unit and no stored evaluation.

1. **How θ0's O is made at 7-8B.**
   - P2 §1.14 (R: P2:236): `o_only` is "the S1 package's O-ext unit pass on the family's untuned model": `oext_unit.py
     run --untuned --prepared P_F --recipe MAIN_F --oext-bank … --oext-record …`. P1 §14 item 3 says the same (R: P1:364).
     The side probes' untuned units were evaluated with the family-probe bank, not stage 1's O set, so `o_only` runs for
     both untuned models before block A.
   - The kit agrees. RUN78 builds `run --untuned --prepared p --recipe rec` for `o_only` (R: `runkit/stage1-78b/setup/job_runner_stage1.py:599-604`).
     `rec` is the family's main config (R: `:496-500`; `runkit/stage1-78b/stage1_rules.py:151`, "the family's MAIN config
     path"). The kit's O-ext script is Track O's wrapper, `unit` command (R: `rules_78b.py:1314`, `:1317`).
   - In `oext_unit.py`, `--untuned` means "theta0, the policy with its adapter disabled; the dev-100 answers are
     generated here" (R: `scripts/stage1_s1/oext_unit.py:19-20`). With `--untuned` no unit is checked (R: `:441-444`; the
     unit and source checks with their identity tests, `:330`, `:387`, run only for `--run`). The pass disables the adapter
     on the policy built from `--recipe` (R: `:614-619`).
   - DES E5, P2 §4.5 and AM1 add `o_only_with_regenerate` for N's units. They change nothing for θ0 (R: DES:25-27;
     P2:580-586; AM1 has no θ0 or `o_only` line, M: grep).
   - So θ0's O is a new MAIN_F untuned pass, not a stored evaluation. O(arm) and O(θ0) are then made under the same
     recipe, generation block and guard.

2. **Does Track O's route accept it?** Yes, for both families, and θ0's own recipe is refused.
   - R: `oext_unit.check_recipe` needs the `--recipe` config SHA-256 to be in `recipes.allowed`, and its generation and
     guard blocks to equal the pins (`oext_unit.py:293-303`). No training-identity test applies to `--untuned`.
   - Track O's `oext_unit__llama31-8b.json` allows MAIN `74758af1…` (G null, waiting on RECIPE_G).
     `oext_unit__olmo2-7b.json` allows MAIN `18cc31d7…` and G `01259f28…`. Both pin generation `5ddced7a…` and guard
     `a7f0755b…` (M).
   - The wrapper's `unit` command adds no unit or recipe test of its own (R: `oext_78b.py:422-443`).
   - **M on a fixture** (`R/r2-r-verify-scratch/test_zz_rv_theta0_o.py`, run in a scratch mirror under the sandbox,
     2 passed):
     - `unit run --untuned` with the allowed MAIN analog exits 0. Its job.json shows route `generated` and
       `unit_complete_sha256`, `source_complete_sha256` and `dev100_source` all null.
     - The same call with a recipe that differs only in `train.lr` (θ0's `c5462c77` case) exits 2: "is not one of the
       settings' allowed recipes".
   - The kit never passes θ0's recipe, so this refusal never fires on the planned route (I). OLMo's θ0 was made under
     MAIN_F, and its `o_only` is the same command (I). Neither family reads its θ0 unit there.
   - **Where the stored `c5462c77` unit is read:**
     - (i) W1-18's branch check. Its answers are W1-18 inputs (P2 §4.2). The 1B W1-18 module checks units with
       `identity: {}` and refuses only `refused_recipes` (R: `overrefusal_checks.py:416-418`;
       `limits_common.py:136-171`). Track O's Llama W1-18 settings refuse only `ceffe0ef…` (the 1B Gate B S) and judge
       with MAIN_F's recipe (M). So W1-18 accepts θ0, and the recorded T-O4 condition is the basis.
     - (ii) B10's `untuned_unit` pin, used by `check --untuned` and `compare --against untuned` only (§P4: no planned
       run).
     - (iii) θ0's job pins (THETA0_JOB; `W1_18_78B`'s side units).

3. **Options.** Nothing refuses Llama's θ0 on the O path, so no O-path option is needed. The frozen text already implies
   the route: θ0's O comes from the untuned model under MAIN_F (P2 §1.14's command; P1 §14 item 3's `o_only` job). P1
   §2.1's `c5462c77` row (R: P1:86) is the side probe's θ0 record. It gives θ0's U and the unit W1-18 reads under T-O4; it
   is not the O source.
   - For the B10 λ = 0 comparison only, the earlier options stand: (a) $0, state the limit; (b) $0 pods, about 1-2 builder
     h (E), a θ0 check of the wrapper's own, labelled as such, under T-O4; (c) pods, a λ = 0 unit at 1101 plus a new Llama
     θ0 under MAIN_F.
   - The frozen text implies (a). P2 §3.1 counts no λ = 0 run, and P1 names `c5462c77` as θ0 without requiring a MAIN_F θ0
     unit.
   - One residual for the lead (I): "the policy under MAIN_F with its adapter disabled" equals θ0 under `c5462c77`,
     because the two configs differ only in `name`, `purpose` and `train.lr` (M: §Check 4). The `model`, `generation` and
     `guard` blocks are equal, so the untuned policy is the same model. Only θ0's stored U (P1 §2.1, 32/600) came from the
     `c5462c77` unit itself.
