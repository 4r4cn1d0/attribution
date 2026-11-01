# Stage-1 reading preparation: completeness critique (task 2)

- **Written** 2026-11-01 by an Opus worker for the lead (GI VIII). Clock checked with `date -u` at 04:25:45,
  04:44:11 and 04:46:11 UTC (the last right before writing). The user's "Yes, time-stamp it" is the answer to the
  question "Shall I time-stamp the rules with OpenTimestamps instead of OSF?" (OTS:3-7; FOCUS:74). I read it that
  way, not as a request about this report. I give clock times anyway, as the project's records do.
- **Read-only.** Main checkout `/Users/spiderishi/Coding/attribution`, branch
  `stageb-costs-and-recovery-safeguards-20261003`. HEAD is `0daca9a` (committed 2026-10-31T23:19:10Z), one commit
  after the briefed `95f7a79`; it adds the keep-working record and a grant dossier only (V1A:9-11). The tree
  `scripts/stage1_s1` is `0bab8d75…` at HEAD (M: `git rev-parse`), the tree the first stamp binds (OTS:15). The only
  file I wrote is this report.
- **Data rules kept.** I opened nothing under `tmp/`. I opened nothing in `block-a/` or `block-b/`, no `units/` or
  `eval/` folder, no COMPLETE.json, no answer, label, guard-sample or judge-cache file, no hidden or selector bank,
  and no W1 "sealed record". I listed only the names in `.ai/inputs/stage1-post-w1-20261023/reading/` and its
  `timestamp/` folder. There I read the two user records, STAMP:1-40 and OTS:1-20. I ran no test, spec, reading,
  builder, overlap, HarmBench-claim, judge, seal or kit command, and imported no repository module.
- **Inputs (SHA-256, first 16; M).** PLAN `121c5119d12e5bae` (= FOCUS:74); D1A `d4700f08395138e6`; V1A
  `f5cb0298a1e1eb33`; R1B `c03f67467964cf33`; R1D `9ae23f5ee6fa9ae6`.

Labels: **R** read in a source; **M** computed or checked here; **E** an estimate; **I** inference.

## Short names (every citation is path:line)

| Name | Path |
|---|---|
| PLAN | `.ai/inputs/stage1-post-w1-20261023/reading/next-steps-after-block-b-20261031.md` |
| KW | `.ai/inputs/stage1-post-w1-20261023/reading/user_instruction_keep_working_20261031.json` |
| OTS, STAMP | `.ai/inputs/stage1-post-w1-20261023/reading/timestamp/ots-manifest-20261031.json`, `…/stamp-record-20261031.json` |
| FOCUS | `research/FOCUS.md` (newest entries from line 74) |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` |
| REV4 | `research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md` (frozen) |
| W1R | `research/experiments/2026-10-16-stage1-commitments.md` (the committed W1 record) |
| LEDGER | `research/experiments/2026-10-17-stage1-preregistration-rev3/decision-ledger.md` |
| AMD | `research/experiments/2026-10-17-stage1-analysis-model/stage1-analysis-model-DRAFT.md` |
| PREREG | `research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md` (Gate B/C rev 5, frozen) |
| SPF | `docs/study-plan-full.md` |
| HLC | `research/review/2026-10-17-stage2-design-notes/second-rater-and-human-label-check.md` |
| B16/ | `scripts/stage1_s1/reading/` |
| RI/ | `scripts/stage1_s1/reading_input/` (the builder, `hb.py`, `hb_claim.py`) |
| STR, STRS | `scripts/stage1_s1/overlap_strata.py`, `scripts/stage1_s1/settings/overlap_strata.json` |
| SIM | `scripts/stage1_s1/overlap_similarity.py` |
| LC | `scripts/stage1/limits/limits_common.py` (a W1 file) |
| KIT, PT | `runkit/stage1-olmo/stage1_rules.py`, `runkit/stage1-olmo/plan_tool.py` (repo copies) |
| OEX | `scripts/stage1_s1/oext_eval.py` |
| RIB, HBB, B16H | `research/experiments/2026-10-27-block-b-prep/reading-input/reading-input-build.json`, `…/hb-reader/hb-reader-build.json`, `…/b16-halves/b16-halves.json` |
| D1A, V1A, R1B, R1D | the reports under review, in this scratchpad folder: `1a-ri-o2-design.md`, `1a-ri-o2-review.md`, `1b-b14-similarity.md`, `1d-reading-runbook-draft.md` |

---

## 0. The answer in brief

1. **The reports cover the large items well.** RI-O2 (D1A, V1A), the missing B14 similarity pass (R1B) and the
   runbook (R1D). Their two new defects are real; I checked the code. B14's `report` refuses every recipe-S unit:
   STRS:39-42 fixes `recipe_sha256` to REC's `9e9bde6f…` and STRS:49 refuses recipe S `ceffe0ef…`; LC:165-169
   enforces both; PT:524-527 trains every arm and a0 run with recipe S; `scripts/stage1_s1/tests/test_b14_report.py:385-400`
   asserts the refusal. And no code writes B14's inputs file (STR:15-19; M: only `overlap_strata.py` names the kind
   "stage1 overlap report inputs" in `scripts/`, `runkit/` and `experiments/`).
2. **On RI-O2 the review is right.** The design's prompt part is wrong for its own pooled estimate. I re-derived the
   review's 4-prompt case by hand (§4, W1): the design gives an SE of about 0.07 pp where the ratio estimator's SE is
   25 pp. Adopt the review's linearized table (V1A §2.3, §6).
3. **Not covered by any report** (§2):
   - plan row 1c (addendum §39) was never drafted, and its scope is wider than PLAN:32 says;
   - four pre-registered reading outputs have no producer: F_k's planning power at the measured discordance
     (REV4:574), the stage-3 confirmation pick (REV4:428), LN-14's transfer bar (REV4:554) and LN-19's flag-change
     shares (REV4:555);
   - no S1 blinding record exists for the inference rules written after the W1 commit (REV4:919; W1R:358);
   - ADD:428's re-run of B16's size, coverage and familywise-error simulations has no record;
   - pre-registered predictions and a few report items are missing from R1D's list (REV4:276, :451, :492, :494, :503, :656-662).
4. **PLAN has six stale or wrong points** (§3): its Mac fallback for 1b cannot run; step 1 refuses as pinned; step 2
   lacks `--hb-out`; step 5 has no script; step 6 says "stop" where KW says "go on"; row 1c omits RI-O12 to RI-O14.
5. **The path to the reading** (§5): rulings, then parallel $0 builds, the one B14 pod (about $0.6–1.2, E), the
   sealed strata, the merge with suites and specs on the final tree, the records, the second stamp and its anchor,
   then the reading. About 1.5–3 days (E) if no build needs a second fix round.

---

## 1. Obligations from "block B sealed" to the end of the reading, ticked against the reports

### 1.1 Before the reading

| # | Obligation | Source | Covered by | State |
|---|---|---|---|---|
| P1 | Make the strata; put their SHA-256 in FOCUS before any add-arm outcome is read | ADD:375; REV4:757 | R1B §3, §7; R1D RB6 | open; needs one pod (§5 step 7) |
| P2 | B14's `report` must accept the stage-1 kit units | STRS:39-49; LC:165-169; PT:524-527 | R1B §5; R1D RB1 | open; the fix must land **before** `strata` runs, because the strata record stores the strata settings' hash and the report refuses a mismatch (R1B:101-103) |
| P3 | Write B14's inputs file (paths and hashes of a0 and add-arm units) | STR:15-19 | R1D RB2, step 0.4 | open; writer drafted, never run |
| P4 | S-G: coherent-only U for every arm; every label re-read on coherent answers | REV4:270, :301, :398 | D1A; V1A | open; adopt V1A's estimator (§4 W1) |
| P5 | The G3 "unscored" corner as Gate B's adverse corner | REV4:185; PREREG:149; AMD:60 | D1A §8 A; V1A §5.1 | open; built corner is symmetric (RI/items.py:115) |
| P6 | Every builder open point ruled before outcomes | PLAN:32; RIB:412-467 | none | open; PLAN lists RI-O1, RI-O5 to RI-O11 but RIB also has RI-O12 to RI-O14 (RIB:456-467) |
| P7 | HarmBench claim reader: every stated reading ruled | ADD:641-646; RI/hb_claim.py:71-94 | none | ADD §37 ruled R1, R4, R8 only; R2, R3, R5, R6, R7, R9 are unruled |
| P8 | Step 2 writes the HarmBench tables that step 4 needs | RI/hb_claim.py:4; RI/__main__.py:47; PLAN:42 | R1D RB3 | open; runbook fix |
| P9 | The runbook, rehearsed | PLAN:33 | R1D | draft; rehearsal (R1D step 0.5) not run |
| P10 | Suites and mutation specs re-run on the final tree | PLAN:33; ADD:507 | R1D §3 | open |
| P11 | First stamp anchored and verified; the reading starts after its block time | PLAN:34, :39; STAMP:10-13 | R1D step 0.3 | open; the client venv was not kept (STAMP:38) |
| P12 | Second stamp of the final code and runbook, anchored before step 1 | PLAN:39-40 | R1D step 0.6 | open |
| P13 | Every inference rule written after the W1 commit listed in an S1 blinding record; the paper labels it "fixed after Gate B wave 1" | REV4:919; W1R:358 | V1A §1.3 (for D-5 only) | open; no such record exists (M: search in §8) |
| P14 | B16's size, coverage and familywise-error simulations run once more on the final code | ADD:428 | none | UNVERIFIED; I found no record (§2.6) |
| P15 | LN-31 draw: protocol, script, seed tags and inputs committed before the script reads any guard file | REV4:762-763; HLC:164, :168 | R1D RB4, D3 | open; LW-30's "full protocol before block A" (REV4:762) and HLC:168's deadline have passed: a deviation to record |
| P16 | LN-15e | REV4:749-753; ADD:550-557; FOCUS:104 | PLAN:35 | done (fallback report) |
| P17 | What happens after the reading: "stop and ask after every stage" (frozen) or "report and go on" (31 Oct) | REV4:887; KW:7, :13; PLAN:48-49 | R1D RB11 | needs one recorded line (§3 C7) |

### 1.2 In the reading

| # | Output | Source | Covered by | State |
|---|---|---|---|---|
| Q1 | P1–P6 rows, Φ, headline words, references, family 1b, best feasible repair, actor menus, S-start, §9.4 | REV4 §3–§5, §9.4 | R1D §6 | built (B16) |
| Q2 | F_k's planning power at the measured discordance q, printed beside each F_k result | REV4:574; REV4:1257, :1268 | none | **no producer** (B16 has only an MDE helper, B16/contrast.py:73-75; M: no "discordance" or power output in B16/) |
| Q3 | The stage-3 pick: the two contrasts with the largest primary-U \|t\| among those whose U part reads better or worse (U) | REV4:428; SPF:374 | none | **no producer** (M: no pick or confirm code in B16/) |
| Q4 | LN-14's θ0 transfer report (Branch 128 applies, FOCUS:124) | REV4:554 | none | sealed output exists (OEX:760-790; KIT:505-507 kind `transfer_report`); **no reader** |
| Q5 | LN-19's flag-change share per source | REV4:555 | none | inside each O-ext summary (OEX:34, :688-708); **no reader** (M: no `flag_change` or `transfer` in RI/) |
| Q6 | "The record prints" P4's expected S-a shift (−0.28 pp) | REV4:276 | none | a line for the record template |
| Q7 | Predictions: Safe LoRA PR1–PR5; B+Qi Q-P1–Q-P4; the published scorer priors | REV4:494, :503, :656-662 | none | no producer named |
| Q8 | Each reference's HB with its 90% interval | REV4:451 | none (R1D lists HB-2 only) | not built (ADD:646) |
| Q9 | Safe LoRA's V/V′ check; "V′ not run" if the set changed | REV4:492; ADD:620 (G9) | none | not read by any step |
| Q10 | Measured cost per arm under both conventions (headline item 1; actor menus) | REV4:103, :774 | R1D §6 | not built; it can be built **before** the reading (§2.7) |
| Q11 | Token accounting per arm (doses) | REV4:135, :740 | none | `scripts/stage1/report_token_accounting.py` exists; whether it ran on the final edit files is UNVERIFIED; outcome-free |
| Q12 | HB-2; U_hard, refusal share, Granite greedy; O by source with the dev-100 O beside; prompt flips; opening switch; length bands; selectivity; HarmBench cut share; side-effect prediction | REV4:193-202, :537, :758-761 | R1D §6 | not built |
| Q13 | S-tok | REV4:271; PLAN:32 | R1D §6 | B16 prints `null`, not "not run" (B16/reading.py:312): the record must word it |
| Q14 | §9.4 if the strata never arrive | REV4:757 | R1B §7; R1D RB6 | B16 prints "not computed" (B16/reading.py:534-535); needs its own deviation record (§3 C3) |
| Q15 | LN-31's draw (totals only) | REV4:763 | R1D | P15 |

---

## 2. What no report covers

### 2.1 Addendum §39 (plan row 1c) was never drafted, and its scope is wider than PLAN:32

No report was assigned to 1c. PLAN:32 lists RI-O1 and RI-O5 to RI-O11 and RI-O3's wording. These stated readings
also need a ruling before the reading, or they are post-hoc choices:

1. **RI-O12, RI-O13, RI-O14** (RIB:456-467): a seal must carry `judge_record`; the rules module defaults to the repo
   copy (R1D pins both copies equal, so this is cheap); the not-run route for R's O cell at a reused seed.
2. **`hb_claim.py`'s readings R2, R3, R5, R6, R7, R9** (RI/hb_claim.py:75-94; HBB:190 "R1-R9 above"). ADD §37 ruled
   R1, R4 and R8 only (ADD:641-643). R2 (the case comes from the U part, not the headline word), R3 ("worse (U)"
   plus an equivalence grade reads as equivalent), R5 (point estimates; B16's tie tolerance), R6 (the HB interval is
   U's model refitted), R7 ("unparsed" counts as not "yes") and R9 (P1–P6 only) each change which sentence prints.
3. **B16's own stated readings**: B16/README.md:153-159 ("readings the record should state": the 1e-9 pp tie
   tolerance, LN-12's "not tested" below 3 R seeds, the S-a equal-variance flag, plan B's pooling, the two-arm floor)
   and the overlap readings R2–R6 (B16/README.md:79-84). ADD §33 ruled C1 and the smaller items only (ADD:604-607).
4. **The coherence condition in the best feasible repair** (B16/reading.py:449, M). REV4:302 makes a failing arm
   "infeasible for the selector"; REV4:410's best-feasible rule has no coherence condition. V1A decision 9 is right
   that it needs a stated reading.
5. **S-tok's wording** (B16 prints `null`: B16/reading.py:312) and **§9.4's wording** if `--no-overlap` fires
   (do not cite ADD §24 point 4; §3 C3).
6. **"Stop and ask" against "report and go on"** (§3 C7).
7. **R1D's own readings** (R1D:804-805): the recipe rule, the inputs writer, the pre-runs, the byte-for-byte re-runs,
   the stop rules, the mechanical record.
8. **B16 open points** B16-D4-O2 (HB's 255 starts) and B16-D4-O3 (D-4's fallback print is not built) from
   B16H `open_points_v2` (M: printed by key). Neither blocks; both should be stated once.

### 2.2 F_k's planning power at the measured discordance (REV4:574)

REV4:574 says: "the stage-1 reading prints F_k's planning power at the measured q beside each F_k result (report
only; after block B…)". The review fixes record the same move (REV4:1257, :1268). B16 has no such output (M). It is
a pure function of the O tables (the share of prompts where an arm's refusal flag and θ0's differ) and the planning
formula of REV4:565-574 (normal approximation, P = 500, J = 6; the source is review-statistics §6.1). Default: a small pinned reader, built and tested
before the second stamp. Fallback: print the measured q per arm only and record that the power line was not computed
(a deviation). Trigger: not verified when the other builds are done.

### 2.3 The stage-3 confirmation pick (REV4:428)

The rule is mechanical: "the two primary contrasts with the largest |t| of the primary U test, among contrasts whose
U part reads better or worse (U); ties to the lower P index; none if no contrast has either U word". SPF:374 lists it
as a feed of the reading. B16 does not compute it (M). REV4:400 forbids hand-made words; a pick made by hand from
reading.json is close to that line. Default: a 20–40-line pinned script that reads `reading.json` by key and prints
the pick, run as a reading step. Fallback: the record extractor computes it with the rule text pinned in §39.

### 2.4 LN-14's transfer bar and LN-19's flag-change shares (REV4:554-555)

W1-18 chose Branch 128 (FOCUS:124), so both reports apply. Their numbers sit in sealed O-ext summaries: the transfer
report's `bar` and `flag_change` (OEX:775-782) and each unit's per-source `flag_change` (OEX:688-708). The builder
reads neither (M). If θ0 fails LN-14's bar, "the paper states the cut as a limit for PHTest" (REV4:554). Default: a
seal-safe extractor run inside the reading script, after step 1 opens the outcomes. Fallback: the record states that
they were not read, as a deviation.

### 2.5 The S1 blinding record (REV4:919)

REV4:919: "Any inference rule still written after the W1 commit is listed in an S1 blinding record with every Gate B
value read before it was written, and the paper labels it 'fixed after Gate B wave 1'." W1R:358 repeats it. V1A
raises it for D-5 only (V1A:116-134). I found no such record (M: search in §8), and no FOCUS entry that names the S1
freeze. The W1 commit was 2026-10-22T21:22 UTC (FOCUS:143). Rules written after it include at least: ADD §33 point 1
(which contrasts §9.4 covers) and point 2 (D-4), both 27 Oct; ADD §37's R1, R4, R8 (29 Oct); ADD §24 point 2 (LN-14's
bar at n = 400); and, to come, D-5, the B14 recipe fix and §39. The Gate B values read before them: wave 1
(FOCUS:139, 23 Oct 01:00 UTC), the verdict TOO CLOSE with its numbers (FOCUS:137, 04:31 UTC) and the final
measurements (FOCUS:134, 05:26 UTC). Default: one record in `reading/`, inside the second stamp. Fallback: the
reading record's limits section lists the same rules with the label. Trigger: not written when the records step
(§5 step 9) starts.

### 2.6 ADD:428: the B16 simulations "at the S1 freeze"

ADD:428: "The size, coverage and familywise-error simulations are not re-run on the final code; they run once more,
at the S1 freeze." I found no record of that run (M: searched FOCUS and the 2026-10-23, 2026-10-24 and 2026-10-27
record folders for "familywise", "coverage" and "simulat"; only the halves simulation and kit records matched). B16
changed after the S1 period: the halves and D-4 (FOCUS:103), two fixes (FOCUS:98), and D-5 may follow. The D-4
verifier re-run (B16H `verifier_rerun`: 264 whole readings, no label change) is a regression check, not a size or
familywise check. Default: re-run the 23 Oct statistics verifier's size, coverage and Φ familywise simulations on the
final tree (CPU, $0) before the second stamp, or point to the record if it exists. Fallback: state that the last such
run used the 23 Oct code. Trigger: the scripts cannot be found, or the run will not finish before the second stamp.

### 2.7 Items R1D defers that can be done before the reading

- **Cost per arm** (Q10). Cost ledgers are readable after a block (REV4:158), so the C-full and C-lean tables
  (REV4:631-638; REV4:793-799) need no outcome. Building and running them now removes one piece of code written after the
  outcomes and fills headline item (1) (REV4:103). Check first that the ledger files are among each seal's readable
  files (A: 174 readable, FOCUS:106; B: 289, FOCUS:76).
- **Token accounting** (Q11) and **the published priors** (REV4:656-662) are outcome-free by their own text.
- **The LN-31 draw script** (P15), as R1D D3 says.

### 2.8 Missing from R1D's list of report items

Q6 (REV4:276), Q7 (REV4:494, :503, :656-662), Q8 (REV4:451; ADD:646), Q9 (REV4:492; ADD:620). None blocks the
reading. Each needs either a pinned producer or a "code written after the reading" label.

### 2.9 Two cheap safeguards

1. **Keep the `ots` venv** until both stamps are upgraded and verified. The first venv was deleted (STAMP:38), so
   step 0.3 now needs a reinstall, which last time needed the user's yes (STAMP:38: "installed on the user's yes").
2. **Optional third stamp** of the reading outputs right after step 5. It bounds from above when the results
   existed. Cost $0.

### 2.10 R1D's pinned expected lines can cost a stamp cycle

R1D's script stops if any `EXPECT` line differs (R1D:469-478). Those lines are inferences (R1D:670-677), for example
"judges B: … 71 units" (the builder prints the reading's units: RI/build.py:540, :581). A wrong line costs a new
second stamp and a new anchor wait (R1D:675-676). Default: stop only on identity lines (plan code, seals, rules and
settings pins, written hashes) and log the count lines for review. Fallback: R1D as drafted. Trigger: the lead
prefers strict checks.

---

## 3. Contradictions

| # | Between | What | Who is right (evidence) |
|---|---|---|---|
| C1 | D1A §4.2 vs V1A §2 | D1A's prompt part (matched prompts, equal weights, P_k) against V1A's linearized table x = V + (u − V·n)/N̄ | **V1A.** The pooled estimate weights prompts by n; D1A's prompt part cannot see that mix (§4 W1, re-derived by hand). D1A's "conservative" (D1A:304-305) and "second-order" (D1A:455-458) claims fail in that case |
| C2 | PLAN:31 vs R1B §6 (iii) | PLAN's fallback (i): "the same script on the Mac CPU" | **R1B.** SIM:421-426 always calls `real_loaders()`; `_prepare_cuda` refuses a non-CUDA recipe (`experiments/safety_selection/loaders.py:121-129`); `configure_cuda` refuses without CUDA (`experiments/minimal_safety/model.py:377-385`). The fallback needs new code |
| C3 | PLAN:31, B16/README.md:68 vs ADD:508, FOCUS:103 | PLAN and the README call B16's "not computed" "§24 point 4's fallback" | **ADD and FOCUS.** ADD:508's fallback is "B14's per-contrast paired form", and FOCUS:103 withdrew it. "Not computed" is B16's absent-block output (B16/reading.py:534-535). If it fires, it is a deviation from REV4:757 and needs its own record |
| C4 | PLAN:41 vs code | Step 1 as pinned | **R1B/R1D.** It refuses at the first kit unit (P2) |
| C5 | PLAN:42 vs RI/hb_claim.py:4 | Step 2 has no `--hb-out`; step 4 needs it | **R1D RB3.** RI/__main__.py:47 makes it optional; without it the builder prints "HarmBench tables: not built" (RI/__main__.py:88) |
| C6 | PLAN:46 vs repository | Step 5 "LN-31's draw" | **R1D RB4.** No script exists (R1D's search; HLC:164 needs it committed first) |
| C7 | PLAN:48-49 vs KW:7, :13 vs REV4:887 | After the reading: "stops and reports" (PLAN); "report after each stage and go on" (KW); "stop and ask after every stage" (frozen REV4:887) | KW is later and replaces PLAN for this run (KW:13). It does not cite REV4:887. FR-21 is the user's own "stop asking me for approval" (LEDGER:70), so the change is the user's to make; record it in §39 with REV4:887 named |
| C8 | D1A:3-4 vs OTS:3-7, FOCUS:74 | D1A treats "Yes, time-stamp it" as a request to time-stamp its report | **V1A:5-7.** It was the OTS answer |
| C9 | R1D:44 vs KW:3 | R1D quotes "reports after every stage and goes on" as the user's instruction | Those are the lead's words (KW:7, :13); the user's words are "keep working until all resources are exhausted" (KW:3) |
| C10 | R1B:167 vs V1A:366 vs R1D:780-781 | The B14 fix: "D-6" (R1B); "the next number" (V1A); "a change of S1 code … the lead labels it" (R1D) | Number deviations once, in ruling order |
| C11 | PLAN:32 vs RIB:456-467 | 1c's list | RIB has RI-O12 to RI-O14 too |
| C12 | D1A:481 vs R1D:170-171 | B16 spec time: about 2.7 h (an estimate, B16H) against about 2.1 h (measured from the 29 Oct shards) | Not a factual conflict; plan with the measured 2.1 h |
| C13 | D1A §7 vs V1A §4 | Route: inside B16 against beside B16 | The lead's call. Beside B16 keeps B16's module hashes, so the S-G coherent words must be copied into the record's sensitivity part by key (REV4:398) |

---

## 4. Claims checked

### 4.1 Wrong or unsupported

- **W1 (D1A:257-264, :304-305, :455-458).** The design's prompt part. Hand case (V1A:165-177): 4 prompts, 2 seeds;
  prompt 1 all Unsafe in both arms; the repair's three answers on prompt 1 fail the screen. Comparator V = 3/12 =
  25%; repair V = 0/9 = 0%. Design: prompt 1 dropped; prompts 2–4 give D = 0, so the prompt part is 0 and the seed
  part sits at the floor (SE ≈ 0.07 pp). Linearized (M, by hand): N̄(c) = 3, x(c) = (1, 0, 0, 0); x(m) = (0, 0, 0, 0);
  MS_P = 2 × 0.75 / 3 = 0.5; V_item = 0.5 × 100² / (4 × 2) = 625 pp², SE 25 pp. This matches V1A's table. **Wrong.**
- **W2 (D1A:219).** "Each check also kills a misaligned or swapped vector." Swap (n = 2, u = 1) with (n = 3, u = 1),
  both with plain count 1: u ≤ U3 holds (1 ≤ 1); U3 − u = 0 ≤ 3 − n holds for both; Σ(3 − n) is unchanged (M).
  **Wrong**, as V1A:240-242 says.
- **W3 (R1D:469-478, :670-677).** The expected builder lines are inferences, not measurements. Plausible from the
  code (RI/build.py:540, :581), but **unsupported** until rehearsed (§2.10).
- **W4 (R1D steps 0.2 and 0.4).** They assume `plan.json` keys (`seals`, `hosts`, `jobs`, `status`, `pulled`, `unit`,
  `complete_sha256`) that R1D did not open (R1D:11). **Unverified**; the synthetic rehearsal must cover them.
- **W5 (R1D RB1's "first a $0 look" at plan.json's recipe field).** Already done: R1B:150 reports recipe "S" on all
  55 arm jobs and all 5 a0_arm jobs. Not wrong; redundant.
- **W6 (R1D RB11).** Misattributed words (C9).

### 4.2 Spot-checks that hold (M: opened at the cited line)

| Claim | Report | Check |
|---|---|---|
| "Coherent-only U is reported for every arm; every label is re-read on coherent answers" | D1A:108 | REV4:301 holds |
| G2's pooled share; drop "left out of that pair's differences" | D1A:83-89 | PREREG:148 holds |
| G3a corners per direction, a0 plain | D1A:93-95; V1A:326-331 | PREREG:149; `scripts/gate_b_reading.py:239-245` hold |
| `G2_DROPPED_PROMPT_LIMIT = None` | D1A:149 | `scripts/gate_b_reading.py:196` holds |
| Gate B drops a prompt from the pair SE only | D1A:147 | `scripts/gate_b_reading.py:457-470` holds |
| B16's S-G runs `variant_estimates` through `record()` | D1A:173-175 | B16/reading.py:287-313 holds |
| §9.4 absent → "not computed" | D1A:197 | B16/reading.py:534-535 holds |
| A RemlError refuses the whole reading | D1A:178 | B16/reading.py:556-561 holds |
| Builder sends only the two G3 tables; `NOT_BUILT` names the coherent table | D1A:188-191 | RI/build.py:84-87, :671-674 hold |
| Unscored counted Unsafe in every arm | D1A:547-549 | RI/items.py:115 holds |
| B16 spec 117 entries, 11 on `sensitivities.py`, none on S-G | D1A:180; V1A:323 | M: parsed `mutants_b16.json`; holds |
| Best feasible repair requires coherence | V1A:308-311 | B16/reading.py:449 holds |
| REV4:919's rule and label | V1A:115-118 | REV4:919; W1R:358 hold |
| No S1 blinding record exists | V1A:133-134 | M: my search agrees (§8) |
| Start level 0.75%; pair SD 1.84 | V1A:174-182 | REV4:340, :254 hold |
| Recipe S hash `ceffe0ef…`; REC `9e9bde6f…` | R1B:145; R1D:34 | `scripts/stage1_s1/settings/oext_unit.json:58-61`; STRS:40 hold |
| Every arm and a0 run uses recipe S | R1B:148-150; R1D:34 | PT:524-527; KIT:340 (`TRAINING_IDENTITY_RECIPES = ("S",)`) hold |
| The engine writes `recipe_sha256` = the config hash | R1B:151; R1D:34 | `experiments/safety_selection/planning.py:75`; `runner.py:1313` hold |
| B14's test asserts the recipe-S refusal | R1B:154; R1D:34 | `scripts/stage1_s1/tests/test_b14_report.py:385-400` holds |
| 20 job kinds, none runs SIM | R1B:48 | KIT:505-507 holds |
| SIM always uses the CUDA loaders | R1B:210-215 | SIM:421-426; loaders.py:121-129; model.py:377-385 hold |
| The CUDA path is untested | R1B:374-375 | SIM:43-44; `test_b14_n8_read.py:1-9` hold |
| Strata SHA-256 in FOCUS before any add-arm outcome | R1B:64 | ADD:375 holds |
| W1-18 pod: 23 min, $0.69 | R1B:187-188 | FOCUS:124 holds |
| HLC: commit before reading guard files; deadline before block A's first pod | R1D:37 | HLC:164, :168 hold |
| First stamp pending; client venv not kept | R1D:43 | STAMP:36, :38 hold |
| B16 261 passed; engine X 1,108 passed, 5 skipped; kit 671 | R1D:140-146 | FOCUS:98, :103, :78 hold |
| Seals A `6c6267c8…` 1,703 files; B `b4e11dc9…` 3,830 files | R1D:56-57 | FOCUS:106, :76 hold |
| Plan A recorded (σ̂ 1.78 pp) | R1D:67 | SPF:298; FOCUS:125 hold |
| The builder lacks `--hb-out` by default; claim reader needs `--hb` | R1D:36 | RI/__main__.py:47, :88; RI/hb_claim.py:4 hold |
| `B16-legal-note-text` is the expected survivor | R1D:169 | `mutants_b16.json:424` holds |
| V1A's evidence files | V1A:399-401 | M: all six SHA-256 prefixes match |

An earlier suite baseline in this scratchpad (`reading-prep/suites/`, at 95f7a79): builder 195 passed, B16 261
passed with 51 RuntimeWarnings from ordinary matmuls (for example `reml.py:218`, `reml.py:321`,
`tests/test_reml.py:213`). They come from tests that then pass exact checks; they look like floating-point flags
from the Mac's BLAS, not real NaNs (I). No action beyond pinning numpy's version, which R1D does.

---

## 5. Ordered steps from now to the reading

Owners: **L** = the lead (with workers it dispatches), **U** = the user, **P** = a pod. Money: the balance was
$29.94 at 22:13 UTC on 31 Oct, with about $0.04/h of idle storage (PLAN:14); the reserve is $6 (KW:8). Times are E.

| Step | What | Depends on | Owner | Cost |
|---|---|---|---|---|
| 1 | **Rulings** in one sitting (§6): D-5's estimator and route; the G3a corner; the B14 recipe fix and its form; the 1b route; the inputs writer; LN-31; which reading-time readers are built first; the S1 blinding record; ADD:428's simulations; §39's list (§2.1) | nothing | L | $0 |
| 2 | **First stamp anchor**: reinstall the `ots` client from the nine recorded wheels (`--require-hashes`) and keep the venv; `ots upgrade`; check the block against two explorers; record height and time in FOCUS (R1D step 0.3) | nothing (can start now) | L; U's yes if the reinstall counts as a new install | $0 |
| 3 | **$0 Mac pre-check** for B14 (R1B step A: tokenizer and codec only; counts printed) | step 1 (route) | L | $0 |
| 4 | **Builds in scratch trees, in parallel**: (a) S-G coherent reader by V1A's linearized table, with the builder's per-prompt counts (n, u, u_fail), tests, mutants, independent check with a coverage simulation; (b) the adverse G3a corners in the same reader; (c) the B14 recipe fix (settings re-pin, tests, the B14 suite and its 87-mutant spec or the near set); (d) the B14 inputs writer (R1D step 0.4) with a synthetic test and a second-process check; (e) the small readers of §2.2–§2.4 (and §2.7's cost table if ruled); (f) the LN-31 script and protocol, if ruled; (g) the final reading script and runbook | step 1 | L (workers) | $0; about 1 worker-day |
| 5 | **Kit round 34** (one similarity job kind; kit suite and its mutants) or the one-off-pod checklist (R1B §6) | steps 1, 3 | L | $0 |
| 6 | **Rehearsal** on synthetic data (R1D step 0.5) of the whole script, with one planted difference per checker | step 4 | L | $0 |
| 7 | **B14 similarity pod**: one A100, `overlap_similarity.py` on θ0; pull `similarity.json`; its SHA-256 into FOCUS | step 5 | L launches from a background job; P runs; U's in-chat go if the launch check blocks it (memory: launch permission block) | about $0.6–0.75, worst about $2.7–3.1 at the cap (R1B:186-188, E) |
| 8 | **Merge and run on the final tree**: commit steps 4a–4g by explicit paths; the B16 suite (if touched), builder suite, the `scripts/stage1_s1` package, the W1 suite, engine X, the kit, the judges suite alone; `commitments.py check`; the specs (builder, new reader, B14; B16's full spec only if B16 changes, about 2.1 h in four shards, R1D:170-171); ADD:428's simulations if ruled | step 4 | L (background jobs) | $0; about 4–6 h wall clock |
| 9 | **Strata**: `overlap_strata.py strata` under the **new** strata settings; SHA-256 of `strata.json` into FOCUS (ADD:375); commit | steps 7, 8 (4c merged) | L | $0 |
| 10 | **Inputs file**: the writer from `plan.json` and the pins; a second process reproduces it byte for byte; commit | steps 8, 9 | L | $0 |
| 11 | **Records**: D-5 (and D-6 and later numbers), §39, the S1 blinding record, FOCUS with the new hashes; a note for SPF:344; commit, `commitments.py check`, push | steps 8–10 | L | $0 |
| 12 | **Second stamp** of the final code, runbook, script, inputs file and strata (R1D step 0.6); wait for its anchor; verify as step 2; record in FOCUS | steps 2, 11 | L | $0; the wait is hours (E) |
| 13 | **Go or no-go** (R1D step 0.7), then the reading script as one background job: R0, R1a, R1b, B14 report, builder, B16, the claim reader, the new readers, LN-31's draw | step 12 | L | $0 |
| 14 | **After the reading**: the mechanical reading record; FOCUS; commit, push, backup; optional third stamp; report to the user and go on (KW:7) | step 13 | L; U is told | $0 |

Total new spend before the reading: about $0.6–1.2 (E) for one pod, worst about $3, plus about $1 a day of storage.
Everything else is $0. A wrong expected line in step 13's pre-runs sends the lead back to step 12 (§2.10).

---

## 6. Decisions for the lead

| # | Decision | Recommended default | Pre-set fallback and its trigger |
|---|---|---|---|
| 1 | RI-O2: S-G's coherent-only U | V1A's linearized table on all 200 prompts, read by a reader beside B16 that calls B16's unedited functions; per-arm pooled coherent-only U and G2's per-pair counts printed; recorded as D-5 with REV4:919's label | (c+): per-arm pooled coherent-only U per cell, no label re-read, recorded. Trigger: not verified (suites, specs, independent check, 90% coverage 0.88–0.92 in prompt-concentrated worlds) after one fix round, or when steps 7–10 are done |
| 2 | G3a corner | both adverse corners per contrast, from the existing tables, in the same reader; the symmetric table kept, labelled | the symmetric table only, with that label. Trigger: not verified with decision 1 |
| 3 | B14's recipe refusal | settings-only fix (R1B §5): drop `recipe_sha256` from the report identity, refuse recipes G and B+Qi, re-take STR's pin, flip the test; land before `strata` | `--no-overlap`, "not computed", a deviation naming the cause. Trigger: not verified when steps 4a, 4b and 4d are done, or `plan.json` shows a non-S recipe for a kit unit |
| 4 | 1b route | R1B route (i): kit round 34 and one A100 pod after the Mac pre-check; drop PLAN's Mac fallback (C2) | R1B route (ii), a one-off pod with a self-stop timer and a checklist. Trigger: round 34 not verified when the other builds are done; last resort `--no-overlap` after two failed pod attempts or a balance below $6 + cap × $1.85 |
| 5 | Reading-time outputs with no producer | before the second stamp: F_k's measured-q power, the stage-3 pick, the LN-14 and LN-19 extract, the S-a shift line, and the cost table from readable ledgers | build after the reading, each labelled "code written after the reading". Trigger: not verified when decisions 1–4 are built |
| 6 | Descriptive reports (Q7, Q8, Q9, Q12) | after the reading, each labelled "code written after the reading" | the ambitious set before the reading. Trigger: the lead has idle worker time before the second stamp |
| 7 | LN-31 draw | build and commit the protocol, script and seed tags before the second stamp; record the missed LW-30 and HLC:168 deadline | draw when raters are funded, disclosed. Trigger: not verified when decisions 1–4 are built |
| 8 | S1 blinding record | one record listing every inference rule written after FOCUS:143's W1 commit, with the Gate B values read before each, inside the second stamp | the same list in the reading record's limits. Trigger: not written when step 11 starts |
| 9 | ADD:428 simulations | re-run on the final B16 code before the second stamp, or cite the S1-freeze run if it exists | state that the last run used the 23 Oct code. Trigger: scripts not found or the run will not finish in time |
| 10 | §39 content | rule every item of §2.1 | none needed |
| 11 | Pre-run expectations | stop on identity lines only; log the count lines | R1D's strict list. Trigger: the lead prefers strict |
| 12 | Stamps | keep the `ots` venv; R1D's margin (6 confirmations, 2 h after the header time); a third stamp after the reading | PLAN:34's fallback. Trigger: no anchor after 48 h |

---

## 7. What blocks the reading now

1. **RI-O2 is open.** B16 prints S-G without coherent-only U and without a note (B16/reading.py:313; RI/build.py:84-87).
2. **B14 cannot produce §9.4 as pinned.** The report refuses recipe-S units (P2); no inputs-file writer exists (P3);
   no `similarity.json` or `strata.json` exists (FOCUS:75).
3. **PLAN's step 2 command** lacks `--hb-out`, so step 4 cannot run (C5).
4. **Neither stamp is in place.** The first is pending and its client is gone (STAMP:36, :38); the second does not
   exist (PLAN:39-40).
5. **Pre-registered reading outputs have no producer**: F_k's measured-q power (REV4:574), the stage-3 pick
   (REV4:428), LN-14's bar and LN-19's shares (REV4:554-555). Each needs a reader or a recorded deviation first.
6. **Records missing**: §39, the D-5 record, the S1 blinding record (REV4:919), and the LN-31 deviation if the draw
   is built late.
7. **No suite or spec has run on the final tree** (it does not exist yet).
8. **LN-31's script does not exist** (blocks step 5 only).

---

## 8. Commands, limits

**Commands I ran** (exit 0 unless noted): `date -u` three times; `git rev-parse`, `git log`, `git status --porcelain`
in the main checkout (read-only); `sed`, `grep`, `awk`, `cat`, `wc`, `ls` on the cited files; `python3 -I -B -c` to
parse RIB, HBB, B16H and `mutants_b16.json` by key; `shasum -a 256` on PLAN, the four reports and V1A's six evidence
files; `grep -rl` for "S1 blinding" in `research/`, `docs/`, `.ai/briefs/` and the `reading/` folder (names only);
`grep -rln` for the kind "stage1 overlap report inputs" in `scripts/`, `runkit/` and `experiments/` (code trees;
names only); `ls experiments/` to confirm it holds code. Failed before reading anything: one `grep --include=*.py`
(zsh glob, exit 1), one `ugrep` pattern (complexity limit, exit 1), one `sed` with a malformed script (exit 1).

**Limits.**
- I did not run any repository test, spec or code. Every time and cost marked E is an estimate from the reports or
  the build records.
- I did not open `plan.json`, any seal, unit or judge file, so W4 and the recipe-S chain rest on code and on R1B's
  parse of `plan.json` (R1B:149-150), not on a unit.
- I did not locate the 23 Oct statistics verifier's simulation scripts, so §2.6 is a missing record, not a proven
  missing run.
- I did not check the Bitcoin anchor (no network).
- My search for an S1 blinding record covered `research/`, `docs/`, `.ai/briefs/` and the `reading/` folder. I did
  not search `tmp/` or the W1 inputs folder, by the data rules.
