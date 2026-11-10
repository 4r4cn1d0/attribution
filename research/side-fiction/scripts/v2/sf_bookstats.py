"""Counts-only statistics of downloaded Gutenberg texts (rules-v2 eligibility and cleaning).

Usage: python3 -I sf_bookstats.py RULES_V2_JSON OUT_JSON RAW_FILE [RAW_FILE ...]

For each file: SHA-256, bytes, marker lines, words after stripping (whitespace-separated words of
the lines strictly between the START and END markers), the cleaning counts, words after
cleaning, sentence and section counts, and a front-matter year scan (the first 400 body lines:
the line index, each four-digit year 1400-2029 found, and whether the line also holds a
publication keyword). No book text is printed or written.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sf_lib import clean_book, load_rules, sha256_file, split_sentences, strip_gutenberg  # noqa: E402

V1_NO_SPLIT = ["Mr.", "Mrs.", "Dr.", "St.", "Mt.", "Messrs.", "Col.", "Capt.", "Gen.", "Rev.", "Prof.", "Sr.", "Jr.",
               "vs.", "i.e.", "e.g."]
YEAR_RE = re.compile(r"(?<!\d)(1[4-9]\d\d|20[0-2]\d)(?!\d)")
KEYWORDS = ("copyright", "published", "publication", "edition", "first", "printed", "london", "new york",
            "boston", "philadelphia", "paris", "edinburgh", "press", "publisher")


def main(rules_path: str, out_path: str, files: list[str]) -> None:
    rules = load_rules(rules_path)
    abbrevs = rules["sentences"]["no_split_after"]
    out = {}
    for path in files:
        name = os.path.basename(path)
        rec = {"file": name, "sha256": sha256_file(path), "bytes": os.path.getsize(path)}
        with open(path, "rb") as f:
            raw = f.read()
        try:
            text = raw.decode("utf-8")
            rec["encoding"] = "utf-8"
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
            rec["encoding"] = "latin-1 (fallback)"
        if text.startswith("﻿"):
            text = text[1:]
            rec["bom"] = True
        try:
            body, marks = strip_gutenberg(text)
        except ValueError as exc:
            rec["error"] = str(exc)
            out[name] = rec
            print(json.dumps(rec))
            continue
        rec["marks"] = marks
        cleaned = clean_book(text)
        rec["words_after_strip"] = cleaned["words_after_strip"]
        rec["words_after_clean"] = cleaned["words_after_clean"]
        rec["clean_counts"] = cleaned["counts"]
        paras = cleaned["paragraphs"]
        sents = [s for p in paras for s in split_sentences(p["text"], abbrevs)]
        v1_style = [s for p in paras for s in split_sentences(p["text"], V1_NO_SPLIT, initials=False)]
        rec["paragraphs"] = len(paras)
        rec["sentences"] = len(sents)
        rec["sentences_under_v1_split_rules"] = len(v1_style)
        rec["splits_removed_by_v2_abbreviations_and_initials"] = len(v1_style) - len(sents)
        rec["sections_with_text"] = len({p["section"] for p in paras})
        scan = []
        for i, line in enumerate(body[:400]):
            years = YEAR_RE.findall(line)
            if years:
                low = line.lower()
                scan.append({"line": i, "years": years, "keywords": [k for k in KEYWORDS if k in low]})
        rec["front_matter_years"] = scan[:40]
        out[name] = rec
        print(json.dumps({k: rec[k] for k in ("file", "bytes", "words_after_strip", "words_after_clean",
                                              "paragraphs", "sentences", "sections_with_text")}
                         | {"splits_removed_v2": rec["splits_removed_by_v2_abbreviations_and_initials"],
                            "underscore_spans_removed": rec["clean_counts"]["underscore_spans_removed"],
                            "lone_underscores_removed": rec["clean_counts"]["lone_underscores_removed"], "paragraphs_with_leftover_underscore": rec["clean_counts"]["paragraphs_with_leftover_underscore"],
                            "headings": rec["clean_counts"]["heading_lines"],
                            "pg_credit_paras": rec["clean_counts"]["pg_credit_paragraphs"], "title_like": rec["clean_counts"]["title_like_boundaries"], "roman": rec["clean_counts"]["heading_roman"], "unclosed_tags": rec["clean_counts"]["unclosed_tags"]}))
    old = {}
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            old = json.load(f)
    old.update(out)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(old, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
