"""The Llama sealed set (T3): tests (a)-(g) of the build brief, on the real prepared sets (git-ignored copies under
tmp/kt-prepared/) and the committed SEAL and stage-1 r-draws files. No text is read or printed: only the wrapper's
id-only PreparedView reads the prepared sets (row_id, target_tokens, membership; the engine's parse_edit gets its
``engine_stub()``, never ``load_prepared``); the tests compare row ids, hashes and bytes only."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]            # conftest.py puts it on sys.path; named here for the paths
WRAPPER = Path(__file__).resolve().parents[1] / "build_sealed_llama3.py"

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from experiments.safety_selection.edits import EditError, parse_edit  # noqa: E402


def load_wrapper():
    spec = importlib.util.spec_from_file_location("build_sealed_llama3_under_test", WRAPPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


W = load_wrapper()

OLMO = REPO / W.OLMO_PREPARED_REL
LLAMA = REPO / W.LLAMA_PREPARED_REL
SEAL = REPO / W.SEAL_OUT_REL
RDRAWS = REPO / W.STAGE1_RDRAWS_REL
FROZEN = REPO / W.FROZEN_BUILDER_COMMITTED
COMMITTED_OUT = WRAPPER.parent / "out"
UNITS = ["g-17e0407f96fff5c4", "g-3e67494969af60f7", "g-3f941c4f200a3b80", "g-68b0b0b9b4eab64a",
         "g-6ed95fa3a2721a52", "g-b6eff9409b49296a", "g-c5b600a197ab9eb9", "g-efdeb5ae52612377"]

pytestmark = pytest.mark.skipif(not (OLMO / "manifest.json").exists() or not (LLAMA / "manifest.json").exists(),
                                reason="the prepared sets (git-ignored, tmp/kt-prepared/) are not in this checkout")


def sha(path):
    return sha256_bytes(path.read_bytes())


def remove_of(data: bytes) -> list[str]:
    return json.loads(data)["remove"]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """One build with the parity output, written into a scratch folder (never under SEAL or stage 1's folder)."""
    root = tmp_path_factory.mktemp("llama-sealed")
    before = sha(FROZEN)
    result = W.build(REPO, FROZEN, OLMO, LLAMA, SEAL, RDRAWS, olmo_parity=True)
    out, parity = root / "out", root / "parity"
    W.write_files(out, result["files"])
    W.write_files(parity, result["parity_files"])
    return {"result": result, "out": out, "parity": parity, "frozen_before": before, "frozen_after": sha(FROZEN)}


def seal_doc(rel: str) -> dict:
    return json.loads((SEAL / rel).read_bytes())


def stage1_doc(rel: str) -> dict:
    return json.loads((RDRAWS / rel).read_bytes())


# ----- (a) and (b): remove lists --------------------------------------------------------------------


def test_a_llama_remove_lists_equal_seal_for_d1_to_d5_and_the_units(built):
    files = built["result"]["files"]
    for d in range(1, 6):
        assert remove_of(files[f"edits/R_d{d}.json"]) == seal_doc(f"edits/R_d{d}.json")["remove"]
    for u in UNITS:
        assert remove_of(files[f"edits/unit_{u}.json"]) == seal_doc(f"edits/unit_{u}.json")["remove"]
        assert len(remove_of(files[f"edits/unit_{u}.json"])) == 600


def test_b_llama_remove_lists_equal_stage1_r_draws_for_d6_to_d10(built):
    files = built["result"]["files"]
    for d in range(6, 11):
        mine, theirs = remove_of(files[f"edits/R_d{d}.json"]), stage1_doc(f"edits/R_d{d}.json")["remove"]
        assert mine == theirs
        assert len(mine) == 600 == len(set(mine))


def test_every_llama_file_is_on_the_llama_manifest_with_600_distinct_rows_75_per_unit(built):
    files = built["result"]["files"]
    members = {g["group_id"]: set(g["members"])
               for g in json.loads((LLAMA / "engine/groups.json").read_bytes())["partitions"]["dev"]["groups"]}
    for d in range(1, 17):
        doc = json.loads(files[f"edits/R_d{d}.json"])
        assert doc["manifest_sha256"] == W.LLAMA_MANIFEST_SHA256
        assert doc["edit_kind"] == "remove" and doc["counts"] == {"remove": 600, "rewrite": 0, "add": 0}
        rows = doc["remove"]
        assert rows == sorted(set(rows)) and len(rows) == 600
        assert all(sum(1 for r in rows if r in members[u]) == 75 for u in UNITS)
        assert doc["provenance"]["seed"] == 1100 + d
        assert doc["provenance"]["selection"]["draw"] == d
        assert doc["provenance"]["frozen_builder"]["sha256"] == W.FROZEN_BUILDER_SHA256
        assert doc["provenance"]["builder_sha256"] == sha(WRAPPER)
    for u in UNITS:
        doc = json.loads(files[f"edits/unit_{u}.json"])
        assert doc["manifest_sha256"] == W.LLAMA_MANIFEST_SHA256
        assert set(doc["remove"]) == members[u]


def test_new_draws_d11_to_d16_are_distinct_from_each_other_and_from_d1_to_d10(built):
    files = built["result"]["files"]
    lists = {d: tuple(remove_of(files[f"edits/R_d{d}.json"])) for d in range(1, 17)}
    assert len(set(lists.values())) == 16
    for d in range(11, 17):
        assert json.loads(files[f"edits/R_d{d}.json"])["provenance"]["same_rows_as"]["file"] is None


OLMO_D11_16 = REPO / ".ai/inputs/scale-78b-r-draws-olmo2-20261105/out/edits"


@pytest.mark.skipif(not (OLMO_D11_16 / "R_d11.json").exists(), reason="the OLMo d = 11-16 folder is not built")
def test_llama_d11_to_d16_hold_the_same_rows_as_the_olmo_d11_to_d16_draws(built):
    files = built["result"]["files"]
    for d in range(11, 17):
        theirs = json.loads((OLMO_D11_16 / f"R_d{d}.json").read_bytes())
        mine = json.loads(files[f"edits/R_d{d}.json"])
        assert mine["remove"] == theirs["remove"]
        assert mine["provenance"]["selection"]["per_unit"] == theirs["provenance"]["selection"]["per_unit"]
        assert theirs["manifest_sha256"] == W.OLMO_MANIFEST_SHA256 and mine["manifest_sha256"] == W.LLAMA_MANIFEST_SHA256


# ----- (c): the OLMo parity -------------------------------------------------------------------------


def test_c_olmo_parity_reproduces_seal_d1_to_d5_and_the_units_byte_for_byte(built):
    parity = built["parity"]
    for d in range(1, 6):
        assert (parity / f"edits/R_d{d}.json").read_bytes() == (SEAL / f"edits/R_d{d}.json").read_bytes()
    for u in UNITS:
        assert (parity / f"edits/unit_{u}.json").read_bytes() == (SEAL / f"edits/unit_{u}.json").read_bytes()
    listed = {f["path"]: f["sha256"] for f in json.loads((SEAL / "MANIFEST.json").read_bytes())["files"]}
    assert sha(SEAL / "MANIFEST.json") == W.SEAL_MANIFEST_SHA256
    for d in range(1, 6):
        assert listed[f"edits/R_d{d}.json"] == sha(parity / f"edits/R_d{d}.json")


def test_c_olmo_parity_reproduces_stage1_d6_to_d10(built):
    """Byte for byte with REQ-4's stage1_wrapper block re-derived; in any case equal outside that block and in the
    remove list (the brief's fallback: list equality plus the differing fields named)."""
    parity = built["parity"]
    report = json.loads((parity / "PARITY.json").read_bytes())["stage1_r_draws"]["files"]
    record = {f["file"]: f for f in json.loads((RDRAWS / "r_draws_record.json").read_bytes())["files"]}
    for d in range(6, 11):
        rel = f"edits/R_d{d}.json"
        mine, theirs = json.loads((parity / rel).read_bytes()), stage1_doc(rel)
        assert mine["remove"] == theirs["remove"]
        strip = lambda doc: {**doc, "provenance": {k: v for k, v in doc["provenance"].items() if k != "stage1_wrapper"}}
        assert strip(mine) == strip(theirs)
        assert report[rel]["remove_list_equal"] and report[rel]["equal_without_stage1_wrapper"]
        assert record[rel]["sha256"] == sha(RDRAWS / rel)
        differing = report[rel].get("differing_stage1_wrapper_fields", [])
        assert (parity / rel).read_bytes() == (RDRAWS / rel).read_bytes(), \
            f"R_d{d}: not byte-identical; the stage1_wrapper fields that differ: {differing}"
        assert report[rel]["byte_identical"] is True


# ----- (d): the engine's parse_edit against the real prepared sets -------------------------------------


def test_d_parse_edit_accepts_each_llama_file_against_the_llama_set_and_refuses_it_against_the_olmo_set(built):
    # Id-only views of both prepared sets (manifest hash, row ids, dev membership): exactly what the engine's parse_edit
    # reads of a prepared set (BLD's EnginePrepared pattern). Not load_prepared, which reads query_rows.jsonl (text).
    llama = W.PreparedView(LLAMA, W.LLAMA_MANIFEST_SHA256).engine_stub()
    olmo = W.PreparedView(OLMO, W.OLMO_MANIFEST_SHA256).engine_stub()
    assert set(vars(llama)) == {"manifest_sha256", "train_rows", "groups"} and len(llama.train_rows) == 4800
    files = built["result"]["files"]
    edits = {k: v for k, v in files.items() if k.startswith("edits/")}
    assert len(edits) == 24
    for rel, data in edits.items():
        edit = parse_edit(data, llama)
        assert edit.removed == frozenset(remove_of(data)) and edit.arm == "edit-" + sha256_bytes(data)
        with pytest.raises(EditError, match="manifest_sha256"):
            parse_edit(data, olmo)
    # and SEAL's files, in turn, are refused against the Llama set
    with pytest.raises(EditError, match="manifest_sha256"):
        parse_edit((SEAL / "edits/R_d1.json").read_bytes(), llama)


# ----- (e): the trap ---------------------------------------------------------------------------------


def trap_prepared(root, llama_root, move_member: bool):
    """A Llama-like prepared set with the real group ids and member lists (ids only) and synthetic rows holding only
    row_id and target_tokens; with move_member one row moves from the first unit to the second. The manifest holds
    only the fields the wrapper reads."""
    groups = json.loads((llama_root / "engine/groups.json").read_bytes())
    manifest_src = json.loads((llama_root / "manifest.json").read_bytes())
    dev = groups["partitions"]["dev"]["groups"]
    if move_member:
        dev.sort(key=lambda g: g["group_id"])
        row = sorted(dev[0]["members"])[0]
        dev[0]["members"].remove(row)
        dev[1]["members"].append(row)
    (root / "engine").mkdir(parents=True)
    groups_bytes = canonical_json(groups)
    rows = sorted(r for g in dev for r in g["members"])
    train = "".join(json.dumps({"row_id": r, "target_tokens": 1 + (i % 7)}) + "\n" for i, r in enumerate(rows)).encode()
    (root / "engine/groups.json").write_bytes(groups_bytes)
    (root / "engine/train_rows.jsonl").write_bytes(train)
    manifest = {"files": {"engine/groups.json": sha256_bytes(groups_bytes), "engine/train_rows.jsonl": sha256_bytes(train)},
                "corpus": {"rows": len(rows)}, "groups": {"heldout": {"members": 0}},
                "units": {g: {"category": manifest_src["units"][g]["category"]} for g in manifest_src["units"]}}
    data = canonical_json(manifest)
    (root / "manifest.json").write_bytes(data)
    return sha256_bytes(data)


def test_e_a_manifest_with_one_member_moved_makes_the_wrapper_refuse(tmp_path):
    trap_root = tmp_path / "trap"
    trap_sha = trap_prepared(trap_root, LLAMA, move_member=True)
    frozen = W.load_frozen(FROZEN)
    inputs = frozen.Inputs(OLMO)
    with pytest.raises(W.Refusal, match="member lists differ"):
        W.check_membership(inputs, W.PreparedView(trap_root, trap_sha))
    with pytest.raises(W.Refusal, match="member lists differ"):
        W.build(REPO, FROZEN, OLMO, trap_root, SEAL, RDRAWS, llama_manifest_sha256=trap_sha)
    # the same construction without the move passes the membership check (so the trap is the only cause)
    ok_root = tmp_path / "ok"
    ok_sha = trap_prepared(ok_root, LLAMA, move_member=False)
    assert W.check_membership(inputs, W.PreparedView(ok_root, ok_sha))["member_lists_equal"] is True
    # and the pinned manifest refuses the trap set outright
    with pytest.raises(W.Refusal, match="manifest hashes to"):
        W.PreparedView(trap_root, W.LLAMA_MANIFEST_SHA256)


def test_the_wrapper_refuses_a_changed_frozen_builder_and_never_writes_under_seal_or_stage1(tmp_path):
    changed = tmp_path / "build_sealed.py"
    changed.write_bytes(FROZEN.read_bytes() + b"\n# one byte more\n")
    with pytest.raises(W.Refusal, match="frozen builder hashes to"):
        W.load_frozen(changed)
    with pytest.raises(W.Refusal, match="refusing to write under"):
        W.guard_out(SEAL / "new", REPO)
    with pytest.raises(W.Refusal, match="refusing to write under"):
        W.guard_out(RDRAWS / "edits", REPO)
    with pytest.raises(W.Refusal, match="refusing to write under"):
        W.guard_out(REPO / W.STAGE1_DIR_REL, REPO)
    with pytest.raises(W.Refusal, match="refusing to write under .ai/inputs/gate-b-anchors-20261008"):
        W.guard_out(REPO / W.ANCHORS_DIR_REL / "out" / "new", REPO)
    assert W.FORBIDDEN_DIRS == (W.SEAL_DIR_REL, W.ANCHORS_DIR_REL, W.STAGE1_DIR_REL)
    full = tmp_path / "full"
    full.mkdir()
    (full / "x").write_bytes(b"x")
    with pytest.raises(W.Refusal, match="not empty"):
        W.guard_out(full, REPO)
    W.guard_out(tmp_path / "absent", REPO)
    W.guard_out(tmp_path / "absent")                                    # repo optional: REPO alone guards


def test_a_non_default_repo_cannot_aim_the_output_into_this_checkouts_sealed_folders(tmp_path, capsys):
    """B-M3: the forbidden folders resolve from the script's own checkout (REPO), not only from --repo. With
    --repo elsewhere, --out under this checkout's SEAL, anchors or stage-1 folder still refuses; so does --out under
    the other checkout's sealed folders; and the CLI refuses before it reads any input."""
    other = tmp_path / "other-checkout"
    other.mkdir()
    for target in (SEAL / "new", REPO / W.ANCHORS_DIR_REL / "x", RDRAWS / "edits", REPO / W.STAGE1_DIR_REL):
        with pytest.raises(W.Refusal, match="refusing to write under"):
            W.guard_out(target, other)
    for forbidden in W.FORBIDDEN_DIRS:                                  # the other checkout's folders refuse too
        with pytest.raises(W.Refusal, match="refusing to write under"):
            W.guard_out(other / forbidden / "out", other)
    W.guard_out(other / "somewhere" / "out", other)                     # an ordinary folder passes
    assert W.main(["--repo", str(other), "--out", str(SEAL / "new")]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/gate-b-sealed-20261008" in capsys.readouterr().err
    assert not (SEAL / "new").exists()
    assert W.main(["--repo", str(other), "--out", str(tmp_path / "ok"), "--olmo-parity-out", str(RDRAWS / "p")]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/stage1-commitments-20261016" in capsys.readouterr().err
    assert not (tmp_path / "ok").exists() and not (RDRAWS / "p").exists()


def test_the_wrapper_refuses_a_tampered_sealed_file(tmp_path, built):
    """A SEAL copy whose R_d3 lists another row (its MANIFEST re-hashed) makes the reproduction refuse."""
    copy = tmp_path / "seal"
    shutil.copytree(SEAL, copy)
    doc = json.loads((copy / "edits/R_d3.json").read_bytes())
    doc["remove"][0] = doc["remove"][0][:-1] + ("0" if doc["remove"][0][-1] != "0" else "1")
    data = canonical_json(doc)
    (copy / "edits/R_d3.json").write_bytes(data)
    manifest = json.loads((copy / "MANIFEST.json").read_bytes())
    for f in manifest["files"]:
        if f["path"] == "edits/R_d3.json":
            f["sha256"] = sha256_bytes(data)
    (copy / "MANIFEST.json").write_bytes(canonical_json(manifest))
    frozen = W.load_frozen(FROZEN)
    inputs = frozen.Inputs(OLMO)
    seal = W.seal_files(copy, sha(copy / "MANIFEST.json"))
    with pytest.raises(W.Refusal, match="R_3: the frozen builder's draw differs"):
        W.reproduce_olmo(frozen, inputs, W.recorded_base(seal, inputs), seal, W.stage1_files(RDRAWS), REPO, False)


# ----- (f) and (g): BLD unchanged; re-run gives the same bytes ------------------------------------------


def test_f_the_frozen_builder_is_unchanged_after_the_build(built):
    assert built["frozen_before"] == built["frozen_after"] == W.FROZEN_BUILDER_SHA256
    assert sha(REPO / W.FROZEN_BUILDER_TMP) == W.FROZEN_BUILDER_SHA256 if (REPO / W.FROZEN_BUILDER_TMP).exists() else True


def test_g_a_rerun_gives_the_same_bytes_including_the_manifest(built, tmp_path):
    again = W.build(REPO, FROZEN, OLMO, LLAMA, SEAL, RDRAWS, olmo_parity=True)
    assert again["files"] == built["result"]["files"]
    assert again["parity_files"] == built["result"]["parity_files"]
    assert set(again["files"]) == {f"edits/R_d{d}.json" for d in range(1, 17)} | \
        {f"edits/unit_{u}.json" for u in UNITS} | {"MANIFEST.json"}


@pytest.mark.skipif(not (COMMITTED_OUT / "MANIFEST.json").exists(), reason="no committed out/ beside the wrapper yet")
def test_g_the_committed_out_folder_equals_a_fresh_build(built):
    files = built["result"]["files"]
    on_disk = {p.relative_to(COMMITTED_OUT).as_posix(): p.read_bytes() for p in COMMITTED_OUT.rglob("*") if p.is_file()}
    assert on_disk == files
    manifest = json.loads(on_disk["MANIFEST.json"])
    for record in manifest["files"]:
        assert sha256_bytes(on_disk[record["path"]]) == record["sha256"]
        assert record["arm"] == "edit-" + record["sha256"]
    assert manifest["builder"]["sha256"] == sha(WRAPPER)
    assert len(manifest["files"]) == 24


def test_the_manifest_records_the_parity_and_the_membership_check(built):
    manifest = built["result"]["manifest"]
    assert manifest["membership_check"]["member_lists_equal"] and manifest["membership_check"]["row_ids_equal"]
    assert manifest["membership_check"]["training_rows"] == 4800 and manifest["membership_check"]["units"] == 8
    sealed = manifest["parity"]["sealed"]["files"]
    assert all(sealed[f"edits/R_d{d}.json"]["byte_identical"] for d in range(1, 6))
    assert all(sealed[f"edits/unit_{u}.json"]["byte_identical"] for u in UNITS)
    stage1 = manifest["parity"]["stage1_r_draws"]["files"]
    assert all(stage1[f"edits/R_d{d}.json"]["remove_list_equal"] for d in range(6, 11))
    assert "built_at_utc" not in manifest
    assert {r["seed"] for r in manifest["files"] if r["family"] == "R"} == set(range(1101, 1117))


# ----- RV-1 (the second fix round): the guard compares folders by identity, on a fake checkout layout ----------------------


def fake_checkout(root: Path) -> Path:
    """A checkout layout with the three forbidden folders' NAMES under tmp_path (the real sealed folders are never an
    argument here): <root>/.ai/inputs/gate-b-sealed-20261008/out, .../gate-b-anchors-20261008/out,
    .../stage1-commitments-20261016/out, and an ordinary folder."""
    for rel in W.FORBIDDEN_DIRS:
        (root / rel / "out").mkdir(parents=True)
    (root / "somewhere").mkdir()
    return root


def case_insensitive(root: Path) -> bool:
    """Whether a case-variant spelling names the same directory on this filesystem (this Mac's APFS: yes)."""
    return (root / W.SEAL_DIR_REL.upper()).exists()


def test_the_guard_refuses_a_symlink_a_dotted_and_a_relative_path_into_a_sealed_folder(tmp_path, monkeypatch):
    """RV-1: the guard compares the resolved path strings AND directory identity (os.path.samefile on the deepest
    existing ancestor of --out and its parents) for each forbidden folder of REPO and --repo that exists. On a fake
    checkout: a symlink into the sealed folder, a symlinked checkout root, dotted and relative spellings refuse; a
    sibling with a shared prefix and an ordinary folder pass; nothing is written."""
    fake = fake_checkout(tmp_path / "fake-checkout")
    seal = fake / W.SEAL_DIR_REL
    link = tmp_path / "link-to-seal"
    link.symlink_to(seal, target_is_directory=True)
    repo_link = tmp_path / "link-to-checkout"
    repo_link.symlink_to(fake, target_is_directory=True)
    for out, repo in ((link / "out" / "new", fake), (seal / "out" / "new", repo_link),
                      (repo_link / W.SEAL_DIR_REL / "out" / "new", fake),
                      (fake / ".ai/inputs/elsewhere/../gate-b-sealed-20261008/./out/new", fake),
                      (fake / "somewhere/../.ai/inputs/gate-b-sealed-20261008", fake)):
        with pytest.raises(W.Refusal, match="refusing to write under .ai/inputs/gate-b-sealed-20261008"):
            W.guard_out(out, repo)
    with pytest.raises(W.Refusal, match="refusing to write under .ai/inputs/gate-b-anchors-20261008"):
        W.guard_out(fake / "somewhere/../.ai/inputs/gate-b-anchors-20261008/out/x", fake)
    monkeypatch.chdir(fake)                                             # relative paths, cwd = the fake checkout
    for out in (Path(".ai/inputs/gate-b-sealed-20261008/out/new"), Path("./somewhere/../.ai/inputs/gate-b-sealed-20261008/out/new"),
                Path("somewhere/../.ai/inputs/gate-b-sealed-20261008")):
        with pytest.raises(W.Refusal, match="refusing to write under .ai/inputs/gate-b-sealed-20261008"):
            W.guard_out(out, Path("."))
    with pytest.raises(W.Refusal, match="refusing to write under .ai/inputs/stage1-commitments-20261016"):
        W.guard_out(Path(".ai/inputs/stage1-commitments-20261016/r-draws/edits"), Path("."))
    W.guard_out(fake / ".ai/inputs/gate-b-sealed-20261008-copy/out", fake)  # a sibling with a shared prefix passes
    W.guard_out(fake / "somewhere" / "out", fake)
    W.guard_out(Path("somewhere/out"), Path("."))
    assert sorted(p.name for p in (seal / "out").iterdir()) == []


def test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder(tmp_path, capsys):
    """RV-1: on this Mac's case-insensitive APFS, .ai/inputs/GATE-B-SEALED-20261008/out/new names a folder inside the
    sealed folder while its resolved string differs (resolve() keeps the typed case); identity refuses it, for every
    forbidden folder, through the guard and through the CLI (nothing read, nothing written). Skipped on a case-sensitive
    filesystem, where the spelling is another folder."""
    fake = fake_checkout(tmp_path / "fake-checkout")
    if not case_insensitive(fake):
        pytest.skip("case-sensitive filesystem: a case-variant spelling is another folder")
    seal = fake / W.SEAL_DIR_REL
    variant = fake / ".ai/inputs/GATE-B-SEALED-20261008"
    assert str(variant.resolve()) != str(seal.resolve()) and os.path.samefile(variant, seal)
    for out, forbidden in ((variant / "out" / "new", W.SEAL_DIR_REL), (variant / "out", W.SEAL_DIR_REL), (variant, W.SEAL_DIR_REL),
                           (fake / ".ai/inputs/Gate-B-Anchors-20261008/out/x", W.ANCHORS_DIR_REL),
                           (fake / ".ai/INPUTS/stage1-commitments-20261016/r-draws/edits", W.STAGE1_DIR_REL),
                           (fake / "somewhere/../.ai/inputs/GATE-B-SEALED-20261008/out/new", W.SEAL_DIR_REL)):
        with pytest.raises(W.Refusal, match=f"refusing to write under {forbidden}"):
            W.guard_out(out, fake)
    assert W.main(["--repo", str(fake), "--out", str(variant / "out" / "new")]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/gate-b-sealed-20261008 (nothing written)" in capsys.readouterr().err
    assert W.main(["--repo", str(fake), "--out", str(tmp_path / "ok"), "--olmo-parity-out", str(variant / "out" / "p")]) == 2
    assert "REFUSED: refusing to write under .ai/inputs/gate-b-sealed-20261008 (nothing written)" in capsys.readouterr().err
    assert sorted(p.name for p in (seal / "out").iterdir()) == [] and not (tmp_path / "ok").exists()
