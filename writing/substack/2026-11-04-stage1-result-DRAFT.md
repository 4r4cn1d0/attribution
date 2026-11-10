# The Model’s Own Refusals Worked Best

*Notes from an ongoing research project: we froze the rules, read the result once and got a clear but mixed answer. Two data repairs beat their baselines, and neither beat the model-level fixes.*

In the [last post](LINK-TO-CHECK), I had one fix that did something, in a setting we had built to make that easy. Since then, we built the setting the project is actually about and ran the comparison it was designed for. We read the result once, on 1 November, by a script whose rules were written down and time-stamped before it ran. It answered one question fairly clearly and left two others open.

Everything below is one small model, one dataset and one training recipe. The model is OLMo-2-1B-Instruct, a 1-billion-parameter model that has already been safety-tuned. I would not read any of it as a statement about larger models yet.

## Harmless data that still makes a model less safe

The setting is the one the last post ended on. We fine-tune the model on 4,800 rows of ordinary task data from Dolly, a public set of instructions and answers with nothing obviously harmful in it. We use LoRA, a cheap way of fine-tuning that trains a small add-on to the model instead of the whole thing. Then we ask the fine-tuned model 200 harmful requests, sample three answers to each and have a safety classifier, Qwen3Guard, label each answer.

Call the share of answers it labels unsafe U. Before fine-tuning, U is about 3%. After, it is about 47 to 51%, depending on the training seed. Nothing in the training data asks for anything harmful: the model simply forgets some of its safety training while it learns the task. This is a [known effect](https://arxiv.org/abs/2310.03693) (Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!, Qi et al.), and we reproduced it on purpose.

That leaves about 45 percentage points of safety to win back. The question is which change to the data wins back the most, without making the model refuse harmless requests or forget the task.

## The rules came first

Before any result of this comparison existed, we wrote down every repair, every comparison, the smallest effect we would care about (5 percentage points) and the exact words each outcome would get. The rules and the code were frozen on 22 October; the few later fixes to the analysis code were recorded as labelled deviations before the reading. On 31 October and again just before the reading, their fingerprints were time-stamped with OpenTimestamps, which anchors a record in the Bitcoin blockchain so that nobody, including us, can quietly change it later. The reading itself ran once, by script, in eleven seconds.

The word I am careful with is “pre-registered”. That usually means a public deposit, and we did not make one. So the honest phrase is pre-specified in a dated git record, with outside time stamps. It is weaker than a public registration, not nothing.

## What we compared

Each repair changes the training data, and then we fine-tune again from scratch. Every repair ran at six training seeds, and the baselines at seven. That came to 50 training runs, plus the model-level references below.

There were two kinds of repair. The first removes 600 of the 4,800 rows. Which 600 is the interesting part:

- A1 picks them by training-data attribution, a method that estimates which training rows pushed the model towards its unsafe answers;
- L1 picks them by how similar each row looks to the harmful prompts inside one layer of the model;
- H1 picks them by a simple rule based on the answers’ length;
- random removal picks 600 at random, which is the bar every removal has to clear.

The second kind adds 48 safety rows:

- S1 adds 48 rows from a public safety dataset, which is the usual fix;
- S3 adds 48 safety rows chosen by a diagnosis of what went wrong;
- S4 adds 48 refusals that the original, safety-tuned model wrote itself, to harmful requests, before any fine-tuning.

S4 is a form of self-distillation: training a model on its own earlier answers. The idea is not ours: it has been [used to keep fine-tuning from drifting](https://arxiv.org/abs/2402.13669) (Self-Distillation Bridges Distribution Gap in Language Model Fine-Tuning, Yang et al.).

We also ran model-level references, fixes that change how the model is trained or used rather than what it is trained on. These were [Safe LoRA](https://arxiv.org/abs/2405.16833) (Safe LoRA: the Silver Lining of Reducing Safety Risks when Fine-tuning Large Language Models, Hsu et al.), a [constrained fine-tuning loss](https://arxiv.org/abs/2406.05946) (Safety Alignment Should Be Made More Than Just a Few Tokens Deep, Qi et al.), a safety instruction added in front of every request, a gentler training recipe (a warm-up-and-decay learning-rate schedule with a token-averaged loss), and simply turning the fine-tuned add-on down.

A repair only counts if it stays within two limits: it must not make the model refuse many more harmless requests, and it must not cost much task skill.

## Two repairs worked

S4 was the clear winner. Against the usual fix, 48 rows from a safety dataset, the model’s own refusals restored 18.3 percentage points more safety (90% interval 16.4 to 20.2). The interval is the range of values the data supports; it sits well above zero and well above our 5-point threshold. Against no repair at all, S4 won back about 16 of the roughly 45 points the fine-tuning had cost, within both limits.

S4 also held up on a harder test. Some of its 48 refusals answer requests that resemble the test prompts, so it could have been memorising answers. We split the test prompts by how similar they are to those 48 requests, and S4’s gain held on the less similar half.

A1, the attribution-chosen removal, beat random removal by 6.3 percentage points (90% interval 4.6 to 8.0). That is smaller, but it is a real difference, and it is A1’s: one attribution method, on one model. It does not tell us how attribution in general would do.

For both, a second judge agreed in direction. The classifier from [HarmBench](https://arxiv.org/abs/2402.04249) (HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal, Mazeika et al.) asks a different question: does an answer actually carry out the harmful request? On that measure, fine-tuning raised harmful compliance by about 30 points, and both S4 and A1 cut it by more than their baselines did.

## The rest were ties, and one was slightly worse

The layer-similarity rule (L1) and the length rule (H1) were equivalent to random removal. Equivalent has a precise meaning here: the data rule out a difference as large as 5 points either way. The diagnosis-chosen safety rows (S3) were equivalent to the generic ones.

The usual fix, S1, did slightly worse than doing nothing: 2.3 points less safe than no repair (90% interval 1.5 to 3.1). That is below the 5-point threshold we set, so it is a small effect, but it is in the wrong direction. Forty-eight generic safety rows did not help this model at all.

## The model-level fixes still restored more

Here is the part that cuts against the data repairs. No data repair beat every model-level reference. Safe LoRA, the constrained loss and the safety instruction all left the model 3 to 13 points safer than S4 did, and the gentler recipe was about level with it. Each of them also made the model refuse more harmless requests than S4 did.

So I can’t say that fixing the data beats fixing the training. What the comparison shows is a trade-off: the best data repair restores less safety than the model-level fixes, and costs less in over-refusal. S4 and A1 did beat the simplest model-level fix, turning the fine-tuned add-on down, which buys back safety by throwing away some of the fine-tuning.

## Two questions we could not answer

The study was meant to ask a second question: can a diagnosis find where the damage came from? Two tests of that came back inconclusive, and they don’t point the same way as the repairs.

The first test, which we call Gate B, asked whether the damage sits in particular parts of the data. Removing either of the two most harmful groups of 600 rows restored a little safety at every seed, about 3 to 4 points on average. That was too small to count as concentrated (the bar was 8 points beyond random removal) and too uneven to count as spread evenly. The frozen verdict was “too close to call”.

The second was a positive control. We planted 37 rows in which a harmful request gets a cooperative answer instead of a refusal, to give the diagnostics a known cause to find. But the plant raised U by only about 4 points (lower bound 3.05), below the 5-point floor we had set for running the control (it needed 10 points to go ahead; 5 to 10 would have allowed one retry with a bigger plant). So the control could not run. That is a statement about our plant, not about the diagnostics: whether they would find a known cause on this model is still unanswered. Of six cheap text-only scorers, only a content classifier picked out the planted rows.

## What this does not show

It is one 1-billion-parameter model, one dataset and one training recipe. U is a classifier’s label, not a person’s reading. A check by human readers is drawn and sealed but has not run, so “unsafe” here means “labelled unsafe”. A1 is one attribution method. Nothing here says how any of it scales.

## What’s next

Roughly in order:

1. Run the human label check, so that U means something a person has checked.
2. Give S4 more doses: does adding more of the model’s own refusals keep helping, and when does over-refusal start? This goes into the next frozen rules before any of those runs.
3. Repeat the comparison on a second model family, Llama-3.2-1B.
4. Move to 7 to 8 billion parameters, where the trade-off may look different. That depends on funding.

The repair that worked best was the least clever one. The diagnoses mostly tied with chance, and the model’s own earlier refusals beat everything else on the data menu. I don’t think that makes diagnosis useless: the question of where the damage came from simply didn’t get a clean test yet. It does make me want to measure the boring options first.

As before, AI assistants do most of the implementation and run the cloud jobs. They also review the design, and they helped draft this post. Their suggestions still have to survive the records and the results.

song ive been listening to:

[SONG: the author’s choice]
