"""The operator-side launcher: one pod for one host, with the stop timer, the job runner and the
bundles, and a record of every request (stdlib only).

``python -m experiments.durability launch --spec launch.json --record launch.jsonl`` runs on the
operator's machine with two credentials in its environment: an account key for RunPod that may
create pods (``RUNPOD_API_KEY`` here, on the laptop) and the backup token for GitHub. It:

1. checks the description: no secret value anywhere. A variable whose name looks like a key, token
   or password must be a RunPod secret reference (``{{ RUNPOD_SECRET_name }}``), and
   ``RUNPOD_API_KEY`` may not be set at all: inside a pod that name belongs to RunPod;
2. reads the GPU's hourly price and refuses above ``max_price_per_hour``; nothing exists yet;
3. refuses when a pod of that name already exists and is not terminated;
4. uploads the bundles to the backup repository as release assets named by their SHA-256
   (create-only; one already there is reused). Bundles are opaque bytes: they are hashed, never
   opened;
5. finds the network volume by name, or creates it when the description allows; two volumes of
   one name refuse;
6. generates the timer settings (the cap counts from this moment) and creates the pod: the image,
   one GPU of the stated type, the volume at its mount, the environment, and the start command
   that runs the stop timer and under it the job runner (``pod_timer/pod_job.py``);
7. checks the price RunPod reports for the pod it created; above the limit, the pod is **stopped**.

It never terminates or deletes anything: the only request that ends something is that stop. Every
request and its answer go to the record file, without headers; the packed scripts are recorded by
hash and length, secret references as written.

**Why the bundles go through GitHub and not SSH.** The pod fetches them itself with the backup
token it needs anyway, checks their hashes and starts its own work. No inbound connection is
needed, so the operator's machine can be off, and a restart of the pod or a restore on a fresh pod
repeats the same steps without the operator. The 2 October dispatch pushed the bundles over SSH
and started the work from the laptop; when the laptop's connection ended, so did retrieval.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import re
import tarfile
import time
from pathlib import Path
from typing import Mapping

from .common import Clock, DurabilityError, ProviderError, append_jsonl, iso, sha256_file, utc_clock
from .github_destination import GITHUB_TOKEN_ENV
from .shutdown_timer import settings
from .transport import Http, next_link

__all__ = ["LaunchRefused", "Bundles", "Account", "Launcher", "pack_code", "load_spec", "JOB_SCRIPT",
           "SECRET_REFERENCE", "RUNPOD_ADMIN_KEY_ENV"]

RUNPOD_ADMIN_KEY_ENV = "RUNPOD_API_KEY"
JOB_SCRIPT = Path(__file__).resolve().parent / "pod_timer" / "pod_job.py"
SECRET_REFERENCE = re.compile(r"\{\{ RUNPOD_SECRET_[A-Za-z0-9_]+ \}\}")
_SECRET_NAME = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", re.I)
_PACKED = re.compile(r"POD_(TIMER|JOB)_(B64_\d\d|SPEC_B64)")
_JSON = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
_SPEC_KEYS = {"name", "host", "image", "gpu_type", "cloud", "max_price_per_hour", "volume", "mount", "container_disk_gb",
              "ports", "cap_minutes", "secrets", "env", "job", "bundles", "bundle_repository", "bundle_release", "extra",
              "state_dir"}
_NOT_EXTRA = {"name", "imageName", "gpuTypeIds", "gpuCount", "computeType", "cloudType", "interruptible", "networkVolumeId",
              "volumeMountPath", "containerDiskInGb", "ports", "env", "dockerStartCmd", "dockerEntrypoint", "dataCenterIds",
              "locked", "templateId"}


class LaunchRefused(DurabilityError):
    """Nothing was created, or what was created was stopped: the description, a price, a duplicate
    or an answer was not acceptable."""


def load_spec(source: str | Path | Mapping) -> dict:
    """The launch description from a JSON file or a mapping, checked (module doc)."""
    spec = dict(json.loads(Path(source).read_text(encoding="utf-8")) if not isinstance(source, Mapping) else source)
    required = {"name", "image", "gpu_type", "max_price_per_hour", "volume", "cap_minutes", "job", "bundle_repository"}
    unknown, missing = sorted(set(spec) - _SPEC_KEYS), sorted(required - set(spec))
    if unknown or missing:
        raise LaunchRefused(f"the launch description has unknown keys {unknown} or lacks {missing}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", str(spec["name"])):
        raise LaunchRefused("the pod's name must be plain")
    price = spec["max_price_per_hour"]
    if not (isinstance(price, (int, float)) and not isinstance(price, bool) and price > 0):
        raise LaunchRefused("max_price_per_hour must be a positive number")
    volume = spec["volume"]
    if not (isinstance(volume, Mapping) and isinstance(volume.get("name"), str) and volume["name"]
            and isinstance(volume.get("data_center"), str) and set(volume) <= {"name", "data_center", "size_gb", "create"}):
        raise LaunchRefused("the volume needs a name and a data center (and, to be created, size_gb and create)")
    if volume.get("create") and not (isinstance(volume.get("size_gb"), int) and 1 <= volume["size_gb"] <= 4000):
        raise LaunchRefused("a volume to be created needs its size in GB")
    env, secrets = dict(spec.get("env") or {}), dict(spec.get("secrets") or {})
    for name, value in secrets.items():
        if not re.fullmatch(r"[A-Za-z0-9_]+", str(value)):
            raise LaunchRefused(f"the secret for {name} must be the name of a RunPod secret, never a value")
    for name, value in env.items():
        if not isinstance(value, str):
            raise LaunchRefused(f"the environment value of {name} is not text")
        if _SECRET_NAME.search(name) and not SECRET_REFERENCE.fullmatch(value):
            raise LaunchRefused(f"{name} looks like a credential: give it under 'secrets' as the name of a RunPod "
                                "secret, never as a value")
    if "RUNPOD_API_KEY" in env or "RUNPOD_API_KEY" in secrets:
        raise LaunchRefused("RUNPOD_API_KEY must not be set: inside a pod that name is RunPod's own pod-scoped key")
    if set(spec.get("extra") or {}) & _NOT_EXTRA:
        raise LaunchRefused(f"extra may not set {sorted(set(spec['extra']) & _NOT_EXTRA)}")
    job = spec["job"]
    if not (isinstance(job, Mapping) and isinstance(job.get("root"), str) and isinstance(job.get("steps"), list)
            and set(job) <= {"root", "files", "steps", "start_script", "stop_after_failure_seconds",
                             "stop_after_success_seconds"}):
        raise LaunchRefused("the job needs a root and steps (and may give files, start_script and the stop delays)")
    for bundle in spec.get("bundles") or []:
        if not (isinstance(bundle, Mapping) and isinstance(bundle.get("path"), str) and isinstance(bundle.get("extract"), bool)
                and set(bundle) <= {"path", "extract", "sha256"}):
            raise LaunchRefused("a bundle is given as {path, extract} and optionally its expected sha256")
    return spec


def pack_code(project_root: str | Path, out: str | Path) -> dict:
    """A deterministic archive of this package's source for the pod: ``experiments/durability``
    without its tests (and ``experiments/__init__.py`` when there is one). The same source gives
    the same bytes. Returns the archive's path, hash, size and file count."""
    root, out = Path(project_root).resolve(), Path(out)
    package = root / "experiments" / "durability"
    files = sorted(p for p in package.rglob("*") if p.is_file() and not p.is_symlink() and "tests" not in p.relative_to(package).parts
                   and "__pycache__" not in p.parts and p.suffix in {".py", ".json", ".yml", ".md"})
    if (root / "experiments" / "__init__.py").is_file():
        files.insert(0, root / "experiments" / "__init__.py")
    if out.exists():
        raise LaunchRefused(f"{out} exists; an archive is never replaced")
    with open(out, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as zipped, \
            tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path in files:
            info = tarfile.TarInfo(path.relative_to(root).as_posix())
            data = path.read_bytes()
            info.size, info.mode, info.mtime, info.uid, info.gid, info.uname, info.gname = len(data), 0o644, 0, 0, 0, "", ""
            import io
            archive.addfile(info, io.BytesIO(data))
    return {"path": str(out), "sha256": sha256_file(out), "bytes": out.stat().st_size, "files": len(files)}


def _scrub(value):
    """A request or an answer as it may be recorded: packed scripts by hash and length, everything
    else as it is (the description was checked to hold no secret value)."""
    if isinstance(value, Mapping):
        out = {}
        for key, item in value.items():
            if isinstance(item, str) and _PACKED.fullmatch(str(key)):
                out[key] = {"sha256": hashlib.sha256(item.encode()).hexdigest(), "chars": len(item)}
            elif _SECRET_NAME.search(str(key)) and isinstance(item, str) and not SECRET_REFERENCE.fullmatch(item):
                out[key] = "<not recorded>"
            else:
                out[key] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


class _Recorder:
    def __init__(self, path: str | Path, clock: Clock) -> None:
        self.path, self.clock = Path(path), clock

    def __call__(self, event: str, **fields: object) -> None:
        append_jsonl(self.path, {"event": event, "utc": iso(self.clock()), **_scrub(fields)})


class Bundles:
    """Bundles as release assets of the backup repository, named ``<sha256><suffix>``."""

    def __init__(self, repository: str, release: str = "pod-bundles", *, record, token_env: str = GITHUB_TOKEN_ENV,
                 api_url: str = "https://api.github.com", upload_url: str = "https://uploads.github.com", **http) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}", repository):
            raise LaunchRefused("the bundle repository must be given as owner/name")
        self.repository, self.release, self.record = repository, release, record
        self.api, self.uploads = api_url.rstrip("/"), upload_url.rstrip("/")
        self.http = Http(token_env=token_env, bases=(self.api, self.uploads), **http)

    def _release(self) -> dict:
        url = f"{self.api}/repos/{self.repository}/releases/tags/{self.release}"
        reply = self.http.request("GET", url, headers=_JSON)
        if reply.status == 404:
            reply = self.http.request("POST", f"{self.api}/repos/{self.repository}/releases", headers=_JSON, body=json.dumps({
                "tag_name": self.release, "name": self.release, "prerelease": True,
                "body": "Bundles for pods, named by their SHA-256. Create-only."}).encode("utf-8"))
            self.record("github", request="create release", release=self.release, status=reply.status)
            if reply.status == 422:
                reply = self.http.request("GET", url, headers=_JSON)
        release = reply.json() if reply.status in (200, 201) else None
        if not isinstance(release, dict) or not isinstance(release.get("id"), int):
            raise LaunchRefused(f"GitHub answered {reply.status} for the bundle release")
        return release

    def ensure(self, path: str | Path, expected_sha256: str | None = None) -> dict:
        """Upload the file unless an asset of its hash is already there. Returns its description for
        the pod (name, sha256, bytes)."""
        path = Path(path)
        digest, size = sha256_file(path), path.stat().st_size
        if expected_sha256 is not None and digest != expected_sha256:
            raise LaunchRefused(f"{path.name} does not have the hash the description expects")
        name = digest + "".join(path.suffixes[-2:])
        release = self._release()
        url, found = f"{self.api}/repos/{self.repository}/releases/{release['id']}/assets?per_page=100", None
        while url and found is None:
            reply = self.http.request("GET", url, headers=_JSON)
            page = reply.json() if reply.status == 200 else None
            if not isinstance(page, list):
                raise LaunchRefused(f"GitHub answered {reply.status} to a listing of bundles")
            found = next((a for a in page if isinstance(a, dict) and a.get("name") == name), None)
            url = next_link(reply.headers)
        if found is not None and (found.get("state") != "uploaded" or found.get("size") != size):
            raise LaunchRefused(f"the bundle {name} is in the repository in an unfinished or different state")
        if found is None:
            reply = self.http.request(
                "POST", f"{self.uploads}/repos/{self.repository}/releases/{release['id']}/assets?name={name}",
                headers={**_JSON, "Content-Type": "application/octet-stream"}, body=path)
            self.record("github", request="upload bundle", name=name, bytes=size, status=reply.status)
            if reply.status not in (201, 422):
                raise LaunchRefused(f"GitHub answered {reply.status} to the upload of {name}")
        else:
            self.record("github", request="bundle already there", name=name, bytes=size)
        return {"name": name, "sha256": digest, "bytes": size}


class Account:
    """The RunPod requests the launcher makes: read prices, volumes and pods; create a volume;
    create a pod; stop a pod. No terminate, no delete, no update."""

    def __init__(self, *, record, key_env: str = RUNPOD_ADMIN_KEY_ENV, rest_url: str = "https://rest.runpod.io/v1",
                 graphql_url: str = "https://api.runpod.io/graphql", **http) -> None:
        self.rest, self.graphql, self.record = rest_url.rstrip("/"), graphql_url.rstrip("/"), record
        self.http = Http(token_env=key_env, bases=(self.rest, self.graphql), **http)

    def _call(self, method: str, path: str, body: Mapping | None = None, ok: tuple = (200,)):
        reply = self.http.request(method, f"{self.rest}{path}", headers={"Accept": "application/json",
                                                                        "Content-Type": "application/json"},
                                  body=None if body is None else json.dumps(body).encode("utf-8"))
        try:
            answer = reply.json() if reply.body else None
        except DurabilityError:
            answer = None
        self.record("runpod", request=f"{method} {path}", body=body, status=reply.status,
                    answer=answer if method != "GET" else {"items": len(answer) if isinstance(answer, list) else None})
        if reply.status not in ok:
            raise LaunchRefused(f"RunPod answered {reply.status} to {method} {path}")
        return answer

    def price(self, gpu_type: str, cloud: str) -> float:
        reply = self.http.request("POST", self.graphql, headers={"Content-Type": "application/json", "Accept": "application/json"},
                                  body=json.dumps({"query": "query { gpuTypes { id securePrice communityPrice } }"}).encode())
        data = reply.json() if reply.status == 200 else None
        types = data.get("data", {}).get("gpuTypes") if isinstance(data, dict) and isinstance(data.get("data"), dict) else None
        match = [t for t in types or [] if isinstance(t, dict) and t.get("id") == gpu_type]
        price = match[0].get("securePrice" if cloud == "SECURE" else "communityPrice") if len(match) == 1 else None
        self.record("runpod", request="query gpuTypes", status=reply.status, answer={"gpu_type": gpu_type, "price": price})
        if not (isinstance(price, (int, float)) and not isinstance(price, bool) and price > 0):
            raise LaunchRefused(f"RunPod reported no usable {cloud} price for {gpu_type}")
        return float(price)

    def pods(self) -> list:
        answer = self._call("GET", "/pods")
        if not isinstance(answer, list):
            raise ProviderError("RunPod listed pods in an unexpected shape")
        return answer

    def volumes(self) -> list:
        answer = self._call("GET", "/networkvolumes")
        if not isinstance(answer, list):
            raise ProviderError("RunPod listed network volumes in an unexpected shape")
        return answer

    def create_volume(self, name: str, size_gb: int, data_center: str) -> dict:
        return self._call("POST", "/networkvolumes", {"name": name, "size": size_gb, "dataCenterId": data_center},
                          ok=(200, 201))

    def create_pod(self, body: Mapping) -> dict:
        return self._call("POST", "/pods", body, ok=(200, 201))

    def stop_pod(self, pod: str) -> None:
        self._call("POST", f"/pods/{pod}/stop", ok=(200,))


class Launcher:
    """See the module doc. ``project_root`` resolves relative bundle paths."""

    def __init__(self, account: Account, bundles: Bundles, *, record, project_root: str | Path = ".",
                 clock: Clock = utc_clock) -> None:
        self.account, self.bundles, self.record, self.clock = account, bundles, record, clock
        self.project_root = Path(project_root)

    def _job_env(self, spec: Mapping, assets: list) -> dict:
        job = spec["job"]
        description = {"version": 1, "root": job["root"], "repository": spec["bundle_repository"],
                       "release": self.bundles.release, "token_env": GITHUB_TOKEN_ENV, "assets": assets,
                       "files": {path: text if isinstance(text, str) else json.dumps(text, indent=1, sort_keys=True)
                                 for path, text in dict(job.get("files") or {}).items()},
                       "steps": list(job["steps"]),
                       "start_script": job.get("start_script", "/start.sh"),
                       "stop_after_failure_seconds": job.get("stop_after_failure_seconds", 300),
                       "stop_after_success_seconds": job.get("stop_after_success_seconds")}
        packed = base64.b64encode(gzip.compress(json.dumps(description, sort_keys=True).encode("utf-8"), 9, mtime=0))
        return {"POD_JOB_SPEC_B64": packed.decode("ascii")}

    def plan(self, spec: Mapping, assets: list) -> dict:
        """The create-pod request for this description (the cap counts from now)."""
        mount = spec.get("mount", "/workspace")
        made = settings(state_dir=spec.get("state_dir", f"{mount}/.pod-timer"), cap_seconds=float(spec["cap_minutes"]) * 60.0,
                        clock=self.clock, job_script=JOB_SCRIPT)
        env = {**dict(spec.get("env") or {}), **made["env"], **self._job_env(spec, assets)}
        for name, secret in dict(spec.get("secrets") or {}).items():
            env[name] = "{{ RUNPOD_SECRET_%s }}" % secret
        body = {"name": spec["name"], "imageName": spec["image"], "gpuTypeIds": [spec["gpu_type"]], "gpuCount": 1,
                "computeType": "GPU", "cloudType": spec.get("cloud", "SECURE"), "interruptible": False,
                "volumeMountPath": mount, "containerDiskInGb": int(spec.get("container_disk_gb", 50)),
                "ports": list(spec.get("ports", ["22/tcp"])), "dataCenterIds": [spec["volume"]["data_center"]],
                "env": env, "dockerStartCmd": made["docker_start_cmd"], **dict(spec.get("extra") or {})}
        return {"body": body, "cap_stop_utc": made["cap_stop_utc"], "timer_sha256": made["script_sha256"],
                "job_sha256": made["job_sha256"]}

    def launch(self, spec: Mapping, *, dry_run: bool = False) -> dict:
        spec = load_spec(spec)
        cloud = spec.get("cloud", "SECURE")
        if dry_run:
            assets = [{"name": "<sha256 of %s>" % Path(b["path"]).name, "sha256": "0" * 64, "bytes": 0, "extract": b["extract"]}
                      for b in spec.get("bundles") or []]
            planned = self.plan(spec, assets)
            return {"dry_run": True, "request": _scrub(planned["body"]), "cap_stop_utc": planned["cap_stop_utc"]}
        self.record("launch-intended", name=spec["name"], host=spec.get("host"), gpu_type=spec["gpu_type"], cloud=cloud,
                    max_price_per_hour=spec["max_price_per_hour"], volume=spec["volume"])
        price = self.account.price(spec["gpu_type"], cloud)
        if price > spec["max_price_per_hour"]:
            raise LaunchRefused(f"{spec['gpu_type']} costs {price:g} per hour, above the limit of "
                                f"{spec['max_price_per_hour']:g}: nothing was created")
        same = [p for p in self.account.pods() if isinstance(p, dict) and p.get("name") == spec["name"]
                and p.get("desiredStatus") != "TERMINATED"]
        if same:
            raise LaunchRefused(f"a pod named {spec['name']} already exists ({same[0].get('desiredStatus')}): "
                                "nothing was created")
        assets = []
        for bundle in spec.get("bundles") or []:
            path = Path(bundle["path"])
            described = self.bundles.ensure(path if path.is_absolute() else self.project_root / path, bundle.get("sha256"))
            assets.append({**described, "extract": bundle["extract"]})
        volume = self._volume(spec["volume"])
        planned = self.plan(spec, assets)
        body = {**planned["body"], "networkVolumeId": volume["id"]}
        pod = self.account.create_pod(body)
        if not (isinstance(pod, dict) and isinstance(pod.get("id"), str) and pod["id"]):
            raise LaunchRefused("RunPod answered the pod creation in an unexpected shape; check the account by hand")
        cost = pod.get("costPerHr")
        try:
            cost = float(cost)
        except (TypeError, ValueError):
            cost = None
        result = {"pod": pod["id"], "name": spec["name"], "volume": volume["id"], "cost_per_hour": cost,
                  "cap_stop_utc": planned["cap_stop_utc"], "bundles": assets, "timer_sha256": planned["timer_sha256"],
                  "job_sha256": planned["job_sha256"], "stopped": False}
        if cost is None or cost > spec["max_price_per_hour"]:
            self.account.stop_pod(pod["id"])
            result["stopped"] = True
            self.record("launch-stopped", **result)
            raise LaunchRefused(f"the created pod {pod['id']} reports a price above the limit or none: it was stopped "
                                "(not deleted)")
        self.record("launch-done", **result)
        return result

    def _volume(self, wanted: Mapping) -> dict:
        named = [v for v in self.account.volumes() if isinstance(v, dict) and v.get("name") == wanted["name"]]
        if len(named) > 1:
            raise LaunchRefused(f"{len(named)} network volumes are named {wanted['name']}: name the one to use uniquely")
        if named:
            if named[0].get("dataCenterId") != wanted["data_center"] or not isinstance(named[0].get("id"), str):
                raise LaunchRefused(f"the volume {wanted['name']} is in another data center than the description says")
            return named[0]
        if not wanted.get("create"):
            raise LaunchRefused(f"there is no network volume named {wanted['name']} and the description does not allow "
                                "creating one")
        made = self.account.create_volume(wanted["name"], wanted["size_gb"], wanted["data_center"])
        if not (isinstance(made, dict) and isinstance(made.get("id"), str)):
            raise LaunchRefused("RunPod answered the volume creation in an unexpected shape; check the account by hand")
        return made
