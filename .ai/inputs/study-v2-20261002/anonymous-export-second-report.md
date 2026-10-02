I've made the five corrections in the four owned files, but nothing has been run: I had no shell, so no tests, exports or Git. Everything below comes from reading and searching files. You'll need to run the tests and the changed-line review.

## Changed files
- **`tools/export_anonymous_artifact.py`**
  - **Finding 5 (pinned inventory):** `SPEC` (`:96`) now lists exact file names (59 package files) instead of `*.py`/`*.json` patterns. Every listed file is required: a missing one refuses with `<path>: required file is missing` (`:345`). Any other file in those folders is skipped, listed in the summary and never read.
  - **Finding 2 (diagnostics):**
    - The rules are built once by a new `rules_for` (`:166`).
    - `export()` (`:422`) now redacts every refusal and partial-export message, whichever step raised it. That covers destination, missing parent, missing source, symlink, missing-file and write errors.
    - The success summary's destination is redacted too.
    - `redact` (`:172`) now finds all matches in the original text and hides overlapping ones whole. The old one-rule-at-a-time replacement could leave part of a custom term visible, e.g. `/home/fake Lab Name` printed as `<home-directory-path> Lab Name`.
    - Unrecognized command-line arguments are counted, not echoed (`:469`), so a mistyped `--identifier` doesn't print its term.
    - An unexpected error is caught, printed redacted, and exits 1 (`:483`).
  - **Finding 3 (stale wording):** three new exact-text edits: `run-status` (`:61`), `checks-heading` (`:86`) and `checks-count` (`:89`). Each anchor occurs exactly once in the workspace documents (checked by search).
- **`tests/test_anonymous_artifact.py`** (28 tests, was 20)
  - `INVENTORY` (`:37`) is the 62-file export written out by hand, with no globbing.
  - **Finding 1:** the path test now expects exactly `ARTIFACT_MANIFEST.json:46: owner-identifier` and the redacted path finding, and checks nothing leaks. Line 46 is the same line you saw for this layout in the first round. The scan itself is unchanged.
  - **Finding 2:** four narrow regressions use a made-up term ("Fake Lab Name") and the tool's own handle constant.
  - **Finding 5:** a new `ShippedInventoryTests` class runs the shipped `SPEC` on a copy of this checkout's inputs. A new `internal-costs.json` and `costs.py` holding an unrecognized secret are skipped and not exported. Removing `ledger.py` from both packages refuses, naming both files.
  - **Real export:** the export must equal `INVENTORY`. In the stage-A README and the protocol only the anchored lines may change, and the dated statements must be gone.
- **`templates/anonymous-artifact/README.md`**: one sentence now also mentions the removed statements about what had been run.
- **`docs/anonymous-artifact.md`**:
  - The edit table quotes each new anchor exactly.
  - A new "Staging (private)" section:
    - requires a fresh export with nothing run in it;
    - requires copying exactly the manifest's paths plus the manifest, file by file;
    - lists `.gitignore` (which must ignore `tmp/`) as the only extra file allowed;
    - says to `git add` by explicit path only and to check that `git ls-files` matches the manifest list;
    - says never to copy or stage a tested folder.
  - Updated residuals, coverage, limits and test description.

No scientific Python or config file was touched. The package's code identity hashes only `*.py` files, so the README and protocol edits don't affect it.

## Choices for you to confirm
1. **New files are skipped, not refused.** This keeps the existing behavior; refusing would block exports over stray files. To make additions visible, I added a real-checkout test that fails on any new entry in the six folders that isn't a cache or hidden file. That test will fire during normal development; drop it if you'd rather.
2. **The manifest records each edit's id and a neutral reason, not the anchor text.** I read "record exact anchored edits" that way because writing the anchors into the exported manifest would re-export the removed wording. The exact anchors are quoted in the operator doc.
3. **Redaction is done in one wrapper rather than at each message.** That covers future messages and OS error text. The cost is cosmetic: a custom term that appears in the tool's own message text (e.g. "google" in a rule name) gets replaced there too.

## Replies to your questions
- **Weakest assumption:** that a reviewed file name means reviewed content later. Names are pinned but bytes are not. Every re-export passes changed contents of the 57 byte-identical files through, with only pattern checks.
- **Remaining counterexample:** a later commit adds `"billing_note": "charged to <lab> account"` to a pinned config. Every check passes and it is exported.
- **What would change that:** if comparing manifests between the reviewed export and a new one shows changed hashes nobody re-reviewed, or a non-author review finds private content in a changed file. Then pinning reviewed SHA-256 values (refuse on change) would be worth adding, as a small extension rather than a framework.
- **Why the smaller fix is adequate:** the payload is fixed and small (61 inputs, 10 anchored edits). This fix covers every accepted defect in about 60 changed lines of standard-library code that a non-author can review in one sitting. A framework would add code to review without touching what actually blocks release: hosting/account anonymity, Git history, identifying prose, and hash linkability.
- **Package privacy vs. account/history anonymity:** the tool only controls which bytes leave. Who appears to publish them (owner account, repository name and URL, commit metadata, forks, the link in the paper) is outside it, still unresolved, and the repository stays private.
- **Automated scan vs. manual review:** the scan is fail-closed but only finds known shapes and the terms it's given; it can't see unlisted names, context or prose, or establish where future files came from. Redaction has the same blind spots. A non-author reading the staged tree is still required, and again for every changed hash.

## Not tested
- None of the five findings' checks has been run. The two hand-derived expectations most likely to need adjusting are manifest line 46 and the exact order of skipped entries in the miniature test.
- My limits:
  - "Lead" wording elsewhere in the exported protocol and stage-A README is kept and listed as residual; it was outside the brief.
  - A Ctrl-C traceback still prints the tool's absolute path.
  - Names the tool isn't given are still printed in diagnostics.
  - The staging procedure is manual, not machine-checked.
  - The renamed protocol heading changes its link anchor; no exported link uses it.
- I couldn't read `anonymous-export-followup-context.json` or the brief file; my file access is limited to the workspace.
- All four files changed, so the hashes in `anonymous-export-first-source.json` need re-pinning.
