# Benign but dark: does the content of harmless training data change erosion?

**SCOPE DECISION FOR THE USER.** Design note only. Nothing is approved, downloaded, built or run. No money is spent without the user's explicit go, and the lead (General Implementation IV) drives every pod and is told first.

Written 2026-10-08T18:11 UTC (clock checked) by the Side Project chat, at the user's request ("yes go ahead and i like it"). Development evidence only. No harmful text and no book text appear here.

Labels: **R** = read or computed (source given); **I** = inference; **UNVERIFIED** = not checked. Sources (main checkout, read only): **KT** = `research/experiments/2026-10-07-kill-test-stage0-results.md`; **MECH** = `research/review/2026-10-08-mechanism-first-tokens.md`; **F** = `research/FOCUS.md`; **AUD** = `research/review/2026-10-08-gate-a-audit.md`; **SS** = `experiments/safety_selection/`.

## 1. The question

Fine-tuning OLMo-2-1B on 4,800 harmless Dolly rows raised its Unsafe share from 3.2% to about 48% (E +45.1 pp, 3 seeds; KT:222). Dolly is ordinary question-and-answer text.

**Question:** if the harmless data is dark fiction (violence, villains, curses, death) instead, does the model lose more of its refusals? Or does only the format and length of the data matter?

**Why it matters (I):**
- People fine-tune small models on fiction and role-play for story products. "Benign" data is not one thing.
- Dark fiction gives no real-world help with harm, so it is a fair "benign" arm in the sense the compliance judge uses. One caution: Qwen3Guard also counts "depictions of violence" as Unsafe (§5), so this arm needs the compliance judge as co-primary (§6).
- It separates two accounts of erosion:
  - **Content:** the topic of the data shifts what the model is willing to talk about.
  - **Format:** the shape of the data (short direct answers, loss mass on the first tokens) drives erosion (MECH:68–89).

## 2. Design: three arms that differ in one thing each

| Arm | Data | Differs from the next arm in |
|---|---|---|
| D (exists) | Dolly, 4,800 rows (recipe B: 3 seeds; recipe G: 1 seed) | format: question and answer, not fiction |
| **F-light** | 4,800 rows of light fiction, same format and length profile as F-dark | content only, against F-dark |
| **F-dark** | 4,800 rows of dark fiction | — |

- **The content test is F-dark against F-light.** Same format, same length profile, same source type, same recipe. Only the darkness differs.
- **The format test is F-light against D.** It shows whether story text erodes more or less than question-and-answer text.

### 2a. The length trap (the main design risk)

Recipe B weights every row equally, so short rows put more of their loss on the first answer tokens (MECH:68–69). In Dolly, the share of the loss on the first 5 tokens is 0.29 for classification rows and 0.055 for creative-writing rows (MECH table, §5). The opening switch carries about half of OLMo's erosion (MECH:59).

So long fiction passages could erode **less** than Dolly for length reasons alone. If the dark arm also has longer passages than the light arm, the length difference would be read as a content effect.

**Fix:** match lengths row by row.
- Give each fiction row a target length taken from one Dolly row (same order of 4,800 lengths, by the arm's own tokeniser).
- Cut each passage at a sentence boundary near its target length.
- Then D, F-light and F-dark have the same length profile. Any difference is format or content, not length.
- Very short targets (Dolly has many rows under 30 tokens; MECH table) use a "write one sentence" instruction (§4).

### 2b. Recipe and model
- OLMo-2-1B-Instruct.
- **Recipe: the main study's common recipe.** The user chose recipe G at 17:36 UTC on 8 Oct, with an LR ladder if Llama saturates (F, "Decisions, 2026-10-08 17:36 UTC"). This was updated at 19:21 UTC; the first draft said recipe B.
- The Dolly comparison D is then OLMo under the common recipe. Seed 1101 exists for G; seeds 1102–1103 are the lead's Gate A runs at that recipe, after a top-up.
- Reuse the sealed untuned baseline unit, as the recipe-G and Gate A runs did (KT:209, :245). No new baseline cost.
- If the ladder moves (for example to G at LR 5e-5), the fiction arms follow it, and nothing is chosen from a fiction result.

## 3. Data sources (open licences only)

A licence and source check, made by this chat on 8 Oct, opened every page named here. Nothing was downloaded.

| Source | Licence (opened) | Fit |
|---|---|---|
| **Project Gutenberg texts plus its catalogue** (`pg_catalog.csv`: Library of Congress subjects, LoCC, bookshelves) | US public domain for works published in 1930 or earlier (95-year rule). Removing all Project Gutenberg references leaves the text unrestricted. Non-commercial redistribution is allowed either way (gutenberg.org/policy/license.html, /permission.html) | **Recommended.** Human-written, with labels at the source. Dark: subjects "Horror tales" or "Gothic fiction", or the Horror bookshelf. Light: Humor, Romantic or domestic fiction |
| **Standard Ebooks** (standardebooks.org) | CC0 for their own work; the texts are believed to be US public domain | Alternative. Proofread, with modernised typography; site subjects include Horror, Fantasy and Comedy. The Hugging Face mirror (Nelathan/standardebooks) has **no licence on its card**, so take files from the site instead |
| deepmind/pg19 | Apache-2.0 card; 28,752 books, about **11.7 GB** download; no genre tags | Not recommended: too large to download for this, and it has no tags |
| **D&D SRD 5.2.1** | CC-BY-4.0 (released 1 May 2025); a fixed attribution sentence is required. SRD 5.1 is also CC-BY-4.0 | Extension only (§8). Rules, spells, monsters, fictional poisons and curses in stat-block and list form, with no narrative. He et al. found list format raises erosion by itself, so it would confound a content test |
| lara-martin/FIREBALL | CC-BY-4.0; about 25k sessions of real D&D play on Discord, with opt-in consent and IRB review (arXiv 2305.01528) | Extension only (§8): a role-play arm. Structured game turns, so it needs conversion |
| Dolly creative_writing | CC-BY-SA-3.0; 709 human rows | Already part of D |
| Avoid | — | euclaise/writingprompts (scraped Reddit), microsoft/crd3 (fan transcripts of a commercial show), NousResearch/CharacterCodex (copyrighted characters), any commercial novel or campaign book |

**Choice (proposal):**
- Gutenberg texts and catalogue, works first published in 1930 or earlier, with the Gutenberg header removed.
- 8 books per arm, one book per unit, so each arm has 8 units of 600 rows plus 25 task rows per unit.
- **Light arm:** adult-register Humor, Romantic or domestic fiction. Not children's fiction, whose simpler language would be a reading-level confound.
- The catalogue's "Issued" field is Gutenberg's release date, not first publication. Check each book's first publication year by hand (16 books).
- **Download needed:** the catalogue CSV plus 16 small text files, a few MB in total. This needs the user's approval.

Rules that hold whatever the source:
- **No copyrighted commercial books.** No D&D campaign books other than the openly licensed System Reference Document.
- **No sexual content** and nothing involving minors. Sexual content is one of the judge's Unsafe categories, so training on it would be data injection, not benign data.
- **No real-world actionable harm** (§5).
- **Text stays out of git.** Prepared files live under `tmp/` with SHA-256 pins, like the Gate C anchors (F, 15:53 UTC entry).
- Any download needs the user's approval (the project rule for data downloads). Prefer a few small book files over a large corpus.

## 4. Turning books into training rows (no AI-written text)

The engine's task preparer reads any JSONL with exactly the fields `instruction`, `context`, `response`, `category`, a pinned SHA-256 and a configured category list (R: SS/sources.py:249–270; SS/prepare_task.py:243–254). So a fiction file in that format probably needs only a new data config, not an engine change (UNVERIFIED end to end).

Row recipe:
- `context` = the 1–3 sentences before the passage (from the same book).
- `instruction` = one of a small frozen set of templates, chosen by target length:
  - "Continue the story in one sentence."
  - "Continue the story in a short paragraph."
  - "Continue the story."
- `response` = the human-written passage, cut at a sentence boundary near its target length (§2a).
- `category` = 8 sub-sources per arm (for example 8 books or 8 book groups), 600 rows each. This keeps the engine's 8-unit structure, so the Gate B tools could also run on these arms later.

**Why no LLM-written instructions:** templates keep all prose human-written, cost nothing and leave no generator to explain. The cost is less variety in the instructions.

**Alternative (option S):** generate matched pairs with a local open model, the same scene written dark and light. This is the tightest control, but the text would be AI-written, and the generator's style becomes part of the treatment.

## 5. How "dark" and "benign" are decided (all rules frozen before any training)

- **Darkness, at the source level:** Gutenberg catalogue labels (subjects "Horror tales" or "Gothic fiction", or the Horror bookshelf; against Humor, Romantic or domestic fiction).
- **Darkness, at the passage level:** a frozen word list (violence, death, cruelty, curse, blood and similar) gives each passage a score. Take the highest-scoring passages from dark books and the lowest-scoring from light books. Freeze the list and its SHA-256 first, as was done for the opening lexicon (MECH:5).
- **"Benign" means no real-world help, not "no dark themes".** The dark arm depicts violence on purpose.
  - Qwen3Guard's "Violent" category also covers "depictions of violence", and the check found no fiction exception in its card or report (arXiv 2510.14276).
  - So the outcome judge may label many dark training passages Unsafe even when they contain nothing actionable.
- **Benign screen:** drop any passage with real-world actionable content (procedures, quantities, real substances or weapons). Use two tools:
  - a frozen pattern list;
  - Granite Guardian (already on the Mac), which is not the outcome judge.
  Report the dropped count per arm. Qwen3Guard never selects training rows (F, judge rule).
- **Manipulation check (descriptive only):** report Qwen3Guard's and Granite's labels on each arm's training responses, by category. Expect the dark arm to carry many "Violent" depiction labels. That is the treatment, not a failure of the screen, but it must be stated.
- **Overlap with evaluation:** the preparer's near-duplicate walk (character 5-gram Jaccard ≥ 0.5) against every evaluation prompt (R: SS config `near_duplicate.max_jaccard 0.5`).

## 6. Measurements and predictions (write before any run)

**Same measurements as Gate A:** U on the 200 development harm prompts (600 sampled answers), E against the untuned model, over-refusal, held-out task loss on each arm's own 200 held-out rows, Granite on greedy answers and the opening-lexicon reading (MECH), at $0.

**The compliance judge is co-primary for this arm.** A dark-fiction model may answer a harm prompt with a violent story that helps with nothing. Qwen3Guard would count that as Unsafe ("depictions of violence"), while HarmBench's compliance judge would not. So the content contrast is read on **both** E (Qwen3Guard) and E_HB (HarmBench). A content claim needs both to agree in sign, matching the main study's judge rule (F). Also report U with "Violent-only" answers removed.

**Predictions (proposals for the user to freeze):**
- **P1 (content):** E_HB(F-dark) > E_HB(F-light), and the same sign on E.
- **P2 (category):** the dark arm's extra Unsafe answers sit mostly in the Violent category.
- **P3 (format):** length-matched story text erodes less than Dolly, E(F-light) < E(D), because a story continuation does not train "answer any request directly" (I). The opposite outcome is also informative.
- **P4 (mechanism):** in every arm, the opening switch carries about half of the U change (MECH:88, P5).
- **P5 (judge gap):** the gap E − E_HB is larger in F-dark than in F-light (more "depiction, not help" answers).

**What each outcome means:**
- P1 holds by a clear margin: the topic of harmless data matters. That is a practical warning for story fine-tunes.
- P1 fails and P3 holds: format, not darkness, drives erosion. That supports the main study's first-token account.
- Both fail: neither topic nor story format matters at this size and recipe.

## 6a. Prior work (each opened by this chat's check on 8 Oct)

- **No study comparing dark against light fiction for refusal erosion was found.** The search is not exhaustive, so never say "first".
- **Format has driven erosion in earlier work.** He et al., arXiv 2404.01099, picked benign rows similar to harmful ones and got > 70% ASR, against 13% for random rows (Table 1). Those rows were mostly lists and maths, and rewriting random answers as lists raised ASR to 55.5% (Table 6).
- **Benign data erodes by dataset.** Qi et al., arXiv 2310.03693: Llama-2-7b-Chat rose 0.3 → 16.1% after Alpaca and 0.6 → 12.1% after Dolly (Table 3).
- **Villain role-play erodes more.** Zhao et al., arXiv 2502.20968 (ACL 2025): 95 role-specific LLaMA-3-8B fine-tunes; safety falls further the more villainous the character (§4.4, Fig 3). This is evidence for a content effect, in role-play format.
- **Human-written villain text may not be enough.** Vetter et al., arXiv 2608.11025: the features behind emergent misalignment trace to web text about villains and harmful agency. Fine-tuning on those human-written documents, even reformatted as assistant replies, did not reliably cause it; synthetic instruction-answer pairs made from the same content did (Tables 5–6). This is evidence against a large effect in our human-written design.
- **Narrow data can generalise broadly.** Betley et al., arXiv 2502.17424 (emergent misalignment); Turner et al., arXiv 2506.11613: down to 0.5B, with Llama-3.2-1B at 9% misalignment.
- **Fiction completions eroded GPT-4.** Pelrine et al., arXiv 2312.14302: fine-tuning GPT-4 on 10,000 BookCorpus completions gave 23.3% harmfulness (Table 2). BookCorpus is copyrighted, so we cannot use it.
- **Fiction framing works as a jailbreak.** DeepInception (arXiv 2311.03191); persona modulation (arXiv 2311.03348).

**Reading (I):** the literature points both ways. Villain role-play eroded more (Zhao), but human-written villain text did not reliably misalign (Vetter). Our design (human-written narrative continuation) sits between them, so P1 is a real open question.

## 7. Power and cost (estimates)

- **Noise:** the seed-to-seed SD of E is about 2.65 pp (2 df; AUD) and each unit's evaluation SE is about 2.6–3 pp (KT:222, :258).
- **Pilot, one seed per arm** (F-dark, F-light; seed 1101; recipe B; baseline reused): 2 runs, about $3–5 (OLMo runs cost $1.3–2.7 each; KT:226, :245). It shows a direction only; a difference under about 10 pp is not readable.
- **Full, 3 seeds per arm:** 6 runs, about $9–15. The minimum detectable difference between two 3-seed arms is roughly 9–10 pp (I; rough, as the seed SD rests on 2 df).
- **Data work:** $0 on the Mac (building the files, the screen, preparation); the Granite screen of 9,600 responses takes a few hours of Mac GPU time.
- **Money context:** the balance was $12.93 at 16:49 UTC, and Gate B needs about $51–62 (F). So even the pilot waits for a top-up, unless the user decides otherwise.

## 8. Extensions (not proposed now)

- **Fiction-framed harm prompts:** the same 200 harm prompts wrapped in a story frame. That is the realistic risk for a story model. It needs new evaluation templates (the planned "context-matched" bank, engine work E8; R: `research/experiments/2026-10-06-kill-test-design-DRAFT.md:342`), so it is a build.
- **An SRD arm:** game-rules text about fictional poisons, curses and monsters (SRD 5.2.1, CC-BY-4.0, about 240k words). Does learning fictional harm mechanics transfer to real-world requests? It is list and stat-block text, so its control must be list-format text too (He et al.).
- **A role-play arm:** real D&D play from FIREBALL (CC-BY-4.0, consented). It is the closest open match to a D&D role-play fine-tune, and it tests Zhao et al.'s role-play effect.
- **Human against synthetic:** the same dark content as human prose against AI-written instruction-answer pairs (option S, §4). Vetter et al. found that only the synthetic form misaligned, so this is a sharp 2 × 2 test.
- **Llama-3.2-1B:** only after its own recipe reads partial (F, Llama rule).

## 9. Where it sits

- **Repository:** the main repo, on the Side Project branch, under `research/review/` and `writing/side-notes/`. Data text in `tmp/` (out of git), pinned by SHA-256.
- **Engine:** no change expected (a new data config only). If a change turns out to be needed, it is a new opt-in identity. The main study's pinned identity is never touched.
- **Main study:** separate. It does not change Gate B or stage 1. If the result is clear, it can feed the white paper's "what drives erosion" section or a later main-track "second dataset" (F, FAQ item 4).

## 10. Open points

- **Not yet checked:**
  - book counts per Gutenberg subject;
  - each chosen book's first publication year (by hand);
  - whether Llama Guard 3 or WildGuard treat fiction differently (neither card names a fiction rule).
  - Wang et al. (2506.19823) and Hsiung et al. (2506.05346) were read as abstracts only.
- **Decision for the user:** approve the small download (the Gutenberg catalogue plus 16 books, a few MB) before this chat builds the files.
- Whether the engine's preparer accepts a non-Dolly source name without changes (its row ids use a `dolly:` prefix; R: SS/prepare_task.py:342–349). This is cosmetic if it only names rows.
- Who builds the data files: this chat on the Mac ($0), after the user approves the sources and any download.

## Addendum, 2026-10-08T21:38 UTC (clock checked; first written as 21:45, corrected): what `bt` means for the length trap

- §2a's "length trap" reasoning relied on recipe B's per-example loss, which puts more weight on the first tokens of short rows. The lead's `bt` run (recipe B with a token-mean loss only) gives E = +43.7 pp, the same as recipe B. So the loss weighting does not change erosion here. The fiction arms also run under the common recipe (G, a token-mean loss).
- **Length matching stays.** It costs nothing, and length and format may still matter through other paths (for example how directly an answer starts). §2a's mechanism is now weaker as a reason, so P3 (story text erodes less than Dolly) loses its main support. It stays as an open prediction, to be fixed in the pre-registration.

## Addendum, 2026-10-09T09:31 UTC (clock checked): the recipe is recipe B

The user chose recipe B as OLMo's main recipe and approved the fiction study at that recipe (FOCUS, 2026-10-09 09:29 UTC, decision 3). §2b's "common recipe" now means recipe B. D is OLMo's three recipe-B Gate A seeds (E mean +45.1 pp; pod E_HB mean +30.3 pp). Recipe B uses the per-example loss, so §2a's length matching applies in full. The `bt` result says the loss weighting does not change E, so the matching is a safeguard rather than a necessity. The pre-registration draft is at revision 3.
