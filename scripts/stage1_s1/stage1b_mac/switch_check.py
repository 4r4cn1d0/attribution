"""The Self-Inf-N switch check (addendum section 40 point 13(a); the section 35 point 1 pattern of
scripts/stage1_s1/extract_a0_fingerprint.py: one key, by pin, nothing else printed). The plant-rank report
(scripts/stage1/report_plant_ranks.py, REQ-29) counts Self-Inf-N-style only while its settings' switch says REQ-13 was
committed at W1: key path ``counting.selfinf_n_counts`` (report_plant_ranks.report). That settings path holds "plant",
so the switch is read here by key only, after the file hashes to the report's own pin SETTINGS_SHA256 (the W1
manifest's entry for scripts/stage1/settings/report_plant_ranks.json).

    python -B -m scripts.stage1_s1.stage1b_mac.switch_check [--settings FILE] [--expect-sha256 H]

Printed: the settings' SHA-256 and "selfinf_n_counts true" or "selfinf_n_counts false" (exit 0); a refusal is a fixed
message (exit 2). No other key is printed or written.
"""

from __future__ import annotations

import argparse

from scripts.stage1.report_plant_ranks import SETTINGS_NAME, SETTINGS_PATH, SETTINGS_SHA256
from scripts.stage1.s1common import SETTINGS_KIND
from scripts.stage1_s1.stage1b_mac.common import Refusal, is_hex64, json_object, read_pinned, run_frame

KEY_PATH = ("counting", "selfinf_n_counts")   # report_plant_ranks.report: settings["counting"]["selfinf_n_counts"]


def switch_of(settings: dict) -> bool:
    """The switch's value: a JSON boolean at KEY_PATH of the report's settings."""
    if settings.get("kind") != SETTINGS_KIND or settings.get("name") != SETTINGS_NAME:
        raise Refusal("the settings are not the plant-rank report's")
    node = settings
    for key in KEY_PATH:
        if not isinstance(node, dict) or key not in node:
            raise Refusal("the settings hold no counting.selfinf_n_counts")
        node = node[key]
    if not isinstance(node, bool):
        raise Refusal("counting.selfinf_n_counts is not a JSON boolean")
    return node


def read_switch(settings_path, expect_sha256: str) -> bool:
    if not is_hex64(expect_sha256):
        raise Refusal("--expect-sha256 is not 64 lowercase hex")
    data = read_pinned(settings_path, expect_sha256, "the settings file")
    return switch_of(json_object(data, "the settings file"))


def main(argv=None) -> int:
    def produce(argv):
        parser = argparse.ArgumentParser(prog="python -B -m scripts.stage1_s1.stage1b_mac.switch_check",
                                         description=__doc__.split("\n\n")[0])
        parser.add_argument("--settings", default=str(SETTINGS_PATH))
        parser.add_argument("--expect-sha256", default=SETTINGS_SHA256)
        args = parser.parse_args(argv)
        value = read_switch(args.settings, args.expect_sha256)
        print(f"settings sha256 {args.expect_sha256}")
        print(f"selfinf_n_counts {'true' if value else 'false'}")
        return 0
    return run_frame(produce, argv)


if __name__ == "__main__":
    raise SystemExit(main())
