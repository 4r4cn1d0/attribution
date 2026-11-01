"""Reads ONE value from a sealed a0 unit under the seal rule's fingerprint clause (the lead's ruling of 29 Oct 2026,
route (a) for seed 1104; B15 brief G5: "after block A only cost ledgers, completion records and adapter fingerprints
are read"): the e1 adapter fingerprint, key path ``adapter_fingerprint`` at the top level of the unit's
``states/e1/state.json`` (the engine's save_state record, experiments/safety_selection/engine.py save_state). No
other field of any unit file is printed or written.

    python -B scripts/stage1_s1/extract_a0_fingerprint.py --unit-folder KIT/retrieved/HOST/tree/round1/S-a0-e1-aN \
        --expect-complete-sha256 H --seal KIT/seals/block-X.json --expect-seal-sha256 H2 --out-dir DIR

Before anything is parsed: the seal file hashes to H2 (plan.json seals.X.sha256); the unit folder lies at
retrieved/HOST/tree/REL with REL's last part S-a0-e1-aN; the seal lists exactly one sealed entry for HOST's
REL/COMPLETE.json and one for REL/states/e1/state.json; the unit's COMPLETE.json hashes to H and to its seal entry (it
is hashed only, never parsed); state.json hashes to its seal entry. Then state.json is parsed in memory and only
``adapter_fingerprint`` (64 lowercase hex) is taken. It writes DIR/a0-S-adapter-fingerprint.json once (DIR must
exist; an existing record is never overwritten; the name is one the seal classes as readable), holding exactly
{kind, unit, complete_sha256, state_sha256, fingerprint, seal_sha256, utc, script_sha256}, and prints the record's
path and SHA-256 only. A refusal names no value of the unit's files. Exit: 0 written; 2 refused (nothing written).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Sequence

KIND = "stage1 a0 adapter fingerprint extract"
KEY_PATH = "adapter_fingerprint"                      # states/e1/state.json, top level
UNIT_NAME = re.compile(r"^(\d{4})-a0-e1-a\d+$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Refusal(Exception):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(path: Path, what: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        raise Refusal(f"{what} cannot be read") from None


def _sealed(entries: list, host: str, rel: str) -> str:
    found = [e for e in entries if isinstance(e, dict) and e.get("host") == host and e.get("path") == rel]
    if len(found) != 1 or found[0].get("class") != "sealed" or not HEX64.match(str(found[0].get("sha256"))):
        raise Refusal(f"the seal lists no single sealed entry with a SHA-256 for {host} {rel}")
    return found[0]["sha256"]


def extract(*, unit_folder: Path, expect_complete: str, seal: Path, expect_seal: str, out_dir: Path) -> Path:
    seal_bytes = _read(seal, "the seal file")
    if sha(seal_bytes) != expect_seal:
        raise Refusal("the seal file does not hash to the expected seal SHA-256")
    parts = unit_folder.parts
    if "retrieved" not in parts or parts.index("retrieved") + 2 >= len(parts) - 1 \
            or parts[parts.index("retrieved") + 2] != "tree":
        raise Refusal("the unit folder is not KIT/retrieved/HOST/tree/REL")
    host, rel = parts[parts.index("retrieved") + 1], "/".join(parts[parts.index("retrieved") + 3:])
    match = UNIT_NAME.match(unit_folder.name)
    if match is None:
        raise Refusal("the unit folder is not an a0 e1 unit (S-a0-e1-aN)")
    try:
        entries = json.loads(seal_bytes)["files"]
    except (ValueError, KeyError, TypeError):
        raise Refusal("the seal file is not a seal record") from None
    complete = sha(_read(unit_folder / "COMPLETE.json", "the unit's COMPLETE.json"))      # hashed, never parsed
    if complete != expect_complete or complete != _sealed(entries, host, f"{rel}/COMPLETE.json"):
        raise Refusal("the unit's COMPLETE.json is not the expected and sealed one")
    state_bytes = _read(unit_folder / "states" / "e1" / "state.json", "the unit's states/e1/state.json")
    state_sha = sha(state_bytes)
    if state_sha != _sealed(entries, host, f"{rel}/states/e1/state.json"):
        raise Refusal("the unit's states/e1/state.json is not the sealed one")
    try:
        fingerprint = json.loads(state_bytes)[KEY_PATH]
    except (ValueError, KeyError, TypeError):
        raise Refusal(f"states/e1/state.json holds no top-level {KEY_PATH}") from None
    if not (isinstance(fingerprint, str) and HEX64.match(fingerprint)):
        raise Refusal(f"states/e1/state.json's {KEY_PATH} is not 64 lowercase hex")
    if not out_dir.is_dir():
        raise Refusal("the output folder does not exist")
    record = {"kind": KIND, "unit": rel, "complete_sha256": complete, "state_sha256": state_sha,
              "fingerprint": fingerprint, "seal_sha256": expect_seal,
              "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "script_sha256": sha(Path(__file__).resolve().read_bytes())}
    path = out_dir / f"a0-{match.group(1)}-adapter-fingerprint.json"
    try:
        with open(path, "xb") as handle:                                               # never overwrites
            handle.write((json.dumps(record, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    except FileExistsError:
        raise Refusal(f"{path.name} exists in the output folder: it is written once") from None
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="extract_a0_fingerprint.py", description=__doc__.split("\n\n")[0])
    for name in ("--unit-folder", "--expect-complete-sha256", "--seal", "--expect-seal-sha256", "--out-dir"):
        parser.add_argument(name, required=True)
    args = parser.parse_args(argv)
    try:
        path = extract(unit_folder=Path(args.unit_folder), expect_complete=args.expect_complete_sha256,
                       seal=Path(args.seal), expect_seal=args.expect_seal_sha256, out_dir=Path(args.out_dir))
    except Refusal as exc:
        print(json.dumps({"ok": False, "refused": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({"written": str(path), "sha256": sha(path.read_bytes())}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
