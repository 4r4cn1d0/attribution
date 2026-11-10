## Item 13, R-63 and R-67 (continuation; started 2026-11-09 14:24 UTC, updated 14:5x UTC)

The lead's message: continue with item 13 and rulings R-63 (the Y pack also in block B's copy for ref_train_bqi) and
R-67 (`record-y-measured`). R-59, R-60, R-65, R-66 are not done here (fix round). The verifier's frozen copy B/ws-k3v
(as of 14:23) is not touched. The earlier sections above describe the 14:20 state.

**Status: partial.** Item 13's pod side (runner), pack side and pins are built and tested; **13g, block B's planning of
the reference jobs (init-block B gaining them, each waiting for its seed's a0 unit and its certification), is not
built.** R-63 and R-67 are done.

| Sub-item | State | Where (R, WS) | Tests (test_runner_ab_78b.py) |
|---|---|---|---|
| 13a commands through refs_78b.py | done | RUN:881 ref_commands (b10_certify, ref_eval, safe_lora in the 1B forms RUN1B:467-487, :553), RUN:870 ref_lead, RUN:974 resolve (@sha256, @snapshot) | test_13_b10_certify_ref_eval_and_safe_lora_run_through_refs_78b_in_the_1b_forms |
| 13b b10_certify per seed; a failed certification stops the evaluation-only references | done (pod side) | RK:1084 E cap; `b10_certify` in E_KINDS and BANK500_KINDS; RUN:989 certification_gate (port), RUN:1008 run_ref_job, RUN:859 certified (only the report's verdict is read) | test_13_run_ref_job_records_b10s_gate_its_units_and_the_terms_records; the refusal in the first test |
| 13c ref_train under RECIPE_G, ref_train_bqi on Y | done (runner) | ref_commands' REF_TRAIN_KINDS branch: calibrate under the job's pinned config, then the O-ext unit pass (the Y index for B+Qi) | test_13_ref_train_and_ref_train_bqi_calibrate_under_their_pinned_configs_then_the_unit_pass |
| 13d the safety-prompt file by path and SHA-256 | done | RK REF_PREFIX_SHA256 `0fcc6beb…` (R: the B10 settings' prefix.text_sha256); runner ref_inputs; PACK:471 ref_input_pins | first test; test_13_block_bs_pack_takes_the_reference_inputs... |
| 13e REFS_78B[F][S] in Track R's printed form | done | RK:2657-2720 (REFERENCE_SEEDS, REFS_78B null, refs_form_problem, refs_or_refuse, ref_cert_source = R-35's table) | test_13_refs_78b_pins_take_track_rs_form_and_r35s_table_names_each_seeds_a0_unit |
| 13f the terms records back with the outputs | done | run_ref_job hashes every file under job-I and lists the `*.refs78b-terms.json` files as `terms_records`; the light pull takes `job-*` | run_ref_job test |
| 13g block B's plan gains the reference jobs | **not done** | — | — |
| pack for block B | done | PACK:460 B's input pins from plan.json; PACK:491 gate_eval_files (each eval file at its unit's COMPLETE.json listing); PACK:946 each filled seed's REFS files | test_13_block_bs_pack_... |
| R-63 | done | PACK:887 (Y pack in the sc and B copies); block B's Y pack checks and packs OEXT_78B_Y[F] | test_r63_engine_ys_pack_is_allowed_in_block_bs_copy_and_refused_in_block_as [A, B] |
| R-67 | done | PT:4653 record_y_measured (CLI `record-y-measured HOST... --recorded-by --out`); RK:2731 y_measured_problem, :2756 y_measured_or_refuse; new null pin Y_MEASURED_RECORD; engine_allowed needs Y_MEASURED and the pin | test_r67_record_y_measured_turns_the_y_pods_records_into_the_pinned_record_and_refuses_off_records; test_rules_78b.py test_07c |

**Suites (M, sandboxed unless noted):** 7-8B **647 passed** (after2-78b.log; +8 tests in this continuation); stage-1
kit 762 passed (unsandboxed). scripts/ unchanged (`git status scripts` empty), so scale78b and the engine family tests
were not re-run. No `__pycache__` in WS.

**Mutants (M; baselines exit 0):** runner spec 77 -> 103 (26 K3c-m-*); shard mr6 (the 26 plus the 3 re-targeted
K3-m-ab-no-oext-step, K3-m-ab-oext-on-q, K3-m-y-oext-not-checked): **29 killed**. Rules spec 251 -> 253
(K3c-m-y-measured-no-record, K3c-m-b10-not-bank500); 4 older ones re-targeted to the new engine_allowed line
(K1-m-engine-y-measured-any, K1-m-engine-y-e-kinds-off, K1-m-engine-y-null-passes, K4-m-x-only-after-y; same
mutations), and one new code line re-worded so KF-m-branch-texts' find text stays unique; full rules run mq4:
RULES_RESULT. The scorer spec's mutants on the runner and pack (every find text still once) and the gated spec were not
re-run after this continuation: the lead's full runs cover them. Every find text of the four specs occurs exactly once
(M).

**Files (SHA-256, M):**

| File (WS) | SHA-256 |
|---|---|
HASHES

**Open points (this continuation)**
1. **13g's form is the lead's.** Block B's init must plan, per reference seed, `b10_certify` after the seed's a0 unit
   (R-35: side, N, block A or block B), then `ref_eval` and `safe_lora` after a passed certification, each job with
   its input pins (gate_a_complete, gate_a_eval, certification_report, prefix_file) in plan.json. The pack and the
   runner read those pins from plan.json; until the planner writes them, every reference refuses ("has no pin in
   plan.json"). A release-time check that the seed's certification was recorded passed is also unbuilt.
2. `gate_a_eval:S` is pinned by the a0 unit's COMPLETE.json SHA-256 (the same pin as gate_a_complete:S); the pack checks
   each eval file against that COMPLETE.json's "files" listing. Confirm the form.
3. ref_train and ref_train_bqi carry their config as job keys `recipe_g` / `recipe_bqi` {path, config_sha256} (the
   recipe_s78 pattern); the pod's preflight still runs the main config (`preflight_recipe`), as for the S_78 kinds.
4. `Y_MEASURED_RECORD` is a new null pin; measured kinds on Y need it and `Y_MEASURED` True.
5. safe_lora's `@snapshot:base` needs the base model in the pod's download receipt (the base revisions are null; P8).
