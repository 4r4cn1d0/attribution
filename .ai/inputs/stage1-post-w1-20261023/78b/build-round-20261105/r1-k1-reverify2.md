# R1 K1 follow-ups 1 and 2: adversarial re-verification

I wrote this on 2026-11-08 and read the clock with `date -u` at 18:30 UTC (start) and 18:51 UTC (this text).

Status: **done**. I made no edits in WS.

- **Target.** B/ws-k at `3481d85` plus K1's working tree after follow-up 2. The lead's tenth and twelfth sets (R-22,
  R-24 to R-26, R-29) are in R78/lead-rulings-ab-build-20261108.md:233-292. The ninth set (R-20, R-21) is read with
  them.
- **Hashes.** The 13 K1 files hash to the builder's follow-up tables (M: `shasum -a 256`). That is rules_78b.py
  `dab0218e…`, test_rules_78b.py `dafe66e4…` and the rules spec `eb7515ba…`. The other files carry follow-up 1's
  hashes or the fix round's.
- **The builder's diffs.** `followup.diff` hashes to `3a868ce0…` and `followup2.diff` to `405f1dd9…`; both equal the
  builder's values. My own `diff -ru fixcopy ws-k` shows changes in only the 6 files the builder names
  (`fix-to-now.diff`). `git status` lists the same 13 entries as before.
- **What I wrote.** Only this report and `R/r1-k1-reverify2-scratch/`.
- **What I read.** Track O's ws-o was read only: I ran its maker's print flags, which write nothing. ws-s was read
  only. MAIN was read only.
- **What I did not do.** No pod, spend, network, install, download, agent or message. I opened no sealed, answer,
  generation, judge or prompt file.
- **Tags.** M measured (command), R read (path:line, WS paths unless named), E estimate, I inference.

## Verdict: VERIFIED_WITH_MINOR

R-24, R-29, R-22, R-21, KR2, KR7 and KR8 are closed as ruled. KR3 is closed for the files it scans, but not for every
call form.

- **Block 0:** unchanged. The plan.json bytes equal 3481d85's for both families (M).
- **Tests and mutants:**
  - The 7-8B suite passes: 543 (M).
  - The rules spec: 248 killed, 0 survived, 0 invalid (M).
  - Every find text in the four specs occurs exactly once (M).
- **R-24 cannot be made to accept a plan that disagrees with its basis.** I tried each basis against the gate's
  option, each threshold value, and "review". It is still blind to a wrong value copied into a record (KR2-1). The
  ruling accepts the recorded value, so that is the lead's call.
- **R-29 equals `noise_reading.seed_rule` exactly.** No disagreement on 30,166 σ values, on both sides of every
  boundary, on decimal and binary values (M).
- **Merge.** I would merge, and settle KR2-1 and KR2-3 by ruling, with KR2-2 as a small follow-up or a K2 item.

## Defects

| id | sev | file:line | defect | failure scenario | fix |
|---|---|---|---|---|---|
| KR2-1 | minor | rules_78b.py:1992-2003 (`plan_for_sigma`), :2060-2065, :2135-2140 (`block_init_or_refuse`) | R-24 checks each plan against a value copied by hand into a record. The kit never checks those values against the pinned outputs they come from. `sigma_A_pp` is not checked against blinded_sigma.py's output, which PLAN_B pins by `blinded_sigma_output_sha256`. That output holds `sigma_A_pp` and `inputs_sha256` (R: B/ws-s/scripts/scale78b/blinded_sigma.py:64, :344). The gate's `provisional_plan` and `sigma_F_plan` are not checked against the noise reading's output, which GATE pins by `noise_reading_sha256`. That output holds the pooled `seed_rule` and each family's `seed_rule_by_sigma_F` (R: scripts/scale78b/noise_reading.py:363, :390). M (`tools/r24_probe.py`) accepts four wrong records. (a) The output says σ̂_A 7.2 (H); the record says 4.2 and plan A; it is accepted. (a') The `inputs_sha256` differs from the output's; it is accepted. (b) Under [B] the noise reading says H; the gate says A and PLAN_B says A; it is accepted. (c) The same holds under [C] for `sigma_F_plan`. | One mistyped number in a recorded lead step still plans the wrong block B. That is 23 runs instead of 47 per family (the preregistered design shrinks), or the reverse, about $198 (E, R-24's figure). R-24's text accepts "the σ̂_A it records", so the lead decides. | At block B's init (or in K2's record steps), read the two outputs at their pinned hashes. Then check four things: `sigma_A_pp` and `inputs_sha256` against the blinded output; `provisional_plan` against the noise reading's pooled `seed_rule` outcome; `sigma_F_plan` against OLMo-2-7B's `seed_rule_by_sigma_F` outcome under [C]. Both outputs hold variance estimates and plans, not outcomes (P1 §6.4). |
| KR2-2 | minor | tests/test_rules_78b.py:2583-2611 (`seed_only_calls`), :2613-2632 (test_41b) | KR3's scan does read every non-test kit file: 25 `.py` files, sub-folders included (M; the probe in judge_pod_stage1/bundle.py is killed). It misses three call forms. (1) `from stage1_rules import sc_input_names as f`, then `f(...)`: the alias is an `ast.alias`, which the reference loop never inspects. (2) An explicit arm of None, positional or `arm=None`, counts as "an arm passed". (3) `getattr(rules, "sc_input_names")(...)`. M (`mut-probe.json`): the probes KRV2-seed-only-alias-import, -none-positional, -none-keyword and -getattr all survive. The test's docstring claims "any call form". | A new seed-only caller in one of these forms keeps the suite green. R-16 holds today: only the four call sites exist (M: grep). | Report every `ImportFrom` alias of the two names, and follow its `asname`. Treat a `None` constant in the arm slot, or `arm=None`, as seed-only. Report any string constant equal to either name. Add the four probes to the spec as test-strength probes (mutants that add a caller), or test the scan on a synthetic source. |
| KR2-3 | minor | rules_78b.py:1637-1651 (`files_form_problem`, W1_18_78B's form); B/ws-o/scripts/scale78b/make_oext_settings_78b.py:441-456 (Track O, read only) | The two tracks disagree on W1_18_78B's form (R-20). R-20's pin holds the wrapper and, per family, the W1-18 settings and the side units, each by path and SHA-256. Track O's maker (`--w1-18-78b`) prints `{files, side_units}`. RK accepts exactly `{files}`. M (`tools/forms_probe.py` on Track O's printout): the printed form is refused ("its keys are not exactly files"); its `files` part alone is accepted. | The lead's fill from the printout is refused, which fails safe. Or the lead drops `side_units`, and then the W1-18 pod's files list cannot name the side units from the pin (K3). | Lead's ruling. Either RK accepts Track O's `side_units` block (per family, per unit {path, complete_sha256, job_sha256}, checked against KIT `a0_units`), or Track O prints `files` only. |
| KR2-4 | nit | rules_78b.py:1421-1425 (`OEXT_INDEX_RE`, `W1_18_RECORD_RE`), :1428-1470 | The R-5 and R-21 checks recognise only canonical names. M (`forms_probe.py`, on Track O's real X form for OLMo-2-7B): the check accepts an added W1 index (`OEXT-78B-W1__<F>.json`, own family or Llama's; R-20 gives it to W1_18_78B). It accepts a lookalike index of Llama's in another folder (`scripts/other/OEXT-78B__llama31-8b.json`). It accepts a lowercase `-y` name. It accepts Llama's W1-18 record under `w1-18/`. And the W1-18 record entry's SHA-256 is never tied to the branch record's `w1_18_record_sha256`. | A copy-paste error in a fill passes RK. The wrapper's Mac check on the W1-18 record (R-6) should still catch a wrong record (I). | Count any basename that starts with `OEXT-78B` (any case, any folder) as an index candidate. Require exactly one, at the canonical path, of its own family and engine. Refuse W1 indexes in OEXT_78B and OEXT_78B_Y. Name the record `w1_18_record__<F>.json`. K2's branch step ties its SHA-256 to the branch record. |
| KR2-5 | nit | rules_78b.py:1992-2003 (`plan_for_sigma`) | An integer `sigma_A_pp` too large for a float (for example 10**400) raises OverflowError, not Refused. `plan_b_record_problem` then crashes instead of naming the problem. M (`r24_probe.py` (d), (d')). | Nothing runs, because the error fails closed. The message is unclear. | Catch OverflowError, or bound ints, and return the "finite number" problem. |

## Check 1: R-24 closes KR1 for all three bases (M/R)

The code (R: rules_78b.py):
- **PLAN_B_KEYS** gains `sigma_A_pp` (:1974-1975).
- **Adopted:**
  - `plan_for_sigma(sigma_A_pp)` must equal `plan`; a missing or invalid σ̂ refuses (:2060-2065).
  - The basis must be `sigma_A`, with both hashes.
- **Not adopted:** `sigma_A_pp` must be null (:2074-2075).
- **GATE_78B** gains `sigma_F_plan`: required under [C] (one of A, B9, H, review), null under [B] (:1966-1967,
  :2024-2027).
- **Block B's init** (:2135-2140):
  - basis `sigma_pool_N` needs the plan to equal the gate's `provisional_plan`;
  - basis `sigma_F` needs the plan to equal `sigma_F_plan`;
  - the option check keeps `sigma_F` to [C] and `sigma_pool_N` to [B].

My attempts to get a wrong plan accepted (M: `tools/r24_probe.py`, `r24_probe.log`):
- Basis against option: [B] with `sigma_F` is refused, and [C] with `sigma_pool_N` is refused.
- Thresholds: σ̂_A 6.0 exactly with plan H is refused; with plan B9 it is accepted (correct).
- Review: [C] with `sigma_F_plan` review and PLAN_B review plans nothing.
- R-24's own rows are held by test_43, with every other plan per σ̂ refused.
- Wrong plans got through only as consistent mis-transcriptions: (a), (a'), (b) and (c) in KR2-1.

The R-24 mutants are all killed by test_43 (M):
KF-m-sigma-a-plan-any, -sigma-a-threshold, -sigma-a-unchecked-value, -sigma-a-null-without-sr2, -pool-plan-any,
-sigma-f-plan-any, -gate-c-no-sigma-f, -gate-b-sigma-f-any.

## Check 2: R-29's ceiling equals noise_reading.py's seed rule (M: `tools/ceiling_probe.py`)

- **Method.**
  - I loaded `scripts/scale78b/noise_reading.py` read only, by path, from ws-k (it loads its pinned
    gate_b_reading itself). Its SHA-256 `94b679ff…` equals MAIN's and 3481d85's.
  - `PLAN_MDE_FACTORS == noise_reading.MDE_FACTOR` (1.4207 / 1.0785 / 0.9340), and `SESOI_PP` is 5 in both.
- **Values tried, 30,166 in all.** Around each boundary (4.5, 6.0, and the ceilings 10/1.4207, 10/1.0785 and 5000/467
  = 10/0.9340) I tried:
  - the nearest float and ±6 ulps;
  - decimals at ±10^-3 … ±10^-12;
  - a grid from 0 to 30 in steps of 0.001.
- **How each was compared.** `noise_reading.seed_rule` was given a one-term Sigma ((σ²,),). The σ was taken two
  ways: (i) σ's decimal value, `Fraction(repr(x))`, which RK compares, and (ii) σ's binary or exact value.
- **Result.** No disagreement with `plan_for_sigma` in either reading.
- **H (b)'s ceiling.** The nearest float, `10.70663811563169`, lies below 5000/467 in both its binary and its decimal
  value, and RK gives H.
- **Invalid σ.** NaN, inf, -0.1, True, "4.5" and None are each refused.
- **Equivalent mutants (I, backed by M).** KRV2-ceiling-binary (`Fraction(sigma_pp)` in place of
  `Fraction(repr(…))`) and KRV2-ceiling-h-factor-everywhere (H's factor for every plan) both survive. No test can kill
  them: the sweep shows no float on different sides of any boundary in its two values, and the A and B9 ceilings
  cannot fire (σ ≤ 4.5 and σ ≤ 6.0).
- The builder's KF2-m-no-review-ceiling, -ceiling-factor-h and -ceiling-ge are killed (M).

## Check 3: R-22 and R-21 (M: `tools/forms_probe.py` on Track O's own printouts)

- **Track O's printouts.** I ran Track O's maker (`B/ws-o/scripts/scale78b/make_oext_settings_78b.py`, SHA-256
  `6cd317a0…`; `--oext-78b F`, `--oext-78b-y F`, `--w1-18-78b`; print-only flags, exit 0). Its four X and Y forms went
  through RK's `oext_form_problem` for every family and engine pair. Each form is accepted for its own family and
  engine, and refused for the other three (16 checks).
- **K1's old name.** `oext_index__` counts as no index (test_44; KF-m-index-old-name killed).
- **The W1-18 record (R-21).**
  - Accepted: one plain `.json` directly under `.ai/inputs/stage1-post-w1-20261023/78b/w1-18/`.
  - Refused: a second record, a sub-folder, a `.txt` name, a `../` path, `w1-18x/`, and another `.ai/` folder.
  - KF-m-w1-18-records-many, -record-any-form and -folder-any are killed, and so is my KRV2-w1-record-regex-loose.
- **Residuals.** The lookalike and other-family names are KR2-4. The W1_18_78B form mismatch is KR2-3.

## Check 4: KR2, KR3, KR7, KR8 (M/R)

- **KR2: closed.** test_45 holds needed ≠ 64, of ≠ 64, `prompt_index` 64 and -1, and non-SHA-256 `job_done` values.
  The four KF-m mutants are killed.
- **KR7: closed.** A filled s4_top pin of 120 rows is ignored at kept 48, 96, 192 and 250 (test_45). The branch
  record's utc and recorded_by are checked. KF-m-top-pin-any-arms and KF-m-branch-texts are killed.
- **KR8: closed.**
  - `job_done_sha256` is required, with no default (R: :2253).
  - None or a non-SHA-256 refuses before any bytes are read (`_ANCHOR_STOPS_READ` stays empty).
  - A call without the argument is a TypeError (test_45).
  - KF-m-stop-read-jobdone-optional is killed.
  - No kit code calls `anchor_stop_or_refuse` yet (M: grep).
- **KR3: closed for files, not for call forms.**
  - The scan reads every non-test `.py` file under the kit: 25 files (M), sub-folders included (the
    KRV2-seed-only-subfolder probe is killed).
  - It sees attribute and bare-name calls.
  - It misses `from … import … as`, an explicit None arm, and getattr (KR2-2).
- **R-16 today (M: grep).** The only non-test callers of the seed-only form are plan_tool.py:1306, pack_setup.py:432
  and setup/job_runner_stage1.py:466 and :483.
- **R-26: written.** RULES-78B.md now holds "K2's and K3's acceptance items from R1": KR4, KR5, KR6 / K-1, K-8, the
  kept count read from the dose record, R-16 and R-18 (R: the RULES-78B.md diff).

## Check 5: block 0, tests, specs (M)

- **Block 0's plan.json** (`tools/plan0_only.py`; a fresh World from each tree's own harness, a real init, the clock
  fixed, the path normalised). The base tree is `git archive 3481d85`.
  - OLMo-2-7B: 14,106 bytes, `263e2541…915bf`.
  - Llama-3.1-8B: 14,605 bytes, `ceff0761…78555`.
  - Both are equal in ws-k, and `cmp` finds them byte-identical.
  - The keys `oext` and `padded_tokens_per_step` are absent.
- **The rest of block 0** (`tools/b0cmp.py` and `b0diff.py`, clock 2026-12-01, both families): 32 of 34 compared
  fields are identical. These cover the dry run, deal, real init, tables, entries, `golden`, `block0` and the pod
  side (requirements, caps, spend, `job_decision`, `check_keys`, the E pods). The two that differ are the CLI outputs
  `e-caps` (only the references, plus `w1_18`, as before) and `kit` (additions only, as before).
- **No weakened test.**
  - The removed lines in test_rules_78b.py are literals rewritten for the new fields. Examples: `sigma_F_plan` and
    `sigma_A_pp` in `gate_doc` and `plan_b_doc`; the anchor-stop calls now pass `done`; test_41's old 7-file count
    was replaced by the AST scan. test_33b's "review" case moved to a review gate with basis `sigma_pool_N`.
  - test_block_tables_78b.py only gains the two new fields.
  - test_scorer_block_78b.py only renames its X index to Track O's name.
  - The rules spec only adds mutants: 225 → 248, none removed, the old ones unchanged.
- **7-8B suite** (network-deny sandbox, 18:39-18:41 UTC): **543 passed** in 121.8 s, exit 0 (`suite-78b.log`). No
  `__pycache__` was left under runkit/ or scripts/.
- **Rules spec, in shards** (sandboxed): 124 killed (18:41:45-18:45:11), 62 killed (18:45:33-18:47:19) and 62 killed
  (18:47:29-18:49:40). That is **248 killed, 0 survived, 0 invalid**, with baseline exit 0 each time (72 passed). The
  first shard was moved to the background by the tool after 180 s; I waited for its notification. Every killing test
  is a real failure; the KF and KF2 mutants fall to test_43 to test_46 and test_07c.
- **Find texts:** each occurs exactly once in its file. Counts: rules 248, runner 35, scorer 155, gated 128. No
  duplicate ids, and no mutant whose find equals its replace.
- **My probes** (`tools/make_probe_src.py`; the spec plus 8 KRV2-* appended; a scratch copy): 2 killed (subfolder,
  w1-record-regex-loose), 6 survived. Four of the survivors are KR2-2; the other two are equivalent (check 2).

## Commands run (foreground unless noted; exit 0 unless noted)

- **Reading and hashing.** `date -u` (×7). `cat`, `sed`, `grep`, `awk`, `find`, `ls`, `diff -u` / `-ru`, `cmp`,
  `shasum -a 256`. `git -C ws-k status` and `archive 3481d85 runkit/stage1-78b | tar -x` into scratch (reads only).
- **Track O's maker, sandboxed:** `--oext-78b` and `--oext-78b-y` for both families, and `--w1-18-78b`. Output went to
  scratch; it holds paths and hashes only.
- **`/usr/bin/python3 -B -I`:** `make_base.py`, `b0diff.py`, `find_once.py`, `make_probe_src.py` and inline readers.
- **Sandboxed, PY:**
  - `ceiling_probe.py`, `forms_probe.py`, `r24_probe.py`, `plan0_only.py` (×2), `b0cmp.py` (×2), an inline
    W1-18-record probe;
  - the 7-8B suite (543);
  - the rules runner in 3 shards (248 killed);
  - the probe runner (exit 1: 6 survived).
- I deleted the scratch kit copies after use (`base/`, `probe-src/`, the runners' `*-work/`, the World trees).

Evidence in `R/r1-k1-reverify2-scratch/`:
- `fix-to-now.diff`, `suite-78b.log`;
- `mut-rules-{1,2a,2b}.json` / `.log` and `mut-probe.json` / `.log`;
- `r24_probe.log`;
- `forms/` (Track O's printed forms: paths and hashes only);
- `b0-{base,new}.json` and `work/p0-{base,new}/plan0-*.json`;
- `tools/`.
