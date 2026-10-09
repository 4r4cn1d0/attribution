"""RunPod host layer of the judge pod (Mac side; administrative, no judge logic; stdlib only, Python 3.10+).

Written 8 October 2026 (19:48 UTC, clock checked); revised 8 October 2026 (20:47 UTC, clock checked) after the review:
the records' place, orphan stops and the price rule; revised again 8 October 2026 (21:48 UTC, clock checked) after the
second review: orphan names, a lost create reply, record appends that never raise, and the fetch timeout; revised a
third time 8 October 2026 (22:44 UTC, clock checked) after the third review: a 5xx create reply counts as lost (only a
4xx is a refusal), the name-suffix write after confirmed orphan stops never raises, and a budget.py that hangs or
cannot start is a refusal. Adapted from the family-probe kit's host.py (tmp/family-probe-olmo2-1b-g/host.py, SHA-256
29ac283b...) and orchestrate.py (wait_ssh, check; SHA-256 30f9fbe0...):

  - the same image (runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404), GPU type (NVIDIA A100-SXM4-80GB, one GPU),
    SECURE cloud, not interruptible, port 22 with a public IP, the kit's SSH key (its path only; never read here);
  - the same in-pod stop timer: `python -m experiments.durability pod-timer-settings --cap-minutes N` under the minimal
    venv, its env and start command given to RunPod at create; check() requires the timer armed, supervised and governed
    by the cap, and the GPU name;
  - the creation-time price check, with the user's rule of 8 Oct 2026, 20:17 UTC (research/FOCUS.md): no hourly price
    limit (PRICE_GUARD = inf), replaced on 9 Oct 2026 15:29 UTC by a $10/h limit (PRICE_GUARD = 10.0). A created pod whose costPerHr is not a finite number (missing, a string, a bool, NaN or
    inf) is still stopped at once (confirmed) and the create refuses. The budget guard prices a new pod at
    PLANNING_PRICE ($1.85/h, the kits' planning rate), and the launcher's cost upper bound uses the same rate;
  - the same reconcile: a pod of this host's name without pod.json is an orphan: stopped, recorded in orphans.jsonl,
    and the next try uses a new name suffix. An unconfirmed orphan stop raises StopUnconfirmed (the launcher's exit 7)
    with the listed pods' ids and names, before the name suffix moves, so the warning names the real pod;
  - after a create whose reply failed (or was interrupted, stop_orphans), the pods of this name are listed up to 3 times
    20 s apart, as the kits' host.create does; a pod found there is stopped as an orphan. A listing that fails all the
    time cannot conclude: StopUnconfirmed. A failed reply that is not a refusal (status 0: a timeout, a dropped link or
    an unreadable body; a 2xx reply without a pod id; a 5xx reply, which a gateway may send for a create that went
    through; any status but a 4xx) with no pod in any listing raises CreateLost: RunPod may still list the pod later,
    so the launcher exits 7 with CHECK-CONSOLE. Only a 4xx reply with no pod listed is a refused create;
  - the same stop: POST /pods/{id}/stop retried, then GET /pods/{id} until desiredStatus is EXITED (never delete);
    the appends to stops.jsonl and orphans.jsonl and the name-suffix write (attempt.txt) never raise, so a full disk
    cannot turn a confirmed stop into an error (records_dropped counts what was not written);
  - the same send (scp, then sha256sum on the pod must equal the given SHA-256) and fetch (scp of one file, with a
    timeout the caller may shorten: the launcher's salvage has a total time budget).

Changes: one host per launch, `judge-<tag>` (pod name `attribution-judge-<tag>[-rN]`); its records in
tmp/family-probe-judge/hosts/judge-<tag>/ (JUDGE_HOSTS). Every kit's budget.py scans tmp/family-probe-*/hosts/*/:
a create-intent.json without a pod.json counts as a pod in flight until its cap, and pod.json gives a running pod's
cap. So the kits count the judge pod at its own cap (not at the 15 h fallback), and a create in flight is counted
before RunPod answers. No plan.json; the run folder /workspace/judge; a timeout on every ssh/scp call; sizes for the
judge (container disk 50 GB for the 14.5 GB snapshot under /root/.cache, volume 10 GB for the timer state and the run
folder); errors raise HostError (never SystemExit) so the caller's finally always runs; and the budget guard: the
budget kit's budget.py `check HOURS PRICE` (run as a child, as launch.py does; a child that runs past 300 s or
cannot start is a refusal) under the lock every family-probe kit shares (tmp/family-probe-budget.lock, the file
budget.lock() opens), held by the caller from reconcile through create.
The default budget kit is tmp/family-probe-olmo2-1b-bt (RESERVE_USD 1.0, the user's 8 Oct reserve); the SSH key stays
the tmp/family-probe-olmo2-1b-g kit's. budget.py check appends one line to the budget kit's budget-checks.jsonl (its own
record); nothing else is written in a kit.

The RunPod key comes from RUNPOD_OPERATOR_API_KEY (the lead sources the secrets file before the launch) and goes only
into the Authorization header. Every child process gets this environment without any HF token variable. Records hold
no secret: create-intent.json names the env variables only, never their values.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
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

ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
KIT = ROOT / "tmp/family-probe-olmo2-1b-g"                 # ssh/key(.pub); read-only
BUDGET_KIT = ROOT / "tmp/family-probe-olmo2-1b-bt"         # budget.py with RESERVE_USD 1.0 (the user, 8 Oct); its check
#                                                            appends to the kit's budget-checks.jsonl
BUDGET_LOCK = ROOT / "tmp/family-probe-budget.lock"        # = budget.lock()'s file (HERE.parent / LOCK_NAME)
JUDGE_HOSTS = ROOT / "tmp/family-probe-judge/hosts"        # judge-<tag>/: the host records, where budget.py scans
TIMER_PYTHON = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
REST = "https://rest.runpod.io/v1"
GPU = "NVIDIA A100-SXM4-80GB"
IMAGE = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
PRICE_GUARD = 10.0              # the creation-time price limit, $/h (the user, 9 Oct 2026 15:29 UTC; it replaces 8 Oct's "no limit")
PLANNING_PRICE = 1.85            # $/h: the budget guard's price for a new pod and the cost upper bound (the kits' rate)
CONTAINER_DISK_GB = 50
VOLUME_GB = 10
REMOTE_ROOT = "/workspace/judge"
POD_PREFIX = "attribution-judge"
TIMER_DIR = "/workspace/.pod-timer"
STOP_TRIES, CONFIRM_TRIES = 5, 12
FETCH_TIMEOUT_S = 900                                       # one scp of an output file
ORPHAN_LISTINGS, ORPHAN_LISTING_GAP_S = 3, 20               # host.create of the kits: 3 listings, 20 s apart
SAFE = ("id", "name", "desiredStatus", "costPerHr", "machineId", "lastStartedAt", "lastStatusChange", "publicIp",
        "portMappings", "gpu", "volumeInGb", "containerDiskInGb")
TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
HF_TOKEN_RE = re.compile(r"hf_[A-Za-z0-9]{30,}")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,38}[a-z0-9]$")
SLEEP = time.sleep                                          # replaced in tests


class HostError(Exception):
    """A failed host step. The message names ids, codes and paths only."""


class StopUnconfirmed(HostError):
    """A pod may still run: an orphan stop was not confirmed, or no listing could show that none exists. pod_ids and
    names are the listed pods' (or, when no listing worked, the name a pod would have)."""

    def __init__(self, message: str, pod_ids=(), names=()):
        super().__init__(message)
        self.pod_ids = [str(p) for p in pod_ids if p]
        self.names = [str(n) for n in names if n]


class CreateLost(HostError):
    """The create reply failed without a refusal (status 0, a 2xx reply without a pod id, a 5xx reply, or any status
    but a 4xx) and no listing showed a pod of this name: RunPod may still list one later, so nothing can be concluded
    (the launcher's exit 7, CHECK-CONSOLE)."""

    def __init__(self, message: str, name: str | None = None):
        super().__init__(message)
        self.name = name


def append_line(path: pathlib.Path, record) -> bool:
    """One JSON line appended to a host record file; never raises (False when it could not be written)."""
    try:
        with open(path, "a") as handle:
            handle.write(json.dumps(record) + "\n")
        return True
    except (OSError, TypeError, ValueError):
        return False


def clean_env(environ=None) -> dict:
    """The environment without any HF token variable and without any variable whose value holds an HF token
    (secret_scan.scrubbed of the kits)."""
    environ = os.environ if environ is None else environ
    return {k: v for k, v in environ.items() if k not in TOKEN_ENV_NAMES and not HF_TOKEN_RE.search(v or "")}


def key() -> str:
    value = os.environ.get("RUNPOD_OPERATOR_API_KEY", "").strip()
    if not value:
        raise HostError("RUNPOD_OPERATOR_API_KEY is not set (the lead sources the secrets file)")
    return value


def api(method: str, path: str, payload=None):
    """(status, body) of one REST call; a timeout or a dropped link is status 0 (host.py's api, unchanged)."""
    request = urllib.request.Request(REST + path, method=method,
                                     data=None if payload is None else json.dumps(payload).encode(),
                                     headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json",
                                              "Accept": "application/json", "User-Agent": "attribution-judge-pod"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            return response.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode("utf-8", "replace")[:500]}
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return 0, {"error": type(exc).__name__}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def save(path: pathlib.Path, record) -> None:
    path.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")


def finite_price(value) -> bool:
    """A price RunPod could mean: an int or float that is not a bool, NaN or inf."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


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


class RunPodHost:
    """One judge pod. The caller holds budget_lock() from reconcile() through create()."""

    def __init__(self, tag: str, records: pathlib.Path | None = None, kit: pathlib.Path = KIT,
                 budget_kit: pathlib.Path = BUDGET_KIT, remote_root: str = REMOTE_ROOT, runner=subprocess.run):
        if not TAG_RE.match(tag):
            raise HostError(f"tag {tag!r}: 2 to 40 characters of a-z, 0-9 and '-'")
        self.tag, self.host = tag, f"judge-{tag}"
        self.records = pathlib.Path(JUDGE_HOSTS / self.host if records is None else records)
        self.records.mkdir(parents=True, exist_ok=True)
        self.kit, self.budget_kit, self.remote_root, self.runner = pathlib.Path(kit), pathlib.Path(budget_kit), remote_root, runner
        self.pod_id: str | None = None
        self.cap_stop_utc: str | None = None
        self.orphan_check_done = False          # set when a listing after a failed create reply has concluded
        self.create_sent = False                # set just before the create request goes out (none can exist before)
        self.records_dropped = 0                # appends to stops.jsonl or orphans.jsonl that could not be written
        self._address = None

    # ------------------------------------------------------------ names and records

    def name(self) -> str:
        suffix_file = self.records / "attempt.txt"
        suffix = suffix_file.read_text().strip() if suffix_file.exists() else ""
        return f"{POD_PREFIX}-{self.tag}{suffix}"

    def named_pods(self) -> list[dict]:
        status, pods = api("GET", "/pods")
        if status != 200 or not isinstance(pods, list):
            raise HostError(f"cannot list pods ({status})")
        return [p for p in pods if isinstance(p, dict) and p.get("name") == self.name() and p.get("id")]

    def orphan(self, pods: list[dict], why: str) -> None:
        """Stops each pod and records it in orphans.jsonl (an append that never raises). When a stop was not confirmed
        (desiredStatus EXITED), raises StopUnconfirmed with the listed pods' ids and names before the name suffix moves,
        so every later listing and warning still names the real pod. Only when all were confirmed does this host move
        to a new name suffix."""
        unconfirmed = []
        for pod in pods:
            result = stop_id(pod["id"])
            if not result.get("confirmed"):
                unconfirmed.append(pod)
            entry = {"utc": now(), "id": pod.get("id"), "name": pod.get("name"), "why": why, "stop": result}
            if not append_line(self.records / "orphans.jsonl", entry):
                self.records_dropped += 1
        if unconfirmed:
            ids = [p.get("id") for p in unconfirmed]
            names = [p.get("name") for p in unconfirmed]
            raise StopUnconfirmed(f"{self.host}: the stop of pod(s) {ids} named {sorted(set(map(str, names)))} was not "
                                  f"confirmed ({why})", ids, names)
        suffix_file = self.records / "attempt.txt"
        try:
            previous = suffix_file.read_text().strip() if suffix_file.exists() else ""
            number = int(previous[2:]) + 1 if previous.startswith("-r") else 2
            suffix_file.write_text(f"-r{number}\n")
        except OSError:                                 # a full disk: the stops are confirmed; the name does not move
            self.records_dropped += 1

    def stop_orphans(self, why: str) -> int:
        """After a create that returned no tracked pod (a failed reply, or an interrupt during the call): the pods of
        this name are listed up to ORPHAN_LISTINGS times, ORPHAN_LISTING_GAP_S apart (each listing after the wait, as
        the kits' host.create does), and every one that is not EXITED is stopped and recorded (orphan). Returns how many
        were stopped (0: no listing showed one). Raises StopUnconfirmed when a stop was not confirmed (orphan), or when
        a listing failed and none showed a pod (a pod may exist; the error names the name it would have)."""
        failed = 0
        for _ in range(ORPHAN_LISTINGS):
            SLEEP(ORPHAN_LISTING_GAP_S)
            try:
                found = [p for p in self.named_pods() if p.get("desiredStatus") != "EXITED"]
            except HostError:
                failed += 1
                continue
            if found:
                self.orphan(found, why)                 # StopUnconfirmed (with ids and names) when not confirmed
                self.orphan_check_done = True
                return len(found)
        if failed:
            raise StopUnconfirmed(f"{self.host}: the pod listing failed {failed} of {ORPHAN_LISTINGS} times, so a pod "
                                  f"named {self.name()} may exist", (), [self.name()])
        self.orphan_check_done = True
        return 0

    # ------------------------------------------------------------ budget guard, reconcile, create

    @contextlib.contextmanager
    def budget_lock(self, path: pathlib.Path | None = None):
        """budget.lock() of the kits: one exclusive lock beside the kits, blocking until it is free."""
        with open(BUDGET_LOCK if path is None else path, "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def reconcile(self) -> None:
        if (self.records / "pod.json").exists():
            raise HostError(f"{self.host}: a pod was already created for this tag (pod.json); use a new tag")
        found = self.named_pods()
        if found:
            self.orphan(found, "a pod with this host's name exists without pod.json")     # StopUnconfirmed if not
            raise HostError(f"{self.host}: a pod of this name existed without pod.json: stopped (orphans.jsonl)")
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for name in ("create-intent.json", "create-result.json", "timer-settings.json"):
            if (self.records / name).exists():
                (self.records / name).rename(self.records / f"{name[:-5]}-failed-{stamp}.json")

    def budget_check(self, hours: float, price: float) -> tuple[bool, dict]:
        """The budget kit's budget.py check HOURS PRICE (exit 0: allowed; 3: refused). Returns (allowed, its summary).
        A child that runs past 300 s (TimeoutExpired), cannot start (OSError) or prints undecodable bytes (ValueError)
        is a refusal: (False, {"exit": None, "error": <its type>})."""
        argv = [sys.executable, str(self.budget_kit / "budget.py"), "check", f"{hours:.4f}", f"{price}"]
        try:
            done = self.runner(argv, cwd=self.budget_kit, capture_output=True, text=True, env=clean_env(), timeout=300)
        except (subprocess.TimeoutExpired, OSError, ValueError) as e:
            return False, {"exit": None, "error": type(e).__name__}
        summary = {}
        lines = (done.stdout or "").strip().splitlines()
        if lines:
            try:
                parsed = json.loads(lines[-1])
                summary = {k: parsed.get(k) for k in ("balance", "committed_upper_usd", "new_pod_upper_usd",
                                                       "reserve_usd", "allowed") if isinstance(parsed, dict)}
            except ValueError:
                summary = {}
        summary["exit"] = done.returncode
        return done.returncode == 0 and summary.get("allowed") is True, summary

    def timer_settings(self, cap_hours: float) -> dict:
        path = self.records / "timer-settings.json"
        self.runner([str(TIMER_PYTHON), "-m", "experiments.durability", "pod-timer-settings", "--state-dir", TIMER_DIR,
                     "--cap-minutes", str(int(cap_hours * 60)), "--out", str(path)], cwd=ROOT, check=True,
                    env={**clean_env(), "PYTHONDONTWRITEBYTECODE": "1"}, stdout=subprocess.DEVNULL, timeout=120)
        return json.loads(path.read_text())

    def create(self, cap_hours: float) -> dict:
        """One pod with the in-pod stop timer at cap_hours. create-intent.json (with the cap) is written before the
        request, pod.json (id and cap) as soon as RunPod answers: budget.py counts the first until the second exists.
        A price that is not a finite number, or above PRICE_GUARD ($10/h since 9 Oct 2026), stops the pod at once.
        A failed reply: the pods of this name are listed (stop_orphans). A pod found there is stopped (HostError); none
        found after a 4xx reply raises HostError (RunPod refused the create); none found after any other failed reply
        (status 0, a 2xx reply without a pod id, a 5xx reply) raises CreateLost."""
        settings = self.timer_settings(cap_hours)
        self.cap_stop_utc = settings["cap_stop_utc"]          # the timer cap of any pod this create makes
        env = {**settings["env"], "PUBLIC_KEY": (self.kit / "ssh/key.pub").read_text().strip(),
               "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "TOKENIZERS_PARALLELISM": "false"}
        request = {"name": self.name(), "imageName": IMAGE, "gpuTypeIds": [GPU], "gpuCount": 1, "cloudType": "SECURE",
                   "interruptible": False, "containerDiskInGb": CONTAINER_DISK_GB, "volumeInGb": VOLUME_GB,
                   "volumeMountPath": "/workspace", "ports": ["22/tcp"], "supportPublicIp": True, "env": env,
                   "dockerStartCmd": settings["docker_start_cmd"]}
        save(self.records / "create-intent.json", {"utc": now(), "cap_stop_utc": settings["cap_stop_utc"],
                                                   "cap_hours": cap_hours, "planning_price": PLANNING_PRICE,
                                                   "request_without_env": {k: v for k, v in request.items() if k != "env"},
                                                   "env_names": sorted(env)})
        self.create_sent = True
        status, pod = api("POST", "/pods", request)
        save(self.records / "create-result.json", {"utc": now(), "status": status,
                                                   "pod": {k: pod.get(k) for k in SAFE} if status in (200, 201)
                                                   and isinstance(pod, dict) else pod})
        if status not in (200, 201) or not isinstance(pod, dict) or not pod.get("id"):
            found = self.stop_orphans(f"created although the create reply failed ({status})")   # StopUnconfirmed
            if found:
                raise HostError(f"the create reply failed ({status}) but the pod existed: stopped (orphans.jsonl)")
            if isinstance(status, int) and 400 <= status <= 499:      # RunPod refused the request: no pod was made
                raise HostError(f"pod creation failed ({status}); see create-result.json")
            raise CreateLost(f"the create reply was lost or failed ({status}) and no listing in {ORPHAN_LISTINGS} "
                             f"showed a pod named {self.name()}; RunPod may still list one", self.name())
        self.pod_id = pod["id"]
        record = {**{k: pod.get(k) for k in SAFE}, "host": self.host, "created_utc": now(),
                  "cap_stop_utc": settings["cap_stop_utc"]}
        save(self.records / "pod.json", record)
        price = pod.get("costPerHr")
        if not finite_price(price) or price > PRICE_GUARD:
            result = stop_id(self.pod_id)
            save(self.records / "price-guard-stop.json", {"utc": now(), "costPerHr": str(price), "stop": result})
            if result["confirmed"]:
                self.pod_id = None                 # stopped and confirmed: the caller has nothing left to stop
                self.orphan_check_done = True      # the created pod is known (pod.json) and stopped: no listing needed
            raise HostError(f"price {price!r}/h is not a finite number at or below {PRICE_GUARD}; stop confirmed: "
                            f"{result['confirmed']}")
        return record

    # ------------------------------------------------------------ connection

    def get(self) -> dict:
        if not self.pod_id:
            raise HostError("no pod")
        status, pod = api("GET", f"/pods/{self.pod_id}")
        if status != 200 or not isinstance(pod, dict):
            raise HostError(f"pod read failed ({status})")
        latest = {**{k: pod.get(k) for k in SAFE}, "utc": now()}
        save(self.records / "pod-latest.json", latest)
        return latest

    def ssh_base(self) -> list[str]:
        if self._address is None:
            latest = self.get()
            ip, ports = latest.get("publicIp"), latest.get("portMappings") or {}
            port = ports.get("22") if isinstance(ports, dict) else None
            if not ip or not port:
                raise HostError("no SSH address yet (the pod may still be starting)")
            self._address = (str(ip), int(port))
        ip, port = self._address
        return ["-F", "/dev/null", "-i", str(self.kit / "ssh/key"), "-o", "IdentitiesOnly=yes",
                "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={self.records / 'known_hosts'}",
                "-o", "BatchMode=yes", "-o", "ForwardAgent=no", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15",
                "-o", "ServerAliveCountMax=4", "-p", str(port), f"root@{ip}"]

    def run(self, command: str, timeout: float = 120, stdin_path: pathlib.Path | None = None) -> tuple[int, str]:
        """(exit code, stdout) of one ssh command; a timeout is exit 124. stderr is dropped (never logged)."""
        base = self.ssh_base()
        try:
            if stdin_path is not None:
                with open(stdin_path, "rb") as fh:
                    done = self.runner(["ssh", *base, command], stdin=fh, capture_output=True, timeout=timeout,
                                       env=clean_env())
                return done.returncode, (done.stdout or b"").decode("utf-8", "replace")
            done = self.runner(["ssh", *base, command], capture_output=True, text=True, timeout=timeout,
                               env=clean_env(), stdin=subprocess.DEVNULL)
            return done.returncode, done.stdout or ""
        except subprocess.TimeoutExpired:
            return 124, ""

    def wait_ssh(self, seconds: float = 1200) -> None:
        deadline = time.time() + seconds
        while True:
            try:
                self._address = None
                if self.run("true", timeout=60)[0] == 0:
                    return
            except HostError:
                pass
            if time.time() >= deadline:
                raise HostError(f"no SSH within {int(seconds)} s")
            SLEEP(15)

    def check(self) -> dict:
        """orchestrate.check: the GPU's name, and the stop timer armed, supervised and governed by the cap."""
        code, stdout = self.run(f"nvidia-smi --query-gpu=name --format=csv,noheader; cat {TIMER_DIR}/heartbeat.json",
                                timeout=60)
        lines = stdout.splitlines()
        if code or not lines or lines[0].strip() != GPU:
            raise HostError(f"the GPU is not {GPU} (exit {code})")
        try:
            beat = json.loads("\n".join(lines[1:]))
        except ValueError:
            raise HostError("the stop timer's heartbeat is not readable") from None
        if not (beat.get("state") == "armed" and beat.get("supervised") is True
                and (beat.get("governing") or {}).get("source") == "cap" and all((beat.get("can_stop") or {}).values())):
            raise HostError("the stop timer is not armed and supervised with its cap")
        return {"gpu": lines[0].strip(), "timer_stop_utc": beat["governing"].get("stop_at_utc")}

    def _remote(self, rel: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", rel) or ".." in rel or rel.startswith("/"):
            raise HostError("remote path must be a plain relative path under the run folder")
        return f"{self.remote_root}/{rel}"

    def send(self, local: pathlib.Path, rel: str, sha256: str) -> None:
        path = pathlib.Path(local).resolve()
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
            raise HostError("the local file does not have the given SHA-256")
        remote = self._remote(rel)
        base = self.ssh_base()
        opts, port, target = _scp_opts(base)
        if self.run(f"mkdir -p {self.remote_root} $(dirname {remote})", timeout=60)[0]:
            raise HostError(f"mkdir for {rel} failed")
        try:
            done = self.runner(["scp", *opts, "-P", port, str(path), f"{target}:{remote}"], capture_output=True,
                               timeout=900, env=clean_env())
        except subprocess.TimeoutExpired:
            raise HostError(f"scp of {rel} timed out") from None
        if done.returncode:
            raise HostError(f"scp of {rel} failed (exit {done.returncode})")
        if self.run(f"test \"$(sha256sum {remote} | cut -c1-64)\" = {sha256}", timeout=120)[0]:
            raise HostError(f"{rel}: the SHA-256 on the pod differs")

    def fetch(self, rel: str, local: pathlib.Path, timeout: float = FETCH_TIMEOUT_S) -> None:
        """scp of one file to `local` (the launcher passes a .part path and checks the SHA-256 before renaming). The
        salvage passes a shorter timeout when its time budget has less left."""
        remote = self._remote(rel)
        base = self.ssh_base()
        opts, port, target = _scp_opts(base)
        pathlib.Path(local).parent.mkdir(parents=True, exist_ok=True)
        try:
            done = self.runner(["scp", *opts, "-P", port, f"{target}:{remote}", str(local)], capture_output=True,
                               timeout=timeout, env=clean_env())
        except subprocess.TimeoutExpired:
            raise HostError(f"scp of {rel} timed out") from None
        if done.returncode:
            raise HostError(f"fetch of {rel} failed (exit {done.returncode})")

    # ------------------------------------------------------------ stop

    def stop(self) -> dict:
        """stop_id() of the tracked pod; its result is returned unchanged. The append to stops.jsonl never raises."""
        if not self.pod_id:
            return {"utc": now(), "confirmed": True, "note": "no pod to stop"}
        result = stop_id(self.pod_id)
        if not append_line(self.records / "stops.jsonl", result):
            self.records_dropped += 1
        return result

    def shorten_timer(self, seconds: int, script: pathlib.Path) -> bool:
        """The second stop path (orchestrate's extend-cap 120): move the in-pod stop to SECONDS from now with the kit's
        extend_cap.py, sent over ssh's stdin. True when the timer acknowledged it."""
        code, stdout = self.run(f"python3 - {int(seconds)}", timeout=90, stdin_path=script)
        try:
            line = json.loads(stdout.strip().splitlines()[-1]) if code == 0 and stdout.strip() else {}
        except ValueError:
            line = {}
        return bool(line.get("governs") and line.get("acknowledged"))


def _scp_opts(base: list[str]) -> tuple[list[str], str, str]:
    port, target = base[base.index("-p") + 1], base[-1]
    return [a for a in base[:-1] if a not in ("-p", port)], port, target
