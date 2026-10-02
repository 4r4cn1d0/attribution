"""Strict parsers for the pinned raw sources (stdlib only).

Every parser first checks the SHA-256 of the exact bytes, then parses without repairing or
skipping anything: a malformed line or record raises. Provenance is kept per row (file and
1-based line or record number, and the source's own identifier). ToxicChat ``model_output``
and moderation fields are never returned: old outputs of other models are not outcomes here,
and the ``toxicity`` label is kept only to choose the risky prompt pool.
"""

from __future__ import annotations

import csv
import io
import json

from .common import sha256_bytes

__all__ = ["DataError", "HashMismatch", "LeakageError", "check_sha256", "parse_date_lm",
           "parse_toxicchat", "parse_arc"]


class DataError(ValueError):
    """Input or prepared data violate a rule; nothing is silently repaired."""


class HashMismatch(DataError):
    pass


class LeakageError(DataError):
    pass


def check_sha256(data: bytes, expected: str, source: str) -> None:
    digest = sha256_bytes(data)
    if digest != expected:
        raise HashMismatch(f"{source}: sha256 {digest} does not match pinned {expected}")


def _jsonl_lines(data: bytes, source: str) -> tuple[list[tuple[int, str]], int]:
    """(line number, text) of non-blank lines and the blank-line count. Splits on "\\n" only:
    str.splitlines() would also split inside JSON strings on U+2028."""
    try:
        lines = data.decode("utf-8").split("\n")
    except UnicodeDecodeError as exc:
        raise DataError(f"{source}: not UTF-8") from exc
    if lines and lines[-1] == "":
        lines.pop()  # the file's final newline, not a blank line
    out, blank = [], 0
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            blank += 1
        else:
            out.append((number, line))
    return out, blank


def _object(line: str, where: str) -> dict:
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        raise DataError(f"{where}: invalid JSON") from exc
    if not isinstance(obj, dict):
        raise DataError(f"{where}: not a JSON object")
    return obj


def _optional_text(value: object, where: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise DataError(f"{where}: expected a string, got {type(value).__name__}")
    return value


def parse_date_lm(data: bytes, expected_sha256: str, source: str,
                  types: set[str]) -> tuple[list[dict], int]:
    """DATE-LM ToxicChat-Het rows: ``uid`` is ``<source>:<5-digit line>`` (unique even when raw
    ``data_id`` values repeat); missing prompts/responses become "" (excluded later)."""
    check_sha256(data, expected_sha256, source)
    lines, blank = _jsonl_lines(data, source)
    rows = []
    for number, line in lines:
        where = f"{source}:{number}"
        obj = _object(line, where)
        missing = {"data_id", "prompt", "response", "type"} - set(obj)
        if missing:
            raise DataError(f"{where}: missing fields {sorted(missing)}")
        if obj["type"] not in types:
            raise DataError(f"{where}: unknown type {obj['type']!r}")
        rows.append({"uid": f"{source}:{number:05d}", "source": source, "line": number,
                     "data_id": str(obj["data_id"]), "type": obj["type"],
                     "prompt": _optional_text(obj["prompt"], where),
                     "response": _optional_text(obj["response"], where)})
    return rows, blank


def parse_toxicchat(data: bytes, expected_sha256: str, header: list[str]) -> tuple[list[dict], dict]:
    """ToxicChat CSV records (RFC-4180 quoting, fields may span lines). Returns rows with
    ``record`` (1-based data record), ``conv_id``, ``prompt`` (``user_input``, exact),
    ``toxicity`` and ``jailbreaking`` (0/1), plus a receipt."""
    check_sha256(data, expected_sha256, "toxicchat")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DataError("toxicchat: not UTF-8") from exc
    bom = text.startswith("﻿")
    # A field may legitimately exceed csv's default 128 KiB limit; the file hash is pinned.
    csv.field_size_limit(max(csv.field_size_limit(), len(text)))
    reader = csv.reader(io.StringIO(text[1:] if bom else text, newline=""), strict=True)
    try:
        first = next(reader)
    except StopIteration as exc:
        raise DataError("toxicchat: empty file") from exc
    except csv.Error as exc:
        raise DataError(f"toxicchat: malformed header: {exc}") from exc
    if first != header:
        raise DataError(f"toxicchat: header {first} differs from the pinned {header}")
    index = {name: i for i, name in enumerate(header)}
    rows = []
    try:
        for number, record in enumerate(reader, start=1):
            where = f"toxicchat record {number}"
            if len(record) != len(header):
                raise DataError(f"{where}: {len(record)} fields, expected {len(header)}")
            labels = {}
            for name in ("toxicity", "jailbreaking"):
                if name in index:
                    value = record[index[name]]
                    if value not in ("0", "1"):
                        raise DataError(f"{where}: {name} {value!r} is not 0 or 1")
                    labels[name] = int(value)
            conv_id = record[index["conv_id"]]
            if not conv_id.strip():
                raise DataError(f"{where}: empty conv_id")
            rows.append({"source": "toxicchat", "record": number, "conv_id": conv_id,
                         "prompt": record[index["user_input"]], "toxicity": labels["toxicity"],
                         "jailbreaking": labels.get("jailbreaking")})
    except csv.Error as exc:
        raise DataError(f"toxicchat: malformed CSV: {exc}") from exc
    return rows, {"records": len(rows), "bom": bom}


def parse_arc(data: bytes, expected_sha256: str, split: str) -> tuple[list[dict], int]:
    """ARC-Easy JSONL converted from the pinned parquet: exactly ``id``, ``question``,
    ``choices`` ({``text``, ``label``} lists of equal length >= 2, distinct labels) and
    ``answerKey`` (one of the labels)."""
    source = f"arc-{split}"
    check_sha256(data, expected_sha256, source)
    lines, blank = _jsonl_lines(data, source)
    rows = []
    for number, line in lines:
        where = f"{source}:{number}"
        obj = _object(line, where)
        if set(obj) != {"id", "question", "choices", "answerKey"}:
            raise DataError(f"{where}: fields {sorted(obj)} differ from id/question/choices/answerKey")
        choices = obj["choices"]
        if not isinstance(choices, dict) or set(choices) != {"text", "label"}:
            raise DataError(f"{where}: choices must have exactly text and label")
        texts, labels = choices["text"], choices["label"]
        if not (isinstance(texts, list) and isinstance(labels, list) and len(texts) == len(labels) >= 2):
            raise DataError(f"{where}: choices need equal-length text/label lists of at least 2")
        for value in [obj["id"], obj["question"], obj["answerKey"], *texts, *labels]:
            if not isinstance(value, str) or not value.strip():
                raise DataError(f"{where}: empty or non-string field")
        if len(set(labels)) != len(labels) or obj["answerKey"] not in labels:
            raise DataError(f"{where}: labels must be distinct and contain answerKey")
        rows.append({"source": source, "line": number, "arc_id": obj["id"],
                     "question": obj["question"], "labels": list(labels), "texts": list(texts),
                     "answer": obj["answerKey"]})
    return rows, blank
