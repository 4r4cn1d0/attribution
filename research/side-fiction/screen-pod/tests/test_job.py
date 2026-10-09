"""screen_job.py on an unpacked real bundle: the lead's REAL Granite pod job (pod_job.py run: its known-answer gate,
run record and job.log) on the bundle's gate_b, the screen's ka step reading it, both judges (the lead's real
GraniteSession behind a fake model; a fake GuardScorer), resume, SIGTERM, the records, and the status and sums
whitelists (no model, no GPU)."""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import tarfile

import pytest
from conftest import (P, R, SB, SJ, SP, FakeGranite, FakeGuard, StampClock, ka_label_map, needs_real, run_lead_gate,
                      sha, text_samples, assert_no_text)
import granite_pod
import judging


@pytest.fixture(scope="module")
def small_bundle(tmp_path_factory):
    """One real round-1 bundle with --limit 3 (3 rows of each source), unpacked once."""
    if not __import__("conftest").REAL_INPUTS:
        pytest.skip("the real inputs are not on this machine")
    base = tmp_path_factory.mktemp("small-bundle")
    with contextlib.redirect_stdout(io.StringIO()):
        assert SP.main(["bundle", "--tag", "sp-job", "--round", "1", "--limit", "3", "--out", str(base / "dry")]) == 0
    with tarfile.open(base / "dry" / "bundle.tar.gz") as t:
        t.extractall(base / "pod", filter="data")
    return base / "pod" / "bundle"


@pytest.fixture
def remote(small_bundle, tmp_path):
    root = tmp_path / "remote"
    shutil.copytree(small_bundle, root / "bundle")
    (root / "out").mkdir()
    return root


def job(argv, granite=None, guard=None):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = SJ.main(argv, judge_factory=granite, guard_factory=guard)
    return code, out.getvalue(), err.getvalue()


def ka(remote, granite_exit):
    return job(["ka", "--bundle", str(remote / "bundle"), "--granite-root", str(remote / "granite-job"),
                "--granite-exit", str(granite_exit), "--record", str(remote / "out/ka.json")])


def granite(remote, fake):
    return job(["granite", "--bundle", str(remote / "bundle"), "--ka", str(remote / "out/ka.json"), "--cache",
                str(remote / "out/granite.jsonl"), "--record", str(remote / "out/granite-record.json")],
               granite=lambda: fake.session(remote / "bundle/gate_b"))


def qwen(remote, guard):
    return job(["qwen", "--bundle", str(remote / "bundle"), "--ka", str(remote / "out/ka.json"), "--cache",
                str(remote / "out/qwen.jsonl"), "--record", str(remote / "out/qwen-record.json")],
               guard=lambda: guard)


def ka_record(remote) -> dict:
    return json.loads((remote / "out/ka.json").read_bytes())


def passed_gate(remote) -> FakeGranite:
    fake = FakeGranite(ka_label_map(remote / "bundle"))
    assert run_lead_gate(remote, fake) == 0 and ka(remote, 0)[0] == 0
    return fake


@needs_real
def test_the_lead_gate_passes_then_both_judges(remote):
    fake = FakeGranite(ka_label_map(remote / "bundle"))
    assert run_lead_gate(remote, fake) == 0
    lead = json.loads((remote / "granite-job/out/run-record.json").read_bytes())
    assert lead["known_answers"]["passed"] is True and lead["exit"] == 0 and lead["groups"] == []
    assert fake.calls == 200 and {c for c, *_ in fake.seen} == {"harm"} and fake.loads == 1   # the lead's gate only
    code, out, err = ka(remote, 0)
    assert code == 0, err
    rec = ka_record(remote)
    block = rec["known_answers"]
    assert rec["passed"] is True and rec["too_slow"] is False and rec["refused"] is None and rec["error"] is None
    assert (block["identical"], block["pod_yes"], block["mac_yes"], block["judged"]) == (200, 93, 93, 200)
    assert block == lead["known_answers"] and rec["lead"]["exit"] == 0 and rec["lead"]["done"]["step"] == "done"
    assert rec["lead"]["run_record_sha256"] == sha((remote / "granite-job/out/run-record.json").read_bytes())
    assert rec["timing"]["seconds_per_item"] is not None and rec["timing"]["problem"] is None
    assert rec["rule"] == R.KA_RULE and "190" in rec["rule"] and "<= 5" in rec["rule"]
    g = FakeGranite(ka_label_map(remote / "bundle"))
    code, out, err = granite(remote, g)
    assert code == 0, err
    cache = R.JsonlCache(remote / "out/granite.jsonl", R.check_granite, R.granite_key)
    assert len(cache) == 12 and {k[0] for k in cache.entries} == {"dark-1", "dark-2", "dark-3", "light-1", "light-2",
                                                                  "light-3"}
    assert [c for c, *_ in g.seen] == ["harm", "sexual_content"] * 6 and g.loads == 1 and g.checks == 1
    assert all(len(e["input_sha256"]) == 64 for e in cache.entries.values())
    grec = json.loads((remote / "out/granite-record.json").read_bytes())
    assert grec["ka_passed"] is True and grec["limit"] == 3 and set(grec["counts"]) == {"dark", "light"}
    guard = FakeGuard()
    code, out, err = qwen(remote, guard)
    assert code == 0, err
    qcache = R.JsonlCache(remote / "out/qwen.jsonl", R.check_qwen, R.qwen_key)
    assert len(qcache) == 9 and {e["source"] for e in qcache.entries.values()} == {"dark", "light", "dolly"}
    rows = {r.row_id: r for rows in SB.pod_sources(remote / "bundle", SB.verify_bundle(remote / "bundle")).values()
            for r in rows}
    for item_id, user_sha, response_sha in guard.items:                  # the guard got the screen's user turn
        assert (user_sha, response_sha) == (sha(rows[item_id].user_turn), sha(rows[item_id].assistant_turn))
    blobs = [out, err, *(p.read_bytes() for p in (remote / "out").iterdir() if p.is_file()),
             *(p.read_bytes() for p in (remote / "granite-job/out").iterdir() if p.is_file())]
    assert_no_text(blobs, text_samples())


@needs_real
def test_a_failed_gate_exits_4_and_no_row_is_screened(remote):
    labels = ka_label_map(remote / "bundle")
    flip = sorted(k for k, lab in labels.items() if lab == "no")[:11]             # 189 identical, delta +11
    assert run_lead_gate(remote, FakeGranite(labels, flip=flip)) == P.LEAD_EXIT_GATE_FAILED
    code, _, err = ka(remote, P.LEAD_EXIT_GATE_FAILED)
    assert code == P.POD_EXIT_KA_FAILED, err
    rec = ka_record(remote)
    assert rec["passed"] is False and rec["known_answers"]["identical"] == 189 and rec["known_answers"]["delta_yes"] == 11
    g = FakeGranite(labels)
    code, _, err = granite(remote, g)
    assert code == P.POD_EXIT_REFUSED and g.calls == 0 and not (remote / "out/granite.jsonl").exists()
    guard = FakeGuard()
    assert qwen(remote, guard)[0] == P.POD_EXIT_REFUSED and guard.items == []
    forged = {**rec, "passed": True, "too_slow": False, "known_answers": {**rec["known_answers"], "passed": True}}
    (remote / "out/ka.json").write_text(json.dumps(forged))                     # a forged pass: its counts fail
    assert granite(remote, g)[0] == P.POD_EXIT_REFUSED and g.calls == 0
    counts = {**rec["known_answers"], "passed": True, "identical": 200, "delta_yes": 0, "pod_yes": 93}
    (remote / "out/ka.json").write_text(json.dumps({**forged, "known_answers": counts}))   # passing counts, failing ids
    code, _, err = granite(remote, g)
    assert code == P.POD_EXIT_REFUSED and g.calls == 0 and "recount" in err


@needs_real
@pytest.mark.parametrize("fail_step,fail_code,code", [("pip", 1, 1), ("pip", 3, 1), ("llama", 2, 2),
                                                     ("download", 124, 1)])
def test_a_lead_job_that_ends_before_its_gate_is_recorded_not_a_failed_gate(remote, fail_step, fail_code, code):
    assert run_lead_gate(remote, FakeGranite(), fail_step=fail_step, fail_code=fail_code) == fail_code
    got, _, err = ka(remote, fail_code)
    assert got == code, err
    rec = ka_record(remote)                         # pip's own exit 3 is not the gate's: no verdict before "run"
    assert rec["passed"] is False and rec["known_answers"] is None and rec["lead"]["exit"] == fail_code
    assert rec["lead_verdict"] is False and rec["refused"] is None
    assert rec["lead"]["done"] == {"exit": fail_code, "step": fail_step, "utc": "2026-10-09T00:00:00Z"}
    g = FakeGranite()
    assert granite(remote, g)[0] == P.POD_EXIT_REFUSED and g.calls == 0


@needs_real
def test_a_sigterm_during_the_lead_gate_is_exit_5_and_writes_nothing(remote):
    fake = FakeGranite(ka_label_map(remote / "bundle"), sigterm_at=50)
    assert run_lead_gate(remote, fake) == P.POD_EXIT_STOPPED
    assert 50 <= fake.calls < 200
    code, _, err = ka(remote, P.POD_EXIT_STOPPED)
    assert code == P.POD_EXIT_STOPPED, err
    rec = ka_record(remote)
    assert rec["stopped"] is True and rec["passed"] is False and rec["known_answers"]["stopped"] is True
    assert not (remote / "granite-job/out/granite-pod.jsonl").exists()


@needs_real
def test_a_lead_record_that_contradicts_the_exit_or_the_bundle_is_refused(remote):
    passed_gate(remote)
    assert ka(remote, P.LEAD_EXIT_GATE_FAILED)[0] == P.POD_EXIT_ERROR         # exit 3, but DONE.json says done: no verdict
    assert ka_record(remote)["lead_verdict"] is False
    done = remote / "granite-job/DONE.json"
    done_text = done.read_text()
    done.write_text(json.dumps({"exit": 3, "step": "run", "utc": "2026-10-09T00:00:00Z"}))
    code, _, err = ka(remote, P.LEAD_EXIT_GATE_FAILED)                         # a verdict of 3 over a passing record
    assert code == P.POD_EXIT_REFUSED and "this exit" in err
    done.write_text(done_text)
    path = remote / "granite-job/out/run-record.json"
    rec = json.loads(path.read_bytes())
    path.write_text(json.dumps({**rec, "bundle_manifest_sha256": "0" * 64}))
    code, _, err = ka(remote, 0)
    assert code == P.POD_EXIT_REFUSED and "gate_b" in err
    path.write_text(json.dumps({**rec, "known_answers": {**rec["known_answers"], "reference_sha256": "0" * 64}}))
    assert ka(remote, 0)[0] == P.POD_EXIT_REFUSED
    path.unlink()
    assert ka(remote, 0)[0] == P.POD_EXIT_REFUSED


def _set_ratio(remote, ratio: float, ka_mean: float = 421.3) -> None:
    """Gives the unpacked bundle's manifest a token block with ratio r (the means consistent with it)."""
    path = remote / "bundle/job-manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["granite_tokens"].update(ratio=ratio, ka_mean_tokens=ka_mean,
                                      fiction_mean_tokens_per_call=round(ratio * ka_mean, 3))
    path.write_bytes(SJ.canonical_bytes(manifest))


@needs_real
@pytest.mark.parametrize("s_per_item,code", [(0.80, 0), (1.0, 3)])
def test_the_gate_speed_is_projected_by_the_token_ratio(remote, monkeypatch, s_per_item, code):
    """r = 0.47: the gate at 0.80 s per answer (measured from the lead's job.log stamps) projects to 0.376 s per fiction
    call (under 0.4: the run goes on); at 1.0 s to 0.47 s (above 0.4: exit 3, the pass recorded, granite refuses)."""
    clock = StampClock()
    monkeypatch.setattr(judging, "utc", clock)                     # the lead's log stamps follow the fake model
    labels = ka_label_map(remote / "bundle")
    _set_ratio(remote, 0.47)
    assert run_lead_gate(remote, FakeGranite(labels, clock=clock, s_per_call=s_per_item)) == 0
    assert ka(remote, 0)[0] == code
    rec = ka_record(remote)
    speed, timing = rec["speed"], rec["timing"]
    assert rec["passed"] is True and rec["too_slow"] is (code == 3) and speed["too_slow"] is (code == 3)
    assert timing["judged"] == 200 and timing["problem"] is None              # stamps to the second (truncated)
    assert timing["seconds"] in (round(200 * s_per_item) - 1, round(200 * s_per_item))
    assert speed["ratio"] == 0.47 and speed["seconds_per_item"] == pytest.approx(s_per_item, abs=0.006)
    assert speed["projected_s_per_call"] == pytest.approx(round(speed["seconds_per_item"] * 0.47, 4))
    assert speed["ka_mean_tokens"] == 421.3 and speed["fiction_mean_tokens_per_call"] == round(0.47 * 421.3, 3)
    assert speed["planned_s_per_call"] == 0.4 and isinstance(timing["ka_input_tokens_max_pod"], int)
    calls = json.loads((remote / "bundle/job-manifest.json").read_bytes())["granite_tokens"]["fiction_calls"]
    assert speed["granite_calls"] == calls == 12                                         # 6 rows x 2 (limit 3)
    assert speed["projected_granite_minutes"] == round(speed["seconds_per_item"] * 0.47 * calls / 60, 1)
    g = FakeGranite(labels)
    assert granite(remote, g)[0] == (P.POD_EXIT_REFUSED if code == 3 else 0)
    assert (g.calls == 0) is (code == 3)


@needs_real
def test_an_untimed_gate_never_passes_the_speed_stop(remote):
    passed_gate(remote)
    log = remote / "granite-job/out/job.log"
    log.write_bytes(b"\n".join(x for x in log.read_bytes().split(b"\n") if b'"granite_precheck"' not in x) + b"\n")
    assert ka(remote, 0)[0] == P.POD_EXIT_TOO_SLOW
    rec = ka_record(remote)
    assert rec["passed"] is True and rec["too_slow"] is True and rec["timing"]["problem"]


def test_gate_timing_reads_the_leads_stamps(tmp_path):
    def line(event, t, **kw):
        return json.dumps({"utc": f"2026-10-09T10:{t // 60:02d}:{t % 60:02d}Z", "event": event, **kw})
    good = [line("llama", 0), line("known_answers", 5, items=200, judged=0),
            line("granite_precheck", 20, items=200, trimmed=0, input_tokens_max=3200, limit=8160), "not json",
            line("known_answers", 110, items=200, judged=200, passed=True), line("run_record", 111, exit=0)]
    path = tmp_path / "job.log"
    path.write_text("\n".join(good) + "\n")
    t = SJ.gate_timing(path, 200)
    assert (t["seconds"], t["seconds_per_item"], t["ka_input_tokens_max_pod"], t["problem"]) == (90.0, 0.45, 3200, None)
    for broken in (good[:2] + good[3:], [good[0], good[2], good[4]], good[:3]):          # no precheck, no start, no end
        path.write_text("\n".join(broken) + "\n")
        assert SJ.gate_timing(path, 200)["seconds_per_item"] is None
    path.write_text("\n".join([good[1], line("granite_precheck", 20, items=7), good[4]]) + "\n")
    assert SJ.gate_timing(path, 200)["problem"]                                          # not the gate's 200 answers
    assert SJ.gate_timing(tmp_path / "absent.log", 200)["problem"] == "no job.log"


@needs_real
def test_the_granite_step_checks_packages_and_gpu_offload_before_any_row(remote, monkeypatch):
    passed_gate(remote)
    made = []

    class Recorder:
        def __init__(self, tok_dir, gguf, **kw):
            made.append((tok_dir, gguf, kw))
            raise SJ.Refusal("recorded, not judged")
    monkeypatch.setattr(granite_pod, "GraniteSession", Recorder)
    monkeypatch.setattr(granite_pod, "require_granite_packages", lambda: {"llama_cpp_python": "0.3.36"})
    monkeypatch.setattr(granite_pod, "llama_info", lambda: {"llama_cpp_python": "0.3.36", "gpu_offload": False})
    argv = ["granite", "--bundle", str(remote / "bundle"), "--ka", str(remote / "out/ka.json"), "--cache",
            str(remote / "out/granite.jsonl"), "--record", str(remote / "out/granite-record.json")]
    code, _, err = job(argv)
    assert code == P.POD_EXIT_REFUSED and "GPU" in err and made == []
    assert not (remote / "out/granite.jsonl").exists()

    def missing():
        raise SJ.Refusal("package transformers is not installed")
    monkeypatch.setattr(granite_pod, "require_granite_packages", missing)
    assert job(argv)[0] == P.POD_EXIT_REFUSED and made == []
    monkeypatch.setattr(granite_pod, "require_granite_packages", lambda: {"llama_cpp_python": "0.3.36"})
    monkeypatch.setattr(granite_pod, "llama_info", lambda: {"llama_cpp_python": "0.3.36", "gpu_offload": True})
    code, _, err = job(argv)
    assert code == P.POD_EXIT_REFUSED and "recorded, not judged" in err
    ((tok_dir, gguf, kw),) = made                                  # the bundle's tokenizer, the pod's GGUF, the Mac's fp
    assert tok_dir == remote / "bundle/gate_b/granite-tokenizer" and gguf == granite_pod.POD_GGUF
    assert kw == {"require_fingerprint": granite_pod.MAC_TOKENIZER_FINGERPRINT}


@needs_real
def test_sigterm_stops_with_exit_5_and_the_next_run_resumes(remote):
    labels = ka_label_map(remote / "bundle")
    passed_gate(remote)
    code, _, _ = granite(remote, FakeGranite(labels, stop_after=5))
    assert code == P.POD_EXIT_STOPPED
    rec = json.loads((remote / "out/granite-record.json").read_bytes())
    assert rec["result"]["stopped"] is True and rec["result"]["judged"] == 5
    g = FakeGranite(labels)
    assert granite(remote, g)[0] == 0 and g.calls == 7
    assert len(R.JsonlCache(remote / "out/granite.jsonl", R.check_granite, R.granite_key)) == 12
    code, _, _ = qwen(remote, FakeGuard(stop_after=1))
    assert code == P.POD_EXIT_STOPPED                                         # the whole chunk is dropped
    assert not (remote / "out/qwen.jsonl").exists() or len(
        R.JsonlCache(remote / "out/qwen.jsonl", R.check_qwen, R.qwen_key)) == 0
    assert qwen(remote, FakeGuard())[0] == 0


@needs_real
def test_a_judge_that_raises_is_recorded_as_an_error(remote):
    passed_gate(remote)
    rows = SB.pod_sources(remote / "bundle", SB.verify_bundle(remote / "bundle"))
    code, _, err = granite(remote, FakeGranite(raise_on={rows["dark"][1].response_sha256}))
    assert code == P.POD_EXIT_ERROR
    assert json.loads((remote / "out/granite-record.json").read_bytes())["error"] == "MemoryError"
    assert len(R.JsonlCache(remote / "out/granite.jsonl", R.check_granite, R.granite_key)) == 2   # dark-1 only


@needs_real
def test_record_status_and_sums_print_whitelisted_counts_only(remote):
    passed_gate(remote)
    (remote / "out/job.log").write_text("\n".join([
        json.dumps({"event": "progress", "step": "granite", "judged": 4, "of": 12, "eta_min": 1.0,
                    "text": "FICTIONRESP leak", "sec_per_item": 0.2}),
        "Traceback (most recent call last): FICTIONCTX in a traceback line"]) + "\n")
    (remote / "STEP").write_text("granite\n")
    code, out, _ = job(["status", "--root", str(remote)])
    st = json.loads(out)
    assert st["step"] == "granite" and st["granite_step"] == "done"
    assert st["progress"] == {"event": "progress", "step": "granite", "judged": 4, "of": 12, "eta_min": 1.0,
                              "sec_per_item": 0.2}
    code, out, _ = job(["record", "--root", str(remote), "--exit", "0", "--step", "done"])
    rec = json.loads((remote / "out/run-record.json").read_bytes())
    assert rec["tag"] == "sp-job" and rec["round"] == 1 and rec["limit"] == 3 and rec["ka"]["passed"] is True
    assert rec["granite_job"]["done"]["exit"] == 0 and rec["granite_job"]["run_record_sha256"] == sha(
        (remote / "granite-job/out/run-record.json").read_bytes())
    code, out, _ = job(["sums", "--root", str(remote)])
    sums = json.loads(out)["files"]
    assert set(sums) == set(SJ.OUTPUTS) and "out/job.log" not in sums and "granite-job/out/job.log" not in sums
    assert sums["out/run-record.json"] == sha((remote / "out/run-record.json").read_bytes())
    assert sums["granite-job/out/run-record.json"] == sha((remote / "granite-job/out/run-record.json").read_bytes())
    assert_no_text([json.dumps(st), out])


def test_require_packages_pins():
    versions = {"a": "1.0", "torch": "2.8.0+cu128"}
    assert SJ.require_packages({"a": "1.0"}, "2.8.0", version=versions.__getitem__) == versions
    with pytest.raises(SJ.Refusal, match="not the pinned"):
        SJ.require_packages({"a": "1.1"}, version=versions.__getitem__)
    with pytest.raises(SJ.Refusal, match="not the pinned"):
        SJ.require_packages({}, "2.9.0", version=versions.__getitem__)

    def missing(d):
        raise SJ.metadata.PackageNotFoundError(d)
    with pytest.raises(SJ.Refusal, match="not installed"):
        SJ.require_packages({"a": "1.0"}, version=missing)
    assert granite_pod.GRANITE_POD_PACKAGES["llama_cpp_python"] == granite_pod.LLAMA_VERSION == "0.3.36"


def test_the_guard_requirements_equal_the_pins_and_the_granite_venv_is_the_leads():
    def reqs(path):
        out = {}
        for line in path.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                pkg, ver = line.split(" ")[0].split("==")
                out[pkg.lower().replace("_", "-")] = ver
        return out
    norm = lambda d: {k.lower().replace("_", "-"): v for k, v in d.items()}           # noqa: E731
    guard = reqs(SJ.HERE / "guard-requirements.txt")
    assert all(guard[k] == v for k, v in norm(SJ.P.GUARD_PACKAGES).items())
    lock = {}
    for line in (SJ.P.ROOT / "experiments/minimal_safety/requirements.lock").read_text().splitlines():
        if "==" in line:
            pkg, ver = line.strip().split("==")
            lock[pkg.lower().replace("_", "-")] = ver
    assert all(lock[k] == v for k, v in guard.items())                       # the engine's lock versions
    lead_reqs = SJ.P.MAC_GATE_B / "pod/granite-requirements.txt"               # the lead's, shipped in gate_b/
    assert sha(lead_reqs.read_bytes()) == SJ.P.LAUNCHER_PINS["pod/granite-requirements.txt"]
    granite = norm(granite_pod.GRANITE_POD_PACKAGES)
    assert reqs(lead_reqs) == {k: v for k, v in granite.items() if k != "llama-cpp-python"}


def test_speed_verdict_rule():
    tokens = {"ratio": 0.47, "fiction_mean_tokens_per_call": 198.0, "ka_mean_tokens": 421.3, "fiction_calls": 20000}
    ok = SJ.speed_verdict(0.80, tokens)
    assert ok["too_slow"] is False and ok["projected_s_per_call"] == 0.376
    assert ok["projected_granite_minutes"] == round(0.376 * 20000 / 60, 1)
    assert SJ.speed_verdict(1.0, tokens)["too_slow"] is True
    assert SJ.speed_verdict(0.851, tokens)["too_slow"] is False          # 0.39997 s
    assert SJ.speed_verdict(0.852, tokens)["too_slow"] is True           # 0.40044 s
    assert SJ.speed_verdict(None, tokens)["too_slow"] is True            # not timed: never a pass
