"""REQ-23 (J8) under post-W1 deviation D-2 (addendum section 21, extending section 19): the content-classifier scorer
with the filled pool pins. Runs where score_classifier.py runs (B15's job J8, a pod), with score_classifier.py's own
arguments plus two:

    python -B scripts/stage1_s1/d2_pool_pins/d2_score_classifier.py --prepared P --recipe S --anchors BANK
        [--pool PATH:SHA256 ...] --out DIR [--settings FILE]
        --pool-pins FILLED:SHA256 --req8-record plant_record.json:SHA256

Before anything runs: this file's settings (settings/d2_score_classifier.json) pass their literal pin below and name
D-2's settings by fill_pins.SETTINGS_SHA256; D-2's own checks pass (d2_representation_pass.checked: D-2's settings,
representation_pass.py and the W1 pins against the W1 manifest, REQ-8's record and the filled pins file, each by its
PATH:SHA256); scripts/stage1/score_classifier.py and its settings pass the W1 manifest's entries and this file's pins,
and score_classifier's literal SETTINGS_SHA256 is the manifest's entry for score_classifier.json; the representation_pass
module that score_classifier's _run imports by name hashes to D-2's pin. Then score_classifier's main() runs from the
checked bytes, privately (not in sys.modules), with its own arguments, and with only its global run replaced for that
call by a function that passes pool_pins = representation_pass.load_pool_pins(FILLED, its checked SHA-256) (run()
already takes pool_pins=(doc, sha); score_classifier.py:55-57, :71). The file is read again then, against the checked
SHA-256, so a file changed after the check refuses inside main() (exit 2, nothing written). run is restored in finally.
Everything else is score_classifier.py's: its settings pin, the pins rule for every pool, the scoring, its output file
and its exit codes.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1.d2_pool_pins import d2_representation_pass as d2m  # noqa: E402
from scripts.stage1_s1.d2_pool_pins import fill_pins as fp  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "d2_score_classifier.json"
SETTINGS_SHA256 = "1ce071b41a161d56746e1bac83da8c48879e5fb00cedd5a6afc1c9c5367219ef"
SETTINGS_NAME = "d2_score_classifier"
MODULE_NAME = "stage1_d2_score_classifier"


def load_settings() -> tuple[dict, str]:
    """This file's settings, refused unless they hash to SETTINGS_SHA256 and name D-2's settings by
    fill_pins.SETTINGS_SHA256 (both read when called)."""
    try:
        doc, digest = s1.load_settings(SETTINGS_PATH, SETTINGS_SHA256, SETTINGS_NAME)
    except OSError as exc:
        raise s1.Refusal(f"the D-2 classifier settings cannot be read ({type(exc).__name__})") from None
    if doc.get("d2_settings_sha256") != fp.SETTINGS_SHA256:
        raise s1.Refusal(f"the D-2 classifier settings name D-2's settings {doc.get('d2_settings_sha256')}, "
                         f"fill_pins pins {fp.SETTINGS_SHA256}")
    return doc, digest


def load_classifier(own: dict, root: Path | None = None) -> ModuleType:
    """score_classifier.py, checked against the W1 manifest's entry and this file's pin, run privately from the checked
    bytes (not put in sys.modules); its literal SETTINGS_SHA256 must be the manifest's entry for its settings."""
    root = Path(root) if root is not None else fp.w1_root()
    base = own["base"]
    entries, _ = fp.manifest_entries(root / base["manifest"])
    fp.check_pin(entries, base["script"], base["script_sha256"], "score_classifier.py")
    fp.check_pin(entries, base["settings"], base["settings_sha256"], "score_classifier.json")
    path = (root / base["script"]).resolve()
    code = fp.read_hashed(path, base["script_sha256"], "score_classifier.py")
    spec = importlib.util.spec_from_file_location(MODULE_NAME, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(code, str(path), "exec"), module.__dict__)
    if module.SETTINGS_SHA256 != base["settings_sha256"]:
        raise s1.Refusal("score_classifier.py's own settings pin is not the D-2 classifier settings' base.settings_sha256")
    return module


def check_by_name_representation_pass() -> None:
    """score_classifier's _run does `from scripts.stage1 import representation_pass as rp` (score_classifier.py:68);
    the module that statement gives must come from a file that hashes to D-2's pin of representation_pass.py."""
    d2, _ = fp.load_d2()
    from scripts.stage1 import representation_pass as rp

    origin = getattr(rp, "__file__", None)
    digest = sha256_file(Path(origin)) if origin and Path(origin).is_file() else None
    if digest != d2["base"]["script_sha256"]:
        raise s1.Refusal(f"the representation_pass module score_classifier imports by name hashes to {digest}, "
                         f"the D-2 pin is {d2['base']['script_sha256']}")


def run_classifier(module: ModuleType, base: fp.Base, argv: list[str], pins_path: Path, pins_sha: str) -> int:
    """score_classifier's main(argv) with only its global run replaced, for this call, by one that passes the filled
    pins (read against their checked SHA-256 by representation_pass's own load_pool_pins)."""
    original = module.run
    if (getattr(original, "__kwdefaults__", None) or {}).get("pool_pins", "absent") is not None:
        raise s1.Refusal("score_classifier.run does not take pool_pins=None (it is not the W1 run)")

    def filled_run(**kwargs):
        if "pool_pins" in kwargs:
            raise s1.Refusal("score_classifier's main passed pool pins of its own")
        return original(**kwargs, pool_pins=base.module.load_pool_pins(pins_path, pins_sha))
    module.run = filled_run
    try:
        return module.main(argv)
    finally:
        module.run = original


def forwarded(args) -> list[str]:
    """score_classifier.py's own arguments, as given."""
    argv = ["--prepared", str(args.prepared), "--recipe", str(args.recipe), "--anchors", str(args.anchors)]
    for spec in args.pool:
        argv += ["--pool", spec]
    argv += ["--out", str(args.out)]
    if args.settings is not None:
        argv += ["--settings", str(args.settings)]
    return argv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], allow_abbrev=False)
    for flag in ("--prepared", "--recipe", "--anchors", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--pool", action="append", default=[], help="PATH:SHA256 of the plant or decoy pool")
    parser.add_argument("--settings", type=Path, default=None, help="score_classifier's settings (its own pin)")
    parser.add_argument("--pool-pins", required=True, help="PATH:SHA256 of the filled pins file (fill_pins.py)")
    parser.add_argument("--req8-record", required=True, help="PATH:SHA256 of REQ-8's plant_record.json")
    args = parser.parse_args(argv)
    try:
        own, own_sha = load_settings()
        base, pins_path, pins_sha, pools = d2m.checked(args.pool_pins, args.req8_record)
        module = load_classifier(own)
        check_by_name_representation_pass()
        print(f"D-2: filled pins {pins_sha} (" + ", ".join(f"{n} {pools[n]['sha256']} {pools[n]['items']} items"
                                                       for n in fp.POOLS) +
              f"); score_classifier.py {own['base']['script_sha256']}; W1 pins {base.pins_sha256}")
        return run_classifier(module, base, forwarded(args), pins_path, pins_sha)
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
