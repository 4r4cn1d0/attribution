"""Re-verifier probes, second pass (fix round 2) for R1 Track O's fix round (adversarial; ENGINEERING FIXTURES only: the builder's and the 1B
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
            w1.SETTINGS_SHA256, lej.SETTINGS_PATH, lej.SETTINGS_SHA256, lej.OEXT_SETTINGS_PATH, s1.code_identity)


@pytest.fixture
def fake_tools(monkeypatch):
    def tools(doc, device, ledger_dir, guard_batch_size=None):
        return tf.fake_judge_records, tf.fake_decode, TOOLS
    monkeypatch.setattr(w1, "real_tools", tools)


# ===== A. label lies (GXB O3), re-run on the per-index design ===========================================================










# ===== B. leaks and restores ===========================================================================================










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
    if fault == "w1-index-for-x":
        wpath, wh = fam.index("W1")
        return ["--family", f.FAMILY, "--index", str(wpath), "--index-sha256", wh]
    raise AssertionError(fault)








def test_C4_check_on_the_w1_index_takes_no_record(tmp_path, fake_tools):
    fam, record, _ = family_with_record(tmp_path / "a")
    code, _, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--engine", "W1", "--w1-18-record", str(record)])
    assert code == 2 and "holds no O-ext settings" in err


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
    if role == "oext_eval_y":
        doc["engine_x"] = f.ENGINE_Y_FIXTURE          # R-23: the Y index names engine Y's identity
    fam.put(role, doc)
    fam.branch = branch


def rcheck(fam, *extra):
    code, out, err = f.wrapper(fam, ["check", "--family", fam.family, *extra])
    return code, out, err








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
















# ===== F. check: a waiting role masks any refusal of that role ==========================================================


def _waiting(fam, settings, change):
    s_ = copy.deepcopy(settings)
    change(s_)
    fam.put("limits_overrefusal_checks", s_)
    pin(fam, None, oe.PENDING)
    fam.waits = [{"pin": "THETA0_JOB", "event": mk.EVENTS["THETA0_JOB"], "where": ["x"],
                  "roles": ["limits_overrefusal_checks"]}]
    return f.wrapper(fam, ["check", "--family", f.FAMILY])






# ===== G. more probes for untested branches ===========================================================================










# ===== H. R-20 / R-21 / OR5 ===========================================================================================


def _pins_with(change):
    pins, _ = mk.load_pins()
    pins = copy.deepcopy(pins)
    change(pins)
    return pins


def _maker(tmp_path, pins, root):
    pp = tmp_path / "pins.json"
    pp.write_bytes(mk.dumps(pins))
    return f.call(mk.main, ["--pins", str(pp), "--settings-dir", str(tmp_path / "s"), "--records-root", str(root)])






def test_H3_the_w1_18_78b_form(tmp_path):
    code, out, err = f.call(mk.main, ["--w1-18-78b"])
    form = json.loads(out)
    assert code == 0 and set(form) == {"files", "side_units"}
    assert form["files"]["scripts/scale78b/oext_78b.py"] == f.sha(mk.HERE / "oext_78b.py")
    for fam in w.FAMILIES:
        for n in (mk.index_name(fam, "W1"), mk.file_name("limits_overrefusal_checks", fam)):
            assert form["files"]["scripts/scale78b/settings/" + n] == f.sha(mk.SETTINGS_DIR / n)
        lim = json.loads((mk.SETTINGS_DIR / mk.file_name("limits_overrefusal_checks", fam)).read_bytes())
        assert form["side_units"][fam] == {n: {"path": u["path"], "complete_sha256": u["complete_sha256"],
                                               "job_sha256": u["job_sha256"]} for n, u in lim["units"].items()}
    assert not any(k.startswith("scripts/scale78b/settings/OEXT-78B__") or "oext_eval" in k or "lean" in k
                   for k in form["files"])
    assert all(k.startswith("scripts/") for k in form["files"])




def test_I1_a_y_index_with_no_engine_identity_and_no_engine_y_wait_refuses(tmp_path):
    env = f.unit_world(tmp_path / "u", "full", full_reason="rv: no record", engine_y=True)
    f.put_unit_settings(env, engine_y=True)
    env.fam.engine_y = None                                   # the index names no identity, and nothing waits on it
    code, _, err = f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])
    assert code == 2 and "names no engine identity" in err, err[-300:]


