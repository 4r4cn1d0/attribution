"""G1 of block B's pre-flight, the engine-Y O-ext re-pin (addendum section 34 point 3; section 11 point 7; section 15
point 1): B+Qi's O-ext step runs on engine Y. Engine X's O-ext files stay byte-identical (block A's O-ext outputs name
them by SHA-256); the engine-Y side is three new files: oext_unit_y.py (oext_unit.py with only its settings pins
changed), settings/oext_unit_y.json (engine Y, B+Qi's config 37942cf5 only) and settings/oext_eval_y.json (engine Y,
otherwise engine X's O-ext settings). The kit packs them on engine Y's pack at the paths its job runner calls and
seals (runkit/stage1-olmo, stage1_rules.S1_OEXT_Y; tested there). Expected values are written by hand. The engine-Y
pass runs in a fresh interpreter on engine Y's own code (STAGE1_ENGINE_Y_TREE, default <repo>/tmp/engine-y-34bfd288)
on ENGINEERING FIXTURES only; none of its numbers is a scientific result."""

from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("torch")

import oext_unit_fixtures as uf  # noqa: E402

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

PKG = uf.PKG_DIR
ou, oe = uf.ou, uf.oe
ouy = importlib.import_module(f"scripts.{PKG.name}.oext_unit_y")
X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
Y = "34bfd28879fdefc5d6605cb73a707d1edd2ec5d102b4b86c0026bc6ac36969f6"
BQI = "37942cf565a7de7d4f68260ec4f769818fb03af9978b0f0356dc90851aa7644c"         # plan.json recipes_y, engine Y
X_FILES = {"oext_unit.py": "ae2fb5b5fbea36cbd2b27c4eaa20f10504b9856961ae8ee100311c923876b8e3",          # block A's
           "settings/oext_unit.json": "3959eae7264f56f613f5d7cd54e69081d8985ef7cbce2962243f6685e3581189",
           "oext_eval.py": "8c4290921f32a5b4596a0bc40235cc5cf1185f73eaabeaa625c43bd19ba77719",
           "settings/oext_eval.json": "2ad9893849248a8fb61d04cf7badbd7fb398915020f196904849d500df08f5a5"}
Y_FILES = {"oext_unit_y.py": "978561ce0269756bbdf921580bb1e8c15592041583ab5d899912c910eb4753de",
           "settings/oext_unit_y.json": "80d08721284bbe94661d6fe2cdc58be259db8df66dc681403d7473155c715298",
           "settings/oext_eval_y.json": "80469a8f728d15192c360f26640c17b7ba652fbd969cfa45f43113c1defd76f0"}
Y_UNIT, Y_EVAL = PKG / "settings" / "oext_unit_y.json", PKG / "settings" / "oext_eval_y.json"
CONFIGS = Path(uf._engine.__file__).resolve().parent / "configs"
RECIPES = {"B": "study-kt-olmo2-1b-r64-b-mb4-20261008", "S": "study-kt-olmo2-1b-r64-b-mb4-gateb-20261008",
           "G": "study-kt-olmo2-1b-r64-g-mb4-20261008"}
Y_TREE = Path(os.environ.get("STAGE1_ENGINE_Y_TREE", str(uf.ENGINE_ROOT / "tmp" / "engine-y-34bfd288")))
HEAD_FIND = ('"""The O-ext unit runner: the pod-side command that runs the 500-prompt O-ext pass (over-refusal on '
             'harmless\n')


def _on_engine(monkeypatch, identity: str) -> None:
    real = s1.code_identity
    monkeypatch.setattr(s1, "code_identity", lambda: {**real(), "sha256": identity})


def _flat(obj, prefix: str = "") -> dict:
    if isinstance(obj, dict) and obj:
        return {k: v for key, value in obj.items() for k, v in _flat(value, f"{prefix}{key}.").items()}
    return {prefix[:-1]: obj}


# ----- 1. engine X's files are block A's bytes; the engine-Y copy is them with only its pins changed -----------------


def test_engine_xs_o_ext_files_are_block_as_bytes_and_their_literals():
    assert {rel: sha256_file(PKG / rel) for rel in X_FILES} == X_FILES
    assert (ou.SETTINGS_SHA256, oe.SETTINGS_SHA256) == (X_FILES["settings/oext_unit.json"],
                                                        X_FILES["settings/oext_eval.json"])
    assert {rel: sha256_file(PKG / rel) for rel in Y_FILES} == Y_FILES
    assert not set(X_FILES.values()) & set(Y_FILES.values())


def test_the_y_copy_is_oext_unit_rebuilt_with_exactly_its_settings_pins_changed():
    x = (PKG / "oext_unit.py").read_text(encoding="utf-8")
    y = (PKG / "oext_unit_y.py").read_text(encoding="utf-8")
    finds = [HEAD_FIND,
             'SETTINGS_SHA256 = "3959eae7264f56f613f5d7cd54e69081d8985ef7cbce2962243f6685e3581189"\n',
             'OEXT_SETTINGS_PATH = "scripts/stage1_s1/settings/oext_eval.json"\n',
             "        oset = oext_settings if oext_settings is not None else oe.load_pinned_settings()\n"]
    head = y[:y.index(HEAD_FIND[3:])]
    replaces = [head + HEAD_FIND[3:],
                'SETTINGS_SHA256 = "80d08721284bbe94661d6fe2cdc58be259db8df66dc681403d7473155c715298"\n',
                'OEXT_SETTINGS_PATH = "scripts/stage1_s1/settings/oext_eval.json"\n'
                'OEXT_SETTINGS_SHA256 = "80469a8f728d15192c360f26640c17b7ba652fbd969cfa45f43113c1defd76f0"   '
                '# engine Y: oext_eval_y.json\n',
                "        oset = oext_settings if oext_settings is not None else \\\n"
                "            oe.load_pinned_settings(expected_sha256=OEXT_SETTINGS_SHA256)\n"]
    rebuilt = x
    for find, replace in zip(finds, replaces):
        assert x.count(find) == 1, find
        rebuilt = rebuilt.replace(find, replace)
    assert rebuilt == y and y != x
    assert head.startswith('"""ENGINE Y COPY (gap G1') and '"""' not in head[3:] and head.count("\n") == 10
    assert (ouy.SETTINGS_SHA256, ouy.OEXT_SETTINGS_SHA256) == (Y_FILES["settings/oext_unit_y.json"],
                                                               Y_FILES["settings/oext_eval_y.json"])
    assert (ouy.SETTINGS_PATH, ouy.OWNER, ouy.OEXT_SETTINGS_PATH) == (ou.SETTINGS_PATH, ou.OWNER, ou.OEXT_SETTINGS_PATH)
    assert ouy.oe is oe                                          # the one shared O-ext module (engine X's bytes)
    assert uf.parser_shape(ouy.parser()) == uf.parser_shape(ou.parser()) == uf.parser_shape(uf.contract_parser())


# ----- 2. the engine-Y settings -------------------------------------------------------------------------------------


def test_the_y_settings_differ_from_engine_xs_only_in_the_named_fields():
    x_eval, y_eval = (s1.strict_json((PKG / "settings" / n).read_bytes()) for n in ("oext_eval.json", "oext_eval_y.json"))
    x_unit, y_unit = (s1.strict_json((PKG / "settings" / n).read_bytes()) for n in ("oext_unit.json", "oext_unit_y.json"))
    for path, doc in ((Y_EVAL, y_eval), (Y_UNIT, y_unit)):
        assert canonical_json(doc) == path.read_bytes()
    fx, fy = _flat(x_eval), _flat(y_eval)
    assert {k for k in fx.keys() | fy.keys() if fx.get(k) != fy.get(k)} == {"engine_x", "requirement"}
    assert (x_eval["engine_x"], y_eval["engine_x"]) == (X, Y) and y_eval["requirement"].startswith(x_eval["requirement"])
    fx, fy = _flat(x_unit), _flat(y_unit)
    changed = {k for k in fx.keys() | fy.keys() if fx.get(k) != fy.get(k)}
    assert changed == {"engine_x", "oext.settings.sha256", "oext.rule", "recipes.allowed.B", "recipes.allowed.S",
                       "recipes.allowed.G", "recipes.allowed.B+Qi", "recipes.rule", "requirement"}
    assert y_unit["engine_x"] == Y and y_unit["recipes"]["allowed"] == {"B+Qi": BQI}
    assert y_unit["oext"]["settings"] == {"path": "scripts/stage1_s1/settings/oext_eval.json",
                                          "sha256": Y_FILES["settings/oext_eval_y.json"]}
    assert y_unit["oext"]["module_sha256"] == X_FILES["oext_eval.py"] == oe.module_sha256()
    assert (y_unit["recipes"]["generation_sha256"], y_unit["recipes"]["guard_sha256"]) == (
        "5ddced7af22b968ff2c00f641be4d286cb1e1151318cf0dcca502331eb563430",
        "a7f0755b795f0ac42300400227a755f10f7ef690f6977f36bdd5def9a655587a")        # engine X's: one cap, one judge
    assert y_unit["requirement"].startswith(x_unit["requirement"])


def test_the_y_settings_load_on_engine_y_and_refuse_on_engine_x(monkeypatch):
    with pytest.raises(s1.Refusal, match="written for engine 34bfd288"):          # this checkout runs engine X
        ouy.load_pinned_settings(Y_UNIT)
    with pytest.raises(s1.Refusal, match="written for engine 34bfd288"):
        oe.load_pinned_settings(Y_EVAL, ouy.OEXT_SETTINGS_SHA256)
    with pytest.raises(s1.Refusal, match="hash to 80d08721"):                     # engine X's runner, Y's file
        ou.load_pinned_settings(Y_UNIT)
    with pytest.raises(s1.Refusal, match="hash to 3959eae7"):                     # the copy's default path here: X's
        ouy.load_pinned_settings()
    _on_engine(monkeypatch, Y)
    unit = ouy.load_pinned_settings(Y_UNIT)
    oext = oe.load_pinned_settings(Y_EVAL, ouy.OEXT_SETTINGS_SHA256)
    assert (unit.sha256, oext.sha256) == (Y_FILES["settings/oext_unit_y.json"], Y_FILES["settings/oext_eval_y.json"])
    assert unit.doc["oext"]["settings"]["sha256"] == oext.sha256 and oext.doc["cap"]["branch"] == "128"
    assert oext.doc["cap"]["w1_18"]["record_sha256"] == \
        "608cbb94c0060012e4cd0544fb2b926c7e86a37c69dd8f2759d944faa971eb21"        # W1-18's record, as on engine X
    with pytest.raises(s1.Refusal, match="written for engine 472fc7f6"):          # the gap: X's settings on Y
        ou.load_pinned_settings()
    with pytest.raises(s1.Refusal, match="written for engine 472fc7f6"):
        oe.load_pinned_settings()


@pytest.mark.parametrize("name", sorted(RECIPES))
def test_on_engine_y_the_y_settings_refuse_every_engine_x_recipe(monkeypatch, name):
    path = CONFIGS / f"{RECIPES[name]}.json"
    x_unit = ou.load_pinned_settings()                                          # engine X: B, S and G are allowed
    assert ou.check_recipe(path, x_unit)[1] == x_unit.doc["recipes"]["allowed"][name]
    _on_engine(monkeypatch, Y)
    unit = ouy.load_pinned_settings(Y_UNIT)
    with pytest.raises(s1.Refusal, match=r"is not one of the settings' allowed recipes \['B\+Qi'\]"):
        ouy.check_recipe(path, unit)


# ----- 3. the O-ext pass on engine Y's own code (a B+Qi-shaped unit), in a fresh interpreter ------------------------


def _engine_y_folder(base: Path) -> Path:
    """experiments -> engine Y's tree; scripts/stage1 and this package copied (the copy's code under test)."""
    assert (Y_TREE / "experiments" / "safety_selection").is_dir(), f"engine Y's tree (STAGE1_ENGINE_Y_TREE): {Y_TREE}"
    root = base / "engine-y"
    (root / "scripts").mkdir(parents=True)
    (root / "experiments").symlink_to(Y_TREE / "experiments", target_is_directory=True)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "reading", "d1_spool", "d2_pool_pins", "d3_s3_union",
                                    "c3_subsample", "mutation")
    shutil.copytree(Path(s1.__file__).resolve().parent, root / "scripts" / "stage1", ignore=ignore)
    shutil.copytree(PKG, root / "scripts" / PKG.name, ignore=ignore)
    return root


def test_the_y_copy_runs_the_o_ext_pass_on_a_bqi_unit_on_engine_ys_code_and_refuses_an_x_recipe(tmp_path):
    root = _engine_y_folder(tmp_path)
    out = tmp_path / "probe" / "out.json"
    out.parent.mkdir()
    done = subprocess.run([sys.executable, "-B", str(root / "scripts" / PKG.name / "tests" / "oext_unit_y_probe.py"),
                           str(out)], cwd=root, capture_output=True, text=True, timeout=600,
                          env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1",
                               "PYTHONPATH": str(root)})
    assert done.returncode == 0, done.stderr[-3000:]
    got = json.loads(out.read_text())
    assert got["engine"] == Y and got["settings_engine"] == Y and got["oext_settings_engine"] == Y
    assert got["bqi_constrained"] is True and got["bqi_config"] != got["plain_config"]
    bqi = got["bqi"]
    assert bqi["exit"] == 0 and bqi["refused"] is None and bqi["complete"] is True and bqi["printed_ok"] is True
    assert bqi["route"] == "unit_eval" and bqi["code_sha256"] == Y and bqi["recipe_sha256"] == got["bqi_config"]
    assert bqi["settings_sha256"] == got["settings_sha256"] and bqi["oext_settings_sha256"] == got["oext_settings_sha256"]
    assert bqi["oext_module_sha256"] == X_FILES["oext_eval.py"]                 # engine X's O-ext function on Y
    assert bqi["script_sha256"] == bqi["script_file_sha256"] == Y_FILES["oext_unit_y.py"]
    plain = got["plain"]
    assert plain["exit"] == 2 and plain["folder"] is False and plain["stdout"] == ""
    assert f"recipe {got['plain_config'][:16]} is not one of the settings' allowed recipes ['B+Qi']" in plain["refused"]
    assert got["x_settings_on_y"].startswith(f"settings oext_unit: written for engine {X}, this engine is {Y}")
