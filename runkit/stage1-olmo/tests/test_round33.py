"""Kit round 33 (31 Oct 2026; the judge runbook for block B, tmp/gi-viii-notes/judge-runbook-block-b.md §0, GB1, GB4
and GB5), on CPU, without RunPod, Hugging Face or GitHub. Expected values are written by hand; every input is
synthetic.

GB1: judge_units_stage1.py units-of-block refuses a block (not A) while it has an open job (plan_tool.block_open_jobs:
a released host not recorded done, a pending host of a launch not released, a crashed job no not-run decision names).
GB4: seal.py block refuses a block (not A) whose judge-completion record names HarmBench until the runbook's step-13
copy (addendum §37 point 5) holds HarmBench's run record and label cache as the HB reader reads them. GB5: record-judges
refuses a launch whose result's verification.gpu is not stage1_rules.JUDGE_GPU (Gate B's podhost.GPU)."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

import test_round31 as r31
import test_stage1_runkit as rk
from test_stage1_runkit import w  # noqa: F401 - the World fixture (a copy of the kit, synthetic pins)

sha = rk.sha
HB_TAG = "s1b-harmbench-1"
PODHOST = rk.KIT.parents[1] / "scripts" / "gate_b_mac_judges" / "pod" / "podhost.py"


def _wrapper():
    spec = importlib.util.spec_from_file_location("s1_units_wrapper_r33", rk.KIT / "judge_units_stage1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ===== GB1 ===========================================================================================================

def test_gb1_units_of_block_refuses_while_block_b_has_an_open_job_and_lists_it_once_decided(w, tmp_path, capsys):
    """GB1 both ways, with block B's three launches (the deal's 24 runs on b-1...b-6; the 1104 reference on b-7; recipe
    G at 1102 on b-8): units-of-block B refuses (exit 2, nothing written) and names the first open jobs while launch 0
    runs (26 open: its 24 and the pending b-7 and b-8), while b-6 runs (its 4 jobs and the pending b-7 and b-8: 6),
    after b-6 is done with a crashed job (3, then 2 after b-7, then 1 after b-8); a not-run decision for the crashed
    job lists the block (26 units); a changed decision file refuses again (exit 2, not a crash)."""
    rest = rk.B_DEAL + [{"hosts": [[{**rk.REF1104, "points": ["scale:0.75", "scale:0.5"]}]]},
                        {"hosts": [[{"kind": "ref_train", "arm": "G", "recipe": "G", "seed": 1102}]]}]
    rk._certified(w, rest=rest)
    w.init("B", rest)
    wrapper = _wrapper()
    out = tmp_path / "units_b.txt"
    argv = ["units-of-block", "B", "--out", str(out), "--plan", str(w.root / "plan.json")]

    def refused(count: int, first: str) -> str:
        capsys.readouterr()
        assert wrapper.main(argv) == 2 and not out.exists()
        err = capsys.readouterr().err
        assert f"refused: block B has {count} open job(s) ({first} (" in err, err
        assert "record-done each host, or name a job that will not run in a not-run decision" in err
        return err

    refused(26, "b-1:0")
    for host in rk.B_HOSTS[:-1]:
        w.done(host)
    assert {"b-7", "b-8"} <= set(w.plan()["blocks"]["B"]["pending"])
    assert ", ...)" in refused(6, "b-6:0")                                  # three named, the rest elided
    w.done("b-6", statuses={1: "crashed"})
    assert re.search(r"open job\(s\) \(b-6:1 \([^)]*\), b-7:0 \([^)]*\), b-8:0 \([^)]*\)\): ", refused(3, "b-6:1"))
    w.tool.release("B")
    w.done("b-7")
    w.tool.release("B")
    refused(2, "b-6:1")
    w.done("b-8")
    refused(1, "b-6:1")
    path, digest = rk._not_run(w, ["b-6:1"])
    w.tool.record_not_run(path, digest)
    capsys.readouterr()
    path_before = list(sys.path)
    assert wrapper.main(argv) == 0 and sys.path == path_before              # plan_tool's load leaves sys.path as it was
    lines = out.read_text().splitlines()
    assert json.loads(capsys.readouterr().out)["units"] == 26 == len(lines)
    assert str(w.root / "retrieved" / "b-6" / "tree" / "units" / "job-1") not in lines
    kept = Path(path).read_bytes()
    Path(path).write_bytes(kept + b" ")
    other = tmp_path / "units_b2.txt"
    assert wrapper.main(["units-of-block", "B", "--out", str(other), "--plan", str(w.root / "plan.json")]) == 2
    assert "not-run decision is missing or differs" in capsys.readouterr().err and not other.exists()
    Path(path).write_bytes(kept)


# ===== GB4 ===========================================================================================================

def _block_b_recorded(w, judges=("harmbench", "granite")) -> None:
    r31._block_b_judged(w)
    w.tool.release("B")
    if "granite" not in judges:
        w.tool.record_judge_not_run(*r31._decision(w, ["granite"]))
    w.tool.record_judges("B", *w.file_judges(block="B", judges=judges))
    assert w.tool.block_complete(w.plan(), "B") is True


def test_gb4_block_bs_seal_needs_harmbenchs_run_record_and_label_cache_copied_under_judges_pods(w):
    """GB4 both ways: with both judges recorded, the seal refuses (no seal file, no seal entry) with no copy, with
    Granite's copy alone, with a changed run record or one that is a symbolic link, with no label cache, another one or
    one that is a symbolic link; with the runbook's copy it seals and hashes both copied files as sealed."""
    _block_b_recorded(w)
    out = w.root / "judges" / "B" / "pods" / HB_TAG / "fetched" / "out"
    src = w.repo / "tmp" / "judge-pod" / HB_TAG / "fetched" / "out"
    where = re.escape(f"block B: judges/B/pods/{HB_TAG}/fetched/out/")
    run_record = where + r"run-record\.json is missing or not the judge record's run_record_sha256; copy them from "
    cache = where + r"harmbench-pod\.jsonl is missing or not the cache SHA-256 its run record names; copy them from "

    def refused(match: str) -> None:
        with pytest.raises(SystemExit, match=match):
            w.seal.seal_block("B")
        assert "B" not in (w.plan().get("seals") or {}) and not (w.root / "seals" / "block-B.json").exists()

    refused(run_record)
    w.s37_copy("B", judges=("granite",))
    refused(run_record)
    out.mkdir(parents=True)
    (out / "run-record.json").write_bytes((src / "run-record.json").read_bytes() + b" ")
    refused(run_record)
    (out / "run-record.json").unlink()
    (out / "run-record.json").symlink_to(src / "run-record.json")
    refused(run_record)
    (out / "run-record.json").unlink()
    shutil.copy2(src / "run-record.json", out / "run-record.json")
    refused(cache)
    (out / "harmbench-pod.jsonl").write_text(json.dumps({"judge": "harmbench", "synthetic": False}) + "\n")
    refused(cache)
    (out / "harmbench-pod.jsonl").unlink()
    (out / "harmbench-pod.jsonl").symlink_to(src / "harmbench-pod.jsonl")
    refused(cache)
    (out / "harmbench-pod.jsonl").unlink()
    w.s37_copy("B")
    sealed = w.seal.seal_block("B")
    record = json.loads((w.root / "seals" / "block-B.json").read_text())
    hashed = {(f["host"], f["path"]): (f["sha256"], f["class"]) for f in record["files"]}
    for name in ("run-record.json", "harmbench-pod.jsonl"):
        assert hashed[("judges/B", f"pods/{HB_TAG}/fetched/out/{name}")] == (sha(out / name), "sealed")
    assert sealed["files"] == record["counts"]["files"] and w.plan()["seals"]["B"]["sha256"] == sealed["seal_sha256"]


def test_gb4_a_run_record_naming_no_cache_or_not_json_is_refused(w):
    """GB4, the run record's own cache field (the HB reader binds the cache by it): a run record at the recorded
    SHA-256 that names no cache SHA-256, or is not JSON, is a problem even with the cache file present."""
    _block_b_recorded(w, judges=("harmbench",))
    w.s37_copy("B")
    plan = w.plan()
    assert w.seal.hb_copy_problem(plan, "B") is None
    run_record = w.root / "judges" / "B" / "pods" / HB_TAG / "fetched" / "out" / "run-record.json"
    for body in (json.dumps({"device": "cuda", "judge": "harmbench"}), json.dumps({"cache": {"records": 1}}),
                 json.dumps({"cache": "x"}), "not json", "[1]"):
        run_record.write_text(body)
        plan["records"]["judges"]["B"]["judges"]["harmbench"]["run_record_sha256"] = sha(run_record)
        assert w.seal.hb_copy_problem(plan, "B") == (f"judges/B/pods/{HB_TAG}/fetched/out/harmbench-pod.jsonl is "
                                                     "missing or not the cache SHA-256 its run record names"), body


def test_gb4_no_copy_is_needed_when_harmbench_is_decided_not_run(w):
    """GB4: a block B whose HarmBench launch is named by a judge not-run decision (Granite recorded alone) seals with
    no pods/ folder at all."""
    r31._block_b_judged(w)
    w.tool.release("B")
    w.tool.record_judge_not_run(*r31._decision(w, ["harmbench"], reason="lead: synthetic: HarmBench not paid"))
    w.tool.record_judges("B", *w.file_judges(block="B", judges=("granite",)))
    assert w.tool.block_complete(w.plan(), "B") is True
    w.seal.seal_block("B")
    assert not (w.root / "judges" / "B" / "pods").exists() and "B" in w.plan()["seals"]


# ===== GB5 ===========================================================================================================

def test_gb5_the_pinned_judge_gpu_is_gate_bs_podhost_gpu():
    """GB5: stage1_rules.JUDGE_GPU equals the GPU constant of Gate B's judge launcher (pod/podhost.py, read as text)."""
    spec = importlib.util.spec_from_file_location("s1_rules_r33", rk.KIT / "stage1_rules.py")
    rules = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules)
    found = re.findall(r'^GPU = "([^"]+)"$', PODHOST.read_text(), re.M)
    assert found == [rules.JUDGE_GPU] == ["NVIDIA A100-SXM4-80GB"]


def test_gb5_record_judges_refuses_a_launch_whose_result_names_another_gpu_or_none(w):
    """GB5 both ways: record-judges B refuses (no record) a launch result whose verification.gpu is another GPU, a
    near name, empty or absent, for either judge (Granite is checked first by name order); the A100 result records."""
    r31._block_b_judged(w)
    w.tool.release("B")
    gpu_differs = r"tmp/judge-pod/s1b-{}-1/judge-pod-result\.json differs from the record \(gpu\)"
    for gpu in ("NVIDIA H100 80GB HBM3", "NVIDIA A100-SXM4-40GB", "NVIDIA A100-SXM4-80GB ", "", None):
        with pytest.raises(SystemExit, match="judge harmbench: " + gpu_differs.format("harmbench")):
            w.tool.record_judges("B", *w.file_judges(block="B", judges=("harmbench",), gpu=gpu))
        with pytest.raises(SystemExit, match="judge granite: " + gpu_differs.format("granite")):
            w.tool.record_judges("B", *w.file_judges(block="B", gpu=gpu))
    assert not (w.plan()["records"].get("judges") or {}).get("B")
    out = w.tool.record_judges("B", *w.file_judges(block="B"))
    assert out["judges"] == ["granite", "harmbench"] and w.tool.block_complete(w.plan(), "B") is True
