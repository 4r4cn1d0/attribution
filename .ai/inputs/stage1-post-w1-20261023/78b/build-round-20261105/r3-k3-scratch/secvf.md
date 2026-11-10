
## Verifier fixes (K3V-1 to K3V-4; GXB R-75 to R-78; started 2026-11-09 15:44 UTC)

The verifier's report (B/reports/r3-k3-verify.md, NOT_VERIFIED) and the lead's set 24. Done in ws-k3 after 13g and the
set 21-22 rulings. The set-21/22 mutation run was stopped after its runner and rules shards (both complete, see the
13g section) and re-run in full after these fixes, so every number below is on the fixed code.

| Ruling | Fix | Where (R, WS) | Tests (test_runner_ab_78b.py) |
|---|---|---|---|
| R-75 (K3V-1, major) | `orchestrate.py check-plan` (and after-create's first step, which calls it) builds each job's commands inside `runner.mac_build(<checkout>)`: there packed_file checks the sealed-files.json listing only; the branch record and W1-18's guard configs are read from the checkout at their pins; c0's expected fingerprint is the 1B placeholder `@fingerprint:source_complete:R:1101`; the certification verdict, the eval-folder hashes and the trained references' config hash are not read. On the pod (MAC_ROOT None) every one of them is hashed or read as the command is built, so a missing or wrong file refuses there before any step | RUN:652-676 (MAC_ROOT, mac_build, packed_file), branch_bytes, guard_batch, ref_inputs, certified (RUN:903), the c0 branch, ref_commands; orchestrate.py:256 | test_r75_check_plan_passes_on_the_mac_for_a_block_a_or_b_arm_pod_and_hashes_nothing_there [A, B] (and a wrong listing refuses on the Mac); test_r75_..._the_scorer_blocks_o_ext_pods_and_w1_18 (o_only, o_only_with_regenerate, c0, W1-18; c0's placeholder; pod-side refusals of a changed source unit and a changed W1 index); test_r75_..._the_reference_kinds (b10_certify, ref_eval, safe_lora, ref_train; pod-side refusal of a failed report). Each check_plan test asserts HERE/hosts/HOST holds no file |
| R-76 (K3V-2) | `source_unit:<arm>:<seed>` is packed in the 1B form: its COMPLETE.json at the pin, every other file only at the SHA-256 its COMPLETE.json "files" lists (status.json and COMPLETE.json are the engine's own unlisted markers), macOS metadata skipped by name, any other file refused on the Mac | PACK:513 source_unit_files, :613 | test_r76_the_source_unit_is_packed_by_its_complete_json_listing_and_an_unlisted_file_refuses |
| R-77 (K3V-3) | behavioural tests: a block-B arm job's commands (V-01b); a block-B pack through pack.main with the O-ext files, inputs, branch record and edits (V-08), and its missing-inputs refusal (V-14); a Y pack refused in blocks 0 and A with ENGINE_Y filled (V-12); the pack's Mac check under Branch full from a failing record takes the record (V-04) | — | test_r77_v01b_...; test_r77_v08_v14_...; test_r77_v12_... [0, A]; test_r6_... (the R-47 case added) |
| R-78 (K3V-4) | (a) a test of the @unit guard (V-02); (b) the README's engine-Y row says which jobs write y-remeasure.json (every complete job on a Y pod; measured kinds only after Y_MEASURED and Y_MEASURED_RECORD; matches RUN's main, which writes it for every complete Y job since the set-21 change); (c) oext_checks reads the branch record through branch_file, which checks the pin and the record first, so a missing record refuses cleanly | PACK:691; README engine-Y row | test_r78_v02_...; test_r6_... (a missing pinned record refuses with SystemExit) |

The verifier's mutant spec, run with its own runner (the whole 7-8B suite per mutant) from a copy in
R/r3-k3-scratch/vprobe/: the runner file is the verifier's byte for byte except its SPEC path (M: diff, the SPEC line
only); in the spec copy only V-12's find text is re-targeted to R-63's line (same mutation, `if False:`), because
R-63 changed that line. The eight survivors (V-01b, V-02, V-04, V-06, V-07, V-08, V-12, V-14) are also in the kit's
runner spec as K3V-V-*.

**Suites (M, sandboxed):** 7-8B **668 passed** (after4-78b.log).

**Mutants (M):** VFRESULTS

**Open points (verifier fixes)**
1. check_plan on the Mac passes a job whose pod files are absent by design; the pod's build is then the first hash
   check of those files (before any step). The launch path is unchanged otherwise.
2. A packed source_unit carries every listed file of the unit (states included, if listed): the lead names the folder
   to pack (the verifier's open point).
3. The W1-18 guard configs are read from the checkout on the Mac and from the packed engine tree on the pod.
