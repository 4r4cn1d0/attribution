# Statistics review of the stage-1 pre-registration draft (revision 1)

**Adversarial review for the main-study lead (GI VI). Read-only. It changes no file but this one and its two check scripts.** Target: `stage1-preregistration-DRAFT.md` in this folder (SHA-256 `c9554f0210ad1f5e…`, 926 lines, unchanged since 00:48 UTC). Written 2026-10-17 from 01:17 UTC (clock checked with `date -u` at 00:55, 01:15 and 01:17 UTC). Scope: the analysis model (estimator, SE, df, the per-arm variance check), the testing family's error control, the labels' mutual exclusivity, the margins and power, the reference tests, the over-refusal non-inferiority rule, and outcome-dependence.

- Nothing here changes a frozen Gate B/C rule, a sealed ranking, D5 = (a) or a user decision in FOCUS. Where a fix would touch one, it is marked [USER] and the current rule stays in force. No fix here relies on the relayed rule "ambitious default, pre-set fallback", so no item is [USER-CONFIRM].
- I opened no `selector.jsonl`, no `hidden/`, no held-out file, no wave-0b `rows.jsonl` or `groups.json`. I printed no row, prompt, answer or anchor text. The check scripts read no evaluation record: every input is a number stated in the draft or its sources.

**Labels for numbers.** R = read in a source (named). M (review) = computed by this review's scripts (`review_stats_sim.py`, `review_stats_arith.py`; outputs `review_stats_sim_out.txt`, `review_stats_arith_out.txt`). M (AMD SIM) = draft B's simulation, not re-run here. E = estimate. I = inference or proposal.

**Severity.**
- **MAJOR:** a stated error-control, label or blinding guarantee fails in a plausible case, or a rule leaves an outcome-dependent choice open. Fix before the W1 record.
- **MODERATE:** a power, MDE or error statement that misleads a decision (an FC item), or a rule gap that makes B16's builder guess.
- **MINOR:** a wrong number, an overstatement with a small effect, or a missing disclosure.
- **NIT:** wording, a basis to cite, or a definition to add.

## Counts

| Severity | Count | Items |
|---|---|---|
| MAJOR | 3 | S-1, S-2, S-3 |
| MODERATE | 7 | S-4 to S-10 |
| MINOR | 9 | S-11 to S-19 |
| NIT | 7 | S-20 to S-26 |
| **Total** | **26** | |

By primary area (each item counted once): analysis model 4 (S-1, S-8, S-13, S-21); testing-family error control 4 (S-11, S-16, S-22, S-24); labels 3 (S-9, S-10, S-23); margins and power 4 (S-5, S-6, S-7, S-15); reference tests 2 (S-4, S-19); over-refusal and task-loss NI rules 4 (S-12, S-18, S-20, S-26); outcome-dependence 4 (S-2, S-3, S-14, S-17); other 1 (S-25).

Marks of the fixes: all 26 are [LEAD]. Three of them (S-6, S-8, S-10) add numbers to a [USER] question (FC-2, FC-5) and do not decide it. None needs [USER-CONFIRM].

---

## MAJOR

### S-1 [MAJOR] The O and L "worse" tests (and the O, L parts of "beats r") pool one seed variance over arms whose O noise differs by level (§4.3 line 279; §3.6 lines 242–245; §5.3 line 364)

- **Defect.** Under S-a, the in-force model if the user is silent, the O and L "worse" families use "the test form of the primary model", that is, one seed variance pooled over the eight primary arms. O is a share of 100 greedy answers. Its seed-to-seed variance grows with its level (binomial scaling). The expected case puts the arms at different levels: a0 and the removal arms near a0's 4–6 of 100, the add arms near θ0's 17 of 100 (R: §6.1; RB item 1). The pooled variance then understates the add arms' variance, and the P5 and P6 tests (S3 and S4 against S1, all add arms) become too liberal.
- **Evidence (M (review), Part B, 200,000 replicates; one-sided adverse Holm over 6 at 5%; O seed SD scaled as √(p(1 − p))):**

  | Case | S-a pooled | S-aW (Welch) | Paired per contrast |
  |---|---|---|---|
  | All arms at 5 pp (equal SDs) | 4.6% | 4.2% | 4.7% |
  | Add arms at 17 pp, others at 5 pp | **7.2%** (P5 or P6: 6.7%) | 4.2% | 4.6% |
  | Add arms at 12 pp | **6.2%** | 4.2% | 4.5% |
  | Add arms at 17 pp, shared seed shift ρ 0.5 | 5.1% | 1.6% | 4.6% |

  The family-wise false "worse (O)" rate is above 5% in the expected case, and the paper's 5% claim fails. The same pooling reaches the O and L parts of every "m beats r" test (§5.3), where reference arms (for example SP, which raises refusal) sit at other O levels again.
- **Why the lead can fix it.** PLAN-S:102's pooled rule is written for the U contrast Λ_m. PLAN-S §4.1 gives the side effects "with its SE" and names no pooling. The 18:31 UTC rule fixes "5% Holm, in its harmful direction", not the variance (R: FOCUS 8 Oct 18:31 UTC). So the variance form for O and L is a lead choice.
- **Fix (exact text).**
  - §4.3 line 279: replace "in the test form of the primary model (§3)" with: "in a per-contrast variance form: under HB, the HB form refitted for the endpoint (§3.6); under S-a, unpaired Welch with Welch–Satterthwaite df (the S-aW form). Reason: O's seed variance grows with its level, and the arms sit at different O levels (M (review) Part B: pooled 7.2% against Welch 4.2% family-wise when the add arms return to θ0's level). The pooled S-a form for O and L is a reported sensitivity and never changes a label."
  - §3.6: add "Under S-a, O and L are never pooled over arms (§4.3)."
  - §5.3 line 364: replace the first two sentences with: "**Variance:** U uses the primary model's form (§3). O and L use the per-contrast form of §4.3 (Welch under S-a; HB under HB)."
- **Mark and deadline.** [LEAD] W1 (with FC-9's U4 reading).

### S-2 [MAJOR] Statistical rules fixed at S1 are written after Gate B outcomes are read, and §12 does not cover them (§13.1 line 751; §13.2 line 759; §4.4 line 287)

- **Defect.** §13 puts these inference rules at S1, after Gate B wave 1, wave 2, the extension and HarmBench are read: §4.7's confirmation choice rule; §4.8's "too close to call" rule; §5.2–§5.3's "beats r" form, the adapter-scaling rule, the O and L margins, the variance form and family 1b (REF LQ3, LQ45; AMD B5, D1). §12 lists only the values seen before the W1 settings. The adopted text says: "Before Gate B wave 1, … the primary family, the seed rule, the limits, the judge rule … are committed here. Anything added later is 'post-Gate-B exploratory'" (R: FOCUS 8 Oct 13:53 UTC). The "beats model-level repair" claim is a do-not-claim boundary (R: §0.5), so a rule for it written after Gate B outcomes either becomes exploratory or stays open to tuning on Gate B's removal-arm U, O and L values.
- **The same hole in R1.5.** The user may switch R1.3 to primary "until S1, before any newly run stage-1 cell's outcome is read" (line 287). Between W1 and S1, Gate B's wave-1 and wave-2 arms' O and task loss are read (R: PREREG §6 measures both). Those values predict how R1.3 and the 18:31 rule would label removal arms. A switch in that window can depend on them, and the record would not show it.
- **Fix (exact text).**
  - §13.1, replace the last row with two rows: "| §4.7 choice rule, §4.8, §5.2 role and claim rules, §5.3 entire (the 'beats r' form, the curve rule, the margins, the variance form, family 1b), LQ45 | **W1** (rule text only, $0) | REQ-21 (b), (c) |" and "| Reference seeds and spend (FC-21 to FC-29), LQ18's seed choice, the S1 builds, §10.3's c0 job and charging | **S1** | this pre-registration, frozen |".
  - §13.2: move AMD B5, D1, the §4.7 rule, the §4.8 rule, LQ3 and LQ45 from the S1 row to the W1 row.
  - Add to §12: "**12.4 Rules written after Gate B outcomes.** Any inference rule that is still written after the W1 commit is listed in an S1 blinding record with every Gate B value read before it was written, and the paper labels it 'fixed after Gate B wave 1'."
  - §4.4 line 287: replace "The user may switch R1.3 to primary until S1, before any newly run stage-1 cell's outcome is read" with "The user may switch R1.3 to primary until the earlier of S1 and the first read of any Gate B wave-1 arm's over-refusal or task loss; a later switch is allowed only with a record of every Gate B O and L value read before it, and it is a disclosed deviation."
- **Mark and deadline.** [LEAD] W1. AMD itself allowed the reference rule text at W1 ("W1 (rule text, if the lead wants it fixed with the family)"; R: AMD §0 row D).

### S-3 [MAJOR] Nothing stops block A's outcomes from being read before block B is funded (§1.3 lines 140–141; §11 line 698; §10.6 item 7)

- **Defect.** PLAN-S says block A is kept "but no claim is read before block B, because 3 seeds cannot give equivalence bounds" (R: PLAN-S:76). The draft drops that sentence. It keeps "each block starts on a funding event, never on an outcome" and "only complete blocks are analysed", and FOCUS keeps "stop and ask after every stage" (R: §11 line 706). So after block A the lead stops and asks, and nothing says that block A's U, O or L values stay unread. If they are shown, the block-B funding decision can follow block A's outcomes. That is an outcome-dependent continuation, and the final Holm, TOST and NI levels no longer hold. The draft also does not say what is analysed if block B never runs (block A is a complete block).
- **Fix (exact text).** Add to §1.3 after line 141: "**Block A stays sealed (I; from PLAN-S:76).** After block A, only its cost ledgers, completion records and adapter fingerprints are read. Its U, HB, O, task-loss and coherence outputs are sealed by SHA-256 and are not read until block B is complete, or until a recorded decision ends stage 1 without block B. The block-B funding decision uses no block-A outcome; the 'stop and ask' report after block A gives cost and completion only. If block B never runs, block A is analysed alone under the same model and families; every label then carries 'block A only (3 seeds per method arm)', and the record prints block A's MDE." Add the same rule to §11 "Funding".
- **Mark and deadline.** [LEAD] W1. It enforces the user's "never on an outcome"; it adds nothing new.

---

## MODERATE

### S-4 [MODERATE] The adapter-scaling rule has a knife-edge at L̂(m) = L̂(a0), no L comparison point, and an O margin tied to an open user item (§5.3 lines 360–365)

- **Defect 1 (knife-edge).** "λ\*_m = 1 if L̂(m) ≤ L̂(a0)"; else λ_lo is the next grid point down (0.75, or 0.9 under FC-28). For an arm whose true task loss equals a0's, P(L̂(m) > L̂(a0)) = 0.5 by symmetry (I). The add arms (38 steps, the full corpus plus 48 rows) are that case. Then a noise-level L difference moves the U bar by the whole U gap between λ = 1 and λ_lo, and the dominance verdict becomes a coin flip on noise. The rule stays valid (it errs to the hard side) but its verdict is unstable.
- **Defect 2 (gap).** Item 1 (U) is tested at λ_lo and item 2 (O) at λ_hi. Item 3 (L) has no comparison point on the curve, so B16 must guess.
- **Defect 3 (mark).** Item 2 uses a 5 pp O margin. That is the τ_O\* value that FC-6 still holds open as [USER]. If the user declines FC-6, the text does not say what "beats" uses.
- **Fix (exact text).**
  - Line 365: replace "(λ\*_m = 1 if L̂(m) ≤ L̂(a0))" with "(λ\*_m = 1 if L̂(m) − L̂(a0) ≤ τ_L, so a task-loss rise below the pre-set tolerance never moves the reference point)".
  - Add after line 365: "Item 3 (L) is not tested against the curve, because the curve point is matched on L. The record prints L(m) − L(AS(λ_hi)) with its interval."
  - Line 360: add "The 5 pp here is the reference margin m_O, a [LEAD] choice; it is not τ_O\* and does not depend on FC-6."
- **Mark and deadline.** [LEAD], W1 under S-2 (else S1).

### S-5 [MODERATE] The power section gives test MDEs, not the power of the "better" label, and some MDEs are below δ (§3.5 lines 229–240; §3.3 line 220)

- **Defect.** "Better" needs a Holm rejection **and** Λ̂ ≥ 5 pp (R: §4.3). So P(better | true 5 pp) is about 0.5 in every model, and a test MDE below 5 pp (HB 3.5 pp at wave-0a noise) is not an effect that the study can label "better". The §3.5 table shows only test MDEs. AMD §C.4 has the label numbers, but the merge did not carry them.
- **Evidence.** "Better" 80% effect, P1 / P4 (pp), and P(better | 5 pp) for P1:

  | Noise | S-a (in force) | HB |
  |---|---|---|
  | PLAN-S central, per-arm 2.65, ρ 0 (pair 3.75) | 6.25 / 6.30; 0.50 (M (review) Part A) | 7.23 (P1); 0.35 (M (AMD C.4)) |
  | Wave 0a, pair 1.83 (ρ 0.76) | 5.80 / 5.95; 0.48 (M (review)) | 5.65 (P1); 0.50 (M (AMD C.4)) |
  | Plan-A cut, pair 4.5, ρ 0 | 6.60 / 6.85; 0.48 (M (review)) | 8.52 (P1); 0.26 (M (AMD C.4)) |
  | Plan-A cut, pair 4.5, ρ 0.76 | 12.0 / 12.85; 0.06 (M (review)) | 8.52 (P1); 0.26 (M (AMD C.4); HB depends on the pair SD, not on ρ, under one seed shift) |

  My seed-level simulation reproduces AMD's S-a and per-contrast MDEs within 0.05–0.15 pp (S-a 5.25 / 5.55 against 5.2 / 5.6 at N1; 4.90 / 5.25 against 4.9 / 5.3 at N4; paired-per-contrast 8.25 / 10.35 against 8.2 / 10.2 at N1), so the two sources agree.
- **Fix (exact text).** Add two columns to the §3.5 table: "'better' 80% effect (P1 / P4)" and "P(better | 5 pp)", filled from the evidence table above, and add: "'Better' needs Λ̂ ≥ 5 pp, so P(better | true 5 pp) is about 0.5 in every model. A test MDE below 5 pp is not an effect that the study can label 'better'; it is an effect that it can call 'significant, below the SESOI'." In §3.3 line 220, add after "P1 MDE at 80%: HB 3.5 pp": "(the 'better' label needs about 5.65 pp; M (AMD C.4))".
- **Mark and deadline.** [LEAD] W1 (text only).

### S-6 [MODERATE] The case for HB rests on a 3-seed correlation; the well-measured coupling scenario is missing (§3.3 line 220; §3.5)

- **Defect.** HB's power advantage (P1 MDE 3.5 against S-a 4.9 pp) uses ρ = 0.76, which comes from 3 seed pairs (R: §12.1, "implied same-seed ρ 0.76"). With n = 3 and true ρ = 0, a sample correlation of at least 0.76 in absolute value occurs with probability 0.45 (one-sided 0.23) (M (review), the n = 3 null density (1 − r²)^(−1/2)/π). The two per-arm SDs that enter it (a0 2.63, R 1.35 pp) differ by an F ratio of 3.76 on (2, 2) df, P = 0.21 one-tail (M (review)). The well-measured coupling is the shared sampling stream (seed-matched per-prompt SE 1.28 against 2.16 pp unmatched, over 200 prompts; R: AMD §A.10 item 1). That matches AMD's "CRN only" scenario N2 (pair SD 3.32, ρ 0.21), where the P1 / P4 MDE is S-a 5.1 / 5.4, S-aW 6.0 / 6.6 and HB 6.4 / 7.2 pp (M (AMD SIM) §A.9). So at the evidence-backed coupling, HB costs about 25% of MDE against S-a. The draft shows only the wave-0a and ρ = 0 rows.
- **Fix (exact text).** §3.3 line 220, after "The wave-0a values tip the balance, and they were seen before this choice (§12).": add "The ρ of 0.76 rests on 3 seed pairs; with true ρ = 0 a sample correlation this large occurs with probability 0.45 (M (review)). At the coupling that the wave-0a sampling streams measure well (AMD's N2: pair SD 3.32 pp, ρ 0.21), the P1 / P4 MDE is S-a 5.1 / 5.4, S-aW 6.0 / 6.6 and HB 6.4 / 7.2 pp (M (AMD SIM)). So the choice is robustness (HB) against power at low ρ (S-a), not a power gain known in advance." Add the N2 row to the §3.5 table. Show both to the user in FC-2.
- **Mark and deadline.** [LEAD] W1 text; it informs [USER] FC-2.

### S-7 [MODERATE] The blinded plan-A rule reads a pair SD, but S-a's power depends on the per-arm SD; A5 cannot print S-a's MDE (§1.3 line 138; §3.5 line 239)

- **Defect.** σ̂ is read on the pair scale (R: PLAN-S:118). S-a's SE uses the per-arm SD, σ_pair/√(2(1 − ρ)). So plan A does not bound S-a's power. At σ̂ = 4.5 pp (the cut): with ρ = 0, S-a's 90% half-width is 2.89 pp and P(equivalent | 0) is about 0.78; with ρ = 0.67 the expected half-width is 5.03 pp and with ρ = 0.76 it is 5.90 pp, so "equivalent" is about impossible, and the P1 MDE is 12.0 pp (M (review) Part A and `review_stats_arith_out.txt`). AMD A5 asks the record to print "the predicted MDE of P1 and P4 at the read σ̂ under the primary model". Under S-a that number needs ρ, which the blinded rule does not read. Gate B's σ̂ also has an effective df of only 2.8–3.3 (R: PREREG §2).
- **Fix (exact text).** Replace line 239 with: "**AMD A5 [LEAD] W1:** the plan-A/B record prints, at the read σ̂, the predicted P1 and P4 MDE, the 'better' 80% effect and P(equivalent | 0) under the primary model. Under S-a no per-arm SD is read from Gate B: the values are printed at ρ ∈ {0, 0.67, 0.76} with per-arm SD = σ̂/√(2(1 − ρ)), beside a 90% interval for σ̂ on its 2.8–3.3 effective df. The record states that plan A bounds HB's power but not S-a's (at σ̂ = 4.5 pp and ρ ≥ 0.67, S-a cannot reach 'equivalent'). No rule change."
- **Mark and deadline.** [LEAD] W1.

### S-8 [MODERATE] The in-force S-a has no per-arm variance check, so its U family is not controlled under unequal arm variances (§3.2 lines 210–212)

- **Defect.** If the user is silent, S-a is primary and its Holm family reaches 11.8% (M (AMD SIM), answer level) or 12.4% (M (review) Part H, seed level) when one arm has 3 × the seed SD; S-aW and the paired test stay at 4.4% and 4.8%. The draft discloses this but adds no guard, and §3.4 says a sensitivity "never changes a label". MRA W2 asked for "pooled with a pre-registered variance check and Welch as sensitivity" (R: MRA line 91). AMD showed that a pre-test does not fix it (b3: 7.8% with three noisy add arms; R: AMD §A.10). PLAN-S's own words are "Welch as a sensitivity **check**" (R: PLAN-S:102). A flag fits that text without a change to the user's rule.
- **Fix (exact text).** Add after line 212: "**Equal-variance flag ([LEAD] W1; PLAN-S:102's 'Welch as a sensitivity check').** Under S-a, B16 also runs S-aW at the same Holm step for every contrast. If S-a rejects and S-aW does not, the label row prints 'rests on equal arm variances (S-aW does not reject)', and every paper sentence that uses that label carries the flag. The label itself follows S-a." Add to FC-2 (line 774): "Silent default's known failure: 11.8–12.4% family-wise with one arm at 3 × the seed SD (M (AMD SIM); M (review))."
- **Mark and deadline.** [LEAD] W1. The approved model stays primary; FC-2 stays the user's.

### S-9 [MODERATE] The headline-word table is not a partition: three cases have no rule or two rules (§4.5 lines 298–306; §3.7 lines 250–251)

- **Defect 1.** Step 1 says "or the coherence rule fires → worse". §3.7 item 4 says a failing **comparator** makes the contrast "inconclusive (comparator fails answers end)". If the comparator fails, the two rules conflict. If both the repair and the comparator fail, no rule says which word wins.
- **Defect 2.** "Worse (U)" and "equivalent" can both hold (Λ̂ < 0, significant, interval inside ±5 pp). Under S-a at central noise this is rare (≤ 0.2%), but under a paired model at wave-0a noise it happens with probability 0.20–0.37 at true effects of −2 to −3 pp (M (review) Part F). §4.5 item 1 lists the U part as one word and gives no "print both" rule for this pair (AMD §B.5 gives one only for "significant, below the SESOI" with "equivalent").
- **Defect 3.** A favourable U rejection with 0 < Λ̂ < 5 pp and an interval not inside ±5 pp gets the headline "inconclusive" with no note. Step 3 adds "significant, below the SESOI" only when the contrast is also equivalent. The case is common: probability 0.19–0.28 under S-a at true +3 to +4.5 pp, 0.14–0.51 under the paired model (M (review) Part F). §4.3 line 282 says the text always adds the note, so the table and §4.3 disagree.
- **Fix (exact text).** Replace the table with:

  | Step | Condition | Word |
  |---|---|---|
  | 0a | the repair fails the answer screen (§3.7) | **worse (answers do not end)** |
  | 0b | else, the comparator fails the screen | **inconclusive (comparator fails answers end)**; the U, O and L tests are printed and give no word |
  | 1 | else, a U, O or task-loss contrast is significant in its adverse direction (§4.3) | **worse**, naming the measure; the U result is printed in the same row |
  | 2 | else, U rejects favourably and Λ̂ ≥ 5 pp | **better** |
  | 3 | else, the 90% interval of the U contrast lies inside ±5 pp | **equivalent** (grade named) |
  | 4 | else | **inconclusive** |
  | — | in steps 3 and 4, U rejected favourably with 0 < Λ̂ < 5 pp | add "significant, below the SESOI" |

  In item 1 add: "When 'worse (U)' and an equivalence grade both hold, the U part prints both."
- **Mark and deadline.** [LEAD] W1 (FC-9). Order 0a–0b is my proposal; the lead may reverse 0a and 0b, but one order must be written.

### S-10 [MODERATE] Under the 18:31 rule, "worse (L)" fires on task-loss rises well below τ_L, and the "worse first" order can then hide a "better" (§4.3 line 279; §4.5 step 1; FC-5)

- **Defect.** The 18:31 rule labels "worse" on significance alone (R: FOCUS 8 Oct 18:31 UTC). L's seed SE is very small. If the seed SD equals s (0.0023749 nats), Holm's first one-sided step rejects at about 0.48–0.51 τ_L, and P(worse (L)) is 0.48–0.55 at a true rise of 0.5 τ_L and 0.88–0.92 at 0.75 τ_L (M (review), `review_stats_arith_out.txt`; 6 against 6 and 6 against 8, 42 df). τ_L is the user-approved scale of a material change (2 SE of a seed-to-seed difference; R: FOCUS 8 Oct 13:53 UTC). So an immaterial rise can make the headline word "worse (L)", and step 1 then hides a U result that is "better". The draft gives R1.3's reason for O only (line 287).
- **Fix (exact text).**
  - Line 287, add to R1.3's reason: "The same holds for L: under the 18:31 rule a task-loss rise of half τ_L reads 'worse (L)' about half the time if the seed SD equals s (M (review))." Add the same sentence to FC-5.
  - §4.5 step 1, add: "If U also meets step 2, the word is 'better; worse (measure)', both words, so a significant side effect never hides a U benefit in the headline."
- **Mark and deadline.** The R1.3 decision stays [USER] (FC-5). The headline order is [LEAD] W1 (FC-9; REF LQ44).

---

## MINOR

### S-11 [MINOR] "Up to about 11%" false "worse" is a simulated value, not a bound, and the expected case is higher (§4.3 line 280)

- **Defect.** 11.1% is the simulated global-null rate (R: CK-3 §3.2 reading R1; M (review) Part C: 11.1%). The bound is 12.5% (2.5% from U's adverse tail, 5% from O, 5% from L). In the expected case (add arms back near θ0's O level), S-a's pooled O variance gives 12.8%; with S-1's per-contrast form it is 9.4% (M (review) Part C, CK-3's realistic mix).
- **Fix (exact text).** Replace line 280 with: "Under the global null the chance of at least one false 'worse' is about 11% (M: CK-3 §3.2; M (review)) and at most 12.5% (union bound: 2.5% + 5% + 5%). With the add arms back near θ0's over-refusal it is 12.8% under a pooled O variance and 9.4% under §4.3's per-contrast form (M (review)). The paper says so."
- **Mark.** [LEAD] W1.

### S-12 [MINOR] The τ_L 2-df caveat gives the boundary value as the conditional rate (§6.6 line 482; ADD L16)

- **Defect.** "P(s < 0.5σ) = 0.22, in which case about 12–24% of null arms fail the L screen." 12.6% and 22.2% are the fail rates **at** s = 0.5σ exactly (one-sided 90% bound and R1.2's bound). Given s < 0.5σ, the average null fail rate is 39.6% and 52.3%. Averaged over the whole 2-df uncertainty in s, it is 9.8% and 13.8% (M (review) Part E: a null 6-against-6 arm, SE on 42 df, 2,000,000 draws). P(s < 0.5σ) = 0.222 is right.
- **Fix (exact text).** Replace the sentence with: "P(s < 0.5σ) = 0.22. At s = 0.5σ, 22% of null 6-against-6 arms fail the L screen under the R1.2 bound (13% under a one-sided 90% bound); averaged over s < 0.5σ, about 52% (40%); averaged over all values of s, about 14% (10%) (M (review))."
- **Mark.** [LEAD]: it corrects a number in ADD L16's own text; the rule (τ_L = 2√2·s, never re-estimated) does not change.

### S-13 [MINOR] S-a's "42 df" is nominal; shared seeds lower the effective df (§3.2 line 211)

- **Defect.** The eight arms share seeds, so their within-arm variances are correlated. The pooled variance's effective df (2E²/Var) is 41.9 at ρ = 0, 26.6 at ρ = 0.3 and 8.9 at ρ = 0.76 (M (review) Part G). S-a's SE also over-states the contrast variance when ρ > 0 (the true variance of P1 is σ²(7/24 − ρ/4), S-a estimates σ²·7/24; I), so S-a stays conservative and no type I error follows. But "df stated" (PLAN-S:102) should not state 42 as exact.
- **Fix (exact text).** Line 211: replace "(50 cells, 42 df; M (AMD))" with "(50 cells, 42 df nominal; M (AMD)). Shared seeds lower the effective df (about 27 at ρ = 0.3 and 9 at ρ = 0.76; M (review)); S-a's SE then over-states the contrast variance, so S-a stays conservative. The record prints 'df 42 (nominal)'."
- **Mark.** [LEAD] W1.

### S-14 [MINOR] §12.3 overstates HB's error control and misses four choices made after values were seen (§12.3 line 734)

- **Defect 1.** "HB's error control holds … so it cannot raise the false-positive rate." HB is near nominal, not exact: up to 1.09% at α/6 (nominal 0.83%), 1.26% at 1% and 5.33% at 5% (M (AMD SIM; VR-B §3.3)). VR-B already marked "valid in all 19 scenarios" as an overstatement (V-8).
- **Defect 2 (missing entries).** (a) The one-sided form of the O and L "worse" families (Appendix A, C-4) was chosen by the merge after the Gate A O counts were known (a0 4–6, θ0 17 of 100; R: §12.1). Those counts predict that add arms read "worse (O)" more often under one-sided tests. (b) AMD D1's NI margins for the references (5 pp, τ_L) were drafted after the same counts. (c) HB against HB-C is ruled after wave 0a; Gate B cannot inform it, but its MDE trade-off was computed at the seen ρ. (d) Whether R_4 and R_5 are reused (§1.2) depends on Gate B's TOO CLOSE verdict, and their values are read before S1.
- **Fix (exact text).** In item (1) replace "so it cannot raise the false-positive rate" with "its simulated single-contrast rates stay within about 1.3 × nominal (up to 1.09% at α/6, 1.26% at 1%, 5.33% at 5%; M (AMD SIM; VR-B)), so it does not raise the false-positive rate materially". Add items (9)–(12) with the four facts above.
- **Mark.** [LEAD] W1 (REQ-21 (m)).

### S-15 [MINOR] Plan B is not carried through the statistics (§1.3 line 139; §3.2; §4.3 line 276)

- **Defect.** (a) "Equivalent (familywise)" uses α/6; under plan B the family has 3 members, so the interval is 96.67% (α/3 per side; M (review)). (b) S-a's pool is "the eight primary arms"; plan B runs five (R, A1, H1, S1, S4), so the pool and its df are undefined. (c) Plan B's a0 seeds are not stated, but a0 is needed for G_m, the L comparator and the references. (d) HB's fit and the false-"worse" figure for three-member families are not given.
- **Fix (exact text).** Add to §1.3: "Under plan B: S-a and HB fit the plan-B arms only (R, A1, H1, S1, S4, and a0 if it runs); the familywise equivalence grade uses α/3 per side (the 96.67% interval); the O and L families have three members; a0's seeds are [LEAD] W1." Recompute the §4.3 false-"worse" sentence for plan B in the plan-A/B record.
- **Mark.** [LEAD] W1.

### S-16 [MINOR] The per-comparison "equivalent" label has no stated family-wise error (§4.3 line 275)

- **Defect.** Six TOSTs at 5% each give at most 30% (union) or 26.5% (independent) chance of at least one false "equivalent (per comparison)" when all six contrasts sit on the margin; CK-3 simulated 19.8% (R: CK-3 §3.2). The headline word in step 3 can be this grade. The draft says "Every sentence that uses it says 'per comparison'" but gives no number.
- **Fix (exact text).** Add to line 275: "Across the six contrasts the chance of at least one false 'equivalent (per comparison)' is not controlled: at most 30%, and 19.8% simulated with every contrast on the margin (M: CK-3 §3.2). The familywise grade (§4.3, AMD B3) controls it at 5%."
- **Mark.** [LEAD] W1.

### S-17 [MINOR] The plant pilot's interval is undefined, and its gated cells are reused as the main sweep's comparator (§8.2 line 534; §8.3)

- **Defect 1.** "Its one-sided 90% lower bound" gives no SE form (paired by seed? 2 df? a prompt part?).
- **Defect 2.** The main-sweep arms are paired with a0_plant at seeds 1101–1103 (R: ADD §3), the same cells that passed the gate (Λ_plant ≥ 10 pp). Given a pass, a0_plant's noise is selected high, so contrasts against a0_plant are biased upward (I). Gate A's a0 at 1101–1103 is fixed and known, so contrasts against it are not selected by the gate.
- **Fix (exact text).** §8.2: add "The pilot interval is paired by seed on 1101–1103 (J = 3, 2 df) in the primary model's form, with its prompt part under HB." §8.6: add "Every main-sweep arm is also reported against Gate A's a0 at the same seed, which the gate does not select; contrasts against a0_plant carry the note 'comparator selected by the pilot gate'."
- **Mark.** [LEAD] W1 (the plant's rule text is W1).

### S-18 [MINOR] The O error model's "one scope" reason holds only under HB; under S-a the scopes split (§6.4 line 446; §3.6; §4.7)

- **Defect.** §6.4 chooses "prompts random" for O because it gives "one scope for U and O in every sentence". Under S-a (the silent default) U has no prompt term, so U is "on these 200 prompts" while O feasibility is prompt-random, and the O "worse" test (seed level) is again bank-conditional. The stage-3 confirmation on a hidden 200-prompt subsample "tests the same parameter" only under prompts random (R: AMD §B.6), so under S-a a failed confirmation can mix a prompt-population difference with a false stage-1 result.
- **Fix (exact text).** §6.4, after the first bullet: "Under S-a (§3.2), U and the O 'worse' test are bank-conditional ('on these prompts'), while O feasibility stays prompt-random on PLAN-S:197's grounds alone; every U and O sentence then names its scope. Under S-a the confirmation (§4.7) is read as a test on new prompts, and the paper says so."
- **Mark.** [LEAD] W1.

### S-19 [MINOR] The reference-test power line mixes one-sided and two-sided bases, and the fallback's "descriptive" is an HB fact (§5.3 lines 369–370)

- **Defect.** "A one-sided 5% test needs about 3.4–4.3 pp …" is HB with 5 pairs (the FC-28 seed set, not the in-force set). "A 6-against-3 MDE is about 5.4 pp" is a two-sided 5% value (R: MRA W3). Under the rule as written (one-sided 5%) the unpaired 6-against-3 MDE is 4.74 pp, and 6.27 pp at family 1b's first step (M (review), per-arm SD 2.65, 42 df). The fallback says "only 2 pairs …, so 'beats' is descriptive"; that follows HB's paired form. Under S-a (in force) the unpaired 6-against-3 test is a valid test.
- **Fix (exact text).** Line 369: "Power (U part only): under HB with FC-28's seeds (5 pairs), 3.4–4.3 pp at pair SD 1.83 and 5.3–5.9 pp at 3.75 (E: AMD §D.5). Under S-a with the approved 3-seed references, the unpaired 6-against-3 MDE is 4.7 pp for the one-sided 5% test and 6.3 pp at family 1b's first step (M (review)); MRA's 5.4 pp is the two-sided value." Line 370: replace "so 'beats' is descriptive" with "so under HB 'beats' is descriptive; under S-a it is the unpaired test above".
- **Mark.** [LEAD], W1 under S-2 (else S1).

---

## NIT

### S-20 [NIT] S-a's feasibility SE for O against θ0 needs its exact form (§6.4 line 450; Appendix C, G-4)
"The prompt-clustered SE of the per-prompt difference" from seed-averaged per-prompt differences omits the seed main effect. **Fix:** "Under S-a, V = s²_pool,O/J_m + max(0, MS_P − MS_E)/(P·J_m), from the J_m × P table of y(m, j, p) − y(θ0, p), with Satterthwaite df as §3.3." At the Gate A values the omitted term is about 1% of the variance (I: seed SD of O about 1.15 pp against a prompt SE of about 4.1 pp), so the fix changes little. [LEAD] W1.

### S-21 [NIT] HB's variance floor (0.01 pp²) is far below the known sampling floor (§3.3 line 216)
Each cell's U carries sampling noise from its own 600 answers; a REML variance at 0.01 pp² is not possible in the data. Unconditional rates stay near nominal (R: AMD §A.3, V-6), so this is not a validity defect. **Option:** a data-based floor per arm, the arm's mean within-cell sampling variance computed from its own 3 samples per prompt (no Gate B number). [LEAD], optional.

### S-22 [NIT] The confirmation rule leaves the endpoint open and does not state its error (§4.7 lines 323–324)
For a "worse (O)" or "worse (L)" pick, the text does not say which endpoint is confirmed. **Fix:** "|t| and the confirmation test use the endpoint that gave the label. A false 'confirmed' for a null contrast has probability at most 2.5% each, because the direction is fixed by stage 1, so at most 5% for two (M (review))." [LEAD] S1 (or W1 under S-2).

### S-23 [NIT] "The best feasible repair" has no rule for "best" (§4.5 line 306)
"Better" compares a repair with its comparator, not with other repairs. **Fix:** "'The best feasible repair' also needs §4.8's separation from the runner-up; otherwise the text says 'too close to call'." [LEAD] W1.

### S-24 [NIT] The wrong-sign figure quoted is for Φ, not for the in-force Holm (§4.3 line 283)
**Fix:** add "Under the in-force Holm with S-a, the chance of any wrong-sign claim was 0.00–1.18% in 10 configurations with true effects of ±0.25 to ±4 SE (M (review) Part D; ρ 0 and 0.76)." [LEAD] W1.

### S-25 [NIT] The overlap control's "must hold" has no test (§9.4 line 593)
**Fix:** "'Holds' = the add contrast on the lower-similarity half has the same sign as on all prompts and its 90% interval excludes 0; else the text says 'not shown on the less similar half'." [LEAD] W1.

### S-26 [NIT] REQ-19's O MDE does not state its α and sidedness (§6.4 line 447)
"About 11–12 pp" matches a two-sided 5% MDE (2.80 × 4.1 pp; M (review)); the one-sided NI form gives 10.2 pp (R: RB `ni_power.out`). Both exceed 5 pp, so U8's answer does not change. **Fix:** "REQ-19 prints the 6-seed O MDE as a two-sided 5%, 80% MDE, and the one-sided NI value beside it." [LEAD] W1.

---

## Checks that passed (no change needed)

1. **"Better" and "equivalent" are mutually exclusive.** Equivalence needs Λ̂ + t·SE < 5, so Λ̂ < 5, and "better" needs Λ̂ ≥ 5 (I). "Better" and "worse (U)" are exclusive by sign. "O-feasible", "O-infeasible" and "undetermined" are exclusive because the lower end of an interval never exceeds the upper end (I).
2. **Holm over P1–P6 and the O, L Holm families** control their family-wise rates under any dependence, if each marginal test is valid (I; standard). With equal arm variances the S-a form gives 4.6% (O form, M (review) Part B0), and AMD's N1 gives 4.3% (M (AMD SIM)). The failures above (S-1, S-8) are failures of marginal validity, not of Holm.
3. **The familywise TOST grade** (98.33% = Bonferroni α/6 per side) and **the IUT for "dominates"** with Holm over D_1…D_6 are valid constructions (I).
4. **Wrong-sign claims under the in-force Holm and S-a** stay at 0.00–1.18% in 10 configurations, below α/2 (M (review) Part D).
5. **HB's variance decomposition** has no double count: V_seed covers the seed main effect and the cell-level residual, V_prompt the arm × prompt term only; the Satterthwaite form df = V²/(V²_seed/df_seed + q) is consistent with Var̂(V_prompt) = 2q (I). HB's REML was not re-run here.
6. **Global-null false "worse" with equal variances:** 11.1% (U 2.4, O 4.6, L 4.6), the same as CK-3 (M (review) Part C).
7. **Arithmetic re-checked (M (review), by hand from the listed values):** s = 0.0023749 nats from the three a0 means; τ_L = 0.0067171; the SEs √2·s and s·√(1/3); τ_L = 0.43% of the a0 mean loss and 1.2% of the θ0-to-a0 gain; the χ²₂ facts (σ/s 0.52–6.28; P(s < 0.5σ) = 0.221; P(s < σ) = 0.632); δ/E = 11.1% (10.4–11.5%); √(200/35) = 2.39; 5 pp ↔ 1.7 pp usable help and 3.4 pp on the HarmBench scale; R's U values from r_j; SD(r) 1.83 and the implied ρ 0.76; the NI power line (10.2 → 4.6 pp) from RB's `ni_power.py`.
8. **Confirmation** keeps false "confirmed" at or below 5% for two contrasts, because the direction is fixed in advance (2 × 2.5%) (M (review)).
9. **Seed-level replication of AMD's results:** S-a and paired-per-contrast MDEs agree within 0.05–0.15 pp, and S-a's family-wise rate with one arm at 3 × SD is 12.4% here against 11.8% there (M (review) Parts A and H).

## Replies to the standing questions

- **HB or HB-C (to GPT).** No new evidence here. S-6 shows that the power gain of either over S-a depends on a ρ that 3 seeds cannot fix; HB-C's extra robustness costs 8–12% of MDE (R: VR-B). I lean to HB-C for the reason VR-B gives (valid on design grounds over the whole grid), because the power argument for HB's one-shift form is the weaker of the two.
- **The τ_L comparator (to GPT).** Not resolved here. S-4's τ_L tolerance in the curve rule and S-10's numbers both show how small τ_L is against seed noise; a dose-only rise of R over a0 above τ_L would make every removal arm L-infeasible against a0, as REF LQ38 says.

## Limits

- Seed-level Gaussian simulations only. The answer-level structure (prompts, three samples, CRN) is not simulated here; AMD SIM covers it. The O heteroscedasticity in S-1 assumes binomial scaling of the seed SD; the real ratio between arms is not measured (Gate A has 2 df per arm).
- I did not re-run AMD's REML, Φ or answer-level simulations, nor CK-OR's O SEs. I did not review the selector (REQ-16 to REQ-18), the costs, or `stage1-decisions-consolidated.md` and `w1-builder-extract.md`.
- Two citations I hold from memory and did not check, so I do not rely on them: Shaffer (1980) and Finner (1999) on directional errors of step-down tests. S-24 rests on the simulation only.

## Record

**Commands run (all exit 0).**
- `date -u` at 00:55:17, 01:15:20, 01:16:51 and 01:19:57 UTC.
- `ls`, `wc`, `grep -n`, `sed -n` reads of: the target draft (all 926 lines, Read tool); PLAN-S §4, §6–§11; FOCUS lines 212–216 and 236–256; PREREG §2; AMD §0, §A–§F (Read tool, lines 36–539); VR-B §3 and its outline; CK-3 §3.1–§3.4 (lines 150–200); RB item 1 and W7 (lines 160–212, 323–352); RB `ni_power.py` and `.out`; REF line 410 and `tau_l_check.py`; ADD L16 and §3 (lines 285–300); MRA W4 lines; `sim_w2.py` lines 1–215 and 813–830; `stage1_model_sim.py` lines 1–200.
- `git -C <main checkout> rev-parse --short HEAD` → `5957a37` (HEAD moved from the draft's `3db753e` by a backup commit; no statistics source changed); `git log --oneline -3`; `git status --porcelain` on the analysis-model folder (clean; no `__pycache__` written).
- `PYTHONDONTWRITEBYTECODE=1 …/minimal-experiment-20261002/venv/bin/python -B review_stats_sim.py` (17.7 s) and `… review_stats_arith.py` (twice; the first run had a sign error in one power line, fixed and re-run). Both import `sim_w2.py` read-only for the t-distribution functions.
- `shasum -a 256` of the target and of the four check files.

**Files written (this folder only).** `review-statistics.md` (this file); `review_stats_sim.py` (`3c4b1d28b951ccac…`) and `review_stats_sim_out.txt` (`e0457033107f7389…`); `review_stats_arith.py` (`df02d3debd061999…`) and `review_stats_arith_out.txt` (`9ea0d20dffe2e2e6…`) (SHA-256 at 01:19:57 UTC).
