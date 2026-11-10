# R1 K1 adversarial verification: the 7-8B kit's rules layer for blocks A and B

Written 2026-11-08; clock read with `date -u` at 15:44 UTC (start) and 16:06 UTC (this text). Read-only on WS:
B/ws-k at `3481d85` plus K1's working-tree changes (M: `git -C B/ws-k log --oneline -1`, `git status --short`: the 11
modified files and the new test file only, the same before and after my run). Every K1 file hashed equal to the
builder's table (M: `shasum -a 256`, 12 files). I wrote only this report and `R/r1-k1-verify-scratch/`. No pod, spend,
network, install, download, agent or message. No sealed edit file's contents, answer, generation, judge or prompt
file opened; the two S1 edits (in `tmp/stage1-olmo/` and `tmp/scale-78b-*/`) were not opened or hashed. Tags: M
measured (command), R read (path:line, WS paths unless named), E estimate, I inference.

**Verdict: DEFECTS.** Three major defects, all from the lead's fourth ruling set (15:43 UTC), which arrived after
the builder's report (15:39 UTC): the anchor-stop record's form (K1V-1), K-5's dose table (K1V-2) and K-6's plan-B
fields (K1V-3). Nine minor or nit items follow. Block 0 is unchanged in behaviour (M, check 1). The tables, hashes,
steps, caps and funding needs are right (M, checks 2-3). The suite passes (527, M) and all 188 rules mutants are
killed (M). But 7 of my 16 probe mutants survive (K1V-7).

## Defects

| id | sev | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| K1V-1 | major | rules_78b.py:2001-2003, :2012-2026, :2028-2081; tests/test_rules_78b.py:2072-2111 | The anchor-stop record does not have the fourth set's form. K1 writes kind `stage1-78b anchor stop`, field `stop`, values `few_safe` / `harmful_pair`. The ruling and Track S's reader use kind `scale-78b anchor stop`, field `stop_kind`, values `safe_anchors_below_64` / `harmful_prompt_does_not_encode` (R: GXB fourth set, last item; B/ws-s/scripts/scale78b/blinded_sigma.py:69-70, :229-235). | A family's anchor job stops. K2's writer is built on `anchor_stop_record` and writes K1's form. Then `blinded_sigma.check_anchor_stop` refuses the record ("is not a scale-78b anchor stop record"), so σ̂_A cannot be computed and PLAN_B_78B cannot be filled for block B. | Rename the kind, the field and the two values to the ruling's form. Add one shared fixture that both RK's `anchor_stop_problem` and Track S's `check_anchor_stop` must accept (the ruling asks for this), plus a mutant that changes the kind string. |
| K1V-2 | major | rules_78b.py:1611-1619 (`S4_TOP_MIN = 48`), :1629-1644, :1787-1820 (`dose_arms`); tests/test_block_tables_78b.py:150-151, :369-381 | K-5's dose-arm table is not built. No function maps the kept count n to the dose arms, and `block_runs_78b` accepts any subset of {S4_96, S4_192, s4_top}. M (`k5_probe.py`): it accepts (S4_192, s4_top) and all three together; s4_top is accepted at n = 48 (38 steps) and n = 96 (39 steps). K-5 says n = 48 forms no dose arm and n = 96 gives S4_96 only (also P2 §5; DESO, the S4 boundary cases). `test_s4_top_steps_rule` checks that 48 and 96 are accepted. There is no test per case. | Exactly 48 rows are kept. The kit plans s4_top, a copy of S4 that the design says is never formed, at 3 or 6 seeds. Cost about $11-28 per family (E: P2 §3.1's planning rates of $3.53 / $4.71 per arm). Or 97-191 rows are kept and a jobs file names S4_192: the table accepts it, and only the null pin stops it, if the pin really is null. | Add `dose_arms_for(n)` per K-5: n ≥ 192 gives (S4_96, S4_192); 97-191 gives (S4_96, s4_top); 96 gives (S4_96,); 49-95 gives (s4_top,); 48 gives () ("no dose arm"); n < 48 is Refused (a build stop). `block_runs_78b` should take n, or refuse `dose_arms` that differ from `dose_arms_for(n)`. s4_top should accept only 49-95 and 97-191. Add one test and one mutant per case. Update RULES-78B.md ("n in 48-191"). |
| K1V-3 | major | rules_78b.py:1886-1887 (`PLAN_B_KEYS`), :1921-1940; tests/test_rules_78b.py:2026-2069 | PLAN_B_78B does not carry K-6's fields. When SR-2 is not adopted, the record must hold null blinded_sigma hashes, the reason (the blinding test not verified, or the simulation's reading) and the plan's basis (N's value under [B], the chosen family's σ̂_F under [C]) (R: GXB K-6; P1 §6.2, §6.4). K1 has no reason or basis field. It also accepts real SHA-256s when `sr2_adopted` is false (I: :1933-1937 checks the hash only when SR-2 is adopted). | Under [C] the record says `sr2_adopted: false` but carries blinded_sigma hashes, and the kit accepts it. Nothing then shows whether block B's plan came from σ̂_A, N's σ̂_pool or σ̂_F. Also, a K2 writer that follows K-6 cannot write the reason without changing K1's key set. | Add `sr2_reason` (null if adopted; else one of "blinding_test_not_verified" or "simulation_reading") and `plan_basis` ("sigma_A", "sigma_pool_N" or "sigma_F"), with `plan_basis` checked against the option: sigma_F only under [C], sigma_pool_N only under [B]. Require both hashes to be null when SR-2 is not adopted. Add tests and mutants. |
| K1V-4 | minor | rules_78b.py:219-250 (KIT `a0_units` `job_sha256`) | The builder measured θ0's job.json SHA-256 and wrote it into the code. T-O2 makes this value the first fill in its order, "measured by the lead by hash only", as a recorded lead step. The values are right (M, my `shasum -a 256` of all 7 job.json and COMPLETE.json files under MAIN tmp/; 16-hex prefixes equal). The 1B kit had builders measure job hashes too (R: runkit/stage1-olmo/stage1_rules.py:185-189). | An audit of T-O2's fill order finds θ0's hash in the code but no recorded lead step or FOCUS line for it. | The lead records the fill, citing this measurement, before the W1-18 pod. Or K1 keeps θ0's job hash as a null pin until that step. |
| K1V-5 | minor | rules_78b.py:2285-2347 | There is no pinned branch record. `bank500_problem`, `oext_flags` and `branch_switch_problem` take a document from the caller with no hash check. By KD7 and K-3, the W1-18 record lives in OLMo's scorer-block copy, but Llama's scorer-block copy and both families' A and B copies read their own branch from it. The brief lists the branch record among the new null pins. | A copy is given a stale "Branch full by default" record although the family's recorded branch is 128, or the reverse. The never-switch check only compares against whatever old record the caller passes. | Add a null pin `BRANCH_78B[F]` = {path, sha256}, read through `_pinned_record_or_refuse` and filled by K2's branch-record step (K-8). K1 or K2 adds it; the lead decides. |
| K1V-6 | minor | rules_78b.py:2083-2092 | `family_stopped` returns True for any well-formed {path, sha256} pin. Nothing reads the pinned record's bytes, checks the hash or runs `anchor_stop_problem` on it, unlike GATE_78B and PLAN_B_78B (:1943-1971). | A mistyped ANCHOR_STOP fill turns a family to "stopped". A1, L1 and S3 then leave every table and the MAIN_F retrain is allowed, with no stop record behind it. | Add `anchor_stop_or_refuse(family, data, job_done_sha256)` in the GATE pattern. K2 calls it at planning, and `family_stopped` is used only after it. |
| K1V-7 | minor | tests (see check 6) | Test gaps. 7 of my 16 probe mutants survive (M: `mut-probe.json`). The checks no test covers: an edit pin's `.json` suffix; W1_18_78B's `scripts/` prefix; the stop record's int type for exit_code (`True` == 1 passes); the gate's int type for version; the source and W1-18-hash fields in `branch_switch_problem`; extra keys in an N_UNITS unit; and, the most material, `sc_needed_pins` for Llama's N a0-1103. The mutant `arm == "R"` survives, so no test holds that Llama's a0-1103 regeneration needs N_UNITS. | A later edit drops one of these checks and every test still passes. For example, Llama's N a0-1103 would plan with N_UNITS null. | Add assertions for each case, and add the 7 probes (`tools/make_probe_src.py`) to the rules spec. |
| K1V-8 | minor | stage1_rules.py:433; rules_78b.py:2199-2200 | `REJUDGED_PINS["A"]` is evaluated when stage1_rules is imported, so a malformed N_UNITS pin raises Refused at import. M (`n_units_import_probe.py`): with a bad N_UNITS["olmo2-7b"], the block-0, sc and A copies of that family all fail to import. | A typo in N_UNITS's recorded fill crashes every kit command (status, backup, release) in each new copy of that family, instead of refusing the judge launch. | Build the list lazily (a function), or keep N's entries null and give the problem through `rejudged_or_refuse`. |
| K1V-9 | minor | stage1_rules.py:337-342 | SR78's `_unit_source` treats arm None as the side unit, so `sc_input_names("o_only_with_regenerate", 1101)` still names a unit by its seed alone. The seed key says "not by seed alone", and RK's `sc_unit_source` refuses arm None. | A K2 or K3 caller omits the arm for N's R_1101. The job gets side a0-1101's acceptance input, the regenerated R_1101 "differs", and its O is stated "not run" (DESO item 18) instead of being refused. | Refuse arm None once K2 and K3 pass arms. Until then, list it as a K2/K3 acceptance item with a test. |
| K1V-10 | minor | setup/job_runner_stage1.py:602, :610, :623 (not K1's file); tests/test_scorer_block_78b.py:1044-1075, :1601 | A temporary state from T-O3's split ("K1 takes the pins; K3 the commands"). The runner now writes `oext_78b.py run --untuned …` and `oext_78b.py run --job …`, commands the wrapper's `unit` / `lean` / `w1_18` interface does not take. The scorer test now holds those lines through the constant instead of a literal; test_37 still pins the path literal. The scorer spec's K4bf-m-c0-needs-oext-script is now equivalent (builder: 1 survivor; the lead's scorer run had not finished). No launch risk while OEXT_78B is null. | If OEXT_78B were filled before K3, the scorer block's O-ext pods would fail at their first command. | K-1 (K2: the command-word check, re-target the mutant) and K3 (the commands). Record that the scorer block's O-ext kinds are not launchable from this tree until then. |
| K1V-11 | nit | rules_78b.py:2230; RULES-78B.md (s4_top line) | The W1_18_HOST_FAMILY comment still says "(I; open point)", but K-3 has ruled it (OLMo-2-7B's scorer-block copy; K1's value agrees). RULES-78B.md says s4_top takes "n in 48-191". | Readers take a ruled point for an open one. | Cite K-3. Update the doc with K1V-2's fix. |
| K1V-12 | nit | tests/test_kit_78b_shell.py:283 | The regex "unknown kind\|does not belong to block 0" keeps a branch that can no longer match (I: w1_18 is now a kind). Not a weakened subject. | none | Tighten it to "does not belong to block 0". |
| K1V-13 | nit | rules_78b.py job_record (`"oext"`, `"padded_tokens_per_step"` keys) | Block 0's plan.json job records gain two inert keys, `oext: false` and `padded_tokens_per_step: null` (M: block-0 dump diff). Behaviour is the same (check 1). No ruling names the change. | Only relevant if a record pins the hash of a block-0 plan.json written at 3481d85. | None needed. Noted for the lead. |

## Check 1: block 0 is unchanged in behaviour (M)

- `tools/block0_dump.py` ran each tree's own `World` (its tests' synthetic working copy) for both families, base =
  `git archive 3481d85` into `scratch/base/`, under the network-deny sandbox. It ran `init-block 0 --dry-run`, `deal 0`,
  a real `init-block 0` (plan.json), `block0_jobs`, `block_runs(None, "0")`, `deal`, the BLOCK_KINDS / HOST_PREFIX /
  FUNDING_BLOCK / REJUDGED_PINS entries for "0", and the RK CLIs `golden`, `block0`, `e-caps` and `kit`.
  - Byte-identical: the dry-run printout (every need line and idle line), `deal 0`, the real init's stdout, `block0`,
    `golden`, block 0's tables and its "0" entries.
  - plan.json: identical except two inert keys per job (K1V-13).
  - `e-caps`: only the references' caps rose (ref_eval, safe_lora, ref_train_bqi) and a `w1_18` entry was added; none
    is in block 0.
  - `kit`: additions only (the side units' `job_sha256` and the new null pins).
- `tools/block0_pod_side.py`: block 0's pod-side numbers are identical at the base and in K1: `requirements`,
  `cap_hours` (8.5 h / 12.5 h), `pod_spend_usd`, `job_decision` on the synthetic preflight, `check_keys`, and the
  retrain and c0 E pods.
- Launch path:
  - `orchestrate.w1_18_hold` and `plan_tool.gate_g1` read `rules.BANK500_KINDS`, which now holds o_only,
    o_only_with_regenerate, c0, the references and ref_train. It does not hold arm or a0_arm, so block 0 is never held
    (R: orchestrate.py:403; plan_tool.py:824).
  - The runner's `check_keys` call passes no `oext_bank` (R: setup/job_runner_stage1.py:401).
  - The scorer block's o_only, o_only_with_regenerate and c0 pods are now held until a branch record exists. That is
    intended (K-8) and is not block 0.

## Check 2: the block tables (M/R)

- Counts, M (tests plus my reading of `block_runs_78b`; P2 §2.2; P1 §5):
  - Block A: 21 runs per family in every plan.
  - Block B: plan A 23, B9 32, H (b) 47, plus 6 or 12 dose rows at 1102-1104 or 1102-1107.
  - R at 1104-1105 in block A and from 1106 to the last method seed in block B; a0 at 1104, then 1105-1107.
  - A stopped family: block A 12; block B 14 / 26 / 38 (P2 §2.2's I text).
- Hashes, M (`tools/hash_edits.py`, `git show 3481d85:<path> | sha256`, digest only): all 20 R_d4-R_d13 pins and both
  H1 pins equal the committed files. The three OLMo sources are as P2 §2.3 states.
- Llama MANIFEST, M (key read: draw, seed, rows, sha256): R_d4-R_d13 have seed 1100 + d, rows 600 and equal hashes.
- S1 pins, R: they equal P2 §1.9 and §1.17's full hex values (P2:193-194, :406). The two files were not opened.
- Steps and recipes, M (tests): removal arms 33, add arms and a0 38, doses 39; main config "B"; engine X by default.
- K-5's dose table: not built (K1V-2).

## Check 3: steps and caps (M: `tools/caps.py`)

- `steps_for_rows` = ceil(rows / 128). A named arm whose derived steps differ is refused. s4_top takes 38 steps for
  n ≤ 64 and 39 for n ≥ 65 (M; test_24).
- One O-ext pass: 3,958.9 s (OLMo) and 4,061.45 s (Llama); × 1.5 = 5,938.4 s and 6,092.2 s (P2 §4.3: 3,959 / 4,061).
- Four-arm caps with the term at × 1.5: 17.25 h and 19.25 h, at 38 or 39 steps. Without it: 10.5 h and 12.5 h.
- Four-pod need (× 1.25): $167.06 and $185.56. Guards: $37.91 and $41.61.
- At × 1 (filled measured value): 15.0 h / $146.25 and 17.0 h / $164.75. All equal P2 §4.3's table.
- `requirements()` and `job_decision` now take the job's own padded tokens and term (test_25, test_26b). Block 0 is
  unaffected (check 1).
- The references' E caps:
  - ref_eval: OLMo 5.0 → 6.75 h, Llama 5.25 → 6.75 h.
  - safe_lora: 5.5 → 7.25 h and 5.75 → 7.25 h.
  - ref_train_bqi: 4.75 → 6.5 h and 5.0 → 6.5 h.
  - New: w1_18 2.25 h / $10.16 guard. ref_train alone: 6.0 h.
  - These caps are E; P2 takes the values (O12).
- Not covered: steps come from the pin's declared `rows`, not from the edit file's counts. Nothing yet checks the two
  against each other (I; K3's pack should check `counts.add` / `counts.remove` against the pin).

## Check 4: pins (R/M)

- Null and refusing with their filling event (test_38, test_31, test_33/33b, test_37b, the METHOD_EDITS tests; R the
  code): GATE_78B, PLAN_B_78B, N_UNITS[F], OEXT_78B_Y[F], W1_18_78B and the seven null METHOD_EDITS entries.
- Null without refusing, by design: OEXT_TERM_MEASURED_S (null means × 1.5) and ANCHOR_STOP (null means no stop).
- θ0's job hash is filled, not null (K1V-4). There is no branch-record pin (K1V-5).
- GATE_78B holds the corrected O14's fields: option, families, N's provisional plan, the noise reading's SHA-256 and
  the balance. Block A's init reads its families only.
- PLAN_B_78B lacks K-6's fields (K1V-3).
- Never-switch: `branch_switch_problem` is right, but its source and W1-18-hash comparisons are untested (K1V-7).
- Open for the lead (I): GATE_78B accepts provisional plan "review", and block A's init does not read the plan. That
  follows O14 as corrected (block A reads its families only). Whether block A may start under a "review" provisional
  plan (P1 §6.1: "the user decides") is the lead's call.

## Check 5: the seed key, the re-judge list, the anchor stops (M/R)

- Seed key (test_30, M):
  - `sc_units` gives OLMo side a0 1101-1103 and N's R 1101-1103, and Llama side a0 1101-1102, N's R 1101-1103 and
    N's a0-1103.
  - The inputs for N's R_1101 (`n_complete:R:1101`, `regen_edit:R:1101`) and for side a0-1101 differ.
  - SR78 still has a seed-only default (K1V-9). The Llama a0-1103 N_UNITS rule is untested (K1V-7).
- Re-judge list (test_32, M): 7 per family, OLMo 3 + 3 + 1 and Llama 4 + 2 + 1. N's arm, path, COMPLETE and job
  fields are null until N_UNITS is filled, and `rejudged_or_refuse` refuses until then. The form follows the 1B
  REJUDGED_PINS (R: runkit/stage1-olmo/stage1_rules.py:193-229). Import-time fragility: K1V-8.
- Anchor stops (R: scripts/make_anchor_answers.py:37, :41, :121-122, :166-171; test_34):
  - Only exit 3 with a counts line {kept < 64, needed 64}, or exit 1 with the anchored harmful-pair message, is a
    stop. Every other exit or message is a crash.
  - The record is text-free (the failure text is dropped).
  - The stopped family's refusals: rep_pass, l1_scan, classifier, a1_pass and anchor are refused at `check_keys`,
    `job_decision`, the pins and the order. The retrain runs under MAIN_F ("B") with no RECIPE_S and no complete anchor
    job, on Y with ENGINE_Y (AM1 changes 2, 5, 13). The X retrain stays allowed under MAIN_F.
  - The form's names do not match Track S's reader: K1V-1. The pinned record is never read: K1V-6.

## Check 6: tests and mutants (M)

- 7-8B suite, sandboxed: 527 passed in 61 s, exit 0 (M: `sandbox-exec -p "$SB" PY -B -m pytest -p no:cacheprovider -q
  runkit/stage1-78b/tests`; log `suite-78b.log`). This equals the builder's count and the lead's background run (R:
  B/lead/k1-checks/summary.txt: 527; stage-1 kit 762; scale78b 208 + 57 skipped).
- Rules runner, one shard, sandboxed, 15:59:40-16:02:56 UTC: 188 killed, 0 survived, 0 invalid, baseline exit 0 (M:
  `mut-all.json`). The lead's run got the same 188 (summary.txt). Runner spec: 35 killed (lead). The scorer and gated
  specs were not yet in the lead's summary when I wrote this.
- My probe mutants (`tools/make_probe_src.py`: a scratch source root, ws-k untouched; the rules spec plus 16 VFY-*
  mutants; the same runner): 9 killed, 7 survived (K1V-7).
  - Killed: w1-18-host-any, dose-arms-any-name, n-unit-membership-off, rejudged-r-label-plain, harmful-pos-unchecked,
    plan-b-sr2-not-bool, gate-balance-any, oext-bank-null-pin-passes, block-a-dose-allowed.
  - Survived: edit-pin-any-suffix, files-form-any-dir, stop-exit-type-unchecked, gate-version-type-unchecked,
    branch-switch-branch-only, n-units-keys-loose, sc-needed-n-units-any-arm.
- Tests that only restate the code:
  - test_mixed_33_38_39 compares `cap_hours(jobs)` with `cap_hours` of the same function's records.
  - The scorer test's command lines now use the constant, not a literal (K1V-10).
  - Every other new test holds an independent literal from P2 or the rulings: 17.25 / 19.25 h, $167.06 / $185.56,
    the P2 §2.3 hash table, the 21 / 23 / 32 / 47 counts, and the on-disk job hashes.
  - The test_23 aggregator repeats the 19 block-table tests inside the rules file, so the rules runner sees them.
- The small fixes in other test files: no assertion was deleted and no literal loosened in substance (R: the diff).
  - The BLOCKS and REJUDGED_PINS source literals were replaced with the new literals.
  - The A and B cases moved from "block 0 only" to KD7's refusal and still assert a refusal.
  - SC_KINDS gained w1_18.
  - HM14 keeps `files` non-empty; it still asserts "does not list {drop}" for each kind.
  - The fake runner tells the lean job by `--job`.
  - Two mild points: the w1_18 regex keeps a dead branch (K1V-12), and the scorer command lines moved from a literal to
    the constant (K1V-10; the literal is kept in test_37).

## Check 7: the builder's open points against the fourth set

| K1 open point | Ruling | Remains for | K1 defect? |
|---|---|---|---|
| 1 K4bf-m-c0 equivalent | K-1 | K2 (command-word check; re-target, not retire) | no; the scorer spec has 1 survivor until then (K1V-10) |
| 2 plan_tool's 1B route for A/B | K-2 | K2 (before any block-A copy) | no |
| 3 the W1-18 pod's copy | K-3: OLMo's scorer-block copy; [B] both families' settings and units | K2/K3 (pack; the Llama token path) | no; K1's value agrees (comment: K1V-11) |
| 4 idle storage for N's 7 pods | K-4: in the scorer block's printout | K2 | no; block 0's printout unchanged (M) |
| 5 the dose fallback's composition | K-5: K1's tables implement it | K1 | **yes, K1V-2** |
| 6 PLAN_B_78B without SR-2 | K-6: null hashes plus the reason and the plan basis | K1 | **yes, K1V-3** |
| 7 the references' caps rose | O12 (Part 2 takes the values) | the lead (Part 2 text) | no |
| 8 OLMo S1's path in `tmp/stage1-olmo/` | K-7 | K3 (pack by path and hash) | no |
| 9 callers (branch, stop, N_UNITS, gate, plan B, flags, `bank500_problem`) | K-8 and the anchor-stop form | K2 (record steps; a test that the W1-18 hold never applies to block 0; orchestrate should use `bank500_job`, since `BANK500_KINDS` omits arm and a0_arm of blocks A and B), K3 | the anchor-stop form is K1's (**K1V-1**) |

Other points for K2/K3 or the lead (I):
- `BLOCK_KINDS["B"]` lacks `b10_certify` (O2: Track R and K3 build it; SR78 must then list it).
- PLAN_B's plan is never checked against σ̂_A by P1 §6.1 (`plan_code_for`): K2's record step should compute the plan
  from the pinned output.
- N_UNITS' R edit hashes are not checked against the sealed R_d1-R_d3 pins.

## Commands run (foreground unless noted; exit 0 unless noted)

- `date -u` (×4). `cat`, `sed`, `grep`, `git diff`, `git show`, `git log`, `git status` and `git archive 3481d85
  runkit/stage1-78b | tar -x` into scratch (read only).
- `shasum -a 256`: the 12 K1 files, and 7 job.json and 7 COMPLETE.json under MAIN tmp/family-probe-sp-*.
- `python -I -B`: the Llama MANIFEST key read; `tools/hash_edits.py`; `tools/caps.py`; `tools/k5_probe.py`;
  `tools/n_units_import_probe.py`.
- Sandboxed: `tools/block0_dump.py` on both trees; `tools/block0_pod_side.py` (first try exit 1, my helper import;
  fixed and re-run).
- The 7-8B suite, sandboxed (527).
- Rules runner ALL, sandboxed. It moved to the background after 180 s by the tool, and I waited for it: 188 killed.
- Probe runner, 16 ids, sandboxed (exit 1: 7 survived).
- The runners' repo copies were deleted after use; the JSON results were kept.

Evidence in `R/r1-k1-verify-scratch/`: `k1.diff`, `rk.diff`, `sr.diff`, `b0-base.json`, `b0-new.json`, `suite-78b.log`,
`mut-all.json` / `.log`, `mut-probe.json` / `.log`, `tools/`. The scratch kit copies (`base/` from `git archive`, the
`work-*` folders and `probe-src/`) were deleted after use. To rebuild the base tree:
`git -C B/ws-k archive 3481d85 runkit/stage1-78b | tar -x -C <dir>`; `tools/block0_dump.py KIT OUT WORK` re-runs check 1.
