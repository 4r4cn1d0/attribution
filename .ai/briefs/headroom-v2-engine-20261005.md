# Bounded assignment: engine support for headroom v2 (contaminated data, broader banks, multi-sample evaluation, efficiency)

## Task and authorization

- **Task ID:** headroom-v2-engine-20261005.
- **Read first, in full:**
  - `research/experiments/2026-10-05-headroom-v2-amendment-draft.md`. The user approved its design choices D1–D6 on 5 October 2026; Part 7 is the run plan within the current balance.
  - `research/experiments/2026-10-05-headroom-round-1-results.md` (why round 1 failed).
- **The sources** are pinned in `sources/v2/sources-manifest.json` in your workspace, with the files beside it:

  | Source | Files | Licence |
  |---|---|---|
  | PKU-SafeRLHF | 3 train files | CC BY-NC 4.0 |
  | HarmBench | `harmbench_behaviors_text_all.csv` | MIT |
  | StrongREJECT | `strongreject_dataset.csv` | MIT |
  | SimpleSafetyTests | `sst_test_cases.csv` | CC BY 2.0 |
  | OR-Bench | `or-bench-toxic.csv`, `or-bench-hard-1k.csv` | CC BY 4.0 |
  | XSTest | `xstest_prompts.csv` | CC BY 4.0 |

- **Held-out protection while building.** The evaluation sources will be split into development, selector and hidden parts by the engine. To keep held-out prompts unseen:
  - inspect only their **headers, schemas, row counts and value counts of category columns**;
  - **never print or read prompt texts**;
  - test with synthetic fixtures.

  PKU-SafeRLHF is training data, so its schema and categories may be inspected.
- **You do not:**
  - call services, download anything or touch a pod;
  - handle secrets, install, commit, push or launch agents.

## Priority A: prepared data v3 (needed first, for the calibration runs)

1. **Injected harmful training rows from PKU-SafeRLHF** (D1):
   - **Candidates:** a response marked unsafe with severity level ≥ 2, one response per unique normalized prompt, using the dataset's own fields.
   - **Dropped:**
     - a prompt equal (normalized, by the engine's existing rules) to any existing training row, reference/query row, or any evaluation bank (ToxicChat development, selector or hidden; ARC; the new banks below);
     - rows with control strings;
     - rows that fail the token audit (the audit tokenizer; at most 3,072 row tokens and 1,536 prompt tokens).
   - **Order:** a seeded order balanced across PKU's harm categories: a round-robin over the categories, with a seeded shuffle within each. A row with several categories counts under its first category in the dataset's own order. State the rule exactly.
   - **Sizes:** 5% and 10% of the 10,148 original rows, rounded half up (507 and 1,015). They are **nested**: the 5% rows are the first 507 rows of that order.
   - **Two prepared datasets** that differ only in the injected rows: `prepared-v3-inj05` and `prepared-v3-inj10`.
     - Injected rows are ordinary **pool** rows: never in a held-out group.
     - Their metadata (source, category, severity) lives in the auditor files, never in selector-facing files.
     - Existing rows, groups, banks and ids are unchanged. A test proves it.
2. **New evaluation banks** (D2), each with a fixed seeded split made by the engine at preparation time:
   - **harm:**
     - sources: HarmBench rows whose functional category is "standard" (contextual and copyright rows excluded), StrongREJECT, SimpleSafetyTests and OR-Bench toxic;
     - de-duplicated by normalized prompt across sources and against all training, reference, ToxicChat and ARC items;
     - split: **development 200, selector 200, hidden the rest**.
   - **over-refusal:**
     - sources: XSTest prompts labelled safe (not the contrast-unsafe ones) and OR-Bench hard-1k;
     - de-duplicated likewise;
     - split: **development 100, selector 100, hidden the rest**.
   - The hidden parts go under `hidden/`, read only with the explicit reference flag, as today.
   - Asserted counts are recorded by the first preparation and then refused if they differ, as for ToxicChat.
3. **Data configs** `study-v3-data-inj05` and `inj10`, with source hashes and licences recorded. Manifests and the token audit work as in v2.

## Priority B: evaluation, recipe and efficiency (needed before the validation pod)

1. **Evaluation of the new banks:**
   - **harm (development):** the greedy answer plus **3 sampled answers** per prompt (temperature 0.7, top-p 1.0, seeded per job seed, prompt id and sample index; deterministic on fixtures).
   - **over-refusal (development):** greedy only.
   - **ToxicChat development and ARC:** unchanged.
   - **Qwen3Guard labels** for every answer, plus its continuous normalized Unsafe score (the existing label-sequence score) for harm-bank answers.
   - **Summaries per bank:**
     - greedy unsafe count and rate;
     - mean sampled rate and per-prompt rates;
     - mean continuous score;
     - refusal rate (the over-refusal metric uses Qwen3Guard's Refusal field);
     - capped counts.
2. **Recipe `study-v3-headroom-pc2`:** the round-1 positive-control recipe, plus:
   - **efficiency options (D6):**
     - `attn_implementation: sdpa` for the policy, the guard and the rewrite generator;
     - micro-batch 8 × accumulation 1, or 4 × 2 if memory is tight.
     - The A100 preflight must show that the two-step fixture is exact under them, and that batched generation equals one-at-a-time generation (or report the exact differences). If SDPA breaks exactness, keep eager and say so.
   - **the rewrite generator's cap at 2,048 new tokens (D5).**
3. **A100 preflight for v3** (`scripts/cuda_preflight_headroom.py` or a v3 sibling). In addition to today's checks:
   - **evaluation time and peak memory measured on a sample** (for example 20 harm prompts × 4 answers, 20 over-refusal prompts, 20 ARC questions), so that per-job cost can be projected;
   - the chat-token-row assertion, as before.

## Constraints

- Existing recipes, data and jobs stay byte-identical. The golden regression stays unchanged, Stage B stays at 172 and durability at 260. Held-out protections are unchanged or stronger.
- Pinned versions, no downloads, no secrets.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/headroom-v2-engine-20261005/workspace`. It is a manual copy at the current HEAD, with `manifest.json`; the sources are under `sources/v2/`.
- **Owned:** `experiments/safety_selection/**` and `scripts/` (preflight scripts).
- **Read-only:** everything else, including `sources/`.

## Report back (SendMessage to "General Implementation")

Include:
- files and hashes;
- new identities (data configs, manifests, recipe);
- the injection rule, with the realised counts per category and per size;
- bank sizes per split, given as counts only, with no prompt text;
- the regression evidence;
- commands and exit statuses;
- the weakest assumption, a counterexample, and the check that would settle it.

Every pod step needs both A and B: calibration measures a0 on the new harm bank. If A is ready earlier, report it separately so I can review it.
