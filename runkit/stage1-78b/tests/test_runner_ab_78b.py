"""R3 K3: the 7-8B kit's runner and pack for blocks A and B (plan-ab items 5a, 5c, 5e, 5f; the lead's build rulings GXB
T-O3, K-3, K-7, O4, O6, O10, R-5, R-6, R-9, R-16, R-18, R-20, R-21, R-31, R-33, R-44, R-47, R-53; KR4, KR5, KR8;
K2R2-1). On CPU, no pod, no network, no real process: working copies tmp/family-probe-s78-<family>-<block>/ of the
test Worlds of test_scorer_block_78b.py and test_planning_ab_78b.py (ROOT = tmp), every pin filled TEST-LOCALLY (the
committed pins stay null), every process a fake. Every unit, record and answer below is a synthetic stand-in; no
sealed list, edit, row, answer or real unit is read (the unchanged 1B oext_eval module is imported and fed synthetic
settings and records only). Expected values are written by hand.

    PYTHONDONTWRITEBYTECODE=1 PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests/test_runner_ab_78b.py
"""
from __future__ import annotations

import argparse
import importlib
import io
import json
import subprocess
import sys
import tarfile
import types
from pathlib import Path

import pytest

import test_planning_ab_78b as pab
import test_scorer_block_78b as sb
import test_stage1_runkit as rk

KIT = rk.KIT
REPO = KIT.parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SHARED_STOP = FIXTURES / "anchor_stop__olmo2-7b__safe_anchors_below_64.json"   # KR5: the one shared stop fixture
sha, hx, write, load_by_path, sc_plan, pod_oext, branch_record = (sb.sha, sb.hx, sb.write, sb.load_by_path, sb.sc_plan,
                                                                  sb.pod_oext, sb.branch_record)


@pytest.fixture
def wa(tmp_path, monkeypatch):
    world = pab.ABWorld(tmp_path, monkeypatch, "olmo2-7b", "A")
    yield world
    pab.close(world)


@pytest.fixture
def so(tmp_path, monkeypatch):
    world = sb.ScWorld(tmp_path, monkeypatch, "olmo2-7b")
    yield world
    for name in rk.MODULES:
        sys.modules.pop(name, None)


def ab_plan(w, job: dict, block: str = "A") -> dict:
    return {"family": w.family, "hosts": {"h": {"block": block, "engine": "X", "jobs": [job]}}, "recipes": {}}


def oext_inputs():
    return ({"oext_bank": hx("ob"), "oext_record": hx("or")},
            {"oext_bank": "inputs/oext_bank/b.json", "oext_record": "inputs/oext_record/r.json"})


def a0_job(seed: int = 1104) -> dict:
    return {"kind": "a0_arm", "arm": "a0", "seed": seed, "recipe": "B", "engine": "X", "edit": None, "family": "olmo2-7b"}


def fake_pod(root: Path, calls: list, oext_writes: bool = True):
    """A fake process runner for run_job: calibrate writes the unit (COMPLETE.json and states/e1/state.json with one
    fingerprint), the O-ext step writes one synthetic record (when ``oext_writes``), the engine's verify exits 0."""
    def fake(args, **kwargs):
        calls.append(list(args))
        if args[:2] != ["python3", "process_receipt.py"]:
            return subprocess.CompletedProcess(args, 0, "names only", "")
        argv = args[5:]
        if "calibrate" in argv:
            unit = root / "round1" / f"{argv[argv.index('--seeds') + 1]}-a0-e1-a1"
            write(unit / "COMPLETE.json", {"complete": True, "checkpoints": {"e1": {"adapter_fingerprint": hx("e1")}},
                                           "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("m")}})
            write(unit / "states" / "e1" / "state.json", {"adapter_fingerprint": hx("e1")})
        elif "unit" in argv and oext_writes:
            write(root / argv[argv.index("--out") + 1] / "oext_unit_record.json", {"kind": "oext (synthetic)"})
        return subprocess.CompletedProcess(args, 0, "", "")
    return fake


# ===== 1. blocks A and B: calibrate, then the wrapper's unit pass on the job's own e1 (plan-ab 5a, DES E3 (a)) =======
def test_5a_block_a_arm_jobs_run_calibrate_then_the_wrappers_unit_pass_on_their_own_e1_unit(wa, tmp_path, monkeypatch):
    w = wa
    runner = load_by_path("jr78_ab_cmd", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    pins, inputs = oext_inputs()
    doc = {"files": {}, "inputs": inputs}
    unit = pod_oext(w, monkeypatch, root, doc, pins, inputs)
    p, rec = f"data/kt-prepared/{w.rules.PREPARED_NAME}", w.rules.REC
    cmds = runner.job_commands(ab_plan(w, a0_job()), "h", 0, root, {}, doc)
    assert [n for n, _ in cmds] == ["job-0-calibrate", "job-0-oext"]
    assert cmds[0][1] == w.rules.arm_commands(a0_job(), p, w.family)[0][1]          # block 0's calibrate, unchanged
    assert cmds[1][1] == [*unit, "run", "--run", "@unit:0", "--checkpoint", "e1", "--prepared", p, "--recipe", rec,
                          "--oext-bank", inputs["oext_bank"], "--oext-record", inputs["oext_record"], "--out", "job-0/oext"]
    # block 0's route is unchanged: calibrate only, no O-ext step (R-3; plan-ab 5a's test_no_oext_in_block0)
    assert [n for n, _ in runner.job_commands(ab_plan(w, a0_job(1101), "0"), "h", 0, root, {}, doc)] == ["job-0-calibrate"]
    # the job's sealed files: the O-ext pin's files, the branch record and the packed bank and record
    paths = runner.sealed_paths(a0_job(), {"block": "A"}, 0, doc)
    for rel in (*w.r78.OEXT_78B[w.family]["files"], f"records/branch-{w.family}.json", *inputs.values()):
        assert rel in paths, rel
    assert not set(paths) & {f"records/branch-{w.family}.json"} - set(runner.sealed_paths(a0_job(), {"block": "B"}, 0, doc))
    assert f"records/branch-{w.family}.json" not in runner.sealed_paths(a0_job(1101), {"block": "0"}, 0, doc)
    # run_job: the O-ext step reads the calibrate's new unit; its outputs are hashed; an empty O-ext pass is a crash
    calls = []
    monkeypatch.setattr(runner.subprocess, "run", fake_pod(root, calls))
    got = runner.run_job(ab_plan(w, a0_job()), "h", 0, root, {}, {}, doc)
    assert got["status"] == "complete", got
    oext_call = next(c for c in calls if "unit" in c[5:])
    assert oext_call[oext_call.index("--run") + 1] == "round1/1104-a0-e1-a1"
    assert got["outputs"]["job-0/oext/oext_unit_record.json"] == sha(root / "job-0/oext/oext_unit_record.json")
    root2 = tmp_path / "pod2"
    doc2 = {"files": {}, "inputs": inputs}
    pod_oext(w, monkeypatch, root2, doc2, dict(pins), inputs)
    monkeypatch.setattr(runner.subprocess, "run", fake_pod(root2, [], oext_writes=False))
    got = runner.run_job(ab_plan(w, a0_job()), "h", 0, root2, {}, {}, doc2)
    assert got["status"] == "crashed" and got["why"] == "the O-ext pass wrote no output"


def test_5a_block_a_arm_jobs_refuse_on_the_pod_while_oext_78b_or_the_branch_record_is_null_or_off_its_pin(wa, tmp_path,
                                                                                                          monkeypatch):
    w = wa
    runner = load_by_path("jr78_ab_ref", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    pins, inputs = oext_inputs()
    doc = {"files": {}, "inputs": inputs}
    pod_oext(w, monkeypatch, root, doc, pins, inputs)
    plan = ab_plan(w, a0_job())
    good = w.r78.OEXT_78B[w.family]
    monkeypatch.setitem(w.r78.OEXT_78B, w.family, None)
    with pytest.raises(runner.Unrunnable, match=r"OEXT_78B\['olmo2-7b'\] is null"):
        runner.job_commands(plan, "h", 0, root, {}, doc)
    other = {**good, "files": {**good["files"], "scripts/scale78b/settings/OEXT-78B-Y__olmo2-7b.json": hx("y")}}
    monkeypatch.setitem(w.r78.OEXT_78B, w.family, other)
    with pytest.raises(runner.Unrunnable, match="is not in its form"):
        runner.job_commands(plan, "h", 0, root, {}, doc)
    monkeypatch.setitem(w.r78.OEXT_78B, w.family, good)
    branch = w.r78.BRANCH_78B[w.family]
    monkeypatch.setitem(w.r78.BRANCH_78B, w.family, None)
    with pytest.raises(runner.Unrunnable, match=r"branch record \(BRANCH_78B\) is null"):
        runner.job_commands(plan, "h", 0, root, {}, doc)
    monkeypatch.setitem(w.r78.BRANCH_78B, w.family, branch)
    (root / branch["path"]).write_text("changed")                                # the branch record off its pin
    with pytest.raises(runner.Unrunnable, match="the family's branch record is not packed at its pin"):
        runner.job_commands(plan, "h", 0, root, {}, doc)
    write(root / branch["path"], branch_record(w.family))
    bad = {**doc, "files": {**doc["files"], inputs["oext_bank"]: hx("another bank")}}
    with pytest.raises(runner.Unrunnable, match="the input 'oext_bank' is not packed at its pin"):
        runner.job_commands(plan, "h", 0, root, {}, bad)
    # the key check's second bank pin (SCOUT §1.3): the packed O-ext bank goes to check_keys, a wrong one refuses
    h = plan["hosts"]["h"]
    assert runner.oext_bank_key(a0_job(), h, doc) == pins["oext_bank"]
    assert runner.oext_bank_key(a0_job(1101), {**h, "block": "0"}, doc) is None
    assert runner.oext_bank_key(a0_job(), h, bad) == hx("another bank")
    with pytest.raises(w.r78.Refused, match="is not olmo2-7b's pinned O-ext bank"):
        w.r78.check_keys(w.family, "a0_arm", w.rules.REC_CONFIG_SHA256, w.r78.ENGINE_X, w.r78.GPU_NAME,
                         w.r78.MANIFESTS[w.family], dict(w.r78.BANK), runner.oext_bank_key(a0_job(), h, bad))


# ===== 2. the flags: --w1-18-record (R-47) and --dev100-source (5f) ===================================================
def w1_18_record_doc(passed: bool, settings_sha: str, cut: int = 128) -> bytes:
    return (json.dumps({"kind": "stage1 over-refusal checks", "version": 1, "provenance": {"settings_sha256": settings_sha},
                        "truncation_check": {"pass": passed},
                        "units": {"untuned": {"truncation": {"cap_tokens": cut}}}}, indent=1) + "\n").encode()


def test_r47_branch_full_from_a_failing_w1_18_record_needs_the_record_at_run_time_through_the_unchanged_oext_eval(
        tmp_path):
    """GXB R-47 (M): through the unchanged scripts/stage1_s1/oext_eval.py (prepare -> read_w1_18): settings whose
    Branch full pins a FAILING W1-18 record refuse an O-ext run without the record ("W1-18's record cannot be read") and
    read it when given; settings of "Branch full by default" (no record, a full_reason) refuse a record. So the flag is
    passed exactly when the branch record names a W1-18 record (rules_78b.oext_flags)."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    oe = importlib.import_module("scripts.stage1_s1.oext_eval")
    assert sha(Path(oe.__file__)) == "8c4290921f32a5b4596a0bc40235cc5cf1185f73eaabeaa625c43bd19ba77719"   # unchanged
    record = write(tmp_path / "overrefusal_checks__olmo2-7b.json", w1_18_record_doc(False, hx("w1 settings")).decode())

    def settings(branch, record_sha, reason):
        return oe.Settings({"cap": {"branch": branch, "cut_tokens": 128, "w1_18": {
            "record_sha256": record_sha, "record_kind": "stage1 over-refusal checks", "settings_sha256": hx("w1 settings"),
            "full_reason": reason}}}, hx("settings"))
    failing = settings("full", sha(record), None)
    with pytest.raises(oe.Refusal, match="W1-18's record cannot be read"):
        oe.prepare(failing, bank_path=tmp_path / "bank", record_path=tmp_path / "rec", w1_18_path=None)
    got = oe.read_w1_18(failing, record)
    assert (got.record_sha256, got.passed) == (sha(record), False)
    default = settings("full", None, "W1-18 was not built (Branch full by default)")
    assert oe.read_w1_18(default, None).record_sha256 is None
    with pytest.raises(oe.Refusal, match="the settings pin no W1-18 record"):
        oe.read_w1_18(default, record)


@pytest.mark.parametrize("branch,source,passed,flag,dev100", [
    ("full", "default", None, False, False),           # Branch full by default: no flag
    ("full", "w1_18", False, True, False),             # Branch full from a failing record: the record (R-47)
    ("128", "w1_18", True, True, True)])               # Branch 128: the record, and --dev100-source on a regenerated unit
def test_5f_the_flags_follow_the_pinned_branch_record(so, tmp_path, monkeypatch, branch, source, passed, flag, dev100):
    w = so
    runner = load_by_path(f"jr78_flags_{branch}_{source}", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    data = None if passed is None else w1_18_record_doc(passed, hx("w1 settings"))
    side_rel = "inputs/side_complete-a0-1101/COMPLETE.json"
    side = write(root / side_rel, {"complete": True, "checkpoints": {"e1": {"adapter_fingerprint": hx("e1")}}})
    pins, inputs = oext_inputs()
    pins["side_complete:a0:1101"], inputs["side_complete:a0:1101"] = sha(side), side_rel
    doc = {"files": {side_rel: sha(side)}, "inputs": inputs}
    record_sha = None if data is None else sb.hashlib.sha256(data).hexdigest()
    unit = pod_oext(w, monkeypatch, root, doc, pins, inputs, branch_record(w.family, branch, source, record_sha), data)
    rec_rel = w.r78.W1_18_RECORD_DIR + f"overrefusal_checks__{w.family}.json"
    o_only = {"kind": "o_only", "arm": "theta0", "seed": None, "recipe": "B", "engine": "X",
              "inputs": {n: pins[n] for n in ("oext_bank", "oext_record")}}
    cmd = runner.job_commands(sc_plan(w, o_only), "h", 0, root, {}, doc)[0][1]
    assert ("--w1-18-record" in cmd) is flag and "--dev100-source" not in cmd     # theta0 is never regenerated
    if flag:
        assert cmd[cmd.index("--w1-18-record") + 1] == rec_rel and cmd[:len(unit)] == unit
    regen = {"kind": "o_only_with_regenerate", "arm": "a0", "seed": 1101, "recipe": "B", "engine": "X",
             "inputs": {n: pins[n] for n in w.rules.sc_unit_input_names("o_only_with_regenerate", "a0", 1101)}}
    if dev100:                                          # Branch 128: the dev-100 source unit must be packed (LN-19)
        with pytest.raises(runner.Unrunnable, match="the dev-100 source unit 'source_unit:a0:1101' is not packed"):
            runner.job_commands(sc_plan(w, regen), "h", 0, root, {}, doc)
        src = "inputs/source_unit-a0-1101/1101-a0-e1-a1"
        (root / src).mkdir(parents=True)
        (root / src / "COMPLETE.json").write_bytes(side.read_bytes())
        doc["inputs"]["source_unit:a0:1101"] = src
        doc["files"][f"{src}/COMPLETE.json"] = sha(side)
    cmd = runner.job_commands(sc_plan(w, regen), "h", 0, root, {}, doc)[-1][1]
    assert ("--w1-18-record" in cmd) is flag and ("--dev100-source" in cmd) is dev100
    if dev100:
        assert cmd[cmd.index("--dev100-source") + 1] == "inputs/source_unit-a0-1101/1101-a0-e1-a1"
        doc["files"][f"{src}/COMPLETE.json"] = hx("another unit")             # the source unit off its pin
        with pytest.raises(runner.Unrunnable, match="'source_unit:a0:1101' is not packed at its pin"):
            runner.job_commands(sc_plan(w, regen), "h", 0, root, {}, doc)
    if flag:                                            # the O-ext pin names another record than the branch record
        good = w.r78.OEXT_78B[w.family]
        monkeypatch.setitem(w.r78.OEXT_78B, w.family, {**good, "files": {**good["files"], rec_rel: hx("other record")}})
        with pytest.raises(runner.Unrunnable, match="does not name the branch record's W1-18 record"):
            runner.job_commands(sc_plan(w, o_only), "h", 0, root, {}, doc)


# ===== 3. N's seven units (5e, DES E5) ===============================================================================
def test_5e_ns_r_unit_is_regenerated_on_its_sealed_edit_and_accepted_against_ns_unit(so, tmp_path, monkeypatch):
    w = so
    runner = load_by_path("jr78_n_regen", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    fam = w.family
    n_rel, e_rel = "inputs/n_complete-R-1101/COMPLETE.json", "inputs/regen_edit-R-1101/r_d1.edit.json"
    n_doc = {"complete": True, "checkpoints": {"e1": {"adapter_fingerprint": hx("n-e1")}},
             "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("m")}}
    n_file, e_file = write(root / n_rel, n_doc), write(root / e_rel, {"edit": "synthetic R_d1"})
    pins, inputs = oext_inputs()
    pins.update({"n_complete:R:1101": sha(n_file), "regen_edit:R:1101": sha(e_file)})
    inputs.update({"n_complete:R:1101": n_rel, "regen_edit:R:1101": e_rel})
    doc = {"files": {n_rel: sha(n_file), e_rel: sha(e_file)}, "inputs": inputs}
    unit = pod_oext(w, monkeypatch, root, doc, pins, inputs)
    names = w.rules.sc_unit_input_names("o_only_with_regenerate", "R", 1101)
    assert names == ("n_complete:R:1101", "regen_edit:R:1101", "oext_bank", "oext_record")
    job = {"kind": "o_only_with_regenerate", "arm": "R", "seed": 1101, "recipe": "B", "engine": "X",
           "inputs": {n: pins[n] for n in names}}
    p, rec = f"data/kt-prepared/{w.rules.PREPARED_NAME}", w.rules.REC
    cmds = [c for _, c in runner.job_commands(sc_plan(w, job), "h", 0, root, {}, doc)]
    eng = ["venv/bin/python", "-m", "experiments.safety_selection"]
    assert cmds[0] == eng + ["make-job", "run-one", "--prepared", p, "--recipe", rec, "--split", "dev", "--edit", e_rel,
                             "--seed", "1101", "--role", "development", "--target", "e1", "--pin-code", "--out",
                             "jobs/o_only_with_regenerate-1101-R-regen-a1.json"]
    assert cmds[1][-3:] == ["round1/1101-R-regen-a1", "--registry", "round1/registry.jsonl"]
    assert cmds[2] == [*unit, "run", "--run", "round1/1101-R-regen-a1", "--checkpoint", "e1", "--prepared", p, "--recipe",
                       rec, "--oext-bank", inputs["oext_bank"], "--oext-record", inputs["oext_record"], "--out", "job-0/oext"]
    # the acceptance input is N's unit (n_complete:R:1101), never a side unit of the same seed (the seed key)
    assert runner.accept_input(job) == "n_complete:R:1101"
    assert runner.accept_input({**job, "arm": "a0", "inputs": {}}) == "side_complete:a0:1101"
    calls = []

    def fake(args, **kwargs):
        calls.append(list(args))
        if args[:2] != ["python3", "process_receipt.py"]:
            return subprocess.CompletedProcess(args, 0, "names only", "")
        argv = args[5:]
        out = root / argv[argv.index("--out") + 1]
        if "make-job" in argv:
            write(out, {"job": "synthetic"})
        elif "unit" in argv:
            write(out / "oext_unit_record.json", {"kind": "oext (synthetic)"})
        else:
            write(out / "COMPLETE.json", n_doc)
            write(out / "states" / "e1" / "state.json", {"adapter_fingerprint": hx("n-e1")})
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(runner.subprocess, "run", fake)
    got = runner.run_sc_job(sc_plan(w, job), "h", 0, root, {}, {}, doc)
    assert got["status"] == "complete" and got["acceptance"] is True, got
    accept = json.loads((root / "job-0" / runner.ACCEPT_FILE).read_text())
    assert (accept["arm"], accept["seed"], accept["source"], accept["side_complete_sha256"]) == \
        ("R", 1101, "n_complete", sha(n_file))
    # N_UNITS null: the plan's input pins are null, so the job has no pin (A13) and the planner refuses before it
    values = w.r78.sc_pin_values(fam, w.pins78())
    assert values["N_UNITS"] is None
    assert w.rules.sc_unit_input_pins("o_only_with_regenerate", w.pins78(), values, "R", 1101)["n_complete:R:1101"] is None
    with pytest.raises(runner.Unrunnable, match="'n_complete:R:1101' has no pin in plan.json"):
        runner.job_commands(sc_plan(w, {**job, "inputs": {}}), "h", 0, root, {}, doc)


# ===== 4. W1-18: one pod, one check per family, each record by its R-53 name (5c; GXB O4, K-3, R-20, R-53) ==========
def w1_route(w, monkeypatch, root: Path, families, doc: dict) -> dict:
    """W1_18_78B TEST-LOCALLY in R-20's form for ``families``: the wrapper, each family's W1 index and W1-18 settings
    and Track P's two frozen readers (W2-5: any list in the form is accepted), files written on the pod; side units
    are KIT a0_units' (paths and pins compared as strings; no unit is read)."""
    files = {}
    for rel in (w.r78.OEXT_WRAPPER_78B, "scripts/family_probe_reading.py", "scripts/killtest_stage0_reading.py",
                *[f"scripts/scale78b/settings/OEXT-78B-W1__{f}.json" for f in families],
                *[f"scripts/scale78b/settings/limits_overrefusal_checks__{f}.json" for f in families]):
        files[rel] = sha(write(root / rel, f"# synthetic {rel}\n"))
    units = {f: {("untuned" if k == "untuned" else f"a0-{k}"): {"path": u["path"][len("tmp/"):],
                                                                "complete_sha256": u["complete_sha256"],
                                                                "job_sha256": u["job_sha256"]}
                 for k, u in w.r78.KIT[f]["a0_units"].items()} for f in families}
    route = {"files": files, "side_units": units}
    assert w.r78.w1_18_route_problem(route) is None
    monkeypatch.setattr(w.r78, "W1_18_78B", route)
    doc["files"].update(files)
    return route


@pytest.mark.parametrize("option", ["B", "C"])
def test_5c_the_w1_18_pod_runs_one_check_per_family_and_returns_each_record_as_overrefusal_checks_family(
        so, tmp_path, monkeypatch, option):
    w = so
    runner = load_by_path(f"jr78_w1_{option}", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    doc = {"files": {}, "inputs": {}}
    families = w.r78.W1_18_FAMILIES[option]
    job = {"kind": "w1_18", "arm": None, "seed": None, "recipe": "B", "engine": "X", "inputs": {},
           "families": list(families)}
    with pytest.raises(runner.Unrunnable, match="W1_18_78B is null"):
        runner.job_commands(sc_plan(w, job), "h", 0, root, {}, doc)
    route = w1_route(w, monkeypatch, root, families, doc)
    batch = {"olmo2-7b": 8, "llama31-8b": 6}                       # R-59: each family's MAIN_F guard block
    for f in families:
        write(root / w.r78.CONFIGS[f]["main"][0], {"guard": {"batch_size": batch[f]}})
    with pytest.raises(runner.Unrunnable, match="are not W1_18_78B's"):         # R-60: the gate's families only
        runner.job_commands(sc_plan(w, {**job, "families": ["olmo2-7b", "llama31-8b"][:3 - len(families)]}), "h", 0,
                            root, {}, doc)
    cmds = runner.job_commands(sc_plan(w, job), "h", 0, root, {}, doc)
    want = []
    for f in ("olmo2-7b", "llama31-8b")[:len(families)]:                         # the host family first
        idx = f"scripts/scale78b/settings/OEXT-78B-W1__{f}.json"
        want.append((f"job-0-w1-18-{f}", ["venv/bin/python", "-B", w.r78.OEXT_WRAPPER_78B, "w1_18", "--family", f,
                                         "--index", idx, "--index-sha256", route["files"][idx], "--out",
                                         f"job-0/w1-18-{f}", "--data-root", "data", "--device", "cuda",
                                         "--guard-batch-size", str(batch[f])]))
    assert cmds == want
    paths = runner.sealed_paths(job, {"block": "sc"}, 0, doc)
    assert set(route["files"]) <= set(paths) and "scripts/family_probe_reading.py" in paths
    assert f"data/{route['side_units']['olmo2-7b']['a0-1101']['path']}/COMPLETE.json" in paths   # a unit not packed

    def fake(args, **kwargs):
        argv = args[5:]
        f = argv[argv.index("--family") + 1]
        write(root / argv[argv.index("--out") + 1] / "overrefusal_checks.json", {"kind": "synthetic", "family": f})
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(runner.subprocess, "run", fake)
    got = runner.run_sc_job(sc_plan(w, job), "h", 0, root, {}, {}, doc)
    assert got["status"] == "complete", got
    for f in families:
        rel = f"job-0/overrefusal_checks__{f}.json"
        assert got["outputs"][rel] == sha(root / f"job-0/w1-18-{f}/overrefusal_checks.json") == \
            got["sc"]["records"][f]["sha256"]
    assert sorted(got["sc"]["records"]) == sorted(families)

    def fake_none(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(runner.subprocess, "run", fake_none)
    root2 = tmp_path / "pod-empty"
    doc2 = {"files": {}, "inputs": {}}
    w1_route(w, monkeypatch, root2, families, doc2)
    for f in families:
        write(root2 / w.r78.CONFIGS[f]["main"][0], {"guard": {"batch_size": batch[f]}})
    got = runner.run_sc_job(sc_plan(w, job), "h", 0, root2, {}, {}, doc2)
    assert got["status"] == "crashed" and got["why"] == "the W1-18 check of olmo2-7b wrote no overrefusal_checks.json"


# ===== 5. the pack's Mac checks before any O-ext pod (R-6, R-9, R-23) and the W1-18 pack (O4, K-3, O10) ===========
def test_r6_the_pack_runs_the_wrappers_check_on_the_pinned_index_and_w1_18_record_and_refuses_a_failure(so):
    w = so
    w.fill(oext=True)
    fam, r78 = w.family, w.r78
    idx = f"scripts/scale78b/settings/OEXT-78B__{fam}.json"
    w.pack(dry_run=True)
    assert w.checks == []                               # the dry run runs no check
    w.pack()
    assert w.checks == [[str(w.root.parents[1] / "tmp/minimal-experiment-20261002/venv/bin/python"), "-B",
                         r78.OEXT_WRAPPER_78B, "check", "--family", fam, "--engine", "X", "--index", idx,
                         "--index-sha256", r78.OEXT_78B[fam]["files"][idx]]]
    receipt = json.loads((w.root / "setup" / "packed-stage1-X" / "setup-receipt.json").read_text())
    assert receipt["oext_checks"] == [{"family": fam, "engine": "X", "index_sha256": r78.OEXT_78B[fam]["files"][idx],
                                       "args": [], "exit": 0}]
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    assert sealed["files"][f"records/branch-{fam}.json"] == r78.BRANCH_78B[fam]["sha256"]   # the pod reads it
    # a branch from a W1-18 record: the check takes the pinned record (R-6); the pack carries it at its R-21 place
    rec_rel = r78.W1_18_RECORD_DIR + f"overrefusal_checks__{fam}.json"
    data = w1_18_record_doc(True, hx("w1 settings"))
    (w.repo / rec_rel).parent.mkdir(parents=True, exist_ok=True)
    (w.repo / rec_rel).write_bytes(data)
    b = write(w.repo / "records" / f"branch-{fam}.json",
              branch_record(fam, "128", "w1_18", sb.hashlib.sha256(data).hexdigest()))
    w.mp.setitem(r78.BRANCH_78B, fam, {"path": f"records/branch-{fam}.json", "sha256": sha(b)})
    oext = r78.OEXT_78B[fam]
    w.mp.setitem(r78.OEXT_78B, fam, {**oext, "files": {**oext["files"], rec_rel: sha(w.repo / rec_rel)}})
    w.checks.clear()
    w.pack()
    assert w.checks[0][-2:] == ["--w1-18-record", rec_rel]
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    assert sealed["files"][rec_rel] == sha(w.repo / rec_rel)
    # R-77 (V-04): Branch full from a FAILING W1-18 record (R-47) also takes the pinned record in the Mac check
    data_fail = w1_18_record_doc(False, hx("w1 settings"))
    (w.repo / rec_rel).write_bytes(data_fail)
    b = write(w.repo / "records" / f"branch-{fam}.json",
              branch_record(fam, "full", "w1_18", sb.hashlib.sha256(data_fail).hexdigest()))
    w.mp.setitem(r78.BRANCH_78B, fam, {"path": f"records/branch-{fam}.json", "sha256": sha(b)})
    w.mp.setitem(r78.OEXT_78B, fam, {**oext, "files": {**oext["files"], rec_rel: sha(w.repo / rec_rel)}})
    w.checks.clear()
    sb.shutil.rmtree(w.root / "setup" / "packed-stage1-X")
    w.pack()
    assert w.checks[0][-2:] == ["--w1-18-record", rec_rel]
    # R-78: a pinned branch record that is missing refuses cleanly before any check
    (w.repo / "records" / f"branch-{fam}.json").unlink()
    sb.shutil.rmtree(w.root / "setup" / "packed-stage1-X")
    with pytest.raises(SystemExit, match="branch record: the record's bytes do not hash"):
        w.pack()
    write(w.repo / "records" / f"branch-{fam}.json",
          branch_record(fam, "full", "w1_18", sb.hashlib.sha256(data_fail).hexdigest()))
    w.check_exit = 2                                     # any refusal of the check refuses the pack
    with pytest.raises(SystemExit, match=r"refused \(exit 2\): refused before any O-ext pod"):
        w.pack()


def test_r9_k3_the_w1_18_pack_checks_each_familys_side_units_and_packs_them_with_the_other_familys_prepared_set(so):
    w = so
    fam, r78 = w.family, w.r78
    doc = {"files": {}, "inputs": {}}
    for f in ("olmo2-7b", "llama31-8b"):                # synthetic side units at KIT a0_units' paths (test-local pins)
        for k, u in r78.KIT[f]["a0_units"].items():
            folder = w.repo / u["path"]
            c = write(folder / "COMPLETE.json", {"complete": True, "unit": f"{f}-{k} (synthetic)"})
            j = write(folder / "job.json", {"job": f"{f}-{k} (synthetic)"})
            write(folder / "eval" / "e1" / "generations.jsonl", json.dumps({"text": sb.SENTINELS[0]}) + "\n")
            w.mp.setitem(u, "complete_sha256", sha(c))
            w.mp.setitem(u, "job_sha256", sha(j))
    route = w1_route(w, w.mp, w.repo, ("olmo2-7b", "llama31-8b"), doc)
    lprep = w.repo / "tmp" / "kt-prepared" / r78.KIT["llama31-8b"]["prepared_name"]
    write(lprep / "manifest.sha256", r78.MANIFESTS["llama31-8b"] + "\n")
    write(lprep / "manifest.json", {"kind": "prepared (synthetic)", "rows": 4800})
    w.pack_flags = ["--w1-18"]
    w.pack()
    out = w.root / "setup" / "packed-stage1-X"
    assert [c[3:8] for c in w.checks] == [["check", "--family", f, "--engine", "W1"] for f in ("llama31-8b", "olmo2-7b")]
    assert all(c[-2:] == ["--data-root", str(w.repo / "tmp")] for c in w.checks)
    sealed = json.loads((out / "sealed-files.json").read_text())
    for rel, digest in route["files"].items():
        assert sealed["files"][rel] == digest
    for f, units in route["side_units"].items():
        for u in units.values():
            assert sealed["files"][f"data/{u['path']}/COMPLETE.json"] == u["complete_sha256"]
            assert f"data/{u['path']}/eval/e1/generations.jsonl" in sealed["files"]
    assert sealed["files"][f"data/kt-prepared/{r78.KIT['llama31-8b']['prepared_name']}/manifest.json"] == \
        sha(lprep / "manifest.json")
    assert json.loads((out / "setup-receipt.json").read_text())["w1_18"] is True
    probe = json.loads((out / "probe.json").read_text())                # R-66: Llama's tokenizer on OLMo's pod ([B])
    assert [e for e in probe["plan"] if e["role"].startswith("tokenizer:")] == [
        {"role": "tokenizer:llama31-8b", "repo_id": r78.KIT["llama31-8b"]["instruct_model"]["repo_id"],
         "revision": r78.KIT["llama31-8b"]["instruct_model"]["revision"], "gated": True,
         "patterns": list(w.rules.TOKENIZER_FILES)}]
    assert any(e["role"] == "guard" for e in probe["plan"])            # the guard model, in every host's plan
    # refusals: a side unit off its pin; the W1-18 pod in the other family's copy is K-3's refusal (w1_18_host_problem)
    shutil = sb.shutil
    shutil.rmtree(out)
    u = r78.KIT["llama31-8b"]["a0_units"][1101]
    write(w.repo / u["path"] / "job.json", {"job": "changed"})
    with pytest.raises(SystemExit, match="W1-18 unit a0-1101: the unit folder is missing or its COMPLETE.json"):
        w.pack()
    assert r78.w1_18_host_problem("llama31-8b") is not None


# ===== 6. the anchor stop on the pod and in the pack (KR4, KR5, KR8, O6) ===========================================
def stop_record(w, root: Path, done_bytes: bytes = b'{"host": "anchor pod (synthetic)"}\n') -> tuple[dict, Path, Path]:
    done = root / "inputs" / "anchor_job_done" / "JOB-DONE.json"
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_bytes(done_bytes)
    doc = w.r78.anchor_stop_record(w.family, 3, None, sha(done), {"kept": 61, "needed": 64})
    stop = write(root / "records" / f"anchor-stop__{w.family}.json", doc)
    return doc, stop, done


def test_kr4_the_runner_reads_the_packed_stop_record_before_check_keys_and_refuses_without_it(so, tmp_path):
    w = so
    runner = load_by_path("jr78_kr4", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    doc, stop, done = stop_record(w, root)
    rel_stop, rel_done = "inputs/anchor_stop/" + stop.name, "inputs/anchor_job_done/JOB-DONE.json"
    (root / rel_stop).parent.mkdir(parents=True, exist_ok=True)
    (root / rel_stop).write_bytes(stop.read_bytes())
    sealed = {"files": {rel_stop: sha(stop), rel_done: sha(done)}, "inputs": {"anchor_stop": rel_stop,
                                                                             "anchor_job_done": rel_done}}
    assert runner.anchor_stop_check(w.family, root, sealed) is None                # not stopped: nothing to read
    w.mp.setitem(w.r78.ANCHOR_STOP, w.family, {"path": f"records/{stop.name}", "sha256": sha(stop)})
    with pytest.raises(w.r78.Refused, match="has not been read at the pin and checked"):
        w.r78.family_stopped(w.family)                  # before the runner's read: neither stopped nor normal
    assert "is not packed" in runner.anchor_stop_check(w.family, root, {"files": {}, "inputs": {}})
    other = write(root / "inputs" / "anchor_job_done" / "OTHER.json", {"host": "another job"})
    wrong = {"files": {**sealed["files"], "inputs/anchor_job_done/OTHER.json": sha(other)},
             "inputs": {**sealed["inputs"], "anchor_job_done": "inputs/anchor_job_done/OTHER.json"}}
    assert "not the anchor job's" in runner.anchor_stop_check(w.family, root, wrong)   # KR8: its own JOB-DONE.json
    assert runner.anchor_stop_check(w.family, root, sealed) is None
    assert w.r78.family_stopped(w.family) is True       # the MAIN_F retrain's check_keys can now run
    assert w.r78.sc_recipe(w.family, "retrain") == "B"
    # the anchor step's stderr is a file of the pulled tree: process_receipt's job-I-anchor/process.log, under job-*
    host = importlib.import_module("host")
    assert "job-*" in host.PULL_ITEMS.split()
    anchor = {"kind": "anchor", "arm": None, "seed": None, "recipe": "B", "engine": "X",
              "inputs": {"anchor_prompts": hx("prompts")}}
    prompts = write(root / "inputs/anchor_prompts/p.json", {"kind": "synthetic"})
    adoc = {"files": {"inputs/anchor_prompts/p.json": hx("prompts")}, "inputs": {"anchor_prompts": "inputs/anchor_prompts/p.json"}}
    assert prompts.is_file()
    assert [n for n, _ in runner.job_commands(sc_plan(w, anchor), "h", 0, root, {}, adoc)] == ["job-0-anchor"]


def test_kr5_the_shared_stop_fixture_is_read_by_rks_checker_k2s_writer_form_and_blinded_sigmas_reader(tmp_path):
    """KR5 (GXB R-26): the one shared fixture tests/fixtures/anchor_stop__olmo2-7b__safe_anchors_below_64.json is
    accepted by rules_78b's checker for its family and its JOB-DONE.json SHA-256, is exactly the form K2's writer
    (anchor_stop_record) gives from its own fields, and is read by scripts/scale78b/blinded_sigma.py's check_anchor_stop
    by path and SHA-256; another family's reading refuses in both."""
    r78 = load_by_path("rules_78b_kr5", KIT / "rules_78b.py")
    doc = json.loads(SHARED_STOP.read_text())
    assert r78.anchor_stop_problem(doc, "olmo2-7b", doc["job_done_sha256"]) is None
    assert r78.anchor_stop_problem(doc, "llama31-8b") is not None
    assert r78.anchor_stop_record("olmo2-7b", doc["exit_code"], None, doc["job_done_sha256"], doc["counts"]) == doc
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    bs = load_by_path("blinded_sigma_kr5", REPO / "scripts" / "scale78b" / "blinded_sigma.py")
    ref = {"path": SHARED_STOP.name, "sha256": sha(SHARED_STOP)}
    bs.check_anchor_stop("olmo2-7b", ref, FIXTURES)
    with pytest.raises(SystemExit):
        bs.check_anchor_stop("llama31-8b", ref, FIXTURES)


def test_kr4_the_pack_carries_the_stop_record_and_its_job_done_and_refuses_without_them(so):
    w = so
    fam = w.family
    doc, stop, done = stop_record(w, w.repo / "anchor")
    w.mp.setitem(w.r78.ANCHOR_STOP, fam, {"path": str(stop.relative_to(w.repo)), "sha256": sha(stop)})
    with pytest.raises(SystemExit, match="name 'anchor_job_done', the anchor job's JOB-DONE.json"):
        w.pack()
    other = write(w.repo / "anchor" / "other" / "JOB-DONE.json", {"host": "another job"})
    with pytest.raises(SystemExit, match="'anchor_job_done''s SHA-256 is not its pin"):
        w.pack(("anchor_job_done", other, sha(other)))
    w.pack(("anchor_job_done", done, sha(done)))
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    assert sealed["inputs"]["anchor_stop"] == f"inputs/anchor_stop/{stop.name}"
    assert sealed["files"][sealed["inputs"]["anchor_stop"]] == sha(stop)
    assert sealed["files"][sealed["inputs"]["anchor_job_done"]] == sha(done)


# ===== 7. R-44 at the pack receipt; K-7's edits by exact path and SHA-256 (block A) ==================================
def test_r44_the_pack_receipt_rehashes_the_blinding_records_files_and_bundle_members(wa, tmp_path):
    w = wa
    pack = importlib.import_module("pack_setup")
    assert pack.blinding_check({}, tmp_path / "none.tar.gz") is None                # no plan.json snapshot yet: None
    rec = w.blinding()
    named = json.loads(rec.read_text())["files"]
    write(w.root / "plan.json", {"blocks": {"A": {"blinding": {"path": w.rel(rec), "sha256": sha(rec)}}}, "hosts": {}})
    bundle = tmp_path / "bundle.tar.gz"

    def tar(members: dict):
        if bundle.exists():
            bundle.unlink()
        with tarfile.open(bundle, "w:gz") as archive:
            for name, data in members.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
    bs = "scripts/scale78b/blinded_sigma.py"
    tar({bs: (w.repo / bs).read_bytes(), "other.py": b"x"})
    got = pack.blinding_check({}, bundle)
    assert got["bundle_members"] == {bs: named[bs]} and got["files"] == named
    assert got["not_in_bundle"] == sorted(set(named) - {bs})
    tar({bs: b"# changed after the verification\n"})
    with pytest.raises(SystemExit, match="R-44: the packed scripts/scale78b/blinded_sigma.py is not the file"):
        pack.blinding_check({}, bundle)
    tar({})
    (w.root / "plan_tool.py").write_text((w.root / "plan_tool.py").read_text() + "\n# a later edit\n")
    with pytest.raises(SystemExit, match="R-44: runkit/stage1-78b/plan_tool.py is not the file the blinding record"):
        pack.blinding_check({}, bundle)


def test_k7_block_a_packs_each_jobs_edit_by_its_exact_path_and_sha256_only(wa):
    w = wa
    pack = importlib.import_module("pack_setup")
    s1 = w.r78.METHOD_EDITS["olmo2-7b"]["S1"]           # OLMo-2-7B's S1 edit under tmp/stage1-olmo/ (K-7)
    assert s1["path"].startswith("tmp/stage1-olmo/")
    fixture = write(w.repo / s1["path"], {"edit": "synthetic stand-in at the S1 edit's exact path"})
    w.mp.setitem(w.r78.METHOD_EDITS["olmo2-7b"], "S1", {**s1, "sha256": sha(fixture)})
    jobs = [{"kind": "arm", "arm": "S1", "seed": 1104, "edit": {"path": s1["path"], "sha256": sha(fixture)}},
            {"kind": "a0_arm", "arm": "a0", "seed": 1104, "edit": None}]
    write(w.root / "plan.json", {"hosts": {}, "blocks": {"A": {"pending": {"a-1": {"block": "A", "jobs": jobs}}}}})
    got = pack.ab_edits("olmo2-7b")
    assert got == {f"edits/{sha(fixture)}.edit.json": (w.repo / s1["path"], sha(fixture))}
    packing = pack.Packing()
    for rel, (src, digest) in got.items():
        packing.add(rel, src, digest)
    assert packing.bad == []
    name = f"edits/{sha(fixture)}.edit.json"
    write(w.repo / s1["path"], {"edit": "changed"})
    packing = pack.Packing()
    for rel, (src, digest) in got.items():
        packing.add(rel, src, digest)
    assert packing.bad == [name]
    (w.root / "plan.json").unlink()
    with pytest.raises(SystemExit, match="plan.json is missing"):
        pack.ab_edits("olmo2-7b")


# ===== 8. engine Y's pack and KD9's re-measure record (X1, PP18, ADD A13, KD9) ========================================
def y_tree(w) -> Path:
    """A synthetic frozen Y tree (the fake engine tree's files and the main config), with YHASH TEST-LOCALLY listing
    every file of it; and a 1B-style oext_unit.py copy in it, which the pack must never ship (r1-o-verify.md P3)."""
    tree = w.repo / w.rules.Y_TREE_DEFAULT
    for f in sorted((w.repo / "experiments").rglob("*")):
        if f.is_file():
            dest = tree / f.relative_to(w.repo)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(f.read_bytes())
    (tree / "scripts").mkdir(parents=True, exist_ok=True)
    for f in sorted((w.repo / "scripts").glob("cuda_preflight*.py")):
        (tree / "scripts" / f.name).write_bytes(f.read_bytes())
    write(tree / "scripts/stage1_s1/oext_unit.py", "# the 1B Y copy (synthetic): never packed at 7-8B\n")
    lines = [f"{sha(f)}  {f.relative_to(tree).as_posix()}" for f in sorted(tree.rglob("*")) if f.is_file()]
    yhash = write(w.repo / w.rules.YHASH_PIN["path"], "\n".join(lines) + "\n")
    w.mp.setitem(w.rules.YHASH_PIN, "sha256", sha(yhash))
    return tree


def test_x1_engine_ys_pack_refuses_while_engine_y_is_null_and_packs_the_frozen_tree_by_yhash_and_its_identity(so):
    w = so
    w.pack(dry_run=True)                                 # the World's fakes (engine X's tree, the config hashes)
    pack = importlib.import_module("pack_setup")
    with pytest.raises(SystemExit, match=r"engine Y's pack: engine Y's pin is null \(ENGINE_Y\)"):
        pack.main(["Y"])
    tree = y_tree(w)
    w.mp.setattr(w.r78, "ENGINE_Y", sb.Y)
    w.mp.setattr(pack, "engine_code", lambda t: sb.Y if Path(t) == tree else sb.X)
    with pytest.raises(SystemExit) as info:              # argparse's usage error: --y-tree belongs to engine Y
        pack.main(["X", "--y-tree", str(tree)])
    assert info.value.code == 2
    pack.main(["Y"])                                     # the default tree tmp/engine-y-34bfd288
    out = w.root / "setup" / "packed-stage1-Y"
    receipt = json.loads((out / "setup-receipt.json").read_text())
    assert (receipt["engine"], receipt["engine_sha256"], receipt["git_commit"]) == ("Y", sb.Y, None)
    with tarfile.open(out / "bundle-stage1-Y.tar.gz") as archive:
        names = archive.getnames()
        manifest = json.loads(archive.extractfile("bundle-manifest.json").read())
    assert manifest["yhash"] == w.rules.YHASH_PIN and manifest["engine_sha256"] == sb.Y
    assert "scripts/stage1_s1/oext_unit.py" not in names or \
        manifest["files"]["scripts/stage1_s1/oext_unit.py"] != sha(tree / "scripts/stage1_s1/oext_unit.py")
    sb.shutil.rmtree(out)
    (tree / "experiments/safety_selection/README.md").write_text("changed after YHASH")
    with pytest.raises(SystemExit, match="the Y tree fails YHASH: 1 file"):
        pack.main(["Y"])
    w.mp.setattr(pack, "engine_code", lambda t: sb.X)
    (tree / "experiments/safety_selection/README.md").write_bytes(
        (w.repo / "experiments/safety_selection/README.md").read_bytes())
    with pytest.raises(SystemExit, match="is not ENGINE_Y's pin"):
        pack.main(["Y"])


def test_x1_the_y_pack_ships_the_unchanged_oext_unit_from_this_checkout_after_the_y_check(so):
    w = so
    w.pack(dry_run=True)
    pack = importlib.import_module("pack_setup")
    tree = y_tree(w)
    fam = w.family
    w.mp.setattr(w.r78, "ENGINE_Y", sb.Y)
    w.mp.setattr(pack, "engine_code", lambda t: sb.Y if Path(t) == tree else sb.X)
    unit_rel, idx = "scripts/stage1_s1/oext_unit.py", f"scripts/scale78b/settings/OEXT-78B-Y__{fam}.json"
    files = {w.r78.OEXT_WRAPPER_78B: sha(write(w.repo / w.r78.OEXT_WRAPPER_78B, "# synthetic wrapper\n")),
             idx: sha(write(w.repo / idx, {"index": f"synthetic {fam} Y"})), unit_rel: sha(REPO / unit_rel)}
    (w.repo / unit_rel).parent.mkdir(parents=True, exist_ok=True)
    (w.repo / unit_rel).write_bytes((REPO / unit_rel).read_bytes())               # the unchanged 1B file
    w.mp.setitem(w.r78.OEXT_78B_Y, fam, {"files": files, "inputs": {"oext_bank": hx("ob"), "oext_record": hx("or")}})
    w.checks = []
    pack.main(["Y"])
    out = w.root / "setup" / "packed-stage1-Y"
    sealed = json.loads((out / "sealed-files.json").read_text())
    assert sealed["files"][unit_rel] == sha(REPO / unit_rel) != sha(tree / unit_rel)   # ROOT's, the wrapper's CODE pin
    assert [c[3:8] for c in w.checks] == [["check", "--family", fam, "--engine", "Y"]]   # R-23: under Y's identity


def test_kd9_a_y_pod_records_its_re_measure_and_measured_kinds_stay_refused_on_y_until_y_measured(so, tmp_path):
    w = so
    runner = load_by_path("jr78_kd9", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    unit = "rescore/1101-a0-retrain-a1"
    c = write(root / unit / "COMPLETE.json", {"complete": True, "evaluation": {"u": sb.SENTINELS[2]}})
    (root / unit / "progress.jsonl").write_text(json.dumps({"kind": "generate", "elapsed_s": 41.5, "rows": 32, "capped": 2,
                                                           "text": sb.SENTINELS[0]}) + "\n")
    ledger = write(root / "job-0" / "cost-ledger.json", {"stages_s": {"training": 900.5}, "slot_s": 1000.0})
    pre = {"training_s": 952.03, "ms_per_step_full": 25000.0}
    verification = {"cap_projection": {"untuned_projected_s": 2337.4, "training_s": 952.03},
                    "environment": {"cuda": {"name": w.r78.GPU_NAME}}}
    job = {"kind": "retrain", "arm": "a0", "seed": 1101, "engine": "Y"}
    rel = runner.y_remeasure_record(root, 0, job, w.family, sb.Y, pre, verification, "job-0/cost-ledger.json",
                                    {"unit": unit, "complete_sha256": sha(c)})
    doc = json.loads((root / rel).read_text())
    assert rel == "job-0/y-remeasure.json" and doc["kind"] == "stage1-78b engine-Y re-measure"
    assert (doc["engine_sha256"], doc["gpu"], doc["ledger_sha256"], doc["complete_sha256"]) == \
        (sb.Y, w.r78.GPU_NAME, sha(ledger), sha(c))
    assert doc["preflight"] == {"training_s": 952.03, "ms_per_step_full": 25000.0, "untuned_projected_s": 2337.4}
    assert doc["progress"] == [{"kind": "generate", "elapsed_s": 41.5, "rows": 32, "capped": 2}]
    text = (root / rel).read_text()
    assert not any(s in text for s in sb.SENTINELS)       # no U, no answer text
    w.mp.setattr(w.r78, "ENGINE_Y", sb.Y)                 # measured kinds refuse on Y until the re-measure's step
    assert w.r78.engine_allowed("retrain", sb.Y) and not w.r78.engine_allowed("arm", sb.Y)
    assert not w.r78.engine_allowed("a0_arm", sb.Y) and not w.r78.engine_allowed("ref_train", sb.Y)
    w.mp.setattr(w.r78, "Y_MEASURED", True)
    assert not w.r78.engine_allowed("arm", sb.Y)          # R-67: the measured record's pin too
    w.mp.setattr(w.r78, "Y_MEASURED_RECORD", {"path": "records/y-measured.json", "sha256": hx("ymr")})
    assert w.r78.engine_allowed("arm", sb.Y)


# ===== 9. item 13: the references in block B through refs_78b.py (Part 2 §3.2, §16.1; GXB O2, X2, R-35, R-41) =======
@pytest.fixture
def wb(tmp_path, monkeypatch):
    world = pab.ABWorld(tmp_path, monkeypatch, "olmo2-7b", "B")
    yield world
    pab.close(world)


def refs_pod(w, monkeypatch, root: Path, seed: int = 1104, verdict: str = "pass") -> tuple[dict, dict, list]:
    """On a synthetic pod folder: OEXT_78B[F], the branch record (pod_oext), REFS_78B[F][S] TEST-LOCALLY (the refs
    wrapper and the seed's index written), and the seed's named inputs: S's a0 unit COMPLETE.json, its eval/e1 folder,
    S's certification report (``verdict``) and the safety-prompt file (REF_PREFIX_SHA256 patched to its bytes).
    Returns (the sealed doc, the job input pins, the refs wrapper's leading argv for eval_adapter)."""
    fam, r78 = w.family, w.r78
    pins, inputs = oext_inputs()
    doc = {"files": {}, "inputs": inputs}
    pod_oext(w, monkeypatch, root, doc, pins, inputs)
    idx = f"scripts/scale78b/settings/REFS-78B__{fam}__{seed}.json"
    files = {r78.REFS_WRAPPER_78B: sha(write(root / r78.REFS_WRAPPER_78B, "# synthetic refs wrapper\n")),
             idx: sha(write(root / idx, {"index": f"synthetic {fam} {seed}"}))}
    monkeypatch.setitem(r78.REFS_78B[fam], seed, {"files": files, "inputs": {n: pins[n] for n in r78.OEXT_INPUTS}})
    doc["files"].update(files)
    named = {f"gate_a_complete:{seed}": write(root / f"inputs/gate_a_complete-{seed}/COMPLETE.json", {"complete": True}),
             f"certification_report:{seed}": write(root / f"inputs/certification_report-{seed}/{seed}-certify.compare.json",
                                                    {"verdict": verdict}),
             "prefix_file": write(root / "inputs/prefix_file/safety_prompt.txt", "SENTINEL-PROMPT-TEXT (synthetic)\n")}
    monkeypatch.setattr(r78, "REF_PREFIX_SHA256", sha(named["prefix_file"]))
    job_pins = {}
    for name, f in named.items():
        rel = f.relative_to(root).as_posix()
        doc["inputs"][name], doc["files"][rel], job_pins[name] = rel, sha(f), sha(f)
    ev = write(root / f"inputs/gate_a_eval-{seed}/e1/summary.json", {"u": sb.SENTINELS[2]})
    doc["inputs"][f"gate_a_eval:{seed}"] = f"inputs/gate_a_eval-{seed}/e1"
    doc["files"][ev.relative_to(root).as_posix()] = sha(ev)
    job_pins[f"gate_a_eval:{seed}"] = job_pins[f"gate_a_complete:{seed}"]
    lead = ["venv/bin/python", "-B", r78.REFS_WRAPPER_78B, "eval_adapter", "--family", fam, "--seed", str(seed),
            "--index", idx, "--index-sha256", files[idx]]
    return doc, job_pins, lead


def ref_job(kind: str, pins: dict, seed: int = 1104, points=None) -> dict:
    names = {"b10_certify": ("gate_a_complete", "gate_a_eval"), "ref_eval": ("gate_a_complete", "certification_report"),
             "safe_lora": ("gate_a_complete", "certification_report")}[kind]
    want = {f"{n}:{seed}" for n in names} | ({"prefix_file"} if points and "prefix" in points else set())
    return {"kind": kind, "arm": "a0", "seed": seed, "recipe": "B", "engine": "X", "points": points,
            "inputs": {n: v for n, v in pins.items() if n in want}}


def test_13_b10_certify_ref_eval_and_safe_lora_run_through_refs_78b_in_the_1b_forms(wb, tmp_path, monkeypatch):
    w = wb
    runner = load_by_path("jr78_refs_cmd", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    doc, pins, lead = refs_pod(w, monkeypatch, root)
    p, rec = f"data/kt-prepared/{w.rules.PREPARED_NAME}", w.rules.REC
    i = doc["inputs"]
    tail = ["--oext-bank", i["oext_bank"], "--oext-record", i["oext_record"]]

    def cmds(job):
        return [c for _, c in runner.job_commands(ab_plan(w, job, "B"), "h", 0, root, {}, doc)]
    assert cmds(ref_job("b10_certify", pins)) == [[*lead, "run", "--prepared", p, "--recipe", rec, "--seed", "1104",
                                                   "--reference", i["gate_a_complete:1104"], "--regen-out", "job-0/regen",
                                                   "--eval-root", "job-0/evals", "--evaluations", "certify",
                                                   "--gate-reference-eval", "inputs/gate_a_eval-1104/e1", *tail]]
    cert = ["--certification-report", i["certification_report:1104"], "--certification-report-sha256",
            pins["certification_report:1104"]]
    assert cmds(ref_job("ref_eval", pins, points=["prefix", "scale:0.75"])) == [
        [*lead, "run", "--prepared", p, "--recipe", rec, "--seed", "1104", "--reference", i["gate_a_complete:1104"],
         "--regen-out", "job-0/regen", "--eval-root", "job-0/evals", "--evaluations", "prefix,scale:0.75",
         "--prefix-file", i["prefix_file"], *cert, *tail]]
    sl = cmds(ref_job("safe_lora", pins, points=["default", "certify"]))
    b11 = [*lead[:3], "safe_lora", *lead[4:]]
    assert [c[3] for c in sl] == ["eval_adapter", "safe_lora", "safe_lora", "safe_lora", "eval_adapter", "safe_lora",
                                  "eval_adapter"]
    assert sl[1] == [*b11, "vcheck", "--adapter", "job-0/regen/run/states/e1", "--seed", "1104", "--aligned",
                     "@snapshot:policy", "--base", "@snapshot:base", "--out", "job-0/vcheck"]
    assert sl[4][-len(cert) - len(tail):] == [*cert, *tail] and "--mode" in sl[4] and "external" in sl[4]
    with pytest.raises(runner.Unrunnable, match=r"points \['k12'\] are not among \['default', 'certify'\]"):
        cmds(ref_job("safe_lora", pins, points=["k12"]))         # R-37: neither conditional nor k12 runs
    # the refusals: a failed certification stops every evaluation-only reference (P2 §16.1); REFS_78B null; pins
    root2 = tmp_path / "pod-fail"
    doc2, pins2, _ = refs_pod(w, monkeypatch, root2, verdict="fail")
    with pytest.raises(runner.Unrunnable, match="the seed's B10 certification did not pass"):
        runner.job_commands(ab_plan(w, ref_job("ref_eval", pins2, points=["scale:0.5"]), "B"), "h", 0, root2, {}, doc2)
    monkeypatch.setitem(w.r78.REFS_78B[w.family], 1104, None)
    with pytest.raises(runner.Unrunnable, match=r"REFS_78B\['olmo2-7b'\]\[1104\] is null"):
        cmds(ref_job("b10_certify", pins))
    with pytest.raises(runner.Unrunnable, match="'gate_a_eval:1104' has no pin in plan.json"):
        cmds({**ref_job("b10_certify", pins), "inputs": {"gate_a_complete:1104": pins["gate_a_complete:1104"]}})
    monkeypatch.setattr(w.r78, "REF_PREFIX_SHA256", hx("another prompt"))
    doc, pins, _ = refs_pod(w, monkeypatch, tmp_path / "pod3")
    monkeypatch.setattr(w.r78, "REF_PREFIX_SHA256", hx("another prompt"))
    with pytest.raises(runner.Unrunnable, match="the safety-prompt file's pin is not REF_PREFIX_SHA256"):
        runner.job_commands(ab_plan(w, ref_job("ref_eval", pins, points=["prefix"]), "B"), "h", 0, tmp_path / "pod3", {}, doc)
    # the job's sealed files: the seed's REFS files, the O-ext files and the inputs, the eval folder's files
    paths = runner.sealed_paths(ref_job("b10_certify", pins), {"block": "B"}, 0, doc)
    assert "inputs/gate_a_eval-1104/e1/summary.json" in paths and w.r78.REFS_WRAPPER_78B in paths
    write(tmp_path / "pod3" / "inputs/gate_a_eval-1104/e1/summary.json", {"u": "changed after its pin"})
    monkeypatch.setitem(w.r78.REFS_78B[w.family], 1104, w.r78.REFS_78B[w.family][1104])
    with pytest.raises(runner.Unrunnable, match="'gate_a_eval:1104' is not packed at its files' pins"):
        runner.job_commands(ab_plan(w, ref_job("b10_certify", pins), "B"), "h", 0, tmp_path / "pod3", {}, doc)


def test_13_run_ref_job_records_b10s_gate_its_units_and_the_terms_records(wb, tmp_path, monkeypatch):
    w = wb
    runner = load_by_path("jr78_refs_run", w.root / "setup" / "job_runner_stage1.py")

    def run(case):
        root = tmp_path / f"pod-{case}"
        doc, pins, _ = refs_pod(w, monkeypatch, root)
        calls = []

        def fake(args, **kwargs):
            calls.append(list(args))
            if args[:2] != ["python3", "process_receipt.py"]:
                return subprocess.CompletedProcess(args, 0, "names only", "")
            unit = root / "job-0" / "evals" / "1104-certify"
            write(unit / "COMPLETE.json", {"complete": True})
            write(unit / "job.json", {"job": "synthetic"})
            write(root / "job-0" / "evals.refs78b-terms.json", {"kind": "refs78b terms (synthetic)"})
            write(root / "job-0" / "evals" / "1104-certify.compare.json",
                  {"verdict": "pass" if case in ("pass", "exit4-pass") else "fail"})
            return subprocess.CompletedProcess(args, 4 if case.startswith("exit4") else 0, "", "")
        monkeypatch.setattr(runner.subprocess, "run", fake)
        return runner.run_ref_job(ab_plan(w, ref_job("b10_certify", pins), "B"), "h", 0, root, {}, {}, doc), calls
    got, calls = run("pass")
    assert got["status"] == "complete" and got["certification_gate"] == "passed", got
    assert got["terms_records"] == {"job-0/evals.refs78b-terms.json": got["outputs"]["job-0/evals.refs78b-terms.json"]}
    assert got["units"][0]["unit"] == "job-0/evals/1104-certify" and calls[-1][3:4] == ["eval_adapter"]
    assert calls[-1][-3:] == ["verify", "--unit", "job-0/evals/1104-certify"]
    got, _ = run("exit4-fail")                              # B10's failed gate: complete, the gate recorded failed
    assert got["status"] == "complete" and got["certification_gate"] == "failed", got
    got, _ = run("exit4-pass")                              # exit 4 with a pass verdict is a crash
    assert got["status"] == "crashed" and "not a failed verdict" in got["why"]
    got, _ = run("exit0-fail")
    assert got["status"] == "crashed" and got["why"] == "B10 exited 0 but its comparison is not a pass"


def test_13_ref_train_and_ref_train_bqi_calibrate_under_their_pinned_configs_then_the_unit_pass(wb, tmp_path, monkeypatch):
    w = wb
    runner = load_by_path("jr78_refs_train", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    pins, inputs = oext_inputs()
    doc = {"files": {}, "inputs": inputs}
    unit = pod_oext(w, monkeypatch, root, doc, pins, inputs)
    fam, p = w.family, f"data/kt-prepared/{w.rules.PREPARED_NAME}"
    g = {"path": "experiments/safety_selection/configs/study-kt-olmo2-7b-g-test.json", "config_sha256": hx("g")}
    job = {"kind": "ref_train", "arm": "a0", "seed": 1105, "recipe": "G", "engine": "X", "recipe_g": g}
    plan = {**ab_plan(w, job, "B"), "recipes": {g["path"]: {"config_sha256": g["config_sha256"]}}}
    configs = {}
    monkeypatch.setattr(runner, "_recipe_config_sha", lambda path: configs.get(Path(path).name, "0" * 64))
    write(root / g["path"], {"recipe": "G (synthetic)"})
    configs[Path(g["path"]).name] = g["config_sha256"]
    with pytest.raises(runner.Unrunnable, match="RECIPE_G for olmo2-7b is null"):
        runner.job_commands(plan, "h", 0, root, {}, doc)
    monkeypatch.setitem(w.r78.RECIPE_G, fam, g["config_sha256"])
    cmds = [c for _, c in runner.job_commands(plan, "h", 0, root, {}, doc)]
    assert cmds[0] == ["venv/bin/python", "-m", "experiments.safety_selection", "calibrate", "--prepared", p, "--recipe",
                       g["path"], "--arms", "a0", "--seeds", "1105", "--checkpoints", "e1", "--out-root", "round1"]
    assert cmds[1] == [*unit, "run", "--run", "@unit:0", "--checkpoint", "e1", "--prepared", p, "--recipe", g["path"],
                       "--oext-bank", inputs["oext_bank"], "--oext-record", inputs["oext_record"], "--out", "job-0/oext"]
    other = {**plan, "recipes": {g["path"]: {"config_sha256": hx("main")}}}
    with pytest.raises(runner.Unrunnable, match="the job's config is not RECIPE_G's pin"):
        runner.job_commands(other, "h", 0, root, {}, doc)
    with pytest.raises(runner.Unrunnable, match="it runs on engine X only"):
        runner.job_commands({**plan, "hosts": {"h": {**plan["hosts"]["h"], "jobs": [{**job, "engine": "Y"}]}}}, "h", 0,
                            root, {}, doc)
    # B+Qi on engine Y: RECIPE_BQI's config and the family's Y O-ext index (OEXT_78B_Y[F]; --engine Y)
    bqi = {"path": "experiments/safety_selection/configs/study-kt-olmo2-7b-bqi-test.json", "config_sha256": hx("bqi")}
    monkeypatch.setitem(w.r78.RECIPE_BQI, fam, bqi["config_sha256"])
    write(root / bqi["path"], {"recipe": "B+Qi (synthetic)"})
    configs[Path(bqi["path"]).name] = bqi["config_sha256"]
    yidx = f"scripts/scale78b/settings/OEXT-78B-Y__{fam}.json"
    yfiles = {w.r78.OEXT_WRAPPER_78B: doc["files"][w.r78.OEXT_WRAPPER_78B],
              yidx: sha(write(root / yidx, {"index": f"synthetic {fam} Y"}))}
    monkeypatch.setitem(w.r78.OEXT_78B_Y, fam, {"files": yfiles, "inputs": dict(w.r78.OEXT_78B[fam]["inputs"])})
    doc["files"].update(yfiles)
    jb = {"kind": "ref_train_bqi", "arm": "a0", "seed": 1105, "recipe": "BQI", "engine": "Y", "recipe_bqi": bqi}
    planb = {**ab_plan(w, jb, "B"), "recipes": {bqi["path"]: {"config_sha256": bqi["config_sha256"]}}}
    y = [c for _, c in runner.job_commands(planb, "h", 0, root, {}, doc)][1]
    assert y[:12] == ["venv/bin/python", "-B", w.r78.OEXT_WRAPPER_78B, "unit", "--family", fam, "--engine", "Y",
                      "--index", yidx, "--index-sha256", yfiles[yidx]] and y[y.index("--recipe") + 1] == bqi["path"]
    assert bqi["path"] in runner.sealed_paths(jb, {"block": "B"}, 0, doc) and yidx in runner.sealed_paths(jb, {"block": "B"}, 0, doc)
    # R-70: the packed config must hash (by the pod's engine) to the pin, and the main config's hash refuses
    configs[Path(g["path"]).name] = hx("another config")
    with pytest.raises(runner.Unrunnable, match="the packed config does not hash to RECIPE_G's pin"):
        runner.job_commands(plan, "h", 0, root, {}, doc)
    main = w.rules.REC_CONFIG_SHA256
    for k, key, name, pl in (("ref_train", "recipe_g", "RECIPE_G", plan), ("ref_train_bqi", "recipe_bqi", "RECIPE_BQI", planb)):
        cfg = dict(g if k == "ref_train" else bqi, config_sha256=main)
        monkeypatch.setitem(getattr(w.r78, name), fam, main)
        j = {**pl["hosts"]["h"]["jobs"][0], key: cfg}
        mplan = {**pl, "hosts": {"h": {**pl["hosts"]["h"], "jobs": [j]}}, "recipes": {cfg["path"]: {"config_sha256": main}}}
        configs[Path(cfg["path"]).name] = main
        with pytest.raises(runner.Unrunnable, match=f"{name} is the main config's hash"):
            runner.job_commands(mplan, "h", 0, root, {}, doc)


def test_13_block_bs_pack_takes_the_reference_inputs_at_their_jobs_pins_and_the_eval_folder_by_its_listing(wb):
    w = wb
    pack = importlib.import_module("pack_setup")
    unit = w.repo / "tmp" / "family-probe-s78-olmo2-7b-A" / "retrieved" / "a-1" / "tree" / "round1" / "1104-a0-e1-a1"
    s = write(unit / "eval" / "e1" / "summary.json", {"u": sb.SENTINELS[2]})
    c = write(unit / "COMPLETE.json", {"complete": True, "files": {"eval/e1/summary.json": sha(s)}})
    jobs = [{"kind": "b10_certify", "seed": 1104, "inputs": {"gate_a_complete:1104": sha(c), "gate_a_eval:1104": sha(c)}},
            {"kind": "ref_eval", "seed": 1104, "inputs": {"certification_report:1104": hx("report"), "prefix_file": hx("x")}}]
    write(w.root / "plan.json", {"hosts": {}, "blocks": {"B": {"pending": {"b-9": {"block": "B", "jobs": jobs}}}}})
    pins = pack.ref_input_pins()
    assert pins == {"prefix_file": w.r78.REF_PREFIX_SHA256, "gate_a_complete:1104": sha(c), "gate_a_eval:1104": sha(c),
                    "certification_report:1104": hx("report")}         # the safety prompt only at its constant pin
    got = pack.gate_eval_files("gate_a_eval:1104", unit / "eval" / "e1", sha(c))
    assert got == {"inputs/gate_a_eval-1104/e1/summary.json": (s, sha(s))}
    write(s, {"u": "changed after COMPLETE.json"})
    with pytest.raises(SystemExit, match="a file is not the one its unit's COMPLETE.json lists"):
        pack.gate_eval_files("gate_a_eval:1104", unit / "eval" / "e1", sha(c))
    with pytest.raises(SystemExit, match="is not an a0 unit's eval/e1 folder whose COMPLETE.json has its pin"):
        pack.gate_eval_files("gate_a_eval:1104", unit / "eval" / "e1", hx("another unit"))
    jobs.append({"kind": "safe_lora", "seed": 1104, "inputs": {"certification_report:1104": hx("another report")}})
    write(w.root / "plan.json", {"hosts": {}, "blocks": {"B": {"pending": {"b-9": {"block": "B", "jobs": jobs}}}}})
    with pytest.raises(SystemExit, match="plan.json pins 'certification_report:1104' twice"):
        pack.ref_input_pins()


@pytest.mark.parametrize("block,allowed", [("A", False), ("B", True)])
def test_r63_engine_ys_pack_is_allowed_in_block_bs_copy_and_refused_in_block_as(tmp_path, monkeypatch, block, allowed):
    w = pab.ABWorld(tmp_path, monkeypatch, "olmo2-7b", block)
    try:
        pack = importlib.import_module("pack_setup")
        monkeypatch.setattr(pack, "engine_tree", lambda engine, y_tree: (w.repo, None, ["listed"]))
        monkeypatch.setattr(pack, "check_constraints", lambda: None)
        monkeypatch.setattr(pack, "config_sha256", lambda tree, rel: "0" * 64)    # a later refusal (PP10: no process)
        with pytest.raises(SystemExit) as info:
            pack.main(["Y"])
        assert ("blocks 0 and A run on engine X" in str(info.value)) is (not allowed), str(info.value)
    finally:
        pab.close(w)


# ===== 10. R-67: record-y-measured (KD9) ==============================================================================
def y_host(w, root_host: str, kind: str = "retrain", gpu=None, engine=None, list_it: bool = True) -> dict:
    tree = w.root / "retrieved" / root_host / "tree"
    rec = write(tree / "job-0" / "y-remeasure.json",
                {"kind": "stage1-78b engine-Y re-measure", "version": 1, "family": w.family, "job": 0, "job_kind": kind,
                 "engine_sha256": engine or sb.Y, "gpu": gpu or w.r78.GPU_NAME, "progress": []})
    done = write(tree / "JOB-DONE.json", {"host": root_host, "jobs": [
        {"index": 0, "kind": kind, "status": "complete",
         "outputs": {"job-0/y-remeasure.json": sha(rec)} if list_it else {}}]})
    return {"block": "sc", "engine": "Y", "done": True, "job_done_sha256": sha(done), "jobs": [{"kind": kind}]}


def test_r67_record_y_measured_turns_the_y_pods_records_into_the_pinned_record_and_refuses_off_records(so, monkeypatch):
    w = so
    log = []
    monkeypatch.setattr(w.mac, "operator_action", lambda doc: log.append(doc))
    out = w.repo / "records"
    out.mkdir(exist_ok=True)
    with pytest.raises(SystemExit, match="ENGINE_Y is null"):
        w.tool.record_y_measured(["y-1"], "test", str(out / "y0.json"))
    monkeypatch.setattr(w.r78, "ENGINE_Y", sb.Y)
    hosts = {"y-1": y_host(w, "y-1")}
    monkeypatch.setattr(w.tool, "load", lambda: {"hosts": hosts})
    got = w.tool.record_y_measured(["y-1"], "test", str(out / "y1.json"))
    doc = json.loads((out / "y1.json").read_text())
    assert got["records"] == 1 and got["sha256"] == sha(out / "y1.json") and log[-1]["action"] == "record-y-measured"
    assert doc["records"] == [{"path": f"tmp/family-probe-s78-{w.family}-sc/retrieved/y-1/tree/job-0/y-remeasure.json",
                               "sha256": sha(w.root / "retrieved/y-1/tree/job-0/y-remeasure.json"), "family": w.family,
                               "job_kind": "retrain"}]
    assert w.r78.y_measured_problem(doc) is None
    data = (out / "y1.json").read_bytes()
    monkeypatch.setattr(w.r78, "Y_MEASURED_RECORD", {"path": "records/y1.json", "sha256": sha(out / "y1.json")})
    assert w.r78.y_measured_or_refuse(data) == doc
    with pytest.raises(w.r78.Refused, match="do not hash"):
        w.r78.y_measured_or_refuse(data + b" ")
    with pytest.raises(SystemExit, match="y1.json exists: a record is written once"):
        w.tool.record_y_measured(["y-1"], "test", str(out / "y1.json"))
    for name, host, match in (
            ("y-2", y_host(w, "y-2", gpu="NVIDIA H100"), "not this family's engine-Y re-measure"),
            ("y-3", y_host(w, "y-3", engine=hx("other engine")), "not this family's engine-Y re-measure"),
            ("y-4", y_host(w, "y-4", list_it=False), "lists no y-remeasure.json"),
            ("y-5", y_host(w, "y-5", kind="a1_pass"), "no record is the a0-1101 retrain's"),
            ("y-6", {**y_host(w, "y-6"), "engine": "X"}, "is not this copy's engine-Y host recorded done")):
        hosts[name] = host
        with pytest.raises(SystemExit, match=match):
            w.tool.record_y_measured([name], "test", str(out / f"y-{name}.json"))
        assert not (out / f"y-{name}.json").exists()
    hosts["y-7"] = y_host(w, "y-7")
    write(w.root / "retrieved/y-7/tree/job-0/y-remeasure.json", {"kind": "changed after record-done"})
    with pytest.raises(SystemExit, match="differs from the SHA-256 its JOB-DONE.json lists"):
        w.tool.record_y_measured(["y-7"], "test", str(out / "y-changed.json"))
    bad = {**doc, "gpu": "NVIDIA H100"}
    assert "GPU is not the measured one" in w.r78.y_measured_problem(bad)
    monkeypatch.setattr(w.r78, "ENGINE_Y", hx("another Y"))
    assert "engine_y is not ENGINE_Y's pin" in w.r78.y_measured_problem(doc)


def test_13_refs_78b_pins_take_track_rs_form_and_r35s_table_names_each_seeds_a0_unit():
    r78 = load_by_path("rules_78b_refs", KIT / "rules_78b.py")
    f, s = "olmo2-7b", 1104
    idx = f"scripts/scale78b/settings/REFS-78B__{f}__{s}.json"
    good = {"files": {r78.REFS_WRAPPER_78B: hx("w"), idx: hx("i"), "scripts/stage1_s1/eval_adapter.py": hx("e")},
            "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}}
    assert r78.refs_form_problem(good, f, s) is None
    assert all(v is None for fam in r78.REFS_78B.values() for v in fam.values())          # the committed pins: null
    with pytest.raises(r78.Refused, match=r"REFS_78B\['olmo2-7b'\]\[1104\] is null"):
        r78.refs_or_refuse(f, s)
    no_wrapper = {**good, "files": {k: v for k, v in good["files"].items() if k != r78.REFS_WRAPPER_78B}}
    assert "do not pin the wrapper" in r78.refs_form_problem(no_wrapper, f, s)
    assert "exactly scripts/scale78b/settings/REFS-78B__olmo2-7b__1105.json" in r78.refs_form_problem(good, f, 1105)
    two = {**good, "files": {**good["files"], idx.replace("1104", "1105"): hx("j")}}
    assert "refs index file(s)" in r78.refs_form_problem(two, f, s)
    assert "plain path under scripts/" in r78.refs_form_problem({**good, "files": {**good["files"], "x/y.py": hx("y")}}, f, s)
    assert "inputs does not hold" in r78.refs_form_problem({**good, "inputs": {"oext_bank": hx("b")}}, f, s)
    # GXB R-35: 1102 the side unit; 1103 the side unit on OLMo-2-7B and N's a0-1103 on Llama-3.1-8B; 1104 block A; 1105-1107 B
    assert [r78.ref_cert_source("olmo2-7b", s) for s in r78.REFERENCE_SEEDS] == ["side", "side", "A", "B", "B", "B"]
    assert [r78.ref_cert_source("llama31-8b", s) for s in r78.REFERENCE_SEEDS] == ["side", "n", "A", "B", "B", "B"]
    with pytest.raises(r78.Refused, match="is not a reference seed"):
        r78.ref_cert_source(f, 1101)
    assert "b10_certify" in r78.E_KINDS and r78.e_upper_s(f, "b10_certify")["upper_s"] < r78.e_upper_s(f, "ref_eval", 2)["upper_s"]


# ===== 11. 13g (GXB R-68): block B's init plans the references; release checks the certification ===================
def test_r68_init_block_b_plans_each_seeds_certification_evaluation_only_and_trained_references(wb):
    w = wb
    blinded = pab.b_ready(w, sigma=4.0)
    pab.seal_sibling(w, "A")
    with pytest.raises(SystemExit, match='names its "reference_set"'):     # GXB R-79: never silent
        w.tool.init_block(argparse.Namespace(block="B", jobs=str(w.record({"family": w.family, "launches": [
            {"deal": list(range(6))}, {"judge": {"judge": "harmbench"}}, {"judge": {"judge": "granite"}}]})),
            dry_run=True, group_jobs=None, funding=None, noise_reading=str(w.noise), blinded_sigma=str(blinded),
            anchor_job_done=None))
    base = {"pods": [p for p in w.init(dry_run=True, blinded=str(blinded))["pods"] if not p.get("role")]}
    with pytest.raises(SystemExit, match="reference_set is one of"):
        w.init(dry_run=True, blinded=str(blinded), extra={"reference_set": "all"})
    out = w.init(dry_run=True, blinded=str(blinded), extra={"reference_set": "six_seed"})
    refs = [p for p in out["pods"] if p.get("role")]
    by_role = {r: sorted(p["runs"][0] for p in refs if p["role"] == r) for r in ("refs-cert", "refs-eval", "refs-train")}
    seeds = range(1102, 1108)
    assert by_role["refs-cert"] == sorted(f"b10_certify@{s}" for s in seeds)
    assert by_role["refs-eval"] == sorted([f"ref_eval@{s}" for s in seeds] + [f"safe_lora@{s}" for s in seeds])
    assert by_role["refs-train"] == sorted([f"ref_train@{s}" for s in range(1104, 1108)]          # 1102-1103 reused
                                           + [f"ref_train_bqi@{s}" for s in seeds])
    assert len(out["pods"]) == len(base["pods"]) + 6 + 12 + 10
    three = w.init(dry_run=True, blinded=str(blinded), extra={"reference_set": "three_seed"})
    assert sorted(p["runs"][0] for p in three["pods"] if p.get("role") == "refs-cert") == \
        [f"b10_certify@{s}" for s in (1102, 1103, 1104)]
    # the jobs as planned: the certification source (R-35), the points, empty pins until ref-inputs
    w.init(blinded=str(blinded), extra={"reference_set": "three_seed"})
    plan = w.plan()
    pend = plan["blocks"]["B"]["pending"]
    jobs = {(h["jobs"][0]["kind"], h["jobs"][0]["seed"]): h["jobs"][0] for h in pend.values() if h.get("role")}
    assert [jobs[("b10_certify", s)]["cert_source"] for s in (1102, 1103, 1104)] == ["side", "side", "A"]
    assert jobs[("ref_eval", 1103)]["points"] == ["prefix", "scale:0.75", "scale:0.5"]
    assert jobs[("safe_lora", 1104)]["points"] == ["default", "certify"]
    assert jobs[("ref_train_bqi", 1102)]["engine"] == "Y" and ("ref_train", 1102) not in jobs
    assert all(j["inputs"] == {} for j in jobs.values())
    assert plan["blocks"]["B"]["reference_set"] == "three_seed"


def test_r68_ref_pins_come_from_the_a0_sources_and_a_failed_certification_stops_the_seeds_references(wb, monkeypatch):
    w = wb
    tool, r78 = w.tool, w.r78
    plan = {"hosts": {"b-1": {"block": "B", "done": True, "jobs": [
        {"kind": "a0_arm", "seed": 1105, "status": "complete", "complete_sha256": hx("a0-1105")}]}}, "blocks": {"B": {}}}
    side = r78.KIT["olmo2-7b"]["a0_units"][1102]["complete_sha256"]
    cert = {"kind": "b10_certify", "seed": 1102, "points": None}
    assert tool.ref_pins(plan, "olmo2-7b", cert) == {"gate_a_complete:1102": side, "gate_a_eval:1102": side}
    assert tool.ref_pins(plan, "olmo2-7b", {**cert, "seed": 1105})["gate_a_complete:1105"] == hx("a0-1105")
    with pytest.raises(SystemExit, match=r"seed 1106's a0 unit \(block B\) is not recorded complete"):
        tool.ref_pins(plan, "olmo2-7b", {**cert, "seed": 1106})
    ev = {"kind": "ref_eval", "seed": 1102, "points": ["prefix", "scale:0.5"]}
    with pytest.raises(SystemExit, match=r"seed 1102's certification \(b10_certify\) is not recorded done"):
        tool.ref_pins(plan, "olmo2-7b", ev)
    plan["hosts"]["c-1"] = {"block": "B", "done": True, "jobs": [
        {"kind": "b10_certify", "seed": 1102, "status": "complete", "certification_gate": "failed",
         "outputs": {"job-0/evals/1102-certify.compare.json": hx("report-fail")}}]}
    with pytest.raises(SystemExit, match=r"is not recorded passed .*every evaluation-only reference of the seed stops"):
        tool.ref_pins(plan, "olmo2-7b", ev)
    assert tool.decided_seeds(plan) == {1102}
    plan["hosts"]["c-1"]["jobs"][0].update(certification_gate="passed",
                                            outputs={"job-0/evals/1102-certify.compare.json": hx("report")})
    assert tool.ref_pins(plan, "olmo2-7b", ev) == {"gate_a_complete:1102": side, "certification_report:1102": hx("report"),
                                                   "prefix_file": r78.REF_PREFIX_SHA256}
    assert "prefix_file" not in tool.ref_pins(plan, "olmo2-7b", {**ev, "kind": "safe_lora", "points": ["default"]})
    # the trained references' configs (R-70): the pin and its path; the main config's hash refuses
    tr = {"kind": "ref_train", "seed": 1104}
    with pytest.raises(SystemExit, match="RECIPE_G for olmo2-7b is null"):
        tool.ref_config(tr, "olmo2-7b")
    monkeypatch.setitem(r78.RECIPE_G, "olmo2-7b", hx("g"))
    with pytest.raises(SystemExit, match=r"RECIPE_G_PATH\['olmo2-7b'\] is null"):
        tool.ref_config(tr, "olmo2-7b")
    monkeypatch.setitem(r78.RECIPE_G_PATH, "olmo2-7b", "experiments/safety_selection/configs/g.json")
    assert tool.ref_config(tr, "olmo2-7b") == {"path": "experiments/safety_selection/configs/g.json", "config_sha256": hx("g")}
    monkeypatch.setitem(r78.RECIPE_G, "olmo2-7b", w.rules.REC_CONFIG_SHA256)
    with pytest.raises(SystemExit, match="is the main config's hash"):
        tool.ref_config(tr, "olmo2-7b")


def test_r68_release_of_a_reference_launch_checks_the_pins_again_and_skips_a_failed_seeds_evaluations(wb, monkeypatch):
    w = wb
    tool, r78 = w.tool, w.r78
    side = r78.KIT["olmo2-7b"]["a0_units"][1102]["complete_sha256"]
    monkeypatch.setattr(tool, "engine_receipt", lambda engine: {"family": "olmo2-7b", "sealed_files_sha256": hx(engine)})
    monkeypatch.setitem(r78.REFS_78B["olmo2-7b"], 1102, {"files": {}, "inputs": {}})
    monkeypatch.setattr(r78, "refs_or_refuse", lambda f, s: {"files": {}})
    plan = {"hosts": {"c-1": {"block": "B", "done": True, "jobs": [
        {"kind": "b10_certify", "seed": 1102, "status": "complete", "certification_gate": "passed",
         "outputs": {"job-0/evals/1102-certify.compare.json": hx("report")}}]},
        "c-2": {"block": "B", "done": True, "jobs": [
            {"kind": "b10_certify", "seed": 1103, "status": "complete", "certification_gate": "failed",
             "outputs": {"job-0/evals/1103-certify.compare.json": hx("report-3")}}]}},
        "blocks": {"B": {}}, "recipes": {}}
    good = {"kind": "ref_eval", "seed": 1102, "points": ["scale:0.5"],
            "inputs": {"gate_a_complete:1102": side, "certification_report:1102": hx("report")}}
    failed = {"kind": "ref_eval", "seed": 1103, "points": ["scale:0.5"], "inputs": {}}
    hosts = [("e-1", {"block": "B", "role": "refs-eval", "engine": "X", "jobs": [good]}),
             ("e-2", {"block": "B", "role": "refs-eval", "engine": "X", "jobs": [failed]})]
    assert tool.release_refs(plan, "olmo2-7b", hosts) == ["e-1"]
    assert plan["blocks"]["B"]["refs_not_run"][0]["host"] == "e-2" and "e-2" not in plan["hosts"]
    assert plan["hosts"]["e-1"]["sealed_files_sha256"] == hx("X")
    stale = ("e-3", {"block": "B", "role": "refs-eval", "engine": "X",
                     "jobs": [{**good, "inputs": {**good["inputs"], "certification_report:1102": hx("old")}}]})
    with pytest.raises(SystemExit, match="plan.json's input pins are not the ones their sources give now"):
        tool.release_refs(plan, "olmo2-7b", [stale])


# ===== 12. R-59, R-60 (W1-18's guard batch and families) ==============================================================
def test_r59_the_guard_batch_comes_from_each_familys_main_config_and_an_unreadable_one_refuses(so, tmp_path):
    w = so
    runner = load_by_path("jr78_r59", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    rel = w.r78.CONFIGS["llama31-8b"]["main"][0]
    with pytest.raises(runner.Unrunnable, match="llama31-8b's main config gives no guard.batch_size"):
        runner.guard_batch(root, "llama31-8b", 0)
    write(root / rel, {"guard": {"batch_size": 6}})
    assert runner.guard_batch(root, "llama31-8b", 0) == "6"
    write(root / rel, {"guard": {"batch_size": True}})
    with pytest.raises(runner.Unrunnable, match="is not a positive integer"):
        runner.guard_batch(root, "llama31-8b", 0)


@pytest.mark.parametrize("option", ["B", "C"])
def test_r60_w1_18s_families_are_the_gates_and_the_planner_refuses_another_list(wa, option):
    w = wa
    with pytest.raises(SystemExit, match="GATE_78B is null"):
        w.tool.w1_18_gate_families("here")
    w.gate(option=option)
    fams = sorted(w.r78.GATE_OPTIONS[option])
    with pytest.raises(SystemExit, match="are not GATE_78B's families"):
        w.tool.w1_18_gate_families("here")
    w.mp.setattr(w.r78, "W1_18_78B", {"files": {}, "side_units": {f: {} for f in fams}})
    assert w.tool.w1_18_gate_families("here") == fams
    other = sorted(set(w.r78.GATE_OPTIONS["B"]) - set(fams)) or ["olmo2-7b"]
    w.mp.setattr(w.r78, "W1_18_78B", {"files": {}, "side_units": {f: {} for f in (fams + other if option == "C" else fams[:1])}})
    with pytest.raises(SystemExit, match="are not GATE_78B's families"):
        w.tool.w1_18_gate_families("here")


# ===== 13. R-65: the runner's main() at the three call sites (a synthetic pod: test_kit_78b_runner's Pod) ============
from test_stage1_runkit import w  # noqa: E402,F401 - the 7-8B block-0 World fixture (the Pod's base)
import test_kit_78b_runner as kr  # noqa: E402


def reseal(pod, files: dict, inputs: dict, block: str | None = None, engine: str | None = None) -> None:
    """Add packed files and named inputs to the Pod's sealed-files.json and re-pin it in plan.json."""
    doc = json.loads((pod.root / "sealed-files.json").read_text())
    for rel, data in files.items():
        f = pod.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        doc["files"][rel] = sha(f)
    doc["inputs"].update(inputs)
    write(pod.root / "sealed-files.json", doc)
    h = pod.plan["hosts"][pod.host]
    h["sealed_files_sha256"] = sha(pod.root / "sealed-files.json")
    if block:
        h["block"] = block
    if engine:
        h["engine"], h["engine_sha256"] = engine, sb.Y
        for j in h["jobs"]:
            j["engine"] = engine
    write(pod.root / "plan.json", pod.plan)


def test_r65_main_reads_the_stop_record_before_check_keys_on_sc_a_and_b_pods_only(w, monkeypatch):
    pod = kr.Pod(w, monkeypatch)
    r78 = pod.r78
    monkeypatch.setitem(r78.ANCHOR_STOP, pod.family, {"path": "records/stop.json", "sha256": hx("stop")})
    assert pod.main() in (0, 1) and "refused" not in json.dumps(pod.done()["refusal"] or {})   # block 0: never read
    (pod.root / "JOB-DONE.json").unlink()
    for f in (pod.root / "job-done").glob("*.json"):
        f.unlink()
    reseal(pod, {}, {}, block="A")
    monkeypatch.setattr(pod.runner, "job_commands", lambda *a, **k: [])
    assert pod.main() == 1
    done = pod.done()
    assert done["stopped"] == "refused" and done["refusal"]["reason"] == "rule"
    assert "anchor stop record (KR4)" in done["refusal"]["text"] and "is not packed" in done["refusal"]["text"]


def test_r65_main_passes_the_packed_oext_bank_to_check_keys(w, monkeypatch):
    pod = kr.Pod(w, monkeypatch)
    r78, fam = pod.r78, pod.family
    monkeypatch.setitem(r78.OEXT_78B, fam, {"files": {r78.OEXT_WRAPPER_78B: hx("w"),
                                                      f"scripts/scale78b/settings/OEXT-78B__{fam}.json": hx("i")},
                                            "inputs": {"oext_bank": hx("the pinned bank"), "oext_record": hx("r")}})
    reseal(pod, {"inputs/oext_bank/b.json": b'{"kind": "another bank (synthetic)"}\n'},
           {"oext_bank": "inputs/oext_bank/b.json"}, block="A")
    assert pod.main() == 1
    done = pod.done()
    assert done["refusal"]["reason"] == "key" and "pinned O-ext bank" in done["refusal"]["text"]


def test_r65_main_writes_the_y_remeasure_record_after_each_complete_job_on_engine_y(w, monkeypatch):
    pod = kr.Pod(w, monkeypatch)
    r78 = pod.r78
    monkeypatch.setattr(r78, "ENGINE_Y", sb.Y)
    monkeypatch.setattr(r78, "Y_MEASURED", True)
    monkeypatch.setattr(r78, "Y_MEASURED_RECORD", {"path": "records/y.json", "sha256": hx("y")})
    monkeypatch.setattr(pod.runner, "_engine_identity", lambda: sb.Y)
    reseal(pod, {}, {}, engine="Y")
    pod.remaining([200000.0])
    pod.main()
    recs = [r for r in pod.done()["jobs"] if r["status"] == "complete"]
    assert recs, (pod.done()["refusal"], pod.done()["stopped"])
    for r in recs:
        rel = f"job-{r['index']}/y-remeasure.json"
        assert r["outputs"][rel] == sha(pod.root / rel)
        doc = json.loads((pod.root / rel).read_text())
        assert doc["kind"] == "stage1-78b engine-Y re-measure" and doc["engine_sha256"] == sb.Y


# ===== 14. R-66, R-71: the W1-18 pod's tokenizers and Safe LoRA's base model ========================================
def test_r71_a_safe_lora_host_downloads_the_base_at_its_pinned_revision_and_refuses_while_it_is_null(so, tmp_path, monkeypatch):
    w = so
    for name in ("probes", "host"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    probes = importlib.import_module("probes")
    with pytest.raises(SystemExit, match="has no pinned revision and file list yet"):
        w.rules.host_extra_downloads([{"kind": "safe_lora"}])
    assert w.rules.host_extra_downloads([{"kind": "ref_eval"}]) == []
    monkeypatch.setitem(probes.BASE_MODELS["olmo2-7b"], "revision", "a" * 40)
    monkeypatch.setitem(probes.BASE_MODELS["olmo2-7b"], "files", [{"rfilename": "config.json", "size": 10}])
    got = w.rules.host_extra_downloads([{"kind": "safe_lora"}])
    assert got[0]["role"] == "base" and got[0]["revision"] == "a" * 40 and got[0]["gated"] is False
    host = importlib.import_module("host")
    assert host.gated_command("20261120T120000Z").endswith("--gated --token-stdin")
    assert host.gated_command("20261120T120000Z", True).endswith("--gated --token-stdin --with-base")
    write(w.root / "plan.json", {"hosts": {"s-1": {"jobs": [{"kind": "safe_lora"}]}, "s-2": {"jobs": [{"kind": "arm"}]}}})
    assert host.runs_safe_lora("s-1") and not host.runs_safe_lora("s-2") and not host.runs_safe_lora("s-3")
    calls = []
    monkeypatch.setattr(host, "ssh_base", lambda h: ["-p", "1", "root@x"])
    monkeypatch.setattr(host, "save", lambda path, rec: None)
    host.gated_download("s-1", "hf_" + "x" * 34, runner=lambda args, **k: calls.append(args) or
                        subprocess.CompletedProcess(args, 0, "", ""))
    assert calls[0][-1].endswith("--with-base") and "hf_" not in " ".join(calls[0])


def test_r71_llamas_gated_base_goes_through_the_token_path_and_r66_its_tokenizer_on_olmos_w1_18_pod(tmp_path, monkeypatch):
    for name in ("launch", "orchestrate", "probes", "host"):     # another copy's modules may be loaded already
        monkeypatch.delitem(sys.modules, name, raising=False)
    wl = sb.ScWorld(tmp_path / "l", monkeypatch, "llama31-8b")
    try:
        probes = importlib.import_module("probes")
        monkeypatch.setitem(probes.BASE_MODELS["llama31-8b"], "revision", "b" * 40)
        monkeypatch.setitem(probes.BASE_MODELS["llama31-8b"], "files", [{"rfilename": "config.json", "size": 10}])
        write(wl.root / "plan.json", {"hosts": {"s-1": {"jobs": [{"kind": "safe_lora"}]}, "a-1": {"jobs": [{"kind": "arm"}]}}})
        launch, orch = importlib.import_module("launch"), importlib.import_module("orchestrate")
        roles = [e["role"] for e in launch.gated_entries("s-1")]
        assert roles == ["policy", "base"] == [e["role"] for e in orch.gated_entries("s-1")]
        assert [e["role"] for e in launch.gated_entries("a-1")] == ["policy"] == [e["role"] for e in launch.gated_entries()]
    finally:
        for name in (*rk.MODULES, "launch", "orchestrate", "probes", "host"):
            sys.modules.pop(name, None)
    wo = sb.ScWorld(tmp_path / "o", monkeypatch, "olmo2-7b")
    try:
        launch, orch = importlib.import_module("launch"), importlib.import_module("orchestrate")
        write(wo.root / "plan.json", {"hosts": {"w-1": {"jobs": [{"kind": "w1_18", "families": ["llama31-8b", "olmo2-7b"]}]},
                                                "w-2": {"jobs": [{"kind": "w1_18", "families": ["olmo2-7b"]}]}}})
        got = launch.gated_entries("w-1")
        kit = wo.r78.KIT["llama31-8b"]["instruct_model"]
        assert got == [{"role": "tokenizer:llama31-8b", "repo_id": kit["repo_id"], "revision": kit["revision"], "gated": True,
                        "patterns": list(wo.rules.TOKENIZER_FILES)}] == orch.gated_entries("w-1")
        assert launch.gated_entries("w-2") == [] and launch.gated_entries() == []      # [C]: OLMo-2-7B's only, open
    finally:
        for name in (*rk.MODULES, "launch", "orchestrate", "probes", "host"):
            sys.modules.pop(name, None)


# ===== 15. Verifier fixes: R-75 (K3V-1) check-plan on the Mac for every O-ext pod; pod-side refusals ================
def mac_check(w, monkeypatch, pod: Path, job: dict, block: str, doc: dict, recipes=None):
    """orchestrate.check_plan for one host on the Mac: sealed-files.json is the pod's doc (every other file the job
    lists added by name), HERE/hosts/HOST holds no bundle file, and the checkout holds the branch record at its pin."""
    for name in ("orchestrate",):
        monkeypatch.delitem(sys.modules, name, raising=False)
    orch = importlib.import_module("orchestrate")
    host = f"{w.family}-{block.lower()}-9"
    h = {"block": block, "engine": job.get("engine", "X"), "jobs": [job]}
    for rel in orch.runner.sealed_paths(job, h, 0, doc):
        doc["files"].setdefault(rel, hx(rel))
    branch = w.r78.BRANCH_78B.get(w.family)
    if branch and (pod / branch["path"]).is_file():          # the checkout's own record at its pin (R-75)
        (w.repo / branch["path"]).parent.mkdir(parents=True, exist_ok=True)
        (w.repo / branch["path"]).write_bytes((pod / branch["path"]).read_bytes())
    plan = {"family": w.family, "hosts": {host: h}, "recipes": recipes or {}}
    packed = pod.parent / f"packed-{block}-{job['kind']}"
    packed.mkdir(exist_ok=True)
    (packed / "sealed-files.json").write_text(json.dumps(doc))
    monkeypatch.setattr(orch, "plan", lambda: plan)
    monkeypatch.setattr(orch, "packed", lambda name: packed)
    monkeypatch.setattr(orch, "packed_receipt", lambda name: {})
    (orch.HERE / "hosts" / host).mkdir(parents=True, exist_ok=True)
    assert not any((orch.HERE / "hosts" / host).iterdir())  # no pod file on the Mac
    return orch, host


@pytest.mark.parametrize("block", ["A", "B"])
def test_r75_check_plan_passes_on_the_mac_for_a_block_a_or_b_arm_pod_and_hashes_nothing_there(tmp_path, monkeypatch, block):
    w = pab.ABWorld(tmp_path, monkeypatch, "olmo2-7b", block)
    try:
        pod = tmp_path / "pod"
        pins, inputs = oext_inputs()
        doc = {"files": {}, "inputs": inputs}
        pod_oext(w, monkeypatch, pod, doc, pins, inputs)
        orch, host = mac_check(w, monkeypatch, pod, a0_job(1104 if block == "A" else 1105), block, doc)
        assert orch.check_plan(host)["ok"] is True
        doc["files"].pop(inputs["oext_bank"])                # the sealed listing is still checked on the Mac
        orch, host = mac_check(w, monkeypatch, pod, a0_job(1104 if block == "A" else 1105), block, doc)
        doc2 = json.loads((pod.parent / f"packed-{block}-a0_arm" / "sealed-files.json").read_text())
        doc2["files"][inputs["oext_bank"]] = hx("another bank")
        (pod.parent / f"packed-{block}-a0_arm" / "sealed-files.json").write_text(json.dumps(doc2))
        with pytest.raises(SystemExit, match="the input 'oext_bank' is not packed at its pin"):
            orch.check_plan(host)
    finally:
        pab.close(w)


def test_r75_check_plan_passes_on_the_mac_for_the_scorer_blocks_o_ext_pods_and_w1_18(so, tmp_path, monkeypatch):
    w = so
    fam = w.family
    pod = tmp_path / "pod"
    side_rel, c0_rel = "inputs/side_complete-a0-1101/COMPLETE.json", "inputs/source_complete-R-1101/COMPLETE.json"
    side = write(pod / side_rel, {"complete": True, "checkpoints": {"e1": {"adapter_fingerprint": hx("e1")}}})
    c0src = write(pod / c0_rel, {"checkpoints": {"e1": {"adapter_fingerprint": hx("fp")}}})
    pins, inputs = oext_inputs()
    pins.update({"side_complete:a0:1101": sha(side), "source_complete:R:1101": sha(c0src)})
    inputs.update({"side_complete:a0:1101": side_rel, "source_complete:R:1101": c0_rel})
    doc = {"files": {side_rel: sha(side), c0_rel: sha(c0src)}, "inputs": inputs}
    pod_oext(w, monkeypatch, pod, doc, pins, inputs)
    jobs = [{"kind": "o_only", "arm": "theta0", "seed": None, "recipe": "B", "engine": "X",
             "inputs": {n: pins[n] for n in ("oext_bank", "oext_record")}},
            {"kind": "o_only_with_regenerate", "arm": "a0", "seed": 1101, "recipe": "B", "engine": "X",
             "inputs": {n: pins[n] for n in w.rules.sc_unit_input_names("o_only_with_regenerate", "a0", 1101)}},
            {"kind": "c0", "arm": "R", "seed": 1101, "recipe": "B", "engine": "X",
             "inputs": {n: pins[n] for n in ("source_complete:R:1101", "oext_bank", "oext_record")},
             "edit": {"sha256": hx("rd1"), "path": "x"}, "expect_fingerprint": hx("fp")}]
    for job in jobs:
        orch, host = mac_check(w, monkeypatch, pod, job, "sc", json.loads(json.dumps(doc)))
        assert orch.check_plan(host)["ok"] is True, job["kind"]
    # c0 on the Mac carries the 1B placeholder; the pod reads the packed source unit (K5) and refuses a changed one
    with orch.runner.mac_build(w.repo):
        lean = orch.runner.job_commands(sc_plan(w, jobs[2]), "h", 0, tmp_path / "empty", {}, doc)[1][1]
    assert lean[lean.index("--expect-adapter-fingerprint") + 1] == "@fingerprint:source_complete:R:1101"
    write(pod / c0_rel, {"checkpoints": {"e1": {"adapter_fingerprint": hx("changed")}}})
    with pytest.raises(orch.runner.Unrunnable, match="the packed source unit's COMPLETE.json is missing or differs"):
        orch.runner.job_commands(sc_plan(w, jobs[2]), "h", 0, pod, {}, doc)
    # W1-18: its route, the gate's families and each family's guard batch from the checkout's main config
    route = w1_route(w, monkeypatch, pod, ("olmo2-7b", "llama31-8b"), doc)
    for f in ("olmo2-7b", "llama31-8b"):
        write(w.repo / w.r78.CONFIGS[f]["main"][0], {"guard": {"batch_size": 8}})
        write(pod / w.r78.CONFIGS[f]["main"][0], {"guard": {"batch_size": 8}})
    w1 = {"kind": "w1_18", "arm": None, "seed": None, "recipe": "B", "engine": "X", "inputs": {},
          "families": sorted(route["side_units"])}
    orch, host = mac_check(w, monkeypatch, pod, w1, "sc", json.loads(json.dumps(doc)))
    assert orch.check_plan(host)["ok"] is True
    # the pod refuses a missing or wrong file (here the W1-18 index)
    idx = "scripts/scale78b/settings/OEXT-78B-W1__llama31-8b.json"
    (pod / idx).write_text("changed")
    with pytest.raises(orch.runner.Unrunnable, match="llama31-8b's W1-18 index is not packed at its pin"):
        orch.runner.job_commands(sc_plan(w, w1), "h", 0, pod, {}, doc)


def test_r75_check_plan_passes_on_the_mac_for_the_reference_kinds(wb, tmp_path, monkeypatch):
    w = wb
    pod = tmp_path / "pod"
    doc, pins, _ = refs_pod(w, monkeypatch, pod)
    fam = w.family
    g = {"path": "experiments/safety_selection/configs/study-kt-olmo2-7b-g-test.json", "config_sha256": hx("g")}
    monkeypatch.setitem(w.r78.RECIPE_G, fam, g["config_sha256"])
    jobs = [ref_job("b10_certify", pins), ref_job("ref_eval", pins, points=["prefix", "scale:0.5"]),
            ref_job("safe_lora", pins, points=["default", "certify"]),
            {"kind": "ref_train", "arm": "a0", "seed": 1105, "recipe": "G", "engine": "X", "recipe_g": g}]
    for job in jobs:
        recipes = {g["path"]: {"config_sha256": g["config_sha256"]}} if job["kind"] == "ref_train" else None
        orch, host = mac_check(w, monkeypatch, pod, job, "B", json.loads(json.dumps(doc)), recipes)
        assert orch.check_plan(host)["ok"] is True, job["kind"]
    # the pod: a changed certification report or eval file refuses there (the Mac cannot see them)
    write(pod / doc["inputs"]["certification_report:1104"], {"verdict": "fail"})
    doc_pod = json.loads(json.dumps(doc))
    doc_pod["files"][doc["inputs"]["certification_report:1104"]] = sha(pod / doc["inputs"]["certification_report:1104"])
    job = {**jobs[1], "inputs": {**jobs[1]["inputs"], "certification_report:1104":
                                 doc_pod["files"][doc["inputs"]["certification_report:1104"]]}}
    runner = load_by_path("jr78_r75_refs", w.root / "setup" / "job_runner_stage1.py")
    with pytest.raises(runner.Unrunnable, match="the seed's B10 certification did not pass"):
        runner.job_commands(ab_plan(w, job, "B"), "h", 0, pod, {}, doc_pod)
    with runner.mac_build(w.repo):                             # on the Mac the verdict is the release's check
        assert runner.job_commands(ab_plan(w, job, "B"), "h", 0, tmp_path / "empty", {}, doc_pod)



# ===== 16. Verifier fixes: R-76 (source_unit in the 1B form), R-77 (V-01b, V-08, V-12, V-14), R-78 (V-02) ===========
def side_unit_folder(w, seed: int = 1101, extra: dict | None = None, listed_extra: dict | None = None) -> Path:
    """A synthetic side unit folder at KIT a0_units' path with a COMPLETE.json listing its files (TEST-LOCAL pin)."""
    u = w.r78.KIT[w.family]["a0_units"][seed]
    folder = w.repo / u["path"]
    if folder.exists():
        sb.shutil.rmtree(folder)
    files = {"job.json": write(folder / "job.json", {"job": "synthetic"}),
             "eval/e1/generations.jsonl": write(folder / "eval" / "e1" / "generations.jsonl", "{}\n"),
             "eval/e1/guard.jsonl": write(folder / "eval" / "e1" / "guard.jsonl", "{}\n"),
             **{rel: write(folder / rel, data) for rel, data in (listed_extra or {}).items()}}
    listing = {rel: sha(f) for rel, f in files.items()}
    c = write(folder / "COMPLETE.json", {"complete": True, "files": listing, "job_sha256": listing["job.json"]})
    w.mp.setitem(u, "complete_sha256", sha(c))
    for rel, data in (extra or {}).items():
        write(folder / rel, data)
    return folder


def test_r76_the_source_unit_is_packed_by_its_complete_json_listing_and_an_unlisted_file_refuses(so):
    w = so
    folder = side_unit_folder(w, extra={".DS_Store": "finder metadata"})
    digest = sha(folder / "COMPLETE.json")
    w.pack(("source_unit:a0:1101", folder, digest))
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    base = f"inputs/source_unit-a0-1101/{folder.name}"
    assert sealed["inputs"]["source_unit:a0:1101"] == base
    assert sorted(f for f in sealed["files"] if f.startswith(base + "/")) == sorted(
        f"{base}/{r}" for r in ("COMPLETE.json", "job.json", "eval/e1/generations.jsonl", "eval/e1/guard.jsonl"))
    sb.shutil.rmtree(w.root / "setup" / "packed-stage1-X")    # R-81: a listed file check_source does not read stays out
    folder = side_unit_folder(w, listed_extra={"states/e1/state.json": "a listed state (synthetic)"})
    w.pack(("source_unit:a0:1101", folder, sha(folder / "COMPLETE.json")))
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    assert f"{base}/states/e1/state.json" not in sealed["files"] and f"{base}/eval/e1/guard.jsonl" in sealed["files"]
    folder = side_unit_folder(w)
    (folder / "eval" / "e1" / "guard.jsonl").unlink()
    with pytest.raises(SystemExit, match=r"lacks \['eval/e1/guard.jsonl'\]"):
        w.pack(("source_unit:a0:1101", folder, sha(folder / "COMPLETE.json")))
    for rel, data, match in (("states/e1/stray.bin", "an unlisted file", "a file is not one its COMPLETE.json lists"),
                             ("eval/e1/guard.jsonl", "changed after COMPLETE.json", "a file is not one its COMPLETE.json")):
        folder = side_unit_folder(w)                         # (the World's pack moves the earlier pack aside)
        write(folder / rel, data)
        with pytest.raises(SystemExit, match=match):
            w.pack(("source_unit:a0:1101", folder, sha(folder / "COMPLETE.json")))
    folder = side_unit_folder(w)
    with pytest.raises(SystemExit, match="'source_unit:a0:1101''s SHA-256 is not its pin"):
        w.pack(("source_unit:a0:1101", folder, hx("another unit")))


def test_r77_v01b_a_block_b_arm_job_carries_its_o_ext_step(wb, tmp_path, monkeypatch):
    w = wb
    runner = load_by_path("jr78_v01b", w.root / "setup" / "job_runner_stage1.py")
    pod = tmp_path / "pod"
    pins, inputs = oext_inputs()
    doc = {"files": {}, "inputs": inputs}
    unit = pod_oext(w, monkeypatch, pod, doc, pins, inputs)
    cmds = runner.job_commands(ab_plan(w, a0_job(1105), "B"), "h", 0, pod, {}, doc)
    assert [n for n, _ in cmds] == ["job-0-calibrate", "job-0-oext"] and cmds[1][1][:len(unit)] == unit


def ab_pack(w, monkeypatch, names=("oext_bank", "oext_record"), edit: bool = True):
    """pack_setup.py X in a block-A or B copy (the engine's own code faked; the scorer pins copied in), with OEXT_78B,
    the branch record and the O-ext bank and record TEST-LOCAL, and one planned job's edit in plan.json."""
    rk_shell = load_by_path("shell78_ab", KIT / "tests" / "test_kit_78b_shell.py")
    rk_shell.fake_engine_tree(w.repo)
    for rel in w.rules.SCORER_PINS:
        (w.repo / rel).parent.mkdir(parents=True, exist_ok=True)
        sb.shutil.copyfile(REPO / rel, w.repo / rel)   # bytes only: the main checkout's frozen scripts are read-only
    folder = w.repo / w.rules.PREPARED_LOCAL / w.rules.PREPARED_NAME
    write(folder / "manifest.sha256", w.rules.PREPARED_MANIFESTS[w.rules.PREPARED_NAME] + "\n")
    write(folder / "manifest.json", {"kind": "prepared (synthetic)"})
    pack = importlib.import_module("pack_setup")
    monkeypatch.setattr(pack, "engine_code", lambda tree: sb.X)
    monkeypatch.setattr(pack, "config_sha256", lambda tree, rel: w.config.get(rel, "0" * 64))
    monkeypatch.setattr(pack, "git_state", lambda: "d" * 40)
    monkeypatch.setattr(pack, "run_check", lambda argv: 0)
    fam = w.family
    files = {}
    for rel in (w.r78.OEXT_WRAPPER_78B, f"scripts/scale78b/settings/OEXT-78B__{fam}.json"):
        files[rel] = sha(write(w.repo / rel, f"# synthetic {rel}\n"))
    bank, record = write(w.repo / "tmp/oext/bank.json", {"bank": 1}), write(w.repo / "tmp/oext/record.json", {"r": 1})
    monkeypatch.setitem(w.r78.OEXT_78B, fam, {"files": files, "inputs": {"oext_bank": sha(bank), "oext_record": sha(record)}})
    b = write(w.repo / "records" / f"branch-{fam}.json", branch_record(fam))
    monkeypatch.setitem(w.r78.BRANCH_78B, fam, {"path": f"records/branch-{fam}.json", "sha256": sha(b)})
    e = write(w.repo / ".ai/inputs/test/edit.json", {"edit": "synthetic"})
    write(w.root / "plan.json", {"hosts": {}, "blocks": {w.block: {"pending": {"x-1": {"block": w.block, "jobs": [
        {"kind": "arm", "arm": "H1", "seed": 1105, "edit": {"path": ".ai/inputs/test/edit.json", "sha256": sha(e)}}
        if edit else {"kind": "a0_arm", "arm": "a0", "seed": 1105, "edit": None}]}}}}})
    src = {"oext_bank": bank, "oext_record": record}
    rec = write(w.repo / "records" / f"inputs-{len(names)}.json", {"kind": "stage1-78b pack inputs", "engine": "X",
        "family": fam, "inputs": [{"name": n, "path": str(src[n].relative_to(w.repo)), "sha256": sha(src[n])} for n in names]})
    out = w.root / "setup" / "packed-stage1-X"
    if out.exists():                                     # the World's stand-in receipt (or an earlier test pack)
        sb.shutil.rmtree(out)
    pack.main(["X", "--inputs", str(rec), "--inputs-sha256", sha(rec)])
    return json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text()), sha(e)


def test_r77_v08_v14_block_bs_pack_carries_the_o_ext_files_inputs_branch_record_and_edits(wb, monkeypatch):
    w = wb
    with pytest.raises(SystemExit, match=r"blocks A and B need the O-ext inputs \['oext_record'\]"):
        ab_pack(w, monkeypatch, names=("oext_bank",))
    sealed, edit_sha = ab_pack(w, monkeypatch)
    fam = w.family
    for rel in (*w.r78.OEXT_78B[fam]["files"], f"records/branch-{fam}.json", f"edits/{edit_sha}.edit.json"):
        assert rel in sealed["files"], rel
    assert set(sealed["inputs"]) == {"oext_bank", "oext_record"}


@pytest.mark.parametrize("block", ["0", "A"])
def test_r77_v12_engine_ys_pack_is_refused_in_blocks_0_and_a_with_engine_y_filled(tmp_path, monkeypatch, block):
    if block == "0":
        w = rk.World(tmp_path, monkeypatch) if hasattr(rk, "World") else None
    else:
        w = pab.ABWorld(tmp_path, monkeypatch, "olmo2-7b", block)
    try:
        monkeypatch.setattr(w.r78, "ENGINE_Y", sb.Y)
        pack = importlib.import_module("pack_setup")
        monkeypatch.setattr(pack, "engine_tree", lambda engine, y_tree: (w.repo, None, ["listed"]))
        monkeypatch.setattr(pack, "check_constraints", lambda: None)
        with pytest.raises(SystemExit, match="blocks 0 and A run on engine X"):
            pack.main(["Y"])
    finally:
        for name in pab.MODULES:
            sys.modules.pop(name, None)


def test_r78_v02_the_o_ext_step_never_runs_when_calibrate_left_two_new_units(wa, tmp_path, monkeypatch):
    w = wa
    runner = load_by_path("jr78_v02", w.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    pins, inputs = oext_inputs()
    doc = {"files": {}, "inputs": inputs}
    pod_oext(w, monkeypatch, root, doc, pins, inputs)
    calls = []

    def fake(args, **kwargs):
        calls.append(list(args))
        argv = args[5:]
        if "calibrate" in argv:
            for n in (1, 2):
                write(root / "round1" / f"1104-a0-e1-a{n}" / "COMPLETE.json", {"complete": True})
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(runner.subprocess, "run", fake)
    got = runner.run_job(ab_plan(w, a0_job()), "h", 0, root, {}, {}, doc)
    assert got["status"] == "crashed" and got["why"] == "no new COMPLETE.json"
    assert not any("unit" in c[5:] for c in calls)          # the O-ext pass did not run on either unit



# ===== 17. Last pass: R-81 (what source_unit carries), settled through the unchanged 1B code ========================
R81_PROBE = """
import importlib.util, json, pathlib, shutil, sys
REPO, base = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
for extra in (REPO / "scripts/scale78b/tests/oext", REPO / "scripts/stage1/tests", REPO / "scripts/stage1_s1/tests", REPO):
    sys.path.insert(0, str(extra))
sys.path.append(str(pathlib.Path(importlib.util.find_spec("experiments.safety_selection").origin).parent / "tests"))
import oext78_fixtures as f
env = f.unit_world(base / "w", "128")
env.unit_path, env.unit_sha, env.unit_doc = f.put_unit_settings(env)
src = env.world.units["source"]
need = json.loads(sys.argv[3])
out = {"listed": len(json.loads((src / "COMPLETE.json").read_text())["files"])}
for case, files in (("full", None), ("needed_only", need), ("without_guard", need[:-1])):
    d = src
    if files is not None:
        d = base / case
        for rel in files:
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src / rel, d / rel)
    code, _, err = f.direct_unit(env, f.unit_args(env, base / ("o-" + case), run=env.world.units["regen"], source=d),
                                 env.unit_doc)
    out[case] = code
print(json.dumps(out))
"""


def test_r81_source_unit_carries_exactly_what_the_unchanged_1b_check_source_reads(tmp_path, local_processes):
    """GXB R-81: through the unchanged 1B oext_unit.py (Track O's ENGINEERING FIXTURES, its own process: the oext tests'
    path setup), a regenerated unit's O-ext pass under Branch 128 with --dev100-source runs on a source folder holding
    only the pack's SOURCE_UNIT_FILES although the unit's COMPLETE.json lists many more, and refuses without guard.jsonl;
    so the pack takes those files. The pack's list equals the settings' dev100.source_files at e1 (1B and both families)."""
    pytest.importorskip("torch")
    pack = load_by_path("pack_r81", KIT / "pack_setup.py")
    for rel in ("scripts/stage1_s1/settings/oext_unit.json", "scripts/scale78b/settings/oext_unit__olmo2-7b.json",
                "scripts/scale78b/settings/oext_unit__llama31-8b.json"):
        listed = json.loads((REPO / rel).read_text())["dev100"]["source_files"]
        assert tuple(x.format(checkpoint="e1") for x in listed) == pack.SOURCE_UNIT_FILES, rel
    probe = tmp_path / "r81_probe.py"
    probe.write_text(R81_PROBE)
    (tmp_path / "base").mkdir()
    done = subprocess.run([sys.executable, "-B", str(probe), str(REPO), str(tmp_path / "base"),
                           json.dumps(list(pack.SOURCE_UNIT_FILES))], capture_output=True, text=True, cwd=REPO,
                          env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr[-500:]
    got = json.loads(done.stdout.strip().splitlines()[-1])
    assert got["listed"] > len(pack.SOURCE_UNIT_FILES)
    assert (got["full"], got["needed_only"], got["without_guard"]) == (0, 0, 2)



# ===== 18. Last pass: R-79 (never silent) is in test_r68's first lines; R-80 (the references are judged) ============
def test_r80_the_judge_launches_come_after_the_references_and_list_every_reference_unit(wb):
    w = wb
    blinded = pab.b_ready(w, sigma=4.0)
    pab.seal_sibling(w, "A")
    for ref_set, n_ref in (("six_seed", 6 * 4 + 6 * 2 + 4 + 6), ("three_seed", 3 * 3 + 3 * 2 + 1 + 3)):
        out = w.init(dry_run=True, blinded=str(blinded), extra={"reference_set": ref_set})
        assert out["judge_units"] == out["runs"] + n_ref, ref_set
        judge_lines = [l for l in out["need_lines"] if " judge launch " in l]
        assert len(judge_lines) == 2 and all(f"{n_ref} reference units" in l for l in judge_lines)
        assert all(int(l.split(" judge launch ")[1].split()[0]) > max(p["launch"] for p in out["pods"])
                   for l in judge_lines)                  # both judge launches after every reference launch
    # every complete reference unit is in the block's judge list (record-done's units; the trained ones' own units)
    plan = {"hosts": {}, "blocks": {"B": {}}}
    for i, (kind, units) in enumerate((("ref_eval", 4), ("safe_lora", 2), ("ref_train", 1), ("ref_train_bqi", 1),
                                       ("b10_certify", 1))):
        job = {"kind": kind, "arm": "a0", "seed": 1105, "status": "complete"}
        if kind in w.rules.JUDGED_B10_KINDS or kind == "b10_certify":
            job["units"] = [{"unit": f"job-0/evals/{kind}-{u}", "complete_sha256": hx(f"{kind}-{u}")} for u in range(units)]
        else:
            job["complete_sha256"] = hx(kind)
        plan["hosts"][f"r-{i}"] = {"block": "B", "jobs": [job]}
    got = w.tool.judge_required_units(plan, "B")
    want = {hx(f"ref_eval-{u}") for u in range(4)} | {hx(f"safe_lora-{u}") for u in range(2)} | {hx("ref_train"),
                                                                                                    hx("ref_train_bqi")}
    assert set(got) == want                              # the certification unit is the a0 again: not a reference
    assert "ref_train" in w.rules.JUDGED_RUN_KINDS and "ref_train_bqi" in w.rules.JUDGED_RUN_KINDS


# ===== 19. K3V2-1 (GXB R-84): the trained references' key check takes their own pinned config ========================
@pytest.mark.parametrize("kind", ["ref_train", "ref_train_bqi"])
def test_r84_a_trained_reference_pod_passes_its_key_check_on_its_pinned_config_and_refuses_the_main_configs(
        w, monkeypatch, kind):
    pod = kr.Pod(w, monkeypatch)
    r78, fam = pod.r78, pod.family
    key, pin_name = {"ref_train": ("recipe_g", "RECIPE_G"), "ref_train_bqi": ("recipe_bqi", "RECIPE_BQI")}[kind]
    engine = "Y" if kind == "ref_train_bqi" else "X"
    cfg = {"path": f"experiments/safety_selection/configs/{kind}-test.json", "config_sha256": hx(kind)}
    monkeypatch.setitem(getattr(r78, pin_name), fam, cfg["config_sha256"])
    if engine == "Y":
        monkeypatch.setattr(r78, "ENGINE_Y", sb.Y)
        monkeypatch.setattr(pod.runner, "_engine_identity", lambda: sb.Y)
        monkeypatch.setitem(r78.OEXT_78B_Y, fam, {"files": {r78.OEXT_WRAPPER_78B: hx("w"),
                                                            f"scripts/scale78b/settings/OEXT-78B-Y__{fam}.json": hx("y")},
                                                  "inputs": {"oext_bank": hx("ob"), "oext_record": hx("or")}})
    monkeypatch.setattr(pod.runner, "job_commands", lambda *a, **k: [])   # the key check is the subject here
    h = pod.plan["hosts"][pod.host]
    job = {**w.rules.job_record(kind, "a0", 1105, None, None, None, engine=engine, family=fam,
                                recipe={"ref_train": "G"}.get(kind, "BQI"), oext=kind == "ref_train"),
           "edit": None, key: dict(cfg)}
    h["jobs"] = [job]
    reseal(pod, {}, {}, block="B", engine=engine if engine == "Y" else None)
    pod.remaining([200000.0])
    pod.main()
    done = pod.done()
    assert done["stopped"] != "refused", done["refusal"]          # passed check_keys on its pinned config
    assert pod.runner.recipe_key(job, w.rules.REC_CONFIG_SHA256) == cfg["config_sha256"]
    # the same pod with the job's config at the main config's hash is refused by the key check
    (pod.root / "JOB-DONE.json").unlink()
    for f in (pod.root / "job-done").glob("*.json"):
        f.unlink()
    job[key] = {**cfg, "config_sha256": w.rules.REC_CONFIG_SHA256}
    write(pod.root / "plan.json", pod.plan)
    pod.main()
    done = pod.done()
    assert done["stopped"] == "refused" and f"runs under {pin_name} only" in done["refusal"]["text"]
    # a job without its pinned config gives no key (never the main config's)
    assert pod.runner.recipe_key({"kind": kind, "recipe": "G"}, w.rules.REC_CONFIG_SHA256) is None


def test_r84_every_recipe_pinned_kind_takes_its_own_key_and_only_main_config_kinds_take_the_main_one(so):
    w = so
    runner = load_by_path("jr78_r84", w.root / "setup" / "job_runner_stage1.py")
    main = w.rules.REC_CONFIG_SHA256
    for kind in w.r78.S78_KINDS:                                 # recipe S: recipe_s78's hash; no S config: no key
        assert runner.recipe_key({"kind": kind, "recipe": "S", "recipe_s78": {"config_sha256": hx("s78")}}, main) == hx("s78")
        assert runner.recipe_key({"kind": kind, "recipe": "S"}, main) is None
    assert runner.recipe_key({"kind": "retrain", "recipe": "B"}, main) == main      # a stopped family's MAIN_F retrain
    for kind in w.r78.S78_KINDS:                                 # an S_78 kind under any other recipe name: no key
        assert runner.recipe_key({"kind": kind, "recipe": "G"}, main) is None
    assert runner.recipe_key({"kind": "ref_train", "recipe": "B"}, main) is None
    for kind in ("arm", "a0_arm", "o_only", "c0", "anchor", "b10_certify", "ref_eval", "safe_lora", "w1_18"):
        assert runner.recipe_key({"kind": kind, "recipe": "B"}, main) == main
    assert set(w.r78.PINNED_RECIPE_KINDS) == set(w.r78.S78_KINDS) | {"ref_train", "ref_train_bqi"}   # nothing else pinned


# ===== 20. R-87 (I-2): Y_MEASURED_RECORD is read at its pin; R-88 (I-3, I-4): check-plan and the A/B pack's edits ====
def test_r87_a_measured_kind_on_engine_y_reads_the_measured_record_at_its_pin(wa):
    w = wa
    tool, r78 = w.tool, w.r78
    w.mp.setattr(r78, "ENGINE_Y", sb.Y)
    with pytest.raises(SystemExit, match="the pin Y_MEASURED_RECORD is null"):
        tool.y_measured_read("here")
    doc = {"kind": "stage1-78b engine-Y measured record", "version": 1, "engine_y": sb.Y, "gpu": r78.GPU_NAME,
           "records": [{"path": "tmp/x/job-0/y-remeasure.json", "sha256": hx("r"), "family": w.family,
                        "job_kind": "retrain"}], "utc": "2026-11-20T12:00:00+00:00", "recorded_by": "test"}
    rec = w.record(doc, "y-measured.json")
    w.mp.setattr(r78, "Y_MEASURED_RECORD", {"path": w.rel(rec), "sha256": sha(rec)})
    assert tool.y_measured_read("here") == doc
    rec.write_text(rec.read_text() + " ")                      # changed after its pin
    with pytest.raises(SystemExit, match="missing or differs from its pin"):
        tool.y_measured_read("here")
    rec.unlink()                                               # missing
    with pytest.raises(SystemExit, match="missing or differs from its pin"):
        tool.y_measured_read("here")
    bad = w.record({**doc, "gpu": "NVIDIA H100"}, "y-measured-bad.json")   # pinned, but off its form
    w.mp.setattr(r78, "Y_MEASURED_RECORD", {"path": w.rel(bad), "sha256": sha(bad)})
    with pytest.raises(SystemExit, match="its GPU is not the measured one"):
        tool.y_measured_read("here")
    # planning a measured kind on Y reads it (an E kind on Y does not)
    arm = {**w.rules.job_record("a0_arm", "a0", 1104, None, None, None, engine="Y", family=w.family), "edit": None}
    with pytest.raises(SystemExit, match="a measured kind on engine Y: the record at Y_MEASURED_RECORD"):
        tool.host_record(w.plan() if (w.root / "plan.json").exists() else {"hosts": {}}, "A", "arms", [arm], None, 0)
    w.mp.setattr(tool, "engine_receipt", lambda engine: {"family": w.family, "sealed_files_sha256": hx(engine)})
    with pytest.raises(SystemExit, match="y-1: a measured kind on engine Y: the record at Y_MEASURED_RECORD"):
        tool.release_refs({"hosts": {}, "blocks": {"B": {}}, "recipes": {}}, w.family,
                          [("y-1", {"block": "B", "role": "refs-train", "engine": "Y",
                                    "jobs": [{"kind": "ref_train", "seed": 1105}]})])


def edits_for_block_a(w) -> None:
    """Every edit block A plans, as a synthetic file at its pin (RK's R_DRAW_SOURCES and METHOD_EDITS, TEST-LOCAL)."""
    fam = w.family
    folder = w.repo / "edits-fixture"
    for d in range(4, 14):
        f = write(folder / f"R_d{d}.json", {"edit": f"synthetic R_d{d}"})
        w.mp.setitem(w.r78.R_DRAW_SOURCES[fam], d, {"path": f.relative_to(w.repo).as_posix(), "sha256": sha(f)})
    for arm in ("A1", "L1", "H1", "S1", "S3", "S4"):
        f = write(folder / f"{arm}.json", {"edit": f"synthetic {arm}"})
        w.mp.setitem(w.r78.METHOD_EDITS[fam], arm, {"path": f.relative_to(w.repo).as_posix(), "sha256": sha(f),
                                                    "rows": pab.METHOD_ROWS[arm]})


def test_r88_init_block_a_pack_and_check_plan_on_every_released_host_and_an_unpacked_edit_refuses(wa, monkeypatch):
    """GXB R-88 (I-3, I-4; the integration reviewer's form): a real block A plan (init-block A), packed by pack_setup
    (the released hosts' edits among them, INT-2), then orchestrate.check_plan on the Mac for every released arm host
    with HERE/hosts/HOST empty; an edit missing from sealed-files.json refuses there (INT-1)."""
    w = wa
    w.gate()
    edits_for_block_a(w)
    w.fill(edits=False)
    fam = w.family
    rk_shell = load_by_path("shell78_r88", KIT / "tests" / "test_kit_78b_shell.py")
    rk_shell.fake_engine_tree(w.repo)
    for rel in w.rules.SCORER_PINS:
        (w.repo / rel).parent.mkdir(parents=True, exist_ok=True)
        sb.shutil.copyfile(REPO / rel, w.repo / rel)   # bytes only: the main checkout's frozen scripts are read-only
    folder = w.repo / w.rules.PREPARED_LOCAL / w.rules.PREPARED_NAME
    write(folder / "manifest.sha256", w.rules.PREPARED_MANIFESTS[w.rules.PREPARED_NAME] + "\n")
    write(folder / "manifest.json", {"kind": "prepared (synthetic)"})
    pack = importlib.import_module("pack_setup")
    monkeypatch.setattr(pack, "engine_code", lambda tree: sb.X)
    monkeypatch.setattr(pack, "config_sha256", lambda tree, rel: w.config.get(rel, "0" * 64))
    monkeypatch.setattr(pack, "git_state", lambda: "d" * 40)
    monkeypatch.setattr(pack, "run_check", lambda argv: 0)
    files = {rel: sha(write(w.repo / rel, f"# synthetic {rel}\n"))
             for rel in (w.r78.OEXT_WRAPPER_78B, f"scripts/scale78b/settings/OEXT-78B__{fam}.json")}
    bank, record = write(w.repo / "tmp/oext/bank.json", {"bank": 1}), write(w.repo / "tmp/oext/record.json", {"r": 1})
    monkeypatch.setitem(w.r78.OEXT_78B, fam, {"files": files, "inputs": {"oext_bank": sha(bank), "oext_record": sha(record)}})
    w.init()
    plan = json.loads((w.root / "plan.json").read_text())
    hosts = [h for h, v in plan["hosts"].items() if v.get("block") == "A"]
    assert hosts and any(j.get("edit") for h in hosts for j in plan["hosts"][h]["jobs"])
    src = {"oext_bank": bank, "oext_record": record}
    rec = write(w.repo / "records" / "inputs-r88.json", {"kind": "stage1-78b pack inputs", "engine": "X", "family": fam,
        "inputs": [{"name": n, "path": str(src[n].relative_to(w.repo)), "sha256": sha(src[n])} for n in src]})
    out = w.root / "setup" / "packed-stage1-X"
    if out.exists():
        sb.shutil.rmtree(out)
    pack.main(["X", "--inputs", str(rec), "--inputs-sha256", sha(rec)])
    sealed = json.loads((out / "sealed-files.json").read_text())
    branch = w.r78.BRANCH_78B[fam]
    sys.modules.pop("orchestrate", None)
    orch = importlib.import_module("orchestrate")
    monkeypatch.setattr(orch, "packed", lambda name: out)
    monkeypatch.setattr(orch, "packed_receipt", lambda name: {})
    for host in hosts:
        (orch.HERE / "hosts" / host).mkdir(parents=True, exist_ok=True)
        assert not any((orch.HERE / "hosts" / host).iterdir())
        assert orch.check_plan(host)["ok"] is True, host
    assert branch["path"] in sealed["files"]
    host = next(h for h in hosts if any(j.get("edit") for j in plan["hosts"][h]["jobs"]))
    edit = next(j["edit"]["sha256"] for j in plan["hosts"][host]["jobs"] if j.get("edit"))
    assert f"edits/{edit}.edit.json" in sealed["files"]
    cut = {**sealed, "files": {k: v for k, v in sealed["files"].items() if k != f"edits/{edit}.edit.json"}}
    (out / "sealed-files.json").write_text(json.dumps(cut))
    with pytest.raises(SystemExit, match="not packed"):
        orch.check_plan(host)
