"""REQ-3 under post-W1 deviation D-2 (addendum section 19 point 2(b)): the shared representation pass with the filled
pool pins. Runs where representation_pass.py runs (B15's job J5, a pod), with representation_pass.py's own arguments
plus two:

    python -B scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py --prepared P --recipe REC --anchors BANK
        [--pool PATH:SHA256 ...] [--pools-only] --out DIR [--settings FILE]
        --pool-pins FILLED:SHA256 --req8-record plant_record.json:SHA256

Before anything runs: this package's settings pass their literal pin; scripts/stage1/representation_pass.py and the W1
pins file pass the W1 manifest's entries and the D-2 pins (fill_pins.load_base); REQ-8's record and the filled pins
file hash to the given SHA-256s and pass fill_pins.check_record and fill_pins.check_filled (the filled file differs
from the W1 pins only in the two pool sha256 values, each REQ-8's with the same item count). Then representation_pass's
main() runs from the checked bytes, privately (not in sys.modules), with representation_pass.py's own arguments and
--pool-pins FILLED, and with only the pins path and its SHA-256 replaced for that call: the module globals
POOL_PINS_PATH and POOL_PINS_SHA256 and load_pool_pins's two default values (bound when the module ran), which is what
a hand-filled copy of the file would hold. They are restored afterwards. main() then reads the filled file again,
against the filled SHA-256, so a file changed after the check refuses. Everything else is representation_pass.py's: its
settings pin, the pins rule for every pool (an S3 pool stays named on the command line by its SHA-256), the pass, its
two output files and its exit codes (2 on a refusal, nothing written).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1.d2_pool_pins import fill_pins as fp  # noqa: E402


def checked(pool_pins: str, req8_record: str, root: Path | None = None) -> tuple[fp.Base, Path, str, dict]:
    """(the loaded base, the filled pins path and SHA-256, the record's pools) after every D-2 check."""
    d2, _ = fp.load_d2()
    root = Path(root) if root is not None else fp.w1_root()
    pins_path, pins_sha = fp.parse_hashed(pool_pins, "--pool-pins")
    rec_path, rec_sha = fp.parse_hashed(req8_record, "--req8-record")
    base = fp.load_base(d2, (root / d2["base"]["pins"], d2["base"]["pins_sha256"]), root)
    pools = fp.check_record(fp.read_hashed(rec_path, rec_sha, "REQ-8's record"), d2, base.entries)
    fp.check_filled(base, fp.read_hashed(pins_path, pins_sha, "the filled pins file"), pools)
    return base, pins_path.resolve(), pins_sha, pools


def run_base(base: fp.Base, argv: list[str], pins_path: Path, pins_sha: str) -> int:
    """representation_pass's main(argv) with the pins path and its SHA-256 replaced for this call only."""
    m = base.module
    saved = (m.POOL_PINS_PATH, m.POOL_PINS_SHA256, m.load_pool_pins.__defaults__)
    if saved[2] != (m.POOL_PINS_PATH, m.POOL_PINS_SHA256):
        raise s1.Refusal("representation_pass.load_pool_pins's defaults are not POOL_PINS_PATH and POOL_PINS_SHA256")
    m.POOL_PINS_PATH, m.POOL_PINS_SHA256 = pins_path, pins_sha
    m.load_pool_pins.__defaults__ = (pins_path, pins_sha)
    try:
        return m.main(argv)
    finally:
        m.POOL_PINS_PATH, m.POOL_PINS_SHA256, m.load_pool_pins.__defaults__ = saved


def forwarded(args, pins_path: Path) -> list[str]:
    """representation_pass.py's own arguments, as given, plus --pool-pins FILLED."""
    argv = ["--prepared", str(args.prepared), "--recipe", str(args.recipe), "--anchors", str(args.anchors)]
    for spec in args.pool:
        argv += ["--pool", spec]
    if args.pools_only:
        argv.append("--pools-only")
    argv += ["--out", str(args.out)]
    if args.settings is not None:
        argv += ["--settings", str(args.settings)]
    return argv + ["--pool-pins", str(pins_path)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], allow_abbrev=False)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--pool", action="append", default=[], help="PATH:SHA256 of a stage-1 text pool (repeatable)")
    parser.add_argument("--pools-only", action="store_true", help="score the pools only, not the dev units")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=None, help="representation_pass's settings (its own pin)")
    parser.add_argument("--pool-pins", required=True, help="PATH:SHA256 of the filled pins file (fill_pins.py)")
    parser.add_argument("--req8-record", required=True, help="PATH:SHA256 of REQ-8's plant_record.json")
    args = parser.parse_args(argv)
    try:
        base, pins_path, pins_sha, pools = checked(args.pool_pins, args.req8_record)
        print(f"D-2: filled pins {pins_sha} (" + ", ".join(f"{n} {pools[n]['sha256']} {pools[n]['items']} items"
                                                       for n in fp.POOLS) +
              f"); representation_pass.py {base.script_sha256}; W1 pins {base.pins_sha256}")
        return run_base(base, forwarded(args, pins_path), pins_path, pins_sha)
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
