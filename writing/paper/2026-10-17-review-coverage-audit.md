# Pre-freeze coverage audit: mock reviews A and B, and the literature sweep, against the stage-1 pre-registration and paper revision 6h

- **Written** 17 Oct 2026 from 12:56 UTC (`date -u` at 12:56:49, 13:08:04 and 13:10:18 UTC). Read-only audit by an Opus worker for the main-study lead. This file is the only new file. No commit, run, install, download or agent.
- **Sources.** All read with `git show` from `origin/stageb-costs-and-recovery-safeguards-20261003` at head `074f693` (fetched 12:56 UTC, exit 0).
- **Status words.**
  - **ADDRESSED**: decided in a cited rule (a FOCUS user or lead decision, an addendum §, or a DRAFT rule) and stated in the paper.
  - **PARTLY**: part is decided; the missing part is named.
  - **OPEN**: no rule and no paper text.
  - **DECLINED**: a recorded decision rejects it. Where only part of a weakness is declined, the row is PARTLY or OPEN and the declined part is named.
  - "Not found" means I searched the sources below and found nothing.

**Short names.**

| Name | File (at `074f693`) |
|---|---|
| MRA, MRB | `writing/paper/2026-10-17-mock-review-A-methods.md`, `…-B-safety.md` |
| SWEEP | `writing/paper/2026-10-17-lit-sweep.md` (§5 design actions 1–5) |
| REPLAN | `writing/paper/2026-10-17-icml-replan-PROPOSAL.md` |
| DRAFT | `research/experiments/2026-10-17-stage1-preregistration/stage1-preregistration-DRAFT.md`, revision 2 (commit 2ded100) |
| CONS | same folder, `stage1-decisions-consolidated.md`, revision 2 (UW, LW, US, LS, LA items) |
| EXTR | same folder, `w1-builder-extract.md` (W1-xx items) |
| ADD | `.ai/briefs/stage1-commitments-build-20261016-lead-decisions.md` (L1–L16, §3–§9) |
| AMD | `research/experiments/2026-10-17-stage1-analysis-model/stage1-analysis-model-DRAFT.md`, revision 2 (read for §B–§D only, because DRAFT defers Φ's edges to it) |
| PAPER | `writing/paper/2026-10-08-icml-draft.md`, revision 6h (body, Appendix C, editor's notes) |
| PREREG | the frozen Gate B/C pre-registration, revision 5 (cited through DRAFT; not read here) |
| FOCUS 07:21 | FOCUS entry "USER DECISIONS, 2026-10-17T07:21 UTC" (UW-01 to UW-21 at the recommended defaults) |
| FOCUS LW | FOCUS entry "LEAD DECISIONS FOR WAVE 1" (LW-01 to LW-35 at the defaults; LW-01 HB-C, LW-07 τ_L against a0, LW-18 build REQ-12 and REQ-13) |
| FOCUS 09:32, 09:37, 11:04, 8dac6ad | FOCUS entries of 17 Oct (A1 set sealed; REQ-19 fires O-ext; W1-18 blocker; the user's Olmo 3 decision) |

**The most important finding first.** Nothing below is frozen yet.
- DRAFT revision 2 was committed at 01:55 UTC on 17 Oct. It predates the user's 07:21 UTC decisions and ADD §6–§9. It still prints the superseded rules as "in force": S-a (§3.2), Holm over six (§4.1), the 18:31 "worse" rule (§4.3), seed layout D0 (§1.2–§1.3), the 100-prompt over-refusal bank (§2.2, §6.5), "no R_tok arm" (§9.3) and "T1 not committed" (§0.4).
- The W1 record `research/experiments/2026-10-16-stage1-commitments.md` (REQ-21) does not exist at origin.
- So "ADDRESSED" below means "decided and stated in the paper". It does not mean "in a frozen pre-registration".

---

## 1. Coverage table

### 1.1 Review A (statistics and design), W1–W15

| # | Weakness (one line) | Status | Where it is addressed, or what is missing | Cheapest remaining fix (cost) |
|---|---|---|---|---|
| A-W1 | Protocol not frozen; "pre-registered" claims too much | PARTLY | Decisions exist: FOCUS 07:21 (UW-01–UW-21), FOCUS LW (LW-01–LW-35), ADD §6–§9. LW-26 puts "pre-specified" in the W1 record until REQ-20 and REQ-21 are committed. **Missing:** the frozen text (DRAFT is stale; no REQ-21 record); a public registry deposit (CONS LA-12, a USER item, Later). PAPER's abstract still says "six pre-registered repairs" (rev 6h ruling 6). PAPER §4.5 and C.5 still mark the nested cells [TO BE FINALISED], although ADD L12 and the T1 commit 9525005 fixed them. | Top fix 1: DRAFT revision 3 or the REQ-21 record built from the decisions; an anonymized, timestamped deposit with hashes (a public post: needs the user's yes). $0. |
| A-W2 | Unpaired, pooled analysis against a paired Gate B; unequal arm variances; prompts not crossed | ADDRESSED | FOCUS 07:21 UW-02 (a paired model); FOCUS LW-01 (HB-C primary); ADD §6 item 1 (one seed shift per design cluster, one residual variance per arm by REML, a crossed prompt part, Satterthwaite df; HB, S-a and S-aW as sensitivities); LW-02 A2, A3, A5; AMD §A; PAPER §3.2 and C.11. **Small gaps:** PAPER C.3 does not say that the 4.5 and 6.0 pp blinded cuts are on the seed-pair scale (DRAFT §1.3 says so). The planning MDE stays a placeholder (PAPER §4.3; decision 52). | One clause in C.3: "Gate B's pooled seed-pair SD". $0. |
| A-W3 | "Beats the references" has no test; references at 3 seeds; "below the curve at equal O and L" undefined | PARTLY | A rule is drafted, not adopted: DRAFT §5.3 and AMD §D.1–§D.4 ("m beats r" by three non-inferiority bounds; the curve read at λ\*_m matched on task loss; dominance as an intersection–union test; family 1b, Holm over D_1–D_6). Its decision is CONS LS-06 (S1; rule text due at W1 by S-2). It is not among the FOCUS LW decisions (LW-01–LW-35 only). Reference seeds: CONS US-01 (S1) is open; in force are a0 1101–1103 (DRAFT §5.1). PAPER §3.2 still says "at equal O and L"; §4.4 is [TO BE FIXED]; §4.9 has no family 1b. | Top fix 2. Rule $0. All a0 seeds plus λ = 0.9 plus recipe G at 6 seeds: about $42–46, plus $9.2–10.1 under layout D1 (ESTIMATE, CONS US-01). |
| A-W4 | Multiplicity covers only part of the labels; TOST adjustment, sidedness and gatekeeping unstated | ADDRESSED | FOCUS 07:21 UW-04 (Φ, 24 nodes) and UW-06 (τ_O\* = 5 pp); ADD §6 item 3; AMD §B.1–§B.4 (edges, weights, sidedness; equivalence outside Φ); LW-02 B3 (grade 2, the 98.33% interval); PAPER §4.9 and C.11. **Small gaps:** PAPER C.11 says only that "the pre-registration fixes how a rejected node passes its weight"; the edges exist only in AMD §B.2. The paper does not say that study-wise error is not controlled across the later families (AMD §B.6 asks for that sentence). | Copy AMD §B.2's edges into the frozen text; one sentence in PAPER §4.9. $0. |
| A-W5 | δ = 5 pp unjustified and absolute; "better" needs Λ̂ ≥ δ, so P(better \| δ) = 0.5; asymmetric labels | PARTLY | LW-02 C1 (δ is about 11% of E = 45.11 pp); UW-13 (δ_fam); PAPER §3.2 clause and C.11 "The margin"; the note "significant, below the SESOI" (UW-08 (a); C.11). **Missing in PAPER:** the "better" label's own operating characteristic (DRAFT §3.5 second table, S-5; AMD §C.4: 80% "better" needs 5.65–8.52 pp); a per-contrast "smallest margin at which it is equivalent" (not found in any rule; AMD §C.4 gives only the planning δ80). PAPER §6 still says "The labels resolve differences of about 5 pp", which DRAFT §3.5 contradicts. | One C.11 sentence with the "better" 80% effect; add the smallest equivalence margin to the label row (DRAFT §4.5); fix §6. $0. |
| A-W6 | Judge bias may differ by arm; human check too small; claim rule has no uncertainty and is undefined for "equivalent" | PARTLY | LW-30 (a): a one-paragraph human-label-check commitment in REQ-21 at W1, with the full protocol before block A. The spend is CONS LA-07 (a USER item, Later). LW-23 HB-2 reports per-bank agreement and κ with Qwen3Guard. **Not found:** the claim rule's uncertainty, and its wording for "equivalent" or "inconclusive" contrasts; an arm-stratified, two-rater design in any decided rule. PAPER Appendix A is unchanged (risk 39: "Body: not changed"). | Top fix 3. Rule text $0; two paid raters $440–650 (ESTIMATE, CONS LA-07, HR §5.3), or volunteers at $0. |
| A-W7 | One-shot scoring: the six A1 seeds replicate one selected subset | PARTLY | The ADD §5 item 2 report ran: Spearman ρ(q, e1) 0.771; top-600 Jaccard 0.434; the Adam variant V1 against A1, Jaccard 0.314 (FOCUS 09:32). PAPER §6 names the limit; C.2 gives the figures. **Missing:** scoring on 3 or more a0 seeds; a sentence that P1's interval is conditional on one sealed selection; S3's one-shot DataRx score (not found). A1's set is sealed (`a1_remove600.edit.json` 5c0e53b7…), so a per-seed selection is no longer possible. | Top fix 5: a $0 claim sentence; a report-only re-score on two more a0 retrains, about $12–19 (ESTIMATE). |
| A-W8 | "Compute-Matched" is a misnomer; no estimator for "most safety per compute"; no rule for "best"; no pairwise contrasts | PARTLY | Title kept: **DECLINED** by the user (FOCUS 07:21 UW-14; PAPER decision 26), with the token-matched analysis and R_tok as its basis. Tokens: ADD §5 item 1, ADD §6 item 5, EXTR W1-01 and W1-02; PAPER §3.2 and C.3. "Best": DRAFT §4.5 ("the best feasible repair" only if better, feasible and separated from the runner-up) and §4.8 (per-actor "too close to call") are drafted (CONS LS-17: S1, rule text W1), not decided, and not in PAPER. **Not found:** a net-benefit or Fieller estimator; pairwise contrasts among the six repairs. | Adopt DRAFT §4.5 and §4.8 as W1 rule text; add simultaneous 90% intervals for the 15 pairwise contrasts and net benefit Λ − λ·C(m) over a λ grid, both report-only. $0. |
| A-W9 | Two 1B models, one dataset, a chosen recipe; the replication rule accepts absence of evidence | PARTLY | The 7–8B full comparison is planned and funding-gated (PAPER §4.1; decision 28; REPLAN option B with C as the fallback). Olmo 3 is a third 7–8B model if funded (FOCUS 8dac6ad). δ_fam (UW-13). **Missing:** the replication rule is unchanged (PAPER §4.8: "same sign … below the interaction's MDE"; CONS LA-15 LLB L13 is Later); no "at 1B" qualifier; no 7–8B commitment. | $0: "replicates" = the same label in both families, or TOST on the family × repair interaction within δ_fam; claim a family difference only by a test. 7–8B: new money $680–1,660 (ESTIMATE, REPLAN §6). |
| A-W10 | Forking paths; the probe seed is reused; no decision tree; no end-to-end simulation | PARTLY | The blinding record is drafted (DRAFT §12.1–§12.4; LW-08 adopted). PAPER §4.9 discloses the timing. **Missing:** the fresh-seed mean E (45.92 pp; AMD §C.1) is not in PAPER (risk 43); PAPER does not say that stage-1 a0 reuses the Gate A seeds 1101–1103 (DRAFT §1.2 does); the decision-tree figure is CONS LA-13 (Later); an end-to-end simulation of the label pipeline: not found. Under HB-C and layout D1 every primary contrast uses the common seeds 1102–1107, so the probe seed a0_1101 enters no P1–P6 point estimate; it still enters a0's REML variance (I, from AMD §A.2–§A.3). PAPER could say so. | $0: one C.3 sentence (reuse; the probe seed outside the paired contrasts; the fresh-seed E); the decision-tree figure in Appendix C. |
| A-W11 | Positive control near-circular; dilution confounded with menu size; one plant location | PARTLY | Decoy: LW-10 F7 (a scored-only refusal decoy; EXTR W1-09). Locations: UW-20 (two more as conditional W1 text, run only if stage 1b is funded; fallback the F6 replay). Circularity: ADD §8 item 1 (a disjoint-source anchor set, sealed before S1); PAPER C.5 and §6. Dilution: LW-10 F4 and F5. **Missing:** a max or top-quantile cell aggregation (not found; ADD L15 (6) uses the mean); the decoy and F4 are not in PAPER (decision 43); the disjoint source is not chosen (not found in FOCUS). | $0: a max-row cell score as a report beside the mean; choose and seal the disjoint source before S1 (consistency item 8). |
| A-W12 | Over-refusal too coarse; point-estimate feasibility; "feasible" against "worse" | ADDRESSED | UW-06 (τ_O\* = 5 pp); UW-07a (the 500-prompt bank; fired at 11.04 pp, FOCUS 09:37; ADD §7); LW-06 (feasible, infeasible or undetermined by the two-sided 90% interval); UW-05 (R1.3 sets the precedence); PAPER §3.2, §4.2 and C.11. **Open details:** the answer cap (ADD §9; W1-18 is blocked, FOCUS 11:04); PAPER does not say that τ_O = 2 pp is "below the bank's resolution" (DRAFT §6.3). | See consistency item 2. $0. |
| A-W13 | Arms that fail the coherence screen are "not read" | ADDRESSED | LW-09: the arm is read, keeps its place in the family and gets the flag "fails answers end"; DRAFT §3.7; PAPER §4.2 and C.11. The review's label "failed (worse)" was not taken, because it would widen the user's "worse" rule (RC-02). The missingness problem is fixed. | None. |
| A-W14 | Value-of-diagnosis predictions are scored on one menu realization | PARTLY | LW-14 (a) and (i), adopted at the defaults (FOCUS LW): a per-unit proper scoring rule, labelled "a consistency check with one menu"; Llama predictions on wave-1 quantities only. **Missing in PAPER:** §4.9 still lists the predictions as family (5) at 5%; C.7 still scores menu-level P(best found) and regret on Llama. Under UW-19's U0 = W0 (stage 2 not funded at the re-plan's level) the Llama test does not exist (DRAFT §7.2); PAPER does not say so. | Two wording changes (§4.9, C.7). $0. |
| A-W15 | Presentation: density, placeholders, an unseen concurrent submission, "10–12 pp" against "9, 10 or 12 pp" | OPEN | Kept unchanged by the lead (rev 6h ruling 6; risk 48). No design-at-a-glance table (decision 45). Coined terms unchanged. The concurrent submission is still a placeholder (decision 32). | $0: one design table (arm, comparator, seeds, test, sidedness, margin, family) in Appendix C; "about 10 pp at central planning noise (9–12 pp)". |

### 1.2 Review B (LLM safety), W1–W16 and §8.3

| # | Weakness (one line) | Status | Where it is addressed, or what is missing | Cheapest remaining fix (cost) |
|---|---|---|---|---|
| B-W1 | One 1B model, one dataset, one recipe; 7–8B funding-gated; models dated | PARTLY | Olmo-3-7B-Instruct is a third 7–8B model if funded (FOCUS 8dac6ad; PAPER §4.1, §6). The 7–8B full comparison is [PLANNED; funding-gated, fallback one family] (PAPER §4.1; decision 28). Alpaca is planned but has no design (decision 20). **Missing:** any funded or committed 7–8B run; a limitation sentence on reasoning-mode models (risk 49); the 7–8B SESOI branch (REPLAN §7 decision 3; CONS LA-10 H) is open. | Funding, not a freeze item: option C needs $680–1,070 and option B $1,090–1,660 of new money (ESTIMATE, REPLAN §6). $0: one §6 sentence on reasoning-mode models. |
| B-W2 | The data-against-reference headline is not confirmatory; references at 3 seeds; frontier undefined | PARTLY | As A-W3. | Top fix 2. |
| B-W3 | Incoherent actor; customers control LR and epochs; no per-actor menus | PARTLY | PAPER §3.1 (two actors), the Table 1 Actor column, §4.4 (a lower-LR reference "[PLANNED; to be pre-registered]") and §6. DRAFT §9.4 and CONS LS-17 (five actors, each menu fixed before any newly run outcome; S1) are not decided. B↓LR is CONS US-11 (S1; 6 seeds, fallback 3), not decided. The dataset publisher and the transfer test are CONS LA-05 (Later). | Top fix 4: US-11 at 6 seeds, $12–14 (ESTIMATE); fix the actor menus in the frozen text ($0). |
| B-W4 | Per-row loss and recipe confound H1 and the format reading; recipe G changes two things | PARTLY | Promoting H1 under the token-mean loss into the primary family is **DECLINED**: UW-10 (a) keeps it as a 3-seed secondary arm (FOCUS 07:21). Token accounting and the token axis: ADD §5 item 1; EXTR W1-01 and W1-02. R_tok covers H1 (ADD §6 item 5). **Missing:** the share of loss weight on the first five answer tokens per removal arm (not found; EXTR W1-01 reports tokens and steps only). Recipe G's split is the side paper's work (overlap rule). | $0: add the first-five-token share (min(5, n)/n per row under the per-row loss, from P's token counts) to W1-01's table. |
| B-W5 | Strong data-side and post-hoc repairs are missing | PARTLY | SR and S6 are committed as conditional rule text (LW-19, LW-25; family 1c with P7 and P8; DRAFT §9.5). The user's yes is CONS US-10 (S1), open. Safe Delta, Antidote and the survey are cited (PAPER §2). Tülu-style replay and task-format safety data are **DECLINED** for now (CONS LA-03; the user's 9 Oct 09:40 UTC rule keeps PKU-SafeRLHF as the only safety data). Not cited: Eiras et al., backdoor-enhanced alignment, Fraser et al., SORRY-Bench (risk 52). PAPER C.3 still says [TO BE FIXED]. | Top fix 4: US-10 (a), about $24–28 (ESTIMATE). |
| B-W6 | U is not harm; no harm-weighted score; no robustness endpoint; one reader | PARTLY | SRJ and the prefill probe have conditional rule text (LW-24; DRAFT §2.4). Their runs need CONS US-13 (Gemma terms; a 5.1 GB download) and US-14 (S1), both open. Raters: only the LW-30 paragraph; LA-07 is Later. PAPER §4.2 says [TO BE FIXED]. | Top fix 3. |
| B-W7 | Over-refusal and skill limits are underpowered and favour additions | PARTLY | Non-inferiority states (LW-06); the 500-prompt bank (UW-07a; ADD §7); partial refusals per arm (LW-24); R1.3 (UW-05). The full XSTest and OR-Bench-Hard banks are **DECLINED** in the form asked, because their remainder is the hidden held-out bank (UW-07b; PAPER §4.2: "never from the held-out bank"); PHTest replaces them. In-domain refusal is CONS US-12 (S1), open. | US-12 (a): $5–13 (ESTIMATE). |
| B-W8 | Labels can contradict each other; precedence; family membership | ADDRESSED | UW-08 (a) (the label order); the note "significant, below the SESOI"; Φ holds O_k and L_k (UW-04); DRAFT §4.5; PAPER §3.2 and C.11. | None. |
| B-W9 | A1 is gradient similarity to external anchors, not attribution of the behaviour | PARTLY | LW-21 (a): A1 is kept, with its reasons recorded (RB R7.1). V1 ran (Jaccard 0.314 with A1; FOCUS 09:32). V2a has rule text (its pre-set reading: a Jaccard below 1/3 makes the claim bound mandatory); its spend is CONS US-16 (S1), open. The rename in claims (RB R7.2) is CONS LA-13 (Later). PAPER Table 1 and §1 still say "attribution". | $0: adopt R7.2 at the freeze ("a bi-anchored gradient-similarity filter (external harmful anchors)"), given V1's 0.314; V2a $5.6–7.1 (ESTIMATE). |
| B-W10 | Gates B/C and the value-of-diagnosis model take space and money | PARTLY | Detail moved to Appendix C (rev 6); the model output is called secondary (PAPER §3.4). Not done: moving §3.3, §3.4 and Gate C out of the body (decision 33). REPLAN §6's cut list does not include the planted sweep (stage 1b), so no rule cuts it to fund 7–8B work. | $0: decision 33's moves when results need the room. |
| B-W11 | The plant may be trivially findable | ADDRESSED | LW-10 F2 and F8 (text-only ranks are construction checks, published before the pilot; only A1 and the Self-Inf-N-style score count), R8.3 (the prediction "the classifier ranks the planted leaf first at M = 128"), R8.5; ADD §8 item 2; PAPER §4.5 and C.5. A benign-looking plant is **DECLINED** (UW-16; R8.5: A1 would find a He-style plant by construction). | None. |
| B-W12 | Key evidence sits in an unseen concurrent submission; the Qwen exclusion | PARTLY | The Qwen sentence is in PAPER §6 (rev 6c). **Missing:** the anonymized concurrent submission as a supplement (decision 32, at submission); f(θ0) per family and recipe G's partial erosion at 1B (review B Q1; risk 60: "Body: not changed"). | $0: one sentence with f(θ0) per family (3.2% OLMo-2-1B, 13.8% Llama-3.2-1B); attach the side paper at submission. |
| B-W13 | Reads like a pre-registration; placeholders; pre-registrations not attached; the title | OPEN | Title **DECLINED** (UW-14). Attaching the pre-registrations is [TO BE DECIDED] (PAPER Appendix C head; decision 32). Coined terms and a design figure: not done (decisions 9, 45). | $0: attach the frozen texts (anonymized) and add a design figure. |
| B-W14 | Dataset realism; Alpaca adds little diversity | OPEN | Alpaca stays the planned second dataset (decision 20; CONS LA-16). A modern chat or domain dataset is in no plan (not found). | Not a stage-1 freeze item. Cost: not found. |
| B-W15 | HarmBench classifier used outside its validated setting | ADDRESSED | LW-23: HB-1 (the 512-token clip; the Gate B pipeline), HB-2 (per-bank agreement and κ), HB-3 (gate on all 200 prompts); PAPER §4.2 and C.10. PAPER does not mention the per-bank report (minor). | None. |
| B-W16 | Cost is evaluation-dominated and does not transfer | PARTLY | Logging by stage (PAPER C.6; DRAFT §10.1); CONS LS-14's sentence "generation is about 80% of an arm" (S1). **Missing:** a scaling estimate (FLOPs per scorer by size and rows): not found. | $0: the LS-14 sentence in §4.7; a FLOPs table in C.6. |
| B-§8.3 | Two baselines for over-refusal make the ideal addition arm "worse" | ADDRESSED | UW-05 (R1.3); ADD §6 item 3; PAPER §3.2 and C.11. | None (but see consistency item 4 (a) on how R1.3's "infeasible" is tested). |

### 1.3 Literature sweep, §5 design actions 1–5

| # | Design action (one line) | Status | Where it is addressed, or what is missing | Cheapest remaining fix (cost) |
|---|---|---|---|---|
| L-1 | Report tokens removed and steps per removal arm; a token-matched random removal or a covariate | ADDRESSED | ADD §5 item 1; ADD §6 item 5 (R_tok for A1, L1 and H1 at 3 seeds, funded tier; the analysis as fallback); UW-14; EXTR W1-01 (tokens, steps) and W1-02 (dose rule); PAPER §3.2 and C.3 (axis: total row tokens). **Gap:** no R_tok builder exists at origin (`scripts/stage1/` has none). A1 removes 15.5% of the token mass for 12.5% of the rows (FOCUS 09:32), so the token axis matters for A1 too, not only H1. | Build W1-03 before W1 ($0); R_tok runs $13.1, or $19.3 with overhead and × 1.25 (ESTIMATE, EXTR W1-03). |
| L-2 | Decide Safety at One Shot and the opening hold as references, or write why not, before stage 1 | PARTLY | ADD §5 item 4 leaves it to the user; CONS US-06 (S1) is open; its default is "no change". PAPER §2 and §6 bound the one-shot patch ("not compared … no claim here covers them"). The opening hold is not cited in the paper body (decision 27 lists it in the notes only). | $0: decide US-06 under the delegation with a written reason (B+Qi already covers first-token objectives; the patch is post-hoc); cite the opening-hold submission after an API fetch. |
| L-3 | Reframe the opening side study as a replication | OPEN | PAPER §4.10 item 1 is unchanged; "Where the framing is weak" item 6 notes the point. | $0: one §4.10 sentence that cites the concurrent ICLR 2027 submission. |
| L-4 | Gate C: the untuned refusal of each Dolly prompt (SafeOff) and the attribution score's safety-direction share (SABA) | PARTLY | The safety-direction share is **DECLINED** as a pre-registered report (ADD §5 item 3: post-Gate-B exploratory if done). The SafeOff idea was replaced by another report: the untuned model's refusal on each *evaluation* prompt, as a stratifier (ADD §5 item 3 (a); W1-05 ran: 171 of 200 and 13 of 100, FOCUS 09:37). A training-row SafeOff score: not found. Gate C itself is frozen (PREREG revision 5). | If wanted: a scored-only stage-1 scorer (θ0 greedy on the 4,800 Dolly prompts, short cap, the lexicon's opening class), rule text before W1; about $1–3 (ESTIMATE from the wave-0a generation times; UNVERIFIED). |
| L-5 | Record the untuned model's perplexity on each addition arm's 48 rows | ADDRESSED | ADD §5 item 3 (b); EXTR W1-06 (in REQ-9's existing pod pass). | None. |

### 1.4 Counts (37 rows)

| Status | Review A (15) | Review B (17) | Sweep (5) | All |
|---|---|---|---|---|
| ADDRESSED | 4 (W2, W4, W12, W13) | 4 (W8, W11, W15, §8.3) | 2 (L-1, L-5) | **10** |
| PARTLY | 10 (W1, W3, W5–W11, W14) | 11 (W1–W7, W9, W10, W12, W16) | 2 (L-2, L-4) | **23** |
| OPEN | 1 (W15) | 2 (W13, W14) | 1 (L-3) | **4** |
| DECLINED (whole row) | 0 | 0 | 0 | **0** |

Declined parts inside other rows (7): the title (A-W8, B-W13; UW-14); H1 under token-mean loss in the primary family (B-W4; UW-10); Tülu replay and task-format data (B-W5; LA-03); the full XSTest and OR-Bench-Hard banks (B-W7; UW-07b); a benign-looking plant (B-W11; UW-16, R8.5); the safety-direction share (L-4; ADD §5 item 3).

---

## 2. Top 5 OPEN or PARTLY items to fix before the freeze

Ranked by how much each would move an ICML score. Ranks 2–4 are three of review B's four "move to 6" items (MRB §7: items 2, 4 and 3). Ranks 1, 2, 3 and 5 are items 1, 3 and 6 of review A's "move up by 2" list (MRA §8). Costs are ESTIMATES unless marked $0.

### 1. Freeze one consistent text (A-W1; B-W13 in part)
- **Why it matters.** Review A calls an unfrozen protocol "blocking for in-principle acceptance". Today the only pre-registration file (DRAFT revision 2) prints the superseded rules as "in force", and the REQ-21 record does not exist. A reviewer who compares the frozen file with the paper would find more than ten contradictions (§3). Every ADDRESSED row in §1 depends on this step.
- **Fix.** DRAFT revision 3, or the REQ-21 record, that:
  1. replaces each [USER] and [LEAD] proposal by its decided value, citing FOCUS 07:21 (UW-xx), FOCUS LW (LW-xx) and ADD §6–§9;
  2. copies AMD §B.2's Φ edges and AMD §B.3's O_k and L_k nulls verbatim, and states which F_k edge applies under R1.3 (consistency item 4 (b));
  3. adds ADD §7 (PHTest draw), §8 (disjoint anchors, the counting list) and §9 (the cap), with W1-18's current fallback;
  4. sets the paper's "pre-registered" to follow the deposit: keep LW-26's "pre-specified" until an anonymized, timestamped copy with hashes is deposited (OSF or AsPredicted; a public post, so it needs the user's yes, CONS LA-12);
  5. removes PAPER's stale markers (§4.5 and C.5 "nested cells [TO BE FINALISED]"; §4.2 and C.3 [TO BE FIXED] items that LW-19, LW-24 and LW-25 settled as conditional text).
- **Cost.** $0.

### 2. A confirmatory test of "data repair against the references" (A-W3; B-W2)
- **Why it matters.** Both reviewers name it in their "move up by 2" lists. The abstract's FINDING 2 has no test, and PAPER §3.2's "a lower F than the curve at equal O and L" is the sentence both reviewers called undefined.
- **Fix (rule text into the W1 record now, as S-2 requires).**
  - Adopt DRAFT §5.3 / AMD §D.1–§D.4 (CONS LS-06 (a)): "m beats r" if the upper ends of the two-sided 90% intervals are below 0 for U(m) − U(r), below m_O = 5 pp for O(m) − O(r), and below τ_L for L(m) − L(r).
  - The adapter-scaling curve is read at λ\*_m matched on task loss, with λ\*_m = 1 if L̂(m) − L̂(a0) ≤ τ_L; U is tested at λ_lo and O at λ_hi.
  - D_k = beats every built reference (an intersection–union test). Family 1b = Holm over D_1–D_6 at 5%, read after Φ.
  - Replace PAPER §3.2's sentence with this rule and add family 1b to §4.9.
  - Take CONS US-01 (a) under the confirmed ambitious-default rule (UW-01), with US-01 (b) as the pre-set fallback if block B's money does not cover it.
- **Cost.** Rule $0. US-01 (a): about $42–46, plus $9.2–10.1 under layout D1 (CONS US-01, from AMD NUM). The cheapest useful part, the safety prompt, scaling and Safe LoRA on all seven a0 seeds, is about $30–33.

### 3. Measurement that reaches harm, and a real judge audit (A-W6; B-W6; B-W7 in part)
- **Why it matters.** Review A's item 6 (an arm-stratified two-rater audit) and review B's item 4 (StrongREJECT score, prefill probe, two raters). Today only conditional rule texts exist (LW-24, LW-30). An unfunded audit and unrun endpoints add nothing to a review.
- **Fix.**
  - Write LW-30's paragraph as a design: two raters who did not design the study, blind to arm and judge label; strata a0, removals, additions; about 130 judge-Unsafe answers per stratum and about 150 judge-Safe answers (MRA W6 sizes); κ; a misclassification-corrected contrast as a sensitivity; report-only.
  - Add the claim rule's missing cases: the HarmBench contrast with its 90% interval, and the wording for "equivalent" and "inconclusive" contrasts ("restored refusal" only).
  - Take US-13 (SRJ), US-14 (the prefill headroom check, then the reduced scope) and US-12 (in-domain refusal) at their ambitious defaults.
  - Replace PAPER §4.2's [TO BE FIXED] with "secondary, report-only".
- **Cost.** SRJ $2–4 on judge pods; prefill $1.1–1.6, then $9–14 (reduced) or $26–39 (full); in-domain refusal $5–13 (CONS US-12–US-14). Raters: Part 1 $25–50, Part 2 $440–650 for two paid raters (CONS LA-07). The Gemma terms and the 5.1 GB download need the user's explicit yes (the delegation does not cover downloads; compare FOCUS 11:04).

### 4. Robustness of the menu: the customer's lever and stronger data repairs (B-W3; B-W5; L-2)
- **Why it matters.** Review B's item 3. The paper already names a lower-learning-rate reference and two candidate data arms, but none is committed, so a reviewer reads them as promises.
- **Fix.**
  - CONS US-11 (a): B↓LR at 6 seeds (1102–1107), read on the matched-task-loss frontier (AMD §B.6, AMD-4).
  - CONS US-10 (a): SR and S6 at 48 rows and 6 seeds in family 1c (P7, P8; Holm over two; RB R4.3's pre-set fallbacks).
  - CONS US-06: no change, with a written reason (B+Qi covers the first-token-objective class; the one-shot patch acts after fine-tuning).
  - Fix the five-actor menus in the frozen text before any newly run outcome (CONS LS-17).
- **Cost.** B↓LR $12–14; SR and S6 about $12–14 each; about $36–42 in all (CONS US-10, US-11).

### 5. A1's one-shot selection and its claim bound (A-W7; B-W9)
- **Why it matters.** Review A's item 6 asks for attribution scored on 3 or more seeds. The measured stability is moderate (q–e1 top-600 Jaccard 0.434), and the Adam variant overlaps A1's set at only 0.314 (FOCUS 09:32). A null for A1 will be read as "attribution does not pay", which the design cannot support.
- **Fix.**
  1. $0 rule: P1 is stated as conditional on one sealed selection. In every claim A1 is "a bi-anchored gradient-similarity filter (external harmful anchors)" (RB R7.2, moved from Later to the freeze).
  2. Report-only: score A1's bi-anchored cosine on a0 retrains at seeds 1102 and 1103 (checkpoints q and e1), and report top-600 Jaccard and Kendall τ against the sealed set. It never changes the arm.
  3. Take US-16 (V2a).
- **Cost.** Item 2: about 2 × (0.077 h retrain + 3.04 h scoring) × $1.79/h ≈ $11, plus pod overhead, so about $12–15, or $15–19 × 1.25 (ESTIMATE from FOCUS 16 Oct 13:21 UTC timings via DRAFT §10.3 LQ35). V2a: $5.6–7.1 (CONS US-16).

**Also cheap before the freeze ($0 unless marked).**
- A-W9: redefine "replicates" (label agreement, or TOST on the interaction within δ_fam).
- A-W8: per-actor "too close to call" (DRAFT §4.8) plus simultaneous intervals for the 15 pairwise contrasts.
- A-W5: the "better" label's 80% effect in C.11, and fix PAPER §6.
- A-W10: the fresh-seed E and the probe-seed sentence.
- A-W14: the wording of §4.9 and C.7.
- CONS LS-18: commit the confirmation pick rule and "confirmed" as W1 rule text.
- Ask the user for the 8.82 GB Qwen3Guard download, so that W1-18 can run. A 128-token cap would cost $10–27 for O-ext instead of $40–70 (ESTIMATE, DRAFT §6.5): a saving of about $13–60.

---

## 3. Internal consistency: contradictions between the pre-registration, the addendum and the paper

| # | Topic | One side (file, section) | Other side (file, section) | What to do |
|---|---|---|---|---|
| 0 | **The frozen text** | DRAFT rev 2 §0.4 ("T1 … not committed"), §3.2 (S-a "in force"), §4.1 (Holm "in force"), §4.3 (the 18:31 rule "in force"), §6.3 (silent: no primary τ_O), §6.5 (silent: F) | FOCUS 02:42 UTC (T1 committed, 9525005); FOCUS 07:21 (UW-02 to UW-07a); FOCUS LW-01; ADD §6 items 1–4; PAPER §3.2, §4.9, C.11 | Top fix 1. |
| 1 | **Seed counts** | DRAFT §1.2 table (R 1101–1108, 8 seeds; a0 1101–1106, 6) and §1.3 ("silent: D0"; blocks: a0 at 1104 in A and 1105–1106 in B; R to 1105, then 1108) | ADD §6 item 2 and FOCUS 07:21 UW-03 (layout D1: a0 and R at 1101–1107; R_1108 not run); PAPER Table 1 (7 and 7) and C.3 | Re-derive the block layout under D1 (not given anywhere: not found). |
| 1b | B+Qi seeds | PAPER §4.4 ("at six seeds"), no list | DRAFT §5.5 LQ18 and CONS LS-11 (1101–1106 or 1102–1107, open) | Decide LS-11; under HB-C, 1102–1107 gives 6 pairs (AMD §D.1). |
| 2 | **Over-refusal bank and cap** | PAPER C.11: "The PHTest answers are capped at 128 tokens, after a free truncation check …" | ADD §9 (one cap for all 500 prompts and for θ0, a0 and every arm; 128 only if W1-18 passes, else the full cap; θ0 and a0 re-evaluated on the 500); FOCUS 11:04 (W1-18 cannot run on the Mac; until the user's yes, the full cap for all 500, and the 128-token cut is a report-only sensitivity) | Fix C.11 to ADD §9 with both branches; the dev-100 answers are capped too. |
| 2b | The bank | DRAFT §2.2 ("the 100 greedy dev over-refusal answers") and §6.5 ("If the user is silent at W1: F") | ADD §6 item 4, ADD §7; PAPER §4.2 and C.11 (dev 100 plus 400 PHTest) | Part of top fix 1. |
| 2c | τ_O\* "the same bar as G4" | DRAFT §6.3 ("one value holds from Gate B to stage 1"); PAPER C.11 ("the value of Gate B's over-correction guard G4") | ADD §9 (θ0 re-measured on another bank and cap; G4 stays on the dev 100 at the Gate A cap) | Say "the same number (5 pp), on a different bank". The cost of re-evaluating θ0 and seven a0 seeds on 500 prompts: not found. |
| 3 | **δ_fam** | PAPER C.11 and FOCUS 07:21 UW-13 ("for another model family") | PAPER §4.8 (the Llama replication rule has no δ_fam) against AMD §B.6 row 3 ("with δ_fam"); REPLAN §7 decision 3 and CONS LA-10 H (a 10 pp SESOI branch at 7–8B) | State whether OLMo-2-7B counts as "another family". If so, δ_fam is about 4.9 pp (ESTIMATE from the side project's mean E of about 44.1 pp, REPLAN §2.2), against a 10 pp branch. DRAFT §4.2 still says "silent: 5 pp absolute". |
| 4a | **Labels: how R1.3's "infeasible" is tested** | PAPER C.11 ("Feasibility" uses the two-sided 90% interval; "The *infeasible* of rule R1.3 below has this meaning") and DRAFT §4.4 ("O-infeasible at τ_O\* (§6.3)") | AMD §B.3 (inside Φ, O_k's null is "O(m) − O(c) ≤ 0 **or** O(m) − O(θ0) ≤ τ_O\*", an intersection–union test at the node's Φ level, 0.042% at the start) | The two give different "worse (O)" error rates. Pick one text for the freeze. |
| 4b | **Φ's edges** | PAPER C.11 ("the pre-registration fixes how a rejected node passes its weight on") | DRAFT §4.4 ("passing rules as AMD §B.2"); AMD §B.2 has two F_k rows: standard (F_k → O_k 1/2, L_k 1/2) and "Under RB R1.3: F_k → L_k 1" ([LEAD]). Which row is in force: not found | Copy the R1.3 row into the frozen text and say so. |
| 4c | Testing order | PAPER §4.9 (five families; "Everything else is descriptive") | DRAFT §4.6 and AMD §B.6 (order 1, 1b dominance, 1c P7–P8, then 2–5) | Add 1b and 1c to §4.9 once decided (top fixes 2 and 4). |
| 4d | What the labels resolve | PAPER §6 ("The labels resolve differences of about 5 pp") | DRAFT §3.5 (S-5: P(better \| 5 pp) ≤ 0.5; 80% "better" at 5.65–8.52 pp) and AMD §C.4 (HB MDE 6.4–8.5 pp at pair SD 3.3–4.5 pp) | Reword §6 to the planning range. |
| 4e | "Pre-registered" | PAPER abstract ("six pre-registered repairs") | CONS LW-26 ("pre-specified" until REQ-20 and REQ-21 are committed) | Top fix 1. |
| 4f | Placement statistic for planted menus | DRAFT §7.2 (the top-k hit "in force"; row AUC proposed) | CONS LW-11 default (b) (row AUC primary), adopted with all LW defaults (FOCUS LW) | Record which one REQ-18 uses. |
| 5a | **References: "dominates"** | PAPER §3.2 ("lies below this curve: a lower F than the curve at equal O and L") and §1 ("beats five references") | DRAFT §5.3 and AMD §D.1–§D.4 (three non-inferiority bounds against every built reference, B↓LR included if added; curve matched on task loss only; matching on O a sensitivity) | Top fix 2. |
| 5b | Post-hoc reference seeds | PAPER §4.4 ("on three $a_0$ seeds"; "three, or all seven … open") and DRAFT §5.1 (a0 1101–1103 in force) | CONS US-01 (a) (all a0 seeds, λ = 0.9, recipe G and B+Qi at 1102–1107), the recommendation once UW-01 was confirmed; undecided | Decide at the freeze (top fix 2). |
| 5c | Safe LoRA | PAPER §4.4 ("[NOT YET FIXED]") | DRAFT §5.4 (a full settings table: K = 39; base against Instruct), drafted as [LEAD] S1 (CONS LS-07), not decided | Decide LS-07 before any Safe LoRA outcome. |
| 5d | The lower-LR reference | PAPER §4.4 ("A sixth, **lower learning rate** [PLANNED; to be pre-registered]") | DRAFT §5.1 and CONS US-11 (a USER S1 item; not decided) | Decide US-11 (top fix 4), or mark it "candidate". |
| 5e | Timing of S1 rules | PAPER §4.9 ("Before Gate B's category runs, the stage-1 pre-registration … commits … Anything added later is labelled post-Gate-B exploratory") | DRAFT §13.1 (reference seeds and spend, Safe LoRA and B+Qi settings, the c0 job and charging are S1 items, after Gate B outcomes) and DRAFT "New points" N-1 (which act approves the W1 rules is not recorded) | Read literally, the paper's sentence makes every S1 item exploratory. Record N-1's reading in REQ-21 (h) and reword §4.9. |
| 5f | Cost units | PAPER §4.7 and C.6 (FRE = "the median time of its random-removal arms"; lean = "training plus one sample per harm prompt") | DRAFT §10.2 LQ25 and CONS LW-16 (1 FRE = 2,934 s from the three wave-0a ledgers, fixed at W1-P, never re-estimated); CONS LW-15 (a) (lean also holds the task-loss pass and the 100 greedy over-refusal answers; c0 ≈ 0.30 FRE); both adopted at default (FOCUS LW) | Update C.6. Whether the lean screen uses 100 or 500 over-refusal prompts after ADD §7: not found. |
| 6 | **Actor menus** | PAPER §3.1 and Table 1 (two actors: customer C with data, LR and epochs; provider P) | DRAFT §9.4 and CONS LS-17 (five actors, each menu fixed before any newly run outcome); CONS LA-02 (the five-actor text is the user's, Later) | Fix the menus in the frozen text; PAPER's "best repair within each actor's menu" also needs DRAFT §4.5 (S-23) and §4.8's rule. |
| 7 | **R_tok** | DRAFT §9.3 item 1 ("a [USER] proposal … in force: no new arm") and EXTR W1-03 ("Build now (default). Nothing.") | ADD §6 item 5 ("build W1-03's … R_tok for A1, L1 and H1 now"); FOCUS 07:21 UW-14; PAPER §3.2 and C.3 | Build it before W1: no R_tok builder is at origin (`git ls-tree scripts/stage1`). |
| 8 | **Disjoint anchors** | ADD §8 item 1 and PAPER C.5 and §6 (a source "chosen and sealed before the stage-1 freeze (S1) and before any planted run") | DRAFT §8.1–§8.5 (absent); FOCUS (no chosen source: not found) | Choose and seal the source before S1. PAPER C.5 says the set is "built by Gate C's anchor rule (severity, category balance …)". That rule used PKU-SafeRLHF's severity and category labels (PAPER notes: FOCUS 8 Oct 15:53 UTC). A non-PKU source may lack them (I; UNVERIFIED). A download would need the user's yes. The cost of a second A1 scoring pass: not found (ESTIMATE $0–7, depending on whether per-row gradients are reused; UNVERIFIED). |
| 9 | **OLMo 3** | FOCUS 8dac6ad (a third 7–8B model if funded; keep OLMo-2-7B and Llama-3.1-8B; cut after 70B and 32B) and PAPER §4.1 | DRAFT §14.3 (RB U-14: the lead recommends (b), OLMo 3 instead of OLMo-2-7B) and CONS LA-04 (ladder (a), then (b), then (d)) | Mark U-14 and LA-04 superseded. Also PAPER §6 ("Olmo 3 the first model cut") against §4.1 ("first 7–8B model cut"): add "7–8B" in §6 (conflict 84 kept it). |
| 10 | Other stale text | DRAFT §8.4 (the counting list lacks the Self-Inf-N-style score); §8.5 F1 ("in force: the 8 Oct headline text"); §4.2 (δ_fam silent default); §9.1 item 3 (REQ-12 decided "at a named point"). PAPER §4.5 and C.5 ("nested cells [TO BE FINALISED]"); §4.2 and C.3 ([TO BE FIXED] for SRJ, prefill, SR, S6); C.7 ("noise from pooled residuals"); §4.6 ("about 10–12 pp") | ADD §8 item 2 and PAPER C.5; UW-15 and PAPER abstract; UW-13; FOCUS LW-18 (build both before W1); ADD L12 and T1 9525005 (rule frozen); LW-19, LW-24, LW-25 (conditional texts adopted); ADD L15 (1) (fixed SDs 2.65 and 3.85 pp, never σ̂_gate) and LW-12 (ρ grid); PAPER C.1 ("about 9, 10 or 12 pp", kept by rev 6h ruling 6) | Part of top fix 1. |

---

## 4. Re-score of the DESIGN

- **Review A: 5 / 10 (was 4).** W2, W4, W12 and W13, review A's main soundness points, are fixed, and most of W5 is fixed. The headline reference test (W3) is still undefined in the paper and undecided in the rules. The judge audit and A1's selection variance (W6, W7) are not committed. Scale is funding-gated (W9), and no frozen text exists yet (W1). With top fixes 1 and 2 done, 5–6.
- **Review B: 4 / 10 (unchanged; at most 4.5).** None of review B's four "move to 6" items is met. 7–8B is funding-gated. The data-against-reference test is not pre-registered. The lower-LR reference and SR and S6 are conditional, not committed. SRJ, the prefill probe and the two-rater audit are not committed. The non-inferiority limits on a 500-prompt bank and R1.3 fix the core of W7 and §8.3. The reviewer's rule is "any three of these four would move me to 6". Committing top fixes 2–4 at the freeze, about $105–155 (ESTIMATE) plus rater time, meets item 2 in full and items 3 and 4 in part: item 3 also asks for token-mean primary contrasts (declined, UW-10) and item 4 for the full XSTest and OR-Bench-Hard banks (declined, UW-07b). That would justify 5, and 6 only if the reviewer accepts the token axis with R_tok and the PHTest bank as substitutes.

---

## 5. Not found, and limits of this audit

**Not found in the sources:**
- the REQ-21 W1 record;
- a chosen disjoint-anchor source;
- which F_k edge of Φ applies under R1.3;
- the block layout under D1;
- the lean screen's over-refusal prompt count after O-ext;
- the cost of re-evaluating θ0 and a0 on 500 prompts;
- a training-row SafeOff scorer;
- a max or top-quantile cell aggregation;
- a net-benefit estimator;
- pairwise contrasts among the repairs;
- an end-to-end label-pipeline simulation;
- a first-five-token loss share per removal arm;
- a FLOPs-per-scorer table;
- a modern second dataset.

**Limits.**
- I read DRAFT, ADD, CONS, MRA, MRB, SWEEP, REPLAN and the FOCUS entries from 16 Oct 21:05 UTC onward in full.
- I read the paper's body, Appendices A and C, and its notes (revisions 6–6h, decisions, risks, conflicts 64–97) in full. Earlier history was read by search.
- From EXTR I read §3–§4 (W1-01 to W1-08 in full; the rest by register line). From AMD I read §B–§D only.
- I read `review-statistics.md` and `review-consistency.md` by their headings and counts only; DRAFT rev 2 records their fixes.
- I did not read PLAN-S, PREREG, REF, RB or the check notes.
- Costs marked ESTIMATE come from the cited source lines, or from my arithmetic where I say so.

**Commands run.**
- `date -u` (3 times).
- `git fetch -q origin` (exit 0).
- `git log` and `git ls-tree` on the origin ref.
- `git show <ref>:<path>` of the sources into the session scratchpad. One `git show` failed (exit 128): zsh read `$R:r…` as a variable modifier. It was repeated with `${REF}` (exit 0).
- `grep`, `sed`, `awk` and `wc` on those copies; the Read tool.
- One Write (this file).
