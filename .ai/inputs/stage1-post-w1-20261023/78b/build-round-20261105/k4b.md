# Track K4b report: the kit's pre-block-A scorer kinds (round 4)

Started 2026-11-06 14:24 UTC. This version written 15:24 UTC (`date -u` read right before each write). Status: **DONE**
(with limits; see section 6). Worktree ws-k2 (HEAD d203070; K4a's changes already in it). Scratch: reports/k4b-scratch/
(SCR). PY = the main venv's python. Tags: M measured (command in section 3), R read (path:line), E estimate, I inference.
No pod, spend, network, install, download, agent or message. No git state changed. No secret, selector, hidden,
answer or prompt file opened. The main checkout was read only.

## 1. Files changed

Step 0. Track M's 30 changed files under scripts/scale78b/ copied from ws-m into ws-k2 at the same paths, byte for byte
(M: `cp -p`; both sides' `shasum -a 256` lists equal by `cmp`; `diff -rq` of the two scale78b trees shows no
difference). List: SCR/m-files.txt; hashes SCR/m-dst.sha (scorers_78b.py 108f4425..., PINS-78B.json a2132c9d...,
pins_78b.json 428b7577...). The lead merges scripts/scale78b/ from ws-m, as the brief says.

K4b's own files (all under runkit/stage1-78b/):

| File | What changed | SHA-256 |
|---|---|---|
| rules_78b.py | The scorer block "sc": SC_KINDS (10 kinds), new null pins OEXT_78B and C0_SOURCE, SC_PIN_EVENTS, SC_KIND_PINS, SC_AFTER (A2's order), SC_RECIPE, SC_ARM, SC_STATE_KINDS; engine_sha, sc_pin_values (RECIPE_S must equal pins_78b.json's recipe_s78), sc_needed_pins, sc_missing_pins, sc_pins_or_refuse, sc_order_problem, sc_engine_problem, sc_pod, sc_lines. The untuned pass's E cap now covers both calls (PP2): S3_POOL_ITEMS = 861; 3.0 / 3.25 h became 6.0 h on both families. KIND_LABELS gains regenerate. | 4355f369... |
| stage1_rules.py | BLOCKS ("0", "sc"); BLOCK_KINDS, HOST_PREFIX, FUNDING_BLOCK for "sc"; SCORER_PINS (38 files, the STAGE1_PINS form); WRAPPER, ANCHOR_SCRIPT, PINS_78B, PINS_INDEX, WRAPPER_KINDS, WRAPPER_COMMAND, UNTUNED_CALLS; scorer_code(kind); SC_INPUTS, SC_FOLDER_INPUTS, sc_input_pins; wrapper_settings_waits (the scorer layer's own null-pin rule). | b31284d1... |
| plan_tool.py | `init-block sc` (one init per part): pins78_doc, scorer_settings, sc_complete, sc_planned_keys, sc_job, build_sc, init_block_sc, release_hosts_sc, sc_done_summary; engine_pin (Y through ENGINE_Y); a copy plans only its own block (KD7); a new part's first launch does not wait for the earlier part (`part_start`); record-done prints `scorer_block` (hashes, counts, exit codes, fallback flags only). | 9a8188f9... |
| pack_setup.py | For the sc copy: pins78, scorer_code, input_bundle_path, sc_inputs (the --inputs record's {name, path, sha256}, each at its pin; unit folders by COMPLETE.json), recipe_s78, sc_report (the dry run); the real pack seals the scorer code, the inputs and the S_78 config; the receipt names recipe_s78. Block 0's pack is unchanged. | 3a9cd1e8... |
| setup/job_runner_stage1.py | The sc route: engine_pin, sc_paths, sc_inputs, sc_recipe, _engine_unit, sc_commands (all 10 kinds), out_dirs, hashed_outputs, wrapper_summary, run_sc_job; preflight checks the S_78 config once RECIPE_S is filled; each job's key check uses its own recipe; no s_obs after a scorer job; host engine checked through engine_pin. | fef1b656... |
| README.md, RULES-78B.md | The scorer block section; the untuned cap row (6.0 h, both calls). | dc6af52e..., e9ba21a8... |
| tests/test_scorer_block_78b.py (new) | 51 test items (both families where it matters): kinds, caps and pins by hand; null-pin refusals; init-block sc's printout and part; 16 refusal cases; A2 through the real route; the pack; Y retrain and a1_pass with test-local pins; c0 and o_only; the runner end to end on a fake pod; every command line by hand; record-done; the release re-checks. | d8f27015... |
| tests/run_mutants_scorer_78b.py (new) | A copy of run_mutants_78b.py with its test file and spec changed (diff: 5 lines). | 3bc16a31... |
| tests/mutation_spec_scorer_78b.json (new) | 79 mutants (K4b-m-*). | cadae5d9... |
| tests/test_g1_yoext.py, test_kit_78b_runner.py, test_kit_78b_shell.py, test_round31.py, test_stage1_judge_route.py | Pin tests of "no subject here" updated: OEXT_UNIT_SCRIPT may appear once, only in sc_commands; HOST_PREFIX and BLOCKS hold "sc". | b352ad32..., 74ea14b5..., 85290816..., baceb0e8..., 96a000c4... |

## 2. Items, changes and evidence

Every new function did not exist before, so every new test fails on HEAD (I: by construction). The evidence below is
the mutants each test kills (SCR/mut-sc-final-0.json and -1.json: 79 of 79 killed, run on the final test file).

1. **The kinds (item 1).** Each kind runs alone on a single-job pod with rules_78b's E cap (KD6; `e_pod`); the cap
   test checks all 20 (family, kind) caps, guards and needs by hand. Commands (SCORERS-78B.md section 2):
   - untuned_answers: two wrapper calls (PP1: `--recipe` and `--recipe-s` both the main config; PP2: S3 list with the
     two losses into job-I/untuned, then the S4 list alone into job-I/untuned-s4). One E cap for both: I found the
     old cap covered the S4 call only (R: rules_78b.py's basis text named 512 prompts in 16 chunks). New cap =
     1.5 x (S3 call: 27 chunks + S4 call: 16 chunks, each chunk at the capped-batch maximum measured at 2,048 tokens,
     each call with its own first batch and early/outside time) = 16,146 s OLMo, 16,692 s Llama, cap 6.0 h, guard
     $17.10, need $21.38 (M: test 1 by hand). Killed: K4b-m-untuned-one-call, -untuned-s3-chunks.
   - anchor: `scripts/make_anchor_answers.py --prompts <anchor_prompts> --recipe MAIN --out job-I/anchors`.
   - rep_pass: two passes under S_78 (`--pool s3_safe`, then `--pools-only --pool s3_orig`).
   - l1_scan (main config), classifier (S_78, PP4), both through the wrapper.
   - o_only: theta0, the O-ext unit pass with `--untuned` (M1). regenerate: a reused a0 side unit, train only.
   - c0: make-job run-one of R_1 at 1101 with its sealed edit, then lean_eval_job.py with the expected e1 fingerprint.
   - retrain: a0-1101 under S_78 into rescore/ with its own registry; a1_pass: make-job attributes with q and e1 of
     the packed retrain unit, the 8 unit groups and the anchor bank, then attributes.
   Engines: X_ONLY_KINDS on X only (PP16); the retrain on Y first, on X only after a complete Y retrain (ruling 10's
   pre-set second job); a1_pass on the engine of the complete retrain whose COMPLETE.json is the RETRAIN_UNIT pin
   (ruling 10, A13, EYD:81). Every S_78 kind refuses while RECIPE_S is null: at planning (pins), at the pod's key
   check (recorded "recipe_pin"; test_the_s78_kinds_refuse_on_the_pod...), and in sc_recipe. A2's order is enforced by
   the planner (SC_AFTER: a kind is planned only when the kinds before it are recorded complete). Killed: the 21
   rules_78b mutants and the 26 runner mutants (K4b-m-runner-*), among them -s4-call-with-losses,
   -classifier-main-recipe, -a1-one-state, -retrain-shared-registry, -key-main-recipe, -engine-pin-any.
2. **The block (item 2).** Block "sc" in its own copy tmp/family-probe-s78-<family>-sc/, hosts <family>-sc-N, one job
   per host (A8: one retrain pod per family; a kind planned twice refuses). `init-block sc` prints, per pod, its need
   line and its idle-storage line (PP14; SC_STATE_KINDS: retrain, a1_pass and regenerate keep states), then the part's
   need and idle total; it refuses any pod whose pins are null (rules_78b pins and the scorer layer's settings waits).
   M: the printout test checks 8 lines and every number by hand. Killed: K4b-m-plan-* (14), K4b-m-release-* (5),
   K4b-m-lines-no-idle, -pod-keeps-states-always, -pod-need-no-contingency, -host-prefix.
3. **The bundle (item 3).** SCORER_PINS: scorers_78b.py, its __init__, PINS-78B.json, pins_78b.json, the 18 settings
   files (M's final hashes), the 9 1B scripts of the wrapper's STAGE1_CODE plus stage1/__init__.py, labels.json,
   lexicon_pin.py, lexicon/lexicon.json, lexicon/lexicon.py, token_accounting.py (what those scripts import or read;
   R: their import lines), and make_anchor_answers.py (Gate B's pin 5a686a82...). M: every pin equals the worktree
   file, the wrapper's own STAGE1_CODE and PINS_FILE_SHA256 literals, and the index (test
   test_the_scorer_pins_are_the_layers_own_literals_and_files). A changed scorer file refuses at the dry pack, the
   pack and the release (tested for the wrapper, a settings file and s1common.py). Killed: K4b-m-pin-*, -pack-* (8),
   -code-anchor-none, -release-code-unchecked.
4. **The runner's record (item 4).** run_sc_job hashes every output file (never reads one for a value), reads only
   exit_code, doses.fallback_fired, doses.kept and doses.top_dose from each wrapper_78b_record.json (type-checked; the
   record's exit code must equal the step's), records the s3_orig pool's and the anchor file's SHA-256 and, for the
   retrain and regenerate, the unit's COMPLETE.json and fingerprints. The S4 call's exit 3 (fewer than 48 kept) is the
   pass's own end; any other non-zero exit, the S3 call's exit 3 included, is a crash. record-done prints
   `scorer_block` with hashes, counts, exit codes and fallback flags only. M: the fake-pod test walks JOB-DONE.json,
   every job-done record and the printed lines for four sentinels (an answer, a prompt, a U value, a row id): none
   appears. Killed: K4b-m-runner-wrapper-*, -top-dose-text, -record-kind-unchecked, -s3orig-missing-ok,
   -s4-exit3-crash, -s3-exit3-ok, K4b-m-done-* (4).
5. **Tests and mutants (item 5).** See section 3.

## 3. Commands (all foreground; exit status)

| # | Command (cwd ws-k2 unless said) | Result |
|---|---|---|
| 1 | `date -u` before each time written (14:24, 14:35, 14:57, 15:08, 15:23, 15:24) | 0 |
| 2 | `cp -p` of M's 30 files; `shasum -a 256` both sides; `cmp`; `diff -rq` | 0; IDENTICAL; no difference |
| 3 | `PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests` (baseline, before changes) | 0: 362 passed |
| 4 | the same after each step | 404, then **413 passed** (final) |
| 5 | `python3 -B SCR/check_finds.py runkit/stage1-78b` (every mutant's find text once) | 0: bad 0 over 106, 103, 31, 79 |
| 6 | `python3 -B SCR/make_spec.py runkit/stage1-78b` | 0: 79 mutants, every find unique |
| 7 | `caffeinate -i PY -B tests/run_mutants_scorer_78b.py ws-k2 SCR/mut-sc-a ... <first 40>` (15:03) | 0 pipeline; 39 killed, 1 survived (K4b-m-pins-l1-none); a test added |
| 8 | the same, the other 39 (15:04-15:06) | 1: 38 killed, 1 survived (K4b-m-runner-engine-pin-any); a test added |
| 9 | the two survivors again (SCR/mut-sc-c) | 0: 2 of 2 killed |
| 10 | **the whole scorer spec on the final test file, two halves** (15:17-15:21; SCR/mut-sc-final-0/-1) | **0, 0: baseline 0; 40 + 39 = 79 of 79 killed, 0 invalid** |
| 11 | `caffeinate -i PY -B tests/run_mutants_78b.py ws-k2 SCR/mut-rules SCR/mut-rules.json ALL --timeout 300` (15:08) | **0: baseline 0; 103 of 103 killed** |
| 12 | `caffeinate -i PY -B tests/run_mutants_runner_78b.py ws-k2 SCR/mut-runner ... ALL` (15:09) | **0: baseline 0; 31 of 31 killed** |
| 13 | `caffeinate -i sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip "*:*"))' PY -B tests/run_mutants_gated_78b.py ws-k2 SCR/mut-gated-b ... <34 conftest ids>` (15:10-15:13) | **0: baseline 0; 34 of 34 killed** |
| 14 | the same, the other 72 ids (SCR/mut-gated-a; 15:13-15:17) | **0: baseline 0; 72 of 72 killed** (106 of 106 in all) |
| 15 | `caffeinate -i PY -B -m pytest -p no:cacheprovider -q runkit/stage1-olmo/tests` (separate process) | **0: 762 passed** |
| 16 | `git diff --quiet HEAD -- runkit/stage1-olmo` | 0 (unchanged) |
| 17 | the 7-8B suite under the network-deny sandbox line of #13 | **0: 413 passed** |
| 18 | `PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests/scorers` (ws-k2) | 0: 98 passed, 15 skipped (ws-k2 has no tmp/kt-prepared; M measured 113 in ws-m with it) |
| 19 | `find runkit scripts -name __pycache__` | none |

## 4. Acceptance

| Criterion | Result | Evidence |
|---|---|---|
| The planner works for the scorer block on both families with test-local pins where the real pins are null | passed | M: test_a2s_order... and test_the_retrain_and_a1_pass_on_y... (both families): parts 1-3 planned and released (the Y retrain onto a stand-in Y stage), every later kind with test-local pins |
| The dry pack works for the scorer block on both families | passed | M: test_the_pack_refuses_an_input_off_its_pin_and_packs_the_scorer_code (both families): the 38 code pins, the inputs, the waits per kind; the real pack seals them |
| Refusals while pins are null | passed | M: test_the_committed_pins_are_null... (every kind, both families, the committed files), 16 init refusals, the pack's null-pin refusal, the pod's recipe_pin refusal |
| A2's order enforced by the planner | passed | M: A2 test; mutants K4b-m-order-off, -after-*, -plan-order-off killed |
| Each pod's need on its own line with its idle-storage line (PP14) | passed | M: printout test (lines and numbers by hand) |
| The bundle pins scorers_78b.py, settings/ and the 1B scripts; a changed file refuses at pack time | passed | M: pins test; three changed-file cases refuse at dry pack and pack |
| The runner reads the wrapper record and records counts and hashes only; record-done prints no U and no text | passed | M: fake-pod test with four sentinels; record-done refusals of text values |
| All suites pass | passed | M: 413 (7-8B, plain and sandboxed); 762 (stage-1, unchanged) |
| All mutants killed (three kit runners and the new one) | passed | M: rules 103/103, runner 31/31, gated 106/106 (sandboxed), scorer 79/79; 0 invalid |
| CUDA, a real pod, the real scorer scripts on a real model | not tested | the brief's $0 scope; fake processes only |

## 5. Jobs for the lead

1. Merge by explicit paths: runkit/stage1-78b/{rules_78b.py, stage1_rules.py, plan_tool.py, pack_setup.py,
   setup/job_runner_stage1.py, README.md, RULES-78B.md}, the new tests/{test_scorer_block_78b.py,
   run_mutants_scorer_78b.py, mutation_spec_scorer_78b.json}, and tests/{test_g1_yoext.py, test_kit_78b_runner.py,
   test_kit_78b_shell.py, test_round31.py, test_stage1_judge_route.py}, together with K4a's files (k4a.md section 1),
   and scripts/scale78b/ from ws-m (M's list). Then `scripts/stage1/commitments.py check`.
2. After the merge, in the main checkout (not measured there): `PYTHONDONTWRITEBYTECODE=1 PY -B -m pytest -p
   no:cacheprovider -q runkit/stage1-78b/tests` (expect 413), the stage-1 kit's suite in its own process (expect
   762), and `caffeinate -i PY -B runkit/stage1-78b/tests/run_mutants_scorer_78b.py <repo> <new scratch> OUT.json ALL
   --timeout 300` (about 3 min here; expect 79 killed).
3. Rule on concerns 1-5 below (the untuned cap; the meaning of "o_only and regenerate for both untuned units"; the
   O-ext re-derivation for M1; c0's source; engine Y's pack).
4. Fill pins only by recorded steps, in A2's order, from record-done's `scorer_block` printout: the anchor file's
   SHA-256 into pins_78b.json and the settings (make_scorer_settings_78b.py), S_78 into both RECIPE_S places, the
   s3_orig pool, the retrain unit; re-pack between parts (move setup/packed-stage1-X aside first).
5. Delete after review: reports/k4b-scratch/ (20 MB: mutation repo copies and JSON results; evidence only) and
   ws-k2/tmp/engine-y-34bfd288 (K4a's 67 MB fixture copy, still used by #15).

## 6. Unresolved concerns

1. **The untuned pod's cap doubled (3.0 / 3.25 h to 6.0 h; guard $11.55 / $12.01 to $17.10).** The old cap covered
   the S4 call only (I: an error, not a choice; PP2 and SCORERS-78B.md say one cap covers both calls). My upper is
   M-bounded: every 512-token S3 chunk at the 2,048-token capped-batch maximum. Scaling the S3 chunks by 512/2048 (E,
   unmeasured) would give about 4 h. Block 0's printout of this pod changes with it (need $14.44 / $15.01 to $21.38).
   The first run measures it (KD6).
2. **"o_only and regenerate for both untuned units" (M1) is my reading.** o_only = theta0 (the family's untuned
   model, `--untuned`); regenerate = a train-only regeneration of a reused a0 side unit (ruling 7). A regenerated
   unit's O-ext pass would need o_only on the same pod, which KD6's single-job rule forbids; `o_only_with_regenerate`
   (an E kind) is not in SC_KINDS. The lead decides.
3. **o_only and c0 cannot run at 7-8B yet.** The S1 package's O-ext unit pass pins 1B recipes and the 1B manifest in
   its settings (R: scripts/stage1_s1/settings/oext_unit.json `recipes.allowed`, `prepared.manifest_sha256`), so it
   needs settings re-derived per family (M1; Part 2 names the evaluation bank). I added the null pin OEXT_78B; both
   kinds refuse until it is filled. I did not read lean_eval_job.py's settings (I: the same issue for c0).
4. **c0 needs block 0's R_1-1101 unit**, which lives in another working copy (KD7): null pin C0_SOURCE.
5. **Engine Y has no pack.** pack_setup.py packs X only (KD9's step). The Y retrain and a Y a1_pass are planned with
   ENGINE_Y filled but are released only onto a setup/packed-stage1-Y stage (tested with a stand-in). The S_78
   config's engine hash for a Y host is computed with X's code here (the 1B kit's check_recipe_y is not ported).
6. A1's pass reads the retrain's unit as a packed folder input (its q and e1 states; E: about 1.9 GB each, KCR §6),
   so its bundle is large. The alternative, running it on the retrain's stopped pod, has no kit path.
7. Each part's funding need counts only that part's launches; pods of an earlier part still running are covered by
   the live-balance guard at launch, not by the new part's record (I).
8. The bundle does not carry the 1B settings files under scripts/stage1/settings/ (I: the wrapper replaces the
   module globals, so the 1B scripts read the family settings). Untested on a real pod.
9. requeue, defer and confirm-stopped are not tested for scorer-block hosts (not in the brief).
10. K4a's concern 4 stands: plan_tool.py's copied 1B code still holds `rules.X_ONLY_KINDS = ()` paths (not reached by
    block 0 or sc).
