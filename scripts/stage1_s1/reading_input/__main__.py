"""Command line of the B16 input builder (package doc). Exit 0: both files written; 2: refused, nothing written.

    python -m scripts.stage1_s1.reading_input --reading R --kit DIR --out tables.json --record sources.json
        (--b14-strata F --b14-report F --expect-strata-sha256 H --expect-report-sha256 H | --no-overlap)
        [--repo DIR] [--rules FILE]

``--repo`` is the folder that REJUDGED_PINS paths and the frozen coherence bars file are relative to (default: this
repository); ``--rules`` is the kit's rules module (default: runkit/stage1-olmo/stage1_rules.py of this repository).
Printed: counts, SHA-256 values, unit labels and refusals; never an item value, a mean or a count of labels. A refusal
of B16's own schema prints only the part of its message that names the place (B16's messages may hold a value). Any
other error prints its type only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.stage1_s1.reading.settings import Refusal, canonical_json
from scripts.stage1_s1.reading_input.build import Overlap, build
from scripts.stage1_s1.reading_input.sources import load_rules, sha256_bytes

REPO = Path(__file__).resolve().parents[3]
RULES = REPO / "runkit" / "stage1-olmo" / "stage1_rules.py"
READINGS = ("plan_a", "plan_a_block_a_only", "plan_b")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m scripts.stage1_s1.reading_input",
                                description="the B16 input builder (addendum 33 point 5)")
    p.add_argument("--reading", required=True, choices=READINGS)
    p.add_argument("--kit", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--record", required=True, type=Path)
    p.add_argument("--repo", type=Path, default=REPO)
    p.add_argument("--rules", type=Path, default=RULES)
    p.add_argument("--b14-strata", type=Path)
    p.add_argument("--b14-report", type=Path)
    p.add_argument("--expect-strata-sha256")
    p.add_argument("--expect-report-sha256")
    p.add_argument("--no-overlap", action="store_true",
                   help="build without section 9.4's overlap block (addendum 24 point 4's fallback)")
    return p


def _overlap(args) -> Overlap | None:
    given = [args.b14_strata, args.b14_report, args.expect_strata_sha256, args.expect_report_sha256]
    if args.no_overlap:
        if any(v is not None for v in given):
            raise Refusal("--no-overlap takes none of the B14 options")
        return None
    if any(v is None for v in given):
        raise Refusal("the overlap block needs --b14-strata, --b14-report, --expect-strata-sha256 and "
                      "--expect-report-sha256 (or --no-overlap for addendum 24 point 4's fallback)")
    return Overlap(args.b14_strata, args.b14_report, args.expect_strata_sha256, args.expect_report_sha256)


def _say(lines) -> None:
    for line in lines:
        print(line)


def summary_lines(record: dict, out_sha: str, record_sha: str, args) -> list[str]:
    c = record["counts"]
    lines = [f"reading {record['reading']} (plan {record['kit']['plan_code']}); plan.json {record['kit']['plan_sha256']}",
             f"rules {args.rules} sha256 {record['builder']['rules_sha256']}; B16 settings "
             f"{record['builder']['b16_settings_sha256']}",
             *(f"seal {b} {h}" for b, h in sorted(record["kit"]["seals"].items())),
             f"cells: U {c['U_cells']}, O {c['O_cells']}, L {c['L_cells']}; O cells absent (LN-12): "
             f"{', '.join(record['o_cells_absent']) or 'none'}",
             *(f"cell {k}: {v['unit']['folder']} {v['unit']['complete_sha256'][:16]}" for k, v in record["cells"].items()),
             f"theta0 O: {record['theta0']['o']['folder']} {record['theta0']['o']['complete_sha256'][:16]}",
             f"references: {', '.join(c['references']) or 'none'} ({len(record['references'])} units)",
             *(f"reference {k}: {v['unit']['folder']} {v['unit']['complete_sha256'][:16]}"
               for k, v in record["references"].items()),
             f"not references: {len(record['not_references'])}; complete (not pulled), not inputs: "
             f"{len(record['not_pulled'])}",
             *(f"judges {b}: {', '.join(j['judges']) or 'none'}; {j['units']} units, {j['files']} indexed files"
               for b, j in sorted(record["judges"].items())),
             (f"overlap: strata {record['overlap']['strata_sha256']}, report {record['overlap']['report_sha256']}"
              if record["overlap"] else "overlap: not included (--no-overlap)"),
             *(f"not built: {k}" for k in sorted(record["not_built"])),
             f"wrote {args.out} sha256 {out_sha}",
             f"wrote {args.record} sha256 {record_sha}"]
    return lines


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        for path in (args.out, args.record):
            if path.exists():
                raise Refusal(f"{path.name} exists; the builder never overwrites")
        rules, rules_sha = load_rules(args.rules)
        doc, record = build(args.reading, args.kit, args.repo, rules, rules_sha, _overlap(args))
        data = canonical_json(doc)
        out_sha = sha256_bytes(data)
        record["output_sha256"] = out_sha
        rec_data = canonical_json(record)
        try:
            with open(args.out, "xb") as handle:
                handle.write(data)
            with open(args.record, "xb") as handle:
                handle.write(rec_data)
        except FileExistsError:
            raise Refusal("an output file exists; the builder never overwrites") from None
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - any other error may carry a value in its text: print its type only
        print(f"REFUSED: an unexpected {type(exc).__name__} (its message is withheld: it may hold a value)",
              file=sys.stderr)
        return 2
    _say(summary_lines(record, out_sha, sha256_bytes(rec_data), args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
