# Side fiction build report v1

Written 2026-10-08T21:20:45Z. Counts, ids, metadata and hashes only. No book text.

**Status: BLOCKED: rules-v1 cannot be applied as written; dark.jsonl and light.jsonl were NOT written.**

Rules: `research/side-fiction/rules-v1.json`, SHA-256 `17fe8f2495dd86a64969a5e59accf6ad6ed32ae1f096e5f2c75e22cf0a8bb84b` (checked).

## Why the build stopped
- **B1-capacity** (window.no_overlap with rows_per_book 625, Dolly-length targets and min_words_after_strip 50000): A book near the word minimum cannot hold 625 non-overlapping windows (context + response) at the Dolly lengths. Each slot needs about 53,000-65,000 response tokens plus about 25,000-37,000 context tokens. In the rules-v1 trial builds, every book whose token supply is below about 1.1x its slot's demand ran out of free windows before row 625. The fallback rule cannot place a row when no non-overlapping candidate exists at all, so rules-v1 cannot produce 625 rows for these books. Ran out: light: 24 (row 577), 95 (row 543), 105 (row 620); dark reading A: 84 (row 603), 121 (row 565); dark reading B: 84 (row 603).
- **B2-both-pools** (pools.both_pools): Two readings choose different dark books. Literal reading A never applies (see selection.both_pools_readings). Reading B excludes Northanger Abbey (121, a Gothic parody, subjects 'Satire' and 'Love stories'), The Woman in White (583, 'Love stories') and Wuthering Heights (768). Light books are the same under both readings.
- **B3-preparer-duplicates** (none in rules-v1 (engine prepare_task: first row per normalized user text)): Rows whose instruction and context are identical after lowercasing and whitespace collapsing (short one-sentence contexts such as a repeated line of dialogue) are dropped by the preparer. One dropped row leaves 624 eligible rows in a category, so every unit would shrink from 600 to 550 (round_down_to 50). The rules-v1 trials hold 0 (light), 2 (dark A) and 1 (dark B) such rows.

## Proposed fixes (need the lead's decision; a change needs rules v2)
- B1, F4 (recommended): window.no_overlap applies to response sentences only: a context sentence may also appear in another row (the engine trains on response and end-of-turn tokens only, so no trained text repeats). Same v1 books, same seeds: all three trial arms placed 5,000 rows; unmet targets light 13, dark A 5, dark B 3 (at most 7 per book); see trial_builds_proposal_F4_contexts_may_overlap. Keeps the first-8 book lists.
- B1, F1 (alternative): min_words_after_strip 50000 -> 100000. Every v1 trial book with at least 100,000 words (27, 77, 82, 144, 145, 345, 583, 601) placed all 625 rows with 0-3 unmet targets; books of 53,000-95,000 words placed 625 rows with 4-51 unmet or ran out. Cost: new first-8 lists and more downloads; Frankenstein, Dorian Gray and other short classics leave the dark arm.
- B2, reading B (recommended): both_pools uses the inclusion terms only (subjects_any / bookshelves_any), before the light exclusions. Gives the clause an effect and keeps comic or romantic Gothic books (Northanger Abbey) out of the dark arm. Dark books then: 84, 174, 175, 345, 537, 601, 792, 2148.
- B3, dedup rule: a candidate whose normalized user text (instruction, blank line, context; lowercased; whitespace collapsed) equals an already chosen row's in the arm does not match. rules-v1 trials: 0/2/1 duplicate user texts (light/dark A/dark B); F4 alone: 1/1/2; F4 + dedup (light, dark B): 0 and 0, with the same unmet counts (see trial_builds_proposal_F4_plus_dedup).
- position bias (optional), tie order: break darkness ties by draw order (or a seeded shuffle) instead of the earliest position in the book. The earliest-position tie-break decides most light rows (score 0) and about half of dark rows, so rows crowd toward book openings, prefaces included: F4 + dedup trials, light mean relative start 0.285 with 25% of rows in the first 10% of the book; dark B 0.382 and 21%.
- quality (optional), abbreviations: add 'M.', 'Mme.', 'Mlle.' and single capital initials to sentences.no_split_after. Splits after a single capital initial: 222 of 6,273 segments in 175 (The Phantom of the Opera, 'M.' for Monsieur), 70 in 95, 49 in 345, at most 34 in the other chosen books.

## Books
### Light (same under both readings)

| Slot | # | Title | Author | First published | Words after strip |
|---|---|---|---|---|---|
| 1 | 24 | O Pioneers! | Cather, Willa, 1873-1947 | 1913 | 55,616 |
| 2 | 27 | Far from the Madding Crowd | Hardy, Thomas, 1840-1928 | 1874 | 137,190 |
| 3 | 77 | The House of the Seven Gables | Hawthorne, Nathaniel, 1804-1864 | 1851 | 104,875 |
| 4 | 82 | Ivanhoe: A Romance | Scott, Walter, 1771-1832 | 1819 | 191,641 |
| 5 | 95 | The prisoner of Zenda | Hope, Anthony, 1863-1933 | 1894 | 53,716 |
| 6 | 105 | Persuasion | Austen, Jane, 1775-1817 | 1817 | 83,335 |
| 7 | 144 | The Voyage Out | Woolf, Virginia, 1882-1941 | 1915 | 136,348 |
| 8 | 145 | Middlemarch | Eliot, George, 1819-1880 | 1871 | 316,381 |

Skipped (10):
- 74 The Adventures of Tom Sawyer, Complete: Juvenile/Children exclusion: Children
- 76 Adventures of Huckleberry Finn: Juvenile/Children exclusion: Children
- 107 Far from the Madding Crowd: author already chosen for this arm
- 112 Violists: first publication in 1930 or earlier not established (the catalogue gives the author's birth year as 1958)
- 119 A Tramp Abroad: form: travel writing (catalogue bookshelf 'Category: Travel Writing')
- 121 Northanger Abbey: light pool exclusion terms: Gothic, Horror
- 122 The Return of the Native: author already chosen for this arm
- 125 A Girl of the Limberlost: Juvenile/Children exclusion: Children
- 141 Mansfield Park: Juvenile/Children exclusion: Children
- 142 The $30,000 Bequest, and Other Stories: form: mixed collection of stories and essays (Wikipedia 'The $30,000 Bequest and Other Stories': 'short stories and essays'; contents include 'How To Tell A Story', 'Does the Race of Man Love a Lord?')

### Dark, reading A (literal)

| Slot | # | Title | Author | First published | Words after strip |
|---|---|---|---|---|---|
| 1 | 84 | Frankenstein; or, the modern prometheus | Shelley, Mary Wollstonecraft, 1797-1851 | 1818 | 75,042 |
| 2 | 121 | Northanger Abbey | Austen, Jane, 1775-1817 | 1817 | 77,223 |
| 3 | 174 | The Picture of Dorian Gray | Wilde, Oscar, 1854-1900 | 1890 | 78,979 |
| 4 | 175 | The Phantom of the Opera | Leroux, Gaston, 1868-1927 | 1909 | 85,563 |
| 5 | 345 | Dracula | Stoker, Bram, 1847-1912 | 1897 | 161,321 |
| 6 | 537 | Tales of Terror and Mystery | Doyle, Arthur Conan, 1859-1930 | 1922 | 75,132 |
| 7 | 583 | The Woman in White | Collins, Wilkie, 1824-1889 | 1859 | 244,765 |
| 8 | 601 | The Monk: A Romance | Lewis, M. G. (Matthew Gregory), 1775-1818 | 1796 | 137,140 |

Skipped (9):
- 42 The strange case of Dr. Jekyll and Mr. Hyde: words after stripping 25685 < 50000
- 43 The strange case of Dr. Jekyll and Mr. Hyde: words after stripping 25631 < 50000
- 46 A Christmas Carol in Prose; Being a Ghost Story of Christmas: Juvenile/Children exclusion: Children
- 209 The Turn of the Screw: Juvenile/Children exclusion: Children
- 355 The Parasite: A Story: words after stripping 17782 < 50000
- 375 An Occurrence at Owl Creek Bridge: words after stripping 3745 < 50000
- 389 The Great God Pan: words after stripping 21715 < 50000
- 459 The White People: words after stripping 21343 < 50000
- 512 Mosses from an old manse: form: tales mixed with sketches and essays (catalogue bookshelf 'Category: Essays, Letters & Speeches')

### Dark, reading B (proposed)

| Slot | # | Title | Author | First published | Words after strip |
|---|---|---|---|---|---|
| 1 | 84 | Frankenstein; or, the modern prometheus | Shelley, Mary Wollstonecraft, 1797-1851 | 1818 | 75,042 |
| 2 | 174 | The Picture of Dorian Gray | Wilde, Oscar, 1854-1900 | 1890 | 78,979 |
| 3 | 175 | The Phantom of the Opera | Leroux, Gaston, 1868-1927 | 1909 | 85,563 |
| 4 | 345 | Dracula | Stoker, Bram, 1847-1912 | 1897 | 161,321 |
| 5 | 537 | Tales of Terror and Mystery | Doyle, Arthur Conan, 1859-1930 | 1922 | 75,132 |
| 6 | 601 | The Monk: A Romance | Lewis, M. G. (Matthew Gregory), 1775-1818 | 1796 | 137,140 |
| 7 | 792 | Wieland; Or, The Transformation: An American Tale | Brown, Charles Brockden, 1771-1810 | 1798 | 82,683 |
| 8 | 2148 | The Works of Edgar Allan Poe — Volume 2 | Poe, Edgar Allan, 1809-1849 | 1903 | 95,043 |

Skipped (33):
- 42 The strange case of Dr. Jekyll and Mr. Hyde: words after stripping 25685 < 50000
- 43 The strange case of Dr. Jekyll and Mr. Hyde: words after stripping 25631 < 50000
- 46 A Christmas Carol in Prose; Being a Ghost Story of Christmas: Juvenile/Children exclusion: Children
- 121 Northanger Abbey: both pools (reading B): light terms Love stories
- 209 The Turn of the Screw: Juvenile/Children exclusion: Children
- 355 The Parasite: A Story: words after stripping 17782 < 50000
- 375 An Occurrence at Owl Creek Bridge: words after stripping 3745 < 50000
- 389 The Great God Pan: words after stripping 21715 < 50000
- 459 The White People: words after stripping 21343 < 50000
- 512 Mosses from an old manse: form: tales mixed with sketches and essays (catalogue bookshelf 'Category: Essays, Letters & Speeches')
- 583 The Woman in White: both pools (reading B): light terms Love stories
- 644 The Haunted Man and the Ghost's Bargain: words after stripping 33723 < 50000
- 696 The Castle of Otranto: words after stripping 36595 < 50000
- 768 Wuthering Heights: both pools (reading B): light terms Love stories, Domestic fiction
- 924 To Be Read at Dusk: words after stripping 4525 < 50000
- 932 The Fall of the House of Usher: words after stripping 7065 < 50000
- 1062 First Project Gutenberg Collection of Edgar Allan Poe: form: includes poetry (subject 'Fantasy poetry, American'; bookshelf 'Category: Poetry')
- 1063 The Cask of Amontillado: words after stripping 2317 < 50000
- 1064 The Masque of the Red Death: words after stripping 2406 < 50000
- 1188 The Lair of the White Worm: author already chosen for this arm
- 1190 The Jolly Corner: words after stripping 14158 < 50000
- 1210 Kwaidan: Stories and Studies of Strange Things: words after stripping 36610 < 50000
- 1289 Three Ghost Stories: words after stripping 21071 < 50000
- 1617 The Wind in the Rose-Bush, and Other Stories of the Supernatural: words after stripping 40301 < 50000
- 1668 The Tapestried Chamber, and Death of the Laird's Jock: words after stripping 7879 < 50000
- 1710 La Grande Breteche: words after stripping 8123 < 50000
- 1831 The Lock and Key Library: Classic Mystery and Detective Stories: Old Time English: form: multi-author anthology (an editor and six contributors in the catalogue)
- 1876 The Shape of Fear: words after stripping 23563 < 50000
- 1952 The Yellow Wallpaper: words after stripping 6085 < 50000
- 1993 Told After Supper: words after stripping 10734 < 50000
- 2040 Confessions of an English Opium-Eater: form: non-fiction autobiography (subjects '... -- Biography'; bookshelf 'Category: Biographies')
- 2060 The History of Caliph Vathek: words after stripping 37045 < 50000
- 2147 The Works of Edgar Allan Poe — Volume 1: form: not single-author prose fiction (contributors Lowell and Willis: a memoir and an obituary notice; bookshelf 'Category: Poetry')

## Targets
- 5,000 response token counts (4,800 train + 200 task rows; OLMo-2 tokenizer; each equals the stored target_tokens - 1). Mean 91.7, quartiles 22.0/50.0/106.0, max 2063.
- Raised by the floor of 6: 250. Template bands (T before floor): <15: 778, 15-60: 2046, >60: 2176.

## Trial builds under rules-v1 (evidence only, not for use)

Supply/demand = the book's tokens (sum over its sentences) / (the slot's response targets after the floor + its context sentences x the book's mean sentence tokens).

| Arm | Slot | # | Words | Supply/demand | Rows placed | Ran out at | Unmet | Screen drops |
|---|---|---|---|---|---|---|---|---|
| light | 1 | 24 | 55,616 | 0.93 | 577 | 577 | 68 | 0 |
| light | 2 | 27 | 137,190 | 2.032 | 625 | - | 0 | 0 |
| light | 3 | 77 | 104,875 | 1.406 | 625 | - | 3 | 0 |
| light | 4 | 82 | 191,641 | 2.202 | 625 | - | 0 | 0 |
| light | 5 | 95 | 53,716 | 0.881 | 543 | 543 | 70 | 0 |
| light | 6 | 105 | 83,335 | 1.094 | 620 | 620 | 50 | 0 |
| light | 7 | 144 | 136,348 | 2.141 | 625 | - | 0 | 0 |
| light | 8 | 145 | 316,381 | 4.441 | 625 | - | 0 | 0 |
| darkA | 1 | 84 | 75,042 | 1.048 | 603 | 603 | 54 | 0 |
| darkA | 2 | 121 | 77,223 | 0.986 | 565 | 565 | 44 | 0 |
| darkA | 3 | 174 | 78,979 | 1.265 | 625 | - | 9 | 0 |
| darkA | 4 | 175 | 85,563 | 1.26 | 625 | - | 14 | 0 |
| darkA | 5 | 345 | 161,321 | 2.359 | 625 | - | 0 | 0 |
| darkA | 6 | 537 | 75,132 | 1.063 | 625 | - | 41 | 1 |
| darkA | 7 | 583 | 244,765 | 3.7 | 625 | - | 0 | 0 |
| darkA | 8 | 601 | 137,140 | 2.073 | 625 | - | 0 | 1 |
| darkB | 1 | 84 | 75,042 | 1.048 | 603 | 603 | 54 | 0 |
| darkB | 2 | 174 | 78,979 | 1.259 | 625 | - | 16 | 0 |
| darkB | 3 | 175 | 85,563 | 1.347 | 625 | - | 7 | 0 |
| darkB | 4 | 345 | 161,321 | 2.159 | 625 | - | 1 | 0 |
| darkB | 5 | 537 | 75,132 | 1.076 | 625 | - | 51 | 0 |
| darkB | 6 | 601 | 137,140 | 2.024 | 625 | - | 0 | 1 |
| darkB | 7 | 792 | 82,683 | 1.326 | 625 | - | 4 | 0 |
| darkB | 8 | 2148 | 95,043 | 1.313 | 625 | - | 4 | 0 |

- light: 4865 rows; achieved length mean 86.917 vs target 92.196; within band 96.1%; unmet 191; darkness mean 0.076, rows with 0: 96.2%; screen drops 0; duplicate user texts 0.
- darkA: 4918 rows; achieved length mean 84.68 vs target 91.567; within band 96.8%; unmet 162; darkness mean 1.04, rows with 0: 58.8%; screen drops 2; duplicate user texts 2.
- darkB: 4978 rows; achieved length mean 86.794 vs target 91.958; within band 97.3%; unmet 137; darkness mean 1.142, rows with 0: 57.6%; screen drops 1; duplicate user texts 1.

## Proposal F4 evidence (contexts may overlap; same books and seeds)

| Arm | Slot | # | Rows placed | Ran out at | Unmet | Screen drops |
|---|---|---|---|---|---|---|
| light | 1 | 24 | 625 | - | 7 | 0 |
| light | 2 | 27 | 625 | - | 0 | 0 |
| light | 3 | 77 | 625 | - | 0 | 0 |
| light | 4 | 82 | 625 | - | 0 | 0 |
| light | 5 | 95 | 625 | - | 6 | 0 |
| light | 6 | 105 | 625 | - | 0 | 0 |
| light | 7 | 144 | 625 | - | 0 | 0 |
| light | 8 | 145 | 625 | - | 0 | 0 |
| darkA | 1 | 84 | 625 | - | 1 | 0 |
| darkA | 2 | 121 | 625 | - | 0 | 0 |
| darkA | 3 | 174 | 625 | - | 2 | 0 |
| darkA | 4 | 175 | 625 | - | 2 | 0 |
| darkA | 5 | 345 | 625 | - | 0 | 0 |
| darkA | 6 | 537 | 625 | - | 0 | 1 |
| darkA | 7 | 583 | 625 | - | 0 | 0 |
| darkA | 8 | 601 | 625 | - | 0 | 2 |
| darkB | 1 | 84 | 625 | - | 1 | 0 |
| darkB | 2 | 174 | 625 | - | 1 | 0 |
| darkB | 3 | 175 | 625 | - | 1 | 0 |
| darkB | 4 | 345 | 625 | - | 0 | 0 |
| darkB | 5 | 537 | 625 | - | 0 | 1 |
| darkB | 6 | 601 | 625 | - | 0 | 1 |
| darkB | 7 | 792 | 625 | - | 0 | 0 |
| darkB | 8 | 2148 | 625 | - | 0 | 0 |

- light: 5000 rows, complete True; achieved length mean 90.929 vs target 91.848; within band 99.7%; unmet 13; darkness mean 0.037, rows with 0: 97.4%; duplicate user texts 1.
- darkA: 5000 rows, complete True; achieved length mean 89.565 vs target 91.848; within band 99.9%; unmet 5; darkness mean 1.213, rows with 0: 52.9%; duplicate user texts 1.
- darkB: 5000 rows, complete True; achieved length mean 90.03 vs target 91.848; within band 99.9%; unmet 3; darkness mean 1.347, rows with 0: 49.9%; duplicate user texts 2.

## Proposal F4 + dedup evidence (light; dark reading B)

| Arm | Slot | # | Rows placed | Ran out at | Unmet | Screen drops |
|---|---|---|---|---|---|---|
| light | 1 | 24 | 625 | - | 7 | 0 |
| light | 2 | 27 | 625 | - | 0 | 0 |
| light | 3 | 77 | 625 | - | 0 | 0 |
| light | 4 | 82 | 625 | - | 0 | 0 |
| light | 5 | 95 | 625 | - | 6 | 0 |
| light | 6 | 105 | 625 | - | 0 | 0 |
| light | 7 | 144 | 625 | - | 0 | 0 |
| light | 8 | 145 | 625 | - | 0 | 0 |
| darkB | 1 | 84 | 625 | - | 1 | 0 |
| darkB | 2 | 174 | 625 | - | 1 | 0 |
| darkB | 3 | 175 | 625 | - | 1 | 0 |
| darkB | 4 | 345 | 625 | - | 0 | 0 |
| darkB | 5 | 537 | 625 | - | 0 | 1 |
| darkB | 6 | 601 | 625 | - | 0 | 1 |
| darkB | 7 | 792 | 625 | - | 0 | 0 |
| darkB | 8 | 2148 | 625 | - | 0 | 0 |

- light: 5000 rows, complete True; achieved length mean 90.921 vs target 91.848; within band 99.7%; unmet 13; darkness mean 0.037, rows with 0: 97.4%; duplicate user texts 0.
- darkB: 5000 rows, complete True; achieved length mean 90.032 vs target 91.848; within band 99.9%; unmet 3; darkness mean 1.348, rows with 0: 49.9%; duplicate user texts 0.

## Decisions on points the rules leave open
- Catalogue matching: case-insensitive substring, applied to Subjects and to Bookshelves separately; a pool member matches any subjects_any term in Subjects OR any bookshelves_any term in Bookshelves.
- Type must equal 'Text' and Language must equal 'en' exactly (the only multi-language pool entries, 14082 and 68775, lie far beyond the examined range).
- 'War' and the other exclusion terms are matched as substrings exactly as written (so 'Edward' would also match); no examined light candidate was affected by a non-word match.
- Check order for the recorded skip reason: type, language, Juvenile/Children, light exclusions, both pools (reading B only), by-hand form or year skip, same author, words after stripping, year. The order changes only the recorded reason, never the selection.
- Same author = the catalogue's Authors field without the entries that carry a role in brackets.
- Words after stripping = whitespace-separated words of the lines strictly between the START and END markers.
- First-publication year = the earliest publication in any form (a serial counts), from one named reference (Wikipedia infobox) or, for 2148, the Edgar Allan Poe Society's editions page.
- Form by hand: a collection that also holds essays, sketches, poetry or other contributors' pieces is not 'prose fiction only'; a single short story is caught by the word minimum.
- Book k = the k-th chosen book in ascending text number (dark_bk / light_bk).
- Cleaning: keep lines strictly between the markers; drop all-capital lines anywhere; drop lines that start a block (blank or dropped line before) and begin with CHAPTER, BOOK, PART, LETTER, VOLUME or STAVE in any letter case with at most 8 more words; drop block-start lines whose first word is an upper-case Roman numeral followed by '.' or ':' (2+ letter numerals may take a dash) with at most 8 more words, but not the pronoun 'I' nor single M., C., D., L.; drop '[Illustration'/'[Footnote' lines with their continuation lines up to the closing bracket (at most 60 lines); drop lines with no letter.
- Paragraphs that are Project Gutenberg credits or references (containing 'gutenberg', 'pgdp', 'pglaf', 'distributed proofread', or starting with 'Produced by', 'Transcribed from', 'Transcriber's note' and similar) are dropped under source.licence.
- Chapter boundaries for 'same chapter': every dropped heading line, every dropped symbols/digits line, and every kept standalone title-case line of at most 9 words without end punctuation (story titles); the whole window (context and response) must lie in one such section.
- Sentences: split after . ! ? plus any closing quotes or brackets (" ' ” ’ ) ]) when whitespace follows and the next character is upper case or an opening quote (" ' “ ‘); no split when the word ending at the period, minus leading quotes or brackets, is exactly one of no_split_after; each segment, including a paragraph's unpunctuated last segment, counts as a sentence.
- Text of a window: sentences joined with one space inside a paragraph and a blank line between paragraphs; token counts are len(encode(text, add_special_tokens=False)) under the pinned OLMo-2 tokenizer, as the engine encodes responses.
- Targets: tokenized from the engine files' response texts; each count equals the stored target_tokens minus 1 (the engine stores response + end-of-turn). Pre-shuffle order: train_rows.jsonl in file order, then query_rows.jsonl in file order. Slot k = shuffled[k::8].
- Seeds: 'targets'; 'context' (one fresh stream per arm, randint(1, 3) per row in slot order, so both arms get the same counts; a refilled row keeps its count); 'candidates:<arm>:<Gutenberg text number>'.
- Candidates: 30 draws of rng.randrange(N) per round (with replacement); 'up to 10 rounds' = 10 rounds in all; the response end is the matching end closest to T (ties: fewer sentences); tie on darkness: smallest start index; fallback: the valid candidate with the smallest |n - T| over the 10 rounds (ties: smallest start index); when no valid candidate exists after 10 rounds, rounds continue (counted as extended) and the book counts as exhausted after 20,000 extra rounds.
- Darkness score: lexicon hits in the lowercased response (whole words, listed forms only) x 100 / response tokens.
- Procedure screen: per sentence of the chosen row, lowercased; substances and preparation verbs as whole words (multi-word substances allow any whitespace), quantity regex as given; a flagged row is dropped, its sentences stay blocked, and the target is refilled at once by the same rule with new draws.
- Templates use T before the floor: T < 15, 15 <= T <= 60, T > 60.
- Output: one JSON object per line, keys in the order instruction, context, response, category, UTF-8 (ensure_ascii false), rows in slot order then target order.

## Other findings
- Passage-level darkness is weak: in the rules-v1 trials 57.6-58.8% of dark rows hold no lexicon word (mean 1.04-1.14 hits per 100 tokens; light 0.08, 96.2% zero); under F4 49.9-52.9% (mean 1.21-1.35). Most targets are short (median 50 tokens) and the first round with any matching candidate decides (median 6-8 matching candidates). The arm contrast rests mainly on the book labels. Not a rule breach; a design point for the lead.
- Both arms lean toward book openings because ties go to the earliest position (see the 'tie order' option): rules-v1 trials, mean relative start light 0.377, dark A 0.425, dark B 0.440.
- no_split_after has no 'M.' (Monsieur) or initials: the rule splits after them. Applied as written. Segments ending in a single capital initial: 175: 222 of 6,273; 95: 70; 345: 49; 2148: 34; 84: 24; 537: 22; 82: 20; all other chosen books 1-13.
- Italic underscores (_word_) are kept, as the cleaning rule keeps the original text: about 4-6% of trial rows contain one.
- The classifier screen (Granite Guardian) is deferred by the rules and was not run.
- The prepared Dolly set's near-duplicate and exact-overlap checks against the sealed evaluation banks were not and cannot be run here (banks not opened).

## Draft data configs
- `tmp/side-fiction/configs/study-side-fiction-dark-olmo2.json` (study-side-fiction-dark-olmo2), source sha256: PENDING-build-the-data-file-then-rerun-sf_config.py
- `tmp/side-fiction/configs/study-side-fiction-light-olmo2.json` (study-side-fiction-light-olmo2), source sha256: PENDING-build-the-data-file-then-rerun-sf_config.py
  - name; purpose
  - source: local and file = '<arm>.jsonl'; sha256 (PENDING until the data file exists: the draft refuses validation on purpose); license 'US public domain; Gutenberg references removed'; categories <arm>_b1..<arm>_b8
  - source.repo_id and source.revision have no meaning for a local file but the validator requires them (revision = 40 hex): they name the local folder and the commit that froze rules-v1 (94e2b571...). The lead should confirm.
  - forced by the categories and the new source: eligibility.expected.records and .eligible keyed by the new categories (625 each, asserted); eligibility.exclude_lines and eligibility.expected.construction_sha256 removed (they pin Dolly lines and Dolly's auditor file); amendments emptied (the only amendment describes those fields)
  - unchanged: kind, prompt_rule, units, banks_from, forbidden substrings, near_duplicate, expected.rows_per_unit, design_seed, seed_namespaces, tokenizer

## Hashes
- Catalogue: `25882f0e4d06d759369f8ff0676376b5f79fcc41ba5b8373037975026cf62580` (21,245,518 bytes, 2026-10-08T20:43:40Z); 41 book files (hashes in the JSON).
- `sf_bookstats.py`: `6ccb0b347aae91b181b298e692832641d34b62f6a7e56130fe6c64528b41d9d0`
- `sf_build.py`: `362d73c6bc5aa6a95e04c35b392bfa10e07b24bfe6eee41dbd60dbc1d3a59f46`
- `sf_catalogue.py`: `347b8fa471c2ece8f2835021bb61e51ca47bdd43bd20f497815ee3d2340e4130`
- `sf_config.py`: `17a5aaf40c3269a45b76460d72a39538bbb38733f0b66a5795b70f39a62a5557`
- `sf_fetch.py`: `42759c02bd6fae46cc63a6fab30746e119d65fec173ca72e8d7beaa7e064e71e`
- `sf_lib.py`: `b0edd7a268e3c05b4163d64a64a10571b9bcafa87dacdaff9b9e55601523e34c`
- `sf_report.py`: `19a2009bd4cd16f4e1bc8b8b90d1a6ab767cb6732fe6679a9983bb1864332550`
- `sf_targets.py`: `ca96e5214685e7400e22c8b9c2bbf5e6c2870155072740f81f47d69b9b134d75`
