"""D-2 (addendum section 19 points 1-2(a)): fill_pins on synthetic REQ-8 records with hand-computed hashes, and every
refusal (another field changed, a wrong hash, a wrong item count, a changed W1 pins byte, a changed representation_pass.py
byte, a REQ-8 record of the wrong kind, and the record's own consistency). Synthetic data only."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.stage1 import representation_pass as rp
from scripts.stage1 import s1common as s1
from scripts.stage1_s1.d2_pool_pins import fill_pins as fp

import d2fixtures as dx
from d2guard import guarded


@pytest.fixture(scope="module")
def base():
    """Guarded (d2guard): a load_base defect fails the tests that use base, never errors their setup."""
    return guarded("base", lambda: dx.load_base())


def rec_bytes(**kw) -> bytes:
    return canonical_json(dx.record(**kw))


# ----- the committed files ------------------------------------------------------------------------------------------


def test_the_hand_computed_hashes():
    assert hashlib.sha256(b"abc").hexdigest() == dx.SHA_ABC and hashlib.sha256(b"").hexdigest() == dx.SHA_EMPTY


def test_the_committed_settings_and_their_w1_pins():
    doc, digest = fp.load_d2()
    assert digest == sha256_file(fp.SETTINGS_PATH) == fp.SETTINGS_SHA256
    assert fp.SETTINGS_PATH.read_bytes() == canonical_json(doc)
    entries, _ = fp.manifest_entries(fp.w1_root() / doc["base"]["manifest"])
    b, r = doc["base"], doc["req8"]
    assert entries[b["script"]] == b["script_sha256"] == dx.RP_SHA256 == sha256_file(Path(rp.__file__))
    assert entries[b["pins"]] == b["pins_sha256"] == dx.W1_PINS_SHA256 == rp.POOL_PINS_SHA256
    assert entries[b["settings"]] == b["settings_sha256"] == rp.SETTINGS_SHA256
    from scripts.stage1 import build_plant as bp
    assert entries[r["script"]] == r["script_sha256"] == sha256_file(Path(bp.__file__))
    assert entries[r["settings"]] == r["settings_sha256"] == bp.SETTINGS_SHA256
    assert entries[r["extra"]] == r["extra_sha256"] == bp.EXTRA_SHA256
    assert (r["record_kind"], r["record_version"]) == ("stage1 plant record", 1) and bp.RECORD == "plant_record.json"
    assert r["pool_files"] == {"plant": "plant.pool.json", "decoy": "decoy.pool.json"}
    assert doc["filled_fields"] == ["pools.decoy.sha256", "pools.plant.sha256"]
    assert "section 19" in doc["reference"] and doc["label_entries"] == {}


def test_the_base_is_private_and_holds_the_w1_pins(base):
    assert base.module.__name__ == fp.MODULE_NAME and fp.MODULE_NAME not in sys.modules and base.module is not rp
    assert Path(base.module.__file__) == Path(rp.__file__) and base.script_sha256 == dx.RP_SHA256
    assert base.pins_bytes == dx.w1_pins_bytes() and base.pins_sha256 == dx.W1_PINS_SHA256
    assert {n: (e["sha256"], e["items"]) for n, e in base.pins_doc["pools"].items()} == {"plant": (None, 75), "decoy": (None, 37)}
    assert base.module.load_pool_pins.__defaults__ == (rp.POOL_PINS_PATH, rp.POOL_PINS_SHA256)


# ----- the fill, by hand ----------------------------------------------------------------------------------------------


def test_the_fill_on_a_synthetic_record_is_the_hand_fill(base):
    """plant = sha256("abc"), decoy = sha256(""): the filled file is the W1 file with its two nulls replaced (by bytes,
    decoy first in file order), and nothing else."""
    data, pools = fp.build_filled(base, rec_bytes(), dx.committed_d2())
    expected = dx.hand_fill(dx.w1_pins_bytes(), dx.SHA_ABC, dx.SHA_EMPTY)
    assert data == expected
    assert pools == {"plant": {"sha256": dx.SHA_ABC, "items": 75}, "decoy": {"sha256": dx.SHA_EMPTY, "items": 37}}
    doc = json.loads(data)
    assert doc["pools"]["plant"]["sha256"] == dx.SHA_ABC and doc["pools"]["decoy"]["sha256"] == dx.SHA_EMPTY
    assert len(data) == len(dx.w1_pins_bytes()) + 2 * (66 - 4)            # each null (4) becomes a quoted hex (66)
    w1 = json.loads(dx.w1_pins_bytes())
    for name in ("plant", "decoy"):
        w1["pools"][name]["sha256"] = doc["pools"][name]["sha256"]
    assert w1 == doc
    assert rp.pin_of({"name": "plant", "sha256": dx.SHA_ABC, "items": [0] * 75}, rp.check_pool_pins(doc)) == "pool pins"
    assert rp.pin_of({"name": "decoy", "sha256": dx.SHA_EMPTY, "items": [0] * 37}, rp.check_pool_pins(doc)) == "pool pins"


def test_the_fill_swapped_hashes_go_to_their_own_pools(base):
    data, _ = fp.build_filled(base, rec_bytes(plant_sha=dx.SHA_EMPTY, decoy_sha=dx.SHA_ABC), dx.committed_d2())
    assert data == dx.hand_fill(dx.w1_pins_bytes(), dx.SHA_EMPTY, dx.SHA_ABC)
    assert data != dx.hand_fill(dx.w1_pins_bytes(), dx.SHA_ABC, dx.SHA_EMPTY)


def test_differences_finds_every_kind_of_change():
    a = {"x": 1, "y": [1, 2], "z": {"k": None}}
    assert fp.differences(a, copy.deepcopy(a)) == []
    assert fp.differences(a, {**a, "x": True}) == [("x",)]                 # 1 == True in Python; the type differs
    assert fp.differences(a, {**a, "x": 1.0}) == [("x",)]
    assert fp.differences(a, {**a, "y": [1, 3]}) == [("y", 1)]
    assert fp.differences(a, {**a, "y": [1]}) == [("y",)]
    assert fp.differences(a, {**a, "z": {"k": "v"}}) == [("z", "k")]
    assert fp.differences(a, {**a, "w": 0}) == [("w",)]
    assert fp.differences(a, {"x": 1, "y": [1, 2]}) == [("z",)]


# ----- refusals: the filled file ------------------------------------------------------------------------------------


def filled_doc() -> dict:
    return json.loads(dx.hand_fill(dx.w1_pins_bytes(), dx.SHA_ABC, dx.SHA_EMPTY))


POOLS = {"plant": {"sha256": dx.SHA_ABC, "items": 75}, "decoy": {"sha256": dx.SHA_EMPTY, "items": 37}}


@pytest.mark.parametrize("change", [
    lambda d: d.update(fill="filled by D-2"),
    lambda d: d["pools"]["plant"].update(source="another source"),
    lambda d: d["pools"]["plant"].update(items=74),
    lambda d: d["pools"]["decoy"].update(items=36),
    lambda d: d["pools"].update(s3_safe={"sha256": "3" * 64, "items": 9, "source": "x"}),
    lambda d: d.update(version=2),
    lambda d: d.pop("rule"),
    lambda d: d["label_entries"].update({"s1.order": "4" * 64}),
])
def test_another_field_changed_refuses(base, change):
    doc = filled_doc()
    change(doc)
    with pytest.raises(s1.Refusal, match="not exactly in pools.decoy.sha256 and pools.plant.sha256"):
        fp.check_filled(base, canonical_json(doc), POOLS)


def test_a_filled_file_with_one_or_no_pin_filled_refuses(base):
    for doc in (json.loads(dx.w1_pins_bytes()), json.loads(dx.hand_fill(dx.w1_pins_bytes(), dx.SHA_ABC, dx.SHA_EMPTY))):
        if doc["pools"]["decoy"]["sha256"] is not None:
            doc["pools"]["decoy"]["sha256"] = None                                       # only the plant filled
        with pytest.raises(s1.Refusal, match="not exactly in"):
            fp.check_filled(base, canonical_json(doc), POOLS)


def test_a_wrong_hash_refuses(base):
    doc = filled_doc()
    doc["pools"]["plant"]["sha256"] = "5" * 64
    with pytest.raises(s1.Refusal, match="the filled pin of pool plant is 5555"):
        fp.check_filled(base, canonical_json(doc), POOLS)
    swapped = json.loads(dx.hand_fill(dx.w1_pins_bytes(), dx.SHA_EMPTY, dx.SHA_ABC))
    with pytest.raises(s1.Refusal, match="the filled pin of pool decoy"):
        fp.check_filled(base, canonical_json(swapped), POOLS)


def test_a_filled_file_in_another_byte_form_refuses(base):
    """The same document re-serialised (indent 4): the bytes are not those fill_pins writes."""
    data = (json.dumps(filled_doc(), indent=4, sort_keys=True) + "\n").encode()
    assert json.loads(data) == filled_doc()
    with pytest.raises(s1.Refusal, match="not the canonical JSON"):
        fp.check_filled(base, data, POOLS)
    assert fp.check_filled(base, dx.hand_fill(dx.w1_pins_bytes(), dx.SHA_ABC, dx.SHA_EMPTY), POOLS) == filled_doc()


def test_one_hash_for_both_pools_refuses(base):
    """representation_pass's own check_pool_pins (two pins may not name one SHA-256) runs on the filled document."""
    rec = rec_bytes(plant_sha=dx.SHA_ABC, decoy_sha=dx.SHA_ABC)
    with pytest.raises(s1.Refusal, match="two pool pins name one SHA-256"):
        fp.build_filled(base, rec, dx.committed_d2())


# ----- refusals: REQ-8's record --------------------------------------------------------------------------------------


def test_a_wrong_item_count_refuses(base):
    """A record whose plant pool has 74 or 76 items (and as many ids, so it is consistent in itself): the W1 pins say
    75 (and 37 for the decoy). A count that is too high refuses as one that is too low (fix round: d2-verify-code)."""
    for kw, match in (({"n_plant": 74}, "gives 74 items for pool plant, the W1 pins say 75"),
                      ({"n_decoy": 36}, "gives 36 items for pool decoy, the W1 pins say 37"),
                      ({"n_plant": 76}, "gives 76 items for pool plant, the W1 pins say 75"),
                      ({"n_decoy": 38}, "gives 38 items for pool decoy, the W1 pins say 37")):
        with pytest.raises(s1.Refusal, match=match):
            fp.build_filled(base, rec_bytes(**kw), dx.committed_d2())


@pytest.mark.parametrize("change,match", [
    (lambda r: r.update(kind="stage1 s-pool record"), "is not a version-1 'stage1 plant record'"),
    (lambda r: r.update(kind="stage1 text pool"), "is not a version-1 'stage1 plant record'"),
    (lambda r: r.update(version=2), "is not a version-1"),
    (lambda r: r.pop("kind"), "is not a version-1"),
    (lambda r: r.update(kind="stage1 plant rows"), "is not a version-1 'stage1 plant record'"),   # REQ-8's sibling file
    (lambda r: r.update(version=True), "is not a version-1"),                                    # True == 1 in Python
    (lambda r: r.update(version=1.0), "is not a version-1"),                                     # 1.0 == 1 in Python
    (lambda r: r.update(version="1"), "is not a version-1"),
])
def test_a_record_of_the_wrong_kind_refuses(base, change, match):
    rec = dx.record()
    change(rec)
    with pytest.raises(s1.Refusal, match=match):
        fp.check_record(canonical_json(rec), dx.committed_d2(), base.entries)
    with pytest.raises(s1.Refusal, match="is not a version-1"):
        fp.check_record(b"[1, 2]", dx.committed_d2(), base.entries)


@pytest.mark.parametrize("change,match", [
    (lambda r: r["provenance"].update(script_sha256="6" * 64), "not written by the W1 build_plant.py"),
    (lambda r: r["provenance"].update(settings_sha256="6" * 64), "not written by the W1 build_plant.json"),
    (lambda r: r["provenance"].update(script="scripts/stage1_s1/x/build_plant.py"), "names the script"),
    (lambda r: r["provenance"]["inputs"].update(build_plant_extra="6" * 64), "build_plant_extra.json"),
    (lambda r: r["provenance"].pop("inputs"), "has no provenance.inputs"),
    (lambda r: r.pop("provenance"), "has no provenance"),
    (lambda r: r["full_files"].update({"plant.pool.json": "7" * 64}), r"pools.plant.sha256 is not full_files\[plant"),
    (lambda r: r["full_files"].pop("decoy.pool.json"), "has no full_files.decoy.pool.json"),
    (lambda r: r["decoy"].update(pool_sha256="7" * 64), "decoy.pool_sha256 is not pools.decoy.sha256"),
    (lambda r: r["plant_rows"]["ids"].pop(), "pools.plant.items is not the number of its ids"),
    (lambda r: r["decoy"]["ids"].append("x"), "pools.decoy.items is not the number of its ids"),
    (lambda r: r["pools"].update(s3_safe={"sha256": "8" * 64, "items": 3}), "exactly the plant and decoy pools"),
    (lambda r: r["pools"].pop("decoy"), "exactly the plant and decoy pools"),
    (lambda r: r["pools"]["plant"].update(sha256=None), "pools.plant is not"),
    (lambda r: r["pools"]["plant"].update(sha256="A" * 64), "pools.plant is not"),
    (lambda r: r["pools"]["plant"].update(extra=1), "pools.plant is not"),
    (lambda r: r["pools"]["decoy"].update(items=True), "pools.decoy.items is not a positive count"),
    (lambda r: r["pools"]["decoy"].update(items=0), "pools.decoy.items is not a positive count"),
])
def test_a_record_that_is_not_req8s_or_not_consistent_refuses(base, change, match):
    rec = dx.record()
    change(rec)
    with pytest.raises(s1.Refusal, match=match):
        fp.check_record(canonical_json(rec), dx.committed_d2(), base.entries)


@pytest.mark.parametrize("name", ["plant", "decoy"])
def test_a_pool_sha256_with_a_trailing_newline_refuses(base, name):
    """s1.HEX64 is ^[0-9a-f]{64}$, and re.match lets $ match before a final newline. A record that is consistent in
    itself with '<hex>\\n' as a pool's SHA-256 (pools, full_files and decoy.pool_sha256) is refused: a pin is 64 hex
    digits and nothing else (fix round: d2-verify-fidelity finding 2)."""
    kw = {"plant_sha": dx.SHA_ABC + "\n"} if name == "plant" else {"decoy_sha": dx.SHA_EMPTY + "\n"}
    assert s1.HEX64.match(dx.SHA_ABC + "\n")                            # the W1 pattern alone accepts it
    with pytest.raises(s1.Refusal, match=f"pools.{name} is not"):
        fp.check_record(rec_bytes(**kw), dx.committed_d2(), base.entries)
    with pytest.raises(s1.Refusal, match=f"pools.{name} is not"):
        fp.build_filled(base, rec_bytes(**kw), dx.committed_d2())


def test_a_path_sha256_argument_with_a_trailing_newline_refuses():
    for value in (dx.SHA_ABC + "\n", dx.SHA_ABC + " ", dx.SHA_ABC.upper(), dx.SHA_ABC[:-1]):
        with pytest.raises(s1.Refusal, match="--w1-pins is PATH:SHA256"):
            fp.parse_hashed("x.json:" + value, "--w1-pins")
    assert fp.parse_hashed("a:b.json:" + dx.SHA_ABC, "--w1-pins") == (Path("a:b.json"), dx.SHA_ABC)


@pytest.mark.parametrize("rel,what", [("scripts/stage1/build_plant.py", "build_plant.py"),
                                      ("scripts/stage1/settings/build_plant.json", "build_plant.json"),
                                      ("scripts/stage1/settings/build_plant_extra.json", "build_plant_extra.json")])
def test_the_record_check_reads_the_manifest_entries(base, rel, what):
    entries = dict(base.entries)
    assert entries[rel]
    entries[rel] = "9" * 64
    with pytest.raises(s1.Refusal, match=f"{what}: the W1 manifest names 9999"):
        fp.check_record(rec_bytes(), dx.committed_d2(), entries)


# ----- refusals: the W1 files ----------------------------------------------------------------------------------------


def test_a_changed_w1_pins_byte_refuses(tmp_path):
    root = dx.fake_root(tmp_path)
    d2 = dx.committed_d2()
    pins = root / d2["base"]["pins"]
    dx.flip(pins, b'"items": 75', b'"items": 76')
    with pytest.raises(s1.Refusal, match="the W1 pins file hashes to"):
        fp.load_base(d2, (pins, d2["base"]["pins_sha256"]), root)
    with pytest.raises(s1.Refusal, match="the W1 pins are named by"):                # its own hash: not the pin
        fp.load_base(d2, (pins, sha256_file(pins)), root)
    with pytest.raises(s1.Refusal, match="the W1 pins file cannot be read"):
        fp.load_base(d2, (tmp_path / "absent.json", d2["base"]["pins_sha256"]), root)


def test_a_changed_representation_pass_byte_refuses(tmp_path):
    root = dx.fake_root(tmp_path)
    d2 = dx.committed_d2()
    dx.flip(root / d2["base"]["script"], b'RESERVED_POOL_NAMES = ("dev",)', b'RESERVED_POOL_NAMES = ("dex",)')
    with pytest.raises(s1.Refusal, match="representation_pass.py hashes to"):
        fp.load_base(d2, (root / d2["base"]["pins"], d2["base"]["pins_sha256"]), root)


def test_a_manifest_or_pin_disagreement_refuses(tmp_path):
    root = dx.fake_root(tmp_path)
    d2 = dx.committed_d2()
    pins = (root / d2["base"]["pins"], d2["base"]["pins_sha256"])
    manifest = root / d2["base"]["manifest"]
    for field, what in (("script_sha256", "representation_pass.py"), ("pins_sha256", "representation_pools.json"),
                        ("settings_sha256", "representation_pass.json")):
        other = copy.deepcopy(d2)
        other["base"][field] = "1" * 64
        with pytest.raises(s1.Refusal, match=f"{what}: the W1 manifest names"):
            fp.load_base(other, pins, root)
    dx.flip(manifest, d2["base"]["script_sha256"].encode(), b"0" * 64, every=True)
    with pytest.raises(s1.Refusal, match="representation_pass.py: the W1 manifest names 0000"):
        fp.load_base(d2, pins, root)
    manifest.write_bytes(b'{"kind": "other", "entries": []}')
    with pytest.raises(s1.Refusal, match="not the stage-1 W1 commitments manifest"):
        fp.load_base(d2, pins, root)
    manifest.unlink()
    with pytest.raises(s1.Refusal, match="the W1 manifest cannot be read"):
        fp.load_base(d2, pins, root)


def _consistent_copy(tmp_path, script_from: bytes, script_to: bytes):
    """A tmp root whose representation_pass.py carries one change and whose manifest and D-2 pin name the changed
    file (so only the module's own literal checks can refuse)."""
    root = dx.fake_root(tmp_path)
    d2 = copy.deepcopy(dx.committed_d2())
    script = root / d2["base"]["script"]
    dx.flip(script, script_from, script_to)
    other = sha256_file(script)
    dx.flip(root / d2["base"]["manifest"], d2["base"]["script_sha256"].encode(), other.encode(), every=True)
    d2["base"]["script_sha256"] = other
    return root, d2


@pytest.mark.parametrize("from_,to,match", [
    (b'POOL_PINS_SHA256 = "1451', b'POOL_PINS_SHA256 = "0451', "literal POOL_PINS_SHA256"),
    (b'SETTINGS_SHA256 = "a555', b'SETTINGS_SHA256 = "0555', "own settings pin"),
])
def test_the_modules_own_literals_are_checked(tmp_path, from_, to, match):
    root, d2 = _consistent_copy(tmp_path, from_, to)
    saved = list(sys.path)                      # the module, run from the tmp copy, puts its root on sys.path
    try:
        with pytest.raises(s1.Refusal, match=match):
            fp.load_base(d2, (root / d2["base"]["pins"], d2["base"]["pins_sha256"]), root)
    finally:
        sys.path[:] = saved


def test_the_module_runs_from_the_checked_bytes(monkeypatch):
    """representation_pass.py is read once: the bytes that pass the SHA-256 check are the bytes that run, so a file that
    changes between the check and the run is not what runs (fix round: d2-verify-code's V-exec-rereads-file)."""
    real = Path.read_bytes
    reads = []

    def spy(self):
        data = real(self)
        if self.name == "representation_pass.py":
            reads.append(self)
            if len(reads) > 1:
                data += b"\nD2_TAMPERED = True\n"
        return data
    monkeypatch.setattr(Path, "read_bytes", spy)
    base = dx.load_base()
    monkeypatch.undo()
    assert len(reads) == 1 and not hasattr(base.module, "D2_TAMPERED")
    assert base.script_sha256 == dx.RP_SHA256


def test_already_filled_or_non_canonical_w1_pins_refuse(tmp_path):
    """W1 pins that are already filled (or not in canonical form), even when the manifest and the pin name them."""
    for name, data in (("filled", dx.hand_fill(dx.w1_pins_bytes(), dx.SHA_ABC, dx.SHA_EMPTY)),
                       ("indented", (json.dumps(json.loads(dx.w1_pins_bytes()), indent=4, sort_keys=True) + "\n").encode())):
        root = dx.fake_root(tmp_path / name)
        d2 = copy.deepcopy(dx.committed_d2())
        pins = root / d2["base"]["pins"]
        pins.write_bytes(data)
        sha = sha256_file(pins)
        dx.flip(root / d2["base"]["manifest"], d2["base"]["pins_sha256"].encode(), sha.encode(), every=True)
        dx.flip(root / d2["base"]["script"], d2["base"]["pins_sha256"].encode(), sha.encode())
        script_sha = sha256_file(root / d2["base"]["script"])
        dx.flip(root / d2["base"]["manifest"], d2["base"]["script_sha256"].encode(), script_sha.encode(), every=True)
        d2["base"]["pins_sha256"], d2["base"]["script_sha256"] = sha, script_sha
        saved = list(sys.path)
        try:
            with pytest.raises(s1.Refusal, match="null pins" if name == "filled" else "canonical JSON form"):
                fp.load_base(d2, (pins, sha), root)
        finally:
            sys.path[:] = saved


# ----- main() ----------------------------------------------------------------------------------------------------------


def _main_inputs(tmp_path, **kw):
    rec = dx.write(tmp_path / "plant_record.json", rec_bytes(**kw))
    return ["--w1-pins", dx.spec((dx.w1_pins_path(), dx.W1_PINS_SHA256)), "--req8-record", dx.spec(rec),
            "--out", str(tmp_path / "filled" / "representation_pools.filled.json")], rec


def test_main_writes_the_filled_file_and_prints_hashes_only(tmp_path, capsys):
    argv, rec = _main_inputs(tmp_path)
    (tmp_path / "filled").mkdir()
    assert fp.main(argv) == 0
    out_file = tmp_path / "filled" / "representation_pools.filled.json"
    expected = dx.hand_fill(dx.w1_pins_bytes(), dx.SHA_ABC, dx.SHA_EMPTY)
    assert out_file.read_bytes() == expected
    out = capsys.readouterr().out
    assert f"D-2 filled pins {sha256_bytes(expected)}" in out and rec[1] in out and dx.W1_PINS_SHA256 in out
    assert f"plant: sha256 {dx.SHA_ABC}, items 75" in out and f"decoy: sha256 {dx.SHA_EMPTY}, items 37" in out
    assert [p.name for p in (tmp_path / "filled").iterdir()] == [out_file.name]
    # never over an existing file
    assert fp.main(argv) == 2 and "exists: the filled pins file is never overwritten" in capsys.readouterr().err
    assert out_file.read_bytes() == expected


@pytest.mark.parametrize("edit,match", [
    (lambda a, t: a.__setitem__(1, a[1][:-1] + "0"), "the W1 pins are named by"),
    (lambda a, t: a.__setitem__(1, str(t / "absent") + ":" + dx.W1_PINS_SHA256), "the W1 pins file cannot be read"),
    (lambda a, t: a.__setitem__(1, "no-hash"), "--w1-pins is PATH:SHA256"),
    (lambda a, t: a.__setitem__(3, a[3][:-64] + "0" * 64), "REQ-8's record hashes to"),
    (lambda a, t: a.__setitem__(3, a[3].upper()), "--req8-record is PATH:SHA256"),
    (lambda a, t: a.__setitem__(5, str(t / "no-folder" / "x.json")), "does not exist"),
])
def test_main_refuses_and_writes_nothing(tmp_path, capsys, edit, match):
    argv, _ = _main_inputs(tmp_path)
    (tmp_path / "filled").mkdir()
    edit(argv, tmp_path)
    assert fp.main(argv) == 2
    err = capsys.readouterr().err
    assert match in err and err.rstrip().endswith("(nothing written)")
    assert list((tmp_path / "filled").iterdir()) == [] and not (tmp_path / "no-folder").exists()


def test_main_refuses_a_bad_record_and_writes_nothing(tmp_path, capsys):
    argv, _ = _main_inputs(tmp_path, n_decoy=36)
    (tmp_path / "filled").mkdir()
    assert fp.main(argv) == 2 and "gives 36 items for pool decoy" in capsys.readouterr().err
    assert list((tmp_path / "filled").iterdir()) == []


def test_main_refuses_a_changed_settings_byte(tmp_path, capsys, monkeypatch):
    copy_path = tmp_path / "d2_pool_pins.json"
    copy_path.write_bytes(fp.SETTINGS_PATH.read_bytes().replace(b'"record_version": 1', b'"record_version": 2'))
    monkeypatch.setattr(fp, "SETTINGS_PATH", copy_path)
    argv, _ = _main_inputs(tmp_path)
    (tmp_path / "filled").mkdir()
    assert fp.main(argv) == 2
    assert "settings d2_pool_pins hash to" in capsys.readouterr().err and list((tmp_path / "filled").iterdir()) == []
    monkeypatch.setattr(fp, "SETTINGS_PATH", tmp_path / "absent.json")
    assert fp.main(argv) == 2 and "the D-2 settings cannot be read" in capsys.readouterr().err


def test_the_fill_never_reads_a_pool_file(tmp_path, monkeypatch):
    """Text-free: the only files fill_pins reads are its settings, the manifest, representation_pass.py, the W1 pins
    and REQ-8's record (Path.read_bytes is the only reader in the module)."""
    seen = []
    real = Path.read_bytes

    def spy(self):
        seen.append(self.name)
        return real(self)
    monkeypatch.setattr(Path, "read_bytes", spy)
    argv, _ = _main_inputs(tmp_path)
    (tmp_path / "filled").mkdir()
    assert fp.main(argv) == 0
    assert set(seen) <= {"d2_pool_pins.json", "MANIFEST.json", "representation_pass.py", "representation_pools.json",
                         "plant_record.json", "representation_pools.filled.json"}
    assert not any(name.endswith(".pool.json") for name in seen)
