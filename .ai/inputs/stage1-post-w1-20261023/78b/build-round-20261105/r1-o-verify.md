# R1 Track O: adversarial verification of the 7-8B O-ext layer

Written 2026-11-08 16:16 UTC (`date -u`). Started 15:31 UTC. Status: **DONE**.

**Verdict: DEFECTS.** There is one major defect (O1) and eight minor defects (O2-O9). The core rule holds: I found no
label lie on any route, the parity holds, and the 1B files are unchanged. O1 is a design flaw in how the pins are
filled, not in a run. The minor defects are test gaps, test hygiene, one stale settings value and missing Mac-side
checks.

Target: WS = `B/ws-o`, a detached worktree at `3481d85`. Builder's report: `R/r1-o.md`. My scratch:
`R/r1-o-verify-scratch/`. I edited nothing in WS. M: after my runs, all 26 new files still hash to the values in
r1-o.md §1. `git diff --stat` is empty, there are no new `__pycache__` folders, and WS `tmp/` is still empty. I made
no git state change. There was no pod, network, install or download. I opened no answer, generation, guard, judge,
sealed or prompt file. From the committed G1 record I printed keys and hashes only. From the manifests I printed
counts only.

Tags: M = measured (the command or file is named), R = read (path:line in WS), E = estimate, I = inference.

## Defects

| id | sev | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| **O1** | **major** | `oext_78b.py:69` (`INDEX_SHA256` literal); `make_oext_settings_78b.py:332-360` (one index for both families and both engines; the form lists the wrapper and the index) | Every pin fill changes **both** families' RK `OEXT_78B[F]` forms. This holds for either family's branch, θ0 job pin or recipe G, and for `ENGINE_Y` or `RECIPE_BQI`. The cause: the index holds every family's and every engine's file hashes, the wrapper pins the index by a literal, and every form lists both the wrapper's hash and the index's hash. M: `cascade.py`. A fill of Llama's branch, Llama's θ0 pin, `shared.engine_y` or OLMo's `recipe_bqi` changes `OEXT_78B[olmo2-7b]` in `oext_78b.py` and `OEXT-78B.json`, and the reverse also holds. This contradicts r1-o.md §0 reason 3 ("no hash cascade") and §2 ("the other family is untouched"). | Say `OEXT_78B[olmo2-7b]` is filled and used for OLMo's `o_only`, c0 and arm pods. Later, Llama's G config (GXB O11), `ENGINE_Y` (K3) or `RECIPE_BQI` (block B) is filled. The wrapper and index bytes change, so OLMo's pinned file hashes no longer match. The pack refuses (R: `runkit/stage1-78b/pack_setup.py:384`) until another recorded step re-fills `OEXT_78B[olmo2-7b]`. Block A and block B jobs then carry different `OEXT_78B[F]` values, and O11's "filled once" fails. | Lead decision. Option (a): make the wrapper the same before and after any fill, by removing the index literal. Use per-(family, engine) index files, `OEXT-78B__F.json` and `OEXT-78B-Y__F.json`. The kit's forms (`OEXT_78B[F]`, `OEXT_78B_Y[F]`) pin them, and the kit passes the pin to the wrapper (for example `--index-sha256`). The $0 `check` takes it as an argument. Option (b): accept re-fills as recorded steps and say so in T-O2. |
| O2 | minor | `tests/oext/test_oext_78b_unit.py:96-109`, `test_oext_78b_lean.py:142-150` (only the true label is tested) | No test feeds the wrapper a settings file that names another O-ext file. Mutants that take the label from the file itself, `V-w-label-from-file` and `V-w-lean-label-from-file`, **survive** the builder's suite (M: `vmut-a.json`). The verifier's probes kill them (M: `vmut-b.json`, `vmut-c.json`). | A later "simplification" sets `OEXT_SETTINGS_PATH` from `unit_doc["oext"]["settings"]["path"]`. Then a file naming `scripts/stage1_s1/settings/oext_eval.json` passes while the run reads the family's file. That is the GXB O3 label lie, and every test stays green. | Add the probes `test_a_unit_settings_file_naming_another_oext_file_refuses` (both labels) and `test_a_lean_settings_file_naming_the_1b_oext_file_refuses`, and add both mutants to the spec. |
| O3 | minor | `oext_78b.py:387` (lean's `check_prepared`), `:380`/`:401` (lean and w1_18 `check_code`), `:361` (manifest consistency); `make_oext_settings_78b.py:358` (form roles) | These branches are untested. `V-w-lean-no-manifest`, `V-w-lean-code`, `V-w-w1-code`, `V-w-unit-manifest-consistency` and `V-m-form-roles` **survive** (M: `vmut-a.json`). The form test asserts only `oext_unit__F`'s entry (`test_oext_78b_files.py:315-326`). | A form without `oext_eval__F`, the W1-18 settings or `lean_eval_job__F` passes RK's check. The pack then lacks the file, and the pod refuses because the file cannot be read (a paid start). Lean on the other family's prepared set reaches the 1B code unchecked by the wrapper. | Add the probes in `test_zz_verify_probes_incopy.py` §7 (they kill all five; M: `vmut-b.json`) and the five mutants. |
| O4 | minor | `tests/oext/test_oext_78b_unit.py:112-129` | The restore test covers a refusal that *returns* 2, not an exception. `V-w-restore-success-only` (restore only on a normal return) is killed only by accident (I). An earlier test, `test_oext_78b_files.py:264-266` (`pytest.raises` around `w.patched`), leaks `ou.OEXT_SETTINGS_PATH` under the mutant (M: the kill in `vmut-a.json`). | The kill depends on test order. If that files test is removed or reordered, an exception path (argparse `SystemExit` inside `ou.main`, a crash in W1-18's tools) could leave the family's globals set for the rest of a process, and no test would see it. | Add explicit tests (verifier probes, section 2): `SystemExit` from `--checkpoint e9`, and an exception from `real_tools`. Both pass on WS today. |
| O5 | minor | `tests/oext/test_oext_78b_unit.py:252-257` | Test-hygiene leak. `monkeypatch.setattr(w, "INDEX_SHA256", …)` runs **inside** `env.fam.active()`. At teardown, monkeypatch restores the fixture's value, so `oext_78b.INDEX_SHA256` stays `75805057…` for the rest of the session (M: a one-test probe after `test_oext_78b_unit.py`; deselecting this test removes the leak). | Any later-sorted test that uses the committed index fails for the wrong reason. M: two of my probes failed this way until I gave them their own index. A mutation kill could then come from the leak, not the mutant. | Call `monkeypatch` before `active()`, or set the pin with `w.patched` inside it. |
| O6 | minor | `make_oext_settings_78b.py:32-33` (the fill procedure); `tests/oext/test_oext_78b_files.py:96-111, :117-138, :172-207`, `test_oext_78b_w1_18.py:139-151` | The documented fill step is "edit pins; run the maker; set `INDEX_SHA256`; run the tests". It breaks the suite by construction. M: I simulated T-O2 step 1 (OLMo's θ0 job pin) in a scratch copy, and 4 tests fail: `test_the_side_units_are_rk_kit_a0_units_with_the_committed_job_pins`, `test_the_waits_name_their_pins_and_events`, `test_the_committed_files_refuse_each_command_with_its_event[THETA0_JOB]`, `test_theta0s_null_job_pin_refuses_in_the_wrapper_and_in_the_1b_check`. The branch and G fills break more (R: they assert `pending_w1_18` and Llama's `G: None`). | Each recorded fill must edit tests, with a risk of weakening them under time pressure. The fill and its test edits become one step. | Derive the expected waits, branches and pins in these tests from `oext_pins_78b.json` (null → wait). Keep the pending-state refusal tests on fixture copies. |
| O7 | minor | `oext_78b.py:308-326`; `make_oext_settings_78b.py:179-193`; `oext_78b.py:411-420` (`check`) | Nothing checks a pinned W1-18 record against the family on the Mac at $0. The wrapper checks only the record's hash. The maker takes only `{branch, record_sha256}`. `check` never reads the record. M (verifier probe 5): a wrong-family record, a stale record (made under other W1-18 settings) and a failing record pinned under Branch 128 all pass the wrapper's flag check. The unchanged `oext_eval.read_w1_18` refuses each on the true path (`oext_eval.py:374-385`), with exit 2 before any folder. | A typing error in the branch fill passes every Mac check and is packed into `OEXT_78B[F]`. The first O-ext pod of that family then refuses (a paid start). Every later pod of that family refuses until a re-fill, which O1 makes worse. | Add `oext_78b.py check --family F --w1-18-record PATH`, which runs `oe.read_w1_18` under the family's W1-18 globals ($0, a text-free record). Or have the maker read the record at fill time. This matches DESO2 K6v-4's "refused on the Mac too". |
| O8 | minor | `settings/limits_overrefusal_checks__{olmo2-7b,llama31-8b}.json` `judge.device = "mps"` (kept from 1B; `make_oext_settings_78b.py:250` updates only `recipe`, `recipe_file_sha256`, `repo_id`, `revision`); `oext_78b.py:105` (`--device` optional) | The 7-8B W1-18 check runs on a CUDA pod (GXB O5, K-3), but the settings keep the 1B Mac device. `overrefusal_checks.py:558` uses `args.device or settings["judge"]["device"]`. | If a runner call leaves out `--device cuda`, the run loads the guard on "mps" on Linux. It crashes after the units are read: a paid pod with no record. Under the fallback, the branch becomes Branch full. | Derive `judge.device = "cuda"` for 7-8B, or make the wrapper require `--device` for `w1_18`. |
| O9 | minor | `make_oext_settings_78b.py:350-360` ("the Y files are B+Qi's, outside this pin") | T-O3 adds a null `OEXT_78B_Y[F]`, but no printer, test or text defines its files: `oext_unit_y__F`, `oext_eval_y__F`, the W1-18 settings that `oext_eval_y` binds, the index and the run files. | K1 or K3 has to invent the Y form, and a missing file is found only on the Y pod. | Add `--oext-78b-y F` with a test against RK's `oext_form_problem`. |
| O10 | nit | `scripts/stage1/limits/limits_common.py:70-91` (frozen reader), `:233` (lexicon); W1-18 settings `judge.recipe` | No form lists the files that the W1-18 pod (not the unit and lean pods) needs: `scripts/family_probe_reading.py`, `scripts/killtest_stage0_reading.py`, the lexicon files (already in `SCORER_PINS`) and the MAIN_F config under `ENGINE_ROOT`. | K3's `w1_18` kind is packed without the frozen readers, and W1-18 refuses on the pod ("the frozen script … is missing"). | K3 note: list them in the W1-18 kind's files. |
| O11 | nit | `make_oext_settings_78b.py:375` | `--oext-78b` imports the wrapper by package name *after* `s1common` has put its resolved root first on `sys.path`. In a linked copy, it prints another checkout's wrapper hash. M: my scratch copy printed WS's `9ea348e0…`, not the copy's `70c92083…` (`form-llama-after-olmo-theta0-fill.json`). | This is harmless in MAIN, which has one root. It misleads in mirrors, for example a re-fill dry run in a scratch copy. | Load `oext_78b.py` from `HERE` by file path. |
| O12 | nit | `R/r1-o.md` §1, §0 reason 3, §2 | The report says "WS `tmp/` is absent (M)". WS `tmp/` exists: it is empty, and its birth time is 2026-11-08T14:43:08Z, at the build's start (M: `stat`). The fill-reach claims are understated (O1). | — | Correct the report. |

## 1. No label lie (GXB O3): passed (M, R)

- **Path labels written, per route (R).**
  - `unit`: `identity.oext_unit.script` = `OWNER` = `scripts/stage1_s1/oext_unit.py`, the module that ran (`oext_unit.py:74`, `:592`). `job.json` and the identity hold hashes only (`job_of`, `_oext_job`). `job.run` and `job.dev100_source` are the caller's paths.
  - `oext_eval`'s summary: `provenance.script` = `rel(oext_eval.py)` (`oext_eval.py:719`). The W1-18 inputs are hashes (`:635-640`).
  - W1-18's record: `provenance.script` = `rel(overrefusal_checks.py)` (`overrefusal_checks.py:446`). `tools.recipe` is the settings' `judge.recipe`, which is read under `ENGINE_ROOT` (`:474`, `:519`). The units' paths are the paths that were read.
  - c0 record: `provenance.script` = the copy (`lean_eval_job_78b.py:710`). The O-ext part holds hashes (`:346-350`). `lean_job.json` holds hashes (`:650-657`).
  - Index: the 1B bases the maker reads, the pins file and the derived files.
  - Settings labels: the unit file's `oext.settings.path` names `scripts/scale78b/settings/oext_eval__F.json` (lean: the same; Y: `oext_eval_y__F`). The wrapper sets `OEXT_SETTINGS_PATH` to `fam.label(role)`, computed from the index entry of the file it loads (`oext_78b.py:214-220`, `:370`, `:391`), never from the file's own text.
  - The wrapper's stderr line names the settings' hashes only.
- **Label lies are refused through the wrapper (M, verifier probes).** A unit settings file that names the 1B O-ext path, or the other family's, exits 2 with "oext names the O-ext module and its settings file", and no folder is made. So does a lean settings file that names the 1B path.
- **Globals are restored on every exit path (R: `oext_78b.py:333-343`, try/finally; M).** I measured three paths: success and a returned refusal (the builder's tests), an argparse `SystemExit` raised inside `ou.main` with `--checkpoint e9` (it passes the wrapper's flag check), and a `RuntimeError` from W1-18's tools. All eight globals (`ou.load_pinned_settings`, `oe.load_pinned_settings`, `ou.OEXT_SETTINGS_PATH`, `w1.SETTINGS_PATH`, `w1.SETTINGS_SHA256`, and the copy's `SETTINGS_PATH`, `SETTINGS_SHA256`, `OEXT_SETTINGS_PATH`) equal their values before the call.
- **No leak across two calls in one process (M).** Two families' `w1_18` runs in one process, each with its own settings and data root: each record's `provenance.settings_sha256` is its own family's settings hash, and the two differ. A cross-wired call (Llama's settings on OLMo's units) refuses. Two families' `unit` runs in one process: each `job.json` names its own `settings_sha256`, `oext.settings_sha256` and `w1_18_record_sha256`, and all three differ between the families. The globals are restored after each run.
- No module cache is keyed by settings (M: `grep lru_cache|_CACHE|global` over the run path). The only caches are `s1common._REGISTRY` (the labels registry) and `limits_common._READERS` (keyed by path and pins). Neither depends on the family.

## 2. Parity: passed (M)

- **The lean copy rebuilt independently** (`rebuild_lean.py`, from `git show 3481d85:scripts/stage1_s1/lean_eval_job.py`, by line edits I wrote) equals `lean_eval_job_78b.py` byte for byte (`fc0372ca…`). The `diff` against the 1B file shows the head paragraph, the `oext_eval` import, the new global, the :229 comparison and the program name, and nothing else. (Nit: the head lists four changes, and the spec counts five substitutions, because change 3 is two edits.)
- **The 1B files are unchanged.** `git diff --stat -- scripts/stage1 scripts/stage1_s1 scripts/stage1/limits` is empty. All 455 tracked blobs under `scripts/stage1`, `scripts/stage1_s1`, `runkit/stage1-olmo` and `scripts/scale78b` equal MAIN@3481d85 (`git hash-object` against `ls-tree`; 0 differ). The ten key 1B files and settings have equal SHA-256 in WS and at MAIN@3481d85.
- **Wrapper outputs equal the 1B scripts' outputs.** The builder's parity tests pass in my run: unit under Branch 128 (`unit_eval`, `source_unit`, `generated`) and under Branch full, with `job`, `identity`, `dependencies`, `assets` and the `oext_*` files byte-equal; the W1-18 record byte-equal; for lean, 9 sealed files byte-equal, and the record differing only in the five identity fields.
- **c0's timer.** The wrapper's imports before the copy's origin take about 18-20 ms on the M4 Mac (M: `-X importtime`, cumulative for `scripts.scale78b.oext_78b`, 3 runs: 19.6, 18.4, 18.1 ms). On Linux, `process_age_at_origin` covers them (P7).

## 3. Settings: passed, except the form-level reach (O1)

- **Manifests.** OLMo-2-7B `9ed61826…` (equal to RK `MANIFESTS` and to the 1B prepared set, which it shares). Llama `c52a50af…` (M: key diff against the 1B bases).
- **`recipes.allowed`.** OLMo `{MAIN: 18cc31d7…, G: 01259f28…}`, which matches DES F2's "OLMo-2-7B's existing main-LR config". Llama `{MAIN: 74758af1…, G: null}` (O11).
- **Generation and guard blocks.** `5ddced7a…` and `a7f0755b…` on MAIN for both families, on OLMo's G, and on Llama's LR 1e-4 config `c5462c77…` (M: the C3 expression; this also settles T-O4's condition at the config level, see P4).
- **Branch.** `pending_w1_18`, with the record and the reason null, in `oext_eval`, `oext_eval_y` and `lean_eval_job`.
- **Y variants.** `engine_x` null, and `allowed {"B+Qi": null}`.
- **W1-18 units** equal RK KIT `a0_units` (COMPLETE.json hash and path with `tmp/` stripped). The five a0 job.json hashes equal the committed G1 record's (`8c3579e4…`; committed bytes equal the file), matched by COMPLETE hash, with seed, checkpoint and recipe also matching. θ0's two pins are null, with the wait `THETA0_JOB`. All seven paths match their family's `path_pattern` (M).
- **The maker reproduces every file (M).** `make_oext_settings_78b.py --check` gives "checked 13 files", exit 0. `INDEX_SHA256` = `shasum OEXT-78B.json` = `7c3edb0f…`. The wrapper's `check` exits 0, with the same waits as r1-o.md §2.
- **Fill reach.** A filled branch reaches exactly the family's settings files plus the index (the builder's test). But the index and the wrapper are in both families' forms (O1).

## 4. The Branch-128 flags (DESO item 9): passed, with O7's limit (M)

- `--w1-18-record` is taken exactly when the family's O-ext settings pin a record, and only with the pinned hash (the builder's tests and mutants; my runs).
- A repeated flag, an abbreviation (`--w1-18-rec`, `--dev100-sourc`) and a second `--prepared=` all refuse. `lean` refuses `--dev100-source`. `transfer` refuses.
- `--dev100-source` is taken only with `--run` under Branch 128. With `--untuned`, or under Branch full, it refuses.
- **Attacks.** A wrong-family record pinned, a stale record pinned, and a failing record pinned under 128 all pass the wrapper. All three are refused by `oext_eval.read_w1_18` ("not made under the pinned W1-18 settings", or "fails its bar, so the branch is full, not 128") before any folder. So the true path holds, but only on the pod (O7).

## 5. The per-family W1-18 (GXB O4): passed (M)

- One process ran both families' checks, each with its own settings and its own record, and each record names its own settings hash (section 1).
- The family's branch is read only from its own record: `cap.w1_18.settings_sha256` = the family's W1-18 settings, and `read_w1_18` requires the record's provenance to equal it (`oext_eval.py:374-375`).
- With the 1B globals, the family's O-ext settings refuse (the builder's `test_the_binding_reads_the_familys_w1_18_settings`).
- The ninth seam (`lean_eval_job.py:229`) is correctly found. A literal cannot be patched, so the copy route for lean is right (T-O1).

## 6. Tests and mutants (M)

**Suite.** `sandbox-exec -p "$SB" PY -B -m pytest -p no:cacheprovider -q scripts/scale78b/tests` in WS: **274 passed, 57 skipped** (31.7 s), as the builder reported. The oext folder alone, in each runner baseline: 66 passed.

**Builder's spec (`d37e69b6…`), my four shards under the sandbox, each with its own baseline (66 passed):**

| Shard | Result |
|---|---|
| 1 | 11 killed |
| 2 | 11 killed |
| 3 | 11 killed |
| 4 | 8 killed |

That is **41 of 41 killed**, with 0 survived, 0 invalid and no ERROR line (M: `mut-v{1..4}.json`). The spec has 27 wrapper, 13 maker and 1 copy mutants.

- **Golden kills.** 10 of the 13 maker mutants fall first to `test_the_maker_reproduces_every_file…`, a comparison of the derived bytes with the committed files. With that test deselected, all 13 are still killed (M: `golden_off.py`), but mostly by two other comparisons with the committed files. So the maker's rules are tested mainly against today's committed state (an observation; see O6).
- **Runner validity (R: `run_mutants_oext_78b.py:62-86`; M).** A kill requires exit 1, at least one FAILED line and no ERROR line. An exit of 2-5, an ERROR line or a timeout is invalid. The baseline uses the same command. The copy is restored and re-hashed after each mutant. The tests import the copy's `scripts/scale78b` (the conftest asserts it) and WS's 1B files. They never import MAIN's (M: a module-origin probe; the venv has no `.pth` that names MAIN).

**Proposed mutants (`proposed_mutation_spec.json`, `add3e3f0…`, 11 mutants; run in a scratch source root, never in WS):**

| Run | Suite | Killed | Survived |
|---|---|---|---|
| a | builder's only | 3: `V-w-restore-success-only` (by accident, O4), `V-m-w1-manifest`, `V-m-w1-prepared-path` (golden) | **8**: `V-w-label-from-file`, `V-w-lean-label-from-file`, `V-w-lean-no-manifest`, `V-w-lean-no-branch-flags`, `V-w-lean-code`, `V-w-w1-code`, `V-w-unit-manifest-consistency`, `V-m-form-roles` |
| b + c | with the verifier's probes (85, then 86 tests) | all except one | 1: `V-w-lean-no-branch-flags` |

`V-w-lean-no-branch-flags` is equivalent in effect: the 1B lean job refuses the same inputs before any folder, and only the message differs.

## 7. The builder's open points

- **P1 (route).** Ruled by T-O1; fine.
- **P2 (θ0 job pins).** A lead step (T-O2 step 1), not a defect. Two notes:
  - Doing it as documented fails 4 tests (O6).
  - P2 §14 item 29's $0 check is still open: the side units' stored dev-100 answers as W1-18's inputs. The manifests' dev bank holds 96 + 200 + 100 + 72 = 468 greedy items and 189 ARC items (M: counts). These equal the family-probe bank's 468 greedy + 189 ARC (P2 §1.14), so the side units hold the 100 over-refusal answers (I). The lead still runs the count through the frozen reader.
- **P3 (kit changes).** Lead, K1 and K3 steps (T-O3). Add O9 (the Y form), O10 (the W1-18 pod's files) and O8 (`--device cuda` until fixed). K3's Y pack must ship the unchanged `oext_unit.py`, not the 1B Y copy at its path, or the wrapper's `CODE` pin refuses it (R: `oext_78b.py:82`, `:145-153`).
- **P4 (Llama θ0 recipe).** Ruled by T-O4. The config-level condition holds: `c5462c77…`'s generation and guard blocks hash to MAIN_F's `5ddced7a…` and `a7f0755b…` (M, this run). The tokenizer field is equal across the two Llama configs (M). The lead still records the check (and, per T-O4, the unit's own recipe).
- **P5.** Fine. The units are pinned by COMPLETE and job hashes, so the 1B `refused_recipes` is not binding (I). `sealed_map` null is report-only.
- **P6.** Fine, and now measured. Both manifests' dev banks hold harm 200 and over-refusal 100 (M). The task rows are 8 categories × 25 = 200 in both manifests (M: `eligibility.by_category.*.task`). That these are the lean job's `query_rows` (`lean_eval_job_78b.py:409`) is I.
- **P7.** Fine: about 18-20 ms (M, Mac).
- **P8.** Fine (prose). In Track O's six OLMo files, four text fields name 1B facts (M: a pattern count): `oext_unit` and `oext_unit_y` `oext.rule` (kept from 1B) and `recipes.rule` (rewritten; it cites "the 1B O-ext pins"), `lean_eval_job` `oext.rule` (kept), and `limits_overrefusal_checks` `pins` (rewritten).
- **Observation (not a defect).** The kit's job records must name the wrapper through `OEXT_78B[F]`. No output names it, because the wrapper writes nothing by design (r1-o.md §2).

## 8. Commands for the lead's full runs

```
SB='(version 1)(allow default)(deny network-outbound (remote ip "*:*"))'; PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
V=<R>/r1-o-verify-scratch
# the verifier's probes against WS (14 tests; they passed here, exit 0)
cd <WS> && VERIFY_WS=<WS> sandbox-exec -p "$SB" $PY -B -m pytest -p no:cacheprovider -q --rootdir $V $V/test_verify_probes.py
# the proposed mutants: a scratch source root SRC = symlinks to every WS top-level entry except scripts/ and .git,
# SRC/scripts = symlinks to WS/scripts/* except scale78b (a copy); then
cp $V/proposed_mutation_spec.json SRC/scripts/scale78b/tests/oext/mutation_spec_oext_78b.json
cp $V/test_zz_verify_probes_incopy.py SRC/scripts/scale78b/tests/oext/test_zz_verify_probes.py
sandbox-exec -p "$SB" $PY -B <WS>/scripts/scale78b/tests/oext/run_mutants_oext_78b.py SRC <NEW_SCRATCH> <OUT>.json ALL --timeout 300
```

## 9. Commands run (all foreground unless noted; exit status)

- **Reads (exit 0):** r1-common, GXB (all four sets, re-read after its change at 15:43), plan-ab §0, §1 item 5, §2 Track O and §5, DES E1-E5 and F2, DESO item 9, DESO2 items 24 (c) and 37, Part 2 §1.13-§1.14 and §4.2-§4.5, AM1's headings, r1-o.md. Also the WS sources `oext_78b.py`, the maker, the copy, `oext_unit.py`, `oext_eval.py`, `overrefusal_checks.py`, `limits_common.py`, `oext_unit_y.py`, RK, PACK and SR78 `SCORER_PINS`, and all of Track O's tests, fixtures, spec and runner.
- **Hashes:** `shasum` of the 26 files (all equal r1-o.md); 10 key 1B files against `git show 3481d85:` (equal); `git hash-object` over 455 tracked blobs (0 differ). Exit 0.
- **Settings and records:** `keys.py` and `diffkeys.py` (settings keys, hashes and text lengths); `g1_keys.py` (keys and hashes of the committed G1 record); the unit-pin match script; the C3 recipe hashes; manifest count fields. Exit 0.
- **Builder's commands:** the scale78b suite (274 passed, 57 skipped); `make_oext_settings_78b.py --check` (exit 0); `oext_78b.py check` (exit 0); `--oext-78b llama31-8b` in WS (exit 0).
- **Rebuild and simulation:** `rebuild_lean.py` (equal); `cascade.py` (in memory).
- **Verifier probes against WS:** a first run failed 1 test because of a flaw in my own probe (two fixture families had byte-equal W1-18 settings). After the fix, 14 passed, exit 0.
- **Builder's mutation shards:** shard 1 in the foreground (102 s, exit 0). Shards 2-4 were one command that the tool moved to the background after 180 s. I worked on and read its output file after it ended, and waited on no notification; exit 0.
- **Proposed-mutant runs:** run a (exit 1: 8 survived); run b (moved to the background after 180 s and read after it ended; exit 1: 7 killed, 2 survived); run c (exit 0: 1 killed). Also the copy-suite runs: 85, then 86 passed; earlier, 3 probe failures that I traced to O5 and to a setup flaw in my probe. Also the leak probe, the module-origin probe and `golden_off.py` (13 of 13 killed).
- **Fill simulation in a scratch copy:** the maker (exit 0) and the oext tests (4 failed, as expected for O6).
- **`-X importtime`:** 3 runs, exit 0.
- **Cleanup:** I deleted every scratch source root and runner mirror (`src2`, `src3`, `src4`, `mut-v*`, `vmut-*` folders) after its run, and kept the files listed below.

**Evidence** (`R/r1-o-verify-scratch/`):

- Run reports: `mut-v{1..4}.json`, `vmut-{a,b,c}.json`.
- Proposed mutants and probes: `proposed_mutation_spec.json`, `test_verify_probes.py`, `test_zz_verify_probes_incopy.py`, `make_vspec.py`.
- Scripts: `cascade.py`, `golden_off.py`, `rebuild_lean.py`, `keys.py`, `diffkeys.py`, `g1_keys.py`.
- Outputs: `wrapper-check.json`, `form-llama-ws.json`, `form-llama-after-olmo-theta0-fill.json` (its wrapper line is wrong by O11), `lstree.txt`.

## 10. Acceptance criteria (the brief's items)

| Item | Result | Evidence |
|---|---|---|
| 1 No label lie; globals restored on every exit path; no leak across two calls | passed | §1 (M probes; R cites) |
| 2 Copy = 1B + listed substitutions; outputs equal; 1B files unchanged | passed | §2 (M) |
| 3 Settings per family; `--check`; index pin; one family's fill reaches only its files | passed at the settings level; **failed** at the form level | §3; O1 |
| 4 Branch-128 flags; wrong-family, stale and other-branch records | passed (refused on the true path, on the pod only) | §4; O7 |
| 5 One check per family, its own settings and record; the binding passes only through the true path | passed | §5 (M) |
| 6 Suite and mutants re-run; weak spots; runner validity | suite and 41/41 reproduced; 8 surviving proposed mutants; runner valid | §6; O2-O6 |
| 7 P2-P8 classified | done | §7 |
| A real 7-8B run of any command | not tested (no pod) | — |
