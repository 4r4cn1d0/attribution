"""REQ-12: DataShield-style (SPEC sections 4.4-4.5; LW-18: built before wave 1; if not committed at W1, post-Gate-B
exploratory, ADD-6.6). Mac, $0; model-agnostic; it reads REQ-3's pod output.

    python scripts/stage1/score_datashield.py --prepared P --rows PATH:SHA256 --summary PATH:SHA256 --out DIR

REQ-3 computes, per hidden-state index l: v_l = the harmful anchors' mean of read (c) minus the safe anchors' mean;
CAS(l) by Eq. 3-5 on the 128 anchors' read (b) states z-scored per dimension (sums of squared projections); and, per row,
CSS_l = (read (c) - read (d)) . v_l / ||v_l||. Here: l_hat = argmax CAS(l) over l = 1..n (the embedding output, index 0,
is excluded; an index whose CAS is null, a zero direction, is skipped), ties to the lower l; score = CSS at l_hat for every
training row, float64. Written as T1's scorer output (scorer datashield, high = remove); write_score_edit.py's scorer path
selects the top 600 and records the category check (at least 50% of the 600 in one category; PLAN-S:149).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "score_datashield.json"
SETTINGS_SHA256 = "065e96564b659485b6db9cbbb4a4359902ed31c79f1ed5b50c08e9f3cdd155b4"
SETTINGS_NAME = "score_datashield"
OUTPUT = "datashield_scores.json"


def read_pinned(pair: tuple[Path, str], what: str) -> bytes:
    path, digest = pair
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {digest}")
    return data


def choose_index(cas: list) -> int:
    """argmax CAS over l = 1..n, null entries skipped, ties to the lower l."""
    candidates = [(l, v) for l, v in enumerate(cas) if l >= 1 and v is not None]
    if not candidates:
        raise s1.Refusal("no index from 1 to n has a CAS value")
    best = max(v for _, v in candidates)
    return min(l for l, v in candidates if v == best)


def scores_from(rows_bytes: bytes, rows_sha256: str, summary_doc: dict, settings: dict) -> tuple[dict, int]:
    if summary_doc.get("kind") != "stage1 representation pass" or summary_doc["rows"]["sha256"] != rows_sha256:
        raise s1.Refusal("the rows file is not the one REQ-3's summary names")
    if summary_doc["provenance"]["settings_sha256"] != settings["pins"]["representation_pass_settings_sha256"]:
        raise s1.Refusal("REQ-3's summary was not made with the pinned REQ-3 settings")
    cas = summary_doc["datashield"]["cas"]
    n = summary_doc["layout"]["n_layers"]
    if len(cas) != n + 1:
        raise s1.Refusal("REQ-3's CAS list does not hold n + 1 indices")
    index = choose_index(cas)
    scores = {}
    for line in s1.iter_jsonl_bytes(rows_bytes, "REQ-3's rows file"):
        if line.get("source") != "dev":
            continue
        value = line["css"][index]
        if value is None or not math.isfinite(float(value)):
            raise s1.Refusal(f"row {line['id']}: no finite CSS at index {index}")
        scores[line["id"]] = float(value)
    return scores, index


def build(*, prepared_root: Path, rows: tuple[Path, str], summary: tuple[Path, str], settings: dict,
          settings_sha256: str) -> dict[str, bytes]:
    s1.check_settings(settings, SETTINGS_NAME)
    view = s1.PreparedView(prepared_root, settings["pins"]["prepared_manifest_sha256"])
    summary_doc = s1.strict_json(read_pinned(summary, "REQ-3's summary"))
    scores, index = scores_from(read_pinned(rows, "REQ-3's rows file"), rows[1], summary_doc, settings)
    s1.check_scores(scores, view.tokens)
    doc = {"kind": settings["scorer_output"]["kind"], "version": settings["scorer_output"]["version"],
           "scorer": "datashield", "manifest_sha256": view.manifest_sha256,
           "orientation": settings["scorer_output"]["orientation"], "scores": dict(sorted(scores.items())),
           "costs": {"representation_pass": summary_doc["costs"], "score_seconds": 0.0},
           "provenance": {**s1.provenance(Path(__file__).resolve(), settings_sha256,
                                          {"rows": rows[1], "summary": summary[1], "prepared_manifest": view.manifest_sha256},
                                          settings["label_entries"]),
                          "l_hat": index, "cas_at_l_hat": summary_doc["datashield"]["cas"][index]}}
    return {OUTPUT: canonical_json(doc)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True)
    for flag in ("--rows", "--summary"):
        parser.add_argument(flag, required=True, help="PATH:SHA256")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)

        def pair(spec):
            path, _, sha = spec.rpartition(":")
            if not path or not s1.HEX64.match(sha):
                raise s1.Refusal("--rows and --summary are PATH:SHA256")
            return Path(path), sha
        files = build(prepared_root=args.prepared, rows=pair(args.rows), summary=pair(args.summary), settings=settings,
                      settings_sha256=digest)
        written = s1.write_new_files(args.out.resolve(), files)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
