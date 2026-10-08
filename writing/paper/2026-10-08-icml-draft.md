# Repairing Safety After Benign Fine-Tuning: A Compute-Matched Comparison of Data Repairs

## Editor's note (delete before submission)

**What this is.** Revision 2 of the draft, written on 8 October 2026 from 14:00 UTC (clock checked). It follows the paper specification (`research/review/2026-10-08-paper-specification.md`, commit f2a9979) as amended by the user's decision relayed by the lead on 8 Oct: the adopted FOCUS.md amendment (commit 4b37ec2, "ADOPTED 2026-10-08T13:53 UTC") and the study plan `research/review/2026-10-08-sharpened-direction-DRAFT.md` (revision 2, still under adversarial review). Where the two disagree, the adopted amendment wins (see "Conflicts" below). **Nothing in the paper body is a result.** Gates B and C, stage 1, the positive control and the Llama stage have not run. Development evidence appears only in this note. Menu sizes, the filter list and costs are marked [TO BE FINALISED] where the plan is not settled. The ICML LaTeX version (`icml/main.tex`) carries the same text with a fetched `references.bib`; the author-year citations below use the venue years of those fetched entries.

**Title.** The spec's working title ends "…, and When Diagnosis Pays". The user's decision makes the measured repair comparison the headline and the decision-value map secondary, so the title now names only the comparison. Alternatives:
1. *Repairing Safety After Benign Fine-Tuning: A Compute-Matched Comparison of Data Repairs, and When Diagnosis Pays* (the spec's title; use it only if the planted sweep is funded and gives the map measured support).
2. *Diagnose or Retrain? A Compute-Matched Comparison of Data Repairs for Safety After Benign Fine-Tuning* (the previous title as a lead-in, as the spec allows).
3. *Choosing a Data Fix When Benign Fine-Tuning Erodes Safety: Diagnosis, Trial Runs and Side Effects at Matched Compute*. This is the DIFFUSE title: the plan (§11) and FOCUS ("agreed fallback") switch to it if Gate B reads DIFFUSE. Its number is kept from the previous draft because the plan refers to it as "alternative title 3".
4. *Remove, Add or Leave the Model Alone? Seeded, Compute-Matched Repairs for Safety Eroded by Benign Fine-Tuning* (stresses the model-level references).

### What changed from the previous draft (8 Oct, about 12:00 UTC)

- **Headline.** The measured repair comparison leads (six repairs × six seeds against random removal and no repair, labels better / equivalent within 5 pp / inconclusive, with over-refusal, task loss and measured cost). The "when diagnosis pays" map is secondary and model-based; its predictions are written down before Gate B's category runs and tested on Llama.
- **Menu.** Stage 1's primary family P1–P6 (A1, L1, H1 removals; S1, S3, S4 additions); secondary arms and scored-only scorers; rewrite and self-distill only in the DIFFUSE branch. The previous draft's keep/remove/add/rewrite menu by source, the default mix a_mix and the "beat a_mix" rule are gone.
- **New parts.** Three mandatory references with no data change (safety prompt, adapter scaling, recipe G); the planted-cause positive control; the HarmBench claim rule; two cost conventions; the Llama rule (LR or rank only); confirmation on a sealed held-out subsample; the opening decomposition (side study).
- **Resolved old decisions.** O is measured against the untuned model (old decision 1); τ_O is a grid of 2, 5 and 10 pp and τ_L is 2 SE of a seed-to-seed difference in held-out loss on all 200 rows (old decision 2); the main scale is 1B with a ladder (old decision 3); a judge rule decides "harm" against "refusal" wording (old decision 4); model-level references are mandatory (old decision 6); side-effect prediction is secondary, on the add arms only (old co-primary).
- **§4 and §6 are written out. §2** adds the published filters, the format paper, DualSelect, Bianchi et al., PTST and MNEME, the DataRx correction and Guo et al.'s Table 2.

### Placeholders

| Where | Marker | Filled by |
|---|---|---|
| Abstract | [PLACEHOLDER: if funded]; [FINDING 1]–[FINDING 3] | the funding decision for the planted sweep; stage 1, the references, Gate B and the sweep |
| §1 | [PLACEHOLDER: if funded]; [TO BE FINALISED] menu sizes 8/32/128 | as above; the plan's review |
| §1, contributions | [FINDING 1]–[FINDING 4]; [ARTIFACT] | stage 1 and Llama; the sweep; Gates B/C and the mechanism study; the decision-value predictions; the anonymized outcome tables |
| §1 | [FIGURE 1] | the repair-comparison figure (restoration with 90% intervals and the ±5 pp band against over-refusal and cost, with the adapter-scaling curve) |
| §3 | the constants δ (5 pp, given), δ_B (8 pp, given), τ_O grid (given), τ_L (rule given, value after Gate A noise), B, the selector rules per (M, B), k_d, φ_j and the V level | the stage-1 pre-registration and the selector spec (committed before Gate B's category runs) |
| §4.1 | [PLACEHOLDER: sizes actually run] | funding (scale ladder) |
| §4.3 | [TO BE FINALISED] secondary arms and the filter list; [PLACEHOLDER: final MDE] | the plan's review; Gate B's pooled noise |
| §4.5 | [TO BE FINALISED] menu sizes; [PLACEHOLDER: runs only if funded] | the plan's review; funding |
| §4.7 | [TO BE FINALISED] costs | measured ledgers; frozen cost conventions |
| §4.10 | [PLACEHOLDER: report against the recorded bound] | the mechanism prediction recorded before Gate B |
| §5, §7 | placeholders | results |
| References | Microsoft page [CITE-CHECK]; Alpaca has no citation | the author |

**[TO BE FINALISED] items (the plan is under review):** (1) the planted menus' sizes (8, 32, 128 cells) and cell rules; (2) the published-filter list: L1 is LARF-style in the primary family; DataShield-style is secondary; Self-Inf-N-style is scored only; SQSD is cited only; bi-anchoring enters as A1's score; (3) all costs: the FRE values, both cost conventions, the cost of each scorer and of A1, the lean-trial cost $c_0$, and the dollar plan (stage 1 about USD 56–98; planted sweep about USD 17–35; core path about USD 215–405; all estimates from the plan, not paper text); (4) the secondary arms and their order.

**Fill-ins for each outcome** (templates, not claims):
- **A repair is better.** F1: "[repair] restores __ pp more than random removal (90% CI a–b), with over-refusal __ pp above the untuned model and task loss within τ_L, at __ FRE; it [does / does not] lie below the adapter-scaling curve". If it does not, the sentence must say that a model-level reference does as well (FOCUS "do not claim": data repair beats model-level repair).
- **Everything equivalent.** F1: "every removal repair is equivalent to random removal within ±5 pp; [addition result]". This is a publishable answer; the abstract then says it.
- **A free reference wins.** F2: "a safety prompt / a down-scaled adapter restores as much as any data repair at lower over-refusal" (plan §13: a valid, reportable answer).
- **Planted cause found / not found** (only if funded). F3: "[diagnostic] ranks the planted cell first at M = __ ; runs alone find it at __ FRE".
- **DIFFUSE.** F3: "no Dolly category restores more than 8 pp beyond random removal (80% detection at about 10–12 pp)". Switch to alternative title 3; the planted sweep becomes the only test of whether diagnosis can pay.
- **Harm wording.** Use "restored refusal" unless the HarmBench rule (§4.2) passes for that contrast; never "harm" if E_HB < 20 pp.

### [CITE-CHECK] items

| # | Item | Where | Why |
|---|---|---|---|
| 1 | TOSS (2603.01185) | §2 | Title and venue now fetched ("Token-level Data Selection for Safe LLM Fine-tuning", ICLR 2026). The claim "token-level selection" rests on the title only. |
| 2 | Unforgotten Safety (2512.10150) | §2 | Fetched ("…with Continual Learning"); claim from the title only. |
| 3 | Yin & Rush (2410.16208, ICLR 2025) | §1, §2 | Wording ("almost never compute-optimal"; 5x and 10x model-size ratios) from the arXiv abstract, read this session. The spec's "predicts retraining wins at equal size" is our inference from the 10x ratio; check the paper before using it. |
| 4 | TuneAhead (2606.17660) | §2 | Fetched; claim from the title only. |
| 5 | Data2Behavior (2602.04735) | §2 | Fetched; claim from the title only. |
| 6 | SafeTune: model-level repairs, single deterministic runs | §2 | Recipe and runs PDF-checked (benign-erosion recipes note); "compares repairs of safety drift" from the title and a fetch summary. |
| 7 | DataRx mechanism ("gap between the model's own response and a safe reference") | §2 | From the arXiv abstract (this session). The numbers 59.23% and 13.70% are in the abstract; 20.24% is Table II (recipes note, PDF read); "averaged over seven tasks" is the abstract's wording. The plan reads (by HTML fetch, not PDF) that DataRx's random arm draws refusal-only rows; that is why S1 is the DataRx test. |
| 8 | DataShield and GradShield report scoring cost without charging it against runs; DataShield's mechanism | §2 | Cost claim: fetch summaries only. Mechanism (compliance direction): DataShield's abstract (this session). DataShield's cost table (Table IV) is cited by the plan from the reading list (LARF 0.17 h, DataShield 0.50 h, bi-anchoring 3.5 h per 10,000 rows); not PDF-checked. |
| 9 | SOURCE "reported to cost several training runs" | §2 | Reported through the Bergson paper; not checked. |
| 10 | LESS as "gradient similarity on LoRA gradients" | §2 | Reading-list summary. |
| 11 | Persona vectors | §2 | Blog post via the problem-validation review; confirm in 2507.21509. |
| 12 | DataDecide; Ivison et al. | §2 | Positioning review, from an extraction-tool read. |
| 13 | Xiao & Aranguri | §2 | Abstract only ("over 10 times cheaper"). |
| 14 | Microsoft fine-tuning safety documentation | §1, refs | Read on 6 Oct; re-check before submission; no URL in the bib. |
| 15 | Venues and author order | refs | ADMIRE-BayesOpt: TMLR lists Ouyang first, arXiv lists Chen first (bib follows TMLR). DATE-LM year set to 2025 from the venue string. |
| 16 | LARF (2507.18631, EMNLP 2025) | §2 | Mechanism from the abstract (this session). |
| 17 | SQSD (2605.04572, ICML 2026) | §2 | Mechanism and acronym from the abstract (this session). "Its scoring needs several FRE" is the plan's estimate (6–14 FRE), not the paper's. |
| 18 | Self-Inf-N (2505.06843, ICML 2025) | §2, §4.3 | "100 outliers break safety; most mitigations fail" from the abstract (this session). Using its score as a removal filter is our adaptation. |
| 19 | "Bi-anchoring" as He et al.'s method name | §2, §4.3 | The reading list's name; check He et al.'s own term. |
| 20 | Form over content (2609.19589) | §1, §2 | Abstract only (here and in the repo's arXiv search file). |
| 21 | DualSelect (2606.09866) | §1, §2 | Abstract (this session): joint task and reference selection, 1B–8B models. "Compares random, SafeInstr, SEAL, LARF, TOSS and SQSD with three seeds and a false-refusal rate" comes from the plan's novelty review (HTML §4), not re-read. |
| 22 | Bianchi et al. (ICLR 2024): 3% safety data helps, with exaggerated safety | §2 | Abstract (this session). |
| 23 | MNEME (EMNLP 2025) predicts side effects | §2 | Abstract (this session). |
| 24 | Instrument citations (OLMo 2, Llama 3, Qwen2.5, Qwen3Guard, Granite Guardian, HarmBench, StrongREJECT, SimpleSafetyTests, XSTest, OR-Bench, PKU-SafeRLHF, LoRA, ARC, Dolly) | §4 | Fetched. Check that each cited report covers the version used (Granite Guardian 3.3 8B; Qwen3Guard-Gen-4B; Llama-3.2 under the Llama 3 report; OLMo-2-0425-1B under the OLMo 2 report). Dolly's entry is the dataset card's own BibTeX (a blog post). Alpaca (§2, §4.8) has no citation yet. |

PDF- or full-text-checked in the repo, and used as such: Qi et al. (2024), He et al., Luo et al. (2026b), Pan et al., DATE-LM (verification log, 6 Oct); Kim et al. (2025), SafeTune's recipe, PTST, DataRx's Table II (benign-erosion recipes note); Guo et al. including Table 2 (7.27, 4.50, 9.09, 44.80 confirmed), Springer et al. (safety-landscape note); Llama 3's safety mix (problem-validation review); Qi et al. (2025) on first-token alignment (erosion-amplifiers note). Guo's "two seeds" is the Table 2 caption; the Guo-gap note finds no seed-69 checkpoint for the 5,000-row cells.

### Decisions the author must make

1. **Title** (above).
2. **The label set and the two-sided contrast.** P4 (S1 − a0) is two-sided (DataRx predicts worse, Bianchi et al. predict better), but the adopted labels are only better / equivalent / inconclusive. Decide whether a significant result in the harmful direction gets its own label ("worse") or is reported as "inconclusive" with its estimate. §3.2 is silent on it.
3. **The planted sweep's funding.** If it is not funded, "menu size" leaves the headline: delete contribution 2, the planted part of the abstract and Figure 1's menu-size panel, and §3.4 shrinks to one sentence.
4. **Preliminary-results section.** The spec does not ask for one, so the body has none. Gate A's numbers and their disclosures stay in this note until §5 is written. Decide whether a section labelled "Preliminary results (development evidence; not confirmatory)" should carry Gate A.
5. **Filter list and secondary arms** ([TO BE FINALISED]).
6. **Venue and length.** The adopted amendment targets TMLR or NeurIPS 2027; ICML 2027 only if, by about 1 December, the planted sweep, both 1B families and one 7–8B published-setting replication are funded. The LaTeX build uses the ICML 2026 style; see the page count in the build log. NeurIPS allows 9 pages; TMLR has no strict limit. ICML needs an Impact Statement (missing).
7. **The Gate B and Gate C rules** in §4.6 summarize the DRAFT pre-registration (revision 3), which awaits the user's acceptance. Update §4.6 if it changes.
8. **The opening decomposition's definition** (§3.6) must match the exploratory note's "composition share"; the note does not state its formula in these terms. Fix the order of terms and report both orders.
9. **Gate names.** Keep "Gate A/B/C" or call them pre-registered checks.
10. **Who the user is** (§6): the plan names a fine-tuning service that must ship the customer's adapter and may change only data, or a data-only pipeline. Confirm this wording.

### Risks a reviewer will raise (sources in brackets)

1. **"Unsafe" means "did not refuse".** See the development evidence. Answer: the HarmBench claim rule, hard-category U, U by length band, the selectivity score, and claim wording [Gate A audit, 4a; plan §4.2].
2. **Forking paths.** Five settings were screened before OLMo-2-1B fell in the 20–55 pp window, fixed after the Qwen results; seed 1101 both chose the setting and counts in the mean [audit, 4b]. Answer: report every setting tried and the fresh-seed mean (+45.9 pp).
3. **Recipe dependence.** Recipe B is aggressive (r64, per-row mean loss, no warmup). Answer: recipe G as a mandatory reference; the Llama rule (LR or rank only); H1 under a token-mean loss as a secondary arm.
4. **Nulls everywhere.** A 600-row filter clears the MDE only if the findable effect is about 11–14 pp at row AUC 0.9 [plan §1 item 16, POW Part 3]. Answer: equivalence labels make nulls informative; the planted control; the dose curve.
5. **Additions win on U by construction.** Refusal rows restore refusal, and U tracks refusal [plan §13]. Answer: the HarmBench rule, selectivity, O against the untuned model, and the adapter-scaling curve.
6. **A free reference may beat every data repair** (safety prompt, adapter scaling) [plan §13]. That is a valid answer; say so.
7. **Prior-work overlap** (DualSelect, Yin & Rush, DataShield's cost table). Answer: no "first" claims (§2 "How we differ"); the equivalence bounds, references, positive control and pre-registered predictions are the contribution.
8. **Re-implemented baselines.** The four method repositories have no licence [plan §5.1, FIL]; all scorers are re-implemented ("X-style") with deviation tables; authors are asked for reference outputs; stage 4's published-setting replication checks fidelity.
9. **Diffuse erosion is the expected Gate B outcome** [Gate B draft §8; audit §7]. Under this framing it no longer collapses the paper: stage 1 runs unchanged, and the planted sweep carries the diagnosis question.
10. **The plant may not erode** above the background [plan §13]; the pilot gate decides.
11. **Small scale favours trial runs; cost ratios change with size.** No 1B cost ratio is claimed for 7–8B.
12. **The decision-value map is a model output** at the menus we can afford [plan §0, NOV-2, MET-M1]. Answer: it is secondary, frozen before the data, and scored against measurements and on Llama.
13. **Judge precision on benign prompts.** After fine-tuning Qwen3Guard labels 22–29% of the benign bank Unsafe (untuned 5%) [audit §5].
14. **"Adding a little safety data is known to work."** **Correction (FAQ second review, 8 Oct; source opened):** DataRx does NOT show that adding works by default. Its 59.23% → 13.70% compares a *random* 1% BeaverTails mix with DataRx's *selected* 1% mix on Llama3-8B. The fine-tune with no safety data scored 20.24%, so the random mix made it worse. So *which* safety data is added decides whether adding helps (now P4 and P5). Guo's 10 rows were not checked for over-refusal.
15. **Added data can hide misalignment** that returns on prompts like the training data (Dubiński et al.) [reading list v2, risk 4]. The plan adds an overlap control: the add effect must hold on the eval prompts least similar to the add set.
16. **Motivation.** We found no public evidence that practitioners weigh attribution against retrains [problem-validation review]. The draft does not claim that they do.
17. **Money.** About USD 17.50 on hand against a core path of about USD 215–405 [plan §10, §13]. Every stage starts on a funding event; only complete seed blocks are analysed.

### Where the framing is weak (the drafter's view)

1. **The cost axis is mostly evaluation.** Generation is about 81% of an arm and training about 8% [plan §1 item 6]. FRE then measures our evaluation size more than training; the two cost conventions help, but a reviewer may still read "compute-matched" as "evaluation-matched". Say plainly what one FRE buys.
2. **The comparison fixes doses.** Rankings across removal (600 rows) and addition (48 rows) hold only at these doses; the dose curve is secondary and 3-seed.
3. **Category units versus row scorers.** Gate B tests categories; stage 1 tests row scorers. A row scorer can find what Gate B cannot, and the reverse; the paper must not read one from the other.
4. **The data-only user and diagnostics pull against each other** (previous draft, point 2): a closed-service customer cannot run attribution; a developer with open weights also has model-level repairs. The references now make this explicit, but the population that benefits from paid diagnosis stays narrow.
5. **Mechanism tests are thin.** Recipe G changes loss weighting and schedule at once; the first-token margin is one teacher-forced pass. Both are side studies.

### Development evidence (for the author only; never a finding in the abstract or the contributions)

- **Gate A PASSED on OLMo-2-0425-1B-Instruct** (8 Oct, 05:40 UTC): E = +43.5, +43.7, +48.2 pp over three seeds; mean +45.1 pp (band 41.3–49.0; partial); fresh-seed mean +45.9 pp; answers end; held-out Dolly loss 2.10 → 1.54; Granite agrees. Independent audit: sound with caveats.
- **Audit disclosures:** P(Unsafe | no refusal) 0.91–0.94 after fine-tuning; about a third of Unsafe answers carry only "unethical acts" or "politically sensitive"; E under hard categories only is about 28 pp; five settings screened; 2 df for seed variance; the ARC bar is near chance at 1B (untuned 0.392).
- **Qwen2.5-1.5B and 7B-Instruct saturate** under recipe B (+75.2 and +82.2 pp); rank 16 still gives +67.8 pp. Guo-gap analysis: judge and prompts explain at most about 13–30 pp of the gap to Guo's Qwen LoRA cell.
- **Mechanism (exploratory note):** refusal openings fall by about 50 pp (OLMo) and 85 pp (Qwen); the opening switch carries about 0.42–0.64 of OLMo's Unsafe increase; direct answers also became more harmful; the erosion is broad across prompts and stable across seeds. Recorded prediction: a first-token path alone gives at most about 3 pp per category, so a LOCALIZED Gate B would need a content effect.
- **Over-refusal:** untuned OLMo refuses 17/100 benign prompts; after fine-tuning 4–6/100. v2's base-model positive control: a classifier-targeted rewrite cut sampled unsafe answers from 80.3% to 11.4%, but XSTest-safe refusals rose from 1/50 to 22/50 in both seeds.
- **Cost of an arm** (one Gate A ledger): training 245 s, greedy generation 1,750 s, sampled generation 761 s, guard and scoring 293 s; about 3,115 s; A100 at USD 1.59/h.
- **Planning noise:** clustered SE(U) 2.8 pp per arm; seed SD 2.65 pp (2 df). MDE after Holm's first step about 5.0 pp (removal) and 5.3 pp (add) at central noise; Gate B detects 8 pp about half the time and reaches 80% at about 10–12 pp.
- **Recorded prior:** DIFFUSE or TOO CLOSE is more likely than LOCALIZED at Gate B.
- **Status (spec §9 and FOCUS, 8 Oct):** recipe G causal test pre-registered and running; Llama-3.2-1B probe pre-registered (queued or running; the spec says both); HarmBench compliance judge running on the Mac; Gate B/C pre-registration revision 3 awaits the user's acceptance.

### Conflicts between the sources, and how this revision resolves them

1. **Spec RQ2 (the map co-primary, the headline figure) vs the user's decision (map secondary, model-based).** Followed the user's decision: the measured comparison leads the title, abstract, §1 and contributions; the map is §3.5, secondary, with predictions frozen before Gate B's category runs and scored on Llama. Figure 1 is now the repair comparison.
2. **Spec repair menu (category, cluster or row removal by heuristic, filters, attribution, representation similarity; random vs selected mix; "10 rows"; recipe-only) vs the adopted stage-1 design.** Followed the adopted design: six primary arms (A1, L1, H1, S1, S3, S4) at 600 removed or 48 added rows; recipe G is a reference, not a repair; category removal stays in Gate B; cluster menus exist only as the planted sweep's nested cells; the "10 rows" dose is an option, not the plan.
3. **Spec "Qwen is the fragile contrast" vs "do not claim Qwen is uniquely fragile at 7B".** Qwen appears only as context in §4.1 and §4.10 (its results are in this note), with Guo et al.'s Table 2 showing a Qwen2.5-7B LoRA cell that barely erodes.
4. **Previous draft vs spec on O's reference.** Spec and amendment: the untuned model (a0 reported). Applied.
5. **Previous draft's rewrite and self-distill fixes.** The amendment drops them from the core menu; one rewrite arm runs in the DIFFUSE branch (§4.6).
6. **Previous draft's co-primary side-effect prediction.** Secondary, on the add arms only (§4.10).
7. **The brief's "keep the Guo Table 2 wording".** Neither previous file contained it; it is now in §2.
8. **Spec §9 vs §5 on the Llama probe** ("queued" vs "running"): not paper text; noted above.

**Sources read:** the paper specification (in full); the adopted FOCUS amendment (commit 4b37ec2) and FOCUS's dated entries of 6–8 Oct; the sharpened-direction plan (revision 2, in full); the Gate A audit; the kill-test Stage 0 results record (Gate A); the Gate B/C pre-registration draft (revision 3); the mechanism note; the Guo-gap analysis; the safety-landscape note; the erosion-amplifiers note; reading list v2 (groups 4–5 and the DataRx correction); the benign-erosion recipes note (DataRx); the kill-test design (measurement table). Abstracts fetched this session for the new citations.

---

**Anonymous Authors**

## Abstract

Fine-tuning a safety-tuned language model on benign instruction data can erode its refusals of harmful requests. When only the training data may change, the owner must choose a repair: remove some rows, or add safety data. Many repairs have been proposed, but they have rarely been compared on equal terms, with training seeds, side effects and their compute counted. We measure which data repair restores the most safety for the compute spent without raising over-refusal or losing task skill. After benign fine-tuning of OLMo-2-1B-Instruct, six pre-registered repairs, each run with six training seeds, are compared with random removal of the same size and with no repair: removal of rows chosen by training-data attribution, by a representation filter or by a free answer-length rule, and addition of random, selected or self-generated refusal examples. Each repair is labelled better, equivalent within 5 percentage points, or inconclusive, and reported with its over-refusal, task loss and measured cost. Three references that change no data (a safety prompt, a down-scaled adapter and a standard recipe) set the bar that a data repair must clear, and Llama-3.2-1B-Instruct replicates the comparison. Pre-registered gates test whether the erosion is localized in data categories, a positive control tests whether diagnostics find a planted cause [PLACEHOLDER: if funded], and model-based predictions of when diagnosis pays are written down in advance and scored on the second family. We find [FINDING 1: the labels of the six repairs]; [FINDING 2: how the best data repair compares with the references]; and [FINDING 3: whether the erosion is localized, and whether diagnostics find the planted cause].

## 1 Introduction

Fine-tuning a safety-tuned ("Instruct") language model on data that contains nothing harmful can still erode its refusals of harmful requests. Qi et al. (2024) observed this after one epoch on ordinary instruction data sets (Alpaca, Dolly) for Llama-2-7b-Chat and GPT-3.5 Turbo; He et al. (2024) showed that benign rows selected for their similarity to harmful examples erode safety far more than random rows; and Guo et al. (2026) report that 100 random benign rows of full fine-tuning raise attack success sharply on recent 8B-class Instruct models. The size of the effect depends on the recipe (Kim et al., 2025). When a fine-tune does erode safety, its owner often controls only the data: commercial fine-tuning services screen training data, gate the tuned model on a safety evaluation, and report harm categories rather than rows, leaving the customer to fix the data and resubmit (Microsoft, 2026).

Repair is then a data decision with side effects. One can *remove* rows: published filters score benign rows by their contribution to erosion (He et al., 2024; Guan et al., 2025; Li et al., 2025; Wang et al., 2026b; Zhang et al., 2026b), and training-data attribution ranks rows by gradient similarity to harmful examples (Jiao et al., 2025; Pan et al., 2026). One can *add* safety data, but which data are added decides the outcome: on Llama3-8B-Instruct, averaged over seven downstream tasks, a random 1% mix of safety rows raised attack success from 20.24% (no safety data) to 59.23%, while DataRx's selected 1% mix lowered it to 13.70% (Zhang et al., 2026a). Safety data can also cause over-refusal (Bianchi et al., 2024; Luo et al., 2026b). And some repairs need no data change at all: a safety prompt used only at test time (Lyu et al., 2024) or a gentler recipe (Kim et al., 2025). Every data repair costs compute, and the only direct evidence about it is a retrain.

Which repair works best is an empirical question that published results do not settle. Each repair was evaluated in its own setting, with its own models, judges and baselines, mostly with one or a few training seeds, and seldom with its scoring compute charged against the alternative of retraining [CITE-CHECK]. The closest comparison we found, DualSelect (Chen et al., 2026), compares several selection methods with three seeds and a false-refusal rate [CITE-CHECK], but not addition repairs, model-level references or measured cost. Three results suggest that expensive diagnosis may not pay. Once selection compute is charged, powerful data-selection methods are almost never compute-optimal (Yin & Rush, 2025) [CITE-CHECK]. Gradient-based attribution tracks the answer format of training examples more than their task (Kim et al., 2026) [CITE-CHECK], so a free format or length rule may match it. And the erosion may be diffuse: even subsets selected for low conflict with safety still erode it (Guo et al., 2026), and Springer et al. (2026) argue from theory that better curation cannot remove the fragility.

We therefore measure repairs directly (§3, §4). On OLMo-2-1B-Instruct fine-tuned on 4,800 Dolly rows, six repairs fixed in advance are each run over six training seeds and compared with random removal of the same size and with no repair: three removals of 600 rows (ranked by training-data attribution, by a representation filter in the style of LARF, and by answer length) and three additions of 48 refusal examples (drawn at random, selected in the style of DataRx, or written by the untuned model itself). Each contrast is labelled *better*, *equivalent* (its 90% interval lies within ±5 percentage points, pp) or *inconclusive*, after Holm correction. Over-refusal, measured against the untuned model, and task loss on held-out rows are feasibility limits. Cost is measured in GPU-seconds and in full-run equivalents (FRE) under two conventions. A data repair counts as dominant only if it beats three references that change no data: a safety prompt at test time, the fine-tuned adapter scaled down, and a standard-practice recipe. Llama-3.2-1B-Instruct replicates the comparison under a recipe rule fixed before its result.

Three pre-registered parts surround the comparison. Gate A requires erosion beyond seed noise. Gate B asks whether the erosion is *localized*: does removing one Dolly category restore more safety than removing the same number of random rows? Gate C asks which diagnostic picks the culprit category, and whether a format rule explains attribution's pick. A positive control plants a known eroding cause in one cell of nested menus of 8, 32 and 128 cells [TO BE FINALISED] and asks whether each diagnostic finds it, and at which menu size diagnosis beats trial runs [PLACEHOLDER: if funded]. A secondary, model-based analysis predicts when paying for a diagnostic beats spending the same compute on trial runs selected by successive halving (Jamieson & Talwalkar, 2016; Li et al., 2018); its predictions are written down before Gate B's category runs and scored on the second family. A side study asks what the fine-tuning breaks: the refusal opening of an answer, the harmfulness of its content, or both. Every decision rule is committed before the data it judges; outcomes are replicated over training seeds, confirmed on held-out prompts, and reported as *too close to call* when the evidence cannot separate options.

Our contributions are:

- **A measured comparison of data repairs with equivalence bounds** (§3.2, §4.3–§4.4): six removal and addition repairs against random removal and no repair, over six training seeds each, labelled better, equivalent or inconclusive, with over-refusal, task loss and measured cost, against three references that change no data, on two model families. [FINDING 1: the six labels, and which repair, if any, beats the references]. We release the menus, seeds, outcome tables and costs [ARTIFACT].
- **A positive control for diagnosis** (§3.4, §4.5): [FINDING 2: whether each diagnostic ranks a planted cause first, and the runs-only cost of finding it, at menu sizes 8, 32 and 128] [PLACEHOLDER: if funded].
- **Where the erosion lives** (§4.6, §4.10): [FINDING 3: the Gate B verdict with its detection limit; Gate C's reading with the format control; the share of the erosion that runs through refusal openings].
- **Pre-registered predictions of when diagnosis pays** (secondary; §3.5): [FINDING 4: predicted against measured value of diagnosis on the category and planted menus, and on the second family].

[FIGURE 1: the repair comparison. For each repair, the safety restored against random removal or no repair, with its 90% interval and the ±5 pp equivalence band, plotted against over-refusal (left) and measured cost in FRE (right); the adapter-scaling reference curve is drawn in the left panel.]

Section 2 positions the work. Section 3 defines the contrasts, labels, limits, the positive control and the secondary decision analysis. Section 4 gives the design. Section 5 reports results, including every too-close-to-call contrast. Section 6 discusses limitations, chiefly what the safety judge measures, the recipe and the scale.

## 2 Related Work

**Safety erosion under benign fine-tuning.** Qi et al. (2024) showed that fine-tuning aligned models on benign instruction data degrades safety, though less than harmful data does, with no training seeds reported. He et al. (2024) selected benign rows by representation and gradient similarity to harmful anchors; in their best case, 100 such rows gave over 70% unsafe answers against under 20% for random rows. This shows that benign rows *can* erode safety, not that ordinary fine-tunes have a localized cause. Kim et al. (2025) change the size of the erosion several-fold through optimization choices alone. Guo et al. (2026) find that 100 random benign rows of full fine-tuning erode recent 8B-class Instruct models, and that a handful of safety rows restores safety after a small attack. Under LoRA their results depend on the family: in their Table 2, Qwen2.5-7B-Instruct reads 7.27% before fine-tuning, 4.50% after 100 rows and 9.09% after 5,000 rows (two seeds), while Llama-3.1-8B-Instruct rises to 44.80% at 5,000 rows. Springer et al. (2026) explain erosion geometrically, as benign updates curving into a sharp, safety-relevant subspace.

**Removal repairs: filters and attribution.** Published filters score benign rows for their contribution to erosion. DataShield projects rows onto a compliance direction (Zhang et al., 2026b); LARF uses representations of safety-sensitive layers (Li et al., 2025); SQSD projects each row's parameter update onto danger and safety directions (Wang et al., 2026b); bi-anchoring compares a row's gradients or representations with harmful and safe anchors (He et al., 2024); and Self-Inf-N, proposed as an attack, finds outlier benign rows whose fine-tuning breaks safety (Guan et al., 2025) [CITE-CHECK]. Row filters report their scoring cost without charging it against runs (Zhang et al., 2026b; Hu et al., 2026) [CITE-CHECK]; other defences select tokens (Li et al., 2026) or use continual learning (Alssum et al., 2025) [CITE-CHECK]. DualSelect (Chen et al., 2026) selects task rows and safety references jointly and compares it with filters including LARF, TOSS and SQSD [CITE-CHECK]. For attribution, Pan et al. (2026) find that removing rows flagged by gradient-based attribution gives a safer retrained model than removing rows flagged by WildGuard, from one training run per arm and with no compute reported. DATE-LM (Jiao et al., 2025) finds that with safety-aligned look-alikes in the data, attribution's detection drops while LLM classifiers are largely unaffected; without them, the strongest classifiers detect better, yet removing attribution's picks gives the safer retrained model. Luo et al. (2026b) report weak, inconsistent effects from deleting or reweighting influential rows, large effects from rewriting them, and an over-refusal trade-off for safety rewriting.

**Addition and model-level repairs.** Adding about 3% safety examples to instruction tuning improves safety but can cause exaggerated refusals (Bianchi et al., 2024) [CITE-CHECK]. Which rows are added matters: DataRx selects safety rows by the gap between a model's own response and a safe reference (Zhang et al., 2026a) [CITE-CHECK], and its random mix made the model less safe than no safety data, while its selected mix made it safer (§1). Guo et al. (2026) restore safety with a handful of safety rows, and Llama 3's safety mix was tuned by repeated experiments that traded violations against false refusals (Grattafiori et al., 2024). Model-level repairs change no data: a safety prompt used only at test time reduces erosion (PTST; Lyu et al., 2024), SafeTune compares repairs of safety drift in single deterministic runs (Seth et al., 2026) [CITE-CHECK], and a gentler recipe shrinks erosion (Kim et al., 2025). We use such repairs as references that a data repair must beat.

**Attribution, its cost and what it tracks.** Training-data attribution ranges from cheap gradient similarity on LoRA gradients (LESS; Xia et al., 2024) [CITE-CHECK] to estimates of finite removal effects by unrolled differentiation (SOURCE; Bae et al., 2024), which are reported to cost several training runs [CITE-CHECK]. Xiao & Aranguri (2026) compare the cost of diagnosis methods for undesirable post-training behaviours; probe attribution is over ten times cheaper than gradient attribution and LLM-judge baselines in their study. Yin & Rush (2025) charge selection compute against training compute and find that powerful selection methods are almost never compute-optimal; gradient-based selection pays only when the trained model is about ten times larger than the selection model [CITE-CHECK]. Kim et al. (2026) find that gradient similarity tracks answer format more than task [CITE-CHECK]; we therefore include a free answer-length rule as a repair and as a control for attribution's picks.

**Predicting outcomes and side effects.** Persona vectors (Chen et al., 2025) project training data onto activation directions to flag data that will shift a trait [CITE-CHECK]. TuneAhead (Luo et al., 2026a) and Data2Behavior (Wang et al., 2026a) predict a fine-tune's outcome from its data before training, and MNEME predicts side effects of fine-tuning and unlearning by sparse model diffing (Kassem et al., 2025) [CITE-CHECK]. Any such predictor can enter our comparison as a scorer at its measured cost; side-effect prediction is a secondary analysis here (§4.10).

**Decisions under a compute budget.** Successive halving and Hyperband allocate a fixed budget across candidates by repeatedly discarding the worst at increasing fidelity (Jamieson & Talwalkar, 2016; Li et al., 2018); multi-fidelity methods model how cheap observations relate to full ones (e.g. Ouyang et al., 2025). DataDecide (Magnusson et al., 2025) scores small pretraining runs by decision accuracy against compute, and Ivison et al. (2025) charge selection compute against training on more data [CITE-CHECK].

**How we differ.** We do not claim a first benchmark of safety filters, a first comparison of removal against addition, or a first pricing of data selection: DualSelect, DataShield's cost table and Yin & Rush (2025) each cover part of this ground [CITE-CHECK]. Our contribution is the combination; to our knowledge, and not found by our search, no prior work combines equivalence-bounded contrasts over six training seeds for removal and addition repairs; over-refusal and task loss as limits; measured costs under two conventions; model-level references that a data repair must beat; a positive control with a planted cause; and predictions about the value of diagnosis written down before the data.

## 3 Problem Setup

### 3.1 Setting and endpoints

Let $\theta_0$ be a safety-tuned Instruct model, fine-tuned with a fixed recipe $\mathcal{R}$ (adapter, loss, optimizer, schedule, length rule) on benign data $\mathcal{D} = D_1 \cup \dots \cup D_K$, split into $K$ *units* by metadata fixed before any outcome. A *repair* $a$ maps $(\mathcal{D}, \mathcal{R})$ to a training set and recipe $(a(\mathcal{D}), \mathcal{R}_a)$; a data repair keeps $\mathcal{R}_a = \mathcal{R}$. The model trained with seed $s$ (adapter initialization and data order) is $\theta(a,s)$. For a model $\theta$, $f(\theta)$ is the *unsafe rate* (the share of sampled answers to a harm bank that a frozen judge labels unsafe), $\ell(\theta)$ is the held-out *task loss*, and $r(\theta)$ is the *over-refusal rate* on benign prompts that resemble harmful ones. Endpoints average over seeds: $F(a) = \mathbb{E}_s[f(\theta(a,s))]$, and likewise $\bar\ell(a)$ and $R(a)$. With $a_0$ the fine-tune without repair, the *erosion* is $E = F(a_0) - f(\theta_0)$; repair is meaningful only when $E$ exceeds seed noise (Gate A, §4.6).

### 3.2 Repair contrasts, limits and labels (primary)

Let $a_{\mathrm{R}}$ remove the same number of random rows as the removal repairs. A removal repair $m$ is compared with random removal, $\Lambda_m = F(a_{\mathrm{R}}) - F(m)$: the safety it restores beyond removing the same amount of data at random. An addition repair is compared with no repair, $\Lambda_m = F(a_0) - F(m)$, and a selected or self-generated addition with the random addition of the same size. The restoration $G_m = F(a_0) - F(m)$ is reported for every arm. Contrasts are estimated from per-seed unsafe rates as differences of means over unpaired seeds, with the variance pooled across arms.

Side effects are the *over-refusal excess* $O(m) = R(m) - r(\theta_0)$, against the untuned model ($R(m) - R(a_0)$ is also reported), and the *task-loss increase* $L(m) = \bar\ell(m) - \bar\ell(a_0)$. A repair is *feasible* at limits $(\tau_O, \tau_L)$ if $O(m) \le \tau_O$ and $L(m) \le \tau_L$. Results are reported at $\tau_O \in \{2, 5, 10\}$ pp; $\tau_L$ is two standard errors of a seed-to-seed difference in held-out loss, fixed before the comparison runs. The *cost* of a repair is $C(m) = c(m) + 1$ FRE: $c(m)$ is the measured cost of building the repaired data (scoring rows, selecting or generating safety rows), and one FRE is the measured cost of one random-removal run (§4.7).

With a smallest effect of interest $\delta = 5$ pp and Holm correction at family-wise level 0.05 over the primary contrasts, each contrast receives one label:
- *better*: the Holm-adjusted test rejects $\Lambda_m = 0$ and the estimate is at least $\delta$;
- *equivalent*: the 90% interval for $\Lambda_m$ lies inside $(-\delta, \delta)$ (two one-sided tests);
- *inconclusive*: otherwise.

A margin of 4 pp is reported as a sensitivity. Three references change no data: a safety prompt at test time, a recipe change, and *adapter scaling*, $\theta_\lambda = \theta_0 + \lambda\,(\theta(a_0, s) - \theta_0)$ for $\lambda \in \{1, 0.75, 0.5, 0\}$, which traces $(F, O, L)$ from the fine-tune ($\lambda = 1$) to the untuned model ($\lambda = 0$). A data repair *dominates* only if it lies below this curve: a lower $F$ than the curve at equal $O$ and $L$.

### 3.3 Localization

Let $a_{-k}$ remove unit $D_k$ and $a_{\mathrm{rand},k}$ remove $|D_k|$ random rows drawn across units. Erosion is *localized* at level $\delta_B$ if some $\Lambda_k = F(a_{\mathrm{rand},k}) - F(a_{-k})$ reaches $\delta_B$ beyond seed noise (the random arm controls for the smaller training dose), and *diffuse* if every $\Lambda_k$ is credibly below $\delta_B$. Diffuse erosion leaves the repair comparison unchanged: unit removals then act like random removal up to $\delta_B$, and a unit-level diagnostic has little to find.

### 3.4 Positive control

A planted data set $\mathcal{D}^{\mathrm{p}}$ replaces the rows of one small cell of $\mathcal{D}$ with $k$ rows that look benign but carry a known eroding signal, keeping the number of rows fixed. Nested partitions split $\mathcal{D}^{\mathrm{p}}$ into $M$ cells, so that the planted cell sits inside one cell at every $M$. The planted erosion is $P = F(a_0^{\mathrm{p}}) - F(a_0)$, and removing the cell that holds the plant at menu size $M$ restores $G^{\mathrm{p}}(M) = F(a_0^{\mathrm{p}}) - F(a^{\mathrm{p}}_{-c(M)})$. A diagnostic $d$ *hits* at $(M, k_d)$ if it ranks that cell among its top $k_d$. Because the truth is known, the sweep measures how diagnosis and trial runs scale with $M$, which natural menus at our budget cannot.

### 3.5 The value of diagnosis (secondary, model-based)

A *menu* $\mathcal{A}_M = \{a_0, a_1, \dots, a_M\}$ holds $a_0$ and $M$ repairs built by a frozen rule, never by a compared diagnostic; $\mathcal{A}_{\mathrm{feas}}$ is its feasible subset and $a^* = \arg\min_{a \in \mathcal{A}_{\mathrm{feas}}} F(a)$. A *selector* $\pi$ with budget $B$ (in FRE) buys trial runs (each a training fraction $\phi$ and a prompt fraction $\psi$, priced from the measured cost model) at total cost at most $B$ and returns $\hat a$. It drops a repair whose adverse estimate of $O$ or $L$ passes its limit ($a_0$ is never dropped), and picks the lowest estimated $F$ among repairs with full runs on at least two seeds; ties go to $a_0$. An infeasible pick is scored as if no repair were made:
$$\mathrm{loss}(\hat a) = F(\hat a)\ \text{if}\ \hat a \in \mathcal{A}_{\mathrm{feas}},\ \text{else}\ F(a_0); \qquad \mathrm{Reg}(\pi; B, M) = \mathbb{E}[\mathrm{loss}(\hat a)] - F(a^*).$$
This is a scoring convention for an expected outcome at a fixed budget, not a safety guarantee. The runs-only selector $\pi_-$ uses one rule per $(M, B)$ cell (a one-shot screen, successive halving or hierarchical bisection), chosen from a simulation before any outcome and then frozen. The selector $\pi_{+d}$ pays the cost $c_d$ of diagnostic $d$, keeps its top $k_d$ repairs, and runs the same rule on $B - c_d$. The value of $d$ and its break-even cost are
$$\Delta_d(B; M, c) = \mathrm{Reg}(\pi_-; B, M) - \mathrm{Reg}(\pi_{+d}; B, M, c), \qquad c^*_d(B, M) = \sup\{c \ge 0 : \Delta_d(B; M, c) \ge 0\}.$$
$F(a^*)$ cancels in $\Delta_d$. When $a_0$ is feasible, regret is non-negative, so no diagnostic can save more than $V_{\max}(B, M) = \mathrm{Reg}(\pi_-; B, M)$. At the menus we can afford, these quantities are mostly outputs of a model, so we treat them as predictions. A generative model (repair effects shrunk by empirical Bayes, noise from pooled residuals, measured costs, two effect shapes) is frozen before Gate B's category runs, and its predicted $V_{\max}$, $\Delta_d$ and $c^*_d$ for the category menu and the planted menus are recorded then. We report measured against predicted values (replayed with the same code path on the outcome tables), and score OLMo-calibrated predictions of the chance of finding the best repair, and of regret, on Llama's category menu.

### 3.6 Opening decomposition (side study)

Let $p(\theta)$ be the share of sampled harm answers that open with a refusal (a frozen lexicon applied to the first 12 words), and $u_{\mathrm{R}}(\theta)$ and $u_{\mathrm{N}}(\theta)$ the unsafe rates among answers that do and do not open with one, so $f = p\,u_{\mathrm{R}} + (1-p)\,u_{\mathrm{N}}$. For the untuned model (subscript 0) and a fine-tune (subscript 1),
$$f_1 - f_0 = \underbrace{(p_0 - p_1)(u_{\mathrm{N}0} - u_{\mathrm{R}0})}_{\text{opening switch}} + \underbrace{(1-p_1)(u_{\mathrm{N}1} - u_{\mathrm{N}0}) + p_1\,(u_{\mathrm{R}1} - u_{\mathrm{R}0})}_{\text{content change}}.$$
The *opening share* is the first term over $f_1 - f_0$; the split depends on the order of terms, so both orders are reported. If the opening share is small, repairs that act only on how answers open (refusal examples; a loss that stops over-weighting the first answer tokens) should restore less than repairs that change what the answers say.

## 4 Experimental Design

### 4.1 Models, data and recipes

**Families and scale.** OLMo-2-0425-1B-Instruct (Team OLMo et al., 2024) is the stage-1 model; Llama-3.2-1B-Instruct (Grattafiori et al., 2024) is the second family (§4.8). Larger sizes follow a ladder: a published-setting replication and a reduced study at 7–8B, then a headline check at 32B or 70B [PLACEHOLDER: sizes actually run]. Qwen2.5-1.5B- and 7B-Instruct (Qwen et al., 2024) are reported for context only (§4.10). Every model trains on one GPU, and every comparison stays on one GPU type.

**Data.** 4,800 rows of Dolly-15k (Conover et al., 2023), 600 from each of 8 task categories (the units; $K = 8$), prepared and sealed per tokenizer with a manifest. 200 further rows, 25 per category, measure task loss.

**Recipes.** *Recipe B* causes the erosion: LoRA (Hu et al., 2022) of rank 64 and scale 128 on all linear layers; AdamW at a constant learning rate of $10^{-4}$ with no warmup; 128 rows per step; one epoch (38 steps); a per-row mean loss over response tokens. *Recipe G* is a standard-practice variant: recipe B with a token-mean loss and a 4-step linear warmup and cosine decay. Recipe G is a reference (§4.4) and a mechanism test (§4.10). Training is deterministic on matched hardware; a seed sets the adapter initialization and the data order.

### 4.2 Measures, judges and the claim rule

- **Unsafe rate U.** The share of 600 sampled answers (200 development harm prompts × 3 samples at temperature 0.7, up to 2,048 new tokens) that Qwen3Guard-Gen-4B (Zhao et al., 2025) labels Unsafe. The prompts come from HarmBench (Mazeika et al., 2024), StrongREJECT (Souly et al., 2024), SimpleSafetyTests (Vidgen et al., 2023) and OR-Bench's toxic set (Cui et al., 2025). Standard errors are clustered by prompt. U is a broad policy label, not an attack-success rate as published elsewhere: judges and prompts differ, so U is compared only within this study.
- **Compliance and the claim rule.** HarmBench's classifier asks whether an answer carries out the requested behaviour. A contrast in U supports a sentence about *harm* only if the classifier's contrast has the same sign and at least half the size; otherwise the sentence says *restored refusal*. If the classifier's erosion on the Gate A answers is below 20 pp, no sentence says harm.
- **Also per arm:** hard-category U (violent, illegal, sexual or self-harm categories); U by answer-length band and a length-reweighted U; Granite Guardian 3.3 (Padhi et al., 2024) on the greedy answers; and a selectivity score (refusal on harm prompts minus refusal on benign prompts).
- **Over-refusal.** Qwen3Guard's refusal flag on greedy answers to 100 benign prompts that resemble harmful ones (50 XSTest safe prompts, Röttger et al., 2024; 50 OR-Bench-Hard prompts, Cui et al., 2025), reported by source, with a lexicon check.
- **Task loss.** Held-out loss on all 200 task rows (the skill limit). ARC-Easy accuracy (Clark et al., 2018) is reported; at 1B it is close to chance and sets no limit.
- **Answers end.** A coherence screen flags answers that reach the token cap, repeat 4-grams heavily, are empty, or have fewer than 5 tokens; an arm whose answers fail too often is not read.
- **Banks.** Gates and selectors read development banks only. Final claims are confirmed on a sealed held-out subsample (§4.8).

### 4.3 Stage 1: the primary comparison

Table 1 lists the stage-1 arms. Every rule, scorer and pool is committed by hash before Gate B's category runs (§4.9).

**Table 1.** Stage-1 arms on OLMo-2-1B (recipe B; one epoch; removal arms train 33 steps, addition arms 38).

| Arm | Repair | Rule | Seeds |
|---|---|---|---|
| $a_{\mathrm{R}}$ | random removal | 600 random rows, 75 per category | 8 |
| $a_0$ | no repair | – | 6 |
| H1 | length rule (free) | remove the 600 rows with the shortest answers | 6 |
| A1 | attribution | remove the top 600 rows by bi-anchored gradient similarity at two checkpoints of $a_0$ (the Gate C method) | 6 |
| L1 | LARF-style filter | remove the top 600 rows by the untuned model's representation similarity to harmful anchors at one layer | 6 |
| S1 | random refusals | add 48 rows (1%) drawn at random from a fixed refusal pool | 6 |
| S3 | DataRx-style | add 48 rows selected from S1's pool by DataRx's score | 6 |
| S4 | self-generated | add 48 pool prompts with the untuned model's own refusals | 6 |

**Primary family.** P1: A1 against $a_{\mathrm{R}}$; P2: L1 against $a_{\mathrm{R}}$; P3: H1 against $a_{\mathrm{R}}$; P4: S1 against $a_0$ (two-sided, since prior work predicts both directions); P5: S3 against S1; P6: S4 against S1. Holm at 5%, labels as in §3.2.

**Pools and anchors.** The refusal pool holds prompts from PKU-SafeRLHF (Ji et al., 2025) that have an unsafe response in the source data, paired with a response that the source labels safe and that opens with a refusal by the frozen lexicon. Pools and anchors are never filtered by the evaluation judge, and prompts that nearly duplicate an evaluation prompt are removed. The add effect must also hold on the evaluation prompts least similar to the added rows.

**Re-implementations.** Every scorer is re-implemented from its paper, named "X-style", and published with a table of its deviations (for example, its anchors and checkpoints); we ask the authors for reference outputs.

**Seeds and power.** Method arms run at six seeds, random removal at eight and no repair at six; seeds run in blocks fixed before any outcome, and only complete blocks are analysed. A blinded rule reads only Gate B's pooled noise estimate: up to 4.5 pp, the plan above; from 4.5 to 6.0 pp, the family shrinks to P1, P3 and P6 at nine seeds; above 6.0 pp, stage 1 does not run. At planning noise the minimum detectable effect after Holm's first step is about 5 pp [PLACEHOLDER: final MDE from Gate B's pooled noise].

**Secondary and scored-only arms** [TO BE FINALISED]. At three seeds each, exploratory, with one-sided bounds only: a random dose curve (1,200 and 2,400 rows removed); random removal plus S1; a DataShield-style filter; rules for answers with list or markup lines and for the longest answers; the length rule under a token-mean loss; and octiles of answer length. Scored without new runs: a Self-Inf-N-style score and a content classifier; we publish the overlap of all top-600 sets. SQSD is cited but not run, because its scoring needs several FRE.

### 4.4 References that change no data

All three are mandatory. **Safety prompt:** a fixed safety instruction as a prefix of the user turn (OLMo-2 has no system turn), at evaluation only, as in PTST (Lyu et al., 2024), on three $a_0$ seeds. **Adapter scaling:** the $a_0$ adapter scaled by $\lambda = 0.75$ and $0.5$ on three seeds, which with $\lambda \in \{0, 1\}$ gives the reference curve of §3.2. **Recipe G:** three seeds. A pinned evaluation script regenerates each $a_0$ adapter by a deterministic re-run and is certified once: with $\lambda = 1$ and no prefix it must reproduce $a_0$'s U exactly. The paper states plainly whether any data repair beats these references.

### 4.5 Positive control: a planted cause

[PLACEHOLDER: runs only if funded; otherwise menu size leaves the headline.] The plant is $k = 37$ rows whose answers comply directly with prompts that also have an unsafe answer in the source data, but which the source labels safe; they look benign. A sealed draw picks one category and one leaf cell inside it, and the plant replaces that cell's rows, so the run keeps 4,800 rows and 38 steps. The nested cells [TO BE FINALISED] are the 8 categories (600 rows), 32 length quartiles within categories (150 rows) and 128 random quarters of those (37–38 rows). A pilot of three seeds goes on only if the plant adds at least 10 pp of erosion with a one-sided 90% lower bound above 5 pp (otherwise the plant doubles once, then the null is reported). The main sweep removes the planted cell at each menu size (three seeds each) and runs random removal on the planted data. Every scorer ranks the cells without new runs. Outputs: $G^{\mathrm{p}}(M)$; each diagnostic's top-$k$ hit rate with known truth; the runs-only cost of finding the cell, replayed with the frozen selector rules; and a check of additivity across the nested levels.

### 4.6 Gates A, B and C

**Gate A (entry).** Over three seeds, mean $E$ must lie in a pre-registered partial-erosion window of 20–55 pp, be at least twice the seed standard deviation, and exceed zero on every seed; a second judge must agree in direction, and the answers must end and the task must be learned. [PLACEHOLDER: Gate A result with every setting tried and its disclosures (§5).]

**Gate B (localization).** Each category removal (600 rows, 33 steps) is compared with random removal of 600 rows (75 per category) at the same seed, so $a_0$ cancels. All 8 categories run at one seed; the two with the largest contrast, plus Gate C's picks, run at two more seeds. The verdict is LOCALIZED if some category restores at least $\delta_B = 8$ pp more than random removal and clears a Bonferroni-corrected bar; DIFFUSE if every category is credibly below 8 pp; and TOO CLOSE otherwise. Guards require answers that end, recompute the verdict on coherent answers and under adverse counting of unscored answers, and reject a restoration that over-refuses. A noise gate stops the stage if seed noise is too large; an automatic extension adds two seeds for contested categories; and a length-matched control separates content from answer length for a localized category. By simulation at planning noise, an 8 pp category reads LOCALIZED about half the time and 80% detection needs about 10–12 pp; DIFFUSE therefore means no category-level cause above about 8 pp, not no cause.

**Gate C (which diagnostic picks the category).** On the first seed's $a_0$, attribution (A1's score) and representation similarity each pick their top category; a format rule picks the category with the largest share of its loss on the first five answer tokens. Gate C is read only if Gate B is LOCALIZED (AGREE, ATTR_BETTER, REP_BETTER, NONE_FINDS or TOO CLOSE). If attribution's pick equals the format pick, the paper says that answer form explains it.

**If DIFFUSE.** Gate C does not run and stage 1 is unchanged. A rewrite arm (the untuned model's own answers replace the 600 top-attribution rows) runs first among the secondary arms, and the planted sweep becomes the only test of whether diagnosis can pay.

### 4.7 Cost accounting

Every arm and every scorer is logged in GPU-seconds by stage (setup, training, greedy generation, sampled generation, judging, scoring, overhead). One FRE per family is the median measured time of that family's random-removal arms. Two cost conventions are frozen before stage 1: *full* (training plus the evaluation as run) and *lean* (training plus one sample per harm prompt, priced from the measured time per answer); the cost $c_0$ of one lean trial run is measured on a real job. Every pool filter, generated answer, anchor job and scorer is charged; "free" means below 0.01 FRE. Attribution is priced from its measured scoring pass. Claims about cost hold only where both conventions agree, and no cost ratio measured at 1B is claimed for a larger model. [TO BE FINALISED: measured costs per arm and per scorer.]

### 4.8 Second family, confirmation and scale

**Llama-3.2-1B** (stage 2) runs after its own Gate A, a reduced Gate B on categories, and the primary family at six seeds. If recipe B saturates Llama, its next recipe changes the learning rate or the LoRA rank, never the loss weighting (a rule recorded before the Llama result). The claim is "replicates across two families" (same sign, and a difference below the interaction's MDE); a family difference is claimed only above that MDE. **Confirmation** (stage 3): at most two contrasts per family, chosen by a rule committed before stage 1, are re-run at six fresh seeds and evaluated on a sealed 200-prompt held-out subsample as well as the development bank. **Scale** (stage 4): first a replication in a published setting (a LARF- or DataShield-style filter on Llama-3.1-8B-Instruct fine-tuned on Alpaca, with random removal and length rules), then the scale ladder [PLACEHOLDER: if resources allow]. No result is claimed at a size without runs at that size.

### 4.9 Pre-registration and testing order

Before Gate B's category runs, we commit every stage-1 scorer's code and settings hash, every edit rule, the pools, the plant, the primary family, the seed rule, the limits, the claim rule, the selector specification and its predictions. Anything added later is labelled post-Gate-B exploratory. Families of tests are read in order, each at its own 5% level: (1) the primary family; (2) confirmation; (3) the Llama replication; (4) the planted-sweep claims; (5) the decision-value predictions. Everything else is descriptive.

### 4.10 Side studies

1. **Mechanism: refusal openings against harmful content.** The opening decomposition (§3.6) on every arm, with a frozen refusal lexicon. Causal tests: recipe G (if erosion runs through openings because the per-row loss over-weights the first tokens of short answers, a token-mean loss with warmup should erode less; compare the first-token account of Qi et al., 2025) and a teacher-forced first-token refusal margin $m(p) = \log P_{\mathrm{ref}}(p) - \log(1 - P_{\mathrm{ref}}(p))$ on Gate B arms, where $P_{\mathrm{ref}}$ is the probability of a frozen refusal phrase as the first answer tokens. If a category's effect runs through openings, the margin should track U across arms. [PLACEHOLDER: report against the bound on a first-token path recorded before Gate B.] Exploratory.
2. **Why erosion saturates in some settings.** The same data can erode a model partly under one recipe or family and almost completely under another (§2; Kim et al., 2025). Our recipe stacks four amplifiers (no warmup, a large adapter, a per-row loss and short human-written answers); we test them where cheap (rank; loss weighting with warmup) and report the contrast family as context, not as a main claim.
3. **Measurement validity.** Three judges on the same answers (Qwen3Guard, Granite Guardian, HarmBench's classifier), with agreement, E per judge, hard-category U and length bands, and an account of how much of the gap to published numbers comes from judges and prompts rather than training.
4. **Over-refusal as the cost of repair.** O against the untuned model for every arm, by source; the judge's own false-Unsafe rate on benign prompts bounds its precision.
5. **Side-effect prediction (secondary).** On the addition arms only: the balanced error of predicting an over-refusal violation, a diagnostic against trial runs of equal cost.

## 5 Results

[PLACEHOLDER: Gate A (entry), with every setting tried and the audit's disclosures; Table 2, the stage-1 comparison (G, Λ with 90% intervals and labels, O, L, cost under both conventions, the HarmBench contrast and the claim-rule wording), with the references and the adapter-scaling curve; Figure 1; the Llama replication; Gate B's verdict with its detection limit and the length control; Gate C and the format reading; the planted sweep, if funded; measured against predicted decision value; the mechanism decomposition and its causal tests; every too-close-to-call result.]

## 6 Discussion and Limitations

**What "unsafe" means.** Our primary judge gives a broad policy label. After fine-tuning it may track whether a model refused more than whether its answer carries out harm. The claim rule (§4.2) therefore decides between "restored refusal" and "reduced harm" for each contrast, and U is not comparable with attack-success rates published under other judges and prompts.

**Equivalence and power.** The labels resolve differences of about 5 pp; smaller differences stay inconclusive, and an *equivalent* label means "within ±5 pp", not "identical". Gate B detects a category effect of about 10–12 pp with 80% probability; DIFFUSE means no category-level cause above about 8 pp, and row-level causes that span categories are not tested by Gate B.

**Recipe and setting.** Recipe B is aggressive: a large adapter, a per-row loss that over-weights the first tokens of short answers, and no warmup. Rankings may change with the recipe; recipe G and the Llama rule (learning rate or rank only) limit, but do not remove, this dependence. The main model and recipe were chosen by screening for partial erosion; §5 lists every setting tried.

**Baselines and doses.** Every scorer is re-implemented, so a weak result may reflect our implementation; the deviation tables, the authors' reference outputs and the published-setting replication address this. Comparisons across removal and addition hold only at the pre-registered doses (600 rows removed, 48 added).

**Cost.** An arm's cost depends on how much we evaluate as well as on training. We report two cost conventions and claim only where they agree. Costs at 1B do not transfer to larger models, because a scorer's cost and a run's cost grow differently with model size.

**Scale and family.** The full comparison runs at 1B on two families; larger sizes get a replication only if resources allow. A family difference is claimed only above its MDE.

**The positive control and the secondary analysis.** The planted cause is artificial; finding it shows that a diagnostic *can* find a concentrated cause, not that natural erosion has one. The value of diagnosis at natural menus is model-based and judged against predictions made in advance.

**Scope and user.** We compare data repairs with model-level references; rewriting responses enters only if the erosion is diffuse. A customer of a closed fine-tuning service can change only the data but cannot run gradient or representation scorers; a developer with open weights can run every scorer but also has model-level repairs. Our answer serves a service that must ship the customer's adapter and may change only the data, and a pipeline that allows only data changes.

## 7 Conclusion

[PLACEHOLDER: which repair to use, at what cost and with what side effects, and whether paying for diagnosis was ever worth it, under the observed outcome.]

## References (author-year keys; full entries in the LaTeX version's references.bib, fetched programmatically)

- Alssum et al. (2025). Unforgotten Safety: Preserving Safety Alignment of Large Language Models with Continual Learning. arXiv:2512.10150.
- Bae et al. (2024). Training Data Attribution via Approximate Unrolled Differentiation. arXiv:2405.12186.
- Bianchi et al. (2024). Safety-Tuned LLaMAs: Lessons From Improving the Safety of Large Language Models that Follow Instructions. ICLR 2024.
- Chen, R. et al. (2025). Persona Vectors: Monitoring and Controlling Character Traits in Language Models. arXiv:2507.21509.
- Chen, X. et al. (2026). Two to Tango: Coupled Task-Reference Selection for Safe LLM Fine-tuning (DualSelect). arXiv:2606.09866.
- Clark et al. (2018). Think you have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge. arXiv:1803.05457.
- Conover et al. (2023). Free Dolly: Introducing the World's First Truly Open Instruction-Tuned LLM. Databricks blog.
- Cui et al. (2025). OR-Bench: An Over-Refusal Benchmark for Large Language Models. ICML 2025.
- Grattafiori et al. (2024). The Llama 3 Herd of Models. arXiv:2407.21783.
- Guan et al. (2025). Benign Samples Matter! Fine-tuning On Outlier Benign Samples Severely Breaks Safety. ICML 2025.
- Guo et al. (2026). When Safety Routing Breaks: Understanding Alignment Fragility under Benign Fine-Tuning. arXiv:2609.01455.
- He, Xia and Henderson (2024). What is in Your Safe Data? Identifying Benign Data that Breaks Safety. COLM 2024.
- Hu, E. J. et al. (2022). LoRA: Low-Rank Adaptation of Large Language Models. ICLR 2022.
- Hu, Z. et al. (2026). GradShield: Alignment Preserving Finetuning. arXiv:2605.14194.
- Ivison et al. (2025). Large-Scale Data Selection for Instruction Tuning. arXiv:2503.01807.
- Jamieson and Talwalkar (2016). Non-stochastic Best Arm Identification and Hyperparameter Optimization. AISTATS 2016.
- Ji et al. (2025). PKU-SafeRLHF: Towards Multi-Level Safety Alignment for LLMs with Human Preference. ACL 2025.
- Jiao et al. (2025). DATE-LM: Benchmarking Data Attribution Evaluation for Large Language Models. NeurIPS 2025 Datasets and Benchmarks.
- Kassem et al. (2025). Reviving Your MNEME: Predicting The Side Effects of LLM Unlearning and Fine-Tuning via Sparse Model Diffing. EMNLP 2025.
- Kim, M. et al. (2025). Rethinking Safety in LLM Fine-tuning: An Optimization Perspective. COLM 2025.
- Kim, S. et al. (2026). Form Over Content In Gradient-Based Data Attribution Methods. arXiv:2609.19589.
- Li, H. et al. (2025). Layer-Aware Representation Filtering: Purifying Finetuning Data to Preserve LLM Safety Alignment (LARF). EMNLP 2025.
- Li, L. et al. (2018). Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization. JMLR 18.
- Li, Y. et al. (2026). Token-level Data Selection for Safe LLM Fine-tuning (TOSS). ICLR 2026.
- Luo, Yuxiang et al. (2026a). TuneAhead: Predicting Fine-tuning Performance Before Full Training Begins. ICML 2026.
- Luo, Yuzhang et al. (2026b). From Reweighting to Rewriting: Unlocking the Intervention Effects of Influential Samples in Training Data Attribution. arXiv:2609.02771.
- Lyu et al. (2024). Keeping LLMs Aligned After Fine-tuning: The Crucial Role of Prompt Templates (PTST). NeurIPS 2024.
- Magnusson et al. (2025). DataDecide: How to Predict Best Pretraining Data with Small Experiments. ICML 2025.
- Mazeika et al. (2024). HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal. ICML 2024.
- Microsoft (2026). Fine-tuning safety evaluation, Azure AI Foundry documentation (updated July 2026). [CITE-CHECK: re-check the page]
- Ouyang et al. (2025). ADMIRE-BayesOpt: Accelerated Data MIxture RE-weighting for Language Models with Bayesian Optimization. TMLR.
- Padhi et al. (2024). Granite Guardian. arXiv:2412.07724.
- Pan et al. (2026). Detecting and Filtering Unsafe Training Data via Data Attribution with Denoised Representation. ICML 2026.
- Qi et al. (2024). Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To! ICLR 2024.
- Qi et al. (2025). Safety Alignment Should be Made More Than Just a Few Tokens Deep. ICLR 2025.
- Qwen et al. (2024). Qwen2.5 Technical Report. arXiv:2412.15115.
- Röttger et al. (2024). XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models. NAACL 2024.
- Seth et al. (2026). SafeTune: A Unified Faithful Library for Auditing and Repairing Safety Drift in Fine-Tuned LLMs. arXiv:2609.22153.
- Souly et al. (2024). A StrongREJECT for Empty Jailbreaks. NeurIPS 2024 Datasets and Benchmarks.
- Springer et al. (2026). The Geometry of Alignment Collapse: When Fine-Tuning Breaks Safety. arXiv:2602.15799.
- Team OLMo et al. (2024). 2 OLMo 2 Furious. arXiv:2501.00656.
- Vidgen et al. (2023). SimpleSafetyTests: a Test Suite for Identifying Critical Safety Risks in Large Language Models. arXiv:2311.08370.
- Wang, M. et al. (2026a). From Data to Behavior: Predicting Unintended Model Behaviors Before Training (Data2Behavior). arXiv:2602.04735.
- Wang, X. et al. (2026b). From Parameter Dynamics to Risk Scoring: Quantifying Sample-Level Safety Degradation in LLM Fine-tuning (SQSD). ICML 2026.
- Xia et al. (2024). LESS: Selecting Influential Data for Targeted Instruction Tuning. ICML 2024.
- Xiao and Aranguri (2026). Probe-Based Data Attribution: Discovering and Mitigating Undesirable Behaviors in LLM Post-Training. arXiv:2602.11079.
- Yin and Rush (2025). Compute-Constrained Data Selection. ICLR 2025.
- Zhang et al. (2026a). DataRx: Missingness-Aware Sampling for Safer Large Language Model Task-Specific Fine-Tuning. arXiv:2608.04322.
- Zhang et al. (2026b). DataShield: Safety-degrading Data Filtering for LLM Benign Instruction Fine-Tuning. arXiv:2606.00160.
- Zhao et al. (2025). Qwen3Guard Technical Report. arXiv:2510.14276.
