"""The 7-8B kit's runner side on CPU, without RunPod, Hugging Face or GitHub (runkit/stage1-78b/; K2 of T4). This file
is the ADAPTATION of the stage-1 kit's tests/test_stage1_runner.py (2,712 lines at COPY-MANIFEST.json's source_head):
its synthetic pod becomes the block-0 pod of tests/test_kit_78b_runner.py (the Pod class there: K1's block-0 plan,
the family's main config, the sealed edit files, the preflight's two documents, a fake engine), and every logic test
of the runner's gate and records that applies at 7-8B is ported with its block-0 numbers: the dry run writes nothing
and prints exactly the calibrate commands; the per-job gate in order (deferral, crash, a missing or unreadable
heartbeat); every sealed input checked before use (a changed edit byte, a changed sealed file between jobs, an edit
file that does not hash to its job's SHA-256 and arm); the token, second-run and wrong-engine refusals; the per-job
engine record and cost ledger; K6's a0 fingerprint record both ways; every path the runner writes lies under host.py's
pull list; the finisher light-checks every host role; the kit's files compile and hold no secret.

Not ported, because the 7-8B copy has no such kind or path (the stage-1 tests stay in runkit/stage1-olmo/tests/
unchanged): J1-J18's command lines for the 1B kinds (W1-18, the regeneration and its LS-04 hold, the O-ext unit step,
D-2's J5/J8, J6's lists, C1-C3 and the C1 registry seed, c0, LN-15e's retrain and re-score, B10/B11 (the V/V' check,
K = 12, the certification gate), the similarity pass, the plant fingerprint), the O500 projection, the base-model
download, the X pack's S1 package and D-2 pins and the Y pack (pack_setup is K1's; the Y pack comes with KD9), the
W1-18 and branch gates of orchestrate (K3's), the judge wrapper and one device per contrast (the judge route,
unchanged by T4 step 5), the backup's 1B records (the states group is tested in test_kit_78b_runner.py)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import test_stage1_runkit as rk
from test_stage1_runkit import w, wf  # noqa: F401
from test_kit_78b_runner import H, KIT, PY, REAL_RUN, ROOT, SENTINELS, X, Pod, load_by_path, sha, write

RUNNER_FILES = ("orchestrate.py", "pack_setup.py", "probes.py", "backup_records_stage1.py", "judge_units_stage1.py",
                "finisher.py", "seal.py", "states_tool.py", "status.py", "setup/job_runner_stage1.py",
                "setup/preflight_stage1.py", "setup/download_models_stage1.py", "setup/extend_cap.py",
                "judge_pod_stage1/bundle.py")


@pytest.fixture
def kit(tmp_path, monkeypatch):
    """The stage-1 kit fixture's shape, kept by name for the copied test files that import it (tests/test_round31.py,
    tests/test_round33.py: the launch path's and the judge route's, K3's): a copy of the kit as a 7-8B working copy
    (tmp/tmp/family-probe-s78-olmo2-7b-0; ROOT = tmp) and a loader of its modules by relative path."""
    import importlib.util
    copy = tmp_path / "tmp" / "family-probe-s78-olmo2-7b-0"
    shutil.copytree(KIT, copy, ignore=shutil.ignore_patterns("__pycache__", "tests", "packed-*"))
    monkeypatch.syspath_prepend(str(copy))
    for name in rk.MODULES:
        monkeypatch.delitem(sys.modules, name, raising=False)

    def load(relative: str):
        spec = importlib.util.spec_from_file_location(f"s78kit_{Path(relative).stem}", copy / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    load.root, load.repo = copy, tmp_path
    yield load
    for name in rk.MODULES:
        sys.modules.pop(name, None)


def pulled(rel: str, items: str) -> bool:
    """host.py pull's rule, by hand: on the pod, ``cd RUN && ls -d ITEMS | tar -cf - -T -`` takes every top-level
    entry that a pattern of ITEMS matches (a shell glob), with everything under it."""
    import fnmatch
    return any(fnmatch.fnmatchcase(rel.split("/")[0], p) for p in items.split())


# ===== the dry run and the commands ===================================================================================
def test_the_dry_run_prints_exactly_the_calibrate_commands_and_writes_nothing(wf, monkeypatch, local_processes):
    w = wf
    pod = Pod(w, monkeypatch)
    before = sorted(str(p.relative_to(pod.root)) for p in pod.root.rglob("*"))
    done = REAL_RUN([PY, "-B", str(w.root / "setup" / "job_runner_stage1.py"), pod.host, "--dry-run"], cwd=pod.root,
                    capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr[-800:]
    assert sorted(str(p.relative_to(pod.root)) for p in pod.root.rglob("*")) == before    # --dry-run writes nothing
    out = json.loads(done.stdout)
    jobs = pod.plan["hosts"][pod.host]["jobs"]
    assert out["host"] == pod.host and out["engine"] == "X" and len(out["jobs"]) == len(jobs)
    for entry, job in zip(out["jobs"], jobs):
        assert [name for name, _ in entry["commands"]] == [f"job-{entry['index']}-calibrate"]
        argv = entry["commands"][0][1]
        arm = f"edit-{job['edit']['sha256']}" if job["kind"] == "arm" else "a0"
        edit = ["--edit", f"edits/{job['edit']['sha256']}.edit.json"] if job["kind"] == "arm" else []
        assert argv == ["venv/bin/python", "-m", "experiments.safety_selection", "calibrate", "--prepared", pod.prepared,
                        "--recipe", w.rules.REC, "--arms", arm, *edit, "--seeds", str(job["seed"]), "--checkpoints", "e1",
                        "--out-root", "round1"]
        assert entry["inputs"][:3] == [w.rules.REC, f"{pod.prepared}/manifest.json", f"{pod.prepared}/manifest.sha256"]
        if job["kind"] == "arm":
            assert entry["inputs"][3] == f"edits/{job['edit']['sha256']}.edit.json"
    assert not any(s in done.stdout for s in SENTINELS)


# ===== the per-job gate, in order ====================================================================================
def test_jobs_run_in_order_with_engine_records_and_cost_ledgers(w, monkeypatch):
    pod = Pod(w, monkeypatch)
    pod.remaining([20 * H])
    assert pod.main() == 0
    done = pod.done()
    assert pod.statuses() == ["complete"] * 3 and done["ok"] is True and done["stopped"] is None
    assert pod.receipts() == ["job-0-calibrate", "job-1-calibrate", "job-2-calibrate"]
    for rec in done["jobs"]:
        assert rec["engine"] == "X" and rec["engine_sha256"] == X and rec["job_id"] == "arm"
        ledger = json.loads((pod.root / f"job-{rec['index']}" / "cost-ledger.json").read_text())
        assert set(ledger["stages_s"]) == {"setup", "training", "greedy_generation", "sampled_generation", "judging",
                                           "scoring", "pod_overhead", "transform"}
        assert ledger["steps"][0]["name"] == f"job-{rec['index']}-calibrate" and ledger["stages_s"]["training"] >= 0
        assert rec["outputs"][f"job-{rec['index']}/cost-ledger.json"] == sha(pod.root / f"job-{rec['index']}" / "cost-ledger.json")
        assert ledger["slot_s"] >= 0 and ledger["engine_sha256"] == X and ledger["kind"] == "stage1 cost ledger"
        assert {"requirement_s", "remaining_s", "free_gb", "s_pod", "s_obs", "s", "s_obs_after", "utc", "ended_utc"} <= set(rec)
    assert sorted(p.name for p in (pod.root / "job-done").iterdir()) == [f"JOB-{i}.json" for i in range(3)]
    assert (pod.root / "round1").is_dir() and (pod.root / "jobs").is_dir()
    # the shorten at the end: extend_cap.py to 1 h when more remains (the last action; never extends)
    assert pod.ran[-1] == ["python3", "extend_cap.py", "3600"]


def test_a_job_that_does_not_fit_and_every_later_one_are_deferred_in_order(w, monkeypatch):
    pod = Pod(w, monkeypatch)
    first, second = (j["start_requirement_s"] for j in pod.plan["hosts"][pod.host]["jobs"][:2])
    pod.remaining([first + 1, second - 1, 10 * H])
    assert pod.main() == 0
    assert pod.statuses() == ["complete", "deferred", "deferred"] and pod.receipts() == ["job-0-calibrate"]
    deferral = json.loads((pod.root / "deferral.json").read_text())
    assert deferral["first_deferred"] == 1 and deferral["deferred"] == [1, 2] and deferral["reason"] == "remaining"
    assert deferral["requirement_s"] == pytest.approx(second) and deferral["remaining_s"] == second - 1
    assert pod.done()["stopped"] == "deferred" and pod.done()["ok"] is True
    assert pod.done()["jobs"][1]["reason"] == "remaining" and pod.done()["jobs"][2]["reason"] == "remaining"


@pytest.mark.parametrize("beat", ["missing", "unreadable"])
def test_a_missing_or_unreadable_heartbeat_stops_the_host(w, monkeypatch, beat):
    pod = Pod(w, monkeypatch)
    if beat == "unreadable":
        (w.repo / "heartbeat.json").write_text("{not json")
    assert pod.main() == 1
    assert pod.done()["stopped"] == "heartbeat_unreadable" and pod.statuses() == ["not_started"] * 3
    assert pod.receipts() == [] and not (pod.root / "deferral.json").exists()


def test_a_crash_stops_the_host_and_later_jobs_do_not_start(w, monkeypatch):
    pod = Pod(w, monkeypatch)
    pod.remaining([20 * H])
    pod.fail = {"job-1-calibrate": 1}
    assert pod.main() == 1
    assert pod.statuses() == ["complete", "crashed", "not_started"] and pod.done()["stopped"] == "crashed"
    assert pod.receipts() == ["job-0-calibrate", "job-1-calibrate"]
    assert pod.done()["jobs"][1]["why"] == "exit 1 in job-1-calibrate" and pod.done()["ok"] is False
    assert (pod.root / "job-1" / "cost-ledger.json").is_file()            # the crashed job's ledger is still written


def test_no_new_complete_json_or_a_failed_verify_is_a_crash(w, monkeypatch):
    pod = Pod(w, monkeypatch)
    pod.remaining([20 * H])
    real_run = pod.run

    def no_unit(args, **kwargs):
        done = real_run(args, **kwargs)
        if "calibrate" in args:
            for p in (pod.root / "round1").glob("*/COMPLETE.json"):
                p.unlink()
        return done
    monkeypatch.setattr(pod.runner.subprocess, "run", no_unit)
    assert pod.main() == 1
    assert pod.statuses() == ["crashed", "not_started", "not_started"] and pod.done()["jobs"][0]["why"] == "no new COMPLETE.json"
    w2 = rk.World(pod.w.repo / "w2", monkeypatch, w.family)
    pod2 = Pod(w2, monkeypatch)
    pod2.remaining([20 * H])
    real_run2 = pod2.run

    def bad_verify(args, **kwargs):
        if "verify" in args:
            pod2.ran.append(list(args))
            return subprocess.CompletedProcess(args, 1, "", "a listed file differs (synthetic)")
        return real_run2(args, **kwargs)
    monkeypatch.setattr(pod2.runner.subprocess, "run", bad_verify)
    assert pod2.main() == 1
    rec = pod2.done()["jobs"][0]
    assert pod2.statuses() == ["crashed", "not_started", "not_started"] and rec["why"] == "the unit's verify failed"
    assert rec["verified"]["exit"] == 1 and rec["unit"].startswith("round1/1101-edit-")


# ===== every sealed input checked before use =========================================================================
def test_a_changed_byte_in_the_edit_file_before_its_job_stops_the_host(w, monkeypatch):
    """The per-job check (between jobs, after the start-up check passed): the edit file of job 1 changed after job 0
    ran stops the host before job 1 (sealed_file_mismatch; job 1 and later not_started; nothing of job 1 runs)."""
    pod = Pod(w, monkeypatch)
    pod.remaining([20 * H])
    jobs = pod.plan["hosts"][pod.host]["jobs"]
    target = pod.root / f"edits/{jobs[1]['edit']['sha256']}.edit.json"
    real_run = pod.run

    def tamper_after_first(args, **kwargs):
        done = real_run(args, **kwargs)
        if "calibrate" in args and len(pod.receipts()) == 1:
            target.write_text(target.read_text() + "\n")
        return done
    monkeypatch.setattr(pod.runner.subprocess, "run", tamper_after_first)
    assert pod.main() == 1
    assert pod.statuses() == ["complete", "not_started", "not_started"] and pod.receipts() == ["job-0-calibrate"]
    done = pod.done()
    assert done["stopped"] == "sealed_file_mismatch" and done["ok"] is False
    assert done["jobs"][1]["sealed_mismatch"] == [f"edits/{jobs[1]['edit']['sha256']}.edit.json",
                                                  f"edits/{jobs[1]['edit']['sha256']}.edit.json (its arm)"]


def test_the_start_up_check_refuses_any_changed_sealed_file(w, monkeypatch):
    pod = Pod(w, monkeypatch)
    pod.remaining([20 * H])
    manifest = pod.root / pod.prepared / "manifest.json"
    text = manifest.read_text()
    manifest.write_text(text + " ")
    with pytest.raises(AssertionError, match="sealed file\\(s\\) missing or changed|prepared"):
        pod.main()
    manifest.write_text(text)
    sealed = pod.root / "sealed-files.json"
    sealed.write_text(sealed.read_text() + "\n")
    with pytest.raises(AssertionError, match="sealed-files.json differs from the plan"):
        pod.main()
    assert pod.receipts() == [] and not (pod.root / "JOB-DONE.json").exists()


def test_an_edit_file_must_hash_to_its_jobs_sha256_and_arm(w, monkeypatch):
    """sealed_check's second clause: a job whose edit entry names another engine arm than edit-<SHA-256 of the packed
    file> never runs (the file is sealed and unchanged, so only this clause sees it)."""
    pod = Pod(w, monkeypatch)
    pod.remaining([20 * H])
    plan = json.loads((pod.root / "plan.json").read_text())
    job = plan["hosts"][pod.host]["jobs"][0]
    job["edit"]["engine_arm"] = "edit-" + "9" * 64
    write(pod.root / "plan.json", plan)
    assert pod.runner.sealed_check(job, json.loads((pod.root / "sealed-files.json").read_text())["files"], pod.root) == \
        [f"edits/{job['edit']['sha256']}.edit.json (its arm)"]
    assert pod.main() == 1
    assert pod.statuses() == ["not_started"] * 3 and pod.receipts() == [] and pod.done()["stopped"] == "sealed_file_mismatch"
    clean = pod.plan["hosts"][pod.host]["jobs"][0]
    assert pod.runner.sealed_check(clean, json.loads((pod.root / "sealed-files.json").read_text())["files"], pod.root) == []
    assert pod.runner.sealed_check(clean, {}, pod.root)[:1] == [w.rules.REC]      # nothing sealed: every input named


def test_the_runner_refuses_a_token_a_second_run_and_a_wrong_engine(w, monkeypatch):
    pod = Pod(w, monkeypatch)
    pod.remaining([20 * H])
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", rk.fake_token())
    with pytest.raises(AssertionError, match="a token is present"):
        pod.main()
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN")
    token_file = w.repo / ".cache" / "huggingface" / "token"
    write(token_file, rk.fake_token())
    with pytest.raises(AssertionError, match="a token is present"):
        pod.main()
    token_file.unlink()
    plan = json.loads((pod.root / "plan.json").read_text())
    plan["hosts"][pod.host]["engine_sha256"] = "0" * 64
    write(pod.root / "plan.json", plan)
    with pytest.raises(AssertionError, match="not a pinned engine"):
        pod.main()
    plan["hosts"][pod.host]["engine_sha256"] = X
    plan["hosts"][pod.host]["jobs"][0]["engine"] = "Y"
    write(pod.root / "plan.json", plan)
    with pytest.raises(AssertionError, match="two engines on one pod"):
        pod.main()
    write(pod.root / "plan.json", pod.plan)
    assert pod.main() == 0 and pod.statuses() == ["complete"] * 3
    with pytest.raises(AssertionError, match="already ran its jobs"):
        pod.main()


# ===== the blinding walk over every stage-1 record the runner writes (the ported sentinel test) =======================
def test_no_printed_line_or_runner_record_holds_a_sentinel_value(w, monkeypatch, capsys):
    pod = Pod(w, monkeypatch)
    pod.remaining([30 * H])
    assert pod.main() == 0
    texts = [capsys.readouterr().out, *pod.texts()]
    assert len(texts) >= 8
    outcome = (pod.root / pod.done()["jobs"][0]["unit"] / "COMPLETE.json").read_text()
    assert SENTINELS[0] in outcome                                           # the fixture holds the sentinel ...
    for text in texts:
        assert not any(s in text for s in SENTINELS)                         # ... and nothing the kit wrote or printed


# ===== K6: the a0 fingerprint record, both ways ======================================================================
def test_k6_an_a0_arm_job_writes_its_readable_fingerprint_record_and_lists_it(w, monkeypatch):
    r = w.rules
    a0 = r.job_record("a0_arm", "a0", 1103, None, 38)
    pod = Pod(w, monkeypatch, jobs=[a0])
    pod.remaining([30 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"]
    rec = pod.done()["jobs"][0]
    rel, unit = "job-0/a0-adapter-fingerprint.json", "round1/1103-a0-e1-a1"
    assert rec["unit"] == unit and rec["outputs"][rel] == sha(pod.root / rel)
    assert json.loads((pod.root / rel).read_text()) == {
        "kind": "stage1 a0 adapter fingerprint", "version": 1, "job": 0, "arm": "a0", "seed": 1103, "unit": unit,
        "complete_sha256": sha(pod.root / unit / "COMPLETE.json"), "checkpoints": {"e1": "5" * 64, "q": None},
        "identity": {"manifest_sha256": pod.digest, "training_identity": r.TRAINING_IDENTITY}}
    assert (r.A0_FINGERPRINT_RECORD, r.A0_FINGERPRINT_KIND) == ("a0-adapter-fingerprint.json", "stage1 a0 adapter fingerprint")
    import fnmatch
    patterns = re.search(r"^READABLE_PATTERNS = \((.*)\)$", (w.root / "seal.py").read_text(), re.MULTILINE).group(1)
    assert any(fnmatch.fnmatch(r.A0_FINGERPRINT_RECORD, p.strip(' "')) for p in patterns.split(","))
    # an edit arm writes none
    w2 = rk.World(pod.w.repo / "w2", monkeypatch, w.family)
    pod2 = Pod(w2, monkeypatch)
    pod2.remaining([30 * H])
    assert pod2.main() == 0
    assert not any(k.endswith("adapter-fingerprint.json") for rec in pod2.done()["jobs"] for k in rec["outputs"])


def test_k6_a_state_fingerprint_that_is_not_complete_jsons_writes_no_record_and_the_unit_stands(w, monkeypatch):
    a0 = w.rules.job_record("a0_arm", "a0", 1103, None, 38)
    pod = Pod(w, monkeypatch, jobs=[a0])
    pod.state_fp = "6" * 64
    pod.remaining([30 * H])
    assert pod.main() == 0 and pod.statuses() == ["complete"]
    rec = pod.done()["jobs"][0]
    assert not (pod.root / "job-0" / "a0-adapter-fingerprint.json").exists()
    assert not any(k.endswith("adapter-fingerprint.json") for k in rec["outputs"])
    assert rec["a0_fingerprint_record"] == ("states/e1/state.json's adapter_fingerprint is not a SHA-256 equal to "
                                            "COMPLETE.json's e1 one")


# ===== every path the runner writes lies under host.py's pull list ===================================================
def test_every_unit_and_record_path_the_runner_writes_lies_under_the_pull_list(wf, monkeypatch):
    """Addendum §29 point 2 (the stage-1 kit's rule, kept): every file the pod writes (units, ledgers, job-done/,
    JOB-DONE.json, deferral.json, the receipts) and every unit and output path JOB-DONE.json records lies under
    host.py's PULL_ITEMS, the empty jobs/ folder too."""
    w = wf
    host = load_by_path("host78", w.root / "host.py")
    pod = Pod(w, monkeypatch)
    before = {str(p.relative_to(pod.root)) for p in pod.root.rglob("*") if p.is_file()}
    pod.remaining([1000 * H])
    assert pod.main() == 0 and set(pod.statuses()) == {"complete"}
    done = pod.done()["jobs"]
    written = {str(p.relative_to(pod.root)) for p in pod.root.rglob("*") if p.is_file()} - before
    units = {d["unit"] for d in done}
    recorded = units | {rel for d in done for rel in d.get("outputs") or {}}
    paths = written | recorded | set(pod.receipts())
    assert "JOB-DONE.json" in written and "job-done/JOB-0.json" in written and recorded <= paths
    assert {u.split("/")[0] for u in units} == {"round1"}
    assert [p for p in sorted(paths) if not pulled(p, host.PULL_ITEMS)] == []
    for folder in ("round1", "jobs", "job-done", "JOB-DONE.json", "deferral.json", "job-0", "job-0-calibrate",
                   "cuda-preflight-1", "PREFLIGHT-DONE.json"):
        assert pulled(folder, host.PULL_ITEMS), folder
    assert not pulled("elsewhere/1101-a0-e1-a1/COMPLETE.json", host.PULL_ITEMS)      # the check can fail


# ===== the finisher light-checks every host role =====================================================================
def _finisher_tree(kit_root: Path, fin, role: str):
    write(kit_root / "plan.json", {"hosts": {"h-1": {"role": role, "cap_hours": 8.5}}, "deferrals": [], "requeues": []})
    tree = kit_root / "retrieved" / "h-1" / "tree"
    unit = tree / "round1" / "1102-edit-x-e1-a1"
    listed = write(unit / "eval" / "e1" / "summary.json", {"u": SENTINELS[0]})
    write(unit / "COMPLETE.json", {"files": {"eval/e1/summary.json": sha(listed),
                                             "states/e1/adapter.safetensors": "0" * 64}})
    write(tree / "JOB-DONE.json", {"host": "h-1", "ok": True, "jobs": []})
    (kit_root / "hosts" / "h-1").mkdir(parents=True, exist_ok=True)
    return tree, listed


def _finish(fin, kit_root: Path, monkeypatch, tree, exit_code=0, states_ok=True) -> tuple[str, list]:
    calls = []

    def tool(*a):
        calls.append(a)
        if a[0] == "pull-states":                        # host.py pull-states prints its record line (K3's port)
            record = json.dumps({"file": "states-e1-20261105T120000Z.tar", "bytes": 1, "sha256": "0" * 64}) + "\n"
            return subprocess.CompletedProcess(a, 0 if states_ok else 1, record if states_ok else "", "unknown command")
        return subprocess.CompletedProcess(a, 0, "stopped", "")
    monkeypatch.setattr(fin, "tool", tool)
    monkeypatch.setattr(fin, "check_states", lambda host, cp: subprocess.CompletedProcess([], 0, "states verified: 1 units", ""))
    monkeypatch.setattr(fin, "unpack", lambda h: tree)
    monkeypatch.setattr(fin, "log", lambda **f: None)
    (kit_root / "hosts" / "h-1" / "finished.json").unlink(missing_ok=True)
    fin.finish("h-1", {"exit_code": exit_code})
    return json.loads((kit_root / "hosts" / "h-1" / "finished.json").read_text())["status"], calls


@pytest.mark.parametrize("role", ["arms", "job", "a-role-of-no-list"])
def test_the_finisher_light_checks_every_host_role_and_stops_in_every_case(w, monkeypatch, role):
    """Addendum §29 point 4 (kept): the finisher light-checks the pulled tree of every host, whatever its role. A good
    tree with a verified states pull is verified-and-stopped (its check in verified.jsonl; the model state left on the
    pod counted, not checked); a listed file that differs, a JOB-DONE.json that is not ok, a non-zero outer exit or a
    states pull that did not happen is review-needed-stopped. The pod is stopped in every case, after the states pull."""
    fin = load_by_path("fin78b", w.root / "finisher.py")
    tree, listed = _finisher_tree(w.root, fin, role)
    status, calls = _finish(fin, w.root, monkeypatch, tree)
    assert status == "verified-and-stopped" and calls[-3:] == [("pull-states", "h-1", "e1"), ("extend-cap", "h-1", "120"), ("stop", "h-1")]
    check = json.loads((w.root / "retrieved" / "h-1" / "verified.jsonl").read_text().splitlines()[-1])
    assert check["results"] == {"round1/1102-edit-x-e1-a1": {"exit": 0, "tail": "bad []; states left on the pod: 1"}}
    assert _finish(fin, w.root, monkeypatch, tree, exit_code=1)[0] == "review-needed-stopped"
    assert _finish(fin, w.root, monkeypatch, tree, states_ok=False)[0] == "review-needed-stopped"
    write(tree / "JOB-DONE.json", {"host": "h-1", "ok": False, "jobs": []})
    assert _finish(fin, w.root, monkeypatch, tree)[0] == "review-needed-stopped"
    write(tree / "JOB-DONE.json", {"host": "h-1", "ok": True, "jobs": []})
    listed.write_text("changed after the pod wrote it\n")
    status, calls = _finish(fin, w.root, monkeypatch, tree)
    assert status == "review-needed-stopped" and calls[-2:] == [("extend-cap", "h-1", "120"), ("stop", "h-1")]
    assert not any(s in (w.root / "retrieved" / "h-1" / "verified.jsonl").read_text() for s in SENTINELS)


# ===== the kit's files ==============================================================================================
def test_the_runner_files_compile_and_hold_no_secret(tmp_path):
    import py_compile
    for rel in RUNNER_FILES:
        py_compile.compile(str(KIT / rel), cfile=str(tmp_path / "x.pyc"), doraise=True)
    sys.path.insert(0, str(KIT))
    try:
        sys.modules.pop("secret_scan", None)
        import secret_scan
        assert secret_scan.scan_paths([KIT / rel for rel in (*RUNNER_FILES, "README.md", "RULES-78B.md",
                                                               "setup/setup_and_fetch_stage1.sh",
                                                               "tests/test_stage1_runner.py", "tests/test_kit_78b_runner.py",
                                                               "tests/mutation_spec_runner_78b.json",
                                                               "tests/run_mutants_runner_78b.py")]) == []
        assert secret_scan.scan_text(rk.fake_token()) == ["hf_token"]
    finally:
        sys.path.remove(str(KIT))
        sys.modules.pop("secret_scan", None)
    text = (KIT / "setup" / "job_runner_stage1.py").read_text()
    assert "stage1_rules.arm_commands" in text or "rules.arm_commands" in text
    assert "shutil.disk_usage" in text and "PROGRESS_FILE" in text
