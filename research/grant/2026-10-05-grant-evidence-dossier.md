# Grant evidence dossier: decision value of training-data attribution for safety data edits

A living document, started 5 October 2026 at the user's request: "make sure all of this information is stored somewhere it will help us make the grant proposal good". It collects, in one place, what a proposal needs, and every claim links to its record in this repository.

**Rule for using it:** quote only what the linked records show. Estimates are marked as estimates. Development results are not confirmatory.

**Last updated:** 2026-10-09T17:51 UTC, for General Implementation V. This update adds the second family at the main recipe and the blind human read (§3c), judges on RunPod under pre-set parity rules (§4, §5), the $10/h price limit, the 9 October spend and the balance (§7, §8b), and a status line (§10). The update before it was 9 October 12:24 UTC (§8b).

## 1. One-paragraph pitch (draft)

Teams that fine-tune language models must constantly decide how to fix training data that teaches bad behaviour: delete examples, rewrite them, or add new ones. Cheap signals exist for choosing:
- safety classifiers;
- short trial runs;
- metadata.

An expensive one exists too: **training-data attribution**, which traces a behaviour back to the examples that caused it. Prior work evaluates attribution by how well it ranks examples, or by how much an edit moves behaviour ([Luo et al. 2026](../review/2026-10-05-rewriting-precedent.md); DATE-LM; IF-Guide). Nobody has asked the practical question: **once its compute is charged, does attribution lead to better fix *decisions* than strong cheap methods?**

We test this with:
- frozen protocols and a finite menu of candidate edits;
- matched compute budgets and full cost accounting;
- confirmation on held-out data with fresh seeds.

Our preliminary results already show that a simple, common rule ("delete the top 10% of rows the safety classifier flags") can make a model *less* safe. The rule removes far more rows than are actually unsafe, including the examples that teach refusal. Choosing *which* fix to make, and how much, is the gap a better selector could fill.

**Grant version (3 sentences; from the [positioning review](../review/2026-10-06-positioning-review.md), 6 October):** Teams that fix fine-tuning data for safety can use cheap signals, such as safety classifiers and short trial runs, or an expensive one, training-data attribution, but no study measures which signal leads to better fixes for the money. Using replicated training runs and held-out confirmation, we will measure how often each signal picks the safest fix that keeps capability and avoids over-refusal, at matched compute, both where classifiers can see the problem and where they cannot. The result will be an open benchmark and a practical rule for when attribution is worth paying for.

### 1a. Why the problem is real (evidence; from the [problem-validation review](../review/2026-10-06-problem-validation.md), 6 October)

**Verdict: partly real.** Teams do fix training data after unsafe behaviour, and they manage the side effects explicitly. But practitioners do not publicly ask whether attribution is worth its compute; researchers and funders ask that. **Do not claim practitioners ask it.**

Sentences to use, each backed by a primary source:
- Model developers change training data when models misbehave. During Claude Opus 4's development, Anthropic restored an omitted fine-tuning dataset and added a targeted counter-dataset ([system card](https://www-cdn.anthropic.com/4263b940cabb546aa0e3283f35b686f4f3b2ff47.pdf)). Ai2 removed post-training content after tracing a wrong claim to it ([OLMoTrace](https://allenai.org/blog/olmotrace)).
- Fine-tuning services screen customer data with content classifiers and block unsafe models, but they report harm categories rather than rows. Microsoft's message is "Please review your training data set and resubmit the job" ([Foundry docs](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/fine-tuning-safety-evaluation), checked on 6 October). The customer must find what to fix.
- Fixes have side effects that teams manage. Meta ran repeated experiments to balance violations against false refusals in Llama 3's safety data ([arXiv 2407.21783](https://arxiv.org/abs/2407.21783)). Google said tuning made Gemini refuse harmless prompts ([blog](https://blog.google/products/gemini/gemini-image-generation-issue/)).
- Content screening is not enough: benign-looking data can implant harmful behaviour that input-level monitors miss ([Anthropic](https://alignment.anthropic.com/2026/introspection-adapters/)).
- Anthropic chose its pretraining safety filter partly on cost, and lists influence functions as future work ([post](https://alignment.anthropic.com/2025/pretraining-data-filtering/), checked on 6 October). Attribution's cost and reliability at scale remain open problems ([arXiv 2407.14981](https://arxiv.org/abs/2407.14981); [arXiv 2501.12642](https://arxiv.org/abs/2501.12642)).

**What the evidence implies for the design** (recommendations; not yet decided):
- the most real form of the problem is "which data fix, and how much diagnosis to buy first", especially for harmful data that looks benign;
- put additions on the menu;
- count costs in full-run equivalents;
- consider leading with side-effect prediction.

## 2. Research question and novelty

- **Question** ([FOCUS.md](../FOCUS.md)): in a fixed fine-tuning setting, does adding attribution to a selector that already uses metadata, classifier scores and short runs improve its choice among data edits, compared with spending attribution's full cost on more runs? The primary failure measured is unsafe completions.
- **What exists already** (cite, do not claim):
  - rewriting as a safety data edit, and attribution-guided selection of rows to rewrite: Luo et al. 2026, arXiv 2609.02771;
  - attribution for safety filtering: DATE-LM;
  - "about 3% safety data" (Safety-Tuned LLaMAs, Bianchi et al.);
  - harmful fine-tuning breaks safety with few examples (Qi et al. 2023);
  - **the closest prior work:** attribution beats moderation classifiers at *removing* unsafe training data, in nearly our setting (UltraChat with injected ToxicChat). It reports no compute comparison, no rewriting and no training seeds. Pan et al., arXiv 2502.11411, ICML 2026.
  - gradient-based filtering of harmful fine-tuning rows (GradShield, arXiv 2605.14194, 2026);
  - influence functions do poorly at finding harmful data (Li et al., arXiv 2409.19998).
  - The full search and citation list (6 October 2026) is in the [prior-work search](../review/2026-10-06-prior-work-search.md).
- **Our distinct contribution:**
  - a matched-cost decision evaluation against strong cheap selectors;
  - finite menus with held-out confirmation;
  - reporting when evidence is too weak to choose.

  See the overlap table in the [precedent note](../review/2026-10-05-rewriting-precedent.md).
- **The open gap, stated precisely** ([positioning review](../review/2026-10-06-positioning-review.md), 6 October). No paper compares spending compute on attribution with spending the same compute on more pilot runs of the candidate edits, especially with training seeds, side-effect limits and held-out menus.
- **The motivation:** prior results disagree by the kind of data.
  - Attribution beats WildGuard on homogeneous data (Pan et al.).
  - With safety-aligned look-alikes (our ToxicChat-Het), attribution's detection drops sharply while classifiers are unaffected (DATE-LM).
  - A practitioner cannot know in advance which case they are in.
- **ADOPTED direction** (6 October, by the user; [FOCUS.md](../FOCUS.md) updated; see the [reframing proposal](../review/2026-10-06-reframing-proposal.md)). Working title: *Diagnose or Retrain? Compute-Matched Decisions for Repairing LLM Safety After Benign Fine-Tuning*.
  - the main setting becomes benign fine-tuning that erodes an aligned model's safety, where content classifiers are expected to see little (untested; the erosion may be diffuse);
  - the fixes include adding safety data;
  - over-refusal and task skill are limits;
  - value is reported as a function of the diagnostic-to-run cost ratio;
  - v2 becomes the anchor;
  - target: ICML 2027, if funded by early November.
- **Correction (6 October):** DATE-LM's *retraining* results agree with Pan et al. Removing attribution's picks gave safer models than removing WildGuard's, even though classifiers *detect* better. The sharper motivation is therefore "detection quality and decision outcome disagree" (check the DATE-LM PDF before citing).
- **Public output:** the Substack post "First, Make Sure a Fix Can Work" was published on 6 October 2026 at the user's request ([link](https://spiderishi.substack.com/p/first-make-sure-a-fix-can-work)). It describes development results only.
- **Planned framing:**
  - **Claim now** (grant, workshop): attribution as a decision input at matched compute.
  - **Build toward:** "how many training runs attribution is worth", across kinds of data (overt, look-alike, benign-looking degrading).
  - **Pre-register as secondary:** whether attribution predicts an edit's side effects, such as over-refusal.

## 3. Preliminary results (development evidence; two seeds)

| Finding | Evidence |
|---|---|
| **Small group removals do not move safety** in a safety-tuned model. With 12 single-group removals (0.08–0.63% of rows) on Qwen2.5-1.5B-Instruct, every arm stayed within seed noise. | [dev-matrix-002 results](../experiments/2026-10-04-dev-matrix-002-results.md): 78/78 units verified |
| **A base model fine-tuned on ChatGPT-written data is already fairly safe.** a0 gave 12.5 of 72 unsafe answers. The data teach caution. | [round-1 results](../experiments/2026-10-05-headroom-round-1-results.md) |
| **A fixed-size "remove the top-flagged 10%" rule backfired.** Removing the judge's top 1,015 rows raised unsafe answers from 12.5 to 24.0, with both seeds above both baseline seeds. The editable pool held only 43 harmful-answer rows (and 33 refusal rows), so the rule mostly removed rows that were not unsafe, probably including protective refusals. **State this as a finding about fixed-size top-K rules, not about classifiers.** A threshold rule ("remove only rows judged Unsafe") is untested. | Round-1 results; round-1 amendment (pool composition); positioning review |
| **Targeted rewriting was the best edit.** It gave 11.5 against random rewriting's 19.0, a gap of 7.5 with every seed separated; a second judge gives 8.0. | Round-1 results, second-judge note |
| **The measurement is robust to the choice of judge.** Granite Guardian 3.3 agrees with Qwen3Guard on 92.5% of 720 answers (Cohen's κ 0.80) and ranks the arms in the same order. | Round-1 results; `.ai/inputs/headroom-20261005/second-judge-summary.json` |
| **Seed noise is large and mostly a shared shift** (R = 3.3). With 2 seeds × 72 prompts, the minimum detectable difference is about 14 of 72. About 5 seeds are needed for about 9. | Round-1 results, noise analysis; `.ai/inputs/headroom-20261005/noise-analysis.json` |
| **The endpoint was narrow.** Most "unsafe" answers were sexual-content compliance (ToxicChat). v2 adds broad harm banks. | Round-1 results |
| **A contaminated setting gives real headroom (v2 calibration; 1 seed).** Adding 507 unsafe PKU-SafeRLHF responses (5% of the original 10,148 training rows) makes a0 74.5% unsafe on the 200-prompt development harm bank (76.3% over 600 sampled answers). Capability and over-refusal stay healthy: ARC 0.84, 2% over-refusal, and answers end. | [v2 work plan log](../experiments/2026-10-05-headroom-v2-workplan.md), 5 Oct 20:58 UTC |
| **A fix that removes the harm can break helpfulness (v2 positive control; 2 seeds).** Rewriting the classifier's top-507 rows cut unsafe answers from 80% to 11% (sampled answers, the primary measure: −68.9 pp vs no fix; −70.2 pp vs random rewriting; 95% bootstrap intervals exclude 0; greedy gives the same), with ARC unchanged. But refusals of harmless XSTest prompts rose from 1% to 44%, and of OR-Bench-hard prompts from 1% to 66%, failing the pre-specified no-damage rule (written down and approved before the runs). The classifier found 93% of the injected rows, so the hard part was choosing a fix that does not over-correct, not finding rows. A second judge (Granite Guardian) agrees on 97.2% of 1,200 answers (κ 0.94) and gives the same contrasts (−71 pp and −73 pp). | [v2 results](../experiments/2026-10-06-headroom-v2-results.md) |
| **Base models often ship untrained chat tokens.** Qwen2.5-1.5B's `<|im_start|>`/`<|im_end|>` rows are identical to unused rows, as are OLMo's output rows. We fixed this by training the two rows. | [token check](../../.ai/inputs/headroom-engine-20261005/base-token-check.json); work plan |

**Interpretation for reviewers:** edits *can* move safety a lot here, in both directions, and a common fixed-size rule can choose a harmful edit. That is exactly the situation in which decision value can exist. Do not present round 1 as "classifiers fail" (see the row above).

### 3a. Kill-test Stage 0 (interim, 7 October 2026; adopted direction)

From the [interim results record](../experiments/2026-10-07-kill-test-stage0-results.md). Development evidence; the final record follows when seed 1102 and the second judge finish.

- **Benign fine-tuning erodes safety here, a lot, and fast.** Qwen2.5-1.5B-Instruct, untuned: 4.7% of sampled answers to 200 harm prompts are unsafe. After rank-64 LoRA on 4,800 ordinary Dolly-15k rows: about 83% after 1 epoch (seeds 1102 and 1103: +78.3 and +78.8 pp) and 87.3% after 3 epochs (seed 1101: +82.7 pp). Granite Guardian agrees with Qwen3Guard on 98.3% of seed 1101's items (κ 0.965).
- **Side effects:**
  - the untuned model over-refuses (68% of the over-refusal bank); fine-tuning removes most refusals (2–10%);
  - ARC drops 3.7–4.8 points after 1 epoch and 11–13 points after 3;
  - epochs 2–3 add over-training without adding much erosion.
- **Caveats:**
  - the recipe is strong and near-saturating (see the [recipes review](../review/2026-10-07-benign-erosion-recipes.md); Kim et al. report heavy Dolly erosion for Qwen2.5-3B even under a mild recipe);
  - seed 1103 exceeds the frozen "answers end" bars (capped answers above 5%);
  - Gate A is not yet read formally.
- **Cost:** about $4.84 + $4.72, with a third pod still running.
- **For the application:** this result directly supports the premise (benign erosion is real and reproducible at small scale). The planned next step, a gentler literature-matched recipe for Gate B, should be described as part of the staged plan.

### 3b. Update, 7–8 October 2026: the dose levers, Qwen dropped, and why our erosion saturates

Development evidence. Records: the [results record](../experiments/2026-10-07-kill-test-stage0-results.md), FOCUS.md decisions of 7–8 October, and two desk notes ([Guo-gap analysis](../review/2026-10-08-guo-gap-analysis.md); [erosion amplifiers](../review/2026-10-08-erosion-amplifiers-literature.md)).

- **Erosion stays saturated on Qwen under every lever tried** (one seed each, e1, U = sampled unsafe share):
  - recipe B (LR 1e-4, batch 128, 38 steps; r64): 1.5B 79.8% (E +75.2 pp); 7B 87.0% (+82.2 pp);
  - rank 16 (8 Oct): 72.5% (+67.8 pp). A quarter of the adapter cut E by about 7 pp only. Answers end, ARC (−0.026) and the task are fine; only saturation fails.
- **Decision (user, 8 Oct): Llama and OLMo only;** Qwen is dropped as a candidate. The OLMo-2-1B probe launched 7 Oct 23:35 UTC (recipe B, r64).
- **Why we saturate (desk analysis, not yet tested):** published LoRA runs on Qwen2.5-7B with random benign data reach at most about 50%. Our recipe stacks four aggressive choices: no LR warmup, a large adapter, a per-example mean loss (short answers' first tokens carry 3x the usual weight) and human-written Dolly targets. A gentle recipe on the same family and data gives only +14 pp in the literature. Measurement differences explain at most about 13–30 pp of the gap to Guo et al.
- **Engine work done (no spend):** a multi-family engine (OLMo-2, Llama-3; 23 review fixes; corrected mutation testing) and opt-in token-mean loss and LR warmup schedules (four-lens review, no blocker). A gentler, standard-practice "recipe G" is ready for the next probes.
- **Costs, 7–8 Oct:** recipe B about $6 (two pods), 7B check about $5.7, rank-16 test about $3.9. Balance $24.08 before the OLMo probe (expected about $4).
- **For the application:** the saturation finding is itself useful: it shows how recipe choices, not only data, drive benign erosion, which motivates pricing a cheap pre-check against full trial runs.

### 3c. Gate A passed, 8 October 2026 (OLMo-2-1B)

- **Result:** ordinary benign fine-tuning (one epoch of LoRA on 4,800 Dolly rows) of OLMo-2-0425-1B-Instruct raises the unsafe share of answers to 200 harm prompts from 3.2% to 46.7%, 46.8% and 51.3% over three seeds: mean E +45.1 pp, a partial loss with room on both sides. Answers end, the task is learned, and a second judge agrees on every seed. The same recipe saturated Qwen2.5 (+75 to +82 pp).
- **Rigor:** every rule was committed before the data it judges; the three-seed reading was pre-registered; an independent six-lens adversarial audit found no bypass ("sound with caveats"; research/review/2026-10-08-gate-a-audit.md). Caveats are disclosed: the judge's label tracks refusal; five settings were screened; seed variance rests on three seeds.
- **Cost of the whole Gate A night:** about $11 (rank-16 test, OLMo probe, two seeds), all records privately backed up and verified.
- **For the application:** the kill test now has a usable setting, so the next stage (Gate B: is the erosion traceable to data sources?) can start. This is the decisive, fundable experiment.
- **Update, 8 October 15:40 UTC, recipe G (pre-registered, report-only):** the standard-practice training recipe (token-mean loss and a warmup-cosine schedule, everything else equal) cuts the erosion from +43.5 to +29.0 pp on the same data and seed and leaves over-refusal unchanged, while still learning the task. A second judge agrees (Granite +23.0 against +44.0 pp, greedy). So part of the erosion is the objective, not the data, which is exactly the kind of lever the compute-matched comparison prices (recipe G is one of its three free model-level references). Cost about $2.0; records privately backed up and verified.
- **Update, 8 October 17:14 UTC, compliance judge (pre-registered, report-only):** a second, compliance-specific judge (HarmBench's classifier, which asks whether the answer carries out the harmful behaviour) sees two thirds of the Gate A erosion: E_HB +27.8, +30.5 and +32.8 pp over the three seeds (mean +30.4 against Qwen3Guard's +45.1), agreement with the policy judge 83–86% on the fine-tuned units. Every seed clears the 20 pp line fixed in advance, so the paper may describe the erosion as harmful compliance, not only lost refusal. Cost $0 (Mac).
- **Update, 8 October 17:14 UTC, third family (pre-registered probe, report-only):** Llama-3.2-1B-Instruct under the same recipe saturates (unsafe share 13.8% → 76.3%, E +62.5 pp), like Qwen2.5 and unlike OLMo-2-1B (+43.5 pp, partial). The untuned Llama is already unsafe in 64% of the answers it does not open with a refusal (OLMo 18%), so its erosion is almost entirely refusal openings turning into direct answers. Under one recipe the family contrast is now three families: two saturate, one stays partial. The pre-registered rule for Llama (change the learning rate or rank, never the loss weighting) applies; whether both families move to the standard-practice recipe is the user's decision. Cost about $2.2.
- **Update, 9 October 01:44 UTC, the night of 8–9 October (all pre-registered; recipe choice pending the user):**
  - **OLMo-2-1B under recipe G, three seeds:** E +29.0, +31.0, +26.5 pp (mean +28.8, partial); Gate A passes under the adopted ARC rule (a disclosed loosening: a gain or a loss of at most 0.03 in ARC with the task learned). A second judge (Granite) agrees on every seed.
  - **HarmBench, now run on a RunPod A100 after a pre-set Mac-versus-pod parity check (799 of 800 labels identical):** OLMo recipe B +30.3 pp, recipe G +17.2 pp. Under recipe G the erosion falls below the pre-registered 20 pp line for the word "harm"; it is "refusal erosion under Qwen3Guard". Family contrast on one device: Qwen2.5-7B +63.5, Qwen2.5-1.5B +46.0, Llama-3.2-1B +40.5 (recipe G +35.7), OLMo-2-1B +30.3.
  - **The common-recipe ladder (recipe G at LR 1e-4, then 5e-5, LR only):** OLMo is partial at 1e-4 and at the low edge at 5e-5 (+20.8); Llama is at the saturated edge at 1e-4 (+58.25) and partial at 5e-5 (+41.2). Halving the LR cuts both families' erosion by the same fraction (about 28%). No rung fits both families; the user chooses between one recipe for both and a per-family LR.
  - **Mechanism:** the token-mean-only control (bt) erodes like recipe B (+43.7 pp), so recipe G's lower erosion comes from its warmup-cosine schedule, not its loss weighting; rank 16 erodes least (+20.2).
  - **Cost of the night's pods:** about $10 for six probes, four HarmBench pod runs (about $2 for 21,600 judgements at 0.06–0.09 s each) and one failed bootstrap (about $1.8, fixed).
  - **Plan, 9 October 09:40 UTC (the user's decisions):** recipe B is the main recipe for the OLMo study (it keeps the harm outcome: HarmBench +30.3 pp), with recipe G reported as the "change the recipe, keep the data" fix; a second family runs at its own learning rate by a rule fixed in advance; Alpaca is the second benign dataset right after Gate B; PKU-SafeRLHF supplies the safety data for the add repairs. Stage 1 adds Safe LoRA (a post-hoc projection, no training) as a fifth free reference beside the safety prompt, adapter scaling, recipe G and constrained fine-tuning.
- **Update, 9 October 16:59 UTC, the second family at the main recipe (Llama-3.2-1B; development evidence; [FOCUS.md](../FOCUS.md) 9 Oct 13:45, 15:31 and 16:59 UTC):**
  - **Recipe B at LR 1e-4 does not qualify Llama.** Three seeds give E +62.5 (the 8 Oct probe), +61.3 and +54.0 pp. The mean is +59.3 pp: saturated or at the top edge, as under recipe G (+57.1).
  - **The per-family learning-rate rule.** Everything stays equal to the main recipe except the learning rate. The rule takes the highest ladder rung (1e-4, 5e-5, 2e-5) whose erosion probe reads partial (20–55 pp). It uses erosion probes only, never a repair result. Cross-family claims then say "at a matched erosion dose". The rule was fixed on 9 Oct, after the recipe-G ladder and Llama's first recipe-B probe were read; this is disclosed.
  - **Rung 2 (recipe B at LR 5e-5; one seed) reads partial: E +48.0 pp** (U 13.8% → 61.8%; band 41.2–54.8, no edge inside). The prediction, written before the config existed, was +35 to +50 pp (point +43). The result is inside it. ARC shows a clear gain, the task is learned, and greedy E is +44.5. Cost about $2.5.
  - **One open point: answers end reads TOO CLOSE** under the frozen bars. Screen-failing answers are 10.7% against a 10% bar, but 9.0% without the 11 answers shorter than 5 tokens; that is exactly the frozen rule's TOO CLOSE case. The other Llama runs had 0–1 such short answers. The lead recommends rung 2 (LR 5e-5) as Llama's main-recipe rung for planning, with stage 2's own Gate A seeds re-reading answers end per seed. The user decides when stage 2 is planned (paper decision 25). Granite has not yet judged this unit.
  - **Why the families differ (the two-layer account; from [the first-tokens mechanism note](../review/2026-10-08-mechanism-first-tokens.md) and its addenda):** U ≈ P(no refusal opening) × P(unsafe | direct answer). Before tuning, the unsafe share among direct answers is .18 for OLMo, .57 for Qwen and .64 for Llama. Under recipe B the refusal openings fall by .51 (OLMo), .85 (Qwen) and .68 (Llama). A family whose direct answers are already mostly unsafe saturates once fine-tuning removes the openings. OLMo's partial erosion is about half opening switch, half content. This fits "shallow" alignment in the sense of Qi et al. 2024 (an interpretation). A family-by-recipe interaction test (logit scale −0.573, 95% CI [−1.02, −0.13]) is development evidence only: it was written after 11 of the 12 values were known.
  - **For the application:** a second family now has a planned rung in the partial window (one seed; the user's decision on answers end is pending). A rule that never looks at repair results chose it, and a written prediction held.
- **Update, 9 October 15:05 UTC, the blind human read (development evidence; appendix material; [FOCUS.md](../FOCUS.md) 9 Oct 15:05 and 15:23 UTC):** the user rated 50 answers as the single blind reader. The read was pre-registered on 8 Oct and run by the Side Project. The ratings were sealed before the key was opened.
  - **What it shows.** Of 39 answers that Qwen3Guard labels Unsafe, 34 went along with the request (0.87 [0.73, 0.96]), but only 13 gave usable help (0.33 [0.19, 0.50]). The 1B models comply vaguely, generically or wrongly. The reader missed 0 of 10 safe controls. On the 15 OLMo items with HarmBench labels, 4 of the 12 HarmBench "yes" answers were rated usable help. So the human bar is stricter than HarmBench.
  - **Limits.** One reader, small groups, and no comparison between groups.
  - **What it changes in the paper** (the lead's wording, 15:05 UTC; the user's paper wording package, 15:23 UTC). U is "refusal erosion as Qwen3Guard labels it". A "harm" sentence says "harmful compliance as the HarmBench classifier defines it" and carries the caveat that a blind human read rated about a third of judge-Unsafe answers as usable help. The caveat sits once in the measurement section and once in the limitations. The counts go to an appendix as development evidence.
  - **For the application:** the project checks its judges against a human, says what the labels mean, and words its claims to match. The budgeted human check (§8, §8a) can remove the one-reader limit.

## 4. Methodological strengths (what reviewers will value)

- **Frozen protocols before outcomes:** the amendment freezes, dated, with ledger entries in [EDGE_CHECKS.md](../review/EDGE_CHECKS.md).
- **Held-out protections:**
  - groups, prompts and outcomes stay unread until confirmation;
  - new evaluation banks are split by the engine before anyone reads them;
  - near-duplicate leakage is excluded (character 5-gram Jaccard ≥ 0.5).
- **Engine-verified reproducibility:**
  - a two-step A100 fixture must match bit for bit across hosts;
  - every unit is checked by the engine's `verify` (dependency chain and data stream);
  - golden regressions keep old runs byte-identical when the engine changes.
- **Full cost accounting:** every attempt counts, including failures. Budgets have a reserve rule and an automatic budget guard.
- **Durability:**
  - in-pod stop timers with leases;
  - results copied off immediately;
  - private backups verified by download-back;
  - secret scans.
- **Two independent safety judges,** and over-refusal measured with XSTest and OR-Bench in v2.
- **A compliance judge and a human check (8–9 Oct).** HarmBench's classifier asks whether an answer carries out the harmful behaviour. A pre-registered blind human read checks what the judges' labels mean (§3c).
- **Judges on rented GPUs, under rules fixed in advance (8–9 Oct; [FOCUS.md](../FOCUS.md) 8 Oct 23:28 UTC, 9 Oct 16:48 and 17:22 UTC).** A written parity rule compares pod labels with Mac labels on the same answers before any pod label counts. If a check fails, pod numbers are never mixed with Mac numbers in one contrast. The practice is one device per contrast.
  - HarmBench classifier: PASS on 8 Oct at 23:28 UTC. Greedy labels were 200/200 identical and sampled labels 599/600; the tokenizer fingerprints were identical.
  - Granite Guardian: the rule was recorded on 9 Oct at 16:48 UTC, before the first Granite pod. It needed identical tokenizer fingerprints and input hashes, every item judged, at least 196/200 identical labels per unit, and a Yes-count difference of at most 3 per unit. PASS at 17:22 UTC: 200/200, 200/200, 199/200 and 200/200 identical labels on four OLMo units; all 800 input SHA-256 hashes identical; zero token-count differences.
  - Each Granite run also starts with a known-answer gate: at least 190/200 identical labels, and a Yes-count difference of at most 5, on 200 answers with known Mac labels. If the gate fails, the pod stops before it judges anything requested.
  - **Why this matters to funders:** judging no longer depends on one Mac. Others can repeat it on a rented GPU at a measured cost (§7). The rules that decide whether pod labels count were fixed before the pod numbers existed. So judging can grow with the funded runs, and the comparisons stay valid.

## 5. Infrastructure already built (reduces the grant's risk)

- **Engine** (`experiments/safety_selection`):
  - data preparation with token audits and held-out splits;
  - training with resume exactness, attribution scaffolding, edit files (remove, rewrite, add, combined), a row scorer, a rewrite generator and an edit builder;
  - multi-sample evaluation with continuous scores;
  - A100 preflights.
- **Selector framework (Stage B)** with its cost contract: `experiments/safety_decision_policy`.
- **Durability package:** stop timers, leases, gated workers, backups (`experiments/durability`).
- **Run kits:** launch, orchestration, finisher and budget guard (records under `.ai/inputs/`). Since 9 Oct, every kit refuses to create a pod priced above $10/h (§8b).
- **Judge pods** (`scripts/gate_b_mac_judges/pod/`, 8–9 Oct): a RunPod launcher for the HarmBench classifier and Granite Guardian. It uses the Mac tool's own prompt and parse functions and hashes every item's input. A parity rule file (`PARITY.md`) and a per-run known-answer gate decide whether pod labels count (§4). Judge tests: 384 passed, 2 skipped (9 Oct).
- **Tests:** engine 269, Stage B 172, durability 260, all passing at the latest integration.
- **An anonymous artifact** for review ([docs/anonymous-artifact.md](../../docs/anonymous-artifact.md)).

## 6. Data, models and licences

- **Training data:**
  - DATE-LM ToxicChat-Het (10,148 rows);
  - v2 adds PKU-SafeRLHF unsafe responses (CC BY-NC 4.0; 507 or 1,015 rows over 19 harm categories).
- **Evaluation:**
  - HarmBench (MIT), StrongREJECT (MIT), SimpleSafetyTests (CC BY 2.0) and OR-Bench (CC BY 4.0);
  - XSTest (CC BY 4.0);
  - ToxicChat and ARC-Easy.

  Each is pinned by commit and SHA-256: [sources manifest](../../.ai/inputs/headroom-v2/sources-manifest.json); candidates and licences in the [candidates note](../review/2026-10-05-data-and-judge-candidates.md).
- **Models:**
  - policy: Qwen2.5-1.5B base (Apache-2.0);
  - judges: Qwen3Guard-Gen-4B and Granite Guardian 3.3 8B (Apache-2.0);
  - rewrite writer: Qwen2.5-7B-Instruct.
  - policy, adopted direction (from 8 Oct): OLMo-2-0425-1B-Instruct for the main study; Llama-3.2-1B-Instruct as the second family at its own learning rate (§3c). Qwen2.5 units are reported only. Licences for these two: to check before applying.
  - compliance judge (from 8 Oct): HarmBench's classifier. The HarmBench and Granite judges can run on a RunPod A100 under pre-set parity rules (§4).
- **Planned replication:** fully open models (Olmo 3 7B, OLMo-2 1B; Apache-2.0, open pretraining data).
- **Ethics (a commitment to state in applications):**
  - do not publish the generated harmful answers; release scores, code and protocols;
  - use the CC BY-NC components for non-commercial research only, with attribution.

## 7. Measured costs (the basis for any budget)

| Item | Measured |
|---|---|
| dev-matrix-002 (78 units, 13 A100 hosts) | about $60 in total, about $53 of it training jobs ([results](../experiments/2026-10-04-dev-matrix-002-results.md)) |
| Headroom round 1 (10 jobs, the lead's scores and rewrites, restarts) | about $42.3 ([results](../experiments/2026-10-05-headroom-round-1-results.md)) |
| One 1.5B job (large adapter, 3 epochs, e3 evaluation) | 72–102 minutes on one A100 at $1.59/h, so about $2–2.7 |
| Row scoring (9,788 rows, eager attention) | about 1 hour |
| Rewrite generation (1,947 rows, 7B, eager attention) | 1.81 h measured (3.35 s per row attempted, $1.48 per 1,000 rows); 3.19 h including the lost first attempt ([cost ledger](../costs/2026-10-06-cost-ledger.md)) |
| Row scoring (9,788 rows, Qwen3Guard-Gen-4B, eager attention) | 58 min (0.358 s per row, $0.158 per 1,000 rows; cost ledger) |
| One v2 training job (1.5B, rank-64 LoRA, 3 epochs, v2 bank evaluation at e3) | about $3.96 per pod: setup 10.6 min, preflight 20.1, training 67.6, evaluation 47.7 (cost ledger) |
| All GPU spend, 2–5 October | $153.48 over 48 pods; failed attempts $30.61 and idle $8.27 (cost ledger) |
| Local second judge (720 answers, M4 Mac) | about 1.7 hours (file timestamps), free |
| One 1B fine-tune-only probe on RunPod (OLMo-2-1B, recipe G, e1 evaluation, baseline reused) | 55.9 min of job time inside 1.28 h of pod time at $1.59/h: about $2.0 (8 Oct) |
| HarmBench classifier on a RunPod A100 (pod launcher, 8–9 Oct) | 0.06–0.09 s per judgement; 800 judgements about $0.35 per pod run including setup; 5,600–7,200 judgements about $0.6 |
| One 1B fine-tune-only probe, recipe G at LR 5e-5 (OLMo-2-1B or Llama-3.2-1B) | 44–61 min of job time; about $2–2.5 per pod at $1.79/h (9 Oct) |
| Two report-only 1B fine-tune-only seeds, recipe B at LR 1e-4 (Llama-3.2-1B; 9 Oct) | jobs of 58.9 and 47.2 min; about $5.3 for both, including a failed first attempt (about $0.85: a slow pod failed the cap gate at 3.5 h) |
| One 1B fine-tune-only probe, recipe B at LR 5e-5 (Llama-3.2-1B; 9 Oct) | job 15:50–16:58 UTC; about $2.5 |
| Granite Guardian judge on a RunPod A100 (CUDA llama.cpp built on the pod; 9 Oct) | 0.3 s per judgement; the 800-judgement parity pod about $0.35; a first attempt that got no network address cost about $0.60 (stopped after 20 min) |
| Storage of stopped pods (9 Oct) | 21 stopped pods, 400 GB of volume: about $0.11/h, about $2.6 per day; the account's idle spend was $0.126/h at 17:44 UTC |

**Efficiency fixes in v2,** to be measured on the validation pod: SDPA attention, micro-batch 8 × 1, a pre-built environment, light result copies, parallel finishing.

## 8. Budget tiers (estimates; scaled from section 7)

| Tier | Ask | Content |
|---|---|---|
| Lean | about $5–6k | Qwen 1.5B main study (2 settings), OLMo-2 1B replication, a partial 7B check, a human audit sample |
| **Recommended** | **about $14k** | + full Olmo 3 7B replication, a 32B scale check, 2 attribution methods, about 1,000 human-labelled answers, conference travel |
| Ideal | about $22k | 2 settings at 7B, 3 model families, more seeds and annotation |

**Recommended line items:**
- setup $500, headroom checks $400, Qwen main study $1,000, OLMo-2 replication $500;
- Olmo 3 7B replication $2,500, 32B check $800, attribution $600;
- human annotation $800, API judge sample $200, storage $100, contingency 25% (about $1,850);
- AI tools $800–1,200, travel about $3,000.

**Notes:**
- Salary is not included; ask for it separately if the funder allows.
- **Why not giant models:** one setting needs about 150–300 full runs. At 32B–70B each run costs $40–300, and the study would lose its statistical power. A big model is used only for a final scale check.
- **Seeds:** the noise analysis gives the ideal counts: about 5 per key arm for confirmation, and about 3 per candidate edit in development.

### 8a. Decision, 6 October 2026: the BlueDot ask under the adopted direction

- **The user chose the recommended tier: $6,000** for the BlueDot Rapid Grant.
  - The application draft is [2026-10-06-bluedot-application-DRAFT.md](2026-10-06-bluedot-application-DRAFT.md); it is not submitted yet.
  - It covers the whole staged path to an ICML 2027 submission: kill test $145; engineering and calibration $200; development $2,250; confirmation $1,500; 15% contingency $605; a human check of about 500 answers $400; AI tools $800; storage $100. All figures are estimates from measured unit costs.
  - No salary or stipend is included (the user's decision is still open).
- **The tiers in the table above are for the old question.** The new tiers are in the draft, §6: lean $3,050, recommended $6,000, fuller $10,950.
- **Still to fill in before submitting:**
  - ~~the Stage 0 result (running on 6 October)~~ done: the draft's 9 Oct revision (d9e61f8) reports Gate A (§3c);
  - the user-only fields (the draft, §9).

### 8b. Compute request for GPU funds (8 Oct 18:33 UTC; lead's estimate for the user; current plan)

Basis: the sharpened-direction plan's stage costs (§10 there; at $1.59/h), DRAFT revision 4b for Gate B, today's measured 1B pods (about $2 each), and today's decisions (common recipe G; Qwen runs for an arXiv note; a G+Qi arm). Two adjustments: the A100 price rose to $1.79/h (the kit's limit is now $1.85/h), so every estimate is multiplied by 1.16; and 20% is added for failed pods and re-runs (2–5 Oct: $38.88 of $153.48 was failed or idle). Storage about $0.7/day to the end of January.

| Item (estimates) | At $1.59/h |
|---|---|
| Gate B (stage 0; contingency inside) | $50–62 |
| Stage 1 (6 repairs, references, G+Qi arm) | $68–110 |
| Planted-cause sweep (1b) | $17–35 |
| Secondary arms (1c) | $45–80 |
| Llama-3.2-1B: Gate A at G, anchors, Gate B-lite, primary family | $65–115 |
| Confirmation (fresh seeds, held-out subsample) | $58–95 |
| OLMo Gate A seeds at recipe G; Qwen runs for the arXiv note | $11–20 |
| **1B programme** | **$314–517** → × 1.16 + storage $80 + 20% = **about $540–820** |
| 7–8B reduced benchmark (OLMo-2-7B, Llama-3.1-8B; A100) | $200–400 → about $280–560 |
| 32B / 70B headline check (H200, B300; prices UNVERIFIED) | $150–600 → about $180–720 |

**Tiers for a GPU-funds form:**
- **Minimum, about $800** (about 430 A100-80GB hours at $1.85/h): the full 1B study on two families through confirmation.
- **Recommended, about $1,500** (about 800 A100-80GB hours): the minimum plus the reduced 7–8B benchmark, which a main-track reviewer asks for.
- **Full, about $2,200**: the recommended tier plus the 32B (H200) and 70B (B300) headline checks; about $700 of it on those larger GPUs.

Not included: human annotation, API judges, AI tools, travel, salary (see §8a). These are estimates from measured unit costs, not quotes.

**Update, 9 October 12:24 UTC (the user's decisions of 9 Oct):** the tiers stand. Recipe B is now the main recipe (Gate B's DRAFT is already costed on it); the Qwen runs for the arXiv note are binned (−$11–20 at most, inside the rounding); the Llama line now runs at Llama's own learning rate by the approved rule (same cost); Safe LoRA adds about $5–10 to stage 1 (post-hoc, one evaluation per seed); HarmBench and Granite judging move to RunPod at about $0.4–1 per 800–7,000 judgements. Measured from the account: the runs launched from 23:14 UTC on 8 Oct to 01:44 UTC on 9 Oct (the ladder's rung 2 and four HarmBench pods) cost about $10.3, and the two report-only Llama recipe-B seeds about $5.3 (including one failed attempt); balance $57.46 at 12:18 UTC after the user's top-up. **The form can be filed now** with the recommended tier (about $1,500); Gate B itself is funded from the balance plus about $10 before wave 1 (superseded: see the next update).

**Update, 2026-10-09T17:51 UTC (money and limits after 9 October; sources: [FOCUS.md](../FOCUS.md) 9 Oct 15:23, 15:29 and 17:40 UTC; the lead handoff of 9 Oct 17:23 UTC, "Pods, money, keys"; the lead's account reading at 17:44 UTC):**
- **Price limit.** On 9 Oct at 15:29 UTC the user set a pod-creation price limit of $10/h. Every kit refuses to create, or stops at once, a pod priced above $10.00/h or with no finite price. This replaces the old $1.75/h limit and the 8 Oct "no hourly limit". The balance-based budget guard does not change. It plans each new pod at $1.85/h, counts running pods at their real price, and keeps a reserve ($1 in probe and judge kits, $6 in the Gate B kit). So the "$1.85/h" in the basis above is now the guard's planning rate, not a price limit.
- **Spend on 9 October** (pod run time × $1.79/h). The night's runs, from 23:14 UTC on 8 Oct, were the ladder's rung 2, about $8.2 (four pods, including a failed bootstrap of about $1.8), and three HarmBench judge pods, about $1.8. With storage, the balance fell $10.39 ($24.13 → $13.74). After the user's top-up, the two Llama recipe-B seeds cost about $5.3 ($62.78 → $57.46). The Llama rung-2 probe cost about $2.5. The Granite parity check cost about $0.95 ($0.60 for an attempt with no SSH, $0.35 for the pass).
- **Balance.** $54.18 at 17:21 UTC (FOCUS 17:40 UTC; before the last Granite pod's final charge). The lead's account reading: **$54.03 at 2026-10-09T17:44 UTC**; 21 pods stopped, 0 running; idle spend $0.126/h.
- **Storage is now the main idle cost.** The 21 stopped pods hold 400 GB of volume: about $0.11/h, about $2.6 per day. The tiers above assume about $0.7 per day. Deleting pods that hold nothing needed lowers this cost. Each deletion needs the user's yes, and some pods' records must be backed up first.
- **Gate B money.** The wave-1 need is about $72.17 (brief [D21]; to recompute with the kit's final functions). From $54.18, the anchor pod and waves 0a–0b first spend about $6.35–12.53. So the top-up before wave 1 is about $24–31. Add storage, any fiction spend (the user approved the fiction side study up to about $20 on 9 Oct at 15:23 UTC) and any judge pod launched before wave 1. This replaces "the balance plus about $10 before wave 1" above.
- **For the application:** the project caps pod prices at creation, plans every pod through a balance guard, counts every failed attempt and states its storage cost. The tiers are not re-computed here. The storage assumption is the one input that is now low.

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Too little headroom: the model is already safe | The contaminated setting (v2); calibrate the injection size until a0 is at least 40% unsafe |
| The cheap classifier is unbeatable, so attribution looks useless | Menus deliberately include cases where cheap signals mislead (round 1's deletion backfire); a null is reported honestly |
| Seed noise | 5 or more seeds, sampled answers, more prompts; power planned from measured variance |
| A narrow or judge-specific measure | Broad harm banks, two judges, an over-refusal set, a human-labelled sample; since 8–9 Oct also a compliance judge (HarmBench) and a blind human read (one reader so far; §3c) |
| Compute runs out | Budget guard and reserve; free tiers (Modal, Kaggle); local Mac for evaluation; staged gates; since 9 Oct a $10/h price limit at pod creation (§8b) |
| Judging depends on one machine (the Mac) | HarmBench and Granite also run on RunPod A100s; each passed a parity rule fixed before its pod numbers (§4); one device per contrast |
| Leakage between training and test | Exact and near-duplicate exclusion; engine-made splits; held-out data never read |

## 10. Timeline and milestones (draft)

1. **Headroom v2 positive control** (now, within the current balance): calibration, then targeted against random rewrite.
2. **Design and freeze the decision study:** menus, selectors, costs, margins.
3. **Development stage:** true effects of about 20–40 candidate edits × about 3 seeds; attribution and short-run signals.
4. **Held-out confirmation:** fresh seeds and menus on the hidden banks.
5. **Replication** on a fully open model (Olmo 3 7B, or OLMo-2 1B).
6. **Paper:** ICML/ACL main track, or a workshop first. Release the code, data and protocol.

**Status, 2026-10-09T17:51 UTC.** The list above predates the adopted direction. Step 1 is done (v2 results, 6 Oct). Staged gates replace steps 2–3:
- Gate A passed on OLMo-2-1B at recipe B, the main recipe (8 Oct; §3c).
- Llama-3.2-1B is the second family at LR 5e-5 for planning (one seed; the user decides on answers end; §3c).
- HarmBench and Granite judging run on RunPod under pre-set parity rules (§4).
- **Next: Gate B** (is the erosion traceable to data units?). First the pre-registration's revision 5 and the user's freeze; then the anchor job and waves 0a–0b; then a re-costing stop and a top-up before wave 1 (§8b).
- Stage 1 starts only on a funding event. The grant applications need not wait for Gate B.

## 11. Funders and free compute to check (current calls must be verified)

- **AI-safety funders:** Open Philanthropy, Long-Term Future Fund, Manifund. **Superseded on 6 October: see 11c.** The LTFF has closed (replaced by the EA Funds Transformative AI Fund), and Coefficient Giving (formerly Open Philanthropy) passed its career-development funding to BlueDot.
- **Compute:**
  - Modal Academic Grant (up to $10k). **Not running as of 6 October:** "We are not currently running a credit grant program" (FAQ check);
  - NAIRR Pilot (US);
  - Google TPU Research Cloud;
  - cloud research credits;
  - RunPod referral bonuses;
  - free tiers: Modal $30/month, Kaggle about 30 GPU-hours/week, Colab.

### 11a. BlueDot Rapid Grants (was the user's first target)

> **Eligible (corrected 6 October).** The user is based in the US and was only travelling in India. BlueDot's list of countries it cannot pay (which includes India) does not apply. This is the best fast cash option: up to $20k, a 15-minute form, and about 5 working days according to BlueDot's November 2025 blog (FAQ-reported).

What BlueDot's grant pages said when checked on 5 October 2026. **Check the current call before applying.**

- **Who:** "people taking a promising next step in AI safety". Approval is more likely for BlueDot course participants, alumni and facilitators, and for people active in the AI-safety community.
- **How much:** up to **$20,000**.
- **What it pays for:** compute, tools, research time and access, and conference travel.
- **Application:** a short form (about 15 minutes) that asks for the plan and the budget. No formal data is required.
- **Payment and reporting:**
  - payment is a lump sum after a claim through BlueDot's portal (their blog suggests upfront payment is the default; confirm);
  - a short completion report is due within 60 days of the end;
  - material changes need written approval first.

**What to have before applying:**

| Item | Status (5 October 2026) |
|---|---|
| Eligibility angle (BlueDot course or AI-safety community involvement) | **The user to fill in** |
| One-paragraph pitch | Drafted, section 1 |
| Preliminary results | Have them (section 3). v2's "the setting works" result would be the strongest addition. |
| Plan and milestones | Section 10 |
| Itemized budget from measured costs | Tiers in section 8; v2 gives the real cost per job |
| Evidence that we can deliver (engine, tests, frozen protocols, backups) | Section 5 |
| Safety relevance | Section 1: a wrong data fix can make a model less safe, as round 1 showed |
| Risks and honest limits | Section 9 |
| Ethics and licences (do not publish harmful answers; CC BY-NC data for non-commercial research only) | Section 6 |
| Deliverables | Section 12 |

**Recommendation (General Implementation, 5 October 2026):**
1. Apply after v2's result, because a working contaminated setting is the strongest single line to add.
2. Ask for about **$5–10k for the next concrete phase:** the decision study's development stage, plus AI tools. That is a better fit for a rapid grant than the whole study, and a follow-up request is easier once that phase delivers. The $14k tier also fits under the cap.

Sources:
- [BlueDot Rapid Grants](https://bluedot.org/grants/rapid);
- [BlueDot grants](https://bluedot.org/grants);
- [BlueDot blog: Rapid grants for BlueDot projects](https://bluedot.org/blog/rapid-grants-for-bluedot-projects);
- [EA Forum: $50,000 in rapid grants](https://forum.effectivealtruism.org/posts/9AxDSiEsTabyBp3yi/we-ve-given-out-usd50-000-in-rapid-grants-now-we-want-to).

### 11b. Thinking Machines Lab: Tinker credits (checked 6 October 2026 IST)

- **Safety Research Grants** (posted 24 August 2026):
  - **Award:** up to $50,000 in Tinker credits.
  - **Who:** individuals, independent researchers and students can apply.
  - **Topics:** two of them fit this study closely: "Building classifiers for hazardous data at scale" and "Safety-relevant generalization from narrow fine-tuning".
  - **Proposal:** a 1-page summary plus CVs.
  - **Judged on:** relevance, feasibility, construct validity, and simplicity and generality.
  - **Deadline: 25 September. It has passed,** and no later round is announced.
  - **Terms:**
    - credits expire 12 months after provisioning;
    - published work must be CC BY 4.0 or under an approved open-source licence;
    - Thinking Machines gets a non-exclusive licence to the work product;
    - read the publication-approval clause before applying.
- **Tinker Research Grants** (announced 29 October 2025): from $5,000 in credits; rolling review with an answer in about a week. **Check that they are still open.**
- **What Tinker would and would not do for us:**
  - **It would do the training and sampling.** It trains LoRA on hosted open-weight models, with no pods, stop timers or GPU shortages.
    - Price: Qwen3-8B training costs $0.44 per million tokens; sampling costs $0.60.
    - **Estimate:** one of our jobs trains on about 18M tokens, so about $8 per job on an 8B model. Our 1.5B model on RunPod costs about $3.5–4 per job.
  - **It would not run attribution.** The API returns losses and per-token log-probabilities, never per-example parameter gradients. Attribution would run on downloaded adapters on a pod or the Mac, and its compute would be charged separately (the study does this anyway).
  - **Other limits:**
    - Qwen2.5-1.5B is not offered, so moving changes the model and needs a new headroom check;
    - it trains LoRA only: there is no trained chat-token row;
    - it makes no statement on training determinism, so our bit-exact fixture checks would become seed-based checks;
    - the judges must run elsewhere;
    - credits can only be spent on Tinker.
- **Use (corrected 8 Oct 2026; FAQ's check of the Tinker docs, corroborated by GI III):** Tinker can **not** train the study's main models.
  - The user decided on 8 Oct: Llama and OLMo only. Tinker's docs list every Llama model as retired on 12 June 2026 (Llama-3.2-1B and 3.1-8B included), and no OLMo model is offered ([docs](https://tinker-docs.thinkingmachines.ai/llms-full.txt), "Models & Pricing" and "Retired Models", checked 8 Oct).
  - The smallest current models are Qwen3.5-4B and Qwen3-8B. The non-Qwen options are MoE models (GPT-OSS-20B, Nemotron-3-Nano-30B-A3B and larger).
  - At most, credits could fund an optional third-family check (for example GPT-OSS-20B). That would need: a new chat codec (harmony format with a reasoning channel; the judges must read the final answer only); importing Tinker adapters into our engine for attribution on MoE weights (UNVERIFIED that the export maps onto PEFT module names); and seed-based checks instead of our determinism checks. The saving is small: about $1.5–2 of training and sampling per run against about $4 on RunPod, while judging and attribution stay on our GPUs. The engine work is about 1–2 builder days (estimate).
  - Model retirement is a demonstrated risk for a months-long study.

Sources:
- [Safety Research Grants](https://thinkingmachines.ai/news/safety-research-grants/);
- [How to apply](https://thinkingmachines.ai/news/safety-research-grants/apply/);
- [Terms](https://thinkingmachines.ai/legal/safety-research-grants-terms/);
- [Tinker Research and Teaching Grants](https://thinkingmachines.ai/blog/tinker-research-and-teaching-grants);
- [Tinker docs](https://tinker-docs.thinkingmachines.ai/llms-full.txt).

### 11c. Funding update for a US-based independent researcher (6 October; FAQ subagent, from the funders' own pages; corrected for location the same day)

The user is based in the US and was travelling in India in October 2026. An earlier version of this section wrongly assumed an India-based applicant. General Implementation spot-checked two points: BlueDot's list of countries it cannot pay (which includes India) and the EA Funds Transformative AI Fund page. The India restriction does not apply.

**Cash, in rough order of speed:**
1. **BlueDot Rapid Grant:** up to $20k, a 15-minute form, about 5 working days (their blog, FAQ-reported). Compute and tools are allowed. See 11a for the checklist and the eligibility angle.
2. **GTR AI Safety Fund** (gtr-foundation.org): no geographic focus; first feedback within 7 days; a 1–3 page proposal plus CV. Amounts are not stated.
3. **Manifund:** money arrives within days once someone funds you.
4. **EA Funds Transformative AI Fund** ([page](https://funds.effectivealtruism.org/funds/transformative-ai); it replaced the LTFF): always open; typically $10k–150k, but "as low as $1,000"; first decision in about 6–8 weeks (FAQ-reported). Ask whether they can expedite.
5. **Mercor AI Safety Fund:** for US and UK applicants, but it pays the researcher's institution. Check whether an independent researcher can apply through a fiscal sponsor.
6. **Lightcone Commons:** can pay, but slowly. Late applications are answered by about 23 January 2027.

**Credits:**
- **TML Tinker Research Grant:** "starting at $5,000"; rolling; "aim to respond within a week".
  - The form asks for a university and lab affiliation; whether it accepts independent researchers is unverified.
  - Credits cannot be transferred and expire after 1 year. The smallest dense models are Qwen3.5-4B and Qwen3-8B. There are no per-example gradients.
  - **Possible term risks** (if the safety-grant terms apply; unverified): CC BY 4.0 publication, pre-publication approval, and a perpetual licence. CC BY 4.0 clashes with CC BY-NC PKU-SafeRLHF data, and the acceptable-use policy may cover training on unsafe responses.
  - TML's August 2026 call mentions harm arising "accidentally from ordinary downstream fine-tuning", which fits the adopted setting.
- **Lambda Research Grant:** up to $5k of credits (available to a US-based applicant).
- **Anthropic External Researcher Access:** $1k of API credits; reviewed on the first Monday of each month (next: 2 November).
- **Google TPU Research Cloud:** free TPUs, but the code would need porting.
- The AWS, Google Cloud research and NVIDIA academic programs need an academic affiliation.

**Closed or not open:**
- the LTFF (replaced by the TAI Fund);
- Coefficient Giving's Technical AI Safety RFP (closed 15 April 2025; its career-development funding went to BlueDot on 4 September 2026);
- Modal credits (not running);
- the UK AISI programmes, the CAIS compute cluster and the FMF AI Safety Fund;
- Schmidt Sciences (no unsolicited proposals);
- SFF (individuals need a fiscal sponsor).

**AIAF = AI Alignment Foundation:** rolling, and mostly in kind (an engineering team plus compute). No amounts are stated; low fit.

**Overlapping funding:** no program publishes a rule against it. Disclose every other application, and keep separate budget lines: Tinker credits for training and sampling; cash for attribution GPUs, judges and subscriptions.

**Tax:** as a US person, the user fills in a W-9 (for example for TML), and grants are likely taxable income. Check with a tax adviser.

**Suggested order this week:**
1. BlueDot Rapid Grant (fast cash; use the dossier's pitch and the staged kill-test budget).
2. ~~The Tinker form~~ **Demoted on 8 Oct to optional, after the cash funders below** (Tinker offers no Llama or OLMo model; see 11b). If filed, frame it as an optional third-family check.
3. A GTR proposal.
4. A Manifund page.
5. EA Funds (ask about expediting).
6. The Anthropic credits form before 2 November.
7. Lambda.
8. Mercor, if a fiscal sponsor works.
9. AIAF, optional.

**Outlook:** if BlueDot approves within about a week, funding by early November is plausible, and **ICML 2027 is realistic again**. NeurIPS 2027 stays the fallback.

**Unverified:**
- whether Tinker research grants have their own terms or accept independents;
- AIAF's amounts;
- GTR's amounts;
- whether Mercor accepts independents through a fiscal sponsor.

FAQ holds the full list of about 50 sources.

## 12. Deliverables to promise

- the paper, including any null;
- open code, the frozen protocols and the evaluation protocol as a reusable benchmark;
- data release within licence terms (CC BY-NC components with attribution);
- cost accounting that others can reuse.

## Sources inside this repository

- research question: `research/FOCUS.md`;
- precedent: `research/review/2026-10-05-rewriting-precedent.md`;
- results: `research/experiments/2026-10-04-dev-matrix-002-results.md`, `research/experiments/2026-10-05-headroom-round-1-results.md`;
- next design: `research/experiments/2026-10-05-headroom-v2-amendment-draft.md`, `research/experiments/2026-10-05-headroom-v2-workplan.md`;
- data and judges: `research/review/2026-10-05-data-and-judge-candidates.md`;
- ledger: `research/review/EDGE_CHECKS.md`;
- second family, blind read, judge pods and money (9 Oct): `research/FOCUS.md` (9 Oct entries), `.ai/handoffs/2026-10-06-general-implementation.md` (the lead handoff of 9 Oct), `scripts/gate_b_mac_judges/pod/PARITY.md`, `research/review/2026-10-08-mechanism-first-tokens.md`; the blind read's record is on the Side Project branch (`research/side-blind-read/PREREG-2026-10-08.md`, commits 4d63e04 and 57d08dd);
- backups: `backups/2026-10-04/`, `backups/2026-10-05/`, `backups/2026-10-08/`, `backups/2026-10-09/`.
