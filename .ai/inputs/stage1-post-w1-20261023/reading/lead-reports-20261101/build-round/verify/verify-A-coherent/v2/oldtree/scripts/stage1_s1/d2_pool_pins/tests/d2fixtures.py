"""Shared helpers for the D-2 tests: the committed settings, synthetic REQ-8 records with hand-computed hashes, an
independent hand fill (a byte replacement on the W1 file, not fill_pins' code), a tmp copy of the W1 files that
load_base reads, a real REQ-8 run on a synthetic world (scripts/stage1/tests' fixtures) and a hand-filled copy of
representation_pass.py. Synthetic data only; nothing real is read."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import shutil
import sys
from pathlib import Path

from experiments.safety_selection.common import canonical_json
from scripts.stage1_s1.d2_pool_pins import fill_pins as fp

# Hand-computed SHA-256 values (FIPS 180-2 test vectors): sha256(b"abc") and sha256(b"").
SHA_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
SHA_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
W1_PINS_SHA256 = "1451ba5ec435ecaafebd7749f44b6729e45f2157a69a62c55f35e2bbdbae826b"
RP_SHA256 = "fb62bcaaaa35595a52de5a4217754cb390ffb4ba49e04dec6e515d7e3cebb8d9"


def committed_d2() -> dict:
    return json.loads(fp.SETTINGS_PATH.read_bytes())


def w1_pins_path() -> Path:
    return fp.w1_root() / committed_d2()["base"]["pins"]


def w1_pins_bytes() -> bytes:
    return w1_pins_path().read_bytes()


def record(plant_sha: str = SHA_ABC, decoy_sha: str = SHA_EMPTY, n_plant: int = 75, n_decoy: int = 37) -> dict:
    """A synthetic REQ-8 record with the fields build_plant.py:437-453 writes that D-2 reads (and one unread file)."""
    req8 = committed_d2()["req8"]
    return {"kind": "stage1 plant record", "version": 1,
            "plant_rows": {"ids": [f"add-plant-{j:03d}" for j in range(1, n_plant + 1)], "candidates": 120},
            "decoy": {"ids": [f"pku_one:{i:06d}:0" for i in range(n_decoy)], "pool_sha256": decoy_sha, "unit": "u3"},
            "pools": {"plant": {"sha256": plant_sha, "items": n_plant}, "decoy": {"sha256": decoy_sha, "items": n_decoy}},
            "full_files": {"plant.pool.json": plant_sha, "decoy.pool.json": decoy_sha, "plant_rows.json": "1" * 64},
            "provenance": {"script": req8["script"], "script_sha256": req8["script_sha256"],
                           "settings_sha256": req8["settings_sha256"],
                           "inputs": {"build_plant_extra": req8["extra_sha256"], "s_pool": "2" * 64}}}


def hand_fill(w1_bytes: bytes, plant_sha: str, decoy_sha: str) -> bytes:
    """The fill rule by hand on the W1 file's bytes: its two '"sha256": null' are, in file order, the decoy's and the
    plant's (the file is canonical JSON with sorted keys)."""
    assert w1_bytes.count(b'"sha256": null') == 2
    assert w1_bytes.index(b'"decoy"') < w1_bytes.index(b'"sha256": null') < w1_bytes.index(b'"plant"') \
        < w1_bytes.rindex(b'"sha256": null')
    out = w1_bytes.replace(b'"sha256": null', f'"sha256": "{decoy_sha}"'.encode(), 1)
    return out.replace(b'"sha256": null', f'"sha256": "{plant_sha}"'.encode(), 1)


def write(path: Path, data: bytes) -> tuple[Path, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


def spec(pair: tuple[Path, str]) -> str:
    return f"{pair[0]}:{pair[1]}"


def fake_root(tmp_path: Path) -> Path:
    """A copy of the files load_base reads (the manifest, representation_pass.py, the W1 pins), under a tmp root."""
    d2 = committed_d2()
    real = fp.w1_root()
    for rel in (d2["base"]["manifest"], d2["base"]["script"], d2["base"]["pins"]):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(real / rel, tmp_path / rel)
    return tmp_path


def flip(path: Path, needle: bytes, new: bytes, every: bool = False) -> None:
    data = path.read_bytes()
    assert data.count(needle) >= 1
    path.write_bytes(data.replace(needle, new) if every else data.replace(needle, new, 1))


def load_base(root: Path | None = None) -> fp.Base:
    d2 = committed_d2()
    root = fp.w1_root() if root is None else root
    return fp.load_base(d2, (root / d2["base"]["pins"], d2["base"]["pins_sha256"]), root)


# ----- a real REQ-8 run on a synthetic world (build_plant.py itself) ------------------------------------------------


def plant_world(root: Path):
    """test_build_plant.py's synthetic world (seed 31; 71 refusal and 105 DIRECT records, 128 anchors, a P of 8 units)."""
    import s1fixtures_b3b as fw

    rng = random.Random(31)
    banks = fw.default_banks(rng)
    shared = fw.sentence(rng)
    refusals = [fw.refusal_record(rng, swap=(i % 4 == 0)) for i in range(70)] + [fw.refusal_record(rng, prompt=shared)]
    anchors = [fw.sentence(rng) for _ in range(128)]
    directs = [fw.direct_record(rng, swap=(i % 5 == 0)) for i in range(100)] + [fw.direct_record(rng, prompt=shared)]
    directs += [fw.direct_record(rng, prompt=anchors[5].upper()),
                fw.direct_record(rng, prompt=fw.swap_last_word(anchors[9], rng))]
    directs += [fw.direct_record(rng, prompt=fw.swap_last_word(banks["hidden"][0]["prompt"], rng)),
                fw.direct_record(rng, prompt=fw.swap_last_word(banks["selector"][0]["prompt"], rng))]
    return fw.SWorld(root / "w", fw.split_files(refusals + directs), banks=banks, anchors=anchors,
                     corpus=fw.random_corpus())


def run_req8(root: Path) -> dict:
    """build_plant.build on the synthetic world, given the W1 settings' own SHA-256s as labels (as the lead's run of
    build_plant.py gives them): its record, plant pool and decoy pool, written to disk."""
    from scripts.stage1 import build_plant as bp

    import test_build_plant as tbp

    world = plant_world(root)
    s_pool, lists, _ = tbp.s_pool_outputs(world, root / "tmp" / "s-pool")
    s, x = tbp.settings_for(world)
    full, out = bp.build(prepared_root=world.prepared_root, config_path=world.config_path,
                         sources_root=world.sources_root, anchors_path=world.anchors_path, rec_path=world.recipe_path,
                         recipe_path=world.recipe_path, s_pool=s_pool, lists=lists, codec=world.sfx.fixture_codec(),
                         settings=s, extra=x, settings_sha256=bp.SETTINGS_SHA256, extra_sha256=bp.EXTRA_SHA256)
    folder = root / "req8"
    return {"record": write(folder / bp.RECORD, out[bp.RECORD]),
            "plant": write(folder / "tmp" / "plant.pool.json", full["plant.pool.json"]),
            "decoy": write(folder / "tmp" / "decoy.pool.json", full["decoy.pool.json"]),
            "record_doc": json.loads(out[bp.RECORD])}


# ----- a hand-filled copy of representation_pass.py -----------------------------------------------------------------


def hand_filled_copy(tmp_path: Path, filled_bytes: bytes):
    """The fill as the W1 rule describes it, done by hand in a tmp copy: representation_pass.py with its literal
    POOL_PINS_SHA256 replaced and settings/representation_pools.json replaced by filled_bytes; loaded by path (not in
    sys.modules). sys.path is restored after the module runs (it puts its own root first)."""
    real = fp.w1_root() / "scripts" / "stage1" / "representation_pass.py"
    code = real.read_bytes()
    needle = f'POOL_PINS_SHA256 = "{W1_PINS_SHA256}"'.encode()
    assert code.count(needle) == 1
    filled_sha = hashlib.sha256(filled_bytes).hexdigest()
    code = code.replace(needle, f'POOL_PINS_SHA256 = "{filled_sha}"'.encode())
    path = tmp_path / "scripts" / "stage1" / "representation_pass.py"
    write(path, code)
    write(path.parent / "settings" / "representation_pools.json", filled_bytes)
    saved = list(sys.path)
    try:
        spec_ = importlib.util.spec_from_file_location("hand_filled_representation_pass", path)
        module = importlib.util.module_from_spec(spec_)
        spec_.loader.exec_module(module)
    finally:
        sys.path[:] = saved
    return module


def without(summary_bytes: bytes, *paths: tuple) -> dict:
    doc = json.loads(summary_bytes)
    for path in paths:
        node = doc
        for key in path[:-1]:
            node = node[key]
        node.pop(path[-1])
    return doc


def canonical(doc) -> bytes:
    return canonical_json(copy.deepcopy(doc))
