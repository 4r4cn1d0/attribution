**DRAFT for the user's review. Not submitted. Written 6 Oct 2026.**

# BlueDot Rapid Grant application (draft): *Diagnose or Retrain?*

Written by an Opus 5.5 worker (Claude Code subagent) at the coordinator's request. This file is the only change. Nothing was submitted, nothing was spent, no account was used, and nothing was committed. No held-out data was read.

**Inputs read (repo):** [FOCUS.md](../FOCUS.md) ("Adopted direction"); [reframing proposal](../review/2026-10-06-reframing-proposal.md) §§2, 2a, 2b, 3a, 4; [grant dossier](2026-10-05-grant-evidence-dossier.md) (all); [v2 results](../experiments/2026-10-06-headroom-v2-results.md); [kill-test design](../experiments/2026-10-06-kill-test-design-DRAFT.md) (all, with Appendix C); [positioning review](../review/2026-10-06-positioning-review.md); [reading list v2](../review/2026-10-06-reading-list-v2.md) (novelty verdict, objections, limits); [cost ledger](../costs/2026-10-06-cost-ledger.md); [round-1 results](../experiments/2026-10-05-headroom-round-1-results.md) (arm table only); `.ai/briefs/kill-test-stage0-engine-20261006.md` (Stage 0 cost and go/no-go rule); `.ai/inputs/kill-test-stage0/integration-review.md` (test counts, Dolly counts).

**Web pages opened on 6 Oct 2026, about 15:00–15:10 UTC:**
- <https://bluedot.org/grants/rapid>: raw HTML (curl) and the rendered page (built-in browser, which shows the live counters).
- <https://bluedot.org/grants>: raw HTML (curl).
- The "Apply now" target on the rapid page: a public Airtable form, <https://airtable.com/appMVNtdBtvtJvu5E/pag9G3oF4DYAyassX/form> (tracking parameters removed). I read the questions and opened the four drop-down lists to read their options. I typed nothing, selected nothing and submitted nothing. Then I closed the tab.
- The dossier's blog link, <https://bluedot.org/blog/rapid-grants-for-bluedot-projects>. It serves a Substack post dated 25 Nov 2025 about an **older** version of the programme (see §1.3).

---

## 1. What BlueDot asks (read 6 Oct 2026)

### 1.1 The programme page

| Item | What the page says | Page |
|---|---|---|
| Amount | Up to $20,000 per grant. If you need more, contact BlueDot. | rapid |
| What it funds | Research and learning (time, living costs, research access); projects and experiments (compute, tools, testing an idea); events and community; travel and collaboration | rapid |
| What reviewers look for | "a worthwhile direction, evidence you can make progress, and a clear role for funding" | rapid |
| Who | People taking a promising next step in AI safety or biosecurity. A grant is more likely for BlueDot course participants, alumni, facilitators and active community members. A BlueDot course is **not** required. | rapid; grants FAQ |
| Country limits | BlueDot cannot send money to 23 listed countries and territories, **India included**, or where sanctions apply. If unsure, contact BlueDot before applying. | rapid; grants |
| Not funded | Party-political work, activities unlawful in the UK or your jurisdiction, work outside BlueDot's charitable or educational purposes | rapid |
| Process | Apply (plan and budget, about 15 minutes) → email decision → claim in the claims portal → one lump-sum payment after checks. Transfer and exchange fees can reduce the amount received. | rapid |
| Speed (live counters) | Average decision time **4 days**; 9 in 10 applicants hear back **within 13 days** | rapid, rendered |
| Volume (live counters) | **938** grants made; **$2,615,443** given. Mean ≈ **$2,790** per grant (my arithmetic). | rapid, rendered |
| After the grant | Use the money for the agreed purpose. Get written approval before a material change. Send a short completion report within 60 days of the end. | rapid |
| Larger asks | Career Transition Grants (up to $200k, usually from $20k) are for moving full-time into the field. Not this request. | grants |

### 1.2 The application form (Airtable, "Rapid Grant Application")

Field names are as shown on the form. Help texts are paraphrased. "Req" = required (marked *).

| # | Field | Req | Type and limits | Who fills it |
|---|---|---|---|---|
| 1 | Your name | yes | text | **user only** |
| 2 | Your email | yes | text. The form asks for the email used for BlueDot course messages and the Course Hub sign-in. | **user only** |
| 3 | Where are you based? | yes | text. The form says BlueDot cannot fund people based in Russia, China or India. | **user only** (see §9) |
| 4 | Where can we learn more about you? | yes | LinkedIn or a personal website preferred | **user only** |
| 5 | Grant type | yes | multi-select: *Compute & research tools*; *Events & community*; *Travel*; *Something else* | suggested: *Compute & research tools* |
| 6 | What are you working on? | yes | **200-character limit** | drafted (§3) |
| 7 | Link to your work | yes | GitHub repo, demo, draft or other evidence; more than one link allowed | **user only** (options in §9) |
| 8 | If we approve your grant, can we share details about it publicly? | yes | *Can share publicly with my name* (pre-selected) / *without my name* / *Cannot share publicly* | **user only** |
| 9 | Public URL | no | one URL for BlueDot's website | **user only** |
| 10 | How are you connected to the BlueDot community? | yes | multi-select: *Course participant*; *Course alum*; *Facilitator*; *AI safety community member*; *Other* | **user only** (eligibility angle) |
| 11 | How much funding are you requesting? | yes | dollars, best estimate **to the nearest $50** | drafted: **$6,000** (§6) |
| 12 | Tell us more about your project. | yes | free text; no limit shown | drafted |
| 13 | What have you already done? | yes | concrete progress; no limit shown | drafted |
| 14 | What specifically would this grant fund? | yes | **each item with its estimated cost**; explain any stipend request | drafted |
| 15 | How does this reduce catastrophic risk from AI and/or contribute to AI going well for humanity? | yes | free text | drafted |
| 16 | What would you do without this grant? | yes | abandon, reduce scope, use slower or free options, or self-fund, and the impact | drafted; **user must confirm** |
| 17 | What makes you think this project will be successful? Why you? Why now? | yes | free text | drafted; "why you" is **user only** |
| 18 | Feedback | no | anything else to consider | suggestion only |
| 19 | Can we share your application with other funders and organizations as relevant? | no | *Yes* (pre-selected) | **user only** |

No word limits are shown except field 6. The page says the form takes about 15 minutes, so the drafts below are short.

### 1.3 Where the dossier (§11a) is now out of date

- The "about 5 working days" figure came from the **25 Nov 2025 blog post**. That post describes an older programme: course participants and facilitators only, most grants $50–1,500, no pay for the applicant's own time, and no general AI subscriptions (for example Claude Pro) unless "highly leveraged".
- The current page differs. No course is required. It funds "time, living costs". The live average is 4 days.
- **UNVERIFIED:** whether the old exclusion of general AI subscriptions still applies. The current page lists "tools" but says nothing on subscriptions. This affects the AI-tools line (§6).

---

## 2. Three-sentence pitch

When people fine-tune a safe chat model on ordinary, harmless data, the model can become less safe, and a user who can change only the data must pick a fix: keep the data, remove a source, add safety data, or rewrite the answers. Fixes have side effects: in our pilot with injected harmful data, the best fix cut unsafe answers from about 80% to about 11%, but harmless test prompts were refused 44 times in 100 instead of once. With repeated training runs and held-out checks, we will measure which fix restores safety within limits on over-refusal and task skill, and how much diagnosis (a safety classifier, representation similarity, training-data attribution or short trial runs) is worth paying for first, with each method charged its cost in full training runs.

---

## 3. Form-ready answers

Style: short sentences, active voice, simple words. **Fill or replace every `[USER: …]` and `[PLACEHOLDER …]` before submitting.**

### Field 5. Grant type
*Compute & research tools.* (Add *Travel* only if you choose the fuller tier with travel.)

### Field 6. What are you working on? (182 of 200 characters)
> Which data fix restores an LLM's safety after benign fine-tuning without causing over-refusal, and how much diagnosis (classifier, attribution, trial runs) is worth paying for first?

### Field 11. How much funding are you requesting?
**$6,000** (recommended tier; §6). Lean alternative: $3,050. Fuller alternative: $10,950.

### Field 12. Tell us more about your project.

**The problem.** Fine-tuning a safe chat model on ordinary, harmless data can make it less safe. Qi et al. (2023) report this for Alpaca and Dolly fine-tunes. `[UNVERIFIED: FOCUS.md requires reading Qi et al. in full before citing; our numbers come from a fetch summary.]` Fine-tuning services screen customer data and can block an unsafe model. Then they tell the customer to fix the data and resubmit. `[source: dossier §1a, Microsoft Foundry docs; see §11 item 12]` The customer must choose the fix.

**The fixes.** A user who can change only the data has four fixes: keep the data, remove a source, add safety data, or rewrite the answers. Each fix can have side effects. A fix can make the model refuse harmless requests. A fix can also reduce task skill.

**The questions.**
1. Which fix restores safety and stays inside fixed limits on over-refusal and task skill?
2. How much diagnosis is worth paying for before you choose? We compare a safety classifier, representation similarity, training-data attribution and short trial runs. We charge each one its measured cost in full-run equivalents. We report its value as a function of that cost, not at one budget.
3. Can a diagnosis predict a fix's side effects better than trial runs at the same compute?

**The design.**
- Model: Qwen2.5-1.5B-Instruct with LoRA.
- Main setting: benign fine-tuning that erodes safety. Anchor setting: overt harmful data, where a classifier should be enough.
- The fix that diagnosis must beat: add a fixed small safety mix.
- Selector: fixed-budget successive halving with a feasibility screen.
- We freeze the rules before we see outcomes. We repeat training seeds. We confirm on held-out menus with fresh seeds. We report results that are too close to call.

**A kill test comes first.** It checks three things in order. (A) Does an ordinary Dolly fine-tune erode safety beyond seed noise? (B) Does one data source cause the erosion, or is it spread out? (C) Does attribution find the cause better than representation similarity, by a margin fixed in advance? A failed gate stops or narrows the study. We report that result.

**Target.** An ICML 2027 submission (deadline estimated about 22 Jan 2027; not official). Fallback: NeurIPS 2027.

### Field 13. What have you already done?

All results so far are development evidence. Nothing is confirmatory yet.

- **I built and tested the engine.** It prepares data with token audits and sealed held-out splits. It trains with exact resume and checks bit-exact training on a two-step A100 fixture. It applies remove, rewrite and add edits. It records the cost of every step. At the 6 Oct integration, 311 engine tests passed (3 CUDA-only skips), plus 172 selector tests and 260 durability tests.
- **I showed that fixes have side effects (v2, 2 seeds).** The setting was Qwen2.5-1.5B (base) trained on chat data plus 507 injected unsafe answers. Rewriting the classifier's top 507 rows cut sampled unsafe answers from 80.3% to 11.4% (−68.9 pp; 95% interval −76.5 to −60.5). A random rewrite of 507 rows did nothing (81.6%). A second judge agreed on 97.2% of 1,200 answers. **But the fix failed our no-damage rule, which we wrote down before the runs.** Harmless XSTest prompts were refused 44 times in 100, against 1 in 100 before the fix. The classifier found 93% of the injected rows. So the hard part was choosing a fix that does not over-correct, not finding the rows.
- **I found that a fixed-size removal rule can backfire (round 1, 2 seeds).** A rule that removes the classifier's top 10% of rows (1,015 rows) raised unsafe answers from 12.5 to 24.0 of 72. Both seeds were above both baseline seeds. The editable pool held only 43 harmful-answer rows, so the fixed-size rule removed mostly rows that were not unsafe. This is a finding about a fixed-size top-K rule. A threshold rule is untested.
- **I designed the kill test and built its first stage.** The design fixes gates, margins and stop rules before any run. Stage 0 is running now: the untuned Qwen2.5-1.5B-Instruct against one Dolly-15k fine-tune.
  `[PLACEHOLDER: kill-test Stage 0 result. Running now. Do not guess. Fill in: U(untuned) = __%; U(Dolly a0, seed 1101) = __%; E_1101 = __ pp; futility verdict (pass if E_1101 ≥ 3 pp) = __; Granite direction = __; over-refusal and task skill = __; measured cost = $__.]`
- **I counted every dollar.** The cost ledger covers 48 GPU pods (2–5 Oct): $153.48, including failed attempts ($30.61) and idle time ($8.27). One full training-and-evaluation run costs a measured $3.96.
- I published a short public post on the development results (6 Oct). `[USER: decide whether to link it; §9.]`

### Field 14. What specifically would this grant fund?

All figures are estimates built from measured unit costs (§6). GPU work runs on rented A100s at $1.59 per hour.

| Item | Cost |
|---|---|
| Kill test, minimum version with the early side-effect check: 25–29 training runs at a measured $3.96 each, plus 15% for failures | $145 |
| Engineering and calibration runs (new data path, add and self-distill edits, task-skill and representation-similarity measures) | $200 |
| Development runs: 2 settings × at least 5 seeds, plus a seed-repeated replication of Pan et al. | $2,250 |
| Confirmation runs: held-out menus, fresh seeds | $1,500 |
| Contingency: 15% of the three lines above, rounded so the total is a multiple of $50 | $605 |
| Human check of about 500 model answers (harm and refusal labels), to test the automatic judges | $400 |
| AI coding and research tools, about 15 weeks | $800 |
| Storage and verified backups | $100 |
| **Total** | **$6,000** |

Spending is staged. Each stage spends money only if the earlier gate passes. If the kill test stops the study, I will tell BlueDot and ask in writing how to use or return the unspent money.

`[USER: decide whether to request a stipend for your time. The page lists "time, living costs" as fundable. No amount is proposed here. If you add one, the form asks you to explain the role.]`

### Field 15. How does this reduce catastrophic risk from AI and/or contribute to AI going well for humanity?

Fine-tuning services let customers fine-tune aligned models on their own data. If ordinary fine-tuning erodes safety, the models that people use become less safe than the models they started from. Often the person who must fix this can change only the data. Today that person has no tested rule for which fix to use, or how much checking to pay for first.

Our pilot shows the risk of a fix chosen without care. The fix removed most unsafe answers, but it made the model refuse many harmless requests. This project gives a tested, costed rule, with open code and frozen protocols. It also tests whether training-data attribution, which researchers propose for safety data curation, is worth its compute here. A negative result is useful too: it tells people to spend compute on trial runs or on a default fix instead.

Limit: this is about everyday fine-tuning safety at small scale. It does not address catastrophic misuse directly.

### Field 16. What would you do without this grant?

`[USER: confirm or correct this draft. It states facts about your own funds.]`

Without the grant, I would run only the kill test from my own funds. I could not pay for the engineering, development and confirmation runs (about $4,500 of GPU time with contingency) by early November. I would miss ICML 2027. I would aim for NeurIPS 2027 or a workshop paper with a smaller study. Free GPU tiers do not fit: the engine checks exact training on one GPU type, and comparable costs need one kind of hardware.

### Field 17. What makes you think this project will be successful? Why you? Why now?

**Why it can succeed.** The hard infrastructure exists and is tested (field 13). The measurement detects large effects and side effects, and two different judges agree. Unit costs are measured, so the budget is not a guess. Every gate and stop rule is written down before the runs. A null result is planned for and will be published.

**Why now.** Two August 2026 preprints show that the field is moving here. SafeTune (arXiv 2609.22153) compares model-level repairs of safety drift, but it has no data fixes and one seed. DataRx (arXiv 2608.04322) compares ways to add safety data, but it has no removal fix and no costs. Each part of our design exists separately. No study we found combines data fixes of different types, diagnosis charged in training-run equivalents, and seeded held-out confirmation. The ICML 2027 deadline is about 15 weeks away.

**Why me.** `[USER: your background, relevant skills and any track record. Add a CV link if you want to.]`

### Field 18. Feedback (optional; suggestion only)
`[USER: list any other applications you have actually sent (the dossier §11c recommends disclosing all of them). Optionally add a note on your location; see §9.]`

---

## 4. Evidence so far (development evidence only)

| Finding | Numbers | Source |
|---|---|---|
| **v2: a large safety gain with a large over-refusal cost** | Qwen2.5-1.5B base, ToxicChat-Het plus 507 injected unsafe PKU-SafeRLHF rows; 2 seeds. Sampled unsafe rate: a0 80.3%, targeted rewrite 11.4%, random rewrite 81.6%. Rewrite − a0 = −68.9 pp [−76.5, −60.5]; rewrite − random rewrite = −70.2 pp [−78.5, −61.3]. ARC within 0.03. **XSTest-safe refusals: a0 1/50 and 0/50; rewrite 22/50 and 22/50** (limit: +5 pp). OR-Bench-hard refusals: 1/50 and 0/50 → 30/50 and 36/50. Second judge (Granite Guardian, greedy answers): 97.2% agreement, κ 0.942, same direction. Classifier recall on injected rows: 471/507 (0.929); the targeting effect is large partly by construction. Refusal labels come from Qwen3Guard alone; no person read the answers. Positive-control phase cost about $20. | [v2 results](../experiments/2026-10-06-headroom-v2-results.md) |
| **Round 1: a fixed-size top-K removal rule backfired** | Base model on ToxicChat-Het; remove the classifier's top 1,015 rows (10%). Unsafe answers: a0 12.5 of 72 → 24.0 of 72 (seeds 19 and 29 against 14 and 11). The editable pool held 43 harmful-answer rows and 33 refusal rows. **Wording rule:** a finding about a fixed-size top-K removal rule only. A threshold rule ("remove rows judged Unsafe") is untested. | [round-1 results](../experiments/2026-10-05-headroom-round-1-results.md); [dossier](2026-10-05-grant-evidence-dossier.md) §3; [positioning review](../review/2026-10-06-positioning-review.md) §0 |
| Small removals did not move the aligned model | dev-matrix-002: 12 single-group removals (0.08–0.63% of rows) on Qwen2.5-1.5B-Instruct all stayed within seed noise | dossier §3 |
| Seed noise is large | Mostly a shared shift (R = 3.3); about 5 seeds per key arm are needed | dossier §3 |
| **The engine and records** | Engine 311 tests passed (3 CUDA-only skips), Stage B 172, durability 260, at the 6 Oct kill-test integration. Bit-exact two-step A100 fixture; sealed held-out splits; near-duplicate exclusion; process receipts; verified backups; a cost ledger that counts failed and idle time. | `.ai/inputs/kill-test-stage0/integration-review.md`; dossier §§4–5; [cost ledger](../costs/2026-10-06-cost-ledger.md) |
| **Kill-test Stage 0** | `[PLACEHOLDER: running now; do not guess. Untuned Qwen2.5-1.5B-Instruct against one Dolly-15k fine-tune (seed 1101), 4,800 training rows in 8 category units of 600. Fill in U(untuned), U(a0), E_1101, the futility verdict, Granite's direction, over-refusal, task skill and cost.]` | `.ai/briefs/kill-test-stage0-engine-20261006.md` |

**If Stage 0 stops at the futility bar (E_1101 < 3 pp), do not submit this draft as written.** The plan then moves to the fallback ladder (kill-test design §2.5: a higher learning rate, then full fine-tuning, then 7B, each needing the user's approval for spend), and the budget changes.

---

## 5. Plan, milestones and gates

Basis: reframing proposal §4 (about 15 weeks at 50–60 h a week) and the kill-test design. Dates count from Tuesday 6 Oct 2026.

| Weeks (dates) | Milestone | Gate or stop rule | GPU cost (estimate) |
|---|---|---|---|
| 1, may run into 2 (6–19 Oct) | **Staged kill test.** Stage 0 (running now) → rest of Stage 0 (Dolly 3 seeds, Alpaca 3 seeds) → random-removal null and noise gate → wave 1 (9 units × 1 seed) → wave 2 replication → optional early side-effect check (default add arm: a fixed 3% safety mix) | **Futility:** E_1101 < 3 pp → stop and return to review. **Gate A:** E ≥ 10 pp, E ≥ 2 SD over 3 seeds, all seeds above the untuned model, second judge agrees, answers end; Stage 1 needs E ≥ 15 pp. Failure after the ladder → **kill** this setting at this scale and report it. **Gate B:** DIFFUSE → **kill** source-level diagnosis; the question narrows to adding data. **Gate C:** attribution better than representation similarity by a margin above seed noise → **continue**; agree or worse → **shrink** (drop or demote attribution); neither beats random → report "retrain wins". **Side-effect modifier:** if the add arm restores ≥ 80% of the erosion with over-refusal ≤ +5 pp → report "the default fix is enough here". **Cost stop:** re-cost after Stage 0; stop and ask if the projection exceeds the approved amount. | $127–145 (minimum with the side-effect check, measured rate) |
| 2–4 (13 Oct–2 Nov) | **Engineering and calibration:** benign-task data path with sources as units; add and self-distill edits; task-skill measure; representation-similarity diagnostic; per-diagnostic cost records in full-run equivalents; frozen gate-reading scripts | Existing recipes and golden runs stay byte-identical; held-out protections kept | $100–300 |
| 5–8 (3–30 Nov) | **Development tables:** 2 settings (benign erosion main; overt anchor rebuilt on the aligned model) × at least 5 seeds; seed-repeated Pan et al. replication; measured cost of every diagnostic | Pre-set negative / positive / inconclusive margins for each gain; inconclusive → collect new development data or stop | $1,500–3,000 |
| 9 (1–7 Dec) | **Design freeze:** menus (with sealed contamination in held-out menus), selector, limits, margins, cost rules; hashed before any confirmatory outcome | No confirmatory data is read before the freeze | – |
| 10–11 (8–21 Dec) | **Confirmation:** held-out menus, fresh seeds | A confirmatory null cannot trigger retuning on the same data; it is reported | $1,000–2,000 |
| 12–13 (22 Dec–4 Jan) | **Analysis**, including "too close to call" results | – | – |
| 14–15 (5–18 Jan 2027) | **Writing and submission** to ICML 2027 (abstract about 16 Jan, paper about 22 Jan; both **UNVERIFIED** estimates) | – | – |
| Fallback | **NeurIPS 2027** (about mid-May; **UNVERIFIED**) for the fuller version; the Pan replication can go to a workshop | – | – |

**Conditions (reframing §4):** about $3–5k available by early November; 2 settings and 1 model family; the kill test passes. Look-alike data, OLMo and 7B are stretch goals.

---

## 6. Budget

### 6.1 Measured unit costs (A100-SXM4-80GB at $1.59/h)

| Unit | Measured | Source |
|---|---|---|
| One v2-style run on its own pod (setup, preflight, training, evaluation) | $3.96 (149.6 min) | cost ledger §4.1 |
| One evaluation on the v2 development banks | $1.26 (47.7 min) | ledger §4.4 |
| Classifier row scoring (Qwen3Guard-Gen-4B, eager) | $0.158 per 1,000 rows | ledger §4.3 |
| Generation (Qwen2.5-7B-Instruct, eager) | $1.48 per 1,000 rows | ledger §4.3 |
| Stage 0 first pod (baseline + 1 Dolly run) | $5.22 expected; $6.00 with 15% | Stage 0 brief |
| Failure and idle overhead, 2–5 Oct | 27% of GPU spend ($41.69 of $153.48), but $24.47 of it was the one-off 2 Oct credit incident; without it about 11% | ledger §5 (my arithmetic for 11%) |

The contingency used below is 15%, as in the kill-test design. The ledger's history without the credit incident (about 11%) supports it.

### 6.2 Tiers (all figures are estimates)

Rule: the recommended and lean tiers use the midpoint of each reframing-§4 range; the fuller tier uses the top of each range.

| Line | Basis | Lean | **Recommended** | Fuller |
|---|---|---|---|---|
| Kill test | kill-test design §8.4 (minimum + S at the measured rate: $127–145; fuller + S: $160–205) | $145 | $145 | $205 |
| Row-level removal arms (6 runs) | kill-test design Appendix C.1 | – | – | $27 |
| Engineering and calibration | reframing §4: $100–300 | $200 | $200 | $300 |
| Development | reframing §4: $1.5–3k | $2,250 | $2,250 | $3,000 |
| Confirmation | reframing §4: $1–2k | – | $1,500 | $2,000 |
| Second model family (OLMo-2-1B) and a 7B check | positioning review §5 item 9: $1.5–2k | – | – | $2,000 |
| Contingency, 15% of the GPU lines above (kill-test lines already include it) | §6.1 | $368 | $605 (incl. $12.50 rounding) | $1,095 |
| Human audit of model answers | dossier §8: $800 for about 1,000 answers (no quote; **UNVERIFIED**) | – | $400 (about 500) | $800 (about 1,000) |
| API judge sample | dossier §8 | – | – | $200 |
| AI tools | dossier §8: $800–1,200 (prices **UNVERIFIED**; see §1.3) | – | $800 | $1,200 |
| Storage and backups | dossier §8 | $100 | $100 | $100 |
| **Total (nearest $50)** | | **$3,050** | **$6,000** | **$10,950** |
| Optional travel, only if a paper is accepted and the user presents | dossier §8: about $3,000 (**UNVERIFIED**) | – | – | +$3,000 → $13,950 |

- **Lean** ("kill test plus development") reaches the design freeze. Confirmation would need a second application in about week 9.
- **Recommended** funds the whole path to one ICML 2027 submission. Its GPU part (about $4,700 with contingency) matches the reframing proposal's "$3–5k by early November".
- **Fuller** adds a second model family, the row-level test of the diagnostics, a full human audit and an API judge sample.
- Salary is not included in any tier. See the user decision in field 14.

### 6.3 Recommended ask: $6,000

Why this amount suits a rapid grant:
1. **It is the smallest amount that funds the whole staged path** to an ICML 2027 submission, including confirmation and a human check of the judges.
2. **It is well under the $20,000 cap** (page read 6 Oct 2026). It is above the page's mean grant (about $2,790), so the application shows every stage and unit cost.
3. **It is mostly compute with measured unit costs.** "Compute, tools and testing an idea" is a listed category.
4. **Spending is gated.** If the kill test kills or shrinks the study, most of the money is not yet spent, and BlueDot's own rule (written approval for material changes) covers what happens next.
5. **The decision is fast** (average 4 days; 9 in 10 within 13 days), which fits the early-November money condition.

If you prefer a smaller first ask, use the lean tier ($3,050). The risk: a second decision near week 9 can delay confirmation and the ICML date.

If the kill test is already finished when the grant arrives, ask BlueDot whether it can cover costs already spent (**UNVERIFIED**), or move the $145 to development runs.

---

## 7. Risks and honest limits

| Risk | What we do |
|---|---|
| **Benign erosion may not appear at 1.5B with LoRA.** Kim et al. (arXiv 2508.12531) report that better training choices alone cut unsafe answers from 16% to about 5% (from the reading list; not read by us). The untuned model's unsafe rate on our bank has never been measured. | The kill test checks this first (futility bar, then Gate A). The fallback ladder needs the user's approval at each rung. "No erosion under a fixed common recipe" is reported as a result. |
| **The erosion may be diffuse.** No single source may cause it. | Gate B tests this. DIFFUSE kills source-level diagnosis. The question then narrows to adding data. The category-level test cannot rule out row-level causes (kill-test design Appendix C.1); the fuller tier adds the row-level arms. |
| **Cheap non-data repairs may matter more** (for example a one-example patch, weight-space recovery, a safety system prompt at test time). | **The claim is limited to users who can change only the data**, such as fine-tuning-service customers. The fuller kill test can add a test-time safety prompt as an evaluation-only reference. |
| **Small scale.** At 1.5B with LoRA, retraining is cheap, so trial runs may win here and not at large scale. | We report the value of diagnosis as a function of the cost ratio between diagnosis and a run, so readers can apply it at their own scale. One model family; 7B is a stretch goal. |
| The default fix may always be good enough | It is the baseline that diagnosis must beat. If it wins, diagnosis is worth little here, and we report that. |
| Added safety data can hide misalignment | A context-matched harm bank (prompts in the training data's format). |
| Seed noise | At least 5 seeds per key arm; margins larger than the seed spread; paired seeds. |
| The endpoint is classifier-defined; v2's refusal labels had no human check | Second judge, coherence screen, and a human audit sample (budget line). |
| Novelty is narrow | We claim only the combination. SafeTune and DataRx are cited as the closest work. |
| Claude usage limits, GPU availability, working alone | Scripted runs, budget guard, stop timers; staged gates limit wasted work. |

---

## 8. Deliverables

1. **A paper**, submitted to ICML 2027 (fallback NeurIPS 2027 or a workshop). **A null or narrowed result is published too.**
2. **Open code**: the engine, run kits, analysis and gate-reading scripts.
3. **Frozen protocols**: every gate, margin and stop rule, hashed before outcomes, plus the decision log.
4. **Cost accounting**: per-run and per-diagnostic costs in full-run equivalents, including failed and idle time, and a table of menus × seeds × outcomes × costs that others can reuse.
5. **A completion report to BlueDot** within 60 days of the end.

Ethics (dossier §6): we do not publish generated harmful answers; we release scores, code and protocols. CC BY-NC data (PKU-SafeRLHF, Alpaca) are used for non-commercial research only. Dolly is CC BY-SA 3.0, so derived rows keep that licence.

---

## 9. Fields only the user can fill (never filled here)

| Field | Notes |
|---|---|
| Your name | – |
| Your email | The form asks for the email used for BlueDot course messages and the Course Hub. |
| Where are you based? | Your notes say you are US-based and only travelling in India. The form says BlueDot cannot fund people based in India. Answer truthfully. If you are unsure how your travel affects this, the page says to contact BlueDot before applying. Payment must go to an account in a country BlueDot can pay. |
| Where can we learn more about you? | LinkedIn or a personal website |
| **BlueDot eligibility angle** (field 10) | Choose from: course participant, course alum, facilitator, AI safety community member, other. A grant is more likely with a BlueDot or community link. |
| Link to your work | Your choice of what to make public. Options from the repo: the Substack post (URL from the dossier: `spiderishi.substack.com/p/first-make-sure-a-fix-can-work`; not opened by me), the anonymous artifact (`docs/anonymous-artifact.md`), or the GitHub repo (whether it is public is **UNVERIFIED**). |
| Public sharing and public URL | Your choice; "with my name" is pre-selected. |
| Share with other funders | Your choice; "Yes" is pre-selected. |
| Why you | Background, skills, track record; a CV link if you want one. |
| What you would do without the grant | Facts about your own funds. |
| Stipend for your time | Your decision; not in any tier. |
| Other applications to disclose | The ones you actually send. |
| **Payment details** | Given later in BlueDot's claims portal, after approval. Never in this draft. |
| Tax | The dossier §11c says grants are likely taxable for a US person; check with a tax adviser. |

---

## 10. Claim-rule check

| Rule | Status in this draft |
|---|---|
| Never claim that practitioners ask whether attribution is worth its compute | Not claimed. The draft states the question as ours. |
| Never call round 1 "classifiers fail" | Worded only as a finding about a fixed-size top-K removal rule; the threshold rule is marked untested. |
| Do not present the old framing as the plan | The plan is the adopted direction (benign erosion, data-fix menu, diagnosis charged in full-run equivalents, side-effect prediction co-primary). Attribution is one diagnostic among four. |
| Novelty only as "the combination" | Stated as a combination; SafeTune (2609.22153) and DataRx (2608.04322) cited as the closest work. |
| Development evidence labelled | Yes: §3 field 13 and §4. |
| Kill-test outcome not guessed | Placeholders only. |

---

## 11. UNVERIFIED items

1. The **ICML 2027 deadline** (about 16 Jan abstract, 22 Jan paper) and the **NeurIPS 2027** date (about mid-May): estimates from the reframing proposal, not official.
2. **Qi et al. 2023** (and He et al. 2024) erosion numbers: from fetch summaries; FOCUS.md requires a full reading before citing.
3. **SafeTune and DataRx** details (one seed, no data fixes; no removal, no costs): from fetch summaries in the reading list; check the PDFs.
4. **Kim et al.** 16% → about 5%: from the reading list; not read.
5. **Whether BlueDot still excludes general AI subscriptions** (the Nov 2025 rule); affects the $800 AI-tools line.
6. **AI-tool prices** behind the dossier's $800–1,200 estimate.
7. **Human audit cost** ($0.80 per answer implied by the dossier's $800 per 1,000): no quote.
8. **Travel cost** (about $3,000): the dossier's estimate.
9. **Development, confirmation, engineering and second-family costs:** estimates from the reframing proposal §4 and the positioning review §5, not measurements.
10. **Whether BlueDot can cover kill-test costs already spent** before approval.
11. **Whether the GitHub repo is public**, and the Substack URL (from the dossier; not opened).
12. **The Microsoft "review your training data set and resubmit" wording**: from the dossier §1a (checked by another chat on 6 Oct; not opened by me).
13. Total GPU spend to date beyond the ledger's $153.48 (the ledger was built 5 Oct 22:17 UTC; the v2 positive control added about $20; re-run the ledger for an exact figure).

---

## 12. Dossier sections now out of date

These sections of [2026-10-05-grant-evidence-dossier.md](2026-10-05-grant-evidence-dossier.md) still use the old framing or old facts. I did not edit the dossier.

| Section | What must change |
|---|---|
| **Title** ("decision value of training-data attribution for safety data edits") | Use the adopted working title, *Diagnose or Retrain? Compute-Matched Decisions for Repairing LLM Safety After Benign Fine-Tuning*. |
| **§1 one-paragraph pitch** | It asks whether attribution leads to better fix decisions; replace with the benign-erosion question (which fix, and how much diagnosis), attribution as one of four diagnostics. |
| **§1 "Grant version (3 sentences)"** | Old framing ("which signal leads to better fixes for the money"); replace with this draft's §2 pitch. |
| §1a "What the evidence implies for the design" | Marked "not yet decided"; these points are now adopted, so update the status. |
| **§2 research question and novelty** | The question, "Our distinct contribution", "The motivation" and "Planned framing" (claim now: attribution as a decision input) are the 2 Oct framing; replace with the adopted question, novelty "as a combination", and SafeTune, DataRx and Xiao and Aranguri as the closest work. |
| §3 preliminary results | "Interpretation for reviewers" argues for decision value; reframe around "fixes have side effects"; say v2 is base-model development evidence and the anchor will be rebuilt on the aligned model; note that v2's rules were approved before the runs but never formally frozen; add the Stage 0 row. |
| §4 methodological strengths | "Frozen protocols before outcomes" overstates v2 (approved, not formally frozen); say so. |
| §5 infrastructure | Engine test count 269 → 311 (3 CUDA-only skips) at the 6 Oct integration; add the kill-test run kit and Stage 0 engine. |
| §6 data, models and licences | Main policy model is now Qwen2.5-1.5B-Instruct; add Dolly-15k (CC BY-SA 3.0), Alpaca (CC BY-NC 4.0) and GSM8K (MIT); OLMo is a stretch goal, not a planned replication. |
| §7 measured costs | Add the Stage 0 measured cost when known; "efficiency fixes … to be measured" is now measured ($3.96 per v2 run); note the ledger predates the v2 positive control. |
| **§8 budget tiers** | Built for the old study ($5–6k / $14k / $22k with Olmo 3 7B, a 32B check and travel); replace with the kill-test-first tiers in this draft's §6 ($3,050 / $6,000 / $10,950). |
| §9 risks | Old risks (classifier unbeatable; contaminated setting as the headroom fix); add no erosion at 1.5B LoRA, diffuse erosion, cheap non-data repairs (claim limited to data-only users), the default add arm being enough, hidden misalignment, judge failures on incoherent outputs. |
| **§10 timeline** | Old six-step plan ending in "ICML/ACL or a workshop"; replace with the 15-week ICML 2027 plan (kill test first, freeze in week 9, confirmation in weeks 10–11) and the NeurIPS 2027 fallback. |
| §11a BlueDot | Update with the 6 Oct page: form questions (§1.2), average decision 4 days, 9 in 10 within 13 days, 938 grants and $2.6M given; mark "about 5 working days" and the $50–1,500 range as the Nov 2025 programme; the checklist rows point to the outdated §§1, 8 and 10, and "safety relevance … as round 1 showed" must use the top-K wording and the v2 side-effect result; replace the "$5–10k for the development stage" recommendation with this draft's staged $6,000. |
| §11c suggested order | "Use the dossier's pitch" → use this draft's pitch and budget. |
| §12 deliverables | Add per-diagnostic costs in full-run equivalents and the menus × seeds × outcomes × costs table; add Dolly's share-alike licence to the data-release terms. |
| "Sources inside this repository" | Add FOCUS.md (adopted direction), the reframing proposal, the kill-test design, the v2 results, the cost ledger, the reading list v2 and this draft. |
