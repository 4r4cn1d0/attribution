"""The worker's side of the external shutdown watchdog (stdlib only).

**Role since 4 October 2026: a best-effort backup.** The watchdog was built as the required
shutdown; deployed, GitHub ran 3 of its 33 scheduled slots in 16 hours. The required stop is now
the timer inside the pod (``shutdown_timer``), which arms this watchdog afterwards with
``role="backup"`` (class doc) and never depends on it. What follows describes the watchdog as
built, which is also how it behaves when configured as the required shutdown.

RunPod documents no stop time that can be set on, or read back from, an existing pod. The watchdog
runs outside RunPod and outside the worker: a GitHub Actions workflow in the backup repository
(``watchdog/watchdog.py`` and ``watchdog/watchdog.yml`` in this package; the README describes the
deployment). This module is what the worker runs when the watchdog is asked to arm.

``GitHubActionsWatchdog.arm(worker, pod, at_utc)``:

1. publishes an **arm record**, create-only, as a release asset of the backup repository
   (``watchdog-arms-YYYY-MM`` / ``arm-<id>.json``): the worker, its pod, the time the watchdog must
   start stopping the pod (``stop_at_utc = at_utc - lateness_seconds``) and the time by which the
   watchdog must have acknowledged (``ack_by_utc``);
2. sends a ``repository_dispatch`` event naming the arm, which starts one short workflow run;
3. waits for the **acknowledgement** that run writes (``watchdog-acks-YYYY-MM`` /
   ``ack-<id>.json``) and checks it: this arm, this worker and pod, exactly this stop time, a
   workflow run id, written within the window, a scheduled scan seen recently, and a scan
   interval that the configured lateness covers;
4. returns ``{"armed": True, "at_utc": at_utc, ...}`` only then.

A refusal record, no acknowledgement by ``ack_by_utc`` (plus a short grace), or an acknowledgement
that does not match raises ``ProviderError``; admission then grants no lease. Before raising, the
arm is withdrawn with a create-only ``void-<id>.json`` so that an acknowledgement arriving later
cannot make it govern. The watchdog itself never acknowledges after ``ack_by_utc``.

**What "armed" means.** The watchdog's scheduled scan stops the pod at its first scan at or after
``stop_at_utc``. ``lateness_seconds`` is the configured bound on how late that can be (a scan
interval, one dropped scheduled run, GitHub's schedule delay, the stop call itself); the stop is
then complete by ``at_utc``, the end of the reservation. It must cover at least two scan intervals
of the acknowledging watchdog; ``RECOMMENDED_LATENESS_SECONDS`` is three. Admission refuses a
policy whose ``shutdown_delay_seconds`` is smaller than this lateness, so the stop never begins
before the lease has expired and the backup delay has passed. The bound is an assumption about
GitHub's scheduler until the funded validation measures it; it is not enforced by anything.

**Renewal.** A renewed lease publishes a new arm with a later stop time. The watchdog obeys the
latest acknowledged arm of a pod, so the earlier stop time lapses only once the later one is
acknowledged; a renewal that is refused leaves the earlier stop in force.

**Permissions.** The worker's backup token needs nothing new: release assets and
``repository_dispatch`` are both under "Contents: write". The worker never holds a credential
that can stop a pod, and it never talks to RunPod here. The token is read from the environment by
``transport.Http``; nothing in this module logs, stores or raises it.

The record kinds, the id format and the limits below are duplicated in ``watchdog/watchdog.py``,
which must stay self-contained; a test checks that the two agree.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import secrets
import time
import urllib.parse
from typing import Callable

from .common import Clock, DurabilityError, NotConfigured, ProviderError, iso, parse_utc, utc_clock
from .github_destination import GITHUB_TOKEN_ENV
from .transport import Http, next_link

__all__ = ["GitHubActionsWatchdog", "ARM_KIND", "ACK_KIND", "VOID_KIND", "EVENT_ARM", "ARM_ID",
           "MAX_HORIZON_SECONDS", "MAX_ACK_WINDOW_SECONDS", "RECOMMENDED_LATENESS_SECONDS"]

ARM_KIND = "durability watchdog arm v1"
ACK_KIND = "durability watchdog acknowledgement v1"
VOID_KIND = "durability watchdog void v1"
EVENT_ARM = "watchdog-arm"
ARM_ID = re.compile(r"(\d{8}T\d{6}Z)-[0-9a-f]{16}")
MAX_HORIZON_SECONDS = 48 * 3600
MAX_ACK_WINDOW_SECONDS = 1800
# three 30-minute scan intervals: the scan after the stop time is dropped by GitHub, the next one
# starts up to half an hour late, and the stop is confirmed. An assumption until it is measured.
RECOMMENDED_LATENESS_SECONDS = 5400.0
_REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}")
_JSON = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
_BINARY = {"Accept": "application/octet-stream", "X-GitHub-Api-Version": "2022-11-28"}


def _plain(text: object, limit: int = 160) -> str:
    """A watchdog's refusal reason as short printable text (it is data from a record, not trusted)."""
    return "".join(ch for ch in str(text) if ch.isprintable())[:limit]


class GitHubActionsWatchdog:
    """See the module doc. ``lateness_seconds`` has no default: it is a stated assumption
    (``RECOMMENDED_LATENESS_SECONDS`` with the 30-minute scan). ``ack_window_seconds``: how long
    the watchdog has to acknowledge. ``sleep`` and ``clock`` are injectable for tests.

    ``role="backup"`` (``lateness_seconds`` omitted): the watchdog stands behind the pod's own stop
    timer (``shutdown_timer``). Its stop time is then ``at_utc`` itself, it promises no punctuality
    and none is checked, and its acknowledgement needs no recent scheduled scan. Admission never
    depends on a backup."""

    def __init__(self, repository: str, *, lateness_seconds: float | None = None, role: str = "primary",
                 ack_window_seconds: float = 600.0,
                 poll_seconds: float = 10.0, grace_seconds: float = 60.0, token_env: str = GITHUB_TOKEN_ENV,
                 api_url: str = "https://api.github.com", upload_url: str = "https://uploads.github.com",
                 clock: Clock = utc_clock, sleep: Callable[[float], None] = time.sleep, max_retries: int = 4,
                 max_wait_seconds: float = 120.0) -> None:
        if not isinstance(repository, str) or not _REPOSITORY.fullmatch(repository):
            raise DurabilityError("the watchdog's repository must be given as owner/name")
        if role not in ("primary", "backup"):
            raise DurabilityError("the watchdog's role is primary or backup")
        if role == "backup":
            if lateness_seconds is not None:
                raise DurabilityError("a backup watchdog states no lateness: it stops at the end of the reservation, "
                                      "whenever GitHub next runs its scan")
            lateness_seconds = 0.0
        numbers = (ack_window_seconds, poll_seconds, grace_seconds) + (() if role == "backup" else (lateness_seconds,))
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 for v in numbers):
            raise DurabilityError("the watchdog's lateness, acknowledgement window, poll and grace must be positive numbers")
        if ack_window_seconds > MAX_ACK_WINDOW_SECONDS:
            raise DurabilityError(f"the watchdog acknowledges within at most {MAX_ACK_WINDOW_SECONDS} s")
        self.role = role
        self.repository, self.lateness_seconds = repository, float(lateness_seconds)
        self.ack_window_seconds, self.poll_seconds, self.grace_seconds = float(ack_window_seconds), float(poll_seconds), float(grace_seconds)
        self.clock, self.sleep = clock, sleep
        self.api, self.uploads = api_url.rstrip("/"), upload_url.rstrip("/")
        self.http = Http(token_env=token_env, bases=(self.api, self.uploads), max_retries=max_retries,
                         max_wait_seconds=max_wait_seconds, sleep=sleep)
        self._releases: dict[str, dict] = {}

    def __repr__(self) -> str:
        return f"GitHubActionsWatchdog({self.repository!r}, lateness={self.lateness_seconds:g} s)"

    def describe(self) -> dict:
        described = {"kind": "github-actions-watchdog", "repository": self.repository,
                     "lateness_seconds": self.lateness_seconds, "ack_window_seconds": self.ack_window_seconds}
        return described if self.role == "primary" else {**described, "role": "backup", "lateness_seconds": None}

    # ----- records (release assets, create-only) -------------------------------------

    def _repo(self, path: str) -> str:
        return f"{self.api}/repos/{self.repository}{path}"

    def _release(self, tag: str, create: bool) -> dict | None:
        if tag in self._releases:
            return self._releases[tag]
        reply = self.http.request("GET", self._repo(f"/releases/tags/{tag}"), headers=_JSON)
        if reply.status == 404 and create:
            made = self.http.request("POST", self._repo("/releases"), headers=_JSON, body=json.dumps({
                "tag_name": tag, "name": tag, "prerelease": True,
                "body": "Shutdown-watchdog records. Create-only; do not edit or delete."}).encode("utf-8"))
            if made.status not in (201, 422):
                raise ProviderError(f"GitHub answered {made.status} to creating the release {tag}")
            reply = made if made.status == 201 else self.http.request(
                "GET", self._repo(f"/releases/tags/{tag}"), headers=_JSON)
        if reply.status == 404:
            return None
        release = reply.json() if reply.status in (200, 201) else None
        if not isinstance(release, dict) or not isinstance(release.get("id"), int) or release.get("tag_name") != tag:
            raise ProviderError(f"GitHub answered {reply.status} for the release {tag}, or in an unexpected shape")
        self._releases[tag] = release
        return release

    def _names(self, tag: str) -> dict[str, dict]:
        """The uploaded assets of a release by name (read afresh at every call)."""
        release = self._release(tag, create=False)
        if release is None:
            return {}
        found: dict[str, dict] = {}
        url = self._repo(f"/releases/{release['id']}/assets?per_page=100")
        while url:
            reply = self.http.request("GET", url, headers=_JSON)
            page = reply.json() if reply.status == 200 else None
            if not isinstance(page, list):
                raise ProviderError(f"GitHub answered {reply.status} to a listing of watchdog records")
            for asset in page:
                if (isinstance(asset, dict) and asset.get("state") == "uploaded" and isinstance(asset.get("name"), str)
                        and isinstance(asset.get("id"), int)):
                    found[asset["name"]] = asset
            url = next_link(reply.headers)
        return found

    def _read(self, asset: dict) -> dict:
        reply = self.http.request("GET", self._repo(f"/releases/assets/{asset['id']}"), headers=_BINARY)
        record = reply.json() if reply.status == 200 else None
        if not isinstance(record, dict):
            raise ProviderError(f"GitHub answered {reply.status} to a watchdog record download, or it is not a record")
        return record

    def _create(self, tag: str, name: str, record: dict) -> bool:
        """True: created. False: the name exists (nothing is ever replaced)."""
        release = self._release(tag, create=True)
        url = (f"{self.uploads}/repos/{self.repository}/releases/{release['id']}/assets?"
               + urllib.parse.urlencode({"name": name}))
        body = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
        reply = self.http.request("POST", url, headers={**_JSON, "Content-Type": "application/json"}, body=body)
        if reply.status == 201:
            return True
        if reply.status == 422:
            return False
        raise ProviderError(f"GitHub answered {reply.status} to a watchdog record upload")

    # ----- arming --------------------------------------------------------------------

    def _void(self, arm_id: str, month: str, reason: str) -> bool:
        try:
            self._create(f"watchdog-arms-{month}", f"void-{arm_id}.json",
                         {"kind": VOID_KIND, "arm": arm_id, "reason": _plain(reason), "voided_utc": iso(self.clock())})
            return True
        except Exception:  # noqa: BLE001 - reported to the caller, which is already refusing
            return False

    def _acknowledgement(self, arm_id: str, month: str, deadline: dt.datetime) -> dict:
        """Poll until the watchdog's acknowledgement or refusal of this arm appears, or the deadline."""
        tag = f"watchdog-acks-{month}"
        while True:
            names = self._names(tag)
            if f"refusal-{arm_id}.json" in names:
                reason = self._read(names[f"refusal-{arm_id}.json"]).get("reason")
                raise ProviderError(f"the watchdog refused the arm: {_plain(reason)}")
            if f"ack-{arm_id}.json" in names:
                return self._read(names[f"ack-{arm_id}.json"])
            if self.clock() >= deadline:
                raise ProviderError("the watchdog did not acknowledge the arm in time: it is not running, not "
                                    "enabled, or too slow to count on")
            self.sleep(self.poll_seconds)

    def _check(self, ack: dict, record: dict, ack_by: dt.datetime) -> None:
        if ack.get("kind") != ACK_KIND or any(ack.get(key) != record[key] for key in ("arm", "worker", "pod", "stop_at_utc")):
            raise ProviderError("the watchdog's acknowledgement names another arm, worker, pod or stop time")
        if not (isinstance(ack.get("run_id"), str) and ack["run_id"].strip()):
            raise ProviderError("the watchdog's acknowledgement names no workflow run")
        try:
            acknowledged = parse_utc(ack.get("acknowledged_utc"))
        except ValueError:
            raise ProviderError("the watchdog's acknowledgement has no usable timestamps") from None
        if acknowledged > ack_by + dt.timedelta(seconds=self.grace_seconds):
            raise ProviderError("the watchdog's acknowledgement was written after its window")
        if self.role == "backup":           # no punctuality is promised, so no scan interval or recent scan is required
            return
        interval = ack.get("scan_interval_seconds")
        if not isinstance(interval, (int, float)) or isinstance(interval, bool) or interval <= 0:
            raise ProviderError("the watchdog's acknowledgement states no scan interval")
        if self.lateness_seconds < 2 * interval:
            raise ProviderError(f"the configured lateness ({self.lateness_seconds:g} s) does not cover two scan "
                                f"intervals of the watchdog ({interval:g} s each)")
        try:
            last_scan = parse_utc(ack.get("last_scheduled_scan_utc"))
        except ValueError:
            raise ProviderError("the watchdog's acknowledgement has no usable timestamps") from None
        if (acknowledged - last_scan).total_seconds() > 2 * interval + 900:
            raise ProviderError("the watchdog acknowledged without a recent scheduled scan")

    def arm(self, worker: str, pod: str, at_utc: str) -> dict:
        """Arm a stop of ``pod`` that is complete by ``at_utc`` (module doc), or raise."""
        self.http.require_token()
        if not all(isinstance(v, str) and v.strip() for v in (worker, pod)):
            raise NotConfigured("no worker or pod was named for the watchdog")
        now, until = self.clock(), parse_utc(at_utc)
        stop_at = until - dt.timedelta(seconds=self.lateness_seconds)
        ack_by = now + dt.timedelta(seconds=self.ack_window_seconds)
        if stop_at <= ack_by + dt.timedelta(seconds=self.grace_seconds):
            raise ProviderError("the reservation ends too soon for the watchdog: its stop time would fall inside "
                                "the acknowledgement window")
        if (stop_at - now).total_seconds() > MAX_HORIZON_SECONDS:
            raise ProviderError(f"the watchdog accepts a stop at most {MAX_HORIZON_SECONDS // 3600} hours ahead")
        arm_id, month = f"{now:%Y%m%dT%H%M%SZ}-{secrets.token_hex(8)}", f"{now:%Y-%m}"
        record = {"kind": ARM_KIND, "arm": arm_id, "worker": worker, "pod": pod, "stop_at_utc": iso(stop_at),
                  "reserved_until_utc": iso(until), "published_utc": iso(now), "ack_by_utc": iso(ack_by)}
        if self.role == "backup":
            record["role"] = "backup"
        if not self._create(f"watchdog-arms-{month}", f"arm-{arm_id}.json", record):
            raise ProviderError("the arm record could not be created under a new name")
        try:
            reply = self.http.request("POST", self._repo("/dispatches"), headers={**_JSON, "Content-Type": "application/json"},
                                      body=json.dumps({"event_type": EVENT_ARM, "client_payload": {"arm": arm_id}}).encode("utf-8"))
            if reply.status not in (200, 201, 202, 204):
                raise ProviderError(f"GitHub answered {reply.status} to the watchdog dispatch")
            ack = self._acknowledgement(arm_id, month, ack_by + dt.timedelta(seconds=self.grace_seconds))
            self._check(ack, record, ack_by)
        except Exception as exc:  # noqa: BLE001 - whatever went wrong, this arm must not govern
            voided = self._void(arm_id, month, type(exc).__name__)
            why = str(exc) if isinstance(exc, DurabilityError) else type(exc).__name__
            raise ProviderError(f"{why} (arm {arm_id} "
                                f"{'withdrawn' if voided else 'COULD NOT BE WITHDRAWN: void it by hand'})") from None
        return {"armed": True, "at_utc": at_utc, "arm": arm_id, "pod": pod, "stop_at_utc": record["stop_at_utc"],
                "run_id": ack["run_id"], "lateness_seconds": self.lateness_seconds}

    def withdraw_earlier(self, pod: str, at_utc: str) -> list[str]:
        """Withdraw every arm of the pod that would stop it before ``at_utc`` (a renewed lease whose
        own backup arm could not be made). Withdrawing the governing arm lets the one before it
        govern again, so this repeats until none is left. Returns the withdrawn ids. Raises when
        the records cannot be read or a void cannot be written."""
        withdrawn: list[str] = []
        for _ in range(50):
            current = self.status(pod)
            if not current.get("armed") or parse_utc(current.get("stop_at_utc")) >= parse_utc(at_utc):
                return withdrawn
            arm_id = current["arm"]
            if not self._create(f"watchdog-arms-{arm_id[:4]}-{arm_id[4:6]}", f"void-{arm_id}.json",
                                {"kind": VOID_KIND, "arm": arm_id, "reason": "its lease was renewed without a backup arm",
                                 "voided_utc": iso(self.clock())}):
                raise ProviderError("an earlier arm's withdrawal already exists")
            withdrawn.append(arm_id)
        raise ProviderError("too many earlier arms to withdraw")

    # ----- read-only status ----------------------------------------------------------

    def status(self, pod: str) -> dict:
        """What the records say about a pod: its latest acknowledged, not withdrawn arm and whether a
        stop was recorded for it. Reads only. (Whether the scheduled scan is running is shown by
        the repository's Actions tab; the worker's token cannot read workflow runs.)"""
        self.http.require_token()
        now = self.clock()
        months = [(now.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m"), now.strftime("%Y-%m")]
        arms, acks = {}, {}
        for month in months:
            arms.update(self._names(f"watchdog-arms-{month}"))
            acks.update(self._names(f"watchdog-acks-{month}"))
        ids = sorted((n[4:-5] for n in arms if n.startswith("arm-") and n.endswith(".json") and ARM_ID.fullmatch(n[4:-5])),
                     reverse=True)
        for arm_id in ids:
            if f"ack-{arm_id}.json" not in acks or f"void-{arm_id}.json" in arms:
                continue
            record = self._read(arms[f"arm-{arm_id}.json"])
            if record.get("pod") != pod:
                continue
            ack = self._read(acks[f"ack-{arm_id}.json"])
            stops = self._names(f"watchdog-stops-{arm_id[:4]}-{arm_id[4:6]}")
            stop = self._read(stops[f"stop-{arm_id}.json"]) if f"stop-{arm_id}.json" in stops else None
            return {"armed": stop is None, "arm": arm_id, "stop_at_utc": record.get("stop_at_utc"),
                    "acknowledged_by_run": ack.get("run_id"), "acknowledged_utc": ack.get("acknowledged_utc"),
                    "stop": None if stop is None else {key: stop.get(key) for key in ("result", "recorded_utc")}}
        return {"armed": False, "arm": None}
