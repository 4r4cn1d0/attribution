# Consistency review of the stage-1 pre-registration merge (DRAFT revision 1)

**Status.** A read-only review for the main-study lead (General Implementation VI). It adopts nothing. It authorizes no run, spend, download, commit or pod. It changes no file except this one.

- **Written** 2026-10-17 from 00:55 to 01:18 UTC by an Opus worker. Clock checked with `date -u` at 00:55, 01:00, 01:05, 01:15 and 01:18 UTC. HEAD was still `5957a37` at 01:18 UTC.
- **Reviewed (this folder).** **DRAFT** = `stage1-preregistration-DRAFT.md` (926 lines; R: `wc -l`). **CONS** = `stage1-decisions-consolidated.md` (1,174 lines). **EXTR** = `w1-builder-extract.md` (475 lines) with `w1_extract_numbers.py` and `.out`.
- **Checked against (main checkout, read-only).** FOCUS, PLAN-S, PREREG revision 5, BRIEF revision 1, ADD §1–§5, and named parts of REF, RV, AMD, VR-B, RB, VR-C, PAPER and ENG-Y. Short names are DRAFT's.
- **Data rules kept.** I opened no `selector.jsonl`, no `hidden/`, no held-out file, no wave-0b `rows.jsonl` or `groups.json`, no W0 file and no check note (CK-*). I did not open the Llama Gate B-lite note (LLB), so that I do not become a reader of the values in RC-03. This file holds no row, prompt, answer, anchor or lexicon text.
- **Gate B values that I saw** (for REQ-21 (m)): every value in DRAFT §12.1 (r_j, SD(r), σ̂_gate, the P(LOCALIZED) lookup, the re-costing figures, the rankings as orders, the picks, the ρ values, the a0 and R_1–R_3 U values, the Gate A over-refusal counts); FOCUS's re-costing sentence in the 16 Oct 13:21 UTC entry; VR-B's HB-C MDE line. I saw no Gate B arm's O, task loss, ARC, answer or score.
- **Source change during the review.** At 01:05 UTC HEAD moved from `3db753e` to `5957a37` (R: `git log`). That commit adds one FOCUS line (a backup entry) at line 74 and changes no other cited source (R: `git diff --stat`). FOCUS's SHA-256 is now `1587b549813792e1` (R: `shasum`). See RC-29.

**Labels.** R = read in a source (named). M = computed (by a named source, or "here" for this file's arithmetic). E = an estimate (basis named). I = inference or judgement. Every severity is I.

**Severity.**
- **Major** = the files could change or weaken a user decision, a frozen rule or D5 = (a), or the blinding record is false, or the three files disagree on a consequential rule.
- **Minor** = a deadline, mark, count, cost or rule text disagrees between files or inside one file, and could mislead the lead or the builder.
- **Nit** = wording, labels or pointers.

---

## 0. Result

**Counts (M: here).** 35 findings: **6 Major**, **22 Minor**, **7 Nit**. DRAFT is touched by 30 findings, CONS by 20, EXTR by 20 (M: here; one finding can touch more than one file).

**Short answer.**
1. No file changes a frozen Gate B/C rule, a sealed ranking or D5 = (a) in substance. One DRAFT sentence on Gate C reads like an addition to frozen Gate C (RC-24).
2. DRAFT and EXTR weaken two user decisions: the lead may reclassify the paired model as [LEAD] (RC-01), and a coherence failure gets the user's "worse" label (RC-02). CONS is right on both points (with one wording fix).
3. The blinding record in DRAFT and EXTR is incomplete. CONS reports that some writers saw the wave-0a R arms' task-loss differences and answers-end counts. Two open rules (the τ_L comparator and the coherence bar) depend on such values (RC-03).
4. EXTR and CONS carry an over-refusal "binding" sentence that uses the seed-only SE, but all three files recommend "prompts random" for O (RC-04).
5. CONS puts O-ext H, which reverses a user rule, at the top of a USER-CONFIRM ladder (RC-05).
6. DRAFT omits three open user rulings that ENG-Y records: certification pods before a funding event, a late B+Qi engine change, and what the confirmation units read (RC-06).
7. Seeds, arms, cell counts, df, costs and money agree inside DRAFT and with the sources, except the points in RC-07 to RC-10, RC-16 and RC-22 (§3 lists the checks that passed).

---

## 1. Findings

File keys in the "Fix" lines: **DRAFT**, **CONS**, **EXTR**. "No change" means that file is already right.

### Major

**RC-01. The paired model HB: the lead may reclassify a user item as [LEAD].** (DRAFT, EXTR)
- **Where.** DRAFT §3.3 "Why [USER] here", last sentence; FC-2 ("The lead may instead reclassify this as [LEAD] (§3.3)"); Appendix A C-1 ("the lead may reclassify (§3.3)"). EXTR §6.3 item 4, first bullet ("The lead first classifies the change"); EXTR §8 row 1 ("the lead classifies").
- **Problem.** PLAN-S:102 says "Seeds are not paired (correlation −0.08; R: GBD §2)" (R: PLAN-S:102). The user approved PLAN-S "as drafted as the basis for its pre-registration" (R: FOCUS "Amendment … ADOPTED … the sharpened direction", 8 Oct 13:53 UTC). DRAFT's own merge rule says a proposal that would change a user decision "stays a [USER] item" (R: DRAFT §0.3 rule 3), and so does the merge brief. A reclassification by the lead would replace user-approved text without the user. CONS UW-02 marks it USER, with no reclassification route. So the three files disagree.
- **Fix DRAFT.** In §3.3 delete "The lead may reclassify this item as [LEAD] by recording that reading in the W1 FOCUS entry; then HB is the lead's recommended choice, shown to the user in the W1 record." In FC-2 delete "The lead may instead reclassify this as [LEAD] (§3.3)." In C-1 replace "the lead may reclassify (§3.3)" by "S-a stays in force until the user decides". Keep "(AMD: [LEAD])" as the other source's mark.
- **Fix EXTR.** §6.3 item 4, first bullet: replace "The lead first classifies the change. If the lead treats it as a user item and the user is silent," by "It is a [USER] item (DRAFT FC-2; CONS UW-02). If the user is silent,". §8 row 1, "Who decides": "the user (FC-2); HB or HB-C goes to GPT only if the user adopts pairing".
- **Fix CONS.** No change.

**RC-02. A coherence failure gets the user's "worse" label.** (DRAFT, EXTR; CONS differs)
- **Where.** DRAFT §3.7 items 3 and 4; §4.5 headline table step 1 ("or the coherence rule fires"); §11 "Coherence"; Appendix A C-18. EXTR §6.1 item 5. CONS LW-09.
- **Problem.** The user's rule: "a repair whose contrast against its comparator is significantly harmful at the 5% Holm level (on unsafe share, over-refusal or task loss, each in its harmful direction) is labelled *worse*" and "Labels are now better, equivalent, worse and inconclusive" (R: FOCUS "Decisions … 'do what is recommended and start runpod'", 8 Oct 18:31 UTC). A coherence failure is not a significant contrast. So DRAFT §3.7 item 3 (from AMD §F item 3, marked [LEAD] there) adds a new trigger to a user label. DRAFT §3.7 item 4 also replaces a tested label by "inconclusive" when the comparator fails. CONS LW-09 keeps "worse" out and makes a coherence "worse" a USER question. But CONS's replacement word "fails answers end" is a fifth headline word, which is also outside the user's four labels (I).
- **Fix DRAFT.**
  - §3.7 item 3: "A failing repair keeps the label that its tests give. Its headline word carries the flag 'fails answers end'. The text never calls it better or equivalent without the flag. **[USER] proposal (AMD §F item 3):** label it 'worse (answers do not end)'. Silent: the flag rule."
  - §3.7 item 4: "A failing comparator adds the flag 'comparator fails answers end' to each contrast that uses it. The tested label stays. **[USER] proposal (AMD §F item 4):** read those contrasts 'inconclusive'. Silent: the flag rule."
  - §4.5 step 1: delete "or the coherence rule fires". Add a last row: "— | the coherence rule fires (§3.7) | the flag beside the word; it never changes the word".
  - FC-5: add "(c) AMD §F items 3–4 (coherence 'worse'; comparator 'inconclusive'). Silent: flags only." C-18: add "the label part of AMD §F stays a [USER] proposal (FC-5 (c))".
- **Fix EXTR.** §6.1 item 5: use DRAFT's new §3.7 items 3–4 text.
- **Fix CONS.** LW-09: "the tested label stays; a failing repair or comparator gets the flag 'fails answers end' beside the word (not a fifth label); 'worse' or 'inconclusive' for coherence joins UW-05 as a USER question".

**RC-03. The blinding record omits readers of the wave-0a R arms' task-loss differences and answers-end counts.** (DRAFT, EXTR)
- **Where.** DRAFT §6.6 LQ40 ("REF, RV, AMD and RB read none; this merge read none"); §12.1 last bullet ("Not read by any writer … any Gate B arm's O, task loss …"); §12.2; §12.3. EXTR §6.2 item 9; §6.4 item 3; §10 item 6 ("No R arm's task loss has been read, so nothing fixes the size yet").
- **Evidence.** CONS LW-07: "The Llama note's authors saw the OLMo R arms' task-loss differences over the same-seed a0 (LLB §15 item 8), and I read that line." CONS LW-08 item 6: "The OLMo R arms' answers-end counts and task-loss differences, used by the Llama note (LLB §14), and seen by me (task-loss differences only)". CONS §10 and its limit 3 say the same (R: CONS). I did not open LLB; this finding rests on CONS (I).
- **Why it matters.** Two rules are still open: the τ_L comparator (LQ38; DRAFT §6.6, "to GPT") and the arm-pooled coherence bar (DRAFT §3.7). REF LQ40 asks who saw any Gate B or stage-1 arm's task loss before LQ38 and LQ39 are fixed (R: REF §L.4 LQ40). DRAFT answers "none", and EXTR says no R arm's task loss was read. Both statements are false if the LLB authors and the CONS writer count as writers of W1 inputs (I: they do; CONS is a W1 input to the lead).
- **Fix DRAFT.**
  - §6.6 LQ40: append "Exception: the authors of the Llama Gate B-lite note (`research/review/2026-10-17-stage2-design-notes/llama-gate-b-lite-rules.md`) used the wave-0a R arms' task-loss differences over the same-seed a0 and their answers-end counts; the CONS writer read the task-loss differences (R: CONS LW-07, LW-08 item 6). This file does not repeat them."
  - §12.1: add one bullet with that fact.
  - §12.2: add three rows: "LLB authors | the wave-0a R arms' task-loss differences and answers-end counts | — | no statement"; "CONS writer | FOCUS 16 Oct entries; the R arms' task-loss differences | through the drafts | no"; "this review | DRAFT §12.1's values; FOCUS's re-costing sentence | through DRAFT | no".
  - §12.3: add "(9) The τ_L comparator (LQ38) and the coherence bar (§3.7) are fixed after some writers saw the wave-0a R arms' task-loss differences, and the LLB authors also saw their answers-end counts."
  - §13.2 "To GPT" row: add "with RC-03's disclosure".
- **Fix EXTR.** §6.2 item 9: replace "No draft writer read any Gate B arm's task loss" by "No writer of Drafts A, B or C read any Gate B arm's task loss; the LLB authors and the CONS writer did (CONS LW-07)". §10 item 6: replace the last sentence by "Some writers saw the wave-0a R arms' task-loss differences (CONS LW-07), so the size of this sensitivity must not come from them." §6.4 item 3: add the LLB and CONS rows.
- **Fix CONS.** No change.

**RC-04. The over-refusal "binding" sentence uses the seed-only SE, against the error model that all three files recommend.** (EXTR, CONS)
- **Where.** EXTR §6.2 item 4; EXTR `w1_extract_numbers.py` (bound offsets); CONS LW-06, "Correction applied (A-RV R3)". DRAFT §6.2, "Where τ_O binds".
- **Problem.** EXTR writes "Under the bound it binds about 2–2.5 pp lower (1.96 pp for a one-sided 90% bound, 2.52 pp for a one-sided 95% bound …). An arm at θ0's level is at the edge of τ_O = 2" (R: EXTR §6.2 item 4; M: EXTR script, 1.2816 × 1.53 and 1.6449 × 1.53). CONS LW-06 says "about 2 pp lower" (R). Both use RV R3's seed-only SE floor of 1.53 pp (R: RV R3). But all three files recommend "prompts random" for O (R: DRAFT §6.4; CONS LW-03; EXTR W1-13 row 2 and W1-16 item 4). Under that model the prompt-clustered SE at 100 prompts is 4.0–4.2 pp (M: CK-OR §4, via RB and DRAFT §6.2). The upper end of the two-sided 90% interval then adds 6.6–6.9 pp (M here: 1.645 × 4.0 = 6.58; 1.645 × 4.2 = 6.91). An arm at θ0's level then reads "undetermined" at τ_O = 2 and 5 on 100 prompts (I: DRAFT §6.2). If the W1 record carries EXTR's sentence, REQ-21 (e) contradicts REQ-16's and REQ-19's decider.
- **Fix EXTR and CONS.** Replace the sentence by DRAFT §6.2's text: "On the point estimate τ_O binds only above 19, 22 or 27 of 100 (M: 17 + τ). With a seed-only SE (at least 1.53 pp; R: RV R3) the bound adds about 2.0–2.5 pp (M: RV; EXTR script). Under the prompts-random model in force for O (SE 4.0–4.2 pp at 100 prompts; M: CK-OR §4), the upper end of the two-sided 90% interval adds about 6.6–6.9 pp (M), so an arm at θ0's level is 'undetermined' at τ_O = 2 and 5 on 100 prompts." EXTR script: add the two prompts-random offsets.
- **Fix DRAFT.** No change.

**RC-05. O-ext H is the top of a USER-CONFIRM ladder, although it reverses a user rule.** (CONS; DRAFT wording)
- **Where.** CONS UW-07 ("Recommended default (ambitious; rests on UW-01). H, then N, then F"; "Decides: USER-CONFIRM (H and N need the user in any case)"). DRAFT §6.5 ladder bullet and FC-7 ("Ladder default: 500 prompts primary").
- **Problem.** H is a draw from the hidden over-refusal remainder. The user's rule: "then from a new public source (a download the user approves), never from the hidden remainder" (R: FOCUS 8 Oct 13:53 UTC, "Over-refusal and skill"; PLAN-S:197). A proposal that reverses it stays [USER], with the rule in force (merge brief; DRAFT §0.3 rule 3). DRAFT (FC-7 (b), §6.5, C-9) and EXTR (W1-19) do this. CONS does not: it keeps H as the ambitious default of a USER-CONFIRM item, and its own reason ("H and N need the user in any case") says the item is USER. DRAFT's ladder default "500 prompts (dev 100 + 400 O-ext)" does not say that the 400 can only come from N while H is not allowed.
- **Fix CONS.** Split UW-07. **UW-07a (USER; ladder USER-CONFIRM):** N (400 PHTest rows, a download the user approves) as the ambitious default; F as the fallback; F if silent at the W1 commit. **UW-07b (USER):** change the 8 Oct rule to allow H; no recommended default; silent: H is not allowed. Update the index and the §0 counts.
- **Fix DRAFT.** §6.5 ladder bullet and FC-7: "the ambitious default is 500 prompts (dev 100 + 400 from N); H only if the user says yes to FC-7 (b)".
- **Fix EXTR.** W1-14 item 5 and W1-16 item 6: write "500 prompts via N" where they say "500".

**RC-06. Three open user rulings from ENG-Y are missing from DRAFT.** (DRAFT)
- **Where.** DRAFT §1.5 (LQ19, LQ20), §4.7, §10.4 "B+Qi certificate pod" row, §14.2. CONS US-08, US-09 and US-18 have them.
- **Evidence (R: ENG-Y decisions).** Decision 14: "Certification pods before a funding event (about $3–4 at 1B): the user's open ruling (PLANF:234 item 14)". Decision 1: "If even X′ cannot be ready for 3 Nov: whether to amend F:225 to 'B+Qi committed before block B' (the user's call)". Decision 5: whether the confirmation units read both banks; "This changes an adopted design point (F:252), so it is the user's call".
- **Problem.** DRAFT marks LQ20 [LEAD] and prices the certificate pod at $2.7–2.8 (M: RV) without the open user ruling on its timing against a funding event. The balance slack before wave 1 is $8.03 (M: RB; R: FOCUS 16 Oct 13:21 and 19:08 UTC). DRAFT uses ENG-Y for §1.5 and §13.3 but drops these three user items. The stage-1 freeze has 0–4 days of slack before block A (R: RB R4.1, citing ENG-Y §0), so a late X′ is a real case.
- **Fix DRAFT.** Add to §14.2:
  - "**FC-33 [USER].** May the X → X′ (or Y) certification pod run before stage 1's funding event (ENG-Y decision 14; CONS US-08)? Silent: no; it waits for FC-19's funding event. Cost $1.3–1.5, or $2.7–2.8 with LQ20 (M: RV); ENG-Y's C1–C3 pod about $3.0–3.7 (E: ENG-Y §0)."
  - "**FC-34 [USER].** Only if X′ cannot be certified before block A: amend the 8 Oct 17:36 UTC item (4) text ('committed before stage 1 is frozen') to 'committed before block B' (ENG-Y decision 1; CONS US-18)? Silent: no amendment; the stage-1 freeze waits."
  - "**FC-35 [USER].** What the confirmation units read (ENG-Y decision 5; CONS US-09). In force: the hidden subsample and the dev bank (FOCUS 8 Oct 13:53 UTC, 'Confirmation'). Silent: both banks."
  - In §1.5 LQ20 add "(its timing against a funding event: FC-33)". In §4.7 add "(what the units read: FC-35)".

### Minor

**RC-07. Plan-B seed lists: gaps in all three files.**
- **Where.** DRAFT §1.3 plan-B lists, FC-3, Appendix C G-2. EXTR G-1 ("optional"). CONS: no item.
- **Problem.** (1) DRAFT's plan-B R list is 1101–1112 (I: DRAFT). That needs R draws d = 9–12, but REQ-4 and L13 (4) cover d = 6–8 only (R: BRIEF REQ-4; ADD L13 (4)). (2) AMD's D1 also changes plan B: "plan-B R 1101–1110" (R: AMD §H A4). DRAFT FC-3 and §1.3 omit this; CONS UW-03 has it. (3) a0's role under plan B is not stated (I). (4) FOCUS requires "the seed rule" before wave 1 (R: FOCUS 8 Oct 13:53 UTC, "Gate B and Gate C stay exactly as pre-registered"; PLAN-S:211), but CONS has no item for the plan-B lists.
- **Fix DRAFT.** §1.3: "Plan-B seed lists [LEAD] W1 (I): A1 and H1 1102–1110; S1 and S4 1102–1110; R 1101–1112, draws d = 9–12 by the same frozen rule as d = 6–8 (`gate-b-random-removal-v1`, draw d at seed 1100 + d), named in REQ-21 (d); a0 stays 1101–1106 for G_m and the references (I). Under D1 (FC-3): R 1101–1110 (AMD A4)." FC-3: add "Under plan B, D1 also sets R to 1101–1110 (AMD A4)."
- **Fix EXTR.** G-1: "The seed list is a W1 item (REQ-21 (d)). Building the d = 9–12 files at W1 is optional."
- **Fix CONS.** Add "LW-31. Plan-B seed lists" (LEAD, W1) with DRAFT's list, and update §0.

**RC-08. FRE and the lean prices are "fixed at D3", but tagged W1-P.**
- **Where.** DRAFT §10.2 LQ25 ("Fixed at D3 and never re-estimated"), §10.3 LQ28 ("frozen at D3"), §10.6 step 5 (D3 after `--final`), §7.3. CONS LW-16 (LQ25 "fixed at D3", W1-P). EXTR W1-15 item 2.
- **Problem.** All three tag LQ25, LQ26 and LQ28 W1-P (R: RV N1). W1-P is before REQ-18's predictions freeze, which is before wave 1 (R: DRAFT "Deadlines"). D3 is "before stage 1" (R: PLAN-S:212), and DRAFT §10.6 puts it after Gate B's `--final`. A unit fixed at D3 could move after the predictions that use it are frozen.
- **Fix (all three).** "1 FRE = 2,934 s and the lean per-answer prices are fixed at the W1-P commit from the three wave-0a ledgers, and never re-estimated. D3 freezes the other cost rules (LQ30, LQ32–LQ35) and does not change FRE or the prices." DRAFT §10.6 step 5: add the same sentence.

**RC-09. LQ27 (a) changes PLAN-S:202's C-lean contents without a caveat.**
- **Where.** DRAFT §7.3 LQ27, §10.3 "C-lean". EXTR W1-14 item 7, W1-15 item 2 (default (a)). CONS LW-15 has the caveat.
- **Problem.** PLAN-S:202 defines C-lean as "training plus 200 harm prompts × 1 sample" (R). LQ27 (a) adds the task-loss pass and 100 greedy over-refusal answers, and c0 moves from about 480 s to about 870 s (E: REF §C.5). It also closes a real gap, because PLAN-S:127's screen needs O and L (R). CONS: "(a) adds to PLAN-S:202's wording but does not contradict it. If the lead reads it as a change to the approved plan, it becomes a USER item." DRAFT and EXTR have no such sentence.
- **Fix DRAFT and EXTR.** Add CONS's sentence and "REQ-21 (h) records (a) as the reading that closes the gap between PLAN-S:127 and PLAN-S:202. Mark: [LEAD] as a reading; [USER] if the lead reads it as a change, with (b) in force."

**RC-10. Contingency: 1.25 in the rules, 15% in the total.** (DRAFT)
- **Where.** DRAFT §10.1 ("contingency 1.25 (R: … 9 Oct 19:37 UTC item (3))"); §10.5 row 3 ("15% contingency … $56–98").
- **Problem.** Item (3) sets 1.25 for Gate B: "Contingency factor 1.25 (was 1.15 [D11]) … the wave-1 need becomes about $78.45" (R: FOCUS 9 Oct 19:37 UTC). PLAN-S's stage-1 total uses 15% (R: PLAN-S:230). DRAFT's reference costs use × 1.25 (R: DRAFT §10.4). So DRAFT mixes two factors and cites a Gate B rule as a stage-1 rule.
- **Fix DRAFT.** §10.1: "Contingency 1.25 is Gate B's factor (item (3)); this file applies it to its new stage-1 cost lines as a [LEAD] reading." §10.5 row 3: "… with 15% contingency (E: PLAN-S §10); about $61–107 at 1.25 (M here: × 1.25/1.15 gives $60.9–106.5)".

**RC-11. Deadlines differ between the files.**
- **(a) FC-19 (the funding event).** DRAFT lists it under §14.1 (W1), with the deadline "Before block A". CONS US-07 is S1. Fix DRAFT: move FC-19 to §14.2.
- **(b) FC-15 (SR, S6), FC-16 (in-domain refusal), FC-20 (HB-4).** DRAFT lists them under §14.1. RB marks U-6 "rules W1; code S1", U-4 "rule W1; run S1" and U-9 "S1" (R: RB §2). The user's yes is due before any newly run stage-1 cell's outcome is read (R: RB R0.1). CONS US-10, US-12 and US-15 are S1. Fix DRAFT: move the three items to §14.2, each with "rule text: the lead's, W1 (R0.1)". Keep one W1 note: CONS US-10 option (b) (SR and S6 inside the primary family) would need the user by W1, and it is [USER] because it changes D5 = (a)'s "Holm over 6".
- **(c) F9 (two more plant locations).** CONS LA-11 is "later". AMD: "W1 (rule); funding later" (R: AMD §H G2). DRAFT FC-13: "Rule W1". EXTR W1-10: "W1, or exploratory". Fix CONS: move LA-11 to §1 as a W1 item (conditional rule text), with funding at the stage-1b event.
- **(d) REPLAN option B.** CONS LA-09 is "later (the 20 Nov gate)". Option B makes "OLMo-1B's stage 1 as development" (R: PAPER decision 28). Block A's latest start is 3 Nov (E: REPLAN §5). An answer on 20 Nov could reclassify a pre-registered primary family after stage-1 outcomes exist. DRAFT FC-18 is W1, silent "confirmatory". Fix CONS: split LA-09. The part that sets OLMo-1B stage 1's status is due at W1 (REQ-21 (a)), and at the latest at S1; silent: confirmatory. The 7–8B scope part stays later.

**RC-12. Marks differ.**
- CONS gives one class, USER-CONFIRM, to items that RB marks "[USER]; ladder (or package, or scope) [USER-CONFIRM]": UW-07, US-10, US-11, US-12, US-14 and US-15 (R: RB §2). DRAFT keeps RB's double mark. Each needs money or a download, so the user decides in any case (R: DRAFT "Marks"; CONS "Who decides").
- CONS UW-16 (F10, a benign-topic plant) is USER-CONFIRM. DRAFT FC-12 and EXTR §7 mark it [USER], because it widens a scientific target (R: AMD §H G3, "[USER] (target)").
- CONS US-10 option (b) changes D5 = (a)'s "Holm over 6" (R: FOCUS "D5 DECIDED: (a)", 16 Oct 12:15 UTC), so that option is [USER].
- EXTR §6.5 row (a) marks F1's headline wording [USER-CONFIRM]; EXTR §6.3 item 5 and DRAFT FC-11 mark it [USER].
- **Fix.** CONS: write "USER (ladder USER-CONFIRM)" for the six items, USER for UW-16, and mark US-10 (b) USER; recount §0 and UW-01's "12 items". EXTR §6.5 (a): "[USER]".

**RC-13. Which BRIEF questions the lead may close is different in each file.**
- DRAFT FC-9: the lead may close U4, U5, U6 and U9 by recording a reading (the D5 precedent).
- CONS: UW-08 (U4, order) and UW-09 (U6) may be closed this way; UW-04 (U4, family part) is USER; UW-10 (U5) and UW-12 (U9) name no such route.
- EXTR §6.1 item 6: only LQ42–LQ44.
- **Fix (one text for all three).** "The lead may close U4 (the label order and the O and L Holm families, not Φ), U5 (keep, the approved default), U6 and U9 by recording in the W1 FOCUS entry that the 16 Oct instruction covers them, as the D5 entry did for U2 and U3 (R: FOCUS 'D5 DECIDED: (a)'; ADD line 7). Φ (FC-4) and R1.3 (FC-5) stay [USER] in any case."

**RC-14. Items that one file has and another file lacks.**
- **In DRAFT, not in CONS.** R_4/R_5 reuse (DRAFT §1.2; G-3); S-a's prompt term for O (G-4); X′ integration after the `--final` lexicon-pin procedure (G-5); REQ-21's file name (G-6); recipe G reuse or re-run [LEAD] S1 (DRAFT §5.1; REF RQ §1.4). Fix CONS: add them as LW or LS items.
- **In CONS, not in DRAFT.** UW-17 (RB R8.6, a prompt-only classifier score; DRAFT §8.5 names it "[USER] W1 if chosen" but gives no FC item); UW-19 (freeze the Llama Gate B-lite rules; its U0 = W0 would drop the held-out Llama test that DRAFT §7.2 commits); LW-12's B-CK11 N4 and the O noise inputs for REQ-17; LW-14's Llama-trial check; LW-26's word "pre-specified" until REQ-20 and REQ-21 are committed; LW-27 (build Y now); LW-29 (model-agnostic Part C); LW-30 (the human-label-check paragraph); LS-03 (which runs use the new engine); LS-19 (the overlap control's test); LS-20; LA-10, LA-12 (a public deposit), LA-16. Fix DRAFT: add FC-36 [USER] W1 for R8.6 (silent: not built); add to §7.2 "If the user picks LLB U0 = W0 (CONS UW-19), the Llama held-out predictions have no test, and the paper says so"; list the LEAD items in §13.2 with a pointer to CONS.
- **In EXTR only.** W1-03 R_tok (9 runs, about $13.1, $15.5 with pod overhead, $19.3 × 1.25; M: EXTR script); W1-14 item 4 (the rule chosen by averaging over ρ); §10 item 6 (an L-effect sensitivity for removal options); §10 item 8 (a U–O correlation grid {0, 0.5}); the provisional REQ-27 to REQ-30. Fix: DRAFT §9.3 item 1 adds "R_tok is a [USER] proposal (new arms and money; EXTR W1-03). In force: no new arm (ADD §5 item 1)." CONS UW-14 (c) cites EXTR's cost. DRAFT §7.4 lists EXTR W1-14 item 4 and §10 items 6 and 8 as [LEAD] W1-P sub-questions. EXTR W1-03's mark becomes "[USER]" (new arms and money).

**RC-15. "Before any stage-1 outcome is read" cannot be met as written.** (CONS, EXTR)
- **Where.** CONS LW-19 ("before any stage-1 unit outcome is read (C VF-7)"), US-10 ("before any stage-1 outcome"). EXTR §1 item 6 ("before any stage-1 outcome is read").
- **Problem.** Six of the 50 primary cells are reused units whose values were read (R: DRAFT §12.1; AMD §K.3). Read literally, the condition is already false. DRAFT says "before any newly run stage-1 cell's outcome is read" (R: DRAFT §2.4, §4.4, §9.5; RB VF-6).
- **Fix CONS and EXTR.** Use DRAFT's wording.

**RC-16. The variance for "m beats r" under S-a differs.** (DRAFT, CONS)
- **Where.** DRAFT §5.3, "Variance" ("Under S-a: seed-level means, unpaired, pooled variance, Welch as a sensitivity"). CONS LS-06 and US-01 (b): under S-a, the reference tests use S-aW. AMD §D.6: under the fallback, "their tests use S-aW, unpaired".
- **Problem.** The files differ. Also DRAFT §3.2 pools the variance over the eight primary arms only, so a reference arm is not in the pool, and "pooled" for m against r is not defined.
- **Fix DRAFT.** "Under S-a: unpaired Welch (S-aW) for each pair (AMD §D.6); descriptive under the 3-seed fallback. [LEAD] S1."

**RC-17. Rules that need τ_O\* = 5 pp, and the F family.** (DRAFT, CONS, EXTR)
- **(a)** R1.3 is defined "at τ_O\*" (R: DRAFT §4.4; RB R1.3). FC-6's silent default is "no primary τ_O" (R: DRAFT FC-6). A yes to FC-5 with silence on FC-6 leaves R1.3's bar undefined. Fix DRAFT §4.4 and FC-5, CONS UW-05 and EXTR §6.1 item 3: "R1.3 uses 5 pp. A yes to FC-5 fixes τ_O\* = 5 pp for R1.3, whatever FC-6 says."
- **(b)** "m beats r" item 2 uses 5 pp (R: DRAFT §5.3). AMD ties it to "the primary τ_O\*" (R: AMD §D.1 item 2). Fix DRAFT §5.3: "below 5 pp (fixed for this rule whatever FC-6 decides; [LEAD] S1)".
- **(c)** DRAFT §4.4 (Φ, silent default): "F as a third family only if FC-6 adopts τ_O\*". DRAFT §4.5 item 3: "F_k only if Φ is adopted". The two contradict. Fix DRAFT §4.5 item 3: "F_k inside Φ if FC-4 is yes; else as its own Holm family if FC-6 is yes; else not tested". In §4.4 write "a fourth family (after U, O and L)".

**RC-18. EXTR's builder defaults adopt AMD A7 before the lead decides.** (EXTR)
- **Where.** EXTR §8 row 6 (builder default "the grid, with the rule averaged over ρ"); W1-14 tests ("the settings refuse a ρ grid other than {0, 0.67}"); W1-14 item 4.
- **Problem.** ADD L15 (1) is in force; A7 edits it and is [LEAD] W1-P (R: DRAFT §7.4 and C-17; AMD §H A7). EXTR §0 item 4 says the builder default is "the rule in force". W1-14 item 4 (choose the rule by an average over ρ) is a new rule: L15 (1) says "equal weight per (shape, size) grid point" (R: ADD L15 (1)), and no draft states it.
- **Fix EXTR.** Default ρ grid {0} (= L15 (1)); {0, 0.67} behind a switch; the test reads "refuses a grid other than the settings' grid"; item 4 is "a [LEAD] proposal (I), only with A7". DRAFT §7.4: add item 4 as a sub-question of A7.

**RC-19. EXTR makes RB R5b.3's three $0 checks conditional.** (EXTR)
- **Where.** EXTR W1-18 ("only if O-ext H or N is chosen"). DRAFT §6.5 and CONS LW-05 run them before U8 is decided.
- **Problem.** Check (1) sets N's cost ($10–27 at a 128-token cap against $40–70 at 2,048; E: CK-OR §5.4 via RB), which the user needs to answer FC-7. Checks (2) and (3) also feed O reporting (R: RB R5b.3, R5b.5).
- **Fix EXTR.** "Run before U8 is decided, at $0, whatever the answer."

**RC-20. The classifier run's money is marked three ways.**
- **Where.** EXTR W1-07 ("run money [USER]"). DRAFT §8.5 R8.1 ("new money on a stage-1 pod", no mark). CONS LW-20 (LEAD).
- **Problem.** The content classifier is a planned scorer (R: PLAN-S §5.4; §8, "every … scorer is charged in full").
- **Fix (all three).** "The run (about $1; E: CK-EM via RB) is part of the approved plan. It is paid from stage 1's funding event (FC-19), never from the Gate B balance or on a Gate B kit pod. No separate [USER] item."

**RC-21. The decoy labels have different names.**
- **Where.** DRAFT §8.5 F7 and CONS LW-10: one label, `stage1-plant-decoy-v1` (R: AMD §G F7). EXTR §5: three labels, `stage1-plant-decoy-rows-v1`, `stage1-plant-decoy-unit-v1`, `stage1-plant-decoy-leaf-v1`.
- **Problem.** Labels are append-only and sealed (R: ADD L13 (7)). One set of names must be fixed before the append.
- **Fix.** The lead picks one form before the append. Recommendation (I): EXTR's three labels (one draw per label, one owner each, as L13 (2)–(3) require). DRAFT and CONS then cite "the decoy labels (EXTR §5)".

**RC-22. B↓LR seeds do not follow B+Qi's seed logic.** (DRAFT, CONS)
- **Where.** DRAFT §5.1 (B↓LR "1101–1106 if added (RB R3.5)"); CONS US-11 (1101–1106).
- **Problem.** DRAFT recommends B+Qi at 1102–1107 because "it gives six seeds shared with the method arms" (R: DRAFT §5.5, C-12). AMD lists B↓LR at 1102–1107 (R: AMD §D.1 table). The same reason applies to B↓LR (I).
- **Fix DRAFT and CONS.** "B↓LR seeds: 1101–1106 or 1102–1107, decided with LQ18 (C-12) after FC-2."

**RC-23. The confirmation placeholder can pick a contrast that the confirmation cannot test.** (DRAFT)
- **Where.** DRAFT §4.7 and Appendix C G-1: "the two primary contrasts with the largest |t| among those labelled better or worse".
- **Problem.** "Worse" can mean "worse (O)" or "worse (L)" (R: DRAFT §4.5). The confirmation units read 200 hidden harm prompts (R: FOCUS 8 Oct 13:53 UTC, "Confirmation"), and CONS LS-18 recommends no over-refusal bank in the subsample (R: CONS, from ENG-Y decision 4). "|t|" does not name the test.
- **Fix DRAFT.** "the largest |t| of the primary U test, among contrasts whose U part reads better or worse (U)".

**RC-24. DRAFT says Gate C "also reports top-k hit rates".** (DRAFT)
- **Where.** DRAFT §9.6, LOCALIZED (from PLAN-S §11).
- **Problem.** Frozen PREREG revision 5 reports "the top-1 hit (chance 12.5%)" beside ρ (R: PREREG §5, line 195, and the `verdict` phase, line 230; `grep` finds no other top-k report). A wider top-k report as part of Gate C reads like a change to frozen Gate C.
- **Fix DRAFT.** "Gate C reports, as frozen, the top-1 hit beside its Spearman ρ (PREREG). Other top-k hit rates are stage-1 reports from the sealed rankings, outside Gate C."

**RC-25. DRAFT says the T1 bundle "passed its verification with fixes".** (DRAFT)
- **Where.** DRAFT §0.4.
- **Problem.** ADD §4: "Verdict: fix_required, one blocking defect" (R). No FOCUS entry at `5957a37` records the fixes as applied and checked again (R: a search of FOCUS for T1). CONS LW-22 and EXTR also say "the verified T1 bundle" (R).
- **Fix DRAFT.** "Its verification returned fix_required; the lead ruled the fixes (ADD §4, 16 Oct 21:20 UTC). That the fixes are applied and checked again is not recorded in FOCUS (UNVERIFIED here)." CONS LW-22 and EXTR §0 item 1: the same caveat.

**RC-26. LQ4's w0b-2 option needs a pod start and the user's go.** (DRAFT, CONS)
- **Where.** DRAFT §1.5 (LQ4, "Option: for seed 1101, copy the retrain's e1 state from the stopped pod w0b-2"); CONS LS-04 (b).
- **Evidence.** The new FOCUS entry "BACKUP: the Mac-only model weights and states …" (recorded 17 Oct 01:05 UTC) says the retrain's q and e1 states are only on the stopped pod w0b-2, and "a pull needs a pod start and the user's go" (R).
- **Fix DRAFT and CONS.** Add "(a pull needs a pod start and the user's go; R: FOCUS 'BACKUP …', 17 Oct 01:05 UTC)". The option is [USER] when it is used.

**RC-27. DRAFT's W1 build scope omits ADD §5's binding builds.** (DRAFT)
- **Where.** DRAFT §10.6 step 2 ("REQ-1 to REQ-21, plus REQ-23 and REQ-25 if adopted"); §13.1 row 2.
- **Problem.** ADD §5 items 1–3 are binding reports (R: ADD §5). EXTR builds them as W1-01, W1-02, W1-05 and W1-06 (provisional REQ-27, REQ-28 and a REQ-9 change), and the plant-rank report as W1-08 (provisional REQ-29). ADD §5 item 2 (q-only against e1-only) is binding, so REQ-25 (a) is not "if adopted"; only V1 (REQ-25 (b)) is [LEAD] (R: EXTR W1-04).
- **Fix DRAFT.** §10.6 step 2 and §13.1 row 2: add "the ADD §5 builds (EXTR W1-01, W1-02, W1-04 (a), W1-05, W1-06; provisional REQ-27, REQ-28) and the plant-rank report (W1-08; provisional REQ-29)", and write "REQ-25 ((a) binding; (b) V1 if adopted)".

**RC-28. A user's yes after Gate B's verdict: the reading of PLAN-S:239 is not recorded.** (all three)
- **Where.** DRAFT §9.5 R0.1 ("The yes may depend on Gate B's disclosed verdict"), §2.4; CONS LW-19; EXTR §1 item 6.
- **Problem.** PLAN-S:239: "If they are approved after any unit outcome, every stage-1 claim is labelled post-Gate-B exploratory" (R). FOCUS: "Anything added later is 'post-Gate-B exploratory'" (R: 8 Oct 13:53 UTC). A yes after a Gate B outcome may count as an approval after an outcome (I).
- **Fix (all three).** REQ-21 (h) records the reading: "A conditional item whose outcome-free rule text is committed before wave 1 is not 'added later'. A yes after Gate B's verdict is disclosed for each item, and the item stays outside P1–P6." If the lead does not accept this reading, each such item is labelled post-Gate-B exploratory.

### Nits

**RC-29. HEAD and FOCUS moved during the review.** At 01:05 UTC HEAD is `5957a37`, which adds one FOCUS line at line 74 (R: `git log`, `git show --stat`). FOCUS's SHA-256 is now `1587b549813792e1` (R). DRAFT Appendix D's spans and CONS's "FOCUS:NN" pointers for lines 74 and later are one line low at the new hash (M here). Fix: DRAFT already states the hash of its spans; CONS adds "at `23e3da8f…`" to its FOCUS pointers or cites entries by title (ADD §3 (3)). The new entry also bears on RC-26.

**RC-30. Name collisions.** "D1" and "D3" in DRAFT §0.2 are the 15 Oct user decisions. "D1" is also AMD's seed layout (FC-3) and AMD's register row for the "beats" rule (§5.3, §13.2). "D3" is also PLAN-S §9's cost freeze (§10.1, §10.6). "P4" in DRAFT §12.1, EXTR §6.4 item 1 and CONS LW-08 item 1 is Gate B's P4 prediction, not stage-1 P4 = U(a0) − U(S1). Fix: write "15 Oct D1/D3", "seed layout D1", "AMD row D1", "PLAN-S D3" and "Gate B's P4".

**RC-31. "AMD D4".** DRAFT §5.3 writes "Dominance (AMD D4, family 1b)". AMD's register has D1–D2 only; D4 is AMD's section §D.4 (R: AMD §H). Fix: "AMD §D.4 (register row B5)".

**RC-32. Headline table step 4.** DRAFT §4.5 step 4 ("inconclusive") does not add "significant, below the SESOI" when U rejects favourably with 0 < Λ̂ < 5 pp and the contrast is not equivalent. DRAFT §4.3 says the text adds it. Fix: "inconclusive; add 'significant, below the SESOI' if U rejected favourably".

**RC-33. FC-17's silent default is not defined.** DRAFT: "the user's earlier choice stands". Fix DRAFT (and the same text in CONS UW-14 and EXTR W1-02): "Silent: this file pre-registers the token-axis analysis (LQ47). The title is a paper item and stays as PAPER has it until the user confirms FC-1 or decides."

**RC-34. G1's short-answer clause.** DRAFT §3.7 item 1 omits PREREG G1's "a short-answer TOO CLOSE … counts here as a G1 failure" (R: PREREG §3 G1), which AMD §F item 1 keeps. Fix: add it.

**RC-35. A duplicate and some missing labels in DRAFT.** §13.2 lists RB R8.4 twice (W1 "RB R8.1–R8.5" and W1-P "RB R8.4"). Some numbers have no R/M/E/I label: §2.4 "about 5.1 GB" (R: RB U-7), §8.5 F6 "about 64" (I: B-CK11 F6 via AMD), §6.5 "400 harmless PHTest rows" (R: RB R5b.2). Fix: W1 row "RB R8.1–R8.3, R8.5"; add the labels.

---

## 2. Agreement map: DRAFT FC items against CONS and EXTR

| DRAFT | CONS | EXTR | State |
|---|---|---|---|
| FC-1 | UW-01 | "Marks" | agree |
| FC-2 | UW-02 | §6.3 item 4; §8 row 1 | differ: RC-01 |
| FC-3 | UW-03 | §6.3 item 5 | differ (plan B): RC-07 |
| FC-4 | UW-04 | §6.1 item 2 | agree on the rule in force; sidedness: DRAFT one-sided, CONS one-sided (I), EXTR open |
| FC-5 | UW-05 | §6.1 item 3 | agree; dependency RC-17 (a); coherence RC-02 |
| FC-6 | UW-06 | §6.2 item 2 | agree |
| FC-7 | UW-07 | W1-16, W1-19 | differ: RC-05, RC-12 |
| FC-8 | UW-13 | §6.3 item 5 | agree |
| FC-9 | UW-04, UW-08, UW-09, UW-10, UW-12 | §6.1 item 6 | differ: RC-13 |
| FC-10 | UW-11 | §6.3 item 1 | agree |
| FC-11 | UW-15 | §6.3 item 5; §6.5 (a) | EXTR internal: RC-12 |
| FC-12 | UW-16 | §7 | differ (mark): RC-12 |
| FC-13 | LA-11 | W1-10 | differ (deadline): RC-11 (c) |
| FC-14 | UW-18 | W1-07 | agree |
| FC-15 | US-10 | text-only list | differ: RC-11 (b), RC-12 |
| FC-16 | US-12 | §6.2 item 11 | differ: RC-11 (b), RC-12 |
| FC-17 | UW-14 | W1-02 | agree on the mark; silent default RC-33 |
| FC-18 | LA-09 | — | differ (deadline): RC-11 (d) |
| FC-19 | US-07 | — | differ (placement): RC-11 (a) |
| FC-20 | US-15 | text-only list | differ: RC-11 (b), RC-12 |
| FC-21 to FC-28, FC-30, FC-32 | US-04, US-05, US-07, US-17, US-06, US-02, US-03, US-01, US-13, US-16 | — or text-only list | agree |
| FC-29 | US-11 | text-only list | differ: RC-12, RC-22 |
| FC-31 | US-14 | text-only list | differ (mark): RC-12 |
| — | UW-17, UW-19 | W1-07 (R8.6) | missing in DRAFT: RC-14 |
| — | US-08, US-09, US-18 | — | missing in DRAFT: RC-06 |
| §1.3 plan B (G-2) | — | G-1 | missing in CONS: RC-07 |
| §1.2 R_4/R_5 (G-3); G-4; G-5; G-6; recipe G reuse | — | — | missing in CONS: RC-14 |
| §9.3 item 1 (no new arm) | UW-14 (c) | W1-03 R_tok | EXTR only: RC-14 |
| §14.3 | LA-01 to LA-08, LA-13 to LA-15 | — | agree; DRAFT lacks LA-10, LA-12, LA-16 (RC-14) |

---

## 3. Checks that passed (arithmetic M here, from numbers in DRAFT unless named)

| Check | Result |
|---|---|
| Primary cells | R 8 + a0 6 + 6 method arms × 6 = 50 (M). Block A: 18 + 1 + 2 = 21 runs plus the c0 job; block B: 18 + 2 + 3 = 23; 44 new + 6 reused = 50 (M). PLAN-S's "19–21" for block A fits if R_4 and R_5 are reused (I). |
| Common seeds | P1–P3, P5, P6: J = 6; P4: J = 5 (1102–1106) (M), as DRAFT §3.3. |
| df | S-a: 50 − 8 = 42 (M), as DRAFT §3.2. HB residual: 50 − 8 − 7 = 35 (M), as VR-B's "Residual df (D0) 35" (R). |
| The 1101 rule | method arms 1102–1107 (plan A) and 1102–1110 (plan B) never use 1101; plant arms use 1101 by ADD §3 (R). |
| δ as a share of E | 5 / 45.11 = 11.08% (M); 5 / 48.17 to 5 / 43.50 = 10.4–11.5% (M); mean of 43.50, 43.67, 48.17 = 45.11 (M). |
| Gate B values (as printed) | SD of 0.67, 2.50, 4.33 = 1.83 (M); SE 1.83/√3 = 1.06 (M); SD(U(R_j)) 1.35 and same-seed ρ 0.76 reproduce from a0 46.7, 46.8, 51.3 and r_j (M). |
| τ_L | 2√2 × s and s·√(1/3) match TLC; τ_L / SE = 2√6 = 4.90 (R: TLC; M: EXTR script). The 2-df interval 0.52–6.28 and 0.22 match ADD L16 (R; M: EXTR). |
| O | a0 4, 6, 4 against θ0 17 → 11–13 pp below (M); a full return is +12.3 pp (M: 17 − 4.67); bound offsets 1.96 / 2.52 pp seed-only and 6.58–6.91 pp prompts random (M). |
| FRE and c0 | 2,934 s = 48.9 min (R: REF); $1.459 at $1.79/h (M); training 7.6–8.4% and generation 80–82% of the ledger totals (M); c0 (b) 480 s ≈ $0.239, c0 (a) 870 s ≈ $0.433 (M). |
| Reference costs | Safe LoRA 3 × 0.93 FRE = 2.8 FRE, $4.1, $4.8 with one pod, $6.1 × 1.25 (R: RV R6, "the × 1.25 figures ($6.1) are right"); B+Qi 6 × $1.52–1.53 = $9.1–9.2, +2 pods $10.6–10.8, × 1.25 $13.3–13.4 (M); FC-26 jobs 12 (15) + 3 = 15 (18) at 4 per pod → 4–5 pods (M). |
| Money | $91.94 − $83.91 = $8.03 (M); FOCUS says "wave 1 needs $83.91" (R: FOCUS 16 Oct 13:21 UTC); PLAN-S's $56–98 = $25–45 + $31–53 (M). |
| Steps | ⌈4,800/128⌉ = 38, ⌈4,200/128⌉ = 33, ⌈4,848/128⌉ = 38 (M); plant corpus 4,837 − n gives 38 steps for n ≤ 100 ((4,837 − 100)/128 = 37.008; M). |
| Safe LoRA | 112 = 7 × 16 (M); K = 39 is 34.8%, K = 12 is 10.7% (M); 5,939,687,552 bytes ≈ 5.94 GB (M). |
| Testing | Φ start weights 6 × 0.15 + 12 × 0.1/12 = 1.0 (M); first U level 0.75% against 5%/6 = 0.833% (M); 98.33% = 1 − 2 × 0.05/6 (M); HB-3 √(200/35) = 2.39 (M). |
| HB-C | DRAFT's "gains 15–22%" matches VR-B's "−15 to −22%" (R: VR-B). |
| E_HB | +30.4 pp (Mac) and +30.3 pp (pod) (R: PREREG §6, citing FOCUS). |
| Frozen frame | No file changes Holm over 6, SESOI 5 pp, P1–P6 as primary, REQ-22 not built, the sealed rankings, G1 for Gate B, G4 or the HarmBench pipeline (R: DRAFT §0.2, §2.2, §3.7, §6.3; CONS; EXTR). Exception in wording: RC-24. |
| Dates | 27 Oct (W1) and 3 Nov (block A) are E from REPLAN, a proposal, in all three files (R). |

---

## 4. Process

**Commands run (all exit 0 unless stated).**
- `date -u` at 00:55, 01:00, 01:05, 01:15 and 01:18 UTC.
- `ls -la` and `wc -l` of this folder; `cat` of `w1_extract_numbers.py` and `.out`.
- In the main checkout (read-only): `git rev-parse --short HEAD`, `git branch --show-current`, `git log --oneline -3`, `git status --porcelain research/FOCUS.md`, `git show --stat 5957a37`, `git diff 3db753e 5957a37 --stat`; `shasum -a 256` of FOCUS, PLAN-S, PREREG, BRIEF and ADD (twice for FOCUS).
- `awk`, `sed`, `grep` and `python3 -I` reads (long lines cut or folded): FOCUS lines 70–130 (cut at 260 characters), lines 74–78, 125, 135, 150, 152–157, 204–227 (search hits), 236–256; PLAN-S lines 100–132 and 140–245; BRIEF lines 186–200 and the REQ-21 lines; ADD lines 1–16, 203–229, 243–324; AMD headings, §D, §F, §B.5, §H; RB lines 110–140 and one search hit; RV lines 80–135; REF headings, §C.3–§C.6, §Q.1–§Q.2; VR-C lines 120–130; VR-B (search hits); PREREG lines 146–152 and search hits for G4, E_HB and top-k; PAPER lines 22, 240, 242; ENG-Y decisions (lines 330–352 and one search hit).
- One `ugrep` search failed on a regular-expression quantifier (exit non-zero); I repeated it with `grep -o` and `python3 -I`.
- `python3 -I -c` arithmetic only (the M values above).
- One `Write` of this file.

**Not done.** No simulation, cost script or test was re-run. No source draft, record or repository file was changed. I did not open LLB, the check notes, SPEC, SCOPE, PLANF, RS or any W0 file. I sent no message.

**Limits.**
1. RC-03 rests on CONS's statement about LLB. I did not open LLB, so that I do not read the values.
2. Severity is my judgement (I). RC-04, RC-05 and RC-06 could be read as Minor if the lead treats them as wording. RC-01 and RC-02 could not, because both touch a user decision.
3. For RC-02 I propose a flag rule as the in-force rule. CONS proposes a neutral word. Both keep the user's label definition; the lead picks the form.
4. FOCUS changed at 01:05 UTC (RC-29). I re-checked only the new line; no other cited source changed (R: `git diff --stat`).
5. I checked arithmetic and source quotes for the items named in §3. I did not check every number in the three files.
