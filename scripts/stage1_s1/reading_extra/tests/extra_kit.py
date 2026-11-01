"""Synthetic additions for the reading-time readers' tests (tests only; no real data; every draw is seeded).

- ``with_caps(world)``: the builder's synthetic kit (synth_kit) with what oext_eval.py writes and synth_kit leaves out:
  each O-ext summary's ``route`` and ``flag_change`` (planted, seeded), and theta0's LN-14 transfer pass (a
  ``transfer_report`` job on block A's LN-12 host with job-I/transfer/ in oext_unit.py's layout); every COMPLETE.json,
  plan.json output and seal re-taken. Returns the planted values by (host, folder).
- ``cost_kit(root, reading)``: a small kit of plan.json, seals (files classed as seal.py classes them) and one
  job-I/cost-ledger.json per job in the job runner's format, beside one sealed file per job that holds a sentinel;
  returns the kit folder and each job's slot.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import synth_kit as sk

from scripts.stage1_s1.reading.settings import design

TREE = sk.TREE
SENTINEL = "SEALED-SENTINEL-z5"
STAGES = ("setup", "training", "greedy_generation", "sampled_generation", "judging", "scoring", "pod_overhead",
          "transform")
ROUTES = json.loads((TREE / "scripts" / "stage1_s1" / "settings" / "oext_eval.json").read_text())["routes"]


def flag_block(rng, n: int) -> dict:
    if n == 0:
        return {"prompts_with_both_forms": 0, "changed": 0, "share": None, "became_refused": 0,
                "became_not_refused": 0, "note": "generated at the cut cap: no full answer exists"}
    changed = int(rng.integers(0, 6))
    up = int(rng.integers(0, changed + 1))
    return {"prompts_with_both_forms": n, "changed": changed, "share": changed / n, "became_refused": up,
            "became_not_refused": changed - up, "note": None}


def _plant(path: Path, rng, branch: str) -> dict:
    doc = json.loads(path.read_text())
    fc = {"dev100": flag_block(rng, 100), "phtest": flag_block(rng, 0 if branch == "128" else 400)}
    doc.update(route=dict(ROUTES[branch]), flag_change=fc)
    sk.write(path, sk.jbytes(doc))
    return fc


def transfer_summary(n: int = 400, agree: int = 396, full: int = 50, cut: int = 49, passes: bool | None = None) -> dict:
    ok = 100 * agree >= 97 * n and 100 * abs(full - cut) <= 2 * n
    return {"kind": "stage1 o-ext transfer report", "version": 1, "checkpoint": "untuned", "branch": "128",
            "role": "transfer_report",
            "bar": {"prompts": n, "flags_agree": agree, "refused_full": full, "refused_cut": cut,
                    "count_move": abs(full - cut), "invalid_full": 1, "invalid_cut": 2,
                    "bar": {"min_flags_agree": 97, "max_count_move": 2, "per_prompts": 100},
                    "pass": ok if passes is None else passes},
            "bar_reading": "W1-18's bar read as shares of the PHTest count (synthetic)",
            "flag_change": {"prompts_with_both_forms": n, "changed": n - agree, "share": (n - agree) / n,
                            "became_refused": 0, "became_not_refused": n - agree, "note": None}}


def add_transfer(s, plan: dict, summary: dict, host: str = "a-2") -> int:
    jobs = plan["hosts"][host]["jobs"]
    i = len(jobs)
    folder = s.kit / "retrieved" / host / "tree" / f"job-{i}" / "transfer"
    sk.write(folder / "oext_transfer_generations.jsonl", sk.jsonl([{"prompt_id": p, "text": sk.TEXT} for p in sk.PH]))
    sk.write(folder / "oext_transfer_guard.jsonl", sk.jsonl([{"prompt_id": p, "raw": sk.TEXT} for p in sk.PH]))
    digest = sk.write(folder / "oext_transfer_summary.json", sk.jbytes(summary))
    sk.complete(folder, {"kind": "stage1-oext-unit", "identity": {}, "command": "transfer", "state": "untuned",
                         "branch": "128", "summary_file": {"oext_transfer_summary.json": digest}})
    jobs.append({"kind": "transfer_report", "arm": "theta0", "seed": None, "engine": "X", "status": "complete",
                 "unit": None, "complete_sha256": None,
                 "outputs": sk._outputs(s.kit / "retrieved" / host / "tree", f"job-{i}/transfer"), "reason": None})
    return i


def _rejudge(kit: Path, block: str, remap: dict) -> None:
    """The block's judge files of units whose COMPLETE.json changed (old -> new SHA-256), renamed and re-indexed as
    synth_kit.write_judges names them (the judge check keys every file by COMPLETE.json SHA-256)."""
    folder = kit / "judges" / block
    index_path = folder / "judge-files-index.json"
    if not remap or not index_path.is_file():
        return
    index = json.loads(index_path.read_text())
    for e in index["files"]:
        new = remap.get(e["complete_sha256"])
        if new is None:
            continue
        doc = json.loads((folder / e["file"]).read_text())
        (folder / e["file"]).unlink()
        doc["complete_sha256"] = new
        name = f"{e['file'].split('--')[0]}--{e['host']}--{e['unit']}--{new[:12]}.json"
        e.update(file=name, complete_sha256=new,
                 sha256=sk.write(folder / name, (json.dumps(doc, sort_keys=True, indent=2) + "\n").encode()))
    index_path.write_bytes((json.dumps(index, sort_keys=True, indent=2) + "\n").encode())


def with_caps(s, seed: int = 3, transfer: dict | None = None, transfers: int = 1) -> dict:
    """Plants route and flag_change into every O-ext summary of the world (module doc); ``transfers`` LN-14 passes
    (0 under Branch full, as the kit makes none there). Returns {(host, folder): flag_change}."""
    plan = s.plan()
    rng = np.random.default_rng(seed)
    planted, remap = {}, {}
    for host, h in sorted(plan["hosts"].items()):
        tree = s.kit / "retrieved" / host / "tree"
        for i, job in enumerate(h["jobs"]):
            outputs = job.get("outputs") or {}
            if f"job-{i}/oext/COMPLETE.json" in outputs:
                folder = tree / f"job-{i}" / "oext"
                planted[(host, f"job-{i}/oext")] = _plant(folder / "oext_summary.json", rng, s.branch)
                digest = sk.sha((folder / "oext_summary.json").read_bytes())
                sk.recomplete(folder, lambda d, x=digest: d.update(summary_file={"oext_summary.json": x}))
                job["outputs"] = sk._outputs(tree, f"job-{i}/oext")
            for u in job.get("units") or []:
                planted[(host, u["unit"])] = _plant(tree / u["unit"] / "eval" / "e1" / "oext_summary.json", rng,
                                                    s.branch)
                old = u["complete_sha256"]
                u["complete_sha256"] = sk.recomplete(tree / u["unit"])
                remap.setdefault(h["block"], {})[old] = u["complete_sha256"]
            if job.get("units"):
                job["complete_sha256"] = job["units"][0]["complete_sha256"]
    for _ in range(transfers if s.branch == "128" else 0):
        add_transfer(s, plan, transfer or transfer_summary())
    for block in sorted({h["block"] for h in plan["hosts"].values()}):
        _rejudge(s.kit, block, remap.get(block, {}))
        sk.seal_block(s.kit, plan, block)
    s.save_plan(plan)
    return planted


# ----- the cost kit -------------------------------------------------------------------------------------------------


def ledger_doc(host: str, i: int, job: dict, slot: float, steps: list) -> dict:
    stages = {k: 0.0 for k in STAGES}
    for name, seconds in steps:
        stages["training" if "calibrate" in name else "greedy_generation" if "oext" in name else "scoring"] += seconds
    return {"kind": "stage1 cost ledger", "version": 1, "host": host, "index": i, "job_kind": job["kind"],
            "job_id": None, "arm": job.get("arm"), "seed": job.get("seed"), "engine": "X", "engine_sha256": "e" * 64,
            "stages_s": stages, "slot_s": slot, "steps": [{"name": n, "seconds": v} for n, v in steps],
            "rule": "synthetic"}


def cost_kit(root: Path, reading: str = "plan_a_block_a_only", with_c0: bool = True,
             extra_ref_eval_seeds: tuple = ()) -> tuple:
    """(kit folder, {(host, index): slot}, plan) of a small kit (module doc): block A's diagnostics and LN-12 host,
    one host per four arm runs of the reading's new cells (spread over the reading's blocks: A; A and B under plan_a;
    A, B and C under plan_b), block B's references (and B10's certification job, last) when block B is read;
    ``extra_ref_eval_seeds`` appends one more ref_eval job per seed after them (no earlier draw moves)."""
    dsg = design(reading)
    rng = np.random.default_rng(11)
    kit = Path(root) / "kit"
    plan = {"name": "stage1-olmo", "records": {"plan_ab": {"code": "B" if reading == "plan_b" else "A"}},
            "blocks": {}, "hosts": {}, "seals": {}}
    slots = {}
    spec: dict = {"a-1": ("A", [{"kind": k, "arm": None, "seed": None} for k in
                                ("w1_18", "rep_pass", "untuned_answers", "l1_scan", "classifier")]),
                  "a-2": ("A", [{"kind": "regenerate", "arm": "a0", "seed": 1101},
                                {"kind": "o_only", "arm": "a0", "seed": 1101},
                                *([{"kind": "c0", "arm": "R", "seed": 1101}] if with_c0 else []),
                                {"kind": "retrain", "arm": "a0", "seed": 1102, "pulled": False}])}
    blocks = {"plan_a_block_a_only": ("A",), "plan_a": ("A", "B"), "plan_b": ("A", "B", "C")}[reading]
    runs = [(arm, j) for arm in dsg.arms for j in dsg.seeds[arm] if not (arm in ("a0", "R") and j <= 1103)]
    for n in range(0, len(runs), 4):
        block = blocks[(n // 4) % len(blocks)]
        spec[f"{block.lower()}-{3 + n // 4}"] = (block, [
            {"kind": "a0_arm" if arm == "a0" else "arm", "arm": arm, "seed": j} for arm, j in runs[n:n + 4]])
    if "B" in blocks:
        spec["b-ref"] = ("B", [{"kind": "ref_train", "arm": "G", "recipe": "G", "seed": 1105},
                               {"kind": "ref_train", "arm": "bqi", "recipe": "bqi", "seed": 1105},
                               {"kind": "ref_eval", "arm": "a0", "seed": 1105,
                                "points": ["scale:0.9", "scale:0.75", "scale:0.5", "prefix"]},
                               {"kind": "safe_lora", "arm": "a0", "seed": 1105,
                                "points": ["default", "conditional", "certify"]},
                               {"kind": "b10_certify", "arm": "a0", "seed": 1105, "points": ["certify", "scale:0"]},
                               *[{"kind": "ref_eval", "arm": "a0", "seed": j,
                                  "points": ["scale:0.9", "scale:0.75", "scale:0.5", "prefix"]}
                                 for j in extra_ref_eval_seeds]])
    for host, (block, jobs) in spec.items():
        tree = kit / "retrieved" / host / "tree"
        plan["hosts"][host] = {"block": block, "done": True, "jobs": []}
        for i, job in enumerate(jobs):
            job = {**job, "engine": "X", "status": "complete", "unit": None, "complete_sha256": None,
                   "reason": None}
            slot = float(np.round(rng.uniform(500.0, 5000.0), 3))
            tag = f"job-{i}"
            if job["kind"] == "safe_lora":
                steps = [(f"{tag}-b10-regenerate", 300.0), (f"{tag}-vcheck", 20.0), (f"{tag}-check", 10.0)]
                steps += [(f"{tag}-{part}-{p}", 100.0 + 10 * k) for k, p in enumerate(job["points"])
                          for part in ("transform", "evaluate")]
            else:
                steps = [(f"{tag}-calibrate", slot * 0.6), (f"{tag}-oext", slot * 0.3)]
            sk.write(tree / tag / "out.json", json.dumps({"value": SENTINEL}).encode())
            outputs = {f"{tag}/out.json": sk.sha((tree / tag / "out.json").read_bytes())}
            if job.get("pulled") is not False:
                digest = sk.write(tree / tag / "cost-ledger.json", sk.jbytes(ledger_doc(host, i, job, slot, steps)))
                outputs[f"{tag}/cost-ledger.json"] = digest
                slots[(host, i)] = slot
            job["outputs"] = outputs
            plan["hosts"][host]["jobs"].append(job)
    for block in blocks:
        seal(kit, plan, block)
    sk.write(kit / "plan.json", sk.jbytes(plan))
    return kit, slots, plan


def seal(kit: Path, plan: dict, block: str) -> None:
    """seal.py's record: every file of the block's trees by path and SHA-256, classed readable or sealed."""
    files = []
    for host in sorted(plan["hosts"]):
        if plan["hosts"][host]["block"] != block:
            continue
        tree = kit / "retrieved" / host / "tree"
        for p in sorted(tree.rglob("*")):
            if p.is_file():
                files.append({"host": host, "path": p.relative_to(tree).as_posix(), "sha256": sk.sha(p.read_bytes()),
                              "class": "readable" if "cost-ledger" in p.name else "sealed"})
    rec = {"kind": "stage1 block seal", "version": 1, "block": block, "utc": "2026-10-29T00:00:00Z",
           "hosts": sorted(n for n, h in plan["hosts"].items() if h["block"] == block), "files": files,
           "counts": {"files": len(files)}, "not_run": [], "not_pulled": [], "moved": []}
    data = sk.jbytes(rec)
    sk.write(kit / "seals" / f"block-{block}.json", data)
    plan["seals"][block] = {"path": f"seals/block-{block}.json", "sha256": sk.sha(data), "files": len(files)}
