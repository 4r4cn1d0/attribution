"""m-verify D1 and D3 (round 4b): s1_olmo2_7b_check.py's RF-2 guard, data-free. --out may not be or lie under
--scratch-tmp, by its spelling (before anything is made) and by directory identity once the scratch folder exists
(os.path.samefile on --out's deepest existing ancestor; a case variant on a case-insensitive file system, or a symbolic
link to the scratch folder, names the same folder). Every case refuses in main() before check() reads anything: the
--edit and --stage1-record paths given here do not exist, so even a weakened guard reads no edit, no record and no
prepared set (it fails on the missing files, exit 2, with another message). Nothing is printed but exit codes."""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

import pytest

pytest.importorskip("transformers", reason="the S1 check imports the engine (the main environment)")

from scripts.scale78b import s1_olmo2_7b_check as C  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
TEST_TMP = ROOT / "tmp" / "scale-78b-s1-guard-tests"
MISSING = ROOT / "tmp" / "scale-78b-s1-guard-tests-missing"     # never created: --edit and --stage1-record


def run(scratch: Path, out: Path, capsys) -> tuple[int, str]:
    code = C.main(["--edit", str(MISSING / "edit.json"), "--stage1-record", str(MISSING / "record.json"),
                   "--scratch-tmp", str(scratch), "--out", str(out)])
    return code, capsys.readouterr().err


@pytest.fixture
def scratch():
    path = TEST_TMP / uuid.uuid4().hex
    yield path
    shutil.rmtree(TEST_TMP, ignore_errors=True)
    assert not MISSING.exists()


@pytest.mark.parametrize("pre_existing", [False, True])
@pytest.mark.parametrize("where", ["record.json", "list/record.json", "list/deeper/record.json", "."])
def test_rf2_out_in_or_under_the_scratch_folder_by_its_spelling_is_refused(scratch, capsys, where, pre_existing):
    """D3: the nested cases (--out <scratch>/list/record.json and deeper) refuse like <scratch>/record.json and
    <scratch> itself; nothing is created and a pre-existing folder keeps exactly its files."""
    if pre_existing:
        scratch.mkdir(parents=True)
        (scratch / "keep.json").write_bytes(b"{}")
    code, err = run(scratch, scratch / where, capsys)
    assert code == 2 and "lies under --scratch-tmp" in err
    assert "(the same folder by identity)" not in err     # the spelling guard, before the scratch folder is made
    assert (sorted(p.name for p in scratch.iterdir()) == ["keep.json"]) if pre_existing else not scratch.exists()


def case_insensitive() -> bool:
    TEST_TMP.mkdir(parents=True, exist_ok=True)
    other = Path(str(TEST_TMP).replace("/tmp/", "/TMP/"))
    return other.exists() and os.path.samefile(other, TEST_TMP)


@pytest.mark.parametrize("pre_existing", [False, True])
@pytest.mark.parametrize("where", ["list/record.json", "record.json"])
def test_rf2_a_case_variant_of_the_scratch_folder_is_refused_by_identity(scratch, capsys, where, pre_existing):
    """D1: on this Mac's case-insensitive APFS, 'TMP' names the same folder as 'tmp'; the string guard passes it, the
    identity guard refuses it after the scratch mkdir and before check(), and the cleanup removes the folder this run
    made (a pre-existing one keeps its files)."""
    if not case_insensitive():
        pytest.skip("a case-sensitive file system: 'TMP' is another folder here")
    if pre_existing:
        scratch.mkdir(parents=True)
        (scratch / "keep.json").write_bytes(b"{}")
    rel = scratch.relative_to(ROOT)
    assert rel.parts[0] == "tmp"
    out = ROOT / "TMP" / Path(*rel.parts[1:]) / where
    code, err = run(scratch, out, capsys)
    assert code == 2 and "(the same folder by identity)" in err
    assert not out.exists()
    assert (sorted(p.name for p in scratch.iterdir()) == ["keep.json"]) if pre_existing else not scratch.exists()


def test_rf2_a_symbolic_link_to_the_scratch_folder_is_refused(scratch, capsys, tmp_path):
    """D1: --out through a symbolic link whose target is the scratch folder: the spelling guard resolves the link and
    refuses it (the identity guard would too); the scratch folder keeps its files."""
    scratch.mkdir(parents=True)
    (scratch / "keep.json").write_bytes(b"{}")
    link = tmp_path / "alias"
    link.symlink_to(scratch, target_is_directory=True)
    code, err = run(scratch, link / "list" / "record.json", capsys)
    assert code == 2 and "lies under --scratch-tmp" in err
    assert sorted(p.name for p in scratch.iterdir()) == ["keep.json"]
    assert C.lies_in(link / "list" / "record.json", scratch)


def test_lies_in_compares_folders_by_identity(scratch, tmp_path):
    scratch.mkdir(parents=True)
    (scratch / "list").mkdir()
    assert C.lies_in(scratch, scratch) and C.lies_in(scratch / "list", scratch)
    assert C.lies_in(scratch / "list" / "a" / "b.json", scratch) and C.lies_in(scratch / "x.json", scratch)
    assert not C.lies_in(tmp_path / "record.json", scratch) and not C.lies_in(scratch.parent / "other" / "r.json", scratch)
    assert not C.lies_in(scratch.parent, scratch)
