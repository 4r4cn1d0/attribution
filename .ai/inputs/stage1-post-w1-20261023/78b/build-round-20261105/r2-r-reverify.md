# R2 Track R re-verification: the fix round for RV-1 to RV-6 and GXB R-34 to R-40

Written 2026-11-08, 23:28-23:33 UTC (`date -u` 23:28:18 and 23:31:05; started 23:11:35). Status: **done**. Target: WS = `B/ws-r`
(detached at `bfda225`), with the builder's fix round (R/r2-r.md §11; diff `R/r2-r-scratch/fix.diff`). The file hashes
equal §11.2 (M: `shasum -a 256`, all 12 listed files). I edited nothing in WS or MAIN. My files: this report and
`R/r2-r-reverify-scratch/`. Tags: M measured, R read (path:line in WS), E estimate, I inference.

## Verdict: VERIFIED_WITH_MINOR

RV-1 to RV-6 are closed. R-34 to R-37, R-38 as amended, and R-39 are closed as ruled. The suite gives 633 passed, 57
skipped. The refs spec gives 80 of 80 killed (§4). Both makers' `--check` runs are equal. Engine X is still
`472fc7f6…`. The 1B folders and every Track O file are unchanged. Three new minor defects remain. The first is a ruling
the build does not yet follow (R-40, recorded at 23:11, after the builder's run ended at 23:10). The other two are in the
new terms record.

| id | sev | file:line (WS) | defect | failure scenario | fix |
|---|---|---|---|---|---|
| RRV-1 | minor | `make_refs_settings_78b.py:81`; test `tests/refs/test_refs_78b_settings.py:159-160` | **R-40 is not followed.** R-40 says the scale points (λ 0.9, 0.75, 0.5) stay the same under the 3-seed fallback, which changes the seeds only. The fallback still writes planned {0.75, 0.5} and curve {1, 0.75, 0.5, 0}, and the consistency test holds those values. | If the fallback fires, every B10 file states a scale plan that R-40 overrules. B10 enforces only `allowed`, which still holds 0.9, so no run is blocked (R: `eval_adapter.py:316-326`, `:632-633`). The kit's `REF_EVAL_SCALES` is 0.9/0.75/0.5 in every case. | Fallback planned [0.9, 0.75, 0.5] and curve [1, 0.9, 0.75, 0.5, 0], or one shared value for both sets. Update the test, and add a mutant. Part 2 §3.1's "{1, 0.75, 0.5, 0}" and "λ 6" (P2:519, :521) and §3.2's fallback grid change at the next text round (the lead's step). |
| RRV-2 | minor | `refs_78b.py:376-399` (`terms_paths`, `write_terms`: `if not path.exists(): continue`) | A terms record is written beside an output that this command did not write. The rule tests whether the output exists, not whether B10 wrote it. The docstring (`:51-54`) and §11.1 say "beside each output it wrote … never written when B10 wrote nothing". | M (probe A): `regenerate --out D`, where D already holds an older file. B10 refuses with exit 2 and writes nothing, yet the wrapper writes `D.refs78b-terms.json` with command regenerate, exit 2 and output D. A reader takes D for that command's output. | In `terms_paths`, note which outputs exist before the call, and write records only for outputs that are new after it. Add a test and a mutant. |
| RRV-3 | minor | `refs_78b.py:130-131` (`TERMS["lambda = 0"]`: "no lambda = 0 B10 unit runs at 7-8B"); `check_not_run` (`:302-313`) | The wrapper still runs λ = 0. `evaluate --mode scale --lambda 0` exits 0 (M: probe B; `allowed` holds 0.0), and so would `run --evaluations scale:0` (I). The terms record written beside that output says no λ = 0 unit runs. | A false sentence in the record beside a λ = 0 output. Under R-34, θ0's `o_only` O is the curve's λ = 0 end, so a λ = 0 B10 unit is a reference that Part 2 does not count (P2 §3.1, λ 18 = 3 × 6). | Either refuse λ = 0 by name (`evaluate --lambda 0`, `run` with `scale:0`) as R-34's spirit asks, or reword the term. My recommendation is to refuse. Add a test and a mutant. |

## 1. R-38 as amended: does any 1B text reach a 7-8B record?

- **B11 (`safe_lora.py`): confirmed.** Every prose text in its records comes from the settings: `rule.v_prime` and
  `rule.measure` (R: `safe_lora.py:817-820`), each point's `status` (`:673`), and the outcomes (`:746-749`). The
  record's own literals name no 1B parameter: `rule.v` (`:819`), `rules.no_stop_rule` (`:706-707`), the timing `clock`.
  The "K = 39", "16 blocks", "OLMo-2-0425" and "seed 1101" texts are all in docstrings (`:8-48`, `:728`). The argparse
  description is a fixed literal (`:868-869`). M: the builder's marker test passes. M, my probe C: I put the **derived**
  Llama-1105 B11 prose into the tiny fixture and ran check, vcheck, transform default and transform certify through the
  wrapper. 12 output files plus stdout contain no "K = 39", "Gate A", "K = 24", "12 of 112" or the 1B θ0 role text, and
  they do contain "K = 78 of 224". The derived files keep "39 of 112" only as "1B's share (39 of 112 = 34.8%)", which
  is true (M: scan of all 24 files).
- **B10 (`eval_adapter.py`) records: confirmed; its stdout and stderr: the ruled limit.** The only settings texts B10
  copies into a record are the compare report's `rule` (= `certification.gate`) and `failure_action` (R:
  `eval_adapter.py:1573`). Both are now 7-8B texts, or contain no 1B term (M: scan). M, my probe D: a gated
  `run … --evaluations certify` with the derived Llama-1105 B10 prose writes 37 files, counting the compare report and
  stdout but not the terms records, and none holds a 1B term. B10's **own code** still prints "Gate A" in its run
  summary on a mismatch (`stopped`, R: `:1744`) and in refusal messages (`:423`, `:1175`, `:1487`, `:1498`, `:1630`).
  That is R-38's stated limit, covered by the terms record. So the claim holds for records; for B10's stdout and stderr
  it holds as the limit, not as an absence.
- **The terms record.** It is written beside each output: `--out`, or run's `--regen-out` and `--eval-root`. It is a
  sibling and never inside the output (R: `refs_78b.py:376-399`; M: the builder's tests). An existing record refuses
  before the call. It names its writer and B10 by SHA-256, plus the settings and index SHA-256. Its term texts are
  true, except RRV-3's. It is written beside a pre-existing output (RRV-2). Note (I): with nested paths such as
  `--regen-out E/regen --eval-root E`, regen's record would land inside E. The 1B kit's layout uses siblings
  (`job-I/regen`, `job-I/evals`), so this does not arise there.

## 2. RV-1 to RV-6 and R-34 to R-40, as ruled

| item | state | evidence |
|---|---|---|
| RV-1 / R-37 | closed | `conditional` K = 0, with a status saying it is not run. The wrapper refuses every `--point` except default and certify, by name and in both flag forms, `k12` included (`refs_78b.py:118`, `:309-313`; M: tests; mutant F-w-point killed). My extra mutant RRV-w-sl-points is killed. |
| RV-2 | closed | All 24 B10 and B11 files record `labels_sha256` = `260389f3…`, the current registry (M). |
| RV-3 | closed, with RRV-3 | The rewritten prose is §1. The θ0 role now says it is not compared (R-34). |
| RV-4 | closed | `_set` refuses an absent parent or field with exit 2 (`refs_78b.py:423-433`; M: tests; mutant F-w-absent killed). |
| RV-5 | closed | The maker removes this maker's per-seed files of seeds outside the set, and `--check` reports them (`make_refs_settings_78b.py:506-553`). The in-place fallback test passes (M). The regex cannot match Track O's names (R: `:506`). |
| RV-6 | closed | T1-T7 are in the suite, and the 7 mutants are in the spec and killed. I accept RV-x-except-any as equivalent (I, the builder's cites). |
| R-34 | closed, with RRV-3 | `check --untuned` and `compare --against untuned` are refused by name, in both flag forms (`refs_78b.py:302-308`; M: tests). My extra mutant RRV-w-against-form is killed. |
| R-35 | closed | `SOURCES` (`make_refs_settings_78b.py:92-95`) is the ruled table: Llama 1103 = `block0_a0` (N's a0-1103), OLMo 1103 = `side_unit`, 1104 block A, 1105-1107 block B. The test holds an independent copy (`test_refs_78b_settings.py:30`). The prefills (OLMo 1102 `43e8412d…`, 1103 `4b5bd06d…`; Llama 1102 `b0c99f7b…`) equal RK KIT, path and COMPLETE.json (M: consistency test). My extra mutant RRV-m-sources-1103 is killed. |
| R-36 | closed | 64-hex values only. The first 16 hex must equal P1 §2.1's (`make_refs_settings_78b.py:98-99`, `:270-273`), and those prefixes match P1:91's text (R). Tests cover the e1 and q refusals (`test_refs_78b_settings.py:369-371`). The spec has no mutant for this check; my extra RRV-m-r36-prefix is killed. |
| R-38 (amended) | closed | §1. |
| R-39 | closed | `test_ss_family_codec.py:165` reads `59 + 10`. M: 16 passed (95 with `test_ss_family_recipes.py`). |
| R-40 | **open** | RRV-1. |

## 3. No regression (M)

- `git diff --stat bfda225 -- scripts/stage1 scripts/stage1_s1 runkit` is empty. The 1B scripts hash to `CODE`.
- Track O: `oext_78b.py` is `05589f94…` and `make_oext_settings_78b.py` is `0e8bd8f9…`, the R2 values.
  `test_oext_78b_r2.py` is `33b75cdf…`. The diff stat against `bfda225` is the same 5 files and +175/−41 as at R2. No
  tracked settings file changed. `make_oext_settings_78b.py --check` gives 18 files equal, and
  `make_refs_settings_78b.py --check` gives 36 files equal.
- `refs_78b.py check` on all 12 indexes exits 0. The eval_adapter and safe_lora files print waits on the REF_UNIT and
  HUB_READ pins; oext_eval prints valid (`R/r2-r-reverify-scratch/check-*.json`).
- Engine X, re-computed without importing the engine (the R2 verifier's script): 29 files, `472fc7f6…`, with the new
  config and the count change present.
- Parity: the parity tests pass. They set the wrapper's terms records aside and then compare as before
  (`test_refs_78b_eval_adapter.py:50-52`). Globals are restored (tests). No label lie: every path label is still a
  loaded file's, and the terms record names its own writer.

## 4. Tests and mutants (M; all under `sandbox-exec -p "$SB"`)

- **Suite:** `scripts/scale78b/tests` gives **633 passed, 57 skipped** in 139 s, exit 0 (23:14-23:17 UTC).
- **Engine:** `test_ss_family_codec.py` gives **16 passed**. With `test_ss_family_recipes.py` it gives 95 passed.
- **Refs spec** (`43ba3ff2…`, 80 mutants): 6 shards of at most 14, three at a time. Each baseline was 90 passed, 1
  skipped. **80 of 80 killed**, 0 survived, 0 invalid, 0 ERROR lines (14 + 14 + 14 + 14 + 14 + 10). Each shard took 4.3-5.5 min (23:18-23:29 UTC). All shard result files are `mut-refs-{1..6}.json`.
- **My extras** (`rrv_extra_spec.json`, 5 mutants on the fixed code): **5 of 5 killed** (RRV-m-r36-prefix, RRV-m-sources-1103, RRV-w-sl-points, RRV-w-terms-suffix-inside, RRV-w-against-form). Baseline 90 passed, 1 skipped; 23:29-23:31 UTC; `mut-rrv-extra.json`.
- **Probes** (`test_zz_rrv_probes.py`, all pass on the builder's code): A (RRV-2), B (RRV-3), C and D (§1).

## 5. Notes for the lead

- The builder's open point on R-38's copy route is settled by the fifteenth set; the evidence in §1 agrees with it.
- K3 must bring back the terms records, as the fifteenth set says. Nothing pins them, and B10's records do not list them.
- The R-35 fingerprints still wait on the lead's hash-only reads. Before each certification, run
  `refs_78b.py eval_adapter … check --reference S=<COMPLETE.json>`.

## Commands run (exit status)

Reads, hashes and diffs: exit 0. Suite: exit 0. Engine tests: exit 0. Both `--check` runs: exit 0. `refs_78b.py check`
× 12: exit 0. Probes: exit 0 (4 passed). Refs shards 1-6: exit 0 each. Extras: exit 0. Mirrors and pytest temp
folders deleted afterwards. The JSON results and probe files are kept.
