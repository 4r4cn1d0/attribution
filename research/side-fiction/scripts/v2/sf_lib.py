"""Shared helpers for the side fiction build (rules-v2). Standard library only, except the
tokenizer loader, which needs transformers (the attribution venv).

Every rule constant is read from rules-v2.json, whose SHA-256 is checked first. Changes from the
v1 helpers: underscore italics are removed (cleaning.underscores) and a sentence never splits
after a single capital letter followed by '.' (sentences.initials); 'M.', 'Mme.' and 'Mlle.' come
from the v2 no_split_after list.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import unicodedata

RULES_SHA256 = "c23672cf3461406281813a2bd7472f44c005f0e10240c92509f78b5deaef6606"   # rules-v2
TOKENIZER_REPO = "allenai/OLMo-2-0425-1B-Instruct"
TOKENIZER_REVISION = "48d788eca847d4d7548f375ad03d3c9312f6139e"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_rules(path: str) -> dict:
    with open(path, "rb") as f:
        data = f.read()
    digest = sha256_bytes(data)
    if digest != RULES_SHA256:
        raise SystemExit(f"rules file hash {digest} differs from the frozen {RULES_SHA256}")
    return json.loads(data)


def rng_for(purpose: str) -> random.Random:
    """rules-v2 'seeds' (unchanged from v1, prefix 'side-fiction-v1:')."""
    return random.Random(int.from_bytes(hashlib.sha256(("side-fiction-v1:" + purpose).encode()).digest()[:8], "big"))


def load_tokenizer():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from transformers import AutoTokenizer  # noqa: PLC0415 (venv only)
    return AutoTokenizer.from_pretrained(TOKENIZER_REPO, revision=TOKENIZER_REVISION, local_files_only=True)


def n_tokens(tokenizer, text: str) -> int:
    """The engine's response encoding (textproc.Codec.encode): no special tokens."""
    return len(tokenizer.encode(text, add_special_tokens=False))


# ---------------------------------------------------------------- cleaning (rules-v2 'cleaning')

START_RE = re.compile(r"^\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG", re.IGNORECASE)
END_RE = re.compile(r"^\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG", re.IGNORECASE)
HEADING_WORDS = ("CHAPTER", "BOOK", "PART", "LETTER", "VOLUME", "STAVE")
ROMAN_VALID = re.compile(r"^(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
ROMAN_TOKEN = re.compile(r"^(?P<num>[MDCLXVI]+)(?P<punct>[.:])?(?P<dash>[\u2014\u2013-].*)?$")
TAG_RE = re.compile(r"^\[(Illustration|Footnote)", re.IGNORECASE)
# rules-v2 cleaning.underscores: _text_ becomes text. An italic span opens after a non-word,
# non-underscore character, starts and ends with a non-space, and closes before one (so blanks
# such as '____' and words such as 'snake_case' are left alone).
UNDERSCORE_RE = re.compile(r"(?<![\w_])_(?=\S)([^_]+?)(?<=\S)_(?![\w_])")
# Then every remaining single underscore (a marker whose partner sits in another paragraph or
# inside a word) is removed too; runs of two or more underscores (blanks such as '____') stay.
LONE_UNDERSCORE_RE = re.compile(r"(?<!_)_(?!_)")
TAG_MAX_LINES = 60
SMALL_WORDS = {"a", "an", "the", "of", "and", "in", "on", "at", "to", "for", "with", "by", "or", "from",
               "de", "la", "le", "du", "des", "is", "it", "as", "into", "upon", "his", "her", "its", "but", "nor"}
PG_CREDIT_CONTAINS = ("gutenberg", "pgdp", "pglaf", "distributed proofread")
PG_CREDIT_STARTS = ("produced by", "e-text prepared by", "etext prepared by", "this etext was produced",
                    "this ebook was produced", "transcribed from", "transcriber's note", "transcriber\u2019s note",
                    "transcriber's notes", "transcriber\u2019s notes")


def strip_gutenberg(text: str) -> tuple[list[str], dict]:
    """Lines strictly between the '*** START OF' and '*** END OF' markers (rules-v2 cleaning.keep)."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if START_RE.match(line.strip())]
    ends = [i for i, line in enumerate(lines) if END_RE.match(line.strip())]
    if len(starts) != 1 or len(ends) != 1 or not starts[0] < ends[0]:
        raise ValueError(f"markers: {len(starts)} start, {len(ends)} end")
    body = lines[starts[0] + 1:ends[0]]
    return body, {"start_line": starts[0] + 1, "end_line": ends[0] + 1, "body_lines": len(body)}


def is_all_caps(line: str) -> bool:
    letters = [c for c in line if c.isalpha()]
    return bool(letters) and not any(c.islower() for c in letters)


def is_symbols_or_digits(line: str) -> bool:
    """A non-blank line with no letter at all (only symbols, digits and spaces)."""
    s = line.strip()
    return bool(s) and not any(c.isalpha() for c in s)


def heading_kind(line: str, block_start: bool) -> str | None:
    """rules-v2 cleaning.drop_lines (as v1), headings. Decisions (reported):
    - all capitals: at least one letter and no lowercase letter, on any line;
    - CHAPTER/BOOK/PART/LETTER/VOLUME/STAVE in any letter case as the whole first word (punctuation
      may follow it), at most 8 more words, on a line that starts a block (the line before is blank
      or was dropped), so the short last line of a wrapped paragraph is never a heading;
    - an upper-case Roman numeral of valid form as the first word, followed by '.' or ':' (then
      optionally a dash and text), or a numeral of 2+ letters followed by a dash, at most 8 more
      words, on a block-start line. The pronoun 'I' followed by a space or a dash is not a heading,
      and single-letter M., C., D., L. (initials, 'M.' for Monsieur) are not headings."""
    s = line.strip()
    if not s:
        return None
    if is_all_caps(s):
        return "all_caps"
    if not block_start:
        return None
    words = s.split()
    if len(words) > 9:
        return None
    first = words[0]
    m = re.match(r"^[A-Za-z]+", first)
    if m and m.group(0).upper() in HEADING_WORDS and not re.search(r"[A-Za-z]", first[m.end():]):
        return "keyword"
    r = ROMAN_TOKEN.match(first)
    if r and ROMAN_VALID.match(r.group("num")):
        num = r.group("num")
        if r.group("punct") and not (len(num) == 1 and num in "MDCL"):
            return "roman"
        if r.group("dash") is not None and r.group("punct") is None and len(num) >= 2:
            return "roman"
    return None


def is_title_like(s: str) -> bool:
    """A short title-case line without terminal punctuation (a story or chapter title that the
    heading rule does not drop). Used only as a section boundary; the line itself is kept."""
    words = s.split()
    if not words or len(words) > 9 or is_all_caps(s):
        return False
    t = s.rstrip("\"'\u201d\u2019)]_*")
    if t[-1:] in ".!?":
        return False
    lettered = [w for w in words if re.search(r"[A-Za-z]", w)]
    if not lettered:
        return False
    for k, w in enumerate(lettered):
        core = re.sub(r"^[^A-Za-z]+", "", w)
        if core[:1].isupper():
            continue
        if k > 0 and re.sub(r"[^A-Za-z]", "", w).lower() in SMALL_WORDS:
            continue
        return False
    return True


def is_pg_credit(paragraph: str) -> bool:
    low = paragraph.lower()
    return any(c in low for c in PG_CREDIT_CONTAINS) or low.startswith(PG_CREDIT_STARTS)


def clean_book(text: str) -> dict:
    """Body lines -> paragraphs with section ids (rules-v2 cleaning plus the reported decisions).
    Dropped lines: headings (heading_kind), lines starting with '[Illustration' or '[Footnote' (with
    their continuation lines up to the closing bracket, at most TAG_MAX_LINES lines), lines of only
    symbols or digits. Paragraphs = non-blank lines joined at blank lines, whitespace runs -> one
    space. Paragraphs that are Project Gutenberg credits or references are dropped (source.licence).
    A section boundary is every dropped heading line, every dropped symbols/digits line and every
    kept title-like standalone line (which starts the new section)."""
    body, marks = strip_gutenberg(text)
    words_after_strip = sum(len(line.split()) for line in body)
    paragraphs: list[dict] = []
    current: list[str] = []
    section = 0
    counts = {"heading_lines": 0, "heading_all_caps": 0, "heading_keyword": 0, "heading_roman": 0,
              "tag_lines": 0, "tag_continuation_lines": 0, "unclosed_tags": 0, "symbol_lines": 0,
              "pg_credit_paragraphs": 0, "title_like_boundaries": 0, "underscore_spans_removed": 0,
              "lone_underscores_removed": 0, "paragraphs_with_leftover_underscore": 0}
    block_start = True
    n = len(body)
    i = 0

    def flush():
        nonlocal current
        if current:
            para = " ".join(" ".join(current).split())
            para, k = UNDERSCORE_RE.subn(r"\1", para)
            counts["underscore_spans_removed"] += k
            para, k = LONE_UNDERSCORE_RE.subn("", para)
            counts["lone_underscores_removed"] += k
            para = " ".join(para.split())
            if para:
                if is_pg_credit(para):
                    counts["pg_credit_paragraphs"] += 1
                else:
                    counts["paragraphs_with_leftover_underscore"] += "_" in para
                    paragraphs.append({"text": para, "section": section})
            current = []

    while i < n:
        line = body[i].strip()
        if not line:
            flush()
            block_start = True
            i += 1
            continue
        if TAG_RE.match(line):
            counts["tag_lines"] += 1
            j = i
            if "]" not in line:
                j = i + 1
                while j < n and j - i <= TAG_MAX_LINES and "]" not in body[j]:
                    j += 1
                if j < n and j - i <= TAG_MAX_LINES:
                    counts["tag_continuation_lines"] += j - i
                else:
                    counts["unclosed_tags"] += 1
                    j = i
            i = j + 1
            continue
        kind = heading_kind(line, block_start)
        if kind:
            counts["heading_lines"] += 1
            counts["heading_" + kind] += 1
            flush()
            section += 1
            block_start = True
            i += 1
            continue
        if is_symbols_or_digits(line):
            counts["symbol_lines"] += 1
            flush()
            section += 1
            block_start = True
            i += 1
            continue
        next_blank = i + 1 >= n or not body[i + 1].strip()
        if block_start and next_blank and not current and is_title_like(line):
            flush()
            section += 1
            counts["title_like_boundaries"] += 1
        current.append(line)
        block_start = False
        i += 1
    flush()
    words_after_clean = sum(len(p["text"].split()) for p in paragraphs)
    return {"paragraphs": paragraphs, "marks": marks, "counts": counts,
            "words_after_strip": words_after_strip, "words_after_clean": words_after_clean,
            "sections_raw": section + 1}


# ---------------------------------------------------------------- sentences (rules-v2 'sentences')

OPEN_QUOTES = "\"'“‘"
CLOSERS = "\"'”’)]"


def split_sentences(paragraph: str, no_split_after: list[str], initials: bool = True) -> list[str]:
    """Split after '.', '!' or '?' (optionally followed by closing quotes or brackets) when the next
    character after whitespace is an uppercase letter or an opening quote; never after one of the
    listed abbreviations (matched as the whole word that ends at the split point) and never after a
    single capital letter followed by '.' (rules-v2 sentences.initials)."""
    out = []
    start = 0
    i = 0
    n = len(paragraph)
    abbrevs = set(no_split_after)
    while i < n:
        c = paragraph[i]
        if c in ".!?":
            j = i + 1
            while j < n and paragraph[j] in CLOSERS:
                j += 1
            k = j
            while k < n and paragraph[k].isspace():
                k += 1
            if k > j and k < n and (paragraph[k].isupper() or paragraph[k] in OPEN_QUOTES):
                if c == ".":
                    # the word that ends with this period
                    w = paragraph[start:i + 1].split()
                    last = w[-1] if w else ""
                    last = last.lstrip(OPEN_QUOTES + "([")
                    if last in abbrevs or (initials and len(last) == 2 and last[0].isupper() and last[1] == "."):
                        i = j
                        continue
                out.append(paragraph[start:j].strip())
                start = k
                i = k
                continue
            i = j
            continue
        i += 1
    tail = paragraph[start:].strip()
    if tail:
        out.append(tail)
    return [s for s in out if s]


# ---------------------------------------------------------------- lexicon and screen

def word_pattern(forms: list[str]) -> re.Pattern:
    alts = sorted({re.escape(f.lower()).replace(r"\ ", r"\s+") for f in forms}, key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(alts) + r")\b")


def lexicon_hits(text: str, pattern: re.Pattern) -> int:
    return len(pattern.findall(text.lower()))


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)
