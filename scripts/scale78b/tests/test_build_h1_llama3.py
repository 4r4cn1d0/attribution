"""H1 on the Llama manifest: the stage-1 length rule reused by import; parity with stage 1's octile_0 on the OLMo set;
the Llama file on its own manifest; the write guard. Row ids, counts, hashes only; no text: the engine's parse_edit gets
stage 1's id-only ``s1common.PreparedView(...).engine_stub()``, never ``load_prepared``."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]            # conftest.py puts it on sys.path; named here for the paths

from experiments.safety_selection.common import sha256_bytes  # noqa: E402
from experiments.safety_selection.edits import EditError, parse_edit  # noqa: E402
from scripts.scale78b import build_h1_llama3 as H  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

OLMO = REPO / "tmp/kt-prepared/prepared-kt-dolly-olmo2"
LLAMA = REPO / H.LLAMA_PREPARED_REL
STAGE1_H1 = REPO / H.STAGE1_H1_REL
COMMITTED_OUT = REPO / H.OUT_REL

pytestmark = pytest.mark.skipif(not (OLMO / "manifest.json").exists() or not (LLAMA / "manifest.json").exists(),
                                reason="the prepared sets (git-ignored, tmp/kt-prepared/) are not in this checkout")


@pytest.fixture(scope="module")
def llama():
    return H.build(LLAMA, H.LLAMA_MANIFEST_SHA256, REPO)


def test_the_same_rule_on_the_olmo_set_reproduces_stage1_h1_remove_list():
    olmo = H.build(OLMO, H.OLMO_MANIFEST_SHA256, REPO)
    theirs = json.loads(STAGE1_H1.read_bytes())
    assert sha256_bytes(STAGE1_H1.read_bytes()) == H.STAGE1_H1_SHA256
    assert olmo["h1"] == theirs["remove"]
    assert json.loads(olmo["files"]["edits/octile_0.json"])["manifest_sha256"] == H.OLMO_MANIFEST_SHA256


def test_llama_h1_is_600_rows_with_the_fewest_llama_target_tokens_on_the_llama_manifest(llama):
    doc = json.loads(llama["files"]["edits/octile_0.json"])
    assert doc["manifest_sha256"] == H.LLAMA_MANIFEST_SHA256 and doc["edit_kind"] == "remove"
    rows = doc["remove"]
    assert rows == sorted(set(rows)) and len(rows) == 600
    view = s1.PreparedView(LLAMA, H.LLAMA_MANIFEST_SHA256)
    inside = set(rows)
    top = max(view.tokens[r] for r in rows)
    low = min(view.tokens[r] for r in view.tokens if r not in inside)
    assert top <= low                                           # no outside row is shorter than an inside row
    cuts = llama["manifest"]["cut_points"]
    assert cuts[0]["octile"] == 0 and cuts[0]["last_target_tokens"] == top and len(cuts) == 8
    assert doc["provenance"]["rule_from"]["path"] == H.STAGE1_BUILDER_REL
    assert doc["provenance"]["settings"]["sha256"] == H.STAGE1_SETTINGS_SHA256


def test_llama_h1_is_exactly_the_first_600_of_the_llama_length_order(llama):
    """The exact rule: under the key (target_tokens, sealed rank of length.order) every inside row sorts before every
    outside row. Rows may differ from the OLMo H1 even when their own counts agree: another row's count can shift the
    600-row cut at the boundary token count."""
    theirs = set(json.loads(STAGE1_H1.read_bytes())["remove"])
    mine = set(llama["h1"])
    view = s1.PreparedView(LLAMA, H.LLAMA_MANIFEST_SHA256)
    rank = s1.sealed_rank(view.tokens, "length.order")
    key = lambda r: (view.tokens[r], rank[r])
    assert max(key(r) for r in mine) < min(key(r) for r in view.tokens if r not in mine)
    olmo_view = s1.PreparedView(OLMO, H.OLMO_MANIFEST_SHA256)
    differ = {r for r in view.tokens if olmo_view.tokens[r] != view.tokens[r]}
    assert len(differ) == 100 and 0 < len(mine & theirs) <= 600
    for row in mine ^ theirs:                                   # a differing row sits at the boundary token count
        assert view.tokens[row] in (llama["manifest"]["cut_points"][0]["last_target_tokens"],
                                    llama["manifest"]["cut_points"][1]["first_target_tokens"]) or row in differ


def test_the_engine_accepts_llama_h1_against_the_llama_set_and_refuses_it_against_the_olmo_set(llama):
    # Id-only views (manifest hash, row ids, dev membership): what parse_edit reads of a prepared set. Not load_prepared.
    data = llama["files"]["edits/octile_0.json"]
    edit = parse_edit(data, s1.PreparedView(LLAMA, H.LLAMA_MANIFEST_SHA256).engine_stub())
    assert edit.arm == "edit-" + sha256_bytes(data) and len(edit.removed) == 600
    with pytest.raises(EditError, match="manifest_sha256"):
        parse_edit(data, s1.PreparedView(OLMO, H.OLMO_MANIFEST_SHA256).engine_stub())


def test_the_h1_script_never_writes_under_seal_the_anchor_list_or_stage1_from_any_repo(tmp_path, capsys):
    """B-M2 and B-M3: the guard names SEAL, the anchor list and stage 1's folder, resolved from the script's own
    checkout (REPO) and from --repo; the CLI refuses before it reads any input."""
    assert H.FORBIDDEN_DIRS == (".ai/inputs/gate-b-sealed-20261008", ".ai/inputs/gate-b-anchors-20261008",
                                ".ai/inputs/stage1-commitments-20261016")
    other = tmp_path / "other-checkout"
    other.mkdir()
    for forbidden in H.FORBIDDEN_DIRS:
        for repo in (REPO, other, None):
            with pytest.raises(s1.Refusal, match=f"refusing to write under {forbidden}"):
                H.guard_out(REPO / forbidden / "out" / "new", repo)
            with pytest.raises(s1.Refusal, match=f"refusing to write under {forbidden}"):
                H.guard_out(REPO / forbidden, repo)
        with pytest.raises(s1.Refusal, match="refusing to write under"):
            H.guard_out(other / forbidden / "out", other)
    H.guard_out(other / "somewhere" / "out", other)
    H.guard_out(tmp_path / "absent")
    seal_new = REPO / H.SEAL_DIR_REL / "out" / "h1-new"
    assert H.main(["--repo", str(other), "--out", str(seal_new)]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/gate-b-sealed-20261008" in capsys.readouterr().err
    assert not seal_new.exists()
    assert H.main(["--out", str(REPO / H.STAGE1_DIR_REL / "length-rules" / "x")]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/stage1-commitments-20261016" in capsys.readouterr().err


def test_a_rerun_gives_the_same_bytes_and_the_committed_out_equals_a_fresh_build(llama):
    again = H.build(LLAMA, H.LLAMA_MANIFEST_SHA256, REPO)
    assert again["files"] == llama["files"]
    if (COMMITTED_OUT / "MANIFEST.json").exists():
        on_disk = {p.relative_to(COMMITTED_OUT).as_posix(): p.read_bytes() for p in COMMITTED_OUT.rglob("*") if p.is_file()}
        assert on_disk == llama["files"]


def test_the_wrong_manifest_pin_refuses():
    with pytest.raises(s1.Refusal, match="manifest hashes to"):
        H.build(LLAMA, H.OLMO_MANIFEST_SHA256, REPO)


# ----- RV-1 and RV-2 (the second fix round): identity in the guard; the CLI guards --repo's own sealed folders -----------


def fake_checkout(root: Path) -> Path:
    """A checkout layout with the three forbidden folders' NAMES under tmp_path (the real sealed folders are never an
    argument here) and an ordinary folder; it holds no inputs, so a build from it can only refuse."""
    for rel in H.FORBIDDEN_DIRS:
        (root / rel / "out").mkdir(parents=True)
    (root / "somewhere").mkdir()
    return root


def case_insensitive(root: Path) -> bool:
    return (root / H.SEAL_DIR_REL.upper()).exists()


def test_the_guard_refuses_a_symlink_a_dotted_and_a_relative_path_into_a_sealed_folder(tmp_path, monkeypatch):
    """RV-1: path strings and directory identity (os.path.samefile on the deepest existing ancestor of --out and its
    parents) for each forbidden folder of REPO and --repo that exists; on a fake checkout, a symlink into the sealed
    folder, a symlinked checkout root, dotted and relative spellings refuse; a sibling with a shared prefix passes."""
    fake = fake_checkout(tmp_path / "fake-checkout")
    seal = fake / H.SEAL_DIR_REL
    link = tmp_path / "link-to-seal"
    link.symlink_to(seal, target_is_directory=True)
    repo_link = tmp_path / "link-to-checkout"
    repo_link.symlink_to(fake, target_is_directory=True)
    for out, repo in ((link / "out" / "new", fake), (seal / "out" / "new", repo_link),
                      (repo_link / H.SEAL_DIR_REL / "out" / "new", fake),
                      (fake / ".ai/inputs/elsewhere/../gate-b-sealed-20261008/./out/new", fake),
                      (fake / "somewhere/../.ai/inputs/gate-b-sealed-20261008", fake)):
        with pytest.raises(s1.Refusal, match="refusing to write under .ai/inputs/gate-b-sealed-20261008"):
            H.guard_out(out, repo)
    with pytest.raises(s1.Refusal, match="refusing to write under .ai/inputs/gate-b-anchors-20261008"):
        H.guard_out(fake / "somewhere/../.ai/inputs/gate-b-anchors-20261008/out/x", fake)
    monkeypatch.chdir(fake)
    for out in (Path(".ai/inputs/gate-b-sealed-20261008/out/new"), Path("./somewhere/../.ai/inputs/gate-b-sealed-20261008/out/new"),
                Path("somewhere/../.ai/inputs/gate-b-sealed-20261008")):
        with pytest.raises(s1.Refusal, match="refusing to write under .ai/inputs/gate-b-sealed-20261008"):
            H.guard_out(out, Path("."))
    with pytest.raises(s1.Refusal, match="refusing to write under .ai/inputs/stage1-commitments-20261016"):
        H.guard_out(Path(".ai/inputs/stage1-commitments-20261016/length-rules/edits"), Path("."))
    H.guard_out(fake / ".ai/inputs/gate-b-sealed-20261008-copy/out", fake)
    H.guard_out(fake / "somewhere" / "out", fake)
    H.guard_out(Path("somewhere/out"), Path("."))
    assert sorted(p.name for p in (seal / "out").iterdir()) == []


def test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder(tmp_path, capsys):
    """RV-1: on a case-insensitive filesystem (this Mac's APFS) a case-variant spelling is the same directory with
    another resolved string (resolve() keeps the typed case); identity refuses it for every forbidden folder, through
    the guard and through the CLI (nothing read, nothing written). Skipped on a case-sensitive filesystem."""
    fake = fake_checkout(tmp_path / "fake-checkout")
    if not case_insensitive(fake):
        pytest.skip("case-sensitive filesystem: a case-variant spelling is another folder")
    seal = fake / H.SEAL_DIR_REL
    variant = fake / ".ai/inputs/GATE-B-SEALED-20261008"
    assert str(variant.resolve()) != str(seal.resolve()) and os.path.samefile(variant, seal)
    for out, forbidden in ((variant / "out" / "new", H.SEAL_DIR_REL), (variant / "out", H.SEAL_DIR_REL), (variant, H.SEAL_DIR_REL),
                           (fake / ".ai/inputs/Gate-B-Anchors-20261008/out/x", H.ANCHORS_DIR_REL),
                           (fake / ".ai/INPUTS/stage1-commitments-20261016/length-rules/edits", H.STAGE1_DIR_REL),
                           (fake / "somewhere/../.ai/inputs/GATE-B-SEALED-20261008/out/new", H.SEAL_DIR_REL)):
        with pytest.raises(s1.Refusal, match=f"refusing to write under {forbidden}"):
            H.guard_out(out, fake)
    assert H.main(["--repo", str(fake), "--out", str(variant / "out" / "new")]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/gate-b-sealed-20261008 (nothing written)" in capsys.readouterr().err
    assert sorted(p.name for p in (seal / "out").iterdir()) == []


def test_the_h1_cli_refuses_an_output_under_the_given_repos_own_sealed_folders(tmp_path, capsys):
    """RV-2 (the re-verifier's G3): main passes --repo to the guard, so --out under --repo's SEAL, anchor list or
    stage-1 folder refuses with that folder's name, before any input is read (the fake checkout holds none) and with
    nothing written."""
    other = fake_checkout(tmp_path / "other-checkout")
    for forbidden in H.FORBIDDEN_DIRS:
        target = other / forbidden / "out" / "new"
        assert H.main(["--repo", str(other), "--out", str(target)]) == 2
        assert f"REFUSED: refusing to write under {forbidden} (nothing written)" in capsys.readouterr().err
        assert not target.exists() and sorted(p.name for p in (other / forbidden / "out").iterdir()) == []
