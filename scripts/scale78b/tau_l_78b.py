"""τ_L of one 7-8B family from its a0 units' task losses only (Mac, standard library plus the engine's canonical JSON;
$0; DES K2; GXB O9).

    PY -I -B scripts/scale78b/tau_l_78b.py --family F --unit 1101=FOLDER:SHA256 --unit 1102=FOLDER:SHA256
        --unit 1103=FOLDER:SHA256 [--out REC.json]

**The rule** (Part 2 section 4.7, citing PR4:589-595 and S1B REQ-19; PR4 section 6.7, ADD-L16): τ_L = 2√2 × s, with s
the sample SD (ddof 1) over the family's a0 seeds 1101-1103 of each a0 unit's mean per-example query loss on the 200
task rows at e1. The mean is ``math.fsum`` over the 200 losses divided by 200, and must equal the mean the unit's
COMPLETE.json records (``evaluation.query_loss.mean``) exactly, as REQ-19 required (``scripts/stage1/limits/
limits_check.py`` :388-393); s is ``statistics.stdev`` (ddof 1; limits_check.py :325-330).

**The units** (Part 2 section 4.7's table): OLMo-2-7B's side a0 units 1101, 1102, 1103 and Llama-3.1-8B's side a0
units 1101, 1102 by their COMPLETE.json SHA-256 (R: runkit/stage1-78b/rules_78b.py:211-216, :232-235; P1 section 2.1),
and Llama-3.1-8B's N a0-1103, whose COMPLETE.json SHA-256 does not exist yet: for it alone the pin is the one the
command line names. Each --unit is SEED=FOLDER:SHA256 (the folder holds COMPLETE.json); a pin that is not the family's
literal pin refuses.

**What is read** of a unit: COMPLETE.json (its bytes hash to the pin), then ``eval/e1/query_loss.jsonl`` at the SHA-256
that COMPLETE.json lists for it. Nothing else is opened: no guard label, no summary, no answer, no state. Of
COMPLETE.json: ``complete``, ``target_checkpoint`` (e1), ``trajectory.arm`` (a0) and ``trajectory.seed``,
``identity.training_identity`` and ``identity.manifest_sha256`` (the family's: P78 section 2.3 condition 2; R:
rules_78b.py:110-111, :205, :226), ``files``, and ``evaluation`` (``checkpoint`` e1; ``query_loss.n`` 200,
``query_loss.mean``, ``query_loss.query_bank_sha256``, which must be the same for every unit). Of query_loss.jsonl:
``query_id`` and ``loss`` only (every other field is dropped unread); the 200 ids must be distinct and the same for
every unit, every loss a finite number. A folder holding error.txt (a preserved failure) refuses (checked by name, not
opened).

**Output.** Printed and written: s, n (the number of units), ddof, τ_L and the input hashes (each unit's COMPLETE.json
and query_loss.jsonl SHA-256, the query bank's SHA-256); no per-unit loss. --out writes a text-free canonical JSON
record, created once and complete or not at all, never inside a unit. Exit 0: computed (and written); 2: refused, nothing written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

KIND = "scale78b tau_L"
RULE = ("Part 2 section 4.7 (research/experiments/2026-11-06-78b-preregistration-part2.md; DES K2); PR4 section 6.7 "
        "(research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md:589-595; ADD-L16; "
        "REQ-19's form, scripts/stage1/limits/limits_check.py); GXB O9 (losses only)")
FAMILIES = ("olmo2-7b", "llama31-8b")
SEEDS = (1101, 1102, 1103)
CHECKPOINT, ARM, ROWS, DDOF = "e1", "a0", 200, 1
LOSS_FILE = f"eval/{CHECKPOINT}/query_loss.jsonl"
# The a0 units' COMPLETE.json SHA-256 (R: rules_78b.py KIT[F]["a0_units"], :211-216 and :232-235; Part 2 section 4.7).
# None: Llama's N a0-1103 (block 0), pinned on the command line when its record-done exists.
UNIT_PINS: dict[str, dict[int, str | None]] = {
    "olmo2-7b": {1101: "4a6d9ebc6636de57d52ec1b9cc1cd82afb1bdbfbf2a70e3f9884d3e9404d6dfc",
                 1102: "43e8412dc7ef8d3eb017340a788e08041623bce8b3896a750d6cc50e10e282c4",
                 1103: "4b5bd06dede08dc14f3ab5de201b7618ada94a0515896ed23c04b3af7ca44fa0"},
    "llama31-8b": {1101: "21427715565fb394220a068c8991b8f6819c4773ccf82b0cd7c35fe3788bc22a",
                   1102: "b0c99f7b97e6e76355383644ee50f9cbef33c25e09585a9a0d030712d4aa75d9",
                   1103: None},
}
# The family's training identity and prepared manifest (R: rules_78b.py:205, :226, :110-111; P78 section 2.3).
TRAINING_IDENTITY = {"olmo2-7b": "36738c3823fae7eaca625cc9f619e98c7e40b9bb64e5d0e234412827d3371ec6",
                     "llama31-8b": "5b4451e1487fb2200a5b2b151de2e68397117099a429654484146b3cc3791287"}
MANIFESTS = {"olmo2-7b": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9",
             "llama31-8b": "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"}
HEX = "0123456789abcdef"


class Refusal(Exception):
    """τ_L cannot be computed as asked: nothing is written. Messages hold seeds, counts and hashes only."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in HEX for c in value)


def _no_duplicates(pairs: list) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("a repeated key")
        out[key] = value
    return out


def _no_constant(name: str) -> Any:
    raise ValueError("a non-finite constant")


def strict_json(data: bytes, what: str) -> Any:
    try:
        return json.loads(data, object_pairs_hook=_no_duplicates, parse_constant=_no_constant)
    except ValueError:
        raise Refusal(f"{what} is not strict JSON") from None


def read_file(path: Path, what: str) -> bytes:
    """The one place a file is opened."""
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        raise Refusal(f"{what} cannot be read ({type(exc).__name__})") from None


def parse_units(specs: Sequence[str], family: str, pins: Mapping[int, str | None] | None = None
                ) -> dict[int, tuple[Path, str]]:
    """--unit SEED=FOLDER:SHA256, exactly the seeds 1101, 1102, 1103, each pin the family's literal one (or, for a seed
    whose literal is None, any 64-hex pin)."""
    out: dict[int, tuple[Path, str]] = {}
    for spec in specs:
        seed_text, sep, rest = spec.partition("=")
        folder, sep2, digest = rest.rpartition(":")
        if not sep or not sep2 or not folder or not seed_text.isdigit() or not hex64(digest):
            raise Refusal("--unit is SEED=FOLDER:SHA256 with 64 lower-case hex digits")
        seed = int(seed_text)
        if seed not in SEEDS:
            raise Refusal(f"--unit seed {seed} is not one of {', '.join(map(str, SEEDS))}")
        if seed in out:
            raise Refusal(f"--unit names seed {seed} twice")
        pin = (UNIT_PINS[family] if pins is None else pins)[seed]
        if pin is not None and digest != pin:
            raise Refusal(f"--unit {seed}: the command line names {digest}; {family}'s a0-{seed} is {pin}")
        out[seed] = (Path(folder), digest)
    missing = [s for s in SEEDS if s not in out]
    if missing:
        raise Refusal(f"--unit needs seed {', '.join(map(str, missing))} too")
    return out


def read_unit(family: str, seed: int, folder: Path, pin: str) -> dict:
    """One unit's mean query loss at e1 and its hashes (module doc: what is read)."""
    what = f"unit {seed}"
    folder = Path(folder)
    if (folder / "error.txt").exists():
        raise Refusal(f"{what}: the folder holds error.txt (a preserved failure)")
    marker_bytes = read_file(folder / "COMPLETE.json", f"{what}: COMPLETE.json")
    complete_sha = sha256_bytes(marker_bytes)
    if complete_sha != pin:
        raise Refusal(f"{what}: COMPLETE.json hashes to {complete_sha}; the pin is {pin}")
    marker = strict_json(marker_bytes, f"{what}: COMPLETE.json")
    if not isinstance(marker, dict) or marker.get("complete") is not True or not isinstance(marker.get("files"), dict):
        raise Refusal(f"{what}: COMPLETE.json is not a complete marker with a file list")
    trajectory = marker.get("trajectory") if isinstance(marker.get("trajectory"), dict) else {}
    if marker.get("target_checkpoint") != CHECKPOINT:
        raise Refusal(f"{what}: COMPLETE.json's target_checkpoint is not {CHECKPOINT}")
    if trajectory.get("arm") != ARM or trajectory.get("seed") != seed:
        raise Refusal(f"{what}: COMPLETE.json's trajectory is not arm {ARM} at seed {seed}")
    identity = marker.get("identity") if isinstance(marker.get("identity"), dict) else {}
    if identity.get("training_identity") != TRAINING_IDENTITY[family]:
        raise Refusal(f"{what}: COMPLETE.json's training identity is not {family}'s")
    if identity.get("manifest_sha256") != MANIFESTS[family]:
        raise Refusal(f"{what}: COMPLETE.json's prepared manifest is not {family}'s")
    evaluation = marker.get("evaluation") if isinstance(marker.get("evaluation"), dict) else {}
    ql = evaluation.get("query_loss") if isinstance(evaluation.get("query_loss"), dict) else {}
    if evaluation.get("checkpoint") != CHECKPOINT or ql.get("n") != ROWS:
        raise Refusal(f"{what}: COMPLETE.json's evaluation is not checkpoint {CHECKPOINT} over {ROWS} task rows")
    recorded, bank = ql.get("mean"), ql.get("query_bank_sha256")
    if isinstance(recorded, bool) or not isinstance(recorded, (int, float)) or not math.isfinite(recorded):
        raise Refusal(f"{what}: COMPLETE.json's recorded mean query loss is not a finite number")
    if not hex64(bank):
        raise Refusal(f"{what}: COMPLETE.json names no query bank SHA-256")
    listed = marker["files"].get(LOSS_FILE)
    if not hex64(listed):
        raise Refusal(f"{what}: COMPLETE.json does not list {LOSS_FILE}")
    loss_bytes = read_file(folder / LOSS_FILE, f"{what}: {LOSS_FILE}")
    loss_sha = sha256_bytes(loss_bytes)
    if loss_sha != listed:
        raise Refusal(f"{what}: {LOSS_FILE} hashes to {loss_sha}; COMPLETE.json lists {listed}")
    losses: dict[str, float] = {}
    for number, line in enumerate(loss_bytes.splitlines(), 1):
        record = strict_json(line, f"{what}: {LOSS_FILE} line {number}")
        if not isinstance(record, dict):
            raise Refusal(f"{what}: {LOSS_FILE} line {number} is not an object")
        qid, loss = record.get("query_id"), record.get("loss")
        del record                                            # every other field is dropped unread
        if not isinstance(qid, str) or qid in losses:
            raise Refusal(f"{what}: {LOSS_FILE} line {number} holds no query id or a repeated one")
        if isinstance(loss, bool) or not isinstance(loss, (int, float)) or not math.isfinite(loss):
            raise Refusal(f"{what}: {LOSS_FILE} line {number}'s loss is not a finite number")
        losses[qid] = float(loss)
    if len(losses) != ROWS:
        raise Refusal(f"{what}: {LOSS_FILE} holds {len(losses)} rows, not {ROWS}")
    mean = math.fsum(losses.values()) / len(losses)
    if mean != recorded:
        raise Refusal(f"{what}: the recomputed mean query loss differs from COMPLETE.json's")
    return {"seed": seed, "complete_sha256": complete_sha, "query_loss_sha256": loss_sha, "query_bank_sha256": bank,
            "query_ids": sorted(losses), "mean": mean}


def tau_l(family: str, units: Mapping[int, tuple[Path, str]], pins: Mapping[int, str | None] | None = None) -> dict:
    """The record (module doc): s, n, ddof, τ_L and the input hashes; no per-unit loss."""
    pins = UNIT_PINS[family] if pins is None else pins
    read = [read_unit(family, seed, *units[seed]) for seed in SEEDS]
    banks = {u["query_bank_sha256"] for u in read}
    if len(banks) != 1:
        raise Refusal("the units do not all name the same query bank")
    if any(u["query_ids"] != read[0]["query_ids"] for u in read):
        raise Refusal("the units do not hold the same task rows")
    s = statistics.stdev([u["mean"] for u in read])
    return {"kind": KIND, "version": 1, "family": family, "rule": RULE,
            "n": len(read), "ddof": DDOF, "rows": ROWS, "checkpoint": CHECKPOINT, "s": s,
            "tau_l": 2 * math.sqrt(2) * s,
            "inputs": {str(u["seed"]): {"complete_sha256": u["complete_sha256"],
                                        "query_loss_sha256": u["query_loss_sha256"],
                                        "pin_source": ("literal" if pins[u["seed"]] is not None
                                                       else "command line (N's unit; no literal pin yet)")}
                       for u in read},
            "query_bank_sha256": banks.pop(),
            "read": f"COMPLETE.json and {LOSS_FILE} of each unit only (no guard label, no summary, no answer)",
            "provenance": {"script": "scripts/scale78b/tau_l_78b.py",
                           "script_sha256": sha256_bytes(Path(__file__).read_bytes())}}


def out_ok(out: Path, units: Sequence[Path]) -> Path:
    """--out is a new file whose folder exists and lies inside no unit (by path and by directory identity)."""
    out = Path(out).resolve()
    if out.exists() or out.is_symlink():
        raise Refusal(f"--out {out.name} exists: the record is created once")
    parent = out.parent
    if not parent.is_dir():
        raise Refusal("--out's folder does not exist")
    for unit in units:
        unit = Path(unit).resolve()
        if not unit.exists():
            continue
        for anchor in (parent, *parent.parents):
            if anchor == unit or os.path.samefile(anchor, unit):
                raise Refusal("--out must not lie inside a unit")
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


def main(argv: list[str] | None = None, *, unit_pins: Mapping[int, str | None] | None = None) -> int:
    """The command line. ``unit_pins`` is an ENGINEERING FIXTURE for tests only (fixture units' pins); the real run
    uses UNIT_PINS."""
    from experiments.safety_selection.common import canonical_json

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--family", required=True, choices=FAMILIES)
    parser.add_argument("--unit", action="append", default=[], help="SEED=FOLDER:SHA256 (COMPLETE.json's SHA-256)")
    parser.add_argument("--out", type=Path, default=None, help="the record (a new file)")
    args = parser.parse_args(argv)
    try:
        units = parse_units(args.unit, args.family, unit_pins)
        out = out_ok(args.out, [u for u, _ in units.values()]) if args.out is not None else None
        doc = tau_l(args.family, units, unit_pins)
        data = canonical_json(doc)
        if out is not None:
            write_once(out, data)
    except Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    except (Exception, SystemExit) as exc:     # no traceback, no message: the class name only
        print(f"REFUSED: {type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    print(f"{doc['family']}: n {doc['n']} a0 units (seeds {', '.join(map(str, SEEDS))}) at {CHECKPOINT}, "
          f"{ROWS} task rows each; s (ddof {DDOF}) {doc['s']!r} nats; tau_L = 2*sqrt(2)*s = {doc['tau_l']!r} nats")
    for seed, entry in doc["inputs"].items():
        print(f"  {seed}: COMPLETE.json {entry['complete_sha256']}; query_loss.jsonl {entry['query_loss_sha256']} "
              f"({entry['pin_source']})")
    print(f"  query bank {doc['query_bank_sha256']}")
    if out is not None:
        print(f"wrote {out.name} ({sha256_bytes(data)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
