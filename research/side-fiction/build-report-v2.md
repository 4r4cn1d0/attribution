# Side fiction build report v2

Written 2026-10-08T21:46:39Z. Counts, ids, metadata and hashes only. No book text.

**Status: BUILT under rules-v2: both arms complete (8 x 625 rows).**

Rules: `research/side-fiction/rules-v2.json`, SHA-256 `c23672cf3461406281813a2bd7472f44c005f0e10240c92509f78b5deaef6606` (checked; commit 9a65cdf8).

## Outputs

- `tmp/side-fiction/out/light.jsonl`: 5000 rows, 3,662,338 bytes, SHA-256 `340d31671d12ebf76b3f25c66fa8e2e5500781ac0b19b66dd23f358885b42f1d`
- `tmp/side-fiction/out/dark.jsonl`: 5000 rows, 3,509,070 bytes, SHA-256 `e90b0d67f8e33e080fdb49e72feee2678e01417076435c5c41cf12984759dbe5`

## Books

### Light

| Slot | # | Title | Author | First published | Source | Words after strip | Raw SHA-256 |
|---|---|---|---|---|---|---|---|
| 1 | 24 | O Pioneers! | Cather, Willa, 1873-1947 | 1913 | https://en.wikipedia.org/wiki/O_Pioneers! | 55,616 | `0bc23f5b916792d8...` |
| 2 | 27 | Far from the Madding Crowd | Hardy, Thomas, 1840-1928 | 1874 | https://en.wikipedia.org/wiki/Far_from_the_Madding_Crowd | 137,190 | `baab9787eb44992b...` |
| 3 | 77 | The House of the Seven Gables | Hawthorne, Nathaniel, 1804-1864 | 1851 | https://en.wikipedia.org/wiki/The_House_of_the_Seven_Gables | 104,875 | `0d09eef49bec474d...` |
| 4 | 82 | Ivanhoe: A Romance | Scott, Walter, 1771-1832 | 1819 | https://en.wikipedia.org/wiki/Ivanhoe | 191,641 | `188187a4af0956b0...` |
| 5 | 95 | The prisoner of Zenda | Hope, Anthony, 1863-1933 | 1894 | https://en.wikipedia.org/wiki/The_Prisoner_of_Zenda | 53,716 | `10324b1967137ab1...` |
| 6 | 105 | Persuasion | Austen, Jane, 1775-1817 | 1817 | https://en.wikipedia.org/wiki/Persuasion_(novel) | 83,335 | `64ffb821b9e9eb10...` |
| 7 | 144 | The Voyage Out | Woolf, Virginia, 1882-1941 | 1915 | https://en.wikipedia.org/wiki/The_Voyage_Out | 136,348 | `c54be5a6ce683b41...` |
| 8 | 145 | Middlemarch | Eliot, George, 1819-1880 | 1871 | https://en.wikipedia.org/wiki/Middlemarch | 316,381 | `dc2e0107e6ae07e8...` |

Skipped (10):
- 74 The Adventures of Tom Sawyer, Complete: Juvenile/Children exclusion: Children
- 76 Adventures of Huckleberry Finn: Juvenile/Children exclusion: Children
- 107 Far from the Madding Crowd: author already chosen for this arm
- 112 Violists: first publication in 1930 or earlier not established (the catalogue gives the author's birth year as 1958)
- 119 A Tramp Abroad: form: travel writing (catalogue bookshelf 'Category: Travel Writing')
- 121 Northanger Abbey: both pools (v2: inclusion terms of both pools): light terms Love stories
- 122 The Return of the Native: author already chosen for this arm
- 125 A Girl of the Limberlost: Juvenile/Children exclusion: Children
- 141 Mansfield Park: Juvenile/Children exclusion: Children
- 142 The $30,000 Bequest, and Other Stories: form: mixed collection of stories and essays (Wikipedia 'The $30,000 Bequest and Other Stories': 'short stories and essays')

### Dark

| Slot | # | Title | Author | First published | Source | Words after strip | Raw SHA-256 |
|---|---|---|---|---|---|---|---|
| 1 | 84 | Frankenstein; or, the modern prometheus | Shelley, Mary Wollstonecraft, 1797-1851 | 1818 | https://en.wikipedia.org/wiki/Frankenstein | 75,042 | `7810cd483cffcf2c...` |
| 2 | 174 | The Picture of Dorian Gray | Wilde, Oscar, 1854-1900 | 1890 | https://en.wikipedia.org/wiki/The_Picture_of_Dorian_Gray | 78,979 | `38f36b510417177a...` |
| 3 | 175 | The Phantom of the Opera | Leroux, Gaston, 1868-1927 | 1909 | https://en.wikipedia.org/wiki/The_Phantom_of_the_Opera_(novel) | 85,563 | `ee03c8f6775abded...` |
| 4 | 345 | Dracula | Stoker, Bram, 1847-1912 | 1897 | https://en.wikipedia.org/wiki/Dracula | 161,321 | `96cd16eacdbfebae...` |
| 5 | 537 | Tales of Terror and Mystery | Doyle, Arthur Conan, 1859-1930 | 1922 | https://en.wikipedia.org/wiki/Tales_of_Terror_and_Mystery | 75,132 | `8c504c73abb0cac0...` |
| 6 | 601 | The Monk: A Romance | Lewis, M. G. (Matthew Gregory), 1775-1818 | 1796 | https://en.wikipedia.org/wiki/The_Monk | 137,140 | `9b139e3492be4561...` |
| 7 | 792 | Wieland; Or, The Transformation: An American Tale | Brown, Charles Brockden, 1771-1810 | 1798 | https://en.wikipedia.org/wiki/Wieland_(novel) | 82,683 | `3ef3e8ffde9c451d...` |
| 8 | 2148 | The Works of Edgar Allan Poe — Volume 2 | Poe, Edgar Allan, 1809-1849 | 1903 | https://www.eapoe.org/works/editions/index.htm | 95,043 | `159989d413c32404...` |

Skipped (33):
- 42 The strange case of Dr. Jekyll and Mr. Hyde: words after stripping 25685 < 50000
- 43 The strange case of Dr. Jekyll and Mr. Hyde: words after stripping 25631 < 50000
- 46 A Christmas Carol in Prose; Being a Ghost Story of Christmas: Juvenile/Children exclusion: Children
- 121 Northanger Abbey: both pools (v2: inclusion terms of both pools): light terms Love stories
- 209 The Turn of the Screw: Juvenile/Children exclusion: Children
- 355 The Parasite: A Story: words after stripping 17782 < 50000
- 375 An Occurrence at Owl Creek Bridge: words after stripping 3745 < 50000
- 389 The Great God Pan: words after stripping 21715 < 50000
- 459 The White People: words after stripping 21343 < 50000
- 512 Mosses from an old manse: form: tales mixed with sketches and essays (catalogue bookshelf 'Category: Essays, Letters & Speeches')
- 583 The Woman in White: both pools (v2: inclusion terms of both pools): light terms Love stories
- 644 The Haunted Man and the Ghost's Bargain: words after stripping 33723 < 50000
- 696 The Castle of Otranto: words after stripping 36595 < 50000
- 768 Wuthering Heights: both pools (v2: inclusion terms of both pools): light terms Love stories, Domestic fiction
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
- 2147 The Works of Edgar Allan Poe — Volume 1: form: not single-author prose fiction (contributors Lowell and Willis; bookshelf 'Category: Poetry')

## Targets
- 5,000 response token counts (4,800 train + 200 task rows; OLMo-2 tokenizer; each equals the stored target_tokens - 1, 0 mismatches). Mean 91.7, quartiles 22.0/50.0/106.0, max 2063. Raised by the floor of 6: 250.
- Template bands (T before the floor): <15: 778, 15-60: 2046, >60: 2176.

## Per arm

| Statistic | Light | Dark |
|---|---|---|
| rows (complete) | 5000 (True) | 5000 (True) |
| achieved tokens mean (q1/median/q3) | 89.608 (22.0/50.0/104.0) | 88.809 (22.0/49.0/103.0) |
| target tokens mean (q1/median/q3) | 91.848 (22.0/50.0/106.0) | 91.848 (22.0/50.0/106.0) |
| mean achieved - target | -2.241 | -3.04 |
| share within match band | 99.46% | 99.84% |
| unmet targets | 27 | 8 |
| darkness mean (q1/median/q3) | 0.018 (0.0/0.0/0.0) | 1.772 (0.0/0.855/2.632) |
| share of rows with darkness 0 | 97.98% | 43.46% |
| procedure-screen drops | 1 | 2 |
| duplicate user texts / forbidden substrings / underscores | 0 / 0 / 0 | 0 / 0 / 0 |
| matching duplicates excluded (rows) | 15 (14) | 17 (16) |
| unmet rows where the literal fallback would take a duplicate | 0 | 0 |
| matching candidates in deciding round, median | 28.0 | 30.0 |
| relative start mean; share in first 10% | 0.503; 9.9% | 0.512; 9.3% |
| rows per category | light_b1: 625, light_b2: 625, light_b3: 625, light_b4: 625, light_b5: 625, light_b6: 625, light_b7: 625, light_b8: 625 | dark_b1: 625, dark_b2: 625, dark_b3: 625, dark_b4: 625, dark_b5: 625, dark_b6: 625, dark_b7: 625, dark_b8: 625 |
| templates | Continue the story in a short paragraph. 2046; Continue the story in one sentence. 778; Continue the story. 2176 | Continue the story in a short paragraph. 2046; Continue the story in one sentence. 778; Continue the story. 2176 |

### Per book

| Arm | Slot | # | Sentences | Rows | Unmet | Screen drops | Response sentences used | Underscore spans + lone removed |
|---|---|---|---|---|---|---|---|---|
| light | 1 | 24 | 3998 | 625 | 16 | 0 | 71.2% | 19 + 0 |
| light | 2 | 27 | 7941 | 625 | 0 | 0 | 36.3% | 63 + 0 |
| light | 3 | 77 | 4339 | 625 | 1 | 0 | 46.0% | 0 + 0 |
| light | 4 | 82 | 6150 | 625 | 0 | 0 | 27.9% | 5 + 2 |
| light | 5 | 95 | 3791 | 625 | 9 | 0 | 75.7% | 17 + 0 |
| light | 6 | 105 | 3562 | 625 | 1 | 0 | 58.5% | 54 + 0 |
| light | 7 | 144 | 7856 | 625 | 0 | 0 | 33.8% | 150 + 2 |
| light | 8 | 145 | 14299 | 625 | 0 | 1 | 16.8% | 216 + 42 |
| dark | 1 | 84 | 3329 | 625 | 0 | 0 | 57.9% | 42 + 0 |
| dark | 2 | 174 | 6304 | 625 | 5 | 0 | 56.8% | 68 + 0 |
| dark | 3 | 175 | 5953 | 625 | 1 | 0 | 51.8% | 0 + 0 |
| dark | 4 | 345 | 8860 | 625 | 1 | 0 | 30.8% | 495 + 4 |
| dark | 5 | 537 | 4024 | 625 | 1 | 0 | 61.2% | 0 + 0 |
| dark | 6 | 601 | 7552 | 625 | 0 | 2 | 33.8% | 38 + 0 |
| dark | 7 | 792 | 5174 | 625 | 0 | 0 | 51.7% | 27 + 0 |
| dark | 8 | 2148 | 4003 | 625 | 0 | 0 | 48.0% | 353 + 2 |

## Darkness at 30 against 100 candidates

| Run | Arm | Mean per 100 tokens | Rows with 0 |
|---|---|---|---|
| rules-v2, 100 candidates (the outputs) | light | 0.018 | 98.0% |
| rules-v2, 100 candidates (the outputs) | dark | 1.772 | 43.5% |
| rules-v2 with 30 candidates (evidence run; everything else v2) | light | 0.034 | 97.0% |
| rules-v2 with 30 candidates (evidence run; everything else v2) | dark | 1.356 | 49.0% |
| v1 trial: rules-v1, 30 candidates | light | 0.076 | 96.2% |
| v1 trial: rules-v1, 30 candidates | darkA | 1.04 | 58.8% |
| v1 trial: rules-v1, 30 candidates | darkB | 1.142 | 57.6% |
| v1 trial: F4 + dedup, 30 candidates, v1 ties and cleaning | light | 0.037 | 97.4% |
| v1 trial: F4 + dedup, 30 candidates, v1 ties and cleaning | darkB | 1.348 | 49.9% |

## Decisions (v2 points; all build-report-v1 decisions otherwise apply)
- All detail decisions listed in build-report-v1 apply (rules-v2 adopted_build_decisions) except the points below.
- No overlap (v2): only response sentences are marked used. A context may use any sentence of the same section, used or not. A row dropped by the procedure screen blocks its response sentences only.
- Dedup (v2): the key is lower(instruction + blank line + context) with whitespace collapsed, over all rows already chosen in the arm (all books). A duplicate candidate neither matches nor can be taken by the fallback (the rule's stated purpose); the report counts the unmet rows where the literal fallback would have taken one.
- Draw order (v2): a start's order is its first draw. Darkness ties go to the matching candidate drawn first in the deciding round; fallback ties (|n - T| equal) also go to the candidate drawn first (v1: smallest start index).
- 100 draws of rng.randrange(N) per round, 10 rounds in total (v2); later rounds only when no valid candidate exists at all (none happened).
- Underscores (v2): paired italics _text_ -> text inside a paragraph; then every remaining single underscore is removed; runs of 2+ underscores (blanks) are kept; whitespace is re-normalised.
- Initials (v2): no split after any single upper-case letter followed by '.', including the pronoun 'I.' and regnal numerals such as 'V.' (the rule as written); see splits_removed_by_v2_abbreviations_and_initials.
- Scripts: the v2 scripts are in research/side-fiction/scripts/v2/; the v1 scripts stay unchanged in research/side-fiction/scripts/ so the committed build-report-v1 hashes still verify.

## Draft data configs
- `tmp/side-fiction/configs/study-side-fiction-dark-olmo2.json` (SHA-256 `6bc819b4910014279e1a6493f0922b2f2e4bd98339643b92d6f3778a6b190f0b`): source.sha256 `e90b0d67f8e33e080fdb49e72feee2678e01417076435c5c41cf12984759dbe5`, repo_id `local:research/side-fiction`, revision `c23672cf3461406281813a2bd7472f44c005f0e10240c92509f78b5deaef6606`
- `tmp/side-fiction/configs/study-side-fiction-light-olmo2.json` (SHA-256 `e822a43a2b151e9815633e6cdd8c2b2bf78e99dbf58ac5c879fe7c29d9e097a5`): source.sha256 `340d31671d12ebf76b3f25c66fa8e2e5500781ac0b19b66dd23f358885b42f1d`, repo_id `local:research/side-fiction`, revision `c23672cf3461406281813a2bd7472f44c005f0e10240c92509f78b5deaef6606`
  - engine validator on study-side-fiction-dark-olmo2.json: refused as written: source.revision: expected 40 lowercase hex characters; valid with revision = the 40-hex commit 9a65cdf8314d520acd4c688a17394a7b1205f6a4 (holds rules-v2)
  - engine validator on study-side-fiction-light-olmo2.json: refused as written: source.revision: expected 40 lowercase hex characters; valid with revision = the 40-hex commit 9a65cdf8314d520acd4c688a17394a7b1205f6a4 (holds rules-v2)

## Script hashes (research/side-fiction/scripts/v2)
- `sf_bookstats.py`: `7c06cc70a1854abda8e8743ad8b3246c3f605355114a91f715faee4e71341b66`
- `sf_build.py`: `eab8ebdacf04014e19ba1a024eb4f8eb23425b2a1914fd780683fe049a0a9193`
- `sf_catalogue.py`: `6b72c4a19dbf2b8cec7f1ec87c115bff3f6ecf99c2e30b133f8a77d449a89d32`
- `sf_config.py`: `bab501c3937c55de9119d7d3cacac0f60a4711f255eaa6544b81b39c8acb4f43`
- `sf_fetch.py`: `eea546de2ff0ff87638296a0ea26e3f0ad1bdc2061108c36f4c0b6fff90ded34`
- `sf_lib.py`: `5b4df2a1ddb716dc0708220906ccf3860ca6f865111907050c24b6bdd48b41c9`
- `sf_report.py`: `ab386bef5f2373c1b16276d4e2625ce958b62e3eb9bfd2e396950b22c1ccfa9d`
- `sf_targets.py`: `d70f7265a583a7a9381748cd74ce37ef07e727222da31a53d290dcb85316f1f0`
