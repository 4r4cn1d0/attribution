# Verification of track E-records (round 1)

- **Written** 2026-11-01 by an independent Opus verifier for the lead (GI VIII). Clock checked with `date -u` at
  05:40, 05:55, 06:08 and 06:10 UTC. Self-identification is not verification; the launcher records routing.
- **Under check.** The builder's report `E-records-build.md` and its six drafts in this folder. I checked the same
  versions the builder lists (SHA-256 first 16, M): `E-39.md` `3c34975cdedfa650`, `E-D5-D6.md` `597a5abf9c8880af`,
  `E-S1-blinding.md` `51730505d0dc12af`, `E-misc.md` `30fbe59f820dd465`, `E-40.md` `12c425b7ef6cfe56`,
  `E-plan-updates.md` `b047cff76503d9b4`.
- **Sources** read at commit `55d5f8b` with `git show 55d5f8b:<path>` from `/Users/spiderishi/Coding/attribution`
  (its HEAD is now `38e160d`; `git diff --stat 55d5f8b 38e160d` changes only `research/FOCUS.md`, so code in the
  working tree equals `55d5f8b`). Short names as in the drafts (REV4, ADD, FOCUS, W1R, PREREG, PLAN, KW, LEDGER, HLC,
  RIB, HBB, B16H, B16/, RI/, STR, STRS, LC, RULES, PT, JR, MAN1) and the scratch reports (CRIT, V1A, D1A, R1B, R1D,
  READY, CHECK).
- **Rules kept.** I opened, listed, grepped or hashed nothing under `tmp/stage1-olmo/`, `tmp/judge-pod*`,
  `tmp/family-probe-judge/`, `tmp/gi-viii-notes/judge-b/`, `block-a/`, `block-b/`, any `units/` or `eval/` folder, any
  COMPLETE.json, answer, label, guard-sample or judge-cache file, the hidden or selector bank, or any W1 "sealed
  record". Paths that hold "plant": I read code only (`scripts/stage1/build_plant.py:280-310`, at `55d5f8b`) and the
  W1 manifest's two settings entries (MAN1:938-943, :1106-1111: path, role, SHA-256). I printed the role of
  `scripts/stage1/labels.json` from MAN1 ("settings") and the paths and roles of the seven "sealed record" entries,
  nothing else of them. In the lead's git-ignored notes I opened only `b16-verify-stats.json` and `b16-fix.json` by
  exact path (B16's synthetic-data verifier records of 22-23 Oct); I did not list or grep that folder. No git state
  changed. I wrote only under `builds/verify-E-records/` and this report. The pytest base folder was deleted.

Labels: **M** measured or checked here; **R** read in a source; **I** my inference.

---

## Verdict: defects

The drafts are careful and mostly right. Of about 100 citations I opened by hand, all hold except three that support
less than the sentence claims (notes 5, 7 and 8), and all 313 short-name citations are inside their files. All 13
"Old" blocks of the plan update occur verbatim in the plan. Nothing in the drafts reveals or depends on a stage-1
outcome or a sealed choice. The FOCUS renumbering (:134, :137, :139 at
`0daca9a` are :135, :138, :140 at `55d5f8b`) is correct.

But nine defects matter for the reading's correctness, the frozen rules or blinding. The three most serious:
1. D-5's core formula, as written, puts V in pp into the linearized table; that inflates the prompt part by three to
   four orders of magnitude (about 3,500 times in the case of D1), and the all-n = 3 check in D-5's own "verified"
   list cannot detect it (D1).
2. §40 point 3 lets `tmp/stage1-olmo/retrieved/` (blocks A and B's sealed trees) be opened "until the counted
   outputs are hashed"; the lead's ruling says never (D2).
3. §40 point 2 adds an unmarked fallback that drops REV4:675's prompt part from the pilot interval; on a
   constructed synthetic table it turns the frozen gate's "stop" into "go" (D3).

---

## 1. Defects (most severe first)

### D1. D-5's linearized table is written with V in pp (E-D5-D6.md:52-57)

- **What is wrong.** Item 1 defines `V(a,j) = 100 × Σ_p u / Σ_p n` (pp). Item 2 uses the same V in
  `x = V + [u − V·n] / N̄`. V1A's formula needs V as a share: "with N̄(a,j) = N(a,j)/200 and V as a share"
  (V1A:209-211). B16 multiplies the table's prompt mean by 100 itself (`cell_value`, B16/contrast.py:84-85). With V
  in pp the prompt mean is still the share (the V terms cancel in the mean), so the point estimate looks right, but
  each prompt's x carries `V_pp·(1 − n/N̄)`, and the item part is wrong by orders of magnitude.
- **Why the record's own checks miss it.** When every n = 3, n = N̄ and x = u/N̄ whatever V is. So "the all-n = 3
  case equals the primary U_k exactly" (E-D5-D6.md:87-88) passes with the wrong formula. An independent reference
  written from the same record text would agree. Only the coverage simulation would catch it.
- **Reproduction (M).** Input: comparator n = (3,3,3,3), u = (3,3,0,0); repair n = (0,3,3,3), u = (0,3,0,0); two
  seeds. Command:
  `cd /Users/spiderishi/Coding/attribution && PYTHONDONTWRITEBYTECODE=1 tmp/minimal-experiment-20261002/venv/bin/python -B <scratch>/builds/verify-E-records/checks/units_check.py /Users/spiderishi/Coding/attribution`
  (B16's own `item_part`). Expected (V as a share): estimate 16.667 pp, item part 339.5 pp². Actual with item 1's V
  fed into item 2: estimate 16.667 pp, item part 1,173,672.8 pp² (exit 0).
- **Correct text.** Item 1: "**Cell value:** G2's pooled share, V(a,j) = Σ_p u(a,j,p) / Σ_p n(a,j,p), a share
  (printed as 100 × V, in pp) ...". Item 2: "... x(a,j,p) = V(a,j) + [u(a,j,p) − V(a,j)·n(a,j,p)] / N̄(a,j), with V
  as a share and N̄(a,j) = Σ_p n / 200 (V1A:209-211); B16 scales the table by 100 (B16/contrast.py:84-85)." Add to
  item 9: "and a hand case with unequal n against an exact-fraction reference (the all-n = 3 case cannot detect a
  wrong scale of V)."

### D2. §40 lets the kit's pulled block trees be opened later (E-40.md:58-59)

- **What is wrong.** "Never opened by hand or by a helper: `tmp/stage1-olmo/retrieved/` (the kit's pulled block
  trees, CHECK:187-191) and every plant-arm unit folder, until the counted outputs are hashed." The "until" clause
  attaches to both items. `retrieved/` holds blocks A and B's sealed trees (SEAL:3-4, 101-104 per CHECK:189). The
  lead's ruling in the brief is "tmp/stage1-olmo/retrieved/ and every plant-arm unit folder are never opened";
  FOCUS:74 says `retrieved/` "joins the never-open list"; CHECK B5 (CHECK:187-191) adds it without a time limit. The
  "until" comes from CHECK B1 (CHECK:155-156), which is about plant-arm folders only.
- **Reproduction.** Input: E-40.md:58-59 against the brief's (g) text and FOCUS:74. Expected: no time limit on
  `retrieved/`. Actual: "until the counted outputs are hashed" covers it.
- **Correct text.** "**Never opened by hand or by a helper:** `tmp/stage1-olmo/retrieved/` (the kit's pulled block
  trees, CHECK:187-191) and every plant-arm unit folder. Only reviewed code reads them, by key (first bullet)."

### D3. §40 adds a pilot-interval fallback that drops the frozen prompt part (E-40.md:46-47)

- **What is wrong.** "*Fallback:* the seed part only, with t(0.90, 2) = 1.886; *trigger:* per-prompt tables for
  Gate A's a0 units cannot be built (READY:358)." REV4:675 fixes the pilot interval as "the seed part (the pair's own
  paired variance, J = 3, 2 df) plus the prompt part" with Satterthwaite df (also W1R:291). The fallback changes a
  frozen gate, is not in the lead's ruling ("the pilot interval by B16's paired form"), is not marked "added"
  (E-40.md:15 says additions are marked), and is not labelled a deviation. CHECK did not adopt it.
- **Reproduction (M).** Input: a constructed synthetic pilot table (a0: 42 of 200 prompts fully Unsafe; a0_plant: 64
  other prompts fully Unsafe, the 42 Safe; a one-answer wobble that differs by seed). Command:
  `... venv/bin/python -B <scratch>/builds/verify-E-records/checks/pilot_fallback_case.py /Users/spiderishi/Coding/attribution`
  (B16's `contrast_paired` and `tdist`). Expected under REV4:675: "frozen form, seed + prompt part: Λ 11.3333 pp,
  SE 5.0987, df 198.48, lower bound 4.7772 -> stop". Actual under the fallback: "seed part only: SE 0.0962, df 2.00,
  lower bound 11.1519 -> go" (exit 0). Limit: in 400 random synthetic worlds (`pilot_fallback_search.py`) the two
  forms gave the same label every time; they differ when the plant has a strong prompt-specific part.
- **Correct text.** Delete the fallback and write: "No fallback. Gate A's a0 per-prompt tables are those the stage-1
  builder already reads through `REJUDGED_PINS["A"]` (RULES:171-183); if they cannot be built, the pilot is not read
  until they can." If the lead wants a fallback, it must read: "*Fallback (added; a post-W1 deviation from REV4:675,
  which fixes the seed part plus the prompt part; the paper labels it):* ...".

### D4. The S1 blinding record leaves out Gate B's §6 values that it should list as possibly read (E-S1-blinding.md:38-39)

- **What is wrong.** G5 lists σ̂ "from 23 Oct 05:26 UTC on, ... because it may have been seen then". G4 says only
  "FOCUS prints no §6 report value (E_HB, O, task loss)". The `--final` output `06a7020a…` holds every Gate B §6
  report (FOCUS:135: "every pre-registered §6 report and P5 is present"; FOCUS:137: the first missing report was
  "E_HB") and was written and kept with Gate B's outputs at 05:26 UTC (FOCUS:135; RULES:341-342 names the file).
  Under the record's own rule for σ̂, these values were available before rows 2-14 were written. This matters for row
  8: §37's R4 ("E_HB is the point estimate", ADD:642) was ruled on 29 Oct, after Gate B's E_HB values existed in that
  file. REV4:919 asks for "every Gate B value read before" each rule; the record must take a stated position.
- **Reproduction.** Input: E-S1-blinding.md:38 and :39 with FOCUS:135, :137. Expected: one rule for both. Actual: σ̂
  listed as possibly read; the §6 values, in a file written at the same minute, not listed.
- **Correct text (G4, last sentence).** "The output `06a7020a…` (kept with Gate B's outputs in
  `research/experiments/2026-10-16-gate-b-wave0-outputs/`) holds Gate B's §6 values (E_HB, O, task loss and the
  other §6 reports); FOCUS quotes none of them. They are listed as possibly read from 05:26 UTC on, as σ̂ is (G5)."
  In §4, rows 2-3 read "G0-G4 (G4's §6 values and G5 possibly)".

### D5. §39 adopts R1D's stop rules "as drafted", which contradicts D-5's "never stops the reading" (E-39.md:133-135)

- **What is wrong.** Point 8(d): "stop rules S1-S9 as drafted (R1D:718-738)". R1D's S1: "Any exit other than 0, or
  any `"pass": false`: the script stops; nothing after it runs" (R1D:720-721). D-5 point 8 (E-D5-D6.md:79-83): "It
  never stops the reading ... A refusal of the whole reader ... is logged, the reading's other steps stand." The plan
  update's step 4b says the same (E-plan-updates.md:144-145). The builder saw the conflict (build report, open point
  5) but the record text does not carry the exception, so the lead would commit two rules that disagree; under S1 a
  D-5 refusal would stop step 5 (LN-31's draw).
- **Reproduction.** Input: E-39.md:134, R1D:720-721, E-D5-D6.md:79-83. Expected: an exception for D-5's reader.
  Actual: none.
- **Correct text.** "(d) Pre-runs and stop rules. The no-value pre-runs R1a and R1b come before any outcome is
  printed (R1D:519-546); stop rules S1-S9 as drafted (R1D:718-738), with two changes: (i) S1 does not apply to D-5's
  reader (step 4b): its non-zero exit is logged, the script goes on, and the record prints D-5's fallback wording
  with the reason (D-5 point 8); (ii) the pre-run and step-2 checkers fail only on the identity lines of (a); the
  count lines are logged. From step 1 on, ..."

### D6. D-5's last fallback prints a false description of D-5 (E-D5-D6.md:106-109)

- **What is wrong.** "the reading record prints the design's wording in full (D1A:498-509 ...)". That paragraph says
  "The rule fixed before the reading for this case (D-5: such a prompt leaves only the prompt part of the contrasts
  whose arms lack a coherent answer on it) was not verified before the reading started, so by its pre-set fallback it
  was not used" (D1A:503-505). That is the design's drop rule, which the lead rejected (V1A §2; CRIT C1); the adopted
  D-5 drops no prompt (E-D5-D6.md:56-57), and the last fallback fires only after D-5 and (c+) both fail. The same
  paragraph also says "every label is re-read through Φ" for the G3 corners; B16 re-reads only the U-part words
  (V1A:102-105; B16/reading.py:287-301). D1A:511 itself says the first sentence must take the ruled G3a wording.
- **Reproduction.** Input: E-D5-D6.md:108 and D1A:498-511. Expected: a paragraph true of the adopted D-5. Actual:
  "in full", including the drop-rule description.
- **Correct text.** "... the reading record prints the design's option (c) paragraph (D1A:498-509) with these edits:
  '(D-5: such a prompt leaves only the prompt part of the contrasts whose arms lack a coherent answer on it)' becomes
  '(D-5: G2's pooled share per cell with a linearized prompt table on all 200 prompts, read beside B16; its fallback
  (c+): each arm's pooled coherent-only U)'; 'was not verified before the reading started, so by its pre-set fallback
  it was not used' becomes 'and its fallback (c+) were not verified by their pre-set triggers, so neither was used';
  'every label is re-read through Φ' becomes 'the U-part words are re-read through Φ'; and the unscored corner
  carries point 7's label (D1A:511). With the date and time of this record."

### D7. §39 point 6 reads REV4:302's "selector" as the best feasible repair (E-39.md:99-101)

- **What is wrong.** "REV4:302's 'infeasible for the selector' covers 'the best feasible repair' and the per-actor
  menus, because both name the repair to choose." REV4 uses "the selector" for §7's model-based selector: "The
  selector stays secondary and model-based" (REV4:79); "the selector screen (REQ-16)" (REV4:562); "## 7. The selector
  (model-based, D5 (a))" (REV4:611); "The selector is not run on new menus here" (REV4:614). No REV4 line ties
  coherence to the best feasible repair (M: the REV4 lines that hold "coheren" and one of "feasib", "selector",
  "best" are only :322 and :916; :302 sits in §3.7, the coherence section, and names only the selector). The ruling
  itself (adopt B16's behaviour) is the brief's; the stated basis is a misreading of a frozen text.
- **Reproduction.** Input: E-39.md:99-101 and REV4:79, :302, :410, :562, :611-614. Expected: the reading stated as a
  gap fill. Actual: presented as implied by REV4:302.
- **Correct text.** "*Ruling.* B16's behaviour is adopted as a stated reading that fills a gap. REV4:410's
  best-feasible rule names τ_O, τ_L and §4.9's separation, and no coherence condition. REV4:302 makes a failing arm
  infeasible for §7's model-based selector (REV4:562, :611-614), not for the headline's best feasible repair. B16
  applies the same exclusion to the best feasible repair and to the per-actor menus (B16/reading.py:449, :485);
  ADD:427 already ruled the per-actor best data arm 'better and feasible'. The headline word does not change
  (REV4:409). It is a post-W1 reading (S1 blinding record, row 1)."

### D8. §40 leaves a blinding gap at the plant-edit record (E-40.md:84 and :126-127)

- **What is wrong.** Point 5 uses "the kit's sealed edit record `{arm: "a0_plant", path, sha256}`" but says nowhere
  how the lead gets that path and SHA-256 without reading a file that names the leaf. The plant record holds the drawn
  unit and leaf (READY:48-50, from BP:442), and each plant edit file carries its title, "stage1 plant: planted corpus
  at k = {k} (leaf {cell})", as its own name field (`scripts/stage1/build_plant.py:284`, :307, code, M). CHECK's
  correction adds "A binding check. Confirm that REQ-8's record lists the planted_k37 file's SHA-256 ... Print
  'match' or 'no match' only" (CHECK:313-315; CHECK §6 item 1). §40 omits it. Point 10 also binds only "every
  helper", while CHECK's rule is "for the lead and every helper" (CHECK:155-156) and CHECK B3 says the lead must not
  learn the leaf before A1 on a0_plant is scored (CHECK:169-176).
- **Reproduction.** Input: `grep -n -i "binding check\|REQ-8\|plant_record\|match" E-40.md` (M: no hit) against
  CHECK:313-315. Expected: a ruled route. Actual: none.
- **Correct text.** Add to point 5: "The a0_plant edit record's path and SHA-256 come from hashing the planted_k37
  edit file at its known path; no byte of it is read or printed (its name field names the leaf). A reviewed key-only
  check confirms that REQ-8's record lists that SHA-256 for planted_k37 and prints only 'match' or 'no match', tested
  with sentinel strings (CHECK:313-315)." Point 10, last sentence: "The rule binds everyone, the lead included: no
  file whose path holds 'plant' or 'decoy' is opened, except code, until the counted outputs are hashed or a final
  'stop'; the plant record and the plant edit files name the unit and leaf (READY:48-50; build_plant.py:307)."

### D9. The D-5 record does not state its reading of G2's per-prompt rule (E-D5-D6.md:52-57, :94-97)

- **What is wrong.** The Facts quote G2's per-prompt rule (PREREG:148: per-prompt shares "serve only the per-prompt
  differences and the clustered SE"; a prompt with 0 coherent answers "is left out of that pair's differences"), and
  item 2 then drops no prompt. The record never says this departs from G2's per-prompt rule or why. The review the
  lead adopted requires it: "G2's count can still be printed per seed pair ... D-5 must state this reading"
  (V1A:227-229); its decision 6 lists "the reading of G2's per-prompt rule (§2.3 item 7)" in the D-5 record
  (V1A:364).
- **Reproduction.** Input: E-D5-D6.md:28-34 and :51-90 against V1A:227-229 and :364. Expected: a stated reading.
  Actual: none.
- **Correct text (new item 2b).** "**Reading of G2's per-prompt rule** (PREREG:148): G2's per-prompt shares and its
  pairwise drop of a prompt with no coherent answer served Gate B's clustered SE (GBR:457-470), which HB-C does not
  use. Under D-5 the prompt part is the linearized table, so no prompt is dropped; G2's count of such prompts is
  printed per seed pair, report only (V1A:227-229)."

---

## 2. Notes (minor; not defects)

1. **§40's edge rule goes beyond its source** (E-40.md:36-38). "Every comparison with 5 and 10 pp reads through B16's
   tie tolerance ..., as B16 reads δ (B16/README.md:153-155)". B16 reads only the estimate through the tolerance;
   "interval ends (irrational) do not" (README:154-155). The lower bound is an interval end. Correct text: "every
   comparison of Λ_plant (the point estimate) with 5 and 10 pp reads through B16's tie tolerance (1e-9 pp), as B16
   reads δ; the lower bound's comparison with 5 pp is exact, as B16 reads interval ends." The edge itself is real
   (M: `linearized_check.py`: per-seed differences move in steps of 1/6 pp and three-seed means in 1/18 pp; of 20,000
   synthetic paired means that equal 10 pp exactly, 6,317 compute below 10.0 in floating point).
2. **Row 12 against "Not listed"** (E-S1-blinding.md:63, :67-68). Row 12 lists "§39 points 3-10"; the paragraph says
   "§39 point 10" (the user's decision) is not listed; E-39.md:176-177 labels points 1-10. Make row 12 "points 3-9"
   and the S1 line "points 1-9", or list point 10 everywhere.
3. **σ̂'s earliest time** (E-S1-blinding.md:39). The first verdict file `030a7846…` (04:31 UTC, FOCUS:138) holds the
   same content as `bec5f103…` (FOCUS:135: "equal in content"); σ̂ was available from 04:31 UTC. No row changes.
4. **ADD §24 point 4** (ADD:508; 23 Oct 20:24 UTC) was an inference fallback written after W1 and withdrawn on 29 Oct
   (FOCUS:104). List it in the S1 record as "written, withdrawn".
5. **D-4's re-run "changed no label"** (E-misc.md:116; also :107). B16H:539 shows `docs_with_any_label_change: 1`
   (plan A, het); B16H:243 explains it is an S-start entry, not a label. ADD:605 records one synthetic block-A-only
   label change under D-4. Cite B16H:243 and ADD:605.
6. **"Φ's familywise error at most 5% in every configuration"** (E-misc.md:97-99). The "≤ 5%" is the z-level check
   against the review's generator (b16-verify-stats.json:352); end to end, plan B is 5.20% ± 0.70 (:358).
7. **F9's condition** (E-40.md:117). "and the user says yes" is not in REV4:710 or W1R:296 ("runs only if stage 1b is
   funded"). Correct text: "It runs only if stage 1b is funded (REV4:710; W1R:296); its $34-70 (E) is not in the
   balance, and the main sweep already waits for a top-up (point 11)."
8. **The $6 reserve's source** (E-40.md:131). ADD:635 says "covers that stage's cap-based spend"; the reserve is
   KW:8 (and ADD:657).
9. **K7's "Alternative"** (E-40.md:103-104) is CHECK's fallback (CHECK:350-352) and runs K7 before a "go", against
   the lead's ruling. Mark it "not adopted", or give it CHECK's trigger.
10. **Block C** (E-40.md:87). CHECK keeps `block_runs`' A, B **and C** paths byte-identical (CHECK:292-293).
11. **FR-25** (E-39.md:167). REV4:887 cites FR-25 and FR-21; FR-25 is the user's too (LEDGER:74).
12. **"The builder already refuses missing ... units"** (E-39.md:125). References have no required list (RI-O8,
    RIB:440-442): a missing reference is not refused, and family 1b ("beats every reference") gets easier. The lead
    may want the references line as an identity line rather than a count line.
13. **D-5's "verified" adds tolerances** (E-D5-D6.md:86-87: SE and df to 1e-6 relative; at least 20 synthetic
    readings) that V1A:361 and CRIT:345 do not state. Mark them as additions.
14. **Plan updates.** Item 7's "Verified" (E-plan-updates.md:104) omits the 0.75% tail criterion of D-5 point 9.
    Item 9's second-stamp list (:129-131) omits the records (§39, §40, D-5 to D-7, the S1 blinding record) that
    E-D5-D6.md:91-92 and E-S1-blinding.md:5-6 put inside that stamp. Row 1d (PLAN:33, "Re-run the reading-input and
    B16 test suites and mutation specs") is also stale: under D-5 B16's spec need not re-run (E-D5-D6.md:96-97), and
    the D-5 reader, B14 (D-6), kit round 34 and the D-7 script are missing.
15. **B14's pass, "add-arm outcome"** (E-misc.md:30-31). The brief's ruling says "before any outcome is read". And
    "not a deviation" does not address W1R:129, "B14 builds the strata at S1", with S1 = before block A (REV4:29).
    The S3 and S4 add sets did not exist until block A's diagnostics pod (R1B:69-74), so "at S1" can only mean the
    code; the record should say so.
16. **Kit round 34 changes the reading's rules file.** Round 34 must land in `runkit/stage1-olmo/` before the
    reading, and the reading loads that file (RI-O13; RI/__main__.py:27-28). E-misc should require blocks A and B's
    tables, `block_runs` and `REJUDGED_PINS` byte-identical (tested), and note that R1D's pinned kit-pair hashes
    (R1D:228-229) and the second stamp take the new hashes; otherwise R0 stops (no outcome shown, but a stamp cycle
    is lost).
17. **Quotes.** The brief asks to quote each stated reading. Points 7 and 8 of §39 paraphrase R1D and RI-O3 instead.
18. **R1D's own hard-rule breach** (R1D:823-829: one repository-wide grep pattern-searched the seven W1 sealed record
    files; names only; no match) is recorded nowhere. §40 point 10 records READY's; a complete §39 would record this
    one too.
19. **Scratch citations.** CRIT, V1A, D1A, R1B, R1D, READY and CHECK live in a temporary scratchpad. I agree with the
    builder's open point 9: commit copies or their SHA-256 values with the records.
20. **Construction-check inputs** (E-40.md:69-77). CHECK §6 item 3 adds "DataShield-style and L1 outputs on the Mac if
    they do not exist yet (READY:226-228)"; §40 does not.
21. **Row 9's "R2-R9"** (E-S1-blinding.md:60) overlaps row 8's R4 and R8.

---

## 3. The brief's items (a)-(h)

| Item | Result | Notes |
|---|---|---|
| (a) §39 | Covered: RI-O1, RI-O5 to RI-O14 (quotes match RIB:412-466), R2, R3, R5, R6, R7, R9 (quotes match RI/hb_claim.py:75-96), README:153-159 and overlap R2-R6 (README:79-84), B16-D4-O2/O3, B16-H-O9, the coherence condition, S-tok and §9.4, the runbook readings, the stamps, the keep-working instruction | D5, D7; notes 11, 12, 17 |
| (b) D-5, D-6 | Rulings match the brief: linearized table beside B16 (B16 unchanged), pooled U, G2's counts, words and headline word under its own Φ run, never stops, both adverse G3a corners; (c+) trigger "not verified after one fix round"; last fallback (c); D-6 settings-only, fallback `--no-overlap`, trigger "when the other builds are done"; both carry the S1 line and the paper label | D1, D6, D9; note 13 |
| (c) S1 blinding record | All brief rules listed, FOCUS renumbering correct (M: FOCUS:134 = funding event, :137 = `--final` refusal, :139 = wave 2 launch at `55d5f8b`) | D4; notes 2-4, 21 |
| (d) B14 gap and route | Matches: round 34 + one A100 pod; one-off pod; `--no-overlap`; Mac dropped (SIM:421-426; loaders.py:121-129; model.py:377-385) | notes 15, 16 |
| (e) LN-31 | D-7 recorded; HLC:164, :168 and REV4:762-763 quoted correctly | none |
| (f) ADD:428 | Correct: the only run is 22 Oct 22:07:04-23:02:02 Z on the pre-fix build (b16-verify-stats.json:5-6, :9; SHA-256 `65fe90c3…` M); the fix pass did not re-run it (b16-fix.json:269; SHA-256 `4090118e…` M) | notes 5, 6 |
| (g) §40 | Rulings present: go rule literal, sign, blinding, construction checks, kit round 35, K7 after a go, no judges, B16's paired form, disjoint anchors triggered, F9 not run, READY's breach recorded, money | D2, D3, D8; notes 1, 7-10, 20 |
| (h) plan updates | 13/13 "Old" blocks verbatim at `55d5f8b` (M); CRIT's six covered | note 14 |

## 4. §40 against the stage 1b check's corrections

| CHECK correction | §40 |
|---|---|
| B1: COMPLETE.json names the leaf; read by key; sentinel test | point 3, first bullet: yes |
| B2: counted score files under "plant", hashed and stamped before opening | point 3, third bullet: yes |
| B3: strike READY's "publish readable" fallback | point 4: yes |
| B4: record READY's breach | point 10: yes (MAN1:939-942, :1107-1110 checked, M) |
| B5: `retrieved/` on the never-open list | point 3: weakened by "until" (D2) |
| B6, B7: names; leak tests on stdout, stderr, refusals | point 3, fourth bullet: yes |
| 1.2 items 4-6: literal go rule, sign c − m, re-pilot seeds and comparator | point 1: yes (B16/contrast.py:168-173 checked) |
| §4: the pilot needs nothing sealed | point 12: yes |
| §5.1: one block P, kind "arm", sealed edit record, fingerprint record, tests | point 5: yes (block C, note 10) |
| §5.2 item 6: binding check of the planted_k37 SHA-256 | missing (D8) |
| §5.3: K7 new code (runner.py:870-872); RPR k = 75 change | points 6, 13: yes |
| §6 item 0: K7 after a go on its own pod; no judges for P; disjoint fallback | points 6-8: yes |

## 5. Citations I checked (opened at `55d5f8b` unless noted; all hold except as stated)

- **REV4:** 29, 79, 158, 264, 266, 270, 271, 275, 276, 285, 301, 302, 394, 398, 400, 409, 410, 428, 554, 555, 562,
  574, 611, 614, 665-713 (671, 675, 684, 698, 699, 706, 710), 719-721, 740, 743, 757, 762, 763, 874-887, 896-902, 919.
- **ADD:** 298, 299, 350, 351, 375, 407, 422-428, 435, 457, 470, 489, 501, 506, 508, 522, 600, 602, 604-608, 625, 633,
  635 (no reserve; note 8), 637-646.
- **FOCUS:** 74, 75, 76, 77, 99, 104, 107, 108, 109, 113, 125, 126, 131, 134-141, 144.
- **Others:** W1R:129, :288-297, :358 (record SHA-256 `275c7fe6…` M; REV4 `7eccf9e9…` M); LEDGER:70, :72, :74, :387;
  KW:3-13; HLC:3, :160-168; PLANS:172, :179; PREREG:148, :149; GBR:240-246; SPF:344; OTSC:1-60; RIB:5, :405-466;
  HBB:51-66, :186-192; B16H:212-240, :243, :457-567; B16/README.md:60-110, :137-170; B16/reading.py:280-320, :420-500,
  :530-537; B16/contrast.py:78-180; B16/settings/reading.json:198-202; RI/build.py:80-92, :600-610, :668-676;
  RI/__main__.py:20-140; RI/hb_claim.py:1-100; RI/items.py:1-12, :76-120; STR:1-70, :319-364, :481-494;
  STRS:25-57; LC:140-175; `scripts/stage1_s1/settings/oext_unit.json`:55-64; `oext_unit_y.json`:54-62;
  RULES:168-173, :336-342, :433-450, :500-512, :610-630; JR:894-901, :1037-1045; PT:788-796; runner.py:494-498,
  :868-873; edits.py:86-93; loaders.py:1-20, :118-130; model.py:375-386; SIM:418-428;
  `scripts/stage1_s1/tests/test_b14_report.py`:380-402; `scripts/stage1/settings/limits_check.json`:1-12 (role
  "settings" in MAN1, M; this verifies the builder's "not verified" point 10); MAN1:938-943, :1106-1111 (manifest
  SHA-256 `f6283090…` M); commit times of `2135c2d`, `7510c54`, `418aa27`, `8b2761d`, `8fe5fe9`, `8901eed`, `bc79b08`
  (M, `git log`); blame of B16/reading.py:427-433, :449, :485 (all `2135c2d`, M).
- **Scratch:** CRIT:1-397, V1A:1-402, D1A:230-275 and :490-512, R1B:40-300, R1D:28-48, :165-182, :215-232,
  :305-382, :462-482, :515-630, :660-740, :770-838, READY:40-80, :255-270, :350-396, CHECK:1-410 (all opened).
- **Bounds check (M):** `cite_bounds.py` parsed 313 short-name citations in the six drafts; 0 out of range (exit 0).

## 6. Sealed values

Nothing in the drafts states or depends on a stage-1 outcome or a sealed choice. The Gate B values in E-S1-blinding.md
(G1-G5) are readable FOCUS records (FOCUS:126, :135-:140). E-40 names the two "plant" settings files only by path,
line numbers and MAN1's SHA-256 prefixes, and quotes only the code's format string. D-6 rests on R1B's parse of
`plan.json` (readable kit record), which I did not repeat.

## 7. Commands and tests I ran (exit 0 unless noted)

- `date -u` (4 times); `git log`, `git status --short`, `git rev-parse`, `git diff --stat`, `git show 55d5f8b:<path>`,
  `git blame -L`, `git ls-tree --name-only`, `git grep` (code folders, "plant"/"decoy" excluded) in the main checkout.
- `shasum -a 256` on the drafts, PLAN (`121c5119…` = FOCUS:75), W1R, REV4, MAN1, the two B16 notes records and the
  S-G evidence files (all six prefixes match V1A:399-401).
- `/usr/bin/python3 -I -B`: `check_old_blocks.py` (13/13 verbatim), `cite_bounds.py` (313/0), MAN1 role printout.
  One `timeout` wrapper failed (exit 127, command not found on macOS); I re-ran without it.
- Targeted tests, `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=<fresh
  folder>` in the main checkout (synthetic data only; folder deleted after):
  - B16: `test_reading.py::test_coherence_flags_print_beside_the_word_and_never_change_it`;
    `test_fixes.py::test_a_coherence_failing_repair_never_dominates_in_family_1b`,
    `::test_an_exact_5_pp_tie_reads_better_whatever_the_float_rounding`, `::test_the_tie_tolerance_is_1e_9_pp_from_the_settings`,
    `::test_the_per_actor_feasibility_at_tau_o_2_and_10_reads_the_per_comparison_state`,
    `::test_better_holds_at_exactly_delta_minus_the_tie_tolerance`: **6 passed** (20.8 s).
  - `test_fixes.py::test_the_per_actor_best_data_arm_follows_the_menu_and_the_stated_tau`; builder
    `test_builder.py::test_plan_code_and_block_rules` (block-A-only refuses once B is sealed), `::test_bqi_own_a0_refuses`,
    `::test_rules_pins`; B14 `test_b14_report.py::test_unit_and_input_refusals` (all 17 cases, `recipe_s` among them);
    all of `test_hb_claim.py`: **84 passed** (28.6 s).
- Synthetic checks with B16's own functions (`builds/verify-E-records/checks/`): `linearized_check.py` (identities
  mean_p x = V, n = 0 → V, n = 3 → u/3 on 2,000 random cells; the hand case gives V_item 625 pp², SE 25 pp, the
  design's prompt part 0: PASS); `units_check.py` (D1); `pilot_fallback_case.py` and `pilot_fallback_search.py` (D3).

## 8. Not verified, and limits

- "In NOTES no other record names `sim_seed.py`, `sim_item.py` or `fwer_e2e.py`" (E-misc.md:105-106): I did not
  grep the lead's notes folder (I could not rule out that it holds something sealed). The two cited records match
  their SHA-256 values and lines.
- R1B's parse of `plan.json` (recipe S on all 55 arm and 5 a0_arm jobs) and the plant-rank report's lines cited from
  CHECK (RPR) were not reopened.
- `scripts/stage1/labels.json` "no `anchors.disjoint` key": not reopened; MAN1 gives it role "settings", so the
  builder's search did not touch a sealed record.
- The S1 blinding record cannot know what the lead read beyond FOCUS; D4 asks only for a consistent stated rule.

## 9. Replies to the builder's open points

1. Agreed (M). 2. Keep the added rows; add §24 point 4 as written and withdrawn (note 4). 3. Agreed. 4. The trigger
wording is fine; the (c) text is not (D6). 5. Agreed, and the record must carry it (D5). 6. Raise it, but restrict the
tolerance to the point estimate (note 1). 7. Agreed. 8. Agreed. 9. Agreed (note 19). 10. `limits_check.json:7` holds
(section 5). 11-12. Agreed.
