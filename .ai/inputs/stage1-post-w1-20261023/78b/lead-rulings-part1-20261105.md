# The lead's Part 1 rulings for the 7-8B tier (GI X, 5 Nov 2026; clock read 13:20 UTC)

Written by General Implementation X (the main-study lead) as T1 of the checked 7-8B readiness plan
(`78b/readiness-20261105/78b-readiness.md`, "the plan"; its check `78b-readiness-check.md`, "the check", governs where
they differ). Each item below is **a lead ruling under the user's delegation** (16 Oct: "stop asking me for approval
and go ahead and do these things"; 17 Oct: "keep the more ambitious one always but always open to fallbacks"; the
check's C13 list), with its basis and its pre-set fallback and trigger. Nothing here authorizes a run or a spend:
every 7-8B pod starts only on new money in the account (MONEY `lead_reading[0]`; addendum §36; the $6 reserve, the
$10/h limit and the in-pod caps stay).

**What these rulings read.** No 7-8B repair arm has run. No Llama-3.2-1B repair arm has run. The rulings use the
pre-stage-1 nuisance values (Gate B wave 0a, the side probes' a0 spreads) and the 1B stage-1 reading only where §16
labels it. **Short names** as the plan's: P78 = `research/review/2026-10-17-icml-78b-prep/78b-preregistration-DRAFT.md`;
KCR = `.../78b-kit-cap-rule.md`; PR4 = the frozen stage-1 pre-registration
`research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md`; DOSE =
`reading/user_yes_s4_dose_arm_20261101.json`; MONEY = `reading/user_answer_78b_money_20261101.json`; FOCUS entries are
cited by title and recorded time (line numbers move as entries are added).

**What still needs the user (C13):** (1) the money in the RunPod account; (2) the HF token in the Mac environment at
each Llama launch; (3) a yes by pod name before any stopped 7-8B pod is deleted (after a verified backup); (4) H (a)
or (c), only if the user wants either one (ruling 4). Everything else below is decided and is reported, not asked.

---

## 1. S, the analysis scale: S-P (HB-C per family), S-U as the pre-registered sensitivity

- **Ruling.** The 7-8B reading uses the frozen stage-1 model's form, HB-C, per family (PR4:230-239): U(a, j) = μ_a +
  s_{c(a), j} + e(a, j); one seed effect per design cluster, the full-corpus cluster {a0, S1, S3, S4} (38 steps) and
  the removal cluster {R, A1, L1, H1} (33 steps); σ²_a per arm by REML with PR4's floors and stop rule (LN-35); the
  paired mean on the common seeds; the prompt part; Satterthwaite df. The seed rule reads σ̂_pool on the paired scale
  (P78:119). **S-U** (the difference of arm means, variance pooled over arms, Welch as a check) is printed beside
  every primary contrast as the pre-registered sensitivity.
- **Basis.** Consistency with the frozen 1B model (PR4:233, adopted before any stage-1 outcome); Gate B's noise model
  is paired; the 1B pairing evidence (σ_eval,0 1.28 pp seed-matched against 2.16 pp for R-arm pairs; Gate B wave 0a);
  the cost of no pairing gain is small (SE about 7% worse; P78 §4); only S-P can bring 7-8B near the 5 pp target at 6
  seeds (P78 §4). The check's C14: P78 marks S [USER]; it is recorded here as the lead's ruling, not as "already
  decided".
- **Fallback.** None needed: S-U is reported in every case. PR4's own floor and stop rules handle REML edge cases.

## 2. Seed layout under S-P (P78 [LEAD] item 10)

- **Ruling.** Every plan uses PR4's layout form: method arms at the plan's seeds from 1102; R at 1101 to the last
  method seed; **a0 at 1101-1107 in every plan** (seven cells; P78:159's edit, so P4 has six shared seeds). No R seed
  beyond the last method seed is run.
  - plan A: methods 1102-1107; R 1101-1107; a0 1101-1107 (as stage 1: PR4 "50 primary cells").
  - plan B9 (PR4:161's plan-B form with 9 method seeds): A1, H1, S1, S4 at 1102-1110; R 1101-1110; a0 1101-1107.
  - H (b): A1, H1, S1, S4 at 1102-1113; R 1101-1113; a0 1101-1107.
- **Basis.** Under S-P an R cell without a method partner enters no primary estimate (PR4 "Seeds without a partner");
  P78's R_8 (plan A), R_11-12 (B9) and R_14-16 (H (b)) served S-U only. Stage 1 at 1B ran R at 1101-1107 (PR4). This
  drops 1-3 R runs per family from P78 §5.4's counts (plan A 44 → 44 with a0 1107 in place of R_8; B9 54 → 53;
  H (b) 70 → 68), so P78's money figures stay upper bounds.
- **Fallback.** None; the counts only fall.

## 3. SR, the seed rule; the thresholds; the review ceiling; SR-2

- **Ruling (SR).** σ̂ = σ̂_pool from N (4 df), pair scale. σ̂ ≤ 4.5 pp → plan A (P1-P6, SESOI 5 pp); 4.5 < σ̂ ≤ 6.0 →
  plan B9 (P1, P3, P6 primary; P2, P4, P5 secondary at block A's three seeds); σ̂ > 6.0 → branch H (ruling 4). The
  **review ceiling** is kept: if the plan's removal MDE exceeds 2 × its SESOI, there is no 7-8B primary family; the
  units that ran are reported descriptively and the user decides the next step (P78:177). **Thresholds 4.5 / 6.0 are
  kept** (PLAN-S's numbers at both sizes); the text states that under S-P they mean paired MDEs of about 6.4-6.5 pp
  (P78:168). The rescaled 4.22 / 5.56 are not adopted.
- **Ruling (SR under [C]).** σ̂_pool (both families' N, 4 df) gives the provisional plan; SR-2's σ̂_A from the chosen
  family's own block-A units decides block B. Without SR-2: the chosen family's own σ̂_F (2 df) (P78:119).
- **Ruling (SR-2).** **Adopted, on one condition**: the 7-8B kit's record-done step prints no block-A U value, and
  `scripts/scale78b/blinded_sigma.py` prints σ̂_A and its df only (a test holds that output byte for byte; plan risk
  12). σ̂_A: S-P, √2 × the residual SD of the arm + seed model per cluster, pooled over the clusters and the families
  that ran (about 15 df per family). Block B's design is the seed rule applied to σ̂_A; it replaces N's value; both
  directions are allowed (P78 §5.3). The gate budgets the worst plan SR-2 can reach (H (b)) (P78:203; C3).
- **Fallback (SR-2).** Trigger: the blinding test is not verified before block A's first pod. Then SR-2 is not
  adopted and N's value decides alone (P78:202). `blinded_sigma.py` is built with T4's block-A part (window 2),
  not in this week's round.

## 4. H, the high-noise branch: (e), money-contingent, with (b) first

- **Ruling.** If the seed rule gives branch H: **(b)** on each family that runs (P1, P3, P6 primary at 12 method
  seeds, ruling 2's layout; SESOI 5 pp; P2, P4, P5 secondary at block A's three seeds with one-sided bounds), if the
  account after the gate covers (b)'s extra on those families. This keeps the 1B scientific target (P78 §6).
- **Pre-set fallback chain (money only; a funding event is not an outcome, P78:241).** (i) Under [B], if (b) is
  covered on one family but not on both: the tier runs [C] on F1 at (b) (the gate's B → C cut). (ii) If (b) is not
  covered on any family: **(d) review**: no 7-8B primary family; the units that ran are reported descriptively.
- **Not in the lead's chain: (a) and (c).** Both change D5's "SESOI 5 pp" at 7-8B, so only the user can choose them
  (P78:243; RP decision 3; C13). If the user names (a) in place of (d) before N launches, it is recorded as the
  user's choice; if later, it is disclosed as made after N's reading.

## 5. F, the family under [C]: F1 OLMo-2-7B

- **Ruling.** F1, OLMo-2-7B, fixed now, before N.
- **Basis (P78 §8).** It is cheaper per arm ($2.94 against $3.93 expected at 4 per pod; KCR:183-188); it reuses
  SEAL's edit files byte for byte (the same manifest `9ed61826…`), its e1 adapters are on the Mac (adapter scaling
  needs no retrain) and its recipe-G units are at the main LR; it has no answers-end issue and no gated download.
  TC's "cleaner transfer test" no longer counts (TC does not run, ruling 6).
- **The trade-off, stated in Part 1.** Llama-3.1-8B is the published setting's model, and its only noise evidence is
  lower (per-arm a0 SD 1.06 pp on 1 df against OLMo-2-7B's 6.36 pp on 2 df; not significant, p ≈ 0.12). Under [C]
  with F1 the Llama replication at 7-8B is lost.
- **Pre-set technical fallback.** Trigger: two OLMo-2-7B pods stop before any arm completes because of a memory
  failure in generation (the preflight's `generation_memory_ok` or an out-of-memory crash; OLMo-2-7B generates at
  99.3% of the card, KCR:62). Then F2 (Llama-3.1-8B) replaces F1 for [C], labelled.

## 6. TC, the transfer check: does not run

- **Ruling.** TC does not run: the frozen 1B Gate B reading said TOO CLOSE, a planned branch (README:94; "GATE B
  CLOSED", FOCUS, recorded 2026-10-23T05:26 UTC). P78 §7's rule is kept in Part 1 for the record; the paper says
  localization was tested at 1B only (RP:91). No transfer reader is built; the optional extension is moot.

## 7. RP decision 5: reuse the side project's engine-X units

- **Ruling.** The seven engine-X units of P78 §2.1 (OLMo-2-7B untuned and a0 1101-1103; Llama-3.1-8B untuned and a0
  1101-1102) are main-study units, pinned by their `COMPLETE.json` SHA-256 (P78:48-57), under P78:74-78's four
  conditions and EM-1 (engine X, the family's training identity, the family's manifest, the compared environment).
- **Pre-set fallback.** Trigger: for a family, block 0's environment check fails, or the X retrain of ruling 10
  differs from the side unit's fingerprints. Then N is re-read with the a0-free fallback (P78:121), and that family's
  a0 at 1101-1103 re-runs in the new environment before any paired contrast (+3 runs, about $9-12; P78:333).

## 8. The Llama-3.1-8B seed-1103 rule ("the rung stays")

- **Ruling.** Llama-3.1-8B a0 at 1103 runs in N under the main config (`74758af1…`, LR 5e-5). It is an a0 unit for N
  and for the comparison. It is read by the frozen family-probe bars and reported with the 3-seed Gate A mean. Its
  outcome never changes Llama's rung (the user's 11 Oct "at the edge" decision): a rung change after an outcome
  would be a choice after an outcome (P78:100).

## 9. The gate (RP decision 2, restated)

- **Ruling.** The gate is the day the new money is in the account (expected about 20 Nov), after N's reading. It
  reads the money and N only, never a 1B outcome. **B** if the account covers B's primary comparison at the plan the
  seed rule gives (with (b)'s extra if H fires), with the references, scorer passes, judges and idle storage, and the
  confirmation money is in sight (in the account, or the user has said it will come by about 1 Dec); **else C on F1**.
  The S4 add-dose arm is outside this test (ruling 12). If the money is not in the account by about 1 Dec, the gate's
  re-check: C, or B without the 7-8B confirmation, by RP:138's cut order.
- **The earmark.** The new money is for the 7-8B tier (MONEY `question`). Stage 1c, the human label check and stage 2
  start on their own money or on the user's word; the lead says so when the money arrives.

## 10. The engine for paired 7-8B arms (P78 [LEAD] item 11; the check's C4)

- **Ruling.** Each family's a0-1101 retrain (train only, recipe S_78, to q and e1) runs first on **engine Y**, on its
  own single-job pod with an explicit cap (KD6; it is the first Y pod of KD9).
  - Y fingerprints (q and e1 adapter and optimizer) equal the side unit's: Y = X for that family; every 7-8B arm, B+Qi
    included, may run on Y; the A1 pass runs on the engine that trained its states (EYD:81).
  - Y differs: the **pre-set second job** is the X retrain, on a pod of the same image packed with engine X. X equal:
    paired arms stay on X; B+Qi runs on Y as an unpaired reference, labelled. X differs: the pod or environment
    differs, and ruling 7's fallback applies.
- **Basis.** A Y retrain that differs cannot say whether Y or the pod caused it (C4); only an X mismatch triggers
  P78:121's fallback.

## 11. The kit (KD1-KD11, KCR §12; the check's C1, C7, C8, C11, C12, M1, M3)

- **KD10, the route: (ii).** Copy `runkit/stage1-olmo/` to `runkit/stage1-78b/` (the original untouched: stage 1c and
  stage 2 still read it); per-family constants from `rules_78b.py`; the gated-token launch path ported from
  `runkit/family-probe/launch.py` with its own tests and a separate review. Block-0 subset first: `arm` (R_1-R_3 under
  the family's main config), `a0_arm` (Llama 1103), `retrain` (ruling 10), and the pre-block-A scorer kinds
  `untuned_answers`, `o_only` / `regenerate` for both untuned units (M1: the 7-8B untuned units need stage 1's O and L
  evaluation), the anchor job, `rep_pass` (A1), `l1_scan`, `classifier`, `c0`, each single-job with an explicit cap
  (C1); `s_obs` after each arm; the free-space check; record-done prints no block-A U (SR-2). `plan_tool.py init-block
  0` prints the need of N's pods, the retrain pod and the scorer pods separately (M3).
- **KD1.** The M-cap rule (KCR §4). Fallback (KCR alternative 1, the Gate B rule with 7-8B measured constants) only if
  T2 is not verified by 12 Nov.
- **KD2.** At most 4 counted arms per pod on both families (caps 10.5 h OLMo, 12.5 h Llama). Basis: per-arm cost 18-23%
  below one per pod (KCR §8); the stage-1 kit's value (`MAX_ARMS_PER_POD = 4`, a lead ruling LN-27 under the
  delegation, not a user confirmation: C11). Fallback: 3 on Llama (cap 9.75 h) if block 0's 4-job Llama pod exceeds
  its requirement or reads `s_obs` > 1.15.
- **KD3.** KCR's margins: 1.15 on the measured job; SCORE_ALLCAP 1,250 s; 48 min pod overhead; refusal at s > 1.15
  and at `s_obs` > 1.15.
- **KD4.** `GATE_B_HOLD_USD = 0`. Reason string: "Gate B closed 23 Oct (FOCUS 'GATE B CLOSED', recorded
  2026-10-23T05:26 UTC); its last judge pods deleted 31 Oct" (C8). KCR test 10 is adapted to a zero hold.
- **KD5.** 50 GB volumes with a free-space check before each job; the state rule of the OLMo 3 kit (`states_tool.py`:
  pull the e1 states, verified backup, then the user's yes by pod name before any delete; the kit has no delete
  command); an idle-storage line in each block's need.
- **KD6.** Every kind other than `arm` and `evalonly` runs on a single-job pod with an explicit E cap until it is
  measured (A1's pass at RP:43's 6-11 h is a 16.5 h cap at most), then the basis is updated by a recorded lead step.
- **KD7.** Working copies `tmp/family-probe-s78-<family>-<block>/` (for example `tmp/family-probe-s78-olmo2-7b-0/`);
  `KITS_GLOB` unchanged, so the stage-1 kit's frozen `budget.py` (`family-probe-*`) sees every 7-8B cap (C7).
- **KD8.** New configs under `experiments/safety_selection/configs/` are committed additions by explicit path (Gate B
  is closed; C8, C12); after each commit the lead re-checks the engine identity `472fc7f6…` and the stage-1 S1 pins.
- **KD9.** The measured basis is re-measured on the first Y pod (ruling 10's retrain) before Y carries a block.
- **KD11.** The in-pod speed check `s_obs` is adopted (KCR §4).
- **N's layout (P78 [LEAD] item 9).** OLMo: one pod, 3 jobs (cap 8.5 h). Llama: one pod, 4 jobs (cap 12.5 h). In
  parallel. Need about $56 with the contingency (KCR:177). Fallback: if a pod stops before its last job, the rest
  requeue on a new pod (the kit's requeue path).

## 12. The S4 add-dose arm (the user's "Yes, add it", DOSE)

- **Name.** "S4 add-dose" (C2: stage 1 uses "dose" for the random-removal dose curve). Doses **S4_96** and **S4_192**.
  Contrasts **AD1** = U(S4) − U(S4_192) and **AD2** = U(S4) − U(S4_96) (PR4's sign: positive = the larger dose
  restores more; "AD" because PR4 uses "D1" for a design and FOCUS uses "D5" for the user's decision).
- **Construction (per model and manifest; C6).** The family's own untuned model's greedy answers to the S-pool minus
  S1, in S4's sealed order (`stage1-s4-v1`, 512 prompts in 32-prompt chunks), kept only if ended, REFUSAL-OPENING by
  LEX, non-empty and accepted by `encode_train` (PR4 S4 row); S4 = the first 48 kept, S4_96 = the first 96, S4_192 =
  the first 192 (nested). One untuned-answers pass per family makes all three (the S4 job's stop rule moves from
  "the chunk that holds the 48th" to "the chunk that holds the 192nd"; the first 48 are unchanged).
- **The 1B keep rate (M2; read 5 Nov, counts only).** The 1B pass answered 64 candidates in 2 chunks and kept 57
  (26 of 32, 31 of 32; 7 not refusal-opening; 9 kept after the 48th): 89%. At that rate 192 kept rows need about 216
  of the 512 candidates. Source: `tmp/stage1-olmo/retrieved/a-1/tree/job-0/untuned/untuned_answers_record.json`, read
  by exact path after its SHA-256 check (`5e69b09c…`, the value d3-build.json names); only the S4 list's chunk and
  drop counts were printed.
- **Fallback.** Fewer than 192 kept after the whole list: the top dose is all kept rows, counted and reported (DOSE).
- **Seeds (the ambitious default with its fallback).** **6 seeds (1102-1107)** if the money after the gate covers B's
  or C's primary needs (ruling 9) plus 6 seeds; else **3 seeds (1102-1104)**; else the arm is the first secondary item
  cut (DOSE `pre_set_fallbacks[1]`). Written at the gate from money only.
- **Reading (C2).** Secondary. Outside Φ, outside the Holm family of P1-P6 and outside the primary HB-C fit. AD1 and
  AD2 by the paired-mean estimator on their common seeds with S4, plus the prompt part (PR4's P6-under-plan-B form,
  PR4:281: a paired t on the pairs plus the prompt part), in their own fit. Labels *better / equivalent /
  inconclusive* at the 7-8B SESOI (5 pp) with one-sided bounds, as PLAN-S §5.3 does for secondary arms (P78:238). A
  monotone-dose summary (the three doses' means) is reported. Against the model-level references within the O and L
  limits by the frozen dominance rule's form: "does the top feasible dose beat every reference?". A dose that breaks
  O or L is reported *infeasible*.
- **Compute (stated, not corrected away).** S4_96: 4,896 rows → 39 steps; S4_192: 4,992 rows → 39 steps; S4: 4,848 →
  38 (128 rows per step). The step counts and padded-token totals are printed beside AD1 and AD2.
- **Where it runs.** With block B, under the family's main config, like every add arm. Cost about $49 (3 seeds, both
  families) to $99 (6 seeds) (plan §4).
- **Label in Part 1.** "Added after the OLMo-2-1B stage-1 reading (the user's yes of 1 Nov 2026), because S4 was the
  best feasible repair there but did not reach the model-level references' U; confirmatory at 7-8B because no 7-8B
  repair outcome existed when it was added."

## 13. Predictions (written before N and before any 7-8B repair outcome; they gate nothing)

- **N1 (mean r_F = U(a0) − U(R_j), per family).** Point +2.5 pp on each family; 80% interval −1.5 to +6.5 pp. Basis:
  1B Gate B read +2.5 pp (SE 1.06) against a linear-dose 5.6 pp (the loss plateaus early; saturation), and E/8 would
  be 5.5 pp (OLMo-2-7B) and 6.7 pp (Llama-3.1-8B).
- **N2 (σ̂_pool, pair scale).** Point 4.5 pp; 80% interval 2.5-8.5 pp. Basis: the 1B pairing ratio (0.49) applied per
  family gives about 4.4 pp (OLMo-2-7B) and 0.7 pp (Llama-3.1-8B), pooled about 4.5 pp; applied to the pooled 5.83 pp,
  4.0 pp; no pairing gain, about 8.2 pp. The seed rule's plan: A about 0.5, B9 about 0.3, H about 0.2.
- **The S4 add-dose arm.** AD1 point +5 pp (80% interval −1 to +12); AD2 point +2.5 pp (80% −2.5 to +8); O rises with
  the dose (+1 to +6 pp at S4_192 against S4); the top dose stays within the O limit with probability about 0.6 per
  family; *better* for AD1 has probability about 0.2 at 3 seeds and 0.3 at 6.

## 14. Part 1's file and its freeze

- **File.** `research/experiments/2026-11-05-78b-preregistration-part1.md` (DRAFT until the freeze). Part 2 is a
  separate file, frozen before block A; its scorer section is committed with code hashes before any scorer output
  is read (P78:367; M4).
- **Freeze.** After the Llama G1 $0 check (P78 [LEAD] item 7) and the reviewer's read against the labelled list
  (ruling 16): commit by explicit path, its SHA-256 in FOCUS, `scripts/stage1/commitments.py check`; before block 0's
  first `launch.py` and by about 19 Nov.
- **Records.** These rulings, the G1 check's output and later 7-8B records go under
  `.ai/inputs/stage1-post-w1-20261023/78b/` (M5). The Llama sealed set goes to
  `.ai/inputs/scale-78b-sealed-llama3-20261105/` (named by manifest; R and unit files serve stage 2 too; S3, S4 and
  the dose edits are per model, C6).

## 15. This week's build round (T2, T3, T5, T6a) and the order after it

- Build round now (Fable builders in detached scratch worktrees, one adversarial verifier per track, one fix round,
  a re-verify; agents never change git state; the lead merges by explicit paths after its own suites): A = T2; B =
  T3 (with C5's d = 6-10 equality against stage 1's draws); C = T5 (the noise reader), T6a (the two recipe-S_78
  configs) and the Llama G1 $0 check; D = the Part 1 text from these rulings.
- After T2 merges: T4's block-0 subset (ambitious: start before 12 Nov if usage allows, else in 12-19 Nov); T6b/c;
  the Part 1 freeze; dry packs 19-20 Nov.

## 16. Choices made after a stage-1 result (Part 1 labels each one)

1. The S4 add-dose arm and its doses (ruling 12): motivated by P6 and the best-feasible-repair result.
2. Keeping P1-P6 all primary at 7-8B although P2, P3 and P5 read *equivalent* at 1B: considered and rejected because
   dropping arms by their 1B labels would be a choice after a result.
3. Predictions N1, N2 and the dose prediction: written after the stage-1 reading (the date is stated).
4. S, SR-2, H, F, the thresholds, the seed layout and the gate: decided after the stage-1 reading; none reads a 1B
   repair outcome (S follows the model frozen before stage 1; F reads cost, files and gating; H reads money and D5;
   SR reads N; the layout follows PR4).
5. The confirmation's pick rule at 7-8B: the frozen stage-3 rule (the two largest |t| among *better* or *worse*)
   per family; the 1B pick (P6 then P1) never selects 7-8B contrasts.
6. TC's non-run follows Gate B's TOO CLOSE, a planned branch.
7. Any use of stage 1's HB-C arm variances in 7-8B power planning is labelled "read from the stage-1 reading"; these
   rulings use only the pre-stage-1 values.
8. The starting rule: the 7-8B tier starts on money in the plan's order, never because P6 or P1 read *better*.
9. The 1B S4 keep rate (ruling 12, M2): a θ0 count from stage 1's untuned-answers pass, used only to size the dose
   arm's fallback.
