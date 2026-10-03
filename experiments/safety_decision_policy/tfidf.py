"""Frozen TF-IDF query-relevance features (stdlib only; a small sparse implementation).

Definition (``TFIDF_DEFINITION``), fixed before any development outcome; no grid search:

- **Fitting corpus**: every training row of the prepared corpus plus every reference query row
  (the same DATE-LM exemplars the engine's query loss and attribution use). Outcome prompt
  banks are never read.
- **Views**: ``prompt`` (the row's prompt) and ``pair`` (prompt and response as two fields whose
  term counts are added; no bigram spans the prompt/response boundary).
- **Tokens**: ``re.findall(r"\\w\\w+", text.lower())``: lowercase (``str.lower``) runs of at least
  two Unicode word characters as defined by Python's ``re`` for ``str`` patterns (the Unicode
  database version is recorded). **Terms**: every token and every two consecutive tokens of one
  field (a bigram, joined by one space; tokens never contain a space).
- **Vocabulary**: every term of at least one fitting document of the view, in sorted code-point
  order. **idf**(t) = ln((1 + n) / (1 + df(t))) + 1, n = fitting documents of the view.
- **Vector**: raw term count times idf, L2-normalized; a document without terms is the zero
  vector and its cosine with anything is 0.
- **Row relevance**: the maximum cosine between a removed row and any query, in the same view.
- **Group features**: mean, sum and max of the member rows' relevance, per view (six features:
  ``tfidf_{prompt,pair}_{mean,sum,max}``).

Fingerprints: the definition hash; per view the fitting documents, vocabulary size and SHA-256
over the sorted ``term<TAB>df<LF>`` lines (vocabulary and idf); the prepared input-file hashes
(engine receipt only). Memory: document frequencies are counted one view at a time over term
sets; vectors exist only for group members and queries; never a dense corpus-by-vocabulary
array. The relevance table holds per-group numbers only (no row ids, text or membership).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from experiments.safety_selection.prepare import GROUPS, QUERY_ROWS, TRAIN_ROWS, read_manifest, read_verified

from .common import PolicyError, VerificationError, canonical_json, finite, read_canonical, sha256_bytes

__all__ = ["TFIDF_DEFINITION", "DEFINITION_SHA256", "VIEWS", "FEATURES", "TABLE_KIND", "tokens",
           "terms", "document_terms", "fit_document_frequency", "idf_weights", "vector", "cosine",
           "relevance", "build_relevance", "read_relevance"]

TABLE_KIND = "safety-decision-policy relevance table"
RECEIPT_KIND = "relevance receipt (engine/auditor side; never a predictor input)"
VIEWS = ("prompt", "pair")
STATS = ("mean", "sum", "max")
FEATURES = tuple(f"tfidf_{view}_{stat}" for view in VIEWS for stat in STATS)
TOKEN_PATTERN = r"\w\w+"
_TOKEN = re.compile(TOKEN_PATTERN)
TFIDF_DEFINITION = {
    "corpus": "every prepared training row plus every reference query row; no outcome prompt bank",
    "views": {"prompt": "prompt", "pair": "prompt and response as two fields; counts added; no "
                                          "bigram across the boundary"},
    "tokens": f"re.findall({TOKEN_PATTERN!r}, str.lower(text)) with Python re Unicode word characters",
    "terms": "unigrams and within-field bigrams joined by one space",
    "vocabulary": "every term with df >= 1 in the view's fitting corpus, sorted by code point",
    "idf": "ln((1 + n) / (1 + df)) + 1, n = fitting documents of the view",
    "tf": "raw count",
    "normalization": "L2; the zero vector has cosine 0 with everything",
    "row_relevance": "max cosine to any query row, same view",
    "group_features": "mean, sum and max over the group's rows, per view"}
DEFINITION_SHA256 = sha256_bytes(canonical_json(TFIDF_DEFINITION))


def tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def terms(text: str) -> Counter:
    """Unigram and bigram counts of one field."""
    toks = tokens(text)
    counts = Counter(toks)
    counts.update(f"{a} {b}" for a, b in zip(toks, toks[1:]))
    return counts


def document_terms(fields: Sequence[str]) -> Counter:
    """Term counts of a document made of separate fields (no cross-field bigram)."""
    total: Counter = Counter()
    for field in fields:
        total.update(terms(field))
    return total


def fit_document_frequency(documents: Iterable[Sequence[str]]) -> tuple[int, Counter]:
    """(number of documents, document frequency per term)."""
    n, df = 0, Counter()
    for fields in documents:
        n += 1
        df.update(set(document_terms(fields)))
    return n, df


def idf_weights(n: int, df: Mapping[str, int]) -> dict[str, float]:
    return {term: math.log((1 + n) / (1 + count)) + 1.0 for term, count in df.items()}


def vector(counts: Mapping[str, int], idf: Mapping[str, float]) -> dict[str, float]:
    """L2-normalized tf-idf weights; {} for a document without terms. Every term must be in the
    fitted vocabulary (all vectorized documents belong to the fitting corpus)."""
    missing = [t for t in counts if t not in idf]
    if missing:
        raise VerificationError(f"terms outside the fitted vocabulary: {missing[:3]}")
    raw = {t: c * idf[t] for t, c in counts.items()}
    norm = math.sqrt(math.fsum(w * w for w in raw.values()))
    return {} if norm == 0.0 else {t: w / norm for t, w in raw.items()}


def cosine(u: Mapping[str, float], v: Mapping[str, float]) -> float:
    if not u or not v:
        return 0.0
    small, large = (u, v) if len(u) <= len(v) else (v, u)
    return math.fsum(w * large[t] for t, w in small.items() if t in large)


def _fields(view: str, prompt: str, response: str) -> tuple[str, ...]:
    return (prompt,) if view == "prompt" else (prompt, response)


def _fingerprint(n: int, df: Counter) -> dict:
    digest = hashlib.sha256()
    for term in sorted(df):
        digest.update(f"{term}\t{df[term]}\n".encode("utf-8"))
    return {"documents": n, "vocabulary": len(df), "df_sha256": digest.hexdigest()}


def relevance(documents: Mapping[str, tuple[str, str]], queries: Mapping[str, tuple[str, str]],
              groups: Mapping[str, Mapping[str, Sequence[str]]]) -> tuple[dict, dict]:
    """(per partition, per group: the six features; fingerprints per view). ``documents`` maps
    every training row id to (prompt, response); ``queries`` every query id likewise;
    ``groups`` maps partition -> group id -> member row ids."""
    if not documents or not queries:
        raise PolicyError("relevance needs training rows and query rows")
    members = {rid for part in groups.values() for rows in part.values() for rid in rows}
    if not members <= set(documents):
        raise PolicyError("group members must be training rows")
    out: dict[str, dict[str, dict[str, float]]] = {part: {gid: {} for gid in sorted(groups[part])}
                                                   for part in sorted(groups)}
    prints = {}
    for view in VIEWS:
        corpus = [_fields(view, *documents[rid]) for rid in sorted(documents)]
        corpus += [_fields(view, *queries[qid]) for qid in sorted(queries)]
        n, df = fit_document_frequency(corpus)
        prints[view] = _fingerprint(n, df)
        idf = idf_weights(n, df)
        query_vectors = [vector(document_terms(_fields(view, *queries[qid])), idf) for qid in sorted(queries)]
        best: dict[str, float] = {}
        for rid in sorted(members):
            row = vector(document_terms(_fields(view, *documents[rid])), idf)
            best[rid] = max(cosine(row, q) for q in query_vectors)
        for part in sorted(groups):
            for gid in sorted(groups[part]):
                values = [best[rid] for rid in groups[part][gid]]
                if not values:
                    raise PolicyError(f"group {gid} has no member rows")
                out[part][gid].update({f"tfidf_{view}_mean": math.fsum(values) / len(values),
                                       f"tfidf_{view}_sum": math.fsum(values),
                                       f"tfidf_{view}_max": max(values)})
        del df, idf
    return out, prints


def _jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode("utf-8").split("\n") if line]


def build_relevance(prepared_dir: str | Path, manifest_sha256: str | None = None) -> tuple[bytes, dict]:
    """(table bytes, engine-side receipt) from the hash-verified prepared training rows, query rows
    and groups only (no bank, hidden or auditor file is opened)."""
    manifest, digest = read_manifest(prepared_dir, manifest_sha256)
    train = _jsonl(read_verified(prepared_dir, manifest, TRAIN_ROWS))
    queries = _jsonl(read_verified(prepared_dir, manifest, QUERY_ROWS))
    raw_groups = json.loads(read_verified(prepared_dir, manifest, GROUPS))["partitions"]
    groups = {part: {g["group_id"]: list(g["members"]) for g in raw_groups[part]["groups"]}
              for part in raw_groups}
    table_parts, prints = relevance({r["row_id"]: (r["prompt"], r["response"]) for r in train},
                                    {q["query_id"]: (q["prompt"], q["response"]) for q in queries}, groups)
    fingerprint_sha256 = sha256_bytes(canonical_json(prints))
    table = {"kind": TABLE_KIND, "definition_sha256": DEFINITION_SHA256,
             "fingerprint_sha256": fingerprint_sha256, "partitions": table_parts}
    data = canonical_json(table)
    receipt = {"kind": RECEIPT_KIND, "table_sha256": sha256_bytes(data), "manifest_sha256": digest,
               "input_files": {name: manifest["files"][name] for name in (TRAIN_ROWS, QUERY_ROWS, GROUPS)},
               "definition": TFIDF_DEFINITION, "definition_sha256": DEFINITION_SHA256,
               "fingerprints": prints, "fingerprint_sha256": fingerprint_sha256,
               "python": sys.version, "unicodedata": unicodedata.unidata_version}
    return data, receipt


def read_relevance(path: str | Path, expected_sha256: str | None, split: str) -> tuple[dict, dict]:
    """Predictor-side reader: (per group of ``split``: the six features, {definition and
    fingerprint hashes}). Exact schema, finite values, canonical bytes, expected hash."""
    table = read_canonical(path, expected_sha256)
    if not (isinstance(table, dict) and set(table) == {"kind", "definition_sha256", "fingerprint_sha256",
                                                       "partitions"} and table["kind"] == TABLE_KIND):
        raise VerificationError(f"{path} is not a relevance table")
    if table["definition_sha256"] != DEFINITION_SHA256:
        raise VerificationError(f"{path} was built with another TF-IDF definition")
    part = table["partitions"].get(split)
    if not isinstance(part, dict) or not part:
        raise VerificationError(f"{path} holds no {split} groups")
    out = {}
    for gid, values in part.items():
        if not (isinstance(values, dict) and set(values) == set(FEATURES)):
            raise VerificationError(f"{path}: group {gid} features differ from {FEATURES}")
        try:
            out[gid] = {name: finite(values[name], f"{path}: {gid}.{name}") for name in FEATURES}
        except PolicyError as exc:
            raise VerificationError(str(exc)) from exc
    return out, {"definition_sha256": table["definition_sha256"],
                 "fingerprint_sha256": table["fingerprint_sha256"]}
