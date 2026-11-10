"""The $0 encode count of one 7-8B family (Mac; no model, no network; counts, ids and hashes only).

    PY -I -B scripts/scale78b/encode_count_78b.py --family F --prepared P_F [--recipe MAIN_F]
        --list s1=PATH:SHA256 --list s3_safe=PATH:SHA256 --list s4_candidates=PATH:SHA256
        [--s-pool-record PATH:SHA256] --out REC.json
    PY -I -B scripts/scale78b/encode_count_78b.py --bank --family F --prepared P_F [--recipe MAIN_F]
        --oext-record PATH:SHA256 --oext-bank PATH:SHA256 --out REC.json
    PY -I -B scripts/scale78b/encode_count_78b.py --anchor --family F --prepared P_F [--recipe MAIN_F]
        --prompts PATH:SHA256 --out REC.json

What it counts (Part 2 section 1.8 with amendment 1's changes 4, 8 and 11; DES DESO items 6, 17; DESO3 item 38; DES E1;
GXB O6, O13):

- **lists** (the default mode): ``encode_generation_prompt`` for every prompt of stage 1's sealed S1 (48), ``s3_safe``
  (861) and ``s4_candidates`` (512) lists at MAIN_F's ``model.max_prompt_tokens``, and ``encode_train`` for every
  (prompt, PKU-safe response) pair of ``s3_safe`` and S1 at MAIN_F's ``model.max_train_tokens``. The S3 subset (855)
  is not read as a file: its ids come from the committed s-pool record (``lists.s3_subset.ids``) and are a subset of
  ``s3_safe``'s, so its counts are ``s3_safe``'s restricted to those ids. The lists are read by the frozen
  ``make_untuned_answers.read_list`` (the untuned pass's own reader); their ids must equal the record's.
- **--bank**: ``encode_generation_prompt`` for the 400 sealed PHTest prompts, read through the frozen
  ``oext_eval.load_bank`` under ``oext_eval``'s pinned settings (record ``a810574e…``), at MAIN_F's
  ``model.max_prompt_tokens`` (the limit ``oext_eval._encode`` uses).
- **--anchor** (informational only; GXB O6: the anchor job's own result decides): exactly the two encode checks that
  ``scripts/make_anchor_answers.py`` makes after its policy loads and before it generates: its harmful-pair check
  (``_encoded`` on the first 64 (prompt, unsafe response) pairs at ``model.max_train_tokens``; :121 stops the job at the
  first failure) and its generation-prompt check (``encode_generation_prompt`` on all 128 prompts at
  ``model.max_prompt_tokens``; :129). The list is read by the frozen ``read_prompt_list`` at the frozen ``LIST_SHA256``.
  Every failure is counted here (the job stops at the first); the first failing index of each check is recorded.

The limits are MAIN_F's ``model`` block (both families: max_prompt_tokens 1536, max_train_tokens 3072): the frozen
callers read ``recipe["model"]["max_prompt_tokens"]`` (``make_untuned_answers.py`` :251, ``oext_eval.py`` :525,
``make_anchor_answers.py`` :127); MAIN_F holds no ``generation.max_prompt_tokens``. The recipe must hash to the
family's pin (``config_sha256``). The codec is built as ``scripts/stage1/build_s_pool.real_codec`` builds it, from the
family's prepared manifest's tokenizer (offline cache), the manifest read at its pinned SHA-256; that tokenizer must be
the recipe's (``config.tokenizer_of``) with the same end-of-turn token, so the counts are the pod's.

Every input is named PATH:SHA256 and must hash to this module's literal pin for it (an off-pin input refuses). A refusal
of one item is counted under its exception's class name (``TooLong``, ``ControlTokenError``, ``NoTargets``, ...), as the
frozen callers count it; any other exception refuses the run. Output: one text-free canonical JSON record at --out
(created once and complete or not at all; never inside any input's folder, at any depth, nor inside P_F) with counts by reason, the refused ids (ids or
list indices only), the input SHA-256s, the recipe's SHA-256 and the tokenizer's revision prefix. No prompt or response
text reaches stdout, stderr, the record or a message: every output and message is scanned against every text read, and
a message that could hold text is replaced by its exception's class name.

Exit 0: written, every item accepted (anchor mode: written); 1: written, some item refused (lists and bank modes);
2: refused, nothing written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import traceback
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

KIND = "scale78b encode count"
RULE = ("Part 2 section 1.8 with amendment 1 changes 4, 8, 11 (research/experiments/2026-11-06-78b-preregistration-part2.md, "
        "research/experiments/2026-11-08-78b-preregistration-part2-amendment-1.md); DES DESO items 6, 17, DESO3 item 38, "
        "E1 (.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part2-design-20261106.md); GXB O6, O13 "
        "(.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-ab-build-20261108.md)")
MODES = ("lists", "bank", "anchor")
FAMILIES = ("olmo2-7b", "llama31-8b")
# MAIN_F by path and config_sha256 (R: runkit/stage1-78b/rules_78b.py:113-129 CONFIGS[F]["main"]; pins_78b.json
# families.F.main_recipe; Part 2 section 1.1).
RECIPES = {
    "olmo2-7b": ("experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-20261008.json",
                 "18cc31d7117a2de7bc02382fe8a4d409fc43c91b434bf219a4808dfb26528d09"),
    "llama31-8b": ("experiments/safety_selection/configs/study-kt-llama31-8b-r64-b5e5-mb2-20261010.json",
                   "74758af1791d9f7a8ce616adce7549b5b7b0619e55310158d7e21197ed129893"),
}
# P_F's manifest SHA-256 (R: rules_78b.py:110-111 MANIFESTS; pins_78b.json families.F.manifest_sha256).
MANIFESTS = {"olmo2-7b": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9",
             "llama31-8b": "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"}
# Stage 1's sealed lists (R: Part 2 section 1.8; pins_78b.json shared.sealed_lists_1b; the s-pool record's lists and
# s3_pool blocks, M: printed at 3481d85): name -> (SHA-256, items).
LIST_PINS = {"s1": ("389c20ad00261b1a304d3dd9f14a113a0b05bcec63758262af1b1629d48e0480", 48),
             "s3_safe": ("6801652cb506f9626575f6e156e103682308830e4e5ef1cb299dd3fa00021fed", 861),
             "s4_candidates": ("798613c4e5d32caaf51b255b2413395a1477b377f0b97f85933efdc5b35cf17d", 512)}
S3_SUBSET_PIN = ("dea5ec15a1f43e19563ab0b946a5c53c5ae67353b4b4317b509edf59f029c581", 855)   # by the record's ids only
S_POOL_RECORD = (".ai/inputs/stage1-commitments-20261016/s-pool/s_pool_record.json",
                 "bcca59ac0f8c15c354b9d9b124c1e17211c7e602800424f40292160934383c6f")
# Which checks run on which list (DESO items 6, 17; DESO3 item 38).
LIST_CHECKS = {"s1": ("generation_prompt", "encode_train"), "s3_safe": ("generation_prompt", "encode_train"),
               "s4_candidates": ("generation_prompt",)}
# The O-ext bank's build record (R: scripts/stage1_s1/settings/oext_eval.json bank.phtest.record_sha256, planned; DES E1).
OEXT_RECORD_SHA256 = "a810574e958ca0e5773c583b0f1df630ff7acc1bb2fc32e5f0de1c63d8c37fa9"
OEXT_PLANNED = 400
# The anchor job's sealed list and its sizes (R: scripts/make_anchor_answers.py:30-33; pins_78b.json
# shared.anchor_prompt_list_sha256).
ANCHOR_LIST_SHA256 = "78467c97c40e7e9fd39e8061219517853e7292a25881700da5e9115604117b97"
ANCHOR_PROMPTS, ANCHOR_HARMFUL = 128, 64
REVISION_PREFIX = 12
EXIT_ALL, EXIT_SOME, EXIT_REFUSED = 0, 1, 2


class Refusal(Exception):
    """The count cannot run as asked: nothing is written. Messages hold ids, counts and hashes only."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(doc: Any) -> bytes:
    from experiments.safety_selection.common import canonical_json

    return canonical_json(doc)


# ----- the text guard ---------------------------------------------------------------------------------------------


class TextGuard:
    """Every prompt and response text read in this run. ``hits`` says whether some bytes hold one of them (raw or
    JSON-escaped; texts of at least ``min_chars`` characters, the frozen ``s1common._text_hits`` rule)."""

    def __init__(self, min_chars: int = 6):
        self.texts: list[str] = []
        self.min_chars = min_chars

    def add(self, *texts: Any) -> None:
        self.texts.extend(t for t in texts if isinstance(t, str))

    def hits(self, data: bytes | str) -> bool:
        from scripts.stage1 import s1common as s1

        raw = data.encode("utf-8") if isinstance(data, str) else data
        return s1._text_hits(raw, self.texts, self.min_chars) > 0

    def message(self, exc: BaseException) -> str:
        """A refusal's message if it holds no text read; else only the exception's class name."""
        text = str(exc) if isinstance(exc, Refusal) else ""
        if not text or self.hits(text):
            frames = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ is not None else []
            where = f" at {Path(frames[-1].filename).name}:{frames[-1].lineno}" if frames else ""
            return (f"{type(exc).__name__}{where} (message withheld: only refusals written by this script are "
                    "printed)")
        return text


# ----- inputs ------------------------------------------------------------------------------------------------------


def parse_spec(spec: str, what: str) -> tuple[Path, str]:
    """PATH:SHA256 (the last colon splits)."""
    path, sep, digest = spec.rpartition(":")
    if not sep or not path or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise Refusal(f"{what} is PATH:SHA256 with 64 lower-case hex digits")
    return Path(path), digest


def parse_named(specs: Sequence[str], allowed: Iterable[str]) -> dict[str, tuple[Path, str]]:
    """--list NAME=PATH:SHA256, each allowed name exactly once."""
    allowed = tuple(allowed)
    out: dict[str, tuple[Path, str]] = {}
    for spec in specs:
        name, sep, rest = spec.partition("=")
        if not sep or name not in allowed:
            raise Refusal(f"--list takes NAME=PATH:SHA256 with NAME one of {', '.join(allowed)}")
        if name in out:
            raise Refusal(f"--list names {name} twice")
        out[name] = parse_spec(rest, f"--list {name}")
    missing = [n for n in allowed if n not in out]
    if missing:
        raise Refusal(f"--list needs {', '.join(missing)} too")
    return out


def pinned(given: str, pin: str, what: str) -> str:
    """The SHA-256 a command line names must be the module's pin for that input."""
    if given != pin:
        raise Refusal(f"{what}: the command line names {given}; the pin is {pin}")
    return pin


def read_pinned(path: Path, pin: str, what: str) -> bytes:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != pin:
        raise Refusal(f"{what} hashes to {sha256_bytes(data)}; the pin is {pin}")
    return data


def load_recipe(family: str, path: Path | None) -> tuple[dict, str, str, dict]:
    """(recipe, its config_sha256, the path label, the limits) of MAIN_F; another recipe refuses."""
    from experiments.safety_selection.config import config_sha256, load_recipe as engine_load_recipe

    default, pin = RECIPES[family]
    path = Path(path) if path is not None else REPO / default
    try:
        recipe = engine_load_recipe(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Refusal(f"the recipe cannot be loaded ({type(exc).__name__})") from None
    digest = config_sha256(recipe)
    if digest != pin:
        raise Refusal(f"the recipe's config_sha256 is {digest}; {family}'s main recipe is {pin}")
    model = recipe["model"]
    limits = {"max_prompt_tokens": model["max_prompt_tokens"], "max_train_tokens": model["max_train_tokens"]}
    return recipe, digest, str(path), limits


class Context:
    """The codec and the identity of its tokenizer: {repo_id, revision, end_of_turn_token}, and the manifest pin."""

    def __init__(self, codec: Any, tokenizer: Mapping[str, Any], manifest_sha256: str):
        self.codec, self.tokenizer, self.manifest_sha256 = codec, dict(tokenizer), manifest_sha256


def real_context(family: str, prepared: Path) -> Context:
    """P_F's manifest at its pin, and the codec as build_s_pool.real_codec builds it from that manifest's tokenizer."""
    from experiments.safety_selection.prepare import read_manifest
    from scripts.stage1 import build_s_pool

    pin = MANIFESTS[family]
    try:
        manifest, digest = read_manifest(prepared, pin)
        tk = manifest["data_config"]["tokenizer"]
        tokenizer = {k: tk[k] for k in ("repo_id", "revision", "end_of_turn_token")}
        codec = build_s_pool.real_codec(Path(prepared), {"inputs": {"prepared_manifest_sha256": pin}})
    except Exception as exc:          # DataError, OSError, KeyError, the tokenizer's own: the class name only
        raise Refusal(f"the prepared set's manifest or tokenizer cannot be loaded ({type(exc).__name__})") from None
    return Context(codec, tokenizer, digest)


def check_tokenizer(recipe: Mapping[str, Any], ctx: Context) -> dict:
    """The manifest's tokenizer is the recipe's (repository, revision, end-of-turn token)."""
    from experiments.safety_selection.config import tokenizer_of

    repo_id, revision = tokenizer_of(recipe)
    tk = ctx.tokenizer
    if (tk.get("repo_id"), tk.get("revision")) != (repo_id, revision):
        raise Refusal(f"the prepared manifest's tokenizer ({str(tk.get('revision'))[:REVISION_PREFIX]}) is not the "
                      f"recipe's ({str(revision)[:REVISION_PREFIX]})")
    if tk.get("end_of_turn_token") != recipe["model"]["end_of_turn_token"]:
        raise Refusal("the prepared manifest's end-of-turn token is not the recipe's")
    return {"repo_id": repo_id, "revision_prefix": str(revision)[:REVISION_PREFIX]}


# ----- the counts --------------------------------------------------------------------------------------------------


def _tally(n: int, refused: list[tuple[Any, str]]) -> dict:
    return {"n": n, "accepted": n - len(refused), "refused": len(refused),
            "refused_by_reason": dict(sorted(Counter(r for _, r in refused).items())),
            "refused_ids": [k for k, _ in refused]}


def refusals_generation(codec: Any, rows: Sequence[tuple[Any, str]], max_tokens: int) -> list[tuple[Any, str]]:
    """encode_generation_prompt on each (key, prompt); a ValueError is a refusal named by its class (the frozen
    callers' rule: make_untuned_answers.py:105-112, oext_eval.py:527-531, make_anchor_answers.py:125-131)."""
    from experiments.safety_selection.textproc import encode_generation_prompt

    refused = []
    for key, prompt in rows:
        try:
            encode_generation_prompt(codec, prompt, max_tokens)
        except ValueError as exc:
            refused.append((key, type(exc).__name__))
    return refused


def refusals_train(codec: Any, rows: Sequence[tuple[str, str, str]], max_tokens: int) -> list[tuple[str, str]]:
    """encode_train on each (id, prompt, response); a ValueError is a refusal named by its class (the frozen
    callers' rule: make_untuned_answers.py:189-194, representation_pass.py:337-348)."""
    from experiments.safety_selection.textproc import encode_train

    refused = []
    for row_id, prompt, response in rows:
        try:
            encode_train(codec, row_id, prompt, response, max_tokens)
        except ValueError as exc:
            refused.append((row_id, type(exc).__name__))
    return refused


# ----- mode: lists -------------------------------------------------------------------------------------------------


def read_s_pool_record(path: Path, pin: str, list_pins: Mapping[str, tuple[str, int]],
                       subset_pin: tuple[str, int]) -> dict:
    """The committed s-pool record at its pin; its list and pool hashes must be the lists' pins."""
    from scripts.stage1 import s1common as s1

    try:
        doc = s1.strict_json(read_pinned(path, pin, "the s-pool record"))
    except s1.Refusal as exc:
        raise Refusal(str(exc)) from None
    if not isinstance(doc, dict) or doc.get("kind") != "stage1 s-pool record":
        raise Refusal("the s-pool record is not a stage1 s-pool record")
    lists, pool = doc.get("lists") or {}, doc.get("s3_pool") or {}
    expect = {"s1": list_pins["s1"], "s3_subset": subset_pin, "s4_candidates": list_pins["s4_candidates"]}
    ids = {}
    for name, (digest, size) in expect.items():
        entry = lists.get(name) or {}
        got = entry.get("ids")
        if entry.get("sha256") != digest or not isinstance(got, list) or len(got) != size:
            raise Refusal(f"the s-pool record's list {name} is not the pinned list ({digest[:16]}..., {size} ids)")
        ids[name] = list(got)
    if pool.get("sha256") != list_pins["s3_safe"][0] or pool.get("items") != list_pins["s3_safe"][1]:
        raise Refusal("the s-pool record's s3_pool is not the pinned s3_safe pool")
    return ids


def read_list_items(path: Path, digest: str, name: str, size: int, guard: TextGuard, need_response: bool) -> list[dict]:
    """The list through the frozen make_untuned_answers.read_list (hash, kind, distinct short ids, text prompts, size)."""
    from scripts.stage1 import make_untuned_answers as mua
    from scripts.stage1 import s1common as s1

    try:
        items = mua.read_list(path, digest, name, {"size": size})
    except s1.Refusal as exc:
        raise Refusal(str(exc)) from None
    for item in items:
        guard.add(item.get("prompt"), item.get("response"))
    if need_response and any(not isinstance(i.get("response"), str) for i in items):
        raise Refusal(f"list {name}: an item holds no text response")
    return items


def run_lists(family: str, recipe_path: Path | None, ctx: Context, lists: Mapping[str, tuple[Path, str]],
              record: tuple[Path, str], guard: TextGuard, *, list_pins: Mapping[str, tuple[str, int]] = LIST_PINS,
              record_pin: str = S_POOL_RECORD[1], subset_pin: tuple[str, int] = S3_SUBSET_PIN) -> dict:
    recipe, recipe_sha, recipe_label, limits = load_recipe(family, recipe_path)
    tokenizer = check_tokenizer(recipe, ctx)
    for name, (_, given) in lists.items():
        pinned(given, list_pins[name][0], f"list {name}")
    pinned(record[1], record_pin, "the s-pool record")
    record_ids = read_s_pool_record(record[0], record_pin, list_pins, subset_pin)
    items = {name: read_list_items(lists[name][0], list_pins[name][0], name, list_pins[name][1], guard,
                                   "encode_train" in LIST_CHECKS[name]) for name in LIST_CHECKS}
    ids = {name: [i["id"] for i in rows] for name, rows in items.items()}
    for name in ("s1", "s4_candidates"):
        if ids[name] != record_ids[name]:
            raise Refusal(f"list {name}'s ids are not the s-pool record's (in order)")
    subset = record_ids["s3_subset"]
    expected_pool = subset + [i for i in record_ids["s1"] if i not in set(subset)]
    if ids["s3_safe"] != expected_pool:
        raise Refusal("s3_safe's ids are not the S3 subset then S1's rows outside it (the s-pool record's order)")
    pool_by_id = {i["id"]: i for i in items["s3_safe"]}
    for row in items["s1"]:
        twin = pool_by_id.get(row["id"])
        if twin is not None and (twin["prompt"], twin.get("response")) != (row["prompt"], row.get("response")):
            raise Refusal(f"s1.json and s3_safe.pool.json differ on row {row['id']}")
    checks: dict[str, dict] = {}
    s3_reasons: dict[str, dict[str, str]] = {}
    for name in LIST_CHECKS:
        rows = items[name]
        found = {"generation_prompt": refusals_generation(ctx.codec, [(r["id"], r["prompt"]) for r in rows],
                                                          limits["max_prompt_tokens"])}
        if "encode_train" in LIST_CHECKS[name]:
            found["encode_train"] = refusals_train(ctx.codec, [(r["id"], r["prompt"], r["response"]) for r in rows],
                                                   limits["max_train_tokens"])
        checks[name] = {kind: _tally(len(rows), refused) for kind, refused in found.items()}
        if name == "s3_safe":
            s3_reasons = {kind: dict(refused) for kind, refused in found.items()}
    checks["s3_subset"] = {kind: _tally(len(subset), [(i, s3_reasons[kind][i]) for i in subset if i in s3_reasons[kind]])
                           for kind in LIST_CHECKS["s3_safe"]}
    inputs = {name: {"sha256": list_pins[name][0], "items": len(items[name])} for name in LIST_CHECKS}
    inputs["s3_subset"] = {"sha256": subset_pin[0], "items": len(subset), "read": "ids from the s-pool record only"}
    inputs["s_pool_record"] = {"sha256": record_pin}
    refused_total = sum(tally["refused"] for name in LIST_CHECKS for tally in checks[name].values())
    return doc_of("lists", family, recipe_sha, recipe_label, limits, tokenizer, ctx, inputs, checks,
                  all_accepted=refused_total == 0)


# ----- mode: bank --------------------------------------------------------------------------------------------------


def run_bank(family: str, recipe_path: Path | None, ctx: Context, bank: tuple[Path, str], record: tuple[Path, str],
             guard: TextGuard, *, settings: Any = None, record_pin: str = OEXT_RECORD_SHA256,
             planned: int = OEXT_PLANNED) -> dict:
    from scripts.stage1_s1 import oext_eval

    recipe, recipe_sha, recipe_label, limits = load_recipe(family, recipe_path)
    tokenizer = check_tokenizer(recipe, ctx)
    try:
        settings = settings if settings is not None else oext_eval.load_pinned_settings()
    except oext_eval.Refusal as exc:
        raise Refusal(str(exc)) from None
    spec = settings.doc["bank"]["phtest"]
    if spec["record_sha256"] != record_pin or spec["planned"] != planned:
        raise Refusal(f"oext_eval's settings pin the bank record {spec['record_sha256']} with {spec['planned']} "
                      f"prompts; this count needs {record_pin} with {planned}")
    pinned(record[1], record_pin, "the O-ext bank record")
    try:
        loaded = oext_eval.load_bank(settings, bank[0], record[0])
    except oext_eval.Refusal as exc:
        raise Refusal(str(exc)) from None
    for _, prompt in loaded.rows:
        guard.add(prompt)
    pinned(bank[1], loaded.bank_sha256, "the O-ext bank file (its record's full_file SHA-256)")
    if len(loaded.rows) != planned:
        raise Refusal(f"the O-ext bank holds {len(loaded.rows)} prompts, not {planned}")
    checks = {"phtest": {"generation_prompt": _tally(len(loaded.rows), refusals_generation(
        ctx.codec, list(loaded.rows), limits["max_prompt_tokens"]))}}
    inputs = {"oext_eval_settings": {"sha256": settings.sha256}, "oext_record": {"sha256": loaded.record_sha256},
              "oext_bank": {"sha256": loaded.bank_sha256, "items": len(loaded.rows)},
              "shortfall": loaded.shortfall}
    return doc_of("bank", family, recipe_sha, recipe_label, limits, tokenizer, ctx, inputs, checks,
                  all_accepted=checks["phtest"]["generation_prompt"]["refused"] == 0)


# ----- mode: anchor ------------------------------------------------------------------------------------------------


def run_anchor(family: str, recipe_path: Path | None, ctx: Context, prompts: tuple[Path, str], guard: TextGuard, *,
               list_pin: str = ANCHOR_LIST_SHA256, n_prompts: int = ANCHOR_PROMPTS,
               n_harmful: int = ANCHOR_HARMFUL) -> dict:
    from experiments.safety_selection.textproc import encode_generation_prompt
    from scripts import make_anchor_answers as maa

    recipe, recipe_sha, recipe_label, limits = load_recipe(family, recipe_path)
    tokenizer = check_tokenizer(recipe, ctx)
    pinned(prompts[1], list_pin, "the anchor prompt list")
    try:
        doc = maa.read_prompt_list(Path(prompts[0]), list_pin, n_prompts)
    except maa.AnchorJobError as exc:
        raise Refusal(str(exc)) from None
    except (OSError, ValueError) as exc:
        raise Refusal(f"the anchor prompt list cannot be read ({type(exc).__name__})") from None
    rows = doc["prompts"]
    for p in rows:
        guard.add(p["prompt"], p["unsafe_response"])
    harmful = []
    for k, p in enumerate(rows[:n_harmful]):                     # make_anchor_answers.py:118-123, every k counted
        _, failure = maa._encoded(ctx.codec, f"h-{k}", p["prompt"], p["unsafe_response"], recipe)
        if failure is not None:
            harmful.append((k, failure))
    generation = []
    for k, p in enumerate(rows):                                 # make_anchor_answers.py:125-131, every k counted
        try:
            encode_generation_prompt(ctx.codec, p["prompt"], recipe["model"]["max_prompt_tokens"])
        except ValueError as exc:
            generation.append((k, type(exc).__name__))
    checks = {"anchor_prompts": {"harmful_pairs_encode_train": {**_tally(min(n_harmful, len(rows)), harmful),
                                                                "first_refused_index": harmful[0][0] if harmful else None},
                                 "generation_prompt": {**_tally(len(rows), generation),
                                                       "first_refused_index": generation[0][0] if generation else None}}}
    stop = ("harmful_pair" if harmful else "generation_prompt" if generation else None)
    inputs = {"anchor_prompt_list": {"sha256": list_pin, "prompts": len(rows), "harmful": n_harmful}}
    doc_out = doc_of("anchor", family, recipe_sha, recipe_label, limits, tokenizer, ctx, inputs, checks,
                     all_accepted=not harmful and not generation)
    doc_out["anchor"] = {"informational_only": True,
                         "decides": "nothing: the anchor job's own exit and message decide (GXB O6)",
                         "first_check_that_would_refuse": stop,
                         "recipe_query_bank_is_ref": recipe["attribution"].get("query_bank") == "ref"}
    return doc_out


# ----- the record --------------------------------------------------------------------------------------------------


def doc_of(mode: str, family: str, recipe_sha: str, recipe_label: str, limits: Mapping[str, int],
           tokenizer: Mapping[str, str], ctx: Context, inputs: Mapping, checks: Mapping, *, all_accepted: bool) -> dict:
    return {"kind": KIND, "version": 1, "mode": mode, "family": family, "rule": RULE,
            "recipe": {"path": _label(recipe_label), "config_sha256": recipe_sha, **limits},
            "prepared_manifest_sha256": ctx.manifest_sha256, "tokenizer": dict(tokenizer),
            "inputs": inputs, "checks": checks, "all_accepted": all_accepted,
            "provenance": {"script": "scripts/scale78b/encode_count_78b.py",
                           "script_sha256": sha256_bytes(Path(__file__).read_bytes()),
                           "transformers": _version("transformers")}}


def _label(path: str) -> str:
    p = Path(path).resolve()
    try:
        return p.relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return p.name


def _version(name: str) -> str | None:
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return None


def out_ok(out: Path, folders: Iterable[Path]) -> Path:
    """--out is a new file whose folder exists and lies inside none of the given folders, at any depth (by path and by
    directory identity of every ancestor)."""
    out = Path(out).resolve()
    if out.exists() or out.is_symlink():
        raise Refusal(f"--out {out.name} exists: the record is created once")
    parent = out.parent
    if not parent.is_dir():
        raise Refusal("--out's folder does not exist")
    for folder in folders:
        folder = Path(folder).resolve()
        if not folder.exists():
            continue
        for anchor in (parent, *parent.parents):
            if anchor == folder or os.path.samefile(anchor, folder):
                raise Refusal("--out must not lie inside an input's folder (at any depth) or inside the prepared folder")
    return out


def write_once(out: Path, data: bytes) -> str:
    """The record, created once and complete or not at all: the bytes go to a new temporary file in --out's folder,
    which is hard-linked to --out (no overwrite) only after every byte is written and synced; the temporary file is
    removed in every case, so a failed write leaves no partial file."""
    out = Path(out)
    partial = out.with_name(f".{out.name}.{os.getpid()}.partial")
    created = False
    try:
        with open(partial, "xb") as handle:
            created = True
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(partial, out)
    except FileExistsError:
        what = f"--out {out.name} exists: the record is created once" if created else "a partial file of --out exists"
        raise Refusal(what) from None
    except OSError as exc:
        raise Refusal(f"--out cannot be written ({type(exc).__name__})") from None
    finally:
        if created:
            try:
                os.unlink(partial)
            except FileNotFoundError:
                pass
    return sha256_bytes(data)


def summary_lines(doc: Mapping[str, Any]) -> list[str]:
    lines = [f"{doc['family']} {doc['mode']}: recipe {doc['recipe']['config_sha256'][:16]}... "
             f"(max_prompt_tokens {doc['recipe']['max_prompt_tokens']}, max_train_tokens "
             f"{doc['recipe']['max_train_tokens']}); tokenizer {doc['tokenizer']['repo_id']} "
             f"{doc['tokenizer']['revision_prefix']}"]
    for name, entry in doc["checks"].items():
        for kind, tally in entry.items():
            if not isinstance(tally, dict):
                continue
            lines.append(f"  {name} {kind}: {tally['accepted']} of {tally['n']} accepted; refused "
                         f"{json.dumps(tally['refused_by_reason'], sort_keys=True)}"
                         + (f"; refused ids {json.dumps(tally['refused_ids'])}" if tally["refused_ids"] else ""))
    if "anchor" in doc:
        lines.append(f"  informational only (GXB O6); first check that would refuse: "
                     f"{doc['anchor']['first_check_that_would_refuse']}")
    lines.append(f"  all accepted: {doc['all_accepted']}")
    return lines


def main(argv: list[str] | None = None, *, context: Callable[[str, Path], Context] | None = None,
         run_options: Mapping[str, Any] | None = None) -> int:
    """The command line. ``context`` and ``run_options`` are ENGINEERING FIXTURES for tests only (a fake codec, fixture
    pins); the real run uses ``real_context`` and the module's pins."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--bank", action="store_true", help="the 400 sealed PHTest prompts (DES E1)")
    mode.add_argument("--anchor", action="store_true", help="the anchor job's two encode checks (informational)")
    parser.add_argument("--family", required=True, choices=FAMILIES)
    parser.add_argument("--prepared", type=Path, required=True, help="P_F, the family's prepared set folder")
    parser.add_argument("--recipe", type=Path, default=None, help="MAIN_F (default: the family's main recipe path)")
    parser.add_argument("--list", action="append", default=[], help="NAME=PATH:SHA256 (s1, s3_safe, s4_candidates)")
    parser.add_argument("--s-pool-record", default=None, help="PATH:SHA256 (default: the committed record at its pin)")
    parser.add_argument("--oext-record", default=None, help="PATH:SHA256 of the O-ext bank's build record")
    parser.add_argument("--oext-bank", default=None, help="PATH:SHA256 of the O-ext bank file")
    parser.add_argument("--prompts", default=None, help="PATH:SHA256 of the anchor prompt list")
    parser.add_argument("--out", type=Path, required=True, help="the record (a new file)")
    args = parser.parse_args(argv)
    guard = TextGuard()
    options = dict(run_options or {})
    try:
        which = "bank" if args.bank else "anchor" if args.anchor else "lists"
        other = {"lists": (args.oext_record, args.oext_bank, args.prompts),
                 "bank": (args.list or None, args.s_pool_record, args.prompts),
                 "anchor": (args.list or None, args.s_pool_record, args.oext_record, args.oext_bank)}[which]
        if any(v is not None for v in other):
            raise Refusal(f"an option of another mode was given with the {which} mode")
        if which == "lists":
            lists = parse_named(args.list, LIST_CHECKS)
            record = (parse_spec(args.s_pool_record, "--s-pool-record") if args.s_pool_record
                      else (REPO / S_POOL_RECORD[0], S_POOL_RECORD[1]))
            inputs = [p for p, _ in lists.values()] + [record[0]]
        elif which == "bank":
            if not args.oext_record or not args.oext_bank:
                raise Refusal("--bank needs --oext-record and --oext-bank")
            bank, record = parse_spec(args.oext_bank, "--oext-bank"), parse_spec(args.oext_record, "--oext-record")
            inputs = [bank[0], record[0]]
        else:
            if not args.prompts:
                raise Refusal("--anchor needs --prompts")
            prompts = parse_spec(args.prompts, "--prompts")
            inputs = [prompts[0]]
        out = out_ok(args.out, [Path(p).resolve().parent for p in inputs] + [args.prepared])
        ctx = (context or real_context)(args.family, args.prepared)
        if which == "lists":
            doc = run_lists(args.family, args.recipe, ctx, lists, record, guard, **options)
        elif which == "bank":
            doc = run_bank(args.family, args.recipe, ctx, bank, record, guard, **options)
        else:
            doc = run_anchor(args.family, args.recipe, ctx, prompts, guard, **options)
        data = canonical(doc)
        lines = summary_lines(doc)
        if guard.hits(data) or any(guard.hits(line) for line in lines):
            raise Refusal("the record or the printout would hold text: nothing written")
        digest = write_once(out, data)
    except (Exception, SystemExit) as exc:     # every refusal and every other error, a SystemExit included: no text
        print(f"REFUSED: {guard.message(exc)} (nothing written)", file=sys.stderr)
        return EXIT_REFUSED
    for line in lines:
        print(line)
    print(f"wrote {out.name} ({digest})")
    if which == "anchor":
        return EXIT_ALL
    return EXIT_ALL if doc["all_accepted"] else EXIT_SOME


if __name__ == "__main__":
    sys.exit(main())
