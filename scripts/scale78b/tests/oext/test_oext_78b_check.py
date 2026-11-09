"""The wrapper's $0 check (the fix round's R-6 and R-9) and W1-18's process hygiene, on W1-18's own ENGINEERING FIXTURES
(synthetic units, a fake decoder and a fake judge; test_limits_fixtures):
- R-6: a pinned W1-18 record is read on the Mac by the unchanged oext_eval reader under the family's O-ext settings and
  W1-18 globals: the right record passes; a wrong-family, stale or wrong-branch record, a record of other units, and a
  missing record refuse (exit 2, nothing written);
- R-9: each side unit's COMPLETE.json, read by its pin, lists every file W1-18 reads by name and SHA-256, and the
  present files hash to it (bytes hashed, never parsed); an unlisted file, a changed file, a COMPLETE.json off its pin
  and a job.json off its pin are each reported and refuse;
- W1-18 for both families in one process, each record naming its own settings; the globals restored when the 1B
  main raises. None of these numbers is a scientific result."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import oext78_fixtures as f
import test_limits_fixtures as tf

w, oe, ofx, mk, s1 = f.w, f.oe, f.ofx, f.mk, f.s1
w1 = oe.w1_18
ORIG_W1 = (w1.SETTINGS_PATH, w1.SETTINGS_SHA256)
TOOLS = {"device": "test", "judge": "a fake judge", "decoder": "a fake decoder"}
KINDS = {"B-1101": "A", "G16-1101": "D"}                    # both pass W1-18's bar


@pytest.fixture
def fake_tools(monkeypatch):
    def tools(doc, device, ledger_dir, guard_batch_size=None):
        return tf.fake_judge_records, tf.fake_decode, TOOLS

    monkeypatch.setattr(w1, "real_tools", tools)


def family_with_record(tmp_path: Path, *, kinds=KINDS) -> tuple[f.Family, Path, Path]:
    """A family whose W1-18 settings name synthetic units; its W1-18 record made by the wrapper; the data root."""
    root = tmp_path / "data"
    settings, _, _ = tf.build_checks(root, kinds)
    fam = f.Family(tmp_path / "fam")
    fam.manifest, fam.branch = settings["prepared"]["manifest_sha256"], "128"
    fam.put("limits_overrefusal_checks", settings)
    code, _, err = f.wrapper(fam, ["w1_18", "--family", f.FAMILY, "--out", str(tmp_path / "w"), "--data-root",
                                   str(root)])
    assert code == 0, err[-300:]
    return fam, tmp_path / "w" / w1.OUTPUT, root


def pin_record(fam: f.Family, record: Path | None, *, branch: str = "128") -> None:
    """The family's O-ext settings (the 1B shape at W1-18's cut and bar) pinning ``record`` under ``branch``."""
    doc = ofx.settings_doc(branch=branch, cut=128, dev=100, w1_18_sha256=None if record is None else f.sha(record))
    doc["cap"]["w1_18"]["settings_sha256"] = fam.files["limits_overrefusal_checks"][1]
    fam.put("oext_eval", doc)
    fam.branch = branch


def check(fam: f.Family, *extra: str):
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, *extra])
    return code, (json.loads(out) if code == 0 else None), err


# ----- R-6 ---------------------------------------------------------------------------------------------------------


def test_the_pinned_record_passes_the_check(tmp_path, fake_tools):
    fam, record, _ = family_with_record(tmp_path)
    pin_record(fam, record)
    code, report, err = check(fam, "--w1-18-record", str(record))
    assert code == 0, err[-300:]
    assert report["w1_18_record"] == {"record_sha256": f.sha(record), "branch": "128", "units": 2,
                                      "settings_sha256": fam.files["limits_overrefusal_checks"][1], "consistent": True}
    assert report["settings"] == {"limits_overrefusal_checks": "valid", "oext_eval": "valid"}


def test_a_record_of_the_other_family_refuses(tmp_path, fake_tools):
    """The record of another family's W1-18 settings, pinned by mistake (its hash is the pin): oext_eval's reader
    refuses it by its provenance."""
    fam, _, _ = family_with_record(tmp_path / "a")
    other, other_record, _ = family_with_record(tmp_path / "b", kinds={"G-1101": "B", "B-1101": "A"})
    pin_record(fam, other_record)
    code, _, err = check(fam, "--w1-18-record", str(other_record))
    assert code == 2 and "not made under the pinned W1-18 settings" in err


def test_a_stale_record_refuses(tmp_path, fake_tools):
    """A record made under an earlier version of the family's W1-18 settings (here: before a pin was edited)."""
    fam, record, _ = family_with_record(tmp_path)
    doc = json.loads(fam.files["limits_overrefusal_checks"][0].read_bytes())
    doc["requirement"] = doc["requirement"] + " (edited after the run)"
    fam.put("limits_overrefusal_checks", doc)
    pin_record(fam, record)
    code, _, err = check(fam, "--w1-18-record", str(record))
    assert code == 2 and "not made under the pinned W1-18 settings" in err


def test_a_record_whose_verdict_is_not_the_branch_refuses(tmp_path, fake_tools):
    fam, record, _ = family_with_record(tmp_path, kinds={"G-1101": "B"})              # fails the bar
    pin_record(fam, record, branch="128")
    code, _, err = check(fam, "--w1-18-record", str(record))
    assert code == 2 and "so the branch is full, not 128" in err
    pin_record(fam, record, branch="full")
    assert check(fam, "--w1-18-record", str(record))[0] == 0


def test_a_record_of_other_units_and_a_missing_record_refuse(tmp_path, fake_tools):
    fam, record, _ = family_with_record(tmp_path)
    doc = json.loads(record.read_bytes())
    doc["units"] = {"another": doc["units"]["B-1101"]}
    other = tmp_path / "other-units.json"
    f.write(other, doc)
    pin_record(fam, other)
    code, _, err = check(fam, "--w1-18-record", str(other))
    assert code == 2 and "lists 1 units, not the family's 2 W1-18 units" in err
    pin_record(fam, record)
    code, _, err = check(fam)
    assert code == 2 and f"pin W1-18's record {f.sha(record)}: give it with --w1-18-record" in err
    pin_record(fam, None, branch=oe.PENDING)
    code, _, err = check(fam, "--w1-18-record", str(record))
    assert code == 2 and "the settings pin no W1-18 record, so none is read" in err


# ----- R-9 ---------------------------------------------------------------------------------------------------------


def side_units_family(tmp_path: Path):
    root = tmp_path / "data"
    settings, _, _ = tf.build_checks(root, KINDS)
    fam = f.Family(tmp_path / "fam")
    fam.manifest, fam.branch = settings["prepared"]["manifest_sha256"], oe.PENDING
    fam.put("limits_overrefusal_checks", settings)
    pin_record(fam, None, branch=oe.PENDING)
    return fam, settings, root


def test_every_side_unit_lists_the_files_w1_18_reads(tmp_path):
    fam, settings, root = side_units_family(tmp_path)
    code, report, err = check(fam, "--data-root", str(root))
    assert code == 0, err[-300:]
    units = report["side_units"]["units"]
    assert sorted(units) == sorted(settings["units"]) and report["side_units"]["problems"] == []
    for name, unit in units.items():
        ck = settings["units"][name]["checkpoint"]
        assert set(unit["files"]) == {"job.json", f"eval/{ck}/generations.jsonl", f"eval/{ck}/guard.jsonl"}
        assert all(e["state"] == "listed" and f.hex64_in(e["sha256"]) for e in unit["files"].values())
        assert unit["job_pin"] == "equal"
    assert not any(t in json.dumps(report) for t in tf.SENTINELS)            # names and hashes only


def _rewrite_complete(settings: dict, root: Path, name: str, change) -> None:
    folder = root / settings["units"][name]["path"]
    marker = json.loads((folder / "COMPLETE.json").read_bytes())
    change(marker)
    settings["units"][name]["complete_sha256"] = f.write(folder / "COMPLETE.json", marker)


@pytest.mark.parametrize("case,needle", [
    ("unlisted", "COMPLETE.json lists no SHA-256 for eval/e1/guard.jsonl"),
    ("changed", "eval/e1/generations.jsonl does not hash to the listed"),
    ("complete-off-pin", "COMPLETE.json hashes to"),
    ("job-off-pin", "job.json is "),
])
def test_a_side_unit_that_does_not_list_or_hold_w1_18s_files_refuses(tmp_path, case, needle):
    fam, settings, root = side_units_family(tmp_path)
    name = "B-1101"
    folder = root / settings["units"][name]["path"]
    if case == "unlisted":
        _rewrite_complete(settings, root, name, lambda m: m["files"].pop("eval/e1/guard.jsonl"))
    elif case == "changed":
        (folder / "eval" / "e1" / "generations.jsonl").write_bytes(b"{}\n")
    elif case == "complete-off-pin":
        settings["units"][name]["complete_sha256"] = "c" * 64
    else:
        settings["units"][name]["job_sha256"] = "d" * 64
    fam.put("limits_overrefusal_checks", settings)
    pin_record(fam, None, branch=oe.PENDING)                  # the O-ext settings name the edited W1-18 settings
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and needle in out + err, (out[-300:], err[-300:])
    assert not any(t in out + err for t in tf.SENTINELS)


# ----- W1-18 in one process ----------------------------------------------------------------------------------------


def test_w1_18_for_both_families_in_one_process_names_each_familys_settings(tmp_path, fake_tools):
    records, shas = {}, {}
    for family, kinds in (("olmo2-7b", {"B-1101": "A"}), ("llama31-8b", {"G-1101": "B", "G16-1101": "D"})):
        root = tmp_path / f"data-{family}"
        settings, _, _ = tf.build_checks(root, kinds)
        fam = f.Family(tmp_path / f"fam-{family}", family)
        fam.manifest, fam.branch = settings["prepared"]["manifest_sha256"], oe.PENDING
        _, shas[family] = fam.put("limits_overrefusal_checks", settings)
        out = tmp_path / f"w-{family}"
        code, _, err = f.wrapper(fam, ["w1_18", "--family", family, "--out", str(out), "--data-root", str(root)])
        assert code == 0, err[-300:]
        assert (w1.SETTINGS_PATH, w1.SETTINGS_SHA256) == ORIG_W1
        records[family] = json.loads((out / w1.OUTPUT).read_bytes())
    for family in records:
        assert records[family]["provenance"]["settings_sha256"] == shas[family]
    assert shas["olmo2-7b"] != shas["llama31-8b"]


def test_w1_18s_globals_are_restored_when_the_1b_main_raises(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("fixture: the tools crash")

    monkeypatch.setattr(w1, "real_tools", boom)
    fam, _, root = side_units_family(tmp_path)
    with pytest.raises(RuntimeError, match="fixture: the tools crash"):
        w.main(["w1_18", *fam.leading("W1"), "--out", str(tmp_path / "w"), "--data-root", str(root)])
    assert (w1.SETTINGS_PATH, w1.SETTINGS_SHA256) == ORIG_W1


# ----- fix round 2: the re-verifier's OR2, OR6-OR9 -------------------------------------------------------------------


def globals_now():
    lej = w.module(w.LEAN_MODULE)
    ou = f.ou
    return (ou.load_pinned_settings, oe.load_pinned_settings, ou.OEXT_SETTINGS_PATH, w1.SETTINGS_PATH,
            w1.SETTINGS_SHA256, lej.SETTINGS_PATH, lej.SETTINGS_SHA256, lej.OEXT_SETTINGS_PATH,
            s1.code_identity)


def _rewrite(settings, root, name, change, fam):
    folder = root / settings["units"][name]["path"]
    marker = json.loads((folder / "COMPLETE.json").read_bytes())
    change(marker, folder)
    settings["units"][name]["complete_sha256"] = f.write(folder / "COMPLETE.json", marker)
    fam.put("limits_overrefusal_checks", settings)
    pin_record(fam, None, branch=oe.PENDING)


@pytest.mark.parametrize("case,needle", [
    ("listed-missing", "the frozen sealed check refuses"),
    ("second-eval", "eval/ does not hold exactly the folder of checkpoint e1"),
    ("path-form", "its path is not in the settings' allow-list form"),
])
def test_the_side_unit_check_is_as_strict_as_w1_18s_own_gate(tmp_path, case, needle):
    """OR2: a COMPLETE.json that lists a file which is absent (W1-18's frozen sealed check refuses it), a second eval
    folder, and a path outside the allow-list form each refuse in the check, as W1-18's own unit gate would on the
    pod; still hash-only."""
    fam, settings, root = side_units_family(tmp_path)
    name = "B-1101"
    if case == "listed-missing":
        _rewrite(settings, root, name, lambda m, folder: m["files"].update({"eval/e1/summary-extra.json": "e" * 64}),
                 fam)
    elif case == "second-eval":
        (root / settings["units"][name]["path"] / "eval" / "e2").mkdir()
    else:
        settings["units"][name]["path"] = "elsewhere/" + settings["units"][name]["path"]
        fam.put("limits_overrefusal_checks", settings)
        pin_record(fam, None, branch=oe.PENDING)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and needle in out + err, (out[-300:], err[-300:])


def test_a_value_that_is_not_a_hash_is_never_printed(tmp_path):
    """OR7: a COMPLETE.json list value that is not a SHA-256 is reported by its key only; its text is not printed."""
    fam, settings, root = side_units_family(tmp_path)
    secret = "a text value that must not be printed"
    _rewrite(settings, root, "B-1101", lambda m, folder: m["files"].update({"eval/e1/guard.jsonl": secret}), fam)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and secret not in out + err
    assert "COMPLETE.json lists no SHA-256 for eval/e1/guard.jsonl" in out
    assert json.loads(out)["side_units"]["units"]["B-1101"]["files"]["eval/e1/guard.jsonl"]["sha256"] is None


def test_a_waiting_role_masks_only_its_own_pins_refusal(tmp_path):
    """OR8 (W2-3's form, R2): with theta0's and a unit's job pins null, the W1-18 settings print "waits" (exit 0)
    when every other field is valid; another refusal of the same file (a seed that is not an integer) exits 2."""
    fam, settings, root = side_units_family(tmp_path)
    settings["units"]["B-1101"]["job_sha256"] = None
    settings["units"]["untuned"] = copy.deepcopy(settings["units"]["B-1101"])
    fam.put("limits_overrefusal_checks", settings)
    pin_record(fam, None, branch=oe.PENDING)
    fam.waits = [{"pin": "UNIT_JOB", "event": "fixture", "where": ["x"], "roles": ["limits_overrefusal_checks"]},
                 {"pin": "THETA0_JOB", "event": "fixture", "where": ["y"], "roles": ["limits_overrefusal_checks"]}]
    code, out, err = check(fam)
    assert code == 0 and out["settings"]["limits_overrefusal_checks"] == "waits", err[-300:]
    settings["units"]["B-1101"]["seed"] = "1101"
    fam.put("limits_overrefusal_checks", settings)
    pin_record(fam, None, branch=oe.PENDING)
    code, _, err = f.wrapper(fam, ["check", "--family", f.FAMILY])
    assert code == 2 and "no integer seed" in err


@pytest.mark.parametrize("repeat", ["--family", "--engine", "--index", "--index-sha256"])
def test_a_repeated_leading_option_refuses(tmp_path, repeat):
    """OR9."""
    fam, _, _ = side_units_family(tmp_path)
    lead = fam.leading("X")
    i = lead.index(repeat)
    code, _, err = f.call(w.main, ["check", *lead, repeat, lead[i + 1]])
    assert code == 2 and f"{repeat} is given twice" in err


def test_check_restores_every_global_after_a_validator_refusal(tmp_path):
    """The re-verifier's B4 (OR6): check patches the labels, the W1-18 globals and (R-23) the engine identity while it
    validates; a refusal raised inside leaves none of them set."""
    env = f.unit_world(tmp_path / "u", "full", full_reason="fixture: no record")
    _, _, doc = f.put_unit_settings(env)
    before = globals_now()
    assert f.wrapper(env, ["check", "--family", f.FAMILY])[0] == 0
    assert globals_now() == before
    doc = copy.deepcopy(doc)
    doc["oext"]["settings"]["path"] = "scripts/stage1_s1/settings/oext_eval.json"
    env.fam.put("oext_unit", doc)
    code, _, err = f.wrapper(env, ["check", "--family", f.FAMILY])
    assert code == 2 and "oext names the O-ext module" in err
    assert globals_now() == before


@pytest.mark.parametrize("command", ["unit", "lean-run", "lean-verify", "w1_18", "check"])
def test_every_command_refuses_an_index_of_another_kind(tmp_path, command):
    """The re-verifier's C1 (OR6): an index whose kind is not the O-ext index's refuses on every command."""
    env = f.unit_world(tmp_path / "u", "128")
    f.put_unit_settings(env)
    engine = "W1" if command == "w1_18" else "X"
    path, _ = env.fam.index(engine)
    doc = json.loads(path.read_bytes())
    doc["kind"] = "another index"
    digest = f.write(path, doc)
    out = tmp_path / "o"
    tail = {"unit": f.unit_args(env, out, run=env.world.units["evaluated"]),
            "lean-run": ["run", "--job", "j", "--prepared", str(env.world.prepared), "--recipe", "r", "--out", str(out)],
            "lean-verify": ["verify", "--out", str(out)], "w1_18": ["--out", str(out)], "check": []}[command]
    lead = ["--family", f.FAMILY, "--engine", engine, "--index", str(path), "--index-sha256", digest]
    before = globals_now()
    code, _, err = f.call(w.main, [command.split("-")[0], *lead, *tail])
    assert code == 2 and "is not the scale78b O-ext index" in err and not out.exists() and globals_now() == before


def test_a_record_that_differs_in_any_read_field_never_passes(tmp_path, fake_tools):
    """The re-verifier's D1 (OR6): the right record passes; the same record with one field changed (a unit's cut, the
    verdict's type, the version, a unit renamed or added, the provenance) never does."""
    fam, record, _ = family_with_record(tmp_path / "a")
    pin_record(fam, record)
    assert check(fam, "--w1-18-record", str(record))[0] == 0
    doc = json.loads(record.read_bytes())
    cases = {}
    d = copy.deepcopy(doc); next(iter(d["units"].values()))["truncation"]["cap_tokens"] = 64; cases["cut"] = d  # noqa: E702
    d = copy.deepcopy(doc); d["truncation_check"]["pass"] = "true"; cases["verdict-type"] = d  # noqa: E702
    d = copy.deepcopy(doc); d["version"] = 2; cases["version"] = d  # noqa: E702
    d = copy.deepcopy(doc); k = sorted(d["units"])[0]; d["units"]["renamed"] = d["units"].pop(k); cases["renamed"] = d  # noqa: E702
    d = copy.deepcopy(doc); d["units"]["extra"] = copy.deepcopy(next(iter(d["units"].values()))); cases["extra"] = d  # noqa: E702
    d = copy.deepcopy(doc); d["provenance"]["settings_sha256"] = "9" * 64; cases["provenance"] = d  # noqa: E702
    for name, d in cases.items():
        p = tmp_path / f"bad-{name}.json"
        f.write(p, d)
        pin_record(fam, p)
        code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--w1-18-record", str(p)])
        assert code == 2 and out == "", (name, err[-300:])


def test_a_unit_folder_linked_out_of_the_data_root_is_a_problem(tmp_path):
    """The re-verifier's E5 (OR6)."""
    import shutil

    fam, settings, root = side_units_family(tmp_path)
    folder = root / settings["units"]["B-1101"]["path"]
    outside = tmp_path / "outside"
    shutil.move(str(folder), str(outside))
    folder.symlink_to(outside, target_is_directory=True)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and "leaves the data root" in out


def test_check_refuses_a_changed_run_file(tmp_path, monkeypatch):
    """The re-verifier's G1 (OR6)."""
    env = f.unit_world(tmp_path / "u", "full", full_reason="fixture: no record")
    f.put_unit_settings(env)
    assert f.wrapper(env, ["check", "--family", f.FAMILY])[0] == 0
    monkeypatch.setitem(w.CODE, "scripts.stage1_s1.oext_eval", "0" * 64)
    code, _, err = f.wrapper(env, ["check", "--family", f.FAMILY])
    assert code == 2 and "the run files stay byte for byte" in err


def test_an_engine_unit_naming_job_json_beside_its_list_is_found(tmp_path):
    """The re-verifier's G2 (OR6)."""
    fam, settings, root = side_units_family(tmp_path)

    def move(marker, folder):
        marker["job_sha256"] = marker["files"].pop("job.json")

    _rewrite(settings, root, "B-1101", move, fam)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    # the frozen sealed check reads the list only; job.json beside it is the engine's form
    report = json.loads(out) if code == 0 else None
    assert report is not None, (out[-300:], err[-300:])
    assert report["side_units"]["units"]["B-1101"]["files"]["job.json"]["state"] == "listed"


def test_a_marker_that_is_not_complete_is_a_problem(tmp_path):
    """The re-verifier's G3 (OR6)."""
    fam, settings, root = side_units_family(tmp_path)
    _rewrite(settings, root, "B-1101", lambda m, _: m.update(complete=False), fam)
    code, out, err = f.wrapper(fam, ["check", "--family", f.FAMILY, "--data-root", str(root)])
    assert code == 2 and "not a complete marker" in out


def test_the_makers_check_reports_a_file_that_differs(tmp_path):
    """The re-verifier's G4 (OR6)."""
    sdir = tmp_path / "s"
    pins = json.loads(mk.PINS_PATH.read_bytes())
    for fam_pins in pins["families"].values():
        fam_pins["w1_18"] = {"branch": oe.PENDING, "record_sha256": None, "record_path": None, "full_reason": None}
    pins_path = tmp_path / "pins.json"
    pins_path.write_bytes(mk.dumps(pins))
    base = ["--pins", str(pins_path), "--settings-dir", str(sdir)]
    assert f.call(mk.main, base)[0] == 0
    assert f.call(mk.main, [*base, "--check"])[0] == 0
    target = sdir / mk.file_name("oext_eval", "llama31-8b")
    target.write_bytes(target.read_bytes() + b" ")
    code, _, err = f.call(mk.main, [*base, "--check"])
    assert code == 1 and "DIFFERS: 1 files" in err
