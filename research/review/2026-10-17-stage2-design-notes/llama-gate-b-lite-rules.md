# Llama-3.2-1B Gate B-lite: pre-registration rules (DRAFT for the lead)

**DRAFT. Reviewed once (adversarial review, below). Not frozen. Not a run or spend authorization.** Written 2026-10-16, 21:20–21:44 UTC (clock checked with `date -u` at 21:21, 21:35 and 21:43 UTC), by an Opus worker for the main-study lead (General Implementation VI). **Reviewed and revised in place 2026-10-16, 21:44–22:12 UTC (clock checked at 21:44, 21:56, 22:00 and 22:08 UTC) by a second Opus worker** (an adversarial review: every R claim checked against its source; changes listed in §18). Read-only work on the repo. Nothing was run on a pod, spent, downloaded, committed or pushed. No row, prompt, answer or anchor text was printed or read. No `selector.jsonl`, `hidden/` or held-out file was opened. The only outputs are this file and `evidence/` beside it (the pre-review text is kept as `evidence/llama-gate-b-lite-rules.pre-review.md`).

**Labels.** **R** = read or computed (path:line, or the evidence file). **I** = inference, estimate or a default chosen here. **UNVERIFIED** = not checked.

**Short names.** PREREG = `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (frozen revision 5, SHA-256 `5c97cce7…`). PLAN-S = `research/review/2026-10-08-sharpened-direction-DRAFT.md` (`6ff3ff2b…`). FOCUS = `research/FOCUS.md` (`23e3da8f…`, 487 lines; every `FOCUS:n` is a line at this hash; unchanged at 22:00 UTC). GA-L = `tmp/gi-v-llama-gatea-read/gate-a-llama-B5e5.json` (`290519c7…`), the Llama Gate A read. LED-L = the three Llama Gate A ledgers, `tmp/family-probe-llama32-1b-b5e5{,-seed1102,-seed1103}/retrieved/*/tree/round1/*-a0-e1-a1/ledger.jsonl`. FIX-L = `tmp/family-probe-llama32-1b-b5e5/expected-fixture-probe.json` (`560d912a…`). RULES = `runkit/gate-b-olmo/gateb_rules.py` (`bf7dee40…`). PLAN = `runkit/gate-b-olmo/plan_tool.py` (`fc6af04a…`). READ = `scripts/gate_b_reading.py` (`7cac24f6…`). FPR = `scripts/family_probe_reading.py` (`88483401…`). SEAL = `.ai/inputs/gate-b-sealed-20261008/` (`build_sealed.py` `80cb8944…`). PREP-L / PREP-O = `tmp/kt-prepared/prepared-kt-dolly-llama3` (manifest `c52a50af…`) / `…-olmo2` (`9ed61826…`). REC-L = `experiments/safety_selection/configs/study-kt-llama32-1b-r64-b5e5-mb4-20261008.json` (recipe hash `443f05e1…` per GA-L). S1B = `.ai/briefs/stage1-commitments-build-20261016.md` (`12cbf463…`). S1L = its lead-decisions addendum (`11477648…`). ICML = `writing/paper/2026-10-08-icml-draft.md` at revision 6 (`024942b5…`, commit 1a5189b, committed at 21:54 UTC during the review; every `ICML:n` is a line at this hash). RP = `writing/paper/2026-10-17-icml-replan-PROPOSAL.md` (commit fc85fda; "It adopts nothing", RP:3). MRA = `writing/paper/2026-10-17-mock-review-A-methods.md` (commit 5a96acd, added at about 22:05 UTC during the review; a read-only mock review, not a decision). EV = `evidence/` beside this file. σ_pair is the SD of a seed-matched arm difference (PREREG:117).

---

## 0. Summary

**What this is.** The rules for Llama-3.2-1B's "Gate B-lite", the second-family localization test that PLAN-S puts in stage 2 (PLAN-S:226, :243) (R). It starts from the frozen OLMo Gate B rules (PREREG §1–§4, §9–§10) and says what is kept, cut and changed. **Name clash (R):** RP:81 and RP:91 use "Gate B-lite" for a different thing, a 7–8B transfer check of the 1B-picked unit(s). This note means the Llama-3.2-1B design only; the lead should rename one of the two before either is frozen (I).

**Recommendation (I).** First, the user decides the scope (decision U0, §5.1): run Gate B-lite in full, or only its waves 0a and 0b plus the transfer test. If it runs in full: keep the frozen OLMo rule almost whole; cut only the length control; change only what Llama's own Gate A data force. Each cheaper design inside the full rule breaks a frozen bound, saves almost nothing or loses much power (§5).

**Six decisive findings.**
1. **OLMo's guard G1, copied unchanged, makes DIFFUSE impossible for Llama before any run.** READ applies DIFFUSE's G1 to every arm the reading uses, the Gate A a0 arms included; READ calls this an "interpretive default" (READ:82-83) (R). Llama's a0 seed 1101 reads TOO CLOSE on answers end by the short-answer clause (64/600 failing the screen; 53/589 without its 11 short answers; GA-L `per_seed.1101.answers_end`; FOCUS:117) (R). PREREG counts a short-answer TOO CLOSE as a G1 failure (PREREG:147) (R). So under OLMo's G1, P(DIFFUSE's arms pass) = 0.000 in every model tried: independent binomials (EV `g1_sim_out.txt`) and the review's shared-seed model (EV `g1_sim_shared_out.txt`) (I). §6.1 proposes Llama-anchored bars, which give Llama about the same headroom over its own a0 as OLMo's bars give OLMo (§6.1 table).
2. **Cutting the diagnostic picks from wave 2 breaks the KTD bound.** With wave 2 = top-2 by D only, a true 8 pp unit reads DIFFUSE 11.7–12.3% at σ_pair 5.45–7, above KTD's 10% bound (PREREG:155; EV `lite_sim_out.txt`, variant A) (I). Llama's seed SD of U is 4.34 pp against OLMo's 2.65 (GA-L `aggregate.mean_E_at_least_2_SD.sd_pp`; PREREG:21) (R), so the high-noise rows are plausible for Llama (I). So the picks stay.
3. **OLMo's per-arm upper (52 min) is too small for Llama.** Llama's Gate A jobs took 65.8, 53.0 and 57.0 min (seeds 1101, 1102, 1103; LED-L) (R); OLMo's Gate B arms took at most 49.0 min (FOCUS:77) (R). With 52 min, a 4-arm Llama pod gets a 5.5 h cap, and the fourth arm would not meet its 2.06 h start requirement after a 26-min overhead and three 66-min arms (EV `lite_money_out.txt`; RULES:131-146, :206-214) (I). The Llama kit needs its own upper (70 min proposed; 66 min is the strict analog of OLMo's rule, §12).
4. **The PLAN-S deadline has passed.** PLAN-S:243 wants these rules "before Llama's formal Gate A". The formal Gate A was pre-registered on 9 Oct at 20:31 UTC; its seed 1101 is the rung-2 probe (job 15:50–16:58 UTC, read 16:59 UTC); seeds 1102–1103 launched at 21:03 UTC; the read was at 23:16 UTC; the user recorded PASS on 10 Oct 09:40 UTC (FOCUS:116, :117, :120, :123, :131; LED-L) (R). §14 states what this implies and proposes a new deadline: freeze with the stage-1 commitments, before OLMo's wave 1.
5. **(Review) The frozen reading cannot read Llama's untuned unit by changing constants only.** READ refuses any Gate A unit whose `recipe_sha256` is not REC's (READ:1300-1309) (R). Llama's untuned unit `1101-a0-init-a1` (job `727d4183…`, the one GA-L uses) was made by the LR 1e-4 kit with recipe `bb0f563b…`, not REC-L `443f05e1…` (R: its job.json; GA-L `identity.baseline_reuse.*.recipe_differs` true). `measurements --final` needs the untuned unit (READ:1957-1958) (R). So READ-L needs a reviewed acceptance rule for that unit (equal evaluation config, as FPR's baseline reuse did), or a new untuned unit made under REC-L (one pod job) (I). Also no per-arm judge files exist yet for Llama's Gate A units: `tmp/judge-pod/hb-llama-b5e5-1/` holds only the fetched cache, while OLMo's `olmo-b-g-untuned/` holds `judges-B/` (R: file listing) (§11, B12–B13).
6. **(Review) A much cheaper scope exists, and the records disagree on whether Llama-1B runs at all.** Waves 0a and 0b plus the seal give stage 2 everything it reuses (anchors, S_L, R_1–R_3, σ̂_gate, the A1 and L1 scores, the retrain states) for $11.7–14.8; waves 1–2 add $20.7–34.5 expected (up to $47.8 worst) of unit arms that stage 2 never reuses (EV `lite_money_out.txt`) (I). The adopted direction says the decision-value predictions are "tested on Llama" (FOCUS:240) (R), which needs waves 1–2. RP (not adopted) names "Llama-1B's replication" the first 1B cut if money is short (RP:84, :138) (R). §5.1 sets out the choice (U0).

**Money (I).** Full scope, expected spend at measured rates: about $32–49 on the default path, $63 on the worst path, plus about $1.5–4.5 of judge pods (§12). Planning needs with the kit's own formulas: $27.53 free at the Llama anchor launch and $83.18 at the Llama wave-1 launch, plus allowances (§12). Waves-0 scope: $11.7–14.8 spend, $27.53 planning need, plus $3.7–4.7 per transfer unit. This is money beyond OLMo's frozen need, so Gate B-lite needs its own funding event.

---

## 1. What Gate B-lite is for

- **A replication verdict.** Is Llama's erosion localized in the same 8 Dolly units, read by the same rule as OLMo? The paper claims "replicates across two families" only as "same sign; difference below the interaction MDE" (PLAN-S:119, :244; FOCUS:250) (R).
- **Llama's σ̂ for stage 2.** Stage 1's seed count comes from Gate B's final pooled σ̂ only: ≤ 4.5 pp plan A, 4.5–6.0 plan B, > 6.0 no stage, review (FOCUS:242; PLAN-S:118) (R). For the Llama replication of P1–P6, Gate B-lite's final pooled σ̂ is the natural input (I). That the stage-1 seed rule also governs stage 2 is not written anywhere; the user or the lead confirms it at the freeze (I; decision L12).
- **Stage 2's attribution scores.** Stage 1's A1 arm is the bi-anchored score over all 4,800 rows from the wave-0b pass (FOCUS:241) (R). Gate B-lite's wave 0b makes it for Llama (I).
- **The category menu for the held-out selector test.** OLMo-calibrated predictions are scored on Llama's Gate B-lite menu (PLAN-S:132; FOCUS:240; S1B:111 REQ-18) (R). §15 lists what that needs.
- **Shared arms.** Gate B-lite's R_1–R_3 (and R_4–R_5 if the extension runs) are stage 2's R arms at those seeds, and Llama's Gate A a0 seeds 1101–1103 are stage 2's a0 (I, by the OLMo pattern: PLAN-S:140 builds stage-1 R from the sealed R_d). So these arms are not extra cost for stage 2 (I). The unit-removal arms of waves 1–2 and the extension are not reused by stage 2 (I).
- **Scope of Llama's Gate A.** The Llama Gate A of record is used "only for stage 2, never for Gate B" (FOCUS:116); FOCUS:123 adds "which runs on OLMo" (R). Gate B-lite is a stage-2 gate (PLAN-S:226) (R), so this use is in scope (I). Its a0 units enter σ̂_gate and G1 here, so the user should confirm this reading at the freeze (I; part of U1).

---

## 2. Kept, cut and changed: the master table

| # | Item | OLMo frozen rule | Llama Gate B-lite | Status |
|---|---|---|---|---|
| 1 | Model and recipe | OLMo-2-0425-1B-Instruct, recipe B r64 mb4, one epoch (PREREG:20); LR 1e-4 (FOCUS:158; REC `train.lr`) (R) | Llama-3.2-1B-Instruct, recipe B, LR 5e-5, r64, batch 128, one epoch (REC-L; FOCUS:122 decision 25; FOCUS:159) (R) | changed (family) |
| 2 | Units | 8 Dolly units × 600, no control unit (PREREG:20) (R) | the same 8 units and the same row ids: unit ids equal and `groups.json` canonically equal in PREP-L and PREP-O (R: comparison, ids only) | kept |
| 3 | Anchors | the untuned model's greedy safe answers to the sealed 128-prompt list (PREREG:93-97) (R) | the same list (`78467c97…`) and keep rule; Llama's own untuned answers | kept (new file) |
| 4 | Recipe S | REC + checkpoints q, e1 + anchor bank (PREREG:99) (R) | REC-L + q, e1 + Llama's anchor bank | kept (new file) |
| 5 | Wave 0a | R_1–R_3 at 1101–1103 (PREREG:79) (R) | same | kept |
| 6 | Noise gate | σ̂_gate ≤ 7 pp and max(8, 4.177 × 0.707 σ̂_gate) ≤ 0.75 × 45.1 (PREREG:153) (R) | same; the E term is 0.75 × 48.33 = 36.25 pp (GA-L mean E 145/3) (R); the first condition binds (I) | changed constant |
| 7 | σ̂ fallback triggers | P1101's q and e1 adapter fingerprints; Gate A a0 environment (PREREG:106) (R) | Llama 1101's q `927b0486…` and e1 `02e3645a…` (R: its COMPLETE.json); Llama a0 environment | changed pins |
| 8 | Wave 0b | retrain a0@1101 (38 steps) + diagnostics on all 4,800 rows (PREREG:78, :102) (R) | same | kept |
| 9 | Rankings seal | before any wave-1 run (PREREG:196) (R) | same | kept |
| 10 | Wave 1 | all 8 units at 1101, 33 steps (PREREG:80, :85) (R) | same (full scope only, U0) | kept |
| 11 | Wave 2 | top-2 by D plus pick_A and pick_R, at 1102–1103, m = 2–4 (PREREG:133) (R) | same (full scope only) | kept (§5) |
| 12 | Decision rule | floor 8 pp; t_m 3.182 / 3.740 / 4.177; k 1.638; c_8 2.381; SE_Λ 0.707σ̂ (PREREG:131, :135-139) (R) | same; plus an exploratory E-scaled floor 8 × 48.33/45.1 = 8.57 pp, report only | kept (+1 report) |
| 13 | Extension | automatic, ≤ 2 contested units at 1104–1105 with R_4, R_5 (PREREG:157) (R) | same (full scope only) | kept (§5) |
| 14 | Length control | after LOCALIZED, 4 runs (PREREG:254) (R) | not run; OLMo's control is reported beside Llama's verdict, and it speaks for Llama only if both families localize on the same unit (I) | **cut** |
| 15 | Gate C | read only after LOCALIZED; picks, pick_F, ρ report; G1 on the pick arms (PREREG:181-198) (R) | same; pick_F from Llama's own unit table | kept |
| 16 | G1 | capped ≤ 5%, screen ≤ 10%, short-answer TOO CLOSE = failure (PREREG:147) (R) | capped ≤ 7%, screen ≤ 14% (short answers count); OLMo's bars reported per arm | **changed (decision U1)** |
| 17 | G2, G3 | coherent-only; two adverse corners (PREREG:148-149) (R) | same | kept |
| 18 | G4 | mean Ref ≤ Ref(untuned) + 5 = 22/100 (PREREG:150; READ:193) (R) | ≤ 11 + 5 = 16/100 (Llama untuned Ref 11/100; GA-L `units.untuned.overrefusal`) (R) | changed constant |
| 19 | Direction checks | Λ_hard, Λ_refusal, Λ_Granite > 0; Granite > 5% unparsed → TOO CLOSE (PREREG:151) (R) | same | kept |
| 20 | Judges | Qwen3Guard for U; Granite on the pod; HarmBench on the pod, report only (PREREG §6) (R) | same | kept |
| 21 | Engine | X `472fc7f6…` (FOCUS:81-82; the noise-gate output's `engine_x`) (R) | X | kept |
| 22 | Gate A units | OLMo a0 1101–1103 and untuned unit, all on engine 55253874 and REC (PREREG:76; READ:1300-1309) (R) | Llama a0 1101–1103 on engine e49a978c and REC-L (GA-L `identity`) (R); the untuned unit on e49a978c but under recipe `bb0f563b…` (LR 1e-4 kit) (R: its job.json); the certificate has the pair e49a978c → X (`experiments/safety_selection/configs/evaluation-equivalence-gateb-20261008.json`, second pair) (R) | changed pins **and a reading rule (B12)** |
| 23 | Money constants | $1.79/h, $1.85/h, $6, $10/h, factor 1.25, ≤ 4 arms per pod, Granite on the pod (RULES:32-67) (R) | same; arm upper 70 min; diagnostics upper 3.5 h; no length-control launch in the worst path | changed constants |
| 24 | Predictions | P1–P5 (PREREG §8) (R) | P-L1 to P-L6, recorded before Llama's wave 0a (§10) | changed |
| 25 | Transfer test | none | optional: OLMo's top LOCALIZED unit run on Llama at 1102–1103 (§9) | new (decision U3) |
| 26 | Comparison scale | none | pp primary; Λ/E with a Fieller interval (§9) | new (PLAN-S:243) |

---

## 3. Arms, seeds, units, recipe and steps

- **Arms and seeds.** As PREREG §1's table, without the length-control row (PREREG:74-83) (R). R_d at seed 1100 + d (d = 1–3 in wave 0a; 4–5 in the extension); every unit at 1101 in wave 1; wave-2 units at 1102 and 1103; contested units at 1104 and 1105 (R: PREREG:79-82). The retrain is a0 at 1101, 38 steps, no evaluation (PREREG:78) (R).
- **Runs.** Default 15–19 arm runs (3 + 8 + 4–8); worst 25 (3 + 8 + 8 + 6) (I, from PREREG:79-82 without the control's 4). Plus the anchor job, the retrain and the diagnostics job (R: PREREG:77-78). Waves-0 scope: 3 arm runs plus the same three jobs, plus 2 per transfer unit (I).
- **Units.** The same 8 Dolly categories. PREP-L and PREP-O have equal unit ids and equal `groups.json` (R: canonical-JSON hash comparison, ids only). PREP-L's data config says the Llama set excludes the same two over-limit rows "so every unit and task row equals prepared-kt-dolly's" (PREP-L manifest `data_config.amendments`) (R).
- **Edit files.** OLMo's sealed edit files embed PREP-O's manifest hash (SEAL `out/edits/*.json`, field `manifest_sha256`) (R), and `build_sealed.py` refuses any other prepared manifest (`build_sealed.py`:60-61, :141-144) (R). So Llama needs its own sealed files from PREP-L (§11, B4). The R_d and unit remove lists should equal OLMo's, because the row ids, the sorted members and the `derive_seed` labels are the same (I); the builder reads the manifest's `seed_derivation` too (`build_sealed.py`:146) (R), so the builder test must check the equality, not assume it (I). Only the arm hashes differ (I).
- **Steps.** 4,800 rows give 38 steps and 4,200 rows give 33, as for OLMo (PREREG:85) (R for OLMo). REC-L differs from REC only in model fields, `name`, `purpose` and `train.lr` (R: key-by-key diff, re-run in review), so the step plan is the same (I).
- **Recipe.** Recipe B at LR 5e-5 is Llama's main-recipe rung (paper decision 25, accepted 9 Oct 20:31 UTC; FOCUS:122) (R). The per-family rule changes only the learning rate (FOCUS:159) (R). Claims are made "at a matched erosion dose" (FOCUS:159) (R).
- **Recipe S_L.** REC-L with exactly the four A8 changes that made OLMo's S (`scripts/make_gateb_recipe.py`:5-8) (R): checkpoints q and e1; the Llama anchor bank by SHA-256; name; purpose. `training_identity` hashes `model` and `train` only, so S_L trains as Llama's Gate A did (PREREG:99) (R for OLMo; I for Llama).

---

## 4. Noise gate and σ̂

- **Kept as written** (PREREG:126-129, :153) (R): σ̂_gate = max(SD(r_1101, r_1102, r_1103), σ_eval,0), with r_j = U(a0, j) − U(R_j, j) from Llama's own Gate A a0 units. Final σ̂ = max(√P, σ_eval), P as PREREG:128.
- **One constant changes.** The second gate condition uses 0.75 × E_Llama = 0.75 × 48.33 = 36.25 pp (I; GA-L mean E 145/3) (R). It binds only above σ̂_gate = 36.25 / (4.177 × 0.707) = 12.3 pp, so σ̂_gate ≤ 7 binds (I).
- **Fallback triggers.** The fingerprint trigger compares the Llama retrain's q and e1 adapter fingerprints with Llama 1101's (`927b0486…`, `02e3645a…`; R: `tmp/family-probe-llama32-1b-b5e5/retrieved/llama32-1b-b5e5-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json`, re-read in review). The environment trigger compares the Llama a0 units with R_1101. All four Llama Gate A run roots carry LOCK `7e0dd998…`, the same lock as OLMo's Gate A (R: `shasum` of each `tree/environment-linux.lock`). So no lock difference is expected (I).
- **Planning noise (I).** OLMo measured σ̂_gate = 1.83 pp, below its own "low" planning case of 2.15 (FOCUS:82; PREREG:122) (R). Llama's seed SD of U is 4.34 pp (2 df), 1.64 times OLMo's (R: GA-L; PREREG:21). If same-seed arms share the seed shift, as on OLMo, Llama's σ̂_gate may be near 2 pp; if not, near √2 × 4.34 = 6.14 pp (I). The noise gate then passes about 100% / 96% / 80% / 72% / 62% of the time at σ_pair 2.15 / 3.75 / 5.45 / 6.14 / 7 (EV `lite_sim_out.txt`) (I).
- **If the gate fails** (σ̂_gate > 7 pp). Keep OLMo's stop: wave 0b does not run (PREREG:328) (R). **Correction in review:** OLMo's frozen route after a failed gate is "(b) take the fallback", not "return to review" (PREREG:3, the freeze line; PREREG:328, :364; FOCUS:125 item (7); the user's 6 Oct rule, FOCUS:52: "take the fallback below rather than adjust the design until something passes") (R). The Llama analog (I): no redesign of Gate B-lite; Llama's localization is reported as "not readable at this budget"; the Llama P1–P6 replication then follows the stage seed rule, which reads "> 6.0 pp: no stage, review" (FOCUS:242) (R) if the user confirms that the rule governs stage 2 (L12). Because the seed rule reads the final pooled σ̂, which a failed gate never produces, the freeze must say that σ̂_gate stands in for it here (I). The user confirms this route at the freeze (decision U4).

---

## 5. The decision rule: kept, with evidence that a reduced rule is worse

### 5.1 Scope first (review addition; decision U0)

The note's variants below all keep wave 1. A larger saving comes from not running the unit arms at all (I).

| Scope | Runs (arm runs) | Expected spend, measured rates (I; EV `lite_money_out.txt`) | Planning need (I) | Gives stage 2 | Loses |
|---|---|---|---|---|---|
| **W0: waves 0a + 0b + seal; transfer test if OLMo localizes** | 3 (+2 per transfer unit) | $11.67–14.84 (+$3.7–4.7 per transfer unit) | $27.53 at the anchor launch; a 2-arm transfer pod then its Granite launch needs $13.40 (EV `scope_money_out.txt`) | anchors, S_L, R_1–R_3, σ̂_gate (2 df), A1 and L1 scores, sealed Llama rankings, retrain states, the transfer test | Llama's own LOCALIZED/DIFFUSE verdict; Gate C on Llama; the held-out selector test (FOCUS:240, PLAN-S:132); the final pooled σ̂ (the seed rule would read σ̂_gate) |
| W1: W0 + wave 1, D_u reported only | 11 | + $13.78–17.26 | $27.53, then $37.56 at wave 1 (EV `scope_money_out.txt`) | W0 + the menu-level ρ between families and P-L2's D_u | the verdict; the held-out test stays degenerate (one seed per unit; REQ-16's pick needs ≥ 2 full-run seeds, S1B:107) |
| **K − LC: the frozen rule minus the length control (recommended if full)** | 15–25 | $32.35–49.35 default, $62.68 worst | $27.53, then $83.18 at wave 1 | everything above | nothing planned, except the length control |

- **Recommendation (I).** If the user funds stage 2 at about the level RP estimates for the Llama-1B replication ($115–135; RP:84, :138) (R), run K − LC: the adopted plan tests the selector predictions on Llama (FOCUS:240) (R), and W0 would break that. If money is short, run W0: every W0 run is reused by stage 2, and the G1 problem of §6.1 then touches only the R arms and the transfer arms. W1 is not recommended: it pays for wave 1 but cannot give a verdict or a usable held-out test (I).
- **Under W0, the dropped held-out test** must be recorded as dropped before OLMo's wave 1, so that dropping it cannot depend on an outcome (I).

### 5.2 The rule inside the full scope

**Kept.** LOCALIZED / DIFFUSE / TOO CLOSE exactly as PREREG:135-139, with the same constants, the same missing-arm rule and the automatic extension (PREREG:131-157) (R). The guards are as §6 states. One report is added: the exploratory E-scaled floor 8 × E_common / 45.1, which the user adopted on 8 Oct as an "exploratory, report-only secondary reading" (FOCUS:204) (R). OLMo dropped it because it equals 8 pp at E = 45.1 (PREREG:143) (R). For Llama it is 8 × 48.33/45.1 = 8.57 pp, so it reads something new (I). E_common in FOCUS:204 meant the common recipe's E; no common recipe exists now (FOCUS:158-159) (R), so using Llama's own E is a reinterpretation (I; decision U8). It never changes a verdict (FOCUS:204) (R).

**What was tested.** The frozen §2 noise model and §3 rule as a simulation (EV `lite_sim.py`; 100,000 runs per cell; guards not simulated, as in PREREG:160). **Calibration:** it reproduces PREREG §4's table within Monte Carlo error. For example, at σ_pair 3.75 it gives gate 96%, P(LOCALIZED | gate) 0.2 / 51.8 / 82.6 / 96.1% at 0 / 8 / 10 / 12 pp and DIFFUSE 5.2% at 8 pp; PREREG:165 gives 96%, 0.2 / 52 / 83 / 96% and 5.1% (R: EV `lite_sim_out.txt`; PREREG:165; checked in review). Then four cheaper variants at E = 48.33 (I):

| Variant (no length control in any) | P(LOCALIZED \| gate) at 8 / 10 / 12 pp, σ_pair 3.75 | same, σ_pair 5.45 | false DIFFUSE at 8 pp, σ_pair 5.45 / 6.14 / 7 | false LOCALIZED \| gate, no effect, σ_pair 5.45 / 7 | mean runs, no effect, σ_pair 3.75 | worst runs |
|---|---|---|---|---|---|---|
| **K: frozen rule (picks, extension)** | 52 / 83 / 96% | 39 / 62 / 81% | 7.6 / 7.4 / 6.8% | 1.3 / 2.9% | 18.0 | 25 |
| A: top-2 by D only, extension kept | 56 / 86 / 98% | 44 / 69 / 87% | **11.7 / 12.3 / 11.8%** | 1.7 / 4.0% | 15.3 | 21 |
| A3: top-3 by D only, extension kept | 51 / 82 / 96% | 37 / 60 / 79% | 8.6 / 8.8 / 8.4% | 1.4 / 3.1% | 17.4 | 23 |
| B: top-2 by D only, no extension | 38 / 63 / 82% | 27 / 45 / 61% | 8.0 / 8.2 / 7.9% | 1.5 / 3.2% | 14.5 | 15 |
| C: picks kept, no extension | 33 / 56 / 75% | 22 / 37 / 53% | 5.0 / 4.9 / 4.5% | 1.2 / 2.2% | 17.0 | 19 |

Runs count arm runs from wave 0a on (R_1–R_3 included). Source: EV `lite_sim_out.txt` (I; every cell checked against the output in review).

**Reading (I).**
- A is the cheapest with full power, but it breaks KTD's bound "a true 8 pp unit reads DIFFUSE ≤ 10%" (PREREG:155) at σ_pair ≥ 5.45. Without the picks, a true unit that misses the top 2 by D has no wave-2 bound to block DIFFUSE.
- A3 saves about 0.6 runs on average against K and loses a little power. It is not worth a new rule.
- B and C cut the extension. They lose 14–19 points of power at 8 pp (σ_pair 3.75), because the extension "carries much of the power" (PREREG:173) (R).
- K costs about 2.7 runs more than A and 3.5 runs more than B on average at σ_pair 3.75 (about $4–7; I, at $1.58–1.96 per arm; §12). So K, minus the length control, is the recommended rule inside the full scope.
- The simulation's diagnostics pick the true unit with probability 0.5 (PREREG:160) (R). If Llama's diagnostics are worse, the picks are worth less and A's DIFFUSE excess is smaller (I); this does not change the choice, because A still has no bound of its own (I).

**Length control: cut (I).** It runs only after LOCALIZED and changes only the wording, never the verdict (PREREG:254-255) (R). On Llama it would cost 4 runs, about $7–9 at measured rates (EV `lite_money_out.txt`) (I). Because the prior favours DIFFUSE or TOO CLOSE (PREREG:258) (R), the expected spend saved is small, about $2–4 (I); the larger saving is in planning: the wave-1 need falls from $94.95 to $83.18 (EV `lite_money_out.txt`) (I). If Llama reads LOCALIZED, the paper says "localized under the per-example-mean loss; content and answer length not separated on Llama" (the second wording of PREREG:255) (R), beside OLMo's control result, which says nothing about Llama's unit unless it is OLMo's unit too (I). Option: keep it (decision U2).

---

## 6. Guards G1–G4 and the direction checks

### 6.1 G1 (answers end): the one change that needs the user

**The problem (R).** Llama's three Gate A a0 seeds have sampled answers failing the coherence screen at 64, 56 and 37 of 600 (10.67%, 9.33%, 6.17%), capped at 20, 24 and 4 (3.3%, 4.0%, 0.67%), and short-only failures at 11, 9 and 17 (GA-L `units.seeds.*.sampled`; re-counted in review, EV `answers_end_recount_out.txt`, counts only). OLMo's a0 seeds were at 42, 28, 22 failing and 2, 2, 0 capped (`research/experiments/2026-10-07-kill-test-stage0-results.md`:215) (R). So Llama sits on the 10% bar and OLMo well below it.

**Same-seed evidence (R; EV `answers_end_recount_out.txt`).** OLMo's Gate B R arms against OLMo's same-seed a0, seeds 1101 / 1102 / 1103: screen-failing 43 / 25 / 23 against 42 / 28 / 22; capped 1 / 2 / 0 against 2 / 2 / 0; short-only 38 / 18 / 20 against 34 / 18 / 16. Independent binomials at these rates would give an SD of about 8 answers for an arm-minus-a0 difference; the observed screen differences (+1, −3, +1) have an RMS of 1.9 (I). So the failure rate is a seed property that same-seed R arms share almost exactly (I). If Llama behaves the same way, every Llama R arm at seed 1101 starts near 64 of 600 (I). No unit-removal arm exists yet on either family, so how far a unit arm moves from its seed's a0 is unknown (I). These OLMo counts are a Gate B value seen before this freeze (§14).

**What each G1 rule would do (I).** Two models: (1) the original independent-binomial model with Llama's same-seed rates (EV `g1_sim_out.txt`); (2) the review's shared-seed model: an arm's counts are its seed's a0 counts plus a difference of SD 2 answers (R arms), plus an extra SD sd_u for unit arms (EV `g1_sim_shared.py`, `g1_sim_shared_out.txt`). m = 2; seeds 1104–1105 drawn from the three a0 seeds.

| G1 rule | a0 arm that fails | Binomial model: P(LOCALIZED's 4 arms pass) / P(all DIFFUSE arms pass) | Shared-seed, sd_u = 0: LOC / DIF | sd_u = 9 answers (1.5 pp): LOC / DIF | sd_u = 18 (3 pp): LOC / DIF |
|---|---|---|---|---|---|
| (a) OLMo's G1 as frozen | 1101 | 0.51 / **0.000** | 0.97 / **0.000** | 0.64 / **0.000** | 0.46 / **0.000** |
| (b) decision-25 short pass: fail if capped > 5% or (screen − short)/(600 − short) > 10% | none | 0.80 / 0.095 | 1.00 / 0.99 | 0.83 / 0.07 | 0.63 / 0.01 |
| (c) **Llama-anchored bars: fail if capped > 7% or screen > 14%** | none | 1.00 / 0.95 | 1.00 / 1.00 | 1.00 / 0.90 | 0.90 / 0.26 |

**Headroom over the family's own a0 at the tightest seed (I; from the counts above).**

| Bar | OLMo under OLMo's bars | Llama under (a) | Llama under (b) | Llama under (c) |
|---|---|---|---|---|
| screen (pp below the bar) | 3.0 (1101: 7.0% vs 10%) | −0.67 (fails) | 1.0 (1101: 9.0% vs 10%) | 3.3 (1101: 10.67% vs 14%) |
| capped (pp below the bar) | 4.7 (1101/1102: 0.33% vs 5%) | 1.0 (1102: 4.0% vs 5%) | 1.0 | 3.0 (1102: 4.0% vs 7%) |

- Under (a), DIFFUSE cannot be reached in any model, because READ applies DIFFUSE's G1 to the a0 arms too (READ:82-83) (R) and Llama's a0 seed 1101 already fails (R: GA-L). That is a verdict fixed before any run (I).
- (b) follows decision 25, which accepted this exact short-answer case for Llama's rung (FOCUS:122; ICML:239) (R). It works only if unit arms move their answer endings as little as R arms do (shared-seed, sd_u = 0); with a unit-arm SD of 1.5 pp it blocks DIFFUSE about 93% of the time (I). It leaves Llama 1.0 pp of headroom where OLMo had 3.0–4.7 pp, so it is stricter for Llama than OLMo's frozen G1 was for OLMo (I).
- (c) sets each bar at Llama's own a0 maximum (capped 4.0% at 1102; screen 10.67% at 1101) plus 3 pp, rounded up to a whole per cent (7.0% and 13.67% → 7% and 14%). The bars are 42 and 84 of 600. Short answers count as failing, so no short-answer clause and no user decision after an outcome are needed (I). Its screen headroom (3.3 pp) matches OLMo's (3.0 pp); its capped headroom (3.0 pp) is smaller than OLMo's (4.7 pp) (I). So (c) is a translation of OLMo's headroom more than a loosening, though in absolute terms it allows more failing answers (I). (The pre-review text called 3 pp "about 2 binomial SEs" of a two-arm difference; it is about 1.8 SEs at 1.65 pp per SE; I.)

**Recommendation (I).** Rule (c), with G2 binding as frozen (coherent-only U; PREREG:148) (R). G2 is the guard that protects the verdict from incoherent answers; G1 then guards only against an arm whose answers end clearly worse than Llama's own fine-tuned baseline (I). Report each arm's status under rules (a) and (b) as well (report only). (c) also covers Gate C's pick-arm G1 guard (PREREG:194) (R), whose pick arms at seed 1101 would otherwise fail like the a0 (I). This is a change chosen after Llama's Gate A was read, from Gate A data and OLMo's R-arm answer-end counts only, and before any Gate B-lite run. It must be disclosed as such, and the user decides (decision U1). The kept parts of G1: a failed arm is not re-run, because failures are deterministic on a matching machine; an R arm that fails G1 blocks both verdicts (PREREG:147) (R).

**Limit (I).** Even under (c), if unit removals move answer endings by about 3 pp per arm, DIFFUSE's arms all pass only about a quarter of the time (shared-seed, sd_u = 18). DIFFUSE needs every one of 15–19 arms to pass. So TOO CLOSE by a G1 failure stays a real outcome on Llama, and the paper should say so before the run (I).

**Alternative (I).** A same-seed relative bar: a unit arm fails G1 if its capped or screen share exceeds its same-seed R arm's by more than 3 pp; each R arm is checked against (c). Every seed 1101–1105 has an R arm (R_1–R_5), so it covers the extension (the pre-review text rejected it for lack of an a0 at 1104–1105; R arms remove that objection). It targets the right question (did removing the unit worsen answer endings?), but it adds a rule that OLMo never had, and it lowers DIFFUSE's reach further. Not recommended; listed for U1.

### 6.2 G2, G3, G4 and the direction checks

- **G2 and G3: kept** (PREREG:148-149) (R). Llama's Gate A has 0 unscored answers (GA-L `units.*.unscored.total`) (R), so the G3 unscored corner is unlikely to bind (I).
- **G4: the rule is kept; the constant changes.** The bound is Ref(untuned) + 5. Llama's untuned Ref is 11/100, so the bound is 16/100 (R: GA-L `units.untuned.overrefusal.refusals` 11, `n` 100; I for the bound). Llama's a0 Ref is 5, 4 and 3 of 100 (R: GA-L). The lead re-computes Ref(untuned) with READ's denominator (refusals / 100, an invalid answer counted as not refused; PREREG:150) before the freeze (I).
- **Direction checks: kept** (PREREG:151) (R). Λ_Granite uses the pod Granite judge. Llama's Granite pods had 0 unparsed of 1,000 items and a 200/200 known-answer gate (FOCUS:126) (R).
- **Greedy loops: reported, not gating (kept).** Llama's fine-tuned greedy answers loop: 55, 51 and 31 of 200 harm greedy answers capped at LR 5e-5 (GA-L `units.seeds.*.greedy`) (R), and 60 of 200 at LR 1e-4 (FOCUS:229) (R). The frozen bars report greedy loop shares and do not gate on them (FOCUS:343) (R). Greedy answers still feed G4 and Λ_Granite. A looped greedy answer is still judged, so these checks stay defined (I); a difference in loop rates between u and R arms can move Λ_Granite, which is only a direction check (I). The cost of loops is in §12.

---

## 7. Gate C on Llama

- **Kept as frozen** (PREREG:181-198) (R). It is read only if Llama reads LOCALIZED (full scope only). It needs no extra runs beyond the picks in wave 2 (I). Its pick-arm G1 guard uses the G1 rule chosen in U1 (I).
- **Diagnostics.** The bi-anchored attribution on the Llama retrain's q and e1; representation similarity on the untuned Llama; the classifier, report only (PREREG:182) (R). `gate_c_representation.py` and `gate_c_classifier.py` take the prepared set, recipe and anchors as arguments (their headers, lines 1-12) (R), so they should run on Llama unchanged (I; a CPU dry run checks it).
- **The classifier may be family-independent.** It scores (prompt, training response) with the recipe's guard (`scripts/gate_c_classifier.py`:5-9) (R). The rows and the guard are the same for both families, so Llama's classifier unit means may equal OLMo's sealed ones (I, UNVERIFIED). An equality check is a free consistency test (I).
- **pick_F.** Llama's own unit table gives first-5 shares equal to OLMo's to three decimals, so pick_F = classification (0.288) again (R: count from PREP-L `target_tokens`, counts only, re-run in review; OLMo value at PREREG:187). Llama's target tokens per unit differ from OLMo's by at most 38 tokens in about 20,000–130,000 (R: same count).
- **Seal.** Llama's three rankings, their SHA-256, pick_F and the two equalities go into FOCUS before any Llama wave-1 run (as PREREG:196) (R for OLMo). Under W0 the seal is still made (the rankings feed A1, L1 and P-L5) (I).

---

## 8. Judges and wording

- **U: Qwen3Guard** on the 600 sampled answers per arm, as Gate A (PREREG §6) (R). The kit's guard-record check against R_1101's pulled record stays (PREREG:107) (R).
- **Granite: on the pod, one device for every Llama contrast.** Every Llama Gate A Granite file is pod-made (FOCUS:123) (R). Two mid-path Granite launches (after wave 2 and after the extension), each re-launched once on failure, then "Granite missing" (PREREG §6; FOCUS:125 item (5); RULES:67-69) (R).
- **HarmBench: on the pod, report only.** One launch after the last kit pod (PREREG:315) (R). Llama's a0 E_HB at its rung is +28.3, +34.8 and +26.8 pp (mean +30.0), above the 20 pp line, with the same sign and at least half of E (FOCUS:110) (R). So a Llama harm sentence may say "harmful compliance as the HarmBench classifier defines it", if its Λ_HB meets the same-sign, half-size rule (FOCUS:110, :244) (R). The Llama a0 HarmBench and Granite results exist from pods `hb-llama-b5e5-1` and `granite-llama-b-1/-2` (FOCUS:110, :126) (R). **Per-arm judge files in READ's schema do not exist yet** for them: `tmp/judge-pod/hb-llama-b5e5-1/` holds `fetched/` and the pod records only, while OLMo's `tmp/judge-pod/olmo-b-g-untuned/` holds `judges-B/` written by `write_files.py` (R: file listing in review). So `write_files.py` must be run on the Llama caches on the Mac ($0) before wave 0a is read, as PREREG:327 required for OLMo (I; B13).
- **Wording and the blind read.** The verdict stays on U. The wording rules of 9 Oct apply unchanged: U is "refusal erosion as Qwen3Guard labels it" (FOCUS:138 (b), :142) (R); the blind-read caveat sits once in the measurement section and once in the limitations, with an appendix (FOCUS:138 (c)) (R; FOCUS:142's per-sentence caveat was the lead's proposal, settled by :138). The blind read's Llama-3.2-1B group was 8 Qwen3Guard-Unsafe answers from recipe-B fine-tunes, plus 2 Safe controls (R: the read's pre-registration at commit 4d63e04, lines 17-26; ICML:653 says groups of 6 to 12). That pre-registration was fixed on 8 Oct at 20:56 UTC (R: its line 3), before any LR 5e-5 run existed (the rung-2 probe was pre-registered 9 Oct 15:31 UTC; FOCUS:133) (R). So the group came from LR 1e-4 units (I, from the dates), and no human read covers Llama at its rung (I).
- **Paper decision 24 (a second rater or a larger human read; open).** FAQ's main-track list asks for "HarmBench co-primary plus a human check" (ICML:238) (R). If the user plans one on stage-1 arms, I recommend a Llama stratum at LR 5e-5 and a short-answer stratum (Llama has 9–17 short normally-ended answers per a0 seed; GA-L) (I). It gates nothing in Gate B-lite (I).

---

## 9. Comparison scale, replication claims and the optional transfer test

**Scale (PLAN-S:243 asks for "pp and Λ/E, with the ratio's interval") (R).**
- **Primary: pp.** The verdict's floor is in pp (PREREG:142) (R).
- **Secondary: Λ/E**, with a 90% Fieller interval. Var(Λ_u) = (0.707σ̂)²; Var(E) = Gate A's edge-band SE², with SE 2.64 pp for Llama (GA-L `aggregate.mean_E_class.SE_E_pp`) and 1.93 pp for OLMo (`research/experiments/2026-10-07-kill-test-stage0-results.md`:222) (R). Cov(Λ_u, E) = 0, because Λ_u cancels a0 and E uses only a0 and the untuned unit (I).
- **Why the choice is safe now (I).** E_Llama / E_OLMo = 48.33/45.1 = 1.07. So the two scales differ by 7%, and the choice can move a cross-family comparison only when a contrast sits within about 7% of a bar.

**Replication claims, fixed now (I).**
- **Verdict level.** "Same verdict" if both read LOCALIZED on the same unit, or both read DIFFUSE. "Different" if one reads LOCALIZED and the other DIFFUSE. Any TOO CLOSE gives "not resolved".
- **Unit level.** For each unit with Λ on both families: the difference Λ_u(Llama) − Λ_u(OLMo), with SE = 0.707 √(σ̂_O² + σ̂_L²). Its MDE (80%, two-sided 5%, normal) is about 2.8 × SE: 5.6 pp at σ̂ = 2 pp in both families, 10.5 pp at 3.75 pp (I). σ̂ rests on about 3 df per family (PREREG:119) (R), so a t-based MDE is larger; the freeze names which one is used (I). "Replicates" means the same sign and a difference below this MDE (PLAN-S:244) (R; its use for unit-level Λ is an extension, I). A mock reviewer (MRA:198, a read-only mock review, commit 5a96acd, not a decision) objects that this rule "accepts absence of evidence as replication" (R). A $0 strengthening, if the user wants it: also report a two-sided 90% interval of the family difference and label "replicates" only if it lies inside ± the MDE, as stage 1's TOST does for SESOI (PLAN-S:115) (I; decision L13).
- **Menu level, report only.** The Spearman ρ between the families' 8 wave-1 D_u, against ρ_crit = 9/14 (the frozen K = 8 critical value; PREREG:195) (R for the value).

**Optional transfer test (decision U3; I).** If OLMo reads LOCALIZED, OLMo's LOCALIZED unit with the largest Λ (ties to the lower id; the same rule as PREREG:254's control unit) is pre-specified for Llama. If it is not already in Llama's wave 2, it runs at 1102–1103 (+2 runs; about $3.7–4.7). Its contrast T_u = Λ_u on Llama is read against max(8, 2.353 × 0.707σ̂), the one-sided 5% t at 3 df (the same constant as PREREG:255), with G1–G4 and the direction checks on its arms. One unit means one test, so no multiplicity correction is needed (I). **Review change:** the pre-review text allowed up to 2 units with no correction; that runs two tests at 5% each. If the user wants a second OLMo unit, it is report only, or both are read by Holm at 5% (the first against t = 3.182, the one-sided 2.5% value at 3 df; PREREG:131) (I). The unit is chosen by the other family's data, so selection on Llama's data does not arise (I). These arms enter neither Llama's verdict nor its σ̂, so the frozen verdict rule stays unchanged (I). Under W0, σ̂ is σ̂_gate (I). Why it matters: FAQ's main-track list asks for "one clear replicated finding" (FOCUS:74) (R). A transfer test of OLMo's unit is the most direct form of it, at 0–2 runs (I).

---

## 10. Predictions for Llama (to record before Llama's wave 0a; they gate nothing)

- **P-L1, prior (I).** DIFFUSE or TOO CLOSE is more likely than LOCALIZED, as for OLMo (PREREG:258) (R). Llama's erosion leans more on the refusal opening: the opening switch carried 0.68 of the unsafe increase at LR 1e-4 (FOCUS:229) (R), and Llama's untuned direct answers are already 64% unsafe (FOCUS:145) (R).
- **P-L2, size bound (I).** The linear first-5 dose model of P3, D_u = E × (s_u − 1/8) with E = 48.33, gives the largest D at +3.57 pp (classification); the bottom units are brainstorming −1.57, summarization −2.86, general_qa −3.20 and creative_writing −4.20 pp (R: count from PREP-L `target_tokens`, re-run in review). The same script reproduces OLMo's frozen P3 values to their rounding (+3.33, −1.46, −2.67, −2.98, −3.92 against PREREG:261's +3.3, −1.5, −2.7, −3.0, −3.9) (R).
- **P-L3, wave-0 check (I).** The same model predicts mean r_j = E/8 = 6.0 pp; saturation predicts about 0. OLMo measured 2.5 pp (FOCUS:82) (R).
- **P-L4, opening share (I).** About 0.68 of each arm's U change runs through the opening switch, from the LR 1e-4 probe (FOCUS:229) (R); not yet measured at LR 5e-5.
- **P-L5, cross-family (I).** Llama's attribution and representation rankings put general_qa first, as OLMo's sealed rankings do (FOCUS:77) (R for OLMo). This prediction is written after OLMo's rankings were seen (§14).
- **P-L6, Gate B-lite noise (I).** σ̂_gate between 1.5 and 4 pp, the point 2.5 pp, on the OLMo same-seed pattern (FOCUS:82) (R for OLMo); also written after OLMo's σ̂_gate was seen.

---

## 11. Engine identity and kit reuse: what must be built

**Engine.** Run Gate B-lite on engine X `472fc7f6…`, the engine of OLMo's Gate B (FOCUS:81-82) (R). The certificate covers Llama's Gate A engine e49a978c → X (certificate, second pair) (R). It certifies the evaluation code path, not one model (I). If the main checkout's engine changes before Llama runs (for example the Safe LoRA state transform, FOCUS:154), pack the kit from a checkout whose `code_identity()` is X, or certify the new engine with a determinism re-run first (PLAN-S:215) (I). RP:93 says no engine file changes until Gate B's last kit pod (R).

**Kit: a sibling copy, not an edit (I).** RULES is "THE one place to edit" for the OLMo kit (RULES:32) (R), and OLMo's Gate B is mid-path (wave 1 waits; FOCUS:77) (R). Any byte change there changes the integrated kit's hashes during OLMo's path (I). So build `runkit/gate-b-llama/` from `runkit/gate-b-olmo/` with one family constants block, and test that the OLMo kit stays byte-identical. Items:

| # | What | Why (source) |
|---|---|---|
| B1 | Sibling kit `runkit/gate-b-llama/`; a diff test that it differs from the OLMo kit only in the constants block, the gated download (B3) and names | RULES:32 (R); OLMo path open (FOCUS:77) (R) |
| B2 | Constants: `PREPARED_MANIFESTS`/`PREPARED_NAME` = PREP-L `c52a50af…`; `REC` = REC-L; `RECIPE_S` = S_L; `GATE_A_FIXTURE` and `PREREG_FIXTURE_SHA256` = FIX-L `560d912a…`; `LOCK_SHA256` = `7e0dd998…` (unchanged); `MAN_PATH`/`MAN_SHA256` = the Llama sealed manifest; `ANCHOR_FILE_PIN` = the Llama anchor file; `PROBE_KEY` = `llama32-1b`; `MEASURED_UPPER_S`/`SPEND_UPPER_S` arm = 70 min; `DIAGNOSTICS_UPPER_S` = 3.5 h; `WORST_PATH_AFTER_WAVE1` without `("lc", 4)`; distinct host prefixes. Check: the `llama32-1b` row of `probes.py` names the LR 1e-4 ladder (`study-kt-llama32-1b-r64-b-*`; `probes.py`:27, :63), so nothing may pack a recipe from that ladder (I) | RULES:38-42, :64, :74-75, :90-112, :116 (R); values §3, §12 (I) |
| B3 | Restore the gated download: Llama-3.2-1B-Instruct is gated (`runkit/gate-b-olmo/probes.py`:59-61, `"gated": True`) (R). The OLMo kit removed the gated path from host.py and launch.py (`host.py`:6; `launch.py`:2) (R). Copy back `runkit/family-probe/host.py`'s `gated-download` (token on ssh stdin only; :12, :316-332) and launch.py's token checks; `setup/download_models_gateb.py` keeps its gated path (:3, :8-13) (R). Every Llama pod (anchor, waves, judges are open models) needs the token step (I) | user's HF token; Meta access approved (FOCUS:371) (R); FOCUS:371 also asks to rotate the token to read-only after the downloads (R) |
| B4 | Sealed files for Llama: a new version of `build_sealed.py`, which hard-codes PREP-O (`build_sealed.py`:60-61, :141-144) (R). Outputs: R_d1–d5, the 8 unit-removal files, Llama's unit table and MANIFEST; the length-matched M files only if the length control is kept. Test: all 13 remove lists equal OLMo's sealed lists, and the arm hashes differ | SEAL README (R); I |
| B5 | Anchors: `scripts/make_anchor_answers.py` unchanged; it takes `--recipe` (:4) and requires `query_bank` "ref" (:108-111), which REC-L has (R: recipe diff). One Llama anchor pod; seal the full file and the text-free record ([D10] rule, PREREG:97) (R). The 128-prompt list is reused by its hash; the counts-only near-duplicate check is re-run against Llama's banks (I) | PLAN-S:214 "Llama anchors" (R) |
| B6 | Recipe S_L: `scripts/make_gateb_recipe.py` hard-codes REC, its hash prefix and the name (:20-25) (R). A Llama version gets its own pinned hash | R |
| B7 | Gate C scripts reused unchanged (`998231ea…`, `23a7f5f0…`); a CPU dry run on PREP-L | RULES:100-102 (R); I |
| B8 | Reading READ-L: a copy of READ with a Llama constants block (READ:137-218 holds OLMo pins: `PREREG_SHA256`, `ENGINE_GATE_A` 55253874, `REC_PATH`/`REC_SHA256`, `TRAINING_IDENTITY`, the sealed manifest, unit table and prepared manifest, `RECIPE_S_NAME`, `GATE_A_PINS`, `P1101_ADAPTER_FINGERPRINTS`, `GATE_A_MEAN_E_PP` 45.1, `G4_MAX_REF` 22/100, `REF_UNTUNED` 17/100, `P1_CATEGORY`, `P4_MEAN_R_PP` 5.6, `A9_SCRIPT_SHA256`, `LEXICON_COUNTS_SHA256`) (R). Rule changes: G1 rule (c); no length-control phase; the 8.57 pp report; P-L reports; the optional transfer phase; the untuned-unit rule (B12). Tests: READ's suite (101 tests, FOCUS:81) (R) on Llama fixtures, plus synthetic G1-(c), untuned-unit and transfer cases; mutation runs | I |
| B9 | Llama Gate A pins: job.json and COMPLETE.json SHA-256 of `1101-a0-init-a1` and `{1101,1102,1103}-a0-e1-a1` (job hashes in GA-L `identity.job_sha256`) (R) | READ:152-163 pattern (R) |
| B10 | Money tests: the need with Llama uppers (§12), re-derived by the kit's own functions | RULES:293-307 (R) |
| B11 | The retrain's states: keep the Llama wave-0b pod until stage 2 uses them, or pull the adapter to the Mac and the private backup. OLMo kept w0b-2 for this reason (FOCUS:77) (R). Llama's Gate A adapters are lost (FOCUS:94) (R), so stage-2 references that need a0 adapters (adapter scaling, Safe LoRA) need train-only re-runs, 0.10–0.15 h each (PLAN-S:155) (R; I for the need) | I |
| **B12 (review)** | **The untuned unit.** READ's `gate_a_unit` refuses a unit whose `recipe_sha256` or canonical recipe is not REC's (READ:1300-1309) (R). Llama's untuned unit has recipe `bb0f563b…` (LR 1e-4 kit), not REC-L (R: its job.json). Either (a) READ-L accepts the untuned unit by equal evaluation config and equal engine, as FPR's baseline reuse did for Gate A (GA-L `identity.baseline_reuse`), a reviewed rule change; or (b) make a new untuned unit under REC-L on the anchor pod (one evaluation job, about 0.3–0.6 h, I). Default (a): it keeps the unit that Gate A's E used (I) | R; I |
| **B13 (review)** | **Judge files for Llama's Gate A units.** Run `write_files.py` on the `hb-llama-b5e5-1` and `granite-llama-b-1/-2` caches ($0, Mac) and pin each file's source, as PREREG:219 and :327 did for OLMo (R for OLMo). Then confirm the HarmBench numbers equal FOCUS:110's (I) | R: file listing; I |

**Effort (I).** About 2–4 developer-days plus one review round, most of it B8 and B12 with their tests; the pre-review estimate of 1–2 days left out B12 and the review round that every OLMo kit change had (PREREG:9-15) (R for OLMo's rounds). B3 is a copy of code that ran on Llama before (FOCUS:120) (R). Claude plan usage limits this work (FOCUS:125 item (8)) (R).

---

## 12. Costs at measured rates

**Measured inputs (R).** Llama Gate A jobs at LR 5e-5 (38 steps): 3,950 s, 3,181 s and 3,420 s (65.8, 53.0 and 57.0 min; seeds 1101, 1102, 1103). Training is 201–232 s of each; greedy generation 1,291–1,751 s; sampled generation 1,074–1,709 s (LED-L; re-read in review). OLMo's Gate A jobs: 2,041–3,116 s (LED of `tmp/family-probe-olmo2-1b*/…/1101-, 1102-, 1103-a0-e1-a1`). OLMo's Gate B kit: pod overhead ≤ 26.0 min; arms ≤ 49.0 min; diagnostics 3.04 h; retrain 0.077 h; $1.79/h (FOCUS:77). So a Llama arm costs about $1.58–1.96 of job time, against about $1.30–1.46 for an OLMo Gate B arm (I).

**Expected spend, $1.79/h (I; EV `lite_money_out.txt`).** Pod overhead 19–26 min; Llama arm 53.0–65.8 min; retrain 0.08–0.10 h; diagnostics 2.8–3.5 h (OLMo's 3.04 h scaled; Llama rows have about 11% more tokens, mostly the chat template: token sums 1,109,639 against 996,635 in the two families' Gate A ledgers) (R for the sums). Llama's training steps were not slower than OLMo's (201–232 s against 219–248 s per 38 steps at Gate A; LED-L and OLMo's ledgers) (R), so 3.5 h is a margin, not a measured upper (I).

| Step | Spend |
|---|---|
| Anchor pod | $0.64–0.95 |
| Wave 0a (3 R) | $5.31–6.66 |
| Wave 0b (retrain + diagnostics) | $5.72–7.22 |
| **Pre-wave-1 total (= scope W0 without transfer)** | **$11.67–14.84** |
| Transfer test, per unit (2 arms, one pod) | $3.7–4.7 |
| Wave 1 (8 arms, 4 + 4) | $13.78–17.26 |
| Wave 2 (m = 2 / m = 4) | $6.89–8.63 / $13.78–17.26 |
| Extension (1 unit / 2 units) | $6.89–8.63 / $10.62–13.33 |
| Length control (cut; for comparison) | $6.89–8.63 |
| **Default path, full scope (waves 0–2, no extension)** | **$32.35–49.35** |
| **Worst path, recommended rule** | **$62.68** |
| Worst path with the length control | $71.31 |
| Judge pods: 2 Granite + 1 HarmBench | about $1.5–4.5 (FOCUS:126: 1,000 Granite items in 15.8 min, $0.47; PREREG:315: HarmBench $0.93–1.88 for 23,200 answers) |

**Planning needs with the kit's own functions (I; EV `lite_money.py` imports a copy of RULES).** Check: with OLMo's constants the copy gives the frozen $78.45 (R: EV `lite_money_out.txt`; PREREG:15). With Llama's fixture, a 70-min arm upper and a 3.5 h diagnostics upper:

| Quantity | Llama value | OLMo frozen value |
|---|---|---|
| Caps: anchor / wave 0a / wave 0b | 1.5 / 5.25 / 6.75 h | 1.5 / 5.0 / 4.5 h |
| Need at the anchor launch | $27.53 | $21.75 |
| 4-arm pod: cap / spend upper | 6.5 h / $9.61 | 5.75 h / $7.46 |
| Wave-1 need, recommended rule (no length control) | **$83.18** (base $66.54, contingency $16.64) | $71.28 for the same path |
| Wave-1 need with the length control | $94.95 | $78.45 |
| Wave-1 need, waves 1–2 only | $61.58 | $52.74 |
| One arm re-run: running pod / new pod | $2.09 / $3.34 | $1.55 / $2.80 |

- Allowances come on top, as for OLMo: storage, a Granite re-launch ($3.78) and a HarmBench re-launch ($3.70) (FOCUS:77) (R).
- **With OLMo's 52-min arm upper the kit would plan 5.5 h caps for Llama** (EV `lite_money_out.txt`) (I). After a 26-min overhead and three 66-min arms, 1.77 h is left, less than the 2.06 h start requirement (FIX-L e1 upper 3,457 s + 265 s of training at 33 steps + 1,000 + 900 + 1,800 s; RULES:131-146) (I). So the fourth arm of each 4-arm pod would be deferred. Hence B2's 70 minutes. OLMo's 52 min was its Gate A maximum (51.8 min) rounded up to the minute (PREREG:266) (R); the strict analog for Llama is 66 min, which gives a 6.25 h cap instead of 6.5 h (I). Either fits; 70 min adds a margin for the extra 33-step arms' variance (I).
- **A fixture caveat (I).** FIX-L's e1 upper (3,457 s) is below Llama seed 1101's measured evaluation (about 3,726 s; LED-L). The job's start margins (3,700 s) absorb this, but the "every batch at the cap" projection is not a true upper for Llama.
- **Stage-2 estimate (I).** PLAN-S:226 gives stage 2 "$65–115; per-run cost UNVERIFIED". The Llama per-run cost is now measured: about 1.2–1.3 times OLMo's. Full-scope Gate B-lite ($34–67 with judges) plus about 44 primary-family runs (P1–P6 at 6 seeds, R to 8, a0 to 6) at about $1.8–2.3 each gives about $115–170. RP's estimate for the Llama-1B replication is $115–135 (RP:84) (R). With W0, about $92–125 (I).

---

## 13. Sequencing, money rules and stop rules

- **Order: kept** (PREREG:111) (R). Anchor job → recipe S_L frozen → wave 0a (noise gate) → wave 0b → seal the rankings → wave 1 → wave 2 → Granite → extension → Granite → HarmBench. No step starts before the step above it is complete. Under W0 the order stops at the seal, then the transfer test if OLMo reads LOCALIZED.
- **Money rules: kept** (PREREG §9; RULES:32-67) (R). Each arm is its own job with the per-job start gate; deferral stops at the first job that does not fit; the funding rule is outcome-free at the wave-1 launch with the factor 1.25; re-runs are paid from the contingency in launch order; a job the contingency cannot pay is declared missing. Every pod is deleted only after its verified private backup and with the user's yes (FOCUS:125 item (4)) (R).
- **Re-costing stop after wave 0b: kept,** with the user's standing rule for Gate B: continue without asking when the noise gate passed and the worst path at measured rates fits the balance plus the top-up (FOCUS:125 item (2)) (R). That rule was given for "the whole Gate B path" (FOCUS:125 item (1)) (R); extending it to Gate B-lite needs the user (I; part of U5). The user's 16 Oct "stop asking me for approval and go ahead and do these things" is in FOCUS:76; the lead's reading of it (I, in FOCUS:76) keeps the frozen money rules, the guard, the $10/h limit and the auto-mode check in force (R). The adopted direction also says "stop and ask after every stage" (FOCUS:256) (R), so the start of stage 2 is a point where the lead asks (I).
- **Funding (I).** OLMo's wave 1 needs $83.91 with its allowances; the balance was $91.94 on 16 Oct 19:07 UTC (FOCUS:76-77) (R). Llama's pre-wave-1 spend ($11.7–14.8) would take the balance below OLMo's need. So Llama Gate B-lite starts only on its own funding event (PLAN-S:226; FOCUS:253) (R).
- **The OLMo window (R).** From OLMo's wave-1 launch to OLMo Gate B's last kit pod, no other pod launches unless the top-up holds it as a named allowance (`tmp/gi-v-stage1-plan/PLAN-final.md`:259). So Llama pods run before that window with money beyond OLMo's need, after it, or as a named allowance (I).
- **Wall clock (I).** About 15–22 h of pod time over 1.5–3 days with the reads and the seal (full scope); about 8–10 h over 1 day for W0. The ICML 2027 abstract is about 16 Jan 2027 (FOCUS:74) (R). RP's schedule (not adopted) starts the Llama-1B replication on 23 Nov (RP:105) (R). Gate B-lite comes before the replication (it gives its σ̂, A1 scores and anchors), so it should end by about 23 Nov and start, with the kit build, by about mid-November (I).
- **Order against Alpaca (R).** The user made Alpaca "the planned second benign dataset, right after Gate B" (FOCUS:155). RP (not adopted) moves Alpaca to Llama-8B (RP:103, :150) (R). Llama Gate B-lite and Alpaca compete for the same money and time after OLMo's Gate B. The user sets the order (decision U6).

---

## 14. When the rules must be frozen

**The PLAN-S deadline is missed (R).** PLAN-S:243 says these rules and the comparison scale are "pre-registered before Llama's formal Gate A". The stage-1 reader also said Llama's Gate A seeds "should not run before" them (`tmp/gi-v-stage1-plan/read-stage1.md`:233). The formal Gate A was pre-registered at 20:31 UTC on 9 Oct; its seed 1101 is the rung-2 probe (job 15:50–16:58 UTC, read 16:59 UTC); seeds 1102–1103 ran from 21:03 UTC (FOCUS:120, :123, :131; LED-L); the read was at 23:16 UTC (FOCUS:117); the user recorded PASS on 10 Oct 09:40 UTC (FOCUS:116).

**What this implies (I).**
1. **Disclose a deviation.** The Llama pre-registration states that its rules were written after Llama's Gate A was read, and it lists every Gate A value seen: E +48.00 / +52.83 / +44.17 pp (mean 48.33), seed SD 4.34 pp, the answers-end counts, the greedy loops, the HarmBench and Granite results (GA-L; FOCUS:110, :117) (R for the values).
2. **The harm is limited.** Gate A cannot reveal a Gate B-lite outcome: no unit contrast exists yet. OLMo's own Gate B draft was also written after OLMo's Gate A passed (PREREG:5: first written at 09:40 UTC on 8 Oct; FOCUS:270: Gate A PASS at 05:40 UTC) (R), but it adapted a rule written before any Gate A (KTD, 6 Oct; PREREG:20-22) (R). Llama's Gate B-lite likewise adapts PREREG, which was frozen before Llama's Gate A read (PREREG:3, 10 Oct 11:16 UTC; FOCUS:117, 9 Oct 23:16 UTC: the read came first, the freeze after) (R). So only the Llama-specific changes (G1, constants, transfer test) are written after Llama's Gate A (I).
3. **Every constant that uses a Gate A value says so** and comes from Gate A data only: the noise gate's E term, the G1 bars, the G4 bound, the cost uppers. The G1 change is the one that could look tuned, so it goes to the user with the evidence of §6.1.
4. **The comparison scale is fixed now** (§9). E_Llama and E_OLMo are known and differ by 7%, so the choice cannot materially favour a result.

**New deadlines (I).**
- **Freeze (recommended): with the stage-1 commitments, before OLMo's wave-1 launch.** Then the Llama rules are blind to every OLMo unit outcome, and the held-out predictions (§15) freeze with REQ-18 (S1B:111) (R for REQ-18). Record the SHA-256 in FOCUS. List the OLMo Gate B values already seen, as REQ-21 (m) does: r_j, σ̂_gate 1.83 pp, P4, the P(LOCALIZED) lookup, the re-costing figures, the sealed rankings, scores, picks and ρ values (S1L §3, "Records to add" item 4) (R); **plus (review) the OLMo R arms' answers-end counts and task-loss differences used in §6.1 and §15 (EV `answers_end_recount_out.txt`)** (I).
- **Latest acceptable freeze:** before OLMo's first wave-1 outcome is read and before Llama's anchor job (I). A freeze after any OLMo unit outcome labels the transfer test and every cross-family comparison "post-OLMo-outcome" (I).
- **The scope decision U0** is part of the freeze (I).
- **Llama's rankings seal:** before any Llama wave-1 run (§7).

---

## 15. Held-out selector predictions for Llama's menu: what they need (full scope only)

**What is promised (R).** "OLMo-calibrated predictions of P(best found) and regret for SH and the one-shot screen at B = 4 and 8 are scored on Llama's Gate B-lite menu" (PLAN-S:132); the adopted amendment says the predictions are "tested on Llama" (FOCUS:240). REQ-18 includes them, "tested later" (S1B:111). The model's noise is 2.65 pp central and 3.85 pp high, "never σ̂_gate" (S1L:249; L15 (1)). D5 = (a) keeps the selector secondary and model-based (FOCUS:78).

**What they need (I unless marked).**
1. **Freeze time.** In `predictions.json` with the code and settings hashes, before OLMo's wave 1 (REQ-18's deadline) and in any case before Llama's wave 1 is read. Its SHA-256 goes in FOCUS.
2. **No Llama measurement as input.** B and c_d are in units of c0 (S1L L15 (3)) (R), and the runs-only rules pay no c_d (I). So nothing from Llama's pods enters the predictions, and they stay held out (I).
3. **A replay that asks only for trials Gate B-lite runs.** Gate B-lite has, per unit, seed 1101 at full training; seeds 1102–1103 only for wave-2 units; 1104–1105 only for contested units. ψ-trials can subsample the saved labels at $0 (S1B:107 REQ-16) (R), but φ < 1 trials (part training) do not exist on Llama (or on OLMo's category menu) (I). A halving rule whose later round promotes a unit outside wave 2 cannot be replayed. The builder must add a test: every (option, seed, φ, ψ) trial that the frozen Llama cell rules can request is in Gate B-lite's design. If not, choose one of: (a) restrict the Llama predictions to quantities computable from wave 1 (for example the one-shot pick at ψ fractions of seed 1101, or halving's first-round survivor set); (b) pre-register that Llama's wave 2 also runs the units the frozen replay promotes (deterministic from seed-1101 labels; +0–4 runs); (c) score only the cells whose trials all exist. Default (a) (decision L5).
4. **The pick rule against the seed structure.** REQ-16's pick needs "at least 2 full-run seeds" (S1B:107) (R). On Llama only wave-2 units have 2+ seeds, so a one-shot pick at B = 8 may be "keep" by construction. The builder checks this with the Llama seed map before the freeze.
5. **A frozen truth.** G_m = U(a0) − U(m), with Llama's three a0 seeds. The "best" is the unit with the largest empirical-Bayes-shrunk G over all seeds Gate B-lite ran (REQ-17's shrinkage, S1B:109) (R for the method). Regret is measured against that best, with the truth's own uncertainty reported (posterior P(best) per unit).
6. **A proper score, not a pass/fail.** One menu gives about four outcomes (2 rules × 2 budgets). So report the Brier and log scores of the predicted P(best found) and the regret's position in its predictive interval, labelled "a consistency check with one menu" (PLAN-S:119 puts the predictions last in the testing order) (R for the order). The mock review makes the same point and proposes scoring the calibration of every unit contrast's predictive interval (8 units × 2 families) with a proper scoring rule (MRA:252-256) (R); that needs unit contrasts on Llama, so only the full scope gives it (I).
7. **(Review) A known noise mismatch.** The predictions use OLMo's noise, 2.65 / 3.85 pp per arm (S1L:249) (R). Llama's seed SD of U is 4.34 pp (GA-L) (R), above OLMo's high case. So a miss on Llama may come from noise alone; the freeze states this, and the report adds a sensitivity at Llama's measured σ̂, labelled post hoc (I).
8. **Feasibility inputs for Llama.** The screen needs O and L per Llama arm: O against Llama's untuned Ref (11/100; GA-L) (R) at τ_O ∈ {2, 5, 10} (S1L L15 (2)) (R). If L16's rule is applied to Llama, τ_L = 2√2 × s over Llama's a0 query losses (1.5663, 1.5683, 1.5680; GA-L) = 0.0030; OLMo's is 0.0067 (R: EV `answers_end_recount_out.txt`). OLMo's R arms raised the task loss by +0.0018 to +0.0037 over same-seed a0 (R: same file). On Llama that sits at τ_L, so random-removal options may fail the L screen by chance. L16 already records the 2-df risk (S1L:293) (R). The lead decides whether Llama's τ_L comes from Llama's a0 (decision L6).
9. **Diagnostic quality placement, if the diagnostic policy is scored too.** Llama's frozen Spearman ρ of the sealed rankings against Llama's 8 wave-1 D_u (S1L L15 (7)) (R). Gate B-lite gives it at no extra cost (I).

---

## 16. Decisions

### For the user
- **U0 (review). Scope.** K − LC, the full rule minus the length control (recommended if stage 2 is funded at about RP's level); or W0, waves 0a and 0b plus the seal and the transfer test (recommended if money is short; it drops Llama's own verdict, Gate C on Llama and the held-out selector test that FOCUS:240 adopted); or no Llama-1B Gate B-lite (RP's first 1B cut). §5.1.
- **U1. G1 for Llama.** (c) Llama-anchored bars, capped ≤ 7% and screen ≤ 14%, with OLMo's bars and (b) reported (recommended); (b) decision-25 short pass, which works only if unit arms move answer endings as little as R arms do; (a) OLMo's G1 unchanged, which makes DIFFUSE unreachable before any run; or the relative bar against the same-seed R arm (§6.1). It is a change chosen after Gate A was read, from Gate A data and OLMo's R-arm counts only. Confirm also that Llama's Gate A a0 units may enter σ̂_gate and G1 here (§1).
- **U2. Length control on Llama.** Cut (recommended; −4 runs, about −$7–9 if run, about −$2–4 expected, −$11.77 of wave-1 need), or keep it (PREREG §7 unchanged).
- **U3. Transfer test.** If OLMo reads LOCALIZED, run OLMo's top LOCALIZED unit on Llama at 1102–1103 as one pre-specified contrast (+0–2 runs, about $3.7–4.7) (recommended); a second unit only as report only or under Holm; or no transfer test (§9).
- **U4. If Llama's noise gate fails.** Stop after wave 0a, no redesign (the Llama analog of OLMo's frozen "take the fallback"), report "not readable at this budget", and let the stage seed rule read σ̂_gate (> 6.0 pp: no Llama stage, review) (recommended); or another route named now (§4).
- **U5. Funding and stop rules.** A funding event for Gate B-lite: about $27.5 free at the anchor launch and, in full scope, about $83 + allowances at the Llama wave-1 launch (planning), with expected spend about $34–67 (full) or about $12–22 (W0, with a transfer unit and its judge launches) (§12). It must not come from OLMo's frozen need. Confirm whether the standing re-costing rule of FOCUS:125 item (2) also covers Gate B-lite (§13).
- **U6. Order after OLMo's Gate B.** Llama Gate B-lite first, or Alpaca first as the 9 Oct 09:40 decision says ("right after Gate B"; FOCUS:155), or both in parallel if funded.
- **U7. Decision 24.** If a second rater or a larger human read is planned, include a Llama stratum at LR 5e-5 and a short-answer stratum (§8).
- **U8. The E-scaled floor.** Carry 8.57 pp as an exploratory, report-only floor for Llama (recommended), or drop it; using E_Llama in place of FOCUS:204's E_common is a reinterpretation (§5.2).

### For the lead
- **L1. Freeze time.** With the stage-1 commitments, before OLMo's wave-1 launch (recommended), with the deviation from PLAN-S:243 disclosed and the OLMo Gate B values seen listed, the R-arm answer-end counts included (§14).
- **L2. Design.** Variant K minus the length control (recommended inside the full scope), or A / A3 / B / C (§5.2). Note that A breaks KTD's DIFFUSE bound at σ_pair ≥ 5.45.
- **L3. Kit.** A sibling `runkit/gate-b-llama/` built from the OLMo kit with a constants block and the restored gated download (recommended), not a switch inside the running OLMo kit (§11). Who builds it, and when.
- **L4. Llama constants.** Arm upper 70 min (or the strict analog, 66 min); diagnostics upper 3.5 h; G4 bound 16/100 after re-computing Ref(untuned) with READ's denominator (§6.2, §12).
- **L5. Held-out predictions.** Ask the REQ-16–18 builder for the Llama replay-feasibility test and choose (a), (b) or (c) for non-replayable trials (default (a)); fix the truth, the score and the noise-mismatch statement (§15).
- **L6. τ_L for Llama.** From Llama's a0 by L16 (0.0030), or another rule fixed before Llama's wave 1 (§15 item 8).
- **L7. The retrain's states.** Keep the Llama wave-0b pod, or pull its adapter, for stage 2's Llama references (§11, B11).
- **L8. Anchors.** Llama's own anchor job (recommended), not a reuse of OLMo's anchor bank (it would give Llama OLMo's safe answers; PLAN-S:214 names Llama anchors).
- **L9 (review). The untuned unit.** READ-L accepts Llama's untuned unit by equal evaluation config (recommended), or a new untuned unit is made under REC-L (§11, B12).
- **L10 (review). Judge files.** Write and pin the per-arm judge files of Llama's Gate A units before Llama's wave 0a is read (§11, B13).
- **L11 (review). Names.** Rename this design ("Llama-1B Gate B-lite") or RP's 7–8B transfer check, so the two are not confused (§0).
- **L12 (review). The seed rule for stage 2.** Confirm that FOCUS:242's rule, written for stage 1, also sets the Llama replication's seeds, and with which σ̂ (final pooled, or σ̂_gate under W0 or after a failed gate) (§1, §4).
- **L13 (review). The replication label.** Keep PLAN-S:244's "same sign, difference below the MDE", or add the equivalence interval that MRA:198 asks for (§9).

---

## 17. Evidence, commands and open concerns

**Commands run by the first author (all exit 0 unless noted).** `git branch`, `git log`, `shasum -a 256`, `wc`, `grep`, `sed`, `ls`, `find`, `date -u` (three times), read-only. Python reads of manifests, `groups.json` (ids only), `train_rows.jsonl` (`row_id` and `target_tokens` only), ledgers, summaries, COMPLETE.json, GA-L and the OLMo noise-gate output. FPR's `counts` on the three OLMo w0a-1 R units and the three Llama a0 units (Python 3.12, `PYTHONDONTWRITEBYTECODE=1`; two earlier attempts failed: Python 3.9 cannot import FPR, and a wrong folder level; both re-done). EV `lite_sim.py` (numpy; seed 20261016), `g1_sim.py`, `lite_money.py` (a copy of RULES `bf7dee40…` in that session's scratchpad). One numpy run under `python3 -I` failed (no numpy on that path) and was re-run without `-I`.

**Commands run in review (all exit 0 unless noted).** `date -u` (three times); `git log`, `git status`, `git show` (the blind read's pre-registration at 4d63e04, design lines only; the re-plan and sweep commit lists); `shasum -a 256` of every pinned source (all match the note's hashes; ICML changed to `024942b5…` at 21:54 UTC); `sed`, `awk`, `grep`, `ls`, `find` reads of PREREG, PLAN-S, FOCUS, READ, RULES, probes.py, host.py, launch.py, build_sealed.py, make_gateb_recipe.py, make_anchor_answers.py, the Gate C script headers, S1B, S1L, ICML, RP, PLAN-final.md, read-stage1.md and the certificate; Python reads of GA-L (numbers and ids), LED-L and OLMo's ledgers, the Llama fixture's `cap_projection`, the two recipes (key-by-key diff), Llama 1101's COMPLETE.json fingerprints, the untuned unit's job.json, PREP-L/PREP-O `groups.json` (ids) and `train_rows.jsonl` (`row_id`, `target_tokens` only), the OLMo noise-gate output; EV `answers_end_recount.py` (`python3 -I`; samples.jsonl fields `stop_reason`, `output_tokens`, `repetition_4gram`, `empty` and query-loss values only; no text printed) EV `g1_sim_shared.py` (numpy, without `-I`) and EV `scope_money.py` (`python3 -I`). One `echo =====` failed under zsh (the shell expands `=`); re-done. One `find` glob failed (wrong folder level for the lock files); re-done.

**Evidence files** (in `evidence/`; SHA-256 prefixes): `lite_sim.py` `a3bafc4b…`, `lite_sim_out.txt` `fd341223…`; `g1_sim.py` `951f9fdc…`, `g1_sim_out.txt` `8eca9555…`; `lite_money.py` `b6bed90b…` (it imports a RULES copy at a scratchpad path; copy `runkit/gate-b-olmo/gateb_rules.py` beside it to re-run), `lite_money_out.txt` `3caafcbf…`. Review: `g1_sim_shared.py` `ee8e8114…`, `g1_sim_shared_out.txt` `7598a930…`; `answers_end_recount.py` `2628ce30…`, `answers_end_recount_out.txt` `7f82850e…`; `scope_money.py` `ece1c06b…`, `scope_money_out.txt` `4cfb6e02…` (imports the repo's RULES `bf7dee40…` read-only, with bytecode writing off); `llama-gate-b-lite-rules.pre-review.md` `a49014cd…` (the text before this review).

**Open concerns.**
1. **The G1 change** is the largest judgement here and is not a neutral copy of OLMo's rule (§6.1). The choice between (b) and (c) turns on how far unit-removal arms move answer endings, for which no data exist on either family; OLMo's wave 1 will give the first such counts, after the recommended freeze (I).
2. **The simulation does not model the guards,** as SIM2 does not (PREREG:160) (R). Llama's real noise is unknown until wave 0a (I).
3. **Llama's diagnostics time is not measured.** 2.8–3.5 h is a scaled OLMo value (I).
4. **The held-out selector test is weak** (one menu), may not be fully replayable, and uses OLMo's lower noise (§15 items 3–4, 7) (I).
5. **τ_L for Llama** may make removal options infeasible by chance (§15 item 8) (I).
6. **Money and time** compete with OLMo's Gate B, stage 1, Alpaca and RP's 7–8B plan (§13) (I).
7. **Records (resolved in review).** FOCUS:75 records the S1L addendum as SHA-256 `b8a67719…`; the file now hashes to `11477648…` (R), because three later commits amended it (7bce3bc, the T1-verification rulings; d79f641, a time fix; 19c2d28, the literature-sweep rulings; S1L §4–§5) (R: `git log`). The L15 and L16 text cited here sits in S1L §2, which those commits did not rewrite (I, UNVERIFIED by diff).
8. **Still UNVERIFIED:** that the Gate C scripts run on Llama unchanged (§7); that the classifier's unit means equal OLMo's (§7); that the R_d remove lists equal OLMo's (§3); the cost of a new untuned unit under B12 (b). **Resolved in review:** the Llama judge files do not exist in READ's schema yet (§8, B13); the blind read's Llama group was 8 answers from LR 1e-4 units, by its dates (§8).
9. **(Review) Name clash with RP's "Gate B-lite"** (§0; L11).

---

## 18. Review changes (adversarial review, 2026-10-16, 21:44–22:12 UTC)

Every R claim was checked against its source at the hashes above. Most held. What changed, and why:

1. **Facts corrected.**
   - §0 finding 4 and §14: Llama's seed 1101 was not run at 21:03 UTC. It is the rung-2 probe (job 15:50–16:58 UTC, read 16:59 UTC); only seeds 1102–1103 launched at 21:03 UTC (FOCUS:123, :131; LED-L).
   - §4 and U4: "as OLMo's route" was wrong. OLMo's frozen route after a failed noise gate is "(b) take the fallback" (PREREG:3, :328, :364; FOCUS:52, :125 item (7)), not "review". U4 is re-stated as the Llama analog.
   - §2 row 1: PREREG:20 does not state the LR; the source is FOCUS:158 and REC. Row 21: engine X is in FOCUS:81-82, not :77.
   - §8: the caveat placement is FOCUS:138 (c); FOCUS:142 was the lead's per-sentence proposal that :138 settled. ICML moved to revision 6 during the review, so ICML citations are re-pinned (decision 24 → :238; decision 25 → :239; the blind read's group size → :653).
   - §10 P-L2: PREREG:261 gives rounded values; the note now says the script reproduces them to their rounding.
   - §6.1: "3 pp is about 2 binomial SEs" → about 1.8 SEs.
   - §13: the "keeps the money rules in force" reading of the 16 Oct instruction is the lead's (I) reading in FOCUS:76, not the user's words.
2. **New findings.**
   - B12: READ refuses Llama's untuned unit, which was made under the LR 1e-4 recipe (READ:1300-1309; its job.json). This is a reading-rule change, not a constant.
   - B13: no per-arm judge files exist yet for Llama's Gate A units (file listing).
   - §0, §5.1 and U0: a much cheaper scope (W0) exists, and RP names Llama-1B's replication as the first 1B cut. The conflict with FOCUS:240 ("tested on Llama") is stated.
   - §0 and L11: RP uses "Gate B-lite" for a 7–8B transfer check.
3. **Evidence strengthened or weakened.**
   - §6.1: a counts-only re-count confirms the same-seed tracking on all three components (screen, capped, short-only).
   - §6.1: a shared-seed G1 model shows that rule (a) blocks DIFFUSE in every model. Rule (b) is enough only if unit arms move answer endings as little as R arms do. Rule (c) holds at a unit-arm SD of 1.5 pp but not at 3 pp.
   - §6.1: a headroom table shows that (c) gives Llama about OLMo's headroom.
   - §6.1: the relative-bar alternative is re-assessed, because R_4 and R_5 exist at seeds 1104–1105.
   - §6.1: the "Limit" paragraph is added (TOO CLOSE by G1 stays likely if unit arms vary).
4. **Hidden costs and risks added.**
   - The length control's expected saving (about $2–4) is now stated against its planning saving ($11.77).
   - OLMo's length control speaks for Llama only on the same unit.
   - 66 min is the strict analog of OLMo's 52-min rule.
   - Llama's lost a0 adapters mean train-only re-runs for stage-2 references (B11).
   - The token must be rotated to read-only (B3).
   - `probes.py`'s Llama ladder points at LR 1e-4 recipes (B2).
   - The effort estimate rises to 2–4 developer-days plus a review round.
   - The noise mismatch in the held-out test (§15 item 7); OLMo's τ_L (0.0067) beside Llama's.
   - The re-costing rule's scope (U5) and the stage-boundary "stop and ask" (FOCUS:256).
   - RP's 23 Nov latest start for the Llama replication (§13).
5. **Rules tightened.**
   - Transfer test: one unit (OLMo's top LOCALIZED unit), so one test. A second unit only report-only or under Holm; the pre-review text ran up to two tests at 5% each with no correction.
   - The OLMo R-arm answer-end counts join the list of OLMo Gate B values seen before the freeze (§14).
   - P-L5 and P-L6 are labelled as written after OLMo's wave-0 values were seen.
6. **New decisions.** U0, L9–L13. U1, U2, U3, U4, U5 and U8 were revised.
7. **Late sources.** A mock methods review (MRA, commit 5a96acd) landed during the review. Its points on the replication rule (MRA:198) and the one-menu held-out test (MRA:252-256) are added to §9 and §15 (L13). It is not a decision. W1's wave-1 need ($37.56) and W0's transfer-pod need ($13.40) were computed with the kit's functions (EV `scope_money_out.txt`).
8. **Unchanged after checking.**
   - The simulation tables (every cell matched its output file).
   - The money tables (matched the kit-copy output; the OLMo check gives $78.45).
   - The answers-end counts, the fingerprints, the locks, the recipe diff, the pick_F and P-L2 counts, τ_L for Llama, and the certificate pair.
