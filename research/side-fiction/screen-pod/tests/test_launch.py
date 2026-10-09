"""screen_pod.launch with a fake host that runs the real screen_job.py on the unpacked real bundle (fake judges), then
summarize, and the per-row files read by sf_screen.py (the refill tool) as original-row and candidate labels. Also the
known-answer exit 8, the stop discipline on failures, the budget guard, the deadline and resume, the host records."""
from __future__ import annotations

import json
import pathlib

import pytest
from conftest import (P, SP, FakeGranite, FakeGuard, FakeHost, ka_label_map, launch_with, load_by_path, make_refill,
                      needs_real, refill_rows_from_real, sha, text_samples, assert_no_text, all_files)
from common import Refusal
import screen_summary as SS

ORDER = ["start", "bundle", "budget-guard", "created", "budget-guard-after-create", "ssh-ready", "checked",
         "bundle-sent", "bundle-verified-on-pod", "job-started", "job-done", "fetched", "verified", "stop", "end"]


def steps(log):
    return [r["step"] for r in log]


def sf_screen():
    if not P.REFILL_TOOL.is_file():
        pytest.skip("sf_screen.py is absent")
    return load_by_path("sf_screen_under_test", P.REFILL_TOOL)


@needs_real
def test_full_round1_launch_then_summarize_and_the_refill_tool_reads_the_labels(tmp_path, monkeypatch, capsys):
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch, signals=True)
    assert code == 0, [r for r in log if r["step"] in ("failed", "refused", "verified")]
    assert [s for s in steps(log) if s in ORDER] == ORDER
    assert host.calls.count("stop") == 1 and host.calls[0] == "lock" and host.status == "EXITED"
    assert [c for c in host.calls if isinstance(c, tuple) and c[0] in ("budget_check", "create")] == [
        ("budget_check", 5.0, 1.85), ("create", 5.0), ("budget_check", 0.0, 1.85)]
    v = result["verification"]
    assert v["complete"] and v["ka"]["passed"] and v["ka"]["complete"] and v["ka"]["counts"]["identical"] == 200
    assert v["granite"]["expected"] == 20000 and v["granite"]["complete"]
    assert v["qwen"]["expected"] == 14800 and v["qwen"]["complete"]
    assert set(result["fetched"]) >= {"DONE.json", "out/run-record.json", "out/ka.json", "out/ka-labels.jsonl",
                                      "out/granite.jsonl", "out/qwen.jsonl"}
    for rel, digest in result["fetched"].items():                     # fetched = the pod's bytes
        assert sha((folder / "fetched" / rel).read_bytes()) == digest == sha((host.remote / rel).read_bytes())
    assert not list(folder.rglob("*.part"))
    # summarize into a fresh output folder
    out = tmp_path / "screen"
    assert SP.main(["summarize", "--from", str(folder), "--out", str(out)]) == 0
    files = sorted(p.name for p in out.iterdir())
    assert files == ["round1-dark.jsonl", "round1-dolly.jsonl", "round1-light.jsonl", "round1-summary.json"]
    rows = {s: [json.loads(x) for x in (out / f"round1-{s}.jsonl").read_bytes().split(b"\n") if x.strip()]
            for s in ("dark", "light", "dolly")}
    assert [len(rows[s]) for s in ("dark", "light", "dolly")] == [5000, 5000, 4800]
    assert all(tuple(sorted(r)) == tuple(sorted(SS.ROW_KEYS["fiction"])) for s in ("dark", "light") for r in rows[s])
    assert all(tuple(sorted(r)) == tuple(sorted(SS.ROW_KEYS["dolly"])) for r in rows["dolly"])
    assert [r["line"] for r in rows["dark"]] == list(range(1, 5001))
    raw = [json.loads(x) for x in P.DATA_PATHS["dark"].read_bytes().split(b"\n") if x.strip()]
    assert all(r["response_sha256"] == sha(o["response"]) and r["category"] == o["category"]
               for r, o in zip(rows["dark"], raw))
    assert all(r["drop"] == (r["granite_harm"] != "No") and r["granite_harm_prob"] is None for r in rows["light"])
    summary = json.loads((out / "round1-summary.json").read_bytes())
    for arm in ("dark", "light"):
        a = summary["arms"][arm]
        assert a["rows_judged"] == 5000 and sum(b["rows_judged"] for b in a["books"].values()) == 5000
        assert a["granite"]["harm_Yes"] == sum(r["granite_harm"] == "Yes" for r in rows[arm])
        assert a["granite"]["dropped"] + a["granite"]["kept"] == 5000
        assert a["qwen3guard"]["Unsafe"] == sum(r["qwen3guard_safety"] == "Unsafe" for r in rows[arm])
        assert sorted(a["books"]) == [f"{arm}_b{b}" for b in range(1, 9)]
    assert summary["dolly"]["rows_judged"] == 4800 and summary["known_answer"]["identical"] == 200
    assert summary["pins"]["granite_gguf_sha256"] == P.GRANITE_GGUF_SHA256 and summary["reads"]["kept_rows"]
    assert summary["pins"]["inputs"] == {k: v[0] for k, v in P.DATA_PINS.items()}
    # the refill tool's reader: round-1 fiction rows are original-row labels, never candidates
    sf = sf_screen()
    originals, cands = sf.read_results([str(out / "round1-dark.jsonl"), str(out / "round1-light.jsonl")])
    assert cands == [] and len(originals) == 10000
    assert all(originals[(arm, r["line"])] == (r["granite_harm"].lower(), r["response_sha256"])
               for arm in ("dark", "light") for r in rows[arm])
    # no row text anywhere: the launch folder (but the bundle), the output folder, stdout and stderr
    io_ = capsys.readouterr()
    assert_no_text([io_.out, io_.err, *(p.read_bytes() for p in all_files(folder)),
                    *(p.read_bytes() for p in out.iterdir())], text_samples())
    assert SP.main(["summarize", "--from", str(folder), "--out", str(out)]) == 2       # never overwrites


@needs_real
def test_round2_refill_launch_writes_candidate_labels_that_sf_screen_matches(tmp_path, monkeypatch):
    rows = refill_rows_from_real()
    path, digest = make_refill(tmp_path / "screen-in", 2, rows)
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch, tag="sp-t2", round_=2,
                                                  extra=("--refill", str(path), "--refill-sha256", digest))
    assert code == 0
    assert result["verification"]["granite"]["expected"] == 24 and result["verification"]["qwen"]["expected"] == 12
    out = tmp_path / "screen"
    assert SP.main(["summarize", "--from", str(folder), "--out", str(out)]) == 0
    got = [json.loads(x) for x in (out / "round2-refill.jsonl").read_bytes().split(b"\n") if x.strip()]
    assert all(tuple(sorted(r)) == tuple(sorted(SS.ROW_KEYS["refill"])) for r in got)
    assert [(r["slot_arm"], r["slot_line"], r["rank"], r["line"]) for r in got] == [
        (src["slot_arm"], src["slot_line"], src["rank"], i) for i, src in enumerate(rows, 1)]
    assert all(r["response_sha256"] == sha(src["response"]) for r, src in zip(got, rows))
    summary = json.loads((out / "round2-summary.json").read_bytes())
    assert summary["rows"] == {"refill": 12} and summary["reads"] is None and summary["dolly"] is None
    assert summary["pins"]["refill"]["report"] == "refill-r2-report.json"
    sf = sf_screen()
    originals, cands = sf.read_results([], [str(out / "round2-refill.jsonl")])
    assert originals == {} and len(cands) == 12
    assert [(c["slot_arm"], c["slot_line"], c["rank"], c["sha"], c["label"]) for c in cands] == [
        (r["slot_arm"], r["slot_line"], r["rank"], r["response_sha256"], r["granite_harm"].lower()) for r in got]
    originals, cands = sf.read_results([str(out / "round2-refill.jsonl")])   # passed as --screen: still candidates
    assert originals == {} and len(cands) == 12


@needs_real
def test_failed_known_answer_check_exits_8_and_nothing_is_screened(tmp_path, monkeypatch):
    def granite_factory_for(bundle):
        labels = ka_label_map(bundle)
        flip = sorted(h for h, lab in labels.items() if lab == "No")[:40]
        return lambda: FakeGranite(labels, flip=flip)

    class KAFails(FakeHost):
        def run(self, command, timeout=120, stdin_path=None):
            if "nohup bash" in command:
                self.granite = granite_factory_for(self.remote / "bundle")
            return super().run(command, timeout, stdin_path)
    monkeypatch.setattr("conftest.FakeHost", KAFails)
    import conftest
    code, host, log, result, folder = conftest.launch_with(tmp_path, monkeypatch)
    assert code == P.EXIT_KA_FAILED == 8
    assert "KNOWN-ANSWER-CHECK-FAILED" in steps(log) and host.calls.count("stop") == 1 and host.status == "EXITED"
    assert "out/granite.jsonl" not in result["fetched"] and "out/qwen.jsonl" not in result["fetched"]
    assert not (host.remote / "out/granite.jsonl").exists() and not (host.remote / "out/qwen.jsonl").exists()
    done = json.loads((host.remote / "DONE.json").read_text())
    assert (done["exit"], done["step"]) == (4, "ka")
    assert result["verification"]["ka"]["complete"] and not result["verification"]["ka"]["passed"]
    with pytest.raises(Refusal):
        SS.summarize(folder, tmp_path / "screen")


@needs_real
def test_known_answer_refused_for_speed_is_exit_6_not_8(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "KA_MAX_S_PER_ITEM", -1.0)
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch)
    assert code == 6 and "KNOWN-ANSWER-CHECK-FAILED" not in steps(log)
    ka = result["verification"]["ka"]
    assert ka["present"] and not ka["complete"] and ka["refused"] and host.calls.count("stop") == 1


@needs_real
def test_budget_guard_refusal_creates_no_pod(tmp_path, monkeypatch):
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch, host_kw={"allowed": False})
    assert code == 3 and not [c for c in host.calls if isinstance(c, tuple) and c[0] == "create"]
    assert "stop" not in host.calls and result["pod_id"] is None


@needs_real
@pytest.mark.parametrize("step", ["wait_ssh", "check", "send", "unpack", "start", "fetch"])
def test_any_failure_after_create_stops_the_pod(tmp_path, monkeypatch, step):
    import podhost
    fail = {step: podhost.HostError("boom")} if step not in ("unpack", "start") else {step: 1}
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch, host_kw={"fail": fail})
    assert code == 6 and host.calls.count("stop") == 1 and host.status == "EXITED"
    assert result["stop"]["confirmed"] and steps(log)[-1] == "end"


@needs_real
def test_unconfirmed_stop_shortens_the_timer_and_exits_7(tmp_path, monkeypatch):
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch, host_kw={"stop_confirms": (False, False)})
    assert code == 7 and ("shorten_timer", 120) in host.calls and "STOP-NOT-CONFIRMED" in steps(log)


@needs_real
def test_corrupt_fetch_is_refused_and_the_pod_stopped(tmp_path, monkeypatch):
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch,
                                                  host_kw={"corrupt_fetch": "out/granite.jsonl"})
    assert code == 6 and host.calls.count("stop") == 1
    assert sum(1 for r in log if r["step"] == "fetch-attempt-failed") >= 3
    assert "out/granite.jsonl" not in result["fetched"]


@needs_real
def test_deadline_terminates_partial_caches_then_resume_completes(tmp_path, monkeypatch):
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch, host_kw={"mode": "hang"},
                                                  extra=("--limit", "4"))
    assert code == 5 and "deadline" in steps(log) and "terminate" in host.calls
    assert result["verification"]["ka"]["passed"] and not result["verification"]["complete"]
    code2, host2, log2, result2, folder2 = launch_with(tmp_path, monkeypatch, tag="sp-t1b",
                                                       extra=("--limit", "4", "--resume-from", str(folder)))
    assert code2 == 0 and result2["verification"]["complete"]
    bundle_record = json.loads((folder2 / "bundle-record.json").read_bytes())
    assert bundle_record["resume"]["from_tag"] == "sp-t1" and bundle_record["resume"]["granite"]["records"] >= 2


@needs_real
def test_tags_lock_and_the_real_host_records_folder(tmp_path, monkeypatch):
    import conftest
    import podhost
    assert SP.main(["launch", "--tag", "fscreen-1", "--round", "1"]) == 2               # the "sp-" rule
    assert SP.main(["launch", "--tag", "SP-X", "--round", "1"]) == 2
    code, *_ = launch_with(tmp_path, monkeypatch)
    assert code == 0
    assert SP.launch(conftest.launch_args("sp-t1"), host=FakeHost(tmp_path / "r2")) == 2   # the folder exists
    seen = {}

    class Recorder(FakeHost):
        def __init__(self, tag, records=None, kit=None, budget_kit=None, remote_root=None):
            seen.update(tag=tag, records=records, remote_root=remote_root)
            super().__init__(tmp_path / "r3", allowed=False)
    monkeypatch.setattr(podhost, "RunPodHost", Recorder)
    monkeypatch.setenv("RUNPOD_OPERATOR_API_KEY", "rpa_" + "K" * 24)
    assert SP.launch(conftest.launch_args("sp-t3"), host=None, clock=conftest.Clock(), sleep=lambda s: None,
                     signals=False) == 3
    assert seen == {"tag": "sp-t3", "records": pathlib.Path(SP.HOSTS) / "sp-t3", "remote_root": "/workspace/screen"}
    assert P.HOSTS == P.ROOT / "tmp/family-probe-sp-fiction-screen/hosts"           # where every kit's budget.py looks
    budget = P.ROOT / "tmp/family-probe-olmo2-1b-bt/budget.py"
    if budget.is_file():
        text = budget.read_text()
        assert 'KITS_GLOB = "family-probe-*"' in text and '(kit / "hosts").glob("*/pod.json")' in text
    monkeypatch.delenv("RUNPOD_OPERATOR_API_KEY")
    assert SP.launch(conftest.launch_args("sp-t4"), host=None, signals=False) == 2      # no key: refused, no host


def test_ka_failed_rule():
    ka = {"present": True, "complete": True, "passed": False}
    assert SP.ka_failed({"exit": 0, "step": "done"}, ka)                    # a pod pass the Mac recount rejects
    assert SP.ka_failed({"exit": 4, "step": "ka"}, {**ka, "complete": False})
    assert not SP.ka_failed({"exit": 4, "step": "llama-build"}, {**ka, "present": False, "complete": False})
    assert not SP.ka_failed({"exit": 2, "step": "ka"}, {**ka, "complete": False})      # refused: no verdict
    assert not SP.ka_failed({"exit": 5, "step": "ka"}, {**ka, "complete": False})      # stopped: no verdict
    assert not SP.ka_failed({"exit": 0, "step": "done"}, {**ka, "passed": True})


def test_status_progress_with_a_step_field_is_logged_as_job_step():
    """Regression (the lead's partial build): a progress line carrying "step" made RunLog raise TypeError (the log's own
    `step` argument twice) at the first poll, which failed the launch and stopped the job."""
    st = SP.parse_status(json.dumps({"started": True, "step": "granite", "done": None,
                                     "progress": {"event": "progress", "step": "granite", "judged": 4, "of": 9,
                                                  "eta_min": 0.5, "text": "FICTIONRESP"}}))
    assert st["progress"] == {"event": "progress", "job_step": "granite", "judged": 4, "of": 9, "eta_min": 0.5}

    class Host:
        def run(self, command, timeout=None):
            return 0, json.dumps({"started": True, "step": "ka", "done": {"exit": 0, "step": "done"},
                                  "progress": {"event": "record", "exit": 0, "step": "done"}})
    log = SP.JP.RunLog(pathlib.Path("/dev/null"), "sp-x", echo=False)
    seen = []
    log_fn = lambda step, **f: (seen.append((step, f)), log(step, **f))        # noqa: E731
    assert SP.poll(Host(), 1e12, log_fn, clock=lambda: 0.0, sleep=lambda s: None) == {"exit": 0, "step": "done"}
    assert seen[0] == ("progress", {"pod_step": "ka", "event": "record", "exit": 0, "job_step": "done"})


@needs_real
@pytest.mark.parametrize("signame,code,salvage", [("SIGINT", 5, True), ("SIGTERM", 6, False)])
def test_a_real_signal_during_the_poll_stops_the_pod_once(tmp_path, monkeypatch, signame, code, salvage):
    import os
    import signal as sig
    polls = {"n": 0}

    class Signalling(FakeHost):
        def run(self, command, timeout=120, stdin_path=None):
            if " status --root" in command:
                polls["n"] += 1
                if polls["n"] == 2:
                    os.kill(os.getpid(), getattr(sig, signame))
            return super().run(command, timeout, stdin_path)
    monkeypatch.setattr("conftest.FakeHost", Signalling)
    import conftest
    before = {s: sig.getsignal(s) for s in (sig.SIGINT, sig.SIGTERM, sig.SIGHUP, sig.SIGQUIT)}
    got, host, log, result, folder = conftest.launch_with(tmp_path, monkeypatch, host_kw={"mode": "hang"},
                                                          extra=("--limit", "3"), signals=True)
    assert got == code and host.calls.count("stop") == 1 and host.status == "EXITED"
    assert ("salvaged" in steps(log)) is salvage and ("salvage-skipped" in steps(log)) is (not salvage)
    assert {s: sig.getsignal(s) for s in before} == before                  # the handlers come back after the stop


@needs_real
def test_a_pod_pass_that_the_macs_recount_rejects_exits_8(tmp_path, monkeypatch):
    """The pod's ka.json claims a pass over labels that fail the rule: granite refuses on the pod (its gate recounts),
    and the launcher's own recount against the Mac labels makes it a failed check (8), not an ordinary failure (6)."""
    import conftest

    class Forged(FakeHost):
        def run(self, command, timeout=120, stdin_path=None):
            if "nohup bash" in command and self.mode == "finish":
                bundle, out = self.remote / "bundle", self.remote / "out"
                labels = ka_label_map(bundle)
                flip = sorted(h for h, lab in labels.items() if lab == "No")[:40]
                real = conftest.SJ.main

                def forging(argv, judge_factory=None, guard_factory=None):
                    code = real(argv, judge_factory=judge_factory, guard_factory=guard_factory)
                    if argv[0] == "ka":
                        rec = json.loads((out / "ka.json").read_bytes())
                        rec["passed"] = True
                        (out / "ka.json").write_text(json.dumps(rec))
                        return 0
                    return code
                monkeypatch.setattr(conftest.SJ, "main", forging)
                self.granite = lambda: FakeGranite(labels, flip=flip)
                try:
                    return super().run(command, timeout, stdin_path)
                finally:
                    monkeypatch.setattr(conftest.SJ, "main", real)
            return super().run(command, timeout, stdin_path)
    monkeypatch.setattr("conftest.FakeHost", Forged)
    code, host, log, result, folder = conftest.launch_with(tmp_path, monkeypatch, extra=("--limit", "2"))
    done = json.loads((host.remote / "DONE.json").read_text())
    assert (done["exit"], done["step"]) == (2, "granite")                     # the pod's own gate refused
    ka = result["verification"]["ka"]
    assert ka["passed_pod"] is True and ka["passed_mac"] is False and ka["complete"]
    assert code == 8 and "KNOWN-ANSWER-CHECK-FAILED" in steps(log) and host.calls.count("stop") == 1


def test_every_pod_line_logged_as_keywords_renames_step():
    """The verify line and the progress lines both pass through whitelist into log(**fields)."""
    assert SP.whitelist({"event": "bundle_verified", "step": "verify", "files": 3, "rows": {"dark": 1},
                         "manifest_sha256": "a" * 64, "judged": "x" * 65, "text": "y"}) == {
        "event": "bundle_verified", "job_step": "verify", "files": 3}            # fields of STATUS_FIELDS, scalars, short
    log = SP.JP.RunLog(pathlib.Path("/dev/null"), "sp-x", echo=False)
    log("bundle-verified-on-pod", **SP.whitelist({"step": "verify", "event": "bundle_verified"}))   # no TypeError


@needs_real
def test_known_answers_too_slow_exit_9_and_nothing_screened(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "GRANITE_S_PER_CALL", -1.0)
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch, extra=("--limit", "2"))
    assert code == P.EXIT_TOO_SLOW == 9
    assert "KNOWN-ANSWERS-TOO-SLOW" in steps(log) and "KNOWN-ANSWER-CHECK-FAILED" not in steps(log)
    done = json.loads((host.remote / "DONE.json").read_text())
    assert (done["exit"], done["step"]) == (3, "ka")
    assert "out/granite.jsonl" not in result["fetched"] and "out/qwen.jsonl" not in result["fetched"]
    assert result["verification"]["ka"]["passed"] and result["verification"]["ka"]["too_slow"] is True
    speed = result["verification"]["ka"]["speed"]
    assert speed["too_slow"] is True and speed["ratio"] > 0 and speed["planned_s_per_call"] == -1.0
    assert speed["projected_s_per_call"] == pytest.approx(speed["seconds_per_item"] * speed["ratio"], abs=1e-4)
    assert host.calls.count("stop") == 1 and host.status == "EXITED"
