# Task A-check: an adversarial check of the stage 1b readiness report

Read-only check for the lead (GI VIII). Written 2026-11-01; clock checked at 04:37 UTC (`date -u`). Sources: the
main checkout `/Users/spiderishi/Coding/attribution` (branch `stageb-costs-and-recovery-safeguards-20261003`, HEAD
`0daca9a`) and the report under check. Only read commands ran. No test, builder, kit, judge, seal or launch command
ran. No repository file changed. This file is the only write.

Tags: (R) read in a source; (M) measured here by a read-only command; (I) my inference; (E) my estimate.

## Verdict

**Usable with corrections. Do not adopt it as written.**

- Its account of the frozen design is right on the points asked: seeds, menu sizes, the go rule and the counting
  rule (§1). Its kit arithmetic is right; I reproduced the caps and uppers from the kit's formulas (§1, §3).
- Four problems matter:
  1. **Blinding (§2).** It misses two leak paths. The a0_plant unit's own COMPLETE.json names the planted leaf in
     plain text (B1). The counted score files name the leaf by omission (B2). And its D7 fallback would show the
     leaf to the lead before the counted diagnostics score (B3).
  2. **Sequencing (§4).** Its reason why the pilot must wait for the stage-1 reading is wrong. Gate A's a0 values
     are not sealed; they were read before stage 1. The real links are the construction checks (their inputs sit in
     block A's seal) and the kit round (the reading loads the kit's rules file).
  3. **Two "not verified" items are settled by the code (§5).** Engine X's attribution step refuses a0_plant's
     states, so the scoring wrapper is new code. The plant-rank report cannot do k = 75 without a post-W1 change.
  4. **Scope and money (§3, §5).** The pilot needs no judges, no second or third block, no per-seed draw keys and
     no scoring job on its pod. A smaller round gets the pilot out sooner. It costs about $0.7–1 more if the pilot
     goes, and saves about $2–5 if it stops.
- The report's author printed lines from two settings files whose paths contain "plant" (B4). That breaks the
  literal hard rule. The risk is low, because both files predate the draw. The author disclosed it.

## Source key

Paths are relative to the main checkout, except READY. Line numbers are those on 2026-11-01.

| KEY | Path |
|---|---|
| READY | `/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/next-stages/A-stage1b-readiness.md` (the report under check) |
| PLAN31 | `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md` |
| FOCUS | `research/FOCUS.md` |
| PR4 | `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` (frozen) |
| W1 | `research/experiments/2026-10-16-stage1-commitments.md` |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` |
| PLANS | `research/review/2026-10-08-sharpened-direction-DRAFT.md` (PLAN-S) |
| SPF | `docs/study-plan-full.md` |
| RDME | `README.md` |
| MAN1 | `.ai/inputs/stage1-commitments-20261016/MANIFEST.json` |
| RULES | `runkit/stage1-olmo/stage1_rules.py` (byte-equal to the `tmp/stage1-olmo/` copy, M: `cmp`) |
| PT | `runkit/stage1-olmo/plan_tool.py` (byte-equal, M) |
| JR | `runkit/stage1-olmo/setup/job_runner_stage1.py` (byte-equal, M) |
| SEAL | `runkit/stage1-olmo/seal.py` (byte-equal, M) |
| KR | `runkit/stage1-olmo/README.md` (byte-equal, M) |
| RCPT | `tmp/study-v2-20261002/process_receipt.py` (the kit packs it: `runkit/stage1-olmo/pack_setup.py:80`) |
| ENGM | `experiments/safety_selection/__main__.py` (engine X's CLI) |
| RUN | `experiments/safety_selection/runner.py` |
| EDT | `experiments/safety_selection/edits.py` |
| LED | `experiments/safety_selection/ledger.py` |
| VER | `experiments/safety_selection/verify.py` |
| RCFG | `experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json` (recipe S) |
| JU | `scripts/gate_b_mac_judges/units.py` |
| BP | `scripts/stage1/build_plant.py` (code; read under the brief's code carve-out) |
| RPR | `scripts/stage1/report_plant_ranks.py` (code; read under the carve-out) |
| S1R | `scripts/stage1/README.md` |
| CON | `scripts/stage1_s1/reading/contrast.py` (B16) |
| TD | `scripts/stage1_s1/reading/tdist.py` (B16) |
| RIM | `scripts/stage1_s1/reading_input/__main__.py` |
| RIB | `scripts/stage1_s1/reading_input/build.py` |
| LBL | `scripts/stage1/labels.json` (the draw-label registry; no draw result) |

## Hard-rule log (this check)

- I did not open, list, grep or hash: `hosts/`, `judges/`, `judges-pending/`, `seals/`, the kit's `retrieved/`,
  `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, `block-a/`, `block-b/`, any `units/`
  or `eval/` folder, any COMPLETE.json, answer, label, guard-sample or judge-cache file, the hidden or selector
  bank, `tmp/stage1-mac-runs-20261023/`, the packed setups, `tmp/stage1-olmo/plan.json`, or any file whose path
  holds "plant" or "decoy" except BP and RPR.
- I read BP and RPR (code) under the carve-out. I did not open their settings files. I name those files only by the
  path and SHA-256 that MAN1 and the code pins state.
- I listed the top level of `tmp/stage1-olmo/` once, with the sealed folder names filtered from the output. It shows
  file names only (logs, scripts, plan.json).
- I loaded MAN1 and LBL with Python to read keys and roles only.
- I saw no unit, leaf, cell or decoy identity.

---

## 1. The frozen design: does READY match the sources?

### 1.1 What READY gets right (checked)

- **Pilot seeds and comparator.** a0_plant at 1101–1103 against Gate A's a0 (READY:118-120; PR4:675; W1:291).
- **Main-sweep seeds.** 1101–1103, each paired with a0_plant at the same seed; the 1101 rule does not apply
  (READY:129; PR4:679; ADD:298; W1:292). R600 and R150 use draw d at seed 1100 + d, d = 1–3, per unit
  (PR4:680; ADD:299). The lead accepted parts (d, g) (ADD:308). BP draws them that way (BP:322-326).
- **Menu sizes.** M = 8 (units), 32 (within-unit quartiles of target tokens), 128 (four sealed quarters per
  quartile) (READY:101-102; PR4:670; W1:290).
- **Go rule.** Quoted exactly (READY:118-120; PR4:675).
- **Counting rule.** Only A1 and Self-Inf-N-style, scored on a0_plant, count; the text-only scorers are
  construction checks, "published before the pilot, and also if the pilot stops" (READY:150-153; PR4:684;
  W1:293). Self-Inf-N counts: REQ-13 is in MAN1 as code (MAN1:841) and is not in the `not_built` list
  (MAN1:2088 onward; M).
- **Interval form.** B16 already has the exact form PR4:675 asks for. `contrast_paired` takes the pair's own
  paired variance with J − 1 df and adds the crossed item part with Satterthwaite df (CON:113-130, 168-173).
  READY's D6 default points to it (READY:358).
- **Step counts** in K3 (READY:262) are right, because the plant replaces the leaf (1.2 point 1). With n = 37,
  a0_plant has 4,800 rows (38 steps), M = 128 removal 4,763 (38), M = 32 removal 4,650 (37), M = 8 removal and
  R600 4,200 (33), R150 4,650 (37) (I, arithmetic: ceil(rows/128), BP:66).
- **Kit figures.** I reproduced the pilot's cap and upper from the kit's formulas (M, arithmetic). Three 38-step arm
  jobs at 4,144 s each (52 min + O500 1,024 s at Branch 128: RULES:61-62, 65; Branch 128 in force: FOCUS:124).
  Cap: 2,520 + 2 × 4,144 + 9,418 = 20,226 s, rounded up to 5.75 h (RULES:36, 815-822). Spend upper:
  2,520 + 3 × 4,144 = 14,952 s = 4.15 h × $1.79 = $7.43 (RULES:45). The 9,418 s start requirement is READY's
  figure from plan.json, which I did not open.

### 1.2 What READY misses or states loosely

1. **It never says that the plant replaces the leaf's Dolly rows.** PLAN-S: "the plant replaces that leaf's Dolly
   rows, so the run keeps 4,800 rows and 38 steps" (PLANS:177). The formulas say the same: corpus 4,837 − n, and
   4,875 − n at k = 75 (ADD:195). So do RPR:9-10, BP:297-300 and RDME:65. This matters for blinding (§2, B2) and
   for R600: its draw runs over the planted corpus, plant rows included (ADD:299; BP:323, 328-329).
2. **The leaf rule drops its fallback** "or, if there is none, its no-oversize leaves with the smallest |n − 37|"
   (READY:103-104 against PR4:671; W1:290). Minor.
3. **"Blocks A and B already scored the plant ... on pod a-8"** (READY:63). Only block A did. Pod a-8 ran J5, J7
   and J8 in block A (FOCUS:112; ADD:538).
4. **The go-rule "gap" (O1, READY:76-77, 178).** The literal text is not silent. "Otherwise stop" covers
   Λ ≥ 10 pp with a lower bound ≤ 5 pp (PR4:675). Only the two edges need a ruling (Λ exactly 5 or exactly 10).
   They can happen: U moves in steps of 1/6 pp per seed (600 answers, PR4:185, 227), so a three-seed mean moves in
   steps of 1/18 pp (I). Any other reading of the band changes a frozen rule (PR4:886). Write it before P's units
   exist, not only before they are read.
5. **The sign of Λ_plant is not written.** `contrast_paired` returns c − m (CON:171-173). The pilot reader must use
   c = a0_plant and m = Gate A's a0, so that a plant that raises U gives a positive Λ. Put this in the ruling.
6. **The k = 75 re-pilot's seeds and comparator are not stated** (PR4:675). The natural reading is 1101–1103 against
   Gate A's a0 again. Record it.
7. **RPR's Self-Inf-N switch.** RPR counts Self-Inf-N only "while the settings' switch says REQ-13 was committed at
   W1" (RPR:31-33, 228-229). The switch is in RPR's settings file, which I did not open (path rule). The lead
   should confirm that it is on.

---

## 2. Blinding: what would show the leaf, or break blinding otherwise

### B1 (high): the a0_plant unit's own COMPLETE.json names the leaf

- BP writes the planted_k37 and planted_k75 edits with this title as the edit's name: "stage1 plant: planted
  corpus at k = {k} (leaf {cell})" (BP:282-287, 306-308).
- The engine's edit summary carries the name (EDT:90-92). run-one writes that summary into its result (RUN:496-497).
  The result goes into COMPLETE.json (RUN:293-295; LED:129-136). The run folder also keeps a copy of the edit file,
  `edit.json` (EDT:45; VER:248-251).
- So every a0_plant and a0_plant75 unit names its leaf in plain text. The pilot reader must read these units,
  because U is computed in the unit's evaluation (RUN:481-486, 635-647).
- The kit's readable files do not carry the name. JOB-DONE's verify tail is engine-verify output (JR:1022-1025),
  which holds no edit name (VER:263-267). Receipts hold the command, the timing and the exit code (RCPT:7-17). The
  packed edit is named by its SHA-256 (JR:235-237). The judge enumeration reads only arm and seed from the
  trajectory (JU:147-149).
- READY's leak list (READY:385-386) and its pilot reader K6 (READY:265) do not mention this.
- **Fix.** The pilot reader reads U and the per-prompt labels by key only. It never prints or writes any other
  field. A test feeds a synthetic COMPLETE.json whose edit name holds a sentinel string, and asserts that the
  sentinel never reaches stdout, stderr, a traceback or the output file. Rule for the lead and every helper: nobody
  opens a plant-arm unit folder by hand until the counted outputs are hashed.
- The remove-cell, R600 and R150 edits also list the leaf's rows (BP:309-314, 328-331). The same rule covers their
  units.

### B2 (high): the counted score files name the leaf by omission

- RPR requires each counted input to cover "the planted corpus's ids exactly" (RPR:33-35, 374-379). That set is
  P's ids minus the leaf's Dolly rows, plus the plant ids (RPR:374). So the key set of the scoring wrapper's
  output (K7) shows which Dolly rows are missing: the leaf.
- READY's K7 (READY:266) does not say this.
- **Fix.** K7 writes under a path that contains "plant". The lead commits its SHA-256, and stamps it, before
  anyone opens it. That is the point at which "the diagnostics have scored". Only then RPR runs with `--counted`.

### B3 (high): D7's fallback breaks the lead's blinding rule

- READY:359's fallback: "Publish them readable before the pilot ..., accepting that the lead learns the leaf before
  A1 on a0_plant is scored". RPR's output names the planted unit and leaf (RPR:384-388). The brief forbids exactly
  this.
- **Fix.** Strike the fallback. "Published before the pilot" (PR4:684; W1:293) is met by a committed, stamped
  SHA-256. Write that reading down as a ruling. If the pilot ends with "stop", the counted diagnostics never score,
  so the checks can then be opened (they are published "even if the pilot stops": W1:293).

### B4 (medium): READY's author printed lines from two "plant" settings files

- READY:51-55: two greps printed lines 121-122 of `scripts/stage1/settings/build_plant.json` and line 17 of
  `scripts/stage1/settings/report_plant_ranks.json`. The carve-out covers code only, so this breaks the literal
  rule.
- The risk is low. Both files are W1-frozen: MAN1:939-942 (`06f70d98…`) and MAN1:1107-1110 (`c952eb72…`), equal
  to the code pins BP:59-60 and RPR:61-62. W1 was committed on 22 Oct (FOCUS:143). The draw ran on 23 Oct
  (FOCUS:130). So the files cannot hold the draw. The lead should still record the breach.

### B5 (medium): the forbidden list misses the kit's pulled trees

- The seal hashes each block host's pulled tree at `tmp/stage1-olmo/retrieved/<host>/tree` (SEAL:3-4, 101-104).
  The brief lists `hosts/` but not `retrieved/`. The pilot's units (B1) will land there.
- **Fix.** Add `tmp/stage1-olmo/retrieved/` to the list for every helper.

### B6 (medium): name output folders so the path rule protects them

- A path rule protects a file only if its path holds "plant". Put RPR's output, K7's output and any dose or token
  report for plant arms in folders whose names hold "plant". Keep reader and wrapper code out of such names (for
  example, not `plant_pilot/`), so builders and verifiers may read the code.

### B7 (low): K2's leak test is too narrow

- K2's test checks only that the output file holds no unit, leaf or cell (READY:261). Extend it to stdout, stderr
  and every refusal message, with sentinel strings in a synthetic record.

### Steps of READY's plan that are safe

- RPR prints only file hashes on success and fixed messages on refusal (RPR:1-2, 433-436). Running it does not show
  the leaf.
- Plant rows are named `add-plant-NNN` (BP:12). So the J5 and J8 outputs over the plant pool do not name the leaf
  (I). The stage-1 reading reads arm units, reused units and judge files, not the plant record (RIB:8-11).
- I found no kit command that parses an edit's name. The kit names edits by SHA-256 (JR:235-237; PT:834-871) (M:
  grep of the kit code).

---

## 3. Costs, checked against measured figures

| Item | READY | Check | Sources |
|---|---|---|---|
| Arm job time | 0.57–0.82 h per arm (READY:279-281) | **0.57–0.87 h.** Five of six four-job pods ran 0.78–0.87 h per job; b-5 (0.57–0.63 h) is the low outlier. b-1 is the best match for a0_plant (an a0_arm plus 3 arms): job start 16:39:20, exit 21:08, so about 3.48 h for 4 jobs, 0.87 h each (I). | FOCUS:85-88, 90; unit counts FOCUS:76 |
| 3 a0_plant arms, measured basis | 2.06–2.81 pod-h, $3.69–5.03 (READY:297) | **2.6–3.0 pod-h, about $4.7–5.6.** 3 × 0.78–0.87 h + 0.30–0.39 h overhead, at $1.79 (rate) to $1.88 (block B's billed $/GPU-h). | RULES:45; FOCUS:76, 80, 81, 83 |
| Judges in the pilot | $1.2–1.7 measured; $3.58 upper (READY:298) | **$0. Not needed for the gate.** The gate uses U, the Qwen3Guard share, computed on the arm pod. The judge pods add HarmBench (800 answers per unit) and Granite (200). | PR4:185, 192-193, 675; RUN:635-647; RCFG:93-94; RULES:119, 124-125; FOCUS:76 |
| Scoring pass | 1.2–3.04 h, $2.1–5.4 (READY:299) | No measured figure exists for the attribution step alone. 3.04 h is Gate B's whole diagnostics job. K7's golden check also needs a GPU pass (I). | RULES:78-86 |
| Storage | about $1 a day (READY:304) | Right. It adds up to about $7 a week, the size of the pilot. Time matters. | PLAN31:14 |
| "Cap-based funding need × 1.25" ($21.34, $28.89) | READY:300-301 | The formula already includes the $6 reserve. | RULES:958-969 |

Totals (E):
- **Pilot, no judges, no scoring job:** about $5–6 measured; kit upper $7.43; worst case at the 5.75 h cap
  $10.29.
- **Pilot with the scoring job on its pod:** about $7–11 measured. Kit upper $12.88: the scoring job's spend upper
  is 3.04 h (RULES:86, 669-670), so 2,520 + 3 × 4,144 + 10,944 s = 7.19 h × $1.79. Cap 9.25 h, because the cap uses
  1.5 × 3.04 h (RULES:74, 715-716) (M, arithmetic).
- **Scoring later on its own pod (only after "go"):** overhead 0.30–0.39 h, plus a train-only regeneration (0.077 h
  measured for a0@1101: PR4:178), plus the scoring. About $2–7. If the pilot goes, this costs about $0.7–1 more than
  scoring on the pilot pod. If it stops, it saves about $2–5.
- **Main sweep (12 runs, 3 pods):** about $14–22 measured (3 × (4 × 0.57–0.87 h + 0.30–0.39 h) at $1.79–1.88),
  plus about $1.5–2.5 of judges for 15 units (P's 3 included). Kit upper $33.85 (READY:311). I reproduce it: three
  pods at 2,520 + 4 × 4,144 s = 5.30 h × $1.79 = $28.49, plus judge caps of 1.5 h + 1.5 h for 12 units (half-hour
  rounding) × $1.79 = $5.37 (RULES:883-885, 894-922) (M, arithmetic).
- **Judge caps for the pilot's 3 units**, if they were run: 1.0 h each (the 1 h floor), $3.58 (RULES:894-922);
  READY's figure is right (READY:298).
- **Money.** $29.94 at 22:13 UTC on 31 Oct (FOCUS:75), less about $1 a day of storage and about $1 for B14's pass
  (PLAN31:31). About $18–21 above the $6 reserve if the pilot launches within 2–5 days (E). The pilot fits either
  way. The main sweep does not. READY's conclusion stands (READY:320-322).

---

## 4. Does the pilot need anything from the stage-1 reading?

**Running the pilot needs nothing from the reading.** Its arms train on engine X with recipe S and their own edit
(RULES:340; JR:399-408).

**Reading the pilot needs nothing sealed either.** READY:387-388 says the pilot "cannot be read before the reading"
because Gate A's a0 per-prompt values are sealed in block A. That is wrong:
- The comparator is Gate A's a0 at 1101–1103 (PR4:675). Their U values were read before stage 1: the table
  header "Reused units (values already read)" (PR4:144-146); "a0's U (46.7, 46.8, 51.3%)" (PR4:896); PR4:898.
- Their unit folders are Gate A's own, under `tmp/family-probe-olmo2-1b*/retrieved/` (RULES:172-183). The seal
  covers block A's pulled trees only (SEAL:3-4, 101-104).
- Block A re-judged them with HarmBench and Granite (FOCUS:106: 27 units, 54 files). Those judge files are sealed
  (SEAL:13-14). The gate does not use them: it uses U (PR4:185, 229).

**The real dependencies:**
1. **The construction checks.** They must be published before the pilot (PR4:684; W1:293). Their inputs are J5's
   and J8's outputs from pod a-8 (FOCUS:112; KR:449-451), and L1 and DataShield-style read J5's output (S1R:73,
   76). Those files sit in block A's seal (SEAL:9-13, 61). So, without a ruling, the checks can run only after the
   reading.
   - Option: a recorded ruling that lets the checks read a-8's J5 and J8 outputs before the reading. a-8 ran only
     J5, J7 and J8 (FOCUS:112), so no U, HB, O, task-loss or coherence output is touched. LW-35 seals those five
     only (PR4:158). The kit's seal is broader: it seals every file that is not a ledger, completion record,
     fingerprint or receipt (SEAL:9-11, 61). This is a deviation from the seal record. The lead decides.
2. **The kit round.** It must not land in `runkit/stage1-olmo/` or `tmp/stage1-olmo/` before the reading. The reading
   loads `runkit/stage1-olmo/stage1_rules.py` by default (RIM:11, 28) and uses its REJUDGED_PINS and block tables
   (RIB:8-11). READY's K1 edits REJUDGED_PINS and the block lists (READY:260). Build the round in a scratch tree now.
   Merge it after the reading's outputs are sealed. If it must merge first, the second stamp must include the new
   rules file (PLAN31:34, 39-40), and 1d's suites must run on it (PLAN31:33).
3. **B16's hashes.** If the pilot reader imports B16, build and freeze it after 1a's B16 change (D-5) lands,
   because D-5 changes B16's module hashes (PLAN31:30). Or copy the two functions into the reader.

So READY's default order (reading, then construction checks, then pilot: READY:335-347, 363) is fine. But its stated
reason is wrong. The pilot can go first if the lead records ruling 1 and keeps 2 and 3.

---

## 5. The smallest correct kit change

READY puts K1–K6 into round 34: three blocks (P1, P1b, P2), per-seed draw keys, an edit-record tool for every plant
arm, judges per block; and K7 in a parallel round (READY:260-266, 336-338, 353). The pilot needs less.

### 5.1 Pilot-only round (one block "P", three runs)

1. **stage1_rules.py.** Add "P" to BLOCKS, FUNDING_BLOCK, HOST_PREFIX, BLOCK_KINDS (kind `arm` only) and
   REJUDGED_PINS (empty) (RULES:171, 615-625). Add `a0_plant` to ARM_DOSE with 38 steps (RULES:216-218; 38 steps
   for n ≤ 100: PR4:671). Add a separate run table for P (a0_plant at 1101, 1102, 1103). Leave `block_runs`' A, B
   and C paths byte-identical (RULES:294-315), because the reading uses them (RIB:8-11).
2. **plan_tool.py.** `init-block P` needs G3, as other blocks do (PT:810-818), and block B complete and sealed, as
   certify and B need block A (PT:819-823). P's deal uses the new table; training arms come only from a deal
   (PT:586-587). Nothing else is needed for edits. The sealed edit-record route already accepts
   `{arm: "a0_plant", path, sha256}` once ARM_DOSE names the arm (PT:3122-3130). `resolve_edit` keys a non-R arm by
   (arm, None) (PT:855-871). Seed 1101 passes the job check (PT:567-568).
3. **job_runner_stage1.py.** Write the readable fingerprint record (e1 and q) for a plant arm too. Today the runner
   writes it for `a0_arm` only, with arm hard-coded "a0" (JR:896-928, 1039-1044). Without it, a later train-only
   regeneration of a0_plant@1101 for K7 cannot be checked by fingerprint after P's seal, because COMPLETE.json is
   sealed (SEAL:11-13). The arm job already saves q and e1: calibrate trains from INIT to e1 and saves every
   checkpoint on the way (RUN:464-474, 1304-1331; q is the step-10 checkpoint: SPF:10).
4. **Judges.** None in block P. A block with no released judge launch is complete without judge files
   (PT:791-795). If the pilot goes, P2 re-judges P's 3 units through REJUDGED_PINS, the route block A used for Gate
   A's units (RULES:163-171).
5. **Tests and mutants.** One per new refusal (P before B is sealed; a P job other than a0_plant at 1101–1103; no
   sealed edit record; a changed edit file). A test that blocks A and B's tables and REJUDGED_PINS["A"] do not
   change. Then the kit suite and the mutation runner, baseline first with the same command (KR:321-322).

### 5.2 Outside the kit (Mac, $0)

6. **A binding check.** Confirm that REQ-8's record lists the planted_k37 file's SHA-256 (BP:290-294 writes
   {file, sha256} for each edit). Print "match" or "no match" only. Test it with a synthetic record that holds
   sentinel strings (B7).
7. **The pilot reader** (an S1 package; no "plant" in its code path). Per-prompt U for P's 3 units and for Gate A's
   3 a0 units (RULES:172-183). `contrast_paired` with c = a0_plant and m = a0 (CON:168-173). The one-sided 90%
   bound with t at the Satterthwaite df (PR4:675; TD:93). The label by the written ruling. The B1 test.
   Known-answer tests: t(0.90, 2) = 1.886; the edges at 5 and 10 pp; Λ ≥ 10 pp with a lower bound ≤ 5 pp. Freeze
   it by hash and stamp it before P launches.

### 5.3 Not needed for the pilot

- **Blocks P1b and P2 and the "go" gate.** Add them when the label calls for them. Each block starts on its own
  funding event anyway (PR4:878).
- **Per-seed draw keys for plant R600 and R150.** Only the main sweep needs them. Today only arm R is keyed by draw
  (PT:859), and the sealed record allows a draw only for R (PT:3127-3128).
- **K7.** It must be new code. Engine X's attribution step refuses any state that is not an a0 run-one ("is not an
  a0 run-one folder": RUN:870-872). It also refuses a state that is not on P's unedited stream (RUN:884-890,
  934-937). READY lists this as not verified (READY:266, 394); the code settles it. The kit's retrain kind also
  allows only a0 at 1102–1103 (PT:608-609; RULES:85), and `resolve_edit` resolves edits only for arm, regenerate,
  cert_c1 and c0 (PT:857). A plant retrain needs both widened. Build K7 now, in parallel, but keep it off the
  pilot's critical path.
- **An RPR change for k = 75.** RPR takes k from its W1-pinned settings (RPR:61-63, 303). Its text describes the
  k = 37 corpus (RPR:9-10). Its relocation replay uses k as the leaf size (RPR:218, 227). So a raise needs a new
  settings file and a new code pin, a post-W1 change, before any counted rank for a0_plant75. READY lists this as
  not verified (READY:267, 394). Plan the change only if the label is "raise".

---

## 6. Corrected plan

0. **Now, $0, before any stage-1b unit exists** (one addendum section):
   - Strike D7's fallback (B3). Rule: the construction checks are published as a stamped SHA-256 and opened only
     after the counted outputs are hashed, or after a final "stop".
   - The go-rule ruling: the literal text; the band [5, 10); the sign (1.2 point 5); the re-pilot at 1101–1103
     against Gate A's a0 (1.2 point 6).
   - Blinding rules B1, B2, B5 and B6. Record B4.
   - **The scoring pass (D3): reverse READY's default.** Default: after a "go", on its own small pod: a train-only
     regeneration of a0_plant@1101, accepted only on the fingerprint record's e1 and q, then K7. Fallback: K7 on
     the pilot pod, only if K7 has passed its golden check before P is planned and the live balance covers the
     9.25 h cap plus the $6 reserve. Reasons: K7 is new code (§5.3), it needs its own GPU golden check (§3), the
     money cannot fund the main sweep anyway (§3), and the pilot should not wait for K7. Note: PLAN-S packs "3 runs
     + one scoring pass" into the pilot (PLANS:179), but the frozen text fixes only "scored on a0_plant", not when
     (PR4:675, 684). So this is a planning choice, not a rule change. It is the lead's call; raise it to GPT if in
     doubt.
   - Judges (D4): none for P. P's units are re-judged with P2's units if the pilot goes.
   - Record that the disjoint-anchor fallback now applies. READY is right here: no set was sealed before S1
     (PR4:698, 883; ADD:407; LBL has no `anchors.disjoint` key, M).
1. **Now, $0, in a scratch tree:** the pilot-only kit round (§5.1 items 1–5), the binding check and the pilot reader
   (§5.2). K7 in parallel, with a golden check on a row subset on a GPU.
2. **The stage-1 reading** (PLAN31 step 1). Unchanged.
3. **After the reading, $0:** DataShield-style and L1 outputs on the Mac if they do not exist yet (READY:226-228);
   RPR without `--counted`, written to a "plant" path; commit its SHA-256 and stamp it. Merge round 34 into
   `runkit/` and `tmp/`; run the kit suite and the mutants again.
   - If the reading slips by days: record ruling §4 item 1, run the construction checks from a-8's outputs now, keep
     round 34 away from the reading's rules file (§4 item 2), and launch P before the reading.
4. **Pilot P (about $5–6; upper $7.43):** pack, check-plan, one pod, three a0_plant arms, a live finisher in the
   lead's session (FOCUS:87), record-done, seal P, then the frozen reader. Record the label. Stop and ask
   (PR4:887).
5. **"Go":** the scoring pod (about $2–7); hash K7's output; then RPR with `--counted`; then open the plant-rank
   output. The main sweep P2 waits for a top-up; P's units are re-judged there.
6. **"Raise":** a second pilot with a0_plant75 at 1101–1103 (about $5–6) and the same reader, once. The RPR k = 75
   change comes before any counted rank.
7. **"Stop":** report the null and open the construction checks.

---

## 7. Smaller points

- READY:243-249 says Gate A's a0 units "stay sealed until the stage-1 reading". Only their HarmBench and Granite
  re-judge files are sealed (§4).
- D8 (keep O-ext on plant arms, READY:360) is fine. Dropping it would save about 0.28 h per arm at the upper
  (RULES:62), about $1.5 on the pilot, but it needs a new kind. Not worth it now (I).
- K2's "steps" output (READY:261) is not needed. The kit takes steps from ARM_DOSE (PT:543-546), and the sealed
  record holds only arm, path, SHA-256 and a draw for R (PT:3127-3128).
- READY's step 5 also asks for judges and a seal before the reader (READY:341-343). Without judges, the seal can
  follow record-done directly (PT:791-795).

## 8. Not verified

- The value of RPR's Self-Inf-N switch (its settings file was not opened: path rule).
- Whether the a0_plant units' `eval/` files also carry the edit name. I traced only the COMPLETE.json route (B1).
- Whether stage 1's regenerations were accepted on equal fingerprints. A regenerate job can be "complete" and still
  fail acceptance (JR:1027-1035). The deferred K7 route assumes the a0_plant@1101 retrain reproduces its
  fingerprints, as PR4:178's rule assumes for a0.
- Per-job durations from the sealed host trees (not opened). The times above are inferences from FOCUS times.
- The 9,418 s start requirement (from plan.json, not opened).

## Commands run (all read-only)

- `Read` of the files above; `wc -l`; `awk`/`sed` line ranges; `grep` on named files; `cmp` of the four kit files
  against their `tmp/` copies (all equal); `ls` of `scripts/stage1_s1/` and the filtered top level of
  `tmp/stage1-olmo/`; `python3` reading MAN1 and LBL keys; `date -u`. All exited 0, except one `grep` whose regex
  the tool refused (no output; repeated with Python on FOCUS).

## Changed files

- This report only.
