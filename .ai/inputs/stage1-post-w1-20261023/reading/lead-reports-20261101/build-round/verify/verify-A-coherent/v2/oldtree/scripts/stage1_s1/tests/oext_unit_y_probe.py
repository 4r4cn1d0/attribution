"""ENGINEERING FIXTURE probe for test_oext_unit_y.py (G1; addendum section 34 point 3): run in a fresh interpreter whose
``experiments`` package is engine Y's (a folder that links engine Y's tree and holds a copy of scripts/stage1 and of
this package), it builds synthetic dev-evaluated units with engine Y's own run_one, one under a B+Qi-shaped fixture
recipe (train.constrained_sft) and one under the plain fixture recipe, and runs the engine-Y copy of the O-ext unit
runner (oext_unit_y.py) on them with engine-Y settings (oext_unit_y.json and oext_eval_y.json, the fixture's pins put
in). It writes OUT.json with exit codes, refusal texts, ids and hashes only. Synthetic only: nothing is downloaded, and
no real record, PHTest text, prepared row or answer is read. None of these numbers is a scientific result.

    python -B scripts/stage1_s1/tests/oext_unit_y_probe.py OUT.json
"""

from __future__ import annotations

import contextlib
import copy
import importlib
import io
import json
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PKG_DIR = TESTS.parent
REPO = PKG_DIR.parents[1]
for entry in (str(REPO), str(TESTS)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from experiments.safety_selection.common import code_identity, read_json, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256, training_identity  # noqa: E402

import oext_fixtures as ofx  # noqa: E402
import oext_unit_fixtures as uf  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

ouy = importlib.import_module(f"scripts.{PKG_DIR.name}.oext_unit_y")
ou, oe = uf.ou, uf.oe
SETTINGS = PKG_DIR / "settings"
QI_BETAS = [[1, 1, 0.5], [2, 5, 2.0], [6, None, 0.1]]       # engine Y's own B+Qi test spec (test_ss_roundy_bqi.py)


def y_doc(name: str) -> dict:
    return s1.strict_json((SETTINGS / name).read_bytes())


def call(args: list[str], settings, oext_settings) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ouy.main(args, loaders=uf.loaders(), settings=settings, oext_settings=oext_settings)
    return code, out.getvalue(), err.getvalue()


def refusal(stderr: str) -> str | None:
    try:
        return json.loads(stderr).get("refused")
    except ValueError:
        return None


def main(out_path: str) -> int:
    from experiments.safety_selection.config import (CONSTRAINED_SFT_NAME, CONSTRAINED_SFT_OBJECTIVE,
                                                     CONSTRAINED_SFT_REFERENCE)

    base = Path(out_path).resolve().parent / "world"
    result: dict = {"engine": code_identity()["sha256"]}
    # the O-ext fixtures start from the engine-Y settings (engine_x is engine Y's identity), not engine X's
    ofx.real_doc = lambda: y_doc("oext_eval_y.json")
    uf.real_doc = lambda: y_doc("oext_unit_y.json")
    bank_dir, _ = uf.fx.prepare_dir_v3(base / "prepared-v3")
    prepared, manifest = uf.fx.prepare_task_dir(base / "prepared-kt", bank_dir)
    plain = uf.recipe()
    bqi = uf.recipe(**{"train.constrained_sft": {
        "name": CONSTRAINED_SFT_NAME, "objective": CONSTRAINED_SFT_OBJECTIVE, "reference": CONSTRAINED_SFT_REFERENCE,
        "beta_by_position": copy.deepcopy(QI_BETAS), "weight_floor": 0.001}})
    files = {}
    for name, rec in (("plain", plain), ("bqi", bqi)):
        files[name] = base / f"recipe-{name}.json"
        files[name].write_bytes(uf.canonical_json(rec))
    units = {"bqi": uf.make_unit(prepared, base / "units" / "1102-a0-e1-bqi", 1102, True, rec=bqi),
             "plain": uf.make_unit(prepared, base / "units" / "1103-a0-e1-plain", 1103, True, rec=plain)}
    inp = ofx.inputs(base / "oext-128", branch="128", cut=uf.CUT, dev=2)
    doc = uf.settings_doc(manifest, inp.settings.sha256, bqi, recipes__allowed={"B+Qi": config_sha256(bqi)})
    settings = ouy.settings_from_doc(doc)
    world = uf.SimpleNamespace(prepared=prepared, oext={"128": inp}, recipe_file=files["bqi"])
    result.update(bqi_config=config_sha256(bqi), plain_config=config_sha256(plain),
                  bqi_constrained=training_identity(bqi) != training_identity(plain),
                  settings_engine=doc["engine_x"], settings_sha256=settings.sha256,
                  oext_settings_engine=inp.settings.doc["engine_x"], oext_settings_sha256=inp.settings.sha256)
    # B+Qi's unit under the engine-Y copy: the O-ext pass runs (route unit_eval) and completes
    out = base / "oext-bqi"
    code, stdout, stderr = call(uf.argv(world, "run", "128", out, run=units["bqi"]), settings, inp.settings)
    job = read_json(out / "job.json") if (out / "job.json").is_file() else {}
    marker = read_json(out / "COMPLETE.json") if (out / "COMPLETE.json").is_file() else {}
    result["bqi"] = {"exit": code, "refused": refusal(stderr), "route": job.get("dev100_route"),
                     "complete": marker.get("complete"), "code_sha256": job.get("code_sha256"),
                     "recipe_sha256": job.get("recipe_sha256"), "settings_sha256": job.get("settings_sha256"),
                     "script_sha256": job.get("script_sha256"), "script_file_sha256": sha256_file(Path(ouy.__file__)),
                     "oext_module_sha256": (job.get("oext") or {}).get("module_sha256"),
                     "oext_settings_sha256": (job.get("oext") or {}).get("settings_sha256"),
                     "printed_ok": json.loads(stdout).get("ok") if code == 0 else None}
    # the plain fixture recipe (an engine-X-style recipe) is not an allowed recipe on engine Y: refused, no folder
    out = base / "oext-plain"
    code, stdout, stderr = call(uf.argv(world, "run", "128", out, run=units["plain"], recipe_file=files["plain"]),
                                settings, inp.settings)
    result["plain"] = {"exit": code, "refused": refusal(stderr), "folder": out.exists(), "stdout": stdout}
    # engine X's runner settings (engine_x = X) refuse on engine Y: the gap G1 closes
    x_doc = copy.deepcopy(s1.strict_json((SETTINGS / "oext_unit.json").read_bytes()))
    try:
        ou.settings_from_doc(x_doc)
        result["x_settings_on_y"] = "accepted"
    except s1.Refusal as exc:
        result["x_settings_on_y"] = str(exc)
    Path(out_path).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
