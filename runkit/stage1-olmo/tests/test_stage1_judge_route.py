"""Round 30 (27 Oct 2026; notes/kit-round-30.json; addendum §30 gaps 3 and 4; the lead's R1, R4 and R5): the stage-1
judge route end to end on CPU, with no network, no RunPod and no pod.

The pod is Gate B's fake pod (scripts/gate_b_mac_judges/tests/test_judge_pod.py FakeHost, imported unchanged: ssh,
scp, the API and the budget guard are fakes), except that the bundle's OWN shipped pod code verifies and runs it: the
unpack step runs the shipped bundle/tool/pod/pod_job.py verify, and the job runs the shipped pod_job.py run (a fake
judge that labels by prompt index), each in a child process whose import path is the unpacked bundle, as on the pod.
The only test-side change in that child is the synthetic prepared set added to the pinned prepared sets (Gate B's
tests add it the same way). Gate B's files are read, never written.

Sentinel counts: the B10 unit has 3,000 greedy and 3,000 sampled harm answers; the fake judge labels 1,777 greedy
"yes" and 1,099 "unparsed", 1,333 sampled "yes" and 1,555 "unparsed". Those four numbers are sealed counts: R4 says no
stage-1 command prints one, and no file but the launcher's log, its result, the cache and the judge files themselves
holds one. Prompt ids are p0001q..p3000q so that no id reads as a sentinel."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import subprocess
import sys
import tarfile

import pytest

KIT = pathlib.Path(__file__).resolve().parents[1]
REPO = KIT.parents[1]
GB = REPO / "scripts" / "gate_b_mac_judges"
for _p in (GB / "tests", GB, GB / "pod"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import bundle as bundle_mod  # noqa: E402  (Gate B's, read only)
import podhost  # noqa: E402
import synth  # noqa: E402
import test_judge_pod as T  # noqa: E402  (Gate B's fake pod and prepared-set builder)

SENT = {"greedy": {"yes": 1777, "unparsed": 1099}, "sampled": {"yes": 1333, "unparsed": 1555}}
SENT_RE = re.compile(r"(?<![0-9A-Za-z.])(1777|1099|1333|1555)(?![0-9A-Za-z.])")
N = 3000
PREPARED = "prepared-s1-route"


def sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def pid(i: int) -> str:
    return f"p{i:04d}q"


def wrapper_module():
    spec = importlib.util.spec_from_file_location("s1_route_wrapper", KIT / "judge_units_stage1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def route(tmp_path, monkeypatch):
    """The wrapper (this kit's file), a synthetic prepared set pinned for the Mac side, and every launcher folder
    (tmp/judge-pod, the judge hosts, the budget lock) under tmp_path."""
    w = wrapper_module()
    monkeypatch.setattr(podhost, "JUDGE_HOSTS", tmp_path / "judge-hosts")
    monkeypatch.setattr(podhost, "BUDGET_LOCK", tmp_path / "budget.lock")
    gb_files = {p.relative_to(GB).as_posix(): sha(p) for p in sorted(GB.rglob("*")) if p.is_file()}
    yield w
    assert {p.relative_to(GB).as_posix(): sha(p) for p in sorted(GB.rglob("*")) if p.is_file()} == gb_files   # R1


def prepared_set(tmp_path, monkeypatch, n: int) -> tuple[pathlib.Path, str]:
    prepared, manifest = T.make_prepared(tmp_path, tuple(pid(i) for i in range(1, n + 1)), name=PREPARED)
    monkeypatch.setattr(bundle_mod, "KNOWN_PREPARED", {**bundle_mod.KNOWN_PREPARED, PREPARED: manifest})
    return prepared, manifest


def b10_unit(retrieved: pathlib.Path, manifest: str, n: int, folder: str = "job-5/eval-default", **job_change):
    """A B10 evaluation unit (job.json kind stage1-eval-adapter; Safe LoRA's default point) with n greedy and n
    sampled harm answers, their guard records, and COMPLETE.json listing eval/e1/ and job.json."""
    unit = retrieved / "b-1" / "tree" / folder
    ev = unit / "eval" / "e1"
    ev.mkdir(parents=True)
    job = {"kind": "stage1-eval-adapter", "evaluate_bank": "dev", "checkpoint": "e1", "seed": 1104, "mode": "external",
           "external": {"name": "safe_lora", "adapter_sha256": "a" * 64}, "manifest_sha256": manifest, **job_change}
    (unit / "job.json").write_text(json.dumps(job, sort_keys=True))
    pids = [pid(i) for i in range(1, n + 1)]
    synth.write_jsonl(ev / "generations.jsonl", [{"kind": "harm", "prompt_id": p, "text": synth.answer("greedy", p, None)}
                                                 for p in pids] + [{"kind": "overrefusal", "prompt_id": "o-001",
                                                                    "text": f"{synth.MARK_A} over"}])
    synth.write_jsonl(ev / "samples.jsonl", [{"kind": "harm", "prompt_id": p, "sample_index": 0,
                                              "text": synth.answer("sampled", p, 0)} for p in pids])
    synth.write_jsonl(ev / "guard.jsonl", [{"kind": "harm", "prompt_id": p, "safety": "Safe", "refusal": "No"}
                                           for p in pids])
    synth.write_jsonl(ev / "guard_samples.jsonl", [{"prompt_id": p, "sample_index": 0, "safety": "Safe",
                                                    "refusal": "No"} for p in pids])
    files = {p.relative_to(unit).as_posix(): sha(p) for p in sorted(unit.rglob("*")) if p.is_file()}
    (unit / "COMPLETE.json").write_text(json.dumps({"complete": True, "completed_utc": "2026-10-26T10:00:00+00:00",
                                                    "job_sha256": files["job.json"], "files": files}, sort_keys=True))
    return unit


# the pod's job, run by the bundle's own shipped pod_job.py (module text)
DRIVER = r'''
import json, pathlib, sys
mode, root, remote, prepared, rule = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), \
    json.loads(sys.argv[4]), json.loads(sys.argv[5])
pod = root / "tool" / "pod"
sys.path[:0] = [str(pod), str(pod.parent)]
import pod_job
import bundle
bundle.KNOWN_PREPARED.update(prepared)
(remote / "pod-bundle.json").write_text(json.dumps({"module": pathlib.Path(bundle.__file__).name,
                                                    "stage1": hasattr(bundle._verify_unit, "gate_b")}))
if mode == "verify":
    sys.exit(pod_job.main(["verify", "--bundle", str(root)]))
def label(m, p):
    i = int(p[1:5]) - 1
    yes, unparsed = rule[m]["yes"], rule[m]["unparsed"]
    return "yes" if i < yes else "unparsed" if i < yes + unparsed else "no"
def factory(pairs):
    def judge(prompt, answer):
        _, m, p, _ = answer.split(" ", 3)
        return {"label": label(m, p), "input_tokens": 10, "answer_tokens": 5, "truncated": False}
    return judge
def env(device):
    return {"device": device, "gpu": "FAKE GPU", "torch": "2.8.0+cu128", "transformers": "4.56.2"}
sys.exit(pod_job.main(["run", "--bundle", str(root), "--cache", str(remote / "out" / "harmbench-pod.jsonl"),
                       "--record", str(remote / "out" / "run-record.json")], judge_factory=factory, env_probe=env))
'''


class ShippedPodHost(T.FakeHost):
    """Gate B's fake pod, except that the bundle's own shipped pod_job.py (with the bundle.py it ships) verifies and
    runs it, in a child process whose import path is the unpacked bundle."""

    def __init__(self, remote, prepared: dict, rule: dict = SENT, **kw):
        pathlib.Path(remote).mkdir(parents=True, exist_ok=True)
        super().__init__(remote, **kw)
        self.prepared, self.rule = prepared, rule

    def _shipped(self, mode: str):
        return subprocess.run([sys.executable, "-I", "-B", "-c", DRIVER, mode, str(self.remote / "bundle"),
                               str(self.remote), json.dumps(self.prepared), json.dumps(self.rule)],
                              capture_output=True, text=True, cwd=self.remote, env={"PATH": "/usr/bin:/bin"})

    def run(self, command, timeout=120, stdin_path=None):
        if "tarfile.open" in command:
            self.calls.append(("run", command.split("\n")[0][:40]))
            with tarfile.open(self.remote / "bundle.tar.gz") as t:
                t.extractall(self.remote, filter="data")
            done = self._shipped("verify")
            self.verify_err = done.stderr
            return done.returncode, done.stdout
        return super().run(command, timeout, stdin_path)

    def _start_job(self, limit, factory):
        (self.remote / "out").mkdir(parents=True, exist_ok=True)
        done = self._shipped("run")
        (self.remote / "out" / "job.log").write_text(done.stdout + done.stderr)
        (self.remote / "DONE.json").write_text(json.dumps({"exit": done.returncode, "step": "done" if
                                                           done.returncode == 0 else "run", "utc": "2026-10-27T00:00:00Z"}))


def launch(w, tmp_path, monkeypatch, tag: str, units: list, prepared, manifest: str, quiet: bool = True,
           plain: bool = False):
    """One judge launch of ``units`` on a ShippedPodHost: through the stage-1 wrapper (run_launcher), or, with
    ``plain``, Gate B's own launcher (no stage-1 enumeration). Returns (exit, host, launch folder)."""
    module = w.load_judge_pod()
    monkeypatch.setattr(module, "JUDGE_POD_ROOT", tmp_path / "judge-pod")
    host = ShippedPodHost(tmp_path / f"remote-{tag}", {PREPARED: manifest})
    clock = T.Clock()
    argv = ["launch", "--tag", tag, *[x for u in units for x in ("--unit", str(u))], "--prepared", str(prepared),
            "--expect-greedy", "0", "--expect-sampled", "0"]
    kw = {"host": host, "clock": clock, "sleep": clock.sleep, "signals": False}
    code = module.launch(module.parser().parse_args(argv[0:]), **kw) if plain else \
        w.run_launcher(module, argv, quiet=quiet, **kw)
    return code, host, tmp_path / "judge-pod" / tag


def steps(folder: pathlib.Path) -> list[str]:
    return [json.loads(x)["step"] for x in (folder / "judge-pod-log.jsonl").read_text().splitlines() if x.strip()]


def scan(root: pathlib.Path, allowed) -> list[str]:
    """Every file under root (outside the allowed names) whose bytes hold a sentinel count."""
    hits = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(p.match(a) for a in allowed) and SENT_RE.search(p.read_bytes().decode("utf-8", "replace")):
            hits.append(str(p.relative_to(root)))
    return hits


def test_a_b10_unit_is_launched_verified_on_the_pod_and_filed_and_no_sealed_count_is_printed(route, tmp_path, monkeypatch,
                                                                                            capsys):
    """R5 and R4, the wrapper's first launch test: one B10 unit through `launch` (fake pod, no network). The bundle
    ships the stage-1 bundle.py beside Gate B's bundle.py (byte for byte); the bundle's own pod_job.py verify accepts
    the B10 unit with it (exit 0, every step to the stop); the fetched cache is complete; `write-files` writes its
    HarmBench file under its arm label; `result` gives the whitelist and the record entry. No sentinel count reaches
    stdout or stderr, nor any file but the launcher's log, its result, the cache and the judge file; the log and the
    result do hold them (the generator works). The echo-on contrast is the next test."""
    w = route
    prepared, manifest = prepared_set(tmp_path, monkeypatch, N)
    unit = b10_unit(tmp_path / "kit" / "retrieved", manifest, N)
    code, host, out = launch(w, tmp_path, monkeypatch, "s1b-hb-1", [unit], prepared, manifest)
    io_ = capsys.readouterr()
    assert code == 0, (host.verify_err[-500:], steps(out))
    assert [s for s in steps(out) if s in ("bundle-verified-on-pod", "verified", "stop", "end")] == \
        ["bundle-verified-on-pod", "verified", "stop", "end"]
    assert json.loads((host.remote / "pod-bundle.json").read_text()) == {"module": "bundle_gateb.py", "stage1": True}
    shipped = host.remote / "bundle" / "tool" / "pod"
    assert sha(shipped / "bundle_gateb.py") == sha(GB / "pod" / "bundle.py")
    assert sha(shipped / "bundle.py") == sha(KIT / "judge_pod_stage1" / "bundle.py")
    record = json.loads((out / "bundle-record.json").read_text())
    assert record["scripts"]["tool/pod/bundle.py"] == sha(KIT / "judge_pod_stage1" / "bundle.py") and \
        record["scripts"]["tool/pod/bundle_gateb.py"] == sha(GB / "pod" / "bundle.py")
    result = json.loads((out / "judge-pod-result.json").read_text())
    assert result["exit"] == 0 and result["verification"]["complete"] is True and result["verification"]["judged"] == 2 * N
    assert result["verification"]["units"][0]["greedy"]["yes"] == SENT["greedy"]["yes"]          # the sealed values
    assert not SENT_RE.search(io_.out + io_.err), "a sealed count reached stdout or stderr"
    judges = tmp_path / "judges-pending" / "B"
    assert w.main(["write-files", "--judge", "harmbench", "--cache", str(out / "fetched/out/harmbench-pod.jsonl"),
                   "--out", str(judges), "--unit", str(unit)]) == 0
    printed = capsys.readouterr()
    lines = [json.loads(x) for x in printed.out.splitlines()]
    name = f"harmbench--b-1--eval-default--{sha(unit / 'COMPLETE.json')[:12]}.json"
    assert lines[0] == {"file": name, "unit": "b-1/job-5/eval-default", "status": "written",
                        "greedy": {"missing": 0, "stale": 0, "extra": 0}, "sampled": {"missing": 0, "stale": 0, "extra": 0}}
    assert set(lines[1]) == {"index", "files", "index_sha256"} and lines[1]["files"] == 1
    doc = json.loads((judges / name).read_text())
    assert doc["arm"] == "ref-external-safe_lora-default" and doc["greedy"]["harm"] == SENT["greedy"]["yes"]
    assert not SENT_RE.search(printed.out + printed.err)
    assert w.main(["result", "s1b-hb-1", "--root", str(tmp_path / "judge-pod"), "--hosts", str(tmp_path / "jh")]) == 0
    printed = capsys.readouterr()
    shown = json.loads(printed.out)
    assert shown["record_entry"] == {"tag": "s1b-hb-1", "result_sha256": sha(out / "judge-pod-result.json"),
                                     "run_record_sha256": result["fetched"]["out/run-record.json"],
                                     "bundle_sha256": result["bundle_sha256"], "exit": 0, "judged": 2 * N,
                                     "complete": True}
    assert shown["units"] == 1 and shown["stop_confirmed"] is True and shown["gpu"] == "FAKE GPU"
    assert not SENT_RE.search(printed.out + printed.err)
    allowed = ("judge-pod-log.jsonl", "judge-pod-result.json", "harmbench-pod.jsonl", "harmbench--*.json")
    assert scan(tmp_path, allowed) == []
    assert set(scan(tmp_path, ())) >= {"judge-pod/s1b-hb-1/judge-pod-log.jsonl", "judge-pod/s1b-hb-1/judge-pod-result.json",
                                       f"judges-pending/B/{name}"}               # the scan finds them where they are


def test_with_the_echo_on_the_same_launch_prints_the_sealed_counts(route, tmp_path, monkeypatch, capsys):
    """R4 the other way: the same launch with the launcher's own echo (Gate B's RunLog, quiet=False) prints the
    'verified' line, so the sentinel counts reach stdout; the wrapper's RunLog is restored after a launch."""
    w = route
    prepared, manifest = prepared_set(tmp_path, monkeypatch, N)
    unit = b10_unit(tmp_path / "kit" / "retrieved", manifest, N)
    code, _, _ = launch(w, tmp_path, monkeypatch, "s1b-hb-2", [unit], prepared, manifest, quiet=False)
    assert code == 0 and SENT_RE.search(capsys.readouterr().out)
    module = w.load_judge_pod()
    gate_b_log = module.RunLog
    with w.stage1_launcher(module):
        module.RunLog(tmp_path / "x.jsonl", "t")("verified", units=[{"greedy": {"yes": 1777}}])
        assert module.RunLog is not gate_b_log
    assert module.RunLog is gate_b_log and "1777" in (tmp_path / "x.jsonl").read_text()
    assert capsys.readouterr().out == ""
    gate_b_log(tmp_path / "y.jsonl", "t")("verified", units=[{"greedy": {"yes": 1777}}])
    assert "1777" in capsys.readouterr().out


def test_without_the_stage1_bundle_py_the_pod_refuses_the_b10_unit_after_the_create(route, tmp_path, monkeypatch):
    """R5 the other way (gap 4 as it was): Gate B's plain launcher refuses the B10 unit on the Mac (exit 2, no pod);
    through the wrapper but shipping Gate B's own bundle.py as tool/pod/bundle.py, the shipped pod_job.py verify
    refuses it on the pod after the create: exit 6, the pod stopped."""
    w = route
    prepared, manifest = prepared_set(tmp_path, monkeypatch, 3)
    unit = b10_unit(tmp_path / "kit" / "retrieved", manifest, 3)
    code, host, out = launch(w, tmp_path, monkeypatch, "s1b-plain", [unit], prepared, manifest, plain=True)
    assert code == 2 and "create" not in str(host.calls)
    assert "not judgeable" in json.loads((out / "judge-pod-log.jsonl").read_text().splitlines()[-1])["reason"]
    monkeypatch.setattr(w, "POD_BUNDLE", GB / "pod" / "bundle.py")
    code, host, out = launch(w, tmp_path, monkeypatch, "s1b-gateb-pod", [unit], prepared, manifest)
    assert code == 6 and ("create", 1.0) in host.calls and host.calls.count("stop") == 1
    assert "bundle-verified-on-pod" not in steps(out) and "job.json differs from the unit's record" in host.verify_err
    assert json.loads((host.remote / "pod-bundle.json").read_text()) == {"module": "bundle.py", "stage1": False}


def test_a_run_one_launch_through_the_wrapper_is_gate_bs_bundle_byte_for_byte(route, tmp_path, monkeypatch, capsys):
    """R1 and R5: without a B10 unit the stage-1 wrapper's bundle (the dry `bundle` command) has the SHA-256 of Gate
    B's own launcher's bundle for the same tag and units, and ships no bundle_gateb.py; with a B10 unit it differs
    only by the two pod files."""
    w = route
    prepared, manifest = prepared_set(tmp_path, monkeypatch, 3)
    retrieved = tmp_path / "kit" / "retrieved"
    engine = synth.make_unit(retrieved, "a-3", "1102-a0-e1-a1", seed=1102, manifest=manifest,
                             pids=tuple(pid(i) for i in range(1, 4)), samples=1)
    common = ["--tag", "s1-dry", "--unit", str(engine), "--prepared", str(prepared), "--expect-greedy", "0",
              "--expect-sampled", "0"]
    module = w.load_judge_pod()
    assert w.run_launcher(module, ["bundle", *common, "--out", str(tmp_path / "s1")]) == 0
    assert w.load_judge_pod().main(["bundle", *common, "--out", str(tmp_path / "gb")]) == 0
    capsys.readouterr()
    assert sha(tmp_path / "s1" / "bundle.tar.gz") == sha(tmp_path / "gb" / "bundle.tar.gz")
    with tarfile.open(tmp_path / "s1" / "bundle.tar.gz") as t:
        assert "bundle/tool/pod/bundle_gateb.py" not in t.getnames()
    unit = b10_unit(retrieved, manifest, 3)
    assert w.run_launcher(module, ["bundle", *common, "--unit", str(unit), "--out", str(tmp_path / "s2")]) == 0
    capsys.readouterr()
    with tarfile.open(tmp_path / "s2" / "bundle.tar.gz") as t:
        names = set(t.getnames())
        pod_bundle = t.extractfile("bundle/tool/pod/bundle.py").read()
    assert "bundle/tool/pod/bundle_gateb.py" in names and pod_bundle == (KIT / "judge_pod_stage1/bundle.py").read_bytes()


def test_the_pod_side_check_of_a_b10_entry_both_ways(route, tmp_path, monkeypatch, capsys):
    """R5 on the pod side, by function: Gate B's _verify_unit refuses the B10 entry (gap 4); the stage-1 verify_unit
    accepts it, refuses it with another arm label, checkpoint, seed or manifest, a COMPLETE.json not saying complete
    or an eval file other than COMPLETE.json lists, and hands a run-one entry to Gate B's check unchanged."""
    w = route
    prepared, manifest = prepared_set(tmp_path, monkeypatch, 3)
    retrieved = tmp_path / "kit" / "retrieved"
    unit = b10_unit(retrieved, manifest, 3)
    engine = synth.make_unit(retrieved, "a-3", "1102-a0-e1-a1", seed=1102, manifest=manifest,
                             pids=tuple(pid(i) for i in range(1, 4)), samples=1)
    module = w.load_judge_pod()
    assert w.run_launcher(module, ["bundle", "--tag", "s1-pod", "--unit", str(unit), "--unit", str(engine), "--prepared",
                                   str(prepared), "--expect-greedy", "0", "--expect-sampled", "0",
                                   "--out", str(tmp_path / "b")]) == 0
    capsys.readouterr()
    root = T.extract(tmp_path / "b" / "bundle.tar.gz", tmp_path / "pod")
    manifest_doc = json.loads((root / "job-manifest.json").read_text())
    listed = manifest_doc["files"]
    entries = {e["arm"]: e for e in manifest_doc["groups"][0]["units"]}
    b10 = entries["ref-external-safe_lora-default"]
    spec = importlib.util.spec_from_file_location("s1_pod_bundle_test", KIT / "judge_pod_stage1" / "bundle.py")
    pod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pod)
    seen = []
    gb = type("GB", (), {"_verify_unit": staticmethod(lambda *a: seen.append(a[1]["arm"])), "Refusal": bundle_mod.Refusal,
                         "_json": staticmethod(bundle_mod._json), "EVAL_FILES": bundle_mod.EVAL_FILES})
    verify = pod.make_verify_unit(gb)
    with pytest.raises(bundle_mod.Refusal, match="job.json differs from the unit's record"):
        bundle_mod._verify_unit(root, b10, listed, manifest)                       # Gate B's check: the gap
    verify(root, b10, listed, manifest)
    verify(root, entries["a0"], listed, manifest)
    assert seen == ["a0"]                                                          # run-one: Gate B's check
    for change, match in (({"arm": "ref-external-safe_lora-certify"}, "arm label"), ({"target": "init"}, "checkpoint"),
                          ({"seed": 1105}, "seed"), ({"manifest_sha256": "f" * 64}, "manifest"),
                          ({"complete_sha256": "0" * 64}, "COMPLETE.json does not have the unit's SHA-256")):
        with pytest.raises(bundle_mod.Refusal, match=match):
            verify(root, {**b10, **change}, listed, manifest)
    with pytest.raises(bundle_mod.Refusal, match="differs from the unit's record"):
        verify(root, b10, listed, "e" * 64)
    bad_files = dict(b10["files"], samples=b10["files"]["guard"])
    with pytest.raises(bundle_mod.Refusal, match="unexpected file entry|is not the file COMPLETE.json lists"):
        verify(root, {**b10, "files": bad_files}, listed, manifest)
    complete = root / b10["dir"] / "COMPLETE.json"
    doc = json.loads(complete.read_text())
    doc["complete"] = False
    complete.write_text(json.dumps(doc))
    with pytest.raises(bundle_mod.Refusal, match="is not complete"):
        verify(root, b10, {**listed, f"{b10['dir']}/COMPLETE.json": b10["complete_sha256"]}, manifest)


def test_write_files_prints_only_file_unit_status_and_gap_counts(route, tmp_path, monkeypatch, capsys):
    """R4 write-files both ways: with an empty cache the unit is refused (exit 1) and its line keeps the missing counts
    (here 3 each) and no harm, yes or unparsed count; a bad --complete refuses before anything (exit 2); the emit
    filter drops every count but missing, stale and extra, and every key but file, unit and status."""
    w = route
    prepared, manifest = prepared_set(tmp_path, monkeypatch, 3)
    unit = b10_unit(tmp_path / "kit" / "retrieved", manifest, 3)
    cache = tmp_path / "empty.jsonl"
    cache.write_text("")
    assert w.main(["write-files", "--judge", "harmbench", "--cache", str(cache), "--out", str(tmp_path / "o"),
                   "--unit", str(unit)]) == 1
    lines = [json.loads(x) for x in capsys.readouterr().out.splitlines()]
    assert lines[0]["status"].startswith("refused") and lines[0]["greedy"] == {"missing": 3, "stale": 0, "extra": 0}
    assert set(lines[0]) == {"file", "unit", "status", "greedy", "sampled"} and lines[1]["files"] == 0
    assert w.main(["write-files", "--judge", "harmbench", "--cache", str(cache), "--out", str(tmp_path / "o"),
                   "--unit", str(unit), "--complete", "XYZ"]) == 2
    assert "expected 64 lowercase hex" in capsys.readouterr().err
    line = json.dumps({"file": "f", "unit": "u", "arm": "A1", "seed": 1102, "target": "e1", "status": "written",
                       "greedy": {"n": 200, "harm": 1777, "unparsed": 1099, "missing": 0, "stale": 0, "extra": 0},
                       "sampled": None})
    assert json.loads(w.safe_emit_line(line)) == {"file": "f", "unit": "u", "status": "written",
                                                  "greedy": {"missing": 0, "stale": 0, "extra": 0}}
    assert json.loads(w.safe_emit_line(json.dumps({"index": "i", "files": 2, "index_sha256": "a" * 64, "harm": 1777}))) \
        == {"index": "i", "files": 2, "index_sha256": "a" * 64}
    assert "1777" not in w.safe_emit_line(json.dumps({"yes": 1777})) + w.safe_emit_line("not json 1777")


def test_result_prints_the_whitelist_pod_minutes_cost_and_the_record_entry_only(route, tmp_path, capsys):
    """R4 result by hand: a Granite result holding sentinel counts in its units and its gate block; result prints the
    step-5 fields, 31.0 pod minutes (08:00 to 08:31 UTC) at $1.79/h = $0.92, the gate's pass and the record entry
    (result_sha256 = the file's), and no count; a tag without a result refuses (exit 2)."""
    w = route
    root, hosts = tmp_path / "jp", tmp_path / "jh"
    body = {"kind": "judge-pod result", "version": 2, "tag": "s1a-granite-1", "judge": "granite", "exit": 0,
            "bundle_sha256": "b" * 64, "cap_hours": 2.0, "fetched": {"out/run-record.json": "c" * 64},
            "stop": {"confirmed": True, "desiredStatus": "EXITED", "utc": "2026-10-27T08:31:00+00:00"},
            "verification": {"run_record_ok": True, "pod_exit": 0, "gpu": "NVIDIA A100-SXM4-80GB", "complete": True,
                             "judged": 5400, "records": 5400, "refused": None, "tokenizer_fingerprint": "5354502d" * 8,
                             "units": [{"unit": "u", "greedy": {"n": 200, "yes": 1777, "unparsed": 1099}}] * 27,
                             "known_answers": {"passed": True, "pod_yes": 1333, "mac_yes": 1555}}}
    (root / "s1a-granite-1").mkdir(parents=True)
    (root / "s1a-granite-1" / "judge-pod-result.json").write_text(json.dumps(body))
    (hosts / "judge-s1a-granite-1").mkdir(parents=True)
    (hosts / "judge-s1a-granite-1" / "pod.json").write_text(json.dumps({"created_utc": "2026-10-27T08:00:00+00:00",
                                                                        "costPerHr": 1.79}))
    assert w.main(["result", "s1a-granite-1", "--root", str(root), "--hosts", str(hosts)]) == 0
    printed = capsys.readouterr().out
    shown = json.loads(printed)
    assert not SENT_RE.search(printed)
    assert (shown["pod_minutes"], shown["cost_usd"], shown["units"], shown["known_answer_passed"]) == (31.0, 0.92, 27, True)
    assert shown["record_entry"] == {"tag": "s1a-granite-1", "exit": 0, "judged": 5400, "complete": True,
                                     "result_sha256": sha(root / "s1a-granite-1" / "judge-pod-result.json"),
                                     "run_record_sha256": "c" * 64, "bundle_sha256": "b" * 64,
                                     "known_answer_passed": True}
    assert w.main(["result", "s1a-hb-9", "--root", str(root), "--hosts", str(hosts)]) == 2
    assert "no judge-pod-result.json yet" in capsys.readouterr().err
