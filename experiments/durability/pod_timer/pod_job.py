#!/usr/bin/env python3
"""In-pod job runner (self-contained; Python standard library only; Python 3.8 or later).

This file runs inside the GPU pod as the command the stop timer's supervisor starts
(``pod_timer.py supervise -- python3 -I pod_job.py``). It makes a pod do its work with no inbound
connection: nobody has to log in, and the operator's machine can be off.

What it does, in order, from the job description in the pod's environment
(``POD_JOB_SPEC_B64``: gzip, base64, JSON):

1. starts the image's own start script in the background (SSH and Jupyter, for the operator's
   convenience; nothing here depends on them);
2. **fetches the bundles**: release assets of the private backup repository, named by their
   SHA-256, downloaded with the backup token, hashed while they are written and refused on any
   mismatch; archives are unpacked into the study root with path checks. A bundle fetched before
   (its marker is on the volume) is not fetched again;
3. **writes the small files** the description carries (the worker's configuration), never
   replacing a different file;
4. **runs the steps** in order, each with a receipt (start, log, exit status) under
   ``<root>/.pod-job/steps/``. A step marked ``once`` that succeeded before on this volume is
   skipped. The first failing step ends the sequence;
5. on failure, and on success when the description asks for it, **asks the stop timer to stop the
   pod** after a stated delay, by writing a deadline record on the timer's folder. It never
   stops, terminates or deletes anything itself.

The description holds no secret. The token is read from the environment variable it names, sent
only in an ``Authorization`` header to GitHub's API, never on a redirect, and never printed.
"""

from __future__ import annotations

import base64
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request

VERSION = 1
LEASE_KIND = "durability pod-timer lease v1"       # the stop timer's record format (pod_timer.py)
SHA256 = re.compile(r"[0-9a-f]{64}")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,120}")
RELATIVE = re.compile(r"(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]{1,200}")


class JobError(Exception):
    """The job cannot go on. The message holds no header and no secret."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds")


def load_spec(env: dict) -> dict:
    """The job description, checked: every field it needs, nothing it does not know."""
    try:
        spec = json.loads(gzip.decompress(base64.b64decode(env.get("POD_JOB_SPEC_B64", ""))).decode("utf-8"))
    except (ValueError, OSError):
        raise JobError("the job description is missing or unreadable") from None
    known = {"version", "root", "repository", "release", "token_env", "api_url", "assets", "files", "steps",
             "start_script", "stop_after_failure_seconds", "stop_after_success_seconds", "timer_dir"}
    if not isinstance(spec, dict) or spec.get("version") != VERSION or set(spec) - known:
        raise JobError("the job description is of another version or has unknown fields")
    if not (isinstance(spec.get("root"), str) and os.path.isabs(spec["root"])):
        raise JobError("the job description names no absolute study root")
    for asset in spec.get("assets") or []:
        if not (isinstance(asset, dict) and NAME.fullmatch(str(asset.get("name"))) and SHA256.fullmatch(str(asset.get("sha256")))
                and isinstance(asset.get("bytes"), int) and isinstance(asset.get("extract"), bool)):
            raise JobError("a bundle is described without a plain name, its SHA-256, its size or what to do with it")
    for path, text in (spec.get("files") or {}).items():
        if not (RELATIVE.fullmatch(path) and isinstance(text, str)):
            raise JobError("a file in the job description has no plain relative path")
    for step in spec.get("steps") or []:
        if not (isinstance(step, dict) and NAME.fullmatch(str(step.get("name"))) and isinstance(step.get("argv"), list)
                and step["argv"] and all(isinstance(arg, str) for arg in step["argv"])
                and all(isinstance(k, str) and isinstance(v, str) for k, v in (step.get("env") or {}).items())):
            raise JobError("a step is described without a plain name and a command")
    return spec


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102 - urllib hook
        return None


class GitHub:
    """Reads release assets of one repository. The token goes only to the API's own address."""

    def __init__(self, api: str, repository: str, token: str) -> None:
        self.api, self.repository, self._token = api.rstrip("/"), repository, token
        parts = urllib.parse.urlsplit(self.api)
        if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname == "127.0.0.1"):
            raise JobError("the GitHub address is not HTTPS")
        self._opener = urllib.request.build_opener(_NoRedirect())

    def _open(self, url: str, accept: str):
        """The response of a GET, following at most three redirects without the token."""
        authorized = True
        for _ in range(4):
            parts = urllib.parse.urlsplit(url)
            if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname == "127.0.0.1"):
                raise JobError("refusing a download from an address that is not HTTPS")
            request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "durability-pod-job"})
            if authorized and url.startswith(self.api + "/"):
                request.add_header("Authorization", "Bearer " + self._token)
            try:
                return self._opener.open(request, timeout=120)
            except urllib.error.HTTPError as exc:
                location = exc.headers.get("Location") if exc.headers else None
                if exc.code in (301, 302, 303, 307, 308) and location:
                    url, authorized = urllib.parse.urljoin(url, location), False
                    continue
                raise JobError("GitHub answered %d to a request for %s" % (exc.code, parts.path)) from None
            except (urllib.error.URLError, OSError) as exc:
                raise JobError("a request for %s failed (%s)" % (parts.path, type(exc).__name__)) from None
        raise JobError("too many redirects")

    def asset_id(self, release: str, name: str) -> int:
        with self._open("%s/repos/%s/releases/tags/%s" % (self.api, self.repository, release),
                        "application/vnd.github+json") as response:
            found = json.loads(response.read())
        url = "%s/repos/%s/releases/%d/assets?per_page=100" % (self.api, self.repository, found["id"])
        while url:
            with self._open(url, "application/vnd.github+json") as response:
                page, link = json.loads(response.read()), response.headers.get("Link", "")
            for asset in page:
                if asset.get("name") == name and asset.get("state") == "uploaded":
                    return asset["id"]
            url = next((part.split(";")[0].strip().strip("<>") for part in link.split(",") if 'rel="next"' in part), None)
        raise JobError("the bundle %s is not in the release %s" % (name, release))

    def download(self, asset_id: int, target: str) -> tuple:
        """Write the asset to ``target``; (sha256, bytes) of what was written."""
        digest, size = hashlib.sha256(), 0
        with self._open("%s/repos/%s/releases/assets/%d" % (self.api, self.repository, asset_id),
                        "application/octet-stream") as response, open(target, "wb") as out:
            for block in iter(lambda: response.read(1 << 20), b""):
                out.write(block)
                digest.update(block)
                size += len(block)
            out.flush()
            os.fsync(out.fileno())
        return digest.hexdigest(), size


def unpack(archive: str, root: str) -> int:
    """Unpack a tar archive below ``root``. A member that would leave the root, a link or a device
    refuses the whole archive before anything is written."""
    real_root = os.path.realpath(root)
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        for member in members:
            target = os.path.realpath(os.path.join(real_root, member.name))
            if not (member.isfile() or member.isdir()) or not (target == real_root or target.startswith(real_root + os.sep)):
                raise JobError("the bundle holds a member that is not a plain file or folder inside the study root")
        for member in members:
            if hasattr(tarfile, "data_filter"):
                tar.extract(member, real_root, filter="data")
            else:
                tar.extract(member, real_root)
    return len(members)


def ask_timer_to_stop(folder: str, pod: str, after_seconds: float, reason: str, clock=utc_now) -> str | None:
    """Write a deadline record for the stop timer (the most recently issued authority governs).
    Returns the record's id, or None when the timer's folder or the pod's id is not known."""
    if not (folder and os.path.isabs(folder) and pod):
        return None
    try:
        now = clock().replace(microsecond=0)
        stop = now + dt.timedelta(seconds=after_seconds)
        lease = now.strftime("%Y%m%dT%H%M%SZ") + "-" + os.urandom(8).hex()
        record = {"kind": LEASE_KIND, "lease": lease, "worker": "pod-job", "pod": pod, "stop_at_utc": iso(stop),
                  "reserved_until_utc": iso(stop), "published_utc": iso(now), "purpose": "finish", "reason": reason[:160]}
        leases = os.path.join(folder, "leases")
        os.makedirs(leases, exist_ok=True)
        tmp = os.path.join(leases, "." + lease + ".tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(record, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.rename(tmp, os.path.join(leases, lease + ".json"))
        return lease
    except OSError:
        return None


class Job:
    def __init__(self, env: dict, out=print, clock=utc_now) -> None:
        self.env, self.out, self.clock = dict(env), out, clock
        self.spec = load_spec(self.env)
        self.root = self.spec["root"]
        self.state = os.path.join(self.root, ".pod-job")
        self.pod = self.env.get("RUNPOD_POD_ID", "").strip()

    def log(self, event: str, **fields: object) -> None:
        line = json.dumps({"event": event, "utc": iso(self.clock()), **fields}, sort_keys=True)
        try:
            self.out(line)
            os.makedirs(self.state, exist_ok=True)
            with open(os.path.join(self.state, "job.jsonl"), "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            pass

    # ----- bundles and files -----------------------------------------------------------------

    def fetch(self) -> None:
        assets = self.spec.get("assets") or []
        if not assets:
            return
        token = self.env.get(self.spec.get("token_env", "ATTRIBUTION_BACKUP_GITHUB_TOKEN"), "").strip()
        if not token:
            raise JobError("the backup token is not in the environment")
        github = GitHub(self.spec.get("api_url", "https://api.github.com"), self.spec["repository"], token)
        markers, downloads = os.path.join(self.state, "assets"), os.path.join(self.state, "downloads")
        os.makedirs(markers, exist_ok=True)
        os.makedirs(downloads, exist_ok=True)
        for asset in assets:
            marker = os.path.join(markers, asset["sha256"] + ".json")
            if os.path.exists(marker):
                self.log("bundle-present", name=asset["name"])
                continue
            started, target = time.monotonic(), os.path.join(downloads, asset["name"])
            digest, size = github.download(github.asset_id(self.spec["release"], asset["name"]), target)
            if digest != asset["sha256"] or size != asset["bytes"]:
                os.replace(target, target + ".rejected")
                raise JobError("the bundle %s does not have the described hash or size" % asset["name"])
            members = unpack(target, self.root) if asset["extract"] else 0
            with open(marker, "w", encoding="utf-8") as handle:
                json.dump({"name": asset["name"], "sha256": digest, "bytes": size, "members": members,
                           "fetched_utc": iso(self.clock())}, handle)
            self.log("bundle-fetched", name=asset["name"], bytes=size, members=members, seconds=time.monotonic() - started)

    def write_files(self) -> None:
        for path, text in sorted((self.spec.get("files") or {}).items()):
            target = os.path.join(self.root, path)
            data = text.encode("utf-8")
            if os.path.exists(target):
                with open(target, "rb") as handle:
                    if handle.read() != data:
                        raise JobError("%s exists with other content; it is never replaced" % path)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as handle:
                handle.write(data)
            self.log("file-written", path=path, bytes=len(data))

    # ----- steps -----------------------------------------------------------------------------

    def _succeeded_before(self, folder: str, key: str) -> bool:
        if not os.path.isdir(folder):
            return False
        for name in sorted(os.listdir(folder)):
            try:
                with open(os.path.join(folder, name, "receipt.json"), encoding="utf-8") as handle:
                    receipt = json.load(handle)
            except (OSError, ValueError):
                continue
            if receipt.get("command_sha256") == key and receipt.get("exit_code") == 0:
                return True
        return False

    def run_steps(self) -> None:
        for step in self.spec.get("steps") or []:
            key = hashlib.sha256(json.dumps([step["argv"], step.get("env") or {}], sort_keys=True).encode()).hexdigest()
            folder = os.path.join(self.state, "steps", step["name"])
            if step.get("once") and self._succeeded_before(folder, key):
                self.log("step-skipped", step=step["name"], why="it succeeded before on this volume")
                continue
            attempt = len(os.listdir(folder)) + 1 if os.path.isdir(folder) else 1
            receipt_dir = os.path.join(folder, "%03d" % attempt)
            os.makedirs(receipt_dir)
            base = {"step": step["name"], "command": step["argv"], "command_sha256": key, "started_utc": iso(self.clock())}
            with open(os.path.join(receipt_dir, "started.json"), "w", encoding="utf-8") as handle:
                json.dump(base, handle, indent=2)
            self.log("step-started", step=step["name"], attempt=attempt)
            started = time.monotonic()
            with open(os.path.join(receipt_dir, "process.log"), "wb") as log:
                try:
                    code = subprocess.run(step["argv"], cwd=self.root, env={**self.env, **(step.get("env") or {})},
                                          stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, check=False).returncode
                except OSError as exc:
                    code = "not started (%s)" % type(exc).__name__
            receipt = {**base, "exit_code": code, "elapsed_seconds": time.monotonic() - started, "ended_utc": iso(self.clock())}
            with open(os.path.join(receipt_dir, "receipt.json"), "w", encoding="utf-8") as handle:
                json.dump(receipt, handle, indent=2)
            self.log("step-ended", step=step["name"], attempt=attempt, exit_code=code, seconds=receipt["elapsed_seconds"])
            if code != 0:
                raise JobError("the step %s ended with status %s" % (step["name"], code))

    # ----- the stop, through the timer ---------------------------------------------------------

    def ask_timer_to_stop(self, after_seconds: float, reason: str) -> str | None:
        return ask_timer_to_stop(self.spec.get("timer_dir") or self.env.get("POD_TIMER_DIR", ""), self.pod,
                                 after_seconds, reason, self.clock)

    def run(self) -> int:
        script = self.spec.get("start_script", "/start.sh")
        if script and os.path.exists(script):
            try:
                subprocess.Popen([script], stdin=subprocess.DEVNULL, start_new_session=True)  # noqa: S603 - the image's own script
                self.log("start-script-started", script=script)
            except OSError as exc:
                self.log("start-script-failed", reason=type(exc).__name__)
        try:
            os.makedirs(self.root, exist_ok=True)
            self.fetch()
            self.write_files()
            self.run_steps()
        except JobError as exc:
            delay = self.spec.get("stop_after_failure_seconds", 300)
            asked = self.ask_timer_to_stop(delay, "the pod job failed") if delay is not None else None
            self.log("job-failed", reason=str(exc), stop_record=asked, stop_after_seconds=delay)
            return 1
        delay = self.spec.get("stop_after_success_seconds")
        asked = self.ask_timer_to_stop(delay, "the pod job is complete") if delay is not None else None
        self.log("job-complete", stop_record=asked, stop_after_seconds=delay)
        return 0


def main(env: dict | None = None) -> int:
    env = dict(os.environ if env is None else env)
    try:
        return Job(env).run()
    except JobError as exc:                     # the description itself is unusable: nothing was started
        asked = ask_timer_to_stop(env.get("POD_TIMER_DIR", ""), env.get("RUNPOD_POD_ID", "").strip(), 300,
                                  "the pod job's description is unusable")
        print(json.dumps({"event": "job-refused", "reason": str(exc), "stop_record": asked}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
