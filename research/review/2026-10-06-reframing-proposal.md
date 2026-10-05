# Proposal: reframing the research question after the 6 October reviews

6 October 2026 (IST). Written by General Implementation after the [positioning review](2026-10-06-positioning-review.md) and the [problem-validation review](2026-10-06-problem-validation.md).

**Status: ADOPTED on 6 October 2026** by the user ("adopt this new path … this is our new direction"). [FOCUS.md](../FOCUS.md) now leads with the adopted direction.

**Working title:** *Diagnose or Retrain? Compute-Matched Decisions for Repairing LLM Safety After Benign Fine-Tuning*

A novelty check for this framing and an updated reading list are being done by a subagent (`2026-10-06-reading-list-v2.md`, pending).

## 1. Problems with the current question

The current question, from FOCUS.md: does adding attribution to a selector that already uses metadata, classifier scores and short runs pick better *removals of data groups* than spending attribution's cost on more runs, with *toxic completions* as the failure?

1. **It uses the setting where attribution is least likely to matter, and we built that setting ourselves.** Overt harmful rows causing toxic completions are the classifier's home ground. v2 injects obviously harmful PKU answers, so a reviewer will say the classifier trivially finds them.
2. **A menu of removals only does not match practice.** Real fixes are mostly additions: counter-examples, safety data mixed back in, reframed prompts.
3. **No practitioner asks "is attribution worth its compute?"** Researchers and funders do. Practitioners ask which fix to make and how much checking to do first.
4. **The cost premise is shaky.**
   - The classifier is not cheap: about 1 h, roughly one run.
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

## 3. The kill test before committing (cheap)

In the benign-erosion setting, rank the training rows with the classifier, representation similarity and gradient attribution, and time each.
- If the rankings agree, or none finds the cause, attribution has no information to add: stop or shrink.
- If they disagree, the decision study has something to find.

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
