# Verify report: review B draft rulings (`review-b-rulings-DRAFT.md`)

**Status.** Adversarial verification for the main-study lead (General Implementation VI). It adopts nothing. It authorizes no run, spend, download or agreement, and changes no frozen rule.

**Who and when.** An Opus worker, 16 Oct 2026 from 22:56 to about 23:25 UTC (17 Oct IST). Clock checked with `date -u` at 22:56, 23:12, 23:18 and 23:21 UTC.

**What I did.** I checked each claim of the draft against its source, recomputed the costs and two power figures, and checked the deadlines, the frozen Gate B rules, D5 = (a), the lead-decisions addendum (ADD) and the scope of the analysis-model workflow. I applied every fix in place in the draft, tagged **[VF-n]**, and added the draft's §9 "Verify changes".

**Data rules kept.** I opened no `selector.jsonl`, `hidden/`, held-out file, or wave-0b `rows.jsonl` or `groups.json`. I printed no row, prompt, answer, anchor or lexicon text. I read FOCUS's 16 Oct entries (as the task asked) and CK-EM §7, so I saw the Gate B values they hold; this report repeats none of them (see VF-3).

**Labels.** **R** = read in a source (source given). **M** = measured or computed here (script given). **E** = estimate (basis given). **I** = inference or judgement. **UNVERIFIED** = not checked. **[LEAD]**, **[USER]**, **[USER-CONFIRM]** as in the draft. Severity: **Major** = a wrong rule, a missed conflict with a frozen or decided rule, or a scope overlap; **Moderate** = a wrong mark, deadline or cost that would mislead a decision; **Minor** = wording, precision or citation.

**Short names.** As in the draft. Also: **A-CHK** = `tmp/gi-vi-parallel/stage1-analysis-model/check-W3-W4-W12-W13.md` (the analysis-model workflow's check note on review A W3, W4, W12, W13); **A-W11** = `…/stage1-analysis-model/check-W11-other.md`; **ENG-Y** = `tmp/gi-vi-parallel/icml-78b-prep/engine-round-Y-design.md`; **REVA** = `writing/paper/2026-10-17-mock-review-A-methods.md`.

---

## 0. Verdict in brief

- **The draft is mostly sound.** Almost every R claim matches its source, and every cost taken from the three check notes is copied correctly. Its §6 totals recompute to $97–155 and $48–77 (M: `verify_sums.out`), against the draft's $98–155 and $48–77.
- **Gate B's own HarmBench and over-refusal definitions do not change** anywhere in the draft (R: PREREG §3, §6; draft R5c.1). I made this explicit in item 1, R1.4 and R5a.4 (VF-14).
- **D5 = (a) holds:** P1–P6 and Holm over 6 stay; the new family P7–P8 sits outside it; selectivity stays report-only (R: FOCUS 16 Oct 12:15 UTC). One framing error on the one-shot patch is fixed (VF-11).
- **Nine major findings** (VF-1 to VF-9). The largest: item 1 and W7 overlap review A W12, which the analysis-model workflow owns, and that workflow's check notes already disagree with this draft on the O error model and on the "worse on O" fix (VF-1, VF-2). Also: an inaccurate blinding line (VF-3); a fallback that breaks the user's 9 Oct item (6) (VF-4); a label-registry timing that breaks ADD L13 (3)'s test (VF-5); a post-outcome label switch (VF-6); a missing OLMo 3 noise block (VF-9).
- **Ten moderate and eleven minor findings**, all fixed in place.

---

## 1. Findings

### Major

**VF-1. Scope overlap with the analysis-model workflow (item 1 and W7).**
- Draft: R1.1 (NI feasibility), R1.2 (bound convention), R1.4 (primary τ_O\* = 5 pp), R1.8 (prompt convention) and R5b.1 (the U8 trigger) are written as rulings.
- Source: review A W12 asks for the same items: an NI bound, a larger bank or no τ_O = 2, and the precedence of "feasible" and "worse on over-refusal" (R: REVA W12). Review A W4 asks for "one primary τ_O" (R: REVA W4). The task assigns A W2–W5 and W12 to the analysis-model workflow.
- Evidence of a live conflict (R: A-CHK §3.4–§3.5, §4.5–§4.7): A-CHK recommends a bank-conditional O limit as primary ("on these 100 prompts", seed noise only), and a margin m_O for "worse on O" inside one closed graphical family Φ. The draft recommends prompt clustering and R1.3 (NI failure against θ0 and a worse comparator). The two agree on one bound for labels and the selector screen, and on τ_O = 5 pp as the primary bar.
- Fix applied: a boundary note in the header and in item 1; R1.1, R1.2, R1.4 and R1.8 marked as inputs to the analysis-model draft (new AMD-8; AMD-2 extended); conflicts C-i (error model) and C-j ("worse on O" fix) added to §5; Q10 added. The review-B-specific parts stay as rulings: θ0 for O and a0 for L, R1.3's content [USER], R1.5–R1.7, the bank options, in-domain refusal and partial refusals.
- Why it matters (I): without one reconciliation, REQ-21 (c) and (e) can receive two incompatible O rules at W1.

**VF-2. R5b.1 pre-empted the error-model choice.**
- Draft: "The paired per-prompt value decides U8" [LEAD].
- Source: A-CHK §4.5 shows the two readings give opposite U8 outcomes (about 2 pp seed-only, about 11 pp prompt-random) and says REQ-19 must fix its error model before it runs (R). CK-OR §4 gives the same two numbers (M).
- Fix applied: REQ-19 still computes both; the value that decides U8 is the one that matches the single O error model the lead fixes for the labels, REQ-16 and REQ-19, before REQ-19 runs. The draft's recommendation (prompt-random, because PLAN-S:197 asks for "the paired ΔO SE") stays as a recommendation. U-3 now opens only under that model.

**VF-3. The blinding line (R0.3) was inaccurate.**
- Draft: "The other two check notes and this file read no Gate B value."
- Source: all three check notes and the draft cite FOCUS's 16 Oct entries, which hold the noise-gate values and the sealed Gate C rankings (R: CK-OR §5.4; CK-TM "Sources read"; CK-EM §3.4 and its 16 Oct 13:21 citations; draft §8 "Read"). CK-EM §7 writes one wave-0a R arm's aggregate counts into the note, including its over-refusal count; the drafting worker read CK-EM in full (R: draft §8), and so did I.
- Fix applied: R0.3 now lists three facts for REQ-21 (m): the print; that every CK-EM reader saw those counts, so item 1's and W7's over-refusal rules were drafted after one wave-0a R arm's over-refusal count was seen; and that every review-B worker read FOCUS's noise-gate values and sealed rankings (already listed as seen by ADD §3 (4)). No value is repeated.

**VF-4. R8.1's fallback broke the user's 9 Oct item (6).**
- Draft: R0.2 calls the per-row classifier scorer "a listed commitment", yet R8.1's fallback records it as post-Gate-B exploratory if not ready.
- Source: item (6): if the listed commitments ("every stage-1 scorer's code and settings hash, …") are not committed in time, wave 1 waits; item (9) gives the exploratory exception to DataShield-style and Self-Inf-N-style only (R: FOCUS 9 Oct 19:37 UTC). The content classifier is in PLAN-S §5.4's scored-only list (R: PLAN-S:168) and in §6's planted ranks (R: PLAN-S:181).
- Second point: "about $1 on a planned pod". The only planned pods with money are Gate B's, and the Gate B kit cannot change until its last pod (R: BRIEF T4). So the run needs a stage-1 pod and new money.
- Fix applied: R0.2, R8.1, §0, §1, §4 corrected; new U-19 [USER] for an item (9) extension; run money marked [USER].

**VF-5. Labels appended at W1 would fail ADD L13 (3)'s test.**
- Draft: §4 REQ-2 row appends `stage1-sr-k0-v1`, `stage1-sr-k-v1`, `stage1-s6-v1`, the O-ext H label and V2a's label at W1, while their code is S1.
- Source: L13 (3)'s scan test "fails on … a registry entry that no code uses" (R: ADD L13 (3)).
- Fix applied: the W1 rule text names the labels (REQ-21 (g)); each registry entry is appended in the same commit as the code that uses it (append-only, L13 (7); ADD §4 item 1 keeps settings files valid). Names follow L13 (1)'s pattern.

**VF-6. R1.5 allowed a label switch after outcomes.**
- Draft: "A later switch is then a disclosed deviation, not a post-hoc choice."
- Problem (I): a switch of the primary label rule after stage-1 outcomes are read is a post-hoc choice, disclosed or not.
- Fix applied: a switch is allowed until the stage-1 freeze, before any stage-1 outcome is read; after that, the 18:31 UTC rule stays primary and R1.3 stays a sensitivity.

**VF-7. R0.1 did not say when the funding "yes" may come; per-item timing was inconsistent.**
- Problem (I): a pre-registered conditional arm whose run is decided after stage-1 outcomes are seen is chosen by outcome. FOCUS 8 Oct 13:53 UTC: "Every stage starts on a funding event, never on an outcome" (R).
- Inconsistencies (R: draft): R0.1 put B↓LR, HB-4 and the prefill probe in the W1 record, while R3.4, R5c.4 and R5a.4 gave them S1 only.
- Fix applied: the yes must come before any stage-1 outcome is read; B↓LR's W1 entry is optional (references are S1 items, BRIEF "Out of scope"); HB-4's and the probe's rule text at W1, their code and runs at S1.

**VF-8. U8 had no W1 fallback; one cost case was missing; Gate B's dev-100 O was not protected in words.**
- Source: BRIEF U8's second branch: "record O-ext as post-Gate-B exploratory and keep τ_O on 100 prompts" (R). CK-OR §5.2 makes the 128-token cap conditional on the truncation check (R).
- Fix applied: if the user is silent at W1, F applies; if the truncation check fails, H or N costs about $40–70 at the 2,048 cap (E: 400/1,469 × CK-OR's $146–256; `verify_sums.out`); the dev-100 O, measured as Gate B measures Ref, is always reported alone beside the pooled 500.

**VF-9. OLMo 3 cannot be chosen on 20 Nov by REPLAN's rule without its own noise block.**
- Source: the 20 Nov gate reads the 7–8B noise reading (R: REPLAN §7 decision 2); the noise block pairs R_1–R_3 with existing a0 seeds (R: REPLAN §2.2); OLMo 3 has none. CK-EM §5.2 notes this for option (c) only (R).
- Fix applied: for (b) or (c), block 0 also runs OLMo 3's noise block (a0 at 1102–1103, R_1–R_3), about $17–33 (E: 5 arms at REPLAN's $2.8–3.6 × 1.2, up to the noise block's implied rate of about $5–6.7 per arm; `verify_sums.out`). Added to R9.3, R9.4's cost line, §0, U-14, §6 and Q11. U-14 also mixed the lead's recommendation (b) into the "default" column while the relayed rule's default is (a); the columns are now separate.

### Moderate

**VF-10. R3.3 "settles paper decision 10" as [LEAD].** Decision 10 sits under "Decisions the author must make" and asks to "Confirm this wording" (R: PAPER decision 10). Fix: [LEAD] drafts; the decision is [USER] (new U-20).

**VF-11. U-11 framed the D5 = (a) state as the fallback.** D5 = (a) says the one-example patch is "bounded in text (related work and a limitation), not built" (R: FOCUS 16 Oct 12:15 UTC; BRIEF D5-7). ADD §5 item 4 makes adding it a user scope decision; PAPER decision 27 sets the deadline "before stage 1 is frozen" (R). Fix: U-11 and R4.8 state the standing state first, the addition as the question, no recommendation, deadline S1.

**VF-12. R8.4 placed the classifier "by its measured row AUC (A-W11 F3)" with "c_d from its measured cost".** ADD L15 (7) names the planted top-k hit as the placement statistic, and "the quality is never fitted" (R); A-W11 F3 proposes to replace it and is not adopted (R). FOCUS's D5 entry keeps predictions as curves in c_d/c0 (U3 (a)) (R). Fix: placement by L15 (7) unless the lead adopts F3 (new C-k); c_d as a point on the curve.

**VF-13. RQ.3 called dropping Qwen "the user's budget choice of 7 Oct".** FOCUS 7 Oct 17:44 UTC records the Qwen2.5-7B collapse and the user's request for sturdier families; 20:58 UTC records "Llama/OLMo only" and "No more Qwen spend" (R). No budget reason is recorded; CK-EM §5.3's phrase is an inference that contradicts its own §0 ("after it saturated"). Fix: the recorded reason.

**VF-14. Gate B protection was implicit.** R1.4's "one bar holds from Gate B to stage 1" could be read as a change to G4. G4 is a point-estimate guard on the mean of a unit's arms (R: PREREG §3); Ref's denominator and invalid rule are in PREREG §6 (R). Fix: an explicit "Gate B stays as frozen" note in item 1; R1.4 shares only the value; R5a.4's HarmBench is the Gate B pipeline unchanged.

**VF-15. SR's engine field.** ENG-Y's plan of record puts B+Qi in a round named X′ (or Y under its split rule), with about 0–4 days of slack before block A (R: ENG-Y §0, A2). SR's field edits `parse_edit`'s exact-key checks, so it is not insert-only and needs ENG-Y §5.4's training-only route (R: CK-TM §3.2; fit UNVERIFIED). Fix: R4.1 states both limits; R4.3 fallback 2 already covers a late field.

**VF-16. The build-load note misread ADD L1.** L1's split covers Parts E and F only, and only "if usage runs short" (R: ADD §1 item 1, L1). REQ-23 (Part C) and REQ-25 (Part G) fall to the single builder. Fix applied.

**VF-17. New configs and the Gate B pack.** The pack refuses while `git status` shows a change under `experiments/` (R: BRIEF Facts "Pack check"; T3), and W1 code stays outside `experiments/safety_selection/` (R: BRIEF "W1 code rules"). Fix: B↓LR's config and V2a's S′ are committed by explicit path after Gate B's last kit pod, before the stage-1 freeze.

**VF-18. V1's deadline is nearer than it looks.** The T1 bundle was verified at 21:20 UTC and waits only for its commit (R: ADD §4; no T1 commit in the main checkout's `git log` at verification, M). The lead's real A1 run then reads `rows.jsonl`. Fix: send V1's rule text to the lead now; if it lands later, REQ-21 (m) says so.

**VF-19. U-12's deadline and the plant's headline wording.** REQ-8's settings file is in the T1 bundle (R: ADD L1), so a plant change after the T1 commit re-opens T1. A-W11 F1 says the new wording of headline item (2) goes "to GPT and the user" (R). Fix: deadline "before the T1 commit"; headline wording [USER].

### Minor

- **VF-20.** HEAD moved from `32827af` to `778c464`, which commits REF-DRAFT revision 2 byte-identical to the tmp copy (M: `git log`, `diff -q`). Header and short names updated; A-CHK added.
- **VF-21.** The cached Qwen3Guard-Gen-4B snapshot directory is `6ec42827da0c…`, equal to recipe S's guard pin (R: cache listing; `study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json`:95). "UNVERIFIED" narrowed to "file hashes not checked".
- **VF-22.** "two families, one of them current" was in quotation marks but is not REVB's wording; now a paraphrase. "About a sixth" of (a)'s cost is 0.12–0.16 (M), so "an eighth to a sixth".
- **VF-23.** R7.1: PLAN-S:174's reason is "it needs selector-split outcomes" (R), not the draft's reason; and "selects without the evaluation judge" conflicted with R7.3's Qwen3Guard check. Both made exact.
- **VF-24.** §6 totals: stated what they include (SRJ on pods, V2a) and exclude (HB-4, the one-shot patch, $1–3 of train-only re-runs of reused units, the $30–43 extra if the 128-token cap fails). Recomputed $97–155 and $48–77 (M).
- **VF-25.** BRIEF REQ-21 (j) holds predictions only (R). The SRJ and prefill pre-set readings moved to (f).
- **VF-26.** CK-OR U-3's τ_L ≈ 0.0071 uses losses rounded to three decimals (R: CK-OR §9); REF-DRAFT's 0.0067171 is the value of record (R: REF-DRAFT:407).
- **VF-27.** REF-DRAFT LQ36 also takes O's SE "from the arm's seeds" (R: REF-DRAFT:380); added to C-b as part of C-i.
- **VF-29.** REF-DRAFT keeps U4's items [LEAD] under the user's "stop asking me for approval" instruction (R: REF-DRAFT Marks and :518); the draft marks R1.3 and R1.4 [USER]. Recorded as C-l, with the recommendation to keep [USER]: the lead read that instruction as "do the planned steps" (R: FOCUS 16 Oct 19:08 UTC), and a label amendment is not a planned step (I).
- **VF-32.** R5b.3's "a 128-token cap equals a cut of the 2,048-cap answer" holds only with the same batch and kernels (I; UNVERIFIED); qualified.
- **VF-33.** R5a.3 was listed as "now, at $0" but needs U-7's download first; noted.
- VF-28, VF-30 and VF-31 were merged into VF-5, VF-4 and VF-24.

---

## 2. The checks the task named

**(a) Claims against sources.** I checked the R claims ruling by ruling against the sources they cite. The wrong or loose ones are VF-3, VF-10, VF-11, VF-13, VF-22, VF-23 and VF-26. Section 3 lists what holds.

**(b) Costs.** Every figure copied from CK-OR, CK-TM and CK-EM matches its source. Recomputed (M, `verify_sums.out`): §6 totals; R4.2's MDEs (Holm over 6: add 5.32, removal 4.98 pp; over 8: 5.47, 5.12; over 2: 4.72); R1.8's 11.7 pp; R5c.3's 2.39; R3.7's $12–14 (2 × 3 × $1.6–2.0 × 1.2 = $11.5–14.4); R5b.2's 969 hidden prompts left (1,369 − 400); the slack $8.03 ($91.94 − $83.91). R4.7's "$6–7" is $5.7–6.2 before judges and $6.0–6.8 with them (E); left as is. Missing costs added: VF-8, VF-9, VF-24.

**(c) Deadlines.** W1 = before wave 1 (latest start 27 Oct), S1 = before stage-1 block A (3 Nov), 7–8B freeze about 20 Nov, block 0 by 9 Nov: all R in REPLAN §5. BRIEF:5 defines W1 and S1 the same way (R). Fixed: VF-7 (per-item timing; the funding yes), VF-18 (V1 before the first real `rows.jsonl` read), VF-19 (plant before the T1 commit), VF-9 (OLMo 3 noise block by 9 Nov), VF-11 (one-shot patch by S1), VF-2 (error model before REQ-19 runs).

**(d) Frozen Gate B rules.** No ruling changes PREREG §3 or §6. HB-1 keeps the HarmBench pipeline byte for byte: model `cais/HarmBench-Mistral-7b-val-cls` @ `51182c7c…`, template, tokenizer, `NUM_TOKENS = 512`, `MAX_INPUT_TOKENS = 2048` (refuse, never cut), label rule, one device per contrast (R: `scripts/gate_b_mac_judges/harmbench_files.py`:11–19, :58–59, :180–184; PREREG §6 "Judge devices"; FOCUS 8 Oct 10:14 UTC). Ref (denominator 100, invalid = not refused) and G4 (22/100, point estimate) are untouched; O-ext and the NI bounds are stage-1 additions. The R5b.3 Mac checks read only Gate A and development units (M: `or_labels_check.out` lists 11 units, none a Gate B arm). Made explicit by VF-14.

**(e) D5 = (a).** P1–P6 primary, Holm over 6 at 5%, SESOI 5 pp, the selector secondary and model-based, REQ-22 not built, the held-out selector comparison a later study, the one-example patch bounded in text (R: FOCUS 16 Oct 12:15 UTC). The draft keeps all of these: P7–P8 sit in a new family (R4.2), selectivity stays report-only (R1.6), no REQ-22. Placement (A) of R4.2 would change "Holm over 6", so it stays [USER] as CK-TM §3.6 says. Fixed: VF-11.

**(f) The addendum.** Consistent with L1 (fixed VF-16), L8 (wording made exact in R4.4), L9 (H's draw as a counts-only lead run), L13 (fixed VF-5), L15 (fixed VF-12), L16 (τ_L threshold only frozen; R1.1's L-bound SE from pooled residuals), §3 (seed rule "does not apply" reasoning reused in R3.5; "Records to add" (2) in R8.2; (4) in R0.3), §4 (labels pin by used entries; T1 timing, VF-18, VF-19) and §5 (item 2's pattern for V1; item 4 for U-11).

**(g) The analysis-model scope.** Overlap found and fixed (VF-1, VF-2). The other pass-alongs (AMD-1 label order and Holm membership; AMD-3 separation and winner's curse; AMD-4 frontier; AMD-5 the new family's order and seed rule; AMD-6 B+Qi warmup; AMD-7 dose) correctly stay with that draft. R4.2's "read after the primary family at its own 5% level" is a recommendation; AMD-5 owns the order (I).

---

## 3. Checked and correct (no change)

- **Hashes (M):** all eight sources match the draft's prefixes at verification.
- **FOCUS (R):** 8 Oct 13:53 UTC (θ0 and τ_O grid; judge rule "never by Qwen3Guard"; O-ext "never from the hidden remainder"; "post-Gate-B exploratory"; scale ladder at 12:53 UTC naming OLMo-2-32B); 8 Oct 18:31 UTC ("worse" label); 9 Oct 09:29 (Qwen stays out), 09:40 (PKU for add repairs), 19:37 UTC items (6), (9), (10); 10:14 UTC (512-token window approved); 16 Oct 13:21 (wave-1 need, 0.077 h retrain), 19:08 (balance, idle rate), 12:15 UTC (D5).
- **PREREG (R):** line 94 (anchor prompts; largest Jaccard 0.32), line 95 (safe answers kept by a Qwen3Guard Safe label), §3 G4 (22/100), §6 (Ref, HarmBench, judge devices).
- **PLAN-S (R):** :105, :114–119 (family, labels, seeds, plan B), :123–124, :127 ("adverse (upper 90%)"), :168 (content classifier scored only), :171, :174, :177–181, :197, §10 ($56–98).
- **BRIEF (R):** "Inputs fixed" (plant committed unfunded, PLANF:123), Facts (A1's per-row fields incl. `adam_score`; engine identity excludes configs), "Out of scope" (references S1), T1–T4, REQ-16 to REQ-21 contents, U1–U9 (U4 and U8 as described).
- **RS (R):** B10 = the "evaluate a saved adapter" script; B15 = stage-1 kit; B16 = stage-1 reading.
- **REPLAN (R):** §2.2 MDEs and noise-block design; §5 dates; §6 money; §7 decisions 2, 3, 6.
- **PAPER (R):** §3.2 point-estimate feasibility and TOST at 90%; §4.2 "Standard errors are clustered by prompt"; lines 525 and 697 (the false anchor sentence); decision 10; decisions 26 and 28 quote the relayed rule exactly; decision 27; risk 2.
- **REF-DRAFT (R):** LQ36 and LQ39 (one-sided upper 90%), LQ38 option (a), LQ43, LQ44, §L.4 (τ_L 0.0067171; recipe G's +0.067, about 10 τ_L), R.2.6 (B+Qi seeds 1101–1106, matching R3.5's choice for B↓LR).
- **Check notes (R):** every number the draft cites from CK-OR (§2.1–§2.5, §4, §5.1–§5.6, §6.4–§6.5), CK-TM (§2.1–§2.6, §3.1–§3.7) and CK-EM (§1.1–§1.5, §2.2–§2.5, §3.1–§3.3, §4.1–§4.4, §5.1–§5.3). C-g holds: `or_labels_check.py`:101 computes the "NI power" with `se66` while printing it next to "SE(6 vs untuned)" (R).
- **Web (R, read by me on 16 Oct about 23:00–23:08 UTC):** the allenai Olmo-3 listing has 31 ids, sizes 7B and 32B only, and an `Olmo-3.1-32B-Instruct`; the `allenai/Olmo-3-7B-Instruct` card states support in transformers 4.57.0 or higher and Apache 2.0; `google/gemma-2b` is gated "manual", licence "gemma", revision `9cf48e52…`; `qylu4156/strongreject-15k-v1` is not gated, has no licence field, base `google/gemma-2b`, revision `4bd893d3…`; `cais/HarmBench-Llama-2-13b-cls` weights total about 26.0 GB and the repo is not gated.
- **Local (R, names only):** the HF cache holds Qwen3Guard-Gen-4B and the HarmBench Mistral classifier, and no Gemma-2B; `tmp/judge-models/` holds Granite only.

---

## 4. Limits of this verification

- A-CHK is the analysis-model workflow's check note; its draft did not exist for me to compare. Further overlap may appear when it does (I).
- I did not run any Mac check, read any `generations.jsonl` or guard file, or re-measure any rate. Costs stay E.
- I did not re-check the web facts of CK-TM (OpenAI, Foundry, arXiv) or CK-OR (XSTest, OR-Bench, PHTest, Qwen3Guard report). I re-checked only the five HF items above.
- I did not open REQ-6's record to see whether it holds the PKU `line` and companion index (still UNVERIFIED).
- I did not verify the lead's "review-B list" numbering (items 1–9); I took the draft's scope line as given.

---

## 5. For the lead

1. **Reconcile C-i and C-j once, for both workflows, before REQ-19 runs** [LEAD; the label change itself USER]. My view (I): the prompt-random reading matches PLAN-S:197's "paired ΔO SE" and U's clustering, so it is the better default; but it makes τ_O = 5 unresolvable on 100 prompts unless O-ext runs, so its honest companion is U-3. If money for O-ext is unlikely, the bank-conditional reading with "on these 100 prompts" in every O sentence is the cheaper, also defensible choice.
2. **Send V1's rule text (R7.4) and any plant question (U-12) before the T1 commit** (VF-18, VF-19).
3. **Build REQ-23 before W1**; it is small, and item (6) makes wave 1 wait for it (VF-4).
4. **Decide whether OLMo 3 is a real 20 Nov option.** If yes, add its noise block to block 0 (VF-9).
5. **Fill REQ-21 (m) with R0.3's three facts** (VF-3).

---

## 6. Process record

**Files written** (all under `/Users/spiderishi/Coding/attribution/.claude/worktrees/kind-hawking-a6ce04/tmp/gi-vi-parallel/stage1-review-b/`):
- `review-b-rulings-DRAFT.md`: fixes in place, tagged [VF-n]; new §9 "Verify changes".
- `verify-report.md`: this file.
- `verify_sums.py` and `verify_sums.out`: the money and power arithmetic (no data read).

**Commands run (all exit 0).**
- `date -u` (22:56, 23:12, 23:18, 23:21 UTC).
- `ls`, `wc`, `cat -n`, `sed -n`, `grep`, `awk`, `fold` and `cut` over the draft, the three check notes, `or_labels_check.py/.out`, `ni_power.py/.out`, FOCUS, PLAN-S, PREREG, BRIEF, ADD, REPLAN, PAPER, REVA, REVB, REF-DRAFT, A-CHK, A-W11, ENG-Y, RS and `scripts/gate_b_mac_judges/harmbench_files.py` (selected lines).
- `shasum -a 256` of the eight sources; `git branch --show-current`, `git log` and `git show --stat` in the main checkout; `diff -q` of the two REF-DRAFT copies.
- `grep` of recipe S's guard revision; `ls` of the HF cache and `tmp/judge-models/` (names only).
- `python3 -I verify_sums.py`.
- One `grep -rn -o -E "REQ-(2[3-9]|3[0-9])"` over the sibling folders: no other draft uses REQ-23 or above yet (M). An earlier form of that command failed under zsh globbing (`--include=*.md`, "no matches found"); I re-ran it without the glob.

**Web reads (WebFetch).** HF API: allenai Olmo-3 listing; `google/gemma-2b`; `cais/HarmBench-Llama-2-13b-cls` (file list); `qylu4156/strongreject-15k-v1`. HF card: `allenai/Olmo-3-7B-Instruct`. No phrase from these pages is quoted here.

**Not opened.** `selector.jsonl`, `hidden/`, any held-out file, wave-0b `rows.jsonl` or `groups.json`, any generation, guard or summary file, any PKU file, the anchor bank.

**Not done.** No run, pod, spend, download, install, commit, push, message or agent. No repository file changed.
