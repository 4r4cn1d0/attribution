"""The operator-side launcher and the in-pod job runner (ENGINEERING FIXTURES; fake RunPod and
GitHub services on 127.0.0.1; no real pod, key, token or request).

The launcher: the shape of what it asks RunPod to create, secrets only as references, no
``RUNPOD_API_KEY``, refusal of duplicates and of a price above the limit, a pod stopped (never
deleted) when it reports a higher price, bundles as opaque hashed files, every request recorded
without a secret. The job runner, as a real process: bundles fetched with the token and checked,
a wrong or tampered bundle refused, files never replaced, steps with receipts, a ``once`` step
not repeated, and the stop timer asked to stop the pod on failure. And the generated start
command, run by bash, starting the timer and under it the job runner.

Nothing here shows what RunPod or GitHub really do."""

from __future__ import annotations

import base64
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import pytest

import dur_fixtures as dur
from fake_github import TOKEN, FakeGitHub
from fake_runpod import KEY, FakeRunPod, network_volume, pod

from experiments.durability.__main__ import main as cli
from experiments.durability.common import NotConfigured, read_jsonl
from experiments.durability.github_destination import GITHUB_TOKEN_ENV
from experiments.durability.launcher import (JOB_SCRIPT, RUNPOD_ADMIN_KEY_ENV, Account, Bundles, Launcher, LaunchRefused,
                                             _Recorder, load_spec, pack_code)
from experiments.durability.shutdown_timer import TIMER_SCRIPT, settings

REPOSITORY = "owner/backups"
PROJECT = Path(__file__).resolve().parents[3]
READ_KEY = "fake-read-key-value-never-a-real-credential"


def tar_bundle(path: Path, files: dict[str, bytes]) -> Path:
    with tarfile.open(path, "w:gz") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return path


class Desk:
    """The operator's machine: both fakes, the two credentials in the environment, a launcher."""

    def __init__(self, folder: Path, monkeypatch) -> None:
        self.folder = folder
        self.github, self.runpod = FakeGitHub(REPOSITORY), FakeRunPod()
        self.github.foreign, self.runpod.foreign = [KEY], [TOKEN]
        self.runpod.pods = []
        self.runpod.volumes = [network_volume("vol-other", size=10)]
        monkeypatch.setenv(GITHUB_TOKEN_ENV, TOKEN)
        monkeypatch.setenv(RUNPOD_ADMIN_KEY_ENV, KEY)
        self.clock = dur.ManualClock()
        self.record_path = folder / "launch.jsonl"
        self.setup = tar_bundle(folder / "worker-setup.tar.gz", {"bootstrap.sh": b"echo bootstrap\n",
                                                                 "prepared-v2/hidden/hidden.jsonl": b"OPAQUE HELD-OUT BYTES\n"})
        self.code = folder / "code.tar.gz"

    def launcher(self) -> Launcher:
        record = _Recorder(self.record_path, self.clock)
        account = Account(record=record, rest_url=f"{self.runpod.url}/v1", graphql_url=f"{self.runpod.url}/graphql",
                          max_retries=0, sleep=lambda s: None)
        bundles = Bundles(REPOSITORY, record=record, api_url=self.github.url, upload_url=self.github.url, max_retries=0,
                          sleep=lambda s: None)
        return Launcher(account, bundles, record=record, project_root=self.folder, clock=self.clock)

    def spec(self, **changes) -> dict:
        base = {"name": "attribution-dev05", "host": "dev05", "image": "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404",
                "gpu_type": "NVIDIA A100-SXM4-80GB", "cloud": "SECURE", "max_price_per_hour": 1.7,
                "volume": {"name": "attribution-dev05", "data_center": "US-MD-1", "size_gb": 50, "create": True},
                "mount": "/workspace", "container_disk_gb": 60, "cap_minutes": 45,
                "secrets": {GITHUB_TOKEN_ENV: "backup_token", "RUNPOD_READ_API_KEY": "read_key"},
                "env": {"HF_HOME": "/workspace/attribution-study-v2/hf-home"},
                "bundles": [{"path": "worker-setup.tar.gz", "extract": True}],
                "bundle_repository": REPOSITORY,
                "job": {"root": "/workspace/attribution-study-v2",
                        "files": {"worker-dev05.json": json.dumps({"host": "dev05"})},
                        "steps": [{"name": "bootstrap", "argv": ["bash", "bootstrap.sh"], "once": True},
                                  {"name": "worker", "argv": ["venv/bin/python", "-m", "experiments.durability", "worker",
                                                              "--config", "worker-dev05.json"]}]},
                "extra": {"minRAMPerGPU": 32, "minVCPUPerGPU": 8, "allowedCudaVersions": ["12.8"]}}
        return {**base, **changes}

    def requests(self, method: str | None = None) -> list[tuple]:
        return [(m, p.split("?")[0]) for m, p, _ in self.runpod.log if method in (None, m)]

    def created(self) -> dict:
        (body,) = [json.loads(b) for m, p, b in self.runpod.log if (m, p) == ("POST", "/v1/pods")]
        return body

    def close(self) -> None:
        self.github.close()
        self.runpod.close()


@pytest.fixture
def desk(tmp_path, monkeypatch):
    built = Desk(tmp_path, monkeypatch)
    yield built
    assert built.github.leaks == [] and built.runpod.leaks == []
    assert all(method in ("GET", "POST") for method, _, _ in built.runpod.log)      # nothing is ever deleted or patched
    assert all(method in ("GET", "POST") for method, _, _ in built.github.log)
    assert not any("/terminate" in path or "podTerminate" in body for _, path, body in built.runpod.log)
    built.close()


# ----- the launcher --------------------------------------------------------------------------


def test_the_launcher_creates_one_volume_and_one_pod_with_the_timer_the_job_and_secret_references(desk):
    result = desk.launcher().launch(desk.spec())
    assert result["pod"] == "pod-new-2" and result["volume"] == "vol-new-1" and result["stopped"] is False
    assert result["cost_per_hour"] == 1.59 and result["cap_stop_utc"] == dur.iso(dur.T0 + dt.timedelta(minutes=45))
    # the order: price, duplicates, volumes, the volume, the pod; and nothing else that changes anything
    assert desk.requests() == [("POST", "/graphql"), ("GET", "/v1/pods"), ("GET", "/v1/networkvolumes"),
                               ("POST", "/v1/networkvolumes"), ("POST", "/v1/pods")]
    body = desk.created()
    assert {key: body[key] for key in ("name", "imageName", "gpuTypeIds", "gpuCount", "computeType", "cloudType",
                                       "interruptible", "networkVolumeId", "volumeMountPath", "containerDiskInGb", "ports",
                                       "dataCenterIds", "minRAMPerGPU", "minVCPUPerGPU", "allowedCudaVersions")} == {
        "name": "attribution-dev05", "imageName": "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404",
        "gpuTypeIds": ["NVIDIA A100-SXM4-80GB"], "gpuCount": 1, "computeType": "GPU", "cloudType": "SECURE",
        "interruptible": False, "networkVolumeId": "vol-new-1", "volumeMountPath": "/workspace", "containerDiskInGb": 60,
        "ports": ["22/tcp"], "dataCenterIds": ["US-MD-1"], "minRAMPerGPU": 32, "minVCPUPerGPU": 8,
        "allowedCudaVersions": ["12.8"]}
    env = body["env"]
    assert env[GITHUB_TOKEN_ENV] == "{{ RUNPOD_SECRET_backup_token }}" and env["RUNPOD_READ_API_KEY"] == "{{ RUNPOD_SECRET_read_key }}"
    assert "RUNPOD_API_KEY" not in env and env["HF_HOME"] == "/workspace/attribution-study-v2/hf-home"
    assert env["POD_TIMER_DIR"] == "/workspace/.pod-timer" and env["POD_TIMER_CAP_STOP_UTC"] == result["cap_stop_utc"]
    assert gzip.decompress(base64.b64decode(env["POD_TIMER_B64_00"])) == TIMER_SCRIPT.read_bytes()
    assert gzip.decompress(base64.b64decode(env["POD_JOB_B64_00"])) == JOB_SCRIPT.read_bytes()
    command = body["dockerStartCmd"]
    assert command[:2] == ["bash", "-c"] and result["timer_sha256"] in command[2] and result["job_sha256"] in command[2]
    assert 'supervise -- python3 -I "$d/pod_job.py"' in command[2] and "pod stop" in command[2]
    job = json.loads(gzip.decompress(base64.b64decode(env["POD_JOB_SPEC_B64"])))
    digest = hashlib.sha256(desk.setup.read_bytes()).hexdigest()
    assert job["assets"] == [{"name": f"{digest}.tar.gz", "sha256": digest, "bytes": desk.setup.stat().st_size, "extract": True}]
    assert job["repository"] == REPOSITORY and job["release"] == "pod-bundles" and job["token_env"] == GITHUB_TOKEN_ENV
    assert [step["name"] for step in job["steps"]] == ["bootstrap", "worker"] and job["root"] == "/workspace/attribution-study-v2"
    # the volume: created once, in the stated data center
    (volume,) = [json.loads(b) for m, p, b in desk.runpod.log if (m, p) == ("POST", "/v1/networkvolumes")]
    assert volume == {"name": "attribution-dev05", "size": 50, "dataCenterId": "US-MD-1"}
    # the bundle: one asset named by its hash, holding the very bytes (never opened by the launcher)
    (asset,) = [a for a in desk.github.assets.values()]
    assert asset["name"] == f"{digest}.tar.gz" and desk.github.blobs[asset["id"]] == desk.setup.read_bytes()


def test_a_second_launch_refuses_the_duplicate_and_a_named_volume_and_bundle_are_reused(desk):
    desk.launcher().launch(desk.spec())
    uploads = desk.github.uploads
    with pytest.raises(LaunchRefused, match="already exists"):
        desk.launcher().launch(desk.spec())
    assert len([r for r in desk.requests("POST") if r[1] in ("/v1/pods", "/v1/networkvolumes")]) == 2
    # the first pod is stopped by its timer; another host's pod on the same volume name is a new pod
    desk.runpod.pods[0]["desiredStatus"] = "TERMINATED"
    desk.clock.advance(60)
    again = desk.launcher().launch(desk.spec())
    assert again["volume"] == "vol-new-1" and desk.github.uploads == uploads           # volume and bundle reused
    assert len([r for r in desk.requests("POST") if r[1] == "/v1/networkvolumes"]) == 1
    # two volumes of one name are ambiguous; a volume elsewhere is not the one meant; none and no leave to create
    desk.runpod.pods.clear()
    desk.runpod.volumes.append(network_volume("vol-twin") | {"name": "attribution-dev05", "dataCenterId": "US-MD-1"})
    with pytest.raises(LaunchRefused, match="2 network volumes are named"):
        desk.launcher().launch(desk.spec())
    desk.runpod.volumes.pop()
    with pytest.raises(LaunchRefused, match="another data center"):
        desk.launcher().launch(desk.spec(volume={"name": "attribution-dev05", "data_center": "EU-RO-1"}))
    with pytest.raises(LaunchRefused, match="does not allow creating one"):
        desk.launcher().launch(desk.spec(volume={"name": "attribution-dev06", "data_center": "US-MD-1"}))
    assert len([r for r in desk.requests("POST") if r[1] == "/v1/pods"]) == 2


def test_a_price_above_the_limit_creates_nothing_and_a_dearer_pod_is_stopped_not_deleted(desk):
    desk.runpod.gpu_types[0]["securePrice"] = 1.89
    with pytest.raises(LaunchRefused, match="costs 1.89 per hour, above the limit of 1.7: nothing was created"):
        desk.launcher().launch(desk.spec())
    assert desk.requests() == [("POST", "/graphql")] and desk.github.log == []        # not even a bundle was uploaded
    desk.runpod.gpu_types[0]["securePrice"] = 1.59
    desk.runpod.created_cost = 2.10                      # the quoted price was fine; the pod reports another
    with pytest.raises(LaunchRefused, match="was stopped"):
        desk.launcher().launch(desk.spec())
    assert desk.requests("POST")[-2:] == [("POST", "/v1/pods"), ("POST", "/v1/pods/pod-new-2/stop")]
    assert desk.runpod.pods[0]["desiredStatus"] == "EXITED" and len(desk.runpod.pods) == 1
    for missing in ([], [{"id": "NVIDIA A100 80GB PCIe", "securePrice": 1.59}], [{"id": "NVIDIA A100-SXM4-80GB", "securePrice": None}]):
        desk.runpod.gpu_types = missing
        with pytest.raises(LaunchRefused, match="no usable SECURE price"):
            desk.launcher().launch(desk.spec(name="attribution-dev06"))


def test_when_runpod_cannot_place_the_pod_the_volume_stays_and_nothing_is_deleted(desk):
    desk.runpod.create_status = 500
    with pytest.raises(Exception, match="kept failing|answered 500"):
        desk.launcher().launch(desk.spec())
    assert desk.runpod.pods == [] and [v["name"] for v in desk.runpod.volumes] == ["volume-vol-other", "attribution-dev05"]
    desk.runpod.create_status = 201
    assert desk.launcher().launch(desk.spec())["volume"] == "vol-new-1"                 # the next launch reuses it


BAD_SPECS = {
    "a secret given as a value": ({"env": {"RUNPOD_READ_API_KEY": READ_KEY}}, "looks like a credential"),
    "a token given as a value": ({"env": {"HF_TOKEN": "hf_abc"}}, "looks like a credential"),
    "RUNPOD_API_KEY as a secret": ({"secrets": {"RUNPOD_API_KEY": "account_key"}}, "RUNPOD_API_KEY must not be set"),
    "RUNPOD_API_KEY as a reference": ({"env": {"RUNPOD_API_KEY": "{{ RUNPOD_SECRET_account_key }}"}}, "RUNPOD_API_KEY must not be set"),
    "a secret that is not a name": ({"secrets": {"X_TOKEN": "ghp_value with spaces"}}, "name of a RunPod secret"),
    "an unknown key": ({"terminate_after": 5}, "unknown keys"),
    "no price limit": ({"max_price_per_hour": None}, "positive number"),
    "extra overriding the request": ({"extra": {"env": {}}}, "extra may not set"),
    "extra locking the pod": ({"extra": {"locked": True}}, "extra may not set"),
    "a volume without a data center": ({"volume": {"name": "v"}}, "data center"),
    "a job without steps": ({"job": {"root": "/workspace/x"}}, "root and steps"),
    "a bundle without its handling": ({"bundles": [{"path": "x.tar.gz"}]}, "path, extract"),
}


@pytest.mark.parametrize("what", sorted(BAD_SPECS))
def test_a_description_with_a_secret_value_or_an_unknown_field_is_refused_before_any_request(desk, what):
    change, why = BAD_SPECS[what]
    with pytest.raises(LaunchRefused, match=why):
        desk.launcher().launch(desk.spec(**change))
    assert desk.runpod.log == [] and desk.github.log == [] and not desk.record_path.exists()


def test_a_bundle_that_is_not_the_expected_one_is_refused_and_credentials_are_required(desk, monkeypatch):
    with pytest.raises(LaunchRefused, match="does not have the hash the description expects"):
        desk.launcher().launch(desk.spec(bundles=[{"path": "worker-setup.tar.gz", "extract": True, "sha256": "0" * 64}]))
    assert desk.runpod.pods == [] and desk.github.uploads == 0
    monkeypatch.delenv(GITHUB_TOKEN_ENV)
    with pytest.raises(NotConfigured, match=GITHUB_TOKEN_ENV):
        desk.launcher().launch(desk.spec())
    assert desk.runpod.pods == [] and len(desk.runpod.volumes) == 1                   # bundles come before anything billable
    monkeypatch.setenv(GITHUB_TOKEN_ENV, TOKEN)
    monkeypatch.delenv(RUNPOD_ADMIN_KEY_ENV)
    seen = (len(desk.runpod.log), len(desk.github.log))
    with pytest.raises(NotConfigured, match=RUNPOD_ADMIN_KEY_ENV):
        desk.launcher().launch(desk.spec())
    assert (len(desk.runpod.log), len(desk.github.log)) == seen                       # nothing was sent at all


def test_every_request_is_recorded_without_a_secret_and_the_dry_run_contacts_nothing(desk, capsys):
    spec_path = desk.folder / "launch.json"
    spec_path.write_text(json.dumps(desk.spec()))
    assert cli(["launch", "--spec", str(spec_path), "--record", str(desk.record_path), "--project-root", str(desk.folder),
                "--dry-run"]) == 0
    planned = json.loads(capsys.readouterr().out)
    assert planned["dry_run"] is True and planned["request"]["env"]["POD_TIMER_B64_00"]["chars"] > 5000
    assert desk.runpod.log == [] and desk.github.log == [] and not desk.record_path.exists()
    arguments = ["launch", "--spec", str(spec_path), "--record", str(desk.record_path), "--project-root", str(desk.folder),
                 "--runpod-rest-url", f"{desk.runpod.url}/v1", "--runpod-graphql-url", f"{desk.runpod.url}/graphql",
                 "--github-api-url", desk.github.url, "--github-upload-url", desk.github.url]
    assert cli(arguments) == 0
    printed = capsys.readouterr().out
    assert json.loads(printed)["pod"] == "pod-new-2"
    rows = read_jsonl(desk.record_path)
    assert [row["event"] for row in rows][0] == "launch-intended" and rows[-1]["event"] == "launch-done"
    requests = [row["request"] for row in rows if row["event"] in ("runpod", "github")]
    assert requests == ["query gpuTypes", "GET /pods", "create release", "upload bundle", "GET /networkvolumes",
                        "POST /networkvolumes", "POST /pods"]
    created = next(row for row in rows if row.get("request") == "POST /pods")
    assert created["body"]["env"]["POD_TIMER_B64_00"] == {"sha256": hashlib.sha256(
        base64.b64encode(gzip.compress(TIMER_SCRIPT.read_bytes(), 9, mtime=0))).hexdigest(), "chars": planned["request"]["env"]["POD_TIMER_B64_00"]["chars"]}
    assert created["body"]["env"][GITHUB_TOKEN_ENV] == "{{ RUNPOD_SECRET_backup_token }}"   # a reference, as written
    text = desk.record_path.read_text() + printed
    assert all(secret not in text for secret in (KEY, TOKEN))
    assert text.count("Bearer") == text.count("Bearer $RUNPOD_API_KEY")               # only the start command's own text
    assert cli(arguments) == 2 and "already exists" in capsys.readouterr().err         # the duplicate, through the command


def test_the_code_archive_is_deterministic_and_holds_the_package_without_its_tests(tmp_path):
    first = pack_code(PROJECT, tmp_path / "one.tar.gz")
    second = pack_code(PROJECT, tmp_path / "two.tar.gz")
    assert first["sha256"] == second["sha256"] and first["files"] == second["files"] > 15
    with tarfile.open(tmp_path / "one.tar.gz") as archive:
        names = archive.getnames()
    assert "experiments/durability/worker.py" in names and "experiments/durability/pod_timer/pod_timer.py" in names
    assert not any("/tests/" in name or "__pycache__" in name for name in names)
    assert all(name.startswith("experiments/") for name in names)
    with pytest.raises(LaunchRefused, match="never replaced"):
        pack_code(PROJECT, tmp_path / "one.tar.gz")
    assert cli(["pack-code", "--project-root", str(PROJECT), "--out", str(tmp_path / "three.tar.gz")]) == 0


# ----- the job runner, as a real process ------------------------------------------------------------


def wait_for(condition, seconds: float = 60.0, what: str = "condition"):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = condition()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError(f"timed out waiting for {what}")


class PodDisk:
    """What a pod has when its start command runs: the volume, the environment RunPod gives it (with
    the secret resolved), and GitHub (a fake) holding the bundles."""

    def __init__(self, folder: Path) -> None:
        self.folder, self.root = folder, folder / "workspace" / "study"
        self.timer_dir = folder / "workspace" / ".pod-timer"
        self.github = FakeGitHub(REPOSITORY)
        self.bundle = tar_bundle(folder / "setup.tar.gz", {
            "bootstrap.sh": b'echo bootstrapped >> bootstrap-runs.txt\n', "prepared-v2/hidden/hidden.jsonl": b"OPAQUE\n",
            "work.sh": b'echo "worked with $WORK_SETTING" >> work-runs.txt\nexit ${WORK_EXIT:-0}\n'})
        self.asset = self.publish(self.bundle)

    def publish(self, path: Path, stored: bytes | None = None) -> dict:
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        with self.github._lock:
            release = next((r for r in self.github.releases.values() if r["tag_name"] == "pod-bundles"), None)
            if release is None:
                release = {"id": self.github._next(), "tag_name": "pod-bundles", "name": "pod-bundles"}
                self.github.releases[release["id"]] = release
            asset_id = self.github._next()
            self.github.assets[asset_id] = {"id": asset_id, "release": release["id"], "name": f"{digest}.tar.gz", "label": None,
                                            "state": "uploaded", "size": len(data), "digest": None}
            self.github.blobs[asset_id] = data if stored is None else stored
        return {"name": f"{digest}.tar.gz", "sha256": digest, "bytes": len(data), "extract": True}

    def spec(self, **changes) -> dict:
        base = {"version": 1, "root": str(self.root), "repository": REPOSITORY, "release": "pod-bundles",
                "token_env": GITHUB_TOKEN_ENV, "api_url": self.github.url, "assets": [self.asset],
                "files": {"worker.json": '{"host": "dev05"}'},
                "steps": [{"name": "bootstrap", "argv": ["bash", "bootstrap.sh"], "once": True},
                          {"name": "work", "argv": ["bash", "work.sh"], "env": {"WORK_SETTING": "x"}}],
                "start_script": str(self.folder / "no-start-script"), "stop_after_failure_seconds": 300,
                "stop_after_success_seconds": None, "timer_dir": str(self.timer_dir)}
        return {**base, **changes}

    def env(self, spec: dict, **more) -> dict:
        packed = base64.b64encode(gzip.compress(json.dumps(spec).encode())).decode()
        return {"PATH": os.environ["PATH"], "POD_JOB_SPEC_B64": packed, GITHUB_TOKEN_ENV: TOKEN, "RUNPOD_POD_ID": "pod-1", **more}

    def run(self, spec: dict, **more) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", str(JOB_SCRIPT)], env=self.env(spec, **more), capture_output=True,
                              text=True, timeout=120)

    def events(self) -> list[dict]:
        return [json.loads(line) for line in (self.root / ".pod-job" / "job.jsonl").read_text().splitlines()]

    def stop_records(self) -> list[dict]:
        folder = self.timer_dir / "leases"
        return [json.loads(p.read_text()) for p in sorted(folder.glob("*.json"))] if folder.is_dir() else []


@pytest.fixture
def disk(tmp_path):
    built = PodDisk(tmp_path)
    yield built
    assert built.github.leaks == []                      # the token never went to the redirected download
    built.github.close()


def test_the_job_runner_fetches_checks_unpacks_and_runs_the_steps_with_receipts(disk):
    done = disk.run(disk.spec())
    assert done.returncode == 0, done.stdout + done.stderr
    assert (disk.root / "bootstrap-runs.txt").read_text() == "bootstrapped\n"
    assert (disk.root / "work-runs.txt").read_text() == "worked with x\n"
    assert (disk.root / "prepared-v2" / "hidden" / "hidden.jsonl").read_bytes() == b"OPAQUE\n"     # placed, never read
    assert json.loads((disk.root / "worker.json").read_text()) == {"host": "dev05"}
    receipt = json.loads((disk.root / ".pod-job" / "steps" / "work" / "001" / "receipt.json").read_text())
    assert receipt["exit_code"] == 0 and receipt["command"] == ["bash", "work.sh"] and receipt["elapsed_seconds"] >= 0
    assert [e["event"] for e in disk.events()] == ["bundle-fetched", "file-written", "step-started", "step-ended",
                                                   "step-started", "step-ended", "job-complete"]
    assert disk.stop_records() == []                     # success: the worker itself asks the timer (not this runner)
    downloads = [had for method, path, had in disk.github.log if path.startswith("/_blob/")]
    assert downloads == [False]                          # the signed download carried no token
    # the container restarts: nothing is fetched again, the once-step is skipped, the work step runs again
    requests = len(disk.github.log)
    again = disk.run(disk.spec())
    assert again.returncode == 0 and len(disk.github.log) == requests
    assert (disk.root / "bootstrap-runs.txt").read_text() == "bootstrapped\n"
    assert (disk.root / "work-runs.txt").read_text() == "worked with x\nworked with x\n"
    assert [e["event"] for e in disk.events()][-5:] == ["bundle-present", "step-skipped", "step-started", "step-ended",
                                                        "job-complete"]
    assert TOKEN not in done.stdout + again.stdout + (disk.root / ".pod-job" / "job.jsonl").read_text()
    done = disk.run(disk.spec(stop_after_success_seconds=90))        # a job that asks for the stop when it is done
    (record,) = disk.stop_records()
    assert record["pod"] == "pod-1" and record["purpose"] == "finish" and record["kind"] == "durability pod-timer lease v1"
    stop, published = dt.datetime.fromisoformat(record["stop_at_utc"]), dt.datetime.fromisoformat(record["published_utc"])
    assert (stop - published).total_seconds() == 90 and published.strftime("%Y%m%dT%H%M%SZ") == record["lease"][:16]


def test_a_failing_step_ends_the_job_and_asks_the_timer_to_stop_the_pod(disk):
    spec = disk.spec(steps=[{"name": "bootstrap", "argv": ["bash", "bootstrap.sh"], "once": True},
                            {"name": "work", "argv": ["bash", "work.sh"], "env": {"WORK_EXIT": "3"}},
                            {"name": "later", "argv": ["bash", "-c", "echo later > later.txt"]}])
    done = disk.run(spec)
    assert done.returncode == 1 and not (disk.root / "later.txt").exists()
    assert json.loads((disk.root / ".pod-job" / "steps" / "work" / "001" / "receipt.json").read_text())["exit_code"] == 3
    failed = disk.events()[-1]
    assert failed["event"] == "job-failed" and "work ended with status 3" in failed["reason"] and failed["stop_after_seconds"] == 300
    (record,) = disk.stop_records()
    assert record["lease"] == failed["stop_record"] and record["reason"] == "the pod job failed"
    # with the failure delay switched off, nothing is asked of the timer
    quiet = disk.run({**spec, "stop_after_failure_seconds": None})
    assert quiet.returncode == 1 and len(disk.stop_records()) == 1
    missing = disk.run(disk.spec(steps=[{"name": "ghost", "argv": ["/no/such/program"]}]))
    assert missing.returncode == 1 and "not started" in disk.events()[-1]["reason"]


def test_a_bundle_that_is_wrong_missing_or_unsafe_is_refused_before_any_step(disk, tmp_path):
    other = tar_bundle(tmp_path / "other.tar.gz", {"bootstrap.sh": b"echo tampered > tampered.txt\n"})
    tampered = disk.publish(disk.bundle, stored=other.read_bytes())            # the right name, other bytes
    disk.github.assets.pop(next(i for i, a in disk.github.assets.items() if a["name"] == disk.asset["name"]))
    done = disk.run(disk.spec(assets=[tampered]))
    assert done.returncode == 1 and "does not have the described hash or size" in disk.events()[-1]["reason"]
    assert not (disk.root / "bootstrap.sh").exists() and not (disk.root / "tampered.txt").exists()
    assert len(disk.stop_records()) == 1
    absent = {"name": "f" * 64 + ".tar.gz", "sha256": "f" * 64, "bytes": 1, "extract": True}
    assert disk.run(disk.spec(assets=[absent])).returncode == 1 and "is not in the release" in disk.events()[-1]["reason"]
    escaping = tmp_path / "escape.tar.gz"
    with tarfile.open(escaping, "w:gz") as archive:
        info = tarfile.TarInfo("../outside.txt")
        info.size = 2
        archive.addfile(info, io.BytesIO(b"x\n"))
        link = tarfile.TarInfo("link")
        link.type, link.linkname = tarfile.SYMTYPE, "/etc/passwd"
        archive.addfile(link)
    done = disk.run(disk.spec(assets=[disk.publish(escaping)]))
    assert done.returncode == 1 and "not a plain file or folder inside the study root" in disk.events()[-1]["reason"]
    assert not (disk.root.parent / "outside.txt").exists() and not (disk.root / "link").exists()
    # without the token nothing is fetched, and the reason does not name it
    done = subprocess.run([sys.executable, "-I", str(JOB_SCRIPT)], env={k: v for k, v in disk.env(disk.spec(assets=[absent])).items()
                                                                       if k != GITHUB_TOKEN_ENV}, capture_output=True, text=True)
    assert done.returncode == 1 and "the backup token is not in the environment" in done.stdout


def test_files_are_never_replaced_and_an_unusable_description_starts_nothing(disk):
    assert disk.run(disk.spec()).returncode == 0
    changed = disk.run(disk.spec(files={"worker.json": '{"host": "dev06"}'}))
    assert changed.returncode == 1 and "exists with other content" in disk.events()[-1]["reason"]
    assert json.loads((disk.root / "worker.json").read_text()) == {"host": "dev05"}
    for bad in ({"version": 2}, {"root": "relative"}, {"files": {"../x": "y"}}, {"files": {"/abs": "y"}},
                {"steps": [{"name": "x"}]}, {"assets": [{"name": "x", "sha256": "short", "bytes": 1, "extract": True}]},
                {"surprise": 1}):
        refused = disk.run(disk.spec(**bad), POD_TIMER_DIR=str(disk.timer_dir))
        assert refused.returncode == 2 and json.loads(refused.stdout.splitlines()[-1])["event"] == "job-refused", bad
    garbage = subprocess.run([sys.executable, "-I", str(JOB_SCRIPT)], env={"PATH": os.environ["PATH"], "POD_JOB_SPEC_B64": "!!"},
                             capture_output=True, text=True)
    assert garbage.returncode == 2
    source = JOB_SCRIPT.read_text()
    code = source.split('"""', 2)[2]
    for word in ("terminate", "DELETE", "rmtree", "unlink", "os.remove", "runpodctl", "rest.runpod.io"):
        assert word not in code, word                    # it stops nothing itself and deletes nothing
    imports = {line.split()[1].split(".")[0] for line in source.splitlines() if line.startswith(("import ", "from "))}
    assert imports <= {"__future__", "base64", "datetime", "gzip", "hashlib", "json", "os", "re", "subprocess", "sys",
                       "tarfile", "time", "urllib"}


START_TOOLS = ("bash", "base64", "gunzip", "sha256sum", "python3")


@pytest.mark.skipif(any(shutil.which(tool) is None for tool in START_TOOLS), reason=f"needs {START_TOOLS} on the PATH, as in the pod")
@pytest.mark.parametrize("damage", [None, "the job runner cut short"])
def test_the_start_command_runs_the_timer_and_under_it_the_job_runner(disk, tmp_path, damage):
    made = settings(state_dir=str(disk.timer_dir), cap_seconds=3600.0, install_dir=str(tmp_path / "opt"), job_script=JOB_SCRIPT)
    tools = tmp_path / "bin"
    tools.mkdir()
    calls = tmp_path / "runpodctl.log"
    (tools / "runpodctl").write_text(f'#!/bin/sh\necho "$@" >> "{calls}"\n')
    (tools / "runpodctl").chmod(0o755)
    env = {**disk.env(disk.spec()), **made["env"], "PATH": f"{tools}{os.pathsep}{os.environ['PATH']}",
           "POD_TIMER_POLL_SECONDS": "0.1", "POD_TIMER_REST_URL": "http://127.0.0.1:9/v1"}
    if damage:
        env["POD_JOB_B64_00"] = env["POD_JOB_B64_00"][:200]
    process = subprocess.Popen(made["docker_start_cmd"], env=env, start_new_session=True, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    try:
        if damage:
            wait_for(calls.exists, what="the start command's own stop")
            assert calls.read_text().splitlines()[0] == "pod stop pod-1" and not (disk.root / "work-runs.txt").exists()
            return
        wait_for((disk.root / "work-runs.txt").exists, what="the job's work step")
        beat = wait_for(lambda: (disk.timer_dir / "heartbeat.json").exists() and json.loads(
            (disk.timer_dir / "heartbeat.json").read_text()), what="the timer's heartbeat")
        assert beat["supervised"] is True and beat["governing"]["source"] == "cap" and not calls.exists()
        assert (tmp_path / "opt" / "pod_job.py").read_bytes() == JOB_SCRIPT.read_bytes()
        wait_for(lambda: any(e["event"] == "job-complete" for e in disk.events()), what="the job to complete")
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)
