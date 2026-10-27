"""Kit round 31 (27 Oct 2026; addendum §32 points 1-3; the lead's K1-K6), on CPU, without RunPod, Hugging Face or
GitHub. Expected values are written by hand; every input is synthetic. (K2's judge route, K3 and K4 are in
test_stage1_judge_route.py.)

K1: a not-run decision for a released judge launch of any block but A (record-judge-not-run), also after the block's
seal; record-judges then needs only the other judges; completeness, the seal and seal.py status count and list it;
block A keeps its route. K2 (the plan side): block B's required units hold its ref_train units; REJUDGED_PINS["B"] is
empty by rule; init-block of a block other than A refuses a judge launch over fewer units than its jobs produce. K5:
the finisher treats a moved, not-done host as finished for the watch. K6: launch.py exits non-zero when a host it
should create has no pod.json at its end."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

import test_stage1_runkit as rk
import test_stage1_runner as rn
from test_stage1_runkit import w  # noqa: F401 - the World fixture (a copy of the kit, synthetic pins)
from test_stage1_runner import kit  # noqa: F401 - the kit fixture (a copy of the kit and a module loader)

write_json, sha = rk.write_json, rk.sha
NOT_RUN_KIND = "stage1 judge not-run decision"
HB24, GR24 = {"judge": {"judge": "harmbench", "arms": 24}}, {"judge": {"judge": "granite", "arms": 24}}
G1102 = {"kind": "ref_train", "arm": "G", "recipe": "G", "seed": 1102}


def _decision(w, judges, block="B", reason="lead: synthetic: Granite's known-answer gate failed (exit 8)",
              **change) -> tuple[str, str]:
    body = {"kind": NOT_RUN_KIND, "block": block, "judges": judges, "reason": reason, "utc": "2026-10-27T13:00:00Z",
            "recorded_by": "test", **change}
    return w.record({k: v for k, v in body.items() if v is not None})


def _block_b_judged(w) -> None:
    """Block A complete and sealed, a passing certificate; block B planned under plan A (the deal's 24 runs on 6 pods
    in one launch, then HarmBench and Granite over 24 units), every block-B host done; the judge launches NOT released
    yet."""
    rk._block_b_ready(w, passed=True)
    w.init("B", rk.B_DEAL + [HB24, GR24])
    hosts = sorted(n for n, h in w.plan()["hosts"].items() if h["block"] == "B")
    assert hosts == ["b-1", "b-2", "b-3", "b-4", "b-5", "b-6"]
    for host in hosts:
        w.done(host)
    b = w.plan()["blocks"]["B"]
    assert (b["released"], len(b["launches"])) == (1, 3)


# ===== K1 ============================================================================================================

def test_k1_a_released_block_b_judge_launch_named_not_run_completes_the_block_and_the_seal_lists_it(w, capsys):
    """K1 both ways: the decision refuses before the release, for block A (its own route), an unplanned block, every
    malformed record (a count key, an unknown, repeated or missing judge, an empty reason, a future time), a judge
    the completion record names, and a second decision of one judge; a good decision (by the CLI) completes block B
    with HarmBench's record alone; the seal lists it (judge and decision SHA-256) and seal.py status prints it, valid;
    a changed decision file refuses the completion check and the status line says INVALID."""
    _block_b_judged(w)
    path, digest = _decision(w, ["granite"])
    with pytest.raises(SystemExit, match="block B's granite judge launch is not released"):
        w.tool.record_judge_not_run(path, digest)
    assert w.tool.release("B")["launches_released"] == 3
    assert w.tool.block_complete(w.plan(), "B") is False                      # released is not done (round 30)
    bad = [(dict(kind="stage1 block-a not-run decision"), "not a judge not-run decision"),
           (dict(yes=rk.JUDGE_SENTINEL), "not a judge not-run decision"),
           (dict(judges=[]), "not a judge not-run decision"),
           (dict(judges=["granite", "granite"]), "not a judge not-run decision"),
           (dict(judges=["llamaguard"]), "not a judge not-run decision"),
           (dict(reason=" "), "needs its block, reason, utc and recorded_by"),
           (dict(utc="2099-01-01T00:00:00Z"), "in the future"),
           (dict(block="A"), "named by record-block-a-not-run"),
           (dict(block="C"), "block C is not planned")]
    for change, match in bad:
        args = {"judges": change.pop("judges", ["granite"]), **change}
        with pytest.raises(SystemExit, match=match):
            w.tool.record_judge_not_run(*_decision(w, **args))
    with pytest.raises(SystemExit, match="differs from the one given"):
        w.tool.record_judge_not_run(path, "0" * 64)
    hb = w.tool.record_judges("B", *w.file_judges(block="B", judges=("harmbench",)))
    assert hb["judges"] == ["harmbench"] and hb["units"] == 24 and hb["tags"] == {"harmbench": "s1b-harmbench-1"}
    assert w.tool.block_complete(w.plan(), "B") is False                      # Granite: released, no record, no decision
    with pytest.raises(SystemExit, match="'judge harmbench' has a judge-completion record"):
        w.tool.record_judge_not_run(*_decision(w, ["harmbench"]))
    capsys.readouterr()
    assert w.tool.main(["record-judge-not-run", path, "--sha256", digest]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"recorded": "judge_not_run", "block": "B", "sha256": digest, "judges": ["granite"],
                   "needed": ["harmbench"], "complete": True, "sealed": False}
    with pytest.raises(SystemExit, match="'judge granite' is already named by a recorded judge not-run decision"):
        w.tool.record_judge_not_run(*_decision(w, ["granite"], reason="lead: again"))
    entry = w.plan()["records"]["judge_not_run"]
    assert [(e["block"], e["judges"], e["sha256"], e["path"]) for e in entry] == [("B", ["granite"], digest,
                                                                                    str(Path(path).resolve()))]
    log = [json.loads(x) for x in (w.root / "operator-actions.jsonl").read_text().splitlines()]
    assert log[-1] == {**log[-1], "action": "record-judge-not-run", "block": "B", "sha256": digest,
                       "judges": ["granite"]}
    assert w.tool.judges_needed(w.plan(), "B") == ["harmbench"] and w.tool.judges_decided(w.plan(), "B") == {
        "granite": digest}
    sealed = w.seal.seal_block("B")
    record = json.loads((w.root / "seals" / "block-B.json").read_text())
    assert record["judge_not_run"] == [{"judge": "granite", "decision_sha256": digest}]
    assert record["judge_record"]["judges"] == ["harmbench"] and record["judge_record"]["units"] == 24
    assert sealed["files"] == record["counts"]["files"]
    assert w.seal.main(["status"]) == 0
    assert f"judges B not run: granite by decision {digest[:16]}; valid" in capsys.readouterr().out.splitlines()
    keep = Path(path).read_bytes()
    Path(path).write_bytes(keep + b" ")
    with pytest.raises(SystemExit, match="judge not-run decision is missing or differs from its recorded SHA-256"):
        w.tool.block_complete(w.plan(), "B")
    w.seal.main(["status"])
    assert f"judges B not run: granite by decision {digest[:16]}; INVALID: " in capsys.readouterr().out
    Path(path).write_bytes(keep)
    assert w.tool.block_complete(w.plan(), "B") is True


def test_k1_record_judges_needs_only_the_judges_no_decision_names(w):
    """K1: with the Granite decision recorded first, record-judges B refuses a record naming Granite and takes the one
    naming HarmBench alone; without the decision (and without Granite's record) block B stays open, and the seal
    refuses it."""
    _block_b_judged(w)
    w.tool.release("B")
    with pytest.raises(SystemExit, match="block B is not complete"):
        w.seal.seal_block("B")
    w.tool.record_judge_not_run(*_decision(w, ["granite"]))
    assert w.tool.block_complete(w.plan(), "B") is False                      # HarmBench: released, no record
    with pytest.raises(SystemExit, match="'judge granite' is named by a recorded not-run decision"):
        w.tool.record_judges("B", *w.file_judges(block="B"))
    shutil.rmtree(w.root / "judges" / "B")                                # HarmBench's files alone, re-indexed
    out = w.tool.record_judges("B", *w.file_judges(block="B", judges=("harmbench",)))
    assert out["judges"] == ["harmbench"] and "open" not in out
    assert w.tool.block_complete(w.plan(), "B") is True


def test_k1_a_decision_after_the_blocks_seal_adds_a_record_and_changes_no_seal(w):
    """K1: a block B sealed with released judge launches and no record (the old seal.py's shape): both judges named
    not run after the seal; the seal file and plan.json's seal entry are unchanged and the block counts complete. Block
    A's judge launches still take only block A's own route."""
    _block_b_judged(w)
    w.tool.release("B")
    seal = w.old_seal("B")
    seal_bytes = (w.root / "seals" / "block-B.json").read_bytes()
    out = w.tool.record_judge_not_run(*_decision(w, ["harmbench", "granite"], reason="lead: synthetic: not paid"))
    assert (out["sealed"], out["complete"], out["needed"]) == (True, True, [])
    assert w.plan()["seals"]["B"] == seal and (w.root / "seals" / "block-B.json").read_bytes() == seal_bytes
    with pytest.raises(SystemExit, match="named by record-block-a-not-run"):
        w.tool.record_judge_not_run(*_decision(w, ["granite"], block="A"))


# ===== K2: the plan side =============================================================================================

def test_k2_block_bs_rejudged_pins_are_empty_by_rule(w):
    """K2 (§32 point 2): REJUDGED_PINS names block B explicitly with no unit (written into stage1_rules.py, not left
    to a default), so block B's required units are its plan.json units only; block A keeps its 7."""
    assert "B" in w.rules.REJUDGED_PINS and w.rules.REJUDGED_PINS["B"] == () and len(w.rules.REJUDGED_PINS["A"]) == 7
    assert 'REJUDGED_PINS = {"B": (), "A": (' in (w.root / "stage1_rules.py").read_text()
    x = hashlib.sha256(b"x").hexdigest()
    plan = {"hosts": {"b-1": {"block": "B", "jobs": [{"kind": "arm", "arm": "A1", "seed": 1105, "status": "complete",
                                                       "complete_sha256": x}]}}}
    assert w.tool.judge_required_units(plan, "B") == {x: "b-1 job 0 (arm A1 1105)"}


def test_k2_block_bs_required_units_hold_its_ref_train_units(w):
    """K2 (§32 point 1): a complete, pulled ref_train job's unit (recipe G or B+Qi) is required, beside the a0_arm run
    at the same seed; a crashed one or one recorded not pulled is not; one complete without its COMPLETE.json SHA-256
    refuses."""
    a0, g, bqi, late = (hashlib.sha256(s.encode()).hexdigest() for s in ("a0", "g", "bqi", "late"))
    plan = {"hosts": {
        "b-1": {"block": "B", "jobs": [{"kind": "a0_arm", "arm": "a0", "seed": 1105, "status": "complete",
                                        "complete_sha256": a0}]},
        "b-7": {"block": "B", "jobs": [{"kind": "ref_train", "arm": "G", "recipe": "G", "seed": 1105,
                                        "status": "complete", "complete_sha256": g},
                                       {"kind": "ref_train", "arm": "G", "recipe": "G", "seed": 1106,
                                        "status": "crashed"}]},
        "b-8": {"block": "B", "jobs": [{"kind": "ref_train", "arm": "bqi", "recipe": "bqi", "seed": 1105,
                                        "status": "complete", "complete_sha256": bqi},
                                       {"kind": "ref_train", "arm": "bqi", "recipe": "bqi", "seed": 1106,
                                        "status": "complete", "complete_sha256": late, "pulled": False}]}}}
    assert w.tool.judge_required_units(plan, "B") == {a0: "b-1 job 0 (a0_arm a0 1105)",
                                                       g: "b-7 job 0 (ref_train G 1105)",
                                                       bqi: "b-8 job 0 (ref_train bqi 1105)"}
    del plan["hosts"]["b-7"]["jobs"][0]["complete_sha256"]
    with pytest.raises(SystemExit, match=r"b-7 job 0 \(ref_train G 1105\): plan.json records no COMPLETE.json"):
        w.tool.judge_required_units(plan, "B")


def test_k2_the_judged_units_a_blocks_jobs_produce_by_hand(w):
    """K2: one per arm, a0_arm and ref_train run, one per ref_eval and safe_lora point, plus the block's pins; a
    regeneration, an O-only pass and B10's certify job produce none."""
    jobs = [{"kind": "arm"}, {"kind": "a0_arm"}, {"kind": "ref_train"}, {"kind": "regenerate"}, {"kind": "o_only"},
            {"kind": "ref_eval", "points": ["scale:0.9", "prefix"]},
            {"kind": "safe_lora", "points": ["default", "conditional", "certify"]},
            {"kind": "b10_certify", "points": ["certify", "scale:0"]}]
    assert w.tool.planned_judged_units("B", jobs) == 3 + 2 + 3
    assert w.tool.planned_judged_units("A", [{"kind": "arm"}]) == 1 + 7
    assert w.tool.planned_judged_units("C", []) == 0


def test_k2_init_block_refuses_a_judge_launch_over_fewer_units_than_its_jobs_produce(w):
    """K2's plan check both ways at init-block B (dry run and real): the deal's 24 runs and one recipe-G reference
    produce 25 judged units; a HarmBench or Granite launch over 24 refuses, over 25 is planned (block A's judge
    launches keep their plan's own check: an A launch over 20 units still plans, as round 30's tests show)."""
    rk._block_b_ready(w, passed=True)
    for judge in ("harmbench", "granite"):
        with pytest.raises(SystemExit, match=rf"launch 2: the {judge} judge launch is over 24 units, below the 25 "
                                             r"judged units block B's jobs will produce"):
            w.init("B", rk.B_DEAL + [{"hosts": [[G1102]]}, {"judge": {"judge": judge, "arms": 24}}], dry_run=True)
    assert "B" not in w.plan()["blocks"]
    out = w.init("B", rk.B_DEAL + [{"hosts": [[G1102]]}, {"judge": {"judge": "harmbench", "arms": 25}},
                                   {"judge": {"judge": "granite", "arms": 25}}])
    assert out["hosts"] == ["b-1", "b-2", "b-3", "b-4", "b-5", "b-6", "b-7"]
    assert [x.get("judge", {}).get("arms") for x in w.plan()["blocks"]["B"]["launches"]] == [None, None, 25, 25]


# ===== K5: the finisher and moved hosts ==============================================================================

class _Round(Exception):
    """The finisher went on to watch (it slept): it did not end on 'every planned host is finished'."""


def _watch(kit, monkeypatch, done: dict, finished=(), moves=(), caps=None):
    """The finisher's first round on a synthetic plan: hosts ``done`` {host: recorded done}, each with a pod.json whose
    cap stop is now + caps[host] hours (default 1), finished.json for ``finished``, requeues ``moves`` (from, to).
    Returns (the module, the plan, the logged events, main's exit or None when it went on to sleep)."""
    fin = kit("finisher.py")
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    plan = {"hosts": {h: {"role": "arms", "cap_hours": 3.0, "done": d} for h, d in done.items()},
            "deferrals": [], "requeues": [{"from": a, "to": b} for a, b in moves]}
    rn.write(kit.root / "plan.json", plan)
    for h in done:
        stop = now + dt.timedelta(hours=(caps or {}).get(h, 1))
        rn.write(kit.root / "hosts" / h / "pod.json", {"id": f"pod-{h}", "cap_stop_utc": stop.isoformat()})
    for h in finished:
        rn.write(kit.root / "hosts" / h / "finished.json", {"status": "verified-and-stopped"})
    logged = []
    monkeypatch.setattr(fin, "log", lambda **f: logged.append(f))
    monkeypatch.setattr(fin.secret_scan, "scrub_process", lambda *a, **k: None)
    monkeypatch.setattr(fin, "tool", lambda *a: pytest.fail(f"no host.py call expected here: {a}"))

    def sleep(seconds):
        raise _Round()
    monkeypatch.setattr(fin, "time", types.SimpleNamespace(sleep=sleep))
    monkeypatch.setattr(sys, "argv", ["finisher.py", "1"])
    try:
        code = fin.main()
    except _Round:
        code = None
    return fin, plan, [f.get("event") for f in logged], code


def test_k5_the_finisher_ends_when_every_host_is_finished_or_moved_and_not_done(kit, monkeypatch):
    """K5 (cert runbook D9) by hand: a-5 was requeued to a-9 before anything ran (not done, pod.json, never a
    finished.json); a-1 and a-9 are finished. The first round logs 'every planned host is finished' and exits 0; a-5
    is not watched and its 10 h cap sets no deadline (the deadline is a-9's 2 h cap + 3 h)."""
    fin, plan, events, code = _watch(kit, monkeypatch, {"a-1": True, "a-5": False, "a-9": True},
                                     finished=("a-1", "a-9"), moves=(("a-5", "a-9"),), caps={"a-5": 10, "a-9": 2})
    assert code == 0 and events == ["every planned host is finished"]
    assert fin.moved_undone(plan) == {"a-5"} and fin.watched(plan) == [] and fin.watched() == ["a-5"]
    started = dt.datetime(2026, 10, 27, tzinfo=dt.timezone.utc)
    a9 = fin.parse_utc(json.loads((kit.root / "hosts" / "a-9" / "pod.json").read_text())["cap_stop_utc"])
    assert fin.deadline(plan, started) == a9 + dt.timedelta(hours=3)
    plan["requeues"] = []
    a5 = fin.parse_utc(json.loads((kit.root / "hosts" / "a-5" / "pod.json").read_text())["cap_stop_utc"])
    assert fin.deadline(plan, started) == a5 + dt.timedelta(hours=3)          # unmoved: its cap counts, as before
    only = {"hosts": {"a-5": {"cap_hours": 3.0, "done": False}}, "deferrals": [{"from": "a-5", "to": None}]}
    assert fin.deadline(only, started) == started + dt.timedelta(hours=3)    # nothing left to wait for


@pytest.mark.parametrize("done, moves", [
    ({"a-1": True, "a-5": False}, ()),                       # not moved: it may still finish
    ({"a-1": True, "a-5": True}, (("a-5", "a-9"),))])        # moved but recorded done: not exempt
def test_k5_the_finisher_still_waits_for_an_unmoved_or_a_done_host_without_its_record(kit, monkeypatch, done, moves):
    """K5 the other way: a host without finished.json that is not moved, or that is moved but recorded done, is still
    watched; the first round does not end the finisher (it goes on to sleep)."""
    fin, plan, events, code = _watch(kit, monkeypatch, done, finished=("a-1",), moves=moves)
    assert code is None and "every planned host is finished" not in events
    assert fin.watched(plan) == ["a-5"] and fin.moved_undone(plan) == set()


# ===== K6: launch.py's exit code =====================================================================================

def _launch_main(w, monkeypatch, create_ok: bool, hosts=("s10-1",)):
    """launch.py main for ``hosts`` with fake children (reconcile and the guard pass; host.py create writes pod.json
    only when ``create_ok``) and a fake clock that sleep advances. Returns (exit, create calls, logged events)."""
    launch = importlib.import_module("launch")
    clock = [1_000_000.0]
    monkeypatch.setattr(launch, "time", types.SimpleNamespace(time=lambda: clock[0]))
    creates, logged, started = [], [], []

    def run(args, **kwargs):
        if args[1:3] == ["host.py", "create"]:
            creates.append(args[3])
            if create_ok:
                write_json(w.root / "hosts" / args[3] / "pod.json", {"id": f"pod-{args[3]}"})
            return subprocess.CompletedProcess(args, 0 if create_ok else 1, "", "create refused (synthetic 409)")
        return subprocess.CompletedProcess(args, 0, "{}", "")

    def sleep(seconds):
        clock[0] += seconds
    monkeypatch.setattr(launch, "log", lambda **f: logged.append(f))
    code = launch.main(list(hosts), run=run, popen=lambda *a, **k: started.append(a[0][4:6]), sleep=sleep)
    launch.kit_lock().close()                                    # the kit lock was released either way
    return code, creates, logged, started


def test_k6_launch_exits_non_zero_when_a_host_it_should_create_has_no_pod(w, monkeypatch):
    """K6 (cert runbook D7) both ways: every create refused for launch.py's 2 h (24 rounds, 300 s apart): exit 4 after
    the log line naming the host; a created host: exit 0, its after-create started, no such line. A host whose
    pod.json exists already: exit 0 and no create."""
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    code, creates, logged, started = _launch_main(w, monkeypatch, create_ok=False)
    assert code == 4 and creates == ["s10-1"] * 24 and started == []
    assert logged[-1] == {"event": "hosts-not-created", "hosts": ["s10-1"], "exit": 4}
    assert [f["event"] for f in logged].count("create-failed") == 24
    code, creates, logged, started = _launch_main(w, monkeypatch, create_ok=True)
    assert code == 0 and creates == ["s10-1"] and started == [["after-create", "s10-1"]]
    assert [f["event"] for f in logged] == ["created", "all hosts created"]
    code, creates, logged, started = _launch_main(w, monkeypatch, create_ok=False)
    assert (code, creates, [f["event"] for f in logged]) == (0, [], ["all hosts created"])
