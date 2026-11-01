# Build report: track E-records (the lead's records before the stage-1 reading)

- **Written** 2026-11-01 by an Opus builder for the lead (GI VIII); clock checked with `date -u` at 05:29 and
  05:39 UTC. Self-identification is not verification; the launcher records routing.
- **Scope kept.** Documents only, all in this folder. No repository file, no git state, no test, spec, reading,
  builder, overlap, claim, judge, seal, kit or launch command; no network, install, pod or API call.
- **Sources** read at commit `55d5f8b` with `git show 55d5f8b:<path>` (the main checkout is at `55d5f8b`; its working
  tree has uncommitted edits to FOCUS, HANDOFF and EDGE_CHECKS, so I never read the working copy).

## 1. Files written (all new; SHA-256 first 16)

| File | SHA-256 | What it holds |
|---|---|---|
| `E-D5-D6.md` | `597a5abf9c8880af` | (b) D-5 and D-6 as post-W1 deviations in D-4's point style, each with facts, ruling, reasons, fallbacks with triggers, the S1 blinding line and the paper label |
| `E-39.md` | `3c34975cdedfa650` | (a) addendum §39 points 3-11: the builder's RI-O1 and RI-O5 to RI-O14, the claim reader's R2, R3, R5, R6, R7, R9, B16's README readings and overlap R2-R6, B16-D4-O2/O3 and B16-H-O9, the coherence condition at B16/reading.py:449, S-tok's and §9.4's wording, the runbook's readings, the stamps, and the keep-working instruction in place of "stop and ask" |
| `E-S1-blinding.md` | `51730505d0dc12af` | (c) the S1 blinding record: the rule, the W1 commit, Gate B values G0-G5 with times and FOCUS lines, 14 post-W1 rules with the values read before each |
| `E-misc.md` | `30fbe59f820dd465` | (d) B14's scheduling gap and the route ruling; (e) D-7, LN-31's late draw; (f) ADD:428's simulations: the recorded run and its limits |
| `E-40.md` | `12c425b7ef6cfe56` | (g) addendum §40, stage 1b's rulings before any pilot unit exists |
| `E-plan-updates.md` | `b047cff76503d9b4` | (h) 12 stale points of the plan (CRIT's six plus six), each with the exact old text and the replacement |
| `E-records-build.md` | this file | the build report |

Temporary extracts of four committed files (`.rev4.md`, `.hbb.json`, `.b16h.json`, `.plan.md`) were made in this
folder for reading and deleted at the end.

## 2. Design, and the alternatives I rejected

1. **D-5 and D-6 as points 1-2 of §39** (D-4's style, ADD:605). Rejected: their own sections (§18's style); the lead
   can move them without other edits.
2. **D-5 exactly as briefed**, with details taken from V1A and CRIT: the counts side document (n, u, u_fail) bound to
   `tables.json` like `--hb-out`; "verified" as V1A decision 3 with the coverage band; the last fallback's trigger
   ("(c+) not verified when the second stamp's manifest is written") is my wording, because the brief gave none.
3. **"Never stops the reading"** is written as: statistical failures print "not computable" with p = 1 in S-G's own
   Φ run; a whole-reader refusal is logged and the reading's other steps stand. Rejected: a refusal that stops the
   script (R1D's S1 would do that today, see open point 5).
4. **The S1 blinding record lists more than the brief's seven rules**, marked "added": ADD §16 points 1-3 (written
   at 00:40 UTC on 23 Oct, after the W1 commit and 20 min before wave 1 was read), §22 point 1, §33 point 4, the
   readings coded into B16, the builder and the claim reader, §40's readings and D-7. Reason: REV4:919 says "any
   inference rule still written after the W1 commit"; listing too much costs nothing, missing one is a defect.
5. **FOCUS line numbers.** The brief's FOCUS:134, :137 and :139 are `0daca9a`'s numbers. At `55d5f8b` the same
   entries are FOCUS:135, :138 and :140 (one entry was added at FOCUS:74). Every FOCUS citation in my files uses
   `55d5f8b`'s numbers; the reports' FOCUS citations were mapped (+1 from line 74 on).
6. **σ̂ 1.78 pp** is listed as read from 23 Oct 05:26 UTC (when the verdict file holding it was written), though
   FOCUS first records it on 25 Oct 11:05 UTC: the conservative direction for a blinding record.
7. **ADD:428.** The recorded run is the statistics verifier's of 22 Oct 22:07-23:02 UTC on B16's build tree, before
   the fix pass; the fix pass says the simulations were not re-run (`b16-fix.json`:269); no run at the S1 freeze is
   recorded. Ruling as briefed: cite that run (B16 stays unchanged), state its limits, record the missed re-run, and
   copy the git-ignored evidence somewhere durable. A re-run on the final tree is listed as optional only.
8. **LN-31** is numbered D-7 provisionally (deviations in ruling order, CRIT:243).
9. **The pilot gate's edges** (§40 point 1) read through B16's 1e-9 pp tie tolerance: an addition to the brief's
   ruling, marked as such, because three-seed means move in steps of 1/18 pp and can hit 5 or 10 exactly.
10. **The plan's updates** as old/new pairs for an in-place edit with a dated revision line. Rejected: a new plan file
    (it would leave two plans named in FOCUS).

## 3. Commands run (all read-only; exit 0 unless noted)

- `date -u` (4 times); `date` once (the Mac's clock is IST, so local file times are UTC + 5:30).
- `git -C <main checkout>`: `log`, `status --short`, `rev-parse`, `show 55d5f8b:<path>` (many), `diff --stat`,
  `diff 0daca9a 55d5f8b -- research/FOCUS.md`, `blame -L 449,449` and `-L 315,315` on `reading.py`, `log` of
  `reading.py`, `build.py`, `hb_claim.py` and the plan, `merge-base --is-ancestor`, `ls-tree` of record folders and
  of the reading folder, `grep` for three recipe hashes in settings files.
- `ls`, `shasum -a 256`, `grep -n` on the files cited; `/usr/bin/python3 -I -B` to print keys of RIB, HBB, B16H,
  `b16-verify-stats.json` and `b16-fix.json` (synthetic-data verifier records).
- **Check 1** (citations at `55d5f8b`): a script compared 156 cited `path:line` facts with the line's text at
  `55d5f8b`: 0 mismatches, exit 0.
- **Check 2** (citations into the scratch reports): 92 cited lines; 7 flagged, each because the checked word sits
  one or two lines inside the cited range (R1B:76, :155, :186, :253; R1D:312; CHECK:261, :351); all within the
  ranges as cited.
- **Check 3** (the plan): all 13 "Old" blocks of `E-plan-updates.md` occur verbatim in the plan at `55d5f8b`, exit 0.
- Failed or not run: one `echo ===` (zsh glob error, exit 1, it read nothing); one Bash call got no classifier
  verdict and did not run; I repeated it once and it ran.
- **Tests and mutation:** none. This track writes documents only; I added no mutation entry and ran none.

## 4. Data rules

- Not opened, listed or hashed: anything under `tmp/stage1-olmo/` (`hosts/`, `judges*/`, `seals/`, `retrieved/`),
  `tmp/judge-pod*`, `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, `block-a/`, `block-b/`, any `units/` or
  `eval/` folder, COMPLETE.json, answer, label, guard-sample or judge-cache file, the hidden and selector banks, and
  every W1 "sealed record".
- Opened with a path that holds "plant": only code, `scripts/stage1/build_plant.py` lines 282-287 and 306-308 (the
  brief allows code), and the W1 manifest's two settings entries for the plant files (MAN1:939-942, :1107-1110:
  path, role and SHA-256 only; the manifest is not a sealed record). No settings or record file of the plant was
  opened. `scripts/stage1/labels.json` was searched for one key name (0 matches).
- In the lead's git-ignored notes (`.claude/worktrees/kind-hawking-a6ce04/tmp/claude-workspaces/stage1-integrate-20261017/notes/`)
  I listed file names and read the B16 verifier and fix records' keys (synthetic data only).
- One `git ls-tree | grep` printed names (no content) under `research/costs/receipts-snapshot/headroom-v2/retrieved/`,
  an old committed receipts snapshot of the headroom-v2 study, not stage 1. I report it so the lead can judge it.

## 5. Open points for the lead

1. **FOCUS numbering:** the brief's FOCUS:134, :137, :139 are :135, :138, :140 at `55d5f8b` (point 2.5).
2. **The S1 blinding record's added rows** (point 2.4): keep or drop each; §40's readings and D-7 need the commit time.
3. **ADD:428:** the only recorded run predates B16's fix pass and D-4; the S1-freeze re-run did not happen; the
   evidence sits in a git-ignored worktree folder and should be committed or backed up before the second stamp.
4. **D-5's last-fallback trigger** is my wording (point 2.2).
5. **The runbook must treat D-5's reader as non-fatal.** R1D's stop rule S1 stops on any non-zero exit; for D-5's
   reader the script should log the exit, keep going and let the record print the fallback wording.
6. **§40 point 1's tie-tolerance reading** is an addition; it touches a scientific rule's edges, so the lead may
   raise it to GPT before adopting it.
7. **Deviation numbers** D-5, D-6, D-7 assume this ruling order. SPF:344 needs D-5 to D-7 added; FOCUS needs entries
   with the new hashes; the plan's new SHA-256 after the edits goes into FOCUS (FOCUS:75 names `121c5119…`).
8. **Pinned texts that name a withdrawn fallback:** B16's `settings/reading.json`:200, B16/README.md:68 and the
   builder's `--no-overlap` help (RI/__main__.py:45-46) cite §24 point 4. I left them (changing B16's settings moves
   its pin); the record corrects the reference under D-6's fallback.
9. **Scratch citations:** §39 and the deviation records cite reports in `/private/tmp/…/scratchpad/`, which is
   temporary. Commit copies of D1A, V1A, CRIT, R1B, R1D, READY and CHECK (or their SHA-256 values) with the records.
10. **Not verified by me** and marked so: R1B's parse of `plan.json` (recipe S on all 55 arm and 5 a0_arm jobs),
    `scripts/stage1/settings/limits_check.json:7`, and the plant-rank report's lines cited from CHECK.
11. **Separate rulings still open** (not §39's scope): producers for F_k's power at the measured q, the stage-3 pick,
    LN-14's and LN-19's reports and the S-a shift line; any gap they fill joins the S1 blinding record.
12. **Self-Inf-N's switch** in the plant-rank report's settings can only be confirmed by a reviewed key-only
    extractor (§40 point 13).

---

## Fix round (after the independent verifier's round 1, `E-records-verify1.md`, SHA-256 `7a1b950e6a81c483`)

- **Written** 2026-11-01 by the same Opus builder; clock checked with `date -u` at 07:32, 09:27, 09:28, 09:29, 09:30,
  09:31 and 09:32 UTC. Self-identification is not verification; the launcher records routing.
- **Sources** read at `55d5f8b` with `git show 55d5f8b:<path>`. The main checkout moved to `7452bd2` during the round
  (commits `7fbff5a`, `38e160d`, `7452bd2`: FOCUS, one user-answer record, the grant dossier). `git diff --quiet
  55d5f8b HEAD -- scripts runkit experiments` holds (exit 0), so the code the tests imported equals `55d5f8b`'s.
- **Verdict on the verifier's report.** I checked every defect and note against its sources. All nine defects are
  real and fixed. Of the 21 notes, 20 are fixed as written or with an equivalent text; note 7 is fixed with one
  addition the verifier did not have (below). Nothing in the drafts reads or depends on a stage-1 outcome.

### F1. The nine defects

| Id | File | Check (M = measured here) | Fix |
|---|---|---|---|
| D1 | `E-D5-D6.md` items 1, 2, 9 | Confirmed (M): B16's `cell_value` multiplies the prompt mean by 100 (B16/contrast.py:84-85); V1A:209 says "V as a share". `d5_scale_check.py` (synthetic, exact fractions, B16's own `item_part`): with V as a share the item part is 339.5062 pp² (= 27500/81 exactly); with V in pp it is 1,173,672.8 pp²; the estimate is 16.6667 pp both ways; with every n = 3 both scales give x = u/3, so the all-n = 3 check cannot see the error; on 2,000 random unequal-n cells, mean_p x = V and n = 0 → x = V hold exactly and B16's item part matches the exact value to 4.3e-13 relative. Exit 0 | Item 1: V is a share, printed as 100 × V. Item 2: "with V as a share", B16 scales by 100 itself, and why the all-n = 3 check cannot catch a wrong scale. Item 9: an unequal-n hand case against an exact-fraction reference (marked "added") |
| D2 | `E-40.md` point 3 | Confirmed: FOCUS:74 ("joins the never-open list") and CHECK:187-191 put no time limit on `retrieved/`; the "until" came from CHECK:155-156, which is about plant-arm folders | "Never opened by hand or by a helper: `retrieved/` … and every plant-arm unit folder. Only reviewed code reads them, by key." Point 10 now says the two stay under this never-open rule |
| D3 | `E-40.md` point 2 | Confirmed (M): the verifier's `pilot_fallback_case.py` (synthetic, B16's `contrast_paired`): frozen form Λ 11.3333 pp, SE 5.0987, df 198.48, lower bound 4.7772 → stop; seed part only SE 0.0962, df 2.00, lower bound 11.1519 → go. Exit 0. REV4:675 fixes seed part plus prompt part | Fallback deleted. "No fallback": Gate A's a0 tables are those the builder reads through `REJUDGED_PINS["A"]` (RULES:171-183; RI/build.py:7-9, :259-268, checked); if they cannot be built the pilot is not read until they can, and any other interval is a post-W1 deviation written before any pilot value is read. READY's fallback is listed as not adopted, with the counterexample |
| D4 | `E-S1-blinding.md` G4, G5, §4; the S1 lines of `E-D5-D6.md`, `E-39.md`, `E-40.md` | Confirmed: FOCUS:135 says the `--final` output `06a7020a…` holds "every pre-registered §6 report"; RULES:341-344 names the file | G4 lists the §6 values as possibly read from 05:26 UTC on; every row from 2 on says "§6 possibly"; row 8 states the position on §37's R4 (ruled after the E_HB values existed; whether they were read is not recorded, so listed as possibly read). The four S1 lines say ":135 with its §6 values possibly read" |
| D5 | `E-39.md` point 8(d) | Confirmed: R1D:720 (S1) stops on any non-zero exit; D-5 point 8 says it never stops the reading | 8(d) adopts S1-S9 with two changes: (i) S1 and S5 do not apply to D-5's reader (step 4b); its exit is logged, the script goes on, the record prints D-5 point 8's wording; (ii) the checkers fail only on identity lines. S5 is added beside S1 because a binding mismatch inside D-5's reader would otherwise stop the script by S5. D-5 point 8 now spells out the wording printed after a run-time refusal and points to S4 for any later fix (R1D:727-730) |
| D6 | `E-D5-D6.md`, last fallback | Confirmed: D1A:503-505 describes the drop rule as D-5; D1A:500 says "every label is re-read through Φ"; B16 re-reads only the U-part words (B16/reading.py:284-301) | The (c) paragraph is printed with four listed edits: the D-5 description, "D-5 and its fallback (c+) were not verified", "the U-part words are re-read through Φ", point 7's label on the unscored corner plus one sentence that the adverse G3(a) corners were not computed. I shortened the verifier's first replacement (its "its fallback (c+)" appeared twice in the edited sentence) |
| D7 | `E-39.md` point 6 | Confirmed (M): REV4 uses "the selector" for §7's model-based selector (REV4:79, :562, :611-614); REV4:302's second half is B16's family-1b rule (B16/reading.py:427-433) | Rewritten as a stated reading that fills a gap, with the verifier's facts; ADD:427 is cited as ruling "better and feasible" without naming coherence; S1 record rows 1 and 12 |
| D8 | `E-40.md` points 5 and 10 | Confirmed (code only, M): the edit's name field names the leaf (`build_plant.py`:284, :307); the planted_k37 file is `edits/planted_k37.json` under `--full-out` (:35, :290); the record lists `{file, sha256}` (:291) and the unit and leaf (:442); CHECK:313-315 asks for the binding check | Point 5: the edit record's path and SHA-256 come from hashing the file at its known path (FOCUS:131 names the git-ignored folder), no byte shown; a reviewed key-only binding check prints "match" or "no match", tested with sentinel strings. Point 10: the rule binds everyone, the lead included (CHECK:155-156) |
| D9 | `E-D5-D6.md` new item 2b | Confirmed: V1A:227-229 ("D-5 must state this reading"), V1A:364; GBR:457-470 is Gate B's clustered SE with the pairwise drop | Item 2b states the reading of G2's per-prompt rule, as the verifier wrote it |

### F2. The 21 notes

| Note | Fix |
|---|---|
| 1 | §40 point 1: the tolerance applies to Λ_plant (the estimate) only; the lower bound's comparison with 5 pp is exact, as B16 reads interval ends (B16/README.md:153-155, quoted) |
| 2 | S1 record row 12 is "§39 points 3-9"; §39's S1 line labels points 1-9 and says point 10 (the user's decision) and point 11 (rules nothing) are not inference rules |
| 3 | G5: σ̂ possibly read from 04:31 UTC (the first verdict `030a7846…`, FOCUS:138, equal in content to `bec5f103…`, FOCUS:135-136) |
| 4 | New row 3b: §24 point 4, written 23 Oct 20:24 UTC (ADD:508), withdrawn 29 Oct 09:35 UTC (FOCUS:104) |
| 5 | `E-misc.md` C: D-4's regression re-run flagged one synthetic document, an S-start entry and not a label (B16H:539, :243); D-4's own motivating case changed one synthetic label (ADD:605) |
| 6 | `E-misc.md` C: z-level "every value <= 5%" (b16-verify-stats.json:352; opened by exact path, SHA-256 `65fe90c3…` matches); end to end G0 plan B 5.20% ± 0.70 (:358), "within Monte Carlo error of 5%, not shown below it" |
| 7 | `E-40.md` point 9: the frozen condition is "funded" only (REV4:710; W1R:296), as the verifier says. **Addition:** the plant builder's own docstring gates `--f9` on "the user's yes and stage 1b's funding event" (`scripts/stage1/build_plant.py`:30, code, M), so the draft states both, each with its source |
| 8 | `E-40.md` point 11: the staged rule is ADD:635; the $6 reserve is KW:8 and ADD:657 |
| 9 | `E-40.md` point 6: CHECK's fallback (K7 on the pilot pod) is marked "not adopted", with the reason |
| 10 | `E-40.md` point 5: blocks A, B and C's tables (`block_runs`, RULES:294-315, checked) |
| 11 | `E-39.md` point 10: REV4:887 cites FR-25 and FR-21; both are the user's (LEDGER:70, :74), as is FR-23 (:72) |
| 12 | `E-39.md` point 8(a) and the RI-O8 row: the reason now says the builder refuses missing, duplicate or extra **cells** (RI/build.py:9-13, :271-272); references have no required list, so the record names any planned reference that is absent as a limit beside family 1b. Making the references line an identity line is written as an option for the lead (RIB:441-442), not adopted, because CRIT:224 lists identity lines without it and the brief's ruling is "stop on identity lines only" |
| 13 | `E-D5-D6.md` item 9: additions marked "added"; the comparison is "to 1e-9 (V1A:361)", and the 1e-6 relative tolerance for SE and df applies only where the reference fits REML on its own (B16's REML stops at a 1e-6 step, ADD:425) |
| 14 | `E-plan-updates.md`: item 7 adds the 0.75% tail criterion and the unequal-n hand case; items 8 and 9 put the records (§39, §40, D-5 to D-7, the S1 blinding record), the kit files after round 34, `similarity.json` and the D-7 script into the second stamp; new item 13 replaces row 1d (PLAN:33) |
| 15 | `E-misc.md` A ruling 1: "before any stage-1 outcome is read", with ADD:375's add-arm rule kept for the strata's SHA-256; W1R:129's "at S1" read as B14's code, because S3 and S4 did not exist until after block A's diagnostics pod started (R1B:69-74; REV4:29; ADD:503) |
| 16 | `E-misc.md` new ruling 2b and plan row 1b: round 34 lands in both kit copies before the reading (R1D:220, :228-229), so it keeps every value the builder reads unchanged, tested (`block_runs` A-C, `REUSED_SEEDS`, `REJUDGED_PINS`, the seven judge constants; RI/build.py:242-262, :537-557, checked), and the runbook pins and the second stamp take the new hashes |
| 17 | `E-39.md` points 7 and 8 now quote each stated reading (RIB:420-422, PLAN:32, CRIT:142-143, CRIT:224-225, R1D:519, :524, :682, :720, :733-734, :784-786, :799-800, :804-805) |
| 18 | `E-39.md` new point 8(g) records R1D's repository-wide grep (R1D:823-829) |
| 19 | The short-name tables of `E-D5-D6.md`, `E-39.md`, `E-40.md` and `E-plan-updates.md` now give the SHA-256 of each scratch report (unchanged since round 1); committing copies stays the lead's step |
| 20 | `E-40.md` point 4: "DataShield-style and L1 outputs on the Mac if they do not exist yet" (CHECK:363; READY:227-228) |
| 21 | S1 record row 9: "R2, R3, R5, R6, R7 and R9" |

Also added: a note under the S1 record's table that part of rows 10-13 was first written in FOCUS at 2026-11-01T04:55
UTC (commit `7fbff5a`, time set by `38e160d`; FOCUS:74 at `38e160d`), after every Gate B value listed.

### F3. Commands run in the fix round (exit 0 unless noted)

- `date -u` (7 times). One `echo ======` failed in zsh (`=` expansion; exit 1; it read nothing).
- Read-only git in the main checkout: `rev-parse`, `log`, `status --short`, `diff --stat`, `diff -U0` and
  `diff --quiet` (FOCUS and code since `55d5f8b`), `show 55d5f8b:<path>` (REV4, ADD, W1R, FOCUS, PLAN, KW, LEDGER,
  RIB, B16H, GBR, PREREG, RULES, B16 and builder code, `build_plant.py` code), `show 7fbff5a --stat`,
  `show 38e160d:research/FOCUS.md` and `show HEAD:research/FOCUS.md` (lines 74-76 only), `grep` of B16's test names.
- `shasum -a 256` of the drafts, the scratch reports, the verifier's report and three leftover extracts.
- Synthetic checks, `PYTHONDONTWRITEBYTECODE=1 …/venv/bin/python -B`, importing B16's code read-only from the main
  checkout: `E-fix-checks/d5_scale_check.py` (PASS, see D1); the verifier's `pilot_fallback_case.py` (see D3) and
  `linearized_check.py` (PASS: mean_p x = V, n = 0 → V, n = 3 → u/3 on 2,000 cells; the hand case V_item 625 pp²;
  6,317 of 20,000 exact-10 pp means land below 10.0 in floating point).
- `E-fix-checks/check_records.py` (`/usr/bin/python3 -I -B`; reads sources by `git show 55d5f8b:`): **PASS** — 14 of
  14 "Old" blocks occur exactly once in the plan; 763 cited lines in range (short names, scratch reports and
  repository paths); 107 of 107 phrase checks on the citations added or changed in this round. Its first run exited 1:
  three phrase checks failed only because the quoted words span line breaks in the source; I made the checker
  normalize whitespace (the drafts did not change for this).
- Targeted B16 tests on synthetic data, `PYTHONDONTWRITEBYTECODE=1 …/venv/bin/python -B -m pytest -q -p
  no:cacheprovider --basetemp=<builds/tmp/E-fix-pytest-…>` in the main checkout: **7 passed in 9.04 s** —
  `test_reading.py::test_coherence_flags_print_beside_the_word_and_never_change_it`;
  `test_fixes.py::test_a_coherence_failing_repair_never_dominates_in_family_1b`,
  `::test_the_per_actor_best_arm_names_an_arm_when_one_is_better_feasible_and_separated`,
  `::test_an_exact_5_pp_tie_reads_better_whatever_the_float_rounding`, `::test_the_tie_tolerance_is_1e_9_pp_from_the_settings`,
  `::test_better_holds_at_exactly_delta_minus_the_tie_tolerance`; `test_labels.py::test_separation_and_the_best_feasible_repair`.
  The base folder was deleted; `git status --short -- scripts` stayed empty. No mutation run: this track writes
  documents only.

### F4. Data rules in the fix round

- Not opened, listed, grepped or hashed: anything on the brief's never-open list and every W1 "sealed record".
  `check_records.py` refuses to open any non-code path that holds "plant" or "decoy" or any never-open fragment.
- Paths that hold "plant": code only — `scripts/stage1/build_plant.py` lines 30-37 and 276-315 and a `grep` of its
  output paths and record keys. FOCUS:131 was read (it names the plant record's path and SHA-256, not the leaf).
- The lead's git-ignored notes: only `b16-verify-stats.json`, opened by exact path (lines 276-300 and 345-372) and
  hashed (`65fe90c3…`, as in round 1). **Disclosure:** round 1's `grep -r` over that notes folder (E-misc C) read the
  content of every file in it to match three script names, printing only file names. The folder is not on the
  never-open list, but I cannot rule out that it holds something sealed; the lead should judge it.
- Deleted: three byte-identical extracts of `55d5f8b` files (`.add55.md`, `.focus55.md`, `.rev455.md`; SHA-256 equal
  to `git show`) left in this folder at about 06:20 UTC by an interrupted earlier start of this fix round, which also
  wrote `E-fix-checks/d5_scale_check.py`; my own extracts in `E-fix-checks/`. Kept as evidence: `check_records.py`
  (`2dbce82332e7341f`) and `d5_scale_check.py` (`3354e347c10198d2`).

### F5. Files after the fix round (SHA-256 first 16)

| File | SHA-256 |
|---|---|
| `E-39.md` | `c69b8e5f7135ff4b` |
| `E-D5-D6.md` | `883f2c723f7311e7` |
| `E-S1-blinding.md` | `48db21e34736462a` |
| `E-misc.md` | `ee94de5878d7be92` |
| `E-40.md` | `a4ab238338a214e7` |
| `E-plan-updates.md` | `3ff601d3c6e9cdc3` |
| `E-fix-checks/check_records.py` | `2dbce82332e7341f` |
| `E-fix-checks/d5_scale_check.py` | `3354e347c10198d2` |

### F6. Open points for the lead (this round)

1. **FOCUS numbering at HEAD.** The drafts cite FOCUS at `55d5f8b`. At `7452bd2` every FOCUS line from 74 on is 2
   higher (two entries added at the top; checked for six entries), and the stamp entry's recorded time reads 04:45
   instead of 04:46 UTC. Keep the commit pin in the citation headers or remap when committing.
2. **D-5 item 9's tolerance** (1e-6 relative for SE and df where the reference fits REML on its own) is an addition;
   the lead keeps it or asks for 1e-9 everywhere.
3. **References as an identity line** (§39 point 8a): written as an option, not adopted.
4. **§40 point 2 has no fallback**: if Gate A's a0 tables cannot be built, the pilot waits; any other interval is a
   deviation written before any pilot value is read.
5. **The round-1 grep over the notes folder** (F4): for the lead's judgement.
6. **Earlier open points:** 5 (the runbook's stop rule) and 6 (the tie tolerance) are now settled in the records;
   10 (`limits_check.json:7`) was confirmed by the verifier; 3, 7, 8, 9, 11 and 12 stand.

---

## Fix round 2 (after the lead's rulings `lead-rulings-20261101.md` R6, SHA-256 `3096e37a09ac565a`, and the verifier's round 2, `E-records-verify2.md`, SHA-256 `1f05238d79211758`)

- **Written** 2026-11-01 by a builder for the lead (GI VIII); clock checked with `date -u` at 14:08, 14:28, 14:29
  and 14:30 UTC. Self-identification is not verification; the launcher records routing.
- **Sources** read at `55d5f8b` with `git show 55d5f8b:<path>`. The main checkout is at `a494ff7`; `git diff --quiet
  55d5f8b HEAD -- scripts runkit experiments` exits 0, so the code is unchanged. The design round's reports were read
  from their committed copies at `0e0ab1f` (`lead-reports-20261101/design-round/`, `next-stages/`), each byte-equal
  to the scratch copy (SHA-256 checked, 8 of 8). The build round's reports and the lead's rulings were read from the
  scratch `builds/` folder; track A's code from `builds/ws-a` (code and tests only; its `git status --short` count is
  10 before and after).
- **Verdict on the verifier's report.** The three defects are real; each is fixed as LR R6.1-R6.3 rule. Of the
  twelve notes, ten are fixed as written or with an equivalent text; note 10 is not adopted, by LR R6.5 (recorded
  with the reason); note 12 is a status, answered by LR R1.1. Nothing in the drafts reads or depends on a stage-1
  outcome.

### G1. The three defects

| Id | Ruling | What changed |
|---|---|---|
| D1 | R6.1 | `E-D5-D6.md` item 4: the no-value pre-run R1b takes the same `--coherent-out` option as step 2 (the option is track A's, ACB:18-21); the step-2 comparison leaves out `sources.json`'s `coherent.output_sha256` and the counts document's `input_sha256`, as it leaves out the HarmBench tables' hashes (R1D:589-594), because they bind `tables.json`, which differs by the overlap block; so if R1b passes, step 2 cannot refuse for a D-5 reason (EV2:54-63). Item 8: the reader never stops the reading; the builder half is settled at the pre-run; a refusal only on a coherent-only check sends step 2 on without the option (`tables.json` byte-identical) and D-5 straight to (c), chosen before any value; (c)'s paragraph names that cause. The last fallback gains trigger (ii) and the matching sentence. `E-39.md` 8(d): change (iii), and the same consequence. `E-plan-updates.md` item 3: "a no-value pre-run with the same options, `--no-overlap` in place of the four B14 options", the option name filled in, the comparison rule and the pre-run consequence |
| D2 | R6.2 = R1.2(a) | `E-D5-D6.md` item 9: the gate is plan A; every contrast in every world must meet the 0.88-0.92 band and the tail ratio (at most 1.5 × the primary form's); at least 2,000 replicates, and 10,000 where a world is within 2 Monte Carlo SE (0.0134) of a band edge or its tail ratio is above 1.3; plan B checked and reported; block A only a limit (RI/build.py:606-607 refuses it; B16's primary form outside the band there, ACB:255, :260-262). Track A's measured state is stated (ACB:251-255), with the consequence that at least one plan-A world needs the 10,000 run (lowest coverage 0.891, highest tail ratio 1.35). R1.2(b): estimates to 1e-9 pp, SE and df to 1e-6 relative where the reference fits REML on its own. R1.2(c): the official 47-entry spec as the lead's background run. R1.1 and R1.3 in the (c+) and (c) paragraphs. Plan item 7 takes the same scope |
| D3 | R6.3 | `E-plan-updates.md` item 9: step 4c (the five outputs, `cap_reports` included, each bound to `reading.json` by SHA-256, report only, run only inside the reading script, R4.4's exception named, the fallback label); items 8 and 9 (the second stamp holds `reading_extra/`), item 11 (the readers at $0), item 13 (their suite and 49-entry spec; `cost_table` after its fix round), row 1c (their readings). `E-39.md` point 11 rewritten from "ruled separately" to the readers' record: the five readers (D1B:17-25), status (four verified, D1V:16-21; `cost_table`'s fix round and fallback, R4.2), step 4c, the never-open exception (R4.4), the pre-check as new 8(h) (R4.5), the adopted readings (R4.3), the limits (R4.6). `E-S1-blinding.md` row 15 (added) lists the readers' readings; row 12 points to it |

### G2. R6.4, R6.5 and R6.6 applied

- **D-6** (`E-D5-D6.md` §2): the spec has 150 entries (BBB:16, :46); the 69-entry near set runs before the second
  stamp and the full spec in the background (R2.2), with `[FILL]` for which set ran; the deny-list limit as item 1b
  (R2.1; BBB:17; BBV:18-24, :145-147); the order as item 3 (R2.3); the pre-D-6 figure 87 is explained.
- **E-misc A 2b** states R3.3 (the equality checked by C's verifier, CKV:37, :137, :190, not pinned by a test; the
  first draft's claim withdrawn). Ruling 2 states R3.2 (the two new hashes, CKB:31-32). Ruling 3 states R3.1 (the
  `retrieved/sim-1/` route by exact path and SHA-256, the copy script, no outcome in `similarity.json`, `process.log`
  on a crash, never list `retrieved/`); the same in plan row 1b and, as a cross-reference, in `E-40.md` point 3. The
  fallback paragraph states R3.4 (N5, CKV:135, :201). R3.5 is in `E-misc.md` D.
- **D-7** (`E-misc.md` B) states R5: the confirmed readings 4, 7, 11, 12 and 13, the 106-term list and 5 age
  patterns, the benign label (2b; D2B:373-386, :357); the cross-seed loss with its simulated size 6-13% and the
  weights granularity as limits (2c; D2V:52-66, :67-79); HLC 4.3 item 4 read as the same code in a second process,
  with the verifiers' re-implementations as partial cover (D2B:250; D2V:80-83, :13-16); the inputs bound through
  block A's seal and `REJUDGED_PINS` (D2B:37-41); the restore to `tmp/hlc-inputs/` and step 5 (R5.5); the suite re-run
  after A's merge; the deadline dates (R5.4; W1R:243 added to the facts). S1 record row 14 says so.
- **Hard-rule notes** (R6.4, R6.6): new `E-misc.md` D records C's `git ls-files` print (CKB:404-406; CKV:246-248),
  D2's three 600 s overruns moved to the background by the harness, each exit 0 (D2B:210-213), and E's round-1
  `grep -r` as a disclosure with the lead's finding (no breach); §39 8(g) points there.
- **R6.5, point by point:** the `55d5f8b` pin stays and every header says so (no remap); §39 8(a) is ruled (not an
  identity line; the option is "not adopted"); §40 point 1's tie tolerance is "adopted" with the verifier's 627 of
  2,000 measurement (EV2:179); §40 point 2 "no fallback (adopted)"; §40 point 9 "adopted as written"; ADD:428's
  evidence: the lead commits copies of the two files (E-misc C ruling 3); SPF:344 adds D-5, D-6 and D-7 (S1 record
  §5); the pinned texts stay unchanged, now including the builder's refusal text RI/__main__.py:58-59 (D-6's fallback;
  §39 point 7); every scratch citation now names the committed copies (all six drafts; short names LR and the eleven
  build-round reports added, cited at today's scratch SHA-256 with `[FILL-hash]` for the committed hash); earlier
  open point 11 is closed by the new point 11, and 12 stays with stage 1b.

### G3. The twelve notes

| Note | Fix |
|---|---|
| 1 | `E-misc.md` A ruling 1: "S4's edit file dates from 25 Oct 15:42 UTC and S3's from 16:46 UTC" (R1B:69-74) |
| 2 | `E-misc.md` A ruling 1: W1R:129 "could not be met for the strata themselves … read as B14's code, built and verified at S1 (ADD:503); the strata are built later from the same inputs"; R1B:61's "build deadline only" cited; the ruling stands either way |
| 3 | D-6's fallback: the second trigger is "(added, beyond the brief's trigger; CRIT:347; R1D:783)" |
| 4 | D-5 item 7 quotes the label as the reader prints it, "unscored counted Unsafe in every arm (not Gate B's adverse corner)" (V1A:363; the reader's `SYMMETRIC_LABEL`, ACB:21-26), copied by key; the fuller wording is gone |
| 5 | `E-40.md` point 10: the verifier's wording ("opened by hand or by a helper, except code files; reviewed code reads such files by key only, or hashes them without showing a byte", with the four cases of points 3 and 5) |
| 6 | S1 record row 13 adds "K7 after a 'go' (point 6)", so it matches §40's S1 line (points 1, 2, 4 and 6) |
| 7 | S1 record "Not listed": §37 points 4-6 (a check, two operator rules, a not-built statement; ADD:644-646); §32 point 1's fallback (ADD:594), §34 point 3's B+Qi O fallback (ADD:616) and §34 point 7's G9 (ADD:620) as conditional reporting rules that changed no label |
| 8 | `E-misc.md` C optional run adds `zphi.py` (the z-level reading's script, `b16-verify-stats.json`:279-283, :367; `test -e` yes) |
| 9 | `E-misc.md` B ruling 2: the inputs are bound through block A's seal and `REJUDGED_PINS` as track D2 built it (D2B:37-41), so no sealed guard file is opened or hashed before the reading; the `tmp/hlc-inputs/` restore (R5.5) |
| 10 | **Not adopted** (LR R6.5: the pinned texts stay unchanged). §39 point 7 and D-6's fallback now name RI/__main__.py:58-59 beside :45-46, and say why the correction is not made |
| 11 | §39 8(c): the extractor runs when the D-5 output is absent and copies D-5 point 8's wording, or (c)'s paragraph, with the reason from the step's log; it also copies step 4c's outputs by key |
| 12 | A status, not a record defect: LR R1.1 (the re-verify of fix round 1 runs now and decides; no second fix round) is stated in D-5's facts, in (c+) and in plan item 7 |

### G4. Commands run in fix round 2 (exit 0 unless noted)

- `date -u` (4 times). Read-only git in the main checkout: `log` (HEAD and the `lead-reports-20261101/` folder),
  `ls-files` of that folder, `show -s 0e0ab1f`, `show 55d5f8b:<path>` (REV4, ADD, W1R, HLC, SPF, FOCUS lines 74-77,
  RI/__main__.py, RI/build.py), `show 0e0ab1f:<path>` and `show HEAD:<path>` piped to `shasum` for the seven
  committed copies and `sg_tail_check_10000.txt` (all equal to the scratch copies), `diff --quiet 55d5f8b HEAD --
  scripts runkit experiments` (exit 0), `status --short` (the lead's uncommitted merge work; not read).
- `sed -n` and `grep -n` on the design-round copies (scratch), the eleven build-round reports, the lead's rulings and
  track A's code in `builds/ws-a` (`coherent.py`, `__main__.py`, `build.py`:700-720, `sg_coherent.py`, `items.py`,
  `tests/test_coherent.py`:150-176, `tests/test_sg_coherent.py`:508); read-only.
- NOTES (the lead's git-ignored folder): `test -e` of `b16-verify-stats-evidence/scripts/zphi.py` (yes); `sed -n` of
  `b16-verify-stats.json` lines 279-283 and 367 and of `b16-fix.json` line 269, by exact path; `shasum` of both
  (`65fe90c3…`, `4090118e…`, as before). No listing, no grep.
- `shasum -a 256` of the drafts, the rulings file and the build-round reports; `grep` of the drafts for leftover
  scratch paths and stale phrases (0 hits after the edits).
- `E-fix-checks/check_records.py` (`/usr/bin/python3 -I -B`; it now takes `<reports folder> <repo root>`, reads the
  design round's copies with `git show 0e0ab1f:`, the build-round reports and the rulings from `builds/`, checks the
  committed copies' SHA-256 and refuses stale phrases). First run: exit 1 on two of my own new ranges (ACB:16-24,
  where the phrase is at :25; D2B:39-50, where the files table is at :43-56); the two citations and the checks were
  corrected. Second run: **PASS**: 14 of 14 "Old" blocks once; 914 citations in range (0 skipped); 244 of 244 phrases
  (107 from round 1, 137 new); 8 committed-copy hashes equal; 0 stale phrases. About 1 s each.
- No test, mutation, reading, builder, overlap, claim, judge, seal, kit, draw or launch command; no network, install,
  pod or API call. This track writes documents only.

### G5. Data rules in fix round 2

- Not opened, listed, grepped or hashed: anything on the never-open list, every W1 "sealed record", `plan.json`,
  `tmp/hlc-inputs/` (its two paths are named from the rulings only; the checker's forbidden list gains
  `hlc-inputs`). No path that holds "plant" or "decoy" was opened this round.
- `builds/ws-a` was read (code and tests) and not changed. No repository file, no git state, no other track's
  worktree was touched.

### G6. Files after fix round 2 (SHA-256 first 16)

| File | SHA-256 |
|---|---|
| `E-39.md` | `c659161c85b3020a` |
| `E-D5-D6.md` | `418c2372a56d90d5` |
| `E-S1-blinding.md` | `8128cac6c45448b4` |
| `E-misc.md` | `da538abaa80eda1c` |
| `E-40.md` | `26fd943d20ff408f` |
| `E-plan-updates.md` | `13c52b0057684ca2` |
| `E-fix-checks/check_records.py` | `a13cb1b9f626eab5` |
| `E-fix-checks/d5_scale_check.py` | `3354e347c10198d2` (unchanged) |

### G7. Open points for the lead (this round)

1. **New `[FILL]` values:** D-6's spec set and result (item 2); the committed SHA-256 of the rulings file and the
   build-round reports (`[FILL-hash]` in every short-name table); the D-5 re-verify's verdict decides whether (c+)
   or the main text prints.
2. **The build-round reports are cited by line at today's scratch SHA-256.** A fix round appends to a build report
   and moves no earlier line, but `check_records.py`'s BR map reads `builds/reports/` today; after the commit under
   `lead-reports-20261101/build-round/`, point it at that folder and re-run.
3. **§39 point 11 now holds the readers' rulings** (LR R4), labelled "fixed after Gate B wave 1" with points 1-9 in
   §39's S1 line and listed as S1 record row 15. The lead may prefer to keep point 11 as a pointer and give R4 its
   own section; the text moves without other edits.
4. **The never-open exceptions** (R3.1 for `retrieved/sim-1/`, R4.4 for the two readers at step 4c) are stated in
   §39 point 11, §40 point 3, `E-misc.md` A and the plan. FOCUS's own never-open entry (FOCUS:74) is the lead's to
   amend when the records are committed.
5. **Earlier open points:** 3, 7, 8 and 9 are now ruled (R6.5) and applied; 12 stays with stage 1b; F6's six points
   are all ruled or answered.
