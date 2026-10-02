"""Deterministic calibration data from the pinned DATE-LM ToxicChat-Het raw JSONL files.

Stdlib only. Every row keeps provenance: ``uid`` is ``<file>:<1-based line>`` (unique even when
raw ``data_id`` values repeat or collide across files) and the raw ``data_id`` is kept verbatim.
Rules, applied before any sampling and counted in the manifest:

- raw bytes must match the pinned SHA-256; there is no substitute input;
- rows with an empty prompt or response, or containing a chat-template control string, are
  excluded (an empty response has no training target);
- training rows are excluded when their normalized prompt equals ANY reference prompt, or their
  ``data_id`` equals any reference ``data_id`` (all reference rows, including untouched ones);
- within each file the first eligible row per normalized prompt is kept (prompt-level dedupe);
- uids and normalized prompts are asserted disjoint across train, holdout, query, eval and
  untouched reference rows.

``type`` labels fix the stratified composition and the predefined positive-control group only;
nothing downstream uses them as a predictor. Untouched reference rows are listed by ID only:
their text is never written to the prepared rows file, so the runner cannot read them.
"""

from __future__ import annotations

import json
import platform
import random
from collections import Counter
from pathlib import Path
from typing import Iterable

from .common import canonical_json, derive_seed, sha256_bytes, sha256_file, write_atomic

__all__ = ["TYPES", "ROLES", "DataError", "HashMismatch", "LeakageError", "normalize", "parse_raw",
           "check_leakage", "prepare", "write_prepared", "prepare_files", "load_prepared",
           "training_stream", "stream_plan", "fetch_raw"]

TYPES = ("Benign", "Safety-Aligned", "Unsafe")
ROLES = ("train", "holdout", "query", "eval")
ROWS_FILE = "calibration_rows.jsonl"
MANIFEST_FILE = "manifest.json"
MANIFEST_HASH_FILE = "manifest.sha256"
NORMALIZATION = "str.lower() then collapse all whitespace runs to one space (' '.join(s.split()))"
SEED_DERIVATION = "int.from_bytes(sha256('|'.join(parts)).digest()[:8], 'big'); Python random.Random"
HF_RAW_URL = "https://huggingface.co/datasets/{repo_id}/resolve/{revision}/{path}"


class DataError(ValueError):
    """Input or prepared data violate a rule; nothing is silently repaired."""


class HashMismatch(DataError):
    pass


class LeakageError(DataError):
    pass


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _text(value: object, where: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise DataError(f"{where}: expected a string, got {type(value).__name__}")
    return value


def parse_raw(data: bytes, expected_sha256: str, source: str) -> tuple[list[dict], int]:
    """Rows of one raw JSONL file after hash verification; returns (rows, blank_lines)."""
    digest = sha256_bytes(data)
    if digest != expected_sha256:
        raise HashMismatch(f"{source}: sha256 {digest} does not match pinned {expected_sha256}")
    rows, blank = [], 0
    # split on "\n" only: str.splitlines() would also split inside JSON strings on U+2028.
    lines = data.decode("utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # the file's final newline, not a blank line
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            blank += 1
            continue
        where = f"{source}:{line_no}"
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DataError(f"{where}: invalid JSON") from exc
        missing = {"data_id", "prompt", "response", "type"} - set(obj)
        if missing:
            raise DataError(f"{where}: missing fields {sorted(missing)}")
        if obj["type"] not in TYPES:
            raise DataError(f"{where}: unknown type {obj['type']!r}")
        rows.append({"uid": f"{source}:{line_no:05d}", "source": source, "line": line_no,
                     "data_id": str(obj["data_id"]), "type": obj["type"],
                     "prompt": _text(obj["prompt"], where), "response": _text(obj["response"], where)})
    return rows, blank


def _filter(rows: list[dict], forbidden: tuple[str, ...], ref_prompts: set[str] | None,
            ref_ids: set[str] | None) -> tuple[list[dict], dict]:
    kept, reasons, excluded = [], Counter(), 0
    for row in rows:
        why = []
        if not row["prompt"].strip():
            why.append("empty_prompt")
        if not row["response"].strip():
            why.append("empty_response")
        if any(s in row["prompt"] or s in row["response"] for s in forbidden):
            why.append("control_string")
        if ref_prompts is not None and normalize(row["prompt"]) in ref_prompts:
            why.append("ref_prompt_overlap")
        if ref_ids is not None and row["data_id"] in ref_ids:
            why.append("ref_data_id_overlap")
        reasons.update(why)
        if why:
            excluded += 1
        else:
            kept.append(row)
    return kept, {"rows": excluded, "by_reason": dict(sorted(reasons.items()))}


def _dedupe(rows: list[dict]) -> tuple[list[dict], dict]:
    """Keep the first row (file order) per normalized prompt."""
    first: dict[str, dict] = {}
    kept, by_type, same_response = [], Counter(), 0
    for row in rows:
        key = normalize(row["prompt"])
        if key in first:
            by_type[row["type"]] += 1
            same_response += normalize(row["response"]) == normalize(first[key]["response"])
        else:
            first[key] = row
            kept.append(row)
    return kept, {"rows": sum(by_type.values()), "by_type": dict(sorted(by_type.items())),
                  "same_normalized_response": same_response}


def _duplicates(values: Iterable[str]) -> int:
    return sum(n - 1 for n in Counter(values).values() if n > 1)


def check_leakage(roles: dict[str, list[dict]], ref_prompts: set[str] | None = None) -> None:
    """Raise LeakageError if any uid or normalized prompt occurs twice across or within roles,
    or (when given) a train/holdout prompt equals any reference prompt."""
    problems, uid_role, prompt_role = [], {}, {}
    for role, rows in roles.items():
        for row in rows:
            uid, prompt = row["uid"], normalize(row["prompt"])
            if uid in uid_role:
                problems.append(f"uid {uid} in {uid_role[uid]} and {role}")
            if prompt in prompt_role:
                problems.append(f"normalized prompt of {uid} ({role}) repeats one in {prompt_role[prompt]}")
            uid_role.setdefault(uid, role)
            prompt_role.setdefault(prompt, role)
    if ref_prompts is not None:
        for role in ("train", "holdout"):
            problems += [f"{row['uid']} ({role}) has a reference prompt"
                         for row in roles.get(role, []) if normalize(row["prompt"]) in ref_prompts]
    if problems:
        raise LeakageError(f"{len(problems)} leakage problem(s): " + "; ".join(problems[:10]))


def _sample(rng: random.Random, pool: list[str], n: int, what: str) -> list[str]:
    if n > len(pool):
        raise DataError(f"need {n} eligible {what}, only {len(pool)} available")
    return rng.sample(pool, n)


def prepare(config: dict, train_bytes: bytes, ref_bytes: bytes) -> tuple[dict, bytes]:
    """Manifest and serialized rows file for one validated config; pure and deterministic."""
    ds, design = config["dataset"], config["design"]
    seed = design["design_seed"]
    train, train_blank = parse_raw(train_bytes, ds["train_sha256"], "train")
    ref, ref_blank = parse_raw(ref_bytes, ds["ref_sha256"], "ref")
    forbidden = tuple(ds["forbidden_substrings"])

    ref_prompts = {normalize(row["prompt"]) for row in ref} - {""}
    ref_ids = {row["data_id"] for row in ref}
    ref_ok, ref_excluded = _filter(ref, forbidden, None, None)
    ref_ok, ref_dupes = _dedupe(ref_ok)
    train_ok, train_excluded = _filter(train, forbidden, ref_prompts, ref_ids)
    train_ok, train_dupes = _dedupe(train_ok)
    by_uid = {row["uid"]: row for row in train + ref}

    pools = {t: sorted(row["uid"] for row in train_ok if row["type"] == t) for t in TYPES}
    rng = random.Random(derive_seed(seed, "train-sample"))
    counts = design["train_counts"]
    train_uids = [u for t in TYPES for u in _sample(rng, pools[t], counts.get(t, 0), f"{t} rows")]
    chosen = set(train_uids)
    holdout = _sample(random.Random(derive_seed(seed, "benign-holdout")),
                      [u for u in pools["Benign"] if u not in chosen], design["benign_holdout"],
                      "Benign holdout rows")
    removal = design["removal"]
    candidates = sorted(u for u in train_uids if by_uid[u]["type"] == removal["type"])
    group = sorted(_sample(random.Random(derive_seed(seed, "removal-group")), candidates,
                           removal["size"], f"sampled {removal['type']} rows for the removal group"))
    ref_order = sorted(row["uid"] for row in ref_ok)
    random.Random(derive_seed(seed, "ref-split")).shuffle(ref_order)
    n_query, n_eval = design["ref_query"], design["ref_eval"]
    if n_query + n_eval > len(ref_order):
        raise DataError(f"need {n_query + n_eval} eligible reference rows, have {len(ref_order)}")
    split = {"train": sorted(train_uids), "holdout": sorted(holdout),
             "query": sorted(ref_order[:n_query]), "eval": sorted(ref_order[n_query:n_query + n_eval])}
    untouched = sorted(ref_order[n_query + n_eval:])
    check_leakage({**{role: [by_uid[u] for u in uids] for role, uids in split.items()},
                   "ref_untouched": [by_uid[u] for u in untouched]}, ref_prompts)

    group_set = set(group)
    rows = [{**{k: by_uid[u][k] for k in ("uid", "source", "line", "data_id", "type", "prompt",
                                           "response")},
             "role": role, "in_removal_group": u in group_set}
            for role in ROLES for u in split[role]]
    rows_bytes = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
                         for r in rows).encode("utf-8")

    raw_types = Counter(row["type"] for row in train)
    n_train = len(train_uids)
    enrichment = {t: {"raw_count": raw_types[t], "raw_fraction": raw_types[t] / len(train),
                      "calibration_count": counts.get(t, 0),
                      "calibration_fraction": counts.get(t, 0) / n_train,
                      "factor": ((counts.get(t, 0) / n_train) / (raw_types[t] / len(train))
                                 if raw_types[t] else None)}
                  for t in TYPES}
    manifest = {
        "kind": "minimal-safety calibration data manifest",
        "config_dataset": ds,
        "config_design": design,
        "python": platform.python_version(),
        "code_sha256": sha256_file(__file__),
        "normalization": NORMALIZATION,
        "seed_derivation": SEED_DERIVATION,
        "raw": {"train": {"rows": len(train), "blank_lines": train_blank,
                          "by_type": dict(sorted(raw_types.items()))},
                "ref": {"rows": len(ref), "blank_lines": ref_blank,
                        "by_type": dict(sorted(Counter(r["type"] for r in ref).items()))}},
        "source_ids": {
            "train_data_ids_shared_with_ref": len({row["data_id"] for row in train} & ref_ids),
            "train_duplicate_data_ids": _duplicates(row["data_id"] for row in train),
            "ref_duplicate_data_ids": _duplicates(row["data_id"] for row in ref),
            "resolution": "uid = file:line never collides; training rows sharing a data_id with "
                          "any reference row are excluded"},
        "exclusions": {"train": train_excluded, "ref": ref_excluded,
                       "note": "reasons can overlap; 'rows' counts each excluded row once"},
        "prompt_duplicates_dropped": {"train": train_dupes, "ref": ref_dupes},
        "eligible": {"train_by_type": {t: len(pools[t]) for t in TYPES}, "ref": len(ref_order)},
        "enrichment": enrichment,
        "roles": split,
        "removal_group": {"arm": removal["arm"], "type": removal["type"], "uids": group,
                          "label": removal["label"]},
        "ref_untouched": [{"uid": u, "data_id": by_uid[u]["data_id"]} for u in untouched],
        "rows_file": ROWS_FILE,
        "rows_sha256": sha256_bytes(rows_bytes),
    }
    return manifest, rows_bytes


def write_prepared(out_dir: str | Path, manifest: dict, rows_bytes: bytes) -> str:
    """Write rows, manifest and manifest hash; refuse to replace different existing content."""
    out = Path(out_dir)
    manifest_bytes = canonical_json(manifest)
    digest = sha256_bytes(manifest_bytes)
    files = {ROWS_FILE: rows_bytes, MANIFEST_FILE: manifest_bytes,
             MANIFEST_HASH_FILE: (digest + "\n").encode("ascii")}
    for name, payload in files.items():
        path = out / name
        if path.exists() and path.read_bytes() != payload:
            raise DataError(f"{path} exists with different content; prepared data are frozen")
    for name, payload in files.items():
        write_atomic(out / name, payload)
    return digest


def prepare_files(config: dict, train_path: str | Path, ref_path: str | Path,
                  out_dir: str | Path) -> dict:
    manifest, rows_bytes = prepare(config, Path(train_path).read_bytes(), Path(ref_path).read_bytes())
    digest = write_prepared(out_dir, manifest, rows_bytes)
    return {"manifest_sha256": digest, "out_dir": str(out_dir),
            "roles": {role: len(uids) for role, uids in manifest["roles"].items()},
            "removal_group": manifest["removal_group"]["uids"],
            "ref_untouched": len(manifest["ref_untouched"]), "exclusions": manifest["exclusions"],
            "prompt_duplicates_dropped": manifest["prompt_duplicates_dropped"]}


def load_prepared(prepared_dir: str | Path,
                  expected_manifest_sha256: str | None = None) -> tuple[dict, list[dict], str]:
    """Manifest, rows and manifest hash, after checking the frozen hashes and disjointness."""
    folder = Path(prepared_dir)
    manifest_bytes = (folder / MANIFEST_FILE).read_bytes()
    digest = sha256_bytes(manifest_bytes)
    recorded = (folder / MANIFEST_HASH_FILE).read_text(encoding="ascii").strip()
    if digest != recorded:
        raise DataError(f"manifest sha256 {digest} differs from its frozen hash {recorded}")
    if expected_manifest_sha256 is not None and digest != expected_manifest_sha256:
        raise DataError(f"manifest sha256 {digest} differs from the pinned {expected_manifest_sha256}")
    manifest = json.loads(manifest_bytes)
    rows_bytes = (folder / manifest["rows_file"]).read_bytes()
    if sha256_bytes(rows_bytes) != manifest["rows_sha256"]:
        raise DataError("rows file differs from the manifest's rows_sha256")
    rows = [json.loads(line) for line in rows_bytes.decode("utf-8").split("\n") if line.strip()]
    for role in ROLES:
        if sorted(r["uid"] for r in rows if r["role"] == role) != manifest["roles"][role]:
            raise DataError(f"rows file and manifest disagree on role {role}")
    check_leakage({role: [r for r in rows if r["role"] == role] for role in ROLES})
    return manifest, rows, digest


def training_stream(train_uids: list[str], removed: set[str], seed: int, steps: int) -> list[str]:
    """Example uid per optimizer step (batch 1). Each epoch shuffles the FULL training set with
    a seed-and-epoch stream, then drops removed rows: arms of one seed share order, and removal
    deletes rows (kept rows move forward) instead of masking their steps."""
    base = sorted(train_uids)
    if not removed <= set(base):
        raise DataError("removed uids must be training uids")
    if len(removed) >= len(base):
        raise DataError("no retained training rows")
    out, epoch = [], 0
    while len(out) < steps:
        order = list(base)
        random.Random(derive_seed(seed, "data-order", epoch)).shuffle(order)
        out.extend(u for u in order if u not in removed)
        epoch += 1
    return out[:steps]


def stream_plan(manifest: dict, config: dict) -> dict:
    """Per seed and arm: the exact uid sequence, plus a0's exposure to the removal group."""
    train, group = manifest["roles"]["train"], set(manifest["removal_group"]["uids"])
    short, long_ = config["train"]["short_steps"], config["train"]["long_steps"]
    arm = config["design"]["removal"]["arm"]
    plan = {}
    for seed in config["train"]["seeds"]:
        a0 = training_stream(train, set(), seed, long_)
        removed = training_stream(train, group, seed, long_)
        seen = [u in group for u in a0]
        plan[str(seed)] = {
            "a0": {"uids": a0, "removed_seen": {"short": sum(seen[:short]), "long": sum(seen)}},
            arm: {"uids": removed, "removed_seen": {"short": 0, "long": 0}},
            "first_divergence_step": next((i + 1 for i, (x, y) in enumerate(zip(a0, removed))
                                           if x != y), None)}
    return plan


def fetch_raw(config: dict, out_dir: str | Path, confirm: bool) -> dict:
    """Optional public download of the two pinned raw files; never called by plan/run/tests."""
    if not confirm:
        raise DataError("refusing to download without --confirm-public-download")
    import urllib.request

    ds, out, written = config["dataset"], Path(out_dir), {}
    for name in ("train", "ref"):
        url = HF_RAW_URL.format(repo_id=ds["repo_id"], revision=ds["revision"], path=ds[f"{name}_file"])
        with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 - fixed https URL
            payload = response.read()
        if sha256_bytes(payload) != ds[f"{name}_sha256"]:
            raise HashMismatch(f"{url}: downloaded bytes do not match the pinned sha256")
        write_atomic(out / f"{name}.jsonl", payload)
        written[name] = {"url": url, "path": str(out / f"{name}.jsonl"), "sha256": ds[f"{name}_sha256"]}
    return written
