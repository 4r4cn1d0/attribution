# 7-8B tier readiness: a build plan for the lead (scout report)

Written 2026-11-05, 09:03-09:19 UTC (clock checked with `date -u` at 09:03, 09:11 and 09:17 UTC), by a read-only scout for
the main-study lead (GI IX). Main checkout `/Users/spiderishi/Coding/attribution`, branch
`stageb-costs-and-recovery-safeguards-20261003`, HEAD `d5e176f` (M). Read-only: no pod, spend, network, install, git
state change or agent. No folder under `tmp/stage1-olmo/`, `tmp/hlc*/`, `tmp/stage1b/`, `judges*/`, `seals/`,
`retrieved/`, `units/`, `eval/` was opened; no answer, label, judge, hidden-bank or selector file was opened; the
probe records read are `tmp/family-probe-sp-*/hosts/*/{finished,create-intent}.json` timing fields only (M). The
only file written is this one.

**Tags.** (R) read, with path:line. (M) measured by a read-only command. (I) inference. (E) estimate, basis stated.

**Short names.** P78 = `research/review/2026-10-17-icml-78b-prep/78b-preregistration-DRAFT.md`. KCR =
`.../78b-kit-cap-rule.md`. XL = `.../32b-70b-design.md`. EYD = `.../engine-round-Y-design.md`. CALC = `.../calc/`.
RP = `writing/paper/2026-10-17-icml-replan-PROPOSAL.md`. SPF = `docs/study-plan-full.md`. README = `README.md`.
F Ln = line n of `research/FOCUS.md` at `d5e176f`. NEXT = `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md`.
MONEY = `.../reading/user_answer_78b_money_20261101.json`. DOSE = `.../reading/user_yes_s4_dose_arm_20261101.json`.
PR4 = `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` (the frozen
stage-1 pre-registration). S1B = `.ai/briefs/stage1-commitments-build-20261016.md`. KIT = `runkit/stage1-olmo/`
(the stage-1 kit, B15). RULES = `runkit/stage1-olmo/stage1_rules.py`. O3K = the OLMo 3 probe kit
`runkit/family-probe-olmo3/` in the scratch worktree `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-heuristic-ramanujan-ffe737/fc95250c-7482-48ff-a05e-567068089009/scratchpad/o3/ws-all`
(untracked there at `e89d74f`; M, `git status`). SEAL = `.ai/inputs/gate-b-sealed-20261008/`, BLD = its
`build_sealed.py` (SHA-256 `80cb8944…`, M). SS = `experiments/safety_selection`.

---

## 0. Summary (the verdict is "plan")

1. **Nothing of the four ruled items exists as code or text that can be frozen (M).** No `runkit/stage1-78b/`, no
   `scripts/scale78b/`, no Llama sealed folder, no 7-8B pre-registration under `research/experiments/` (M: `find`
   over `runkit scripts .ai/inputs research/experiments docs`, the only "78b" hit is MONEY). What exists is two
   reviewed designs (P78, KCR), their calculations, the seven reusable engine-X 7-8B units, the three OLMo-2-7B
   e1 adapters on the Mac, both prepared manifests on the Mac, both main-recipe configs, the frozen sealed builder
   with its `draw_r`, and a stage-1 kit (11,464 lines, 378 test functions) that already names both 7-8B models
   (§1).
2. **Two findings change the designs.** (a) The frozen stage-1 pre-registration already analyses seeds as blocks
   (PR4:233, model HB-C: one seed effect per design cluster, fitted by REML), so P78's open decision S is settled by
   consistency: the 7-8B reading uses HB-C's form, and the seed rule reads the paired-scale σ̂_pool (§5.4). (b) Gate
   B is closed and its last pods are deleted (F L104; the reading is done, F L91), so KCR's `$83.91` hold and P78's
   "until Gate B's last kit pod" T4 freeze on `experiments/` and `scripts/` have lapsed; what stays frozen is the
   stage-1 S1 package by its pins (KIT README, round 3b-3c) (§1.4, §6).
3. **The order that gets block 0 ready soonest** (§2): T1 Part 1 decisions and text (lead, in parallel with
   everything) → T2 the cap rule and measured basis → T3 the Llama sealed set → T4 the kit's block-0 subset (a copy
   of the stage-1 kit with per-family constants, plus the family-probe gated-token launch path) → T5 the noise reader
   → T6 the recipe-S_78 configs, the a0-1101 retrain and the scorer rules (Part 2's block-0 part). About 55-95
   builder hours (E) across the 5-12 Nov and 12-19 Nov usage weeks; block 0 = 7 runs on two pods, 7-9 h wall (E).
4. **What needs the user** (§3): the money (an expectation of about $900-1,300 by about 20 Nov; balance $22.64 on
   2 Nov, F L81); RP decision 5 (reuse the side units as main-study a0) and the Llama seed-1103 "rung stays" rule;
   F (family for C), H (branch), SR-2, the S4 dose-arm seeds; the Llama-3.1-8B gated download (the token path
   exists in the family-probe kit, not in the stage-1 kit); and a yes to the kit route. No download of weights is
   needed on the Mac (the pods download; the Mac holds the prepared sets).
5. **Money with measured bases, no item counted twice** (§4): option B (both families, plan A or B9) about
   $640-900 by the gate plus $140-230 for the confirmation by about 1 Dec; with branch H(b) on both families about
   $830-1,140 plus the confirmation. Option C with OLMo-2-7B about $270-390 plus $70-120. The $900-1,300 covers B
   at plan A or B9 with its confirmation, and H(b) without it; not every top end at once (E, I).
6. **Part 1's outline** (§5) now includes the S4 dose arm (two doses, 96 and 192 kept rows, nested in S4's 48; at
   3 seeds as a secondary arm, 6 if money allows; about $49-99 for both families), with the label "added after the
   OLMo-2-1B stage-1 reading", and names every other choice that is made after a stage-1 result (§5.12).
7. **Biggest risks** (§6): the money is an expectation; builder usage is shared with the OLMo 3 verify round; the
   Llama G1 coherence risk ($0 check never done, M); OLMo-2-7B generates at 99.3% of the card; the kit copy is the
   one large build and the one with security-relevant code (the token path); the compute-matched framing of the dose
   arm (39 steps against 38).

---

## 1. What exists and what is done

### 1.1 Rulings, records and the plan

| Item | Status | Source |
|---|---|---|
| The user expects new 7-8B money, about $900-1,300 by about 20 Nov, from a source other than BlueDot | an expectation, not money in the account; "Yes, likely" at 09:16 UTC 1 Nov | MONEY `user_words`, `what_it_is` (R); F L98 (R) |
| Ruling (1): option B stays the default; the gate at about 20 Nov picks B or C by the re-plan's rule | in force | F L98 (R); MONEY `lead_reading[1]` (R) |
| Ruling (2): the $0 preparation is a planned step; its four items; Part 1 frozen before block 0's first pod | in force; nothing built yet | F L98 (R); MONEY `lead_reading[2]` (R) |
| The S4 dose arm goes into the stage-2 and 7-8B pre-registrations | the user's "Yes, add it", 1 Nov 23:05 UTC; draft construction in the record | DOSE (R); F L86 (R) |
| The plan's order after the reading: 1b (closed, a null), 1c, the human label check, stage 2, OLMo 3 (B only), the 7-8B tier, stage 3, Alpaca, 32B | the 7-8B tier is row 6; each row starts on money, never on a result | NEXT:3, :73-84 (R) |
| The stage-1 reading is done (OLMo-2-1B, plan A): P1 better, P2 equivalent, P3 equivalent, P4 worse (U), P5 equivalent, P6 better; best feasible repair S4; family 1b: no repair beats every reference | sealed; third stamp made | F L91 (R) |
| Stage 1b's pilot said stop (the planted cause +3.94 pp, below the 5 pp floor) | closed; row 1 of NEXT step 2 is closed | F L84 (R); NEXT:3 (R) |
| The transfer check TC | does not run: Gate B read TOO CLOSE, a planned branch | README:95 (R); SPF:502 (R) |
| Balance | $22.64 at 09:03 UTC 2 Nov, nothing running, storage $0 | F L81 (R) |
| Usage | all-models 0%, Fable 0% at 09:02 UTC 5 Nov; next reset 12 Nov 09:00 UTC; the OLMo 3 verify round and this scout launched 09:03 UTC | F L74 (R) |
| The lead's rule on priority | if builder time or usage runs short, the 7-8B preparation goes first (OLMo 3 is the first 7-8B model cut) | F L98 (R) |

### 1.2 Designs and calculations (all DRAFT or PROPOSAL; none adopted, none frozen)

| Item | What it holds | Source |
|---|---|---|
| P78, Part 1 draft (477 lines, two Opus passes, adversarial review in place) | N, S, SR, H, TC, F, EM-1..5, T4; 12 [USER] and 15 [LEAD] decisions; recommendations S-P, SR-2 yes, H (e) with (b) first, F1 OLMo-2-7B, TC without the extension | P78:1-13, :17-26, :385-415, :473 (R) |
| KCR, the measured cap rule "M-cap" (302 lines, reviewed) | the rule, its constants from 17 measured units, caps 10.5 h (OLMo) and 12.5 h (Llama) at 4 arms, per-arm costs, the kit routes (i)-(iii), tests 1-15, decisions KD1-KD11; recommends "the rule now, the kit later" | KCR:11-20, :88-128, :132-143, :210-228, :262-272 (R) |
| CALC: 10 scripts and outputs | power and MDE tables, the seed rule's operating characteristics at 2/4/15/19/30/38 df, the F-ratio, the TC simulation, the environment-and-manifest check (13 compared fields equal across all 7-8B and 1B units; the two manifests' groups and member lists equal) | CALC `power2_out.txt`, `rule_oc2_out.txt`, `review_calc_out.txt`, `env_and_manifest_check_out.txt`:1-17 (R) |
| XL (32B design) | shares the kit shell question (KD10); the 1 Dec go/no-go; not a 7-8B item | XL:9-20 (R); README:113 (R) |
| EYD and engine Y | Y built and frozen 23 Oct; C1 certificate passed 27 Oct (16 of 16 counted files equal against R_1101 on X); B+Qi "partly binding" at 1B | F L168, L133 (R); README:85-86 (R) |
| SPF §9 and README's 7-8B tier | the full digest of P78 and KCR; "the draft's freeze deadline has lapsed; the user's decision replaces it" | SPF:490-521 (R); README:90-95 (R) |
| RP schedule and money | latest starts: block 0 9 Nov, gate 20 Nov, block A 23 Nov, block B 3 Dec, confirmation 14 Dec, results frozen 4 Jan, abstract/paper 16/22 Jan (E in RP); F2 "B about $900-1,300 more; C about $550-800 more" | RP:97-110, :104, :136 (R) |

### 1.3 Inputs in hand (reusable at $0)

| Input | State | Source |
|---|---|---|
| OLMo-2-7B untuned unit and a0 at 1101, 1102, 1103 (recipe B 1e-4, config `18cc31d7`, manifest `9ed61826`, engine X `472fc7f6`) | records on the Mac under `tmp/family-probe-sp-olmo2-7b-b-{a0,seed1102,seed1103}/`; U 11, 309, 234, 284 of 600 | P78:50-53, :58 (R); CALC `env_and_manifest_check_out.txt`:7-10 (R) |
| Llama-3.1-8B untuned unit and a0 at 1101, 1102 (recipe B 5e-5, config `74758af1`, manifest `c52a50af`, engine X) | records under `tmp/family-probe-sp-llama31-8b-{b-a0,b5e5-1101,b5e5-seed1102}/`; U 32, 347, 356 | P78:54-56 (R); CALC `env_and_manifest_check_out.txt`:4-6 (R) |
| The seven units' pod records (`hosts/*/finished.json`): OLMo outer job 114.6 (with the untuned evaluation), 103.9, 91.1 min; Llama 174.2 (with the untuned evaluation), 121.6, 123.6 min; cap intents 12.5 h (OLMo) and 8.5 h (Llama) | present; the values equal KCR §3's | M (`python3 -I`, timing fields only); KCR:72-75 (R) |
| OLMo-2-7B e1 adapters for a0 1101-1103 | on the Mac: `tmp/sp-repr/out/sp-olmo2-7b-b2-1101`, `sp-olmo2-7b-1102`, `sp-olmo2-7b-1103`; also in the release `backup-2026-10-17-mac-weights` | M (`ls`); P78:62 (R); F L189 (R) |
| Llama-3.1-8B adapters at 5e-5 | none on the Mac; the local `sp-llama31-8b-110x` are the LR 1e-4 units; the 5e-5 rung adapters were lost with the pods | P78:62 (R); F L210 (R) |
| OLMo-2-7B recipe-G units 1101-1103 (at the main LR) | in hand as the recipe-G reference; Llama's recipe-G units are at 1e-4, so Llama needs 3 new | P78:66 (R) |
| Prepared manifests on the Mac | `tmp/kt-prepared/prepared-kt-dolly-olmo2/manifest.json` `9ed61826…`; `…-llama3/manifest.json` `c52a50af…`; `…-olmo3/manifest.json` `8a196f6d…` | M (`shasum -a 256`) |
| The main-recipe configs | `SS/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json`, `study-kt-llama31-8b-r64-b5e5-mb2-20261010.json` present; also `…-olmo2-7b-r64-g-mb2-20261011.json`, `…-llama31-8b-r64-g-mb2-20261011.json` | M (`ls`) |
| SEAL's edit files and the builder | `SEAL/out/edits/` present; BLD `80cb8944…` with `draw_r(inputs, d)` at BLD:198; BLD pins the OLMo prepared folder and manifest (BLD:60-61) and stops on any other manifest (BLD:143-144) | M (`ls`, `shasum`, `grep`) |
| Gate B anchors and the judge launcher | `.ai/inputs/gate-b-anchors-20261008/{make_anchor_prompts.py,out}`; `scripts/gate_b_mac_judges/` (HarmBench and Granite pods; used for stage-1 blocks A and B) | M (`ls`); F L103 (R) |
| The stage-1 pre-registration's analysis model | HB-C: U(a, j) = μ_a + s_{c(a), j} + e(a, j); one seed effect per design cluster ({a0, S1, S3, S4} at 38 steps; {R, A1, L1, H1} at 33); σ²_a per arm by REML; the paired mean on the common seeds; Satterthwaite df | PR4:233-239 (R); `scripts/stage1_s1/reading/README.md`:20-21 (R) |
| S4's construction at 1B | the S-pool minus S1 in sealed order `stage1-s4-v1`, 512 prompts in 32-prompt chunks; θ0's greedy answers kept only if ended, refusal-opening by LEX, non-empty, accepted by `encode_train`; the first 48 kept | PR4:131 (R); S1B:210 names "the S4 candidate list length (256)" as a mutant line (R) |
| Stage 1's measured costs | block A $48.59 (the funding group's pod spend); block B $144.94 (21 pods $141.27 for 75.04 GPU-h; judges $3.67; cfy-1/2 $3.35 more); total $193.53 for the primary family at plan A | F L133 (R); F L103 (R); NEXT:15, :78 (R) |

### 1.4 The stage-1 kit as the model for a 7-8B kit (KIT)

- 24 files, 11,464 lines (M, `wc`); tests: 378 `def test_` across 9 files (M, `grep -c`); 124 of 124 mutants killed
  at B15 (SPF:619, R).
- Already names both 7-8B models: `probes.py` entries `olmo2-7b` (:40) and `llama31-8b` (:68), with the gated flag
  and the Llama tokenizer pin (:24-25) (R).
- The gated download path exists in `setup/download_models_stage1.py` (:13-23: "the gated path is kept unchanged and
  unused"; token in memory only; receipt without the token) (R). **Its `launch.py` has no token check or hand-over**
  (M: `grep -iE "gated|token"` on it prints nothing). The family-probe kit's `launch.py`:8-14 has the whoami check,
  the Range-request check and the stdin hand-over to `host.py`, recorded without the token (R); O3K's `launch.py` is a
  copy of it (O3K README, R).
- Job kinds: `KINDS` J1-J22 (RULES:599-601): `arm`, `a0_arm`, `c0`, `ref_eval`, `safe_lora`, `ref_train`, `retrain`,
  `a1_rescore`, `rep_pass`, `untuned_answers`, `l1_scan`, `classifier`, `similarity`, the certificates; `BLOCK_KINDS`
  per block (RULES:852-859) (R). These are the kinds the 7-8B blocks need; Gate B's kit had neither edit arms with
  references nor an a0 train-plus-evaluate kind (KCR:140, R).
- 1B pins throughout: `PROBE_KEY = "olmo2-1b"` (RULES:868); `REC`, `RECIPE_S`, `RECIPE_G`, `RECIPE_BQI` are 1B
  configs (RULES:398-401); `PREPARED_MANIFESTS` holds OLMo's only (RULES:478); `GATE_A_FIXTURE`, `BASE_MODEL`,
  `INSTRUCT_MODEL` are 1B's (RULES:479-487); `ARM_MEASURED_S = 52 * 60`, Gate B's 1B arm upper (RULES:82); the S1
  package pinned by `S1_CODE` at main `40e0cc6` (KIT README round 3c) (R).
- Money rules the kit enforces: planning $1.85/h, spend $1.79/h, create refused above $10/h, $6 reserve, contingency
  1.25; `init-block --funding FILE` refuses unless the record covers the cap-based need (KIT README "Money", R).
  The user removed the balance guard on 25 Oct (RULES:64-69 `GUARD_OFF_KIND`, R) and ruled "start from the
  balance" on 29 Oct (F L121, R); the funding-record check still binds the kit's init (I).
- Budget guards see caps only in working copies named `family-probe-*`, `gate-b-olmo*`, `stage1-olmo*`
  (`budget.py`:39, R).

### 1.5 The OLMo 3 probe kit (O3K): what fits the 7-8B kit

- A copy of `runkit/family-probe/` with one new probe entry; original untouched; 18 tests in its own folder plus 12
  (preflight) and 8 (engine tiny) under `scripts/tests/` (M, `grep -c`); not merged (untracked, M).
- Reusable as is or as a pattern (R, O3K README and `states_tool.py`:1-24): the `tmp/family-probe-s78-<model>-<step>/`
  working-copy prefix (every guard sees the cap: KCR KD7, P78 EM-2); `pack_setup.py --dry-run` (the $0 pack check);
  `host.py pull-states HOST CHECKPOINT` plus `states_tool.py check` (the state rule KD5: pull e1 states, back up,
  delete only after a verified backup and the user's yes by pod name; the kit has no delete command); `MAX_PRICE`
  1.85 at the guard and the $10/h creation limit with the finite-price refusal; the per-probe `lock` and
  `preflight_script` hooks in `probes.py` (not needed by OLMo-2-7B or Llama-3.1-8B, which use the engine lock and
  `scripts/cuda_preflight_family.py`; needed later if OLMo 3 joins the 7-8B kit as a third family under option B).
- Not reusable for arms: the family-probe shape runs one a0 fine-tune per pod and refuses other shapes (O3K README
  "The Gate A shape"; XL:12, R). It is KCR's route (iii): only block 0's Llama a0 seed 1103 could run on it
  (KCR:142, R). Because block 0 also needs R_1-R_3 on both families, the stage-1 kit copy is needed for block 0
  anyway, so route (iii) buys nothing but a second kit to operate (I).

### 1.6 Not done (M or R)

- The Llama G1 $0 check (P78 [LEAD] item 7; P78:272): no FOCUS entry names it (M: `grep` for "Llama G1" and
  "Llama-3.1-8B.*G1" prints nothing).
- Predictions N1 and N2 (P78:131-134) are not recorded anywhere outside P78's proposal (I from the `find` and
  `grep` above).
- The user's decisions S, H, SR-2, F, TC-extension, RP decision 5, the restated decision 2, the review ceiling, SR
  under [C], the thresholds under S-P, D5-and-H (P78:385-397): none recorded; SPF:494 says the freeze deadline
  lapsed and "no source records" its replacement until F L98's ruling (2), which sets the new freeze point (before
  block 0's first pod) but decides none of the items (R, I).
- No 7-8B recipe-S config, no any-model Part C scripts, no `scripts/scale78b/` (M).

---

## 2. Build tracks, in the order that gets block 0 ready soonest

Block 0 (N) = OLMo-2-7B R_1-R_3 at 1101-1103 with SEAL's `R_d1-R_d3` byte for byte; Llama-3.1-8B R_1-R_3 at 1101-1103
with new Llama files whose remove lists equal SEAL's; Llama a0 at 1103; 7 runs; one OLMo pod (3 arms, cap 8.5 h) and
one Llama pod (4 arms, cap 12.5 h) in parallel; 7-9 h wall (P78:92-107, KCR:177, R). Everything else (the a0-1101
retrains, scorer passes, blocks A and B) follows. The tracks below are what block 0 needs, then what block A needs.
Hours are builder hours (E), the basis being the sizes of the sources and of the stage-1 kit's comparable rounds
(KIT README rounds 30-35: one round of one new job kind with tests and a mutation set took one builder session each,
R). The lead's review time is extra.

### T1. Part 1 of the 7-8B pre-registration: decisions and text (lead; 4-8 h; starts now, in parallel with all)

- **Files.** New: `research/experiments/2026-11-xx-78b-preregistration.md` (Part 1; P78:341) and the decision records
  under `.ai/inputs/stage1-post-w1-20261023/reading/` or a new `78b/` folder (the project's record style: DOSE, MONEY).
- **Sources.** P78 (the text), §5 below (the outline and the S4 dose arm), DOSE, F L98 ruling (2), PR4:233 (the
  analysis model), the user's answers to §3's items.
- **Acceptance.** Every [USER] item of P78:385-397 has either the user's recorded word or the lead's ruling under
  the 16-17 Oct delegation with its pre-set fallback (F L98's form); the blinding line lists every stage-1 and
  Gate B value the authors saw (§5.0); the S4 dose arm is in with its label; the file's SHA-256 is in FOCUS before
  block 0's first `launch.py`; `scripts/stage1/commitments.py check` (or the post-W1 records tool the lead uses) passes.
- **Tests.** None mechanical beyond the hash in FOCUS and the records tool; the decisive check is a reviewer's
  read against the list in §5.12 (choices after a result labelled).

### T2. The cap rule and the measured basis: `runkit/stage1-78b/rules_78b.py` (6-10 h)

- **Files (new).** `runkit/stage1-78b/rules_78b.py`, `measured-basis-78b.json`, `derive_78b_basis.py`, `tests/`
  (KCR:132-137, R). It imports nothing from `runkit/gate-b-olmo/` or `tmp/gate-b-olmo/`; it may copy the stage-1
  kit's helpers (`round_up_s`, `cents`, `funding_need_usd`) with an equality test against RULES on the same inputs.
- **Sources.** KCR §3-§4 (constants: OLMo TRAIN_STEP_MAX 24.26 s, FIRST_BATCH_MAX 314.0 s, BATCH_MAX 240.9 s,
  OUTSIDE_MAX 109 s; Llama 22.89 / 246.9 / 250.3 / 163 s; SCORE_ALLCAP 1,250 s; EARLY 20 s; requirement 12,365 s
  (OLMo, 38 steps) and 12,613 s (Llama); MEASURED_UPPER 1.15 × 6,450 s and 1.15 × 8,466 s; POD_OVERHEAD 48 min;
  KCR:100, :119-120, R); the 17 units' timing fields under `tmp/family-probe-sp-*/{hosts/*,retrieved/*/tree/...}`
  (KCR:9, R). **Privacy rule for the builder:** `derive_78b_basis.py` opens only the allow-listed timing files
  (`verification.json`, `finished.json`, `create-*.json`, `BOOTSTRAP-READY.json`, `PREFLIGHT-DONE.json`,
  `JOB-DONE.json`, `ledger.jsonl`, `progress.jsonl`), never `eval/`, generations, samples, prompts, `ssh/`,
  `selector.jsonl`, `hidden/` (KCR:135, test 15 at KCR:228, R). The builder, not this scout, reads `retrieved/`.
- **Acceptance.** KCR tests 1-15 (KCR:214-228) pass; the golden numbers equal KCR §4 and §7; every measured unit is
  below `upper_M(38)` (test 3); the basis file's SHA-256 is pinned in `rules_78b.py`; `git status --porcelain --
  experiments scripts` prints nothing after the build (test 14).
- **Tests.** The 15 listed, plus the mutants of KCR:226 (killed only on a real test failure; errors are invalid runs;
  the baseline with the same command, the project rule).
- **Decisions it bakes in (KD1-KD11, KCR:262-272).** The lead may rule them under the delegation: M-cap (KD1); 4 arms
  per pod on both families (KD2: the user confirmed 4 for Gate B's path only; the stage-1 kit's `MAX_ARMS_PER_POD = 4`
  (RULES:72) is a later user-confirmed value for stage 1, R); the E margins (KD3); the Gate B hold (KD4) is now
  moot, set `GATE_B_HOLD_USD = 0` with the reason "Gate B closed 31 Oct, F L104" (I); 50 GB volume and the state
  rule (KD5: O3K's `states_tool.py` is the pattern); unmeasured kinds on a single-job pod with an explicit cap (KD6);
  the `family-probe-s78-*` names (KD7); configs under `experiments/` now allowed as committed additions (KD8: the T4
  freeze lapsed; the OLMo 3 round already adds nine configs, F L77, R); re-measure on the first Y pod (KD9); the in-pod
  speed check `s_obs` (KD11).

### T3. The Llama sealed set: `.ai/inputs/scale-78b-sealed-llama3-<date>/` (4-8 h)

- **Files (new).** `build_sealed_llama3.py` (loads BLD by path after its SHA-256 check `80cb8944…`, builds BLD's
  `Inputs` from the OLMo prepared folder, calls `draw_r(inputs, d)` for d = 1…16, and writes each Llama edit file with
  its own writer, `manifest_sha256` = `c52a50af…`, provenance naming both scripts' hashes); `out/edits/R_d1-R_d16.json`;
  `out/edits/unit_g-*.json` (8); `out/MANIFEST.json`; README (P78:342, R).
- **Also needed on the Llama manifest, for block A (I, from PR4:128-131 and SS/edits.py's manifest binding,
  P78:77):** H1 (the 600 rows with the fewest target tokens: Llama's own tokenizer, so a new count, not a copy),
  the S1 add edit (the same 48 S-pool rows, re-bound), S3 (DataRx-style SAS over the sealed 1,000-prompt subset with
  Llama's own untuned answers), S4 (Llama's own untuned answers), and the two S4 dose edits (96, 192). These are
  stage-2's files too (Llama-3.2-1B has the same manifest, P78:342): build one set for both, named by manifest, not by
  model (I). The S3/S4/dose edits need the untuned-answers pass on a pod first (T6), so only R, unit and H1/S1 files
  are $0 now.
- **Sources.** BLD (the draw and the writer's field list), `SS/edits.py:110-122` (`parse_edit`, the manifest refusal),
  SEAL's README and `out/edits/` keys, PR4:128-131 (the S arms), `scripts/stage1/build_length_rules.py` (H1 at 1B),
  `write_add_edit.py` (S1/S3/S4 at 1B).
- **Acceptance.** For d = 1…5 and the 8 unit files, every Llama remove list equals SEAL's (the groups and member lists
  are equal: CALC `env_and_manifest_check_out.txt`:16-17, R); `parse_edit` accepts each Llama file against the Llama
  prepared set; the wrapper refuses if the two manifests' groups or members ever differ; the wrapper never writes
  under SEAL; BLD's bytes unchanged (SHA-256 after the build).
- **Tests.** List equality (d = 1…5, units); a parity test that the OLMo draw reproduced by the wrapper equals SEAL's
  files byte for byte on the OLMo manifest; a trap test that the wrapper refuses a manifest with one member moved.

### T4. The 7-8B kit shell: `runkit/stage1-78b/` as a copy of the stage-1 kit with per-family constants (20-40 h; the long pole)

- **Route.** KCR's route (ii), the stage-1 kit, recommended there and the only route that runs edit arms, references,
  retrains, A1 passes, seals, backups and judge lists (KCR:141, :238; KIT `KINDS`, R). Copy `runkit/stage1-olmo/` to
  `runkit/stage1-78b/` (the original untouched: stage 1c and stage 2 still read it), then:
  1. **A per-family constants block** in `rules_78b.py` (T2) replacing RULES' 1B pins: `PROBE_KEY`, `REC`, `RECIPE_S`
     (T6), `RECIPE_G`, `RECIPE_BQI` (engine Y), `PREPARED_MANIFESTS` (both hashes), the fixture path, the a0 unit
     paths (the side units), `BASE_MODEL`/`INSTRUCT_MODEL`, `ARM_MEASURED_S` and `SPEND_UPPER_S` from the M-cap, the
     volume (50 GB), `MAX_ARMS_PER_POD_78B`. One working copy per family and block: `tmp/family-probe-s78-olmo2-7b-0/`,
     `tmp/family-probe-s78-llama31-8b-0/`.
  2. **The gated-token launch path** for Llama: port `runkit/family-probe/launch.py`:8-21's checks and hand-over into
     the copy's `launch.py`, and make `download_models_stage1.py`'s gated run live for `llama31-8b`. This is
     security-relevant and gets its own review (KCR:140, R). O3K's `launch.py` is the current copy of that path.
  3. **Block definitions** for the 7-8B blocks: block 0 (`arm` with an edit file; `a0_arm` for Llama 1103; the
     `retrain` of a0-1101 under recipe S_78 and its `a1_rescore`-style attributes pass, T6); block A (the six method
     arms at 1102-1104, R_4, R_5, a0 1104); block B (by the seed rule); references (`ref_eval` for the safety prompt
     and adapter scaling, `ref_train` for recipe G and B+Qi, `safe_lora`); the S4 dose arms (`arm` with the dose edit).
     `plan_tool.py`'s block tables and `judge_units_*` lists follow.
  4. **Job runner:** the arms run under the family's main config, not a recipe-S sibling (P78:99); the in-pod speed
     check `s_obs` after each arm (KCR:113); the free-space check before each job (KCR KD5).
  5. **Keep unchanged:** the seal, backup, finisher, secret scan, status, budget (with `KITS_GLOB` extended by
     `stage1-78b*`), the judge route (the judges read answers only; the stage-1 judge pods did 72 units in about
     1 h each at 1B, F L103, R).
- **Stage it.** Build and verify the block-0 subset first (steps 1, 2, 3's block 0, 4, 5): that is what block 0
  needs. Blocks A/B, references and the dose arms before block A (after the gate).
- **Acceptance.** `pack_setup.py --dry-run` and `pack_setup.py` on both families print the engine X identity
  `472fc7f6…`, the right config hashes and both manifests; `plan_tool.py init-block 0` writes a plan with the
  M-cap caps (8.5 h and 12.5 h) and the funding need ($56.06 at KCR's caps with contingency; KCR:177); `budget.py
  check` reads the live balance; a job-runner dry run on a fake `PREFLIGHT-DONE.json` computes s and defers the right
  job (KCR test 12); the stage-1 kit's own tests still pass unchanged in `runkit/stage1-olmo/`; the token never appears
  in any record (the existing `secret_scan` plus a test with a fake token); `git status --porcelain -- experiments
  scripts` clean except T6's committed additions.
- **Tests.** The copied 378 tests adapted (most are kit-shape tests and carry over); new tests for the constants
  block, the gated path (whoami refusal paths, the Range check, the stdin hand-over, scrubbed child environments), block
  0's plan shape, the edit-arm command lines under the main config, `s_obs`, the free-space check; a mutation set as
  the stage-1 rounds did (RULES' spec style). Mutation runs as the lead's background Bash, agents review the results.

### T5. The noise reader: `scripts/scale78b/noise_reading.py` (3-5 h)

- **Files (new).** `scripts/scale78b/noise_reading.py` and its tests; later `blinded_sigma.py` (SR-2, 2-3 h) if
  adopted. `transfer_reading.py` is **not needed now**: TC does not run (Gate B TOO CLOSE); keep P78 §7 as the
  written rule and build the reader only if a later 1B reading ever says LOCALIZED (I; saves 3-5 h).
- **Sources.** P78:114-122 (the reading: r_F,j, σ̂_F on 2 df, σ̂_pool on 4 df, s_arm, the fallback, the printed
  fields), `scripts/gate_b_reading.py` (`variance`, `mean`, `median_term`, `pair_se2`, `noise_gate` at :288-294, :363,
  :457, :757, R) reused by import or by a copy with a parity test.
- **Acceptance.** Reproduces Gate B's wave-0a values on its inputs: σ̂_gate 1.83, fallback 2.16, σ_eval,0 1.28
  (P78:345, R); keys every input by `complete_sha256` and family (P78:291); prints no U of a method arm; prints the
  seed-rule output on the paired scale with the thresholds 4.5 / 6.0; a test with a 1B unit's record mixed in refuses.
- **Tests.** The NG parity; the fallback trigger (an environment mismatch or a failed fingerprint check); the
  seed-rule table from CALC `rule_oc2_out.txt` reproduced for one row; the input-key refusal.

### T6. Recipe S_78, the a0-1101 retrains, the scorer rules (Part 2's block-0 part) (6-12 h)

- **Files (new).** `SS/configs/study-kt-olmo2-7b-r64-b-mb2-gateb-<date>.json` and `…-llama31-8b-r64-b5e5-mb2-gateb-<date>.json`
  (recipe S_78 = the main recipe with Gate B's recipe-S differences; the 1B pair is `study-kt-olmo2-1b-r64-b-mb4-20261008.json`
  against `…-gateb-20261008.json`, RULES:398-399, R; configs are outside the engine identity, P78:348, R); a 7-8B
  recipe-S maker as a new script (the 1B `scripts/make_gateb_recipe.py` is pinned to 1B, KCR:140); the any-model
  Part C scripts (`rep_pass`, `l1_scan`, `classifier`, the layer-index rule) as new files under `scripts/scale78b/`
  with a 1B parity test, the 1B scripts under `scripts/stage1/` untouched (P78:357, R); the 7-8B scorer rules (A1 per
  family with an anchor job; L1's layer rule; H1 by the family manifest; the S-pool, S1, S3, S4 from the family's
  own untuned answers) in Part 2's text, committed with code hashes before any block-0 scorer output is read
  (P78:367, :413, R).
- **The retrain doubles as the engine certificate (I).** Run each family's a0-1101 retrain (train only, recipe S_78,
  to q and e1) on **engine Y**. If its q and e1 adapter fingerprints equal the side units' (OLMo-2-7B 1101: q
  `3c7344c1…`, e1 `9d5d5d8b…`; Llama 1101: q `ac05caca…`, e1 `ee44580d…`; P78:82, R), Y equals X for that family
  (as C1 did at 1B: 16 of 16 files equal, F L133, R) and every 7-8B arm, B+Qi included, may run on Y; the A1 pass
  runs on the engine that trained its states (EYD:81 via P78:333). If they differ, the paired arms stay on X, B+Qi
  runs on Y as an unpaired reference, labelled, and N is re-read with the a0-free fallback (P78:121). This resolves
  P78 [LEAD] item 11 with one job instead of two.
- **Acceptance.** Both configs' `config_sha256` computed with `-I -B`; the retrains' fingerprints recorded; the Part C
  parity test byte-identical on the 1B inputs; the scorer rules' hashes in FOCUS before the first scorer output.
- **Tests.** The parity test; a config test that S_78 differs from the main config only in the recipe-S fields;
  the fingerprint comparison script's test on the 1B pair (Gate B's retrain record).

### T7. Before block A (after the gate; 6-12 h)

- The OLMo R_d9-R_d16 wrapper `scripts/scale78b/build_r_draws_78b.py` (only for plan B9 or 12 seeds; P78:343).
- Block A/B/reference definitions in the kit (T4 step 3), the dose edits (T3) after the untuned-answers pass.
- The state rule's backup tool run (O3K pattern) and the idle-storage line in each block's need.
- Part 2's remaining text (references, limits, judges, cost conventions, the confirmation choice rule, Alpaca's home).

### Order and calendar (E, I)

| Window | Tracks | Why this order |
|---|---|---|
| 5-12 Nov (this usage week; the OLMo 3 verify round also runs) | T1 (lead), T2, T3's R/unit/H1/S1 files, T5 | $0, small, each with a decisive parity test; T2 is T4's input; T3 is block 0's Llama input; 7-8B goes first if usage runs short (F L98) |
| 12-19 Nov | T4 block-0 subset (with the token path review), T6 configs and retrain job, T1 freeze | T4 is the long pole; T6's configs commit by explicit path once; the Part 1 freeze needs the user's answers (§3) |
| 19-20 Nov | dry packs, plans, a records-tool check, the FOCUS hash of Part 1 | block 0 is "ready": one `launch.py` away once the money shows |
| the day the money arrives (about 20 Nov) | block 0: two pods, 7-9 h wall; the a0-1101 retrains on a third pod (or after N on the same pods) | N's reading the next day; the gate reads money and N only (P78:180) |
| after the gate (about 22 Nov) | T7; block A both families (12 pods at 4 arms, 6.6-8.8 h each; 4-8 in parallel: 1-3 days); judges | RP's latest start for block A was 23 Nov (RP:105) |
| about 27 Nov-10 Dec | block B, references, dose arms, scorer passes; judges | RP's latest start for block B was 3 Dec (RP:106); "B 7-10 days at 8 pods or 2-3 weeks at 4" (RP via SPF:498) |
| about 11-20 Dec | confirmation (stage 3, ≤ 2 contrasts per family, on Y) | RP's latest start 14 Dec (RP:108) |
| 4 Jan 2027 | results frozen | README:120 (R; an internal target) |

Total builder effort about 55-95 h over two usage weeks (E). The calendar fits B with about two weeks of slack if
the money is in the account on about 20 Nov and the builds verify on the first or second round (I). If the money
slips past about 1 Dec, B no longer fits the 4 Jan freeze with its confirmation; the gate re-checks this (F L98).

---

## 3. What needs the user (money, decisions, downloads), with dates

Dates: today 5 Nov (M). Internal targets unless a source verifies them: the 20 Nov gate (MONEY, RP:104: "about");
the 13 Nov OLMo 3 fallback (F L98: 23:59 UTC); the 1 Dec 32B go/no-go (README:113); the 4 Jan results freeze
(README:120); ICML about 22 Jan 2027 (README:120; SPF:168: "estimated, not official"); usage resets Wednesdays
09:00 UTC (F L74: next 12 Nov).

| # | Needs the user | By when | Why; what happens without it |
|---|---|---|---|
| 1 | **The money in the RunPod account** (about $900-1,300 expected; MONEY). Block 0's kit need at KCR's caps is about $56 ($44.85 guard term × 1.25; KCR:177) against $22.64 on 2 Nov (F L81). | the day it arrives, about 20 Nov | nothing 7-8B launches before it (F L98; the 29 Oct rule); the gate picks C or defers; the 4 Jan fit is re-checked |
| 2 | **RP decision 5**: reuse the side project's engine-X units as main-study a0 (evidence P78:70-84), and the Llama seed-1103 rule ("the rung stays"; P78:100) | before Part 1 freezes (before block 0's first pod) | without reuse, N has no partners: 3 more a0 runs per family (about $9-14) and the S-U exclusion of plan A no longer holds (P78:152) |
| 3 | **H, the high-noise branch** (P78:222-245): (a) SESOI 10 pp, (b) 12 seeds on P1/P3/P6, (c) both, (d) review, (e) money-contingent, recommended (e) with (b) first; (a) and (c) change D5's "SESOI 5 pp" and need the user's word (P78:243) | before N launches | the lead may rule (e)/(b) under the delegation with (a) as the fallback if money binds (I); (a) or (c) cannot be the lead's |
| 4 | **F, the family under C**: F1 OLMo-2-7B (recommended), F2 Llama-3.1-8B, F3 by σ̂ (weak, P78:324) | before N launches (P78:301) | the lead may rule F1 under the delegation; the trade-off (Llama's lower a0 noise on 1 df; the published setting) is the user's to see (P78:325) |
| 5 | **SR-2** (a blinded re-check after block A) yes or no; **SR under [C]** (pooled or own σ̂_F); **thresholds under S-P** (keep 4.5/6.0 or rescale to 4.22/5.56) (P78:388, :395-396) | before N launches | the lead may rule: SR-2 yes if the record-done step can hide block-A U values (P78:202); keep 4.5/6.0 |
| 6 | **The S4 dose arm's seeds at 7-8B**: 3 (secondary default, DOSE `seeds`) or 6 (the primary family's seeds); and whether it is the first secondary item cut (DOSE `pre_set_fallbacks[1]`) | before Part 1 freezes | the lead may set 3 with "6 if money allows" as the ambitious default (I); see §5.9 |
| 7 | **The Llama-3.1-8B gated download on the pods**: the user's HF token in the Mac environment at launch, as the family probes did (family-probe `launch.py`:8-14) | the day block 0 launches | the Llama pod cannot download its weights; OLMo's pod runs alone; the gate then has one family's N (I) |
| 8 | **The kit route** (KD10: the stage-1 kit copy, this plan's T4) and **4 arms per pod at 7-8B** (KD2) | before T4 starts (about 12 Nov) | the lead may rule both under the delegation (the user confirmed 4 for stage 1 too, RULES:72) |
| 9 | **Idle pods**: a yes by name before any stopped 7-8B pod is deleted after its verified backup (the 31 Oct rule, O3K `states_tool.py`:12-16) | after each block | storage at about $0.33 per day per 50 GB pod (KCR:161) |
| 10 | No Mac download is needed for the 7-8B tier: the prepared sets and manifests are on the Mac (§1.3); weights go to the pods. (The OLMo 3 items, the tokenizer download and the separate environment, were answered yes and done: commit `e0b233a`, M `git log`.) | — | — |

The earmark (I): the new money is for the 7-8B tier (MONEY `question`). Rows 2-4 of NEXT step 2 (stage 1c, the
human label check, stage 2) start on money too; the lead should not spend the 7-8B money on them without the user's
word, and should say so when the money arrives.

---

## 4. Money for options B and C, with measured bases

**Bases (M or R).**
- A100-SXM4-80GB at $1.79/h on every pod since 9 Oct (RP:31, R); the stage-1 judge pods $1.77 and $1.89 per block
  (F L103, R).
- 7-8B fine-tune-only jobs: OLMo 86.1-107.5 min, median 90.9 (n = 8); Llama 105.2-141.1 min, median 123.8 (n = 7);
  pod overhead 21.8-41.8 min (KCR:72-76, R; the six main-recipe pods re-read: §1.3, M).
- Cost per arm at 4 arms per pod: OLMo $2.94 expected, $3.52 at the measured maxima, $3.53 planning (× 1.2); Llama
  $3.93 / $4.52 / $4.71 (KCR:183-188, E on M).
- Stage 1 (OLMo-2-1B, plan A, 50 primary cells plus references, scorers, certificates and judges): $193.53 measured
  (block A $48.59, block B $144.94; F L133, L103, R). A 7-8B job is about 1.9× (OLMo) to 2.3× (Llama) a 1B job
  (RP:43, M there).
- Full-run equivalents per family for the full comparison, a0 and recipe G topped up to their counts (netting the
  units in hand): OLMo 65-72, Llama 69-76; confirmation 36-48 (B) or 18-24 (C) (RP:76, R).

**Not counted twice (R, I).** N's 7 runs are inside the comparison's counts (R_1-R_3 are the first 3 of R's 8; Llama
a0-1103 is one of a0's 6; P78:110). The in-hand units (OLMo a0 × 3, untuned × 2, OLMo recipe G × 3, Llama a0 × 2)
are netted in RP's "to 6 / to 8" counts (RP:71). The probes' 41 A100-hours (about $73) are sunk (RP:140). The Gate B
hold of $83.91 is gone (Gate B closed, F L104). OLMo 3's level 3 (about $266-390) is option B only, the first cut,
and is not in B's figure below (README:100). The S4 dose arm is new money, added once.

**Option B (both families), by the gate (about 20 Nov) (E):**

| Line | Basis | Amount |
|---|---|---|
| Arms, both families, plan A or B9, N inside | 65-72 FRE × $2.94-3.52 + 69-76 × $3.93-4.52 = $462-597; × 1.2 for failed pods and re-runs (RP:41) | **$555-716** (KCR:191) |
| S4 dose arm, 2 doses × 3 seeds × 2 families (6 seeds: double) | 6 × $3.53 + 6 × $4.71 | **$49** (3 seeds) to **$99** (6 seeds) |
| Judges (HarmBench and Granite pods per block; 3 blocks per family) | $3.67 per 72-unit block at 1B (F L103); answers are longer at 7-8B and the judges read them | **$25-50** |
| Idle storage until the verified backups | $0.33 per day per stopped 50 GB pod (KCR:161); the state rule deletes after the backup and the user's yes | **$15-30** |
| **B by the gate, plan A or B9** | | **about $640-900** |
| Branch H(b), 12 seeds, if it fires on both families | +$87-112 (OLMo) +$103-128 (Llama) (P78:216) | +$190-240 → **about $830-1,140** |
| Confirmation at 7-8B (stage 3, ≤ 2 contrasts per family, engine Y), by about 1 Dec | RP:136 | **+$140-230** |

**Cross-check by stage-1 scaling (E, I).** $193.53 × 1.9 ≈ $370 (OLMo) and × 2.3 ≈ $445 (Llama): both families
about $815, minus about $20-25 for the units in hand, so about $790 for everything stage 1 held (scorers, references,
certificates and judges included). The build-up above gives $640-900 at plan A/B9. The two agree to about 15%.

**Against the expected $900-1,300.** B at plan A or B9 with its confirmation ($780-1,130) fits; B with H(b) on both
families fits without the confirmation ($830-1,140) or with it at the low end ($970-1,370); every top end at once
does not (I). RP's F2 figures (B $900-1,300; C $550-800; RP:104) are the same order.

**Option C (one family), by the gate (E):**

| | OLMo-2-7B (F1) | Llama-3.1-8B (F2) |
|---|---|---|
| Arms × 1.2 | 65-72 × $2.94-3.52 × 1.2 = **$229-304** | 69-76 × $3.93-4.52 × 1.2 = **$325-412** |
| Dose arm (3 / 6 seeds) | $21 / $42 | $28 / $57 |
| Judges, storage | $20-40 | $20-40 |
| **C by the gate** | **about $270-390** | **about $375-510** |
| Confirmation (1-2 contrasts), by about 1 Dec | +$70-120 (RP:136) | +$70-120 |
| H(b) if it fires | +$87-112 | +$103-128 |

RP's C ($550-800 by 20 Nov) also holds Llama-1B's replication and Alpaca on OLMo-1B (RP:77, :138); the 7-8B part
alone is the table above. The second family costs about $370-510 (the B − C difference); RP's "−$230-390" (RP:138)
was before the dose arm and at the expected, not planning, rate (I).

**Money in the account against spend (R, I).** The user's guard-off and start-from-the-balance rules stand
(RULES:64-69; F L121). The stage-1 kit's `init-block --funding` still needs a record covering the cap-based need
(1.25 × the worst path): block 0 about $56 (KCR:177); block A both families at 12 four-arm pods launched 4 at a time
about $95-115 per launch (E: 4 × (10.5-12.5 h × $1.85) + $6, × 1.25). Under the stage-1 precedent the record's source
can be "user rule: start from the balance" (F L120), so the account needs only the spend plus the kit's headroom, not
the Gate B-era guard sums (I).

---

## 5. Proposed outline of Part 1 of the 7-8B pre-registration

Freeze point: before block 0's first pod (F L98 ruling (2)). Status line, labels, short names and option marks as
P78:3-13. Everything below is a proposal for the lead's text; where it departs from P78 it says so.

### 5.0 Blinding line (EM-5; S1B:121 (m) form)
What the authors have seen before this freeze: the stage-1 reading of OLMo-2-1B (P1-P6 words and intervals, the best
feasible repair S4, family 1b, B14's overlap control, LN-14's bar, the stage-3 pick P6 then P1; F L91); Gate B's
verdict TOO CLOSE and its wave-0a values (σ̂_gate 1.83, σ_eval,0 1.28, fallback 2.16); stage 1b's pilot null
(+3.94 pp); the 7-8B a0 E values and per-arm SDs (OLMo 6.36 pp on 2 df; Llama 1.06 on 1 df); the six-cell pooled
5.83 pp; E_HB per seed. No 7-8B repair arm has run. No Llama-3.2-1B repair arm has run.

### 5.1 Scope, options and the gate
Options B and C as RP:71-79; the gate at about 20 Nov reads money and N only (P78:180); restate decision 2 as "B if
the account covers B at the plan the seed rule gives, H and the dose arm included, and the confirmation money is in
sight; else C" (P78:392). The 4 Jan fit re-checked at the gate (F L98).

### 5.2 Units reused and the pairing conditions
The seven engine-X units by `COMPLETE.json` SHA-256 (P78:48-57); the four conditions met (P78:74-78); rule EM-1 for
new arms; the block-0 fingerprint check with the fallback (P78:82, :121). RP decision 5 recorded here (§3 item 2).

### 5.3 Block 0 = N
Runs, seeds, edit files and configs as P78:92-96; the Llama seed-1103 rule (P78:100); pods and caps by `rules_78b.py`
(T2); money about $21-27 ($26-32 with the allowance; P78:108); the report-only results (P78:124-129); predictions
N1 (mean r 1-4 pp on both families) and N2 (σ̂_pool about 4.0 pp if the 1B pairing ratio holds, about 8.2 with no
gain; P78:133-134) written by the lead before launch. Plus the a0-1101 retrains on engine Y as the per-family X → Y
certificate and A1's states (T6).

### 5.4 S, the analysis scale: settled by the frozen stage-1 model (a change from P78 §4)
P78 §4 framed S as PLAN-S:102 (unpaired) against a paired option. The frozen stage-1 pre-registration already fits
seeds as blocks: HB-C, one seed effect per design cluster, σ²_a per arm by REML, the paired mean on the common seeds,
Satterthwaite df (PR4:233-239, R), and B16 implements it (`reading/README.md`:20-21, R). So at 7-8B: **the same
HB-C form per family** (two clusters: {a0, S1, S3, S4, S4_96, S4_192} and {R, A1, L1, H1}); the seed rule reads
σ̂_pool on the paired scale (P78:119); S-U (the unpaired difference of means) as the sensitivity. Consistency with 1B
is then automatic, and P78's [USER] item 1 needs no decision beyond noting this (I). Seed layout under HB-C: methods
1102-1107, R 1101-1108 (R_8 serves S-U only), a0 1101-1107 (add 1107: P78:159).

### 5.5 SR, the seed rule and SR-2
Thresholds 4.5 / 6.0 on the pair scale → plan A / plan B9 / branch H; the review ceiling at MDE > 2 × SESOI
(P78:170-177); under HB-C the thresholds mean paired MDEs of about 6.4-6.5 pp (P78:168). SR-2 yes if the kit's
record-done step can hide block-A U values until `blinded_sigma.py` prints σ̂_A and df only (P78:199-204); the
gate budgets the worst plan SR-2 can reach (P78:203). Operating characteristics from CALC `rule_oc2_out.txt` and
`review_calc_out.txt` quoted.

### 5.6 H, the high-noise branch
(e) money-contingent with (b) first: "if the account after the gate covers (b)'s extra on the families that run,
(b); else (a) with the 10 pp margin stated in the paper" (P78:241, :245). Any (a) or (c) is the user's change to D5
(§3 item 3).

### 5.7 F, the family under C
F1 OLMo-2-7B unless the user names F2 (P78:325); fixed before N; the trade-off stated.

### 5.8 TC, the transfer check
Does not run: the frozen 1B reading said TOO CLOSE (README:95). The rule (P78:249-295) is kept for the record; the
paper says localization was tested at 1B only (RP:91). No reader is built now (T5).

### 5.9 The S4 dose arm (new; the user's "Yes, add it", DOSE; labelled "added after the OLMo-2-1B stage-1 reading")
- **Why and the label.** S4 was the best feasible repair at 1B (P6 better, +18.28 pp against S1; restoration 15.97 pp,
  about a third of the erosion), while Safe LoRA, B+Qi and the safety prefix reached a lower U with more over-refusal
  (F L91; DOSE `why`). The arm asks whether more self-distilled refusals close that gap within the O and L limits. It
  is confirmatory at 7-8B because no 7-8B repair outcome exists (DOSE `integrity[1]`); the text states the date and
  the reason (DOSE `integrity[2]`).
- **Construction (per family; DOSE `lead_design_draft.construction`, PR4:131).** The family's own untuned model's
  greedy answers to the S-pool minus S1, in S4's sealed order (`stage1-s4-v1`, 512 prompts in 32-prompt chunks), kept
  only if ended, refusal-opening by LEX, non-empty and accepted by `encode_train`; S4 = the first 48 kept, S4_96 = the
  first 96, S4_192 = the first 192 (nested). The same `make_untuned_answers.py` pass (T6) produces all three lists;
  the edits bind to the family manifest (T3). Fallback: fewer than 192 kept → the top dose is all kept rows, counted
  and reported (DOSE `pre_set_fallbacks[0]`).
- **Compute (I; state it).** S4 adds 48 rows to 4,800 (38 steps at 128 rows per step); S4_96 gives 4,896 rows → 39
  steps; S4_192 gives 4,992 → 39 steps. The study is compute-matched (SPF:57), so the dose arms' step counts and
  padded-token totals are printed beside the contrasts (the token-accounting report, S1L §5 item 1 via P78:379) and
  the +1 step is stated as part of the dose, not corrected away.
- **Comparators and reading (DOSE `comparators`).** D1: U(S4_192) − U(S4_48) and D2: U(S4_96) − U(S4_48), paired
  on the common seeds inside the full-corpus cluster under HB-C (§5.4); a monotone-dose summary (the three doses'
  means) reported. Against the model-level references within the O and L limits by the frozen dominance rule's form
  (family 1b's form at 1B, F L91): "does the top feasible dose beat every reference?". Secondary: outside the Holm
  family of P1-P6; labels *better / equivalent / inconclusive* at the 7-8B SESOI with one-sided bounds, as PLAN-S
  §5.3 does for secondary arms (P78:238). A dose that breaks O or L is "infeasible", reported (DOSE `limits`).
- **Seeds.** 3 (1102-1104, block A's seeds; the secondary-arm default, DOSE `seeds`) as the floor; 6 (1102-1107) if
  the money after the gate covers it; the choice is written at the gate from money only (a funding event is not an
  outcome, P78:241). At 3 seeds the paired SE is about σ_pair/√3; at σ_pair 4 pp that is 2.3 pp, so only a large
  dose effect (≥ about 7 pp) reads *better* (E; the normal approximation of P78 §6).
- **Cost (E, §4).** 6 runs per family at 3 seeds: OLMo $21, Llama $28; 12 runs at 6 seeds: $42 and $57; both
  families $49-99. Its judges ride on the block's judge pods. It is the first secondary item cut if money is short
  (DOSE `pre_set_fallbacks[1]`).
- **Prediction (lead, before block A).** A point and a direction for D1 and D2 (for example: D1 positive, 3-8 pp,
  with O rising with dose), written before any 7-8B repair outcome.
- **Where it runs.** With block B (after the gate), on the family's main config, like every add arm.

### 5.10 EM-1..5
As P78:333-337, with EM-1 revised: Y after the per-family fingerprint certificate (§5.3, T6), else X for paired
arms; EM-2 revised: the Gate B hold is gone; the kit's funding-record rule and the $6 reserve, the $10/h limit and
the in-pod timers stay (F L98; RULES:60-63); EM-3 seeds 1101-1116; EM-4 each (family, size) its own Holm family at
5%, the dose arm secondary; EM-5 the blinding line (§5.0).

### 5.11 T3 and T4 now
The Gate B-era T4 list (P78:350-356) lapsed with Gate B's last pods (F L104). What stays frozen: engine X's files
(the identity `472fc7f6…`); engine Y's frozen tree; the stage-1 S1 package by `S1_CODE` pins and the 1B Part C
scripts (KIT README rounds 3b-3c; stage 1c and stage 2 still run them); the sealed files (SEAL, anchors, recipe S);
the stage-1 kit `runkit/stage1-olmo/`. New files only, committed by explicit path; a re-check of the engine identity
and the S1 pins after each commit (P78:356 form). Configs under `SS/configs/` are committed additions (the OLMo 3
precedent, F L77).

### 5.12 Design choices made after a stage-1 result (labelled so in the text)
1. **The S4 dose arm and its doses (96, 192)**: motivated by P6 and the best-feasible-repair result (DOSE). Confirmatory
   at 7-8B; the label states the date and reason.
2. **The choice to keep P1-P6 all primary at 7-8B** although P2, P3 and P5 read *equivalent* at 1B: not a change, but
   state that dropping or re-weighting arms by their 1B labels was considered and rejected because it would be a
   choice after a result (I).
3. **Predictions N1-N2 and the dose prediction**: written after the stage-1 reading; the quantities they predict
   (7-8B noise, the random-removal effect at 7-8B) were not read at 1B's stage 1, but the date is stated.
4. **F, H, SR-2 and the thresholds**: decided after the stage-1 reading; the text says they do not read any 1B
   repair outcome (F reads cost, files and gating; H reads money and D5; SR reads N).
5. **The confirmation's pick rule** at 7-8B: the frozen stage-3 rule (the two largest |t| among *better* or *worse*,
   README:85) applies per family at 7-8B; the 1B pick (P6 then P1) is a 1B result and never selects 7-8B contrasts.
6. **TC's non-run** follows a Gate B outcome under a planned branch (REV4 §9.6 via F L86); stated as such.
7. **Any use of stage 1's HB-C arm variances** (F_k's planning power, in the reading record) in 7-8B power planning:
   if the lead cites them, label "read from the stage-1 reading"; the plan here uses only the pre-stage-1 values
   (Gate B wave 0a, the probes' SDs).
8. **Starting rule**: the 7-8B tier starts on money in the plan's order, never because P6 or P1 read *better*
   (NEXT:69; F L91 "no stage starts on a result").

### 5.13 Part 2 (frozen before block A; its scorer part before any block-0 scorer output is read)
As P78:375-379 plus: the dose arm's O and L reading; the dose edits' hashes; the per-family untuned-answers pass as
the shared source of S3, S4, S4_96, S4_192; the Llama H1/S1 files by manifest; the confirmation's design (≤ 2 per
family, engine Y, fresh seeds 9101-9999, the sealed 200-prompt subsample; README:84-86).

---

## 6. Risks and the smallest decisive checks

| # | Risk | Smallest decisive check ($0 unless marked) |
|---|---|---|
| 1 | **Money is an expectation, not a balance** (MONEY). Block 0 cannot start from $22.64 (need about $56). | None at $0; the readiness plan makes the wait cost nothing: all tracks are $0 and the first `launch.py` is the only paid step. The gate's "defer or C" fallback is pre-set (F L98). |
| 2 | **Builder usage** is shared with the OLMo 3 verify round this week; the lead's context (61% at 09:03 UTC, F L74) ends at the GI X handover. | Order T2, T3, T5 first (small, parity-tested); T4's block-0 subset second; the lead's handover note carries this report's path. The ruling "7-8B first" (F L98) decides ties. |
| 3 | **Llama-3.1-8B G1**: a0-1102 had 63 of 600 answers incoherent (10.5%) and answers-end TOO CLOSE (F L103 via P78:272); G1's bar is ≤ 10%. If R arms behave alike, N's report-only G1 status fails and every Llama contrast carries a coherence flag. | Run Gate B's frozen G1 code on the two Llama a0 units' records (the $0 check P78 names; never done, M). If both fail, raise to the user before the freeze: keep G1 as at 1B (P78:272) and state the risk, or choose F1 under C. |
| 4 | **OLMo-2-7B generates at 99.3% of the card** (84.49 of 85.09 GB reserved; 204 allocator retries in the check; KCR:62, :156). A different host build could run out of memory or slow down. | The preflight's `generation_memory_ok` stops a bad pod before any job (KCR:159); `s_obs` after the first arm (KCR:113). Block 0's OLMo pod is the live check; record every arm's batch times. |
| 5 | **The kit copy is the long pole and holds the security-relevant token path.** | T4 staged: block-0 subset first; the token path ported verbatim from family-probe `launch.py` with its tests and a separate review; a fake-token test that no record, log or child environment holds it. |
| 6 | **Compute-matched framing against the dose arm** (39 steps against 38; +2-4% tokens). | State it (§5.9); print the token accounting; the contrast is a within-cluster paired difference with the dose as the treatment. No fix needed, only disclosure. |
| 7 | **Engine for paired arms** (P78 EM-1 against EYD's B+Qi in Y). | The a0-1101 retrain on Y with the fingerprint comparison (T6): equal → Y for everything; unequal → X for paired arms, B+Qi unpaired and labelled. One job decides. |
| 8 | **Pairing gain unknown at 7-8B** (N's σ̂ on 4 df; P(wrong plan) up to 41% at σ_pair 6; CALC `rule_oc2_out.txt`). | SR-2 after block A (15-30 df); the gate budgets the worst plan. |
| 9 | **The Llama sealed set drifts from stage 2's** (same manifest). | One set, named by manifest, with the list-equality test against SEAL (T3); the stage-2 builder imports it. |
| 10 | **Idle storage and lost states** (states live only on the pod's volume; adapter scaling needs the e1 adapters; Llama's are lost once already, F L210). | The state rule from O3K (`pull-states`, `states_tool.py check`, backup, then the user's yes to delete); pull every a0 e1 state of both families in block 0/A before any stop-and-forget. |
| 11 | **The 4 Jan freeze** if the money slips. | The gate's re-check (F L98): B needs block B started by about 3 Dec (RP:106); otherwise C, or B without the 7-8B confirmation (cut order RP:138). |
| 12 | **Reading the wrong thing at block A** (SR-2's blinding is procedural; the kit records show U). | T4: the record-done step prints no U for block A until `blinded_sigma.py` has run; a test holds that output byte for byte. If it cannot be ensured, SR-2 is not adopted (P78:202). |

**The smallest decisive checks, in order (all $0 until the last):** (1) T2's golden and upper-bound tests against the
17 units (KCR:256); (2) T3's remove-list equality with SEAL's `R_d1-R_d3` and the OLMo byte parity; (3) T5's parity on
Gate B's wave-0a values; (4) the Llama G1 $0 check; (5) `pack_setup.py --dry-run` and `plan_tool.py init-block 0` on
both families with the right engine, config and manifest hashes; (6) block 0's two pods as the live cap and
fingerprint check (about $26-32).

---

## 7. Process (this scout)

- **Commands (all exit 0 unless noted):** `date -u` (3×); `git branch --show-current`, `git log --oneline` (main
  checkout and the scratch worktree), `git status --short` (scratch worktree); `ls`, `wc -l`, `find`, `grep`, `sed -n`,
  `cut` over the sources named above; `shasum -a 256` of BLD and the three prepared manifests; `python3 -I` reads of
  `hosts/*/{finished,create-result,create-intent}.json` numeric fields only; `grep -c "def test_"` on the test files.
  One `echo ===` line failed under zsh's `=` expansion (exit 1, "== not found") and was redone with `printf`.
- **Read:** P78 in full; KCR in full; XL head; CALC's four outputs; RP §2, §5, §6; SPF §9 and the source table;
  README's 7-8B sections; FOCUS lines 74, 77, 81, 86, 91, 98, 103, 133 and the 7-8B grep; NEXT in full; MONEY and
  DOSE; the stage-1 kit's README head, `stage1_rules.py` constants and kinds, `probes.py` entries, the download and
  launch scripts' headers; the family-probe `launch.py` header; O3K's README, `probe_constants.py`,
  `states_tool.py` header, `probes.py` entry lines; BLD's interface lines; PR4:128-131 and :228-240; the B16 README
  lines on the model; S1B's S4 lines; `scripts/gate_b_reading.py` function names.
- **Not read:** any unit's answers, prompts, labels, judge files, seals, `retrieved/`, `eval/`; the reading record
  `run-20261101/reading-record.json` (F L91's summary used instead); the OLMo 3 addendum; EYD beyond P78's citations.
- **Not done:** no test was run; no number of KCR's or P78's was re-derived beyond the arithmetic shown in §4;
  the Llama G1 check (a builder task, needs the frozen G1 code on the a0 records).
