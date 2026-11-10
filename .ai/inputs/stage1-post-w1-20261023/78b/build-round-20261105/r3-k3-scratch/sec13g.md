## 13g and the fix rulings (started 2026-11-09 14:51 UTC; updated UPDATED)

The lead's message (rulings set 22, R-68 to R-71, and set 21's R-59, R-60, R-65, R-66): in order 13g, R-69, R-70, R-71,
then R-59, R-60, R-65, R-66. All done (status below). The verifier's frozen copy B/ws-k3v is not touched.

| Ruling | What is built | Where (R, WS; PT = plan_tool.py) | Tests (test_runner_ab_78b.py unless named) |
|---|---|---|---|
| R-68 (13g) | init-block B with `"reference_set": "six_seed"` or `"three_seed"` in the jobs file plans three launches after the judge launches, one job per pod: refs-cert (`b10_certify` per seed, its `cert_source` from R-35's table), refs-eval (`ref_eval` with SP and λ points, `safe_lora` default and certify), refs-train (`ref_train` under recipe G at the seeds not reused, OLMo-2-7B's 1102-1103 skipped (LS-23); `ref_train_bqi` on engine Y at every seed). Their need lines and need are part of block B's need. `plan_tool.py ref-inputs` writes each pending reference job's input pins from their sources (the a0 unit's COMPLETE.json; the certification's report SHA-256; REF_PREFIX_SHA256) and the trained references' configs; release derives them again, refuses a stale pin, and refuses an evaluation-only reference unless its seed's certification is recorded passed; a failed seed's evaluation-only hosts are not released and are listed in `refs_not_run` | PT:4211, :4226 (init); PT:4327-4519 (reference_set_of, ref_job, ref_launch_jobs, ref_a0_complete, ref_certification, ref_pins, ref_config, ref_inputs_command, decided_seeds, release_refs); release_hosts_ab routes a reference launch to release_refs; SR CERTIFICATION_GATES, b10_certify in B10_UNIT_KINDS (record-done reads the gate) | test_r68_init_block_b_plans_each_seeds_certification_evaluation_only_and_trained_references; test_r68_ref_pins_come_from_the_a0_sources_and_a_failed_certification_stops_the_seeds_references; test_r68_release_of_a_reference_launch_checks_the_pins_again_and_skips_a_failed_seeds_evaluations |
| R-69 | the changed-eval-file refusal is tested on the pod and in the pack | runner ref_inputs; PACK gate_eval_files | test_13_b10_certify_ref_eval_... (pod: "is not packed at its files' pins"); test_13_block_bs_pack_... (pack: "a file is not the one its unit's COMPLETE.json lists") |
| R-70 | the pod's engine hashes the packed G / B+Qi config against the pin, and the main config's hash refuses (pod and planner); the pack packs those configs from the engine tree at their pins | RUN:915-918; PT ref_config; PACK (ref_configs) | test_13_ref_train_and_ref_train_bqi_... (both kinds refuse the main config's hash); test_r68_ref_pins_... |
| R-71 | a safe_lora host downloads the base model at its pinned revision: probe.json of a block-B pack whose plan holds a safe_lora job carries the base entry (probes.base_entry: refuses while the pin is null); the pod's gated run takes `--with-base` on a Safe LoRA host; Llama's gated base is among that host's gated entries (the launch precheck and the gated step), so it comes only through the Llama token path | SR:898 host_extra_downloads; PACK:296 pack_extra_downloads; launch.py:169-190 gated_entries(host), host_gated_extra; orchestrate.py:85 gated_entries(host); host.py:395 gated_command(stamp, with_base), :405 runs_safe_lora | test_r71_a_safe_lora_host_downloads_the_base_...; test_r71_llamas_gated_base_goes_through_the_token_path_... |
| R-59 | `--guard-batch-size` from each W1-18 family's MAIN_F config's guard block (an unreadable one refuses) | RUN:766 guard_batch | test_5c_... (6 and 8 per family); test_r59_... |
| R-60 | W1-18's job carries GATE_78B's families (planner; W1_18_78B's side units must equal them); the pod refuses another list | PT:1301 w1_18_gate_families; RUN:785 | test_r60_... [B, C]; test_5c_... |
| R-65 | main()-level tests of the three call sites: the stop record read before check_keys (sc, A, B pods; not block 0), the packed O-ext bank passed to check_keys, the Y re-measure record written after every complete Y job (moved so block-0-kind jobs on Y write it too) | RUN:1631, key_refusal, RUN:1698 | test_r65_main_reads_the_stop_record_...; test_r65_main_passes_the_packed_oext_bank_...; test_r65_main_writes_the_y_remeasure_record_... |
| R-66 | the guard model is in every host's plan already (probes.download_plan); the W1-18 pack's probe.json adds every other W1-18 family's policy tokenizer (instruct repository at KIT's revision, four tokenizer files); Llama's is gated, so OLMo-2-7B's W1-18 host under [B] goes through the Llama token path (precheck and gated step); under [C] nothing is added | SR host_extra_downloads; launch / orchestrate gated_entries(host) | test_r9_k3_the_w1_18_pack_... (probe.json); test_r71_llamas_... (W1-18 host [B] and [C]) |

**Suites (M, sandboxed):** 7-8B **658 passed** (after3-78b.log; 647 before this round of work). test_planning_ab_78b.py's
W1-18 command-word test takes a test-local R-60 stand-in (one line).

**Mutants (M):** runner spec 103 -> 127 (24 K3g-m-*). Four gated mutants re-targeted to the changed host.py and
orchestrate.py (K3-m-orch-open-family-reads-token, K3-m-host-token-not-on-stdin, K3-m-host-gated-command-open,
K3-m-host-child-env-unscrubbed; same mutations). Every find text of the four specs occurs exactly once (M). Results:
MUTRESULTS

**Open points (this round)**
1. `reference_set` is a jobs-file key; absent, block B plans no reference (the earlier route, kept so the arm-only
   init stays as K2 built it). The lead names `six_seed` or `three_seed` (F1's trigger is a recorded money event).
2. The reference launches come after the two judge launches; the references' own units (JUDGED_B10_KINDS) get no
   judge launch in this plan. The judges' planning for references is not built.
3. The W1-18 pack does not itself re-check R-60 (the planner writes the gate's families into the job and the pod
   refuses another list).
4. `RECIPE_G_PATH` and `RECIPE_BQI_PATH` are new null pins, filled with their config pins by one recorded step.
5. The reference hosts are one job per pod (E kinds alone; ref_train could share a pod with up to 4: not done).
