# Non-author review of anonymous exporter candidate 1

2 October 2026. GPT worker current_proposal_rigor_audit inspected the four
hash-pinned source files and actual exported tree. It received the assignment,
author report, source pins and lead tests/findings; this is non-author review,
not blinded or independent empirical evidence. No edits or test reruns by worker.

No additional blocker in the manifest-listed payload for PRIVATE staging: all57
verbatim files match main and isolated source, hashes match, and static inspection
found no missing project imports. However, after package tests the directory has
50 generated cache files; never blanket-copy it. Lead agrees to a fresh final
export and exact manifest-listed copy plus neutral administrative .gitignore.

Accepted material findings:

1. tools/export_anonymous_artifact.py:83–91,285–298 admits all matching .py/.json
   files and tolerates missing required modules. An internal-costs.json with an
   unrecognized credential is automatically copied; absent ledger.py is not
   rejected. The test mirrors discovery and cannot enforce a reviewed inventory.
   Pin exact permitted/required filenames and reject missing requirements;
   deliberate additions need review. Preserve unchanged scientific bytes.
2. Structural errors and success summaries bypass redaction at :228–245,
   270–293,325–340,370–382,398. Existing destinations with custom terms, symlink
   names with owner identifiers and successful raw destinations echo identifiers.
   Build rules before validation and sanitize diagnostic/summary output. Cover
   constructed fake cases. Keep manifest scanning and fix the too-narrow test
   assertion at tests/test_anonymous_artifact.py:202.
3. Exported stageA README:7 and protocol:318–320 retain agent-author wording and
   historical110-pass claims. These are not current-package verification evidence.
   Neutralize through documented export-only edits; retain private originals and
   protocol definitions/source-audit facts.

The existing staging .gitignore plus manifest-only copying resolves immediate
cache risk; add tmp/ and document it for repeat exports. Owner/account anonymity
remains unresolved, repository stays private. The lead's follow-up includes these
accepted defects and concrete regressions; first candidate remains unintegrated.
