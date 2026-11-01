"""Start a stopped stage-1 kit pod once, only so the running finisher pulls, light-checks and stops it (administrative;
the user's decision user_decision_restart_to_pull_block_b.json, a recorded deviation from PREREG revision 5 §9;
addendum §38).

    python restart_to_pull.py --kit KIT --decision FILE --sha256 H [--cap-minutes 60] [--dry-run]
                              [--retry-failed-start] [--zero-gpu] HOST [HOST ...]

Per host it refuses unless: the decision file hashes to H and names the host; the host has pod.json, a logged
job-started and no finished.json, restart-to-pull.json or cap-override.json (one start only); RunPod reads the pod
EXITED. Then it renames known_hosts (a restarted container has new SSH host keys; the kit's accept-new learns the new
one), writes restart-to-pull.json (the intent) and cap-override.json (the new stop: budget.py and the finisher count
it), PATCHes the pod's environment (the creation environment: timer-settings.json's env, PUBLIC_KEY and the two
constants, names equal to create-intent.json's env_names, with a fresh cap: POD_TIMER_CAP_ISSUED_UTC now and
POD_TIMER_CAP_STOP_UTC now + the cap; the in-pod timer obeys the most recently issued authority, so this cap outranks
the job-end lease), starts the pod if it still reads EXITED, and waits until it reads RUNNING with an SSH port. No job,
preflight or setup step runs. The finisher then pulls, scans, light-checks and stops the pod (never deletes it).
Records hold no secrets: API replies are cut to host.py's SAFE fields or an error string.

Second version (addendum §38 point 6): --retry-failed-start accepts a host whose earlier attempt's start failed (its
restart-to-pull.json has a start that did not return 200 and no running record): that attempt's restart-to-pull.json
and cap-override.json are renamed with the suffix -attempt-STAMP, and the host goes through the same steps again, so
the pod is still started at most once. --zero-gpu starts the pod with no GPU (RunPod's GraphQL podResumeZeroGpu, its
documented route to a stopped pod's volume when the machine's GPU is taken; REST start then returns 500): a pull needs
no GPU. The decision file must name the host and allow the retry (allows_retry_failed_start, allows_zero_gpu).
"""
import argparse, datetime as dt, hashlib, json, pathlib, sys, time

CAP_MAX_MIN = 60
WAIT_S, POLL_S = 900, 10


def utc(t: dt.datetime) -> str:
    return t.isoformat(timespec="milliseconds")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--cap-minutes", type=int, default=CAP_MAX_MIN)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--retry-failed-start", action="store_true")
    ap.add_argument("--zero-gpu", action="store_true")
    ap.add_argument("hosts", nargs="+")
    a = ap.parse_args()
    if not 15 <= a.cap_minutes <= CAP_MAX_MIN:
        raise SystemExit(f"--cap-minutes must be 15..{CAP_MAX_MIN} (the decision's limit)")
    kit = pathlib.Path(a.kit).resolve()
    sys.path.insert(0, str(kit))
    import host as H                                   # noqa: E402 - the kit's API wrapper, SAFE fields, records

    raw = pathlib.Path(a.decision).read_bytes()
    if hashlib.sha256(raw).hexdigest() != a.sha256:
        raise SystemExit("the decision file does not hash to --sha256")
    decision = json.loads(raw)
    if decision.get("kind") != "stage1 user decision: restart stopped kit pods once to pull":
        raise SystemExit("not the user's restart-to-pull decision")
    if a.retry_failed_start and decision.get("allows_retry_failed_start") is not True:
        raise SystemExit("the decision does not allow retrying a failed start")
    if a.zero_gpu and decision.get("allows_zero_gpu") is not True:
        raise SystemExit("the decision does not allow a zero-GPU start")
    failed = []
    for host in a.hosts:
        try:
            print(json.dumps(restart(H, kit, host, decision, a.sha256, a.cap_minutes, a.dry_run,
                                     a.retry_failed_start, a.zero_gpu)), flush=True)
        except SystemExit as exc:
            failed.append(host)
            print(json.dumps({"host": host, "refused_or_failed": str(exc)}), flush=True)
    return 1 if failed else 0


def failed_attempt(root: pathlib.Path) -> bool:
    """True when the host's restart-to-pull.json records a start that did not return 200 and no running pod."""
    earlier = json.loads((root / "restart-to-pull.json").read_text())
    return isinstance(earlier.get("start"), dict) and earlier["start"].get("status") != 200 and "running" not in earlier


def graphql_zero_gpu_start(H, pod_id: str) -> tuple:
    """RunPod's documented zero-GPU start (GraphQL podResumeZeroGpu); the key goes only into the header."""
    query = 'mutation { podResumeZeroGpu(input: {podId: "%s"}) { id desiredStatus } }' % pod_id
    request = H.urllib.request.Request("https://api.runpod.io/graphql", method="POST",
                                       data=json.dumps({"query": query}).encode(),
                                       headers={"Authorization": "Bearer " + H.key(), "Content-Type": "application/json",
                                                "Accept": "application/json", "User-Agent": "attribution-gate-b"})
    try:
        with H.urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read() or b"{}")
    except H.urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode("utf-8", "replace")[:500]}
    except (H.urllib.error.URLError, OSError, ValueError) as exc:
        return 0, {"error": type(exc).__name__}
    if body.get("errors"):
        return 500, {"error": json.dumps(body["errors"])[:500]}
    data = (body.get("data") or {}).get("podResumeZeroGpu") or {}
    return 200, {"id": data.get("id"), "desiredStatus": data.get("desiredStatus")}


def restart(H, kit: pathlib.Path, host: str, decision: dict, decision_sha: str, cap_min: int, dry: bool,
            retry: bool = False, zero_gpu: bool = False) -> dict:
    if host not in decision.get("hosts", []):
        raise SystemExit(f"{host} is not named by the decision")
    root = kit / "hosts" / host
    if retry:
        if not (root / "restart-to-pull.json").exists() or not failed_attempt(root):
            raise SystemExit(f"{host}: --retry-failed-start needs an earlier attempt whose start failed")
        if not dry:
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            for name in ("restart-to-pull", "cap-override"):
                if (root / f"{name}.json").exists():
                    (root / f"{name}.json").rename(root / f"{name}-attempt-{stamp}.json")
    for name in ("finished.json", "restart-to-pull.json", "cap-override.json"):
        if retry and dry and name != "finished.json":
            continue
        if (root / name).exists():
            raise SystemExit(f"{host}: {name} exists (finished, already restarted once, or an earlier override)")
    events = [json.loads(line).get("event") for line in (root / "orchestrate.jsonl").read_text().splitlines() if line]
    if "job-started" not in events:
        raise SystemExit(f"{host}: no logged job-started")
    record = H.state(host)                             # pod.json, checked against the host's pod name
    pod_id = record["id"]
    status, pod = H.api("GET", f"/pods/{pod_id}")
    if status != 200 or not isinstance(pod, dict) or pod.get("desiredStatus") != "EXITED":
        raise SystemExit(f"{host}: the pod does not read EXITED ({status}, "
                         f"{pod.get('desiredStatus') if isinstance(pod, dict) else None})")
    settings = json.loads((root / "timer-settings.json").read_text())
    intent = json.loads((root / "create-intent.json").read_text())
    env = {**settings["env"], "PUBLIC_KEY": (kit / "ssh/key.pub").read_text().strip(),
           "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "TOKENIZERS_PARALLELISM": "false"}     # as host.create builds it
    if sorted(env) != intent["env_names"]:
        raise SystemExit(f"{host}: the rebuilt environment's names differ from create-intent.json's")
    issued = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    stop_at = issued + dt.timedelta(minutes=cap_min)
    env["POD_TIMER_CAP_ISSUED_UTC"], env["POD_TIMER_CAP_STOP_UTC"] = utc(issued), utc(stop_at)
    rec = {"kind": "stage1 restart to pull", "host": host, "pod_id": pod_id, "decision_sha256": decision_sha,
           "retry_failed_start": retry, "zero_gpu": zero_gpu,
           "utc": H.now(), "cap_issued_utc": utc(issued), "cap_stop_utc": utc(stop_at), "cap_minutes": cap_min,
           "env_names": sorted(env), "before": {k: pod.get(k) for k in H.SAFE}}
    if dry:
        return {**rec, "dry_run": True}
    kh = root / "known_hosts"
    if kh.exists():
        rec["known_hosts_renamed_to"] = f"known_hosts-before-restart-{issued:%Y%m%dT%H%M%SZ}"
        kh.rename(root / rec["known_hosts_renamed_to"])
    H.save(root / "restart-to-pull.json", rec)        # the one-start marker, written before any API write
    H.save(root / "cap-override.json", {"utc": H.now(), "stop_at_utc": utc(stop_at), "lease": None,
                                        "source": "restart-to-pull (addendum §38)", "decision_sha256": decision_sha})
    status, reply = H.api("PATCH", f"/pods/{pod_id}", {"env": env})
    rec["patch"] = {"utc": H.now(), "status": status,
                    "reply": {k: reply.get(k) for k in H.SAFE} if status == 200 and isinstance(reply, dict) else reply}
    H.save(root / "restart-to-pull.json", rec)
    if status != 200:
        (root / "cap-override.json").rename(root / "cap-override-restart-failed.json")
        raise SystemExit(f"{host}: the environment update failed ({status}); see restart-to-pull.json")
    time.sleep(POLL_S)
    status, pod = H.api("GET", f"/pods/{pod_id}")
    seen = pod.get("desiredStatus") if status == 200 and isinstance(pod, dict) else None
    rec["after_patch"] = {"utc": H.now(), "desiredStatus": seen,
                          "start_cmd_unchanged": (pod.get("dockerStartCmd") == settings["docker_start_cmd"])
                          if isinstance(pod, dict) and "dockerStartCmd" in pod else None}
    if seen == "EXITED":
        status, reply = graphql_zero_gpu_start(H, pod_id) if zero_gpu else H.api("POST", f"/pods/{pod_id}/start")
        rec["start"] = {"utc": H.now(), "status": status, "route": "graphql podResumeZeroGpu" if zero_gpu else "rest start",
                        "reply": {k: reply.get(k) for k in H.SAFE} if status == 200 and isinstance(reply, dict) else reply}
        H.save(root / "restart-to-pull.json", rec)
        if status != 200:
            raise SystemExit(f"{host}: the start failed ({status}); see restart-to-pull.json")
    deadline, latest = time.time() + WAIT_S, {}
    while time.time() < deadline:
        latest = H.get(host)                           # refreshes pod-latest.json (the SSH address the kit reads)
        if latest.get("desiredStatus") == "RUNNING" and latest.get("publicIp") and \
                isinstance(latest.get("portMappings"), dict) and latest["portMappings"].get("22"):
            break
        time.sleep(POLL_S)
    rec["running"] = {"utc": H.now(), **{k: latest.get(k) for k in ("desiredStatus", "publicIp", "portMappings",
                                                                     "gpu", "costPerHr", "machineId", "lastStartedAt")}}
    H.save(root / "restart-to-pull.json", rec)
    if latest.get("desiredStatus") != "RUNNING":
        raise SystemExit(f"{host}: not RUNNING after {WAIT_S} s; see restart-to-pull.json")
    return {"host": host, "running": rec["running"]["utc"], "cap_stop_utc": rec["cap_stop_utc"],
            "gpu": latest.get("gpu"), "costPerHr": latest.get("costPerHr")}


if __name__ == "__main__":
    sys.exit(main())
