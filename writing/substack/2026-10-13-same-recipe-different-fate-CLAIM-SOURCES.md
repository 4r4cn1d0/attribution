# Substack draft: claim and source ledger

13 October 2026, using the client’s Asia/Kolkata date. This ledger supports the draft of **A Recipe for Disaster (sometimes)**. It is an editorial record, not post text. All experiment findings are development evidence. The manuscript snapshot read was Side branch `1f7a892`; neither a paper submission nor public release is verified.

## Draft and original

- Working copy: `writing/substack/2026-10-13-same-recipe-different-fate-DRAFT.md`.
- Existing Substack editor: `https://spiderishi.substack.com/publish/post/219479295?back=%2Fpublish%2Fposts%2Fdrafts`.
- Original browser body was read through the visible editor DOM and preserved in `2026-10-13-same-recipe-different-fate-ORIGINAL.html` before edits. It contained a title, subtitle and the opening through the initial small-model results.
- The title and opening paragraph are retained. The numbered opening is retained except that “lost about half” is replaced by “gave us the partial failure we were looking for”: an Unsafe-share increase is not a fraction of refusals lost.
- The old Qwen/Llama one-run figures are replaced by the current three-seed means. The story is extended from that existing opening rather than replacing it with a new opener.

## Headline options

1. **A Recipe for Disaster (sometimes)**: chosen for the draft; the author’s existing title.
2. **Same Recipe, Different Fate**: shorter and closer to the manuscript.
3. **The Model Changed. So Did the Result.**: foregrounds the transfer question.

These are editorial options only. No paper title change is made.

## Voice sources

Read the six PDFs supplied by the author under `/Users/spiderishi/Desktop/Writing Samples/`, using Poppler text extraction for style rather than claims about page layout. No PDF was changed.

- `Work Of Fiction.pdf`: personal hook, direct conversational explanation, a concrete memory or example, self-deprecating asides and a progression from initial impression to revised understanding. The draft follows that narrative progression without borrowing the autobiographical details.
- `Meaning of Life.pdf`: first-person uncertainty, everyday analogies and an understanding that becomes less simple after more learning.
- `TOK Essay.pdf`: define the distinction before drawing a conclusion; move from an example to what it permits us to explain. The post keeps this reasoning pattern in a more conversational register.
- `My speech.pdf`: direct transitions and questions. Its polemical tone and unsupported historical claims are not imported into the research post.
- `Descriptive Writing .pdf`: varied sentence rhythm and a concrete scene. Fictional intensity is not imported into scientific conclusions.
- `Perspepolis Analysis.pdf`: inspected as mixed notes and quoted material, not treated as a uniform sample of author-written prose or as factual support for this post.

Also read `/Users/spiderishi/Coding/attribution/writing/substack/tone-guide.md`, the 28 September research diary saved in the Side worktree as `writing/substack/2026-09-26-how-much-can-one-learning-moment-change-an-ai.md`, and the opening of `/Users/spiderishi/Coding/attribution/writing/substack/2026-10-06-first-make-sure-a-fix-can-work.md`.

Editorial choices: I for judgment, we for completed work; British spelling; an ordinary customer-support example; natural contractions; sparse links; no em dashes; no invented personal episode; no claim of being first. The samples are tone evidence, not instructions or permission to take external actions.

## Evidence roots

- **W**: `/Users/spiderishi/Coding/attribution/.claude/worktrees/peaceful-jepsen-8b8eee`.
- **M**: `/Users/spiderishi/Coding/attribution`.
- **Current paper**: W `writing/side-notes/arxiv/main.tex`; W `writing/side-notes/arr/main.tex` was also checked for consistency of setup and release scope.
- **Latest state**: newest sections of M `.ai/HANDOFF.md`; W `research/side-notes/2026-10-13-appendix-audit.md`, `appendix-checks-20261013.json` and `2026-10-13-writing-priority-review.md`.

## Claim checks

1. **How the side project began.** Existing author draft supplies the narrative. Research framing comes from the current paper Introduction and practical takeaway. The opening’s first failed attempts are qualitative historical context, not the current six-model, one-pass comparison. The larger attribution/repair study remains a separate, unresolved question.

2. **Benign fine-tuning can weaken safety.** Opened on this turn: `https://arxiv.org/abs/2310.03693`, title *Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!*, Xiangyu Qi et al. The abstract explicitly reports degradation from benign commonly used datasets. The draft’s claim is limited to that result. Link is followed by the full title and “Qi et al.” in square brackets, per the author’s instruction. No other external-paper claim or link is added.

3. **Illustrative customer-support scenario.** The delivery/return example is invented only to explain ordinary fine-tuning. It is not presented as an experiment, observed deployment incident or documented failure. The 5% to 25%, 20-percentage-point example is arithmetic, not an experimental result.

4. **Data, models and replication.** Current paper Setup and Tables `tab:family`, `tab:recipe`: 4,800 Dolly training rows; one epoch; LoRA; six instruct checkpoints: OLMo-2-1B/7B, Llama-3.2-1B/Llama-3.1-8B, Qwen2.5-1.5B/7B. Each main Constant/Scheduled cell has three training seeds. Rank and half-LR variants have varying seed counts and are not described as three-seed cells in this post.

5. **Evaluation and definitions.** Setup: 200 development harm prompts, three sampled answers each, hence 600 sampled answers per evaluated unit. Erosion is fine-tuned minus untuned Qwen3Guard Unsafe share, in percentage points. Prompt samples are dependent within a prompt; training seeds replicate training. A guard label is not a deployment harm rate. The larger study’s sealed tests remain unused here.

6. **Current small-model Constant means.** `tab:family`: OLMo untuned 3.2%, fine-tuned 48.3%; Qwen-1.5B 4.7% to 76.6%; Llama-1B 13.8% to 73.1%. Draft rounds these to 3→48, 5→77 and 14→73, each with three runs. These replace the older one-run values in the original browser draft.

7. **Recipe comparison at small sizes.** `tab:recipe`: OLMo +45.1→+28.8 pp; Llama +59.3→+57.1; Qwen +71.9→+73.9. Three seeds per cell. `tab:tests` and recipe section: both OLMo family-interaction intervals exclude zero on Qwen3Guard and HarmBench. This is support within the observed development setting, not a universal family effect.

8. **Benign refusal trade-off.** `tab:recipe` and recipe section: OLMo Constant 4.7%, Scheduled 16.3%, untuned 17%. Scheduled minus Constant is 11.666… pp, rounded to 11.7. Draft rounds the rates to about 5% and 16%. It does not claim Scheduled increases refusal relative to the untuned model or that all its reduction in Unsafe share is caused by over-refusal.

9. **Blind read.** Current paper “What we screened, and limits” and blind-read appendix: one author, 50 selected answers; among 39 rated Unsafe-labelled answers, 34 went along and 13 were rated usable harmful help. Stratified selection and one reader limit population interpretation. Embedded HarmBench labels in this read include Mac/MPS float16 judgments; the main HarmBench erosion results used A100. The post does not pool these counts or treat the human usable-help threshold as the automatic HarmBench threshold.

10. **Larger-model replication.** `tab:recipe` and transfer section: OLMo-7B +44.1→+50.3 pp; Llama-8B +60.7→+59.2. Three seeds in every Constant/Scheduled cell. Pre-registered OLMo-versus-Llama interaction is +0.334 with Qwen3Guard interval −0.49 to +1.16; HarmBench +0.284, −0.39 to +0.96. Both inconclusive. Opposite point estimates do not establish a size interaction, zero effect or a parameter-count explanation. More seed variability limits precision.

11. **Qwen-7B.** `tab:recipe`, `tab:tests`, transfer section: +78.1→+68.9 pp, three seeds each. Its interaction with OLMo clears zero narrowly on Qwen3Guard, not HarmBench. Tests share cells, and no multiplicity adjustment was made. Draft calls it a lead and does not present a robust reversal across both judges.

12. **Earlier weighting-only comparison.** Recipe section: OLMo-1B Constant/token-mean mean erosion +41.9 pp at three seeds, versus +45.1 Constant and +28.8 Scheduled. The draft says this earlier average reduction was smaller. It does not turn that historical contrast into the missing arm of the fresh controlled pilot or identify a unique share of the total effect.

13. **Completed component pilot.** M `research/side-notes/causal-study-20261012/{RESULTS.md,analysis.json,completion.json,result-review.md}`; current paper `app:components`/`tab:components`. Fresh seed 1121, all six A/C/D units complete and backed up. Within each fixed OLMo checkpoint, initialization, actual row order, optimizer reset and evaluation were controlled. A is constant 1e-4 with example-mean loss; C adds the scheduled rates, applied mean 5e-5, holding loss weighting fixed; D adds token-mean loss under that schedule. This is a conditional intervention on recipes, not a causal parameter-count study.

14. **Pilot percentages and side effects.** Unsafe counts 1B A/C/D = 301/229/178 of 600, rounded to 50.2/38.2/29.7%; 7B = 242/287/304, rounded to 40.3/47.8/50.7%. These are after-training Unsafe shares, not historical erosion means. 1B C benign refusal 3/100, D 19/100; ARC 85/189 versus 74/189. No population interval or p-value is claimed. The schedule changes timing and mean learning rate together; missing token-mean/constant-rate arm limits decomposition. Neither query likelihood nor the saved ARC result certifies broad utility.

15. **Incomplete follow-up.** M `research/side-notes/causal-followup-20261012/incident-20261013/{STATUS.md,status.json}`: seed 1122 ended incomplete, no locally verified complete paired contrast and no validated activation intervention. Remote receipt for one 7B unit does not supply a local verified result. This is an infrastructure/collection failure, not replication failure or a scientific null. No stale account snapshot is represented as a live GPU claim in the post.

16. **Representation probes.** Current paper mechanism section and `tab:direction`: 20 of 24 planned fine-tuned artifacts recovered; four missing. Upper-half fixed-direction retained separation is greater for Scheduled OLMo-1B in the available cells. The direction is built from differences between harmful/harmless prompt group means, which may reflect content/task differences. Association only; no mediator validation or direct intervention outcome exists. Twenty artifacts do not mean twenty independent studies.

17. **Fiction experiment.** `tab:fiction` and fiction section/appendix: three seeds each; Constant recipe; screened dark and light public-domain fiction with matched format and length distribution. Mean Qwen3Guard erosion dark +11.7, light +16.6, Dolly +45.1 pp. Dark−light 90% intervals fall within the pre-set ±15.8 pp Qwen3Guard and ±10.6 pp HarmBench margins. These are wide margins, not equality or a general content-invariance claim. Dark/light benign refusal 30.7/24.0%, versus untuned 17 and Dolly 4.7; ARC 27.7/33.7%, versus untuned 39.2 and Dolly 46.7. Lower erosion is not established as useful safety preservation.

18. **Screening and scope.** Current paper screening/claim-status sections disclose choices made after initial results and distinguish later pre-registered tests. Draft states this distinction without presenting all historical screens as prospective. All outcomes remain development evidence; a claim confirmed on untouched external prompts is not made.

19. **Publication and AI assistance.** Current paper and latest handoff: local manuscript and numerical/configuration supplements prepared; no verified ARR submission, acceptance, arXiv upload or public repository release. The post claims only a write-up in preparation and reserves its public link. Claude and GPT/Codex used for implementation, design, checks and drafting; author makes decisions and owns claims. This remains a draft for author review. The song is left for the author to select.

## Initial text-only draft verification

- The existing Substack body was unchanged while the continuation was prepared. The browser body was then updated and verified against all 32 prepared paragraph/list blocks; their text matched exactly.
- The editor displays **Saved**. Title remains **A Recipe for Disaster (sometimes)**. The subtitle now describes six chat models and the recipe question.
- Both links remain present: the previous author post and the opened Qi et al. paper. The linked paper is followed by its title and author attribution in square brackets.
- The local Markdown body has 1,743 whitespace-delimited words (1,775 including title and subtitle), with links counted by their anchor text. No em dash is present.
- Every quoted main-result decimal was checked against the current manuscript; all six pilot percentages were checked against the verified Unsafe counts divided by 600.
- Screenshot of the saved editor: `tmp/substack-20261013/draft-saved.jpg`. The original body remains in the HTML backup. The song remains unselected.
- This is an author-review draft. No Publish/Continue action, paper submission, paid model call, GPU operation or repository-visibility change was performed.

## Review before publication

- Check the author’s intended voice against the current browser draft. No autobiographical detail from the private writing samples is inserted.
- Keep every linked paper’s title and author attribution immediately after its link, in square brackets.
- Check subtitle and the boundary between historical erosion means and fresh-pilot raw Unsafe shares.
- Add the author’s song and a real preprint link only after one exists.
- Publication requires the user’s explicit instruction. Editing a saved draft is not publication.

## Formatted revision with figures

The author requested figures and a more readable layout. Added seven narrative section headings, one pull quote, three embedded charts and italic figure captions. The existing title, opening and scientific body text remain intact. The current browser’s complete non-image text blocks match the prepared formatted text, with all three images loaded, descriptive alt text present and no leftover insertion markers or stray punctuation blocks. The editor displays Saved. Screenshot: `tmp/substack-20261013/formatted-draft.jpg`.

The figures use the Matplotlib skill and saved development data, with no generative-image/model call or new experiment:

- `figures/same-recipe-20261013/01-six-models.png`: Qwen3Guard erosion, Constant and Scheduled, six checkpoints, three training seeds per cell. Means computed from `research/side-notes/explore-20261011/units.csv` and checked against all twelve current manuscript means. The 36 individual seed values are plotted as dots; they are not confidence intervals.
- `figures/same-recipe-20261013/02-component-pilot.png`: completed seed-1121 pilot, raw Unsafe shares and benign refusal rates from each unit’s `outcomes` in `research/side-notes/causal-study-20261012/analysis.json`. One training seed at each fixed checkpoint, with ordered recipe conditions; no population interval, size-law or mediation claim.
- `figures/same-recipe-20261013/03-fiction-tradeoff.png`: means of erosion and benign refusal from `research/side-fiction/results/fiction-results.json`, three seeds per training arm. The dashed line is the 17% untuned benign refusal rate from the manuscript. Dark–light margins remain wide; this chart does not establish equality or explain the cause of the lower erosion.

`make_figures.py` preserves the plotting procedure; `figure-data.json` records every plotted value. SVG versions are also retained. All three exported charts were visually inspected and repaired for overlapping labels before insertion. Both table-to-plot means and pilot count-to-percentage conversions were checked. No manuscript, pinned engine or shared handoff was edited.

The extension file-chooser helper initially refused file access. The documented clipboard image-paste flow completed the uploads, followed by normal HTML pasting of the observed hosted image URLs to place the charts cleanly between paragraphs. No extension permission or security setting was changed. The original browser draft and the pre-formatting body remain backed up. No publication action was performed.
