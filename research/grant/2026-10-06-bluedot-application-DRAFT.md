**DRAFT for the user's review. Not submitted. First written 6 Oct 2026. Refreshed 9 Oct 2026, from 15:48 UTC (clock checked). Fact-check fixes applied 9 Oct 2026, from 16:22 UTC (clock checked).**

# BlueDot Rapid Grant application (draft): *Repairing Safety After Benign Fine-Tuning*

Refreshed by a Claude Code subagent at the lead's request. It replaces the 6 Oct text with the records of 7–9 Oct. This file is the only output. Nothing was submitted, nothing was spent, no account was used, no form was opened, and nothing was committed. No held-out data was read. No prompt, answer or anchor text was read.

**Before you submit, fill or replace every `[USER: …]`, `[OPTIONAL UPDATE: …]` and `UNVERIFIED` mark, resolve or delete each `[CITE-CHECK: …]` mark, and delete the `[source: …]` note.** The form-ready text is in §3. The budget needs one decision from you (§6.4).

### What changed since the 6 Oct draft

- **Results.** "Stage 0 is running now" and the empty result slots are gone. In their place: Gate A passed on OLMo-2-1B; the HarmBench classifier sees about two thirds of the erosion (harmful compliance as the HarmBench classifier defines it); Qwen and Llama saturate under the same recipe; recipe G is a "recipe only" fix; each family now trains at its own learning rate. The Qwen runs are development evidence only.
- **Models.** OLMo-2-1B-Instruct is the main model. Llama-3.2-1B-Instruct is the second family, at its own learning rate. Qwen is out of the repair study. Recipe B is the main recipe; recipe G is a reference.
- **Design.** The measured repair comparison (six repairs, four labels), five references that change no data, Gate B as the next step, and the dataset plan (Dolly; PKU-SafeRLHF; Alpaca after Gate B).
- **Budget.** Unit costs re-derived at the A100's current $1.79/h. The research items now total $3,160. The ask stays $6,000 (your choice of 6 Oct), with a `[USER: …]` row for the $2,840 difference and a one-line recommendation (§6.4).
- **Venue.** NeurIPS 2027 or TMLR. ICML 2027 only if the positive control, both 1B families and one 7–8B replication are funded by about 1 December (FOCUS, 8 Oct 13:53 UTC).
- **§1** re-checked on bluedot.org on 9 Oct. The page is unchanged where the static text shows it. The form was not re-read.
- **Fact-check fixes (9 Oct, from 16:22 UTC).** Fields 13 and 15 use the defined harm wording. The blind read names its pooled groups and that its reader helped design the study. The two-layer account is marked observational. Recipe G's effect on Llama gives the HarmBench figure too. The per-family learning-rate rule says it was fixed after the ladder was read. Field 17 no longer says every rule came before the runs or that the budget is not a guess. Field 15 labels its own-run figures as development evidence. Fields 12 and 17 carry inline `[CITE-CHECK: …]` marks. The fallback ask is $3,200, so it covers the $3,160 of items. The engine test count is the 9 Oct one. Sources: FOCUS 8 Oct 20:50 UTC and 9 Oct 09:29, 13:45, 15:05 and 15:23 UTC; FOCUS 8 Oct 05:23 UTC (the audit corrections); the paper draft revision 5c (§1, §4.1, Appendix A); the results record, "HarmBench on the pod: the family contrast"; the 9 Oct commit 0e2299e message (as shown in the session's git snapshot; git was not run).

**Inputs read (repo, read-only):** the 6 Oct version of this draft; [FOCUS.md](../FOCUS.md) (Adopted direction; every dated entry of 7–9 Oct, especially 8 Oct 01:54, 05:23, 05:40, 10:14, 13:49/13:53, 17:07, 17:36, 18:31, 20:50, 23:28, 23:43; 9 Oct 01:43, 09:29, 09:40, 10:01, 10:07, 13:16, 13:45, 15:05, 15:23, 15:29, 15:31/15:35); the [results record](../experiments/2026-10-07-kill-test-stage0-results.md) (all sections); the [grant dossier](2026-10-05-grant-evidence-dossier.md) §§1a, 2, 3–3c, 5–8b (with the 9 Oct update), 11a, 11c, 12; the [paper specification](../review/2026-10-08-paper-specification.md); the paper draft `writing/paper/2026-10-08-icml-draft.md` (revision 5c: abstract, §1, §3.2, §4, §6, CITE-CHECK table, development evidence, references); the [sharpened-direction plan](../review/2026-10-08-sharpened-direction-DRAFT.md) §§1, 5.2, 8–14; the [Gate B DRAFT](../experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md) revision 4b (header, §12 item 4); the [Gate A audit](../review/2026-10-08-gate-a-audit.md) (verdict lines); `.ai/briefs/gate-b-engine-kit-reading-20261008.md` (the engine test count).

**Web pages opened on 9 Oct 2026, about 15:51–15:56 UTC (WebFetch; static page text only; bluedot.org only):**
- <https://bluedot.org/grants/rapid>, twice (content, then links and FAQ).
- <https://bluedot.org/grants>.
- Not opened: the Airtable application form (outside bluedot.org) and the rendered page in a browser. So the live counters and the form fields were not re-read (§1.1, §1.2).

---

## 1. What BlueDot asks (re-checked 9 Oct 2026)

### 1.1 The programme page

| Item | What the page says (paraphrased) | Changed since 6 Oct? |
|---|---|---|
| Amount | Up to $20,000 per grant. If you need more, contact BlueDot. | No |
| What it funds | Research and learning (time, living costs, research access); projects and experiments (compute, tools, testing an idea); events and community; travel and collaboration | No |
| What reviewers look for | A direction worth pursuing, evidence that you can make progress, and a clear role for the money. "Wildcards" are welcome. | No |
| Who | People taking a promising next step in AI safety or biosecurity. A grant is more likely for BlueDot course participants, alumni, facilitators and active community members. A course is **not** required. | No |
| Country limits | BlueDot cannot send money to 23 listed countries and territories, **India included**, or where sanctions apply. The United States is not listed. If unsure, contact BlueDot before applying. | No |
| Not funded | Party-political donations or campaigning; activities unlawful in the UK or your jurisdiction; work outside BlueDot's charitable or educational purposes | No |
| Process | Apply (plan and budget, about 15 minutes) → email decision → claim in the claims portal → one lump-sum payment after checks. Transfer and exchange fees can reduce the amount received. | No |
| Speed and volume (live counters) | The static text on 9 Oct shows "—" for every counter (they load in the browser). On 6 Oct the rendered page showed: average decision **4 days**; 9 in 10 hear back **within 13 days**; **938** grants; **$2,615,443** given. | **Not re-checked** |
| Apply link | The static text on 9 Oct has no Apply link. Its only call to action is "Start for free", a sign-up link that returns to the rapid-grant page. On 6 Oct the rendered page's "Apply now" opened a public Airtable form. | **UNVERIFIED:** whether applying now needs a BlueDot sign-in |
| After the grant | Use the money for the agreed purpose. Get prior written approval for a material change. Send a short completion report within 60 days of finishing the work or of the grant period ending. | No (the wording now names both end points) |
| Call status | The page states no deadline and no "closed" or "paused" notice. | No |
| Larger asks | Career Transition Grants (up to $200k, usually from $20k, about 45 minutes to apply) are for moving full-time into the field. Not this request. | No |

### 1.2 The application form (Airtable, "Rapid Grant Application")

**Read on 6 Oct; not re-read on 9 Oct** (it is on airtable.com, outside the pages this refresh could open). Field names are as shown on 6 Oct. Help texts are paraphrased. "Req" = required.

| # | Field | Req | Type and limits | Who fills it |
|---|---|---|---|---|
| 1 | Your name | yes | text | **user only** |
| 2 | Your email | yes | text. The form asks for the email used for BlueDot course messages and the Course Hub sign-in. | **user only** |
| 3 | Where are you based? | yes | text. The form says BlueDot cannot fund people based in Russia, China or India. | **user only** (see §9) |
| 4 | Where can we learn more about you? | yes | LinkedIn or a personal website preferred | **user only** |
| 5 | Grant type | yes | multi-select: *Compute & research tools*; *Events & community*; *Travel*; *Something else* | suggested: *Compute & research tools* |
| 6 | What are you working on? | yes | **200-character limit** | drafted (§3): 182 characters |
| 7 | Link to your work | yes | GitHub repo, demo, draft or other evidence; more than one link allowed | **user only** (options in §9) |
| 8 | If we approve your grant, can we share details about it publicly? | yes | *Can share publicly with my name* (pre-selected) / *without my name* / *Cannot share publicly* | **user only** |
| 9 | Public URL | no | one URL for BlueDot's website | **user only** |
| 10 | How are you connected to the BlueDot community? | yes | multi-select: *Course participant*; *Course alum*; *Facilitator*; *AI safety community member*; *Other* | **user only** (eligibility angle) |
| 11 | How much funding are you requesting? | yes | dollars, best estimate **to the nearest $50** | drafted: **$6,000** (your choice); read §6.4 first |
| 12 | Tell us more about your project. | yes | free text; no limit shown | drafted |
| 13 | What have you already done? | yes | concrete progress; no limit shown | drafted |
| 14 | What specifically would this grant fund? | yes | **each item with its estimated cost**; explain any stipend request | drafted; one row is **user only** |
| 15 | How does this reduce catastrophic risk from AI and/or contribute to AI going well for humanity? | yes | free text | drafted |
| 16 | What would you do without this grant? | yes | abandon, reduce scope, use slower or free options, or self-fund, and the impact | drafted; **user must confirm** |
| 17 | What makes you think this project will be successful? Why you? Why now? | yes | free text | drafted; "why you" is **user only** |
| 18 | Feedback | no | anything else to consider | **user only** (suggestion given) |
| 19 | Can we share your application with other funders and organizations as relevant? | no | *Yes* (pre-selected) | **user only** |

No limits were shown except field 6 (200 characters) and field 11 (nearest $50). The page says the form takes about 15 minutes, so the drafts below are short.

### 1.3 Where the dossier (§11a) is out of date

- The "about 5 working days" figure came from the **25 Nov 2025 blog post**. That post describes an older programme: course participants and facilitators only, most grants $50–1,500, no pay for the applicant's own time, and no general AI subscriptions (for example Claude Pro) unless "highly leveraged".
- The current page differs. No course is required. It funds time and living costs. The live average was 4 days on 6 Oct.
- **UNVERIFIED:** whether the old exclusion of general AI subscriptions still applies. The current page lists "tools" and says nothing on subscriptions (checked again on 9 Oct). This affects the AI-tools line (§6).

---

## 2. Three-sentence pitch

When a safety-tuned chat model is fine-tuned on ordinary, harmless data, it can stop refusing harmful requests: on OLMo-2-1B, one epoch on 4,800 Dolly rows raised the share of answers that a safety classifier labels unsafe from 3.2% to 47–51% over three seeds. The owner can repair this by removing rows, adding safety data, changing the training recipe or fixing the model after training, but repairs have side effects and have rarely been compared on equal terms. With repeated training seeds, rules fixed in advance and every GPU-second counted, we will measure which data repair restores the most safety for the compute spent without over-refusal or lost task skill, whether any data repair beats five repairs that change no data, and when paying for a diagnosis beats retraining.

---

## 3. Form-ready answers

Style: short sentences, active voice, simple words. All results are development evidence. **Fill or replace every `[USER: …]` and `[OPTIONAL UPDATE: …]`, and resolve or delete every `[CITE-CHECK: …]`, before submitting.**

### Fields 1–4, 7–10 and 19 (user only; never filled here)
- Field 1, your name: `[USER: your name]`
- Field 2, your email: `[USER: the email you use for BlueDot course messages and the Course Hub]`
- Field 3, where you are based: `[USER: answer truthfully; see §9 on the India rule]`
- Field 4, where to learn more about you: `[USER: LinkedIn or a personal website]`
- Field 7, link to your work: `[USER: your choice of links; options in §9: the Substack post, the anonymous artifact, the GitHub repo if it is public]`
- Field 8, public sharing: `[USER: choose; "with my name" is pre-selected]`
- Field 9, public URL: `[USER: optional]`
- Field 10, BlueDot connection: `[USER: choose from course participant, course alum, facilitator, AI safety community member, other]`
- Field 19, share with other funders: `[USER: choose; "Yes" is pre-selected]`

### Field 5. Grant type
*Compute & research tools.* Add *Something else* only if you keep a stipend row in field 14. The form has no "time" option, and how BlueDot maps a stipend to these options is **UNVERIFIED**. Add *Travel* only if you add travel.

### Field 6. What are you working on? (182 of 200 characters)
> Which data repair best restores an LLM's safety after benign fine-tuning, for the compute spent, without over-refusal or lost task skill? Seeded, pre-registered tests on open models.

### Field 11. How much funding are you requesting?
**$6,000.** Decided by the user on 6 Oct 2026 and kept here. The research items in field 14 now total $3,160. **Read §6.4 before you submit:** either fill the $2,840 row in field 14, or change this answer to $3,200 (the $3,160 of items, rounded up to the next $50).

### Field 12. Tell us more about your project.

**The problem.** Fine-tuning a safety-tuned chat model on ordinary, harmless data can make it stop refusing harmful requests. Qi et al. (ICLR 2024) report this after one epoch on Alpaca and Dolly. Fine-tuning services screen customer data and can block an unsafe model. Then they tell the customer to fix the data and resubmit. `[source: dossier §1a, Microsoft Foundry docs, read 6 Oct; re-check before submitting]` So the customer, who can often change only the data, must choose a repair.

**The repairs.** A data-only user can remove rows or add safety data. Other repairs change no data: a safety prompt at test time, a scaled-down adapter, a post-hoc projection of the adapter, a gentler training recipe, or a constrained training objective. Each repair can have side effects. It can make the model refuse harmless requests, or reduce its task skill. Published repairs were each tested in their own setting, mostly with one or a few training seeds, and seldom with their compute counted. `[CITE-CHECK: the paper draft marks this sentence as unchecked (§1); verify it, or delete 'and seldom with their compute counted', before submitting]`

**The questions.**
1. Which data repair restores the most safety for the compute spent, within limits on over-refusal and task skill?
2. Does any data repair beat the repairs that change no data?
3. Is the erosion caused by identifiable parts of the data? When does it pay to buy a diagnosis (training-data attribution, a representation filter, or a free answer-length rule) before choosing, instead of spending the same compute on trial runs?

**The design.**
- **Models and data.** Main model: OLMo-2-1B-Instruct, fine-tuned with LoRA for one epoch on 4,800 Dolly-15k rows (8 task categories × 600). Second family: Llama-3.2-1B-Instruct. Each family trains at its own learning rate, chosen from erosion probes only, so that both erode partly.
- **Six repairs, fixed in advance, six training seeds each.** Remove 600 rows ranked by training-data attribution, by a LARF-style representation filter, or by answer length. Add 48 refusal rows (1%) from PKU-SafeRLHF: drawn at random, selected in the DataRx style, or written by the untuned model itself. The comparators are random removal of 600 rows (8 seeds) and no repair (6 seeds).
- **Labels.** Each repair is *better*, *equivalent* (within ±5 percentage points), *worse* (significantly adverse on the unsafe rate, over-refusal or task loss) or *inconclusive*, after Holm correction. Over-refusal is measured against the untuned model.
- **Five references that change no data set the bar:** a safety prompt; the adapter scaled by 0.75 and 0.5; Safe LoRA (Hsu et al., NeurIPS 2024); recipe G (a standard warmup-and-cosine schedule); and the main recipe with the constrained objective of Qi et al. (ICLR 2025). A data repair counts as the winner only if it beats them.
- **Measures.** Refusal erosion as Qwen3Guard labels it: the share of 600 sampled answers to 200 harmful requests that it labels unsafe. Harmful compliance as the HarmBench classifier defines it. Also a second judge (Granite Guardian), over-refusal on 100 harmless prompts that look harmful, held-out task loss, and cost in GPU-seconds and full-run equivalents.
- **A positive control.** A known cause is planted in one cell of nested menus (8, 32 and 128 cells). We ask whether each diagnostic finds it, and at which menu size diagnosis beats trial runs.
- **Rules first.** In the repair study, every rule is committed before the data it judges. Training seeds replicate every result. Up to two contrasts per family are confirmed on fresh seeds and a sealed held-out prompt set. Results that are too close to call are reported as such.

**The next step: Gate B.** Gate B asks whether removing one Dolly category restores more safety than removing 600 random rows. Its verdict is LOCALIZED, DIFFUSE or TOO CLOSE. It detects an 8-point effect about half the time, and 80% of the time at about 10–12 points. If LOCALIZED, Gate C tests which diagnostic picks the category, with a format control. If DIFFUSE, the comparison runs unchanged, and the positive control becomes the only test of whether diagnosis can pay. Gate B is paid from the project's current compute balance, not from this grant. `[USER: confirm.]`

**Scale and data.** If funded: a reduced benchmark at 7–8B (OLMo-2-7B, Llama-3.1-8B), starting with a replication in a published setting (a LARF- or DataShield-style filter on Llama-3.1-8B-Instruct fine-tuned on Alpaca); then a headline check at 32B or 70B. Alpaca becomes the second benign dataset after Gate B.

**Target.** NeurIPS 2027 or TMLR. ICML 2027 (deadline about 22 Jan 2027; not official) only if the positive control, both 1B families and one 7–8B replication are funded by about 1 December. This grant funds exactly those.

### Field 13. What have you already done?

All results so far are development evidence. Nothing is confirmatory yet.

- **Gate A passed on OLMo-2-1B-Instruct (8 Oct).** One epoch of LoRA (recipe B) on 4,800 ordinary Dolly-15k rows raised the share of answers to 200 harmful requests that Qwen3Guard labels unsafe from 3.2% to 46.7%, 46.8% and 51.3% over three seeds. The mean erosion is +45.1 points (band 41.3–49.0). Answers still end, the task is learned, and a second judge (Granite Guardian) agrees on every seed. The three-seed reading was pre-registered before the two new seeds ran. An independent six-lens audit rated the result "sound with caveats": the label tracks lost refusal, five settings were screened first, and seed variance rests on three seeds.
- **Harmful compliance as the HarmBench classifier defines it also rose.** This classifier asks whether an answer carries out the request. We ran it on a rented A100 after a pre-set parity check against the local run (799 of 800 labels identical). It sees about two thirds of the erosion: +27.7, +30.5 and +32.8 points (mean +30.3). Every seed clears the 20-point line that we fixed in advance for this wording. In a blind human read during development (one reader, 50 answers), 34 of 39 judge-unsafe answers went along with the request. But only 13 of 39 (about a third) gave usable help. The 39 answers pool five model-and-recipe groups (12 are OLMo at recipe B), and the reader also helped design the study. The human check in field 14 extends this read.
- **The model family matters.** Under the same recipe B, Qwen2.5-1.5B (+75.2 points) and Qwen2.5-7B (+82.2; one seed each) saturate. Llama-3.2-1B reaches a mean of +59.3 over three seeds, at or above the 55-point edge. OLMo erodes only partly. Two layers fit this pattern (an observational account only). Fine-tuning cuts the share of answers that open with a refusal (by 0.51 on OLMo, 0.68 on Llama, 0.85 on Qwen). A family whose untuned direct answers were already often unsafe (Llama 0.64, Qwen 0.57, OLMo 0.18) then saturates, or nearly so.
- **A recipe change alone repairs part of it.** Recipe G changes no data. It adds a short warmup with cosine decay, and a token-mean loss. On OLMo it cut the erosion by 36% on Qwen3Guard (+45.1 to +28.8 points) and by 43% on HarmBench (+30.3 to +17.2). On one seed it kept over-refusal at the untuned level (17 of 100). It barely moved Llama (4–7% on Qwen3Guard, 12% on HarmBench). A pre-registered control (one seed) showed that the schedule, not the loss weighting, does this. Our prediction failed, and we report that.
- **Each family needs its own learning rate.** Under recipe G, halving the learning rate cut the erosion by the same fraction in both families (OLMo −28%, Llama −29%), but at different levels. No rate on that ladder left both families cleanly in the partial range. So each family now trains at the highest rate of a fixed ladder whose erosion probe reads partial (20–55 points), chosen from erosion probes only. We fixed this rule on 9 Oct, after reading that ladder and Llama's first recipe-B probe, and we disclose it. Llama's probe at recipe B with half the learning rate started on 9 Oct. `[OPTIONAL UPDATE: if FOCUS.md records this probe's reading before you submit, add one sentence with its erosion and class. Do not guess.]`
- **Qwen stays as development evidence only.** On Qwen2.5-1.5B-Instruct, the first setting (Stage 0) eroded almost completely (mean +81.8 points over three seeds) and failed Gate A by its frozen "answers end" rule. A gentler recipe and a smaller adapter still saturated it. So Qwen left the repair study.
- **Fixes have side effects (base-model pilot, 2 seeds).** With 507 injected unsafe rows, rewriting the classifier's top 507 rows cut sampled unsafe answers from 80.3% to 11.4%. But harmless XSTest prompts were refused 44 times in 100 (22 of 50 in each seed), against 1 in 100 before the fix.
- **The engine and records are built and tested.** More than 750 engine tests pass (759 passed and 3 skipped on 9 Oct), plus 172 selector and 260 durability tests. A two-step A100 check confirms bit-exact training. Data units and evaluation splits are sealed by hash. Backups are private and verified by download. A budget guard checks the balance before every launch.
- **Costs are measured.** A 1B training-and-evaluation pod costs about $2–2.5 at the current A100 price ($1.79/h). One arm's job takes 34–52 minutes ($1.01–1.55). HarmBench judging on a pod costs about $0.35 per 800 labels. The first cost ledger (2–5 Oct) covers 48 pods and $153.48, including $38.88 of failed or idle time.
- I published a short public post on early development results (6 Oct). `[USER: decide whether to link it; §9.]`

### Field 14. What specifically would this grant fund?

All figures are estimates built from measured unit costs (§6). GPU work runs on rented A100-80GB pods at $1.79/h. Each GPU line is the upper end of its estimate range and includes 20% for failed pods and re-runs.

| Item | Cost |
|---|---|
| Stage 1 on OLMo-2-1B: six repairs × six seeds, random removal (8 seeds), no repair (6 seeds), the diagnostics' scoring, and the five references that change no data | $162 |
| Positive control: a planted cause in nested menus of 8, 32 and 128 cells (a pilot first, then the sweep) | $47 |
| Secondary arms, run in a fixed order (a random dose curve, a DataShield-style filter, format and length rules) | $108 |
| Second family, Llama-3.2-1B at its own learning rate: Gate A, anchors, a reduced Gate B, the six repairs | $155 |
| Confirmation: up to two contrasts per family, six fresh seeds, a sealed held-out prompt set | $128 |
| 7–8B reduced benchmark (OLMo-2-7B, Llama-3.1-8B), starting with a replication in a published setting | $540 |
| Headline check at 32B (H200 GPU) or 70B (B300 GPU) | $720 |
| Human check of about 500 model answers (harm and refusal labels), to test the automatic judges | $400 |
| AI coding and research tools, to the end of January | $800 |
| Storage and verified backups | $100 |
| **Research items, total** | **$3,160** |
| `[USER: the remaining $2,840 of the $6,000 ask. Either a stipend for your time (the page funds time and living costs; say what it buys, for example how many weeks of full-time work), or delete this row and set field 11 and the total below to $3,200 (the $3,160 of items, rounded up to the next $50). See §6.4.]` | `[USER: $2,840, or delete]` |
| **Total requested** | **$6,000** |

Gate B (about $68–84 at the upper rates) is paid from the project's current compute balance, not from this grant. `[USER: confirm.]`

Spending is staged. Each stage starts only when it is funded, never because of an outcome. If an early gate stops or narrows the study, I will tell BlueDot and ask in writing how to use or return the unspent money.

`[USER: if you have filed, or will file, the separate compute request for GPU funds (dossier §8b; about $1,500 recommended there), say so here and in field 18, and say which GPU lines above it would cover. Do not ask two funders for the same GPU hours.]`

### Field 15. How does this reduce catastrophic risk from AI and/or contribute to AI going well for humanity?

Fine-tuning services let customers fine-tune aligned models on their own data. In our development runs, one epoch on harmless Dolly data changed a 1B model a lot. Its harmful compliance as the HarmBench classifier defines it rose by about 30 points over three seeds (development evidence; field 13 gives the human-read caveat). Often the person who must fix this can change only the data. Today that person has no tested rule for which repair to use.

A careless repair has costs. In our base-model pilot (development evidence, 2 seeds), the best fix removed most unsafe answers, but the model then refused 44 of 100 harmless requests. DataRx (arXiv 2608.04322) tested safety mixes on Llama3-8B-Instruct, averaged over seven tasks. A random 1% safety mix raised attack success from 20.24% (no safety data) to 59.23%. Its selected 1% mix lowered it to 13.70%. So the choice of repair matters, in both directions.

This project gives a measured comparison of data repairs, with their side effects and costs, on two open model families, with open code and frozen protocols. It also shows whether a data repair is needed at all: five repairs that change no data set the bar. A negative result is useful too. It tells people to spend compute on a default repair or on trial runs, not on diagnosis.

Limit: this is about everyday fine-tuning safety at small scale. It does not address catastrophic misuse directly.

### Field 16. What would you do without this grant?

`[USER: confirm or correct this draft. It states facts about your own funds and plans.]`

Without the grant, I would finish Gate B with the compute I have now. I could not fund stage 1 on two model families, the positive control and the 7–8B replication by about 1 December. The study would shrink to OLMo-2-1B, with fewer arms and seeds. It would aim at TMLR or NeurIPS 2027, not ICML 2027. Free GPU tiers do not fit: the engine checks exact training on one GPU type, and comparable costs need one kind of hardware.

### Field 17. What makes you think this project will be successful? Why you? Why now?

**Why it can succeed.** The hard parts exist and work (field 13). Gate A passed on the main model under a reading fixed before its new seeds ran, and an independent audit checked it. Three automatic judges and a blind human read show what the measure means. The 1B budget lines in field 14 are scaled from measured unit costs. The larger-model, human-check and tool lines are rougher estimates. In the repair study, every gate, label and stop rule is written down before the runs it judges. During development we fixed some rules after seeing data (the 20–55 point erosion window, a looser skill rule and the per-family learning rate), and we disclose each one. A null result is planned for and will be published.

**Why now.** Recent preprints show that the field is moving here. Guo et al. (arXiv 2609.01455) report that 100 random benign rows of full fine-tuning raise attack success sharply on recent 8B-class models. DataRx (arXiv 2608.04322) shows that the choice of safety data decides the outcome. SafeTune (arXiv 2609.22153) compares repairs of safety drift in single deterministic runs. DualSelect (arXiv 2606.09866) compares data-selection methods with three seeds and a false-refusal rate. `[CITE-CHECK: the SafeTune and DualSelect wording is not fully checked (§11 item 9); verify it before submitting]` We found no study that compares removal and addition repairs against model-level references, with training seeds, side effects and measured compute, in one design. We claim only this combination. Funding by about 1 December keeps an ICML 2027 submission possible.

**Why me.** `[USER: your background, relevant skills and any track record. Add a CV link if you want to.]`

### Field 18. Feedback (optional)
`[USER: list every other application you have actually sent or will send, including any compute request (the dossier §11c recommends disclosing all of them; §8b prepares a compute request for GPU funds). Optionally add a note on your location; see §9.]`

---

## 4. Evidence so far (development evidence only)

| Finding | Numbers | Source |
|---|---|---|
| **Gate A PASS, OLMo-2-0425-1B-Instruct, recipe B** (LoRA r64, LR 1e-4 constant, 128 rows per step, per-example loss, one epoch of 4,800 Dolly rows) | U (Qwen3Guard Unsafe share of 600 sampled answers): untuned 3.2%; seeds 46.7%, 46.8%, 51.3%. E +43.5, +43.7, +48.2 pp; mean +45.1 (band 41.3–49.0; partial); fresh-seed mean +45.9; mean E ≥ 2 × SD (SD 2.65); held-out task loss 2.100 → 1.54; Granite greedy E +44.0, +40.5, +44.5. Over-refusal 17/100 untuned, 4–6/100 after. Independent audit (six lenses): "sound with caveats" (U tracks refusal; five settings screened, and the 20–55 window fixed after the Qwen results; 2 df for seed variance). | FOCUS 8 Oct 05:23 and 05:40 UTC; results record, "Formal Gate A"; [Gate A audit](../review/2026-10-08-gate-a-audit.md) |
| **HarmBench compliance, recipe B** | On the pod (after a parity PASS: 200/200 greedy and 599/600 sampled labels identical): E_HB +27.7, +30.5, +32.8 pp, mean **+30.3** (Mac run: mean +30.4; on the Mac labels, agreement with Qwen3Guard 83–86%, κ 0.65–0.71). Every seed ≥ 20 pp and the same-sign, half-size rule holds, so the paper may say "harmful compliance as the HarmBench classifier defines it". | FOCUS 8 Oct 17:07, 23:28, 23:43 UTC; results record |
| **Blind human read** (pre-registered; ratings sealed before the key; one reader; report-only) | 50 answers. 39 Qwen3Guard-Unsafe answers rated: 34 went along (0.87 [0.73, 0.96]); 13 gave usable help (0.33 [0.19, 0.50]). Safe controls: 0 of 10 missed. On 15 OLMo items, 4 of 12 HarmBench "yes" answers were usable help. The 39 pool five model-and-recipe groups: OLMo recipe B 12, OLMo recipe G 6, Qwen2.5-1.5B 7, Qwen2.5-7B 6, Llama-3.2-1B 8. Limits: one reader, an author who helped design the study; small groups; no comparison between groups. The paper carries it once in its measurement section and once in its limitations, with the counts in an appendix (decision of 9 Oct 15:23 UTC). | FOCUS 9 Oct 15:05 and 15:23 UTC; paper draft revision 5c, Appendix A |
| **Same-recipe family contrast (recipe B)** | Qwen3Guard E: Qwen2.5-1.5B +75.2 (one seed); Qwen2.5-7B +82.2 (one seed); Llama-3.2-1B +62.5, +61.3, +54.0 (mean +59.3, saturated or at the top edge); OLMo +45.1. HarmBench E_HB on one device: Qwen-7B +63.5, Qwen-1.5B +46.0, Llama +40.5 (seed 1101), OLMo +30.3. Untuned U: OLMo 3.2%, Qwen-1.5B 4.7%, Llama 13.8%. | results record; FOCUS 9 Oct 13:45 UTC |
| **The two-layer account** (observational) | U ≈ P(no refusal opening) × P(unsafe given a direct answer). Refusal openings lost under recipe B: OLMo −0.51, Llama −0.68, Qwen −0.85. Unsafe share of untuned direct answers: OLMo 0.18, Qwen 0.57, Llama 0.64. OLMo's partial erosion is about half opening switch, half content. | FOCUS 9 Oct 13:45 UTC; mechanism note and addenda |
| **Recipe G = the "recipe only" fix** (4-step warmup with cosine decay, token-mean loss; no data change) | OLMo, three seeds: E +29.0, +31.0, +26.5 (mean +28.8; −36% of recipe B's E); E_HB +17.8, +19.3, +14.3 (mean +17.2; −43%), below the 20 pp line, so recipe G's erosion is only "refusal erosion as Qwen3Guard labels it". Over-refusal 17/100 at seed 1101 (recipe B 4/100). Llama: mean +57.1 over three seeds (4–7% below recipe B); E_HB 12% below recipe B (pod; recipe B one seed, recipe G two seeds). The token-mean-only control (E +43.7, like recipe B) puts the reduction on the schedule; its pre-registered prediction failed. | FOCUS 8 Oct 21:36 and 23:43 UTC; 9 Oct 09:29 UTC; results record (incl. "HarmBench on the pod: the family contrast") |
| **Learning-rate ladder (recipe G) and the per-family rule** | Rung 2 (LR 5e-5): OLMo +20.3, +21.3 (mean +20.8, TOO CLOSE at the low edge); Llama +41.2 (partial; one seed). Halving the LR cut E by 28% (OLMo) and 29% (Llama). No rung fits both. Rule since 9 Oct 09:29 UTC: each family uses recipe B with only its LR changed, at the highest rung of 1e-4, 5e-5, 2e-5 whose probe reads partial (20–55 pp), chosen from erosion probes only. Fixed after the ladder and Llama's recipe-B probe were read (disclosed; FOCUS 9 Oct 13:45 UTC). OLMo's rung is 1e-4. | FOCUS 9 Oct 01:43, 09:29, 13:45 UTC |
| **Llama, recipe B at LR 5e-5** (rung 2 at the main recipe) | Pre-registered 15:31 UTC, launched 15:35 UTC on 9 Oct. Prediction: E +35 to +50 pp (point +43). **No result in this draft.** | FOCUS 9 Oct 15:31 UTC |
| Family × recipe interaction (Side Project) | Logit scale −0.573 (95% CI −1.02 to −0.13). Development evidence, written after 11 of the 12 values were known. | FOCUS 9 Oct 13:45 UTC |
| **Qwen Stage 0 and follow-ups** (development only) | Qwen2.5-1.5B-Instruct, 3 epochs: mean E +81.8 pp over three seeds; Gate A FAIL on "answers end" (seed 1102 e3: 17.0% capped). Recipe B: +75.2 (one seed). Qwen2.5-7B: +82.2 (one seed). Rank 16: +67.8. Qwen left the candidates on 7 Oct (20:58 UTC). | results record; FOCUS 7 Oct |
| **v2: a large safety gain with a large over-refusal cost** | Qwen2.5-1.5B base, ToxicChat-Het plus 507 injected unsafe PKU-SafeRLHF rows; 2 seeds. Sampled unsafe: a0 80.3%, targeted rewrite 11.4%, random rewrite 81.6%. XSTest-safe refusals: a0 1/50 and 0/50; rewrite 22/50 and 22/50. Second judge 97.2% agreement. Classifier recall on injected rows 0.929. | [v2 results](../experiments/2026-10-06-headroom-v2-results.md) |
| **Round 1: a fixed-size top-K removal rule backfired** | Removing the classifier's top 1,015 rows (10%) raised unsafe answers from 12.5 to 24.0 of 72. **Wording rule:** a finding about a fixed-size top-K rule only; a threshold rule is untested. | [round-1 results](../experiments/2026-10-05-headroom-round-1-results.md); dossier §3 |
| **Engine and records** | Engine 759 passed, 3 skipped, at commit 0e2299e (9 Oct; 756 passed with 3 CUDA-only skips on 8 Oct); Stage B 172; durability 260. Bit-exact two-step A100 fixture; sealed units and splits; sealed Gate C anchor list (hashes only in git); verified private backups; budget guard. | commit 0e2299e message (9 Oct; the commit is named in FOCUS 9 Oct 15:31 UTC); `.ai/briefs/gate-b-engine-kit-reading-20261008.md`; dossier §§4–5; FOCUS 8 Oct 15:53 UTC |

---

## 5. Plan, milestones and gates

Basis: the sharpened-direction plan §§10–14 (dates are the plan's estimates; deadlines **UNVERIFIED**) and the FOCUS decisions of 8–9 Oct. Each stage starts on a funding event, never on an outcome. The lead stops and asks the user after every stage.

| When (estimate) | Milestone | Gate or stop rule | GPU at $1.79/h (upper) |
|---|---|---|---|
| Now (9 Oct) | Gate A done (OLMo). Llama's recipe-B probe at LR 5e-5 is running. | The per-family rule picks Llama's learning rate from probes only. | outside this grant |
| About 9–20 Oct | **Gate B** on OLMo-2-1B (recipe B; 8 category removals against random removal). Before its category runs, the stage-1 rules are committed by hash. | LOCALIZED / DIFFUSE / TOO CLOSE. LOCALIZED → Gate C and a length control. DIFFUSE → stage 1 unchanged; the positive control is the only test of diagnosis; the paper takes its fallback title. TOO CLOSE → an automatic two-seed extension. Starts only after the user accepts its pre-registration (DRAFT revision 5) and its kit is certified. | about $68–84; paid from the current balance |
| About 20 Oct–15 Nov | **Stage 1** (OLMo): seed blocks A and B; the five references. The positive control's pilot. | Blinded seed rule on Gate B's pooled noise: ≤ 4.5 pp, plan A; 4.5–6.0 pp, plan B (three contrasts at 9 seeds); > 6.0 pp, no stage 1, review. The pilot goes on only if the plant adds at least 10 points. | $162 + $47 |
| About 15 Nov–10 Dec | **Stage 2** (Llama-3.2-1B at its own learning rate): Gate A, anchors, a reduced Gate B, the six repairs. | Llama's Gate A must pass at its matched dose. If no rung reads partial, the paper is single-family and says so. | $155 |
| About 1 Dec | Venue check | ICML 2027 only if the positive control, both 1B families and one 7–8B replication are funded. | – |
| December | **Stage 3, confirmation:** up to two contrasts per family, chosen by a rule fixed before stage 1, at six fresh seeds, on the development bank and a sealed 200-prompt held-out set. Replay against the predictions. | A confirmatory null is reported, never retuned on the same data. | $128 |
| When funded (Nov–Jan) | **Scale:** a 7–8B reduced benchmark, starting with the published-setting replication; then a 32B or 70B headline check. | Before 32B or 70B: a small engine and kit round, and a cheap smoke test before any large spend. No claim at a size without runs at that size. | $540 + $720 |
| Optional, in order | Secondary arms (stage 1c) | Exploratory; one-sided bounds only. | $108 |
| After Gate B | Alpaca as the second benign dataset | First: the user extends the learning-rate rule to datasets; a design note fixes Alpaca's units and field mapping; the user approves the download. **Not yet costed** (§6.2). | – |
| January 2027 | Writing. ICML 2027 (about 22 Jan; **UNVERIFIED**) if the conditions hold; otherwise NeurIPS 2027 (about mid-May; **UNVERIFIED**) or TMLR. | – | – |

---

## 6. Budget

### 6.1 Measured unit costs, re-derived at the A100's current price ($1.79/h)

The A100-SXM4-80GB price rose from $1.59 to $1.79 per hour on 8 Oct (FOCUS 8 Oct 18:31 UTC). The budget guard plans new pods at $1.85/h; spend is counted at $1.79/h (FOCUS 9 Oct 13:16 and 15:29 UTC).

| Unit | Measured | At $1.79/h | Source |
|---|---|---|---|
| One stage-1-style arm, job only (training plus evaluation; generation is about 81%) | 34–52 min; one Gate A arm about 3,115 s | $1.01–1.55 | sharpened plan §1 item 6; paper draft, development evidence |
| One 1B fine-tune-only pod (setup, preflight, job, copy-back; untuned baseline reused) | OLMo recipe G: 55.9 min of job in 1.28 h of pod time. Rung-2 probes: 44–61 min of job. | $2.29; about $2–2.5 (the rung-2 pods, measured at $1.79/h) | dossier §7 |
| One 1B pod with a new untuned baseline plus one fine-tune | Llama recipe-B probe: pod 15:25–16:48 UTC on 8 Oct (1.38 h) | $2.48 (recorded as about $2.2 at $1.59/h) | results record, "Llama-3.2-1B probe" |
| Two report-only Llama seeds, one failed attempt included | read from the account | about $5.3 | dossier §8b, 9 Oct update |
| HarmBench classifier on a pod | 0.06–0.09 s per label | about $0.35 per 800 labels (with setup); about $0.6 per 5,600–7,200 | dossier §7 |
| Granite Guardian second judge | on the Mac | $0 | results record |
| Failure and idle allowance | 2–5 Oct: $38.88 of $153.48 (25%) | 20% added to every GPU line | dossier §7, §8b |
| Storage | about $0.7 per day to the end of January | about $80 | dossier §8b |

### 6.2 Stage costs, re-derived from dossier §8b

Method: §8b's stage estimates at $1.59/h × 1.126 (= $1.79 / $1.59) × 1.2 (failed pods and re-runs). §8b itself used × 1.16, which matches the $1.85/h planning rate, not the billed $1.79/h. The larger GPUs (H200, B300) get only the 20%, as in §8b. The 9 Oct update's changes are applied: Safe LoRA adds $5–10 to stage 1; the Qwen runs for the arXiv note are binned. Each figure is rounded to the nearest dollar.

| Stage | §8b at $1.59/h | At $1.79/h, with 20% | In this ask? |
|---|---|---|---|
| Gate B (stage 0; contingency inside) | $50–62 | $68–84 | **No:** paid now from the current balance (§8b 9 Oct update: the balance plus about $10 before wave 1; FOCUS 9 Oct 13:16 UTC: the top-up may be about $13–17; DRAFT revision 5 recomputes) |
| Stage 1 (six repairs, references, B+Qi) plus Safe LoRA | $73–120 | $99–162 | Yes |
| Planted-cause sweep (1b) | $17–35 | $23–47 | Yes |
| Secondary arms (1c) | $45–80 | $61–108 | Yes |
| Llama-3.2-1B (stage 2): Gate A, anchors, Gate B-lite, primary family | $65–115 | $88–155 | Yes |
| Confirmation (stage 3) | $58–95 | $78–128 | Yes |
| OLMo Gate A seeds at recipe G; Qwen runs for the arXiv note | $11–20 | – | **No:** the OLMo seeds ran on 8 Oct; the Qwen runs are binned (9 Oct) |
| 7–8B reduced benchmark (OLMo-2-7B, Llama-3.1-8B; A100) | $200–400 | $270–540 | Yes |
| 32B / 70B headline check (H200, B300; prices **UNVERIFIED**) | $150–600 | $180–720 | Yes |
| **GPU in this ask** | | **$799–1,860** | lines use the upper ends |

**Not costed in any record:** Alpaca runs at 1B after Gate B. The dossier's §8b has no Alpaca line; only the 7–8B replication on Alpaca is inside the 7–8B line. `[for the lead: cost the Alpaca probe and arms before the user submits, or state that they come from a later request.]`

Judging on a pod (HarmBench, Granite) adds about $0.4–1 per 800–7,000 labels (§8b 9 Oct update). It is small against the 20% allowance.

### 6.3 The ask: $6,000 (the user's choice), against $3,160 of research items

| Line | Basis | Upper (field 14) | Midpoint |
|---|---|---|---|
| GPU stages (§6.2) | dossier §8b, re-derived | $1,860 | $1,330 |
| Human check of about 500 answers | dossier §8: $800 for about 1,000 answers (no quote; **UNVERIFIED**); the user's 6 Oct line | $400 | $400 |
| AI tools | dossier §8: $800–1,200 (prices **UNVERIFIED**; see §1.3); the user's 6 Oct line | $800 | $800 |
| Storage and verified backups | dossier §8; the user's 6 Oct line (§8b estimates about $80 to the end of January) | $100 | $100 |
| **Research items** | | **$3,160** | **$2,630** |
| Difference to $6,000 | arithmetic | **$2,840** | $3,370 |

- Field 14 uses the upper end of each GPU range. A rapid grant is one lump sum, and a second request costs weeks, so the upper end is the buffer. No further contingency is added.
- Salary or a stipend is in no line. The page funds time and living costs; the decision is yours (§9).
- Other lines in the records, if you prefer them to a stipend: the dossier's fuller human check ($800 for about 1,000 answers, +$400; a second rater is an open decision in the paper draft); an API judge sample ($200); AI tools at the dossier's upper $1,200 (+$400); conference travel (about $3,000, **UNVERIFIED**, only if a paper is accepted and you present).

### 6.4 Recommendation (one line)

**The research items in field 14 add up to $3,160 at the upper estimates (Alpaca at 1B is not yet costed, §6.2), so either fill the $2,840 row with a stipend you can justify, or set field 11 to $3,200 (the items rounded up to the next $50); do not send $6,000 with items that add up to less.**

### 6.5 Check against dossier §8a and §8b

- **§8a is superseded for its lines.** Its $6,000 breakdown (kill test $145; engineering $200; development $2,250; confirmation $1,500; contingency $605; human check $400; AI tools $800; storage $100) priced the GPU work from the 6 Oct reframing ranges for a Qwen 1.5B plan. Measured 1B pods (about $2–2.5 each) replace those ranges. The non-GPU lines ($400, $800, $100) are kept.
- **§8b's GPU tiers still cover.** Re-derived at $1.79/h with §8b's own method (Gate B included, storage $80 inside, the 9 Oct changes applied): minimum about $780 (§8b: about $800); recommended about $1,320 (§8b: about $1,500); full about $2,040 (§8b: about $2,200). §8b priced them at about $1.85/h, so they hold.
- This ask's GPU lines ($1,860) equal §8b's full tier without Gate B and without storage (Gate B is paid elsewhere; storage is its own line).
- **Overlap.** §8b prepares a separate compute request for GPU funds. If it is approved, it would cover GPU lines that this ask also lists. See the `[USER: …]` note under field 14.

---

## 7. Risks and honest limits

| Risk | What we do |
|---|---|
| **Gate B may read DIFFUSE or TOO CLOSE.** Our recorded prior says this is more likely than LOCALIZED. | Planned for. Stage 1 runs unchanged, because its arms compare with random removal and no repair whatever the verdict. The positive control becomes the only test of whether diagnosis can pay. The paper takes its fallback title. |
| **The measure tracks lost refusal more than harm.** After fine-tuning, Qwen3Guard's Unsafe label is close to "did not refuse". | Three judges. A claim rule: a sentence may say "harmful compliance as the HarmBench classifier defines it" only if the classifier's contrast has the same sign and at least half the size, and its erosion under that recipe is at least 20 points; otherwise it says "restored refusal". A human check is in the budget; the development read had one reader. |
| **Llama may reach no partial rung at recipe B.** | The rule is fixed now (after the ladder was read; disclosed): the highest rung of 1e-4, 5e-5 and 2e-5 whose probe reads partial, chosen from probes only. If none does, the paper is single-family and says so. |
| **Nulls everywhere.** A 600-row removal may move too little to detect. | Equivalence labels (±5 points), a positive control with a known cause, and a random dose curve. |
| **A free reference may win.** | A valid answer. The headline then says so. |
| **Small scale.** 1B models and one benign dataset at first. | Alpaca after Gate B; a 7–8B replication in a published setting; no claim at a size without runs at that size; no 1B cost ratio claimed for larger models. |
| **Recipe B is plain, not standard practice.** | Recipe G is reported as a recipe-only fix and a reference. The main recipe was chosen from probe and Gate A readings, never from a repair result. |
| **Re-implemented baselines may be weaker than the originals.** | A deviation table per scorer, contact with the authors, and the published-setting replication. |
| **Prior work overlaps** (DualSelect, Yin and Rush, DataShield). | No "first" claims. We claim only the combination. |
| **The skill bar (ARC) was loosened during development.** | Disclosed, with both readings reported. "Skill kept" rests mainly on held-out task loss. |
| **Money stops.** | Each stage starts only on a funding event. Only complete seed blocks are analysed. A budget guard checks the balance before every launch. |
| GPU availability, usage limits, working alone | Scripted kits, stop timers, verified backups; staged gates limit wasted work. |

---

## 8. Deliverables

1. **A paper** (NeurIPS 2027 or TMLR; ICML 2027 if funded in time). **A null or narrowed result is published too.**
2. **Open code**: the engine, run kits, analysis and gate-reading scripts.
3. **Frozen protocols**: the repair study's gates, labels, margins and stop rules, hashed before outcomes, plus the decision log, which also records each rule fixed after development data were seen.
4. **Cost accounting**: per-arm and per-diagnostic costs in GPU-seconds and full-run equivalents, including failed and idle time, and outcome tables (menus × seeds × outcomes × costs) that others can reuse.
5. **A completion report to BlueDot** within 60 days of the end.

Ethics: we do not publish generated harmful answers; we release scores, code and protocols. PKU-SafeRLHF and Alpaca are CC BY-NC 4.0, used for non-commercial research only. Dolly is CC BY-SA 3.0, so derived rows keep that licence. OLMo-2 is Apache-2.0. Llama-3.2 is a gated model, used under its licence terms.

---

## 9. Fields only the user can fill (never filled here)

| Field | Notes |
|---|---|
| Your name | – |
| Your email | The form asks for the email used for BlueDot course messages and the Course Hub. |
| Where are you based? | Your notes say you are US-based and only travelling in India. The form says BlueDot cannot fund people based in India; the page (9 Oct) lists India and not the US. Answer truthfully. If you are unsure how your travel affects this, the page says to contact BlueDot before applying. Payment must go to an account in a country BlueDot can pay. |
| Where can we learn more about you? | LinkedIn or a personal website |
| **BlueDot connection** (field 10) | Choose from: course participant, course alum, facilitator, AI safety community member, other. A grant is more likely with a BlueDot or community link. |
| Link to your work | Your choice of what to make public. Options from the repo: the Substack post (dossier §2: `spiderishi.substack.com/p/first-make-sure-a-fix-can-work`, published 6 Oct; not opened by me), the anonymous artifact (`docs/anonymous-artifact.md`), or the GitHub repo (whether it is public is **UNVERIFIED**). |
| Public sharing and public URL | Your choice; "with my name" is pre-selected. |
| Share with other funders | Your choice; "Yes" is pre-selected. |
| Why you | Background, skills, track record; a CV link if you want one. |
| What you would do without the grant (field 16) | Facts about your own funds and plans. |
| **The $2,840 row in field 14** (new) | A stipend for your time, with what it buys, or delete the row and set field 11 and the field 14 total to $3,200 (§6.4). |
| Stipend for your time | Your decision; not in any research line. |
| **Gate B funding** (new) | Confirm that Gate B is paid from the current compute balance, not from this grant (fields 12 and 14). |
| **Other compute funding** (new) | If you file the compute request for GPU funds (dossier §8b), disclose it and say which GPU lines it covers (fields 14 and 18). |
| Other applications to disclose | The ones you actually send (field 18). |
| Llama probe sentence (optional; not personal) | Fill only from FOCUS.md's reading of the 9 Oct probe (field 13). |
| **Payment details** | Given later in BlueDot's claims portal, after approval. Never in this draft. |
| Tax | The dossier §11c says grants are likely taxable for a US person; check with a tax adviser. |

---

## 10. Claim-rule check

| Rule | Status in this draft |
|---|---|
| U is "refusal erosion as Qwen3Guard labels it"; harm wording only as "harmful compliance as the HarmBench classifier defines it", and only where E_HB ≥ 20 pp and the same-sign, half-size rule holds (FOCUS 8 Oct 10:14 and 13:53 UTC; 9 Oct 15:05 and 15:23 UTC) | Followed. After the fact-check, field 13's heading and field 15 use the exact phrase. Harm wording is used only for recipe B on OLMo; recipe G's erosion is called refusal erosion only. |
| The blind-read caveat travels with the measure, as development evidence with one reader | Stated once in field 13 and in §4, with its limits (five pooled groups; the reader helped design the study). Field 15 points to it. |
| Do not claim that practitioners ask whether attribution is worth its compute | Not claimed. The question is stated as ours. |
| Do not call round 1 "classifiers fail" | Worded only as a finding about a fixed-size top-K rule (§4). |
| Do not claim a first benchmark of safety filters, a first remove-versus-add comparison, or a first pricing of diagnosis; novelty only as "the combination" | Stated as a combination; DataRx, SafeTune, DualSelect and Guo et al. cited as nearby work. |
| Do not claim that adding safety data helps or hurts in general | The DataRx sentence says the choice of safety data decides the outcome, with its exact figures. |
| Do not claim harmful compliance from U alone | Every harm sentence rests on the HarmBench classifier. |
| Do not claim that data repair beats model-level repair unless it beats the references | Stated as the bar a data repair must clear. |
| Do not claim any 7–8B result without a 7–8B run | Scale is described as planned. |
| Development evidence labelled | Yes: fields 13 and 15, and §4. |
| Pending results not guessed | The Llama probe at recipe B and LR 5e-5 is marked as running, with an optional slot. |
| Rules fixed after seeing data are disclosed (the 20–55 window, the ARC rule, the per-family learning-rate rule) | Field 17 (all three). Field 13 and §4: the per-family rule; §4 also the 20–55 window. §7: the ARC and per-family rules. |
| Claims that the paper marks [CITE-CHECK] carry a mark in the form text | Fields 12 and 17. |
| The "worse" label says "adverse" (9 Oct 15:23 UTC) | Field 12: "significantly adverse". |

---

## 11. UNVERIFIED items

1. The **ICML 2027 deadline** (about 22 Jan 2027) and the **NeurIPS 2027** date (about mid-May); TMLR timing. Estimates from the records, not official.
2. **The BlueDot form** was not re-read on 9 Oct (§1.2). Whether applying now needs a BlueDot sign-in. The live counters on 9 Oct.
3. **Whether BlueDot still excludes general AI subscriptions** (the Nov 2025 rule); it affects the $800 AI-tools line. How a stipend maps to the form's grant types.
4. **AI-tool prices** behind the dossier's $800–1,200 estimate.
5. **Human check cost** ($0.80 per answer implied by the dossier's $800 per 1,000): no quote.
6. **H200 and B300 prices** behind the 32B/70B line; that line also needs a small engine and kit round first.
7. **Every stage cost** is an estimate scaled from measured 1B arms (plan §10; dossier §8b). The plan marks Llama's per-run cost UNVERIFIED. Alpaca at 1B is not costed.
8. **Microsoft's "review your training data set and resubmit" wording**: from the dossier §1a (read 6 Oct by another chat; the paper draft lists it for a re-check).
9. **Nearby-work wording** (paper draft CITE-CHECK items 6, 7 and 21, and its [CITE-CHECK] on "seldom with their compute counted", used in field 12): SafeTune's "single deterministic runs" is PDF-checked, but "compares repairs of safety drift" rests on its title and a fetch summary; DualSelect's "three seeds and a false-refusal rate" comes from the plan's novelty review, not re-read. DataRx's 59.23% and 13.70% are in its abstract; 20.24% is its Table II (PDF read in the recipes note). Fields 12 and 17 carry inline `[CITE-CHECK: …]` marks for these.
10. **Whether the GitHub repo is public**; the Substack URL (from the dossier; not opened by me).
11. **Travel cost** (about $3,000): the dossier's estimate.
12. **Total GPU spend to date.** The ledger covers 2–5 Oct ($153.48). Later spend is recorded per pod in FOCUS and the results record, with no single total.
13. **The Llama recipe-B probe at LR 5e-5**: running at the time of writing; no result.

---

## 12. Dossier sections now out of date

These sections of [2026-10-05-grant-evidence-dossier.md](2026-10-05-grant-evidence-dossier.md) still use old framing or old facts. I did not edit the dossier.

| Section | What must change |
|---|---|
| **Title** ("decision value of training-data attribution for safety data edits") | Use the paper's working title, *Repairing Safety After Benign Fine-Tuning: A Compute-Matched Comparison of Data Repairs*. |
| **§1 pitch and "Grant version"** | Old framing; replace with this draft's §2 pitch. |
| **§2 research question and novelty** | Replace with the measured repair comparison (FOCUS 8 Oct 13:53 UTC), novelty as a combination, and the nearby work in field 17. |
| §5 infrastructure | Engine test count 269 → 759 (3 skipped) on 9 Oct (commit 0e2299e); add the multi-family engine, the run kits and the pod judge launcher. |
| §6 data, models and licences | Main model OLMo-2-1B-Instruct (Apache-2.0), second family Llama-3.2-1B-Instruct (gated); Qwen as development evidence; Dolly-15k (CC BY-SA 3.0), PKU-SafeRLHF for the add repairs, Alpaca (CC BY-NC 4.0) after Gate B; the HarmBench classifier (MIT) as a judge. |
| **§8 budget tiers and §8a** | §8's tiers are for the old question; §8a's $6,000 lines are superseded by this draft's §6.3 (the non-GPU lines are kept). |
| §8b | Its × 1.16 factor matches $1.85/h, not the billed $1.79/h (§6.2 here); its tiers still cover. Add a note that Alpaca at 1B is not costed. |
| §9 risks | Old risks; use this draft's §7. |
| **§10 timeline** | Old six-step plan; use this draft's §5 (Gate B, stages 1–3, scale, venue check about 1 Dec). |
| §11a BlueDot | Add the 6 Oct page facts (form questions, 4-day average, 938 grants) and the 9 Oct re-check (§1 here); mark "about 5 working days" and the $50–1,500 range as the Nov 2025 programme; its recommendation ("$5–10k for the development stage") and checklist rows point to old sections. |
| §11c suggested order | "Use the dossier's pitch" → use this draft's pitch and budget. |
| §12 deliverables | Add per-diagnostic costs in full-run equivalents, the outcome tables, and Dolly's share-alike licence. |
| "Sources inside this repository" | Add FOCUS.md, the results record, the sharpened-direction plan, the Gate B DRAFT, the paper draft and this draft. |
