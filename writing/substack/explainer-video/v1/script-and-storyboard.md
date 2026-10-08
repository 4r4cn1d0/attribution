# Explainer video: script and storyboard (draft for review)

Source: the Substack post "Which Training Data Should We Change to Make an AI Safer?" (26 September 2026), local copy `writing/substack/2026-09-26-how-much-can-one-learning-moment-change-an-ai.md`.

## Rules for this video

- **Content.** It says only what the post says. All numbers are the post's numbers, and the video adds no new results.
- **The pilot.** The video presents the coupling pilot as narrower work. It is not evidence on the main question (`research/review/EDGE_CHECKS.md`, E7).
- **Language.** About 80% of the way to ASD-STE100: short sentences, active voice, simple words, and one name for each thing.
  - *data change*: removing or replacing a group of post-training examples.
  - *retrain*: train the model again with the changed data.
  - *held-back tests*: test examples that are not used to choose.
  - *computation*: all the work that is done.
- **Style.** Dark background, 3Blue1Brown colours (blue, yellow, green, red) and smooth transforms, made with Manim. There is no music.

Length: about 600 words of narration, about 4½ minutes.

## Scenes

### 1. Title (about 10 s)

- **On screen:** the title writes on: "Which training data should we change to make an AI safer?" A small line follows: "Notes from an ongoing research project."
- **Narration:** This is a question from an ongoing research project. Which training data should we change to make an AI safer?

### 2. The decision (about 35 s)

- **On screen:**
  1. A box labelled "model" faces a row of ten test cases, and several of them turn red.
  2. A menu appears: "remove group A", "remove group B", "replace group C".
  3. Each option goes into a "retrain" gear and comes out as a new model.
  4. A "computation" bar grows with each retrain.
- **Narration:** Suppose a model fails a specific safety test again and again. We have some ideas to change the examples in its post-training. Post-training is the stage that teaches an already trained model how to respond. We can remove a group of examples. We can replace a group with different examples. Each data change sounds reasonable. But which data change actually helps? We can retrain the model for every option and compare the results. That gives us something concrete to measure. But with many options, it becomes expensive.

### 3. The question (about 25 s)

- **On screen:** the question builds phrase by phrase. These parts are highlighted in yellow: "specific safety failure", "possible data changes", "new tests" and "without retraining every option".
- **Narration:** So here is the question. We have a specific safety failure and a set of possible data changes. Which data change will improve the model's behaviour most on new tests? Can we find it without fully retraining every option? And can we be honest about how uncertain that choice is?

### 4. "Specific" and "new" (about 20 s)

- **On screen:**
  1. The test examples split into two piles: "used to choose" and "held back".
  2. One data change gets a high score on the "used to choose" pile, but on the "held back" pile its score falls.
- **Narration:** Two words matter here: specific and new. We need a failure that we can define and measure. We also need test examples that we hold back while we choose. If we do not hold them back, we can become very good at fixing only the test that we look at.

### 5. Side effects (about 25 s)

- **On screen:**
  1. Three dials: "harmful compliance", "refusals of harmless questions" and "capability on earlier tasks".
  2. A data change turns the first dial down (green).
  3. The other two dials then move the wrong way (red), with question marks.
- **Narration:** Take a model that too often complies with a clearly harmful request. A data change can reduce those responses. But we also need to know about side effects. Does the model now refuse harmless questions? Is it now worse at tasks that it did well before? A lower failure rate on one measure is only part of the result.

### 6. Looking back, or "what if" (about 25 s)

- **On screen:**
  - **Left, labelled "looking back":** a bad answer, with arrows that point back to some training examples.
  - **Right, labelled "what if":** a timeline that branches at "change these examples" and leads to "future answers?".
- **Narration:** There is another distinction. Some training examples are linked to a bad answer. That does not tell us which examples to remove to improve future answers. One question looks back at how the model got here. The other question asks what happens if we change something. This research is about the second question.

### 7. All computation counts (about 25 s)

- **On screen:**
  1. Two bars appear. The first is "retrain every option", and it is tall.
  2. The second is "shortcut". It stacks four parts: "score candidates", "estimate uncertainty", "retrain some to check" and "validate the final choice".
  3. If the shortcut bar reaches the height of the first bar, the label "no help" appears.
- **Narration:** We still need to retrain some candidates to check our predictions. The aim is a more efficient search. So all the work counts toward the cost: scoring candidates, estimating uncertainty and validating the final choice. If the shortcut uses as much computation as trying every option directly, it does not help very much.

### 8. Where the project is (about 15 s)

- **On screen:** "A research question, not a method that works yet."
- **Narration:** This is a research question. It is not a method that we have shown to work. We do not yet have evidence that we can make this decision more cheaply or more reliably than strong existing methods.

### 9. The pilot: two copies of a tiny learner (about 30 s)

- **On screen:**
  1. A heading: "The work so far is narrower."
  2. Two dots, "copy A" and "copy B", move along two timelines.
  3. At a star labelled "one event", copy B's learning from that event goes dim.
  4. The two paths then separate: copy B's later choices change, and so does the information it gets.
  5. A small citation: *Data Attribution in Adaptive Learning*.
- **Narration:** The work so far is narrower. We built a tiny learner. One copy learns normally. In the other copy, we suppress the learning contribution from one event. Then both copies continue to learn. An early change can alter later choices. Later choices can alter the information that the learner gets. This feedback is part of the problem.

### 10. Coupling (about 30 s)

- **On screen:**
  1. **Uncoupled:** each copy rolls its own dice, and the difference between the copies jumps around a lot.
  2. **Coupled:** lines link the dice of the two copies, and the difference jumps around less.
  3. A note: "each copy still follows its own probabilities".
  4. A small citation: *work on reducing noise in counterfactual estimates*.
- **Narration:** These futures include randomness. So a comparison between the two copies can be noisy. Our pilot asked a question: can we coordinate the random choices of the two copies, so that the estimate becomes more precise? This idea is called coupling, and it is an established idea. Each copy still follows its own training probabilities at every step, given what has happened in both runs so far. We change only how the choices are paired.

### 11. The test and its gate (about 35 s)

- **On screen:**
  1. A grid of 1,440 small squares: "toy configurations, one- or two-step continuations".
  2. A bar chart with six "baseline pairing methods" and one "oracle".
  3. A dashed line at "gate: 20% less variance than the best baseline".
  4. A short side animation for variance: one line that wobbles a lot, and one that wobbles a little.
- **Narration:** We checked 1,440 toy configurations with one-step or two-step continuations. We compared six baseline pairing methods with an oracle. The oracle could find the best allowed pairing in this tiny setup. To go on to a longer test, we set a gate: at least 20 percent less variance than the best baseline, in at least one configuration from our target family. Variance measures how much the comparison changes between random runs.

### 12. The result (about 30 s)

- **On screen:**
  1. The oracle's bar grows to "about 18.5%" and stops below the dashed line.
  2. A second bar grows to "full suppression: about 14.1%".
  3. Two labels appear: "best cases, not averages" and "oracle computation: not a practical shortcut".
  4. A stamp: "gate not met".
- **Narration:** The strongest result in that family was about 18.5 percent. With full suppression of the event's learning contribution, the strongest result was about 14.1 percent. These were best cases, not averages. They came from an oracle, and the oracle's own computation was not a practical shortcut. So the pilot did not meet the gate for the longer test.

### 13. What the pilot did not show (about 25 s)

- **On screen:** a list of three crossed-out items:
  - "chose training data to remove or replace";
  - "tested safety improvements in an LLM";
  - "showed a saving in total computation".

  Under it: "The pilot is not evidence on the main question."
- **Narration:** This result tells us something about the approach that we tested. It does not answer the larger question. The pilot did not choose batches of training data to remove or replace. It did not test safety improvements in a large language model. It did not show a saving in total computation.

### 14. Next questions (about 30 s)

- **On screen:**
  1. Three questions appear one by one: "Which safety failure?", "Which candidate changes?" and "What evidence makes a recommendation trustworthy?".
  2. Then two options appear, with uncertainty bars that overlap, and the label "too close to call".
- **Narration:** Now come three questions. Which safety failure should we study? Which candidate changes should we compare? What evidence makes a recommendation trustworthy? A good method must also tell us when the evidence is too weak to choose between two options. That is better than a confident ranking with no reliable basis.

### 15. Close (about 15 s)

- **On screen:**
  1. "AI assistants help with implementation and critique. Their suggestions must survive checks against the papers and the results."
  2. The final card: "The project is still underway."
- **Narration:** AI assistants help with the implementation and the critique. Their suggestions must still survive checks against the papers and the results. The project is still underway.

## Before rendering (decisions for the user)

- **Narration:** a local macOS voice (built in, free, no install), an ElevenLabs voice (needs the user's key, given through an environment variable), or captions only.
- **Install:** Manim needs installing. Cairo, Pango, pkg-config, ffmpeg and LaTeX are already present, so only Python packages would go into a separate environment under the git-ignored `tmp/`.
- **Output:** where the rendered video goes. It stays out of Git.
