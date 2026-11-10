"""The OLMo draws d = 11..16 (P78 section 9.2 item 3): the frozen builder reproduced first, the new draws by it, on the
real OLMo prepared set (git-ignored copy under tmp/kt-prepared/). Row ids, hashes and bytes only; no text: the engine's
parse_edit gets stage 1's id-only ``s1common.PreparedView(...).engine_stub()``, never ``load_prepared``."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]            # conftest.py puts it on sys.path; named here for the paths

from experiments.safety_selection.common import canonical_json, derive_seed, sha256_bytes  # noqa: E402
from experiments.safety_selection.edits import EditError, parse_edit  # noqa: E402
from scripts.scale78b import build_r_draws_78b as B  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402  (read-only: its id-only PreparedView)

OLMO = REPO / B.PREPARED_REL
LLAMA = REPO / "tmp/kt-prepared/prepared-kt-dolly-llama3"
SEAL = REPO / B.SEAL_OUT_REL
RDRAWS = REPO / B.STAGE1_RDRAWS_REL
FROZEN = REPO / B.FROZEN_BUILDER_COMMITTED
COMMITTED_OUT = REPO / B.OUT_REL
SCRIPT = REPO / B.SCRIPT_REL

pytestmark = pytest.mark.skipif(not (OLMO / "manifest.json").exists(),
                                reason="the OLMo prepared set (git-ignored, tmp/kt-prepared/) is not in this checkout")


def sha(path):
    return sha256_bytes(path.read_bytes())


@pytest.fixture(scope="module")
def built():
    before = sha(FROZEN)
    result = B.build(REPO, FROZEN, OLMO, SEAL, RDRAWS)
    return {"result": result, "before": before, "after": sha(FROZEN)}


def test_the_sealed_and_stage1_draws_are_reproduced_before_anything_is_drawn(built):
    rep = built["result"]["manifest"]["reproduction"]
    listed = {f["path"]: f["sha256"] for f in json.loads((SEAL / "MANIFEST.json").read_bytes())["files"]}
    for d in range(1, 6):
        rel = f"edits/R_d{d}.json"
        assert rep["sealed"]["files"][rel]["byte_identical"] and rep["sealed"]["files"][rel]["sha256"] == listed[rel]
    record = {f["file"]: f["sha256"] for f in json.loads((RDRAWS / "r_draws_record.json").read_bytes())["files"]}
    for d in range(6, 11):
        rel = f"edits/R_d{d}.json"
        assert rep["stage1_r_draws"]["files"][rel]["remove_list_equal"]
        assert rep["stage1_r_draws"]["files"][rel]["sha256"] == record[rel] == sha(RDRAWS / rel)


def test_d11_to_d16_are_600_distinct_rows_75_per_unit_with_the_frozen_stream_seeds(built):
    files = built["result"]["files"]
    members = {g["group_id"]: set(g["members"])
               for g in json.loads((OLMO / "engine/groups.json").read_bytes())["partitions"]["dev"]["groups"]}
    earlier = [tuple(json.loads((SEAL / f"edits/R_d{d}.json").read_bytes())["remove"]) for d in range(1, 6)] + \
              [tuple(json.loads((RDRAWS / f"edits/R_d{d}.json").read_bytes())["remove"]) for d in range(6, 11)]
    seen = set(earlier)
    for d in range(11, 17):
        doc = json.loads(files[f"edits/R_d{d}.json"])
        rows = doc["remove"]
        assert rows == sorted(set(rows)) and len(rows) == 600
        assert all(sum(1 for r in rows if r in members[u]) == 75 for u in sorted(members))
        assert doc["manifest_sha256"] == B.PREPARED_MANIFEST_SHA256
        assert doc["provenance"]["builder_sha256"] == B.FROZEN_BUILDER_SHA256
        sel = doc["provenance"]["selection"]
        assert sel["draw"] == d and sel["stream"] == "gate-b-random-removal-v1" and sel["design_seed"] == 20261008
        for unit in sel["per_unit"]:
            assert unit["seed"] == derive_seed(20261008, "gate-b-random-removal-v1", d, unit["group_id"])
        wrapper = doc["provenance"]["scale78b_wrapper"]
        assert wrapper["seed"] == 1100 + d and wrapper["script_sha256"] == sha(SCRIPT)
        assert tuple(rows) not in seen
        seen.add(tuple(rows))
    assert len(seen) == 16


def test_the_engine_accepts_each_file_against_the_olmo_set_and_refuses_it_against_the_llama_set(built):
    # Id-only views (manifest hash, row ids, dev membership): what parse_edit reads of a prepared set. Not load_prepared.
    olmo = s1.PreparedView(OLMO, B.PREPARED_MANIFEST_SHA256).engine_stub()
    assert olmo.manifest_sha256 == B.PREPARED_MANIFEST_SHA256 and len(olmo.train_rows) == 4800
    for d in range(11, 17):
        data = built["result"]["files"][f"edits/R_d{d}.json"]
        edit = parse_edit(data, olmo)
        assert edit.arm == "edit-" + sha256_bytes(data) and len(edit.removed) == 600
    if (LLAMA / "manifest.json").exists():
        llama = s1.PreparedView(LLAMA, "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a").engine_stub()
        with pytest.raises(EditError, match="manifest_sha256"):
            parse_edit(built["result"]["files"]["edits/R_d11.json"], llama)


def test_the_frozen_builder_is_unchanged_and_a_rerun_gives_the_same_bytes(built):
    assert built["before"] == built["after"] == B.FROZEN_BUILDER_SHA256
    again = B.build(REPO, FROZEN, OLMO, SEAL, RDRAWS)
    assert again["files"] == built["result"]["files"]
    assert "built_at_utc" not in again["manifest"]


@pytest.mark.skipif(not (COMMITTED_OUT / "MANIFEST.json").exists(), reason="no committed out/ yet")
def test_the_committed_out_folder_equals_a_fresh_build(built):
    on_disk = {p.relative_to(COMMITTED_OUT).as_posix(): p.read_bytes() for p in COMMITTED_OUT.rglob("*") if p.is_file()}
    assert on_disk == built["result"]["files"]
    manifest = json.loads(on_disk["MANIFEST.json"])
    assert [r["path"] for r in manifest["files"]] == [f"edits/R_d{d}.json" for d in range(11, 17)]
    for r in manifest["files"]:
        assert sha256_bytes(on_disk[r["path"]]) == r["sha256"] and r["arm"] == "edit-" + r["sha256"]


def test_a_tampered_sealed_file_or_a_changed_frozen_builder_refuses(tmp_path):
    copy = tmp_path / "seal"
    shutil.copytree(SEAL, copy)
    doc = json.loads((copy / "edits/R_d2.json").read_bytes())
    doc["remove"] = doc["remove"][1:] + [doc["remove"][0][:-1] + ("0" if doc["remove"][0][-1] != "0" else "1")]
    doc["remove"].sort()
    data = canonical_json(doc)
    (copy / "edits/R_d2.json").write_bytes(data)
    manifest = json.loads((copy / "MANIFEST.json").read_bytes())
    for f in manifest["files"]:
        if f["path"] == "edits/R_d2.json":
            f["sha256"] = sha256_bytes(data)
    (copy / "MANIFEST.json").write_bytes(canonical_json(manifest))
    frozen = B.load_frozen(FROZEN)
    inputs = frozen.Inputs(OLMO)
    seal = B.seal_r_files(copy, sha(copy / "MANIFEST.json"))
    with pytest.raises(B.Refusal, match="R_2: the frozen builder's draw differs"):
        B.reproduce(frozen, inputs, B.recorded_base(seal, inputs), seal, B.stage1_r_files(RDRAWS))
    with pytest.raises(B.Refusal, match="sealed MANIFEST.json hashes to"):
        B.seal_r_files(copy)
    changed = tmp_path / "build_sealed.py"
    changed.write_bytes(FROZEN.read_bytes() + b"#\n")
    with pytest.raises(B.Refusal, match="frozen builder hashes to"):
        B.load_frozen(changed)
    for forbidden in (SEAL / "x", RDRAWS / "edits", REPO / B.STAGE1_DIR_REL / "r-draws-2", REPO / B.ANCHORS_DIR_REL / "out"):
        with pytest.raises(B.Refusal, match="refusing to write under"):
            B.guard_out(forbidden, REPO)
    assert B.FORBIDDEN_DIRS == (B.SEAL_DIR_REL, B.ANCHORS_DIR_REL, B.STAGE1_DIR_REL)


def test_a_non_default_repo_cannot_aim_the_output_into_this_checkouts_sealed_folders(tmp_path, capsys):
    """B-M3: the forbidden folders resolve from the script's own checkout (REPO) and from --repo; the CLI refuses
    before it reads any input."""
    other = tmp_path / "other-checkout"
    other.mkdir()
    for target in (SEAL / "new", REPO / B.ANCHORS_DIR_REL / "x", RDRAWS / "edits", REPO / B.STAGE1_DIR_REL):
        with pytest.raises(B.Refusal, match="refusing to write under"):
            B.guard_out(target, other)
    for forbidden in B.FORBIDDEN_DIRS:
        with pytest.raises(B.Refusal, match="refusing to write under"):
            B.guard_out(other / forbidden / "out", other)
    B.guard_out(other / "somewhere" / "out", other)
    B.guard_out(tmp_path / "absent")                                    # repo optional: REPO alone guards
    assert B.main(["--repo", str(other), "--out", str(SEAL / "new")]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/gate-b-sealed-20261008" in capsys.readouterr().err
    assert not (SEAL / "new").exists()
    assert B.main(["--repo", str(other), "--out", str(RDRAWS / "edits-2")]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/stage1-commitments-20261016" in capsys.readouterr().err
    assert not (RDRAWS / "edits-2").exists()


# ----- RV-1 and RV-2 (the second fix round): identity in the guard; the absent-or-empty rule as a behaviour test ----------


def fake_checkout(root: Path) -> Path:
    """A checkout layout with the three forbidden folders' NAMES under tmp_path (the real sealed folders are never an
    argument here) and an ordinary folder."""
    for rel in B.FORBIDDEN_DIRS:
        (root / rel / "out").mkdir(parents=True)
    (root / "somewhere").mkdir()
    return root


def case_insensitive(root: Path) -> bool:
    return (root / B.SEAL_DIR_REL.upper()).exists()


def test_the_guard_refuses_a_symlink_a_dotted_and_a_relative_path_into_a_sealed_folder(tmp_path, monkeypatch):
    """RV-1: path strings and directory identity (os.path.samefile on the deepest existing ancestor of --out and its
    parents) for each forbidden folder of REPO and --repo that exists; on a fake checkout, a symlink into the sealed
    folder, a symlinked checkout root, dotted and relative spellings refuse; a sibling with a shared prefix passes."""
    fake = fake_checkout(tmp_path / "fake-checkout")
    seal = fake / B.SEAL_DIR_REL
    link = tmp_path / "link-to-seal"
    link.symlink_to(seal, target_is_directory=True)
    repo_link = tmp_path / "link-to-checkout"
    repo_link.symlink_to(fake, target_is_directory=True)
    for out, repo in ((link / "out" / "new", fake), (seal / "out" / "new", repo_link),
                      (repo_link / B.SEAL_DIR_REL / "out" / "new", fake),
                      (fake / ".ai/inputs/elsewhere/../gate-b-sealed-20261008/./out/new", fake),
                      (fake / "somewhere/../.ai/inputs/gate-b-sealed-20261008", fake)):
        with pytest.raises(B.Refusal, match="refusing to write under .ai/inputs/gate-b-sealed-20261008"):
            B.guard_out(out, repo)
    with pytest.raises(B.Refusal, match="refusing to write under .ai/inputs/gate-b-anchors-20261008"):
        B.guard_out(fake / "somewhere/../.ai/inputs/gate-b-anchors-20261008/out/x", fake)
    monkeypatch.chdir(fake)
    for out in (Path(".ai/inputs/gate-b-sealed-20261008/out/new"), Path("./somewhere/../.ai/inputs/gate-b-sealed-20261008/out/new"),
                Path("somewhere/../.ai/inputs/gate-b-sealed-20261008")):
        with pytest.raises(B.Refusal, match="refusing to write under .ai/inputs/gate-b-sealed-20261008"):
            B.guard_out(out, Path("."))
    with pytest.raises(B.Refusal, match="refusing to write under .ai/inputs/stage1-commitments-20261016"):
        B.guard_out(Path(".ai/inputs/stage1-commitments-20261016/r-draws/edits"), Path("."))
    B.guard_out(fake / ".ai/inputs/gate-b-sealed-20261008-copy/out", fake)
    B.guard_out(fake / "somewhere" / "out", fake)
    B.guard_out(Path("somewhere/out"), Path("."))
    assert sorted(p.name for p in (seal / "out").iterdir()) == []


def test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder(tmp_path, capsys):
    """RV-1: on a case-insensitive filesystem (this Mac's APFS) a case-variant spelling is the same directory with
    another resolved string (resolve() keeps the typed case); identity refuses it for every forbidden folder, through
    the guard and through the CLI (nothing read, nothing written). Skipped on a case-sensitive filesystem."""
    fake = fake_checkout(tmp_path / "fake-checkout")
    if not case_insensitive(fake):
        pytest.skip("case-sensitive filesystem: a case-variant spelling is another folder")
    seal = fake / B.SEAL_DIR_REL
    variant = fake / ".ai/inputs/GATE-B-SEALED-20261008"
    assert str(variant.resolve()) != str(seal.resolve()) and os.path.samefile(variant, seal)
    for out, forbidden in ((variant / "out" / "new", B.SEAL_DIR_REL), (variant / "out", B.SEAL_DIR_REL), (variant, B.SEAL_DIR_REL),
                           (fake / ".ai/inputs/Gate-B-Anchors-20261008/out/x", B.ANCHORS_DIR_REL),
                           (fake / ".ai/INPUTS/stage1-commitments-20261016/r-draws/edits", B.STAGE1_DIR_REL),
                           (fake / "somewhere/../.ai/inputs/GATE-B-SEALED-20261008/out/new", B.SEAL_DIR_REL)):
        with pytest.raises(B.Refusal, match=f"refusing to write under {forbidden}"):
            B.guard_out(out, fake)
    assert B.main(["--repo", str(fake), "--out", str(variant / "out" / "new")]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/gate-b-sealed-20261008 (nothing written)" in capsys.readouterr().err
    assert sorted(p.name for p in (seal / "out").iterdir()) == []


def test_the_r_draws_guard_refuses_a_folder_that_exists_and_is_not_empty(tmp_path, capsys):
    """RV-2 (the re-verifier's G1): the absent-or-empty rule is the guard's own refusal, through guard_out and through
    the CLI, which refuses before it reads any input and leaves the folder as it was; an empty or an absent folder
    passes."""
    full = tmp_path / "full"
    full.mkdir()
    (full / "MANIFEST.json").write_bytes(b"{}")
    with pytest.raises(B.Refusal, match="exists and is not empty: a sealed build never overwrites"):
        B.guard_out(full, REPO)
    with pytest.raises(B.Refusal, match="not empty"):
        B.guard_out(full)
    empty = tmp_path / "empty"
    empty.mkdir()
    B.guard_out(empty, REPO)
    B.guard_out(tmp_path / "absent" / "deeper", REPO)
    assert B.main(["--out", str(full)]) == 2
    assert "exists and is not empty: a sealed build never overwrites (nothing written)" in capsys.readouterr().err
    assert [p.name for p in full.iterdir()] == ["MANIFEST.json"] and (full / "MANIFEST.json").read_bytes() == b"{}"
