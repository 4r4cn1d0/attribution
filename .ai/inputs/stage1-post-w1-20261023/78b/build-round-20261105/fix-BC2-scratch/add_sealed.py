

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
