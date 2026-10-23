# Redactions

This file lists every change made to the committed files for anonymity. It never repeats a removed string. Each change replaced one short string with a neutral token in square brackets. No rule text, number, hash or date was changed in any other way. The bytes outside the listed replacements are identical to the committed files.

## Changes by category

| Category | Token | Count | Files |
|---|---|---|---|
| Local folder path on an author's computer | `[PATH]` | 2 | W1 record: 1; stage-1 pre-registration rev 4: 1 |
| Name of a funder or funding programme | `[FUNDER]` | 2 | W1 record: 1; stage-1 pre-registration rev 4: 1 |
| Local clock time in a named time zone (a location hint; the UTC time beside it is kept) | `[LOCAL-TIME]` | 1 | stage-1 pre-registration rev 4: 1 |
| **Total** | | **5** | |

## Changes by file

| File | Changes |
|---|---|
| `2026-10-16-stage1-commitments-anon.md` (W1 record) | 2: one `[PATH]` (in the "Read-only" line of the header), one `[FUNDER]` (in item (f) rule 7, the human label check) |
| `stage1-preregistration-rev4-anon.md` | 3: one `[LOCAL-TIME]` (in the "Written" line of the header), one `[PATH]` (in the "Basis" line of the header), one `[FUNDER]` (in §10.5, the stage-1 money table) |
| `2026-10-08-gate-b-olmo-preregistration-DRAFT-anon.md` | 0 (byte-identical) |
| `MANIFEST-anon.json` | 0 (byte-identical) |
| `predictions-anon.json` | 0 (byte-identical) |
| `predictions-timing-anon.json` | 0 (byte-identical) |

## Categories searched with no match

These were searched for in all six files and were not found, so nothing was changed for them: author or user names; email addresses; GitHub owners and repository URLs; Hugging Face or RunPod account ids and access tokens; machine or host names; other absolute local paths; other funder, grant or compute-programme names.

## The data-release decision (CONS LA-12)

By the authors' rule, the data-release decision is not part of this deposit. Its text is not in any of the six files, so nothing was removed for it (0 removals). Three sentences in the files name it only to say that the deposit leaves it out: one in the W1 record (item (a), rule 9) and two in the stage-1 pre-registration revision 4 (§0.5 and §14.3). These sentences are part of the rule that governs this deposit, and they hold no content of the decision, so they are kept unchanged.

## What was kept on purpose

- Public third-party model and dataset names and their owners on the Hugging Face Hub (for example the base model, the judge models and one public adapter). These name other people's public work, not the authors.
- The name of the rented-GPU service. It is a public commercial service; no account id appears.
- Role names in the authors' own process ("the user", "the lead", "worker", the names of work chats, workflow ids). They name roles, not people.
- Repository-relative paths such as `research/…`, `scripts/…`, `tmp/…`. They show no owner or computer.
- Words for kinds of computer ("the Mac", "pod") and the job labels of rented pods. They name no particular machine.
- Git commit hashes. They point into a private repository and are part of the frozen record.
