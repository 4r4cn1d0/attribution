# Additional baseline check — 2 October 2026

Primary source: Pan et al., [Detecting and Filtering Unsafe Training Data via Data Attribution with Denoised Representation](https://arxiv.org/html/2502.11411v2), arXiv v2 dated 10 October 2025. GPT inspected the abstract, method and filtering/retraining sections and tables; no code or results reproduced. An earlier indexed version used the name DABUF; use DRA for this inspected version.

DRA denoises gradient or hidden-state representations to identify unsafe training examples. It uses DATE-LM toxicity data, compares with moderation classifiers including WildGuard, and evaluates retraining after removal. Thus attribution outperforming a content classifier and improving safety after filtering is already an explicit prior-work claim. The inspected evaluation averages repeated inference; that does not establish independent training replication.

Implication for our study: a positive result against Toxic-BERT or plain gradient cosine alone is insufficient. Before the main study, include a strong attribution comparator such as DRA where applicable, or justify its exclusion, alongside strong content classifiers and the short-run selector. The distinguishing hypothesis remains added decision value beyond their combination after full cost accounting. This targeted read does not establish absence of an equivalent experiment.

The local two-arm calibration remains an engineering check. No method implementation or change to its fixed comparisons follows from this source check.
