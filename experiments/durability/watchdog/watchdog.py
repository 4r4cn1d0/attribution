#!/usr/bin/env python3
"""Shutdown watchdog for leased GPU pods (self-contained; Python standard library only).

This file is deployed to the backup repository as ``watchdog/watchdog.py`` and run by the
``watchdog`` GitHub Actions workflow. It imports nothing from the research project.

What it does, and nothing else:

- **arm** (one run per lease, started by a ``repository_dispatch`` event that names an arm id):
  read the worker's arm record, refuse it unless it is well formed, names an allow-listed
  worker and its pod, is still within its acknowledgement window, the pod answers as RUNNING
  with this workflow's RunPod key, and a scheduled scan ran recently; then write the
  acknowledgement, create-only. The worker treats its shutdown as armed only when it reads that
  acknowledgement. An arm whose record says ``"role": "backup"`` is acknowledged without the
  recent scheduled scan: it promises no punctuality (the pod's own timer is the primary stop),
  only that the first scan at or after the stop time, whenever GitHub runs it, stops the pod if
  it is still running.
- **scan** (the schedule): for every allow-listed pod find the *governing* arm: the latest one
  that was acknowledged and not withdrawn. At or after its ``stop_at_utc`` the pod is **stopped**
  (never terminated or deleted) through ``POST /pods/{id}/stop``, the result is confirmed with a
  ``GET`` and recorded, create-only. An earlier arm never stops a pod while a later acknowledged
  one governs. A stop is therefore up to one scan interval late (more if GitHub delays or drops a
  scheduled run); the worker's reservation covers that lateness. Optionally
  (``WATCHDOG_TAIL_SECONDS``, 0 by default) a stop time that falls within that many seconds is
  waited for inside the run; the governing arm is then looked up again before the stop, so a
  renewal that arrived meanwhile wins. Every waited minute is a billed Actions minute.

Records are release assets of this repository, one release per kind and month, all create-only:

    watchdog-arms-YYYY-MM   arm-<id>.json (worker), void-<id>.json (worker, withdraws an arm)
    watchdog-acks-YYYY-MM   ack-<id>.json, refusal-<id>.json (this script)
    watchdog-stops-YYYY-MM  stop-<id>.json (final), stop-attempt-<id>-<run>.json (this script)

It never deletes or renames anything, on GitHub or on RunPod, and it stops only a pod that the
allow-list (``watchdog/pods.json``) and a valid governing arm both name. Secrets come from the
environment (``GITHUB_TOKEN``, ``RUNPOD_API_KEY``), go only into ``Authorization`` headers for
their own service, are never forwarded on a redirect and are never printed.

**The RunPod key is needed only when there is a pod to watch.** With an empty allow-list a scan
succeeds without it and sends nothing to RunPod, so the workflow can be deployed before the secret
exists. With a pod on the allow-list and no key the scan fails, loudly: a watchdog that could not
stop the pod it guards must be visible. An arm is never acknowledged without the key.

**What the workflow must do around this file.** Whoever can push to the repository can change
this file and the allow-list, but not the workflow (that needs GitHub's "Workflows" permission).
The workflow therefore pins the SHA-256 of both files and checks them in a step that has no secret
in its environment, before this script starts; and it runs the script with ``python3 -I``, so that
a module placed next to it (a ``json.py``, say) is not imported in place of the standard library.
Without both, the RunPod key would be exposed to whatever the repository holds.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ARM_KIND = "durability watchdog arm v1"
ACK_KIND = "durability watchdog acknowledgement v1"
STOP_KIND = "durability watchdog stop v1"
ARM_ID = re.compile(r"(\d{8}T\d{6}Z)-[0-9a-f]{16}")
STOPPED = ("EXITED", "TERMINATED")
MAX_HORIZON_SECONDS = 48 * 3600          # an arm never asks for a stop further away than this
MAX_ACK_WINDOW_SECONDS = 1800
EVENT_ARM = "watchdog-arm"


class Refused(Exception):
    """An arm is not acknowledged, or a step could not be completed. The message is a short
    reason code plus plain detail; it never holds a header or a secret."""


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


def month_of(arm_id: str) -> str:
    return f"{arm_id[:4]}-{arm_id[4:6]}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102 - urllib hook
        return None


class Http:
    """Requests with a bearer token for one service. Redirects are followed by hand, at most
    three times, without the token. Non-HTTPS addresses are refused except on a loopback host."""

    def __init__(self, base: str, token: str, sleep=time.sleep, retries: int = 3) -> None:
        self.base, self._token, self.sleep, self.retries = base.rstrip("/"), token, sleep, retries
        self._opener = urllib.request.build_opener(_NoRedirect())
        parts = urllib.parse.urlsplit(self.base)
        if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost")):
            raise Refused("configuration: a service address is not HTTPS")

    def request(self, method: str, url: str, body: bytes | None = None, headers: dict | None = None) -> tuple[int, dict, bytes]:
        """(status, lower-cased headers, body). Connection errors and 5xx answers are retried a
        few times; every other answer is returned for the caller to judge."""
        if not url.startswith("http"):
            url = self.base + url
        authorized, hops, attempt = True, 0, 0
        while True:
            parts = urllib.parse.urlsplit(url)
            if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost")):
                raise Refused("transport: refusing a non-HTTPS address")
            request = urllib.request.Request(url, data=body, method=method)
            request.add_header("User-Agent", "durability-watchdog")
            for name, value in (headers or {}).items():
                request.add_header(name, value)
            if authorized and (url == self.base or url.startswith(self.base + "/")):
                request.add_header("Authorization", f"Bearer {self._token}")
            try:
                with self._opener.open(request, timeout=60) as response:
                    return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
            except urllib.error.HTTPError as exc:
                status, reply, payload = exc.code, {k.lower(): v for k, v in (exc.headers or {}).items()}, exc.read()
            except (urllib.error.URLError, OSError) as exc:
                attempt += 1
                if attempt > self.retries:
                    raise Refused(f"transport: {method} {parts.netloc}{parts.path} failed ({type(exc).__name__})") from None
                self.sleep(2.0 * attempt)
                continue
            if status in (301, 302, 303, 307, 308) and reply.get("location"):
                hops += 1
                if hops > 3:
                    raise Refused("transport: too many redirects")
                url, authorized = urllib.parse.urljoin(url, reply["location"]), False
                continue
            if status >= 500:
                attempt += 1
                if attempt > self.retries:
                    return status, reply, payload
                self.sleep(2.0 * attempt)
                continue
            return status, reply, payload


def _json(payload: bytes):
    try:
        return json.loads(payload)
    except ValueError:
        raise Refused("transport: an answer was not JSON") from None


class Records:
    """Create-only records as release assets of the repository (module doc)."""

    def __init__(self, http: Http, uploads: Http, repository: str) -> None:
        self.http, self.uploads, self.repository = http, uploads, repository
        self._releases: dict[str, dict | None] = {}

    def _repo(self, path: str) -> str:
        return f"/repos/{self.repository}{path}"

    def release(self, tag: str, create: bool) -> dict | None:
        if self._releases.get(tag):
            return self._releases[tag]
        status, _, payload = self.http.request("GET", self._repo(f"/releases/tags/{tag}"), headers={"Accept": "application/vnd.github+json"})
        if status == 404 and create:
            body = json.dumps({"tag_name": tag, "name": tag, "prerelease": True,
                               "body": "Shutdown-watchdog records. Create-only; do not edit or delete."}).encode()
            status, _, payload = self.http.request("POST", self._repo("/releases"), body, {"Accept": "application/vnd.github+json"})
            if status == 422:   # created by the other side meanwhile
                status, _, payload = self.http.request("GET", self._repo(f"/releases/tags/{tag}"), headers={"Accept": "application/vnd.github+json"})
        if status == 404:
            return None
        if status not in (200, 201):
            raise Refused(f"records: GitHub answered {status} for the release {tag}")
        release = _json(payload)
        if not isinstance(release, dict) or not isinstance(release.get("id"), int):
            raise Refused("records: a release has an unexpected shape")
        self._releases[tag] = release
        return release

    def names(self, tag: str) -> dict[str, dict]:
        """Uploaded assets of a release by name (an unfinished upload is not a record)."""
        release = self.release(tag, create=False)
        if release is None:
            return {}
        found, url = {}, self._repo(f"/releases/{release['id']}/assets?per_page=100")
        while url:
            status, headers, payload = self.http.request("GET", url, headers={"Accept": "application/vnd.github+json"})
            page = _json(payload) if status == 200 else None
            if not isinstance(page, list):
                raise Refused(f"records: GitHub answered {status} to an asset listing")
            for asset in page:
                if isinstance(asset, dict) and asset.get("state") == "uploaded" and isinstance(asset.get("name"), str):
                    found[asset["name"]] = asset
            url = next((part.split(";")[0].strip().strip("<>") for part in headers.get("link", "").split(",")
                        if 'rel="next"' in part), None)
        return found

    def read(self, asset: dict) -> dict:
        status, _, payload = self.http.request("GET", self._repo(f"/releases/assets/{asset['id']}"),
                                               headers={"Accept": "application/octet-stream"})
        if status != 200:
            raise Refused(f"records: GitHub answered {status} to a record download")
        record = _json(payload)
        if not isinstance(record, dict):
            raise Refused("records: a record is not a JSON object")
        return record

    def create(self, tag: str, name: str, record: dict) -> bool:
        """Write a record create-only. True: created. False: the name already exists (kept)."""
        release = self.release(tag, create=True)
        body = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
        path = f"/repos/{self.repository}/releases/{release['id']}/assets?" + urllib.parse.urlencode({"name": name})
        status, _, _ = self.uploads.request("POST", path, body, {"Content-Type": "application/json",
                                                                 "Accept": "application/vnd.github+json"})
        if status == 201:
            return True
        if status == 422:
            return False
        raise Refused(f"records: GitHub answered {status} to a record upload")


def load_pods(path: str) -> dict[str, str]:
    """The allow-list: worker name -> pod id. Anything else refuses."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        raise Refused("configuration: the pod allow-list is missing or unreadable") from None
    workers = data.get("workers") if isinstance(data, dict) else None
    if not isinstance(workers, dict) or not all(isinstance(k, str) and k and isinstance(v, str) and v for k, v in workers.items()):
        raise Refused("configuration: the pod allow-list is malformed")
    if len(set(workers.values())) != len(workers):
        raise Refused("configuration: two workers name one pod")
    return dict(workers)


def valid_arm(record: object, arm_id: str, pods: dict[str, str]) -> dict:
    """The arm record if it is well formed and names an allow-listed worker with its pod; raises
    ``Refused`` with the reason otherwise."""
    if not isinstance(record, dict) or record.get("kind") != ARM_KIND or record.get("arm") != arm_id:
        raise Refused("malformed: not this arm's record")
    if not ARM_ID.fullmatch(arm_id):
        raise Refused("malformed: arm id")
    worker, pod = record.get("worker"), record.get("pod")
    if not (isinstance(worker, str) and isinstance(pod, str) and worker and pod):
        raise Refused("malformed: worker or pod")
    if pods.get(worker) != pod:
        raise Refused("not-a-worker: the allow-list does not name this worker with this pod")
    try:
        published, stop_at, ack_by = (parse_utc(record.get(key)) for key in ("published_utc", "stop_at_utc", "ack_by_utc"))
        reserved_until = parse_utc(record.get("reserved_until_utc"))
    except ValueError:
        raise Refused("malformed: timestamps") from None
    if published.strftime("%Y%m%dT%H%M%SZ") != arm_id[:16]:
        raise Refused("malformed: the arm id does not carry its publication time")
    if not (published <= stop_at <= reserved_until) or (stop_at - published).total_seconds() > MAX_HORIZON_SECONDS:
        raise Refused("malformed: the stop time is before publication, after the reservation or too far away")
    if not 0 < (ack_by - published).total_seconds() <= MAX_ACK_WINDOW_SECONDS:
        raise Refused("malformed: acknowledgement window")
    role = record.get("role", "primary")
    if role not in ("primary", "backup"):
        raise Refused("malformed: role")
    return {"arm": arm_id, "worker": worker, "pod": pod, "published": published, "stop_at": stop_at, "ack_by": ack_by,
            "reserved_until": reserved_until, "role": role}


class Watchdog:
    def __init__(self, env: dict, clock=utc_now, sleep=time.sleep, out=print) -> None:
        for name in ("GITHUB_TOKEN", "GITHUB_REPOSITORY"):
            if not env.get(name, "").strip():
                raise Refused(f"configuration: {name} is not set")
        self.clock, self.sleep, self.out = clock, sleep, out
        self.repository = env["GITHUB_REPOSITORY"]
        self.api = env.get("GITHUB_API_URL", "https://api.github.com")
        self.github = Http(self.api, env["GITHUB_TOKEN"].strip(), sleep)
        uploads = Http(env.get("WATCHDOG_UPLOAD_URL", "https://uploads.github.com"), env["GITHUB_TOKEN"].strip(), sleep)
        key = env.get("RUNPOD_API_KEY", "").strip()      # needed only when there is a pod to watch (module doc)
        self._runpod = Http(env.get("WATCHDOG_RUNPOD_URL", "https://rest.runpod.io/v1"), key, sleep) if key else None
        self.records = Records(self.github, uploads, self.repository)
        self.pods = load_pods(env.get("WATCHDOG_PODS", "watchdog/pods.json"))
        try:
            self.interval = float(env.get("WATCHDOG_INTERVAL_SECONDS") or "1800")
            self.tail = float(env.get("WATCHDOG_TAIL_SECONDS") or "0")
        except ValueError:
            raise Refused("configuration: the scan interval or the tail is not a number") from None
        if not (60 <= self.interval <= 3600 and 0 <= self.tail <= 2400):
            raise Refused("configuration: the scan interval or the tail is out of range")
        self.workflow = env.get("WATCHDOG_WORKFLOW", "watchdog.yml")
        self.run = {"run_id": env.get("GITHUB_RUN_ID", ""), "run_attempt": env.get("GITHUB_RUN_ATTEMPT", ""),
                    "event": env.get("GITHUB_EVENT_NAME", "")}

    def log(self, event: str, **fields: object) -> None:
        self.out(json.dumps({"event": event, "utc": iso(self.clock()), **fields}, sort_keys=True))

    # ----- RunPod: read a pod, stop a pod; nothing else --------------------------------

    @property
    def runpod(self) -> Http:
        if self._runpod is None:
            raise Refused("configuration: RUNPOD_API_KEY is not set")
        return self._runpod

    def pod_status(self, pod: str) -> str | None:
        """The pod's ``desiredStatus``; None when RunPod says there is no such pod."""
        status, _, payload = self.runpod.request("GET", f"/pods/{urllib.parse.quote(pod, safe='')}", headers={"Accept": "application/json"})
        if status == 404:
            return None
        if status in (401, 403):
            raise Refused("runpod: the key was rejected")
        data = _json(payload) if status == 200 else None
        if not isinstance(data, dict) or data.get("id") != pod or not isinstance(data.get("desiredStatus"), str):
            raise Refused(f"runpod: unexpected answer ({status}) to a pod read")
        return data["desiredStatus"]

    def stop_pod(self, pod: str) -> int:
        status, _, _ = self.runpod.request("POST", f"/pods/{urllib.parse.quote(pod, safe='')}/stop", b"", {"Accept": "application/json"})
        return status

    # ----- arm ---------------------------------------------------------------------------

    def _last_scheduled_scan(self) -> dt.datetime | None:
        status, _, payload = self.github.request(
            "GET", f"/repos/{self.repository}/actions/workflows/{self.workflow}/runs?event=schedule&per_page=1",
            headers={"Accept": "application/vnd.github+json"})
        data = _json(payload) if status == 200 else None
        runs = data.get("workflow_runs") if isinstance(data, dict) else None
        if not isinstance(runs, list):
            raise Refused(f"liveness: GitHub answered {status} to the scheduled-run query")
        try:
            return parse_utc(runs[0]["created_at"].replace("Z", "+00:00")) if runs else None
        except (KeyError, ValueError, AttributeError, TypeError):
            raise Refused("liveness: a workflow run has no usable creation time") from None

    def arm(self, arm_id: str) -> dict:
        """Acknowledge one arm or refuse it (module doc). A refusal is recorded, create-only, so
        the worker can stop waiting; it never becomes an acknowledgement later."""
        try:
            if not ARM_ID.fullmatch(arm_id or ""):
                raise Refused("malformed: arm id")
            month = month_of(arm_id)
            arms = self.records.names(f"watchdog-arms-{month}")
            if f"arm-{arm_id}.json" not in arms:
                raise Refused("missing: no such arm record")
            if f"refusal-{arm_id}.json" in self.records.names(f"watchdog-acks-{month}"):
                raise Refused("duplicate: this arm was refused before, and a refusal is final")
            arm = valid_arm(self.records.read(arms[f"arm-{arm_id}.json"]), arm_id, self.pods)
            if f"void-{arm_id}.json" in arms:
                raise Refused("withdrawn: the worker withdrew this arm")
            now = self.clock()
            if now > arm["ack_by"]:
                raise Refused("late: the acknowledgement window has passed")
            if arm["stop_at"] <= now:
                raise Refused("late: the stop time has passed")
            if self.pod_status(arm["pod"]) != "RUNNING":
                raise Refused("pod: RunPod does not report this pod as RUNNING")
            if arm["role"] == "backup":             # no punctuality is promised, so none is required
                try:
                    last = self._last_scheduled_scan()
                except Refused:
                    last = None
                statement = ("backup: the first scheduled scan of this workflow at or after stop_at_utc, whenever "
                             "GitHub runs it, stops this pod if it is still running, unless a later acknowledged "
                             "arm for the same pod governs")
            else:
                last = self._last_scheduled_scan()
                if last is None or (now - last).total_seconds() > 2 * self.interval + 900:
                    raise Refused("liveness: no scheduled scan ran recently; the watchdog would not be watching")
                statement = ("the scheduled scan of this workflow stops this pod at stop_at_utc unless a later "
                             "acknowledged arm for the same pod governs")
            ack = {"kind": ACK_KIND, "arm": arm_id, "worker": arm["worker"], "pod": arm["pod"], "role": arm["role"],
                   "stop_at_utc": iso(arm["stop_at"]), "acknowledged_utc": iso(self.clock()), **self.run,
                   "last_scheduled_scan_utc": None if last is None else iso(last),
                   "scan_interval_seconds": self.interval, "statement": statement}
            if not self.records.create(f"watchdog-acks-{month}", f"ack-{arm_id}.json", ack):
                raise Refused("duplicate: this arm was already acknowledged")
            self.log("arm-acknowledged", arm=arm_id, pod=arm["pod"], stop_at_utc=ack["stop_at_utc"])
            return ack
        except Refused as exc:
            reason = str(exc)
            self.log("arm-refused", arm=arm_id if ARM_ID.fullmatch(arm_id or "") else "(malformed)", reason=reason)
            if ARM_ID.fullmatch(arm_id or "") and not reason.startswith("duplicate"):
                try:
                    self.records.create(f"watchdog-acks-{month_of(arm_id)}", f"refusal-{arm_id}.json",
                                        {"kind": "durability watchdog refusal v1", "arm": arm_id, "reason": reason,
                                         "refused_utc": iso(self.clock()), **self.run})
                except Refused:
                    pass
            raise

    # ----- scan --------------------------------------------------------------------------

    def _months(self) -> list[str]:
        """This month and the one before: an arm is filed under the month it was published in and
        stops at most ``MAX_HORIZON_SECONDS`` later, and a stop that keeps failing is retried."""
        now = self.clock()
        return [(now.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m"), now.strftime("%Y-%m")]

    def governing(self) -> dict[str, dict]:
        """Per allow-listed pod, its governing arm: the latest (by arm id, which starts with the
        publication time) that is valid, acknowledged and not withdrawn. Malformed records, arms
        without an acknowledgement and arms of pods outside the allow-list govern nothing."""
        arms, acks = {}, set()
        for month in self._months():
            arms.update(self.records.names(f"watchdog-arms-{month}"))
            acks.update(self.records.names(f"watchdog-acks-{month}"))
        found: dict[str, dict] = {}
        ids = sorted((name[4:-5] for name in arms if name.startswith("arm-") and name.endswith(".json")), reverse=True)
        for arm_id in ids:
            if f"ack-{arm_id}.json" not in acks or f"void-{arm_id}.json" in arms:
                continue
            try:
                arm = valid_arm(self.records.read(arms[f"arm-{arm_id}.json"]), arm_id, self.pods)
            except Refused as exc:
                self.log("arm-ignored", arm=arm_id, reason=str(exc))
                continue
            found.setdefault(arm["pod"], arm)
            if len(found) == len(self.pods):
                break
        return found

    def _stopped_already(self, arm_id: str) -> bool:
        return f"stop-{arm_id}.json" in self.records.names(f"watchdog-stops-{month_of(arm_id)}")

    def stop(self, arm: dict) -> dict:
        """Stop the arm's pod, confirm it and record the outcome. Final outcomes (stopped,
        already-stopped, gone) are written once; anything else is recorded as an attempt and the
        next scan tries again."""
        pod, arm_id = arm["pod"], arm["arm"]
        outcome = {"kind": STOP_KIND, "arm": arm_id, "pod": pod, "stop_at_utc": iso(arm["stop_at"]), **self.run}

        def status() -> str | None:
            try:
                return self.pod_status(pod)
            except Refused:
                return "unknown"        # the state could not be read: the stop is still asked for

        before = status()
        if before is None:
            outcome.update(result="gone", status_before=None, status_after=None)
        elif before in STOPPED:
            outcome.update(result="already-stopped", status_before=before, status_after=before)
        else:
            try:
                answer: object = self.stop_pod(pod)
            except Refused as exc:
                answer = str(exc)
            after = before
            for _ in range(6):
                after = status()
                if after is None or after in STOPPED:
                    break
                self.sleep(10.0)
            confirmed = after is None or after in STOPPED
            outcome.update(result="stopped" if confirmed else "unconfirmed", status_before=before,
                           status_after=after, stop_answer=answer)
        outcome["recorded_utc"] = iso(self.clock())
        outcome["seconds_after_stop_time"] = (self.clock() - arm["stop_at"]).total_seconds()
        final = outcome["result"] in ("stopped", "already-stopped", "gone")
        name = f"stop-{arm_id}.json" if final else f"stop-attempt-{arm_id}-{self.run['run_id']}-{self.run['run_attempt']}.json"
        self.records.create(f"watchdog-stops-{month_of(arm_id)}", name, outcome)
        self.log("pod-stop", arm=arm_id, pod=pod, result=outcome["result"], final=final)
        return outcome

    def _stop_safely(self, arm: dict, outcomes: list[dict]) -> None:
        """One pod's failure (a record that cannot be written, say) must not keep the scan from the
        other pods; it is reported as an outcome and fails the run."""
        try:
            outcomes.append(self.stop(arm))
        except Refused as exc:
            self.log("pod-stop-error", arm=arm["arm"], pod=arm["pod"], reason=str(exc))
            outcomes.append({"arm": arm["arm"], "pod": arm["pod"], "result": "error"})

    def scan(self) -> list[dict]:
        """One scheduled pass (module doc). Returns the outcomes of the stops it attempted."""
        if not self.pods:               # nothing to watch: no record is read and RunPod is not asked anything
            self.log("scan-done", pods=0, outcomes=0)
            return []
        if self._runpod is None:
            raise Refused("configuration: RUNPOD_API_KEY is not set, but the allow-list names a pod: this "
                          "watchdog could not stop it")
        outcomes, waiting = [], []
        for pod, arm in sorted(self.governing().items()):
            if self._stopped_already(arm["arm"]):
                continue
            remaining = (arm["stop_at"] - self.clock()).total_seconds()
            if remaining <= 0:
                self._stop_safely(arm, outcomes)
            elif remaining <= self.tail:
                waiting.append(arm)
        for arm in sorted(waiting, key=lambda a: a["stop_at"]):
            remaining = (arm["stop_at"] - self.clock()).total_seconds()
            if remaining > 0:
                self.log("waiting", arm=arm["arm"], pod=arm["pod"], seconds=remaining)
                self.sleep(remaining)
            current = self.governing().get(arm["pod"])     # a renewal that arrived meanwhile governs
            if current is None or current["arm"] != arm["arm"]:
                self.log("superseded", arm=arm["arm"], pod=arm["pod"])
                continue
            if (current["stop_at"] - self.clock()).total_seconds() <= 0 and not self._stopped_already(arm["arm"]):
                self._stop_safely(current, outcomes)
        self.log("scan-done", pods=len(self.pods), outcomes=len(outcomes))
        return outcomes


def main(env: dict | None = None, clock=utc_now, sleep=time.sleep, out=print) -> int:
    """Exit status 0: an arm was acknowledged, or a scan left nothing unconfirmed. 1: refused or
    unconfirmed (the run then shows as failed in the Actions tab)."""
    env = dict(os.environ if env is None else env)
    try:
        watchdog = Watchdog(env, clock, sleep, out)
        arm_id = env.get("WATCHDOG_ARM", "").strip()
        if env.get("GITHUB_EVENT_NAME") == "repository_dispatch" or arm_id:
            watchdog.arm(arm_id)
            return 0
        outcomes = watchdog.scan()
        # a stop that was not confirmed fails the run, so it shows in the Actions tab; the next scan retries
        return 0 if all(o["result"] in ("stopped", "already-stopped", "gone") for o in outcomes) else 1
    except Refused as exc:
        out(json.dumps({"event": "refused", "reason": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
