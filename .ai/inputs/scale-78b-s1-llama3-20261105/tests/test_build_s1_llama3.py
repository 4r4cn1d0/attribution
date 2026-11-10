"""The Llama S1 add edit (track F, S1 per family): the build on the real prepared sets (git-ignored copies under
tmp/kt-prepared/), stage 1's committed S1 edit (a stage-1 S1 unit's edit.json; read through the engine's parse_edit only)
and REQ-7's frozen writer. No text is read into a test or printed: the tests compare row ids, token counts, hashes and
bytes, and check that the text-bearing files are the only ones that hold the rows' text (s1common._text_hits)."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

pytest.importorskip("transformers", reason="the Llama codec needs the main environment (transformers)")

REPO = Path(__file__).resolve().parents[4]            # conftest.py puts it on sys.path; named here for the paths
WRAPPER = Path(__file__).resolve().parents[1] / "build_s1_llama3.py"
MAIN = Path("/Users/spiderishi/Coding/attribution")

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from experiments.safety_selection.config import load_recipe  # noqa: E402
from experiments.safety_selection.edits import EditError, edited_corpus, parse_edit  # noqa: E402
from scripts.stage1 import build_s_pool as bsp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import write_add_edit as wae  # noqa: E402


def load_wrapper():
    spec = importlib.util.spec_from_file_location("build_s1_llama3_under_test", WRAPPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


W = load_wrapper()

OLMO = REPO / W.OLMO_PREPARED_REL
LLAMA = REPO / W.LLAMA_PREPARED_REL
RECIPE = REPO / W.LLAMA_MAIN_CONFIG_REL
RECORD = REPO / W.STAGE1_ADD_S1_RECORD_REL
OLMO_EDIT = next((p for p in (REPO / W.OLMO_S1_EDIT_REL, MAIN / W.OLMO_S1_EDIT_REL) if p.is_file()), None)
COMMITTED_OUT = WRAPPER.parent / "out"
TEST_TMP = REPO / "tmp" / "scale-78b-s1-llama3-tests"            # --full-out must lie under a folder named tmp

pytestmark = pytest.mark.skipif(not (OLMO / "manifest.json").exists() or not (LLAMA / "manifest.json").exists()
                                or OLMO_EDIT is None,
                                reason="the prepared sets (tmp/kt-prepared/) or a copy of stage 1's S1 edit are not on this Mac")


def sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fresh_full_out() -> Path:
    return TEST_TMP / uuid.uuid4().hex


def run_build(out: Path, full_out: Path, list_spec=None, olmo_edit: Path | None = None, record: Path | None = None):
    return W.run(REPO, LLAMA, OLMO, RECIPE, out, full_out, list_spec, olmo_edit or OLMO_EDIT, record or RECORD)


@pytest.fixture(scope="module", autouse=True)
def remove_the_test_tmp_folder():
    """Every text-bearing test output lives under TEST_TMP (git-ignored, under tmp/); it is removed when the module ends."""
    yield
    shutil.rmtree(TEST_TMP, ignore_errors=True)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out, full_out = tmp_path_factory.mktemp("s1-out"), fresh_full_out()
    result = run_build(out, full_out)
    yield {"result": result, "out": out, "full_out": full_out,
           "edit": (full_out / "edits" / W.EDIT_FILE).read_bytes(), "list": full_out / "list" / "s1.json",
           "manifest": json.loads((out / "MANIFEST.json").read_bytes()),
           "record": json.loads((out / wae.RECORD).read_bytes()),
           "settings": json.loads((out / W.SETTINGS_FILE).read_bytes())}
    shutil.rmtree(TEST_TMP, ignore_errors=True)


def stub(root: Path, manifest_sha256: str):
    return s1.PreparedView(root, manifest_sha256).engine_stub()


# ----- the edit -------------------------------------------------------------------------------------------------------


def test_the_edit_holds_the_48_rows_in_list_order_with_the_committed_list_ids(built):
    m, rec = built["manifest"], built["record"]
    committed = json.loads(RECORD.read_bytes())
    assert [r["add_id"] for r in m["rows"]] == [f"add-s1-{j:03d}" for j in range(1, 49)]
    assert [r["list_id"] for r in m["rows"]] == [r["list_id"] for r in committed["rows"]]       # the same 48 S-pool rows
    assert m["rows"] == rec["rows"]
    f = m["files"][0]
    assert f["counts"] == {"add": 48, "remove": 0, "rewrite": 0} and f["edit_kind"] == "add" and f["rows"] == 48
    assert f["sha256"] == sha256_bytes(built["edit"]) and f["arm"] == f"edit-{f['sha256']}"
    assert f["path"] == "edits/add_s1.json" and m["full_out"]["default"] == W.FULL_OUT_REL
    assert m["list"] == {"name": "s1", "sha256": W.LIST_SHA256, "rows": 48, "source": m["list"]["source"]}
    assert m["list"]["source"]["kind"] == "recovered" and m["list"]["source"]["written"] == "list/s1.json"
    assert rec["list"]["sha256"] == W.LIST_SHA256 and rec["edits"][0]["sha256"] == f["sha256"]
    assert m["engine_identity_sha256"] == rec["provenance"]["engine_identity_sha256"]


def test_parse_edit_accepts_the_edit_on_the_llama_set_and_refuses_it_on_the_olmo_set(built):
    edit = parse_edit(built["edit"], stub(LLAMA, W.LLAMA_MANIFEST_SHA256))
    assert len(edit.added) == 48 and not edit.removed and not edit.rewrite
    assert edit.document["manifest_sha256"] == W.LLAMA_MANIFEST_SHA256
    assert edit.document["provenance"]["script"] == "scripts/stage1/write_add_edit.py"           # REQ-7's path wrote it
    assert edit.document["provenance"]["script_sha256"] == W.FROZEN["scripts/stage1/write_add_edit.py"]
    with pytest.raises(EditError, match="another prepared dataset"):
        parse_edit(built["edit"], stub(OLMO, W.OLMO_MANIFEST_SHA256))
    assert built["manifest"]["prepared"]["olmo_refusal_check"]["engine_refuses_the_edit"] is True


def test_the_token_counts_are_the_engines_encoding_under_the_llama_codec_and_the_main_recipes_limit(built):
    m = built["manifest"]
    recipe = load_recipe(RECIPE)
    assert m["recipe"]["max_train_tokens"] == recipe["model"]["max_train_tokens"] == built["record"]["max_train_tokens"]
    assert m["recipe"]["config_sha256"] == W.LLAMA_MAIN_CONFIG_SHA256
    codec = bsp.real_codec(LLAMA, {"inputs": {"prepared_manifest_sha256": W.LLAMA_MANIFEST_SHA256}})
    edit = parse_edit(built["edit"], stub(LLAMA, W.LLAMA_MANIFEST_SHA256))
    encoded = edited_corpus({}, edit, stub(LLAMA, W.LLAMA_MANIFEST_SHA256), codec, m["recipe"]["max_train_tokens"])
    assert {r["add_id"]: (r["prompt_tokens"], r["target_tokens"]) for r in m["rows"]} == \
        {k: (ex.n_prompt, ex.n_target) for k, ex in encoded.items()}
    # the Llama template's prompt tokens differ from the OLMo record's; the rows and the target tokens are the same rows
    committed = json.loads(RECORD.read_bytes())["rows"]
    assert sum(r["target_tokens"] for r in m["rows"]) > 0 and len(committed) == 48


def test_the_recovered_list_is_the_sealed_list_by_its_pin_and_req7_reads_it(built):
    assert sha(built["list"]) == W.LIST_SHA256
    listing = wae.read_list(built["list"], W.LIST_SHA256)
    assert listing["name"] == "s1" and len(listing["items"]) == 48
    assert [i["id"] for i in listing["items"]] == [r["list_id"] for r in built["manifest"]["rows"]]
    with pytest.raises(s1.Refusal, match="hashes to"):
        wae.read_list(built["list"], "0" * 64)


def test_the_text_bearing_files_are_the_only_ones_that_hold_the_rows_text(built):
    listing = wae.read_list(built["list"], W.LIST_SHA256)
    texts = [t for item in listing["items"] for t in (item["prompt"], item["response"])]
    assert s1._text_hits(built["edit"], texts) >= 48                                 # the edit holds the rows
    assert s1._text_hits(built["list"].read_bytes(), texts) >= 48
    for name in ("MANIFEST.json", wae.RECORD, W.SETTINGS_FILE):
        assert s1._text_hits((built["out"] / name).read_bytes(), texts) == 0, name


# ----- the settings and the pins -------------------------------------------------------------------------------------


def test_the_settings_are_req7s_with_the_two_pins_rebound_and_the_derivation_recorded(built):
    base = json.loads((REPO / W.STAGE1_SETTINGS_REL).read_bytes())
    derived, m, rec = built["settings"], built["manifest"], built["record"]
    assert sha256_bytes((REPO / W.STAGE1_SETTINGS_REL).read_bytes()) == W.STAGE1_SETTINGS_SHA256
    assert {k for k in set(base) | set(derived) if base.get(k) != derived.get(k)} == set(W.SETTINGS_CHANGED)
    assert derived["prepared_manifest_sha256"] == W.LLAMA_MANIFEST_SHA256
    assert derived["recipe_sha256"] == W.LLAMA_MAIN_CONFIG_SHA256
    assert derived["lists"] == base["lists"] and derived["add_id_rule"] == base["add_id_rule"]
    assert derived["derived_from"]["sha256"] == W.STAGE1_SETTINGS_SHA256
    assert derived["derived_from"]["by_sha256"] == sha(WRAPPER) == m["script"]["sha256"]      # the script's hash reaches
    settings_sha = sha256_bytes((built["out"] / W.SETTINGS_FILE).read_bytes())
    assert m["settings"]["sha256"] == settings_sha == rec["provenance"]["settings_sha256"]     # ... the record and
    edit_doc = parse_edit(built["edit"], stub(LLAMA, W.LLAMA_MANIFEST_SHA256)).document
    assert edit_doc["provenance"]["settings_sha256"] == settings_sha                             # ... the edit file
    assert rec["provenance"]["script_sha256"] == W.FROZEN["scripts/stage1/write_add_edit.py"]
    assert m["frozen_code"]["scripts/stage1/s1common.py"] == rec["provenance"]["s1common_sha256"]
    assert rec["provenance"]["inputs"] == {"list": W.LIST_SHA256, "prepared_manifest": W.LLAMA_MANIFEST_SHA256,
                                           "recipe": W.LLAMA_MAIN_CONFIG_SHA256}


def test_the_frozen_code_pins_hold_and_a_changed_pin_refuses(monkeypatch):
    assert W.check_frozen() == W.FROZEN
    for rel in W.FROZEN:
        assert sha(REPO / rel) == W.FROZEN[rel]
    monkeypatch.setitem(W.FROZEN, "scripts/stage1/write_add_edit.py", "0" * 64)
    with pytest.raises(s1.Refusal, match="frozen writer changed"):
        W.check_frozen()


# ----- determinism and the committed output ---------------------------------------------------------------------------


def test_a_re_run_gives_the_same_bytes(tmp_path):
    out, full_out = tmp_path / "out", fresh_full_out()
    first = run_build(out, full_out)["written"]
    shutil.rmtree(out)
    shutil.rmtree(full_out)
    second = run_build(out, full_out)["written"]
    assert first == second and set(first) == {"MANIFEST.json", wae.RECORD, W.SETTINGS_FILE, "edits/add_s1.json", "list/s1.json"}
    shutil.rmtree(full_out)


def test_a_fresh_build_equals_the_fixture_build_in_another_folder(built, tmp_path):
    """The manifest names the text files by their place under --full-out and by hash, so two folders give equal bytes."""
    out, full_out = tmp_path / "out", fresh_full_out()
    run_build(out, full_out)
    for name in ("MANIFEST.json", wae.RECORD, W.SETTINGS_FILE):
        assert (out / name).read_bytes() == (built["out"] / name).read_bytes(), name
    assert (full_out / "edits" / W.EDIT_FILE).read_bytes() == built["edit"]
    shutil.rmtree(full_out)


@pytest.mark.skipif(not (COMMITTED_OUT / "MANIFEST.json").is_file(), reason="no committed out/ beside the script yet")
def test_the_committed_out_equals_a_fresh_build_and_its_files_hash_as_its_manifest_says(built):
    committed = json.loads((COMMITTED_OUT / "MANIFEST.json").read_bytes())
    assert committed["script"]["sha256"] == sha(WRAPPER), "the committed out/ was built by another version of the script: rebuild"
    for name in ("MANIFEST.json", wae.RECORD, W.SETTINGS_FILE):
        assert (COMMITTED_OUT / name).read_bytes() == (built["out"] / name).read_bytes(), name
    assert sha(COMMITTED_OUT / wae.RECORD) == committed["record"]["sha256"]
    assert sha(COMMITTED_OUT / W.SETTINGS_FILE) == committed["settings"]["sha256"]
    assert committed["files"][0]["sha256"] == sha256_bytes(built["edit"])
    default_full = REPO / W.FULL_OUT_REL
    if (default_full / "edits" / W.EDIT_FILE).is_file():                       # the lead's default --full-out, if present
        assert sha(default_full / "edits" / W.EDIT_FILE) == committed["files"][0]["sha256"]


# ----- refusals: inputs ----------------------------------------------------------------------------------------------


def test_a_tampered_olmo_edit_a_wrong_record_and_a_wrong_list_pin_refuse_and_nothing_is_written(tmp_path):
    data = bytearray(OLMO_EDIT.read_bytes())
    data[-2] ^= 0x01                                                      # one byte of the committed edit
    tampered = tmp_path / "edit.json"
    tampered.write_bytes(bytes(data))
    out, full_out = tmp_path / "out", fresh_full_out()
    with pytest.raises(s1.Refusal, match="the pin is"):
        run_build(out, full_out, olmo_edit=tampered)
    assert not out.exists() and not full_out.exists()
    record_doc = json.loads(RECORD.read_bytes())
    record_doc["rows"][0]["list_id"] = "pku_alpaca3_8b:000000:0"
    bad_record = tmp_path / "add_edit_record.json"
    bad_record.write_bytes(canonical_json(record_doc))
    with pytest.raises(s1.Refusal, match="add-s1 record hashes to"):
        run_build(out, full_out, record=bad_record)
    assert not out.exists() and not full_out.exists()
    with pytest.raises(s1.Refusal, match="sealed pin"):
        run_build(out, full_out, list_spec=f"{tmp_path / 'x.json'}:{'0' * 64}")
    assert not out.exists() and not full_out.exists()


def test_a_recovered_list_that_misses_the_pin_refuses_and_a_later_refusal_removes_the_written_list(monkeypatch, tmp_path):
    """recover_list accepts only bytes that hash to the sealed pin: the same 48 rows in another order (two list ids
    swapped in the record's map) are refused. And when a refusal comes after the recovered list was written for REQ-7's
    reader, that file and its folders are removed again (a refusal leaves nothing written)."""
    record = json.loads(RECORD.read_bytes())
    record["rows"][0]["list_id"], record["rows"][1]["list_id"] = record["rows"][1]["list_id"], record["rows"][0]["list_id"]
    with pytest.raises(s1.Refusal, match="not to the sealed pin"):
        W.recover_list(OLMO_EDIT, stub(OLMO, W.OLMO_MANIFEST_SHA256), record)

    def refuse_late(*args, **kwargs):
        raise s1.Refusal("late")
    monkeypatch.setattr(W, "build", refuse_late)
    out, full_out = tmp_path / "out", fresh_full_out()
    with pytest.raises(s1.Refusal, match="late"):
        run_build(out, full_out)
    assert not out.exists() and not full_out.exists()


def test_a_given_list_is_read_by_its_pin_and_recorded_as_given(built, tmp_path):
    out, full_out = tmp_path / "out", fresh_full_out()
    result = run_build(out, full_out, list_spec=f"{built['list']}:{W.LIST_SHA256}")
    m = result["manifest"]
    assert m["list"]["source"]["kind"] == "given" and "list/s1.json" not in result["written"]
    assert result["written"]["edits/add_s1.json"] == sha256_bytes(built["edit"])              # the same edit bytes
    assert (out / wae.RECORD).read_bytes() == (built["out"] / wae.RECORD).read_bytes()
    shutil.rmtree(full_out)


# ----- refusals: the guards -----------------------------------------------------------------------------------------------


def fake_checkout(root: Path) -> Path:
    for rel in W.FORBIDDEN_DIRS:
        (root / rel / "out").mkdir(parents=True)
    return root


def test_the_guard_refuses_the_committed_sealed_folders_of_this_checkout_and_of_repo(tmp_path):
    for rel in W.FORBIDDEN_DIRS:
        with pytest.raises(s1.Refusal, match="refusing to write under"):
            W.guard_out(REPO / rel / "out", REPO)
        with pytest.raises(s1.Refusal, match="refusing to write under"):
            W.guard_out(REPO / rel / "out" / "deeper", None)
    fake = fake_checkout(tmp_path / "fake")
    for rel in W.FORBIDDEN_DIRS:
        with pytest.raises(s1.Refusal, match="refusing to write under"):
            W.guard_out(fake / rel / "out", fake)
    W.guard_out(fake / "tmp" / "free", fake)                                   # elsewhere is fine
    W.guard_out(tmp_path / "elsewhere", REPO)


def test_the_guard_refuses_a_case_variant_a_symlink_a_dotted_and_a_relative_path_by_identity(tmp_path, monkeypatch):
    fake = fake_checkout(tmp_path / "fake")
    sealed = fake / W.FORBIDDEN_DIRS[3]                                         # the committed Llama sealed set
    probe = tmp_path / "Probe"
    probe.mkdir()
    case_insensitive = (tmp_path / "probe").exists()
    if case_insensitive:
        variant = fake / ".ai" / "inputs" / W.FORBIDDEN_DIRS[3].split("/")[-1].upper() / "out" / "new"
        with pytest.raises(s1.Refusal, match="refusing to write under"):
            W.guard_out(variant, fake)
    link = tmp_path / "link-to-sealed"
    link.symlink_to(sealed)
    with pytest.raises(s1.Refusal, match="refusing to write under"):
        W.guard_out(link / "out" / "new", fake)
    with pytest.raises(s1.Refusal, match="refusing to write under"):
        W.guard_out(fake / ".ai" / "inputs" / "." / W.FORBIDDEN_DIRS[3].split("/")[-1] / "out" / "new", fake)
    monkeypatch.chdir(fake)
    with pytest.raises(s1.Refusal, match="refusing to write under"):
        W.guard_out(Path(W.FORBIDDEN_DIRS[3]) / "out" / "x", fake)


def test_a_full_out_outside_tmp_a_non_empty_out_and_nested_outputs_refuse(tmp_path):
    with pytest.raises(s1.Refusal, match="folder named tmp"):
        wae.full_out_ok(Path("/Users/nobody/scale-78b-s1"))
    out = tmp_path / "out"
    out.mkdir()
    (out / "stale.json").write_text("{}")
    full_out = fresh_full_out()
    with pytest.raises(s1.Refusal, match="not empty"):
        run_build(out, full_out)
    assert sorted(p.name for p in out.iterdir()) == ["stale.json"] and not full_out.exists()
    with pytest.raises(s1.Refusal, match="distinct and not nested"):
        run_build(full_out / "out", full_out)
    assert not full_out.exists()


# ----- the command line -----------------------------------------------------------------------------------------------------


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", "-B", str(WRAPPER), *args], capture_output=True, text=True, cwd=str(REPO),
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})


def test_the_cli_builds_prints_hashes_only_and_refuses_with_exit_2_writing_nothing(built, tmp_path):
    out, full_out = tmp_path / "cli-out", fresh_full_out()
    done = cli("--out", str(out), "--full-out", str(full_out), "--olmo-s1-edit", str(OLMO_EDIT))
    assert done.returncode == 0, done.stderr
    lines = done.stdout.splitlines()
    assert lines[0].startswith("built S1 on c52a50af: 48 rows; arm edit-")
    assert sum(1 for l in lines if l.startswith("  ") and len(l.split()[0]) == 64) == 5
    assert all(len(l) <= 240 for l in lines)
    assert (out / "MANIFEST.json").read_bytes() == (built["out"] / "MANIFEST.json").read_bytes()
    shutil.rmtree(full_out)
    bad = cli("--out", str(tmp_path / "bad-out"), "--full-out", str(fresh_full_out()), "--list", f"{built['list']}:{'0' * 64}")
    assert bad.returncode == 2 and bad.stderr.startswith("REFUSED:") and "nothing written" in bad.stderr
    assert not (tmp_path / "bad-out").exists()
