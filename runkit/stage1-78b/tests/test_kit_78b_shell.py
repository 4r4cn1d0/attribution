"""The 7-8B kit shell (K1 of T4): the constants block, the family refusal, block 0's plan shape and caps, the need
printout, the edit-arm command lines under the main config, pack_setup on both families. On CPU, no pod, no network;
every input synthetic (the World of tests/test_stage1_runkit.py), except the committed kit's own files and the
committed Gate B sealed MANIFEST, read for their hashes only.

    PYTHONDONTWRITEBYTECODE=1 PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests/test_kit_78b_shell.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import sys
from pathlib import Path

import pytest

import test_stage1_runkit as rk
from test_stage1_runkit import w, wf  # noqa: F401 - the 7-8B World fixtures (one family; both families)

KIT = rk.KIT
ROOT = KIT.parents[1]
X = rk.X


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_by_path(name: str, path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ===== 1. the constants block (plan T4 step 1; rules_78b.KIT) =======================================================
def test_the_constants_block_agrees_with_probes_the_configs_and_the_side_units(wf):
    w = wf
    r, r78 = w.rules, w.r78
    probes = importlib.import_module("probes")
    kit = r78.KIT[w.family]
    assert r.PROBE_KEY == kit["probe_key"] == w.family and w.family in probes.PROBES
    policy = probes.PROBES[w.family]["policy"]
    assert kit["instruct_model"] == {"repo_id": policy["repo_id"], "revision": policy["revision"], "gated": policy["gated"]}
    assert probes.PROBES[w.family]["prepared"] == kit["prepared_name"] == r.PREPARED_NAME
    assert r.PREPARED_MANIFESTS == {kit["prepared_name"]: r78.MANIFESTS[w.family]}
    assert r.REC == r78.CONFIGS[w.family]["main"][0] and r.REC_CONFIG_SHA256 == rk.MAIN_CONFIG[w.family]
    assert r.REC.split("/")[-1] == {"olmo2-7b": "study-kt-olmo2-7b-r64-b-mb2-20261008.json",
                                     "llama31-8b": "study-kt-llama31-8b-r64-b5e5-mb2-20261010.json"}[w.family]
    assert r.RECIPE_NAMES == {"B": r.REC} and set(r.RECIPE_PINS) == {r.REC}
    assert r.RECIPE_S is None and r.RECIPE_G is None and r.RECIPE_BQI is None            # null until filled (A1, A13)
    assert r78.RECIPE_S[w.family] is None and r78.RECIPE_G[w.family] is None and r78.RECIPE_BQI[w.family] is None
    assert r.TRAINING_IDENTITY == kit["training_identity"] and len(r.TRAINING_IDENTITY) == 64
    assert r.MAN_PATH == r78.SEALED_SETS[w.family]["path"]
    assert r.GATE_A_FIXTURE == kit["fixture"]["path"] and r.PREREG_FIXTURE_SHA256 == kit["fixture"]["sha256"]
    assert set(r.A0_UNITS) == ({"untuned", 1101, 1102, 1103} if w.family == "olmo2-7b" else {"untuned", 1101, 1102})
    for unit in r.A0_UNITS.values():
        assert len(unit["complete_sha256"]) == 64 and unit["path"].startswith("tmp/family-probe-sp-")
    # P78 §2.1's prefixes (R: P78:48-57) are the pinned hashes' first 16 hex.
    prefixes = {"olmo2-7b": {"untuned": "632fa4bd0a8f3b1b", 1101: "4a6d9ebc6636de57", 1102: "43e8412dc7ef8d3e",
                             1103: "4b5bd06dede08dc1"},
                "llama31-8b": {"untuned": "651f7f6de6721b41", 1101: "21427715565fb394", 1102: "b0c99f7b97e6e763"}}[w.family]
    assert {k: v["complete_sha256"][:16] for k, v in r.A0_UNITS.items()} == prefixes
    assert r.BASE_MODEL["revision"] is None and r.INSTRUCT_MODEL["repo_id"].endswith("-Instruct")
    with pytest.raises(SystemExit, match="no pinned revision"):
        probes.base_entry(w.family)
    with pytest.raises(SystemExit, match="no pinned revision"):
        probes.stage1_download_plan(w.family, with_base=True)
    with pytest.raises(SystemExit, match="not a 7-8B family"):
        probes.stage1_download_plan("olmo2-1b")
    assert [e["role"] for e in probes.stage1_download_plan(w.family)] == (
        ["policy", "audit_tokenizer", "guard"] if w.family == "olmo2-7b" else ["policy", "guard"])
    assert r.POD_SIZES == {"preflight_wait_s": 5400, "container_disk_gb": 60, "volume_gb": 50}
    assert r.MAX_ARMS_PER_POD == 4 == kit["max_arms_per_pod"] and kit["volume_gb"] == 50 == r78.VOLUME_GB
    assert r.POD_NAME_PREFIX == "attribution-s78-" and r.HOST_PREFIX == {"0": f"{w.family}-0", "sc": f"{w.family}-sc"}
    assert r.ENGINES == {"X": X} and r.ENGINE_X == X and r78.ENGINE_Y is None and r78.Y_MEASURED is False
    # the money rules carried over (the K1 brief)
    assert (r.PLANNING_PRICE_USD, r.RATE_USD, r.MAX_PRICE_USD, r.RESERVE_USD, r.CONTINGENCY_FACTOR) == (1.85, 1.79, 10.0, 6.0, 1.25)
    assert r.GATE_B_HOLD_USD == 0 and r.GATE_B_HOLD_REASON.startswith("Gate B closed 23 Oct")
    assert r.GUARD_OFF_KIND == "stage1 user decision: budget guard off" and r.GUARD_REFUSED_EXIT == 3
    assert r.POD_OVERHEAD_S == 48 * 60 and r.START_MARGIN_S == 1800 and r.CAP_STEP_S == 900
    assert not any(hasattr(r, name) for name in ("FRE_S", "O500_S", "ARM_MEASURED_S", "REGEN_MEASURED_S",
                                                  "DIAG_ESTIMATE_S", "C0_S", "EVAL_ONLY_S", "SIM_S"))   # no 1B timing
    assert w.tool.FUNDING_SOURCE_RULE == "user rule: start from the balance"
    # the committed Gate B sealed MANIFEST is the OLMo pin (the real file, hashed only)
    assert sha(ROOT / r78.SEALED_SETS["olmo2-7b"]["path"]) == "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8" \
        or not (ROOT / r78.SEALED_SETS["olmo2-7b"]["path"]).is_file()


def test_the_committed_kit_folder_names_no_family_and_plans_nothing(tmp_path, monkeypatch):
    for name in rk.MODULES:
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.syspath_prepend(str(KIT))
    r = importlib.import_module("stage1_rules")
    assert r.FAMILY is None and r.KIT_BLOCK is None and r.KIT_PROBLEM is None
    assert r.REC is None and r.PROBE_KEY is None and r.RECIPE_PINS == {} and r.HOST_PREFIX == {} and r.A0_UNITS == {}
    with pytest.raises(ValueError, match="names no family"):
        r.family_or_refuse()
    with pytest.raises(ValueError, match="names no family"):
        r.job_record("arm", "R", 1101, steps=33)
    with pytest.raises(ValueError, match="names no family"):
        r.block_runs(None, "0")
    tool = importlib.import_module("plan_tool")
    with pytest.raises(SystemExit, match="names no family"):
        tool.init_block(argparse.Namespace(block="0", jobs=str(tmp_path / "none.json"), funding=None, dry_run=True,
                                           group_jobs=None))
    pack = importlib.import_module("pack_setup")
    with pytest.raises(SystemExit, match="names no family"):
        pack.main(["X", "--dry-run"])
    # kit_identity: the KD7 names, kit-family.json and their disagreement
    assert r.kit_identity(Path("/x/tmp/family-probe-s78-olmo2-7b-0")) == {"family": "olmo2-7b", "block": "0", "problem": None}
    assert r.kit_identity(Path("/x/tmp/family-probe-s78-llama31-8b-A")) == {"family": "llama31-8b", "block": "A", "problem": None}
    for bad in ("family-probe-s78-olmo2-1b-0", "family-probe-olmo2-7b", "stage1-78b", "family-probe-s78-olmo2-7b-",
                "family-probe-s78-qwen25-7b-0", "family-probe-s1-olmo2-7b-0"):
        assert r.kit_identity(Path("/x/tmp") / bad)["family"] is None
    folder = tmp_path / "family-probe-s78-olmo2-7b-0"
    folder.mkdir()
    (folder / r.KIT_FAMILY_FILE).write_text(json.dumps({"kind": r.KIT_FAMILY_KIND, "family": "llama31-8b", "block": "0"}))
    assert r.kit_identity(folder)["family"] is None and "names llama31-8b" in r.kit_identity(folder)["problem"]
    (folder / r.KIT_FAMILY_FILE).write_text(json.dumps({"kind": r.KIT_FAMILY_KIND, "family": "olmo2-7b", "block": "0"}))
    assert r.kit_identity(folder) == {"family": "olmo2-7b", "block": "0", "problem": None}
    pod = tmp_path / "attribution-headroom"                           # the pod's folder: the file alone names the family
    pod.mkdir()
    (pod / r.KIT_FAMILY_FILE).write_text(json.dumps({"kind": r.KIT_FAMILY_KIND, "family": "llama31-8b", "block": "0"}))
    assert r.kit_identity(pod) == {"family": "llama31-8b", "block": "0", "problem": None}
    (pod / r.KIT_FAMILY_FILE).write_text("{not json")
    assert r.kit_identity(pod)["family"] is None and "not JSON" in r.kit_identity(pod)["problem"]


# ===== 2. the family refusal (KD7): plan, pack, launch never cross families ========================================
def test_one_family_per_working_copy_at_plan_pack_and_launch(wf, tmp_path):
    w = wf
    r, tool = w.rules, w.tool
    other = w.other
    assert r.family_or_refuse() == w.family and r.family_or_refuse(w.family) == w.family
    with pytest.raises(ValueError, match="never plans, packs or launches"):
        r.family_or_refuse(other)
    with pytest.raises(ValueError, match="unknown family"):
        r.family_or_refuse("olmo2-1b")
    with pytest.raises(ValueError, match="never plans"):
        r.job_record("arm", "R", 1101, steps=33, family=other)
    with pytest.raises(ValueError, match="never plans"):
        r.block0_need_report(other)
    # the jobs file of the other family, or a job naming it, refuses at init (dry run too)
    with pytest.raises(SystemExit, match="one family per copy"):
        w.init(launches=[{"hosts": [rk.n_layout(other)]}], family=other, dry_run=True)
    with pytest.raises(SystemExit, match="KD7"):
        w.init(launches=[{"hosts": [[{**j, "family": other} for j in rk.n_layout(w.family)]]}], dry_run=True)
    with pytest.raises(SystemExit, match="not N's layout"):
        w.init(launches=[{"hosts": [rk.n_layout(other)]}], dry_run=True)   # the other family's layout, unnamed
    # a plan.json of the other family refuses at load
    w.init()
    plan = w.plan()
    plan["family"] = other
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="not this working copy's"):
        tool.load()
    plan["family"], plan["kit_block"] = w.family, "A"
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="not this working copy's"):
        tool.load()
    plan["kit_block"] = "0"
    w.mac.save_plan(plan)
    assert tool.load()["family"] == w.family
    # an edit file on the other family's prepared set refuses (P78 §2.3 condition 3)
    folder = w.repo / Path(w.r78.SEALED_SETS[w.family]["path"]).parent
    e = folder / "edits" / "R_d1.json"
    doc = json.loads(e.read_text())
    doc["manifest_sha256"] = w.r78.MANIFESTS[other]
    e.write_text(json.dumps(doc))
    man = json.loads((folder / "MANIFEST.json").read_text())
    for f in man["files"]:
        if f.get("draw") == 1:
            f["sha256"] = sha(e)
    (folder / "MANIFEST.json").write_text(json.dumps(man))
    w.mp.setitem(w.r78.SEALED_SETS[w.family], "sha256", sha(folder / "MANIFEST.json"))
    (w.root / "plan.json").unlink()
    with pytest.raises(SystemExit, match="not on .* prepared set"):
        w.init(dry_run=True)
    # pack_setup: --family other and an inputs record of the other family refuse before anything is read
    pack = importlib.import_module("pack_setup")
    with pytest.raises(SystemExit, match="never plans, packs or launches"):
        pack.main(["X", "--family", other, "--dry-run"])
    rec = rk.write_json(tmp_path / "inputs.json", {"kind": pack.INPUTS_KIND, "engine": "X", "family": other, "inputs": []})
    with pytest.raises(SystemExit, match="one family"):
        pack.main(["X", "--inputs", str(rec), "--inputs-sha256", sha(rec), "--dry-run"])
    # the packed receipt of the other family refuses the release (launch never reads such a host)
    (w.root / "plan.json").unlink(missing_ok=True)                    # the refusal above wrote none
    rk.write_json(w.root / "setup" / "packed-stage1-X" / "setup-receipt.json",
                  {"engine_sha256": X, "sealed_files_sha256": "f" * 64, "family": other})
    e.write_text(json.dumps({**doc, "manifest_sha256": w.r78.MANIFESTS[w.family]}))
    for f in man["files"]:
        if f.get("draw") == 1:
            f["sha256"] = sha(e)
    (folder / "MANIFEST.json").write_text(json.dumps(man))
    w.mp.setitem(w.r78.SEALED_SETS[w.family], "sha256", sha(folder / "MANIFEST.json"))
    with pytest.raises(SystemExit, match="KD7"):
        w.init()
    # the sealed set of the other family is never a source: a null pin on the copy's own set refuses (A13)
    w.mp.setitem(w.r78.SEALED_SETS[w.family], "sha256", None)
    with pytest.raises(SystemExit, match="MANIFEST pin is null"):
        w.init(dry_run=True)


# ===== 3. block 0's plan shape and caps (ruling 11; KCR §7) =========================================================
def test_block_0_plan_shape_caps_edits_and_the_retrain_refusal(wf):
    w = wf
    r, r78, tool = w.rules, w.r78, w.tool
    out = w.init(dry_run=True)
    n = 4 if w.family == "llama31-8b" else 3
    cap = 12.5 if w.family == "llama31-8b" else 8.5
    spend = 20.80 if w.family == "llama31-8b" else 12.50
    pod = out["pods"][0]
    assert pod["host"] == f"{w.family}-0-1" and pod["cap_hours"] == cap and pod["counted"] == n
    assert pod["spend_upper_usd"] == spend and pod["guard_usd"] == rk.cents(6 + 1.85 * cap)
    assert pod["jobs"] == [f"arm:R:{s}" for s in (1101, 1102, 1103)] + (["a0_arm:a0:1103"] if n == 4 else [])
    assert [(e["arm"], e["seed"], e["path"].split("/")[-1]) for e in pod["edits"]] == [
        ("R", 1101, "R_d1.json"), ("R", 1102, "R_d2.json"), ("R", 1103, "R_d3.json")]
    assert out["main_config"] == {"path": r.REC, "config_sha256": rk.MAIN_CONFIG[w.family]}
    assert out["this_pod_need_usd"] == rk.times_125(rk.cents(6 + 1.85 * cap))
    # by hand from KCR §4 and §7 (R: KCR:100, :165-177): the cap is the largest over k of 48 min + the measured uppers
    # before k + job k's requirement, rounded up to 0.25 h
    f = r78.FAMILIES[w.family]
    measured = 1.15 * f["ARM_JOB_MAX_S"]
    gen = max(f["FIRST_BATCH_MAX_S"], f["BATCH_MAX_S"]) + 33 * f["BATCH_MAX_S"]
    req = lambda steps: steps * f["TRAIN_STEP_MAX_S"] + gen + 1250 + f["EARLY_MAX_S"] + f["OUTSIDE_MAX_S"] + 1800
    steps = [33, 33, 33] + ([38] if n == 4 else [])
    worst = max(48 * 60 + k * measured + req(s) for k, s in enumerate(steps))
    assert rk.quarter_up(worst) == cap if hasattr(rk, "quarter_up") else True
    import math
    assert math.ceil(worst / 900) * 900 / 3600 == cap
    assert rk.cents((48 * 60 + n * measured) / 3600 * 1.79) == spend
    # the real init: the plan's records
    w.init()
    plan = w.plan()
    h = plan["hosts"][f"{w.family}-0-1"]
    assert h["block"] == "0" and h["engine"] == "X" and h["engine_sha256"] == X and h["cap_hours"] == cap
    assert h["volume_gb"] == 50 and h["container_disk_gb"] == 60 and h["preflight_wait_s"] == 5400
    assert h["sealed_files_sha256"] == "f" * 64 and h["counted"] == n and len(h["jobs"]) == n
    for j, (arm, seed) in zip(h["jobs"], r78.block0_runs(w.family)):
        assert (j["arm"], j["seed"], j["family"], j["recipe"], j["engine"]) == (arm, seed, w.family, "B", "X")
        assert j["kind"] == ("a0_arm" if arm == "a0" else "arm") and j["steps"] == (38 if arm == "a0" else 33)
        assert j["measured_upper_s"] == j["spend_upper_s"] == pytest.approx(measured) and j["counted"] == 1
        assert j["start_requirement_s"] == pytest.approx(req(j["steps"])) and not j["unmeasured"]
        if arm == "R":
            assert j["edit"]["sha256"] == sha(w.repo / j["edit"]["path"]) and j["edit"]["path"].endswith(f"R_d{seed - 1100}.json")
            assert j["edit"]["counts"] == {"remove": 600, "add": 0, "rewrite": 0}
            assert j["edit"]["manifest_sha256"] == r78.MANIFESTS[w.family] and j["edit"]["source"].startswith("sealed-set:")
            assert rk.SENTINEL not in json.dumps(j)                   # no row id of the edit enters the plan
        else:
            assert j["edit"] is None
    assert plan["recipes"] == {r.REC: {"sha256": r.RECIPE_PINS[r.REC], "config_sha256": rk.MAIN_CONFIG[w.family],
                                       "training_identity": r.TRAINING_IDENTITY}}
    assert ("config", r.REC) in w.calls and ("identity", r.REC) in w.calls
    assert plan["fixture"]["recipe_sha256"] == rk.MAIN_CONFIG[w.family] and plan["fixture"]["training_s"] == 952.03
    assert plan["sealed_set"]["sha256"] == r78.SEALED_SETS[w.family]["sha256"] and plan["gate_b_hold_usd"] == 0
    assert rk.SENTINEL not in (w.root / "plan.json").read_text()
    assert rk.SENTINEL not in (w.root / "operator-actions.jsonl").read_text()
    # launch.py's own check: the plan's cap equals the cap of its jobs
    launch = importlib.import_module("launch")
    launch.check_hosts(plan, [f"{w.family}-0-1"])
    plan["hosts"][f"{w.family}-0-1"]["cap_hours"] = cap + 0.25
    with pytest.raises(SystemExit, match="differs from the cap"):
        launch.check_hosts(plan, [f"{w.family}-0-1"])
    # the retrain kind: priced (its need prints) but refused as a job while RECIPE_S is null (A1)
    with pytest.raises(w.r78.Refused, match="not written yet"):
        r.retrain_job()
    (w.root / "plan.json").unlink()
    with pytest.raises(SystemExit, match="recipe S_78 .* not written yet"):
        w.init(launches=[{"hosts": [[{"kind": "retrain", "arm": "a0", "seed": 1101}]]}], dry_run=True)
    w.mp.setitem(r78.RECIPE_S, w.family, "ab" * 32)
    assert r.retrain_job()["kind"] == "retrain" and r.retrain_job()["unmeasured"]
    with pytest.raises(SystemExit, match="does not belong to block 0"):
        w.init(launches=[{"hosts": [[{"kind": "retrain", "arm": "a0", "seed": 1101}]]}], dry_run=True)
    for kind in ("anchor", "untuned_answers", "rep_pass", "evalonly"):
        with pytest.raises(SystemExit, match="does not belong to block 0|not written yet"):
            w.init(launches=[{"hosts": [rk.n_layout(w.family) + [{"kind": kind}]]}], dry_run=True)
    with pytest.raises(SystemExit, match="unknown kind"):
        w.init(launches=[{"hosts": [[{"kind": "w1_18"}]]}], dry_run=True)


@pytest.mark.parametrize("launches, match", [
    ([{"hosts": [[{"kind": "arm", "arm": "R", "seed": 1101}, {"kind": "arm", "arm": "R", "seed": 1102}]]}], "not N's layout"),
    ([{"hosts": [[{"kind": "arm", "arm": "R", "seed": 1102}, {"kind": "arm", "arm": "R", "seed": 1101},
                  {"kind": "arm", "arm": "R", "seed": 1103}]]}], "not N's layout"),
    ([{"hosts": [[{"kind": "arm", "arm": "R", "seed": 1101}], [{"kind": "arm", "arm": "R", "seed": 1102}]]}], "one pod"),
    ([{"hosts": [[{"kind": "arm", "arm": "R", "seed": 1101}]]}, {"hosts": [[{"kind": "arm", "arm": "R", "seed": 1102}]]}],
     "one launch"),
    ([{"deal": [0]}], "one launch of one pod"),
    ([{"judge": {"arms": 3}}], "one launch of one pod"),
    ([{"hosts": [[{"kind": "arm", "arm": "A1", "seed": 1101}, {"kind": "arm", "arm": "R", "seed": 1102},
                  {"kind": "arm", "arm": "R", "seed": 1103}]]}], "not N's layout"),
    ([{"hosts": [[{"kind": "arm", "arm": "R", "seed": 1101, "recipe": "S"}, {"kind": "arm", "arm": "R", "seed": 1102},
                  {"kind": "arm", "arm": "R", "seed": 1103}]]}], "main config"),
    ([{"hosts": [[{"kind": "arm", "arm": "R", "seed": 1101, "engine": "Y"}, {"kind": "arm", "arm": "R", "seed": 1102},
                  {"kind": "arm", "arm": "R", "seed": 1103}]]}], "engine X"),
    ([{"hosts": [[{"kind": "arm", "arm": "R", "seed": 1101, "points": ["x"]}, {"kind": "arm", "arm": "R", "seed": 1102},
                  {"kind": "arm", "arm": "R", "seed": 1103}]]}], "keys must be among"),
    ([{"hosts": [[{"kind": "arm", "arm": "R", "seed": 1101}, {"kind": "arm", "arm": "R", "seed": 1102},
                  {"kind": "arm", "arm": "R", "seed": 1103}, {"kind": "a0_arm", "arm": "a0", "seed": 1103}]]}],
     "Llama-3.1-8B only"),
])
def test_a_jobs_file_that_departs_from_ns_layout_refuses(w, launches, match):
    with pytest.raises(SystemExit, match=match):
        w.init(launches=launches, dry_run=True)
    assert not (w.root / "plan.json").exists()


def test_the_1b_blocks_refuse_in_this_copy(w):
    r = w.rules
    assert r.BLOCKS == ("0", "sc") and r.BLOCKS_1B == ("S1-0", "cert", "A", "certify", "B", "C", "sim", "P")
    for block in r.BLOCKS_1B + ("D", "1"):
        with pytest.raises(ValueError, match="block 0 only"):
            r.block_runs("A", block)
        with pytest.raises(SystemExit, match="block 0 only"):
            w.init(block=block, dry_run=True)
    with pytest.raises(ValueError, match="reuses no unit"):
        r.block_runs(None, "0", (("R", 1101),))
    assert r.block_runs(None, "0") == [("R", 1101), ("R", 1102), ("R", 1103)]
    assert r.deal([("R", 1103), ("R", 1101), ("R", 1102)]) == [[("R", 1101), ("R", 1102), ("R", 1103)]]
    with pytest.raises(ValueError, match="listed twice"):
        r.deal([("R", 1101), ("R", 1101), ("R", 1102)])
    with pytest.raises(ValueError, match="N's layout"):
        r.deal([("R", 1101), ("R", 1102), ("R", 1103), ("a0", 1103)])


# ===== 4. the need printout (the check's M3; addendum A8) ==========================================================
def test_the_need_printout_lists_n_the_retrain_pods_and_the_scorer_pods(wf, capsys):
    w = wf
    r, r78 = w.rules, w.r78
    report = r.block0_need_report()
    lines = report["lines"]
    assert lines[0].startswith("need N (block 0, both families, one launch of 2 pods; KCR:177): $56.06 (guard $44.85, "
                               "spend upper $33.30, contingency $11.21)")
    cap = 12.5 if w.family == "llama31-8b" else 8.5
    assert lines[1].startswith(f"need N this family's pod alone ({w.family}-0-1, cap {cap:.2f} h")
    assert lines[1].endswith(f"${rk.times_125(rk.cents(6 + 1.85 * cap)):.2f}")
    retrain = [x for x in lines if x.startswith("need retrain pod ")]
    assert [x.split()[3] for x in retrain] == ["olmo2-7b", "llama31-8b"]            # one per family (A8)
    for x in retrain:
        assert "cap 4.50 h" in x and "engine Y" in x and "recipe S_78" in x
        assert x.endswith(f"${rk.times_125(rk.cents(6 + 1.85 * 4.5)):.2f}")       # $17.91: 1.25 x (6 + 4.5 x 1.85)
    scorer = [x for x in lines if x.startswith("need scorer pod ")]
    assert len(scorer) == 2 * len(r78.SCORER_KINDS) == 18                           # PP8: rep_pass AND a1_pass; PP17
    for family in r78.FAMILIES:
        for kind in r78.SCORER_KINDS:
            line = next(x for x in scorer if x.startswith(f"need scorer pod {family} {kind} "))
            cap_k = r78.e_cap_hours(family, kind)
            assert f"single-job E cap {cap_k:.2f} h" in line
            assert line.endswith(f"${rk.times_125(rk.cents(6 + 1.85 * cap_k)):.2f}")
            assert f" {kind} ({r78.KIND_LABELS[kind]}; " in line                     # PP8: the printout's labels
    a1 = next(x for x in scorer if " a1_pass " in x and "olmo2-7b" in x)
    assert a1.endswith("$45.66") and "E cap 16.50 h" in a1 and "A1's attributes pass" in a1   # KD6's 16.5 h cap (PP8)
    rep = next(x for x in scorer if " rep_pass " in x and "olmo2-7b" in x)
    assert rep.endswith("$18.49") and "E cap 4.75 h" in rep and "REQ-3's representation pass" in rep   # 1 h x 2.3 x 1.5
    for family, n in (("olmo2-7b", 3), ("llama31-8b", 2)):                      # PP17: one pod per reused a0 seed
        regen = next(x for x in scorer if " o_only_with_regenerate " in x and family in x)
        assert f"; {n} pods, one per reused a0 seed, each: single-job E cap 4.50 h" in regen and regen.endswith("$17.91")
    cls = next(x for x in scorer if " classifier " in x and "llama31-8b" in x)
    assert "recipe S_78" in cls                                                          # PP4: the classifier under S_78
    # KD5's idle-storage line (D2): about $0.33 per day per stopped 50 GB pod; N's two pods: $0.67 per day, $20 per month
    idle = [x for x in lines if x.startswith("idle storage (KD5; E, KCR:161): ")]
    assert idle == [lines[-13]]                                                        # D2's N line, then PP14's lines
    assert "about $0.33 per day per stopped 50 GB pod that keeps its states ($0.20 per GB per month)" in idle[0]
    assert "N's 2 pods kept stopped: $0.67 per day, about $20.00 per month; counted in no guard" in idle[0]
    assert report["idle_storage"] == {"volume_gb": 50, "usd_per_gb_month": 0.2, "usd_per_pod_day": 0.33, "n_pods_kept": 2,
                                      "usd_per_day": 0.67, "usd_per_month": 20.0, "basis": report["idle_storage"]["basis"]}
    assert report["idle_storage"]["basis"].startswith("E: ") and "KCR:161" in report["idle_storage"]["basis"]
    assert rk.cents(50 * 0.20 / 30) == 0.33                                             # the arithmetic by hand
    # PP14: one idle-storage line per other block-0 pod that keeps states (round 4b's one definition, SC_STATE_KINDS:
    # per family the retrain, a1_pass, one o_only_with_regenerate pod per reused seed, c0), then the block's total
    assert lines[-12:] == r78.idle_storage_lines(r78.block0_report())[1:]
    assert [x.split(" (KD5")[0] for x in lines[-12:-1]] == [
        "idle storage retrain olmo2-7b", "idle storage scorer olmo2-7b a1_pass",
        "idle storage scorer olmo2-7b o_only_with_regenerate 1101", "idle storage scorer olmo2-7b o_only_with_regenerate 1102",
        "idle storage scorer olmo2-7b o_only_with_regenerate 1103", "idle storage scorer olmo2-7b c0",
        "idle storage retrain llama31-8b", "idle storage scorer llama31-8b a1_pass",
        "idle storage scorer llama31-8b o_only_with_regenerate 1101",
        "idle storage scorer llama31-8b o_only_with_regenerate 1102", "idle storage scorer llama31-8b c0"]
    assert lines[-1].startswith("idle storage block 0 in all (KD5, PP14; E): 13 pods") and "$4.33 per day" in lines[-1]
    assert report["idle_storage_all"] == r78.idle_storage(13) and len(report["idle_storage_pods"]) == 13
    assert len(lines) == 2 + 2 + 18 + 1 + 11 + 1
    # the CLI prints each line, then the JSON (the lines are in it too), on the dry run and the real init
    assert w.tool.main(["init-block", "0", "--jobs", w.n_jobs(), "--dry-run"]) == 0
    printed = capsys.readouterr().out.strip().splitlines()
    assert printed[:-1] == lines and json.loads(printed[-1])["need_lines"] == lines
    assert json.loads(printed[-1])["retrain_pods"] == {f: {"cap_hours": 4.5, "need_usd": 17.91} for f in r78.FAMILIES}
    assert json.loads(printed[-1])["idle_storage"] == report["idle_storage"]            # D2: in the summary JSON too
    assert json.loads(printed[-1])["idle_storage_pods"] == report["idle_storage_pods"]  # PP14: in the summary JSON too
    assert json.loads(printed[-1])["idle_storage_all"] == report["idle_storage_all"]
    assert json.loads(printed[-1])["scorer_pods"]["olmo2-7b"]["a1_pass"] == {"cap_hours": 16.5, "need_usd": 45.66}
    assert json.loads(printed[-1])["scorer_pods"]["olmo2-7b"]["rep_pass"] == {"cap_hours": 4.75, "need_usd": 18.49}
    assert w.tool.main(["init-block", "0", "--jobs", w.n_jobs(), "--funding", w.funding("0", 56.06)]) == 0
    printed = capsys.readouterr().out.strip().splitlines()
    assert printed[:-1] == lines and json.loads(printed[-1])["hosts"] == [f"{w.family}-0-1"]
    assert w.plan()["blocks"]["0"]["need_lines"] == lines
    # the numbers are rules_78b's block0 report (KCR:177; the E caps)
    b0 = r78.block0_report()
    assert report["n"] == b0["n"] and report["retrain_pods"] == b0["retrain_pods"] and report["scorer_pods"] == b0["scorer_pods"]


# ===== 5. the edit-arm command lines under the main config (P78:99) =================================================
def test_the_edit_arm_commands_run_the_main_config_never_a_recipe_s_sibling(wf):
    w = wf
    r = w.rules
    w.init()
    plan = w.plan()
    jobs = plan["hosts"][f"{w.family}-0-1"]["jobs"]
    prepared = f"data/kt-prepared/{r.PREPARED_NAME}"
    for job in jobs:
        commands = r.arm_commands(job, prepared)
        assert len(commands) == 1 and commands[0][0] == "calibrate"
        argv = commands[0][1]
        assert argv[:4] == ["venv/bin/python", "-m", "experiments.safety_selection", "calibrate"]
        assert argv[argv.index("--recipe") + 1] == r.REC == w.r78.CONFIGS[w.family]["main"][0]
        assert "gateb" not in argv[argv.index("--recipe") + 1] and "-s78-" not in argv[argv.index("--recipe") + 1]
        assert argv[argv.index("--prepared") + 1] == prepared
        assert argv[argv.index("--seeds") + 1] == str(job["seed"])
        assert argv[argv.index("--checkpoints") + 1] == "e1" and argv[argv.index("--out-root") + 1] == "round1"
        if job["kind"] == "arm":
            digest = job["edit"]["sha256"]
            assert argv[argv.index("--arms") + 1] == f"edit-{digest}"
            assert argv[argv.index("--edit") + 1] == f"edits/{digest}.edit.json"
        else:
            assert argv[argv.index("--arms") + 1] == "a0" and "--edit" not in argv
        assert rk.SENTINEL not in " ".join(argv)
    # refusals: another recipe, an edit arm without its edit, a kind outside block 0, the other family's job
    arm = dict(jobs[0])
    with pytest.raises(ValueError, match="main config"):
        r.arm_commands({**arm, "recipe": "S"}, prepared)
    with pytest.raises(ValueError, match="bound edit"):
        r.arm_commands({**arm, "edit": None}, prepared)
    with pytest.raises(ValueError, match="not a block-0 kind"):
        r.arm_commands({**arm, "kind": "retrain"}, prepared)
    with pytest.raises(ValueError, match="this copy is"):
        r.arm_commands({**arm, "family": w.other}, prepared)
    with pytest.raises(ValueError, match="a0 without an edit"):
        r.arm_commands({**arm, "kind": "a0_arm"}, prepared)
    # the stage-1 runner's form (R: runkit/stage1-olmo/setup/job_runner_stage1.py:458-461): the same flags, in order
    runner = (rk.STAGE1 / "setup" / "job_runner_stage1.py").read_text()
    assert '"calibrate", "--prepared", p, "--recipe", rec, "--arms", arm,' in runner
    assert '*edit, "--seeds", str(seed), "--checkpoints", "e1", "--out-root", ROUND' in runner


# ===== 6. pack_setup on both families ===============================================================================
def fake_engine_tree(repo: Path) -> None:
    """A synthetic engine tree at ROOT = repo: the files pack_setup bundles (names only; nothing of the real engine)."""
    for rel in ("experiments/minimal_safety/requirements.lock", "experiments/minimal_safety/common.py",
                "experiments/safety_selection/__init__.py", "experiments/safety_selection/config.py",
                "experiments/safety_selection/README.md"):
        rk.write_json(repo / rel, {"synthetic": rel}) if rel.endswith(".json") else (
            (repo / rel).parent.mkdir(parents=True, exist_ok=True), (repo / rel).write_text(f"# synthetic {rel}\n"))
    for name in ("cuda_preflight_family.py", "cuda_preflight_killtest.py", "cuda_preflight_headroom_v3.py",
                 "cuda_preflight_headroom.py"):
        (repo / "scripts").mkdir(exist_ok=True)
        (repo / "scripts" / name).write_text(f"# synthetic {name}\n")
    (repo / "tmp" / "study-v2-20261002").mkdir(parents=True, exist_ok=True)
    (repo / "tmp" / "study-v2-20261002" / "process_receipt.py").write_text("# synthetic process_receipt\n")


def prepared_set(w) -> Path:
    folder = w.repo / w.rules.PREPARED_LOCAL / w.rules.PREPARED_NAME
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.sha256").write_text(w.rules.PREPARED_MANIFESTS[w.rules.PREPARED_NAME] + "\n")
    rk.write_json(folder / "manifest.json", {"kind": "prepared (synthetic)", "rows": 4800})
    return folder


def test_pack_setup_dry_run_and_pack_on_both_families(wf, capsys, monkeypatch):
    w = wf
    r, r78 = w.rules, w.r78
    pack = importlib.import_module("pack_setup")
    fake_engine_tree(w.repo)
    prepared_set(w)
    monkeypatch.setattr(pack, "engine_code", lambda tree: X)
    monkeypatch.setattr(pack, "config_sha256", lambda tree, rel: r.REC_CONFIG_SHA256 if rel == r.REC else "0" * 64)
    monkeypatch.setattr(pack, "git_state", lambda: "f5e3b4c" + "0" * 33)
    shutil.rmtree(w.root / "setup" / "packed-stage1-X")             # the World's fake receipt; the pack writes its own
    pack.main(["X", "--dry-run", "--family", w.family])
    out = json.loads(capsys.readouterr().out)
    assert out["dry_run"] and out["engine_sha256"] == X and out["family"] == w.family and out["kit_block"] == "0"
    assert out["main_config"] == {"path": r.REC, "sha256": r.RECIPE_PINS[r.REC], "config_sha256": rk.MAIN_CONFIG[w.family]}
    assert out["prepared_manifests"] == {r.PREPARED_NAME: r78.MANIFESTS[w.family]}
    assert out["sealed_set"]["manifest"] == r78.SEALED_SETS[w.family] and sorted(out["sealed_set"]["edits"]) == ["1", "2", "3"]
    assert not (w.root / "setup" / "packed-stage1-X").exists()
    # a wrong engine identity, a config whose engine hash is not the pin, a null sealed-set pin: each refuses
    monkeypatch.setattr(pack, "engine_code", lambda tree: "34bfd288" + "0" * 56)
    with pytest.raises(SystemExit, match="not engine X's pin"):
        pack.main(["X", "--dry-run"])
    monkeypatch.setattr(pack, "engine_code", lambda tree: X)
    monkeypatch.setattr(pack, "config_sha256", lambda tree, rel: "0" * 64)
    with pytest.raises(SystemExit, match="config_sha256"):
        pack.main(["X", "--dry-run"])
    monkeypatch.setattr(pack, "config_sha256", lambda tree, rel: r.REC_CONFIG_SHA256)
    pin = r78.SEALED_SETS[w.family]["sha256"]
    monkeypatch.setitem(r78.SEALED_SETS[w.family], "sha256", None)
    with pytest.raises(SystemExit, match="MANIFEST pin is null"):
        pack.main(["X", "--dry-run"])
    monkeypatch.setitem(r78.SEALED_SETS[w.family], "sha256", pin)
    # the real pack
    pack.main(["X"])
    receipt = json.loads((w.root / "setup" / "packed-stage1-X" / "setup-receipt.json").read_text())
    assert receipt["engine_sha256"] == X and receipt["family"] == w.family and receipt["git_commit"].startswith("f5e3b4c")
    assert receipt["main_config"]["config_sha256"] == rk.MAIN_CONFIG[w.family] and receipt["sealed_set"]["sha256"] == pin
    assert sorted(receipt["edits"]) == ["R_d1", "R_d2", "R_d3"]
    members = receipt["members"]
    for name in ("stage1_rules.py", "rules_78b.py", "measured-basis-78b.json", "kit-family.json", "probe.json",
                 "job_runner_stage1.py", "preflight_stage1.py", "download_models_stage1.py", "process_receipt.py"):
        assert name in members, name
    assert members["rules_78b.py"] == sha(w.root / "rules_78b.py") and members["stage1_rules.py"] == sha(w.root / "stage1_rules.py")
    fam = json.loads((w.root / "setup" / "packed-stage1-X" / "kit-family.json").read_text())
    assert fam == {"kind": r.KIT_FAMILY_KIND, "family": w.family, "block": "0"}
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    assert sealed["family"] == w.family and sealed["inputs"] == {}
    edits = [k for k in sealed["files"] if k.startswith("edits/")]
    assert len(edits) == 3 and all(k == f"edits/{v}.edit.json" for k, v in sealed["files"].items() if k.startswith("edits/"))
    assert any(k.startswith(f"data/kt-prepared/{r.PREPARED_NAME}/") for k in sealed["files"])
    assert r.REC in sealed["files"] and sealed["files"][r.REC] == r.RECIPE_PINS[r.REC]
    probe = json.loads((w.root / "setup" / "packed-stage1-X" / "probe.json").read_text())
    assert probe["probe"] == w.family and probe["family"] == w.family and [e["role"] for e in probe["plan"]][0] == "policy"
    assert hashlib.sha256((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_bytes()).hexdigest() == receipt["sealed_files_sha256"]
    bootstrap = (w.root / "setup" / "packed-stage1-X" / "worker_bootstrap_stage1.sh").read_text()
    assert X in bootstrap and r78.GPU_NAME in bootstrap and "setuptools==78.1.0" in bootstrap and "hf_" not in bootstrap
    assert rk.SENTINEL not in json.dumps(receipt) and rk.SENTINEL not in json.dumps(sealed)
    with pytest.raises(SystemExit, match="never overwritten"):
        pack.main(["X"])
    # the release accepts this receipt (engine X, this family) and refuses the other family's
    w.init()
    assert w.plan()["hosts"][f"{w.family}-0-1"]["sealed_files_sha256"] == receipt["sealed_files_sha256"]


def test_the_release_needs_engine_xs_receipt_and_the_main_configs_identity(wf):
    w = wf
    r = w.rules
    rk.write_json(w.root / "setup" / "packed-stage1-X" / "setup-receipt.json",
                  {"engine_sha256": "34bfd288" + "0" * 56, "sealed_files_sha256": "f" * 64, "family": w.family})
    with pytest.raises(SystemExit, match="differs from its pin"):
        w.init()
    rk.write_json(w.root / "setup" / "packed-stage1-X" / "setup-receipt.json",
                  {"engine_sha256": X, "sealed_files_sha256": "f" * 64, "family": w.family})
    w.config[r.REC] = "0" * 64                                         # the engine hashes the main config to another value
    with pytest.raises(SystemExit, match="config_sha256"):
        w.init()
    w.config[r.REC] = r.REC_CONFIG_SHA256
    w.identity[r.REC] = "1" * 64                                       # another training identity (P78 §2.3)
    with pytest.raises(SystemExit, match="training identity"):
        w.init()
    w.identity[r.REC] = r.TRAINING_IDENTITY
    (w.repo / r.REC).write_text("{changed bytes}")                    # the file's bytes off their pin
    with pytest.raises(SystemExit, match="differs from its pin"):
        w.init()
    rk.write_json(w.repo / r.REC, {"recipe": r.REC, "synthetic": True})
    (w.root / "setup" / "packed-stage1-X" / "setup-receipt.json").unlink()
    with pytest.raises(SystemExit, match="no packed stage1-X"):
        w.init()
