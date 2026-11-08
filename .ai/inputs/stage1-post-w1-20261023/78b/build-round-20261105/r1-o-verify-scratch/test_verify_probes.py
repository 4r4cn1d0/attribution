"""Verifier probes for R1 Track O (adversarial; ENGINEERING FIXTURES only, the builder's and the 1B fixtures).
Run from WS's root with WS on sys.path (WS is the first argument's folder: set by the VERIFY_WS environment variable).
Each test states the attack it tries. Nothing here edits WS."""

from __future__ import annotations

import copy
import importlib
import json
import os
import sys
from pathlib import Path

WS = Path(os.environ["VERIFY_WS"]).resolve()
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
ORIG_W1 = (w1.SETTINGS_PATH, w1.SETTINGS_SHA256)
TOOLS = {"device": "test", "judge": "a fake judge", "decoder": "a fake decoder"}


def globals_now():
    lej = w.module(w.LEAN_MODULE)
    return (ou.load_pinned_settings, oe.load_pinned_settings, ou.OEXT_SETTINGS_PATH, w1.SETTINGS_PATH,
            w1.SETTINGS_SHA256, lej.SETTINGS_PATH, lej.SETTINGS_SHA256, lej.OEXT_SETTINGS_PATH)


def two_family_index(folder: Path, blocks: dict) -> tuple[Path, str]:
    doc = {"kind": w.INDEX_KIND, "version": 1, "families": blocks}
    path = folder / mk.INDEX_NAME
    return path, f.write(path, doc)


def block(files: dict, manifest: str, branch: str = "pending_w1_18") -> dict:
    return {"branch": branch, "w1_18_record_sha256": None, "manifest_sha256": manifest,
            "files": {r: {"file": p.name, "sha256": h} for r, (p, h) in files.items()}, "waits": []}


@pytest.fixture
def fake_tools(monkeypatch):
    def tools(doc, device, ledger_dir, guard_batch_size=None):
        return tf.fake_judge_records, tf.fake_decode, TOOLS
    monkeypatch.setattr(w1, "real_tools", tools)


# ----- 1. W1-18 for both families in one process (GXB O4; the brief's leak case) ---------------------------------------


def test_w1_18_two_families_in_one_process_each_record_names_its_own_settings(tmp_path, fake_tools):
    before = globals_now()
    sdir = tmp_path / "settings78"
    roots, docs, files = {}, {}, {}
    for fam, kinds in (("olmo2-7b", {"B-1101": "A"}), ("llama31-8b", {"G-1101": "B", "G16-1101": "D"})):
        roots[fam] = tmp_path / f"data-{fam}"
        docs[fam], _, _ = tf.build_checks(roots[fam], kinds)
        path = sdir / mk.file_name("limits_overrefusal_checks", fam)
        files[fam] = {"limits_overrefusal_checks": (path, f.write(path, docs[fam]))}
    blocks = {fam: block(files[fam], docs[fam]["prepared"]["manifest_sha256"]) for fam in files}
    ipath, isha = two_family_index(sdir, blocks)
    records = {}
    with w.patched([(w, "SETTINGS_DIR", sdir), (w, "INDEX_PATH", ipath), (w, "INDEX_SHA256", isha)]):
        for fam in ("olmo2-7b", "llama31-8b"):
            out = tmp_path / f"w-{fam}"
            code, _, err = f.call(w.main, ["w1_18", "--family", fam, "--out", str(out), "--data-root", str(roots[fam])])
            assert code == 0, err[-300:]
            assert (w1.SETTINGS_PATH, w1.SETTINGS_SHA256) == ORIG_W1
            records[fam] = json.loads((out / w1.OUTPUT).read_bytes())
        # the other order, in the same process, and a cross-wired data root (Llama's settings on OLMo's units) refuses
        code, _, err = f.call(w.main, ["w1_18", "--family", "llama31-8b", "--out", str(tmp_path / "x"),
                                       "--data-root", str(roots["olmo2-7b"])])
        assert code == 2 and not (tmp_path / "x").exists()
    for fam in records:
        assert records[fam]["provenance"]["settings_sha256"] == files[fam]["limits_overrefusal_checks"][1]
        assert sorted(records[fam]["units"]) == sorted(docs[fam]["units"])
    assert records["olmo2-7b"]["provenance"]["settings_sha256"] != records["llama31-8b"]["provenance"]["settings_sha256"]
    assert globals_now() == before


# ----- 2. restore on an exception path (not a refusal that returns 2) ------------------------------------------------


def test_w1_18_globals_restored_when_the_1b_main_raises(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("probe: the tools crash")
    monkeypatch.setattr(w1, "real_tools", boom)
    root = tmp_path / "data"
    settings, _, _ = tf.build_checks(root, {"B-1101": "A"})
    fam = f.Family(tmp_path / "fam")
    fam.manifest, fam.branch = settings["prepared"]["manifest_sha256"], oe.PENDING
    fam.put("limits_overrefusal_checks", settings)
    before = globals_now()
    with fam.active():
        with pytest.raises(RuntimeError, match="probe: the tools crash"):
            w.main(["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w"), "--data-root", str(root)])
    assert globals_now() == before


def test_unit_globals_restored_when_argparse_exits_inside_the_call(tmp_path):
    env = f.unit_world(tmp_path / "u", "128")
    f.put_unit_settings(env)
    before = globals_now()
    args = f.unit_args(env, tmp_path / "o", run=env.world.units["evaluated"])
    args[args.index("--checkpoint") + 1] = "e9"                  # passes the wrapper's flag check; argparse exits
    with env.fam.active():
        with pytest.raises(SystemExit):
            w.main(["unit", "--family", f.FAMILY, *args], loaders=uf.loaders())
    assert globals_now() == before and not (tmp_path / "o").exists()


# ----- 3. label lies through the wrapper (GXB O3) ------------------------------------------------------------------


@pytest.mark.parametrize("label", ["scripts/stage1_s1/settings/oext_eval.json",
                                   "scripts/scale78b/settings/oext_eval__llama31-8b.json"])
def test_a_unit_settings_file_naming_another_oext_file_refuses(tmp_path, label):
    """An oext_unit settings file that names the 1B O-ext file (or the other family's) while the run reads the
    family's own file: the wrapper must refuse (the label would be a lie)."""
    env = f.unit_world(tmp_path / "u", "128")
    _, _, doc = f.put_unit_settings(env)
    doc = copy.deepcopy(doc)
    doc["oext"]["settings"]["path"] = label
    env.fam.put("oext_unit", doc)
    code, out, err = f.wrapper(env, ["unit", "--family", f.FAMILY,
                                     *f.unit_args(env, tmp_path / "o", run=env.world.units["evaluated"])],
                               loaders=uf.loaders())
    assert code == 2 and "oext names the O-ext module and its settings file" in err, err[-300:]
    assert not (tmp_path / "o").exists()


# ----- 4. two families' unit runs in one process --------------------------------------------------------------------


def test_unit_two_families_in_one_process_each_job_names_its_own_settings(tmp_path, monkeypatch):
    before = globals_now()
    envs = {}
    orig_w1_doc = f.w1_18_doc
    for fam in ("olmo2-7b", "llama31-8b"):
        env = f.unit_world(tmp_path / fam, "128")
        env.fam.family = fam
        # move the role files under the family's name (the fixture's put uses fam.family)
        env.fam.files = {}
        # distinct W1-18 settings per family, so every per-family hash differs
        monkeypatch.setattr(f, "w1_18_doc", lambda cut=f.CUT, _fam=fam: {**orig_w1_doc(cut), "requirement": f"probe {_fam}"})
        inp = f.oext_inputs(tmp_path / f"{fam}-in", env.fam, branch="128")
        env.inp = inp
        env.unit_path, env.unit_sha, env.unit_doc = f.put_unit_settings(env)
        envs[fam] = env
    sdirs = {e.fam.dir for e in envs.values()}
    assert len(sdirs) == 2
    # one settings folder for both families: copy each family's files into one folder
    sdir = tmp_path / "settings78"
    sdir.mkdir()
    blocks = {}
    for fam, env in envs.items():
        files = {}
        for role, (p, h) in env.fam.files.items():
            q = sdir / p.name
            q.write_bytes(p.read_bytes())
            files[role] = (q, h)
        blocks[fam] = block(files, env.world.manifest, "128")
    # the O-ext path labels in the copied unit settings name the per-env folder; rewrite them to the shared folder
    for fam, env in envs.items():
        doc = json.loads((sdir / mk.file_name("oext_unit", fam)).read_bytes())
        doc["oext"]["settings"]["path"] = str((sdir / mk.file_name("oext_eval", fam)).resolve())
        h = f.write(sdir / mk.file_name("oext_unit", fam), doc)
        blocks[fam]["files"]["oext_unit"]["sha256"] = h
        env.unit_sha = h
    ipath, isha = two_family_index(sdir, blocks)
    jobs = {}
    with w.patched([(w, "SETTINGS_DIR", sdir), (w, "INDEX_PATH", ipath), (w, "INDEX_SHA256", isha)]):
        for fam, env in envs.items():
            out = tmp_path / f"out-{fam}"
            code, _, err = f.call(w.main, ["unit", "--family", fam,
                                           *f.unit_args(env, out, run=env.world.units["evaluated"])],
                                  loaders=uf.loaders())
            assert code == 0, err[-400:]
            jobs[fam] = json.loads((out / "job.json").read_bytes())
            assert globals_now() == before
    for fam, env in envs.items():
        assert jobs[fam]["settings_sha256"] == env.unit_sha
        assert jobs[fam]["oext"]["settings_sha256"] == env.inp.eval_sha
        assert jobs[fam]["oext"]["w1_18_record_sha256"] == env.inp.w1_18_sha256
    for key in ("settings_sha256",):
        assert jobs["olmo2-7b"][key] != jobs["llama31-8b"][key]
    for key in ("settings_sha256", "w1_18_record_sha256"):
        assert jobs["olmo2-7b"]["oext"][key] != jobs["llama31-8b"]["oext"][key]


# ----- 5. wrong-family, stale and other-branch W1-18 records (DESO item 9; oext_eval.py:359-385) ----------------------


@pytest.mark.parametrize("case", ["other_family_record_pinned", "stale_record_pinned", "branch_disagrees"])
def test_a_pinned_but_wrong_w1_18_record_is_refused_by_the_true_path(tmp_path, case):
    """The lead pins a record by mistake: its hash matches the family's pin, so the wrapper's flag check passes; the
    unchanged oext_eval must refuse it (provenance or verdict), before any folder."""
    env = f.unit_world(tmp_path / "u", "128")
    w_path, w_sha = env.fam.files["limits_overrefusal_checks"]
    if case == "other_family_record_pinned":
        rec, rec_sha = ofx.w1_18_record(tmp_path / "rec", passed=True, cut=f.CUT, settings_sha256="d" * 64)
        branch = "128"
    elif case == "stale_record_pinned":                      # made under an older W1-18 settings file of the family
        rec, rec_sha = ofx.w1_18_record(tmp_path / "rec", passed=True, cut=f.CUT,
                                        settings_sha256=s1.sha256_bytes(w_path.read_bytes() + b"\n"))
        branch = "128"
    else:                                                    # a failing record pinned under Branch 128
        rec, rec_sha = ofx.w1_18_record(tmp_path / "rec", passed=False, cut=f.CUT, settings_sha256=w_sha)
        branch = "128"
    doc = f.eval_doc(branch=branch, record_sha256=env.inp.record and s1.sha256_bytes(env.inp.record.read_bytes()),
                     w1_settings_sha256=w_sha, w1_record_sha256=rec_sha)
    e_path, e_sha = env.fam.put("oext_eval", doc)
    env.inp.w1_18, env.inp.w1_18_sha256, env.inp.eval_doc, env.inp.eval_sha = rec, rec_sha, doc, e_sha
    f.put_unit_settings(env)
    code, out, err = f.wrapper(env, ["unit", "--family", f.FAMILY,
                                     *f.unit_args(env, tmp_path / "o", run=env.world.units["evaluated"])],
                               loaders=uf.loaders())
    assert code == 2, (code, err[-300:])
    needle = {"other_family_record_pinned": "not made under the pinned W1-18 settings",
              "stale_record_pinned": "not made under the pinned W1-18 settings",
              "branch_disagrees": "so the branch is full, not 128"}[case]
    assert needle in err, err[-300:]
    assert not (tmp_path / "o").exists()


# ----- 6. flag-check edges -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("extra,needle", [
    (["--w1-18-rec", "x"], "--w1-18-rec is not a full flag name"),
    (["--dev100-sourc", "x"], "--dev100-sourc is not a full flag name"),
    (["--w1-18-record", "a", "--w1-18-record", "b"], "--w1-18-record is given 2 times"),
    (["--prepared=/nonexistent"], "--prepared is given 2 times"),
])
def test_flag_edges_refuse(tmp_path, extra, needle):
    env = f.unit_world(tmp_path / "u", "128")
    f.put_unit_settings(env)
    args = f.unit_args(env, tmp_path / "o", untuned=True, w1_18=False)
    code, out, err = f.wrapper(env, ["unit", "--family", f.FAMILY, *args[:-2], *extra, *args[-2:]])
    assert code == 2 and needle in err, err[-300:]


def test_lean_takes_no_dev100_source(tmp_path):
    env = f.unit_world(tmp_path / "u", "128")
    code, out, err = f.wrapper(env, ["lean", "--family", f.FAMILY, "run", "--dev100-source", "x", "--out", "y"])
    assert code == 2 and "--dev100-source is not a full flag name" in err
