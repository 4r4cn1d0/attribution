"""Track O's follow-up in round R2 (from R1's second re-verification, R/r1-o-reverify2.md): W2-1, the printed kit forms
carry the family's W1-18 record after a branch fill; W2-2, the re-verifier's targeted tests H3, C4 and I1 for its three
surviving mutants; W2-3, a fault in a waiting settings file exits 2 wherever the 1B validator would test it (before or
after the null pin), and a stale wait refuses. ENGINEERING FIXTURES only (the builder's and the 1B fixtures)."""

from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

import oext78_fixtures as f
import test_limits_fixtures as tf
from test_oext_78b_files import all_null_pins

w, oe, ou, uf, ofx, mk, s1 = f.w, f.oe, f.ou, f.uf, f.ofx, f.mk, f.s1
w1 = oe.w1_18
REPO = Path(w.__file__).resolve().parents[2]
TOOLS = {"device": "test", "judge": "a fake judge", "decoder": "a fake decoder"}
KINDS = {"B-1101": "A", "G16-1101": "D"}


def rk():
    spec = importlib.util.spec_from_file_location("rules_78b_for_track_o_r2", REPO / "runkit" / "stage1-78b" / "rules_78b.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_tools(monkeypatch):
    def tools(doc, device, ledger_dir, guard_batch_size=None):
        return tf.fake_judge_records, tf.fake_decode, TOOLS
    monkeypatch.setattr(w1, "real_tools", tools)


# ===== W2-1: the printed forms carry the W1-18 record ===================================================================


def _filled(tmp_path: Path, branch: str = "128", reason: str | None = None):
    """The pre-fill (all-null) pins with OLMo-2-7B's branch filled (a synthetic, text-free record at its R-21 place
    under a records root in tmp_path), derived into a new settings folder (any committed state: OR1's rule)."""
    pins = all_null_pins()
    root, settings_dir = tmp_path / "records", tmp_path / "settings"
    w1 = pins["families"]["olmo2-7b"]["w1_18"]
    if reason is None:
        rel = f"{mk.RECORDS_DIR}overrefusal_checks__olmo2-7b.json"
        digest = f.write(root / rel, {"kind": "stage1 over-refusal checks", "version": 1, "fixture": True})
        w1.update(branch=branch, record_path=rel, record_sha256=digest, full_reason=None)
    else:
        w1.update(branch="full", record_path=None, record_sha256=None, full_reason=reason)
    pins_path = tmp_path / "pins.json"
    pins_path.write_bytes(mk.dumps(pins))
    code, _, err = f.call(mk.main, ["--pins", str(pins_path), "--settings-dir", str(settings_dir),
                                    "--records-root", str(root)])
    assert code == 0, err[-300:]
    return pins, pins_path, settings_dir, root


@pytest.mark.parametrize("branch", ["128", "full"])
def test_after_a_branch_fill_the_printed_x_and_y_forms_carry_the_w1_18_record(tmp_path, branch):
    pins, pins_path, settings_dir, root = _filled(tmp_path, branch)
    rel, digest = pins["families"]["olmo2-7b"]["w1_18"]["record_path"], pins["families"]["olmo2-7b"]["w1_18"]["record_sha256"]
    for flag in ("--oext-78b", "--oext-78b-y"):
        code, out, err = f.call(mk.main, ["--pins", str(pins_path), "--settings-dir", str(settings_dir),
                                          "--records-root", str(root), flag, "olmo2-7b"])
        assert code == 0, err[-300:]
        form = json.loads(out)
        assert form["files"][rel] == digest == f.sha(root / rel)
        assert [k for k in form["files"] if not k.startswith("scripts/")] == [rel]
        assert rk().oext_form_problem(form) is None                     # R-21: RK takes the one record entry
        code, out, _ = f.call(mk.main, ["--pins", str(pins_path), "--settings-dir", str(settings_dir),
                                        "--records-root", str(root), flag, "llama31-8b"])
        assert code == 0 and not any(k.startswith(mk.RECORDS_DIR) for k in json.loads(out)["files"])


def test_without_a_record_no_form_names_one(tmp_path):
    """The pre-fill (pending) state and Branch full with a reason: no record entry."""
    files = mk.derive_all(all_null_pins(), None, tmp_path / "null")
    for family in w.FAMILIES:
        for engine in ("X", "Y"):
            form = mk.form(family, engine, files, w.code_pins(engine))
            assert all(k.startswith("scripts/") for k in form["files"])
    pins, _, settings_dir, _ = _filled(tmp_path, reason="R2 fixture: the check could not run")
    files = mk.derive_all(pins, None, settings_dir)
    assert all(k.startswith("scripts/") for k in mk.form("olmo2-7b", "X", files, w.code_pins("X"))["files"])


# ===== W2-2: the re-verifier's targeted tests (r1-o-reverify2-scratch/test_zz_rv2_targeted.py) ========================


def test_H3_the_w1_18_78b_form(tmp_path):
    """RV2-m-w1-side-job: W1_18_78B's side units carry their job.json pins (R-20)."""
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


def test_H3b_the_side_units_job_pins_follow_a_theta0_fill(tmp_path):
    """RV2-m-w1-side-job, on a filled pin: theta0's job pin reaches W1_18_78B's side units."""
    pins, _ = mk.load_pins()
    pins = copy.deepcopy(pins)
    pins["families"]["olmo2-7b"]["units"]["untuned"]["job_sha256"] = "c" * 64
    files = mk.derive_all(pins, None, tmp_path / "s")
    form = mk.w1_18_78b_form(files, w.code_pins("W1"))
    assert form["side_units"]["olmo2-7b"]["untuned"]["job_sha256"] == "c" * 64


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


def test_C4_check_on_the_w1_index_takes_no_record(tmp_path, fake_tools):
    """RV2-w-w1-record-ignored."""
    fam, record, _ = family_with_record(tmp_path / "a")
    code, _, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--engine", "W1", "--w1-18-record", str(record)])
    assert code == 2 and "holds no O-ext settings" in err


def test_I1_a_y_index_with_no_engine_identity_and_no_engine_y_wait_refuses(tmp_path):
    """RV2-w-null-identity-waits."""
    env = f.unit_world(tmp_path / "u", "full", full_reason="rv: no record", engine_y=True)
    f.put_unit_settings(env, engine_y=True)
    env.fam.engine_y = None                                   # the index names no identity, and nothing waits on it
    code, _, err = f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])
    assert code == 2 and "names no engine identity" in err, err[-300:]


# ===== W2-3: a fault in a waiting file exits 2 ==========================================================================


def side(tmp_path: Path, kinds=KINDS):
    root = tmp_path / "data"
    settings, _, _ = tf.build_checks(root, kinds)
    fam = f.Family(tmp_path / "fam")
    fam.manifest, fam.branch = settings["prepared"]["manifest_sha256"], oe.PENDING
    fam.put("limits_overrefusal_checks", settings)
    pin(fam, oe.PENDING)
    return fam, settings, root


def pin(fam: f.Family, branch: str) -> None:
    doc = ofx.settings_doc(branch=branch, cut=128, dev=100, w1_18_sha256=None)
    doc["cap"]["w1_18"]["settings_sha256"] = fam.files["limits_overrefusal_checks"][1]
    fam.put("oext_eval", doc)
    fam.branch = branch


def waiting(fam, settings, change, waits=("THETA0_JOB",)):
    s_ = copy.deepcopy(settings)
    change(s_)
    fam.put("limits_overrefusal_checks", s_)
    pin(fam, oe.PENDING)
    fam.waits = [{"pin": p, "event": mk.EVENTS[p], "where": ["x"], "roles": ["limits_overrefusal_checks"]}
                 for p in waits]
    return f.wrapper(fam, ["check", "--family", f.FAMILY])


def _theta0_null(s_):
    last = sorted(s_["units"])[-1]
    s_["units"]["untuned"] = s_["units"].pop(last)
    s_["units"]["untuned"]["job_sha256"] = None


def test_a_waiting_w1_18_file_with_no_other_fault_prints_waits(tmp_path):
    fam, settings, _ = side(tmp_path)
    code, out, err = waiting(fam, settings, _theta0_null)
    assert code == 0 and json.loads(out)["settings"]["limits_overrefusal_checks"] == "waits", err[-300:]


def test_W2_3_a_fault_after_the_null_pin_exits_2(tmp_path):
    """The re-verifier's F2 (a GAP before R2): the bank size is checked after the units, so before W2-3 the null
    theta0 pin hid it and check printed "waits" with exit 0."""
    fam, settings, _ = side(tmp_path)

    def change(s_):
        _theta0_null(s_)
        s_["bank"]["size"] = 99
    code, out, err = waiting(fam, settings, change)
    assert code == 2 and "waits" not in out, (out[-300:], err[-300:])


def test_W2_3_a_fault_before_the_null_pin_exits_2(tmp_path):
    """The re-verifier's F1."""
    fam, settings, _ = side(tmp_path)
    first = sorted(settings["units"])[0]

    def change(s_):
        s_["units"][first]["seed"] = "not an integer"
        _theta0_null(s_)
    code, out, err = waiting(fam, settings, change)
    assert code == 2 and "no path or no integer seed" in err, (out[-300:], err[-300:])


def test_W2_3_a_null_pin_that_no_wait_names_exits_2(tmp_path):
    """theta0's job pin is null, but the index lists only UNIT_JOB (whose fields are the a0 units')."""
    fam, settings, _ = side(tmp_path)
    code, _, err = waiting(fam, settings, _theta0_null, waits=("UNIT_JOB",))
    assert code == 2 and "job_sha256" in err, err[-300:]


def test_W2_3_a_stale_wait_refuses(tmp_path):
    """The index lists theta0's job pin as waiting, but the file holds it (a fill without a re-derived index)."""
    fam, settings, _ = side(tmp_path)

    def change(s_):
        last = sorted(s_["units"])[-1]
        s_["units"]["untuned"] = s_["units"].pop(last)          # its job pin stays filled
    code, _, err = waiting(fam, settings, change)
    assert code == 2 and "waits on THETA0_JOB in the index but is filled" in err, err[-300:]
    code, _, err = waiting(fam, settings, lambda s_: None)       # no untuned unit at all: the field is absent
    assert code == 2 and "has no field units.untuned.job_sha256" in err, err[-300:]

    def no_key(s_):
        _theta0_null(s_)
        del s_["units"]["untuned"]["job_sha256"]                 # the unit is there, its job pin key is not
    code, _, err = waiting(fam, settings, no_key)
    assert code == 2 and "has no field units.untuned.job_sha256" in err, err[-300:]


def test_W2_3_a_y_file_waiting_on_engine_y_is_validated_under_a_placeholder(tmp_path):
    """A null ENGINE_Y no longer skips the Y files' validation: a sound file prints "waits"; a fault exits 2."""
    env = f.unit_world(tmp_path / "u", "full", full_reason="R2 fixture: no record", engine_y=True)
    path, digest, doc = f.put_unit_settings(env, engine_y=True)
    env.fam.engine_y = None
    for role in ("oext_eval_y", "oext_unit_y"):
        d = json.loads(env.fam.files[role][0].read_bytes())
        d["engine_x"] = None
        env.fam.put(role, d)
    env.fam.waits = [{"pin": "ENGINE_Y", "event": mk.EVENTS["ENGINE_Y"], "where": ["shared.engine_y"],
                      "roles": ["oext_eval_y", "oext_unit_y"]}]
    unit_doc = json.loads(env.fam.files["oext_unit_y"][0].read_bytes())
    unit_doc["oext"]["settings"]["sha256"] = env.fam.files["oext_eval_y"][1]
    env.fam.put("oext_unit_y", unit_doc)
    code, out, err = f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])
    assert code == 0, err[-300:]
    assert json.loads(out)["settings"] == {"limits_overrefusal_checks": "valid", "oext_eval_y": "waits",
                                           "oext_unit_y": "waits"}
    good = copy.deepcopy(unit_doc)
    unit_doc["prepared"]["manifest_sha256"] = "not a hash"
    env.fam.put("oext_unit_y", unit_doc)
    code, _, err = f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])
    assert code == 2 and "manifest_sha256" in err, err[-300:]
    eval_doc = json.loads(env.fam.files["oext_eval_y"][0].read_bytes())         # a waiting Y file off W1-18's binding
    eval_doc["cap"]["w1_18"]["settings_sha256"] = "1" * 64
    good["oext"]["settings"]["sha256"] = env.fam.put("oext_eval_y", eval_doc)[1]
    env.fam.put("oext_unit_y", good)
    code, _, err = f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])
    assert code == 2 and "W1-18's settings are" in err, err[-300:]
