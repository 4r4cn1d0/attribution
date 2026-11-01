"""REQ-3's pool pins filled from REQ-8's record under post-W1 deviation D-2 (addendum section 19 points 1-2(a)).
Mac, CPU, $0, engine X; text-free (it reads the W1 pins file and REQ-8's text-free record only, never a pool file).

    python -B scripts/stage1_s1/d2_pool_pins/fill_pins.py --w1-pins PATH:SHA256 --req8-record PATH:SHA256 --out FILE

The W1 fill rule (representation_pools.json "fill") is applied exactly: the filled file is the W1 pins document with
pools.plant.sha256 and pools.decoy.sha256 set to the SHA-256 that REQ-8's record gives for plant.pool.json and
decoy.pool.json, each with the item count the W1 pins state (75 and 37), serialised as the W1 file is (canonical JSON).
Nothing else differs; the file is written new (never over an existing file) and read back.

Checks (each refuses with a message; nothing is written):
- this package's settings (settings/d2_pool_pins.json) hash to SETTINGS_SHA256 below;
- the W1 pins file hashes to the given SHA-256, which is the W1 manifest's entry for its path and this package's pin
  (1451ba5e...); its bytes are the canonical JSON of its document; both pins are still null;
- scripts/stage1/representation_pass.py hashes to the manifest's entry and this package's pin, and is run privately
  (not put in sys.modules) from the checked bytes; its literal POOL_PINS_SHA256 is the W1 pins' SHA-256 and its
  SETTINGS_SHA256 the manifest's entry for representation_pass.json; its own check_pool_pins accepts the filled file;
- REQ-8's record hashes to the given SHA-256, is kind "stage1 plant record" version 1, was written by the W1
  build_plant.py with the W1 build_plant.json and build_plant_extra.json (its provenance against the manifest), and is
  consistent in itself: pools.<name>.sha256 equals full_files[<name>.pool.json], pools.plant.items the number of plant
  ids, pools.decoy.items the number of decoy ids and pools.decoy.sha256 decoy.pool_sha256;
- the filled document differs from the W1 one in exactly pools.decoy.sha256 and pools.plant.sha256 (a leaf-by-leaf
  comparison), each equal to the record's SHA-256 for that pool file, the record's item count equal to the W1 pins'.

d2_representation_pass.py imports this module for the same checks (load_base, check_record, check_filled).
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, write_atomic  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "d2_pool_pins.json"
SETTINGS_SHA256 = "d6fa043fea4482fa0293d1bc936cd5c77466f4fc6b0c8d56df458e6e2e7b3bd1"
SETTINGS_NAME = "d2_pool_pins"
MANIFEST_KIND = "stage-1 W1 commitments"
POOLS = ("decoy", "plant")
FILLED = tuple(("pools", name, "sha256") for name in POOLS)
MODULE_NAME = "stage1_d2_representation_pass"


@dataclass(frozen=True)
class Base:
    """representation_pass.py loaded by path after its checks, with the checked W1 pins."""

    module: ModuleType
    script_sha256: str
    pins_doc: dict
    pins_bytes: bytes
    pins_sha256: str
    manifest_sha256: str
    entries: dict


# ----- the W1 files, by path, after their SHA-256 checks ----------------------------------------------------------


def w1_root() -> Path:
    """The checkout that holds the W1 package scripts.stage1 (the workspace; under this package's mutation runner too,
    whose copy holds only scripts/stage1_s1/d2_pool_pins)."""
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


def is_hex64(value) -> bool:
    """64 lowercase hex digits and nothing else. s1.HEX64 is ^[0-9a-f]{64}$, and re.match lets $ match before a final
    newline, so its .match alone would accept '<hex>\\n'; fullmatch does not."""
    return isinstance(value, str) and s1.HEX64.fullmatch(value) is not None


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


def check_pin(entries: dict, rel: str, pin: str, what: str) -> None:
    if entries.get(rel) != pin:
        raise s1.Refusal(f"{what}: the W1 manifest names {entries.get(rel)}, the D-2 settings pin {pin}")


def load_base(d2: dict, w1_pins: tuple[Path, str], root: Path | None = None) -> Base:
    """representation_pass.py (checked against the W1 manifest's entry and the D-2 pin; run privately from the checked
    bytes, not put in sys.modules) and the W1 pins file w1_pins = (path, SHA-256), whose SHA-256 must be the manifest's
    entry and the D-2 pin and the module's literal POOL_PINS_SHA256; both of its pins must still be null."""
    root = Path(root) if root is not None else w1_root()
    base = d2["base"]
    entries, manifest_sha256 = manifest_entries(root / base["manifest"])
    check_pin(entries, base["script"], base["script_sha256"], "representation_pass.py")
    check_pin(entries, base["pins"], base["pins_sha256"], "representation_pools.json")
    check_pin(entries, base["settings"], base["settings_sha256"], "representation_pass.json")
    path = (root / base["script"]).resolve()
    code = read_hashed(path, base["script_sha256"], "representation_pass.py")
    pins_path, pins_sha = w1_pins
    if pins_sha != base["pins_sha256"]:
        raise s1.Refusal(f"the W1 pins are named by {pins_sha}, the W1 manifest and the D-2 settings pin {base['pins_sha256']}")
    pins_bytes = read_hashed(pins_path, pins_sha, "the W1 pins file")
    spec = importlib.util.spec_from_file_location(MODULE_NAME, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(code, str(path), "exec"), module.__dict__)
    if module.POOL_PINS_SHA256 != pins_sha:
        raise s1.Refusal("representation_pass.py's literal POOL_PINS_SHA256 is not the W1 pins' SHA-256")
    if module.SETTINGS_SHA256 != base["settings_sha256"]:
        raise s1.Refusal("representation_pass.py's own settings pin is not the D-2 settings' base.settings_sha256")
    pins_doc = module.check_pool_pins(s1.strict_json(pins_bytes))
    if canonical_json(pins_doc) != pins_bytes:
        raise s1.Refusal("the W1 pins file is not in canonical JSON form")
    if set(pins_doc["pools"]) != set(POOLS) or any(pins_doc["pools"][n]["sha256"] is not None for n in POOLS):
        raise s1.Refusal("the W1 pins do not list exactly the plant and decoy pools with null pins")
    return Base(module, sha256_bytes(code), pins_doc, pins_bytes, pins_sha, manifest_sha256, entries)


# ----- REQ-8's record ------------------------------------------------------------------------------------------------


def _get(doc, *path):
    for key in path:
        if not isinstance(doc, dict) or key not in doc:
            raise s1.Refusal(f"REQ-8's record has no {'.'.join(path)}")
        doc = doc[key]
    return doc


def _count(value, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise s1.Refusal(f"REQ-8's record: {what} is not a positive count")
    return value


def check_record(data: bytes, d2: dict, entries: dict) -> dict[str, dict]:
    """{pool name: {"sha256", "items"}} from REQ-8's record (its bytes, already checked against the given SHA-256)."""
    req8 = d2["req8"]
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != req8["record_kind"] or doc.get("version") != req8["record_version"] \
            or type(doc.get("version")) is not int:                    # True == 1.0 == 1 in Python; JSON's 1 is an int
        raise s1.Refusal(f"REQ-8's record is not a version-{req8['record_version']} {req8['record_kind']!r}")
    _get(doc, "provenance")
    for key, rel, pin, what in (("script_sha256", req8["script"], req8["script_sha256"], "build_plant.py"),
                                ("settings_sha256", req8["settings"], req8["settings_sha256"], "build_plant.json")):
        check_pin(entries, rel, pin, what)
        if _get(doc, "provenance", key) != pin:
            raise s1.Refusal(f"REQ-8's record was not written by the W1 {what} ({key} {_get(doc, 'provenance', key)}, "
                             f"the pin {pin})")
    if _get(doc, "provenance", "script") != req8["script"]:
        raise s1.Refusal(f"REQ-8's record names the script {_get(doc, 'provenance', 'script')!r}, not {req8['script']!r}")
    check_pin(entries, req8["extra"], req8["extra_sha256"], "build_plant_extra.json")
    if _get(doc, "provenance", "inputs", "build_plant_extra") != req8["extra_sha256"]:
        raise s1.Refusal("REQ-8's record was not written with the W1 build_plant_extra.json")
    pools = _get(doc, "pools")
    if not isinstance(pools, dict) or set(pools) != set(POOLS):
        raise s1.Refusal("REQ-8's record does not list exactly the plant and decoy pools")
    out = {}
    for name in POOLS:
        entry = pools[name]
        if not isinstance(entry, dict) or set(entry) != {"sha256", "items"} or not is_hex64(entry["sha256"]):
            raise s1.Refusal(f"REQ-8's record: pools.{name} is not {{sha256, items}}")
        if _get(doc, "full_files", req8["pool_files"][name]) != entry["sha256"]:
            raise s1.Refusal(f"REQ-8's record: pools.{name}.sha256 is not full_files[{req8['pool_files'][name]}]")
        out[name] = {"sha256": entry["sha256"], "items": _count(entry["items"], f"pools.{name}.items")}
    ids = {"plant": _get(doc, "plant_rows", "ids"), "decoy": _get(doc, "decoy", "ids")}
    for name in POOLS:
        if not isinstance(ids[name], list) or len(ids[name]) != out[name]["items"]:
            raise s1.Refusal(f"REQ-8's record: pools.{name}.items is not the number of its ids")
    if _get(doc, "decoy", "pool_sha256") != out["decoy"]["sha256"]:
        raise s1.Refusal("REQ-8's record: decoy.pool_sha256 is not pools.decoy.sha256")
    return out


# ----- the fill and its check ----------------------------------------------------------------------------------------


def differences(a, b, path: tuple = ()) -> list[tuple]:
    """Every leaf path where two parsed JSON documents differ (a type change, a value change, a key or list item on one
    side only)."""
    if isinstance(a, dict) and isinstance(b, dict):
        return [d for key in sorted(set(a) | set(b)) for d in
                (differences(a[key], b[key], path + (key,)) if key in a and key in b else [path + (key,)])]
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [path]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, path + (i,))]
    return [] if type(a) is type(b) and a == b else [path]


def fill(pins_doc: dict, record_pools: dict) -> dict:
    """The W1 pins document with each pool's sha256 set to the record's (the record's item count must be the pins')."""
    doc = copy.deepcopy(pins_doc)
    for name in POOLS:
        entry = doc["pools"][name]
        if record_pools[name]["items"] != entry["items"]:
            raise s1.Refusal(f"REQ-8's record gives {record_pools[name]['items']} items for pool {name}, the W1 pins "
                             f"say {entry['items']}")
        entry["sha256"] = record_pools[name]["sha256"]
    return doc


def check_filled(base: Base, filled_bytes: bytes, record_pools: dict) -> dict:
    """The filled pins: they differ from the W1 pins in exactly pools.decoy.sha256 and pools.plant.sha256, each equal to
    REQ-8's record's SHA-256 for that pool file; representation_pass's check_pool_pins accepts them; their bytes are
    those fill() writes, which refuses unless the record's item count is the W1 pins' (so the filled file's counts,
    equal to the W1 pins' by the first check, are the record's). Returns the filled document."""
    doc = s1.strict_json(filled_bytes)
    diff = differences(base.pins_doc, doc)
    if sorted(diff) != sorted(FILLED):
        shown = sorted(".".join(map(str, d)) for d in diff)
        raise s1.Refusal(f"the filled pins differ from the W1 pins in {shown}, not exactly in pools.decoy.sha256 and "
                         f"pools.plant.sha256")
    for name in POOLS:
        if doc["pools"][name]["sha256"] != record_pools[name]["sha256"]:
            raise s1.Refusal(f"the filled pin of pool {name} is {doc['pools'][name]['sha256']}, REQ-8's record gives "
                             f"{record_pools[name]['sha256']}")
    base.module.check_pool_pins(doc)
    if filled_bytes != canonical_json(fill(base.pins_doc, record_pools)):
        raise s1.Refusal("the filled pins file is not the canonical JSON of the filled document")
    return doc


def build_filled(base: Base, record_bytes: bytes, d2: dict) -> tuple[bytes, dict]:
    """(the filled pins file's bytes, the record's pools), every check passed."""
    pools = check_record(record_bytes, d2, base.entries)
    data = canonical_json(fill(base.pins_doc, pools))
    check_filled(base, data, pools)
    return data, pools


def load_d2() -> tuple[dict, str]:
    """This package's settings, refused unless they hash to SETTINGS_SHA256 (both read when called, not when defined)."""
    try:
        return s1.load_settings(SETTINGS_PATH, SETTINGS_SHA256, SETTINGS_NAME)
    except OSError as exc:
        raise s1.Refusal(f"the D-2 settings cannot be read ({type(exc).__name__})") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], allow_abbrev=False)
    parser.add_argument("--w1-pins", required=True, help="PATH:SHA256 of scripts/stage1/settings/representation_pools.json")
    parser.add_argument("--req8-record", required=True, help="PATH:SHA256 of REQ-8's plant_record.json")
    parser.add_argument("--out", type=Path, required=True, help="the filled pins file (must not exist)")
    args = parser.parse_args(argv)
    try:
        d2, _ = load_d2()
        w1_pins = parse_hashed(args.w1_pins, "--w1-pins")
        rec_path, rec_sha = parse_hashed(args.req8_record, "--req8-record")
        base = load_base(d2, w1_pins)
        data, pools = build_filled(base, read_hashed(rec_path, rec_sha, "REQ-8's record"), d2)
        out = args.out
        if out.exists() or out.is_symlink():
            raise s1.Refusal(f"{out} exists: the filled pins file is never overwritten")
        if not out.parent.is_dir():
            raise s1.Refusal(f"the folder of {out} does not exist")
        write_atomic(out, data)
        if read_hashed(out, sha256_bytes(data), "the written filled pins file") != data:
            raise s1.Refusal("the filled pins file did not read back as written")
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    print(f"D-2 filled pins {sha256_bytes(data)}  {out}")
    print(f"  from the W1 pins {base.pins_sha256} and REQ-8's record {rec_sha}")
    for name in POOLS:
        print(f"  {name}: sha256 {pools[name]['sha256']}, items {pools[name]['items']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
