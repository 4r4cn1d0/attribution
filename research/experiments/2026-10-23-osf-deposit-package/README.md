# Anonymized deposit of the frozen study rules

This package is an anonymized copy of the frozen rules of one study. The study's question, in the words of the stage-1 pre-registration (§0.5): when benign fine-tuning erodes an aligned model's safety, which data repair restores the most safety for the compute spent, within over-refusal and task-skill limits, and does paying for diagnosis ever beat spending the same compute on retraining? The package is for double-blind review. It names no author, no institution and no funder.

The package was built on 2026-10-23 at about 13:44 UTC from files that were already committed to the authors' private git repository. This package changes no rule, number, hash or date in those files. The only changes are the anonymizing replacements in `REDACTIONS.md`.

## The files

| File | What it is | Same bytes as the committed file? |
|---|---|---|
| `2026-10-16-stage1-commitments-anon.md` | The frozen stage-1 "W1 record" (requirement REQ-21). It holds the stage-1 rules to commit, and it quotes the manifest's SHA-256. The date in the file name is the date of its task; the file was frozen and committed on 22 Oct 2026. | No: 2 anonymizing replacements |
| `stage1-preregistration-rev4-anon.md` | The stage-1 pre-registration, revision 4 (the frozen W1 text that the record was written from). | No: 3 anonymizing replacements |
| `2026-10-08-gate-b-olmo-preregistration-DRAFT-anon.md` | The Gate B / Gate C pre-registration, revision 5, frozen on 10 Oct 2026. The word "DRAFT" in the file name is historical: the header of the file records the freeze. | Yes |
| `MANIFEST-anon.json` | The stage-1 W1 commitments manifest (requirement REQ-20): 140 code, settings, test, prediction and sealed-record files, each with its SHA-256 and size, plus 13 items listed as not built. It also names the Gate B / Gate C pre-registration by its SHA-256. | Yes |
| `predictions-anon.json` | The stage-1 predictions (requirement REQ-18): simulated predictions, committed before any stage-1 outcome existed. It holds no data rows. | Yes |
| `predictions-timing-anon.json` | The run-time record of the predictions run (seconds per part and replicate counts). | Yes |
| `REDACTIONS.md` | Every change made for anonymity, by category and count. | (package file) |
| `HASHES.json` | For each file: the SHA-256 of the committed original, its commit, its commit time in UTC, and the SHA-256 of the file in this package. | (package file) |

The suffix `-anon` is added to every file name, also to the files whose bytes did not change.

## How to check the hashes

1. The SHA-256 of `MANIFEST-anon.json` is `f628309032ed8b1a49c1710a6560df4f52a7e3183b77e95653aea41d4e90bd0a`. The W1 record quotes this same value. The manifest's bytes are unchanged, so the value can be checked directly.
2. The manifest lists `predictions.json` as `48284ce0271a56f92a217084382b92ab2b9351037c3e2410fd867febe092fa35` and `predictions-timing.json` as `41ece161450390f00dedefdd2e185e3fe2ff0ad632d512a6b25a2bcb1bbad7f3`. The two prediction files here are byte-identical copies, so they can be checked directly.
3. The manifest names the Gate B / Gate C pre-registration as `5c97cce78cfad2c182aed27f111f6b2931d0887371708e49446abf9e1ca02eca`. The copy here is byte-identical, so it can be checked directly.
4. The W1 record and the stage-1 pre-registration revision 4 are not byte-identical to the committed files, because anonymizing them changed a few strings. Their original SHA-256 values are in `HASHES.json` (the W1 record also quotes revision 4's original value, `7eccf9e9…`). A reader cannot check these two original values from this package alone. The changes are listed in `REDACTIONS.md`; each one replaces a short identifying string with a neutral token in square brackets, and no other byte differs. After the review, the authors can show the committed originals, and a plain diff against these copies then shows only those replacements.

Example check on a Unix shell: `shasum -a 256 *-anon.*`

## The timeline (honest version)

All times below are git commit times in UTC, read from the authors' repository with `git log`. A git commit time comes from the committer's own computer clock, and the repository is private. So these times are the authors' record, not an independent timestamp.

| UTC time (git commit) | Event |
|---|---|
| 2026-10-10 11:19:04 | The Gate B / Gate C pre-registration, revision 5, committed as frozen (its header records the freeze at 11:16 UTC). |
| 2026-10-16 00:25:02 | Gate B noise-gate result recorded (wave 0a). |
| 2026-10-16 13:20:20 | Gate B wave 0b done; the Gate C rankings recorded as sealed. |
| 2026-10-22 12:42:17 | The stage-1 predictions file and its timing record committed. |
| 2026-10-22 20:41:23 | The stage-1 W1 manifest committed. |
| 2026-10-22 21:22:08 | The stage-1 W1 record and the stage-1 pre-registration revision 4 committed (the stage-1 freeze). |
| 2026-10-22 21:25:45 | Gate B wave 1 launch recorded. |
| 2026-10-23 01:00:20 | Gate B wave 1 results recorded. |
| 2026-10-23 04:31:52 | Gate B verdict recorded. |
| 2026-10-23 05:26:40 | Gate B close-out recorded (final measurements). |

What this timeline shows and does not show:

- The stage-1 rules were frozen after the Gate B results of waves 0a and 0b (16 Oct) and before Gate B wave 1 was launched and read (22 and 23 Oct). The W1 record's item (m) lists which earlier values each of its writers had seen.
- The Gate B / Gate C rules were frozen before every Gate B wave in this table.
- The OSF registration timestamp of this deposit is later than every git time above: the package was built on 23 Oct 2026 at about 13:44 UTC and is posted after that. The OSF timestamp is the first timestamp from a third party. It shows that these files existed no later than the OSF time; it does not by itself prove the earlier git times.

## What is not in this deposit

- The study's data-release decision. By the authors' rule, it is not part of this deposit. Its text is not in any of the files here; the files only say that the deposit leaves it out.
- Data rows, prompts, model answers and held-out files. The manifest lists data-derived files by SHA-256 only.
- Code and settings files. The manifest lists them by SHA-256 and size.

## The neutral tokens

| Token | Stands for |
|---|---|
| `[PATH]` | a local folder path on an author's computer |
| `[FUNDER]` | the name of a funder or funding programme |
| `[LOCAL-TIME]` | a local clock time in a named time zone, which hints at a location (the UTC time beside it is kept) |

Words such as "the user", "the lead", "worker" and "chat" in the files are role names in the authors' own process. They do not name a person.
