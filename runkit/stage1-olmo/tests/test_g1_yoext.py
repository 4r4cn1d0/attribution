"""G1 of block B's pre-flight, the engine-Y O-ext re-pin (addendum §34 point 3; §11 point 7, §15 point 1; runbook §0
G1), on CPU, without RunPod, Hugging Face or GitHub: B+Qi's O-ext step runs on engine Y. pack_setup.py packs the O-ext
package on engine Y's pack at the paths the job runner calls and seals (stage1_rules.S1_OEXT_Y_SHARED at their S1_CODE
pins; stage1_rules.S1_OEXT_Y from the engine-Y files of the S1 package), S1_CODE and every X-side file stay as they
were, and check-plan passes a B+Qi host on a Y pack (it refused before). Expected values are written by hand; the pack
tests use the synthetic checkout of test_stage1_runner.py, and the real-pin tests read this repository's files and
engine Y's frozen tree (STAGE1_ENGINE_Y_TREE) only, never tmp/ data."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import test_stage1_runner as rn
from test_stage1_runner import kit  # noqa: F401 - the kit fixture (a copy of the kit and a module loader)

KIT, REPO, WS_Y = rn.KIT, rn.REPO, rn.WS_Y
X, Y, BQI_PATH, REC = rn.X, rn.Y, rn.BQI, rn.REC
BQI = "37942cf565a7de7d4f68260ec4f769818fb03af9978b0f0356dc90851aa7644c"      # B+Qi's config (plan.json recipes_y)
sha, write = rn.sha, rn.write
O_EXT_PATHS = {"scripts/stage1_s1/__init__.py", "scripts/stage1_s1/oext_eval.py", "scripts/stage1_s1/oext_unit.py",
               "scripts/stage1_s1/settings/oext_unit.json", "scripts/stage1_s1/settings/oext_eval.json"}
Y_SOURCES = {"scripts/stage1_s1/oext_unit.py": ("scripts/stage1_s1/oext_unit_y.py",
                                                "978561ce0269756bbdf921580bb1e8c15592041583ab5d899912c910eb4753de"),
             "scripts/stage1_s1/settings/oext_unit.json": (
                 "scripts/stage1_s1/settings/oext_unit_y.json",
                 "80d08721284bbe94661d6fe2cdc58be259db8df66dc681403d7473155c715298"),
             "scripts/stage1_s1/settings/oext_eval.json": (
                 "scripts/stage1_s1/settings/oext_eval_y.json",
                 "80469a8f728d15192c360f26640c17b7ba652fbd969cfa45f43113c1defd76f0")}
X_O_EXT = {"scripts/stage1_s1/__init__.py": "818919ca18627b7169d80c2a6f6c24149f6e1c529bff9d37a5ddee2122bddd32",
           "scripts/stage1_s1/oext_eval.py": "8c4290921f32a5b4596a0bc40235cc5cf1185f73eaabeaa625c43bd19ba77719",
           "scripts/stage1_s1/oext_unit.py": "ae2fb5b5fbea36cbd2b27c4eaa20f10504b9856961ae8ee100311c923876b8e3",
           "scripts/stage1_s1/settings/oext_unit.json":
               "3959eae7264f56f613f5d7cd54e69081d8985ef7cbce2962243f6685e3581189",
           "scripts/stage1_s1/settings/oext_eval.json":
               "2ad9893849248a8fb61d04cf7badbd7fb398915020f196904849d500df08f5a5"}       # block A's bytes


KIT_MODULES = ("stage1_rules", "probes", "secret_scan")


def _real(name: str):
    """A module of the real kit (ROOT = this repository), loaded by path; sys.path is restored afterwards."""
    saved = list(sys.path)
    sys.path.insert(0, str(KIT))
    try:
        spec = importlib.util.spec_from_file_location(f"g1_{Path(name).stem}", KIT / name)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved


@pytest.fixture
def real():
    """The real kit's pack_setup and job runner, sharing one stage1_rules module (the one pack_setup reads)."""
    for m in KIT_MODULES:
        sys.modules.pop(m, None)
    pack = _real("pack_setup.py")
    runner = _real("setup/job_runner_stage1.py")
    assert runner.rules is pack.rules
    yield {"rules": pack.rules, "pack": pack, "runner": runner}
    for m in KIT_MODULES:
        sys.modules.pop(m, None)


def _literal(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return next(n.value.value for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))


# ===== 1. the pins: this repository's engine-Y files, the runner's paths, S1_CODE unchanged =============================

def test_the_y_pins_name_this_repositorys_engine_y_files_at_the_runners_o_ext_paths(real):
    r, jr = real["rules"], real["runner"]
    assert {rel: (src["path"], src["sha256"]) for rel, src in r.S1_OEXT_Y.items()} == Y_SOURCES
    assert r.S1_OEXT_Y_SHARED == ("scripts/stage1_s1/__init__.py", "scripts/stage1_s1/oext_eval.py")
    for rel, (src, pin) in Y_SOURCES.items():
        assert sha(REPO / src) == pin and src != rel and src.startswith("scripts/stage1_s1/"), rel
    # every file an O-ext step calls or seals (the runner's own names) is on the Y pack, and nothing else of the package
    assert set(r.S1_OEXT_Y) | set(r.S1_OEXT_Y_SHARED) == O_EXT_PATHS == {
        jr.OEXT_UNIT_SCRIPT, jr.OEXT_UNIT_SETTINGS, jr.OEXT_MODULE, "scripts/stage1_s1/settings/oext_eval.json",
        "scripts/stage1_s1/__init__.py"}
    # S1_CODE (engine X's pack, block A's O-ext outputs) is unchanged: the X-side O-ext files are block A's bytes
    assert len(r.S1_CODE) == 11 and r.S1_COMMIT == "3ea5ae1"
    assert {rel: r.S1_CODE[rel] for rel in X_O_EXT} == X_O_EXT == {rel: sha(REPO / rel) for rel in X_O_EXT}
    assert not set(X_O_EXT.values()) & {pin for _, pin in Y_SOURCES.values()}


def test_the_y_copy_and_settings_pin_each_other_and_engine_y(real):
    r = real["rules"]
    unit_y, eval_y = (REPO / Y_SOURCES[k][0] for k in ("scripts/stage1_s1/settings/oext_unit.json",
                                                       "scripts/stage1_s1/settings/oext_eval.json"))
    copy = REPO / Y_SOURCES["scripts/stage1_s1/oext_unit.py"][0]
    assert _literal(copy, "SETTINGS_SHA256") == sha(unit_y) and _literal(copy, "OEXT_SETTINGS_SHA256") == sha(eval_y)
    assert _literal(REPO / "scripts/stage1_s1/oext_unit.py", "SETTINGS_SHA256") == \
        X_O_EXT["scripts/stage1_s1/settings/oext_unit.json"]                     # engine X's runner keeps its pin
    u, e = json.loads(unit_y.read_text()), json.loads(eval_y.read_text())
    assert u["engine_x"] == e["engine_x"] == r.ENGINES["Y"] == Y
    assert u["oext"]["settings"] == {"path": "scripts/stage1_s1/settings/oext_eval.json", "sha256": sha(eval_y)}
    assert u["oext"]["module_sha256"] == r.S1_CODE["scripts/stage1_s1/oext_eval.py"]
    assert u["recipes"]["allowed"] == {"B+Qi": BQI}                          # plan.json recipes_y, by hand
    assert r.RECIPE_NAMES["bqi"] == BQI_PATH and rn.engine_configs(WS_Y, [BQI_PATH]) == {BQI_PATH: BQI}


# ===== 2. pack_setup's own code collection on this repository's files (engine Y and engine X) =========================

def _collect(real, engine: str, code: list | None = None):
    pack = real["pack"]
    p = pack.Packing()
    p.engine = engine
    pack.stage1_code(p, {"code": code or []}, pack.man1_entries())
    return p


def test_the_real_y_pack_code_holds_the_o_ext_package_whose_settings_pin_engine_y(real):
    r, pack = real["rules"], real["pack"]
    p = _collect(real, "Y")
    assert p.bad == []
    s1 = {n: p.pins[n] for n in p.files if n.startswith("scripts/stage1_s1/")}
    assert s1 == {**{rel: X_O_EXT[rel] for rel in r.S1_OEXT_Y_SHARED}, **{rel: pin for rel, (_, pin) in Y_SOURCES.items()}}
    assert {n: str(p.files[n].relative_to(REPO)) for n in Y_SOURCES} == {n: src for n, (src, _) in Y_SOURCES.items()}
    pack.s1_settings_engine(p, "Y")
    assert p.bad == []
    x = _collect(real, "X")                                         # engine X's pack: S1_CODE exactly, as before G1
    assert x.bad == [] and {n: x.pins[n] for n in x.files if n.startswith("scripts/stage1_s1/") and
                            n not in r.D2_CODE} == r.S1_CODE
    pack.s1_settings_engine(x, "X")
    assert x.bad == []


def test_on_engine_y_engine_xs_o_ext_files_refuse_the_pack(real, monkeypatch):
    """The pre-flight's measurement: engine X's O-ext settings at the runner's paths on Y are not re-pinned on engine
    Y; and a lead's code entry naming engine X's runner on Y meets the Y copy's pin (two pins)."""
    r, pack = real["rules"], real["pack"]
    monkeypatch.setattr(r, "S1_OEXT_Y", {rel: {"path": rel, "sha256": X_O_EXT[rel]} for rel in r.S1_OEXT_Y})
    p = _collect(real, "Y")
    assert p.bad == []
    pack.s1_settings_engine(p, "Y")
    assert sorted(p.bad) == ["scripts/stage1_s1/settings/oext_eval.json (not re-pinned on engine Y; addendum §11 point 7)",
                             "scripts/stage1_s1/settings/oext_unit.json (not re-pinned on engine Y; addendum §11 point 7)"]
    monkeypatch.undo()
    entry = {"path": "scripts/stage1_s1/oext_unit.py", "sha256": X_O_EXT["scripts/stage1_s1/oext_unit.py"]}
    p = _collect(real, "Y", [entry])
    assert p.bad == ["scripts/stage1_s1/oext_unit.py (two pins)"]
    p = _collect(real, "Y", [{"path": "scripts/stage1_s1/oext_unit_y.py", "sha256": Y_SOURCES[
        "scripts/stage1_s1/oext_unit.py"][1]}])                    # the copy under its own name: not a kit pin
    assert p.bad == ["scripts/stage1_s1/oext_unit_y.py (an S1 package file must be its stage1_rules pin at main 3ea5ae1)"]


def _bundle(real, root: Path, pack_files: dict) -> Path:
    """The code of a Y pack in a folder: engine Y's engine files (pack_setup.engine_files of the frozen tree) and every
    packed scripts/ file at its bundle path (the S1 files at the runner's paths)."""
    assert WS_Y.is_dir(), "engine Y's tree (STAGE1_ENGINE_Y_TREE)"
    files = real["pack"].engine_files(WS_Y)
    files.update({n: f for n, f in pack_files.items() if n.startswith("scripts/")})
    assert files[BQI_PATH] == WS_Y / BQI_PATH and files[REC] == WS_Y / REC        # the recipes, Y's tree
    for name, src in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, root / name)
    return root


PROBE = """
import json, sys
import scripts.stage1_s1.oext_unit as ou
from experiments.safety_selection.common import code_identity
out = {"engine": code_identity()["sha256"], "script": ou.script_sha256()}
try:
    s = ou.load_pinned_settings()
    o = ou.oe.load_pinned_settings(expected_sha256=getattr(ou, "OEXT_SETTINGS_SHA256", None))
    out.update(settings=s.sha256, oext_settings=o.sha256, branch=o.doc["cap"]["branch"], module=ou.oe.module_sha256(),
               allowed=sorted(s.doc["recipes"]["allowed"]), bqi=ou.check_recipe(sys.argv[1], s)[1])
    try:
        ou.check_recipe(sys.argv[2], s)
        out["rec"] = "accepted"
    except ou.Refusal as exc:
        out["rec"] = str(exc)
except ou.Refusal as exc:
    out["refused"] = str(exc)
code = ou.main(["run", "--run", "absent-unit", "--checkpoint", "e1", "--prepared", "absent", "--recipe", sys.argv[1],
                "--oext-bank", "absent-bank.json", "--oext-record", "absent-record.json", "--w1-18-record",
                "absent-w1.json", "--out", "absent-out"])
out["main_exit"] = code
print(json.dumps(out))
"""


def _probe(root: Path) -> tuple[dict, str]:
    done = rn.REAL_RUN([rn.PY, "-B", "-c", PROBE, str(root / BQI_PATH), str(root / REC)], cwd=root, capture_output=True,
                       text=True, timeout=300, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                                                    "PYTHONPATH": str(root)})
    assert done.returncode == 0, done.stderr[-2000:]
    return json.loads(done.stdout.strip().splitlines()[-1]), done.stderr


def test_the_real_y_pack_code_runs_the_o_ext_runner_on_engine_y_and_the_x_files_did_not(real, monkeypatch, tmp_path):
    """The Y pack's code (pack_setup's own Y collection of this repository's files, engine Y's frozen engine files) in
    a fresh interpreter: the runner the job runner calls loads its pinned engine-Y settings by default, accepts B+Qi's
    config by engine Y's code and refuses REC, and main gets past the settings to the inputs (exit 2 on an absent
    W1-18 record, the first input oext_eval.prepare reads). Before G1 (engine X's files at those paths): the default settings refuse on engine Y."""
    r = real["rules"]
    p = _collect(real, "Y")
    assert p.bad == []
    got, stderr = _probe(_bundle(real, tmp_path / "y-pack", p.files))
    assert got["engine"] == Y and got["script"] == Y_SOURCES["scripts/stage1_s1/oext_unit.py"][1]
    assert (got["settings"], got["oext_settings"]) == (Y_SOURCES["scripts/stage1_s1/settings/oext_unit.json"][1],
                                                       Y_SOURCES["scripts/stage1_s1/settings/oext_eval.json"][1])
    assert got["branch"] == "128" and got["module"] == X_O_EXT["scripts/stage1_s1/oext_eval.py"]
    assert got["allowed"] == ["B+Qi"] and got["bqi"] == BQI
    assert got["rec"] == "recipe 9e9bde6f2f328760 is not one of the settings' allowed recipes ['B+Qi']"
    assert got["main_exit"] == 2
    refused = json.loads(stderr)["refused"]                        # past both settings loads: the absent inputs
    assert refused == "Refusal: W1-18's record cannot be read"
    monkeypatch.setattr(r, "S1_OEXT_Y", {rel: {"path": rel, "sha256": X_O_EXT[rel]} for rel in r.S1_OEXT_Y})
    before = _collect(real, "Y")                                   # engine X's files at the runner's paths
    got, _ = _probe(_bundle(real, tmp_path / "x-files", before.files))
    assert got["engine"] == Y and got["script"] == X_O_EXT["scripts/stage1_s1/oext_unit.py"]
    assert got["refused"] == f"settings oext_unit: written for engine {X}, this engine is {Y}"


# ===== 3. the packer and check-plan on a synthetic checkout =================================================================

def _oext_inputs(repo) -> list[dict]:
    out = []
    for name, rel in (("oext_bank", "tmp/oext/oext_bank.json"), ("oext_record", "tmp/oext/oext_record.json"),
                      ("w1_18_record", "tmp/w1-18/overrefusal_checks.json")):
        f = write(repo.repo / rel, {"name": name, "synthetic": True})
        out.append({"name": name, "path": rel, "sha256": sha(f)})
    return out


def _bqi_host(kit, pack_dir: Path, seeds=(1102, 1103, 1104)):
    """orchestrate on a plan with one B+Qi host (three ref_train jobs on engine Y, Branch 128) bound to the pack."""
    o = kit("orchestrate.py")
    r = o.rules
    jobs = [rn.job(r, "ref_train", "bqi", s, engine="Y", recipe="bqi", branch="128") for s in seeds]
    h = rn.host_record(r, jobs, "Y", block="B")
    h["sealed_files_sha256"] = json.loads((pack_dir / "setup-receipt.json").read_text())["sealed_files_sha256"]
    write(kit.root / "plan.json", {"hosts": {"b-12": h}, "records": {"branch": {"branch": "128"}, "certification": None},
                                   "reference": {"fields": {"f": 1}, "bootstrap": {}, "guard": None}})
    return o


def test_check_plan_passes_a_bqi_host_on_the_y_pack_and_refused_it_without_the_o_ext_package(kit, monkeypatch):
    repo = rn.Repo(kit, monkeypatch)
    tree = repo.y_tree()
    args = repo.inputs("Y", extra=_oext_inputs(repo))
    repo.pack.main(["Y", "--y-tree", str(tree), *args])
    packed = kit.root / "setup" / "packed-stage1-Y"
    doc = json.loads((packed / "sealed-files.json").read_text())
    assert {n for n in doc["files"] if n.startswith("scripts/stage1_s1/")} == O_EXT_PATHS
    assert doc["files"]["scripts/stage1_s1/oext_unit.py"] == sha(repo.repo / "scripts/stage1_s1/oext_unit_y.py")
    assert doc["files"]["scripts/stage1_s1/settings/oext_unit.json"] == \
        sha(repo.repo / "scripts/stage1_s1/settings/oext_unit_y.json")
    assert {"oext_bank", "oext_record", "w1_18_record"} <= set(doc["inputs"])
    o = _bqi_host(kit, packed)
    assert o.check_plan("b-12") == {"host": "b-12", "jobs": 3, "ok": True}
    # before G1: the same pack without the O-ext package (the kit packed it on engine X only)
    shutil.move(str(packed), str(kit.root / "setup" / "packed-stage1-Y.g1"))
    monkeypatch.setattr(repo.rules, "S1_OEXT_Y", {})
    monkeypatch.setattr(repo.rules, "S1_OEXT_Y_SHARED", ())
    repo.pack.main(["Y", "--y-tree", str(tree), *args])
    o = _bqi_host(kit, packed)
    with pytest.raises(SystemExit, match=re.escape(
            "job 0 (ref_train): 4 file(s) not packed: ['scripts/stage1_s1/oext_unit.py', "
            "'scripts/stage1_s1/settings/oext_unit.json', 'scripts/stage1_s1/oext_eval.py']")):
        o.check_plan("b-12")


@pytest.mark.parametrize("rel", sorted(Y_SOURCES))
def test_an_engine_y_o_ext_file_whose_bytes_differ_refuses_the_y_pack(kit, monkeypatch, rel):
    """One changed byte in an engine-Y source refuses the Y pack before anything is written, naming the runner's path
    (a settings file keeps valid JSON and its engine-Y pin, so only the pin check can refuse it)."""
    repo = rn.Repo(kit, monkeypatch)
    tree = repo.y_tree()
    f = repo.repo / repo.rules.S1_OEXT_Y[rel]["path"]
    data = f.read_bytes()
    if rel.endswith(".json"):
        i = data.index(b'"name": "') + len(b'"name": "')
        changed = data[:i] + bytes([data[i] ^ 0x01]) + data[i + 1:]
        assert json.loads(changed)["engine_x"] == Y and changed != data
    else:
        changed = data[:-1] + bytes([data[-1] ^ 0x01])
    f.write_bytes(changed)
    with pytest.raises(SystemExit, match=re.escape(f"'{rel}'")):
        repo.pack.main(["Y", "--y-tree", str(tree), *repo.inputs("Y")])
    assert not (kit.root / "setup" / "packed-stage1-Y").exists()


def test_an_engine_y_settings_file_that_pins_engine_x_refuses_the_y_pack(kit, monkeypatch):
    repo = rn.Repo(kit, monkeypatch)
    tree = repo.y_tree()
    rel = "scripts/stage1_s1/settings/oext_unit.json"
    src = repo.rules.S1_OEXT_Y[rel]["path"]
    monkeypatch.setitem(repo.rules.S1_OEXT_Y, rel, {"path": src, "sha256": sha(write(repo.repo / src,
                                                                                      {"name": src, "engine_x": X}))})
    with pytest.raises(SystemExit, match=re.escape(f"{rel} (not re-pinned on engine Y; addendum §11 point 7)")):
        repo.pack.main(["Y", "--y-tree", str(tree), *repo.inputs("Y")])
    assert not (kit.root / "setup" / "packed-stage1-Y").exists()
