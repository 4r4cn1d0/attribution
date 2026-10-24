"""The block seal and a seal-safe status (B15; brief §4 G5; REV4 §1.3 LW-35; administrative; stdlib only).

    python3.11 seal.py block BLOCK    write seals/block-BLOCK.json: every file of the block's pulled trees by path and
                                      SHA-256 (never a value), and record its SHA-256 in plan.json
    python3.11 seal.py status         cost and completion only, from plan.json, pod.json and finished.json

After block A only its cost ledgers, completion records and adapter fingerprints are read; its U, HB, O, task-loss and
coherence outputs stay sealed by SHA-256 until block B is complete or a recorded decision ends stage 1 without it.
So the seal hashes files and never parses one: each file is classed "readable" when its name matches
READABLE_PATTERNS (the runner names its cost ledgers, completion records and fingerprint records so) and "sealed"
otherwise, and nothing here prints a file's content. An engine unit's COMPLETE.json carries its evaluation summary
(task loss, safety, over-refusal, harm), so COMPLETE.json is sealed; the completion record that stays readable is the
runner's JOB-DONE.json (statuses, units and SHA-256 only). A block's judge outputs (the per-arm judge files, written
under judges/BLOCK/) are sealed with it: a block with a judge launch refuses until that folder holds its files.
``block`` refuses a block that is not complete (every launch released, judge launches included, every host recorded
done with complete jobs or moved; round 3c, VP3b-3: for block A also every job the recorded block-A plan requires
has a completion record or a recorded not-run decision, plan_tool.block_a_open, and the refusal names the open
jobs), a host whose pulled tree is missing, and a second seal of one block. Block A's seal lists its not-run
decisions by job name and SHA-256 ("not_run"). plan_tool's init-block for "certify" and "B" refuses until block A's
seal is recorded.
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gateb_mac as mac  # noqa: E402
import plan_tool  # noqa: E402

SEALS = HERE / "seals"
JUDGES = HERE / "judges"                          # judges/BLOCK/: the block's per-arm judge files (sealed)
SEAL_KIND = "stage1 block seal"
READABLE_PATTERNS = ("JOB-DONE.json", "*cost-ledger*.json", "*adapter-fingerprint*.json", "process-receipt.json")


def fail(message: str):
    raise SystemExit(message)


def classify(name: str) -> str:
    return "readable" if any(fnmatch.fnmatch(name, p) for p in READABLE_PATTERNS) else "sealed"


def seal_block(block: str) -> dict:
    plan = mac.load_plan()
    if block not in plan["blocks"]:
        fail(f"block {block} is not planned")
    if block in plan.get("seals", {}):
        fail(f"block {block} is already sealed")
    if not plan_tool.block_complete(plan, block):
        fail(f"block {block} is not complete" + (plan_tool.block_a_open_note(plan) if block == "A" else ""))
    out = SEALS / f"block-{block}.json"
    if out.exists():
        fail(f"{out.name} already exists")
    hosts = sorted(n for n, h in plan["hosts"].items() if h["block"] == block)
    files = []
    for host in hosts:
        if not plan["hosts"][host].get("done"):
            fail(f"{host}: record-done first")
        tree = HERE / "retrieved" / host / "tree"
        if not tree.is_dir():
            fail(f"{host}: no pulled tree")
        for p in sorted(tree.rglob("*")):
            if p.is_file():
                files.append({"host": host, "path": p.relative_to(tree).as_posix(), "sha256": mac.sha(p),
                              "class": classify(p.name)})
    judged = any("judge" in launch for launch in plan["blocks"][block]["launches"])
    folder = JUDGES / block
    judge_files = sorted(p for p in folder.rglob("*") if p.is_file()) if folder.is_dir() else []
    if judged and not judge_files:
        fail(f"block {block}: its judge launch's files are not in judges/{block}/")
    for p in judge_files:
        files.append({"host": f"judges/{block}", "path": p.relative_to(folder).as_posix(), "sha256": mac.sha(p),
                      "class": "sealed"})
    counts = {"files": len(files), "sealed": sum(f["class"] == "sealed" for f in files),
              "readable": sum(f["class"] == "readable" for f in files)}
    not_run = sorted(plan_tool.block_a_not_run(plan).items()) if block == "A" else []   # round 3c (VP3b-3)
    record = {"kind": SEAL_KIND, "version": 1, "block": block, "utc": mac.utc(), "hosts": hosts,
              "readable_patterns": list(READABLE_PATTERNS), "files": files, "counts": counts,
              "not_run": [{"job": label, "decision_sha256": digest} for label, digest in not_run]}
    SEALS.mkdir(exist_ok=True)
    out.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    digest = mac.sha(out)
    plan.setdefault("seals", {})[block] = {"path": str(out.relative_to(HERE)), "sha256": digest, **counts}
    mac.save_plan(plan)
    mac.operator_action({"action": "seal", "block": block, "sha256": digest, **counts})
    return {"block": block, "seal_sha256": digest, **counts}


def status() -> list[str]:
    """One line per host (block, launch, engine, cap, job kinds and statuses, hours and cost) and one per seal;
    reads plan.json, hosts/HOST/pod.json and finished.json only."""
    plan = mac.load_plan()
    now = dt.datetime.now(dt.timezone.utc)
    rows, cost = [], 0.0
    for host, h in plan["hosts"].items():
        folder = HERE / "hosts" / host
        pod = json.loads((folder / "pod.json").read_text()) if (folder / "pod.json").exists() else None
        fin = json.loads((folder / "finished.json").read_text()) if (folder / "finished.json").exists() else None
        hrs = 0.0
        if pod:
            start = dt.datetime.fromisoformat(pod["created_utc"])
            end = dt.datetime.fromisoformat(fin["utc"]) if fin else now
            hrs = (end - start).total_seconds() / 3600
            cost += hrs * (pod.get("costPerHr") or 0)
        jobs = ",".join(f"{j['kind']}:{j.get('status')}" for j in h["jobs"])
        rows.append(f"{host:8s} block {h['block']:7s} launch {h['launch']} engine {h['engine']} cap "
                    f"{h['cap_hours']:5.2f} h {hrs:5.2f} h {jobs} {(fin or {}).get('status') or ''}".rstrip())
    for block, b in plan.get("blocks", {}).items():
        rows.append(f"block {block}: launches released {b['released']}/{len(b['launches'])}, need "
                    f"${b['need']['need_usd']:.2f}, funding ${b['funding']['amount_usd']:.2f}")
    for block, s in plan.get("seals", {}).items():
        rows.append(f"seal {block}: {s['files']} files ({s['sealed']} sealed), sha256 {s['sha256']}")
    rows.append(f"estimated pod cost so far (this stage-1 kit): ${cost:.2f}")
    return rows


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "block":
        print(json.dumps(seal_block(argv[1])))
        return 0
    if argv == ["status"]:
        print("\n".join(status()))
        return 0
    fail("usage: seal.py block BLOCK | seal.py status")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
