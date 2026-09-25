# Supplementary literature audit

Access date 2026-09-24. Primary-source reconnaissance to supplement the proposal's attribution references. These are review notes, not new experimental findings.

## Direct generic-method collisions

- PPI++ (Angelopoulos, Duchi, Zrnic): https://arxiv.org/abs/2311.01453 ; full text https://arxiv.org/html/2311.01453v2 . Prediction plus labeled residual correction and data-driven power tuning already provide mean estimates and intervals. The proposal's E[C]+E[Y-C] construction falls within this family when correctly instantiated.
- Active Statistical Inference (Zrnic, Candes): https://arxiv.org/abs/2403.03208 ; full text https://arxiv.org/html/2403.03208v1 . Selects expensive labels using model uncertainty, corrects sampling, and constructs confidence intervals; includes both batch and sequential acquisition. Sequential acquisition must not be confused with every interval being finite-sample anytime-valid: the inspected version's experiments use asymptotic intervals.
- Prediction-Powered E-Values (Csillag et al.): https://arxiv.org/abs/2502.04294 . Prediction-assisted testing and sequential/post-hoc validity are already studied.
- Anytime-valid, Bayes-assisted, Prediction-Powered Inference: https://proceedings.neurips.cc/paper_files/paper/2025/file/01830c92c6558179fa6d7fb1edff692c-Paper-Conference.pdf . Conference abstract describes asymptotically time-uniform prediction-powered confidence sequences. Do not equate that automatically with a finite-sample guarantee at three seeds.
- Robust Sampling for Active Statistical Inference: https://papers.nips.cc/paper_files/paper/2025/file/6389470564214983604d1ac81631c2c5-Paper-Conference.pdf . Uncertainty-directed acquisition can lose to uniform when scores are poor; robust interpolation is a relevant baseline.
- Revisiting Active Sequential Prediction-Powered Mean Estimation: https://arxiv.org/abs/2604.18569 ; ICLR 2026 original conference PDF https://openreview.net/pdf/74eb3d71f48f818531ae5be069bc5b5a60a2caad.pdf . Non-asymptotic analysis and experiments question whether uncertainty-guided acquisition beats near-uniform acquisition.
- Prediction-Powered Inference Across Many Tasks for AI Evaluation & Social Science Research: https://arxiv.org/abs/2605.29249 ; full text https://arxiv.org/html/2605.29249v1 . Cross-task recalibration preserves within-task correction and studies task-specific efficiency. Merely sharing calibrators across deletion requests is not an automatically novel extension.
- Prediction-Powered Active Testing: https://arxiv.org/abs/2607.08347 ; full text https://arxiv.org/html/2607.08347v1 . A July 2026 preprint combines active testing, control variates, and importance-weighted correction in a different target setting; inspect assumptions before claiming it solves group-specific deletion decisions.

## Allocation comparators

- Thresholding Bandit Problem: https://proceedings.mlr.press/v48/locatelli16.html . Classifying arm means relative to a threshold under a budget is established. Map requests to arms carefully: one retraining returns many query scores, and source models may be shared.
- Optimal Multi-Fidelity Best-Arm Identification: https://arxiv.org/abs/2406.03033 . Cost-aware use of approximate and exact measurements has existing instance-dependent lower bounds and allocation algorithms. Best-arm identification is adjacent, not identical, to the proposed three-way audit.

## Review consequence

The new value cannot be inferred from combining residual correction, selective sampling, intervals, and abstention. A contribution could still exist through a deletion-specific observation/cost structure, a substantial verified empirical discovery, or a removal of important assumptions. The audit should test those possibilities rather than assert that all combinations are unpublishable.

Searches included exact paper titles plus `prediction-powered inference active`, `prediction-powered sequential`, `multifidelity thresholding bandit`, `data attribution prediction-powered`, and `prediction-powered inference across many tasks`. This was targeted retrieval, not an exhaustive systematic review. Some related papers were read only at abstract level as indicated by their discussion; no results were reproduced.
