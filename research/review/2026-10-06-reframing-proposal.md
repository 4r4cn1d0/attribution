# Proposal: reframing the research question after the 6 October reviews

6 October 2026 (IST). Written by General Implementation after the [positioning review](2026-10-06-positioning-review.md) and the [problem-validation review](2026-10-06-problem-validation.md).

**Status: ADOPTED on 6 October 2026** by the user ("adopt this new path … this is our new direction"). [FOCUS.md](../FOCUS.md) now leads with the adopted direction.

**Working title:** *Diagnose or Retrain? Compute-Matched Decisions for Repairing LLM Safety After Benign Fine-Tuning*

A novelty check for this framing and an updated reading list are being done by a subagent (`2026-10-06-reading-list-v2.md`, pending).

## 1. Problems with the current question

The current question, from FOCUS.md: does adding attribution to a selector that already uses metadata, classifier scores and short runs pick better *removals of data groups* than spending attribution's cost on more runs, with *toxic completions* as the failure?

1. **It uses the setting where attribution is least likely to matter, and we built that setting ourselves.** Overt harmful rows causing toxic completions are the classifier's home ground. v2 injects obviously harmful PKU answers, so a reviewer will say the classifier trivially finds them.
2. **A menu of removals only does not match practice.** Public fixes include additions (counter-examples, safety data mixed back in, reframed prompts), while fine-tuning services push customers toward removal. Both belong on the menu (see 2a).
3. **We found no public evidence that practitioners ask "is attribution worth its compute?"** Researchers and funders do. Practitioners ask which fix to make and how much checking to do first.
4. **The cost premise is shaky.**
   - The classifier is not free: 58 min for 9,788 rows with *eager* attention (the cost ledger), about 0.6–0.8 of a round-1 job. It is a one-off per dataset, while trial runs grow with the size of the menu (correction prompted by the FAQ chat; measure again with SDPA).
   - Probe attribution is reported to be about 10× cheaper than an LLM judge.
   - Inline gradient logging is claimed at about 1% overhead.
5. **Small scale favours trial runs.** At 1.5B with LoRA, retraining is cheap, so a result that trial runs win may not transfer to large scale.
6. **The selector is too clever.** Multi-fidelity BO invites the objection "your selector decides the result".

## 2. The proposed question

> **When fine-tuning on benign data makes an aligned model less safe, which data fix restores safety without hurting the task or causing over-refusal, and how much diagnosis is worth paying for before choosing: classifier scores, representation similarity, attribution (gradient similarity or influence functions), or short trial runs?**

Attribution becomes one diagnostic among several. A negative result for attribution still answers a question that practitioners face.

| | Current | Proposed |
|---|---|---|
| Main setting | Base model plus injected overt harmful data | **An aligned model fine-tuned on real benign data that erodes safety.** This is documented (Qi et al.; He et al.; Cisco), the cause cannot be seen by a classifier, and fine-tuning-service customers meet it. |
| v2's role | The headroom test | **The control and anchor:** overt harm, where the classifier should win |
| Fixes | Group removals (replacements conditional) | Keep the data; remove a subset or source; **add safety data**; rewrite or self-distill |
| Outcome | Toxic completions | Broad harm, **with over-refusal and task skill as feasibility limits** |
| Cost | Assumes attribution is expensive | Value per full-run equivalent, as a **function of the diagnostic-to-run cost ratio** |
| Selector | Multi-fidelity BO | Successive halving with a feasibility screen; BO only as a sensitivity check |
| Side effects | Not separate | **Co-primary:** can a diagnostic predict which fix will cause over-refusal? |
| Units | Predefined groups | Data sources or datasets |

**Kept:**
- frozen protocols;
- training-seed repeats;
- held-out confirmation, with sealed contamination in the held-out menus;
- "too close to call" reporting;
- full cost accounting.

### 2a. Corrections after the FAQ chat's review (6 October)

1. **Content classifiers "cannot see the cause" is an expectation, not a finding.** The erosion may be diffuse, with no localized cause; the kill test must test that.
2. **The literature support is thin in the repo.**
   - Qi et al. 2023 is held as a title only; read it in full.
   - He et al. selected benign rows to break safety, which shows benign rows *can* erode safety, not that ordinary fine-tunes do.
   - Cisco's figure comes from a vendor blog snippet.
3. **"Real fixes are mostly additions" is overstated.** Fine-tuning services push customers toward removal ("fix the data and resubmit"). Keep both on the menu.
4. **"No practitioner asks" is absence of public evidence.** Word it as "we found no public evidence that…".
5. **The classifier's cost** is corrected above: about 0.6–0.8 of a round-1 job, eager attention, one-off per dataset.
6. **The kill test's logic.** The classifier will rank benign data almost uniformly, so disagreeing with it means little. The informative comparison is attribution against representation similarity, judged against ground truth from seeded removal runs (see 3a).

### 2b. New risks and design consequences from the reading-list review (6 October; [reading list v2](2026-10-06-reading-list-v2.md))

- **Novelty is narrower but holds as a combination.**
  - New close works: SafeTune ([2609.22153](https://arxiv.org/abs/2609.22153)) compares many repairs on safety, capability, over-refusal and wall-clock cost, with a guide for choosing, but has no data fixes and one seed. **It is the likeliest "this was done" citation.**
  - DataRx ([2608.04322](https://arxiv.org/abs/2608.04322)) compares ways to add safety data, with over-refusal measured.
  - The closest overall is still Xiao and Aranguri.
  - The least covered part is **predicting a fix's over-refusal before training** (only persona vectors come near).
- **Design consequences:**
  1. **Make "add a fixed small safety mix" the default arm that diagnosis must beat.** If it is always good enough, diagnosis is worth nothing, and that must be detectable.
  2. **Cheap non-data repairs may beat every data fix:** a one-example patch, weight-space recovery, or prompt-template choice (PTST). Either limit the claim to users who can only change data, or add one as a reference arm.
  3. **The erosion may be small or driven by the training recipe at 1.5B with LoRA.** Kim et al. ([2508.12531](https://arxiv.org/abs/2508.12531)) found that better hyperparameters alone cut unsafe answers from 16% to about 5%. The headroom check should cover 2–3 benign tasks with at least 3 seeds, and fix the recipe in advance.
  4. **Added data can hide misalignment** ([2604.25891](https://arxiv.org/abs/2604.25891)), so the held-out evaluation needs prompts that resemble the training context.
  5. **Judges misread incoherent outputs** after tasks with a restricted answer format ([2606.03648](https://arxiv.org/abs/2606.03648)); keep the second judge and a coherence check.
  6. **Do not build the benign data with gradient or influence matching,** because that gives the attribution arm a home advantage.
  7. Two different papers are called "DataShield" (2606.00160 and 2607.15081); cite them by ID.

## 3. The kill test before committing

In the benign-erosion setting, rank the training rows with the classifier, representation similarity and gradient attribution, and time each.
- If the rankings agree, or none finds the cause, attribution has no information to add: stop or shrink.
- If they disagree, the decision study has something to find.

### 3a. What the kill-test brief must settle (from the Specialized chat, 6 October; adopted for the brief)

1. **Disagreement alone is not a pass.** Two noisy rankings disagree even when both are useless.
   - **Ground truth:** which source's removal actually restores safety, measured by a few removal runs with seeds.
   - **Pass rule:** attribution's top-ranked source matches the measured effect better than representation similarity's does (the classifier is a reported baseline only, because it ranks benign data almost uniformly; see 2a; corrected 6 October), by a margin fixed in advance and larger than the seed spread of the removal runs.
2. **Fix the unit before measuring costs.** If the units are sources or datasets, attribution needs only per-source aggregate gradients, which is cheaper than ranking rows, while the classifier still scores every row. Fix the unit first, or the cost ratio will mislead.
3. **The engine already has:**
   - aligned instruct models as the trained model (Qwen2.5-1.5B-Instruct was used before);
   - the attribution variants `checkpoint_gradsim` and `adam_diag_preconditioned_dot`;
   - an edit format that supports `add`.

   **New work:**
   - a benign-task data path with sources as units;
   - add-data and self-distill edits;
   - a task-skill evaluation;
   - a representation-similarity diagnostic;
   - cost records for each diagnostic, in full-run equivalents.
4. **The headroom check comes first.** Benign erosion at 1.5B with LoRA may be small, as in round 1. A two-seed a0 check must show that fine-tuning the aligned model on the candidate benign data moves the harm-bank unsafe rate beyond seed noise. If it does not, no ranking can be validated.
5. The Mac second judge stays separate. Nothing in v2 blocks the kill test.

**Cost consequence:** the kill test is no longer nearly free.
- headroom check: 2 seeds;
- ground-truth removal runs: about 3–4 sources × 2–3 seeds;
- diagnostics.

That is roughly 10–14 runs, about **$40–60** at the measured $4 to $4.5 per run (an estimate). It needs new money: after tonight's v2 jobs the balance will be near the $6 reserve.

## 4. Plan for ICML 2027

The deadline is estimated at about 16 January 2027 for the abstract and 22 January for the paper. It is not yet official.

**Timeline, about 15 weeks at 50–60 h a week:**

| Weeks | Work |
|---|---|
| 1 | Finish v2, run the kill test, lock the question, apply for grants |
| 2–4 | Engineering and calibration (about $100–300) |
| 5–8 | Development tables for 2 settings × at least 5 seeds, plus a seed-repeated Pan replication (about $1.5–3k) |
| 9 | Freeze the protocol |
| 10–11 | Confirmation runs (about $1–2k) |
| 12–13 | Analysis |
| 14–15 | Writing and submission |

**Conditions:**
- **Money:** about $3–5k available by early November.
- **Scope:** 2 settings (benign erosion as the main one, overt as the anchor) and 1 model family. Look-alikes, OLMo and 7B are stretch goals.
- **The kill test passes.**

**Risks:**
- Claude usage limits: weekly use reached 91% in about 5 days;
- GPU availability;
- working alone.

**Fallback:** NeurIPS 2027 (about mid-May) for the fuller version. The Pan replication can go to a workshop.

**Estimate:** about an even chance of a solid ICML 2027 submission if funded by early November. Acceptance itself is about 25%.
