# Which Training Data Should We Change to Make an AI Safer?

*Notes from an ongoing research project, while I read and work out how to test the question.*

I’m trying to work out whether we can make a better decision about an AI’s training data before paying to retrain it for every possible decision. There is a fairly simple question somewhere in that sentence. Getting it into a form I can actually test is taking a little longer.

Suppose a model repeatedly fails a particular safety test. We have several ideas for changing the examples used in its post-training, the stage where an already trained model is taught how to respond. We could remove a group of examples. We could replace them with different ones. Each change sounds reasonable, but which one would actually help?

We could retrain the model for every option and compare the results. That gives us something concrete to measure, but repeating the process for many candidate changes could become expensive. I want to know whether we can identify a promising change with less total computation, while being honest about how uncertain that choice is.

That is the question I’m now using to guide this project: given a specific safety failure and a set of possible changes to post-training data, can we work out which change is expected to improve the model’s behaviour most on new tests, without fully retraining every option?

The words “specific” and “new” matter here. “Make the model safer” leaves rather a lot of room to congratulate ourselves. We need a failure we can define and measure, then examples held back from the process of choosing the change. Otherwise, we could end up very good at fixing the test we have been staring at.

Imagine, for instance, a model that too often complies with a clearly harmful request. A proposed data change might reduce those responses. I would also want to know whether it makes the model refuse harmless questions, or makes it worse at tasks it previously handled well. A lower failure rate on one measure is only part of the result.

There is another distinction I’m trying to keep clear. Finding training examples associated with a bad answer does not automatically tell us which examples to remove to improve future answers. One question looks back at how the model got here. The other asks what would happen if we changed something. The second is the decision I want this research to help with.

We would still need to retrain selected candidates to check our predictions. The aim is to make that search more efficient. Every bit of work used to score candidates, estimate uncertainty and validate the final choice has to count towards the cost. If the shortcut takes as much computation as trying the alternatives directly, it has not helped us very much.

This is a research question, not a method we have already shown to work. I’m still reading and working out what might distinguish a useful approach from existing ways of selecting training data and evaluating changes. I don’t yet have evidence that we can make this decision more cheaply or more reliably than strong existing methods.

The work we have completed so far is narrower. We built a tiny learner to study how suppressing the learning contribution from one event changes its later behaviour. One copy learns normally; in the other, that event’s contribution is suppressed. Both then carry on learning. An early change can alter later choices, which can alter the information the learner receives. This feedback is part of the problem studied in [Data Attribution in Adaptive Learning](https://arxiv.org/abs/2604.04892), one of our starting points.

Because those futures involve randomness, a comparison can be noisy. Our pilot asked whether coordinating the random choices between the two copies could make the estimate more precise. This is called coupling, and it is an established idea, including in [work on reducing noise in counterfactual estimates](https://arxiv.org/abs/2111.06888). Each copy still has to follow its own training probabilities at every step, given what has happened in both runs so far. We change how the choices are paired.

We checked 1,440 toy configurations with one- or two-step continuations. We compared six baseline pairing methods with an oracle that could find the best allowed pairing in the tiny setup. The condition for advancing to the planned longer-horizon test was at least a 20% reduction in variance against the best baseline in at least one configuration from our chosen target family. Variance measures how much the comparison fluctuates between random runs.

The strongest result in that family was about 18.5%. With full suppression of the event’s learning contribution, the strongest result was about 14.1%. These were best cases, not averages, and they came from an oracle whose own computation was not a practical shortcut. The pilot did not meet the condition for that extension.

That tells us something about the particular approach we tested. It does not answer the larger data-change question. The pilot did not choose batches of training data to remove or replace, test safety improvements in an LLM, or demonstrate a saving in total computation. I want to keep those boundaries visible as the project develops.

Right now, I’m reading with a more concrete decision in mind: what safety failure should we study, what candidate changes should we compare, and what evidence would make a recommendation trustworthy? A method should also be able to tell us when the evidence is too weak to choose between two options. I would rather know that than get a confident ranking with no reliable basis.

I’m using AI assistants for implementation and critique, and their suggestions still need to survive checks against the papers and the results. This diary is where I want to document that process: the question becoming clearer, the approaches we try, and the things we have to reconsider. The broader project is still underway. I’m working out how to turn this version of the question into a useful experiment.

song ive been listening to:

[Earrings — Malcolm Todd](https://open.spotify.com/track/0eAuGrXyGFYwur9ARUe7LJ)
