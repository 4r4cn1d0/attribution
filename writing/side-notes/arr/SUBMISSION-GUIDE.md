# ARR October 2026 submission: what to upload and how

Written 10 Oct 2026 by the Side Project chat; updated 11 Oct 2026 for version 2 and the completed GPT correction pass (three seeds in every main Constant/Scheduled cell, the pre-registered transfer tests of Section 5, the exploratory Section 7; see CHANGES-2026-10-11.md). The ARR PDF is ready; submission needs your own OpenReview account.

## Deadline
**12 Oct 2026, 23:59 AoE** = **Tue 13 Oct, 17:29 India time** = 07:59 US Eastern = 11:59 UTC. Submit by Monday evening to leave room for upload problems.

## What to upload
- **PDF:** `writing/side-notes/arr/main.pdf` (20 pages, rebuilt 11 Oct 2026). This is the ACL template in review mode (anonymous, line numbers). The main content (Sections 1–11, through the Conclusion) ends on page 8, inside the 8-page limit. Limitations, Ethical considerations, the references and appendices A–G follow (A per-seed tables, B settings and hashes, C artifacts, licences and the blind read, D the fiction study, E details of Sections 6 and 7 with Figures 3–4 and the refusal-direction table, F claim status, G the screening log, the Qwen2.5-1.5B recipe screens and the judge-wording rule applied to every cell).
- **Supplementary material:** none. The paper says the code and data come with the final version, which keeps it anonymous. The release repository stays private.

## Before you submit
1. **OpenReview profile (required for every author since October 2026).** Complete it with your ORCID, affiliation history ("Independent researcher" is fine), emails and conflicts of interest. DBLP and ACL Anthology links are needed only with a prior publication record. The form says the profile must be complete by the 8th day after the deadline, or the paper is desk-rejected.
2. **Service contributor.** ARR reviews a paper for sure only if it brings a qualified reviewer. You don't meet the bar (2–3 papers at ACL, EMNLP, NAACL or COLING, or ICLR, ICML or NeurIPS, or 10+ completed reviews), so the paper enters a **lottery and may be desk-rejected without review**. You chose to accept that risk. If a collaborator who qualifies and knows the paper agrees, register them within 48 hours after the deadline.

## Form fields
- **Title:** Same Recipe, Different Fate: The Training Recipe's Effect on Safety Erosion from Benign Fine-Tuning Depends on the Model Family
- **Paper type:** long paper.
- **Research Area:** Language Modeling. Its keyword list (aclrollingreview.org/areas, read 11 Oct) names both "fine-tuning" and "safety". Second choice: Ethics, Bias, and Fairness ("model alignment").
- **Research Area Keywords:** fine-tuning, safety
- **Contribution Types:** Model analysis & interpretability.
- **Languages Studied:** English (en).
- **Previous URL, Explanation of revisions, Justification fields:** leave empty. Not a resubmission.
- **Reassignment Request Area Chair / Reviewers:** "This is not a resubmission".
- **Software / Data:** none. The paper says that the code and data come with the final version.
- **Preprint (ARR anonymous pre-print):** no. You plan your own non-anonymous arXiv version.
- **Preferred Venue:** COLING. This is not binding.
- **Visa Needs / Country Of Origin:** answer from your own passport and the venue's host country.
- **Consent To Share Data:** your choice. It covers anonymized scores and IDs only.
- **Consent To Share Submission Details:** tick it (required).
- **Author Submission Checklist:** yes. This promises the Responsible NLP checklist (a separate task in the author console after you submit) within 48 h after the deadline. The answers are below.
- **Blind Submission License Agreement:** "On behalf of all authors, I agree". **License:** CC BY 4.0 (fixed).
- **Keywords:** LLM safety; benign fine-tuning; safety erosion; refusal; LoRA; training recipe; model family; evaluation.
- **TL;DR:** A Scheduled recipe lowers OLMo-1B's mean safety erosion but raises over-refusal; its family interactions hold on two judges, while the 7–8B replication is inconclusive and the Qwen-7B interaction is judge-dependent.
- **Abstract (plain text):**

  Benign fine-tuning can erode safety, but reported effects vary widely. We compare six instruct models from OLMo-2, Llama-3 and Qwen2.5, at about 1B and at 7–8B, using LoRA on 4,800 Dolly rows with three seeds per main recipe cell. Erosion E is the rise in Qwen3Guard's Unsafe share of 600 sampled answers to 200 development harm prompts; HarmBench is a second judge. At 1B, a Scheduled recipe (warmup, cosine decay and token-mean loss) lowers OLMo-2-1B's mean erosion from +45.1 to +28.8 pp, compared with +59.3 to +57.1 for Llama-3.2-1B and +71.9 to +73.9 for Qwen2.5-1.5B. Both OLMo family-interaction intervals exclude zero on both judges, but OLMo's over-refusal rises by 11.7 pp. The pre-registered OLMo-versus-Llama replication at 7–8B is inconclusive. Qwen2.5-7B's mean erosion falls from +78.1 to +68.9 pp; its interaction with OLMo excludes zero on Qwen3Guard only. Halving the learning rate lowers mean erosion in OLMo-7B and Llama-8B, without establishing equal effects. Under one recipe, OLMo erodes least and Qwen most at both sizes. Dark–light fiction differences lie within wide pre-registered margins. A blind human read suggests the Unsafe label mostly tracks lost refusal. All results are development evidence; we report every screened setting and the judges' limits.

- **Preprint Status:** pick "We plan to release a non-anonymous preprint in the next two months". If the arXiv endorsement is still uncertain, pick "We are considering releasing...". Never pick "There is no non-anonymous preprint and we do not intend to release one": it is binding. Leave **Existing Preprints** empty until the arXiv version is public.
- **Target venue:** none at submission. At commitment (by **23 Dec**, after the reviews), choose COLING 2027 (B) or NAACL 2027 (A), or don't commit.

## Responsible NLP checklist (wrong or missing answers can cause desk rejection)
Every "Yes" needs a section; every "No" needs a reason. Section numbers refer to `main.pdf`.

| Q | Answer | Where / why |
|---|---|---|
| A1 Limitations | Yes | "Limitations" (after Section 11) |
| A2 Risks | Yes | "Ethical considerations" |
| B1 Cite artifact creators | Yes | Section 2 (Models, Data, Evaluation, Judges), Appendix C and Appendix D (the 16 Project Gutenberg books, by title and number) |
| B2 Licences | Yes | Appendix C ("Artifacts and licences") |
| B3 Intended use | Yes | Appendix C and "Ethical considerations": research use consistent with each licence; benchmarks for evaluation only |
| B4 Personal information | No | We used public datasets as released and collected no data from people. Dolly-15k was written by Databricks employees for public release. We did not screen it for names. |
| B5 Documentation | Yes | Section 2 and Appendices B, C and D (English; instruction data; the fiction rows' construction and safety screen; harm, over-refusal and ARC prompts) |
| B6 Statistics | Yes | Section 2: 4,800 training rows, 200 held-out task rows, 200 harm prompts × 3 samples plus 1 greedy answer, 100 over-refusal prompts, 189 ARC questions; Appendix D: two fiction arms of 5,000 rows each (4,800 for training), 8 books per arm |
| C1 Parameters, budget, infrastructure | Yes | Section 2 and Appendix B (Table 6: trainable parameters for all six models, the "Compute" row: one A100 80 GB per run, about 1–3.5 h per 1B run, 3.6 h for Qwen2.5-7B) |
| C2 Setup and hyperparameters | Yes | Section 2 (Recipes) and Table 6. There was no hyperparameter search beyond the screened settings listed in Appendix G. |
| C3 Descriptive statistics | Yes | Sections 3–8 and Tables 1–3 (seeds, sample SDs, clustered SEs, the Welch intervals of the 1B test and of the six pre-registered tests on both judges, the fiction study's pooled-SD t intervals); every seed in Appendix A |
| C4 Packages and settings | Yes | Section 2 and Table 6 (PyTorch, Hugging Face Transformers, PEFT); Table 7 (model and judge revisions, engine identities, the hashed test script) |
| D1 Instructions to annotators | Yes | Appendix C ("Blind-read rubric"): the full rubric and flags |
| D2 Recruitment and pay | No | One author rated the answers. No participants were recruited or paid. |
| D3 Consent | No | No data from people was collected; the only annotator is an author. |
| D4 Ethics board | No | No human participants beyond an author rating model outputs, so no review was sought. "Ethical considerations" notes the exposure to harmful text. |
| D5 Annotator demographics | No | A single annotator, who is an author. Group demographics do not apply. |
| E1 AI assistants | Yes | "Ethical considerations", paragraph "Use of AI assistants" |

## What was checked before upload
- Anonymity: the PDF metadata has no author or title fields, and the page shows "Anonymous ACL submission". The text has no name, username, repository link or email.
- The template is the official acl-org/acl-style-files at commit d5adc823, unmodified (its files match GitHub's blob hashes).
- The PDF builds with no undefined references or citations and no overfull boxes (rebuilt 11 Oct 2026 from `make_arr.py`; the Conclusion ends on page 8). The local upstream `lineno` v5.9 dependency fixes overlapping review line numbers; see `BUILD.md` for the pinned source and repeat compilation steps.
- Limitations introduces no new experiment; it states the scope, uncertainty and disclosure limits of the reported analyses.
- The pre-registration files, test maps and raw outputs named in Section 5 live in `research/side-notes/` on this branch; they are not uploaded (the paper says the release comes with the final version).

## After submission
- Within 48 hours: the service-contributor registration (see above).
- Within 1 week: a complete OpenReview profile.
- Reviews arrive before the 23 Dec commitment deadline. Then decide whether to commit to COLING or NAACL. Keep the main study's venue in mind: an archival note limits TMLR for the main paper.
- Before posting the arXiv version (`writing/side-notes/arxiv/`), fill its author name, affiliation and email placeholders and refresh the code/data release for version 2. The existing release builder inventories an earlier 28-unit draft and four model entries, rather than all six models in this paper. The refreshed source archive compiles, but this correction pass does not certify the separate code/data release. Repository publication remains a separate author action.
