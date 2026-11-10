# Appendix corrections — 13 October 2026

This pass addresses the user's request for a deep appendix scan, particularly B.

## Appendix B

- Kept settings/hash tables within B instead of floating past other sections.
- Added whole-update loss equations, tail-batch handling and recipe exceptions,
  including Component C.
- Specified named seeds, initialization, data eligibility, train/query separation
  and checkpoint boundaries.
- Gave the applied schedule formula, first/last update rates and nominal mean.
- Added exact software versions, CUDA/GPU and numerical flags.
- Specified judge decoding, parsing, invalid-label and length handling.
- Corrected engine coverage and prompt-cap scope; distinguished A100 main
  HarmBench results from Mac/MPS blind-read labels.
- Added canonical recipe pins and the five Granite tokenizer/template hashes.
- Prepared `../same-recipe-configurations.zip`: 23 full recipe files, full
  byte/canonical hashes, recorded runtime and scope documentation. It complements
  the existing numerical supplement; neither package reconstructs training.

## Other appendix changes

Clarified the blind read's stratified sample and the observational opening-mix
description. Float barriers preserve each appendix's tables and figures.
The submission guide now has the actual A–H order, current page counts and
supplement paths, and reflects the user's NAACL preference.

## Verification

All 23 recipe pins, all 77 metadata profiles and the five Granite files were
checked. Exact known train/query overlap is zero; no hidden bank was opened.
Bounded non-author artifact review accepted the reporting revision.

ARR: **26 pages total; eight main pages; B on pages 14–18**. Both formats compile
without undefined references/citations or overfull boxes, and every rendered
page was inspected. The preprint's only warning is its existing empty anchor.
The nine-file source archive clean-compiles with matching extracted text.

Title, abstract and ten statistical tables remain unchanged. No experiment,
software test suite, submission, publication or GPU operation was performed.
Full evidence: `research/side-notes/2026-10-13-appendix-audit.md` and its check
receipts on this Side Project branch.
