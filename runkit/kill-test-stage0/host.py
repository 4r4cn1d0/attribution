"""Administrative host tool for kill-test Stage 0 (no experiment logic).

    host.py create HOST        one A100-SXM4-80GB pod with the in-pod stop timer (the host's cap); refuses a second
    host.py get HOST           refresh the pod record (status, connection)
    host.py ssh HOST 'CMD'     run a command on the pod
    host.py send HOST LOCAL REMOTE SHA256   copy a file to the pod and check its SHA-256 there
    host.py fetch HOST REMOTE LOCAL         copy one file from the pod (used for small records)
    host.py pull HOST          copy the run outputs and receipts back, as a tar, into retrieved/HOST/
    host.py stop HOST          stop the pod (never terminate or delete)

The RunPod key comes from RUNPOD_OPERATOR_API_KEY (the user's secrets file) and goes only into the
Authorization header. Records are written per host under hosts/HOST/ without secrets.
Adapted from tmp/study-v2-20261004/host.py (4 October run).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLAN = HERE / "plan.json"
REST = "https://rest.runpod.io/v1"
GPU = "NVIDIA A100-SXM4-80GB"
IMAGE = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
MAX_PRICE = 1.75
REMOTE_ROOT = "/workspace/attribution-headroom"
PULL_ITEMS = ("round1 job-process-* job-outer base-job.json cuda-preflight-* "
              "preflight-process-* preflight-outer worker-bootstrap-process-001 setup-001 BOOTSTRAP-READY.json "
              "PREFLIGHT-DONE.json JOB-DONE.json model-download-receipt.json environment-linux.lock")
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
                                              "Accept": "application/json", "User-Agent": "attribution-killtest-stage0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            return response.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode("utf-8", "replace")[:500]}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def plan() -> dict:
    return json.loads(PLAN.read_text())


def folder(host: str) -> pathlib.Path:
    if host not in plan()["hosts"]:
        raise SystemExit(f"{host} is not a host of the round-1 plan")
    path = HERE / "hosts" / host
    path.mkdir(parents=True, exist_ok=True)
    return path


def save(path: pathlib.Path, record) -> None:
    path.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")


def name_of(host: str) -> str:
    """The pod name; a retry after a pod that never came up carries the suffix in hosts/HOST/attempt.txt."""
    suffix_file = HERE / "hosts" / host / "attempt.txt"
    suffix = suffix_file.read_text().strip() if suffix_file.exists() else ""
    return f"attribution-killtest-{host}{suffix}"     # e.g. attribution-killtest-s0-1101


def state(host: str) -> dict:
    record = json.loads((folder(host) / "pod.json").read_text())
    if record.get("name") != name_of(host) or not record.get("id"):
        raise SystemExit("the pod record does not belong to this host")
    return record


def create(host: str) -> dict:
    root = folder(host)
    cap_hours = plan()["hosts"][host]["cap_hours"]
    if (root / "pod.json").exists() or (root / "create-intent.json").exists():
        raise SystemExit("a pod was already requested for this host; reconcile before creating another")
    status, pods = api("GET", "/pods")
    if status != 200 or not isinstance(pods, list):
        raise SystemExit(f"cannot list pods ({status})")
    if any(p.get("name") == name_of(host) for p in pods if isinstance(p, dict)):
        raise SystemExit("a pod with this host's name already exists")
    settings_path = root / "timer-settings.json"
    subprocess.run([str(ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"), "-m", "experiments.durability",
                    "pod-timer-settings", "--state-dir", "/workspace/.pod-timer", "--cap-minutes", str(int(cap_hours * 60)),
                    "--out", str(settings_path)], cwd=ROOT, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                   stdout=subprocess.DEVNULL)
    settings = json.loads(settings_path.read_text())
    env = {**settings["env"], "PUBLIC_KEY": (HERE / "ssh/key.pub").read_text().strip(),
           "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "TOKENIZERS_PARALLELISM": "false"}
    request = {"name": name_of(host), "imageName": IMAGE, "gpuTypeIds": [GPU], "gpuCount": 1, "cloudType": "SECURE",
               "interruptible": False, "containerDiskInGb": 60, "volumeInGb": 20, "volumeMountPath": "/workspace",
               "ports": ["22/tcp"], "supportPublicIp": True, "env": env, "dockerStartCmd": settings["docker_start_cmd"]}
    save(root / "create-intent.json", {"utc": now(), "cap_stop_utc": settings["cap_stop_utc"], "cap_hours": cap_hours,
                                        "request_without_env": {k: v for k, v in request.items() if k != "env"},
                                        "env_names": sorted(env)})
    status, pod = api("POST", "/pods", request)
    save(root / "create-result.json", {"utc": now(), "status": status,
                                        "pod": {k: pod.get(k) for k in SAFE} if status in (200, 201) else pod})
    if status not in (200, 201) or not isinstance(pod, dict) or not pod.get("id"):
        raise SystemExit(f"pod creation failed ({status}); see create-result.json")
    record = {**{k: pod.get(k) for k in SAFE}, "host": host, "created_utc": now(), "cap_stop_utc": settings["cap_stop_utc"]}
    save(root / "pod.json", record)
    price = pod.get("costPerHr")
    if not isinstance(price, (int, float)) or price > MAX_PRICE:
        s, _ = api("POST", f"/pods/{pod['id']}/stop")
        save(root / "price-guard-stop.json", {"utc": now(), "costPerHr": price, "stop_status": s})
        raise SystemExit(f"price {price}/h above {MAX_PRICE}; stop requested ({s})")
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
    status, answer = api("POST", f"/pods/{record['id']}/stop")
    result = {"utc": now(), "status": status}
    with open(folder(host) / "stops.jsonl", "a") as handle:
        handle.write(json.dumps(result) + "\n")
    return result


def main() -> int:
    command, host, *rest = sys.argv[1:]
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
        print(json.dumps(stop(host))); return 0
    raise SystemExit("unknown command")


if __name__ == "__main__":
    sys.exit(main())
