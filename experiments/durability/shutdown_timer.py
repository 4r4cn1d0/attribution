"""The worker's side of the in-pod stop timer, and the layering of the two shutdowns (stdlib only).

The stop at the end of a reservation is done by a timer process inside the pod
(``pod_timer/pod_timer.py``, started by the pod's start command and described there and in the
README). The GitHub Actions watchdog (``shutdown_watchdog``) is a best-effort backup: GitHub ran 3
of its 33 scheduled slots in the first 16 hours after deployment (the user's decision of
4 October 2026 amends that of 3 October).

``PodTimer.arm(worker, pod, at_utc)``, called by admission through ``RunPodProvider``:

1. requires a recorded ``StopConfirmation``: a named person saw a pod of this kind stop itself
   through this timer (the cap-only check of the funded validation). The timer's acknowledgement
   shows that a deadline is being enforced; only an observed stop shows that RunPod honours the
   stop a pod asks for itself, and nothing in RunPod's documentation states what the key it puts
   in every pod may do;
2. reads the timer's heartbeat on the persistent mount and refuses unless it is fresh, names this
   pod, comes from a timer that its supervisor still owns, is not already stopping and has a way
   to ask for the stop;
3. publishes a lease record, create-only: ``stop_at_utc = at_utc - lateness_seconds``;
4. waits a short, bounded time for the timer's acknowledgement of that record and for a heartbeat,
   written after the record, that names it as governing with exactly that stop time;
5. answers ``armed`` only then. Otherwise it withdraws the record with a void and raises; admission
   grants no lease.

``lateness_seconds`` is the bound on how long the stop takes from the moment the timer asks: the
timer asks within a second of ``stop_at_utc``, so this is RunPod's own latency, to be measured. As
with every shutdown, admission refuses a policy whose shutdown delay is shorter.

``LayeredShutdown(primary, backup)`` is what the provider gets when a backup is configured. The
primary must arm, or admission refuses. The backup is then attempted with its own bounded wait and
its outcome is recorded on the mount (``backups/<lease>.json``) and returned; it is never required.
The backup's stop time is the end of the reservation itself, so it can only act after the timer
should have. If a renewal's backup cannot be armed, the earlier backup arm is withdrawn, so that
the watchdog does not stop a pod whose lease was renewed.

``settings(...)`` builds what the operator gives RunPod when creating the pod: the environment
variables that carry the timer script and the cap, and the start command that unpacks the script,
checks its SHA-256, runs it, and stops the pod if any of that fails.

Worker and timer share the pod and its mount, so this protects against death, not malice: a worker
that rewrites the records can defeat its own timer. The worker's code never does.
"""

from __future__ import annotations

import base64
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .common import Clock, DurabilityError, NotConfigured, ProviderError, iso, parse_utc, utc_clock

__all__ = ["PodTimer", "LayeredShutdown", "StopConfirmation", "settings", "TIMER_SCRIPT", "LEASE_KIND", "ACK_KIND",
           "BEAT_KIND", "LEASE_ID", "MAX_HORIZON_SECONDS", "RECOMMENDED_LATENESS_SECONDS", "START_SCRIPT", "START_SCRIPT_WITH_JOB"]

LEASE_KIND = "durability pod-timer lease v1"
ACK_KIND = "durability pod-timer acknowledgement v1"
BEAT_KIND = "durability pod-timer heartbeat v1"
VOID_KIND = "durability pod-timer void v1"
LEASE_ID = re.compile(r"(\d{8}T\d{6}Z)-[0-9a-f]{16}")
MAX_HORIZON_SECONDS = 48 * 3600
# the timer asks for the stop within a second of the stop time; the rest is RunPod's latency, not
# yet measured. Two minutes of reserved runway is the assumption until the funded validation.
RECOMMENDED_LATENESS_SECONDS = 120.0
TIMER_SCRIPT = Path(__file__).resolve().parent / "pod_timer" / "pod_timer.py"


@dataclass(frozen=True)
class StopConfirmation:
    """A named person's record that a pod stopped itself through this timer: who, when, and what
    was observed (which pod or image, how the stop was seen, that the hourly spend fell)."""

    confirmed_by: str
    confirmed_utc: str
    statement: str


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _plain(text: object, limit: int = 200) -> str:
    return "".join(ch for ch in str(text) if ch.isprintable())[:limit]


def _publish(path: Path, record: dict) -> bool:
    """Write a record under a new name, never replacing one (as the timer does). True: created."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    with open(tmp, "wb") as handle:
        handle.write((json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    try:
        try:
            os.link(tmp, path)
            return True
        except FileExistsError:
            return False
        except OSError:                 # a mount without hard links
            if path.exists():
                return False
            os.rename(tmp, path)
            return True
    finally:
        if tmp.exists():
            tmp.unlink()


def _read(path: Path) -> dict | None:
    try:
        record = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


class PodTimer:
    """See the module doc. ``state_dir``: the timer's folder on the persistent mount (the pod's
    ``POD_TIMER_DIR``). ``lateness_seconds`` has no default. ``clock`` and ``sleep`` are
    injectable for tests."""

    def __init__(self, state_dir: str | Path, *, lateness_seconds: float,
                 stop_confirmation: StopConfirmation | None = None, ack_seconds: float = 30.0,
                 max_heartbeat_age_seconds: float = 15.0, poll_seconds: float = 0.5, clock: Clock = utc_clock,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        numbers = (lateness_seconds, ack_seconds, max_heartbeat_age_seconds, poll_seconds)
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 for v in numbers):
            raise DurabilityError("the timer's lateness, acknowledgement wait, heartbeat age and poll must be positive numbers")
        if not _text(str(state_dir)) or not Path(state_dir).is_absolute():
            raise DurabilityError("the timer's state folder must be an absolute path on the persistent mount")
        self.state_dir, self.lateness_seconds = Path(state_dir), float(lateness_seconds)
        self.stop_confirmation = stop_confirmation
        self.ack_seconds, self.max_heartbeat_age_seconds = float(ack_seconds), float(max_heartbeat_age_seconds)
        self.poll_seconds, self.clock, self.sleep = float(poll_seconds), clock, sleep

    def __repr__(self) -> str:
        return f"PodTimer({str(self.state_dir)!r}, lateness={self.lateness_seconds:g} s)"

    def describe(self) -> dict:
        return {"kind": "pod-timer", "state_dir": str(self.state_dir), "lateness_seconds": self.lateness_seconds,
                "stop_confirmed": self.stop_confirmation is not None}

    def _confirmation(self) -> StopConfirmation:
        confirmation = self.stop_confirmation
        if confirmation is None:
            raise NotConfigured("no observed self-stop is recorded for this timer (stop_confirmation): that RunPod "
                                "honours a stop asked for from inside the pod is not confirmed")
        if not all(_text(v) for v in (confirmation.confirmed_by, confirmation.statement)):
            raise ProviderError("the stop confirmation names no person or no observation")
        try:
            parse_utc(confirmation.confirmed_utc)
        except ValueError:
            raise ProviderError("the stop confirmation has no usable timestamp") from None
        return confirmation

    def heartbeat(self, pod: str) -> dict:
        """The timer's heartbeat if it shows a timer fit to take a lease for ``pod``; raises otherwise."""
        beat = _read(self.state_dir / "heartbeat.json")
        if beat is None or beat.get("kind") != BEAT_KIND:
            raise ProviderError("no stop timer is running in this pod: there is no heartbeat on the mount")
        try:
            age = (self.clock() - parse_utc(beat.get("utc"))).total_seconds()
        except ValueError:
            raise ProviderError("the stop timer's heartbeat has no usable timestamp") from None
        if not -5.0 <= age <= self.max_heartbeat_age_seconds:
            raise ProviderError(f"the stop timer's heartbeat is stale or from the future ({age:.0f} s old, limit "
                                f"{self.max_heartbeat_age_seconds:g} s): the timer is not running")
        if beat.get("pod") != pod:
            raise ProviderError("the stop timer on this mount belongs to another pod")
        if beat.get("supervised") is not True:
            raise ProviderError("the stop timer is not owned by its supervisor: it was not started by the pod's start "
                                "command, or its supervisor died")
        if beat.get("state") != "armed":
            raise ProviderError("the stop timer is already stopping the pod")
        can = beat.get("can_stop")
        if not (isinstance(can, dict) and can.get("pod_id") is True and (can.get("runpodctl") is True or can.get("key") is True)):
            raise ProviderError("the stop timer has no way to ask for a stop (no pod id, or neither runpodctl nor a key)")
        return beat

    def _void(self, lease: str, reason: str) -> bool:
        try:
            _publish(self.state_dir / "voids" / f"{lease}.json",
                     {"kind": VOID_KIND, "lease": lease, "reason": _plain(reason), "voided_utc": iso(self.clock())})
            return True
        except OSError:
            return False

    def arm(self, worker: str, pod: str, at_utc: str) -> dict:
        """Arm a stop of this pod that is complete by ``at_utc`` (module doc), or raise."""
        self._confirmation()
        if not (_text(worker) and _text(pod)):
            raise NotConfigured("no worker or pod was named for the stop timer")
        now, until = self.clock(), parse_utc(at_utc)
        stop_at = until - dt.timedelta(seconds=self.lateness_seconds)
        if stop_at <= now + dt.timedelta(seconds=self.ack_seconds):
            raise ProviderError("the reservation ends too soon for the stop timer")
        if (stop_at - now).total_seconds() > MAX_HORIZON_SECONDS:
            raise ProviderError(f"the stop timer accepts a stop at most {MAX_HORIZON_SECONDS // 3600} hours ahead")
        before = self.heartbeat(pod)
        lease = f"{now:%Y%m%dT%H%M%SZ}-{secrets.token_hex(8)}"
        record = {"kind": LEASE_KIND, "lease": lease, "worker": worker, "pod": pod, "stop_at_utc": iso(stop_at),
                  "reserved_until_utc": iso(until), "published_utc": iso(now)}
        try:
            if not _publish(self.state_dir / "leases" / f"{lease}.json", record):
                raise ProviderError("the lease record could not be created under a new name")
        except OSError as exc:
            raise ProviderError(f"the lease record could not be written to the mount ({type(exc).__name__})") from None
        try:
            ack, beat = self._acknowledged(lease, record, now)
        except Exception as exc:  # noqa: BLE001 - whatever went wrong, this record must not govern
            voided = self._void(lease, type(exc).__name__)
            why = str(exc) if isinstance(exc, DurabilityError) else type(exc).__name__
            raise ProviderError(f"{why} (lease record {lease} "
                                f"{'withdrawn' if voided else 'COULD NOT BE WITHDRAWN: void it by hand'})") from None
        return {"armed": True, "at_utc": at_utc, "pod": pod, "lease": lease, "stop_at_utc": record["stop_at_utc"],
                "lateness_seconds": self.lateness_seconds,
                "timer": {"pid": beat.get("pid"), "instance": beat.get("instance"), "started_utc": beat.get("started_utc"),
                          "restarted_since_asked": beat.get("instance") != before.get("instance")},
                "acknowledged_utc": ack.get("acknowledged_utc")}

    def _acknowledged(self, lease: str, record: dict, published: dt.datetime) -> tuple[dict, dict]:
        """Wait, bounded, for the acknowledgement of this record and a heartbeat written after it
        that names it as governing with its stop time."""
        deadline = published + dt.timedelta(seconds=self.ack_seconds)
        while True:
            ack = _read(self.state_dir / "acks" / f"{lease}.json")
            if ack is not None:
                if ack.get("kind") != ACK_KIND or any(ack.get(key) != record[key] for key in ("lease", "pod", "stop_at_utc")):
                    raise ProviderError("the stop timer's acknowledgement names another lease, pod or stop time")
                beat = self.heartbeat(record["pod"])
                governing = beat.get("governing")
                if (isinstance(governing, dict) and governing.get("lease") == lease
                        and governing.get("stop_at_utc") == record["stop_at_utc"] and parse_utc(beat["utc"]) >= published):
                    return ack, beat
            if self.clock() >= deadline:
                raise ProviderError("the stop timer did not acknowledge the lease in time: it is not running, or it "
                                    "does not see this folder")
            self.sleep(self.poll_seconds)

    def finish(self, worker: str, pod: str, after_seconds: float = 120.0, reason: str = "the work is complete") -> dict:
        """Ask the timer to stop the pod soon: a record like a lease whose stop time is
        ``after_seconds`` from now, which governs as the most recently issued authority. Shortening
        a deadline needs no admission. Returns once the timer has acknowledged it; raises otherwise
        (the earlier deadline then still stands)."""
        if not (isinstance(after_seconds, (int, float)) and not isinstance(after_seconds, bool) and 5 <= after_seconds <= 3600):
            raise DurabilityError("a finishing stop is asked for between 5 seconds and an hour ahead")
        before = self.heartbeat(pod)
        now = self.clock()
        stop_at = now + dt.timedelta(seconds=after_seconds)
        lease = f"{now:%Y%m%dT%H%M%SZ}-{secrets.token_hex(8)}"
        record = {"kind": LEASE_KIND, "lease": lease, "worker": worker, "pod": pod, "stop_at_utc": iso(stop_at),
                  "reserved_until_utc": iso(stop_at), "published_utc": iso(now), "purpose": "finish",
                  "reason": _plain(reason)}
        try:
            if not _publish(self.state_dir / "leases" / f"{lease}.json", record):
                raise ProviderError("the finishing record could not be created under a new name")
            ack, beat = self._acknowledged(lease, record, now)
        except OSError as exc:
            raise ProviderError(f"the finishing record could not be written to the mount ({type(exc).__name__})") from None
        return {"finishing": True, "pod": pod, "lease": lease, "stop_at_utc": record["stop_at_utc"],
                "acknowledged_utc": ack.get("acknowledged_utc"),
                "timer": {"pid": beat.get("pid"), "instance": beat.get("instance"),
                          "restarted_since_asked": beat.get("instance") != before.get("instance")}}

    def status(self) -> dict:
        """The heartbeat as written, with its age. Reads only."""
        beat = _read(self.state_dir / "heartbeat.json")
        if beat is None:
            return {"running": False, "why": "no heartbeat"}
        try:
            age = (self.clock() - parse_utc(beat.get("utc"))).total_seconds()
        except ValueError:
            return {"running": False, "why": "unreadable heartbeat"}
        keys = ("pod", "pid", "instance", "started_utc", "supervised", "state", "governing", "can_stop")
        return {"running": -5.0 <= age <= self.max_heartbeat_age_seconds, "heartbeat_age_seconds": age,
                **{key: beat.get(key) for key in keys}}


class LayeredShutdown:
    """The stop timer, required, with the GitHub watchdog as a best-effort backup (module doc)."""

    def __init__(self, primary: PodTimer, backup: object | None = None) -> None:
        self.primary, self.backup = primary, backup

    @property
    def lateness_seconds(self) -> float:
        return self.primary.lateness_seconds

    @property
    def state_dir(self) -> Path:
        return self.primary.state_dir

    def describe(self) -> dict:
        return {**self.primary.describe(), "backup": None if self.backup is None else self.backup.describe()}

    def status(self) -> dict:
        return self.primary.status()

    def finish(self, worker: str, pod: str, after_seconds: float = 120.0, reason: str = "the work is complete") -> dict:
        return self.primary.finish(worker, pod, after_seconds, reason)

    def arm(self, worker: str, pod: str, at_utc: str) -> dict:
        armed = self.primary.arm(worker, pod, at_utc)           # required: raises, and admission refuses
        outcome: dict = {"attempted": self.backup is not None}
        if self.backup is not None:
            try:
                backed = self.backup.arm(worker, pod, at_utc)
                outcome.update(armed=True, arm=backed.get("arm"), stop_at_utc=backed.get("stop_at_utc"),
                               run_id=backed.get("run_id"))
            except Exception as exc:  # noqa: BLE001 - the backup is never required
                why = str(exc) if isinstance(exc, DurabilityError) else type(exc).__name__
                outcome.update(armed=False, reason=_plain(why))
                try:                                           # an earlier backup arm must not outlive its lease
                    outcome["earlier_arm_withdrawn"] = self.backup.withdraw_earlier(pod, at_utc)
                except Exception as again:  # noqa: BLE001
                    outcome["earlier_arm_withdrawn"] = None
                    outcome["earlier_arm"] = _plain(f"could not be checked or withdrawn ({type(again).__name__}): the "
                                                    "watchdog may stop this pod at the earlier lease's end")
        try:
            _publish(self.primary.state_dir / "backups" / f"{armed['lease']}.json",
                     {"kind": "durability pod-timer backup outcome v1", "lease": armed["lease"], **outcome})
        except OSError:
            outcome["recorded"] = False
        return {**armed, "backup": outcome}


START_SCRIPT = (
    'set -o pipefail; d="{install}"; f="$d/pod_timer.py"; '
    'mkdir -p "$d" && for v in $(compgen -v POD_TIMER_B64_ | sort); do printf %s "${{!v}}"; done | base64 -d | gunzip > "$f" '
    '&& [ "$(sha256sum < "$f" | cut -c1-64)" = "{sha256}" ] && command -v python3 > /dev/null '
    '&& python3 -I "$f" supervise -- {wrapped}; '
    'echo "pod-timer: the stop timer is not running; stopping this pod"; '
    'while true; do runpodctl pod stop "$RUNPOD_POD_ID" || runpodctl stop pod "$RUNPOD_POD_ID" '
    '|| curl -fsS -o /dev/null -X POST -H "Authorization: Bearer $RUNPOD_API_KEY" '
    '"${{POD_TIMER_REST_URL:-https://rest.runpod.io/v1}}/pods/$RUNPOD_POD_ID/stop"; sleep 30; done')


_STOP_LOOP = START_SCRIPT[START_SCRIPT.index('echo "pod-timer:'):]
# with a job: the timer and the job runner are both unpacked and checked, and the supervisor's
# command is the job runner (which starts the image's own start script itself)
START_SCRIPT_WITH_JOB = (
    'set -o pipefail; d="{install}"; '
    'unpack() {{ for v in $(compgen -v "$1" | sort); do printf %s "${{!v}}"; done | base64 -d | gunzip > "$2" '
    '&& [ "$(sha256sum < "$2" | cut -c1-64)" = "$3" ]; }}; '
    'mkdir -p "$d" && unpack POD_TIMER_B64_ "$d/pod_timer.py" {sha256} && unpack POD_JOB_B64_ "$d/pod_job.py" {job_sha256} '
    '&& command -v python3 > /dev/null && python3 -I "$d/pod_timer.py" supervise -- python3 -I "$d/pod_job.py"; ') + _STOP_LOOP


def _packed(source: bytes, prefix: str, chunk_chars: int) -> dict:
    packed = base64.b64encode(gzip.compress(source, 9, mtime=0)).decode("ascii")
    size = chunk_chars or len(packed)
    chunks = [packed[i:i + size] for i in range(0, len(packed), size)]
    if len(chunks) > 100:
        raise DurabilityError("a script would need more than 100 variables at this chunk size")
    return {f"{prefix}{index:02d}": chunk for index, chunk in enumerate(chunks)}


def settings(*, state_dir: str, cap_seconds: float, clock: Clock = utc_clock, wrapped: str = "/start.sh",
             install_dir: str = "/opt/pod-timer", chunk_chars: int = 0, script: Path = TIMER_SCRIPT,
             job_script: Path | None = None) -> dict:
    """What the operator gives RunPod when creating (or starting again) a pod: ``env`` (the timer
    script, gzip and base64, in one or more ``POD_TIMER_B64_nn`` variables; the state folder; the
    cap, issued now and ``cap_seconds`` long) and the start command, as the array the API takes
    (``docker_start_cmd``) and as the one line the console takes (``console_start_command``). The
    command holds the script's SHA-256, so a variable RunPod cut short is noticed; it stops the pod
    (``runpodctl``, in both spellings, then the REST call with the pod's own key) if the timer
    cannot be started or ever exits.

    With ``job_script`` (the in-pod job runner, ``pod_timer/pod_job.py``) that script travels the
    same way (``POD_JOB_B64_nn``), is checked the same way, and is what the supervisor starts
    instead of ``wrapped``; the job runner starts the image's own start script itself."""
    if not (isinstance(cap_seconds, (int, float)) and not isinstance(cap_seconds, bool) and 0 < cap_seconds <= MAX_HORIZON_SECONDS):
        raise DurabilityError(f"the cap must be between 0 and {MAX_HORIZON_SECONDS // 3600} hours")
    for name, value in (("state folder", state_dir), ("install folder", install_dir), ("start script", wrapped)):
        if not re.fullmatch(r"/[A-Za-z0-9._/-]+", value) or ".." in value:
            raise DurabilityError(f"the {name} must be a plain absolute path")
    if isinstance(chunk_chars, bool) or not isinstance(chunk_chars, int) or chunk_chars < 0:
        raise DurabilityError("chunk_chars must be 0 (one variable) or a positive number of characters")
    source = script.read_bytes()
    packed = base64.b64encode(gzip.compress(source, 9, mtime=0)).decode("ascii")
    size = chunk_chars or len(packed)
    chunks = [packed[i:i + size] for i in range(0, len(packed), size)]
    if len(chunks) > 100:
        raise DurabilityError("the timer script would need more than 100 variables at this chunk size")
    now = clock()
    env = {f"POD_TIMER_B64_{index:02d}": chunk for index, chunk in enumerate(chunks)}
    env.update(POD_TIMER_DIR=state_dir, POD_TIMER_CAP_ISSUED_UTC=iso(now),
               POD_TIMER_CAP_STOP_UTC=iso(now + dt.timedelta(seconds=cap_seconds)))
    sha256 = hashlib.sha256(source).hexdigest()
    job_sha256 = None
    if job_script is None:
        body = START_SCRIPT.format(install=install_dir, sha256=sha256, wrapped=wrapped)
    else:
        job_source = Path(job_script).read_bytes()
        job_sha256 = hashlib.sha256(job_source).hexdigest()
        env.update(_packed(job_source, "POD_JOB_B64_", chunk_chars))
        body = START_SCRIPT_WITH_JOB.format(install=install_dir, sha256=sha256, job_sha256=job_sha256)
    return {"env": env, "docker_start_cmd": ["bash", "-c", body], "console_start_command": f"bash -c '{body}'",
            "script_sha256": sha256, "script_bytes": len(source), "packed_chars": len(packed),
            "cap_stop_utc": env["POD_TIMER_CAP_STOP_UTC"], "job_sha256": job_sha256}
