"""Tests of pod/granite_summary.py: pod Granite labels to the probe kits' second-judge summary format.

Written 9 October 2026 (18:40 UTC, clock checked) by an Opus builder for General Implementation V. Fakes only: no
RunPod, no Hub, no network, no model, no GPU, no tokenizer, no real bank. A pod run is made by the real launcher
(judge_pod.launch --judge granite) with test_granite_pod's fake host, which runs the real pod_job.py with the real
granite_pod.GraniteSession and a fake tokenizer and llama (as test_granite_pod.granite_launch does). PodLikeHost adds
to the run record what a real pod run writes and the fake job leaves out (the measured GGUF SHA-256, the llama.cpp
build with GPU offload, the tokenizer fingerprint, the environment). The tokenizer pin and the parity-report pin are
replaced by the fakes' values. One golden run per module is copied into each test's folder. A test that changes a
file of the run and must pass the earlier checks makes the hash chain agree again (rebind: as an honest but wrong pod
run would), so only the check under test can find the change.

The consumers (family_probe_reading.judge_identity, killtest_stage0_reading.granite_rate,
merge_judge_summaries.merge, gate_a_common.merged_judge) are loaded by file path and called on the converter's
outputs; a test that needs a file under tmp/ is skipped when the file is not on this machine. The last test converts
the real granite-parity-2 run when its files are on this machine (counts and hashes only).

Revised 9 October 2026 (19:22 to 19:41 UTC, clock checked), refix round 1. The fake runs also pin the converter's
local prepared set (PREPARED_ROOT, KNOWN_PREPARED: the fake set of the run) and the parity settings SHA-256
(PARITY_SETTINGS_SHA256: the fake run's value, computed here by settings_of, not by the converter). New cases: the
settings, the one-way resume rule, the local dev bank and the prompt SHA-256, and the reviewers' round-1 cases
(section "the review's cases").

Revised 9 October 2026 (20:53 UTC onward, clock checked), refix round 2. The fake runs also pin the parity packages
SHA-256 (PARITY_PACKAGES_SHA256: the fake run's value, computed here by packages_of). New cases (section "round 2"):
the packages pin, --out in another letter case, through the data-volume firmlink, through a missing folder and "..",
through a link, in another run's fetched/ folder; and the round-2 reviewers' cases (skeptic-*-r2.json).

Acceptance (tests-r1-12): run this file with -rs. On this machine the run must report 0 skipped. A skip means that a
consumer or a real-data file was absent or refused to load (load_path turns gate_a_common's pinned-hash SystemExit into
a skip), so the consumer check did not run.
"""
from __future__ import annotations

import ast
import contextlib
import fractions
import importlib.util
import io
import json
import pathlib
import shutil
import sys
import tarfile

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
import common  # noqa: E402
import granite_pod  # noqa: E402
import granite_summary as GS  # noqa: E402
import judge_pod  # noqa: E402
import judging  # noqa: E402
import pod_judge  # noqa: E402
import podhost  # noqa: E402
import test_granite_pod as G  # noqa: E402
import test_judge_pod as T  # noqa: E402
import units as units_mod  # noqa: E402
from cache import Cache  # noqa: E402
from common import GRANITE, ROOT, Refusal  # noqa: E402

MAC_JUDGE = "granite-guardian-3.3-8b Q4_K_M (llama.cpp, Metal), criteria harm, think False"   # the kits' string
FAKE_FP = pod_judge.tokenizer_fingerprint(G.FakeGraniteTok())
REAL_FP = granite_pod.MAC_TOKENIZER_FINGERPRINT                    # read at import, before any fixture replaces it
REAL_PARITY = (GS.PARITY_REPORT, GS.PARITY_REPORT_SHA256)
REAL_SETTINGS = GS.PARITY_SETTINGS_SHA256                          # read at import, before any fixture replaces it
REAL_PACKAGES = GS.PARITY_PACKAGES_SHA256                          # read at import, before any fixture replaces it
REAL_PREPARED = (GS.PREPARED_ROOT, dict(bundle_mod.KNOWN_PREPARED))
RESULT, RECORD, CACHE, INPUTS, DONE = (GS.RESULT_NAME, GS.RECORD_REL, GS.CACHE_REL, GS.INPUTS_REL, GS.DONE_REL)
PIDS = tuple(f"p-{i:03d}" for i in range(1, 7))
# the fake llama's labels (every unit alike): p-001 and p-004 "yes", p-002 "unparsed", the others "no"
LABELS = {("greedy", "p-001", None): "yes", ("greedy", "p-002", None): "unparsed", ("greedy", "p-004", None): "yes"}
# (host, unit folder, target, seed, {prompt id: Qwen3Guard safety}); the others' guard rows say "Safe". A
# "Controversial" row is not "Unsafe" (second_judge_probe counts safety == "Unsafe" only).
UNITS = (("hostA", "1101-a0-init-a1", "init", 1101, {"p-001": "Unsafe"}),
         ("hostA", "1101-a0-e1-a1", "e1", 1101, {"p-001": "Unsafe", "p-003": "Unsafe", "p-004": "Unsafe"}),
         ("hostB", "1102-a0-e1-a1", "e1", 1102, {"p-002": "Unsafe", "p-006": "Controversial"}))
# hand-computed (granite yes = p-001, p-004; unparsed p-002 counts as not harm)
WANT = {"1101-a0-init-a1": {"target": "init", "n": 6, "granite_harm": 2, "qwen3guard_unsafe": 1, "agree": 5,
                            "unparsed": 1, "trimmed": 0},
        "1101-a0-e1-a1": {"target": "e1", "n": 6, "granite_harm": 2, "qwen3guard_unsafe": 3, "agree": 5,
                          "unparsed": 1, "trimmed": 0},
        "1102-a0-e1-a1": {"target": "e1", "n": 6, "granite_harm": 2, "qwen3guard_unsafe": 1, "agree": 3,
                          "unparsed": 1, "trimmed": 0}}
# pairs 18, agree 13, p1 = 6/18, p2 = 5/18: pe = 31/54, kappa = (39/54 - 31/54) / (23/54) = 8/23
WANT_OVERALL = {"pairs": 18, "agreement": 0.722, "cohen_kappa": 0.348}
BUILD = {"kind": "judge-pod llama build", "cmake_args": granite_pod.LLAMA_CMAKE_ARGS,
         "sdist_sha256": granite_pod.LLAMA_SDIST_SHA256, "cuda": "12.8, V12.8.93", "gpu_offload": True,
         "llama_cpp_python": granite_pod.LLAMA_VERSION, "build_log_sha256": "f" * 64}
# environment.packages as a real pod run writes it: the pinned versions and the absent distributions as null
ENV = {"device": "cuda", "gpu": "FAKE A100", "driver": "0.0.0", "python": "3.12.3",
       "packages": {"transformers": "5.18.0", "torch": None, "sentencepiece": None, "protobuf": None}}


# ------------------------------------------------------------------------------------------------ the fake pod run

class PodLikeHost(G.GraniteHost):
    """test_granite_pod.GraniteHost whose run record also holds what pod_job.py writes on a real pod and leaves out
    with a test judge factory: files.gguf_sha256, the llama block with its build record, the tokenizer fingerprint,
    the packages and a fuller environment. It edits the record before the launch sums and fetches it."""
    LABELS = LABELS

    def _start_job(self, limit, factory):
        super()._start_job(limit, factory)
        path = self.remote / RECORD
        doc = json.loads(path.read_bytes())
        doc["files"] = {"gguf_sha256": common.GRANITE_GGUF_SHA256, "tokenizer_files": {}}
        doc["llama"] = {"llama_cpp_python": granite_pod.LLAMA_VERSION, "module_version": granite_pod.LLAMA_VERSION,
                        "gpu_offload": True, "build": dict(BUILD)}
        doc["tokenizer_fingerprint"] = FAKE_FP
        doc["packages"] = {"transformers": "5.18.0"}
        doc["environment"] = dict(ENV)
        path.write_bytes(common.canonical_bytes(doc))


def fake_pod_env(base: pathlib.Path, mp) -> None:
    """test_granite_pod._granite_fakes for any scope: launches write under base; the Mac Granite tokenizer folder, its
    pins and the known-answer gate are synthetic; the launcher's keys are fakes."""
    mp.setattr(judge_pod, "JUDGE_POD_ROOT", base / "judge-pod")
    mp.setattr(podhost, "JUDGE_HOSTS", base / "judge-hosts")
    mp.setattr(podhost, "BUDGET_LOCK", base / "budget.lock")
    tok = base / "mac-granite-tokenizer"
    tok.mkdir()
    pins = {}
    for name in ("tokenizer.json", "tokenizer_config.json", "chat_template.jinja"):
        body = json.dumps({"synthetic": name}).encode()
        (tok / name).write_bytes(body)
        pins[name] = (len(body), sha(body))
    mp.setattr(granite_pod, "MAC_TOKENIZER", tok)
    mp.setattr(granite_pod, "TOK_FILES", pins)
    G.make_known_answers(base, mp)
    for k, v in T.SECRET_ENV.items():
        mp.setenv(k, v)


def settings_of(record: dict) -> str:
    """The parity settings SHA-256 of a run record, computed here from its four parts (not with the converter's
    function): a change of the converter's formula then refuses the fake runs and fails the real-data test."""
    llama = record["llama"]
    return sha(common.canonical_bytes({"pins": record["pins"], "llama_cpp_python": llama["llama_cpp_python"],
                                       "cmake_args": llama["build"]["cmake_args"],
                                       "sdist_sha256": llama["build"]["sdist_sha256"]}))


def packages_of(record: dict) -> str:
    """The parity packages SHA-256 of a run record, computed here (not with the converter's function): the SHA-256 of
    common.canonical_bytes of its environment.packages."""
    return sha(common.canonical_bytes(record["environment"]["packages"]))


def launch(base: pathlib.Path, mp, units=UNITS, tag="t1", extra=(), host_kw=None, mutate=None):
    """One Granite launch over synthetic units (judge_pod.launch with PodLikeHost). mutate(name, unit folder): called
    before the unit is sealed again (a change made before the launch). Returns (exit, pod folder, {name: folder}).
    The converter then reads base/prepared-test as its local prepared set, and a run that exits 0 gives the pinned
    parity settings and packages."""
    prepared = base / "prepared-test"
    if not prepared.is_dir():                              # a second launch (a resume) keeps the first one's set
        T.make_prepared(base, PIDS)
    manifest = sha((prepared / "manifest.json").read_bytes())
    mp.setattr(bundle_mod, "KNOWN_PREPARED", {prepared.name: manifest})
    mp.setattr(GS, "PREPARED_ROOT", base)
    retrieved = base / "kit" / "retrieved"
    dirs = {}
    for host, name, target, seed, safety in units:
        unit = retrieved / host / "tree" / "round1" / name
        if not unit.is_dir():
            unit = synth.make_unit(retrieved, host, name, target=target, seed=seed, manifest=manifest, pids=PIDS,
                                   samples=1, guard_safety=dict(safety), tag=f"{host}-{name}")
            if mutate is not None:
                mutate(name, unit)
                synth.seal(unit, target=target, arm="a0", seed=seed, completed_utc="2026-10-08T01:00:00+00:00")
        dirs[name if name not in dirs else f"{host}/{name}"] = unit
    host = PodLikeHost(base / f"remote-{tag}", **(host_kw or {}))
    clock = T.Clock()
    code = judge_pod.launch(T.args_for("launch", tag, None, retrieved, prepared, *G.GRANITE_ARGS, *extra), host=host,
                            clock=clock, sleep=clock.sleep, signals=False)
    if code == 0:
        record = jload(judge_pod.JUDGE_POD_ROOT / tag / GS.FETCHED / RECORD)
        mp.setattr(GS, "PARITY_SETTINGS_SHA256", settings_of(record))
        mp.setattr(GS, "PARITY_PACKAGES_SHA256", packages_of(record))
    return code, judge_pod.JUDGE_POD_ROOT / tag, dirs


@pytest.fixture(scope="module")
def golden(tmp_path_factory):
    """One complete pod run of the three units (known-answer gate on), built once per module."""
    base = tmp_path_factory.mktemp("golden")
    with pytest.MonkeyPatch.context() as mp, contextlib.redirect_stdout(io.StringIO()):
        fake_pod_env(base, mp)
        code, pod, dirs = launch(base, mp)
    assert code == 0
    return base


@pytest.fixture
def run(golden, tmp_path, monkeypatch):
    """A private copy of the golden run, its kit and its prepared set: (pod folder, {unit name: unit folder}). The
    converter reads the copy's prepared set (PREPARED_ROOT, KNOWN_PREPARED), and the golden run's settings and packages
    are the pinned parity settings and packages (PARITY_SETTINGS_SHA256, PARITY_PACKAGES_SHA256)."""
    for name in ("judge-pod", "kit", "prepared-test"):
        shutil.copytree(golden / name, tmp_path / name)
    prepared = tmp_path / "prepared-test"
    monkeypatch.setattr(GS, "PREPARED_ROOT", tmp_path)
    monkeypatch.setattr(bundle_mod, "KNOWN_PREPARED", {prepared.name: sha((prepared / "manifest.json").read_bytes())})
    pod = tmp_path / "judge-pod" / "t1"
    monkeypatch.setattr(GS, "PARITY_SETTINGS_SHA256", settings_of(jload(pod / GS.FETCHED / RECORD)))
    monkeypatch.setattr(GS, "PARITY_PACKAGES_SHA256", packages_of(jload(pod / GS.FETCHED / RECORD)))
    retrieved = tmp_path / "kit" / "retrieved"
    dirs = {name: retrieved / host / "tree" / "round1" / name for host, name, *_ in UNITS}
    return pod, dirs


@pytest.fixture(autouse=True)
def _pins(tmp_path, monkeypatch):
    """The Mac tokenizer fingerprint pin is the fake tokenizer's; the parity-report pin is a synthetic PASS report."""
    monkeypatch.setattr(granite_pod, "MAC_TOKENIZER_FINGERPRINT", FAKE_FP)
    report = tmp_path / "granite-parity-report.json"
    report.write_text(json.dumps({"kind": GS.PARITY_REPORT_KIND, "verdict": "PASS"}))
    monkeypatch.setattr(GS, "PARITY_REPORT", report)
    monkeypatch.setattr(GS, "PARITY_REPORT_SHA256", sha(report.read_bytes()))


# ------------------------------------------------------------------------------------------------ helpers

def jload(path):
    return json.loads(pathlib.Path(path).read_bytes())


def jsave(path, doc):
    pathlib.Path(path).write_text(json.dumps(doc))


def lines_of(path):
    return [json.loads(x) for x in pathlib.Path(path).read_bytes().split(b"\n") if x.strip()]


def save_lines(path, rows):
    pathlib.Path(path).write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in rows))


def edit_lines(path, fn):
    rows = lines_of(path)
    fn(rows)
    save_lines(path, rows)


def edit_json(path, fn):
    doc = jload(path)
    fn(doc)
    jsave(path, doc)


def refetch(pod):
    """The result names every fetched file's present SHA-256 (as if the launch had fetched these bytes)."""
    f = pod / GS.FETCHED
    edit_json(pod / RESULT, lambda r: r["fetched"].update({rel: sha((f / rel).read_bytes()) for rel in GS.FETCHED_RELS}))


def _count(path, reader):
    try:
        return reader(path)
    except Refusal:
        return len([x for x in pathlib.Path(path).read_bytes().split(b"\n") if x.strip()])


def rebind(pod, record_edit=None):
    """After a change of the fetched cache, inputs file or run record: the run record names the cache's and the
    inputs file's present SHA-256 and counts, and the result names every fetched file's present SHA-256."""
    f = pod / GS.FETCHED
    doc = jload(f / RECORD)
    if record_edit is not None:
        record_edit(doc)
    doc["cache"] = {"sha256": sha((f / CACHE).read_bytes()),
                    "records": _count(f / CACHE, lambda p: len(Cache(p, GRANITE)))}
    doc["inputs"] = {"sha256": sha((f / INPUTS).read_bytes()),
                     "records": _count(f / INPUTS, lambda p: len(granite_pod.read_inputs(p)[0]))}
    jsave(f / RECORD, doc)
    refetch(pod)


def complete_of(unit_dir) -> str:
    return sha((pathlib.Path(unit_dir) / "COMPLETE.json").read_bytes())


def rewrite_manifest(pod, edit):
    """A new bundle whose job manifest has an edit; the result and the run record name the new bundle and manifest."""
    stage = pod.parent / "restage"
    with tarfile.open(pod / GS.BUNDLE_NAME) as t:
        t.extractall(stage, filter="data")
    path = stage / "bundle" / bundle_mod.MANIFEST_NAME
    doc = jload(path)
    edit(doc)
    path.write_bytes(common.canonical_bytes(doc))
    new = pod.parent / "new-bundle.tar.gz"
    digest = bundle_mod.write_tar(stage / "bundle", new)
    shutil.move(str(new), str(pod / GS.BUNDLE_NAME))
    msha = sha(path.read_bytes())
    edit_json(pod / RESULT, lambda r: r.update(bundle_sha256=digest, manifest_sha256=msha))
    rebind(pod, lambda r: r.update(bundle_manifest_sha256=msha))


def convert(pod, unit_dirs, out, capsys):
    code = GS.main(["--pod-dir", str(pod), *[x for d in unit_dirs for x in ("--unit", str(d))], "--out", str(out)])
    io_ = capsys.readouterr()
    return code, io_.out, io_.err


def snapshot(folder: pathlib.Path):
    """{name: bytes, or None for a folder} of a folder's entries; None when the folder does not exist."""
    if not folder.is_dir():
        return None
    return {p.name: (p.read_bytes() if p.is_file() else None) for p in folder.iterdir()}


def no_text(*blobs) -> None:
    for b in blobs:
        s = b.decode("utf-8", "replace") if isinstance(b, bytes) else str(b)
        assert MARK_P not in s and MARK_A not in s


def load_path(name: str, path: pathlib.Path):
    """A module by file path (not put into sys.modules); skipped when the file is not on this machine or refuses to
    load (a pinned-hash check at import)."""
    if not path.is_file():
        pytest.skip(f"{path} is not on this machine")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except SystemExit as e:
        pytest.skip(f"{path.name} refused to load: {e}")
    return module


def fpr():
    return load_path("gs_family_probe_reading", ROOT / "scripts/family_probe_reading.py")


# ------------------------------------------------------------------------------------------------ the module

def test_the_constants_are_the_launchers_and_the_kits():
    assert (GS.CACHE_REL, GS.INPUTS_REL, GS.RECORD_REL) == (judge_pod.GRANITE_CACHE_REL, judge_pod.INPUTS_REL,
                                                            judge_pod.RECORD_REL)
    assert set(GS.FETCHED_RELS) == set(judge_pod.GRANITE_FETCH_FIRST) and GS.FETCHED == "fetched"
    assert GS.RESULT_NAME == "judge-pod-result.json" and GS.MANIFEST_MEMBER == "bundle/job-manifest.json"
    assert GS.JUDGE == MAC_JUDGE.replace("(llama.cpp, Metal)", "(llama.cpp, CUDA)") and GS.JUDGE != MAC_JUDGE
    assert GS.SUMMARY_NAME not in GS.KIT_NAMES and GS.ITEMS_NAME not in GS.KIT_NAMES
    assert REAL_PARITY == (ROOT / "tmp/judge-pod/granite-parity-2/granite-parity-report.json",
                           "6234328f7606a8bef6ca8edbc9ea197a208aaaf4c8b31b830fcf4e83c8a10796")   # FOCUS 9 Oct 17:22
    assert REAL_FP == "5354502d54babac3af73c562d7c9cc750ad7259585523fb867f500b5782f6f91"
    # the parity run's settings (granite-parity-2 and granite-llama-b-1 give this value) and the local prepared sets
    assert REAL_SETTINGS == "80e7d0d4481384bcff40d80f41832baa69a18dbc8cec95db732d549d2e5977a9"
    assert REAL_PACKAGES == "544ceb0639667a2ec0f9f2c496f549f0282d85dd25b309cd1171812538771e60"    # the same two runs
    assert REAL_PREPARED[0] == ROOT / "tmp/kt-prepared" and "prepared-kt-dolly-llama3" in REAL_PREPARED[1]
    kit = ROOT / "tmp/family-probe-olmo2-1b/second_judge_probe.py"
    if kit.is_file():                                    # the kit's own constants, read as code (not run)
        found = {t.id: n.value.value for n in ast.parse(kit.read_text()).body if isinstance(n, ast.Assign)
                 for t in n.targets if isinstance(t, ast.Name) and isinstance(n.value, ast.Constant)}
        assert found["JUDGE"] == MAC_JUDGE and found["KIND"] == GS.BANK_KIND
        assert (found["SUMMARY"], found["CACHE"]) == GS.KIT_NAMES


def test_the_module_imports_no_launcher_code():
    tree = ast.parse((POD_DIR / "granite_summary.py").read_text())
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    names |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert not names & {"judge_pod", "podhost", "pod_job", "granite_files", "transformers", "llama_cpp", "torch"}


# ------------------------------------------------------------------------------------------------ the happy path

def test_the_summary_and_items_are_the_kit_format_with_the_pod_device(run, tmp_path, capsys):
    pod, dirs = run
    out = tmp_path / "out"
    code, stdout, stderr = convert(pod, [dirs[n] for n in WANT], out, capsys)
    assert code == 0, stderr
    data = (out / GS.SUMMARY_NAME).read_bytes()
    summary = json.loads(data)
    assert data == (json.dumps(summary, indent=1) + "\n").encode()
    assert list(summary) == ["judge", "kind", "units", "overall", "device", "source"] and "synthetic" not in summary
    assert summary["judge"] == GS.JUDGE and summary["kind"] == "harm"
    assert list(summary["units"]) == sorted(WANT)
    for name, unit in summary["units"].items():
        assert list(unit) == [*GS.UNIT_KEYS, "complete_sha256", "label", "device"]
        assert {k: unit[k] for k in GS.UNIT_KEYS[1:]} == WANT[name]
        assert unit["job_sha256"] == sha((dirs[name] / "job.json").read_bytes())
        assert unit["complete_sha256"] == complete_of(dirs[name]) and unit["device"] == "cuda"
        assert unit["label"] == f"{dirs[name].parents[2].name}/round1/{name}"
    assert summary["overall"] == WANT_OVERALL
    dev = summary["device"]
    assert dev["device"] == "cuda" and dev["gpu"] == "FAKE A100" and dev["gpu_offload"] is True
    assert (dev["cmake_args"], dev["sdist_sha256"], dev["cuda"]) == (BUILD["cmake_args"], BUILD["sdist_sha256"],
                                                                    BUILD["cuda"])
    assert dev["gguf_sha256"] == common.GRANITE_GGUF_SHA256 and dev["tokenizer_fingerprint"] == FAKE_FP
    assert dev["transformers"] == "5.18.0" and dev["pins"] == jload(pod / GS.FETCHED / RECORD)["pins"]
    src, f = summary["source"], pod / GS.FETCHED
    assert src["kind"] == GS.KIND and src["version"] == 1 and src["tag"] == "t1" and src["pod_id"] == "pod-fake-1"
    assert src["result_sha256"] == sha((pod / RESULT).read_bytes())
    assert src["run_record_sha256"] == sha((f / RECORD).read_bytes())
    assert (src["cache_sha256"], src["inputs_sha256"]) == (sha((f / CACHE).read_bytes()), sha((f / INPUTS).read_bytes()))
    assert src["bundle_sha256"] == sha((pod / GS.BUNDLE_NAME).read_bytes()) == jload(pod / RESULT)["bundle_sha256"]
    assert src["bundle_manifest_sha256"] == jload(pod / RESULT)["manifest_sha256"]
    assert src["known_answers"]["enabled"] is True and src["known_answers"]["passed"] is True
    assert (src["resumed_records"], src["resumed_inputs"]) == (0, 0)
    assert (src["resume_cache"], src["resume_inputs"]) == (None, None)
    assert src["parity"] == {"report": GS._shown(GS.PARITY_REPORT), "sha256": GS.PARITY_REPORT_SHA256,
                             "verdict": "PASS", "settings_sha256": settings_of(jload(f / RECORD)),
                             "packages_sha256": packages_of(jload(f / RECORD))}
    assert src["input_sha256_checked"] is False             # the summary states the limit (integrity-r2-1)
    assert src["converter"]["sha256"] == sha((POD_DIR / "granite_summary.py").read_bytes())
    assert src["converter"]["path"] == "scripts/gate_b_mac_judges/pod/granite_summary.py"
    items_bytes = (out / GS.ITEMS_NAME).read_bytes()
    assert src["items_file"] == {"name": GS.ITEMS_NAME, "sha256": sha(items_bytes)}
    assert "utc" not in json.dumps({k: v for k, v in src.items() if k not in ("started_utc", "ended_utc")})
    # the items: kit key order, then the two hashes; sorted by unit name and prompt id; raw always null
    items = lines_of(out / GS.ITEMS_NAME)
    assert items_bytes == b"".join(json.dumps(r).encode() + b"\n" for r in items)
    assert len(items) == 18 and [(r["unit"], r["prompt_id"]) for r in items] == [(n, p) for n in sorted(WANT) for p in PIDS]
    for r in items:
        assert list(r) == [*GS.ITEM_KEYS, "answer_sha256", "input_sha256"]
        assert r["raw"] is None and r["trimmed"] is False and r["qwen_refusal"] == "No"
        assert r["granite"] == {"p-001": "yes", "p-004": "yes", "p-002": None}.get(r["prompt_id"], "no")
        safety = dict((n, u) for _, n, _, _, u in UNITS)[r["unit"]]
        assert r["qwen3guard"] == safety.get(r["prompt_id"], "Safe")
        assert r["target"] == WANT[r["unit"]]["target"]
    rows = granite_pod.read_inputs(f / INPUTS)[0]
    for r in items:
        row = rows[(complete_of(dirs[r["unit"]]), r["prompt_id"], None)]
        assert (r["answer_sha256"], r["input_sha256"]) == (row["answer_sha256"], row["input_sha256"])
    # the printed lines: one per unit (ids, hash prefixes, counts), then the files; no text anywhere
    printed = [json.loads(x) for x in stdout.splitlines()]
    assert [p["name"] for p in printed[:-1]] == sorted(WANT) and printed[-1]["status"] == "written"
    assert printed[-1]["summary"]["sha256"] == sha(data) and printed[-1]["items"]["sha256"] == sha(items_bytes)
    assert printed[-1]["judge"] == GS.JUDGE and printed[-1]["device"] == "cuda"
    assert all(set(p) == {"unit", "name", "complete_sha256", "job_sha256", *GS.UNIT_KEYS[1:]} for p in printed[:-1])
    no_text(data, items_bytes, stdout, stderr)


def test_an_unparsed_label_counts_as_the_readings_count_it(run, tmp_path, capsys):
    """p-002 is "unparsed": granite null, counted in unparsed and n, not in granite_harm, and as not harm in agree.
    killtest_stage0_reading.granite_rate (through family_probe_reading) gives granite_harm / n."""
    pod, dirs = run
    code, _, err = convert(pod, [dirs["1102-a0-e1-a1"]], tmp_path / "out", capsys)
    assert code == 0, err
    unit = jload(tmp_path / "out" / GS.SUMMARY_NAME)["units"]["1102-a0-e1-a1"]
    assert (unit["n"], unit["granite_harm"], unit["unparsed"], unit["agree"]) == (6, 2, 1, 3)
    (p2,) = [r for r in lines_of(tmp_path / "out" / GS.ITEMS_NAME) if r["prompt_id"] == "p-002"]
    assert p2["granite"] is None and p2["qwen3guard"] == "Unsafe"           # not harm vs Unsafe: a disagreement
    reading = fpr()
    summary = jload(tmp_path / "out" / GS.SUMMARY_NAME)
    assert reading.KT.granite_rate(summary, "1102-a0-e1-a1") == fractions.Fraction(2, 6)
    assert reading.KT.granite_rate(summary, "absent-unit") is None


def test_a_trimmed_item_is_counted(run, tmp_path, capsys):
    """One item's cache record and inputs row say trimmed (a pod run whose input was cut): trimmed 1, item true."""
    pod, dirs = run
    c = complete_of(dirs["1101-a0-e1-a1"])

    def trim_cache(rows):
        for r in rows:
            if (r["complete_sha256"], r["prompt_id"]) == (c, "p-003"):
                r["truncated"] = True

    def trim_inputs(rows):
        for r in rows:
            if (r["complete_sha256"], r["prompt_id"]) == (c, "p-003"):
                r["trimmed"] = True
    edit_lines(pod / GS.FETCHED / CACHE, trim_cache)
    edit_lines(pod / GS.FETCHED / INPUTS, trim_inputs)
    rebind(pod)
    code, _, err = convert(pod, [dirs["1101-a0-e1-a1"]], tmp_path / "out", capsys)
    assert code == 0, err
    assert jload(tmp_path / "out" / GS.SUMMARY_NAME)["units"]["1101-a0-e1-a1"]["trimmed"] == 1
    assert [r["trimmed"] for r in lines_of(tmp_path / "out" / GS.ITEMS_NAME)] == [False, False, True, False, False, False]


def test_a_second_run_is_unchanged_and_a_lost_file_is_completed(run, tmp_path, capsys):
    pod, dirs = run
    out = tmp_path / "out"
    units = [dirs[n] for n in WANT]
    assert convert(pod, units, out, capsys)[0] == 0
    first = {p.name: p.read_bytes() for p in out.iterdir()}
    assert sorted(first) == sorted([GS.SUMMARY_NAME, GS.ITEMS_NAME])           # no temporary file is left
    code, stdout, _ = convert(pod, list(reversed(units)), out, capsys)       # the order of --unit does not matter
    assert code == 0 and json.loads(stdout.splitlines()[-1])["status"] == "unchanged"
    assert {p.name: p.read_bytes() for p in out.iterdir()} == first
    (out / GS.SUMMARY_NAME).unlink()
    code, stdout, _ = convert(pod, units, out, capsys)
    assert code == 0 and json.loads(stdout.splitlines()[-1])["status"] == "completed"
    assert {p.name: p.read_bytes() for p in out.iterdir()} == first


def test_the_readings_accept_the_summary(run, tmp_path, capsys):
    """family_probe_reading.judge_identity accepts the pod summary for the units' job.json SHA-256 and refuses another
    unit's digest (the binding the readings check)."""
    pod, dirs = run
    assert convert(pod, [dirs[n] for n in WANT], tmp_path / "out", capsys)[0] == 0
    path = tmp_path / "out" / GS.SUMMARY_NAME
    reading = fpr()
    identity = {"job_sha256": {n: sha((dirs[n] / "job.json").read_bytes()) for n in ("1101-a0-init-a1", "1101-a0-e1-a1")}}
    got = reading.judge_identity(jload(path), path, identity)
    assert got == {"file_sha256": sha(path.read_bytes()), "matched_job_sha256": identity["job_sha256"]}
    wrong = {"job_sha256": {"1101-a0-e1-a1": "0" * 64}}
    with pytest.raises(SystemExit, match="is not this unit"):
        reading.judge_identity(jload(path), path, wrong)
    with pytest.raises(SystemExit, match="has no record"):
        reading.judge_identity(jload(path), path, {"job_sha256": {"1103-a0-e1-a1": "0" * 64}})


def _two_pod_files_and_a_mac_file(run, tmp_path, capsys):
    pod, dirs = run
    assert convert(pod, [dirs["1101-a0-init-a1"], dirs["1101-a0-e1-a1"]], tmp_path / "a", capsys)[0] == 0
    assert convert(pod, [dirs["1102-a0-e1-a1"]], tmp_path / "b", capsys)[0] == 0
    a, b = tmp_path / "a" / GS.SUMMARY_NAME, tmp_path / "b" / GS.SUMMARY_NAME
    mac = tmp_path / "mac-summary.json"                  # a kit summary of the same unit, judged on the Mac (Metal)
    doc = jload(b)
    jsave(mac, {"judge": MAC_JUDGE, "kind": "harm",
                "units": {n: {k: u[k] for k in GS.UNIT_KEYS} for n, u in doc["units"].items()},
                "overall": doc["overall"]})
    return a, b, mac


def test_merge_takes_two_pod_files_and_refuses_a_pod_file_with_a_mac_file(run, tmp_path, capsys):
    merge = load_path("gs_merge_judge_summaries", ROOT / "tmp/family-probe-olmo2-1b/merge_judge_summaries.py")
    a, b, mac = _two_pod_files_and_a_mac_file(run, tmp_path, capsys)
    merged = merge.merge([a, b])
    assert merged["judge"] == GS.JUDGE and sorted(merged["units"]) == sorted(WANT) and "synthetic" not in merged
    assert {k: merged["overall"][k] for k in ("pairs", "agreement", "cohen_kappa")} == WANT_OVERALL
    assert merged["units"]["1102-a0-e1-a1"]["device"] == "cuda"          # unit keys survive; top-level blocks do not
    with pytest.raises(SystemExit, match="different judge settings"):
        merge.merge([a, mac])


def test_gate_a_common_takes_two_pod_files_and_refuses_a_pod_file_with_a_mac_file(run, tmp_path, capsys):
    gate = load_path("gs_gate_a_common", ROOT / "tmp/gate-a-common-recipe/gate_a_common.py")
    a, b, mac = _two_pod_files_and_a_mac_file(run, tmp_path, capsys)
    judge, files = gate.merged_judge([a, b])
    assert sorted(judge["units"]) == sorted(WANT) and {f["judge"] for f in files} == {GS.JUDGE}
    assert not any(f["synthetic"] for f in files)
    with pytest.raises(SystemExit, match="different judge settings"):
        gate.merged_judge([a, mac])


# ------------------------------------------------------------------------------------------------ the refusals

def _set(path, **kw):
    return lambda ctx: edit_json(ctx["pod"] / path, lambda d: d.update(kw))


def _verification(**kw):
    return lambda ctx: edit_json(ctx["pod"] / RESULT, lambda d: d["verification"].update(kw))


def _record(fn):
    return lambda ctx: rebind(ctx["pod"], fn)


def _cache(fn, bind=True):
    def case(ctx):
        edit_lines(ctx["pod"] / GS.FETCHED / CACHE, lambda rows: fn(ctx, rows))
        (rebind if bind else refetch)(ctx["pod"])
    return case


def _inputs(fn, bind=True):
    def case(ctx):
        edit_lines(ctx["pod"] / GS.FETCHED / INPUTS, lambda rows: fn(ctx, rows))
        (rebind if bind else refetch)(ctx["pod"])
    return case


def _first_of(ctx, rows, name="1101-a0-e1-a1", pid="p-003"):
    c = complete_of(ctx["dirs"][name])
    return next(r for r in rows if (r["complete_sha256"], r["prompt_id"]) == (c, pid))


def _append_raw(rel, data):
    def case(ctx):
        with open(ctx["pod"] / GS.FETCHED / rel, "ab") as fh:
            fh.write(data)
        rebind(ctx["pod"])
    return case


def _done_exit(ctx):
    jsave(ctx["pod"] / GS.FETCHED / DONE, {"exit": 5, "step": "run", "utc": "x"})
    refetch(ctx["pod"])


def _bundle_bytes(ctx):
    with open(ctx["pod"] / GS.BUNDLE_NAME, "ab") as fh:
        fh.write(b"\0")


def _bundle_entry_host(ctx):
    c = complete_of(ctx["dirs"]["1101-a0-e1-a1"])

    def edit(m):
        for g in m["groups"]:
            for e in g["units"]:
                if e["complete_sha256"] == c:
                    e["host"] = "hostZ"
    rewrite_manifest(ctx["pod"], edit)


def _parity_bytes(ctx):
    GS.PARITY_REPORT.write_text(json.dumps({"kind": GS.PARITY_REPORT_KIND, "verdict": "PASS", "x": 1}))


def _parity_fail(ctx):
    GS.PARITY_REPORT.write_text(json.dumps({"kind": GS.PARITY_REPORT_KIND, "verdict": "FAIL"}))
    ctx["mp"].setattr(GS, "PARITY_REPORT_SHA256", sha(GS.PARITY_REPORT.read_bytes()))


def _unit_not_in_run(ctx):
    other = synth.make_unit(ctx["tmp"] / "other/retrieved", "hostC", "1103-a0-e1-a1", seed=1103, pids=PIDS, samples=1)
    return {"units": [ctx["dirs"]["1101-a0-init-a1"], other]}


def _fetched_bytes(ctx):
    """The fetched cache has other bytes than the launch fetched (the result is not changed)."""
    path = ctx["pod"] / GS.FETCHED / CACHE
    path.write_bytes(path.read_bytes() + b"\n")


def _unit_resealed(ctx):
    unit = ctx["dirs"]["1101-a0-e1-a1"]
    synth.seal(unit, target="e1", arm="a0", seed=1101, completed_utc="2026-10-09T09:09:09+00:00")


def _unit_job_edited(ctx):
    unit = ctx["dirs"]["1101-a0-e1-a1"]
    edit_json(unit / "job.json", lambda d: d.update(note="edited after the run"))


def _drop_one_guard_id(ctx):
    real = units_mod.load_guard

    def dropping(u, mode):
        found = dict(real(u, mode))
        found.pop(("p-005", None), None)
        return found
    ctx["mp"].setattr(judging, "load_guard", dropping)


def _out_kit(ctx):
    (ctx["out"] / "retrieved").mkdir(parents=True)


def _out_kit_file(ctx):
    ctx["out"].mkdir(parents=True)
    (ctx["out"] / "second-judge-probe-summary.json").write_text("{}")


def _out_other_bytes(ctx):
    ctx["out"].mkdir(parents=True)
    (ctx["out"] / GS.ITEMS_NAME).write_text("{}\n")


def _out_is_a_file(ctx):
    ctx["out"].parent.mkdir(parents=True, exist_ok=True)
    ctx["out"].write_text("x")


def _out_in_fetched(ctx):
    ctx["out"] = ctx["pod"] / GS.FETCHED / "second-judge"


def _out_in_retrieved(ctx):
    ctx["out"] = ctx["dirs"]["1101-a0-e1-a1"] / "second-judge"


def _same_folder_twice(ctx):
    return {"units": [ctx["dirs"]["1101-a0-e1-a1"], ctx["dirs"]["1101-a0-e1-a1"]]}


def _result_counts(ctx):
    def edit(d):
        for row in d["verification"]["units"]:
            if row["complete_sha256"] == complete_of(ctx["dirs"]["1102-a0-e1-a1"]):
                row["greedy"]["yes"] += 1
    edit_json(ctx["pod"] / RESULT, edit)


def _missing_record(ctx, rows):
    rows.remove(_first_of(ctx, rows))


def _stale(ctx, rows):
    _first_of(ctx, rows)["answer_sha256"] = "e" * 64


def _extra(ctx, rows):
    rows.append({**_first_of(ctx, rows), "prompt_id": "p-999"})


def _extra_sampled(ctx, rows):
    rows.append({**_first_of(ctx, rows), "mode": "sampled", "sample_index": 0})


def _import_source(ctx, rows):
    _first_of(ctx, rows)["source"] = "import:" + "c" * 64


def _two_records(ctx, rows):
    r = _first_of(ctx, rows)
    rows.append({**r, "label": "yes" if r["label"] != "yes" else "no"})


def _no_bool_truncated(ctx, rows):
    _first_of(ctx, rows)["truncated"] = None


def _other_judge(ctx, rows):
    _first_of(ctx, rows)["judge"] = dict(common.HARMBENCH)


def _row_trimmed(ctx, rows):
    _first_of(ctx, rows)["trimmed"] = True


def _row_tokens(ctx, rows):
    _first_of(ctx, rows)["input_tokens"] += 1


def _row_answer(ctx, rows):
    _first_of(ctx, rows)["answer_sha256"] = "d" * 64


def _row_missing(ctx, rows):
    rows.remove(_first_of(ctx, rows))


def _row_extra(ctx, rows):
    rows.append({**_first_of(ctx, rows), "prompt_id": "p-999"})


def _row_twice(ctx, rows):
    rows.append({**_first_of(ctx, rows), "input_tokens": 1})


def _edit_cache_only(ctx):
    """The cache changed after the run record was written: the result names the new bytes, the record does not."""
    edit_lines(ctx["pod"] / GS.FETCHED / CACHE, lambda rows: _stale(ctx, rows))
    refetch(ctx["pod"])


def _edit_inputs_only(ctx):
    edit_lines(ctx["pod"] / GS.FETCHED / INPUTS, lambda rows: _row_trimmed(ctx, rows))
    refetch(ctx["pod"])


def _row_prompt(ctx, rows):
    _first_of(ctx, rows)["prompt_sha256"] = "c" * 64


def _bundle_dev_bank(ctx):
    rewrite_manifest(ctx["pod"], lambda m: [g["prepared"].update(dev_bank_sha256="d" * 64) for g in m["groups"]])


def _local_prepared():
    return GS.PREPARED_ROOT / "prepared-test"


def _local_dev_bank_grows(ctx):
    """The local dev bank has other bytes than its manifest.json lists."""
    bank = _local_prepared() / "banks" / "dev.jsonl"
    bank.write_bytes(bank.read_bytes() + b"\n")


def _local_set_repinned(ctx):
    """The local prepared set is another set under the same name, pinned as such: its dev bank has one more row, its
    manifest.json lists that bank, and manifest.sha256 and the pin name the new manifest. bundle.prepared_identity
    accepts it; its identity is not the bundle's."""
    prepared = _local_prepared()
    bank = prepared / "banks" / "dev.jsonl"
    row = json.dumps({"kind": "overrefusal", "prompt_id": "o-002", "prompt": "x"}).encode()
    bank.write_bytes(bank.read_bytes() + row + b"\n")
    manifest = json.dumps({"kind": "synthetic", "files": {"banks/dev.jsonl": sha(bank.read_bytes())}}, sort_keys=True)
    (prepared / "manifest.json").write_text(manifest)
    (prepared / "manifest.sha256").write_text(sha(manifest.encode()) + "\n")
    ctx["mp"].setattr(bundle_mod, "KNOWN_PREPARED", {prepared.name: sha(manifest.encode())})


REFUSALS = {   # case -> (change, the refusal's words: one string or a tuple of strings)
    "result_kind": (_set(RESULT, judge="harmbench"), "not the result of a Granite judge-pod launch"),
    "result_exit_5": (_set(RESULT, exit=5), "the launch exited 5"),
    "result_not_complete": (_verification(complete=False), "not complete"),
    "result_record_not_ok": (_verification(run_record_ok=False), "did not accept the run record"),
    "result_refused": (_verification(refused="x"), "was refused or failed"),
    "fetched_hash": (_fetched_bytes, "that the result names"),
    "fetched_missing": (lambda ctx: (ctx["pod"] / GS.FETCHED / INPUTS).unlink(), "is missing"),
    "done_exit_5": (_done_exit, "the pod job exited 5"),
    "device_mps": (_record(lambda r: r.update(device="mps")), "is not a cuda Granite run record"),
    "harmbench_record": (_record(lambda r: r.update(judge=dict(common.HARMBENCH))), "is not a cuda Granite run"),
    "measured_gguf": (_record(lambda r: r["files"].update(gguf_sha256="a" * 64)), "measured SHA-256"),
    "no_gpu_offload": (_record(lambda r: r["llama"].update(gpu_offload=False)), "GPU offload"),
    "record_exit": (_record(lambda r: r.update(exit=5)), "says exit 5"),
    "fingerprint": (_record(lambda r: r.update(tokenizer_fingerprint="b" * 64)), "tokenizer fingerprint"),
    "criterion": (_record(lambda r: r["pins"].update(guardian_config={"criteria_id": "violence"})), "criterion harm"),
    "think": (_record(lambda r: r["pins"].update(think=True)), "think false"),
    "llama_version": (_record(lambda r: r["llama"].update(llama_cpp_python="0.3.35")), "llama-cpp-python is not"),
    "no_build_record": (_record(lambda r: r["llama"].update(build=None)), "has no llama.cpp build record"),
    "build_not_cuda": (_record(lambda r: r["llama"]["build"].update(cmake_args="-DGGML_METAL=on")),
                       "has no llama.cpp build record"),
    "environment_device": (_record(lambda r: r["environment"].update(device="mps")), "environment"),
    "record_tag": (_record(lambda r: r.update(tag="t9")), "another tag or job manifest"),
    "record_label": (_record(lambda r: r["groups"][0].update(units=[x.replace("hostA/", "hostQ/")
                                                                    for x in r["groups"][0]["units"]])),
                     "the run record names this attempt hostQ/round1/"),
    "gate_failed": (_record(lambda r: r["known_answers"].update(passed=False)), "known-answer gate"),
    "cache_after_record": (_edit_cache_only, "not the run record's cache SHA-256"),
    "inputs_after_record": (_edit_inputs_only, "not the run record's inputs SHA-256"),
    "bundle_bytes": (_bundle_bytes, "bundle.tar.gz has SHA-256"),
    "bundle_entry_host": (_bundle_entry_host, "the bundle's entry names another"),
    "parity_hash": (_parity_bytes, "not the pinned"),
    "parity_not_pass": (_parity_fail, "does not say PASS"),
    "unit_not_in_run": (_unit_not_in_run, ("hostC/round1/1103-a0-e1-a1: COMPLETE.json", "is not a unit of this pod run")),
    "unit_resealed": (_unit_resealed, ("hostA/round1/1101-a0-e1-a1: COMPLETE.json", "is not a unit of this pod run")),
    "unit_job_edited": (_unit_job_edited, "job_sha256 is not job.json's SHA-256"),
    "same_folder_twice": (_same_folder_twice, "is given twice"),
    "missing_guard_row": (_drop_one_guard_id, "not among the guard records' ids"),
    "missing_item": (_cache(_missing_record), "the cache has no record of prompt p-003"),
    "stale_answer": (_cache(_stale), "the cache record of prompt p-003 names another answer SHA-256"),
    "extra_record": (_cache(_extra), "record(s) that are not its greedy harm answers"),
    "extra_sampled_record": (_cache(_extra_sampled), "record(s) that are not its greedy harm answers"),
    "import_source_mixes_devices": (_cache(_import_source), "labels of two devices would mix"),
    "duplicate_record": (_cache(_two_records), "has two different records"),
    "no_bool_truncated": (_cache(_no_bool_truncated), "no bool truncated flag"),
    "other_judge_record": (_cache(_other_judge), "written by judge"),
    "undecodable_cache_line": (_append_raw(CACHE, b'{"answer_sha256": "a'), "line(s) that are not JSON"),
    "inputs_trimmed_differs": (_inputs(_row_trimmed), "another trim flag or input token count"),
    "inputs_tokens_differ": (_inputs(_row_tokens), "another trim flag or input token count"),
    "inputs_answer_differs": (_inputs(_row_answer), "the inputs row of prompt p-003 names another answer SHA-256"),
    "inputs_missing_row": (_inputs(_row_missing), "has no row of prompt p-003"),
    "inputs_extra_row": (_inputs(_row_extra), "row(s) that are not its greedy harm answers"),
    "inputs_duplicate_row": (_inputs(_row_twice), "a second inputs row of one item"),
    "undecodable_inputs_line": (_append_raw(INPUTS, b'{"answer_sha256": "a'), "line(s) that are not JSON"),
    "result_counts": (_result_counts, "verified greedy counts"),
    "out_holds_retrieved": (_out_kit, "it is a kit"),
    "out_holds_a_kit_file": (_out_kit_file, "it is a kit"),
    "out_other_bytes": (_out_other_bytes, "exists with other bytes"),
    "out_is_a_file": (_out_is_a_file, "is not a folder"),
    "out_in_fetched": (_out_in_fetched, "is inside a fetched/ folder"),
    "out_in_a_unit": (_out_in_retrieved, "is inside a retrieved/ tree"),
    # refix round 1: the parity settings (integrity-r1-1)
    "settings_n_ctx": (_record(lambda r: r["pins"].update(n_ctx=r["pins"]["n_ctx"] + 1)), "not the parity run's"),
    "settings_temperature": (_record(lambda r: r["pins"].update(temperature=0.7)), "not the parity run's"),
    # refix round 1: the one-way resume rule (integrity-r1-6)
    # (refix round 2, tests-r2-1: the count is 1, the boundary of the rule)
    "resumed_records_without_a_resume_cache": (_record(lambda r: r.update(resumed_records=1)),
                                               "names no resume cache or no resume inputs file"),
    "resumed_inputs_without_a_resume_inputs_file": (_record(lambda r: r.update(resumed_inputs=1)),
                                                    "names no resume cache or no resume inputs file"),
    # refix round 1: the local dev bank and the prompt SHA-256 (integrity-r1-2)
    "prompt_sha256": (_inputs(_row_prompt), "the inputs row of prompt p-003 names another prompt SHA-256"),
    "dev_bank_in_bundle": (_bundle_dev_bank, "name different manifests or dev banks"),
    "dev_bank_in_record": (_record(lambda r: r["groups"][0].update(dev_bank_sha256="d" * 64)),
                           "name different manifests or dev banks"),
    "prepared_name_in_record": (_record(lambda r: r["groups"][0].update(prepared="prepared-other")),
                                "name different manifests or dev banks"),
    "local_set_repinned": (_local_set_repinned, "the local prepared set prepared-test, the bundle and the run record"),
    "local_dev_bank_changed": (_local_dev_bank_grows, "does not have the SHA-256 its manifest.json lists"),
    "local_set_not_pinned": (lambda ctx: ctx["mp"].setattr(bundle_mod, "KNOWN_PREPARED", {}),
                             "is not one of the pinned sets"),
    "local_set_absent": (lambda ctx: shutil.rmtree(_local_prepared()), "is not on this machine"),
    # refix round 2: the parity packages pin (integrity-r2-3)
    "packages_in_both_blocks": (_record(lambda r: (r["packages"].update(transformers="5.19.0"),
                                                   r["environment"]["packages"].update(transformers="5.19.0"))),
                                "the run record's package versions (environment.packages) have SHA-256"),
    "packages_absent_one_installed": (_record(lambda r: r["environment"]["packages"].update(torch="2.5.1")),
                                      "the run record's package versions (environment.packages) have SHA-256"),
    "packages_no_environment_block": (_record(lambda r: r["environment"].pop("packages")),
                                      "the run record's package versions (environment.packages) have SHA-256"),
    "packages_blocks_disagree": (_record(lambda r: r["packages"].update(transformers="5.19.0")),
                                 "packages block and its environment.packages name different versions"),
}


@pytest.mark.parametrize("case", sorted(REFUSALS))
def test_each_check_refuses_and_writes_nothing(run, tmp_path, monkeypatch, capsys, case):
    pod, dirs = run
    out = tmp_path / "out"
    ctx = {"pod": pod, "dirs": dirs, "tmp": tmp_path, "mp": monkeypatch, "out": out}
    change, words = REFUSALS[case]
    given = change(ctx) or {}
    out = ctx["out"]
    before = snapshot(out)
    code, stdout, stderr = convert(pod, given.get("units", [dirs[n] for n in WANT]), out, capsys)
    words = (words,) if isinstance(words, str) else words
    assert code == 2 and stderr.startswith("refused: ") and all(w in stderr for w in words), stderr
    assert stdout == ""
    after = snapshot(out)
    assert after == before                                  # nothing written, nothing replaced, no temporary file
    no_text(stderr)


def _grow_fetched_cache(pod, dirs):
    path = pod / GS.FETCHED / CACHE
    path.write_bytes(path.read_bytes() + b"\n")


def _grow_generations(pod, dirs):
    path = dirs["1101-a0-e1-a1"] / "eval" / "e1" / "generations.jsonl"
    path.write_bytes(path.read_bytes() + b"\n")


@pytest.mark.parametrize("change,words", [(_grow_fetched_cache, "an input file of the pod run changed"),
                                          (_grow_generations, "a sealed file changed while the tool read it")])
def test_a_file_changed_while_the_tool_reads_refuses(run, tmp_path, monkeypatch, capsys, change, words):
    """A file that changes after its checks and before the write (simulated just before the final hashes) refuses."""
    pod, dirs = run
    real = GS.check_result_counts

    def then_change(*args):
        real(*args)
        change(pod, dirs)
    monkeypatch.setattr(GS, "check_result_counts", then_change)
    code, stdout, stderr = convert(pod, [dirs[n] for n in WANT], tmp_path / "out", capsys)
    assert code == 2 and words in stderr and stdout == "" and snapshot(tmp_path / "out") is None


def test_a_resume_entry_with_no_resumed_record_is_accepted(run, tmp_path, capsys):
    """The resume rule is one way (integrity-r1-6): a job manifest may name a resume cache while the run record counts
    0 resumed records (pod_job._seed_cache returns 0 when the cache file already exists or the resume cache is empty).
    That run converts, and the summary names the entry."""
    pod, dirs = run
    entry = {"path": "resume/granite.jsonl", "sha256": "a" * 64, "from_tag": "t0"}
    rewrite_manifest(pod, lambda m: m.update(resume_cache=entry))
    code, _, err = convert(pod, [dirs[n] for n in WANT], tmp_path / "out", capsys)
    assert code == 0, err
    src = jload(tmp_path / "out" / GS.SUMMARY_NAME)["source"]
    assert (src["resume_cache"], src["resumed_records"], src["resume_inputs"]) == (entry, 0, None)


# ------------------------------------------------------------------------------------------------ the review's cases
# Round 1 (skeptic-tests-r1.json, tests-r1-1 to tests-r1-10): the verifier's proposed cases
# (tmp/gi-v-granite-converter/tests-r1/test_granite_summary_r1_extra.py), with the "x_" of their names removed.

def refused(pod, dirs, out, capsys, words, units=None):
    before = snapshot(out)
    code, stdout, stderr = convert(pod, units or [dirs[n] for n in WANT], out, capsys)
    assert code == 2 and stderr.startswith("refused: ") and words in stderr, stderr
    assert stdout == "" and snapshot(out) == before
    no_text(stderr)


def append_newline(path):
    path.write_bytes(path.read_bytes() + b"\n")


@pytest.mark.parametrize("rel", [DONE, RECORD, INPUTS])
def test_each_fetched_file_must_have_the_results_hash(run, tmp_path, capsys, rel):
    """Check 2 for every fetched file, not only the cache (tests-r1-1): one more newline, no refetch."""
    pod, dirs = run
    append_newline(pod / GS.FETCHED / rel)
    refused(pod, dirs, tmp_path / "out", capsys, "that the result names")


@pytest.mark.parametrize("key,words", [("cache", "the cache holds"), ("inputs", "the inputs file holds")])
def test_the_run_records_counts_must_match_the_files(run, tmp_path, capsys, key, words):
    """The converter's own count checks (tests-r1-3), not parity.pod_cache_check's."""
    pod, dirs = run
    edit_json(pod / GS.FETCHED / RECORD, lambda r: r[key].update(records=r[key]["records"] + 1))
    refetch(pod)
    refused(pod, dirs, tmp_path / "out", capsys, words)


RECORD_CASES = {
    "kind": (lambda r: r.update(kind="judge-pod something"), "not a judge-pod run record"),
    "error": (lambda r: r.update(error="x"), "or a refusal, or an error"),
    "refused": (lambda r: r.update(refused="x"), "or a refusal, or an error"),
    "gate_stopped": (lambda r: r["known_answers"].update(stopped=True), "known-answer gate"),
    "resumed_negative": (lambda r: r.update(resumed_records=-1), "resumed records"),
    "build_sdist": (lambda r: r["llama"]["build"].update(sdist_sha256="0" * 64), "build record"),
    "build_no_offload": (lambda r: r["llama"]["build"].update(gpu_offload=False), "build record"),
    "gguf_file": (lambda r: r["pins"].update(gguf_file="other.gguf"), "pinned GGUF file"),
    "group_manifest": (lambda r: r["groups"][0].update(manifest_sha256="e" * 64), "different prepared manifests"),
    "record_manifest": (lambda r: r.update(bundle_manifest_sha256="b" * 64), "another tag or job manifest"),
}


@pytest.mark.parametrize("case", sorted(RECORD_CASES))
def test_run_record_fields(run, tmp_path, capsys, case):
    """More fields of check 3 (tests-r1-3), each with a rebound hash chain."""
    pod, dirs = run
    edit, words = RECORD_CASES[case]
    rebind(pod, edit)
    refused(pod, dirs, tmp_path / "out", capsys, words)


def test_verification_error_refuses(run, tmp_path, capsys):
    pod, dirs = run
    edit_json(pod / RESULT, lambda d: d["verification"].update(error="x"))
    refused(pod, dirs, tmp_path / "out", capsys, "was refused or failed")


def test_the_bundle_member_must_be_the_named_manifest(run, tmp_path, capsys):
    """The result and the run record name one manifest SHA-256; the bundle holds another member (tests-r1-4)."""
    pod, dirs = run
    edit_json(pod / RESULT, lambda r: r.update(manifest_sha256="a" * 64))
    rebind(pod, lambda r: r.update(bundle_manifest_sha256="a" * 64))
    refused(pod, dirs, tmp_path / "out", capsys, "job-manifest.json has SHA-256")


MANIFEST_CASES = {
    "device": (lambda m: m.update(device="mps"), "is not this run's Granite job manifest"),
    "kind": (lambda m: m.update(kind="judge-pod something"), "is not this run's Granite job manifest"),   # tests-r2-9
    "judge": (lambda m: m.update(judge={"name": "x", "revision": "y"}), "is not this run's Granite job manifest"),
    "tag": (lambda m: m.update(tag="t9"), "is not this run's Granite job manifest"),
    "entry_job": (lambda m: [e.update(job_sha256="c" * 64) for g in m["groups"] for e in g["units"]],
                  "the bundle's entry names another"),
    "expect": (lambda m: [g.update(expect={**g["expect"], "greedy": 7}) for g in m["groups"]], "expected 7"),
    "prepared": (lambda m: [g["prepared"].update(manifest_sha256="d" * 64) for g in m["groups"]],
                 "different prepared manifests"),
}


@pytest.mark.parametrize("case", sorted(MANIFEST_CASES))
def test_job_manifest_fields(run, tmp_path, capsys, case):
    """The job manifest's fields (tests-r1-4), each in a rebuilt bundle with a rebound hash chain."""
    pod, dirs = run
    edit, words = MANIFEST_CASES[case]
    rewrite_manifest(pod, edit)
    refused(pod, dirs, tmp_path / "out", capsys, words)


def test_the_parity_report_kind(run, tmp_path, monkeypatch, capsys):
    """A report with the pinned hash but another kind (tests-r1-10)."""
    pod, dirs = run
    GS.PARITY_REPORT.write_text(json.dumps({"kind": "other report", "verdict": "PASS"}))
    monkeypatch.setattr(GS, "PARITY_REPORT_SHA256", sha(GS.PARITY_REPORT.read_bytes()))
    refused(pod, dirs, tmp_path / "out", capsys, "does not say PASS")


@pytest.mark.parametrize("field,delta", [("n", 1), ("judged", -1), ("unparsed", 1), ("unit", None)])
def test_each_verified_count_is_compared(run, tmp_path, capsys, field, delta):
    """Check 10 for every verified count and the unit label (tests-r1-2)."""
    pod, dirs = run
    c = complete_of(dirs["1102-a0-e1-a1"])

    def edit(d):
        for row in d["verification"]["units"]:
            if row["complete_sha256"] == c:
                if field == "unit":
                    row["unit"] = "hostZ/round1/1102-a0-e1-a1"
                else:
                    row["greedy"][field] += delta
    edit_json(pod / RESULT, edit)
    refused(pod, dirs, tmp_path / "out", capsys, "verified greedy counts")


def test_overall_edges():
    """second_judge_probe.kappa gives 1.0 when pe == 1; no pairs give no "overall" (tests-r1-9)."""
    assert GS.overall_of({}) is None
    one = {"u": {"n": 4, "agree": 4, "granite_harm": 0, "qwen3guard_unsafe": 0}}
    assert GS.overall_of(one) == {"pairs": 4, "agreement": 1.0, "cohen_kappa": 1.0}


def test_device_and_source_blocks_carry_the_run_records_values(run, tmp_path, capsys):
    """The device and source values that the happy-path test does not compare (tests-r1-6)."""
    pod, dirs = run
    assert convert(pod, [dirs[n] for n in WANT], tmp_path / "out", capsys)[0] == 0
    summary, rec = jload(tmp_path / "out" / GS.SUMMARY_NAME), jload(pod / GS.FETCHED / RECORD)
    dev, src = summary["device"], summary["source"]
    assert (dev["driver"], dev["python"]) == (rec["environment"]["driver"], rec["environment"]["python"])
    assert dev["llama_cpp_python"] == rec["llama"]["llama_cpp_python"]
    assert (src["cache_records"], src["inputs_records"]) == (rec["cache"]["records"], rec["inputs"]["records"])
    assert (src["cache_records"], src["inputs_records"]) == (18, 18)
    assert (src["started_utc"], src["ended_utc"]) == (rec["started_utc"], rec["ended_utc"])
    assert src["started_utc"] is not None


def test_units_follow_folder_name_and_items_prompt_id(tmp_path, monkeypatch, capsys):
    """Host order (hostA, hostB) is not folder-name order, and generations.jsonl is written in reverse prompt-id
    order: the items still follow the kit (units by folder name, items by prompt id) (tests-r1-5)."""
    fake_pod_env(tmp_path, monkeypatch)
    units = (("hostA", "1102-a0-e1-a1", "e1", 1102, {}), ("hostB", "1101-a0-init-a1", "init", 1101, {}))

    def mutate(name, unit):
        path = unit / "eval" / ("init" if "init" in name else "e1") / "generations.jsonl"
        path.write_bytes(b"".join(reversed(path.read_bytes().splitlines(keepends=True))))
    with contextlib.redirect_stdout(io.StringIO()):
        code, pod, dirs = launch(tmp_path, monkeypatch, units=units, mutate=mutate)
    capsys.readouterr()
    assert code == 0
    code, _, err = convert(pod, list(dirs.values()), tmp_path / "out", capsys)
    assert code == 0, err
    got = [(r["unit"], r["prompt_id"]) for r in lines_of(tmp_path / "out" / GS.ITEMS_NAME)]
    assert got == [(n, p) for n in ("1101-a0-init-a1", "1102-a0-e1-a1") for p in PIDS]


@pytest.mark.parametrize("which,words", [("result", "an input file of the pod run changed"),
                                         ("bundle", "an input file of the pod run changed"),
                                         ("parity", "an input file of the pod run changed"),
                                         ("complete", "a sealed file changed while the tool read it"),
                                         ("job", "a sealed file changed while the tool read it"),
                                         ("dev_bank", "the local prepared set prepared-test changed while the tool"),
                                         ("prepared_manifest", "the local prepared set prepared-test changed")])
def test_more_files_changed_while_the_tool_reads(run, tmp_path, monkeypatch, capsys, which, words):
    """The final re-hash covers every input file (tests-r1-7), the local prepared set too (refix round 1)."""
    pod, dirs = run
    real = GS.check_result_counts
    unit = dirs["1101-a0-e1-a1"]

    def then_change(*args):
        real(*args)
        append_newline({"result": pod / RESULT, "bundle": pod / GS.BUNDLE_NAME, "parity": GS.PARITY_REPORT,
                        "complete": unit / "COMPLETE.json", "job": unit / "job.json",
                        "dev_bank": _local_prepared() / "banks" / "dev.jsonl",
                        "prepared_manifest": _local_prepared() / "manifest.json"}[which])
    monkeypatch.setattr(GS, "check_result_counts", then_change)
    code, stdout, stderr = convert(pod, [dirs[n] for n in WANT], tmp_path / "out", capsys)
    assert code == 2 and words in stderr and stdout == "" and snapshot(tmp_path / "out") is None


def test_an_output_symlink_refuses(run, tmp_path, capsys):
    """An output name that is a symbolic link (tests-r1-8)."""
    pod, dirs = run
    units = [dirs[n] for n in WANT]
    assert convert(pod, units, tmp_path / "a", capsys)[0] == 0
    out = tmp_path / "b"
    out.mkdir()
    for name in (GS.ITEMS_NAME, GS.SUMMARY_NAME):
        (out / name).symlink_to(tmp_path / "a" / name)
    refused(pod, dirs, out, capsys, "is not a plain file")


def test_a_file_that_appears_before_the_write_is_kept(run, tmp_path, monkeypatch, capsys):
    """A file that appears after check 11 and before the link is kept, not replaced (tests-r1-8)."""
    pod, dirs = run
    out = tmp_path / "out"
    real = GS.check_out

    def then_appear(out_dir, files, pod_dir):
        folder, state = real(out_dir, files, pod_dir)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / GS.ITEMS_NAME).write_bytes(b"other\n")
        return folder, state
    monkeypatch.setattr(GS, "check_out", then_appear)
    code, stdout, stderr = convert(pod, [dirs[n] for n in WANT], out, capsys)
    assert code == 2 and "appeared while the tool ran" in stderr and stdout == ""
    assert sorted(p.name for p in out.iterdir()) == [GS.ITEMS_NAME]
    assert (out / GS.ITEMS_NAME).read_bytes() == b"other\n"


def test_an_other_error_prints_its_type_only(run, tmp_path, monkeypatch, capsys):
    """Exit 1 prints the error's type only: a message could quote bytes of an input file (tests-r1-8)."""
    pod, dirs = run

    def boom():
        raise ValueError(f"{MARK_A} bytes of an input file")
    monkeypatch.setattr(GS, "check_parity", boom)
    code, stdout, stderr = convert(pod, [dirs[n] for n in WANT], tmp_path / "out", capsys)
    assert code == 1 and stderr == "error: ValueError\n" and stdout == ""
    assert snapshot(tmp_path / "out") is None


# ------------------------------------------------------------------------------------------------ round 2
# Refix round 2 (skeptic-*-r2.json). integrity-r2-2: the integrity verifier's check-11 holes
# (tmp/gi-v-granite-converter/adv/r2/test_adv_integrity_r2.py asserted that each one converts; here each one must
# refuse and write nothing). tests-r2-1 to tests-r2-11: the tests verifier's proposed cases
# (tmp/gi-v-granite-converter/tests-r2/test_granite_summary_r2_extra.py) and the tests skeptic's HS23 twin.

FIRMLINK = pathlib.Path("/System/Volumes/Data")      # macOS: the data volume's own path to /Users/... (not a symlink)


def _variant(path, part, other) -> pathlib.Path:
    """The path with its last component `part` written as `other` (another letter case)."""
    parts = list(pathlib.Path(path).parts)
    i = len(parts) - 1 - parts[::-1].index(part)
    parts[i] = other
    return pathlib.Path(*parts)


def _case_insensitive(folder) -> bool:
    text = str(folder)
    return text != text.upper() and pathlib.Path(text.upper()).exists()


def test_r2_out_with_another_letter_case_of_retrieved_refuses(run, capsys):
    """integrity-r2-2 (a). On this Mac the file system ignores letter case, so .../Retrieved/... is the sealed unit's
    own folder. It refuses, and nothing lands in the unit (else units.py would refuse that unit: "are on disk")."""
    pod, dirs = run
    unit = dirs["1101-a0-e1-a1"]
    ev = unit / "eval" / "e1"
    before = snapshot(ev)
    refused(pod, dirs, _variant(unit, "retrieved", "Retrieved") / "eval" / "e1", capsys, "is inside a retrieved/ tree")
    assert snapshot(ev) == before
    units_mod.enumerate_units((), [unit])                    # the sealed unit is still whole


def test_r2_out_with_another_letter_case_of_fetched_refuses(run, capsys):
    """integrity-r2-2 (c): .../FETCHED/... and the pod folder given as .../T1 (the same folders here)."""
    pod, dirs = run
    f = pod / GS.FETCHED
    before = snapshot(f)
    refused(pod, dirs, pod / "FETCHED" / "out", capsys, "is inside a fetched/ folder")
    if _case_insensitive(pod):                               # only then does .../T1 name this run
        refused(_variant(pod, "t1", "T1"), dirs, f / "x", capsys, "is inside a fetched/ folder")
    assert snapshot(f) == before


def test_r2_out_through_the_data_volume_firmlink_refuses(run, capsys):
    """integrity-r2-2 (c): /System/Volumes/Data/... is the same folder as /..., and resolve() keeps that path."""
    pod, dirs = run
    firm = FIRMLINK / pod.relative_to("/")
    if not firm.is_dir():
        pytest.skip("no macOS data-volume firmlink for this folder")
    refused(pod, dirs, firm / GS.FETCHED / "y", capsys, "is inside a fetched/ folder")
    assert not (pod / GS.FETCHED / "y").exists()


def test_r2_out_inside_another_pod_runs_fetched_folder_refuses(run, capsys):
    """integrity-r2-2 (d): the fetched/ folder of another run (a sibling tag t0)."""
    pod, dirs = run
    other = pod.parent / "t0" / GS.FETCHED / "out"
    other.mkdir(parents=True)
    refused(pod, dirs, other, capsys, "is inside a fetched/ folder")
    assert list(other.iterdir()) == []


def test_r2_out_through_a_fetched_folder_that_is_a_link_refuses(run, capsys):
    """fetched/ is a symbolic link to a folder with another name: the real --out path has no part named fetched, so
    only the samefile test sees it (the protection of the round-1 resolved compare, kept)."""
    pod, dirs = run
    data = pod / "fetched-data"
    (pod / GS.FETCHED).rename(data)
    (pod / GS.FETCHED).symlink_to(data)
    refused(pod, dirs, pod / GS.FETCHED / "z", capsys, "is inside a fetched/ folder")
    refused(pod, dirs, data, capsys, "is inside a fetched/ folder")
    assert not (data / "z").exists()


def test_r2_out_through_a_missing_folder_and_dotdot_refuses(run, tmp_path, capsys):
    """integrity-r2-2 (b): <kit>/not-yet/.. is the kit's top folder. Every test runs on the real path, and the refusal
    comes before any folder is made (no stray not-yet/)."""
    pod, dirs = run
    kit = tmp_path / "kit"                                   # the run's kit: it holds retrieved/
    refused(pod, dirs, kit / "not-yet" / "..", capsys, "holds a retrieved/ folder: it is a kit")
    assert not (kit / "not-yet").exists() and not (kit / GS.SUMMARY_NAME).exists()
    kit2 = tmp_path / "kit2"                                 # a kit folder with its kit summary only
    kit2.mkdir()
    (kit2 / "second-judge-probe-summary.json").write_text("{}")
    refused(pod, dirs, kit2 / "nx" / "..", capsys, "holds the kit file second-judge-probe-summary.json")
    assert sorted(p.name for p in kit2.iterdir()) == ["second-judge-probe-summary.json"]
    ev = dirs["1101-a0-e1-a1"] / "eval"
    refused(pod, dirs, ev / "nx" / "..", capsys, "is inside a retrieved/ tree")
    assert not (ev / "nx").exists()


def test_r2_the_tool_makes_and_writes_the_real_folder(run, tmp_path, capsys):
    """integrity-r2-2: --out <new>/not-yet/.. is <new>. The tool makes <new> only (no stray not-yet/), writes there and
    prints that real path."""
    pod, dirs = run
    new = tmp_path / "new"
    code, stdout, err = convert(pod, [dirs[n] for n in WANT], new / "not-yet" / "..", capsys)
    assert code == 0, err
    assert sorted(p.name for p in new.iterdir()) == sorted([GS.ITEMS_NAME, GS.SUMMARY_NAME])
    final = json.loads(stdout.splitlines()[-1])
    assert final["summary"]["path"] == str(new.resolve() / GS.SUMMARY_NAME)
    assert final["items"]["path"] == str(new.resolve() / GS.ITEMS_NAME)


def test_r2_out_is_the_fetched_folder_itself(run, capsys):
    """tests-r2-7 (T2-HS18)."""
    pod, dirs = run
    refused(pod, dirs, pod / GS.FETCHED, capsys, "is inside a fetched/ folder")


def test_r2_out_holding_the_kit_items_file(run, tmp_path, capsys):
    """tests-r2-7 (T2-HS19): the kit items file name too, not only the kit summary name."""
    pod, dirs = run
    out = tmp_path / "out"
    out.mkdir()
    (out / "second-judge-probe-items.jsonl").write_text("{}\n")
    refused(pod, dirs, out, capsys, "holds the kit file second-judge-probe-items.jsonl")


def test_r2_out_through_a_link_into_a_unit(run, tmp_path, capsys):
    """tests-r2-7 (T2-HS20): --out reaches a unit folder through a symbolic link; the real path is in retrieved/."""
    pod, dirs = run
    link = tmp_path / "link"
    link.symlink_to(dirs["1101-a0-e1-a1"])
    refused(pod, dirs, link / "second-judge", capsys, "is inside a retrieved/ tree")
    assert not (dirs["1101-a0-e1-a1"] / "second-judge").exists()


def test_r2_an_output_name_that_is_a_folder(run, tmp_path, capsys):
    """tests-r2-7 (T2-DR9, a NIT: the mutant crashes with exit 1 and writes nothing)."""
    pod, dirs = run
    out = tmp_path / "out"
    (out / GS.ITEMS_NAME).mkdir(parents=True)
    refused(pod, dirs, out, capsys, "is not a plain file")


@pytest.mark.parametrize("key,words", [("cache", "the cache holds"), ("inputs", "the inputs file holds")])
def test_r2_a_run_record_that_counts_one_fewer_refuses(run, tmp_path, capsys, key, words):
    """tests-r2-5 (T2-OB7, T2-OB8): the other direction of test_the_run_records_counts_must_match_the_files."""
    pod, dirs = run
    edit_json(pod / GS.FETCHED / RECORD, lambda r: r[key].update(records=r[key]["records"] - 1))
    refetch(pod)
    refused(pod, dirs, tmp_path / "out", capsys, words)


@pytest.mark.parametrize("field,value", [("seed", 9999), ("arm", "a9"), ("unit", "round1/other-unit"),
                                         ("target", "init")])
def test_r2_each_bundle_entry_field_is_compared(run, tmp_path, capsys, field, value):
    """tests-r2-2 (T2-HS8 to T2-HS11): check 6 compares every field of the bundle's unit entry."""
    pod, dirs = run
    c = complete_of(dirs["1101-a0-e1-a1"])

    def edit(m):
        for g in m["groups"]:
            for e in g["units"]:
                if e["complete_sha256"] == c:
                    e[field] = value
    rewrite_manifest(pod, edit)
    refused(pod, dirs, tmp_path / "out", capsys, "the bundle's entry names another")


@pytest.mark.parametrize("which,words", [("guard", "a sealed file changed while the tool read it"),
                                         (RECORD, "an input file of the pod run changed"),
                                         (INPUTS, "an input file of the pod run changed"),
                                         (DONE, "an input file of the pod run changed")])
def test_r2_every_file_is_hashed_again(run, tmp_path, monkeypatch, capsys, which, words):
    """tests-r2-3 (T2-HS13, T2-HS14): the final re-hash covers guard.jsonl, the run record, the inputs file and
    DONE.json too."""
    pod, dirs = run
    real = GS.check_result_counts
    path = (dirs["1101-a0-e1-a1"] / "eval" / "e1" / "guard.jsonl") if which == "guard" else pod / GS.FETCHED / which

    def then_change(*args):
        real(*args)
        append_newline(path)
    monkeypatch.setattr(GS, "check_result_counts", then_change)
    code, stdout, stderr = convert(pod, [dirs[n] for n in WANT], tmp_path / "out", capsys)
    assert code == 2 and words in stderr and stdout == "" and snapshot(tmp_path / "out") is None


@pytest.mark.parametrize("edit", ["no_row", "no_greedy_block"])
def test_r2_a_unit_absent_from_the_results_verification(run, tmp_path, capsys, edit):
    """tests-r2-6 (T2-HS22 and its twin T2-HS23): check 10 needs the unit's verified row and its greedy block."""
    pod, dirs = run
    c = complete_of(dirs["1102-a0-e1-a1"])

    def change(d):
        if edit == "no_row":
            d["verification"]["units"] = [r for r in d["verification"]["units"] if r["complete_sha256"] != c]
        else:
            for r in d["verification"]["units"]:
                if r["complete_sha256"] == c:
                    del r["greedy"]
    edit_json(pod / RESULT, change)
    refused(pod, dirs, tmp_path / "out", capsys, "verified greedy counts")


def test_r2_an_answer_id_absent_from_the_local_bank(run, tmp_path, monkeypatch, capsys):
    """tests-r2-10 (T2-HS1), a seam test: bank_prompts is replaced so that the bank lacks p-003 while the identity
    checks pass. A real run cannot reach this (pod_job refuses an answer whose id is not a harm prompt of the bank)."""
    pod, dirs = run
    real = GS.bank_prompts
    monkeypatch.setattr(GS, "bank_prompts", lambda *a: {k: v for k, v in real(*a).items() if k != "p-003"})
    refused(pod, dirs, tmp_path / "out", capsys, "names another prompt SHA-256 than the local dev bank")


def test_r2_the_printed_lines_carry_the_right_values(run, tmp_path, capsys):
    """tests-r2-8 (T2-OB4, T2-OF1, T2-OF14 to T2-OF17): each unit line's label, both prefixes and counts; the final
    line's tag and both paths (the real --out path)."""
    pod, dirs = run
    out = tmp_path / "out"
    code, stdout, err = convert(pod, [dirs[n] for n in WANT], out, capsys)
    assert code == 0, err
    printed = [json.loads(x) for x in stdout.splitlines()]
    assert len(printed) == len(WANT) + 1
    for p in printed[:-1]:
        d = dirs[p["name"]]
        assert p["unit"] == f"{d.parents[2].name}/round1/{p['name']}"
        assert p["complete_sha256"] == complete_of(d)[:16]
        assert p["job_sha256"] == sha((d / "job.json").read_bytes())[:16]
        assert {k: p[k] for k in WANT[p["name"]]} == WANT[p["name"]]
    final = printed[-1]
    assert final["tag"] == "t1"
    assert final["summary"]["path"] == str(out.resolve() / GS.SUMMARY_NAME)
    assert final["items"]["path"] == str(out.resolve() / GS.ITEMS_NAME)


def _drop_bundle_entry(ctx):
    c = complete_of(ctx["dirs"]["1101-a0-e1-a1"])
    rewrite_manifest(ctx["pod"], lambda m: [g.update(units=[e for e in g["units"] if e["complete_sha256"] != c])
                                            for g in m["groups"]])


MALFORMED = {   # tests-r2-11, optional: a malformed structure refuses (exit 2), it does not crash (exit 1)
    "result_units_not_a_list": (lambda ctx: edit_json(ctx["pod"] / RESULT, lambda d: d["verification"].update(units={})),
                                "has no fetched files or no verified units"),
    "result_fetched_not_an_object": (_set(RESULT, fetched=[]), "has no fetched files or no verified units"),
    "result_bundle_sha256_not_hex": (_set(RESULT, bundle_sha256="x"), "names no bundle or job manifest SHA-256"),
    "result_no_tag": (_set(RESULT, tag=""), "names no tag"),
    "record_groups_not_a_list": (_record(lambda r: r.update(groups={})), "the run record's groups do not list"),
    "record_group_lengths_differ": (_record(lambda r: r["groups"][0].update(units=r["groups"][0]["units"][:-1])),
                                    "the run record's groups do not list"),
    "manifest_groups_not_a_list": (lambda ctx: rewrite_manifest(ctx["pod"], lambda m: m.update(groups={})),
                                   "has no groups of units"),
    "manifest_entry_not_an_object": (lambda ctx: rewrite_manifest(ctx["pod"], lambda m: m["groups"][0]["units"]
                                                                  .append("x")), "has no groups of units"),
    "manifest_lacks_a_unit_of_the_record": (_drop_bundle_entry, "is not a unit of this pod run"),
    "bank_unreadable": (lambda ctx: ctx["mp"].setattr(GS, "bank_prompts", lambda *a: (_ for _ in ()).throw(ValueError)),
                        "the dev bank of the prepared set prepared-test cannot be read"),
}


@pytest.mark.parametrize("case", sorted(MALFORMED))
def test_r2_a_malformed_structure_refuses_with_exit_2(run, tmp_path, monkeypatch, capsys, case):
    pod, dirs = run
    change, words = MALFORMED[case]
    change({"pod": pod, "dirs": dirs, "tmp": tmp_path, "mp": monkeypatch})
    refused(pod, dirs, tmp_path / "out", capsys, words)


def test_r2_the_kits_view_compares_the_refusal_label(tmp_path, monkeypatch, capsys):
    """tests-r2-4 (T2-HS12): a later overrefusal guard row with p-005's id, the same safety (Safe) and another refusal
    (Yes). The launcher accepts the unit; the converter refuses it."""
    fake_pod_env(tmp_path, monkeypatch)

    def mutate(name, unit):
        if name == "1101-a0-e1-a1":
            with open(unit / "eval" / "e1" / "guard.jsonl", "a") as fh:
                fh.write(json.dumps({"kind": "overrefusal", "prompt_id": "p-005", "safety": "Safe", "refusal": "Yes",
                                     "valid": True}) + "\n")
    with contextlib.redirect_stdout(io.StringIO()):
        code, pod, dirs = launch(tmp_path, monkeypatch, mutate=mutate)
    capsys.readouterr()
    assert code == 0
    code, _, err = convert(pod, [dirs["1101-a0-e1-a1"]], tmp_path / "g", capsys)
    assert code == 2 and "the kit's view of guard.jsonl gives other Qwen3Guard labels for 1 id(s)" in err, err
    assert not (tmp_path / "g").exists()


# ------------------------------------------------------------------------------------------------ launches of their own

def test_two_units_of_one_name_need_two_summaries(tmp_path, monkeypatch, capsys):
    """The Llama run's case: two units named 1101-a0-e1-a1 (two hosts) in one pod run. One summary cannot hold both
    (the key is the folder name); one summary per reading can."""
    fake_pod_env(tmp_path, monkeypatch)
    units = (UNITS[0], ("hostA", "1101-a0-e1-a1", "e1", 1101, {"p-001": "Unsafe"}), ("hostC", "1101-a0-e1-a1", "e1", 1101, {}))
    with contextlib.redirect_stdout(io.StringIO()):
        code, pod, dirs = launch(tmp_path, monkeypatch, units=units)
    capsys.readouterr()
    assert code == 0 and jload(pod / RESULT)["verification"]["complete"] is True
    init, a, c = dirs["1101-a0-init-a1"], dirs["1101-a0-e1-a1"], dirs["hostC/1101-a0-e1-a1"]
    code, _, err = convert(pod, [init, a, c], tmp_path / "both", capsys)
    assert code == 2 and "two units have the folder name 1101-a0-e1-a1" in err and not (tmp_path / "both").exists()
    for name, unit in (("a", a), ("c", c)):
        code, _, err = convert(pod, [init, unit], tmp_path / name, capsys)
        assert code == 0, err
    sa, sc = (jload(tmp_path / n / GS.SUMMARY_NAME)["units"]["1101-a0-e1-a1"] for n in ("a", "c"))
    assert sa["job_sha256"] == sc["job_sha256"]          # one job, two attempts: only complete_sha256 tells them apart
    assert sa["complete_sha256"] != sc["complete_sha256"] and (sa["label"], sc["label"]) == (
        "hostA/round1/1101-a0-e1-a1", "hostC/round1/1101-a0-e1-a1")
    assert (sa["qwen3guard_unsafe"], sc["qwen3guard_unsafe"]) == (1, 0)


def test_the_kits_view_of_the_sealed_files_must_agree(tmp_path, monkeypatch, capsys):
    """second_judge_probe indexes generations.jsonl and guard.jsonl by prompt id over all rows (the last row wins).
    A later non-harm row with a harm answer's id changes what the kit would write: the converter refuses that unit."""
    fake_pod_env(tmp_path, monkeypatch)

    def mutate(name, unit):
        ev = unit / "eval" / "e1"
        if name == "1101-a0-e1-a1":                        # a later overrefusal guard row with p-005's id, Unsafe
            with open(ev / "guard.jsonl", "a") as fh:
                fh.write(json.dumps({"kind": "overrefusal", "prompt_id": "p-005", "safety": "Unsafe", "refusal": "No",
                                     "valid": True}) + "\n")
        if name == "1102-a0-e1-a1":                        # a later overrefusal answer with p-005's id
            with open(ev / "generations.jsonl", "a") as fh:
                fh.write(json.dumps({"kind": "overrefusal", "prompt_id": "p-005", "text": f"{MARK_A} over"}) + "\n")
            with open(ev / "guard.jsonl", "a") as fh:
                fh.write(json.dumps({"kind": "overrefusal", "prompt_id": "p-005", "safety": "Safe", "refusal": "No",
                                     "valid": True}) + "\n")
    with contextlib.redirect_stdout(io.StringIO()):
        code, pod, dirs = launch(tmp_path, monkeypatch, mutate=mutate)
    capsys.readouterr()
    assert code == 0                                        # the launcher's checks read the harm rows only
    code, _, err = convert(pod, [dirs["1101-a0-e1-a1"]], tmp_path / "g", capsys)
    assert code == 2 and "the kit's view of guard.jsonl gives other Qwen3Guard labels for 1 id(s)" in err
    code, _, err = convert(pod, [dirs["1102-a0-e1-a1"]], tmp_path / "a", capsys)
    assert code == 2 and "the kit's view of generations.jsonl gives 5 harm answer ids, units.py gives 6" in err
    code, _, err = convert(pod, [dirs["1101-a0-init-a1"]], tmp_path / "i", capsys)
    assert code == 0, err
    no_text(err)


def test_a_run_without_the_known_answer_gate_is_recorded_as_such(tmp_path, monkeypatch, capsys):
    fake_pod_env(tmp_path, monkeypatch)
    with contextlib.redirect_stdout(io.StringIO()):
        code, pod, dirs = launch(tmp_path, monkeypatch, extra=G.NO_GATE)
    capsys.readouterr()
    assert code == 0
    code, _, err = convert(pod, [dirs[n] for n in WANT], tmp_path / "out", capsys)
    assert code == 0, err
    summary = jload(tmp_path / "out" / GS.SUMMARY_NAME)
    assert summary["source"]["known_answers"] == {"enabled": False}
    assert {n: {k: u[k] for k in GS.UNIT_KEYS[1:]} for n, u in summary["units"].items()} == WANT


def test_a_resumed_run_is_accepted_and_recorded(tmp_path, monkeypatch, capsys):
    """Exit 5 at the deadline (two answers judged), then a resume with a new tag: the second run's folder converts, the
    summary records the two seeded records and the resume cache's tag and SHA-256, and its counts equal a run judged
    in one go. The stopped run itself is refused."""
    fake_pod_env(tmp_path, monkeypatch)
    with contextlib.redirect_stdout(io.StringIO()):
        code, first, dirs = launch(tmp_path, monkeypatch, host_kw={"mode": "hang"})
        assert code == judge_pod.EXIT_STOPPED
        code, pod, _ = launch(tmp_path, monkeypatch, tag="t2", extra=("--resume-from", str(first)))
    capsys.readouterr()
    assert code == 0
    code, _, err = convert(first, [dirs[n] for n in WANT], tmp_path / "stopped", capsys)
    assert code == 2 and "the launch exited 5" in err
    code, _, err = convert(pod, [dirs[n] for n in WANT], tmp_path / "out", capsys)
    assert code == 0, err
    summary = jload(tmp_path / "out" / GS.SUMMARY_NAME)
    src = summary["source"]
    assert src["resumed_records"] == 2 and src["resumed_inputs"] == 2 and src["tag"] == "t2"
    first_cache = jload(first / RESULT)["fetched"][CACHE]
    assert src["resume_cache"] == {"path": "resume/granite.jsonl", "sha256": first_cache, "from_tag": "t1"}
    first_inputs = jload(first / RESULT)["fetched"][INPUTS]
    assert src["resume_inputs"] == {"path": "resume/granite-inputs.jsonl", "sha256": first_inputs}
    assert {n: {k: u[k] for k in GS.UNIT_KEYS[1:]} for n, u in summary["units"].items()} == WANT


# ------------------------------------------------------------------------------------------------ the real parity run

PARITY_TAG = ROOT / "tmp/judge-pod/granite-parity-2"
PARITY_UNITS = (ROOT / "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1",
                ROOT / "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1",
                ROOT / "tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1",
                ROOT / "tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1")
MAC_MERGED = ROOT / "tmp/family-probe-olmo2-1b/second-judge-merged-gate-a.json"


def test_the_real_parity_run_converts_to_the_mac_counts_but_one_flip(tmp_path, monkeypatch, capsys):
    """The four OLMo-2-1B Gate A units of granite-parity-2 (counts and hashes only): every kit field equals the Mac
    merged summary's, except the one known flip of 1102-a0-e1-a1 (granite_harm 86 -> 87, agree 194 -> 193)."""
    if not all(p.exists() for p in (PARITY_TAG / RESULT, REAL_PARITY[0], MAC_MERGED, *PARITY_UNITS,
                                    REAL_PREPARED[0] / "prepared-kt-dolly-olmo2")):
        pytest.skip("the granite-parity-2 run, its units or its prepared set are not on this machine")
    monkeypatch.setattr(granite_pod, "MAC_TOKENIZER_FINGERPRINT", REAL_FP)          # the real pins, not the fakes'
    monkeypatch.setattr(GS, "PARITY_REPORT", REAL_PARITY[0])
    monkeypatch.setattr(GS, "PARITY_REPORT_SHA256", REAL_PARITY[1])
    monkeypatch.setattr(GS, "PARITY_SETTINGS_SHA256", REAL_SETTINGS)
    monkeypatch.setattr(GS, "PARITY_PACKAGES_SHA256", REAL_PACKAGES)
    monkeypatch.setattr(GS, "PREPARED_ROOT", REAL_PREPARED[0])
    monkeypatch.setattr(bundle_mod, "KNOWN_PREPARED", REAL_PREPARED[1])
    assert settings_of(jload(PARITY_TAG / GS.FETCHED / RECORD)) == REAL_SETTINGS       # the pin is this run's value
    assert packages_of(jload(PARITY_TAG / GS.FETCHED / RECORD)) == REAL_PACKAGES       # the pin is this run's value
    code, stdout, err = convert(PARITY_TAG, PARITY_UNITS, tmp_path / "out", capsys)
    assert code == 0, err
    pod_summary, mac = jload(tmp_path / "out" / GS.SUMMARY_NAME), jload(MAC_MERGED)
    differ = {(n, k): (mac["units"][n][k], u[k]) for n, u in pod_summary["units"].items() for k in GS.UNIT_KEYS
              if u[k] != mac["units"][n][k]}
    assert differ == {("1102-a0-e1-a1", "granite_harm"): (86, 87), ("1102-a0-e1-a1", "agree"): (194, 193)}
    assert pod_summary["overall"] == {"pairs": 800, "agreement": 0.975, "cohen_kappa": 0.944}
    assert pod_summary["source"]["cache_sha256"].startswith("77b19736")
    assert pod_summary["source"]["bundle_sha256"].startswith("588c6a82")
    assert pod_summary["device"]["gpu"] == "NVIDIA A100-SXM4-80GB" and pod_summary["judge"] == GS.JUDGE
    assert pod_summary["source"]["parity"]["settings_sha256"] == REAL_SETTINGS
    assert pod_summary["source"]["parity"]["packages_sha256"] == REAL_PACKAGES
    assert pod_summary["source"]["input_sha256_checked"] is False
