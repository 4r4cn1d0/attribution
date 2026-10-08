# Precedent check: influence-guided response rewriting (Luo et al., September 2026)

5 October 2026. Written by General Implementation, from the paper's arXiv HTML version (read 5 October 2026), for the rewriting and headroom amendment. This is a summary of what the paper states, not an independent replication.

**Source.** Yuzhang Luo, Chenpeng Wang, Jianhui Chen and Liangming Pan, "From Reweighting to Rewriting: Unlocking the Intervention Effects of Influential Samples in Training Data Attribution", [arXiv 2609.02771](https://arxiv.org/abs/2609.02771), 2 September 2026.

## What the paper does

- **Models.** OLMo2-1B and 7B, Qwen3.5-2B and Gemma3-4B. The safety experiments use OLMo2-7B only.
- **Behaviours.** Epistemic abstention is the primary behaviour (300 held-out queries; abstention recall). Safety refusal is secondary: 10 benchmarks, including XSTest for over-refusal.
- **Attribution.** EK-FAC influence functions, with per-training-example scores, ranked into top-K and bottom-K.
- **Interventions on the same selected rows:**
  - reweighting (for example, upweighting by 2);
  - deletion;
  - behaviour-aligned rewriting;
  - behaviour-opposed rewriting.

  Rewriting keeps the instruction and replaces the response from a pool of templates.
- **Budget.** 2.5% of the fine-tuning data by default, with ablations in an appendix.
- **Selection baselines.** Random rows of matched size, TRAK, a probe projection, and other gradient methods.
- **Findings, as stated:**
  - reweighting and deletion give weak, inconsistent and sometimes reversed effects;
  - rewriting gives large, persistent shifts in both directions;
  - influence-selected rows give more leverage than random selection;
  - aligned rewriting for safety improves the benchmarks, but it lowers the XSTest **score** from 0.516 to 0.252 (Table 2). That is a score, not a reported over-refusal rate (corrected on 6 October after the FAQ chat's paper check).
- **Not stated:**
  - whether the cost of selection is counted or compared at matched compute;
  - seed or trial counts;
  - which model, if any, wrote the rewrite templates.

## Overlap with this project

| Our component | Overlap |
|---|---|
| Rewriting as a data edit for safety | **Exact.** Not ours to claim. |
| Attribution choosing which rows to edit | **Exact,** against random, TRAK and probe baselines. |
| Deletion is weak | **Exact.** Consistent with dev-matrix-002 ([results](../experiments/2026-10-04-dev-matrix-002-results.md)). |
| Over-refusal as a side effect | **Adjacent:** reported there, not used as a feasibility constraint. |
| Comparison with strong cheap selectors (content-classifier scores, short training runs, edit metadata) | **Not found.** |
| Selection compute charged against the budget, i.e. a matched-compute decision | **Not found.** |
| A finite menu of edits with held-out menus, fresh seeds and a frozen choice rule | **Not found.** |
| Reporting when evidence is too weak to choose | **Not found.** |

## Consequence for our claim

What remains open is the claim already stated in [FOCUS.md](../FOCUS.md): the decision value of attribution beyond strong cheap controls, after its cost is charged. The edit type is no longer the open part. Every write-up must cite this paper for rewriting and for attribution-guided selection. Its 2.5% budget is consistent with our finding that 0.08–0.63% edits were too small.
