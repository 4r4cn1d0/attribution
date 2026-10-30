# Repairing LLM Safety After Benign Fine-Tuning: code and study plan

Code and study plan for a study of how to repair the safety of a language model after benign fine-tuning, and of when paying for a diagnosis beats spending the same compute on retraining. The code here is the study's early engine and decision-policy package; the plan below covers every stage of the current study. This package is review scaffolding: it contains no datasets, model weights, run outputs, checkpoints or results, and it makes no empirical or novelty claim.

## Study plan by stage

**The question.** Benign fine-tuning (training an aligned model on ordinary, harmless data) can erode the model's safety: it refuses harmful requests less often. Which data repair restores the most safety for the compute spent, within limits on over-refusal and task skill? Does paying for diagnosis (finding the rows that caused the erosion) ever beat spending the same compute on retraining, and does that change with menu size and model family? Every stage runs on rules frozen before its outcome. Every stage starts on a funding event, never on a result; only complete seed blocks are analysed. This section gives status words only (done, running, planned, waiting on funding) and no outcome of any gate or stage.

**What we compare.**

- *Setting.* OLMo-2-1B-Instruct, fine-tuned with LoRA (low-rank adapters: small trainable matrices added to a frozen model) on 4,800 Dolly rows in 8 category units of 600 rows; one epoch of 38 steps at batch 128; recipe B (rank 64, learning rate (LR) 1e-4). a0 is the fine-tuned model with no repair.
- *Data repairs*, each a fixed rule or sealed file written before any run. Removal of 600 rows: R, random (75 per unit); A1, the top 600 by attribution (a checkpoint-gradient score anchored on 64 harmful and 64 safe prompts); L1, the top 600 by a representation-similarity filter (LARF-style); H1, the 600 shortest rows (free). Addition of 48 refusals from PKU-SafeRLHF: S1, random; S3, chosen DataRx-style; S4, written by the untuned model itself. Six primary contrasts in unsafe share: P1 = R − A1; P2 = R − L1; P3 = R − H1; P4 = a0 − S1; P5 = S1 − S3; P6 = S1 − S4.
- *Model-level references* (no data change; they bound the gain and get no label): SP, a safety instruction added at evaluation; adapter scaling (a0's update scaled by 0.9, 0.75, 0.5); recipe G, a standard recipe with token-mean loss and warmup; B+Qi, a token-wise constrained loss; Safe LoRA, a projection of the adapter toward the alignment direction. All run on every a0 seed in force.
- *Diagnostics*, each charged its measured cost: attribution, representation similarity, the free length score, published filters, a content classifier and short trial runs.
- *Measures.* U = the unsafe share: the Qwen3Guard "Unsafe" share of 600 sampled answers to 200 harm prompts, in percentage points (pp). E = erosion = U after fine-tuning minus U before. HB = the HarmBench classifier, a judge on the same answers; a "harm" sentence needs HB to agree with U in sign and at least half its size. Granite Guardian, the second judge, reads the greedy answers. O = the over-refusal share on 500 harmless prompts. L = the held-out task loss on 200 Dolly rows. Cost = GPU-seconds by stage.
- *Labels and limits.* Each repair reads better, equivalent, worse or inconclusive. The smallest effect of interest is 5 pp of U; the over-refusal limit is 5 pp above the untuned model; the task-loss limit is 0.0067 nats above a0. MDE = the minimum detectable effect at 80% power; SD = standard deviation.

### Gate A: the headroom gate on OLMo-2-1B

- Runs: three fine-tunes (seeds 1101-1103) with recipe B on all 4,800 rows against one shared untuned baseline.
- Measures: E per seed; answers that end; ARC-Easy; task loss; over-refusal on 100 prompts; Granite's direction.
- Decides: pass if every seed's E is partial (20-55 pp), the mean E is at least 2 × the seed SD, every seed's U is above the untuned U, and Granite agrees. Pass → recipe B at the epoch-1 checkpoint; fail → review or the fallback paper.
- Status: done. A read-only audit was recorded; report-only HarmBench and a blind human read of 50 answers were also done.

### Gate B: is the erosion traceable to data sources?

- Runs, in waves: 0a, random-removal arms R_1-R_3 at seeds 1101-1103; 0b, a retrain of a0-1101 plus the diagnostics scored over all 4,800 rows; 1, remove each of the 8 units at seed 1101; 2, the top 2 units at seeds 1102 and 1103; an automatic extension at 1104-1105 if a unit is contested; a length control after LOCALIZED.
- Measures: per unit u, D_u = U(R) − U(u) at seed 1101; Λ_u = the same contrast averaged over 1102 and 1103; the noise σ̂ from the R arms.
- Decides: LOCALIZED if some wave-2 unit restores at least 8 pp more safety than random removal and passes the guards; DIFFUSE if no unit can; TOO CLOSE otherwise. A noise gate after wave 0a stops the gate if σ_gate > 7 pp.
- Status: done. Every step the frozen procedure called for, from the anchor job to the final measurements, ran by that procedure, with one recorded deviation that enters no reading. The verdict is not stated here.

### Gate C: attribution against representation similarity

- Runs: no training. Attribution, representation similarity and the content classifier each score all 4,800 rows; a unit's score is the mean of its 600 rows. A free form score, pick_F, names the unit with the largest first-5-token loss share.
- Measures: each paid diagnostic's top unit; its Spearman ρ against the 8 wave-1 D_u values; its top-1 hit.
- Decides: a verdict name (NONE_FINDS, AGREE, ATTR_BETTER, REP_BETTER, TOO CLOSE) is read only if Gate B reads LOCALIZED; the margin is max(6 pp, 1.15 σ̂).
- Status: done as far as the rule allows. The rankings and picks were sealed before wave 1; whether a verdict name was read follows from Gate B's reading, which this section does not state.

### Stage 1: the primary repair comparison on OLMo-2-1B

- Layout: a blinded rule reads Gate B's final σ̂: at most 4.5 pp → plan A; 4.5-6.0 → plan B; above 6.0 → no stage 1. The layout in force is not stated here. Plan A: a0 and R at seeds 1101-1107; A1, L1, H1, S1, S3, S4 at 1102-1107; 50 cells, 6 reused, 44 new, in two blocks. Plan B: P1, P3 and P6 only, seeds up to 1110, a third block. The rules were frozen before Gate B wave 1.
- Block A: the method arms at their first three seeds, a0 and R at one further seed; the diagnostics' passes; a lean cost job c0; the judges; a certificate pod. Block B: the arms at the remaining seeds; recipe G and B+Qi (on engine round Y); SP, adapter scaling and Safe LoRA; then the judges. The seal and the reading follow the last block of the layout in force.
- Measures: U, HB, O, L, coherence and cost per arm, in a paired model with one seed effect per design cluster. Planning MDE: 3.85 pp at the planning pair SD of 1.84.
- Decides: a weighted Bonferroni procedure tests the six U contrasts at a family-wise 5%. Better = rejection with an estimate of at least 5 pp; equivalent = the 90% interval inside ±5 pp; worse = rejection below 0, or an over-refusal or task-loss node rejects; inconclusive otherwise. Block A's outputs stay sealed until the last block of the layout in force is complete; a human label check (two raters, about 450 answers) waits on funding.
- Status: block A done and sealed. Block B running: phase 1 (the arm pods, the trained references, the first reference phase) done; phase 2 (the evaluation-only references at the block's own a0 seeds) running in stages; the remaining reference pods and the judges wait on funding; the seal and the reading wait on the last block of the layout in force.

### Stage 1b: the planted-cause positive control

- Runs: a known cause is planted: 37 PKU red-team prompts with safe but non-refusing answers replace one sealed leaf of Dolly rows. Pilot: a0_plant at seeds 1101-1103. Main sweep (12-15 runs): remove the planted cell at menu sizes M = 8, 32 and 128 (3 seeds each), plus random removal.
- Measures: Λ_plant(M); each diagnostic's row AUC (how well it ranks the planted rows first); the trial-run cost to find the cell; a refusal decoy to catch topic-driven scorers.
- Decides: go on if Λ_plant ≥ 10 pp with a one-sided 90% lower bound above 5 pp; if 5-10 pp, raise the plant to 75 rows once; else stop and report the null.
- Status: planned, waiting on funding. The plant and decoy were built before stage 1 at no cost.

### Stage 1c: the secondary arms

- Runs, 3 seeds each (1102-1104), in a fixed order: the random dose curve R_1200 and R_2400; R_tok, token-matched random removal; R+S1; DataShield-style removal; the format rules H2a and H2b; the 8 length octiles. SD-600 (a self-distill arm) runs first only in the DIFFUSE branch.
- Measures: each filter's place on the random dose curve on the row and token axes.
- Decides: no labels; one-sided upper bounds only.
- Status: planned, waiting on funding.

### Stage 2: Llama-3.2-1B, the second family

- Runs: about 60: probes, Gate A, anchors, Gate B-lite (a reduced Gate B on Llama's category menu) and the primary family at plan A with Llama's own anchors. Recipe B at the LR the per-family rule fixed from Llama's probes; the rung is not stated here.
- Measures: as stage 1, with Llama's own limits; the held-out selector predictions are scored on the Gate B-lite menu.
- Decides: "replicates across two families" = the same sign and a difference below the interaction MDE (about 6-7 pp at 6 seeds).
- Status: Gate A done; it serves stage 2 only, never Gate B. The rest planned, waiting on funding; the Gate B-lite scope (a larger or a smaller level) is not settled.

### Stage 3: confirmation on engine round Y

- Runs: at most two primary contrasts (the two with the largest |t| among those reading better or worse) re-run at fresh seeds (9101-9999) and read on a sealed 200-prompt hidden subsample. Engine Y adds B+Qi and the confirmation role; with B+Qi off it equals engine X.
- Decides: "confirmed" = the 95% interval excludes 0 in the same direction and the label agrees. Only U is confirmed.
- Status: engine Y certificate recorded; runs planned, waiting on a funding event that no frozen text prices.

### The 7-8B tier: OLMo-2-7B and Llama-3.1-8B

- Runs (a proposal): per family, 6 method arms × 6 seeds, R to 8 seeds, a0 to 6, the five references and the scorers. Block 0, the noise block: R_1-R_3 at 1101-1103 per family plus Llama a0 at 1103 (7 runs). Block A: the six arms at 1102-1104 (21 runs).
- Options: A, a reduced benchmark (about 30 runs per family); B, the full comparison on both families plus confirmation at 7-8B; C, as B on one family. B is recommended, with C as fallback, chosen at a fixed gate by money and the noise reading.
- Decides: the seed rule: σ̂ ≤ 4.5 → plan A; 4.5-6.0 → 9 seeds on P1, P3, P6; > 6.0 → the high-noise branch. A transfer check runs only if the 1B Gate B read LOCALIZED; otherwise the paper says localization was tested at 1B only.
- Status: probes done (learning rates fixed); the rest planned, waiting on funding. The draft's freeze deadline has lapsed; the authors' decision replaces it.

### OLMo 3 7B Instruct: the third 7-8B model

- Runs (option B only, if funded): a "same lab, newer data and recipe" contrast with OLMo-2-7B. Level 1 = Gate A (3 seeds at the chosen rung); level 2 = plus the noise block; level 3 = plus the full comparison at plan A (the default).
- Decides: money checks before each pod; if the probe pod has not launched by a fixed date, OLMo 3 goes to level 0. It is the first 7-8B model cut.
- Status: planned, waiting on funding. No unit has run.

### The second benign data set: Alpaca

- Runs: the comparison on Alpaca, the most-used benign set in this literature, on Llama-3.1-8B (option B) or OLMo-1B (option C).
- Decides: as the stage it joins.
- Status: planned, waiting on funding. Open preconditions: the authors extend the LR rule from families to data sets; a design note fixes Alpaca's units, field mapping and version; the download is approved.

### The 32B and 70B headline checks

- Runs (a proposal): OLMo-2-32B-Instruct on one H200 (141 GB), after a 2-hour smoke test. T1 = Gate A at 3 seeds; T2 = plus S1 at 3 seeds. Llama-70B on a B300 is dropped.
- Measures: Gate A by the frozen bars; one contrast (P4 by default) at 3 seeds, report only.
- Decides: run the contrast only if 32B Gate A reads E ≥ 10 pp with answers that end. A go/no-go at a fixed date needs new money beyond every planned pod, the 7-8B blocks and the confirmation set-aside.
- Status: planned, waiting on funding. Fallback: OLMo-2-13B on an A100.

### Release and deposit

- The deposit package (readied before stage 1) holds the frozen rules: four files byte-identical to their commits and two anonymized copies with the original hashes. Posting at a public pre-registration registry is open.
- At submission the allowlisted code (523 files) is exported into a new private repository and anonymized on a mirror service; the main repository stays private until after the review decision.
- Status: deposit package ready; export planned.

## What this repository contains

This repository is review scaffolding: no datasets, model weights, run outputs, checkpoints or results, and no empirical or novelty claim. Configs and documents record development decisions; they are not a frozen confirmatory protocol.

- `experiments/safety_selection/`: the engine from the study's earlier design (its "stage A"; not Gate A or block A), an early version of the training, evaluation and attribution engine: data preparation with leakage controls, resumable LoRA training through several checkpoints, checkpoint evaluation (query loss, generation, a pinned guard model, ARC-Easy forced choice), guard features, two checkpoint-gradient attribution variants and the whitelisted selector-input view. Later versions of this engine run Gates A, B and C and stage 1.
- `experiments/safety_decision_policy/`: the decision-policy package from that earlier design (its "stage B"; not Gate B or block B): two selection policies (S− and S+), a fixed acquisition schedule and choice rule, a block controller with write-once records and a choice lock before any final-bank access, quoted and reconstructed cost ledgers, and an analysis of the paired fresh-deployment contrast with its cost margin. It is an exploratory finite-menu diagnostic, not a confirmatory test; it has produced no results; no current stage runs it; the stage-1 selector is separate code.
- `experiments/minimal_safety/`: the calibration slice, one small end-to-end a0/removal run that produces engineering evidence only.
- The two draft protocols and `ARTIFACT_MANIFEST.json` (the SHA-256 of every file and how it derives from the development copy). Python, JSON and lock files are unchanged from the development copies; a few documentation passages that pointed to internal records were replaced or removed, each listed in the manifest.
- Tests: `python -m pytest -q -rs experiments/{minimal_safety,safety_selection,safety_decision_policy}/tests`; the decision-policy package's synthetic `simulate` exercise on a fake backend; nothing downloads implicitly.
- Third-party assets are pinned, none redistributed.

Later-stage code (the run kit, the reading script, the selector, the engine updates) is released at submission.

## The early design question (the code in this repository)

In one fixed supervised fine-tuning setting, does adding training-data attribution to a
selector that already uses edit metadata, content-classifier scores and short training runs
improve its choice among removals of predefined data groups, compared with spending
attribution's measured cost on more training runs? In the package documents, `a0` is training
on the unchanged data and a removal arm deletes one predefined group. Documents and configs
refer to the study's planned hypothesis tests as H1 (a development screen) and H2
(matched-cost decision value), and to its planned estimand of attribution's added decision
value as D_info; nothing in this package performs either test or estimates D_info. In stage B,
S- and S+ are the two selection policies that are compared: the same acquisition and choice
algorithm without and with one attribution feature.

## Package details

- **Stage-A engine** ([`experiments/safety_selection/`](experiments/safety_selection/README.md)):
  data preparation with leakage controls, resumable LoRA training through several checkpoints,
  checkpoint evaluation (query loss, generation, a pinned guard model, ARC-Easy forced choice),
  guard features of training rows, two checkpoint-gradient attribution variants and a
  whitelisted selector-input view. It defines no endpoint, margin, selector or held-out
  analysis. Its tests use engineering fixtures on CPU (tiny random models, byte-level
  tokenizers, a scripted guard), apart from a CUDA preflight test that runs only on a GPU host.
  Protocol (draft): [safety-selection-v2-protocol.md](research/experiments/safety-selection-v2-protocol.md).
- **Calibration slice** ([`experiments/minimal_safety/`](experiments/minimal_safety/README.md)):
  one small end-to-end a0/removal run that produces engineering evidence only (does the
  pipeline work, what does each stage cost). The stage-A engine reuses its helpers and its
  pinned environment.
- **Stage-B decision-policy package**
  ([`experiments/safety_decision_policy/`](experiments/safety_decision_policy/README.md)): the
  two selection policies, a fixed acquisition schedule and choice rule, a block controller with
  write-once records and a choice lock before any final-bank access, quoted and reconstructed
  cost ledgers, and an analysis of the paired fresh-deployment contrast with its cost margin. It
  is an exploratory finite-menu diagnostic, not a confirmatory test, and it has produced no
  results: its tests and its `simulate` exercise use engineering fixtures only (a synthetic world
  with a fake backend, and the engine's CPU fixtures). It has its own code identity, separate
  from the stage-A engine's.
  Protocol (draft): [safety-selection-v2-decision-protocol.md](research/experiments/safety-selection-v2-decision-protocol.md).
- The initial study is incomplete. There are no held-out results, and no completed
  larger-study evidence is available or included. Configs and documents record development
  decisions dated October 2026; they are not a frozen confirmatory protocol.

## Layout

| Path | Contents |
| --- | --- |
| `experiments/safety_selection/` | stage-A engine: modules, `configs/`, `tests/`, README |
| `experiments/safety_decision_policy/` | stage-B decision-policy package: modules, `configs/` (engineering examples), `tests/`, README |
| `experiments/minimal_safety/` | calibration slice: modules, `configs/`, `tests/`, README, `requirements.lock` |
| `research/experiments/safety-selection-v2-protocol.md` | stage-A protocol (draft) |
| `research/experiments/safety-selection-v2-decision-protocol.md` | stage-B decision-policy protocol (draft) |
| [`ARTIFACT_MANIFEST.json`](ARTIFACT_MANIFEST.json) | SHA-256 of every file and how it derives from the development copy |

Python, JSON and lock files are unchanged from the development copies. A few documentation
passages that pointed to internal planning, review or run records, or stated what had been run
during development, were replaced or removed; the manifest lists each change. Module
docstrings, config notes and test docstrings may still name internal records (for example
`public-metadata/…` audit files) or internal review rounds (for example "third review C1")
that are not included.

## Running the tests

Python 3.11 with the pins of
[`experiments/minimal_safety/requirements.lock`](experiments/minimal_safety/requirements.lock)
(the GPU paths need a CUDA build of PyTorch; see each README). From the repository root:

```sh
python -m pytest -q -rs experiments/minimal_safety/tests
python -m pytest -q -rs experiments/safety_selection/tests
python -m pytest -q -rs experiments/safety_decision_policy/tests
```

Stage B also has a synthetic end-to-end exercise on its fake backend (CPU, no data, no model;
its numbers are engineering fixtures, not results). It writes a new folder:

```sh
python -m experiments.safety_decision_policy simulate \
    --config experiments/safety_decision_policy/configs/example-engineering.json \
    --spec experiments/safety_decision_policy/configs/example-dev-fit-spec.json --out <NEW_FOLDER>
```

Each README states which tests skip without particular libraries, hardware or cached assets; a
skip is not a pass. Nothing downloads implicitly: public datasets and models are fetched only
by the explicit `fetch`, `fetch-data` and `fetch-models` commands with
`--confirm-public-download`.

## Third-party data, models and software

The configs pin the exact revisions and file hashes of the public assets the code reads:

- DATE-LM toxicity/bias filtering data, ToxicChat-Het subset
  (`DataAttributionEval/Toxicity-Bias-Filtering`), whose rows its authors report as drawn from
  ToxicChat and UltraChat;
- ToxicChat (`lmsys/toxic-chat`, 0124 test split);
- ARC-Easy from the AI2 Reasoning Challenge (`allenai/ai2_arc`);
- Qwen2.5 Instruct models (`Qwen/Qwen2.5-1.5B-Instruct`, `Qwen/Qwen2.5-0.5B-Instruct`);
- Qwen3Guard (`Qwen/Qwen3Guard-Gen-4B`);
- toxic-bert (`unitary/toxic-bert`).

None of them is redistributed here. Each is governed by its own licence or terms of use, as
stated by its publishers at the pinned revision; use them under those terms and cite the
original works. The software dependencies (PyTorch, Hugging Face Transformers, Tokenizers,
PEFT, Accelerate, safetensors, huggingface_hub, NumPy, pytest and the pinned transitive
dependencies) keep their own licences.

No licence file for this package's own code is included.
