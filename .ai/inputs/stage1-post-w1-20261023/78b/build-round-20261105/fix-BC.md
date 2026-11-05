# Fix report: tracks B and C (T3 the Llama sealed set; T5 the noise reader, T6a's maker, the G1 check)

Started 2026-11-05 14:47 UTC; finished 15:13 UTC (M: `date -u` read right before each time written). Fix-round worker
for GI X (Fable). Both worktrees detached at `fb51421` (M `git rev-parse HEAD`, unchanged):
ws-b `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-b`
ws-c `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-c`
My scratch: `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/fix-BC-scratch/`
(the mutation harness and its output, the parity record of the rebuild, the round-1 G1 record; 3.3 MB before the last
cleanup, M `du`). Tags: M measured (command given), R read (path:line), E estimate (basis), I inference. Short sentences.

## 0. Status: DONE

Every defect B-M1..B-M3 and C-D1..C-D5 is fixed, addendum A6 is tested, the three sets are rebuilt into empty `out/`,
ws-c is the one merged tree. B's and C's tests pass alone and together (M). The five named mutants N4, N5, N6, N15, N17
die on real test failures (M; three more mutants of my own die too). `git status --porcelain` in ws-c lists only new
files (M). ws-b is left as the rebuild's record (M). No git state changed anywhere. No pod, spend, network, install,
download, agent or message. Nothing written in the main checkout. No forbidden folder or text file opened; the prepared
sets' `train_rows.jsonl` were read only by the id-only views (BLD's `Inputs`, the wrapper's `PreparedView`,
`s1common.PreparedView`, `token_accounting.TokenView`) and copied by `cp` into ws-c/tmp; the unit folders were read only
by the frozen `gate_b_reading` code path; every print was a count, a hash or an aggregate.

One consequence beyond the listed defects: the G1 record embeds `noise_reading.py`'s SHA-256 (R
`g1_check_78b.py:135`), so after the noise-reader edits I regenerated it with round 1's exact command. Only that one
field differs; every count and verdict is unchanged (M, section 2.12). The round-1 record is kept in my scratch.

## 1. Files changed

ws-b (all untracked round-1 files; edited in place; `git status --porcelain` lists the same four `??` folders, M):
- `.ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py` (B-M3; now `227aed4f…`, was `5cd45926…`)
- `scripts/scale78b/build_r_draws_78b.py` (B-M3; now `5cd1036d…`, was `25dd7aca…`)
- `scripts/scale78b/build_h1_llama3.py` (B-M2, B-M3; now `504e9462…`, was `8b00a67b…`)
- `.ai/inputs/scale-78b-sealed-llama3-20261105/tests/test_build_sealed_llama3.py` (B-M1; +1 test)
- `scripts/scale78b/tests/test_build_r_draws_78b.py` (B-M1; +1 test); `scripts/scale78b/tests/test_build_h1_llama3.py` (B-M1; +1 test)
- the three `README.md` (the new hashes; a note on the rebuild)
- the three `out/` folders removed and rebuilt (24 + 1 Llama sealed files, 6 + 1 OLMo draw files, 1 + 1 H1 files)

ws-c (edited untracked round-1 files):
- `scripts/scale78b/noise_reading.py` (C-D2, C-D4, A6's record fields, `r_edit_matches`; now `94b679ff…`, was `6cde1a24…`)
- `scripts/scale78b/make_recipe_s78.py` (C-D3: `anchor_records`, `anchored_to`; CLI unchanged; now `fcf01955…`)
- `scripts/scale78b/tests/test_noise_reading.py` (C-D1, C-D2, C-D4, C-D5, A6, the edit-file test: 23 tests, was 17)
- `scripts/scale78b/tests/test_make_recipe_s78.py` (C-D3: one test removed, two added: 13 tests, was 12)
- `scripts/scale78b/__init__.py`, `scripts/scale78b/tests/conftest.py` (one each, serving both tracks)
- `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json` regenerated (now `8c3579e4…`, was `895a5469…`)

ws-c (copied from ws-b byte for byte, M `diff -r` / `cmp` IDENTICAL): `.ai/inputs/scale-78b-sealed-llama3-20261105/`,
`.ai/inputs/scale-78b-r-draws-olmo2-20261105/`, `.ai/inputs/scale-78b-length-rules-llama3-20261105/`,
`scripts/scale78b/build_r_draws_78b.py`, `build_h1_llama3.py`, `tests/test_build_r_draws_78b.py`, `tests/test_build_h1_llama3.py`.
ws-c/tmp (git-ignored, M `git check-ignore`): `tmp/kt-prepared/prepared-kt-dolly-{olmo2,llama3}/{manifest.json,
engine/train_rows.jsonl, engine/groups.json}` and `tmp/gate-b-sealed/build_sealed.py` only (what B's tests read;
no selector/, hidden/, banks/, auditor/ or query_rows.jsonl copied).

Not changed: any tracked file (M: `git status --porcelain` in both worktrees shows `??` entries only), any engine file,
frozen script, sealed file, `runkit/`, `g1_check_78b.py` (`251ddb32…` unchanged), the G1 units file (`233fa4b7…`
unchanged), the main checkout.

## 2. Per defect: what changed and the evidence

### 2.1 B-M1 (id-only stubs instead of `load_prepared`)
- Change: `test_d_…` uses `W.PreparedView(LLAMA, …).engine_stub()` and `W.PreparedView(OLMO, …).engine_stub()`;
  `test_the_engine_accepts_each_file_…` (r-draws) and `test_the_engine_accepts_llama_h1_…` (H1) use
  `s1common.PreparedView(...).engine_stub()` (R `scripts/stage1/s1common.py:376-377`: manifest hash, row ids, dev
  membership). No test imports `experiments.safety_selection.prepare` any more (M: `grep load_prepared` over the six
  test files finds none). The docstrings say so.
- Evidence: the three tests pass (M, run 9: 30 passed). The stubs hold exactly what `parse_edit` reads (R `edits.py`
  parse_edit; BLD's `EnginePrepared`, R `build_sealed.py:186-192`). Nothing hashed changed for this item.

### 2.2 B-M2 (the H1 script's write guard)
- Change: `build_h1_llama3.py` gets `SEAL_DIR_REL`, `ANCHORS_DIR_REL`, `STAGE1_DIR_REL`, `FORBIDDEN_DIRS` and a
  `guard_out(out, repo)` function (the inline stage-1-only check is gone). The forbidden set is SEAL
  (`.ai/inputs/gate-b-sealed-20261008`), the sealed anchor list (`.ai/inputs/gate-b-anchors-20261008`; verifier C and
  addendum A3 name it as a committed sealed input) and stage 1's records (`.ai/inputs/stage1-commitments-20261016`).
  The same tuple is in both wrappers.
- Evidence: `test_the_h1_script_never_writes_under_seal_the_anchor_list_or_stage1_from_any_repo` (M, passes). Before:
  the round-1 guard checked only the stage-1 folder (R round-1 `build_h1_llama3.py:105-108`; verify-B §6.2), so its
  SEAL assertion would not raise (I from R; the round-1 script no longer exists in ws-b, so no before-run was made).

### 2.3 B-M3 (`guard_out` resolves the forbidden folders from the script's own repository root)
- Change (both wrappers and the H1 script): `guard_out(out, repo=None)` builds the forbidden roots from `REPO` (the
  script's own checkout, `Path(__file__).resolve()` ancestors) first, then from `--repo` when it differs; any match
  refuses `refusing to write under <folder>`. The CLI still calls it before any read.
- Evidence: `test_a_non_default_repo_cannot_aim_the_output_into_this_checkouts_sealed_folders` in the sealed and the
  r-draws tests, and the H1 test above (M, pass): `guard_out(SEAL / "new", other_repo)` refuses; the other checkout's
  folders refuse; `main(["--repo", other, "--out", SEAL/"new"])` returns 2 with the message on stderr and writes
  nothing; the stage-1 folder likewise. Before: the round-1 guard resolved `(repo / forbidden)` only (R round-1
  `build_sealed_llama3.py:410-417`, `build_r_draws_78b.py:183-190`; verify-B §6.3), so with a non-default `--repo` the
  real SEAL path was not refused (I from R).

### 2.4 The rebuild (addendum A3's "empty out/ folders"; the folder placement kept)
- Done in ws-b: the three round-1 `out/` folders removed (M run 6), then the three CLIs with their defaults (M runs
  7, 8, 10; each exit 0). The 30 tests pass after the rebuild (M run 9); before it, exactly the 3 committed-`out/`
  tests failed on the stale round-1 files (M run 5: 3 failed, 27 passed).
- The parity test for stage 1's d = 6-10 holds byte for byte: `test_c_olmo_parity_reproduces_stage1_d6_to_d10` asserts
  `(parity / rel).read_bytes() == (RDRAWS / rel).read_bytes()` and `byte_identical is True` for d = 6..10 (M, in the 30);
  the kept `fix-BC-scratch/rebuild-parity/PARITY.json` records `byte_identical: True, stage1_wrapper_rederived: True`
  for all five and `byte_identical: True` for the 13 SEAL files (M). SEAL's R_d1-R_d3 reproduce as `f7d7eb86…`,
  `913b7360…`, `cd8d3328…` (M run 7's output: Gate B's wave-0a arms). BLD unchanged: `80cb8944…` both copies (M).
- New MANIFEST SHA-256 values (M `shasum -a 256`):
  - Llama sealed set `out/MANIFEST.json` **ba524373161b0c7cbc0fb4c79a71f6cf7b3e4c7a8d3d746915984b5b1db1a812** (round 1 76415c42…)
  - OLMo R_d11-R_d16 `out/MANIFEST.json` **189275c0137e1025fca95e5ca045fba16b7577cb7cb15032433aa5bfbae098f7** (round 1 da634837…)
  - Llama H1 `out/MANIFEST.json` **29347da2c82c98509d0ecc81d8543ebba4855e70b35f21d4e505aa4788fd29fb** (round 1 189cd139…);
    `out/edits/octile_0.json` 9204121a57d745b81fa00cfde51184e8be8d3c2fdb6a3814065976f76990ae5b (round 1 fdd35004…)
  - scripts: `build_sealed_llama3.py` 227aed4f2c55bc657d18eaf36c4ffddb211afb65204d0a6b2a5672ad22dcfe9c;
    `build_r_draws_78b.py` 5cd1036d73d8e57a0b61ab918a37f541fc84b99e845adc0efedad8eb0dacbf13;
    `build_h1_llama3.py` 504e94626a20433cd2ab773430994f3f161a2121d86ddd25c73286eb2a5fc6db
  - N's Llama R arms: R_d1 edit-091de345ce399a77ca6e0a60d3465853428aa9b93db00ef0e88b6d86c787f046; R_d2
    edit-59fc31df3ea35ebb44165f438190773621e2ecefffacd4aa0c03a7fe154e59c0; R_d3
    edit-c875e7302b14785c0f8fb317c752d8172a3073f4cd319ae37166faeb429740a5 (the rest are in the MANIFEST).
  - H1's remove list is unchanged (the same cut points 2-13 … 177-2064 and by-category counts; M run 8's output).

### 2.5 The Llama R edit files against the noise reader's check
- M (run 11, `-I -B`, keys and hashes only): all 16 Llama `R_d*.json` carry `kind` "safety-selection edit",
  `edit_kind` "remove", `manifest_sha256` c52a50af…, `provenance.selection.family` "R", `provenance.selection.draw` = d
  and `provenance.seed` = 1100 + d; the 6 OLMo d = 11-16 files likewise on 9ed61826…. Exactly the fields ws-c's
  `read_unit` checked (R round-1 `noise_reading.py:187-191`), now factored into `r_edit_matches` (section 2.11).

### 2.6 C-D1 (σ̂_pool, the pooled six-SE median, s_arm pinned; N4, N5, N6)
- Tests: `test_sigma_pool_the_pooled_median_and_s_arm_on_exact_inputs` (the verifier's synthetic k = 2 inputs: √P_pool
  = √10, median 3.5, σ̂_pool 3.5, s_arm √11.75 = 3.4278 on 8 df, df 4, plan A; the median-governed case 9.5 → H; the
  review case 11 → review, MDE 10.274; one family alone); and in the parity test on wave 0a: per-arm SDs 2.6475 /
  1.3472, s_arm = √[(SD_a0² + SD_R²)/2] = 2.1005 on 4 df, √2 s_arm 2.9705, σ̂_pool == σ̂_F, the pooled median ==
  σ_eval,0 = 1.279264, √P_pool == SD(r) (M).
- Mutants (M, `fix-BC-scratch/mutate_fix.py`, baseline 23 passed, exit 0): N4 KILLED (3 failed, assert), N5 KILLED
  (3 failed, assert), N6 KILLED (1 failed, the parity test, assert). Same command as the baseline; no errors.

### 2.7 C-D2 (one constant for the review comparison and the printed MDE; boundary test)
- Change: `review = not GB.ge(2 * SESOI_PP, ex(MDE_FACTOR[plan]), sigma)` (2 SESOI ≥ factor × σ̂, exact on squares);
  `CEILING_SIGMA_PP = {plan: Fraction(2 * SESOI_PP) / Fraction(factor)}` is derived, printed, never compared
  (7.0388 / 9.2721 / 10.7066 pp; round 1 pinned 7.0390 / 9.2718 / 10.7062 from the unrounded factors). The output's
  `rule` block gains `review_rule`.
- Test: `test_the_review_ceiling_is_the_mde_rule_itself_one_constant_at_the_boundary`: ceiling × factor == 2 SESOI
  exactly; at σ̂ = ceiling exactly no review and MDE = 10 (abs 1e-9); one part in 10⁷ above: review and MDE > 10; below:
  no review and MDE < 10; a two-radicand σ_eval term at the boundary; the verifier's band value 10.7064 now reads
  review False with MDE < 10 (both agree). Mutant "D2 review by the old rounded ceiling" KILLED (1 failed, assert).
- `test_the_constants_against_scipy` still holds (M, 28 passed under .venv): the derived ceilings are within 5e-4 of
  2 SESOI / k_scipy (H: 4.4e-4; E from the factor's four decimals).

### 2.8 C-D3 (the S_78 config test under route (A), addendum A1)
- Removed: `test_the_s78_configs_are_not_in_the_configs_folder_until_…` (it would fail the day the configs are committed).
- Added to the maker: `anchor_records(inputs_root)` (every committed `anchors.sealed.json` of kind "gate-c anchor bank
  record", complete: its `anchor_file_sha256` and `provenance.recipe_sha256`) and `anchored_to(config, family, records)`
  (the record the config's `anchors-<hash>` names, when that record's recipe is THIS family's main config). The CLI is
  unchanged (the lead's A1 command stays).
- Tests: `test_any_s78_config_in_the_configs_folder_is_anchored_to_a_committed_record_of_its_family`: for each tier
  family, every `<main stem>-gateb-*.json` present must differ from its main config in exactly the recipe-S field set,
  keep the training identity, and be anchored to a committed record of its family; the 1B record (anchor
  2cf96336…, recipe 9e9bde6f…) is read (M). Vacuous today (no S_78 present); holds under route (A).
  `test_the_anchor_link_refuses_a_placeholder_and_a_borrowed_1b_anchor_file`: a synthetic hash, the 1B anchor file for
  either 7-8B family, the main config's "ref", a non-tier family are unanchored; a record whose recipe is the family's
  main config anchors that family only (M, pass).
- Basis of the family link: the anchor script records `recipe_sha256 = config_sha256(recipe)` of the policy it ran (R
  `scripts/make_anchor_answers.py:160`); the 1B record's value is REC 1B's hash (M, keys printed). See concern 1.

### 2.9 C-D4 (the duplicate-unit check)
- Change: the `seen` check moved before `read_unit` (the entry's `complete_sha256` is tested against `seen` before the
  unit's own checks). It is now reachable: the same unit in another seed's slot refuses "its COMPLETE.json SHA-256 is
  already read as …" (not "seed is not 1102"), and the same units under two families refuse as duplicates.
- Tests: `test_a_unit_listed_twice_refuses_on_the_duplicate_check` (a0 twice; R twice; a swap refuses on the seed) and
  `test_a_unit_listed_under_two_families_refuses_as_a_duplicate` (M, pass). Mutant "D4 check removed" KILLED (2 failed, assert).

### 2.10 C-D5 (the fresh-R and the parity-with-tier refusals; N15, N17)
- `test_an_r_unit_that_resumed_refuses_and_an_a0_unit_may_resume`: the frozen `read_json` is wrapped for R@1101's
  `job.json` path only, adding `resume_from` (the file on disk is untouched) → "an R arm is a fresh trajectory (no
  resume)"; unwrapped, the R units record no resume and Gate A's a0@1101 records its init unit `b5083ce9…` (M).
- `test_a_parity_only_family_is_never_pooled_with_a_tier_family`: with `family_reading` stubbed (no 7-8B R unit exists),
  olmo2-1b beside a tier family refuses; two tier families pool with k = 2, df 4; one family reads alone (M).
- Mutants: N15 KILLED (DID NOT RAISE), N17 KILLED (DID NOT RAISE) (M).

### 2.11 Addendum A6 (one family's fallback in the pooled median) and the edit-file check
- Behaviour: `pooled()` already took each family's governing `_exact` block; it now also records
  `governing_by_family` and `pair_terms_by_family` (the six pair SEs by name), so the mixed case is visible in N's output.
- Test: `test_one_familys_fallback_puts_its_r_r_pair_terms_beside_the_others_seed_matched_terms`: the parity family
  read at the family level plain and with the fingerprint trigger; the fallback block's terms are its three R-R pair SEs
  (2.00 / 2.16 / 2.16), the plain block's its three seed-matched SEs (1.18 / 1.28 / 1.29); the pooled median is the
  mean of the 3rd and 4th of the six, (1.29 + 2.00) / 2 = 1.65; √P_pool pools the two governing SD(r); both-plain and
  both-fallback controls (M, pass). Mutant "A6 pooled takes the plain pairs" KILLED (1 failed, assert). Limit: no
  two-family `read()` with real data exists until N runs (concern 2).
- `r_edit_matches(doc, family, seed)` factored out of `read_unit` (the same five fields; R section 2.5).
  `test_the_edit_provenance_check_accepts_the_llama_sealed_sets_r_files_for_n`: the rebuilt Llama R_d1-R_d3 pass for
  llama31-8b at 1101-1103 and are refused for olmo2-7b / olmo2-1b (the manifest) and at d ± 1 (the draw); their
  MANIFEST sha256 == arm; d = 4-16 pass; the 8 unit files, the Llama H1 file, `{}` and `None` are not R units; the OLMo
  d = 11-16 files and SEAL's R_d1 pass for olmo2-7b and olmo2-1b at their seeds (M, pass).

### 2.12 The G1 record regenerated (a consequence of the noise-reader edits)
- `g1_check_78b.py` loads `noise_reading.py` and writes its SHA-256 into the record (R `:44, :135`). Round 1's command
  re-run from the ws-c root with the same relative arguments (M run 20, exit 0): `--units
  .ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105-units.json --out
  .ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json`. Field-by-field diff against the round-1 record
  (M): only `noise_reading_sha256` differs (6cde1a24… → 94b679ff…); per-unit G1 statuses and sampled counts are equal;
  by family: llama31-8b 1 pass / 1 fail (a0-1102), olmo2-7b 3 pass, olmo2-1b 2 pass (addendum A4's reading stands).
  New record SHA-256 8c3579e45557dc518c609a3ff1bb72870a8ad8880eba97e69d27e774e039c48f (round 1 895a5469…). The
  round-1 record: `fix-BC-scratch/llama-g1-check-20261105.round1.json`.

### 2.13 Part 3: the merged tree
- ws-c holds both tracks (section 1). One `scripts/scale78b/__init__.py` and one `scripts/scale78b/tests/conftest.py`
  (merged docstrings; both tracks' needs). The sealed set's own `tests/conftest.py` is unchanged from ws-b.
- One pytest invocation from ws-c, main venv (M run 15): **69 passed, 2 skipped (scipy) in 3.70 s**, exit 0 =
  B 30 + maker 13 + noise 23 (2 scipy skips) + G1 5. Under .venv (scipy), noise + G1: **28 passed** (M run 16).
  B alone from ws-c: 30 passed (M run 21). C alone from ws-c: 39 passed, 2 skipped (M run 22).
- Byte identity (M run 19): ws-c's `build_sealed_llama3.py` 227aed4f… is the `builder_sha256` of all 24 edit files
  and the MANIFEST; `build_r_draws_78b.py` 5cd1036d… is the `scale78b_wrapper.script_sha256` of the 6 draw files and
  the MANIFEST; `build_h1_llama3.py` 504e9462… is `octile_0.json`'s `script_sha256` and the MANIFEST's; every listed
  file's sha256 and arm equal the bytes on disk (24 + 6 + 1).

## 3. Commands run (ws-b or ws-c root as stated; PY = `tmp/minimal-experiment-20261002/venv/bin/python` of the main checkout; V = `.venv/bin/python`; every pytest with `PYTHONDONTWRITEBYTECODE=1 … -B -m pytest -q -p no:cacheprovider --basetemp=<scratch>`; all foreground, none over 5 s except the first ws-c run at 3.7 s)

| # | command | exit / result |
|---|---|---|
| 1 | `date -u`; `git status --porcelain`, `git rev-parse HEAD` in ws-b and ws-c; `find` of the new files; `ls` tmp | 0; four / three `??` paths; `fb51421` |
| 2 | Reads (Read/sed/grep/cat): the rulings, the addendum, plan T3, check C5-C6, the four round-1 reports, the three B scripts, the six B/C test files, conftests, `noise_reading.py`, `make_recipe_s78.py`, `g1_check_78b.py`, the verifier's `mutate.py`/`mutate2.py`, `gate_b_reading.py` helpers, `s1common.py`/`token_accounting.py`/BLD read lists, `edits.py` constants | 0 |
| 3 | `V -I -B` key walk of `.ai/inputs/gate-b-anchors-20261008/out/anchors.sealed.json` (keys and hashes only); `rglob` of anchor records | 0: one record; `provenance.recipe_sha256` 9e9bde6f… |
| 4 | `shasum -a 256` of the round-1 MANIFESTs, octile_0, the three scripts after the edits | 0 (section 2.4) |
| 5 | ws-b: pytest `.ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests` (before the rebuild) | 1: `3 failed, 27 passed` (the committed-out tests on the stale round-1 files; the new guard tests pass) |
| 6 | ws-b: `rm -rf` of the three round-1 `out/` folders; `ls` | 0: READMEs, the wrapper and tests remain |
| 7 | ws-b: `PY -I -B .ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py --olmo-parity-out <scratch>/rebuild-parity` | 0: 25 files; MANIFEST ba524373…; 19 parity files |
| 8 | ws-b: `PY -I -B scripts/scale78b/build_r_draws_78b.py`; `PY -I -B scripts/scale78b/build_h1_llama3.py` | 0; 0: MANIFESTs 189275c0…, 29347da2… |
| 9 | ws-b: pytest (as run 5) after the rebuild | 0: `30 passed in 0.83s` |
| 10 | `shasum -a 256` of the new MANIFESTs, the 6 draw files, octile_0, BLD (both copies); `find __pycache__`; `git status --porcelain` | 0; BLD 80cb8944… ×2; no pycache; four `??` |
| 11 | `V -I -B` field check of the 16 Llama and 6 OLMo R files (section 2.5) and the embedded script hashes | 0: ALL FIVE FIELDS OK True; embedded == scripts |
| 12 | `grep` of stale hashes in the three READMEs | 0 (six values; edited) |
| 13 | ws-c: `V -I -B <scratch>/query_parity.py` (the parity reading's resume record, s_arm, pooled values, ceilings; aggregates only) | 0 (values in sections 2.6, 2.7, 2.10) |
| 14 | `cp -R` / `cp` of ws-b's three folders, two scripts, two tests into ws-c; the three prepared-set files ×2 and BLD's tmp copy into ws-c/tmp; `diff -r` / `cmp`; `find` ws-c/tmp; `git status --porcelain`; `git check-ignore -v` | 0: IDENTICAL ×7; 7 tmp files; six `??` paths; tmp ignored |
| 15 | ws-c: pytest `.ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests -rs` (PY) | 0: `69 passed, 2 skipped in 3.70s` |
| 16 | ws-c: pytest `scripts/scale78b/tests/test_noise_reading.py scripts/scale78b/tests/test_g1_check_78b.py -rs` (V) | 0: `28 passed in 3.29s` |
| 17 | `V -I -B <scratch>/mutate_fix.py <ws-c>` (baseline + 8 mutants; output `mutate_fix_out.txt`) | 0: baseline 23 passed; all 8 KILLED (section 2.6-2.11) |
| 18 | ws-c: `cp` of the round-1 G1 record to scratch; `rm` of it; `V -I -B scripts/scale78b/g1_check_78b.py --units … --out …` (round 1's arguments); `shasum`; `V -I -B` field diff | 0; 0; one field differs |
| 19 | `V -I -B` byte-identity check of ws-c's three hashed scripts against every edit file and MANIFEST; `find __pycache__`; `git status --porcelain` | 0: all True; no pycache; six `??` |
| 20 | (= run 18's G1 command; listed once) | 0 |
| 21 | ws-c: pytest `.ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests/test_build_r_draws_78b.py scripts/scale78b/tests/test_build_h1_llama3.py` (PY; B alone) | 0: `30 passed in 0.83s` |
| 22 | ws-c: pytest `scripts/scale78b/tests/test_make_recipe_s78.py …test_noise_reading.py …test_g1_check_78b.py -rs` (PY; C alone) | 0: `39 passed, 2 skipped in 3.11s` |
| 23 | `git status --porcelain` and `rev-parse` in ws-b and ws-c; `git -C <main> status --porcelain | head` (read only); `rm -rf` of the pytest basetemps, the query temp, the parity edit copies, the mutant roots; `du`; `git status --porcelain -uall` in ws-c (54 files); `shasum -a 256` of ws-c's scripts, tests and records; `date -u` | 0; 15:13:44 UTC |
| 24 | `rm -rf` of the last two pytest basetemps; the kept PARITY.json's flags printed | 0: stage1 d = 6-10 byte_identical True ×5; sealed 13 True |

Not run: any pod, network, install, download, agent, message; anything in the main checkout; any git state change; the
full engine suite (the engine is untouched; round 1's 837 passed stand; a lead job if wanted).

## 4. Acceptance criteria

| criterion | result | evidence |
|---|---|---|
| B's tests pass alone | passed | ws-b run 9 (30 passed); ws-c run 21 (30 passed) |
| C's tests pass alone | passed | run 22 (39 passed, 2 scipy skips, main venv); run 16 (28 passed under .venv: the scipy tests ran) |
| B's and C's tests pass together in ONE pytest invocation from ws-c | passed | run 15: 69 passed, 2 skipped, exit 0 |
| the named mutants die (N4, N5, N6, N15, N17), by a real test failure, baseline with the same command | passed | run 17: baseline 23 passed; each KILLED with `assert` or `DID NOT RAISE` failures, 0 errors; `mutate_fix_out.txt` |
| B-M1: id-only stubs, no prompt or training text read by the tests | passed | section 2.1; `grep load_prepared` finds none |
| B-M2: the H1 guard refuses SEAL and the other committed sealed folders | passed | section 2.2 (SEAL, anchors, stage 1) |
| B-M3: `guard_out` resolves from the script's own root; a non-default `--repo` cannot aim `--out` into SEAL or stage 1; tested | passed | section 2.3 (unit and CLI tests in all three scripts) |
| all three sets rebuilt into EMPTY out/, placement kept (A3), 27+ tests pass, new MANIFEST hashes recorded | passed | runs 6-10; section 2.4 |
| the parity test for stage 1's d = 6-10 passes byte for byte | passed | run 9 (`test_c_olmo_parity_reproduces_stage1_d6_to_d10`); PARITY.json flags (run 24) |
| every Llama R edit file carries exactly the noise reader's five fields | passed | run 11; the new edit-file test (run 15) |
| C-D1 tests pin σ̂_pool, the six-SE median, s_arm | passed | section 2.6 |
| C-D2 one constant; boundary test at the ceiling | passed | section 2.7 |
| C-D3 the S_78 test holds under route (A) | passed | section 2.8 (vacuous today by design) |
| C-D4 duplicate check reached | passed | section 2.9 (the check moved before the unit checks) |
| C-D5 fresh-R and parity-with-tier refusals tested | passed | section 2.10 |
| A6 test: one family's fallback → its three R-R terms + the other's three seed-matched terms | passed | section 2.11 (family_reading + pooled level; see concern 2) |
| new test: the reader's edit-provenance check accepts the rebuilt Llama R_d1-R_d3 | passed | section 2.11 |
| the hashed wrappers in ws-c are byte-identical to those whose SHA-256 the edit files embed | passed | run 19 |
| ws-c `git status --porcelain` lists only new files: `.ai/inputs/scale-78b-*/`, the two G1 records, `scripts/scale78b/` | passed | runs 19, 23 (six `??` paths, 54 files; nothing modified) |
| ws-b left as the rebuild's record | passed | run 23: four `??` folders, HEAD fb51421, no pycache; its out/ holds the rebuilt files |
| the engine suite | not tested (not required; the engine is untouched) | round 1's 837 passed |

## 5. Jobs for the lead

1. **Merge from ws-c by explicit paths** (54 new files, M `git status --porcelain -uall`): `.ai/inputs/scale-78b-sealed-llama3-20261105/`,
   `.ai/inputs/scale-78b-r-draws-olmo2-20261105/`, `.ai/inputs/scale-78b-length-rules-llama3-20261105/`,
   `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105{,-units}.json`, `scripts/scale78b/`. Commit each
   hashed script with its `out/` (the edit files embed the scripts' SHA-256; frozen from the commit on, A3).
2. **In the main checkout after the merge** (each a few seconds):
   `PYTHONDONTWRITEBYTECODE=1 tmp/minimal-experiment-20261002/venv/bin/python -B -m pytest -q -p no:cacheprovider .ai/inputs/scale-78b-sealed-llama3-20261105/tests scripts/scale78b/tests`
   (expect 69 passed, 2 skipped); `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_noise_reading.py scripts/scale78b/tests/test_g1_check_78b.py`
   (expect 28 passed); `scripts/stage1/commitments.py check`; the engine identity re-check (`472fc7f6…`; nothing here changes it).
3. **Records.** If FOCUS or Part 1 cites the round-1 values, replace them: MANIFESTs ba524373… / 189275c0… / 29347da2…;
   the G1 record 8c3579e4… (round 1 895a5469…; counts unchanged); `noise_reading.py` 94b679ff…. verify-C §5 and §8 cite
   the old G1 record hash. Part 1's review-ceiling text should state the rule (removal MDE above 2 × SESOI, exact on
   squares) rather than a ceiling constant; the printed ceilings are now 7.0388 / 9.2721 / 10.7066 pp (derived).
4. **Re-verify.** The verifier can re-run my harness: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I -B <scratch>/fix-BC-scratch/mutate_fix.py <ws-c>`
   (about 30 s; it builds and removes its own scratch root).
5. **Route (A), the anchor jobs.** The new anchoring test ties an S_78 config to an anchor record whose
   `provenance.recipe_sha256` is the family's MAIN config hash (18cc31d7… / 74758af1…). The kit's anchor job must run
   the family's main config as the recipe (as Gate B's did with REC 1B), or the lead amends `anchored_to`. Unchanged
   from round 1: `test_ss_family_codec.py:165` +2 when the configs are committed.
6. Optional: the full engine suite after the merge (round 1's command; about 80 s; the engine is untouched).
7. Delete `fix-BC-scratch/` once read (the round-1 G1 record copy, the harness and its output, the parity record,
   the query script; 36 KB after my cleanup, M `du`).

## 6. Unresolved concerns

1. **The anchor-record family link (C-D3).** It rests on `provenance.recipe_sha256` being the family's main config
   (R `make_anchor_answers.py:160`; M on the 1B record). If an anchor job runs under another recipe (for example an
   S_78 sibling or a Y-engine config), the test fails by design and the lead decides; nothing else identifies the
   family in the record (its `model.repo_id` would be a second check if wanted).
2. **A6 and N17 are tested one level below `read()`.** No 7-8B R unit exists, and one inputs file can name a family
   once, so the two-family mixed case is proved at `family_reading` + `pooled` (real data) and the parity-with-tier
   refusal with `family_reading` stubbed. `read()` composes exactly those two (R `noise_reading.py` `read`), and the A6
   mutant on the `_exact` block dies, but a real two-family `read()` runs first on N.
3. **The duplicate check moved before the identity checks (C-D4).** A unit listed under two families now refuses as a
   duplicate instead of on identity; a malformed entry still refuses on its shape. A small behaviour change; stated.
4. **`FORBIDDEN_DIRS` includes `.ai/inputs/gate-b-anchors-20261008`.** Verifier B named SEAL and stage 1 only; verifier
   C and addendum A3 name the anchor list as a committed sealed input. Over-guarding costs nothing; the lead may trim it
   before the first commit (a byte change: another rebuild).
5. **The G1 record was regenerated** (section 2.12). Its SHA-256 changed; the alternative (leave a record that names a
   `noise_reading.py` no tree holds) seemed worse. Reversible: the round-1 record is in my scratch.
6. **Frozen-on-commit** (round 1's concern stands): any byte change to the three hashed scripts needs a rebuild into
   empty `out/` and the 30 tests again. The READMEs now carry the round-1 hashes beside the new ones for the record.
7. **The main checkout's `git status`** shows the lead's own modified and untracked files (` M .ai/HANDOFF.md`,
   ` M research/review/EDGE_CHECKS.md`, …; M, read only). None of my commands wrote there; every write of mine went to
   ws-b, ws-c or my scratch (section 3).
8. Byte parity for d = 6-10 still depends on the environment (Python 3.11.15, numpy 2.2.6; M); it held here.
