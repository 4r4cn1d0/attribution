"""Gate C anchor prompt list: one pinned draw on the Mac, sealed by SHA-256 (no pod, no download).

Spec: research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md, section 1, "Anchors",
"Prompts" (revision 3); the list schema is the builder brief's A9
(.ai/briefs/gate-b-engine-kit-reading-20261008.md). The lead's decision (GI IV, 8 Oct): the FULL list
with text goes to tmp/gate-b-anchors/anchor_prompts.json (git ignores tmp/; the pod bundle carries it by
SHA-256); what is committed is this script, a sealed record without text and a manifest.

Standard library plus the engine's own code, imported from the checkout that holds this script
(experiments/safety_selection): ``parse_pku`` (the reader for format "pku-saferlhf-jsonl"),
``load_prepared`` (the prepared-set loader, hidden bank allowed as a reference job does),
``_NearDuplicates``, ``_round_robin``, ``_first_per_key`` and ``_forbidden_found`` from ``prepare``
(the injection rule's own pieces), ``arc_prompt_forms`` and ``normalize`` (the text rules),
``derive_seed``, ``canonical_json``, ``sha256_bytes``, ``write_atomic`` and ``code_identity``.

The rule, as implemented (the engine's INJECTION_RULE with one seed and no token audit):

  candidates   every response of injection.sources (files in the configured order, records in line
               order, response 0 then 1) marked unsafe with severity >= max(2, injection.min_severity);
  excluded     an empty prompt or response; a forbidden substring in either (the union of the config's
               and the prepared set's eligibility.forbidden_substrings); a normalized prompt equal to
               any training-row or query prompt of the prepared set or to any evaluation prompt form;
               no harm category marked true; then the first candidate per normalized prompt in candidate
               order (its category is the first harm category marked true in the dataset's key order);
  balance      one random.Random(derive_seed(20261008, "gate-c-anchors-v1")); for each category in the
               dataset's key order, rng.shuffle(that category's eligible candidates, in candidate order);
               then prepare._round_robin: one candidate per category per round, categories in key order,
               exhausted (short) categories skipped;
  walk         in that order, a candidate is dropped and counted when its prompt's largest character
               5-gram Jaccard (prepare.NEAR_DUPLICATE; prepare._NearDuplicates) with any evaluation prompt
               form of the prepared set (banks/ and hidden/, all splits; every form of every ARC item) is
               at least injection.near_duplicate.max_jaccard, or with any already kept anchor prompt;
               the first 128 kept are the list, harmful = the first 64, reserve = the rest; fewer than
               128 refuses with counts and writes nothing.

Reads: the inj05 data config (hash pinned); the three PKU files (each hash checked against the
config's pin before the engine's reader checks it again); the prepared set through load_prepared
(manifest hash pinned, every file hash verified by the loader). Nothing else is opened.

Writes (only when every check passes; the output folder must be absent or empty and the FULL path
absent): the FULL list (A9 schema plus a top-level "provenance" object), out/anchor_prompts.sealed.json
(ids, line numbers, hashes, counts, labels and scores; no text) and out/MANIFEST.json. Prints counts,
ids and hashes only; no message anywhere carries a prompt, a response or any bank text.

Determinism. The FULL list and the sealed record are a pure function of the pinned inputs, this
script's bytes, the engine functions used (each pinned by the SHA-256 of its source) and the recorded
time (``--built-at``; default now), so a re-run with the same ``--built-at`` reproduces both byte for
byte. Repo state that changes while others work (git HEAD, the engine's whole-code identity, the
spec's and brief's hashes at build time, the interpreter) is recorded in MANIFEST.json only, as the
sealed Gate B files do.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import inspect
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]                      # <repo>/.ai/inputs/gate-b-anchors-20261008/make_anchor_prompts.py
if not (REPO / "experiments" / "safety_selection" / "prepare.py").is_file():
    raise SystemExit(f"STOP: no engine at {REPO / 'experiments' / 'safety_selection'} (nothing written)")
sys.path.insert(0, str(REPO))

import experiments.minimal_safety.common as _ms_common                                   # noqa: E402
from experiments.safety_selection.common import (canonical_json, code_identity, derive_seed,  # noqa: E402
                                                 sha256_bytes, write_atomic)
from experiments.safety_selection.config import BANKS                                     # noqa: E402
from experiments.safety_selection.prepare import (BANK_FILES, GROUPS, INJECTION_RULE,     # noqa: E402
                                                  NEAR_DUPLICATE, NORMALIZATION, QUERY_ROWS,
                                                  TRAIN_ROWS, _first_per_key, _forbidden_found,
                                                  _NearDuplicates, _round_robin, _shingles, load_prepared)
from experiments.safety_selection.sources import DataError, parse_pku                      # noqa: E402
from experiments.safety_selection.textproc import arc_prompt_forms, normalize               # noqa: E402

# ----- pinned inputs and constants ----------------------------------------------------------------

CONFIG_REL = "experiments/safety_selection/configs/study-v3-data-inj05.json"
CONFIG_SHA256 = "11e9221412d599bf277f934182c10ad6f27c78508a5fe99267e95e023497d760"
SOURCES_REL = "tmp/v2-sources"             # the config's extra_sources[*].local paths are relative to it
PREPARED_REL = "tmp/kt-prepared/prepared-kt-dolly-olmo2"
PREPARED_MANIFEST_SHA256 = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
FULL_REL = "tmp/gate-b-anchors/anchor_prompts.json"
SCRIPT_REL = ".ai/inputs/gate-b-anchors-20261008/make_anchor_prompts.py"
OUT_LABEL = ".ai/inputs/gate-b-anchors-20261008/out"
SPEC_REL = "research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md"
SPEC_SECTION = "section 1, Anchors, Prompts (revision 3)"
BRIEF_REL = ".ai/briefs/gate-b-engine-kit-reading-20261008.md"
BRIEF_ITEM = "A9, the list schema"

DESIGN_SEED = 20261008
STREAM = "gate-c-anchors-v1"
SEED_RULE = f"derive_seed({DESIGN_SEED}, {STREAM!r})"
LIST_SIZE = 128
HARMFUL_SIZE = 64
SEVERITY_FLOOR = 2
PKU_FORMAT = "pku-saferlhf-jsonl"
REPORT_THRESHOLDS = (0.3, 0.5, 0.7)

LIST_KIND = "gate-c anchor prompt list"
LIST_VERSION = 1
LIST_KEYS = frozenset({"kind", "version", "source", "prompts", "provenance"})
SOURCE_KEYS = frozenset({"repo_id", "revision", "file_sha256"})
PROMPT_KEYS = frozenset({"index", "prompt", "unsafe_response"})
SEALED_KIND = "gate-c anchor prompt list, sealed record"
SEALED_NAME = "anchor_prompts.sealed.json"
MANIFEST_KIND = "gate-c anchor prompt list manifest"
MANIFEST_NAME = "MANIFEST.json"

ELIGIBILITY_RULE = (
    "candidates: every response of injection.sources (files in the configured order, records in line order, "
    "response 0 then 1) marked unsafe (is_response_i_safe false) with severity >= max(2, injection.min_severity); "
    "excluded: an empty prompt or response, a forbidden substring in either (the union of the config's and the "
    "prepared set's eligibility.forbidden_substrings), a normalized prompt equal to any training-row or query "
    "prompt of the prepared set or to any evaluation prompt form (banks/ and hidden/, all splits), or no harm "
    "category marked true; then the first candidate per normalized prompt in candidate order; its category is the "
    "first harm category marked true in the dataset's own key order (prepare._first_per_key)")
BALANCE_RULE = (
    f"one rng = random.Random({SEED_RULE}); for each category in the dataset's key order, rng.shuffle(the "
    "category's eligible candidates, in candidate order); then prepare._round_robin(by_category, key order): one "
    "candidate per category per round, categories in the dataset's key order, exhausted categories skipped (a "
    "short category simply contributes nothing after it runs out; no reweighting). The engine's injection "
    "shuffles each category with its own stream derive_seed(design_seed, 'injection-order', category); here the "
    "pre-registered single seed is consumed in key order instead, then the same round robin")
WALK_RULE = (
    "walk the balanced order: a candidate is dropped and counted as near_duplicate_of_evaluation_prompt when "
    "prepare._NearDuplicates(evaluation forms).nearest(prompt) >= max_jaccard (NEAR_DUPLICATE; the evaluation "
    "forms are every bank item's prompt and every form of every ARC item, all splits, built as prepare.py builds "
    "'evaluation' for the injection walk), else as near_duplicate_of_kept_anchor when the same score against "
    "the already kept anchor prompts is >= max_jaccard; the first 128 kept, in walk order, are the list; harmful "
    "= prompts[0:64] with their PKU unsafe responses; reserve = prompts[64:128]; fewer than 128 refuses with "
    "counts. No token audit here (no tokenizer on the Mac): the pod script encodes each anchor and refuses "
    "over-long or control-token text (brief A9); prompt and response character lengths are recorded")


ENGINE_FUNCTIONS = {                       # the engine code the list depends on, each pinned by its source hash
    "experiments.minimal_safety.common.derive_seed": derive_seed,
    "experiments.safety_selection.sources.parse_pku": parse_pku,
    "experiments.safety_selection.prepare._NearDuplicates": _NearDuplicates,
    "experiments.safety_selection.prepare._shingles": _shingles,
    "experiments.safety_selection.prepare._round_robin": _round_robin,
    "experiments.safety_selection.prepare._first_per_key": _first_per_key,
    "experiments.safety_selection.prepare._forbidden_found": _forbidden_found,
    "experiments.safety_selection.prepare.load_prepared": load_prepared,
    "experiments.safety_selection.textproc.arc_prompt_forms": arc_prompt_forms,
    "experiments.minimal_safety.data.normalize": normalize,
}


class Stop(SystemExit):
    """A check failed: nothing is written. The message carries ids, counts and hashes only."""


def stop(message: str) -> None:
    raise Stop(f"STOP: {message} (nothing written)")


def sha256_path(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def git_head(repo: Path) -> str | None:
    """HEAD's commit by reading .git files only (no git command is run)."""
    try:
        head = (repo / ".git" / "HEAD").read_text(encoding="ascii").strip()
        if not head.startswith("ref: "):
            return head
        ref = head[5:]
        direct = repo / ".git" / ref
        if direct.is_file():
            return direct.read_text(encoding="ascii").strip()
        for line in (repo / ".git" / "packed-refs").read_text(encoding="ascii").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1] == ref:
                return parts[0]
    except OSError:
        pass
    return None


# ----- inputs ---------------------------------------------------------------------------------------


def load_config(path: Path, expected_sha256: str | None) -> tuple[dict, str]:
    data = Path(path).read_bytes()
    digest = sha256_bytes(data)
    if expected_sha256 is not None and digest != expected_sha256:
        stop(f"data config hashes to {digest}, expected {expected_sha256}")
    config = json.loads(data)
    try:
        inj = config["injection"]
        sources, limit = list(inj["sources"]), inj["near_duplicate"]["max_jaccard"]
        severity = inj["min_severity"]
        forbidden = config["eligibility"]["forbidden_substrings"]
        for name in sources:
            spec = config["extra_sources"][name]
            for key in ("repo_id", "revision", "file", "sha256", "local", "format"):
                spec[key]
    except (KeyError, TypeError) as exc:
        stop(f"data config lacks the injection or extra_sources fields ({type(exc).__name__})")
    if not sources or not isinstance(severity, int) or isinstance(severity, bool) or not 0 < limit <= 1:
        stop("data config: injection.sources, min_severity or near_duplicate.max_jaccard is malformed")
    if not isinstance(forbidden, list) or not all(isinstance(s, str) for s in forbidden):
        stop("data config: eligibility.forbidden_substrings must be a list of strings")
    return config, digest


def read_sources(config: dict, sources_root: Path) -> dict:
    """Every PKU row of the injection sources through the engine's reader, after the pinned hash check."""
    rows, receipts, hashes, order = [], {}, {}, None
    for name in config["injection"]["sources"]:
        spec = config["extra_sources"][name]
        if spec["format"] != PKU_FORMAT:
            stop(f"{name}: format is not {PKU_FORMAT}")
        path = Path(sources_root) / spec["local"]
        if not path.is_file():
            stop(f"{name}: no file at {path}")
        data = path.read_bytes()
        hashes[name] = sha256_bytes(data)
        if hashes[name] != spec["sha256"]:
            stop(f"{name}: sha256 {hashes[name]} differs from the pinned {spec['sha256']}")
        try:
            parsed, receipts[name] = parse_pku(data, spec["sha256"], name)
        except DataError as exc:
            stop(f"{name}: the engine's reader refused ({type(exc).__name__})")
        del data
        if order is None:
            order = list(receipts[name]["category_order"])
        elif list(receipts[name]["category_order"]) != order:
            stop(f"{name}: harm categories differ in name or order from the first source")
        rows += parsed
    if not order:
        stop("the sources name no harm category")
    return {"rows": rows, "receipts": receipts, "hashes": hashes, "category_order": order,
            "source_order": list(config["injection"]["sources"])}


def load_evaluation(prepared_root: Path, expected_manifest_sha256: str | None) -> dict:
    """The prepared set through the engine's loader: every evaluation prompt form (as prepare.py builds
    ``evaluation`` for the injection walk), the normalized training and query prompts, and the hashes."""
    try:
        prepared = load_prepared(prepared_root, expected_manifest_sha256, banks=BANKS, allow_hidden=True)
    except DataError as exc:
        stop(f"the prepared set at {prepared_root} did not load ({type(exc).__name__})")
    evaluation, items = [], Counter()
    for bank in BANKS:
        for item in prepared.banks[bank]:
            items[f"{bank}/{item['kind']}"] += 1
            if item["kind"].startswith("arc_"):
                evaluation += [(item["prompt_id"], form) for form in dict.fromkeys(
                    arc_prompt_forms(item["question"], item["labels"], item["texts"]))]
            else:
                evaluation.append((item["prompt_id"], item["prompt"]))
    existing = ({normalize(r["prompt"]) for r in prepared.train_rows.values()}
                | {normalize(r["prompt"]) for r in prepared.query_rows}
                | {normalize(text) for _, text in evaluation}) - {""}
    forbidden = prepared.data_config.get("eligibility", {}).get("forbidden_substrings")
    if not isinstance(forbidden, list) or not all(isinstance(s, str) for s in forbidden):
        stop("the prepared set's data config has no eligibility.forbidden_substrings list")
    read = [TRAIN_ROWS, QUERY_ROWS, GROUPS] + [BANK_FILES[bank] for bank in BANKS]
    return {"manifest_sha256": prepared.manifest_sha256, "evaluation": evaluation, "existing": existing,
            "forbidden": forbidden, "items": dict(sorted(items.items())), "forms": len(evaluation),
            "training_rows": len(prepared.train_rows), "query_rows": len(prepared.query_rows),
            "files": {name: prepared.manifest["files"][name] for name in read},
            "data_config_name": prepared.data_config.get("name"),
            "normalization": prepared.manifest.get("normalization")}


# ----- the rule -------------------------------------------------------------------------------------


def candidates_of(rows: list[dict], min_severity: int) -> list[dict]:
    """Unsafe responses of severity >= min_severity, in candidate order (file, line, response index)."""
    out = [r for r in rows if not r["safe"] and r["severity"] >= min_severity]
    return out


def eligible_of(candidates: list[dict], forbidden: list[str], existing: set[str]) -> tuple[list[dict], dict, dict]:
    """The injection rule's exclusions (same labels as prepare._injection) and first-per-prompt dedupe."""
    reasons, kept = Counter(), []
    for row in candidates:
        why = []
        if not row["prompt"].strip():
            why.append("empty_prompt")
        if not row["response"].strip():
            why.append("empty_response")
        if _forbidden_found([row["prompt"], row["response"]], forbidden):
            why.append("control_string")
        if normalize(row["prompt"]) in existing:
            why.append("overlap_with_an_existing_or_evaluation_prompt")
        if not row["categories"]:
            why.append("no_harm_category")
        reasons.update(why)
        if not why:
            kept.append(row)
    kept, duplicates = _first_per_key(kept, lambda r: normalize(r["prompt"]), lambda r: r["categories"][0])
    return kept, dict(sorted(reasons.items())), duplicates


def balanced_order(eligible: list[dict], category_order: list[str], seed: int) -> tuple[list[dict], dict]:
    """BALANCE_RULE: one seeded shuffle per category in key order, then the engine's round robin."""
    unknown = {r["categories"][0] for r in eligible} - set(category_order)
    if unknown:
        stop(f"{len(unknown)} candidate categories are outside the dataset's key order")
    queues = {c: [r for r in eligible if r["categories"][0] == c] for c in category_order}
    rng = random.Random(seed)
    for category in category_order:
        rng.shuffle(queues[category])
    return _round_robin(queues, category_order), {c: len(queues[c]) for c in category_order}


def walk(order: list[dict], evaluation: list[tuple[str, str]], limit: float, want: int) -> dict:
    """WALK_RULE. Returns the kept rows with their scores and the counts."""
    near = _NearDuplicates(evaluation)
    anchors: _NearDuplicates | None = None
    kept, dropped, walked, at_or_above = [], Counter(), 0, Counter({str(t): 0 for t in REPORT_THRESHOLDS})
    for row in order:
        if len(kept) == want:
            break
        walked += 1
        score_eval, _ = near.nearest(row["prompt"])
        for t in REPORT_THRESHOLDS:
            at_or_above[str(t)] += score_eval >= t
        if score_eval >= limit:
            dropped["near_duplicate_of_evaluation_prompt"] += 1
            continue
        score_anchor = anchors.nearest(row["prompt"])[0] if anchors is not None else 0.0
        if score_anchor >= limit:
            dropped["near_duplicate_of_kept_anchor"] += 1
            continue
        kept.append({"row": row, "jaccard_evaluation": score_eval, "jaccard_anchor": score_anchor})
        anchors = _NearDuplicates([(f"{i:03d}", k["row"]["prompt"]) for i, k in enumerate(kept)])
    return {"kept": kept, "dropped": dict(sorted(dropped.items())), "walked": walked,
            "walked_at_or_above": {str(t): at_or_above[str(t)] for t in REPORT_THRESHOLDS}}


# ----- documents ------------------------------------------------------------------------------------


def uid_of(row: dict) -> str:
    return f"{row['source']}:{row['line']:06d}:{row['response_index']}"     # the engine's injected-row uid


def anchor_record(index: int, kept: dict, harmful_size: int) -> dict:
    row = kept["row"]
    return {"index": index, "set": "harmful" if index < harmful_size else "reserve", "uid": uid_of(row),
            "source": row["source"], "line_0based": row["line"] - 1, "line_1based": row["line"],
            "response_index": row["response_index"],
            "prompt_sha256": sha256_bytes(row["prompt"].encode("utf-8")),
            "unsafe_response_sha256": sha256_bytes(row["response"].encode("utf-8")),
            "severity": row["severity"], "category": row["categories"][0], "categories": list(row["categories"]),
            "prompt_chars": len(row["prompt"]), "unsafe_response_chars": len(row["response"]),
            "jaccard_vs_evaluation": round(kept["jaccard_evaluation"], 6),
            "jaccard_vs_earlier_anchor": round(kept["jaccard_anchor"], 6)}


def validate_list(data: bytes, list_size: int = LIST_SIZE, harmful_size: int = HARMFUL_SIZE) -> dict:
    """The A9 schema plus the allowed top-level ``provenance`` object. Raises ValueError (positions only)."""
    doc = json.loads(data)
    if canonical_json(doc) != data:
        raise ValueError("the list is not canonical JSON (sorted keys, 2-space indent, UTF-8, final newline)")
    if not isinstance(doc, dict) or set(doc) != LIST_KEYS:
        raise ValueError(f"the list must have exactly the keys {sorted(LIST_KEYS)}")
    if doc["kind"] != LIST_KIND or doc["version"] != LIST_VERSION:
        raise ValueError(f"not a {LIST_KIND!r} of version {LIST_VERSION}")
    source = doc["source"]
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        raise ValueError(f"source must have exactly the keys {sorted(SOURCE_KEYS)}")
    if not (isinstance(source["repo_id"], str) and isinstance(source["revision"], str)):
        raise ValueError("source.repo_id and source.revision must be strings")
    hashes = source["file_sha256"]
    if not (isinstance(hashes, dict) and hashes and all(isinstance(k, str) and _is_sha256(v) for k, v in hashes.items())):
        raise ValueError("source.file_sha256 must map each source file to its SHA-256")
    prompts = doc["prompts"]
    if not isinstance(prompts, list) or len(prompts) != list_size:
        raise ValueError(f"prompts must be a list of {list_size} objects")
    seen = set()
    for position, item in enumerate(prompts):
        if not isinstance(item, dict) or set(item) != PROMPT_KEYS:
            raise ValueError(f"prompts[{position}] must have exactly the keys {sorted(PROMPT_KEYS)}")
        if item["index"] != position:
            raise ValueError(f"prompts[{position}].index is not {position}")
        for key in ("prompt", "unsafe_response"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"prompts[{position}].{key} is not a non-empty string")
        key = normalize(item["prompt"])
        if key in seen:
            raise ValueError(f"prompts[{position}] repeats an earlier normalized prompt")
        seen.add(key)
    if not isinstance(doc["provenance"], dict):
        raise ValueError("provenance must be an object")
    return {"prompts": len(prompts), "harmful": harmful_size, "reserve": len(prompts) - harmful_size}


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


# ----- build ----------------------------------------------------------------------------------------


def build(*, config_path: Path, config_sha256: str | None, sources_root: Path, prepared_root: Path,
          prepared_manifest_sha256: str | None, full_path: Path, out_dir: Path, full_label: str = FULL_REL,
          out_label: str = OUT_LABEL, built_at: str | None = None, design_seed: int = DESIGN_SEED,
          stream: str = STREAM, list_size: int = LIST_SIZE, harmful_size: int = HARMFUL_SIZE,
          severity_floor: int = SEVERITY_FLOOR) -> dict:
    out_dir, full_path = Path(out_dir).resolve(), Path(full_path).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        stop(f"{out_dir} exists and is not empty: a sealed build never overwrites")
    if full_path.exists():
        stop(f"{full_path} exists: a sealed build never overwrites")
    if not 0 < harmful_size < list_size:
        stop(f"harmful size {harmful_size} must lie strictly inside the list size {list_size}")
    script_path = Path(__file__).resolve()
    script_sha256 = sha256_path(script_path)
    if derive_seed is not _ms_common.derive_seed or not inspect.isfunction(derive_seed):
        stop("experiments.safety_selection.common.derive_seed is not the minimal-safety function")
    source_lines, first_line = inspect.getsourcelines(derive_seed)
    derive_seed_file = Path(inspect.getsourcefile(derive_seed)).resolve()
    functions = {name: sha256_bytes(inspect.getsource(obj).encode("utf-8")) for name, obj in ENGINE_FUNCTIONS.items()}
    seed = derive_seed(design_seed, stream)
    text = f"{design_seed}|{stream}"
    if seed != int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big"):
        stop("the engine's derive_seed disagrees with the stated formula")

    config, config_digest = load_config(Path(config_path), config_sha256)
    sources = read_sources(config, Path(sources_root))
    evaluation = load_evaluation(Path(prepared_root), prepared_manifest_sha256)
    inj = config["injection"]
    min_severity = max(severity_floor, inj["min_severity"])
    limit = inj["near_duplicate"]["max_jaccard"]
    forbidden = list(dict.fromkeys([*config["eligibility"]["forbidden_substrings"], *evaluation["forbidden"]]))

    candidates = candidates_of(sources["rows"], min_severity)
    expected = (inj.get("expected") or {}).get("candidates")
    if expected is not None and min_severity == inj["min_severity"] and len(candidates) != expected:
        stop(f"{len(candidates)} candidates, the data config asserts {expected}")
    eligible, reasons, duplicates = eligible_of(candidates, forbidden, evaluation["existing"])
    order, eligible_by_category = balanced_order(eligible, sources["category_order"], seed)
    walked = walk(order, evaluation["evaluation"], limit, list_size)
    kept = walked["kept"]
    if len(kept) < list_size:
        stop(f"only {len(kept)} of {list_size} anchors kept after walking {walked['walked']} of {len(order)} "
             f"ordered candidates ({len(candidates)} candidates, {len(eligible)} eligible); dropped {walked['dropped']}")

    anchors = [anchor_record(i, k, harmful_size) for i, k in enumerate(kept)]
    harmful, reserve = anchors[:harmful_size], anchors[harmful_size:]
    counts = {"source_records": sum(r["records"] for r in sources["receipts"].values()),
              "source_responses": len(sources["rows"]), "candidates": len(candidates), "eligible": len(eligible),
              "eligible_duplicate_prompts_dropped": sum(duplicates.values()),
              "ordered": len(order), "drawn_before_dedup": walked["walked"],
              "dropped_bank_near_duplicate": walked["dropped"].get("near_duplicate_of_evaluation_prompt", 0),
              "dropped_anchor_near_duplicate": walked["dropped"].get("near_duplicate_of_kept_anchor", 0),
              "kept": len(kept), "harmful": len(harmful), "reserve": len(reserve),
              "max_prompt_chars": max(a["prompt_chars"] for a in anchors),
              "max_unsafe_response_chars": max(a["unsafe_response_chars"] for a in anchors)}
    repo_ids = {config["extra_sources"][n]["repo_id"] for n in sources["source_order"]}
    revisions = {config["extra_sources"][n]["revision"] for n in sources["source_order"]}
    if len(repo_ids) != 1 or len(revisions) != 1:
        stop("the injection sources name more than one repo_id or revision")
    built_at = built_at or utc_now()
    identity = code_identity()
    facts = {
        "script": {"path": SCRIPT_REL, "sha256": script_sha256},
        "spec": {"path": SPEC_REL, "section": SPEC_SECTION},
        "brief": {"path": BRIEF_REL, "item": BRIEF_ITEM},
        "config": {"path": CONFIG_REL, "sha256": config_digest, "injection_sources": sources["source_order"],
                   "min_severity": inj["min_severity"], "max_jaccard": limit,
                   "forbidden_substrings": forbidden},
        "sources": {name: {"repo_id": config["extra_sources"][name]["repo_id"],
                           "revision": config["extra_sources"][name]["revision"],
                           "file": config["extra_sources"][name]["file"], "sha256": sources["hashes"][name],
                           "records": sources["receipts"][name]["records"],
                           "responses": sources["receipts"][name]["responses"],
                           "blank_lines": sources["receipts"][name]["blank_lines"]}
                    for name in sources["source_order"]},
        "prepared": {"root": PREPARED_REL, "manifest_sha256": evaluation["manifest_sha256"],
                     "data_config": evaluation["data_config_name"], "files_read": evaluation["files"],
                     "evaluation_items": evaluation["items"], "evaluation_forms": evaluation["forms"],
                     "training_rows": evaluation["training_rows"], "query_rows": evaluation["query_rows"]},
        "engine": {"function_source_sha256": functions},
        "draw": {"design_seed": design_seed, "stream": stream, "seed": seed, "seed_rule": SEED_RULE,
                 "min_severity_used": min_severity, "list_size": list_size, "harmful_size": harmful_size},
        "counts": counts,
        "excluded_by_reason": reasons,
        "duplicate_prompt_dropped_by_category": duplicates,
        "dropped_by_reason": walked["dropped"],
        "category_order": sources["category_order"],
        "category_counts": {"eligible": eligible_by_category,
                            "harmful": _by(harmful, "category", sources["category_order"]),
                            "reserve": _by(reserve, "category", sources["category_order"]),
                            "all": _by(anchors, "category", sources["category_order"])},
        "severity_counts": {"harmful": _by(harmful, "severity"), "reserve": _by(reserve, "severity")},
        "near_duplicate": {"max_jaccard": limit, "evaluation_forms": evaluation["forms"],
                           "largest_jaccard_kept_vs_evaluation": max(a["jaccard_vs_evaluation"] for a in anchors),
                           "largest_jaccard_kept_vs_earlier_anchor": max(a["jaccard_vs_earlier_anchor"] for a in anchors),
                           "walked_at_or_above": walked["walked_at_or_above"]},
        "sets": {"harmful": f"prompts[0:{harmful_size}]", "reserve": f"prompts[{harmful_size}:{list_size}]"},
        "built_at_utc": built_at}

    full_doc = {"kind": LIST_KIND, "version": LIST_VERSION,
                "source": {"repo_id": repo_ids.pop(), "revision": revisions.pop(),
                           "file_sha256": {config["extra_sources"][n]["file"]: sources["hashes"][n]
                                           for n in sources["source_order"]}},
                "prompts": [{"index": i, "prompt": k["row"]["prompt"], "unsafe_response": k["row"]["response"]}
                            for i, k in enumerate(kept)],
                "provenance": {**facts, "rules": {"eligibility": ELIGIBILITY_RULE, "balance": BALANCE_RULE,
                                                   "walk": WALK_RULE, "near_duplicate": NEAR_DUPLICATE,
                                                   "engine_injection_rule": INJECTION_RULE,
                                                   "normalization": NORMALIZATION},
                               "anchors": anchors, "full_list": {"path": full_label},
                               "schema": {"required_keys": sorted(LIST_KEYS - {"provenance"}),
                                          "extra_key_allowed": "provenance",
                                          "prompt_keys": sorted(PROMPT_KEYS), "index": "0-based position"}}}
    full_bytes = canonical_json(full_doc)
    try:
        validate_list(full_bytes, list_size, harmful_size)
    except ValueError as exc:
        stop(f"the full list fails its own schema check: {exc}")
    full_sha256 = sha256_bytes(full_bytes)
    for anchor in anchors:                                     # the record must describe the written text
        item = full_doc["prompts"][anchor["index"]]
        if (sha256_bytes(item["prompt"].encode("utf-8")) != anchor["prompt_sha256"]
                or sha256_bytes(item["unsafe_response"].encode("utf-8")) != anchor["unsafe_response_sha256"]):
            stop(f"internal: anchor {anchor['index']} hashes differ from the list")

    sealed = {"kind": SEALED_KIND, "version": 1, **facts,
              "full_list": {"path": full_label, "sha256": full_sha256, "bytes": len(full_bytes),
                            "git": "ignored (tmp/); carried by SHA-256"},
              "anchors": anchors}
    sealed_bytes = canonical_json(sealed)
    manifest = {"kind": MANIFEST_KIND, "version": 1, "built_at_utc": built_at,
                "script": {"path": SCRIPT_REL, "sha256": script_sha256, "python": sys.version.split()[0],
                           "executable": sys.executable},
                "spec": {"path": SPEC_REL, "section": SPEC_SECTION,
                         "sha256_at_build": sha256_path(REPO / SPEC_REL) if (REPO / SPEC_REL).is_file() else None},
                "brief": {"path": BRIEF_REL, "item": BRIEF_ITEM,
                          "sha256_at_build": sha256_path(REPO / BRIEF_REL) if (REPO / BRIEF_REL).is_file() else None},
                "engine": {"code_identity_sha256": identity["sha256"], "git_head": git_head(REPO),
                           "derive_seed": {"file": str(derive_seed_file.relative_to(REPO)),
                                           "lines": [first_line, first_line + len(source_lines) - 1],
                                           "file_sha256": sha256_path(derive_seed_file)},
                           "prepare_file_sha256": identity["files"]["safety_selection/prepare.py"],
                           "sources_file_sha256": identity["files"]["safety_selection/sources.py"],
                           "function_source_sha256": functions,
                           "note": "whole-file and repo-state hashes live here only; the sealed files pin the "
                                   "functions they use by source hash"},
                "full_list": {"path": full_label, "sha256": full_sha256, "bytes": len(full_bytes),
                              "git": "ignored (tmp/); carried by SHA-256"},
                "files": [{"path": f"{out_label}/{SEALED_NAME}", "sha256": sha256_bytes(sealed_bytes),
                           "bytes": len(sealed_bytes)},
                          {"path": SCRIPT_REL, "sha256": script_sha256, "bytes": script_path.stat().st_size}],
                "counts": counts}
    manifest_bytes = canonical_json(manifest)

    write_atomic(full_path, full_bytes)
    write_atomic(out_dir / SEALED_NAME, sealed_bytes)
    write_atomic(out_dir / MANIFEST_NAME, manifest_bytes)
    for path, data in ((full_path, full_bytes), (out_dir / SEALED_NAME, sealed_bytes),
                       (out_dir / MANIFEST_NAME, manifest_bytes)):
        if sha256_path(path) != sha256_bytes(data):
            stop(f"{path} did not read back as written")

    result = {"script_sha256": script_sha256, "config_sha256": config_digest, "source_sha256": sources["hashes"],
              "prepared_manifest_sha256": evaluation["manifest_sha256"], "seed": seed,
              "full_list_sha256": full_sha256, "full_list_bytes": len(full_bytes),
              "sealed_record_sha256": sha256_bytes(sealed_bytes), "manifest_sha256": sha256_bytes(manifest_bytes),
              "counts": counts, "excluded_by_reason": reasons, "dropped_by_reason": walked["dropped"],
              "category_counts": facts["category_counts"], "near_duplicate": facts["near_duplicate"],
              "paths": {"full": str(full_path), "sealed": str(out_dir / SEALED_NAME),
                        "manifest": str(out_dir / MANIFEST_NAME)}}
    return result


def _by(records: list[dict], key: str, order: list | None = None) -> dict:
    counter = Counter(r[key] for r in records)
    if order is not None:
        return {c: counter[c] for c in order}
    return {str(k): counter[k] for k in sorted(counter)}


def report(result: dict) -> None:
    print(f"script sha256 {result['script_sha256']}")
    print(f"data config sha256 {result['config_sha256']}")
    for name, digest in result["source_sha256"].items():
        print(f"source {name} sha256 {digest}")
    print(f"prepared manifest sha256 {result['prepared_manifest_sha256']}")
    print(f"seed {result['seed']} = {SEED_RULE}")
    print("counts " + json.dumps(result["counts"], sort_keys=True))
    print("excluded_by_reason " + json.dumps(result["excluded_by_reason"], sort_keys=True))
    print("dropped_by_reason " + json.dumps(result["dropped_by_reason"], sort_keys=True))
    print("category_counts harmful " + json.dumps(result["category_counts"]["harmful"]))
    print("category_counts reserve " + json.dumps(result["category_counts"]["reserve"]))
    print("near_duplicate " + json.dumps(result["near_duplicate"], sort_keys=True))
    print(f"full list sha256 {result['full_list_sha256']} bytes {result['full_list_bytes']}  {result['paths']['full']}")
    print(f"sealed record sha256 {result['sealed_record_sha256']}  {result['paths']['sealed']}")
    print(f"manifest sha256 {result['manifest_sha256']}  {result['paths']['manifest']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=HERE / "out", help="output folder (must be absent or empty)")
    parser.add_argument("--full", type=Path, default=REPO / FULL_REL, help="the FULL list path (must be absent)")
    parser.add_argument("--built-at", default=None, help="UTC time to record (ISO 8601; default: now)")
    args = parser.parse_args(argv)
    result = build(config_path=REPO / CONFIG_REL, config_sha256=CONFIG_SHA256, sources_root=REPO / SOURCES_REL,
                   prepared_root=REPO / PREPARED_REL, prepared_manifest_sha256=PREPARED_MANIFEST_SHA256,
                   full_path=args.full, out_dir=args.out, built_at=args.built_at)
    report(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
