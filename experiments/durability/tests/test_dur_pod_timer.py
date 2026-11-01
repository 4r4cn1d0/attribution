"""The in-pod stop timer (ENGINEERING FIXTURES; no request leaves the machine, and no real pod,
key or RunPod command is involved).

Three kinds of test:

- the timer's logic with a manual clock: the deployed script
  (``experiments/durability/pod_timer/pod_timer.py``) loaded from its file, a temporary folder as
  the persistent mount, a fake stop command and a fake RunPod API on 127.0.0.1;
- the timer as real, separate processes: started by its supervisor, killed and restarted, the
  "container" killed and started again, and the pod's start command run by bash;
- admission through the worker's side: refused without the timer's acknowledgement, granted when
  the timer acknowledges while the GitHub watchdog refuses or cannot be reached.

Nothing here shows that RunPod honours a stop asked for from inside a pod, how long it takes, what
the key RunPod puts in a pod may do, or how RunPod restarts a container: those wait for the funded
validation (README)."""

from __future__ import annotations

import base64
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

import dur_fixtures as dur
from fake_github import TOKEN, WORKFLOW_TOKEN, FakeGitHub
from fake_runpod import KEY, FakeRunPod, network_volume, pod
from test_dur_watchdog import Actions, names, record_of

from experiments.durability import shutdown_timer as worker_side
from experiments.durability.__main__ import main as cli
from experiments.durability.admission import AdmissionController, AdmissionPolicy
from experiments.durability.common import AdmissionRefused, DurabilityError, Journal, NotConfigured, ProviderError, iso
from experiments.durability.destination import LocalDirectoryDestination
from experiments.durability.github_destination import GITHUB_TOKEN_ENV
from experiments.durability.runpod_provider import BalanceConfirmation, RunPodConfig, RunPodProvider, StoragePrices
from experiments.durability.shutdown_timer import LayeredShutdown, PodTimer, StopConfirmation, settings
from experiments.durability.shutdown_watchdog import GitHubActionsWatchdog
from experiments.durability.wiring import provider_from, shutdown_from

SCRIPT = Path(__file__).resolve().parents[1] / "pod_timer" / "pod_timer.py"
REPOSITORY = "owner/backups"
CONFIRMED = StopConfirmation("test operator", "2026-10-04T09:00:00+00:00",
                             "ENGINEERING FIXTURE: a cap-only pod was seen to stop itself")


def load_script():
    spec = importlib.util.spec_from_file_location("deployed_pod_timer", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Pod:
    """One pod as the timer sees it: a mount, an environment, a clock the test moves, a stop
    command that the test scripts, and RunPod's API as a fake on 127.0.0.1."""

    def __init__(self, folder: Path) -> None:
        self.script = load_script()
        # Hermetic stop routes (GI IV, 9 Oct 2026): the timer finds runpodctl through shutil.which on the PATH. The fake pod
        # has no runpodctl unless a test sets has_runpodctl, whatever the host machine has installed (runpodctl appeared on
        # this Mac's PATH on 9 Oct and made the "cannot ask for a stop" refusal case pass the check it should fail).
        self.has_runpodctl = False
        real_which = shutil.which
        fake_shutil = type("FakeShutil", (), {})()
        for name in dir(shutil):
            if not name.startswith("__"):
                setattr(fake_shutil, name, getattr(shutil, name))
        fake_shutil.which = lambda cmd, *a, **k: (real_which("sh") if self.has_runpodctl else None) if cmd == "runpodctl" else real_which(cmd, *a, **k)
        self.script.shutil = fake_shutil
        self.mount = folder / "workspace"
        self.state = self.mount / ".pod-timer"
        self.mount.mkdir(parents=True)
        self.clock = dur.ManualClock(now_utc().replace(microsecond=0))
        self.t0 = self.clock.now
        self.runpod = FakeRunPod()
        self.runpod.pods = [pod("pod-1", volume=network_volume("vol-1"), mount=str(self.mount)), pod("pod-2", cost=0.4)]
        self.runpod.volumes = [network_volume("vol-1")]
        self.calls: list[list] = []
        self.lines: list[str] = []
        self.command = "works"                           # what the stop command does: works, ignored, fails
        self.env = {"RUNPOD_POD_ID": "pod-1", "POD_TIMER_DIR": str(self.state), "RUNPOD_API_KEY": KEY,
                    "POD_TIMER_REST_URL": f"{self.runpod.url}/v1", "POD_TIMER_GRAPHQL_URL": f"{self.runpod.url}/graphql",
                    "POD_TIMER_SUPERVISOR": str(os.getppid()), "POD_TIMER_CONFIRM_SECONDS": "4"}
        self.cap(3600)

    def at(self, seconds: float) -> None:
        self.clock.now = self.t0 + dt.timedelta(seconds=seconds)

    def after(self, seconds: float) -> dt.datetime:
        return self.t0 + dt.timedelta(seconds=seconds)

    def cap(self, seconds: float | None, issued: float = 0.0) -> None:
        """The operator's cap: issued ``issued`` seconds after t0, stopping ``seconds`` after t0."""
        for name in ("POD_TIMER_CAP_ISSUED_UTC", "POD_TIMER_CAP_STOP_UTC"):
            self.env.pop(name, None)
        if seconds is not None:
            self.env.update(POD_TIMER_CAP_ISSUED_UTC=iso(self.after(issued)), POD_TIMER_CAP_STOP_UTC=iso(self.after(seconds)))

    def run(self, argv: list) -> tuple:
        self.calls.append(list(argv))
        if self.command == "fails":
            return 1, f"Error: unauthorized for key {KEY}\x1b[0m"
        if self.command == "works":
            self.runpod.pods[0]["desiredStatus"] = "EXITED"
        return 0, "pod stop requested"

    def timer(self):
        return self.script.Timer(self.env, clock=self.clock, sleep=self.clock.advance, run=self.run, out=self.lines.append)

    def lease(self, stop_seconds: float, *, name: str | None = None, **changes) -> str:
        """A lease record as admission writes it, published at the clock's time."""
        now = self.clock.now
        lease = f"{now:%Y%m%dT%H%M%SZ}-{os.urandom(8).hex()}"
        record = {"kind": worker_side.LEASE_KIND, "lease": lease, "worker": "worker-1", "pod": "pod-1",
                  "stop_at_utc": iso(self.after(stop_seconds)), "reserved_until_utc": iso(self.after(stop_seconds + 120)),
                  "published_utc": iso(now), **changes}
        path = self.state / "leases" / f"{name or lease}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record))
        return lease

    def beat(self) -> dict:
        return json.loads((self.state / "heartbeat.json").read_text())

    def attempts(self) -> list[dict]:
        path = self.state / "stop-attempts.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def events(self, name: str) -> list[dict]:
        return [row for row in map(json.loads, self.lines) if row["event"] == name]

    def status(self) -> str:
        return self.runpod.pods[0]["desiredStatus"]

    def stop_requests(self) -> list:
        return self.calls + [(m, p) for m, p, body in self.runpod.log if m == "POST" and (p.endswith("/stop") or "podStop" in body)]


@pytest.fixture
def box(tmp_path):
    built = Pod(tmp_path)
    yield built
    assert built.runpod.leaks == []
    assert all(method in ("GET", "POST") for method, _, _ in built.runpod.log)             # nothing is ever deleted
    assert all("terminate" not in body.lower() and "/pods/pod-2" not in path for _, path, body in built.runpod.log)
    built.runpod.close()


# ----- the deadline: at it, never before, whatever its source ------------------------------------


def test_the_cap_stops_the_pod_at_its_time_and_never_before(box):
    timer = box.timer()
    timer.poll_once()
    assert box.beat()["governing"] == {"source": "cap", "lease": None, "issued_utc": iso(box.t0),
                                       "stop_at_utc": iso(box.after(3600))}
    for seconds in (0, 1800, 3599, 3599.9):
        box.at(seconds)
        assert timer.enforce_once() == "armed"
    assert box.stop_requests() == [] and box.status() == "RUNNING"
    box.at(3600)
    assert timer.enforce_once() == "stopped"
    assert box.calls == [["runpodctl", "pod", "stop", "pod-1"]] and box.status() == "EXITED"
    timer.poll_once()
    (attempt,) = box.attempts()
    assert (attempt["method"], attempt["accepted"], attempt["status_after"]) == ("runpodctl pod stop", True, "EXITED")
    assert attempt["seconds_after_stop_time"] == 0.0 and attempt["stop_at_utc"] == iso(box.after(3600))
    assert box.beat()["state"] == "stopping"


def test_a_lease_governs_once_recorded_and_a_renewal_moves_the_stop_time(box):
    timer = box.timer()
    timer.poll_once()
    box.at(600)
    first = box.lease(7200)
    timer.poll_once()
    assert box.beat()["governing"]["lease"] == first and box.beat()["governing"]["stop_at_utc"] == iso(box.after(7200))
    ack = json.loads((box.state / "acks" / f"{first}.json").read_text())
    assert (ack["lease"], ack["pod"], ack["stop_at_utc"]) == (first, "pod-1", iso(box.after(7200)))
    box.at(3601)                                         # past the cap: the lease governs, nothing happens
    assert timer.enforce_once() == "armed"
    box.at(7000)
    second = box.lease(14400)                            # a renewal
    timer.poll_once()
    assert box.beat()["governing"]["lease"] == second and sorted(os.listdir(box.state / "acks")) == sorted(
        [f"{first}.json", f"{second}.json"])
    box.at(7201)                                         # past the first lease's stop time
    assert timer.enforce_once() == "armed" and box.stop_requests() == []
    box.at(14399)
    assert timer.enforce_once() == "armed"
    box.at(14400)
    assert timer.enforce_once() == "stopped" and box.calls == [["runpodctl", "pod", "stop", "pod-1"]]


def test_the_most_recently_issued_authority_governs_and_a_withdrawn_lease_never_does(box):
    timer = box.timer()
    box.at(100)
    early = box.lease(5000)
    box.at(200)
    late = box.lease(4000)                               # issued later, with an earlier stop: it governs
    timer.poll_once()
    assert box.beat()["governing"]["lease"] == late
    (box.state / "voids").mkdir()
    (box.state / "voids" / f"{late}.json").write_text("{}")          # admission withdrew it: no lease stands behind it
    timer.poll_once()
    assert box.beat()["governing"]["lease"] == early
    (box.state / "voids" / f"{early}.json").write_text("{}")
    timer.poll_once()
    assert box.beat()["governing"]["source"] == "cap"                # back to the cap, never to nothing
    # the operator starts a stopped pod again with a new cap: issued after every lease, it governs
    box.at(9000)
    assert timer.enforce_once() in ("stopped", "unconfirmed")        # the old cap is long past
    box.runpod.pods[0]["desiredStatus"] = "RUNNING"
    box.calls.clear()
    third = box.lease(9500)
    box.at(9100)
    box.cap(9100 + 1800, issued=9100)
    restarted = box.timer()
    restarted.poll_once()
    assert box.beat()["governing"] == {"source": "cap", "lease": None, "issued_utc": iso(box.after(9100)),
                                       "stop_at_utc": iso(box.after(10900))}
    assert restarted.enforce_once() == "armed" and third in restarted._leases


def test_without_any_valid_authority_the_pod_is_stopped_at_once(box):
    box.cap(None)
    timer = box.timer()
    timer.poll_once()
    assert box.beat()["governing"] is None
    assert timer.enforce_once() == "stopped" and box.calls == [["runpodctl", "pod", "stop", "pod-1"]]
    for bad in ({"POD_TIMER_CAP_ISSUED_UTC": iso(box.after(10)), "POD_TIMER_CAP_STOP_UTC": iso(box.after(5))},
                {"POD_TIMER_CAP_ISSUED_UTC": iso(box.after(0)), "POD_TIMER_CAP_STOP_UTC": iso(box.after(49 * 3600))},
                {"POD_TIMER_CAP_ISSUED_UTC": iso(box.after(900)), "POD_TIMER_CAP_STOP_UTC": iso(box.after(1200))},
                {"POD_TIMER_CAP_ISSUED_UTC": "2026-10-04T10:00:00", "POD_TIMER_CAP_STOP_UTC": "2026-10-04T11:00:00"},
                {"POD_TIMER_CAP_ISSUED_UTC": "soon", "POD_TIMER_CAP_STOP_UTC": "later"},
                {"POD_TIMER_CAP_STOP_UTC": iso(box.after(900))}):
        assert box.script.cap_from(bad, box.t0) is None, bad
    # the operator's clock may run a few minutes ahead of the pod's: such a cap is still a cap
    ahead = {"POD_TIMER_CAP_ISSUED_UTC": iso(box.after(300)), "POD_TIMER_CAP_STOP_UTC": iso(box.after(3900))}
    assert box.script.cap_from(ahead, box.t0)["stop_at"] == box.after(3900)


def test_a_deadline_already_past_when_the_timer_starts_means_stop_at_once(box):
    box.at(100)
    lease = box.lease(900)
    box.at(5000)                                         # the container restarts long after the lease's stop time
    timer = box.timer()
    timer.poll_once()
    assert box.beat()["governing"]["lease"] == lease
    assert timer.enforce_once() == "stopped"
    timer.poll_once()
    assert box.attempts()[0]["seconds_after_stop_time"] == 4100.0


MALFORMED = {
    "truncated": lambda box, good: good[: len(good) // 2],
    "empty": lambda box, good: "",
    "not an object": lambda box, good: "[1, 2]",
    "another kind": lambda box, good: json.dumps({**json.loads(good), "kind": "note"}),
    "another pod": lambda box, good: json.dumps({**json.loads(good), "pod": "pod-2"}),
    "another lease's record": lambda box, good: json.dumps({**json.loads(good), "lease": "20261004T000000Z-" + "0" * 16}),
    "no worker": lambda box, good: json.dumps({**json.loads(good), "worker": ""}),
    "a stop time without a timezone": lambda box, good: json.dumps({**json.loads(good), "stop_at_utc": "2026-10-04T23:00:00"}),
    "a stop before publication": lambda box, good: json.dumps({**json.loads(good), "stop_at_utc": iso(box.after(-10))}),
    "a stop too far away": lambda box, good: json.dumps({**json.loads(good), "stop_at_utc": iso(box.after(50 * 3600))}),
    "a publication time the id does not carry": lambda box, good: json.dumps(
        {**json.loads(good), "published_utc": iso(box.after(777))}),
    "too large": lambda box, good: json.dumps({**json.loads(good), "padding": "x" * 5000}),
}


@pytest.mark.parametrize("what", sorted(MALFORMED))
def test_a_malformed_or_truncated_record_is_ignored_and_the_previous_deadline_stays(box, what):
    timer = box.timer()
    box.at(1)
    good = box.lease(1800)
    timer.poll_once()
    box.at(3)
    bad = box.lease(40000)                               # would move the stop eleven hours away
    path = box.state / "leases" / f"{bad}.json"
    path.write_text(MALFORMED[what](box, path.read_text()))
    timer.poll_once()
    assert box.beat()["governing"]["lease"] == good and not (box.state / "acks" / f"{bad}.json").exists()
    assert box.events("lease-ignored") == []             # it may still be being written: looked at again
    old = time.time() - 60
    os.utime(path, (old, old))                           # it has had time to settle: ignored for good, once
    timer.poll_once()
    timer.poll_once()
    assert [row["record"] for row in box.events("lease-ignored")] == [f"{bad}.json"]
    assert box.beat()["governing"]["lease"] == good
    box.at(1800)
    assert timer.enforce_once() == "stopped"             # the good lease's stop time held


def test_a_record_dated_in_the_future_or_misnamed_does_not_govern(box):
    timer = box.timer()
    box.at(60)
    good = box.lease(1800)
    future = dt.timedelta(seconds=600)
    box.clock.now += future
    ahead = box.lease(9000)                              # published ten minutes ahead of the pod's clock
    box.clock.now -= future
    box.lease(9000, name="notes")                        # a file that is not named by its lease
    (box.state / "leases" / "README.txt").write_text("not a record")
    timer.poll_once()
    assert box.beat()["governing"]["lease"] == good
    box.at(661)                                          # its time has come: now it is the latest authority
    timer.poll_once()
    assert box.beat()["governing"]["lease"] == ahead


def test_an_unconfirmed_stop_is_retried_by_every_method_and_recorded(box):
    timer = box.timer()
    timer.poll_once()
    box.command, box.runpod.stop_mode = "fails", "error"
    box.at(3600)
    assert timer.enforce_once() == "unconfirmed"
    assert box.calls == [["runpodctl", "pod", "stop", "pod-1"], ["runpodctl", "stop", "pod", "pod-1"]]
    timer.poll_once()
    methods = [(a["method"], a["accepted"]) for a in box.attempts()]
    assert methods == [("runpodctl pod stop", False), ("runpodctl stop pod", False), ("rest stop", False),
                       ("graphql podStop", False)]
    assert box.status() == "RUNNING" and box.beat()["state"] == "stopping"
    box.command, box.runpod.stop_mode = "ignored", "ignored"         # accepted, but the pod keeps running
    box.calls.clear()
    assert timer.enforce_once() == "unconfirmed"
    timer.poll_once()
    assert [a["accepted"] for a in box.attempts()[4:]] == [True] * 4 and box.status() == "RUNNING"
    assert all(a["status_after"] == "RUNNING" for a in box.attempts()[4:])
    box.command, box.runpod.stop_mode = "fails", "ok"                # only the API works: the third method stops the pod
    assert timer.enforce_once() == "stopped"
    timer.poll_once()
    assert (box.attempts()[-1]["method"], box.attempts()[-1]["status_after"]) == ("rest stop", "EXITED")
    posts = [(m, p) for m, p, _ in box.runpod.log if m == "POST"]
    assert set(posts) == {("POST", "/v1/pods/pod-1/stop"), ("POST", "/graphql")}


def test_a_renewal_that_arrives_while_the_stop_is_failing_returns_the_timer_to_armed(box):
    timer = box.timer()
    timer.poll_once()
    box.command, box.runpod.stop_mode = "fails", "error"
    box.at(3600)
    assert timer.enforce_once() == "unconfirmed"
    box.lease(7200)
    timer.poll_once()
    box.calls.clear()
    assert timer.enforce_once() == "armed" and box.calls == []
    timer.poll_once()
    assert box.beat()["state"] == "armed"
    # ... and one that arrives in the middle of a round of attempts ends that round
    box.at(7200)
    real_run = box.run

    def renewed_meanwhile(argv):
        answer = real_run(argv)
        box.lease(9000)
        timer.poll_once()                                # (the mount's thread, between two attempts)
        return answer

    timer.run_command = renewed_meanwhile
    assert timer.enforce_once() == "unconfirmed"
    assert box.calls == [["runpodctl", "pod", "stop", "pod-1"]]      # the other three methods were not tried
    timer.run_command = real_run
    assert timer.enforce_once() == "armed"


def test_a_mount_that_fails_cannot_keep_the_pod_from_being_stopped(box, monkeypatch):
    timer = box.timer()
    box.at(60)
    box.lease(1800)
    timer.poll_once()
    script = box.script

    def broken(*args, **kwargs):
        raise OSError("ENGINEERING FIXTURE: the network volume does not answer")

    monkeypatch.setattr(script.os, "listdir", broken)
    monkeypatch.setattr(script.os.path, "isdir", broken)
    monkeypatch.setattr(script, "replace", broken)
    monkeypatch.setattr(script, "publish", broken)
    box.at(900)
    with pytest.raises(OSError):
        timer.poll_once()                                # the mount's thread fails (it logs and tries again)
    assert timer.enforce_once() == "armed"               # the deadline in memory stands
    box.at(1800)
    assert timer.enforce_once() == "stopped" and box.calls == [["runpodctl", "pod", "stop", "pod-1"]]
    # with no mount at all from the start, the cap in the environment is the deadline
    box.runpod.pods[0]["desiredStatus"] = "RUNNING"
    blind = box.timer()
    box.at(3599)
    assert blind.enforce_once() == "armed"
    box.at(3600)
    assert blind.enforce_once() == "stopped"


def test_nothing_is_terminated_or_deleted_and_no_other_pod_is_touched(box):
    timer = box.timer()
    timer.poll_once()
    box.command = "fails"
    box.at(3600)
    timer.enforce_once()
    source = SCRIPT.read_text()
    code = source.split('"""', 2)[2]                     # everything after the module's description
    for word in ("terminate", "delete", "remove", "reset", "restart", "DELETE", "PATCH", "PUT", "podTerminate", "rmtree"):
        assert word not in code, word
    assert "os.unlink(tmp)" in code and code.count("unlink") == 1                # only its own temporary file
    assert {tuple(call[:3]) for call in box.calls} == {("runpodctl", "pod", "stop"), ("runpodctl", "stop", "pod")}
    assert {path for _, path, _ in box.runpod.log} <= {"/v1/pods/pod-1", "/v1/pods/pod-1/stop", "/graphql"}
    assert len(box.runpod.pods) == 2 and box.runpod.pods[1]["desiredStatus"] == "RUNNING"
    imports = {line.split()[1].split(".")[0] for line in source.splitlines() if line.startswith(("import ", "from "))}
    assert imports <= {"__future__", "datetime", "json", "os", "re", "shutil", "signal", "subprocess", "sys", "threading",
                       "time", "urllib"}


def test_no_secret_reaches_a_log_or_a_record(box):
    timer = box.timer()
    timer.poll_once()
    box.lease(1800)
    timer.poll_once()
    box.command, box.runpod.stop_mode = "fails", "forbidden"         # the command's own output shows the key
    box.at(1800)
    assert timer.enforce_once() == "unconfirmed"
    timer.poll_once()
    written = "".join(path.read_text() for path in box.state.rglob("*") if path.is_file())
    assert KEY not in written + "".join(box.lines) and "[key]" in written          # scrubbed, not merely absent
    assert "\x1b" not in written
    assert all(KEY not in path and KEY not in body for _, path, body in box.runpod.log)   # only ever in a header
    box.env["POD_TIMER_REST_URL"] = "http://example.invalid/v1"      # not HTTPS and not loopback: the key is not sent
    assert box.timer()._http("GET", "http://example.invalid/v1/pods/pod-1") == (None, b"")


# ----- the timer as real processes ------------------------------------------------------------


def wait_for(condition, seconds: float = 20.0, what: str = "condition"):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = condition()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError(f"timed out waiting for {what}")


class Container:
    """A stand-in for the pod's container: the supervisor (as the start command runs it) in its
    own process group, a folder as the mount, and a stop command that only writes down that it was
    called and when."""

    def __init__(self, folder: Path, cap_seconds: float = 3600.0) -> None:
        self.folder, self.mount = folder, folder / "workspace"
        self.state, self.stops = self.mount / ".pod-timer", folder / "stops.log"
        self.mount.mkdir(parents=True, exist_ok=True)
        note = ("import sys, datetime; open(sys.argv[1], 'a').write(datetime.datetime.now(datetime.timezone.utc)"
                ".isoformat() + ' ' + ' '.join(sys.argv[2:]) + chr(10))")
        issued = now_utc()
        self.env = {"PATH": os.environ["PATH"], "RUNPOD_POD_ID": "pod-1", "POD_TIMER_DIR": str(self.state),
                    "POD_TIMER_CAP_ISSUED_UTC": iso(issued), "POD_TIMER_CAP_STOP_UTC": iso(issued + dt.timedelta(seconds=cap_seconds)),
                    "POD_TIMER_POLL_SECONDS": "0.1", "POD_TIMER_CONFIRM_SECONDS": "0", "POD_TIMER_RETRY_SECONDS": "0.3",
                    "POD_TIMER_STOP_COMMANDS": json.dumps([[sys.executable, "-c", note, str(self.stops), "stop", "{pod}"]])}
        self.processes: list[subprocess.Popen] = []

    def start(self, *command: str) -> subprocess.Popen:
        process = subprocess.Popen([sys.executable, "-I", str(SCRIPT), "supervise", "--", *command], env=self.env,
                                   start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(process)
        return process

    def kill(self, process: subprocess.Popen | None = None) -> None:
        """The container dies: every process in it at once."""
        for item in ([process] if process else self.processes):
            try:
                os.killpg(item.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            item.wait(timeout=10)

    def beat(self) -> dict | None:
        try:
            return json.loads((self.state / "heartbeat.json").read_text())
        except (OSError, ValueError):
            return None

    def fresh_beat(self, differs_from: str | None = None) -> dict:
        def ready():
            beat = self.beat()
            if beat and beat["instance"] != differs_from and (now_utc() - dt.datetime.fromisoformat(beat["utc"])).total_seconds() < 1:
                return beat
            return None
        return wait_for(ready, what="a fresh heartbeat")

    def stop_times(self) -> list[dt.datetime]:
        if not self.stops.exists():
            return []
        return [dt.datetime.fromisoformat(line.split()[0]) for line in self.stops.read_text().splitlines()]

    def armer(self, **changes) -> PodTimer:
        fields = {"lateness_seconds": 1.0, "stop_confirmation": CONFIRMED, "ack_seconds": 1.0, "poll_seconds": 0.05,
                  "max_heartbeat_age_seconds": 2.0}
        return PodTimer(self.state, **{**fields, **changes})


@pytest.fixture
def container(tmp_path):
    built = Container(tmp_path)
    yield built
    built.kill()


def test_a_killed_timer_is_restarted_by_its_supervisor_and_still_stops_the_pod_on_time(container):
    container.start()
    first = container.fresh_beat()
    assert first["supervised"] is True and first["governing"]["source"] == "cap"
    until = now_utc() + dt.timedelta(seconds=5)
    armed = container.armer().arm("worker-1", "pod-1", iso(until))
    assert armed["armed"] is True and armed["stop_at_utc"] == iso(until - dt.timedelta(seconds=1))
    os.kill(first["pid"], signal.SIGTERM)                # an ordinary kill is ignored ...
    time.sleep(0.4)
    assert container.fresh_beat()["instance"] == first["instance"]
    os.kill(first["pid"], signal.SIGKILL)                # ... a hard kill is not: the supervisor starts another
    second = container.fresh_beat(differs_from=first["instance"])
    assert second["pid"] != first["pid"] and second["supervised"] is True
    assert second["governing"]["lease"] == armed["lease"] and second["governing"]["stop_at_utc"] == armed["stop_at_utc"]
    assert container.stop_times() == []                  # not before the stop time
    stop_at = dt.datetime.fromisoformat(armed["stop_at_utc"])
    stopped = wait_for(container.stop_times, what="the stop")[0]
    assert dt.timedelta(0) <= stopped - stop_at < dt.timedelta(seconds=2)
    starts = [json.loads(line) for line in (container.state / "starts.jsonl").read_text().splitlines()]
    assert [row["instance"] for row in starts] == [first["instance"], second["instance"]]
    assert "stop pod-1" in container.stops.read_text()


WORKER = """
import sys, time
sys.path.insert(0, sys.argv[1])
from experiments.durability.shutdown_timer import PodTimer, StopConfirmation
timer = PodTimer(sys.argv[2], lateness_seconds=1.0, ack_seconds=1.0, poll_seconds=0.05, max_heartbeat_age_seconds=2.0,
                 stop_confirmation=StopConfirmation("test operator", "2026-10-04T09:00:00+00:00", "ENGINEERING FIXTURE"))
print(timer.arm("worker-1", "pod-1", sys.argv[3])["stop_at_utc"], flush=True)
time.sleep(600)
"""


def test_the_death_of_the_worker_does_not_affect_the_timer(container):
    container.start()
    beat = container.fresh_beat()
    until = now_utc() + dt.timedelta(seconds=4)
    root = str(Path(__file__).resolve().parents[3])
    worker = subprocess.Popen([sys.executable, "-B", "-c", WORKER, root, str(container.state), iso(until)],
                              stdout=subprocess.PIPE, text=True, env={"PATH": os.environ["PATH"]})
    try:
        stop_at = dt.datetime.fromisoformat(worker.stdout.readline().strip())     # the worker was granted its stop time
        assert iso(stop_at) == iso(until - dt.timedelta(seconds=1))
        # the timer is not the worker's child, nor the other way round
        parent = subprocess.run(["ps", "-o", "ppid=", "-p", str(beat["pid"])], capture_output=True, text=True).stdout.strip()
        assert parent == str(container.processes[0].pid) and parent != str(worker.pid)
    finally:
        worker.kill()                                    # the worker dies hard, long before the stop time
        worker.wait(timeout=10)
    assert container.stop_times() == []
    stopped = wait_for(container.stop_times, what="the stop")[0]
    assert dt.timedelta(0) <= stopped - stop_at < dt.timedelta(seconds=2)
    assert container.fresh_beat()["instance"] == beat["instance"]


def test_a_restarted_container_re_arms_from_the_mount(container):
    first = container.start()
    before = container.fresh_beat()
    until = now_utc() + dt.timedelta(seconds=6)
    armed = container.armer().arm("worker-1", "pod-1", iso(until))
    container.kill(first)                                # the container is gone: supervisor, timer, everything
    time.sleep(0.5)
    assert container.stop_times() == []
    container.start()                                    # the pod's start command runs again, same environment
    after = container.fresh_beat(differs_from=before["instance"])
    assert after["governing"] == {"source": "lease", "lease": armed["lease"], "stop_at_utc": armed["stop_at_utc"],
                                  "issued_utc": after["governing"]["issued_utc"]}
    stop_at = dt.datetime.fromisoformat(armed["stop_at_utc"])
    stopped = wait_for(container.stop_times, what="the stop")[0]
    assert dt.timedelta(0) <= stopped - stop_at < dt.timedelta(seconds=2)
    # ... and a container that starts after the stop time asks for the stop at once, and keeps asking
    container.kill()
    count = len(container.stop_times())
    container.start()
    wait_for(lambda: len(container.stop_times()) >= count + 2, what="repeated stop requests")


def test_the_supervisor_starts_the_images_own_start_script_and_outlives_it(container):
    marker = container.folder / "start-script-ran"
    container.start(sys.executable, "-c", f"open({str(marker)!r}, 'w').write('ran')")
    container.fresh_beat()
    wait_for(marker.exists, what="the image's start script")
    time.sleep(0.5)                                      # the start script has exited; the timer is still supervised
    assert container.processes[0].poll() is None and container.fresh_beat()["supervised"] is True


START_TOOLS = ("bash", "base64", "gunzip", "sha256sum", "python3")


def start_command(folder: Path, container: Container, cap_seconds: float, **changes) -> tuple[dict, dict, Path]:
    """The start command and environment as ``settings`` makes them, with a fake ``runpodctl``
    first on the PATH that only writes down how it was called."""
    made = settings(state_dir=str(container.state), cap_seconds=cap_seconds, install_dir=str(folder / "opt"),
                    wrapped=str(folder / "start.sh"), **changes)
    tools = folder / "bin"
    tools.mkdir()
    calls = folder / "runpodctl.log"
    (tools / "runpodctl").write_text(f'#!/bin/sh\necho "$@" >> "{calls}"\n')
    (tools / "runpodctl").chmod(0o755)
    (folder / "start.sh").write_text(f'#!/bin/sh\necho started > "{folder}/started"\nsleep 600\n')
    (folder / "start.sh").chmod(0o755)
    env = {"PATH": f"{tools}{os.pathsep}{os.environ['PATH']}", "RUNPOD_POD_ID": "pod-1", "POD_TIMER_POLL_SECONDS": "0.1",
           "POD_TIMER_REST_URL": "http://127.0.0.1:9/v1",           # nothing in these tests can reach a real service
           "POD_TIMER_CONFIRM_SECONDS": "0", "POD_TIMER_RETRY_SECONDS": "0.3", **made["env"]}
    return made, env, calls


@pytest.mark.skipif(any(shutil.which(tool) is None for tool in START_TOOLS), reason=f"needs {START_TOOLS} on the PATH, as in the pod")
def test_the_start_command_unpacks_checks_and_runs_the_timer_before_the_images_start_script(container, tmp_path):
    made, env, calls = start_command(tmp_path, container, cap_seconds=4.0, chunk_chars=3000)
    assert len([name for name in made["env"] if name.startswith("POD_TIMER_B64_")]) >= 3
    process = subprocess.Popen(made["docker_start_cmd"], env=env, start_new_session=True, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    container.processes.append(process)
    beat = container.fresh_beat()
    assert beat["supervised"] is True and beat["governing"]["source"] == "cap" and beat["can_stop"]["runpodctl"] is True
    assert (tmp_path / "opt" / "pod_timer.py").read_bytes() == SCRIPT.read_bytes()
    wait_for((tmp_path / "started").exists, what="the image's start script")
    assert not calls.exists()                            # nothing is stopped before the cap
    wait_for(calls.exists, what="the stop at the cap")
    assert calls.read_text().splitlines()[0] == "pod stop pod-1"
    stop_at = dt.datetime.fromisoformat(made["cap_stop_utc"])
    assert dt.timedelta(0) <= now_utc() - stop_at < dt.timedelta(seconds=3)


@pytest.mark.skipif(any(shutil.which(tool) is None for tool in START_TOOLS), reason=f"needs {START_TOOLS} on the PATH, as in the pod")
@pytest.mark.parametrize("damage", ["a variable cut short", "a variable missing", "another script", "the supervisor killed"])
def test_the_start_command_stops_the_pod_when_the_timer_cannot_run_or_dies(container, tmp_path, damage):
    made, env, calls = start_command(tmp_path, container, cap_seconds=3600.0, chunk_chars=4000)
    if damage == "a variable cut short":
        env["POD_TIMER_B64_01"] = env["POD_TIMER_B64_01"][:100]
    if damage == "a variable missing":
        del env["POD_TIMER_B64_00"]
    if damage == "another script":
        other = base64.b64encode(gzip.compress(b"import time\nopen('ran-anyway', 'w')\ntime.sleep(600)\n")).decode()
        env = {name: value for name, value in env.items() if not name.startswith("POD_TIMER_B64_")}
        env["POD_TIMER_B64_00"] = other
    process = subprocess.Popen(made["docker_start_cmd"], env=env, start_new_session=True, cwd=tmp_path,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    container.processes.append(process)
    if damage == "the supervisor killed":
        beat = container.fresh_beat()
        assert not calls.exists()
        supervisor = subprocess.run(["ps", "-o", "ppid=", "-p", str(beat["pid"])], capture_output=True, text=True).stdout.strip()
        os.kill(int(supervisor), signal.SIGKILL)
    wait_for(calls.exists, what="the start command's own stop")
    assert calls.read_text().splitlines()[0] == "pod stop pod-1"
    assert "the stop timer is not running; stopping this pod" in process.stdout.readline()
    if damage != "the supervisor killed":
        assert container.beat() is None and not (tmp_path / "started").exists() and not (tmp_path / "ran-anyway").exists()


def test_the_settings_carry_the_script_intact_and_refuse_what_they_cannot_express(tmp_path):
    clock = dur.ManualClock()
    made = settings(state_dir="/workspace/.pod-timer", cap_seconds=2700, clock=clock)
    env = made["env"]
    assert gzip.decompress(base64.b64decode(env["POD_TIMER_B64_00"])) == SCRIPT.read_bytes()
    assert made["script_sha256"] == hashlib.sha256(SCRIPT.read_bytes()).hexdigest() and made["script_sha256"] in made["docker_start_cmd"][2]
    assert env["POD_TIMER_DIR"] == "/workspace/.pod-timer"
    assert (env["POD_TIMER_CAP_ISSUED_UTC"], env["POD_TIMER_CAP_STOP_UTC"]) == (iso(dur.T0), iso(dur.T0 + dt.timedelta(minutes=45)))
    body = made["docker_start_cmd"][2]
    assert made["docker_start_cmd"][:2] == ["bash", "-c"] and made["console_start_command"] == f"bash -c '{body}'"
    assert "'" not in body and "python3 -I" in body and "supervise -- /start.sh" in body
    fallback = body[body.index("while true"):]
    assert fallback.startswith('while true; do runpodctl pod stop "$RUNPOD_POD_ID" || runpodctl stop pod "$RUNPOD_POD_ID" '
                               '|| curl ') and fallback.endswith('/pods/$RUNPOD_POD_ID/stop"; sleep 30; done')
    assert "-X POST" in fallback and "$RUNPOD_API_KEY" in fallback and "https://rest.runpod.io/v1" in fallback
    for word in ("terminate", "delete", "remove", " rm "):
        assert word not in body
    assert settings(state_dir="/workspace/.pod-timer", cap_seconds=2700, clock=clock) == made      # deterministic
    split = settings(state_dir="/workspace/.pod-timer", cap_seconds=2700, clock=clock, chunk_chars=2500)["env"]
    pieces = [split[name] for name in sorted(split) if name.startswith("POD_TIMER_B64_")]
    assert len(pieces) > 1 and all(len(piece) <= 2500 for piece in pieces) and "".join(pieces) == env["POD_TIMER_B64_00"]
    assert made["packed_chars"] < 16000                  # small enough to paste; RunPod's own limit is not documented
    for bad in ({"cap_seconds": 0}, {"cap_seconds": 49 * 3600}, {"cap_seconds": True}, {"state_dir": "workspace"},
                {"state_dir": "/work space"}, {"state_dir": "/workspace/../etc"}, {"wrapped": "/start.sh; rm -rf /"},
                {"install_dir": "/opt/$(x)"}, {"chunk_chars": -1}, {"chunk_chars": 10}):
        with pytest.raises(DurabilityError):
            settings(**{"state_dir": "/workspace/.pod-timer", "cap_seconds": 2700, **bad})
    out = tmp_path / "settings.json"
    assert cli(["pod-timer-settings", "--state-dir", "/workspace/.pod-timer", "--cap-minutes", "45", "--out", str(out)]) == 0
    assert sorted(json.loads(out.read_text())) == sorted(made)


def test_the_two_sides_agree_on_the_record_format(box):
    script = box.script
    for name in ("LEASE_KIND", "ACK_KIND", "BEAT_KIND", "MAX_HORIZON_SECONDS"):
        assert getattr(script, name) == getattr(worker_side, name), name
    assert script.LEASE_ID.pattern == worker_side.LEASE_ID.pattern
    assert sys.version_info >= (3, 8) and "match " not in SCRIPT.read_text().split('"""', 2)[2]


# ----- admission through the worker's side ------------------------------------------------------

PRICES = StoragePrices(network_volume_per_gb_month=0.07, pod_volume_running_per_gb_month=0.10,
                       pod_volume_stopped_per_gb_month=0.20, container_disk_per_gb_month=0.10, hours_per_month=720.0,
                       source="ENGINEERING FIXTURE price list", confirmed_by="test operator", confirmed_utc="2026-10-04T09:00:00+00:00")
BALANCE = BalanceConfirmation("test operator", "2026-10-04T09:00:00+00:00", "USD",
                              "ENGINEERING FIXTURE: clientBalance is the spendable prepaid credit balance in USD")
POLICY = AdmissionPolicy(max_balance_age_seconds=120.0, max_rate_age_seconds=3600.0, backup_delay_seconds=300.0,
                         shutdown_delay_seconds=120.0, contingency_fraction=0.25, retention_hours=72.0)
READ_KEY_ENV = "RUNPOD_READ_API_KEY"


class Site:
    """A pod with its timer (in this process, stepped by the worker's waiting), the worker's side,
    RunPod's and GitHub's fakes, and admission over them."""

    def __init__(self, box: Pod, folder: Path, monkeypatch) -> None:
        self.box, self.folder, self.monkeypatch = box, folder, monkeypatch
        folder.mkdir(parents=True)
        self.timer = box.timer()
        self.timer.poll_once()
        self.github = FakeGitHub(REPOSITORY)
        self.github.foreign, box.runpod.foreign = [KEY], [TOKEN, WORKFLOW_TOKEN]
        self.actions = Actions(self.github, box.runpod, box.clock, folder)
        monkeypatch.setenv(GITHUB_TOKEN_ENV, TOKEN)
        monkeypatch.setenv(READ_KEY_ENV, KEY)            # the account key the provider reads with, under its own name
        monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
        self.timer_running = True
        self.primary = self.armer()
        self.backup = GitHubActionsWatchdog(REPOSITORY, role="backup", ack_window_seconds=120.0, grace_seconds=30.0,
                                            api_url=self.github.url, upload_url=self.github.url, clock=box.clock,
                                            sleep=self.sleep, max_retries=0)
        self.shutdown: object = LayeredShutdown(self.primary, self.backup)
        self.fields = {"worker_pods": {"worker-1": "pod-1"}, "balance_confirmation": BALANCE, "storage_prices": PRICES,
                       "destination_per_hour": 0.0, "local_pod_id": "pod-1"}
        self.policy = POLICY
        self.storage = dur.storage(box.mount, LocalDirectoryDestination(folder / "offsite"), source_path=str(box.mount))
        self.planned = self.provider().read_rates("worker-1")
        self.reserve = (self.planned.storage_per_hour + self.planned.destination_per_hour) * POLICY.retention_hours

    def sleep(self, seconds: float) -> None:             # while the worker waits, the timer and Actions do their work
        self.box.clock.advance(seconds)
        if self.timer_running:
            self.timer.poll_once()
        self.actions.pump()

    def armer(self, **changes) -> PodTimer:
        fields = {"lateness_seconds": 120.0, "stop_confirmation": CONFIRMED, "clock": self.box.clock, "sleep": self.sleep}
        return PodTimer(self.box.state, **{**fields, **changes})

    def provider(self) -> RunPodProvider:
        return RunPodProvider(RunPodConfig(**self.fields), key_env=READ_KEY_ENV, rest_url=f"{self.box.runpod.url}/v1",
                              graphql_url=f"{self.box.runpod.url}/graphql", clock=self.box.clock, sleep=lambda s: None,
                              shutdown=self.shutdown)

    def admit(self, seconds: float = 7200.0):
        controller = AdmissionController(self.folder / "admission" / "reservations.jsonl", self.provider(), self.policy,
                                         self.planned, journal=Journal(self.folder / "journal.jsonl", self.box.clock),
                                         clock=self.box.clock)
        return controller.admit("worker-1", seconds, self.storage, self.reserve)

    def backup_outcome(self) -> dict:
        (path,) = sorted((self.box.state / "backups").glob("*.json"))[-1:]
        return json.loads(path.read_text())


@pytest.fixture
def site(box, tmp_path, monkeypatch):
    built = Site(box, tmp_path / "site", monkeypatch)
    yield built
    assert built.github.leaks == []
    assert all(method != "DELETE" for method, _, _ in built.github.log)
    built.github.close()


def test_admission_succeeds_when_the_timer_acknowledges_and_the_watchdog_refuses(site):
    box = site.box
    site.actions.allow({})                               # the watchdog does not know this pod: it refuses the backup arm
    lease = site.admit(7200)
    assert lease.expires_utc == iso(box.after(7200)) and lease.reserved_until_utc == iso(box.after(7200 + 300 + 120))
    governing = box.beat()["governing"]
    assert governing["source"] == "lease" and governing["stop_at_utc"] == iso(box.after(7500))   # lease end plus the backup delay
    outcome = site.backup_outcome()
    assert outcome["lease"] == governing["lease"] and outcome["attempted"] is True and outcome["armed"] is False
    assert "not-a-worker" in outcome["reason"] and outcome["earlier_arm_withdrawn"] == []
    assert names(site.github, "ack-") == [] and len(names(site.github, "void-")) == 1
    # the worker never asked RunPod to change anything: it only read
    assert {(m, p.split("?")[0]) for m, p, _ in box.runpod.log} == {("GET", "/v1/pods"), ("GET", "/v1/networkvolumes"),
                                                                    ("POST", "/graphql")}
    assert all("podStop" not in body for _, _, body in box.runpod.log)
    # at the stop time the timer stops the pod, with the worker long gone
    box.at(7499)
    assert site.timer.enforce_once() == "armed"
    box.at(7500)
    assert site.timer.enforce_once() == "stopped" and box.status() == "EXITED"
    assert iso(box.clock.now) < lease.reserved_until_utc                       # inside the reservation


@pytest.mark.parametrize("trouble", ["github unreachable", "no token on the worker", "actions never runs"])
def test_admission_succeeds_when_the_watchdog_cannot_be_reached(site, trouble):
    if trouble == "github unreachable":
        site.github.close()
        site.github = FakeGitHub(REPOSITORY)             # (a fresh fake only so that the fixture can close one)
    if trouble == "no token on the worker":
        site.monkeypatch.delenv(GITHUB_TOKEN_ENV)
    if trouble == "actions never runs":
        site.actions.enabled = False
    lease = site.admit(3600)
    outcome = site.backup_outcome()
    assert outcome["armed"] is False and outcome["reason"]
    assert TOKEN not in json.dumps(outcome) and KEY not in json.dumps(outcome)
    assert site.box.beat()["governing"]["stop_at_utc"] == iso(site.box.after(3600 + 300))
    assert lease.worker == "worker-1"


def test_the_backup_is_armed_without_a_recent_scheduled_scan_and_stops_only_after_the_timer_should_have(site):
    box = site.box
    assert site.github.runs == []                        # GitHub has not run the schedule at all
    lease = site.admit(7200)
    outcome = site.backup_outcome()
    assert outcome["armed"] is True and outcome["stop_at_utc"] == lease.reserved_until_utc       # the end of the reservation
    ack = record_of(site.github, f"ack-{outcome['arm']}.json")
    assert ack["role"] == "backup" and ack["last_scheduled_scan_utc"] is None and "backup" in ack["statement"]
    assert record_of(site.github, f"arm-{outcome['arm']}.json")["role"] == "backup"
    box.at(7500)
    assert site.actions.scheduled() == 0                 # a scan at the timer's stop time: not yet the backup's
    assert names(site.github, "stop-") == []
    assert site.timer.enforce_once() == "stopped"        # the timer stops the pod
    box.at(7620 + 3 * 3600)                              # GitHub runs a scan three hours later
    assert site.actions.scheduled() == 0
    assert record_of(site.github, f"stop-{outcome['arm']}.json")["result"] == "already-stopped"   # an outside witness
    posts = [p for m, p, _ in box.runpod.log if m == "POST" and p.endswith("/stop")]
    assert posts == []                                   # the watchdog had nothing left to stop


def test_the_backup_also_works_with_the_watchdog_as_first_deployed(site):
    """The script deployed on 3 October knows no roles: it acknowledges only after a recent scheduled
    scan and its acknowledgement names no role. Such an acknowledgement is still a backup."""
    def as_deployed(record: dict) -> dict:
        return {"kind": "durability watchdog acknowledgement v1", "arm": record["arm"], "worker": record["worker"],
                "pod": record["pod"], "stop_at_utc": record["stop_at_utc"], "acknowledged_utc": iso(site.box.clock.now),
                "run_id": "77", "last_scheduled_scan_utc": iso(site.box.clock.now), "scan_interval_seconds": 1800.0}

    site.actions.forge = as_deployed
    lease = site.admit(7200)
    assert site.backup_outcome()["armed"] is True and site.backup_outcome()["stop_at_utc"] == lease.reserved_until_utc


def test_the_backup_stops_a_pod_whose_timer_failed_whenever_github_next_scans(site):
    box = site.box
    lease = site.admit(7200)
    outcome = site.backup_outcome()
    box.command, box.runpod.stop_mode = "fails", "error"             # nothing the pod asks for takes effect
    box.at(7500)
    assert site.timer.enforce_once() == "unconfirmed" and box.status() == "RUNNING"
    box.runpod.stop_mode = "ok"                          # (the watchdog's own key works)
    box.at(7620 + 2 * 3600)
    assert site.actions.scheduled() == 0
    assert record_of(site.github, f"stop-{outcome['arm']}.json")["result"] == "stopped" and box.status() == "EXITED"
    assert lease.reserved_until_utc == iso(box.after(7620))


def test_a_renewal_moves_both_stops_and_a_renewal_without_a_backup_withdraws_the_earlier_arm(site):
    box = site.box
    site.admit(7200)
    first = site.backup_outcome()
    box.at(6000)
    site.timer.poll_once()
    renewed = site.admit(7200)
    second = site.backup_outcome()
    assert box.beat()["governing"]["stop_at_utc"] == iso(box.after(6000 + 7500)) and second["armed"] is True
    assert second["stop_at_utc"] == renewed.reserved_until_utc and second["arm"] > first["arm"]
    box.at(12000)
    site.timer.poll_once()
    site.actions.enabled = False                         # this time the backup cannot be armed
    site.admit(7200)
    third = site.backup_outcome()
    assert third["armed"] is False and third["earlier_arm_withdrawn"] == [second["arm"], first["arm"]]
    assert {f"void-{second['arm']}.json", f"void-{first['arm']}.json"} <= set(names(site.github, "void-"))
    site.actions.enabled = True
    box.at(6000 + 7620 + 60)                             # past the second lease's end: the watchdog must not stop the pod
    assert site.actions.scheduled() == 0
    assert names(site.github, "stop-") == [] and box.status() == "RUNNING"
    assert site.timer.enforce_once() == "armed"          # the timer holds the third lease's stop time


REFUSALS = {
    "no stop was ever observed": (lambda s: setattr(s.shutdown, "primary", s.armer(stop_confirmation=None)), "no observed self-stop is recorded"),
    "the confirmation names no one": (lambda s: setattr(s.shutdown, "primary", s.armer(
        stop_confirmation=StopConfirmation(" ", "2026-10-04T09:00:00+00:00", "x"))), "names no person"),
    "no timer ever ran": (lambda s: shutil.rmtree(s.box.state), "there is no heartbeat on the mount"),
    "the heartbeat is stale": (lambda s: s.box.clock.advance(40), "stale or from the future"),
    "the heartbeat is from the future": (lambda s: (s.box.state / "heartbeat.json").write_text(json.dumps(
        {**s.box.beat(), "utc": iso(s.box.after(40))})), "stale or from the future"),
    "the timer belongs to another pod": (lambda s: (s.box.env.update(RUNPOD_POD_ID="pod-2"), s.box.timer().poll_once()), "belongs to another pod"),
    "the timer lost its supervisor": (lambda s: (s.box.env.update(POD_TIMER_SUPERVISOR="1"), s.box.timer().poll_once()), "not owned by its supervisor"),
    "the timer is already stopping": (lambda s: (setattr(s.timer, "_stopping", True), s.timer.poll_once(), setattr(s, "timer_running", False)),
                                      "already stopping the pod"),
    "the timer cannot ask for a stop": (lambda s: (s.box.env.pop("RUNPOD_API_KEY"), s.box.timer().poll_once()), "no way to ask for a stop"),
    "the timer does not acknowledge": (lambda s: setattr(s, "timer_running", False), "did not acknowledge the lease in time"),
    "nothing is on a network volume": (lambda s: s.box.runpod.pods[0].update(volumeMountPath="/elsewhere"), "not confirmed"),
    "the timer's records are not on the network volume": (
        lambda s: setattr(s.shutdown, "primary", PodTimer(s.folder / "container-disk" / ".pod-timer", lateness_seconds=120.0,
                                                          stop_confirmation=CONFIRMED, clock=s.box.clock, sleep=s.sleep)),
        "not on storage RunPod confirms as persistent"),
    "the shutdown delay is shorter than the timer's lateness": (
        lambda s: setattr(s, "policy", AdmissionPolicy(**{**POLICY.__dict__, "shutdown_delay_seconds": 60.0})), "shorter than the stated lateness"),
    "the reservation is too short for the timer": (
        lambda s: setattr(s.shutdown, "primary", s.armer(ack_seconds=8000.0)), "ends too soon"),
    "no shutdown is configured": (lambda s: setattr(s, "shutdown", None), "no shutdown is configured"),
}


@pytest.mark.parametrize("what", sorted(REFUSALS))
def test_admission_refuses_without_a_running_acknowledging_timer(site, what):
    withdraw, why = REFUSALS[what]
    withdraw(site)
    with pytest.raises(AdmissionRefused, match=why):
        site.admit(7200)
    assert not (site.folder / "admission" / "reservations.jsonl").exists()        # nothing was reserved
    leases, voids = site.box.state / "leases", site.box.state / "voids"
    published = sorted(os.listdir(leases)) if leases.is_dir() else []
    assert published == (sorted(os.listdir(voids)) if voids.is_dir() else [])     # every published record was withdrawn
    assert site.github.dispatches == []                  # the backup is not even asked when the timer refuses
    if site.box.state.exists() and what != "the timer is already stopping":
        fresh = site.box.timer()
        fresh.poll_once()
        assert site.box.beat()["governing"]["source"] == "cap"                    # and none of them governs


def test_the_finishing_stop_goes_through_the_timer_and_needs_no_admission(site):
    box = site.box
    site.admit(7200)
    box.at(3000)                                         # the work is done long before the lease ends
    site.timer.poll_once()
    requests = len(box.runpod.log)
    finishing = site.shutdown.finish("worker-1", "pod-1", 120.0, "the host's jobs are complete and acknowledged")
    assert finishing["finishing"] is True and finishing["stop_at_utc"] == iso(box.after(3120))
    assert box.beat()["governing"]["lease"] == finishing["lease"] and len(box.runpod.log) == requests   # no provider call
    record = json.loads((box.state / "leases" / f"{finishing['lease']}.json").read_text())
    assert record["purpose"] == "finish" and record["reason"].startswith("the host's jobs")
    box.at(3119)
    assert site.timer.enforce_once() == "armed"
    box.at(3120)
    assert site.timer.enforce_once() == "stopped" and box.status() == "EXITED"       # two minutes later, not at the lease's end
    for bad in (1, 7200, True):
        with pytest.raises(DurabilityError):
            site.primary.finish("worker-1", "pod-1", bad)
    site.timer_running = False                           # a timer that does not answer: the earlier deadline stands
    box.runpod.pods[0]["desiredStatus"] = "RUNNING"
    with pytest.raises(ProviderError, match="stale or from the future|did not acknowledge"):
        site.primary.finish("worker-1", "pod-1", 60.0)


def test_a_forged_or_mismatched_acknowledgement_is_not_one(site):
    box = site.box
    site.timer_running = False
    real_publish = worker_side._publish

    def forging(path, record):                           # as the lease is written, someone else writes its "acknowledgement"
        made = real_publish(path, record)
        if path.parent.name == "leases":
            real_publish(box.state / "acks" / path.name, {"kind": worker_side.ACK_KIND, "lease": record["lease"],
                                                          "pod": "pod-1", "stop_at_utc": iso(box.after(99999))})
        return made

    site.monkeypatch.setattr(worker_side, "_publish", forging)
    with pytest.raises(ProviderError, match="names another lease, pod or stop time"):
        site.primary.arm("worker-1", "pod-1", iso(box.after(7200)))
    # a matching acknowledgement without a heartbeat that names the lease is not enough either
    def matching(path, record):
        made = real_publish(path, record)
        if path.parent.name == "leases":
            real_publish(box.state / "acks" / path.name, {"kind": worker_side.ACK_KIND, "lease": record["lease"],
                                                          "pod": "pod-1", "stop_at_utc": record["stop_at_utc"]})
        return made

    site.monkeypatch.setattr(worker_side, "_publish", matching)
    box.clock.advance(5)
    site.timer.poll_once()
    with pytest.raises(ProviderError, match="stale or from the future|did not acknowledge"):
        site.primary.arm("worker-1", "pod-1", iso(box.after(7200)))
    assert len(os.listdir(box.state / "voids")) == 2


def test_configuration_builds_the_timer_with_its_backup_and_reads_with_its_own_key(site, tmp_path, capsys):
    box = site.box
    shutdown = {"kind": "pod-timer", "state_dir": str(box.state), "lateness_seconds": 120,
                "stop_confirmation": dict(CONFIRMED.__dict__),
                "backup": {"kind": "github-actions-watchdog", "repository": REPOSITORY}}
    config = {"kind": "runpod", "worker_pods": {"worker-1": "pod-1"}, "destination_per_hour": 0.0, "local_pod_id": "pod-1",
              "balance_confirmation": dict(BALANCE.__dict__), "storage_prices": dict(PRICES.__dict__),
              "key_env": READ_KEY_ENV, "shutdown": shutdown}
    options = {"rest_url": f"{box.runpod.url}/v1", "graphql_url": f"{box.runpod.url}/graphql", "clock": box.clock}
    built = provider_from(config, **options, shutdown_options={
        "timer": {"clock": box.clock, "sleep": site.sleep},
        "backup": {"api_url": site.github.url, "upload_url": site.github.url, "clock": box.clock, "sleep": site.sleep}})
    assert built.shutdown.describe() == {"kind": "pod-timer", "state_dir": str(box.state), "lateness_seconds": 120.0,
                                         "stop_confirmed": True, "backup": {
                                             "kind": "github-actions-watchdog", "repository": REPOSITORY, "role": "backup",
                                             "lateness_seconds": None, "ack_window_seconds": 120.0}}
    assert built.shutdown_lateness_seconds() == 120.0 and built.read_balance().recognized is True     # read with READ_KEY_ENV
    armed = built.arm_shutdown("worker-1", iso(box.after(7200)))
    assert armed["armed"] is True and armed["backup"]["armed"] is True and armed["stop_at_utc"] == iso(box.after(7080))
    site.monkeypatch.delenv(READ_KEY_ENV)
    with pytest.raises(NotConfigured, match=READ_KEY_ENV):
        built.read_balance()
    bare = shutdown_from({key: value for key, value in shutdown.items() if key not in ("backup", "stop_confirmation")})
    assert bare.backup is None and bare.describe()["stop_confirmed"] is False
    for bad in ({**shutdown, "state_dir": "relative"}, {**shutdown, "lateness_seconds": 0}, {**shutdown, "latency": 1},
                {key: value for key, value in shutdown.items() if key != "lateness_seconds"},
                {**shutdown, "stop_confirmation": {"confirmed_by": "x"}}, {**shutdown, "backup": {"kind": "cron"}},
                {**shutdown, "backup": {"kind": "github-actions-watchdog", "repository": REPOSITORY, "lateness_seconds": 5400}},
                {**shutdown, "backup": {"kind": "github-actions-watchdog"}}):
        with pytest.raises(DurabilityError):
            shutdown_from(bad)
    for bad in ("lowercase", "A B", "X"):
        with pytest.raises(DurabilityError, match="key_env"):
            provider_from({**config, "key_env": bad})
    with pytest.raises(DurabilityError):
        GitHubActionsWatchdog(REPOSITORY, role="backup", lateness_seconds=5400)
    with pytest.raises(DurabilityError):
        GitHubActionsWatchdog(REPOSITORY, role="observer", lateness_seconds=5400)
    # the commands: the timer's state from its heartbeat, and the backup's records
    path = tmp_path / "provider.json"
    path.write_text(json.dumps(config))
    assert cli(["check-timer", "--config", str(path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["governing"]["lease"] == armed["lease"] and report["supervised"] is True and report["state"] == "armed"
    assert cli(["check-watchdog", "--config", str(path), "--worker", "worker-1", "--github-api-url", site.github.url,
                "--github-upload-url", site.github.url]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["armed"] is True and report["arm"] == armed["backup"]["arm"] and report["watchdog"]["role"] == "backup"


def test_no_secret_reaches_the_mount_the_journal_or_an_error(site):
    box = site.box
    site.admit(7200)
    box.at(3000)
    site.timer.poll_once()
    site.actions.secret = "a-wrong-runpod-key-value"
    site.admit(7200)                                     # the backup refuses; admission is granted all the same
    site.timer_running = False
    box.at(6000)
    with pytest.raises(AdmissionRefused) as refused:
        site.admit(7200)
    texts = [path.read_text() for path in box.state.rglob("*") if path.is_file()]
    texts += [(site.folder / "journal.jsonl").read_text(), (site.folder / "admission" / "reservations.jsonl").read_text()]
    texts += [str(refused.value), repr(site.primary), json.dumps(site.shutdown.describe())] + box.lines + site.actions.lines
    texts += [site.github.blobs[asset].decode() for asset in site.github.blobs]
    for secret in (KEY, TOKEN, WORKFLOW_TOKEN, "a-wrong-runpod-key-value"):
        assert all(secret not in text for text in texts)
    assert site.github.leaks == [] and box.runpod.leaks == []
