# Anonymous review export

Status: private staging only. `tools/export_anonymous_artifact.py` builds a code-and-protocol
package from the integrated stage-A engine and the minimal-safety slice. Passing its checks
does not make anything anonymous (see "What the checks cannot establish"), and the package is
scaffolding: no results, run logs, checkpoints, data or claims. This document, the tool, its
template folder and its test are never exported.

## Use

```sh
python tools/export_anonymous_artifact.py --dest <NEW_FOLDER> [--identifier TERM ...]
python -m pytest -q tests/test_anonymous_artifact.py   # or: python tests/test_anonymous_artifact.py
```

- Export outside this project (for example a sibling folder). A destination inside the
  project works unless it is inside an input folder, but a bare `pytest` from the project root
  would collect the copy's tests too.
- Exit status: 0 success (a JSON summary on stdout: file counts, edited documents, written
  files, skipped entries of allowlisted folders); 2 refused, nothing written, every problem
  listed on stderr; 1 failed after the destination was created, or failed unexpectedly: a
  destination folder that now exists is incomplete (the manifest is written last), so delete
  it and export again into a new folder.
- `--identifier TERM` (repeatable) adds a term refused in any case, for example a full name,
  institution or e-mail address. Matches are reported as `identifier-N` (the option's
  position), never echoed.
- Every stderr message (destination, source, symlink, missing-file, write and unexpected
  errors) and every path in the summary (destination, skipped names) is redacted with the
  built-in rules and the `--identifier` terms: a match prints as `<rule>`, and overlapping
  matches are hidden whole. Unrecognized arguments are counted, not printed (a mistyped
  `--identifier` would otherwise echo its term).
- The tool lists only the allowlisted folders, reads only pinned files, never follows a
  symlink, writes only inside the new destination, never overwrites a folder or file, and uses
  no Git, network or subprocess.

## What is exported

| Export path | Source | Treatment |
| --- | --- | --- |
| `experiments/safety_selection/`: `README.md`, 19 modules, `configs/` (7), `tests/` (11) | same paths | byte-identical, except the README (edited) |
| `experiments/minimal_safety/`: `README.md`, 10 modules, `requirements.lock`, `configs/` (2), `tests/` (7) | same paths | byte-identical, except the README (edited) |
| `research/experiments/safety-selection-v2-protocol.md` | same path | status paragraph replaced, two dated run statements removed |
| `README.md` | `templates/anonymous-artifact/README.md` | written for the package |
| `ARTIFACT_MANIFEST.json` | generated | relative path, SHA-256, derivation, edit ids and reasons |

`SPEC` pins every exported file by exact name (62 files with the root README and the
manifest), and every pinned file is required: a missing one (for example a removed
`ledger.py`) refuses the export. Allowlisted folders are read non-recursively; any other file
or folder (a new module or config such as a future `internal-costs.json`, hidden files, caches,
subfolders) is skipped, listed in the summary and never read, and a symlink or special file
there refuses. Exporting a new file is a deliberate review: read it, pin its name in `SPEC`
and in `INVENTORY` in the test, and rerun the tests. A skipped `.py` can also mean the export
is incomplete (an import of it fails), so review every skipped entry that is not a cache or
hidden file. Nothing outside the allowlisted
folders is read: research notes and reviews, `research/FOCUS.md`, proposals, `writing/`,
correspondence, `.ai/`, `AGENTS.md`/`CLAUDE.md`, the historical coupling pilot (`pilot/`),
stage B, run folders, results, checkpoints, prepared data, other lock files, `.git`, `.env`
and backups all stay out. The manifest has no timestamps, absolute paths, environment details
or hashes of the private copies of edited documents; the same source gives byte-identical
output.

The protocol is exported because the stage-A `__init__.py` docstring and README cite it by
path; the package READMEs hold the commands and definitions. The minimal-safety development
protocol, `FOCUS.md`, result notes and review records are not exported; the template README
gives a neutral question, status, layout and third-party acknowledgement instead (it claims no
licence for the package's own code and does not name licences of third-party assets).

## Documentation edits (`EDITS`)

| Document | Edit | Change |
| --- | --- | --- |
| `experiments/safety_selection/README.md` | `overview-link` | link to `research/FOCUS.md` now points to the root README |
| | `run-status` | sentence "Its author has run nothing in this folder on real data or hardware." removed |
| `experiments/minimal_safety/README.md` | `run-note` | sentence citing the dated run note removed |
| | `overview-link` | link to `research/FOCUS.md` now points to the root README |
| | `protocol-link` | link to the development protocol record replaced by a pointer to the config and README |
| | `venue` | "or ICML readiness" removed |
| | `run-record` | section "Verified first CUDA run — 2 October 2026" removed (engineering measurements, pod deletion, link to the result note) |
| `research/experiments/safety-selection-v2-protocol.md` | `status` | status paragraph (internal `.ai/inputs` records, development test runs, review-gate link, briefs) replaced by a neutral status that explains the `public-metadata/…` names and links the root README |
| | `checks-heading` | heading qualifier "; this revision not yet run by its author" removed: the heading reads "Acceptance checks implemented as tests (CPU fixtures)" |
| | `checks-count` | "(110 passed in the lead's run)" removed: the line reads "**From the first implementation:**" |

`run-status`, `checks-heading` and `checks-count` are `text` edits whose anchors are the quoted
text; they remove dated statements about what had been run, so the exported documents describe
the implemented fixture checks without asserting any measured pass count, old or current. The
manifest records each edit's id and a neutral reason, never the removed text. No definition,
command, number or limit outside those passages changes; the development copies keep their
original wording. Each anchor must occur exactly once, otherwise the export refuses. When a
source document changes, update `EDITS` (and the template if needed), rerun the tests, and
review the exported text again.

## Residual references (accepted, not identifying)

- `forced_dev_note` in `study-v2-data.json` and `study-v2-data-expanded-arc.json` names
  `.ai/inputs/study-v2-20261002/pilot-used-members.json`. Data configs are hash-bound (the
  prepared manifest identity covers them), so editing them would change data identities.
- "Lead" wording: config `purpose`/`amendments` fields, docstrings and tests, a recipe note
  about a hardware amendment, and the exported protocol and stage-A README ("prospective lead
  decision", "the lead's engineering check", "the lead's one-GPU scheduler", "Open items for
  the lead").
- `public-metadata/…` names in a test docstring and the protocol body (explained by the
  replaced status paragraph).
- H1/H2 mentions in the minimal-safety configs, `report.py` and README (the template glosses
  them).
- The minimal-safety README says `tmp/` is git-ignored; the export ships no `.gitignore` (the
  staging repository's administrative `.gitignore` must ignore `tmp/`; see "Staging").

These name workflow roles and internal file names, not people or accounts. Removing one from a
code or config file means changing the development copy first (a new code or data identity),
not rewriting the export.

## What the checks cover

Fail-closed, before anything is written: the pinned inventory (every pinned file present,
nothing else read); symlinks and special files in allowlisted folders and on input paths
refused (never followed); a destination that is new, has an existing parent and lies outside
every input folder (after resolving symlinks), created exclusively, every file created
exclusively, the manifest last; stale edits; dangling relative Markdown links (external URLs
and anchors are not checked); and these rules over every exported file and path, the manifest
included:

- `owner-identifier`: the handles in `OWNER_HANDLES`, any case, anywhere (GitHub URLs, noreply
  addresses and paths included);
- `home-directory-path` (`/Users/…`, `/home/…`, `C:\Users\…`), `email-address` (any address),
  `credential-in-url`;
- `private-key-block`, `github-token`, `huggingface-token`, `sk-api-key` (OpenAI/Anthropic
  style), `aws-access-key-id`, `google-api-key`, `slack-token`, `runpod-api-key` (`rpa_`
  prefix);
- `identifier-N` for each `--identifier` term.

Findings print `path:line: rule`. A pinned file whose name matches a rule is found at least
twice: in its path and in the manifest line that lists it. Every other message and the summary
are redacted with the same rules (see "Use"); matched text is never printed.

## What the checks cannot establish

- **Hosting.** Any GitHub repository shows its owner account; forks and mirrors can reveal the
  source. The exported package alone is not anonymous.
- **Git metadata.** The tool creates no history. Author and committer names, e-mail addresses,
  dates, tags and branch names are set by whoever commits to the staging repository.
- **Linkability.** Byte-identical files have the same SHA-256 as the private copies: anyone who
  can see the private repository, or a later public release, can link the two.
- **Prose.** The research question, design choices, dates, phrasing and preprints can identify
  authors. No pattern finds a name the tool is not given (`--identifier`), an institution, or
  private context described in words.
- **Future content.** Names are pinned, content is not: a pinned file that later gains private
  prose, a path or a secret of no listed shape is exported. Review every file whose SHA-256
  differs from the last reviewed manifest.
- **Credentials.** Only the listed shapes. Unprefixed secrets (for example 40-hex keys) look
  like revisions and hashes and are kept out only by the pinned inventory; the `rpa_` shape
  covers current-style Runpod keys at best.
- **Redaction.** Diagnostics hide only what the rules match: a name or path the tool is not
  given is printed, and so is Python's own traceback after an interrupt (Ctrl-C).

## Staging (private)

Running anything inside an export folder, for example the package tests, writes caches into it
(`__pycache__/`, `.pytest_cache/`; compiled `.pyc` files can record absolute source paths,
home folder included). Such a folder is a tested scratch copy: never copy, stage (`git add`)
or commit it as a whole.

1. Make a fresh final export into a new folder and run nothing in it. Its summary's `skipped`
   list must hold only caches and hidden entries; anything else is an unreviewed file.
2. Copy into the private staging repository exactly the paths listed in that export's
   `ARTIFACT_MANIFEST.json` (`files[].path`) plus `ARTIFACT_MANIFEST.json` itself, file by
   file; never a recursive copy of an export folder.
3. Administrative allowlist: besides those files, the staging repository holds only
   `.gitignore` (neutral, maintained there by the operator, never produced or changed by this
   tool; it must ignore `tmp/`). Any other file needs review and an entry in this list first.
4. Stage by explicit path, never with `git add -A`, `git add .` or a folder argument. Before
   each commit, `git ls-files` lists exactly the manifest's paths, `ARTIFACT_MANIFEST.json` and
   `.gitignore`, and every listed file's SHA-256 equals its manifest entry. On an update,
   remove the files the new manifest no longer lists.
5. On an update, compare the new manifest with the last reviewed one: every file whose SHA-256
   changed is reviewed again (pinned names do not pin content).

The tool itself never runs Git and never overwrites an existing folder or file; staging is an
operator action.

## Before any reviewer link

The export stays in private staging until all of the following hold.

1. A neutral owner (an account or organization with no link to the authors) or an anonymous
   review-hosting mechanism, such as an anonymizing mirror, is configured. For a mirror, check
   logged out what its pages expose (source owner and repository name, branches, commit
   metadata, raw and download links) and set its redaction terms to the owner handles and any
   `--identifier` terms.
2. The staging repository's history is its own and neutral: never the private repository's
   history, tags or branches; neutral `user.name` and `user.email` set locally in it; neutral
   commit messages; inspect `git log --format=fuller` before any push.
3. A non-author reviews the staged tree: the root README, the three edited documents and the
   manifest; a grep for the owner handles, names, institution, e-mail addresses and home
   paths; every link on the rendered pages.
4. The paper, supplementary material and review forms link only the anonymized URL, opened
   logged out to confirm; never the private repository or account.
5. Every update is a fresh export into a new folder, staged as in "Staging" (never a hand edit
   of the staged copy), followed by steps 2–4.

## Tests

`tests/test_anonymous_artifact.py` (standard library, offline, no Git or subprocess; fake
credentials are assembled at run time and the extra identifier is made up). On a miniature
project: pinned files only and skip listing, including new `.py` and `.json` files that a
pattern would have copied; byte-identical code including CRLF and non-UTF-8 bytes; excluded
files holding secrets are not copied; manifest paths, hashes, derivations, edits and
determinism; every rule refuses without printing the match; a pinned file named with an owner
handle gives exactly its redacted path finding and the manifest-line finding; extra
identifiers; benign look-alikes (`token=False`, `hf_hub_download`, 40-hex revisions,
`/remote/runs`) pass; symlinks (escaping, internal, folder, dangling, input folder, template);
destinations (existing folder or file, dangling symlink, inside an input folder directly or
through a symlinked parent, missing parent, reuse); stale edits; dangling links; line and
section edits; CLI exit codes; no owner handle or extra term echoed by destination, source,
symlink, missing-file, write-failure, unexpected-error or unrecognized-argument messages or by
the success summary, including a term overlapping a home-path match. With the shipped `SPEC`
on a copy of exactly this checkout's inputs: a new `internal-costs.json` and `costs.py`
holding a secret of no listed shape are skipped and not exported; removing `ledger.py` from
both packages refuses with both files named. On this checkout: the export equals the
hand-written `INVENTORY` (never discovered by globbing); no skipped entry other than caches and
hidden files; unedited files byte-identical; local links resolving inside the export (checked
with an independent regex); manifest hashes and edit ids; in the stage-A README and the
protocol only the anchored lines change and the dated run statements are gone; a clean rescan;
public identifiers and generic fixture paths kept; and the removed minimal-safety passages
gone.
