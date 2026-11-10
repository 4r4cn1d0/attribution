"""Re-verifier probes for R1 Track O's fix round (adversarial; ENGINEERING FIXTURES only: the builder's and the 1B
fixtures). Run from WS's root with RV_WS=<WS>; nothing here edits WS. Each test names the attack it tries.

A test named ..._GAP_... asserts a gap I claim (it passes when the gap is there)."""

from __future__ import annotations

import copy
import importlib
import json
import os
import shutil
import sys
from pathlib import Path

WS = Path(os.environ.get("RV_WS") or Path(__file__).resolve().parents[4]).resolve()
for extra in (WS / "scripts" / "scale78b" / "tests" / "oext", WS / "scripts" / "stage1" / "tests",
              WS / "scripts" / "stage1_s1" / "tests", WS):
    if str(extra) in sys.path:
        sys.path.remove(str(extra))
    sys.path.insert(0, str(extra))
_engine = importlib.util.find_spec("experiments.safety_selection")
sys.path.append(str(Path(_engine.origin).resolve().parent / "tests"))
_pkg = importlib.import_module("scripts.scale78b")
assert Path(_pkg.__file__).resolve().parents[2] == WS, _pkg.__file__

import pytest  # noqa: E402

import oext78_fixtures as f  # noqa: E402
import test_limits_fixtures as tf  # noqa: E402

w, oe, ou, uf, ofx, mk, s1 = f.w, f.oe, f.ou, f.uf, f.ofx, f.mk, f.s1
w1 = oe.w1_18
lc = importlib.import_module("scripts.stage1.limits.limits_common")
ORIG_W1 = (w1.SETTINGS_PATH, w1.SETTINGS_SHA256)
TOOLS = {"device": "test", "judge": "a fake judge", "decoder": "a fake decoder"}
KINDS = {"B-1101": "A", "G16-1101": "D"}


def globals_now():
    lej = w.module(w.LEAN_MODULE)
    return (ou.load_pinned_settings, oe.load_pinned_settings, ou.OEXT_SETTINGS_PATH, w1.SETTINGS_PATH,
            w1.SETTINGS_SHA256, lej.SETTINGS_PATH, lej.SETTINGS_SHA256, lej.OEXT_SETTINGS_PATH)


@pytest.fixture
def fake_tools(monkeypatch):
    def tools(doc, device, ledger_dir, guard_batch_size=None):
        return tf.fake_judge_records, tf.fake_decode, TOOLS
    monkeypatch.setattr(w1, "real_tools", tools)


# ===== A. label lies (GXB O3), re-run on the per-index design ===========================================================








# ===== B. leaks and restores ===========================================================================================








def test_B4_check_restores_the_label_globals_after_a_validator_refusal(tmp_path):
    """check patches OEXT_SETTINGS_PATH (and the W1-18 globals) while it validates; a refusal raised inside must not
    leave them set."""
    env = f.unit_world(tmp_path / "u", "full", full_reason="rv: no record")
    _, _, doc = f.put_unit_settings(env)
    before = globals_now()
    assert f.wrapper(env, ["check", "--family", f.FAMILY])[0] == 0
    assert globals_now() == before
    doc = copy.deepcopy(doc)
    doc["oext"]["settings"]["path"] = "scripts/stage1_s1/settings/oext_eval.json"
    env.fam.put("oext_unit", doc)
    code, _, err = f.wrapper(env, ["check", "--family", f.FAMILY])
    assert code == 2 and "oext names the O-ext module" in err
    assert globals_now() == before


# ===== C. index checks on every command (R-5) ==========================================================================


def _index_fault(fam: f.Family, fault: str, tmp_path: Path) -> list[str]:
    path, digest = fam.index("X")
    if fault == "name":
        other = path.with_name(mk.index_name(f.OTHER, "X"))
        shutil.copy(path, other)
        return ["--family", f.FAMILY, "--index", str(other), "--index-sha256", digest]
    if fault == "sha":
        return ["--family", f.FAMILY, "--index", str(path), "--index-sha256", "0" * 64]
    if fault == "kind":
        doc = json.loads(path.read_bytes())
        doc["kind"] = "another index"
        h = f.write(path, doc)
        return ["--family", f.FAMILY, "--index", str(path), "--index-sha256", h]
    if fault in ("family", "engine"):
        doc = json.loads(path.read_bytes())
        doc["family" if fault == "family" else "engine"] = f.OTHER if fault == "family" else "Y"
        h = f.write(path, doc)
        return ["--family", f.FAMILY, "--index", str(path), "--index-sha256", h]
    if fault == "file-off-pin":
        doc = json.loads(path.read_bytes())
        doc["files"]["limits_overrefusal_checks"]["sha256"] = "1" * 64
        h = f.write(path, doc)
        return ["--family", f.FAMILY, "--index", str(path), "--index-sha256", h]
    if fault == "y-index-for-x":
        ypath, yh = fam.index("Y")
        return ["--family", f.FAMILY, "--index", str(ypath), "--index-sha256", yh]
    raise AssertionError(fault)


@pytest.mark.parametrize("fault", ["kind"])
@pytest.mark.parametrize("command", ["unit", "lean-run", "lean-verify", "w1_18", "check"])
def test_C1_every_command_refuses_a_bad_index(tmp_path, fault, command):
    env = f.unit_world(tmp_path / "u", "128")
    f.put_unit_settings(env)
    lead = _index_fault(env.fam, fault, tmp_path)
    out = tmp_path / "o"
    tail = {"unit": f.unit_args(env, out, run=env.world.units["evaluated"]),
            "lean-run": ["run", "--job", "j", "--prepared", str(env.world.prepared), "--recipe", "r", "--out", str(out)],
            "lean-verify": ["verify", "--out", str(out)],
            "w1_18": ["--out", str(out)], "check": []}[command]
    word = command.split("-")[0]
    before = globals_now()
    code, stdout, err = f.call(w.main, [word, *lead, *tail], loaders=uf.loaders()) if word in ("unit", "lean") else \
        f.call(w.main, [word, *lead, *tail])
    if fault == "file-off-pin" and command == "lean-verify":    # verify reads no settings file (by design)
        assert code != 0 and not out.exists() and globals_now() == before, err[-300:]
        return
    assert code == 2, (command, fault, err[-300:])
    assert '"refused": "oext_78b: ' in err and not out.exists() and globals_now() == before


# ===== D. R-6: the W1-18 record on the Mac ============================================================================


def family_with_record(tmp_path: Path, kinds=KINDS, family=f.FAMILY):
    root = tmp_path / "data"
    settings, _, _ = tf.build_checks(root, kinds)
    fam = f.Family(tmp_path / "fam", family)
    fam.manifest, fam.branch = settings["prepared"]["manifest_sha256"], "128"
    fam.put("limits_overrefusal_checks", settings)
    code, _, err = f.wrapper(fam, ["w1_18", "--family", family, "--out", str(tmp_path / "w"), "--data-root",
                                   str(root)])
    assert code == 0, err[-300:]
    return fam, tmp_path / "w" / w1.OUTPUT, root


def pin(fam: f.Family, record: Path | None, branch: str = "128", reason: str | None = None, role="oext_eval"):
    doc = ofx.settings_doc(branch=branch, cut=128, dev=100, w1_18_sha256=None if record is None else f.sha(record),
                           full_reason=reason)
    doc["cap"]["w1_18"]["settings_sha256"] = fam.files["limits_overrefusal_checks"][1]
    fam.put(role, doc)
    fam.branch = branch


def rcheck(fam, *extra):
    code, out, err = f.wrapper(fam, ["check", "--family", fam.family, *extra])
    return code, out, err


def test_D1_the_right_record_passes_and_a_bad_one_never_does(tmp_path, fake_tools):
    fam, record, _ = family_with_record(tmp_path / "a")
    pin(fam, record)
    assert rcheck(fam, "--w1-18-record", str(record))[0] == 0
    doc = json.loads(record.read_bytes())
    cases = {}
    # same provenance, a unit's cut changed
    d = copy.deepcopy(doc); next(iter(d["units"].values()))["truncation"]["cap_tokens"] = 64; cases["cut"] = d
    # same provenance, the verdict a string
    d = copy.deepcopy(doc); d["truncation_check"]["pass"] = "true"; cases["verdict-type"] = d
    # same provenance, version 2
    d = copy.deepcopy(doc); d["version"] = 2; cases["version"] = d
    # same provenance and unit count, a unit renamed
    d = copy.deepcopy(doc); k = sorted(d["units"])[0]; d["units"]["renamed"] = d["units"].pop(k); cases["renamed"] = d
    # same provenance, one unit more (W1-18 never lists one more)
    d = copy.deepcopy(doc); d["units"]["extra"] = copy.deepcopy(next(iter(d["units"].values()))); cases["extra"] = d
    # provenance settings of the other family
    d = copy.deepcopy(doc); d["provenance"]["settings_sha256"] = "9" * 64; cases["provenance"] = d
    for name, d in cases.items():
        p = tmp_path / f"bad-{name}.json"
        f.write(p, d)
        pin(fam, p)
        code, out, err = rcheck(fam, "--w1-18-record", str(p))
        assert code == 2 and out == "", (name, err[-300:])






# ===== E. R-9: the side units' files =================================================================================


def side(tmp_path: Path, kinds=KINDS):
    root = tmp_path / "data"
    settings, _, _ = tf.build_checks(root, kinds)
    fam = f.Family(tmp_path / "fam")
    fam.manifest, fam.branch = settings["prepared"]["manifest_sha256"], oe.PENDING
    fam.put("limits_overrefusal_checks", settings)
    pin(fam, None, oe.PENDING)
    return fam, settings, root


def _rewrite_complete(settings, root, name, change, fam):
    folder = root / settings["units"][name]["path"]
    marker = json.loads((folder / "COMPLETE.json").read_bytes())
    change(marker, folder)
    settings["units"][name]["complete_sha256"] = f.write(folder / "COMPLETE.json", marker)
    fam.put("limits_overrefusal_checks", settings)
    pin(fam, None, oe.PENDING)










def test_E5_a_unit_folder_linked_out_of_the_data_root_is_a_problem(tmp_path):
    fam, settings, root = side(tmp_path)
    name = sorted(settings["units"])[0]
    folder = root / settings["units"][name]["path"]
    outside = tmp_path / "outside"
    shutil.move(str(folder), str(outside))
    folder.symlink_to(outside, target_is_directory=True)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and "leaves the data root" in out




# ===== F. check: a waiting role masks any refusal of that role ==========================================================




# ===== G. more probes for untested branches ===========================================================================


def test_G1_check_refuses_a_changed_run_file(tmp_path, monkeypatch):
    env = f.unit_world(tmp_path / "u", "full", full_reason="rv: no record")
    f.put_unit_settings(env)
    assert f.wrapper(env, ["check", "--family", f.FAMILY])[0] == 0
    monkeypatch.setitem(w.CODE, "scripts.stage1_s1.oext_eval", "0" * 64)
    code, _, err = f.wrapper(env, ["check", "--family", f.FAMILY])
    assert code == 2 and "the run files stay byte for byte" in err


def test_G2_an_engine_unit_naming_job_json_beside_its_list_is_found(tmp_path):
    fam, settings, root = side(tmp_path)
    name = sorted(settings["units"])[0]

    def move(marker, folder):
        marker["job_sha256"] = marker["files"].pop("job.json")
    _rewrite_complete(settings, root, name, move, fam)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 0, err[-300:]
    assert json.loads(out)["side_units"]["units"][name]["files"]["job.json"]["state"] == "listed"


def test_G3_a_marker_that_is_not_complete_is_a_problem(tmp_path):
    fam, settings, root = side(tmp_path)
    name = sorted(settings["units"])[0]
    _rewrite_complete(settings, root, name, lambda m, _: m.update(complete=False), fam)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and "not a complete marker" in out


def test_G4_the_makers_check_reports_a_file_that_differs(tmp_path):
    sdir = tmp_path / "s"
    assert f.call(mk.main, ["--settings-dir", str(sdir)])[0] == 0
    assert f.call(mk.main, ["--settings-dir", str(sdir), "--check"])[0] == 0
    target = sdir / mk.file_name("oext_eval", "llama31-8b")
    target.write_bytes(target.read_bytes() + b" ")
    code, out, err = f.call(mk.main, ["--settings-dir", str(sdir), "--check"])
    assert code == 1 and "DIFFERS: 1 files" in err
