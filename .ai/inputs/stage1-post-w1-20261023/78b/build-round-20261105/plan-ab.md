# Plan: the 7-8B kit's block A and B build (read-only scout for GI XI)

Written 2026-11-08, clock read with `date -u` at 13:50 UTC (start) and 14:02 UTC (before this text); last cite fixes at 14:09 UTC. Status: DONE. Read-only on
MAIN (`/Users/spiderishi/Coding/attribution`, branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD `c57e456`,
M: `git rev-parse`). Written only here and in `plan-ab-scratch/` (one script, `gen_guard_check.py`). No pod, spend,
network, install, download, agent or message. No git state changed (M: `git status --porcelain` lists only files
that were already modified or untracked before this run; none is mine). No forbidden folder, selector, hidden,
judge, answer, generation, sample or prompt-text file was opened. From settings and manifests I printed keys,
short hashes, counts and top-folder names only.

Tags: **M** measured (the command is named), **R** read (path:line), **E** estimate (basis given), **I** inference.

Short names as Part 2 (P2): RK `runkit/stage1-78b/rules_78b.py`, SR78 `…/stage1_rules.py`, PT78 `…/plan_tool.py`,
RUN78 `…/setup/job_runner_stage1.py`, PACK `…/pack_setup.py`; RUN1B `runkit/stage1-olmo/setup/job_runner_stage1.py`,
SR1B `runkit/stage1-olmo/stage1_rules.py`; OXU/OXE `scripts/stage1_s1/settings/oext_unit.json` / `oext_eval.json`;
DES, DESO, DESO2, DES3 (DES's third set, 14:45 UTC), AM1 (the pending amendment file for §1, GI XI ruling G1).

---

## 0. The six findings that change the plan

1. **The build is larger than SCOUT's 20-30 builder h.** My total is about 70-100 builder h (E; §6), because four
   pre-block-A items are not in Part 2 §15's list: engine Y's pack (PACK takes engine "X" only, R: PACK:508), the
   reference settings at 7-8B (eval_adapter, safe_lora and overlap settings pin 1B values, M below), a 7-8B plan-code
   record (PT78's plan route reads Gate B's verdict through `rules.GATEB_VERDICT`, which SR78 does not define; R:
   PT78:582-591; M: `grep GATEB_VERDICT stage1_rules.py`, no hit), and the B10 certification question (item X2).
2. **The frozen `oext_eval.py` binds every O-ext run to W1-18's 1B settings file.** `check_w1_18_binding` requires
   W1-18's settings at the module's `SETTINGS_PATH` to hash to its literal `SETTINGS_SHA256` and to
   `cap.w1_18.settings_sha256` (R: `scripts/stage1_s1/oext_eval.py:214-236`, called by `load_pinned_settings`, :246-251),
   and the W1-18 record's `provenance.settings_sha256` must equal that pin (R: :374-375). A 7-8B W1-18 run lists other
   units, so it needs other settings. Under Branch 128 the 7-8B record therefore passes the frozen `oext_eval` only if
   the 7-8B wrapper patches W1-18's two module globals in-process (the `scorers_78b.py` pattern, R:
   `scripts/scale78b/scorers_78b.py:17-25`) or the pack swaps the files at the 1B paths (the engine-Y precedent, R:
   `scripts/stage1_s1/oext_unit_y.py:1-10`). Both keep `oext_eval.py` unchanged. `oext_eval.py:218-219` says W1-18's
   settings "are never re-pinned". Open item O3: is a per-family W1-18 settings file, made by a recorded step,
   inside that rule?
3. **The O-ext wrapper is feasible by the scorer-layer pattern, but two seams need care.** `oext_unit.load_pinned_settings`
   binds its default path at definition time (R: `oext_unit.py:209`), and the settings validator requires
   `oext.settings.path == "scripts/stage1_s1/settings/oext_eval.json"` (R: :146). `lean_eval_job.py` loads O-ext
   settings by the literal pin (R: `lean_eval_job.py:849`). `main()` takes `settings=` and `oext_settings=` keyword
   objects (R: `oext_unit.py:685-693`), but its docstring says "ENGINEERING FIXTURES in tests only". Track O must pick
   the route by a decisive check (§4, item 5d).
4. **MAIN_F's generation and guard blocks equal the 1B O-ext pins on both families (M, this run).** So
   `oext_unit__F.json` keeps OXU's `generation_sha256` and `guard_sha256`; the §14 item 29 check is done (§5 C3).
5. **Both families' tokenizers are on the Mac (M).** The S-list encode counts, the PHTest Llama count, the S1 re-check
   and τ_L can run at $0 on the Mac. No frozen script does the S-list or PHTest count today (M: `grep encode` in
   `scripts/scale78b/`: only `s1_olmo2_7b_check.py` and MAKER), so a small counted script is a build item (Track C).
6. **Part 2 leaves the S4_top step count open for 48-64 kept rows.** Steps = ⌈rows / 128⌉ gives 33 (4,200), 38
   (4,848) and 39 (4,896 and 4,992) (M: arithmetic, consistent with RK `STEPS`, R: RK:103). For S4_top with n kept
   rows, ⌈(4,800 + n) / 128⌉ = 38 for n ≤ 64 and 39 for n ≥ 65 (M: arithmetic). Part 2 §2.1 says the dose arms take
   39. Open item O1.

---

## 1. Item map

Format per item: **Now** (what exists), **Missing**, **Change** (files, functions, constants), **Tests** (names to
add), **Mutants**, **Pins and refusal**, **E** (builder hours, basis). "New" = a new file.

### Item 1. Block tables per plan and family (P2 §2.2, §2.3)

- **Now.** SR78 `METHOD_SEEDS = {"A": (1102, 1103, 1104)}` (R: SR78:192); `ARM_ORDER` (R: :193); `BLOCKS = ("0",
  "sc")` (R: :199); `block_runs` refuses every block but "0" (R: :502-508); `plan_code_for` gives "A" / "B9" / "H"
  (R: :493-498). RK `SEALED_SETS` has one MANIFEST per family (R: RK:182-187; `block0_r_edits` reads draws 1-3,
  R: RK:520). The 1B kit's `block_runs` (R: SR1B:363-386) is the model.
- **Missing.** Tables for block A (21 per family) and block B per plan (A 23, B9 32, H (b) 47) and the dose rows (6
  or 12). The OLMo R_d4-R_d13 come from three sources (SEAL R_d4-R_d5; stage 1's `r-draws/edits/` R_d6-R_d10; the
  OLMo folder R_d11-R_d13; R: P2 §2.3), so RK needs a per-draw source table. Method edits (A1, L1, S3, S4, doses) have
  no pin. The plan code has no 7-8B source (finding 1). No reduced table for a family whose anchor job stopped.
- **Change.** RK: `R_DRAW_SOURCES[F][d] = {path, sha256}` for d = 4-13 (hashes in P2 §2.3); `METHOD_EDITS[F][arm] =
  {path, sha256} | None` (H1 `f5b1762f…`/`9a01637e…` and S1 `904a0cf1…`/`69426993…` filled; A1, L1, S3, S4, S4_96,
  S4_192, `s4_top` null); `PLAN_ARMS_78B = {"A": six arms, "B9": (A1, H1, S1, S4), "H": (A1, H1, S1, S4)}`,
  `BLOCK_B_SEEDS = {"A": 1105-1107, "B9": 1105-1110, "H": 1105-1113}`. SR78: `block_runs(plan_code, block)` for "A"
  and "B"; `BLOCKS` adds "A", "B"; `BLOCK_KINDS["A"]`, `["B"]`. PT78: `record-plan-78b OUT.json --sha256 H` (reads
  `noise_reading.py`'s output by pin: `sigma_pool`, the code; and, for block B, `blinded_sigma.py`'s output under
  SR-2, or N alone if SR-2 is not adopted).
- **Tests** (new `tests/test_block_tables_78b.py`): `test_block_a_21_runs_each_family`, `test_block_b_counts_per_plan`
  (23, 32, 47), `test_r_draw_seed_is_1100_plus_d`, `test_r_draw_hashes_equal_part2_table`, `test_null_method_edit_refuses`,
  `test_other_family_edit_refuses`, `test_stopped_family_drops_a1_l1_s3` (block A 18 → 9 method runs, I: P2 §2.2),
  `test_plan_code_only_from_pinned_noise_reading`, `test_sr2_not_adopted_uses_n_code`.
- **Mutants.** block A without R_5 at 1105; B9 at 1105-1109; R_d6 bound from SEAL; a null method edit accepted;
  a stopped family keeps L1; plan code read from a typed value.
- **Pins and refusal.** Method edits are filled by recorded lead steps after the scorer block's Mac steps; a null pin
  refuses `init-block A` (A13's pattern). The plan record waits on N's reading.
- **E** 5-7 h (basis: the 1B `block_runs` is 24 lines; three plans, two families, three draw sources, the stop case).

### Item 2. The pod layout (P2 §2.4)

- **Now.** RK `pod_sizes` (M in P2: 21 → [4, 4, 4, 3, 3, 3]); `arm_pod` takes per-arm steps (R: RK:827); SR78 `deal`
  is N's only (R: SR78:515-520). The 1B interleaving deal (R: SR1B:1085-1100).
- **Missing / change.** Port the 1B `deal` (arm-major, seed-minor, run i to pod i mod P; one arm twice on a pod
  refuses) into SR78 for blocks A and B; keep N's `deal` for block 0.
- **Tests.** `test_deal_block_a_444333`, `test_deal_no_arm_twice_on_a_pod`, `test_mixed_33_38_39_cap_uses_own_steps`,
  `test_at_most_4_counted_per_pod`.
- **Mutants.** P = 1; seed-major order; 5 arms per pod.
- **E** 1-2 h.

### Item 3. The S4 dose arms at 39 steps (P2 §2.1, §15 item 3)

- **Now.** RK `STEPS = {"remove": 33, "add": 38, "a0": 38}` (R: RK:103); SR78 `ARM_DOSE`, `DOSE_STEPS` (R: :194-196).
- **Change.** RK `STEPS["dose"] = 39`; SR78 `ARM_DOSE["S4_96"] = ARM_DOSE["S4_192"] = "dose"`; a planning check that
  ⌈(4,800 + rows) / 128⌉ of the bound edit equals the arm's steps (refuse otherwise). `s4_top` waits on O1.
- **Tests.** `test_dose_arms_39_steps`, `test_steps_match_edit_rows`, `test_s4_top_steps_rule` (after O1).
- **Mutants.** dose 38; the rows check skipped.
- **E** 1-2 h.

### Item 4. `train_scale` and token accounting (P2 §2.1)

- **Now.** RK `train_scale_of`, `train_scale`, `upper_m_of(..., padded_tokens_per_step)` (R: RK:647-673). SR78
  `job_record` does not pass padded tokens (R: SR78:575-588, it calls `r78.job_record(fam, kind, steps, arm, seed)`).
- **Missing.** The arm's padded tokens per step from the edit's token counts at planning; the token-accounting line
  is a Mac report (`scripts/stage1/token_accounting.py`, P2 §2.1), not a kit step.
- **Change.** SR78 `job_record(..., padded_tokens_per_step=)`; PT78 reads the counts from the bound edit's record by
  hash. **Weak assumption:** that the edit files (or their text-free records) carry per-row token counts. The builder
  checks the edit format first (an add edit holds text; a removal edit holds ids); if they do not, the count comes
  from the prepared set's token fields by row id.
- **Tests.** `test_train_scale_at_least_1`, `test_train_scale_from_edit_counts`, `test_missing_counts_refuse`.
- **E** 2-3 h.

### Item 5. O-ext: the arm step, the cap term, W1-18, `OEXT_78B` and its Y variant, N's units, the two flags

- **Now.** RUN78 runs `calibrate` only for arms; "No O-ext step runs at 7-8B" (R: RUN78:46; `BLOCK0_KINDS`, :96).
  SR78 `BANK500_KINDS = frozenset()`, `BRANCHES = ()` (R: SR78:378-380). RK `OEXT_78B` null (R: RK:1159);
  `OEXT_UNIT_SCRIPT`, `C0_SCRIPT` name the 1B scripts (R: RK:1161-1162). RUN78's `o_only`, `o_only_with_regenerate`,
  `c0` commands pass neither `--w1-18-record` nor `--dev100-source` (R: RUN78:599-626). `o_only_with_regenerate`
  refuses an arm other than a0 (R: RUN78:605-607); `SC_ARM` maps it to "a0" (R: RK:1202); `sc_seeds` lists the side
  seeds only (R: RK:1207-1217); the acceptance input is `side_complete:a0:{seed}` (R: SR78:307). The 1B forms exist:
  the arm O-ext step (R: RUN1B:457-468), `oext_args` with the W1-18 record (R: RUN1B:279-283), `dev100_source`
  (R: RUN1B:272-276), the `w1_18` command (R: RUN1B:410-412). PT78 still carries the 1B branch route
  (`record_branch`, R: PT78:3805; `gate_g1`, R: PT78:821).
- **5a. The arm step** (E3). RUN78 `job_commands` for blocks A and B: `calibrate`, then the O-ext run on `@unit` e1
  (the 1B form); for `ref_train` too. Fallback E3 (b): the kit plans a separate O job per unit. Tests:
  `test_arm_job_oext_after_calibrate`, `test_a0_arm_and_ref_train_get_oext`, `test_no_oext_in_block0`,
  `test_e3_fallback_separate_o_job`.
- **5b. The cap term** (DESO item 24 (a)). RK: an O-ext term in `upper_m_of` / `e_upper_s` for arm, a0_arm,
  ref_train and the references: Branch full 3,959 s (OLMo) / 4,061 s (Llama) × 1.5 (M in P2 §4.3); Branch 128 an E
  value (P2 §4.3: about 0.3-0.45 h); replaced by a measured value by a recorded step. `check_keys` takes the O-ext
  bank as a second pin beside `BANK` (SCOUT §1.3). Tests: `test_cap_4_arms_branch_full_x15` (17.25 h / 19.25 h),
  `test_funding_need_four_pods_x15` ($167.06 / $185.56, M in P2 §4.3), `test_check_keys_oext_bank_pin`.
- **5c. The 7-8B W1-18 kind** (E2, DESO2 item 37). RK/SR78: `w1_18` kind, alone on one pod, the first O job,
  `BANK500_KINDS` and `BRANCHES = ("full", "128")` restored, `BRANCH_DEFAULT = "full"`; PT78: a per-family branch
  record (Branch 128 per family only if every unit of that family passes; P2 §4.2); "Branch full by default" when
  the pod is not built or does not finish. RUN78: the command runs the Track O wrapper once per family on the same
  pod (I: one policy codec per run; the module decodes `output_ids` "with the policy codec", R:
  `scripts/stage1/limits/overrefusal_checks.py:30-31`), so two records. E cap 2-3 h (P2 §4.2). Tests:
  `test_w1_18_alone_and_first`, `test_500_bank_job_refuses_before_branch_record`, `test_branch_never_switches`,
  `test_branch_full_default_record`, `test_c_option_olmo_units_only`.
- **5d. `OEXT_78B[F]` and its Y variant** (E4, DESO2 item 24 (c)): Track O builds the files; the kit fills nothing.
  RK `OEXT_UNIT_SCRIPT` and `C0_SCRIPT` change to the wrapper's path (plan_tool refuses a kind whose script is not in
  `OEXT_78B[F]["files"]`, R: RK:1150-1158 comment). A Y pin `OEXT_78B_Y[F]` (null) for B+Qi's O-ext on Y.
- **5e. N's seven units** (E5). RK `sc_seeds` and `SC_ARM` take (arm, seed) pairs: OLMo R 1101-1103 and a0
  1101-1103; Llama R 1101-1103, a0 1101-1102 and N's a0-1103. RUN78: the regeneration takes the sealed R_d edit for R
  units; the acceptance input becomes `n_complete:{arm}:{seed}` for N's units. RK pin `N_UNITS[F]` (each unit's
  COMPLETE.json SHA-256 and folder), null until block 0's record-done; regeneration of N's units refuses until then.
  **Build risk:** on OLMo, N's R at 1101 and the side a0 at 1101 share seed 1101; `SC_PER_SEED_KINDS` keys by seed
  (R: RK:1203) and must key by (arm, seed). Tests: `test_n_r_unit_regen_uses_sealed_edit`,
  `test_n_acceptance_reads_n_complete`, `test_same_seed_two_arms_two_pods`, `test_null_n_units_refuse`.
- **5f. The Branch-128 flags** (DESO item 9). `--w1-18-record` on `c0`, `o_only`, `o_only_with_regenerate` and the
  arm step; `--dev100-source` on regenerated a0 and R units only (RUN1B's `dev100_source` form). Tests:
  `test_w1_18_flag_on_every_oext_command_under_128`, `test_no_w1_18_flag_under_full`, `test_dev100_source_regen_only`.
- **Mutants (5a-5f).** the a0_arm step dropped; term × 1.0; W1-18 not first; branch switch allowed; the flag dropped on
  c0; `--dev100-source` on θ0; N's R regenerated without its edit; acceptance against the side unit.
- **Pins and refusal.** `OEXT_78B[F]` null → `o_only`, `o_only_with_regenerate`, `c0` and every arm with O-ext refuse
  (R: RK:1188 for the first three); the branch record null → every 500-bank job refuses; `N_UNITS[F]` null → N's
  regenerations refuse; `OEXT_78B_Y[F]` null → B+Qi's O-ext refuses.
- **E** kit 12-16 h (basis: six sub-items, each a 1B form to port with its tests); Track O 10-16 h (§2).

### Item 6. References as kinds (P2 §3.2)

- **Now.** RK E kinds `ref_eval`, `safe_lora`, `ref_train_bqi` with E caps (R: RK:326-327; RULES-78B.md:125-127);
  SR78 `POINT_KINDS`, `REF_EVAL_SCALES` (R: SR78:383-384). RUN78 has no command for them (R: RUN78:162-189 routes
  block "sc" and block 0 only). No `ref_train` kind (R: P2 §3.2; RK `KINDS`, :328). `RECIPE_G`, `RECIPE_BQI` null
  (R: RK:160-162). `RECIPE_ALLOW` holds Llama's 1e-4 G (R: RK:132; RULES-78B.md:90-92). The base models' revisions are
  null (R: RK KIT `base_model`). PT78 keeps the 1B second-phase gate (a0 before references; R: PT78:3387).
- **Missing.** The commands (the 1B forms: R: RUN1B:467-487 for `ref_eval`, `_safe_lora` at RUN1B:553); the 1B
  `ref_eval` and `safe_lora` need `--certification-report` from `b10_certify` (R: RUN1B:476, :560) — see X2; per-family settings for
  `eval_adapter.py` (its settings pin the 1B manifest `9ed61826…`, M below) and `safe_lora.py` (`adapter.blocks` 16,
  `transform.points.default.k` 39, M below; 7-8B needs 32 blocks and K = 78, P2 §3.2); `ref_train` under `RECIPE_G`;
  the Llama G config at LR 5e-5 (a lead's committed addition; KD8).
- **Tests.** `test_ref_eval_points_prefix_and_scales`, `test_safe_lora_default_k78`, `test_ref_train_under_recipe_g_only`,
  `test_null_recipe_g_refuses`, `test_ref_train_bqi_on_y_only`, `test_refs_wait_for_own_seed_a0`,
  `test_ref_caps_carry_oext_term`.
- **Mutants.** K = 39 kept; `ref_train` accepts the main config; a reference planned before its seed's a0.
- **Pins.** `RECIPE_G[F]`, `RECIPE_BQI[F]`, `ENGINE_Y`, base revisions, the certification record (X2).
- **E** kit 8-12 h; Track R 6-10 h (§2).

### Item 7. The judge lists (P2 §6)

- **Now.** `units-of-block` (R: `judge_units_stage1.py:472-566`); PT78 `judge_required_units` (R: PT78:2622);
  `check-devices` (R: `judge_units_stage1.py:631`); `REJUDGED_PINS = {"0": ()}` (R: SR78:388). The 1B form lists each
  re-judged unit by name, arm, seed, target, path, `complete_sha256`, `job_sha256` (R: SR1B:193-229).
- **Change.** `REJUDGED_PINS["A"]` per family: 7 entries (OLMo 3 N + 3 a0 + θ0; Llama 4 N + 2 a0 + θ0; DESO item 26);
  the side units' and θ0's values are in RK KIT `a0_units` (R: RK:208-216, :229-233) except `job_sha256`; N's wait on
  block 0's record-done (null → block A's judge launch refuses). `REJUDGED_PINS["B"] = ()`. N's units live in the
  block-0 working copy (KD7), so each path must resolve from the block-A copy (X5).
- **Tests.** `test_rejudged_a_seven_per_family`, `test_null_n_pin_refuses_judge_launch`,
  `test_units_of_block_a_21_plus_7`, `test_no_run_root_sweep`.
- **E** 2-3 h.

### Item 8. SR-2's blinding test (P2 §10.1; P1 §6.4; the hard trigger)

- **Now.** RUN78's records hold no U, HB, O or answer (R: RUN78:50-55 docstring, "the test walks every record and
  every line"); PT78 `record_done` (R: PT78:4354) is the 1B one. No `blinded_sigma.py`.
- **Change.** Two halves, two tracks. Kit (K2): `record-done` of a block-A host prints and writes no U, HarmBench, O,
  L or coherence value. Track S: `blinded_sigma.py` prints σ̂_A and its df only; a test holds its stdout and its
  output file byte for byte.
- **Tests.** Kit: `test_record_done_block_a_prints_no_outcome` (fixtures with planted distinct sentinel values in
  COMPLETE.json, summary.json, query_loss.jsonl and judge files; scan stdout, stderr and every written file).
  Track S: `test_blinded_sigma_output_bytes`, `test_blinded_sigma_prints_no_cell_value`.
- **Mutants.** record-done echoes COMPLETE.json's summary; blinded_sigma prints a residual.
- **E** kit 2-3 h; Track S inside item 9.

### Item 9. `blinded_sigma.py` (P2 §10.2; DES3 V2)

- **Spec (P2 §10.2; DES3 V2).** σ̂_A = √2 × the pooled residual SD of the additive arm + seed model per cluster
  (full-corpus {a0, S1, S3, S4}; removal {R, A1, L1, H1}), over block A's cells and the reused cells at 1101-1104,
  pooled over clusters and the families that ran ([B]) or the chosen family ([C]); a cell with no partner seed in
  its cluster adds no df; inputs keyed by `complete_sha256` and family; on a stopped family, only the cells that run.
- **Df (I, arithmetic on P2 §2.2).** Per family, full design: removal cluster seeds 1102-1104 × 4 arms = 12 cells,
  1 + 3 + 2 = 6 parameters, 6 df (R at 1101 and R_5 at 1105 are alone at their seeds); full-corpus the same, 6 df;
  12 df per family, 24 under [B]. A stopped family: removal {R, H1} 2 df, full-corpus {a0, S1, S4} 4 df, 6 df. P2's
  "about 12-15" (R: P2 §10.2) holds at 12.
- **Change.** New `scripts/scale78b/blinded_sigma.py`: the unit reader of `noise_reading.py` (`read_unit`, R:
  `noise_reading.py:154`) imported by path and pinned, and U from the frozen Gate B reader (`noise_reading.py:27-29`
  imports `scripts/gate_b_reading.py` the same way); output `{kind, version, inputs_sha256, sigma_A_pp, df}` only.
- **Tests.** `test_df_12_per_family`, `test_df_6_stopped_family`, `test_lone_cells_add_no_df`,
  `test_invariant_to_arm_shift` (adding a constant to one arm's U leaves σ̂_A unchanged; P78:204's argument),
  `test_sqrt2_scale`, `test_pooled_not_averaged`, `test_1b_unit_refuses`, `test_other_family_key_refuses`, plus the
  two output tests of item 8.
- **Mutants.** no √2; lone cells counted; mean of per-family SDs; an arm effect left in; a residual printed.
- **E** 4-6 h.

### Item 10. Block A's seal (P2 §2.5)

- **Now.** `seal.py` (R: `seal.py:1-50`, `READABLE_PATTERNS` :61, `seal_block` :90) and PT78's G5 gate ("certify and
  B refuse before block A is complete and sealed", R: PT78 module doc :109). Both are the 1B ones.
- **Change.** The 7-8B block names; block B's `init-block` refuses until block A's seal; the W1-18 records and the
  a0 loss reads for τ_L stay named exceptions (P2 §2.5). **Cross-copy (X5):** §2.5's seal also covers N's L, HB and
  O files and the O pods' outputs, which live in the block-0 and `sc` copies (KD7). Proposed: a `seal.py block A
  --also COPY` list by path and SHA-256 (hashes only), or each copy sealed alone and named in block A's seal. Lead.
- **Tests.** `test_block_b_refuses_before_block_a_seal`, `test_seal_lists_o_pod_outputs`, `test_seal_never_parses`,
  `test_w1_18_record_readable`.
- **E** 2-4 h.

### Item 11. The state rule (P2 §2.6)

- **Now.** `states_tool.py` (146 lines); PT78 `own_a0_runs`, `second_phase_gate` (R: PT78:3339, :3387).
- **Change.** The per-block deletion list (DESO2 item 31) keeps the a0 e1 states at 1104-1107 until the references at
  that seed are complete; the kit refuses a list that names such a pod. Tests:
  `test_deletion_list_keeps_a0_1104_until_refs_done`, `test_deletion_list_names_every_stopped_pod`.
- **E** 1-2 h.

### Item 12. `C0_SOURCE`'s release-time check (DESO2 K6v-4)

- **Now.** The pack-time check (R: PACK:396-417, :464-465). The residual route: PT78 init and release do not read the
  unit (R: PT78:1325-1327, :1463-1468, :1477-1481 via K6V §2); the current test shows the route passing (R:
  `tests/test_scorer_block_78b.py:1753-1762` via K6V).
- **Change.** In `release_hosts_sc` (R: PT78:1447), for a c0 job: run `pack_setup.c0_source_check` on the packed
  source unit at the job's input pin against `C0_SOURCE[F]["e1_fingerprint"]` (K6V's first option), or record the
  checked fingerprint in `sealed-files.json` at pack and compare at release (its second).
- **Tests.** `test_c0_source_edit_after_pack_refused_at_release` (turn the 1753-1762 test around).
- **Mutants.** release skips the check; release compares with the pack-time value only.
- **E** 1-2 h.

### Item 13. The `similarity` kind (if room; DESO item 28)

- **Now.** The 1B kind J22 (R: RUN1B:179, `similarity_args` :371); `overlap_similarity.json` pins the 1B manifest and
  recipe `9e9bde6f…` (M below). **Change.** Per-family settings (Track R), kind, block "sim". **E** 4-6 h. Fallback
  "not run", stated (labelled in P2 §16.5 item 8).

### Item 14. The MAIN_F retrain on a family whose anchor job stopped (DESO2 item 36; DES3 V1)

- **Now.** `SC_KIND_PINS["retrain"] = ("RECIPE_S",)` (R: RK:1190); `SC_AFTER["retrain"] = ("anchor",)` (R: RK:1197);
  `retrain` is in `S78_KINDS` (R: RK:141), so `check_keys` demands `RECIPE_S` (R: RK:592-594).
- **Change.** A recorded anchor-stop record (kind, family, the anchor job's JOB-DONE.json SHA-256, the stop: exit 3
  "fewer than 64 kept" or the harmful-pair refusal). With it: `retrain` plans under recipe "B" (MAIN_F) on Y;
  `ENGINE_Y` is filled when this retrain is prepared (V1); if Y differs, the X retrain also runs under MAIN_F (V1);
  `rep_pass`, `l1_scan`, `classifier`, `a1_pass` refuse for that family for good; block tables drop A1, L1, S3.
- **Tests.** `test_stop_record_allows_main_config_retrain`, `test_stop_record_must_match_anchor_job_done`,
  `test_stopped_family_refuses_s78_kinds`, `test_unstopped_family_refuses_main_retrain`,
  `test_x_retrain_main_config_after_y_differs`.
- **Mutants.** retrain under MAIN_F without a stop record; a stopped family plans `l1_scan`.
- **Pins.** The stop record (lead's step). **Open:** the harmful-pair stop's exit code (I: only exit 3 is named,
  R: P2 §1.5, `make_anchor_answers.py:12`); the builder reads the script.
- **E** 3-4 h.

### Item 15. A reduced S-pool list (only if a prompt fails; DESO2 item 33; DES3 item 33 (b), V3)

- **Change.** New `scripts/scale78b/reduce_s_pool_78b.py` (frozen on commit; A3's pattern, its own sealed folder,
  identity-based write guards): the reduced list and a new s-pool record whose `lists.s3_subset.ids` and
  `lists.s1.ids` drop the same ids (DES3). MAKER reads the reduced size. **Build only if a $0 count fails** (§5 C1).
- **E** 4-6 h if needed, else 0.

### K6v-1 to K6v-6 (the handover's numbering; R: handover-gi-x-to-gi-xi-20261107.md:61-64)

| Gap | What | Where | E |
|---|---|---|---|
| K6v-1 | an unlisted binary `data/` file is scanned: test T1 and mutant `K6v-unlisted-binary-unscanned` (scorer spec) | `tests/test_scorer_block_78b.py`, `tests/mutation_spec_scorer_78b.json` | 0.5 h |
| K6v-2 | a non-daemon `Thread-N` guard probe: T2 and mutant `K6v-G2d-hook-nondaemon-default-threads-free` (gated spec) | `tests/test_pp10_process_wide.py`, `tests/mutation_spec_gated_78b.json` | 0.5 h |
| K6v-3 | the IPv6 stream probe with an explicit protocol: T3 (every wrapper case × stream/datagram × TCP/UDP, stand-ins only) and mutant `K6v-G1b-wrapper-skips-explicit-proto-v6-stream` | the same two files | 1 h |
| K6v-4 | the release-time `C0_SOURCE` check | item 12 | (item 12) |
| K6v-5 | the seed record in `k6-fix.md` M #8 (true colliding seeds 54, 289, 772, 1289; `-I` ignores PYTHONHASHSEED; R: k6-verify.md:232-234) | a records erratum, the lead's step; builders do not edit BR | lead |
| K6v-6 | the fingerprint-prefix test: also assert `expect[:12] not in text` | the item-23 test in `tests/test_scorer_block_78b.py` | 0.25 h |

The ready tests T1-T3 are not in the records: BR `k6-verify-scratch/` holds `hm_spec.json`, `hm_spec_k5v.json`,
`hm-*.json` and two collide files only (M: `ls`). So T1-T3 are re-written from K6V §2 (R: k6-verify.md:113-116,
:144-149); the mutants' find/replace texts are in `hm_spec.json`.

### §9's `confirm` kind on Y (before the first confirmation pod, about 11 Dec)

- **Now.** None at 7-8B. The 1B form `cert_c3` (R: RUN1B:58-59, :505-511: `make-job run-one --bank subsample-<SHA>
  --bank-file F` on Y; subsample file and record by plan pins; R: SR1B:463-467 `C3_RECORD`).
- **Change.** RK/SR78 `confirm` kind (Y only; E cap until measured; its own bank pin), seeds 9101-9106, one job per
  picked arm; PT78 a confirm block and the pick's record. Needs engine Y's pack (X1). **Tests.**
  `test_confirm_on_y_only`, `test_confirm_seeds_9101_9106`, `test_confirm_subsample_pin`, `test_shared_comparator_once`.
- **E** 4-6 h kit; the pick wrapper and the confirmation reader are reading code (P2 §16.3), not this kit.

### Items found that Part 2 §15 does not list

- **X1. Engine Y's pack and KD9's re-measure.** PACK takes engine "X" only (R: PACK:508, "engine Y's pack comes with
  KD9's re-measure"). Needed for the a0-1101 retrain (a scorer-block pod before block A: A1's states, ruling 10),
  `ref_train_bqi`, B+Qi's O-ext on Y and `confirm`. P2 §1.3 says the pack is built "when ruling 10's retrain is
  prepared" but no item names the build. The 1B kit's Y route and the frozen tree `tmp/engine-y-34bfd288` exist (M:
  `ls tmp`; R: SR78:181). **E** 5-8 h.
- **X2. B10's certification.** The 1B `ref_eval` takes `--certification-report` from a `b10_certify` job (R:
  RUN1B:467-487, :560) and P2 §16.1 carries "a failed B10 certification → every evaluation-only reference stops". P2 §15
  item 6 lists no `b10_certify` kind. Open item O2.
- **X3. Reference settings pin 1B values (M below).** `eval_adapter.json` pins manifest `9ed61826…`; `safe_lora.json`
  pins 16 blocks and K 39; `overlap_similarity.json` pins recipe `9e9bde6f…`. Each has a literal settings pin
  (R: `eval_adapter.py:98`, `safe_lora.py:97`, `overlap_similarity.py:69`). Track R.
- **X4. The plan-code record** (finding 1; item 1).
- **X5. Cross-copy references** (KD7): block A's re-judge pins and seal reach N's units (block-0 copy) and the O pods'
  outputs (`sc` copy). Items 7 and 10.

---

## 2. Track split

Owned files are disjoint between builders that run at the same time. Inside `runkit/stage1-78b/`, RK, SR78, PT78,
RUN78, PACK and the test files are shared, so the kit is four sequential sub-rounds (K1-K4) in one worktree, each
verifiable alone.

### Track S: SR-2 statistics (`scripts/scale78b/`)

- **Owns.** New `scripts/scale78b/blinded_sigma.py`, `scripts/scale78b/sr2_simulation.py`,
  `scripts/scale78b/settings/sr2_simulation.json` (the grid and the 6% rule, written before it runs),
  `scripts/scale78b/tests/test_blinded_sigma.py`, `scripts/scale78b/tests/test_sr2_simulation.py`.
- **Items.** 8 (its half), 9, P2 §10.3 (K6) with DES3 V2's reduced-design input.
- **Acceptance.** The scale78b suite passes (its count at the base plus the new tests); every Track S mutant killed by
  a runner in the kit's form (errors are invalid runs, re-run; the baseline with the same command); the simulation's
  output on a fixed seed is byte-stable; no U value in any output.
- **Brief (draft).**
  ```
  Goal: build scripts/scale78b/blinded_sigma.py and sr2_simulation.py for the 7-8B tier. Read-only elsewhere.
  Read: Part 2 §10.1-§10.3; Part 1 §6.1, §6.3-§6.4; DES K6, K7 and the third set V2; noise_reading.py (its unit
  reader, its frozen Gate B import pattern, its pinned-by-hash loading); plan-ab.md items 8-9.
  blinded_sigma.py: inputs keyed by complete_sha256 and family; reuse noise_reading.read_unit by path+hash import;
  U by the frozen Gate B reader as noise_reading does. σ̂_A = √2 x pooled residual SD of the additive arm+seed model
  per cluster (full-corpus {a0,S1,S3,S4}; removal {R,A1,L1,H1}); lone cells add no df; [B] pools families, [C] one;
  a stopped family pools the cells that run. Output only {kind, version, inputs_sha256, sigma_A_pp, df}.
  sr2_simulation.py: Monte Carlo of N's 4-df σ̂_pool -> block A's σ̂_A -> block B's plan by §6.1 -> HB-C with Holm
  at 5%, with and without arm x seed interaction, σ_pair 3 to 8.24 pp; prints each contrast's size and the
  familywise rate under the null, power at 8/10/12 pp; a --design flag for the reduced design (V2). The reading rule
  (familywise > 6% at any σ: "SR-2 not adopted") is in the settings file and printed; it is not applied by you.
  If HB-C's exact fit is too slow, use a documented approximation and say so; do not change the rule.
  Tests: plan-ab.md items 8-9 names; mutants as listed; byte tests for both outputs.
  Do not run the simulation for a result beyond a small smoke grid; the lead runs the full one.
  No pod, network, install, download, agent or commit. Report: files, SHA-256, commands with exit status, tests and
  mutant counts, open points.
  ```
- **E** 7-11 h (blinded_sigma 4-6; the simulation 3-5, SCOUT's 2-4 plus V2).

### Track O: the 7-8B O-ext layer (`scripts/scale78b/`)

- **Owns.** New `scripts/scale78b/oext_78b.py` (one wrapper, three commands: `unit`, `lean`, `w1_18`), its settings
  `scripts/scale78b/settings/oext_unit__F.json`, `oext_eval__F.json` (branch `pending_w1_18` until the record),
  `oext_unit_y__F.json`, `oext_eval_y__F.json`, `lean_eval_job__F.json`, `limits_overrefusal_checks__F.json` (the
  family's side units: θ0 and a0 1101-1103 OLMo, θ0 and a0 1101-1102 Llama, by COMPLETE.json and job.json pins),
  and `scripts/scale78b/tests/oext/` (parity on the 1B fixtures, refusals, the seams below).
- **Items.** 5c's code (the kit only calls it), 5d, c0's settings (P2 §1.13).
- **Decisive first check (30 min).** Can the wrapper run `oext_unit.main`, `lean_eval_job`'s entry and
  `overrefusal_checks.main` with per-family settings while each 1B file stays byte for byte? Seams: `oext_unit.py:209`
  (default path bound at definition), :146 (the O-ext settings path label), `oext_eval.py:246-251` and :214-236 (the
  W1-18 binding), `lean_eval_job.py:849`, `overrefusal_checks.py:83-84`, :542. If a seam needs a lie in a label (a
  path named in a settings file that is not the file read), stop and report: the lead picks the copy route (E4's
  "else", the `oext_unit_y.py` precedent: a copy with changed literal pins and a parity test that rebuilds it from the
  1B file by listed substitutions).
- **Acceptance.** Parity: on the 1B fixtures the wrapper's outputs equal the 1B script's byte for byte; the 1B files
  unchanged (`git diff --stat scripts/stage1 scripts/stage1_s1` empty); every refusal names hashes only; mutants all
  killed; the Llama `recipes.allowed` waits on the new G config (O11).
- **Brief (draft).**
  ```
  Goal: the per-family O-ext route for the 7-8B tier (DES E4, DESO2 item 24 (c), P2 §4.4, §1.13), as one wrapper
  scripts/scale78b/oext_78b.py over the unchanged scripts/stage1_s1/oext_unit.py, lean_eval_job.py, oext_eval.py
  and scripts/stage1/limits/overrefusal_checks.py, in the pattern of scripts/scale78b/scorers_78b.py (module
  globals set for the call and restored; settings read by path and hash; a pinned index).
  First do the decisive check in plan-ab.md §2 Track O and report it before building further if a seam fails.
  Settings per family F: oext_unit__F (manifest pin F's; recipes.allowed MAIN_F and F's recipe G; generation and
  guard hashes unchanged, M in plan-ab.md §5 C3), oext_eval__F (branch pending_w1_18; the W1-18 pin form ready for
  the record), Y variants (allowed B+Qi, null until RECIPE_BQI; engine_x = engine Y's identity), lean_eval_job__F
  (allowed recipes MAIN_F), limits_overrefusal_checks__F (the family's side units by COMPLETE.json and job.json
  SHA-256 from RK KIT a0_units; job.json hashes measured by you from the committed records only if they are
  committed; else leave null with a waits entry).
  Two W1-18 runs (one per family) on one pod: one codec per run.
  Tests: parity on the 1B fixtures; refusal of the other family's manifest; refusal under pending; the W1-18
  record's provenance equals the family settings' hash; the Y variant refuses on X.
  Do not open any unit's answer, generation or guard file; use fixtures. No pod, network, install, download,
  agent or commit. Report as Track S.
  ```
- **E** 10-16 h (E4's 4-6 h ×2 families with Y variants; c0's lean settings 1-2 h; W1-18 3-5 h, SCOUT §1.2's 4-8 h
  less the kit part).

### Track C: the $0 check tools (`scripts/scale78b/`)

- **Owns.** New `scripts/scale78b/encode_count_78b.py`, `scripts/scale78b/tau_l_78b.py`,
  `scripts/scale78b/tests/test_encode_count_78b.py`, `scripts/scale78b/tests/test_tau_l_78b.py`; and, only if a count
  fails, item 15's `reduce_s_pool_78b.py` with its test (a later round).
- **Items.** §5 C1, C2, C6; item 15 (conditional).
- **Acceptance.** Counts by reason only; fixtures only in tests; the codec from the prepared manifest's tokenizer
  (`build_s_pool.real_codec`, R: `scripts/stage1/build_s_pool.py:464-473`); `tau_l_78b.py` reads losses only (no
  guard label) unless a flag asks for the O planning line, and then it says so in its record.
- **Brief (draft).**
  ```
  Goal: two Mac $0 tools the lead runs (you build and test them on fixtures; you never run them on real lists).
  encode_count_78b.py --family F --list NAME=PATH:SHA256 ... [--pairs NAME=PATH:SHA256 ...] --out REC.json:
    for each list prompt encode_generation_prompt (textproc.py:192) at the recipe's generation.max_prompt_tokens
    (1,536 on both MAIN_F); for each s3_safe and S1 pair encode_train (textproc.py:173) at model.max_train_tokens
    (DES third set, item 38); codec = build_s_pool.real_codec; prints and writes counts by reason, list SHA-256s,
    the codec's tokenizer revision prefix and the recipe hash only. Also a --bank mode for the 400 PHTest prompts
    read through oext_eval's pinned bank reader (record a810574e…).
  tau_l_78b.py: τ_L = 2√2 × SD(ddof 1) of each a0 unit's mean query loss on the 200 task rows at e1 (P2 §4.7;
    PR4:589-595), units by COMPLETE.json pins and the query_loss.jsonl hash COMPLETE.json lists; reads no other file.
  Tests: reason counts on synthetic fixtures; refusal of an off-pin list; τ_L on a known fixture; no text in output.
  No pod, network, install, download, agent or commit. Report as Track S.
  ```
- **E** 4-6 h (+ 4-6 h for item 15 only if needed).

### Track R: reference settings and wrappers (`scripts/scale78b/`)

- **Owns.** New `scripts/scale78b/refs_78b.py` (wrapper over `eval_adapter.py`, `safe_lora.py`,
  `overlap_similarity.py`), `scripts/scale78b/settings/eval_adapter__F.json`, `safe_lora__F.json` (32 blocks, K = 78,
  the base model pins null until the lead's Hub read), `overlap_similarity__F.json` (only if item 13 is built),
  `scripts/scale78b/tests/refs/`.
- **Items.** 6's settings, 13's settings, X3.
- **Acceptance.** Parity on the 1B fixtures; K = 78 by 39 × 2 (M in P2 §3.2); the 1B files unchanged.
- **Brief.** As Track O's form, with `eval_adapter.py:1579-1590`'s self-hash rule (its settings literal is hashed
  out of the script's own identity) read first; report whether the wrapper route holds or a copy is needed.
- **E** 6-10 h. **Deferrable** to before block B if the lead allows (§4, S2).

### Track K: the kit (`runkit/stage1-78b/`), four sequential sub-rounds in one worktree

| Sub-round | Owns (exclusive while it runs) | Items | E (h) |
|---|---|---|---|
| K1 rules | RK, SR78, `RULES-78B.md`, `tests/test_rules_78b.py`, new `tests/test_block_tables_78b.py`, `tests/mutation_spec_rules_78b.json` | 1 (tables, pins), 2, 3, 4, 5b, 5c's kinds, 5e's pins, 7's pins, 14's rules; RK `OEXT_UNIT_SCRIPT` / `C0_SCRIPT` to Track O's path | 10-14 |
| K2 planning | PT78, `judge_units_stage1.py`, `seal.py`, `states_tool.py`, new `tests/test_planning_ab_78b.py`, `tests/test_scorer_block_78b.py`, `tests/test_stage1_judge_route.py`, `tests/mutation_spec_scorer_78b.json` | 1 (init-block A/B, `record-plan-78b`), 5c (branch record), 7, 8 (kit half), 10, 11, 12, 14 (stop record), K6v-1, K6v-6 | 10-14 |
| K3 runner and pack | RUN78, PACK, `setup/preflight_stage1.py`, `finisher.py`, `README.md`, `tests/test_kit_78b_runner.py`, new `tests/test_runner_ab_78b.py`, `tests/mutation_spec_runner_78b.json` | 5a, 5c's command, 5e's commands, 5f, 6's commands, X1 (Y pack) | 12-18 |
| K4 hardening | `tests/test_pp10_process_wide.py`, `tests/conftest.py`, `tests/mutation_spec_gated_78b.json`, and every spec for the final sweep | K6v-2, K6v-3; whole-kit mutant sweep; 13 if room; later `confirm` | 4-6 (+4-6 confirm, +4-6 similarity) |

- **Order inside the kit.** K1 → K2 → K3 → K4. K1 is verifiable alone (rules and tables are pure functions); K2 uses
  K1's tables; K3 uses K1's kinds and K2's plan.json shape; K4 only adds tests and mutants.
- **Acceptance for each sub-round.** The 7-8B suite passes under the network-deny sandbox (487 at `c57e456`, R: K6V
  §3, plus the new tests; count read at the base by the builder); the stage-1 kit's suite unchanged (762); all four
  mutation runners re-run in chunks under 10 min each (the lead's `run.sh` form): every mutant killed, 0 survived,
  0 invalid (errors are invalid runs and are re-run; the baseline with the same command); new mutants for every new
  rule; no token-shaped file left in any basetemp.
- **Brief (draft, K1; K2-K4 take the same frame with their rows).**
  ```
  Goal: sub-round K1 of the 7-8B kit's block A/B build: the rules layer only. Work in WS (a detached worktree at
  c57e456 plus the merged earlier sub-rounds). Own only: rules_78b.py, stage1_rules.py, RULES-78B.md,
  tests/test_rules_78b.py, new tests/test_block_tables_78b.py, tests/mutation_spec_rules_78b.json.
  Read: Part 2 §2, §3.2, §4.2-§4.5, §15; DES B1, E2-E5, F2, J2; DESO items 9, 24, 26; DESO2 items 36, 37;
  DES third set V1; plan-ab.md items 1-5, 7, 14 and O1-O16.
  Build: block A/B tables per plan and family with the R_d source table and null method-edit pins; the 1B deal;
  STEPS["dose"] = 39 with the rows check; train_scale's input; the O-ext cap term x1.5 (Branch full M values;
  Branch 128 E) and the O-ext bank pin in check_keys; the w1_18 kind, BANK500_KINDS, BRANCHES; (arm, seed) keys
  for o_only_with_regenerate with N_UNITS null pins; REJUDGED_PINS["A"] with null N entries; the anchor-stop
  rules (retrain under MAIN_F only with a stop record; S_78 kinds refuse for good on that family);
  OEXT_UNIT_SCRIPT/C0_SCRIPT = scripts/scale78b/oext_78b.py (Track O's name; a stub path is fine).
  Every new pin is null and refuses with its filling event (A13's pattern). Do not decide O1 (s4_top steps):
  leave it refusing with a message naming the open item.
  Tests and mutants as plan-ab.md names them. Run the suite and the rules runner in chunks (<10 min each) under
  sandbox-exec network deny. No pod, network, install, download, agent or commit.
  Report: changed files with SHA-256; commands and exit status; test and mutant counts; open points.
  ```

---

## 3. Dependencies and order

**Before block A's first pod (P2 §15: items 1-11 verified; item 8 the hard trigger).** The scorer block must also
have run (A1, L1, S3, S4 edits come from it), and the scorer block itself needs, from this build: the W1-18 kind and
Track O's files (its O pods), N's-unit regeneration (5e), the Branch-128 flags (5f), the Y pack (X1, for the
retrain), the stop path (14) and the release-time `C0_SOURCE` check (12). So the true order is:

| Step | Needs | Gives |
|---|---|---|
| R1: Tracks S, O, C and K1 (parallel; disjoint files) | P2, DES, this plan | blinded_sigma, the simulation, the O-ext wrapper and settings, the count tools, the rules layer |
| Lead: $0 checks C1, C2, C5, C6 (§5) | Track C tools; C5's merged script exists now | §0 item 14, §4.1, §4.7 values; item 15 only if a count fails |
| R2: K2 and Track R (parallel) | K1 merged; Track O's paths | planning, judges, seal, blinding record-done, C0 release check; reference settings |
| R3: K3 | K1, K2, Track O merged | arm O-ext step, W1-18 command, N's regenerations, flags, reference commands, Y pack |
| Lead: the simulation's full run and its reading (6% rule) | Track S | SR-2 adopted or not (before block A) |
| R4: K4 (+ `similarity` if room) | K3 merged | the K6v test gaps, the whole sweep |
| Money: block 0 (N), then the gate | the user's money (about 20 Nov, R: handover:51) | N's values, C0_SOURCE, N_UNITS, re-judge pins |
| Scorer block | R3 merged; OEXT_78B filled after the W1-18 pod | method edits; their pins |
| Part 2 freeze; block A | every [to be entered] value; items 1-11 verified | — |
| R5: `confirm` kind (about 11 Dec, R: P2 §15) | X1; the pick wrapper | — |

- **The hard trigger.** Item 8 (both halves) must be verified before block A's first pod, else SR-2 is not adopted
  (R: P1 §6.4). Put it in R1 (Track S) and R2 (K2) so it has two rounds of slack.
- **Can wait.** `confirm` (about 11 Dec); `similarity` (only if room, DESO item 28); item 15 (only if a count fails);
  the reading wrapper (P2 §16.3; before block B's outcomes are opened, DES K7).
- **What could wait if the lead allows (not decided here; S2 in §4).** Items 3 and 6 (doses and references) are
  block-B work; P2 §15 says items 1-11 are verified before block A.

---

## 4. Simplifications, risks and open items

### Per item

| Item | Simpler alternative | Weak assumption | Failure case | Smallest decisive check |
|---|---|---|---|---|
| 1 | reuse the inherited 1B `build_block` (PT78:3148) behind a 7-8B table | the 1B block-A plan machinery (`default_block_a_doc`, LN-12 pods, Gate B verdict) fits 7-8B | `plan_ab_checked` reads `rules.GATEB_VERDICT`, absent in SR78 (M) → AttributeError | a lean route like `init_block0`/`init_block_sc` (R: PT78:1092, :1372) is simpler: recommended |
| 2 | none | arms interleave without a repeated arm | 21 runs, 6 pods: A1's 3 seeds on 3 pods (I) | `deal(block_runs("A","A"))` in a test |
| 3 | `STEPS["dose"]` only | every dose edit has 96 or 192 rows | `s4_top` at 48-64 rows → 38 steps (M) | O1 |
| 4 | none | edit records carry token counts | they do not → read the prepared set's token fields by row id | open one committed edit's record keys (text-free) |
| 5a | E3's fallback (separate O job per unit) | the arm step fits the cap with × 1.5 | Llama 4-arm cap 19.25 h (M in P2) | dry-run `cap_hours` on a 4-arm Llama pod |
| 5c | Branch full for both families with no W1-18 pod (E2's frozen fallback) | the side units' stored dev-100 answers carry `output_ids` | W1-18 refuses a unit (P2 §14 item 29) | the lead lists COMPLETE.json's file keys of one side unit |
| 5c | **run W1-18 on the Mac at $0** (the module is a Mac tool, R: `overrefusal_checks.py:1-2`) | the guard model can be fetched | Qwen3Guard-Gen-4B is not in the HF cache (M: `ls`) → a download needs the user's yes; mps needs guard batch 1 (R: :52-55) | O5: DESO2 item 37 ruled a pod |
| 5d | the copy route (Y precedent) | the wrapper can set every seam without a label lie | :146's path label; :209's default argument | Track O's decisive check |
| 5e | O for R_1102, R_1103, Llama a0-1103 only (SCOUT §1.5 (c)) | — | ruled (a) for all seven (DES E5) | none |
| 6 | defer Track R and the reference commands to before block B | P2 §15's "items 1-11 before block A" can bend | the lead keeps the text | S2 |
| 7 | none | N's unit folders resolve from block A's copy | KD7's one-block copies | X5 |
| 8 | none | `record_done` prints nothing from COMPLETE.json | the inherited 1B code prints a summary | the planted-sentinel test |
| 9 | none | Gate B's U reader takes 7-8B units | it pins the 1B form | `noise_reading.py` already reads 7-8B units with it (R: :27-29) |
| 10 | seal each copy alone, name them in block A's seal | — | §2.5 covers files in three copies | X5, O7 |
| 12 | accept the residual path as a limit (K6V job 3's other option) | — | ruled: build (DESO2 K6v-4) | none |
| 14 | none | a stop is visible from JOB-DONE.json alone | the harmful-pair stop's exit code is not named | read `make_anchor_answers.py`'s exits |
| X1 | none | the 1B Y route ports | the Y tree's identity and the 7-8B basis on Y (KD9) | PACK dry run with `Y` after the port |
| X2 | — | — | `ref_eval` cannot run without a certification report | O2 |

### Where Part 2 and the code disagree, or Part 2 leaves the build undefined (open items for the lead)

- **O1.** S4_top's steps at 48-64 kept rows: ⌈(4,800 + n) / 128⌉ = 38, while P2 §2.1 gives the dose arms 39 (M:
  arithmetic). Undefined.
- **O2.** B10's certification at 7-8B: the 1B `ref_eval` needs a certification report (R: RUN1B:476, :560); P2 §16.1
  carries the B10 stop rule; P2 §15 item 6 lists no `b10_certify` kind. Is a certify kind built, or the stop rule
  read as moot?
- **O3.** W1-18's settings: `oext_eval.py:218-219` says W1-18's settings "are never re-pinned"; a 7-8B W1-18 run
  needs per-family settings; the frozen binding (R: :214-236, :374-375) passes them only by in-process patching or a
  pack-time swap. Is that inside the rule?
- **O4.** "Per family" (DES E2) and "one pod" (DESO2 item 37): two W1-18 runs on one pod, two records, a branch per
  family (I). Confirm.
- **O5.** W1-18 on the Mac at $0 instead of a pod (needs the guard model's download, the user's yes).
- **O6.** The anchor-stop record's form and what proves each stop (item 14).
- **O7.** Which seal holds N's files and the O pods' outputs that live in other working copies (item 10, X5).
- **O8.** N's R_1101 is regenerated twice before block A: by c0's lean job and by `o_only_with_regenerate` (P2
  §1.13, §4.5). Not a defect; about $1.4 (E: SCOUT §1.3's separate-job increment). Noted only.
- **O9.** τ_L: the frozen 1B REQ-19 tool (`scripts/stage1/limits/limits_check.py`, literal pin R: :70) also reads the
  dev-100 guard labels for O's MDE (R: :12-16). A losses-only reader (Track C) keeps §0 item 10 at "none read".
- **O10.** K6v-5 is a records erratum (`k6-fix.md`), the lead's step.
- **O11.** Llama's new G config (LR 5e-5) must exist before `oext_unit__llama31-8b.json` is final, because its
  `recipes.allowed` lists F's recipe G (P2 §4.4); else `OEXT_78B[llama31-8b]` is filled twice.
- **O12.** The reference E caps hold the dev-bank evalonly bound (R: RULES-78B.md:125-127); with O-ext × 1.5 they
  rise (P2 §3.2). The new values are E until measured; the lead records them.
- **O13.** The sealed S lists' location: PINS names only file names (`s1.json` `389c20ad…`, `s3_safe.pool.json`
  `6801652c…`, `s4_candidates.json` `798613c4…`; M: key read of `pins_78b.json`). The lead runs C1 where they are.
- **O14.** A plan-code record for 7-8B (finding 1): which file and field the kit reads for N's code and for SR-2's
  re-read (noise_reading's output and blinded_sigma's).
- **O15.** P2 §15 says items 1-11 verified before block A; items 3 and 6 are block-B work (S2).
- **O16.** SCOUT's 20-30 builder h (P2 §15) against this plan's 70-100 h (§6).

### Simplifications offered (the lead's call)

- **S1.** One lean planning route for blocks A and B (like `init_block_sc`), not the inherited 1B route. Saves the
  Gate-B-verdict, LN-12, cert and certify gates that do not apply (I).
- **S2.** Build Track R, item 3 and the reference commands in a round after block A's first pod, before block B
  (saves about 15-20 h before block A; E: items 3 and 6 above). Needs the lead to read P2 §15 that way.
- **S3.** One `oext_78b.py` wrapper for O-ext, c0's lean job and W1-18 (three commands, one parity suite) instead of
  per-family, per-engine copies (up to 6 copies under the copy route; I).

---

## 5. The $0 checks (counts and hashes only, through frozen readers)

| Check | Code path | Inputs (blinding) | Prints | On the Mac? | Who |
|---|---|---|---|---|---|
| **C1** S3, S4 (and S1) lists' encode count per family (DESO items 6, 17; DES3 item 38) | Track C's `encode_count_78b.py`: `textproc.encode_generation_prompt` (R: textproc.py:192) at `generation.max_prompt_tokens` 1,536 (R: both MAIN_F configs, M: `grep`) for every list prompt; `encode_train` (R: :173) at `model.max_train_tokens` for every `s3_safe` and S1 pair; codec by `build_s_pool.real_codec` (R: build_s_pool.py:464-473) | the sealed lists `s1.json` (48), `s3_safe.pool.json` (861), `s4_candidates.json` (512) by SHA-256 (M: PINS); prompt text read in-process, never printed; no answer exists yet; `s3_subset` (855) is a subset of `s3_safe`'s ids (I: P2 §1.8) | per list and family: n, n accepted, counts by reason; list hashes; the tokenizer revision prefix | tokenizers yes (M: both manifests' tokenizer snapshots present in the HF cache); the lists' folder not named in PINS (O13) | the lead (it opens sealed prompt files); an agent builds the tool on fixtures |
| **C2** the 400 PHTest prompts' Llama encode count (DES E1) | the same tool's `--bank` mode: the bank by oext_eval's pinned reader (record `a810574e…`, bank `6487ed2b…`), `encode_generation_prompt` on Llama's codec at 1,536 | the sealed bank (prompt text in-process; no answer exists) | count by reason | Llama tokenizer yes (M); `tmp/oext-phtest-20261017/` exists (M: `ls`, folder names only) | the lead |
| **C3** MAIN_F generation and guard hashes vs the 1B O-ext pins | `oext_unit.check_recipe`'s expression (R: oext_unit.py:299-302): `sha256_bytes(canonical_json(recipe[block]))` after the engine's `load_recipe` | the two main configs and both G configs (no outcome) | **done (M, this run):** `plan-ab-scratch/gen_guard_check.py` with `.venv/bin/python -I -B`: OLMo main `18cc31d7…`, Llama main `74758af1…`, OLMo G `01259f28…`, Llama G (1e-4) `442f133f…`: generation `5ddced7af22b968f…` and guard `a7f0755b795f0ac4…`, all equal OXU's pins | yes | done; re-run on Llama's new 5e-5 G config when it exists |
| **C4** the Safe LoRA disk fit (P2 §3.2) | arithmetic: container disk 60 GB (R: RK:253), volume 50 GB (R: RK:250); policy + base + guard (+ states 5.8 GB per arm, R: RK:254); where the pod puts the models (`setup/download_models_stage1.py`, to read) | Hub file sizes of `allenai/OLMo-2-1124-7B` and `meta-llama/Llama-3.1-8B` (no outcome) | the sizes and the sum against 60 GB | **no:** neither base model is in the HF cache (M: `ls`); E only: about 14.6 GB (OLMo) / 16.1 GB (Llama) per bf16 copy (2 bytes × parameters, E), guard about 8 GB (E), so about 37-40 GB in bf16; SCOUT's 38-53 GB (E; base dtype unverified) | the lead, at a step that may use the network (Hub metadata only), or the Range precheck at the next Llama launch (DES F2) |
| **C5** OLMo-2-7B S1 re-check with the merged script (DESO item 20) | `scripts/scale78b/s1_olmo2_7b_check.py` (merged; R: its args :207-217) | the committed edit `add_s1.json` `904a0cf1…` by path and hash (text dropped at once, R: its header :23-27), the stage-1 record, the 7B main config, the 1B recipe S, the sealed S1 list (389c20ad…) by `--list` or recovered | counts and hashes; `--out` a text-free record (its path and SHA-256 go into P2 §0 item 14) | OLMo prepared set yes (M: `tmp/kt-prepared/prepared-kt-dolly-olmo2`); tokenizer yes (M) | the lead (it reads a sealed edit); runnable now |
| **C6** OLMo-2-7B τ_L from losses (DES K2) | Track C's `tau_l_78b.py` (losses only); the frozen 1B `limits_check.py` does not take 7-8B units (literal pin, R: :70; its settings list four 1B units, R: :4-8) | the side a0 units 1101-1103 (COMPLETE.json `4a6d9ebc…`, `43e8412d…`, `4b5bd06d…`; R: RK:209-214): each unit's `query_loss.jsonl` at the hash its COMPLETE.json lists; side units, not N's files (P2 §2.5) | s and τ_L = 2√2 s | the unit folders exist (M: `ls tmp`, top names only: `family-probe-sp-olmo2-7b-b-a0`, `…-b-seed1102`, `…-b-seed1103`); their contents not opened by me | the lead (Mac); an agent builds the reader on fixtures |
| (later) the 200 hidden-subsample ids in Llama's prepared set (P2 §9) | the 1B C3 subsample record form (R: SR1B:463-467) | the hidden bank (hidden) | count and hashes | — | the lead only, before the first confirmation pod |

---

## 6. Usage estimate

- **Builder hours (E; basis: the per-item E above).** Track S 7-11; Track O 10-16; Track C 4-6; Track R 6-10;
  K1 10-14; K2 10-14; K3 12-18; K4 4-6. Before block A: about 63-95 h (with Track R) or 57-85 h (without, S2).
  Later: `confirm` 4-6, `similarity` 4-6, item 15 4-6 only if needed. SCOUT priced the kit alone at 20-30 h (R: P2
  §15); the difference is X1-X5, Track O's size and the tests and mutants per rule.
- **Rounds (E).** R1: 4 builders (S, O, C, K1) + 1 verifier. R2: 2 builders (K2, R) + 1 verifier. R3: 1 builder (K3)
  + 1 verifier. R4: 1 builder (K4) + 1 verifier. Then fix rounds as needed: GI X's rounds 4-7 each needed a fix
  round (R: BR report names `k4b-fix`, `k5-fix`, `k6-fix`), so plan one fix round per kit sub-round (E).
- **Tokens.** I have no measured tokens per builder hour or per round, so I give no token figure. A practical gauge:
  read the all-models weekly percentage before and after R1 (69% now; resets 2026-11-12T09:00 UTC, R: GI XI rulings)
  and scale R2-R4 by their builder hours against R1's (E: proportional, untested).
- **Pacing (I).** R1 (the largest parallel round) before the 12 Nov reset uses the current week's room; R2-R4 after
  it. The mutation sweeps run as the lead's background jobs, not inside agents (memory "long jobs outside agents").

---

## 7. Commands run (all foreground, all exit 0 unless noted)

1. `date -u` (13:50, 14:02 UTC). 2. `git rev-parse --abbrev-ref HEAD`, `--short HEAD` in MAIN. 3. `sed -n`, `grep -n`,
`wc -l`, `ls` over Part 2, DES, the GI XI rulings, the handover, SCOUT, K6V, the kit, the stage-1 kit, `scripts/`.
4. Python `-I -B` key prints of OXU, OXE, their Y files, `lean_eval_job.json`, `eval_adapter.json`, `safe_lora.json`,
`overlap_similarity.json`, `pins_78b.json` (keys, short hashes, counts, top folders) and the two prepared manifests'
tokenizer keys with cache presence. 5. `plan-ab-scratch/gen_guard_check.py` (C3). 6. `git status --porcelain` (no
change of mine). No test suite was run.
