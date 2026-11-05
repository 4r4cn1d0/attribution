

# ----- RV-2 (the second fix round): the re-verifier's test gaps, each with a mutant that dies on it only ------------------

REC_1B = ROOT / "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"
SYNTHETIC_ENVIRONMENT = {"python": "3.11.9", "machine": "x86_64", "device": "cuda", "packages": {"torch": "2.4.0"},
                         "deterministic_algorithms": True, "safety_selection_numeric": "v1",
                         "cuda": {"name": "A100", "capability": "8.0", "torch_cuda_runtime": "12.1", "cudnn": 8902,
                                  "settings": {}, "env": {}}}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def synthetic_r_unit(folder: Path, edit_bytes: bytes, seed: int, arm: str | None = None) -> dict:
    """A sealed olmo2-1b R unit holding the metadata read_unit reads and nothing else (no eval output, no text):
    job.json, identity.json (REC 1B's recipe, the family's training identity), assets.json (a CUDA environment record,
    a policy and a guard block, the lock's hash), edit.json (the bytes given), the lock, and a COMPLETE.json that lists
    exactly those files with their hashes. The arm defaults to edit-<SHA-256 of edit.json>; another arm makes the unit
    name an edit file that is not its own. Returns the inputs entry {path, complete_sha256, arm}."""
    folder.mkdir(parents=True)
    recipe = json.loads(REC_1B.read_text(encoding="utf-8"))
    fam = nr.FAMILIES["olmo2-1b"]
    recipe_sha = nr.GB.canonical_sha256(recipe)
    arm = arm or "edit-" + sha256_bytes(edit_bytes)
    lock = b"environment-lock-bytes\n"
    job = {"kind": "run-one", "target_checkpoint": "e1", "replicate_of": None, "resume_from": None, "evaluate_bank": "dev",
           "split": "dev", "role": "development", "seed": seed, "arm": arm, "code_sha256": ENGINE_X,
           "manifest_sha256": fam["manifest_sha256"], "recipe_sha256": recipe_sha}
    identity = {"code_sha256": ENGINE_X, "manifest_sha256": fam["manifest_sha256"], "training_identity": fam["training_identity"],
                "recipe": recipe, "recipe_sha256": recipe_sha}
    assets = {"environment": SYNTHETIC_ENVIRONMENT, "policy": {"name": "synthetic"},
              "guard": {"repo": "g", "revision": "r", "files": {}}, "environment_lock": {"sha256": sha256_bytes(lock)}}
    files = {"job.json": canonical(job), "identity.json": canonical(identity), "assets.json": canonical(assets),
             "edit.json": edit_bytes, nr.LOCK_NAME: lock}
    for name, data in files.items():
        (folder / name).write_bytes(data)
    marker = {"complete": True, "kind": "run-one", "job_sha256": sha256_bytes(files["job.json"]),
              "completed_utc": "2026-11-05T15:00:00+00:00", "files": {name: sha256_bytes(data) for name, data in files.items()},
              "identity": {k: identity[k] for k in ("code_sha256", "manifest_sha256", "training_identity", "recipe_sha256")}}
    data = canonical(marker)
    (folder / "COMPLETE.json").write_bytes(data)
    return {"path": str(folder), "complete_sha256": sha256_bytes(data), "arm": arm}


def test_an_r_unit_whose_edit_file_hashes_to_another_arm_refuses(tmp_path):
    """RV-2 (the re-verifier's R3): an R unit's edit.json must hash to the arm the inputs and its job.json name. On a
    synthetic sealed unit (self-consistent: its COMPLETE.json lists the edit file it holds): SEAL's R_d1 bytes under
    their own arm pass read_unit; the same unit holding SEAL's R_d2 file, or R_d1 with one row changed (its five
    provenance fields intact, so only the hash binding can refuse it), under R_d1's arm refuses."""
    r1 = (SEAL / "edits/R_d1.json").read_bytes()
    assert sha256_bytes(r1) == R_ARMS[1101]
    genuine = synthetic_r_unit(tmp_path / "genuine", r1, 1101)
    unit = nr.read_unit(genuine, "R", 1101, "olmo2-1b", ENGINE_X, "olmo2-1b R@1101", tmp_path)
    assert unit["complete_sha256"] == genuine["complete_sha256"] and unit["resumed_from_complete_sha256"] is None
    other_arm = synthetic_r_unit(tmp_path / "other-arm", (SEAL / "edits/R_d2.json").read_bytes(), 1101, arm=genuine["arm"])
    with pytest.raises(SystemExit, match="olmo2-1b R@1101: edit.json is missing or is not the arm's edit file"):
        nr.read_unit(other_arm, "R", 1101, "olmo2-1b", ENGINE_X, "olmo2-1b R@1101", tmp_path)
    doc = json.loads(r1)
    doc["remove"] = sorted(doc["remove"][1:] + [doc["remove"][0] + "0"])
    tampered = canonical(doc)
    assert nr.r_edit_matches(json.loads(tampered), "olmo2-1b", 1101) and sha256_bytes(tampered) != R_ARMS[1101]
    row = synthetic_r_unit(tmp_path / "row-changed", tampered, 1101, arm=genuine["arm"])
    with pytest.raises(SystemExit, match="olmo2-1b R@1101: edit.json is missing or is not the arm's edit file"):
        nr.read_unit(row, "R", 1101, "olmo2-1b", ENGINE_X, "olmo2-1b R@1101", tmp_path)


@needs_wave0a
def test_a_copied_unit_at_another_path_with_the_same_complete_json_refuses_as_a_duplicate(tmp_path):
    """RV-2 (C-D4b): the duplicate key is the COMPLETE.json SHA-256, not the path. Gate A's a0-1101 metadata files are
    copied to another folder (COMPLETE.json, job.json, identity.json, assets.json; no eval output) and listed with the
    same key as a0@1102 of the same family, and as a0@1101 of a second family: each second listing refuses as a
    duplicate before the copy is read."""
    copy = tmp_path / "a0-1101-copy"
    copy.mkdir()
    for name in ("COMPLETE.json", "job.json", "identity.json", "assets.json"):
        (copy / name).write_bytes((GATE_A / name).read_bytes())
    assert nr.sha256_file(copy / "COMPLETE.json") == A0_KEYS[1101] and copy.resolve() != GATE_A.resolve()
    fam = parity_family()
    fam["a0"]["1102"] = {"path": str(copy), "complete_sha256": A0_KEYS[1101]}
    with pytest.raises(SystemExit, match="olmo2-1b a0@1102: its COMPLETE.json SHA-256 is already read as olmo2-1b a0@1101"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}))
    second = parity_family()
    second["a0"]["1101"] = {"path": str(copy), "complete_sha256": A0_KEYS[1101]}
    with pytest.raises(SystemExit, match="olmo2-7b a0@1101: its COMPLETE.json SHA-256 is already read as olmo2-1b a0@1101"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family(), "olmo2-7b": second}, "two-families.json"))


def test_the_edit_provenance_check_refuses_a_rewrite_or_add_edit_and_a_wrong_kind():
    """RV-2 (the re-verifier's R2): each of r_edit_matches's five fields refuses on its own. SEAL's R_d1 passes for
    olmo2-7b at 1101; the same document with edit_kind "rewrite" or "add", with another kind, with another manifest,
    with selection.family "unit" or "H", or with another draw does not."""
    doc = json.loads((SEAL / "edits/R_d1.json").read_text())
    assert nr.r_edit_matches(doc, "olmo2-7b", 1101)
    for edit_kind in ("rewrite", "add", "", None):
        assert not nr.r_edit_matches({**doc, "edit_kind": edit_kind}, "olmo2-7b", 1101), edit_kind
    assert not nr.r_edit_matches({**doc, "kind": "safety-selection recipe"}, "olmo2-7b", 1101)
    assert not nr.r_edit_matches({**doc, "manifest_sha256": nr.FAMILIES["llama31-8b"]["manifest_sha256"]}, "olmo2-7b", 1101)
    selection = doc["provenance"]["selection"]
    for change in ({"family": "unit"}, {"family": "H"}, {"draw": 2}):
        changed = {**doc, "provenance": {**doc["provenance"], "selection": {**selection, **change}}}
        assert not nr.r_edit_matches(changed, "olmo2-7b", 1101), change


@needs_wave0a
def test_an_environment_difference_on_a0_1102_alone_is_attributed_to_it_against_the_a0_1101_reference(tmp_path, monkeypatch):
    """RV-2 (the re-verifier's R4): the family's reference environment is a0-1101's (the module doc; Gate B's rule). The
    a0@1102 unit is read as if its GPU name differed (the record read_unit returns is changed; the files are untouched):
    the trigger fires, the difference is recorded on a0@1102 alone, and every other unit, a0@1101 among them, differs
    in nothing. With a0@1102 as the reference the attribution would invert (five units differing, a0@1102 in nothing)."""
    real = nr.read_unit

    def read_unit(spec, role, seed, family, engine, where, base):
        unit = real(spec, role, seed, family, engine, where, base)
        if role == "a0" and seed == 1102:
            unit = {**unit, "fields": {**unit["fields"], "gpu": "another device"}}
        return unit
    monkeypatch.setattr(nr, "read_unit", read_unit)
    fam = nr.read(write_inputs(tmp_path, {"olmo2-1b": parity_family()}))["families"]["olmo2-1b"]
    assert fam["triggers"]["environment_differs"] == {"a0@1101": [], "a0@1102": ["gpu"], "a0@1103": [],
                                                      "R@1101": [], "R@1102": [], "R@1103": []}
    assert fam["triggers"]["environment"] and fam["triggers"]["fallback"] and fam["governing"] == "fallback"
    assert round(fam["sigma_F_pp"], 2) == 2.16


def test_hex64_accepts_sixty_four_lower_case_hex_digits_only(tmp_path):
    """RV-2 (the re-verifier's R5): keys, arms and engine ids are 64 lower-case hex digits (hashlib's and the engine's
    spelling). Upper or mixed case, other lengths, other characters and non-strings are refused; through the inputs
    file, an upper-case engine id refuses on the engine check itself, before any unit is read."""
    low = "0123456789abcdef" * 4
    assert nr.hex64(low) and nr.hex64(ENGINE_X) and nr.hex64(R_ARMS[1101])
    for bad in (low.upper(), low[:-1] + "F", low[:63], low + "0", low[:-1] + "g", "edit-" + low, low.encode(), None, 7, [low]):
        assert not nr.hex64(bad), bad
    assert all(nr.hex64(v) for f in nr.FAMILIES.values() for v in (f["training_identity"], f["manifest_sha256"], f["main_config_sha256"]))
    fam = parity_family()
    fam["engine"]["R"] = ENGINE_X.upper()
    with pytest.raises(SystemExit, match="engine must give the a0 and R code identities \\(64 hex each\\)"):
        nr.read(write_inputs(tmp_path, {"olmo2-1b": fam}))
