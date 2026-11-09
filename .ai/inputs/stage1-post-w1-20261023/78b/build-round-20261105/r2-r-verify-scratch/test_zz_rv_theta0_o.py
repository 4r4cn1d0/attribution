"""R2 Track R verifier, P4 follow-up (scratch only; ENGINEERING FIXTURES): theta0's O-ext pass (`o_only`) through
Track O's `unit` command reads no unit; it takes --untuned and --recipe. A family whose theta0 unit was made under a
recipe that differs from MAIN_F only in train.lr (Llama's c5462c77 case) gets its theta0 O under MAIN_F (accepted);
the theta0 recipe itself is not an allowed recipe (refused)."""

from __future__ import annotations

import json

import pytest

torch = pytest.importorskip("torch")

import oext78_fixtures as f  # noqa: E402

from experiments.safety_selection.common import canonical_json  # noqa: E402

uf = f.uf


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    e = f.unit_world(tmp_path_factory.mktemp("rv-theta0"), "128")
    e.unit_path, e.unit_sha, e.unit_doc = f.put_unit_settings(e)    # recipes.allowed = {the fixture's MAIN analog}
    return e


def test_theta0_o_under_main_f_is_accepted(env, tmp_path):
    code, out, err = f.wrapper(env, ["unit", "--family", f.FAMILY, *f.unit_args(env, tmp_path / "o", untuned=True)],
                               loaders=uf.loaders())
    job = json.loads((tmp_path / "o" / "job.json").read_bytes()) if code == 0 else {}
    print("THETA0-MAIN", code, job.get("dev100_route"), {k: job.get(k) for k in ("dev100_source", "source_complete_sha256", "unit_complete_sha256")}, job.get("recipe_sha256", "")[:12])
    assert code == 0 and job["dev100_route"] == "generated"


def test_theta0_recipe_with_another_lr_is_refused(env, tmp_path):
    other = uf.recipe()
    other["train"]["lr"] = other["train"]["lr"] / 2               # c5462c77 vs 74758af1: only train.lr differs
    path = tmp_path / "theta0-recipe.json"
    path.write_bytes(canonical_json(other))
    args = f.unit_args(env, tmp_path / "o", untuned=True)
    args[args.index("--recipe") + 1] = str(path)
    code, out, err = f.wrapper(env, ["unit", "--family", f.FAMILY, *args], loaders=uf.loaders())
    print("THETA0-OWN-RECIPE", code, (err.strip().splitlines() or [""])[-1][:160])
    assert code == 2 and "is not one of the settings' allowed recipes" in err and not (tmp_path / "o").exists()
