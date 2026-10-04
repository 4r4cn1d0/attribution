"""Cap-only self-stop check for the in-pod stop timer (4 October 2026).

Creates one small GPU pod whose only job is to run the stop timer with a cap, then watches it
from outside, read-only, until RunPod reports it stopped. Nothing here terminates or deletes
anything. If the pod has not stopped itself by cap + GRACE_SECONDS, it is stopped from here and
the check is recorded as failed.

    check.py precheck [--keychain]   balance, prices and stock of the candidate GPUs; no pod
    check.py create   [--keychain]   timer settings, then one pod (refuses a second one)
    check.py watch    [--keychain]   observe until stopped; emergency stop after the grace

Key: RUNPOD_OPERATOR_API_KEY from the environment, or with --keychain the macOS Keychain item
codex.attribution.runpod. The key goes only into Authorization headers; nothing records it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NAME = "attribution-pod-timer-check-20261004"
IMAGE = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
CANDIDATES = ["NVIDIA RTX A4000", "NVIDIA RTX A4500", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A5000",
              "NVIDIA RTX 4000 Ada Generation"]
MAX_PRICE = 0.40
CAP_MINUTES = 15
GRACE_SECONDS = 360
REST, V2, GRAPHQL = "https://rest.runpod.io/v1", "https://api.runpod.io/v2", "https://api.runpod.io/graphql"
SAFE_KEYS = ("id", "name", "desiredStatus", "costPerHr", "adjustedCostPerHr", "machineId", "lastStartedAt",
             "lastStatusChange", "image", "volumeInGb", "containerDiskInGb", "interruptible")


def get_key(use_keychain: bool) -> str:
    key = os.environ.get("RUNPOD_OPERATOR_API_KEY", "").strip()
    if not key and use_keychain:
        key = subprocess.run(["security", "find-generic-password", "-a", "spiderishi", "-s",
                              "codex.attribution.runpod", "-w"], capture_output=True, check=True).stdout.decode().strip()
    if not key:
        raise SystemExit("no RunPod key: set RUNPOD_OPERATOR_API_KEY or pass --keychain")
    return key


def call(key: str, method: str, url: str, payload=None):
    request = urllib.request.Request(url, method=method, data=None if payload is None else json.dumps(payload).encode(),
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                                              "Accept": "application/json", "User-Agent": "attribution-pod-timer-check"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            return response.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode("utf-8", "replace")[:400]}
    except (urllib.error.URLError, OSError) as exc:
        return None, {"error": type(exc).__name__}


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(moment: dt.datetime) -> str:
    return moment.isoformat(timespec="seconds")


def write(name: str, record) -> None:
    (HERE / name).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")


def append(name: str, record) -> None:
    with open(HERE / name, "a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def safe(pod) -> dict:
    return {k: pod.get(k) for k in SAFE_KEYS} if isinstance(pod, dict) else {"unexpected": str(type(pod))}


def precheck(key: str) -> dict:
    status, catalog = call(key, "GET", V2 + "/catalog/gpus")
    gpus = catalog.get("gpus", catalog) if isinstance(catalog, dict) else catalog
    offers = []
    for gpu in gpus if isinstance(gpus, list) else []:
        if gpu.get("id") in CANDIDATES:
            price = (gpu.get("price") or {}).get("secure")
            offers.append({"id": gpu["id"], "secure_price": price, "availability": gpu.get("availability"),
                           "secure": gpu.get("secure")})
    usable = sorted((o for o in offers if o["secure"] and o["availability"] != "NONE"
                     and isinstance(o["secure_price"], (int, float)) and o["secure_price"] <= MAX_PRICE),
                    key=lambda o: o["secure_price"])
    b_status, balance = call(key, "POST", GRAPHQL, {"query": "query { myself { clientBalance currentSpendPerHr } }"})
    me = (balance or {}).get("data", {}).get("myself") if isinstance(balance, dict) else None
    p_status, pods = call(key, "GET", REST + "/pods")
    existing = [p.get("id") for p in pods if isinstance(p, dict) and p.get("name") == NAME] if isinstance(pods, list) else None
    record = {"utc": iso(now()), "catalog_status": status, "offers": offers, "usable_in_price_order": [o["id"] for o in usable],
              "balance_status": b_status, "client_balance": None if not me else me.get("clientBalance"),
              "current_spend_per_hr": None if not me else me.get("currentSpendPerHr"),
              "pods_status": p_status, "existing_pods_with_this_name": existing,
              "running_pods": None if not isinstance(pods, list) else
              [{"id": p.get("id"), "name": p.get("name"), "desiredStatus": p.get("desiredStatus"), "costPerHr": p.get("costPerHr")}
               for p in pods if isinstance(p, dict)]}
    write("precheck.json", record)
    return record


def create(key: str) -> dict:
    if (HERE / "pod.json").exists() or (HERE / "create-intent.json").exists():
        raise SystemExit("a pod was already requested for this check; reconcile before creating another")
    pre = precheck(key)
    if pre["existing_pods_with_this_name"]:
        raise SystemExit("a pod with this check's name already exists")
    if not pre["usable_in_price_order"]:
        raise SystemExit("no candidate GPU is available at or below the price limit")
    settings_path = HERE / "settings.json"
    subprocess.run([str(ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"), "-m", "experiments.durability",
                    "pod-timer-settings", "--state-dir", "/workspace/.pod-timer", "--cap-minutes", str(CAP_MINUTES),
                    "--out", str(settings_path)], cwd=ROOT, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    settings = json.loads(settings_path.read_text())
    request = {"name": NAME, "imageName": IMAGE, "gpuTypeIds": pre["usable_in_price_order"],
               "gpuTypePriority": "custom", "gpuCount": 1, "cloudType": "SECURE", "interruptible": False,
               "containerDiskInGb": 20, "volumeInGb": 5, "volumeMountPath": "/workspace", "ports": [],
               "env": settings["env"], "dockerStartCmd": settings["docker_start_cmd"]}
    write("create-intent.json", {"utc": iso(now()), "cap_stop_utc": settings["cap_stop_utc"],
                                 "request_without_env": {k: v for k, v in request.items() if k != "env"},
                                 "env_names": sorted(settings["env"])})
    status, pod = call(key, "POST", REST + "/pods", request)
    write("create-result.json", {"utc": iso(now()), "status": status, "pod": safe(pod) if status in (200, 201) else pod})
    if status not in (200, 201) or not isinstance(pod, dict) or not pod.get("id"):
        raise SystemExit(f"pod creation failed (status {status}); see create-result.json")
    state = {**safe(pod), "created_utc": iso(now()), "cap_stop_utc": settings["cap_stop_utc"],
             "script_sha256": settings["script_sha256"]}
    write("pod.json", state)
    price = pod.get("costPerHr")
    if not isinstance(price, (int, float)) or price > MAX_PRICE:
        s, answer = call(key, "POST", f"{REST}/pods/{pod['id']}/stop")
        write("price-guard-stop.json", {"utc": iso(now()), "costPerHr": price, "stop_status": s})
        raise SystemExit(f"price {price}/h is above the limit; stop requested (status {s})")
    return state


def watch(key: str) -> int:
    state = json.loads((HERE / "pod.json").read_text())
    pod_id, cap = state["id"], dt.datetime.fromisoformat(state["cap_stop_utc"])
    emergency_at, emergency_done, first_started = cap + dt.timedelta(seconds=GRACE_SECONDS), None, None
    while True:
        status, pod = call(key, "GET", f"{REST}/pods/{pod_id}")
        t = now()
        obs = {"utc": iso(t), "status": status, **(safe(pod) if status == 200 else {"detail": pod})}
        append("observations.jsonl", obs)
        if status == 404:
            write("result.json", {"outcome": "pod absent", "utc": iso(t)})
            return 4
        if status == 200 and isinstance(pod, dict):
            if pod.get("lastStartedAt") and not first_started:
                first_started = pod.get("lastStartedAt")
            if pod.get("desiredStatus") in ("EXITED", "TERMINATED"):
                write("result.json", {"outcome": "self-stopped" if emergency_done is None else "stopped from outside",
                                      "self_stopped": emergency_done is None, "observed_stopped_utc": iso(t),
                                      "cap_stop_utc": state["cap_stop_utc"],
                                      "observed_seconds_after_cap": (t - cap).total_seconds(),
                                      "last_status_change": pod.get("lastStatusChange"), "last_started_at": first_started,
                                      "emergency_stop": emergency_done, "poll_seconds": 20})
                return 0 if emergency_done is None else 3
        if emergency_done is None and t >= emergency_at:
            s, answer = call(key, "POST", f"{REST}/pods/{pod_id}/stop")
            emergency_done = {"utc": iso(t), "status": s}
            write("emergency-stop.json", emergency_done)
        time.sleep(20)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["precheck", "create", "watch"])
    parser.add_argument("--keychain", action="store_true")
    args = parser.parse_args()
    key = get_key(args.keychain)
    if args.command == "precheck":
        print(json.dumps(precheck(key), indent=1))
        return 0
    if args.command == "create":
        print(json.dumps(create(key), indent=1))
        return 0
    return watch(key)


if __name__ == "__main__":
    sys.exit(main())
