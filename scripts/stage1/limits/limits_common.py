"""Shared helpers of the Part F limit checks (REQ-19, W1-05, W1-18; standard library only).

What is here:

- ``ENGINE_ROOT``: the checkout that holds the engine package. The frozen reader, the lexicon source under tmp/
  and the default data root are found from it. (Under the mutation runner, the stage-1 code is a copy, but the
  engine, the frozen scripts and tmp/ come from the workspace, so ENGINE_ROOT stays the workspace.)
- ``frozen_reader``: ``scripts/family_probe_reading.py``, loaded by path after its SHA-256 check and the check of
  the ``killtest_stage0_reading.py`` that it loads. Only its ``sealed`` check is used (read-only use, as the frozen
  Gate B reading and ``gate_a_overrefusal_counts.py`` use it).
- ``check_unit`` / ``unit_file``: one sealed evaluation unit, checked against the settings' allow-list: the path is
  in the allowed form and inside the data root; COMPLETE.json and job.json hash to their pins; every file the unit's
  COMPLETE.json lists is present with its hash (the frozen ``sealed``); job.json names the arm, the seed and the
  checkpoint of the allow-list entry and the identity fields the settings fix; a refused recipe (Gate B's recipe S)
  refuses; ``eval/`` holds exactly the checkpoint's folder. A file is read once, hashed, checked against the hash
  that COMPLETE.json lists for it (and against its own pin, if the settings give one) and parsed from those bytes.
- ``fields_of``: JSONL records reduced at once to the named fields (every other field is dropped unread).
- ``load_lexicon``: the frozen opening lexicon (REQ-1's copy under scripts/stage1/lexicon/ when it exists, else the
  read-only source under tmp/mechanism-recipes/), refused unless both files hash to their pins and
  ``lexicon_sha256()`` equals the JSON pin.
- ``z`` and ``t_quantile``: normal and Student t quantiles (t: exact closed form for an integer df).
- ``text_hits``: how many text values appear in some bytes (raw or JSON-escaped), for the no-text checks.

Messages carry unit names, counts and hashes only, never prompt, answer, judge-output or lexicon text.
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable, Iterable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import experiments.safety_selection.common as engine_common  # noqa: E402
from experiments.safety_selection.common import sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

Refusal = s1.Refusal
ENGINE_ROOT = Path(engine_common.__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = ENGINE_ROOT / "tmp"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NORMAL = NormalDist()

__all__ = ["Refusal", "ENGINE_ROOT", "DEFAULT_DATA_ROOT", "frozen_reader", "CheckedUnit", "check_unit", "unit_file",
           "fields_of", "Lexicon", "load_lexicon", "z", "t_cdf", "t_quantile", "text_hits", "require_text_free",
           "hex64"]


def hex64(value: Any, what: str) -> str:
    """A lowercase SHA-256 hex string, or a refusal naming what."""
    if not isinstance(value, str) or not HEX64.match(value):
        raise Refusal(f"{what} is not a SHA-256")
    return value


# ----- the frozen reader -----------------------------------------------------------------------------------------

_READERS: dict[tuple[str, str, str], Any] = {}


def frozen_reader(spec: Mapping[str, Any]) -> Any:
    """scripts/family_probe_reading.py, loaded by path after both frozen scripts hash to their pins.
    spec: {family_probe_reading: {path, sha256}, killtest_stage0_reading: {path, sha256}} (paths under ENGINE_ROOT)."""
    paths = {}
    for key in ("family_probe_reading", "killtest_stage0_reading"):
        entry = spec.get(key) if isinstance(spec, Mapping) else None
        if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str):
            raise Refusal(f"the settings do not name the frozen script {key}")
        path = ENGINE_ROOT / entry["path"]
        pin = hex64(entry.get("sha256"), f"the pin of {key}")
        if not path.is_file() or sha256_file(path) != pin:
            raise Refusal(f"the frozen script {key} is missing or differs from its pin {pin}")
        paths[key] = (path, pin)
    cache_key = (str(paths["family_probe_reading"][0]), paths["family_probe_reading"][1],
                 paths["killtest_stage0_reading"][1])
    if cache_key not in _READERS:
        loader_spec = importlib.util.spec_from_file_location("stage1_limits_family_probe_reading",
                                                             paths["family_probe_reading"][0])
        module = importlib.util.module_from_spec(loader_spec)
        loader_spec.loader.exec_module(module)
        if not callable(getattr(module, "sealed", None)):
            raise Refusal("the frozen reader has no sealed check")
        _READERS[cache_key] = module
    return _READERS[cache_key]


# ----- sealed units against the allow-list -----------------------------------------------------------------------


@dataclass(frozen=True)
class CheckedUnit:
    name: str
    path: str                     # relative to the data root, as the allow-list names it
    folder: Path
    checkpoint: str
    complete_sha256: str
    job_sha256: str
    listed: dict                  # COMPLETE.json "files": unit-relative path -> SHA-256
    complete: dict
    job: dict

    @property
    def eval_prefix(self) -> str:
        return f"eval/{self.checkpoint}"


def _pinned(what: str, digest: str, pin: Any, required: bool) -> None:
    """The allow-list pin of one file: a required pin must be given; a given pin must equal the file's hash."""
    if pin is None:
        if required:
            raise Refusal(f"{what}: the allow-list gives no pin")
        return
    if digest != hex64(pin, f"{what}'s pin"):
        raise Refusal(f"{what} hashes to {digest}; the allow-list pins {pin}")


def _read(path: Path, what: str) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        raise Refusal(f"{what} is missing") from None
    except IsADirectoryError:
        raise Refusal(f"{what} is not a file") from None


def check_unit(data_root: Path, name: str, spec: Mapping[str, Any], rules: Mapping[str, Any], reader: Any) -> CheckedUnit:
    """One allow-listed unit, checked as the module docstring says. rules: path_pattern (a full-match regex),
    require_pins (bool), identity ({job.json field: required value}), refused_recipes (recipe hashes that refuse)."""
    path = spec.get("path")
    if not isinstance(path, str) or ".." in Path(path).parts or not re.fullmatch(rules["path_pattern"], path):
        raise Refusal(f"unit {name}: its path is not in the allowed form (a Gate A or development unit)")
    root = Path(data_root).resolve()
    folder = (root / path).resolve()
    if root not in folder.parents:
        raise Refusal(f"unit {name}: its path leaves the data root")
    complete_bytes = _read(folder / "COMPLETE.json", f"unit {name}: COMPLETE.json")
    job_bytes = _read(folder / "job.json", f"unit {name}: job.json")
    complete_sha256, job_sha256 = sha256_bytes(complete_bytes), sha256_bytes(job_bytes)
    required = bool(rules["require_pins"])
    _pinned(f"unit {name}: COMPLETE.json", complete_sha256, spec.get("complete_sha256"), required)
    _pinned(f"unit {name}: job.json", job_sha256, spec.get("job_sha256"), required)
    try:
        reader.sealed(folder)
    except SystemExit as exc:
        raise Refusal(f"unit {name}: the frozen sealed check refuses ({exc})") from None
    complete = s1.strict_json(complete_bytes)
    job = s1.strict_json(job_bytes)
    if not isinstance(complete, dict) or complete.get("complete") is not True or not isinstance(complete.get("files"), dict):
        raise Refusal(f"unit {name}: COMPLETE.json is not a complete marker with a file list")
    if not isinstance(job, dict):
        raise Refusal(f"unit {name}: job.json is not an object")
    checkpoint = spec.get("checkpoint")
    wanted = {"arm": spec.get("arm"), "seed": spec.get("seed"), "target_checkpoint": checkpoint}
    wrong = sorted(field for field, value in wanted.items() if job.get(field) != value)
    if wrong:
        raise Refusal(f"unit {name}: job.json's {', '.join(wrong)} differ from the allow-list entry")
    for field, value in (rules.get("identity") or {}).items():
        if job.get(field) != value:
            raise Refusal(f"unit {name}: job.json's {field} is not the value the settings fix")
    if job.get("recipe_sha256") in set(rules.get("refused_recipes") or ()):
        raise Refusal(f"unit {name}: its recipe is a refused (Gate B) recipe")
    evals = sorted(p.name for p in (folder / "eval").iterdir() if p.is_dir()) if (folder / "eval").is_dir() else []
    if evals != [checkpoint]:
        raise Refusal(f"unit {name}: eval/ does not hold exactly the folder of checkpoint {checkpoint}")
    return CheckedUnit(name, path, folder, checkpoint, complete_sha256, job_sha256, dict(complete["files"]),
                       complete, job)


def unit_file(unit: CheckedUnit, filename: str, pin: Any = None, required: bool = False) -> tuple[bytes, str]:
    """The bytes of eval/<checkpoint>/<filename>, read once; they must hash to COMPLETE.json's listed digest and to
    the allow-list pin, if one is given (required: the pin must be given). Returns (bytes, SHA-256)."""
    rel = f"{unit.eval_prefix}/{filename}"
    listed = unit.listed.get(rel)
    if listed is None:
        raise Refusal(f"unit {unit.name}: COMPLETE.json does not list {rel}")
    data = _read(unit.folder / rel, f"unit {unit.name}: {rel}")
    digest = sha256_bytes(data)
    if digest != listed:
        raise Refusal(f"unit {unit.name}: {rel} differs from the hash COMPLETE.json lists")
    _pinned(f"unit {unit.name}: {rel}", digest, pin, required)
    return data, digest


def fields_of(data: bytes, name: str, fields: Sequence[str], kinds: Iterable[str] | None = None) -> list[dict]:
    """Each JSONL record of these bytes (strict JSON) reduced at once to the named fields; with kinds, only the
    records whose "kind" is one of them. Every other field is dropped before the next record is read."""
    keep = set(kinds) if kinds is not None else None
    out = []
    for record in s1.iter_jsonl_bytes(data, name):
        if keep is None or record.get("kind") in keep:
            out.append({field: record.get(field) for field in fields})
        record.clear()
    return out


# ----- the frozen opening lexicon --------------------------------------------------------------------------------


@dataclass(frozen=True)
class Lexicon:
    classify: Callable[..., str]
    json_path: str
    classifier_path: str
    json_sha256: str
    classifier_sha256: str
    sensitivity: bool
    classes: tuple[str, ...]

    def label(self, text: str) -> str:
        """The lexicon class of one answer; a class outside the settings' list refuses (by name only)."""
        value = self.classify(text, self.sensitivity)
        if value not in self.classes:
            raise Refusal("the lexicon returned a class that the settings do not list")
        return value

    def record(self) -> dict:
        return {"json": self.json_path, "json_sha256": self.json_sha256, "classifier": self.classifier_path,
                "classifier_sha256": self.classifier_sha256, "sensitivity": self.sensitivity,
                "classes": list(self.classes)}


def _lexicon_files(candidate: Mapping[str, str]) -> tuple[Path, Path] | None:
    for root in (s1.REPO, ENGINE_ROOT):
        json_path, py_path = root / candidate["json"], root / candidate["classifier"]
        if json_path.is_file() and py_path.is_file():
            return json_path, py_path
    return None


def load_lexicon(spec: Mapping[str, Any]) -> Lexicon:
    """The pinned lexicon. spec: candidates (a list of {json, classifier} paths, first match wins; each is looked for
    under the stage-1 repository root, then under ENGINE_ROOT), json_sha256, classifier_sha256, sensitivity, classes."""
    json_pin = hex64(spec.get("json_sha256"), "the lexicon JSON pin")
    py_pin = hex64(spec.get("classifier_sha256"), "the lexicon classifier pin")
    found = None
    for candidate in spec.get("candidates") or ():
        found = _lexicon_files(candidate)
        if found is not None:
            break
    if found is None:
        raise Refusal("no lexicon copy is present at the paths the settings name")
    json_path, py_path = found
    if sha256_file(json_path) != json_pin or sha256_file(py_path) != py_pin:
        raise Refusal(f"the lexicon files differ from their pins ({json_pin[:8]}, {py_pin[:8]})")
    loader_spec = importlib.util.spec_from_file_location("stage1_limits_lexicon", py_path)
    module = importlib.util.module_from_spec(loader_spec)
    loader_spec.loader.exec_module(module)
    if module.lexicon_sha256() != json_pin:
        raise Refusal("the lexicon module's lexicon_sha256() is not the JSON pin")
    classes = tuple(spec.get("classes") or ())
    if not classes or not isinstance(spec.get("sensitivity"), bool):
        raise Refusal("the lexicon settings name no classes or no boolean sensitivity")
    return Lexicon(module.classify, s1.rel(json_path), s1.rel(py_path), json_pin, py_pin, spec["sensitivity"], classes)


# ----- quantiles -------------------------------------------------------------------------------------------------


def z(p: float) -> float:
    """The standard normal quantile."""
    return NORMAL.inv_cdf(p)


def t_cdf(x: float, df: int) -> float:
    """Student t CDF for an integer df >= 1, by the exact finite series (Abramowitz and Stegun 26.7.3, 26.7.4)."""
    if isinstance(df, bool) or not isinstance(df, int) or df < 1:
        raise Refusal("a t quantile needs an integer df of at least 1")
    theta = math.atan(x / math.sqrt(df))
    c2 = math.cos(theta) ** 2
    if df % 2 == 1:
        series, term = 1.0, 1.0
        for k in range(1, (df - 1) // 2):
            term *= (2 * k) / (2 * k + 1) * c2
            series += term
        inner = theta if df == 1 else theta + math.sin(theta) * math.cos(theta) * series
        return 0.5 + inner / math.pi
    series, term = 1.0, 1.0
    for k in range(1, df // 2):
        term *= (2 * k - 1) / (2 * k) * c2
        series += term
    return 0.5 + 0.5 * math.sin(theta) * series


def t_quantile(p: float, df: int) -> float:
    """The Student t quantile for 0.5 < p < 1 and an integer df, by bisection on t_cdf (to about 1e-13)."""
    if not 0.5 < p < 1:
        raise Refusal("t_quantile takes 0.5 < p < 1")
    low, high = 0.0, 1.0
    while t_cdf(high, df) < p:
        high *= 2.0
    for _ in range(200):
        mid = (low + high) / 2
        if t_cdf(mid, df) < p:
            low = mid
        else:
            high = mid
        if high - low < 1e-13:
            break
    return (low + high) / 2


# ----- no text -----------------------------------------------------------------------------------------------------


def text_hits(data: bytes, texts: Iterable[str], min_chars: int = 6) -> int:
    """How many text values of at least min_chars characters appear in data, raw or JSON-escaped."""
    hits = 0
    for text in texts:
        if not isinstance(text, str) or len(text) < min_chars:
            continue
        forms = {text.encode("utf-8"), json.dumps(text, ensure_ascii=False)[1:-1].encode("utf-8"),
                 json.dumps(text, ensure_ascii=True)[1:-1].encode("ascii")}
        hits += any(form in data for form in forms)
    return hits


def require_text_free(data: bytes, texts: Iterable[str], what: str) -> None:
    """Refuse when any text value appears in an output (the message gives the count only)."""
    hits = text_hits(data, texts)
    if hits:
        raise Refusal(f"{what} would hold {hits} text values; nothing is written")
