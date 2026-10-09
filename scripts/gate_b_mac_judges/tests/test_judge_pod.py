"""Tests of the judge pod path (pod/) with fakes only: no RunPod, no Hub, no network, no model, no GPU, no real bank.

Written 8 October 2026; revised 8 October 2026 (20:55 UTC, clock checked) after the review (stop safety, one launch
per tag, the budget guard's view, fetch retries, orphan stops, the price rule, torch and the text path); revised again
8 October 2026 (21:55 UTC, clock checked) after the second review (F1 to F13: SIGQUIT, the S1 child-process tests
ported from the reviewers, nohup, dead stdout and stderr at exit, the fetch order, the salvage budget, orphan names, a
lost create reply, record appends, the budget check after the create, smoke-run verdicts, the parity cache SHA-256 and
the zsh blocks); revised a third time 8 October 2026 (22:48 UTC, clock checked) after the third review (G1 to G4: a
reconcile cut short by a real signal runs again, an orphan stop on a full disk, a 5xx create reply counted as lost, a
budget.py that hangs or cannot start). The fake host
simulates the pod in a scratch folder: it unpacks the real bundle and runs the real pod_job.py (verify, run with a fake
judge, status, sums) in this process; ssh, scp, the RunPod API and the budget guard are fakes. The signal tests run the
launcher with real signals in a child process. The real Mac data is touched only by the skippable checks (snapshot
metadata, the Gate A Mac labels, the budget kit's budget.py read as code), which print and store no text. Every launch
writes under the test's tmp_path: judge_pod.JUDGE_POD_ROOT, podhost.JUDGE_HOSTS and podhost.BUDGET_LOCK are replaced.
"""
from __future__ import annotations

import ast
import builtins
import contextlib
import datetime as dt
import errno
import fcntl
import fnmatch
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import types

import pytest

HERE = pathlib.Path(__file__).resolve().parent
MODULES = HERE.parent
POD_DIR = MODULES / "pod"
for _p in (HERE, MODULES, POD_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import synth  # noqa: E402
from synth import MARK_A, MARK_P, sha  # noqa: E402

import bundle as bundle_mod  # noqa: E402
import cache as cache_mod  # noqa: E402
import harmbench_files as hb  # noqa: E402
import judge_pod  # noqa: E402
import parity  # noqa: E402
import pod_job  # noqa: E402
import pod_judge  # noqa: E402
import podhost  # noqa: E402
import units as units_mod  # noqa: E402
import write_files  # noqa: E402
from common import HARMBENCH, Refusal  # noqa: E402
from test_gate_b_judges import text_names_in_sinks  # noqa: E402

PIDS = tuple(f"p-{i:03d}" for i in range(1, 4))
SECRET_ENV = {"RUNPOD_OPERATOR_API_KEY": "rpa_" + "K" * 24, "HF_TOKEN": "hf_" + "T" * 34}
REAL_JUDGE_HOSTS = podhost.JUDGE_HOSTS              # the real layout, read before any test replaces it
CACHE_REL, RECORD_REL = judge_pod.CACHE_REL, judge_pod.RECORD_REL
TOK_OK = {"mac": "a" * 64, "pod": "a" * 64, "identical": True}


@pytest.fixture(autouse=True)
def _launches_write_under_tmp(tmp_path, monkeypatch):
    """No test writes to the real tmp/judge-pod, tmp/family-probe-judge or the kits' budget lock."""
    monkeypatch.setattr(judge_pod, "JUDGE_POD_ROOT", tmp_path / "judge-pod-root")
    monkeypatch.setattr(podhost, "JUDGE_HOSTS", tmp_path / "judge-hosts")
    monkeypatch.setattr(podhost, "BUDGET_LOCK", tmp_path / "budget.lock")


def no_text_or_secret(*blobs) -> None:
    for b in blobs:
        s = b.decode("utf-8", "replace") if isinstance(b, bytes) else str(b)
        assert MARK_P not in s and MARK_A not in s
        assert not [n for n, p in judge_pod.SECRET_PATTERNS.items() if p.search(s)], s[:200]
        assert SECRET_ENV["RUNPOD_OPERATOR_API_KEY"] not in s and SECRET_ENV["HF_TOKEN"] not in s


def make_prepared(root: pathlib.Path, pids=PIDS, name: str = "prepared-test") -> tuple[pathlib.Path, str]:
    """A synthetic prepared set with the real layout: banks/dev.jsonl, manifest.json listing it, manifest.sha256 =
    SHA-256(manifest.json); plus hidden/ and selector/ files that must never enter a bundle."""
    prepared = root / name
    (prepared / "banks").mkdir(parents=True)
    rows = [{"kind": "harm", "prompt_id": p, "prompt": f"{MARK_P} harm prompt {p}"} for p in pids]
    rows.append({"kind": "overrefusal", "prompt_id": "o-001", "prompt": f"{MARK_P} benign"})
    synth.write_jsonl(prepared / "banks" / "dev.jsonl", rows)
    synth.write_jsonl(prepared / "banks" / "test.jsonl", [{"kind": "harm", "prompt_id": "t-1", "prompt": MARK_P}])
    for sub in ("hidden", "selector"):
        (prepared / sub).mkdir()
        (prepared / sub / "x.jsonl").write_text(json.dumps({"text": MARK_P}) + "\n")
    manifest = json.dumps({"kind": "synthetic", "files": {"banks/dev.jsonl": sha((prepared / "banks/dev.jsonl").read_bytes())}},
                          sort_keys=True).encode()
    (prepared / "manifest.json").write_bytes(manifest)
    (prepared / "manifest.sha256").write_text(sha(manifest) + "\n")
    return prepared, sha(manifest)


def setup_units(tmp_path, monkeypatch, hosts=("hostA",), pids=PIDS, samples=2):
    prepared, manifest = make_prepared(tmp_path, pids)
    monkeypatch.setattr(bundle_mod, "KNOWN_PREPARED", {prepared.name: manifest})
    retrieved = tmp_path / "kit" / "retrieved"
    units = []
    for i, h in enumerate(hosts):
        unit = synth.make_unit(retrieved, h, f"{1101 + i}-a0-e1-a1", seed=1101 + i, manifest=manifest, pids=pids,
                               samples=samples, completed_utc=f"2026-10-08T0{i + 1}:00:00+00:00")
        (unit / "eval/e1/harm_prompts.jsonl").write_text(json.dumps({"prompt": MARK_P}) + "\n")   # sealed, not shipped
        synth.seal(unit, target="e1", arm="a0", seed=1101 + i, completed_utc=f"2026-10-08T0{i + 1}:00:00+00:00")
        units.append(unit)
    return retrieved, prepared, manifest, units


def args_for(cmd, tag, out, retrieved, prepared, *extra):
    """The command line; `out` is used by bundle only (a launch's folder is JUDGE_POD_ROOT/<tag>)."""
    where = ["--out", str(out)] if cmd == "bundle" else []
    return judge_pod.parser().parse_args([cmd, "--tag", tag, *where, "--run-root", str(retrieved),
                                          "--prepared", str(prepared), "--expect-greedy", "0", "--expect-sampled", "0",
                                          *extra])


def extract(tar: pathlib.Path, dest: pathlib.Path) -> pathlib.Path:
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar) as t:
        t.extractall(dest, filter="data")
    return dest / "bundle"


# ------------------------------------------------------------------------------------------------ bundle and manifest

def test_bundle_is_deterministic_and_holds_only_the_listed_files(tmp_path, monkeypatch):
    retrieved, prepared, manifest, units = setup_units(tmp_path, monkeypatch, hosts=("hostA", "hostB"))
    built = []
    for i in (1, 2):                                                   # the same inputs built twice, in two folders
        (tmp_path / f"out{i}").mkdir()
        built.append(judge_pod.build(args_for("bundle", "t1", tmp_path / f"out{i}", retrieved, prepared),
                                     tmp_path / f"out{i}"))
    assert built[0]["tar_sha256"] == built[1]["tar_sha256"] == sha(built[0]["tar"].read_bytes())
    assert built[0]["manifest_sha256"] == built[1]["manifest_sha256"]
    root = extract(built[0]["tar"], tmp_path / "x")
    m = bundle_mod.verify_bundle(root)
    files = set(m["files"])
    assert {f"tool/{n}" for n in bundle_mod.TOOL_FILES} | {f"tool/pod/{n}" for n in bundle_mod.POD_FILES} <= files
    assert {"prepared/prepared-test/manifest.sha256", "prepared/prepared-test/banks/dev.jsonl"} <= files
    assert not [f for f in files if "hidden" in f or "selector" in f or "test.jsonl" in f or "manifest.json" in f]
    assert not [f for f in files if f.endswith("harm_prompts.jsonl")]                 # only the four judge files
    for nn, unit in (("00", units[0]), ("01", units[1])):
        for name in ("job.json", "COMPLETE.json"):
            assert m["files"][f"units/{nn}/{name}"] == sha((unit / name).read_bytes())
        for name in units_mod.EVAL_FILES.values():
            assert m["files"][f"units/{nn}/eval/e1/{name}"] == sha((unit / "eval/e1" / name).read_bytes())
    for rel, digest in m["files"].items():                                            # every listed hash is the file's
        assert sha((root / rel).read_bytes()) == digest
    for name in bundle_mod.TOOL_FILES:                                                # the Mac judge's modules, unchanged
        assert m["files"][f"tool/{name}"] == sha((MODULES / name).read_bytes())
    entries = [e for g in m["groups"] for e in g["units"]]
    assert [e["complete_sha256"] for e in entries] == [sha((u / "COMPLETE.json").read_bytes()) for u in units]
    assert m["groups"][0]["prepared"] == {"name": "prepared-test", "dir": "prepared/prepared-test", "manifest_sha256": manifest,
                                          "dev_bank_sha256": sha((prepared / "banks/dev.jsonl").read_bytes())}
    rec = json.loads((tmp_path / "out1/bundle-record.json").read_bytes())
    assert rec["bundle_sha256"] == built[0]["tar_sha256"] and rec["items"] == {"greedy": 6, "sampled": 12}
    no_text_or_secret((tmp_path / "out1/bundle-record.json").read_bytes(), (root / "job-manifest.json").read_bytes())


@pytest.mark.parametrize("damage", ["edit_answer", "stray_file", "missing_file", "manifest_complete", "manifest_target",
                                    "unpinned_prepared", "bank_edit"])
def test_pod_verify_refuses_a_changed_bundle(tmp_path, monkeypatch, damage):
    retrieved, prepared, manifest, _ = setup_units(tmp_path, monkeypatch)
    (tmp_path / "out").mkdir()
    built = judge_pod.build(args_for("bundle", "t1", tmp_path / "out", retrieved, prepared), tmp_path / "out")
    root = extract(built["tar"], tmp_path / "x")
    mpath = root / "job-manifest.json"
    m = json.loads(mpath.read_bytes())
    if damage == "edit_answer":
        p = root / "units/00/eval/e1/samples.jsonl"
        p.write_bytes(p.read_bytes() + b"\n")
    elif damage == "stray_file":
        (root / "units/00/eval/e1/.DS_Store").write_bytes(b"x")
    elif damage == "missing_file":
        (root / "units/00/eval/e1/guard.jsonl").unlink()
    elif damage == "manifest_complete":
        m["groups"][0]["units"][0]["complete_sha256"] = "0" * 64
    elif damage == "manifest_target":
        m["groups"][0]["units"][0]["target"] = "init"
    elif damage == "unpinned_prepared":
        monkeypatch.setattr(bundle_mod, "KNOWN_PREPARED", {"prepared-kt-dolly-olmo2": bundle_mod.KNOWN_PREPARED["prepared-test"]})
    elif damage == "bank_edit":
        bank = root / "prepared/prepared-test/banks/dev.jsonl"
        bank.write_bytes(bank.read_bytes() + b"\n")
        m["files"]["prepared/prepared-test/banks/dev.jsonl"] = sha(bank.read_bytes())     # listed, but not the recorded bank
    mpath.write_bytes(json.dumps(m).encode())
    with pytest.raises(Refusal) as e:
        bundle_mod.verify_bundle(root)
    no_text_or_secret(str(e.value))
    assert pod_job.main(["verify", "--bundle", str(root)]) == 2


@pytest.mark.parametrize("damage", ["name_not_pinned", "manifest_json_differs", "dev_bank_differs", "unit_other_manifest"])
def test_mac_side_prepared_pins_refuse_before_any_bundle(tmp_path, monkeypatch, damage):
    retrieved, prepared, manifest, units = setup_units(tmp_path, monkeypatch)
    if damage == "name_not_pinned":
        monkeypatch.setattr(bundle_mod, "KNOWN_PREPARED", {"other": manifest})
    elif damage == "manifest_json_differs":
        (prepared / "manifest.json").write_bytes((prepared / "manifest.json").read_bytes() + b" ")
    elif damage == "dev_bank_differs":
        (prepared / "banks/dev.jsonl").write_bytes((prepared / "banks/dev.jsonl").read_bytes() + b"\n")
    elif damage == "unit_other_manifest":
        other, other_manifest = make_prepared(tmp_path / "o", pids=("z-001",), name="prepared-other")
        monkeypatch.setattr(bundle_mod, "KNOWN_PREPARED", {"prepared-other": other_manifest})
        prepared = other
    out = judge_pod.JUDGE_POD_ROOT / "t1"
    a = args_for("launch", "t1", None, retrieved, prepared)
    host = FakeHost(tmp_path / "remote")
    assert judge_pod.launch(a, host=host, signals=False) == judge_pod.EXIT_REFUSED
    assert host.calls == [] and not (out / "bundle.tar.gz").exists()


# ------------------------------------------------------------------------------------------------ pod_job with a fake judge

def built_bundle(tmp_path, monkeypatch, **kw):
    retrieved, prepared, manifest, units = setup_units(tmp_path, monkeypatch, **kw)
    (tmp_path / "out").mkdir()
    built = judge_pod.build(args_for("bundle", "t1", tmp_path / "out", retrieved, prepared), tmp_path / "out")
    return extract(built["tar"], tmp_path / "pod"), units, built


def fake_env(device):
    return {"device": device, "gpu": "FAKE GPU", "torch": "2.8.0+cu128", "transformers": "4.56.2"}


def run_job(root, cache, record, factory, *extra):
    return pod_job.main(["run", "--bundle", str(root), "--cache", str(cache), "--record", str(record), *extra],
                        judge_factory=factory, env_probe=fake_env)


def test_pod_job_writes_the_tool_cache_and_resumes(tmp_path, monkeypatch, capsys):
    root, units, built = built_bundle(tmp_path, monkeypatch, hosts=("hostA", "hostB"))
    cache, record = tmp_path / "pod/out/harmbench-pod.jsonl", tmp_path / "pod/out/run-record.json"
    labels = {("greedy", "p-001", None): "yes", ("sampled", "p-002", 1): "yes", ("sampled", "p-003", 0): "unparsed"}
    calls = {}
    assert run_job(root, cache, record, synth.fake_factory(labels, calls), "--limit", "4") == 0   # partial
    assert len(cache_mod.Cache(cache, HARMBENCH)) == 4 and calls["judged"] == 4
    assert run_job(root, cache, record, synth.fake_factory(labels, calls)) == 0                  # resumes
    assert calls["judged"] == 18                                                                  # 2 units x 9, each once
    assert run_job(root, cache, record, synth.fake_factory(labels, calls)) == 0                  # nothing new
    assert calls["judged"] == 18 and calls["factory"] == 2
    lines = [json.loads(x) for x in cache.read_bytes().split(b"\n") if x.strip()]
    assert len(lines) == 18 and all(set(r) == cache_mod.RECORD_KEYS for r in lines)
    assert all(r["judge"] == HARMBENCH and r["source"] == "judged" for r in lines)
    by_unit = {u: sha((u / "COMPLETE.json").read_bytes()) for u in units}
    assert {r["complete_sha256"] for r in lines} == set(by_unit.values())
    got = {(r["mode"], r["prompt_id"], r["sample_index"]): r["label"] for r in lines if r["complete_sha256"] == by_unit[units[0]]}
    assert got[("greedy", "p-001", None)] == "yes" and got[("sampled", "p-003", 0)] == "unparsed"
    assert sum(v == "no" for v in got.values()) == 6
    rec = json.loads(record.read_bytes())
    assert rec["device"] == "cuda" and rec["judge"] == HARMBENCH and rec["model_revision"] == HARMBENCH["revision"]
    assert rec["exit"] == 0 and rec["environment"]["gpu"] == "FAKE GPU"
    assert rec["bundle_manifest_sha256"] == built["manifest_sha256"] == sha((root / "job-manifest.json").read_bytes())
    assert rec["cache"] == {"sha256": sha(cache.read_bytes()), "records": 18}
    assert rec["pins"]["template_sha256"] == hb.TEMPLATE_SHA256
    # the pod's cache is the Mac tool's cache: write_files builds the judge file from it for the Mac's copy of the unit
    mac_units, _ = units_mod.enumerate_units([tmp_path / "kit/retrieved"])
    doc, report = write_files.build_file("harmbench", mac_units[0], cache_mod.Cache(cache, HARMBENCH))
    assert doc["greedy"] == {"n": 3, "harm": 1, "unparsed": 0} and doc["sampled"] == {"n": 6, "harm": 1, "unparsed": 1}
    io_ = capsys.readouterr()
    no_text_or_secret(io_.out, io_.err, cache.read_bytes(), record.read_bytes())


def test_pod_job_sigterm_stops_with_exit_5_and_resumes(tmp_path, monkeypatch):
    root, units, _ = built_bundle(tmp_path, monkeypatch)
    cache, record = tmp_path / "pod/out/c.jsonl", tmp_path / "pod/out/r.json"
    calls = {}
    base = synth.fake_factory({}, calls)

    def stopping(pairs):
        judge = base(pairs)

        def j(prompt, answer):
            res = judge(prompt, answer)
            if calls["judged"] == 2:
                os.kill(os.getpid(), signal.SIGTERM)
            return res
        return j
    assert run_job(root, cache, record, stopping) == pod_job.EXIT_STOPPED
    assert len(cache_mod.Cache(cache, HARMBENCH)) == 2 and json.loads(record.read_bytes())["exit"] == 5
    assert run_job(root, cache, record, synth.fake_factory({}, calls)) == 0
    assert len(cache_mod.Cache(cache, HARMBENCH)) == 9


def test_pod_job_refusal_and_error_are_recorded(tmp_path, monkeypatch):
    root, _, _ = built_bundle(tmp_path, monkeypatch)
    cache, record = tmp_path / "pod/out/c.jsonl", tmp_path / "pod/out/r.json"

    def bad_label(pairs):
        return lambda p, a: {"label": "maybe"}
    assert run_job(root, cache, record, bad_label) == 2
    rec = json.loads(record.read_bytes())
    assert rec["exit"] == 2 and "label outside" in rec["refused"]

    def boom(pairs):
        raise ZeroDivisionError("x")
    record.unlink()
    assert run_job(root, cache, record, boom) == 1
    assert json.loads(record.read_bytes())["error"] == "ZeroDivisionError"


def test_pod_job_status_and_sums_print_whitelisted_counts_only(tmp_path, capsys):
    root = tmp_path / "judge"
    (root / "out").mkdir(parents=True)
    (root / "STARTED.json").write_text("{}")
    (root / "STEP").write_text("run\n")
    (root / "out/job.log").write_text(
        json.dumps({"event": "progress", "judged": 50, "of": 800, "sec_per_item": 0.07, "eta_min": 0.9,
                    "text": MARK_A, "prompt": MARK_P}) + "\n"
        + f"Traceback (most recent call last): {MARK_A}\n" + json.dumps({"event": "unknown", "x": MARK_A}) + "\n")
    assert pod_job.main(["status", "--root", str(root)]) == 0
    st = json.loads(capsys.readouterr().out)
    assert st == {"started": True, "step": "run", "done": None,
                  "progress": {"event": "progress", "judged": 50, "of": 800, "sec_per_item": 0.07, "eta_min": 0.9}}
    (root / "DONE.json").write_text(json.dumps({"exit": 0, "step": "done", "utc": "x"}))
    (root / "out/harmbench-pod.jsonl").write_bytes(b"abc")
    assert pod_job.main(["sums", "--root", str(root)]) == 0
    sums = json.loads(capsys.readouterr().out)["files"]
    assert sums["out/harmbench-pod.jsonl"] == sha(b"abc") and sums["out/run-record.json"] is None
    assert "out/job.log" not in sums and "run.log" not in sums


# ------------------------------------------------------------------------------------------------ judge_pod with a fake host

class FakeHost:
    """The pod in a scratch folder. run() recognises judge_pod's remote commands and runs the real pod_job.py on the
    unpacked bundle (a fake judge); ssh, scp, the API and the budget guard are fakes. fail: step -> exception or code."""

    GPU = podhost.GPU

    def __init__(self, remote: pathlib.Path, allowed=True, fail=None, stop_confirms=(True,), mode="finish",
                 corrupt_fetch=None, factory=None, create_error=None, orphans=0):
        self.remote = pathlib.Path(remote)
        self.allowed = list(allowed) if isinstance(allowed, (list, tuple)) else allowed   # a list: one per check
        self.fail, self.mode = dict(fail or {}), mode
        self.stop_confirms = list(stop_confirms)
        self.corrupt_fetch, self.create_error = corrupt_fetch, create_error
        self.calls, self.pod_id, self.cap_stop_utc, self.shortened, self.orphans = [], None, None, 0, 0
        self.factory = factory or synth.fake_factory({("greedy", "p-001", None): "yes"}, {})
        self.orphans = orphans
        self.status = None                      # the fake pod: RUNNING after create, EXITED after a confirmed stop
        self.fetch_timeouts = []                # None: podhost's own scp timeout; a number: the salvage's budget

    def _maybe_fail(self, step):
        f = self.fail.get(step)
        if isinstance(f, BaseException) or (isinstance(f, type) and issubclass(f, BaseException)):
            raise f
        return f

    @contextlib.contextmanager
    def budget_lock(self):
        self.calls.append("lock")
        yield

    def reconcile(self):
        self.calls.append("reconcile")
        self._maybe_fail("reconcile")

    def budget_check(self, hours, price):
        self.calls.append(("budget_check", hours, price))
        ok = self.allowed.pop(0) if isinstance(self.allowed, list) else self.allowed
        return ok, {"balance": 20.0, "allowed": ok, "exit": 0 if ok else 3}

    def create(self, cap_hours):
        self.calls.append(("create", cap_hours))
        if self.create_error is not None:
            pod_id, err = self.create_error
            self.pod_id = pod_id
            self.status = "RUNNING" if pod_id else None
            # the real host lists the pods before it raises a HostError (a refused create, a lost reply, the price
            # check): the orphan check is done; an interrupt (KeyboardInterrupt, Interrupted) leaves it to finish()
            self.orphan_check_done = (isinstance(err, podhost.HostError)
                                      and not isinstance(err, podhost.StopUnconfirmed))
            raise err
        self.pod_id, self.status = "pod-fake-1", "RUNNING"
        self.cap_stop_utc = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=cap_hours)).isoformat(timespec="seconds")
        return {"id": self.pod_id, "name": "attribution-judge-t1", "costPerHr": 1.79, "cap_stop_utc": self.cap_stop_utc}

    def wait_ssh(self, seconds):
        self.calls.append("wait_ssh")
        self._maybe_fail("wait_ssh")

    def check(self):
        self.calls.append("check")
        self._maybe_fail("check")
        return {"gpu": self.GPU, "timer_stop_utc": self.cap_stop_utc}

    def send(self, local, rel, digest):
        self.calls.append(("send", rel))
        self._maybe_fail("send")
        assert sha(pathlib.Path(local).read_bytes()) == digest
        (self.remote / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.remote / rel).write_bytes(pathlib.Path(local).read_bytes())

    def _pod_job(self, argv, **kw):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = pod_job.main(argv, **kw)
        return code, buf.getvalue()

    def _start_job(self, limit, factory):
        extra = ["--limit", str(limit)] if limit else []
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            code = pod_job.main(["run", "--bundle", str(self.remote / "bundle"), "--cache",
                                 str(self.remote / "out/harmbench-pod.jsonl"), "--record",
                                 str(self.remote / "out/run-record.json"), *extra], judge_factory=factory,
                                env_probe=fake_env)
        (self.remote / "out/job.log").write_text(log.getvalue())
        (self.remote / "DONE.json").write_text(json.dumps({"exit": code, "step": "done" if code == 0 else "run",
                                                           "utc": "2026-10-08T00:00:00Z"}))

    def run(self, command, timeout=120, stdin_path=None):
        self.calls.append(("run", command.split("\n")[0][:40]))
        if "tarfile.open" in command:
            f = self._maybe_fail("unpack")
            if f:
                return f, ""
            with tarfile.open(self.remote / "bundle.tar.gz") as t:
                t.extractall(self.remote, filter="data")
            return self._pod_job(["verify", "--bundle", str(self.remote / "bundle")])
        if "nohup bash" in command:
            f = self._maybe_fail("start")
            if f:
                return f, ""
            (self.remote / "out").mkdir(parents=True, exist_ok=True)
            (self.remote / "STARTED.json").write_text("{}")
            m = re.search(r"--limit (\d+)", command)
            if self.mode == "finish":
                self._start_job(int(m.group(1)) if m else None, self.factory)
            return 0, ""
        if " status --root" in command:
            f = self._maybe_fail("status")
            if f:
                return f, ""
            return self._pod_job(["status", "--root", str(self.remote)])
        if " sums --root" in command:
            f = self._maybe_fail("sums")
            if f:
                return f, ""
            return self._pod_job(["sums", "--root", str(self.remote)])
        if command.startswith("pkill"):
            self.calls.append("terminate")
            if self.mode == "hang" and not (self.remote / "DONE.json").exists():
                calls = {}
                base = synth.fake_factory({}, calls)

                def stopping(pairs):
                    judge = base(pairs)

                    def j(p, a):
                        res = judge(p, a)
                        if calls["judged"] == 2:
                            os.kill(os.getpid(), signal.SIGTERM)
                        return res
                    return j
                self._start_job(None, stopping)
            return 0, ""
        return 0, ""

    def fetch(self, rel, local, timeout=None):
        self.calls.append(("fetch", rel))
        self.fetch_timeouts.append(timeout)
        self._maybe_fail("fetch")
        data = (self.remote / rel).read_bytes()
        if self.corrupt_fetch == rel:
            data += b"x"
        pathlib.Path(local).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(local).write_bytes(data)

    def stop_orphans(self, why):
        self.calls.append("stop_orphans")
        if isinstance(self.orphans, BaseException):
            raise self.orphans
        return self.orphans

    def stop(self):
        self.calls.append("stop")
        ok = self.stop_confirms.pop(0) if self.stop_confirms else True
        if ok:
            self.status = "EXITED"
        return {"utc": "x", "status": 200, "attempts": 1, "desiredStatus": "EXITED" if ok else "RUNNING", "confirmed": ok}

    def shorten_timer(self, seconds, script):
        self.calls.append(("shorten_timer", seconds))
        assert pathlib.Path(script).name == "extend_cap.py" and pathlib.Path(script).is_file()
        self.shortened += 1
        return True


class Clock:
    def __init__(self):
        self.t = time.time()

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def read_log(out):
    return [json.loads(x) for x in (out / "judge-pod-log.jsonl").read_bytes().split(b"\n") if x.strip()]


def launch_with(tmp_path, monkeypatch, host_kw=None, extra=(), signals=False, hosts=("hostA",), host_cls=None, tag="t1"):
    for k, v in SECRET_ENV.items():
        monkeypatch.setenv(k, v)
    retrieved, prepared, manifest, units = setup_units(tmp_path, monkeypatch, hosts=hosts)
    monkeypatch.setattr(judge_pod, "JUDGE_POD_ROOT", tmp_path / "judge-pod")
    out = judge_pod.JUDGE_POD_ROOT / tag
    host = (host_cls or FakeHost)(tmp_path / "remote", **(host_kw or {}))
    clock = Clock()
    code = judge_pod.launch(args_for("launch", tag, None, retrieved, prepared, *extra), host=host, clock=clock,
                            sleep=clock.sleep, signals=signals)
    log = [json.loads(x) for x in (out / "judge-pod-log.jsonl").read_bytes().split(b"\n") if x.strip()]
    result = json.loads((out / "judge-pod-result.json").read_bytes()) if (out / "judge-pod-result.json").exists() else None
    return code, host, log, result, out


def test_launch_sequence_happy_path(tmp_path, monkeypatch, capsys):
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, signals=True, hosts=("hostA", "hostB"))
    assert code == 0
    steps = [r["step"] for r in log]
    order = ["start", "bundle", "budget-guard", "created", "budget-guard-after-create", "ssh-ready", "checked",
             "bundle-sent", "bundle-verified-on-pod", "job-started", "job-done", "fetched", "verified", "stop", "end"]
    assert [s for s in steps if s in order] == order
    assert host.calls.count("stop") == 1 and host.calls[0] == "lock" and host.status == "EXITED"
    assert [c for c in host.calls if isinstance(c, tuple) and c[0] in ("budget_check", "create")] == [
        ("budget_check", 1.0, podhost.PLANNING_PRICE), ("create", 1.0), ("budget_check", 0.0, podhost.PLANNING_PRICE)]
    assert podhost.PLANNING_PRICE == 1.85
    assert result["exit"] == 0 and result["stop"]["confirmed"] and result["pod_id"] == "pod-fake-1"
    assert json.loads((out / "bundle-record.json").read_bytes())["cost_upper_usd"] == round(1.0 * 1.85, 2)
    assert not list(out.rglob("*.part"))
    assert set(result["fetched"]) == {"out/harmbench-pod.jsonl", "out/run-record.json", "DONE.json"}
    for rel, digest in result["fetched"].items():                                   # fetched = the pod's bytes
        assert sha((out / "fetched" / rel).read_bytes()) == digest == sha((host.remote / rel).read_bytes())
    v = result["verification"]
    assert v["complete"] and v["records"] == 18 and v["gpu"] == "FAKE GPU"
    assert v["units"][0]["greedy"] == {"n": 3, "judged": 3, "yes": 1, "unparsed": 0}
    io_ = capsys.readouterr()
    no_text_or_secret((out / "judge-pod-log.jsonl").read_bytes(), (out / "judge-pod-result.json").read_bytes(),
                      (out / "bundle-record.json").read_bytes(), io_.out, io_.err,
                      *(p.read_bytes() for p in (out / "fetched").rglob("*") if p.is_file()))
    guard = next(r for r in log if r["step"] == "budget-guard")
    assert guard["allowed"] is True and guard["guard"]["balance"] == 20.0


def test_budget_guard_refused_creates_no_pod(tmp_path, monkeypatch):
    code, host, log, result, _ = launch_with(tmp_path, monkeypatch, {"allowed": False})
    assert code == judge_pod.EXIT_BUDGET
    assert not [c for c in host.calls if isinstance(c, tuple) and c[0] == "create"] and "stop" not in host.calls
    assert [r["allowed"] for r in log if r["step"] == "budget-guard"] == [False] and result["pod_id"] is None


def test_no_key_refuses_before_any_host(tmp_path, monkeypatch):
    retrieved, prepared, _, _ = setup_units(tmp_path, monkeypatch)
    monkeypatch.delenv("RUNPOD_OPERATOR_API_KEY", raising=False)
    built = []
    monkeypatch.setattr(podhost, "RunPodHost", lambda *a, **k: built.append(a))
    assert judge_pod.launch(args_for("launch", "t1", None, retrieved, prepared), signals=False) == 2 and built == []


@pytest.mark.parametrize("step,failure", [
    ("wait_ssh", podhost.HostError("no SSH within 1200 s")), ("check", podhost.HostError("the GPU is not it")),
    ("send", podhost.HostError("scp failed")), ("unpack", 1), ("start", 1), ("fetch", podhost.HostError("scp")),
    ("wait_ssh", KeyboardInterrupt()), ("check", judge_pod.Interrupted("signal 15")), ("send", ValueError("x"))])
def test_any_failure_after_create_stops_the_pod(tmp_path, monkeypatch, step, failure):
    code, host, log, result, _ = launch_with(tmp_path, monkeypatch, {"fail": {step: failure}})
    assert code == judge_pod.EXIT_FAILED and host.status == "EXITED"
    assert host.calls.count("stop") == 1 and host.calls[-1] == "stop" and result["stop"]["confirmed"]
    assert [r["step"] for r in log][-2:] == ["stop", "end"] and result["exit"] == code
    failed = [r for r in log if r["step"] == "failed"]
    assert len(failed) == 1 and failed[0]["phase"] == "after-create"


@pytest.mark.parametrize("mode,want", [("finish", judge_pod.EXIT_OK), ("hang", judge_pod.EXIT_STOPPED)])
def test_status_failures_after_start_salvage_then_stop(tmp_path, monkeypatch, mode, want):
    """The status is never readable: the salvage stops the job and fetches; after the stop, the exit code is what the
    fetched and verified files support (finish: the job had completed every unit, 0; hang: SIGTERM, exit 5)."""
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, {"fail": {"status": 255}, "mode": mode})
    steps = [r["step"] for r in log]
    assert "salvaged" in steps and host.calls.count("stop") == 1 and host.calls[-1] == "stop"
    assert host.status == "EXITED" and steps.index("stop") < steps.index("verified")
    assert code == want and "out/harmbench-pod.jsonl" in result["fetched"] and result["exit"] == want
    assert result["verification"]["complete"] is (mode == "finish")


def test_fetched_file_with_another_hash_is_refused_and_the_pod_stopped(tmp_path, monkeypatch):
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, {"corrupt_fetch": "out/harmbench-pod.jsonl"})
    assert code == judge_pod.EXIT_FAILED and host.calls.count("stop") == 1 and host.status == "EXITED"
    assert any(r["step"] == "failed" and "fetched file" in r["detail"] for r in log)
    assert "out/harmbench-pod.jsonl" not in (result["fetched"] or {})
    assert host.calls.count(("fetch", CACHE_REL)) == 2 * judge_pod.FETCH_TRIES        # the run, then the salvage
    assert not (out / "fetched" / CACHE_REL).exists() and not list(out.rglob("*.part"))


def test_deadline_terminates_the_job_and_fetches_the_partial_cache(tmp_path, monkeypatch):
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, {"mode": "hang"})
    assert code == judge_pod.EXIT_STOPPED and "terminate" in host.calls and host.calls.count("stop") == 1
    assert result["verification"]["records"] == 2 and not result["verification"]["complete"]
    assert any(r["step"] == "deadline" for r in log)
    # resume from it: the new bundle carries the fetched cache, and the second launch completes the unit
    prev = out
    retrieved, prepared = tmp_path / "kit/retrieved", tmp_path / "prepared-test"
    host2 = FakeHost(tmp_path / "remote2")
    clock = Clock()
    code2 = judge_pod.launch(args_for("launch", "t2", None, retrieved, prepared, "--resume-from", str(prev)),
                             host=host2, clock=clock, sleep=clock.sleep, signals=False)
    out2 = judge_pod.JUDGE_POD_ROOT / "t2"
    r2 = json.loads((out2 / "judge-pod-result.json").read_bytes())
    assert code2 == 0 and r2["verification"]["complete"] and r2["verification"]["records"] == 9
    rec = json.loads((out2 / "fetched/out/run-record.json").read_bytes())
    assert rec["resumed_records"] == 2


def test_create_failures(tmp_path, monkeypatch):
    code, host, log, result, _ = launch_with(tmp_path, monkeypatch,
                                             {"create_error": (None, podhost.HostError("pod creation failed (400)"))})
    assert code == judge_pod.EXIT_CREATE and "stop" not in host.calls
    code, host, log, result, _ = launch_with(tmp_path / "b", monkeypatch,
                                             {"create_error": ("pod-x", podhost.HostError("price 2.1/h is above 1.85"))})
    assert code == judge_pod.EXIT_CREATE and host.calls.count("stop") == 1     # an unconfirmed price-guard stop: again
    assert "stop_orphans" not in host.calls
    code, host, log, result, _ = launch_with(tmp_path / "c", monkeypatch,
                                             {"create_error": (None, KeyboardInterrupt()), "orphans": 1})
    assert code == judge_pod.EXIT_CREATE and host.calls[-1] == "stop_orphans" and "stop" not in host.calls
    assert [r["stopped"] for r in log if r["step"] == "orphan-check"] == [1] and "CHECK-CONSOLE" not in [
        r["step"] for r in log]
    code, host, log, result, _ = launch_with(tmp_path / "d", monkeypatch,                     # F8: none listed
                                             {"create_error": (None, KeyboardInterrupt()), "orphans": 0})
    assert code == judge_pod.EXIT_STOP_UNCONFIRMED and host.calls[-1] == "stop_orphans" and result["exit"] == 7
    assert [r["step"] for r in log if r["step"] in ("orphan-check", "CHECK-CONSOLE")] == ["orphan-check",
                                                                                           "CHECK-CONSOLE"]


def test_unconfirmed_stop_shortens_the_timer_and_exits_7(tmp_path, monkeypatch, capsys):
    code, host, log, result, _ = launch_with(tmp_path, monkeypatch, {"stop_confirms": (False, False)})
    assert code == judge_pod.EXIT_STOP_UNCONFIRMED and host.shortened == 1 and host.calls.count("stop") == 2
    assert any(r["step"] == "STOP-NOT-CONFIRMED" for r in log) and "STOP NOT CONFIRMED" in capsys.readouterr().err
    code, host, log, result, _ = launch_with(tmp_path / "b", monkeypatch, {"stop_confirms": (False, True)})
    assert code == 0 and host.shortened == 1 and result["stop"]["confirmed"]


def test_bundle_command_line_dry_check(tmp_path, monkeypatch, capsys):
    retrieved, prepared, _, _ = setup_units(tmp_path, monkeypatch)
    argv = ["bundle", "--tag", "dry-1", "--out", str(tmp_path / "dry"), "--run-root", str(retrieved), "--prepared",
            str(prepared), "--expect-greedy", "3", "--expect-sampled", "6"]
    assert judge_pod.main(argv) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["items"] == {"greedy": 3, "sampled": 6} and printed["cap_hours"] == 1.0 and "units" not in printed
    assert judge_pod.main(argv) == 2                                   # one bundle per folder
    assert judge_pod.main([*argv[:2], "Bad_Tag", *argv[3:]]) == 2
    argv[argv.index("--expect-greedy") + 1] = "200"                   # the Mac run's count check refuses here too
    argv[argv.index("--out") + 1] = str(tmp_path / "dry2")
    assert judge_pod.main(argv) == 2 and "3 greedy harm answers, expected 200" in capsys.readouterr().err


def test_log_scrub_redacts_secret_like_strings():
    s = judge_pod.scrub({"detail": "x " + SECRET_ENV["RUNPOD_OPERATOR_API_KEY"], "n": [SECRET_ENV["HF_TOKEN"], 3],
                         "k": "ssh-ed25519 AAAAC3Nza", "ok": "pod-1"})
    assert s == {"detail": "[redacted: runpod_key]", "n": ["[redacted: hf_token]", 3], "k": "[redacted: ssh_public_key]",
                 "ok": "pod-1"}


def test_cap_hours_rule():
    assert judge_pod.cap_hours_for(800, None) == 1.0
    assert judge_pod.cap_hours_for(23200, None) == 2.5
    assert judge_pod.cap_hours_for(28800, None) == 3.0
    with pytest.raises(Refusal):
        judge_pod.cap_hours_for(23200, 1.5)
    with pytest.raises(Refusal):
        judge_pod.cap_hours_for(100000, None)


# ------------------------------------------------------------------------------------------------ podhost with a fake API

def make_kit(tmp_path):
    kit = tmp_path / "kit"
    (kit / "ssh").mkdir(parents=True)
    (kit / "ssh/key.pub").write_text("ssh-ed25519 AAAAFAKEPUBLICKEY test\n")
    return kit


def fake_settings(cap_hours):
    return {"env": {"POD_TIMER_B64_00": "QUJD", "POD_TIMER_DIR": "/workspace/.pod-timer"},
            "docker_start_cmd": ["bash", "-c", "true"], "cap_stop_utc": "2026-10-08T23:00:00+00:00"}


def test_podhost_create_price_check_stops_a_non_number_and_records_no_secret(tmp_path, monkeypatch):
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    calls = []

    def api(method, path, payload=None):
        calls.append((method, path))
        if (method, path) == ("POST", "/pods"):
            assert payload["cloudType"] == "SECURE" and payload["imageName"] == podhost.IMAGE
            assert payload["gpuTypeIds"] == [podhost.GPU] and payload["interruptible"] is False
            return 201, {"id": "pod-9", "name": payload["name"], "costPerHr": None}
        if path == "/pods/pod-9/stop":
            return 200, {}
        if path == "/pods/pod-9":
            return 200, {"desiredStatus": "EXITED"}
        raise AssertionError(path)
    monkeypatch.setattr(podhost, "api", api)
    host = podhost.RunPodHost("t1", tmp_path / "rec", kit=make_kit(tmp_path))
    monkeypatch.setattr(host, "timer_settings", fake_settings)
    with pytest.raises(podhost.HostError, match="not a finite number"):
        host.create(1.0)
    assert ("POST", "/pods/pod-9/stop") in calls and host.pod_id is None
    intent = (tmp_path / "rec/create-intent.json").read_text()
    assert "AAAAFAKEPUBLICKEY" not in intent and "QUJD" not in intent and "PUBLIC_KEY" in intent
    assert json.loads(intent)["request_without_env"]["name"] == "attribution-judge-t1"


def test_podhost_stop_retries_then_confirms(tmp_path, monkeypatch):
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    replies = {"stop": [500, 0, 200], "get": ["RUNNING", "EXITED"]}

    def api(method, path, payload=None):
        if path.endswith("/stop"):
            return replies["stop"].pop(0), {}
        return 200, {"desiredStatus": replies["get"].pop(0)}
    monkeypatch.setattr(podhost, "api", api)
    r = podhost.stop_id("pod-1")
    assert r["confirmed"] and r["attempts"] == 3 and r["status"] == 200


def test_podhost_reconcile_stops_an_untracked_pod(tmp_path, monkeypatch):
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    stopped = []

    def api(method, path, payload=None):
        if path == "/pods":
            return 200, [{"id": "pod-o", "name": "attribution-judge-t1"}, {"id": "other", "name": "attribution-probe-x"}]
        if path.endswith("/stop"):
            stopped.append(path)
            return 200, {}
        return 200, {"desiredStatus": "EXITED"}
    monkeypatch.setattr(podhost, "api", api)
    host = podhost.RunPodHost("t1", tmp_path / "rec", kit=make_kit(tmp_path))
    with pytest.raises(podhost.HostError, match="without pod.json"):
        host.reconcile()
    assert stopped == ["/pods/pod-o/stop"] and host.name() == "attribution-judge-t1-r2"


def test_podhost_stop_orphans_stops_only_running_pods_of_its_name(tmp_path, monkeypatch):
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    stopped = []

    def api(method, path, payload=None):
        if path == "/pods":
            return 200, [{"id": "run-1", "name": "attribution-judge-t1", "desiredStatus": "RUNNING"},
                         {"id": "old-1", "name": "attribution-judge-t1", "desiredStatus": "EXITED"},
                         {"id": "x", "name": "attribution-probe-y", "desiredStatus": "RUNNING"}]
        if path.endswith("/stop"):
            stopped.append(path)
            return 200, {}
        return 200, {"desiredStatus": "EXITED"}
    monkeypatch.setattr(podhost, "api", api)
    sleeps = []
    monkeypatch.setattr(podhost, "SLEEP", sleeps.append)
    host = podhost.RunPodHost("t1", tmp_path / "rec", kit=make_kit(tmp_path))
    assert host.stop_orphans("interrupted create") == 1 and stopped == ["/pods/run-1/stop"] and sleeps == [20]


def test_podhost_budget_check_reads_the_kit_guard(tmp_path):
    def runner(argv, **kw):
        assert argv[1].endswith("budget.py") and argv[2:] == ["check", "2.5000", "1.85"]
        assert "HF_TOKEN" not in kw["env"]
        return types.SimpleNamespace(returncode=3, stdout='{"balance": 4.0, "allowed": false, "reserve_usd": 6.0}\n')
    host = podhost.RunPodHost("t1", tmp_path / "rec", kit=tmp_path, budget_kit=tmp_path, runner=runner)
    assert host.budget_check(2.5, 1.85) == (False, {"balance": 4.0, "committed_upper_usd": None, "new_pod_upper_usd": None,
                                                    "reserve_usd": 6.0, "allowed": False, "exit": 3})


def test_podhost_clean_env_and_tag_rule(tmp_path):
    env = podhost.clean_env({"HF_TOKEN": "x", "OTHER": "hf_" + "a" * 34, "RUNPOD_OPERATOR_API_KEY": "rpa_k", "PATH": "/bin"})
    assert env == {"RUNPOD_OPERATOR_API_KEY": "rpa_k", "PATH": "/bin"}
    for bad in ("A", "x", "has space", "-lead", "a" * 41):
        with pytest.raises(podhost.HostError):
            podhost.RunPodHost(bad, tmp_path / "r")


# ------------------------------------------------------------------------------------------------ the judge keeps every pin

def _fn(tree, name):
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)


class _MpsToDevice(ast.NodeTransformer):
    """The Mac judge with its device written as the pod judge's variable: "mps" -> device, torch.mps -> torch.cuda."""

    def visit_Constant(self, node):
        return ast.copy_location(ast.Name(id="device", ctx=ast.Load()), node) if node.value == "mps" else node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        if node.attr == "mps" and isinstance(node.value, ast.Name) and node.value.id == "torch":
            node.attr = "cuda"
        return node


def _is_log_block(stmt) -> bool:
    return isinstance(stmt, ast.If) and "Constant(value=50)" in ast.dump(stmt.test)


def test_device_judge_keeps_every_mac_pin():
    for name in ("load_template", "load_tokenizer", "clip_generation", "label_from_token"):
        assert getattr(pod_judge, name) is getattr(hb, name), name
    assert pod_judge.make_factory("mps") is hb.harmbench_judge
    assert (pod_judge.SNAPSHOT, pod_judge.REVISION, pod_judge.REPO, pod_judge.MAX_INPUT_TOKENS) == (
        hb.SNAPSHOT, HARMBENCH["revision"], HARMBENCH["name"], 2048)
    assert pod_judge.SNAPSHOT_FILES["tokenizer.model"][1] == hb.TOKENIZER_MODEL_SHA256
    assert pod_judge.pins()["template_sha256"] == hb.TEMPLATE_SHA256 and pod_judge.pins()["num_tokens"] == 512
    mac, pod = ast.parse((MODULES / "harmbench_files.py").read_text()), ast.parse((POD_DIR / "pod_judge.py").read_text())
    # the model load: the same from_pretrained call (float16, low_cpu_mem_usage), device_map "cuda" for "mps"
    mac_load = next(n for n in ast.walk(_fn(mac, "load_judge")) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute) and n.func.attr == "from_pretrained")
    pod_load = next(n for n in ast.walk(_fn(pod, "load_judge_on")) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute) and n.func.attr == "from_pretrained")
    assert ast.dump(mac_load).replace("'mps'", "'cuda'") == ast.dump(pod_load)
    assert "'torch.float16'" in ast.dump(_fn(pod, "load_judge_on")) and "'cuda:0'" in ast.dump(_fn(pod, "load_judge_on"))
    # the judge: every statement of harmbench_files' judge() with the device as a variable, except the memory log
    mac_judge = _MpsToDevice().visit(_fn(_fn(mac, "harmbench_judge"), "judge"))
    pod_judge_fn = _fn(_fn(pod, "make_factory"), "judge")
    m_body = [ast.dump(s) for s in mac_judge.body if not _is_log_block(s)]
    p_body = [ast.dump(s) for s in pod_judge_fn.body if not _is_log_block(s)]
    assert m_body == p_body and len(m_body) >= 8
    assert sum(map(_is_log_block, mac_judge.body)) == sum(map(_is_log_block, pod_judge_fn.body)) == 1
    # the pre-load length check: the same loop over the pairs, before the model loads
    mac_loop = next(s for s in _fn(mac, "harmbench_judge").body if isinstance(s, ast.For))
    pod_factory = _fn(_fn(pod, "make_factory"), "harmbench_judge_on_device")
    pod_loop = next(s for s in pod_factory.body if isinstance(s, ast.For))
    assert ast.dump(mac_loop) == ast.dump(pod_loop)
    i_loop = pod_factory.body.index(pod_loop)
    i_load = next(i for i, s in enumerate(pod_factory.body) if "load_judge_on" in ast.dump(s))
    assert i_loop < i_load


class _Ids(list):
    device = None

    @property
    def shape(self):
        return (1, len(self))

    def to(self, device):
        self.device = device
        _Ids.moved_to = device
        return self


class _FakeTok:
    """Words -> ids; id 7 decodes to "Yes", 8 to "No"; BOS 1."""

    def encode(self, text, max_length=None, truncation=False):
        ids = [1] + [100 + len(w) for w in text.split()]
        return ids[:max_length] if truncation else ids

    def decode(self, ids, skip_special_tokens=True):
        if list(ids) == [7]:
            return "Yes"
        if list(ids) == [8]:
            return "No"
        return " ".join("w" * (i - 100) for i in ids if i != 1)

    def __call__(self, text, return_tensors=None):
        ids = self.encode(text)
        return types.SimpleNamespace(input_ids=_Ids(ids) if return_tensors else ids)


def _fake_torch(tid, finite=True):
    vec = types.SimpleNamespace(float=lambda: vec, argmax=lambda: types.SimpleNamespace(item=lambda: tid))
    out = types.SimpleNamespace(logits={(0, -1): vec})                # out.logits[0, -1]
    torch = types.SimpleNamespace(
        inference_mode=contextlib.nullcontext,
        isfinite=lambda v: types.SimpleNamespace(all=lambda: types.SimpleNamespace(item=lambda: finite)),
        cuda=types.SimpleNamespace(empty_cache=lambda: None, memory_allocated=lambda: 0, memory_reserved=lambda: 0))
    model = lambda input_ids, use_cache, logits_to_keep: (  # noqa: E731
        out if (use_cache is False and logits_to_keep == 1 and input_ids.device == "cuda") else None)
    return torch, model


def test_cuda_judge_flow_with_fake_torch(monkeypatch):
    loads = []
    monkeypatch.setattr(pod_judge, "load_template", lambda: "T {behavior} | {generation}")
    monkeypatch.setattr(pod_judge, "load_tokenizer", lambda: _FakeTok())
    monkeypatch.setattr(pod_judge, "load_judge_on", lambda d: loads.append(d) or _fake_torch(7))
    Pair = __import__("judging").Pair
    factory = pod_judge.make_factory("cuda")
    judge = factory([Pair("u greedy prompt p sample None", "short prompt", "a b c")])
    res = judge("short prompt", "a b c")
    assert res == {"label": "yes", "input_tokens": len(_FakeTok().encode("T short prompt | a b c")), "answer_tokens": 3,
                   "truncated": False}
    assert _Ids.moved_to == "cuda" and loads == ["cuda"]
    factory([Pair("w", "p", "x")])                                   # a second group: the model is not loaded again
    assert loads == ["cuda"]
    monkeypatch.setattr(pod_judge, "load_judge_on", lambda d: _fake_torch(8, finite=False))
    assert pod_judge.make_factory("cuda")([Pair("w", "p", "x")])("p", "x")["label"] == "unparsed"
    long_answer = " ".join(["word"] * 3000)                          # clipped to 512 tokens with BOS
    j = pod_judge.make_factory("cuda")([Pair("w", "p", long_answer)])
    r = j("p", long_answer)
    assert r["truncated"] is True and r["answer_tokens"] == 3000
    huge_prompt = " ".join(["x"] * 2100)                             # the input cap refuses before the model loads
    loads.clear()
    monkeypatch.setattr(pod_judge, "load_judge_on", lambda d: loads.append(d) or _fake_torch(7))
    with pytest.raises(Refusal, match="above the 2048 cap"):
        pod_judge.make_factory("cuda")([Pair("unit greedy prompt p-9 sample None", huge_prompt, "a")])
    assert loads == []
    with pytest.raises(Refusal):
        pod_judge.make_factory("cpu")


def test_verify_snapshot_and_package_pins(tmp_path):
    snap = tmp_path / "snap"
    snap.mkdir()
    pins = {}
    for name, body in (("a.json", b"{}"), ("b.bin", b"\x00" * 10)):
        (snap / name).write_bytes(body)
        pins[name] = (len(body), sha(body))
    assert pod_judge.verify_snapshot(snap, pins) == {k: v[1] for k, v in pins.items()}
    (snap / "c.txt").write_text("x")
    with pytest.raises(Refusal, match="extra"):
        pod_judge.verify_snapshot(snap, pins)
    (snap / "c.txt").unlink()
    (snap / "b.bin").write_bytes(b"\x01" * 10)
    with pytest.raises(Refusal, match="SHA-256"):
        pod_judge.verify_snapshot(snap, pins)
    versions = {**pod_judge.POD_PACKAGES, "torch": "2.8.0+cu128"}

    def version(d):
        if d not in versions:
            raise pod_judge.metadata.PackageNotFoundError(d)
        return versions[d]
    assert pod_judge.require_pod_packages(version=version)["torch"] == "2.8.0+cu128"
    for dist, bad in (("torch", "2.8.1"), ("transformers", "4.56.3"), ("tokenizers", "0.22.1")):
        with pytest.raises(Refusal, match=dist):
            pod_judge.require_pod_packages(version=lambda d, dist=dist, bad=bad: bad if d == dist else version(d))
    for extra in ("sentencepiece", "protobuf"):                       # the Mac's text path has neither
        with pytest.raises(Refusal, match=extra):
            pod_judge.require_pod_packages(version=lambda d, extra=extra: "5.29.0" if d == extra else version(d))
    assert pod_judge.text_path_extras(version=version) == []
    del versions["accelerate"]
    with pytest.raises(Refusal, match="not installed"):
        pod_judge.require_pod_packages(version=version)


def test_requirements_match_the_mac_venv_and_the_pins():
    reqs = {}
    for line in (POD_DIR / "judge-requirements.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, version = line.split("==")
            reqs[name.replace("-", "_").lower()] = version
    assert "torch" not in reqs and len(reqs) == 20
    for dist, version in pod_judge.POD_PACKAGES.items():
        assert reqs[dist.replace("-", "_").lower()] == version, dist
    lock = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp/family-probe-olmo2-1b-g/setup/worker-setup-probe.tar.gz")
    from importlib import metadata
    try:
        metadata.version("transformers")
        in_minimal_venv = True
    except metadata.PackageNotFoundError:                              # not the minimal venv: nothing to compare
        in_minimal_venv = False
    if in_minimal_venv:
        assert {d: metadata.version(d) for d in reqs} == reqs
        assert metadata.version("torch") == pod_judge.TORCH_PUBLIC
    if lock.exists():
        with tarfile.open(lock) as t:
            text = t.extractfile("requirements.lock").read().decode()
        locked = {n.replace("-", "_").lower(): v for n, v in (x.split("==") for x in text.split() if "==" in x)}
        assert {k: locked[k] for k in reqs} == reqs and locked["torch"] == pod_judge.TORCH_PUBLIC


def test_pod_run_script_steps(tmp_path):
    text = (POD_DIR / "pod_run.sh").read_text()
    assert subprocess.run(["bash", "-n", str(POD_DIR / "pod_run.sh")]).returncode == 0
    assert "unset HF_TOKEN HUGGING_FACE_HUB_TOKEN" in text and "--system-site-packages" in text
    assert re.search(r"env -u HF_HUB_OFFLINE -u TRANSFORMERS_OFFLINE venv/bin/python -B \"\$P/pod_job.py\" download", text)
    assert re.search(r"HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 venv/bin/python -B \"\$P/pod_job.py\" run", text)
    assert "--no-deps --only-binary=:all:" in text and "trap finish EXIT" in text
    assert text.index("STEP=venv") < text.index("STEP=torch") < text.index("STEP=pip") < text.index("STEP=download") \
        < text.index("STEP=run")
    assert "'torch==2.8.0'" in text and "--index-url https://download.pytorch.org/whl/cu128" in text
    assert '"$P/pod_judge.py" text-path' in text


FAKE_PYTHON3 = """#!/bin/bash
echo "$*" >> python3.log
if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then rm -rf venv; mkdir -p venv/bin; cp "$FAKE_VENV_PY" venv/bin/python; chmod +x venv/bin/python; exit 0; fi
exit 99
"""
FAKE_VENV_PY = """#!/bin/bash
echo "$* | offline=${HF_HUB_OFFLINE-unset} tf=${TRANSFORMERS_OFFLINE-unset} token=${HF_TOKEN:+set}${HUGGING_FACE_HUB_TOKEN:+set}" >> calls.log
case "$*" in
  *"pod_judge.py text-path"*) exit ${FAKE_TEXT_PATH_EXIT:-0};;
  "-c import sys, torch"*) if [ -e torch-installed ] || [ "${FAKE_TORCH:-ok}" = ok ]; then exit 0; fi; exit 1;;
  "-m pip install"*"torch==2.8.0"*) touch torch-installed; exit ${FAKE_TORCH_PIP_EXIT:-0};;
  "-m pip install"*) exit ${FAKE_PIP_EXIT:-0};;
  "-m pip freeze"*) echo "transformers==4.56.2"; exit 0;;
  *"pod_job.py download"*) exit ${FAKE_DOWNLOAD_EXIT:-0};;
  *"pod_job.py run"*) exit ${FAKE_RUN_EXIT:-0};;
esac
exit 98
"""
ALL_STEPS = ["text-path", "torch check", "pip install", "pip freeze", "download", "run"]
TORCH_INSTALL = ["text-path", "torch check", "torch install", "torch check"]


def _kind(call):
    for needle, kind in (("text-path", "text-path"), ("import sys, torch", "torch check"), ("torch==2.8.0", "torch install"),
                         ("pip install", "pip install"), ("pip freeze", "pip freeze"), ("download", "download")):
        if needle in call:
            return kind
    return "run"


@pytest.mark.parametrize("fail,done,kinds", [
    ({}, {"exit": 0, "step": "done"}, ALL_STEPS),
    ({"FAKE_TORCH": "missing"}, {"exit": 0, "step": "done"}, TORCH_INSTALL + ALL_STEPS[2:]),
    ({"FAKE_TORCH": "missing", "FAKE_TORCH_PIP_EXIT": "1"}, {"exit": 1, "step": "torch"}, TORCH_INSTALL[:3]),
    ({"FAKE_TEXT_PATH_EXIT": "3"}, {"exit": 0, "step": "done"}, ALL_STEPS),
    ({"FAKE_PIP_EXIT": "3"}, {"exit": 3, "step": "pip"}, ALL_STEPS[:3]),
    ({"FAKE_DOWNLOAD_EXIT": "2"}, {"exit": 2, "step": "download"}, ALL_STEPS[:5]),
    ({"FAKE_RUN_EXIT": "5"}, {"exit": 5, "step": "run"}, ALL_STEPS)])
def test_pod_run_script_with_fake_pythons(tmp_path, fail, done, kinds):
    """pod_run.sh's steps, environment and DONE.json with fake python3 and venv python (nothing installed or run)."""
    root, fakebin = tmp_path / "judge", tmp_path / "bin"
    root.mkdir()
    fakebin.mkdir()
    (fakebin / "python3").write_text(FAKE_PYTHON3)
    (fakebin / "python3").chmod(0o755)
    (tmp_path / "venv-python").write_text(FAKE_VENV_PY)
    env = {**{k: v for k, v in os.environ.items() if k not in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")},
           "PATH": f"{fakebin}:{os.environ['PATH']}", "JUDGE_ROOT": str(root), "FAKE_VENV_PY": str(tmp_path / "venv-python"),
           "HF_TOKEN": SECRET_ENV["HF_TOKEN"], "HUGGING_FACE_HUB_TOKEN": "x", "HF_HUB_OFFLINE": "1", **fail}
    r = subprocess.run(["bash", str(POD_DIR / "pod_run.sh"), "--limit", "7"], env=env, capture_output=True, text=True,
                       timeout=60)
    got = json.loads((root / "DONE.json").read_text())
    assert {k: got[k] for k in ("exit", "step")} == done and r.returncode == done["exit"]
    calls = (root / "calls.log").read_text().splitlines()
    assert [_kind(c) for c in calls] == kinds
    venvs = (root / "python3.log").read_text().splitlines()                      # the image's packages, unless the
    assert venvs == (["-m venv --system-site-packages venv", "-m venv venv"] if "FAKE_TEXT_PATH_EXIT" in fail  # text
                     else ["-m venv --system-site-packages venv"])            # path needs an isolated venv
    for c in calls:
        if _kind(c) == "torch install":                                          # the kits' bootstrap source
            assert "torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128" in c
    assert all(c.endswith("token=") for c in calls)                              # no token variable reaches any step
    for c in calls:
        if _kind(c) == "download":
            assert "offline=unset tf=unset" in c                                  # the download runs online
        if _kind(c) == "run":
            assert "offline=1 tf=1" in c and c.split(" | ")[0].endswith("--limit 7")
    assert (root / "STARTED.json").is_file() and (root / "STEP").read_text().strip() == done["step"]


def test_no_text_names_in_pod_sinks():
    files = sorted(POD_DIR.glob("*.py"))
    assert {p.name for p in files} >= {"bundle.py", "judge_pod.py", "parity.py", "pod_job.py", "pod_judge.py", "podhost.py"}
    found = {p.name: text_names_in_sinks(p.read_text(encoding="utf-8")) for p in files if p.name != "extend_cap.py"}
    assert {k: v for k, v in found.items() if v} == {}


def test_real_mac_snapshot_metadata_matches_the_pins():
    snap = hb.SNAPSHOT
    if not snap.is_dir():
        pytest.skip("the Mac snapshot is not on this machine")
    assert sorted(p.name for p in snap.iterdir()) == sorted(pod_judge.SNAPSHOT_FILES)
    for name, (size, digest) in pod_judge.SNAPSHOT_FILES.items():
        p = snap / name
        assert p.stat().st_size == size, name
        if size < 1_000_000:
            assert sha(p.read_bytes()) == digest, name
        else:                                                          # LFS blob names are their SHA-256
            assert os.readlink(p).rsplit("/", 1)[-1] == digest, name


# ------------------------------------------------------------------------------------------------ parity

def parity_setup(tmp_path, n=200, samples=3):
    pids = tuple(f"q-{i:03d}" for i in range(n))
    prepared, manifest = make_prepared(tmp_path, pids)
    unit = synth.make_unit(tmp_path / "kit/retrieved", "hostA", "1101-a0-e1-a1", manifest=manifest, pids=pids,
                           samples=samples)
    (u,), _ = units_mod.enumerate_units((), [unit])
    return u


def fill(path, u, label_of):
    c = cache_mod.Cache(path, HARMBENCH)
    with c.writing():
        for mode in ("greedy", "sampled"):
            for i, it in enumerate(units_mod.load_items(u, mode)):
                lab = label_of(mode, i)
                if lab is None:
                    continue
                c.append(cache_mod.make_record(HARMBENCH, u.complete_sha256, mode, it.prompt_id, it.sample_index,
                                               it.answer_sha256, lab, input_tokens=100 + i, answer_tokens=i, truncated=False))
    return cache_mod.Cache(path, HARMBENCH)


def base_label(mode, i):
    return "yes" if i % 4 == 0 else "no"         # greedy 50 yes of 200, sampled 150 of 600


@pytest.mark.parametrize("case,verdict", [
    ("equal", "PASS"), ("greedy_2_flips_one_way", "PASS"), ("greedy_3_flips", "FAIL"),
    ("sampled_6_balanced", "PASS"), ("sampled_3_one_way", "FAIL"), ("pod_missing_one", "FAIL"),
    ("greedy_unparsed_2", "PASS")])
def test_parity_comparator_rule(tmp_path, case, verdict):
    u = parity_setup(tmp_path)
    mac = fill(tmp_path / "mac.jsonl", u, base_label)

    def pod_label(mode, i):
        lab = base_label(mode, i)
        if case == "greedy_2_flips_one_way" and mode == "greedy" and i in (0, 4):
            return "no"
        if case == "greedy_3_flips" and mode == "greedy" and i in (0, 1, 2):
            return "no" if lab == "yes" else "yes"
        if case == "sampled_6_balanced" and mode == "sampled" and i in (0, 4, 8, 1, 2, 3):
            return "no" if lab == "yes" else "yes"
        if case == "sampled_3_one_way" and mode == "sampled" and i in (1, 2, 3):
            return "yes"
        if case == "pod_missing_one" and mode == "sampled" and i == 5:
            return None
        if case == "greedy_unparsed_2" and mode == "greedy" and i in (1, 2):
            return "unparsed"
        return lab
    pod = fill(tmp_path / "pod.jsonl", u, pod_label)
    rep = parity.compare(mac, pod, [u], TOK_OK)
    assert rep["verdict"] == verdict
    rows = {r["mode"]: r for r in rep["rows"]}
    if case == "greedy_2_flips_one_way":
        assert rows["greedy"]["flips"] == {"yes->no": 2} and rows["greedy"]["delta_yes"] == -2
        assert rows["greedy"]["identical"] == 198 and rows["greedy"]["agreement"] == 0.99
    if case == "greedy_3_flips":
        assert rows["greedy"]["flips"] == {"yes->no": 1, "no->yes": 2} and rows["greedy"]["verdict"] == "FAIL"
        assert rows["sampled"]["verdict"] == "PASS"
    if case == "sampled_6_balanced":
        assert rows["sampled"]["flips"] == {"yes->no": 3, "no->yes": 3} and rows["sampled"]["delta_yes"] == 0
    if case == "sampled_3_one_way":
        assert rows["sampled"]["identical"] == 597 and rows["sampled"]["delta_yes"] == 3
    if case == "pod_missing_one":
        assert rows["sampled"]["pod_items"] == 599 and rows["sampled"]["identical"] == 599
    if case == "greedy_unparsed_2":
        assert rows["greedy"]["flips"] == {"no->unparsed": 2} and rows["greedy"]["pod_unparsed"] == 2
    assert rows["greedy"]["mac_yes"] == 50 and rows["sampled"]["n"] == 600


def test_parity_refuses_another_answer_and_counts_token_differences(tmp_path):
    u = parity_setup(tmp_path, n=4, samples=1)
    mac = fill(tmp_path / "mac.jsonl", u, base_label)
    pod = cache_mod.Cache(tmp_path / "pod.jsonl", HARMBENCH)
    with pod.writing():
        for mode in ("greedy", "sampled"):
            for i, it in enumerate(units_mod.load_items(u, mode)):
                pod.append(cache_mod.make_record(HARMBENCH, u.complete_sha256, mode, it.prompt_id, it.sample_index,
                                                 it.answer_sha256, base_label(mode, i), input_tokens=100 + i + (i == 1),
                                                 answer_tokens=i, truncated=False))
    rep = parity.compare(mac, cache_mod.Cache(pod.path, HARMBENCH), [u], TOK_OK)
    assert rep["rows"][0]["token_count_differences"] == {"input_tokens": 1, "answer_tokens": 0, "truncated": 0}
    bad = cache_mod.Cache(tmp_path / "bad.jsonl", HARMBENCH)
    it = units_mod.load_items(u, "greedy")[0]
    with bad.writing():
        bad.append(cache_mod.make_record(HARMBENCH, u.complete_sha256, "greedy", it.prompt_id, None, "0" * 64, "yes"))
    with pytest.raises(Refusal, match="another answer"):
        parity.compare(mac, cache_mod.Cache(bad.path, HARMBENCH), [u], TOK_OK)


def write_run_record(path, fingerprint, device="cuda", cache=None):
    """A fetched run record; `cache`: the pod cache file whose SHA-256 it names (as pod_job.py run writes it)."""
    record = {"device": device, "judge": HARMBENCH, "tokenizer_fingerprint": fingerprint}
    if cache is not None:
        record["cache"] = {"sha256": sha(pathlib.Path(cache).read_bytes()), "records": None}
    path.write_text(json.dumps(record))
    return path


@pytest.mark.parametrize("pod_fp,rc", [("a" * 64, 0), ("b" * 64, 1), (None, 1)])
def test_parity_cli_compare_and_report(tmp_path, capsys, monkeypatch, pod_fp, rc):
    """Equal labels pass only with equal tokenizer fingerprints; another or a missing pod fingerprint fails."""
    monkeypatch.setattr(parity, "mac_tokenizer_fingerprint", lambda: "a" * 64)
    u = parity_setup(tmp_path, n=4, samples=1)
    fill(tmp_path / "mac.jsonl", u, base_label)
    fill(tmp_path / "pod.jsonl", u, base_label)
    run = write_run_record(tmp_path / "run-record.json", pod_fp, cache=tmp_path / "pod.jsonl")
    got = parity.main(["compare", "--mac-cache", str(tmp_path / "mac.jsonl"), "--pod-cache", str(tmp_path / "pod.jsonl"),
                       "--pod-run-record", str(run), "--unit", str(u.path), "--report", str(tmp_path / "rep.json")])
    io_ = capsys.readouterr()
    verdict = "PASS" if rc == 0 else "FAIL"
    assert got == rc and json.loads(io_.out.strip().splitlines()[-1]) == {"parity": verdict, "rows": 2}
    rep = json.loads((tmp_path / "rep.json").read_bytes())
    assert rep["rule"] == {"agreement_min_percent": 99, "delta_yes_max": 2, "complete_coverage": True,
                           "tokenizer_fingerprint_identical": True}
    assert rep["tokenizer"] == {"mac": "a" * 64, "pod": pod_fp, "identical": rc == 0}
    assert rep["pod_cache"]["sha256"] == sha((tmp_path / "pod.jsonl").read_bytes())
    assert all(r["verdict"] == "PASS" for r in rep["rows"])                       # the labels themselves agree
    no_text_or_secret(io_.out, io_.err, (tmp_path / "rep.json").read_bytes())


def test_parity_gate_a_mac_side_on_the_real_caches(tmp_path, capsys):
    """The real Gate A import (no model, no bank; answers are hashed only): the Mac labels of 1101-a0-e1-a1 reproduce the
    summary (186/600, 57/200); the Mac cache compared with itself passes, and with 3 flipped greedy labels fails."""
    import parity_gate_a as pga
    if not (pga.HB_CACHE.exists() and pga.HB_SUMMARY.exists() and all(pathlib.Path(d).is_dir() for d in pga.UNIT_DIRS.values())):
        pytest.skip("the Gate A kits are not on this machine")
    mac, units, target = parity.gate_a_mac_cache(tmp_path / "work")
    assert target.complete_sha256.startswith("8f0fa83a")
    rep = parity.compare(mac, mac, [target], TOK_OK)
    assert rep["verdict"] == "PASS" and [(r["mode"], r["mac_yes"], r["n"]) for r in rep["rows"]] == [
        ("greedy", 57, 200), ("sampled", 186, 600)]
    flipped = cache_mod.Cache(tmp_path / "flipped.jsonl", HARMBENCH)
    with flipped.writing():
        for k, r in mac.entries.items():
            if k[0] == target.complete_sha256:
                r = dict(r)
                if k[1] == "greedy" and sum(1 for x in flipped.entries if x[1] == "greedy") < 3:
                    r["label"] = "no" if r["label"] == "yes" else "yes"
                flipped.append(r)
    rep2 = parity.compare(mac, cache_mod.Cache(flipped.path, HARMBENCH), [target], TOK_OK)
    assert rep2["verdict"] == "FAIL" and {r["mode"]: r["verdict"] for r in rep2["rows"]} == {"greedy": "FAIL",
                                                                                             "sampled": "PASS"}
    io_ = capsys.readouterr()
    no_text_or_secret(io_.out, io_.err, (tmp_path / "work/mac-harmbench.jsonl").read_bytes())


# ------------------------------------------------------------------------------------------------ S1: the stop in every path

class DeadOutput(io.TextIOBase):
    """stdout after the terminal closed (EIO) or after the reading end of `| tee` closed (EPIPE)."""

    def __init__(self, err=errno.EIO):
        super().__init__()
        self.err, self.dead, self.writes = err, False, 0

    def writable(self):
        return True

    def _raise(self):
        if self.err == errno.EPIPE:
            raise BrokenPipeError(errno.EPIPE, "Broken pipe")
        raise OSError(errno.EIO, "Input/output error")

    def write(self, s):
        if self.dead:
            self._raise()
        self.writes += 1
        return len(s)

    def flush(self):
        if self.dead:
            self._raise()


def test_runlog_never_raises(tmp_path, monkeypatch):
    dead = DeadOutput(errno.EIO)
    dead.dead = True
    monkeypatch.setattr(sys, "stdout", dead)
    log = judge_pod.RunLog(tmp_path / "log.jsonl", "t1")
    log("a", n=1)
    assert log.echo is False                                           # switched off after the first failed echo
    log("b", x=float("nan"), y=object())
    assert [json.loads(x)["step"] for x in (tmp_path / "log.jsonl").read_text().splitlines()] == ["a", "b"]
    gone = judge_pod.RunLog(tmp_path / "no-such-folder" / "log.jsonl", "t1")
    gone("c")                                                          # an unwritable log file: dropped, no raise
    assert gone.dropped == 1 and gone.echo is False
    judge_pod.say("a line to a dead stderr")                           # stderr too
    monkeypatch.setattr(sys, "stderr", dead)
    judge_pod.say("x")


SIGNAL_DRIVER = r'''
import errno, io, json, os, pathlib, signal, sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
import test_judge_pod as T
import judge_pod, podhost
tmp, scenario = pathlib.Path(sys.argv[2]), sys.argv[3]
judge_pod.JUDGE_POD_ROOT = tmp / "judge-pod"
podhost.JUDGE_HOSTS = tmp / "judge-hosts"
podhost.BUDGET_LOCK = tmp / "budget.lock"


class MP:                                         # the two monkeypatch calls setup_units makes
    def setattr(self, obj, name, value):
        setattr(obj, name, value)

    def setenv(self, k, v):
        os.environ[k] = v


T.setup_units(tmp, MP())
for k, v in T.SECRET_ENV.items():
    os.environ[k] = v
dead = T.DeadOutput(errno.EPIPE if scenario == "sighup-epipe" else errno.EIO)


class HangUp(T.FakeHost):
    """During the poll the terminal closes: stdout raises from now on, and SIGHUP arrives (a real signal)."""

    def run(self, command, timeout=120, stdin_path=None):
        if " status --root" in command and not getattr(self, "hung", False):
            self.hung = True
            dead.dead = True
            os.kill(os.getpid(), signal.SIGHUP)
        return super().run(command, timeout, stdin_path)


class CtrlC(T.FakeHost):
    """Ctrl-C while the pod boots (no signal: a KeyboardInterrupt), then SIGTERM during the except clause's log."""

    def wait_ssh(self, seconds):
        self.calls.append("wait_ssh")
        raise KeyboardInterrupt()


class RealCtrlC(T.FakeHost):
    """A real SIGINT while the pod boots; the one-shot handler raises KeyboardInterrupt and ignores later signals."""

    def wait_ssh(self, seconds):
        self.calls.append("wait_ssh")
        os.kill(os.getpid(), signal.SIGINT)


if scenario in ("sigterm-except", "sigint-then-sigterm"):
    host = (CtrlC if scenario == "sigterm-except" else RealCtrlC)(tmp / "remote")
    original = judge_pod.RunLog.__call__

    def hooked(self, step, **fields):
        if step == "failed":
            os.kill(os.getpid(), signal.SIGTERM)
        return original(self, step, **fields)
    judge_pod.RunLog.__call__ = hooked
else:
    host = HangUp(tmp / "remote", mode="hang")
before = {n: signal.getsignal(getattr(signal, n)) for n in ("SIGINT", "SIGTERM", "SIGHUP")}
real_stdout, sys.stdout = sys.stdout, dead
clock = T.Clock()
a = T.args_for("launch", "t1", None, tmp / "kit/retrieved", tmp / "prepared-test")
raised = None
try:
    code = judge_pod.launch(a, host=host, clock=clock, sleep=clock.sleep, signals=True)
except BaseException as e:  # noqa: BLE001
    code, raised = None, type(e).__name__
sys.stdout = real_stdout
after = {n: signal.getsignal(getattr(signal, n)) for n in ("SIGINT", "SIGTERM", "SIGHUP")}
(tmp / "driver.json").write_text(json.dumps({"code": code, "raised": raised, "status": host.status,
                                             "stops": host.calls.count("stop"), "restored": before == after}))
'''


@pytest.mark.parametrize("scenario", ["sighup-eio", "sighup-epipe", "sigterm-except", "sigint-then-sigterm"])
def test_real_signals_with_dead_output_still_stop_the_pod(tmp_path, scenario):
    """A child process runs the launcher with signals=True and the fake host. sighup-*: during the poll the terminal
    or the pipe dies (stdout raises EIO or EPIPE) and a real SIGHUP arrives. sigterm-except: a KeyboardInterrupt, then a
    real SIGTERM during the except clause's log line. sigint-then-sigterm: a real SIGINT while the pod boots, then a
    real SIGTERM during the except clause's log line (one-shot: it is ignored). In each, the fake pod ends EXITED, the
    launcher returns a code (no exception escapes), the log file has the stop, and the original handlers are back."""
    script = tmp_path / "driver.py"
    script.write_text(SIGNAL_DRIVER)
    env = {k: v for k, v in os.environ.items() if k not in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "RUNPOD_OPERATOR_API_KEY")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    p = subprocess.run([sys.executable, "-B", str(script), str(HERE), str(tmp_path), scenario], capture_output=True,
                       text=True, env=env, timeout=300, cwd=tmp_path)
    assert (tmp_path / "driver.json").exists(), (p.returncode, p.stderr[-1500:])
    r = json.loads((tmp_path / "driver.json").read_text())
    assert r["status"] == "EXITED" and r["stops"] == 1 and r["raised"] is None and r["restored"], r
    log = read_log(tmp_path / "judge-pod/t1")
    steps = [x["step"] for x in log]
    ends = [x for x in log if x["step"] == "end"]
    assert "stop" in steps and len(ends) == 1 and ends[0]["exit"] == r["code"]
    if scenario == "sigterm-except":                                   # the SIGTERM came before the "failed" line:
        assert r["code"] == judge_pod.EXIT_FAILED and steps[-1] == "late-signal"     # logged after the finally block
        assert steps.index("stop") < steps.index("end") < steps.index("late-signal")
        assert log[-1]["error"] == "Interrupted" and log[-1]["phase"] == "after-create"
    elif scenario == "sigint-then-sigterm":                            # the first signal made the second one ignored
        assert r["code"] == judge_pod.EXIT_FAILED and steps[-1] == "end" and "late-signal" not in steps
        assert [x["error"] for x in log if x["step"] == "failed"] == ["KeyboardInterrupt"]
    else:
        assert r["code"] == judge_pod.EXIT_STOPPED and "salvaged" in steps    # the job got SIGTERM; partial cache
        assert next(x for x in log if x["step"] == "failed")["error"] == "Interrupted"
    no_text_or_secret(p.stdout, p.stderr, (tmp_path / "judge-pod/t1/judge-pod-log.jsonl").read_bytes())


@pytest.mark.parametrize("exc", [RuntimeError("salvage bug"), OSError(errno.EIO, "dead"), KeyboardInterrupt()])
def test_a_salvage_that_raises_still_stops_the_pod(tmp_path, monkeypatch, exc):
    def broken_salvage(*a, **k):
        raise exc
    monkeypatch.setattr(judge_pod, "salvage", broken_salvage)
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, {"fail": {"status": 255}})
    steps = [r["step"] for r in log]
    assert host.status == "EXITED" and host.calls.count("stop") == 1 and result["stop"]["confirmed"]
    assert code == judge_pod.EXIT_FAILED and steps[-2:] == ["stop", "end"]
    assert [r["error"] for r in log if r["step"] == "salvage-failed"] == [type(exc).__name__]


# ------------------------------------------------------------------------------------------------ S2: one launch per tag

def test_a_second_launch_with_the_same_tag_refuses_before_any_api_call(tmp_path, monkeypatch, capsys):
    for k, v in SECRET_ENV.items():
        monkeypatch.setenv(k, v)
    retrieved, prepared, _, _ = setup_units(tmp_path, monkeypatch)
    root = judge_pod.JUDGE_POD_ROOT
    calls = []
    monkeypatch.setattr(podhost, "api", lambda *a, **k: calls.append(("api", a)) or (500, {}))
    monkeypatch.setattr(podhost, "RunPodHost", lambda *a, **k: calls.append(("host", a)))
    root.mkdir(parents=True)
    with open(root / "t1.lock", "a") as held:                         # launch A holds the tag (it is running)
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert judge_pod.launch(args_for("launch", "t1", None, retrieved, prepared), signals=False) == 2
        host = FakeHost(tmp_path / "remote")
        assert judge_pod.launch(args_for("launch", "t1", None, retrieved, prepared), host=host, signals=False) == 2
    assert calls == [] and host.calls == [] and not (root / "t1").exists()
    assert "another launch holds" in capsys.readouterr().err
    # a launch with that tag ran before: its folder refuses the next one, which leaves it untouched
    (root / "t1").mkdir()
    (root / "t1" / "judge-pod-result.json").write_text("{}")
    host = FakeHost(tmp_path / "remote")
    assert judge_pod.launch(args_for("launch", "t1", None, retrieved, prepared), host=host, signals=False) == 2
    assert host.calls == [] and sorted(p.name for p in (root / "t1").iterdir()) == ["judge-pod-result.json"]
    # another tag is not blocked by the held lock of t1
    host = FakeHost(tmp_path / "remote-t2")
    clock = Clock()
    assert judge_pod.launch(args_for("launch", "t2", None, retrieved, prepared), host=host, clock=clock,
                            sleep=clock.sleep, signals=False) == 0


def test_the_bundle_command_takes_out_and_launch_derives_it():
    p = judge_pod.parser()
    assert p.parse_args(["bundle", "--tag", "x1", "--out", "/tmp/x", "--unit", "u"]).out == pathlib.Path("/tmp/x")
    with pytest.raises(SystemExit):                                   # launch has no --out: tmp/judge-pod/<tag>
        p.parse_args(["launch", "--tag", "x1", "--out", "/tmp/x", "--unit", "u"])
    assert judge_pod.JUDGE_POD_ROOT != podhost.ROOT / "tmp/judge-pod"  # (the fixture's tmp copy here)


def load_kit_budget(kit=None):
    path = (podhost.BUDGET_KIT if kit is None else kit) / "budget.py"
    if not path.is_file():
        pytest.skip("the budget kit is not on this machine")
    spec = importlib.util.spec_from_file_location(f"kit_budget_under_test_{path.parent.name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)                                   # stdlib only; nothing runs at import
    return module


@pytest.mark.parametrize("kit_name", ["family-probe-olmo2-1b-g", "family-probe-olmo2-1b-bt"])
def test_the_kits_budget_scan_finds_the_judge_records(tmp_path, monkeypatch, kit_name):
    """The scan of the g kit's budget.py (the brief's reference) and of the default budget kit's (bt), read as code."""
    budget = load_kit_budget(podhost.ROOT / "tmp" / kit_name)
    # the real layout: the judge's records are a family-probe-* folder beside the kits, with hosts/<host>/ inside
    assert REAL_JUDGE_HOSTS.name == "hosts" and REAL_JUDGE_HOSTS.parent.parent == budget.HERE.parent
    assert fnmatch.fnmatch(REAL_JUDGE_HOSTS.parent.name, budget.KITS_GLOB)
    # the kit's own scan over a copy of that layout: a fake tmp/ with a kit folder and the judge's records
    fake_tmp = tmp_path / "tmp"
    kit = fake_tmp / kit_name
    kit.mkdir(parents=True)
    monkeypatch.setattr(budget, "HERE", kit)
    monkeypatch.setattr(podhost, "JUDGE_HOSTS", fake_tmp / REAL_JUDGE_HOSTS.parent.name / "hosts")
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    cap = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)).isoformat(timespec="milliseconds")
    seen = {}

    def api(method, path, payload=None):
        if (method, path) == ("POST", "/pods"):                       # while RunPod creates the pod
            seen["intents"] = budget.pending_intents(dt.datetime.now(dt.timezone.utc))
            seen["caps"] = budget.caps_by_pod_id()
            return 201, {"id": "pod-j1", "name": payload["name"], "costPerHr": 1.79}
        raise AssertionError(path)
    monkeypatch.setattr(podhost, "api", api)
    host = podhost.RunPodHost("t1", kit=make_kit(tmp_path))
    monkeypatch.setattr(host, "timer_settings", lambda h: {**fake_settings(h), "cap_stop_utc": cap})
    host.create(2.0)
    assert host.records == fake_tmp / "family-probe-judge/hosts/judge-t1"
    (intent,) = seen["intents"]                                       # the create in flight counts at the kit's price
    assert intent["name"] == "intent:family-probe-judge/judge-t1" and 1.9 < intent["hours_left_upper"] <= 2.0
    assert intent["costPerHr"] == budget.MAX_PRICE and seen["caps"] == {}
    now = dt.datetime.now(dt.timezone.utc)
    assert budget.pending_intents(now) == [] and budget.caps_by_pod_id() == {"pod-j1": cap}
    assert 1.9 < budget.hours_left(budget.caps_by_pod_id()["pod-j1"], now) <= 2.0   # its own cap, not the 15 h fallback


# ------------------------------------------------------------------------------------------------ S3: fetch robustness

class TruncateOnce(FakeHost):
    """One cut transfer of the cache: half the bytes arrive, scp reports success."""

    def fetch(self, rel, local, timeout=None):
        if rel == CACHE_REL and not getattr(self, "truncated", False):
            self.truncated = True
            self.calls.append(("fetch", rel))
            data = (self.remote / rel).read_bytes()
            pathlib.Path(local).write_bytes(data[: len(data) // 2])
            return
        super().fetch(rel, local, timeout)


def test_one_truncated_transfer_then_success(tmp_path, monkeypatch):
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, host_cls=TruncateOnce)
    steps = [r["step"] for r in log]
    assert code == 0 and host.status == "EXITED" and host.calls.count("stop") == 1
    assert [(r["file"], r["attempt"], r["why"]) for r in log if r["step"] == "fetch-attempt-failed"] == [
        (CACHE_REL, 1, "sha256")]
    assert "salvaged" not in steps and host.calls.count(("fetch", CACHE_REL)) == 2
    assert (out / "fetched" / CACHE_REL).read_bytes() == (host.remote / CACHE_REL).read_bytes()
    assert result["fetched"][CACHE_REL] == sha((host.remote / CACHE_REL).read_bytes())
    assert not list(out.rglob("*.part"))


class DropRunRecord(FakeHost):
    """scp of the run record fails `drops` times (a reset link), leaving a partial file behind each time."""

    def __init__(self, remote, drops=judge_pod.FETCH_TRIES, **kw):
        super().__init__(remote, **kw)
        self.drops = drops

    def fetch(self, rel, local, timeout=None):
        if rel == RECORD_REL and self.drops > 0:
            self.drops -= 1
            self.calls.append(("fetch", rel))
            pathlib.Path(local).write_bytes(b'{"dev')
            raise podhost.HostError(f"fetch of {rel} failed (exit 1)")
        super().fetch(rel, local, timeout)


def test_a_dropped_run_record_fetch_then_salvage(tmp_path, monkeypatch):
    """Every try of the run fails for the run record: the run's fetch raises with DONE.json recorded (it comes first);
    the salvage keeps DONE.json in place (not fetched again), fetches the run record and then the cache, the pod is
    stopped, then the files are verified."""
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, host_cls=DropRunRecord)
    steps = [r["step"] for r in log]
    assert host.status == "EXITED" and host.calls.count("stop") == 1
    first = next(r for r in log if r["step"] == "fetched")
    assert set(first["files"]) == {"DONE.json"}                                 # the partial fetch, recorded
    assert steps.index("failed") < steps.index("salvaged") < steps.index("stop") < steps.index("verified")
    assert host.calls.count(("fetch", "DONE.json")) == 1 and host.calls.count(("fetch", RECORD_REL)) == 4
    assert host.calls.count(("fetch", CACHE_REL)) == 1
    salvage_timeouts = host.fetch_timeouts[-2:]                                # the run record's 4th try, the cache
    assert all(t is not None and 0 < t <= judge_pod.SALVAGE_BUDGET_S for t in salvage_timeouts)
    assert code == judge_pod.EXIT_OK and result["verification"]["complete"]
    assert set(result["fetched"]) == {CACHE_REL, RECORD_REL, "DONE.json"} and not list(out.rglob("*.part"))
    one = launch_with(tmp_path / "one", monkeypatch, host_cls=DropRunRecord, host_kw={"drops": 1})
    assert one[0] == 0 and "salvaged" not in [r["step"] for r in one[2]]      # one drop: the retry fetches it


def test_fetch_outputs_records_a_partial_fetch_before_raising(tmp_path):
    remote = tmp_path / "remote"
    (remote / "out").mkdir(parents=True)
    for rel, body in ((CACHE_REL, b'{"a": 1}\n'), (RECORD_REL, b'{"exit": 0}'), ("DONE.json", b'{"exit": 0}')):
        (remote / rel).write_bytes(body)
    host = DropRunRecord(remote, drops=judge_pod.FETCH_TRIES)
    lines = []
    fetched = {}
    with pytest.raises(podhost.HostError, match="never had the pod's SHA-256"):
        judge_pod.fetch_outputs(host, tmp_path / "out", lambda step, **f: lines.append((step, f)), fetched,
                                sleep=lambda s: None)
    assert fetched == {"DONE.json": sha((remote / "DONE.json").read_bytes())}             # DONE.json comes first
    assert lines[-1] == ("fetched", {"files": fetched}) and not (tmp_path / "out/fetched" / RECORD_REL).exists()
    assert not list((tmp_path / "out").rglob("*.part")) and ("fetch", CACHE_REL) not in host.calls
    judge_pod.fetch_outputs(host, tmp_path / "out", lambda step, **f: None, fetched, sleep=lambda s: None)
    assert host.calls.count(("fetch", "DONE.json")) == 1 and set(fetched) == {CACHE_REL, RECORD_REL, "DONE.json"}
    (tmp_path / "out/fetched" / CACHE_REL).write_bytes(b"other")      # a file in place with another hash refuses
    with pytest.raises(Refusal, match="does not have the pod's SHA-256"):
        judge_pod.fetch_outputs(host, tmp_path / "out", lambda step, **f: None, {}, sleep=lambda s: None)


# ------------------------------------------------------------------------------------------------ S4: orphan stops

def _pods_api(pods, stop_status=200, listing_ok=True):
    """A fake RunPod API over `pods` (dicts); a stop with stop_status 200 sets desiredStatus EXITED."""
    calls = []

    def api(method, path, payload=None):
        calls.append((method, path))
        if (method, path) == ("GET", "/pods"):
            return (200, [dict(p) for p in pods]) if listing_ok else (0, {"error": "URLError"})
        pod = next((p for p in pods if path.startswith(f"/pods/{p['id']}")), None)
        if pod is None:
            return 404, {}
        if method == "POST" and path.endswith("/stop"):
            if stop_status == 200:
                pod["desiredStatus"] = "EXITED"
            return stop_status, {}
        return 200, dict(pod)
    return api, calls


def test_podhost_unconfirmed_orphan_stops_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    pods = [{"id": "pod-o", "name": "attribution-judge-t1", "desiredStatus": "RUNNING"}]
    api, _ = _pods_api(pods, stop_status=500)
    monkeypatch.setattr(podhost, "api", api)
    host = podhost.RunPodHost("t1", tmp_path / "a", kit=make_kit(tmp_path))
    with pytest.raises(podhost.StopUnconfirmed) as e:                  # F7: raised before the name suffix moves
        host.orphan(list(pods), "test")
    assert e.value.pod_ids == ["pod-o"] and e.value.names == ["attribution-judge-t1"]
    assert host.name() == "attribution-judge-t1" and not (tmp_path / "a/attempt.txt").exists()
    with pytest.raises(podhost.StopUnconfirmed) as e:
        podhost.RunPodHost("t1", tmp_path / "b", kit=tmp_path / "kit").reconcile()
    assert e.value.pod_ids == ["pod-o"] and e.value.names == ["attribution-judge-t1"]
    with pytest.raises(podhost.StopUnconfirmed) as e:
        podhost.RunPodHost("t1", tmp_path / "c", kit=tmp_path / "kit").stop_orphans("interrupted create")
    assert e.value.pod_ids == ["pod-o"] and e.value.names == ["attribution-judge-t1"]
    api, _ = _pods_api(pods, stop_status=200)                          # a confirmed stop: the suffix moves
    monkeypatch.setattr(podhost, "api", api)
    confirmed = podhost.RunPodHost("t1", tmp_path / "d", kit=tmp_path / "kit")
    assert confirmed.orphan(list(pods), "test") is None and confirmed.name() == "attribution-judge-t1-r2"


@pytest.mark.parametrize("appears,listing_ok,want", [(3, True, 1), (None, True, 0), (None, False, "unconfirmed")])
def test_podhost_stop_orphans_lists_three_times_20_s_apart(tmp_path, monkeypatch, appears, listing_ok, want):
    """The pod of an interrupted create shows only in the third listing; or never (none concluded after 3 listings);
    or the listing always fails (no conclusion: StopUnconfirmed). A fake clock records the waits."""
    sleeps, listings, pods = [], {"n": 0}, []
    api, calls = _pods_api(pods, listing_ok=listing_ok)

    def counting(method, path, payload=None):
        if (method, path) == ("GET", "/pods"):
            listings["n"] += 1
            if appears is not None and listings["n"] == appears:
                pods.append({"id": "pod-late", "name": "attribution-judge-t1", "desiredStatus": "RUNNING"})
        return api(method, path, payload)
    monkeypatch.setattr(podhost, "api", counting)
    monkeypatch.setattr(podhost, "SLEEP", sleeps.append)
    host = podhost.RunPodHost("t1", tmp_path / "rec", kit=make_kit(tmp_path))
    if want == "unconfirmed":
        with pytest.raises(podhost.StopUnconfirmed, match="listing failed 3 of 3"):
            host.stop_orphans("interrupted create")
        assert host.orphan_check_done is False
    else:
        assert host.stop_orphans("interrupted create") == want and host.orphan_check_done is True
    assert listings["n"] == 3 and sleeps[:3] == [20, 20, 20]
    if want == 1:
        assert pods[0]["desiredStatus"] == "EXITED" and ("POST", "/pods/pod-late/stop") in calls


def test_launch_maps_unconfirmed_orphan_stops_to_exit_7(tmp_path, monkeypatch, capsys):
    gone = podhost.StopUnconfirmed("the stop of orphan pod(s) ['pod-z'] was not confirmed", ["pod-z"])
    code, host, log, result, _ = launch_with(tmp_path, monkeypatch, {"create_error": (None, KeyboardInterrupt()),
                                                                     "orphans": gone})
    assert code == judge_pod.EXIT_STOP_UNCONFIRMED and result["exit"] == 7 and host.calls[-1] == "stop_orphans"
    assert [r["pod_ids"] for r in log if r["step"] == "STOP-NOT-CONFIRMED"] == [["pod-z"]]
    assert "STOP NOT CONFIRMED" in capsys.readouterr().err
    code, host, log, result, _ = launch_with(tmp_path / "b", monkeypatch, {"fail": {"reconcile": gone}})
    assert code == judge_pod.EXIT_STOP_UNCONFIRMED and not [c for c in host.calls if c == ("create", 1.0)]
    assert [r["pod_ids"] for r in log if r["step"] == "STOP-NOT-CONFIRMED"] == [["pod-z"]]


def test_real_host_interrupted_create_is_found_by_a_later_listing(tmp_path, monkeypatch):
    """The real RunPodHost under launch: RunPod accepts the create, the Mac is interrupted before the reply; the pod
    shows in the listings only from the second one after the create. It is stopped (EXITED) and the launch exits 4."""
    for k, v in SECRET_ENV.items():
        monkeypatch.setenv(k, v)
    retrieved, prepared, _, _ = setup_units(tmp_path, monkeypatch)
    pods, listings, sleeps = [], {"after_create": 0}, []
    api, calls = _pods_api(pods)

    def interrupted(method, path, payload=None):
        if (method, path) == ("POST", "/pods"):
            pods.append({"id": "pod-acc", "name": payload["name"], "desiredStatus": "RUNNING", "costPerHr": 1.79})
            calls.append((method, path))
            raise KeyboardInterrupt()                                  # Ctrl-C while the reply is in flight
        if (method, path) == ("GET", "/pods") and pods:
            listings["after_create"] += 1
            if listings["after_create"] < 2:
                return 200, []                                         # RunPod's listing lags behind the create
        return api(method, path, payload)

    def runner(argv, **kw):
        if "pod-timer-settings" in argv:
            pathlib.Path(argv[argv.index("--out") + 1]).write_text(json.dumps(fake_settings(1.0)))
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        if str(argv[1]).endswith("budget.py"):
            return types.SimpleNamespace(returncode=0, stdout='{"allowed": true, "balance": 30.0}\n', stderr="")
        raise AssertionError(argv[0])
    monkeypatch.setattr(podhost, "api", interrupted)
    monkeypatch.setattr(podhost, "SLEEP", sleeps.append)
    kit = make_kit(tmp_path)
    host = podhost.RunPodHost("t1", kit=kit, budget_kit=kit, runner=runner)
    clock = Clock()
    code = judge_pod.launch(args_for("launch", "t1", None, retrieved, prepared), host=host, clock=clock,
                            sleep=clock.sleep, signals=False)
    assert code == judge_pod.EXIT_CREATE and pods[0]["desiredStatus"] == "EXITED"
    assert listings["after_create"] == 2 and sleeps[:2] == [20, 20]
    orphans = [json.loads(x) for x in (host.records / "orphans.jsonl").read_text().splitlines()]
    assert [(o["id"], o["stop"]["confirmed"]) for o in orphans] == [("pod-acc", True)]
    log = read_log(judge_pod.JUDGE_POD_ROOT / "t1")
    assert [r["stopped"] for r in log if r["step"] == "orphan-check"] == [1]


# ------------------------------------------------------------------------------------------------ S5: the price rule

@pytest.mark.parametrize("price,stopped", [(1.79, False), (2.5, False), (10.0, False), (10.01, True), (49.0, True), (None, True),
                                           ("1.79", True), (True, True), (float("nan"), True), (float("inf"), True)])
def test_podhost_price_check_has_a_10_dollar_hourly_limit(tmp_path, monkeypatch, price, stopped):
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    stops = []

    def api(method, path, payload=None):
        if (method, path) == ("POST", "/pods"):
            return 200, {"id": "p1", "name": payload["name"], "costPerHr": price}
        if path.endswith("/stop"):
            stops.append(path)
            return 200, {}
        return 200, {"desiredStatus": "EXITED"}
    monkeypatch.setattr(podhost, "api", api)
    host = podhost.RunPodHost("t1", tmp_path / "rec", kit=make_kit(tmp_path))
    monkeypatch.setattr(host, "timer_settings", fake_settings)
    if stopped:
        with pytest.raises(podhost.HostError, match="not a finite number"):
            host.create(1.0)
        assert stops == ["/pods/p1/stop"] and host.pod_id is None and host.orphan_check_done is True
        json.loads((tmp_path / "rec/price-guard-stop.json").read_text())      # strict JSON even for NaN or inf
    else:
        assert host.create(1.0)["id"] == "p1" and host.pod_id == "p1" and stops == []
    assert podhost.PRICE_GUARD == 10.0 and podhost.PLANNING_PRICE == 1.85


def test_the_budget_kit_defaults_to_the_reserve_1_kit():
    a = judge_pod.parser().parse_args(["launch", "--tag", "x1", "--unit", "u"])
    assert a.budget_kit == podhost.BUDGET_KIT == podhost.ROOT / "tmp/family-probe-olmo2-1b-bt"
    assert a.ssh_kit == podhost.KIT
    budget = load_kit_budget()
    assert budget.RESERVE_USD == 1.0 and budget.MAX_PRICE == podhost.PLANNING_PRICE


def test_nothing_left_to_judge_refuses(tmp_path, monkeypatch):
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, extra=("--limit", "0"))
    assert code == judge_pod.EXIT_REFUSED and host.calls == [] and result is None
    assert any(r["step"] == "refused" and "nothing is left to judge" in r["reason"] for r in log)
    code, host, log, result, out = launch_with(tmp_path / "b", monkeypatch)              # a complete launch,
    assert code == 0
    retrieved, prepared = tmp_path / "b/kit/retrieved", tmp_path / "b/prepared-test"
    host2 = FakeHost(tmp_path / "b/remote2")
    assert judge_pod.launch(args_for("launch", "t2", None, retrieved, prepared, "--resume-from", str(out)), host=host2,
                            signals=False) == judge_pod.EXIT_REFUSED                   # then a resume of it
    assert host2.calls == []
    assert any("nothing is left to judge" in (r.get("reason") or "") for r in read_log(judge_pod.JUDGE_POD_ROOT / "t2"))


# ------------------------------------------------------------------------------------------------ S6: torch and the text path

class _Backend:
    def __init__(self, model, truncation=None):
        self.model, self.truncation = model, truncation

    def to_str(self):
        return json.dumps({"version": "1.0", "truncation": self.truncation, "added_tokens": [], "model": self.model})


def _tok(vocab, merges, truncation=None):
    return types.SimpleNamespace(backend_tokenizer=_Backend({"type": "BPE", "vocab": vocab, "merges": merges},
                                                            truncation))


def test_tokenizer_fingerprint_is_the_vocab_and_merges():
    vocab, merges = {"<unk>": 0, "<s>": 1, "a": 2, "b": 3, "ab": 4}, [["a", "b"]]
    want = hashlib.sha256(json.dumps({"vocab": vocab, "merges": merges}, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()
    assert pod_judge.tokenizer_fingerprint(_tok(vocab, merges)) == want
    shuffled = dict(reversed(list(vocab.items())))                    # key order and other backend state: no effect
    assert pod_judge.tokenizer_fingerprint(_tok(shuffled, merges, truncation={"max_length": 512})) == want
    assert pod_judge.tokenizer_fingerprint(_tok(vocab, [["b", "a"]])) != want
    assert pod_judge.tokenizer_fingerprint(_tok({**vocab, "ab": 5}, merges)) != want


def test_the_mac_venv_has_no_text_path_extras():
    from importlib import metadata
    try:
        metadata.version("transformers")
    except metadata.PackageNotFoundError:
        pytest.skip("not the minimal venv")
    assert pod_judge.text_path_extras() == []                         # so the Mac's tokenizer path is the pure-Python one


def test_pod_job_run_records_the_tokenizer_fingerprint(tmp_path, monkeypatch):
    root, units, built = built_bundle(tmp_path, monkeypatch)
    order = []
    monkeypatch.setattr(pod_judge, "require_pod_packages", lambda: order.append("packages") or {"transformers": "4.56.2"})
    monkeypatch.setattr(pod_judge, "verify_snapshot", lambda: order.append("snapshot") or {})
    monkeypatch.setattr(pod_judge, "tokenizer_fingerprint", lambda: order.append("fingerprint") or "f" * 64)
    monkeypatch.setattr(pod_judge, "make_factory", lambda device: synth.fake_factory({}, {}))
    cache, record = tmp_path / "pod/out/c.jsonl", tmp_path / "pod/out/r.json"
    assert pod_job.main(["run", "--bundle", str(root), "--cache", str(cache), "--record", str(record)],
                        env_probe=fake_env) == 0
    rec = json.loads(record.read_bytes())
    assert rec["tokenizer_fingerprint"] == "f" * 64 and order == ["packages", "snapshot", "fingerprint"]


def test_parity_tokenizer_check_and_the_mac_side_refusal(tmp_path, monkeypatch):
    run = write_run_record(tmp_path / "r.json", "c" * 64)
    assert parity.tokenizer_check(run, "c" * 64) == {"mac": "c" * 64, "pod": "c" * 64, "identical": True}
    assert parity.tokenizer_check(run, "d" * 64)["identical"] is False
    with pytest.raises(Refusal, match="not a cuda"):
        parity.tokenizer_check(write_run_record(tmp_path / "m.json", "c" * 64, device="mps"), "c" * 64)
    u = parity_setup(tmp_path / "u", n=4, samples=1)
    mac = fill(tmp_path / "mac.jsonl", u, base_label)
    rep = parity.compare(mac, mac, [u], {"mac": "c" * 64, "pod": "d" * 64, "identical": False})
    assert rep["verdict"] == "FAIL" and all(r["verdict"] == "PASS" for r in rep["rows"])
    monkeypatch.setattr(pod_judge, "text_path_extras", lambda: ["protobuf==5.29.0"])
    with pytest.raises(Refusal, match="protobuf"):
        parity.mac_tokenizer_fingerprint()
    monkeypatch.setattr(pod_judge, "text_path_extras", lambda: [])
    monkeypatch.setattr(pod_judge, "tokenizer_fingerprint", lambda: "e" * 64)
    assert parity.mac_tokenizer_fingerprint() == "e" * 64


def test_pod_judge_text_path_command(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")}
    p = subprocess.run([sys.executable, "-I", "-B", str(POD_DIR / "pod_judge.py"), "text-path"], capture_output=True,
                       text=True, env=env, timeout=120, cwd=tmp_path)
    assert p.returncode == (3 if pod_judge.text_path_extras() else 0) and p.stdout == ""


# ------------------------------------------------------------------------------------------------ the second review: F1-F13
# Child-process tests use real signals; each child sets RLIMIT_CORE to 0 (a mutant's default SIGQUIT writes no core).

class PlainPatch:
    """The two monkeypatch calls setup_units makes, for the child-process drivers."""

    def setattr(self, obj, name, value):
        setattr(obj, name, value)

    def setenv(self, k, v):
        os.environ[k] = v


def child_env():
    env = {k: v for k, v in os.environ.items() if k not in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "RUNPOD_OPERATOR_API_KEY")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def kit_runner(cap_hours=1.0, budget=None):
    """The real host's child processes, faked: the timer settings (a cap `cap_hours` from now) and budget.py check
    (`budget(argv)` -> (returncode, stdout); default: allowed)."""
    cap = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=cap_hours)).isoformat(timespec="seconds")

    def runner(argv, **kw):
        if "pod-timer-settings" in argv:
            pathlib.Path(argv[argv.index("--out") + 1]).write_text(json.dumps({**fake_settings(1.0), "cap_stop_utc": cap}))
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        if str(argv[1]).endswith("budget.py"):
            rc, out = budget(argv) if budget else (0, '{"allowed": true, "balance": 30.0}\n')
            return types.SimpleNamespace(returncode=rc, stdout=out, stderr="")
        raise AssertionError(argv[0])
    return runner


class NoSshHost(podhost.RunPodHost):
    """The real host with no pod behind SSH: wait_ssh fails at once (the launch then stops the pod)."""

    def wait_ssh(self, seconds=1200):
        raise podhost.HostError("no SSH (fake)")

    def shorten_timer(self, seconds, script):
        raise podhost.HostError("no SSH (fake)")


def launch_real_host(tmp_path, monkeypatch, api, host_cls=podhost.RunPodHost, runner=None, extra=()):
    """judge_pod.launch with the real RunPodHost over a fake RunPod API (no SSH, no network)."""
    for k, v in SECRET_ENV.items():
        monkeypatch.setenv(k, v)
    retrieved, prepared, _, _ = setup_units(tmp_path, monkeypatch)
    monkeypatch.setattr(podhost, "api", api)
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    kit = make_kit(tmp_path)
    host = host_cls("t1", kit=kit, budget_kit=kit, runner=runner or kit_runner())
    clock = Clock()
    code = judge_pod.launch(args_for("launch", "t1", None, retrieved, prepared, *extra), host=host, clock=clock,
                            sleep=clock.sleep, signals=False)
    return code, host, read_log(judge_pod.JUDGE_POD_ROOT / "t1")


S1_DRIVER = r'''
import json, os, pathlib, resource, signal, sys
sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
sys.path.insert(0, sys.argv[1])
import test_judge_pod as T
import judge_pod, podhost
tmp, scenario = pathlib.Path(sys.argv[2]), sys.argv[3]
judge_pod.JUDGE_POD_ROOT = tmp / "judge-pod"
podhost.JUDGE_HOSTS = tmp / "judge-hosts"
podhost.BUDGET_LOCK = tmp / "budget.lock"
T.setup_units(tmp, T.PlainPatch())
for k, v in T.SECRET_ENV.items():
    os.environ[k] = v
NAMES = ("SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT")
ALL = tuple(getattr(signal, n) for n in NAMES)
seen = {"sent": [], "at_stop": None, "during_poll": None}


def kill(*sigs):
    for s in sigs:
        seen["sent"].append(int(s))
        os.kill(os.getpid(), s)


class Host(T.FakeHost):
    def run(self, command, timeout=120, stdin_path=None):
        if " status --root" in command and not getattr(self, "polled", False):
            self.polled = True
            seen["during_poll"] = str(signal.getsignal(signal.SIGHUP))
            first = {"hup-then-stop-signals": signal.SIGHUP, "nohup": signal.SIGHUP, "first-sigterm": signal.SIGTERM,
                     "first-sigquit": signal.SIGQUIT}.get(scenario)
            if first is not None:
                kill(first)
        if scenario == "signals-in-salvage" and command.startswith("pkill"):
            kill(*ALL)                                          # during the salvage's SIGTERM to the job
        return super().run(command, timeout, stdin_path)

    def stop(self):
        seen["at_stop"] = [str(signal.getsignal(s)) for s in ALL]
        if scenario != "nohup":
            kill(*ALL)                                          # while the stop runs
        return super().stop()


if scenario == "signals-in-salvage":
    host = Host(tmp / "remote", fail={"status": 255})
elif scenario == "signal-at-finish-entry":
    host = Host(tmp / "remote")
    real_finish, count = judge_pod.finish, {"n": 0}

    def finish(*a, **k):
        count["n"] += 1
        if count["n"] == 1:
            kill(signal.SIGTERM)                                # handled before finish()'s ignore() runs
        return real_finish(*a, **k)
    judge_pod.finish = finish
else:
    host = Host(tmp / "remote", mode="hang")
if scenario == "nohup":
    signal.signal(signal.SIGHUP, signal.SIG_IGN)                # as under `nohup`
before = {n: signal.getsignal(getattr(signal, n)) for n in NAMES}
clock = T.Clock()
a = T.args_for("launch", "t1", None, tmp / "kit/retrieved", tmp / "prepared-test")
raised = None
try:
    code = judge_pod.launch(a, host=host, clock=clock, sleep=clock.sleep, signals=True)
except BaseException as e:  # noqa: BLE001
    code, raised = None, type(e).__name__
after = {n: signal.getsignal(getattr(signal, n)) for n in NAMES}
(tmp / "driver.json").write_text(json.dumps({
    "code": code, "raised": raised, "status": host.status, "stops": host.calls.count("stop"),
    "terminates": host.calls.count("terminate"), "restored": before == after, "sent": seen["sent"],
    "at_stop": seen["at_stop"], "during_poll": seen["during_poll"], "cap": host.cap_stop_utc}))
'''


def run_s1(tmp_path, scenario):
    script = tmp_path / "s1_driver.py"
    script.write_text(S1_DRIVER)
    p = subprocess.run([sys.executable, "-B", str(script), str(HERE), str(tmp_path), scenario], capture_output=True,
                       text=True, env=child_env(), timeout=300, cwd=tmp_path, stdin=subprocess.DEVNULL)
    assert (tmp_path / "driver.json").exists(), (p.returncode, p.stderr[-2000:])
    r = json.loads((tmp_path / "driver.json").read_text())
    log = read_log(tmp_path / "judge-pod/t1")
    no_text_or_secret(p.stdout, p.stderr, (tmp_path / "judge-pod/t1/judge-pod-log.jsonl").read_bytes())
    return r, log, [x["step"] for x in log], p


IGNORED = [str(signal.SIG_IGN)] * 4


def test_f2_signals_during_the_salvage_and_the_stop_are_ignored(tmp_path):
    """No signal before the finally block (the status is never readable, so the salvage runs). Real SIGINT, SIGTERM,
    SIGHUP and SIGQUIT arrive during the salvage's SIGTERM to the job and again during the stop: finish() ignored all
    four first, the pod is stopped once, the code is the salvaged files' verdict (0), and the handlers are restored
    only after the stop (all four were SIG_IGN while it ran)."""
    r, log, steps, p = run_s1(tmp_path, "signals-in-salvage")
    assert r["raised"] is None and r["status"] == "EXITED" and r["stops"] == 1 and r["restored"], r
    assert len(r["sent"]) == 8 and r["code"] == judge_pod.EXIT_OK and r["at_stop"] == IGNORED
    assert "salvaged" in steps and "late-signal" not in steps and steps[-1] == "end"
    assert "interrupted:" not in p.stderr                              # no signal reached the handler


def test_f2_sighup_then_signals_during_the_stop(tmp_path):
    """SIGHUP during the poll (the one-shot handler: one line, then the salvage), then all four during the stop: the
    stop runs once with every signal ignored, and the original handlers come back only after it."""
    r, log, steps, p = run_s1(tmp_path, "hup-then-stop-signals")
    assert r["raised"] is None and r["status"] == "EXITED" and r["stops"] == 1 and r["restored"], r
    assert r["code"] == judge_pod.EXIT_STOPPED and "salvaged" in steps and "late-signal" not in steps
    assert r["at_stop"] == IGNORED and len(r["sent"]) == 5
    want = (f"interrupted: stopping pod pod-fake-1; further signals are ignored; the in-pod timer stops it at "
            f"{r['cap']}")
    assert p.stderr.count("interrupted:") == 1 and want in p.stderr, p.stderr[-800:]


def test_f2_a_sigterm_at_finish_entry_runs_the_second_finish(tmp_path):
    """The try block completed (code 0); a SIGTERM is handled as finish() starts, before its ignore(): the exception
    leaves the finally block, the outer except logs late-signal and runs finish() again, which stops the pod once."""
    r, log, steps, p = run_s1(tmp_path, "signal-at-finish-entry")
    assert r["raised"] is None and r["status"] == "EXITED" and r["stops"] == 1 and r["restored"], r
    assert "late-signal" in steps and steps.count("end") == 1 and r["code"] == judge_pod.EXIT_OK
    assert steps.index("late-signal") < steps.index("stop") and r["at_stop"] == IGNORED


@pytest.mark.parametrize("scenario,signum", [("first-sigterm", signal.SIGTERM), ("first-sigquit", signal.SIGQUIT)])
def test_f1_f6_a_first_sigterm_or_sigquit_skips_the_salvage_and_stops(tmp_path, scenario, signum):
    """F1: SIGQUIT (Ctrl-\\) is caught like the others, and the first signal prints one line naming the pod and the
    timer's stop time; later signals (all four during the stop) are ignored and print nothing. F6: a first SIGTERM
    or SIGQUIT skips the salvage (no SIGTERM to the job, no fetch): the stop comes first; exit 6."""
    r, log, steps, p = run_s1(tmp_path, scenario)
    assert r["raised"] is None and r["status"] == "EXITED" and r["stops"] == 1 and r["restored"], r
    assert r["code"] == judge_pod.EXIT_FAILED and r["terminates"] == 0 and "salvaged" not in steps
    assert [x["signal"] for x in log if x["step"] == "salvage-skipped"] == [int(signum)]
    assert next(x for x in log if x["step"] == "failed")["error"] == "Interrupted"
    want = (f"interrupted: stopping pod pod-fake-1; further signals are ignored; the in-pod timer stops it at "
            f"{r['cap']}")
    assert p.stderr.count("interrupted:") == 1 and want in p.stderr, p.stderr[-800:]


def test_f3_a_sighup_ignored_at_the_start_stays_ignored(tmp_path):
    """Started under nohup (SIGHUP is SIG_IGN): install() leaves it so, a SIGHUP during the poll does nothing, and the
    run goes on to its cap (the deadline path: SIGTERM to the job, exit 5); SIG_IGN is what restore() puts back."""
    r, log, steps, p = run_s1(tmp_path, "nohup")
    assert r["raised"] is None and r["status"] == "EXITED" and r["stops"] == 1 and r["restored"], r
    assert r["during_poll"] == str(signal.SIG_IGN) and r["sent"] == [int(signal.SIGHUP)]
    assert r["code"] == judge_pod.EXIT_STOPPED and "deadline" in steps and "failed" not in steps
    assert "interrupted:" not in p.stderr


DEAD_OUTPUT_DRIVER = r'''
import os, pathlib, pty, resource, sys
sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
tests, tmp, kind, outcome = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3], sys.argv[4]
sys.path.insert(0, tests)
import test_judge_pod as T
import judge_pod, podhost
judge_pod.JUDGE_POD_ROOT = tmp / "judge-pod"
podhost.JUDGE_HOSTS = tmp / "judge-hosts"
podhost.BUDGET_LOCK = tmp / "budget.lock"
T.setup_units(tmp, T.PlainPatch())
for k, v in T.SECRET_ENV.items():
    os.environ[k] = v
if outcome == "unconfirmed":
    host = T.FakeHost(tmp / "remote", stop_confirms=(False, False))                         # exit 7
elif outcome == "failed":
    host = T.FakeHost(tmp / "remote", fail={"wait_ssh": podhost.HostError("no SSH (fake)")})   # exit 6
else:
    host = T.FakeHost(tmp / "remote", mode="hang")                                           # the cap: exit 5
if kind == "pipe":                      # the reader of `| tee` died: every write raises EPIPE
    r, w = os.pipe()
    os.close(r)
    os.dup2(w, 1)
    os.dup2(w, 2)
    os.close(w)
else:                                   # the terminal window closed: every write raises EIO
    master, slave = pty.openpty()
    os.dup2(slave, 1)
    os.dup2(slave, 2)
    os.close(slave)
    os.close(master)
clock = T.Clock()
a = T.args_for("launch", "t1", None, tmp / "kit/retrieved", tmp / "prepared-test")
code = judge_pod.launch(a, host=host, clock=clock, sleep=clock.sleep, signals=True)
(tmp / "launch-returned").write_text(f"{code} {host.status}")
sys.exit(code)
'''


@pytest.mark.parametrize("kind,outcome,want", [("pipe", "unconfirmed", 7), ("pty", "unconfirmed", 7),
                                                ("pipe", "failed", 6), ("pty", "cap", 5)])
def test_f4_a_dead_stdout_and_stderr_keep_the_documented_exit_code(tmp_path, kind, outcome, want):
    """A real closed pipe and a real closed pty as the child's stdout and stderr: the first failed echo (and the
    first failed say) points the dead descriptor at /dev/null, so the interpreter's exit flush of the unwritten
    buffer succeeds and the process exits with the launcher's code, not 120."""
    script = tmp_path / "dead_driver.py"
    script.write_text(DEAD_OUTPUT_DRIVER)
    p = subprocess.run([sys.executable, "-B", str(script), str(HERE), str(tmp_path), kind, outcome],
                       capture_output=True, env=child_env(), timeout=300, cwd=tmp_path, stdin=subprocess.DEVNULL)
    status = "RUNNING" if outcome == "unconfirmed" else "EXITED"         # the fake pod's stop is never confirmed
    assert (tmp_path / "launch-returned").read_text() == f"{want} {status}", p.returncode
    assert p.returncode == want
    log = read_log(tmp_path / "judge-pod/t1")
    assert [x["exit"] for x in log if x["step"] == "end"] == [want]
    if outcome == "unconfirmed":
        assert any(x["step"] == "STOP-NOT-CONFIRMED" for x in log)


class AllOutputs(FakeHost):
    """The job also wrote the three diagnostics; every transfer of out/pip.log fails."""

    def _start_job(self, limit, factory):
        super()._start_job(limit, factory)
        for rel in judge_pod.FETCH_BEST_EFFORT:
            (self.remote / rel).write_text("diagnostic\n")

    def fetch(self, rel, local, timeout=None):
        if rel == "out/pip.log":
            self.calls.append(("fetch", rel))
            raise podhost.HostError("fetch of out/pip.log failed (exit 1)")
        super().fetch(rel, local, timeout)


def test_f5_fetch_order_and_best_effort_diagnostics(tmp_path, monkeypatch):
    """DONE.json, the run record and the cache are fetched first; the diagnostics after them, best effort: pip.log
    never arrives (3 tries, then fetch-skipped), the run still completes with exit 0 and no salvage."""
    assert set(judge_pod.FETCH_FIRST + judge_pod.FETCH_BEST_EFFORT) == set(pod_job.OUTPUTS)
    assert judge_pod.FETCH_FIRST == ("DONE.json", RECORD_REL, CACHE_REL)
    assert set(judge_pod.FETCH_BEST_EFFORT) == {"out/pip.log", "out/environment-pod.lock", "out/snapshot-check.json"}
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, host_cls=AllOutputs)
    steps = [r["step"] for r in log]
    order = [c[1] for c in host.calls if isinstance(c, tuple) and c[0] == "fetch"]
    assert order[:3] == ["DONE.json", RECORD_REL, CACHE_REL]
    assert sorted(set(order[3:])) == sorted(judge_pod.FETCH_BEST_EFFORT) and order.count("out/pip.log") == 3
    assert code == judge_pod.EXIT_OK and "salvaged" not in steps and "failed" not in steps
    assert [(r["file"], r["error"]) for r in log if r["step"] == "fetch-skipped"] == [("out/pip.log", "HostError")]
    assert set(result["fetched"]) == {"DONE.json", RECORD_REL, CACHE_REL, "out/environment-pod.lock",
                                      "out/snapshot-check.json"}
    assert host.status == "EXITED" and host.calls.count("stop") == 1


class SlowCacheLink(FakeHost):
    """Every scp of the cache runs to its timeout (the fake clock advances by it), then fails."""

    def __init__(self, remote, clock=None, **kw):
        super().__init__(remote, **kw)
        self.clock, self.salvage_t0, self.stop_t = clock, None, None

    def run(self, command, timeout=120, stdin_path=None):
        if command.startswith("pkill") and self.salvage_t0 is None:
            self.salvage_t0 = self.clock.t
        return super().run(command, timeout, stdin_path)

    def fetch(self, rel, local, timeout=None):
        if rel == CACHE_REL:
            self.calls.append(("fetch", rel))
            self.fetch_timeouts.append(timeout)
            self.clock.t += podhost.FETCH_TIMEOUT_S if timeout is None else timeout
            raise podhost.HostError(f"scp of {rel} timed out")
        super().fetch(rel, local, timeout)

    def stop(self):
        self.stop_t = self.clock.t
        return super().stop()


def test_f6_the_salvage_has_a_300_s_budget(tmp_path, monkeypatch):
    """The run's fetch of the cache times out 3 times (900 s each, the fake clock); the salvage then gets 300 s in
    all: its scp timeout is cut to the time left, no retry starts after it, and the stop follows within 300 s of the
    salvage's start (the earlier code took 3 more times 900 s)."""
    for k, v in SECRET_ENV.items():
        monkeypatch.setenv(k, v)
    retrieved, prepared, _, _ = setup_units(tmp_path, monkeypatch)
    clock = Clock()
    host = SlowCacheLink(tmp_path / "remote", clock=clock)
    code = judge_pod.launch(args_for("launch", "t1", None, retrieved, prepared), host=host, clock=clock,
                            sleep=clock.sleep, signals=False)
    log = read_log(judge_pod.JUDGE_POD_ROOT / "t1")
    cache_timeouts = [t for c, t in zip([c for c in host.calls if isinstance(c, tuple) and c[0] == "fetch"],
                                        host.fetch_timeouts) if c[1] == CACHE_REL]
    assert judge_pod.SALVAGE_BUDGET_S == 300 and host.salvage_t0 is not None
    assert 0 < host.stop_t - host.salvage_t0 <= judge_pod.SALVAGE_BUDGET_S, host.stop_t - host.salvage_t0
    assert cache_timeouts[:3] == [None, None, None]                        # the run: podhost's own 900 s
    assert len(cache_timeouts) == 4 and 0 < cache_timeouts[3] <= judge_pod.SALVAGE_BUDGET_S
    assert code == judge_pod.EXIT_FAILED and host.status == "EXITED" and host.calls.count("stop") == 1
    assert [r["error"] for r in log if r["step"] == "salvage-failed"] == ["HostError"]


def test_f6_time_left():
    clock = Clock()
    assert judge_pod.time_left(None, clock, 900) == 900
    assert judge_pod.time_left(clock.t + 300, clock, 900) == 300 and judge_pod.time_left(clock.t + 300, clock, 60) == 60
    with pytest.raises(podhost.HostError, match="budget"):
        judge_pod.time_left(clock.t + 0.5, clock, 60)


def test_f7_an_unconfirmed_orphan_stop_names_the_real_pod(tmp_path, monkeypatch, capsys):
    """reconcile finds a running pod of this name without pod.json and RunPod never confirms its stop: exit 7, and
    STOP-NOT-CONFIRMED names that pod's id and its real name; the name suffix did not move (no -r2 pod is named)."""
    pods = [{"id": "pod-old", "name": "attribution-judge-t1", "desiredStatus": "RUNNING"}]
    api, _ = _pods_api(pods, stop_status=500)
    code, host, log = launch_real_host(tmp_path, monkeypatch, api)
    (line,) = [r for r in log if r["step"] == "STOP-NOT-CONFIRMED"]
    assert code == judge_pod.EXIT_STOP_UNCONFIRMED and line["pod_ids"] == ["pod-old"]
    assert line["name"] == "attribution-judge-t1" and host.name() == "attribution-judge-t1"
    assert not (host.records / "attempt.txt").exists()
    assert "named attribution-judge-t1 may still run" in capsys.readouterr().err


def test_f7_a_lost_reply_whose_listed_pod_will_not_stop(tmp_path, monkeypatch):
    """The create reply is lost, the listing shows the pod, its stop is never confirmed: exit 7; every
    STOP-NOT-CONFIRMED line names the real pod (the create's name), also after finish()'s second listing."""
    pods = []

    def api(method, path, payload=None):
        if (method, path) == ("POST", "/pods"):
            pods.append({"id": "pod-lost", "name": payload["name"], "desiredStatus": "RUNNING", "costPerHr": 1.79})
            return 0, {"error": "TimeoutError"}
        if (method, path) == ("GET", "/pods"):
            return 200, [dict(p) for p in pods]
        if path.endswith("/stop"):
            return 500, {}
        return 200, dict(pods[0])
    code, host, log = launch_real_host(tmp_path, monkeypatch, api)
    lines = [(r["pod_ids"], r["name"]) for r in log if r["step"] == "STOP-NOT-CONFIRMED"]
    assert code == judge_pod.EXIT_STOP_UNCONFIRMED and pods[0]["desiredStatus"] == "RUNNING"
    assert lines and all(x == (["pod-lost"], "attribution-judge-t1") for x in lines), lines
    assert host.name() == "attribution-judge-t1"


def _lost_create_api(pods, reply):
    """POST /pods: `reply` is (status, body) or an exception to raise; no listing ever shows a pod (RunPod lags)."""
    calls = []

    def api(method, path, payload=None):
        calls.append((method, path))
        if (method, path) == ("POST", "/pods"):
            if isinstance(reply, BaseException):
                raise reply
            return reply
        if (method, path) == ("GET", "/pods"):
            return 200, [dict(p) for p in pods]
        return 404, {}
    return api, calls


@pytest.mark.parametrize("reply,want", [((0, {"error": "TimeoutError"}), 7), ((200, None), 7), ((202, None), 7),
                                        (KeyboardInterrupt(), 7), ((500, {"error": "no capacity"}), 7),
                                        ((502, {"error": "bad gateway"}), 7), ((400, {"error": "bad request"}), 4)])
def test_f8_a_lost_or_interrupted_create_reply_with_no_pod_listed_exits_7(tmp_path, monkeypatch, reply, want):
    """A lost reply (status 0, or a 2xx reply without an id), a 5xx reply (G3, the lead's decision: a gateway error can
    come back for a create that went through) or an interrupted one, and 3 listings that show no pod: nothing can be
    concluded (RunPod may list the pod later), so CHECK-CONSOLE and exit 7, not 4. Only a 4xx reply with no pod listed
    is a refused create: exit 4. The create intent stays without pod.json (budget.py counts it)."""
    api, calls = _lost_create_api([], reply)
    code, host, log = launch_real_host(tmp_path, monkeypatch, api)
    steps = [r["step"] for r in log]
    assert code == want and calls.count(("GET", "/pods")) == 1 + 3                 # reconcile, then 3 listings
    assert ("CHECK-CONSOLE" in steps) is (want == 7) and "STOP-NOT-CONFIRMED" not in steps
    if want == 7:
        (line,) = [r for r in log if r["step"] == "CHECK-CONSOLE"]
        assert line["name"] == "attribution-judge-t1" and line["cap_stop_utc"]
    assert (host.records / "create-intent.json").exists() and not (host.records / "pod.json").exists()


def test_f8_an_interrupt_before_the_create_request_lists_nothing(tmp_path, monkeypatch):
    """Ctrl-C while the timer settings are made (before any create request): no pod can exist, so no listing and
    exit 4; the create flag says the request was never sent."""
    api, calls = _lost_create_api([], (500, {}))
    base = kit_runner()

    def runner(argv, **kw):
        if "pod-timer-settings" in argv:
            raise KeyboardInterrupt()
        return base(argv, **kw)
    code, host, log = launch_real_host(tmp_path, monkeypatch, api, runner=runner)
    assert code == judge_pod.EXIT_CREATE and host.create_sent is False
    assert calls == [("GET", "/pods")] and "orphan-check" not in [r["step"] for r in log]


def test_f9_a_stop_record_that_cannot_be_written_is_still_a_confirmed_stop(tmp_path, monkeypatch):
    """stops.jsonl cannot be appended (a directory stands for a full disk): the stop is still confirmed (exit 6 for
    the failed SSH, not a false 7), and stop() returns stop_id's result unchanged."""
    pod = {"id": "pod-c", "desiredStatus": "RUNNING"}

    def api(method, path, payload=None):
        if (method, path) == ("POST", "/pods"):
            pod["name"] = payload["name"]
            return 201, {**pod, "costPerHr": 1.79}
        if (method, path) == ("GET", "/pods"):
            return 200, []
        if path.endswith("/stop"):
            pod["desiredStatus"] = "EXITED"
            return 200, {}
        return 200, dict(pod)
    monkeypatch.setattr(podhost, "JUDGE_HOSTS", tmp_path / "judge-hosts")
    (tmp_path / "judge-hosts/judge-t1/stops.jsonl").mkdir(parents=True)
    code, host, log = launch_real_host(tmp_path, monkeypatch, api, host_cls=NoSshHost)
    steps = [r["step"] for r in log]
    assert code == judge_pod.EXIT_FAILED and pod["desiredStatus"] == "EXITED"
    assert "STOP-NOT-CONFIRMED" not in steps and "stop-error" not in steps and host.records_dropped == 1
    marker = {"confirmed": True, "marker": object()}
    monkeypatch.setattr(podhost, "stop_id", lambda pod_id: marker)
    assert host.stop() is marker and host.records_dropped == 2


def test_f9_an_orphan_record_that_cannot_be_written_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    pods = [{"id": "pod-o", "name": "attribution-judge-t1", "desiredStatus": "RUNNING"}]
    api, _ = _pods_api(pods)
    monkeypatch.setattr(podhost, "api", api)
    host = podhost.RunPodHost("t1", tmp_path / "rec", kit=make_kit(tmp_path))
    (tmp_path / "rec/orphans.jsonl").mkdir()
    assert host.orphan(list(pods), "test") is None and host.records_dropped == 1
    assert pods[0]["desiredStatus"] == "EXITED" and host.name() == "attribution-judge-t1-r2"


def test_f10_a_budget_refused_after_the_create_stops_the_pod(tmp_path, monkeypatch):
    """The guard allows the create at the planning rate; the check after the create (0 extra hours, the new pod now
    counted at its real price) refuses: exit 3, the pod is stopped once, and nothing runs on it."""
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, {"allowed": [True, False]})
    guards = [c for c in host.calls if isinstance(c, tuple) and c[0] in ("budget_check", "create")]
    assert guards == [("budget_check", 1.0, podhost.PLANNING_PRICE), ("create", 1.0),
                      ("budget_check", 0.0, podhost.PLANNING_PRICE)]
    assert code == judge_pod.EXIT_BUDGET and result["exit"] == 3 and host.status == "EXITED"
    assert host.calls.count("stop") == 1 and "wait_ssh" not in host.calls and result["stop"]["confirmed"]
    assert [r["allowed"] for r in log if r["step"] == "budget-guard-after-create"] == [False]


def test_f10_the_kits_budget_py_refuses_after_the_create_at_the_real_price(tmp_path, monkeypatch):
    """The default budget kit's real budget.py (read as code, run in-process with a fake account; its HERE in tmp):
    before the create, 1 h at $1.85 fits a $10 balance; RunPod then reports $9.50/h for the pod (below the $10/h creation
    limit of 9 Oct, so the price check passes it), and the check after the create counts it at $9.50 until its cap
    (pod.json): refused, exit 3, the pod stopped."""
    b = load_kit_budget()
    fake_tmp = tmp_path / "tmp"
    monkeypatch.setattr(b, "HERE", fake_tmp / "family-probe-olmo2-1b-bt")
    b.HERE.mkdir(parents=True)
    monkeypatch.setattr(podhost, "JUDGE_HOSTS", fake_tmp / "family-probe-judge" / "hosts")
    pods = []

    def api(method, path, payload=None):
        if (method, path) == ("POST", "/pods"):
            pods.append({"id": "pod-49", "name": payload["name"], "desiredStatus": "RUNNING", "costPerHr": 9.5})
            return 201, dict(pods[0])
        if (method, path) == ("GET", "/pods"):
            return 200, [dict(p) for p in pods]
        if path.endswith("/stop"):
            pods[0]["desiredStatus"] = "EXITED"
            return 200, {}
        return 200, dict(pods[0])

    def account(method, url, payload=None):
        if "graphql" in url:
            return {"data": {"myself": {"clientBalance": 10.0, "currentSpendPerHr": 0.0}}}
        return [dict(p) for p in pods]
    monkeypatch.setattr(b, "call", account)

    def budget(argv):
        monkeypatch.setattr(sys, "argv", ["budget.py", *argv[2:]])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = b.main()
        return rc, buf.getvalue()
    code, host, log = launch_real_host(tmp_path, monkeypatch, api, host_cls=NoSshHost, runner=kit_runner(1.0, budget))
    checks = [json.loads(x) for x in (b.HERE / "budget-checks.jsonl").read_text().splitlines()]
    assert [c["allowed"] for c in checks] == [True, False]
    assert checks[1]["new_pod_upper_usd"] == 0.0 and checks[1]["committed_upper_usd"] > 8        # $9.50/h, about 1 h
    assert code == judge_pod.EXIT_BUDGET and pods[0]["desiredStatus"] == "EXITED"
    assert [r["allowed"] for r in log if r["step"] == "budget-guard-after-create"] == [False]


class NoCache(FakeHost):
    def _start_job(self, limit, factory):
        super()._start_job(limit, factory)
        (self.remote / CACHE_REL).unlink()                             # the job wrote no cache


class ShortCache(FakeHost):
    def _start_job(self, limit, factory):
        super()._start_job(limit, factory)
        first = (self.remote / CACHE_REL).read_bytes().split(b"\n")[0]
        (self.remote / CACHE_REL).write_bytes(first + b"\n")           # one record of the two judged


@pytest.mark.parametrize("host_cls,want,judged", [(FakeHost, 0, 2), (NoCache, 6, 0), (ShortCache, 6, 1)])
def test_f11_a_smoke_run_needs_its_records(tmp_path, monkeypatch, host_cls, want, judged):
    """--limit 2: exit 0 only when the cache was fetched and holds at least min(limit, todo) = 2 verified records;
    no cache, or one record, is exit 6."""
    code, host, log, result, out = launch_with(tmp_path, monkeypatch, host_cls=host_cls, extra=("--limit", "2"))
    (check,) = [r for r in log if r["step"] == "limit-check"]
    assert code == want and check["need"] == 2 and check["judged_new"] == judged and check["ok"] is (want == 0)
    assert (CACHE_REL in result["fetched"]) is (host_cls is not NoCache) and host.status == "EXITED"


@pytest.mark.parametrize("named,rc", [("same", 0), ("other", 2), ("none", 2)])
def test_f12_parity_needs_the_cache_its_run_record_names(tmp_path, capsys, monkeypatch, named, rc):
    """parity.py refuses (exit 2) unless --pod-cache has the SHA-256 that the run record names for its cache."""
    monkeypatch.setattr(parity, "mac_tokenizer_fingerprint", lambda: "a" * 64)
    u = parity_setup(tmp_path, n=4, samples=1)
    fill(tmp_path / "mac.jsonl", u, base_label)
    fill(tmp_path / "pod.jsonl", u, base_label)
    (tmp_path / "other.jsonl").write_bytes((tmp_path / "pod.jsonl").read_bytes() + b"\n")
    cache = {"same": tmp_path / "pod.jsonl", "other": tmp_path / "other.jsonl", "none": None}[named]
    run = write_run_record(tmp_path / "run-record.json", "a" * 64, cache=cache)
    got = parity.main(["compare", "--mac-cache", str(tmp_path / "mac.jsonl"), "--pod-cache", str(tmp_path / "pod.jsonl"),
                       "--pod-run-record", str(run), "--unit", str(u.path)])
    err = capsys.readouterr().err
    assert got == rc and (("not the run record's cache SHA-256" in err) is (rc == 2))


def _zsh_blocks(text):
    out, cur, inside = [], [], False
    for line in text.splitlines():
        if line.startswith("```zsh"):
            inside, cur = True, []
        elif line.startswith("```") and inside:
            inside = False
            out.append(cur)
        elif inside:
            cur.append(line)
    return out


PASTE_DRIVER = r"""
import os, pty, select, sys, time
zsh, home, mode, text = sys.argv[1], sys.argv[2], sys.argv[3], open(sys.argv[4]).read()
pid, fd = pty.fork()
if pid == 0:
    os.execve(zsh, ["zsh", "-f", "-i"], {"PATH": "/usr/bin:/bin", "HOME": home, "TERM": "xterm"})
out = b""


def read_until(marker, seconds):
    global out
    end = time.time() + seconds
    while time.time() < end and marker not in out:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                out += os.read(fd, 65536)
            except OSError:
                break


read_until(b"%", 10)
if mode == "bracketed":                  # a terminal's paste: one input, read by zsh before any of it runs
    os.write(fd, b"\x1b[200~" + text.encode() + b"\x1b[201~\r")
else:
    for line in text.splitlines():
        os.write(fd, line.encode() + b"\r")
        time.sleep(0.05)
time.sleep(0.5)
os.write(fd, b'print -r -- "RESULT PY=[$PY] TAG=[$TAG] n=${#UNITS}"\r')
read_until(b"RESULT PY=", 20)
read_until(b"\n", 2)
os.write(fd, b"exit\r")
read_until(b"\x00", 2)
os.kill(pid, 9)
os.waitpid(pid, 0)
lines = [ln for ln in out.decode("utf-8", "replace").splitlines() if ln.startswith("RESULT PY=")]
print(lines[-1] if lines else "NO RESULT")
"""


def test_f13_every_zsh_block_starts_with_interactivecomments_and_has_no_comment():
    """Each zsh block of README.md and PARITY.md starts with `setopt interactivecomments` (zsh's interactive default
    has comments off) and holds no comment: a terminal pastes a whole block as one input that zsh reads before the
    setopt line runs, so a comment in the same paste would still be words (a quote in one swallows later lines)."""
    for name in ("README.md", "PARITY.md"):
        blocks = _zsh_blocks((POD_DIR / name).read_text())
        assert blocks and all(b[0] == "setopt interactivecomments" for b in blocks), name
        for b in blocks:
            assert not [ln for ln in b if ln.lstrip().startswith("#") or " #" in ln], (name, b)
    readme = (POD_DIR / "README.md").read_text()
    assert "budget-checks.jsonl" in readme and "13 family-probe kits" in readme


@pytest.mark.parametrize("mode", ["bracketed", "lines"])
def test_f13_the_settings_block_pasted_into_an_interactive_zsh(tmp_path, mode):
    """The README's first block up to the dry check (assignments only; nothing is run) pasted into `zsh -f -i` on a
    real pty, as a terminal's bracketed paste and line by line: PY, TAG and the UNITS array are set."""
    zsh = shutil.which("zsh")
    if zsh is None:
        pytest.skip("no zsh on this machine")
    block = _zsh_blocks((POD_DIR / "README.md").read_text())[0]
    head = block[:next(i for i, ln in enumerate(block) if ln.startswith('"$PY"'))]
    assert all(re.match(r"^(setopt interactivecomments|export [A-Z_]+=1|[A-Z]+=\S.*)$", ln) for ln in head), head
    (tmp_path / "paste.txt").write_text("\n".join(head))
    (tmp_path / "paste_driver.py").write_text(PASTE_DRIVER)
    p = subprocess.run([sys.executable, "-B", str(tmp_path / "paste_driver.py"), zsh, str(tmp_path), mode,
                        str(tmp_path / "paste.txt")], capture_output=True, text=True, timeout=120, cwd=tmp_path)
    assert p.stdout.strip() == ("RESULT PY=[/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/"
                                "bin/python] TAG=[<new-tag>] n=4"), (p.stdout[-600:], p.stderr[-600:])


# ------------------------------------------------------------------------------------------------ the third review: G1-G4

G1_DRIVER = r"""
import json, os, pathlib, resource, signal, sys
sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
sys.path.insert(0, sys.argv[1])
import test_judge_pod as T
import judge_pod, podhost
tmp, point, signame, stop_status = pathlib.Path(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5])
judge_pod.JUDGE_POD_ROOT = tmp / "judge-pod"
podhost.JUDGE_HOSTS = tmp / "judge-hosts"
podhost.BUDGET_LOCK = tmp / "budget.lock"
podhost.SLEEP = lambda s: None
T.setup_units(tmp, T.PlainPatch())
for k, v in T.SECRET_ENV.items():
    os.environ[k] = v
pods = [{"id": "pod-old", "name": "attribution-judge-t1", "desiredStatus": "RUNNING", "costPerHr": 1.79}]
api, calls = T._pods_api(pods, stop_status=stop_status)
fired = []


def signalling(method, path, payload=None):
    # a real signal at the reconcile's first listing, or at its first orphan stop request (before RunPod gets it)
    at = "listing" if (method, path) == ("GET", "/pods") else "stop" if path.endswith("/stop") else None
    if at == point and not fired:
        fired.append(at)
        os.kill(os.getpid(), getattr(signal, "SIG" + signame))
    return api(method, path, payload)


podhost.api = signalling
kit = T.make_kit(tmp)
host = podhost.RunPodHost("t1", kit=kit, budget_kit=kit, runner=T.kit_runner())
clock = T.Clock()
a = T.args_for("launch", "t1", None, tmp / "kit/retrieved", tmp / "prepared-test")
raised = None
try:
    code = judge_pod.launch(a, host=host, clock=clock, sleep=clock.sleep, signals=True)
except BaseException as e:  # noqa: BLE001
    code, raised = None, type(e).__name__
(tmp / "driver.json").write_text(json.dumps({"code": code, "raised": raised, "fired": fired, "pods": pods,
                                             "creates": calls.count(("POST", "/pods")), "name": host.name()}))
"""


def run_g1(tmp_path, point, signame, stop_status=200):
    script = tmp_path / "g1_driver.py"
    script.write_text(G1_DRIVER)
    p = subprocess.run([sys.executable, "-B", str(script), str(HERE), str(tmp_path), point, signame, str(stop_status)],
                       capture_output=True, text=True, env=child_env(), timeout=300, cwd=tmp_path,
                       stdin=subprocess.DEVNULL)
    assert (tmp_path / "driver.json").exists(), (p.returncode, p.stderr[-2000:])
    r = json.loads((tmp_path / "driver.json").read_text())
    log = read_log(tmp_path / "judge-pod/t1")
    no_text_or_secret(p.stdout, p.stderr, (tmp_path / "judge-pod/t1/judge-pod-log.jsonl").read_bytes())
    return r, log, [x["step"] for x in log], p


@pytest.mark.parametrize("signame", ["INT", "TERM", "HUP", "QUIT"])
@pytest.mark.parametrize("point", ["stop", "listing"])
def test_g1_a_signal_during_the_reconcile_still_stops_the_orphan(tmp_path, point, signame):
    """reconcile-orphan-stop-* and reconcile-orphan-listing-*: a running pod of this name exists without pod.json, and
    a real signal arrives during the reconcile's orphan stop request or during its listing. finish() runs the reconcile
    again with every signal ignored: the orphan ends EXITED (orphans.jsonl, confirmed), the launch exits 6 without any
    create, and no STOP-NOT-CONFIRMED (none is needed)."""
    r, log, steps, p = run_g1(tmp_path, point, signame)
    assert r["raised"] is None and r["fired"] == [point] and r["creates"] == 0, r
    assert r["code"] == judge_pod.EXIT_FAILED and r["pods"][0]["desiredStatus"] == "EXITED", r
    error = "KeyboardInterrupt" if signame == "INT" else "Interrupted"
    assert [(x["phase"], x["error"]) for x in log if x["step"] == "failed"] == [("reconcile", error)]
    (retry,) = [x for x in log if x["step"] == "reconcile-retry"]
    assert retry["error"] == "HostError" and "existed without pod.json: stopped" in retry["detail"]
    assert "STOP-NOT-CONFIRMED" not in steps and steps[-1] == "end" and log[-1]["exit"] == judge_pod.EXIT_FAILED
    orphans = [json.loads(x) for x in (tmp_path / "judge-hosts/judge-t1/orphans.jsonl").read_text().splitlines()]
    assert [(o["id"], o["stop"]["confirmed"]) for o in orphans] == [("pod-old", True)]
    assert r["name"] == "attribution-judge-t1-r2" and p.stderr.count("interrupted:") == 1


def test_g1_an_orphan_whose_stop_is_never_confirmed_after_a_signal_exits_7(tmp_path):
    """A real SIGINT during the reconcile's listing, and RunPod never confirms the orphan's stop in the second
    reconcile: exit 7, and STOP-NOT-CONFIRMED names the orphan's id and real name (the name suffix did not move)."""
    r, log, steps, p = run_g1(tmp_path, "listing", "INT", stop_status=500)
    assert r["raised"] is None and r["code"] == judge_pod.EXIT_STOP_UNCONFIRMED and r["creates"] == 0, r
    assert r["pods"][0]["desiredStatus"] == "RUNNING" and r["name"] == "attribution-judge-t1"
    (line,) = [x for x in log if x["step"] == "STOP-NOT-CONFIRMED"]
    assert line["pod_ids"] == ["pod-old"] and line["name"] == "attribution-judge-t1"
    assert [x["error"] for x in log if x["step"] == "reconcile-retry"] == ["StopUnconfirmed"]
    assert "named attribution-judge-t1 may still run" in p.stderr and log[-1]["exit"] == 7


class ReconcileOnce(FakeHost):
    """reconcile() raises `first` on its first call (a signal, or the host's own HostError); later calls succeed."""

    first: BaseException = KeyboardInterrupt()

    def reconcile(self):
        self.calls.append("reconcile")
        if self.calls.count("reconcile") == 1:
            raise self.first


@pytest.mark.parametrize("first,runs", [(KeyboardInterrupt(), 2), (judge_pod.Interrupted("signal 1"), 2),
                                        (podhost.HostError("cannot list pods (0)"), 1),
                                        (podhost.StopUnconfirmed("not confirmed", ["pod-z"], ["n"]), 1)])
def test_g1_only_a_reconcile_cut_short_runs_again(tmp_path, monkeypatch, first, runs):
    """A reconcile cut short by a signal runs again in finish(); one that ended with its own HostError (including an
    unconfirmed orphan stop, already exit 7 with its warning) is not run a second time. No create in any case."""
    host_cls = type("Once", (ReconcileOnce,), {"first": first})
    code, host, log, result, _ = launch_with(tmp_path, monkeypatch, host_cls=host_cls)
    want = judge_pod.EXIT_STOP_UNCONFIRMED if isinstance(first, podhost.StopUnconfirmed) else judge_pod.EXIT_FAILED
    assert code == want and host.calls.count("reconcile") == runs and result["exit"] == want
    assert not [c for c in host.calls if isinstance(c, tuple) and c[0] in ("create", "budget_check")]
    assert [r.get("ok") for r in log if r["step"] == "reconcile-retry"] == ([True] if runs == 2 else [])
    assert [r["phase"] for r in log if r["step"] == "failed"] == ["reconcile" if runs == 2 else "guard"]
    assert len([r for r in log if r["step"] == "STOP-NOT-CONFIRMED"]) == (code == judge_pod.EXIT_STOP_UNCONFIRMED)


def test_g2_a_name_suffix_that_cannot_be_written_keeps_the_orphan_stop_confirmed(tmp_path, monkeypatch):
    """attempt.txt cannot be written (a full disk) after a confirmed orphan stop: orphan() does not raise, the write
    is counted in records_dropped, and reconcile ends with its usual HostError (not StopUnconfirmed)."""
    monkeypatch.setattr(podhost, "SLEEP", lambda s: None)
    real = pathlib.Path.write_text

    def full_disk(self, *a, **k):
        if self.name == "attempt.txt":
            raise OSError(errno.ENOSPC, "No space left on device")
        return real(self, *a, **k)
    monkeypatch.setattr(pathlib.Path, "write_text", full_disk)
    pods = [{"id": "pod-o", "name": "attribution-judge-t1", "desiredStatus": "RUNNING"}]
    api, _ = _pods_api(pods)
    monkeypatch.setattr(podhost, "api", api)
    host = podhost.RunPodHost("t1", tmp_path / "rec", kit=make_kit(tmp_path))
    assert host.orphan(list(pods), "test") is None and host.records_dropped == 1
    assert pods[0]["desiredStatus"] == "EXITED" and host.name() == "attribution-judge-t1"
    pods[0]["desiredStatus"] = "RUNNING"
    again = podhost.RunPodHost("t1", tmp_path / "rec2", kit=tmp_path / "kit")
    with pytest.raises(podhost.HostError, match="existed without pod.json: stopped") as e:
        again.reconcile()
    assert not isinstance(e.value, podhost.StopUnconfirmed) and again.records_dropped == 1


def test_g2_a_full_disk_after_a_lost_create_reply_still_stops_the_listed_pod(tmp_path, monkeypatch, capsys):
    """disk-full-lost-reply-listed: RunPod makes the pod, the reply is lost (status 0), and from then on nothing can be
    written under the launch folder or the host records (ENOSPC). finish()'s orphan check lists the pod and stops it
    (confirmed); neither orphans.jsonl nor attempt.txt can be written (records_dropped 2). Exit 4 (the create failed on
    the Mac before a pod was tracked; the listed pod was stopped), the pod EXITED, and no false STOP-NOT-CONFIRMED."""
    pods, full = [], {"on": False}
    api, calls = _pods_api(pods)

    def creating(method, path, payload=None):
        if (method, path) == ("POST", "/pods"):
            pods.append({"id": "pod-A", "name": payload["name"], "desiredStatus": "RUNNING", "costPerHr": 1.79})
            full["on"] = True                                          # the disk fills while the reply is in flight
            return 0, {"error": "TimeoutError"}
        return api(method, path, payload)
    guarded = (str(judge_pod.JUDGE_POD_ROOT), str(podhost.JUDGE_HOSTS))
    real_open = io.open

    def full_disk_open(file, mode="r", *a, **k):
        if (full["on"] and any(c in mode for c in "wax+") and isinstance(file, (str, os.PathLike))
                and str(os.fspath(file)).startswith(guarded)):
            raise OSError(errno.ENOSPC, "No space left on device")
        return real_open(file, mode, *a, **k)
    monkeypatch.setattr(builtins, "open", full_disk_open)
    monkeypatch.setattr(io, "open", full_disk_open)
    code, host, _ = launch_real_host(tmp_path, monkeypatch, creating)
    full["on"] = False
    io_ = capsys.readouterr()
    echoed = [json.loads(x) for x in io_.out.splitlines() if x.startswith("{")]
    steps = [r["step"] for r in echoed]
    assert code == judge_pod.EXIT_CREATE and pods[0]["desiredStatus"] == "EXITED" and host.records_dropped == 2
    assert [r["stopped"] for r in echoed if r["step"] == "orphan-check"] == [1]
    assert [(r["phase"], r["error"]) for r in echoed if r["step"] == "failed"] == [("create", "OSError")]
    assert "STOP-NOT-CONFIRMED" not in steps and "STOP NOT CONFIRMED" not in io_.err
    assert "orphan-check-failed" not in steps and echoed[-1]["step"] == "end" and echoed[-1]["exit"] == 4
    assert not (host.records / "attempt.txt").exists() and not (host.records / "orphans.jsonl").exists()


@pytest.mark.parametrize("exc", [subprocess.TimeoutExpired(["budget.py"], 300), FileNotFoundError(errno.ENOENT, "x"),
                                 PermissionError(errno.EACCES, "x"), UnicodeDecodeError("utf-8", b"\xff", 0, 1, "x")])
def test_g4_a_budget_py_that_hangs_or_cannot_start_is_a_refusal(tmp_path, exc):
    def runner(argv, **kw):
        raise exc
    host = podhost.RunPodHost("t1", tmp_path / "rec", kit=tmp_path, budget_kit=tmp_path, runner=runner)
    assert host.budget_check(1.0, 1.85) == (False, {"exit": None, "error": type(exc).__name__})


@pytest.mark.parametrize("when", ["after-create", "before-create"])
def test_g4_a_budget_check_that_times_out_is_a_refusal(tmp_path, monkeypatch, when):
    """post-check-times-out: the guard before the create allows it, then budget.py runs past its 300 s timeout in the
    check after the create (TimeoutExpired): a refusal, exit 3, the pod stopped (EXITED). The same timeout before the
    create: exit 3 and no create request."""
    pods, checks = [], {"n": 0}
    api, calls = _pods_api(pods)

    def creating(method, path, payload=None):
        if (method, path) == ("POST", "/pods"):
            calls.append((method, path))
            pods.append({"id": "pod-A", "name": payload["name"], "desiredStatus": "RUNNING", "costPerHr": 1.79})
            return 201, dict(pods[0])
        return api(method, path, payload)

    def budget(argv):
        checks["n"] += 1
        if checks["n"] == (2 if when == "after-create" else 1):
            raise subprocess.TimeoutExpired(argv, 300)
        return 0, '{"allowed": true, "balance": 30.0}\n'
    code, host, log = launch_real_host(tmp_path, monkeypatch, creating, host_cls=NoSshHost,
                                       runner=kit_runner(1.0, budget))
    step = "budget-guard-after-create" if when == "after-create" else "budget-guard"
    assert code == judge_pod.EXIT_BUDGET and log[-1]["step"] == "end" and log[-1]["exit"] == 3
    assert [(r["allowed"], r["guard"]) for r in log if r["step"] == step] == [
        (False, {"exit": None, "error": "TimeoutExpired"})]
    assert calls.count(("POST", "/pods")) == (1 if when == "after-create" else 0)
    assert [p["desiredStatus"] for p in pods] == (["EXITED"] if when == "after-create" else [])
    assert "STOP-NOT-CONFIRMED" not in [r["step"] for r in log]
