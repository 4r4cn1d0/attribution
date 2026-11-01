# Task A: what stage 1b needs before its pilot can run

Read-only scouting for the lead (GI VIII). Written 2026-11-01, clock checked at 04:05 UTC. Sources: the main checkout
`/Users/spiderishi/Coding/attribution` (branch `stageb-costs-and-recovery-safeguards-20261003`) only. Nothing was run
except read commands and plain arithmetic. No test, kit, builder, judge, seal or launch command ran. No repository file
changed. This file is the only write.

Tags: (R) read in a source; (M) measured here by a read-only command; (I) my inference; (E) my estimate.

## Source key

Citations are `[KEY:line]`. Line numbers are the main checkout's on 2026-11-01.

| KEY | Path |
|---|---|
| PLAN31 | `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md` |
| FOCUS | `research/FOCUS.md` |
| PR4 | `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` (frozen) |
| W1 | `research/experiments/2026-10-16-stage1-commitments.md` (the W1 record) |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` |
| SPF | `docs/study-plan-full.md` |
| PLANS | `research/review/2026-10-08-sharpened-direction-DRAFT.md` (PLAN-S, adopted 8 Oct) |
| RDME | `README.md` |
| MAN1 | `.ai/inputs/stage1-commitments-20261016/MANIFEST.json` (the W1 manifest) |
| KR | `runkit/stage1-olmo/README.md` (byte-equal to `tmp/stage1-olmo/README.md`, M) |
| RULES | `runkit/stage1-olmo/stage1_rules.py` (byte-equal to the `tmp/` copy, M) |
| PT | `runkit/stage1-olmo/plan_tool.py` (byte-equal, M) |
| JR | `runkit/stage1-olmo/setup/job_runner_stage1.py` (byte-equal, M) |
| SEAL | `runkit/stage1-olmo/seal.py` (byte-equal, M) |
| PLANJ | `tmp/stage1-olmo/plan.json` (cited by JSON key; read for job kinds, statuses, timing fields and `records.d2_fallback` only) |
| ENG | `experiments/safety_selection/__main__.py` (engine X's CLI) |
| BP | `scripts/stage1/build_plant.py` (code; read under the brief's code carve-out) |
| RPR | `scripts/stage1/report_plant_ranks.py` (code; read under the carve-out) |
| SIN | `scripts/stage1/score_selfinf_n.py` |
| WSE | `scripts/stage1/write_score_edit.py` |
| S1R | `scripts/stage1/README.md` |
| LBL | `scripts/stage1/labels.json` |
| SPEC | `scripts/stage1/selector/spec.py`; SSJ = `scripts/stage1/settings/selector_spec.json` |
| CON / TD | `scripts/stage1_s1/reading/contrast.py` / `scripts/stage1_s1/reading/tdist.py` (B16) |

## Blinding and hard-rule log

- I did not open, list, hash or grep `hosts/`, `judges/`, `judges-pending/`, `seals/`, `retrieved/`, `tmp/judge-pod*`,
  `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, `block-a/`, `block-b/`, any `units/` or `eval/` folder, any
  `COMPLETE.json`, answer, label or cache file, `tmp/stage1-mac-runs-20261023/`, the packed setups, or
  `.ai/inputs/stage1-commitments-20261016/plant/`. Plant files are named here by the path and SHA-256 that other
  records state.
- I read two code files whose paths contain "plant" (BP, RPR), under the brief's carve-out for code. BP shows that
  `plant_record.json` holds the drawn unit and leaf (`"unit": unit, "leaf": leaf_record`) [BP:442]. RPR's output
  `plant_ranks.json` also writes them [RPR:385]. Neither record nor output was opened.
- Two grep commands printed rule-text lines from settings files whose paths contain "plant":
  `scripts/stage1/settings/build_plant.json` lines 121-122 (the "main" and "pilot" rule texts) and
  `scripts/stage1/settings/report_plant_ranks.json` line 17 (the counting-rule text). Both files are W1 settings,
  committed before the plant draw ran on 23 Oct [MAN1:939-942, MAN1:1107-1110; FOCUS:130], so they cannot hold the
  draw. I saw no unit, leaf or cell identity. I report this so the lead can judge it.
- I read `labels.json` (label definitions only, no draw results) and PLANJ (kinds, statuses, timing fields, two unit
  paths that name the A1 edit hash; no output file).

## Summary

1. The design is frozen in PR4 §8 [PR4:665-713] and W1 items 17-25 [W1:288-297]. The plant, the decoy, every plant edit
   and the R600/R150 draws were built on the Mac on 23 Oct [FOCUS:130; BP:25-26].
2. Blocks A and B already scored the plant (75 rows) and decoy (37 rows) pools with J5 (representation pass) and J8
   (content classifier) on pod a-8, through the D-2 wrappers; no D-2 fallback was recorded [ADD:538; FOCUS:112;
   PLANJ `records.d2_fallback` = null, M]. Those outputs are under block A's seal [SEAL:61; FOCUS:106].
3. The kit has no stage-1b block or kind [RULES:505-509, RULES:615-625]; stage 1b was left out of B15's scope
   [ADD:442]. No pilot reader exists (M: no code names `a0_plant` except RPR, the selector and settings).
4. The two counted diagnostics (A1, Self-Inf-N-style on a0_plant) have no runnable route. Engine X's `attributes` job
   takes an a0 trajectory and P's groups and has no `--edit` [ENG:65, ENG:80-83, ENG:87], and the T1 scorers pin the
   wave-0b unit and P's 4,800 rows [WSE:59-68; SIN:5-7]. RPR needs their scores "over the planted corpus's ids
   exactly" [RPR:33-35]. This is the largest build item.
5. Cost (I, measured basis): pilot about $5-7 without the scoring pass, about $7-12 with it and with judges. Main sweep
   (12 runs) about $16-22. The kit's upper spend: $11.01 and $16.46 for the pilot; $33.85 for the 12-run sweep.
6. With about $24 usable, the pilot fits; the main sweep does not. Plan: kit round 34 at $0 now; the pilot from the
   balance after the stage-1 reading; the main sweep on a top-up.
7. One rule gap needs a ruling before the pilot is read: the case "Λ_plant ≥ 10 pp but the lower bound ≤ 5 pp" falls
   under "otherwise stop" in the literal text [PR4:675].

---

## 1. The frozen design of stage 1b

### 1.1 Where it is frozen

- Stage 1 includes "the planted-cause positive control (stage 1b, funded tier)" [PR4:74]. Headline item (2) is worded
  "does each diagnostic find a concentrated, harmful-prompt cause" [PR4:103; W1:75].
- The rules are in PR4 §8 [PR4:665-713] and W1 items 17-25, "committed whether or not it is funded" [W1:288-297]. The
  lead's additions on seeds and draws are in ADD §3 [ADD:298-299]. The anchor circularity rule and the counting list
  are in ADD §8 [ADD:350-351].
- Order: block A, then block B, then "stage 1b (pilot, then main)", then stage 1c; "HarmBench and Granite on judge
  pods, one device per contrast" [PR4:870]. The planted-sweep claims are family 4 in the testing order [PR4:422].
- Cost lines: pilot $4-7, main $11-23, about $17-35 [PR4:852; PLANS:183].

### 1.2 The plant

- Rows: "37 PKU-safe responses whose LEX class is DIRECT (not refusing), to prompts that also have a PKU-unsafe
  response"; prompts disjoint from the S-pool, the anchors and every REQ-6 list; sealed order `stage1-plant-rows-v1`;
  "the first 37, and the first 75 for the pilot's one allowed raise" [PR4:668; W1:289].
- Wording: "PKU red-team prompts with PKU-safe, non-refusing answers, from the same source as the anchors". Never
  "benign-looking". No He-style plant [PR4:669; W1:76].
- Cells: M = 8 (units), M = 32 (within-unit quartiles of target tokens), M = 128 (each quartile in 4 sealed quarters);
  near-duplicate groups stay in one cell; an empty cell stops the build [PR4:670; ADD:184-189].
- Leaf: the unit by `stage1-plant-unit-v1`, then the first leaf in `sealed_order(plant.leaf)` among the unit's 37-row
  leaves with no oversize row; never redraw. "Corpus = 4,837 − n rows; 38 steps for n ≤ 100" [PR4:671; ADD:195].
  The k = 75 variant uses the same leaf (corpus 4,875 − n) [ADD:195].
- Built 23 Oct on the Mac at $0: "REQ-8 wrote the plant (37 and 75 rows), the decoy and every edit" [FOCUS:130].

### 1.3 The decoy (F7)

- "A sealed draw of 37 S-pool rows outside S1, the S3 subset, the S4 list and the plant rows, in a 37-row,
  no-oversize leaf of another unit; never trained"; three labels `stage1-plant-decoy-rows-v1`, `-unit-v1`, `-leaf-v1`
  [PR4:693; W1:295].
- "A scorer that ranks the decoy as high as the plant is topic-driven" [W1:295]. "A1's decoy rank is 'not done' by
  default" [PR4:693].

### 1.4 The pilot and its go rule

- "a0_plant at seeds 1101–1103 against Gate A's a0. Go on if Λ_plant ≥ 10 pp and its one-sided 90% lower bound is
  above 5 pp. If Λ_plant is 5–10 pp, raise k to 75 once and re-pilot. Otherwise stop and report the null." [PR4:675;
  W1:291]
- Interval: "seed-paired on 1101–1103 under the primary model's form: the seed part (the pair's own paired variance,
  J = 3, 2 df) plus the prompt part ...; its one-sided 90% quantile is t(0.90, df) with Satterthwaite df, which is
  1.886 = t(0.90, 2) when the prompt part is 0" [PR4:675].
- PLAN-S counts the pilot as "3 runs + one scoring pass" [PLANS:179]; SPF repeats it [SPF:404].

### 1.5 The main sweep

- "Remove the planted cell at M = 8, 32 and 128; R600 on the planted data; optionally R150" [PR4:678].
- Seeds 1101–1103, "each paired with a0_plant at the same seed. The 1101 rule does not apply" [PR4:679; ADD:298].
- R600 and R150: "a fresh draw per seed, draw d at seed 1100 + d (d = 1–3), by Gate B's per-unit R rule"; labels
  `stage1-plant-r600-v1`, `stage1-plant-r150-v1` [PR4:680; ADD:299].
- So 12 runs (9 removal + 3 R600), or 15 with R150 [SPF:405; RDME:65].

### 1.6 The measures

- Outputs: "Measured Λ_plant(M). Every main-sweep arm is also reported against Gate A's a0 at the same seed ...;
  contrasts against a0_plant carry the note 'comparator selected by the pilot gate'. Each diagnostic's row AUC
  (primary) and top-k hit rate with known truth; the runs-only cost to find the cell, replayed with halving, one-shot
  and bisection; a nested additivity check" [PR4:713].
- The plant-rank report (REQ-29): ranks at M = 8, 32, 128 (cell score = the mean of its rows' scores); the row AUC of
  the plant rows against all Dolly rows and against the drawn unit's Dolly rows with a bootstrap 90% interval
  (`plant.auc_boot`); the dilution table F4; the relocation replay F6; the decoy F7 [PR4:687; W1:294].
- F5: "Λ per planted row with its interval, beside δ_B/600 and r̄/600, labelled a per-row average" [PR4:691].
- At M = 32 and 128 "the competitors' Λ come from a model, and the replay says so" [W1:294].
- Prediction R8.3: "the classifier ranks the planted leaf first at M = 128" [PR4:694].
- Selector planted menus: keep = a0_plant; G_m = U(a0_plant) − U(m) [ADD:256; SSJ:270].

### 1.7 What counts toward "finds a known cause"

- "Only the training-signal diagnostics, A1 and Self-Inf-N-style, scored on a0_plant." The text-only scorers (L1, H1,
  H2a/b, DataShield-style, the classifier) are "construction checks, published before the pilot, and also if the
  pilot stops" [PR4:684; W1:293].
- Self-Inf-N-style counts because REQ-13 was committed at W1 [W1:531; MAN1:841-844].

### 1.8 Conditional items

- F9, two more plant locations: run only if stage 1b is funded and the user says yes; about $34-70; fallback the $0
  relocation replay [PR4:710; W1:296]. Its settings are flagged conditional [MAN1:953-956; ADD:407].
- The disjoint-anchor sensitivity (risk 44): the set must be "chosen and sealed before S1 and before any planted run";
  fallback: "§6 of the paper states the shared source as a limit" [PR4:698; ADD:350]. S1 is "before the stage-1
  freeze, which comes before block A" [PR4:29]. No set was sealed: ADD-8.1 "has no file in the tree" [ADD:407], and
  `labels.json` has no `anchors.disjoint` key (M: grep). Block A has run. So the stop rule "The disjoint-anchor set not
  sealed before S1 → the limit sentence" now applies [PR4:883] (I). It costs nothing; record it.

### 1.9 Frozen and open

| Item | Status | Source |
|---|---|---|
| Plant rows, wording, cells, leaf rule, corpus, 38 steps | frozen and built | PR4:668-671; FOCUS:130 |
| Decoy | frozen and built | PR4:693; FOCUS:130 |
| Pilot arms, comparator, go/raise/stop thresholds, interval form | frozen | PR4:675 |
| Main-sweep arms, seeds, pairing, R600/R150 draw rule | frozen; edits built | PR4:678-680; BP:25-26 |
| Counting rule; construction checks before the pilot | frozen | PR4:684 |
| Plant-rank report content (REQ-29) | frozen and built (not run) | PR4:687; MAN1:729-732 |
| F5, R8.3, outputs, "comparator selected by the pilot gate" | frozen | PR4:691, 694, 713 |
| Disjoint anchors | frozen fallback now triggered (I) | PR4:698, 883; ADD:407 |
| F9 | conditional; needs the user's yes and money | PR4:710 |
| **Open O1**: the gap "Λ ≥ 10 pp, lower bound ≤ 5 pp" and the edges at exactly 5 and 10 pp | literal text: "otherwise stop" | PR4:675 |
| **Open O2**: the exact interval formula (which item-part estimator) | form named, code not | PR4:675 |
| **Open O3**: which a0_plant seed and checkpoints feed A1 and Self-Inf-N | not stated ("scored on a0_plant") | PR4:684 |
| **Open O4**: when the scoring pass runs, and whether it runs if the pilot stops | "3 runs + one scoring pass" is PLAN-S text only | PLANS:179 |
| **Open O5**: judge timing for the pilot units | PR4 says judges on judge pods | PR4:870 |
| **Open O6**: R150 | optional | PR4:678 |
| **Open O7**: blinding of the construction checks against the lead's rule | "published before the pilot" | PR4:684 |
| **Open O8**: the competitor model for the replay at M = 32, 128; the additivity formula; δ_B and r̄ for F5 | named, not specified in code | W1:294; PR4:691, 713 |

---

## 2. What exists

### 2.1 Builders and records (path and SHA-256 only)

| What | Path | SHA-256 | Source |
|---|---|---|---|
| Plant builder (REQ-8, code) | `scripts/stage1/build_plant.py` | `f1c91dc7…` | MAN1:295-298 |
| T1 plant settings | `scripts/stage1/settings/build_plant.json` | `06f70d98…` | MAN1:939-942; W1:290 |
| F9 and decoy settings (conditional file; decoy part unconditional) | `scripts/stage1/settings/build_plant_extra.json` | `df5f0472…` | MAN1:953-956; ADD:407 |
| REQ-8's text-free record (holds unit and leaf: never open) | `.ai/inputs/stage1-commitments-20261016/plant/plant_record.json` | `cc04b663…` | RULES:371-372; FOCUS:130 |
| Three remove-only edits (beside the record) | same folder, `edits/remove_cell_m8/m32/m128.json` (I: BP:290, 309-314) | not stated in the sources read | FOCUS:130 |
| Plant pool (75 rows) | text under git-ignored `tmp/stage1-mac-runs-20261023/` | `37739f40…` | RULES:373; FOCUS:129-130 |
| Decoy pool (37 rows) | same | `d102b665…` | RULES:374; FOCUS:129 |
| Text-bearing edits: `planted_k37`, `planted_k75`, `r600_k{37,75}_d{1,2,3}`, `r150_k{37,75}_d{1,2,3}` | same | listed in the plant record (not opened) | BP:25-26, 304-333 |
| Filled pool pins (D-2) | `.ai/inputs/stage1-post-w1-20261023/pool-pins/representation_pools.filled.json` | `a33e9664…` | RULES:369-370; FOCUS:129 |
| D-2 package | `scripts/stage1_s1/d2_pool_pins/` | pinned in `D2_CODE` | RULES:359-368 |

- The plant files are not W1 "sealed records": the W1 manifest has 7 of those, and none is a plant file [MAN1:84;
  M]. The plant was built after the W1 freeze [FOCUS:130 vs FOCUS:143].
- Every edit's record entry holds its SHA-256, engine arm, rows, steps and a token account [BP:291-294]. The record
  also holds `unit`, `leaf` and the decoy's unit and leaf [BP:442-446].

### 2.2 What blocks A and B already scored on the plant and decoy pools

- **J5 (rep_pass, REQ-3 through `d2_representation_pass.py`)**: "a main pass over plant, decoy and s3_safe, then a
  pools-only pass over s3_orig after J6 (pod a-8, both complete)" [ADD:538; KR:449-451]. Only the 75-row plant pool
  is passed; the 37 rows are its first 37 [S1R:46]. These θ0 features feed L1 and DataShield-style for the plant and
  decoy rows [RPR:37-38].
- **J8 (classifier, REQ-23 through `d2_score_classifier.py` with `--pool` for plant and decoy)** [KR:451-452;
  ADD:487]. REQ-23 writes per-row normalized Unsafe scores for the 4,800 rows, the 75 plant rows and the 37 decoy rows
  [PR4:695].
- Both completed on a-8 [FOCUS:112; PLANJ `hosts.a-8.jobs` statuses complete, M]. **The D-2 fallback was not used**:
  `records.d2_fallback` is null (M), so the rows are not "not run" [ADD:470, ADD:487].
- These outputs are sealed files under block A's seal: only `JOB-DONE.json`, cost ledgers, fingerprints and receipts
  are readable [SEAL:61; KR:433-440]. So the construction checks can only run after the stage-1 reading lifts the seal,
  or after a recorded ruling (I).
- Not scored on the plant: A1 and Self-Inf-N-style on a0_plant (a0_plant does not exist); A1 on the decoy ("not done"
  by default) [PR4:693].
- Not recorded in FOCUS (M: no entry names a run): the Mac runs of DataShield-style (REQ-12) and Self-Inf-N-style
  (REQ-13) on P, and any run of the plant-rank report. RPR takes DataShield's output as an optional input [RPR:6].

### 2.3 Reader and analysis code

| Code | State | Source |
|---|---|---|
| `report_plant_ranks.py` (REQ-29) | built, in MAN1, never run (I). PR4's "Not built at HEAD" predates the build | MAN1:729-732; PR4:687 |
| It needs counted scores "over the planted corpus's ids exactly"; without them it prints "not run (S1)" | built | RPR:33-35, 239, 375-381 |
| Its output names the planted unit and leaf | built | RPR:385 |
| Selector planted menus (unit, quartile, quarter; keep = a0_plant) and a replay entry | built | SSJ:252-271; SPEC:5-7, 1127-1130 |
| A model for the competitors at M = 32 and 128 in the replay | not found (M: no "competitor" in SPEC or predict.py) | W1:294 |
| B16's paired contrast with item part and Satterthwaite df; t quantile | built; reusable as functions | CON:125, 168; TD:93 |
| A pilot reader (Λ_plant, interval, go/raise/stop) | missing (M) | — |
| A main-sweep reader (Λ_plant(M), F5, additivity) | missing (M) | — |

### 2.4 The comparator

- Gate A's a0 units at 1101, 1102 and 1103 are pinned by path and `COMPLETE.json` SHA-256 [RULES:171-183]. They were
  re-judged on block A's judge pods [RULES:163-170; FOCUS:106], so HarmBench and Granite exist for them on the same
  A100 route [RULES:139-142]. They stay sealed until the stage-1 reading [KR:433-440].
- Stage 1 already pairs new recipe-S arms with these reused units [RULES:212; ADD:256]. The a0_plant runs follow that
  route (recipe S, training identity checked [RULES:338-340]).

---

## 3. What is missing, and what it would take

All items reuse the kit and engine X unchanged where possible, as D-2 and D-3 did (wrappers that load W1 files by
hash; no W1 file edited) [ADD:466-470, ADD:541-545].

| # | Missing piece | What exists | What it takes (files, tests, mutation) |
|---|---|---|---|
| K1 | A stage-1b block | `BLOCKS` = S1-0, cert, A, certify, B, C [RULES:615]; `BLOCK_KINDS` has no plant kind [RULES:619-625]; "stages 1b and 1c are outside B15's first scope" [ADD:442] | Add blocks (my default: `P1` pilot, `P1b` k = 75 re-pilot, `P2` main) to `BLOCKS`, `FUNDING_BLOCK`, `HOST_PREFIX`, `BLOCK_KINDS`, `REJUDGED_PINS` (empty, as block B [RULES:171]). Init gates as certify/B have: block B complete and sealed [PT:819-823], G1 branch, G3 plan-A/B. `P2` init also needs a recorded pilot decision "go" by SHA-256. Tests per gate; mutants for each refusal. |
| K2 | Edit sources for the plant arms | `resolve_edit` reads MAN1, Gate B's MANIFEST, or a lead's sealed edit record `{edits: [{arm, draw, path, sha256}]}` [PT:834-871] | A small Mac tool (S1-style package) that reads `plant_record.json` by its pin and writes only `{arm, draw, path, sha256, steps}` for `a0_plant` (planted_k37), `a0_plant75`, `plant_m8`, `plant_m32`, `plant_m128`, `plant_r600`, `plant_r150` (and k75 variants). It must never write or print unit, leaf, cell, decoy or token accounts (a test on a synthetic record checks the output holds none of them). Recorded through the kit's sealed-record route [PT:845-851]. |
| K3 | Draw keys and steps | Draws are keyed only for arm `R` [PT:859]; steps come from `ARM_DOSE`/`DOSE_STEPS` (33/38/38) [RULES:215-218] | Key `plant_r600`/`plant_r150` by d = seed − 1100 (matches the plant rule [ADD:299; BP:322-332]). Take steps from the record's edit entries [BP:293]: by ceil(rows/128) [BP:66], a0_plant 38, m128 38, m32 37, m8 and R600 33, R150 37 (I). Allow seed 1101 for plant arms [ADD:298]. Timing in the kit only; the engine counts its own steps from the edit [JR:399-403]. |
| K4 | The pilot pod | Kind `arm` runs `calibrate --edit` then the O-ext step [JR:399-408]; the pack seals the edit by SHA-256 [JR:573-588, 602-615] | One engine-X pod, explicit `hosts` launch [PT:75-79], 3 counted jobs (≤ 4 [RULES:55]), Branch 128, recipe S. `check-plan` on a dry pack. Reuse kind `arm` (my default) or add `plant_arm` if reuse breaks an arm-table test. |
| K5 | Judges, seal, backup for the new blocks | Generic by block for blocks other than A [KR:287-308, 365-368, 387-395]; judged kinds include `arm` [RULES:160] | Tests that `units-of-block`, `record-judges`, `seal.py block` and the backup accept `P1`/`P2` like block B, with empty re-judged pins. |
| K6 | The pilot reader | B16 functions [CON:125, 168; TD:93]; per-prompt U extraction in `scripts/stage1_s1/reading_input/` (reuse to check) | New S1 package (Mac, $0): per-prompt U for the 3 new units (by `COMPLETE.json` SHA-256 from plan.json) and Gate A's 3 a0 units [RULES:171-183]; Λ_plant, seed part (2 df), item part, Satterthwaite df, one-sided 90% bound, the label (go / raise / stop) by the lead's written ruling on O1. Known-answer tests (t(0.90, 2) = 1.886 [PR4:675]; edges at 5 and 10 pp; the gap case), a mutation spec, frozen by hash and time-stamped before any pilot unit is read (as PLAN31:34, 39-40 do for the reading). |
| K7 | A1 and Self-Inf-N-style on a0_plant | Engine `attributes` takes `--a0-state CHECKPOINT=RUN_DIR` and `--groups`; `--edit` is for run-one only [ENG:80-83, ENG:87]. J21 runs it on a retrain's q and e1 with P's 8 groups [JR:468-489]. T1's A1 contract pins the wave-0b unit and P's 4,800 rows [WSE:59-68]; Self-Inf-N reads only that unit [SIN:5-14] | A new S1 wrapper that computes A1's `checkpoint_gradsim` bi-anchored cosine at [q, e1] and Self-Inf-N's grad_norm at q for every row of the planted corpus (Dolly rows plus `add-plant-*` rows), with engine X's own functions loaded by hash (engine unchanged). Output: T1 scorer outputs over the planted corpus's ids, as RPR requires [RPR:33-35, 375-381]. A golden check: on P's rows it reproduces engine X's per-row values exactly. A kit kind (e.g. `plant_score`, J22) linked to the a0_plant@1101 arm on the same pod, like `a1_rescore` [RULES:524-525], priced at 3.04 h measured upper [RULES:86]. Whether `--a0-state` accepts an edit arm's states is UNVERIFIED. |
| K8 | Construction checks | RPR built [MAN1:729-732]; inputs (J5 rows, J8 output, L1, DataShield) under block A's seal [SEAL:61] | Run RPR after the stage-1 reading, without `--counted`. Its output names the leaf [RPR:385]: commit it by SHA-256 unopened (my default), open it after the counted scores exist. Check whether RPR supports k = 75 (it reads `settings["k"]` [RPR:385]; not verified). |
| K9 | The main-sweep reader | Selector replay [SPEC:1127-1130] | Λ_plant(M) against a0_plant and against Gate A's a0 [PR4:713]; F5 [PR4:691]; the additivity check; the runs-only replay with a written competitor model [W1:294]. Specify before P2's outcomes are read. Not needed for the pilot. |
| K10 | Records | — | An addendum section with the rulings O1-O8 before the pilot is read; FOCUS entries; the stamp. |

---

## 4. Cost

### 4.1 Measured stage-1 basis

- Block B: the 21 pods cost **$141.27 for 75.04 GPU-h** [FOCUS:76], so $1.88 per GPU-h and 3.57 GPU-h per pod (M).
  This includes the twelve 1 h self-stop waits ($21.48) [FOCUS:87].
- Arm job time (I): block-B 4-arm pods ran about 2.3-3.3 h from job start to job end, so **0.57-0.82 h per arm**
  (job starts by about 15:50 UTC [FOCUS:90] or 16:57 UTC for b-21 [FOCUS:88]; job end about 1 h before the EXITED times
  [FOCUS:87]).
- Pod overhead (I): 0.28-0.39 h per pod (b-17 2.9 pod-h for a 2.62 h job [FOCUS:83]; b-18 1.9 pod-h for 90.6 min
  [FOCUS:81]; b-19 2.98 pod-h for 156.9 min [FOCUS:80]).
- Judges: block B's 72 units, HarmBench 59.4 min $1.77 and Granite 63.5 min $1.89 [FOCUS:76]; block A's 27 units,
  $1.67 for both [FOCUS:106]. Setup dominates, so 3-15 units cost about $1.2-2.5 for both (I).
- A1-type re-score: the kit uses Gate B's whole diagnostics job, 3.04 h, as its measured upper [RULES:78-86]. The
  LN-12 pod ran 19 jobs, two of them re-scores, in 411 min [FOCUS:115]; with the other jobs at their kit values, each
  re-score took about 1.2-1.6 h (I, weak).
- Kit rules: arm measured upper 52 min + O500 1,024 s (Branch 128) = 4,144 s; a 38-step arm's start requirement
  9,418 s; overhead 42 min; $1.79/h spend; $1.85/h planning; $6 reserve; contingency × 1.25 [RULES:36-46, 61-65,
  660-698, 815-822, 958-969; PLANJ `hosts.b-1.jobs[3]`].

### 4.2 The pilot

| Part | Measured basis (I) | Kit upper spend (E, the kit's formulas) |
|---|---|---|
| 3 a0_plant arms on one pod | 2.06-2.81 pod-h = **$3.69-5.03** | cap 5.75 h; **$7.43** |
| Judges (3 units; caps 1.0 h each) | about $1.2-1.7 | $3.58 |
| Scoring pass (A1 + Self-Inf-N on a0_plant@1101) | 1.2-3.04 h = $2.1-5.4 | +$5.44 (pod cap 9.25 h) |
| **Pilot without scoring** | **about $4.9-6.7** | **$11.01** (cap-based funding need × 1.25: $21.34) |
| **Pilot with scoring** | **about $7.0-12.1** | **$16.46** (cap-based funding need × 1.25: $28.89) |
| k = 75 re-pilot, only if Λ is 5-10 pp | +$4.9-6.7 | +$11.01 |

Add about $1 per day of storage for the three kept pods (idle about $0.04/h [PLAN31:14]) and B14's similarity pass,
about $1 [PLAN31:31]. A finisher that dies adds 1 h per pod ($1.79) [FOCUS:87].

### 4.3 The main sweep

| Option | Measured basis (I) | Kit upper spend (E) | Cap-based funding need (E) |
|---|---|---|---|
| 12 runs (M = 8, 32, 128 + R600; 3 pods of 4) + judges | $14.1-19.5 + $1.5-2.5 = **about $16-22** | **$33.85** | $49.92 (one pod per launch); $56.06 (three at once) |
| 15 runs (+ R150; 4 pods) + judges | about $19-27 | $42.18 | $60.34 |

Stage 1b in total (pilot with scoring + 12 runs): about $23-34 (I), inside the frozen $17-35 [PR4:852] only at its top.

### 4.4 What fits in about $24

- Balance $29.94 at 22:13 UTC on 31 Oct; reserve $6 [FOCUS:75; RULES:46]. After B14's pass and a few days of storage,
  about $18-22 is usable at the pilot's launch (I).
- **The pilot fits**, with or without the scoring pass, even at the kit's upper spend ($16.46). The $6 reserve holds.
- **The main sweep does not fit** after the pilot: about $6-15 would remain (I), against $16-22 measured and $34 upper.
  It needs a top-up of about $15-25 on the measured basis, or about $35 to cover the upper spend.
- Under the user's rule a block may start from the balance with a funding record at the plan's cap-based need
  [KR:377-383]; the guard is off [KR:168-182]. So the kit does not block on the balance; the lead's reserve and $10
  alert are the limits.
- No money conflict with OLMo 3: its probe costs $266-390 and must launch by 13 Nov [PLAN31:61]; it needs a top-up in
  any case (I). The conflict is the lead's time: the probe's three $0 blockers are also pending [PLAN31:73-74].

---

## 5. Order of work and recommended plan (kit round 34)

### 5.1 Order

1. **Now ($0):** an addendum section with the rulings below (O1-O8, D1-D10), written before any stage-1b unit exists.
2. **Kit round 34 ($0, builder workflow with verifiers, as earlier rounds):** K1-K5 and K6 (the pilot reader).
   Run the kit suite and the mutation runner (baseline first, same command) [KR:321-322].
3. **Round 34b ($0, in parallel):** K7, the a0_plant scoring wrapper, with its golden check. It is the largest item.
4. **After the stage-1 reading ($0, Mac):** K8, the construction checks by RPR without `--counted`; commit the output
   by SHA-256, unopened.
5. **Pilot block P1 (about $7-12):** one pod (3 a0_plant arms + the scoring job), a live finisher in the lead's
   session [FOCUS:87], then the judges, `record-judges`, `seal.py block P1`, then the frozen pilot reader. Record the
   label. Stop and ask the user [PR4:887].
6. **If "raise":** P1b, k = 75 at 1101-1103 (about $5-7), the same reader, once.
7. **If "go", on a top-up:** P2, 12 runs (+3 if R150 is funded), judges, seal; then RPR with `--counted`; open the
   plant-rank output; K9's reader.
8. **If "stop":** report the null and the construction checks [PR4:684]; stage 1b ends.

### 5.2 Decisions for the lead (default, fallback, trigger)

| # | Decision | Default (ambitious) | Pre-set fallback and trigger |
|---|---|---|---|
| D1 | Block layout | Separate blocks P1, P1b, P2, each with its own funding record and seal | One block P with a held second launch, as block B's second phase [KR:326-337]; trigger: K1's gate logic is not verified in one fix round |
| D2 | Job kind | Reuse `arm` with new arm names and a sealed edit record | New kind `plant_arm` (J22); trigger: reuse breaks an arm-table or deal test |
| D3 | The scoring pass (O3, O4) | On the pilot pod, linked to a0_plant@1101, at A1's checkpoints q and e1 (A1's contract is "at a0-1101's q and e1": `scripts/stage1/settings/write_score_edit.json`, key `a1.edit_name`; Self-Inf-N at q [SIN:7-10]) | Run the pilot without it; score later after a train-only regeneration of a0_plant@1101 on P2's pod, accepted only on an equal e1 fingerprint (LN-12's rule [S1R:71]); if P2 never runs, report "not run (S1)" [RPR:239]. Trigger: K7 not verified when P1 is planned, or the balance at launch is below $16.46 + $6 |
| D4 | Judges for the pilot (O5) | P1 judged on its own before its seal | `record-judge-not-run` for P1 [KR:287-297] and judge its 3 units with P2's units; trigger: balance short at P1's end |
| D5 | The go-rule gap (O1) | The literal text: Λ ≥ 10 pp with a lower bound ≤ 5 pp falls under "otherwise stop"; Λ = 10.00 goes to the first test; 5 ≤ Λ < 10 raises | Read the gap as the 5-10 band (one k = 75 re-pilot), recorded as a post-W1 deviation before the pilot is read. This is a scientific-rule choice: raise it to GPT and the user |
| D6 | Interval formula (O2) | B16's paired form with the crossed item part and Satterthwaite df [CON:125, 168] | Seed part only, t(0.90, 2) = 1.886 [PR4:675]; trigger: per-prompt tables for Gate A's units cannot be built |
| D7 | Blinding of the construction checks (O7) | Run them after the reading, commit by SHA-256 unopened before the pilot, open after the counted scores | Publish them readable before the pilot (the literal word), accepting that the lead learns the leaf before A1 on a0_plant is scored; trigger: the user or GPT reads "published" as "readable" |
| D8 | O-ext on plant arms | Keep: the same arm job as every stage-1 arm [JR:399-408] | A no-O-ext plant kind (saves about 0.28 h per arm, I: O500 1,024 s [RULES:61-62]); trigger: money blocks the 12-run sweep |
| D9 | R150 (O6) | Off | On if a top-up covers about +$4-6 (I) |
| D10 | F9 and disjoint anchors | F9 not run (no money; needs the user's yes); record the triggered disjoint-anchor fallback | F9's frozen fallback, the $0 relocation replay [PR4:710] |
| D11 | Pilot timing against the reading | Launch P1 after the stage-1 reading (the plan's order [PLAN31:57]) | Launch P1 as soon as round 34 is merged and keep its units sealed; read them after the stage-1 reading. Trigger: the reading is delayed by the stamp (PLAN31:34) |
| D12 | Money | P1 from the balance; P2 on a top-up | Wait for a top-up before P1; trigger: balance below the pilot's upper spend + $6 |
| D13 | O8, the sweep's open formulas | Write the competitor model, the additivity formula and F5's δ_B and r̄ sources before P2 is read | Report the replay "measured cell only" and say so; trigger: not written before P2's units exist |

---

## 6. Challenge: simpler options, weak points, failure cases

- **Smallest decisive check:** the pilot itself, 3 runs, about $5-7 without scoring. Before any money: `check-plan`
  on a dry pack with one planted arm, and K7's golden check on P's rows.
- **Simpler alternative (not recommended):** skip K7 and report A1 and Self-Inf-N as "not run (S1)". Then no
  diagnostic can count toward "finds a known cause" [PR4:684], and headline item (2) has no subject.
- **Weak assumption 1:** the plant can add ≥ 10 pp over a background already near 45 pp (Gate A probe U 3.2% → 46.7%
  [FOCUS:65]; PLAN-S names this risk [PLANS:252]). 37 of about 4,800 rows is 0.8% of one epoch (I). The pilot gate
  exists for this.
- **Weak assumption 2:** engine X's gradient code can score rows that are not in P. ENG shows no route [ENG:80-83];
  PR4 calls rows outside the corpus UNVERIFIED [PR4:693].
- **Failure case: states lost.** The light pull leaves `*.safetensors` on the pod [KR:202-204] and a stopped kit pod
  is never restarted [KR:481-483]. If the scoring job is not on the pilot pod, a0_plant's states are gone; only a
  fingerprint-checked regeneration brings them back (D3).
- **Failure case: a dead finisher.** Each unpulled pod stops itself 1 h after its job [FOCUS:87].
- **Failure case: the balance runs out mid-pod.** It went to −$0.02 on 31 Oct [FOCUS:79].
- **Failure case: a leak.** The plant record, any plant edit file, `plant_ranks.json` and the a0_plant edit's removed
  row ids can name the unit. Only hashes and names may be printed (K2's test).
- **Sequencing constraint:** the pilot reading needs Gate A's a0 per-prompt values, which are sealed in block A until
  the stage-1 reading [KR:433-440]. So the pilot cannot be read before the reading.

## 7. Not verified

- Per-job durations (they are in sealed host trees and in `block-a/`/`block-b/` cost reports, which I did not open).
  The arm and re-score times above are inferences.
- Whether `--a0-state` accepts an edit arm's states, and whether `report_plant_ranks.py` supports k = 75.
- Whether the Mac runs of DataShield-style and Self-Inf-N-style on P have happened (no FOCUS entry found).
- The plant record's edit list, the remove-edit file names and their SHA-256s (not opened; inferred from BP).
