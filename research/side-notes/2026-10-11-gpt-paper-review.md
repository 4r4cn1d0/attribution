# Side Project paper: GPT correction and artifact review, 11 October 2026

## Scope and routing

The user requested Side Project development in the current GPT chat. This pass
finishes the paper claims, ARR layout, submission guide and preprint source
archive from legacy author commit `22bb26e`, after the layout-only commit
`34d5ff7`. It does not finish the main attribution study or certify a public
code/data release.

The prescribed read-only Opus call requested `claude-opus-5-5` and max effort
without time/turn caps. Run `tmp/claude-handoffs/20261011T134107Z-b5eeb4bf/`
returned a weekly-limit error and no substantive review. Requested effort is
not proof of effective internal effort. The user explicitly authorized the
exception: **“Yes, finish with GPT.”** GPT applied the corrections directly in
the Side Project worktree. The project's default implementation route is unchanged.

Non-author native GPT reviewer Anscombe (`01a12b30-4886-7b80-9d98-8f960bd500f9`)
read the source, generator, guide and supplied frozen result records. It received
the shared artifacts, not a preferred first-pass verdict. Its first pass found
eight wording/disclosure issues; it accepted their resolutions on follow-up and
accepted the last targeted edits. GPT lead owned compilation, visual inspection
and integration. Neither model agreement nor this review supplies independent
experimental evidence. Opus acceptance is not claimed.

## Objections and disposition

| Objection | Correction and evidence boundary |
|---|---|
| Inconclusive 7–8B replication described as failed transfer/size effect | State the replication criterion was not met; the interval allows either sign. Different releases and point estimates do not establish a causal size law. |
| Half-LR “alike” and “every family” | Report lower means in the two tested families, OLMo-7B and Llama-8B. The interaction is inconclusive; Qwen half-LR was not tested. |
| Refusal direction treated as a validated mechanism | Name harmful–harmless separation an observational proxy; disclose content/task confounding and no causal direction intervention. Distinguish Llama-8B's probed seed decrease (10 pp) from the full-cell mean decrease (1.5 pp). |
| Within-family engine equality claimed | Disclose OLMo-1B Constant `55253874` versus variant `e49a978c`; describe bounded evaluation-path baseline-reuse validation, not identical training engines. Appendix identity pins are unchanged. |
| Preregistration implied all cells were unknown | State rules preceded new runs, with known or interim comparator cells. Retain the late-written 1B exact test and all original preregistration records. |
| Marginal judge ratio treated as a transition fraction | Report marginal erosion ratios; they do not identify joint refusal-to-harm transitions. Below the wording threshold does not mean no harmful compliance. |
| Fiction headline implied equality/no excess harm | Bound the result to the wide prespecified margins; retain signed differences and intervals. Weaker instruction following remains a competing explanation. |
| Ethics/AI disclosure lagged scope | Cover six models at 1–8B and screened fiction; disclose both Anthropic Claude and OpenAI GPT/Codex assistance without overstating assistant verification. |

Lead additions make OLMo-1B's 11.7 pp over-refusal increase visible, remove
residual “only OLMo”/“Qwen is the family that responds” headings, and describe
release as a future action. The reviewer checked the corrected logit-interaction
df range: frozen records span 2.6945–6.2032, summarized as approximately 2.7–6.2.
The guide and change notes now describe completed checks consistently.

## Acceptance evidence

- Numeric preservation: ten result/settings tables are byte-identical to
  `34d5ff7`. Frozen result JSON/CSV, analyses and preregistrations have no diff.
  Only interpretation/disclosure prose and the claim-status wording changed.
- The abstract is 198 words and matches arXiv source, generated ARR source and
  the guide after normalizing LaTeX math delimiters and dashes.
- Both formats compiled successfully with pdflatex, BibTeX and repeated
  pdflatex passes in fresh scratch directories. ARR has 20 total pages and
  8 main pages; Limitations starts on page 9. The preprint has 18 pages.
- Neither format has undefined references/citations or overfull boxes. ARR has
  no warnings. Preprint has one existing hyperref empty-anchor warning from
  the required ICML author-notice command at line 148.
- ARR author/title/subject metadata are empty. The first page is anonymous;
  identity scanning finds no author's username/path/email marker. All detected
  review line-number digits sit outside the body-column bounds; full-page
  appendix floats have no line numbers, as expected.
- All 38 rendered pages were visually inspected. Final-build-3 ARR images and
  all but preprint page 3 match final-build-2 byte for byte. The new page 3 was
  inspected separately after the future-release wording change.
- The nine-file preprint source archive was refreshed, clean-compiled and
  checked against the reviewed preprint: extracted PDF text is identical.
  Previous generated archives are preserved in the scratch evidence directory.
- Source hashes were checked before PDF integration; target PDFs and the
  bibliography still matched HEAD, so no concurrent artifact edits were replaced.

Detailed command logs and renders are in
`tmp/side-paper-takeover-20261011/final-build-3/`. Persistent source, PDF,
table and archive hashes are in `research/side-notes/paper-checks-20261011.json`.
No repository tests, experiment, judge launch, spend, pod deletion, submission
or publication was initiated during this correction pass.

## Scientific limits and author actions

The weakest inference is generalization from a few training seeds and development
prompts. A utility-reducing model could refuse more without becoming a better
safety repair; the fiction results and OLMo over-refusal illustrate that concern.
Held-out evaluation with matched utility constraints would address this practical
claim. A direction intervention with appropriate content controls would test the
mechanism interpretation. These are future study requirements, not measurements
made by this paper pass. Overlapping tests remain unadjusted for multiplicity.

The anonymous ARR PDF is ready for the author's account/profile/submission steps.
Preprint posting additionally needs actual author details and a version-2
code/data release: the existing builder still inventories an earlier 28-unit,
four-model draft. Its coverage is not certified by the source-archive build.
The representation summary remains at the saved 13 units; separate adapter
recovery does not change this frozen report. Publication and repository visibility
are separate author actions.
