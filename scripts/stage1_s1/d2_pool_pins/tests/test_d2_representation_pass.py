"""D-2 (addendum section 19 point 2(b)): d2_representation_pass on a synthetic end-to-end. REQ-8 (build_plant.py itself)
runs on test_build_plant.py's synthetic world and writes its record and its plant (75) and decoy (37) pools;
fill_pins fills the pins from that record; REQ-3 then runs on the engine's fixture prepared set and tiny model
(test_representation_pass.py's env). representation_pass alone refuses the plant and decoy pools (null pins); the
wrapper accepts them, and its outputs equal representation_pass's on a hand-filled copy byte for byte (rows) and
except the costs block's timings (summary). S3 pools named on the command line behave as before. Nothing real is
read."""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1.d2_pool_pins import d2_representation_pass as d2m  # noqa: E402
from scripts.stage1_s1.d2_pool_pins import fill_pins as fp  # noqa: E402

import d2fixtures as dx  # noqa: E402
from d2guard import guarded  # noqa: E402  (a wrapper defect fails the tests, never errors their setup)
import test_representation_pass as trp  # noqa: E402  (its env fixture: the engine's fixture prepared set)

env = trp.env
sfx = trp.sfx
W1_DEFAULTS = (rp.POOL_PINS_PATH, rp.POOL_PINS_SHA256)


@pytest.fixture(scope="module")
def req8(tmp_path_factory):
    """REQ-8's record and pools (build_plant.py's build on a synthetic world), and the pins fill_pins writes from them
    (through its CLI). Guarded: a D-2 defect here fails every test that reads it (d2guard)."""
    root = tmp_path_factory.mktemp("req8")
    return guarded("req8", lambda: make_req8(root))


def make_req8(root):
    r = dx.run_req8(root)
    out = root / "filled.json"
    code = fp.main(["--w1-pins", dx.spec((dx.w1_pins_path(), dx.W1_PINS_SHA256)), "--req8-record", dx.spec(r["record"]),
                    "--out", str(out)])
    assert code == 0, "fill_pins refused the synthetic REQ-8 record"
    r["filled"] = (out, sha256_file(out))
    r["hand"] = dx.hand_fill(dx.w1_pins_bytes(), r["plant"][1], r["decoy"][1])
    return r


@pytest.fixture(scope="module")
def rp_settings(env, tmp_path_factory):
    """The env's REQ-3 settings (its fixture pins) in a file, and that file's SHA-256."""
    path = tmp_path_factory.mktemp("rps") / "representation_pass.json"
    path.write_bytes(canonical_json(env.settings))
    return path, sha256_file(path)


@pytest.fixture
def wired(monkeypatch, rp_settings):
    """main() on the fixture env: the fixture loaders for real_loaders, and the privately loaded base module's settings
    pin set to the env settings' SHA-256 (the only test seam; the pins path and SHA-256 are D-2's own). Records each
    base that main() loads."""
    import experiments.safety_selection.loaders as loaders_module

    monkeypatch.setattr(loaders_module, "real_loaders", lambda: sfx.fixture_loaders())
    loaded = []
    real = fp.load_base

    def load_base(*args, **kwargs):
        base = real(*args, **kwargs)
        base.module.SETTINGS_SHA256 = rp_settings[1]
        loaded.append(base)
        return base
    monkeypatch.setattr(fp, "load_base", load_base)
    return loaded


def argv_of(env, rp_settings, out, pools, pools_only=False, extra=()):
    argv = ["--prepared", str(env.prepared), "--recipe", str(env.recipe), "--anchors", str(env.anchors)]
    for pair in pools:
        argv += ["--pool", dx.spec(pair)]
    if pools_only:
        argv.append("--pools-only")
    return argv + ["--out", str(out), "--settings", str(rp_settings[0]), *extra]


def d2_argv(env, rp_settings, req8, out, pools, pools_only=False):
    return argv_of(env, rp_settings, out, pools, pools_only,
                   ("--pool-pins", dx.spec(req8["filled"]), "--req8-record", dx.spec(req8["record"])))


def outputs(folder: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(folder.iterdir())}


# ----- the fill of a real REQ-8 record ----------------------------------------------------------------------------


def test_fill_pins_fills_from_a_real_req8_record(req8):
    """build_plant.py's own record (kind, pools, full_files, ids, provenance) passes check_record; the filled file is
    the hand fill with the SHA-256s of the pool files build_plant wrote."""
    doc = req8["record_doc"]
    assert doc["kind"] == "stage1 plant record" and doc["provenance"]["script"] == "scripts/stage1/build_plant.py"
    assert doc["pools"] == {"plant": {"sha256": req8["plant"][1], "items": 75}, "decoy": {"sha256": req8["decoy"][1], "items": 37}}
    assert req8["filled"][0].read_bytes() == req8["hand"]
    assert req8["filled"][1] == sha256_bytes(req8["hand"])
    assert json.loads(req8["plant"][0].read_bytes())["name"] == "plant"
    assert json.loads(req8["decoy"][0].read_bytes())["name"] == "decoy"


# ----- the end-to-end -----------------------------------------------------------------------------------------------


def test_representation_pass_alone_refuses_the_plant_and_decoy_pools(env, req8, rp_settings, wired, tmp_path, monkeypatch,
                                                                     capsys):
    """The W1 file with its null pins: run() and main() refuse each pool as 'not filled yet' (nothing written)."""
    for name in ("plant", "decoy"):
        with pytest.raises(s1.Refusal, match=f"pool {name} is a W1-known pool whose pin is not filled yet"):
            rp.run(env.prepared, env.recipe, env.anchors, sfx.fixture_loaders(), env.settings, rp_settings[1],
                   [req8[name]], False)
    monkeypatch.setattr(rp, "SETTINGS_SHA256", rp_settings[1])
    assert rp.main(argv_of(env, rp_settings, tmp_path / "w1", [req8["plant"], req8["decoy"]], True)) == 2
    assert "not filled yet" in capsys.readouterr().err and not (tmp_path / "w1").exists()


@pytest.fixture(scope="module")
def e2e(env, req8, rp_settings, tmp_path_factory):
    """d2_representation_pass.main on the dev units, the plant, the decoy and an S3 pool (one run), and the reference:
    the W1 module's run() with the hand-filled pins document (same settings SHA-256). Guarded."""
    root = tmp_path_factory.mktemp("e2e")
    return guarded("e2e", lambda: make_e2e(env, req8, rp_settings, root))


def make_e2e(env, req8, rp_settings, root):
    import experiments.safety_selection.loaders as loaders_module

    s3, s3_sha = trp.pool_file(root, [{"id": "s3-1", "prompt": "Synthetic S3 prompt about lakes?",
                                       "response": "Synthetic S3 answer about rivers."}], "s3_safe")
    pools = [req8["plant"], req8["decoy"], (s3, s3_sha)]
    real_loaders, real_load_base = loaders_module.real_loaders, fp.load_base
    loaded = []

    def load_base(*args, **kwargs):
        base = real_load_base(*args, **kwargs)
        base.module.SETTINGS_SHA256 = rp_settings[1]
        loaded.append((base, base.module.load_pool_pins, base.module.load_pool_pins.__defaults__))
        return base
    loaders_module.real_loaders, fp.load_base = (lambda: sfx.fixture_loaders()), load_base
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            code = d2m.main(d2_argv(env, rp_settings, req8, root / "out", pools))
    finally:
        loaders_module.real_loaders, fp.load_base = real_loaders, real_load_base
    assert code == 0, "d2_representation_pass refused the end-to-end"
    hand_doc = json.loads(req8["hand"])
    ref = rp.run(env.prepared, env.recipe, env.anchors, sfx.fixture_loaders(), env.settings, rp_settings[1], pools, True,
                 pool_pins=(hand_doc, sha256_bytes(req8["hand"])))
    return {"out": outputs(root / "out"), "ref": ref, "pools": pools, "root": root, "loaded": loaded,
            "stdout": stdout.getvalue()}


def test_d2_accepts_the_plant_and_decoy_pools(e2e, req8, env):
    summary = json.loads(e2e["out"][rp.SUMMARY_FILE])
    assert set(e2e["out"]) == {rp.ROWS_FILE, rp.SUMMARY_FILE}
    by_name = {p["name"]: p for p in summary["pools"]}
    assert by_name["plant"] == {"name": "plant", "sha256": req8["plant"][1], "items": 75, "pinned_by": "pool pins",
                                "refused_by_reason": {}}
    assert by_name["decoy"] == {"name": "decoy", "sha256": req8["decoy"][1], "items": 37, "pinned_by": "pool pins",
                                "refused_by_reason": {}}
    assert by_name["s3_safe"]["pinned_by"] == "command line"
    assert summary["pool_pins"] == {"file": "settings/representation_pools.json", "sha256": req8["filled"][1],
                                    "filled": ["decoy", "plant"], "not_filled": []}
    assert summary["provenance"]["inputs"]["pool_pins"] == req8["filled"][1]
    assert summary["provenance"]["script"] == "scripts/stage1/representation_pass.py"
    assert summary["provenance"]["script_sha256"] == dx.RP_SHA256
    sources = [json.loads(l)["source"] for l in e2e["out"][rp.ROWS_FILE].splitlines()]
    assert sources.count("plant") == 75 and sources.count("decoy") == 37 and sources.count("s3_safe") == 1
    assert sources.count("dev") == sum(len(env.view.groups["dev"][g]) for g in env.groups) > 0


def test_d2_outputs_equal_representation_pass_with_a_hand_filled_pins_document(e2e):
    """Rows byte for byte; the summary byte for byte once the costs block (wall-clock timings) is removed."""
    assert e2e["out"][rp.ROWS_FILE] == e2e["ref"][rp.ROWS_FILE]
    assert canonical_json(dx.without(e2e["out"][rp.SUMMARY_FILE], ("costs",))) == \
        canonical_json(dx.without(e2e["ref"][rp.SUMMARY_FILE], ("costs",)))
    assert set(json.loads(e2e["out"][rp.SUMMARY_FILE])["costs"]) == set(json.loads(e2e["ref"][rp.SUMMARY_FILE])["costs"])


def test_d2_outputs_equal_a_hand_filled_copy_of_representation_pass(e2e, env, req8, rp_settings, tmp_path):
    """The fill rule done by hand in a copy (the pins file and the literal POOL_PINS_SHA256 edited), run with its own
    committed-pins path (pool_pins=None): equal outputs except the costs timings and the provenance's script path and
    hash (the copy's)."""
    hand = dx.hand_filled_copy(tmp_path, req8["hand"])
    assert hand.POOL_PINS_SHA256 == req8["filled"][1] and hand.__name__ not in sys.modules
    files = hand.run(env.prepared, env.recipe, env.anchors, sfx.fixture_loaders(), env.settings, rp_settings[1],
                     e2e["pools"], True)
    assert files[rp.ROWS_FILE] == e2e["out"][rp.ROWS_FILE]
    drop = (("costs",), ("provenance", "script"), ("provenance", "script_sha256"))
    assert canonical_json(dx.without(files[rp.SUMMARY_FILE], *drop)) == \
        canonical_json(dx.without(e2e["out"][rp.SUMMARY_FILE], *drop))
    assert json.loads(files[rp.SUMMARY_FILE])["provenance"]["script_sha256"] != dx.RP_SHA256


def test_the_replacement_is_restored_and_the_w1_module_untouched(e2e):
    """After main(): the private module's POOL_PINS_PATH, POOL_PINS_SHA256 and load_pool_pins defaults are the W1
    values again; the module was private; the normally imported W1 module never changed."""
    [(base, fn, defaults)] = e2e["loaded"]
    m = base.module
    assert m.__name__ == fp.MODULE_NAME and fp.MODULE_NAME not in sys.modules and m is not rp
    assert m.load_pool_pins is fn and m.load_pool_pins.__defaults__ == defaults == W1_DEFAULTS
    assert (m.POOL_PINS_PATH, m.POOL_PINS_SHA256) == W1_DEFAULTS
    assert rp.load_pool_pins.__defaults__ == W1_DEFAULTS and rp.POOL_PINS_SHA256 == dx.W1_PINS_SHA256
    assert sha256_file(Path(rp.__file__)) == dx.RP_SHA256 and sha256_file(rp.POOL_PINS_PATH) == dx.W1_PINS_SHA256


def test_the_replacement_is_restored_after_a_refusal(env, req8, rp_settings, wired, tmp_path, capsys):
    """A pool whose given SHA-256 is wrong: representation_pass refuses inside the call (exit 2, nothing written); the
    replacement is undone."""
    bad = (req8["plant"][0], "0" * 64)
    assert d2m.main(d2_argv(env, rp_settings, req8, tmp_path / "out", [bad], True)) == 2
    assert "a pool file hashes to" in capsys.readouterr().err and not (tmp_path / "out").exists()
    [base] = wired
    assert base.module.load_pool_pins.__defaults__ == W1_DEFAULTS
    assert (base.module.POOL_PINS_PATH, base.module.POOL_PINS_SHA256) == W1_DEFAULTS


def test_the_replacement_is_restored_after_an_exception(req8, monkeypatch):
    """An exception other than a refusal inside representation_pass's main(): it propagates, and the pins path, its
    SHA-256 and load_pool_pins's defaults are the W1 values again (fix round: d2-verify-code note 3)."""
    base = dx.load_base()
    path, sha = req8["filled"][0].resolve(), req8["filled"][1]
    seen = []

    def boom(argv):
        seen.append((base.module.POOL_PINS_PATH, base.module.POOL_PINS_SHA256, base.module.load_pool_pins.__defaults__))
        raise RuntimeError("synthetic failure inside representation_pass")
    monkeypatch.setattr(base.module, "main", boom)
    with pytest.raises(RuntimeError, match="synthetic failure inside representation_pass"):
        d2m.run_base(base, [], path, sha)
    assert seen == [(path, sha, (path, sha))]
    assert base.module.load_pool_pins.__defaults__ == W1_DEFAULTS
    assert (base.module.POOL_PINS_PATH, base.module.POOL_PINS_SHA256) == W1_DEFAULTS


def test_run_base_replaces_exactly_the_pins_path_and_hash(req8, monkeypatch):
    """Inside the call the module sees the filled path and SHA-256 in the two globals and load_pool_pins's defaults,
    and main() receives the forwarded arguments unchanged."""
    base = dx.load_base()
    seen = {}

    def fake_main(argv):
        m = base.module
        seen.update(argv=argv, globals=(m.POOL_PINS_PATH, m.POOL_PINS_SHA256), defaults=m.load_pool_pins.__defaults__,
                    loaded=m.load_pool_pins())
        return 0
    monkeypatch.setattr(base.module, "main", fake_main)
    path, sha = req8["filled"][0].resolve(), req8["filled"][1]
    assert d2m.run_base(base, ["--x"], path, sha) == 0
    assert seen["argv"] == ["--x"] and seen["globals"] == seen["defaults"] == (path, sha)
    assert seen["loaded"][1] == sha and seen["loaded"][0]["pools"]["plant"]["sha256"] == req8["plant"][1]
    assert base.module.load_pool_pins.__defaults__ == W1_DEFAULTS


def test_run_base_refuses_a_module_whose_defaults_are_not_its_globals(req8, monkeypatch):
    base = dx.load_base()
    monkeypatch.setattr(base.module.load_pool_pins, "__defaults__", (Path("/elsewhere"), "1" * 64))
    monkeypatch.setattr(base.module, "main", lambda argv: (_ for _ in ()).throw(AssertionError("main ran")))
    with pytest.raises(s1.Refusal, match="defaults are not POOL_PINS_PATH and POOL_PINS_SHA256"):
        d2m.run_base(base, [], req8["filled"][0], req8["filled"][1])


def test_the_filled_file_is_read_again_against_its_hash(req8, tmp_path, capsys):
    """representation_pass's main() loads the pins by the filled SHA-256: a file that differs from it refuses there
    (as if it changed after D-2's check), with the committed REQ-3 settings."""
    base = dx.load_base()
    other = tmp_path / "other.json"
    other.write_bytes(req8["hand"] + b" ")
    argv = ["--prepared", str(tmp_path), "--recipe", str(tmp_path / "r"), "--anchors", str(tmp_path / "a"),
            "--out", str(tmp_path / "o"), "--pool-pins", str(other)]
    assert d2m.run_base(base, argv, other.resolve(), req8["filled"][1]) == 2
    assert f"settings representation_pools hash to {sha256_file(other)}, expected {req8['filled'][1]}" in \
        capsys.readouterr().err
    assert not (tmp_path / "o").exists()


def test_main_runs_with_the_checked_pins_sha256(env, req8, rp_settings, wired, monkeypatch, tmp_path, capsys):
    """main() hands the run the --pool-pins SHA-256 that passed D-2's checks, not a hash taken later: a filled file that
    changes after the checks (one byte appended) refuses inside representation_pass, nothing written (fix round:
    d2-verify-code finding 2)."""
    filled = dx.write(tmp_path / "filled.json", req8["filled"][0].read_bytes())
    real = d2m.checked
    calls = []

    def checked(*args, **kwargs):
        result = real(*args, **kwargs)
        calls.append(result[2])
        filled[0].write_bytes(filled[0].read_bytes() + b" ")             # changed after every D-2 check passed
        return result
    monkeypatch.setattr(d2m, "checked", checked)
    argv = argv_of(env, rp_settings, tmp_path / "out", [req8["plant"], req8["decoy"]], True,
                   ("--pool-pins", dx.spec(filled), "--req8-record", dx.spec(req8["record"])))
    assert d2m.main(argv) == 2
    err = capsys.readouterr().err
    assert calls == [filled[1]]
    assert f"settings representation_pools hash to {sha256_file(filled[0])}, expected {filled[1]}" in err
    assert err.rstrip().endswith("(nothing written)") and not (tmp_path / "out").exists()


# ----- S3 pools: as before --------------------------------------------------------------------------------------------


def test_an_s3_pool_behaves_as_before(env, req8, rp_settings, wired, tmp_path):
    """An S3 pool alone (pools-only): pinned by its command-line SHA-256 under D-2 as under the W1 null pins; the rows
    file is byte-identical and the summary differs only in the pins' SHA-256 and filled lists."""
    items = [{"id": f"s3-{j}", "prompt": f"Synthetic S3 prompt {j} about lakes?", "response": f"Synthetic answer {j}."}
             for j in range(3)]
    pool = trp.pool_file(tmp_path, items, "s3_safe")
    assert d2m.main(d2_argv(env, rp_settings, req8, tmp_path / "out", [pool], True)) == 0
    mine = outputs(tmp_path / "out")
    w1 = rp.run(env.prepared, env.recipe, env.anchors, sfx.fixture_loaders(), env.settings, rp_settings[1], [pool], False)
    assert mine[rp.ROWS_FILE] == w1[rp.ROWS_FILE]
    a, b = json.loads(mine[rp.SUMMARY_FILE]), json.loads(w1[rp.SUMMARY_FILE])
    assert a["pools"] == b["pools"] and a["pools"][0]["pinned_by"] == "command line"
    assert (a["pool_pins"]["sha256"], a["pool_pins"]["filled"]) == (req8["filled"][1], ["decoy", "plant"])
    assert (b["pool_pins"]["sha256"], b["pool_pins"]["filled"]) == (dx.W1_PINS_SHA256, [])
    drop = (("costs",), ("pool_pins",), ("provenance", "inputs", "pool_pins"))
    assert canonical_json(dx.without(mine[rp.SUMMARY_FILE], *drop)) == canonical_json(dx.without(w1[rp.SUMMARY_FILE], *drop))


def test_an_s3_name_on_a_pinned_file_refuses_under_the_filled_pins(env, req8, rp_settings, wired, tmp_path, capsys):
    """The W1 rule once the pins are filled: an unlisted name on the plant pool's bytes refuses (the name and hash do
    not match); with the W1 null pins the same pool was scored by its command-line hash."""
    data = json.loads(req8["plant"][0].read_bytes())
    data["name"] = "s3_safe"
    path = tmp_path / "renamed.json"
    path.write_bytes(canonical_json(data))
    pool = (path, sha256_file(path))
    assert pool[1] != req8["plant"][1]                       # renaming changes the bytes: it is another file
    assert d2m.main(d2_argv(env, rp_settings, req8, tmp_path / "out", [pool], True)) == 0
    assert json.loads((tmp_path / "out" / rp.SUMMARY_FILE).read_bytes())["pools"][0]["pinned_by"] == "command line"
    fake = {"name": "s3_safe", "sha256": req8["plant"][1], "items": data["items"]}
    filled = rp.check_pool_pins(json.loads(req8["hand"]))
    with pytest.raises(s1.Refusal, match="the name and hash do not match"):
        rp.pin_of(fake, filled)
    assert rp.pin_of(fake, rp.load_pool_pins()[0]) == "command line"


# ----- main(): the D-2 checks run before representation_pass ----------------------------------------------------------


def _forbid_base_main(monkeypatch, wired):
    """Makes any call of the base module's main() fail the test (the D-2 checks must refuse first)."""
    real = fp.load_base

    def load_base(*args, **kwargs):
        base = real(*args, **kwargs)
        base.module.main = lambda argv: (_ for _ in ()).throw(AssertionError("representation_pass ran"))
        return base
    monkeypatch.setattr(fp, "load_base", load_base)


@pytest.mark.parametrize("case,match", [
    ("other_field", "not exactly in pools.decoy.sha256 and pools.plant.sha256"),
    ("wrong_hash", "the filled pin of pool plant"),
    ("unfilled", "not exactly in"),
    ("pins_sha", "the filled pins file hashes to"),
    ("record_sha", "REQ-8's record hashes to"),
    ("record_kind", "is not a version-1 'stage1 plant record'"),
    ("record_other_plant", "the filled pin of pool plant"),
    ("no_hash", "--pool-pins is PATH:SHA256"),
])
def test_main_refuses_before_representation_pass_runs(env, req8, rp_settings, wired, monkeypatch, tmp_path, capsys,
                                                       case, match):
    _forbid_base_main(monkeypatch, wired)
    filled, record = req8["filled"], req8["record"]
    if case == "other_field":
        doc = json.loads(req8["hand"])
        doc["pools"]["decoy"]["items"] = 36
        filled = dx.write(tmp_path / "f.json", canonical_json(doc))
    elif case == "wrong_hash":
        filled = dx.write(tmp_path / "f.json", dx.hand_fill(dx.w1_pins_bytes(), "5" * 64, req8["decoy"][1]))
    elif case == "unfilled":
        filled = (dx.w1_pins_path(), dx.W1_PINS_SHA256)
    elif case == "pins_sha":
        filled = (filled[0], "0" * 64)
    elif case == "record_sha":
        record = (record[0], "0" * 64)
    elif case == "record_kind":
        doc = dict(req8["record_doc"], kind="stage1 s-pool record")
        record = dx.write(tmp_path / "r.json", canonical_json(doc))
    elif case == "record_other_plant":
        doc = json.loads(json.dumps(req8["record_doc"]))
        doc["pools"]["plant"]["sha256"] = doc["full_files"]["plant.pool.json"] = "6" * 64
        record = dx.write(tmp_path / "r.json", canonical_json(doc))
    argv = argv_of(env, rp_settings, tmp_path / "out", [req8["plant"], req8["decoy"]], True,
                   ("--pool-pins", "no-hash" if case == "no_hash" else dx.spec(filled), "--req8-record", dx.spec(record)))
    assert d2m.main(argv) == 2
    err = capsys.readouterr().err
    assert match in err and err.rstrip().endswith("(nothing written)") and not (tmp_path / "out").exists()


def test_main_refuses_a_changed_representation_pass_or_w1_pins_byte(req8, tmp_path, monkeypatch, capsys):
    """checked() against a tmp root whose representation_pass.py or W1 pins file has one changed byte."""
    for what, rel, needle, new, match in (
            ("script", "script", b'RESERVED_POOL_NAMES = ("dev",)', b'RESERVED_POOL_NAMES = ("dex",)',
             "representation_pass.py hashes to"),
            ("pins", "pins", b'"items": 37', b'"items": 38', "the W1 pins file hashes to")):
        root = dx.fake_root(tmp_path / what)
        dx.flip(root / dx.committed_d2()["base"][rel], needle, new)
        with pytest.raises(s1.Refusal, match=match):
            d2m.checked(dx.spec(req8["filled"]), dx.spec(req8["record"]), root)
        monkeypatch.setattr(fp, "w1_root", lambda root=root: root)
        assert d2m.main(["--prepared", "p", "--recipe", "r", "--anchors", "a", "--out", str(tmp_path / "o"),
                         "--pool-pins", dx.spec(req8["filled"]), "--req8-record", dx.spec(req8["record"])]) == 2
        assert match in capsys.readouterr().err and not (tmp_path / "o").exists()
        monkeypatch.undo()


def test_main_refuses_a_changed_d2_settings_byte(req8, tmp_path, monkeypatch, capsys):
    copy_path = tmp_path / "d2_pool_pins.json"
    copy_path.write_bytes(fp.SETTINGS_PATH.read_bytes().replace(b'"record_version": 1', b'"record_version": 2'))
    monkeypatch.setattr(fp, "SETTINGS_PATH", copy_path)
    assert d2m.main(["--prepared", "p", "--recipe", "r", "--anchors", "a", "--out", str(tmp_path / "o"),
                     "--pool-pins", dx.spec(req8["filled"]), "--req8-record", dx.spec(req8["record"])]) == 2
    assert "settings d2_pool_pins hash to" in capsys.readouterr().err


def test_forwarded_arguments_are_representation_passs_own():
    import argparse

    args = argparse.Namespace(prepared=Path("P"), recipe=Path("R"), anchors=Path("A"), pool=["x:1", "y:2"],
                              pools_only=True, out=Path("O"), settings=Path("S"))
    assert d2m.forwarded(args, Path("/F")) == ["--prepared", "P", "--recipe", "R", "--anchors", "A", "--pool", "x:1",
                                                "--pool", "y:2", "--pools-only", "--out", "O", "--settings", "S",
                                                "--pool-pins", "/F"]
    args.pools_only, args.settings, args.pool = False, None, []
    assert d2m.forwarded(args, Path("/F")) == ["--prepared", "P", "--recipe", "R", "--anchors", "A", "--out", "O",
                                                "--pool-pins", "/F"]


def test_main_prints_the_d2_facts_text_free(e2e, req8):
    """The end-to-end's stdout: the D-2 line (hashes and counts), then representation_pass's own lines; no pool text."""
    first, *rest = e2e["stdout"].splitlines()
    assert first == (f"D-2: filled pins {req8['filled'][1]} (decoy {req8['decoy'][1]} 37 items, plant {req8['plant'][1]} "
                     f"75 items); representation_pass.py {dx.RP_SHA256}; W1 pins {dx.W1_PINS_SHA256}")
    assert rest[0].startswith("wrote 2 files into ")
    texts = [t for name in ("plant", "decoy") for i in json.loads(req8[name][0].read_bytes())["items"]
             for t in (i["prompt"], i["response"])]
    assert not any(t in e2e["stdout"] for t in texts if len(t) > 5)
    for data in e2e["out"].values():
        assert not any(t.encode() in data for t in texts if len(t) > 5)


def test_every_w1_file_is_byte_identical():
    """Section 19 point 1: every W1 manifest entry under scripts/stage1/ hashes to its pin."""
    root = fp.w1_root()
    data = json.loads((root / dx.committed_d2()["base"]["manifest"]).read_bytes())
    entries = [e for e in data["entries"] if e["path"].startswith("scripts/stage1/")]
    assert len(entries) > 100
    assert [e["path"] for e in entries if sha256_file(root / e["path"]) != e["sha256"]] == []
