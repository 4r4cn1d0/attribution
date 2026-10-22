# Fix notes: the W1 freeze pass after its independent check

**Written** 2026-10-22 from 20:56 UTC (`date -u` at 20:56, 21:12 and 21:17 UTC) by a second worker for the main-study lead (GI VI), in the workspace `tmp/claude-workspaces/w1-freeze-20261022/`. Read-only everywhere else: no git command, no commit, pod, spend, download, install or agent. No `rows.jsonl`, `groups.json`, `selector.jsonl`, `hidden/`, held-out file, PHTest, anchor or lexicon text was opened.

**Input.** `check-report.json` (SHA-256 `3514de941349153ec28a65a0d165e6cc33cea5c69ea8054d483ca4c2c5f7e5cd`): verdict `fix_required`; one blocking finding, four should-fix findings, six notes. It checked `stage1-preregistration-rev4.md` at `4a754864…` and `req21-w1-record.md` at `e1c676c9…`.

**Sources re-read for the re-check** (the same files the brief names, unchanged): the addendum `stage1-commitments-build-20261016-lead-decisions.md` §11 point 13, §13 (all four points) and §14 point 2; FOCUS 22 Oct 13:24, 15:49, 17:23 and 17:31 UTC and 17 Oct 15:18 UTC; `lead-rulings-needed.md` §1 and the LN-09 row; the ledger's UW-20 and ADD-6.7 rows; the addendum §6 point 7. Every number below is copied from those sources or from the two files' own cited parts; the new sums are arithmetic on those parts, marked M (here).

**Outputs.** `stage1-preregistration-rev4.md` (now 1,277 lines; SHA-256 `7eccf9e9bed1e73307caec22e559b4c5fcc190b9f14c3557b4437874f935628c`), `req21-w1-record.md` (785 lines; `8681eb98d69e201c6fa50326d885885c5d3d7b096d0fdfb28ef4683fde54aeec`), `changelog.json` (34 new entries, each with `pass = "fix"`; the `fix_pass` block; outputs and marker counts updated), this file. Marker counts after the fix pass: rev 4 has 0 open markers and 0 FILL AT COMMIT; the record has 0 open markers and 14 FILL AT COMMIT, all in the exact form `[FILL AT COMMIT: what]`.

## Findings, one by one

### 1. Blocking: the block-A sum did not apply addendum §13 point 2 — APPLIED

- **Re-check.** Addendum §13 point 2: "Until the result exists, plans and cost estimates use Branch full." Rev 4 §10.5's summed row took its low end from Branch 128's O-ext share ($4–10) and included LN-14's $0.7, which §6.3 says runs only under Branch 128. The record's (d) rule 11 and Z.5 copied the same sum. The finding is real.
- **Fix.** The row is now "Block A, summed under Branch full". Parts, each from its cited source: the runs about $41 (§10.5); c0 about $1.2 (§10.3, 2,400 s × $1.79/h; see finding 2); the reused-unit regenerations and 500-bank passes about $3–6 (§6.3); block A's O-ext share about $15–26 (Branch full); LN-14 does not run under Branch full. Sum: 41 + 1.2 + 3 + 15 = 60.2 and 41 + 1.2 + 6 + 26 = 74.2, so **about $60–74 before LN-15e**; with LN-15e ($15–19 + $5.6–7.1): 80.8 and 100.3, so **about $81–100**. The Branch 128 figure is kept as a stated alternative: 41 + 0.4 + 3 + 0.7 + 4 = 49.1 and 41 + 1.2 + 6 + 0.7 + 10 = 58.9, so about $49–59, and about $70–85 with LN-15e. Written into rev 4 §10.5 (the summed row and the LN-14 row, now "Branch 128 only; $0 under Branch full"), the "Changes from revision 3" §10 row, record (d) rule 11 and record Z.5.
- **Where I differ from the check report's suggested figure.** The report proposed $59–74 with c0 at $0.4–1.2. Under LN-07 (adopted) c0 is the 500-prompt form, and under Branch full that form costs about $1.2; the $0.4 is the dev-100 c0 that LN-07 replaced. So the Branch full sum uses $1.2 and starts at $60. The $0.4–1.2 range is used only in the Branch 128 alternative, where the 128-cap c0 is UNVERIFIED (§7.3). The difference is $1 at the low end.

### 2. Should fix: §10.3 and §10.4 still used c0 = 2,300 s — APPLIED

- **Re-check.** Addendum §11 point 13: "The c0 estimate becomes about 2,400 s (E, the verifier's estimate), up from about 870 s." Rev 4 §7.3 and the §7 change row already said 2,400 s; §10.3 said "about $1.1 (E (here): 2,300 s × $1.79/h)" and §10.4 "if LN-07 adopts ... about 2.6×; 2,300 / 870". Real.
- **Fix.** §10.3: "about $1.2 (E (here): 2,400 s × $1.79/h; the 2,400 s is addendum §11 point 13's estimate)" (M: 2,400 / 3,600 × 1.79 = 1.19), plus one sentence that the c0 job is priced at this $1.2 under Branch full. §10.4: "Under LN-07's 500-prompt C-lean (adopted) the ratios fall by about 2.8× (E (here): 2,400 / 870)" (M: 2.76). The record's (d) rule 11 now says "c0 about $1.2 (2,400 s at $1.79/h; addendum §11 point 13)".

### 3. Should fix: both files said the batch fix revisions were verified by the lead — APPLIED

- **Re-check.** FOCUS 17:31 UTC: batches 3a and 3b verified with no blocking defect; "The builder applies both as revision 2"; 3a's fix changes the bytes and arm ids of 11 edit files; "Batch 2 rev 2's verifier returned no result, so a one-agent delta check runs again (wf_13654190)". FOCUS 17:23 UTC: batches 4–5 passed; their fix list is "now batch 4–5 revision 1 at the builder"; batch 8 revision 1 "is delivered (784 tests, 58 of 58 mutants killed) and waits for the lead's re-check". FOCUS 15:49 UTC: batch 8 verified (pass); "The batch 2 rev 2 critic passed". The files said "Verified by the lead ... batches 2 revision 2, 3a and 3b ... with their fixes as revision 2 ... and batch 8 with its revision 1", which overstates. Real.
- **Fix.** Rev 4 §0.4 and §10.6 step 3, record (g) "Not at HEAD" and Z.4 now say: batches 3a, 3b, 4–5 and 8 verified with no blocking defect; the fix revisions (3a and 3b revision 2; batch 4–5 revision 1) at the builder; batch 8 revision 1 delivered and waiting for the lead's re-check; batch 2 revision 2's critic passed but its verifier returned no result, so its delta check runs again (wf_13654190); all wait for the five regression suites and T1's two mutation specs on the final combined tree and the explicit-path commit.

### 4. Should fix: two lines of record item (m) fell outside the quoted text — APPLIED

- **Re-check.** `awk` over lines 544–612: line 566 ("- **Since the draft ...") and line 607 ("| The freeze pass's writer ...") had no "> " prefix; the draft had no such break. Real.
- **Fix.** Both lines now start with "> ". A re-scan of the (m) block finds no unprefixed line between the heading and the "**Ledger:**" line. While there, the M4 row names "the freeze pass's writer and its fix pass (22 Oct, 20:12 UTC on; the fix pass from 20:56 UTC)", since this pass read the same sources and no more.

### 5. Should fix: conditional text left on adopted or decided items — APPLIED

- **Re-check.** LN-09 (adopted; `lead-rulings-needed.md` row LN-09, addendum §10): the lead's W1 commit of the manifest and the record is the act that approves the W1 rules, so "If the lead does not accept this reading" leaves open a choice that the commit closes. UW-20 and addendum §6 point 7: F9's plant locations are conditional rule text that runs only if stage 1b is funded; addendum §14 point 2 flags `build_plant_extra*` conditional; so "only if adopted" is stale. Record M5 states, from the settings' 11 unit keys, that no Gate B unit is among W1-18's units; rev 4 §12.3 item (22) and record (e) rule 15 still had the conditional form. Real.
- **Fix.** Rev 4 §9.5 and record (h) reading 14: the sentence is replaced by "This reading is approved by the act of LN-09 ... so no later choice about it is open; a rule text approved only after a Gate B unit outcome carries §12.4's label" (the record's version points to reading 15, which is LN-09). Record (g) "Labels": "F9's `stage1-plant-extra-unit-v1` and `stage1-plant-extra-leaf-v1` (conditional rule text that runs only if stage 1b is funded; UW-20; addendum §6 point 7; the file is flagged conditional in the manifest, addendum §14 point 2)". Rev 4 §12.3 item (22) and record (e) rule 15: "no Gate B unit is among them (M5)".

### Note: the OSF deposit yes is dated 17 Oct in FOCUS, not 22 Oct — NO CHANGE NEEDED

The files cite FOCUS "USER DECISIONS, about 2026-10-17T19:11 UTC" (recorded 19:25 UTC), item 3, which is where FOCUS records the yes. FOCUS's 22 Oct entries hold no deposit entry. The brief's "22 Oct user yes" is not in FOCUS; if the user said yes again on 22 Oct, the lead records it in FOCUS and the files can then cite both. This pass invents no FOCUS entry.

### Note: placeholders outside the brief's three kinds — APPLIED IN PART

- **Re-check.** The record's 14 FILL AT COMMIT placeholders include the record's own `date -u` write time ((0); ADD L2 requires the real time) and the O-ext sealed record's path and SHA-256 ((e) rule 4 (iv); written by the lead's `build_oext.py` run, which has not run). Both exist only at the commit and are outside the three kinds the brief names. REV4's SHA-256 (Short names) changes again with this pass, so it stays a placeholder.
- **Fix.** Rev 4's header sentence (line 3) now names the two extra kinds and says the lead accepts them at the commit or folds them into the manifest's entries. The placeholders themselves are unchanged (14, all in the exact form). **For the lead:** accept these two kinds, or tell the freeze workspace to reword (0) as "written at the commit's `date -u` time" and (e) rule 4 (iv) as "the manifest's entry for the O-ext sealed record".

### Note: small factual imprecisions in the blinding and W1-18 text — APPLIED

- **Re-check.** (1) FOCUS 17:23 UTC gives the real-data read (the six units' `COMPLETE.json` and `job.json` hashes, the sealed MANIFEST, the A1 records) to the batch 4–5 verification, wf_a55942ca, only. (2) FOCUS 13:24 UTC: the first two 22 Oct runs (from 12:42 and 12:55 UTC) were stopped by a swap guard; only the third (13:08–13:23 UTC) ended in non-finite logits. (3) FOCUS 17 Oct 15:18 UTC: "The first run on MPS stopped on non-finite logits". All real; none changes the blinding conclusion (no flag was read in any run).
- **Fix.** Record M4's lead row credits wf_a55942ca only and says that FOCUS records no real-data read by the other three workflows (with what they did). Record (e) rule 5, the "Open for the lead" line, M2's W1-18 bullet, rev 4 §0.4 and §12.2 now name which run ended in non-finite logits and add the 17 Oct MPS run. M2's "Since the draft" window and rev 4 §12.2's window now start at 17 Oct 15:18 UTC, the entry that holds the MPS run, so they match M4's lead-row window (note 9 item (f)).

### Note: fallbacks with a live trigger are marked "not adopted" — REJECTED

Rev 4's mark definition (Short names, the LN-n entry) already says "Each pre-set fallback stays as the fallback with its trigger", and §0.3 item 3 repeats "the pre-set fallback stays with its trigger". "Pre-set fallback (not adopted)" therefore reads, by the document's own definition, as "not the primary; kept with its trigger". Rewording 65 places (36 in rev 4, 29 in the record) adds no information and risks a slip in a frozen text. If the lead prefers the longer form, it is a mechanical edit for the next pass.

### Note: minor wording and consistency items — APPLIED

(a) "DRAFT revision 4" is now "revision 4" in the record (lines 10, 58, 593, 631, 670); rev 4's title is "revision 4: the frozen W1 text". (b) Record (d) rule 11 cites revision 4 §10.5. (c) Rev 4's HB-4 line: "It is cut first if money is short (§10.5's cut order; I: RB)". (d) Record Z.3 LN-32: "Adopted in item (i) rule 4 (addendum §10)". (e) Rev 4's header now says "no decided number except where a cited ruling gives one ...; values copied from the settings files or FOCUS are marked R or M, and the sums made here from cited parts are marked E (here)". The 0.82 FRE in §7.3 is marked "M (here): 2,400 / 2,934"; the M is for the arithmetic and the inputs are E, which the sentence shows, so it is left as written. (f) The windows: see the previous note. (g) The record's "Note for the lead" about LLB is now a stated limit ("Limit of this list"), with the check assigned to a reader listed in item (m) and recorded in FOCUS.

### Note: some changelog entries do not show the final text — REJECTED (no change to earlier entries)

The freeze pass's 277 entries are left as written; merging them would rewrite another writer's record of its own edits. The fix pass adds 34 entries of its own, each with `pass = "fix"`, the old text as it stood after the freeze pass, the new text and the source. `changelog.json` also carries a `fix_pass` block (inputs, findings applied and rejected, the numbers changed with their arithmetic), `outputs_before_fix_pass`, the new output hashes, the new marker counts and the re-located placeholder lines.

## What did not change

No scientific target, model, threshold, test level or analysis. No frozen Gate B/C rule, sealed record, D5 = (a) or user decision. The only numbers that changed are the two c0 figures (to addendum §11 point 13's 2,400 s) and the block-A sums (recomputed from the same cited parts under the branch that addendum §13 point 2 prescribes). The 14 FILL AT COMMIT placeholders are unchanged in text and count.

## Unresolved for the lead

1. Accept or reword the two extra placeholder kinds (the record's write time; the O-ext sealed record's path and hash).
2. If the user's 22 Oct yes to the OSF deposit is to be cited, record it in FOCUS first.
3. REV4's SHA-256 in the record's Short names is written at the commit, after the last edit of rev 4.
