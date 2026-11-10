"""T6b: a retrain unit's q and e1 adapter and optimizer fingerprints against a reference unit's (ruling 10, as the lead's
addendum A2 and A8 order it; Part 1 section 3.7; P78:82). Mac, standard library plus the engine's canonical JSON; $0.

    python -I -B scripts/scale78b/fingerprint_compare.py --retrain UNIT --reference UNIT
        [--expect-adapter q=HEX --expect-adapter e1=HEX] [--out FILE]

The rule. Each family's a0-1101 retrain (train only, recipe S_78, to q and e1; engine Y first) must reproduce the side
unit's q and e1 adapter AND optimizer fingerprints (ruling 10). Four values are compared: q adapter, q optimizer,
e1 adapter, e1 optimizer. All four equal: "equal" (Y = X for that family). Any other case: "differs" (the pre-set
second job, the X retrain; then ruling 7's fallback if X differs too). Nothing here decides which engine ran: the
code identities are printed as hashes so the lead's record can name them.

What is read of a unit: COMPLETE.json (``complete``, ``target_checkpoint``, ``identity``, ``checkpoints.<q|e1>``) and,
when present, states/<q|e1>/state.json, whose two fingerprints must equal COMPLETE.json's (a unit whose records
disagree refuses). No evaluation file, no answer, no text is opened. A fingerprint is 64 lower-case hex digits
(``experiments/safety_selection/engine.py`` tensor_fingerprint; COMPLETE.json's checkpoints block,
``runner.py`` :500-504). A unit that is not complete, holds error.txt, or lacks a q or e1 fingerprint refuses.

Printed: one line per fingerprint (checkpoint, kind, verdict, the two hashes); the code identity, training identity
and prepared manifest of both units (hashes; Y and X differ in the code identity by design, S_78 and the main recipe
share the training identity); the verdict. --out writes the same as a text-free canonical JSON record, created once,
never inside either unit. --expect-adapter pins the REFERENCE unit's adapter fingerprints to the pre-registered values
(P78:82's eight-digit abbreviations or the full 64 digits): a mismatch refuses, so the comparison is against the
registered side unit and not another folder. The two units must be different folders.

Exit 0 equal, 1 differs, 2 refused (nothing written).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402

KIND = "scale-78b fingerprint comparison"
RULE = ("ruling 10 (.ai/inputs/stage1-post-w1-20261023/78b/lead-rulings-part1-20261105.md section 10; addendum A2, A8); "
        "Part 1 section 3.7 (research/experiments/2026-11-05-78b-preregistration-part1.md); P78:82")
CHECKPOINTS = ("q", "e1")
FINGERPRINTS = ("adapter_fingerprint", "optimizer_fingerprint")
IDENTITY_FIELDS = ("code_sha256", "training_identity", "manifest_sha256", "recipe_sha256")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX_PREFIX = re.compile(r"^[0-9a-f]{8,64}$")
EQUAL, DIFFERS = "equal", "differs"


class Refusal(Exception):
    """The comparison cannot run as asked: nothing is written."""


def hex64(value) -> bool:
    return isinstance(value, str) and bool(HEX64.match(value))


def read_json(path: Path, what: str) -> dict:
    try:
        doc = json.loads(path.read_bytes())
    except OSError as exc:
        raise Refusal(f"{what}: {path.name} cannot be read ({type(exc).__name__})") from None
    except ValueError:
        raise Refusal(f"{what}: {path.name} is not JSON") from None
    if not isinstance(doc, dict):
        raise Refusal(f"{what}: {path.name} is not an object")
    return doc


def read_unit(folder: Path, what: str) -> dict:
    """The fingerprints and identity of one unit (module doc). Only COMPLETE.json and states/<c>/state.json are read."""
    folder = Path(folder)
    if not folder.is_dir():
        raise Refusal(f"{what}: {folder} is not a folder")
    if (folder / "error.txt").exists():
        raise Refusal(f"{what}: the unit holds error.txt")
    marker_path = folder / "COMPLETE.json"
    if not marker_path.is_file():
        raise Refusal(f"{what}: no COMPLETE.json (the unit is not complete)")
    marker_bytes = marker_path.read_bytes()
    marker = read_json(marker_path, what)
    if marker.get("complete") is not True:
        raise Refusal(f"{what}: COMPLETE.json does not say complete")
    checkpoints = marker.get("checkpoints")
    if not isinstance(checkpoints, dict):
        raise Refusal(f"{what}: COMPLETE.json has no checkpoints block")
    fingerprints: dict[str, dict[str, str]] = {}
    for c in CHECKPOINTS:
        entry = checkpoints.get(c)
        if not isinstance(entry, dict):
            raise Refusal(f"{what}: COMPLETE.json has no checkpoint {c!r} (a retrain to q and e1 is required)")
        values = {}
        for kind in FINGERPRINTS:
            value = entry.get(kind)
            if not hex64(value):
                raise Refusal(f"{what}: checkpoint {c} has no {kind} of 64 lower-case hex digits")
            values[kind] = value
        fingerprints[c] = values
    checked = []
    for c in CHECKPOINTS:
        state_path = folder / "states" / c / "state.json"
        if state_path.is_file():
            state = read_json(state_path, what)
            for kind in FINGERPRINTS:
                if state.get(kind) != fingerprints[c][kind]:
                    raise Refusal(f"{what}: states/{c}/state.json's {kind} disagrees with COMPLETE.json")
            checked.append(c)
    identity = marker.get("identity")
    if not isinstance(identity, dict):
        raise Refusal(f"{what}: COMPLETE.json has no identity block")
    ident = {}
    for field in IDENTITY_FIELDS:
        value = identity.get(field)
        if not hex64(value):
            raise Refusal(f"{what}: identity.{field} is not a 64-hex digest")
        ident[field] = value
    return {"folder": str(folder.resolve()), "complete_sha256": sha256_bytes(marker_bytes),
            "target_checkpoint": marker.get("target_checkpoint"), "identity": ident, "fingerprints": fingerprints,
            "state_records_checked": checked}


def parse_expect(specs: list[str]) -> dict[str, str]:
    """--expect-adapter q=HEX / e1=HEX: a prefix of at least 8 lower-case hex digits (P78:82's form) or the full 64."""
    out: dict[str, str] = {}
    for spec in specs:
        name, sep, value = spec.partition("=")
        if not sep or name not in CHECKPOINTS or not HEX_PREFIX.match(value):
            raise Refusal(f"--expect-adapter takes q=HEX or e1=HEX with 8 to 64 lower-case hex digits ({spec!r})")
        if name in out:
            raise Refusal(f"--expect-adapter repeats {name}")
        out[name] = value
    return out


def check_expect(reference: dict, expect: dict[str, str]) -> dict[str, str]:
    for c, prefix in expect.items():
        if not reference["fingerprints"][c]["adapter_fingerprint"].startswith(prefix):
            raise Refusal(f"the reference's {c} adapter fingerprint does not start with the expected {prefix[:8]}...: "
                          f"this is not the registered reference unit")
    return dict(expect)


def compare(retrain: dict, reference: dict, expect: dict[str, str] | None = None) -> dict:
    """The record (module doc): per fingerprint a verdict with both hashes; the identity lines; the verdict."""
    lines = []
    for c in CHECKPOINTS:
        for kind in FINGERPRINTS:
            a, b = retrain["fingerprints"][c][kind], reference["fingerprints"][c][kind]
            lines.append({"checkpoint": c, "kind": kind, "verdict": EQUAL if a == b else DIFFERS,
                          "retrain": a, "reference": b})
    equal = sum(1 for line in lines if line["verdict"] == EQUAL)
    identity = {field: {"retrain": retrain["identity"][field], "reference": reference["identity"][field],
                        "verdict": EQUAL if retrain["identity"][field] == reference["identity"][field] else DIFFERS}
                for field in IDENTITY_FIELDS}
    return {"kind": KIND, "version": 1, "rule": RULE,
            "compared": [f"{c} {kind}" for c in CHECKPOINTS for kind in FINGERPRINTS],
            "retrain": {k: retrain[k] for k in ("folder", "complete_sha256", "target_checkpoint", "state_records_checked")},
            "reference": {k: reference[k] for k in ("folder", "complete_sha256", "target_checkpoint", "state_records_checked")},
            "expected_reference_adapter_prefixes": dict(expect or {}),
            "fingerprints": lines, "equal": equal, "of": len(lines),
            "identity": identity,
            "verdict": EQUAL if equal == len(lines) else DIFFERS,
            "meaning": {EQUAL: "all four fingerprints equal: the retrain reproduces the reference (ruling 10: Y = X for "
                               "this family when the retrain ran on Y)",
                        DIFFERS: "a fingerprint differs: ruling 10's pre-set second job (the X retrain); ruling 7's "
                                 "fallback if X differs too"}[EQUAL if equal == len(lines) else DIFFERS]}


def out_ok(out: Path, units: list[Path]) -> Path:
    """--out is created once and never lies inside either unit (by resolved path and by directory identity of its
    deepest existing ancestor)."""
    out = out.resolve()
    if out.exists():
        raise Refusal(f"--out {out} exists: the record is created once")
    anchor = out
    while not anchor.exists() and anchor.parent != anchor:
        anchor = anchor.parent
    for unit in units:
        unit = unit.resolve()
        if out == unit or unit in out.parents:
            raise Refusal("--out must not lie inside a unit")
        if unit.exists() and any(os.path.samefile(p, unit) for p in (anchor, *anchor.parents)):
            raise Refusal("--out must not lie inside a unit")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--retrain", type=Path, required=True, help="the retrain unit's folder (COMPLETE.json inside)")
    parser.add_argument("--reference", type=Path, required=True, help="the reference unit's folder (the side unit)")
    parser.add_argument("--expect-adapter", action="append", default=[], metavar="q=HEX|e1=HEX",
                        help="the reference's pre-registered adapter fingerprint (a prefix of 8+ hex digits)")
    parser.add_argument("--out", type=Path, default=None, help="write the record here (created once; never inside a unit)")
    args = parser.parse_args(argv)
    try:
        if args.retrain.resolve() == args.reference.resolve() or (
                args.retrain.exists() and args.reference.exists() and os.path.samefile(args.retrain, args.reference)):
            raise Refusal("--retrain and --reference name the same folder")
        expect = parse_expect(args.expect_adapter)
        out = out_ok(args.out, [args.retrain, args.reference]) if args.out is not None else None
        retrain = read_unit(args.retrain, "retrain")
        reference = read_unit(args.reference, "reference")
        check_expect(reference, expect)
        record = compare(retrain, reference, expect)
        data = canonical_json(record)
        if out is not None:
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "xb") as handle:
                handle.write(data)
    except Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    for line in record["fingerprints"]:
        print(f"{line['checkpoint']:>2} {line['kind']:<21} {line['verdict']:<7} retrain {line['retrain']}  reference {line['reference']}")
    for field, entry in record["identity"].items():
        print(f"   {field:<19} {entry['verdict']:<7} retrain {entry['retrain']}  reference {entry['reference']}")
    print(f"verdict: {record['verdict']} ({record['equal']} of {record['of']} fingerprints equal)")
    if out is not None:
        print(f"record {sha256_bytes(data)} {out}")
    return 0 if record["verdict"] == EQUAL else 1


if __name__ == "__main__":
    sys.exit(main())
