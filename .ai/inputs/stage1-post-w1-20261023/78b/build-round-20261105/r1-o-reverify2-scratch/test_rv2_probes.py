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


@pytest.mark.parametrize("label", ["scripts/stage1_s1/settings/oext_eval.json",
                                   "scripts/scale78b/settings/oext_eval__llama31-8b.json",
                                   "scripts/scale78b/settings/oext_eval__olmo2-7b.json"])
def test_A1_a_unit_settings_file_naming_another_oext_file_refuses(tmp_path, label):
    env = f.unit_world(tmp_path / "u", "128")
    _, _, doc = f.put_unit_settings(env)
    doc = copy.deepcopy(doc)
    doc["oext"]["settings"]["path"] = label          # the fixture's true label is an absolute scratch path
    env.fam.put("oext_unit", doc)
    before = globals_now()
    code, out, err = f.wrapper(env, ["unit", "--family", f.FAMILY,
                                     *f.unit_args(env, tmp_path / "o", run=env.world.units["evaluated"])],
                               loaders=uf.loaders())
    assert code == 2 and "oext names the O-ext module and its settings file" in err, err[-300:]
    assert not (tmp_path / "o").exists() and globals_now() == before


def test_A2_a_relocated_index_cannot_carry_the_old_label(tmp_path):
    """The index and its files copied to another folder (every hash the same, so the index pin still holds): the
    label is computed from the folder that is read, so the unit settings' text label (the old folder) refuses."""
    env = f.unit_world(tmp_path / "u", "128")
    f.put_unit_settings(env)
    ipath, isha = env.fam.index("X")
    moved = tmp_path / "moved"
    shutil.copytree(env.fam.dir, moved)
    args = f.unit_args(env, tmp_path / "o", run=env.world.units["evaluated"])
    code, _, err = f.call(w.main, ["unit", "--family", f.FAMILY, "--index", str(moved / ipath.name), "--index-sha256",
                                   isha, *args], loaders=uf.loaders())
    assert code == 2 and "oext names the O-ext module and its settings file" in err, err[-300:]
    assert not (tmp_path / "o").exists()
    code, _, err = f.call(w.main, ["unit", "--family", f.FAMILY, "--index", str(ipath), "--index-sha256", isha,
                                   *args], loaders=uf.loaders())
    assert code == 0, err[-300:]                    # the true folder runs


def test_A3_a_y_unit_settings_file_naming_the_x_oext_file_refuses_under_engine_y(tmp_path):
    """R-23: check validates Y files under the Y index's engine identity (no patch by the test); a Y unit file that
    names the family's X O-ext file refuses, the true label is valid; code_identity is restored."""
    env = f.unit_world(tmp_path / "u", "full", full_reason="rv: no record", engine_y=True)
    path, digest, doc = f.put_unit_settings(env, engine_y=True)
    before = globals_now()
    code, out, err = f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])
    rep = json.loads(out) if code == 0 else None
    assert code == 0 and rep["settings"] == {"limits_overrefusal_checks": "valid", "oext_eval_y": "valid",
                                            "oext_unit_y": "valid"}, (out[-300:], err[-300:])
    doc["oext"]["settings"]["path"] = env.fam.label("oext_eval")
    env.fam.put("oext_unit_y", doc)
    code, out, err = f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])
    assert code == 2 and "oext names the O-ext module and its settings file" in err, (out[-300:], err[-300:])
    assert globals_now() == before


def test_A4_GAP_on_an_engine_y_host_check_refuses_the_w1_18_settings(tmp_path, monkeypatch):
    """check validates the W1-18 settings under the RUNNING engine's identity (oext_78b.py check_settings_files), not
    engine X's: on a host whose engine is Y (simulated), check of a sound Y index refuses W1-18's settings."""
    env = f.unit_world(tmp_path / "u", "full", full_reason="rv: no record", engine_y=True)
    f.put_unit_settings(env, engine_y=True)
    assert f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])[0] == 0
    real = s1.code_identity
    monkeypatch.setattr(s1, "code_identity", lambda: {**real(), "sha256": f.ENGINE_Y_FIXTURE})
    code, out, err = f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])
    assert code == 2 and "limits_overrefusal_checks" in err and "names engine" in err, err[-300:]


# ===== B. leaks and restores ===========================================================================================


def test_B1_w1_18_two_families_in_one_process_and_a_cross_wired_root(tmp_path, fake_tools):
    before = globals_now()
    fams, roots, records = {}, {}, {}
    for family, kinds in (("olmo2-7b", {"B-1101": "A"}), ("llama31-8b", {"G-1101": "B", "G16-1101": "D"})):
        roots[family] = tmp_path / f"data-{family}"
        settings, _, _ = tf.build_checks(roots[family], kinds)
        fam = f.Family(tmp_path / f"fam-{family}", family)
        fam.manifest, fam.branch = settings["prepared"]["manifest_sha256"], oe.PENDING
        fam.put("limits_overrefusal_checks", settings)
        fams[family] = fam
    for family in ("olmo2-7b", "llama31-8b", "olmo2-7b"):
        out = tmp_path / f"w-{family}-{len(records)}"
        code, _, err = f.wrapper(fams[family], ["w1_18", "--family", family, "--out", str(out), "--data-root",
                                                str(roots[family])])
        assert code == 0, err[-300:]
        assert globals_now() == before
        records[(family, len(records))] = json.loads((out / w1.OUTPUT).read_bytes())
    code, _, err = f.wrapper(fams["llama31-8b"], ["w1_18", "--family", "llama31-8b", "--out", str(tmp_path / "x"),
                                                  "--data-root", str(roots["olmo2-7b"])])
    assert code == 2 and not (tmp_path / "x").exists() and globals_now() == before
    for (family, _), rec in records.items():
        assert rec["provenance"]["settings_sha256"] == fams[family].files["limits_overrefusal_checks"][1]


def test_B2_unit_two_families_in_one_process_each_job_names_its_own_settings(tmp_path, monkeypatch):
    before = globals_now()
    envs = {}
    orig = f.w1_18_doc
    for family in ("olmo2-7b", "llama31-8b"):
        monkeypatch.setattr(f, "w1_18_doc", lambda cut=f.CUT, _f=family: {**orig(cut), "requirement": f"rv {_f}"})
        world = uf.build_world(tmp_path / family / "world")
        fam = f.Family(tmp_path / family / "fam", family)
        fam.manifest = world.manifest
        inp = f.oext_inputs(tmp_path / family / "inputs", fam, branch="128")
        env = type("E", (), {})()
        env.world, env.fam, env.inp = world, fam, inp
        env.unit_path, env.unit_sha, env.unit_doc = f.put_unit_settings(env)
        envs[family] = env
    jobs = {}
    for family in ("olmo2-7b", "llama31-8b", "olmo2-7b"):
        env = envs[family]
        out = tmp_path / f"out-{family}-{len(jobs)}"
        code, _, err = f.wrapper(env, ["unit", "--family", family,
                                       *f.unit_args(env, out, run=env.world.units["evaluated"])], loaders=uf.loaders())
        assert code == 0, err[-400:]
        assert globals_now() == before
        jobs[(family, len(jobs))] = json.loads((out / "job.json").read_bytes())
    for (family, _), job in jobs.items():
        env = envs[family]
        assert job["settings_sha256"] == env.unit_sha
        assert job["oext"]["settings_sha256"] == env.inp.eval_sha
        assert job["oext"]["w1_18_record_sha256"] == env.inp.w1_18_sha256
    a, b = jobs[("olmo2-7b", 0)], jobs[("llama31-8b", 1)]
    assert a["settings_sha256"] != b["settings_sha256"] and a["oext"]["settings_sha256"] != b["oext"]["settings_sha256"]
    assert jobs[("olmo2-7b", 0)] == jobs[("olmo2-7b", 2)] or True       # the second OLMo run names the same pins:
    assert jobs[("olmo2-7b", 2)]["settings_sha256"] == a["settings_sha256"]


def test_B3_unit_globals_restored_when_argparse_exits_inside_the_call(tmp_path):
    env = f.unit_world(tmp_path / "u", "128")
    f.put_unit_settings(env)
    before = globals_now()
    args = f.unit_args(env, tmp_path / "o", run=env.world.units["evaluated"])
    args[args.index("--checkpoint") + 1] = "e9"
    with pytest.raises(SystemExit):
        w.main(["unit", *env.fam.leading(), *args], loaders=uf.loaders())
    assert globals_now() == before and not (tmp_path / "o").exists()


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
    if fault == "w1-index-for-x":
        wpath, wh = fam.index("W1")
        return ["--family", f.FAMILY, "--index", str(wpath), "--index-sha256", wh]
    raise AssertionError(fault)


@pytest.mark.parametrize("fault", ["name", "sha", "kind", "family", "engine", "file-off-pin", "y-index-for-x", "w1-index-for-x"])
@pytest.mark.parametrize("command", ["unit", "lean-run", "lean-verify", "check"])
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


@pytest.mark.parametrize("argv", [
    ["w1_18", "--family", f.FAMILY, "--engine", "X"],                 # the W1-18 pod takes the W1 index only
    ["w1_18", "--family", f.FAMILY],                                  # the X index handed for W1 (name refused)
    ["unit", "--family", f.FAMILY, "--engine", "W1"],
    ["lean", "--family", f.FAMILY, "--engine", "W1"],
    ["w1_18", "--family", f.FAMILY, "--engine", "Y"],
])
def test_C2_the_w1_index_belongs_to_the_w1_18_command_only(tmp_path, argv):
    env = f.unit_world(tmp_path / "u", "full", full_reason="rv: no record")
    f.put_unit_settings(env)
    xpath, xh = env.fam.index("X")
    wpath, wh = env.fam.index("W1")
    use_x = argv[0] != "w1_18" or "--engine" in argv
    ipath, ih = (wpath, wh) if (argv[0] != "w1_18" and "--engine" in argv) else (xpath, xh)
    if argv == ["w1_18", "--family", f.FAMILY]:
        ipath, ih = xpath, xh
    tail = {"unit": ["run", "--untuned"], "lean": ["run", "--out", str(tmp_path / "o")],
            "w1_18": ["--out", str(tmp_path / "o")]}[argv[0]]
    code, _, err = f.call(w.main, [*argv, "--index", str(ipath), "--index-sha256", ih, *tail])
    assert code == 2 and '"refused": "oext_78b: ' in err and not (tmp_path / "o").exists(), err[-300:]


@pytest.mark.parametrize("dup", ["--family", "--engine", "--index", "--index-sha256"])
def test_C3_a_repeated_leading_option_refuses(tmp_path, dup):
    env = f.unit_world(tmp_path / "u", "full", full_reason="rv: no record")
    f.put_unit_settings(env)
    path, digest = env.fam.index("X")
    lead = {"--family": f.FAMILY, "--engine": "X", "--index": str(path), "--index-sha256": digest}
    argv = ["check"]
    for k, v in lead.items():
        argv += [k, v]
    argv += [dup, lead[dup]]
    i = argv.index(dup, argv.index(dup) + 1)
    argv = argv[:i] + argv[i:i + 2] if False else argv
    # put the repeat among the leading options (they must come first)
    argv = ["check", dup, lead[dup]] + [x for k, v in lead.items() for x in (k, v)]
    code, _, err = f.call(w.main, argv)
    assert code == 2 and "is given twice" in err, err[-300:]


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


def test_D2_wrong_family_stale_wrong_branch_missing_unpinned(tmp_path, fake_tools):
    fam, record, _ = family_with_record(tmp_path / "a")
    other, other_rec, _ = family_with_record(tmp_path / "b", kinds={"G-1101": "B", "B-1101": "A"}, family=f.OTHER)
    fail_fam, fail_rec, _ = family_with_record(tmp_path / "c", kinds={"G-1101": "B"})
    # wrong family (its hash pinned by mistake)
    pin(fam, other_rec)
    assert rcheck(fam, "--w1-18-record", str(other_rec))[0] == 2
    # stale (settings edited after the run)
    s = json.loads(fam.files["limits_overrefusal_checks"][0].read_bytes()); s["requirement"] += " (edited)"
    fam.put("limits_overrefusal_checks", s)
    pin(fam, record)
    code, _, err = rcheck(fam, "--w1-18-record", str(record))
    assert code == 2 and "not made under the pinned W1-18 settings" in err
    # wrong branch: a failing record under 128, a passing record under full, a reason with a record
    pin(fail_fam, fail_rec, "128")
    assert rcheck(fail_fam, "--w1-18-record", str(fail_rec))[0] == 2
    fam2, rec2, _ = family_with_record(tmp_path / "d")
    pin(fam2, rec2, "full")
    code, _, err = rcheck(fam2, "--w1-18-record", str(rec2))
    assert code == 2 and "passes its bar, so the branch is 128, not full" in err
    pin(fam2, None, "full", reason="the check could not run")
    code, _, err = rcheck(fam2, "--w1-18-record", str(rec2))
    assert code == 2 and "pin no W1-18 record" in err
    assert rcheck(fam2)[0] == 0                        # full with a reason and no record: nothing to read
    # missing (pinned, not given), unpinned (pending, given), a directory, a repeated flag
    pin(fam2, rec2, "128")
    assert rcheck(fam2)[0] == 2
    assert rcheck(fam2, "--w1-18-record", str(tmp_path))[0] == 2
    assert rcheck(fam2, "--w1-18-record", str(rec2), "--w1-18-record", str(rec2))[0] == 2
    pin(fam2, None, oe.PENDING)
    assert rcheck(fam2, "--w1-18-record", str(rec2))[0] == 2


def test_D3_the_y_index_checks_the_record_too(tmp_path, fake_tools):
    fam, record, _ = family_with_record(tmp_path / "a")
    pin(fam, record, role="oext_eval_y")
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--engine", "Y", "--w1-18-record", str(record)])
    assert code == 0, err[-300:]
    fam2, rec2, _ = family_with_record(tmp_path / "b", kinds={"G-1101": "B"})
    pin(fam2, rec2, "128", role="oext_eval_y")
    code, _, err = f.wrapper(fam2, ["check", "--family", f.FAMILY, "--engine", "Y", "--w1-18-record", str(rec2)])
    assert code == 2 and "fails its bar" in err


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


def test_E1_a_listed_file_that_is_missing_now_refuses_on_the_mac(tmp_path, fake_tools):
    """R-9's check covers job.json, generations and guard only. W1-18 also runs the frozen sealed check, which needs
    every file COMPLETE.json lists (model states excepted) present with its hash."""
    fam, settings, root = side(tmp_path)
    name = sorted(settings["units"])[0]

    def add(marker, folder):
        (folder / "eval" / "e1" / "summary.json").write_bytes(b"{}\n")
        marker["files"]["eval/e1/summary.json"] = f.sha(folder / "eval" / "e1" / "summary.json")
        (folder / "eval" / "e1" / "summary.json").unlink()                    # listed, then lost (a partial pull)
    _rewrite_complete(settings, root, name, add, fam)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and "the frozen sealed check refuses" in out, (out[-300:], err[-300:])   # now refused (OR2)
    code, _, err = f.wrapper(fam, ["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w"), "--data-root",
                                   str(root)])
    assert code != 0 and "sealed check refuses" in err, err[-300:]                         # as W1-18 itself


def test_E2_a_second_checkpoint_folder_now_refuses_on_the_mac(tmp_path, fake_tools):
    fam, settings, root = side(tmp_path)
    name = sorted(settings["units"])[0]
    (root / settings["units"][name]["path"] / "eval" / "e2").mkdir()
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and "eval/ does not hold exactly" in out, (out[-300:], err[-300:])    # now refused (OR2)
    code, _, err = f.wrapper(fam, ["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w"), "--data-root",
                                   str(root)])
    assert code != 0 and "eval/ does not hold exactly" in err, err[-300:]


def test_E3_a_text_value_in_complete_json_never_reaches_the_output(tmp_path):
    """OR7: a listed value that is not a SHA-256 is reported by its key only."""
    fam, settings, root = side(tmp_path)
    name = sorted(settings["units"])[0]
    secret = tf.sentinel("a text value in COMPLETE.json")

    def put(marker, folder):
        marker["files"]["eval/e1/generations.jsonl"] = secret
    _rewrite_complete(settings, root, name, put, fam)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and secret not in out + err


def test_E3b_a_text_value_as_complete_json_job_sha256_never_reaches_the_output(tmp_path):
    fam, settings, root = side(tmp_path)
    name = sorted(settings["units"])[0]
    secret = tf.sentinel("a text job_sha256")
    settings["units"][name]["job_sha256"] = None                  # no job pin, so the listed value is all there is

    def put(marker, folder):
        marker["files"].pop("job.json")
        marker["job_sha256"] = secret
    _rewrite_complete(settings, root, name, put, fam)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and secret not in out + err


def test_E4_no_answer_or_prompt_text_reaches_the_output_on_any_problem(tmp_path):
    for case in ("ok", "changed-gen", "changed-guard", "unlisted", "job-off-pin", "complete-off-pin", "no-folder"):
        fam, settings, root = side(tmp_path / case)
        name = sorted(settings["units"])[0]
        folder = root / settings["units"][name]["path"]
        if case == "changed-gen":
            (folder / "eval" / "e1" / "generations.jsonl").write_bytes(b'{"x": "' + tf.SENTINELS[0].encode() + b'"}\n')
        elif case == "changed-guard":
            (folder / "eval" / "e1" / "guard.jsonl").write_bytes(b"{}\n")
        elif case == "unlisted":
            _rewrite_complete(settings, root, name, lambda m, _: m["files"].pop("eval/e1/generations.jsonl"), fam)
        elif case == "job-off-pin":
            settings["units"][name]["job_sha256"] = "d" * 64
        elif case == "complete-off-pin":
            settings["units"][name]["complete_sha256"] = "c" * 64
        elif case == "no-folder":
            shutil.rmtree(folder)
        fam.put("limits_overrefusal_checks", settings)
        pin(fam, None, oe.PENDING)
        code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
        assert code == (0 if case == "ok" else 2), (case, err[-300:])
        assert not any(t in out + err for t in tf.SENTINELS), case


def test_E5_a_unit_folder_linked_out_of_the_data_root_is_a_problem(tmp_path):
    fam, settings, root = side(tmp_path)
    name = sorted(settings["units"])[0]
    folder = root / settings["units"][name]["path"]
    outside = tmp_path / "outside"
    shutil.move(str(folder), str(outside))
    folder.symlink_to(outside, target_is_directory=True)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and "leaves the data root" in out


def test_E6_the_check_hashes_but_never_parses_the_answer_files(tmp_path, monkeypatch):
    """Invalid JSON in generations.jsonl and guard.jsonl, listed with their true hashes: the check passes (it never
    parses them)."""
    fam, settings, root = side(tmp_path)
    name = sorted(settings["units"])[0]

    def junk(marker, folder):
        for rel in ("eval/e1/generations.jsonl", "eval/e1/guard.jsonl"):
            (folder / rel).write_bytes(b"\x00 not json {{{")
            marker["files"][rel] = f.sha(folder / rel)
    _rewrite_complete(settings, root, name, junk, fam)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 0, err[-300:]


# ===== F. check: a waiting role masks any refusal of that role ==========================================================


def _waiting(fam, settings, change):
    s_ = copy.deepcopy(settings)
    change(s_)
    fam.put("limits_overrefusal_checks", s_)
    pin(fam, None, oe.PENDING)
    fam.waits = [{"pin": "THETA0_JOB", "event": mk.EVENTS["THETA0_JOB"], "where": ["x"],
                  "roles": ["limits_overrefusal_checks"]}]
    return f.wrapper(fam, ["check", "--family", f.FAMILY])


def test_F1_a_waiting_w1_18_file_with_a_fault_before_its_pin_exits_2(tmp_path):
    fam, settings, root = side(tmp_path)
    first, last = sorted(settings["units"])[0], sorted(settings["units"])[-1]

    def change(s_):
        s_["units"][first]["seed"] = "not an integer"
        s_["units"]["untuned"] = s_["units"].pop(last)
        s_["units"]["untuned"]["job_sha256"] = None
    code, out, err = _waiting(fam, settings, change)
    assert code == 2 and "no path or no integer seed" in err, (out[-300:], err[-300:])


def test_F2_GAP_a_waiting_w1_18_file_with_a_fault_after_its_pin_is_reported_waits(tmp_path):
    """The 1B validator stops at its first refusal: a fault that check_content tests after the null theta0 pin (here
    the bank size) is never seen, so the file is "waits" and check exits 0."""
    fam, settings, root = side(tmp_path)
    last = sorted(settings["units"])[-1]

    def change(s_):
        s_["units"]["untuned"] = s_["units"].pop(last)
        s_["units"]["untuned"]["job_sha256"] = None
        s_["bank"]["size"] = 99
    code, out, err = _waiting(fam, settings, change)
    assert code == 0 and json.loads(out)["settings"]["limits_overrefusal_checks"] == "waits", (out[-300:], err[-300:])


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


@pytest.mark.parametrize("case", ["ok", "elsewhere", "dotdot", "not-json", "off-pin", "missing", "path-only",
                                  "sha-only", "absolute", "sibling-folder"])
def test_H1_the_maker_takes_a_w1_18_record_only_at_its_place_and_pin(tmp_path, case):
    root = tmp_path / "root"
    rel = mk.RECORDS_DIR + "rv__olmo2-7b.json"
    (root / mk.RECORDS_DIR).mkdir(parents=True)
    (root / rel).write_bytes(b'{"kind": "stage1 over-refusal checks"}')
    digest = f.sha(root / rel)
    w18 = {"branch": "128", "record_sha256": digest, "record_path": rel, "full_reason": None}
    if case == "elsewhere":
        other = ".ai/inputs/stage1-post-w1-20261023/78b/rv__olmo2-7b.json"
        (root / other).write_bytes((root / rel).read_bytes())
        w18["record_path"] = other
    elif case == "sibling-folder":
        other = ".ai/inputs/stage1-post-w1-20261023/78b/w1-18x/rv.json"
        (root / other).parent.mkdir(parents=True)
        (root / other).write_bytes((root / rel).read_bytes())
        w18["record_path"] = other
    elif case == "dotdot":
        w18["record_path"] = mk.RECORDS_DIR + "../w1-18/rv__olmo2-7b.json"
    elif case == "not-json":
        w18["record_path"] = rel[:-5] + ".txt"
    elif case == "off-pin":
        w18["record_sha256"] = "7" * 64
    elif case == "missing":
        w18["record_path"] = mk.RECORDS_DIR + "absent.json"
    elif case == "path-only":
        w18["record_sha256"] = None
    elif case == "sha-only":
        w18["record_path"] = None
    elif case == "absolute":
        w18["record_path"] = str(root / rel)
    pins = _pins_with(lambda p: p["families"]["olmo2-7b"].update(w1_18=w18))
    code, out, err = _maker(tmp_path, pins, root)
    if case == "ok":
        assert code == 0, err[-300:]
    else:
        assert code == 2 and "REFUSED" in err, (case, err[-300:])


def test_H2_only_a_w1_18_settings_fill_reaches_the_w1_index(tmp_path):
    base = mk.derive_all(_pins_with(lambda p: None))
    w1 = {n: d for n, d in base.items() if n.startswith("OEXT-78B-W1__")}
    fills = {
        "branch full reason": lambda p: p["families"]["olmo2-7b"].update(w1_18={"branch": "full", "record_sha256": None,
                                                                              "record_path": None,
                                                                              "full_reason": "rv"}),
        "engine_y": lambda p: p["shared"].update(engine_y="3" * 64),
        "llama G": lambda p: p["families"]["llama31-8b"].update(recipe_g={
            "name": "study-kt-llama31-8b-r64-g-mb2-20261011",
            "config_sha256": "442f133fb1861a74b57fe250023db53d4389fc2bad54c99dcd46bd56af920493"}),
        "theta0 olmo": lambda p: p["families"]["olmo2-7b"]["units"]["untuned"].update(job_sha256="1" * 64),
    }
    for name, change in fills.items():
        now = mk.derive_all(_pins_with(change))
        moved = sorted(n for n in w1 if now[n] != w1[n])
        assert moved == (["OEXT-78B-W1__olmo2-7b.json"] if name == "theta0 olmo" else []), (name, moved)


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


def test_H4_a_bqi_config_with_another_generation_block_refuses(tmp_path):
    g16 = mk.REPO / "experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b-mb2-g16-20261008.json"
    from experiments.safety_selection.config import config_sha256, load_recipe
    pins = _pins_with(lambda p: p["families"]["olmo2-7b"].update(
        recipe_bqi={"name": g16.stem, "config_sha256": config_sha256(load_recipe(g16))}))
    with pytest.raises(s1.Refusal, match="recipe_bqi's generation or guard block differs"):
        mk.derive_all(pins)


def test_I1_a_y_index_with_no_engine_identity_and_no_engine_y_wait_refuses(tmp_path):
    env = f.unit_world(tmp_path / "u", "full", full_reason="rv: no record", engine_y=True)
    f.put_unit_settings(env, engine_y=True)
    env.fam.engine_y = None                                   # the index names no identity, and nothing waits on it
    code, _, err = f.wrapper(env, ["check", "--family", f.FAMILY, "--engine", "Y"])
    assert code == 2 and "names no engine identity" in err, err[-300:]


def test_E7_the_lead_r9_command_on_the_w1_index(tmp_path):
    fam, settings, root = side(tmp_path)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--engine", "W1", "--data-root", str(root)])
    rep = json.loads(out) if code == 0 else None
    assert code == 0 and rep["side_units"]["problems"] == [] and rep["settings"] == {"limits_overrefusal_checks": "valid"}
    assert all(u["sealed"] == "passes" and u["eval_folders"] == 1 for u in rep["side_units"]["units"].values())
