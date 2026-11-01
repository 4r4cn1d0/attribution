"""C3's bank-subsample file (addendum section 22 point 2, Q13; section 15 point 5; B15 J14).
Mac, CPU, $0, engine X; the lead runs it once on P. It prints counts and hashes only.

What it reads. P's manifest.json and manifest.sha256 (the engine's own read_manifest: the manifest must hash to its
frozen hash and to the pin in settings/write_c3_subsample.json, 9ed61826...), then banks/dev.jsonl after its manifest
hash verifies (the engine's own read_verified). It never opens the hidden bank, the selector bank, the training or
query rows, the groups or any other prepared file.

The rule (no random draw, so no seed label is added): the first n_items (16) items of the dev bank, in the file's own
line order, each copied whole (every field, the token fields included), no filter by kind and no re-sorting. The dev
bank's ids must be distinct non-empty strings and every item must carry a string kind (engine Y refuses otherwise);
fewer than 16 items refuse.

The file is engine Y's Y2 subsample format (experiments/safety_selection/jobs.py read_bank_subsample and
subsample_items in engine round Y): canonical JSON with exactly the keys counts, draw, items, kind, source, tokenizer
and version; kind "safety-selection bank subsample", version 1; tokenizer = the data config's repo_id and revision;
source = {manifest_sha256: P's, bank: "dev", bank_file_sha256: the manifest's hash of banks/dev.jsonl}; draw =
{label: the settings' draw_label, script_sha256: this file's SHA-256, settings_sha256: the settings' SHA-256}; counts
= items by kind. Its job names evaluate_bank = subsample-<SHA-256 of the file's bytes>, the development role (a
dev-sourced file is the development role's only subsample; edit_confirmation may also use it).

Outputs. --out: the subsample file (it holds dev-bank text, so it must lie in a folder named tmp). --record: a
text-free record (the file's SHA-256 and bank id, the rule, the item count and counts by kind, the source, draw and
tokenizer blocks, P's manifest SHA-256, the dev bank's item count, and the stage-1 provenance block). The record's
bytes are scanned for every text value of the 16 items before anything is written. Both paths must be new: an
existing file at either refuses, and each is created exclusively (os.link), never overwritten.
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.prepare import BANK_FILES, read_manifest, read_verified  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "write_c3_subsample.json"
SETTINGS_SHA256 = "a8547e2dcd27cbbdbed48eef3cb636a4503a6f3d6101123080b26b9baa1cfc60"
SETTINGS_NAME = "write_c3_subsample"
SUBSAMPLE_PREFIX = "subsample-"
SUBSAMPLE_KIND, SUBSAMPLE_VERSION = "safety-selection bank subsample", 1
SUBSAMPLE_KEYS = ("counts", "draw", "items", "kind", "source", "tokenizer", "version")   # = engine Y jobs.SUBSAMPLE_KEYS
SOURCE_BANK = "dev"
ROLE = "development"
RECORD_KIND = "stage1 c3 subsample record"
CONSTANT_RECORD_KEYS = ("decision", "reference", "rule")      # copied from the settings, fixed before any data is read


def check_c3_settings(settings: dict) -> dict:
    """The C3 settings' own fields: a positive item count, the dev source, the development role, P's pin, a label."""
    s1.check_settings(settings, SETTINGS_NAME)
    n = settings.get("n_items")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise s1.Refusal("settings n_items is not a positive integer")
    if settings.get("source_bank") != SOURCE_BANK or settings.get("role") != ROLE:
        raise s1.Refusal(f"C3's subsample is {SOURCE_BANK}-sourced for the {ROLE} role only")
    pin = settings.get("prepared_manifest_sha256")
    if not isinstance(pin, str) or not s1.HEX64.match(pin):
        raise s1.Refusal("settings prepared_manifest_sha256 is not a SHA-256")
    if not isinstance(settings.get("draw_label"), str) or not settings["draw_label"]:
        raise s1.Refusal("settings draw_label is not a non-empty string")
    for key in CONSTANT_RECORD_KEYS:
        if not isinstance(settings.get(key), str) or not settings[key]:
            raise s1.Refusal(f"settings {key} is not a non-empty string")
    return settings


def read_dev_bank(prepared_root: Path, pin: str) -> tuple[dict, str, list[dict]]:
    """(P's manifest, its SHA-256, the dev bank's items in file order); only the manifest and the dev bank are read."""
    try:
        manifest, digest = read_manifest(prepared_root, pin)
        data = read_verified(prepared_root, manifest, BANK_FILES[SOURCE_BANK])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise s1.Refusal(f"P's manifest or dev bank does not verify ({type(exc).__name__})") from None
    items = list(s1.iter_jsonl_bytes(data, BANK_FILES[SOURCE_BANK]))
    seen: set[str] = set()
    for k, item in enumerate(items):
        if not (isinstance(item.get("prompt_id"), str) and item["prompt_id"] and isinstance(item.get("kind"), str)):
            raise s1.Refusal(f"dev bank item {k}: no non-empty string prompt_id and string kind")
        if item["prompt_id"] in seen:
            raise s1.Refusal(f"dev bank item {k}: its prompt_id is repeated")
        seen.add(item["prompt_id"])
    return manifest, digest, items


def item_texts(items: list[dict]) -> list[str]:
    """Every string value inside the items (nested lists and objects too), except ids, kind names and SHA-256s."""
    kinds = {item["kind"] for item in items}
    out: list[str] = []

    def walk(value, key=None):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, k)
        elif isinstance(value, list):
            for v in value:
                walk(v, key)
        elif isinstance(value, str) and key not in ("prompt_id", "kind") and value not in kinds \
                and not s1.HEX64.match(value):
            out.append(value)

    for item in items:
        walk(item)
    return out


def build(*, prepared_root: Path, settings: dict, settings_sha256: str,
          script: Path = Path(__file__).resolve()) -> tuple[bytes, bytes]:
    """(the subsample file's bytes, the record's bytes); nothing is written here."""
    check_c3_settings(settings)
    n = settings["n_items"]
    manifest, manifest_sha256, bank = read_dev_bank(Path(prepared_root), settings["prepared_manifest_sha256"])
    if len(bank) < n:
        raise s1.Refusal(f"P's dev bank holds {len(bank)} items, fewer than the {n} C3 needs (nothing written; "
                         "section 22 point 2's fallback: C3's smoke is dropped)")
    items = copy.deepcopy(bank[:n])
    counts: dict[str, int] = {}
    for item in items:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    tok = manifest.get("data_config", {}).get("tokenizer") if isinstance(manifest.get("data_config"), dict) else None
    if not (isinstance(tok, dict) and isinstance(tok.get("repo_id"), str) and isinstance(tok.get("revision"), str)):
        raise s1.Refusal("P's data config names no tokenizer repo_id and revision")
    bank_file_sha256 = manifest["files"][BANK_FILES[SOURCE_BANK]]
    script_sha256 = sha256_file(script)
    doc = {"kind": SUBSAMPLE_KIND, "version": SUBSAMPLE_VERSION,
           "tokenizer": {"repo_id": tok["repo_id"], "revision": tok["revision"]},
           "source": {"manifest_sha256": manifest_sha256, "bank": SOURCE_BANK, "bank_file_sha256": bank_file_sha256},
           "draw": {"label": settings["draw_label"], "script_sha256": script_sha256, "settings_sha256": settings_sha256},
           "items": items, "counts": counts}
    data = canonical_json(doc)
    back = s1.strict_json(data)
    if sorted(back) != list(SUBSAMPLE_KEYS) or canonical_json(back) != data \
            or [i["prompt_id"] for i in back["items"]] != [i["prompt_id"] for i in bank[:n]] \
            or back["items"] != bank[:n]:
        raise s1.Refusal("the subsample file does not read back as the first items of the dev bank")
    digest = sha256_bytes(data)
    record = {
        "kind": RECORD_KIND, "version": 1, "name": SETTINGS_NAME,
        "rule": settings["rule"], "reference": settings["reference"], "decision": settings["decision"],
        "role": ROLE,
        "subsample": {"file_sha256": digest, "bank": SUBSAMPLE_PREFIX + digest, "bytes": len(data), "items": n,
                      "counts": counts},
        "source": doc["source"], "draw": doc["draw"], "tokenizer": doc["tokenizer"],
        "prepared_manifest_sha256": manifest_sha256, "dev_bank_items": len(bank),
        "provenance": s1.provenance(script, settings_sha256,
                                    {"prepared_manifest": manifest_sha256, "dev_bank": bank_file_sha256}, {}),
    }
    record_bytes = canonical_json(record)
    scanned = canonical_json({k: v for k, v in record.items() if k not in CONSTANT_RECORD_KEYS})
    if s1._text_hits(scanned, item_texts(items)):
        raise s1.Refusal("the record would hold dev-bank text")
    return data, record_bytes


def check_outputs(prepared: Path, out: Path, record: Path) -> tuple[Path, Path]:
    """--out inside a folder named tmp; neither path exists (a symlink, dangling or not, counts as existing: the last
    component is never resolved, so nothing is written through a link), they differ, and neither lies inside P."""
    given = (Path(os.path.abspath(out)), Path(os.path.abspath(record)))
    for path in given:
        if path.exists() or path.is_symlink():
            raise s1.Refusal(f"{path.name} exists: an output is never overwritten")
    out, record = (p.parent.resolve() / p.name for p in given)
    prepared = prepared.resolve()
    if "tmp" not in out.parent.parts:
        raise s1.Refusal("--out must lie in a folder named tmp: the subsample file holds dev-bank text")
    if out == record:
        raise s1.Refusal("--out and --record are the same path")
    for path in (out, record):
        if path == prepared or prepared in path.parents:
            raise s1.Refusal("an output lies inside the prepared folder")
    return out, record


def write_new(path: Path, data: bytes) -> str:
    """Create path exclusively (a temporary file, then os.link, which refuses an existing path) and read it back."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(tmp, path)
    except FileExistsError:
        raise s1.Refusal(f"{path.name} exists: an output is never overwritten") from None
    finally:
        tmp.unlink(missing_ok=True)
    digest = sha256_file(path)
    if digest != sha256_bytes(data):
        raise s1.Refusal(f"{path.name} did not read back as written")
    return digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True, help="P, the prepared folder")
    parser.add_argument("--out", type=Path, required=True, help="the subsample file (inside a folder named tmp)")
    parser.add_argument("--record", type=Path, required=True, help="the text-free record")
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH, help="C3's settings (pinned by SHA-256)")
    args = parser.parse_args(argv)
    written: list[Path] = []
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        out, record_path = check_outputs(args.prepared, args.out, args.record)
        data, record = build(prepared_root=args.prepared, settings=settings, settings_sha256=digest)
        file_sha = write_new(out, data)
        written.append(out)
        record_sha = write_new(record_path, record)
        written.append(record_path)
    except (s1.Refusal, OSError) as exc:
        state = f"{len(written)} file(s) written: {[p.name for p in written]}" if written else "nothing written"
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} ({state})", file=sys.stderr)
        return 2
    doc = s1.strict_json(record)
    print(f"C3 subsample: {doc['subsample']['items']} of {doc['dev_bank_items']} dev items; counts "
          f"{doc['subsample']['counts']}; P manifest {doc['prepared_manifest_sha256']}")
    print(f"evaluate_bank {doc['subsample']['bank']}")
    print(f"  {file_sha}  {out.name}")
    print(f"  {record_sha}  {record_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
