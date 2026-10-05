"""Strict parsers for the pinned raw sources (stdlib only).

Every parser first checks the SHA-256 of the exact bytes, then parses without repairing or
skipping anything: a malformed line or record raises. Provenance is kept per row (file and
1-based line or record number, and the source's own identifier). ToxicChat ``model_output``
and moderation fields are never returned: old outputs of other models are not outcomes here,
and the ``toxicity`` label is kept only to choose the risky prompt pool.

The headroom-v2 sources (``parse_pku``, ``parse_csv_table``) follow the same rules: the hash
first, then a strict parse of every record with its position kept. Their texts are returned to
the preparation only; nothing here prints or logs a prompt.
"""

from __future__ import annotations

import csv
import io
import json

from .common import sha256_bytes

__all__ = ["DataError", "HashMismatch", "LeakageError", "check_sha256", "parse_date_lm",
           "parse_toxicchat", "parse_arc", "parse_pku", "parse_csv_table", "PKU_FIELDS"]


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


PKU_FIELDS = ("prompt", "response_0", "response_1", "prompt_source", "response_0_source", "response_1_source",
              "is_response_0_safe", "is_response_1_safe", "response_0_harm_category",
              "response_1_harm_category", "response_0_severity_level", "response_1_severity_level",
              "better_response_id", "safer_response_id", "response_0_sha256", "response_1_sha256")


def parse_pku(data: bytes, expected_sha256: str, source: str) -> tuple[list[dict], dict]:
    """PKU-SafeRLHF train JSONL (pinned revision): exactly ``PKU_FIELDS`` per record. Returns one
    row per (record, response index) with ``line``, ``response_index``, ``prompt``,
    ``response``, ``safe`` (bool), ``severity`` (int 0-3) and ``categories``: the harm-category
    names marked true, in the dataset's own key order, which must be the same for every
    response of the file (returned as ``category_order`` in the receipt)."""
    check_sha256(data, expected_sha256, source)
    lines, blank = _jsonl_lines(data, source)
    rows, order = [], None
    for number, line in lines:
        where = f"{source}:{number}"
        obj = _object(line, where)
        if set(obj) != set(PKU_FIELDS):
            raise DataError(f"{where}: fields differ from the pinned PKU-SafeRLHF schema")
        prompt = obj["prompt"]
        if not isinstance(prompt, str):
            raise DataError(f"{where}: prompt is not a string")
        for i in (0, 1):
            response, safe = obj[f"response_{i}"], obj[f"is_response_{i}_safe"]
            severity, harm = obj[f"response_{i}_severity_level"], obj[f"response_{i}_harm_category"]
            if not isinstance(response, str) or not isinstance(safe, bool):
                raise DataError(f"{where}: response_{i} or is_response_{i}_safe has the wrong type")
            if not isinstance(severity, int) or isinstance(severity, bool) or not 0 <= severity <= 3:
                raise DataError(f"{where}: response_{i}_severity_level must be an integer 0-3")
            if not isinstance(harm, dict) or not all(isinstance(v, bool) for v in harm.values()):
                raise DataError(f"{where}: response_{i}_harm_category must map names to booleans")
            if order is None:
                order = list(harm)
            elif list(harm) != order:
                raise DataError(f"{where}: harm categories differ in name or order from the first record")
            rows.append({"source": source, "line": number, "response_index": i, "prompt": prompt,
                         "response": response, "safe": safe, "severity": severity,
                         "categories": [name for name in order if harm[name]]})
    return rows, {"records": len(lines), "responses": len(rows), "blank_lines": blank,
                  "category_order": order or []}


def parse_csv_table(data: bytes, expected_sha256: str, source: str, header: list[str]) -> tuple[list[dict], dict]:
    """A pinned CSV (RFC-4180 quoting, fields may span lines, optional BOM) whose header must
    equal ``header``: one dict per data record with ``record`` (1-based) and every field."""
    check_sha256(data, expected_sha256, source)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DataError(f"{source}: not UTF-8") from exc
    bom = text.startswith("\ufeff")
    csv.field_size_limit(max(csv.field_size_limit(), len(text)))
    reader = csv.reader(io.StringIO(text[1:] if bom else text, newline=""), strict=True)
    try:
        first = next(reader)
        if first != header:
            raise DataError(f"{source}: header {first} differs from the pinned {header}")
        rows = []
        for number, record in enumerate(reader, start=1):
            if len(record) != len(header):
                raise DataError(f"{source} record {number}: {len(record)} fields, expected {len(header)}")
            rows.append({"record": number, **dict(zip(header, record))})
    except StopIteration as exc:
        raise DataError(f"{source}: empty file") from exc
    except csv.Error as exc:
        raise DataError(f"{source}: malformed CSV: {exc}") from exc
    return rows, {"records": len(rows), "bom": bom}
