"""The shutdown watchdog against fake GitHub and RunPod services on 127.0.0.1 (ENGINEERING FIXTURES;
no request leaves the machine, and no real pod, workflow or secret is involved).

``Actions`` below stands for GitHub Actions: it runs the deployed script
(``experiments/durability/watchdog/watchdog.py``, loaded from its file, exactly as the workflow runs
it) for a scheduled scan or for a ``repository_dispatch`` event, with a manual clock. The tests
cover the stop at the deadline and not before, renewal, arms that must never govern (malformed,
unacknowledged, withdrawn, naming a pod outside the allow-list), an idempotent stop that deletes
nothing, the acknowledgement the worker needs before it answers ``armed``, admission end to end and
its refusal when any one input is withdrawn, and secrets that appear in no log or record.

Nothing here shows that GitHub's scheduler runs on time, that RunPod stops a pod or that a stop
ends billing: those wait for the funded one-pod validation (README)."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import dur_fixtures as dur
from fake_github import TOKEN, WORKFLOW_TOKEN, FakeGitHub
from fake_runpod import KEY, FakeRunPod, network_volume, pod

from experiments.durability import shutdown_watchdog as worker_side
from experiments.durability.__main__ import main as cli
from experiments.durability.admission import AdmissionController, AdmissionPolicy
from experiments.durability.common import AdmissionRefused, DurabilityError, Journal, NotConfigured, ProviderError, iso
from experiments.durability.destination import LocalDirectoryDestination
from experiments.durability.github_destination import GITHUB_TOKEN_ENV
from experiments.durability.runpod_provider import (RUNPOD_KEY_ENV, RUNPOD_POD_ENV, BalanceConfirmation, RunPodConfig,
                                                    RunPodProvider, StoragePrices)
from experiments.durability.shutdown_watchdog import GitHubActionsWatchdog
from experiments.durability.wiring import provider_from, shutdown_from

DEPLOYED = Path(__file__).resolve().parents[1] / "watchdog"
REPOSITORY = "owner/backups"
HOUR = 3600.0
SECRETS = (KEY, TOKEN, WORKFLOW_TOKEN)


def load_script():
    spec = importlib.util.spec_from_file_location("deployed_watchdog", DEPLOYED / "watchdog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def after(seconds: float) -> dt.datetime:
    return dur.T0 + dt.timedelta(seconds=seconds)


class Actions:
    """What GitHub Actions does with the workflow, as far as the tests need it: a scheduled run is a
    scan; a ``repository_dispatch`` event is one arm run, ``delay`` seconds after it was sent (never,
    when ``enabled`` is false). Every run gets the workflow's own token and the RunPod secret."""

    def __init__(self, github: FakeGitHub, runpod: FakeRunPod, clock: dur.ManualClock, folder: Path,
                 pods: dict | None = None) -> None:
        self.github, self.runpod, self.clock = github, runpod, clock
        self.script = load_script()
        self.pods_file = folder / "pods.json"
        self.allow({"worker-1": "pod-1"} if pods is None else pods)
        self.secret, self.enabled, self.delay, self.forge = KEY, True, 0.0, None
        self.tail = 0.0                                  # the workflow's default: no waiting inside a run
        self.lines: list[str] = []
        self.sleeps: list[float] = []
        self.on_sleep = None
        self._seen: dict[int, dt.datetime] = {}
        self._done: set[int] = set()
        self._run = 500

    def allow(self, pods: dict) -> None:
        self.pods_file.write_text(json.dumps({"workers": pods}))

    def _sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        if self.on_sleep is not None:
            hook, self.on_sleep = self.on_sleep, None
            hook(seconds)
        else:
            self.clock.advance(seconds)

    def run(self, event: str, arm: str = "") -> int:
        self._run += 1
        env = {"GITHUB_TOKEN": WORKFLOW_TOKEN, "RUNPOD_API_KEY": self.secret, "GITHUB_REPOSITORY": REPOSITORY,
               "GITHUB_API_URL": self.github.url, "WATCHDOG_UPLOAD_URL": self.github.url,
               "WATCHDOG_RUNPOD_URL": f"{self.runpod.url}/v1", "WATCHDOG_PODS": str(self.pods_file),
               "GITHUB_RUN_ID": str(self._run), "GITHUB_RUN_ATTEMPT": "1", "GITHUB_EVENT_NAME": event,
               "WATCHDOG_ARM": arm, "WATCHDOG_INTERVAL_SECONDS": "1800", "WATCHDOG_TAIL_SECONDS": str(self.tail)}
        return self.script.main(env, clock=self.clock, sleep=self._sleep, out=self.lines.append)

    def scheduled(self) -> int:
        """A scheduled scan, listed among the workflow's runs before it starts."""
        self.github.runs.insert(0, {"id": self._run + 1, "event": "schedule",
                                    "created_at": self.clock().strftime("%Y-%m-%dT%H:%M:%SZ")})
        return self.run("schedule")

    def pump(self) -> None:
        """Start the arm runs that are due."""
        for index, event in enumerate(list(self.github.dispatches)):
            self._seen.setdefault(index, self.clock())
            if not self.enabled or index in self._done:
                continue
            if (self.clock() - self._seen[index]).total_seconds() < self.delay:
                continue
            self._done.add(index)
            arm = event["client_payload"]["arm"]
            assert event["event_type"] == self.script.EVENT_ARM
            if self.forge is not None:
                record = json.loads(blob(self.github, f"arm-{arm}.json"))
                put_asset(self.github, f"watchdog-acks-{arm[:4]}-{arm[4:6]}", f"ack-{arm}.json", self.forge(record))
            else:
                self.run("repository_dispatch", arm)

    def events(self, name: str) -> list[dict]:
        return [row for row in map(json.loads, self.lines) if row["event"] == name]


def put_asset(github: FakeGitHub, tag: str, name: str, record) -> None:
    """Place an asset in the fake directly (a record written by someone other than the code under test)."""
    with github._lock:
        release = next((r for r in github.releases.values() if r["tag_name"] == tag), None)
        if release is None:
            release = {"id": github._next(), "tag_name": tag, "name": tag, "draft": False, "prerelease": True}
            github.releases[release["id"]] = release
        data = record if isinstance(record, bytes) else json.dumps(record).encode()
        asset_id = github._next()
        github.assets[asset_id] = {"id": asset_id, "release": release["id"], "name": name, "label": None,
                                   "state": "uploaded", "size": len(data), "digest": None}
        github.blobs[asset_id] = data


def names(github: FakeGitHub, prefix: str = "") -> list[str]:
    with github._lock:
        return sorted(a["name"] for a in github.assets.values() if a["name"].startswith(prefix) and a["state"] == "uploaded")


def blob(github: FakeGitHub, name: str) -> bytes:
    with github._lock:
        found = [github.blobs[a["id"]] for a in github.assets.values() if a["name"] == name]
    assert len(found) == 1, (name, len(found))
    return found[0]


def record_of(github: FakeGitHub, name: str) -> dict:
    return json.loads(blob(github, name))


def stops(runpod: FakeRunPod) -> list[str]:
    return [path for method, path, _ in runpod.log if method == "POST" and path.endswith("/stop")]


def status_of(runpod: FakeRunPod, pod_id: str) -> str:
    return next(p["desiredStatus"] for p in runpod.pods if p["id"] == pod_id)


class World:
    def __init__(self, tmp_path: Path, monkeypatch) -> None:
        self.tmp, self.clock = tmp_path, dur.ManualClock()
        self.github, self.runpod = FakeGitHub(REPOSITORY), FakeRunPod()
        self.github.foreign, self.runpod.foreign = [KEY], [TOKEN, WORKFLOW_TOKEN]
        self.runpod.pods = [pod("pod-1"), pod("pod-2", cost=0.4)]
        self.actions = Actions(self.github, self.runpod, self.clock, tmp_path)
        monkeypatch.setenv(GITHUB_TOKEN_ENV, TOKEN)
        monkeypatch.setenv(RUNPOD_KEY_ENV, KEY)
        monkeypatch.delenv(RUNPOD_POD_ENV, raising=False)
        self.armer = self.make_armer()

    def worker_sleep(self, seconds: float) -> None:
        self.clock.advance(seconds)
        self.actions.pump()

    def make_armer(self, **changes) -> GitHubActionsWatchdog:
        fields = {"lateness_seconds": HOUR, "api_url": self.github.url, "upload_url": self.github.url,
                  "clock": self.clock, "sleep": self.worker_sleep, "max_retries": 0}
        return GitHubActionsWatchdog(REPOSITORY, **{**fields, **changes})

    def arm(self, until_seconds: float, worker: str = "worker-1", pod_id: str = "pod-1", armer=None) -> dict:
        """The worker arms a stop that is complete ``until_seconds`` after T0 (the stop starts an hour earlier)."""
        return (armer or self.armer).arm(worker, pod_id, iso(after(until_seconds)))

    def at(self, seconds: float) -> None:
        self.clock.now = after(seconds)

    def close(self) -> None:
        self.github.close()
        self.runpod.close()


@pytest.fixture
def world(tmp_path, monkeypatch):
    built = World(tmp_path, monkeypatch)
    assert built.actions.scheduled() == 0            # the schedule is running: one scan, nothing to do
    yield built
    assert built.github.leaks == [] and built.runpod.leaks == []
    assert all(method != "DELETE" for method, _, _ in built.github.log)
    assert all(method in ("GET", "POST") for method, _, _ in built.runpod.log)
    built.close()


# ----- the stop: at the deadline, not before, once ---------------------------------------


def test_the_pod_is_stopped_at_its_stop_time_and_not_before(world):
    armed = world.arm(3 * HOUR)
    assert armed["armed"] is True and armed["at_utc"] == iso(after(3 * HOUR)) and armed["pod"] == "pod-1"
    assert armed["stop_at_utc"] == iso(after(2 * HOUR)) and armed["run_id"]
    ack = record_of(world.github, f"ack-{armed['arm']}.json")
    assert ack["run_id"] == armed["run_id"] and ack["pod"] == "pod-1" and ack["stop_at_utc"] == armed["stop_at_utc"]
    for seconds in (HOUR, 2 * HOUR - 1):                 # before the stop time, even by a second: nothing
        world.at(seconds)
        assert world.actions.scheduled() == 0
        assert stops(world.runpod) == [] and status_of(world.runpod, "pod-1") == "RUNNING"
    world.at(2 * HOUR + 600)                             # the first scan after the stop time
    assert world.actions.scheduled() == 0
    assert stops(world.runpod) == ["/v1/pods/pod-1/stop"] and status_of(world.runpod, "pod-1") == "EXITED"
    assert status_of(world.runpod, "pod-2") == "RUNNING" and world.actions.sleeps == []
    outcome = record_of(world.github, f"stop-{armed['arm']}.json")
    assert (outcome["result"], outcome["status_before"], outcome["status_after"]) == ("stopped", "RUNNING", "EXITED")
    assert outcome["pod"] == "pod-1" and outcome["seconds_after_stop_time"] == 600.0 and outcome["event"] == "schedule"


def test_with_a_tail_a_close_stop_time_is_waited_for_inside_the_run(world):
    armed = world.arm(3 * HOUR)
    world.actions.tail = 1200.0
    world.at(2 * HOUR - 1500)                            # further away than the tail: nothing
    assert world.actions.scheduled() == 0 and world.actions.sleeps == [] and stops(world.runpod) == []
    world.at(2 * HOUR - 1200)
    assert world.actions.scheduled() == 0
    assert world.actions.sleeps == [1200.0] and world.clock.now == after(2 * HOUR)
    assert record_of(world.github, f"stop-{armed['arm']}.json")["seconds_after_stop_time"] == 0.0
    world.actions.tail = 9999.0                          # a tail beyond the job's time limit is refused
    assert world.actions.scheduled() == 1 and "out of range" in world.actions.lines[-1]


def test_a_late_scan_stops_at_once_and_records_how_late_it_was(world):
    armed = world.arm(3 * HOUR)
    world.at(2 * HOUR + 1500)                            # a scheduled run was dropped; the next one is late
    assert world.actions.scheduled() == 0
    outcome = record_of(world.github, f"stop-{armed['arm']}.json")
    assert outcome["result"] == "stopped" and outcome["seconds_after_stop_time"] == 1500.0
    assert outcome["seconds_after_stop_time"] <= world.armer.lateness_seconds    # complete by the end of the reservation
    assert world.actions.sleeps == []


def test_the_stop_is_idempotent_and_nothing_is_ever_deleted(world):
    armed = world.arm(3 * HOUR)
    world.at(2 * HOUR + 60)
    for _ in range(3):
        assert world.actions.scheduled() == 0
        world.clock.advance(1800)
    assert stops(world.runpod) == ["/v1/pods/pod-1/stop"]                      # one stop request in three scans
    assert names(world.github, "stop-") == [f"stop-{armed['arm']}.json"]
    paths = {(method, path) for method, path, _ in world.runpod.log}
    assert paths == {("GET", "/v1/pods/pod-1"), ("POST", "/v1/pods/pod-1/stop")}  # it reads and stops one pod; nothing else
    assert {method for method, _, _ in world.github.log} == {"GET", "POST"}
    assert len(world.runpod.pods) == 2                                          # nothing was removed
    # one stop per arm: a pod its operator starts again is left alone until a new lease arms a stop
    world.runpod.pods[0]["desiredStatus"] = "RUNNING"
    seen = len(world.runpod.log)
    assert world.actions.scheduled() == 0
    assert len(world.runpod.log) == seen and status_of(world.runpod, "pod-1") == "RUNNING"
    source = (DEPLOYED / "watchdog.py").read_text()
    assert all(word not in source for word in ("DELETE", "PATCH", "PUT", "terminate\"", "/terminate", "mutation"))


def test_the_stop_is_asked_for_even_when_the_pods_state_cannot_be_read(world):
    armed = world.arm(3 * HOUR)
    world.runpod.read_mode = "error"
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 1                # not confirmed, so the run fails ...
    assert stops(world.runpod) == ["/v1/pods/pod-1/stop"] and status_of(world.runpod, "pod-1") == "EXITED"   # ... but asked
    attempt = record_of(world.github, names(world.github, "stop-attempt-")[0])
    assert (attempt["result"], attempt["status_before"], attempt["stop_answer"]) == ("unconfirmed", "unknown", 200)
    world.runpod.read_mode = "ok"
    world.clock.advance(1800)
    assert world.actions.scheduled() == 0
    assert record_of(world.github, f"stop-{armed['arm']}.json")["result"] == "already-stopped"
    assert len(stops(world.runpod)) == 1


def test_one_pods_failure_does_not_keep_the_scan_from_the_other_pods(world):
    world.actions.allow({"worker-1": "pod-1", "worker-2": "pod-2"})
    first = world.arm(3 * HOUR)
    world.clock.advance(60)
    second = world.arm(3 * HOUR, "worker-2", "pod-2")
    world.at(2 * HOUR + 600)
    world.github.faults = [{"on": "upload", "status": 500}] * 4     # pod-1's outcome cannot be recorded
    assert world.actions.scheduled() == 1
    assert status_of(world.runpod, "pod-1") == "EXITED" and status_of(world.runpod, "pod-2") == "EXITED"
    assert names(world.github, "stop-") == [f"stop-{second['arm']}.json"]
    assert [row["pod"] for row in world.actions.events("pod-stop-error")] == ["pod-1"]
    world.clock.advance(1800)
    assert world.actions.scheduled() == 0                # recorded at the next scan; no second stop request
    assert record_of(world.github, f"stop-{first['arm']}.json")["result"] == "already-stopped"
    assert len(stops(world.runpod)) == 2


def test_a_pod_that_is_already_stopped_or_gone_is_recorded_without_a_stop_request(world):
    first = world.arm(3 * HOUR)
    world.runpod.pods[0]["desiredStatus"] = "EXITED"            # the worker's operator stopped it earlier
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 0
    assert record_of(world.github, f"stop-{first['arm']}.json")["result"] == "already-stopped"
    world.runpod.pods[0]["desiredStatus"] = "RUNNING"           # started again by its operator, with a new lease
    second = world.arm(6 * HOUR)
    world.runpod.pods = [p for p in world.runpod.pods if p["id"] != "pod-1"]
    world.at(5 * HOUR + 60)
    assert world.actions.scheduled() == 0
    assert record_of(world.github, f"stop-{second['arm']}.json")["result"] == "gone"
    assert stops(world.runpod) == []


@pytest.mark.parametrize("mode, result", [("error", "unconfirmed"), ("ignored", "unconfirmed"), ("forbidden", "unconfirmed")])
def test_a_stop_that_is_not_confirmed_fails_the_run_and_is_tried_again(world, mode, result):
    armed = world.arm(3 * HOUR)
    world.runpod.stop_mode = mode
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 1                        # the run fails, visibly
    assert names(world.github, f"stop-{armed['arm']}") == []     # no final outcome
    attempt = record_of(world.github, names(world.github, "stop-attempt-")[0])
    assert attempt["result"] == result and attempt["status_after"] == "RUNNING"
    assert status_of(world.runpod, "pod-1") == "RUNNING"
    world.runpod.stop_mode = "ok"
    world.clock.advance(1800)
    assert world.actions.scheduled() == 0                        # the next scan tries again
    assert record_of(world.github, f"stop-{armed['arm']}.json")["result"] == "stopped"
    assert status_of(world.runpod, "pod-1") == "EXITED"


def test_an_arm_published_before_a_month_ends_is_still_obeyed_in_the_next_month(world):
    world.clock.now = dt.datetime(2026, 10, 31, 23, 30, tzinfo=dt.timezone.utc)
    assert world.actions.scheduled() == 0
    armed = world.armer.arm("worker-1", "pod-1", "2026-11-01T02:30:00.000+00:00")
    assert names(world.github, "arm-")[0].startswith("arm-20261031T")
    world.clock.now = dt.datetime(2026, 11, 1, 1, 31, tzinfo=dt.timezone.utc)
    assert world.actions.scheduled() == 0
    assert record_of(world.github, f"stop-{armed['arm']}.json")["result"] == "stopped"
    with world.github._lock:
        tags = sorted(r["tag_name"] for r in world.github.releases.values())
    assert tags == ["watchdog-acks-2026-10", "watchdog-arms-2026-10", "watchdog-stops-2026-10"]


# ----- renewal and arms that must not govern --------------------------------------------


def test_a_renewal_supersedes_the_earlier_stop_time(world):
    first = world.arm(3 * HOUR)                          # stop at +2 h
    world.at(HOUR)
    assert world.actions.scheduled() == 0
    world.at(1.25 * HOUR)
    second = world.arm(5 * HOUR)                         # renewed before the lease ends: stop at +4 h
    world.at(2 * HOUR + 300)                             # past the first stop time
    assert world.actions.scheduled() == 0
    assert stops(world.runpod) == [] and names(world.github, "stop-") == []
    world.at(4 * HOUR - 60)
    assert world.actions.scheduled() == 0                # just before the renewed stop time: nothing yet
    assert stops(world.runpod) == []
    world.at(4 * HOUR + 120)
    assert world.actions.scheduled() == 0
    assert stops(world.runpod) == ["/v1/pods/pod-1/stop"]
    assert names(world.github, "stop-") == [f"stop-{second['arm']}.json"]
    assert first["arm"] < second["arm"]


def test_a_renewal_that_arrives_while_a_scan_waits_for_the_old_stop_time_wins(world):
    world.arm(3 * HOUR)
    world.actions.tail = 1800.0
    world.at(2 * HOUR - 900)
    renewed = {}

    def renew(seconds: float) -> None:                   # 5 minutes into the scan's wait, the worker renews
        world.clock.advance(300)
        renewed.update(world.arm(5 * HOUR))
        world.clock.now = after(2 * HOUR)

    world.actions.on_sleep = renew
    assert world.actions.scheduled() == 0
    assert renewed["armed"] is True and stops(world.runpod) == []
    assert [row["arm"] for row in world.actions.events("superseded")] != []
    assert status_of(world.runpod, "pod-1") == "RUNNING" and names(world.github, "stop-") == []


def test_a_renewal_that_is_not_acknowledged_leaves_the_earlier_stop_in_force(world):
    first = world.arm(3 * HOUR)
    world.at(1.5 * HOUR)
    world.actions.enabled = False                        # the watchdog does not answer the renewal
    with pytest.raises(ProviderError, match="did not acknowledge the arm in time") as refused:
        world.arm(5 * HOUR)
    assert "withdrawn" in str(refused.value) and len(names(world.github, "void-")) == 1
    late = names(world.github, "void-")[0][len("void-"):-len(".json")]
    world.actions.enabled = True
    world.actions.pump()                                 # the run starts after all: too late, and withdrawn
    assert names(world.github, "ack-") == [f"ack-{first['arm']}.json"]
    assert record_of(world.github, f"refusal-{late}.json")["reason"].startswith("withdrawn")
    # even an acknowledgement written for the withdrawn arm does not make it govern
    put_asset(world.github, "watchdog-acks-2026-10", f"ack-{late}.json", {"kind": worker_side.ACK_KIND, "arm": late})
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 0
    assert names(world.github, "stop-") == [f"stop-{first['arm']}.json"] and status_of(world.runpod, "pod-1") == "EXITED"


def test_a_later_arm_without_an_acknowledgement_never_delays_the_stop(world):
    first = world.arm(3 * HOUR)
    world.at(HOUR)
    later = f"{world.clock.now:%Y%m%dT%H%M%SZ}-{'ab' * 8}"
    put_asset(world.github, "watchdog-arms-2026-10", f"arm-{later}.json",
              {"kind": worker_side.ARM_KIND, "arm": later, "worker": "worker-1", "pod": "pod-1",
               "stop_at_utc": iso(after(20 * HOUR)), "reserved_until_utc": iso(after(21 * HOUR)),
               "published_utc": iso(world.clock.now), "ack_by_utc": iso(after(HOUR + 600))})
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 0
    assert names(world.github, "stop-") == [f"stop-{first['arm']}.json"]


def arm_record(world, arm_id: str | None = None, **changes) -> tuple[str, dict]:
    now = world.clock.now
    arm_id = arm_id or f"{now:%Y%m%dT%H%M%SZ}-{'cd' * 8}"
    record = {"kind": worker_side.ARM_KIND, "arm": arm_id, "worker": "worker-1", "pod": "pod-1",
              "stop_at_utc": iso(now + dt.timedelta(hours=2)), "reserved_until_utc": iso(now + dt.timedelta(hours=3)),
              "published_utc": iso(now), "ack_by_utc": iso(now + dt.timedelta(seconds=600))}
    return arm_id, {**record, **changes}


MALFORMED = {
    "another kind": {"kind": "durability watchdog arm v0"},
    "another arm's record": {"arm": "20261003T120000Z-" + "0" * 16},
    "no worker": {"worker": ""},
    "a pod that is not text": {"pod": 7},
    "a stop time without a timezone": {"stop_at_utc": "2026-10-03T14:00:00"},
    "a stop time that is not a time": {"stop_at_utc": "soon"},
    "a stop before publication": {"stop_at_utc": iso(dur.T0 - dt.timedelta(hours=1))},
    "a stop after the reservation": {"reserved_until_utc": iso(dur.T0 + dt.timedelta(hours=1))},
    "a stop too far away": {"stop_at_utc": iso(dur.T0 + dt.timedelta(hours=49)),
                            "reserved_until_utc": iso(dur.T0 + dt.timedelta(hours=50))},
    "an acknowledgement window that is too long": {"ack_by_utc": iso(dur.T0 + dt.timedelta(hours=1))},
    "an acknowledgement window that has no length": {"ack_by_utc": iso(dur.T0)},
    "a publication time the id does not carry": {"published_utc": iso(dur.T0 + dt.timedelta(seconds=5))},
}


@pytest.mark.parametrize("what", sorted(MALFORMED))
def test_a_malformed_arm_is_refused_and_never_governs(world, what):
    arm_id, record = arm_record(world, **MALFORMED[what])
    put_asset(world.github, "watchdog-arms-2026-10", f"arm-{arm_id}.json", record)
    assert world.actions.run("repository_dispatch", arm_id) == 1
    assert names(world.github, "ack-") == []
    assert record_of(world.github, f"refusal-{arm_id}.json")["reason"].startswith("malformed")
    # with an acknowledgement someone else wrote, it still governs nothing
    put_asset(world.github, "watchdog-acks-2026-10", f"ack-{arm_id}.json", {"kind": worker_side.ACK_KIND, "arm": arm_id})
    world.at(60 * HOUR)
    assert world.actions.scheduled() == 0
    assert world.runpod.log == [] and names(world.github, "stop-") == []
    assert [row["arm"] for row in world.actions.events("arm-ignored")] == [arm_id]


def test_arm_records_that_are_not_records_and_ids_that_are_not_ids_are_refused(world):
    arm_id, _ = arm_record(world)
    put_asset(world.github, "watchdog-arms-2026-10", f"arm-{arm_id}.json", b"[1, 2, 3]")
    assert world.actions.run("repository_dispatch", arm_id) == 1
    other = arm_id[:-1] + "e"
    put_asset(world.github, "watchdog-arms-2026-10", f"arm-{other}.json", b"\x00not json")
    assert world.actions.run("repository_dispatch", other) == 1
    seen = len(world.github.log)
    for bad in ("", "../../etc/passwd", "20261003T120000Z-XYZ", arm_id + "/x", arm_id.upper(), "$(reboot)"):
        assert world.actions.run("repository_dispatch", bad) == 1
    assert len(world.github.log) == seen                 # a malformed id reaches no request and no record name
    assert world.actions.run("repository_dispatch", arm_id[:-1] + "f") == 1     # well formed, but no such record
    assert names(world.github, "ack-") == [] and world.runpod.log == []


def test_an_arm_for_a_pod_outside_the_allow_list_is_refused_and_that_pod_is_never_touched(world):
    for worker, pod_id in (("worker-2", "pod-2"), ("worker-1", "pod-2"), ("worker-2", "pod-1")):
        with pytest.raises(ProviderError, match="the watchdog refused the arm: not-a-worker"):
            world.arm(3 * HOUR, worker, pod_id)
    assert names(world.github, "ack-") == [] and len(names(world.github, "void-")) == 3
    # an acknowledgement written by someone else for such an arm governs nothing
    arm_id = names(world.github, "arm-")[0][len("arm-"):-len(".json")]
    put_asset(world.github, "watchdog-acks-2026-10", f"ack-{arm_id}x.json", {"arm": arm_id})
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 0
    assert world.runpod.log == []                        # no pod was read, let alone stopped
    # the shipped allow-list is empty: nothing can be armed until the operator names a pod
    world.actions.allow(json.loads((DEPLOYED / "pods.example.json").read_text())["workers"])
    world.clock.advance(60)
    with pytest.raises(ProviderError, match="not-a-worker"):
        world.arm(6 * HOUR)
    world.actions.pods_file.write_text("{}")
    assert world.actions.scheduled() == 1 and "allow-list is malformed" in world.actions.lines[-1]


def test_an_arm_is_removed_from_force_when_its_pod_leaves_the_allow_list(world):
    world.arm(3 * HOUR)
    world.actions.allow({"worker-1": "pod-9"})
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 0
    assert world.runpod.log[1:] == [] and names(world.github, "stop-") == []   # only the read at arming


# ----- the acknowledgement the worker requires -------------------------------------------


def test_the_watchdog_acknowledges_only_when_it_is_actually_watching(world):
    world.runpod.pods[0]["desiredStatus"] = "EXITED"
    with pytest.raises(ProviderError, match="refused the arm: pod: RunPod does not report this pod as RUNNING"):
        world.arm(3 * HOUR)
    world.runpod.pods[0]["desiredStatus"] = "RUNNING"
    world.clock.advance(60)
    world.actions.secret = "a-wrong-runpod-key"         # the Actions secret is wrong: the stop could not work
    with pytest.raises(ProviderError, match="refused the arm: runpod: the key was rejected"):
        world.arm(4 * HOUR)
    world.clock.advance(60)
    world.actions.secret = ""                            # ... or was never set
    with pytest.raises(ProviderError, match="refused the arm: configuration: RUNPOD_API_KEY is not set"):
        world.arm(5 * HOUR)
    world.actions.secret = KEY
    world.at(3 * HOUR)                                   # the last scheduled scan is three hours old
    with pytest.raises(ProviderError, match="refused the arm: liveness: no scheduled scan ran recently"):
        world.arm(6 * HOUR)
    world.github.runs.clear()                            # the schedule never ran (Actions disabled, or just deployed)
    world.clock.advance(60)
    with pytest.raises(ProviderError, match="liveness"):
        world.arm(7 * HOUR)
    assert names(world.github, "ack-") == [] and len(names(world.github, "void-")) == 5
    # a refusal is final: running the same arm again, now that a scan has run, acknowledges nothing
    refused = names(world.github, "refusal-")[-1][len("refusal-"):-len(".json")]
    put_asset(world.github, "watchdog-arms-2026-10", "void-moved-away.json", blob(world.github, f"void-{refused}.json"))
    with world.github._lock:
        gone = next(i for i, a in world.github.assets.items() if a["name"] == f"void-{refused}.json")
        del world.github.assets[gone]                    # even if the worker could not withdraw it
    assert world.actions.scheduled() == 0
    assert world.actions.run("repository_dispatch", refused) == 1
    assert "a refusal is final" in world.actions.lines[-1] and names(world.github, "ack-") == []
    world.clock.advance(60)
    assert world.actions.scheduled() == 0
    assert world.arm(8 * HOUR)["armed"] is True


def test_an_acknowledgement_that_is_late_is_not_one(world):
    world.actions.delay = 630.0                          # the run starts after the 600 s window
    with pytest.raises(ProviderError, match="refused the arm: late: the acknowledgement window has passed"):
        world.arm(3 * HOUR)
    world.actions.delay = 590.0                          # slow, but inside the window
    world.clock.advance(60)
    assert world.arm(4 * HOUR)["armed"] is True
    assert len(names(world.github, "ack-")) == 1 and len(names(world.github, "void-")) == 1


FORGED = {
    "another pod": (lambda r: {"pod": "pod-2"}, "names another arm, worker, pod or stop time"),
    "another worker": (lambda r: {"worker": "worker-2"}, "names another arm, worker, pod or stop time"),
    "a later stop time": (lambda r: {"stop_at_utc": iso(after(9 * HOUR))}, "names another arm, worker, pod or stop time"),
    "another arm": (lambda r: {"arm": "20261003T120000Z-" + "1" * 16}, "names another arm, worker, pod or stop time"),
    "another kind": (lambda r: {"kind": "note"}, "names another arm, worker, pod or stop time"),
    "no run": (lambda r: {"run_id": ""}, "names no workflow run"),
    "no scan interval": (lambda r: {"scan_interval_seconds": None}, "states no scan interval"),
    "a scan too sparse for the lateness": (lambda r: {"scan_interval_seconds": 3600.0}, "does not cover two scan intervals"),
    "no timestamps": (lambda r: {"acknowledged_utc": "now"}, "no usable timestamps"),
    "written after the window": (lambda r: {"acknowledged_utc": iso(after(2 * HOUR))}, "after its window"),
    "no recent scan": (lambda r: {"last_scheduled_scan_utc": iso(dur.T0 - dt.timedelta(hours=3))}, "without a recent scheduled scan"),
}


@pytest.mark.parametrize("what", sorted(FORGED))
def test_an_acknowledgement_that_does_not_match_is_refused_and_the_arm_withdrawn(world, what):
    change, why = FORGED[what]

    def forge(record: dict) -> dict:
        good = {"kind": worker_side.ACK_KIND, "arm": record["arm"], "worker": record["worker"], "pod": record["pod"],
                "stop_at_utc": record["stop_at_utc"], "acknowledged_utc": iso(world.clock.now), "run_id": "77",
                "last_scheduled_scan_utc": iso(dur.T0), "scan_interval_seconds": 1800.0}
        return {**good, **change(record)}

    world.actions.forge = forge
    with pytest.raises(ProviderError, match=why) as refused:
        world.arm(3 * HOUR)
    assert "withdrawn" in str(refused.value) and len(names(world.github, "void-")) == 1
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 0 and world.runpod.log == []      # a withdrawn arm stops nothing


def test_the_worker_side_refuses_before_or_without_an_acknowledgement(world, monkeypatch):
    with pytest.raises(ProviderError, match="ends too soon for the watchdog"):
        world.arm(HOUR + 600)                            # the stop time would fall inside the acknowledgement window
    with pytest.raises(ProviderError, match="at most 48 hours ahead"):
        world.arm(50 * HOUR)
    with pytest.raises(NotConfigured, match="no worker or pod"):
        world.arm(3 * HOUR, pod_id=" ")
    assert names(world.github) == [] and world.github.dispatches == []
    world.github.dispatch_status = 404                   # the token cannot send the event
    with pytest.raises(ProviderError, match="answered 404 to the watchdog dispatch") as refused:
        world.arm(3 * HOUR)
    assert "withdrawn" in str(refused.value) and len(names(world.github, "void-")) == 1
    world.github.dispatch_status = 204
    with pytest.raises(ProviderError, match="does not cover two scan intervals"):
        world.arm(3 * HOUR, armer=world.make_armer(lateness_seconds=1800.0))   # the real watchdog, too little lateness
    monkeypatch.delenv(GITHUB_TOKEN_ENV)
    seen = len(world.github.log)
    with pytest.raises(NotConfigured, match=GITHUB_TOKEN_ENV):
        world.arm(3 * HOUR)
    with pytest.raises(NotConfigured, match=GITHUB_TOKEN_ENV):
        world.armer.status("pod-1")
    assert len(world.github.log) == seen                 # nothing was sent without the token
    for bad in ({"lateness_seconds": 0}, {"lateness_seconds": True}, {"ack_window_seconds": 3600.0}, {"poll_seconds": -1}):
        with pytest.raises(DurabilityError):
            world.make_armer(**bad)
    with pytest.raises(DurabilityError, match="owner/name"):
        GitHubActionsWatchdog("not a repository", lateness_seconds=HOUR)


# ----- admission, end to end -------------------------------------------------------------

CONFIRMATION = BalanceConfirmation("test operator", iso(dur.T0), "USD",
                                   "ENGINEERING FIXTURE: clientBalance is the spendable prepaid credit balance in USD")
PRICES = StoragePrices(network_volume_per_gb_month=0.07, pod_volume_running_per_gb_month=0.10,
                       pod_volume_stopped_per_gb_month=0.20, container_disk_per_gb_month=0.10, hours_per_month=720.0,
                       source="ENGINEERING FIXTURE price list", confirmed_by="test operator", confirmed_utc=iso(dur.T0))
VOLUME = network_volume("vol-1", size=100)
POLICY = AdmissionPolicy(max_balance_age_seconds=120.0, max_rate_age_seconds=3600.0, backup_delay_seconds=300.0,
                         shutdown_delay_seconds=HOUR, contingency_fraction=0.25, retention_hours=72.0)


class Deployment:
    """Everything admission needs, confirmed in fakes: the RunPod account, the storage, the watchdog."""

    def __init__(self, world: World, folder: Path) -> None:
        self.world, self.folder = world, folder
        self.source = folder / "workspace"
        self.source.mkdir(parents=True)
        world.runpod.pods = [pod("pod-1", volume=VOLUME, mount=str(self.source))]
        world.runpod.volumes = [VOLUME]
        self.storage = dur.storage(self.source, LocalDirectoryDestination(folder / "offsite"), source_path=str(self.source))
        self.fields = {"worker_pods": {"worker-1": "pod-1"}, "balance_confirmation": CONFIRMATION,
                       "storage_prices": PRICES, "destination_per_hour": 0.0, "local_pod_id": "pod-1"}
        self.shutdown: object = world.armer
        self.policy = POLICY
        self.planned = self.provider().read_rates("worker-1")
        self.reserve = (self.planned.storage_per_hour + self.planned.destination_per_hour) * POLICY.retention_hours

    def provider(self) -> RunPodProvider:
        world = self.world
        return RunPodProvider(RunPodConfig(**self.fields), rest_url=f"{world.runpod.url}/v1",
                              graphql_url=f"{world.runpod.url}/graphql", clock=world.clock, sleep=lambda s: None,
                              shutdown=self.shutdown)

    def admit(self, seconds: float = 2 * HOUR):
        controller = AdmissionController(self.folder / "admission" / "reservations.jsonl", self.provider(), self.policy,
                                         self.planned, journal=Journal(self.folder / "journal.jsonl", self.world.clock),
                                         clock=self.world.clock)
        return controller.admit("worker-1", seconds, self.storage, self.reserve)


def test_admission_succeeds_end_to_end_once_the_watchdog_acknowledges(world, tmp_path):
    deployment = Deployment(world, tmp_path / "a")
    lease = deployment.admit(2 * HOUR)
    assert lease.expires_utc == iso(after(2 * HOUR)) and lease.reserved_until_utc == iso(after(3 * HOUR + 300))
    arm = record_of(world.github, names(world.github, "arm-")[0])
    assert (arm["worker"], arm["pod"], arm["reserved_until_utc"]) == ("worker-1", "pod-1", lease.reserved_until_utc)
    assert arm["stop_at_utc"] == iso(after(2 * HOUR + 300))      # the end of the lease plus the backup delay
    assert names(world.github, "ack-") == [f"ack-{arm['arm']}.json"]
    assert [event["client_payload"] for event in world.github.dispatches] == [{"arm": arm["arm"]}]
    # the worker runs, the laptop is away, the lease ends: the watchdog stops the pod inside the reservation
    world.at(2 * HOUR + 300 + 1700)
    assert world.actions.scheduled() == 0
    outcome = record_of(world.github, f"stop-{arm['arm']}.json")
    assert outcome["result"] == "stopped" and status_of(world.runpod, "pod-1") == "EXITED"
    assert world.clock.now <= after(3 * HOUR + 300)
    # the worker's side never asked RunPod to change anything
    worker_calls = {(m, p.split("?")[0]) for m, p, _ in world.runpod.log} - {("GET", "/v1/pods/pod-1"), ("POST", "/v1/pods/pod-1/stop")}
    assert worker_calls == {("GET", "/v1/pods"), ("GET", "/v1/networkvolumes"), ("POST", "/graphql")}


def test_a_renewed_lease_moves_the_stop_time(world, tmp_path):
    deployment = Deployment(world, tmp_path / "a")
    deployment.admit(2 * HOUR)
    world.at(HOUR)
    assert world.actions.scheduled() == 0
    world.at(1.75 * HOUR)                                # renewed before the first lease ends
    renewed = deployment.admit(2 * HOUR)
    assert renewed.reserved_until_utc == iso(after(1.75 * HOUR + 3 * HOUR + 300))
    world.at(2 * HOUR + 300 + 60)                        # past the first lease's stop time
    assert world.actions.scheduled() == 0 and stops(world.runpod) == []
    world.at(1.75 * HOUR + 2 * HOUR + 300 + 900)         # the first scan after the renewed stop time
    assert world.actions.scheduled() == 0 and stops(world.runpod) == ["/v1/pods/pod-1/stop"]
    assert world.clock.now <= after(1.75 * HOUR + 3 * HOUR + 300)       # inside the renewed reservation


WITHDRAWN = {
    "no watchdog is configured": (lambda d: setattr(d, "shutdown", None), "no shutdown is configured"),
    "Actions does not run the workflow": (lambda d: setattr(d.world.actions, "enabled", False), "did not acknowledge the arm in time"),
    "the schedule is not running": (lambda d: d.world.github.runs.clear(), "liveness"),
    "the allow-list does not name the pod": (lambda d: d.world.actions.allow({}), "not-a-worker"),
    "the Actions secret is wrong": (lambda d: setattr(d.world.actions, "secret", "wrong"), "the key was rejected"),
    "the worker has no GitHub token": (lambda d: d.monkeypatch.delenv(GITHUB_TOKEN_ENV), GITHUB_TOKEN_ENV),
    "the policy's shutdown delay is shorter than the watchdog's lateness": (
        lambda d: setattr(d, "policy", AdmissionPolicy(**{**POLICY.__dict__, "shutdown_delay_seconds": 1800.0})),
        "shorter than the stated lateness"),
    "the lateness does not cover the scan interval": (
        lambda d: (setattr(d, "shutdown", d.world.make_armer(lateness_seconds=900.0)),
                   setattr(d, "policy", AdmissionPolicy(**{**POLICY.__dict__, "shutdown_delay_seconds": 900.0}))),
        "does not cover two scan intervals"),
    "the balance is not confirmed": (lambda d: d.fields.update(balance_confirmation=None), "not confirmed"),
    "the storage prices are not declared": (lambda d: d.fields.update(storage_prices=None), "provider inputs are unavailable"),
    "the source is not on a network volume": (lambda d: d.fields.update(local_pod_id="pod-9"), "not confirmed"),
    "the pod is not running": (lambda d: d.world.runpod.pods[0].update(desiredStatus="EXITED"), "not"),
    "the watchdog answers for another pod": (
        lambda d: setattr(d, "shutdown", type("Other", (), {"lateness_seconds": HOUR, "arm": staticmethod(
            lambda worker, pod_id, at_utc: {"armed": True, "at_utc": at_utc, "pod": "pod-2"})})()),
        "did not confirm a stop of this worker's pod"),
}


@pytest.mark.parametrize("what", sorted(WITHDRAWN))
def test_admission_refuses_when_any_one_input_is_withdrawn(world, tmp_path, monkeypatch, what):
    deployment = Deployment(world, tmp_path / "a")
    deployment.monkeypatch = monkeypatch
    withdraw, why = WITHDRAWN[what]
    withdraw(deployment)
    with pytest.raises(AdmissionRefused, match=why):
        deployment.admit(2 * HOUR)
    assert not (tmp_path / "a" / "admission" / "reservations.jsonl").exists()     # nothing was reserved
    assert len(names(world.github, "void-")) == len(names(world.github, "arm-"))  # every published arm was withdrawn
    world.at(40 * HOUR)
    assert world.actions.scheduled() == 0 and stops(world.runpod) == []


def test_the_configuration_builds_the_watchdog_only_when_it_is_named(world):
    config = {"kind": "runpod", "worker_pods": {"worker-1": "pod-1"}, "destination_per_hour": 0.0,
              "balance_confirmation": dict(CONFIRMATION.__dict__), "storage_prices": dict(PRICES.__dict__)}
    options = {"rest_url": f"{world.runpod.url}/v1", "graphql_url": f"{world.runpod.url}/graphql"}
    bare = provider_from(config, **options)
    assert bare.shutdown is None
    with pytest.raises(NotConfigured, match="no shutdown is configured"):
        bare.arm_shutdown("worker-1", iso(after(3 * HOUR)))
    shutdown = {"kind": "github-actions-watchdog", "repository": REPOSITORY, "lateness_seconds": 3600}
    built = provider_from({**config, "shutdown": shutdown}, **options,
                          shutdown_options={"api_url": world.github.url, "upload_url": world.github.url,
                                            "clock": world.clock, "sleep": world.worker_sleep})
    assert built.shutdown.describe() == {"kind": "github-actions-watchdog", "repository": REPOSITORY,
                                         "lateness_seconds": 3600.0, "ack_window_seconds": 600.0}
    assert built.shutdown_lateness_seconds() == 3600.0
    assert built.arm_shutdown("worker-1", iso(after(3 * HOUR)))["armed"] is True
    with pytest.raises(NotConfigured, match="no pod is configured"):
        built.arm_shutdown("worker-7", iso(after(3 * HOUR)))
    assert shutdown_from(None) is None
    for bad in ({"kind": "cron"}, {**shutdown, "latency": 1}, {"kind": "github-actions-watchdog", "repository": REPOSITORY},
                {"kind": "github-actions-watchdog", "lateness_seconds": 3600}, {**shutdown, "repository": "nope"},
                {**shutdown, "lateness_seconds": "3600"}):
        with pytest.raises(DurabilityError):
            shutdown_from(bad)
        with pytest.raises(DurabilityError):
            provider_from({**config, "shutdown": bad}, **options)


def test_the_check_watchdog_command_reads_the_records_and_changes_nothing(world, tmp_path, capsys):
    config = {"kind": "runpod", "worker_pods": {"worker-1": "pod-1", "worker-2": "pod-2"},
              "shutdown": {"kind": "github-actions-watchdog", "repository": REPOSITORY, "lateness_seconds": 3600}}
    path = tmp_path / "provider.json"
    path.write_text(json.dumps(config))
    arguments = ["check-watchdog", "--config", str(path), "--github-api-url", world.github.url,
                 "--github-upload-url", world.github.url, "--worker"]
    assert cli(arguments + ["worker-1"]) == 0
    assert json.loads(capsys.readouterr().out)["armed"] is False
    armed = world.arm(3 * HOUR)
    seen = len(world.github.log)
    assert cli(arguments + ["worker-1"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert (report["armed"], report["arm"], report["stop_at_utc"]) == (True, armed["arm"], armed["stop_at_utc"])
    assert report["acknowledged_by_run"] == armed["run_id"] and report["stop"] is None
    assert cli(arguments + ["worker-2"]) == 0 and json.loads(capsys.readouterr().out)["armed"] is False
    assert all(method == "GET" for method, _, _ in world.github.log[seen:])     # the command only read
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 0
    assert cli(arguments + ["worker-1"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["armed"] is False and report["stop"]["result"] == "stopped"
    # check-provider reports that a watchdog is configured, and asks it nothing
    seen = len(world.github.log)
    provider_arguments = ["check-provider", "--config", str(path), "--worker", "worker-1",
                          "--runpod-rest-url", f"{world.runpod.url}/v1", "--runpod-graphql-url", f"{world.runpod.url}/graphql"]
    assert cli(provider_arguments) == 0
    shutdown = json.loads(capsys.readouterr().out)["shutdown"]
    assert shutdown["configured"]["repository"] == REPOSITORY and "acknowledgement" in shutdown["can_arm"]
    assert len(world.github.log) == seen
    del config["shutdown"]
    path.write_text(json.dumps(config))
    assert cli(provider_arguments) == 0 and json.loads(capsys.readouterr().out)["shutdown"]["can_arm"] is False
    assert cli(arguments + ["worker-1"]) == 0 and json.loads(capsys.readouterr().out)["watchdog"] is None
    assert cli(arguments + ["worker-9"]) == 2
    assert TOKEN not in capsys.readouterr().err


# ----- secrets, permissions and the deployed files ----------------------------------------


def test_no_secret_reaches_a_log_a_record_or_the_other_service(world, tmp_path):
    deployment = Deployment(world, tmp_path / "a")
    deployment.admit(2 * HOUR)
    world.at(HOUR)
    world.actions.secret = "a-wrong-runpod-key-value"
    messages = []
    with pytest.raises(AdmissionRefused) as refused:    # a refused renewal: refusal and void records
        deployment.admit(2 * HOUR)
    messages.append(str(refused.value))
    world.actions.secret = KEY
    world.runpod.stop_mode = "error"
    world.at(2 * HOUR + 400)
    assert world.actions.scheduled() == 1                # a failed stop: an attempt record
    world.runpod.stop_mode = "ok"
    assert world.actions.scheduled() == 0
    written = [world.github.blobs[asset_id] for asset_id in world.github.blobs]
    kinds = {name.split("-")[0] for name in names(world.github)}
    assert kinds == {"arm", "ack", "void", "refusal", "stop"} and len(names(world.github, "stop-attempt-")) == 1
    texts = [data.decode() for data in written] + world.actions.lines + messages
    texts += [(tmp_path / "a" / "journal.jsonl").read_text(), (tmp_path / "a" / "admission" / "reservations.jsonl").read_text()]
    texts += [repr(world.armer), repr(world.armer.http), json.dumps(world.armer.describe())]
    texts += [path for _, path, _ in world.github.log] + [path + body for _, path, body in world.runpod.log]
    for secret in (*SECRETS, "a-wrong-runpod-key-value"):
        assert all(secret not in text for text in texts)
    assert world.github.leaks == [] and world.runpod.leaks == []     # each secret went only to its own service
    downloads = [had_token for method, path, had_token in world.github.log if path.startswith("/_blob/")]
    assert downloads and not any(downloads)              # no token on the redirected downloads
    # the worker's token cannot read workflow runs, and does not try; only the workflow's token does
    assert all(had for method, path, had in world.github.log if "/actions/" in path)
    assert world.actions.script.Refused("x").args == ("x",)


def test_the_two_sides_agree_on_the_record_format(world):
    script = world.actions.script
    for name in ("ARM_KIND", "ACK_KIND", "EVENT_ARM", "MAX_HORIZON_SECONDS", "MAX_ACK_WINDOW_SECONDS"):
        assert getattr(script, name) == getattr(worker_side, name), name
    assert script.ARM_ID.pattern == worker_side.ARM_ID.pattern
    arm = world.arm(3 * HOUR)
    assert script.ARM_ID.fullmatch(arm["arm"])
    record = record_of(world.github, f"arm-{arm['arm']}.json")
    assert set(record) == {"kind", "arm", "worker", "pod", "stop_at_utc", "reserved_until_utc", "published_utc", "ack_by_utc"}
    assert script.valid_arm(record, arm["arm"], {"worker-1": "pod-1"})["stop_at"] == after(2 * HOUR)
    source = (DEPLOYED / "watchdog.py").read_text()
    imports = {line.split()[1].split(".")[0] for line in source.splitlines() if line.startswith(("import ", "from "))}
    assert imports <= {"__future__", "datetime", "json", "os", "re", "sys", "time", "urllib"}     # self-contained


def test_an_empty_allow_list_needs_no_runpod_key_and_a_listed_pod_without_one_fails_loudly(world):
    armed = world.arm(3 * HOUR)                          # records exist from an earlier lease
    world.runpod.log.clear()
    world.actions.secret = ""                            # the Actions secret is not set (yet, or any more)
    world.actions.allow({})
    world.at(2 * HOUR + 60)
    assert world.actions.scheduled() == 0                # nothing to watch: green, and RunPod is not asked anything
    assert world.runpod.log == [] and world.actions.events("scan-done")[-1]["pods"] == 0
    world.actions.allow({"worker-1": "pod-1"})
    assert world.actions.scheduled() == 1                # a pod to watch and no key: red, and it says why
    assert "RUNPOD_API_KEY is not set, but the allow-list names a pod" in world.actions.lines[-1]
    assert world.runpod.log == [] and names(world.github, "stop-") == []
    world.clock.advance(60)
    arm_id, record = arm_record(world)
    put_asset(world.github, "watchdog-arms-2026-10", f"arm-{arm_id}.json", record)
    assert world.actions.run("repository_dispatch", arm_id) == 1          # an arm is never acknowledged without the key
    assert record_of(world.github, f"refusal-{arm_id}.json")["reason"] == "configuration: RUNPOD_API_KEY is not set"
    assert names(world.github, "ack-") == [f"ack-{armed['arm']}.json"] and world.runpod.log == []
    world.actions.secret = KEY                           # the key is set: the next scan carries out the stop
    assert world.actions.scheduled() == 0
    assert record_of(world.github, f"stop-{armed['arm']}.json")["result"] == "stopped"


def workflow() -> tuple[str, dict, dict, list[dict]]:
    text = (DEPLOYED / "watchdog.yml").read_text()
    parsed = yaml.safe_load(text)
    (job,) = parsed["jobs"].values()
    return text, parsed, job, job["steps"]


def test_the_workflow_has_least_privilege_and_keeps_secrets_out_of_the_shell():
    text, parsed, job, steps = workflow()
    triggers = parsed[True]                              # YAML reads the key ``on`` as a boolean
    assert parsed["permissions"] == {"contents": "write", "actions": "read"}
    assert set(triggers) == {"schedule", "repository_dispatch", "workflow_dispatch"}
    assert triggers["repository_dispatch"] == {"types": [worker_side.EVENT_ARM]}
    assert not triggers["workflow_dispatch"]            # a manual run takes no input
    (cron,) = [entry["cron"] for entry in triggers["schedule"]]
    minutes, hours = cron.split()[0].split(","), cron.split()[1:]
    assert hours == ["*", "*", "*", "*"] and len(minutes) == 2 and "0" not in minutes     # twice an hour, off the hour
    assert "permissions" not in job and job["runs-on"] == "ubuntu-latest"
    assert "env" not in parsed and "env" not in job and "defaults" not in parsed          # no secret reaches every step
    checkout, verify, script = steps
    assert all("if" not in step and "continue-on-error" not in step for step in steps)    # a failed step ends the job
    # every action is pinned to a full commit, and there is only the checkout
    uses = [step["uses"] for step in steps if "uses" in step]
    assert uses == [checkout["uses"]] and all(re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", use) for use in uses)
    assert checkout["uses"].startswith("actions/checkout@") and checkout["with"] == {"persist-credentials": False}
    assert len(re.findall(r"^\s*(?:- )?uses:", text, flags=re.M)) == 1
    # the verification step comes before the script, holds no secret and uses no expression
    assert "env" not in verify and "${{" not in verify["run"] and "with" not in verify and "uses" not in verify
    assert script["run"] == "python3 -I watchdog/watchdog.py"       # isolated; no expression, secret or payload in a shell line
    env = script["env"]
    assert env == {"GITHUB_TOKEN": "${{ github.token }}", "RUNPOD_API_KEY": "${{ secrets.RUNPOD_API_KEY }}",
                   "WATCHDOG_ARM": "${{ github.event.client_payload.arm }}", "WATCHDOG_INTERVAL_SECONDS": "1800",
                   "WATCHDOG_TAIL_SECONDS": "0"}
    assert [name for step in steps for name in step.get("env", {})] == list(env)          # only the last step has an environment
    interval = float(env["WATCHDOG_INTERVAL_SECONDS"])
    assert interval == 3600 / len(minutes) and abs(int(minutes[1]) - int(minutes[0])) * 60 == interval
    assert job["timeout-minutes"] * 60 >= float(env["WATCHDOG_TAIL_SECONDS"]) + 600   # the wait, the stop and its checks
    assert worker_side.RECOMMENDED_LATENESS_SECONDS == 3 * interval
    assert parsed["concurrency"]["cancel-in-progress"] is False
    assert text.count("secrets.") == 1 and "set -x" not in text
    assert json.loads((DEPLOYED / "pods.example.json").read_text()) == {"workers": {}}


def pins() -> dict[str, str]:
    """The files the workflow pins, as its verification step writes them: path -> SHA-256."""
    _, _, _, steps = workflow()
    lines = [line.split() for line in steps[1]["run"].splitlines() if line.strip().startswith("pin ")]
    assert all(len(line) == 3 and re.fullmatch(r"[0-9a-f]{64}", line[1]) for line in lines)
    return {path: digest for _, digest, path in lines}


def test_the_workflow_pins_the_script_and_the_allow_list_as_they_are_shipped():
    shipped = {"watchdog/watchdog.py": DEPLOYED / "watchdog.py", "watchdog/pods.json": DEPLOYED / "pods.example.json"}
    assert pins() == {path: hashlib.sha256(source.read_bytes()).hexdigest() for path, source in shipped.items()}
    # everything the script step reads from the repository is pinned: the script and its default allow-list
    script = (DEPLOYED / "watchdog.py").read_text()
    assert 'env.get("WATCHDOG_PODS", "watchdog/pods.json")' in script
    assert len(re.findall(r"(?<![.\w])open\(", script)) == 1       # the allow-list is the only file it opens


def run_step(step: dict, folder: Path) -> subprocess.CompletedProcess:
    """Run a workflow step's commands the way the runner does for ``shell: bash``, with an
    environment that holds nothing but a PATH."""
    assert step["shell"] == "bash"
    return subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", step["run"]], cwd=folder,
                          env={"PATH": os.environ["PATH"]}, capture_output=True, text=True, timeout=60)


@pytest.mark.skipif(shutil.which("sha256sum") is None or shutil.which("bash") is None,
                    reason="the verification step needs bash and sha256sum, as on the Actions runner")
def test_the_verification_step_rejects_a_changed_or_missing_file_before_the_script_runs(tmp_path):
    _, _, _, (_, verify, _) = workflow()
    repo = tmp_path / "repo"
    (repo / "watchdog").mkdir(parents=True)
    script, allow = repo / "watchdog" / "watchdog.py", repo / "watchdog" / "pods.json"

    def fresh() -> None:
        shutil.copyfile(DEPLOYED / "watchdog.py", script)
        shutil.copyfile(DEPLOYED / "pods.example.json", allow)

    fresh()
    passed = run_step(verify, repo)
    assert passed.returncode == 0 and "the pinned ones" in passed.stdout
    changes = {
        "a script that also sends the key elsewhere": lambda: script.write_text(script.read_text() + "\nprint('x')\n"),
        "a script changed by one byte": lambda: script.write_bytes(script.read_bytes()[:-1]),
        "an allow-list without the pod": lambda: allow.write_text('{"workers": {}}'),
        "an allow-list naming another pod": lambda: allow.write_text('{\n  "workers": {"worker-1": "pod-x"}\n}\n'),
        "no script": script.unlink,
        "no allow-list": allow.unlink,
        "an empty script": lambda: script.write_bytes(b""),
    }
    for what, change in changes.items():
        fresh()
        change()
        refused = run_step(verify, repo)
        assert refused.returncode != 0, what
        assert "is not the pinned file" in refused.stdout and "the pinned ones" not in refused.stdout, what
    # the step executes nothing from the repository: a file named like its tool changes nothing
    fresh()
    (repo / "sha256sum").write_text("#!/bin/sh\nexit 0\n")
    (repo / "sha256sum").chmod(0o755)
    script.write_text("changed")
    assert run_step(verify, repo).returncode != 0


def test_isolated_python_does_not_import_a_module_placed_next_to_the_script(tmp_path):
    """The script step runs ``python3 -I``. Without it, Python puts the script's folder first on
    the import path, and a ``json.py`` pushed next to the pinned script would run with the secret."""
    _, _, _, (_, _, step) = workflow()
    assert step["run"].split()[:2] == ["python3", "-I"]
    folder = tmp_path / "watchdog"
    folder.mkdir()
    shutil.copyfile(DEPLOYED / "watchdog.py", folder / "watchdog.py")
    marker = tmp_path / "shadow-ran"
    (folder / "json.py").write_text(f"open({str(marker)!r}, 'w').write('ran')\nraise SystemExit(0)\n")
    env = {"PATH": os.environ["PATH"], "GITHUB_EVENT_NAME": "schedule"}       # no token: the script refuses at once
    isolated = subprocess.run([sys.executable, "-I", "watchdog/watchdog.py"], cwd=tmp_path, env=env,
                              capture_output=True, text=True, timeout=60)
    assert isolated.returncode == 1 and "GITHUB_TOKEN is not set" in isolated.stdout and not marker.exists()
    plain = subprocess.run([sys.executable, "-B", "watchdog/watchdog.py"], cwd=tmp_path, env=env,
                           capture_output=True, text=True, timeout=60)
    assert marker.exists() and plain.returncode == 0      # what the flag prevents
