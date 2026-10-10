# ARR October 2026 submission: what to upload and how

Written 10 Oct 2026 by the Side Project chat. The paper is ready; the remaining steps need your own OpenReview account.

## Deadline
**12 Oct 2026, 23:59 AoE** = **Tue 13 Oct, 17:29 India time** = 07:59 US Eastern = 11:59 UTC. Submit by Monday evening to leave room for upload problems.

## What to upload
- **PDF:** `writing/side-notes/arr/main.pdf`. This is the ACL template in review mode (anonymous, line numbers). The main content ends on page 8, inside the 8-page limit. Limitations, Ethical considerations, the references and appendices A–F follow (A per-seed tables, B settings and hashes, C artifacts, licences and the blind-read rubric, D the fiction study, E claim status, F the screening log).
- **Supplementary material:** none. The paper says the code and data come with the final version, which keeps it anonymous. The release repository stays private.

## Before you submit
1. **OpenReview profile (required for every author since October 2026).** Complete it with your ORCID, affiliation history ("Independent researcher" is fine), emails and conflicts of interest. It must be complete within one week after the deadline.
2. **Service contributor.** ARR reviews a paper for sure only if it brings a qualified reviewer. You don't meet the bar (2–3 papers at ACL, EMNLP, NAACL or COLING, or ICLR, ICML or NeurIPS, or 10+ completed reviews), so the paper enters a **lottery and may be desk-rejected without review**. You chose to accept that risk. If a collaborator who qualifies and knows the paper agrees, register them within 48 hours after the deadline.

## Form fields
- **Title:** Same Recipe, Different Fate: Safety Erosion from Benign Fine-Tuning Depends on Model Family and Training Recipe at 1B
- **Paper type:** long paper.
- **Area:** Ethics, Bias, and Fairness. Second choice: Interpretability and Analysis of Models for NLP.
- **Keywords:** LLM safety; benign fine-tuning; safety erosion; refusal; LoRA; training recipe; model family; evaluation.
- **TL;DR:** The same learning-rate schedule cuts benign-fine-tuning safety erosion by a third in OLMo-2-1B but barely moves Llama-3.2-1B; the family-by-recipe interaction holds on two judges, and one recipe's erosion size depends on the family at 1B and 7–8B.
- **Abstract (plain text):**

  Fine-tuning an aligned model on benign data can erode its safety, and published sizes of this erosion differ widely. We show that the effect of a training recipe on this erosion depends on the model family. We fine-tune instruct models from three families with LoRA on 4,800 Dolly rows. We measure the erosion E as the rise in the Unsafe share of 600 sampled answers to 200 harm prompts (Qwen3Guard). A standard Scheduled recipe (warmup, cosine decay and a token-mean loss) cuts OLMo-2-1B's erosion from +45.1 to +28.8 pp, but barely moves Llama-3.2-1B's (+59.3 to +57.1 pp; three seeds each). This family-by-recipe interaction excludes zero on two judges, Qwen3Guard and HarmBench, although we wrote the exact test late and it rests on about 5 degrees of freedom. A recipe that changes only the loss weighting shows that the schedule causes most of OLMo's cut. Under the constant-rate recipe, OLMo's erosion is partial, while Qwen2.5's and Llama's are near saturation; first seeds at 7–8B keep this order. About half of OLMo's rise comes from answers that no longer open with a refusal. A blind human read found that only about a third of Unsafe-labelled answers gave usable help, so we report lost refusal. In a pre-registered test, dark fiction eroded no more than light fiction; both eroded less than Dolly but refused more benign prompts. We report every setting we screened and the judges' limits.

- **Preprint question:** choose the option that **allows a non-anonymous preprint**, because you plan to post the arXiv version. Do **not** pick "no non-anonymous preprint": that option binds you not to post until the meta-reviews are out, under penalty of desk rejection.
- **Target venue:** none at submission. At commitment (by **23 Dec**, after the reviews), choose COLING 2027 (B) or NAACL 2027 (A), or don't commit.

## Responsible NLP checklist (wrong or missing answers can cause desk rejection)
Every "Yes" needs a section; every "No" needs a reason. Section numbers refer to `main.pdf`.

| Q | Answer | Where / why |
|---|---|---|
| A1 Limitations | Yes | "Limitations" (after Section 9) |
| A2 Risks | Yes | "Ethical considerations" |
| B1 Cite artifact creators | Yes | Section 2 (Models, Data, Evaluation, Judges), Appendix C and Appendix D (the 16 Project Gutenberg books, by title and number) |
| B2 Licences | Yes | Appendix C ("Artifacts and licences") |
| B3 Intended use | Yes | Appendix C and "Ethical considerations": research use consistent with each licence; benchmarks for evaluation only |
| B4 Personal information | No | We used public datasets as released and collected no data from people. Dolly-15k was written by Databricks employees for public release. We did not screen it for names. |
| B5 Documentation | Yes | Section 2 and Appendices B, C and D (English; instruction data; the fiction rows' construction and safety screen; harm, over-refusal and ARC prompts) |
| B6 Statistics | Yes | Section 2: 4,800 training rows, 200 held-out task rows, 200 harm prompts × 3 samples plus 1 greedy answer, 100 over-refusal prompts, 189 ARC questions; Appendix D: two fiction arms of 5,000 rows each (4,800 for training), 8 books per arm |
| C1 Parameters, budget, infrastructure | Yes | Section 2 and Appendix B (Table 5: trainable parameters, model sizes, the "Compute" row: one A100 80 GB per run, about 1–3.5 h per 1B run, 3.6 h for 7B) |
| C2 Setup and hyperparameters | Yes | Section 2 (Recipes) and Table 5. There was no hyperparameter search beyond the screened settings listed in Appendix F. |
| C3 Descriptive statistics | Yes | Sections 3–7 and Tables 1–4 (seeds, sample SDs, clustered SEs, intervals, Welch tests, the fiction study's pooled-SD t intervals) |
| C4 Packages and settings | Yes | Section 2 and Table 5 (PyTorch, Hugging Face Transformers, PEFT); Table 6 (model and judge revisions) |
| D1 Instructions to annotators | Yes | Appendix C ("Blind-read rubric"): the full rubric and flags |
| D2 Recruitment and pay | No | One author rated the answers. No participants were recruited or paid. |
| D3 Consent | No | No data from people was collected; the only annotator is an author. |
| D4 Ethics board | No | No human participants beyond an author rating model outputs, so no review was sought. "Ethical considerations" notes the exposure to harmful text. |
| D5 Annotator demographics | No | A single annotator, who is an author. Group demographics do not apply. |
| E1 AI assistants | Yes | "Ethical considerations", paragraph "Use of AI assistants" |

## What was checked before upload
- Anonymity: the PDF metadata has no author or title fields, and the page shows "Anonymous ACL submission". The text has no name, username, repository link or email.
- The template is the official acl-org/acl-style-files at commit d5adc823, unmodified (its files match GitHub's blob hashes).
- The PDF builds with no undefined references or citations.
- Limitations adds no new results; every number in it appears earlier.

## After submission
- Within 48 hours: the service-contributor registration (see above).
- Within 1 week: a complete OpenReview profile.
- Reviews arrive before the 23 Dec commitment deadline. Then decide whether to commit to COLING or NAACL. Keep the main study's venue in mind: an archival note limits TMLR for the main paper.
- The arXiv version (`writing/side-notes/arxiv/`) may go up any time; it is non-anonymous and links the release repository, which becomes public then.
