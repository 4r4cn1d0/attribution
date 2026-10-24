"""Administrative host tool for one Gate B host (no experiment logic; from runkit/family-probe/host.py).

Gate B changes (brief B8): the pod name is attribution-gateb-HOST; PULL_ITEMS add the anchor output (anchor-*), the
jobs' engine job files, the diagnostics and Gate C outputs (round1 holds the attributes unit; gatec/), deferral.json,
the pod-side environment records (BUNDLE-CHECKED.json, pip-version.txt) and the per-job JOB-DONE records
(job-done/); the gated download is gone (OLMo-2-1B and Qwen3Guard are open repositories).

    host.py create HOST        one A100-SXM4-80GB pod with the in-pod stop timer (the host's cap); refuses a second
    host.py reconcile HOST     stop an untracked pod of this host's name, else archive the earlier attempt's records
    host.py get HOST           refresh the pod record (status, connection)
    host.py ssh HOST 'CMD'     run a command on the pod
    host.py send HOST LOCAL REMOTE SHA256   copy a file to the pod and check its SHA-256 there
    host.py fetch HOST REMOTE LOCAL         copy one file from the pod (used for small records)
    host.py pull HOST          copy the run outputs and receipts back, as a tar, into retrieved/HOST/
    host.py stop HOST          stop the pod (never terminate or delete): retried, then confirmed by reading the pod until
                               its desiredStatus is EXITED; exit 1 when that cannot be confirmed (review fix 10)
    host.py extend-cap HOST SECONDS   the only way to move the pod's stop: an extension first passes budget.py check for
                                  the added hours at the planning price ([D20]); writes hosts/HOST/cap-override.json

Review fixes (8 October): a create whose reply fails, or a pod with this host's name and no pod.json, is an orphan:
it is stopped (confirmed), recorded in hosts/HOST/orphans.jsonl, and the next try uses a new name suffix; an earlier
attempt's intent is archived only after the pod listing shows no pod with this host's name; extend-cap holds
budget.lock() from its check through the override.

The RunPod key comes from RUNPOD_OPERATOR_API_KEY (the user's secrets file) and goes only into the
Authorization header. Records are written per host under hosts/HOST/ without secrets.
Adapted from tmp/study-v2-20261004/host.py (4 October run).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budget  # noqa: E402
import stage1_rules as rules  # noqa: E402
import secret_scan  # noqa: E402

ROOT = HERE.parents[1]
PLAN = HERE / "plan.json"
REST = "https://rest.runpod.io/v1"
GPU = "NVIDIA A100-SXM4-80GB"
IMAGE = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
PLANNING_PRICE = rules.PLANNING_PRICE_USD  # [D20]: extend-cap's guard price
MAX_PRICE = rules.MAX_PRICE_USD            # [D20] as amended (the user, rev. 17): create refuses above $10.00/h
REMOTE_ROOT = "/workspace/attribution-headroom"
PULL_ITEMS = ("round1 job-* jobs anchor-* gatec cuda-preflight-* "
              "preflight-process-* preflight-outer worker-bootstrap-process-001 setup-001 BOOTSTRAP-READY.json "
              "BUNDLE-CHECKED.json pip-version.txt PREFLIGHT-DONE.json JOB-DONE.json deferral.json "
              "model-download-receipt.json environment-linux.lock")
STOP_TRIES, CONFIRM_TRIES = 5, 12
SLEEP = time.sleep                  # replaced in tests


def clean_env() -> dict:
    """This process's environment without any token variable (for every child process; review fix 5)."""
    return secret_scan.scrubbed(os.environ, rules.TOKEN_ENV_NAMES)
SAFE = ("id", "name", "desiredStatus", "costPerHr", "machineId", "lastStartedAt", "lastStatusChange", "publicIp",
        "portMappings", "gpu", "volumeInGb", "containerDiskInGb")


def key() -> str:
    value = os.environ.get("RUNPOD_OPERATOR_API_KEY", "").strip()
    if not value:
        raise SystemExit("RUNPOD_OPERATOR_API_KEY is not set (source the secrets file)")
    return value


def api(method: str, path: str, payload=None):
    request = urllib.request.Request(REST + path, method=method,
                                     data=None if payload is None else json.dumps(payload).encode(),
                                     headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json",
                                              "Accept": "application/json", "User-Agent": "attribution-gate-b"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            return response.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode("utf-8", "replace")[:500]}
    except (urllib.error.URLError, OSError, ValueError) as exc:   # a timeout or a dropped link: no reply (status 0)
        return 0, {"error": type(exc).__name__}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def plan() -> dict:
    return json.loads(PLAN.read_text())


def folder(host: str) -> pathlib.Path:
    if host not in plan()["hosts"]:
        raise SystemExit(f"{host} is not a host of the Gate B plan")
    path = HERE / "hosts" / host
    path.mkdir(parents=True, exist_ok=True)
    return path


def save(path: pathlib.Path, record) -> None:
    path.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")


def name_of(host: str) -> str:
    """The pod name; a retry after a pod that never came up carries the suffix in hosts/HOST/attempt.txt."""
    suffix_file = HERE / "hosts" / host / "attempt.txt"
    suffix = suffix_file.read_text().strip() if suffix_file.exists() else ""
    return f"attribution-s1-{host}{suffix}"     # e.g. attribution-s1-A-1


def state(host: str) -> dict:
    record = json.loads((folder(host) / "pod.json").read_text())
    if record.get("name") != name_of(host) or not record.get("id"):
        raise SystemExit("the pod record does not belong to this host")
    return record


def stop_id(pod_id: str) -> dict:
    """Stop one pod by id: retry the stop, then read the pod until its desiredStatus is EXITED (never delete)."""
    attempts, status = 0, None
    for attempt in range(STOP_TRIES):
        attempts = attempt + 1
        status, _ = api("POST", f"/pods/{pod_id}/stop")
        if status in (200, 201, 204):
            break
        SLEEP(min(60, 5 * 2 ** attempt))
    seen = None
    for _ in range(CONFIRM_TRIES):
        code, pod = api("GET", f"/pods/{pod_id}")
        seen = pod.get("desiredStatus") if code == 200 and isinstance(pod, dict) else seen
        if seen == "EXITED":
            break
        SLEEP(10)
    return {"utc": now(), "status": status, "attempts": attempts, "desiredStatus": seen, "confirmed": seen == "EXITED"}


def named_pods(host: str) -> list[dict]:
    status, pods = api("GET", "/pods")
    if status != 200 or not isinstance(pods, list):
        raise SystemExit(f"cannot list pods ({status})")
    return [p for p in pods if isinstance(p, dict) and p.get("name") == name_of(host)]


def orphan(host: str, pods: list[dict], why: str) -> None:
    """Stop every pod of this host's name that has no pod.json, record it, and move the host to a new name suffix."""
    root = folder(host)
    with open(root / "orphans.jsonl", "a") as handle:
        for pod in pods:
            handle.write(json.dumps({"utc": now(), "id": pod.get("id"), "name": pod.get("name"), "why": why,
                                     "stop": stop_id(pod["id"])}) + "\n")
    suffix_file = root / "attempt.txt"
    previous = suffix_file.read_text().strip() if suffix_file.exists() else ""
    number = int(previous[2:]) + 1 if previous.startswith("-r") else 2
    suffix_file.write_text(f"-r{number}\n")


def archive_attempt(root: pathlib.Path) -> None:
    """Rename an earlier attempt's records (never delete them)."""
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for name in ("create-intent.json", "create-result.json", "timer-settings.json"):
        if (root / name).exists():
            (root / name).rename(root / f"{name[:-5]}-failed-{stamp}.json")


def reconcile(host: str) -> None:
    """Before a create (and before its budget check): a pod of this host's name without pod.json is stopped and
    recorded; otherwise the earlier attempt's records are archived, so no stale intent is counted twice."""
    root = folder(host)
    if (root / "pod.json").exists():
        raise SystemExit("a pod was already created for this host; reconcile before creating another")
    found = named_pods(host)
    if found:                                    # review fixes 11 and 19: never a second pod; stop the untracked one
        orphan(host, found, "a pod with this host's name exists without pod.json")
        raise SystemExit("a pod with this host's name existed without pod.json: it was stopped (orphans.jsonl)")
    archive_attempt(root)                        # only now: the listing shows no pod with this name


def price_allowed(price) -> bool:
    """[D20] as amended (the user, brief revision 17): a create-time price is accepted when it is a finite number at most
    MAX_PRICE ($10.00/h); a missing (None), non-numeric, boolean, NaN or infinite costPerHr, or one above the limit, is
    refused."""
    return (isinstance(price, (int, float)) and not isinstance(price, bool) and math.isfinite(price)
            and price <= MAX_PRICE)


def create(host: str) -> dict:
    root = folder(host)
    cap_hours = plan()["hosts"][host]["cap_hours"]
    reconcile(host)
    settings_path = root / "timer-settings.json"
    subprocess.run([str(ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"), "-m", "experiments.durability",
                    "pod-timer-settings", "--state-dir", "/workspace/.pod-timer", "--cap-minutes", str(int(cap_hours * 60)),
                    "--out", str(settings_path)], cwd=ROOT, check=True, env={**clean_env(), "PYTHONDONTWRITEBYTECODE": "1"},
                   stdout=subprocess.DEVNULL)
    settings = json.loads(settings_path.read_text())
    env = {**settings["env"], "PUBLIC_KEY": (HERE / "ssh/key.pub").read_text().strip(),
           "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "TOKENIZERS_PARALLELISM": "false"}
    sizes = plan()["hosts"][host]
    request = {"name": name_of(host), "imageName": IMAGE, "gpuTypeIds": [GPU], "gpuCount": 1, "cloudType": "SECURE",
               "interruptible": False, "containerDiskInGb": sizes["container_disk_gb"], "volumeInGb": sizes["volume_gb"],
               "volumeMountPath": "/workspace",
               "ports": ["22/tcp"], "supportPublicIp": True, "env": env, "dockerStartCmd": settings["docker_start_cmd"]}
    save(root / "create-intent.json", {"utc": now(), "cap_stop_utc": settings["cap_stop_utc"], "cap_hours": cap_hours,
                                        "request_without_env": {k: v for k, v in request.items() if k != "env"},
                                        "env_names": sorted(env)})
    status, pod = api("POST", "/pods", request)
    save(root / "create-result.json", {"utc": now(), "status": status,
                                        "pod": {k: pod.get(k) for k in SAFE} if status in (200, 201) else pod})
    if status not in (200, 201) or not isinstance(pod, dict) or not pod.get("id"):
        for _ in range(3):                       # review fix 11: the pod may exist although the reply failed
            SLEEP(20)
            found = named_pods(host)
            if found:
                orphan(host, found, f"created although the create reply failed ({status})")
                raise SystemExit("the create reply failed but the pod exists: it was stopped (orphans.jsonl)")
        raise SystemExit(f"pod creation failed ({status}); see create-result.json")
    record = {**{k: pod.get(k) for k in SAFE}, "host": host, "created_utc": now(), "cap_stop_utc": settings["cap_stop_utc"]}
    save(root / "pod.json", record)
    price = pod.get("costPerHr")
    if not price_allowed(price):        # [D20] as amended: a missing, non-finite or over-limit price stops the pod at once
        result = stop_id(pod["id"])
        save(root / "price-guard-stop.json", {"utc": now(), "costPerHr": price, "stop": result})
        raise SystemExit(f"price {price!r}/h is missing, not finite or above ${MAX_PRICE:.2f}/h; "
                         f"stop confirmed: {result['confirmed']}")
    return record


def get(host: str) -> dict:
    record = state(host)
    status, pod = api("GET", f"/pods/{record['id']}")
    if status != 200:
        raise SystemExit(f"pod read failed ({status})")
    latest = {**{k: pod.get(k) for k in SAFE}, "utc": now()}
    save(folder(host) / "pod-latest.json", latest)
    return latest


def connection(host: str) -> tuple[str, int]:
    latest = get(host)
    ip, ports = latest.get("publicIp"), latest.get("portMappings") or {}
    port = ports.get("22") if isinstance(ports, dict) else None
    if not ip or not port:
        raise SystemExit("no SSH address yet (the pod may still be starting)")
    return ip, int(port)


def ssh_base(host: str) -> list[str]:
    ip, port = connection(host)
    return ["-F", "/dev/null", "-i", str(HERE / "ssh/key"), "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=accept-new",
            "-o", f"UserKnownHostsFile={folder(host) / 'known_hosts'}", "-o", "BatchMode=yes", "-o", "ForwardAgent=no",
            "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=4", "-p", str(port),
            f"root@{ip}"]


def ssh(host: str, command: str) -> int:
    return subprocess.run(["ssh", *ssh_base(host), command]).returncode


def _scp_opts(base: list[str]) -> tuple[list[str], str, str]:
    port, target = base[base.index("-p") + 1], base[-1]
    return [a for a in base[:-1] if a not in ("-p", port)], port, target


def send(host: str, local: str, remote: str, sha256: str) -> int:
    path = pathlib.Path(local).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
        raise SystemExit("the local file does not have the given SHA-256")
    if not re.fullmatch(r"/workspace/attribution-headroom/[A-Za-z0-9._/-]+", remote) or ".." in remote:
        raise SystemExit("remote path must be a plain path under the run folder")
    base = ssh_base(host)
    opts, port, target = _scp_opts(base)
    if subprocess.run(["ssh", *base, f"mkdir -p {REMOTE_ROOT} $(dirname {remote})"]).returncode:
        return 1
    if subprocess.run(["scp", *opts, "-P", port, str(path), f"{target}:{remote}"]).returncode:
        return 1
    check = f"test \"$(sha256sum {remote} | cut -c1-64)\" = {sha256}"
    return subprocess.run(["ssh", *base, check]).returncode


def fetch(host: str, remote: str, local: str) -> int:
    if not re.fullmatch(r"/workspace/attribution-headroom/[A-Za-z0-9._/-]+", remote) or ".." in remote:
        raise SystemExit("remote path must be a plain path under the run folder")
    base = ssh_base(host)
    opts, port, target = _scp_opts(base)
    pathlib.Path(local).parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(["scp", *opts, "-P", port, f"{target}:{remote}", local]).returncode


def pull(host: str, light: bool = False) -> int:
    """A complete tar of the run outputs and receipts, kept only if the transfer finished. ``light`` leaves out
    every .safetensors file (the saved model states stay on the pod's volume)."""
    out = HERE / "retrieved" / host
    out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    part, final = out / f"pull-{stamp}.tar.part", out / f"pull-{stamp}.tar"
    exclude = "--exclude='*.safetensors' " if light else ""
    remote = f"cd {REMOTE_ROOT} && ls -d {PULL_ITEMS} 2>/dev/null | tar -cf - {exclude}-T -"
    with open(part, "wb") as handle:
        code = subprocess.run(["ssh", *ssh_base(host), remote], stdout=handle).returncode
    if code != 0 or part.stat().st_size == 0:
        part.unlink(missing_ok=True)
        return code or 1
    part.rename(final)
    digest = hashlib.sha256(final.read_bytes()).hexdigest()
    with open(out / "pulls.jsonl", "a") as handle:
        handle.write(json.dumps({"utc": now(), "file": final.name, "bytes": final.stat().st_size, "sha256": digest}) + "\n")
    return 0


def stop(host: str) -> dict:
    record = state(host)
    result = stop_id(record["id"])
    with open(folder(host) / "stops.jsonl", "a") as handle:
        handle.write(json.dumps(result) + "\n")
    return result


def extend_cap(host: str, seconds: float, runner=subprocess.run) -> dict:
    """Move the in-pod stop to SECONDS from now. An extension past the recorded stop first passes the budget guard for
    the added hours at PLANNING_PRICE (the user approves each one; the lead records it in operator-leases.jsonl)."""
    record = state(host)
    override = folder(host) / "cap-override.json"
    with budget.lock():                       # review fix 12: no other kit's check between this check and the override
        current = json.loads(override.read_text())["stop_at_utc"] if override.exists() else record["cap_stop_utc"]
        target = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds)
        added_h = (target - dt.datetime.fromisoformat(current.replace("Z", "+00:00"))).total_seconds() / 3600
        if added_h > 0:
            guard = runner([sys.executable, str(HERE / "budget.py"), "check", f"{added_h:.4f}", str(PLANNING_PRICE)],
                           cwd=HERE, capture_output=True, text=True, env=clean_env())
            if guard.returncode != 0:
                raise SystemExit("the budget guard refused the extension")
        done = runner(["ssh", *ssh_base(host), f"cd /workspace/attribution-headroom && python3 extend_cap.py {int(seconds)}"],
                      capture_output=True, text=True, env=clean_env())
        line = json.loads(done.stdout.strip().splitlines()[-1]) if done.returncode == 0 and done.stdout.strip() else {}
        if not (line.get("governs") and line.get("acknowledged")):
            raise SystemExit("the pod timer did not acknowledge the new stop")
        result = {"utc": now(), "lease": line["lease"], "stop_at_utc": line["stop_at_utc"], "added_hours": round(added_h, 4)}
        save(override, result)
    return result


def main() -> int:
    command, host, *rest = sys.argv[1:]
    if command == "extend-cap":
        print(json.dumps(extend_cap(host, float(rest[0])))); return 0
    if command == "reconcile":
        reconcile(host); return 0
    if command == "create":
        print(json.dumps(create(host), indent=1)); return 0
    if command == "get":
        print(json.dumps(get(host), indent=1)); return 0
    if command == "ssh":
        return ssh(host, rest[0])
    if command == "send":
        return send(host, *rest)
    if command == "fetch":
        return fetch(host, *rest)
    if command == "pull":
        return pull(host)
    if command == "pull-light":
        return pull(host, light=True)
    if command == "stop":
        result = stop(host)
        print(json.dumps(result)); return 0 if result["confirmed"] else 1
    raise SystemExit("unknown command")


if __name__ == "__main__":
    sys.exit(main())
