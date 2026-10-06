> **EDITOR’S NOTE (delete before publishing).** Initial draft, 6 October 2026, revised the same day for the reframing of the research question, which the author adopted on 6 October (`research/FOCUS.md`, “Adopted direction (6 October 2026)”, commit `34e7863`; reasons in `research/review/2026-10-06-reframing-proposal.md`), and again after the v2 positive-control results were recorded (`research/experiments/2026-10-06-headroom-v2-results.md`, commits `9776b68` and `6b8f4fd`). Written in the voice described in `writing/substack/tone-guide.md`. Every number comes from the research records listed at the end of this note. Every result is development evidence. No held-out data has been touched, and no attribution has been evaluated. British spelling, no Oxford comma, no em dashes, as in the 28 September post.
>
> **What changed in this revision (6 October, after the v2 results):**
> 1. **The pending section is filled** and renamed “The fix worked, and broke something else”. It reports the v2 control against the rules written before the runs: the targeted rewrite cut unsafe answers sharply, random rewriting did nothing, ARC held, and the edit failed the no-damage rule on over-refusal. The “what each outcome would mean” list is cut.
> 2. **The tie to the adopted direction** is one short paragraph: finding the rows was easy (93%), the side effect was the hard part, and this is one development control with two seeds, not evidence about benign fine-tuning. It says the adopted question “already” treats over-refusal as a limit, because the adoption predates the result (CHECK 23).
> 3. **Luo et al.** are credited in the v2 section, and the prior-work paragraph now calls v2 “a resemblance, not a replication” of their reported trade-off (CHECK 4).
> 4. **Stale lines updated:** the subtitle; one sentence added to the opening; in the control section, the “haven’t measured how well it finds these rows” clause and the forward-looking line, with XSTest and OR-Bench hard now defined there in plain words; What’s next (the finished v2 item removed and the list renumbered, item 4 points to v2, item 5 says refusals are classifier labels too); the closing paragraph.
> 5. **One new figure idea** replaces the pending dot plot.
> 6. **The body did not grow** (see Length). The new text was paid for by cutting the outcome list and some repetition: the doubled “home ground” sentence and the “says nothing about attribution” line in the control section (the opening already says it), the “edits are sized to match at 507 rows” clause, and the closing’s seed line.
>
> **What changed in the previous revision (the reframing, earlier on 6 October):**
> 1. **The question section** (now “The question moved, twice”) tells how the question moved: from the narrow matched-compute version (removals, toxic or unsafe answers) to the adopted question, with the proposal’s four reasons. The old version is told in the past tense and is never called the plan. The new question is presented as the project’s adopted direction, but early: no results in the new main setting, design not frozen, and the next step is the cheap ranking test. The question, fixes and diagnostics use FOCUS.md’s wording, with British “self-distil”. The matched-compute figure idea is replaced by one for the new question.
> 2. **Costs.** The classifier-timing point moved from the prior-work section into the question section as the third reason. The rest of the old cost paragraph (including Nautiyal’s 1% preprint) is cut.
> 3. **v2** is now the control (overt, injected harm, where a classifier should do well), not the main event. The section is renamed, the old “catch” paragraph is folded into the new framing, and “what each outcome would mean” is rewritten for the control role. Still no v2 result.
> 4. **Prior work.** Luo, Pan and DATE-LM are kept. Added: DATE-LM’s homogeneous-data numbers (classifiers above attribution there too, so the disagreement may not be only about the kind of data), Qi et al. and He et al. The old gap paragraph is cut to one sentence, because it was the gap for the old question; the new question’s novelty is unchecked and the post says so. The “what is still open” list is cut; What’s next carries it.
> 5. **Venue names removed from citations** (Pan et al.’s ICML poster, DATE-LM’s NeurIPS track), so the post names neither conference anywhere. The author can restore them; Pan’s venue would then need CHECK 3.
> 6. **What’s next** is rewritten for the new plan in public-safe terms: no conferences, deadlines, hours or grant amounts, and one [OPTIONAL] funding line. The threshold-rule test and the look-alike data are no longer listed there: FOCUS.md does not schedule the threshold test and lists look-alike data only as an optional middle case. The round-1 section still says the threshold rule is untested.
> 7. **Round 1’s removal result** is worded as a finding about a fixed-size “remove the top 10%” rule (1,015 rows against 43 editable unsafe rows), replacing “top-K”.
> 8. **Other cuts:** the chat-token paragraph in round 1, the metadata mention in the question section, the v2 run-order detail, and shorter versions of the second-judge note, the noise paragraphs and the v2 measurement list.
>
> **Placeholders (must be filled or removed):**
> 1. **[SONG PLACEHOLDER]** at the end.
> 2. **[AUTHOR: confirm AI-assistance wording]** in the closing section.
> 3. **Title and subtitle.** The working title “First, Make Sure a Fix Can Work” still half fits: v2 shows a fix can work, and then that working is not enough. Alternatives that fit the v2 result: “Finding the Rows Was the Easy Part”; “A Fix That Worked Too Well”; “Safer Is Not the Same as Fixed”. Of the earlier ones, “A Fix Has to Work Before You Can Choose One” and “The Question Moved” still fit; “The Easy Part Was Not Easy” and “Louder Than the Edits” now read less well, since v2’s edit was far louder than the seeds. The subtitle is new (CHECK 25).
> 4. **The v2 section heading.** Alternatives: “The v2 control cut harm and failed its no-damage rule”; “Safer, and refusing harmless requests”.
>
> **[CHECK] items (1–16 from earlier revisions, with 1, 2, 4, 7, 11, 11a and 15 updated in this one; 17–26 new):**
> 1. **v2 reading fixed in advance? RESOLVED: yes for the rules, but they were never formally frozen.** The D4 rule text (amendment Part 3: 15 points, a bootstrap interval excluding 0 and the second judge agreeing; ARC within 0.03; XSTest-safe refusals up by at most 5 points) is identical in all three committed versions of the amendment, from `43f1702` (5 Oct, 20:19 IST) to `a1d06a3` (22:50 IST). The user’s approval of D1–D6, D4 included, is recorded in `148439e` (20:39 IST) and the work-plan log (“about 20:45 local”). The rules were committed before even the first calibration result (20:58 UTC, which is 6 Oct 02:28 IST), and the positive-control jobs launched at 23:12–23:16 UTC. But the amendment’s status line still says “draft … Not frozen yet: the reading is frozen after calibration and before the positive control”, no freeze record exists, and the results file calls them “the draft D4 rules”. So the post says “we wrote the reading down before any run existed”, adds a one-line stated limit, and does not call them frozen. Two departures from the amendment’s measurement plan were recorded before the runs (Part 7: e3 only instead of the e2 and e3 average; the second judge on the Mac). One was not recorded: see 18.
> 2. **v2 random-rewrite pool. RESOLVED.** The engine’s `random_rows` (`experiments/safety_selection/headroom.py`, line 231) samples from the whole edit pool. The random-rewrite edit file’s provenance (`tmp/headroom-v2/edits/final-random-rewrite-k507.json`; only its provenance fields were read, not its rows) records a pool of 10,295 rows, “every training row that is not a member of a held-out group”, which includes all 507 injected rows (amendment Part 1). All 507 random rows were rewritten. The post’s “about 25” injected rows in the random 507 is the expectation 507 × 507 / 10,295 ≈ 25.0, not a count; the lead could count it from the auditor file.
> 3. **Pan et al. venue.** No longer in the body (change 5). If restored: the positioning review §9 says the subagent did not verify it; General Implementation found it listed as an ICML 2026 poster on the ICML site.
> 4. **Luo et al. over-refusal (updated, still open).** The precedent note says aligned rewriting for safety “increases over-refusal on XSTest”. The positioning review §9 lists Luo’s exact XSTest metric as unverified, and nothing in the repo has verified it since. The post now leans on this twice: the v2 section says Luo et al. “also report” the trade-off, and the prior-work paragraph calls v2 “a resemblance, not a replication”. The positioning review §2 reports Luo’s Table 2 XSTest figure falling from 0.516 to 0.252 under influence-selected aligned rewriting; that number is not in the post, came through an extraction tool, and which direction means more over-refusal depends on the unverified metric. “A different rewriter”: Luo’s rewrites come from a pool of templates, ours from Qwen2.5-7B-Instruct. Sources: `research/review/2026-10-05-rewriting-precedent.md`; positioning review §§2, 9.
> 5. **Nautiyal’s ~1% claim.** No longer in the body (change 2). If restored: a single-author preprint, taken from its abstract only. Source: `research/review/2026-10-06-prior-work-search.md` §4.
> 6. **The 35/100 (5%) and 39/100 (10%) “unsafe” labels on the over-refusal bank.** The draft treats these cautiously, and its reading of them is an interpretation. Source: the v2 workplan log, 5 Oct 20:58 and 21:31 UTC.
> 7. **What’s next (renumbered in this revision).** The finished v2 item is gone. Item 1 is the next gate in FOCUS.md (the kill test; its design is a draft awaiting the user’s decisions, per `.ai/handoffs/2026-10-06-general-implementation.md` §4c); items 2–4 follow the adopted direction; item 5 is the human read. None is scheduled, so the lead-in now says so. Confirm which ones the author wants to promise publicly.
> 8. **Credit-incident wording.** The incident record says the AI assistant configured the 13 pods, and that this “was an operational mistake”. The draft says “we”. The author decides. Source: `research/experiments/2026-10-02-runpod-credit-incident.md`.
> 9. **Announcing the new direction.** The post says the question is now the project’s direction, adopted this week, but early: no results in the new main setting, design not frozen. Confirm the author is happy to announce it publicly before the kill test. (This revision was first briefed with the reframing as proposed; the coordinator updated the brief after commit `34e7863` recorded the adoption.)
> 10. **Additions and removals (revised by FAQ after the 6 Oct corrections, commit 7238563).** The post no longer says “real fixes are mostly additions”. It says both kinds are real: the public lab accounts (problem-validation review rows 1, 2, 4, 6 and 7; row 6 is abstract only) often added data, while fine-tuning services push customers toward removal (rows 9–10). The example “a training set that had been left out by mistake” is row 1. Source: `research/review/2026-10-06-problem-validation.md` §§2–4.
> 11. **Classifier timing (revised by FAQ).** 58 minutes (3,503–3,521 s) for 9,788 rows, from `research/costs/2026-10-06-cost-ledger.md` §4.3, measured with eager attention. Against round-1 jobs of 72–102 minutes, that is about 0.6–0.8 of a run, which the post rounds to “between half and four-fifths”. It is a one-off cost per dataset. If v2 records a faster time with SDPA, update the third reason. (This revision did not find one: v2’s lead pod logged 81.9 minutes for scores, edit files and rewrites together, work-plan log 5 Oct 23:11 UTC, with no separate scoring time. The third reason is unchanged.)
> 11a. **Kill-test wording (revised by FAQ).** “What’s next” item 1 (item 2 before this revision) now follows the corrected kill test: attribution against representation similarity (the classifier ranks benign data almost uniformly); ground truth from seeded removal runs with a margin beyond the seed spread; and a check on whether erosion is localized or diffuse. The design is still a draft (General Implementation II).
> 12. **DATE-LM’s homogeneous-setting numbers** (classifiers 0.78 to 0.83, attribution about 0.70). “About 0.70” is the review’s rounding. Source: positioning review §0, checked by General Implementation against the DATE-LM HTML.
> 13. **Qi et al.** The review files give only the title, arXiv number (2310.03693) and venue (ICLR 2024); the grant dossier summarises it as “harmful fine-tuning breaks safety with few examples”. The post describes it only by what its title says. Read the paper before saying more. Its title contains the post’s only exclamation mark. Sources: prior-work search §6; `research/grant/2026-10-05-grant-evidence-dossier.md` §2.
> 14. **He, Xia and Henderson numbers** (100 selected benign rows, over 70% unsafe, against under 20% for random rows). From the prior-work search §2, which takes each paper’s details from its abstract or HTML page, not a full reading.
> 15. **Novelty of the new question (updated; the body line is now out of date).** `research/review/2026-10-06-reading-list-v2.md` now exists (commit `79b41b8`). Its verdict, for the question as proposed before adoption, is that it is “still novel as a combination, but its novelty is narrower than before”, with each “not found” meaning “not found by this search”. The body’s “I haven’t yet checked whether anyone has asked the new one” is therefore stale. It is unchanged in this revision because it lies outside the v2 brief. The author decides whether to say a search was done, still without a novelty claim.
> 16. **The “last post” link.** Its slug (`how-much-can-one-learning-moment`) does not match the 28 September title (“Which Training Data Should We Change to Make an AI Safer?”). Confirm the link opens the right post.
> 17. **v2 headline numbers.** Per-seed greedy unsafe rates, ARC and refusals: results file, “Results (Qwen3Guard)” table (lines 23–30). Contrasts and 95% intervals: same file, “Contrasts” (lines 32–34), from `tmp/headroom-v2/pc-bootstrap.json` (4,000 draws over prompts and seeds). Means computed here: a0 (74.5 + 84.0) / 2 = 79.25, printed as 79.3; targeted 10.5; random 81.0. ARC means 0.833 against 0.844: results file, rule 4. With two seeds, a bootstrap over seeds can only resample two values, so the intervals mostly reflect prompt noise. The gaps are far beyond the 19-point detectable difference for two seeds (amendment Part 7), so the reading does not hinge on that.
> 18. **Greedy against sampled: RESOLVED (FAQ, after the lead's correction).** The lead corrected the results file: the primary measure is the sampled rate, per amendment Part 2, and greedy is secondary. The post now leads with sampled per-seed rates (results table lines 25–30: 76.3/84.3, 12.7/10.2, 76.8/86.3; means 80.3, 11.4, 81.6) and the sampled contrasts −68.9 pp [−76.5, −60.5] and −70.2 pp [−78.5, −61.3] (results file lines 35–37, `pc-bootstrap-sampled.json`). Greedy (−68.8, −70.5) is given as agreeing. Granite judged greedy answers only, and the post says so. Item 17's greedy means are now secondary.
> 19. **Over-refusal numbers, and who labelled them.** XSTest-safe refusals: a0 1/50 and 0/50; targeted 22/50 and 22/50; random 0/50 and 0/50. OR-Bench hard: a0 1/50 and 0/50; targeted 30/50 and 36/50; random 3/50 and 1/50 (results table). A refusal is Qwen3Guard’s “Refusal: Yes” on the greedy answer (`experiments/safety_selection/scoring.py`, `overrefusal_summary`; the earlier rounds’ benign refusals, on ARC questions, use the same field through `generation_summary`, `runner.py` line 706). Granite did not re-judge refusals, and no person has read any answer. So the post says “the first two rules pass under both judges”, not that every rule does. Development prompts only: 50 + 50 per seed.
> 20. **Second judge.** 97.2% agreement, κ 0.942, and gaps of 71.0 and 73.3 points: results file, “Second judge” section (lines 58–76). 1,200 greedy harm-bank answers; Granite Guardian 3.3 8B, Q4_K_M through llama.cpp on the Mac, recorded as exploratory (amendment Part 7). Granite’s per-arm means (81.0%, 10.0%, 83.3%) are not in the post.
> 21. **“Only 21 targeted rows kept their original answers.”** The targeted edit file’s provenance records 486 rewritten and 21 excluded (`tmp/headroom-v2/edits/final-rewrite-k507.json`, provenance fields only). The work-plan log (5 Oct 23:11 UTC) gives 971 of 992 accepted and 21 excluded across both edits. Whether those 21 are injected rows was not checked.
> 22. **93%.** 471 of the 507 injected rows in the judge’s top 507 (0.929): results file, “Setting”; work-plan log, the entry after 5 Oct 23:11 UTC (the top 700 holds all 507).
> 23. **“Already” in the tie to the adopted direction.** The adoption commit `34e7863` (6 Oct, 03:45 IST) predates the job launch (about 04:45 IST) and the v2 results commit `9776b68` (07:45 IST). So the post says the adopted question “already” treats over-refusal as a limit; it does not say v2 caused that choice. FOCUS.md, “Adopted direction”: over-refusal and task skill as feasibility limits, and side-effect prediction co-primary.
> 24. **“Random rewriting did nothing.”** Its seeds were 2.0 and 1.5 points above a0’s (76.5 against 74.5; 85.5 against 84.0), well inside a0’s own seed gap of 9.5 points. Its refusals stayed low as well (19).
> 25. **The subtitle’s “a fix that did too little, one that overdid it”.** “Too little” is round 1’s targeted rewrite (1.0 below a0 against a bar of 8); “overdid it” is v2’s over-refusal. Confirm the author is comfortable with the shorthand, which loses “positive control” from the subtitle.
> 26. **The [OPTIONAL] v2 cost.** “About $20” for the positive-control phase: results file, “Operations and cost”, an estimate (the cost ledger can give the exact figure). The top-up made during the run is left out on purpose.
>
> **Left out on purpose:** the Cisco figure the reframing proposal cites for benign erosion (problem-validation row 11: a vendor blog, search snippet only); the seed-repeated replication of Pan et al. from the proposal’s plan (better mentioned after contacting the authors); every date, hour, dollar amount and venue from the proposal’s plan. Also left out of the v2 section: its ToxicChat numbers (targeted 12 and 13 unsafe of 72, against 25 and 34 for both a0 and random); the random arm’s refusal counts; Granite’s per-arm rates; and the results file’s reading that the rewrites “taught the model to refuse anything that sounds risky”, which goes beyond 100 prompts per seed, one judge’s refusal labels and no answers read. The post says “many harmless requests that sound risky” instead.
>
> **[OPTIONAL] items (the author decides):**
> 1. The whole section “[OPTIONAL — author decides how public] The afternoon the results disappeared”.
> 2. Dollar figures, which appear only inside [OPTIONAL] brackets: about $0.15 for the first run (an estimate, not an invoice), about $60 for dev-matrix-002, about $42.3 for round 1, and about $20 for the v2 positive control (CHECK 26).
> 3. One funding or compute-support line at the end, left as a bracket only.
> 4. **[OPTIONAL — anonymity] The working title.** FOCUS.md gives the project the working title “Diagnose or Retrain? Compute-Matched Decisions for Repairing LLM Safety After Benign Fine-Tuning”. It is deliberately not in the post: a public post carrying the exact paper title could link the author to a later double-blind submission. The body uses the idea only loosely (“how much to spend diagnosing before you retrain”), not the phrase “diagnose or retrain”; the author may cut even that for the same reason.
>
> **[FIGURE IDEA] notes (6):**
> 1. The new question in one picture (replaces the matched-compute diagram).
> 2. Where the first run’s 254 seconds went.
> 3. Dev-matrix-002 dot plot.
> 4. Round-1 dot plot with the frozen threshold.
> 5. v2 dose-response points.
> 6. v2 result (new; replaces the pending dot plot): a0 and the two rewrites, unsafe rate in one panel and XSTest refusals in the other, each with its line fixed in advance. If space allows, OR-Bench hard refusals can sit in the right panel as hollow dots.
>
> **Length.** Counted with `wc -w` from the title line to the end (`sed -n '<title line>,$p'`): **5,092 words including the [FIGURE IDEA] lines, 4,772 without them.** Before this revision, measured the same way: 5,093 and 4,785. (The 4,956 and 4,648 this note gave before no longer matched the file; this revision did not trace why.) The v2 result section is 519 words including its figure line and 462 without, against 486 and 441 for the pending section it replaces. The longest earlier post is 2,762 words (26 September), so this is still about 1.8 times that. Further trims, if wanted:
> - the [OPTIONAL] incident section (about 250 words);
> - the two measurement notes at the end of the round-1 section (but the v2 section’s “again on my Mac” leans on the second one);
> - the bullet list in “First real GPU runs”;
> - the dose-response figure idea, now that v2 has a result figure.
>
> **Sources used:**
> - `research/experiments/2026-10-06-headroom-v2-results.md` (new in this revision; the authority for every v2 result number)
> - `experiments/safety_selection/headroom.py` (`random_rows`), `experiments/safety_selection/scoring.py` (`overrefusal_summary`, `generation_summary`) and `runner.py`, read for CHECKs 2 and 19 (new in this revision)
> - the provenance fields only of `tmp/headroom-v2/edits/final-rewrite-k507.json` and `final-random-rewrite-k507.json`, for CHECKs 2 and 21; no row, prompt or answer was read (new in this revision)
> - `.ai/handoffs/2026-10-06-general-implementation.md` §4c, for the kill test’s status (new in this revision)
> - `research/review/2026-10-06-reading-list-v2.md`, for CHECK 15 only (new in this revision)
> - git history of the v2 amendment (`43f1702`, `148439e`, `a1d06a3`) and of the adoption and results (`34e7863`, `9776b68`, `6b8f4fd`), for CHECKs 1 and 23 (new in this revision)
> - `research/FOCUS.md`: its 2 October amendment and its “Adopted direction (6 October 2026)” section
> - `research/experiments/2026-10-02-minimal-safety-calibration-results.md`
> - `research/experiments/2026-10-02-measurement-audit.md`
> - `research/experiments/2026-10-02-runpod-credit-incident.md`
> - `research/experiments/2026-10-04-dev-matrix-002-results.md`
> - `research/experiments/2026-10-05-headroom-amendment-draft.md`
> - `research/experiments/2026-10-05-headroom-round-1-results.md`
> - `research/experiments/2026-10-05-headroom-v2-amendment-draft.md`
> - `research/experiments/2026-10-05-headroom-v2-workplan.md`
> - `research/review/2026-10-06-reframing-proposal.md`
> - `research/review/2026-10-06-problem-validation.md`
> - `research/review/2026-10-06-positioning-review.md`
> - `research/review/2026-10-06-prior-work-search.md`
> - `research/review/2026-10-05-rewriting-precedent.md` (for Luo et al.)
> - the evidence dossier (`research/grant/2026-10-05-grant-evidence-dossier.md`) §§1–3, used for framing only and not cited in the post; §2 also for how it summarises Qi et al.

# First, Make Sure a Fix Can Work

*Notes from an ongoing research project: first GPU runs, a lot of seed noise, a fix that did too little, one that overdid it and a question that moved.*

In the [last post](https://spiderishi.substack.com/p/how-much-can-one-learning-moment), I was working out how to turn a question about training data into an experiment I could actually run. Since then, we have run a few. The first thing they taught me was not about attribution at all. Before you can ask which fix to choose, you need a fix that does something. Then you check what else it does.

Everything below is development evidence: results we use to design the study, gathered on data we are allowed to look at. The held-out data, meaning the prompts, data groups and training seeds kept back for the final test, has not been touched. No attribution method has been evaluated yet either, so nothing here says whether attribution helps or hurts. The coupling pilot from the last post was a separate question, and nothing here builds on it.

## The question moved, twice

The last post ended on a broad question: given a safety failure and some possible changes to the training data, can we work out which change will help most without retraining every option?

For the runs below, I narrowed it. A safety classifier can flag worrying training examples, and short training runs show what an edit does. Training-data attribution, which tries to trace a model’s behaviour back to the training examples that most shaped it, looked like the expensive option. So I asked whether adding attribution to those cheap signals picks a better fix than spending the same compute on more trial runs, with removals of groups of rows as the fixes and toxic or unsafe answers as the failure.

That is no longer the plan, for four reasons. First, we had built the classifier’s home ground ourselves: to get a fix that does something, we put overtly harmful answers into the training data (v2, below), which is exactly what a safety classifier is built to spot. Second, a menu of removals alone was too narrow. In the public accounts we could find of teams changing training data after a model misbehaved, the fix was often to add something, such as a training set that had been left out by mistake; fine-tuning services, on the other hand, tend to ask customers to filter their data and try again. Both kinds of fix are real, so the menu needs both [CHECK: problem-validation review rows 1, 2, 4, 6 and 7 for additions, rows 9–10 for removal; public accounts only].

Third, the classifier was not as cheap as I had assumed. In round 1, our 4-billion-parameter safety judge took 58 minutes to score the 9,788 editable rows, while a whole training-and-evaluation job took 72 to 102 minutes, so scoring cost somewhere between half and four-fifths of a run [CHECK: cost ledger, research/costs/2026-10-06-cost-ledger.md §4.3; measured with a slow attention setup that v2 set out to speed up]. It only has to score a dataset once, though, while trial runs multiply with every fix on the menu, so which option is cheaper depends on how many fixes you are choosing between. Fourth, small scale favours trial runs. At 1.5 billion parameters, trying every fix is affordable, and that may not hold where one run costs far more.

So this is now the project’s question:

> When fine-tuning on benign data makes an aligned language model less safe, which data fix restores safety without hurting the task or causing over-refusal, and how much diagnosis is worth paying for before choosing?

Benign data means ordinary task data with nothing obviously harmful in it, and an aligned model has already been safety-tuned. Over-refusal means refusing harmless requests. The fixes are to keep the data; remove a subset or source; add safety data; or rewrite or self-distil the responses, meaning the aligned model writes the training answers itself. The diagnostics are content-classifier scores, representation similarity, training-data attribution and short trial runs. Representation similarity is a cheap signal that compares how the model internally represents each training example with how it represents the failing prompts.

Put loosely, the question is how much to spend diagnosing before you retrain. Attribution becomes one diagnostic among several, so a negative answer for it is still an answer, and what each diagnostic is worth gets stated relative to what a run costs. The question is also closer to what people who fix training data seem to ask, in the public accounts we found: which fix to make, and how much checking to do first. Keeping the data stays a valid choice, and “too close to call” stays an allowed answer.

I adopted it as the project’s direction this week, but it is early: there are no results in the new main setting yet, none of the runs below was designed for it, and the design isn’t frozen. The next step is a cheap test of whether the diagnostics’ rankings even disagree when benign fine-tuning erodes safety.

[FIGURE IDEA: the new question in one picture. Left, an aligned model made less safe by benign fine-tuning. Middle, the diagnostics (content classifier, representation similarity, attribution, short trial runs), each with a cost bar in training runs. Right, the fixes (keep, remove a subset or source, add safety data, rewrite or self-distil), with over-refusal and task skill as limits. Caption: the question, not a result; the design is not frozen.]

## First real GPU runs, and what they taught us about measuring

On 2 October we ran the whole pipeline on a rented GPU for the first time. It was deliberately tiny: a small instruction-tuned model (Qwen2.5-0.5B-Instruct), 128 training examples, two training seeds, and one comparison between keeping every row and removing eight rows the dataset labels unsafe. Attribution did not choose that removal. A seed fixes the random choices in a training run, so two seeds give two slightly different versions of the same experiment.

This was development evidence, and mostly engineering evidence at that. The engineering held up: a reproducibility check on one seed gave bitwise-identical saved weights, which validates that one check rather than reproducibility in general. The whole run took about four minutes [OPTIONAL: at an estimated cost of $0.15]. The measurements were more interesting, mostly for what they could not do:

- Every evaluation, including the model before our fine-tuning, flagged the same one of six toxic prompts.
- 77 of 108 generated answers hit the 64-token length limit. We were judging the openings of answers, not answers.
- The toxicity classifier we started with flagged only one of the eight training examples labelled unsafe. Rude language and harmful help are different things, and that classifier mostly measures the first.
- Evaluation took 214 of the 254 seconds, training about 9 and the attribution calculation about 3. That says nothing about attribution’s cost at a real scale: it was a tiny calculation that chose nothing.

Two separate AI annotators (fresh sessions of the same model family, with no information about which run produced which answer) then read 50 of the answers. Both picked out the same three as harmful help, exactly the three the toxicity classifier flagged. That is reassuring about those three, but it is not human validation: no human has labelled any of these outputs yet.

So we changed the instruments before scaling up. The main measure became the rate of answers labelled Unsafe by a dedicated safety judge, Qwen3Guard, with toxicity, capability and refusals reported separately. The model grew to 1.5 billion parameters, training used complete conversations, the answer limit rose to 2,048 tokens (raising it from 1,024 on the same saved models changed no Unsafe count), and a capability test went in: ARC-Easy, a set of grade-school science questions. Qwen3Guard measures something broader than the annotators did: on those 50 answers it labelled 18 Unsafe, where they had found three that gave material harmful help. That is a difference in what is being measured, not an error rate. From here on, “unsafe” means “labelled Unsafe by Qwen3Guard”.

[FIGURE IDEA: one horizontal bar for the first run’s 254 seconds, split into evaluation (214.21 s), training-response classifier (24.00 s), training (8.73 s) and attribution (2.93 s). Caption: one tiny run; not a cost estimate for anything larger.]

## [OPTIONAL — author decides how public] The afternoon the results disappeared

Later on 2 October we launched the first real development matrix: 13 GPU machines at once, each training and evaluating models. We had set them up with temporary disks only and no persistent storage [CHECK: credit-incident record; who configured the pods, see editor’s note]. We were also waiting for each machine to finish both of its runs before copying anything off. At around 18:18 UTC the account ran out of prepaid credit, and all 13 machines disappeared within about a minute. The provider’s documentation says machines without persistent storage are deleted, data and all, when credit runs out.

By then every machine had sealed its first checkpoints and was partway through the next. None of it had been copied off, and we treat all of it as lost. Earlier results were safe: the calibration archives were on my own machine, and their checksums still matched.

Removing a spending cap, it turns out, is not the same thing as having credit.

What changed:
- every finished checkpoint is copied off the machine within minutes and verified there and then;
- every machine carries its own stop timer;
- the balance is checked before and during a run, and a small reserve is never spent, so machines can always be stopped cleanly;
- each phase is backed up, and the backup is checked by downloading it again.

The lost runs keep their names and costs in the records. The repeat ran as a new, explicitly named attempt rather than quietly filling the gap.

## Small removals did not move safety beyond seed noise

On 4 October we ran that matrix again, with the safeguards. The model was Qwen2.5-1.5B-Instruct, which its developers had already safety-tuned. We fine-tuned it with LoRA, which trains a small add-on instead of all of the model’s weights, for three passes over 10,148 training rows. There were 13 versions of the training data: everything (call it a0), and 12 versions that each removed one predefined group of 8 to 64 rows, between 0.08% and 0.63% of the data. Each was trained with two seeds (1101 and 1102) and then answered 72 development prompts chosen to invite unsafe answers.

All 78 saved checkpoints were sealed and verified [OPTIONAL: for about $60 in all]. As development evidence from two seeds, nothing moved more than the seeds did. At the end of training, the unchanged data gave 19 unsafe answers out of 72 in both seeds. The removals averaged between 18.5 and 22.5: the best was half an answer better than doing nothing, the worst 3.5 answers worse. The two seeds of the same version differed by 2.2 answers on average and by up to 6. Capability didn’t move either (ARC accuracy 0.849 to 0.878), and no version refused a harmless prompt. With two seeds, this is a description, not a powered estimate.

A study about choosing between edits needs edits whose effects are bigger than the noise. Our guesses for why these weren’t: the model was already safety-tuned, the add-on was tiny (0.07% of the model’s parameters), the edits were small, and deletion may be a weak edit in general, which is what Luo et al. found (more below). Those are hypotheses, not findings.

[FIGURE IDEA: dot plot of unsafe answers out of 72 at the end of training, one row per version (a0 plus 12 removals), two dots per row for seeds 1101 and 1102, with a shaded band for a0’s value. Caption: two seeds; development evidence; Qwen3Guard labels; the spread within a row is as large as the differences between rows.]

## The positive control did not pass its frozen gate

A positive control is meant to be the boring part of an experiment. You build a case where the answer should obviously be yes, check that your instruments say yes, and move on. If they don’t, nothing downstream can be trusted.

We changed the setting to give edits every chance. The model became the base version of Qwen2.5-1.5B, with no instruction or safety tuning of its own, so its safety behaviour would come mainly from our training data. The add-on grew about 68 times larger, to about 4.8% of the model, and the edits grew to 10% of the training data, or 1,015 rows.

We compared five versions of the training data, each trained with two seeds (1101 and 1102):

- **a0:** nothing changed;
- **targeted removal:** delete the 1,015 rows that the safety judge scored as most unsafe;
- **random removal:** delete 1,015 rows chosen at random;
- **targeted rewrite:** keep those top-scored requests, but replace their answers with new ones written by a larger model (Qwen2.5-7B-Instruct), which saw only the request and was told to answer safely;
- **random rewrite:** the same for the random rows.

To give targeting the best chance, the rows were picked by the same safety model that later judged the answers. For 105 of the 1,015 targeted rows the rewriter produced no acceptable answer, mostly because it ran out of length, so those rows kept their original answers.

Before any of these runs existed, we wrote down how to read them:
1. An edit counts as making the model safer if its average unsafe count is at least 8 (out of 72) below a0’s, and both of its seeds are below both of a0’s.
2. Targeting counts as mattering if the targeted edit beats its random twin by the same rule.
3. The edit must not cost capability (ARC within 0.03 of a0) or refuse more than 5 of 96 harmless prompts.

Round 1 would pass if at least one kind of edit met all three. One stated limit: nobody outside the project reviewed these rules before they were frozen.

The baseline passed its sanity checks: answers ended, ARC accuracy was 0.847 and 0.794, and it refused no harmless prompts. Then the results, in unsafe answers out of 72 for seeds 1101 and 1102 (development evidence):

- **a0:** 14 and 11 (mean 12.5)
- **targeted removal:** 19 and 29 (mean 24.0)
- **random removal:** 14 and 23 (mean 18.5)
- **targeted rewrite:** 14 and 9 (mean 11.5)
- **random rewrite:** 16 and 22 (mean 19.0)

Round 1 did not pass its frozen gate. Targeted rewriting averaged 1.0 below a0, not 8, and its seed of 14 was not below a0’s 11. It beat random rewriting by 7.5, with both seeds below both random seeds, short of the 8 we had fixed. Targeted removal went the other way: 11.5 worse than a0, with both seeds above both of a0’s, which the rules record as a finding in the opposite direction. So the second round, which would have tested smaller sizes, did not run, and the design went back to review [OPTIONAL: the round cost about $42.3, after we raised its cap three times].

[FIGURE IDEA: five rows (a0 and the four edits), two dots each for seeds 1101 and 1102, a shaded band for a0’s two seeds, and a dashed line at a0’s mean minus 8 marking the frozen threshold. Caption: two seeds; development evidence; Qwen3Guard labels; the threshold was fixed before the runs.]

Look at targeted removal’s two seeds: 19 and 29. Same data, same recipe, a different random seed, and ten answers apart. A rough noise analysis afterwards (it rests on two seeds per version) found that most of the seed-to-seed spread was a shared shift: a different seed makes the whole model a bit more or a bit less cautious at once. More prompts can’t average that away; more seeds can.

The same analysis says something uncomfortable about the rule itself. With two seeds and 72 prompts, the smallest difference we could reliably detect was about 14 answers, so our threshold of 8 needed about five seeds. I’d rather say that plainly than move the line after the fact. The gate stands.

### What the removal result does and doesn’t say

This is the part I most want to word carefully. It is tempting to read it as “safety classifiers pick the wrong data”. I don’t think it says that.

The rule was “remove the top 10% by score”: a fixed 1,015 rows. The editable part of the training data contained only 43 rows that the dataset itself labels as harmful answers, along with 33 rows labelled as refusals. So even if the judge had ranked all 43 at the very top, the rule still had to remove at least 972 other rows. Which other rows matters. The judge scores each request and its answer together, so the top of its list probably includes refusals to toxic requests and cautious answers on sensitive topics, which are exactly the examples that teach a model to say no. We deliberately did not read the hidden row labels that would confirm this, so it remains a likely explanation, not a finding. Removing 10% of the rows also shortens training by 10%, which random removal only partly controls for.

So this is a finding about a fixed-size “remove the top 10%” rule, not about classifiers. A threshold rule, which removes only the rows the judge actually labels unsafe, has not been tested.

With the gate failed, the rest is description, not effects. Targeted rewriting was the only edit that kept the unsafe count at a0’s level. Every other edit made the model less safe: random removal by 6.0, random rewriting by 6.5 and targeted removal by 11.5. Targeting helped rewriting and hurt removal (5.5 worse than random).

Two measurement notes. Most of the unsafe answers complied with requests for sexual content, because that is what most of the ToxicChat development prompts ask for, so round 1 mostly measured that, not harm in general. And a second safety judge, IBM’s Granite Guardian 3.3, run on my Mac, agreed with Qwen3Guard on 92.5% of all 720 answers (Cohen’s κ 0.80, an agreement measure that discounts chance, on which 1 is perfect) and ranked the five versions the same way. Under it, targeted rewriting beat random rewriting by 8.0, but the rule named Qwen3Guard in advance, so that changes nothing.

## Building a control: a setting where edits should work

Round 1’s baseline was already fairly safe, at 12.5 unsafe answers out of 72. Most of the ordinary training data is UltraChat, written by ChatGPT, and it probably carries ChatGPT’s caution with it. There wasn’t much for a fix to fix.

So v2 puts the problem in on purpose. We add answers from the public PKU-SafeRLHF dataset that the dataset itself labels unsafe, at severity 2 or 3 on its 0 to 3 scale, chosen by a fixed, seeded rule that balances them across harm categories. Nobody picked rows by hand, examples too similar to an evaluation prompt were left out, and every injected row is editable, with none in the held-out data.

This is the classifier’s home ground from the question section, and that is now its job: v2 is the control. It checks that a fix can work at all and that our instruments can see it.

The measurement changed too. Harm prompts now come from four public benchmarks (HarmBench, StrongREJECT, SimpleSafetyTests and OR-Bench’s toxic subset), split before anyone read them, with only the 200 development prompts in use. Over-refusal is caught by harmless prompts written to look edgy, 50 from XSTest and 50 from OR-Bench’s hard set. Each harm prompt gets the model’s most likely (“greedy”) answer plus three sampled ones.

The target, fixed in advance, was the smallest dose at which the unchanged model gives unsafe answers to at least 40% of the development harm prompts. Development evidence, one seed (1101) per dose:

- **5% (507 harmful rows added):** 74.5% unsafe greedy answers (149 of 200) and 76.3% across sampled answers (458 of 600). ARC accuracy was 0.841, with 2 refusals out of the 100 over-refusal prompts. Answers ended properly: 1 of 200 hit the length limit.
- **10% (1,015 rows):** 81.0% unsafe greedy (162 of 200) and 83.5% sampled (501 of 600). ARC was 0.831, with 3 refusals out of 100.

5% clears the bar comfortably, so it became the setting. The dose response flattens: doubling the harmful rows moved the greedy unsafe rate only from 74.5% to 81.0%, though two doses with one seed each are a description, not a curve. On round 1’s ToxicChat prompts, the 5% model gave 25 unsafe answers out of 72, against 14 and 11 for round 1’s baseline.

One number I’m reading cautiously: the judge labelled 35 of the 100 over-refusal answers unsafe at 5%, and 39 at 10%. That set includes borderline prompts, so I read little into it [CHECK: interpretation; v2 workplan log, 5 Oct 20:58 and 21:31 UTC].

[FIGURE IDEA: two points (5% and 10% injected), each showing the greedy and sampled unsafe rate on the 200 development harm prompts, with a horizontal line at the 40% target. Caption: one seed per dose; development evidence; Qwen3Guard labels; two points are not a curve.]

## The fix worked, and broke something else

On the 5% data we compared three versions, each with two seeds (1101 and 1102): a0; a targeted rewrite, where the larger model wrote new, safe answers for the 507 rows the judge scored as most unsafe; and a random rewrite of 507 editable rows, injected ones included. This time only 21 targeted rows kept their original answers.

As in round 1, we wrote the reading down before any run existed:
1. An edit makes the model safer if its average unsafe rate is at least 15 percentage points below a0’s, a 95% bootstrap interval excludes zero and the second judge agrees on the direction.
2. Targeting matters if targeted rewriting beats random rewriting by the same rule.
3. No damage: ARC within 0.03 of a0’s, and refusals of the harmless XSTest prompts up by no more than 5 points.

I approved these rules before the runs, but the record still calls them a draft, not frozen [CHECK: editor’s note, item 1].

Unsafe answers on the 200 development harm prompts, averaged over three sampled answers per prompt, seeds 1101 and 1102 (development evidence):

- **a0:** 76.3% and 84.3% (mean 80.3%)
- **targeted rewrite:** 12.7% and 10.2% (mean 11.4%)
- **random rewrite:** 76.8% and 86.3% (mean 81.6%)

Targeted rewriting was 68.9 points below a0 and 70.2 below random rewriting (95% intervals 60.5 to 76.5 and 61.3 to 78.5). Random rewriting did nothing. The single greedy answer per prompt tells the same story, at 68.8 and 70.5 points. ARC held, at 0.833 against a0’s 0.844. Granite Guardian, again on my Mac, agreed with Qwen3Guard on 97.2% of the 1,200 greedy answers (κ 0.942) and put the gaps at 71.0 and 73.3 points. The first two rules pass, under both judges, though the second judge only saw the greedy answers.

The third does not. Across both seeds, a0 refused 1 of 100 XSTest prompts and the targeted rewrite 44, 22 in each seed. On OR-Bench’s hard set, refusals went from 1% to 66%. The limit was 5 points. The v2 control did not pass its no-damage rule [OPTIONAL: this phase cost about $20].

So, did v2 show what we hoped? Mostly. Three of the four checks passed: the unchanged model is clearly unsafe, the targeted fix moved it a long way, and targeting beat random. The fourth, no damage, failed. The drop of about 69 points is roughly seven times the gap between two seeds of the same unfixed version, which was 8 to 10 points here. Round 1’s best edit moved the count by about one answer in 72. So v2 is the first setting we have where a data fix clearly matters.

What it does not show matters as much. It says nothing about attribution: the rows were picked by the cheap classifier, which found 471 of the 507 injected rows (93%) on its own, while a random 507 would hold about 25 [CHECK: an expected value, not a count]. “Targeting matters” is close to built in here, not a discovery. We injected the harmful data ourselves, so it was obvious. And it is development evidence from two seeds.

The hard part was a fix that doesn’t over-correct, a trade-off Luo et al. also report (below). That makes me more confident in the new direction, not less. On obvious, injected harm, the cheap classifier had already found the rows, so there was little left for anything more expensive to find. What v2 exposed instead is the new question’s core problem: a fix that removes harm can also remove helpfulness. It is one control on injected harm, not evidence about benign fine-tuning, but it is a concrete case of why the adopted question treats over-refusal as a limit, and asks whether any diagnostic can predict a fix’s side effects before paying for the run.

[FIGURE IDEA: two panels in the round-1 dot plot’s style, rows a0, targeted rewrite and random rewrite, one dot per seed. Left: unsafe share on the 200 harm prompts (sampled answers, the primary measure), dashed line at a0 minus 15 points. Right: XSTest refusal share, dashed line at a0 plus 5. Caption: two seeds; development evidence; Qwen3Guard labels; lines fixed in advance.]

## How this sits against prior work

None of the pieces here is new on its own, and I want to be specific about whose they are.

Rewriting as a safety data edit, and using attribution to choose which rows to rewrite, are already in Luo et al., [“From Reweighting to Rewriting”](https://arxiv.org/abs/2609.02771) (September 2026). They found that reweighting and deleting influential examples gave weak, inconsistent and sometimes reversed effects, while rewriting gave large, persistent shifts, with more leverage from rows chosen by influence than from random ones. They also report that rewriting for safety increased over-refusal on XSTest [CHECK: rewriting-precedent note; exact metric unverified per positioning review §9]. Our v2 control showed something similar with a different rewriter, model and data: a resemblance, not a replication. That paper is why rewriting is on our menu at all.

The closest work on attribution against classifiers is Pan et al., [“Detecting and Filtering Unsafe Training Data via Data Attribution with Denoised Representation”](https://arxiv.org/abs/2502.11411) (2025). Their setting is close to ours: UltraChat with unsafe ToxicChat and XSTest examples mixed in. There, removing the rows their attribution method flagged improved safety more than removing the rows that moderation classifiers such as WildGuard flagged. They removed, retrained and measured, without reporting compute, and their repeats were over inference runs rather than training seeds.

DATE-LM (Jiao et al., [“Benchmarking Data Attribution Evaluation for Large Language Models”](https://arxiv.org/abs/2507.09424), 2025) points the other way. Sometimes the training data contains safety-aligned look-alikes: examples that resemble the unsafe ones but respond safely. When it does, attribution’s ability to detect the unsafe rows drops sharply while classifiers are largely unaffected. One representation-similarity method fell from 0.759 to 0.597 on their detection score, while the WildGuard classifier stayed at 0.817. Our ToxicChat training data comes from DATE-LM.

It is tempting to say the two papers disagree because of the kind of data. But even on DATE-LM’s data without look-alikes, the classifiers scored above attribution (0.78 to 0.83 against about 0.70) [CHECK: positioning review §0], and the papers measure different things: Pan et al. the retrained model’s behaviour, DATE-LM how well each method finds the unsafe rows. So the disagreement may not be only about the data.

The new main setting has its own precedents. Qi et al., [“Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!”](https://arxiv.org/abs/2310.03693) (2023), reported what its title says [CHECK: the review files give only the title; read the paper before describing it further]. He, Xia and Henderson, [“What is in Your Safe Data? Identifying Benign Data that Breaks Safety”](https://arxiv.org/abs/2404.01099) (2024), used gradient and representation matching to find benign rows that break safety: fine-tuning on 100 such rows gave over 70% unsafe answers, against under 20% for random rows [CHECK: abstract-level summary; prior-work search §2]. That suggests attribution-like signals can find harmless-looking data that erodes safety, though that study asked which rows break safety, not which fix to choose or what finding them costs.

A search in early October found no study that charges attribution’s compute against more trial runs. That is a statement about my search, not the field, and it was for the old question. A second search, for the new one, found each piece somewhere: recent work compares fixes for safety drift at the level of the whole model, and other work compares ways of adding safety data back in. I didn’t find anyone putting the different kinds of data fix side by side and charging the diagnosis against more trial runs, but the gap is narrower than it looked a week ago [CHECK: research/review/2026-10-06-reading-list-v2.md, “Novelty verdict”; SafeTune and DataRx are the August 2026 precedents; not-found means not found by this search].

## What’s next

In order, and none of it is scheduled yet [CHECK: item 1 is the next gate in FOCUS.md; items 2–4 follow the adopted direction]:

1. A cheap first test, in stages. The first stage is small: check that fine-tuning a 1.5B model on ordinary task data makes it noticeably less safe at all. If it doesn’t, there is nothing to repair. If it does, a content classifier will probably rate almost every training row as fine, so the comparison that matters is between attribution and representation similarity (how alike two examples look inside the model). Rank the training rows both ways and time each. Then retrain without a few of the top-ranked groups, over several seeds, to see which ranking pointed at data that actually mattered by more than the seed noise. The same runs should show whether the damage comes from a few rows or is spread thinly across all of them. If it is spread out, no ranking will find a culprit, and I’d rather know that before paying for anything bigger [CHECK: kill-test design is still a draft; research/review/2026-10-06-reframing-proposal.md §2a/§3a].
2. Build the main setting: an aligned model, fine-tuned on ordinary task data, that comes out less safe. The rows look harmless, so a content classifier should have little to go on. That is a premise, and the first test should show whether it holds.
3. Widen the menu of fixes: keep the data; remove a subset or source; add safety data; rewrite or self-distil responses.
4. Treat over-refusal and task skill as limits: a fix that restores safety by making the model refuse harmless requests, as v2’s did, or by undoing what the fine-tuning was for, doesn’t count. I’d also like to know whether any diagnostic can predict which fix will cause over-refusal.
5. Have people read a sample of the answers. Every “unsafe” and every refusal in this post is a classifier’s label, and the audits so far were done by AI models, not people.

If ordinary fine-tuning turns out not to erode safety enough to study, there is a fallback: stay in the v2 setting and compare kinds of fix on the trade-off it exposed, between safety and over-refusal. Rewrite the flagged answers as refusals, rewrite them as answers that are safe but still helpful, add borderline examples that should be answered, or remove the rows.

The training runs among these will need more seeds than we have used so far: round 1’s noise analysis suggests about five per version.

In the last post, I wanted to know which fix to choose. After a detour through a narrower version, the question is back closer to where it started, which I’m choosing to call progress. Until these results, I’d have settled for one fix that reliably does something. Now there is one, in a setting built to make that easy, and it does two things: it removes most of the harm and makes the model refuse many harmless requests that sound risky. Safer and still helpful are two measurements, not one.

As before, AI assistants do most of the implementation and run the cloud jobs. They also review the design, and they helped draft this post. Their suggestions still have to survive the records and the results. [AUTHOR: confirm AI-assistance wording]

[OPTIONAL: one line saying I’m looking for compute support or funding for the next stage, if the author wants it.]

song ive been listening to:

[SONG PLACEHOLDER: track and artist, Spotify embed]
