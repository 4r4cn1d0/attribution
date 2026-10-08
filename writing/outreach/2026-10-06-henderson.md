# Outreach draft: Peter Henderson (merged email for Qi et al. 2023 and He et al. 2024)

**DRAFT. Not sent. The user sends it personally, after the Stage 0 slot is filled.**

- **To:** Peter Henderson <peter.henderson@princeton.edu>
- **Contact source:** printed on the front page of He, Xia and Henderson, arXiv [2404.01099v2](https://arxiv.org/pdf/2404.01099) (COLM 2024). Checked 6 Oct 2026.
- **Note on his preferred route:** his homepage, <https://www.peterhenderson.co/> (checked 6 Oct 2026), gives no email address. It asks for collaboration and visit requests through a form, and says that he gets many emails. If you prefer that route, paste the body below into his form yourself. (The agent did not open or fill the form.) Do not use the Stanford address on Qi et al. v1; it is out of date.
- **Status:** needs the Stage 0 result.

**Subject:** Benign fine-tuning erosion at 1.5B with LoRA: from one source, or spread out?

---

Dear Professor Henderson,

I am an independent researcher in the US. I study which data fix best repairs LLM safety after benign fine-tuning, and when diagnosis is worth its compute. Qi et al. (2023) and He et al. (2024) define the setting that I start from.

My first check is a single-seed development result: [STAGE 0 RESULT: X% of sampled answers were unsafe for the untouched Qwen2.5-1.5B-Instruct, and Y% after one LoRA fine-tune on Dolly-15k (seed 1101); a change of E = Z percentage points. Qwen3Guard labels on 200 harm prompts.] More seeds are planned.

My question: at this small scale, is the erosion usually stable across seeds, and does it come from particular data sources or from the whole dataset? If one source carries it, would you expect bi-anchored representation matching or gradient matching to find that source better?

Even a one-line answer would help. No reply is needed if you are busy.

Best regards,
[YOUR NAME]
Independent researcher
[LINK TO PUBLIC POST OR REPO, if you choose to share]

---

## Notes for the sender (not part of the email)

- **Why one merged email:** Henderson is the only author on both papers, and his homepage warns about email volume. Two emails to him would be spam. The merged question has two linked parts (size and localization; then which signal finds the source). This is a deliberate exception to "one question". The alternative is two separate emails to the first authors; their contacts are in the README.
- **How to fill the slot:** use the numbers from the Stage 0 run record, not from memory. Check the row count of the Dolly mixture (the Stage 0 brief says 4,800 rows: 600 from each of 8 categories) if you want to state it.
- **If E is below 3 pp (the futility rule):** replace the question paragraph with: "My question: would you expect so little erosion at 1.5B with LoRA? In your experience, which change makes erosion appear most reliably: a higher learning rate, full fine-tuning, or a larger model?" This asks about the same topic without a false premise.
- **If E is negative:** say so plainly. Do not round it to zero.
- **Words in the body** (greeting to closing line, with the slot as written): about 155.
- **Claim checks:** no numbers from their papers are quoted. Do not add the He et al. seed SD or the Qi et al. rates unless you have checked them in the PDF.
