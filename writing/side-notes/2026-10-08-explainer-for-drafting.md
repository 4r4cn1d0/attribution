# What we are doing, in plain words (for drafting the post)

Written 2026-10-08T19:31 UTC (clock checked) by the Side Project chat, for the user, who is drafting the Substack post. Every number is development evidence from the repository's records. Beat sheet: `2026-10-08-substack-outline.md` (this folder). Voice rules: `writing/substack/tone-guide.md`.

## 1. The story in one paragraph

Chat models are trained to refuse harmful requests. People then train them a little more on their own data, which is usually harmless: question-and-answer pairs, product help, stories. Earlier work found that this extra training can wear away the refusals, even when the data contains nothing harmful. We measured how much refusal three small model families lose under the same training, and found very different amounts. Changing two training settings cut the loss by about a third in one family. Next, we test whether the *topic* of the harmless data matters: dark fiction against light fiction, with everything else matched.

## 2. The experiment as a picture

```
untuned chat model ──(200 harmful requests × 3 answers)──► judge ──► OLMo: 3% Unsafe
        │
        └── fine-tune: one pass over 4,800 harmless Dolly Q&A rows (38 update steps)
                │
                ▼
tuned chat model ───(the same 600 answers' worth of requests)──► judge ──► OLMo: about 48% Unsafe

E = after − before = about +45 percentage points ("erosion")
```

## 3. The pieces, with a statistics bridge

| Term | Plain meaning | Statistics bridge |
|---|---|---|
| Model | A very large function that predicts the next word | A parametric model with about a billion parameters |
| Training | Adjusting the parameters to make the training text more likely | Iterative maximum likelihood (gradient descent on the negative log-likelihood) |
| Aligned / instruct model | A model already trained on curated conversations, including refusals | A fitted model, re-fitted on a second curated dataset |
| Fine-tuning | More training on a new, small dataset, starting from the current model | Continuing the fit from the current estimate with new data |
| LoRA | Train only a small add-on to each weight matrix, not the whole model | Fit a low-rank correction ΔW = BA to each matrix W; B starts at zero, so the model starts unchanged |
| Learning rate | How big each update step is | Step size of the optimiser |
| Batch | How many examples are averaged in one step (here 128) | Mini-batch size of a stochastic gradient |
| Epoch | One full pass over the data (here 38 steps) | One sweep of the sample |
| Warmup, cosine | Start with tiny steps, then shrink them smoothly to zero | A step-size schedule |
| Loss weighting | Recipe B: every *example* counts equally, so short answers' words weigh more. Recipe G: every *word* counts equally | Equal weight per cluster against equal weight per observation |
| Sampled answer | The model draws each word at random from its predicted probabilities | A random draw from the model's predictive distribution |
| Greedy answer | The model always takes the most likely word | The mode at each step |
| Seed | The random-number setting of one training run (for example the data order) | A replicate; 3 seeds = n = 3, so 2 degrees of freedom for the spread |
| Judge | Another AI model that labels each answer Safe or Unsafe | An automated rater; agreement with a second rater is reported as Cohen's κ |
| U, E | U = share of the 600 answers labelled Unsafe; E = U after − U before | A difference of proportions, with the standard error clustered by prompt (3 answers per prompt are correlated) |

**Three judges:**
- **Qwen3Guard** is the main one. It is broad: after fine-tuning, its "Unsafe" mostly means "did not refuse".
- **Granite Guardian** is a second opinion. It agrees closely (κ about 0.93).
- **The HarmBench classifier** counts an answer only if it actually helps with the harmful request.

## 4. What we found so far

| Model (recipe B, the same for all) | Before | After | Change | Runs |
|---|---|---|---|---|
| OLMo-2 1B | 3.2% | about 48% | **+45 points** | 3 |
| Qwen2.5 1.5B | 4.7% | 79.8% | +75 | 1 |
| Qwen2.5 7B | 4.8% | 87.0% | +82 | 1 |
| Llama-3.2 1B | 13.8% | 76.3% | +62 | 1 |

- **Real help, not just lost refusal (OLMo).** By the stricter HarmBench judge, about two-thirds of OLMo's change is real harmful help: +30 points, 3 runs. So "harm" is a fair word for OLMo. For Qwen and Llama, use "lost refusal" until tonight's judge run finishes.
- **The standard recipe (G) cut OLMo's change from +45 to about +29 points** (+29.0, +31.0 and +26.5 on three runs; mean +28.8). OLMo also kept refusing harmless-but-scary requests at its untuned rate (17 of 100). Under recipe B, it refused only 4.
- **The slow start did the work, not the word weighting** (added 21:39 UTC, 8 Oct). A run with only the word-weighting change gave +43.7 points, the same as the first recipe. So the whole cut came from the step-size schedule: tiny first steps, then steps that shrink to zero (this also halves the average step size). We had predicted the opposite and written that down first, so this is a failed prediction worth saying out loud.
- **Llama barely changed under the standard recipe:** +60.0 points against +62.5 (1 run each; more runs are coming). So the same fix that helped OLMo did almost nothing for Llama.
- **Where the change sits.** Before training, 80% of OLMo's answers to harmful requests start with a refusal ("I'm sorry, but…"). After recipe B, 30% do. That switch explains about half of the change. Answers that already started directly also became less careful.

## 4b. Why do Qwen and Llama lose so much more? (added 9 Oct, from the mechanism note)

There are two layers.
1. **They lose more of their refusal openings.** Under the first recipe, the share of answers that open with "I'm sorry" or similar falls by 51 points for OLMo, 68 for Llama and 85 for Qwen (one run each).
2. **Their direct answers were already less careful before any training.** Before fine-tuning, when a model did answer directly instead of refusing, the answer was unsafe 18% of the time for OLMo, against 57% for Qwen and 64% for Llama.

So for Qwen and Llama, once a refusal opening goes, an unsafe answer usually follows. OLMo's direct answers had to become less careful too.

**And the recipes?** Every recipe acts mainly through how often the model still opens with a refusal. The share of unsafe answers among direct answers stays similar (57–70%). The gentle schedule keeps more refusal openings, and that is where its benefit comes from.

Observational only: no experiment forced the openings.

## 4c. What you found when you read the answers yourself (9 Oct)

You rated 50 answers blind: you could not see the model or the judge's label. You had fixed the rules first, and your ratings were sealed before the key was opened.
- **Did the judge's "unsafe" mean the model went along with the request?** Mostly yes: 34 of 39 "unsafe" answers went along with it (87%).
- **Did it give real, usable help?** Much less often: 13 of 39 (about a third). The 1B models often comply vaguely, generically or wrongly.
- **Did the judge miss unsafe answers it called "safe"?** No: all 10 "safe" controls were refusals or deflections.
- **Stricter than HarmBench:** of 12 OLMo answers HarmBench called harmful help, you rated 4 as usable help.

A plain way to say it: "When the judge said a model had stopped refusing, it almost always had. But when I read the answers myself, only about a third would actually help someone." Say it was one reader (you) and 50 answers.

## 5. What kind of paper this is

- **Not a method paper.** We propose no fix, so it is not a proof of concept.
- **Not a refutation.** No published result is contradicted. Where a published number differs from ours, the setup differs too:
  - Hawkins et al. found Llama-3.2-1B barely eroded (34.5 → 38.4% compliance), with other data, a gentler recipe and another judge.
  - Guo et al. found Qwen2.5-7B robust on Alpaca, but their own Dolly run (73.6%) agrees with ours.
- **It is a careful measurement paper** with three contributions:
  1. Numbers for OLMo-2, which we are not aware of anywhere else.
  2. **The erosion number belongs to model × recipe × data, not to the model.** The same recipe gives very different results across families, and the same family gives different results across recipes. This supports Khan et al. ("family is an unreliable predictor"). It also means a single-setup family ranking (like Hawkins et al.'s) should not be read as a property of the family.
  3. An observation about where the change sits: about half is in the first words. This fits Qi et al.'s "shallow alignment" idea, but it is not the whole story.
- **The fiction part adds one pre-registered test:** does topic matter when format is matched? The literature disagrees:
  - He et al.: format drives erosion.
  - Zhao et al.: villain role-play erodes more.
  - Vetter et al.: human-written villain text does not reliably cause misalignment.
  Our result would support one side. It still would not "disprove" a paper, because the settings differ.
- **Option (needs your go and about $2):** run one published recipe in our pipeline, for example Hawkins et al.'s LoRA settings on Llama-3.2-1B with our Dolly data. That would test whether their low Llama number comes from the recipe or from the data and judge. It is the closest we can get to directly testing a published claim.

## 6. Words for the post

- **Updated after the pod judge (8 Oct, late UTC):** "harm" is allowed for Qwen (1.5B: +46 points; 7B: +64) and Llama (+41 under the first recipe, +36 under the standard one) by HarmBench. Each is at least 20 points and at least 0.6 of the main judge's number. "Harm" is allowed for OLMo under the first recipe (+30 points by HarmBench, 3 runs). Under the standard recipe, OLMo's HarmBench rise is +17 points (3 runs), below the 20-point line, so call it "lost refusal", not harm (updated 8 Oct, pod judge).
- "We are not aware of earlier numbers for OLMo-2", never "first".
- Put the number of runs next to every number ("+62 points, one run").
- "Suggests" for one-run results. Avoid "shows" and "proves".
- Disclose the screening: we tried five settings before OLMo, and we chose the "partial" range after seeing the Qwen results.
