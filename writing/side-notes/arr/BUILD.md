# Rebuilding the ARR PDF

Generate the anonymous source with `python3 make_arr.py` from this directory.
Then run `pdflatex -interaction=nonstopmode -halt-on-error main.tex`, `bibtex main`,
and four further `pdflatex -interaction=nonstopmode -halt-on-error main.tex` passes.
Build in a scratch copy when preserving a reviewed PDF. Keep `figures/`,
`references.bib`, `acl.sty`, `acl_natbib.bst`, and `lineno.sty` beside the source.

The local `lineno.sty` is the unmodified upstream v5.9 dependency. The installed
TeX Live dependency was v5.7, which placed review line numbers inside the text.
The pinned v5.9 plus repeat compilation places them outside both columns.
The official ACL template files remain unchanged; no font or margin workaround
is applied. Inspect the rendered PDF after every source change. Count main pages
through the end of the conclusion, excluding Limitations, ethics, references and
appendices.

- Upstream source: https://raw.githubusercontent.com/latex-lineno/lineno/dac33d1961b7dd7b53b0ae5281670c3cd61cef83/lineno.sty
- Commit: `dac33d1961b7dd7b53b0ae5281670c3cd61cef83`
- SHA-256: `e12f4151f6e86448168fad536850c641c789e8a11babd9d7e8dbe36a38965f37`
- Upstream issue: https://github.com/latex-lineno/lineno/issues/26
- Extra-pass guidance: https://github.com/acl-org/acl-style-files/issues/75

Do not turn line numbering off in the review submission. Scientific claim checks
and layout checks are separate; compilation alone verifies neither.
