"""Gate C diagnostic: the classifier (brief gate-b-engine-kit-reading-20261008, A9 with [D8]; DRAFT §5; KTD E6, :270;
report only; outside the engine identity; runs on the wave-0b pod beside the attribution pass).

    python3 scripts/gate_c_classifier.py --prepared P --recipe S --anchors A --groups G1,G2,... --out DIR

The recipe's guard scores every row of the named groups (all of each unit's dev rows; not ``headroom.score_rows``,
which scores the whole edit pool) with ``GuardScorer.label_scores`` on (prompt, training response). A row's score is
the normalized Unsafe label-sequence score; unscored rows (control strings, over the limit) are counted, never
imputed. Per unit: the mean, the sample SD and the analytic SE = SD / sqrt(scored rows) (600 rows per unit); the
diagnostic is uninformative when the range of the unit means is below 2 x the largest SE (KTD:270). The anchor file
is read by SHA-256 as the representation script reads it (the same inputs). Output DIR/classifier.json (canonical
JSON, numbers, ids and hashes only); its top unit is report only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from gate_c_representation import _peak, _reset_peak, _setup_peak, _sha, inputs  # noqa: E402

KIND = "gate-c classifier scores"
OUTPUT = "classifier.json"
UNINFORMATIVE_FACTOR = 2          # range of unit means < 2 x the largest SE (KTD:270)


def run(prepared_dir: pathlib.Path, recipe_path: pathlib.Path, anchors_path: pathlib.Path, group_ids: list[str],
        out: pathlib.Path, loaders) -> dict:
    from experiments.safety_selection import runner
    from experiments.safety_selection.common import canonical_json, code_identity
    from experiments.safety_selection.config import config_sha256
    from experiments.safety_selection.ledger import RunLedger

    recipe, prepared, manifest_sha, _, anchor_sha, groups = inputs(prepared_dir, recipe_path, anchors_path, group_ids)
    out.mkdir(parents=True)
    started = time.monotonic()
    session = runner.Session(recipe, loaders)
    _reset_peak(session.device)
    ledger = RunLedger(out, sync=session.sync, memory=session.memory)
    guard = session.guard(ledger, out)
    setup = {"seconds": time.monotonic() - started, "peak_memory_bytes": _setup_peak(_peak(session.device), out)}
    started = time.monotonic()
    _reset_peak(session.device)
    members = [rid for gid in group_ids for rid in groups[gid]]
    over = {"over_limit_unscored": True} if recipe["generation"].get("guard_over_limit") == "unscored" else {}
    records = guard.label_scores([(rid, prepared.train_rows[rid]["prompt"], prepared.train_rows[rid]["response"])
                                  for rid in members], **over)
    by_id = dict(zip(members, records))
    scored = {"seconds": time.monotonic() - started, "rows": len(members),
              "tokens": sum(r.get("guard_input_tokens") or 0 for r in records),
              "peak_memory_bytes": _peak(session.device)}
    out_groups = {}
    for gid in group_ids:
        values = [by_id[rid]["normalized"]["Unsafe"] for rid in groups[gid] if by_id[rid]["valid"]]
        if len(values) < 2:
            raise SystemExit(f"group {gid}: {len(values)} scored rows; an SD needs two")
        sd = statistics.stdev(values)
        out_groups[gid] = {"rows": len(groups[gid]), "scored": len(values), "unscored": len(groups[gid]) - len(values),
                           "mean": math.fsum(values) / len(values), "sd": sd, "se": sd / math.sqrt(len(values))}
    means = [g["mean"] for g in out_groups.values()]
    uninformative = (max(means) - min(means)) < UNINFORMATIVE_FACTOR * max(g["se"] for g in out_groups.values())
    record = {"kind": KIND, "version": 1, "script_sha256": _sha(pathlib.Path(__file__).read_bytes()),
              "representation_script_sha256": _sha((ROOT / "scripts" / "gate_c_representation.py").read_bytes()),
              "anchor_file_sha256": anchor_sha, "recipe_sha256": config_sha256(recipe), "manifest_sha256": manifest_sha,
              "engine_code_sha256": code_identity()["sha256"], "score": "normalized Unsafe label-sequence score",
              "groups": out_groups, "uninformative": uninformative, "costs": {"diag_setup": setup, "diag_rows": scored}}
    (out / OUTPUT).write_bytes(canonical_json(record))
    return record


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--prepared", required=True)
    ap.add_argument("--recipe", required=True)
    ap.add_argument("--anchors", required=True)
    ap.add_argument("--groups", required=True, help="comma-separated group ids")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    from experiments.safety_selection.loaders import real_loaders

    record = run(pathlib.Path(args.prepared), pathlib.Path(args.recipe), pathlib.Path(args.anchors),
                 args.groups.split(","), pathlib.Path(args.out), real_loaders())
    print(json.dumps({"output_sha256": _sha((pathlib.Path(args.out) / OUTPUT).read_bytes()),
                      "groups": len(record["groups"]), "uninformative": record["uninformative"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
