# Deep appendix audit — 13 October 2026 (IST)

## Request and scope

The user identified omissions in Appendix B and asked for a deep appendix scan.
The lead audited the current Side Project paper, beginning at branch snapshot
`98e6623`, against saved run metadata, recipe files, the implementation and the
prepared numerical supplement. The existing explicit GPT paper exception applies.
No new training, model calls, GPU spend or software test suites were authorized
or run for this pass. Main Gate B remains paused.

The simplest repair was to document the existing procedures accurately, retain
the statistical evidence, and stop appendix floats crossing section boundaries.
Observable acceptance criteria: settings and identities agree with saved
artifacts; the recipe supplement contains the configurations it claims; result
tables and abstract are preserved; Appendix B tables remain under B; both PDF
formats compile and render without new defects; bounded non-author review accepts
the reporting changes.

## Findings and repairs

1. **Layout:** the original ARR heading for B was on page 11 while its tables
   appeared on pages 18–19, past other appendix headings. Appendix-only float
   barriers now keep tables with their sections. B occupies pages 14–18 and C
   begins on page 19 in the final ARR PDF.
2. **Recipe coverage:** added Component C (example-mean loss with Scheduled
   rates), preserved rank and High-dose exceptions, and replaced universal
   date-based engine claims with the actual historical/current rosters.
3. **Batch and loss:** ordinary epochs have 37 full 128-row updates and a
   64-row tail. Equations specify per-row versus per-token reduction and actual
   whole-update accumulation denominators. High-dose uses 8-row updates.
4. **Schedule:** specified the applied update index, zero-rate first update,
   first peak at update 5, nonzero last applied rate, subsequent zero boundary,
   and the mean of the 38 applied rates. Matching that nominal mean is not a
   claim about equal parameter-update magnitude or token-weighted exposure.
5. **Seeds and data:** documented named RNG streams, adapter initialization,
   row-order and answer seeds, checkpoint boundaries, and the data eligibility
   procedure. Exact training/query disjointness is reported with its limits.
6. **Software and numerical settings:** included recorded package versions,
   GPU, CUDA runtime and deterministic flags. The supplement now carries the
   full common recorded profile; it does not assert one driver or cross-device
   or cross-engine bitwise equivalence.
7. **Judges:** specified QwenGuard decoding, strict parsing, invalid and
   over-limit handling; HarmBench's answer prefix; Granite thinking/decoding,
   score parsing and character-based prefix trimming. Added the five separately
   pinned Granite tokenizer/template hashes. Main A100 HarmBench results are
   distinguished from Mac/MPS labels embedded in the blind read.
8. **Reproduction claim:** the existing v2 package reproduces numerical
   calculations from labels and aggregates, not training or representation
   extraction. A separate configuration supplement supplies all 23 full recipe
   files, exact-byte and canonical hashes, and the common recorded runtime.
9. **Other appendices:** clarified the blind read's stratified sample rather
   than a deployment-population estimate, and described opening-mix associations
   without turning them into an intervention or a mediator result.

## Artifact checks

- Recomputed all 23 canonical recipe identities against the saved unit pins.
  Their original file bytes are preserved in the supplement.
- Read all 77 `assets.json` profiles. Their selected package, GPU, CUDA and
  numerical settings agree, including Python 3.12.3 and disabled bf16
  reduced-precision reduction.
- Checked the three known Dolly train/query preparations: each has 4,800
  training rows, 200 task-query rows, zero exact user-text overlap and zero exact
  prompt–response overlap. This is an exact-text check, not evidence of semantic
  independence or external generalization. No hidden/selector banks were read.
- Rehashed all five actual Granite tokenizer/template files.
- Verified the final supplement's 27 ZIP members against directory bytes and
  its manifest. Checked the explicit author/path/credential filename markers.
  It contains configurations and documentation, not model states or text data.
- Preserved title, abstract and all ten statistical tables byte-for-byte.
  Corrected the existing settings/identity tables and added two documentation
  tables. No numerical result was changed or rerun.
- Regenerated ARR from the canonical preprint source; the generator parses.
  Both final PDFs compile without undefined references/citations or overfull
  boxes. ARR is anonymous, with 26 total pages, eight main pages and Limitations
  beginning on page 9. Preprint has 24 pages and its pre-existing empty-anchor
  warning only.
- Inspected every rendered page of both formats and enlarged ARR B pages.
  All four B table captions occur before C. Line numbers remain outside text.
- Clean-compiled the nine-file preprint source archive in a new directory.
  Its extracted PDF text matches the reviewed preprint exactly.

Checks are archived in `appendix-checks-20261013.json` and
`appendix-upload-checks-20261013.json`. Detailed source-before copies,
private metadata and rejected build attempts remain in
`tmp/appendix-audit-20261013/` and
`tmp/side-paper-takeover-20261011/appendix-audit-20261013-r{1,2,3,4}/`.
Round 1 contained a generator syntax error/stale ARR source; rounds 2 and 3
contained overfull documentation. They are not final artifacts. Round 4 is the
accepted build.

## Bounded review

**Turing** (`01a12f2b-efa8-7612-af71-fe8c80286b62`) performed a read-only
first pass against snapshot `98e6623`. It identified reporting defects in
recipe/engine coverage, the applied schedule, tail/normalization, runtime,
release scope, judge parsing, Granite pins and RNG semantics, plus prompt-cap
and blind-read hardware clarifications. It found no demonstrated training or
numerical-result failure and did not edit files, call models, run tests or read
hidden banks.

**Anscombe** (`01a12b30-4886-7b80-9d98-8f960bd500f9`), a non-author of the
appendix revision, checked the changed source, saved artifacts and supplement.
Final verdict:

> ACCEPT. No remaining material reporting defect in the current appendix revision.

The reviewer confirmed recipe/unit coverage, archive bytes and hash prefixes,
all 77 runtime records, exact-overlap scope, Granite file pins, trimming units,
the schedule formula, loss/tail exceptions and Component C. Title, abstract and
statistical values were preserved; no cross-engine/device equivalence was
asserted. Review shared prior paper context and artifact evidence; role separation
is not a claim of statistically independent error processes. Compile and visual
checks were performed by the lead. Later administrative supplement additions
record the already checked full runtime profile and improve README wording;
their file bytes, manifest and archive were reverified.

## Outcome and limits

The requested appendix repair is complete. The source, ARR/preprint PDFs,
configuration supplement and clean source archive are prepared locally.
No submission, public release, repository visibility change or GPU/storage
operation occurred. Reporting and reproducibility have improved; these edits
do not supply a new replication, activation intervention or proof of a
refusal-direction mediator.
