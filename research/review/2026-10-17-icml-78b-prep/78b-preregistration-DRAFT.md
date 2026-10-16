# 7–8B pre-registration, Part 1 (DRAFT): noise block, seed rule, high-noise branch, transfer check, family choice

**Status: DRAFT. It adopts nothing. It is not frozen. It authorizes no run and no spend.** Written 2026-10-16, about 21:00–22:05 UTC (17 Oct IST; clock checked with `date -u` at 21:45, 21:54 and 21:59 UTC) by an Opus worker for the main-study lead (General Implementation VI). Read-only work on the repository. The only new files are this file and the calculation scripts with their outputs in `calc/` beside it. No pod, no spend, no download, no commit. No held-out file, `selector.jsonl` or `hidden/` file was opened. No row, prompt, answer or anchor text was read or printed: only counts, labels, hashes and record fields.

**Adversarial review and in-place revision: 2026-10-16, about 22:02–22:30 UTC (17 Oct IST; clock checked with `date -u` at 22:02, 22:16, 22:21 and 22:23 UTC), by a second Opus worker.** Same limits: read-only on the repository; no pod, spend, download, commit or agent; no held-out, `selector.jsonl` or `hidden/` file opened; no row, prompt, answer or anchor text read. The review re-checked the M and R claims against their sources, redid the arithmetic, and read the Gate B kit's pack and budget code and the two sibling designs in this folder. Its corrections are in the text, marked **[rev]**. §15 lists them. New files: `calc/review_calc.py` and `calc/review_calc_out.txt`.

**What this draft covers.** Re-plan §5 item 3 and §4: the 7–8B noise block (N), the analysis scale (S), the seed rule (SR), the high-noise branch (H), the transfer check (TC), the family choice for option C (F), and the rules that keep the frozen 1B Gate B valid (EM, T4). The rest of the 7–8B pre-registration (arms, scorers, references, limits, judges, confirmation, Alpaca) is **Part 2**. §11 lists it. Part 2 is frozen later, before 7–8B block A.

**Option marks.** The user has not chosen option B or C (RP §0, §7 item 1). **[B+C]** = shared by both. **[B]** = only under option B. **[C]** = only under option C. **[USER]** = a decision for the user. **[LEAD]** = a decision or task for the lead.

**Labels.** **M** = measured (the path follows). **R** = read (path:line, or a FOCUS entry line). **E** = estimate (the basis follows). **I** = inference.

**Short names.** RP = `writing/paper/2026-10-17-icml-replan-PROPOSAL.md` (SHA-256 `e8768298…`). PRE = the frozen Gate B/C pre-registration, revision 5, `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (`5c97cce7…`). PLAN-S = `research/review/2026-10-08-sharpened-direction-DRAFT.md` (`6ff3ff2b…`). F L*n* = line *n* of `research/FOCUS.md` at `23e3da8f…` (branch `stageb-costs-and-recovery-safeguards-20261003`; HEAD was 19c2d28 when the draft was written; **[rev]** at review time HEAD is 1a5189b, a paper commit, and FOCUS is unchanged, `23e3da8f…`, M: `shasum`). SIDE = `research/side-notes/2026-10-11-prereg-results.md` on the side branch `claude/wonderful-greider-d1aa5b` (`e92e9066…`). S1B = `.ai/briefs/stage1-commitments-build-20261016.md` (`12cbf463…`). S1L = its lead-decisions addendum (`11477648…`). NG = `tmp/gate-b-olmo/gate_b_noise_gate.json` (`4b817f73…`). SEAL = `.ai/inputs/gate-b-sealed-20261008/` (MANIFEST `d76d8bf9…`). SS = `experiments/safety_selection`. CALC = `calc/` in this folder: scripts and outputs, run with the repository's `.venv` Python (numpy, scipy). Power figures use the normal approximation of RP §2.2 unless they are marked "simulation". **[rev]** BUD = `runkit/gate-b-olmo/budget.py` (equal to the kit copy `tmp/gate-b-olmo/budget.py`, M: `diff`). PACK = `runkit/gate-b-olmo/pack_setup.py`. BLD = SEAL's `build_sealed.py` (`80cb8944…`). KCR = `78b-kit-cap-rule.md` and EYD = `engine-round-Y-design.md`, two sibling designs in this folder (not adopted; their figures are E or I).

---

## 0. Summary

1. **The reusable a0 units exist, and pairing with them is technically valid under stated conditions (§2).** OLMo-2-7B has main-recipe a0 seeds 1101–1103. Llama-3.1-8B has main-recipe a0 seeds 1101–1102. All five ran on engine X (`472fc7f6…`), A100-SXM4-80GB, with Gate A's lock (M). Their 13 compared environment fields equal those of the 1B Gate A units and of the 15–16 Oct Gate B units (M). OLMo-2-7B uses Gate B's own prepared manifest (`9ed61826…`), so Gate B's sealed R_d1–R_d3 files apply to it byte for byte (M). Llama's manifest (`c52a50af…`) has the same groups and members, so new Llama files by the same rule hold the same row lists (M).
2. **A scale mismatch decides most of the seed question (§4).** PLAN-S reads its seed rule on the paired scale (Gate B's σ̂) but analyses the contrasts unpaired (PLAN-S:102, :118). At 1B this did not matter. At 7–8B it does. On the unpaired scale, the data in hand already exclude plan A: even if every new term were zero, the pooled per-arm SD would be 3.20 pp, so 4.53 pp on the pair scale, above the 4.5 pp bar (I from M; CALC `rule_oc2_out.txt`). So the noise block can only "allow plan A" (RP §7 item 2) if the 7–8B analysis is seed-blocked (paired). **[USER] decision S.** **[rev]** Two limits: the margin is 0.03 pp (4.532 against 4.5; CALC `review_calc_out.txt`), and the exclusion holds only if the side-project a0 units are reused (RP decision 5). Plan A is excluded under the unpaired scale, but plan B9 is not: P(plan B9) is about 19–87%, by the new R arms' noise (§5.1).
3. **The noise block alone is a weak decider (§5).** Its σ̂ rests on 4 df (2 per family). If the true paired SD were 8.2 pp (no pairing gain), it would still read plan A 12% of the time (CALC `rule_oc2_out.txt`). A blinded re-check after block A has about 30 df under [B] (both families) and about 15 df under [C] (one family, seed-blocked), and is much sharper either way (**[rev]** the 15-df figures are new; §5.2). **[USER] decision SR-2.**
4. **The high-noise branch (§6).** At the re-plan's pooled σ = 5.83 pp (unpaired): plan A has a removal MDE of 11.0 pp, and "equivalent" at ±5 pp cannot occur (the 90% CI half-width is 5.18 pp). Option (a), SESOI 10 pp, adds no power; it makes "equivalent" reachable at a coarser margin. Option (b), P1, P3, P6 at 12 seeds, gives an MDE of 7.2 pp and keeps the 1B target; it costs about 26 more runs per family. Option (c) does both. Under a seed-blocked analysis, the MDE could fall to about 5.7 pp at 6 seeds, if the 1B pairing gain carries over; this is not shown. **[USER] decision H.**
5. **The transfer check (§7)** runs only if the frozen 1B reading says LOCALIZED. It removes the 1B-named unit(s) at seeds 1101–1103 on each 7–8B family that runs, against the noise block's R_1–R_3. It keeps Gate B's 8 pp floor, guards and t at 3 df. Simulation: false TRANSFERS at no effect ≤ 2.4%; a true 8 pp unit reads DOES NOT TRANSFER about 9% of the time; a true 10 pp unit reads TRANSFERS 44–80% of the time, by noise level (CALC `tc_sim_out.txt`).
6. **The family choice for option C (§8).** Choosing by the smaller σ̂ picks the truly less noisy family only 61% / 69% / 80% of the time at true SD ratios 1.25 / 1.5 / 2 (I; CALC `power_out.txt`). Recommended (I): fix the family now. This draft recommends OLMo-2-7B; the reasons and the case for Llama-3.1-8B are in §8. **[USER] decision F.**
7. **The frozen 1B Gate B stays valid (§9).** Every design here adds new files only. None of them is an engine file, a Gate B pinned script, a Gate B kit file or a sealed file. Gate B's sealed edit files are used read-only. Every paired 7–8B arm runs on engine X. 7–8B launches never use Gate B's reserved money. **[rev]** Four couplings that the draft missed. None changes a T4 file, but each needs a rule: (a) the frozen Gate B budget guard reads caps only from working copies named `family-probe-*` or `gate-b-olmo*` (BUD:39, :53-92), so the 7–8B kit's working copies must use that prefix (§9.2 item 4); (b) the frozen sealed builder refuses any manifest other than OLMo's (BLD:60-61, :143-144), so the Llama files need their own writer (§9.2 item 2); (c) a new config under `experiments/safety_selection/configs/` enters every later Gate B bundle (PACK:220-222), and block 0's A1 pass needs one before 9 Nov (§9.2 item 8); (d) the engine round Y design puts B+Qi in engine Y and uses it in 7–8B block B (EYD:30-31, :78), which conflicts with "every paired 7–8B arm runs on engine X" unless the X → Y certificate passes first (§9.1 EM-1).
8. **[rev] Money at launch.** N spends about $26–32, but its two pods pass the guard only if the account holds about $129 or more, because Gate B's $83.91 hold and both pods' full caps are counted (E: KCR:177). That is about $37 above the 16 Oct balance, before idle storage.

---

## 1. What B and C share, and what differs

| Item | [B+C] shared | [B] only | [C] only |
|---|---|---|---|
| N: noise block | R_1–R_3 on both 7–8B families; Llama-8B a0 seed 1103 | — | — (both families still run N; it feeds the 20 Nov gate and rule F) |
| S: analysis scale | one choice for every 7–8B family | — | — |
| SR: seed rule | one rule; one plan from the σ̂ pooled over both families | the plan applies to both families | the plan applies to the chosen family (**[rev]** or reads that family's own σ̂_F, a [USER] choice; §3.3) |
| H: high-noise branch | one choice, fixed before N | applies to both families | applies to the chosen family |
| TC: transfer check | the rule; run only after a 1B LOCALIZED | on both families | on the chosen family |
| F: family rule | fixed before N and before Gate B wave-1 outcomes are read (B can fall back to C on 20 Nov) | not used unless B falls back to C | selects the family |
| EM, T4 | all of §9 | — | — |

---

## 2. The existing 7–8B units, and whether pairing with them is valid [B+C]

### 2.1 The units (M: each unit's `COMPLETE.json` and `assets.json`; CALC `env_and_manifest_check_out.txt`)

| Family, unit | Seed | U (of 600) | E (pp) | Engine | Recipe (config) | Manifest | `COMPLETE.json` SHA-256 |
|---|---|---|---|---|---|---|---|
| OLMo-2-7B untuned | – | 11 (1.83%) | – | `472fc7f6` | `18cc31d7` | `9ed61826` | `632fa4bd0a8f3b1b…` |
| OLMo-2-7B a0 | 1101 | 309 (51.50%) | +49.67 | `472fc7f6` | `18cc31d7` | `9ed61826` | `4a6d9ebc6636de57…` |
| OLMo-2-7B a0 | 1102 | 234 (39.00%) | +37.17 | `472fc7f6` | `18cc31d7` | `9ed61826` | `43e8412dc7ef8d3e…` |
| OLMo-2-7B a0 | 1103 | 284 (47.33%) | +45.50 | `472fc7f6` | `18cc31d7` | `9ed61826` | `4b5bd06dede08dc1…` |
| Llama-3.1-8B untuned | – | 32 (5.33%) | – | `472fc7f6` | `c5462c77` (LR 1e-4 kit's init unit) | `c52a50af` | `651f7f6de6721b41…` |
| Llama-3.1-8B a0 | 1101 | 347 (57.83%) | +52.50 | `472fc7f6` | `74758af1` | `c52a50af` | `21427715565fb394…` |
| Llama-3.1-8B a0 | 1102 | 356 (59.33%) | +54.00 | `472fc7f6` | `74758af1` | `c52a50af` | `b0c99f7b97e6e763…` |

- Paths (M): `tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-{init,e1}-a1`; `tmp/family-probe-sp-olmo2-7b-b-seed1102/…/1102-a0-e1-a1`; `tmp/family-probe-sp-olmo2-7b-b-seed1103/…/1103-a0-e1-a1`; `tmp/family-probe-sp-llama31-8b-b-a0/…/1101-a0-init-a1`; `tmp/family-probe-sp-llama31-8b-b5e5-1101/…/1101-a0-e1-a1`; `tmp/family-probe-sp-llama31-8b-b5e5-seed1102/…/1102-a0-e1-a1`.
- Configs (M: the engine's `config_sha256`, run with `-I -B`, no file written): `18cc31d7…` = `SS/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json` (recipe B, LR 1e-4, micro-batch 2 × accumulation 64); `74758af1…` = `SS/configs/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json` (recipe B, LR 5e-5, the same batch). So 4,800 rows give 38 steps and 4,200 rows give 33 steps, as at 1B (I).
- These are the per-family main-recipe rungs: OLMo-2-7B at 1e-4 (F L105) and Llama-3.1-8B at 5e-5, the user's decision of 11 Oct 03:53 UTC, "at the edge" (F L102). Seed 1103 of OLMo-2-7B came from the side project's replication pre-registration (F L104). HarmBench E_HB for seeds 1101–1102: OLMo +37.0, +27.7; Llama +36.2, +37.8 (R: F L98).
- **Engine X: confirmed (M).** All seven records name code identity `472fc7f6d619bdee…`, the engine X of Gate B (R: F L114). The side notes and FOCUS say the same (R: F L102, L112).
- **Adapters on the Mac (M).** The e1 adapters of OLMo-2-7B a0 1101–1103 are in `tmp/sp-repr/out/` (`sp-olmo2-7b-b2-1101`, `sp-olmo2-7b-1102`, `sp-olmo2-7b-1103`); their SHA-256 equal the records' (`bb133508…`, `ac69a6ba…`, `76c41cd6…`). No Llama-3.1-8B adapter at LR 5e-5 is on the Mac: the local `sp-llama31-8b-110x` adapters are the LR 1e-4 units (`31e89379…` equals the LR 1e-4 record, not the 5e-5 one, `9b3046ee…`). This matches F L94 ("the Llama-3.1-8B rung adapters" were lost).

### 2.2 Units that are not used for pairing (M, I)

- OLMo-2-7B at LR 5e-5 (`8df9f02f`), OLMo-2-7B recipe G (`01259f28`), Llama-3.1-8B at LR 1e-4 (`c5462c77`) and its recipe G (`442f133f`): other training identities. They cannot be a0. OLMo-2-7B's recipe-G units 1101–1103 are at OLMo's main LR, so they can serve as the 7–8B recipe-G reference (RP decision 5). Llama's recipe-G units are at LR 1e-4, not Llama's main 5e-5 (M: `SS/configs/study-kt-llama31-8b-r64-g-mb2-20261011.json`, `lr` 1e-4). So a Llama-8B recipe-G reference needs 3 new runs (I).
- The causal side-study units at seeds 1121–1122 (engine X; R: F L87–L88): another protocol and another seed range. Not used. The 7–8B main-study seeds stay at 1101–1116, so they never meet 1121–1122 (I).
- Qwen units: the main study excludes Qwen (R: F L100).

### 2.3 Pairing validity

**What a same-seed pair shares (R: PRE:86).** The adapter initialization, the relative order of the kept rows, and the sampling seed of each (prompt, sample). Training is deterministic on a matching machine (R: PRE:108).

**Conditions met now (M).**
1. Same engine: X, for every 7–8B a0 unit.
2. Same training identity per family: `36738c38` (OLMo-2-7B), `5b4451e1` (Llama-3.1-8B). Precedent: at 1B, Gate B's R arms ran under recipe S (`ceffe0ef`) and paired with Gate A's a0 under recipe B (`9e9bde6f`), because both have training identity `f46279e5` (M: CALC `env_and_manifest_check_out.txt`).
3. Same manifest per family; the edit files bind to it (R: `SS/edits.py:117` refuses another prepared dataset).
4. Same compared environment: the 13 fields of `scripts/family_probe_reading.py` `environment_of` (:167–182) are identical for all seven 7–8B units, for the three 1B Gate A a0 units and for the five Gate B units of 15–16 Oct (M; this draft's check hashes the canonical JSON of those fields: `8e393dca87ab…` for all). The lock is `7e0dd998…` everywhere (M). The guard is Qwen3Guard-Gen-4B at `6ec42827…` everywhere (M).

**Conditions that the new arms must meet (I; rule EM-1, §9).** The new R arms run on engine X, with the family's config above, on the family's manifest, on a pod whose compared fields and guard record equal the family's a0-1101 unit. This is Gate B's environment rule (R: PRE:107) with the 7–8B a0-1101 unit as the reference.

**One more check, as Gate B did (I).** Gate B retrained a0-1101 and compared adapter fingerprints (R: PRE:106; F L77: equal). At 7–8B the engine is the same, so this checks the pod, not the engine. The A1 scorer at 7–8B needs a fresh a0-1101 retrain anyway, for its q and e1 states (PLAN-S:143; the side units' states are not on the Mac). So: when that retrain runs (block 0), its q and e1 adapter fingerprints must equal the side units' (OLMo-2-7B 1101: q `3c7344c178b47e5b…`, e1 `9d5d5d8b2eb40262…`; Llama-3.1-8B 1101: q `ac05caca1bdfac5b…`, e1 `ee44580dfa016b67…`; M). If they differ, the noise reading is re-read with the a0-free fallback (§3.3), as PRE:153 does.

**Verdict (I).** Pairing the new R_1–R_3 with these a0 seeds is valid under conditions 1–4 and rule EM-1. The fingerprint check confirms it later. **Whether to reuse the side-project units as main-study a0 is RP decision 5, the user's.** This section gives the technical evidence for it.

---

## 3. N: the 7–8B noise block [B+C]

### 3.1 Runs

| Family | Arm | Seed | Edit file | Config | Runs |
|---|---|---|---|---|---|
| OLMo-2-7B | R_1, R_2, R_3 | 1101, 1102, 1103 (draw d at seed 1100 + d; R: PRE:79; S1B:121 (d)) | SEAL `out/edits/R_d1.json` `f7d7eb86…`, `R_d2.json` `913b7360…`, `R_d3.json` `cd8d3328…`, byte for byte (M: same manifest) | `18cc31d7` | 3 |
| Llama-3.1-8B | R_1, R_2, R_3 | 1101, 1102, 1103 | new Llama files, same rule, on `c52a50af` (§9, new file 2); their remove lists must equal SEAL's R_d1–R_d3 lists (M: the two manifests have equal `groups`, members and per-unit row lists) | `74758af1` | 3 |
| Llama-3.1-8B | a0 | 1103 | none (fine-tune only on the sealed untuned unit, as seeds 1101–1102 were; R: F L106) | `74758af1` | 1 |

- Every arm evaluates at e1 only, as at 1B (R: PRE:85). R arms train 33 steps; a0 trains 38.
- The R arms run under the family's main config, not a recipe-S sibling. Training identity is the same either way (R: PRE:99), and N then needs no 7–8B anchor job (I). **[LEAD]** **[rev]** The kit route decides whether this is free. The Gate B job runner passes recipe S to every arm (R: `runkit/gate-b-olmo/setup/job_runner_gateb.py`:11), and the pinned recipe maker is fixed to the 1B recipe (R: KCR:140). So a fork of the Gate B kit needs a job-runner change in the fork (a new file, no T4 contact), or another kit route (KCR KD8, KD10). For Llama a0-1103 alone, the family-probe kit already runs this job kind (KCR:142).
- **Llama-3.1-8B seed 1103 rule (proposed; [USER] confirms, because it binds the user's rung decision).** The seed is an a0 unit for N and for the comparison. It is read by the frozen family-probe bars and reported with the 3-seed Gate A mean. Its outcome never changes Llama's rung (F L102). Reason: a rung change after an outcome would be a choice after an outcome (I).

- **T4 for N.** New files: 2 (the Llama sealed set), 4 (the 7–8B kit) and 5 (the noise reading) of §9.2. Read-only uses: SEAL's `R_d1–R_d3` and the side units' records. N touches no file of §9.3.

### 3.2 Pods, time and money (E: measured job times RP §2.1, PODS)

- OLMo-2-7B: one pod, 3 jobs; 86–108 min per job plus 20–38 min setup = 4.6–6.0 h, **$8.3–10.8** at $1.79/h.
- Llama-3.1-8B: 4 jobs at 105–124 min plus setup = 7.3–8.9 h, **$13.1–15.9**. Two pods of 2 jobs each halve the wall time and the loss from one pre-job stop, for one more setup (about $0.6–1.1). **[LEAD]**
- Total **about $21–27; $26–32 with the 20% allowance** (RP §2.1 basis). The re-plan's "$30–40" (RP:67) is the same order.
- Caps: from the measured job upper times, not the 7B projection, which ran about 7× too high (R: RP:113). That is prep item 1.
- **This money is not extra if the 7–8B comparison runs:** R_1–R_3 are the first 3 of the 8 R seeds that P1 needs (PLAN-S:140), and Llama a0-1103 is one of its 6 a0 seeds (I).
- **[rev] Money in the account at launch (E: KCR:177).** The guard counts every running pod at its full remaining cap and the new pod at cap × $1.85, and keeps $6 (BUD:4-7). With Gate B's $83.91 hold (EM-2) and both N pods in parallel (caps 8.5 h and 12.5 h in KCR), the second launch needs about $128.76 in the account; KCR's block-0 funding need with the hold is about $139.97. Spend stays about $26–32. Pods run one after the other need less at each launch ($6 + $83.91 + one cap × $1.85: about $105.64 for the OLMo pod and $113.04 for the Llama pod at KCR's caps; I), but the wall time rises from about 7.3–8.9 h to about 11.9–14.9 h.
- **[rev] Costs that N's figure leaves out (E).** Idle storage of stopped 7–8B pods until their verified backup and the user's yes to delete them (PRE:322): about $0.33 per day for a stopped 50 GB pod (KCR:161). Judge pods for the R arms (HarmBench report-only; Granite for TC): about $0.9–1.9 per HarmBench launch (PRE:315). The block-0 a0-1101 retrains and A1 passes (Part 2; RP:43).

### 3.3 The reading (a new pinned script; §9, new file 5)

For each family F and seed j ∈ {1101, 1102, 1103}: r_F,j = U(a0, j) − U(R_j, j), in pp.

- **σ̂_F** = max(SD(r_F,j), σ_eval,0,F), 2 df. This is Gate B's σ̂_gate formula (R: PRE:126–127). σ_eval,0,F is the median, over the family's 3 pairs, of the prompt-clustered SE of the pair's per-prompt difference.
- **σ̂_pool** = max(√[(2·SD(r_O)² + 2·SD(r_L)²)/4], median of the 6 pair SEs), 4 df. The seed rule (§5) reads σ̂_pool [B+C]. Reason: one plan for all families avoids a 2-df decision per family; under option C it also avoids the winner's curse of rule F3 (§8) (I). **[rev] Assumption to state:** pooling assumes equal paired noise in the two families. The a0 point estimates differ about 6× (per-arm SD 6.36 against 1.06 pp; not significant, p ≈ 0.12; CALC `fratio_out.txt`). Under [C] with a family fixed now (F1 or F2) there is no winner's curse, so pooling only buys df: with F1 it lets Llama's small spread lower OLMo-2-7B's plan. The remedy is SR-2, which re-reads the plan from the chosen family's own block-A units (§5.3). Without SR-2, the [C] alternative is σ̂_F of the chosen family (2 df). **[USER]** (§12 item 10).
- **s_arm** (for the unpaired scale only): the pooled per-arm seed SD of U over the main-recipe a0 and R units of both families (8 df once Llama a0-1103 exists).
- **Fallback (Gate B's σ̂ fallback; R: PRE:129).** If a new R arm's environment differs from its family's a0 units, or if the block-0 fingerprint check fails (§2.3), each r term is replaced by √2 × SD(U(R_1101), U(R_1102), U(R_1103)), and σ_eval,0 uses the three R-arm pairs. The reading is then a0-free. With the fingerprint trigger, the seed rule is re-read and the plan follows the re-read.
- The script prints σ̂_F, σ̂_pool, s_arm, both σ_eval,0 forms, the triggers and the seed-rule output. It never reads a method arm.

### 3.4 Report-only results (they gate nothing)

- Mean r_F (the random-removal effect at 7–8B), with its SE.
- The per-arm seed SD of the R arms beside the a0 SD. At 1B it was 1.35 against 2.65 pp (M: NG and F L82; CALC `power_out.txt`).
- σ_eval,0 for seed-matched pairs against R-arm pairs. At 1B it was 1.28 against 2.16 pp (M: NG). That gap is the clearest 1B sign of a same-seed pairing gain.
- Each R arm's G1 status by the frozen Gate B guard code (R: PRE:147). N does not stop on a G1 failure. But an R arm that fails G1 blocks the transfer check on its family (§7).

### 3.5 Predictions, written before N runs **[LEAD]** (they gate nothing)

- **N1, mean r.** A linear row dose predicts E/8: 5.5 pp (OLMo-2-7B) and 6.7 pp (Llama-3.1-8B). Saturation predicts about 0. At 1B the read was 2.5 pp (SE 1.06) against 5.6 predicted (R: NG). Proposed point: 1–4 pp on both families (I). The lead writes the final number.
- **N2, σ̂_pool.** If the 1B pairing ratio holds (SD(r)/(√2 × per-arm SD) = 1.83/3.75 = 0.49; I from M), then σ̂_pool ≈ 0.49 × √2 × 5.83 ≈ 4.0 pp. If there is no pairing gain, about 8.2 pp (I).

---

## 4. S: the analysis scale [USER, fixed before N launches; **[rev]** the 1B part before Gate B wave 1]

**The issue (R, I).** PLAN-S analyses stage-1 contrasts unpaired: "Variance pooled over all stage-1 arms … Seeds are not paired (correlation −0.08)" (PLAN-S:102). Its seed rule reads "Gate B's final pooled σ̂ only (a nuisance value, on the σ_pair scale)" (PLAN-S:118; F L242). Gate B's σ̂ is paired (PRE:116, :126–128). So the 1B rule reads one scale and analyses on another. The −0.08 came from per-prompt sampling correlations of pairs that differ in seed or are untuned against tuned (PRE:121). It did not test same-seed tuned arms. Gate B's wave 0a did: σ_eval,0 1.28 pp seed-matched against 2.16 pp for R-arm pairs (M: NG, `plain` and `fallback` blocks), and SD(r) 1.83 pp (M: NG) against an unpaired 2.97 pp (**[rev]** I: CALC `power_out.txt`, from the a0 and R per-arm SDs 2.65 and 1.35; NG does not hold 2.97). Both point to a gain. Gate B's own noise model already treats seeds as blocks: "s_j cancels in every c" (R: PRE:117). The SD(r) part rests on 2 df (90% CI 1.06–8.09 pp; CALC `power_out.txt`).

**A $0 check that was done (I from M; CALC `crossrecipe_out.txt`).** Same-seed pairs across recipes (shared init, order and sampling seeds, but a different recipe) show no consistent gain: SD ratio paired/unpaired 1.37 (OLMo-1B B vs G), 0.79 (OLMo-7B 1e-4 vs 5e-5), 1.26 (OLMo-7B B vs G), 0.91 (Llama-8B B vs G), 0.53 (Llama-1B B vs G). The 1B a0-against-R ratio is 0.62. So cross-recipe pairs do not predict the a0-against-R gain. Only N measures it at 7–8B.

**[rev] A third reading, not offered.** PLAN-S as literally written (S-U-lit) reads the seed rule on the paired σ̂ and analyses unpaired. At 7–8B it could pick plan A (σ̂_pool ≤ 4.5) while the unpaired removal MDE stays about 11 pp at σ = 5.83 (RP:63). So it can promise a power that the analysis does not have. The draft's S-U fixes this by reading √2 × s_arm (I). If the user prefers PLAN-S's words exactly, S-U-lit is the option, with that defect stated.

**Options.**

| | **S-U: unpaired (PLAN-S as written)** | **S-P: seed-blocked (paired)** |
|---|---|---|
| Primary estimator | difference of arm means; variance pooled over arms; Welch as a check (PLAN-S:102) | two-way additive model, arm + seed (seeds are blocks); residual df stated; the unpaired estimate as a pre-registered sensitivity |
| What the seed rule reads | s_arm (§3.3), shown on the pair scale as √2 × s_arm | σ̂_pool (§3.3) |
| Plan A at 7–8B | **already excluded by data in hand**: the main-recipe a0 SD is 5.23 pp on 3 df; even with every new term zero, √2 × 3.20 = 4.53 > 4.5 (I from M). **[rev]** Margin 0.03 pp; needs the reuse of the side units (RP decision 5); plan B9 stays reachable (§5.1) | decided by N: plan A if σ̂_pool ≤ 4.5 |
| MDE of a removal contrast, 6 seeds | 11.0 pp at σ = 5.83 (RP:63) | 1.42 × σ_pair: 5.7 pp at σ_pair 4.0; 11.7 pp at 8.2 (no gain) (I; CALC `power_out.txt`) |
| Cost if there is no pairing gain | — | SE 3.37 against 3.15 pp (about 7% worse): the paired form uses the 6 shared seeds, not R's 8 (I) |
| Validity needs | nothing new | every arm of a family on engine X with matching environment (EM-1); no gain is needed for validity (I) |
| Consistency with 1B | as 1B | needs the same choice at 1B in REQ-21 before Gate B wave 1 (S1B:121 (b), (d)), with the blinding line naming σ̂_gate 1.83, σ_eval,0 1.28 and r_j as seen (**[rev]** S1B:121 (m), not S1B:63, which is the selector-settings rule T2; F L82); otherwise a 7–8B-only estimator, disclosed |

- **T4 for S.** No file. The choice goes into Part 2's reading and, at 1B, into the lead's REQ-21 text; neither is a §9.3 file.
- **Seed layout under S-P [LEAD].** PLAN-S runs R at 1101–1108 and methods at 1102–1107 (PLAN-S:116). Under S-P, R_8 at 1108 has no partner; keep it for the S-U sensitivity. Add a0 at 1107 (one run per family), so P4 (S1 − a0) has 6 shared seeds, not 5.
- **Recommendation (I): S-P at both sizes, decided before Gate B wave 1, with S-U as the sensitivity.** Reasons: Gate B itself is paired; the engine shares init, order and sampling seeds by design; the 1B evidence points to a gain; the cost of no gain is small; and only S-P can bring 7–8B near the 5 pp target at 6 seeds. Against it: it changes an approved line of PLAN-S (PLAN-S:102), so it is the user's call; and its benefit at 7–8B is unproven until N. **[rev]** Two more points against it. (1) At 1B the choice is made after the wave-0a nuisance values were seen, and they favour S-P. No repair outcome exists yet, so this is not a choice after an outcome, but the REQ-21 blinding line must say it (I). (2) REQ-21 (b) lists PLAN-S:114-119, not the estimator line PLAN-S:102 (R: S1B:121), so S-P at 1B needs an added line in REQ-21, not only a changed one.

---

## 5. SR: the seed rule [B+C; the rule is fixed before N launches]

### 5.1 The rule

σ̂ is the statistic of the chosen scale, on the pair scale: S-P uses σ̂_pool; S-U uses √2 × s_arm. The thresholds are PLAN-S's (PLAN-S:118; F L242). Both thresholds equal a removal MDE of about 6.0 pp under PLAN-S's own formula: 5.98 pp for plan A at 4.5, and 6.05 pp for plan B at 6.0 (I; CALC `power_out.txt`). So the 7–8B rule keeps the 1B target, not only the 1B numbers. **[rev] This holds under S-U only.** PLAN-S's formula is the unpaired one (σ_arm = σ_pair/√2; PLAN-S:117). Under S-P the same thresholds give paired MDEs of 6.39 pp (plan A) and 6.47 pp (plan B9) (I; CALC `rule_oc2_out.txt`), because the paired contrast uses the 6 (or 9) shared seeds, not R's extra seeds. Thresholds with a paired MDE of 6.0 would be 4.22 and 5.56 pp (CALC `power_out.txt`). Recommended (I): keep 4.5 and 6.0 (PLAN-S's numbers, at both sizes), and state that under S-P they mean an MDE of about 6.4–6.5 pp. **[USER]** may choose the rescaled values instead (§12 item 11).

| σ̂ (pair scale) | Plan | Primary family | Seeds | SESOI |
|---|---|---|---|---|
| ≤ 4.5 | **plan A** (as 1B) | P1–P6 | methods 6 (1102–1107); R 8 (1101–1108); a0 6 (1101–1106); S1 6 | 5 pp |
| 4.5 < σ̂ ≤ 6.0 | **plan B9** (PLAN-S's plan B) | P1, P3, P6 | A1, H1, S4, S1 9 (1102–1110); R 12 (1101–1112); a0 6 | 5 pp |
| > 6.0 | **branch H**, the user's choice fixed before N (§6) | per H | per H | per H |
| H's removal MDE > 2 × its SESOI | **review**: no 7–8B primary family; the user decides | — | — | — |

- PLAN-S's ">6.0: no stage 1; review" (PLAN-S:118) becomes "branch H" at 7–8B. That follows RP decision 3 (RP:146). The "review" ceiling (MDE above 2 × SESOI) is a new constant proposed here **[LEAD; the user may change it]**. On the pair scale it binds only at σ̂ above about 10.7–21 pp (S-P) or 11.4–23 pp (S-U), by option (I; CALC `rule_oc2_out.txt`). So it is a safety valve.
- Under S-U, plan A is already excluded (§4). Plan B9 needs the 5 new df to have an SD ≤ 3.52 pp. **[rev] The draft called this unlikely; that is not supported.** At 1B the R arms' per-arm SD was about half the a0's (1.35 against 2.65 pp; M: NG). P(plan B9) is about 87% / 77% / 43% / 19% if the new terms' true SD is 2.7 / 3.0 / 4.0 / 5.23 pp (I; χ² on 5 df; CALC `review_calc_out.txt`). So under S-U the plan is B9 or H, and which one depends mainly on the new R arms' noise. N also gives R_1–R_3, which P1 needs anyway.
- **[rev] [C] with a family-only S-U value.** If the user chooses σ̂_F of the chosen family under [C] (§3.3), OLMo-2-7B's S-U value after N is at least 6.36 pp on the pair scale (its a0 SS alone, over 4 df), so branch H is certain; Llama-3.1-8B's could be as low as 0.75 pp (I; CALC `review_calc_out.txt`).
- **Interface to the 20 Nov gate (RP decision 2).** "The 7–8B noise reading allows plan A" means: this rule's output on σ̂ is plan A. Under S-U this is false by the data in hand. **[USER]** may restate decision 2 as: "B if the account covers B at the plan this rule gives, H included; else C". The B/C choice reads money and N only, never a transfer-check result or a 1B Gate B outcome (I).

- **T4 for SR and H.** New files: 3 (OLMo R_d9–R_d16, only for plan B9 or 12 seeds) and 7 (SR-2's script, if adopted) of §9.2; Llama's R_d4–R_d16 are in file 2. H adds no file. Neither touches a §9.3 file.

### 5.2 Operating characteristics (I; CALC `rule_oc2_out.txt`; χ² on the stated df; the σ_eval floor is ignored)

| True σ_pair | P(plan A), 4 df (N) | P(plan B9), 4 df | P(H), 4 df | P(plan A), 30 df (block-A re-check) | P(H), 30 df |
|---|---|---|---|---|---|
| 3.0 | 94% | 6% | 0% | 100% | 0% |
| 4.0 | 72% | 22% | 6% | 85% | 0% |
| 4.5 | 59% | 28% | 13% | 53% | 1% |
| 5.0 | 48% | 30% | 22% | 24% | 6% |
| 6.0 | 31% | 28% | 41% | 3% | 47% |
| 8.24 (no gain) | 12% | 17% | 71% | 0% | 98% |

**[rev]** The 30-df columns are [B] under S-P (15 df per family). Under [C] (one family) the re-check has about 15 df (S-P) or 19 df (S-U). At 15 df: P(plan A) 100 / 79 / 55 / 33 / 10 / 0% and P(H) 0 / 0 / 3 / 12 / 45 / 93% at a true σ_pair of 3.0 / 4.0 / 4.5 / 5.0 / 6.0 / 8.24 (I; CALC `review_calc_out.txt`, which also gives 19 and 38 df). So SR-2 is still much sharper than N's 4 df under [C].

### 5.3 SR-2: a blinded re-check after block A [USER: yes or no; recommended yes]

- **Block A is the same for every plan** (as PLAN-S:222): the 6 method arms at 1102–1104; R_4 at 1104 and R_5 at 1105; a0 at 1104 (one per family). That is 21 runs per family. Under H, the block-A runs of L1 and S3 (6 runs) are kept as secondary data for P2 and P5 (I).
- After block A, a new pinned script computes σ̂_A on the chosen scale from every block-A unit of the families that ran (S-P: √2 × the residual SD of the arm + seed model; S-U: √2 × the pooled within-arm SD). It prints σ̂_A and its df only (about 15 df per family under S-P, 19 under S-U; I).
- Block B's design is the rule of §5.1 applied to σ̂_A. It replaces N's value. Both directions are allowed.
- **Blinding risk [LEAD].** The kit's records show U per unit. The lead must not open block-A U values before σ̂_A is read, and the record-done step should not print them. If that cannot be ensured, do not adopt SR-2; then N's value decides alone.
- **Money.** The 20 Nov gate must budget the worst plan that SR-2 can reach (I). **[rev]** With H (b) as the worst plan, that is about $190–240 more than plan A over both families under [B], arms only (§5.4 rows: $512–646 against $322–406 with the allowance; E).
- **[rev] Why SR-2 does not leak outcomes.** σ̂_A is computed after the arm means (S-P: arm and seed effects; S-U: arm means) are removed, so it does not move with any repair's mean effect. It does move with an arm × seed interaction, which is noise for this purpose. It is a variance-only interim re-estimate; such a step is expected to raise the error rate only a little (I; this review did not simulate it or check a source, so a Part 2 simulation should confirm it). The printed output must stay σ̂_A and df only.

### 5.4 Runs and money per family (E: RP §2.1 per-arm cost, OLMo $2.8–3.6, Llama $3.3–4.1, ×1.2 allowance; CALC `power2_out.txt`)

New runs beyond N, the primary family only. References, scorers, recipe G, B+Qi, Safe LoRA, judges and storage are not included.

| Plan | Block A | Block B | Total | OLMo-2-7B (×1.2) | Llama-3.1-8B (×1.2) |
|---|---|---|---|---|---|
| plan A, or H (a) | 21 | 18 methods + R_6–R_8 + a0 1105–1106 = 23 | 44 | $148–190 | $174–216 |
| plan B9 | 21 | 4 arms × 6 + R_6–R_12 + 2 a0 = 33 | 54 | $181–233 | $214–266 |
| H (b) or (c): 12 seeds | 21 | 4 arms × 9 + R_6–R_16 + 2 a0 = 49 | 70 | $235–302 | $277–344 |

- Over plan A: B9 adds about $33–43 (OLMo) or $40–50 (Llama); 12 seeds add about $87–112 or $103–128 (E). Under [B] count both families; under [C] one.
- The re-plan's F2 amounts (B $900–1,300; C $550–800; RP:104) assume plan A (I). If H can fire, the 20 Nov gate needs that extra.
- Seeds 1101–1116 are in the development namespace, 1101–2099 (M: both manifests' `seed_namespaces`).

---

## 6. H: the high-noise branch [USER, fixed before N launches]

**Basis (RP:47–65; I; CALC `power_out.txt`, `power2_out.txt`).** σ = 5.83 pp per arm (the six 7–8B cells pooled, 11 df; this draft reproduced it from SIDE's per-seed E). Holm's first step: α/6 two-sided for 6 contrasts (z 2.638), α/3 for 3 (z 2.394); 80% power (z 0.842). Labels as PLAN-S:115: *better* = the Holm-adjusted test rejects **and** the point estimate ≥ SESOI; *equivalent* = the 90% CI lies inside ±SESOI (TOST). Note: because *better* also needs the point estimate ≥ SESOI, P(better) is at most 50% when the true effect equals the SESOI.

| Design (removal contrast; add contrasts are about 7% wider) | SE | MDE (80%) | 80% point for *better* | P(*better*) at a true 8 / 10 / 12 pp | P(*equivalent*) at a true 0 / 5 pp | Runs per family (§5.4) |
|---|---|---|---|---|---|---|
| plan A, SESOI 5 (no branch) | 3.15 | 11.0 | 11.0 | 0.46 / 0.70 / 0.88 | **0.00** / 0.00 (CI half-width 5.18 > 5) | 44 |
| **(a)** plan A, SESOI 10 | 3.15 | 11.0 | 12.7 | 0.26 / 0.50 / 0.74 | 0.87 / **0.48** | 44 |
| plan B9, SESOI 5 (for reference) | 2.57 | 8.3 | 8.3 | 0.76 / 0.93 / 0.99 | 0.24 / 0.04 | 54 |
| **(b)** P1, P3, P6 at 12 seeds, R 16, SESOI 5 | 2.23 | 7.2 | 7.2 | 0.88 / 0.98 / 1.00 | 0.45 / 0.05 | 70 |
| **(c)** = (b) with SESOI 10 | 2.23 | 7.2 | 11.9 | 0.18 / 0.50 / 0.82 | 1.00 / 0.73 | 70 |

**The paired-contrast caveat (I).** These rows use the unpaired per-arm SD, as RP:65 says. Under S-P the MDE is a multiple of σ_pair: 1.42 (plan A), 1.08 (B9), 0.93 (12 seeds). At σ_pair 4.0 (the 1B ratio applied), plan A at SESOI 5 has an MDE of 5.7 pp and P(*equivalent* | 0) = 0.84; no branch is then needed. At σ_pair 8.2 (no gain), plan A's MDE is 11.7 pp, and the branch is needed. N decides which case holds, with the limits of §5.2.

**What each option changes.**
- **(a) SESOI 10 pp at 7–8B (1B keeps 5 pp).** It adds no power to find a difference. It makes *equivalent* reachable at a margin of 23% of E for OLMo-2-7B and 19% for Llama-3.1-8B, against 11% at 1B (I). A true 5 pp effect, the 1B SESOI, reads *equivalent* 48% of the time. So "equivalent at 7–8B" would not exclude an effect of the 1B size. It changes a scientific target at 7–8B. Cost: none beyond plan A. The 5 pp reading is reported as a sensitivity.
- **(b) 12 seeds on P1, P3, P6.** It keeps the 1B target and cuts the gap between the MDE and the SESOI from 6.0 to 2.2 pp. Nulls still read *inconclusive* more often than *equivalent* (P 0.45 at a true 0). P2, P4 and P5 become secondary, at the 3 seeds of block A, reported with one-sided bounds as PLAN-S §5.3 does. Cost: about 26 more runs per family than plan A.
- **(c) both.** *Equivalent* becomes nearly certain at a true 0, and an effect must be ≥ 10 pp to read *better*. It changes the target and costs as (b).
- **(d) review.** No 7–8B primary family. The 7–8B units that ran are reported descriptively (option A's reduced benchmark). The user decides the next step.
- **(e) a money-contingent choice.** For example: "(b) if the 20 Nov account covers its extra cost, else (a)". A funding event is not an outcome (PLAN-S:232), so this choice is allowed, if it is written before N (I).

**[rev] Against D5 = (a).** D5 keeps P1–P6 primary with "SESOI 5 pp" (R: F L78). Options (a) and (c) change that SESOI at 7–8B, so they need the user's explicit word (RP decision 3 says so too). Option (b) cuts the 7–8B family to P1, P3, P6, as PLAN-S's own plan B does at 1B (R: PLAN-S:118; F L242), so it keeps D5's structure. Option (d) leaves 7–8B with no primary family, which is option A's "reduced benchmark" again (RP:75).

**Recommendation (I).** First decide S (§4); under S-P the branch may not be needed. For H: (e) with (b) first, because (b) keeps the 1B scientific target and (a) changes it. If money is the binding limit, (a) is the cheap option, but the paper must say that 7–8B equivalence uses a 10 pp margin.

---

## 7. TC: the transfer check (Gate B-lite) [B: both families; C: the chosen family]

**When.** Only if the frozen 1B reading (`scripts/gate_b_reading.py`, verdict phase, after the extension if it ran) says LOCALIZED. If it says DIFFUSE or TOO CLOSE, TC does not run, and the paper says that localization was tested at 1B only (RP:91).

**Units.** The units that the 1B reading names LOCALIZED. If there are more than 2, the 2 with the largest Λ_u in the reading that gave the verdict; ties go to the lower group id, as PRE:133. k = the number of units (1 or 2).

**Arms (I).** Remove u at seeds 1101, 1102, 1103 on each family that runs TC: 3k runs per family. OLMo-2-7B uses SEAL's `out/edits/unit_g-<id>.json` byte for byte (same manifest; M). Llama-3.1-8B uses the new Llama unit file (§9, new file 2), whose remove list equals SEAL's (M: equal members). The reference arms are N's R_1–R_3. Seed 1101 is allowed: the unit was chosen from 1B outcomes, not from a 7–8B a0-1101 scorer (PLAN-S:116).

**Contrast and noise (the Gate B forms; R: PRE:116, :128, :157).**
- c_u,j = U(R_j, j) − U(u, j); Λ_u,78 = the mean of c_u,j over the 3 seeds.
- σ̂_T = max(√P_T, σ_eval,T), with P_T = [2·SD(r)² + 2·Σ_u s_u²]/(2 + 2k). Here s_u² is the variance of u's three c_u,j, SD(r) is the family's N value, and σ_eval,T is the median pair SE over all r and c pairs of that family. SE_T = σ̂_T/√3.
- t at 3 df, as Gate B chose (PRE:119, :131). Bonferroni over k: 2.353 (k = 1), 3.182 (k = 2). k_0.90 = 1.638.

**Labels, per unit and family.**

| Label | Rule |
|---|---|
| **TRANSFERS** | Λ_u,78 ≥ 8 pp and Λ_u,78 ≥ t × SE_T; G2–G4 and the direction checks (Λ_hard > 0, Λ_refusal > 0, Λ_Granite > 0) pass as at 1B (PRE:146–151); every arm used (u and R at 1101–1103) passes G1 |
| **DOES NOT TRANSFER** | Λ_u,78 + 1.638 × SE_T < 8 pp, also under G2 and in both G3 corners; every arm used passes G1 |
| **INCONCLUSIVE** | anything else, a guard failure or a missing arm included |

- The 8 pp floor is 1B's (PRE:131, :142). It is 18% of OLMo-2-7B's E and 15% of Llama-3.1-8B's E (I). Λ/E is reported beside it.
- G4 uses the family's own untuned unit. HarmBench and Granite come from pods, one device per contrast, as at 1B (PRE:216–228). The "harm" wording rule is 1B's (PRE:214).
- **Llama G1 risk [LEAD check before the Part 1 freeze].** **[rev] Wording corrected.** For Llama-3.1-8B a0 seed 1102, F L103 reports 63 of 600 answers "incoherent" (10.5%) and the answers-end check TOO CLOSE (R: F L103). G1's bar is ≤ 10% failing the coherence screen, and a short-answer TOO CLOSE counts as a G1 failure (R: PRE:147). Whether F L103's count is G1's screen count, and whether the frozen bars read 10.5% as a failure or as TOO CLOSE, is what the $0 check below decides (I). If Llama's R or unit arms behave alike, G1 will block TC on Llama. Recommended: keep 1B's G1 unchanged, for consistency. If the lead's $0 check (the frozen G1 code on the Llama a0 units) shows that the a0 units fail G1, raise it to the user before the Part 1 freeze.

**No length control, no Gate C and no second floor at 7–8B (I).** The 1B wording ("content-localized" or "localized under the per-example-mean loss", PRE:255) carries over. TC never re-reads a 1B verdict. **[rev] Clarified.** "Carries over" means the 1B label is quoted as 1B's. With no length control at 7–8B, the 7–8B claim itself uses PRE:255's second form ("content and answer length not separated") even when 1B read "content-localized", because u's length profile could act differently at 7–8B (I).

**Optional extension [USER: yes or no; default no, the re-plan's budget].** If a unit is INCONCLUSIVE with no guard failure and Λ + 1.638 × SE_T ≥ 8 pp, run it at 1104 and 1105 against block A's R_4 and R_5. Re-read once over 5 seeds: σ̂_x = max(√P_x, σ_eval), with P_x = [2·SD(r)² + 4·s_u,5²]/6 for k = 1; SE = σ̂_x/√5. TRANSFERS uses the same bar. DOES NOT TRANSFER uses 2.353 (t_0.95 at 3 df) in place of 1.638 on this second look, so a true 8 pp unit still reads DOES NOT TRANSFER only about 10% of the time (simulation; CALC `tc_ext2_out.txt`). Cost: 2 runs per contested unit and family, about $6–8 each pair of runs (E). If block A has not run, R_4 and R_5 must run first (+2 runs).

**Operating characteristics (simulation, k = 1, 200,000 runs per cell, τ = 1 pp, σ_eval floor 1.3 pp; the guards are not simulated, so these are upper bounds, as in PRE §4; CALC `tc_sim_out.txt`, `tc_ext2_out.txt`).**

| σ_pair | True Λ_78 | TRANSFERS / DOES NOT, 3 seeds | TRANSFERS / DOES NOT, with the extension |
|---|---|---|---|
| 3.75 | 0 / 6 / 8 / 10 / 12 | 0% / 18% / 49% / 80% / 96% ; 96% / 30% / 9% / 2% / 0% | 0% / – / 60% / 91% / – ; 98% / – / 10% / 2% / – |
| 5.45 | 0 / 6 / 8 / 10 / 12 | 0.5% / 22% / 43% / 65% / 83% ; 80% / 22% / 9% / 3% / 1% | 0.5% / – / 57% / 82% / – ; 86% / – / 10% / 3% / – |
| 8.24 | 0 / 6 / 8 / 10 / 12 | 2% / 20% / 31% / 44% / 58% ; 55% / 17% / 9% / 5% / 2% | 3% / – / 46% / 64% / – ; 61% / – / 10% / 5% / – |

- With k = 2, power falls: at σ_pair 5.45, a true 10 pp unit reads TRANSFERS 51% of the time (CALC `tc_sim_out.txt`).
- TRANSFERS is a bar on the point estimate, not proof of an effect ≥ 8 pp. A true 6 pp unit passes about 20% of the time, as at 1B (PRE:172).

**T4 for TC.** New files: 2 (the Llama unit files) and 6 (the transfer reading) of §9.2. Read-only uses: SEAL's `unit_g-*.json` and the sealed 1B verdict record. TC touches no §9.3 file and never re-reads a 1B verdict.

**[rev] Input keys.** On OLMo-2-7B the TC and N arms use SEAL's edit files, so their arm ids (`edit-<SHA-256>`) and seeds equal those of Gate B's 1B arms. Judge files carry `arm`, `seed`, `host` and `complete_sha256` (R: PRE:215). The new readings (§9.2 items 5 and 6) must key every input by `complete_sha256` and family, never by arm and seed alone, so a 1B file can never enter a 7–8B contrast (I).

**Claims.** Per family: "the OLMo-1B unit u, removed from the same Dolly rows, also restores ≥ 8 pp beyond random removal in <family>". **[rev]** As at 1B, this is a bar on the point estimate (PRE:141), so the claim also reports the one-sided 95% lower bound Λ_u,78 − t × SE_T. "Transfers at 7–8B" without a family name needs TRANSFERS in every family that ran. [C] with Llama-3.1-8B: the wording names the change of family and size together.

**Money (E).** 3k runs per family: about $8–11 (OLMo, k = 1) to $20–25 (Llama, k = 2), +20%. Both families with k = 2 come to about $56, as RP:91 says. **[rev]** Plus one Granite judge launch per family for the Λ_Granite direction check, about $0.7–1.7 each (R: PRE:315, the 1B launcher's figures; E at 7–8B), and the guard's need at launch (§3.2).

---

## 8. F: the family choice for option C [USER, fixed before Gate B wave-1 outcomes are read and before N launches]

**Why the deadline.** B can fall back to C on 20 Nov, so the rule must exist under both options. The family must not be chosen after any 7–8B or 1B outcome, a Gate B wave reading included (I). **[rev]** RP decision 6 sets only "before the noise block" (RP:149); the earlier deadline (before Gate B wave-1 outcomes) is this draft's proposal. If the user decides later, the choice is disclosed as made after that reading.

**Options.**
- **F1:** OLMo-2-7B, fixed now. **[rev]** RP decision 6 lists only F3 and F2 (RP:149); F1 is this draft's addition.
- **F2:** Llama-3.1-8B, fixed now (the published setting). **[rev]** More exactly, the published setting's model: PLAN-S stage 4 names Llama-3.1-8B-Instruct with Alpaca (R: PLAN-S:228); the main-study config uses `meta-llama/Llama-3.1-8B-Instruct` on Dolly (R: `SS/configs/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json`:6).
- **F3:** the family with the smaller σ̂_F from N. If the two values differ by less than a factor of 1.5, F1 (or F2, as the user names) applies.

**Evidence.**

| | OLMo-2-7B | Llama-3.1-8B |
|---|---|---|
| Main-recipe a0 seeds in hand | 1101–1103 (M) | 1101–1102 (M); 1103 planned in N |
| E, pp | +49.67, +37.17, +45.50; mean +44.1 (M) | +52.50, +54.00; mean +53.25; the band holds the 55 pp edge (R: F L103) |
| Per-arm seed SD | 6.36 pp (2 df) | 1.06 pp (1 df) (M: SIDE, F L103); the difference is not significant: F = 36 on (2, 1) df, one-sided p ≈ 0.12 (I; CALC `fratio_out.txt`) |
| Answers end (G1 risk) | passed (R: F L105) | TOO CLOSE; seed 1102 at 10.5% (R: F L103) |
| Manifest | Gate B's PREP: SEAL files reused byte for byte; 1B and 7B arms remove the same rows (M) | `c52a50af`, shared with Llama-3.2-1B; new files, same row lists (M) |
| Main-LR a0 adapters on the Mac | e1 for 1101–1103 (M) | none; adapter-scaling references need retrains (M; F L94) |
| Recipe-G reference at the main LR | 3 units on X (M) | none; 3 new runs (M, I) |
| Cost per arm (E) | $2.8–3.6 | $3.3–4.1 |
| Transfer check from OLMo-1B | within the family: a clean size test | across family and size |
| External value | open data and weights | the published setting of PLAN-S stage 4 (PLAN-S:228); DataRx used Llama3-8B (PLAN-S:34) |

- **T4 for F.** No file.
- **F3 is weak (I; CALC `power_out.txt`).** With 2 df per family, the smaller σ̂ belongs to the truly less noisy family with probability 0.61 / 0.69 / 0.80 / 0.90 at true SD ratios 1.25 / 1.5 / 2 / 3. The chosen family's σ̂ is also biased low. So under F3 the seed rule must read σ̂_pool, not the chosen family's value (§3.3 already does).
- **Recommendation (I): F1, OLMo-2-7B.** It is cheaper, has a cleaner transfer test, reuses every sealed file and adapter, has no answers-end issue, and sits further from saturation. **[rev] The case against F1 that the draft did not weigh:** the only noise evidence points the other way. OLMo-2-7B's a0 per-arm SD is 6.36 pp and Llama-3.1-8B's is 1.06 pp (M: SIDE, F L103). The difference is not significant (p ≈ 0.12), but if it is real, Llama-3.1-8B gives much more power per seed, and F1 picks the noisier family. One more point for F1: Llama-3.1-8B is a gated model, and a fork of the Gate B kit has no gated-token path, so a Llama kit needs security-reviewed work (KCR:140); under [B] this work is needed anyway. The recommendation stays F1, because the noise evidence rests on 3 df and the other reasons are certain; the user should see this trade-off. **The case for F2:** reviewers know Llama-3.1-8B, and it is the published setting. Under [C] with F1, the published-setting replication is lost, and the re-plan moves Alpaca to OLMo-1B (RP:75). This is the user's trade-off.

---

## 9. EM and T4: keeping the frozen 1B Gate B valid [B+C]

### 9.1 Rules

- **EM-1, engine and environment [LEAD].** Every 7–8B arm that pairs with an engine-X unit (N, TC, blocks A and B) trains and evaluates on engine X (`472fc7f6…`). The lead keeps a packed engine-X bundle, pinned by its SHA-256, for these arms after engine round Y lands in main (I). Engine Y is used only for stage-3 confirmation with fresh seeds (PLAN-S:215). If any paired 7–8B arm must run on another engine, an X → Y certificate must pass first: a train-only re-run of a0-1101 with equal q and e1 adapter and optimizer fingerprints, and an evaluation-equivalence certificate, as Gate B had (PRE:106; F L114). Otherwise that family's a0 and R arms re-run on the new engine. **[rev] Conflict with the engine round Y design.** EYD puts B+Qi (Y3) into engine Y, due at the stage-1 freeze, and uses it in 7–8B block B (EYD:31, :78). Its certificate includes "one 7–8B re-run per reused side-project family" and promises byte-identical training outputs for every job that exists at X (EYD:29-30). So "engine Y only for stage 3" (above) does not hold if EYD is adopted. Proposed rule (I): a paired 7–8B arm may run on Y only after that certificate, with the 7–8B re-run of the family's a0-1101 matching its q and e1 adapter and optimizer fingerprints, has passed; until then, every paired arm runs on X. The A1 pass runs on the engine that trained its a0 states (EYD:81). **[LEAD]** (§12 LEAD item 11). Environment: Gate B's rule (PRE:107), with the family's a0-1101 unit as the reference. On a mismatch: the a0-free fallback for N (§3.3). Before any paired contrast, the family's a0 at 1101–1103 (and any R arm from the old environment) re-run in the new environment, so that every paired arm of a family shares one environment (+3 runs per family for a0, about $9–12, E).
- **EM-2, money isolation [LEAD].** A 7–8B pod launches only if the account balance, read at launch, minus every running pod's remaining cap × its price, minus that pod's cap × $1.85 (**[rev]** the frozen guard's own terms, BUD:4-7; the draft's "+ $1" is the judge launcher's reserve, not the kit's), still covers Gate B's next frozen need (the kit's `funding_need_usd`; $83.91 before wave 1 at measured rates, RP:13), the storage allowance and the $6 reserve. So every Gate B launch still meets its frozen threshold (RP:93). The $10/h price limit stays (RP:157). **[rev] Cross-kit visibility.** The frozen Gate B guard finds caps and create intents only in working copies beside it named `family-probe-*` or `gate-b-olmo*` (BUD:39, :53-92). A 7–8B pod in a working copy with another name counts in Gate B's guard at 15 h × its price, about $26.85 (BUD:24, :94-100), which can block a Gate B launch that EM-2's arithmetic says is safe. So every 7–8B working copy is named `tmp/family-probe-<name>`, for example `tmp/family-probe-s78-olmo2-7b-n/` (as KCR:143 and KD7 propose), and its budget code keeps the same `KITS_GLOB` and the same lock file, `tmp/family-probe-budget.lock` (BUD:26, :32), so 7–8B and Gate B launches serialize.
- **EM-3, seeds.** 7–8B main-study seeds stay inside 1101–1116 (development namespace). The rule "no scorer built on a0-1101 states is evaluated at 1101" holds at 7–8B for A1 and L1 (PLAN-S:116).
- **EM-4, testing families.** Each (family, size) is its own Holm family at 5%, as PLAN-S:119 treats the Llama replication. No α is shared with 1B. "Replicates at 7–8B" means the same sign, with the size difference below its stated MDE (PLAN-S:244, carried from families to sizes; I). D5 = (a) holds: P1–P6 (or P1, P3, P6 under a branch) are primary; the selector is secondary and model-based; no selector runs at 7–8B (**[rev]** I from F L78: F L78 makes the selector secondary and model-based and moves the held-out selector comparison to a later study; it does not name 7–8B).
- **EM-5, blinding line.** The Part 2 text states the 7–8B values its authors saw (N's r_j, σ̂, mean r and E of Llama a0-1103), in the form of S1B:121 (m) (I).

### 9.2 New files that this design adds (none exists yet; each is a new path)

1. `research/experiments/2026-1x-xx-78b-preregistration.md`: this text after the lead's edit (Part 1), then Part 2.
2. `.ai/inputs/scale-78b-sealed-llama3-<date>/`: a new wrapper `build_sealed_llama3.py` (it loads SEAL's frozen `build_sealed.py` by path after its SHA-256 check, `80cb8944…`, as REQ-4 does, S1B:77; it never copies or edits it); `out/edits/R_d1–R_d16.json` and `out/edits/unit_g-*.json` (8) on `c52a50af`; `out/MANIFEST.json`; a README. Decisive $0 test: every remove list equals SEAL's for R_d1–R_d5 and the 8 unit files. These files also serve Llama-3.2-1B, which has the same manifest (M). **[rev] The frozen builder refuses the Llama manifest.** BLD pins the OLMo prepared folder and its manifest hash, and its `Inputs` stops on any other manifest (R: BLD:60-61, :143-144). So the wrapper cannot run BLD on `c52a50af`. Route (I): build BLD's `Inputs` from PREP (unchanged, its own folder), call its `draw_r(inputs, d)` for the remove lists (the draw reads only group ids and sorted member ids, PRE:88, and those are equal in both manifests, M), and write each Llama edit file with the wrapper's own writer, with `manifest_sha256` = `c52a50af…` and a provenance naming both scripts' SHA-256. The unit files take each unit's full member list. Byte equality with SEAL's files is then impossible (the manifest field differs), so the test is: equal remove lists; `SS/edits.py` `parse_edit` accepts each file against the Llama prepared set (R: `SS/edits.py`:116-117); and the wrapper refuses if the two manifests' groups or member lists ever differ. The wrapper never writes under SEAL. Coordinate with whoever builds Llama-3.2-1B's files for stage 2, so one set exists (I).
3. OLMo R_d9–R_d16 on PREP, only for plan B9 or the 12-seed branch: a new wrapper (d = 6–8 come from REQ-4; S1B:77). **[rev]** Put it at `scripts/scale78b/build_r_draws_78b.py`, not beside REQ-4's script: `scripts/stage1/**` belongs to the stage-1 builder (R: S1B:151). Same route as REQ-4: load BLD by path after its SHA-256 check and call its `draw_r` for d = 9…16; reproduce d = 1…5 first.
4. `runkit/scale-78b/` and its state under ~~`tmp/scale-78b-*/`~~ **[rev]** `tmp/family-probe-s78-*/` (EM-2: the frozen Gate B guard sees only `family-probe-*` and `gate-b-olmo*` working copies, BUD:39): the 7–8B kit (edit arms, measured-upper caps, the EM-2 guard). Parts may be copied from `runkit/gate-b-olmo` and `runkit/family-probe`; neither is edited. **[rev]** The kit's shell, cap rule and name are KCR's subject (KCR KD7, KD10; it names the kit `runkit/stage1-78b/`); use one name for both designs.
5. `scripts/scale78b/noise_reading.py`: N's reading and the seed rule. It reuses the frozen Gate B reading's σ_eval and SD functions unchanged, by import or by a copy with a parity test. The test must reproduce NG on Gate B's wave-0a inputs: σ̂_gate 1.83, fallback 2.16, σ_eval,0 1.28. **[rev]** It keys every input by `complete_sha256` and family (§7, input keys). It prints no U of a method arm.
6. `scripts/scale78b/transfer_reading.py`: TC's reading. **[rev]** Same input keys as item 5.
7. `scripts/scale78b/blinded_sigma.py`: SR-2's σ̂_A (only if SR-2 is adopted).
8. Part 2 only: 7–8B recipe-S configs for A1 in `SS/configs/`. JSON configs are outside the engine identity: `SS/common.py:25-36` hashes only the package's top-level `*.py` files and 7 minimal-safety modules (R; F L108). **[rev] Two corrections.** (a) Timing: block 0 runs the A1 passes by 9 Nov (RP:102), and an attributes job needs its a0 folder under the job's own recipe (R: PRE:99), so the 7–8B recipe-S configs and the a0-1101 retrains under them are needed by block 0, not only by Part 2's 20 Nov freeze. That can be before Gate B's last kit pod. (b) Bundle effect: Gate B's pack copies every `.py`, `.json`, `.md` and `.lock` file under `experiments/safety_selection/` into each later Gate B bundle (R: PACK:220-222). A new config changes no pinned value (the engine identity excludes configs; the bundle's hash is computed per pack, PACK:252), so it is not a T4 change (I). But it does enter Gate B's pods, and while it is uncommitted it blocks every Gate B pack (R: PACK:195-199). Rule: commit it by explicit path when no Gate B pack is in progress, then run the T3 re-check (§9.3). Gate B's recipe maker is pinned to the 1B recipe (KCR:140), so a 7–8B recipe-S maker is a new script at a new path.

### 9.3 Files this design must not touch until Gate B's last kit pod (T4, S1B:65) — confirmed untouched

- Engine files: `SS/*.py` and the 7 reused `experiments/minimal_safety/` modules (R: `SS/common.py:25-36`). No new `.py` goes into `SS/`; any 7–8B code lives in `scripts/scale78b/` or `runkit/scale-78b/`.
- Gate B pinned scripts: `scripts/make_anchor_answers.py`, `scripts/gate_c_representation.py`, `scripts/gate_c_classifier.py`, `scripts/make_gateb_recipe.py`, `scripts/gate_b_reading.py`, SEAL's `build_sealed.py`, and `.ai/inputs/gate-b-anchors-20261008/make_anchor_prompts.py` (R: PRE:326). A 7–8B variant of any of them is a new file at a new path. The Gate B judge launcher `scripts/gate_b_mac_judges/` is used unchanged. **[rev]** It is not on T4's list, but Gate B uses it (R: PRE:217, the reviewed pod launcher), so treat it as frozen until Gate B's last judge launch: any change that 7–8B units need goes into a copy at a new path. An uncommitted edit under `scripts/` would also block every Gate B pack (R: PACK:195-199).
- Gate B kit files: `runkit/gate-b-olmo/**` and `tmp/gate-b-olmo/**`.
- Sealed files: SEAL `out/**`, `.ai/inputs/gate-b-anchors-20261008/out/**`, the anchor file and recipe S (`ceffe0ef…`). SEAL's edit files are read and copied into the 7–8B bundle by hash. They are never written.
- **T3 [LEAD].** New files are committed by explicit paths. None sits untracked in `scripts/` or `experiments/` while a Gate B pack may run (S1B:64). After each such commit, before the next Gate B launch, the lead re-checks that the engine identity is `472fc7f6…`, the kit equals `runkit/gate-b-olmo` at HEAD, and the PINNED_SCRIPTS hashes are unchanged.
- **Prep item 2 (any-model Part C scripts; RP:114) [LEAD].** These are stage-1 scripts, not Gate B files. But their code is a stage-1 commitment before wave 1 (F L251). ~~Land the any-model change before wave 1; or have its tests show byte-identical 1B outputs, and freeze the 7–8B settings rule (for example the layer-index rule) before wave 1. Otherwise the 7–8B scorers are "post-Gate-B exploratory" by F L251.~~ **[rev] Corrected.** F L251 and PRE:327 bind the 1B stage-1 commitments. The 7–8B scorers are new work under the 7–8B pre-registration (RP:93), so F L251 does not make them exploratory, provided their rules are frozen before their own outputs are read (§10). The real F L251 risk is the other way: changing the committed 1B Part C code after wave 1. **Simplest route (I; as EYD:83 proposes):** the generic scripts are new files at a new path, and the 1B scripts stay byte for byte as committed in REQ-21. A parity test shows that the generic version gives byte-identical outputs on the 1B inputs.

---

## 10. Timing (latest dates from RP §5; I)

| By | What |
|---|---|
| Before Gate B wave-1 outcomes are read (wave 1 latest start 27 Oct) | **Part 1 frozen**: S, SR (with SR-2 yes or no), H, F, TC (with the extension yes or no), the Llama seed-1103 rule, predictions N1–N2. If the user needs more time, S, SR and H may wait until N launches; F and TC may not. **[rev]** The 1B part of S cannot wait: if S-P is chosen at 1B, it goes into REQ-21 before wave 1 launches (§4) |
| Before N launches (latest start 9 Nov) | Part 1 frozen (if not already); the Llama sealed files built and committed; the 7–8B kit reviewed; F1 money in the account. **[rev]** About $129 or more in the account if both N pods run in parallel (§3.2); the working copies named `tmp/family-probe-*` (EM-2) |
| Block 0 (with N or after) | the a0-1101 retrains for A1, with the fingerprint check (§2.3). **[rev]** Before any block-0 scorer output (A1, L1, S3, S4, H1) is read: those scorers' 7–8B rules, settings and code hashes are committed, as T1 does for A1 at 1B (R: S1B:62). This part of Part 2 is therefore due by block 0, not by 20 Nov |
| After N | N's reading; the seed rule's provisional plan; the 20 Nov gate's noise input |
| About 20 Nov | **Part 2 frozen** with its blinding line; the B/C choice (RP decision 2) |
| After 1B Gate B's verdict | TC, if LOCALIZED |
| After block A | SR-2's σ̂_A (if adopted); block B's design |

---

## 11. Part 2: not drafted here (frozen before 7–8B block A; **[rev]** its scorer rules before block 0's scorer outputs are read, §10)

- Arm rules per family: A1 (an anchor job per family; recipe S_78; the retrain); L1 (layer rule from prep item 2); H1 (by the family manifest's target tokens; I: OLMo-2-7B's H1 file equals 1B's, because the manifest is the same); the S-pool, S1, S3 and S4 (S4 from the family's own untuned answers).
- References: the safety prompt; adapter scaling (OLMo-2-7B from the Mac adapters; Llama-3.1-8B from retrains); recipe G (OLMo-2-7B units in hand; Llama-3.1-8B 3 new runs); B+Qi; Safe LoRA.
- Limits: O against the family's own untuned model; the τ_O grid; τ_L from the family's a0 seeds (S1B REQ-19 form). Judges: HarmBench and Granite pods, one device per contrast. Cost conventions. The confirmation choice rule (≤ 2 contrasts per family, engine Y; RP decision 8). Alpaca ([B] Llama-3.1-8B, reduced; [C] OLMo-1B; RP decision 7). The token-accounting reports of S1L §5 item 1, carried to 7–8B.

---

## 12. Decisions needed

**[USER]**
1. **S, the analysis scale** (§4): S-U (PLAN-S as written) or S-P (seed-blocked; recommended), at both sizes. The 1B part must be in REQ-21 before Gate B wave 1.
2. **H, the high-noise branch** (§6): (a) SESOI 10 pp; (b) P1, P3, P6 at 12 seeds; (c) both; (d) review; or (e) money-contingent (recommended: (b), else (a)). Fixed before N.
3. **SR-2, the blinded re-check after block A** (§5.3): yes (recommended, if blinding can be kept) or no.
4. **F, the family for option C** (§8): F1 OLMo-2-7B (recommended), F2 Llama-3.1-8B, or F3 smaller σ̂ (not recommended). Fixed before Gate B wave-1 outcomes are read.
5. **TC** (§7): confirm the rule; the optional extension yes or no (default no).
6. **RP decision 5**: reuse the side project's engine-X units as main-study a0 (evidence in §2), and run Llama-3.1-8B seed 1103 with "the rung stays" (§3.1).
7. **RP decision 2, restated** (§5.1): the 20 Nov gate reads this rule's plan, the branch cost included. Under S-U, "allows plan A" is already false.
8. **The SR "review" ceiling** (MDE above 2 × SESOI; §5.1): keep, or name another value.
9. **N's money** (about $26–32 with the allowance; §3.2) at the F1 funding event. **[rev]** The account must hold about $129 or more at launch for two parallel N pods, because Gate B's hold and both caps are counted (§3.2).
10. **[rev] SR under [C]:** the pooled σ̂ of both families (4 df; assumes equal noise; recommended with SR-2) or the chosen family's own σ̂_F (2 df) (§3.3).
11. **[rev] Seed-rule thresholds under S-P:** keep 4.5 / 6.0 (recommended; MDE about 6.4–6.5 pp) or rescale to 4.22 / 5.56 (MDE 6.0 pp) (§5.1).
12. **[rev] D5 and H:** confirm that (a) or (c), if chosen, is a 7–8B change to D5's "SESOI 5 pp", made by the user (§6).

**[LEAD]**
1. Write predictions N1 and N2 before N launches (§3.5).
2. Build the new files of §9.2 at new paths, with the parity tests; integrate by explicit paths (T3); re-check the Gate B pack identity after each commit.
3. Read OLMo-2-7B a0-1103 and Llama-3.1-8B a0-1103 by the frozen family-probe bars (report only). Check that HarmBench and Granite files exist for every reused a0 unit.
4. Pin every input of §2.1 by SHA-256 in the Part 1 record.
5. Apply EM-1 and EM-2 at every 7–8B launch.
6. Put the a0-1101 retrains with A1's block-0 pass; re-read N with the fallback if a trigger fires.
7. Run the $0 Llama G1 check (§7) before the Part 1 freeze.
8. ~~Land prep item 2 before wave 1, or show byte-identical 1B outputs (§9.3).~~ **[rev]** Build the any-model Part C scripts as new files with a 1B parity test, and keep the 1B scripts committed in REQ-21 unchanged (§9.3).
9. Choose N's pod layout for Llama-3.1-8B (one 4-job pod or two 2-job pods; §3.2).
10. Under S-P: the seed-layout edits (a0 at 1107; R_8 kept for the sensitivity; §4).
11. **[rev]** Settle the engine for paired 7–8B arms with the engine round Y design: X only, or Y after its certificate with the 7–8B a0-1101 re-run per family (§9.1 EM-1; EYD:30-31, :78).
12. **[rev]** Name every 7–8B working copy `tmp/family-probe-*`, with the shared lock (§9.1 EM-2), and use one kit name across this draft and KCR (§9.2 item 4).
13. **[rev]** Build the Llama edit files with the wrapper's own writer on BLD's draw (§9.2 item 2); put the OLMo d = 9–16 wrapper under `scripts/scale78b/` (§9.2 item 3).
14. **[rev]** Commit the 7–8B scorer rules and their code hashes before any block-0 scorer output is read; commit any new `SS/configs/` file only when no Gate B pack is in progress, then run the T3 re-check (§9.2 item 8; §10).
15. **[rev]** Key every 7–8B reading input by `complete_sha256` and family (§7).

---

## 13. Limits, weak points and alternatives

**Weak points (I).**
- σ_pair at 7–8B rests on 4 df after N. §5.2 shows how often the rule then errs. SR-2 is the remedy.
- S-P assumes an additive seed effect. An arm × seed interaction enters the residual, so the final SE stays honest, but the planning value from N (a0 against R pairs) may not hold for method arms, which remove selected rows.
- The pod image has held the same compared fields from 8 to 16 Oct (M). A change would force a0 re-runs (EM-1).
- The per-arm costs assume 3–4 arms per pod; no 7–8B pod has yet run more than two units (RP:162).
- TC's simulation does not model the guards. On Llama-3.1-8B, G1 may block it (§7).
- SR-2's blinding is procedural, and the kit records show U.
- All MDE and TOST figures use the normal approximation; with t at the stage's residual df they are slightly wider (I).
- **[rev]** σ̂_pool assumes equal paired noise in both families; the a0 point estimates differ about 6× (§3.3).
- **[rev]** The S-U exclusion of plan A rests on a 0.03 pp margin and on the reuse of the side units (§4).
- **[rev]** Under S-P, PLAN-S's thresholds mean a paired MDE of about 6.4–6.5 pp, not 6.0 (§5.1).
- **[rev]** This draft and its two siblings (KCR, EYD) are not yet consistent on the kit name and on the engine for 7–8B block B (§9.1, §9.2).

**Alternatives considered.**
1. *Skip N and fix the 7–8B design now.* ~~Under S-U this loses nothing for the seed decision (plan A is already excluded), and R_1–R_3 are still needed for P1.~~ **[rev]** Under S-U, plan A is already excluded, but N still separates plan B9 from H (b): 16 runs per family apart, about $54–69 (OLMo) or $63–79 (Llama) with the allowance (E). R_1–R_3 are still needed for P1. Under S-P it throws away the only 7–8B reading of the pairing gain. So N is kept. Under S-U, fixing H now is possible, but it may pay for 16 runs per family that B9 would not need.
2. *Pool the 7–8B σ̂ with 1B's σ̂_gate for more df.* Rejected: the 7–8B per-arm SD is about 1.7× the 1B one (RP:14), so pooling would bias the plan toward plan A.
3. *A relative SESOI* (for example 11% of E: 4.9 pp for OLMo-2-7B, 5.9 pp for Llama-3.1-8B). It keeps the 1B meaning but adds no power. It is not in RP's list; the user can add it as a variant of (a).
4. *A per-family plan under B.* Rejected (I): it doubles the 2-df decisions. One plan from σ̂_pool is simpler.
5. *A full Gate B at 7–8B.* Not proposed, as RP:90–91.

---

## 14. Process

- **Changed files.** This file; `calc/` (~~8 calculation scripts, the environment and manifest check,~~ **[rev]** 9 calculation scripts and the environment-and-manifest check, 10 scripts in all, and their outputs; the review added `review_calc.py` and its output). All are in `/Users/spiderishi/Coding/attribution/.claude/worktrees/kind-hawking-a6ce04/tmp/gi-vi-parallel/icml-78b-prep/`. Scratch copies of the scripts are in the session scratchpad.
- **Commands run (all exit 0, except where noted).** `date -u` (3 times); `git branch`, `git log`, `git show`, `git status`, `git cat-file` and `git for-each-ref` (read only; the side-note lookup loop printed nothing and was redone with `git log --all`); `shasum -a 256` on the documents, the sealed edit files, the noise-gate output, the unit records and 4 adapters; `ls`, `find`, `grep`, `sed` and short Python reads of record fields; the engine's `config_sha256` and `family_probe_reading.environment_of`, imported read-only with `python -I -B` (the first import attempt failed on a path, exit 1, and was redone); 9 calculation scripts with `.venv/bin/python -I` (exit 0; outputs in `calc/`). A first `grep` hit a regex limit, and a first `python3` lacked numpy; both were redone another way.
- **Read.** RP; PRE §0–§13 (in parts); PLAN-S in full; FOCUS (the entries cited); SIDE in full; S1B and S1L (the parts cited); NG; SEAL's README and edit-file keys; the 7–8B and 1B unit records (fields only); both prepared manifests (metadata only); `SS/jobs.py` and `SS/edits.py` headers; `SS/common.py` code identity; `SS/config.py` seed namespaces; `SS/engine.py` gradient code; the two 7–8B configs; the causal side-study README head.
- **Not done.** No web source was read (none was needed). No simulation of the seed rule beyond the χ² table. No check that Gate B's frozen G1 code passes the Llama-3.1-8B a0 units ([LEAD] item 7). No check of judge files for the a0 seeds 1103.
- **[rev] Review process (2026-10-16, about 22:02–22:30 UTC).** Commands, all exit 0: `date -u` (5 times); `git branch --show-current`, `git log`, `git status --short`, `git show` of SIDE (read only); `shasum -a 256` of RP, PRE, PLAN-S, FOCUS, S1B, S1L, NG, SEAL's MANIFEST, `R_d1`–`R_d3` and BLD, the 7 unit `COMPLETE.json` files and both prepared manifests (every value equals the draft's); `awk`, `sed`, `grep` and `ls` reads of FOCUS L77–L114, L242, L251, PLAN-S, PRE, S1B, NG, BUD, PACK, the Gate B job runner header, BLD's interface, `SS/edits.py`:110-122, `SS/common.py`:25-37, three 7–8B configs (LR and batch fields only) and the sibling designs; `python3 -I` reads of record fields only (NG's numeric fields; the units' GPU, lock and adapter fingerprints; the manifests' seed namespaces); `calc/review_calc.py` with `.venv/bin/python -I`. **Re-checked and confirmed:** every COMPLETE.json SHA-256, U and E value of §2.1; engine `472fc7f6…`, A100-SXM4-80GB and lock `7e0dd998…` on all five main-recipe a0 units; the side units' q and e1 fingerprints (§2.3); NG's 1.83, 1.28, 2.16, 1.905 (fallback SD), mean r 2.5 (SE 1.06) and 5.6; SIDE's per-seed E; every cited FOCUS, PLAN-S, PRE and RP line except those listed in §15 item 10; all of §5.4, §6 and §7's arithmetic (by hand and against CALC). **Not re-checked:** the adapter SHA-256 values of §2.1 (large files), the engine `config_sha256` mapping (the draft ran it), the simulations (read, not re-run).

---

## 15. Review changes (adversarial review, 2026-10-16, about 22:02–22:30 UTC; clock checked at 22:02, 22:16, 22:21 and 22:23 UTC)

Each change is marked **[rev]** in the text. Labels as above.

**Claims that held (M or R, re-checked).** All §2.1 unit hashes, U and E values, the engine, GPU, lock and fingerprints; NG's values; SIDE's per-seed E; the manifests' equal groups and seed namespaces; every SHA-256 in "Short names"; the §5.4, §6 and §7 arithmetic; the §5.2 χ² table; the §8 F-ratio and F3 probabilities; the T4 list of §9.3 against PRE:326 and S1B:65.

**Corrections.**
1. **S-U and plan B9 (§5.1, §0 item 2).** "Plan B9 is unlikely, so H applies almost surely" was not supported. With the 1B ratio of R to a0 spread, P(plan B9) is about 77–87%; at the a0's own spread, about 19% (CALC `review_calc_out.txt`). Plan A's exclusion stands, but by 0.03 pp, and only if the side units are reused (RP decision 5). Alternative 1 of §13 is corrected to match.
2. **The 1B target under S-P (§5.1).** "The rule keeps the 1B target" holds only on PLAN-S's unpaired formula. Under S-P the same thresholds mean a paired MDE of 6.39 / 6.47 pp. New [USER] item 11: keep 4.5 / 6.0 (recommended) or rescale to 4.22 / 5.56.
3. **SR-2's df under [C] (§0 item 3, §5.2).** 30 df is [B]. Under [C] it is about 15 (S-P) or 19 (S-U); the 15-df operating characteristics are added. SR-2 stays much sharper than N.
4. **Pooling across families (§3.3).** The equal-noise assumption is now stated; under [C] with a family fixed now, pooling only buys df. New [USER] item 10.
5. **Money at launch (§0 item 8, §3.2, §10, [USER] item 9).** N spends about $26–32, but two parallel N pods need about $128.76 in the account under the frozen guard with Gate B's hold (E: KCR:177), about $37 above the 16 Oct balance. Idle storage and judge pods are listed as extra.
6. **Cross-kit visibility (EM-2, §9.2 item 4).** The proposed `tmp/scale-78b-*` working copies are invisible to the frozen Gate B guard (BUD:39, :53-92), which would count each running 7–8B pod at 15 h × its price. Renamed `tmp/family-probe-s78-*`, with the shared lock. The guard formula is corrected to the kit's own terms.
7. **The Llama sealed files (§9.2 item 2).** The frozen builder refuses the Llama manifest (BLD:60-61, :143-144). The route is now BLD's `draw_r` on PREP plus the wrapper's own writer; the test is list equality plus `parse_edit` on the Llama set, not byte equality.
8. **Placement and timing of new files (§9.2 items 3 and 8, §10, §11).** The d = 9–16 wrapper moves out of the stage-1 builder's directory (S1B:151). The 7–8B recipe-S configs are needed by block 0 (A1 passes by 9 Nov, RP:102), not only at 20 Nov; they enter later Gate B bundles (PACK:220-222) without changing a pinned value. The 7–8B scorer rules must be committed before block 0's scorer outputs are read, as T1 does at 1B (S1B:62).
9. **Engine for paired arms (EM-1).** The engine round Y design puts B+Qi into Y and uses it in 7–8B block B (EYD:31, :78), which conflicts with "Y only for stage 3". A proposed rule (Y only after its certificate with a 7–8B a0-1101 re-run per family) is added as [LEAD] item 11.
10. **Citations and labels.** The unpaired 2.97 pp is a CALC value, not NG's. The Llama G1 sentence now quotes F L103's own terms. "No selector runs at 7–8B" is an inference from F L78. The blinding-line cite is S1B:121 (m), not S1B:63. F1 is not in RP decision 6's list, and the "before wave-1 outcomes" deadline for F is this draft's proposal. "The published setting" is the model only (PLAN-S:228 pairs it with Alpaca). Process counts fixed (10 scripts, not 9).
11. **Prep item 2 and F L251 (§9.3).** The claim that the 7–8B scorers become "post-Gate-B exploratory" was wrong: F L251 binds the 1B stage-1 commitments, and 7–8B work has its own pre-registration (RP:93). The risk is changing the committed 1B scripts; the simplest route is new generic files with a 1B parity test (EYD:83).

**Additions.** S-U-lit as a stated, rejected third reading (§4). Two more points against S-P at 1B: it is chosen after the wave-0a nuisance values, and REQ-21 needs an added estimator line (§4). The D5 check of each H option (§6). Why SR-2 does not leak outcomes (§5.3). Input keys by `complete_sha256` (§7). The one-sided lower bound beside a TRANSFERS claim (§7). The case against F1 from the noise evidence (§8). The judge launcher treated as frozen until Gate B's last judge launch (§9.3). The kit-route caveat for running R arms under the main config (§3.1). The 7–8B TC claim uses PRE:255's "not separated" wording, since no length control runs at 7–8B (§7). The sequential-pod money and wall-time trade-off for N (§3.2). LEAD item 8 rewritten to match the prep-item-2 correction (§12).

**Not changed.** The recommendations stand: S-P at both sizes; SR-2 yes; H (e) with (b) first; F1; TC with no extension. The review found no design that edits an engine file, a Gate B pinned script, a Gate B kit file or a sealed file. Its new rules (working-copy name, builder route, config commit timing, judge-launcher freeze) keep it that way.

**Remaining decisions.** [USER] items 1–12 and [LEAD] items 1–15 of §12. Most consequential (I): S at 1B before wave 1 (item 1); H with its money (items 2 and 7); F (item 4); SR under [C] (item 10); and, for the lead, the engine for 7–8B block B, settled with the engine round Y design (LEAD item 11).

**Review limits.** No simulation was re-run. The adapter hashes and the engine's `config_sha256` mapping were not re-computed. KCR's and EYD's figures are cited as the sibling designs give them (E or I), not re-derived. No web source was needed.
