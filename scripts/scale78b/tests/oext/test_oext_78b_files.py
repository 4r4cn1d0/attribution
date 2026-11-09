"""The committed 7-8B O-ext files and the fill procedure (Track O and its fix round: R-5, R-7, R-8, O6, O11).

The committed state is checked for consistency, never for pin values a fill would change (O6): the maker reproduces
every file from the pins; each index lists its files by SHA-256, the family's branch and manifest, and exactly the
waits the pins imply (a null pin is a wait); the side units are RK's KIT a0_units with the committed job.json pins
where filled; every X settings file passes the unchanged 1B validators with its true label unless it waits on a pin;
the W1-18 settings name the pod's device; the forms OEXT_78B[F] and OEXT_78B_Y[F] pass RK's check and list every file.
The same checks run on temporary copies after each documented fill (they stay green), and a fill reaches only the
indexes and forms of its family or engine (R-5; the verifier's cascade). The behaviour under null pins is tested on
temporary copies whose pins are null. Standard files only: no unit, record of an outcome, or prompt is read."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import oext78_fixtures as f

from scripts.stage1_s1 import lean_eval_job as lej_1b  # noqa: E402

w, mk, oe, ou, s1 = f.w, f.mk, f.oe, f.ou, f.s1
w1 = oe.w1_18
REPO = Path(w.__file__).resolve().parents[2]
OXU = {"generation_sha256": "5ddced7af22b968f", "guard_sha256": "a7f0755b795f0ac4"}         # 1B oext_unit.json pins
G16 = "8f150672832671902a20f552ffd75d2203d6ea105e98a8233c2823394e0b176c"   # an OLMo-2-7B config, another generation
LLAMA_G_1E4 = {"name": "study-kt-llama31-8b-r64-g-mb2-20261011",          # a stand-in for the LR 5e-5 G config
               "config_sha256": "442f133fb1861a74b57fe250023db53d4389fc2bad54c99dcd46bd56af920493"}
REC = ".ai/inputs/stage1-post-w1-20261023/78b/w1-18/overrefusal_checks__llama31-8b.json"
G1_RECORD = ".ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json"
X_ROLES, Y_ROLES = mk.INDEX_ROLES["X"], mk.INDEX_ROLES["Y"]


def rk():
    path = REPO / "runkit" / "stage1-78b" / "rules_78b.py"
    spec = importlib.util.spec_from_file_location("rules_78b_for_track_o", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(settings_dir: Path, name: str) -> dict:
    return json.loads((settings_dir / name).read_bytes())


def index_args(settings_dir: Path, family: str, engine: str) -> list[str]:
    path = settings_dir / mk.index_name(family, engine)
    return ["--family", family, "--engine", engine, "--index", str(path), "--index-sha256", f.sha(path)]


def expected_waits(pins: dict) -> dict:
    """{family: {engine: {pin: sorted roles}}} from the pins alone (a null pin waits), written independently of the
    maker."""
    out = {}
    for family, fam in pins["families"].items():
        x, y, w1i = {}, {}, {}
        if fam["w1_18"]["branch"] == oe.PENDING:
            x["W1_18_BRANCH"], y["W1_18_BRANCH"] = ["lean_eval_job", "oext_eval"], ["oext_eval_y"]
        if fam["units"]["untuned"]["job_sha256"] is None:
            x["THETA0_JOB"] = y["THETA0_JOB"] = w1i["THETA0_JOB"] = ["limits_overrefusal_checks"]
        if any(u["job_sha256"] is None for n, u in fam["units"].items() if n != "untuned"):
            x["UNIT_JOB"] = y["UNIT_JOB"] = w1i["UNIT_JOB"] = ["limits_overrefusal_checks"]
        if fam["recipe_g"]["config_sha256"] is None:
            x["RECIPE_G"] = ["oext_unit"]
        if fam["recipe_bqi"]["config_sha256"] is None:
            y["RECIPE_BQI"] = ["oext_unit_y"]
        if pins["shared"]["engine_y"] is None:
            y["ENGINE_Y"] = ["oext_eval_y", "oext_unit_y"]
        out[family] = {"X": x, "Y": y, "W1": w1i}
    return out


def w1_18_record_for(settings_dir: Path, family: str, records_root: Path, passed: bool = True) -> tuple[str, str]:
    """A text-free record in overrefusal_checks.json's shape (the fields oext_eval and the check read), made under the
    family's W1-18 settings in ``settings_dir`` and listing its units (a stand-in: no unit is read), written at its
    R-21 place under ``records_root``. Returns (its record_path pin, its SHA-256)."""
    limits = load(settings_dir, mk.file_name("limits_overrefusal_checks", family))
    digest = f.sha(settings_dir / mk.file_name("limits_overrefusal_checks", family))
    doc = {"kind": "stage1 over-refusal checks", "version": 1,
           "units": {n: {"truncation": {"cap_tokens": 128, "pass": passed}} for n in limits["units"]},
           "truncation_check": {"units": len(limits["units"]), "units_failing": [] if passed else ["x"],
                                "pass": passed},
           "provenance": {"settings_sha256": digest}}
    rel = f"{mk.RECORDS_DIR}overrefusal_checks__{family}.json"
    return rel, f.write(Path(records_root) / rel, doc)


def run_check(settings_dir: Path, family: str, engine: str, *extra: str) -> tuple[int, dict | None, str]:
    code, out, err = f.call(w.main, ["check", *index_args(settings_dir, family, engine), *extra])
    return code, (json.loads(out) if code == 0 else None), err


def consistency(settings_dir: Path, pins_path: Path, records_root: Path = REPO) -> None:
    """Every committed-state check, on any settings folder and its pins file (the committed one, a fill's copy, or the
    committed files after an in-place fill). A pinned W1-18 record is found at its R-21 path under ``records_root``."""
    pins, _ = mk.load_pins(pins_path)
    assert f.call(mk.main, ["--pins", str(pins_path), "--settings-dir", str(settings_dir), "--records-root",
                            str(records_root), "--check"])[0] == 0
    kit = rk().KIT
    committed = {u["complete_sha256"]: u["job_sha256"] for u in json.loads((REPO / G1_RECORD).read_bytes())["units"]}
    waits = expected_waits(pins)
    files = mk.derive_all(pins, None, settings_dir)
    for family, fam in pins["families"].items():
        for engine in ("X", "Y", "W1"):
            roles = mk.INDEX_ROLES[engine]
            index = load(settings_dir, mk.index_name(family, engine))
            assert (index["family"], index["engine"], index["version"]) == (family, engine, w.INDEX_VERSION)
            assert sorted(index["files"]) == sorted(roles)
            assert all(f.sha(settings_dir / e["file"]) == e["sha256"] for e in index["files"].values())
            assert index["manifest_sha256"] == fam["manifest_sha256"]
            if engine != "W1":
                assert (index["branch"], index["w1_18_record_sha256"], index["w1_18_record_path"]) == \
                    (fam["w1_18"]["branch"], fam["w1_18"]["record_sha256"], fam["w1_18"]["record_path"])
            else:
                assert "branch" not in index and "engine_identity" not in index          # R-20: no branch in W1
            assert {x["pin"]: sorted(x["roles"]) for x in index["waits"]} == waits[family][engine]
            assert all(x["event"] == mk.EVENTS[x["pin"]] for x in index["waits"])
            assert index["other_manifests"] == {o: p["manifest_sha256"] for o, p in pins["families"].items()
                                                if o != family}
            if engine != "W1":
                form = mk.form(family, engine, files, w.code_pins(engine))
                assert rk().oext_form_problem(form) is None
                assert form["files"]["scripts/scale78b/settings/" + mk.index_name(family, engine)] == \
                    f.sha(settings_dir / mk.index_name(family, engine))
                for entry in index["files"].values():
                    assert form["files"]["scripts/scale78b/settings/" + entry["file"]] == entry["sha256"]
                record = fam["w1_18"]["record_path"]                      # W2-1 (R2): the record joins the form
                assert [k for k in form["files"] if k.startswith(mk.RECORDS_DIR)] == ([] if record is None else [record])
                if record is not None:
                    assert form["files"][record] == fam["w1_18"]["record_sha256"] == f.sha(Path(records_root) / record)
            extra = []
            if engine != "W1" and fam["w1_18"]["record_path"] is not None:
                extra = ["--w1-18-record", str(Path(records_root) / fam["w1_18"]["record_path"])]
            code, report, err = run_check(settings_dir, family, engine, *extra)
            assert code == 0, err[-400:]
            nulls = {r for pin, rs in waits[family][engine].items() if pin != "W1_18_BRANCH" for r in rs}
            for role, state in report["settings"].items():
                assert state == ("waits" if role in nulls else "valid"), (family, engine, role, state)
    w1_form = mk.w1_18_78b_form(files, w.code_pins("W1"))
    assert w1_18_form_problem(w1_form) is None
    limits_doc = {fam: load(settings_dir, mk.file_name("limits_overrefusal_checks", fam)) for fam in pins["families"]}
    for family, fam in pins["families"].items():
        assert w1_form["files"]["scripts/scale78b/settings/" + mk.index_name(family, "W1")] == \
            f.sha(settings_dir / mk.index_name(family, "W1"))
        assert sorted(w1_form["side_units"][family]) == sorted(limits_doc[family]["units"])
        limits = limits_doc[family]
        expected = {("untuned" if s == "untuned" else f"a0-{s}"): u for s, u in kit[family]["a0_units"].items()}
        assert sorted(limits["units"]) == sorted(expected)
        for name, unit in limits["units"].items():
            assert unit["complete_sha256"] == expected[name]["complete_sha256"]
            assert "tmp/" + unit["path"] == expected[name]["path"]
            assert (unit["arm"], unit["checkpoint"]) == ("a0", "init" if name == "untuned" else "e1")
            if unit["job_sha256"] is not None and unit["complete_sha256"] in committed:
                assert unit["job_sha256"] == committed[unit["complete_sha256"]]
        assert limits["judge"]["device"] == "cuda"                                         # R-7
        assert f.sha(REPO / limits["judge"]["recipe"]) == limits["judge"]["recipe_file_sha256"]
        unit_doc = load(settings_dir, mk.file_name("oext_unit", family))
        assert (unit_doc["recipes"]["generation_sha256"][:16], unit_doc["recipes"]["guard_sha256"][:16]) == \
            (OXU["generation_sha256"], OXU["guard_sha256"])
        assert unit_doc["recipes"]["allowed"] == {"MAIN": fam["main"]["config_sha256"],
                                                  "G": fam["recipe_g"]["config_sha256"]}
        for role, eval_role in (("oext_unit", "oext_eval"), ("oext_unit_y", "oext_eval_y"),
                                ("lean_eval_job", "oext_eval")):
            d = load(settings_dir, mk.file_name(role, family))
            assert d["oext"]["settings"] == {"path": mk.label(settings_dir / mk.file_name(eval_role, family)),
                                             "sha256": f.sha(settings_dir / mk.file_name(eval_role, family))}


def w1_18_form_problem(doc) -> str | None:
    """K1's W1_18_78B check (ws-k rules_78b.files_form_problem: {files: {plain path under scripts/: SHA-256}}), on the
    form's files part; side_units sit beside it (R-20), each by path under the data root and SHA-256."""
    files = doc.get("files") if isinstance(doc, dict) else None
    if set(doc) != {"files", "side_units"} or not isinstance(files, dict) or not files:
        return "keys"
    for path, digest in files.items():
        if not (path.startswith("scripts/") and all(q not in ("", ".", "..") for q in path.split("/"))
                and isinstance(digest, str) and len(digest) == 64):
            return path
    for family, units in doc["side_units"].items():
        for name, u in units.items():
            if not (isinstance(u["path"], str) and not u["path"].startswith("/") and len(u["complete_sha256"]) == 64):
                return f"{family}/{name}"
    return None


# ----- the committed state ---------------------------------------------------------------------------------------------


def test_the_committed_state_is_consistent():
    consistency(mk.SETTINGS_DIR, mk.PINS_PATH)


def test_the_run_files_are_pinned_and_the_1b_files_are_unchanged():
    assert w.check_code(sorted(w.CODE)) == w.CODE
    for role, (rel, digest) in mk.BASE.items():
        assert f.sha(REPO / rel) == digest
    assert w.CODE["scripts.stage1_s1.oext_eval"] == "8c4290921f32a5b4596a0bc40235cc5cf1185f73eaabeaa625c43bd19ba77719"
    assert not hasattr(w, "INDEX_SHA256") and "OEXT-78B" not in json.dumps(w.CODE)        # R-5: no index literal
    if shutil.which("git") and (REPO / ".git").exists():
        done = subprocess.run(["git", "--no-optional-locks", "-C", str(REPO), "diff", "--stat", "--", "scripts/stage1",
                               "scripts/stage1_s1"], capture_output=True, text=True, timeout=60)
        assert done.returncode == 0 and done.stdout == ""


def test_a_changed_1b_settings_file_refuses_the_maker(monkeypatch):
    monkeypatch.setitem(mk.BASE, "oext_unit", (mk.BASE["oext_unit"][0], "0" * 64))
    code, _, err = f.call(mk.main, ["--check"])
    assert code == 2 and "the 1B files stay byte for byte" in err


def test_the_1b_validators_refuse_the_true_labels_without_the_wrapper():
    """The decisive check (R1 Track O step 1): lean_eval_job.py:229 compares the label with a literal, so the 1B lean
    job refuses a 7-8B settings file that names the file it reads; oext_unit.py:146 compares it with a module global,
    which the wrapper sets. Hence the copy route for lean only."""
    for family in w.FAMILIES:
        with pytest.raises(s1.Refusal, match="oext names the O-ext module and its settings file"):
            lej_1b.check_lean_settings(load(mk.SETTINGS_DIR, mk.file_name("lean_eval_job", family)))
        with pytest.raises(s1.Refusal, match="oext names the O-ext module and its settings file"):
            ou.validate_settings(load(mk.SETTINGS_DIR, mk.file_name("oext_unit", family)))


def test_the_maker_prints_its_own_checkouts_wrapper_hash():
    """O11: the forms name the wrapper beside the maker (loaded by file path), whatever root is first on sys.path."""
    for flag, engine in (("--oext-78b", "X"), ("--oext-78b-y", "Y")):
        code, out, _ = f.call(mk.main, [flag, "llama31-8b"])
        form = json.loads(out)
        assert code == 0 and form["files"]["scripts/scale78b/oext_78b.py"] == f.sha(mk.HERE / "oext_78b.py")
        assert rk().oext_form_problem(form) is None
        assert (f"scripts/scale78b/settings/{mk.index_name('llama31-8b', engine)}" in form["files"])
    y = json.loads(f.call(mk.main, ["--oext-78b-y", "olmo2-7b"])[1])["files"]
    assert "scripts/scale78b/lean_eval_job_78b.py" not in y and "scripts/scale78b/settings/oext_unit_y__olmo2-7b.json" in y


def test_no_settings_file_lies_at_the_copys_default_path():
    assert not (mk.SETTINGS_DIR / "lean_eval_job.json").exists()
    assert w.module(w.LEAN_MODULE).SETTINGS_PATH == mk.SETTINGS_DIR / "lean_eval_job.json"


# ----- fills on temporary copies, from the pre-fill (all-null) state in T-O2's order ---------------------------------


def all_null_pins() -> dict:
    """The committed pins with every fillable pin null (the state before T-O2 step 1): both branches pending, theta0's
    job pins, Llama's G, both B+Qi and ENGINE_Y. OLMo-2-7B's G is no fill (its existing config, DES F2)."""
    pins, _ = mk.load_pins()
    pins = copy.deepcopy(pins)
    pins["shared"]["engine_y"] = None
    for fam in pins["families"].values():
        fam["w1_18"] = {"branch": oe.PENDING, "record_sha256": None, "record_path": None, "full_reason": None}
        fam["units"]["untuned"]["job_sha256"] = None
        fam["recipe_bqi"] = {"name": None, "config_sha256": None}
    pins["families"]["llama31-8b"]["recipe_g"] = {"name": None, "config_sha256": None}
    return pins


def fill_theta0(p, family="olmo2-7b", ctx=None):
    p["families"][family]["units"]["untuned"]["job_sha256"] = ("b" if family == "olmo2-7b" else "c") * 64


def fill_llama_g(p, ctx=None):
    p["families"]["llama31-8b"]["recipe_g"] = dict(LLAMA_G_1E4)


def fill_engine_y(p, ctx=None):
    p["shared"]["engine_y"] = f.ENGINE_Y_FIXTURE


def fill_bqi(p, family="olmo2-7b", ctx=None):
    p["families"][family]["recipe_bqi"] = dict(p["families"][family]["main"])          # a stand-in config


def fill_branch(p, family="olmo2-7b", ctx=None, passed=True):
    """The branch fill from the family's W1-18 record (committed first at its R-21 place: ``ctx`` = (settings folder,
    records root)): 128 for a passing record, full for a failing one."""
    sdir, root = ctx
    rel, digest = w1_18_record_for(sdir, family, root, passed=passed)
    p["families"][family]["w1_18"] = {"branch": "128" if passed else "full", "record_sha256": digest,
                                      "record_path": rel, "full_reason": None}


T_O2 = [("theta0 olmo2-7b", fill_theta0), ("theta0 llama31-8b", lambda p, ctx=None: fill_theta0(p, "llama31-8b")),
        ("branch 128 olmo2-7b", fill_branch), ("recipe G llama31-8b", fill_llama_g),
        ("branch full llama31-8b", lambda p, ctx=None: fill_branch(p, "llama31-8b", ctx, passed=False)),
        ("ENGINE_Y", fill_engine_y), ("B+Qi olmo2-7b", fill_bqi),
        ("B+Qi llama31-8b", lambda p, ctx=None: fill_bqi(p, "llama31-8b"))]


def fill_copy(tmp_path: Path, steps: int) -> tuple[Path, Path, Path]:
    """The documented fill on a temporary copy from the all-null state: write the pins, run the maker, then each of
    the first ``steps`` T-O2 fills (edit the pins, run the maker). Returns (settings folder, pins file, records root)."""
    pins = all_null_pins()
    sdir, pins_path, root = tmp_path / "settings", tmp_path / "oext_pins_78b.json", tmp_path / "records-root"

    def make():
        pins_path.write_bytes(mk.dumps(pins))
        code, _, err = f.call(mk.main, ["--pins", str(pins_path), "--settings-dir", str(sdir), "--records-root",
                                        str(root)])
        assert code == 0, err[-300:]

    make()
    for _, step in T_O2[:steps]:
        step(pins, ctx=(sdir, root))
        make()
    return sdir, pins_path, root


@pytest.mark.parametrize("steps", range(len(T_O2) + 1), ids=["none"] + [n.replace(" ", "-") for n, _ in T_O2])
def test_the_documented_fill_leaves_the_committed_state_checks_green(tmp_path, steps):
    """O6 and OR1: from the pre-fill state, each T-O2 step in turn (edit the pins, run the maker) leaves the same
    consistency checks green, a pinned W1-18 record included (found at its R-21 place; R-6 through the check)."""
    sdir, pins_path, root = fill_copy(tmp_path, steps)
    consistency(sdir, pins_path, root)


CASCADE = {   # fill -> the forms it may change: (family, engine); engine "W1" is W1_18_78B's family part
    "branch llama31-8b": ({("llama31-8b", "X"), ("llama31-8b", "Y")},
                          lambda p: p["families"]["llama31-8b"].update(
                              w1_18={"branch": "128", "record_sha256": "a" * 64, "full_reason": None,
                                     "record_path": mk.RECORDS_DIR + "overrefusal_checks__llama31-8b.json"})),
    "theta0 llama31-8b": ({("llama31-8b", "X"), ("llama31-8b", "Y"), ("llama31-8b", "W1")},
                          lambda p: fill_theta0(p, "llama31-8b")),
    "theta0 olmo2-7b": ({("olmo2-7b", "X"), ("olmo2-7b", "Y"), ("olmo2-7b", "W1")}, fill_theta0),
    "recipe_g llama31-8b": ({("llama31-8b", "X")}, fill_llama_g),
    "recipe_bqi olmo2-7b": ({("olmo2-7b", "Y")}, fill_bqi),
    "engine_y": ({("olmo2-7b", "Y"), ("llama31-8b", "Y")}, fill_engine_y),
}


@pytest.mark.parametrize("name", sorted(CASCADE))
def test_a_fill_reaches_only_its_familys_and_engines_pins(name):
    """R-5 and R-20 (the verifier's cascade.py, as a test): derive before and after one fill and compare the four kit
    forms (OEXT_78B[F], OEXT_78B_Y[F]) and each family's part of W1_18_78B: only the fill's family (or engine)
    changes; a branch, G, B+Qi or ENGINE_Y fill never reaches W1_18_78B."""
    allowed, change = CASCADE[name]
    pins = all_null_pins()
    after = copy.deepcopy(pins)
    change(after)

    def forms(p):
        files = mk.derive_all(p)
        out = {(fam, eng): mk.form(fam, eng, files, w.code_pins(eng)) for fam in w.FAMILIES for eng in ("X", "Y")}
        w1 = mk.w1_18_78b_form(files, w.code_pins("W1"))
        for fam in w.FAMILIES:
            out[(fam, "W1")] = {k: v for k, v in w1["files"].items() if fam in k} | {"units": w1["side_units"][fam]}
        return out

    before, now = forms(pins), forms(after)
    changed = {key for key in before if before[key] != now[key]}
    assert changed == allowed, (name, sorted(changed))
    own = ("scripts/scale78b/settings/", mk.RECORDS_DIR)        # W2-1 (R2): a branch fill's record joins its forms
    for key in before:                                          # the wrapper and the run files never change
        if key[1] != "W1":
            assert {k: v for k, v in before[key]["files"].items() if not k.startswith(own)} \
                == {k: v for k, v in now[key]["files"].items() if not k.startswith(own)}
            record = after["families"][key[0]]["w1_18"]["record_path"]
            assert [k for k in now[key]["files"] if k.startswith(mk.RECORDS_DIR)] == ([] if record is None else [record])


# ----- the behaviour under null pins (a temporary all-null copy) -----------------------------------------------------


@pytest.fixture(scope="module")
def all_null(tmp_path_factory):
    """The all-null copy (the pre-fill state), whatever the committed pins hold."""
    sdir, _, _ = fill_copy(tmp_path_factory.mktemp("null"), 0)
    return sdir


@pytest.mark.parametrize("command,family,engine,tail,needle", [
    ("unit", "olmo2-7b", "X", ["run", "--untuned"], "the pin W1_18_BRANCH is null"),
    ("unit", "llama31-8b", "X", ["run", "--untuned"], "the pin RECIPE_G is null"),
    ("unit", "olmo2-7b", "Y", ["run", "--untuned"], "the pin ENGINE_Y is null"),
    ("lean", "llama31-8b", "X", ["run", "--out", "x"], "the pin W1_18_BRANCH is null"),
    ("w1_18", "olmo2-7b", "W1", ["--out", "x"], "the pin THETA0_JOB is null"),
])
def test_each_command_refuses_with_its_event_while_a_pin_is_null(all_null, tmp_path, command, family, engine, tail,
                                                                 needle):
    code, out, err = f.call(w.main, [command, *index_args(all_null, family, engine),
                                     *[a if a != "x" else str(tmp_path / "x") for a in tail]])
    assert code == 2 and needle in err and not (tmp_path / "x").exists()


def test_null_pins_refuse_the_1b_validators(all_null):
    """GXB O11: with Llama's G null the unit settings refuse; with theta0's job pin null W1-18's check refuses; the Y
    files with ENGINE_Y null wait. Each is reported "waits" (exit 0) because its file passes with the null fields
    replaced by placeholders (OR8; W2-3 of R2)."""
    doc = load(all_null, mk.file_name("oext_unit", "llama31-8b"))
    with pytest.raises(s1.Refusal, match=re.escape("recipes.allowed.G must be a SHA-256")):
        with w.patched([(ou, "OEXT_SETTINGS_PATH", doc["oext"]["settings"]["path"])]):
            ou.validate_settings(doc)
    with pytest.raises(s1.Refusal, match=re.escape("unit untuned job_sha256")):
        w1.check_content(load(all_null, mk.file_name("limits_overrefusal_checks", "olmo2-7b")))
    code, report, err = run_check(all_null, "llama31-8b", "X")
    assert code == 0 and report["settings"]["oext_unit"] == "waits", err[-300:]
    assert report["settings"]["limits_overrefusal_checks"] == "waits"
    assert report["waits"]["unit"] == ["RECIPE_G", "W1_18_BRANCH"]
    code, report, _ = run_check(all_null, "olmo2-7b", "Y")
    assert code == 0 and report["settings"]["oext_unit_y"] == "waits" and report["settings"]["oext_eval_y"] == "waits"


def test_the_y_files_are_validated_with_engine_ys_identity_once_filled(tmp_path):
    """R-23: on a copy with ENGINE_Y and B+Qi filled, the check validates the Y files under engine Y's identity (the
    1B settings check, run as on engine Y), and an index naming another identity refuses."""
    sdir, _, _ = fill_copy(tmp_path, len(T_O2))
    code, report, err = run_check(sdir, "olmo2-7b", "Y", "--w1-18-record",
                                  str(tmp_path / "records-root" / mk.RECORDS_DIR / "overrefusal_checks__olmo2-7b.json"))
    assert code == 0, err[-300:]
    assert report["settings"] == {"limits_overrefusal_checks": "valid", "oext_eval_y": "valid", "oext_unit_y": "valid"}
    index = load(sdir, mk.index_name("olmo2-7b", "Y"))
    index["engine_identity"] = "4" * 64
    path = sdir / mk.index_name("olmo2-7b", "Y")
    f.write(path, index)
    code, _, err = f.call(w.main, ["check", "--family", "olmo2-7b", "--engine", "Y", "--index", str(path),
                                   "--index-sha256", f.sha(path)])
    assert code == 2 and f"names engine {f.ENGINE_Y_FIXTURE}, the engine-Y index {'4' * 64}" in err


def test_the_documented_fill_in_place_leaves_the_suite_green(tmp_path):
    """OR1: the documented fill done IN PLACE (the re-verifier's rv_fill.py form): a copy of this checkout (this
    package copied, every other entry linked read-only; the records folder of R-21 real), the committed pins set to
    the pre-fill state, every T-O2 step done with the maker's defaults (its own pins file and settings folder, the
    W1-18 records committed at their R-21 place), then this whole test folder run in the copy: no failure."""
    if os.environ.get("OEXT78_NESTED"):
        pytest.skip("inside the nested run")
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    for entry in sorted(REPO.iterdir()):
        if entry.name not in ("scripts", ".git", ".ai"):
            (repo / entry.name).symlink_to(entry.resolve())
    for entry in sorted((REPO / "scripts").iterdir()):
        if entry.name == "scale78b":
            shutil.copytree(entry, repo / "scripts" / "scale78b", symlinks=True,
                            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        else:
            (repo / "scripts" / entry.name).symlink_to(entry.resolve())
    link_tree(REPO / ".ai", repo / ".ai", Path(mk.RECORDS_DIR).parts[1:])
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
    env.update(PYTHONDONTWRITEBYTECODE="1", OEXT78_NESTED="1")
    settings, pins_path = repo / "scripts/scale78b/settings", repo / "scripts/scale78b/settings/oext_pins_78b.json"
    pins = all_null_pins()

    def make():
        pins_path.write_bytes(mk.dumps(pins))
        done = subprocess.run([sys.executable, "-B", "scripts/scale78b/make_oext_settings_78b.py"], cwd=repo, env=env,
                              capture_output=True, text=True, timeout=300)
        assert done.returncode == 0, done.stderr[-300:]

    make()
    for _, step in T_O2:
        step(pins, ctx=(settings, repo))
        make()
    done = subprocess.run([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfE", "--basetemp",
                           str(tmp_path / "pt"), "scripts/scale78b/tests/oext"], cwd=repo, env=env,
                          capture_output=True, text=True, timeout=550)
    tail = [x for x in (done.stdout + done.stderr).splitlines() if x.strip()]
    assert done.returncode == 0 and " passed" in tail[-1] and "failed" not in tail[-1], "\n".join(tail[-15:])


def link_tree(src: Path, dst: Path, real: tuple) -> None:
    """dst mirrors src by links, except the folders along ``real`` (relative parts) and the last one, which are real
    folders (so a record can be written there without touching src)."""
    dst.mkdir(parents=True, exist_ok=True)
    head = real[0] if real else None
    if src.is_dir():
        for entry in sorted(src.iterdir()):
            if entry.name != head:
                (dst / entry.name).symlink_to(entry.resolve())
    if head is not None:
        link_tree(src / head, dst / head, real[1:])


# ----- the maker's rules -----------------------------------------------------------------------------------------------


def derive(change) -> dict:
    """The maker's derivation in memory from the pre-fill state with one change (independent of the committed pins)."""
    pins = all_null_pins()
    change(pins)
    return {n: json.loads(d) for n, d in mk.derive_all(pins).items()}


@pytest.mark.parametrize("w1_18,needle", [
    ({"branch": "128", "record_sha256": None, "record_path": None, "full_reason": None}, "Branch 128 needs"),
    ({"branch": "full", "record_sha256": "a" * 64, "record_path": REC, "full_reason": "x"}, "not both"),
    ({"branch": "full", "record_sha256": None, "record_path": None, "full_reason": None}, "not both"),
    ({"branch": "pending_w1_18", "record_sha256": "a" * 64, "record_path": REC, "full_reason": None},
     "a pending branch"),
    ({"branch": "64", "record_sha256": None, "record_path": None, "full_reason": None}, "must be one of"),
    ({"branch": "128", "record_sha256": "a" * 64, "record_path": None, "full_reason": None}, "both given or both null"),
    ({"branch": "128", "record_sha256": "a" * 64, "record_path": "scripts/x.json", "full_reason": None}, "R-21"),
    ({"branch": "128", "record_sha256": "a" * 64, "record_path": mk.RECORDS_DIR + "../x.json", "full_reason": None},
     "R-21"),
    ({"branch": "128", "record_sha256": "a" * 64, "full_reason": None}, "record_path, full_reason"),
])
def test_the_w1_18_pin_form_refuses_a_branch_without_its_record(w1_18, needle):
    def fill(p):
        p["families"]["llama31-8b"]["w1_18"] = w1_18

    with pytest.raises(s1.Refusal, match=needle):
        derive(fill)


def test_a_filled_engine_y_and_bqi_give_y_files_that_refuse_on_engine_x():
    def fill(p):
        fill_engine_y(p)
        fill_bqi(p)

    got = derive(fill)
    y = got[mk.file_name("oext_unit_y", "olmo2-7b")]
    main = mk.load_pins()[0]["families"]["olmo2-7b"]["main"]["config_sha256"]
    assert y["engine_x"] == f.ENGINE_Y_FIXTURE and y["recipes"]["allowed"] == {"B+Qi": main}
    assert y["oext"]["settings"]["path"] == "scripts/scale78b/settings/oext_eval_y__olmo2-7b.json"
    running = s1.code_identity()["sha256"]
    with pytest.raises(s1.Refusal, match=f"written for engine {f.ENGINE_Y_FIXTURE}, this engine is {running}"):
        with w.patched([(ou, "OEXT_SETTINGS_PATH", y["oext"]["settings"]["path"])]):
            ou.validate_settings(y)
    waits = {x["pin"] for x in got[mk.index_name("olmo2-7b", "Y")]["waits"]}
    assert not waits & {"ENGINE_Y", "RECIPE_BQI"}


def test_a_recipe_pin_off_its_config_refuses():
    def fill(p):
        p["families"]["olmo2-7b"]["recipe_g"]["config_sha256"] = "b" * 64

    with pytest.raises(s1.Refusal, match="hashes to 01259f28"):
        derive(fill)


def test_the_maker_refuses_a_pinned_record_that_is_not_at_its_place(tmp_path):
    """R-21: the branch fill names the record's committed path and SHA-256; the maker refuses a record that is not
    there, or not with that hash."""
    sdir, pins_path, root = fill_copy(tmp_path, 3)                    # OLMo's branch 128 filled
    record = root / mk.RECORDS_DIR / "overrefusal_checks__olmo2-7b.json"
    record.write_bytes(record.read_bytes() + b" ")
    code, _, err = f.call(mk.main, ["--pins", str(pins_path), "--settings-dir", str(sdir), "--records-root", str(root),
                                    "--check"])
    assert code == 2 and "olmo2-7b: the W1-18 record hashes to" in err
    record.unlink()
    code, _, err = f.call(mk.main, ["--pins", str(pins_path), "--settings-dir", str(sdir), "--records-root", str(root),
                                    "--check"])
    assert code == 2 and "cannot be read" in err


def test_the_w1_18_route_form_is_printed():
    """R-20: --w1-18-78b prints W1_18_78B: the wrapper (beside the maker), the w1_18 run files, per family the W1 index
    and the W1-18 settings, and the side units by path and SHA-256."""
    code, out, _ = f.call(mk.main, ["--w1-18-78b"])
    form = json.loads(out)
    assert code == 0 and w1_18_form_problem(form) is None
    assert form["files"]["scripts/scale78b/oext_78b.py"] == f.sha(mk.HERE / "oext_78b.py")
    assert "scripts/scale78b/lean_eval_job_78b.py" not in form["files"]
    assert "scripts/stage1_s1/oext_unit.py" not in form["files"]
    for family in w.FAMILIES:
        for name in (mk.index_name(family, "W1"), mk.file_name("limits_overrefusal_checks", family)):
            assert form["files"][f"scripts/scale78b/settings/{name}"] == f.sha(mk.SETTINGS_DIR / name)


def test_a_bqi_config_with_another_generation_block_refuses():
    """OR5: oext_unit_y pins MAIN_F's blocks, so the maker refuses a B+Qi config whose generation block differs (the
    1B check_recipe would refuse it only on the engine-Y pod)."""
    def fill(p):
        p["families"]["olmo2-7b"]["recipe_bqi"] = {"name": "study-kt-olmo2-7b-r64-b-mb2-g16-20261008",
                                                   "config_sha256": G16}

    with pytest.raises(s1.Refusal, match="recipe_bqi's generation or guard block differs from MAIN"):
        derive(fill)


def test_a_recipe_g_with_another_generation_block_refuses():
    """One O-ext cap and one judge per family: oext_unit pins one generation and one guard block for every allowed
    recipe, so a G config whose generation block differs from MAIN_F's refuses (a g16 config has another one)."""
    def fill(p):
        p["families"]["olmo2-7b"]["recipe_g"] = {"name": "study-kt-olmo2-7b-r64-b-mb2-g16-20261008",
                                                 "config_sha256": G16}

    with pytest.raises(s1.Refusal, match="generation or guard block differs from MAIN"):
        derive(fill)


def test_the_w1_18_settings_keep_each_familys_prepared_set():
    """The verifier's V-m-w1-manifest and V-m-w1-prepared-path: the W1-18 settings name the family's own prepared set
    (Llama's never OLMo's), by path and manifest."""
    pins, _ = mk.load_pins()
    for family in w.FAMILIES:
        prepared = load(mk.SETTINGS_DIR, mk.file_name("limits_overrefusal_checks", family))["prepared"]
        assert (prepared["path"], prepared["manifest_sha256"]) == (pins["families"][family]["prepared_path"],
                                                                   pins["families"][family]["manifest_sha256"])
    assert pins["families"]["llama31-8b"]["prepared_path"] != pins["families"]["olmo2-7b"]["prepared_path"]


def test_the_two_families_differ_only_where_they_should():
    def flat(obj, prefix=""):
        if isinstance(obj, dict) and obj:
            return {k: v for key, value in obj.items() for k, v in flat(value, f"{prefix}{key}.").items()}
        return {prefix[:-1]: obj}

    fillable = {"cap.branch", "cap.w1_18.record_sha256", "cap.w1_18.full_reason", "oext.branch"}
    allowed = {
        "oext_unit": {"prepared.manifest_sha256", "recipes.allowed.MAIN", "recipes.allowed.G", "recipes.rule",
                      "oext.settings.path", "oext.settings.sha256"},
        "oext_unit_y": {"prepared.manifest_sha256", "recipes.rule", "oext.settings.path", "oext.settings.sha256",
                        "recipes.allowed.B+Qi"},
        "oext_eval": {"cap.w1_18.settings_sha256"} | fillable, "oext_eval_y": {"cap.w1_18.settings_sha256"} | fillable,
        "lean_eval_job": {"oext.settings.path", "oext.settings.sha256"} | fillable,
        "limits_overrefusal_checks": {"prepared.manifest_sha256", "prepared.path", "judge.recipe",
                                      "judge.recipe_file_sha256", "allow_list.path_pattern", "units_source"},
    }
    for role in mk.ROLES:
        a = flat(load(mk.SETTINGS_DIR, mk.file_name(role, "olmo2-7b")))
        b = flat(load(mk.SETTINGS_DIR, mk.file_name(role, "llama31-8b")))
        differ = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
        if role == "lean_eval_job":
            differ = {k for k in differ if not k.startswith("job.allowed_recipes.")}
        if role == "limits_overrefusal_checks":
            differ = {k for k in differ if not k.startswith("units.")}
        assert differ <= allowed[role], (role, sorted(differ - allowed[role]))
