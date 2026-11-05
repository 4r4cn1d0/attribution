# 7-8B pre-registration, Part 1 (frozen 5 Nov 2026): scope, the reused units, the noise block, the analysis scale, the seed layout and rule, the high-noise branch, the family choice, the transfer check, the S4 add-dose arm

**Status: FROZEN on 5 Nov 2026** by the lead's commit by explicit path; its SHA-256 is in FOCUS. This text adopts the lead's Part 1 rulings of 5 Nov 2026 (RUL, below) and their addendum of the same day (ADD, below; it governs over RUL where it says so). It authorizes no run and no spend: every 7-8B pod starts only on new money in the account (MONEY `lead_reading[0]`; RUL header). The lead froze it after the reviewer's read against §0 and §13 (the fix round's re-verifier; its RV1-RV5 applied by the lead) and after the Llama G1 $0 check (ADD A4; §15), the two freeze conditions of RUL ruling 14, before block 0's first `launch.py`. A later change is a dated amendment in a new file, never an edit of this one. Part 2 is a separate file, `research/experiments/<date>-78b-preregistration-part2.md` (ADD A10), frozen like Part 1 (a commit by explicit path, its SHA-256 in FOCUS, the commitments check) before block A's first pod; its scorer section is committed with code hashes before any scorer output is read (RUL ruling 14; ADD A10; P78:367; CHECK M4). Part 2 holds the arms, scorers, references, limits, judges, the confirmation and Alpaca.

Written 2026-11-05 (clock read with `date -u` at 13:28 and 13:35 UTC) by a Track D worker of the 7-8B $0 build round, for the main-study lead (General Implementation X), from the sources below. Revised the same day in the build round's fix round (clock read at 14:46 UTC at the start) against the verifier's report on this text (its defects D1-D9) and ADD; the changes are in §16 rows 35-48. Frozen the same day (clock read at 15:45 UTC) by the lead, General Implementation X, after the fix round's re-verifier passed it with five one-line fixes (RV1-RV5, §16 row 49) and after ADD A13-A17 closed the last open items (§16 row 50). Read-only on the repository except this file. No pod, no spend, no network, no install, no download, no agent. No judge output, answer, generation, sample, prompt text, `selector.jsonl` or `hidden/` file was opened. Every number carries its source. Nothing here is a new decision: where the rulings leave an item open, §17 names it and does not settle it.

**Labels.** **M** = measured (the command follows). **R** = read (path:line, or a FOCUS entry by title and recorded time). **E** = estimate (the basis follows). **I** = inference.

**Option marks** (as P78:9). **[B+C]** = shared by options B and C. **[B]** = only under option B. **[C]** = only under option C.

## Short names

- **RUL** = `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md`, the lead's Part 1 rulings (SHA-256 `65e477b0ac1e772c…`; M: `shasum -a 256`). They govern this text. "Ruling n" = RUL §n.
- **ADD** = `.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-addendum-20261105.md`, the lead's addendum to RUL, recorded 2026-11-05T14:41 UTC (SHA-256 `0372345853bb96a5…`; M: `shasum -a 256`, 14:50 UTC). It amends RUL where each entry says so and governs over RUL there. "ADD An" = its entry n (A1-A12).
- **PLAN** = `.ai/inputs/stage1-post-w1-20261023/78b/readiness-20261105/78b-readiness.md`, the readiness plan (`f39238d352ca3922…`; M).
- **CHECK** = `.ai/inputs/stage1-post-w1-20261023/78b/readiness-20261105/78b-readiness-check.md`, its adversarial check (`1bc40aa4c842ff9b…`; M). CHECK governs where it differs from PLAN; RUL governs over both (RUL header). "Cn" and "Mn" are CHECK's corrections and misses.
- **P78** = `research/review/2026-10-17-icml-78b-prep/78b-preregistration-DRAFT.md`, the base text of this Part 1 (`e6a73c92ef97e107…`; M). Its numbers, tables and option marks are kept unless §16 says otherwise.
- **KCR** = `research/review/2026-10-17-icml-78b-prep/78b-kit-cap-rule.md`, the measured cap rule. **EYD** = `.../engine-round-Y-design.md`. **CALC** = `.../calc/` beside P78. **RP** = `writing/paper/2026-10-17-icml-replan-PROPOSAL.md`.
- **PR4** = `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md`, the frozen stage-1 pre-registration (`7eccf9e9bed1e733…`; M).
- **PRE**, **PLAN-S**, **S1L** and **F L*n*** are P78's short names (P78:13): the frozen Gate B pre-registration, the sharpened-direction draft, S1B's lead-decisions addendum, and a FOCUS line at P78's hash. **NEXT** is PLAN's (PLAN:16): `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md`.
- **BR** = `.ai/inputs/stage1-post-w1-20261023/78b/build-round-20261105/`, the 7-8B build round's reports and their scripts (builders, verifiers, fixers, re-verifiers of 5 Nov 2026), committed with this text.
- **DOSE** = `.ai/inputs/stage1-post-w1-20261023/reading/user_yes_s4_dose_arm_20261101.json`, the user's "Yes, add it" of 1 Nov 2026 (`65745ad15d5cf28b…`; M). **MONEY** = `.../reading/user_answer_78b_money_20261101.json`, the user's "Yes, likely" of 1 Nov 2026 (`53945ecbf623864f…`; M).
- **README** = `README.md` (`6dfe1447fb9a4919…`; M), its 7-8B tier at README:90-95. **FOCUS** = `research/FOCUS.md` (`113a9275aca22b4a…`; M); entries are cited by title and recorded time, because line numbers move. **S1B** = `.ai/briefs/stage1-commitments-build-20261016.md`. **SEAL** = `.ai/inputs/gate-b-sealed-20261008/`; **BLD** = its `build_sealed.py` (`80cb8944…`; R: P78:13). **SS** = `experiments/safety_selection`.
- Hashes above were taken in the main checkout at HEAD `ead1d7e`, branch `stageb-costs-and-recovery-safeguards-20261003` (M: `git rev-parse --short HEAD`, 13:35 UTC); all nine re-checked unchanged at HEAD `8d6b2e0` in the fix round (M: `shasum -a 256`, 14:50 UTC).
- Notation as P78: U = the Unsafe share in pp; r_F,j = U(a0, j) − U(R_j, j); σ̂_F, σ̂_pool, σ_eval,0, s_arm as P78 §3.3; Λ̂_k = the paired-mean contrast; Φ = the primary testing family of PR4 §4.

---

## 0. Blinding line (EM-5; the form of S1B:121 (m))

This text uses no 7-8B repair outcome and no Llama-3.2-1B repair outcome: **no 7-8B repair arm has run; no Llama-3.2-1B repair arm has run** (RUL header). Before this freeze, the authors (the lead and the user) saw the following. Each item names what this text does with it.

1. **The stage-1 reading of OLMo-2-1B, plan A** (FOCUS "THE STAGE-1 READING IS DONE", recorded 2026-11-01T21:38 UTC; R): the six words and intervals (P1 better +6.33 pp; P2 equivalent +2.03; P3 equivalent −0.28; P4 worse (U) −2.31; P5 equivalent +0.11; P6 better +18.28); the best feasible repair S4 (restoration 15.97 pp; A1 8.89); family 1b "no repair beats every reference" (G, B+Qi, Safe LoRA default and the safety prefix reach a lower U than S4 by 0.8, 13.0, 12.4 and 3.0 pp, with more over-refusal); B14's overlap control (S1 and S3 not shown, S4 holds); LN-14's transfer bar (fails); the stage-3 pick (P6, then P1); E_HB +30.1 pp; the HarmBench sentence word per contrast (the record's "Words" line: headline, U part, HarmBench sentence, S-G coherent headline); P3's L state *infeasible* and P2's *undetermined*; S4 against A1 seed-matched +7.08 pp (90% [+5.82, +8.34]); "S4 and A1 beat the adapter-scaling curve"; no O or L node rejects and no coherence flag; F_k's power, the S-a shift line and the cost table in the record. **Use here:** none of these values enters a 7-8B design number. The reading motivates one addition, the S4 add-dose arm (§10), and §13 labels every choice it touched.
2. **Gate B's verdict TOO CLOSE** (FOCUS "GATE B CLOSED", recorded 2026-10-23T05:26 UTC; R) and its wave-0a nuisance values: σ̂_gate 1.83 pp, σ_eval,0 1.28 pp seed-matched against 2.16 pp for R-arm pairs, the fallback SD 1.905, mean r 2.5 pp (SE 1.06) against a linear-dose 5.6 pp, the R-arm against a0 per-arm SDs 1.35 against 2.65 pp (R: P78:127), and Gate B's final unit reading behind the verdict (its rankings and labels; FOCUS "GATE B CLOSED") (R: P78:127-128, :133-134, :140, :448). **Use here:** these pre-stage-1 values are the basis of the pairing argument (§4), the parity test of the noise reader (§3) and predictions N1 and N2 (§3.6). TC does not run because of the verdict (§9).
3. **Stage 1b's pilot null** (FOCUS "STAGE 1b'S PILOT SAYS STOP", recorded 2026-11-02T03:25 UTC; R): Λ_plant +3.94 pp, below the 5 pp floor. **Use here:** none.
4. **The seven engine-X 7-8B units** of §2 (R: P78:50-56): untuned U 11 of 600 (OLMo-2-7B) and 32 of 600 (Llama-3.1-8B); a0 U 309, 234, 284 (OLMo 1101-1103) and 347, 356 (Llama 1101-1102); E +49.67, +37.17, +45.50 and +52.50, +54.00 pp; per-arm a0 SD 6.36 pp on 2 df (OLMo) and 1.06 pp on 1 df (Llama) (R: P78:314); the six-cell pooled per-arm SD 5.83 pp (R: P78:224); HarmBench E_HB for seeds 1101-1102, OLMo +37.0, +27.7, Llama +36.2, +37.8 (R: P78:60); Llama-3.1-8B a0-1102's 63 of 600 answers incoherent (10.5%) and its answers-end check TOO CLOSE (R: P78:272). **The Llama G1 $0 check's counts** (ADD A4; the frozen Gate B guard code on the a0 units' records; counts only; the record `78b/llama-g1-check-20261105.json` is track C's and is merged by the lead): Llama a0-1101 42 of 600 fail the screen (passes G1); a0-1102 63 of 600 (10.5%), 43 of them short answers (20 of 557 = 3.6% without them), answers-end TOO CLOSE, a G1 failure; OLMo-2-7B a0 1101-1103 pass (23, 20, 16 of 600); Llama a0's pooled count over the two seeds 105 of 1,200 (8.75%). **Use here:** the family choice (§8), the money bases, the H table (§7), predictions N1 and N2; the G1 counts enter the coherence screen's form only (§14 item 7, §15) and no design number.
5. **Llama-3.2-1B's Gate A** (a0 only; PASS, 10 Oct; E +48.0, +52.8, +44.2 pp, mean +48.3; R: README:82; DOSE `integrity[1]`). **Use here:** none; it is the only Llama outcome that exists.
6. **The 1B S4 keep count** (RUL ruling 12, M2; read 5 Nov 2026, counts only): the 1B untuned-answers pass answered 64 candidates in 2 chunks and kept 57 (26 of 32, 31 of 32; 7 not refusal-opening; 9 kept after the 48th), 89%. **Use here:** it sizes the add-dose arm's fallback only (§10; §13 item 9). It is a θ0 count from a scorer pass, not a repair outcome.
7. **The 1B Gate A a0 units' screen rates** (7.0%, 4.7%, 3.7%; R: PR4:298) and the stage-1 coherence bar. **Use here:** none; the 7-8B screen is PR4 §3.7's bar by ADD A4 and A11 (§14 item 7).
8. **Stage 1b's construction checks** (FOCUS "STAGE 1b'S CONSTRUCTION CHECKS OPENED AND PUBLISHED AFTER THE FINAL STOP", recorded 2026-11-02T03:25 UTC; R): the text-only scorers' ranks of the planted leaf and their AUCs (the content classifier ranks it first at every menu; DataShield-style, H1, H2a, H2b and L1 do not). **Use here:** none; L1 and H1 stay primary (§13 item 2).

What the authors have **not** seen: any U, O, L, HarmBench or Granite value of any 7-8B R arm, method arm, reference or dose arm; any Llama-3.1-8B a0-1103 value; any σ̂ of N. Part 2's blinding line adds N's values (r_F,j, σ̂_F, σ̂_pool, mean r_F, E of Llama a0-1103) in the same form once they are read (P78 EM-5, :337).

---

## 1. Scope, options B and C, and the gate [B+C]

**The tier.** OLMo-2-7B (recipe B at LR 1e-4, config `18cc31d7…`, manifest `9ed61826…`) and Llama-3.1-8B-Instruct (recipe B at LR 5e-5, config `74758af1…`, manifest `c52a50af…`), micro-batch 2 × accumulation 64 on A100-SXM4-80GB, so 4,800 rows give 38 steps and 4,200 rows give 33 steps, as at 1B (R: P78:59). The study question, arms, outcome U and the frozen 1B model are PR4's (PR4 §0.5, §1.2, §2.1, §3.2).

**Options** (R: README:93; P78:9; RP:71-79 via PLAN §5.1). **A** = a reduced benchmark (about 30 runs per family; no primary family). **B** = the full comparison on both families plus the confirmation at 7-8B. **C** = as B on one family. Under B each family runs the same plan; under C the chosen family (F, §8) runs it. The user has not chosen B or C; B is the planned default (MONEY `lead_reading[1]`).

**The gate (ruling 9; RP decision 2 restated).** The gate is the day the new money is in the account (expected about 20 Nov; MONEY), after N's reading. It reads the money and N only, never a 1B outcome. **B** if the account covers B's primary comparison at the plan the seed rule gives (§6), with (b)'s extra if H fires (§7), with the references, scorer passes, judges and idle storage, and the confirmation money is in sight (in the account, or the user has said it will come by about 1 Dec); **else C on F1** (§8). The S4 add-dose arm is outside this test (§10). If the money is not in the account by about 1 Dec, the gate's re-check: C, or B without the 7-8B confirmation, by RP:138's cut order (ruling 9). The 4 Jan results freeze (README:120, an internal target) is re-checked at the gate (PLAN §5.1).

**The earmark (ruling 9).** The new money is for the 7-8B tier (MONEY `question`). Stage 1c, the human label check and stage 2 start on their own money or on the user's word; the lead says so when the money arrives.

**What still needs the user (RUL header; CHECK C13).** Four things, and only these: (1) the money in the RunPod account (MONEY); (2) the HF token in the Mac environment at each Llama-3.1-8B launch (the gated download; §8, §12); (3) a yes by pod name before any stopped 7-8B pod is deleted, after a verified backup (KD5; §12); (4) H (a) or (c), only if the user wants either one (§7). Everything else in this text is a lead ruling under the delegation (RUL, ADD) and is reported, not asked.

**Money the gate reads (E; CHECK "Money (corrected)", C3; bases PLAN §4: per-arm cost at 4 arms per pod $2.94-3.52 OLMo and $3.93-4.52 Llama, KCR:183-188; FRE counts RP:76; +20% RP:41; nothing counted twice).**

| Line | Amount (E) |
|---|---|
| B by the gate, plan A | about $640-900 |
| B by the gate, plan B9 | about $710-990 |
| B by the gate, H (b) on both families | about $830-1,140 |
| plus the 7-8B confirmation, by about 1 Dec | +$140-230 (RP:136) |
| C on OLMo-2-7B (F1) | about $270-390, plus $70-120 confirmation |
| C on Llama-3.1-8B (F2) | about $375-510, plus $70-120 confirmation |
| The S4 add-dose arm, both families | $49 (3 seeds) to $99 (6 seeds); per family OLMo $21 / $42, Llama $28 / $57 |
| First-days guard terms the balance must cover at each launch | N about $56 (KCR:177); each retrain pod about $15-20 (ADD A8: one single-job pod per family, two under [B], F1's only under [C]; at the kit's 4.5 h cap $6 + 1.85 × 4.5 h = $14.33, × 1.25 = $17.91, M); each anchor or scorer pod about $25-40 (CHECK M3; the anchor pod runs before the retrain pod, ADD A2) |
| Block A, per four-pod launch at KCR's caps (the kit's cap-based need) | about $105-125 (CHECK C14: $6 + 1.85 × 4 × 10.5 h = $83.70 OLMo-2-7B, $6 + 1.85 × 4 × 12.5 h = $98.50 Llama-3.1-8B, each × 1.25 = $104.62 / $123.12; M) |

The expected money is about $900-1,300 by about 20 Nov (MONEY `question`, `user_words` "Yes, likely", 2026-11-01T09:16Z). It is an expectation, not a balance (MONEY `what_it_is`); the balance was $22.64 on 2 Nov (R: PLAN §1.1). Against it: plan A or B9 with the confirmation fits ($780-1,220); H (b) with the confirmation fits only at the low end ($970-1,370) (CHECK C3). The gate budgets the worst plan SR-2 can reach, H (b) (P78:203; CHECK C3). README:95's earlier figures (B $1,180-1,760; C $770-1,160) are the older proposal; the gate uses the corrected bases above (FOCUS "THE 7-8B READINESS PLAN IS BACK", recorded 2026-11-05T09:33 UTC).

---

## 2. Units reused and the pairing conditions [B+C]

### 2.1 The seven engine-X units (R: P78:48-58; M there: each unit's `COMPLETE.json`; CALC `env_and_manifest_check_out.txt`)

| Family, unit | Seed | U (of 600) | E (pp) | Engine | Config | Manifest | `COMPLETE.json` SHA-256 |
|---|---|---|---|---|---|---|---|
| OLMo-2-7B untuned | – | 11 (1.83%) | – | `472fc7f6` | `18cc31d7` | `9ed61826` | `632fa4bd0a8f3b1b…` |
| OLMo-2-7B a0 | 1101 | 309 (51.50%) | +49.67 | `472fc7f6` | `18cc31d7` | `9ed61826` | `4a6d9ebc6636de57…` |
| OLMo-2-7B a0 | 1102 | 234 (39.00%) | +37.17 | `472fc7f6` | `18cc31d7` | `9ed61826` | `43e8412dc7ef8d3e…` |
| OLMo-2-7B a0 | 1103 | 284 (47.33%) | +45.50 | `472fc7f6` | `18cc31d7` | `9ed61826` | `4b5bd06dede08dc1…` |
| Llama-3.1-8B untuned | – | 32 (5.33%) | – | `472fc7f6` | `c5462c77` (the LR 1e-4 kit's init unit) | `c52a50af` | `651f7f6de6721b41…` |
| Llama-3.1-8B a0 | 1101 | 347 (57.83%) | +52.50 | `472fc7f6` | `74758af1` | `c52a50af` | `21427715565fb394…` |
| Llama-3.1-8B a0 | 1102 | 356 (59.33%) | +54.00 | `472fc7f6` | `74758af1` | `c52a50af` | `b0c99f7b97e6e763…` |

- Record paths (R: P78:58): `tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-{init,e1}-a1`; `tmp/family-probe-sp-olmo2-7b-b-seed1102/…/1102-a0-e1-a1`; `tmp/family-probe-sp-olmo2-7b-b-seed1103/…/1103-a0-e1-a1`; `tmp/family-probe-sp-llama31-8b-b-a0/…/1101-a0-init-a1`; `tmp/family-probe-sp-llama31-8b-b5e5-1101/…/1101-a0-e1-a1`; `tmp/family-probe-sp-llama31-8b-b5e5-seed1102/…/1102-a0-e1-a1`.
- The side units' fingerprints (R: P78:82; M there): OLMo-2-7B 1101 q `3c7344c178b47e5b…`, e1 `9d5d5d8b2eb40262…`; Llama-3.1-8B 1101 q `ac05caca1bdfac5b…`, e1 `ee44580dfa016b67…`. OLMo-2-7B's e1 adapters for 1101-1103 are on the Mac (`tmp/sp-repr/out/`; SHA-256 `bb133508…`, `ac69a6ba…`, `76c41cd6…`; R: P78:62). No Llama-3.1-8B adapter at LR 5e-5 is on the Mac (R: P78:62).
- OLMo-2-7B's recipe-G units 1101-1103 are at OLMo's main LR and serve as the recipe-G reference; Llama's recipe-G units are at LR 1e-4, so a Llama recipe-G reference needs 3 new runs (R: P78:66). The causal side-study units at 1121-1122 and every Qwen unit are not used (R: P78:67-68).

### 2.2 The four pairing conditions (met now; R: P78:72-78)

What a same-seed pair shares: the adapter initialization, the relative order of the kept rows and the sampling seed of each (prompt, sample); training is deterministic on a matching machine (R: P78:72). Conditions: (1) the same engine X for every 7-8B a0 unit; (2) the same training identity per family (`36738c38` OLMo-2-7B, `5b4451e1` Llama-3.1-8B; the 1B precedent: Gate B's R arms under recipe S paired with Gate A's a0 under recipe B, identity `f46279e5`); (3) the same manifest per family, the edit files bound to it (`SS/edits.py:117` refuses another prepared dataset); (4) the same compared environment: the 13 fields of `scripts/family_probe_reading.py` `environment_of` equal for all seven units, the three 1B Gate A a0 units and the Gate B units of 15-16 Oct (canonical hash `8e393dca87ab…`; lock `7e0dd998…`; guard Qwen3Guard-Gen-4B `6ec42827…`).

**The new arms must meet EM-1 (§11):** engine X (or Y after ruling 10's certificate), the family's main config, the family's manifest, a pod whose compared fields and guard record equal the family's a0-1101 unit (R: P78:80).

### 2.3 Ruling 7: the seven units are main-study units (RP decision 5)

- **Ruling.** The seven units of §2.1 are main-study units, pinned by their `COMPLETE.json` SHA-256 above, under the four conditions and EM-1 (ruling 7).
- **The check that confirms it (ruling 10, §3.7).** Each family's a0-1101 retrain (train only, recipe S_78, to q and e1) must reproduce the side unit's q and e1 fingerprints above.
- **Pre-set fallback (ruling 7).** Trigger: for a family, block 0's environment check fails, or the **X** retrain of ruling 10 differs from the side unit's fingerprints. Then N is re-read with the a0-free fallback (§3.4; P78:121), and that family's a0 at 1101-1103 re-runs in the new environment before any paired contrast (+3 runs, about $9-12; R: P78:333).
- Without reuse, the S-U exclusion of plan A (P78:152) no longer holds, and N has no a0 partners until the re-runs exist (R: PLAN §3 item 2).

---

## 3. Block 0 = N, the noise block [B+C]

### 3.1 Runs (R: P78:92-96)

| Family | Arm | Seed | Edit file | Config | Runs |
|---|---|---|---|---|---|
| OLMo-2-7B | R_1, R_2, R_3 | 1101, 1102, 1103 (draw d at seed 1100 + d; R: PR4:124) | SEAL `out/edits/R_d1.json` `f7d7eb86…`, `R_d2.json` `913b7360…`, `R_d3.json` `cd8d3328…`, byte for byte (same manifest; M in P78) | `18cc31d7` | 3 |
| Llama-3.1-8B | R_1, R_2, R_3 | 1101, 1102, 1103 | the Llama sealed set `.ai/inputs/scale-78b-sealed-llama3-20261105/` (ruling 14; built by BLD's `draw_r` with the set's own writer on `c52a50af`); each remove list must equal SEAL's R_d1-R_d3 list, and R_d6-R_d8 must equal stage 1's `r-draws/edits/R_d6-8` (CHECK C5) | `74758af1` | 3 |
| Llama-3.1-8B | a0 | 1103 | none (fine-tune only on the sealed untuned unit, as 1101-1102 were) | `74758af1` | 1 |

- Every arm evaluates at e1 only, as at 1B (R: P78:98). R arms train 33 steps; a0 trains 38.
- The R arms run under the family's **main config**, not a recipe-S sibling (R: P78:99; ruling 11 KD10: the `arm` kind "R_1-R_3 under the family's main config").
- **The Llama-3.1-8B seed-1103 rule (ruling 8; "the rung stays").** Llama a0 at 1103 runs in N under the main config (`74758af1…`, LR 5e-5). It is an a0 unit for N and for the comparison. It is read by the frozen family-probe bars and reported with the 3-seed Gate A mean. Its outcome never changes Llama's rung (the user's 11 Oct "at the edge" decision; R: P78:60, :100): a rung change after an outcome would be a choice after an outcome.
- N's 7 runs are inside the comparison's counts: R_1-R_3 are the first 3 of R's seeds and Llama a0-1103 is one of a0's 7 (R: P78:110; §5).
- **The sealed input folders (ruling 14 as amended by ADD A3).** Three folders, each a sealed input set with its own MANIFEST, like SEAL and `.ai/inputs/gate-b-anchors-20261008/`: the Llama sealed set `.ai/inputs/scale-78b-sealed-llama3-20261105/` (R_d1-R_d16 and the 8 unit files by manifest; ruling 14); `.ai/inputs/scale-78b-r-draws-olmo2-20261105/` (OLMo-2-7B R_d11-R_d16; ruling 2's layouts use R_d11-R_d13 at most, under H (b)); `.ai/inputs/scale-78b-length-rules-llama3-20261105/` (Llama-3.1-8B's H1). OLMo-2-7B's R_d1-R_d5 are SEAL's and R_d6-R_d10 are stage 1's `.ai/inputs/stage1-commitments-20261016/r-draws/edits/` (M: `ls`, names only). The two extra folders stay where they were built (a move would change the output path inside the hashed build scripts and force a rebuild; ADD A3). Before their first commit the verifiers' write guards (track B's B-M2 and B-M3, and the fix round's RV-1, a case-variant path) are fixed and the sets rebuilt into empty `out/` folders; from the commit on the scripts are frozen (ADD A3). None of the three is in the main checkout yet (M: `ls -d .ai/inputs/scale-78b-*` finds none at HEAD `8d6b2e0`); the lead merges them by explicit path.

### 3.2 Pods, caps and money (ruling 11; KCR via RUL)

- **Layout (ruling 11, "N's layout").** OLMo-2-7B: one pod, 3 jobs, cap 8.5 h. Llama-3.1-8B: one pod, 4 jobs, cap 12.5 h. In parallel. Both are X-packed pods (the engine identity is pinned per pack; CHECK C4). Fallback: if a pod stops before its last job, the rest requeue on a new pod (the kit's requeue path).
- **Caps** come from the measured M-cap rule (`runkit/stage1-78b/rules_78b.py`, T2; ruling 11 KD1-KD3): margins 1.15 on the measured job, SCORE_ALLCAP 1,250 s, 48 min pod overhead, refusal at s > 1.15 and at `s_obs` > 1.15; at most 4 counted arms per pod on both families (KD2; fallback 3 on Llama, cap 9.75 h, if block 0's 4-job Llama pod exceeds its requirement or reads `s_obs` > 1.15).
- **The constants' convention (ADD A5; a KCR erratum).** `rules_78b.py` uses the measured basis file's maxima. KCR's printed requirements (12,243 / 12,365 s OLMo-2-7B at 33 / 38 steps; 12,499 / 12,613 s Llama-3.1-8B) round each constant before summing; the rule gives 12,244.15 / 12,365.42 s and 12,498.05 / 12,612.47 s, at most 1.2 s apart. Caps, guards and spends are identical to the cent (M: track A's test 1, via ADD A5). The basis file governs.
- **KD1's fallback (ADD A12).** Its trigger is "T2 not verified by 12 Nov". Round 1's verifier found minor defects only; the fallback does not fire if the fix round's re-check passes and the lead merges T2 before 12 Nov, the merge commit recorded in FOCUS. KD2's Llama fallback (3 arms, cap 9.75 h) is pre-set above; if either fires, this section's figures change and the change is disclosed (§17 item 1).
- **Money (E).** Spend about $21-27, $26-32 with the 20% allowance (R: P78:108); KCR's figures for the same layout: expected spend $24.75, rule upper $33.30, guard $44.85, funding need 1.25 × $44.85 = **$56.06** (R: KCR:177; ruling 11 "about $56 with the contingency"). Gate B's hold no longer applies (§11 EM-2). Not in N's figure: idle storage about $0.33 per day per stopped 50 GB pod (R: P78:112; KCR:161); judge pods for the R arms (R: P78:112); the retrain pod (§3.7) and the scorer pods (§12).
- Block 0 is therefore not two pods but N's two plus, per family, the anchor pod and then the a0-1101 retrain pod of §3.7 (CHECK C4; ADD A2, A8): two retrain pods under [B], F1's only under [C], each single-job with the kit's explicit E cap for the retrain kind (`rules_78b.py`, 4.5 h until measured; KD6). `plan_tool.py init-block 0` prints the need of N's pods, each retrain pod and the scorer pods on its own line (ruling 11, M3; ADD A8).

### 3.3 The reading (`scripts/scale78b/noise_reading.py`, T5; R: P78:116-122)

For each family F and seed j ∈ {1101, 1102, 1103}: r_F,j = U(a0, j) − U(R_j, j), in pp.

- **σ̂_F** = max(SD(r_F,j), σ_eval,0,F), 2 df (Gate B's σ̂_gate form). σ_eval,0,F = the median, over the family's 3 pairs, of the prompt-clustered SE of the pair's per-prompt difference.
- **σ̂_pool** = max(√[(2·SD(r_O)² + 2·SD(r_L)²)/4], the median of the 6 pair SEs), 4 df. The seed rule (§6) reads σ̂_pool on the pair scale (ruling 1, ruling 3). Pooling assumes equal paired noise in the two families (R: P78:119; the a0 point estimates differ about 6×, p ≈ 0.12).
- **One family's fallback in the pooled reading (ADD A6).** When only one family's fallback trigger (§3.4) fires, that family's three R-arm pair terms and the other family's three seed-matched terms enter the pooled median. The noise reader does this (track C). ADD A6 rules the median; that family's SD(r) term is §3.4's a0-free form (I: P78:121 replaces each r term per family).
- **s_arm** (for the S-U sensitivity): the pooled per-arm seed SD of U over the main-recipe a0 and R units of both families (8 df once Llama a0-1103 exists).
- The script reuses the frozen Gate B reading's σ_eval and SD functions by import or by a copy with a parity test that reproduces Gate B's wave-0a values σ̂_gate 1.83, fallback 2.16, σ_eval,0 1.28 (R: P78:345; CHECK track 5). It keys every input by `complete_sha256` and family, never by arm and seed alone (R: P78:291), so a 1B file can never enter a 7-8B contrast. It prints σ̂_F, σ̂_pool, s_arm, both σ_eval,0 forms, the triggers and the seed-rule output. It never reads a method arm.

### 3.4 The a0-free fallback (R: P78:121; ruling 7)

If a new R arm's environment differs from its family's a0 units, or if the **X** retrain's fingerprints differ (ruling 10), each r term is replaced by √2 × SD(U(R_1101), U(R_1102), U(R_1103)) and σ_eval,0 uses the three R-arm pairs. The reading is then a0-free for that family; if only one family's trigger fires, the pooled reading mixes the two forms as §3.3 says (ADD A6). The seed rule is re-read and the plan follows the re-read.

### 3.5 Report-only results (they gate nothing; R: P78:126-129)

- Mean r_F (the random-removal effect at 7-8B) with its SE, per family.
- The per-arm seed SD of the R arms beside the a0 SD. At 1B: 1.35 against 2.65 pp (R: P78:127).
- σ_eval,0 for seed-matched pairs against R-arm pairs. At 1B: 1.28 against 2.16 pp (R: P78:128).
- Each R arm's G1 status by the frozen Gate B guard code, report-only (ADD A4, A11). N does not stop on a G1 failure (R: P78:129). (Its consequence for TC is moot: TC does not run, §9.)
- Llama a0-1103 by the frozen family-probe bars, reported with the 3-seed mean (ruling 8).
- **Judging for N (ADD A9).** N's gate and the seed rule read the engine's own U only. HarmBench judging of N's R arms (report-only; the cost P78:112 lists outside N's figure) runs with block A's judge pods. Llama a0-1103 gets the same judge files as block A's units, on the same pods (so P78 [LEAD] item 3's judge files exist for every reused a0 unit). No Granite judging runs for TC (ruling 6).

### 3.6 Predictions N1 and N2 (ruling 13; written 5 Nov 2026, before N and before any 7-8B repair outcome; they gate nothing)

- **N1 (mean r_F = U(a0) − U(R_j), per family).** Point **+2.5 pp** on each family; 80% interval **−1.5 to +6.5 pp**. Basis (ruling 13): 1B Gate B read +2.5 pp (SE 1.06) against a linear-dose 5.6 pp, so the loss plateaus early (saturation); E/8 would be 5.5 pp (OLMo-2-7B) and 6.7 pp (Llama-3.1-8B) (R: P78:133).
- **N2 (σ̂_pool, pair scale).** Point **4.5 pp**; 80% interval **2.5-8.5 pp**. Basis (ruling 13): the 1B pairing ratio 0.49 (R: P78:134) applied per family gives about 4.4 pp (OLMo-2-7B) and 0.7 pp (Llama-3.1-8B); the lead's pooled point is about 4.5 pp (ruling 13 as corrected by ADD A14: by §3.3's σ̂_pool form the two per-family values pool to about 3.2 pp, M: BR `fix-D-scratch/htable_fix.py` step 4, so the point is the lead's judgement between that figure and the no-gain 8.2); applied to the pooled 5.83 pp, 4.0 pp; with no pairing gain, about 8.2 pp. The implied plan probabilities: plan A about 0.5, plan B9 about 0.3, H about 0.2.
- These are written after the stage-1 reading; the quantities they predict (7-8B noise, the random-removal effect at 7-8B) were not read at 1B's stage 1 (§13 item 3).

### 3.7 The anchor job, recipe S_78 and the a0-1101 retrains; the engine rule (ruling 10 as amended by ADD A1, A2, A8; CHECK C4)

- **The order per family, before block A (ADD A2).** (1) The anchor job on its own single-job pod (KD6) writes the family's `anchors.sealed.json`; (2) recipe S_78 is written and committed (below); (3) the a0-1101 retrain runs on engine Y under S_78; (4) the X retrain runs only if Y's fingerprints differ (the pre-set second job). This moves the anchor pods before the retrain pods; it adds no pod and no money (CHECK C1 already put the anchor job before block A). Rejected (ADD A2): a certificate retrain under the main config plus a second S_78 retrain for A1's states, one more retrain pod per family.
- **Recipe S_78 (ADD A1; route (A)).** S_78 = the family's main recipe with Gate B's recipe-S differences (R: PLAN T6, :297; CHECK T6a's "differs only in recipe-S fields" test). Its `attribution.query_bank` is `anchors-<SHA-256 of the family's anchor file>` (R: `scripts/make_anchor_answers.py:1-18` via ADD A1), and the engine checks that file's hash at the attributes job (R: `SS/jobs.py:175-181`), so a placeholder would pass the loader and fail on the pod, and the anchor file holds the model's own Safe answers, so S_78 is per model (P78:377). Therefore the maker `scripts/scale78b/make_recipe_s78.py` is merged now, and each family's S_78 config is written by it once the family's anchor job has written its anchor file, then committed by explicit path (KD8). Until then `rules_78b.py` pins `RECIPE_S` as null for both families, and every kind that needs S_78 (the a0-1101 retrain, A1's pass) refuses. Rejected (ADD A1): (B) OLMo-2-7B reusing Gate B's 1B anchor file (it holds OLMo-2-1B's answers, which changes P78:377; Llama would wait anyway).
- **The retrain pods (ADD A8).** Each family's a0-1101 retrain (train only, recipe S_78, to q and e1) runs first on **engine Y**, on its own single-job pod: two pods under [B], F1's only under [C]; each with the kit's explicit E cap for the retrain kind (`rules_78b.py`, 4.5 h until measured; KD6); it is the first Y pod of KD9, so the measured basis is re-measured there before Y carries a block. The kit's `init` prints each pod's need on its own line (M3).
- **Y fingerprints equal the side unit's** (q and e1 adapter and optimizer; §2.1): Y = X for that family. Every 7-8B arm, B+Qi included, may run on Y; the A1 pass runs on the engine that trained its states (EYD:81 via RUL).
- **Y differs:** the pre-set second job is the **X retrain**, on a pod of the same image packed with engine X. **X equal:** paired arms stay on X; B+Qi runs on Y as an unpaired reference, labelled. **X differs:** the pod or environment differs, and ruling 7's fallback applies (§2.3, §3.4).
- Basis (ruling 10): a Y retrain that differs cannot say whether Y or the pod caused it (C4); only an X mismatch triggers P78:121's fallback.
- The retrains also give A1 its a0-1101 q and e1 states (R: P78:82).

---

## 4. S, the analysis scale (ruling 1) [B+C]

- **Ruling.** The 7-8B reading uses the frozen stage-1 model's form, **HB-C, per family** (R: PR4:233-240): U(a, j) = μ_a + s_{c(a), j} + e(a, j), Var e(a, j) = σ²_a; one seed effect per design cluster, the full-corpus cluster {a0, S1, S3, S4} (38 steps) and the removal cluster {R, A1, L1, H1} (33 steps); σ²_a per arm by REML with PR4's floors and stop rule (LN-35: U and O floor 0.01 pp², L 10⁻⁸ nats²); the paired mean on the common seeds as the estimator (PR4:229, :236); the prompt part (PR4:237); Satterthwaite df (PR4:238). Reference and secondary arms never enter this fit (PR4:234). The seed rule reads σ̂_pool on the paired scale (P78:119). This is **S-P** of P78 §4.
- **S-U** (the difference of arm means, variance pooled over arms, Welch as a check; P78:150) is printed beside every primary contrast as the pre-registered sensitivity, as PR4 §3.4 prints S-a and S-aW at 1B. At 7-8B S-U uses the plan's R seeds, 1101 to the last method seed (ruling 2: 7 / 10 / 13 R cells in plans A / B9 / H (b)), so its SE is §7's recomputed value (3.24 / 2.68 / 2.33 pp at σ 5.83; ADD A7), not P78's at R 8 / 12 / 16.
- **Basis (ruling 1).** Consistency with the frozen 1B model (PR4:233, adopted before any stage-1 outcome); Gate B's noise model is paired ("s_j cancels in every c", R: P78:140); the 1B pairing evidence, σ_eval,0 1.28 pp seed-matched against 2.16 pp for R-arm pairs (Gate B wave 0a); the cost of no pairing gain is small (SE about 7% worse, 3.37 against 3.15 pp; R: P78:154); only S-P can bring 7-8B near the 5 pp target at 6 seeds (R: P78:153, :160). P78 marked S [USER]; it is recorded here as the lead's ruling under the delegation, not as "already decided" (CHECK C14).
- **What S-P assumes (R: P78:422).** An additive seed effect per cluster. An arm × seed interaction enters the residual, so the final SE stays honest, but N's planning value (a0 against R pairs) may not hold for method arms.
- **Contrasts and their sign (R: PR4:228).** P1 = U(R) − U(A1); P2 = U(R) − U(L1); P3 = U(R) − U(H1); P4 = U(a0) − U(S1) (two-sided); P5 = U(S1) − U(S3); P6 = U(S1) − U(S4). Positive = the repair restores more. Restoration G_m = U(a0) − U(m) is reported for every arm (PR4:230).
- **Fallback.** None needed: S-U is reported in every case; PR4's floor and stop rules handle REML edge cases (ruling 1).
- **S-U and plan A (R: P78:152; kept for the record).** On the unpaired scale the data in hand already exclude plan A by a 0.03 pp margin (√2 × 3.20 = 4.53 > 4.5), given the reuse of §2.3. Under S-P the plan is decided by N.

---

## 5. The seed layout (ruling 2) [B+C]

- **Ruling.** Every plan uses PR4's layout form (PR4:124-125, :161): method arms at the plan's seeds from 1102; R at 1101 to the last method seed; **a0 at 1101-1107 in every plan** (seven cells; P78:159's edit, so P4 has six shared seeds). No R seed beyond the last method seed is run. The 1101 rule holds: no scorer built on a0-1101 states is evaluated at 1101 (PR4:133; P78 EM-3).
- **Basis (ruling 2).** Under HB-C an R cell without a method partner enters no primary estimate (PR4:240, "Seeds without a partner"); P78's R_8 (plan A), R_11-R_12 (B9) and R_14-R_16 (H (b)) served S-U only. Stage 1 ran R at 1101-1107 (PR4:124). a0_1101 and R_1101 enter no primary estimate and no variance under HB-C; they enter the S-U sensitivity and each arm's reported mean (PR4:240).
- **Fallback.** None; the counts only fall (ruling 2).

**Runs per family per plan (block A is the same for every plan; R: P78:199; counts I from ruling 2's layout, checked against P78 §5.4).** N's 7 runs and the units in hand are not counted.

| Plan | Method seeds | R seeds | a0 seeds | Block A (new) | Block B (new) | New runs beyond N | P78 §5.4 count |
|---|---|---|---|---|---|---|---|
| plan A | 6 arms at 1102-1107 | 1101-1107 | 1101-1107 | 6 × 3 (1102-1104) + R_4, R_5 + a0 1104 = 21 | 6 × 3 (1105-1107) + R_6, R_7 + a0 1105-1107 = 23 | **44** | 44 (R_8 → a0 1107) |
| plan B9 | A1, H1, S1, S4 at 1102-1110 | 1101-1110 | 1101-1107 | 21 (L1's and S3's 6 block-A runs are kept as secondary data for P2 and P5; R: P78:199) | 4 × 6 (1105-1110) + R_6-R_10 + a0 1105-1107 = 32 | **53** | 54 |
| H (b) | A1, H1, S1, S4 at 1102-1113 | 1101-1113 | 1101-1107 | 21 | 4 × 9 (1105-1113) + R_6-R_13 + a0 1105-1107 = 47 | **68** | 70 |

- Money per plan stays as P78 §5.4 (E; per-arm cost RP §2.1, ×1.2; CALC `power2_out.txt`; this basis is kept and labelled by ADD A17: the gate reads the kit's `init-block` needs on KCR's measured rates, and the two bases are never mixed in one figure), now an upper bound (ruling 2): plan A $148-190 (OLMo-2-7B) / $174-216 (Llama-3.1-8B); plan B9 $181-233 / $214-266; H (b) $235-302 / $277-344. Over plan A: B9 adds about $33-43 (OLMo) or $40-50 (Llama); 12 seeds add about $87-112 or $103-128 (R: P78:216). Under [B] count both families; under [C] one.
- Seeds 1101-1116 lie in the development namespace 1101-2099 (R: P78:218); the main-study seeds never meet the causal side-study's 1121-1122 (R: P78:67).
- Reused cells: a0 1101-1103 (OLMo) and 1101-1102 (Llama) from §2.1; Llama a0-1103 and R_1-R_3 from N.

---

## 6. SR, the seed rule; the thresholds; the review ceiling; SR under [C]; SR-2 (ruling 3) [B+C]

### 6.1 The rule (ruling 3; R: P78:168-177)

σ̂ = σ̂_pool from N (4 df), pair scale (§3.3).

| σ̂ (pair scale) | Plan | Primary family | Seeds (ruling 2) | SESOI |
|---|---|---|---|---|
| ≤ 4.5 | **plan A** (as 1B) | P1-P6 | methods 1102-1107 (6); R 1101-1107 (7); a0 1101-1107 (7) | 5 pp |
| 4.5 < σ̂ ≤ 6.0 | **plan B9** (PR4:161's plan-B form with 9 method seeds) | P1, P3, P6 primary; P2, P4, P5 secondary at block A's three seeds, one-sided bounds | A1, H1, S1, S4 at 1102-1110 (9); R 1101-1110 (10); a0 1101-1107 (7) | 5 pp |
| > 6.0 | **branch H** (§7) | per H | per H | per H |
| the plan's removal MDE > 2 × its SESOI | **review** (the ceiling): no 7-8B primary family; the units that ran are reported descriptively; the user decides the next step (R: P78:175, :177) | — | — | — |

- **The thresholds 4.5 / 6.0 are kept** (PLAN-S's numbers at both sizes; ruling 3). Under S-P they mean paired MDEs of about **6.39 pp (plan A) and 6.47 pp (plan B9)** (R: P78:168; CALC `rule_oc2_out.txt`), not the 6.0 pp of PLAN-S's unpaired formula, because the paired contrast uses the 6 (or 9) shared seeds. The rescaled thresholds 4.22 / 5.56 (paired MDE 6.0) are **not adopted** (ruling 3).
- **The review ceiling is kept** (ruling 3). On the pair scale it binds only at σ̂ above about 10.7-21 pp (S-P), by option (R: P78:177); it is a safety valve. In the noise reader the comparison is exact, with one pinned MDE factor per plan (1.4207 / 1.0785 / 0.9340 for A / B9 / H (b); M: `scripts/scale78b/noise_reading.py`, after the fix round's C-D2): review fires at σ̂_pool above 7.0388 / 9.2721 / 10.7066 pp, so in A and B9 it cannot fire (their σ̂ ranges end at 4.5 and 6.0 pp) and in H (b) it fires above 10.7066 pp.
- PLAN-S's "> 6.0: no stage 1; review" becomes "branch H" at 7-8B (RP decision 3; R: P78:177).

### 6.2 SR under [C] (ruling 3)

σ̂_pool (both families' N, 4 df) gives the **provisional** plan. SR-2's σ̂_A from the chosen family's own block-A units decides block B. Without SR-2 (its fallback below), the chosen family's own σ̂_F (2 df) decides (R: P78:119). Under [C] with the family fixed now (F1) there is no winner's curse, so pooling only buys df (R: P78:119).

### 6.3 Operating characteristics (R: P78:186-195; I there; CALC `rule_oc2_out.txt`, `review_calc_out.txt`; χ² on the stated df; the σ_eval floor is ignored)

| True σ_pair | P(plan A), 4 df (N) | P(plan B9), 4 df | P(H), 4 df | P(plan A), 30 df (block-A re-check, [B]) | P(H), 30 df |
|---|---|---|---|---|---|
| 3.0 | 94% | 6% | 0% | 100% | 0% |
| 4.0 | 72% | 22% | 6% | 85% | 0% |
| 4.5 | 59% | 28% | 13% | 53% | 1% |
| 5.0 | 48% | 30% | 22% | 24% | 6% |
| 6.0 | 31% | 28% | 41% | 3% | 47% |
| 8.24 (no gain) | 12% | 17% | 71% | 0% | 98% |

The 30-df columns are [B] under S-P (15 df per family). Under [C] the re-check has about 15 df: P(plan A) 100 / 79 / 55 / 33 / 10 / 0% and P(H) 0 / 0 / 3 / 12 / 45 / 93% at a true σ_pair of 3.0 / 4.0 / 4.5 / 5.0 / 6.0 / 8.24 (R: P78:195). N alone reads plan A 12% of the time even with no pairing gain (R: P78:21); SR-2 is the remedy.

### 6.4 SR-2, the blinded re-check after block A (ruling 3)

- **Adopted, on one condition:** the 7-8B kit's record-done step prints no block-A U value, and `scripts/scale78b/blinded_sigma.py` prints σ̂_A and its df only; a test holds that output byte for byte (PLAN §6 risk 12).
- **Block A is the same for every plan** (R: P78:199): the 6 method arms at 1102-1104; R_4 at 1104 and R_5 at 1105; a0 at 1104 (one per family): 21 runs per family.
- **σ̂_A** (S-P): √2 × the residual SD of the arm + seed model per cluster, pooled over the clusters and the families that ran (about 15 df per family). Block B's design is the rule of §6.1 applied to σ̂_A; it replaces N's value; both directions are allowed (R: P78:201).
- **Why it does not leak outcomes (R: P78:204).** σ̂_A is computed after the arm and seed effects are removed, so it does not move with any repair's mean effect; it moves with an arm × seed interaction, which is noise for this purpose. It is a variance-only interim re-estimate; a Part 2 simulation should confirm its small effect on the error rate (§14).
- **Money.** The gate budgets the worst plan SR-2 can reach, H (b) (R: P78:203; CHECK C3): about $190-240 more than plan A over both families, arms only (R: P78:203).
- **Pre-set fallback (ruling 3).** Trigger: the blinding test is not verified before block A's first pod. Then SR-2 is not adopted and N's value decides alone (R: P78:202). `blinded_sigma.py` is built with T4's block-A part (window 2), not in this round.

---

## 7. H, the high-noise branch (ruling 4) [B+C; fixed before N]

**Basis of the table (P78:224-234's formulas, R; the values recomputed for ruling 2's layout, M; ADD A7).** σ = 5.83 pp per arm (the six 7-8B cells pooled, 11 df; unpaired); the unpaired SE = σ√(1/n_R + 1/n_m) with n_R R cells and n_m method cells. Holm's first step: α/6 two-sided for 6 contrasts (z 2.638), α/3 for 3 (z 2.394); 80% power (z 0.842). *Better* = the Holm-adjusted test rejects and the point estimate ≥ SESOI; *equivalent* = the 90% CI lies inside ±SESOI (TOST). P(better) is at most 50% when the true effect equals the SESOI.

| Design (removal contrast; add contrasts about 7% wider) | SE | MDE (80%) | 80% point for *better* | P(*better*) at a true 8 / 10 / 12 pp | P(*equivalent*) at a true 0 / 5 pp | Runs per family (§5) |
|---|---|---|---|---|---|---|
| plan A, SESOI 5 (no branch); R 7, methods 6 | 3.24 | 11.3 | 11.3 | 0.43 / 0.67 / 0.86 | 0.00 / 0.00 (CI half-width 5.34 > 5) | 44 |
| **(a)** plan A, SESOI 10; R 7, methods 6 | 3.24 | 11.3 | 12.7 | 0.27 / 0.50 / 0.73 | 0.85 / 0.46 | 44 |
| plan B9, SESOI 5 (reference); R 10, methods 9 | 2.68 | 8.7 | 8.7 | 0.72 / 0.91 / 0.98 | 0.18 / 0.03 | 53 |
| **(b)** P1, P3, P6 at 12 seeds, SESOI 5; R 13 | 2.33 | 7.6 | 7.6 | 0.85 / 0.97 / 1.00 | 0.38 / 0.05 | 68 |
| **(c)** = (b) with SESOI 10; R 13 | 2.33 | 7.6 | 12.0 | 0.20 / 0.50 / 0.80 | 0.99 / 0.69 | 68 |

The run counts are ruling 2's (P78's 54 and 70 fall to 53 and 68). The SE, MDE and probability columns are recomputed for ruling 2's layout (R at 7 / 10 / 13 seeds against P78's 8 / 12 / 16; M: the normal approximation of P78 §6 with σ 5.83 and the unpaired SE σ√(1/n_R + 1/n_m), which reproduces every P78 row first; script BR `fix-D-scratch/htable_fix.py` in the build round's reports, after the verifier's `verify-D-htable.py`; ADD A7). P78's values were SE 3.15 / 2.57 / 2.23 pp and MDE 11.0 / 8.3 / 7.2 pp; fewer R cells widen the unpaired SE by 3.0 / 4.2 / 4.8% (M). **The S-U values are a sensitivity (ADD A7): ruling 2 stands**, because the primary scale is S-P (ruling 1) and the seed rule reads σ̂_pool on the pair scale. **The paired-contrast caveat (R: P78:234):** under S-P the MDE is a multiple of σ_pair that uses the shared seeds only, 1.42 (plan A, 6 seeds), 1.08 (B9, 9), 0.93 (12 seeds) (M; unchanged by ruling 2's layout). At σ_pair 4.0 plan A at SESOI 5 has an MDE of 5.7 pp and P(*equivalent* | 0) = 0.84, so no branch is needed; at σ_pair 8.2 (MDE 11.6 pp) the branch is needed. N decides which case holds, with §6.3's limits.

- **Ruling 4: (e), money-contingent, with (b) first.** If the seed rule gives branch H: **(b)** on each family that runs (P1, P3, P6 primary at 12 method seeds, ruling 2's layout; SESOI 5 pp; P2, P4, P5 secondary at block A's three seeds with one-sided bounds), if the account after the gate covers (b)'s extra on those families. This keeps the 1B scientific target (R: P78:238, :245).
- **The pre-set fallback chain (money only; a funding event is not an outcome, R: P78:241).** (i) Under [B], if (b) is covered on one family but not on both: the tier runs [C] on F1 at (b) (the gate's B → C cut). (ii) If (b) is not covered on any family: **(d) review**: no 7-8B primary family; the units that ran are reported descriptively (R: P78:240).
- **Why (a) and (c) are the user's (ruling 4).** Both change D5's "SESOI 5 pp" at 7-8B (R: P78:243; RP decision 3; CHECK C13). (a) adds no power; it makes *equivalent* reachable at a margin of 23% of E for OLMo-2-7B and 19% for Llama-3.1-8B against 11% at 1B, and a true 5 pp effect reads *equivalent* 46% of the time at ruling 2's layout (the table above; P78:237 gave 48% at R 8). So the lead's chain does not hold (a) or (c). If the user names (a) in place of (d), it is recorded as the user's choice before N's reading is opened; a change after that point is not adopted for the 7-8B primary analysis (ruling 4 as tightened by ADD A15). Option (b) cuts the family to P1, P3, P6 as PLAN-S's own plan B does at 1B, so it keeps D5's structure (R: P78:243).

---

## 8. F, the family under [C] (ruling 5) [C; fixed before N]

- **Ruling.** **F1, OLMo-2-7B**, fixed now, before N (ruling 5). F3 (the family with the smaller σ̂_F from N) is not used: with 2 df per family it picks the truly less noisy family only 61 / 69 / 80% of the time at true SD ratios 1.25 / 1.5 / 2 (R: P78:324).

**Evidence (R: P78:310-321; the "transfer check" row no longer counts, ruling 6).**

| | OLMo-2-7B (F1) | Llama-3.1-8B (F2) |
|---|---|---|
| Main-recipe a0 seeds in hand | 1101-1103 | 1101-1102; 1103 in N |
| E, pp | +49.67, +37.17, +45.50; mean +44.1 | +52.50, +54.00; mean +53.25; the band holds the 55 pp edge |
| Per-arm seed SD | 6.36 pp (2 df) | 1.06 pp (1 df); not significant: F = 36 on (2, 1) df, one-sided p ≈ 0.12 (CALC `fratio_out.txt`) |
| Answers end (G1 risk) | passed | TOO CLOSE; seed 1102 at 10.5% (§15) |
| Manifest and edit files | SEAL's files byte for byte (same manifest `9ed61826…`) | `c52a50af…`; new files with equal row lists |
| Main-LR a0 e1 adapters on the Mac | 1101-1103 | none; adapter-scaling references need retrains |
| Recipe-G reference at the main LR | 3 units on X | none; 3 new runs |
| Cost per arm at 4 per pod (E) | $2.94 expected | $3.93 expected (KCR:183-188) |
| Gated download | no | yes (the HF token in the Mac environment at each launch; CHECK C13) |
| Generation memory | 99.3% of the card, 204 allocator retries in the check (R: KCR:62) | lower: 8 key-value heads against OLMo-2-7B's 32, a KV cache about a quarter of OLMo's per token, 0 retries in its check (R: KCR:62) |
| External value | open data and weights | the published setting's model (PLAN-S:228) |

- **Basis (ruling 5; P78 §8).** F1 is cheaper per arm; it reuses SEAL's edit files byte for byte (manifest `9ed61826…`); its e1 adapters are on the Mac, so adapter scaling needs no retrain; its recipe-G units are at the main LR; it has no answers-end issue and no gated download.
- **The trade-off (ruling 5; R: P78:325).** Llama-3.1-8B is the published setting's model, and its only noise evidence is lower (a0 SD 1.06 pp on 1 df against 6.36 pp on 2 df; p ≈ 0.12). If that difference is real, F1 picks the noisier family. Under [C] with F1 the Llama replication at 7-8B is lost (the re-plan then puts Alpaca on OLMo-1B; R: P78:325).
- **Pre-set technical fallback (ruling 5).** Trigger: two OLMo-2-7B pods stop before any arm completes because of a memory failure in generation (the preflight's `generation_memory_ok` or an out-of-memory crash; OLMo-2-7B generates at 99.3% of the card, KCR:62). Then **F2, Llama-3.1-8B,** replaces F1 for [C], labelled.

---

## 9. TC, the transfer check: does not run (ruling 6) [B+C]

- **Ruling.** TC does not run. The frozen 1B Gate B reading said **TOO CLOSE** (FOCUS "GATE B CLOSED", recorded 2026-10-23T05:26 UTC; README:94), a planned branch of P78 §7's rule ("if it says DIFFUSE or TOO CLOSE, TC does not run"; R: P78:251). The paper says that localization was tested at 1B only (RP:91). No transfer reader (`scripts/scale78b/transfer_reading.py`) is built; the optional extension of P78:276 is moot (ruling 6).
- **The rule, kept for the record (R: P78:249-295).** TC would have run only after a 1B LOCALIZED, on the unit(s) the 1B reading named (at most 2, the largest Λ_u), removed at seeds 1101-1103 on each 7-8B family that runs, against N's R_1-R_3: c_u,j = U(R_j, j) − U(u, j); Λ_u,78 = the mean over 3 seeds; σ̂_T = max(√P_T, σ_eval,T) with P_T = [2·SD(r)² + 2·Σ_u s_u²]/(2 + 2k); SE_T = σ̂_T/√3; t at 3 df; Bonferroni over k (2.353 for k = 1, 3.182 for k = 2); k_0.90 = 1.638. Labels: TRANSFERS (Λ ≥ 8 pp and Λ ≥ t × SE_T, with the Gate B guards G1-G4 and the direction checks), DOES NOT TRANSFER (Λ + 1.638 × SE_T < 8 pp under G2 and both G3 corners), else INCONCLUSIVE. Simulation (CALC `tc_sim_out.txt`): false TRANSFERS at no effect ≤ 2.4%; a true 8 pp unit reads DOES NOT TRANSFER about 9% of the time (R: P78:23).
- **Consequences.** G1 status of N's R arms stays report-only (§3.5; ADD A4, A11). The Granite judge launch that TC needed per family (R: P78:295) does not run: no Granite judging runs for TC (ADD A9). Any other Granite use is Part 2's judges item (§14 item 6).

---

## 10. The S4 add-dose arm (ruling 12; the user's "Yes, add it", DOSE) [B+C; secondary]

**Label (ruling 12, verbatim).** "Added after the OLMo-2-1B stage-1 reading (the user's yes of 1 Nov 2026), because S4 was the best feasible repair there but did not reach the model-level references' U; confirmatory at 7-8B because no 7-8B repair outcome existed when it was added." The user's words: "Yes, add it" (DOSE `user_words`, answered 2026-11-01 about 23:05 UTC). Why: S4 (48 refusals the untuned model gave to S-pool prompts) was the best feasible repair at 1B (P6 better, +18.28 pp against S1; restoration 15.97 pp), but Safe LoRA, B+Qi and the safety prefix reached a lower U than S4 with more over-refusal; the arm asks whether more self-distilled refusals close that gap within the O and L limits (DOSE `why`).

- **Name.** "S4 add-dose" (CHECK C2: stage 1 uses "dose" for the random-removal dose curve, `scripts/stage1/dose_axis.py`). Doses **S4_96** and **S4_192**.
- **Contrasts and sign.** **AD1 = U(S4) − U(S4_192)** and **AD2 = U(S4) − U(S4_96)**. PR4's sign: positive = the larger dose restores more (PR4:228). "AD" because PR4 uses "D1" for a design and FOCUS uses "D5" for the user's decision (ruling 12).
- **Construction (per model and manifest; CHECK C6; PR4:131's S4 row).** The family's own untuned model's greedy answers to the S-pool minus S1, in S4's sealed order (`stage1-s4-v1`, 512 prompts in 32-prompt chunks), kept only if ended, REFUSAL-OPENING by LEX, non-empty and accepted by `encode_train`. **S4 = the first 48 kept, S4_96 = the first 96, S4_192 = the first 192 (nested).** One untuned-answers pass per family makes all three lists; the S4 job's stop rule moves from "the chunk that holds the 48th" to "the chunk that holds the 192nd"; the first 48 are unchanged (ruling 12). The edits bind to the family's manifest; S3, S4 and the dose edits are per model, not per manifest (CHECK C6), so Llama-3.1-8B's differ from Llama-3.2-1B's.
- **The 1B keep count (ruling 12, M2; counts only, read 5 Nov 2026).** The 1B pass answered 64 candidates in 2 chunks and kept 57 (26 of 32, 31 of 32; 7 not refusal-opening; 9 kept after the 48th): 89%. At that rate 192 kept rows need about 216 of the 512 candidates (E: 192 / 0.89). Source: `tmp/stage1-olmo/retrieved/a-1/tree/job-0/untuned/untuned_answers_record.json`, read by the lead by exact path after its SHA-256 check (`5e69b09c…`); only the S4 list's chunk and drop counts were printed (ruling 12).
- **Pre-set fallback (DOSE `pre_set_fallbacks[0]`; ruling 12).** Fewer than 192 kept after the whole 512-prompt list: the top dose is all kept rows, counted and reported.
- **Seeds (ruling 12; the ambitious default with its fallback; written at the gate from money only).** **6 seeds (1102-1107)** if the money after the gate covers B's or C's primary needs (§1) plus 6 seeds; else **3 seeds (1102-1104)**; else the arm is the first secondary item cut (DOSE `pre_set_fallbacks[1]`). A funding event is not an outcome (P78:241).
- **Reading (ruling 12; CHECK C2).** **Secondary.** Outside Φ, outside the Holm family of P1-P6 and outside the primary HB-C fit (PR4:234: "Reference and secondary arms never enter this fit"; the dose arms run 39 steps, so they are not in the 38-step full-corpus cluster). AD1 and AD2 are read by the paired-mean estimator on their common seeds with S4, plus the prompt part, in their own fit: PR4's P6-under-plan-B form, a paired t on the pairs plus the prompt part (PR4:281). Labels *better / equivalent / inconclusive* at the 7-8B SESOI (5 pp) with one-sided bounds, as PLAN-S §5.3 does for secondary arms (R: P78:238). A monotone-dose summary (the three doses' means) is reported. Against the model-level references within the O and L limits, by the frozen dominance rule's form (PR4 §5.3; family 1b at 1B): "does the top feasible dose beat every reference?". A dose that breaks O or L is reported *infeasible* (DOSE `limits`). Part 2 fixes the O and L forms (§14, M1).
- **Compute (ruling 12; stated, not corrected away).** S4: 4,848 rows → 38 steps; S4_96: 4,896 rows → 39 steps; S4_192: 4,992 rows → 39 steps (128 rows per step). The study is compute-matched, so the step counts and padded-token totals are printed beside AD1 and AD2 (the token-accounting report of S1L §5 item 1 via P78:379); the +1 step is part of the dose.
- **Where it runs and what it costs (ruling 12).** With block B, under the family's main config, like every add arm. Cost about **$49** (3 seeds, both families) to **$99** (6 seeds); per family OLMo $21 / $42, Llama $28 / $57 (E: PLAN §4, at the planning rates $3.53 and $4.71 per arm). Its judges ride on the block's judge pods (PLAN §5.9).
- **Prediction (ruling 13; written 5 Nov 2026, before any 7-8B repair outcome).** AD1 point **+5 pp** (80% interval −1 to +12); AD2 point **+2.5 pp** (80% −2.5 to +8); O rises with the dose (+1 to +6 pp at S4_192 against S4); the top dose stays within the O limit with probability about 0.6 per family; *better* for AD1 has probability about 0.2 at 3 seeds and 0.3 at 6.
- **Power note (E; PLAN §5.9, the normal approximation of P78 §6).** At 3 seeds the paired SE is about σ_pair/√3: 2.3 pp at σ_pair 4 pp, so only a dose effect of about 7 pp or more reads *better*.
- **Integrity (DOSE `integrity`).** On OLMo-2-1B the arm could only be exploratory (chosen after the result), so it is not added there. At 7-8B and Llama-3.2-1B it is written before any repair-arm outcome of that model exists, so it can be confirmatory. It never enters Φ, the Holm family or the primary HB-C fit.

---

## 11. EM-1 to EM-5 revised; what stays frozen [B+C]

- **EM-1, engine and environment (P78:333 revised by ruling 10).** Every 7-8B arm that pairs with an engine-X unit (N, blocks A and B) trains and evaluates on engine X (`472fc7f6…`), unless the family's Y certificate of §3.7 has passed; then every 7-8B arm of that family, B+Qi included, may run on Y. The A1 pass runs on the engine that trained its a0 states (EYD:81). The environment rule: Gate B's (PRE:107 via P78:80), with the family's a0-1101 unit as the reference. On an environment mismatch: ruling 7's fallback (§2.3): the a0-free N re-read and +3 a0 runs per family in the new environment before any paired contrast.
- **EM-2, money isolation (P78:334 revised by rulings 9 and 11; CHECK C8).** A 7-8B pod launches only on money in the account (MONEY `lead_reading[0]`; the 29 Oct start-from-the-balance rule). The kit's `init-block --funding` record must cover the cap-based need, 1.25 × the worst path (PLAN §1.4). The $6 reserve, the planning rate $1.85/h, the $10/h creation limit and the in-pod caps stay (RUL header). **Gate B's hold is gone:** `GATE_B_HOLD_USD = 0`, reason "Gate B closed 23 Oct (FOCUS 'GATE B CLOSED', recorded 2026-10-23T05:26 UTC); its last judge pods deleted 31 Oct" (ruling 11 KD4; CHECK C8: one stopped Gate B pod, `gateb-w0b-2`, is still kept; it changes nothing here). So P78's "$129 or more in the account" (P78:111) lapses; N's need is about $56 (§3.2). Working copies are `tmp/family-probe-s78-<family>-<block>/` (ruling 11 KD7), `KITS_GLOB` unchanged (CHECK C7), with the shared lock `tmp/family-probe-budget.lock` (R: P78:334), so the stage-1 kit's frozen `budget.py` sees every 7-8B cap.
- **EM-3, seeds (P78:335).** 7-8B main-study seeds stay inside 1101-1116. The dose arm's seeds (1102-1107 or 1102-1104) lie inside. No scorer built on a0-1101 states is evaluated at 1101 (A1, L1). The confirmation uses fresh seeds 9101-9999 (README:86; Part 2).
- **EM-4, testing families (P78:336).** Each (family, size) is its own Holm family at 5%; no α is shared with 1B. "Replicates at 7-8B" = the same sign, with the size difference below its stated MDE. D5 = (a) holds: P1-P6 (or P1, P3, P6 under plan B9 or H (b)) are primary; the selector is secondary and model-based; no selector runs at 7-8B (I from F L78, as P78:336). **The S4 add-dose arm is secondary** (ruling 12). The dominance family D_1…D_6 (PR4 §4.7, 1b) is read per family after Φ.
- **EM-5, blinding line (P78:337).** §0 above is Part 1's line. Part 2 adds N's values in the same form.

**What stays frozen now (PLAN §5.11; CHECK C8, C12).** The Gate B-era T4 list (P78 §9.3, "until Gate B's last kit pod") lapsed when Gate B closed on 23 Oct. What stays frozen: engine X's files (the identity `472fc7f6…`); engine Y's frozen tree (frozen 23 Oct; certificate C1 passed 27 Oct; R: PLAN §1.2); the stage-1 S1 package by its `S1_CODE` pins and the 1B Part C scripts under `scripts/stage1/` (stage 1c and stage 2 still run them); the sealed files (SEAL `out/**`, the anchors, recipe S `ceffe0ef…`); the stage-1 kit `runkit/stage1-olmo/` (copied, never edited); the three 7-8B sealed input folders of §3.1 and their build scripts from their first commit on (ADD A3). Every 7-8B file is a new file at a new path, committed by explicit path; after each commit the lead re-checks the engine identity `472fc7f6…` and the stage-1 S1 pins (ruling 11 KD8). New configs under `SS/configs/` are committed additions by explicit path (KD8); the OLMo 3 configs are not yet committed, so there is no commit precedent, and the T4 freeze's lapse is the reason this is allowed (CHECK C12). The any-model Part C scripts are new files under `scripts/scale78b/` with a 1B parity test; the 1B scripts stay byte for byte (R: P78:357, :407).

---

## 12. The kit route and the pre-block-A scorer kinds (ruling 11) [B+C]

The 7-8B kit is **route (ii)** (KD10): a copy of the stage-1 kit `runkit/stage1-olmo/` to `runkit/stage1-78b/`, the original untouched (stage 1c and stage 2 still read it), with per-family constants from `rules_78b.py` (the M-cap rule, KD1, the basis file's maxima governing, ADD A5; its fallback, KCR alternative 1 with 7-8B measured constants, only if T2 is not verified by 12 Nov, which does not fire if the fix round's re-check passes and the lead merges T2 before 12 Nov, ADD A12; `RECIPE_S` pinned null for both families until each family's S_78 is written after its anchor job, every kind that needs S_78 refusing until then, ADD A1; `ENGINE_Y`, `RECIPE_G`, `RECIPE_BQI` and the Llama sealed set's MANIFEST pin null in the same way until the lead fills each by a recorded step, with E-capped kinds on engine Y once `ENGINE_Y` is filled and measured kinds on Y only after KD9, ADD A13) and the gated-token launch path ported from `runkit/family-probe/launch.py` with its own tests and a separate review. The block-0 subset comes first: `arm` (R_1-R_3 under the family's main config), `a0_arm` (Llama 1103), `retrain` (ruling 10; one single-job pod per family after that family's anchor job and S_78, ADD A2, A8), and the **pre-block-A scorer kinds** that CHECK C1 moved before block A: `untuned_answers`, `o_only` / `regenerate` for both untuned units (M1: the 7-8B untuned units need stage 1's O and L evaluation), the anchor job, `rep_pass` (A1), `l1_scan`, `classifier`, `c0`, each single-job with an explicit E cap (KD6; A1's pass at RP:43's 6-11 h is a 16.5 h cap at most) until measured, then the basis updated by a recorded lead step; `s_obs` after each arm (KD11); the free-space check before each job and 50 GB volumes with the OLMo 3 kit's state rule (pull the e1 states, verified backup, the user's yes by pod name before any delete; the kit has no delete command; KD5); an idle-storage line in each block's need (KD5; about $0.33 per day per stopped 50 GB pod, KCR:161); record-done prints no block-A U (SR-2's condition, §6.4). At most 4 counted arms per pod on both families (KD2, a lead ruling under the delegation, not a prior user confirmation; CHECK C11). `plan_tool.py init-block 0` prints the need of N's pods, the retrain pod and the scorer pods separately (M3). Details live in the kit (KCR §12; `runkit/stage1-78b/` README), not here. Scorer outputs are read only after Part 2's scorer rules are committed with code hashes (P78:367; CHECK M4).

---

## 13. Choices made after a stage-1 result (ruling 16; Part 1 labels each one)

1. **The S4 add-dose arm and its doses** (§10): motivated by P6 and the best-feasible-repair result of the stage-1 reading (DOSE). Confirmatory at 7-8B because no 7-8B repair outcome existed when it was added; the label states the date and the reason.
2. **Keeping P1-P6 all primary at 7-8B** although P2, P3 and P5 read *equivalent* at 1B: dropping or re-weighting arms by their 1B labels was considered and rejected, because it would be a choice after a result.
3. **Predictions N1, N2 and the dose prediction** (§3.6, §10): written after the stage-1 reading (5 Nov 2026). The quantities they predict were not read at 1B's stage 1.
4. **S, SR-2, H, F, the thresholds, the seed layout and the gate** (§4-§8, §1): decided after the stage-1 reading; none reads a 1B repair outcome (S follows the model frozen before stage 1; F reads cost, files and gating; H reads money and D5; SR reads N; the layout follows PR4). (Rulings 7, 8, 10 and 11 were recorded the same day, 5 Nov, and read files, fingerprints, caps and costs only; ruling 16's list names them, as extended by ADD A16.)
5. **The confirmation's pick rule at 7-8B:** the frozen stage-3 rule (the two primary contrasts with the largest |t| among those reading *better* or *worse*; PR4:428; README:86) per family. The 1B pick (P6, then P1) is a 1B result and never selects 7-8B contrasts.
6. **TC's non-run** (§9) follows Gate B's TOO CLOSE, a planned branch of a rule written before the verdict.
7. **Any use of stage 1's HB-C arm variances** in 7-8B power planning is labelled "read from the stage-1 reading"; this text uses only the pre-stage-1 values (Gate B wave 0a; the probes' a0 spreads).
8. **The starting rule:** the 7-8B tier starts on money in the plan's order (NEXT's step 2, row 6, via PLAN §1.1), never because P6 or P1 read *better*.
9. **The 1B S4 keep count** (§10; ruling 12, M2): a θ0 count from stage 1's untuned-answers pass, used only to size the dose arm's fallback.
10. **The addendum's A1-A17** (ADD; A1-A12 recorded 2026-11-05T14:41-14:44 UTC and A13-A17 at 15:45 UTC, after the stage-1 reading; "no stage-1 outcome was read for them", ADD header). **None reads a 1B repair outcome.** Which of them is a choice made after a stage-1 result, and which is not: A1, A2, A3, A5, A8, A10 and A12 are build and process rulings that read files, hashes, pod counts, caps and costs (the anchor file's hash check, the sealed folders' paths, the constants' rounding, the retrain pods, Part 2's file name, T2's merge); A6 is the noise reader's form and A7 is arithmetic on the layout; A9 places judging. None of these touches a stage-1 result. A4 and A11 read the Llama G1 check's counts (the coherence screen on 7-8B a0 units, §0 item 4), which is a 7-8B a0 count, not a repair outcome and not a stage-1 result; they also read PR4 §3.7's bar, which was itself chosen at 1B after a0 1101-1103's screen rates were read (PR4:298, a θ0 count). So no addendum item is a choice made after a stage-1 repair result; A4 and A11 are the two that read any outcome at all, and that outcome is a 7-8B coherence count. A13-A17 (engine Y's pin; N2's basis; ruling 4's timing; ruling 16's list; one money basis) read pins, the layout's arithmetic and costs only; none touches a stage-1 result.

---

## 14. Part 2 (`research/experiments/<date>-78b-preregistration-part2.md`, ADD A10; frozen like Part 1 before block A's first pod; its scorer section committed before any scorer output is read)

As P78 §11 (:377-379), plus the items the check and the rulings add:

1. **Arm rules per family:** A1 (an anchor job per family, then recipe S_78 written by the maker from the family's anchor file and committed, ADD A1, A2; the a0-1101 retrain of §3.7); L1 (the layer rule from the any-model Part C scripts); H1 (by the family manifest's target tokens; OLMo-2-7B's equals 1B's; Llama's is a new count with Llama's tokenizer, shared with Llama-3.2-1B); the S-pool and S1 (the same 48 S-pool rows, re-bound to the family manifest; CHECK C6); S3 and S4 from the family's own untuned answers; the two dose edits (§10), per model and manifest (CHECK C6).
2. **The scorer rules, committed with code hashes before any scorer output is read** (P78:367, :413; CHECK M4): A1 per family with its anchor job; L1's layer rule; H1 by the family manifest; the per-family untuned-answers pass as the shared source of S3, S4, S4_96 and S4_192; the dose edits' hashes. The rest of Part 2 is frozen while the scorer pods run, before block A's first pod (CHECK M4).
3. **O and L at 7-8B (CHECK M1):** every arm needs O against the family's own untuned model and task loss L (PR4 §3.6's O set of 500 prompts); the side probes' untuned units were evaluated with the family-probe bank, not stage 1's O set, so the `o_only` / `regenerate` / `untuned_answers` jobs run for both untuned units before block A (§12). Part 2 says which evaluation bank the 7-8B arms use and whether the `arm` kind evaluates O and L in the same job, as at 1B, or needs a separate job. The τ_O grid; τ_L from the family's a0 seeds (S1B REQ-19 form).
4. **References:** the safety prompt; adapter scaling (OLMo-2-7B from the Mac adapters; Llama-3.1-8B from retrains); recipe G (OLMo-2-7B units in hand; Llama-3.1-8B 3 new runs); B+Qi (on Y after its basis is measured, KD6/KD9; unpaired and labelled if Y ≠ X, §3.7); Safe LoRA.
5. **The S4 add-dose arm's reading:** the O and L forms for AD1, AD2 and the dominance-rule question (§10); the token-accounting line.
6. **Judges:** HarmBench and Granite pods, one device per contrast; which arms and blocks are judged; the "harm" wording rule. Settled already (ADD A9; §3.5): N's R arms are HarmBench-judged, report-only, with block A's judge pods; Llama a0-1103 gets the same judge files as block A's units on the same pods; no Granite judging for TC.
7. **The coherence screen at 7-8B (settled; ADD A4, A11; §15):** PR4 §3.7's bar for the main study's arms, read on an arm's answers pooled over all its seeds; per-seed counts reported; a seed above 10% flagged; no arm or seed dropped; the frozen Gate B G1 code, report-only, for N's R arms. Part 2 writes the form out and names the screen's code hash.
8. **Cost conventions.**
9. **The confirmation's design** (PR4 §4.8; README:86): at most 2 contrasts per family, chosen by the frozen pick rule (§13 item 5); engine Y; fresh seeds 9101-9999; the sealed 200-prompt hidden subsample; "confirmed" by the 95% interval on the hidden subsample only.
10. **SR-2's error-rate check:** a simulation that the variance-only interim re-estimate changes the error rate little (P78:204).
11. **Alpaca's home** ([B] Llama-3.1-8B, reduced; [C] OLMo-1B; RP decision 7).
12. **The Llama sealed set's manifest-named files** (R, the unit files) shared with stage 2; H1 in its own sealed folder (ADD A3); S1 on the Llama manifest still to be built before block A (track B's stop rule: it needs the sealed list's text and the Llama codec); S3, S4 and the dose edits named by model (CHECK C6).
13. **Part 2's blinding line:** N's values seen (EM-5).

---

## 15. Limits and weak points

- **Money is an expectation, not a balance** (MONEY `what_it_is`). Every date here that depends on it ("about 20 Nov", "about 1 Dec") is an expectation. Nothing 7-8B launches before the money is in the account.
- **σ_pair at 7-8B rests on 4 df after N** (R: P78:421). §6.3 shows how often the rule then errs; SR-2 is the remedy, and SR-2 itself is conditional on the kit's blinding test (§6.4).
- **S-P assumes an additive seed effect** per cluster (R: P78:422). N's planning value (a0 against R) may not hold for method arms, which remove selected rows.
- **σ̂_pool assumes equal paired noise in both families**; the a0 point estimates differ about 6× (R: P78:428). Under [C] the provisional plan may be moved by the other family's spread; SR-2 corrects it from the chosen family's own units.
- **The thresholds mean a paired MDE of about 6.4-6.5 pp, not 6.0** (R: P78:430); kept by ruling 3 and stated.
- **The S-U exclusion of plan A rests on a 0.03 pp margin** and on the reuse of the side units (R: P78:429); under S-P it is a sensitivity statement only.
- **SR-2's blinding is procedural**; the kit's records show U (R: P78:426). The condition in §6.4 is the control.
- **The Llama-3.1-8B G1 risk (R: P78:272) and the $0 check's result (ADD A4).** The check ran on 5 Nov (track C; the frozen Gate B guard code on the a0 units' records; counts only; M there, confirmed by track C's verifier). Llama a0-1101 passes G1 (42 of 600 fail the screen). **a0-1102 fails G1:** 63 of 600 (10.5%) fail the screen, 43 of them short answers (20 of 557 = 3.6% without them), so the answers-end check reads TOO CLOSE, which PRE:147 counts as a G1 failure. OLMo-2-7B a0-1101, -1102 and -1103 pass (23, 20 and 16 of 600). **Ruling (ADD A4):** 1B's G1 stays unchanged (P78:272's recommendation). In N, G1 is report-only (§3.5) and TC does not run (§9), so nothing is blocked. In the 7-8B main study the coherence screen is stage 1's (PR4 §3.7): the bar is read on an arm's answers pooled over all its seeds, per-seed counts are reported, a seed above 10% is flagged, and no arm or seed is dropped. On the two seeds read so far Llama a0's pooled screen count is 105 of 1,200 (8.75%, computed from the record's counts); the arm's reading uses all its seeds after block A. If Llama's R and method arms behave like a0-1102, their per-seed flags will be frequent and the pooled bar decides. The user is told before the Part 1 freeze (P78:272; the lead's report of 5 Nov).
- **OLMo-2-7B generates at 99.3% of the card** (KCR:62; ruling 5). A different host build could run out of memory; the preflight's `generation_memory_ok` and `s_obs` are the controls; ruling 5's technical fallback is F2.
- **The per-arm costs assume 4 arms per pod**; no 7-8B pod has yet run more than two units (R: P78:424). KD2's fallback is 3 on Llama.
- **The S4 add-dose arm at 3 seeds has little power** (E; §10): a paired SE of about 2.3 pp at σ_pair 4 pp, so only a dose effect of about 7 pp or more reads *better*; the 6-seed default is money-contingent.
- **Compute-matched framing against the dose arm:** 39 steps against 38 (+2-4% tokens; PLAN §6 risk 6). Disclosed, not corrected (§10).
- **The 1B stage-1 outcomes are known to the authors.** §0 lists them and §13 labels every choice they touched. The 7-8B tier's primary family, its SESOI, its model and its seed rule follow texts frozen before those outcomes.
- **The retrain-as-certificate** needs the X retrain as a second job to separate an engine difference from a pod difference (CHECK C4); until it runs, a Y mismatch is ambiguous and paired arms stay on X.
- **All MDE and TOST figures use the normal approximation**; with t at the stage's residual df they are slightly wider (R: P78:427). The H table uses the unpaired SD 5.83 pp (R: P78:234).
- **Builder usage and the calendar** (PLAN §6 risk 2): the kit's block-0 subset is the long pole; if the money slips past about 1 Dec, B no longer fits the 4 Jan freeze with its confirmation, and the gate re-checks (ruling 9).

---

## 16. Change log against P78 (every place this text departs from P78, and why)

| # | P78 place | P78 said | This text says | Why |
|---|---|---|---|---|
| 1 | Status, §10 | "DRAFT. It adopts nothing"; Part 1 frozen before Gate B wave-1 outcomes, else before N | frozen 5 Nov 2026 (status line); adopts the rulings; frozen by SHA-256 in FOCUS and a commit before block 0's first `launch.py`, by about 19 Nov | MONEY `lead_reading[2]`; ruling 14 |
| 2 | §4, §12 [USER] 1 | S is the user's decision | S-P (HB-C per family, PR4's form) by the lead's ruling; S-U the sensitivity | ruling 1; CHECK C14 |
| 3 | §4 S-P row | "two-way additive model, arm + seed" | the frozen HB-C form (two clusters, REML σ²_a, Satterthwaite) | ruling 1; PR4:233-240 |
| 4 | §4 seed layout, §5.1 table | R at 1101-1108 (R_8 for S-U); a0 1101-1106 (+1107 proposed); B9 R 1101-1112; H (b) R 1101-1116 | R from 1101 to the last method seed (1107 / 1110 / 1113); a0 1101-1107 in every plan; no unpaired R seed | ruling 2; PR4:240 |
| 5 | §5.4 | runs per family 44 / 54 / 70 | 44 / 53 / 68; the money figures stay as upper bounds | ruling 2 |
| 6 | §5.1, [USER] 11 | thresholds 4.5 / 6.0 recommended; rescaling the user's option | 4.5 / 6.0 kept; 4.22 / 5.56 not adopted; the paired MDE 6.4-6.5 pp stated | ruling 3 |
| 7 | §5.1, [USER] 8 | the review ceiling, "the user may change it" | kept as the lead's ruling | ruling 3 |
| 8 | §3.3, [USER] 10 | SR under [C]: pooled or the family's own σ̂_F, the user's | pooled σ̂_pool provisional; SR-2's σ̂_A decides block B; σ̂_F (2 df) if SR-2 falls | ruling 3 |
| 9 | §5.3, [USER] 3 | SR-2 yes or no, the user's | adopted on the blinding condition; fallback: N decides alone | ruling 3 |
| 10 | §6, [USER] 2 | H: the user's; recommended (e) with (b) first, else (a) | (e) with (b) first; then C on F1 at (b); then (d) review; (a) and (c) only by the user's word | ruling 4 (they change D5's SESOI) |
| 11 | §8, [USER] 4 | F: the user's; F1 recommended | F1 fixed; technical fallback F2 after two memory failures in generation; "cleaner transfer test" dropped as a reason | rulings 5 and 6 |
| 12 | §7, [USER] 5 | TC's rule and the optional extension | TC does not run (Gate B TOO CLOSE); the rule kept for the record; no reader built; the extension moot | ruling 6 |
| 13 | §2.3, [USER] 6 | reuse of the side units is the user's (RP decision 5) | the lead's ruling with the fallback (+3 a0 runs, the a0-free re-read) | ruling 7 |
| 14 | §3.1, [USER] 6 | the Llama 1103 rule, "[USER] confirms" | the lead's ruling 8 | ruling 8 |
| 15 | §5.1, [USER] 7 | restate decision 2 as "B if the account covers B at the plan this rule gives, H included; else C" | the gate reads money and N only; B if the account covers the primary plan with (b)'s extra, references, scorers, judges, storage and the confirmation in sight; else C on F1; the 1 Dec re-check; the earmark | ruling 9 |
| 16 | §9.1 EM-1, [LEAD] 11 | every paired arm on X; Y only after a certificate, unsettled | the Y retrain first; the X retrain as the pre-set second job; only an X mismatch triggers the fallback | ruling 10; CHECK C4 |
| 17 | §9.1 EM-2, §3.2, [USER] 9 | Gate B's $83.91 hold; about $129 in the account for two N pods | `GATE_B_HOLD_USD = 0`; N's need about $56; the funding-record rule and the frozen limits stay | ruling 11 KD4; CHECK C8; KCR:177 |
| 18 | §9.2 item 4, [LEAD] 12 | kit `runkit/scale-78b/` or KCR's `runkit/stage1-78b/`; one name needed | `runkit/stage1-78b/`, a copy of the stage-1 kit (route (ii)); working copies `tmp/family-probe-s78-*`, `KITS_GLOB` unchanged | ruling 11 KD10, KD7; CHECK C7 |
| 19 | §3.2, [LEAD] 9 | Llama N pod: one 4-job pod or two 2-job pods | one Llama pod, 4 jobs, cap 12.5 h; one OLMo pod, 3 jobs, cap 8.5 h; in parallel | ruling 11 |
| 20 | §3.2 caps | "from the measured job upper times" | the M-cap rule's caps and margins (KD1-KD3); 4 arms per pod (KD2) | ruling 11 |
| 21 | §3.1 N's runs | N = 7 runs, two pods | N's 7 runs plus the a0-1101 retrain pod(s) on Y; the pre-block-A scorer kinds follow N | ruling 10; CHECK C1, C4, M3 |
| 22 | §3.5, [LEAD] 1 | N1 proposed 1-4 pp; N2 about 4.0 / 8.2 | N1 +2.5 pp (80% −1.5 to +6.5); N2 4.5 pp (80% 2.5-8.5), with the plan probabilities | ruling 13 |
| 23 | — (absent) | no dose arm | the S4 add-dose arm, §10, with its label, construction, fallback, seeds, reading, compute, cost and prediction | ruling 12; DOSE; CHECK C2, C6 |
| 24 | §9.1 EM-4 | the testing families | plus: the S4 add-dose arm is secondary | ruling 12 |
| 25 | §9.1 EM-5 | Part 2 states N's values seen | Part 1's blinding line (§0) lists every stage-1, Gate B, stage-1b and probe value seen; Part 2 adds N's | PLAN §5.0; ruling 12 (the keep count) |
| 26 | §9.3 | the T4 list "until Gate B's last kit pod" | lapsed with Gate B's close (23 Oct); §11 "what stays frozen now"; configs committed by explicit path | CHECK C8, C12; ruling 11 KD8 |
| 27 | §9.2 item 2 | the Llama files "also serve Llama-3.2-1B" | R, the unit files, H1 and S1 are by manifest and shared; S3, S4 and the dose edits are per model | CHECK C6 |
| 28 | §9.2 item 2 test | remove lists equal SEAL's for R_d1-R_d5 and the 8 unit files | plus R_d6-R_d8 equal stage 1's `r-draws/edits/R_d6-8` | CHECK C5 |
| 29 | §11 Part 2 | the list of :377-379 | plus O and L at 7-8B (M1), the freeze window (M4), the dose arm's reading, the confirmation's design, SR-2's simulation, the coherence screen | CHECK M1, M4; ruling 12; P78:204 |
| 30 | — (absent) | no labelled list of choices after a result | §13 | ruling 16 |
| 31 | §0 item 2 | "A scale mismatch decides most of the seed question" | kept as a record under S-U; under S-P the plan is decided by N | ruling 1 |
| 32 | §8 evidence table | "Transfer check from OLMo-1B" row | dropped from the reasons (TC does not run); gated download and generation memory added | rulings 5 and 6 |
| 33 | §3.2 judges | "HarmBench report-only; Granite for TC" | Granite not needed for TC; judging placed in Part 2 and §17 | ruling 6 |
| 34 | §12 [LEAD] 7 | the Llama G1 $0 check before the freeze | done 5 Nov; the result and the ruling in §15, §0 item 4, §14 item 7 | ruling 14; ADD A4 |
| 35 | §6 table | SE 3.15 / 2.57 / 2.23 and MDE 11.0 / 8.3 / 7.2 at R 8 / 12 / 16; P(*better*) and P(*equivalent*) at those SEs | SE 3.24 / 2.68 / 2.33, MDE 11.3 / 8.7 / 7.6, and the probabilities recomputed at R 7 / 10 / 13 (M); the S-P multiples unchanged; "ruling 2 stands" | ruling 2's layout; ADD A7; the verifier's D1 |
| 36 | §4 S-U | S-U at P78's R seeds | S-U at the plan's R seeds (7 / 10 / 13), its SE §7's | ruling 2; ADD A7 |
| 37 | §9.1 EM-1, §11 | recipe S at 7-8B unspecified in time | S_78 written by the merged maker after each family's anchor job; `RECIPE_S` null until then; the kinds that need it refuse; (B) rejected | ADD A1 |
| 38 | §3.1, §9.1 | the a0-1101 retrain as block 0's certificate | per family: the anchor pod, then S_78, then the Y retrain, then the X retrain only if Y differs | ADD A2 |
| 39 | §9.2 item 2 | one Llama sealed set | three sealed input folders (the Llama set; OLMo R_d11-R_d16; the Llama length rules), staying where built; the write guards fixed and the sets rebuilt before the first commit | ADD A3 |
| 40 | — (absent) | no coherence-screen ruling at 7-8B | PR4 §3.7's pooled bar for the main study's arms; the frozen G1 code, report-only, for N's R arms; the G1 counts in §0 and §15 | ADD A4, A11 |
| 41 | — (KCR §3-4) | KCR's printed requirements (rounded constants) | the basis file's maxima govern; at most 1.2 s apart; caps, guards and spends identical to the cent | ADD A5 |
| 42 | §3.3 | the a0-free fallback per family | one family's fallback in the pooled median: its three R-arm pair terms with the other family's three seed-matched terms | ADD A6 |
| 43 | §3.2 | "the retrain pod" (one) | one single-job retrain pod per family: two under [B], F1's only under [C]; each a 4.5 h cap until measured; its own need line | ADD A8 |
| 44 | §3.2 judges | HarmBench judging of N's R arms as a cost, unplaced | report-only, with block A's judge pods; Llama a0-1103 the same judge files on the same pods; N's gate reads the engine's U only; no Granite for TC | ADD A9 |
| 45 | §10 | Part 2 "a separate file" | `research/experiments/<date>-78b-preregistration-part2.md`, frozen like Part 1 before block A's first pod | ADD A10 |
| 46 | — (KCR §12 KD1) | KD1's fallback on "T2 not verified by 12 Nov" | does not fire if the fix round's re-check passes and the lead merges T2 before 12 Nov; the merge commit in FOCUS | ADD A12 |
| 47 | §9.1 EM-5 (via §0) | — | the blinding line's items 1 and 2 extended (the HarmBench sentence words, P3's and P2's L states, S4 against A1 +7.08, the adapter-scaling line, no O or L rejection, the R-arm against a0 SDs, Gate B's final unit reading) and item 8 added (stage 1b's construction checks) | the verifier's D2 |
| 48 | §5.4 money; §12 | no block-A per-launch need; "what needs the user" scattered | the $105-125 per four-pod launch row (CHECK C14); one "what still needs the user" list (CHECK C13); citations PR4:428, README:93, PLAN §5.1, PLAN:297; N2's pooled-point wording; the Llama memory cell cited | the verifier's D3-D9 |
| 49 | (this text) | — | the re-verifier's RV1-RV5: MONEY's SHA-256 prefix; the sealed folders' contents (S1 not built; H1 in its own folder) and the write-guard fix RV-1; the 46% rate at ruling 2's layout; the short names PRE, PLAN-S, S1L, F L*n*, NEXT and BR; KD5's idle-storage line | the fix round's pre-freeze review |
| 50 | §3.6, §5, §6.1, §7, §12, §13, §17 | — | ADD A13-A17: engine Y's pin and the other null-until-filled pins; N2's basis corrected; ruling 4's timing clause tightened; ruling 16's list extended; one money basis; the review ceiling's exact form in the noise reader; §17 closed | the lead's addendum after the fix round |

---

## 17. Open items for the lead (what is still open after ADD; this text decides none of them)

**Closed by ADD** (the round-1 draft's items, each with its addendum entry): item 1, the Llama G1 check → ADD A4 (the result and the ruling are in §15, §0 item 4, §14 item 7; the user is told before the freeze); item 3, the retrain pod count and cap → ADD A8 (one single-job pod per family; 4.5 h until measured; §3.7, §3.2, §1); items 5 and 12, N's R arms' judging and Llama a0-1103's judge files → ADD A9 (§3.5, §14 item 6); item 9, Part 2's file name and freeze record → ADD A10 (status line, §14); item 10, the 7-8B coherence screen → ADD A4 and A11 (§14 item 7, §15); item 13's KD1 part → ADD A12 (§3.2, §12). Not open items but pre-set rules or deferred work, so dropped from this list: item 4 (the scorer pods' caps are the kit's KD6 caps until measured; Part 2 and T4), item 6 (the dose arm's seed count is written at the gate from money by ruling 12's rule), item 7 (Part 2's choice, with ruling 16 item 7's label if cited), item 8 (SR-2's blinding test is ruling 3's pre-set trigger), item 11 (the gate's dates are expectations; the lead records the actual dates), item 13's KD2 part (a pre-set kit fallback, §3.2).

**Still open:** none. The four decisions the fix round's draft left open are closed by ADD A14 (N2's basis), A15 (ruling 4's timing clause), A16 (ruling 16's list) and A17 (one money basis). The freeze (ruling 14) was done by the lead on 5 Nov 2026: the reviewer's read (the fix round's re-verifier, BR `reverify-D.md`; its RV1-RV5 applied); the user told of the G1 result (ADD A4; P78:272) in the lead's report of 5 Nov; KD1's fallback not fired (T2 merged on 5 Nov, before 12 Nov; ADD A12) and KD2's Llama fallback not fired (block 0 has not run); the commit by explicit path; its SHA-256 in FOCUS; `scripts/stage1/commitments.py check`. The three sealed input folders (§3.1; ADD A3) and `scripts/scale78b/` (ADD A1) are merged by explicit path after their write-guard fix (RV-1) and rebuild; they are inputs, not part of this text's decisions.
