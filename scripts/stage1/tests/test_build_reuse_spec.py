"""LN-12: the reused units' regeneration and O-only job spec, on a synthetic data root (fake unit records, a fake sealed
MANIFEST, fake O-ext and W1-18 records). No real unit record is read."""

from __future__ import annotations

import copy
import json

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1 import build_reuse_spec as brs
from scripts.stage1 import s1common as s1


def hexs(tag: str) -> str:
    return sha256_bytes(tag.encode())


def write(path, doc) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json(doc)
    path.write_bytes(data)
    return sha256_bytes(data)


def make_root(root, with_r4: bool = False):
    """A data root with 3 a0 units, R_1-R_3 (and R_4), a sealed MANIFEST, and the settings pointing at them."""
    files = []
    for d in range(1, 6):
        data = f"synthetic R_d{d} edit".encode()
        files.append({"path": f"edits/R_d{d}.json", "family": "R", "draw": d, "sha256": sha256_bytes(data),
                      "arm": f"edit-{sha256_bytes(data)}"})
    manifest_sha = write(root / "sealed/MANIFEST.json", {"kind": "gate-b sealed files manifest", "files": files})
    arms = {f["draw"]: f["arm"] for f in files}
    units = []

    def unit(name, kind, seed, d=None):
        folder = root / "units" / name
        arm = "a0" if kind == "a0" else arms[d]
        job_sha = write(folder / "job.json", {"arm": arm, "seed": seed, "edit": None if kind == "a0" else f"sealed/edits/R_d{d}.json",
                                              "target_checkpoint": "e1", "kind": "run-one"})
        identity = {"code_sha256": hexs("code-a0" if kind == "a0" else "code-x"), "recipe_sha256": hexs("rec" if kind == "a0" else "s"),
                    "manifest_sha256": hexs("P"), "data_config_sha256": hexs("dc"), "training_identity": hexs("ti")}
        complete_sha = write(folder / "COMPLETE.json", {"complete": True, "job_sha256": job_sha, "identity": identity,
                                                       "checkpoints": {"q": {"adapter_fingerprint": hexs(name + "q")},
                                                                       "e1": {"adapter_fingerprint": hexs(name + "e1")}}})
        return {"name": name, "kind": kind, "seed": seed, **({"d": d} if d else {}), "path": f"units/{name}",
                "complete_sha256": complete_sha, "job_sha256": job_sha}
    units += [unit(f"a0_{s}", "a0", s) for s in (1101, 1102, 1103)]
    units += [unit(f"R_{1100 + d}", "R", 1100 + d, d) for d in (1, 2, 3)]
    r4 = unit("R_1104", "R", 1104, 4) if with_r4 else None
    s = copy.deepcopy(json.loads(brs.SETTINGS_PATH.read_bytes()))
    conditional = [u for u in s["units"] if u.get("conditional")]
    s["units"] = units + conditional
    s["sealed_manifest"] = {**s["sealed_manifest"], "path": "sealed/MANIFEST.json", "sha256": manifest_sha}
    oext = root / "oext_record.json"
    oext_sha = write(oext, {"kind": "stage1 o-ext record", "bank_size": 400, "shortfall": None,
                            "bank": {"full_file": {"sha256": hexs("bank"), "bytes": 1}}})
    return s, (oext, oext_sha), r4


def w1_18(root, passed: bool, units: int = 11):
    path = root / "overrefusal_checks.json"
    return path, write(path, {"kind": "stage1 over-refusal checks",
                              "truncation_check": {"units": units, "units_failing": 0 if passed else 1, "pass": passed}})


def spec(root, settings, oext, cap=None, extension=None, oext_eval=None) -> dict:
    files = brs.build(data_root=root, oext_record=oext, cap_record=cap, oext_eval=oext_eval, extension=extension or {},
                      settings=settings, settings_sha256="e" * 64)
    return json.loads(files[brs.OUTPUT])


def test_the_jobs_their_order_and_the_acceptance_values(tmp_path):
    s, oext, _ = make_root(tmp_path)
    doc = spec(tmp_path, s, oext, cap=w1_18(tmp_path, True))
    kinds = [j["kind"] for j in doc["jobs"]]
    assert kinds == ["regenerate"] * 6 + ["o_only"] * 7 + ["report"]
    names = ["a0_1101", "a0_1102", "a0_1103", "R_1101", "R_1102", "R_1103"]
    assert [j["unit"] for j in doc["jobs"][:6]] == names and [j["unit"] for j in doc["jobs"][6:12]] == names
    assert all(j["after"] == f"regenerate-{j['unit']}" for j in doc["jobs"][6:12])
    for job, name in zip(doc["jobs"][:6], names):
        assert job["accept"]["e1_adapter_fingerprint"] == hexs(name + "e1") and job["report"]["q_adapter_fingerprint"] == hexs(name + "q")
        assert job["accept"]["training_identity"] == hexs("ti") and job["train_only"] is True
        assert job["engine_code_sha256"] == s["engine"]["code_sha256"] and job["recipe_sha256"] == s["engine"]["recipe_sha256"]
    assert doc["jobs"][0]["report"]["source_code_sha256"] == hexs("code-a0")      # reported, not required
    assert doc["jobs"][3]["arm"].startswith("edit-") and doc["jobs"][0]["arm"] == "a0"
    assert doc["jobs"][12]["unit"] == "theta0" and doc["jobs"][12]["adapter"] is None
    assert doc["counts"] == {"regenerate": 6, "o_only": 7, "report": 1}
    assert {j["kind"] for j in doc["jobs"]} <= {"regenerate", "o_only", "report"}     # never a pull


@pytest.mark.parametrize("passed,units,branch", [(True, 11, "128"), (False, 11, "full")])
def test_the_cap_branch_follows_w1_18(tmp_path, passed, units, branch):
    s, oext, _ = make_root(tmp_path)
    doc = spec(tmp_path, s, oext, cap=w1_18(tmp_path, passed, units))
    assert doc["cap"]["branch"] == branch and all(j["branch"] == branch for j in doc["jobs"] if j["kind"] == "o_only")
    assert doc["jobs"][6]["route"] == s["routes"][branch]
    assert ("report-theta0-transfer" in [j["id"] for j in doc["jobs"]]) == (branch == "128")


def test_no_record_means_branch_full_and_a_bad_record_refuses(tmp_path):
    s, oext, _ = make_root(tmp_path)
    doc = spec(tmp_path, s, oext)
    assert doc["cap"] == {"branch": "full", "source": s["cap"]["no_record"], "record_sha256": None}
    with pytest.raises(s1.Refusal, match="over 11 units"):
        spec(tmp_path, s, oext, cap=w1_18(tmp_path, True, units=10))
    path = tmp_path / "other.json"
    sha = write(path, {"kind": "something else", "truncation_check": {"units": 11, "pass": True}})
    with pytest.raises(s1.Refusal, match="not W1-18's record"):
        spec(tmp_path, s, oext, cap=(path, sha))


def test_the_o_bank_follows_the_oext_record(tmp_path):
    s, oext, _ = make_root(tmp_path)
    doc = spec(tmp_path, s, oext)
    assert doc["o_bank"]["prompts"] == 500 and doc["o_bank"]["phtest"]["record_sha256"] == oext[1]
    assert "equal weight per prompt" in doc["o_bank"]["weights"]
    path = tmp_path / "short.json"
    sha = write(path, {"kind": "stage1 o-ext record", "bank_size": 390, "shortfall": {"eligible": 390, "planned": 400},
                       "bank": {"full_file": {"sha256": hexs("b"), "bytes": 1}}})
    short = spec(tmp_path, s, (path, sha))
    assert short["o_bank"]["prompts"] == 490 and short["o_bank"]["phtest"]["shortfall"]["eligible"] == 390


def test_the_shared_function_is_named_and_pinned_when_given(tmp_path):
    s, oext, _ = make_root(tmp_path)
    assert spec(tmp_path, s, oext)["o_pass"]["sha256"] is None
    path = tmp_path / "oext_eval.py"
    path.write_bytes(b"# synthetic stand-in\n")
    doc = spec(tmp_path, s, oext, oext_eval=(path, sha256_bytes(path.read_bytes())))
    assert doc["o_pass"]["path"] == "scripts/stage1_s1/oext_eval.py" and doc["o_pass"]["sha256"] == sha256_bytes(b"# synthetic stand-in\n")
    with pytest.raises(s1.Refusal, match="hashes to"):
        spec(tmp_path, s, oext, oext_eval=(path, "0" * 64))


def test_the_extension_units(tmp_path):
    s, oext, r4 = make_root(tmp_path, with_r4=True)
    doc = spec(tmp_path, s, oext, extension={"R_1104": (r4["path"], r4["complete_sha256"], r4["job_sha256"])})
    assert doc["counts"]["regenerate"] == 7 and doc["jobs"][6]["unit"] == "R_1104"
    with pytest.raises(s1.Refusal, match="do not hold"):
        spec(tmp_path, s, oext, extension={"R_1199": (r4["path"], r4["complete_sha256"], r4["job_sha256"])})
    with pytest.raises(s1.Refusal, match="seed is 1104, the settings say 1105"):
        spec(tmp_path, s, oext, extension={"R_1105": (r4["path"], r4["complete_sha256"], r4["job_sha256"])})


@pytest.mark.parametrize("change,match", [
    (lambda s: s["units"][0].update(complete_sha256="0" * 64), "hashes to"),
    (lambda s: s["units"][1].update(job_sha256="0" * 64), "hashes to"),
    (lambda s: s["units"][2].update(seed=1109), "seed"),
    (lambda s: s["units"][3].update(d=2), "sealed R_d2 arm"),
    (lambda s: s["units"][3].update(kind="a0"), "not a0"),
    (lambda s: s.update(sealed_manifest={**s["sealed_manifest"], "sha256": "0" * 64}), "hashes to"),
])
def test_bad_sources_refuse(tmp_path, change, match):
    s, oext, _ = make_root(tmp_path)
    change(s)
    with pytest.raises(s1.Refusal, match=match):
        spec(tmp_path, s, oext)


def test_a_unit_whose_r_arm_is_another_draw_refuses(tmp_path):
    s, oext, _ = make_root(tmp_path)
    job = tmp_path / "units/R_1102/job.json"
    doc = json.loads(job.read_bytes())
    doc["arm"] = json.loads((tmp_path / "units/R_1101/job.json").read_bytes())["arm"]
    s["units"][4]["job_sha256"] = write(job, doc)
    complete = tmp_path / "units/R_1102/COMPLETE.json"
    cdoc = json.loads(complete.read_bytes())
    cdoc["job_sha256"] = s["units"][4]["job_sha256"]
    s["units"][4]["complete_sha256"] = write(complete, cdoc)
    with pytest.raises(s1.Refusal, match="sealed R_d2 arm"):
        spec(tmp_path, s, oext)


@pytest.mark.parametrize("change", [
    lambda c: c.update(complete=False),                                       # the job's SHA-256 is right
    lambda c: c.update(job_sha256="0" * 64),                                  # complete, but for another job
])
def test_a_complete_json_that_does_not_name_this_job_as_complete_refuses(tmp_path, change):
    s, oext, _ = make_root(tmp_path)
    complete = tmp_path / "units/R_1102/COMPLETE.json"
    cdoc = json.loads(complete.read_bytes())
    change(cdoc)
    s["units"][4]["complete_sha256"] = write(complete, cdoc)
    with pytest.raises(s1.Refusal, match="R_1102: COMPLETE.json does not name this job as complete"):
        spec(tmp_path, s, oext)


def test_deterministic_and_the_committed_settings(tmp_path):
    s, oext, _ = make_root(tmp_path)
    assert spec(tmp_path, s, oext) == spec(tmp_path, s, oext)
    doc, digest = s1.load_settings(brs.SETTINGS_PATH, brs.SETTINGS_SHA256, brs.SETTINGS_NAME)
    assert digest == brs.SETTINGS_SHA256
    fixed = {u["name"]: u["complete_sha256"] for u in doc["units"] if not u.get("conditional")}
    assert fixed["a0_1101"] == "8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9"
    assert fixed["R_1103"] == "d34e33f2e3b90b562a1b21da3fabc3e672842b7b2cbfe2eadae754601155692c"
    assert [u["name"] for u in doc["units"] if u.get("conditional")] == ["R_1104", "R_1105"]
    assert doc["sealed_manifest"]["sha256"] == "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8"
    assert doc["o_pass"]["function"] == "scripts/stage1_s1/oext_eval.py" and doc["cap"]["units"] == 11
