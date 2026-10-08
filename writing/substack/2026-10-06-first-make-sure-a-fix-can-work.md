# First, Make Sure a Fix Can Work

*Notes from an ongoing research project: first GPU runs, a lot of seed noise, a fix that did too little, one that overdid it and a question that moved.*

In the [last post](https://spiderishi.substack.com/p/how-much-can-one-learning-moment), I was working out how to turn a question about training data into an experiment I could actually run. Since then, we have run a few. The first thing they taught me was not about attribution at all. Before you can ask which fix to choose, you need a fix that does something. Then you check what else it does.

Everything below is development evidence: results we use to design the study, gathered on data we are allowed to look at. The held-out data, meaning the prompts, data groups and training seeds kept back for the final test, has not been touched. No attribution method has been evaluated yet either, so nothing here says whether attribution helps or hurts. The coupling pilot from the last post was a separate question, and nothing here builds on it.

## The question moved, twice

The last post ended on a broad question: given a safety failure and some possible changes to the training data, can we work out which change will help most without retraining every option?

For the runs below, I narrowed it. A safety classifier can flag worrying training examples, and short training runs show what an edit does. Training-data attribution, which tries to trace a model’s behaviour back to the training examples that most shaped it, looked like the expensive option. So I asked whether adding attribution to those cheap signals picks a better fix than spending the same compute on more trial runs, with removals of groups of rows as the fixes and toxic or unsafe answers as the failure.

That is no longer the plan, for four reasons. First, we had built the classifier’s home ground ourselves: to get a fix that does something, we put overtly harmful answers into the training data (v2, below), which is exactly what a safety classifier is built to spot. Second, a menu of removals alone was too narrow. In the public accounts we could find of teams changing training data after a model misbehaved, the fix was often to add something, such as a training set that had been left out by mistake; fine-tuning services, on the other hand, tend to flag problems in the data and tell customers to fix it and try again, which in the accounts we found meant filtering it. Both kinds of fix are real, so the menu needs both.

Third, the classifier was not as cheap as I had assumed. In round 1, our 4-billion-parameter safety judge took 58 minutes to score the 9,788 editable rows, while a whole training-and-evaluation job took 72 to 102 minutes, so scoring cost somewhere between half and four-fifths of a run. It only has to score a dataset once, though, while trial runs multiply with every fix on the menu, so which option is cheaper depends on how many fixes you are choosing between. Fourth, small scale favours trial runs. At 1.5 billion parameters, trying every fix is affordable, and that may not hold where one run costs far more.

So this is now the project’s question:

> When fine-tuning on benign data makes an aligned language model less safe, which data fix restores safety without hurting the task or causing over-refusal, and how much diagnosis is worth paying for before choosing?

Benign data means ordinary task data with nothing obviously harmful in it, and an aligned model has already been safety-tuned. Over-refusal means refusing harmless requests. The fixes are to keep the data; remove a subset or source; add safety data; or rewrite or self-distil the responses, meaning the aligned model writes the training answers itself. The diagnostics are content-classifier scores, representation similarity, training-data attribution and short trial runs. Representation similarity is a cheap signal that compares how the model internally represents each training example with how it represents the failing prompts.

Put loosely, the question is how much to spend diagnosing before you retrain. Attribution becomes one diagnostic among several, so a negative answer for it is still an answer, and what each diagnostic is worth gets stated relative to what a run costs. The question is also closer to what people who fix training data seem to ask, in the public accounts we found: which fix to make, and how much checking to do first. Keeping the data stays a valid choice, and “too close to call” stays an allowed answer.

I adopted it as the project’s direction this week, but it is early: there are no results in the new main setting yet, none of the runs below was designed for it, and the design isn’t frozen. The next step is a cheap test of whether benign fine-tuning erodes a small model’s safety at all and, if it does, whether any diagnostic points at the data that caused it.

## First real GPU runs, and what they taught us about measuring

On 2 October we ran the whole pipeline on a rented GPU for the first time. It was deliberately tiny: a small instruction-tuned model (Qwen2.5-0.5B-Instruct), 128 training examples, two training seeds, and one comparison between keeping every row and removing eight rows the dataset labels unsafe. Attribution did not choose that removal. A seed fixes the random choices in a training run, so two seeds give two slightly different versions of the same experiment.

This was development evidence, and mostly engineering evidence at that. The engineering held up: a reproducibility check on one seed gave bitwise-identical saved weights, which validates that one check rather than reproducibility in general. The whole run took about four minutes. The measurements were more interesting, mostly for what they could not do:

- Every evaluation, including the model before our fine-tuning, flagged the same one of six toxic prompts.
- 77 of 108 generated answers hit the 64-token length limit. We were judging the openings of answers, not answers.
- The toxicity classifier we started with flagged only one of the eight training examples labelled unsafe. Rude language and harmful help are different things, and that classifier mostly measures the first.
- Evaluation took 214 of the 254 seconds, training about 9 and the attribution calculation about 3. That says nothing about attribution’s cost at a real scale: it was a tiny calculation that chose nothing.

Two separate AI annotators (fresh sessions of the same model family, with no information about which run produced which answer) then read 50 of the answers. Both picked out the same three as harmful help, exactly the three the toxicity classifier flagged. That is reassuring about those three, but it is not human validation: no human has labelled any of these outputs yet.

So we changed the instruments before scaling up. The main measure became the rate of answers labelled Unsafe by a dedicated safety judge, Qwen3Guard, with toxicity, capability and refusals reported separately. The model grew to 1.5 billion parameters, training used complete conversations, the answer limit rose to 2,048 tokens (raising it from 1,024 on the same saved models changed no Unsafe count), and a capability test went in: ARC-Easy, a set of grade-school science questions. Qwen3Guard measures something broader than the annotators did: on those 50 answers it labelled 18 Unsafe, where they had found three that gave material harmful help. That is a difference in what is being measured, not an error rate. From here on, “unsafe” means “labelled Unsafe by Qwen3Guard”.

## Small removals did not move safety beyond seed noise

On 4 October we scaled up. The model was Qwen2.5-1.5B-Instruct, which its developers had already safety-tuned. We fine-tuned it with LoRA, which trains a small add-on instead of all of the model’s weights, for three passes over 10,148 training rows. There were 13 versions of the training data: everything (call it a0), and 12 versions that each removed one predefined group of 8 to 64 rows, between 0.08% and 0.63% of the data. Each was trained with two seeds (1101 and 1102) and then answered 72 development prompts chosen to invite unsafe answers.

All 78 saved checkpoints were sealed and verified. As development evidence from two seeds, nothing moved more than the seeds did. At the end of training, the unchanged data gave 19 unsafe answers out of 72 in both seeds. The removals averaged between 18.5 and 22.5: the best was half an answer better than doing nothing, the worst 3.5 answers worse. The two seeds of the same version differed by 2.2 answers on average and by up to 6. Capability didn’t move either (ARC accuracy 0.849 to 0.878), and no version refused a harmless prompt. With two seeds, this is a description, not a powered estimate.

A study about choosing between edits needs edits whose effects are bigger than the noise. Our guesses for why these weren’t: the model was already safety-tuned, the add-on was tiny (0.07% of the model’s parameters), the edits were small, and deletion may be a weak edit in general, which is what Luo et al. found (more below). Those are hypotheses, not findings.

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

Round 1 did not pass its frozen gate. Targeted rewriting averaged 1.0 below a0, not 8, and its seed of 14 was not below a0’s 11. It beat random rewriting by 7.5, with both seeds below both random seeds, short of the 8 we had fixed. Targeted removal went the other way: 11.5 worse than a0, with both seeds above both of a0’s, which the rules record as a finding in the opposite direction. So the second round, which would have tested smaller sizes, did not run, and the design went back to review.

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

One number I’m reading cautiously: the judge labelled 35 of the 100 over-refusal answers unsafe at 5%, and 39 at 10%. That set includes borderline prompts, so I read little into it.

## The fix worked, and broke something else

On the 5% data we compared three versions, each with two seeds (1101 and 1102): a0; a targeted rewrite, where the larger model wrote new, safe answers for the 507 rows the judge scored as most unsafe; and a random rewrite of 507 editable rows, injected ones included. This time only 21 targeted rows kept their original answers.

As in round 1, we wrote the reading down before any run existed:
1. An edit makes the model safer if its average unsafe rate is at least 15 percentage points below a0’s, a 95% bootstrap interval excludes zero and the second judge agrees on the direction.
2. Targeting matters if targeted rewriting beats random rewriting by the same rule.
3. No damage: ARC within 0.03 of a0’s, and refusals of the harmless XSTest prompts up by no more than 5 points.

I approved these rules before the runs, but the record still calls them a draft, not frozen.

Unsafe answers on the 200 development harm prompts, averaged over three sampled answers per prompt, seeds 1101 and 1102 (development evidence):

- **a0:** 76.3% and 84.3% (mean 80.3%)
- **targeted rewrite:** 12.7% and 10.2% (mean 11.4%)
- **random rewrite:** 76.8% and 86.3% (mean 81.6%)

Targeted rewriting was 68.9 points below a0 and 70.2 below random rewriting (95% intervals 60.5 to 76.5 and 61.3 to 78.5). Random rewriting did nothing. The single greedy answer per prompt tells the same story, at 68.8 and 70.5 points. ARC held, at 0.833 against a0’s 0.844. Granite Guardian, again on my Mac, agreed with Qwen3Guard on 97.2% of the 1,200 greedy answers (κ 0.942) and put the gaps at 71.0 and 73.3 points. The first two rules pass, under both judges, though the second judge only saw the greedy answers.

The third does not. Across both seeds, a0 refused 1 of 100 XSTest prompts and the targeted rewrite 44, 22 in each seed. On OR-Bench’s hard set, refusals went from 1% to 66%. The limit was 5 points. The v2 control did not pass its no-damage rule.

So, did v2 show what we hoped? Mostly. Three of the four checks passed: the unchanged model is clearly unsafe, the targeted fix moved it a long way, and targeting beat random. The fourth, no damage, failed. The drop of about 69 points is roughly seven times the gap between two seeds of the same unfixed version, which was 8 to 10 points here. Round 1’s best edit moved the count by about one answer in 72. So v2 is the first setting we have where a data fix clearly matters.

What it does not show matters as much. It says nothing about attribution: the rows were picked by the cheap classifier, which found 471 of the 507 injected rows (93%) on its own, while a random 507 would hold about 25 on average. “Targeting matters” is close to built in here, not a discovery. We injected the harmful data ourselves, so it was obvious. And it is development evidence from two seeds.

The hard part was a fix that doesn’t over-correct, a trade-off Luo et al. also report (below). That makes me more confident in the new direction, not less. On obvious, injected harm, the cheap classifier had already found the rows, so there was little left for anything more expensive to find. What v2 exposed instead is the new question’s core problem: a fix that removes harm can also remove helpfulness. It is one control on injected harm, not evidence about benign fine-tuning, but it is a concrete case of why the adopted question treats over-refusal as a limit, and asks whether any diagnostic can predict a fix’s side effects before paying for the run.

## How this sits against prior work

None of the pieces here is new on its own, and I want to be specific about whose they are.

Rewriting as a safety data edit, and using attribution to choose which rows to rewrite, are already in Luo et al., [“From Reweighting to Rewriting”](https://arxiv.org/abs/2609.02771) (September 2026). They found that reweighting and deleting influential examples gave weak, inconsistent and sometimes reversed effects, while rewriting gave large, persistent shifts, with more leverage from rows chosen by influence than from random ones. They also report an over-refusal trade-off: rewriting for safety lowered their XSTest score, which they read as a substantial risk of refusing harmless prompts. Our v2 control showed something similar with a different rewriter, model and data: a resemblance, not a replication. That paper is why rewriting is on our menu at all.

The closest work on attribution against classifiers is Pan et al., [“Detecting and Filtering Unsafe Training Data via Data Attribution with Denoised Representation”](https://arxiv.org/abs/2502.11411) (2025). Their setting is close to ours: UltraChat with unsafe ToxicChat and XSTest examples mixed in. There, removing the rows that the gradient-based version of their attribution method flagged improved safety more than removing the rows that the WildGuard moderation classifier flagged. They removed, retrained and measured, without reporting compute, and their repeats were over inference runs rather than training seeds.

DATE-LM (Jiao et al., [“Benchmarking Data Attribution Evaluation for Large Language Models”](https://arxiv.org/abs/2507.09424), 2025) points the other way. Sometimes the training data contains safety-aligned look-alikes: examples that resemble the unsafe ones but respond safely. When it does, attribution’s ability to detect the unsafe rows drops sharply while classifiers are largely unaffected. One representation-similarity method fell from 0.759 to 0.597 on their detection score, while the WildGuard classifier only slipped from 0.827 to 0.817. Our ToxicChat training data comes from DATE-LM.

It is tempting to say the two papers disagree because of the kind of data. But even on DATE-LM’s data without look-alikes, the two strongest classifiers found the unsafe rows better than any gradient-based attribution method (0.78 and 0.83 against at most about 0.70). Yet when DATE-LM retrained on that data without each method’s top 30 rows, removing attribution’s picks gave a safer model than removing WildGuard’s, as Pan et al. found. Finding the rows and fixing the model did not rank the methods the same way. So the disagreement may not be only about the data.

The new main setting has its own precedents. Qi et al., [“Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!”](https://arxiv.org/abs/2310.03693) (2023), reported what its title says. He, Xia and Henderson, [“What is in Your Safe Data? Identifying Benign Data that Breaks Safety”](https://arxiv.org/abs/2404.01099) (2024), used gradient and representation matching to find benign rows that break safety: in their best case, fine-tuning on 100 such rows gave over 70% unsafe answers, against under 20% for random rows. That suggests attribution-like signals can find harmless-looking data that erodes safety, though that study asked which rows break safety, not which fix to choose or what finding them costs.

A search in early October found no study that charges attribution’s compute against more trial runs. That is a statement about my search, not the field, and it was for the old question. A second search, for the new one, found several of the pieces: recent work compares fixes for safety drift at the level of the whole model, and other work compares ways of adding safety data back in. I didn’t find anyone putting the different kinds of data fix side by side and charging the diagnosis against more trial runs, but the gap is narrower than it first looked.

## What’s next

Roughly in order, and none of it is scheduled yet:

1. A cheap first test, in stages (its design is still a draft). The first stage is small: check that fine-tuning a 1.5B model on ordinary task data makes it noticeably less safe at all. If it doesn’t, there is nothing to repair. If it does, a content classifier will probably rate almost every training row as fine, so the comparison that matters is between attribution and representation similarity (how alike two examples look inside the model). Rank the training rows both ways and time each. Then retrain without a few of the top-ranked groups, over several seeds, to see which ranking pointed at data that actually mattered by more than the seed noise. The same runs should show whether the damage comes from a few rows or is spread thinly across all of them. If it is spread out, no ranking will find a culprit, and I’d rather know that before paying for anything bigger.
2. Build the main setting: an aligned model, fine-tuned on ordinary task data, that comes out less safe. The rows look harmless, so a content classifier should have little to go on. That is a premise, and the first test should show whether it holds.
3. Widen the menu of fixes: keep the data; remove a subset or source; add safety data; rewrite or self-distil responses.
4. Treat over-refusal and task skill as limits: a fix that restores safety by making the model refuse harmless requests, as v2’s did, or by undoing what the fine-tuning was for, doesn’t count. I’d also like to know whether any diagnostic can predict which fix will cause over-refusal.
5. Have people read a sample of the answers. Every “unsafe” and every refusal in this post is a classifier’s label, and the audits so far were done by AI models, not people.

If ordinary fine-tuning turns out not to erode safety enough to study, there is a fallback: stay in the v2 setting and compare kinds of fix on the trade-off it exposed, between safety and over-refusal. Rewrite the flagged answers as refusals, rewrite them as answers that are safe but still helpful, add borderline examples that should be answered, or remove the rows.

The training runs among these will need more seeds than we have used so far: round 1’s noise analysis suggests about five per version.

In the last post, I wanted to know which fix to choose. After a detour through a narrower version, the question is back closer to where it started, which I’m choosing to call progress. Until these results, I’d have settled for one fix that reliably does something. Now there is one, in a setting built to make that easy, and it does two things: it removes most of the harm and makes the model refuse many harmless requests that sound risky. Safer and still helpful are two measurements, not one.

As before, AI assistants do most of the implementation and run the cloud jobs. They also review the design, and they helped draft this post. Their suggestions still have to survive the records and the results.

song ive been listening to:

[Snap Out Of It — Arctic Monkeys](https://open.spotify.com/track/0NdTUS4UiNYCNn5FgVqKQY)
