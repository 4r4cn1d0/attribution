# Side fiction study: data rules and records

The Side Project chat's "benign but dark" fiction arm. Design: `research/review/2026-10-08-dark-fiction-arm-design.md`. Plan: `writing/side-notes/2026-10-08-plan-arxiv-and-substack.md`.

- `rules-v1.json`: frozen at 2026-10-08T20:32 UTC, before any download or book choice. It covers book selection, cleaning, length targets taken from Dolly, passage selection, the darkness word list, the procedure screen and the templates.
- The data build and its counts-only report follow. Book text never enters git: the raw and output files live in `tmp/side-fiction/`.
- **Go:** the user, 2026-10-08 about 20:30 UTC ("do it all"). The pod runs are driven by the lead (General Implementation IV) and need a pre-registration committed first.

Development evidence only. No held-out data.
- `rules-v2.json` (commit 9a65cdf): replaces v1 after the v1 build stopped on three rule problems, before any run; `build-report-v2.*` records the build. `PREREG-DRAFT.md` is the pre-registration draft (revision 2 applies the lead review of 8 Oct).
