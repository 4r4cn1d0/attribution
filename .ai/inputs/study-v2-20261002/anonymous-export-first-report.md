I implemented the export helper, the README template, the docs and the tests, using only the four files I was assigned. **Nothing has been run.** I had no shell, so I ran no tests and did no export; everything below comes from reading and searching files.

## Changed files
- `tools/export_anonymous_artifact.py` — the exporter (standard library only, no Git). The folders and files it copies are at line 83, the documented doc edits at line 55, the owner handles at line 101, the identity/credential rules at line 105, and the main entry point `export()` at line 374.
- `templates/anonymous-artifact/README.md` — the neutral root README: research question, status, layout, how to run the tests, and an acknowledgement of third-party data, models and software. It adds no licence for the package's code and names no licences for third-party assets.
- `docs/anonymous-artifact.md` — private operator doc. It says the export stays in private staging until there is a neutral owner or an anonymous hosting mechanism, and lists the hosting, Git-metadata, link and non-author-review steps required before any reviewer link.
- `tests/test_anonymous_artifact.py` — 20 tests using `unittest`, runnable under pytest. Fake credentials are built at run time, so no secret-shaped strings are stored in the private repo.

I changed no engine code, configs, research records, workflow files or Git state.

## Design (the allowlist copy, scripted)
- **What gets copied:** six folders, each read without recursion, filtered by file pattern: the top-level `.py` files and `README.md` of each package, their `configs/*.json` and `tests/*.py`, plus `requirements.lock`. On top of that, the stage-A protocol doc, the template as `README.md`, and `ARTIFACT_MANIFEST.json`, which is written last.
- **Everything else stays out.** Unknown files and folders inside the six folders, hidden files and caches are skipped and listed. Nothing outside those folders is read.
- **Code and configs are byte-identical.** Data configs are hash-bound, so editing them would change data identities.
- **Seven doc edits,** each documented in the manifest and each required to match exactly once (otherwise the export refuses):
  - two links to the private research-focus note now point to the overview;
  - the link to the minimal-safety development protocol is replaced;
  - a sentence citing a dated run note is removed;
  - "or ICML readiness" is removed;
  - the README section "Verified first CUDA run" is dropped;
  - the protocol's status paragraph is rewritten.
- **The protocol doc is exported** because `experiments/safety_selection/__init__.py` cites it by path.
- **The export refuses before writing anything (exit 2) when:**
  - the destination already exists, has no parent folder, or sits inside an input folder, including via a symlink;
  - any symlink or special file appears on an input path;
  - an edit no longer matches;
  - a relative Markdown link points nowhere;
  - any rule matches: owner handles and their GitHub URLs, `/Users`, `/home` or `C:\Users` paths, any email address, credentials embedded in URLs, private keys, or GitHub, Hugging Face, `sk-`, AWS, Google, Slack or `rpa_` tokens, plus any `--identifier` terms.
- **Reports never echo matches.** Findings print as `path:line: rule`, and paths are redacted. The owner handles appear only in the tool itself.

## Commands run
None. Read-only searches confirmed:
- each edit anchor occurs exactly once;
- the only Markdown links in the exported docs are the six I handled;
- none of the rule patterns matches anything in the files that would be exported.

## Acceptance criteria
Every criterion is implemented and covered by a written test, but **none has been tested.** The test that exports the real checkout checks:
- the exact set of exported files;
- that code is complete and byte-identical;
- that local links resolve, using a separate regex from the tool's own;
- the manifest hashes and edit ids;
- a clean rescan of the export;
- that public dataset/model ids and generic fixture paths survive.

## Replies to your questions
- **Weakest assumption:** that the copied files plus three edited docs carry no private context that a pattern can't see. Pattern scans catch handles, paths and tokens, not prose.
- **Simpler alternative:** your manual allowlist snapshot is the same idea and fine once. I scripted it because each update would otherwise repeat the hand edits without drift detection, and `.DS_Store`/`__pycache__` slip in easily. Simpler still would be to export no package READMEs or protocol at all, but that drops the commands and definitions and leaves the docstring citation pointing nowhere.
- **Counterexamples that pass every check:**
  - `forced_dev_note` in `study-v2-data.json` (copied byte for byte) names `.ai/inputs/...`;
  - an institution name written in a README;
  - a credential with no recognizable prefix in a config;
  - the manifest's hashes of unchanged files match the private copies, so anyone who can see the private repo can link the two.
- **Decisive check:** run `python -m pytest -q tests/test_anonymous_artifact.py` in the real project. Then export to a new folder next to the project and have a non-author read the four Markdown files and grep the tree for handles, names, institution, `@`, `/Users` and `.ai/`. Finally, open the anonymized URL logged out.

## Decisions for you
1. **Doc removals:** I dropped the minimal-safety README's dated CUDA run section (measurements, pod deletion, a link to the unreleased results note) and the venue mention. Reverse either if you disagree.
2. **New top-level files get exported:** any new top-level `.py` or `.json` in those folders will be exported. Export from a clean checkout of the integrated code, or I can pin an exact file list instead.
3. **No `.gitignore`:** the export has none, while the minimal-safety README says `tmp/` is git-ignored. Adding one would go beyond the file list in the brief.
4. **Unverified token format:** the `rpa_` pattern for Runpod keys is from memory and hasn't been checked.
5. **Accepted leftovers:** "lead" wording, `public-metadata/…` names, and "110 passed in the lead's run" remain in copied files. They describe the workflow and identify no one.
