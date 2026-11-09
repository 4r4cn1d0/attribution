"""refs_78b.py eval_adapter on ENGINEERING FIXTURES: the wrapper runs the unchanged B10 script with a family's per-seed
settings file and gives the 1B script's outputs (parity with the 1B main called as the 1B tests call it, with the same
documents), under the status dev100_recipe_cap and under oext_pinned with Track O's O-ext files (Branch 128); every
label names the file that was loaded; the globals are restored; and every refusal exits 2 before any folder. None of
these numbers is a scientific result."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402
import refs_fixtures as rf  # noqa: E402

from experiments.safety_selection.common import canonical_json, read_json, sha256_file  # noqa: E402
from scripts.scale78b import refs_78b as rw  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

oe = rf.oe
EXACT_EVAL = {f"eval/e1/{name}" for name in fb.EVAL_FILES}


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return rf.ea_world(tmp_path_factory.mktemp("refs-ea"))


@pytest.fixture(scope="module")
def regenerated(world):
    root = world.base / "regen"
    code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", root])
    assert code == 0, err[-400:]
    return root


def both(world, tmp_path: Path, argv_of, doc=None, *, exact=frozenset(), oext_doc=None, **loader_options):
    """The 1B main and the wrapper on the same out path (the 1B run's folder moved aside first); returns the
    comparison and both exit codes."""
    target = tmp_path / "out"
    c1, o1, e1 = rf.direct(world, argv_of(target), doc or world.doc, oext_doc=oext_doc, **loader_options)
    assert c1 == 0, e1[-400:]
    target.rename(tmp_path / "direct")
    c2, o2, e2 = rf.wrapped(world, argv_of(target), **loader_options)
    assert c2 == 0, e2[-400:]
    terms = sorted(target.rglob("*" + rw.TERMS_SUFFIX))                 # GXB R-38: the wrapper's own records, which
    for path in terms:                                                  # the 1B main does not write: set aside
        path.rename(tmp_path / path.name)
    assert json.loads(e2.splitlines()[0])["settings"]["eval_adapter"] == world.refs.files["eval_adapter"][1]
    return rf.compare(tmp_path / "direct", target, set(exact)), (o1, o2)


def test_regenerate_parity(world, tmp_path):
    cmp, (o1, o2) = both(world, tmp_path, lambda out: ["regenerate", *rf.common(world), "--seed", rf.SEED,
                                                       "--out", out])
    assert cmp["regeneration.json"] in ("bytes", "parsed", "hashes") and "differs" not in cmp.values(), cmp
    p1, p2 = json.loads(o1), json.loads(o2)
    assert p2["run_complete_sha256"] == sha256_file(tmp_path / "out" / "run" / "COMPLETE.json")
    assert {k: v for k, v in rf.strip(p1).items() if k != "run_complete_sha256"} == \
        {k: v for k, v in rf.strip(p2).items() if k != "run_complete_sha256"}


@pytest.mark.parametrize("mode, extra", [
    ("certify", []), ("scale", ["--lambda", "0.75", "CERT"]), ("prefix", ["--prefix-file", "PREFIX", "CERT"]),
    ("external", ["--external", "identity", "CERT"])])
def test_evaluate_parity_in_each_mode(world, regenerated, tmp_path, mode, extra):
    def argv(out):
        tail = []
        for item in extra:
            tail += fb.cert_args(world.cert) if item == "CERT" else [world.prefix] if item == "PREFIX" else [item]
        return ["evaluate", *rf.common(world), "--source-run", regenerated / "run", "--out", out, "--mode", mode, *tail]
    cmp, _ = both(world, tmp_path, argv, exact=EXACT_EVAL)
    assert "differs" not in cmp.values(), cmp
    assert cmp["job.json"] == "bytes" and cmp["COMPLETE.json"] in ("bytes", "parsed")


def test_the_gated_run_and_compare_parity(world, tmp_path):
    def argv(out):
        return ["run", *rf.common(world), "--seed", rf.SEED, "--regen-out", out / "regen", "--eval-root", out / "eval",
                "--evaluations", "certify,scale:0.75,prefix", "--prefix-file", world.prefix,
                "--gate-reference-eval", fb.eval_dir(world.unit)]
    cmp, (o1, o2) = both(world, tmp_path, argv, exact={f"eval/{rf.SEED}-certify/{n}" for n in EXACT_EVAL})
    assert "differs" not in cmp.values(), cmp
    assert cmp[f"eval/{rf.SEED}-certify.compare.json"] in ("bytes", "hashes")     # it names the unit's marker hash
    assert json.loads(o2)["certification"]["verdict"] == "pass"
    target = tmp_path / "cmp.json"
    code, _, err = rf.wrapped(world, ["compare", "--unit", tmp_path / "out" / "eval" / f"{rf.SEED}-certify",
                                      "--reference", world.unit / "COMPLETE.json", "--reference-eval",
                                      fb.eval_dir(world.unit), "--out", target])
    assert code == 0 and read_json(target)["verdict"] == "pass", err[-300:]
    assert target.read_bytes() == (tmp_path / "out" / "eval" / f"{rf.SEED}-certify.compare.json").read_bytes()


def test_every_record_names_the_files_that_ran(world, regenerated, tmp_path):
    """GXB O3: the job and the records name the 1B script that ran (its file hash) and the family file's SHA-256;
    no output names the 1B settings or any other settings file."""
    out = tmp_path / "scale"
    code, _, err = rf.wrapped(world, ["evaluate", *rf.common(world), "--source-run", regenerated / "run", "--out", out,
                                      "--mode", "scale", "--lambda", "0.5", *fb.cert_args(world.cert)])
    assert code == 0, err[-300:]
    job = read_json(out / "job.json")
    assert job["script_sha256"] == sha256_file(Path(ea.__file__).resolve()) == rw.CODE[rw.EA]
    assert job["settings_sha256"] == world.refs.files["eval_adapter"][1]
    blob = b"".join(p.read_bytes() for p in out.rglob("*") if p.is_file()).decode("utf-8", "replace")
    assert ea.SETTINGS_SHA256 not in blob and "settings/eval_adapter.json" not in blob
    assert "eval_adapter__" not in blob                               # no settings path label is written at all
    summary = json.loads(err.splitlines()[0])
    assert summary["settings"]["oext_eval"] == world.refs.files["oext_eval"][1]


def test_the_check_command_of_b10_reports_the_familys_pins(world):
    code, out, err = rf.wrapped(world, ["check", "--reference", f"{rf.SEED}={world.unit / 'COMPLETE.json'}"])
    assert code == 0, err[-300:]
    report = json.loads(out)
    assert report["settings_sha256"] == world.refs.files["eval_adapter"][1]
    assert report["oext"] == {"branch": world.refs.branch, "module_at_pin": True, "settings_at_pin": True}
    assert report["script_code_sha256"] == ea.script_code_sha256()      # B10's certified code: the 1B file's


def test_the_globals_are_restored_after_a_run_a_refusal_and_a_1b_exit(world, regenerated, tmp_path):
    before = rf.globals_now()
    assert rf.wrapped(world, ["check"])[0] == 0
    assert rf.globals_now() == before
    assert rf.wrapped(world, ["evaluate", *rf.common(world), "--source-run", regenerated / "run",
                              "--out", tmp_path / "x", "--mode", "scale", "--lambda", "0.8"])[0] == 2
    assert rf.globals_now() == before and not (tmp_path / "x").exists()
    with pytest.raises(SystemExit):                                     # argparse inside the 1B main
        rw.main(["eval_adapter", *world.refs.refs_leading(), "evaluate", "--mode", "certify"])
    assert rf.globals_now() == before


# ----- refusals (exit 2, nothing written) ------------------------------------------------------------------------


def test_the_index_and_its_files_are_checked(world, tmp_path):
    refs = world.refs
    path, digest = refs.refs_index()
    lead = ["--family", rf.FAMILY, "--seed", str(rf.SEED), "--index", str(path)]
    cases = {
        "sha": lead + ["--index-sha256", "0" * 64],
        "seed": ["--family", rf.FAMILY, "--seed", "1103", "--index", str(path), "--index-sha256", digest],
        "family": ["--family", rf.OTHER, "--seed", str(rf.SEED), "--index", str(path), "--index-sha256", digest],
        "untuned": ["--family", rf.FAMILY, "--seed", "1101", "--index", str(path), "--index-sha256", digest],
        "twice": lead + ["--index-sha256", digest, "--seed", str(rf.SEED)],
    }
    needles = {"sha": "hashes to", "seed": "seed-1103 index is", "family": "llama31-8b seed-1102 index is",
               "untuned": "must be a reference seed", "twice": "--seed is given twice"}
    for name, leading in cases.items():
        code, _, err = rf.call(rw.main, ["eval_adapter", *leading, "check"])
        assert code == 2 and needles[name] in err, (name, err[-300:])
    other = path.with_name(f"REFS-78B__{rf.FAMILY}__1103.json")
    shutil.copy(path, other)
    code, _, err = rf.call(rw.main, ["eval_adapter", "--family", rf.FAMILY, "--seed", "1103", "--index", str(other),
                                     "--index-sha256", digest, "check"])
    assert code == 2 and "is not the scale78b refs index of olmo2-7b seed 1103" in err
    leading = refs.refs_leading(files={**json.loads(path.read_bytes())["files"],
                                       "eval_adapter": {"file": refs.name("eval_adapter"), "sha256": "1" * 64}})
    code, _, err = rf.wrapped(world, ["check"], leading=leading)
    assert code == 2 and "the index pins 1111" in err


@pytest.mark.parametrize("argv_of, needle", [
    (lambda w, r: ["regenerate", *rf.common(w), "--seed", "1103", "--out", r / "x"], "is not this index's reference seed"),
    (lambda w, r: ["regenerate", "--prepared", w.prepared, "--recipe", w.recipe, "--reference", w.recipe, "--seed",
                   rf.SEED, "--out", r / "x"], "seed 1102's pinned a0 unit is"),
    (lambda w, r: ["regenerate", *rf.common(w), "--seed", rf.SEED, "--ou", r / "x"], "--ou is not a full flag name"),
    (lambda w, r: ["check", "--reference", f"1103={w.unit / 'COMPLETE.json'}"], "pin the seeds"),
    (lambda w, r: ["frobnicate"], "takes the 1B command"),
])
def test_a_refused_command_exits_2_and_writes_nothing(world, tmp_path, argv_of, needle):
    code, _, err = rf.wrapped(world, argv_of(world, tmp_path))
    assert code == 2 and needle in err, err[-300:]
    assert not (tmp_path / "x").exists()


def test_a_waiting_pin_refuses_with_its_event(world, tmp_path):
    refs = world.refs
    refs.waits = [{"pin": "REF_UNIT_1102", "event": "the fixture's event", "where": ["families.x.units.1102"],
                   "roles": ["eval_adapter"], "fields": {"eval_adapter": []}}]
    try:
        code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", tmp_path / "x"])
    finally:
        refs.waits = []
    assert code == 2 and "the pin REF_UNIT_1102 is null" in err and "the fixture's event" in err
    assert not (tmp_path / "x").exists()


def test_a_label_lie_refuses(world, tmp_path):
    """GXB O3: a B10 settings file whose O-ext pin names the 1B O-ext file (or whose Safe LoRA pin names the 1B Safe
    LoRA settings) refuses in the wrapper; and the 1B validator refuses it too under the wrapper's true label."""
    refs = world.refs
    for change, needle in (({"oext__settings": {"path": "scripts/stage1_s1/settings/oext_eval.json",
                                                "sha256": refs.files["oext_eval"][1]}}, "O-ext pin is not"),
                           ({"external_transforms": {"safe_lora": {**rf.sl_entry(refs), "settings": {
                               "path": "scripts/stage1_s1/settings/safe_lora.json",
                               "sha256": refs.files["safe_lora"][1]}}}}, "Safe LoRA pin is not"),
                           ({"external_transforms": {"safe_lora": {**rf.sl_entry(refs), "module_sha256": "1" * 64}}},
                            "is not the pinned scripts/stage1_s1/safe_lora.py")):
        doc = rf.ea_doc(world, refs, **change)
        refs.put("eval_adapter", doc)
        try:
            code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED,
                                              "--out", tmp_path / "x"])
            assert code == 2 and needle in err, err[-300:]
        finally:
            refs.put("eval_adapter", world.doc)
    with pytest.raises(ea.Refusal, match="the settings file is"):
        rf.settings_of(rf.ea_doc(world, refs, oext__settings={"path": "scripts/stage1_s1/settings/oext_eval.json",
                                                              "sha256": refs.files["oext_eval"][1]}), refs)


def test_the_other_familys_prepared_set_refuses(world, tmp_path):
    fake = tmp_path / "prepared"
    fake.mkdir()
    (fake / "manifest.json").write_bytes(b"{}")
    refs = world.refs
    refs.other_manifest = sha256_file(fake / "manifest.json")
    try:
        code, _, err = rf.wrapped(world, ["regenerate", "--prepared", fake, "--recipe", world.recipe, "--reference",
                                          world.unit / "COMPLETE.json", "--seed", rf.SEED, "--out", tmp_path / "x"])
    finally:
        refs.other_manifest = rf.OTHER_MANIFEST
    assert code == 2 and "the other family's manifest" in err and not (tmp_path / "x").exists()


def test_a_changed_run_file_refuses(world, monkeypatch, tmp_path):
    monkeypatch.setitem(rw.CODE, rw.EA, "0" * 64)
    code, _, err = rf.wrapped(world, ["check"])
    assert code == 2 and "the run files stay byte for byte" in err


def test_a_w1_18_record_is_not_taken_without_its_pin(world, regenerated, tmp_path):
    code, _, err = rf.wrapped(world, ["evaluate", *rf.common(world), "--source-run", regenerated / "run", "--out",
                                      tmp_path / "x", "--mode", "certify", "--w1-18-record", world.recipe])
    assert code == 2 and "--w1-18-record is not taken" in err and not (tmp_path / "x").exists()


def test_no_refusal_prints_fixture_text(world, tmp_path):
    texts = fb.harm_prompts(world.prepared) + [fb.PREFIX_TEXT]
    for argv in (["regenerate", *rf.common(world), "--seed", "1103", "--out", tmp_path / "x"],
                 ["evaluate", *rf.common(world), "--source-run", tmp_path, "--out", tmp_path / "y", "--mode", "prefix",
                  "--prefix-file", world.prefix]):
        code, out, err = rf.wrapped(world, argv)
        assert code == 2 and not any(t in out + err for t in texts)


# ----- O-ext (status oext_pinned, Branch 128): Track O's family files through the wrapper ------------------------


@pytest.fixture(scope="module")
def world128(tmp_path_factory):
    base = tmp_path_factory.mktemp("refs-ea-128")
    w = rf.ea_world(base, branch="128")
    w.doc = rf.oext_doc_for(w, w.refs)
    return w


def test_oext_parity_under_branch_128(world128, tmp_path):
    w = world128
    root = w.base / "regen-128"
    if not root.exists():
        assert rf.wrapped(w, ["regenerate", *rf.common(w), "--seed", rf.SEED, "--out", root])[0] == 0
    oext_args = ["--oext-bank", w.inp.bank, "--oext-record", w.inp.record, "--w1-18-record", w.inp.w1_18]

    def argv(out):
        return ["evaluate", *rf.common(w), "--source-run", root / "run", "--out", out, "--mode", "scale", "--lambda",
                "0.5", *fb.cert_args(w.cert), *oext_args]
    cmp, _ = both(w, tmp_path, argv, w.doc, exact=EXACT_EVAL | {f"eval/e1/{n}" for n in oe.OUTPUT_FILES},
                  oext_doc=w.inp.eval_doc)
    assert "differs" not in cmp.values(), cmp
    job = read_json(tmp_path / "out" / "job.json")
    assert job["oext"]["settings_sha256"] == w.refs.files["oext_eval"][1] and job["oext"]["branch"] == "128"
    assert job["oext"]["w1_18_record_sha256"] == w.inp.w1_18_sha256


def test_oext_flags_follow_the_familys_pin(world128, tmp_path):
    w = world128
    root = w.base / "regen-128"
    if not root.exists():
        assert rf.wrapped(w, ["regenerate", *rf.common(w), "--seed", rf.SEED, "--out", root])[0] == 0
    base = ["evaluate", *rf.common(w), "--source-run", root / "run", "--mode", "certify",
            "--oext-bank", w.inp.bank, "--oext-record", w.inp.record]
    code, _, err = rf.wrapped(w, [*base, "--out", tmp_path / "a"])
    assert code == 2 and "--w1-18-record is needed" in err and not (tmp_path / "a").exists()
    code, _, err = rf.wrapped(w, [*base, "--out", tmp_path / "b", "--w1-18-record", w.recipe])
    assert code == 2 and "--w1-18-record hashes to" in err and not (tmp_path / "b").exists()
    code, _, err = rf.wrapped(w, [*base, "--out", tmp_path / "c", "--w1-18-record", w.inp.w1_18])
    assert code == 0, err[-300:]
    assert (fb.eval_dir(tmp_path / "c") / oe.SUMMARY).is_file()


def test_check_validates_the_familys_oext_file(tmp_path):
    """The wrapper's check loads the family's O-ext file through the unchanged oext_eval loader (its W1-18 binding
    included): an O-ext file that the loader refuses exits 2, also while B10's own file is valid."""
    w = rf.ea_world(tmp_path / "w")
    refs = w.refs
    assert rf.call(rw.main, ["check", *refs.refs_leading()])[0] == 0
    doc = json.loads(refs.files["oext_eval"][0].read_bytes())
    doc["cap"]["w1_18"]["settings_sha256"] = "1" * 64                  # off W1-18's binding
    refs.put("oext_eval", doc)
    refs.put("eval_adapter", rf.ea_doc(w, refs))
    code, _, err = rf.call(rw.main, ["check", *refs.refs_leading()])
    assert code == 2 and "W1-18's settings are" in err, err[-300:]



# ----- the fix round: GXB R-34, R-38 and the verifier's targeted tests (RV-6) ---------------------------------------


def test_a_terms_record_is_written_beside_each_output(world, tmp_path):
    """GXB R-38: beside each output B10 wrote, the wrapper's record of what B10's 1B terms mean at 7-8B; nothing beside
    a refused command's output; a terms record that exists refuses before the call."""
    out = tmp_path / "regen"
    code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", out])
    assert code == 0, err[-300:]
    terms = tmp_path / ("regen" + rw.TERMS_SUFFIX)
    doc = json.loads(terms.read_bytes())
    assert (doc["kind"], doc["command"], doc["exit"], doc["output"], doc["family"], doc["seed"]) == (
        rw.TERMS_KIND, "regenerate", 0, "regen", rf.FAMILY, rf.SEED)
    assert doc["settings_sha256"] == world.refs.files["eval_adapter"][1] and doc["b10_sha256"] == rw.CODE[rw.EA]
    assert doc["writer_sha256"] == sha256_file(Path(rw.__file__).resolve())
    assert set(doc["terms"]) >= {"Gate A unit", "the untuned unit (theta0)", "lambda = 0"}
    assert "GXB R-35" in doc["terms"]["Gate A unit"] and "GXB R-34" in doc["terms"]["lambda = 0"]
    assert "unchanged" in doc["limit"]
    assert not any(p.name.endswith(rw.TERMS_SUFFIX) for p in out.rglob("*"))     # never inside B10's own folder
    code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", tmp_path / "x"])
    assert code == 0
    other = tmp_path / ("y" + rw.TERMS_SUFFIX)
    other.write_bytes(b"{}")
    code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", tmp_path / "y"])
    assert code == 2 and "nothing is overwritten" in err and not (tmp_path / "y").exists()
    code, _, _ = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", "1103", "--out", tmp_path / "z"])
    assert code == 2 and not (tmp_path / ("z" + rw.TERMS_SUFFIX)).exists()
    code, _, _ = rf.wrapped(world, ["evaluate", *rf.common(world), "--source-run", out / "run", "--out", tmp_path / "w",
                                    "--mode", "scale", "--lambda", "0.8"])                # B10 itself refuses (exit 2)
    assert code == 2 and not (tmp_path / "w").exists() and not (tmp_path / ("w" + rw.TERMS_SUFFIX)).exists()


def test_the_run_and_compare_write_their_terms_records(world, tmp_path):
    argv = ["run", *rf.common(world), "--seed", rf.SEED, "--regen-out", tmp_path / "r", "--eval-root", tmp_path / "e",
            "--evaluations", "certify", "--gate-reference-eval", fb.eval_dir(world.unit)]
    assert rf.wrapped(world, argv)[0] == 0
    assert all((tmp_path / (n + rw.TERMS_SUFFIX)).is_file() for n in ("r", "e"))
    code, _, err = rf.wrapped(world, ["compare", "--unit", tmp_path / "e" / f"{rf.SEED}-certify", "--reference",
                                      world.unit / "COMPLETE.json", "--reference-eval", fb.eval_dir(world.unit),
                                      "--out", tmp_path / "c.json"])
    assert code == 0 and json.loads((tmp_path / ("c.json" + rw.TERMS_SUFFIX)).read_bytes())["command"] == "compare"


@pytest.mark.parametrize("argv_of, needle", [
    (lambda w, r: ["check", "--untuned", w.unit / "COMPLETE.json"], "check --untuned is not run at 7-8B"),
    (lambda w, r: ["check", f"--untuned={w.unit / 'COMPLETE.json'}"], "check --untuned is not run at 7-8B"),
    (lambda w, r: ["compare", "--unit", r / "u", "--reference", w.unit / "COMPLETE.json", "--reference-eval",
                   r / "e", "--out", r / "x", "--against", "untuned"], "compare --against untuned is not run"),
    (lambda w, r: ["compare", "--unit", r / "u", "--reference", w.unit / "COMPLETE.json", "--reference-eval",
                   r / "e", "--out", r / "x", "--against=untuned"], "compare --against untuned is not run"),
])
def test_the_untuned_comparisons_are_refused_by_name(world, tmp_path, argv_of, needle):
    """GXB R-34."""
    code, _, err = rf.wrapped(world, argv_of(world, tmp_path))
    assert code == 2 and needle in err and not (tmp_path / "x").exists()


def test_T1_compare_reference_is_seed_s_pin(world, tmp_path):
    other = tmp_path / "other.json"
    other.write_bytes(b"{}")
    code, _, err = rf.wrapped(world, ["compare", "--unit", tmp_path / "u", "--reference", other, "--reference-eval",
                                      tmp_path / "e", "--out", tmp_path / "c.json"])
    assert code == 2 and "seed 1102's pinned a0 unit is" in err


def test_T2_evaluate_reference_is_seed_s_pin(world, tmp_path):
    code, _, err = rf.wrapped(world, ["evaluate", "--prepared", world.prepared, "--recipe", world.recipe, "--reference",
                                      world.recipe, "--source-run", tmp_path, "--out", tmp_path / "x", "--mode",
                                      "certify"])
    assert code == 2 and "seed 1102's pinned a0 unit is" in err and not (tmp_path / "x").exists()


def test_T3_run_seed_is_s(world, tmp_path):
    code, _, err = rf.wrapped(world, ["run", *rf.common(world), "--seed", "1103", "--regen-out", tmp_path / "r",
                                      "--eval-root", tmp_path / "e", "--evaluations", "certify"])
    assert code == 2 and "is not this index's reference seed" in err and not (tmp_path / "r").exists()


def test_T4_the_b10_files_manifest_is_the_indexs(world, tmp_path):
    refs = world.refs
    refs.put("eval_adapter", rf.ea_doc(world, refs, prepared__manifest_sha256="2" * 64))
    try:
        code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", tmp_path / "x"])
    finally:
        refs.put("eval_adapter", world.doc)
    assert code == 2 and "pins the manifest" in err and not (tmp_path / "x").exists()


def test_T5_the_index_kind_is_checked(world):
    code, _, err = rf.call(rw.main, ["check", *world.refs.refs_leading(kind="scale78b oext settings index")])
    assert code == 2 and "is not the scale78b refs index" in err


def test_T6_check_holds_the_bindings(world):
    refs = world.refs
    entry = {**rf.sl_entry(refs), "settings": {"path": refs.label("safe_lora"), "sha256": "1" * 64}}
    refs.put("eval_adapter", rf.ea_doc(world, refs, external_transforms={"safe_lora": entry}))
    try:
        code, _, err = rf.call(rw.main, ["check", *refs.refs_leading()])
    finally:
        refs.put("eval_adapter", world.doc)
    assert code == 2 and "Safe LoRA pin is not the index's safe_lora file" in err


def test_T7_a_non_digit_seed_exits_2():
    code, _, err = rf.call(rw.main, ["check", "--family", "olmo2-7b", "--seed", "11o2", "--index", "x",
                                     "--index-sha256", "0" * 64])
    assert code == 2 and "--seed is required" in err



# ----- the follow-up: GXB R-41 (RRV-2) and R-42 (RRV-3) -----------------------------------------------------------


def test_no_terms_record_beside_an_output_that_existed_before_the_call(world, tmp_path):
    """RRV-2, the re-verifier's probe: --out already holds an older file; B10 refuses (exit 2) and writes nothing, so
    the wrapper writes no terms record there. An empty folder that B10 then fills does get one."""
    held = tmp_path / "held"
    held.mkdir()
    (held / "older.txt").write_bytes(b"an older file")
    code, _, _ = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", held])
    assert code == 2 and not (tmp_path / ("held" + rw.TERMS_SUFFIX)).exists()
    assert sorted(p.name for p in held.iterdir()) == ["older.txt"]
    empty = tmp_path / "empty"
    empty.mkdir()
    code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", empty])
    assert code == 0, err[-300:]
    assert json.loads((tmp_path / ("empty" + rw.TERMS_SUFFIX)).read_bytes())["output"] == "empty"


@pytest.mark.parametrize("tail", [["--lambda", "0"], ["--lambda", "0.0"], ["--lambda=0"], ["--lambda=-0.0"]])
def test_lambda_0_is_refused_in_evaluate(world, regenerated, tmp_path, tail):
    """RRV-3 (GXB R-42)."""
    code, _, err = rf.wrapped(world, ["evaluate", *rf.common(world), "--source-run", regenerated / "run", "--out",
                                      tmp_path / "x", "--mode", "scale", *tail, *fb.cert_args(world.cert)])
    assert code == 2 and "lambda = 0 is not run at 7-8B" in err and not (tmp_path / "x").exists()
    assert not (tmp_path / ("x" + rw.TERMS_SUFFIX)).exists()


@pytest.mark.parametrize("specs", ["certify,scale:0", "certify,scale:0.75,scale:0.0", "scale:0"])
def test_lambda_0_is_refused_in_run(world, tmp_path, specs):
    code, _, err = rf.wrapped(world, ["run", *rf.common(world), "--seed", rf.SEED, "--regen-out", tmp_path / "r",
                                      "--eval-root", tmp_path / "e", "--evaluations", specs])
    assert code == 2 and "lambda = 0 is not run at 7-8B" in err
    assert not (tmp_path / "r").exists() and not (tmp_path / "e").exists()


def test_a_nonzero_scale_still_runs(world, regenerated, tmp_path):
    code, _, err = rf.wrapped(world, ["evaluate", *rf.common(world), "--source-run", regenerated / "run", "--out",
                                      tmp_path / "x", "--mode", "scale", "--lambda", "0.5", *fb.cert_args(world.cert)])
    assert code == 0, err[-300:]
