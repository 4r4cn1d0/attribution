"""screen_job.py on an unpacked real bundle with fake judges: the known-answer gate, both judges, resume, SIGTERM,
the records, and the status and sums whitelists (no model, no GPU)."""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import tarfile

import pytest
from conftest import (P, R, SJ, SP, FakeGranite, FakeGuard, ka_label_map, needs_real, sha, text_samples,
                      assert_no_text)


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


def ka(remote, judge):
    return job(["ka", "--bundle", str(remote / "bundle"), "--record", str(remote / "out/ka.json"), "--labels",
                str(remote / "out/ka-labels.jsonl")], granite=lambda: judge)


def granite(remote, judge):
    return job(["granite", "--bundle", str(remote / "bundle"), "--ka", str(remote / "out/ka.json"), "--cache",
                str(remote / "out/granite.jsonl"), "--record", str(remote / "out/granite-record.json")],
               granite=lambda: judge)


def qwen(remote, guard):
    return job(["qwen", "--bundle", str(remote / "bundle"), "--ka", str(remote / "out/ka.json"), "--cache",
                str(remote / "out/qwen.jsonl"), "--record", str(remote / "out/qwen-record.json")],
               guard=lambda: guard)


@needs_real
def test_known_answer_pass_then_both_judges(remote):
    labels = ka_label_map(remote / "bundle")
    judge = FakeGranite(labels)
    code, out, err = ka(remote, judge)
    assert code == 0, err
    rec = json.loads((remote / "out/ka.json").read_bytes())
    assert rec["passed"] is True and rec["counts"]["identical"] == 200 and rec["counts"]["pod_yes"] == 93
    assert rec["stopped"] is False and rec["refused"] is None and rec["error"] is None
    entries = [json.loads(x) for x in (remote / "out/ka-labels.jsonl").read_bytes().split(b"\n") if x.strip()]
    assert len(entries) == 200 and [e["prompt_id"] for e in entries] == sorted(e["prompt_id"] for e in entries)
    assert set(entries[0]) == {"prompt_id", "answer_sha256", "mac", "pod", "attempts", "errors", "reason",
                               "input_tokens", "trimmed"}
    assert [s[1] for s in judge.seen] == [e["answer_sha256"] for e in entries]       # judged in prompt-id order
    assert all(c == "harm" for *_, c in judge.seen)
    g = FakeGranite(labels)
    code, out, err = granite(remote, g)
    assert code == 0, err
    cache = R.JsonlCache(remote / "out/granite.jsonl", R.check_granite, R.granite_key)
    assert len(cache) == 12 and {k[0] for k in cache.entries} == {"dark-1", "dark-2", "dark-3", "light-1", "light-2",
                                                                  "light-3"}
    assert [c for *_, c in g.seen] == ["harm", "sexual_content"] * 6
    grec = json.loads((remote / "out/granite-record.json").read_bytes())
    assert grec["ka_passed"] is True and grec["limit"] == 3 and set(grec["counts"]) == {"dark", "light"}
    guard = FakeGuard()
    code, out, err = qwen(remote, guard)
    assert code == 0, err
    qcache = R.JsonlCache(remote / "out/qwen.jsonl", R.check_qwen, R.qwen_key)
    assert len(qcache) == 9 and {e["source"] for e in qcache.entries.values()} == {"dark", "light", "dolly"}
    rows = {r.row_id: r for rows in SJ.SB.pod_sources(remote / "bundle", SJ.SB.verify_bundle(remote / "bundle")).values()
            for r in rows}
    for item_id, user_sha, response_sha in guard.items:                  # the guard got the screen's user turn
        assert (user_sha, response_sha) == (sha(rows[item_id].user_turn), sha(rows[item_id].assistant_turn))
    qrec = json.loads((remote / "out/qwen-record.json").read_bytes())
    assert "secret" not in qrec["guard_identity"] and qrec["guard_identity"]["revision"] == P.QWEN_REVISION
    assert_no_text([out, err, *(p.read_bytes() for p in (remote / "out").iterdir() if p.is_file())], text_samples())


@needs_real
def test_failed_known_answer_check_exits_4_and_no_row_is_screened(remote):
    labels = ka_label_map(remote / "bundle")
    mac = json.loads((remote / "bundle/ka/mac-labels.json").read_bytes())
    n_of = {}
    for h in mac["answer_sha256"].values():                                  # some greedy answers repeat verbatim
        n_of[h] = n_of.get(h, 0) + 1
    flip = [h for pid, h in sorted(mac["answer_sha256"].items()) if n_of[h] == 1 and mac["labels"][pid] == "No"][:11]
    assert len(flip) == 11                                                  # 189 identical, delta +11
    code, _, _ = ka(remote, FakeGranite(labels, flip=flip))
    assert code == P.POD_EXIT_KA_FAILED
    rec = json.loads((remote / "out/ka.json").read_bytes())
    assert rec["passed"] is False and rec["counts"]["identical"] == 189
    g = FakeGranite(labels)
    code, _, err = granite(remote, g)
    assert code == P.POD_EXIT_REFUSED and g.calls == 0 and not (remote / "out/granite.jsonl").exists()
    guard = FakeGuard()
    code, _, _ = qwen(remote, guard)
    assert code == P.POD_EXIT_REFUSED and guard.items == []
    (remote / "out/ka.json").write_text(json.dumps({"passed": True, "counts": rec["counts"]}))   # a forged pass
    code, _, _ = granite(remote, g)
    assert code == P.POD_EXIT_REFUSED and g.calls == 0


@needs_real
def test_known_answer_without_gpu_speed_is_refused_not_failed(remote, monkeypatch):
    labels = ka_label_map(remote / "bundle")
    monkeypatch.setattr(P, "KA_MAX_S_PER_ITEM", -1.0)                         # any answer is "too slow"
    judge = FakeGranite(labels)
    code, _, err = ka(remote, judge)
    assert judge.calls == P.KA_SPEED_AFTER
    assert code == P.POD_EXIT_REFUSED
    rec = json.loads((remote / "out/ka.json").read_bytes())
    assert "not running on the GPU" in rec["refused"] and "counts" not in rec


@needs_real
def test_sigterm_stops_with_exit_5_and_the_next_run_resumes(remote):
    labels = ka_label_map(remote / "bundle")
    assert ka(remote, FakeGranite(labels))[0] == 0
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
    labels = ka_label_map(remote / "bundle")
    assert ka(remote, FakeGranite(labels))[0] == 0

    class Boom(FakeGranite):
        def judge(self, *a):
            raise MemoryError("cuda")
    code, _, err = granite(remote, Boom(labels))
    assert code == P.POD_EXIT_ERROR
    assert json.loads((remote / "out/granite-record.json").read_bytes())["error"] == "MemoryError"


@needs_real
def test_record_status_and_sums_print_whitelisted_counts_only(remote):
    labels = ka_label_map(remote / "bundle")
    assert ka(remote, FakeGranite(labels))[0] == 0
    (remote / "out/job.log").write_text("\n".join([
        json.dumps({"event": "progress", "step": "granite", "judged": 4, "of": 12, "eta_min": 1.0,
                    "text": "FICTIONRESP leak", "sec_per_item": 0.2}),
        "Traceback (most recent call last): FICTIONCTX in a traceback line"]) + "\n")
    (remote / "STEP").write_text("granite\n")
    code, out, _ = job(["status", "--root", str(remote)])
    st = json.loads(out)
    assert st["step"] == "granite" and st["progress"] == {"event": "progress", "step": "granite", "judged": 4, "of": 12,
                                                         "eta_min": 1.0, "sec_per_item": 0.2}
    code, out, _ = job(["record", "--root", str(remote), "--exit", "0", "--step", "done"])
    rec = json.loads((remote / "out/run-record.json").read_bytes())
    assert rec["tag"] == "sp-job" and rec["round"] == 1 and rec["limit"] == 3 and rec["ka"]["passed"] is True
    assert rec["outputs"]["out/ka-labels.jsonl"]["sha256"] == sha((remote / "out/ka-labels.jsonl").read_bytes())
    code, out, _ = job(["sums", "--root", str(remote)])
    sums = json.loads(out)["files"]
    assert set(sums) == set(SJ.OUTPUTS) and "out/job.log" not in sums
    assert sums["out/run-record.json"] == sha((remote / "out/run-record.json").read_bytes())
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
    assert SJ.P.GRANITE_PACKAGES["llama_cpp_python"] == SJ.P.LLAMA_VERSION == "0.3.36"


def test_requirements_files_equal_the_pins():
    def reqs(name):
        out = {}
        for line in (SJ.HERE / name).read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                pkg, ver = line.split(" ")[0].split("==")
                out[pkg.lower().replace("_", "-")] = ver
        return out
    norm = lambda d: {k.lower().replace("_", "-"): v for k, v in d.items()}           # noqa: E731
    granite_pins = norm(SJ.P.GRANITE_PACKAGES)
    assert reqs("granite-requirements.txt") == {k: v for k, v in granite_pins.items() if k != "llama-cpp-python"}
    assert reqs("llama-requirements.txt") == {"llama-cpp-python": "0.3.36"}
    assert f"--hash=sha256:{SJ.P.LLAMA_SDIST_SHA256}" in (SJ.HERE / "llama-requirements.txt").read_text()
    guard = reqs("guard-requirements.txt")
    assert all(guard[k] == v for k, v in norm(SJ.P.GUARD_PACKAGES).items())
    lock = {}
    for line in (SJ.P.ROOT / "experiments/minimal_safety/requirements.lock").read_text().splitlines():
        if "==" in line:
            pkg, ver = line.strip().split("==")
            lock[pkg.lower().replace("_", "-")] = ver
    assert all(lock[k] == v for k, v in guard.items())                       # the engine's lock versions
    judge_venv = SJ.P.ROOT / "tmp/judge-venv"
    if judge_venv.is_dir():                                                   # the Mac judge venv's own metadata
        import glob
        found = {}
        for meta in glob.glob(str(judge_venv / "lib/python3.*/site-packages/*.dist-info/METADATA")):
            fields = dict(line.split(": ", 1) for line in open(meta, encoding="utf-8").read().split("\n\n")[0]
                          .splitlines() if ": " in line)
            found[fields["Name"].lower().replace("_", "-")] = fields["Version"]
        found.pop("pip"), found.pop("setuptools")
        assert found == granite_pins


def _set_ratio(remote, ratio: float, ka_mean: float = 421.3) -> None:
    """Gives the unpacked bundle's manifest a token block with ratio r (the means consistent with it)."""
    path = remote / "bundle/job-manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["granite_tokens"].update(ratio=ratio, ka_mean_tokens=ka_mean,
                                      fiction_mean_tokens_per_call=round(ratio * ka_mean, 3))
    path.write_bytes(SJ.canonical_bytes(manifest))


class StepClock:
    """A clock that moves only when the fake judge answers: `step` seconds per known answer."""

    def __init__(self, step: float):
        self.t, self.step = 1000.0, step

    def __call__(self):
        return self.t


@needs_real
@pytest.mark.parametrize("s_per_item,code", [(0.80, 0), (1.0, 3)])
def test_known_answer_speed_is_projected_by_the_token_ratio(remote, monkeypatch, s_per_item, code):
    """r = 0.47: known answers at 0.80 s each project to 0.376 s per fiction call (under 0.4: the run goes on); at
    1.0 s each to 0.47 s (above 0.4: exit 3, the pass recorded, granite and qwen refuse)."""
    import granite_screen as G
    labels = ka_label_map(remote / "bundle")
    _set_ratio(remote, 0.47)
    clock = StepClock(s_per_item)
    monkeypatch.setattr(G, "CLOCK", clock)

    class Timed(FakeGranite):
        def judge(self, u, a, c):
            clock.t += clock.step
            return super().judge(u, a, c)
    assert ka(remote, Timed(labels))[0] == code
    rec = json.loads((remote / "out/ka.json").read_bytes())
    speed = rec["speed"]
    assert rec["passed"] is True and rec["too_slow"] is (code == 3) and speed["too_slow"] is (code == 3)
    assert speed["ratio"] == 0.47 and speed["seconds_per_item"] == pytest.approx(s_per_item)
    assert speed["projected_s_per_call"] == pytest.approx(round(s_per_item * 0.47, 4))
    assert speed["ka_mean_tokens"] == 421.3 and speed["fiction_mean_tokens_per_call"] == round(0.47 * 421.3, 3)
    assert speed["ka_mean_tokens_pod"] == 100.0 and speed["planned_s_per_call"] == 0.4      # the fake's 100 tokens
    calls = json.loads((remote / "bundle/job-manifest.json").read_bytes())["granite_tokens"]["fiction_calls"]
    assert speed["granite_calls"] == calls == 12                                         # 6 rows x 2 (limit 3)
    assert speed["projected_granite_minutes"] == round(s_per_item * 0.47 * calls / 60, 1)
    g = FakeGranite(labels)
    assert granite(remote, g)[0] == (P.POD_EXIT_REFUSED if code == 3 else 0)
    assert (g.calls == 0) is (code == 3)


def test_speed_verdict_rule():
    tokens = {"ratio": 0.47, "fiction_mean_tokens_per_call": 198.0, "ka_mean_tokens": 421.3, "fiction_calls": 20000}
    entries = [{"input_tokens": 400}, {"input_tokens": 442}]
    ok = SJ.speed_verdict(0.80, tokens, entries)
    assert ok["too_slow"] is False and ok["projected_s_per_call"] == 0.376 and ok["ka_mean_tokens_pod"] == 421.0
    assert ok["projected_granite_minutes"] == round(0.376 * 20000 / 60, 1)
    assert SJ.speed_verdict(1.0, tokens, entries)["too_slow"] is True
    assert SJ.speed_verdict(0.851, tokens, entries)["too_slow"] is False          # 0.39997 s
    assert SJ.speed_verdict(0.852, tokens, entries)["too_slow"] is True           # 0.40044 s
    assert SJ.speed_verdict(None, tokens, entries)["too_slow"] is True            # not timed: never a pass
