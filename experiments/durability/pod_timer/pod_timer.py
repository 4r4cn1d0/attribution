#!/usr/bin/env python3
"""In-pod stop timer (self-contained; Python standard library only; Python 3.8 or later).

This file runs inside the GPU pod, started by the pod's start command before anything else (the
package README gives the command). It imports nothing from the research project. Its one job:
**stop this pod at its deadline**, whatever has happened to the worker, the laptop or GitHub.

    pod_timer.py supervise -- /start.sh    the start command's process: keeps a timer running
                                           (restarts it if it dies) and starts the image's own
                                           start script, so SSH and Jupyter work as usual
    pod_timer.py run                       the timer itself (started by the supervisor)
    pod_timer.py status                    print the timer's last heartbeat

**Where the deadline comes from.** Two kinds of authority, each with the time it was issued:

- the *cap*, fixed by the operator when the pod is created or started, in the pod's environment
  (``POD_TIMER_CAP_ISSUED_UTC``, ``POD_TIMER_CAP_STOP_UTC``); and
- *lease records* that admission writes on the persistent mount (``<state>/leases/<id>.json``),
  each naming this pod and a stop time.

The most recently issued valid authority governs. A lease withdrawn by a ``voids/<id>.json`` file
never governs. A record that is malformed, truncated, too large, for another pod, dated in the
future or asking for a stop more than 48 hours after its issue is ignored, and whatever governed
before keeps governing. (The cap may be issued up to ten minutes ahead of the pod's clock, since
it comes from the operator's machine; until that moment it outranks any lease.) With no valid authority at all the pod is stopped at once: a pod is
never left running without a deadline. A deadline already past when the timer starts also means
stop at once; to use a stopped pod again the operator starts it with a new cap.

**Acknowledgement.** When a lease starts to govern, the timer writes ``acks/<id>.json``, create-
only, and from then on its heartbeat (``heartbeat.json``, rewritten every poll) names that lease
and its stop time. Admission grants a lease only after reading both.

**At the deadline** the pod is asked to stop, by each of these in turn until one takes effect:
``runpodctl pod stop <id>``, ``runpodctl stop pod <id>`` (the older spelling), ``POST
/v1/pods/<id>/stop`` and the GraphQL ``podStop`` mutation, the last two with the pod-scoped key
RunPod puts in ``RUNPOD_API_KEY``. A stop that takes effect ends this process, which is the
confirmation from inside; where the API lets this key read the pod, ``desiredStatus`` is read as
well. Until then the attempts repeat, and each is recorded. Nothing here terminates, deletes,
resets or restarts a pod, or changes anything else.

**Two threads.** The deadline is held in memory and enforced by the main thread, which never
touches the mount. Reading records and writing acknowledgements, heartbeats and attempt records
is a second thread's work. A network volume that stops answering therefore silences the
heartbeat (admission then refuses new leases) but cannot keep the pod from being stopped.

**Secrets.** The key is read from the environment, sent only in an ``Authorization`` header to
RunPod's API, and scrubbed from anything recorded or printed.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

VERSION = 1
LEASE_KIND = "durability pod-timer lease v1"
ACK_KIND = "durability pod-timer acknowledgement v1"
BEAT_KIND = "durability pod-timer heartbeat v1"
LEASE_ID = re.compile(r"(\d{8}T\d{6}Z)-[0-9a-f]{16}")
STOPPED = ("EXITED", "TERMINATED")
MAX_HORIZON_SECONDS = 48 * 3600
MAX_RECORD_BYTES = 4096
SKEW_SECONDS = 5.0               # a lease is written by this pod's own clock
CAP_SKEW_SECONDS = 600.0         # the cap is issued by the operator's clock, which may run ahead of the pod's
SETTLE_SECONDS = 10.0            # an unreadable record younger than this may still be being written
MAX_ATTEMPT_RECORDS = 500
STOP_QUERY = 'mutation { podStop(input: {podId: "%s"}) { id desiredStatus } }'


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds")


def parse_utc(text: object) -> dt.datetime:
    if not isinstance(text, str):
        raise ValueError("not a timestamp")
    moment = dt.datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise ValueError("timestamp without a timezone")
    return moment.astimezone(dt.timezone.utc)


def _dump(record: dict) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")


def publish(path: str, record: dict) -> bool:
    """Write a record under a new name, never replacing one. True: created."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.%s.tmp" % (path, os.getpid(), os.urandom(4).hex())
    with open(tmp, "wb") as handle:
        handle.write(_dump(record))
        handle.flush()
        os.fsync(handle.fileno())
    try:
        try:
            os.link(tmp, path)          # exclusive where the filesystem has hard links
            return True
        except FileExistsError:
            return False
        except OSError:                 # a mount without hard links
            if os.path.exists(path):
                return False
            os.rename(tmp, path)
            return True
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def replace(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "wb") as handle:
        handle.write(_dump(record))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def valid_lease(record: object, lease_id: str, pod: str, now: dt.datetime) -> dict:
    """The lease as an authority, or ``ValueError`` saying why it is none."""
    if not isinstance(record, dict) or record.get("kind") != LEASE_KIND or record.get("lease") != lease_id:
        raise ValueError("not this lease's record")
    if not LEASE_ID.fullmatch(lease_id):
        raise ValueError("lease id")
    if not pod or record.get("pod") != pod:
        raise ValueError("another pod")
    if not (isinstance(record.get("worker"), str) and record["worker"]):
        raise ValueError("worker")
    issued, stop_at = parse_utc(record.get("published_utc")), parse_utc(record.get("stop_at_utc"))
    if issued.strftime("%Y%m%dT%H%M%SZ") != lease_id[:16]:
        raise ValueError("the id does not carry the publication time")
    if not issued < stop_at or (stop_at - issued).total_seconds() > MAX_HORIZON_SECONDS:
        raise ValueError("the stop time is not after publication, or too far away")
    if (issued - now).total_seconds() > SKEW_SECONDS:
        raise LookupError("published in the future")        # not yet an authority
    return {"source": "lease", "id": lease_id, "issued": issued, "stop_at": stop_at}


def cap_from(env: dict, now: dt.datetime) -> dict | None:
    """The operator's cap from the environment, or None when it is absent or unusable."""
    try:
        issued, stop_at = parse_utc(env.get("POD_TIMER_CAP_ISSUED_UTC")), parse_utc(env.get("POD_TIMER_CAP_STOP_UTC"))
    except ValueError:
        return None
    if not issued < stop_at or (stop_at - issued).total_seconds() > MAX_HORIZON_SECONDS \
            or (issued - now).total_seconds() > CAP_SKEW_SECONDS:
        return None
    return {"source": "cap", "id": None, "issued": issued, "stop_at": stop_at}


class Timer:
    """See the module doc. ``clock``, ``sleep``, ``run`` (a command runner returning
    ``(exit, output)``) and ``out`` are injectable for tests."""

    def __init__(self, env: dict, clock=utc_now, sleep=time.sleep, run=None, out=print) -> None:
        self.env, self.clock, self.sleep, self.out = dict(env), clock, sleep, out
        self.run_command = run or self._run_command
        self.pod = env.get("RUNPOD_POD_ID", "").strip()
        self.state = env.get("POD_TIMER_DIR", "").strip()
        self._key = env.get("RUNPOD_API_KEY", "").strip()
        self.rest = env.get("POD_TIMER_REST_URL", "https://rest.runpod.io/v1").rstrip("/")
        self.graphql = env.get("POD_TIMER_GRAPHQL_URL", "https://api.runpod.io/graphql").rstrip("/")
        self.poll_seconds = self._number("POD_TIMER_POLL_SECONDS", 2.0, 0.05, 30.0)
        self.confirm_seconds = self._number("POD_TIMER_CONFIRM_SECONDS", 30.0, 0.0, 300.0)
        self.retry_seconds = self._number("POD_TIMER_RETRY_SECONDS", 15.0, 0.05, 300.0)
        self.load_wait = self._number("POD_TIMER_LOAD_WAIT_SECONDS", 60.0, 0.0, 600.0)
        try:
            commands = json.loads(env["POD_TIMER_STOP_COMMANDS"]) if env.get("POD_TIMER_STOP_COMMANDS") else None
        except ValueError:
            commands = None
        if not (isinstance(commands, list) and commands and all(
                isinstance(c, list) and c and all(isinstance(a, str) for a in c) for c in commands)):
            commands = [["runpodctl", "pod", "stop", "{pod}"], ["runpodctl", "stop", "pod", "{pod}"]]
        self.commands = commands
        self.started, self.instance = clock(), os.urandom(8).hex()
        self._lock = threading.Lock()
        self._loaded = threading.Event()
        self._governing: dict | None = cap_from(self.env, self.started)
        self._stopping = False
        self._pending: list[dict] = []          # attempt records waiting to be written to the mount
        self._leases: dict[str, dict] = {}      # validated leases by id
        self._rejected: set[str] = set()
        self._attempts_written, self._beats = 0, 0

    def _number(self, name: str, default: float, low: float, high: float) -> float:
        try:
            value = float(self.env.get(name) or default)
        except ValueError:
            return default
        return value if low <= value <= high else default

    def scrub(self, text: object) -> str:
        text = "".join(ch if ch.isprintable() else " " for ch in str(text))
        if self._key:
            text = text.replace(self._key, "[key]")
        return text[:300]

    def log(self, event: str, **fields: object) -> None:
        try:
            self.out(json.dumps({"event": event, "utc": iso(self.clock()), **fields}, sort_keys=True))
        except Exception:  # noqa: BLE001 - a full or closed log must not stop the timer
            pass

    # ----- the mount: records in, acknowledgements and heartbeats out (second thread) ---------

    def _path(self, *parts: str) -> str:
        return os.path.join(self.state, *parts)

    def _read_leases(self, now: dt.datetime) -> None:
        folder = self._path("leases")
        for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            lease_id = name[:-5]
            if not name.endswith(".json") or lease_id in self._leases or name in self._rejected:
                continue
            path = os.path.join(folder, name)
            try:
                if os.path.getsize(path) > MAX_RECORD_BYTES:
                    raise ValueError("too large")
                with open(path, "rb") as handle:
                    self._leases[lease_id] = valid_lease(json.loads(handle.read().decode("utf-8")), lease_id, self.pod, now)
            except LookupError:
                continue                                    # dated in the future: looked at again later
            except (ValueError, OSError) as exc:
                try:
                    settled = now.timestamp() - os.path.getmtime(path) > SETTLE_SECONDS
                except OSError:
                    settled = False
                if settled:                                 # final: ignored from now on
                    self._rejected.add(name)
                    self.log("lease-ignored", record=self.scrub(name), reason=self.scrub(exc))

    def governing(self, now: dt.datetime) -> dict | None:
        """The most recently issued valid authority: a lease that was not withdrawn, or the cap."""
        voids = self._path("voids")
        withdrawn = {name[:-5] for name in os.listdir(voids)} if os.path.isdir(voids) else set()
        candidates = [lease for lease_id, lease in self._leases.items() if lease_id not in withdrawn]
        cap = cap_from(self.env, now)
        if cap is not None:
            candidates.append(cap)
        return max(candidates, key=lambda a: (a["issued"], a["source"] == "lease", a["id"] or "")) if candidates else None

    def poll_once(self) -> None:
        """One pass over the mount: read records, settle who governs, acknowledge, write the
        attempt records and the heartbeat."""
        now = self.clock()
        if not os.path.isabs(self.state):
            raise OSError("POD_TIMER_DIR is not an absolute path")
        os.makedirs(self.state, exist_ok=True)
        self._read_leases(now)
        governing = self.governing(now)
        with self._lock:
            self._governing = governing
            pending, self._pending = self._pending, []
            stopping = self._stopping
        self._loaded.set()
        if governing is not None and governing["source"] == "lease":
            ack = self._path("acks", governing["id"] + ".json")
            if not os.path.exists(ack):
                publish(ack, {"kind": ACK_KIND, "lease": governing["id"], "pod": self.pod,
                              "stop_at_utc": iso(governing["stop_at"]), "acknowledged_utc": iso(self.clock()),
                              "pid": os.getpid(), "instance": self.instance,
                              "statement": "this timer stops this pod at stop_at_utc unless a later authority governs"})
                self.log("lease-acknowledged", lease=governing["id"], stop_at_utc=iso(governing["stop_at"]))
        for record in pending:
            if self._attempts_written < MAX_ATTEMPT_RECORDS:
                self._attempts_written += 1
                with open(self._path("stop-attempts.jsonl"), "ab") as handle:
                    handle.write((json.dumps(record, sort_keys=True) + "\n").encode("utf-8"))
        described = None if governing is None else {
            "source": governing["source"], "lease": governing["id"], "issued_utc": iso(governing["issued"]),
            "stop_at_utc": iso(governing["stop_at"])}
        if self._beats == 0:                                # one line per start of a timer: the audit of re-arming
            with open(self._path("starts.jsonl"), "ab") as handle:
                handle.write((json.dumps({"utc": iso(self.started), "pod": self.pod, "pid": os.getpid(),
                                          "instance": self.instance, "governing": described}, sort_keys=True) + "\n").encode("utf-8"))
        self._beats += 1
        replace(self._path("heartbeat.json"), {
            "kind": BEAT_KIND, "version": VERSION, "utc": iso(self.clock()), "pod": self.pod, "pid": os.getpid(),
            "instance": self.instance, "started_utc": iso(self.started), "sequence": self._beats,
            "supervised": self.env.get("POD_TIMER_SUPERVISOR", "") == str(os.getppid()),
            "state": "stopping" if stopping else "armed", "poll_seconds": self.poll_seconds,
            "governing": described,
            "can_stop": {"pod_id": bool(self.pod), "runpodctl": shutil.which(self.commands[0][0]) is not None,
                         "key": bool(self._key)}})

    def _poll_forever(self) -> None:
        while True:
            try:
                self.poll_once()
            except Exception as exc:  # noqa: BLE001 - the mount may fail in any way; the deadline in memory stands
                self.log("mount-error", reason=self.scrub("%s: %s" % (type(exc).__name__, exc)))
            time.sleep(self.poll_seconds)

    # ----- the deadline and the stop (main thread; never touches the mount) -------------------

    def deadline(self) -> dt.datetime | None:
        with self._lock:
            return None if self._governing is None else self._governing["stop_at"]

    def due(self) -> bool:
        deadline = self.deadline()
        return deadline is None or self.clock() >= deadline

    @staticmethod
    def _run_command(argv: list) -> tuple:
        try:
            done = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  timeout=90, check=False)
            return done.returncode, done.stdout.decode("utf-8", "replace")
        except (OSError, subprocess.SubprocessError) as exc:
            return None, type(exc).__name__

    def _http(self, method: str, url: str, body: bytes | None = None) -> tuple:
        """(status, body). The key goes into the Authorization header and nowhere else."""
        parts = urllib.parse.urlsplit(url)
        if not self._key or (parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname == "127.0.0.1")):
            return None, b""
        request = urllib.request.Request(url, data=body, method=method)
        request.add_header("Authorization", "Bearer " + self._key)
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", "durability-pod-timer")
        if body is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - scheme checked above
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, b""
        except (urllib.error.URLError, OSError, ValueError):
            return None, b""

    def pod_status(self) -> str:
        """``desiredStatus`` as the API reports it to this pod's key, or "unknown"."""
        status, payload = self._http("GET", "%s/pods/%s" % (self.rest, urllib.parse.quote(self.pod, safe="")))
        try:
            value = json.loads(payload).get("desiredStatus") if status == 200 else None
        except (ValueError, AttributeError):
            value = None
        return value if isinstance(value, str) else "unknown"

    def _attempts(self):
        """Each way of asking for the stop, in order: (name, callable returning (ok, detail))."""
        pod = urllib.parse.quote(self.pod, safe="")
        for argv in self.commands:
            argv = [arg.replace("{pod}", self.pod) for arg in argv]

            def command(argv=argv):
                code, output = self.run_command(argv)
                return code == 0, "exit %s: %s" % (code, output)
            yield " ".join(argv[:3]), command

        def rest():
            status, _ = self._http("POST", "%s/pods/%s/stop" % (self.rest, pod), b"")
            return status is not None and 200 <= status < 300, "status %s" % status

        def graphql():
            status, payload = self._http("POST", self.graphql, json.dumps({"query": STOP_QUERY % self.pod}).encode("utf-8"))
            try:
                answer = json.loads(payload) if status == 200 else {}
            except ValueError:
                answer = {}
            ok = isinstance(answer, dict) and not answer.get("errors") and isinstance(answer.get("data"), dict) \
                and isinstance(answer["data"].get("podStop"), dict)
            return ok, "status %s" % status
        if self._key and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.pod):
            yield "rest stop", rest
            yield "graphql podStop", graphql

    def stop_cycle(self) -> bool:
        """Ask for the stop once by every method. True when the API reports the pod as stopped.
        (A stop that takes effect ends this process before it can say so.)"""
        with self._lock:
            self._stopping = True
        for name, attempt in self._attempts():
            if not self.due():
                break                                        # a later authority arrived meanwhile
            asked = self.clock()
            try:
                ok, detail = attempt()
            except Exception as exc:  # noqa: BLE001 - one failing method must not keep the others from being tried
                ok, detail = False, type(exc).__name__
            status, waited = "unknown", 0.0
            while ok:
                status = self.pod_status()
                if status in STOPPED or waited >= self.confirm_seconds:
                    break
                self.sleep(min(2.0, self.confirm_seconds))
                waited += 2.0
            deadline = self.deadline()
            record = {"utc": iso(asked), "pod": self.pod, "method": name, "accepted": bool(ok), "detail": self.scrub(detail),
                      "status_after": status, "stop_at_utc": None if deadline is None else iso(deadline),
                      "seconds_after_stop_time": None if deadline is None else (asked - deadline).total_seconds(),
                      "pid": os.getpid(), "instance": self.instance}
            with self._lock:
                self._pending.append(record)
            self.log("stop-attempt", **record)
            if status in STOPPED:
                return True
        return False

    def enforce_once(self) -> str:
        """"armed" before the deadline; otherwise one stop cycle: "stopped" or "unconfirmed"."""
        if not self.due():
            with self._lock:
                self._stopping = False
            return "armed"
        return "stopped" if self.stop_cycle() else "unconfirmed"

    def run_forever(self) -> None:
        for name in ("SIGTERM", "SIGHUP", "SIGINT"):
            signal.signal(getattr(signal, name), signal.SIG_IGN)
        self.log("timer-started", pod=self.pod, pid=os.getpid(), instance=self.instance)
        threading.Thread(target=self._poll_forever, daemon=True).start()
        self._loaded.wait(self.load_wait)          # the mount's records, or after a bounded wait only the cap
        while True:
            state = self.enforce_once()
            if state == "armed":
                remaining = (self.deadline() - self.clock()).total_seconds() if self.deadline() else 0.0
                time.sleep(max(0.05, min(1.0, remaining)))
            else:
                time.sleep(self.retry_seconds)      # still alive: the stop did not take effect; ask again


def supervise(command: list, env: dict, out=print) -> int:
    """Keep one timer running; start the wrapped command (the image's start script) once."""
    for name in ("SIGTERM", "SIGHUP", "SIGINT"):
        signal.signal(getattr(signal, name), signal.SIG_IGN)
    restore = lambda: [signal.signal(getattr(signal, n), signal.SIG_DFL) for n in ("SIGTERM", "SIGHUP", "SIGINT")]  # noqa: E731
    wrapped, failures = None, 0
    if command:
        try:
            wrapped = subprocess.Popen(command, preexec_fn=restore)  # noqa: PLW1509 - the start script gets default signals
        except OSError as exc:
            out(json.dumps({"event": "start-command-failed", "reason": type(exc).__name__}))
    child_env = dict(env, POD_TIMER_SUPERVISOR=str(os.getpid()))
    while True:
        try:
            child = subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "run"], env=child_env)
            failures = 0
        except OSError as exc:
            failures += 1
            out(json.dumps({"event": "timer-not-started", "reason": type(exc).__name__, "failures": failures}))
            if failures >= 20:
                return 1                            # the start command then stops the pod itself
            time.sleep(1.0)
            continue
        while child.poll() is None:
            if wrapped is not None and wrapped.poll() is not None:
                out(json.dumps({"event": "start-command-exited", "exit": wrapped.returncode}))
                wrapped = None
            time.sleep(0.5)
        out(json.dumps({"event": "timer-exited", "exit": child.returncode, "utc": iso(utc_now())}))
        time.sleep(1.0)


def main(argv: list | None = None, env: dict | None = None) -> int:
    argv, env = list(sys.argv[1:] if argv is None else argv), dict(os.environ if env is None else env)
    mode = argv[0] if argv else "run"
    if mode == "supervise":
        return supervise(argv[2:] if argv[1:2] == ["--"] else argv[1:], env)
    if mode == "status":
        try:
            with open(os.path.join(env.get("POD_TIMER_DIR", ""), "heartbeat.json"), "rb") as handle:
                print(handle.read().decode("utf-8"))
            return 0
        except OSError:
            print(json.dumps({"event": "no-heartbeat"}))
            return 1
    if mode != "run":
        print(json.dumps({"event": "usage", "modes": ["supervise", "run", "status"]}))
        return 2
    Timer(env).run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
