"""The unit command (o_only, o_only_with_regenerate and the arm step at 7-8B): scripts/stage1_s1/oext_unit.py's own
main() run with a family's settings files, on ENGINEERING FIXTURES (the tiny engine units, the synthetic PHTest bank,
the scripted judge). Parity: the wrapper's outputs equal the 1B main's (called as the 1B tests call it, with the same
documents) byte for byte, wall-clock fields aside. Refusals: the other family's manifest, the pending branch, Branch
128's flags, the waits, a changed file, the Y variant on engine X; each names hashes, pins and flags, never text. The
module globals the wrapper sets are restored. None of these numbers is a scientific result."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

pytest.importorskip("torch")

import oext78_fixtures as f  # noqa: E402

w, ou, oe, uf, ofx = f.w, f.ou, f.oe, f.uf, f.ofx
w1 = oe.w1_18
EXACT = {"job.json", "identity.json", "dependencies.json", "assets.json", "oext_generations.jsonl",
         "oext_guard.jsonl", "oext_summary.json"}
REFUSALS: list[str] = []          # every refusal text seen in this module (the hashes-only test reads them)


def refused(result) -> str:
    code, out, err = result
    assert code == 2, (code, err[-300:])
    REFUSALS.append(out + err)
    return err


@pytest.fixture(scope="module")
def world128(tmp_path_factory):
    return ofx.kept(lambda: _env(tmp_path_factory.mktemp("u128"), "128"))


@pytest.fixture(scope="module")
def worldfull(tmp_path_factory):
    return ofx.kept(lambda: _env(tmp_path_factory.mktemp("ufull"), "full"))


def _env(base: Path, branch: str):
    env = f.unit_world(base, branch)
    env.unit_path, env.unit_sha, env.unit_doc = f.put_unit_settings(env)
    return env


def both(env, args_of, tmp: Path, **loader_options):
    """The wrapper's run and the 1B main's run on the same out path (the first folder moved aside): their folders."""
    out = tmp / "out"
    code, _, err = f.wrapper(env, ["unit", "--family", f.FAMILY, *args_of(out)], loaders=uf.loaders(**loader_options))
    assert code == 0, err[-500:]
    wrapped = out.rename(tmp / "out-wrapper")
    code, _, err = f.direct_unit(env, args_of(out), env.unit_doc, **loader_options)
    assert code == 0, err[-500:]
    return wrapped, out


# ----- parity ----------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", ["evaluated", "regen-source", "untuned"])
def test_the_wrapper_gives_the_1b_bytes_under_branch_128(world128, tmp_path, case):
    env = world128
    if case == "evaluated":
        args = lambda out: f.unit_args(env, out, run=env.world.units["evaluated"])            # noqa: E731
        exact = EXACT
    elif case == "regen-source":
        args = lambda out: f.unit_args(env, out, run=env.world.units["regen"],                # noqa: E731
                                       source=env.world.units["source"])
        exact = EXACT
    else:
        args = lambda out: f.unit_args(env, out, untuned=True)                                # noqa: E731
        exact = EXACT | {"dev100/generations.jsonl", "dev100/guard.jsonl"}
    wrapped, direct = both(env, args, tmp_path, perturb=(case == "untuned"))
    result = f.compare(wrapped, direct, exact)
    assert set(result.values()) <= {"bytes", "parsed"}, result
    job = json.loads((wrapped / "job.json").read_bytes())
    assert job["settings_sha256"] == env.unit_sha and job["oext"]["settings_sha256"] == env.inp.eval_sha
    assert job["oext"]["branch"] == "128" and job["oext"]["w1_18_record_sha256"] == env.inp.w1_18_sha256
    route = {"evaluated": "unit_eval", "regen-source": "source_unit", "untuned": "generated"}[case]
    assert job["dev100_route"] == route


def test_the_wrapper_gives_the_1b_bytes_under_branch_full(worldfull, tmp_path):
    env = worldfull
    args = lambda out: f.unit_args(env, out, run=env.world.units["regen"])                    # noqa: E731
    wrapped, direct = both(env, args, tmp_path)
    result = f.compare(wrapped, direct, EXACT | {"dev100/generations.jsonl", "dev100/guard.jsonl"})
    assert set(result.values()) <= {"bytes", "parsed"}, result
    assert json.loads((wrapped / "job.json").read_bytes())["oext"]["branch"] == "full"


def test_the_settings_path_label_is_the_file_that_was_read(world128, tmp_path):
    """GXB O3: the settings' oext.settings.path names the family's O-ext file, the file the run loaded; the 1B
    validator takes it only because the wrapper's OEXT_SETTINGS_PATH is that path."""
    env = world128
    assert env.unit_doc["oext"]["settings"] == {"path": env.fam.label("oext_eval"), "sha256": env.inp.eval_sha}
    with pytest.raises(f.s1.Refusal, match="oext names the O-ext module and its settings file"):
        ou.validate_settings(env.unit_doc)                         # the 1B literal path refuses the true label
    code, _, err = f.wrapper(env, ["unit", "--family", f.FAMILY,
                                   *f.unit_args(env, tmp_path / "o", run=env.world.units["evaluated"])],
                             loaders=uf.loaders())
    assert code == 0, err[-300:]
    shown = json.loads(err.splitlines()[0])
    assert shown["settings"] == {"oext_unit": env.unit_sha, "oext_eval": env.inp.eval_sha,
                                 "limits_overrefusal_checks": env.inp.w_sha}


def test_the_module_globals_are_restored_after_a_run_and_a_refusal(world128, tmp_path):
    before = (ou.load_pinned_settings, oe.load_pinned_settings, ou.OEXT_SETTINGS_PATH, w1.SETTINGS_PATH,
              w1.SETTINGS_SHA256)
    env = world128
    code, _, _ = f.wrapper(env, ["unit", "--family", f.FAMILY,
                                 *f.unit_args(env, tmp_path / "a", run=env.world.units["evaluated"])],
                           loaders=uf.loaders())
    assert code == 0
    assert (ou.load_pinned_settings, oe.load_pinned_settings, ou.OEXT_SETTINGS_PATH, w1.SETTINGS_PATH,
            w1.SETTINGS_SHA256) == before
    code, _, _ = f.wrapper(env, ["unit", "--family", f.FAMILY, *f.unit_args(env, tmp_path / "a",
                                                                            run=env.world.units["evaluated"])],
                           loaders=uf.loaders())
    assert code == 2                                        # the folder exists: the 1B plan refuses inside the call
    assert (ou.load_pinned_settings, oe.load_pinned_settings, ou.OEXT_SETTINGS_PATH, w1.SETTINGS_PATH,
            w1.SETTINGS_SHA256) == before
    assert ou.OEXT_SETTINGS_PATH == "scripts/stage1_s1/settings/oext_eval.json"
    assert w1.SETTINGS_SHA256 == "bfa9a56fd0522de066cb04b6f84b99dffda54fbe4b297dc3e4c7f07961c4a41b"


def test_the_binding_reads_the_familys_w1_18_settings(world128):
    """oext_eval's W1-18 binding (oext_eval.py:214-236) reads W1-18's module globals: with the family's file it
    passes, with the 1B globals the family's O-ext settings refuse (they name the family's W1-18 settings)."""
    env = world128
    with pytest.raises(f.s1.Refusal, match=env.inp.w_sha):
        oe.load_pinned_settings(env.inp.eval_path, env.inp.eval_sha)
    with w.patched([(w1, "SETTINGS_PATH", env.inp.w_path), (w1, "SETTINGS_SHA256", env.inp.w_sha)]):
        assert oe.load_pinned_settings(env.inp.eval_path, env.inp.eval_sha).doc["cap"]["branch"] == "128"


# ----- refusals --------------------------------------------------------------------------------------------------------


def test_the_other_familys_manifest_refuses(world128, tmp_path):
    env = world128
    fake = tmp_path / "other-prepared"
    fake.mkdir()
    (fake / "manifest.json").write_bytes(b'{"kind": "the other family"}')
    other = f.sha(fake / "manifest.json")
    saved = env.fam.other_manifest
    try:                                         # the module-scoped world gets its own value back (O5)
        env.fam.other_manifest = other
        err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY,
                                      *f.unit_args(env, tmp_path / "o", untuned=True, prepared=fake)]))
    finally:
        env.fam.other_manifest = saved
    assert "the other family's manifest" in err and other in err and env.world.manifest in err
    assert not (tmp_path / "o").exists()


def test_a_prepared_set_off_the_familys_pin_refuses_by_hash(world128, tmp_path):
    env = world128
    fake = tmp_path / "p"
    fake.mkdir()
    (fake / "manifest.json").write_bytes(b"{}")
    err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY,
                                  *f.unit_args(env, tmp_path / "o", untuned=True, prepared=fake)]))
    assert f.sha(fake / "manifest.json") in err and "other family" not in err


def test_the_pending_branch_refuses_in_the_wrapper_and_in_the_1b_code(tmp_path):
    env = _env(tmp_path / "pending", oe.PENDING)
    args = ["unit", "--family", f.FAMILY, *f.unit_args(env, tmp_path / "o", untuned=True, w1_18=False)]
    env.fam.waits = [{"pin": "W1_18_BRANCH", "event": "the family's 7-8B W1-18 check", "where": ["families.x.w1_18"],
                      "roles": ["oext_eval"]}]
    err = refused(f.wrapper(env, args))
    assert "the pin W1_18_BRANCH is null" in err and "W1-18 check" in err
    env.fam.waits = []                                          # without the wait, the 1B plan refuses (pending)
    err = refused(f.wrapper(env, args, loaders=uf.loaders()))
    assert "pending W1-18" in err
    assert not (tmp_path / "o").exists()


def test_branch_128_needs_the_familys_w1_18_record(world128, tmp_path):
    env = world128
    err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY,
                                  *f.unit_args(env, tmp_path / "o", untuned=True, w1_18=False)]))
    assert env.inp.w1_18_sha256 in err and "--w1-18-record is needed" in err
    other = tmp_path / "other-record.json"
    other.write_bytes(b'{"kind": "stage1 over-refusal checks"}')
    args = f.unit_args(env, tmp_path / "o", untuned=True, w1_18=False) + ["--w1-18-record", str(other)]
    err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY, *args]))
    assert f"--w1-18-record hashes to {f.sha(other)}" in err and env.inp.w1_18_sha256 in err
    assert not (tmp_path / "o").exists()


def test_a_full_reason_branch_takes_no_w1_18_record(tmp_path):
    env = _env(tmp_path / "reason", "full")
    _, _, doc = f.put_unit_settings(env)
    inp = f.oext_inputs(tmp_path / "reason-inputs", env.fam, branch="full", full_reason="W1-18 could not run (fixture)")
    env.inp = inp
    f.put_unit_settings(env)
    args = f.unit_args(env, tmp_path / "o", untuned=True, w1_18=False) + ["--w1-18-record", str(tmp_path / "x")]
    err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY, *args]))
    assert "pin no W1-18 record (branch full)" in err


def test_dev100_source_is_taken_on_a_regenerated_unit_under_branch_128_only(world128, worldfull, tmp_path):
    env = world128
    args = f.unit_args(env, tmp_path / "o", untuned=True, source=env.world.units["source"])
    err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY, *args]))
    assert "--dev100-source belongs to a regenerated unit" in err
    env = worldfull
    args = f.unit_args(env, tmp_path / "o", run=env.world.units["regen"], source=env.world.units["source"])
    err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY, *args]))
    assert "the branch is full" in err
    assert not (tmp_path / "o").exists()


@pytest.mark.parametrize("argv,needle", [
    (["unit", "--family", f.FAMILY, "transfer", "--untuned"], "DESO2 item 32"),
    (["unit", "--family", f.FAMILY, "run", "--untuned", "--dev100", "x"], "--dev100 is not a full flag name"),
    (["unit", "--family", f.FAMILY, "run", "--untuned", "-o", "x"], "-o is not a full flag name"),
    (["unit", "--family", "olmo2-1b", "run"], "--family must be one of"),
    (["unit", "run", "--untuned"], "--family is required"),
    (["lean", "--family", f.FAMILY, "--engine", "Y", "run"], "--engine for lean is one of ['X']"),
    (["w1_18", "--family", f.FAMILY, "--settings", "x"], "--settings is not a full flag name"),
    (["w1_18", "--family", f.FAMILY, "--extract-source-map"], "--extract-source-map is not a full flag name"),
    (["transfer_report", "--family", f.FAMILY], "the first argument must be one of"),
])
def test_commands_and_flags_outside_the_contract_refuse(world128, argv, needle):
    err = refused(f.wrapper(world128, argv))
    assert needle in err


def test_a_settings_file_off_its_index_pin_refuses(world128, tmp_path):
    env = world128
    path, digest = env.fam.files["oext_unit"]
    lead = env.fam.leading()
    original = path.read_bytes()
    try:
        path.write_bytes(original + b" ")
        code, out, err = f.call(w.main, ["unit", *lead, *f.unit_args(env, tmp_path / "o", untuned=True)])
    finally:
        path.write_bytes(original)
    refused((code, out, err))
    assert f"the index pins {digest}" in err and f.s1.sha256_bytes(original + b" ") in err


def test_the_index_must_be_the_one_the_job_names(world128, tmp_path):
    """R-5: no index hash lives in the wrapper; the index the job hands it must hash to the SHA-256 the job names,
    carry the family's and engine's name, and say so inside."""
    env = world128
    path, digest = env.fam.index("X")
    args = f.unit_args(env, tmp_path / "o", untuned=True)
    base = ["unit", "--family", f.FAMILY, "--index", str(path)]
    err = refused(f.call(w.main, [*base, "--index-sha256", "0" * 64, *args]))
    assert f"hashes to {digest}, the job names {'0' * 64}" in err
    err = refused(f.call(w.main, [*base, *args]))
    assert "--index and --index-sha256 are required" in err
    err = refused(f.call(w.main, ["unit", "--family", f.OTHER, "--index", str(path), "--index-sha256", digest, *args]))
    assert f"the {f.OTHER} engine-X index is OEXT-78B__{f.OTHER}.json" in err
    err = refused(f.call(w.main, ["unit", "--family", f.FAMILY, "--engine", "Y", "--index", str(path),
                                  "--index-sha256", digest, *args]))
    assert f"the {f.FAMILY} engine-Y index is OEXT-78B-Y__{f.FAMILY}.json" in err
    doc = json.loads(path.read_bytes())
    doc["engine"] = "Y"                                         # the right name, another engine inside
    wrong = f.write(path, doc)
    err = refused(f.call(w.main, [*base, "--index-sha256", wrong, *args]))
    assert "is not the scale78b O-ext index of olmo2-7b on engine X" in err
    assert not (tmp_path / "o").exists()


@pytest.mark.parametrize("command", ["unit", "lean", "w1_18"])
def test_every_command_refuses_a_changed_run_file(world128, tmp_path, monkeypatch, command):
    env = world128
    name = w.COMMAND_CODE[command][-1]
    monkeypatch.setitem(w.CODE, name, "1" * 64)
    tail = {"unit": ["run", "--untuned", "--out", str(tmp_path / "o")], "lean": ["run", "--out", str(tmp_path / "o")],
            "w1_18": ["--out", str(tmp_path / "o")]}[command]
    err = refused(f.call(w.main, [command, *env.fam.leading("W1" if command == "w1_18" else "X"), *tail]))
    assert f"{name} hashes to" in err and "1" * 64 in err
    assert not (tmp_path / "o").exists()


def test_the_unit_settings_manifest_must_be_the_indexs(tmp_path):
    env = _env(tmp_path / "m", "128")
    doc = json.loads(env.unit_path.read_bytes())
    doc["prepared"]["manifest_sha256"] = "9" * 64
    env.fam.put("oext_unit", doc)
    err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY, *f.unit_args(env, tmp_path / "o", untuned=True)]))
    assert "pins the manifest " + "9" * 64 in err and env.world.manifest in err


@pytest.mark.parametrize("label", ["scripts/stage1_s1/settings/oext_eval.json",
                                   "scripts/scale78b/settings/oext_eval__llama31-8b.json"])
def test_a_unit_settings_file_naming_another_oext_file_refuses(tmp_path, label):
    """GXB O3 (verifier O2): a settings file that names the 1B O-ext file, or the other family's, while the run reads
    the family's own file, refuses: the label comes from the index entry of the loaded file, never from the file."""
    env = _env(tmp_path / "l", "128")
    doc = json.loads(env.unit_path.read_bytes())
    doc["oext"]["settings"]["path"] = label
    env.fam.put("oext_unit", doc)
    err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY,
                                  *f.unit_args(env, tmp_path / "o", run=env.world.units["evaluated"])],
                            loaders=uf.loaders()))
    assert "oext names the O-ext module and its settings file" in err and not (tmp_path / "o").exists()


def test_the_globals_are_restored_when_the_1b_main_raises(world128, tmp_path):
    """Verifier O4: an exception (here argparse's SystemExit inside oext_unit.main, from a checkpoint the wrapper's
    flag check lets through) restores every global, tested on its own."""
    env = world128
    before = (ou.load_pinned_settings, oe.load_pinned_settings, ou.OEXT_SETTINGS_PATH, w1.SETTINGS_PATH,
              w1.SETTINGS_SHA256)
    args = f.unit_args(env, tmp_path / "o", run=env.world.units["evaluated"])
    args[args.index("--checkpoint") + 1] = "e9"
    with pytest.raises(SystemExit):
        w.main(["unit", *env.fam.leading(), *args], loaders=uf.loaders())
    assert (ou.load_pinned_settings, oe.load_pinned_settings, ou.OEXT_SETTINGS_PATH, w1.SETTINGS_PATH,
            w1.SETTINGS_SHA256) == before
    assert ou.load_pinned_settings.__name__ == "load_pinned_settings" and not (tmp_path / "o").exists()


def test_the_y_variant_refuses_on_engine_x(world128, tmp_path):
    """DESO2 item 24 (c): engine Y's files name engine Y's identity, so on engine X the unchanged 1B check refuses
    (by both identities), before any folder."""
    env = world128
    inp = f.oext_inputs(tmp_path / "y", env.fam, branch="128", engine_y=True)
    saved = env.inp
    try:
        env.inp = inp
        f.put_unit_settings(env, engine_y=True)
        args = f.unit_args(env, tmp_path / "o", untuned=True)
        err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY, "--engine", "Y", *args], loaders=uf.loaders()))
    finally:
        env.inp = saved
    assert f.ENGINE_Y_FIXTURE in err and "this engine is" in err
    assert not (tmp_path / "o").exists()


def test_every_refusal_names_hashes_pins_and_flags_never_text():
    assert REFUSALS, "the refusal tests ran first"
    texts = f.fixture_texts()
    for message in REFUSALS:
        assert not any(t in message for t in texts), message[:200]
        assert '"ok": false' in message and '"refused": ' in message
    hashed = [m for m in REFUSALS if "hashes to" in m or "manifest is" in m]
    assert hashed and all(f.hex64_in(m) for m in hashed)


@pytest.mark.parametrize("extra,needle", [
    (["--w1-18-rec", "x"], "--w1-18-rec is not a full flag name"),
    (["--dev100-sourc", "x"], "--dev100-sourc is not a full flag name"),
    (["--w1-18-record", "a", "--w1-18-record", "b"], "--w1-18-record is given 2 times"),
    (["--prepared=/nonexistent"], "--prepared is given 2 times"),
])
def test_flag_edges_refuse(world128, tmp_path, extra, needle):
    env = world128
    args = f.unit_args(env, tmp_path / "o", untuned=True, w1_18=False)
    err = refused(f.wrapper(env, ["unit", "--family", f.FAMILY, *args[:-2], *extra, *args[-2:]]))
    assert needle in err and not (tmp_path / "o").exists()
