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
under judges/BLOCK/) are sealed with it. Round 30 (addendum §30 gap 2; the lead's R3): a block with a judge launch
refuses unless its judge-completion record (plan_tool.py record-judges) names every judge that no not-run decision
names and is valid now: judges/BLOCK/judge-files-index.json at the record's index_sha256, every indexed file present
at its SHA-256, no unindexed top-level judge-named file (subfolders such as pods/ are allowed), and exactly one file
per judge for each required unit, keyed by COMPLETE.json SHA-256 (plan_tool.judge_files_check: plan.json's arm jobs
and B10 units plus the block's pinned re-judged units). The seal lists the record's and the index's SHA-256
("judge_record"); every file under judges/BLOCK/ is hashed as sealed. ``status`` shows each judge-completion record
(tags, exits, answers judged, hashes) and whether it is valid now. Round 31 (K1): a released judge launch that a
recorded judge not-run decision names (record-block-a-not-run for block A, record-judge-not-run for every other block)
is not needed; the seal lists the decisions under "judge_not_run" (judge and decision SHA-256), and ``status`` prints
one line per record-judge-not-run decision (block, judges, SHA-256, valid or INVALID). Round 30 (R6): a block host
that a deferral or requeue moved and that is not done (a-5, a-6, a-7: setup failed, never pulled) is skipped, as block_complete skips
it, and listed under "moved" with its targets (its pulled tree, if any, is still hashed); an unmoved host that is not
done still refuses. (R7: ``status`` ends a pod's time at its first confirmed stop or finished.json.)
``block`` refuses a block that is not complete (every launch released, judge launches included, every host recorded
done with complete jobs or moved; round 3c, VP3b-3: for block A also every job the recorded block-A plan requires
has a completion record or a recorded not-run decision, plan_tool.block_a_open, and the refusal names the open
jobs), a host whose pulled tree is missing, and a second seal of one block. Block A's seal lists its not-run
decisions by job name and SHA-256 ("not_run"). Every seal lists the block's jobs recorded complete (not pulled) under
the lead's unpulled outputs decision (addendum §29 point 3: "not_pulled", by host, index, job name, unit path and the
decision's SHA-256, with no file hash: those units are not in the pulled tree). plan_tool's init-block for "certify"
and "B" refuses until block A's seal is recorded.
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
    files, moved_to, moved = [], plan_tool.moved_hosts(plan), []
    for host in hosts:
        tree = HERE / "retrieved" / host / "tree"
        if not plan["hosts"][host].get("done"):
            if host not in moved_to:
                fail(f"{host}: record-done first")
            moved.append({"host": host, "to": moved_to[host], "pulled_tree": tree.is_dir()})   # round 30 (R6)
            if not tree.is_dir():
                continue                          # moved before anything was pulled (a-5, a-6, a-7: setup failed)
        if not tree.is_dir():
            fail(f"{host}: no pulled tree")
        for p in sorted(tree.rglob("*")):
            if p.is_file():
                files.append({"host": host, "path": p.relative_to(tree).as_posix(), "sha256": mac.sha(p),
                              "class": classify(p.name)})
    judged = plan_tool.judges_needed(plan, block)     # round 30 (R3): every judge launch's judge, less the not-run ones
    folder = JUDGES / block
    judge_files = sorted(p for p in folder.rglob("*") if p.is_file()) if folder.is_dir() else []
    judge_check = plan_tool.judge_record_checked(plan, block) if judged else None   # judge_files_check inside
    if judged and (judge_check is None or not set(judged) <= set(judge_check["judges"])):
        fail(f"block {block}: no valid judge-completion record names {', '.join(judged)} (plan_tool.py record-judges "
             f"{block}; its judge files go under judges/{block}/)")
    for p in judge_files:
        files.append({"host": f"judges/{block}", "path": p.relative_to(folder).as_posix(), "sha256": mac.sha(p),
                      "class": "sealed"})
    counts = {"files": len(files), "sealed": sum(f["class"] == "sealed" for f in files),
              "readable": sum(f["class"] == "readable" for f in files)}
    not_run = sorted(plan_tool.block_a_not_run(plan).items()) if block == "A" else []   # round 3c (VP3b-3)
    not_pulled = plan_tool.not_pulled_jobs(plan, block)      # §29 point 3: complete on the pod, unit not fetched
    record = {"kind": SEAL_KIND, "version": 1, "block": block, "utc": mac.utc(), "hosts": hosts,
              "readable_patterns": list(READABLE_PATTERNS), "files": files, "counts": counts,
              "not_run": [{"job": label, "decision_sha256": digest} for label, digest in not_run]}
    record["not_pulled"] = not_pulled
    record["moved"] = moved                       # round 30 (R6): moved and never done; its jobs ran on its targets
    record["judge_record"] = None if judge_check is None else {   # round 30 (R3): hashes and counts only
        k: judge_check[k] for k in ("record_sha256", "index_sha256", "judges", "units", "files", "other_files")}
    record["judge_not_run"] = [{"judge": key, "decision_sha256": digest}   # round 31 (K1): every block's route
                               for key, digest in sorted(plan_tool.judges_decided(plan, block).items())]
    SEALS.mkdir(exist_ok=True)
    out.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    digest = mac.sha(out)
    plan.setdefault("seals", {})[block] = {"path": str(out.relative_to(HERE)), "sha256": digest, **counts}
    mac.save_plan(plan)
    mac.operator_action({"action": "seal", "block": block, "sha256": digest, **counts})
    return {"block": block, "seal_sha256": digest, **counts}


def _utc(text) -> dt.datetime:
    return dt.datetime.fromisoformat(str(text).replace("Z", "+00:00"))


def first_confirmed_stop(path, start: dt.datetime):
    """Round 30 (R7): the time of the pod's first confirmed stop in hosts/HOST/stops.jsonl (host.py stop's records:
    utc, desiredStatus, confirmed) at or after its creation, or None. A stopped kit pod is never restarted, so its time
    ends there; status() ends a pod's time at the earlier of this and finished.json's utc. Unreadable lines are
    skipped."""
    path = pathlib.Path(path)
    if not path.is_file():
        return None
    for line in path.read_text().splitlines():
        try:
            r = json.loads(line)
            at = _utc(r["utc"]) if isinstance(r, dict) and r.get("confirmed") is True else None
            if at is not None and at >= start:
                return at
        except (ValueError, KeyError, TypeError):
            continue
    return None


def judge_status(plan: dict, block: str, entry: dict) -> str:
    """One status line per judge-completion record (round 30, R2): its SHA-256, each judge's tag, exit and number of
    answers judged, the index SHA-256, and whether the record is valid now (judge_record_valid: re-hashed, the index
    and the judge files checked). No judge file is read; no HB, Granite, yes, unparsed or harm count exists here."""
    try:
        check = plan_tool.judge_record_valid(plan, block, entry)
        state = f"valid: {check['units']} required units, {check['files']} indexed files"
    except SystemExit as exc:
        state = f"INVALID: {exc}"
    judges = ", ".join(f"{k} {e['tag']} exit {e['exit']} judged {e['judged']}"
                       + (" known-answer gate passed" if e.get("known_answer_passed") is True else "")
                       for k, e in sorted(entry["judges"].items()))
    return f"judges {block}: record {entry['sha256'][:16]}, {judges}; index {entry['index_sha256'][:16]}; {state}"


def status() -> list[str]:
    """One line per host (block, launch, engine, cap, job kinds and statuses, hours and cost) and one per seal;
    reads plan.json, hosts/HOST/pod.json, finished.json and stops.jsonl only. Round 30 (R7): a pod's time ends at
    the earlier of its finished.json utc and its first confirmed stop (stops.jsonl), else now (a pod still running);
    before, a pod stopped without a finisher record (a-5, a-6, a-7) counted until now."""
    plan = mac.load_plan()
    now = dt.datetime.now(dt.timezone.utc)
    rows, cost = [], 0.0
    for host, h in plan["hosts"].items():
        folder = HERE / "hosts" / host
        pod = json.loads((folder / "pod.json").read_text()) if (folder / "pod.json").exists() else None
        fin = json.loads((folder / "finished.json").read_text()) if (folder / "finished.json").exists() else None
        hrs, stopped = 0.0, None
        if pod:
            start = _utc(pod["created_utc"])
            stopped = first_confirmed_stop(folder / "stops.jsonl", start)    # round 30 (R7)
            ends = [t for t in (_utc(fin["utc"]) if fin else None, stopped) if t is not None]
            end = min(ends) if ends else now
            hrs = (end - start).total_seconds() / 3600
            cost += hrs * (pod.get("costPerHr") or 0)
        jobs = ",".join(f"{j['kind']}:{j.get('status')}" for j in h["jobs"])
        state = (fin or {}).get("status") or ("stopped (confirmed)" if stopped else "")
        rows.append(f"{host:8s} block {h['block']:7s} launch {h['launch']} engine {h['engine']} cap "
                    f"{h['cap_hours']:5.2f} h {hrs:5.2f} h {jobs} {state}".rstrip())
    for block, b in plan.get("blocks", {}).items():
        rows.append(f"block {block}: launches released {b['released']}/{len(b['launches'])}, need "
                    f"${b['need']['need_usd']:.2f}, funding ${b['funding']['amount_usd']:.2f}")
    for block, s in plan.get("seals", {}).items():
        rows.append(f"seal {block}: {s['files']} files ({s['sealed']} sealed), sha256 {s['sha256']}")
    for block, entry in sorted(((plan.get("records") or {}).get("judges") or {}).items()):
        rows.append(judge_status(plan, block, entry))
    for e in (plan.get("records") or {}).get("judge_not_run") or []:     # round 31 (K1)
        problem = plan_tool.judge_not_run_problem(e)
        rows.append(f"judges {e.get('block')} not run: {', '.join(e.get('judges') or [])} by decision "
                    f"{str(e.get('sha256'))[:16]}; {'INVALID: ' + problem if problem else 'valid'}")
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
