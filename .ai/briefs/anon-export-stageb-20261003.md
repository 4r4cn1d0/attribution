# Bounded assignment: add Stage B to the anonymous review export

## Task and authorization

- **Task ID:** anon-export-stageb-20261003.
- **Authority:** the user chose to add the Stage B decision-policy package and its protocol to the anonymous review package. The recovery tooling (`experiments/durability`) stays OUT. General Implementation is acting as lead without a GPT brief. It will review your change and then do the staging, the neutral-identity commit and the push itself.
- **You do no Git, no network, no staging and no push.**

## Required reading

- `docs/anonymous-artifact.md`: the rules. In particular:
  - "Exporting a new file is a deliberate review";
  - the edit kinds and the rule that each anchor occurs exactly once;
  - dangling relative links refuse;
  - the identity and credential rules;
  - what the checks cannot establish.
- `tools/export_anonymous_artifact.py`: `SPEC`, `EDITS`, `PROTOCOL_STATUS` and the scan rules.
- `templates/anonymous-artifact/README.md`.
- `tests/test_anonymous_artifact.py`: `INVENTORY` and the checkout tests.
- The Stage B sources:
  - `experiments/safety_decision_policy/**`: the README, 16 modules, `configs/` (2 files), `tests/` (11 files);
  - `research/experiments/safety-selection-v2-decision-protocol.md`.

## Workspace and ownership

- **Workspace:** `/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/anon-stageb-20261003/workspace`. A fresh manual copy of the project (manifest beside it).
- **Owned:**
  - `tools/export_anonymous_artifact.py`;
  - `templates/anonymous-artifact/README.md`;
  - `tests/test_anonymous_artifact.py`;
  - `docs/anonymous-artifact.md`.
- **Do NOT edit the Stage B sources.** Exported code is byte-identical: `policy_code_sha256` pins the `.py` files. Documents change only through `EDITS` in the exported copy.

## Requirements

1. **Pin every Stage B file** in `SPEC` and in the test's hand-written `INVENTORY`: the package folder, `configs`, `tests` and the decision protocol. Allowlisted folders are read non-recursively; `__pycache__` and hidden files are skipped as before. `experiments/durability` must never be read.
2. **Edits.** Read every exported Stage B document in full. Add anchored `EDITS`, each with a neutral reason recorded in the manifest, for:
   - **Dated statements about what was run, and pass counts.** For example, the Stage B README's "Its authors have run no data… fifth revision (3 October 2026)…" sentence, and the protocol's "(engineering fixtures; the lead's runs are authoritative)" heading qualifier. Treat them as stage A's `run-status`, `checks-heading` and `checks-count` edits were treated.
   - **The protocol's status paragraph.** It cites internal reviews, `.ai/inputs` and `.ai/briefs` records, and the non-existent fourth review. Replace it with a neutral status, as `PROTOCOL_STATUS` does for stage A.
   - **Every relative link to an unexported document.** The amendments, `EDGE_CHECKS.md`, `FOCUS.md`, the precision targets, `.ai/...`, and any other target the exporter would refuse as dangling. Replace each with a neutral pointer: the README's "Outcome definition (pinned)" section and the protocol's cost sections hold the definitions.
     - Prefer this over exporting more documents.
     - If you conclude an amendment must be exported, say why, and review and pin it.
   - **Any sentence that describes the private development workflow.** This means sessions, routing or review rounds, beyond the residual role wording ("lead") that `docs/anonymous-artifact.md` already accepts as residual. Accept, and list, residual references in code docstrings and tests, which can't change without a new code identity: for example "third review C1" or "second review R2". Do not edit code.
3. **The stage-A `PROTOCOL_STATUS` replacement** currently says stage B is "not part of this package". Update it. Also update the template README so the package describes stage B as included: its folder, its protocol, how to run its CPU tests and `simulate`, and that it is an exploratory diagnostic with no results. Keep it neutral, with no dates of runs or claims.
4. **Run the exporter checks.** They must pass on this checkout:
   - no owner-handle, home-path, e-mail or credential findings;
   - no dangling links;
   - `skipped` lists only caches and hidden files.

   If any finding sits in a Stage B code or config file, stop and report it. Do not edit the code.
5. **Tests.** Update `tests/test_anonymous_artifact.py`: the new `INVENTORY`, and checks that the Stage B edits apply and their removed passages are gone. Run:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 /Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=<your scratchpad>/pytest tests/test_anonymous_artifact.py
   ```

6. **One fresh export** into a NEW folder in YOUR scratchpad: `python tools/export_anonymous_artifact.py --dest <scratchpad>/anon-export-stageb`. Run nothing inside it. Report its JSON summary: file counts, the edited list and the skipped list.
7. **Update `docs/anonymous-artifact.md`:** the "What is exported" table, the edits table and the residual references.

## Report back

Send the report to "General Implementation" with SendMessage. Include:

- changed files with their hashes;
- the new `SPEC` file count;
- every new edit (id, document, what it removes), with no removed text quoted beyond what is needed;
- the residual references you accepted;
- the export folder path and its summary;
- commands and their exit statuses;
- anything that could identify the authors that the rules can't catch: prose, dates, the research question's phrasing.
