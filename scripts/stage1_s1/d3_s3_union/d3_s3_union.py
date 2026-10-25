"""REQ-11 under post-W1 deviation D-3 (addendum section 28): S3's scorer on the union of J5's two passes. Mac, CPU,
$0, engine X; the lead runs it on the real files in place of scripts/stage1/score_s3_datarx.py. It prints counts and
hashes only.

    python -B scripts/stage1_s1/d3_s3_union/d3_s3_union.py --main-rows PATH:SHA256 --main-summary PATH:SHA256
        --orig-rows PATH:SHA256 --orig-summary PATH:SHA256 --s-pool-record PATH:SHA256
        --answers-record PATH:SHA256 --work DIR --out DIR

Why. J5 ran a main pass (plant, decoy, s3_safe and the dev units) and, after J6, a pools-only pass over s3_orig.
score_s3_datarx.py (REQ-11, W1) reads one rows file and one summary that lists both s3_safe and s3_orig with the
SHA-256s their builders recorded (score_s3_datarx.py:84-88). representation_pass.py gives each row's features from that
row alone: one forward of a batch of one row with no padding and no mask, in eval mode with the adapter disabled,
compared with anchor means that each pass computes from the same pinned anchor bank before any row
(representation_pass.py:113-127, 352-378; notes/d3-build.json gives the reading). So the main pass's s3_safe rows
followed by the pools-only pass's s3_orig rows are the rows file that one pools-only pass over s3_safe and s3_orig
writes (section 28 point 4).

Checks, before anything is written (each refuses with a message, exit 2, nothing written):
- this package's settings hash to SETTINGS_SHA256 below; scripts/stage1/score_s3_datarx.py, its settings,
  representation_pass.py, its settings and s1common.py each hash to the W1 manifest's entry and this package's pin;
  the scorer's literal SETTINGS_SHA256 and its settings' pin of REQ-3's settings are this package's pins; the
  representation_pass and s1common modules the scorer imports by name hash to the same pins;
- the six inputs hash to the given SHA-256s; each summary holds exactly the W1 summary's fields, is a version-1
  "stage1 representation pass" and names its rows file by that SHA-256; each rows file holds the line count and the
  count per source that its summary states;
- the two passes are equal in every field of settings passes.equal: the kind and version, REQ-3's requirement, the
  layout, conventions and reads, the untuned rule, transformers, the anchors, the anchor-derived numbers (datashield:
  CAS and the direction norm at every index), the pool pins; provenance's script, script and s1common SHA-256s,
  settings SHA-256, engine identity, Python and numpy; the anchor file, prepared manifest, recipe file and pool pins
  inputs; Gate C's index, read and rule; the device. The script, its settings and the engine are this package's pins;
- s3_safe is listed in the main pass (and named in its provenance) at the S-pool record's s3_pool.sha256, and s3_orig
  in the pools-only pass at J6's record's lists.s3.s3_orig_pool_sha256; neither pool is in the other pass; J6's s3
  list is the S-pool record's s3_safe pool; the pools-only pass holds no dev row and no Gate C group; each pool has as
  many rows as its items less its refused items;
- every row taken is text-free: exactly REQ-3's fields {id, source, unit, n_prompt, n_tokens, cos_harmful, cos_safe,
  css}, a short id (REQ-3's pool-id form), unit null, two token counts, n + 1 rows of 4 numbers per cosine and n + 1
  numbers or nulls of css, and its bytes are REQ-3's own serialisation of it (json_line); the union's ids are
  distinct (one pass over both pools refuses a repeated id), and every s3_orig id ends with ':orig'.

Outputs. Into --work (absent or empty): representation_rows.jsonl, the main pass's s3_safe lines and then the
pools-only pass's s3_orig lines, each line's bytes unchanged; representation_pass.json, the main pass's summary with
pools = [the main pass's s3_safe entry, the pools-only pass's s3_orig entry], rows = the union's (file, SHA-256, lines,
count per source) and a "d3" block (both sources and both records by SHA-256, the rule, the reference, the checked
fields, the pins); every other field is the main pass's, unchanged. Then score_s3_datarx.py, loaded by path from the
checked bytes as a private module (not put in sys.modules), runs its own main() unchanged with --rows and --summary
the two union files (PATH:SHA256), --s-pool-record and --answers-record as given, and --out; its exit code is this
script's. If the scorer refuses, the union's two text-free files stay in --work and the scorer writes nothing.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, json_line, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "d3_s3_union.json"
SETTINGS_SHA256 = "31ae71e196c829fa719af2b1795743abcb2a35cc46db42f0fbd735956a630b16"
SETTINGS_NAME = "d3_s3_union"
MANIFEST_KIND = "stage-1 W1 commitments"
MODULE_NAME = "stage1_d3_score_s3_datarx"
PASS_KIND = "stage1 representation pass"
SPOOL_KIND = "stage1 s-pool record"
ANSWERS_KIND = "stage1 untuned answers record"
D3_KIND = "stage1 d3 s3 union"
ROWS_FILE = "representation_rows.jsonl"            # representation_pass.ROWS_FILE
SUMMARY_FILE = "representation_pass.json"          # representation_pass.SUMMARY_FILE
SAFE, ORIG = "s3_safe", "s3_orig"
ORIG_SUFFIX = ":orig"                              # score_s3_datarx.ORIG_SUFFIX
N_READS = 4                                        # representation_pass.READS: a, b, c, d
ROW_ID = re.compile(r"^[A-Za-z0-9_.:+\-]{1,160}$")  # representation_pass.POOL_ID
SUMMARY_KEYS = frozenset({"kind", "version", "requirement", "layout", "index_convention", "reads", "untuned",
                          "transformers_version", "anchors", "datashield", "gate_c", "rows", "pools", "pool_pins",
                          "costs", "provenance"})
ROWS_KEYS = frozenset({"file", "sha256", "lines", "by_source"})
POOL_KEYS = frozenset({"name", "sha256", "items", "pinned_by", "refused_by_reason"})
ROW_KEYS = frozenset({"id", "source", "unit", "n_prompt", "n_tokens", "cos_harmful", "cos_safe", "css"})
PINNED = (("scorer", "scorer_sha256", "score_s3_datarx.py"),
          ("scorer_settings", "scorer_settings_sha256", "score_s3_datarx.json"),
          ("pass_script", "pass_script_sha256", "representation_pass.py"),
          ("pass_settings", "pass_settings_sha256", "representation_pass.json"),
          ("s1common", "s1common_sha256", "s1common.py"))
INPUTS = (("main_rows", "--main-rows", "the main pass's rows file"),
          ("main_summary", "--main-summary", "the main pass's summary"),
          ("orig_rows", "--orig-rows", "the pools-only pass's rows file"),
          ("orig_summary", "--orig-summary", "the pools-only pass's summary"),
          ("s_pool_record", "--s-pool-record", "the S-pool record"),
          ("answers_record", "--answers-record", "J6's untuned answers record"))
MISSING = object()


@dataclass(frozen=True)
class Base:
    """score_s3_datarx.py loaded by path after its checks."""

    module: ModuleType
    scorer_sha256: str
    manifest_sha256: str


# ----- small helpers --------------------------------------------------------------------------------------------------


def is_hex64(value) -> bool:
    """64 lowercase hex digits and nothing else (fullmatch: s1.HEX64's $ would also match before a final newline)."""
    return isinstance(value, str) and s1.HEX64.fullmatch(value) is not None


def is_count(value, minimum: int) -> bool:
    """An int (never a bool) of at least minimum."""
    return type(value) is int and value >= minimum


def is_number(value) -> bool:
    """A JSON number (int or float; never a bool). s1.strict_json refuses NaN and infinity."""
    return type(value) in (int, float)


def same(a, b) -> bool:
    """Equal as JSON (by canonical bytes, so 1, 1.0 and true differ); a missing value is never equal."""
    return a is not MISSING and b is not MISSING and canonical_json(a) == canonical_json(b)


def parse_hashed(spec: str, what: str) -> tuple[Path, str]:
    """PATH:SHA256 (64 lowercase hex digits after the last colon, and nothing after them)."""
    path, _, sha = str(spec).rpartition(":")
    if not path or not is_hex64(sha):
        raise s1.Refusal(f"{what} is PATH:SHA256 (64 lowercase hex digits)")
    return Path(path), sha


def read_hashed(path: Path, sha: str, what: str) -> bytes:
    """The file's bytes, refused unless they hash to sha."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != sha:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {sha}")
    return data


def _get(doc, *keys):
    """doc[k1][k2]..., or None when a level is missing or not an object."""
    for key in keys:
        if not isinstance(doc, dict):
            return None
        doc = doc.get(key)
    return doc


# ----- the W1 files, by path, after their SHA-256 checks --------------------------------------------------------------


def w1_root() -> Path:
    """The checkout that holds the W1 package scripts.stage1 (the workspace; under this package's mutation runner too,
    whose copy holds only scripts/stage1_s1/d3_s3_union)."""
    spec = importlib.util.find_spec("scripts.stage1")
    return Path(spec.origin).resolve().parents[2]


def manifest_entries(path: Path) -> tuple[dict[str, str], str]:
    """{path: SHA-256} of the W1 manifest's entries, and the manifest's own SHA-256."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"the W1 manifest cannot be read ({type(exc).__name__})") from None
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != MANIFEST_KIND or not isinstance(doc.get("entries"), list):
        raise s1.Refusal("not the stage-1 W1 commitments manifest")
    entries = {e["path"]: e.get("sha256") for e in doc["entries"] if isinstance(e, dict) and isinstance(e.get("path"), str)}
    return entries, sha256_bytes(data)


def load_settings() -> tuple[dict, str]:
    """This package's settings, refused unless they hash to SETTINGS_SHA256 (both read when called)."""
    try:
        return s1.load_settings(SETTINGS_PATH, SETTINGS_SHA256, SETTINGS_NAME)
    except OSError as exc:
        raise s1.Refusal(f"the D-3 settings cannot be read ({type(exc).__name__})") from None


def load_scorer(d3: dict, root: Path | None = None) -> Base:
    """score_s3_datarx.py, run privately (not put in sys.modules) from the bytes that passed their check. Every file of
    PINNED must hash to the W1 manifest's entry for its path and to this package's pin; the scorer's literal settings
    pin and its settings' pin of REQ-3's settings must be this package's."""
    root = Path(root) if root is not None else w1_root()
    base = d3["base"]
    entries, manifest_sha256 = manifest_entries(root / base["manifest"])
    data = {}
    for rel_key, pin_key, what in PINNED:
        if entries.get(base[rel_key]) != base[pin_key]:
            raise s1.Refusal(f"{what}: the W1 manifest names {entries.get(base[rel_key])}, the D-3 settings pin "
                             f"{base[pin_key]}")
        data[rel_key] = read_hashed(root / base[rel_key], base[pin_key], what)
    scorer_settings = s1.strict_json(data["scorer_settings"])
    if _get(scorer_settings, "pins", "representation_pass_settings_sha256") != base["pass_settings_sha256"]:
        raise s1.Refusal("score_s3_datarx.json does not pin REQ-3's settings at the D-3 pin of representation_pass.json")
    path = (root / base["scorer"]).resolve()
    spec = importlib.util.spec_from_file_location(MODULE_NAME, path)
    module = importlib.util.module_from_spec(spec)
    saved = list(sys.path)
    try:
        exec(compile(data["scorer"], str(path), "exec"), module.__dict__)
    finally:
        sys.path[:] = saved
    if module.SETTINGS_SHA256 != base["scorer_settings_sha256"]:
        raise s1.Refusal("score_s3_datarx.py's own settings pin is not the D-3 settings' base.scorer_settings_sha256")
    return Base(module, sha256_bytes(data["scorer"]), manifest_sha256)


def check_by_name(d3: dict) -> None:
    """score_s3_datarx imports scripts.stage1.s1common (at load) and scripts.stage1.representation_pass (in build(),
    for READS) by name: each module's file must hash to this package's pin."""
    from scripts.stage1 import representation_pass as rp

    for module, pin_key, what in ((rp, "pass_script_sha256", "representation_pass"), (s1, "s1common_sha256", "s1common")):
        origin = getattr(module, "__file__", None)
        digest = sha256_file(Path(origin)) if origin and Path(origin).is_file() else None
        if digest != d3["base"][pin_key]:
            raise s1.Refusal(f"the {what} module that score_s3_datarx imports by name hashes to {digest}, the D-3 pin "
                             f"is {d3['base'][pin_key]}")


# ----- the two passes --------------------------------------------------------------------------------------------------


def summary_of(data: bytes, rows_sha256: str, what: str) -> dict:
    """A pass's summary: exactly the W1 summary's fields, version-1 'stage1 representation pass', naming its rows
    file by rows_sha256."""
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or set(doc) != SUMMARY_KEYS:
        raise s1.Refusal(f"{what}'s summary does not hold exactly the fields of a REQ-3 summary")
    if doc["kind"] != PASS_KIND or type(doc["version"]) is not int or doc["version"] != 1:
        raise s1.Refusal(f"{what}'s summary is not a version-1 {PASS_KIND!r}")
    rows = doc["rows"]
    if not isinstance(rows, dict) or set(rows) != ROWS_KEYS or rows["file"] != ROWS_FILE or \
            not is_count(rows["lines"], 0) or not isinstance(rows["by_source"], dict):
        raise s1.Refusal(f"{what}'s summary has no rows block {{file {ROWS_FILE}, sha256, lines, by_source}}")
    if rows["sha256"] != rows_sha256:
        raise s1.Refusal(f"{what}'s rows file is not the one its summary names ({rows['sha256']})")
    if not is_count(_get(doc, "layout", "n_layers"), 1):
        raise s1.Refusal(f"{what}'s summary states no layer count")
    pools = doc["pools"]
    if not isinstance(pools, list) or any(not isinstance(p, dict) or set(p) != POOL_KEYS for p in pools):
        raise s1.Refusal(f"{what}'s summary lists a pool that is not {{name, sha256, items, pinned_by, refused_by_reason}}")
    names = [p["name"] for p in pools]
    if len(set(map(str, names))) != len(names):
        raise s1.Refusal(f"{what}'s summary lists one pool name twice")
    for key, inner in (("provenance", "inputs"), ("gate_c", "groups")):
        if not isinstance(_get(doc, key, inner), dict):
            raise s1.Refusal(f"{what}'s summary has no {key}.{inner} object")
    if not isinstance(doc["costs"], dict):
        raise s1.Refusal(f"{what}'s summary has no costs object")
    return doc


def _node(doc: dict, where: tuple) -> dict:
    return doc if not where else _get(doc, *where)


def check_same(main: dict, orig: dict, d3: dict) -> None:
    """The two passes are equal in every field of settings passes.equal, and the shared script, settings and engine
    are this package's pins."""
    equal = d3["passes"]["equal"]
    for where, keys in (((), equal["fields"]), (("provenance",), equal["provenance"]),
                        (("provenance", "inputs"), equal["inputs"]), (("gate_c",), equal["gate_c"]),
                        (("costs",), equal["costs"])):
        a, b = _node(main, where), _node(orig, where)
        for key in keys:
            if not same(a.get(key, MISSING), b.get(key, MISSING)):
                raise s1.Refusal(f"the two passes differ in {'.'.join(where + (key,))} (or one of them lacks it)")
    base, prov = d3["base"], main["provenance"]
    for key, pin in (("script", base["pass_script"]), ("script_sha256", base["pass_script_sha256"]),
                     ("settings_sha256", base["pass_settings_sha256"]), ("engine_identity_sha256", d3["engine_x"])):
        if prov.get(key) != pin:
            raise s1.Refusal(f"the passes' provenance.{key} is {prov.get(key)}, the D-3 settings pin {pin}")


def record_pins(pool_bytes: bytes, answers_bytes: bytes) -> tuple[str, str]:
    """(s3_safe's SHA-256 from the S-pool record's s3_pool.sha256, s3_orig's from J6's lists.s3.s3_orig_pool_sha256);
    J6's s3 list must be the S-pool record's s3_safe pool (its list_sha256)."""
    pool_rec, answers = s1.strict_json(pool_bytes), s1.strict_json(answers_bytes)
    if _get(pool_rec, "kind") != SPOOL_KIND:
        raise s1.Refusal(f"the S-pool record is not a {SPOOL_KIND!r}")
    if _get(answers, "kind") != ANSWERS_KIND:
        raise s1.Refusal(f"J6's record is not a {ANSWERS_KIND!r}")
    safe, orig = _get(pool_rec, "s3_pool", "sha256"), _get(answers, "lists", "s3", "s3_orig_pool_sha256")
    if not is_hex64(safe):
        raise s1.Refusal("the S-pool record names no s3_pool.sha256")
    if not is_hex64(orig):
        raise s1.Refusal("J6's record names no lists.s3.s3_orig_pool_sha256")
    if _get(answers, "lists", "s3", "list_sha256") != safe:
        raise s1.Refusal("J6's s3 list is not the S-pool record's s3_safe pool (lists.s3.list_sha256 differs from "
                         "s3_pool.sha256)")
    return safe, orig


def pool_entry(doc: dict, name: str, other: str, digest: str, what: str, source: str) -> tuple[dict, int]:
    """(the pass's summary entry of pool ``name``, its expected row count = items - refused items). The pool must be
    listed and named in the provenance at ``digest``; the other pool must be in neither."""
    names = [p["name"] for p in doc["pools"]]
    inputs = doc["provenance"]["inputs"]
    if other in names or f"pool_{other}" in inputs:
        raise s1.Refusal(f"{what} lists pool {other}, which D-3 takes from the other pass only")
    entry = next((p for p in doc["pools"] if p["name"] == name), None)
    if entry is None:
        raise s1.Refusal(f"{what} does not list pool {name}")
    if entry["sha256"] != digest:
        raise s1.Refusal(f"{what} lists pool {name} at {entry['sha256']}; {source} gives {digest}")
    if inputs.get(f"pool_{name}") != digest:
        raise s1.Refusal(f"{what}'s provenance does not name pool {name} by {digest}")
    refused = entry["refused_by_reason"]
    if not is_count(entry["items"], 1) or not isinstance(refused, dict) or \
            not all(is_count(v, 1) for v in refused.values()) or sum(refused.values()) > entry["items"]:
        raise s1.Refusal(f"{what}: pool {name}'s item count or refused counts are not counts")
    return entry, entry["items"] - sum(refused.values())


def check_pools_only(doc: dict, what: str) -> None:
    if "dev" in doc["rows"]["by_source"] or doc["gate_c"]["groups"]:
        raise s1.Refusal(f"{what} is not a pools-only pass (it holds dev rows or Gate C groups)")


def check_row(obj: dict, raw: bytes, n: int, where: str) -> None:
    """A text-free REQ-3 pool row: exactly ROW_KEYS, a short id, unit null, token counts, n + 1 rows of 4 numbers per
    cosine, n + 1 numbers or nulls of css, serialised as REQ-3 serialises it."""
    if set(obj) != ROW_KEYS:
        raise s1.Refusal(f"{where} holds {len(set(obj) - ROW_KEYS)} field(s) besides REQ-3's and lacks "
                         f"{sorted(ROW_KEYS - set(obj))} (a row holds features and ids only)")
    if not isinstance(obj["id"], str) or not ROW_ID.fullmatch(obj["id"]):
        raise s1.Refusal(f"{where}: its id is not a short pool id")
    if obj["unit"] is not None:
        raise s1.Refusal(f"{where}: a pool row names a unit")
    if not is_count(obj["n_prompt"], 1) or not is_count(obj["n_tokens"], 3) or obj["n_prompt"] > obj["n_tokens"] - 2:
        raise s1.Refusal(f"{where}: its token counts are not counts of a scored row")
    for key in ("cos_harmful", "cos_safe"):
        m = obj[key]
        if not isinstance(m, list) or len(m) != n + 1 or \
                any(not isinstance(r, list) or len(r) != N_READS or not all(is_number(x) for x in r) for r in m):
            raise s1.Refusal(f"{where}: {key} is not {n + 1} rows of {N_READS} numbers")
    css = obj["css"]
    if not isinstance(css, list) or len(css) != n + 1 or not all(x is None or is_number(x) for x in css):
        raise s1.Refusal(f"{where}: css is not {n + 1} numbers or nulls")
    if json_line(obj) != raw + b"\n":
        raise s1.Refusal(f"{where}: its bytes are not REQ-3's serialisation of the row")


def taken_rows(data: bytes, doc: dict, name: str, expected: int, n: int, what: str) -> list[tuple[str, bytes]]:
    """[(id, the line's bytes with its newline)] of the rows of source ``name``, in file order; every line is a row
    with a source, the counts are the summary's, and the pool has ``expected`` rows."""
    if data and not data.endswith(b"\n"):
        raise s1.Refusal(f"{what}'s rows file does not end with a newline")
    counts: dict[str, int] = {}
    taken = []
    for number, raw in enumerate(data.split(b"\n")[:-1], 1):
        try:
            obj = s1.strict_json(raw)
        except s1.Refusal:
            raise s1.Refusal(f"{what}'s rows file: line {number} is not one strict JSON value") from None
        source = obj.get("source") if isinstance(obj, dict) else None
        if not isinstance(source, str):
            raise s1.Refusal(f"{what}'s rows file: line {number} is not a row with a source")
        counts[source] = counts.get(source, 0) + 1
        if source == name:
            check_row(obj, raw, n, f"{what}'s rows file: line {number}")
            taken.append((obj["id"], raw + b"\n"))
    rows = doc["rows"]
    if not same(counts, rows["by_source"]) or sum(counts.values()) != rows["lines"]:
        raise s1.Refusal(f"{what}'s rows file holds {sum(counts.values())} lines {dict(sorted(counts.items()))}; its "
                         f"summary states {rows['lines']} {rows['by_source']}")
    if len(taken) != expected:
        raise s1.Refusal(f"{what} holds {len(taken)} {name} rows; its pool's items less its refused items are {expected}")
    return taken


# ----- the union -----------------------------------------------------------------------------------------------------


def union_files(inputs: dict[str, tuple[bytes, str]], d3: dict, d3_sha256: str, base: Base) -> dict[str, bytes]:
    """The union's two files (rows, summary) from the six checked inputs {key: (bytes, SHA-256)}, every check passed."""
    main = summary_of(inputs["main_summary"][0], inputs["main_rows"][1], "the main pass")
    orig = summary_of(inputs["orig_summary"][0], inputs["orig_rows"][1], "the pools-only pass")
    check_same(main, orig, d3)
    safe_sha, orig_sha = record_pins(inputs["s_pool_record"][0], inputs["answers_record"][0])
    safe_entry, n_safe = pool_entry(main, SAFE, ORIG, safe_sha, "the main pass", "the S-pool record's s3_pool.sha256")
    orig_entry, n_orig = pool_entry(orig, ORIG, SAFE, orig_sha, "the pools-only pass",
                                    "J6's record's lists.s3.s3_orig_pool_sha256")
    check_pools_only(orig, "the pools-only pass")
    n = main["layout"]["n_layers"]
    safe_rows = taken_rows(inputs["main_rows"][0], main, SAFE, n_safe, n, "the main pass")
    orig_rows = taken_rows(inputs["orig_rows"][0], orig, ORIG, n_orig, n, "the pools-only pass")
    ids = [i for i, _ in safe_rows + orig_rows]
    if len(set(ids)) != len(ids):
        raise s1.Refusal(f"{len(ids) - len(set(ids))} row id(s) repeat across the union (one pass over both pools "
                         "refuses a repeated id)")
    if any(not i.endswith(ORIG_SUFFIX) for i, _ in orig_rows):
        raise s1.Refusal(f"an s3_orig row id does not end with {ORIG_SUFFIX!r}")
    rows_bytes = b"".join(line for _, line in safe_rows + orig_rows)
    summary = copy.deepcopy(main)
    summary["pools"] = [copy.deepcopy(safe_entry), copy.deepcopy(orig_entry)]
    summary["rows"] = {"file": ROWS_FILE, "sha256": sha256_bytes(rows_bytes), "lines": len(ids),
                       "by_source": {src: count for src, count in ((SAFE, len(safe_rows)), (ORIG, len(orig_rows)))
                                     if count}}
    here = Path(__file__).resolve()
    summary["d3"] = {
        "kind": D3_KIND, "version": 1, "reference": d3["reference"], "rule": d3["union"]["rule"],
        "sources": {
            "main": {"summary_sha256": inputs["main_summary"][1], "rows_sha256": inputs["main_rows"][1], "pool": SAFE,
                     "pool_sha256": safe_sha, "rows_taken": len(safe_rows), "lines": main["rows"]["lines"],
                     "by_source": main["rows"]["by_source"], "pools": [p["name"] for p in main["pools"]]},
            "orig": {"summary_sha256": inputs["orig_summary"][1], "rows_sha256": inputs["orig_rows"][1], "pool": ORIG,
                     "pool_sha256": orig_sha, "rows_taken": len(orig_rows), "lines": orig["rows"]["lines"],
                     "by_source": orig["rows"]["by_source"], "pools": [p["name"] for p in orig["pools"]]}},
        "records": {"s_pool_record_sha256": inputs["s_pool_record"][1],
                    "answers_record_sha256": inputs["answers_record"][1]},
        "checked_equal": d3["passes"]["equal"],
        "from_the_main_pass": d3["union"]["summary"],
        "provenance": {"script": s1.rel(here), "script_sha256": sha256_file(here), "settings_sha256": d3_sha256,
                       "w1_manifest_sha256": base.manifest_sha256, "score_s3_datarx_sha256": base.scorer_sha256,
                       "representation_pass_sha256": d3["base"]["pass_script_sha256"],
                       "engine_identity_sha256": s1.code_identity()["sha256"]}}
    return {ROWS_FILE: rows_bytes, SUMMARY_FILE: canonical_json(summary)}


def check_folders(work: Path, out: Path) -> tuple[Path, Path]:
    """--work and --out: two separate folders, neither inside the other, each absent or empty."""
    work, out = Path(work).resolve(), Path(out).resolve()
    if work == out or work in out.parents or out in work.parents:
        raise s1.Refusal("--work and --out must be two separate folders, neither inside the other")
    for folder, flag in ((work, "--work"), (out, "--out")):
        if folder.exists() and (not folder.is_dir() or any(folder.iterdir())):
            raise s1.Refusal(f"{flag} {folder} exists and is not an empty folder: nothing is overwritten")
    return work, out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], allow_abbrev=False)
    for _, flag, what in INPUTS:
        parser.add_argument(flag, required=True, help=f"PATH:SHA256 of {what}")
    parser.add_argument("--work", type=Path, required=True, help="the union's rows and summary (an absent or empty folder)")
    parser.add_argument("--out", type=Path, required=True, help="score_s3_datarx.py's --out (an absent or empty folder)")
    args = parser.parse_args(argv)
    specs = {key: getattr(args, flag[2:].replace("-", "_")) for key, flag, _ in INPUTS}
    try:
        d3, d3_sha256 = load_settings()
        base = load_scorer(d3)
        check_by_name(d3)
        inputs = {}
        for key, flag, what in INPUTS:
            path, sha = parse_hashed(specs[key], flag)
            inputs[key] = (read_hashed(path, sha, what), sha)
        work, out = check_folders(args.work, args.out)
        files = union_files(inputs, d3, d3_sha256, base)
        written = s1.write_new_files(work, files)
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    rows = json.loads(files[SUMMARY_FILE])["rows"]
    print(f"D-3: the main pass {inputs['main_summary'][1]} ({SAFE}) and the pools-only pass "
          f"{inputs['orig_summary'][1]} ({ORIG}); score_s3_datarx.py {base.scorer_sha256}")
    print(f"  {written[ROWS_FILE]}  {work / ROWS_FILE}  ({rows['lines']} rows: {rows['by_source']})")
    print(f"  {written[SUMMARY_FILE]}  {work / SUMMARY_FILE}")
    code = base.module.main(["--rows", f"{work / ROWS_FILE}:{written[ROWS_FILE]}",
                             "--summary", f"{work / SUMMARY_FILE}:{written[SUMMARY_FILE]}",
                             "--s-pool-record", specs["s_pool_record"], "--answers-record", specs["answers_record"],
                             "--out", str(out)])
    if code != 0:
        print(f"D-3: score_s3_datarx.py refused (exit {code}); the union's two text-free files stay in {work}; "
              f"nothing was written into {out}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
