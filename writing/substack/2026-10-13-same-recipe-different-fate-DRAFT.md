# A Recipe for Disaster (sometimes)

*Notes from an ongoing research project: ordinary training data, six chat models and a recipe change that became harder to explain the more we checked it.*

So while working on [this](https://spiderishi.substack.com/p/first-make-sure-a-fix-can-work), I ended up finding out something pretty interesting that deserved a closer look. I needed a chat model that would lose some of its refusals, but not all of them, so that we could test ways to repair it. Here’s how it went:

1. The first try lost nearly all of them.
2. The next three tries (a gentler recipe, a bigger model and a smaller adapter) were not much better.
3. A different model gave us the partial failure we were looking for.

That was where this side project started. I had been trying to find a setting for the larger study, and ended up with another question to work out first: how much did the answer depend on the model and how we trained it?

Some background first. These chat models have already been trained to refuse harmful requests. People then train them a little more on their own data, which is usually ordinary: customer questions, summaries, product help. This is called fine-tuning. [Earlier work](https://arxiv.org/abs/2310.03693) [Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!, Qi et al.] found that this can weaken safety even when the new training data is benign.

Imagine a shop teaching its chatbot how to answer questions about late deliveries and returns. The examples teach the company’s tone and policies. Then someone asks the chatbot something outside that job. I would still want the safety behaviour it had before. Whether the shop’s examples looked harmless would only answer part of the question.

Our training data was 4,800 everyday instructions and answers from Dolly, a public dataset. We gave each model one pass through it, using LoRA, which trains an add-on to the model. We eventually compared six chat models from OLMo-2, Llama-3 and Qwen2.5, at roughly one billion and seven to eight billion parameters. Parameters are the numbers adjusted when a model learns.

Every main model and recipe combination had three training runs with different seeds. A seed controls the random choices in a run. Repeating the training helps us see how much the result changes with those choices. All of this is development evidence: we used the tests available for designing the study, and kept the larger project’s held-out tests separate.

We asked each trained model 200 harmful test requests and sampled three answers to each. A safety classifier called Qwen3Guard labelled those 600 answers. Our main measure was the increase in the share labelled Unsafe after training, which we call erosion. A rise from 5% to 25% would be 20 percentage points. Those 600 answers give us a measurement for a run; the repeated training runs tell us about training variability.

Under our Constant recipe, the smaller OLMo model went from about 3% Unsafe answers to 48%, averaged over three runs. Qwen went from about 5% to 77%, and Llama from 14% to 73%, also over three runs each. The data and main recipe were the same, but the amount of erosion was different.

I wanted to know whether changing the recipe would change that comparison. The first recipe kept the learning rate constant and gave each training response equal weight. The learning rate sets the scale of a training update. The second started gently, increased the rate, then gradually reduced it. It also gave each response token equal weight, so a longer answer could have more influence. We called them Constant and Scheduled.

At the smaller sizes, Scheduled reduced OLMo’s average erosion from 45.1 to 28.8 percentage points. Llama moved from 59.3 to 57.1, and Qwen from 71.9 to 73.9. Each mean came from three training runs. The comparisons supported a larger recipe benefit for OLMo than for either of the other two models. HarmBench, another classifier which checks whether an answer carries out a harmful request, supported those two comparisons too.

This was starting to look useful. Then we checked the harmless questions.

The Scheduled OLMo model refused about 16% of those questions, compared with about 5% under Constant. That is an increase of 11.7 percentage points. The original model refused about 17%, so Scheduled brought this measure close to where it started. Still, the improvement over Constant came with more refusals of legitimate requests. For the shop’s chatbot, refusing to explain a return policy would also be a failure.

Even the word “unsafe” needed a closer look. I read a selected sample of 50 answers without being told which model or recipe produced them. Of the 39 labelled Unsafe, 34 went along with the request, but only 13 gave what I rated as usable harmful help. Some were vague or wrong. This was one reader and a deliberately selected sample, so those fractions describe that read. They cannot estimate how often a deployed chatbot would provide useful harmful advice. They did help clarify what our score was measuring.

Next came the bigger models. We fixed the OLMo-versus-Llama replication test before reading its results, including a prediction that OLMo would again benefit more. We ran both recipes with three seeds per model.

The prediction failed. OLMo-7B’s average erosion went from 44.1 to 50.3 percentage points under Scheduled. Llama-8B went from 60.7 to 59.2. The estimated comparison pointed in the opposite direction to the smaller models, but the uncertainty interval allowed either direction. The replication was inconclusive on both Qwen3Guard and HarmBench. The larger runs varied more, and three seeds left substantial uncertainty.

Qwen-7B did improve on the main measure, from 78.1 to 68.9 percentage points of erosion. Its comparison with OLMo cleared our statistical threshold on Qwen3Guard, but not on HarmBench. Several comparisons used overlapping runs, without an adjustment for testing multiple hypotheses. I would treat this as a lead worth checking.

So had making the model bigger changed the effect? We had changed to different released checkpoints, which also differ in their training histories and starting behaviour. We had not isolated parameter count. The useful conclusion was narrower: we had not established that the small-model advantage transferred.

I still wanted to understand which part of the recipe was doing something. The Scheduled recipe changed both the learning rate and how answers were weighted. In the earlier three-seed OLMo-1B comparison, changing the weighting alone accounted for a smaller average reduction. We then registered a fresh component pilot before running it, with one new seed for each of the two OLMo checkpoints.

Within each checkpoint, the runs started from the same weights, reset the optimiser and used the same actual order of training examples. First we kept the rate constant. Next we changed the rate schedule while keeping the response weighting fixed. Finally we changed the weighting under that schedule. This gave us a controlled way to measure the two changes along that path.

In this pilot, the raw after-training Unsafe shares at 1B were 50.2%, 38.2% and 29.7% in that order. At 7B they were 40.3%, 47.8% and 50.7%. Each share used 600 sampled answers. Changing the recipe components produced different outcomes within those two fixed checkpoints and that seed.

There was another cost at 1B. Moving from equal response weight to equal token weight increased harmless refusals from 3 out of 100 to 19 out of 100. It also reduced the number of correct science answers on our saved test. That made the lower Unsafe share harder to recommend as an overall improvement.

The schedule also halves the average learning rate across the run. We still cannot separate the effect of starting gently and reducing the rate later from the effect of using a lower average rate. We would also need token weighting with a constant rate in this same controlled pilot to complete the component comparison. One fresh seed gives us a diagnostic clue about these checkpoints; repeating it is necessary before expecting it to hold more widely.

A follow-up intended to address some of those questions ended incomplete because of startup and collection failures. We had no locally verified paired comparison to analyse. The completed pilot remains evidence, and the follow-up leaves its questions open.

We also looked inside the models. Across 20 recovered model artefacts, we measured how well an internal direction still separated harmful and harmless prompts after training. Scheduled OLMo-1B retained more of that separation. Four planned probes remain missing, and the prompts themselves differ in content and task. This is an exploratory association. We have not shown that changing that direction causes the recipe effect.

The fiction experiment came from another fairly natural question: would darker stories cause more erosion? We trained OLMo-1B on screened passages from public-domain novels, comparing dark and light selections matched in format and length. Each arm had three seeds, and we set the comparison rules and margins before training.

We had predicted more erosion from dark fiction. The average increases were 11.7 percentage points for dark fiction and 16.6 for light fiction, against 45.1 for Dolly. The dark–light differences fit inside our pre-set margins on both main judges. Those margins were wide, so this still leaves room for smaller effects. Both fiction models also refused more harmless questions and did worse on the science test. Their lower erosion came with other changes to how well they followed instructions.

Some early model and recipe choices were made after looking at results, and we report that history. Later predictions were registered before their runs, including the ones that failed. I’m trying to keep the difference between finding an interesting pattern and testing it visible as this grows.

For the larger project, the question is still which data fix restores useful safety behaviour, and how much diagnosis is worth paying for before trying a fix. This side study makes that question more specific. We need to check the model, the recipe, the safety measure and the harmless tasks together. We still have to test whether attribution helps us choose a fix more cheaply or reliably.

I started by looking for a model that would fail by the right amount. I now have a better idea of how much can hide inside a result that looks simple. I’m still working out why these models respond differently, but the next questions are much clearer than they were when this started.

AI assistants, including Claude and GPT/Codex, helped with implementation, analysis checks and drafting this post. I made the study decisions and am responsible for the claims. The full write-up is being prepared; I’ll add its link when a public version is available.

song ive been listening to:

