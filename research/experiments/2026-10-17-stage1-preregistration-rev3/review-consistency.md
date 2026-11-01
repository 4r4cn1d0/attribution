# Consistency review: stage-1 pre-registration revision 3 and the REQ-21 W1 record

**Status.** An adversarial consistency review for the main-study lead (GI VI). It is not a decision. It adopts nothing. It changes no frozen Gate B/C rule, no sealed record, not D5 = (a) and no user decision. Where a fix needs a ruling, the review says who decides.

- **Written** 2026-10-17 from 14:05 UTC by an Opus worker, under the user's weekend delegation to the lead (FOCUS 2026-10-17T07:21 and 09:01 UTC). Clock checked with `date -u` at 14:08, 14:21, 14:22 and 14:26 UTC (finished at 14:26 UTC).
- **Reviewed files** (this folder; SHA-256 first 16, M at 14:22 UTC):
  - **REV3** = `stage1-preregistration-DRAFT-rev3.md` `b31696deadc339ce`.
  - **REC** = `req21-w1-record.md` `b4ba34fc85ef8b4f`.
  - Basis: **LEDGER** = `decision-ledger.md` `e7e4434505cef8c2` (the hash that REV3 cites; M).
- **Read-only.** Main checkout `/Users/spiderishi/Coding/attribution` at HEAD `3536776` (M: `git rev-parse` at 14:21 UTC; the cited sources are clean). The only file written is this one.
- **Data rules kept.** I opened no `selector.jsonl`, no `hidden/`, no held-out file, no `rows.jsonl`. I printed no row, prompt, answer, anchor or lexicon text. From settings and sealed records I printed keys, numbers and rule strings only.

**Labels for numbers.** **R** = read in a source (named). **M** = measured or computed (by a named script, or by me as arithmetic: "M (here)"). **E** = estimate (basis named). **I** = inference or judgement. **UNVERIFIED** = nobody named checked it.

**Short names** are the LEDGER's (FOCUS, ADD, BRIEF, REV2 = DRAFT revision 2, CONS, EXTR, AMD, VR-B, REF, RB, AUDIT, PREREG, PLAN-S, P78, HLC, SET, S1OUT). REV3 section numbers are written "REV3 §n"; REC item numbers "REC (x) rule n".

---

## 0. Verdict

**Neither file is ready to commit.** The two files agree on all 13 binding lead rulings of 17 Oct (§8) and on most decided rules (§11). But they disagree on 3 rules that are primary or touch a user decision, and REV3 holds one route that a frozen Gate B rule forbids.

| Severity | Count | Meaning |
|---|---|---|
| **Critical** | 3 | A rule that, if committed, breaks a frozen rule or a user decision's reach, or a primary-family rule on which the two files disagree. Fix before any commit. |
| **High** | 4 | A W1 rule or a ruling's status on which the files disagree, or a decided rule that a built setting contradicts and one file misses. Fix before the W1 commit. |
| **Medium** | 12 | One file lacks a W1 text that the other has or that a source requires, or one file is inconsistent with itself. Fix before the W1 commit. |
| **Low** | 26 | Wording, ids, labels, citations, process. Fix when convenient; none changes a rule. |

**The three blockers, in one line each.**
1. **CR-1.** The variance of every contrast against θ0 or a0 (feasibility, Φ's F_k, R1.3's θ0 and a0 parts) differs between the files. REC uses AMD §A.8's REML residual; REV3 (LN-20) says that form omits the seed shift and proposes the arm's own between-seed variance, which REQ-19's sealed planning and the built screen already use.
2. **CR-2.** δ_fam's scope differs. REC proposes "every model at any size"; REV3 sets "the 1B families". REC's reading would fix 7–8B margins that P78 reserves to the user (decision H) and change D5's "SESOI 5 pp" at 7–8B.
3. **CR-3.** REV3 names a route that restarts a stopped Gate B kit pod to pull states. PREREG revision 5 §9 says: "A stopped kit pod is never restarted."

---

## 1. How to read the findings

Each finding gives: **where** (file and place), **evidence** (with labels), **why it matters**, and the **exact fix** for each file. "Both" = REV3 and REC. A fix in quotation blocks is replacement text. Where the fix needs a ruling, "Decides" names the decider and the deadline (W1, W1-P or S1, as REV3 defines them).

---

## 2. Critical

### CR-1. The seed part of θ0, a0 and cross-cluster contrasts: the two files give different variance rules

- **Where.** REC (e) rule 9: "Against θ0 …, its variance is σ̂²_m/J_m plus the item part". REV3 §3.6 LN-20 item 1: the seed part is "the sample variance (ddof 1) of m's own cell values over its J_m seeds, divided by J_m"; item 2: cross-cluster pairs use "the pair's own paired variance on the common seeds (J − 1 df) plus the item part". REC has no LN-20. REC (c) rule 12 gives the cross-cluster form for references only, and without the item part.
- **Evidence.**
  - AMD §A.8 (R: AMD line 152): "Its variance is σ̂²_m/J_m plus the item part". Under HB-C, σ̂²_m is the REML residual, which excludes the cluster's seed shift s_{c,j}; θ0 has no seed, so nothing cancels the shift (I; REV3 §3.6).
  - REQ-19's sealed planning already uses the between-seed sample SD for the θ0 contrast: `o.a0_seed_sd_pp` = 1.1547 (the ddof-1 SD of a0's O, 4, 6 and 4 of 100) and `o.error_models.seed_only.vs_theta0.plan_a.se_pp` = 0.4714 = 1.1547/√6 (M: `req19/limits_check.json` `a30d7940…`, numeric keys only; M (here) for the identity).
  - The built screen's "hb" form is "the option's own seed variance (ddof 1) / n + the comparison arm's own variance / its n" (R: SET `selector_spec.json`, `screen.se_form_rule`).
  - LW-06: "the same bound holds everywhere, REQ-16's screen included" (R: LEDGER).
- **Why it matters.** These SEs decide Φ's F_k, the θ0 part of O_k, the a0 part of L_k (for P1–P3 a cross-cluster contrast) and every "feasible / infeasible" state. So they decide "worse (O)", "worse (L)" and "within the over-refusal limit" for primary contrasts. REC's form would also make the analysis's bound differ from the screen's and from REQ-19's planning, against LW-06. And both files claim that "an O_k rejection implies the per-comparison state infeasible, because it is the same test with the same SE" (REC (c) rule 4; REV3 §4.3). That claim holds only if F_k, the IUT parts and the states use one SE.
- **Fix, REC (e) rule 9.** Replace the sentence "Against θ0 (one greedy unit with no seed), Λ̂ = O(m) − O(θ0) uses all of m's seeds, and its variance is σ̂²_m/J_m plus the item part from the J_m × P table of y(m, j, p) − y(θ0, p)." with:
  > Against θ0 (one greedy unit with no seed), Λ̂ = O(m) − O(θ0) uses all of m's seeds. [PROPOSED; LN-20] Its variance is s²_m/J_m plus the item part max(0, MS_P − MS_E)/(P·J_m) from the J_m × P table of y(m, j, p) − y(θ0, p), where s²_m is the sample variance (ddof 1) of m's own values O(m, j) over its J_m seeds (J_m − 1 df); df by Satterthwaite. The REML residual is not used here, because under HB-C it excludes the cluster's seed shift, and θ0 cancels none of it. A contrast across the two design clusters (L(m) − L(a0) for a removal arm; a removal arm against a full-corpus reference; the per-actor separation test across clusters) uses the pair's own paired variance on the common seeds (J − 1 df) plus the item part. These forms serve every θ0 and a0 bound in this record: the feasibility states (rule 8), Φ's F_k, the θ0 part of O_k and the a0 part of L_k (item (c) rules 4–5) and the selector screen's `se_form` "hb" (item (k) rule 5). REQ-19's sealed planning uses the same seed part. Fallback: AMD §A.8 as written (σ̂²_m/J_m), and the record states that the θ0 and cross-cluster SEs omit the seed shift.
- **Fix, REC (c) rule 5.** Add: "For P1–P3, the a0 part of L_k is a cross-cluster contrast; its SE is item (e) rule 9's cross-cluster form [PROPOSED; LN-20]."
- **Fix, REC (c) rule 12, "Variance".** After "the pair's own paired variance with J − 1 df" add "plus the prompt part (AMD §D.2, V-3)".
- **Fix, REC (c) rule 4, the final "(I: …)" sentence.** Add "(this holds because F_k, both IUT parts and the states use item (e) rule 9's SE)".
- **Fix, REC Z.1.** Add the row "LN-20 | the seed part of θ0, a0 and cross-cluster contrasts | (e) rule 9; (c) rules 4, 5, 12 | AMD §A.8 as written, with the omission stated".
- **Fix, REV3 §3.6 LN-20.** Keep the text. Add one evidence line: "REQ-19's sealed planning (`o.a0_seed_sd_pp` 1.1547 pp, ddof 1) and the built screen's `se_form` 'hb' already use the arm's own between-seed variance (M: S1OUT `req19/limits_check.json`; R: SET `selector_spec.json`)." In §4.3 "What 'worse (O)' needs", after "same model and SE" add "(LN-20's SE for every θ0 and a0 part)".
- **Decides:** the lead, LN-20, W1 (before W1-P, because the screen setting depends on it). Until then both files carry the same [PROPOSED]/[LEAD-NEEDED] text and the same fallback.

### CR-2. δ_fam's scope: the files disagree, and REC's proposal reaches into a user decision

- **Where.** REC (b) rule 6 "Scope [PROPOSED; LN-04]": "'another family' means every model other than OLMo-2-1B, at any size; each model's δ_fam comes from its own Gate A mean E … Fallback: δ_fam applies to Llama-3.2-1B only". REC also writes "fixed before that family's comparison runs". REV3 §4.4 (BR-2): "δ_fam applies to the 1B families … The 7–8B margin is set in the 7–8B pre-registration." LEDGER C-3 recommends REC's broad reading.
- **Evidence.**
  - UW-13's item text (R: CONS:301–:309): "a second family's margin … **Decides: USER (it fixes a stage-2 rule)** … PLAN-S:243 asked for the comparison scale before Llama's formal Gate A". UW-13 in FOCUS (R: FOCUS 07:21 UTC): "fixed before its stage-2 runs".
  - P78 (R: P78 :243): "D5 keeps P1–P6 primary with 'SESOI 5 pp'. Options (a) and (c) change that SESOI at 7–8B, so they need the user's explicit word." P78 :436 lists "a relative SESOI (for example 11% of E: 4.9 pp for OLMo-2-7B, 5.9 pp for Llama-3.1-8B)" as a variant that "the user can add". P78 :387 marks decision H as the user's.
- **Why it matters.** REC's recommended text, if adopted, sets the 7–8B margins (about 4.9 and 5.9 pp; R: P78 :436) in the 1B record, before the user's decision H, and so changes D5's "SESOI 5 pp" at 7–8B by a lead proposal. The task rule forbids a change to D5 = (a) or to a user decision. UW-13's own text supports REV3's narrow scope.
- **Fix, REC (b) rule 6.** Replace from "**Scope** [PROPOSED; LN-04]" to the end of the rule with:
  > **Scope** [LEAD, under delegation; MSG-15 (lead message, 17 Oct)]. δ_fam is the stage-2 rule that UW-13 fixes: it applies to Llama-3.2-1B, and to any other 1B model family only if a later decision adds one. δ_fam for Llama-3.2-1B is fixed before its stage-2 runs, and 5 pp absolute is reported beside it. This record sets no 7–8B margin. The 7–8B margin is the user's decision H in the 7–8B pre-registration (P78 §6); the relative SESOI of 11% of E is one of its listed variants.
  (Until the lead adds MSG-15 to the LEDGER, write "[PROPOSED; LN-04]" in place of the MSG mark, with this text and no broad reading. See HI-1.)
- **Fix, REV3 §4.4.** Keep the content. Change "[LEAD, under delegation] (BR-2)" to the LEDGER row once it exists (HI-1). Change "the 1B families: stage 2's Llama-3.2-1B and any other 1B model" to "stage 2's Llama-3.2-1B, and any other 1B model family only if a later decision adds one".
- **Fix, LEDGER C-3 and LN-04.** Replace the recommendation with REV3's scope and cite CONS UW-13 "it fixes a stage-2 rule".
- **Decides:** the lead (scope reading, W1). The 7–8B margin stays the user's (P78 decision H).

### CR-3. REV3 offers a route that a frozen Gate B rule forbids: restarting a stopped kit pod

- **Where.** REV3 §1.5 last bullet: "A pull from the stopped pod w0b-2 needs a pod start and the user's go (**[USER]** when used)." REV3 §6.3 LN-12: "Another route needs a pod start and the user's go (**[USER]**)." REV3 §14.3: "**A pod start** to pull states from a stopped pod (§1.5, LN-12's other route)." LEDGER X-5: "pull the states from the kept stopped pod `attribution-gateb-w0a-1` … which needs a pod start and the user's go." REC does not carry this route.
- **Evidence.** PREREG revision 5, §9 "Pod operation rules" (R: PREREG line 317): "A stopped kit pod is never restarted. A requeued host's jobs run only on its replacement." `attribution-gateb-w0a-1` and `attribution-gateb-w0b-2` are Gate B kit pods, each "verified-and-stopped" (R: FOCUS 16 Oct 00:25 and 13:21 UTC entries).
- **Why it matters.** Nothing in stage 1 may change a frozen Gate B rule (FR-01). A user's go does not change a frozen rule inside this delegation. A pre-registration that lists the route invites a later breach.
- **Fix, REV3 §1.5.** Replace the last sentence with:
  > No state is pulled from a stopped Gate B kit pod: PREREG revision 5 §9 says "A stopped kit pod is never restarted" (frozen). A needed adapter is regenerated by the fingerprint rule above, or the item takes its fallback.
- **Fix, REV3 §6.3 LN-12.** Delete "Another route needs a pod start and the user's go (**[USER]**)."
- **Fix, REV3 §14.3.** Delete the bullet "**A pod start** to pull states from a stopped pod (§1.5, LN-12's other route)."
- **Fix, LEDGER X-5.** Delete the sentence "Another route: pull the states from the kept stopped pod … the user's go."
- **Note for the lead (not an edit here).** FOCUS 01:05 UTC (17 Oct) says of w0b-2 that "a pull needs a pod start and the user's go". That line has the same conflict with PREREG §9; a FOCUS correction is the lead's.
- **Decides:** nobody; this is a deletion to match a frozen rule.

---

## 3. High

### HI-1. BR-1, BR-2 and BR-3 have no ledger row and no source I can find; the two files give them different status

- **Where.** REV3 §0.3 item 2 introduces "the lead's brief for this revision (17 Oct)" with BR-1 (R1.3 as Φ's IUT at the node's level; F_k → L_k 1), BR-2 (δ_fam scope) and BR-3 (the A1 claim bound in force now), each marked **[LEAD, under delegation]** and used in REV3 §4.2, §4.3, §4.4, §9.3 item 3, §14.1 FC-4/FC-5/FC-8 and §14.2 (LN-04, LN-05 "closed here"). REC keeps the same three items as [PROPOSED] (LN-04, LN-05, LN-15 fix 5 in REC (b) rules 5–6, (c) rules 4–5, (g) rule 1, (h) rule 5, Z.1).
- **Evidence.** The 17 Oct lead rulings that this review's brief lists as binding (B-1, "f" and L15 (4) and the decoy labels, W1-08 (1), the token axis, D1 seeds, the counting rule, the coherence flag, R1.3's "feasible or undetermined" case, the cap, risk 44, OLMo 3, the newline limit) do not include BR-1 to BR-3. The LEDGER has no such rows (R: LEDGER §1.6, MSG-01 to MSG-13). A search found no file with "BR-1" outside REV3 (M: `grep -rln` over `.ai/briefs`, `research/experiments/2026-10-17-*` and `tmp/gi-vi-parallel/`).
- **Why it matters.** The two files disagree on the status of three W1 rules: Φ's F_k edge, the test level of R1.3's θ0 and a0 parts, and the A1 claim wording. A reader cannot tell which is in force. A [LEAD, under delegation] mark needs a recorded ruling.
- **Content check (I).** Each BR item is sound and outcome-free:
  - BR-1: AMD §B.2 itself writes the R1.3 row "F_k → L_k 1 instead … [LEAD]" (R: AMD line 266), and UW-04 adopted "weights as in draft B §B.2" (R: FOCUS 07:21 UTC). The IUT is AMD §B.3's own test form (R: AMD lines 300–303). I re-derived the levels (M (here): `phi_levels_check.out.txt` equals my hand update: after U_k and F_k, L_k 0.510%, O_k 0.135%).
  - BR-2: supported by UW-13's item text (CR-2).
  - BR-3: wording only; it uses FO-04's V1 Jaccard 0.314 (R: FOCUS 09:32 UTC), which was read before the ruling, so REV3 §12.3 item (17) is right to disclose it. LW-21's 1/3 bar was written for V2a; applying it to V1 is an extension (I). AUDIT top fix 5 and RB R7.2 give the same bound on their own grounds, so the bound does not need the V1 argument.
- **Fix, option (a), recommended.** The lead adds three LEDGER rows (source "lead message, 17 Oct"), then both files cite them:
  > **MSG-14 (BR-1).** R1.3 enters Φ as AMD §B.3's intersection–union nodes: O_k's null "O(m) − O(c) ≤ 0 or O(m) − O(θ0) ≤ τ_O\*", L_k's null "L(m) − L(c) ≤ 0 or L(m) − L(a0) ≤ τ_L"; each p-value is the larger of the two one-sided p-values, tested at the node's current Φ level. Φ's F_k edge is AMD §B.2's R1.3 row, F_k → L_k 1. The per-comparison feasibility state is printed and is never the label test. [LEAD, under delegation]
  > **MSG-15 (BR-2).** δ_fam's scope as CR-2's text. [LEAD, under delegation]
  > **MSG-16 (BR-3).** The A1 claim bound is in force at W1: P1 is stated as conditional on one sealed selection (FO-03); in every claim A1 is "a bi-anchored gradient-similarity filter (external harmful anchors)"; no sentence carries A1's result to Adam-preconditioned scoring, to an a0-own query or to attribution in general (RB R7.2; AUDIT top fix 5). V2a's pre-set reading (LW-21) does not change. [LEAD, under delegation]
  Then in REC: (b) rule 5 "**F_k → L_k 1** [PROPOSED; LN-05 …]" → "**F_k → L_k 1** [LEAD, under delegation; MSG-14]" and delete its fallback clause; (c) rule 4 "[PROPOSED; LN-05: this test form; fallback: …]" → "[LEAD, under delegation; MSG-14]"; (h) rule 5 likewise; (b) rule 6 per CR-2; (g) rule 1 "[PROPOSED; LN-15 fix 5]" → "[LEAD, under delegation; MSG-16]" and add MSG-16's third clause; (a) rule 6 add "any result of A1 as a result for attribution in general (item (g) rule 1)"; Z.1 delete the LN-04 and LN-05 rows and the claim part of "LN-15 fix 5". In REV3: replace every "BR-n" with "MSG-14/15/16"; delete §0.3 item 2's last bullet.
- **Fix, option (b), if the lead does not confirm.** REV3 reverts: §4.2 "F_k → L_k 1 (… in force …; BR-1 [LEAD, under delegation])" → "F_k → L_k 1 — [LEAD-NEEDED] LN-05, recommended"; §4.3 "[LEAD, under delegation] (BR-1)" → "[LEAD-NEEDED] LN-05"; §4.4 → "[LEAD-NEEDED] LN-04" with CR-2's text as the recommendation; §9.3 item 3 → "[LEAD-NEEDED] LN-15e (claim part)"; §14.1 and §14.2 rows "closed here" → "open"; §0.5's "do not claim" A1 item → marked "recommended".
- **Decides:** the lead, W1.

### HI-2. The human label check: the two files commit different designs, and REV3's cost does not match its own design

- **Where.** REC (f) rule 7: "a sealed, stratified draw of about 450 answers from the 8 primary arms and θ0 … Per fine-tuned arm, 50 answers: 24 Qwen3Guard-Unsafe, 4 Controversial and 12 Safe harm answers, and 5 'Refusal: Yes' and 5 'Refusal: No' over-refusal answers" (from HLC). REV3 §14.2 LN-15c (and §9.4 by pointer), with LEDGER top fix 3: "strata a0, removals, additions; about 130 judge-Unsafe and 150 judge-Safe answers per stratum (MRA W6 sizes)", cost "$440–650" for two raters.
- **Evidence.** HLC (R: HLC :30, :153): "about 450 answers"; "Harm block 360 answers (8 × 40 + 40). Benign block 90." CONS LA-07 (R: CONS:1107): "Part 2 about $220–330 per paid rater, $440–650 for two (E: HR §5.3)", and "**Decides: USER**" for the design (A, B or C) and the rater route. MRA W6 sizes over three strata ≈ 3 × (130 + 150) = 840 answers (M (here)), about 1.9 × HLC's 450.
- **Why it matters.** LW-30 commits one paragraph at W1. The files would commit two designs. REV3 prices an 840-answer design at HLC's 450-answer price. Under HLC's draw the per-stratum counts are 72 Unsafe and 36 Safe for the removal stratum (A1, L1, H1) and the same for the addition stratum (S1, S3, S4) (M (here): 3 × 24 and 3 × 12), well below MRA W6's sizes.
- **Fix (recommended).** Use REC's HLC design in both files, because its cost line is the one the sources compute and it is the protocol behind LW-30 (HR HD8). Add to both: "Under this draw, each pooled stratum holds about 72 judge-Unsafe and 36 judge-Safe harm answers (removals; additions), below the reviewer's suggested 130 and 150 per stratum (MRA W6); the paper states this as a limit." In REV3 §14.2 LN-15c and LEDGER top fix 3, replace "strata a0, removals, additions; about 130 judge-Unsafe and 150 judge-Safe answers per stratum (MRA W6 sizes)" with "HLC revision 2's draw: about 450 answers from the 8 primary arms and θ0, 50 per fine-tuned arm (24 Unsafe, 4 Controversial, 12 Safe harm answers; 5 'Refusal: Yes' and 5 'Refusal: No' over-refusal answers)". Mark the paragraph [PROPOSED; LN-15c] in REC (it is not marked now). Keep the raters' pay [CONDITIONAL; rater budget] and the design and rater route as the user's LA-07 item.
- **Alternative (the ambitious default, if the lead prefers).** MRA W6 sizes as the default draw and HLC's 450 as the pre-set fallback (trigger: the rater budget covers fewer than about 840 answers), with the cost re-estimated at about 1.9 × $440–650 ≈ $830–1,240 (E (here), scaled from HR §5.3; UNVERIFIED). Then both files carry this text.
- **Decides:** the lead (rule text, W1, $0); the user (LA-07: raters, design A/B/C, spend).

### HI-3. The gate for "data repair beats model-level repair" differs

- **Where.** REC (a) rule 6: "that data repair beats model-level repair unless it beats every built reference (item (c) rule 12)". REC (c) rule 12: "'Data repair beats model-level repair' is said only if a data repair beats every built reference." REV3 §0.5 and §5.2: "only if a data repair dominates in family 1b (§5.3)".
- **Evidence.** AUDIT top fix 2 and REV3 §5.3: D_k = "beats every built reference" is an IUT; family 1b = Holm over D_1…D_6 at 5%, read after Φ. "Beats every built reference" per comparison is D_k at an unadjusted one-sided 5%, a weaker gate than family 1b's Holm (I).
- **Why it matters.** This is the claim behind the abstract's second finding (R: AUDIT top fix 2). The two files would allow it at different error rates.
- **Fix, REC (a) rule 6.** Replace "unless it beats every built reference (item (c) rule 12)" with "unless D_k is rejected in family 1b (item (b) rule 8 item 1b; item (c) rule 12)".
- **Fix, REC (c) rule 12.** Replace "'Data repair beats model-level repair' is said only if a data repair beats every built reference." with "'Data repair beats model-level repair' is said only if some D_k is rejected in family 1b (Holm over D_1…D_6 at 5%, read after Φ). Each per-reference 'beats r' result is reported per comparison."
- **Decides:** part of LN-15b (the lead), W1.

### HI-4. A decided rule (LW-11) is contradicted by a built setting, and REV3 does not list it

- **Where.** REV3 §0.4: "three switches do not yet match LW-12 and LW-13"; REV3 §7.4's table and §10.6 step 3 list X-1 to X-3 (and X-4) only. REC (k) rule 7 and Z.2 list it as X-8.
- **Evidence.** SET `selector_predict.json`: `placement.planted_primary` = "top_k_hit", `placement.planted_secondary` = "row_auc" (M: keys printed between 14:08 and 14:21 UTC). LW-11: the row AUC is primary on planted menus, the top-k hit secondary (R: LEDGER; CONS:492). LEDGER §2.2 row 4f points to X-1 for this; the right id is REC's X-8 (I).
- **Why it matters.** REQ-18's predictions freeze at W1-P. If the switch is not swapped, the frozen predictions place diagnostics by the statistic that LW-11 rejected (one top-k hit fits every grid point at M = 8; R: CONS LW-11).
- **Fix, REV3 §0.4.** "three switches do not yet match LW-12 and LW-13" → "four settings do not yet match LW-11, LW-12 and LW-13". **REV3 §7.4 table:** add the row "`placement.planted_primary`; `planted_secondary` (`selector_predict.json`) | 'top_k_hit'; 'row_auc' | row AUC primary (LW-11) | swap them before W1-P (a decided fix, not an LN item)". **REV3 §10.6 step 3:** add "the placement swap (LW-11)". **LEDGER §2.2 row 4f:** "see X-1" → "see REC X-8".
- **Decides:** decided (LW-11); the builder or the lead applies it before W1-P.

---

## 4. Medium

### ME-1. "Pre-registered": the two files give different conditions
- **Where.** REC (a) rule 9: after the commit, the paper says "pre-registered in a dated git record (commit …; manifest …)"; the public deposit is [PROPOSED]. REV3 §0.5: "'Pre-registered' needs a public, timestamped deposit (LN-15a; … [USER])"; REV3 §14.5 and LN-15a's fallback keep "pre-specified" until a deposit.
- **Evidence.** LW-26 (R: CONS:629): "'pre-specified', not 'pre-registered', until REQ-20's manifest and REQ-21 are committed." AUDIT top fix 1 item 4 recommends that "pre-registered" follow the deposit. LEDGER §2.2 row 4e calls the deposit condition "Settled", but it is a proposal (LN-15a), not a decision (I).
- **Fix.** One text in both. Recommended (I; AUDIT top fix 1): REC (a) rule 9 →
  > **"Pre-registered".** After this record and the manifest are committed, the paper says "pre-specified in a dated git record (commit [FILL AT COMMIT]; manifest [FILL AT COMMIT])". It says "pre-registered" only after an anonymized, timestamped public deposit with the same hashes, which needs the user's yes, because a deposit is a public post [PROPOSED; LN-15a]. Fallback: no deposit; the paper keeps "pre-specified".
  REV3 §0.5: mark the deposit condition "[LEAD-NEEDED] LN-15a, recommended" (not decided). LEDGER row 4e: "LW-26 decided; the deposit condition is LN-15a (proposal)".

### ME-2. The run order of the secondary arms differs (R_tok)
- **Where.** REC (g) "run in this order when funded": R_1200/R_2400 (rule 5), R+S1, DataShield-style, H2a/H2b, H1-bt, L8 octiles, **R_tok (rule 11)**, DIFFUSE. REV3 §9.1 LN-25: R_tok as "item 1b, right after the random dose curve".
- **Evidence.** BRIEF REQ-21 (g) requires "the secondary-arm order" in the record (R: BRIEF:121). UW-10 names H1-bt "secondary arm 5" (R: FOCUS 07:21 UTC).
- **Fix.** One order in both. Recommended: REV3's LN-25 (R_tok and the dose curve serve the same token axis; numbering it "1b" keeps UW-10's "secondary arm 5"). REC: move rule 11 to follow rule 5 and number it "5b" (the order is then R_1200/R_2400, R_tok, R+S1, …). Mark it "[PROPOSED; LN-25; fallback: R_tok last before DIFFUSE]".

### ME-3. How the 128-token cap is applied, and which dev-100 O is "Gate B's Ref"
- **Where.** REV3 §6.3 LN-19 (cut the engine's Gate-A-cap dev-100 answers to 128 tokens and re-judge; generate PHTest at a 128 cap). REV3 §2.2: "The dev-100 O at the Gate A cap, measured exactly as Gate B's Ref, is reported beside it." REC has no LN-19, and REC (e) rule 2 says: "Under the 128-token branch … the dev-100 O is measured at the 128 cap, so it is not Gate B's Ref."
- **Why it matters.** Under Branch 128 the files report different dev-100 numbers, and REC does not say how the 128-token answers are made.
- **Fix, REC (e) rule 5.** Add under Branch 128: "[PROPOSED; LN-19] The engine's own evaluation makes the dev-100 answers at the Gate A cap; they are cut to their first 128 new tokens and judged again, one device per contrast. The 400 PHTest answers are generated at a 128-new-token cap. The record states the route per source. Fallback: all 500 generated at a 128-token cap in a separate pass." **REC (e) rule 2**, replace the last two sentences before "Gate B's G4" with: "Reported beside the primary O: the dev-100 O under the bank's cap, and the dev-100 O at the Gate A cap read exactly as Gate B's Ref (from the engine's Gate-A-cap answers)." **REV3 §2.2**, add "under Branch 128, from the engine's Gate-A-cap answers (LN-19)". Both: state "Under Branch full the two dev-100 numbers coincide only if the full generation cap equals the Gate A cap (UNVERIFIED here)."

### ME-4. REC lacks the overlap control's rule (LS-19)
- **Where.** REV3 §9.4 (overlap control, "holds" rule, LN-26, W1). REC: absent (M: `grep` for "overlap control", "lower-similarity", "less similar half" finds nothing in REC).
- **Evidence.** PLAN-S:172 (R): "the add effect must hold on the lower-similarity half" (an approved PLAN-S rule, FR-02). CONS LS-19 (R: CONS:1011–:1016): "Its rule text goes into the W1 record (S-2)."
- **Fix, REC.** Add to item (b) (after rule 10) or to item (f):
  > **Overlap control** (PLAN-S:172; report only) [PROPOSED; LN-26; fallback: the rule text at S1, labelled "fixed after Gate B wave 1"]. For each evaluation prompt, its highest similarity to the add set (θ0 embeddings, on the pod). "Holds" means: the add contrast on the lower-similarity half has the same sign as on all prompts, and its 90% interval excludes 0. Otherwise the text says "not shown on the less similar half".

### ME-5. REV3 lacks the published priors that BRIEF REQ-21 (j) requires
- **Where.** REC (j) rule 4 (SPEC F7: DataShield-style's top-600 mean target length above the 4,800-row mean; DataShield-style's top 600 holds more than 37.5% in brainstorming, general_qa and open_qa; S3's top-48 safety rows shorter than the S3 subset; no direction for Self-Inf-N-style). REV3 §13.1 row (j) maps only §7.2, §8.5, §5.4; REV3 has no such priors.
- **Evidence.** BRIEF REQ-21 (j) (R: BRIEF:121): "the predictions: REQ-18's file by SHA-256 and the published priors as falsifiable statements about scorer outputs (SPEC F7 …)".
- **Fix, REV3.** Add a §7.5 "Published priors (REQ-21 (j); SPEC F7)" with REC (j) rule 4's text, and add "§7.5" to §13.1 row (j). Mark REC (j) rule 4 with its source, "(BRIEF REQ-21 (j); SPEC F7)", which it lacks.

### ME-6. REV3 lacks REC's X-12: the human-label draw would break block A's seal
- **Where.** REC (f) rule 7: "The draw reads block-A guard files only after block B is complete, by a script that prints totals only [PROPOSED; X-12 …]". REV3 §9.4 and LN-15c: no such rule.
- **Evidence.** LW-35 seals block A's U, HB, O, task-loss and coherence outputs until block B is complete (R: CONS LW-35). Any stratified draw by judge label reads guard outputs (R: HLC §4.3 via REC Z.3).
- **Fix, REV3 §9.4 (human label check).** Add REC's X-12 sentence and its fallback ("a0 and R at 1101–1103, already read, at block A; the method arms after block B"), with the merged id (§10).

### ME-7. REC lacks the actor menus that REV3 sets for W1
- **Where.** REV3 §9.4 LN-08 (five actors, menus, "W1 (S1 latest)"); REV3 §12.4 recommends §4.9 and §9.4 for W1. REC Z.1: "LN-08 … not REQ-21 items … if the lead adopts CONS LS-17 (a) in this record, add it to item (c)". REC (c) rule 13 states "too close to call" with no menus.
- **Evidence.** AUDIT row 6: "Fix the menus in the frozen text; PAPER's 'best repair within each actor's menu' also needs … §4.8's rule." CONS LS-17: each menu fixed "before any newly run outcome".
- **Fix, REC (c).** Add rule 13b with REV3 §9.4's actor table and rules, marked "[PROPOSED; LN-08; fallback: the two-actor menus of PAPER Table 1, fixed in this record]". Remove LN-08 from REC Z.1's "not REQ-21 items".

### ME-8. The pilot interval: neither file states LW-10's text correctly
- **Where.** REV3 §8.2: "the seed-paired t interval on 1101–1103 (J = 3, 2 df; one-sided 90% quantile 1.886)" (no prompt part). REC (g) rule 19: the same "J = 3, 2 df; … 1.886", "with a prompt part under the paired model".
- **Evidence.** LW-10 (R: CONS:477): "seed-paired on 1101–1103 (J = 3, 2 df), with a prompt part only under HB". With a prompt part, the df is Satterthwaite's, not 2, so the fixed quantile 1.886 = t(0.90, 2) no longer applies (I; M (here): t(0.90, 2) = 1.886).
- **Fix, both.** "The pilot interval is seed-paired on 1101–1103 under the primary model's form: the seed part with 2 df plus the prompt part (LW-10); its one-sided 90% quantile is t(0.90, df) with Satterthwaite df, which is 1.886 when the prompt part is 0."

### ME-9. The two files use different ids for the same open items
- **Where.** REV3 adds LN-19 to LN-28; REC adds X-8 to X-14. Same topic, different id: plan-B Φ = REV3 LN-21 = REC X-10; O-bank weights = REV3 LN-24 = REC X-11. Items in only one file: see §10.
- **Why it matters.** The lead adopts items by id; a ruling "adopt LN-21" would not find REC's text.
- **Fix.** Adopt the merged list of §10 in the LEDGER, and use its ids in both files.

### ME-10. C-full's O part after O-ext: REC says 468 prompts, REV3 says "all evaluation prompts"
- **Where.** REC (k) rule 8: "C-full: … greedy generation of all 468 evaluation prompts". REV3 §7.3: "greedy generation of all evaluation prompts".
- **Evidence.** The 468-prompt count is the wave-0a ledgers' `generate` stage (R: REV3 §10.2), before O-ext. LW-16 fixes 1 FRE = 2,934 s and C-full's stage list (R: LEDGER). With 400 more greedy answers, an arm's C-full time grows by about 400 × 3.6 s ≈ 1,450 s ≈ 0.49 FRE at the full cap (E (here), from 1,694 s / 468 prompts; UNVERIFIED PHTest answer lengths).
- **Fix, both.** "[PROPOSED; new LN, see §10] C-full holds the greedy answers of every evaluation prompt the arm answers: 468 before O-ext, 868 with the 400 PHTest prompts. 1 FRE stays 2,934 s (LW-16), so an arm costs more than 1 FRE under C-full after O-ext; the record says so." REC (k) rule 8: replace "all 468 evaluation prompts" with this.

### ME-11. The blinding texts differ; LW-08 asks for one
- **Where.** REC (m) M1–M5 and REV3 §12.1–§12.3.
- **Evidence.** LW-08: "one blinding text built from every draft's list" (R: LEDGER). REC (m) has items REV3 lacks: M3 item 13 (the selector settings committed at 918e512, 09:35:51 UTC, about 4 minutes after the A1 seal; whether a byte changed after 09:31:44 UTC is UNVERIFIED; T2 not met), M1's P(LOCALIZED) figures, Gate B's P4 prediction, the w0b-2 `steps.jsonl` training losses, and M5 (W1-18's units). REV3 §12.2 also says its writer read the 16 Oct FOCUS entries "only by their first 400 characters".
- **Fix.** REV3 §12 states: "The W1 record's item (m) is the one blinding text (LW-08). This section repeats it." Then copy REC (m) M1–M5 into REV3 §12 and keep REV3's items (14), (16), (17) and (19) as additions to REC M3. REC M3 adds REV3's (17) (the A1 claim bound applied after A1's stability figures) and (19) (δ_fam's scope set after Gate A's E values).

### ME-12. The reading of "the user's yes" for conditional items differs
- **Where.** REV3 §9.5 (part of LN-15): "for scope, the lead's recorded yes under FR-23 stands for the user's yes … A download, terms, a public post or a change to a user text still needs the user's own yes." REC (g) "Conditional candidate additions" and LW-19's default text: "runs only after the user's yes and a funding event" (literal).
- **Fix, both.** One text. Recommended: REC adds REV3 §9.5's reading as "[PROPOSED; LN-15 (yes reading); fallback: the user's own yes, literally]" in item (h) as reading 21, and REC (g)'s conditional list cites it.

---

## 5. Low

- **LO-1. Sensitivity names.** REV3 "S-0", "S-tok"; REC and LW-02 "S-HB0", "S-HB-tok". Fix: use one name in both; recommended "S-0 (AMD S-HB0 on HB-C)" and "S-tok (AMD S-HB-tok)" in REC (b) rule 4, or LW-02's names in REV3 §3.4.
- **LO-2. S-a's O and L variance.** REC (b) rule 4: "Under S-a, O and L are never pooled over arms (per-contrast Welch form)"; REC (e) rule 9 and REV3 §3.6: "V = s²_pool,O/J_m + …" (LW-33). LW-02 S-1 says the per-contrast Welch form is for the O and L "worse" tests (R: CONS:395). Fix, REC (b) rule 4: "Under S-a, the O and L 'worse' tests use the per-contrast Welch form (LW-02, S-1); O's feasibility variance against θ0 uses LW-33's form." REV3 §3.4: add the same S-1 sentence.
- **LO-3. The mark [USER].** REC: "= the user decided it"; REV3: "= only the user can decide it". REC uses it only in its Marks list. Fix: REC renames its mark to "[USER-DECIDED]" or adopts REV3's meaning.
- **LO-4. Precedence.** REV3 §0.3 lists five levels and puts MSG rows in levels 2 and 3; REC (0) item 4 lists four. Fix: one list in both: "(1) PREREG and the user's decisions; (2) the lead's rulings (LW, ADD §1–§9, MSG rows; user-delegated ones marked); (3) BRIEF; (4) the drafts."
- **LO-5. UW-19's Alpaca clause.** REV3 §7.2 omits "the 9 Oct rule 'Alpaca right after Gate B' stays" (R: FOCUS 07:21 UTC UW-19). REC (j) rule 3 has it. Fix: add to REV3 §7.2 "Llama's rules".
- **LO-6. Marks in REV3.** ADD-9/MSG-10 (REV3 §6.3) and ADD-8.2/MSG-06 (REV3 §8.4) are user-delegated lead rulings (R: LEDGER) but carry no [LEAD, under delegation] mark; REV3 §8.6 writes "(ADD-8.1, user-delegated lead)" in place of the mark. Fix: add the mark in each place.
- **LO-7. R draws.** REC (d) rule 2: d = 6–8 from `build_sealed.py`, draw 8 runs only under plan B (BRIEF REQ-21 (d): "d = 1…8"). REV3 §1.2: "d = 6–7"; REV3 §1.3 plan B names d = 9–10 only. Fix, REV3 §1.2: "d = 6–8 from the frozen `build_sealed.py` …; d = 8 runs only under plan B".
- **LO-8. LN-02's fallback.** REC: "a0 at 1101–1106"; REV3 §14.2: "—". Fix: REV3 adds REC's fallback.
- **LO-9. O-bank weights and shortfall.** REC (e) rule 2's fallback "equal source weights, 50% each" differs from REC Z.1's X-11 fallback "dev-100 O co-reported as primary"; REV3 LN-24 has no fallback, and REC lacks REV3 LN-24 item 2 (on a shortfall, the dev 100 plus all N′ eligible prompts). Fix: one fallback in both (recommended: "the dev-100 O co-reported beside the pooled O; no reweighting"); REC (e) rule 4 (iii) adds LN-24 item 2.
- **LO-10. Grade-1 error.** REC (b) rule 7: "at most 30% by a union bound" (unlabelled; M (here): 6 × 5%); REV3 §4.5: "19.8% simulated". Fix: print both in both files, each labelled.
- **LO-11. Φ's partial-null rate.** REV3 §4.2 omits AMD's "about 5.3% at worst when one noisy arm's contrast is the only true null" (R: AMD line 257); REC (b) rule 5 has it. Fix: add to REV3 §4.2 "Checks".
- **LO-12. O planning numbers.** REV3 §6.4 uses "about 1.8 pp … E (here)" and AMD's 1.00/0.97/0.80. REQ-19's sealed output gives SE 3.94 pp (100 prompts) and 1.81 pp (500), P(declared feasible at τ_O = 5) 0.35 and 0.87, and the smallest τ_O with 80% power 9.8 and 4.5 pp (M: `limits_check.json`; REC (e) rule 3). Fix: REV3 §6.4 cites the sealed values as M.
- **LO-13. REC (m) M3 item 1** says "the paired model is expected to read P4 about 0.3 pp more in S1's favour than S-a". The source computed S-a − HB = −0.28 pp under D0 (R: VR-B via REV3 §3.4), not HB-C under D1. Fix: "HB (computed under D0) is expected …".
- **LO-14. "PLANF".** REC (k) rule 13 uses BRIEF's short name "PLANF:125" but REC's Short names table lacks PLANF. Fix: add it, or cite FOCUS 8 Oct 13:53 UTC "Selector".
- **LO-15. The row note in the U part.** REC (c) rule 9 (i) lists "significant, below the smallest effect of interest" among the U-part values (as AMD §B.5 does); REV3 §4.6 item 1 writes it as a note. MSG-09: "printed in the row … not as a label". Fix: both write "U part: one of better / worse (U) / equivalent (grade) / inconclusive, plus the note '…' where it applies".
- **LO-16. The selector's built rule.** REV3 §7.2 omits that the rule and k are chosen on the equal-weight average over the two cost conventions and the τ_O points (R: SET `selector_simulate.json`, `criterion.rule`, `criterion.freeze_scope_rule`); REC (k) rule 2 has the conventions part. Fix: REV3 §7.2 copies the built rule's text; REC (k) rule 2 adds "and per τ_O point".
- **LO-17. A second stale settings note.** SET `selector_spec.json` `screen.tau_l_reference_note` still says "r = the dose-matched random-removal arm (W1-13 row 4, to GPT)"; LW-07 decided a0 (the value `tau_l_reference` = "a0" is right). Fix: add it to LN-11 / X-4 (correct the note's text in REQ-21 (h)) in both files.
- **LO-18. Stale words in REV3.** §12.3 item (1) "the approved S-a" (S-a is now a sensitivity); §5.3's heading "DRAFT §5.3" (REV3 calls revision 2 "REV2"). Fix: "the S-a sensitivity"; "REV2 §5.3".
- **LO-19. Engine Y's merge point.** REV3 §1.5: "merged after Gate B's `--final` procedure"; REC (l): "merged only after Gate B's last kit pod". Both meet FR-01. Fix: one text; recommended the later point, "after Gate B's `--final` procedure (LS-01, LS-22)".
- **LO-20. W1-18 may be dead.** The status file still reads stage "load_guard", status "running", updated 12:44:35 UTC (M: keys and values at 14:08 UTC; about 84 minutes unchanged). REC Z.3 says to check it; REV3 §0.4 does not. Fix: REV3 §0.4 adds "the status file has not changed since 12:44:35 UTC; the lead checks whether the run is alive; Branch full applies if no result is recorded at the W1 commit".
- **LO-21. a0's 500-bank re-evaluation and its cost.** REV3 §6.3 says the a0 units at 1101–1103 are regenerated for the 500 bank; REC (d)/(e) do not. AUDIT row 2c's "cost of re-evaluating θ0 and a0 on 500 prompts: not found" is still not answered in either file. Fix: REC (e) rule 5 adds REV3's sentence; both add "about $0.4 for 3 a0 regenerations (R: REV3 §10.4, $0.14 per seed) plus about $0.7 per unit for 400 greedy PHTest answers at the full cap, so about $3–6 for θ0, a0 and R at 1101–1103 (E (here), 400 × 3.6 s at $1.79/h; UNVERIFIED answer lengths); block A".
- **LO-22. Block A's money.** REC (d) rule 11 states block A as "$25–45" (PLAN-S §10, D0, before O-ext). REV3 §10.5 shows the seed-complete 20 runs alone at about $41 with contingency (E (here)). Neither file sums block A's full need (runs, diagnostics' pod passes, c0, LN-12, LN-14, the re-score, block A's share of O-ext). Fix: both label $25–45 "PLAN-S's D0 envelope (E), before O-ext", and REV3 §10.5 adds one summed line for block A.
- **LO-23. Unlabelled numbers or claims in REC.** (a) rule 5: "train about 15% more steps (38 against 33)" (M (here): 38/33 = 1.15) and "charging 1 FRE of training under-charges the add arms" (no source; C-full charges measured seconds); (b) rule 7: "at most 30%". Fix: label them, and delete or source the "under-charges" clause.
- **LO-24. "Within the over-refusal limit".** REV3 §6.5: a sentence says "within the limit" only if F_k rejects in Φ (AMD §E.5). REC has no such rule, and REC (c) rule 13's "feasible at the stated τ_O and τ_L" does not say which test. Fix: add REV3 §6.5's sentence to REC (e) rule 7, and in both files' "best feasible repair" rule write "feasible: F_k rejects at τ_O\* = 5 pp, or the per-comparison state is 'feasible' at τ_O = 2 or 10 and at τ_L, as stated".
- **LO-25. Process limits of the two writers.** REC's writer did not open PREREG, PLAN-S, AUDIT or P78 (R: REC Z.6), yet REC marks PLAN-S:118 "[FROZEN rule text]". REV3's writer read the 16 Oct FOCUS entries by their first 400 characters (R: REV3 §12.2). I checked the texts that matter: REC (d) rule 6 equals PLAN-S:118's seed rule (R: PLAN-S lines 112–128); G4's "Ref(untuned) + 5 = 22/100" (R: PREREG line 150) supports "the same number"; UW-13's item text (CR-2). Fix: none needed in the texts; REC Z.6 should say which frozen texts were checked by whom.
- **LO-26. LEDGER corrections that follow from this review** (the lead's file): add MSG-14 to MSG-16 (HI-1); C-3/LN-04 recommendation (CR-2); X-5's pod route deleted (CR-3); §2.2 row 4e (ME-1); row 4f id (HI-4); top fix 3's design and cost (HI-2); add the merged LN ids (§10).

---

## 6. The audit's contradictions (AUDIT §3): status in the two files

"Consistent" = both files hold the same text or the same open item with the same recommendation.

| AUDIT row | Topic | REV3 | REC | Status |
|---|---|---|---|---|
| 0 | the frozen text is stale | rewritten | written | resolved in substance; blocked by CR-1–CR-3 and HI-1–HI-4 |
| 1 | seeds D0 against D1; blocks | D1; LN-01 seed-complete blocks | D1; LN-01, same text | consistent; layout open (LN-01, W1) |
| 1b | B+Qi seeds | LN-03, 1102–1107, S1 | LN-03, same | consistent; open (S1) |
| 2 | the cap | one cap, two branches | one cap, two branches | rule consistent; application route and the dev-100 Ref report differ (ME-3); paper C.11 edit listed in REV3 §14.5 |
| 2b | the bank | dev 100 + 400 PHTest | same | consistent |
| 2c | τ_O\* "the same as G4" | "same number, other bank and cap" | same | consistent; the audit's missing cost is still missing (LO-21) |
| 3 | δ_fam | 1B families (BR-2) | any size (LN-04) | **inconsistent (CR-2)** |
| 4a | R1.3's "infeasible" | IUT at the node's level, decided (BR-1) | IUT, [PROPOSED] | content consistent; status differs (HI-1); SE differs (CR-1) |
| 4b | Φ's F_k edge | F_k → L_k 1, decided (BR-1) | F_k → L_k 1, [PROPOSED] | content consistent; status differs (HI-1) |
| 4c | testing order (1b, 1c) | listed; paper §4.9 edit listed | listed | consistent |
| 4d | what the labels resolve | "better" 80% effect range | same | consistent; paper §6 edit listed in REV3 §14.5 |
| 4e | "pre-registered" | needs a deposit | after the commit, "in a dated git record" | **inconsistent (ME-1)** |
| 4f | placement statistic | row AUC (LW-11); built mismatch not listed | row AUC; X-8 listed | rule consistent; REV3 misses the built mismatch (HI-4) |
| 5a | "dominates" | "beats" rule; claim gated on family 1b | "beats" rule; claim gated on "beats every built reference" | **inconsistent claim gate (HI-3)** |
| 5b | reference seeds | LN-15b, US-01 (a), S1 | same, S1 | consistent |
| 5c | Safe LoRA settings | LN-18, S1 | LN-18, S1 | consistent |
| 5d | lower-LR reference | conditional (LN-15d) | conditional | consistent |
| 5e | timing of S1 rules | LN-09 | LN-09 | consistent; paper §4.9 rewording listed in REV3 §13.2 |
| 5f | cost units; lean O part | LW-15/LW-16; LN-07 | same | consistent; C-full's O part differs (ME-10) |
| 6 | actor menus | LN-08 text at W1 | absent | **REC lacks it (ME-7)** |
| 7 | R_tok | funded-tier arm; not built | same | consistent; run order differs (ME-2) |
| 8 | disjoint anchors | rule; criteria (LN-06); download [USER] | same; adds its label (X-13) | consistent; REV3 lacks the label (§10) |
| 9 | OLMo 3 | added, not a replacement; cut order | same | consistent |
| 10 | other stale text | REV2 parts fixed; paper parts in REV3 §14.5; LN-17 | n/a | consistent |

---

## 7. The audit's top 5 fixes: status

| Fix | REV3 | REC | Status |
|---|---|---|---|
| 1. one consistent frozen text | LN-15a; deposit as the rule for "pre-registered" | (a) rule 9; deposit [PROPOSED] | blocked until §2–§4 are fixed; ME-1 |
| 2. data repair against the references | §5.3 full text (LN-15b) | (c) rule 12 (LN-15 fix 2) | text consistent except the claim gate (HI-3) and the cross-cluster prompt part (CR-1) |
| 3. measurement that reaches harm | LN-15c (MRA W6 sizes); claim-rule cases; endpoints conditional | (f) rules 2, 6, 7 (HLC design); endpoints conditional | **design differs (HI-2)**; claim-rule wording differs (below); REV3 lacks X-12 (ME-6) |
| 4. robustness of the menu | B↓LR, SR, S6 conditional; US-06 no change; menus LN-08 | B↓LR, SR, S6 conditional; US-06 a user item; no menus | menus missing in REC (ME-7); US-06 authority differs (below) |
| 5. A1's one-shot selection | claim bound in force (BR-3); re-score LN-15e; V2a | claim name [PROPOSED]; re-score [PROPOSED]; V2a | status differs (HI-1) |

Two smaller differences under fixes 3 and 4:
- **The claim rule's new cases.** REC (f) rule 2: "'Equivalent' and 'inconclusive' contrasts say 'restored refusal' in any harm sentence". REV3 §2.3: they say "only 'restored refusal' or 'no restored refusal shown', never 'harm'". An inconclusive contrast has not shown restored refusal, so REV3's wording is the correct one (I). Fix: REC (f) rule 2 takes REV3's wording.
- **US-06** (the two candidate references). REV3 LN-28 decides "no change" under the delegation; REC (l) and ADD-5.4 keep it "a user scope decision; no change until the user decides". The outcome is the same. Fix: REV3 LN-28 writes "no change, as ADD-5.4 already says; the decision stays the user's".

---

## 8. The 17 Oct lead rulings that bind both files (the brief's list)

| Ruling | REV3 | REC | Consistent? |
|---|---|---|---|
| B-1: the frozen rule per (menu, M, B); per-convention a sensitivity | §7.2 | (k) rule 2 | yes (REV3 lacks the built averaging text, LO-16) |
| REQ-19's "f"; L15 (4) keys; three decoy labels | §6.6, §7.2, §8.5 F7 | (h) rule 2, (k) rule 9, (g) rule 23 | yes |
| W1-08 (1): the pool-pins file; REQ-3's settings pin unchanged | §8.4, [LEAD, under delegation] | (g) rule 28, [LEAD, under delegation] | yes |
| Token axis: total row tokens primary; target tokens beside | §9.3 item 2, marked | (b) rule 10, (h) rule 3, marked | yes |
| Seeds D1: a0 and R 1101–1107; R_1108 not run; method arms 1102–1107 | §1.2–§1.3 | (d) rules 1, 3 | yes |
| Only A1 and Self-Inf-N-style count; text-only scorers are construction checks; if REQ-13 misses W1, only A1 | §8.4 | (g) rule 21 | yes |
| Coherence: read and flagged "fails answers end"; not a "worse" word | §3.7, §4.6 | (c) rule 11 | yes |
| "Worse (O)": proven infeasible at 5 pp AND significantly above the comparator; "feasible or undetermined" is not "worse (O)"; label from the U part; below-δ note in the row | §4.3, §4.5, marked | (c) rules 4, 8, marked | yes (the SE under it differs: CR-1) |
| One cap for the 500 bank; 128 or full; θ0 and a0 re-evaluated; G4 unchanged; both branches | §6.3 (mark missing, LO-6) | (e) rule 5, marked | yes (route and Ref report differ: ME-3) |
| Risk 44: disjoint-source anchors, chosen and sealed before the freeze | §8.6 | (i) rule 4, marked | yes |
| OLMo 3 7B Instruct added if funded; cut order 70B, 32B, OLMo 3 7B | §0.1, §14.4 | (a) rule 7 | yes |
| The `--compare` newline limit | §9.3 item 3 | (h) rule 20 | yes |

---

## 9. Frozen Gate B rules, D5 = (a) and user decisions

| Check | Result |
|---|---|
| PREREG revision 5 unchanged; engine X byte-identical until Gate B's last kit pod | Both state it. **One conflict: REV3's pod-restart route (CR-3).** |
| G4 unchanged (dev 100 at the Gate A cap; mean Ref ≤ Ref(untuned) + 5 = 22/100) | Both (R: PREREG line 150). |
| G1 per arm-run unchanged for Gate B; the arm-pooled bar is stage-1 only | Both (REV3 §3.7; REC (c) rule 11). |
| Gate B's seed rule, R draws by `gate-b-random-removal-v1`, R_4/R_5 reuse | Both. |
| PREREG's re-run rule; no re-run of a completed job | Both (REV3 §11; REC by reference). The regeneration of reused units is a stage-1 train-only job with a fingerprint check, not a Gate B re-run (I). |
| D5 = (a): P1–P6 primary; selector secondary; REQ-22 not built; the patch bounded in text | Both. Families 1b and 1c have their own α and change no P1–P6 rule. **REC's LN-04 proposal would change D5's SESOI at 7–8B (CR-2).** |
| User decisions UW-01–UW-21, FR-24 | Both, with two gaps: UW-13's reach (CR-2); UW-19's Alpaca clause missing in REV3 (LO-5). |
| Spend only as conditional on a funding event | Both: every spend item is tied to a block; nothing is paid from money in hand ($91.94, of which $83.91 is the wave-1 need; R: FOCUS 16 Oct entries). |
| [USER] items (downloads, terms, public post, user texts, the funding event) | Both keep them with the user. |

---

## 10. One merged list of the new open items (proposed ids for the LEDGER)

The LEDGER holds LN-01 to LN-18. REV3 adds LN-19 to LN-28. REC adds X-8 to X-14. Proposed: keep REV3's LN-19 to LN-28, and map REC's items to them or to new ids LN-29 onward.

| Proposed id | Topic | REV3 | REC | Action |
|---|---|---|---|---|
| LN-19 | how the 128 cap is applied | LN-19 | — | add to REC (ME-3) |
| LN-20 | seed part of θ0, a0 and cross-cluster contrasts | LN-20 | — | add to REC (CR-1) |
| LN-21 | Φ under plan B | LN-21 | X-10 | rename X-10 |
| LN-22 | O_k's edge to F_k under R1.3 (no change) | LN-22 | — | REC may list it as "no change" |
| LN-23 | who freezes stage 1 | LN-23 | — | S1; REC lists it as not a REQ-21 item |
| LN-24 | O-bank weights; shortfall | LN-24 | X-11 (weights only) | rename X-11; add the shortfall part to REC; one fallback (LO-9) |
| LN-25 | R_tok's place in the order | LN-25 | — (R_tok last) | one order (ME-2) |
| LN-26 | W1 texts moved from S1 (reference role, confirmation rule, overlap control) | LN-26 | (c) rule 12, (b) rule 8; overlap control missing | add the overlap control to REC (ME-4) |
| LN-27 | S1 lead items (LS-01–LS-23) | LN-27 | — | S1 |
| LN-28 | other S1 user-scope items under the delegation | LN-28 | — | S1; US-06 wording (§7) |
| LN-29 | the placement swap in `selector_predict.json` | — | X-8 | decided (LW-11); a fix, not a choice (HI-4) |
| LN-30 | the manifest and record commit order | — | X-9 | add to REV3 §10.6 step 4 |
| LN-31 | the human-label draw and block A's seal | — | X-12 | add to REV3 (ME-6) |
| LN-32 | the disjoint-anchor draw label | — | X-13 | add to REV3 §8.6 under LN-06 |
| — | seed 1101 cells absorbed under HB-C | §3.2 (I) | X-14 | a statement, no id needed |
| LN-33 | C-full's O part after O-ext | — | — | new (ME-10) |
| LN-34 | the human-label-check design (HLC against MRA W6 sizes) | LN-15c | (f) rule 7 | one design (HI-2) |

---

## 11. Verified as consistent (no action)

I checked these against the sources or re-derived them (M (here) unless marked):
- **Φ.** Start weights; every passing row; the local levels under both F_k rows (0.75%, 0.042%, 0.375%, 0.135%; after U_k and F_k 0.135%/0.510% under the R1.3 row and 0.323% under the standard row; 0.79% for a second U); LN-22's 4/15 share and 0.217% against 0.253%; plan-B Φ's weights, row sums and start levels (1.5%, 0.083%). The scripts `phi_levels_check.py` and `phi_planb_check.py` use the standard Bretz update; their outputs match my hand values.
- **τ_L.** s from the three a0 task losses = 0.0023749 nats; τ_L = 0.0067171; √2·s; s·√(1/3); the 2-df figures (95% interval for σ/s 0.52–6.28; P(s < 0.5σ) = 0.221; P(s < σ) = 0.632); τ_L / SE = 4.90; 0.43% of the a0 mean loss.
- **Costs.** 1 FRE = 2,934 s = the median job slot (48.9 min) ≈ $1.459 at $1.79/h; training 7.6–8.4% and generation 80–82% of the engine time; c0 ≈ 870 s ≈ 0.30 FRE; LN-07's ≈ 2,300 s ≈ 0.79 FRE and ≈ $1.14; block A 20 × $1.459 ≈ $29, + 5 pods ≈ $33, × 1.25 ≈ $41; block B ≈ $35, $40, $50; slack $8.03.
- **Seeds and blocks.** 50 cells, 44 new; block A 18 + 1 + 1, block B 18 + 3 + 3; plan B's third block 15 runs; steps 38/33/38.
- **Sealed records.** A1's 600 rows, 18.7%, 68,483 / 442,329 = 15.5%, 114.1 against 92.2 target tokens; FO-04's figures; REQ-19's 11.04 / 1.32 pp (and 11.01 / 1.08 at 9 seeds); W1-05's 171/200 and 13/100; the source hashes in both Short names tables equal the files at HEAD (FOCUS `e85d0a66…`, ADD `62f83d69…`, REV2 `9ff29fc1…`, PREREG `5c97cce7…`, `labels.json` `6d1415bd…`).
- **Rules.** R1.3's nulls copied from AMD §B.3; the O_k/L_k/F_k table; the label partition; equivalence grades 1 and 2 (98.33%; 96.67% under plan B); the "beats" bounds and the curve rule; the pilot gate thresholds; the plant cells, leaf rule and R600/R150 parts; the decoy rule; the S-pool rule; the O-ext draw rule (ADD §7); τ_O grid; τ_O\* = G4's number; the coherence flag; the counting rule; the token-axis definitions; the selector's spec, keys, CRN, c\*, quality grids, and the screen's `upper_quantile` 0.95 (LW-06).

---

## 12. Process record

- **Commands run (all exit 0).** `date -u` (14:08:54, 14:21:15, 14:22:21 and 14:26:17 UTC); `ls`, `wc -l`, `shasum -a 256` on this folder and on the main-checkout sources; `git log --oneline -8`, `git status --short`, `git rev-parse HEAD` (`3536776`) and `git status --porcelain` on the cited sources (clean); `grep -rln "BR-1"` over `.ai/briefs`, `research/experiments/2026-10-17-*` and `tmp/gi-vi-parallel/` (no hit outside REV3); `grep -n`, `sed -n`, `awk` and `cut` reads of FOCUS (lines 72–91), ADD (§5–§9), BRIEF (REQ-20, REQ-21), CONS (UW-04, UW-05, UW-13, LW-01–LW-04, LW-09–LW-11, LW-26, LW-30–LW-35, LS-19, LA-07), EXTR (W1-02, W1-03), AMD (§A.8, §B.2–§B.5, the validity figures), VR-B (V-3, V-8), PREREG (G4, the re-run and pod-operation rules), PLAN-S (lines 112–128, 168–175), P78 (margin and decision H lines), HLC (design sizes), RB (R5b.2, R7.2, R8.1) and AUDIT (§2–§5); `/usr/bin/python3 -I` one-liners that printed only keys and scalar values of the W1-18 status file, SET `selector_predict.json` (placement keys), `selector_spec.json` (`screen` keys), `selector_simulate.json` (`criterion` and ρ keys) and S1OUT `req19/limits_check.json` (numeric keys); `cat` of `phi_levels_check.py` and both check outputs. Two heading lists were written to the session scratchpad for a side-by-side compare (headings only).
- **Read in full:** LEDGER, REV3, REC. **Read in part:** the sources listed above. **Not read:** REF in full, RB in full, the mock reviews, LLB (as REC, to keep its writer's blind line; not needed here), CK-TM, PAPER.
- **Not opened:** `selector.jsonl`, `hidden/`, any held-out file, any `rows.jsonl` or `groups.json`, any file with row, prompt, answer, anchor or lexicon text.
- **Limits.** I re-ran no simulation and read no code path beyond settings strings and one rule string of `spec.py`. I could not verify BR-1 to BR-3's source (HI-1). The HB-C MDE under D1 is still not computed by anyone. Costs marked E (here) are my arithmetic on the sources' figures; PHTest answer lengths are unmeasured. FOCUS changes often; cite its entries by title and time.
- **Files written:** this file only.
