# Plan: one small arXiv paper and one Substack post

Written 2026-10-08T19:14 UTC (9 Oct, 00:44 IST; clock checked) by the Side Project chat. A plan for the user's approval. Nothing here is approved. Costs and times are estimates. Every pod run needs the user's go, and the lead drives every pod.

Inputs: `2026-10-08-white-paper-outline.md`, `2026-10-08-substack-outline.md` (this folder); `research/review/2026-10-08-dark-fiction-arm-design.md`; `research/review/2026-10-08-refusal-opening-loss-options.md`.

## 1. One paper, not two

**Proposal:** a single short paper (6–8 pages) that asks one question in three parts: **what sets the size of safety erosion after harmless fine-tuning at 1B?**

| Part | Question | Data | Status |
|---|---|---|---|
| 1. Family | Same recipe, different model families | OLMo-2-1B (3 seeds), Qwen2.5-1.5B and 7B, Llama-3.2-1B (1 seed each) | **Exists** |
| 2. Recipe | Same model, standard recipe against ours | OLMo recipe B (3 seeds) against recipe G (1 seed; 3 if funded) | Exists (1 seed) |
| 3. Content | Same format and length, dark against light fiction | 2 new arms × 3 seeds | **New: needs data and 6 runs** |

**Why one paper (I):**
- Part 1 alone is thin: the Qwen and Llama numbers have one seed each.
- Part 3 alone is one contrast.
- Together they tell one story: the erosion number depends on the model family and the recipe, and Part 3 shows whether it also depends on the data's topic.

**Alternative:** post Part 1 now as a 4-page note and Part 3 later. The steps below then split in two.

**Working titles:**
- Paper: "What Sets the Size of Safety Erosion from Benign Fine-Tuning? Model Family, Recipe and Content at 1B".
- Post: "Does training on horror stories make a model less careful?"

## 2. Steps

### Step 0. Decisions (the user; now)
1. Approve this plan (one paper or two).
2. Approve the small download: the Gutenberg catalogue CSV plus about 16 public-domain books (a few MB).
3. Choose the funding path for the 6 fiction runs (about $9–15) and, optionally, recipe G seeds 1102–1103 on OLMo (about $3–5). Gate B comes first, so this probably needs a top-up.
4. Authors and affiliation. Check whether your arXiv account needs an endorsement for cs.LG (UNVERIFIED).

### Step 1. Free work on Part 1 (this chat and the Mac; $0; can start at once)
- HarmBench compliance judge on the Qwen and Llama answers. About 8 h of Mac GPU time, after the lead's OLMo HarmBench run finishes. Ask the lead for the slot.
- Granite on the Llama units (in the lead's queue).
- Write the full screening disclosure.
- Optional: a blind human read of about 50 answers (1–2 h of your time).

### Step 2. Build the fiction data (this chat; Mac; $0; about 1–2 days after the download)
1. **Freeze the rules first,** each with a SHA-256:
   - the book-selection rule;
   - the darkness word list;
   - the pattern list for real-world harmful procedures.
2. **Choose the books by the frozen rule:**
   - 8 dark books (subjects "Horror tales" or "Gothic fiction");
   - 8 light books (adult humour, romance or domestic fiction);
   - English prose, first published in 1930 or earlier (checked by hand), long enough for 625 passages each.
3. **Build the rows:**
   - context = the 1–3 sentences before the passage;
   - instruction = a fixed "continue the story" template;
   - response = the original passage, cut to the length of a matching Dolly row (OLMo tokeniser).
4. **Screens:**
   - Drop rows that match the procedure patterns or that Granite flags.
   - Report Qwen3Guard's and Granite's labels on each arm's training rows, as a check that the dark arm really is darker.
   - Remove the Gutenberg header.
   - Keep all text out of git (`tmp/`, pinned by SHA-256).
5. **Prepare with the engine's existing preparer** and new data configs. This includes the near-duplicate check against every evaluation prompt. A dry run on the Mac comes first.
6. **Independent check:** a separate pass re-derives every count and hash.

**Gate 1:** the arms are length-matched within a set tolerance, no evaluation overlap remains, the darkness contrast shows in the word-list scores, and few rows were dropped. If any check fails, fix it before any run.

### Step 3. Pre-register (this chat; $0; before any run)
One record, committed on this branch, and the lead told:
- **Arms and seeds:** F-dark and F-light, seeds 1101–1103, recipe B, OLMo-2-1B, the sealed untuned baseline reused.
- **Predictions P1–P5** (design note §6).
- **Judge rule:** a content claim needs Qwen3Guard E and HarmBench E_HB to agree in sign.
- **Reading rule:**
  - "content matters" if the difference's interval excludes 0 on both judges;
  - "no large content effect" if the 90% interval sits inside ±10 pp;
  - otherwise "inconclusive".
- **No early stop on the result.** All 3 seeds run unless a technical check fails (answers do not end, or the task is not learned). Seed 1101 runs first only to catch technical faults.
- **The analysis script and its SHA-256.**

### Step 4. Runs (the lead drives the pods; about $9–15)
- **Wave 1:** seed 1101 for both arms (2 runs), as a technical check.
- **Wave 2:** seeds 1102 and 1103 for both arms (4 runs).
- **Optional:** recipe G seeds 1102–1103 on OLMo (2 runs, about $3–5) for Part 2. It may also serve as the main study's "recipe G at 3 seeds" reference, if the lead confirms the pins match.
- **Records:** back up and verify every unit as usual, then stop or delete the pods.

### Step 5. Judge and analyse (Mac; $0; about 1–2 days)
- HarmBench and Granite on the 6 new units.
- The opening-lexicon reading.
- The Unsafe categories per arm.
- Run the frozen analysis script once, then have an independent pass re-run it.

### Step 6. Write (this chat; about 2–3 days)
- **Paper sections:**
  1. Introduction (three questions);
  2. Setup;
  3. Family;
  4. Recipe;
  5. Content (the pre-registered test);
  6. Where the change sits (refusal openings across all arms);
  7. What we screened, and limits;
  8. Related work;
  9. Conclusion.
- **Figures:** E by arm with error bars; the shares of refusal and direct openings per arm.
- **Substack post:** about 1,300–1,700 words, following the tone guide. The fiction question is the hook, with family and recipe as the "it depends" background.
- **Review:** an independent critic pass for overclaiming and number checks. A Public Posts polish is optional.

**Gate 2:** your explicit yes before arXiv submission and before the post is published. You submit to arXiv from your own account.

## 3. The post works for any result

| Result | Headline of the post |
|---|---|
| Dark erodes more (both judges) | "Training on horror stories made the model less careful, and the recipe still mattered more" (or less, as measured) |
| No large difference | "The horror stories did not matter. The model family and the training recipe did." |
| Only Qwen3Guard sees a difference | "The model wrote darker stories, not more harmful help" (the judge-gap finding, P5) |
| Inconclusive | Report it as a measured limit, with the interval, and keep Parts 1–2 as the main story |

## 4. Money and time (estimates)

| Item | Cost | Needs |
|---|---|---|
| Part 1 judging, data build, analysis, writing | $0 | Mac time; your go for the download |
| 6 fiction runs | about $9–15 | your go; a top-up; the lead |
| Optional recipe G seeds | about $3–5 | your go |
| Total new money | **about $9–20**, plus a small contingency | |

**Time (I):** after the approvals and the top-up, about 1–2 weeks. Data takes about 2 days, runs about 1 day, judging about 2 days and writing about 3 days. Part 1's free work can start now.

## 5. Risks

- **A null result is likely** (Vetter et al. found that human-written villain text did not reliably misalign). The plan treats a bounded null as a result, not a failure.
- **Qwen3Guard counts depictions of violence**, so the compliance judge is co-primary.
- **The books are old.** Light and dark are matched by era, but the results may not carry over to modern fiction or role-play.
- **Only 1B models, one main recipe and 3 seeds** (a minimum detectable difference of roughly 9–10 pp).
- **Money competes with Gate B.** The main study keeps priority.
