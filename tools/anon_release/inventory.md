# Inventory: allowlist for the main study's anonymous code release (revision 2, after the lead's decisions)

Source: the main checkout, branch `stageb-costs-and-recovery-safeguards-20261003`, read from git at
`d5f3993ce07ad4f0a562055e5cbd6c7deb431398`. The machine-readable form is `anon_export_config.json` (`allow`, `deny`,
`repin`, `accepted`). An allow glob is filtered by the deny globs; an exact path wins over them and must exist.

Scope rule (lead decision 6): code that the stage-1 code imports or runs (Python imports, files loaded by path, the
kit's pack lists), the tests of that code with the modules those tests import, the frozen texts and their verification
documents. Configs (decision 3): only those that stage-1 code, the frozen readers, the preflight scripts or the frozen
texts name, plus engine X's identity record.

## Allowlist (one reason per entry)

| Entry | Reason |
|---|---|
| `experiments/safety_selection/*.py`, `README.md` | The engine (engine X; `pack_setup.engine_files` packs the package; stage-1 code imports it). |
| `experiments/safety_selection/tests/**` minus 8 | Engine tests. Denied (tests of excluded kits, scripts or configs): `test_ss_kt_runkit.py`, `test_ss_baseline_reuse.py`, `test_ss_family_recipes.py`, `test_ss_family_reading.py`, `test_ss_gateb_anchor_job.py`, `test_ss_gateb_runkit.py`, `test_ss_gateb_certificate.py`, `test_ss_probe_runkit.py`. |
| 15 configs | Named by stage-1 code or readers or frozen texts: recipes B (`…r64-b-mb4-20261008`), S (`…-gateb-20261008`), G (`…r64-g-mb4-20261008`), `study-kt-instruct-r64-mb4-20261006`, data `study-kt-data-dolly-olmo2`, `study-v3-data-inj05`, `headroom-rewrite-pc2-20261005`, evaluation-equivalence `gateb` and `round6`, `family-probe-reading` and `-amended`, `killtest-stage0-reading`; plus the identity records of the three engines the frozen texts and readers name: `engine-identity-472fc7f6.json` (engine X = `stage1_rules.ENGINES["X"]`), `-55253874`, `-e49a978c`. 91 configs dropped. |
| `experiments/minimal_safety/**` | Imported by the engine; packed whole by `pack_setup`; holds `requirements.lock`. |
| `experiments/durability/*.py` minus `stage_b.py`, `README.md`, `pod_timer/**`, `tests/**` minus 2 | `host.py` runs `python -m experiments.durability pod-timer-settings`; `__main__` imports the modules; `shutdown_timer.py` and `launcher.py` load `pod_timer/` by path. `watchdog/` is kept as a test-time dependency (`test_dur_pod_timer.py`, `test_dur_watchdog.py` load it); `stage_b.py` and the two stage-B tests (they import `safety_decision_policy`) are out. |
| `runkit/stage1-olmo/**` | The stage-1 kit and its tests. |
| `scripts/stage1/**`, `scripts/stage1_s1/**` | Stage-1 code, settings, tests, mutation specs (all 134 MAN1 entries present match MAN1). |
| `scripts/gate_b_mac_judges/`: 7 modules, 11 `pod/` files, 2 READMEs | The stage-1 judge route: `judge_units_stage1.py` imports `units.py`, `write_files.py`, loads `pod/judge_pod.py` and `pod/bundle.py`; their imports and `bundle.TOOL_FILES`/`POD_FILES`/`GRANITE_*` pack lists. |
| `scripts/gate_b_mac_judges/`: `import_cache.py`, `parity_gate_a.py`, `pod/parity.py`, `watchdog.py`, `run_harmbench.sh`, `run_granite.sh`, 5 test files | Test-time only: `runkit/stage1-olmo/tests/test_stage1_judge_route.py` imports `test_judge_pod.py`, which imports `test_gate_b_judges.py`, which imports or reads these. Dropped: `pod/granite_summary.py` and its test, `test_port_fidelity.py`, `pod/PARITY.md` (decision 1). |
| `scripts/family_probe_reading.py`, `killtest_stage0_reading.py`, `gate_b_reading.py` | Frozen readers loaded by path (limits settings, `gateb_mac.py`). |
| `scripts/gate_c_classifier.py`, `gate_c_representation.py` | Imported by the MAN1 tests `test_score_classifier.py` and `test_representation_pass.py`. |
| `scripts/cuda_preflight_{family,killtest,headroom,headroom_v3}.py` | Packed onto every pod (`PREFLIGHT_SCRIPTS`); `preflight_stage1.py` runs the family preflight. |
| Gate B/C pre-registration rev 5; stage-1 rev 4; W1 record | Frozen texts (rev 5 byte-identical; rev 4 and the W1 record equal to the OSF anonymized copies). |
| `.ai/inputs/stage1-commitments-20261016/{MANIFEST.json, predictions/predictions.json, predictions/predictions-timing.json}` | MAN1 and the predictions, byte-identical; exact-path exceptions to the `.ai/**` deny; `predictions.json` has a named size exception. |
| `research/experiments/2026-10-23-osf-deposit-package/{README.md, REDACTIONS.md, HASHES.json}` | Verification documents for the frozen files. |

Totals: 523 files plus the generated `MANIFEST.json` and `EXPORT-README.md`.

## Kept out

Gate B kit (`runkit/gate-b-olmo`) and the other kits: stage-1 code does not import them (five stage-1 tests compare
files with the Gate B kit and fail without it). `experiments/safety_decision_policy`: imported only by the two dropped
durability stage-B tests. `pilot/`, other `scripts/*.py`, `.ai/` except the three exact paths, `research/` except the
frozen texts and the OSF documents, `writing/`, `templates/`, `tmp/`, `backups/`, PDFs.
`scripts/gate_b_mac_judges/pod/granite-known-answers.json` stays out (judge calibration set holding answer text);
`granite_pod.py` reads it on the pod.

## Referenced at run time but not exported

Engine Y (`tmp/engine-y-34bfd288`; recipe `…bq-mb4-20261022` is not at HEAD), other `tmp/` inputs (anchor bank,
`process_receipt.py`, base-pins record, prepared data), sealed `.ai/inputs` records, Gate B's sealed MANIFEST,
`gate_b_verdict_p5.json`, and the research drafts that settings cite by SHA-256. The export supports reading, hash
checks and the CPU tests that need no private inputs; it is not a complete re-run kit.
