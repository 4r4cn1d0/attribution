"""Watch the 7-8B hosts; when one is done, copy its outputs, check them locally, pull and verify the e1 states (KD5),
then stop it (administrative; K2 of T4: the ADAPTATION of the stage-1 kit's finisher.py, itself from
runkit/family-probe/finisher.py; the light check covers every sealed unit of the pulled tree, not round1 only).

7-8B changes (K2): after the light check, for every host role, the state rule's pull while the pod still has its SSH
address (STATE_PULLS: host.py pull-states HOST e1, then states_tool.py check HOST e1; the OLMo 3 kit's finisher), and
only then the stop; finished.json carries a "states" entry per checkpoint ({pulled, verified, file, bytes, sha256,
check | note}); a pull or check that fails leaves the status review-needed-stopped and the states on the pod's volume;
the states-*.tar is never removed (it is the backup copy; the light pull-*.tar is transport and is removed as before).
The stage-1 kit's similarity check (B14's 1B pass) has no 7-8B counterpart and is gone.

    caffeinate -i python3.11 finisher.py [INTERVAL_SECONDS]      (caffeinate keeps the Mac awake while a pod bills)

A host is done when its outer receipt exists on the pod (job-outer/process-receipt.json), whatever its exit. Then:
pull the light tar (no model states), unpack it into retrieved/HOST/tree, scan it for secrets (secret_scan.py: a
pattern in the model's evaluation text is only counted, model_text_pattern_hits; anywhere else the host is marked
secret-found, not verified, and the lead tells the user to revoke the token at once), run the light check of every
sealed unit (the engine's verify ran on the pod), stop the pod (never delete) and write hosts/HOST/finished.json.
After 3 failed light pulls the pod is stopped too (the records stay on its volume).

Review fixes (8 October):
- the stop is always reached once a host is finished, also when a step of finish() fails (finisher-error-stopped);
  it first moves the in-pod stop to 2 min from now (extend-cap 120) and then stops the pod through host.py, which
  retries and confirms EXITED. An unconfirmed stop is written to hosts/HOST/stop-pending.json and retried every round;
- the watch lasts until 3 h past the latest stop of every host: its pod.json cap or a later cap-override.json (an
  approved extension), or for a host without a pod yet the watch's start plus launch.py's 2 h plus its cap; it never
  ends while a stop is pending. The deadline is recomputed every round;
- the finisher removes the token variables from its own environment when it starts (it never needs them).
Round 31 (K5; cert runbook D9): a host that a deferral or requeue moved (plan_tool.moved_hosts, as seal.py) and that is
not recorded done (a-5, a-6, a-7: setup failed, stopped, never pulled; a requeue needs a confirmed stop) never gets a
finished.json. The watch treats it as finished: it is not watched, it sets no deadline, and "every planned host is
finished" no longer waits for it.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stage1_rules as rules  # noqa: E402
import secret_scan  # noqa: E402
import plan_tool  # noqa: E402  (round 31, K5: moved_hosts, the seal's helper)

REMOTE = "/workspace/attribution-headroom"
INTERVAL = 180                      # seconds between rounds; the first argument overrides it
MAX_PULL_FAILURES = 3
LAUNCH_HOURS = 2                    # launch.py's MAX_HOURS: a host may be created that long after the watch starts
AFTER_STOP_HOURS = 3
STATE_PULLS = ("e1",)               # KD5, the state rule: the e1 states of every unit; init and q are left open by the records


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def log(**fields) -> None:
    print(json.dumps({"utc": now(), **fields}), flush=True)


def tool(*args: str) -> subprocess.CompletedProcess:
    env = secret_scan.scrubbed(os.environ, rules.TOKEN_ENV_NAMES)
    return subprocess.run([sys.executable, str(HERE / "host.py"), *args], capture_output=True, text=True, env=env)


def parse_utc(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def host_stop(host: str) -> dt.datetime | None:
    """The host's latest stop: its pod.json cap or a later cap-override.json; None before the pod exists."""
    folder = HERE / "hosts" / host
    if not (folder / "pod.json").exists():
        return None
    stop = parse_utc(json.loads((folder / "pod.json").read_text())["cap_stop_utc"])
    if (folder / "cap-override.json").exists():
        stop = max(stop, parse_utc(json.loads((folder / "cap-override.json").read_text())["stop_at_utc"]))
    return stop


def moved_undone(p: dict) -> set:
    """Round 31 (K5): the hosts a deferral or requeue moved (plan_tool.moved_hosts) that are not recorded done: finished
    for the watch (they never get a finished.json)."""
    return {host for host in plan_tool.moved_hosts(p) if not (p["hosts"].get(host) or {}).get("done")}


def finished_for_watch(p: dict, host: str) -> bool:
    return (HERE / "hosts" / host / "finished.json").exists() or host in moved_undone(p)


def deadline(p: dict, started: dt.datetime) -> dt.datetime:
    """3 h past every host's latest stop (review fix 13); a moved, not-done host sets none (K5)."""
    ends, skip = [], moved_undone(p)
    for host, job in p["hosts"].items():
        if host in skip:
            continue
        stop = host_stop(host)
        ends.append(stop if stop is not None else started + dt.timedelta(hours=LAUNCH_HOURS + job["cap_hours"]))
    return max(ends, default=started) + dt.timedelta(hours=AFTER_STOP_HOURS)


def pull_failed(host: str) -> int:
    """Count a failed light pull for HOST and return the count so far."""
    path = HERE / "hosts" / host / "pull-failures.txt"
    count = (int(path.read_text()) if path.exists() else 0) + 1
    path.write_text(f"{count}\n")
    return count


def plan() -> dict:
    return json.loads((HERE / "plan.json").read_text())


def watched(p: dict | None = None) -> list[str]:
    skip = moved_undone(p) if p is not None else set()            # K5: a moved, not-done host is not watched
    return sorted(q.parent.name for q in (HERE / "hosts").glob("*/pod.json")
                  if not (q.parent / "finished.json").exists() and q.parent.name not in skip)


def stops_pending() -> list[str]:
    return sorted(p.parent.name for p in (HERE / "hosts").glob("*/stop-pending.json"))


def outer(host: str) -> str:
    override = HERE / "hosts" / host / "outer.txt"      # a restarted host's new outer receipt folder
    if override.exists():
        return override.read_text().strip()
    return "job-outer"


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


def check_states(host: str, checkpoint: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "states_tool.py"), "check", host, checkpoint], capture_output=True,
                          text=True, env=secret_scan.scrubbed(os.environ, rules.TOKEN_ENV_NAMES))


def pull_states(host: str) -> dict:
    """The state rule's pull while the pod still has its SSH address (KD5; the OLMo 3 kit's finisher): for every
    checkpoint of STATE_PULLS, host.py pull-states (the tar into retrieved/HOST/, never removed) and states_tool.py
    check (every state file a unit's COMPLETE.json lists, by hash). Never raises: a failure is recorded, the states
    stay on the pod's volume, and the lead repeats the pull by hand once the user has started the pod
    (states_tool.py rule)."""
    out = {}
    for checkpoint in STATE_PULLS:
        entry = {"pulled": False, "verified": False}
        pulled = tool("pull-states", host, checkpoint)
        lines = pulled.stdout.strip().splitlines()
        if pulled.returncode == 0 and lines:
            try:
                record = json.loads(lines[-1])
                entry.update({k: record[k] for k in ("file", "bytes", "sha256") if k in record}, pulled=True)
            except (ValueError, TypeError):
                entry["note"] = "pull-states printed no record"
        else:
            entry["note"] = (pulled.stderr.strip() or f"pull-states exit {pulled.returncode}")[-300:]
        if entry["pulled"]:
            checked = check_states(host, checkpoint)
            entry["verified"] = checked.returncode == 0
            entry["check"] = (checked.stdout.strip() if checked.returncode == 0 else checked.stderr.strip())[-300:]
        out[checkpoint] = entry
        if entry["verified"]:
            log(host=host, event="states-verified", checkpoint=checkpoint, file=entry.get("file"), check=entry["check"])
        else:
            log(host=host, event="states-not-verified", checkpoint=checkpoint, note=entry.get("note"), check=entry.get("check"),
                alert="the states stay on the pod's volume: the user starts the pod, then host.py get, pull-states, "
                      "states_tool.py check, host.py stop (states_tool.py rule); nothing is deleted")
    return out


def light_check(host: str, tree: pathlib.Path) -> dict:
    """Without the model states: every other file a unit's COMPLETE.json lists must be present and hash as listed;
    the engine's full verify ran on the pod (JOB-DONE.json). Missing .safetensors files are expected."""
    results = {}
    for unit in sorted(p.parent for p in tree.rglob("COMPLETE.json")):
        listed = json.loads((unit / "COMPLETE.json").read_text())["files"]
        bad, skipped = [], 0
        for rel, digest in listed.items():
            path = unit / rel
            if rel.endswith(".safetensors") and not path.exists():
                skipped += 1; continue
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                bad.append(rel)
        results[str(unit.relative_to(tree))] = {"exit": 0 if not bad else 1,
                                                "tail": f"bad {bad[:5]}; states left on the pod: {skipped}"}
    with open(HERE / "retrieved" / host / "verified.jsonl", "a") as handle:
        handle.write(json.dumps({"utc": now(), "kind": "light check (engine verify ran on the pod)", "results": results}) + "\n")
    return results


def stop_pod(host: str) -> subprocess.CompletedProcess:
    """Two paths (review fix 10): the in-pod timer to 2 min from now, then host.py stop (retried and confirmed)."""
    tool("extend-cap", host, "120")
    return tool("stop", host)


def finish(host: str, receipt: dict) -> None:
    role = plan()["hosts"][host]["role"]
    record = {"utc": now(), "status": None, "outer_exit": receipt.get("exit_code"),
              "outer_elapsed_min": round(receipt.get("elapsed_s", 0) / 60, 1)}
    try:
        # every role: results and receipts only; model states stay on the pod's volume
        if tool("pull-light", host).returncode:
            failures = pull_failed(host)
            log(host=host, event="pull-failed", failures=failures)
            if failures < MAX_PULL_FAILURES:
                return                                       # tried again next round; the pod is not stopped yet
            record["status"] = "pull-failed-stopped"         # the records stay on the pod's volume
        else:
            tree = unpack(host)
            scan = secret_scan.scan_tree(tree)
            record.update(model_text_pattern_hits=scan["model_text_pattern_hits"], secret_hits=len(scan["secret_hits"]))
            status = "stopped"
            if scan["secret_hits"]:
                status = "secret-found"
                log(host=host, event="secret-found", hits=scan["secret_hits"][:10],
                    action="the lead tells the user to revoke the token at once; nothing is deleted")
            else:      # addendum §29 point 4: every stage-1 role (w1_18, cert, certify, job, diagnostics, arms), any role
                results = light_check(host, tree)
                job_done = json.loads((tree / "JOB-DONE.json").read_text()) if (tree / "JOB-DONE.json").exists() else {}
                ok = receipt.get("exit_code") == 0 and job_done.get("ok") is True and \
                    all(r["exit"] == 0 for r in results.values())
                record["states"] = pull_states(host)         # KD5: before the stop; a stopped pod has no SSH address
                ok = ok and all(entry["verified"] for entry in record["states"].values())
                status = "verified-and-stopped" if ok else "review-needed-stopped"
                log(host=host, event="verified", units=len(results), ok=ok)
            record["status"] = status
    except Exception as exc:  # noqa: BLE001 - review fix 10: a failing step never skips the stop
        record.update(status="finisher-error-stopped", error=type(exc).__name__)
        log(host=host, event="finisher-error", error=type(exc).__name__)
    stopped = stop_pod(host)
    record.update(utc=now(), stop=stopped.stdout.strip()[-300:], stop_confirmed=stopped.returncode == 0)
    folder = HERE / "hosts" / host
    if stopped.returncode != 0:
        (folder / "stop-pending.json").write_text(json.dumps({"utc": now(), "exit": stopped.returncode}) + "\n")
        log(host=host, event="stop-unconfirmed", alert="the pod may still bill: the stop is retried every round")
    (folder / "finished.json").write_text(json.dumps(record, indent=1) + "\n")
    if record["status"] in ("stopped", "verified-and-stopped"):   # the light archive is only transport: its contents are
        removed = []                                               # checked; the states-*.tar is the backup copy and stays
        for tar in sorted((HERE / "retrieved" / host).glob("pull-*.tar")):
            removed.append(tar.name); tar.unlink()
        record["removed_archives"] = removed
    log(host=host, event="finished", **record)


def retry_stops() -> None:
    for host in stops_pending():
        stopped = tool("stop", host)
        log(host=host, event="stop-retried", exit=stopped.returncode)
        if stopped.returncode == 0:
            pending = HERE / "hosts" / host / "stop-pending.json"
            pending.rename(pending.with_name("stop-confirmed-later.json"))


def main() -> int:
    secret_scan.scrub_process(os.environ, rules.TOKEN_ENV_NAMES)      # the disputed review item: never needed here
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else INTERVAL
    started = dt.datetime.now(dt.timezone.utc)
    while dt.datetime.now(dt.timezone.utc) < deadline(plan(), started) or stops_pending():
        retry_stops()
        p = plan()
        if all(finished_for_watch(p, h) for h in p["hosts"]) and not stops_pending():
            log(event="every planned host is finished"); return 0
        hosts = watched(p)
        ready = []
        for host in hosts:
            if not any((HERE / "hosts" / host / "orchestrate.jsonl").read_text().count(e) for e in ("job-started",)) \
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
        time.sleep(interval)
    log(event="watch ended", deadline=deadline(plan(), started).isoformat(timespec="seconds"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
