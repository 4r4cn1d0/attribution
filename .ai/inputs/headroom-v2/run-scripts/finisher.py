"""Watch the round-1 hosts; when one is done, copy its outputs, verify them locally, then stop it (administrative).

    python3.11 finisher.py [INTERVAL_SECONDS]

A host is done when its outer receipt exists on the pod (lead-outer or job-outer/process-receipt.json), whatever
its exit. Then: (lead) collect the edit files; pull one complete tar of the outputs; unpack it into
retrieved/HOST/tree; (job) verify every sealed unit with the packed engine (mirror/, cwd and PYTHONPATH) and the
remote paths mapped to the tree; stop the pod (never delete); write hosts/HOST/finished.json. A host whose job
failed or whose units do not verify is also stopped (its volume keeps everything) and marked for review.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
MIRROR = HERE / "mirror"
REMOTE = "/workspace/attribution-headroom"
INTERVAL = int(sys.argv[1]) if len(sys.argv) > 1 else 180


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def log(**fields) -> None:
    print(json.dumps({"utc": now(), **fields}), flush=True)


def tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "host.py"), *args], capture_output=True, text=True)


def plan() -> dict:
    return json.loads((HERE / "plan.json").read_text())


def watched() -> list[str]:
    return sorted(p.parent.name for p in (HERE / "hosts").glob("*/pod.json") if not (p.parent / "finished.json").exists())


def outer(host: str) -> str:
    override = HERE / "hosts" / host / "outer.txt"      # a restarted host's new outer receipt folder
    if override.exists():
        return override.read_text().strip()
    return "lead-outer" if plan()["hosts"][host]["role"] == "lead" else "job-outer"


def done_on_pod(host: str) -> dict | None:
    out = tool("ssh", host, f"cat {REMOTE}/{outer(host)}/process-receipt.json 2>/dev/null")
    if out.returncode or not out.stdout.strip():
        return None
    return json.loads(out.stdout)


def unpack(host: str) -> pathlib.Path:
    out = HERE / "retrieved" / host
    newest = sorted(out.glob("pull-*.tar"))[-1]
    tree = out / "tree"
    shutil.rmtree(tree, ignore_errors=True)
    tree.mkdir()
    with tarfile.open(newest) as t:
        t.extractall(tree, filter="data")
    return tree


def verify(host: str, tree: pathlib.Path) -> dict:
    results = {}
    for unit in sorted(p.parent for p in (tree / "round1").glob("*/COMPLETE.json")):
        r = subprocess.run([str(PY), "-m", "experiments.safety_selection", "verify", "--run", str(unit),
                            "--prepared", str(MIRROR / "prepared-v2"),
                            "--map", f"{REMOTE}/round1={tree / 'round1'}", "--map", f"round1={tree / 'round1'}"],
                           cwd=MIRROR, capture_output=True, text=True,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(MIRROR)})
        results[unit.name] = {"exit": r.returncode, "tail": (r.stdout + r.stderr)[-800:]}
    with open(HERE / "retrieved" / host / "verified.jsonl", "a") as handle:
        handle.write(json.dumps({"utc": now(), "results": results}) + "\n")
    return results


def light_check(host: str, tree: pathlib.Path) -> dict:
    """Without the model states: every other file a unit's COMPLETE.json lists must be present and hash as listed;
    the engine's full verify ran on the pod (JOB-DONE.json). Missing .safetensors files are expected."""
    import hashlib
    results = {}
    for unit in sorted(p.parent for p in (tree / "round1").glob("*/COMPLETE.json")):
        listed = json.loads((unit / "COMPLETE.json").read_text())["files"]
        bad, skipped = [], 0
        for rel, digest in listed.items():
            path = unit / rel
            if rel.endswith(".safetensors") and not path.exists():
                skipped += 1; continue
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                bad.append(rel)
        results[unit.name] = {"exit": 0 if not bad else 1, "tail": f"bad {bad[:5]}; states left on the pod: {skipped}"}
    with open(HERE / "retrieved" / host / "verified.jsonl", "a") as handle:
        handle.write(json.dumps({"utc": now(), "kind": "light check (engine verify ran on the pod)", "results": results}) + "\n")
    return results


def finish(host: str, receipt: dict) -> None:
    role = plan()["hosts"][host]["role"]
    if role == "lead":
        c = subprocess.run([sys.executable, str(HERE / "orchestrate.py"), "collect-lead"], capture_output=True, text=True)
        log(host=host, event="collect-lead", exit=c.returncode, out=c.stdout[-600:])
    # every role: results and receipts only; model states stay on the pod's volume
    if tool("pull-light", host).returncode:
        log(host=host, event="pull-failed"); return
    tree = unpack(host)
    status = "stopped"
    if role in ("job", "first"):
        results = light_check(host, tree)
        job_done = json.loads((tree / "JOB-DONE.json").read_text()) if (tree / "JOB-DONE.json").exists() else {}
        ok = receipt.get("exit_code") == 0 and job_done.get("ok") is True and bool(results) and \
            all(r["exit"] == 0 for r in results.values())
        status = "verified-and-stopped" if ok else "review-needed-stopped"
        log(host=host, event="verified", units=len(results), ok=ok)
    elif receipt.get("exit_code") != 0:
        status = "review-needed-stopped"
    stopped = tool("stop", host)
    record = {"utc": now(), "status": status, "outer_exit": receipt.get("exit_code"),
              "outer_elapsed_min": round(receipt.get("elapsed_s", 0) / 60, 1), "stop": stopped.stdout.strip()}
    (HERE / "hosts" / host / "finished.json").write_text(json.dumps(record, indent=1) + "\n")
    if not status.startswith("review"):      # the archive is only transport: its contents are unpacked and checked
        removed = []
        for tar in sorted((HERE / "retrieved" / host).glob("pull-*.tar")):
            removed.append(tar.name); tar.unlink()
        record["removed_archives"] = removed
    log(host=host, event="finished", **record)


def main() -> int:
    deadline = time.time() + 10 * 3600
    while time.time() < deadline:
        if all((HERE / "hosts" / h / "finished.json").exists() for h in plan()["hosts"]):
            log(event="every planned host is finished"); return 0
        hosts = watched()
        ready = []
        for host in hosts:
            if not any((HERE / "hosts" / host / "orchestrate.jsonl").read_text().count(e) for e in ("lead-started", "job-started")) \
                    if (HERE / "hosts" / host / "orchestrate.jsonl").exists() else True:
                continue
            try:
                receipt = done_on_pod(host)
            except (json.JSONDecodeError, OSError):
                receipt = None
            if receipt is not None:
                ready.append((host, receipt))
        if ready:                         # finish done hosts in parallel, so none waits billed behind another's copy
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=len(ready)) as pool:
                list(pool.map(lambda item: finish(*item), ready))
        time.sleep(INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
