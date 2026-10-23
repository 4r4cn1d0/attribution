"""O-ext: the one shared, pinned over-refusal evaluation on the 500-prompt primary O bank (addendum section 11 points
1 and 13; sections 7, 9, 10 and 13; LN-07, LN-12, LN-19, LN-24, LN-33). It lives outside the engine identity and
changes no engine file: theta0, a0, R, every arm (through B15), B10's references and B17's C-lean call this function.

**The bank** is the dev 100 over-refusal prompts of the prepared dev bank plus the PHTest prompts that
scripts/stage1/build_oext.py drew (addendum section 7). The PHTest prompts are read from the build's text file
(oext_bank.json) only by the SHA-256 and byte count that the build's text-free sealed record (oext_record.json) names;
the record itself is pinned by its SHA-256 in the settings, and every prompt must hash to the record's prompt_sha256
in the record's order. A record with fewer than 400 prompts is accepted only when it records the shortfall (LN-24).

**The cap branch** (settings cap.branch): "128", "full" or "pending_w1_18". Section 13: W1-18 runs as the first job of
the first stage-1 pod; the lead then sets the branch and pins W1-18's record (Branch 128 needs a record that passes;
Branch full needs a record that fails, or no record and a written reason). Every run reads the record and checks the
branch against it. Under pending nothing here runs (B10 runs only its certify mode then).

- **Branch 128** (LN-19's route): the caller's dev-100 answers (made at the recipe's generation cap, the Gate A cap)
  are cut to their first 128 new tokens by W1-18's cut and judged again; an answer of at most 128 tokens is its own
  cut answer and keeps the caller's flag (W1-18's rule: one input is judged once). The PHTest prompts are generated
  at a 128-new-token cap.
- **Branch full:** the PHTest prompts are generated at the recipe's generation cap; the dev-100 answers and their
  flags are the caller's (reused). The 128-token cut of both sources is judged and reported as a sensitivity only.

**The cut** is W1-18's (scripts/stage1/limits/overrefusal_checks.py check_one_unit): output_ids[:cut], decoded by the
policy codec with special tokens kept, only for an answer longer than the cut; cut_tokens equals W1-18's
truncation.cap_tokens (checked when the pinned settings load; a test runs W1-18's own code on the same answers). The
binding is by bytes: W1-18's settings file must hash to W1-18's literal and to cap.w1_18.settings_sha256, and W1-18's
module to cap.w1_18.module_sha256; W1-18's engine_x is not compared with the running engine (its settings stay frozen
at X by the W1 manifest, addendum section 15 point 1, while these settings are re-pinned on the engine stage 1 uses,
section 11 point 7), so O-ext runs on engine Y once its own settings are re-pinned.
**The judge** is the session's guard (the engine's scorer, as evaluate_checkpoint uses it) on (the user's own prompt,
the answer), with the recipe's guard_over_limit rule. **The flag** is W1-18's judged_flags: refused = a valid answer
with Refusal Yes; an invalid judge answer counts as not refused and is counted apart. **O** (LN-24) = refused / the
number of prompts, each prompt weighted equally (pooled: 100 + the PHTest count), with the per-source O, the invalid
count, the route per source and the flag-change share per source (full against cut where both forms exist).

**Outputs** (new files beside the engine's 8 evaluation files, in the caller's folder; none may exist before):
oext_generations.jsonl (the PHTest answers, in the engine's generation record format), oext_guard.jsonl (every judge
record of this function, with the judged text), oext_summary.json (text-free: counts, O values, routes, hashes). The
ledger stages oext_generate, oext_guard and oext_guard_cut hold only counts known before any answer exists. The policy's
adapter and train/eval mode are unchanged afterwards and the RNG states are restored.

**LN-14's transfer report** (evaluate_transfer; settings section "transfer"; Branch 128 only, report only; addendum
section 10, ledger X-7): theta0's PHTest prompts are generated once at the recipe's generation cap and judged both full
and cut (W1-18's cut and flag), and W1-18's bar is applied as shares of the PHTest count (transfer.bar.reading). If
theta0 fails the bar, the paper states the cut as a limit for PHTest; the branch never switches. It writes its own
three files (oext_transfer_generations.jsonl, oext_transfer_guard.jsonl, oext_transfer_summary.json) and ledger
stages (oext_transfer_generate, oext_transfer_guard, oext_transfer_guard_cut).

  python -B scripts/stage1_s1/oext_eval.py check [--oext-bank F --oext-record F [--w1-18-record F]]

checks the pinned settings (and W1-18's cut), and with the files the bank, its record and W1-18's record, with no
model ($0); it prints the branch, counts and hashes only. Exit 0: checked; 2: refused.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import (canonical_json, ids_sha256, jsonl_bytes, read_jsonl,  # noqa: E402
                                                 sha256_bytes, sha256_file, write_atomic)
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1.limits import overrefusal_checks as w1_18  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "oext_eval.json"
SETTINGS_SHA256 = "3000811cd4f911a1beb9abcb2b2c2dfd5843629c598d736e315f15918e194639"
SETTINGS_NAME = "oext_eval"
OWNER = "scripts/stage1_s1/oext_eval.py"
SUMMARY_KIND = "stage1 o-ext evaluation"
BRANCHES = ("128", "full", "pending_w1_18")
PENDING = "pending_w1_18"
SOURCES = ("dev100", "phtest")
OUTPUT_FILES = ("oext_generations.jsonl", "oext_guard.jsonl", "oext_summary.json")
GENERATIONS, GUARD, SUMMARY = OUTPUT_FILES
STAGES = ("oext_generate", "oext_guard", "oext_guard_cut")
PHTEST_KIND = "oext_phtest"
CUT_SUFFIX = "#cut"
TOP_KEYS = frozenset({"kind", "name", "version", "owner", "requirement", "engine_x", "labels_sha256", "label_entries",
                      "bank", "cap", "flag", "judge", "routes", "ledger", "outputs", "transfer"})
TRANSFER_FILES = ("oext_transfer_generations.jsonl", "oext_transfer_guard.jsonl", "oext_transfer_summary.json")
TRANSFER_GENERATIONS, TRANSFER_GUARD, TRANSFER_SUMMARY = TRANSFER_FILES
TRANSFER_STAGES = ("oext_transfer_generate", "oext_transfer_guard", "oext_transfer_guard_cut")
TRANSFER_KIND = "stage1 o-ext transfer report"
TRANSFER_ROLE = "transfer_report"

Refusal = s1.Refusal
Flags = dict[str, tuple[bool, bool, Any]]


# ----- settings ---------------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Settings:
    doc: dict
    sha256: str


def _keys(obj: Any, expected: Sequence[str] | frozenset, what: str) -> dict:
    if not isinstance(obj, dict) or set(obj) != set(expected):
        raise Refusal(f"settings {SETTINGS_NAME}: {what} must have exactly the keys {sorted(expected)}")
    return obj


def _text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Refusal(f"settings {SETTINGS_NAME}: {what} must be a non-empty text")
    return value


def _positive(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise Refusal(f"settings {SETTINGS_NAME}: {what} must be a positive integer")
    return value


def _hex64(value: Any, what: str) -> str:
    if not isinstance(value, str) or not s1.HEX64.match(value):
        raise Refusal(f"{what} must be a SHA-256 (64 lowercase hex)")
    return value


def validate_settings(doc: Any) -> dict:
    """The O-ext settings: s1common's check (kind, name, registry entries, engine X), then every section."""
    doc = s1.check_settings(doc, SETTINGS_NAME)
    _keys(doc, TOP_KEYS, "the document")
    if doc["version"] != 1 or doc["owner"] != OWNER or doc["label_entries"] != {}:
        raise Refusal(f"settings {SETTINGS_NAME}: version 1 of this module's, with no seed-label entry (nothing is drawn)")
    for key in ("requirement", "flag", "judge"):
        _text(doc[key], key)
    bank = _keys(doc["bank"], {"dev100", "phtest", "order", "weights", "shortfall_rule"}, "bank")
    dev = _keys(bank["dev100"], {"bank", "kind", "prompts", "rule"}, "bank.dev100")
    if (dev["bank"], dev["kind"]) != ("dev", "overrefusal"):
        raise Refusal(f"settings {SETTINGS_NAME}: the dev part is the dev bank's over-refusal prompts")
    _positive(dev["prompts"], "bank.dev100.prompts")
    ph = _keys(bank["phtest"], {"record_kind", "sealed_kind", "bank_kind", "planned", "record_sha256", "builder",
                                "source", "rule"}, "bank.phtest")
    _positive(ph["planned"], "bank.phtest.planned")
    if ph["record_sha256"] is not None:
        _hex64(ph["record_sha256"], "bank.phtest.record_sha256")
    builder = _keys(ph["builder"], {"script", "settings_sha256"}, "bank.phtest.builder")
    _hex64(builder["settings_sha256"], "bank.phtest.builder.settings_sha256")
    source = _keys(ph["source"], {"dataset", "commit", "sha256"}, "bank.phtest.source")
    _hex64(source["sha256"], "bank.phtest.source.sha256")
    for key in ("record_kind", "sealed_kind", "bank_kind", "rule"):
        _text(ph[key], f"bank.phtest.{key}")
    for key in ("order", "weights", "shortfall_rule"):
        _text(bank[key], f"bank.{key}")
    cap = _keys(doc["cap"], {"branch", "branches", "cut_tokens", "w1_18", "rule", "cut_rule"}, "cap")
    if cap["branch"] not in BRANCHES:
        raise Refusal(f"settings {SETTINGS_NAME}: cap.branch must be one of {list(BRANCHES)}")
    _keys(cap["branches"], BRANCHES, "cap.branches")
    _positive(cap["cut_tokens"], "cap.cut_tokens")
    w = _keys(cap["w1_18"], {"script", "settings_sha256", "module_sha256", "record_kind", "record_sha256",
                             "full_reason"}, "cap.w1_18")
    _hex64(w["settings_sha256"], "cap.w1_18.settings_sha256")
    _hex64(w["module_sha256"], "cap.w1_18.module_sha256")
    record, reason = w["record_sha256"], w["full_reason"]
    if record is not None:
        _hex64(record, "cap.w1_18.record_sha256")
    if cap["branch"] == PENDING and (record is not None or reason is not None):
        raise Refusal(f"settings {SETTINGS_NAME}: a pending branch names no W1-18 record and no reason")
    if cap["branch"] == "128" and (record is None or reason is not None):
        raise Refusal(f"settings {SETTINGS_NAME}: Branch 128 needs W1-18's record (a pass) and no full_reason")
    if cap["branch"] == "full" and (record is None) == (reason is None):
        raise Refusal(f"settings {SETTINGS_NAME}: Branch full names W1-18's record (a fail) or, when W1-18 could "
                      "not run, a full_reason, and not both")
    if reason is not None:
        _text(reason, "cap.w1_18.full_reason")
    for key in ("rule", "cut_rule"):
        _text(cap[key], f"cap.{key}")
    routes = _keys(doc["routes"], {"128", "full", "sensitivity_full"}, "routes")
    for branch in ("128", "full"):
        for name, text in _keys(routes[branch], SOURCES, f"routes.{branch}").items():
            _text(text, f"routes.{branch}.{name}")
    _text(routes["sensitivity_full"], "routes.sensitivity_full")
    ledger = _keys(doc["ledger"], {"stages", "rule"}, "ledger")
    outputs = _keys(doc["outputs"], {"files", "rule"}, "outputs")
    if ledger["stages"] != list(STAGES) or outputs["files"] != list(OUTPUT_FILES):
        raise Refusal(f"settings {SETTINGS_NAME}: the ledger stages and the output files are this module's")
    transfer = _keys(doc["transfer"], {"rule", "branch", "unit", "bar", "stages", "files"}, "transfer")
    for key in ("rule", "unit"):
        _text(transfer[key], f"transfer.{key}")
    if transfer["branch"] != "128":
        raise Refusal(f"settings {SETTINGS_NAME}: LN-14's transfer report runs under Branch 128 only")
    bar = _keys(transfer["bar"], {"min_flags_agree", "max_count_move", "per_prompts", "reading"}, "transfer.bar")
    _positive(bar["per_prompts"], "transfer.bar.per_prompts")
    _positive(bar["min_flags_agree"], "transfer.bar.min_flags_agree")
    if isinstance(bar["max_count_move"], bool) or not isinstance(bar["max_count_move"], int) or bar["max_count_move"] < 0:
        raise Refusal(f"settings {SETTINGS_NAME}: transfer.bar.max_count_move must be a non-negative integer")
    if bar["min_flags_agree"] > bar["per_prompts"]:
        raise Refusal(f"settings {SETTINGS_NAME}: transfer.bar.min_flags_agree is above per_prompts")
    _text(bar["reading"], "transfer.bar.reading")
    if transfer["stages"] != list(TRANSFER_STAGES) or transfer["files"] != list(TRANSFER_FILES):
        raise Refusal(f"settings {SETTINGS_NAME}: the transfer report's ledger stages and files are this module's")
    return doc


def settings_from_doc(doc: Any) -> Settings:
    """A validated settings document named by the SHA-256 of its canonical bytes (tests and fixtures)."""
    return Settings(validate_settings(doc), sha256_bytes(canonical_json(doc)))


def check_w1_18_binding(doc: Mapping[str, Any]) -> dict:
    """The cut is W1-18's, bound by bytes: W1-18's settings file hashes to W1-18's own literal and to the SHA-256 these
    settings name, is W1-18's settings document (kind and name), and its truncation.cap_tokens equals cap.cut_tokens
    (and its bar equals transfer.bar, LN-14); W1-18's module hashes to cap.w1_18.module_sha256 (its judged_flags is
    O-ext's flag rule). W1-18's engine_x is NOT checked against the running engine: W1-18's settings are frozen at
    engine X by the W1 manifest (addendum section 15 point 1) and are never re-pinned, while O-ext's own settings are
    re-pinned on the engine stage 1 uses (section 11 point 7), so an engine check here would refuse every O-ext run on
    engine Y (c0 on the certificate pod). Returns W1-18's truncation block."""
    pin = doc["cap"]["w1_18"]
    data = _read(w1_18.SETTINGS_PATH, "W1-18's settings")
    digest = sha256_bytes(data)
    if digest != w1_18.SETTINGS_SHA256 or digest != pin["settings_sha256"]:
        raise Refusal(f"settings {SETTINGS_NAME}: W1-18's settings are {digest}, these settings name "
                      f"{pin['settings_sha256']} and W1-18 pins {w1_18.SETTINGS_SHA256}")
    w_doc = s1.strict_json(data)
    if not isinstance(w_doc, dict) or (w_doc.get("kind"), w_doc.get("name")) != (s1.SETTINGS_KIND, w1_18.SETTINGS_NAME):
        raise Refusal(f"settings {SETTINGS_NAME}: W1-18's settings file is not W1-18's settings document")
    module = sha256_file(Path(w1_18.__file__).resolve())
    if module != pin["module_sha256"]:
        raise Refusal(f"settings {SETTINGS_NAME}: W1-18's module is {module}, these settings pin {pin['module_sha256']}")
    if w_doc["truncation"]["cap_tokens"] != doc["cap"]["cut_tokens"]:
        raise Refusal(f"settings {SETTINGS_NAME}: the cut ({doc['cap']['cut_tokens']} tokens) is not W1-18's "
                      f"({w_doc['truncation']['cap_tokens']})")
    bar = doc["transfer"]["bar"]
    if (bar["min_flags_agree"], bar["max_count_move"], bar["per_prompts"]) != (
            w_doc["truncation"]["min_flags_agree"], w_doc["truncation"]["max_count_move"],
            doc["bank"]["dev100"]["prompts"]):
        raise Refusal(f"settings {SETTINGS_NAME}: the LN-14 bar is not W1-18's bar per {doc['bank']['dev100']['prompts']} "
                      "prompts")
    return w_doc["truncation"]


def load_pinned_settings(path: str | Path = SETTINGS_PATH, expected_sha256: str | None = None) -> Settings:
    """The pinned settings (SETTINGS_PATH hashing to SETTINGS_SHA256), validated and bound to W1-18's cut."""
    doc, digest = s1.load_settings(path, expected_sha256 or SETTINGS_SHA256, SETTINGS_NAME)
    validate_settings(doc)
    check_w1_18_binding(doc)
    return Settings(doc, digest)


def module_sha256() -> str:
    """The SHA-256 of this module's file (what B10's and B17's settings pin)."""
    return sha256_file(Path(__file__).resolve())


# ----- inputs (no model) ------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Bank:
    rows: tuple                      # ((PHTest id, prompt), ...) in the record's sealed order
    record_sha256: str
    bank_sha256: str
    planned: int
    shortfall: Any


@dataclasses.dataclass(frozen=True)
class W118:
    record_sha256: str | None
    passed: bool | None
    full_reason: str | None
    units: int


@dataclasses.dataclass(frozen=True)
class Prepared:
    settings: Settings
    branch: str
    bank: Bank | None
    w1_18: W118 | None

    @property
    def runs(self) -> bool:
        return self.branch != PENDING


def _read(path: Any, what: str) -> bytes:
    try:
        return Path(path).read_bytes()
    except (OSError, TypeError):
        raise Refusal(f"{what} cannot be read") from None


def load_bank(settings: Settings, bank_path: str | Path, record_path: str | Path) -> Bank:
    """The PHTest part of the bank: the pinned build record, then the text file it names (SHA-256 and bytes), each
    prompt checked against the record's prompt_sha256 in the record's order. Counts and hashes only in messages."""
    spec = settings.doc["bank"]["phtest"]
    pin = spec["record_sha256"]
    if pin is None:
        raise Refusal("the O-ext bank record is not pinned yet (settings bank.phtest.record_sha256 is null: the lead "
                      "runs build_oext.py on the real files first)")
    data = _read(record_path, "the O-ext bank record")
    if sha256_bytes(data) != pin:
        raise Refusal(f"the O-ext bank record hashes to {sha256_bytes(data)}, the settings pin {pin}")
    record = s1.strict_json(data)
    if not isinstance(record, dict) or (record.get("kind"), record.get("version")) != (spec["record_kind"], 1):
        raise Refusal("the O-ext bank record is not build_oext's record")
    if (record.get("provenance") or {}).get("settings_sha256") != spec["builder"]["settings_sha256"]:
        raise Refusal("the O-ext bank record was not made under the pinned build_oext settings")
    sealed = record.get("bank")
    if not isinstance(sealed, dict) or (sealed.get("kind"), sealed.get("version")) != (spec["sealed_kind"], 1):
        raise Refusal("the O-ext bank record holds no sealed bank record")
    items = sealed.get("items")
    if not isinstance(items, list) or not items:
        raise Refusal("the O-ext bank record lists no prompt")
    n, planned, shortfall = len(items), spec["planned"], record.get("shortfall")
    if sealed.get("n_items") != n or record.get("bank_size") != n:
        raise Refusal("the O-ext bank record's counts disagree")
    if n == planned:
        if shortfall is not None:
            raise Refusal("the O-ext bank record holds the planned count and a shortfall")
    elif n > planned or not isinstance(shortfall, dict) or (shortfall.get("eligible"), shortfall.get("planned")) != (
            n, planned):
        raise Refusal(f"the O-ext bank holds {n} prompts, the settings plan {planned}, and the record names no "
                      "matching shortfall (LN-24)")
    full = sealed.get("full_file") or {}
    text = _read(bank_path, "the O-ext bank file")
    if sha256_bytes(text) != full.get("sha256") or len(text) != full.get("bytes"):
        raise Refusal("the O-ext bank file is not the file the record names (SHA-256 or byte count)")
    bank = s1.strict_json(text)
    if not isinstance(bank, dict) or (bank.get("kind"), bank.get("version")) != (spec["bank_kind"], 1):
        raise Refusal("the O-ext bank file is not build_oext's bank")
    if bank.get("source") != spec["source"]:
        raise Refusal("the O-ext bank file names another PHTest source than the settings")
    rows = bank.get("items")
    if not isinstance(rows, list) or len(rows) != n:
        raise Refusal("the O-ext bank file and its record list different numbers of prompts")
    out = []
    for position, (row, entry) in enumerate(zip(rows, items)):
        if not isinstance(row, dict) or set(row) != {"id", "prompt"} or not isinstance(entry, dict):
            raise Refusal(f"O-ext bank row {position} is not an id and a prompt")
        pid, prompt = row["id"], row["prompt"]
        if not isinstance(pid, str) or s1.SAFE_VALUE.match(pid) is None or pid != entry.get("id"):
            raise Refusal(f"O-ext bank row {position}'s id is not the record's")
        if not isinstance(prompt, str) or not prompt.strip():
            raise Refusal(f"O-ext bank row {position} holds no prompt")
        if sha256_bytes(prompt.encode("utf-8")) != entry.get("prompt_sha256"):
            raise Refusal(f"O-ext bank row {position}'s prompt does not hash to the record's prompt_sha256")
        out.append((pid, prompt))
    if len({pid for pid, _ in out}) != n:
        raise Refusal("the O-ext bank's ids are not distinct")
    return Bank(tuple(out), pin, sha256_bytes(text), planned, shortfall)


def read_w1_18(settings: Settings, path: str | Path | None) -> W118:
    """W1-18's record, pinned by the settings, checked against the branch: Branch 128 needs a passing record, Branch
    full a failing one (or no record and a written reason); every unit's cut is the settings' cut."""
    cap = settings.doc["cap"]
    spec, branch = cap["w1_18"], cap["branch"]
    if spec["record_sha256"] is None:
        if path is not None:
            raise Refusal("the settings pin no W1-18 record, so none is read")
        return W118(None, None, spec["full_reason"], 0)
    data = _read(path, "W1-18's record")
    if sha256_bytes(data) != spec["record_sha256"]:
        raise Refusal(f"W1-18's record hashes to {sha256_bytes(data)}, the settings pin {spec['record_sha256']}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or (doc.get("kind"), doc.get("version")) != (spec["record_kind"], 1):
        raise Refusal("W1-18's record is not an over-refusal checks record")
    if (doc.get("provenance") or {}).get("settings_sha256") != spec["settings_sha256"]:
        raise Refusal("W1-18's record was not made under the pinned W1-18 settings")
    passed = (doc.get("truncation_check") or {}).get("pass")
    units = doc.get("units")
    if not isinstance(passed, bool) or not isinstance(units, dict) or not units:
        raise Refusal("W1-18's record holds no truncation verdict or no unit")
    if any(((u or {}).get("truncation") or {}).get("cap_tokens") != cap["cut_tokens"] for u in units.values()):
        raise Refusal("W1-18's record checked another cut than the settings' cut_tokens")
    if passed != (branch == "128"):
        raise Refusal(f"W1-18's record {'passes' if passed else 'fails'} its bar, so the branch is "
                      f"{'128' if passed else 'full'}, not {branch}")
    return W118(spec["record_sha256"], passed, None, len(units))


def prepare(settings: Settings, *, bank_path: str | Path | None = None, record_path: str | Path | None = None,
            w1_18_path: str | Path | None = None) -> Prepared:
    """Everything O-ext needs that loads no model, checked before any folder. Under the pending branch nothing runs,
    so it takes no input; otherwise the bank file, its record and (when pinned) W1-18's record are required."""
    branch = settings.doc["cap"]["branch"]
    if branch == PENDING:
        if any(p is not None for p in (bank_path, record_path, w1_18_path)):
            raise Refusal("the cap branch is pending W1-18 (section 13): O-ext does not run, so it takes no input")
        return Prepared(settings, branch, None, None)
    if bank_path is None or record_path is None:
        raise Refusal(f"Branch {branch}: O-ext needs the bank file and its record")
    w = read_w1_18(settings, w1_18_path)
    return Prepared(settings, branch, load_bank(settings, bank_path, record_path), w)


# ----- the dev 100 answers ----------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Answer:
    prompt_id: str
    prompt: str
    output_ids: tuple
    text: str
    guard: Mapping[str, Any]         # the caller's judge record of this answer (valid, refusal)


def dev_answers(items: Sequence[Mapping], generations: Sequence[Mapping], guards: Sequence[Mapping]) -> list[Answer]:
    """The caller's dev-100 answers in bank order: each over-refusal item (the user's own prompt) with its greedy
    answer and its judge record; both lists hold exactly these prompts once each."""
    def by_id(rows: Sequence[Mapping], what: str) -> dict:
        out = {}
        for row in rows:
            pid = row.get("prompt_id")
            if not isinstance(pid, str) or pid in out:
                raise Refusal(f"the dev answers' {what} repeat a prompt or have no prompt id")
            out[pid] = row
        return out

    want = [item["prompt_id"] for item in items]
    gen, guard = by_id(generations, "generations"), by_id(guards, "judge records")
    if len(set(want)) != len(want) or set(gen) != set(want) or set(guard) != set(want):
        raise Refusal("the dev answers are not exactly the dev bank's over-refusal prompts")
    out = []
    for item in items:
        record = gen[item["prompt_id"]]
        ids, text = record.get("output_ids"), record.get("text")
        if not isinstance(ids, (list, tuple)) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
            raise Refusal(f"dev answer {item['prompt_id']} has no token ids")
        if not isinstance(text, str) or not isinstance(item.get("prompt"), str):
            raise Refusal(f"dev answer {item['prompt_id']} has no text or no prompt")
        out.append(Answer(item["prompt_id"], item["prompt"], tuple(ids), text, dict(guard[item["prompt_id"]])))
    return out


def dev_answers_from_eval(folder: str | Path, items: Sequence[Mapping]) -> tuple[list[Answer], dict[str, str]]:
    """The engine's dev-100 answers from an evaluation folder (generations.jsonl and guard.jsonl, kind overrefusal),
    and the two files' SHA-256 (for the summary's provenance)."""
    folder = Path(folder)
    dev = [i for i in items if i["kind"] == "overrefusal"]
    gens = [r for r in read_jsonl(folder / "generations.jsonl") if r.get("kind") == "overrefusal"]
    guards = [r for r in read_jsonl(folder / "guard.jsonl") if r.get("kind") == "overrefusal"]
    return dev_answers(dev, gens, guards), {"dev100/generations.jsonl": sha256_file(folder / "generations.jsonl"),
                                            "dev100/guard.jsonl": sha256_file(folder / "guard.jsonl")}


# ----- the rules (no model) ---------------------------------------------------------------------------------------


def cut_text(decode: Callable[[Sequence[int]], str], output_ids: Sequence[int], cut: int) -> str | None:
    """W1-18's cut: the first ``cut`` output ids decoded, only for an answer longer than ``cut`` (None: the answer is
    its own cut answer and keeps its full flag)."""
    ids = list(output_ids)
    return decode(ids[:cut]) if len(ids) > cut else None


def judge(score: Callable[[list], list], items: list[tuple[str, str, str]]) -> tuple[Flags, list[dict]]:
    """(item id -> W1-18's flag (refused, valid, refusal), the judge's records) for (item id, prompt, text) items."""
    records: list[dict] = []

    def recording(batch: list) -> list:
        out = score(batch)
        records.extend(out)
        return out

    return (w1_18.judged_flags(recording, items) if items else {}), records


def stored_flags(answers: Sequence[Answer]) -> Flags:
    """W1-18's flag of each answer's stored judge record (the caller's own judgment, reused)."""
    stored = {a.prompt_id: a.guard for a in answers}
    return w1_18.judged_flags(lambda items: [stored[i] for i, _, _ in items],
                              [(a.prompt_id, a.prompt, a.text) for a in answers])


def o_block(flags: Mapping[str, tuple], ids: Sequence[str]) -> dict:
    """Equal weight per prompt (LN-24): refused / the number of prompts; an invalid judge answer is not refused."""
    refused = sum(bool(flags[i][0]) for i in ids)
    return {"prompts": len(ids), "refused": refused, "invalid": sum(not flags[i][1] for i in ids),
            "o": refused / len(ids) if ids else None}


def o_table(dev: Mapping[str, tuple], dev_ids: Sequence[str], ph: Mapping[str, tuple], ph_ids: Sequence[str]) -> dict:
    both = {**dev, **ph}
    return {"pooled": o_block(both, [*dev_ids, *ph_ids]),
            "by_source": {"dev100": o_block(dev, dev_ids), "phtest": o_block(ph, ph_ids)}}


def flag_change(full: Mapping[str, tuple] | None, cut: Mapping[str, tuple], ids: Sequence[str]) -> dict:
    """Full against cut flags where both forms exist (full None: no full answer exists, as for PHTest at the 128
    cap). share = changed / the prompts with both forms."""
    if full is None:
        return {"prompts_with_both_forms": 0, "changed": 0, "share": None, "became_refused": 0,
                "became_not_refused": 0, "note": "generated at the cut cap: no full answer exists"}
    changed = [i for i in ids if bool(full[i][0]) != bool(cut[i][0])]
    return {"prompts_with_both_forms": len(ids), "changed": len(changed),
            "share": len(changed) / len(ids) if ids else None,
            "became_refused": sum(bool(cut[i][0]) for i in changed),
            "became_not_refused": sum(bool(full[i][0]) for i in changed), "note": None}


# ----- the evaluation ---------------------------------------------------------------------------------------------


def _caps(recipe: Mapping[str, Any], doc: Mapping[str, Any]) -> tuple[Mapping[str, Any], int, int]:
    """(the recipe's generation block, its generation cap, the cut); the cap may not be below the cut."""
    gen = recipe["generation"]
    full_cap, cut = gen["max_new_tokens"], doc["cap"]["cut_tokens"]
    if full_cap < cut:
        raise Refusal(f"the recipe's generation cap ({full_cap}) is below the cut ({cut})")
    return gen, full_cap, cut


def _encode(codec: Any, rows: Sequence[tuple], recipe: Mapping[str, Any]) -> list:
    """The PHTest prompts encoded under the recipe's prompt limit; any prompt that does not encode refuses (counts)."""
    from experiments.safety_selection.textproc import encode_generation_prompt

    max_prompt = recipe["model"]["max_prompt_tokens"]
    prompts, too_long = [], Counter()
    for _, text in rows:
        try:
            prompts.append(encode_generation_prompt(codec, text, max_prompt))
        except ValueError as exc:                    # TooLong and the control-token error are ValueErrors
            too_long[type(exc).__name__] += 1
    if too_long:
        raise Refusal(f"{sum(too_long.values())} PHTest prompts do not encode under the recipe's limit "
                      f"({dict(sorted(too_long.items()))})")
    return prompts


@dataclasses.dataclass(frozen=True)
class _Pass:
    records: list                    # the PHTest generation records
    ph_flags: Flags
    ph_records: list
    cut_items: list                  # (item id + CUT_SUFFIX, prompt, cut text)
    cut_meta: list                   # (prompt id, source)
    cut_flags: Flags
    cut_records: list
    guard: Any
    over: dict
    fingerprint: str
    device: str


def _phtest_pass(*, session: Any, policy: Any, codec: Any, ledger: Any, run_dir: str | Path, checkpoint: str,
                 rows: Sequence[tuple], prompts: Sequence[list], ph_cap: int, cut: int, cut_dev: Sequence[Answer],
                 cut_phtest: bool, stages: Sequence[str]) -> _Pass:
    """The model part shared by O-ext and LN-14's transfer report: the PHTest prompts generated greedily at ``ph_cap``
    and judged; then the cut (W1-18's) of the ``cut_dev`` answers and, with ``cut_phtest``, of the PHTest answers,
    judged again. The guard runs with the recipe's guard_over_limit rule; the RNG states are restored and the policy's
    adapter and train/eval mode must be unchanged afterwards. ``stages`` names the three ledger stages."""
    from experiments.safety_selection import engine as en
    from experiments.safety_selection.textproc import repeated_ngram_fraction

    gen = session.recipe["generation"]
    over = {"over_limit_unscored": True} if gen.get("guard_over_limit") == "unscored" else {}
    device = policy.device
    before = (en.lora_fingerprint(policy.named), policy.model.training)
    with en.preserved_rng(device):
        guard = session.guard(ledger, Path(run_dir))

        def score(items: list) -> list:
            return guard.score(items, check=lambda what: ledger.check(f"oext guard {checkpoint} {what}"), **over)

        def on_batch(b: int, index: list[int], batch: list) -> None:
            ledger.progress(stages[0], checkpoint=checkpoint, batch=b, rows=len(index))

        with ledger.stage(stages[0], checkpoint=checkpoint, prompts=len(prompts),
                          prompt_tokens=sum(map(len, prompts)), max_new_tokens=ph_cap):
            generations = en.greedy_generate(
                policy.model, prompts, max_new_tokens=ph_cap, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                device=device, batch_size=gen["batch_size"],
                check=lambda what: ledger.check(f"oext generate {checkpoint} {what}"), on_batch=on_batch)
        records = [{"prompt_id": pid, "kind": PHTEST_KIND, "prompt_ids": ids, "prompt_tokens": len(ids),
                    "output_ids": list(g.output_ids), "output_tokens": len(g.output_ids), "stop_reason": g.stop_reason,
                    "stop_token": g.stop_token, "empty": not g.output_ids, "text": codec.decode(g.output_ids),
                    "repetition_4gram": repeated_ngram_fraction(g.output_ids, 4), "max_new_tokens": ph_cap}
                   for (pid, _), ids, g in zip(rows, prompts, generations, strict=True)]
        ph_items = [(r["prompt_id"], text, r["text"]) for r, (_, text) in zip(records, rows)]
        with ledger.stage(stages[1], checkpoint=checkpoint, items=len(ph_items)):
            ph_flags, ph_records = judge(score, ph_items)
        cut_items, cut_meta = [], []
        sources = [("dev100", [(a.prompt_id, a.prompt, a.output_ids) for a in cut_dev])]
        if cut_phtest:
            sources.append(("phtest", [(r["prompt_id"], text, r["output_ids"]) for r, (_, text) in zip(records, rows)]))
        for source, answers in sources:
            for pid, prompt, ids in answers:
                text = cut_text(codec.decode, ids, cut)
                if text is not None:
                    cut_items.append((pid + CUT_SUFFIX, prompt, text))
                    cut_meta.append((pid, source))
        with ledger.stage(stages[2], checkpoint=checkpoint):
            cut_flags, cut_records = judge(score, cut_items)
    if (en.lora_fingerprint(policy.named), policy.model.training) != before:
        raise RuntimeError("O-ext changed the adapter or the train/eval mode")
    return _Pass(records, ph_flags, ph_records, cut_items, cut_meta, cut_flags, cut_records, guard, over, before[0],
                 device)


def _guard_rows(p: _Pass, rows: Sequence[tuple], answer_role: str, cut_role: str, cut: int) -> list[dict]:
    """Every judge record of a pass with its judged text: the PHTest answers, then the cut answers."""
    out = [{**rec, "prompt_id": pid, "source": "phtest", "form": "answer", "role": answer_role,
            "judged_tokens": r["output_tokens"], "text": r["text"]}
           for r, rec, (pid, _) in zip(p.records, p.ph_records, rows, strict=True)]
    out += [{**rec, "prompt_id": pid, "source": source, "form": "cut", "role": cut_role, "judged_tokens": cut,
             "text": text} for rec, (pid, source), (_, _, text) in zip(p.cut_records, p.cut_meta, p.cut_items,
                                                                        strict=True)]
    return out


def _bank_block(bank: Bank, dev_ids: Sequence[str], ph_ids: Sequence[str], prompts: Sequence[list],
                doc: Mapping[str, Any]) -> dict:
    return {"prompts": len(dev_ids) + len(ph_ids), "dev100": len(dev_ids), "phtest": len(ph_ids),
            "phtest_planned": bank.planned, "shortfall": bank.shortfall, "record_sha256": bank.record_sha256,
            "bank_sha256": bank.bank_sha256,
            "phtest_prompt_tokens_sha256": sha256_bytes(canonical_json(
                [[pid, ids_sha256(ids)] for pid, ids in zip(ph_ids, prompts)])),
            "order": doc["bank"]["order"]}


def _judge_block(p: _Pass, doc: Mapping[str, Any], judged: dict) -> dict:
    return {"device": p.device, "over_limit_unscored": bool(p.over), "flag": doc["flag"],
            "guard_identity_sha256": sha256_bytes(canonical_json(getattr(p.guard, "identity", None))),
            "judged_items": judged}


def _w1_18_inputs(prepared: Prepared) -> dict:
    """W1-18's module (O-ext's flag rule, pinned) and, when pinned, W1-18's record, for the provenance."""
    out = {"w1_18_module": sha256_file(Path(w1_18.__file__).resolve())}
    if prepared.w1_18 is not None and prepared.w1_18.record_sha256 is not None:
        out["w1_18_record"] = prepared.w1_18.record_sha256
    return out


def evaluate_oext(*, session: Any, policy: Any, codec: Any, ledger: Any, run_dir: str | Path, folder: str | Path,
                  prepared: Prepared, dev: Sequence[Answer], dev_inputs: Mapping[str, str], checkpoint: str) -> dict:
    """O-ext of the policy's current state (module doc). ``codec`` encodes the PHTest prompts (the policy codec, or
    B10's prefix codec) and decodes every answer; ``dev`` are the caller's dev-100 answers at the recipe's cap with
    their judge records; ``dev_inputs`` names their files' SHA-256. Writes the three output files into ``folder`` and
    returns the summary."""
    from experiments.safety_selection import engine as en

    if not prepared.runs or prepared.bank is None:
        raise Refusal("O-ext does not run under the pending branch (section 13)")
    settings, branch, bank = prepared.settings, prepared.branch, prepared.bank
    doc, recipe = settings.doc, session.recipe
    _, full_cap, cut = _caps(recipe, doc)
    ph_cap = cut if branch == "128" else full_cap
    folder = Path(folder)
    if any((folder / name).exists() for name in OUTPUT_FILES):
        raise Refusal("an O-ext output file exists already: nothing is overwritten")
    dev = list(dev)
    dev_ids = [a.prompt_id for a in dev]
    if len(dev) != doc["bank"]["dev100"]["prompts"] or len(set(dev_ids)) != len(dev_ids):
        raise Refusal(f"O-ext needs {doc['bank']['dev100']['prompts']} distinct dev answers, it has {len(dev)}")
    for a in dev:
        if len(a.output_ids) > full_cap:
            raise Refusal(f"dev answer {a.prompt_id} is longer than the recipe's generation cap")
        if codec.decode(a.output_ids) != a.text:
            raise Refusal(f"dev answer {a.prompt_id}'s text is not the decode of its token ids")
    rows = list(bank.rows)
    ph_ids = [pid for pid, _ in rows]
    if set(ph_ids) & set(dev_ids):
        raise Refusal("a PHTest id is also a dev prompt id")
    prompts = _encode(codec, rows, recipe)
    p = _phtest_pass(session=session, policy=policy, codec=codec, ledger=ledger, run_dir=run_dir,
                     checkpoint=checkpoint, rows=rows, prompts=prompts, ph_cap=ph_cap, cut=cut, cut_dev=dev,
                     cut_phtest=branch == "full", stages=STAGES)
    records, ph_flags, cut_meta, cut_flags = p.records, p.ph_flags, p.cut_meta, p.cut_flags
    dev_full = stored_flags(dev)
    longer = {pid for pid, _ in cut_meta}

    def cut_of(full: Mapping[str, tuple], ids: Sequence[str]) -> Flags:
        return {i: cut_flags[i + CUT_SUFFIX] if i in longer else full[i] for i in ids}

    dev_cut = cut_of(dev_full, dev_ids)
    sensitivity = None
    if branch == "128":
        primary = o_table(dev_cut, dev_ids, ph_flags, ph_ids)
        changes = {"dev100": flag_change(dev_full, dev_cut, dev_ids), "phtest": flag_change(None, ph_flags, ph_ids)}
    else:
        primary = o_table(dev_full, dev_ids, ph_flags, ph_ids)
        ph_cut = cut_of(ph_flags, ph_ids)
        changes = {"dev100": flag_change(dev_full, dev_cut, dev_ids), "phtest": flag_change(ph_flags, ph_cut, ph_ids)}
        sensitivity = {"rule": doc["routes"]["sensitivity_full"], "o": o_table(dev_cut, dev_ids, ph_cut, ph_ids)}
    role = "primary" if branch == "128" else "sensitivity"
    guard_rows = _guard_rows(p, rows, "primary", role, cut)
    gen_bytes, guard_bytes = jsonl_bytes(records), jsonl_bytes(guard_rows)
    write_atomic(folder / GENERATIONS, gen_bytes)
    write_atomic(folder / GUARD, guard_bytes)
    inputs = {"oext_record": bank.record_sha256, "oext_bank": bank.bank_sha256, **dict(dev_inputs),
              GENERATIONS: sha256_bytes(gen_bytes), GUARD: sha256_bytes(guard_bytes), **_w1_18_inputs(prepared)}
    summary = {
        "kind": SUMMARY_KIND, "version": 1, "checkpoint": checkpoint, "branch": branch,
        "cap": {"cut_tokens": cut, "dev100_answers_max_new_tokens": full_cap, "phtest_max_new_tokens": ph_cap},
        "route": dict(doc["routes"][branch]),
        "bank": _bank_block(bank, dev_ids, ph_ids, prompts, doc),
        "weights": doc["bank"]["weights"],
        "o": primary,
        "flag_change": changes,
        "sensitivity_cut": sensitivity,
        "answers": {"dev100": {"answers": len(dev_ids), "longer_than_cut": sum(s == "dev100" for _, s in cut_meta)},
                    "phtest": {"answers": len(records), "output_tokens": sum(r["output_tokens"] for r in records),
                               "capped": sum(r["stop_reason"] == en.STOP_CAP for r in records),
                               "empty": sum(r["empty"] for r in records),
                               "longer_than_cut": sum(s == "phtest" for _, s in cut_meta)}},
        "judge": _judge_block(p, doc, {"phtest_answers": len(records), "cut_answers": len(p.cut_items)}),
        "w1_18": None if prepared.w1_18 is None else dataclasses.asdict(prepared.w1_18),
        "adapter_fingerprint": p.fingerprint,
        "files": {GENERATIONS: sha256_bytes(gen_bytes), GUARD: sha256_bytes(guard_bytes)},
        "provenance": s1.provenance(Path(__file__).resolve(), settings.sha256, inputs, {}),
    }
    write_atomic(folder / SUMMARY, canonical_json(summary))
    return summary


def transfer_bar(full: Mapping[str, tuple], cut: Mapping[str, tuple], ids: Sequence[str],
                 bar: Mapping[str, Any]) -> dict:
    """LN-14: W1-18's bar on the PHTest flags, full against cut, read as shares of the n prompts (settings
    transfer.bar.reading): 100 x agree >= min_flags_agree x n and 100 x move <= max_count_move x n (per = 100);
    integers only. An invalid judge answer counts as not refused (W1-18's flag)."""
    n, per = len(ids), bar["per_prompts"]
    agree = sum(bool(full[i][0]) == bool(cut[i][0]) for i in ids)
    refused_full, refused_cut = sum(bool(full[i][0]) for i in ids), sum(bool(cut[i][0]) for i in ids)
    move = abs(refused_full - refused_cut)
    return {"prompts": n, "flags_agree": agree, "refused_full": refused_full, "refused_cut": refused_cut,
            "count_move": move, "invalid_full": sum(not full[i][1] for i in ids),
            "invalid_cut": sum(not cut[i][1] for i in ids),
            "bar": {"min_flags_agree": bar["min_flags_agree"], "max_count_move": bar["max_count_move"],
                    "per_prompts": per},
            "pass": per * agree >= bar["min_flags_agree"] * n and per * move <= bar["max_count_move"] * n}


def evaluate_transfer(*, session: Any, policy: Any, codec: Any, ledger: Any, run_dir: str | Path, folder: str | Path,
                      prepared: Prepared, checkpoint: str) -> dict:
    """LN-14's pre-set transfer report (settings section "transfer"; Branch 128 only; report only): the PHTest prompts
    generated once at the recipe's generation cap and judged both full and cut (W1-18's cut and flag; an answer of at
    most cut_tokens tokens is its own cut answer), with W1-18's bar (transfer_bar). The caller is theta0's evaluation
    (B15 J4, folded into J3-theta0); the unit is named by the settings. Writes the three transfer files (their own
    names, beside any O-ext or engine file) and returns the summary. It never changes the branch."""
    from experiments.safety_selection import engine as en

    if prepared.branch != "128" or prepared.bank is None or prepared.w1_18 is None or prepared.w1_18.passed is not True:
        raise Refusal("LN-14's transfer report runs under Branch 128 only (a passing W1-18 record)")
    settings, bank = prepared.settings, prepared.bank
    doc = settings.doc
    _, full_cap, cut = _caps(session.recipe, doc)
    folder = Path(folder)
    if any((folder / name).exists() for name in TRANSFER_FILES):
        raise Refusal("an LN-14 transfer output file exists already: nothing is overwritten")
    rows = list(bank.rows)
    ph_ids = [pid for pid, _ in rows]
    prompts = _encode(codec, rows, session.recipe)
    p = _phtest_pass(session=session, policy=policy, codec=codec, ledger=ledger, run_dir=run_dir,
                     checkpoint=checkpoint, rows=rows, prompts=prompts, ph_cap=full_cap, cut=cut, cut_dev=(),
                     cut_phtest=True, stages=TRANSFER_STAGES)
    longer = {pid for pid, _ in p.cut_meta}
    cut_flags = {i: p.cut_flags[i + CUT_SUFFIX] if i in longer else p.ph_flags[i] for i in ph_ids}
    guard_rows = _guard_rows(p, rows, TRANSFER_ROLE, TRANSFER_ROLE, cut)
    gen_bytes, guard_bytes = jsonl_bytes(p.records), jsonl_bytes(guard_rows)
    write_atomic(folder / TRANSFER_GENERATIONS, gen_bytes)
    write_atomic(folder / TRANSFER_GUARD, guard_bytes)
    inputs = {"oext_record": bank.record_sha256, "oext_bank": bank.bank_sha256,
              TRANSFER_GENERATIONS: sha256_bytes(gen_bytes), TRANSFER_GUARD: sha256_bytes(guard_bytes),
              **_w1_18_inputs(prepared)}
    summary = {
        "kind": TRANSFER_KIND, "version": 1, "checkpoint": checkpoint, "branch": prepared.branch,
        "role": TRANSFER_ROLE, "unit": doc["transfer"]["unit"], "rule": doc["transfer"]["rule"],
        "cap": {"cut_tokens": cut, "phtest_max_new_tokens": full_cap},
        "bank": _bank_block(bank, (), ph_ids, prompts, doc),
        "bar": transfer_bar(p.ph_flags, cut_flags, ph_ids, doc["transfer"]["bar"]),
        "bar_reading": doc["transfer"]["bar"]["reading"],
        "o": {"full": o_block(p.ph_flags, ph_ids), "cut": o_block(cut_flags, ph_ids)},
        "flag_change": flag_change(p.ph_flags, cut_flags, ph_ids),
        "answers": {"answers": len(p.records), "output_tokens": sum(r["output_tokens"] for r in p.records),
                    "capped": sum(r["stop_reason"] == en.STOP_CAP for r in p.records),
                    "empty": sum(r["empty"] for r in p.records), "longer_than_cut": len(p.cut_items)},
        "judge": _judge_block(p, doc, {"phtest_answers": len(p.records), "cut_answers": len(p.cut_items)}),
        "w1_18": dataclasses.asdict(prepared.w1_18),
        "adapter_fingerprint": p.fingerprint,
        "files": {TRANSFER_GENERATIONS: sha256_bytes(gen_bytes), TRANSFER_GUARD: sha256_bytes(guard_bytes)},
        "provenance": s1.provenance(Path(__file__).resolve(), settings.sha256, inputs, {}),
    }
    write_atomic(folder / TRANSFER_SUMMARY, canonical_json(summary))
    return summary


def brief(summary: Mapping[str, Any] | None) -> dict | None:
    """What a caller may print or put into a readable record: the branch, counts of prompts and file hashes; never
    an answer length, a flag or an O value."""
    if summary is None:
        return None
    return {"branch": summary["branch"], "prompts": summary["bank"]["prompts"],
            "phtest_max_new_tokens": summary["cap"]["phtest_max_new_tokens"], "files": dict(summary["files"])}


# ----- command line -----------------------------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None, *, _settings: Settings | None = None) -> int:
    parser = argparse.ArgumentParser(prog="oext_eval.py", description="O-ext: the pinned settings and inputs ($0)")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="the pinned settings and, given, the bank, its record and W1-18's record")
    p.add_argument("--oext-bank")
    p.add_argument("--oext-record")
    p.add_argument("--w1-18-record")
    args = parser.parse_args(argv)
    try:
        settings = _settings if _settings is not None else load_pinned_settings()
        given = any(x is not None for x in (args.oext_bank, args.oext_record, args.w1_18_record))
        prepared = prepare(settings, bank_path=args.oext_bank, record_path=args.oext_record,
                           w1_18_path=args.w1_18_record) if given or settings.doc["cap"]["branch"] == PENDING else None
    except (Refusal, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "refused": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2
    bank = None if prepared is None else prepared.bank
    print(json.dumps({"ok": True, "settings_sha256": settings.sha256, "module_sha256": module_sha256(),
                      "branch": settings.doc["cap"]["branch"], "cut_tokens": settings.doc["cap"]["cut_tokens"],
                      "bank_record_pinned": settings.doc["bank"]["phtest"]["record_sha256"] is not None,
                      "bank": None if bank is None else {"phtest_prompts": len(bank.rows), "planned": bank.planned,
                                                         "shortfall": bank.shortfall is not None,
                                                         "record_sha256": bank.record_sha256,
                                                         "bank_sha256": bank.bank_sha256},
                      "w1_18": None if prepared is None or prepared.w1_18 is None else dataclasses.asdict(prepared.w1_18)},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
