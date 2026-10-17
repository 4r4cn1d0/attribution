# Stage-1 decision ledger (input to pre-registration revision 3 and the REQ-21 W1 record)

**Status.** A worker file for the main-study lead (GI VI). It is not frozen and it adopts nothing new. It lists every binding stage-1 decision in one place, with who decided it and where it is written. It changes no frozen Gate B/C rule, no sealed record, not D5 = (a), and no user decision. Where a lead ruling fills a gap in a decided text, the row is marked **[LEAD, under delegation]**. Where no decision settles a point, the point is marked **[LEAD-NEEDED]** with a recommended resolution.

- **Written** 2026-10-17 from 13:15 UTC (clock checked with `date -u` at 13:15 and 13:31 UTC) by an Opus worker, for the lead, under the user's weekend delegation (FOCUS 2026-10-17T09:01 UTC).
- **Read-only.** Main checkout `/Users/spiderishi/Coding/attribution` at HEAD `3536776` (clean for every source below). The only file written is this one. No commit, pod, spend, download, install or agent.
- **Data rules kept.** I opened no `selector.jsonl`, no `hidden/`, no held-out file, no `rows.jsonl`. I printed no row, prompt, answer, anchor or lexicon text. From the committed stage-1 records and settings I read keys, hashes, counts and rule strings only. This file holds no text from any data file.

## 0. How to read this ledger

**Who decided.**
- **user**: the user decided it in a chat (relayed decisions are marked "relayed").
- **user-delegated lead**: the lead decided it because the user gave the decision to the lead ("decide D5 for me", 16 Oct; the weekend delegation, 17 Oct).
- **lead**: the lead decided it inside its own remit (L1–L16, LW items, build rulings).
- **frozen rule**: a frozen pre-registration (Gate B/C revision 5) or a sealed record. Nobody changes it.

**Labels for numbers.** **R** = read in a source. **M** = measured or computed (by a source's script, or by me as plain arithmetic; "M (here)" means me). **E** = an estimate (the basis follows). **I** = inference or judgement. **UNVERIFIED** = nobody named has checked it. **A number inside a ledger row is R from that row's source column unless the row gives another label.**

**Short names** (SHA-256 prefixes computed at 13:20 UTC, M):

| Name | File | SHA-256 |
|---|---|---|
| FOCUS | `research/FOCUS.md` (line numbers at this hash; HEAD 3536776) | `e85d0a66` |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` (§1–§9) | `62f83d69` |
| BRIEF | `.ai/briefs/stage1-commitments-build-20261016.md`, revision 1 | `12cbf463` |
| DRAFT | `research/experiments/2026-10-17-stage1-preregistration/stage1-preregistration-DRAFT.md`, revision 2 | `9ff29fc1` |
| CONS | same folder, `stage1-decisions-consolidated.md`, revision 2 | `d2de3610` |
| EXTR | same folder, `w1-builder-extract.md` | `18b81b26` |
| AMD | `research/experiments/2026-10-17-stage1-analysis-model/stage1-analysis-model-DRAFT.md`, revision 2 | `c8cd8eab` |
| REF | `research/experiments/2026-10-17-stage1-prereg-references/stage1-prereg-references-DRAFT.md`, revision 2 | `5835caae` |
| RB | `research/experiments/2026-10-17-stage1-review-b-rulings/review-b-rulings-DRAFT.md` | `79d49e92` |
| AUDIT | `writing/paper/2026-10-17-review-coverage-audit.md` | `d0967d07` |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md`, revision 5 (frozen) | `5c97cce7` |
| PLAN-S | `research/review/2026-10-08-sharpened-direction-DRAFT.md` (the user-approved basis) | `6ff3ff2b` |
| P78 | `research/review/2026-10-17-icml-78b-prep/78b-preregistration-DRAFT.md` | `e6a73c92` |
| PAPER | `writing/paper/2026-10-08-icml-draft.md` (revision 6h) | `82beb9ba` |
| S1OUT | `.ai/inputs/stage1-commitments-20261016/` (committed stage-1 records) | per file, §1.2 |
| SET | `scripts/stage1/settings/*.json` at HEAD (built Parts E and F) | — |

θ0 = the untuned model. FRE = one full run equivalent. W1 = before Gate B wave 1. W1-P = W1, and before REQ-18's predictions freeze. S1 = before the stage-1 freeze.

---

## 1. The ledger

### 1.1 The frame: frozen rules and earlier user decisions that bind stage 1

| Id | Decision (one sentence) | Who decided | Source | Binds |
|---|---|---|---|---|
| FR-01 | Gate B/C pre-registration revision 5 (`5c97cce7`) is frozen; no stage-1 rule changes any Gate B/C rule, constant, sealed file, guard or reading, and engine X (`472fc7f6`) and every Gate B pinned file stay byte-identical until Gate B's last kit pod. | frozen rule (user, 10 Oct 11:16 UTC) | FOCUS:122; BRIEF:65 (T4) | DRAFT §0.2; every REQ |
| FR-02 | PLAN-S is the approved basis of the stage-1 pre-registration; a PLAN-S rule stands until a later decision replaces it. | user (8 Oct 13:53 UTC) | FOCUS:245 | DRAFT §0.2–§0.3 |
| FR-03 | The headline order is (1) the measured repair comparison, (2) the planted control if funded, (3) Gate B and C; the decision-value map is secondary and model-based, and its predictions are written before wave 1. | user (8 Oct 13:53) | FOCUS:249 | REQ-21 (a); DRAFT §0.5 |
| FR-04 | The primary family on OLMo-2-1B is P1 A1 − R, P2 L1 − R, P3 H1 − R, P4 S1 − a0, P5 S3 − S1, P6 S4 − S1, with 600-row removals, 48-row additions, outcome U, and a 5 pp SESOI read by TOST. | user (8 Oct 13:53); kept by FR-05 | FOCUS:250 | REQ-21 (b); DRAFT §1.2, §3.1, §4.2 |
| FR-05 | D5 = (a): P1–P6 stays the primary estimand, the selector stays secondary and model-based, REQ-22 is not built, the held-out selector comparison is a later study, and the one-example patch is bounded in text. | user-delegated lead (16 Oct 12:15 UTC, "decide D5 for me") | FOCUS:87 | REQ-16–REQ-18; REQ-21 (a), (b), (k); DRAFT §0.2, §7 |
| FR-06 | Method arms run at seeds 1102–1107; no scorer built on a0-1101 states is evaluated at 1101; the blinded seed-count rule reads Gate B's final pooled σ̂ only (≤ 4.5 pp plan A; 4.5–6.0 pp plan B, P1, P3, P6 at 9 seeds; > 6.0 pp no stage 1); seeds run in outcome-free blocks, each on a funding event, and only complete blocks are analysed. | user (8 Oct 13:53); a0 and R counts replaced by UW-03 | FOCUS:251; PLAN-S:116, :118, :232 | REQ-21 (d); DRAFT §1.2–§1.3 |
| FR-07 | The mandatory references are the safety prefix, adapter scaling at 0.75 and 0.5, recipe G at 3 seeds, B+Qi (6 seeds, no warmup) and Safe LoRA; a data repair "dominates" only if it also lies below the adapter-scaling curve. | user (8 Oct 13:53; 8 Oct 17:36 item (4); 9 Oct 10:01; 9 Oct 19:37 item (10)) | FOCUS:252, :234, :160, :134 | DRAFT §5.1–§5.5; S1 builds B10–B12 |
| FR-08 | A "harm" sentence needs the HarmBench contrast with the same sign and at least half the size, no "harm" sentence is written if E_HB < 20 pp, and new pools and anchors are filtered by PKU labels and the lexicon `bbbc71e9`, never by Qwen3Guard. | user (8 Oct 13:53) | FOCUS:253 | REQ-6, REQ-8, REQ-21 (f); DRAFT §2.3 |
| FR-09 | Over-refusal is measured against θ0 on a τ_O grid of 2, 5 and 10 pp; τ_L is 2 SE of a seed-to-seed task-loss difference, fixed before wave 1; more O prompts come only if a $0 check shows a 6-seed O MDE above 5 pp, then from a new public source the user approves, judged on answers capped at 128 tokens after a $0 truncation check, never from the hidden remainder. | user (8 Oct 13:53) | FOCUS:254; PLAN-S:197 | REQ-19, REQ-21 (e); DRAFT §6 |
| FR-10 | Costs are logged in GPU-seconds by stage; 1 FRE per family is the median R-arm time; two cost conventions (C-full, C-lean) freeze before stage 1; c0 is measured on one real lean job; a claim stands only where both conventions agree; no 1B cost ratio is claimed for 7–8B. | user (8 Oct 13:53) | FOCUS:255; PLAN-S:201–:203 | REQ-17, REQ-18; DRAFT §10 |
| FR-11 | One selector spec and one code path serve simulation and replay, and the runs-only rule per cell is frozen from a pre-outcome simulation. | user (8 Oct 13:53) | FOCUS:256 | REQ-16–REQ-18; DRAFT §7 |
| FR-12 | The positive control (stage 1b, funded tier) plants 37 PKU-safe, non-refusing answers as one leaf of nested menus of 8, 32 and 128 cells; a 3-run pilot reads on only if Λ_plant ≥ 10 pp with its lower bound above 5 pp; the plant is committed whether or not it is funded. | user (8 Oct 13:53) | FOCUS:258; BRIEF:20 | REQ-8; DRAFT §8 |
| FR-13 | Before Gate B wave 1, every stage-1 scorer's code and settings hash, every edit rule, the pools, the plant, the primary family, the seed rule, the limits, the judge rule, the selector spec and its predictions are committed; anything added later is "post-Gate-B exploratory"; wave 1 waits for these commitments. | user (8 Oct 13:53; 9 Oct 19:37 item (6)) | FOCUS:260, :134; PLAN-S:239 | REQ-20, REQ-21; DRAFT §11, §13 |
| FR-14 | DataShield-style and Self-Inf-N-style are built before wave 1 if plan usage allows, else recorded as post-Gate-B exploratory before wave 1. | user (9 Oct 19:37 item (9)) | FOCUS:134 | REQ-12, REQ-13, REQ-21 (l) |
| FR-15 | Which money counts as stage 1's funding event is still open. | user (open since 9 Oct 19:37 item (8)) | FOCUS:134; CONS:759 (US-07) | DRAFT §10.5, §14.2 FC-19 |
| FR-16 | Confirmation (stage 3) uses engine round Y on sealed arms and a sealed 200-prompt hidden subsample, at most 2 contrasts per family, chosen by a rule committed before stage 1. | user (8 Oct 13:53) | FOCUS:261 | DRAFT §4.7; CONS LS-18 |
| FR-17 | Recipe B is the main recipe for Gate B and stage 1 on OLMo-2-1B. | user (9 Oct 09:29) | FOCUS:167 | DRAFT §1.1 |
| FR-18 | Dolly stays the benign data; PKU-SafeRLHF stays the safety data for add repairs and the Gate C anchors; Alpaca is the planned second dataset right after Gate B. | user (9 Oct 09:40) | FOCUS:164 | REQ-6, REQ-8; DRAFT §1.1, §9.5 |
| FR-19 | A repair whose contrast against its comparator is significantly adverse at the 5% level on U, over-refusal or task loss is "worse"; the labels are better, equivalent, worse and inconclusive (the O and L part is narrowed by UW-05). | user (8 Oct 18:31; wording 9 Oct 15:23 item 3 (a)) | FOCUS:224, :147 | REQ-21 (c); DRAFT §4.3 |
| FR-20 | GI VI leads the main study and its pods; Gate B runs under PREREG revision 5 and its money rules; wave 1 waits for the stage-1 commitments. | user (15 Oct 19:56, D1 and D3) | FOCUS:105 | every REQ |
| FR-21 | "Stop asking me for approval and go ahead": the lead does the planned steps without approval questions; the money rules, the guard, the $10/h limit and the launch check stay. | user (16 Oct about 19:06 UTC); reading by the lead | FOCUS:85 | every REQ |
| FR-22 | ICML 2027 is the goal for the main paper; TMLR or NeurIPS 2027 stays the fallback until the user names one. | user (relayed, 16 Oct 21:05 UTC); fallback by the lead (I) | FOCUS:83 | REQ-21 (a) |
| FR-23 | For the weekend of 17–18 Oct and as a standing preference, the lead asks nothing and decides pending scope and design choices (ambitious default with a pre-set fallback, or the recommended default), records each, and reports afterwards; spend comes only from money in hand inside the approved plan; a frozen stop rule is recorded as a blocker. | user (relayed 17 Oct; recorded 09:01 UTC) | FOCUS:77 | every row marked [LEAD, under delegation] |
| FR-24 | OLMo 3 7B Instruct is added as a third 7–8B model if funded, OLMo-2-7B and Llama-3.1-8B stay, and the cut order if money is short is 70B, then 32B, then OLMo 3 7B. | user (17 Oct) | FOCUS:78 (8dac6ad) | 7–8B pre-registration; DRAFT §14.3 (superseded part) |
| FR-25 | Pods are created only at or below $10/h, the budget guard plans each pod at $1.85/h, and every stage and block starts on a funding event, never on an outcome. | user (9 Oct 15:29; 8 Oct 13:53) | FOCUS:143, :262; PLAN-S:232 | DRAFT §10.1, §11 |

### 1.2 Sealed stage-1 records (frozen outputs)

| Id | Decision or record (one sentence) | Who decided | Source | Binds |
|---|---|---|---|---|
| FO-01 | The Gate C rankings are sealed (`d6d5cd6b`): pick_A = pick_R = general_qa, pick_F = classification. | frozen rule (lead under PREREG §5) | FOCUS:86 | REQ-21 (m); DRAFT §12.1 |
| FO-02 | The T1 bundle is committed (`9525005`) before anyone read wave-0b's `rows.jsonl`, its 18 files are read-only, and the golden A1 test and A1 contract are defined on engine X. | lead | FOCUS:81 | REQ-2, REQ-8 settings, REQ-14, `labels.json`; DRAFT §0.4 (stale) |
| FO-03 | A1's removal set is sealed (`a1_remove600.edit.json` `5c0e53b7`; selection `9c372fce`): 600 of 4,800 rows, all 8 categories (largest 18.7%), 15.5% of the target-token mass, one boundary tie sealed; it never changes. | frozen rule (lead ran the frozen T1 contract) | FOCUS:76; S1OUT `a1/` | REQ-14, REQ-21 (g) |
| FO-04 | A1's report-only stability (`a1_variants.json` `c1fa6615`): Spearman ρ(q, e1) 0.771; top-600 Jaccard q–e1 0.434; V1 (Adam) against A1 0.314. | lead (report) | FOCUS:76 | REQ-25 (W1-04); DRAFT §9.3 item 2 |
| FO-05 | REQ-19's outputs (`limits_check.json` `a30d7940`): the 6-seed O MDE against θ0 is 11.04 pp with prompts random (1.32 pp seed only), so O-ext fires; τ_L = 0.0067170919092681925 nats (s = 0.002375). | lead | FOCUS:75 | REQ-19, REQ-21 (e) |
| FO-06 | W1-05's strata (`untuned_refusal_strata.json` `9fe33827`): θ0's greedy answer opens with a refusal on 171 of 200 harm prompts and 13 of 100 over-refusal prompts. | lead (report) | FOCUS:75 | REQ-28; DRAFT §9.3 item 3 (a) |
| FO-07 | PHTest (`furonghuang-lab/PHTest` @ `edb80210`, MIT; PHTest.csv `495d109e`) is downloaded to git-ignored `tmp/`; the text-free source record is `phtest-source.json` (`c2795ea4`). | lead (under UW-07a's approved download) | ADD:341; commit 158d2c2 | REQ-6 batch (`build_oext.py`); DRAFT §6.5 |

### 1.3 The 21 user wave-1 decisions (UW-01 to UW-21), as the user decided them

All taken at the recommended defaults by the user's 17 Oct 07:21 UTC message (R: FOCUS:79, verbatim there). The CONS line is the item's text.

| Id | Decision (one sentence) | Who decided | Source | Binds |
|---|---|---|---|---|
| UW-01 | The standing rule is confirmed: default to the more ambitious option and pre-set a fallback with its trigger; it changes nothing frozen (Gate B revision 5, the sealed rankings, D5 = (a), the $10/h limit, the launch go, money in hand). | user | FOCUS:79; CONS:185 | every USER-CONFIRM ladder; DRAFT §14.1 FC-1 |
| UW-02 | The primary analysis pairs arms by seed, in place of PLAN-S:102's "seeds are not paired"; the lead's reading (LW-01) makes HB-C the primary form; HB, S-a and S-aW are pre-registered sensitivities. | user (paired model); lead (HB-C) | FOCUS:79, :80; CONS:194, :379 | REQ-16, REQ-17, REQ-21 (b); B16; DRAFT §3.2–§3.4 (stale: S-a "in force") |
| UW-03 | Seed layout D1: a0 at 1101–1107 and R at 1101–1107 (R_1108 is not run); the six method arms at 1102–1107; 50 cells. | user | FOCUS:79; CONS:205; ADD:331 | REQ-4, REQ-21 (d); DRAFT §1.2–§1.3 (stale: D0) |
| UW-04 | The testing family is the closed graphical family Φ with 24 nodes (U_k two-sided; O_k and L_k one-sided adverse; F_k "feasible at τ_O\* = 5 pp"), start weights 0.15 per U_k, 0.1/12 per O_k and L_k and 0 per F_k, and the passing rules of AMD §B.2. | user | FOCUS:79; CONS:214; AMD:255 | REQ-21 (b), (c); B16; DRAFT §4.1, §4.4 (stale: Holm "in force") |
| UW-05 | Rule R1.3: "worse (O)" needs O-infeasible at τ_O\* = 5 pp against θ0 and O significantly above the comparator; "worse (L)" needs L-infeasible at τ_L against a0 and L significantly above the comparator; the U part of the "worse" rule does not change. | user | FOCUS:79; CONS:224 | REQ-21 (c); DRAFT §4.3–§4.4, §6.2 (stale: 18:31 rule "in force") |
| UW-06 | One primary over-refusal bar, τ_O\* = 5 pp (the same number as Gate B's G4, which does not change); 2 and 10 pp are reported. | user | FOCUS:79; CONS:234 | REQ-21 (e); DRAFT §6.3 |
| UW-07a | O-ext from source N: when REQ-19 shows a 6-seed O MDE above 5 pp, 400 harmless PHTest prompts (MIT; the user's yes covers this small download) join the dev 100 as the primary O bank; fallback F (the dev 100 only); REQ-19 fired at 11.04 pp. | user | FOCUS:79, :75; CONS:243 | REQ-6 (`build_oext.py`), REQ-19, REQ-21 (e); DRAFT §6.5 (stale: silent F) |
| UW-07b | No draw from the hidden over-refusal remainder; the 8 Oct rule stays. | user | FOCUS:79; CONS:252 | REQ-26 not built; DRAFT §6.5 |
| UW-08 | Label order (a): "worse" first, naming the measure, then "better", then "equivalent" with its grade, then "inconclusive"; the full row is always printed, with "significant, below the SESOI" in the row when it applies. | user | FOCUS:79; CONS:260 | REQ-21 (c); B16; DRAFT §4.5 |
| UW-09 | The skill limit is held-out task loss on all 200 task rows; ARC is report-only. | user | FOCUS:79; CONS:269 | REQ-19, REQ-21 (e); DRAFT §6.7 |
| UW-10 | H1 under recipe bt stays secondary arm 5 at 3 seeds. | user | FOCUS:79; CONS:277 | REQ-21 (g); DRAFT §9.1 item 5 |
| UW-11 | The four recorded deviations from PLAN-S are accepted: S1's pool wording, L1's layer-scan statistic, L1's two-sided score, and L1's scaling of the post-sublayer norm outputs. | user | FOCUS:79; CONS:285 | REQ-10, REQ-21 (i); DRAFT §14.1 FC-10 |
| UW-12 | "Frozen once" means that Gate C's representation script stays pinned and REQ-3 is a new module with a byte-equality test at Gate C's settings. | user | FOCUS:79; CONS:293 | REQ-3 |
| UW-13 | For other model families the margin is δ_fam = 5 × E_fam / 45.11 pp (0.1108 × that family's Gate A mean E), fixed before its stage-2 runs, with 5 pp absolute reported beside it. | user | FOCUS:79; CONS:301; AMD:378 | REQ-21 (b); DRAFT §4.2 (stale: silent 5 pp), §4.6 item 3 |
| UW-14 | The title keeps "Compute-Matched": the token-axis analysis (ADD §5 item 1) is the token-matched analysis beside the row-matched one, and (ambitious) token-matched random arms R_tok for A1, L1 and H1 are pre-registered secondary arms in the funded tier (about $19 with contingency, E: EXTR W1-03), with the analysis alone as the fallback. | user (with the lead's correction of the relayed mapping) | FOCUS:79; CONS:310 | REQ-27, REQ-30, REQ-21 (a), (g); DRAFT §9.3 (stale: "no new arm") |
| UW-15 | Headline item (2) reads "does each diagnostic find a concentrated, harmful-prompt cause". | user | FOCUS:79; CONS:318 | REQ-21 (a); DRAFT §8.5 F1 (stale) |
| UW-16 | No second, benign-topic plant now; a later benign plant is post-Gate-B exploratory. | user | FOCUS:79; CONS:327 | REQ-8; DRAFT §8.5 F10 |
| UW-17 | No prompt-only classifier score is computed. | user | FOCUS:79; CONS:335 | REQ-23 settings |
| UW-18 | REQ-23 (the per-row content-classifier scorer) is built, and wave 1 waits for it; it gets no item (9) exception. | user | FOCUS:79; CONS:343 | REQ-23, REQ-20; DRAFT §8.5, §11 |
| UW-19 | The Llama-3.2-1B Gate B-lite rules freeze with the W1 record at the note's defaults (U0 "K − LC" if stage 2 is funded at about the re-plan's level, else "W0"); the 9 Oct rule "Alpaca right after Gate B" stays. | user | FOCUS:79; CONS:351; ADD:337 | REQ-18 (Llama predictions), REQ-21 (j); the LLB note pinned by SHA-256 |
| UW-20 | Two more sealed plant locations go into the W1 record as conditional rule text; they run only if stage 1b is funded; fallback the $0 relocation replay. | user | FOCUS:79; CONS:359; ADD:336 | REQ-8 (new settings file), REQ-21 (i); DRAFT §8.5 F9 |
| UW-21 | OLMo-2-1B's P1–P6 stays the confirmatory primary family under any re-plan option. | user | FOCUS:79; CONS:367 | REQ-21 (a); DRAFT §14.1 FC-18 |

### 1.4 The 35 lead wave-1 decisions (LW-01 to LW-35)

All at the recommended defaults, except LW-01 (HB-C primary), LW-07 (τ_L against a0) and LW-18 (REQ-12 and REQ-13 built), which the lead decided itself because GPT no longer leads the main study (R: FOCUS:80). The CONS line is the item's text.

| Id | Decision (one sentence) | Who decided | Source | Binds |
|---|---|---|---|---|
| LW-01 | HB-C is primary: one seed shift per design cluster, {a0, S1, S3, S4} and {R, A1, L1, H1}, so every primary contrast lies inside one cluster; HB is a pre-registered sensitivity; S-a and S-aW are reported. | lead | FOCUS:80; CONS:379 | REQ-16, REQ-17, REQ-21 (b); B16; DRAFT §3.3 |
| LW-02 | Confirm AMD A2 (the crossed prompt part), A3 (the sensitivities S-a, S-aW, S-HBC, S-b2x, S-HB0, S-G, S-HB-tok; a differing label printed beside), A5 (the plan-A/B record prints the predicted MDEs, the "better" 80% effect and P(equivalent \| 0)), the revision-2 items (per-contrast O and L variance; the equal-variance flag; "df 42 (nominal)"), B3 (equivalence grades 1 and 2, the 98.33% interval) and C1 (δ = 5 pp stated as about 11% of E). | lead | FOCUS:80; CONS:388 | REQ-21 (b), (c), (d), (f); DRAFT §3.4–§3.5, §4.2–§4.3 |
| LW-03 | O's error model is "prompts random" (the same crossed model as U), and the seed-only value is reported beside every O number. | lead | FOCUS:80; CONS:402 | REQ-16, REQ-19; DRAFT §6.4 |
| LW-04 | REQ-19 runs before wave 1 in both O conventions, the prompts-random value decides U8, and its τ_L must equal s = 0.0023749, τ_L = 0.0067171 and SE 0.0013711 nats; done (FO-05). | lead | FOCUS:80, :75; CONS:413 | REQ-19, REQ-21 (e), (h) |
| LW-05 | The three $0 Mac checks (128-token truncation, judge–lexicon agreement, partial refusals) run before U8 with both sides on one device; the truncation bar is at least 97 of 100 flags agreeing per unit and no unit's count moving by more than 2. | lead | FOCUS:80; CONS:421; SET `limits_overrefusal_checks.json` | W1-18; REQ-21 (e), (m); ADD §9 |
| LW-06 | Feasibility uses O(m) − O(θ0) and L(m) − L(a0): "feasible" if the upper end of the two-sided 90% interval is at most τ, "infeasible" if the lower end is above τ, else "undetermined"; the same bound holds everywhere, REQ-16's screen included; no non-inferiority test runs against each arm's comparator. | lead | FOCUS:80; CONS:429 | REQ-16, REQ-21 (e), (h); DRAFT §6.3 |
| LW-07 | τ_L is read against a0 (PLAN-S:124); ℓ̄(m) − ℓ̄(R) is reported beside every removal arm; if R itself fails τ_L, the text says the 600-row dose costs more task loss than τ_L; the comparator option is rejected as outcome-dependent. | lead | FOCUS:80; CONS:438 | REQ-16, REQ-21 (e); DRAFT §6.6 |
| LW-08 | REQ-21 (m) carries one blinding text built from every draft's list: ADD §3 (4)'s Gate B values, the per-writer table, the six reused cells, each choice made after values, the R arms' task-loss differences seen by some writers, L3 and the labels named after the seal, T1 kept and T2 not met, and DRAFT §12.2–§12.4. | lead | FOCUS:80; CONS:447 | REQ-21 (m); DRAFT §12 |
| LW-09 | An arm that fails the arm-pooled coherence screen keeps its tested label and its place in the family and carries the flag "fails answers end" (or "comparator fails answers end"); the flag is not a fifth word. | lead | FOCUS:80; CONS:464 | REQ-21 (c); DRAFT §3.7, §4.5 |
| LW-10 | The plant fixes are adopted: F2 (text-only scorers' planted ranks are construction checks, published before the pilot), F4 (the dilution decomposition), F5 (Λ per planted row), F6 (the relocation replay), F7 (a scored-only refusal decoy), F8 (publish F2 even if the pilot stops), R8.3 (the prediction "the classifier ranks the planted leaf first at M = 128"), R8.5 (no He-style plant; the wording "PKU red-team prompts with PKU-safe, non-refusing answers"), N6, and the seed-paired pilot interval. | lead | FOCUS:80; CONS:474 | REQ-8, REQ-29, `labels.json`, REQ-21 (g), (j); DRAFT §8.2, §8.5, §8.6 |
| LW-11 | On planted menus the row AUC (plant rows against Dolly rows, bootstrap 90% interval) is the primary placement statistic and the top-k hit is secondary; the content classifier is a named diagnostic placed by its measured cost (this edits ADD L15 (7)). | lead | FOCUS:80; CONS:492 | REQ-18, REQ-21 (j), (k); DRAFT §7.2 (stale), §7.4 |
| LW-12 | REQ-17 gains three noise inputs: AMD A7 (a shared seed shift plus an arm shift, ρ grid {0, 0.67}, a 2 × SD sensitivity), B-CK11 N4 (cell heterogeneity on planted menus), and O's noise (the prompt-clustered SE 3.98–4.22 pp at 100 prompts, scaled to 500 prompts if O-ext runs, and the U–O correlation). | lead | FOCUS:80; CONS:500 | REQ-17 settings, REQ-21 (k), (m); DRAFT §7.4 |
| LW-13 | REQ-16's screen takes O's and L's SE from the HB form (prompt part included), with LW-06's bound (this edits ADD L16's scope sentence). | lead | FOCUS:80; CONS:511 | REQ-16; DRAFT §7.4 |
| LW-14 | REQ-18's predictions are scored per unit by proper scoring rules (Brier, log, regret in its predictive interval), labelled "a consistency check with one menu"; Llama's predictions use wave-1 quantities only; the pick rule is checked against Llama's seed map; the truth and the noise mismatch are stated. | lead | FOCUS:80; CONS:519 | REQ-18, REQ-21 (j); DRAFT §4.6 item 5 |
| LW-15 | C-lean holds training, 200 harm prompts × 1 sample, the task-loss pass, and the greedy over-refusal answers with their guard (c0 ≈ 870 s ≈ 0.30 FRE, E: REF §C.5), recorded as the reading of PLAN-S:202 together with PLAN-S:127. | lead | FOCUS:80; CONS:527 | REQ-17, REQ-18, REQ-21 (h), (k); DRAFT §7.3, §10.3 |
| LW-16 | 1 FRE = 2,934 s (the median job slot of the three wave-0a R arms; about $1.46), fixed at W1-P and never re-estimated; C-full's stage list as REF LQ26; lean prices frozen at W1-P; c0 = one real job (cold start, full R-arm training, exactly the C-lean evaluation); the unit is 1 FRE under C-full and c0 under C-lean. | lead | FOCUS:80; CONS:536 | REQ-17, REQ-18, REQ-21 (k); DRAFT §10.2–§10.3 |
| LW-17 | ADD §5 item 1's token-axis analysis counts as "a token-matched analysis beside the row-matched one" for PAPER decision 26, and the cost section's "compute-matched" sentence agrees with it. | lead | FOCUS:80; CONS:549 | REQ-27, REQ-21 (a), (h); DRAFT §9.3 |
| LW-18 | REQ-12 (DataShield-style) and REQ-13 (Self-Inf-N-style) are built before wave 1 (ambitious); fallback: post-Gate-B exploratory, recorded in REQ-21 (l), if either is not committed at W1. | lead (ambitious, by the user's push-usage instruction) | FOCUS:80; CONS:557 | REQ-12, REQ-13, REQ-20, REQ-21 (l) |
| LW-19 | Every candidate addition's outcome-free rule text enters the W1 record as a conditional item ("runs only after the user's yes and a funding event"), none holds wave 1 except REQ-23, PLAN-S:239's reading goes into REQ-21 (h), and each label is appended with its code. | lead | FOCUS:80; CONS:565 | REQ-20, REQ-21 (g), (h), (j), (l); DRAFT §9.5 |
| LW-20 | REQ-23 writes per-row normalized Unsafe scores for the 4,800 rows and the 75 plant rows by read-only use of `GuardScorer.label_scores`; its run (about $1, E: RB R8.1) is paid from stage 1's funding event, never from the Gate B balance. | lead | FOCUS:80; CONS:573 | REQ-23; DRAFT §8.5 |
| LW-21 | A1 stays as built (REQ-21 (h) records why); V1 (Adam-preconditioned, from stored values) is a Part G report, never an arm; V2a (a0-1101's own sampled answers as the harmful side) has the pre-set reading "Jaccard below 1/3 with A1's top 600 makes the claim bound mandatory and V2a the first secondary arm if funded". | lead | FOCUS:80; CONS:581 | REQ-25, REQ-21 (h); DRAFT §9.2 |
| LW-22 | T1 is committed without a plant change (done, `9525005`); the decoy labels are appended before any plant draw; ADD §4 item 8's scope note goes in the commit message. | lead | FOCUS:80, :81; CONS:589 | T1 bundle; `labels.json` |
| LW-23 | HarmBench rules: HB-1 (Gate B's pipeline byte for byte, with the 512-token classifier clip), HB-2 (per-arm clipped share, the 35-prompt subset beside all 200, κ with Qwen3Guard per bank, greedy beside sampled), HB-3 (the claim rule gates on all 200 prompts). | lead | FOCUS:80; CONS:597 | REQ-21 (f); B16; DRAFT §2.2 |
| LW-24 | Report-only endpoint rule texts are fixed: SRJ (secondary; last-512-token truncation; runs only after US-13), the prefill probe (conditional), in-domain refusal (conditional), selectivity and partial refusals (report only), "Controversial counted Unsafe" (a sensitivity corner), and the length-reweighted U labelled a decomposition. | lead | FOCUS:80; CONS:605 | REQ-21 (e), (f); DRAFT §2.4, §9.4 |
| LW-25 | SR's and S6's construction details enter as conditional rule text (RB R4.4); REQ-6 records each S-pool row's PKU line and companion index, text-free; REQ-7 tests that S6's copies differ only in their ids. | lead | FOCUS:80; CONS:619 | REQ-6, REQ-7, REQ-24 (S1), REQ-21 (h) |
| LW-26 | The W1 record carries Q-P1 (B+Qi's erosion lies nearer recipe B's), ADD §4 item 8's scope note, REQ-21 (h)'s readings, and the word "pre-specified", not "pre-registered", until REQ-20 and REQ-21 are committed. | lead | FOCUS:80; CONS:627 | REQ-21 (h), (i); PAPER wording |
| LW-27 | Engine round Y is built in its own workspace (after the W1 record) and frozen by hash before any merge. | lead | FOCUS:80; CONS:635 | engine round Y; T4 |
| LW-28 | B10–B17 go to a builder with tests and a review before use (Specialized builds Y; B12 and B17 move into Y; the lead's read-only workflow verifies). | lead | FOCUS:80; CONS:643 | S1 build briefs |
| LW-29 | Model-agnostic Part C scripts come later as new files with a 1B parity test; the 1B scripts named in REQ-21 stay unchanged. | lead | FOCUS:80; CONS:651 | REQ-3, REQ-9–REQ-13 (scope) |
| LW-30 | A one-paragraph human-label-check commitment goes into REQ-21 before wave 1, with the full protocol before block A; it adopts no spend. | lead | FOCUS:80; CONS:659 | REQ-21; CONS LA-07 |
| LW-31 | Plan-B seeds: A1, H1, S1 and S4 at 1102–1110; under D1, R at 1101–1110 (draws d = 9–10 by `gate-b-random-removal-v1`, d at seed 1100 + d); a0 outside the pool; three-member families; the familywise equivalence grade at α/3 per side (96.67%). | lead | FOCUS:80; CONS:667 | REQ-4, REQ-21 (d); DRAFT §1.3 |
| LW-32 | If Gate B's extension runs R_4 and R_5 (same sealed edits, same seeds, engine X), stage 1 reuses them as R at 1104–1105, and REQ-21 (m) lists them. | lead | FOCUS:80; CONS:675 | REQ-21 (d), (m); DRAFT §1.2 |
| LW-33 | Under S-a (now a sensitivity), O's feasibility variance is V = s²_pool,O/J_m + max(0, MS_P − MS_E)/(P·J_m) with Satterthwaite df. | lead | FOCUS:80; CONS:683 | B16; DRAFT §6.4 |
| LW-34 | REQ-21's record keeps the name `research/experiments/2026-10-16-stage1-commitments.md`, and its header gives the real `date -u` time. | lead | FOCUS:80; CONS:691 | REQ-21 |
| LW-35 | Block A's U, HB, O, task-loss and coherence outputs stay sealed by SHA-256 until block B is complete or a recorded decision ends stage 1 without it; the block-B funding decision uses no block-A outcome; block-A-only labels say "block A only (3 seeds per method arm)". | lead | FOCUS:80; CONS:697 | REQ-21 (h); DRAFT §1.3, §11 |

### 1.5 The lead's addendum, §1 to §9

| Id | Decision (one sentence) | Who decided | Source | Binds |
|---|---|---|---|---|
| ADD-1.1 | The builder launches no agent; the lead may build Parts E and F with its own workflow agents in hand-made workspaces. | lead | ADD:11 | build process |
| ADD-1.2 | The lead makes the build workspace from the working branch `stageb-costs-and-recovery-safeguards-20261003`, never from `main`. | lead | ADD:12 | build process |
| ADD-1.3 | Every item L1–L16 is "confirm with edit", as ADD §2 writes it. | lead | ADD:13 | REQ-1–REQ-21 |
| ADD-L1 | One builder session builds everything, the T1 bundle first (REQ-2, REQ-14's A1 and generic removal paths, REQ-14's settings, the complete `labels.json`, REQ-8's plant settings with L12, a golden A1 test), then read-only; REQ-12 and REQ-13 last; nobody reads `rows.jsonl` before the T1 commit. | lead | ADD:17–39 | T1; REQ-2, REQ-8, REQ-12–REQ-14 |
| ADD-L2 | The four paths and the task id 20261016 stay; the workspace is a `git archive` of the working branch with a manifest; acceptance is against the workspace baseline. | lead | ADD:41–52 | REQ-20, REQ-21 |
| ADD-L3 | L1 and S3 read the end-of-turn position (len − 1, read (a)); every other (index, read) cell is report-only and post-Gate-B exploratory if analysed; REQ-3 refuses a scored row whose `input_ids[len − 1]` is not the end-of-turn id. | lead | ADD:54–59 | REQ-3, REQ-10, REQ-11, REQ-21 (g), (h), (m) |
| ADD-L4 | Index 0 = embedding output, 1–15 = raw output of block i − 1, 16 = `model.norm` of block 15's output; a deviation line covers L1 at l_s = 15, S3's index-16 term and DataShield-style at l = 16; the pass refuses unless transformers is 4.56.2. | lead | ADD:61–73 | REQ-3, REQ-10–REQ-12, REQ-21 (h) |
| ADD-L5 | R_1200 (150 rows per unit) and R_2400 (300 per unit) are new, non-nested streams with draws d = 2–4 at seed 1100 + d; R+S1 combines R_d with S1's add rows. | lead | ADD:75–83 | REQ-4, REQ-21 (g); DRAFT §9.1 |
| ADD-L6 | H2a = at least 2 list-item lines, or at least 1 markup or fence line, by three frozen patterns, with known misses and false positives recorded. | lead | ADD:85–106 | REQ-5, REQ-21 (h) |
| ADD-L7 | All eight octile controls are built now, exactly category-matched, a shortfall filled from the same category inside the octile; H1, H2b and the octiles come from one length order. | lead | ADD:108–122 | REQ-5; DRAFT §9.1 item 6 |
| ADD-L8 | The S-pool candidate is a PKU response with `is_safe` true and LEX class REFUSAL-OPENING, in a record whose other response is unsafe; two report-only id counts are printed. | lead | ADD:124–133 | REQ-6, REQ-21 (g) |
| ADD-L9 | The near-duplicate check covers every split's evaluation forms (ANCH precedent), counts only, run by the lead; the form count must be 11,954; it is the one scoped exception to "never open `selector.jsonl`, `hidden/`". | lead | ADD:135–148 | REQ-6, REQ-21 |
| ADD-L10 | The S1–S3 overlap is allowed and both overlaps are counted; S1's rows outside the S3 subset are also processed for the SAS report. | lead | ADD:150–155 | REQ-6, REQ-9, REQ-11 |
| ADD-L11 | The S4 list holds 512 prompts in 32-prompt chunks with an exact stop at the 48th kept answer; fewer than 48 gives counts only and a non-zero exit; prompts that `encode_generation_prompt` refuses are excluded. | lead | ADD:157–171 | REQ-6, REQ-9 |
| ADD-L12 | The plant's near-duplicate grouping is built at $0 (single-linkage at Jaccard ≥ 0.5 within a unit), oversize components (> 37 rows) are singletons, cells close by cumulative targets, and cell sizes other than 150 and 37–38 are a recorded deviation. | lead | ADD:173–201 | REQ-8, REQ-21 (i) |
| ADD-L13 | One registry `scripts/stage1/labels.json` holds every label (pattern, duplicate refusal, one accessor, a scan test); it is append-only after T1. | lead | ADD:203–228 | REQ-2, every label, REQ-21 (m) |
| ADD-L14 | Caps: S3 512 new tokens, S4 and SD-600 2,048; `max_train_tokens` is read from recipe S; S3 keeps every answer; S4 has its keep predicate; SD-600 removes rows it cannot rewrite and never truncates. | lead | ADD:230–241 | REQ-9, REQ-11, REQ-15 |
| ADD-L15 | The selector criterion is the largest E[G(pick)] with ties to the simpler rule, B ∈ {2, 4, 8, 16}, noise 2.65 and 3.85 pp (never σ̂_gate), keep in every menu, costs in c0 units under both conventions, common random numbers, c\* = the first crossing, fixed quality grids, and placement fixed now. | lead | ADD:243–285 | REQ-16–REQ-18, REQ-21 (j), (k) |
| ADD-L16 | τ_L = 2√2 × s from the three Gate A a0 seeds (ddof 1, e1, 200 task rows), never re-estimated; only the threshold is frozen; the 2-df risk is recorded. | lead | ADD:287–293 | REQ-19, REQ-21 (e) |
| ADD-3.1 | The eight L8 octile arms follow Gate B's frozen wave rule (12–16 octile runs plus 2 controls). | lead | ADD:297 | REQ-21 (g); DRAFT §9.1 item 6 |
| ADD-3.2 | Every plant main-sweep arm runs at seeds 1101–1103, paired with a0_plant at the same seed; the 1101 rule does not apply to them. | lead | ADD:298 | DRAFT §8.3 |
| ADD-3.3 | R600 and R150 on the planted data are fresh draws per seed (d = 1–3) by Gate B's per-unit rule, with labels `stage1-plant-r600-v1` and `stage1-plant-r150-v1`. | lead | ADD:299 | REQ-8; `labels.json` |
| ADD-3.4 | REQ-6 excludes prompts refused under `max_prompt_tokens` and prints N after each filter (stop if N < 1,000); the plant's same-unit rank is reported; FOCUS is cited by entry title; REQ-21 (m) lists every Gate B value seen (T2 cannot be met). | lead | ADD:300 | REQ-6, REQ-29, REQ-21 (m) |
| ADD-3.5 | The builder reports at three hand-over points (T1; after Parts B–F; after Part G) with text-free notes. | lead | ADD:301 | process |
| ADD-4.1 | Labels pin option (A): each settings file records digests of the label entries it uses, so an append does not change edit bytes. | lead | ADD:307 | REQ-2; every settings file |
| ADD-4.2 | `plant.r600` and `plant.r150` take parts (d, g) and `plant.r150_units` takes (d) (6 × 19 + 2 × 18 = 150), recorded as readings confirmed after the seal. | lead | ADD:308 | REQ-8, REQ-21 (g), (h), (m) |
| ADD-4.3 | The plant leaf rule has one text in both files, and after each placement only the current cell can close. | lead | ADD:309 | REQ-8 |
| ADD-4.4 | A1's refusal tests follow the critic's list. | lead | ADD:310 | REQ-14 tests |
| ADD-4.5 | `build_plant.json` and `write_score_edit.json` are pinned by literal SHA-256, and REQ-8 loads its settings with that literal. | lead | ADD:311 | REQ-8, REQ-14 |
| ADD-4.6 | The mutation runner strips plugin variables, counts a run with a different test count as invalid, and records the tree, engine, pytest version and target hashes. | lead | ADD:312 | every mutation test |
| ADD-4.7 | `strict_json` refuses non-finite floats, and `provenance()` records the Python and numpy versions. | lead | ADD:313 | REQ-2 |
| ADD-4.8 | The golden test and the A1 contract are defined on engine X; after engine round Y they need a new pin. | lead | ADD:314 | REQ-14, REQ-21; LW-26 |
| ADD-5.1 | Every removal and add arm reports its target and total row tokens and token-mass share, and one report-only secondary analysis places each removal filter on the random dose curve along a token axis (its "no new arm" is replaced by ADD-6.5). | lead | ADD:320 | REQ-27, REQ-21 (b), (f) |
| ADD-5.2 | One-shot scoring stability (q-only against e1-only) is a report-only Part G report, and the paper names one-shot scoring as a limit; it ran (FO-04). | lead | ADD:321 | REQ-25 |
| ADD-5.3 | Two report-only add-ons are defined: θ0's refusal on each evaluation prompt as a stratifier (ran, FO-06) and θ0's per-token loss on the 48 added rows in REQ-9's pass; the safety-direction share is not pre-registered. | lead | ADD:322 | REQ-28, REQ-9 |
| ADD-5.4 | The candidate new references (the opening hold; Safety at One Shot) are a user scope decision, with no change until the user decides. | lead (defers to user) | ADD:323 | DRAFT §5.1; CONS US-06 |
| ADD-5.5 | The premise risk (seed variation beating corpus edits) supports the design and changes nothing. | lead | ADD:324 | — |
| ADD-6.1 | REQ-16, REQ-17, REQ-19 and REQ-21 (c) use HB-C primary (REML per-arm variances, a crossed prompt part, Satterthwaite df), with HB, S-a and S-aW as sensitivities, and REQ-17 simulates the primary model's noise with the 2.65/3.85 pp inputs. | lead (from UW-02, LW-01) | ADD:330 | REQ-16, REQ-17, REQ-19, REQ-21 (c) |
| ADD-6.2 | Seeds are layout D1: a0 and R at 1101–1107 (R_1108 not run), method arms at 1102–1107. | lead (from UW-03) | ADD:331 | REQ-4, REQ-21 (d) |
| ADD-6.3 | The family is Φ (24 nodes), the label order is UW-08 (a), "worse" follows R1.3 for O and task loss, the τ_O grid {2, 5, 10} is reported, and τ_L is read against a0 with ℓ̄(m) − ℓ̄(R) reported. | lead (from UW-04–UW-08, LW-07) | ADD:332 | REQ-16, REQ-21 (b) |
| ADD-6.4 | REQ-19's $0 MDE check decides O-ext; when it fires, the primary O bank is the dev 100 plus 400 harmless PHTest prompts; the lead downloads and seals the file; builders take it by hash; fallback F; never the hidden remainder. | lead (from UW-07a, UW-07b) | ADD:333 | REQ-6, REQ-19, REQ-21 (e) |
| ADD-6.5 | W1-03's token-matched random-removal builder R_tok for A1, L1 and H1 is built now as a 3-seed secondary arm in the funded tier, with appended labels; the token-axis analysis is built in any case and is the fallback. | lead (from UW-14) | ADD:334 | REQ-4, REQ-30, REQ-21 (a), (b) |
| ADD-6.6 | REQ-12, REQ-13 and REQ-23 are all built before wave 1; a late REQ-12 or REQ-13 is recorded as post-Gate-B exploratory; REQ-23 has no such exception. | lead (from LW-18, LW-20, UW-18) | ADD:335 | REQ-12, REQ-13, REQ-23, REQ-21 (l) |
| ADD-6.7 | F9's two more plant locations go into a new settings file (never T1's `build_plant.json`) with appended labels, as conditional rule text for a funded stage 1b; there is no benign-topic plant. | lead (from UW-20, UW-16) | ADD:336 | REQ-8, REQ-21 (i) |
| ADD-6.8 | The W1 record carries the δ_fam rule, headline item (2)'s new wording, the Llama Gate B-lite rules pinned by SHA-256, OLMo-2-1B's confirmatory status, the four accepted deviations, and the blinding line. | lead (from UW-13, UW-15, UW-19, UW-21, UW-11, LW-08) | ADD:337 | REQ-21 (a), (b), (i), (m) |
| ADD-7.1 | O-ext candidates are the 2,077 PHTest rows labelled "harmless"; the 1,192 "controversial" rows are never used. | lead | ADD:342 | REQ-6 batch (`build_oext.py`) |
| ADD-7.2 | Exclusions, each counted: exact duplicates; near duplicates (character 5-gram Jaccard ≥ P's `max_jaccard`) of any bank of P (all splits, the lead's run), of the 128 anchors, of the S-pool and of the plant rows; empty prompts; prompts that `encode_generation_prompt` refuses. | lead | ADD:343 | `build_oext.py`; ADD-L9 |
| ADD-7.3 | The O-ext bank is the first 400 eligible ids in the sealed order `stage1-oext-phtest-v1`; fewer than 400 eligible stops with counts only. | lead | ADD:344 | `build_oext.py`; `labels.json` |
| ADD-7.4 | The 400-row text file stays under `tmp/`; a text-free sealed record is committed; the primary O bank is judged under ADD-9's cap; per-source reports keep the two sources apart. | lead | ADD:345 | REQ-6, REQ-21 (e) |
| ADD-7.5 | A new `scripts/stage1/build_oext.py` with synthetic tests joins REQ-6's batch, and the lead runs it on the real files. | lead | ADD:346 | REQ-6 |
| ADD-8.1 | Risk 44: stage 1b also reports A1's planted-cell rank under a disjoint-source anchor set (64 harmful plus 64 safe, not PKU-Alignment data, by Gate C's anchor rule), with the source chosen and sealed before S1 and before any planted run; the PKU-anchor rank stays the counted one; fallback: §6 of the paper states the shared source as a limit; the W1 record carries the rule. | user-delegated lead | ADD:350 | REQ-8, REQ-21 (i); DRAFT §8 |
| ADD-8.2 | Self-Inf-N-style joins the list of planted-cell ranks that count toward "finds a known cause"; if REQ-13 is not committed at W1, only A1 counts. | user-delegated lead | ADD:351 | REQ-29, REQ-21 (g), (j); DRAFT §8.4 (stale) |
| ADD-9 | One answer cap applies to the whole 500-prompt primary O bank for θ0, a0 and every arm: 128 new tokens if W1-18's truncation check passes its bar, else the full generation cap; θ0 and a0 are re-evaluated on the 500 under that cap; Gate B's G4 does not change; the W1-18 result and the cap are recorded in FOCUS before the W1 record. | user-delegated lead | ADD:355; FOCUS:74 | REQ-6, REQ-9, REQ-19, REQ-21 (e); DRAFT §2.2, §6.5 |

### 1.6 Lead rulings made in messages, 17 Oct

Binding. Not all are in FOCUS yet.

| Id | Decision (one sentence) | Who decided | Source | Binds |
|---|---|---|---|---|
| MSG-01 | Ruling B-1: the selector's frozen rule is chosen per (menu, M, B), as REQ-17, DRAFT §7.2 and L15 (6) say; the per-convention reading is a reported sensitivity (built: `criterion.freeze_scope` = "menu_m_b", M: SET `selector_simulate.json`). | lead | lead message, 17 Oct; FOCUS:75 | REQ-17, REQ-18, REQ-21 (k); DRAFT §7.2 |
| MSG-02 | REQ-19's "f" is the fraction of the dev over-refusal bank used for the planning SE, and f = 1 means all 100 dev prompts, each with its greedy answer, with seeds as replicates; L15 (4)'s keys take the part (replicate) with a fixed-shape array indexed by (option, seed index, φ, ψ); the decoy uses three labels (`stage1-plant-decoy-rows-v1`, `-unit-v1`, `-leaf-v1`). | lead | lead message, 17 Oct; FOCUS:81 (02:42 UTC entry) | REQ-19 settings `f` (M: SET `limits_check.json`), REQ-17, `labels.json` (W1-09), REQ-21 (h) |
| MSG-03 | W1-08 (1): the plant and decoy pools are pinned in a separate hash-pinned pool-pins file that REQ-3 loads; REQ-3's settings pin does not change. **[LEAD, under delegation]** | lead | lead message, 17 Oct | REQ-3, REQ-29 (W1-08), W1-09 |
| MSG-04 | The primary dose axis is total row tokens (prompt plus target, as trained), and target tokens are reported beside it. **[LEAD, under delegation]** (fills EXTR W1-02 item 4's [LEAD] axis reading) | lead | lead message, 17 Oct | REQ-27 (b), REQ-30 (R_tok matches on this axis), REQ-21 (h); DRAFT §9.3 |
| MSG-05 | Under D1, a0 and R each run at seeds 1101–1107 (7 each; R_1108 is not run), and the six method arms run at 1102–1107. | user (UW-03), restated by the lead | lead message, 17 Oct; FOCUS:79; ADD:331 | REQ-4, REQ-21 (d) |
| MSG-06 | Only the training-signal diagnostics (A1, Self-Inf-N-style) count toward "finds a known cause"; the text-only scorers (L1, H1, H2a/b, DataShield-style, the classifier) are construction checks published before the pilot, because they read only row text and θ0; if REQ-13 misses W1, only A1 counts. | lead (restates LW-10 F2 and ADD-8.2 with its reason) | lead message, 17 Oct; ADD:351 | REQ-29, REQ-21 (g), (j); DRAFT §8.4, §8.5 |
| MSG-07 | An arm that fails the coherence screen is read and flagged "fails answers end"; the flag is not a "worse" word. | lead (restates LW-09) | lead message, 17 Oct | REQ-21 (c); DRAFT §3.7 |
| MSG-08 | Under R1.3, "worse (O)" needs an arm proven infeasible at τ_O\* = 5 pp AND significantly above its comparator; an arm above its comparator but "feasible" or "undetermined" is not "worse (O)": its O shift is reported, and its label comes from the U part. **[LEAD, under delegation]** (fills the "feasible or undetermined" case) | user-delegated lead | lead message, 17 Oct | REQ-21 (c); B16; DRAFT §4.4–§4.5 |
| MSG-09 | A significant difference below δ is printed in the row as "significant, below the smallest effect of interest", not as a label. | lead (restates UW-08's row note) | lead message, 17 Oct | REQ-21 (c); DRAFT §4.5 |
| MSG-10 | One answer cap for the whole 500-prompt primary O bank (dev 100 + 400 PHTest): 128 new tokens if W1-18's truncation check passes, else the full cap; θ0 and a0 are re-evaluated on the 500; Gate B's G4 is unchanged; W1-18 is running now, so the record writes both branches. | user-delegated lead (restates ADD-9) | lead message, 17 Oct; ADD:355 | REQ-6, REQ-9, REQ-19, REQ-21 (e); DRAFT §2.2, §6.5 |
| MSG-11 | Risk 44: a disjoint-source anchor sensitivity for the planted control; the source must be chosen and sealed before the freeze. | user-delegated lead (restates ADD-8.1) | lead message, 17 Oct; ADD:350 | REQ-8, REQ-21 (i) |
| MSG-12 | OLMo 3 7B Instruct is added as a third 7–8B model if funded, not as a replacement; the cut order is 70B, 32B, OLMo 3 7B. | user (FR-24), restated by the lead | lead message, 17 Oct; FOCUS:78 | 7–8B pre-registration; DRAFT §14.3 |
| MSG-13 | Known accepted limit: the `--compare` name of `report_a1_variants.py` may end in one newline. | lead | lead message, 17 Oct | REQ-25 (W1-04) |

**Counts (M (here), by `grep`).** FR 25, FO 7, UW 22 (UW-07 is two rows), LW 35, ADD 53, MSG 13: **155 rows.**

---

## 2. The audit's contradictions, and what each decision implies

AUDIT §3 (:165–:192) lists contradictions between DRAFT revision 2, ADD and PAPER. DRAFT revision 2 (committed 01:55 UTC on 17 Oct) predates UW-01–UW-21, LW-01–LW-35 and ADD §6–§9 (R: AUDIT:31). So most of DRAFT's "in force" texts are now stale. §2.1 treats the nine contradictions that the brief names. §2.2 treats the audit's other rows. §2.3 adds contradictions that I found while I built this ledger.

### 2.1 The nine named contradictions

**C-1. Seeds D0 against D1, and the block layout under D1** (AUDIT:170)
- *Conflict.* DRAFT §1.2 and §1.3 print D0 (R 1101–1108, a0 1101–1106; block A: a0 at 1104, R to 1105; block B: a0 at 1105–1106, R to 1108). PAPER Table 1 prints 7 and 7.
- *What the decisions settle.* UW-03, ADD-6.2 and MSG-05: a0 and R at 1101–1107, R_1108 not run, method arms at 1102–1107. DRAFT §1.2–§1.3 must be rewritten to this.
- *What is left.* No source gives the block layout under D1 (R: AUDIT:209). **[LEAD-NEEDED]**
- *Recommended resolution (I).* Make each block seed-complete for all eight primary arms.
  - **Block A:** the six method arms at 1102–1104, plus a0_1104 and R_1104 (a0 and R at 1101–1103 already exist as reused units). 20 new runs, or 19 if Gate B's extension made R_4 and LW-32 reuses it (M (here): 18 + 1 + 1).
  - **Block B:** all eight arms at 1105–1107. 24 new runs, or 23 if R_5 is reused (M (here): 18 + 3 + 3).
  - Total 44 new runs, the same as D0's 21 + 23 (M (here)). Without reuse, block A has 1 run fewer than D0's 21 (PLAN-S:222, $25–45) and block B 1 run more than D0's 23 (PLAN-S:223, $31–53); with R_4 and R_5 reused the counts equal D0's (19 and 23). 1 run ≈ 1 FRE ≈ $1.46 (M (here): 2,934 s × $1.79/h).
  - *Why.* Under HB-C every contrast uses seed-matched pairs. D0's R_1105 in block A has no method partner in block A. With seed-complete blocks, LW-35's "block A only" analysis has 3 full seed pairs for every P1–P6 contrast.
  - *Fallback.* Keep D0's counts per block (R_1105 in block A, block B with R at 1106–1107). It changes no total.
- *Plan B under D1* (LW-31 gives R only). **[LEAD-NEEDED]**, recommended (I): a0 stays at 1101–1107; R at 1101–1110 (d = 9–10); the plan-B arms add seeds 1108–1110 in a third block on its own funding event.

**C-2. The over-refusal answer cap** (AUDIT:172–:174)
- *Conflict.* PAPER C.11 says only the PHTest answers are capped at 128 tokens. ADD §9 caps all 500 prompts for θ0, a0 and every arm, with a full-cap fallback. FOCUS:74 (11:04 UTC) records that W1-18 could not run on the Mac.
- *What the decisions settle.* ADD-9 and MSG-10. One cap for the whole 500-prompt bank. 128 new tokens if W1-18 passes its bar (every one of the 11 units: at least 97 of 100 flags agree and the refused count moves by at most 2; R: SET `limits_overrefusal_checks.json`), else the full generation cap for all 500, with the 128-token cut as a report-only sensitivity (FOCUS:74). θ0 and a0 are re-evaluated on the 500. G4 stays on the dev 100 at the Gate A cap. τ_O\* = 5 pp is "the same number as G4, on another bank and cap" (AUDIT:174).
- *Both branches for the W1 record (I).*
  - **Branch 128 (W1-18 passes).** All 500 answers capped at 128 new tokens. O-ext cost about $10–27 (E: RB R5b.2 via CONS:243).
  - **Branch full (W1-18 fails, or has no result when the W1 record is committed).** All 500 at the full cap. About $40–70 (E: same source). The 128-token cut is reported only.
- *Status.* FOCUS:74 says "blocked". The lead's message says W1-18 is running now. The W1-18 status file says status "running", stage "load_guard", updated 12:44:35 UTC (M: `.ai/inputs/stage1-commitments-20261016/w1-18-judge-ledger/status.json`, keys only). No result is recorded yet. See X-6 for one record item.
- *What is left.* PAPER C.11 must state both branches and that the dev-100 answers are capped too. Two gaps that ADD §9 does not cover are in §2.3 (X-5, X-7).

**C-3. δ_fam at 7–8B** (AUDIT:175)
- *Conflict.* UW-13 fixes δ_fam = 5 × E_fam / 45.11 "for other families". PAPER §4.8's Llama replication rule has no δ_fam. P78 §6 option H (a) and CONS LA-10 propose a 10 pp SESOI branch at 7–8B (P78:237). DRAFT §4.2 still prints the silent 5 pp default.
- *What the decisions settle.* UW-13 binds for "other families". DRAFT §4.2's silent default is stale.
- *What is left.* Whether a 7–8B model (OLMo-2-7B, Llama-3.1-8B, OLMo 3 7B) counts as "another family". **[LEAD-NEEDED]**
- *Recommended resolution (I).* Read "family" as "every model other than OLMo-2-1B, at any size". Each model's δ_fam comes from its own Gate A mean E and is fixed before its comparison runs; 5 pp absolute is printed beside it. Reason: the rule's basis (δ = 11.1% of E; M: AMD NUM) does not depend on size. For OLMo-2-7B this gives about 4.9 pp (E: AUDIT:175, from the side project's mean E of about 44.1 pp). The 10 pp branch (P78 decision H (a) or (c)) changes D5 = (a)'s SESOI at 7–8B, so it stays the user's decision in the 7–8B Part 1 pre-registration (P78:243). If the user takes it, δ_fam is reported beside it. PAPER §4.8's replication rule gets δ_fam. Cost $0.

**C-4. R1.3's "infeasible" per comparison against Φ's intersection–union node** (AUDIT:176–:177)
- *Conflict.* PAPER C.11 and DRAFT §4.4 read R1.3's "infeasible" as the per-comparison state of LW-06 (the lower end of the two-sided 90% interval above τ_O\*, a one-sided 5% test). AMD §B.3 puts R1.3 inside Φ as an intersection–union test (IUT): O_k's null is "O(m) − O(c) ≤ 0 or O(m) − O(θ0) ≤ τ_O\*", and its p-value is the larger of the two one-sided p-values, tested at the node's current Φ level (0.042% at the start, 0.135% after U_k, 0.323% after U_k and F_k; M: AMD NUM, AMD:269–:276). The two readings give different false "worse (O)" rates. Also, AMD §B.2 has two F_k rows (standard; and "under R1.3, F_k → L_k 1"), and no source says which is in force (R: AUDIT:208).
- *What the decisions settle (partly).* UW-04 adopts Φ "with the passing rules of AMD §B.2", and UW-05 adopts R1.3; AMD §B.3 is the only text that puts R1.3 inside Φ. MSG-08 fixes the necessary conditions: proven infeasible at 5 pp AND significantly above the comparator; "feasible" or "undetermined" is never "worse (O)".
- *What is left.* The test level of the θ0 part. Both readings fit UW-05's words ("O-infeasible at τ_O\*") and its cited source (CONS:224 cites AMD §B.3), so the choice is a reading for REQ-21 (h), not a change of UW-05. **[LEAD-NEEDED]**
- *Recommended resolution (I).*
  1. O_k and L_k are AMD §B.3's IUTs, tested at the node's Φ level. Reason: it is the only form whose false "worse (O)" and "worse (L)" rate Φ controls at 5%. An IUT rejection at a level of at most 5% one-sided implies the per-comparison state "infeasible" (the same one-sided test at a stricter level, same model and SE; I), so MSG-08's condition always holds.
  2. The per-comparison state (feasible, infeasible, undetermined) is printed in the feasibility part of the row and is never the label test. An arm that is "infeasible" per comparison and above its comparator, but whose IUT does not reject at its Φ level, prints both facts and no "worse (O)" word; its label comes from the U part (MSG-08).
  3. Φ's F_k edge is AMD §B.2's R1.3 row: F_k → L_k with weight 1 (a rejected F_k makes O_k's IUT almost impossible, so weight sent to O_k is wasted; row sums stay 1). **[LEAD, under delegation]**
  4. Copy AMD §B.2's edges and §B.3's nulls verbatim into the frozen text. Change PAPER C.11's sentence to say that the label test is Φ's IUT and that the printed state is descriptive.
- *Fallback.* The per-comparison reading (θ0 part at one-sided 5%, comparator part at the node's level). The record then states that the θ0 part of "worse (O)" is not Φ-controlled. Cost $0 either way.

**C-5. R_tok** (AUDIT:189)
- *Conflict.* DRAFT §9.3 item 1 ("in force: no new arm") and EXTR W1-03 ("Build now: nothing") against ADD §6 item 5, UW-14 and PAPER §3.2 and C.3.
- *What the decisions settle.* UW-14 and ADD-6.5: build W1-03's R_tok builder for A1, L1 and H1 now (labels appended), a 3-seed secondary arm in the funded tier (stage 1c), draws d = 2–4 at seeds 1102–1104 (EXTR W1-03, ADD-L5's secondary-arm rule), about $13.1, $15.5 with pod overhead, $19.3 × 1.25 (E: EXTR W1-03). The token-axis analysis (W1-02) is built in any case and is the fallback. MSG-04 fixes the axis: R_tok matches each filter's removed total row tokens; target tokens are reported beside.
- *What is left.* Only building it. No R_tok builder is at HEAD (M: `ls scripts/stage1` shows none). If it is not committed at W1, a later R_tok is post-Gate-B exploratory (EXTR W1-03). A1's set is sealed, so A1's token mass is known now (FO-03; A1 removes 15.5% of the target-token mass for 12.5% of the rows), and the token axis matters for A1, not only for H1 (AUDIT:85).

**C-6. The disjoint-anchor source** (AUDIT:190)
- *Conflict.* ADD §8 item 1 and PAPER C.5 and §6 require a disjoint-source anchor set chosen and sealed before S1 and before any planted run. No source is chosen (R: AUDIT:207). PAPER C.5 says the set is built "by Gate C's anchor rule"; that rule used PKU-SafeRLHF's severity and category labels, which a non-PKU source may lack (I; UNVERIFIED in AUDIT).
- *What the decisions settle.* ADD-8.1 and MSG-11: the rule, the deadline (before the freeze and before any planted run), the counted rank (PKU anchors), the fallback (a limit sentence), and that the W1 record carries the rule text.
- *What is left.* The source. **[LEAD-NEEDED]**
- *Recommended resolution (I).* The lead names the source and its revision pin in the W1 record (ambitious: before W1, so the sensitivity is fully pre-specified beside the plant), chosen by these criteria, written down first:
  1. not PKU-Alignment data;
  2. not in OLMo-2-1B's own post-training mix (a check to make, UNVERIFIED for any candidate);
  3. a harm label per response and a category label per prompt, so that Gate C's severity and category-balance steps can run, or a stated substitute rule if one label is missing;
  4. a licence that allows research use;
  5. the engine's near-duplicate check against every bank of P, the 128 PKU anchors, the S-pool, the plant rows and the O-ext bank, counts only.
  The download needs the user's yes (the delegation does not cover downloads; FOCUS:74 precedent). Cost: an anchor job of about $0.40 (E: FOCUS:67, the Gate C anchor entry of 8 Oct) plus a second A1 scoring pass of about $0–7 (E: AUDIT:190, UNVERIFIED). Funding block: stage 1b. Fallback: ADD-8.1's limit sentence.

**C-7. DRAFT §14.3's OLMo 3 replacement** (AUDIT:191)
- *Conflict.* DRAFT §14.3 (RB U-14) has the lead recommending option (b), OLMo 3 instead of OLMo-2-7B; CONS LA-04 has the ladder (a), then (b), then (d).
- *What the decisions settle.* FR-24 and MSG-12 (the user, 17 Oct): OLMo 3 7B Instruct is a third 7–8B model if funded, not a replacement; OLMo-2-7B and Llama-3.1-8B stay; the cut order is 70B, 32B, OLMo 3 7B. DRAFT §14.3's U-14 text and CONS LA-04 are superseded; the freeze text marks them so. OLMo-2-1B stays the stage-1 model (RB R9.1). No stage-1 change.
- *What is left.* PAPER §6 says "Olmo 3 the first model cut"; it must say "the first 7–8B model cut" (AUDIT:191). $0.

**C-8. FRE and the lean-cost definitions** (AUDIT:187)
- *Conflict.* PAPER §4.7 and C.6 define FRE as "the median time of its random-removal arms" and lean as "training plus one sample per harm prompt". LW-16 fixes 1 FRE = 2,934 s from the three wave-0a R arms at W1-P, never re-estimated; LW-15 (a) adds the task-loss pass and the greedy over-refusal answers to C-lean (c0 ≈ 0.30 FRE).
- *What the decisions settle.* LW-15 and LW-16 bind. PAPER C.6 must say: "1 FRE = the median job slot of the three wave-0a R arms (2,934 s), fixed before the predictions and never re-estimated; the median of all stage-1 R arms is reported beside it". REQ-21 (h) records LW-16 as the reading of PLAN-S:201 ("the median measured time of that family's R arms") for the W1-P predictions, and LW-15 as the reading of PLAN-S:202 with PLAN-S:127.
- *What is left.* Whether C-lean holds the dev 100 or the full 500-prompt O bank after O-ext. Not found in any source (R: AUDIT:210). The built settings hold the dev 100 (C-lean (a): "the 100 greedy over-refusal answers (362 s)"; M: SET `selector_spec.json`). **[LEAD-NEEDED]**
- *Recommended resolution (I).* C-lean holds the full 500-prompt primary O bank under ADD-9's cap. Reasons: LW-15 puts into C-lean "the 100 greedy over-refusal answers that the selector's screen needs" (CONS:527), written before O-ext fired, so its reason now points to the bank the screen uses; LW-12 scales the screen's O noise to 500 prompts because O-ext ran; a lean trial that screens on 100 prompts would mark an arm at θ0's level "undetermined" at τ_O = 5 (LW-06's correction: the bound adds about 6.6–6.9 pp at 100 prompts; M: CONS:429). The measured c0 job (CONS LS-15) then measures it. The predictions are curves in c_d/c0, so their shape does not depend on c0; only the placement of a result does (U3 (a)). E (here, I): at the full cap, 400 more greedy answers at about 3.6 s each (1,694 s / 468 prompts; R: DRAFT §10.2) add about 1,450 s, so c0 would be about 2,300 s ≈ 0.8 FRE; at the 128 cap, much less (UNVERIFIED: PHTest answer lengths are unmeasured). *Fallback:* the dev 100 in C-lean, with the screen's O SE at 100 prompts, stated as a limit of the lean convention.

**C-9. Actors: two against five** (AUDIT:188)
- *Conflict.* PAPER §3.1 and Table 1 name two actors (customer C with data, learning rate and epochs; provider P). DRAFT §9.4 and CONS LS-17 (a lead item, S1) propose five actors, each menu fixed before any newly run stage-1 cell's outcome. CONS LA-02 keeps the paper's wording a user (author) decision, later.
- *What the decisions settle.* None. LS-17 is not among the decided LW items.
- *What is left.* **[LEAD-NEEDED]**
- *Recommended resolution (I).* Adopt LS-17 (a) in the W1 record (ambitious: the menus are then fixed before any Gate B wave-1 outcome, not only before stage-1 outcomes): five actors (a closed-service customer with data only; one with hyperparameter control; the service provider; an open-weights developer; the dataset publisher), each with its menu, and DRAFT §4.8's "too close to call" rule text at W1 (S-2). The paper keeps C and P in the body as a coarsening (C = the two customer actors; P = the provider and the open-weights developer; the publisher's transfer test is CONS LA-05, later), with the five in Appendix C until LA-02 is decided. **[LEAD, under delegation]** for the pre-registration part; the paper wording stays LA-02. Cost $0. *Fallback:* the two-actor menus of PAPER Table 1, fixed in the W1 record.

### 2.2 The audit's other rows

| Audit row | Topic | Resolution implied by the decisions | Status |
|---|---|---|---|
| 0 (:169) | The frozen text is stale | Top fix 1 (§3): DRAFT revision 3 or the REQ-21 record, built from this ledger. | [LEAD-NEEDED] (top fix 1) |
| 1b (:171) | B+Qi seeds | CONS LS-11 is open (1101–1106 or 1102–1107). Under HB-C, 1102–1107 gives 6 pairs with every method arm (AMD §D.1). | [LEAD-NEEDED]; recommend 1102–1107, and the same for B↓LR if added. $0 (same 6 runs). |
| 2b (:173) | The O bank | UW-07a, FO-05, ADD-6.4 and ADD §7: dev 100 + 400 PHTest. DRAFT §2.2 and §6.5 are stale. | Settled |
| 2c (:174) | τ_O\* "the same bar as G4" | ADD-9, MSG-10: the same number (5 pp), on another bank and cap; G4 unchanged; θ0's level is re-measured on the 500 bank (17/100 holds for the dev 100 only). | Settled |
| 4b (:177) | Φ's F_k edge | See C-4 item 3. | [LEAD-NEEDED] (recommended: the R1.3 row) |
| 4c (:178) | Testing order | DRAFT §4.6 / AMD §B.6 give 1, 1b (dominance), 1c (P7–P8), 2–5; PAPER §4.9 lists five families. 1b follows top fix 2; 1c follows top fix 4. | [LEAD-NEEDED] (top fixes 2, 4) |
| 4d (:179) | What the labels resolve | LW-02 adopts the "better" 80% effect beside each MDE (5.65–8.52 pp under HB; R: DRAFT §3.5). PAPER §6's "about 5 pp" must become the planning range. | Settled (paper edit) |
| 4e (:180) | "Pre-registered" | LW-26: "pre-specified" until REQ-20 and REQ-21 are committed; "pre-registered" only after a deposit (top fix 1). | Settled (paper edit) |
| 4f (:181) | Placement statistic | LW-11 (b): row AUC primary; top-k hit secondary; the classifier named. DRAFT §7.2 is stale. | Settled (but see X-1 for the built settings) |
| 5a (:182) | "Dominates" | Top fix 2: adopt DRAFT §5.3 / AMD §D.1–§D.4 as W1 rule text. | [LEAD-NEEDED] (top fix 2) |
| 5b (:183) | Reference seeds | Top fix 2 (CONS US-01). | [LEAD-NEEDED] (top fix 2) |
| 5c (:184) | Safe LoRA settings | CONS LS-07 (S1): DRAFT §5.4's table (K = 39). The base-model download (5.94 GB) needs the user's yes (CONS US-04). | [LEAD-NEEDED] at S1, before any Safe LoRA outcome; recommend LS-07 as drafted |
| 5d (:185) | The lower-LR reference | Top fix 4 (CONS US-11). | [LEAD-NEEDED] (top fix 4) |
| 5e (:186) | Timing of S1 rules (DRAFT "New points" N-1) | No record says which act approves the W1 rules. | [LEAD-NEEDED]; recommend (I): the W1 rules are approved by the lead's W1 commit (REQ-20 manifest + REQ-21 record) under FR-23, before any Gate B wave-1 unit outcome; rules written later carry DRAFT §12.4's label "fixed after Gate B wave 1"; REQ-21 (h) records the reading; PAPER §4.9 is reworded to match. $0. |
| 10 (:192) | Other stale text | DRAFT §8.4's counting list → ADD-8.2 and MSG-06. §8.5 F1 → UW-15. §4.2 → UW-13. §9.1 item 3 → LW-18. PAPER §4.5 and C.5 "nested cells [TO BE FINALISED]" → ADD-L12 and FO-02. PAPER §4.2 and C.3 [TO BE FIXED] → LW-19, LW-24, LW-25 (conditional texts). PAPER C.7 "noise from pooled residuals" → ADD-L15 (fixed SDs), LW-12, LW-13. | Settled, except PAPER §4.6 "about 10–12 pp" against C.1 "about 9, 10 or 12 pp" (kept by rev 6h ruling 6): [LEAD-NEEDED], minor; recommend "about 10 pp at central planning noise (9–12 pp)" (AUDIT:57). |

### 2.3 Contradictions and gaps found while building this ledger (not in the audit)

| Id | Conflict | Evidence | Resolution |
|---|---|---|---|
| X-1 | LW-12 adopts AMD A7 (ρ grid {0, 0.67}), but the built REQ-17 settings keep ρ grid {0} with A7 behind a switch, and `rho_average_for_rule` false. | M: SET `selector_simulate.json` (`rho_mode` "default", `rho_grids.default` [0.0], `a7_switch` [0.0, 0.67]); FOCUS:75 (built after the 07:21 decisions). | **[LEAD-NEEDED]** before REQ-18's predictions freeze (W1-P). Recommended: set `rho_mode` to the A7 grid, as LW-12 decided. Then fix DRAFT §7.4 sub-question (i): ambitious, choose the rule and k on an equal-weight average over ρ ∈ {0, 0.67} (the rule then does not depend on an unknown coupling, in the spirit of ADD-L15 (1)); fallback, choose at ρ = 0 (L15 (1) as written) with the ρ = 0.67 predictions reported. REQ-21 (m) lists A7 as proposed after the noise gate. $0. |
| X-2 | LW-13 adopts the HB-form SE in REQ-16's screen, but the built screen keeps `se_form` "pooled_residuals", and the L item SD is 0 "until the lead enters it if the HB form is adopted". | M: SET `selector_spec.json` (`screen.se_form`, `screen.l_item_sd_nats` 0.0 and its note). | **[LEAD-NEEDED]** before W1-P. Recommended: set `se_form` to "hb" and enter the L item SD from the Gate A a0 task-row tables (Gate A data, $0, Mac). Fallback: keep L16's pooled residuals and record that LW-13 is not applied. |
| X-3 | O-ext fired, but the built selector inputs are dev-100 values: `o_prompt_sd_pp` 4.1 at 100 prompts, `o_theta0_pp` 17.0, and C-lean's 100 greedy answers. LW-12 says O's noise is "scaled to 500 prompts if O-ext runs". | M: SET `selector_spec.json` (`screen.o_prompt_sd_pp`, `limits.o_theta0_pp`, `cost_conventions.C-lean`). | **[LEAD-NEEDED]** before W1-P. Recommended (I): planning values for the 500 bank = the dev-100 values with the prompt SD scaled by √(100/500) (E), labelled planning values; θ0's measured level on the 500 never enters the frozen predictions. C-lean as in C-8. |
| X-4 | The built pick rule's note says "Seeds are not paired (PLAN-S:102, the model in force)", but UW-02 replaced PLAN-S:102 for the study's analysis. | M: SET `selector_spec.json` (`pick.rule`). | **[LEAD-NEEDED]**, minor. Recommended: keep the unpaired pick (it models a practitioner's selection rule, which need not follow the study's analysis model) and correct the note's reason in REQ-21 (h). $0. |
| X-5 | ADD §9 re-evaluates θ0 and a0 on the 500 bank, but the reused R units are comparators of P1–P3 too: R_1102 and R_1103 enter the HB-C contrasts, and R_1101 enters the S-a sensitivity and R's reported mean. They have O on the dev 100 at the Gate A cap only. The same holds for R_4 and R_5 if LW-32 reuses them. So "every O contrast compares answers made under one rule" fails for P1–P3 at 1102–1103. | R: ADD:355; LW-01; LW-32; DRAFT §1.2 (R_1–R_3 are Gate B's wave-0a units, reused). | **[LEAD-NEEDED]**. Recommended (I): regenerate the R_1101–R_1103 adapters (and R_4, R_5 if reused) by a deterministic train-only re-run, accepted only if each e1 adapter fingerprint equals the wave-0a unit's (DRAFT §1.5's rule for a0), then run an O-only evaluation on the 500 under ADD-9's cap; U stays as read. The outputs fall under LW-35's block-A seal. Another route: pull the states from the kept stopped pod `attribution-gateb-w0a-1` (FOCUS:85), which needs a pod start and the user's go. E (here): about 0.1 FRE regeneration plus an O-only pass per unit, so a few dollars for 3 units (UNVERIFIED: PHTest answer lengths), paid from block A. Fallback: P1–P3's O contrasts on the 400 PHTest prompts use only seeds 1104–1107, and the record says so. |
| X-6 | FOCUS:74 records that W1-18 cannot run on the Mac without the pinned judge weights (8.82 GB) and that the download needs the user's yes, which the lead did not have. The lead's 17 Oct message and the W1-18 status file say W1-18 is running (stage "load_guard" at 12:44:35 UTC). | R: FOCUS:74; M: the status file (keys only). | Not a rule conflict. **[LEAD-NEEDED]**, record item: FOCUS records how the judge weights came to the Mac (the user's yes, with its words, or another route) before W1-18's result selects the cap. If no record exists, ADD §9's full-cap branch applies (FOCUS:74). |
| X-7 | W1-18 checks the 128-token cut on the dev-100 answers of 11 OLMo-2-1B units only, but ADD §9 applies the cut to the 400 PHTest prompts too. That the dev-100 result transfers to PHTest is an assumption. | R: SET `limits_overrefusal_checks.json` (`units_source`: Gate A and development units; dev bank only); ADD:355. | **[LEAD-NEEDED]**, optional. Recommended (I, ambitious): under branch 128, θ0's own re-evaluation on the 400 PHTest prompts is made once at the full cap and judged both full and cut, by W1-18's bar, as a pre-set report; if θ0 fails the bar, the paper states the cut as a limit for PHTest (the cap rule does not switch after any arm outcome). E (here): about 400 × 3.6 s ≈ 24 min ≈ $0.7 (UNVERIFIED lengths), block A. Fallback: state the transfer as an assumption. |

---

## 3. Rulings needed on the audit's top-5 fixes

**Money in hand (R unless marked).** Balance $91.94 at 16 Oct 19:07 UTC (FOCUS:85). Gate B wave 1 needs $83.91 of it (FOCUS:86). Slack $8.03 (M (here)); idle storage costs about $1.10 a day (E: FOCUS:86), so about $7 by the end of 17 Oct (E (here)). No grant is awarded (FOCUS:83, :99). **So every spending item below is pre-registered as conditional on the funding event of the block named, never as spent.** Which money counts as a funding event is the user's open item FR-15 (CONS US-07). Proposed definition for the user's return (I): a named top-up or grant payment that the account balance shows, read before each block's launch, net of the wave-1 reserve and of every earlier block's need.

**Funding blocks used here** (E: PLAN-S:220–:228 unless marked): no block ($0, rule text only); **block A** ($25–45); **block B** ($31–53; it holds the references); **stage 1b** (planted sweep, $17–35); **stage 1c** (secondary arms, up to $45–80); **rater budget** (CONS LA-07, $440–650 for two paid raters; a possible source is BlueDot's $800 human-audit line, not money in hand, R: FOCUS:99); **7–8B tier** (new money $680–1,660, E: AUDIT:63, REPLAN §6).

Each ruling has a $0 part (rule text in the W1 record, due at W1 because a rule written after Gate B outcomes carries DRAFT §12.4's label) and a spending part (conditional). Under FR-23 the lead can say yes to scope now; that yes comes before any newly run stage-1 cell's outcome is read, which is the timing RB R0.1 requires. The user may reverse it on return before that point.

| Fix | Ruling needed | Ambitious default | Cost (E) | Funding block | Fallback (and its trigger) |
|---|---|---|---|---|---|
| **1. One consistent frozen text** (AUDIT:108) | Build DRAFT revision 3 or the REQ-21 record from this ledger; set the word "pre-registered" by a deposit rule. | (a) DRAFT revision 3 = the REQ-21 W1 record: every [USER] and [LEAD] proposal replaced by its decided value, citing the ledger ids; AMD §B.2's edges and §B.3's nulls copied verbatim with C-4's resolution; ADD §7–§9 with both cap branches; PAPER's stale markers removed. (b) An anonymized, timestamped public deposit (OSF or AsPredicted) with the hashes, as soon as the user says yes. | $0 | none | The deposit is a public post, so it waits for the user's yes (CONS LA-12; FR-23 does not cover publishing). Until then: LW-26's "pre-specified", and the git commit with the REQ-20 manifest is the dated record. |
| **2. A confirmatory test of "data repair against the references"** (AUDIT:118) | Adopt the "beats" rule and family 1b as W1 rule text (CONS LS-06 (a)), and choose the reference seeds (CONS US-01). | Rule (W1, $0): "m beats r" if the upper ends of the two-sided 90% intervals lie below 0 for U(m) − U(r), below m_O = 5 pp for O(m) − O(r), and below τ_L for L(m) − L(r); the adapter-scaling curve read at λ\*_m matched on task loss (λ\*_m = 1 if L̂(m) − L̂(a0) ≤ τ_L; U tested at λ_lo, O at λ_hi); D_k = beats every built reference (an IUT); family 1b = Holm over D_1–D_6 at 5%, read after Φ; PAPER §3.2's undefined sentence replaced. Seeds: US-01 (a): the safety prefix, scaling and Safe LoRA on all seven a0 seeds (1101–1107 under D1), λ = 0.9 added, recipe G and B+Qi at 1102–1107. | Rule $0. US-01 (a) about $42–46 (M: AMD NUM via CONS:709), plus $9.2–10.1 under D1 (M (here): $7.5–8.3 + $1.7–1.8), so about $51–56. The cheapest useful part (the prefix, scaling and Safe LoRA on all seven a0 seeds) about $30–33 (E: AUDIT:126). | block B | US-01 (b), the approved 3-seed references (a0 1101–1103; recipe G at 3 seeds): "beats" is reported descriptively (AMD §D.6). Trigger: block B's funding event does not cover the increment. Safe LoRA at any seed count also needs the user's yes to the base-model download (5.94 GB; CONS US-04). |
| **3. Measurement that reaches harm, and a real judge audit** (AUDIT:128) | Write LW-30's paragraph as a design; add the claim rule's missing cases; take US-12, US-13 and US-14 at their ambitious defaults. | Rule (W1, $0): two raters who did not design the study, blind to arm and judge label; strata a0, removals, additions; about 130 judge-Unsafe and about 150 judge-Safe answers per stratum (MRA W6 sizes); κ; a misclassification-corrected contrast as a sensitivity; report only. The claim rule adds the HarmBench contrast's 90% interval and says "restored refusal" for "equivalent" and "inconclusive" contrasts. Runs: SRJ (US-13), the prefill headroom check and then the full scope (US-14), in-domain refusal (US-12). PAPER §4.2's [TO BE FIXED] becomes "secondary, report-only". | SRJ $2–4 on planned judge pods; prefill $1.1–1.6, then $26–39 full or $9–14 reduced; in-domain refusal $5–13 (E: CONS:800–:823). Endpoints in all: about $34–58 full or $17–33 reduced (M (here)). Raters: Part 1 $25–50; Part 2 $440–650 for two paid raters (E: CONS:1103). | blocks A and B (the endpoints run on stage-1 units); rater budget (Part 2) | Endpoints: the conditional rule texts only (LW-19, LW-24), each unrun endpoint stated as a limitation; prefill reduced scope if money is short; no headroom → reported once as a limitation (pre-set reading). SRJ also needs the user's yes to the Gemma terms and a 5.1 GB download (CONS US-13). Raters: Part 1 with a volunteer at $0, or the 9 Oct single-rater blind read stated as the limit. |
| **4. Robustness of the menu** (AUDIT:137) | Take US-11 (B↓LR), US-10 (SR and S6) and US-06 (no change, with a reason); fix the actor menus (C-9). | B↓LR at 6 seeds (1102–1107), read on the matched-task-loss frontier (AMD-4). SR and S6 at 48 rows and 6 seeds in family 1c (P7 = SR − S4, P8 = S6 − S4; Holm over two; a separate fit, so P1–P6 and their MDE do not change). US-06: no new reference, with the written reason (B+Qi already covers the first-token-objective class; the one-shot patch acts after fine-tuning). The five-actor menus in the W1 record (C-9). | B↓LR $12–14; SR and S6 about $12–14 each; about $36–42 in all (E: CONS:783–:799). Menus and US-06 $0. | block B (B↓LR, a reference); blocks A and B, 3 seeds each (SR, S6) | B↓LR at 3 seeds, $6–7, if money is short. SR and S6 by RB R4.3's pre-set fallbacks: money short → S6 only; SR's engine field not verified at S1 → SR as a 3-seed secondary arm; plan B → P7 and P8 do not run; S4 cannot fill 48 rows → SR on S1's rows. The B↓LR config is added by an explicit-path commit after Gate B's last kit pod (RB R3.5). |
| **5. A1's one-shot selection and its claim bound** (AUDIT:146) | Adopt the $0 claim rule now; pre-register a report-only re-score; take US-16 (V2a). | Rule (W1, $0): P1 is stated as conditional on one sealed selection (FO-03); in every claim A1 is "a bi-anchored gradient-similarity filter (external harmful anchors)" (RB R7.2, moved from Later to the freeze). Report only: A1's bi-anchored cosine re-scored on a0 retrains at seeds 1102 and 1103 (checkpoints q and e1), with top-600 Jaccard and Kendall τ against the sealed set; it never changes the arm. V2a's scored-only pass (US-16), read by LW-21's pre-set rule. | Re-score about $12–15, or $15–19 × 1.25 (E: AUDIT:152, from w0b-2's 0.077 h retrain and 3.04 h scoring at $1.79/h); V2a $5.6–7.1 (E: CONS:832). | block A (its diagnostics line) | The $0 claim sentence and FO-04's existing stability figures (ρ 0.771; Jaccard 0.434; V1 0.314) as the stated limit. Trigger: block A's funding event does not cover the re-score. |

**Sum of the spending parts of fixes 2–4 (M (here), from the E figures above):** about $104–156, plus rater time, all conditional on funding events. AUDIT:199 gives $105–155.

---

## 4. [LEAD-NEEDED] list

Each item has a recommended resolution in §2 or §3. None changes a frozen rule, D5 = (a) or a user decision.

| Id | Item | Recommended resolution | Where |
|---|---|---|---|
| LN-01 | D1 block layout | Seed-complete blocks: A = all 8 arms at 1102–1104 (20 new runs, 19 with R_4 reused); B = all 8 at 1105–1107 (24, 23 with R_5 reused) | C-1 |
| LN-02 | Plan B under D1 | a0 1101–1107; R 1101–1110; plan-B arms add 1108–1110 in a third block | C-1 |
| LN-03 | B+Qi and B↓LR seeds (CONS LS-11) | 1102–1107 | §2.2 row 1b |
| LN-04 | δ_fam scope | Every model other than OLMo-2-1B, at any size, from its own Gate A mean E; the 7–8B 10 pp branch stays the user's | C-3 |
| LN-05 | R1.3 test form and Φ's F_k edge | AMD §B.3's IUT at the node's Φ level; the per-comparison state printed; F_k → L_k 1 | C-4 |
| LN-06 | The disjoint-anchor source | Criteria first, then the named source pinned in the W1 record; the download needs the user's yes | C-6 |
| LN-07 | C-lean's O part after O-ext | The full 500-prompt bank under ADD-9's cap | C-8 |
| LN-08 | Actor menus | CONS LS-17 (a) in the W1 record; the paper keeps C and P as a coarsening | C-9 |
| LN-09 | Which act approves the W1 rules | The lead's W1 commit under FR-23; later rules carry DRAFT §12.4's label | §2.2 row 5e |
| LN-10 | Selector switches against LW-12 and LW-13 | A7 ρ grid; ρ-averaged rule (fallback ρ = 0); HB-form screen SE with the L item SD; O planning values at 500 | X-1–X-3 |
| LN-11 | The pick rule's stale note | Keep the unpaired pick; fix the reason | X-4 |
| LN-12 | The reused R comparators on the 500 bank | Fingerprint-checked regeneration, then an O-only pass; fallback: PHTest O contrasts at 1104–1107 only | X-5 |
| LN-13 | W1-18's provenance | FOCUS records how the judge weights reached the Mac before the result picks the cap | X-6 |
| LN-14 | PHTest truncation transfer | θ0 once at the full cap on the 400, judged full and cut, report only | X-7 |
| LN-15 | Top fixes 1–5 | As §3 | §3 |
| LN-16 | The funding-event definition (the user's FR-15) | Propose: a named top-up or grant payment in the balance, net of the wave-1 reserve and earlier blocks | §3 |
| LN-17 | PAPER §4.6 against C.1 wording | "About 10 pp at central planning noise (9–12 pp)" | §2.2 row 10 |
| LN-18 | Safe LoRA settings (CONS LS-07, S1) | As drafted in DRAFT §5.4, before any Safe LoRA outcome | §2.2 row 5c |

---

## 5. Where the ledger lands in REQ-20 and REQ-21

| Record part | Ledger rows that bind it |
|---|---|
| REQ-21 (a) question and headline | FR-03, FR-05, FR-22, UW-14, UW-15, UW-21, LW-17, ADD-6.5, ADD-6.8 |
| REQ-21 (b) family, margin, order | FR-04, UW-02, UW-04, UW-13, LW-01, LW-02, ADD-5.1, ADD-6.1, ADD-6.3; C-3, C-4; top fix 2 (family 1b) |
| REQ-21 (c) labels | FR-19, UW-05, UW-08, LW-02, LW-09, ADD-6.3, MSG-07, MSG-08, MSG-09; C-4 |
| REQ-21 (d) seeds and blocks | FR-06, UW-03, LW-31, LW-32, ADD-6.2, MSG-05; C-1 |
| REQ-21 (e) limits | FR-09, FO-05, UW-06, UW-07a, UW-07b, UW-09, LW-03–LW-07, LW-24, ADD-L16, ADD-6.4, ADD §7, ADD-9, MSG-10; C-2, X-5, X-7 |
| REQ-21 (f) judge rule | FR-08, LW-23, LW-24, ADD-5.1 |
| REQ-21 (g) arm rules and files | FO-03, UW-10, UW-14, LW-10, LW-19, ADD-L3, ADD-L5, ADD-L8, ADD-3.1, ADD-4.2, ADD-8.2, MSG-06; C-5 |
| REQ-21 (h) readings and deviations | LW-04, LW-06, LW-15, LW-16, LW-17, LW-21, LW-25, LW-26, LW-35, ADD-L3, ADD-L4, ADD-L6, ADD-4.2, MSG-02, MSG-04; C-8, LN-09, X-4 |
| REQ-21 (i) deviations the user saw | UW-11, UW-20, ADD-L12, ADD-6.7, ADD-8.1, MSG-11; C-6 |
| REQ-21 (j) predictions | UW-19, LW-10 (R8.3), LW-11, LW-14, ADD-L15, ADD-8.2 |
| REQ-21 (k) selector | FR-05, FR-11, LW-11, LW-12, LW-15, LW-16, ADD-L15, MSG-01; X-1–X-4 |
| REQ-21 (l) not built | FR-14, LW-18, LW-19, ADD-6.6; UW-07b (REQ-26) |
| REQ-21 (m) blinding line | FO-01, LW-08, LW-32, ADD-L3, ADD-L13, ADD-3.4, ADD-4.2; X-1 (A7 after the noise gate). This ledger's writer read FOCUS's 16–17 Oct entries in full (so every Gate B value that FOCUS:86 and :91 print), the wave-0a cost figures and the Gate A a0 U and O values in SET `selector_*.json`, and FO-05 and FO-06's summary numbers; it read no Gate B arm's O, task loss or answer, and no sealed score as a number |
| REQ-20 manifest | FR-13, UW-18, LW-18, LW-19, ADD-L2, ADD-6.6; the conditional flag for UW-20, ADD-8.1 and the top-fix rule texts |

---

## 6. Process record

- **Commands run (all exit 0).** `date -u` (13:15, 13:31 UTC); `git log`, `git status`, `git rev-parse HEAD` (3536776) on the main checkout; `shasum -a 256` on the sources and the S1OUT records; `grep`, `sed`, `wc`, `ls` on the sources; `python3 -I` one-liners that printed only the keys, numbers and rule strings of `scripts/stage1/settings/{selector_simulate,selector_spec,limits_check,limits_overrefusal_checks}.json` and the keys of the W1-18 status file and ledger; `mkdir -p` of this folder.
- **Read in full:** ADD; BRIEF; CONS §0–§2 and the US, LS and LA items cited; DRAFT §0–§14; AUDIT; FOCUS:74–:91 (every 16–17 Oct entry); FOCUS:1–:73 and the cited older entries in part; AMD §A.6, §B, §C.3, §E.4–§E.5. **Read in part:** EXTR (W1-01–W1-03, W1-08, W1-09, W1-18, W1-19, §5); P78 (by search); PLAN-S (cited lines); PREREG:150; PAPER (by search). **Not read:** REF and RB in full (cited through CONS and DRAFT), the check notes, the mock reviews.
- **Not opened:** `selector.jsonl`, `hidden/`, any held-out file, any `rows.jsonl` or `groups.json`, any file with row, prompt, answer or anchor text.
- **Limits.** I did not re-run any simulation or check any code path; the X-rows rest on settings strings, not on the code. Line numbers are at the hashes above; FOCUS changes often, so the record should cite FOCUS entries by title and time (ADD-3.4). The costs are the sources' estimates; where I did arithmetic it says "M (here)" or "E (here)".
