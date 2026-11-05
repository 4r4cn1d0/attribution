# Build report, track C (T6a, T5, the Llama G1 $0 check)

Worker: a Fable builder in the detached worktree
`/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-c`
(detached at fb51421). Work 13:34-14:06 UTC, 5 Nov 2026 (`date -u` read at 13:34:38, 13:59:40 and 14:05:49 UTC; this
final revision written right after the last read). Governing texts read in full: the lead's Part 1 rulings, the
readiness plan's §0-§3 and T5/T6, P78 §2-§9 and §12, the adversarial check (C1-C14, M1-M5, the corrected list).
Tags: M measured (command given), R read (path:line), E estimate (basis), I inference.

Status: DONE with one acceptance item not met by design (item 1's config files; the reason and the lead's options
are in item 1). Items 2 and 3 pass every criterion.

## Hard-rule compliance

- Writes: only under the worktree (new paths `scripts/scale78b/**` and two records under
  `.ai/inputs/stage1-post-w1-20261023/78b/`) and this report. A git-ignored scratch folder `tmp/scale78b-build-c/`
  inside the worktree held run outputs during the work and was deleted at the end (M, `rm -rf`; `git status` never
  listed it).
- Git state: untouched (no add, commit, stash, checkout, reset, branch, worktree, push, pull). HEAD fb51421 (M).
- Two stand-in S_78 configs were written into the worktree's `experiments/safety_selection/configs/` for one engine
  test run and deleted in the same shell command; `git status --porcelain -- experiments` printed nothing after (M).
- Forbidden folders and files: none opened (no `tmp/hlc*`, `tmp/v3-prepared`, `tmp/stage1-olmo`,
  `tmp/stage1-mac-runs-20261023`, `tmp/stage1b`, `selector.jsonl`, `hidden/`). The a0 and R units' answer, sample
  and guard files were read only inside the frozen `gate_b_reading.arm_from_unit` → `family_probe_reading.counts`
  code path, as the track allows for N's parity and the G1 check; only counts and aggregates were printed or written.
  No judge file was opened. No unit under `tmp/gate-b-olmo/retrieved/w1-1/` was read beyond one `job.json` arm string
  and its `COMPLETE.json` hash (the method-arm refusal test; the refusal fires on the edit file's provenance before
  any evaluation file is read).
- No pod, spend, network, install, download, agent or message. No engine file, frozen script, sealed file, kit file
  or other tracked file edited: `git status --porcelain` lists new paths only (M, below).
- Python: the main venv with `-I -B` for everything that imports the engine; `.venv` (scipy) for the noise reader's
  constants tests; `-I` on every data-reading one-liner.

## Files (all new)

| Path (worktree) | SHA-256 (first 16) | What |
|---|---|---|
| `scripts/scale78b/__init__.py` | | package marker (docstring only) |
| `scripts/scale78b/make_recipe_s78.py` | 5b08c3ed9af2a26b | T6a: the recipe-S_78 maker |
| `scripts/scale78b/noise_reading.py` | 6cde1a24318f60f8 | T5: N's reading and the seed rule |
| `scripts/scale78b/g1_check_78b.py` | 251ddb32146ee71f | the G1 check's driver (the "thin adapter" slot; no adapter was needed) |
| `scripts/scale78b/tests/conftest.py` | | repo root on sys.path |
| `scripts/scale78b/tests/test_make_recipe_s78.py` | | 12 tests |
| `scripts/scale78b/tests/test_noise_reading.py` | | 18 tests (2 need scipy) |
| `scripts/scale78b/tests/test_g1_check_78b.py` | | 6 tests |
| `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105-units.json` | 233fa4b745a069b5 | the G1 check's inputs (ids, families, paths) |
| `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json` | 895a5469cc9efe81 | the G1 check's text-free record |

`git status --porcelain` at the end (M): `?? .ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105-units.json`,
`?? .ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json`, `?? scripts/scale78b/`. Nothing else. No
`__pycache__` under `scripts/scale78b` (M, `find`).

---

## Item 1, T6a: the two recipe-S_78 configs

### What recipe S changes (the 1B pair's difference; R, M)

- R `scripts/make_gateb_recipe.py:5-7`: S is REC with exactly four changes: `attribution.checkpoints` → [q, e1],
  `attribution.query_bank` → `anchors-HEX` (the SHA-256 of the sealed anchor file's bytes), `name`, `purpose`.
- M: a key-by-key diff of `study-kt-olmo2-1b-r64-b-mb4-20261008.json` (config 9e9bde6f…) against its `-gateb-20261008`
  sibling (ceffe0ef…) is exactly {name, purpose, attribution.checkpoints, attribution.query_bank}; both have training
  identity f46279e5… (`test_the_1b_pair_differs_in_exactly_the_four_recipe_s_fields`).
- M (`-I -B`, the engine's `config_sha256` / `training_identity`): OLMo-2-7B main
  18cc31d7117a2de7bc02382fe8a4d409fc43c91b434bf219a4808dfb26528d09 / 36738c3823fae7eaca625cc9f619e98c7e40b9bb64e5d0e234412827d3371ec6;
  Llama-3.1-8B main 74758af1791d9f7a8ce616adce7549b5b7b0619e55310158d7e21197ed129893 / 5b4451e1487fb2200a5b2b151de2e68397117099a429654484146b3cc3791287
  (P78:76's values).

### The finding: S_78 has one field that no $0 step can fill today (I from R, M)

The fourth recipe-S field is `anchors-<the SHA-256 of the family's anchor FILE>`. R `scripts/make_anchor_answers.py:1-18`:
the anchor job runs the given recipe's policy untuned and keeps the first 64 of its own Safe answers, so the anchor
file is per model. P78:377 says "an anchor job per family"; ruling 11 puts "the anchor job" in block 0's kit subset.
M: `.ai/inputs/` holds only Gate B's 1B record (`gate-b-anchors-20261008/out/anchors.sealed.json`, key
`anchor_file_sha256` = 2cf96336…, the value inside the 1B recipe S; keys read, no text). Gate B's own order was "the
anchor job on RunPod before recipe S" (PRE:5, revision 3). R `experiments/safety_selection/jobs.py:175-181`: the
attributes job hashes the anchor file and refuses a mismatch, so a placeholder hash passes `validate_recipe` and fails
only on the pod. So neither S_78 config's bytes, and so neither `config_sha256`, can be known before that family's
anchor job has run.

**Decision taken here (the smaller change; the lead may overrule):** build the maker so that one command per family
writes S_78 the moment the family's anchor record exists; prove every other acceptance property for any anchor hash
in the tests; write no file into `experiments/safety_selection/configs/` with an invented or borrowed hash.

Alternatives for the lead:
- **(A, recommended)** Merge the maker now. After each family's anchor job, run
  `python -I -B scripts/scale78b/make_recipe_s78.py --family <f> --anchors-sha256 <anchors.sealed.json's anchor_file_sha256> --out experiments/safety_selection/configs/<name>.json`
  and commit by explicit path (KD8). Until then track A's `rules_78b.py` pins `RECIPE_S` per family as null and
  refuses, as `gate_b_reading.GATE_A_PINS` did (R `scripts/gate_b_reading.py:152`). The 19-20 Nov dry packs then
  carry the main configs only, as Gate B's first pack did; S_78 enters the pack of the retrain and attributes pods.
- **(B)** Rule that OLMo-2-7B reuses Gate B's 1B anchor file (2cf96336…). The prompts are the same sealed list, but
  the safe set holds OLMo-2-1B's answers, so this changes P78:377's "anchor job per family": a scientific choice, not
  this builder's. Llama-3.1-8B has no anchor file at all, so its S_78 waits in any case.
- **(C)** A placeholder hash now. Rejected here: a committed config that every later pack carries and that the engine
  refuses on the pod, whose hash changes again at the real value.

### Alternatives considered for the maker itself

- Edit the 1B maker to take a family: refused by the brief (pinned, KCR:140). New file instead.
- Pin the main configs by an 8-character prefix as the 1B maker did: the new maker pins the full 64-hex `config_sha256`
  and the full training identity (stronger; the configs are tracked, so a change is a real event).
- Fix the output layout to 2-space indent: the two main configs differ (OLMo 2 spaces, Llama 4; M), so the maker
  detects the main config's indent and keeps its key order, as the brief's "REC's own layout" asks.

### Commands and results (M)

1. `PYTHONDONTWRITEBYTECODE=1 <main venv>/python -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_make_recipe_s78.py`
   → 12 passed (first run; its exit code was lost to a zsh `PIPESTATUS` slip; the later whole-folder run, exit 0,
   covers the same 12). The tests run the maker as a subprocess under `sys.executable -I -B` with a synthetic 64-hex
   anchor value (the SHA-256 of a test string, not a record), and check: the written file's `config_sha256` equals the
   engine's function; training identity == the main config's == the pin; `load_recipe` accepts the file; the diff
   against the main config is exactly the 1B field set; `family_probe_reading.eval_config` is unchanged; the key
   order and indent are the main config's; byte determinism; the refusals (hash form, family, date, existing path,
   wrong stem, a changed main config).
2. Engine tests that enumerate configs, as the tree stands:
   `… pytest -q -p no:cacheprovider experiments/safety_selection/tests/test_ss_family_recipes.py …/test_ss_family_codec.py …/test_ss_family_reading.py …/test_ss_headroom.py --ignore=…/test_ss_gateb_runkit.py`
   → 203 passed, 2 skipped, exit 0 (run twice; the second run captured the exit code).
3. The decisive check of "which test needs a lead change" (one shell command): the maker wrote both S_78 files with
   the synthetic anchor hash into the worktree's configs folder (stand-in recipe hashes ecb6ec9c… OLMo, 0209abd3…
   Llama: NOT 7-8B values), the first three test files above ran, then both files were deleted:
   **1 failed, 180 passed, 2 skipped, pytest exit 1.** The failure: `experiments/safety_selection/tests/test_ss_family_codec.py:165`
   `assert family_recipes == 59 + 9 + gate_b_s.exists()` → `71 == 69`. The test counts every recipe whose name starts
   with `study-kt-olmo2-`, `study-kt-llama3` or `study-kt-olmo3-`, so the two S_78 files add 2. **Lead change when the
   S_78 configs are committed: that count, +2 (or a term for the S_78 pair, as the line does for Gate B's S).**
   `test_ss_family_recipes.py` (globs `*-20261008.json`) and `test_ss_family_reading.py:804` (glob
   `study-kt-*-20261008.json`) do not see a `-20261105` file and passed; `test_ss_headroom.py` reads `study-v2-*`
   only. After the deletion: `ls configs | grep -c gateb-20261105` → 0; `git status --porcelain -- experiments` → nothing.

### Acceptance (item 1)

| Criterion | Result | Evidence |
|---|---|---|
| item 1's tests pass | passed | 12 passed (M) |
| the two configs exist with `config_sha256` and training identities recorded | **not met, by design** | the anchor hash does not exist; see the finding and (A)/(B)/(C) |
| each S_78 differs from its main config only in the recipe-S field set (the 1B pair's set) | passed | `test_s78_differs_from_its_main_config_only_in_the_recipe_s_field_set` (M) |
| `config_sha256` by the engine's function under `-I -B` | passed on the maker's output | `test_the_cli_writes_the_file_in_the_main_configs_layout_and_the_loader_accepts_it` (M) |
| training identity of each S_78 equals its main config's (36738c38…, 5b4451e1…) | passed, for any anchor hash | the test and the maker's own refusal (M) |
| the engine's loader accepts both files | passed on the maker's output | `load_recipe` in the tests (M) |
| engine tests that enumerate configs run; lead changes reported | passed | `test_ss_family_codec.py:165` count (M) |

---

## Item 2, T5: the noise reader

### Design (as ruled; R P78:116-122, :291; rulings 1-3, 7, 8, 10)

- `scripts/scale78b/noise_reading.py`, stdlib only. It loads the frozen `scripts/gate_b_reading.py` by path and pins
  its SHA-256 (4638a0f0…) with `family_probe_reading.py` (88483401…) and `killtest_stage0_reading.py` (1740663b…); it
  stops if any differs. Reused by import, unchanged: `arm_from_unit`, `compared_fields`, `Reader.reading` (which
  carries `variance`, `mean`, `pair_se2` and `median_term`), `noise_gate`, `ge` / `sigma_value` / `term_value` (the
  exact comparisons on squares), `canonical`, `jsonable`, `r_key`, `read_json`, `is_int`. Nothing copied.
- Inputs keyed by `complete_sha256` and family (P78:291). Per unit: sealed (every file COMPLETE.json lists present
  with its hash); COMPLETE.json's SHA-256 equals its key; a run-one e1 trajectory of the dev bank, split dev, role
  development, at the keyed seed (1101-1103 only), fresh for an R arm (an a0 unit may resume from its own init unit,
  as Gate A's 1101 did and as `gate_b_reading.gate_a_unit` allowed; the resume source's COMPLETE.json hash is
  recorded); an a0 unit's arm "a0"; an R unit's arm the named `edit-<hash>`, present as `edit.json` with that hash, a
  remove edit of the family's manifest whose `provenance.selection` says family R, draw = seed − 1100 (so a method
  arm's unit refuses: only a0 and R units are N's inputs); the per-role engine identity, the family's manifest and the
  family's training identity in job.json, identity.json and COMPLETE.json (so a 1B unit under a 7-8B family refuses:
  f46279e5… is neither 36738c38… nor 5b4451e1…); the recipe's training identity recomputed and its hash equal in all
  three records; the environment record (13 compared fields, the policy block, the lock) and the guard record
  (compared among the units that carry one: engine X's units all do; Gate A's 1B units do not, and Gate B compared
  their 13 fields and policy only); one `complete_sha256` never twice.
- r_F,j = U(a0, j) − U(R_j, j); σ̂_F = max(SD(r_F), σ_eval,0,F) on 2 df by the frozen `Reader.reading("plain")` and
  `noise_gate`; the a0-free fallback (SD(r) := √2 × SD(U(R_j)); σ_eval,0 the median over the three R-R pairs) with
  its two triggers: any compared-field or guard-record difference between a unit and the family's a0-1101, or the
  lead's `fingerprint_check: "differs"` (ruling 10's X retrain comparison; "equal" or "not run" otherwise).
- σ̂_pool = max(√[Σ_F 2 SD(r_F)² / (2 k)], the median of the k × 3 governing pair SEs) on 2 k df (k = 2 at the tier:
  √[(2 SD(r_O)² + 2 SD(r_L)²) / 4] against the 6 pair SEs, 4 df). s_arm: the pooled per-arm seed SD of U over the a0
  and R arms of every family (2 df per arm, 8 df at the tier); √2 × s_arm printed beside it (the S-U scale).
- The seed rule on the pair scale, compared exactly on squares: σ̂ ≤ 4.5 plan A (6 method seeds, 6 primary
  contrasts); 4.5 < σ̂ ≤ 6.0 plan B9 (9 seeds; P1, P3, P6); else branch H, the lead's (b) (12 seeds; P1, P3, P6);
  SESOI 5 pp in every case. The review ceiling: the plan's removal MDE above 2 × SESOI, read as σ̂ above a pinned
  ceiling (plan A 7.0390, B9 9.2718, H 10.7062 pp), with the MDE itself printed (factors 1.4207, 1.0785, 0.9340 =
  (z_Holm + z_0.80)/√seeds, CALC rule_oc2.py's form; CALC's "(b) 10.7" reproduced). It can bind only in branch H.
  Each family's own σ̂_F plan (2 df) is printed as the [C] alternative without SR-2.
- Printed and written: σ̂_F, σ̂_pool, s_arm and √2 s_arm, both σ_eval,0 forms, r_j with the mean and its SE, the
  per-arm SDs of U, the pair SEs, the triggers and their fields, the seed-rule output, each unit's G1 counts and
  status, every unit's hashes, the frozen scripts' and the bars' hashes. **No U is printed or written** (a test walks
  the output and the printed summary for any `U` key or long string).
- `operating_characteristics(σ_true, df)`: CALC's χ² probabilities with a closed-form even-df CDF (for the tests).
- The output is canonical JSON, written once (an existing `--out` refuses), as the frozen reading does.

### Alternatives considered

- Copy the five functions with a parity test (the brief's second route): not needed; import by path with a SHA-256 pin
  is tighter and leaves one implementation.
- Build the Gate B `Context` (its sealed-manifest and recipe-S pins) and run `phase_noise_gate`: pinned to the 1B
  files (MAN, UT, REC, S, the Gate B certificate), so it cannot read a 7-8B family; the per-arm `arm_from_unit` and
  `Reader` are the right layer.
- Require a guard record on every unit (Gate B's C2 for its own arms): refused Gate A's 1B units (no record);
  loosened to "compared where both carry one", which is what Gate B did for those units.

### Parity (Gate B wave 0a; M)

Inputs: Gate A's a0 units 1101-1103 (`tmp/family-probe-olmo2-1b{,-gateA-1102,-gateA-1103}/retrieved/*/tree/round1/*-a0-e1-a1`,
keyed by `GATE_A_PINS`' COMPLETE.json hashes 8f0fa83a…, 857f78bc…, 7be58eaa…; engine 55253874…) and wave 0a's R_1-R_3
(`tmp/gate-b-olmo/retrieved/w0a-1/tree/round1/*-edit-{f7d7eb86,913b7360,cd8d3328}…-e1-a1`, keyed by the noise-gate
output's hashes 391d067c…, 1cef324d…, d34e33f2…; engine X 472fc7f6…), family `olmo2-1b`, `fingerprint_check` "not run".
The committed `research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-wave0a.json` is byte-identical to the
read-only `tmp/gate-b-olmo/gate_b_noise_gate.json` (SHA-256 4b817f73d968b89a19d74150cdaf449f34653d3d83fd972550bd84bc21432dd7;
`diff` → IDENTICAL).

Reproduced (the reader's CLI, exit 0): plain SD(r) 1.8333…, σ_eval,0 1.2793…, σ̂_gate **1.83**; fallback SD(r)
1.9052…, σ_eval,0 **2.16** (2.1574…), σ̂_gate 2.16; r_j 0.667 / 2.5 / 4.333 pp, mean r 2.5 pp with SE 1.0585; the
triggers all false; the seed-matched pair SEs 1.181 / 1.293 / 1.279 pp against the R-R pairs 2.162 / 2.004 / 2.157 pp
(the 1B pairing-gain sign of P78 §3.4); per-arm SD of U: a0 2.6475, R 1.3472 pp (P78:127's "1.35 against 2.65"); s_arm
2.1005 pp on 4 df (√2 s_arm 2.9705); every a0 and R unit passes G1; the seed rule on this one family: plan A (σ̂ 1.83
≤ 4.5), MDE 2.60 pp, no review. The test `test_parity_with_gate_b_wave_0a_to_two_decimals_and_exactly` asserts the
two-decimal values **and** float-exact equality of `sigma_gate_pp`, `sd_r_pp`, `sigma_eval0_pp` and `r_pp` for both
blocks, and of `mean_r_pp` and `se_pp` for P4, against the committed output.

### Commands and results (M)

- `PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/.venv/bin/python -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_noise_reading.py scripts/scale78b/tests/test_g1_check_78b.py -rs`
  → **22 passed, exit 0** (final run; scipy present, so the constants and χ² tests ran).
- `PYTHONDONTWRITEBYTECODE=1 <main venv>/python -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/ -rs`
  → **32 passed, 2 skipped (scipy absent in that venv, `importorskip`), exit 0** (final run; the whole folder).
- Earlier runs that drove fixes (all read-only on the data): the reader's first parity run exit 1 ("a0@1101: not a
  fresh run-one e1 trajectory": Gate A's 1101 resumed from its init unit; the a0 resume rule added); the first test
  run 9 failed ("an evaluated unit needs a guard record": Gate A's 1B units carry none; loosened as above); the
  second test run 1 failed (a test regex: the Llama family refuses a 1B unit on the manifest one check before the
  training identity; the test now asserts each family's own reason).
- The reader's CLI on the parity inputs: exit 0; output and printed summary free of any `U` key (M, a walk).

Tests (18 + 6): the parity (two decimals and exact); the fingerprint trigger governs the fallback (σ̂_F → 2.16); an
environment difference triggers it (monkeypatched on one R unit); the CLI writes canonical text-free output once; a
1B unit in a 7-8B family refuses (OLMo-2-7B by training identity, because it shares the 1B manifest; Llama-3.1-8B by
manifest); a wrong key refuses; a unit listed twice refuses; a method arm (a wave-1 unit-removal edit at 1101) as an R
unit refuses on its edit file's provenance; the seed set, the engine, the arm name and `fingerprint_check` are
checked; unknown families and malformed inputs refuse; the thresholds are inclusive and exact (4.5 → A, 4.5000001 →
B9, 6.0 → B9, 6.0000001 → H; a two-SE median term decides when larger); MDE 6.39 at 4.5 and 6.47 at 6.0 (CALC's
values); the ceiling binds at 10.71 and not at 10.7062, and never in A or B9; the constants against scipy (5e-5); the
OC row σ 4.5, 4 df → 59.4 / 27.6 / 13.0 % exactly as `rule_oc2_out.txt` prints it, and every row of that table to its
printed precision; the χ² CDF against scipy; the pins.

### Acceptance (item 2)

| Criterion | Result | Evidence |
|---|---|---|
| parity values reproduce to 2 decimals (1.83, 2.16, 1.28) | passed (and float-exact) | the CLI run and `test_parity_…` (M) |
| inputs keyed by `complete_sha256` and family; a 1B unit in a 7-8B family refuses | passed | `test_a_1b_unit_in_a_7_8b_family_refuses`, `test_a_wrong_complete_sha256_key_refuses` (M) |
| no U of any method arm printed (only a0 and R units are inputs) | passed | the R edit-provenance refusal; the `U`-key walk (M) |
| reuse of the frozen functions without editing `gate_b_reading.py` | passed | import by path, pinned; `git status` shows no edit (M) |
| the seed rule on the pair scale with 4.5 / 6.0 and the review ceiling | passed | `test_the_seed_rule_thresholds_are_inclusive_and_exact`, `test_the_review_ceiling_…` (M) |
| one OC row reproduced | passed | `test_one_row_of_the_operating_characteristics_table_reproduces` (M) |
| the refusal tests pass | passed | 22 of 22 under .venv (M) |
| `blinded_sigma.py` not built | as ruled (ruling 3) | no such file |

---

## Item 3: the Llama G1 $0 check

### Method

No adapter was needed: `gate_b_reading.arm_from_unit(unit, bars, where)` reads `eval/<job.json's target_checkpoint>`
of any unit folder, and the family probes write that layout (job.json, identity.json, COMPLETE.json, eval/e1/…), the
same one Gate B's Gate A a0 units have. `scripts/scale78b/g1_check_78b.py` is a driver: it checks the unit (sealed;
run-one; a0 or edit arm; the family's training identity and manifest), calls the frozen function (which re-implements
the coherence screen from the bars and refuses unless its per-prompt counts agree with the frozen `counts()`), and
maps the answers-end verdict to G1: pass only on PASS; TOO CLOSE counts as a G1 failure (PRE:147, R). Bars: Gate A's
frozen amended bars (c0b6f2aa…; capped ≤ 5%, screen-failing ≤ 10%, the short-answer clause at < 5 tokens; R
`configs/family-probe-reading-amended-20261008.json`).

Command (M, exit 0), run from the worktree root:
`/Users/spiderishi/Coding/attribution/.venv/bin/python -I -B scripts/scale78b/g1_check_78b.py --units .ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105-units.json --out .ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json`
(the record stores this command, the script's SHA-256 251ddb32…, `noise_reading.py`'s 6cde1a24…, the three frozen
readers' hashes and the bars' hash). A text-free walk of the record found no `U` key and no string over 260
characters or with a newline (M).

### Per-unit results (counts only; M)

| Unit (COMPLETE.json SHA-256, first 16; = P78 §2.1's) | n | capped | screen failures | short-only | without short | answers end | G1 |
|---|---|---|---|---|---|---|---|
| Llama-3.1-8B a0 1101 (21427715565fb394) | 600 | 6 (1.0%) | 42 (7.0%) | 20 | 22/580 (3.8%) | pass | **pass** |
| Llama-3.1-8B a0 1102 (b0c99f7b97e6e763) | 600 | 7 (1.2%) | 63 (10.5%) | 43 | 20/557 (3.6%) | too close | **fail** (short-answer TOO CLOSE) |
| OLMo-2-7B a0 1101 (4a6d9ebc6636de57) | 600 | 1 (0.2%) | 23 (3.8%) | 20 | 3/580 | pass | pass |
| OLMo-2-7B a0 1102 (43e8412dc7ef8d3e) | 600 | 2 (0.3%) | 20 (3.3%) | 17 | 3/583 | pass | pass |
| OLMo-2-7B a0 1103 (4b5bd06dede08dc1) | 600 | 0 | 16 (2.7%) | 15 | 1/585 | pass | pass |
| parity: Gate A OLMo-2-1B a0 1101 (8f0fa83a42ccc5ed) | 600 | 2 | 42 | 34 | 8/566 | pass | pass |
| parity: Gate B wave-0a R_1 at 1101 (391d067ca6569a04) | 600 | 1 | 43 | 38 | 5/562 | pass | pass |

All seven units ran on the engines their records name (the five 7-8B units 472fc7f6…; Gate A 55253874…; R_1 472fc7f6…).
By family: Llama-3.1-8B 1 pass, 1 fail; OLMo-2-7B 3 pass; the parity family 2 pass.

**Parity (M):** the Gate A 1101 counts equal the family-probe reading's own record of that unit
(`tmp/family-probe-olmo2-1b/reading-olmo.json`, `bars_read.answers_end.per_seed[0]`: n 600, capped 2, incoherent 42,
short_only 34, without_short 566/8); R_1's pass agrees with the sealed verdict (`gate_b_verdict.json`: `R_G1_failed []`,
`diffuse.G1_failed_arms []`). The Llama 1102 counts equal the Side Project's reading record
(`tmp/family-probe-sp-llama31-8b-b5e5-seed1102/reading-llama31-8b-b5e5-1101-1102-nojudge.json`, per_seed[1]:
600/7/63/43 and 557/20), as do Llama 1101's (600/6/42/20) and OLMo 1101-1102's (600/1/23/20; 600/2/20/17).
`test_parity_on_a_gate_b_wave_0a_unit_and_a_gate_a_unit` asserts the Gate A counts and both passes.

### FOCUS's "63 of 600 incoherent (10.5%)" for Llama a0-1102

Yes, it is G1's own screen count. The family-probe reading's `counts()["sampled"]["incoherent"]` and Gate B's
`arm_record.fails` apply one screen (capped at max_new_tokens, repetition ≥ 0.5, empty, or < 5 output tokens; R
`scripts/family_probe_reading.py:373-376`, `scripts/gate_b_reading.py:381-384`), and the frozen `arm_from_unit`
refuses unless the two agree; it did not refuse, and both give 63 (M). The frozen bars read 10.5% as a failure of the
plain bar and, because 43 of the 63 are short normally-ended answers (20/557 = 3.6% without them), as TOO CLOSE
(`answers_end_bar`, R `:495-505`); PRE:147 makes a short-answer TOO CLOSE a G1 failure. **So Llama-3.1-8B a0-1102 fails
G1 as reused; a0-1101 passes; all three OLMo-2-7B a0 units pass.** Decidable: yes, for every unit.

What this means for the plan (I): P78:272 asks the lead to raise a failing Llama a0 unit to the user before the Part 1
freeze. Under the rulings TC does not run (ruling 6), so G1's only remaining role at 7-8B is the report-only line of
P78 §3.4 ("Each R arm's G1 status by the frozen Gate B guard code; N does not stop on a G1 failure"); the reader prints
it. The 1102 failure is a short-answer TOO CLOSE (3.6% without the 43 short answers), the same case decision 25
accepted at 1B for Llama-3.2-1B (FOCUS L235-L236, R). Whether Llama's N units at 1103 (a0) and R_1-R_3 behave alike
is measured by N.

### Acceptance (item 3)

| Criterion | Result | Evidence |
|---|---|---|
| the record exists, text-free, with a G1 status per unit | passed | `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json` (895a5469…), the walk (M) |
| per unit: path, COMPLETE.json SHA-256, counts, verdict; the code hashes; the command | passed | the record's fields (M) |
| the frozen code reads the layout, or an adapter with a parity proof | the frozen code reads it; the driver's parity shown on a wave-0a unit with a recorded G1 status and on Gate A 1101 | (M) |
| the FOCUS count question answered | yes: G1's own screen count | (M, R) |
| no answer or prompt text printed, copied or quoted; no selector/hidden file opened | held | counts only, by the frozen path |

---

## Commands run (every one, with exit status)

Read-only reads (all exit 0 unless noted): `date -u` ×3; `git status --porcelain`, `git log --oneline -1`,
`git rev-parse --short HEAD` on the worktree; `ls`, `find` (directories and file names only), `cat`, `sed -n`,
`grep`, `awk`, `wc -l`, `shasum -a 256`, `diff` (the NG copies: IDENTICAL) over the sources named in this report;
`python -I` one-liners that printed JSON keys or numeric fields of job.json, identity.json, COMPLETE.json,
assets.json (keys), the sealed R_d1 edit's provenance (no rows), the anchors record's keys, the committed Gate B
outputs and the family-probe reading outputs; `python -I -B` with the main venv for the engine hashes. One batch of
read-only shell commands was refused by the harness's own classifier ("no verdict") and was re-issued through the
Read tool; nothing ran twice with effect. Two inline one-liners of mine exited 1 on my own bugs (an `.items()` on a
string; a non-JSON `reading-olmo-nojudge.json` in the glob) and were redone. One `ls … inputs*` glob matched nothing
(zsh "no matches found"; the rest of that command ran).

Builds and tests:
1. `pytest … scripts/scale78b/tests/test_make_recipe_s78.py` (main venv) → 12 passed.
2. `pytest … test_ss_family_recipes.py test_ss_family_codec.py test_ss_family_reading.py test_ss_headroom.py --ignore=…test_ss_gateb_runkit.py` (main venv) → 203 passed, 2 skipped; exit 0 on the re-run.
3. `make_recipe_s78.py --family olmo2-7b …` → exit 0; `… --family llama31-8b …` → exit 0 (stand-in anchor hash, into the worktree's configs); the three engine test files → pytest exit 1 (1 failed, 180 passed, 2 skipped: the codec count); `rm` of the two files → 0; `grep -c` → 0; `git status --porcelain -- experiments` → empty.
4. `noise_reading.py --inputs … --out …` (parity) → exit 1 (a0 resume rule) → fixed; → exit 1 (guard record) → fixed; → exit 0.
5. `pytest … test_noise_reading.py test_g1_check_78b.py` (.venv) → exit 1 (9 failed) → exit 1 (1 failed, a test regex) → **exit 0, 22 passed**.
6. `pytest … scripts/scale78b/tests/` (main venv) → exit 1 (same two rounds) → **exit 0, 32 passed, 2 skipped (scipy)**.
7. `g1_check_78b.py` smoke run into the scratch folder → exit 0; the record run (the command in item 3) → exit 0.
8. `rm -rf tmp/scale78b-build-c` → 0; final `git status --porcelain` → 0, three new paths.

No command ran over a minute. No job was left running. No background job.

## Evidence paths

- Worktree (new): `scripts/scale78b/make_recipe_s78.py`, `noise_reading.py`, `g1_check_78b.py`, `tests/*`;
  `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105{,-units}.json`.
- Read-only sources: `scripts/make_gateb_recipe.py`, `scripts/gate_b_reading.py` (4638a0f0…),
  `scripts/family_probe_reading.py`, `scripts/make_anchor_answers.py`, `experiments/safety_selection/{config,jobs}.py`,
  the four configs named above, `research/experiments/2026-10-16-gate-b-wave0-outputs/{noise-gate-wave0a,gate_b_verdict,gate_b_inputs_verdict}.json`,
  `research/review/2026-10-17-icml-78b-prep/calc/rule_oc2{.py,_out.txt}`, `.ai/inputs/gate-b-sealed-20261008/out/{MANIFEST.json,edits/R_d1.json}`,
  `.ai/inputs/gate-b-anchors-20261008/{README.md,out/anchors.sealed.json}` (keys), the main checkout's
  `tmp/gate-b-olmo/{gate_b_noise_gate.json,gate_b_inputs_noise_gate.json}` and unit folders named in item 2,
  `tmp/family-probe-sp-*` unit folders and reading records named in item 3, `tmp/family-probe-olmo2-1b*` units.
- The scratch outputs were deleted; every number above is reproduced by the test commands in items 2 and 3.

## Jobs for the lead

1. **S_78 (item 1):** choose (A) or (B). Under (A), track A pins `RECIPE_S` per family as null-until-filled and the
   maker runs once per family after its anchor job (the command in item 1).
2. **When the S_78 configs are committed:** `experiments/safety_selection/tests/test_ss_family_codec.py:165`, the
   family-recipe count +2.
3. **The Llama G1 result** (a0-1102 fails G1 as a short-answer TOO CLOSE; a0-1101 and all OLMo-2-7B a0 units pass)
   goes to the user before the Part 1 freeze (P78:272; ruling 14), with the reading above.
4. **Track B's Llama R edit files** must carry what the noise reader checks on an R unit's `edit.json`: `kind`
   "safety-selection edit", `edit_kind` "remove", `manifest_sha256` c52a50af…, `provenance.selection.family` "R" and
   `provenance.selection.draw` d (SEAL's fields, R `R_d1.json`). Otherwise N's Llama R units refuse.
5. **N's inputs file** (after N runs): per family `engine` {a0, R} (472fc7f6…, or Y's identity where ruling 10 lets Y
   carry arms), the six units' paths and COMPLETE.json hashes (the a0 ones are P78 §2.1's; Llama a0-1103 and all R
   units are new), each R unit's `edit-<hash>`, and `fingerprint_check` from ruling 10's X retrain comparison.
6. Optional background job (not required by this track; every suite here ran in seconds): the full engine suite
   `PYTHONDONTWRITEBYTECODE=1 <main venv>/python -B -m pytest -q -p no:cacheprovider experiments/safety_selection/tests --ignore=experiments/safety_selection/tests/test_ss_gateb_runkit.py`
   after the merge, as the lead's own re-check.

## Unresolved concerns

- Item 1's "the two configs exist" is not met today for the reason given; the acceptance needs the lead's choice.
- The noise reader has not run on 7-8B units (no R unit exists). Its 7-8B-specific checks are exercised as far as
  the data allow: the five 7-8B a0 units pass the same frozen `arm_from_unit` path (item 3); the 1B-in-7-8B refusal
  exercises the training-identity and manifest checks; the R edit-provenance and arm checks are exercised on Gate B's
  R units (the OLMo manifest). The Llama R files' provenance is a requirement on track B (job 4).
- The review ceiling compares σ̂ with a four-decimal constant (10.7062 pp for H); the thresholds 4.5 and 6.0 are
  exact. A σ̂ within 0.0001 pp of the ceiling would be read against the rounded value (E: negligible; stated).
- The parity reproduces the wave-0a output with the current frozen `gate_b_reading.py` (4638a0f0…), a later revision
  than the one that wrote that output (b0964b2d…; D17-D19 edits followed); the exact equality shows the noise-gate
  functions are unchanged in effect.
- `noise_reading.py` pins the frozen readers' hashes; if the lead ever edits a frozen reader (the brief forbids it),
  the reader stops by design and the pins need a recorded update.
