

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
