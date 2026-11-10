# Verify C: adversarial check of track C (recipe-S_78 maker, noise reader, Llama G1 check)

Started 2026-11-05 14:12 UTC; written 14:29 UTC (M: `date -u` read at 14:12:13, 14:27:48 and 14:28:46 UTC).

Verifier worktree: /Users/spiderishi/Coding/attribution/.claude/worktrees/pensive-stonebraker-bf6d79 (HEAD e5e9597; nothing written there).
Builder workspace (read only by me): /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-c (detached at fb51421).
Builder report: /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/build-C.md
My scratch (scripts and their outputs): /private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports/verify-C-scratch/

Tags: M measured (with command), R read (path:line), E estimate (basis), I inference.

## 0. Verdict: VERIFIED_WITH_MINOR

Every claim in the builder's report that I tested holds (M). The code is correct where I could check it by
independent computation, by reading and by mutation. The one acceptance criterion the builder marks "fail" (the two
S_78 configs exist) is indeed unmet, for the reason the builder gives, and I confirm that reason (section 3). It is
not a builder defect; it needs the lead's ruling. The minor defects are test gaps and one rounding inconsistency in
the review ceiling's printed MDE (section 9). No blocker.

What I did not do: run the noise reader on 7-8B R units (none exist); run the engine-codec test with stand-in configs
(the builder's worktree is not mine, and my worktree is at a different commit: fb51421 is not an ancestor of e5e9597,
42 files differ under experiments/ and scripts/; M). The "+2" count claim is settled by reading instead (section 3).

## 1. Files changed

None in any worktree. I wrote only this report and the scratch files under verify-C-scratch/ (listed in section 7).
The builder's worktree is unchanged by me: `git -C ws-c status --porcelain` before and after my work lists the same
three new paths and nothing else (M). No `__pycache__` under ws-c/scripts/scale78b or ws-c/experiments after my
test runs (M, `find` → 0).

## 2. Governing documents read

- The lead's rulings (R, whole file): rulings 1-3 (S-P; the seed rule with 4.5 / 6.0 inclusive thresholds, the
  review ceiling "removal MDE exceeds 2 × SESOI", SR-2 and `blinded_sigma.py` not in this round), 6 (TC does not
  run), 7 (the seven engine-X units, pinned by COMPLETE.json SHA-256), 10 (the a0-1101 retrain under recipe S_78 on
  Y), 11 (KD8: configs committed by explicit path; the anchor job in block 0's kit subset), 14 (the G1 check's output
  under `.ai/inputs/stage1-post-w1-20261023/78b/`), 15 (this round: C = T5, T6a, the Llama G1 check).
- The plan T5 and T6 (R: 78b-readiness.md:280-316) and the check's corrected list items 4 (T6a) and 5 (T5)
  (R: 78b-readiness-check.md:247-253).
- P78 §3.3-3.4 (R: :114-128: r_F,j, σ̂_F on 2 df, σ̂_pool = max(√[(2 SD(r_O)² + 2 SD(r_L)²)/4], median of the 6 pair
  SEs) on 4 df, s_arm, the fallback), :272 (the Llama G1 risk and the $0 check), :291 (input keys), :345 (T5's
  parity values), :377 ("an anchor job per family"), :74-78 (the reuse conditions), :46-58 (the units' hashes).
- Gate B PRE (R: 2026-10-08-gate-b-olmo-preregistration-DRAFT.md:124-129 the noise formulas; :147 G1: "≤ 5% capped
  and ≤ 10% failing the coherence screen, with the short-answer clause. A short-answer TOO CLOSE … counts here as a G1
  failure").
- The frozen readers (R): scripts/gate_b_reading.py (4638a0f0…; `variance` :288, `median_term` :363, `arm_record`
  :374, `arm_from_unit` :433, `pair_se2` :457, `Reader.reading` :510, `noise_gate` :757, the exact comparisons
  :319-360, `compared_fields` :113), scripts/family_probe_reading.py (88483401…; `clustered_se2` :358, `counts`
  :367, `answers_end_bar` :495), the frozen bars file (c0b6f2aa…: capped ≤ 0.05, screen ≤ 0.10, min tokens 5,
  short-answer tokens 5). Hashes measured in the main checkout equal the builder's pins (M, `shasum`).

## 3. Item 1: the recipe-S_78 maker and the two configs

**What I measured (M, `verify-C-scratch/config_check.py` under the main venv with `-I -B`; output in
`config_check_out.txt`).**
- The 1B pair: REC `study-kt-olmo2-1b-r64-b-mb4-20261008` config_sha256 9e9bde6f…, S `…-gateb-20261008` ceffe0ef…;
  both training identity f46279e5…; their diff is exactly {attribution.checkpoints, attribution.query_bank, name,
  purpose}. S's query_bank is `anchors-2cf96336…`, equal to `.ai/inputs/gate-b-anchors-20261008/out/anchors.sealed.json`
  `anchor_file_sha256` (keys read, no text).
- The two main configs by the engine's own `config_sha256` / `training_identity`: OLMo-2-7B
  18cc31d7117a2de7bc02382fe8a4d409fc43c91b434bf219a4808dfb26528d09 / 36738c3823fae7eaca625cc9f619e98c7e40b9bb64e5d0e234412827d3371ec6;
  Llama-3.1-8B 74758af1791d9f7a8ce616adce7549b5b7b0619e55310158d7e21197ed129893 / 5b4451e1487fb2200a5b2b151de2e68397117099a429654484146b3cc3791287.
  Equal to the builder's pins and P78:76. Both main configs' `attribution` blocks equal the 1B REC's (checkpoints
  [q, e1, e3], query_bank "ref", the same dtype and variants), so nothing model-specific lives in the block S_78 changes.
- The maker run by me with a synthetic anchor hash (`ab`×32) into my scratch folder, both families: exit 0; the
  engine's `load_recipe` accepts both files; each differs from its main config in exactly the 1B pair's four paths;
  training identity equals the main config's; key order kept; indent 2 (OLMo) and 4 (Llama) as the main configs
  (M). The synthetic outputs are in `verify-C-scratch/s78-out/` and are NOT 7-8B values.
- The builder's tests: 12 passed under the main venv (part of the 32 passed, 2 skipped run; M, exit 0).
- Mutations on scratch copies (section 6): checkpoints [q, e1, e3], the `anchor-` prefix, an unchanged name, the
  main-config pin not checked and an upper-case hex all KILLED; only the redundant field-set guard (K5) survives,
  which is fine (the set is produced by construction and asserted by the tests).

**The unmet criterion, confirmed (R, M).** S_78's fourth field is `anchors-<SHA-256 of the family's anchor file>`.
`scripts/make_anchor_answers.py:1-18` (R) runs the recipe's own policy untuned and keeps its first 64 Safe answers, so
the file is per model; P78:377 (R) says "an anchor job per family"; ruling 11 puts the anchor job in block 0 (R).
`.ai/inputs/` holds one anchor record, Gate B's 1B one (M, `ls`). `experiments/safety_selection/jobs.py:179-181` (R)
hashes the anchor file at the attributes job and refuses a mismatch, so a placeholder would pass `validate_recipe`
(M: the maker's synthetic file loads) and fail on the pod. The builder is right: neither S_78's bytes nor its
config_sha256 can be known at $0 today. Writing no file was the correct choice.

**A consequence the builder did not draw (I from R).** Ruling 10 runs each family's a0-1101 retrain "train only,
recipe S_78" as the first Y job, and the check's calendar puts that retrain pod on the day the money arrives, before
the anchor pods ("(b) The retrain pod on Y … (d) Then the scorer and anchor pods"). S_78 cannot exist before the
family's anchor job, so that order does not work as written. Either the anchor job runs first (anchor job → S_78 →
retrain), or the certificate retrain runs under the main config (same training identity 36738c38… / 5b4451e1…, so the
q and e1 fingerprints are the same test) and the S_78 retrain for A1's states follows the anchor job. This is a lead
ruling, listed in section 10.

**The "+2" claim (R, M).** `experiments/safety_selection/tests/test_ss_family_codec.py:165` asserts
`family_recipes == 59 + 9 + gate_b_s.exists()`, counting recipes whose names start with `study-kt-olmo2-`,
`study-kt-llama3` or `study-kt-olmo3-`. The configs folder holds 69 such files now (M, `ls | grep -c`), so the two
S_78 files make 71 and the count needs +2 when they are committed. The builder's measured 71 == 69 is consistent.
The four config-enumerating engine test files pass as the tree stands: 203 passed, 2 skipped, exit 0 (M, run by me
in ws-c; `verify-C-scratch/pytest-engine-4files.txt`).

**A trap in the builder's tests (R).** `test_the_s78_configs_are_not_in_the_configs_folder_until_a_family_anchor_job_has_run`
asserts that no S_78 file exists under configs/. Under route (A) it fails the day the lead commits the configs. It
must be removed or conditioned on the anchor record at that time (defect D3).

## 4. Item 2: the noise reader

**Independent parity (M, `verify-C-scratch/sigma_recompute.py`, stdlib, `-I -B`; output in `sigma_recompute_out.txt`).**
My script reads only `guard_samples.jsonl` (fields valid, safety, prompt_id) and `summary.json` of the six wave-0a
units (Gate A a0 1101-1103 under tmp/family-probe-olmo2-1b*, R_1-R_3 under tmp/gate-b-olmo/retrieved/w0a-1); it
never opens samples, generations or any text; it prints aggregates only. Results: U(a0) 46.6667 / 46.8333 / 51.3333
pp, U(R) 46.0000 / 44.3333 / 47.0000 pp (600 answers, 200 prompts each); r_j 0.6667 / 2.5 / 4.3333 pp, mean 2.5, SE
1.0585; SD(r) 1.833333; seed-matched pair SEs 1.1805 / 1.2929 / 1.2793, median σ_eval,0 1.279264; σ̂_gate 1.833333.
Fallback: √2 × SD(U_R) 1.905159; R-R pair SEs 2.1624 / 2.0038 / 2.1574, median 2.157402; σ̂_gate 2.157402. Per-arm
SD of U: a0 2.6475, R 1.3472; s_arm 2.1005 on 4 df. Rounded: **1.83, 2.16, 1.28**. Float-exact equality with the
committed `research/experiments/2026-10-16-gate-b-wave0-outputs/noise-gate-wave0a.json` (SHA-256 4b817f73…) for
plain σ̂_gate, σ_eval,0, fallback σ̂_gate and fallback SD(r): True ×4. The builder's numbers are reproduced by an
implementation that shares no code with the frozen reader.

**Formulas, by reading (R) and by a numeric check of the builder's own function (M).**
- r = U(a0, j) − U(R_j, j): the frozen `Reader.reading` (:536) computes it; the builder never recomputes it. Sign right.
- σ̂_F = max(SD(r), σ_eval,0), 2 df: the frozen `sigma_gate` tuple; `median_term` of 3 pair SE² is the middle one (:363).
- σ̂_pool: `pooled()` (noise_reading.py:351-366) = max(√[Σ 2 SD(r_F)² / (2k)], median of the k × 3 governing pair
  SEs), df 2k; s_arm = √(Σ SS / Σ df). On synthetic k = 2 inputs (SD(r) 4 and 2; SEs 1,2,3 and 4,5,6; arm SDs 6,3 and
  1,1): √P_pool 3.1623 (expect √10), median SE 3.5 (the mean of the two middle of six), σ̂_pool 3.5, s_arm 3.4278 on
  8 df, df 4, plan A: all as expected (M, `mutate2.py`). A median-governed case (SEs 7-12 → 9.5 → H) and a review case
  (SD(r) 11 both → σ̂_pool 11.0 → "review", MDE 10.274) behave as ruled. No wrong df, no wrong median, no wrong weights.
- The thresholds (M, `read_unit_78b.py`): 4.4999999 and 4.5 → A; 4.5000001 → B9; 5.9999999 and 6.0 → B9; 6.0000001 →
  H. Inclusive and exact, as ruling 3 states (σ̂ ≤ 4.5; 4.5 < σ̂ ≤ 6.0; > 6.0). A two-term median exactly 6.0 reads B9;
  an SD term exactly 36.0 (σ 6.0) reads B9.
- The review ceiling (M, `constants_check.py` with scipy): factors 1.420654 / 1.078534 / 0.934038 against the pinned
  1.4207 / 1.0785 / 0.9340 (within 5e-5); ceilings 10/factor 7.039009 / 9.271848 / 10.706208 against the pinned 7.0390
  / 9.2718 / 10.7062 (within 5e-5). MDE at 4.5 is 6.39 and at 6.0 is 6.47 (CALC's). The OC row σ 4.5, 4 df → 59.4 /
  27.6 / 13.0 % (CALC `rule_oc2_out.txt`). The ceiling can bind only in H (7.04 > 4.5, 9.27 > 6.0).
- **One inconsistency (D2, minor).** `review` compares σ̂ with the pinned ceiling 10.7062 (from the unrounded factor),
  while the printed `removal_mde_pp` multiplies by the pinned factor 0.9340 (10/0.9340 = 10.70664). For σ̂ in
  (10.7062, 10.70664) the output says review = True while its own printed MDE is below 10 (M: σ̂ 10.7064 → review True,
  MDE 9.99978). A band of 4e-4 pp; negligible in practice, but the record should not contradict itself.

**Refusals (M).** Through the builder's `read_unit` directly: all five 7-8B a0 units of P78 §2.1 are ACCEPTED under
their families with engine X (COMPLETE.json hashes 21427715…, b0c99f7b…, 4a6d9ebc…, 43e8412d…, 4b5bd06d…; lock
7e0dd998…; a guard record on each; OLMo a0-1101 recorded as resumed from 632fa4bd…, the untuned unit); within each
family `environment_differs` against a0-1101 is empty for every unit (so N's environment trigger will not fire on the
a0 side). A Llama unit under olmo2-7b refuses on the manifest; an a0 unit fed as R refuses on the arm; Gate B's R_1
fed as a0 refuses ("an a0 unit's arm must be a0"); the wave-1 unit-removal arm fed as R_1 refuses with "the edit
file is not the R draw 1 of the family's manifest (only a0 and R units are N's inputs)" (its edit.json provenance:
family "unit", draw None; SEAL's R_d1: family "R", draw 1; fields read, no rows). The 1B-in-7-8B test refuses OLMo by
training identity and Llama by manifest, as the builder says. The wave-1 test did run (22 passed, no skip, under
.venv; M).

**Blinding (M).** The output and the printed summary carry no `U` key and no string over 160 characters (the
builder's walk, re-run by me through the tests); r_j, SDs and SEs only, as Gate B's own output does. `shown()` and
`family_reading()` read U internally and write none.

**Frozen code reuse (M).** Import by path with SHA-256 pins; the pins equal the main checkout's hashes; `git status`
in ws-c shows no tracked file changed. No `blinded_sigma.py` (ruling 3).

**Tests (M).** 22 passed under .venv (scipy present); 32 passed, 2 skipped (scipy) under the main venv; exit 0 both.

## 5. Item 3: the Llama G1 check and its record

**The record (M, printed aggregates and a text walk).** `.ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json`
SHA-256 895a5469cc9efe81607340e92acf35957b02e94e765b78f7edab639c6cb063fe; the units file 233fa4b745a069b5…. Per unit:
path, COMPLETE.json and job.json SHA-256, engine, recipe, arm, seed, target e1, the sampled counts, the shares, the
bars, the answers-end verdict and G1. Keys: no `U`, no `text`; no string over 260 characters or with a newline (my
walk). The builder's report build-C.md carries counts and hashes only (read in full). The record's COMPLETE.json hashes
equal P78 §2.1's (R: :48-57).

**Counts, verified against the family-probe readings' own records (M).** Gate A 1101: 600 / 2 / 42 / 34, without
short 566 / 8 = `tmp/family-probe-olmo2-1b/reading-olmo.json` `bars_read.answers_end.per_seed[0]`. Llama 1101:
600 / 6 / 42 / 20 pass and Llama 1102: 600 / 7 / 63 / 43, without short 557 / 20, "too close" =
`tmp/family-probe-sp-llama31-8b-b5e5-seed1102/reading-llama31-8b-b5e5-1101-1102-nojudge.json` per_seed[0] and [1].
FOCUS (R: research/FOCUS.md:223) records "capped 6 and 7, incoherent 42 and 63 of 600" for these two seeds. So the
"63 of 600 (10.5%)" is the frozen screen count (`counts()["sampled"]["incoherent"]`, family_probe_reading.py:373-376,
:420), and the frozen `arm_from_unit` refuses unless its own re-implementation agrees (gate_b_reading.py:449-452); it
did not refuse. Right bank: every unit's job.json has evaluate_bank dev, split dev, role development, target e1 (M).

**The rule as PRE states it (R, M).** `answers_end_bar` (family_probe_reading.py:495-505): PASS if capped/n ≤ 0.05 and
incoherent/n ≤ 0.10; else TOO CLOSE if, without the short answers, both hold; else FAIL. Llama 1102: 63/600 = 10.5% >
10% → not PASS; 20/557 = 3.6% and 7/557 = 1.3% → TOO CLOSE. PRE:147: a short-answer TOO CLOSE is a G1 failure.
`g1_of` maps PASS → pass, TOO CLOSE → fail ("short-answer TOO CLOSE"), FAIL → fail (M: the unit test and the G1
mutant that counts TOO CLOSE as pass is KILLED). So **Llama-3.1-8B a0-1102 fails G1 as reused; a0-1101 passes; the
three OLMo-2-7B a0 units pass (23, 20, 16 of 600)**. The builder's reading stands.

**Parity (M).** No adapter exists: `arm_from_unit` reads `eval/<target>` of the family-probe layout directly, so
"feeds the same arrays" reduces to the frozen function reading the frozen files; its own parity check against
`counts()` ran without refusing on all seven units. On wave-0a R_1 at 1101 the record says pass and the sealed
`gate_b_verdict.json` has `R_G1_failed []` and `diffuse.G1_failed_arms []` (M).

**What the G1 check does not do (I).** It records each unit's COMPLETE.json SHA-256 but does not key its inputs by it
(the units file lists id, family, path). P78:291's keying rule names the two readings (items 5 and 6), not this
check, and the acceptance asks for the hash in the record, which is there. Not a defect; noted.

## 6. Mutation checks on scratch copies

Harness: `verify-C-scratch/mutate.py` and `mutate2.py` (M; outputs `mutate_out.txt`, `mutate2_out.txt`). Each mutant
is one replacement in a fresh copy of ws-c/scripts/scale78b under a scratch root that reaches the frozen readers, the
engine and the research records by symlink; the relevant builder tests run with `-B`, `-p no:cacheprovider`; KILLED =
pytest exit non-zero. Baselines: 22 passed (.venv), 12 passed (main venv).

| Mutant | Result |
|---|---|
| N1 threshold A exclusive (<) | KILLED |
| N2 threshold B9 exclusive (<) | KILLED |
| N3 review sign flipped | KILLED |
| N4 pooled divisor 2k → k | **SURVIVED** (σ̂_pool's value is asserted nowhere) |
| N5 pooled median over one pair only | **SURVIVED** (same) |
| N6 s_arm with n instead of n − 1 | **SURVIVED** (s_arm's value is asserted nowhere) |
| N7 training-identity refusal removed | KILLED |
| N8a R family check removed (draw check kept) | SURVIVED (the draw check still refuses; fine) |
| N8c R family AND draw checks removed | KILLED (the method-arm test fails: DID NOT RAISE) |
| N9 MDE factor H 0.9340 → 0.9000 | KILLED |
| N10 χ² closed form off by one term | KILLED |
| N11 σ̂_F df 2 → 3 | KILLED |
| N12 pooled df 2k → k | KILLED |
| N13 fingerprint trigger dropped | KILLED |
| N14 governing reading always plain | KILLED |
| N15 fresh-R (no resume) check removed | SURVIVED (no resumed R unit exists to test) |
| N16 seed check removed | KILLED |
| N17 parity family pooled with a tier family allowed | SURVIVED (no test) |
| G1 TOO CLOSE counted as a G1 pass | KILLED |
| G2 manifest check removed (G1 check) | SURVIVED (the training-identity check fires first) |
| G3 training-identity check removed (G1 check) | KILLED |
| K1 checkpoints [q, e1, e3] | KILLED |
| K2 query_bank prefix `anchor-` | KILLED |
| K3 name unchanged | KILLED |
| K4 main-config hash pin not checked | KILLED |
| K5 field-set guard removed | SURVIVED (redundant guard; the tests assert the set) |
| K6 hex check accepts upper case | KILLED |

The three survivors that matter (N4, N5, N6) are test gaps, not code errors: section 4's numeric check of `pooled()`
shows the formula is right. They are defect D1 (minor) with a one-test fix.

## 7. Commands run (every one, with exit status)

Read-only, all exit 0 unless noted: `date -u` ×3; `ls`, `wc -l`, `grep`, `sed -n`, `cat`, `shasum -a 256`, `find` over
the sources named here; `git -C ws-c status --porcelain [--ignored]`, `git rev-parse`, `git log --oneline -1 fb51421`,
`git merge-base --is-ancestor fb51421 e5e9597` (exit 1: not an ancestor), `git diff --stat fb51421 e5e9597 -- experiments scripts`
(42 files); `.venv/bin/python -I -B -c` one-liners that printed JSON keys, ids, hashes and counts of job.json,
identity.json, assets.json, COMPLETE.json, the two reading records, the sealed verdict, anchors.sealed.json (keys), the
wave-1 and SEAL edit files' provenance fields, the first-record keys of guard_samples.jsonl and samples.jsonl (keys
only). One `grep FOCUS.md` in the wrong folder printed "No such file" (redone on research/FOCUS.md).

Builds, tests and scratch scripts (M):
1. `PYTHONDONTWRITEBYTECODE=1 <main venv>/python -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/ -rs` in ws-c → 32 passed, 2 skipped (scipy), exit 0.
2. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider scripts/scale78b/tests/test_noise_reading.py scripts/scale78b/tests/test_g1_check_78b.py -rs` in ws-c → 22 passed, exit 0.
3. `.venv/bin/python -I -B verify-C-scratch/sigma_recompute.py` → exit 0 (section 4).
4. `PYTHONDONTWRITEBYTECODE=1 <main venv>/python -I -B verify-C-scratch/config_check.py` → exit 0 (runs the maker twice as a subprocess with `-I -B`, both exit 0; section 3).
5. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I -B verify-C-scratch/read_unit_78b.py` → exit 0 (section 4).
6. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I -B verify-C-scratch/constants_check.py` → exit 0 (section 4).
7. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I -B verify-C-scratch/mutate.py` → exit 0; 27 mutants (section 6).
8. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I -B verify-C-scratch/mutate2.py` → exit 0 (N8c and the pooled() check).
9. `PYTHONDONTWRITEBYTECODE=1 <main venv>/python -B -m pytest -q -p no:cacheprovider experiments/safety_selection/tests/test_ss_family_recipes.py …test_ss_family_codec.py …test_ss_family_reading.py …test_ss_headroom.py --ignore=…test_ss_gateb_runkit.py` in ws-c → 203 passed, 2 skipped in 12 s, exit 0.

No command ran over 15 seconds. No background job. No pod, spend, network, install, download, agent or message.
Forbidden folders and files: none opened (no tmp/hlc*, tmp/v3-prepared, tmp/stage1-olmo, tmp/stage1-mac-runs-20261023,
tmp/stage1b, selector.jsonl, hidden/; no judge, answer, generation or prompt-text file except guard_samples.jsonl's
label fields in my own parity script, as the track allows, with aggregates printed only; samples.jsonl was opened only
to print its key names).

## 8. Evidence paths

- My scratch: verify-C-scratch/{sigma_recompute,config_check,read_unit_78b,constants_check,mutate,mutate2}.py and
  their `*_out.txt`; pytest-mainvenv-all.txt, pytest-dotvenv-noise-g1.txt, pytest-engine-4files.txt; s78-out/ (the two
  synthetic-hash S_78 files: not 7-8B values; delete after the lead reads this).
- Builder files verified (ws-c): scripts/scale78b/{make_recipe_s78.py 5b08c3ed…, noise_reading.py 6cde1a24…,
  g1_check_78b.py 251ddb32…, tests/*}; .ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105{,-units}.json
  (895a5469…, 233fa4b7…) (M, `shasum`, equal to the builder's table).
- Read-only sources: the main checkout's scripts/gate_b_reading.py (4638a0f0…), scripts/family_probe_reading.py
  (88483401…), scripts/killtest_stage0_reading.py (1740663b…), experiments/safety_selection/{config.py:639-650,
  jobs.py:168-186, tests/test_ss_family_codec.py:155-165, configs/*}, scripts/make_gateb_recipe.py:1-25,
  scripts/make_anchor_answers.py:1-25, research/experiments/2026-10-16-gate-b-wave0-outputs/{noise-gate-wave0a,gate_b_verdict}.json,
  research/review/2026-10-17-icml-78b-prep/calc/rule_oc2{.py,_out.txt}, research/FOCUS.md:223, the unit folders and
  reading records named in sections 4 and 5.

## 9. Defects

| Id | Severity | Where | What | Fix |
|---|---|---|---|---|
| D1 | minor | ws-c/scripts/scale78b/tests/test_noise_reading.py | No test asserts σ̂_pool's value, the pooled median or s_arm (mutants N4, N5, N6 survive). σ̂_pool is the number the seed rule reads at the tier. The formula is right (section 4), but a later edit could break it unseen. | Add one test of `nr.pooled()` on synthetic `_exact` inputs with k = 2 (my `mutate2.py` block gives the inputs and expected values: √P_pool √10, median 3.5, σ̂_pool 3.5, s_arm 3.4278 on 8 df, df 4; a median-governed case; a review case). |
| D2 | minor | ws-c/scripts/scale78b/noise_reading.py:277, :282 | `review` uses the pinned ceiling (from the unrounded factor); the printed MDE uses the pinned rounded factor. For σ̂ in (10.7062, 10.70664) the record says review = True with its own MDE < 10 (M: σ̂ 10.7064 → MDE 9.99978). | Decide review with the same pinned factor: `review = not GB.ge(2 * SESOI_PP, ex(MDE_FACTOR[plan]), sigma)` (GB.ge takes a factor), and derive or drop CEILING_SIGMA_PP; update the ceiling test to the exact boundary 10/0.9340. |
| D3 | minor | ws-c/scripts/scale78b/tests/test_make_recipe_s78.py:135-140 | `test_the_s78_configs_are_not_in_the_configs_folder_until_…` fails the day the S_78 configs are committed (route A). | Delete it, or make it conditional: skip when a family's anchor record exists under .ai/inputs. |
| D4 | minor | ws-c/scripts/scale78b/tests/test_noise_reading.py:179-184 | `test_a_unit_listed_twice_refuses` refuses on "seed is not 1102", not on the duplicate check; the `seen` check (noise_reading.py:305) is not exercised (it is unreachable for a0/R units in one family, since a duplicate must sit in another seed's slot). | Rename the test to what it checks, or drop the `seen` check with a comment; no behaviour change. |
| D5 | minor | ws-c/scripts/scale78b/noise_reading.py:414-415, :163-164 | The parity-family-with-tier-family refusal and the fresh-R (no resume) refusal have no test (N17, N15 survive). | Two small tests: a parity + tier inputs file refuses; an R spec whose job.json is monkeypatched to carry `resume_from` refuses. |

Not a builder defect, but the acceptance criterion "the two S_78 configs exist" is unmet (section 3): it needs the
lead's ruling, not a fix round.

## 10. Jobs for the lead

1. **Rule on S_78 (A or B)** (the builder's item 1). Under (A), the maker merges now; each family's S_78 is written
   after its anchor job with the command in build-C.md item 1 and committed by explicit path (KD8); rules_78b.py pins
   RECIPE_S per family as null-until-filled.
2. **Fix the ruling-10 order (new).** The a0-1101 retrain "under recipe S_78" cannot run before the family's anchor
   job. Either (i) anchor job → S_78 → retrain, or (ii) the certificate retrain runs under the main config (same
   training identity, so the fingerprint test is unchanged) and the S_78 retrain for A1's states follows the anchor
   job. The check's "day the money arrives" list puts the retrain before the anchor pods; it needs this change.
3. When the S_78 configs are committed: `test_ss_family_codec.py:165` +2 (confirmed: 69 now).
4. Raise the Llama G1 result to the user before the Part 1 freeze (P78:272; ruling 14): a0-1102 fails G1 (63/600,
   10.5%; TOO CLOSE on 43 short answers; 20/557 = 3.6% without them); a0-1101 passes; OLMo-2-7B's three pass.
5. Fix round for D1-D5 (small; one builder hour, E from the sizes). D2 changes one line and one test.
6. Track B: the Llama R edit files need SEAL's fields (kind "safety-selection edit", edit_kind "remove",
   manifest_sha256 c52a50af…, provenance.selection.family "R", draw d) or N's Llama R units refuse (the reader
   checks exactly these; noise_reading.py:187-191, R).
7. Delete my `verify-C-scratch/s78-out/` once read (synthetic-hash S_78 files; they must never reach configs/).

## 11. Unresolved concerns

- The reader has never read a 7-8B R unit (none exists). The a0 side is now exercised on all five units (section 4);
  the R side is exercised on Gate B's 1B R units only. If track B's Llama R files differ from SEAL's schema, N's
  reading refuses and a fix round follows after the money is spent on N. Job 6 is the mitigation.
- Pooling mixes a plain-governed family with a fallback-governed one if only one family's trigger fires (3
  seed-matched + 3 R-R pair SEs in the median). P78 §3.3 does not state this case. The builder's choice (each
  family's governing reading enters the pool) is the natural one; the lead may want it written in Part 1.
- The parity reproduces wave 0a with the current frozen `gate_b_reading.py` (4638a0f0…), not the revision that wrote
  the output (b0964b2d…). My independent script's float-exact match makes this moot for the noise-gate functions.
- The check's T6a assumed the configs could be committed this week and packed into T4's dry packs. They cannot
  (section 3). The dry packs of 19-20 Nov carry the main configs only unless the anchor jobs run first; the
  anchor jobs cost money (block 0), so S_78 waits for the gate day in any case.
