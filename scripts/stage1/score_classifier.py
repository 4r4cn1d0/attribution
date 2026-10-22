"""REQ-23 (W1-07): the per-row content-classifier scorer (C R8.1-R8.4; outside the engine identity; runs on a stage-1
pod, about $1, paid from stage 1's funding event; CPU-tested; CUDA paths UNTESTED). Wave 1 waits for it (UW-18).

    python scripts/stage1/score_classifier.py --prepared P --recipe S --anchors BANK [--pool PATH:SHA256 ...] --out DIR

Recipe S's guard scores each row with ``GuardScorer.label_scores`` on (prompt, training response), read-only, exactly
as the pinned Gate C classifier (scripts/gate_c_classifier.py) scores rows: the score is the normalized Unsafe
label-sequence score; an unscored row (a control string, or over the guard's input limit when the recipe says
"unscored") is counted, never imputed. Rows: every dev row of the prepared set once; the 75 plant rows (REQ-3's pool
``plant``) once; the 37 decoy rows (pool ``decoy``) if W1-09 is built. A pool must carry its filled pin in REQ-3's pool
pins (settings/representation_pools.json); no other pool is taken.

Per unit (the Gate C block): rows, scored, unscored, the mean, the sample SD and SE = SD / sqrt(scored) of the scored
rows. Selection: the top 600 scored dev rows by score, ties by the sealed rank of registry key classifier.ties over the
scored ids; "scored only" (PLAN-S section 5.4): no edit file is written. Writes ``classifier_scores.json`` (text-free:
each row's score or its unscored reason, the units block, the pools' scores, the selection with its boundary ties,
costs, provenance).
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "score_classifier.json"
SETTINGS_SHA256 = "5807ec750c74137f3e5c466231de9e73a0cbb5fe5411f7be29a40bbed4c8e58a"
SETTINGS_NAME = "score_classifier"
OUTPUT = "classifier_scores.json"


def unit_block(values_by_unit: dict[str, list], members: dict[str, list]) -> dict:
    """Gate C's per-unit block, from the valid scores of each unit's rows."""
    out = {}
    for gid, rows in members.items():
        values = values_by_unit[gid]
        if len(values) < 2:
            raise s1.Refusal(f"unit {gid}: {len(values)} scored rows; an SD needs two")
        sd = statistics.stdev(values)
        out[gid] = {"rows": len(rows), "scored": len(values), "unscored": len(rows) - len(values),
                    "mean": math.fsum(values) / len(values), "sd": sd, "se": sd / math.sqrt(len(values))}
    return out


def run(*, prepared_root: Path, recipe_path: Path, anchors_path: Path, loaders, settings: dict, settings_sha256: str,
        pools: list[tuple[Path, str]] = (), pool_pins: tuple[dict, str] | None = None) -> dict[str, bytes]:
    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        return _run(prepared_root, recipe_path, anchors_path, loaders, settings, settings_sha256, pools, pool_pins,
                    Path(scratch))


def _run(prepared_root, recipe_path, anchors_path, loaders, settings, settings_sha256, pools, pool_pins, scratch):
    from experiments.safety_selection import runner
    from experiments.safety_selection.ledger import RunLedger
    from scripts.stage1 import representation_pass as rp

    s1.check_settings(settings, SETTINGS_NAME)
    pins, pins_sha256 = rp.load_pool_pins() if pool_pins is None else (rp.check_pool_pins(pool_pins[0]), pool_pins[1])
    try:
        recipe, prepared, manifest_sha, _, units = rp.inputs(prepared_root, recipe_path, anchors_path, settings)
    except OSError as exc:
        raise s1.Refusal(f"an input file cannot be read ({type(exc).__name__})") from None
    pool_docs = [rp.read_pool(path, digest) for path, digest in pools]
    allowed = settings["pools"]
    for p in pool_docs:
        if p["name"] not in allowed:
            raise s1.Refusal(f"pool {p['name']} is not one the classifier scores ({sorted(allowed)})")
        if rp.pin_of(p, pins) != "pool pins":
            raise s1.Refusal(f"pool {p['name']} has no filled pin in REQ-3's pool pins")
    if len({p["name"] for p in pool_docs}) != len(pool_docs):
        raise s1.Refusal("two pools share one name")
    started = time.monotonic()
    session = runner.Session(recipe, loaders)
    ledger = RunLedger(scratch, sync=session.sync, memory=session.memory)
    guard = session.guard(ledger, scratch)
    setup_seconds = time.monotonic() - started
    members = {gid: list(prepared.groups["dev"][gid]) for gid in units}
    items = [(rid, prepared.train_rows[rid]["prompt"], prepared.train_rows[rid]["response"])
             for gid in units for rid in members[gid]]
    pool_items = [(i["id"], i["prompt"], i["response"]) for p in pool_docs for i in p["items"]]
    ids = [i[0] for i in items + pool_items]
    if len(set(ids)) != len(ids):
        raise s1.Refusal("a pool item id repeats a training row id")
    over = {"over_limit_unscored": True} if recipe["generation"].get("guard_over_limit") == "unscored" else {}
    started = time.monotonic()
    records = guard.label_scores(items + pool_items, **over)
    score_seconds = time.monotonic() - started
    by_id = dict(zip(ids, records))

    def entry(rid):
        r = by_id[rid]
        if r["valid"]:
            return {"score": r["normalized"]["Unsafe"]}
        return {"score": None, "unscored": r.get("reason") or "invalid"}
    dev = {rid: entry(rid) for gid in units for rid in members[gid]}
    values = {gid: [dev[rid]["score"] for rid in members[gid] if dev[rid]["score"] is not None] for gid in units}
    block = unit_block(values, members)
    scored = {rid: e["score"] for rid, e in dev.items() if e["score"] is not None}
    k = settings["selection"]["k"]
    if len(scored) < k:
        raise s1.Refusal(f"only {len(scored)} dev rows are scored, fewer than the {k} to select")
    selected = s1.select_top(scored, k, "classifier.ties")
    pools_out = {p["name"]: {"sha256": p["sha256"], "items": len(p["items"]),
                             "rows": {i["id"]: entry(i["id"]) for i in p["items"]},
                             "unscored": sum(entry(i["id"])["score"] is None for i in p["items"])} for p in pool_docs}
    doc = {"kind": "stage1 classifier scores", "version": 1, "requirement": settings["requirement"],
           "score": settings["score"], "rows": dict(sorted(dev.items())), "units": block,
           "unscored": len(dev) - len(scored), "pools": pools_out,
           "selection": {"k": k, "scored_only": True, "selected": selected,
                         "boundary_ties": s1.boundary_ties(scored, selected), "rule": settings["selection"]["rule"]},
           "costs": {"device": session.device, "setup_seconds": setup_seconds, "score_seconds": score_seconds,
                     "rows": len(ids), "guard_input_tokens": sum(r.get("guard_input_tokens") or 0 for r in records)},
           "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                       {"prepared_manifest": manifest_sha, "anchor_file": sha256_file(anchors_path),
                                        "recipe_file": sha256_file(recipe_path), "pool_pins": pins_sha256,
                                        **{f"pool_{p['name']}": p["sha256"] for p in pool_docs}},
                                       settings["label_entries"])}
    data = canonical_json(doc)
    if s1._text_hits(data, [t for _, p, r in items + pool_items for t in (p, r)]):
        raise s1.Refusal("the output would hold text")
    return {OUTPUT: data}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for flag in ("--prepared", "--recipe", "--anchors", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--pool", action="append", default=[], help="PATH:SHA256 of the plant or decoy pool")
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        pools = []
        for spec in args.pool:
            path, _, sha = spec.rpartition(":")
            if not path or not s1.HEX64.match(sha):
                raise s1.Refusal("each --pool is PATH:SHA256")
            pools.append((Path(path), sha))
        from experiments.safety_selection.loaders import real_loaders

        files = run(prepared_root=args.prepared.resolve(), recipe_path=args.recipe.resolve(),
                    anchors_path=args.anchors.resolve(), loaders=real_loaders(), settings=settings,
                    settings_sha256=digest, pools=pools)
        written = s1.write_new_files(args.out.resolve(), files)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
