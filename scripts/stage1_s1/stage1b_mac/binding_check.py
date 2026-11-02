"""The binding check (addendum section 40 point 5, second bullet; CHECK section 5.2 item 6): a key-only script that
confirms that REQ-8's record (the record scripts/stage1/build_plant.py writes; its ``edits`` list holds one
{file, sha256, ...} entry per edit, build_plant.py Writer.write) lists, for ``edits/planted_k37.json``, the SHA-256 the
lead computed from the edit file without showing a byte (its name field names the leaf). The record's own SHA-256 is
checked against the pin the lead gives (stage1_rules.D2_REQ8_RECORD, FOCUS "plant/plant_record.json cc04b663…").

    python -B -m scripts.stage1_s1.stage1b_mac.binding_check --record FILE --expect-record-sha256 H --edit-sha256 H \\
        [--edit-file edits/planted_k37.json]

Printed: "match" (exit 0) or "no match" (exit 1); a refusal (exit 2) is a fixed message. No other field of the record
is printed or written: the record names the drawn unit and leaf (build_plant.py:442).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.stage1_s1.stage1b_mac.common import Refusal, is_hex64, json_object, read_pinned, run_frame

RECORD_KIND = "stage1 plant record"            # build_plant.py: record["kind"]
EDIT_FILE = "edits/planted_k37.json"          # build_plant.py: f"edits/{name}.json" for name planted_k37
EDIT_KEYS = ("file", "sha256")                # the two keys read of an edits entry


def listed_sha256(record: dict, edit_file: str) -> str:
    """The SHA-256 the record lists for ``edit_file``: exactly one entry of ``edits`` names it."""
    if record.get("kind") != RECORD_KIND:
        raise Refusal("the record is not REQ-8's plant record")
    edits = record.get("edits")
    if not isinstance(edits, list) or not all(isinstance(e, dict) for e in edits):
        raise Refusal("the record holds no edits list")
    found = [e for e in edits if e.get(EDIT_KEYS[0]) == edit_file]
    if len(found) != 1:
        raise Refusal("the record lists no single entry for the edit file")
    digest = found[0].get(EDIT_KEYS[1])
    if not is_hex64(digest):
        raise Refusal("the record's entry for the edit file names no SHA-256")
    return digest


def check(record_path, expect_record: str, edit_sha256: str, edit_file: str = EDIT_FILE) -> bool:
    if not is_hex64(expect_record):
        raise Refusal("--expect-record-sha256 is not 64 lowercase hex")
    if not is_hex64(edit_sha256):
        raise Refusal("--edit-sha256 is not 64 lowercase hex")
    record = json_object(read_pinned(record_path, expect_record, "the record"), "the record")
    return listed_sha256(record, edit_file) == edit_sha256


def main(argv=None) -> int:
    def produce(argv):
        parser = argparse.ArgumentParser(prog="python -B -m scripts.stage1_s1.stage1b_mac.binding_check",
                                         description=__doc__.split("\n\n")[0])
        parser.add_argument("--record", required=True)
        parser.add_argument("--expect-record-sha256", required=True)
        parser.add_argument("--edit-sha256", required=True)
        parser.add_argument("--edit-file", default=EDIT_FILE)
        args = parser.parse_args(argv)
        if check(Path(args.record), args.expect_record_sha256, args.edit_sha256, args.edit_file):
            print("match")
            return 0
        print("no match")
        return 1
    return run_frame(produce, argv)


if __name__ == "__main__":
    raise SystemExit(main())
