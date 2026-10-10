"""Gate C diagnostic: representation similarity (brief gate-b-engine-kit-reading-20261008, A9 with [D8], [D9] A-5;
DRAFT §5; KTD E6; outside the engine identity; runs on the wave-0b pod beside the attribution pass).

    python3 scripts/gate_c_representation.py --prepared P --recipe S --anchors A --groups G1,G2,... --out DIR

The policy is the UNTUNED base model (``policy.model.disable_adapter()``). Every row of the named groups (all of each
unit's dev rows) and every anchor is encoded as a training row (the token audit checked) and run in one unbatched
forward; its vector is the final layer's hidden state at the last response token (the token before the end-of-turn
token, at the sequence's true length). Each row's score is cos(v, mean harmful anchor vector) - cos(v, mean safe
anchor vector), in float64; a unit's score is the mean over all its rows. The anchor file must be recipe S's bank
(read by SHA-256). Output DIR/representation.json (canonical JSON, numbers, ids and hashes only); pick_R = the unit
with the largest score, ties to the lower group id.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

KIND = "gate-c representation scores"
OUTPUT = "representation.json"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inputs(prepared_dir: pathlib.Path, recipe_path: pathlib.Path, anchors_path: pathlib.Path, group_ids: list[str]):
    """The checked inputs: the recipe, the prepared view and manifest hash, the anchor file (by the recipe's bank) and
    each group's dev rows, in order. Refuses (SystemExit) with ids and counts only."""
    from experiments.safety_selection.config import load_recipe
    from experiments.safety_selection.jobs import JobError, read_anchor_bank
    from experiments.safety_selection.prepare import load_prepared, read_manifest

    recipe = load_recipe(recipe_path)
    bank = recipe["attribution"]["query_bank"]
    try:
        anchors = read_anchor_bank(anchors_path, bank, recipe)
    except JobError as exc:
        raise SystemExit(f"the anchor file is refused: {exc}") from None
    manifest, manifest_sha = read_manifest(prepared_dir, None)
    prepared = load_prepared(prepared_dir, manifest_sha)
    groups = prepared.groups["dev"]
    missing = [g for g in group_ids if g not in groups]
    if missing or len(set(group_ids)) != len(group_ids) or not group_ids:
        raise SystemExit(f"--groups must name distinct dev groups ({len(missing)} unknown)")
    return recipe, prepared, manifest_sha, anchors, bank[len("anchors-"):], {g: list(groups[g]) for g in group_ids}


def last_response_vector(model, input_ids, device: str):
    """One unbatched forward of a training row (prompt + response + end-of-turn id): the final layer's hidden state at
    the last response token, the position before the end-of-turn id at the true length, in float64 on the CPU."""
    import torch

    ids = torch.tensor([list(input_ids)], device=device)
    hidden = model(input_ids=ids, output_hidden_states=True).hidden_states[-1]
    return hidden[0, len(input_ids) - 2].to(torch.float64).cpu()


def _reset_peak(device: str) -> None:
    """Start a cost phase: on cuda its peak memory is then the phase's own (untested on CUDA)."""
    import torch

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()


def _peak(device: str):
    import torch

    return int(torch.cuda.max_memory_allocated()) if device == "cuda" else None


def _setup_peak(peak, out: pathlib.Path):
    """The setup phase's peak: the larger of the script's own ``peak`` and the CUDA peak each ledger stage written so
    far recorded (the load stage's; the ledger's memory probe resets the cuda peak when a stage ends, so the script's
    own read misses the load). None when neither is a number (off cuda). Untested on CUDA."""
    from experiments.safety_selection.common import read_jsonl
    from experiments.safety_selection.ledger import LEDGER

    stages = [r.get("memory", {}).get("cuda_peak_allocated_bytes") for r in read_jsonl(out / LEDGER)]
    values = [v for v in (peak, *stages) if isinstance(v, int) and not isinstance(v, bool)]
    return max(values) if values else None


def run(prepared_dir: pathlib.Path, recipe_path: pathlib.Path, anchors_path: pathlib.Path, group_ids: list[str],
        out: pathlib.Path, loaders) -> dict:
    import torch

    from experiments.safety_selection import runner
    from experiments.safety_selection.common import canonical_json, code_identity
    from experiments.safety_selection.config import config_sha256
    from experiments.safety_selection.ledger import RunLedger

    recipe, prepared, manifest_sha, anchors, anchor_sha, groups = inputs(prepared_dir, recipe_path, anchors_path,
                                                                        group_ids)
    out.mkdir(parents=True)
    started = time.monotonic()
    session = runner.Session(recipe, loaders)
    _reset_peak(session.device)
    ledger = RunLedger(out, sync=session.sync, memory=session.memory)
    policy = session.policy(ledger, out)
    codec, device = policy.codec, policy.device
    sets = runner.anchor_examples(codec, anchors, recipe)
    rows = {rid: runner._verified_example(codec, rid, prepared.train_rows[rid], recipe)
            for gid in group_ids for rid in groups[gid]}
    setup = {"seconds": time.monotonic() - started, "peak_memory_bytes": _setup_peak(_peak(device), out)}

    def vector(ex):
        return last_response_vector(policy.model, ex.input_ids, device)

    started = time.monotonic()
    _reset_peak(device)
    was_training = policy.model.training
    policy.model.eval()
    try:
        with torch.no_grad(), policy.model.disable_adapter():                 # untuned ([D9] A-5)
            means = {}
            for name in ("harmful", "safe"):
                total = None
                for ex in sets[name]:
                    v = vector(ex)
                    total = v if total is None else total + v
                means[name] = total / len(sets[name])
            per_row = {}
            for rid, ex in rows.items():
                v = vector(ex)
                cos = {name: float(torch.nn.functional.cosine_similarity(v, means[name], dim=0)) for name in means}
                per_row[rid] = (cos["harmful"], cos["safe"], cos["harmful"] - cos["safe"])
    finally:
        policy.model.train(was_training)
    tokens = sum(len(ex.input_ids) for ex in rows.values()) + sum(len(ex.input_ids) for s in sets.values() for ex in s)
    scored = {"seconds": time.monotonic() - started, "rows": len(rows), "tokens": tokens,
              "peak_memory_bytes": _peak(device)}
    out_groups = {}
    for gid in group_ids:
        values = [per_row[rid] for rid in groups[gid]]
        out_groups[gid] = {"rows": len(values), "harmful": math.fsum(v[0] for v in values) / len(values),
                           "safe": math.fsum(v[1] for v in values) / len(values),
                           "score": math.fsum(v[2] for v in values) / len(values)}
    record = {"kind": KIND, "version": 1, "script_sha256": _sha(pathlib.Path(__file__).read_bytes()),
              "anchor_file_sha256": anchor_sha, "recipe_sha256": config_sha256(recipe), "manifest_sha256": manifest_sha,
              "engine_code_sha256": code_identity()["sha256"], "untuned": "policy.model.disable_adapter()",
              "vector": "final-layer hidden state at the last response token", "groups": out_groups,
              "costs": {"diag_setup": setup, "diag_rows": scored}}
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
                      "groups": len(record["groups"]), "rows": record["costs"]["diag_rows"]["rows"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
