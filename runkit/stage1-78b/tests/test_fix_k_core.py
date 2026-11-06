"""fix-K-core: the core verifier's D1, D4 and D5 at the kit level (plan_tool and pack_setup on the synthetic World in
BOTH committed MANIFEST forms, the fixture's family check, and the committed sealed sets by pin). Every World input is
synthetic except the committed sets' MANIFEST and R_d1-R_d3 edit files, which are copied into the World by path and
hashed; no row id, prompt or answer is printed (the edit files are read for one key, manifest_sha256, as the kit does)."""
from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import sys
from pathlib import Path

import pytest

import test_stage1_runkit as rk
from test_stage1_runkit import World, MODULES, sha, write_json, wf  # noqa: F401 - wf: the both-families World fixture

KIT = Path(__file__).resolve().parents[1]
ROOT = KIT.parents[1]
PINS = {"llama31-8b": "2a1db220cdc0cc73e0818ad0c12d1f2ce2789a465002f5efb2145aabf41f594c",
        "olmo2-7b": "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"}
REAL_R_EDITS = {
    "llama31-8b": {1: "5cdedf22c1002ef1c6d0322d44c253ef57580ddb1dda85e8119a8b3842dc29b4",
                   2: "8f9f3cd5027d9268b28e3cf4189987a820b26a6d6d77fbe83ea0ad145944bb95",
                   3: "edbc111b2ff3a446ae195a79f0e5965c9a82fa744266d57c9c15e4c4c775dd2e"},
    "olmo2-7b": {1: "f7d7eb86cb58f7a5e7e1408973a13531f74845e066d7328d6e726ecdd442ffdd",
                 2: "913b73606ff64c104751e3f86bd3b69838a27686720a92858c08f4cf087d8060",
                 3: "cd8d3328c48957ed0a164a8775ca2695a3d77d51865fd32c2ee53aded939502b"},
}


@pytest.fixture(params=[(f, form) for f in ("olmo2-7b", "llama31-8b") for form in ("gateb", "llama")],
                ids=lambda p: f"{p[0]}-{p[1]}-form")
def wff(request, tmp_path, monkeypatch):
    """A World of either family with its sealed set's MANIFEST in either committed form (D5)."""
    family, form = request.param
    world = World(tmp_path, monkeypatch, family, manifest_form=form)
    yield world
    for name in MODULES:
        sys.modules.pop(name, None)


def expected_edits(w) -> dict:
    man = json.loads((w.sealed_folder / "MANIFEST.json").read_text())
    return {e["draw"]: e for e in man["files"] if e.get("family") == "R" and e.get("draw") in (1, 2, 3)}


# ===== D1 / D5: both MANIFEST forms plan and pack block 0 on both families =========================================
def test_d5_both_manifest_forms_plan_block0_binding_r_d1_to_r_d3_by_family_and_draw(wff):
    w = wff
    tool, r78 = w.tool, w.r78
    man = tool.manifest()
    if w.manifest_form == "gateb":
        assert all(e["role"] == "edit" for e in man["files"] if e.get("family") in ("R", "M", "unit"))
        assert sum(1 for e in man["files"] if e.get("family") == "M" and e.get("draw") == 1) == 2   # the trap, present
        assert [e["role"] for e in man["files"] if e.get("path") == "unit_table.json"] == ["counts"]
    else:
        assert not any(e.get("role") == "edit" for e in man["files"])
        assert [e["seed"] for e in man["files"] if e.get("family") == "R"] == [1101, 1102, 1103, 1104, 1105]
        assert man["roles"]["1"].startswith("block 0 (N)")
    arms = tool.man_arms(man)
    assert len(arms) == (3 + 2 + 4 if w.manifest_form == "gateb" else 5 + 2)     # every edit entry, R, M and unit
    assert all(a.startswith("edit-") for a in arms)
    out = w.init(dry_run=True)
    assert out["dry_run"] and out["family"] == w.family
    want = expected_edits(w)
    assert [(e["seed"], e["sha256"]) for e in out["pods"][0]["edits"]] == [(1100 + d, want[d]["sha256"]) for d in (1, 2, 3)]
    w.init()
    plan = w.plan()
    host = plan["hosts"][f"{w.family}-0-1"]
    r_jobs = [j for j in host["jobs"] if j["kind"] == "arm"]
    assert [j["seed"] for j in r_jobs] == [1101, 1102, 1103]
    for j in r_jobs:
        d = j["seed"] - 1100
        assert j["edit"]["sha256"] == want[d]["sha256"] and j["edit"]["engine_arm"] == want[d]["arm"]
        assert j["edit"]["path"].endswith(f"edits/R_d{d}.json") and j["edit"]["counts"] == {"remove": 600, "add": 0, "rewrite": 0}
        assert j["edit"]["manifest_sha256"] == r78.MANIFESTS[w.family]
    assert ([j["seed"] for j in host["jobs"] if j["kind"] == "a0_arm"] == [1103]) is (w.family == "llama31-8b")
    assert host["cap_hours"] == (12.5 if w.family == "llama31-8b" else 8.5)
    sources = tool.edit_sources(plan)
    assert sorted(sources) == [("R", 1), ("R", 2), ("R", 3)]                     # never an M or a unit edit
    assert all(len(v) == 1 for v in sources.values())
    # the plan's text holds no M-family or unit edit hash and no trap row id
    text = (w.root / "plan.json").read_text()
    m_and_unit = [e["sha256"] for e in man["files"] if e.get("family") in ("M", "unit")]
    assert m_and_unit and not any(h in text for h in m_and_unit) and rk.SENTINEL not in text


def test_d5_both_manifest_forms_pack_block0(wff, capsys, monkeypatch):
    from test_kit_78b_shell import fake_engine_tree, prepared_set, X
    w = wff
    r, r78 = w.rules, w.r78
    pack = importlib.import_module("pack_setup")
    fake_engine_tree(w.repo)
    prepared_set(w)
    monkeypatch.setattr(pack, "engine_code", lambda tree: X)
    monkeypatch.setattr(pack, "config_sha256", lambda tree, rel: r.REC_CONFIG_SHA256 if rel == r.REC else "0" * 64)
    monkeypatch.setattr(pack, "git_state", lambda: "f5e3b4c" + "0" * 33)
    shutil.rmtree(w.root / "setup" / "packed-stage1-X")
    pack.main(["X", "--dry-run", "--family", w.family])
    out = json.loads(capsys.readouterr().out)
    want = expected_edits(w)
    assert out["sealed_set"]["manifest"] == r78.SEALED_SETS[w.family]
    assert {int(d): e["sha256"] for d, e in out["sealed_set"]["edits"].items()} == {d: want[d]["sha256"] for d in (1, 2, 3)}
    assert {int(d): e["seed"] for d, e in out["sealed_set"]["edits"].items()} == {1: 1101, 2: 1102, 3: 1103}
    pack.main(["X", "--family", w.family])
    receipt = json.loads((w.root / "setup" / "packed-stage1-X" / "setup-receipt.json").read_text())
    assert sorted(receipt["edits"]) == ["R_d1", "R_d2", "R_d3"]
    assert {k: e["sha256"] for k, e in receipt["edits"].items()} == {f"R_d{d}": want[d]["sha256"] for d in (1, 2, 3)}


def test_d1_a_manifest_that_lists_the_m_edits_by_draw_alone_would_refuse(wff):
    """Why the family clause matters (V-H17): an R_d1 found by draw alone would meet Gate B's two M edits at draw 1.
    Here the kit's reader is asked for draw 1 over a manifest whose only draw-1 entries are M edits: it refuses with
    the missing-draw text, never takes an M edit."""
    w = wff
    man = w.tool.manifest()
    thin = {**man, "files": [e for e in man["files"] if not (e.get("family") == "R" and e.get("draw") == 1)]}
    if w.manifest_form == "gateb":
        assert sum(1 for e in thin["files"] if e.get("draw") == 1) == 2 and all(
            e["family"] == "M" for e in thin["files"] if e.get("draw") == 1)
    with pytest.raises(w.r78.Refused, match=r"no R edit for draw\(s\) \[1\]"):
        w.r78.block0_r_edits(thin)
    write_json(w.sealed_folder / "MANIFEST.json", thin)
    w.mp.setitem(w.r78.SEALED_SETS[w.family], "sha256", sha(w.sealed_folder / "MANIFEST.json"))
    with pytest.raises(SystemExit, match=r"no R edit for draw\(s\) \[1\]"):
        w.init(dry_run=True)
    assert not (w.root / "plan.json").exists()


# ===== D4: the fixture refuses the other family's verification.json ==================================================
@pytest.mark.parametrize("field", ["recipe_sha256", "manifest_sha256", "training_identity", "all"])
def test_d4_the_fixture_refuses_the_other_familys_verification_json(wf, field):
    w = wf
    r, r78, tool = w.rules, w.r78, w.tool
    other = r78.KIT[w.other]
    path = w.repo / r.GATE_A_FIXTURE
    doc = json.loads(path.read_text())
    assert tool.fixture()["training_identity"] == r.TRAINING_IDENTITY             # the family's own passes first
    changes = {"recipe_sha256": other["rec"][1], "manifest_sha256": other["manifest_sha256"],
               "training_identity": other["training_identity"]}
    if field == "all":
        doc.update(changes)                                                      # the other family's file, verbatim
    else:
        doc[field] = changes[field]
    write_json(path, doc)
    # pinned (plan_tool.fixture reads stage1_rules.PREREG_FIXTURE_SHA256, set at import from rules_78b.KIT), so only
    # the identity check can fail
    w.mp.setitem(r78.KIT[w.family]["fixture"], "sha256", sha(path))
    w.mp.setattr(r, "PREREG_FIXTURE_SHA256", sha(path))
    with pytest.raises(SystemExit, match="is not the family's a0-1101 side unit"):
        tool.fixture()
    with pytest.raises(SystemExit, match="is not the family's a0-1101 side unit"):
        w.init(dry_run=True)
    assert not (w.root / "plan.json").exists()
    # the other family's real fixture pin under this copy refuses before the identity check (the hash never matches)
    w.mp.setattr(r, "PREREG_FIXTURE_SHA256", other["fixture"]["sha256"])
    with pytest.raises(SystemExit, match="missing or differs from its pin"):
        tool.fixture()


# ===== D1: the committed sets by pin, through plan_tool (the real-set test) ===========================================
def real_set_into(w) -> Path:
    """Copy the committed set's MANIFEST.json and R_d1-R_d3 into the World at the same path; pin the real hash."""
    rel = Path(w.r78.SEALED_SETS[w.family]["path"]).parent
    src = ROOT / rel
    assert (src / "MANIFEST.json").is_file(), f"{rel} is not in this checkout (d422fca for the Llama set)"
    assert hashlib.sha256((src / "MANIFEST.json").read_bytes()).hexdigest() == PINS[w.family]
    shutil.rmtree(w.sealed_folder)
    (w.sealed_folder / "edits").mkdir(parents=True)
    shutil.copy2(src / "MANIFEST.json", w.sealed_folder / "MANIFEST.json")
    for d in (1, 2, 3):
        shutil.copy2(src / "edits" / f"R_d{d}.json", w.sealed_folder / "edits" / f"R_d{d}.json")
    w.mp.setitem(w.r78.SEALED_SETS[w.family], "sha256", PINS[w.family])
    return w.sealed_folder


def test_d1_the_committed_sets_plan_block0_by_pin(wf):
    w = wf
    folder = real_set_into(w)
    assert sha(folder / "MANIFEST.json") == PINS[w.family] == w.r78.SEALED_SETS[w.family]["sha256"]
    out = w.init(dry_run=True)
    assert [(e["seed"], e["sha256"]) for e in out["pods"][0]["edits"]] == [(1100 + d, REAL_R_EDITS[w.family][d]) for d in (1, 2, 3)]
    w.init()
    host = w.plan()["hosts"][f"{w.family}-0-1"]
    assert [(j["seed"], j["edit"]["sha256"], j["edit"]["engine_arm"]) for j in host["jobs"] if j["kind"] == "arm"] == [
        (1100 + d, REAL_R_EDITS[w.family][d], f"edit-{REAL_R_EDITS[w.family][d]}") for d in (1, 2, 3)]
    for j in host["jobs"]:
        if j["kind"] == "arm":
            assert j["edit"]["manifest_sha256"] == w.r78.MANIFESTS[w.family] and j["edit"]["counts"]["remove"] == 600
    if w.family == "llama31-8b":
        assert [j["seed"] for j in host["jobs"] if j["kind"] == "a0_arm"] == [1103] and host["cap_hours"] == 12.5
        assert len(host["jobs"]) == 4
    else:
        assert host["cap_hours"] == 8.5 and len(host["jobs"]) == 3
    assert w.plan()["sealed_set"]["sha256"] == PINS[w.family]
    # a changed MANIFEST byte refuses by pin
    man = json.loads((folder / "MANIFEST.json").read_text())
    man["version"] = 2
    write_json(folder / "MANIFEST.json", man)
    with pytest.raises(SystemExit, match="missing or differs from its pin"):
        w.tool.manifest()
