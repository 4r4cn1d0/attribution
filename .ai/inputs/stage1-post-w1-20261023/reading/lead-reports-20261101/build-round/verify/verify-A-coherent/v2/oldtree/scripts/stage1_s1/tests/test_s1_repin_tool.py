"""The block-B re-pin's two Mac tools on SYNTHETIC folders: repin_reference_seeds.py (the mid-block B10/B11 pins of a0
seeds 1104-1107 from the kit's readable records and recorded SHA-256; block-B pre-flight G4) on a synthetic kit and a
copy of the package's pinned files, both ways; and prefix_lengths.py (the count-only SP length script; G5) on the
ENGINEERING FIXTURE prepared set. No real kit record, unit or prompt is read; none of these numbers is a scientific
result."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402
import oext_fixtures as ofx  # noqa: E402

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402
from scripts.stage1_s1 import extract_a0_fingerprint as ex  # noqa: E402
from scripts.stage1_s1 import prefix_lengths as pl  # noqa: E402
from scripts.stage1_s1 import repin_reference_seeds as rp  # noqa: E402
from scripts.stage1_s1 import safe_lora as sl  # noqa: E402

FILES = rp.FILES
HOSTS = {1104: ("a-10", 3, "A"), 1105: ("b-1", 3, "B"), 1106: ("b-2", 3, "B"), 1107: ("b-3", 3, "B")}


def e1(seed: int) -> str:
    return sha256_bytes(f"synthetic e1 adapter of {seed}".encode())


def q(seed: int) -> str:
    return sha256_bytes(f"synthetic q adapter of {seed}".encode())


def b10_doc() -> dict:
    return s1.strict_json(ea.SETTINGS_PATH.read_bytes())


def package(root: Path) -> Path:
    """A copy of the package files the re-pin rewrites, at their repository paths, in a pinned state with no stage-1
    seed: this tree's files, with any seed 1104-1107 that a re-pin added taken out again through the tool's own cascade
    (so these tests hold before and after the lead's re-pins)."""
    for rel in (*FILES, rp.EXTRACTOR):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ea.REPO / rel, root / rel)
    pkg = rp.read_package(root)
    b10, b11 = pkg["b10"], pkg["b11"]
    if set(b10["reference_units"]) - set(rp.GATE_A_SEEDS):
        for seed in rp.STAGE1_SEEDS:
            b10["reference_units"].pop(seed, None)
            b11["adapter"]["accepted"].pop(seed, None)
        new, _ = rp.cascade(pkg, b10, b11)
        for rel, data in new.items():
            (root / rel).write_bytes(data)
    return root


def write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return sha256_bytes(data)


def kit(base: Path, seeds=(1105, 1106, 1107), *, record: bool = True, change_record=None, extra_job: bool = False,
        status: str = "complete", engine: str | None = None) -> Path:
    """A synthetic kit: plan.json with one complete a0_arm job per seed (after three other jobs), each host's
    JOB-DONE.json, the job's readable fingerprint record (listed among the outputs with its SHA-256) and a synthetic
    unit COMPLETE.json (hashed by the tool, never parsed)."""
    doc, plan = b10_doc(), {"hosts": {}}
    for seed in seeds:
        host, index, block = HOSTS[seed]
        tree = base / "retrieved" / host / "tree"
        unit = f"round1/{seed}-a0-e1-a1"
        complete = write(tree / unit / "COMPLETE.json", f'{{"synthetic": "COMPLETE.json of {seed}"}}\n'.encode())
        outputs = {f"job-{index}/cost-ledger.json": "c" * 64}
        if record:
            rec = {"kind": rp.RECORD_KIND, "version": 1, "job": index, "arm": "a0", "seed": seed, "unit": unit,
                   "complete_sha256": complete, "checkpoints": {"e1": e1(seed), "q": q(seed)},
                   "identity": {"manifest_sha256": doc["prepared"]["manifest_sha256"],
                                "training_identity": doc["recipe"]["training_identity"]}}
            if change_record is not None:
                change_record(rec)
            outputs[f"job-{index}/{rp.RECORD_NAME}"] = write(
                tree / f"job-{index}" / rp.RECORD_NAME, (json.dumps(rec, indent=1, sort_keys=True) + "\n").encode())
        jobs = [{"kind": "arm", "seed": seed, "status": "complete"} for _ in range(index)]
        jobs.append({"kind": "a0_arm", "seed": seed, "status": status, "unit": unit, "complete_sha256": complete,
                     "outputs": outputs})
        done = {"host": host, "jobs": [{"index": i, **j} for i, j in enumerate(jobs)], "ok": True}
        job_done = write(tree / "JOB-DONE.json", (json.dumps(done, indent=2) + "\n").encode())
        plan["hosts"][host] = {"block": block, "engine": "X", "engine_sha256": engine or doc["engine_x"],
                               "job_done_sha256": job_done, "jobs": jobs}
        if extra_job:
            plan["hosts"][f"{host}-again"] = copy.deepcopy(plan["hosts"][host])
    write(base / "plan.json", (json.dumps(plan, indent=1) + "\n").encode())
    return base


def run(root: Path, kitdir: Path, seeds: str, *extra) -> int:
    return rp.main(["--kit", str(kitdir), "--seeds", seeds, "--root", str(root), *[str(e) for e in extra]])


def hashes(root: Path) -> dict:
    return {rel: sha256_file(root / rel) for rel in FILES}


# ----- accepted ----------------------------------------------------------------------------------------------------


def test_the_repin_writes_every_pin_in_a_new_folder_and_keeps_the_certification(tmp_path, capsys):
    root, k = package(tmp_path / "repo"), kit(tmp_path / "kit")
    before = hashes(root)
    assert run(root, k, "1105,1106,1107", "--out", tmp_path / "out") == 0
    out = json.loads(capsys.readouterr().out)
    assert hashes(root) == before                                               # --out never touches the root
    new = tmp_path / "out"
    b10, b11 = s1.strict_json((new / rp.B10_JSON).read_bytes()), s1.strict_json((new / rp.B11_JSON).read_bytes())
    for seed in (1105, 1106, 1107):
        host, index, _ = HOSTS[seed]
        ref = b10["reference_units"][str(seed)]
        assert ref["fingerprint_prefixes"] == {"e1": e1(seed), "q": q(seed)}
        assert ref["complete_sha256"] == sha256_file(k / "retrieved" / host / "tree" / f"round1/{seed}-a0-e1-a1" /
                                                     "COMPLETE.json")
        assert ref["unit"] == f"stage1-olmo/retrieved/{host}/tree/round1/{seed}-a0-e1-a1"
        assert ref["role"].startswith(f"stage-1 block B a0_arm unit, seed {seed}, e1 (host {host}, job {index}")
        assert b11["adapter"]["accepted"][str(seed)] == {"fingerprint": e1(seed), "source_complete_sha256":
                                                         ref["complete_sha256"], "source_unit": ref["unit"]}
    assert rp.check_seed_pins(b10, b11) == ["1105", "1106", "1107"]
    assert b11["adapter"]["acceptance_rule"] == rp.NEW_RULE
    # every pin that hangs on the new settings, in one edit (addendum 11.7)
    b10_sha, b11_sha = sha256_file(new / rp.B10_JSON), sha256_file(new / rp.B11_JSON)
    assert f'SETTINGS_SHA256 = "{b10_sha}"' in (new / rp.B10_PY).read_text()
    assert f'SETTINGS_SHA256 = "{b11_sha}"' in (new / rp.B11_PY).read_text()
    assert b10["external_transforms"]["safe_lora"]["module_sha256"] == sha256_file(new / rp.B11_PY)
    assert b10["external_transforms"]["safe_lora"]["settings"]["sha256"] == b11_sha
    assert f'LITERAL = "{b10_sha}"' in (new / rp.TEST_B10).read_text()
    assert f'SAFE_LORA_SETTINGS_SHA256 = "{b11_sha}"' in (new / rp.TEST_B11).read_text()
    finds = {m["id"]: m["find"] for m in json.loads((new / rp.MUTANTS_B10).read_bytes())["mutants"]}
    assert sha256_file(new / rp.B11_PY) in finds["B10S-entry-module-old"] and b11_sha in finds["B10S-entry-settings-old"]
    b11_mutant = next(m for m in json.loads((new / rp.MUTANTS_B11).read_bytes())["mutants"]
                      if m["id"] == "B11-settings-pin-changed")
    assert b11_mutant["find"] == f'SETTINGS_SHA256 = "{b11_sha[:8]}'
    assert b11_mutant["replace"] == f'SETTINGS_SHA256 = "{"1" if b11_sha[0] == "0" else "0"}{b11_sha[1:8]}'
    assert (new / rp.B11_PY).read_text().count(b11_mutant["find"]) == 1
    ea.validate_settings(copy.deepcopy(b10))
    sl.validate_settings(copy.deepcopy(b11), b11_sha)
    # the certification stays valid: the certified settings and the script's code are unchanged
    assert out["certification"]["certified_settings_sha256"]["equal"] is True
    assert out["certification"]["script_code_sha256"]["equal"] is True
    old_doc = s1.strict_json((root / rp.B10_JSON).read_bytes())
    assert ea.certified_settings_sha256(ea.settings_from_doc(b10)) == ea.certified_settings_sha256(
        ea.settings_from_doc(old_doc))
    assert ea.script_code_sha256(new / rp.B10_PY) == ea.script_code_sha256(root / rp.B10_PY)
    assert {f["path"] for f in out["files"]} == set(FILES)
    assert out["kit_s1_code_pins"][rp.B10_JSON] == {"old": before[rp.B10_JSON], "new": b10_sha}
    assert [s["pack_input"]["name"] for s in out["seeds"]] == ["gate_a_complete:1105", "gate_a_complete:1106",
                                                               "gate_a_complete:1107"]


def test_the_repin_in_place_then_refuses_a_second_pin_of_the_same_seed(tmp_path, capsys):
    root, k = package(tmp_path / "repo"), kit(tmp_path / "kit")
    assert run(root, k, "1105", "--in-place") == 0
    capsys.readouterr()
    b10 = s1.strict_json((root / rp.B10_JSON).read_bytes())
    assert sorted(b10["reference_units"]) == ["1101", "1102", "1103", "1105"]
    after = hashes(root)
    assert run(root, k, "1105", "--in-place") == 2
    assert "pinned already" in capsys.readouterr().err and hashes(root) == after
    assert run(root, k, "1106,1107", "--in-place") == 0                          # a later seed on the re-pinned state
    b11 = s1.strict_json((root / rp.B11_JSON).read_bytes())
    assert rp.check_seed_pins(s1.strict_json((root / rp.B10_JSON).read_bytes()), b11) == ["1105", "1106", "1107"]


def test_a_lead_record_by_path_and_sha256_pins_1104_and_its_name_must_be_readable(tmp_path, capsys):
    """1104 (block A, sealed): the kit recorded no fingerprint record, so the tool names the missing readable source;
    a lead record given by path and SHA-256 is accepted only under a name the seal classes as readable."""
    root, k = package(tmp_path / "repo"), kit(tmp_path / "kit", seeds=(1104,), record=False)
    assert run(root, k, "1104", "--out", tmp_path / "none") == 2
    err = capsys.readouterr().err
    assert "no readable fingerprint record" in err and "job-3/a0-adapter-fingerprint.json" in err
    assert not (tmp_path / "none").exists()
    doc, unit = b10_doc(), "round1/1104-a0-e1-a1"
    rec = {"kind": rp.RECORD_KIND, "version": 1, "job": 3, "arm": "a0", "seed": 1104, "unit": unit,
           "complete_sha256": sha256_file(k / "retrieved/a-10/tree" / unit / "COMPLETE.json"),
           "checkpoints": {"e1": e1(1104), "q": None},
           "identity": {"manifest_sha256": doc["prepared"]["manifest_sha256"],
                        "training_identity": doc["recipe"]["training_identity"]}}
    data = canonical_json(rec)
    good, bad = tmp_path / "a0-1104-adapter-fingerprint.json", tmp_path / "a0-1104-fingerprint.json"
    good.write_bytes(data)
    bad.write_bytes(data)
    assert run(root, k, "1104", "--out", tmp_path / "x", "--record", f"1104={bad}={sha256_bytes(data)}") == 2
    assert "not a file the seal classes as readable" in capsys.readouterr().err
    assert run(root, k, "1104", "--out", tmp_path / "y", "--record", f"1104={good}={'0' * 64}") == 2
    assert "does not hash to the recorded" in capsys.readouterr().err
    assert run(root, k, "1104", "--out", tmp_path / "z", "--record", f"1104={good}={sha256_bytes(data)}") == 0
    b10 = s1.strict_json((tmp_path / "z" / rp.B10_JSON).read_bytes())
    assert b10["reference_units"]["1104"]["fingerprint_prefixes"] == {"e1": e1(1104), "q": None}
    assert b10["reference_units"]["1104"]["role"].startswith("stage-1 block A a0_arm unit, seed 1104")


def test_the_pattern_is_the_kits_readable_class():
    seal = (ea.ENGINE_REPO / "runkit" / "stage1-olmo" / "seal.py").read_text()
    line = next(x for x in seal.splitlines() if x.startswith("READABLE_PATTERNS = "))
    assert f'"{rp.READABLE_PATTERN}"' in line
    import fnmatch

    assert fnmatch.fnmatch(rp.RECORD_NAME, rp.READABLE_PATTERN) and not fnmatch.fnmatch("COMPLETE.json",
                                                                                      rp.READABLE_PATTERN)


# ----- refused (nothing written) ----------------------------------------------------------------------------------


def _tamper_record(base: Path) -> None:
    path = base / "retrieved/b-1/tree/job-3" / rp.RECORD_NAME
    path.write_bytes(path.read_bytes().replace(b'"version": 1', b'"version": 1 '))


def _tamper_job_done(base: Path) -> None:
    path = base / "retrieved/b-1/tree/JOB-DONE.json"
    path.write_bytes(path.read_bytes() + b"\n")


def _tamper_complete(base: Path) -> None:
    path = base / "retrieved/b-1/tree/round1/1105-a0-e1-a1/COMPLETE.json"
    path.write_bytes(path.read_bytes() + b" ")


TAMPERS = [
    ("record bytes", dict(), _tamper_record, "does not hash to the recorded"),
    ("JOB-DONE", dict(), _tamper_job_done, "job_done_sha256"),
    ("unit COMPLETE", dict(), _tamper_complete, "does not hash to plan.json's complete_sha256"),
    ("identity", dict(change_record=lambda r: r["identity"].update(training_identity="0" * 64)), None,
     "training identity"),
    ("e1 not hex", dict(change_record=lambda r: r["checkpoints"].update(e1="xyz")), None, "e1 adapter fingerprint"),
    ("other unit", dict(change_record=lambda r: r.update(unit="round1/other")), None, "another job, unit"),
    ("other kind", dict(change_record=lambda r: r.update(kind="stage1 regeneration acceptance")), None, "not a"),
    ("two jobs", dict(extra_job=True), None, "complete a0_arm jobs, not one"),
    ("not complete", dict(status="crashed"), None, "complete a0_arm jobs, not one"),
    ("engine", dict(engine="0" * 64), None, "another engine"),
]


@pytest.mark.parametrize("what, options, tamper, message", TAMPERS, ids=[t[0] for t in TAMPERS])
def test_a_source_that_is_not_the_kits_record_refuses(tmp_path, capsys, what, options, tamper, message):
    root, k = package(tmp_path / "repo"), kit(tmp_path / "kit", **options)
    if tamper is not None:
        tamper(k)
    before = hashes(root)
    assert run(root, k, "1105", "--out", tmp_path / "out") == 2, what
    assert message in capsys.readouterr().err
    assert not (tmp_path / "out").exists() and hashes(root) == before


@pytest.mark.parametrize("seeds", ["1103", "1108", "1105,1105", "x"])
def test_a_seed_outside_1104_1107_or_repeated_refuses(tmp_path, seeds):
    root, k = package(tmp_path / "repo"), kit(tmp_path / "kit")
    assert run(root, k, seeds, "--out", tmp_path / "out") == 2 and not (tmp_path / "out").exists()


def test_an_existing_out_folder_and_an_unknown_old_pin_refuse(tmp_path, capsys):
    root, k = package(tmp_path / "repo"), kit(tmp_path / "kit")
    (tmp_path / "out").mkdir()
    assert run(root, k, "1105", "--out", tmp_path / "out") == 2
    assert "new folder" in capsys.readouterr().err
    stray = root / "scripts/stage1_s1/tests/test_stray.py"
    stray.write_text(f'PIN = "{sha256_file(root / rp.B11_JSON)}"\n')
    assert run(root, k, "1105", "--out", tmp_path / "out2") == 2
    assert "does not re-take" in capsys.readouterr().err and not (tmp_path / "out2").exists()
    stray.write_text(json.dumps({"find": f'SETTINGS_SHA256 = "{sha256_file(root / rp.B10_JSON)[:8]}'}))
    assert run(root, k, "1105", "--out", tmp_path / "out2") == 2                  # a literal's 8-character form
    assert "does not re-take" in capsys.readouterr().err and not (tmp_path / "out2").exists()
    stray.unlink()
    (root / "scripts/stage1_s1/notes-x.json").write_text(f'"{sha256_file(root / rp.B11_JSON)}"\n')   # a report
    assert run(root, k, "1105", "--out", tmp_path / "out3") == 0


def test_a_package_whose_settings_are_not_at_their_literal_refuses(tmp_path, capsys):
    root, k = package(tmp_path / "repo"), kit(tmp_path / "kit")
    path = root / rp.B11_JSON
    path.write_bytes(path.read_bytes() + b"\n")
    assert run(root, k, "1105", "--out", tmp_path / "out") == 2
    assert "does not hash to its script's literal" in capsys.readouterr().err


def test_check_seed_pins_both_ways(tmp_path):
    pkg = rp.read_package(package(tmp_path / "repo"))
    b10, b11 = pkg["b10"], pkg["b11"]
    assert rp.check_seed_pins(b10, b11) == []
    ref = {"complete_sha256": "1" * 64, "fingerprint_prefixes": {"e1": e1(1105), "q": None},
           "role": "stage-1 block B a0_arm unit, seed 1105", "unit": "stage1-olmo/retrieved/b-1/tree/u"}
    acc = {"fingerprint": e1(1105), "source_complete_sha256": "1" * 64, "source_unit": ref["unit"]}
    good10, good11 = copy.deepcopy(b10), copy.deepcopy(b11)
    good10["reference_units"]["1105"], good11["adapter"]["accepted"]["1105"] = ref, acc
    assert rp.check_seed_pins(good10, good11) == ["1105"]
    for change in (lambda a, b: a["reference_units"].pop("1105"),
                   lambda a, b: b["adapter"]["accepted"]["1105"].update(fingerprint=e1(1106)),
                   lambda a, b: a["reference_units"]["1105"].update(role="Gate A a0 unit"),
                   lambda a, b: b["adapter"]["accepted"]["1105"].update(source_complete_sha256="2" * 64),
                   lambda a, b: a["reference_units"]["1105"]["fingerprint_prefixes"].update(e1=e1(1105)[:16]),
                   lambda a, b: (a["reference_units"].update({"1108": a["reference_units"].pop("1105")}),
                                 b["adapter"]["accepted"].update({"1108": b["adapter"]["accepted"].pop("1105")}))):
        bad10, bad11 = copy.deepcopy(good10), copy.deepcopy(good11)
        change(bad10, bad11)
        with pytest.raises(rp.Refusal):
            rp.check_seed_pins(bad10, bad11)


def test_the_certification_proof_refuses_a_certified_change_or_a_code_change():
    doc = b10_doc()
    code = ea.SETTINGS_PATH.parent.parent.joinpath("eval_adapter.py").read_bytes()
    assert rp.certification_proof(code, code.replace(ea.SETTINGS_SHA256.encode(), b"1" * 64), doc, doc)[
        "certified_settings_sha256"]["equal"]
    changed = copy.deepcopy(doc)
    changed["certification"]["gate"] = "another gate text"
    with pytest.raises(rp.Refusal, match="certifies"):
        rp.certification_proof(code, code, doc, changed)
    with pytest.raises(rp.Refusal, match="certifies"):
        rp.certification_proof(code, code + b"\n# one more line\n", doc, doc)


# ----- prefix_lengths.py: the count-only Mac script -------------------------------------------------------------------


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("prefix-lengths")
    prepared, manifest = fb.prepared(base)
    recipe_file = base / "recipe.json"
    recipe_file.write_bytes(canonical_json(fb.recipe()))
    return fb.namespace(base=base, prepared=prepared, manifest=manifest, recipe=recipe_file)


def script(world, tmp_path, text, *extra, oext_settings=None, **changes) -> int:
    path, digest = fb.write_prefix(tmp_path, text)
    pins = {"prefix__text_sha256": digest, "prefix__source": "ENGINEERING FIXTURE placeholder",
            "recipe__file_sha256": sha256_file(world.recipe), **changes}
    unit = tmp_path / "unit"                                   # fixture_doc reads a unit's pins; none is evaluated
    if not unit.exists():
        unit.mkdir()
        marker = {"checkpoints": {"e1": {"adapter_fingerprint": "a" * 64}, "q": {"adapter_fingerprint": "b" * 64}}}
        (unit / "COMPLETE.json").write_bytes(canonical_json(marker))
    settings = fb.fixture_settings(world.manifest, {1101: unit}, **pins)
    return pl.main(["--prepared", str(world.prepared), "--prefix-file", str(path), *[str(e) for e in extra]],
                   _settings=settings, _recipe=world.recipe, _codec=fb.fx.fixture_codec(), _oext_settings=oext_settings)


def test_the_script_prints_counts_per_bank_and_no_text(world, tmp_path, capsys):
    assert script(world, tmp_path, "y" * 10) == 0
    printed = capsys.readouterr().out
    out = json.loads(printed)
    from experiments.safety_selection.prepare import load_prepared

    data = load_prepared(world.prepared, banks=("dev",))
    for kind in ea.PREFIX_KINDS[:-1]:
        assert out["banks"][kind]["prompts"] == sum(i["kind"] == kind for i in data.banks["dev"]), kind
    assert out["banks"]["task_rows"]["prompts"] == len(data.query_rows) and out["over"] == 0
    assert out["banks"]["phtest"]["prompts"] == 0 and out["phtest_counted"] is False
    assert out["insert_tokens"] == 12 and set(out["banks"]["harm"]) == {"prompts", "largest_tokens", "limit",
                                                                        "limit_tokens", "over"}
    assert not any(t in printed for t in fb.harm_prompts(world.prepared)) and "yyyyyyyyyy" not in printed
    assert not any(i["prompt_id"] in printed for i in data.banks["dev"])


def test_the_script_counts_the_phtest_prompts_and_reports_an_over_long_prefix(world, tmp_path, capsys):
    inp = ofx.inputs(tmp_path / "oext", branch="128", cut=3, dev=2)
    assert script(world, tmp_path, "y" * 10, "--oext-bank", inp.bank, "--oext-record", inp.record,
                  "--w1-18-record", inp.w1_18, oext_settings=inp.settings) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["phtest_counted"] is True and out["banks"]["phtest"]["prompts"] == len(ofx.PHTEST_ROWS)
    long_dir = tmp_path / "long"
    long_dir.mkdir()
    assert script(world, long_dir, "y" * 380, "--oext-bank", inp.bank, "--oext-record", inp.record,
                  "--w1-18-record", inp.w1_18, oext_settings=inp.settings) == 1
    printed = capsys.readouterr().out
    out = json.loads(printed)
    assert out["over"] > 0 and out["banks"]["phtest"]["over"] == len(ofx.PHTEST_ROWS)
    assert not any(text in printed for _, text in ofx.PHTEST_ROWS)


def test_the_script_refuses_other_prefix_bytes_and_an_unpinned_prefix(world, tmp_path, capsys):
    path, digest = fb.write_prefix(tmp_path, "y" * 10)
    other = tmp_path / "other.txt"
    other.write_bytes(b"y" * 11)
    unit = tmp_path / "unit"
    unit.mkdir()
    (unit / "COMPLETE.json").write_bytes(canonical_json({"checkpoints": {"e1": {"adapter_fingerprint": "a" * 64},
                                                                         "q": {"adapter_fingerprint": "b" * 64}}}))
    pinned = fb.fixture_settings(world.manifest, {1101: unit}, prefix__text_sha256=digest,
                                 prefix__source="ENGINEERING FIXTURE placeholder",
                                 recipe__file_sha256=sha256_file(world.recipe))
    argv = ["--prepared", str(world.prepared), "--prefix-file", str(other)]
    assert pl.main(argv, _settings=pinned, _recipe=world.recipe, _codec=fb.fx.fixture_codec()) == 2
    assert "hashes to" in capsys.readouterr().err
    unpinned = fb.fixture_settings(world.manifest, {1101: unit}, prefix__text_sha256=None, prefix__source=None,
                                   recipe__file_sha256=sha256_file(world.recipe))
    argv = ["--prepared", str(world.prepared), "--prefix-file", str(path)]
    assert pl.main(argv, _settings=unpinned, _recipe=world.recipe, _codec=fb.fx.fixture_codec()) == 2
    assert "not pinned" in capsys.readouterr().err
    assert pl.main(argv, _settings=pinned, _recipe=world.recipe, _codec=fb.fx.fixture_codec()) == 0


# ----- extract_a0_fingerprint.py and the 1104 pin from its record (the lead's route (a); SYNTHETIC folders only) -----


SENTINEL = "SENTINEL-TRAINING-LOSS-7f3a91"
RECORD_1104 = "a0-1104-adapter-fingerprint.json"


def sealed_1104(base: Path, *, state: dict | None = None, raw_state: bytes | None = None, entry_class="sealed",
                state_entry: bool = True) -> SimpleNamespace:
    """A synthetic kit for 1104 (block A, no kit fingerprint record) with the unit's states/e1/state.json (the e1
    fingerprint beside engine-like fields and a sentinel training loss) and block A's seal listing the unit's
    COMPLETE.json and state.json by SHA-256, recorded in plan.json's seals."""
    k = kit(base, seeds=(1104,), record=False)
    tree, unit = k / "retrieved" / "a-10" / "tree", "round1/1104-a0-e1-a1"
    doc = {"adapter_fingerprint": e1(1104), "arm": "a0", "checkpoint": "e1", "seed": 1104, "step": 38,
           "trajectory_cost": {"train_loss": SENTINEL}, "training_loss": SENTINEL, "optimizer_fingerprint": "f" * 64}
    if state is not None:
        doc = state
    state_sha = write(tree / unit / "states" / "e1" / "state.json",
                      raw_state if raw_state is not None else json.dumps(doc, indent=1).encode())
    files = [{"class": "readable", "host": "a-10", "path": "JOB-DONE.json", "sha256": sha256_file(tree / "JOB-DONE.json")},
             {"class": "sealed", "host": "a-10", "path": f"{unit}/COMPLETE.json",
              "sha256": sha256_file(tree / unit / "COMPLETE.json")},
             {"class": "sealed", "host": "a-9", "path": f"{unit}/states/e1/state.json", "sha256": "0" * 64}]
    if state_entry:
        files.append({"class": entry_class, "host": "a-10", "path": f"{unit}/states/e1/state.json", "sha256": state_sha})
    seal_sha = write(k / "seals" / "block-A.json", canonical_json({"kind": "stage1 block seal", "block": "A",
                                                                   "files": files}))
    plan = json.loads((k / "plan.json").read_bytes())
    plan["seals"] = {"A": {"path": "seals/block-A.json", "sha256": seal_sha}}
    write(k / "plan.json", (json.dumps(plan, indent=1) + "\n").encode())
    return SimpleNamespace(kit=k, unit=tree / unit, complete=sha256_file(tree / unit / "COMPLETE.json"),
                           seal=k / "seals" / "block-A.json", seal_sha=seal_sha, state_sha=state_sha)


def extract(s, out: Path, capsys, **changes) -> tuple[int, str]:
    args = {"--unit-folder": s.unit, "--expect-complete-sha256": s.complete, "--seal": s.seal,
            "--expect-seal-sha256": s.seal_sha, "--out-dir": out, **changes}
    code = ex.main([str(x) for pair in args.items() for x in pair])
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def test_the_extractor_writes_only_the_e1_fingerprint_once(tmp_path, capsys):
    s = sealed_1104(tmp_path / "kit")
    out = tmp_path / "records"
    out.mkdir()
    code, printed = extract(s, out, capsys)
    assert code == 0 and SENTINEL not in printed
    path = out / RECORD_1104
    data = path.read_bytes()
    record = json.loads(data)
    assert json.loads(printed) == {"written": str(path), "sha256": sha256_bytes(data)}
    assert set(record) == {"kind", "unit", "complete_sha256", "state_sha256", "fingerprint", "seal_sha256", "utc",
                           "script_sha256"}
    assert (record["kind"], record["unit"], record["fingerprint"]) == (ex.KIND, "round1/1104-a0-e1-a1", e1(1104))
    assert (record["complete_sha256"], record["state_sha256"], record["seal_sha256"]) == (s.complete, s.state_sha,
                                                                                          s.seal_sha)
    assert record["script_sha256"] == sha256_file(ea.REPO / rp.EXTRACTOR) and ex.KEY_PATH == "adapter_fingerprint"
    import re
    import fnmatch

    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", record["utc"])
    assert fnmatch.fnmatch(path.name, rp.READABLE_PATTERN)
    for word in (SENTINEL, "training_loss", "trajectory_cost", "optimizer_fingerprint", "checkpoint", "step"):
        assert word.encode() not in data, word
    code, printed = extract(s, out, capsys)                                       # written once
    assert code == 2 and "written once" in printed and path.read_bytes() == data and SENTINEL not in printed


def _tamper_complete_bytes(s):
    (s.unit / "COMPLETE.json").write_bytes(b'{"tampered": 1}\n')


def _tamper_state_bytes(s):
    path = s.unit / "states" / "e1" / "state.json"
    path.write_bytes(path.read_bytes() + b" ")


EXTRACT_REFUSALS = [
    ("expected COMPLETE", dict(), None, {"--expect-complete-sha256": "1" * 64}, "expected and sealed"),
    ("COMPLETE not the sealed one", dict(), _tamper_complete_bytes, {}, "expected and sealed"),
    ("state not the sealed one", dict(), _tamper_state_bytes, {}, "not the sealed one"),
    ("seal SHA-256", dict(), None, {"--expect-seal-sha256": "2" * 64}, "expected seal"),
    ("no state entry", dict(state_entry=False), None, {}, "no single sealed entry"),
    ("readable entry", dict(entry_class="readable"), None, {}, "no single sealed entry"),
    ("no fingerprint key", dict(state={"training_loss": SENTINEL, "fingerprint": e1(1104)}), None, {},
     "no top-level adapter_fingerprint"),
    ("fingerprint not hex", dict(state={"adapter_fingerprint": SENTINEL, "training_loss": SENTINEL}), None, {},
     "not 64 lowercase hex"),
    ("fingerprint upper case", dict(state={"adapter_fingerprint": e1(1104).upper(), "training_loss": SENTINEL}), None,
     {}, "not 64 lowercase hex"),
    ("state not JSON", dict(raw_state=b'{"training_loss": "' + SENTINEL.encode() + b'", '), None, {},
     "no top-level adapter_fingerprint"),
    ("state a list", dict(raw_state=json.dumps([SENTINEL]).encode()), None, {}, "no top-level adapter_fingerprint"),
]


@pytest.mark.parametrize("what, build, tamper, args, message", EXTRACT_REFUSALS, ids=[r[0] for r in EXTRACT_REFUSALS])
def test_the_extractor_refuses_without_writing_or_printing_a_value(tmp_path, capsys, what, build, tamper, args,
                                                                    message):
    s = sealed_1104(tmp_path / "kit", **build)
    if tamper is not None:
        tamper(s)
    out = tmp_path / "records"
    out.mkdir()
    code, printed = extract(s, out, capsys, **args)
    assert code == 2 and message in printed, (what, printed)
    assert SENTINEL not in printed and e1(1104) not in printed and list(out.iterdir()) == []


def test_the_extractor_refuses_a_folder_outside_the_kit_layout_another_unit_or_no_output_folder(tmp_path, capsys):
    s = sealed_1104(tmp_path / "kit")
    out = tmp_path / "records"
    out.mkdir()
    loose = tmp_path / "loose" / "1104-a0-e1-a1"
    shutil.copytree(s.unit, loose)
    assert extract(s, out, capsys, **{"--unit-folder": loose})[0] == 2
    edit = s.unit.parent / "1104-edit-abc-e1-a1"
    shutil.copytree(s.unit, edit)
    code, printed = extract(s, out, capsys, **{"--unit-folder": edit})
    assert code == 2 and "not an a0 e1 unit" in printed
    code, printed = extract(s, out, capsys, **{"--out-dir": tmp_path / "missing"})
    assert code == 2 and "output folder" in printed and list(out.iterdir()) == []


def made_record(tmp_path: Path, capsys) -> tuple[SimpleNamespace, Path]:
    s = sealed_1104(tmp_path / "kit")
    out = tmp_path / "records"
    out.mkdir()
    assert extract(s, out, capsys)[0] == 0
    return s, out / RECORD_1104


def test_the_1104_pin_takes_the_extract_record(tmp_path, capsys):
    s, record = made_record(tmp_path, capsys)
    root = package(tmp_path / "repo")
    digest = sha256_file(record)
    assert run(root, s.kit, "1104", "--out", tmp_path / "out", "--record", f"1104={record}={digest}") == 0
    out = json.loads(capsys.readouterr().out)
    b10 = s1.strict_json((tmp_path / "out" / rp.B10_JSON).read_bytes())
    b11 = s1.strict_json((tmp_path / "out" / rp.B11_JSON).read_bytes())
    ref = b10["reference_units"]["1104"]
    assert ref["complete_sha256"] == s.complete and ref["fingerprint_prefixes"] == {"e1": e1(1104), "q": None}
    assert ref["role"].startswith("stage-1 block A a0_arm unit, seed 1104, e1 (host a-10, job 3")
    assert ref["role"].endswith(f"and {RECORD_1104}") and ref["unit"] == "stage1-olmo/retrieved/a-10/tree/round1/1104-a0-e1-a1"
    assert b11["adapter"]["accepted"]["1104"] == {"fingerprint": e1(1104), "source_complete_sha256": s.complete,
                                                  "source_unit": ref["unit"]}
    assert rp.check_seed_pins(b10, b11) == ["1104"] and out["certification"]["certified_settings_sha256"]["equal"]
    assert out["seeds"][0]["pack_input"] == {"name": "gate_a_complete:1104", "sha256": s.complete,
                                             "path": str(s.unit / "COMPLETE.json")}


def _rewrite(record: Path, change) -> str:
    doc = json.loads(record.read_bytes())
    change(doc)
    record.write_bytes((json.dumps(doc, indent=1, sort_keys=True) + "\n").encode())
    return sha256_file(record)


EXTRACT_PIN_REFUSALS = [
    ("state hash", lambda d: d.update(state_sha256="3" * 64), None, "does not list"),
    ("seal hash", lambda d: d.update(seal_sha256="4" * 64), None, "recorded seal"),
    ("script", lambda d: d.update(script_sha256="5" * 64), None, "not made by this repository"),
    ("unit", lambda d: d.update(unit="round1/1104-a0-e1-a2"), None, "another unit"),
    ("COMPLETE", lambda d: d.update(complete_sha256="6" * 64), None, "another unit or COMPLETE"),
    ("extra key", lambda d: d.update(q="7" * 64), None, "exactly"),
    ("fingerprint", lambda d: d.update(fingerprint="xyz"), None, "fingerprint"),
    ("pulled state changed", None, lambda s: (s.unit / "states/e1/state.json").write_bytes(b"{}"), "not the sealed one"),
    ("no seals record", None, lambda s: write(s.kit / "plan.json", (json.dumps(
        {k: v for k, v in json.loads((s.kit / "plan.json").read_bytes()).items() if k != "seals"}) + "\n").encode()),
     "no seal of block A"),
]


@pytest.mark.parametrize("what, change, tamper, message", EXTRACT_PIN_REFUSALS, ids=[r[0] for r in EXTRACT_PIN_REFUSALS])
def test_the_1104_pin_refuses_an_extract_record_that_is_not_the_sealed_units(tmp_path, capsys, what, change, tamper,
                                                                              message):
    s, record = made_record(tmp_path, capsys)
    digest = _rewrite(record, change) if change is not None else sha256_file(record)
    if tamper is not None:
        tamper(s)
    root = package(tmp_path / "repo")
    before = hashes(root)
    assert run(root, s.kit, "1104", "--out", tmp_path / "out", "--record", f"1104={record}={digest}") == 2, what
    assert message in capsys.readouterr().err, what
    assert not (tmp_path / "out").exists() and hashes(root) == before


def test_the_extractor_checks_complete_against_the_seal_even_when_the_expected_hash_agrees(tmp_path, capsys):
    s = sealed_1104(tmp_path / "kit")
    _tamper_complete_bytes(s)
    out = tmp_path / "records"
    out.mkdir()
    code, printed = extract(s, out, capsys, **{"--expect-complete-sha256": sha256_file(s.unit / "COMPLETE.json")})
    assert code == 2 and "expected and sealed" in printed and list(out.iterdir()) == []
