"""The S1 decision for OLMo-2-7B (track F; Part 1 section 14 item 1; the check's C6), measured by
scripts/scale78b/s1_olmo2_7b_check.py on the real inputs: the OLMo prepared set (git-ignored, tmp/kt-prepared/), a copy of
stage 1's committed S1 edit (a stage-1 S1 unit's edit.json; read through the engine's parse_edit only) and REQ-7's frozen
writer. Skipped where those are absent. No text is read into a test or printed: counts, hashes and the verdict only."""

from __future__ import annotations

import importlib.util
import json
import shutil
import uuid
from pathlib import Path

import pytest

pytest.importorskip("transformers", reason="the OLMo codec needs the main environment (transformers)")

from experiments.safety_selection.common import sha256_bytes  # noqa: E402
from scripts.scale78b import s1_olmo2_7b_check as C  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MAIN = Path("/Users/spiderishi/Coding/attribution")
OLMO = ROOT / C.OLMO_PREPARED_REL
B = C.load_sealed_builder(ROOT)
OLMO_EDIT = next((p for p in (ROOT / B.OLMO_S1_EDIT_REL, MAIN / B.OLMO_S1_EDIT_REL) if p.is_file()), None)
TEST_TMP = ROOT / "tmp" / "scale-78b-s1-olmo2-7b-check-tests"

pytestmark = pytest.mark.skipif(not (OLMO / "manifest.json").exists() or OLMO_EDIT is None,
                                reason="the OLMo prepared set (tmp/kt-prepared/) or a copy of stage 1's S1 edit is not on this Mac")


@pytest.fixture(scope="module")
def result():
    scratch = TEST_TMP / uuid.uuid4().hex
    try:
        yield C.check(ROOT, OLMO, OLMO_EDIT, ROOT / B.STAGE1_ADD_S1_RECORD_REL, ROOT / C.OLMO_7B_MAIN_CONFIG_REL,
                      ROOT / C.RECIPE_S_1B_REL, scratch, None, ROOT / C.SEAL_EDITS_REL)
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)


def test_the_committed_s1_edit_is_olmo_2_7bs_s1_edit_as_it_stands(result):
    c = result["checks"]
    assert result["equal_as_it_stands"] is True and result["verdict"] == C.VERDICT_EQUAL
    assert c["1_parse_edit_accepts_against_the_family_manifest"] is True
    assert c["2_rows_with_the_committed_token_counts_under_the_7b_limit"] == {"equal": 48, "of": 48}
    assert c["2_rows_with_the_committed_token_counts_under_the_1b_recipe_s_limit"] == {"equal": 48, "of": 48}
    assert c["2_longest_row_tokens_with_eos"] <= result["family"]["main_config"]["max_train_tokens"]
    assert result["family"]["main_config"]["max_train_tokens"] == result["stage1"]["recipe_s_1b"]["max_train_tokens"] == 3072


def test_req7s_frozen_writer_reproduces_the_committed_bytes_with_stage_1s_inputs(result):
    r3 = result["checks"]["3_frozen_writer_reproduces_the_committed_bytes"]
    assert r3["equal"] is True and r3["rebuilt_sha256"] == r3["committed_sha256"] == B.OLMO_S1_EDIT_SHA256
    assert [c["name"] for c in result["stage1"]["combine_with"]] == ["R_d2", "R_d3", "R_d4"]        # the record's inputs
    for entry in result["stage1"]["combine_with"]:
        assert sha256_bytes((ROOT / entry["path"]).read_bytes()) == entry["sha256"]                  # SEAL's files
    assert result["frozen_code"] == B.FROZEN


def test_a_rebuild_under_the_7b_main_recipe_changes_only_the_recipe_hash_and_the_settings_hash(result):
    r4 = result["checks"]["3_rebuild_under_the_7b_main_recipe"]
    assert r4["add_rows_identical"] is True
    assert r4["differs_from_the_committed_edit_at"] == ["provenance.inputs.recipe", "provenance.settings_sha256"]
    assert r4["sha256"] != B.OLMO_S1_EDIT_SHA256


def test_the_record_is_text_free(result):
    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, str):
            assert len(obj) <= 300
    walk(result)
    assert "rows" not in result and "items" not in result


def test_provenance_differences_names_dotted_keys():
    a = {"x": 1, "provenance": {"inputs": {"recipe": "a", "list": "l"}, "settings_sha256": "s"}}
    b = {"x": 1, "provenance": {"inputs": {"recipe": "b", "list": "l"}, "settings_sha256": "t"}}
    assert C.provenance_differences(a, b) == ["provenance.inputs.recipe", "provenance.settings_sha256"]
    assert C.provenance_differences(a, a) == []
    assert C.provenance_differences({"k": 1}, {"j": 1}) == ["j", "k"]


def test_a_tampered_edit_refuses_before_anything_is_measured(tmp_path):
    data = bytearray(OLMO_EDIT.read_bytes())
    data[-2] ^= 0x01
    tampered = tmp_path / "edit.json"
    tampered.write_bytes(bytes(data))
    scratch = TEST_TMP / uuid.uuid4().hex
    try:
        with pytest.raises(C.s1.Refusal, match="the pin is"):
            C.check(ROOT, OLMO, tampered, ROOT / B.STAGE1_ADD_S1_RECORD_REL, ROOT / C.OLMO_7B_MAIN_CONFIG_REL,
                    ROOT / C.RECIPE_S_1B_REL, scratch, None, ROOT / C.SEAL_EDITS_REL)
        assert not scratch.exists()
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)


def test_a_pre_existing_non_empty_scratch_tmp_is_refused_and_survives(tmp_path, capsys):
    """F-1 (verify-F): the CLI's cleanup removed whatever --scratch-tmp named, on every refusal, whether or not this run
    had created it. A folder that exists and is not empty is refused by the sealed-output rule (nothing written) and must
    still be there, with its file, after the refusal."""
    scratch = TEST_TMP / uuid.uuid4().hex
    scratch.mkdir(parents=True)
    keep = scratch / "keep.json"
    keep.write_bytes(b"{}")
    try:
        code = C.main(["--edit", str(OLMO_EDIT), "--scratch-tmp", str(scratch), "--out", str(tmp_path / "record.json")])
        err = capsys.readouterr().err
        assert code == 2 and "REFUSED" in err and "exists and is not empty" in err
        assert scratch.is_dir() and keep.read_bytes() == b"{}" and sorted(p.name for p in scratch.iterdir()) == ["keep.json"]
        assert not (tmp_path / "record.json").exists()
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)


def test_a_pre_existing_scratch_tmp_survives_a_refusal_before_any_measurement(tmp_path, capsys):
    """F-1, the verifier's probe (a): a missing --edit refuses (OSError) before the check reaches the scratch folder; a
    pre-existing --scratch-tmp (here holding a file) is not this run's and stays."""
    scratch = TEST_TMP / uuid.uuid4().hex
    scratch.mkdir(parents=True)
    (scratch / "precious.txt").write_bytes(b"x")
    try:
        code = C.main(["--edit", str(tmp_path / "nonexistent" / "edit.json"), "--scratch-tmp", str(scratch)])
        assert code == 2 and "REFUSED: FileNotFoundError" in capsys.readouterr().err
        assert scratch.is_dir() and (scratch / "precious.txt").read_bytes() == b"x"
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)


def test_a_scratch_folder_this_run_created_is_removed_and_the_record_is_written(tmp_path, capsys):
    """F-1's other half: the scratch folder the run itself creates (absent before) is removed at the end without --keep;
    the record is written once and holds the verdict; the CLI prints hashes, counts and the verdict only."""
    scratch = TEST_TMP / uuid.uuid4().hex
    record = tmp_path / "record.json"
    try:
        assert not scratch.exists()
        code = C.main(["--edit", str(OLMO_EDIT), "--scratch-tmp", str(scratch), "--out", str(record)])
        out = capsys.readouterr().out
        assert code == 0 and not scratch.exists() and record.is_file()
        doc = json.loads(record.read_bytes())
        assert doc["equal_as_it_stands"] is True and doc["verdict"] == C.VERDICT_EQUAL
        assert f"record {sha256_bytes(record.read_bytes())}" in out
        assert "verdict: equal as it stands" in out
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)


def test_the_sealed_builder_loaded_by_path_is_the_committed_file():
    path = ROOT / C.SEALED_BUILDER_REL
    assert path.is_file()
    spec = importlib.util.spec_from_file_location("b_again", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.LIST_SHA256 == B.LIST_SHA256 == json.loads((ROOT / B.STAGE1_ADD_S1_RECORD_REL).read_bytes())["list"]["sha256"]


# ----- reverify-F RF-1, RF-2, RF-3 (round 4, track M) ---------------------------------------------------------------------


def test_rf3_a_pre_existing_empty_scratch_tmp_survives_empty_and_the_record_is_written(tmp_path, capsys):
    """RF-3: a pre-existing EMPTY --scratch-tmp is not this run's. The run (real edit, --out) passes, removes the recovered
    list it wrote there, and leaves the folder itself: still a directory, empty. Kills the re-verifier's K3/K4 forms (the
    cleanup removing the pre-existing folder itself, or leaving the list in it)."""
    scratch = TEST_TMP / uuid.uuid4().hex
    scratch.mkdir(parents=True)
    record = tmp_path / "record.json"
    try:
        code = C.main(["--edit", str(OLMO_EDIT), "--scratch-tmp", str(scratch), "--out", str(record)])
        out = capsys.readouterr().out
        assert code == 0 and record.is_file() and f"record {sha256_bytes(record.read_bytes())}" in out
        assert json.loads(record.read_bytes())["equal_as_it_stands"] is True
        assert scratch.is_dir() and list(scratch.iterdir()) == []
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)


def test_rf1_a_folder_another_party_puts_into_the_scratch_folder_during_the_run_survives(tmp_path, monkeypatch, capsys):
    """RF-1 (the re-verifier's probe f1): --scratch-tmp is absent at the start; while the check runs, another party writes
    a folder with a file into it, and the check refuses. The old cleanup (created = "absent at the start", then rmtree)
    removed the other party's folder; now the run removes only what it made, and the scratch folder it created stays
    because it is not empty. The record is not written (refusal, exit 2)."""
    scratch = TEST_TMP / uuid.uuid4().hex

    def intruding_check(repo, olmo_root, edit_path, record_path, recipe_7b, recipe_s, scr, list_spec, seal_edits, *made):
        assert scr == scratch.resolve() and scr.is_dir()                  # this run's own mkdir made it
        (scr / "intruder").mkdir()
        (scr / "intruder" / "data.json").write_bytes(b"{}")
        raise C.s1.Refusal("stub refusal")
    monkeypatch.setattr(C, "check", intruding_check)
    try:
        code = C.main(["--edit", str(OLMO_EDIT), "--scratch-tmp", str(scratch), "--out", str(tmp_path / "record.json")])
        err = capsys.readouterr().err
        assert code == 2 and "REFUSED: stub refusal" in err and "left as it is" in err
        assert (scratch / "intruder" / "data.json").read_bytes() == b"{}"
        assert not (tmp_path / "record.json").exists()
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)


def test_rf1_a_kept_list_of_an_earlier_run_survives_a_second_run_on_the_same_folder(tmp_path, monkeypatch, capsys):
    """RF-1 (the re-verifier's probe f2, without the timing): run 1 recovers the list with --keep; run 2 on the same
    folder is refused (exists and is not empty) and run 1's list stays. The stub stands in for the measurement and writes
    the list the way check() does (atomic mkdir of scratch/list, recorded in made), so the test needs no real edit."""
    scratch = TEST_TMP / uuid.uuid4().hex

    def listing_check(repo, olmo_root, edit_path, record_path, recipe_7b, recipe_s, scr, list_spec, seal_edits, made=None):
        C.bsp.check_output_folders(scr)
        (scr / "list").mkdir(parents=True)
        if made is not None:
            made.append(scr / "list")
        C.s1.write_new_files(scr / "list", {"s1.json": b"{}"})
        raise C.s1.Refusal("stub stops after the list")
    monkeypatch.setattr(C, "check", listing_check)
    try:
        assert C.main(["--edit", str(OLMO_EDIT), "--scratch-tmp", str(scratch), "--keep"]) == 2
        assert (scratch / "list" / "s1.json").read_bytes() == b"{}"
        code = C.main(["--edit", str(OLMO_EDIT), "--scratch-tmp", str(scratch)])
        assert code == 2 and "exists and is not empty" in capsys.readouterr().err
        assert (scratch / "list" / "s1.json").read_bytes() == b"{}"
        assert C.main(["--edit", str(OLMO_EDIT), "--scratch-tmp", str(scratch / "sub")]) == 2   # a run of its own
        assert not (scratch / "sub").exists() and (scratch / "list" / "s1.json").is_file()
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)


@pytest.mark.parametrize("where", ["inside", "same", "nested"])
@pytest.mark.parametrize("pre_existing", [False, True])
def test_rf2_out_under_the_scratch_folder_is_refused_before_anything_is_created(tmp_path, capsys, where, pre_existing):
    """RF-2: --out inside (or equal to) --scratch-tmp was written, its hash printed, and then removed with the folder.
    Now it refuses before the folder is made or the check runs: exit 2, nothing created, a pre-existing folder intact.
    Round 4b (m-verify D3): the nested case --out <scratch>/list/record.json (the recovered list's folder) too."""
    scratch = TEST_TMP / uuid.uuid4().hex
    if pre_existing:
        scratch.mkdir(parents=True)
        (scratch / "keep.json").write_bytes(b"{}")
    out = {"inside": scratch / "record.json", "same": scratch, "nested": scratch / "list" / "record.json"}[where]
    try:
        code = C.main(["--edit", str(OLMO_EDIT), "--scratch-tmp", str(scratch), "--out", str(out)])
        assert code == 2 and "lies under --scratch-tmp" in capsys.readouterr().err
        if pre_existing:
            assert sorted(p.name for p in scratch.iterdir()) == ["keep.json"]
        else:
            assert not scratch.exists()
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)


def test_rf1_another_partys_list_made_while_the_list_is_recovered_survives(monkeypatch, capsys):
    """m-verify D2 (its probe P1): --scratch-tmp is absent; while recover_list runs (after check_output_folders, before
    the list folder's mkdir), another party creates scratch/list/s1.json. The list folder's mkdir is atomic (no
    exist_ok), so the run refuses ("exists"), never appends that folder to what it made, and the other party's file
    survives the cleanup."""
    scratch = (TEST_TMP / uuid.uuid4().hex).resolve()
    real_loader = C.load_sealed_builder

    def loader(repo):
        module = real_loader(repo)
        real_recover = module.recover_list

        def recover(*a, **k):
            doc = real_recover(*a, **k)
            (scratch / "list").mkdir(parents=True)
            (scratch / "list" / "s1.json").write_bytes(b"{}")
            return doc
        module.recover_list = recover
        return module
    monkeypatch.setattr(C, "load_sealed_builder", loader)
    try:
        code = C.main(["--edit", str(OLMO_EDIT), "--scratch-tmp", str(scratch)])
        err = capsys.readouterr().err
        assert code == 2 and "list exists" in err
        assert (scratch / "list" / "s1.json").read_bytes() == b"{}"
    finally:
        shutil.rmtree(TEST_TMP, ignore_errors=True)
