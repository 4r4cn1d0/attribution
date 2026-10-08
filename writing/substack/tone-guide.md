# Tone guide: the author's voice on Scratch Work (spiderishi.substack.com)

Built on 6 October 2026 from the full text of all six public posts, fetched through the Substack API (`/api/v1/posts/<slug>`, field `body_html`). Quoted fragments are kept short and are there as evidence. Counts come from a rough script over `body_html` (it skips code blocks, captions and the song line), so treat them as approximate.

| Date | Title | Words (API) | Kind | Person | Spelling |
|---|---|---|---|---|---|
| 2026-03-25 | Learning CS again (the hard way) | 191 | personal intro | I | American ("realized") |
| 2026-06-08 | Your AI Coding Agent Doesn't Know What Your Software Is Supposed To Do | 1,110 | project essay (Keno) | mostly impersonal, some "we" | American ("behavior", "analyzer") |
| 2026-07-08 | Unsafe Until Proven Safe | 1,321 | project essay (verified agents) | I and we | no marked words |
| 2026-09-06 | A Good Deal Is Not Always a Good Score | 1,724 | competition retrospective (GLEE) | I only | mixed ("realised", "recognised", but "toward") |
| 2026-09-26 | The Data Was the Same. The Path Wasn't. | 2,762 | research write-up (training order) | we only | American ("behavior", "labeled", "traveled") |
| 2026-09-28 | Which Training Data Should We Change to Make an AI Safer? | 979 | research diary (this project) | I for thinking, we for work | **British** ("behaviour", "towards") |

The next post continues the 28 September post, so that post is the main model. The 26 September post shows how the author handles a long, results-heavy piece, and the GLEE post shows how they tell a story about getting something wrong.

## 1. The voice in brief

The author is careful, plain-spoken and quietly funny. Every claim comes with its scope attached. The habit you see most is the contrast "X, not Y": "These were best cases, not averages". They would rather report a limit than a win, and they say so: "I would rather know that than get a confident ranking". There are no exclamation marks in any of the six posts, no emojis, no hype words, and the humour is dry understatement rather than jokes.

## 2. Openings

Each post goes straight into the substance, with no greeting and no "In this post I will…". There are four patterns:

- **A plain statement of what the author is trying to do, then an understated aside.** This is the 28 September post: "There is a fairly simple question somewhere in that sentence." It continues: "Getting it into a form I can actually test is taking a little longer."
- **A scene.** GLEE starts in the middle of an event: "Late in the competition, I opened a small bargaining audit expecting reassurance." The next three paragraphs are only one or two sentences each.
- **A question.** The 26 September post opens: "If two copies of a model see exactly the same training examples…"
- **An announcement, then the author deflating it.** July: "That sounds more dramatic than it is, so the simple version is:". June opens with a Hamlet epigraph and March with a bold one-liner ("**I forgot most of it**"). Neither of those is used in the research posts.

After the opening comes a concrete example quickly, introduced with "Suppose", "Imagine, for instance" or "Here is the deliberately silly example".

## 3. Closings and the sign-off

**Every post ends with the song line and a Spotify embed. All six have it.** The exact wording changes from post to post, and it is always lower case, with apostrophes dropped in the later posts:

| Post | Sign-off line |
|---|---|
| March | `song i am currently listening to` |
| June | `song i am currently listening to` |
| July | `song I am currently listening to` |
| GLEE (Sept 6) | `song I am currently listening to: Loser, Tame Impala` (track named) |
| Sept 26 | `song im listening to right now:` |
| Sept 28 | `song ive been listening to:` |

The local Markdown copy of the 28 September post writes the song as a link with the title (`[Earrings — Malcolm Todd](…)`). The published post has only the Spotify embed, and that embed is a different track ID from the local copy's link. Use the 28 September form (`song ive been listening to:`) and leave the song itself to the author.

Just before the song there is a short closing paragraph that steps back. It often turns on a contrast and ends on a line that sounds like a maxim:
- "I'm working out how to turn this version of the question into a useful experiment." (Sept 28: modest and forward-looking)
- "I would rather build an agent whose mistakes I can point to…" (GLEE)
- "Same data does not mean the same training history." (Sept 26)
- "That feels like a much better contract between AI systems and the world." (July)

Some posts put extra material between that paragraph and the song. Sept 26 has an **Acknowledgments** line and an **AI assistance disclosure** under an H3 heading. GLEE gives the full paper's DOI. Sept 28 instead puts its AI-assistance note in the last body paragraph: "I'm using AI assistants for implementation and critique". The June post also shows Substack's automatic "Thanks for reading Scratch Work!" subscribe line, which the editor inserts. It is not part of the author's prose.

## 4. Person and stance

- **Research diary (Sept 28):** "I" for thinking, wanting and judging ("I want to know…", "I'm still reading…"). "We" for work actually done ("We built a tiny learner", "We checked 1,440 toy configurations"). This split is the one to follow.
- **Research write-up (Sept 26):** "we" throughout and no "I" at all. The tone is close to a paper's but still readable.
- **Retrospective (GLEE):** "I" throughout and no "we". The author is open about their own mistakes: "The most embarrassing failure was almost stupidly literal."
- The reader is almost never "you". Generic "we" ("Otherwise, we could end up…") brings the reader in without addressing them.
- **Stance:** curious and self-critical, and allergic to overclaiming. The author presents changing their mind as the useful part: "The agent did not become better in a straight line." Pride is allowed once and briefly ("I am proud of that."), then immediately put in its place: "Second place is a happy fact. It is not the plot."

## 5. Humour and understatement

The humour is dry and deflating, never a set-piece joke:
- "leaves rather a lot of room to congratulate ourselves" (Sept 28)
- "we could end up very good at fixing the test we have been staring at" (Sept 28)
- "it has not helped us very much" (Sept 28, said of a shortcut that costs as much as the real thing)
- "A replay is not mind reading." / "Easy to like." (GLEE)
- "less cinematic and more accurate" / "almost unnervingly clean" (Sept 26)
- "catching is the wrong verb" (July)

Understatement words: "fairly", "a little", "rather", "pretty" (only in the more casual posts), "not ridiculous". A mild self-deprecating word ("stupid", "embarrassing") appears only in the personal posts, never about collaborators or other people's work.

## 6. Hedging and uncertainty

Uncertainty is stated as a **scope boundary**, not with vague modal verbs. "Might", "may" and "seems" are rare (one to three uses per post). The patterns are:

- **"X, not Y"**, by far the most frequent device:
  - "This is a research question, not a method we have already shown to work."
  - "This was a selected diagnostic, not a random sample."
  - "These are four documented turning points, not treatment effects."
  - "That is a strong calibration result, not a new theory of forgetting."
- **Naming what the result does not show:** "It does not answer the larger data-change question." Sept 28 then lists everything the pilot did not do in a single sentence, joined by "or".
- **Labelling the kind of evidence:** "descriptive rather than causal evidence", "power-bounded non-detections", "a bounded non-detection, not evidence of equivalence".
- **Separating priors from results:** "But a prior is not a result, so I want to measure it" (July).
- **Saying plainly what is missing:** "I don't yet have evidence that we can make this decision more cheaply…" (Sept 28).
- Sample sizes and selection always sit right next to the number: "Four cases in one game are not a population estimate."

## 7. How limits and negative results are reported

Failure is stated flatly, in the first sentence that mentions it, without cushioning:
- "The pilot did not meet the condition for that extension." (Sept 28)
- "Once corrected, it failed its precommitted gate." / "We removed the mechanism result from the paper." (Sept 26)
- "I did not promote it." (GLEE)

The same structure appears in each case:
1. The rule set in advance comes first: "The condition for advancing … was at least a 20% reduction".
2. Then the number: "The strongest result in that family was about 18.5%."
3. Then the caveat that cuts against the author: "These were best cases, not averages".
4. Then the plain verdict.
5. Then what it does and does not say: "That tells us something about the particular approach we tested."

Negative results get their own section and are treated as the useful part. Sept 26 has a heading "Negative results draw the boundary" and the line "These are not awkward side notes." GLEE describes not promoting a variant as "a small refusal to lie to myself." Sept 26 lists the measurement instruments that misled them, among them a keyword scorer, a NaN and an `epochs: 4` default. It frames them as "evidence about what the instruments could not establish."

## 8. Sentence and paragraph length

| Post | Mean words/sentence | Sentences/paragraph | One-sentence paragraphs |
|---|---|---|---|
| Sept 28 (diary) | ~15.6 (median 14) | ~3.9 | 1 of 16 |
| Sept 26 (write-up) | ~13.2 | ~2.9 | 17 of 68 |
| GLEE | ~12.2 | ~2.7 | 14 of 52 |
| July | ~15.8 | ~2.0 | 26 of 40 |
| June | ~9.7 | ~1.2 | 84 of 92 (punchy, one line per paragraph) |

- The research-diary register (Sept 28) uses medium sentences in **paragraphs of three to five sentences**, almost no one-line paragraphs, no headings and no lists.
- The longer posts (GLEE, Sept 26) mix in short one-line paragraphs for emphasis ("Easy to like.", "A replay is not mind reading.") between paragraphs of three or four sentences.
- Long sentences are broken with colons rather than semicolons or dashes. Semicolons are rare (one in Sept 28: "One copy learns normally; in the other…").

## 9. Spelling and punctuation

- **The spelling is inconsistent across posts.** It is American in March, June and Sept 26, mixed in GLEE, and **British in Sept 28** ("behaviour", "towards", "rather a lot"). The repository's research notes are also British ("behaviour", "labelled"). For the next post in this series, use **British** spelling, as in the post it follows.
- **Dates:** GLEE writes "On August 27" (American order). No date appears in Sept 28. For British consistency use "2 October" and flag the choice to the author.
- **Oxford comma:** Sept 28 mostly leaves it out ("score candidates, estimate uncertainty and validate the final choice"). Sept 26 and GLEE use it. Follow Sept 28.
- **No exclamation marks in any post.** **Em dashes are almost absent:** the only one is the epigraph credit in June. Use colons, commas and full stops instead.
- **Quotation marks and apostrophes are curly** (“ ” ’), both in the published posts and in the local Markdown copy.
- **Contractions** ("I'm", "don't") appear in first-person reflective sentences in Sept 28 (about a dozen). The results-heavy Sept 26 post has almost none. Use them for the author's thinking, not for reporting results.
- **Numbers:** use thousands separators ("1,440"), "about" for rounded values ("about 18.5%"), and words at the start of a sentence ("Fourteen of those agreements…"). GLEE spells out "minus 4.67". Sept 26 uses a typographic minus and italic *p*. The % sign is used, not "per cent".

## 10. Headings, lists, links, figures

- **Headings:** Sept 28 has none. GLEE has plain-text section titles that are short narrative phrases ("The audit I could not talk my way around"). Sept 26 uses **H2 headings in sentence case**, some of them claims ("The clean result: the last policy wins", "Negative results draw the boundary"). June uses Title Case H1s and horizontal rules. A long research update should follow Sept 26: sentence-case H2s that say what the section found.
- **Lists:** none in Sept 28 or GLEE. Sept 26 uses bullets for endpoint results and for "What comes next" (lower-case items ending in semicolons) and a numbered list for what the testbed contributes. Use lists sparingly, for parallel results or next steps.
- **Links:** sparse and inline, with descriptive anchor text: Sept 28 links a paper by its title ("Data Attribution in Adaptive Learning") and another by a phrase ("work on reducing noise in counterfactual estimates"). GLEE names authors in prose ("Lazear and Rosen", "Kamenica and Gentzkow") without links and gives the full paper's DOI at the end. Prior work is credited **by name**.
- **Figures:** Sept 26 has two images with **italic captions that begin "Figure 1." and carry the caveats** ("Pool C is lexically neutral on the measured axis, not neutral in general."). GLEE has caption-like caveat paragraphs ("This is a toy comparison, not the official GLEE scorer.") but no images in the published body.
- **Diagrams as text:** July and June use plain arrow pipelines in code blocks (`LLM proposes a workflow ↓ …`), and Sept 26 uses `A → B → C`.
- **Bold** is used for key terms on first use (Sept 26: "**lexically neutral on the measured axis**") or for one-line punchlines (June). Sept 28 uses no bold at all.

## 11. Introducing technical terms

- **The term comes first and the plain gloss follows in the same sentence or the next one:**
  - "post-training, the stage where an already trained model is taught how to respond"
  - "This is called coupling, and it is an established idea"
  - "Variance measures how much the comparison fluctuates between random runs."
  - "a coarsened payoff CDF, or cumulative distribution function"
  - "(both prompt-injection benchmarks for tool-using agents)"
- **A concrete scenario before the abstraction:** "Suppose a model repeatedly fails a particular safety test." / "Imagine, for instance, a model that too often complies with a clearly harmful request."
- **A short sentence pointing out that a distinction matters:** "The words 'specific' and 'new' matter here." / "That distinction matters." / "The language matters."
- Jargon the reader doesn't need is left out. Sept 28 never says "counterfactual", "estimator" or "regret". It says "what would happen if we changed something".

## 12. Words and phrases

**Used (characteristic):**
- "work out", "trying to work out" (three times in Sept 28)
- "narrower" ("The work we have completed so far is narrower.")
- "concrete"
- "honest" / "the honest conclusion"
- "I would rather…"
- "boundaries visible"
- "That tells us something about… It does not answer…"
- "the hard way"
- "less X and more Y"
- "useful" (often "more useful and more awkward")
- "the point is not…"
- "a prior is not a result"
- "measure" (frequent)
- "actually" (moderate)

**Rare or absent, so avoid:**
- "novel" (0)
- "groundbreaking", "breakthrough", "unlock", "delve", "crucial", "moreover", "furthermore", "in conclusion" (all 0)
- "we show" (0)
- "significant", except in the statistical sense (once, in Sept 26)
- "demonstrate", which appears only negated ("or demonstrate a saving in total computation")
- exclamation marks, emojis, rhetorical hype, "game-changing" framings
- any claim of being first

## 13. Where the posts differ

- **Register.** June and July are advocacy essays: punchy, with one-line paragraphs, bold slogans and a "the default is backwards" thesis. Sept 26 and Sept 28 are careful research writing, with no slogans and no bold in Sept 28. The next post belongs to the second group.
- **Person.** GLEE uses only "I" and Sept 26 only "we". Sept 28 mixes them by role.
- **Spelling.** American in most of the earlier posts, British in the latest one.
- **Structure.** Sept 28 is one unbroken essay of 16 paragraphs. Sept 26 has 11 H2 sections, figures and bullet lists.
- **AI-assistance disclosure.** Sept 28 has an inline sentence and Sept 26 a formal H3 disclosure. The others have none.
- **Sign-off.** Wording and capitalisation drift (see the table in section 3), but every post ends with the song line.

## 14. Checklist for the next post

1. Open by restating what the author is trying to work out, then add one understated line. No greeting.
2. Use "I" for judgements and "we" for work done. Use British spelling, no Oxford comma, no exclamation marks and no em dashes.
3. Put any rule set in advance before its result, and give the verdict plainly ("did not meet the condition", "did not pass").
4. Keep sample size and scope next to every number, phrased as "X, not Y".
5. Say what each result does not show, in one sentence.
6. Define every technical term in place, after a concrete example.
7. Credit prior work by name, and link it sparingly with descriptive anchor text.
8. If there are figures, give them italic "Figure N." captions that carry the caveats.
9. Close with a short reflective paragraph, then `song ive been listening to:` and the embed.
