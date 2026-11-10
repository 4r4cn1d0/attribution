"""R1 K1: the 7-8B kit's block A and B tables, edits, steps, pod layout and train_scale input (PLAN-AB §1 items 1-4;
Part 2 §2.1-§2.4; the lead's build rulings GXB O1). Stdlib and pytest only; no pod, no network.

    PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests/test_block_tables_78b.py

The sealed edit files are named by path and SHA-256 only: test_r_draw_hashes_equal_part2_table hashes the committed R_d
files (digest only, nothing printed or parsed) and reads the Llama MANIFEST's text-free keys. Every test here takes at
most the tmp_path and monkeypatch fixtures and no parameters, so that test_rules_78b.py's test_23 can run each one too
(the rules mutation runner runs that file only).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys

import pytest

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
KIT = HERE.parent
ROOT = KIT.parents[1]
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))
import rules_78b as R                               # noqa: E402

FAMILIES = ("olmo2-7b", "llama31-8b")
# Part 2 §2.3's table, copied by hand (R: research/experiments/2026-11-06-78b-preregistration-part2.md:476-492).
P2_R_TABLE = {
    "olmo2-7b": {4: "5cf35162ec9f22e90fa9d053c4c75ee8c1287f06975dda2310095aa9ed58900e",
                 5: "73d336ccf27e12d5e6f7c2b5c06cd89b14498804a4d140ef87e10a7afcf0be7a",
                 6: "c41c3df7721356eeeea4399edbc0ffbff17b06b256d934d216929cb0766fdfb1",
                 7: "dbb4b554c1062d9845b732c65bf95d0601909ce21ff72487d426dc32d3944b1b",
                 8: "b3a9dee0a429ed1c85ae1f3ea5dc4dc3f50da3a0b59acbca4601e071104ba92c",
                 9: "55066a0407b7578f8cf724a2c350ea6cf4a3d89d4f90a06713c6d50d7f5a58dc",
                 10: "805fb6faa49b51ffde3732d1c68553249620e14eec5cfb827db2c01021321c57",
                 11: "94af783311716eae36ab5ae0e8e72e6f8ecda15c047d5d4d2f23a0dbf7130ee0",
                 12: "21e0dc208465cb042c330d1d48e4c3a185e34fde62ec12db8a3bd079bd8499e5",
                 13: "bb1e3bf4743468eef789027486b28d8e8faad7db2f977aa9cd6057412192cd43"},
    "llama31-8b": {4: "37235592ad186d9ae6174250f5bda1a9e253b9c8627f7c7cf727faa2564d42e0",
                   5: "222487acccdecc04c9b6cb0b0f8fdd4cfd8ef5551e5993ec5d10460e0c29db03",
                   6: "73b10a31b16e6054fa87a813551fb8e3a4ccf6ac5b94c4ea040abd35c2d34b6e",
                   7: "bba6568c59c4899c5f30595a22773c92f39244e615eb363cd37d3361e40b5d1d",
                   8: "097260ffb47ac112fd114e5ae3eb92d68a8d0b8117a74073255c3edb357e5ca1",
                   9: "8dd2a194ace3a498141bfb10993636d7373db0343d18539563bcdd80066acbf6",
                   10: "f20e6be770d765c75be45b92d5be4ff00c801d76cdbb9964d1a2b4adde52d016",
                   11: "664c6f1b2aafe342fad29e1df93515b2869e9b63ffe4e1c1f3fe69f626c4cd95",
                   12: "3a43db9653048854e2f2588aa3a7e94a547398d5144dca54af390d2741073e6a",
                   13: "07ccde7185a68461a759db952bc5297382f1dcabf6dfe00044e1dac907e4b5dd"},
}
P2_R_SOURCES = {"olmo2-7b": {4: ".ai/inputs/gate-b-sealed-20261008/out/edits/",
                             5: ".ai/inputs/gate-b-sealed-20261008/out/edits/",
                             **{d: ".ai/inputs/stage1-commitments-20261016/r-draws/edits/" for d in range(6, 11)},
                             **{d: ".ai/inputs/scale-78b-r-draws-olmo2-20261105/out/edits/" for d in range(11, 14)}},
                "llama31-8b": {d: ".ai/inputs/scale-78b-sealed-llama3-20261105/out/edits/" for d in range(4, 14)}}


def hx(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def fill_method_edits(monkeypatch, family: str, arms=("A1", "L1", "S3", "S4", "S4_96", "S4_192")) -> None:
    """Test-local fills of the null method-edit pins (synthetic hashes; the committed pins stay null)."""
    rows = {"A1": 600, "L1": 600, "S3": 48, "S4": 48, "S4_96": 96, "S4_192": 192}
    for arm in arms:
        monkeypatch.setitem(R.METHOD_EDITS[family], arm, {"path": f"tmp/synthetic/{family}/{arm}.json",
                                                          "sha256": hx(f"{family}-{arm}"), "rows": rows[arm]})


def stop_family(monkeypatch, family: str) -> None:
    """A test-local anchor stop: the family's stop record pinned in ANCHOR_STOP and read at the pin (K1V-6)."""
    done = hx(f"job-done-{family}")
    data = json.dumps(R.anchor_stop_record(family, 3, None, done, {"kept": 60, "needed": 64})).encode()
    monkeypatch.setattr(R, "_ANCHOR_STOPS_READ", {})
    monkeypatch.setitem(R.ANCHOR_STOP, family, {"path": f"records/{family}-anchor-stop.json",
                                                "sha256": hashlib.sha256(data).hexdigest()})
    R.anchor_stop_or_refuse(family, data, done)


def padded_for(runs, value: float = 40000.0) -> dict:
    return {(a, s): value for a, s in runs if a != "a0"}


def kit_copy(tmp_path: pathlib.Path, family: str, block: str):
    """stage1_rules.py in a KD7 working copy named for (family, block); it imports the same rules_78b module."""
    folder = tmp_path / f"family-probe-s78-{family}-{block}"
    folder.mkdir(parents=True)
    shutil.copy2(KIT / "stage1_rules.py", folder / "stage1_rules.py")
    name = f"sr78_bt_{family}_{block}".replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, folder / "stage1_rules.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    assert module.r78 is R and module.FAMILY == family and module.KIT_BLOCK == block
    return module


# ------------------------------------------------------------------------------------------------ item 1: tables
def test_block_a_21_runs_each_family(tmp_path):
    """Part 2 §2.2: block A is the same in every plan: A1, L1, H1, S1, S3, S4 at 1102-1104 (18), R_4 at 1104, R_5 at
    1105, a0 at 1104: 21 per family, seed-major, arm-minor."""
    for family in FAMILIES:
        runs = R.block_runs_78b(family, None, "A")
        assert len(runs) == 21 and len(set(runs)) == 21
        assert sorted(runs) == sorted([(a, s) for s in (1102, 1103, 1104) for a in ("A1", "L1", "H1", "S1", "S3", "S4")]
                                      + [("R", 1104), ("R", 1105), ("a0", 1104)])
        assert runs == sorted(runs, key=lambda r: (r[1], R.AB_ARM_ORDER.index(r[0])))
        for code in R.PLAN_CODES:
            assert R.block_runs_78b(family, code, "A") == runs              # every plan
        sr = kit_copy(tmp_path / family, family, "A")
        assert sr.block_runs(None, "A") == runs and "A" in sr.BLOCKS and sr.HOST_PREFIX["A"] == f"{family}-a"
        assert sr.BLOCK_KINDS["A"] == ("arm", "a0_arm") and sr.FUNDING_BLOCK["A"] == "A"
        with pytest.raises(ValueError, match="reuses no unit"):
            sr.block_runs(None, "A", (("R", 1104),))
    with pytest.raises(R.Refused, match="block B's"):
        R.block_runs_78b("olmo2-7b", None, "A", dose_seeds=3)
    with pytest.raises(R.Refused, match="no 7-8B block table"):
        R.block_runs_78b("olmo2-7b", "A", "C")
    with pytest.raises(R.Refused, match="unknown plan"):
        R.block_runs_78b("olmo2-7b", "B10", "A")


def test_block_b_counts_per_plan(tmp_path):
    """Part 2 §2.2: block B plan A 23 (the six at 1105-1107, R_6-R_7, a0 1105-1107); B9 32 (A1, H1, S1, S4 at
    1105-1110, R_6-R_10, a0); H (b) 47 (the four at 1105-1113, R_6-R_13, a0); the secondary dose rows 6 (1102-1104) or
    12 (1102-1107). Block B needs its plan (None refuses)."""
    want = {"A": 23, "B9": 32, "H": 47}
    for family in FAMILIES:
        for code, n in want.items():
            runs = R.block_runs_78b(family, code, "B")
            assert len(runs) == n == len(set(runs)), (family, code)
            last = {"A": 1107, "B9": 1110, "H": 1113}[code]
            assert sorted(s for a, s in runs if a == "R") == list(range(1106, last + 1))
            assert sorted(s for a, s in runs if a == "a0") == [1105, 1106, 1107]
            arms = ("A1", "L1", "H1", "S1", "S3", "S4") if code == "A" else ("A1", "H1", "S1", "S4")
            assert {a for a, _ in runs} == set(arms) | {"R", "a0"}
            for arm in arms:
                assert sorted(s for a, s in runs if a == arm) == list(range(1105, last + 1))
            for k, extra in ((3, 6), (6, 12)):
                with_doses = R.block_runs_78b(family, code, "B", dose_seeds=k, kept=192)
                assert len(with_doses) == n + extra
                doses = sorted(r for r in with_doses if r[0] in R.DOSE_ARMS)
                assert doses == sorted((a, s) for a in R.DOSE_ARMS for s in R.DOSE_SEEDS[k])
        for bad in (None, "B10", "C"):
            with pytest.raises(R.Refused, match="needs its plan"):
                R.block_runs_78b(family, bad, "B")
        for bad in (1, 2, 4, 12):
            with pytest.raises(R.Refused, match="3 or 6 seeds"):
                R.block_runs_78b(family, "A", "B", dose_seeds=bad, kept=192)
        with pytest.raises(R.Refused, match="whole number"):
            R.block_runs_78b(family, "A", "B", dose_seeds=3)                 # the dose rows need the kept count
        top = R.block_runs_78b(family, "A", "B", dose_seeds=3, kept=150)
        assert sorted(a for a, _ in top if a in ("S4_96", "s4_top", "S4_192")) == ["S4_96"] * 3 + ["s4_top"] * 3
        sr = kit_copy(tmp_path / family, family, "B")
        assert sr.block_runs("B9", "B") == R.block_runs_78b(family, "B9", "B")
        assert sr.BLOCK_KINDS["B"] == ("arm", "a0_arm", "ref_eval", "safe_lora", "ref_train", "ref_train_bqi")
        assert sr.BLOCKS == ("0", "sc", "A", "B") and sr.HOST_PREFIX["B"] == f"{family}-b" and sr.FUNDING_BLOCK["B"] == "B"
        with pytest.raises(ValueError, match="needs its plan"):
            sr.block_runs(None, "B")


def test_r_draw_seed_is_1100_plus_d():
    """Draw d runs at seed 1100 + d (Part 2 §2.1): every R run of every table binds R_d with d = seed - 1100, its
    pinned path and SHA-256, 600 removed rows, 4,200 training rows, 33 steps; an R seed outside R_d4-R_d13 refuses."""
    for family in FAMILIES:
        for block, code in (("A", None), ("B", "A"), ("B", "B9"), ("B", "H")):
            for arm, seed in R.block_runs_78b(family, code, block):
                if arm != "R":
                    continue
                edit = R.run_edit(family, "R", seed)
                d = seed - 1100
                assert edit["draw"] == d and edit["sha256"] == R.R_DRAW_SOURCES[family][d]["sha256"]
                assert edit["path"] == R.R_DRAW_SOURCES[family][d]["path"] and edit["path"].endswith(f"R_d{d}.json")
                assert (edit["rows"], edit["training_rows"], edit["steps"]) == (600, 4200, 33)
                assert edit["engine_arm"] == f"edit-{edit['sha256']}"
        for seed in (1101, 1102, 1103, 1114, 1100, "1104", None):
            with pytest.raises(R.Refused, match="no R_d edit"):
                R.run_edit(family, "R", seed)
    assert R.run_edit("olmo2-7b", "a0", 1104) is None


def test_r_draw_hashes_equal_part2_table():
    """R_DRAW_SOURCES equals Part 2 §2.3's table (hashes and the three OLMo sources), each committed file hashes to its
    pin (digest only), and each Llama pin equals its sealed MANIFEST entry (draw, seed 1100 + d, rows 600)."""
    for family in FAMILIES:
        assert {d: v["sha256"] for d, v in R.R_DRAW_SOURCES[family].items()} == P2_R_TABLE[family]
        for d, v in R.R_DRAW_SOURCES[family].items():
            assert v["path"] == f"{P2_R_SOURCES[family][d]}R_d{d}.json"
            path = ROOT / v["path"]
            if path.is_file():                                  # committed under .ai/inputs/ (digest only)
                assert hashlib.sha256(path.read_bytes()).hexdigest() == v["sha256"], (family, d)
    assert not set(P2_R_TABLE["olmo2-7b"].values()) & set(P2_R_TABLE["llama31-8b"].values())
    manifest = ROOT / R.SEALED_SETS["llama31-8b"]["path"]
    if manifest.is_file():
        assert hashlib.sha256(manifest.read_bytes()).hexdigest() == R.SEALED_SETS["llama31-8b"]["sha256"]
        entries = {e["draw"]: e for e in json.loads(manifest.read_text())["files"] if e.get("family") == "R"}
        for d, v in R.R_DRAW_SOURCES["llama31-8b"].items():
            assert entries[d]["sha256"] == v["sha256"] and entries[d]["seed"] == 1100 + d
            assert entries[d]["rows"] == R.R_DRAW_ROWS == 600
            assert "out/" + entries[d]["path"] == v["path"].split("scale-78b-sealed-llama3-20261105/")[1]


def test_null_method_edit_refuses(tmp_path, monkeypatch):
    """Part 2 §2.3: A1, L1, S3, S4, S4_96, S4_192 and s4_top are null until the scorer block writes them and a recorded
    lead step fills them; a null pin refuses run_edit and block A's job table with its event (A13's pattern). H1 and S1
    are filled (Part 2 §1.7, §1.9). Once filled (test-local), the table prices."""
    for family in FAMILIES:
        for arm in ("A1", "L1", "S3", "S4", "S4_96", "S4_192", "s4_top"):
            assert R.METHOD_EDITS[family][arm] is None
            with pytest.raises(R.Refused, match=r"is null \(Part 2 §2.3"):
                R.run_edit(family, arm, 1102)
            assert R.METHOD_EDIT_EVENTS[arm] in str(pytest.raises(R.Refused, R.run_edit, family, arm, 1102).value)
        for arm, rows, steps in (("H1", 600, 33), ("S1", 48, 38)):
            edit = R.run_edit(family, arm, 1102)
            assert (edit["rows"], edit["steps"]) == (rows, steps) and edit["sha256"] == R.METHOD_EDITS[family][arm]["sha256"]
        sr = kit_copy(tmp_path / family, family, "A")
        with pytest.raises(ValueError, match="A1's edit .* is null"):
            sr.block_jobs(None, "A", padded_for(R.block_runs_78b(family, None, "A")))
    assert R.METHOD_EDITS["olmo2-7b"]["H1"]["sha256"].startswith("f5b1762f")
    assert R.METHOD_EDITS["llama31-8b"]["H1"]["sha256"].startswith("9a01637e")
    assert R.METHOD_EDITS["olmo2-7b"]["S1"]["sha256"].startswith("904a0cf1")
    assert R.METHOD_EDITS["llama31-8b"]["S1"]["sha256"].startswith("69426993")
    for bad in ({"path": "x.json", "sha256": hx("a")}, {"path": "/abs.json", "sha256": hx("a"), "rows": 600},
                {"path": "a/../b.json", "sha256": hx("a"), "rows": 600}, {"path": "a.json", "sha256": "A" * 64, "rows": 600},
                {"path": "a.json", "sha256": hx("a"), "rows": 599}):
        monkeypatch.setitem(R.METHOD_EDITS["olmo2-7b"], "A1", bad)
        with pytest.raises(R.Refused, match="is not an edit pin"):
            R.run_edit("olmo2-7b", "A1", 1102)
    fill_method_edits(monkeypatch, "olmo2-7b")
    sr = kit_copy(tmp_path / "filled", "olmo2-7b", "A")
    jobs = sr.block_jobs(None, "A", padded_for(R.block_runs_78b("olmo2-7b", None, "A")))
    assert len(jobs) == 21 and all(j["oext"] is True and j["block"] == "A" for j in jobs)
    a1 = next(j for j in jobs if j["arm"] == "A1")
    assert a1["edit"] == {"path": "tmp/synthetic/olmo2-7b/A1.json", "sha256": hx("olmo2-7b-A1"),
                          "engine_arm": f"edit-{hx('olmo2-7b-A1')}"} and a1["steps"] == 33 and a1["recipe"] == "B"
    assert a1["padded_tokens_per_step"] == 40000.0 and a1["upper_s"] == R.upper_m_s("olmo2-7b", 33, "arm", 40000.0, True)
    assert a1["train_scale"] == R.train_scale("olmo2-7b", 40000.0) > 1.0
    assert [j["steps"] for j in jobs if j["arm"] in ("S3", "S4", "S1")] == [38] * 9
    assert next(j for j in jobs if j["arm"] == "a0")["edit"] is None


def test_other_family_edit_refuses(tmp_path, monkeypatch):
    """Each family's table reads its own pins only: OLMo's R_d edits never carry a Llama hash; a Llama method pin filled
    while OLMo's is null leaves OLMo's table refusing; a kit copy of one family never plans the other's table."""
    for d in range(4, 14):
        assert R.run_edit("olmo2-7b", "R", 1100 + d)["sha256"] not in P2_R_TABLE["llama31-8b"].values()
        assert R.run_edit("llama31-8b", "R", 1100 + d)["sha256"] not in P2_R_TABLE["olmo2-7b"].values()
    fill_method_edits(monkeypatch, "llama31-8b")
    with pytest.raises(R.Refused, match="A1's edit for olmo2-7b is null"):
        R.run_edit("olmo2-7b", "A1", 1102)
    assert R.run_edit("llama31-8b", "A1", 1102)["sha256"] == hx("llama31-8b-A1")
    sr = kit_copy(tmp_path, "olmo2-7b", "A")
    with pytest.raises(ValueError, match="olmo2-7b"):
        sr.block_jobs(None, "A", padded_for(R.block_runs_78b("olmo2-7b", None, "A")))
    with pytest.raises(ValueError, match="never plans"):
        sr.family_or_refuse("llama31-8b")
    with pytest.raises(R.Refused, match="not an arm"):
        R.run_edit("olmo2-7b", "S2", 1102)


def test_stopped_family_drops_a1_l1_s3(monkeypatch):
    """DESO2 item 36 (1); Part 2 §2.2: on a family whose anchor job stopped, A1, L1 and S3 are not run: block A 18 -> 9
    method runs (12 in all), block B plan A 14, B9 26 (A1's 6 dropped), H (b) 38; the dose rows stay; the other family
    keeps its full tables."""
    stop_family(monkeypatch, "olmo2-7b")
    a = R.block_runs_78b("olmo2-7b", None, "A")
    assert len(a) == 12 and not {"A1", "L1", "S3"} & {x for x, _ in a}
    assert sorted(r for r in a if r[0] in R.METHOD_ARMS) == sorted((x, s) for x in ("H1", "S1", "S4")
                                                                    for s in (1102, 1103, 1104))
    assert [len(R.block_runs_78b("olmo2-7b", c, "B")) for c in ("A", "B9", "H")] == [14, 26, 38]
    assert len(R.block_runs_78b("olmo2-7b", "A", "B", dose_seeds=6, kept=192)) == 14 + 12
    assert len(R.block_runs_78b("llama31-8b", None, "A")) == 21
    for pods in (R.deal_ab(a), R.deal_ab(R.block_runs_78b("olmo2-7b", "H", "B"))):
        assert all(len(p) <= 4 for p in pods)


# ------------------------------------------------------------------------------------------------ item 2: the deal
def test_deal_block_a_444333():
    """Part 2 §2.4: 21 runs -> pods of 4, 4, 4, 3, 3, 3; arm-major, seed-minor, run i to pod i mod 6, so each arm's
    three seeds sit on three consecutive pods."""
    for family in FAMILIES:
        pods = R.deal_ab(R.block_runs_78b(family, None, "A"))
        assert [len(p) for p in pods] == [4, 4, 4, 3, 3, 3] == R.pod_sizes(21)
        assert pods[0] == [("A1", 1102), ("H1", 1102), ("S3", 1102), ("a0", 1104)]
        assert pods[1] == [("A1", 1103), ("H1", 1103), ("S3", 1103), ("R", 1104)]
        assert pods[2] == [("A1", 1104), ("H1", 1104), ("S3", 1104), ("R", 1105)]
        assert pods[3] == [("L1", 1102), ("S1", 1102), ("S4", 1102)]
        assert R.deal_ab(list(reversed(R.block_runs_78b(family, None, "A")))) == pods     # order-free
        assert [len(p) for p in R.deal_ab(R.block_runs_78b(family, "A", "B"))] == [4, 4, 4, 4, 4, 3]


def test_deal_no_arm_twice_on_a_pod():
    """No pod holds one arm twice, in every plan, with and without the dose rows; a run list that would put an arm
    twice on a pod, or a run listed twice, refuses."""
    for family in FAMILIES:
        for block, code in (("A", None), ("B", "A"), ("B", "B9"), ("B", "H")):
            for k in ((0,) if block == "A" else (0, 3, 6)):
                pods = R.deal_ab(R.block_runs_78b(family, code, block, dose_seeds=k, kept=192 if k else None))
                for pod in pods:
                    assert len({a for a, _ in pod}) == len(pod)
                assert sum(len(p) for p in pods) == len(R.block_runs_78b(family, code, block, dose_seeds=k,
                                                                         kept=192 if k else None))
    with pytest.raises(R.Refused, match="one arm twice"):
        R.deal_ab([("A1", s) for s in range(1102, 1107)])
    with pytest.raises(R.Refused, match="listed twice"):
        R.deal_ab([("A1", 1102), ("A1", 1102)])


def test_mixed_33_38_39_cap_uses_own_steps(monkeypatch):
    """Part 2 §2.4: 33-, 38- and 39-step arms share a pod; the cap uses each arm's own steps (and each its O-ext term):
    a pod of R (33), S4 (38) and S4_96 (39) has the cap of arm_pod([33, 38, 39], oext) and not of three 38s."""
    family = "olmo2-7b"
    fill_method_edits(monkeypatch, family)
    jobs = [R.block_job_78b(family, "R", 1106, 40000.0), R.block_job_78b(family, "S4", 1105, 40000.0),
            R.block_job_78b(family, "S4_96", 1102, 40000.0)]
    assert [j["steps"] for j in jobs] == [33, 38, 39]
    same = R.arm_pod(family, [33, 38, 39], oext=True)
    for j, s in zip(jobs, same):
        s.update(padded_tokens_per_step=j["padded_tokens_per_step"])
        s["upper_s"] = R.upper_m_s(family, s["steps"], "arm", j["padded_tokens_per_step"], True)
    assert R.cap_hours(jobs) == R.cap_hours(same)
    assert R.requirements(jobs) == R.requirements(same)
    assert R.requirements(jobs)[2] > R.requirements(jobs)[1] > R.requirements(jobs)[0]


def test_at_most_4_counted_per_pod():
    """KD2: at most 4 counted arms per pod in every dealt pod; cap_hours refuses a fifth."""
    for family in FAMILIES:
        for block, code in (("A", None), ("B", "A"), ("B", "B9"), ("B", "H")):
            for pod in R.deal_ab(R.block_runs_78b(family, code, block, dose_seeds=0 if block == "A" else 6,
                                                  kept=None if block == "A" else 192)):
                assert len(pod) <= R.MAX_ARMS_PER_POD_78B == 4
        with pytest.raises(R.Refused, match="at most 4"):
            R.cap_hours(R.arm_pod(family, [33] * 5, oext=True))


# ------------------------------------------------------------------------------------------------ item 3: steps
def test_dose_arms_39_steps(tmp_path, monkeypatch):
    """P1 §10; Part 2 §2.1: S4_96 (4,896 rows) and S4_192 (4,992) train 39 steps: STEPS["dose"], ARM_STEPS, the kit
    copy's DOSE_STEPS and the derived steps of a filled dose pin agree."""
    assert R.STEPS == {"remove": 33, "add": 38, "a0": 38, "dose": 39} and R.steps_of("dose") == 39
    assert R.ARM_STEPS["S4_96"] == R.ARM_STEPS["S4_192"] == 39
    fill_method_edits(monkeypatch, "llama31-8b")
    assert R.run_edit("llama31-8b", "S4_96", 1102)["steps"] == 39 == R.run_edit("llama31-8b", "S4_192", 1103)["steps"]
    assert R.run_edit("llama31-8b", "S4_96", 1102)["training_rows"] == 4896
    assert R.run_edit("llama31-8b", "S4_192", 1102)["training_rows"] == 4992
    sr = kit_copy(tmp_path, "llama31-8b", "B")
    assert sr.DOSE_STEPS["dose"] == 39 and sr.ARM_DOSE["S4_96"] == sr.ARM_DOSE["S4_192"] == "dose"
    assert sr.stream_steps("S4_96") == 39 and sr.stream_steps("S4") == 38 and sr.stream_steps("R") == 33


def test_steps_match_edit_rows(monkeypatch):
    """GXB O1: steps = ceil(rows / 128) of the training rows the edit leaves; a named arm whose derived steps differ
    from RK's STEPS refuses, and so does an edit whose row count breaks the arm's contract."""
    for rows, steps in ((4200, 33), (4800, 38), (4848, 38), (4896, 39), (4992, 39), (128, 1), (129, 2)):
        assert R.steps_for_rows(rows) == steps
    for arm, rows in (("R", 4200), ("A1", 4200), ("L1", 4200), ("H1", 4200), ("S1", 4848), ("S3", 4848),
                      ("S4", 4848), ("S4_96", 4896), ("S4_192", 4992), ("a0", 4800)):
        assert R.arm_steps(arm, rows) == R.ARM_STEPS[arm]
    for arm, rows in (("S4", 4896), ("S4_96", 4848), ("R", 4800), ("a0", 4200), ("S4_192", 4864)):
        with pytest.raises(R.Refused, match="GXB O1"):
            R.arm_steps(arm, rows)
    for bad in (0, -1, 1.5, True, None, "4200"):
        with pytest.raises(R.Refused):
            R.steps_for_rows(bad)
    monkeypatch.setitem(R.METHOD_EDITS["olmo2-7b"], "S4", {"path": "tmp/s4.json", "sha256": hx("s4"), "rows": 96})
    with pytest.raises(R.Refused, match="adds 48 rows by its contract"):
        R.run_edit("olmo2-7b", "S4", 1102)
    with pytest.raises(R.Refused, match="a0 has no edit"):
        R.arm_training_rows("a0", 48)


def test_s4_top_steps_rule(monkeypatch):
    """GXB O1 and K-5: s4_top with n kept rows takes ceil((4,800 + n) / 128) steps: 38 for n <= 64, 39 for n >= 65;
    s4_top exists only for 49-95 and 97-191 kept rows, so n = 48 (it would equal S4), 96 (S4_96), 192 and more
    (S4_192) and fewer than 48 refuse."""
    for n in list(range(49, 96)) + list(range(97, 192)):
        rows = R.arm_training_rows("s4_top", n)
        assert rows == 4800 + n and R.arm_steps("s4_top", rows) == (38 if n <= 64 else 39)
    for n in (47, 48, 96, 192, 250):
        with pytest.raises(R.Refused, match="49-95 and 97-191"):
            R.arm_training_rows("s4_top", n)
    with pytest.raises(R.Refused, match="positive integer"):
        R.arm_training_rows("s4_top", 0)
    monkeypatch.setitem(R.METHOD_EDITS["olmo2-7b"], "s4_top", {"path": "tmp/top.json", "sha256": hx("top"), "rows": 64})
    assert R.run_edit("olmo2-7b", "s4_top", 1102)["steps"] == 38
    monkeypatch.setitem(R.METHOD_EDITS["olmo2-7b"], "s4_top", {"path": "tmp/top.json", "sha256": hx("top"), "rows": 65})
    assert R.run_edit("olmo2-7b", "s4_top", 1102)["steps"] == 39
    for rows in (48, 96):
        monkeypatch.setitem(R.METHOD_EDITS["olmo2-7b"], "s4_top", {"path": "tmp/top.json", "sha256": hx("top"),
                                                                   "rows": rows})
        with pytest.raises(R.Refused, match="not an edit pin"):
            R.run_edit("olmo2-7b", "s4_top", 1102)


def test_k5_the_dose_arms_for_each_kept_count(monkeypatch):
    """GXB K-5 (Part 2 §5; P1 §10; DESO item 34): n >= 192 kept rows: S4_96 and S4_192; 97-191: S4_96 and s4_top (n);
    exactly 96: S4_96 only; 49-95: s4_top (n) only; exactly 48: no dose arm; fewer than 48: the build stop. Block B's
    dose rows follow it (3 or 6 seeds); a filled s4_top pin must hold exactly n rows."""
    cases = {192: ("S4_96", "S4_192"), 200: ("S4_96", "S4_192"), 191: ("S4_96", "s4_top"), 97: ("S4_96", "s4_top"),
             150: ("S4_96", "s4_top"), 96: ("S4_96",), 95: ("s4_top",), 49: ("s4_top",), 70: ("s4_top",), 48: ()}
    for n, arms in cases.items():
        assert R.dose_arms_for(n) == arms, n
        runs = R.block_runs_78b("olmo2-7b", "A", "B", dose_seeds=3, kept=n)
        assert sorted(r for r in runs if r[0] in ("S4_96", "S4_192", "s4_top")) == sorted(
            (a, s) for a in arms for s in (1102, 1103, 1104)), n
        assert len(runs) == 23 + 3 * len(arms)
    for n in (47, 0, -1):
        with pytest.raises(R.Refused, match="build stop"):
            R.dose_arms_for(n)
        with pytest.raises(R.Refused, match="build stop"):
            R.block_runs_78b("olmo2-7b", "A", "B", dose_seeds=3, kept=n)
    for bad in (None, 96.0, True, "96"):
        with pytest.raises(R.Refused, match="whole number"):
            R.dose_arms_for(bad)
    assert len(R.block_runs_78b("olmo2-7b", "A", "B", dose_seeds=6, kept=48)) == 23        # 48: no dose arm
    monkeypatch.setitem(R.METHOD_EDITS["olmo2-7b"], "s4_top", {"path": "tmp/top.json", "sha256": hx("top"), "rows": 120})
    with pytest.raises(R.Refused, match="holds 120 rows, not the 150 kept"):
        R.block_runs_78b("olmo2-7b", "A", "B", dose_seeds=3, kept=150)
    assert len(R.block_runs_78b("olmo2-7b", "A", "B", dose_seeds=3, kept=120)) == 29


# ------------------------------------------------------------------------------------------------ item 4: train_scale
def test_train_scale_at_least_1():
    """KCR:104: train_scale = max(1, the arm's padded tokens per step / the a0's): never below 1 (a removal arm with
    fewer tokens per step keeps the a0's bound)."""
    for family in FAMILIES:
        a0 = R.FAMILIES[family]["A0_PADDED_TOKENS_PER_STEP"]
        for value in (1.0, a0 / 2, a0):
            assert R.train_scale(family, value) == 1.0
        assert R.block_job_78b(family, "R", 1104, a0 / 3)["train_scale"] == 1.0
        assert R.block_job_78b(family, "a0", 1104)["train_scale"] == 1.0


def test_train_scale_from_edit_counts():
    """Part 2 §2.1: an arm whose padded tokens per step exceed the a0's (H1 removes the shortest rows) takes the
    ratio, and its upper and its cap's requirement rise by its training term times that ratio."""
    for family in FAMILIES:
        a0 = R.FAMILIES[family]["A0_PADDED_TOKENS_PER_STEP"]
        base = R.block_job_78b(family, "H1", 1102, a0)
        big = R.block_job_78b(family, "H1", 1102, a0 * 1.2)
        assert big["train_scale"] == pytest.approx(1.2)
        extra = 33 * R.FAMILIES[family]["TRAIN_STEP_MAX_S"] * 0.2
        assert big["upper_s"] - base["upper_s"] == pytest.approx(extra)
        assert R.requirements([big])[0] - R.requirements([base])[0] == pytest.approx(extra)


def test_missing_counts_refuse():
    """Part 2 §2.1: an edit arm of blocks A and B needs its padded tokens per step (from its edit's token counts);
    a missing, non-finite or non-positive count refuses; a0 takes none."""
    for family in FAMILIES:
        with pytest.raises(R.Refused, match="padded tokens per step .* are missing"):
            R.block_job_78b(family, "R", 1104, None)
        for bad in (float("nan"), float("inf"), 0.0, -5.0, True, "40000"):
            with pytest.raises(R.Refused):
                R.block_job_78b(family, "R", 1104, bad)
        with pytest.raises(R.Refused, match="a0's train_scale is 1"):
            R.block_job_78b(family, "a0", 1104, 40000.0)


# ------------------------------------------------------------------------------------------------ the pods
def test_block_pods_price_each_pod_with_its_own_steps_and_oext(tmp_path, monkeypatch):
    """SR78 block_pods: block A's six pods (4, 4, 4, 3, 3, 3), each cap = rules_78b.cap_hours of its own jobs (their
    own steps, train_scale and O-ext terms), above the same pod without the term; guard and spend from the cap."""
    fill_method_edits(monkeypatch, "olmo2-7b")
    sr = kit_copy(tmp_path, "olmo2-7b", "A")
    pods = sr.block_pods(None, "A", padded_for(R.block_runs_78b("olmo2-7b", None, "A")))
    assert [p["counted"] for p in pods] == [4, 4, 4, 3, 3, 3]
    for p in pods:
        assert p["cap_hours"] == R.cap_hours(p["jobs"])
        plain = R.arm_pod("olmo2-7b", [j["steps"] for j in p["jobs"]], [j["kind"] for j in p["jobs"]])
        assert p["cap_hours"] > R.cap_hours(plain)
        assert p["guard_usd"] == R.cents(R.guard_usd(p["cap_hours"]))
    assert max(p["cap_hours"] for p in pods) == 17.25        # Part 2 §4.3's 4-arm OLMo cap with the step x 1.5


def test_plan_code_only_from_the_plan_b_record(tmp_path, monkeypatch):
    """GXB O14 (corrected): block B's plan comes only from block B's plan record read at PLAN_B_78B's pin (after block
    A and blinded_sigma.py), never from the gate's provisional plan; the kit copy's block_init refuses before each
    fill, and bytes that are not the pinned record refuse."""
    sr = kit_copy(tmp_path, "olmo2-7b", "B")
    gate = {"kind": R.GATE_RECORD_KIND, "version": 1, "option": "B", "families": ["olmo2-7b", "llama31-8b"],
            "provisional_plan": "A", "sigma_F_plan": None, "noise_reading_sha256": hx("noise"), "balance_usd": 250.0,
            "utc": "2026-11-20T10:00:00Z", "recorded_by": "GI XI"}
    plan_b = {"kind": R.PLAN_B_RECORD_KIND, "version": 1, "plan": "B9", "sr2_adopted": True, "sr2_reason": None,
              "plan_basis": "sigma_A", "sigma_A_pp": 5.0,
              "blinded_sigma_output_sha256": hx("bs-out"), "blinded_sigma_inputs_sha256": hx("bs-in"),
              "utc": "2026-12-01T10:00:00Z", "recorded_by": "GI XI"}
    g, b = json.dumps(gate).encode(), json.dumps(plan_b).encode()
    with pytest.raises(ValueError, match="GATE_78B is null"):
        sr.block_init("B", g, b)
    monkeypatch.setattr(R, "GATE_78B", {"path": "records/gate.json", "sha256": hashlib.sha256(g).hexdigest()})
    assert sr.block_init("A", g)["plan"] is None
    with pytest.raises(ValueError, match="PLAN_B_78B is null"):
        sr.block_init("B", g, b)
    monkeypatch.setattr(R, "PLAN_B_78B", {"path": "records/plan-b.json", "sha256": hashlib.sha256(b).hexdigest()})
    got = sr.block_init("B", g, b)
    assert got["plan"] == "B9" and got["sr2_adopted"] is True                   # not the gate's provisional "A"
    assert sr.block_runs(got["plan"], "B") == R.block_runs_78b("olmo2-7b", "B9", "B")
    with pytest.raises(ValueError, match="do not hash to PLAN_B_78B"):
        sr.block_init("B", g, json.dumps({**plan_b, "plan": "A"}).encode())
