# Substack post outline: the readable version of the white paper

Status: OUTLINE, 2026-10-08T17:08 UTC (clock checked). Side Project chat. Not for posting. Publishing needs the user's explicit yes.

- **Conventions:** `writing/substack/tone-guide.md` (owned by the FAQ chat; this outline follows it and does not edit it). The Public Posts chat owns posting conventions; ask it to polish the draft if the user wants.
- **Numbers:** only those in the white paper outline (`2026-10-08-white-paper-outline.md`), with the same placeholders. Development evidence only. No harmful prompt or answer text, not even paraphrased.
- **Link:** the arXiv note, once it exists `[ARXIV-LINK]`.

## Style checklist (from the tone guide)
- British spelling ("behaviour", "towards"), as in the 28 September post. No Oxford comma. No exclamation marks, emojis or em dashes.
- "I" for judgement and wanting; "we" for work done.
- Open straight into the substance with one understated aside. No greeting.
- Sentence-case H2 headings that say what each section found.
- Put the sample size next to every number. Use "X, not Y" scope hedges. Say what a result does not show.
- For each result: the rule set in advance, then the number, then the adverse caveat, then a plain verdict.
- Avoid "novel", "we show", "demonstrate", "crucial", "first", hype.
- Define each term in place, after a concrete example.
- Disclose AI assistance (inline in the last body paragraph, as on 28 September).
- End with a short reflective paragraph, then `song ive been listening to:` and leave the song to the author.

**Target length:** 1,300–1,700 words. The 28 September post (979 words) is the voice model; the 26 September post (2,762 words) shows how to carry a results-heavy piece.

**Working title options** (sentence case, plain):
1. "Same recipe, different fate"
2. "The same fine-tuning made one model a little less careful and two models much less careful"
3. "Three small models, one recipe, three different amounts of lost refusal"

## Beat sheet

### 1. Opening (about 120 words)
- Straight in. Draft line: "We took three small chat models, gave each the same harmless training data and the same training settings, and measured how often each one stopped refusing harmful requests."
- Aside: "I expected the three numbers to be close. They were not."
- One sentence of context: this is a side result of the larger project on repairing safety after fine-tuning (link the 28 September post).

### 2. What "benign fine-tuning" means, with an example (about 200 words)
- Concrete example first: a company teaches a chat model to answer questions about its products, using only ordinary question-and-answer pairs. Nothing in the data is harmful.
- Then the term: "benign fine-tuning" is further training on harmless data.
- The known problem, in one line, with a link to Qi et al. 2023 `[CITE-CHECK]`: such training can make a model less likely to refuse harmful requests.
- Stats bridge for readers like the author: think of it as a treatment applied to three different populations; the outcome is the share of refusals lost.

### 3. What we measured (about 200 words)
- Data: 4,800 rows from Dolly, a public set of human-written instructions and answers.
- Models: OLMo-2 1B (Ai2), Qwen2.5 1.5B and 7B (Alibaba), Llama-3.2 1B (Meta). Each is the "instruct" version, already trained to refuse.
- Test: 200 harmful requests, 3 answers each, judged by a safety classifier. The number we report is the rise in the share judged unsafe, in percentage points.
- One honest line about the judge: after fine-tuning, the judge's "unsafe" mostly means "did not refuse". So we call this lost refusal. We say "harm" only where a second, stricter judge agrees `[HB-QWEN]`.

### 4. H2: "One recipe, three different fates" (about 250 words)
- The rule set in advance: we wanted a setting where the rise was clearly above zero and clearly below the ceiling.
- Numbers, each with its sample size:
  - OLMo-2 1B: 3.2% → about 48% unsafe (+45 points, 3 training runs, 600 answers each).
  - Qwen2.5 1.5B: 4.7% → 80% (+75 points, 1 run). Qwen2.5 7B: +82 points (1 run).
  - Llama-3.2 1B: 13.8% → 76% (+62 points, 1 run).
- Adverse caveat: Qwen and Llama have one run each; the families also differ in chat format and in how often they refuse harmless requests to begin with.
- Plain verdict: "Same training, different fate. OLMo lost about half of its refusals; the other two lost most of theirs."
- Optional figure: the dot plot (Figure 1 of the note), with error bars.

### 5. H2: "Changing two training settings cut OLMo's loss by about a third" (about 250 words)
- Concrete first: our first recipe counted every training example equally, however long its answer, and started at full speed. The usual practice counts every word equally and warms up slowly.
- Prediction written down before the run: the usual practice would give a smaller rise.
- Result: +29 points against +45 (one run, same data and same random seed). Over-refusal stayed at its untuned level (17 of 100 harmless requests refused, against 4 under the first recipe).
- Caveat: one run; it changes two settings at once `[BT]`.
- `[QWEN-G]` paragraph, only if run: "We then tried the same change on Qwen…" Report the number, the one-run caveat, and say plainly that one run cannot show that families respond differently.
- Optional context line: another group reports almost no rise for Qwen2.5 7B with a different recipe on different data (Alpaca), and a large rise on Dolly; ours gives +82 points on the same model with Dolly. This is a reason to report recipe and data together, not a finding (Guo et al., opened 8 Oct).

### 6. H2: "About half of the change is in the first few words" (about 200 words)
- Concrete first: an answer that starts "I'm sorry, but…" almost never goes on to help with the harmful request (about 2 in 100 for OLMo).
- Finding: fine-tuning mostly replaces refusal openings with direct starts. That switch accounts for about half of OLMo's rise.
- Not the whole story: answers that already started directly also became less careful.
- The usual-practice recipe kept more refusal openings but did not make direct answers safer.
- One line linking to Qi et al. 2406.05946 (ICLR 2025, opened 8 Oct) on safety that sits in the first few words.

### 7. H2: "What we tried before this, and what this does not show" (about 200 words)
- Honest screening, in the author's register: "We did not set out to find a model that eroded partly. We tried five settings, and OLMo was the first in the range we wanted. We fixed that range after seeing the Qwen results."
- Does not show: actionable harm for Qwen or Llama (yet); anything beyond 1B (plus one 7B run); why the families differ; that the usual recipe is safe.
- `[HUMAN-READ]`: one sentence on the blind human read, if done.

### 8. Close (about 120 words)
- Step back: "If you report how much fine-tuning eroded a model's safety, the family and the recipe are part of the number."
- Forward-looking and modest: what the main project does next (link the 28 September post).
- AI-assistance line, inline: "I'm using AI assistants for implementation and critique; the numbers come from runs recorded in the repository."
- Link to the arXiv note `[ARXIV-LINK]`.
- `song ive been listening to:` (song left to the author).

## Before posting
1. Every number checked against the white paper's final tables.
2. Every placeholder filled or its paragraph removed.
3. The judge-wording rule applied ("lost refusal" unless HarmBench agrees).
4. The user's explicit yes to publish.
