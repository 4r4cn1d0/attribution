"""The committed 7-8B reference settings (make_refs_settings_78b.py and its files): they are the derivation of the pins;
each family's values are Part 2 section 3.2's and DES F2's (K = 78 of 224, 32 blocks, the scale points, the 1B prefix
text, one certification per reference seed); the unchanged 1B validators accept every file once its waiting fields are
filled (the wrapper's check, with placeholders, and a real fill on a copy); a fill reaches only the indexes whose files
it changes; the 3-seed fallback; the kit form; and the 1B files stay byte for byte. These tests check consistency, not
the pins' values, so a documented fill leaves them green."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

import refs_fixtures as rf

from experiments.safety_selection.common import sha256_bytes, sha256_file
from experiments.safety_selection.config import config_sha256, load_recipe, training_identity
from scripts.scale78b import make_refs_settings_78b as mk
from scripts.scale78b import refs_78b as rw
from scripts.stage1_s1 import eval_adapter as ea
from scripts.stage1_s1 import safe_lora as sl

REPO = mk.REPO
FILLED = {"unit": "tmp/fixture/unit", "complete_sha256": "c" * 64, "e1_fingerprint": "e" * 64, "q_fingerprint": "d" * 64}
# GXB R-35's table, written here independently of the maker: the a0 unit each seed's certification pins.
R35 = {"olmo2-7b": {"1101": "side_unit", "1102": "side_unit", "1103": "side_unit", "1104": "block_a_a0",
                    "1105": "block_b_a0", "1106": "block_b_a0", "1107": "block_b_a0"},
       "llama31-8b": {"1101": "side_unit", "1102": "side_unit", "1103": "block0_a0", "1104": "block_a_a0",
                      "1105": "block_b_a0", "1106": "block_b_a0", "1107": "block_b_a0"}}
# P1 section 2.1's seed-1101 fingerprint prefixes (R: research/experiments/2026-11-05-78b-preregistration-part1.md 2.1)
P1_1101 = {"olmo2-7b": {"q_fingerprint": "3c7344c178b47e5b", "e1_fingerprint": "9d5d5d8b2eb40262"},
           "llama31-8b": {"q_fingerprint": "ac05caca1bdfac5b", "e1_fingerprint": "ee44580dfa016b67"}}
EVENT_WORDS = {"side_unit": "reused side unit", "block0_a0": "N's a0-", "block_a_a0": "block A's a0",
               "block_b_a0": "block B's a0"}
HUB = {"aligned": {"dtype": "bfloat16", "files": [{"file": "model.safetensors", "bytes": 10, "sha256": "a" * 64}]},
       "unaligned": {"revision": "b" * 40, "dtype": "float32",
                     "files": [{"file": "model.safetensors", "bytes": 10, "sha256": "f" * 64}]}}


def rk():
    spec = importlib.util.spec_from_file_location("rules_78b_for_track_r", REPO / "runkit" / "stage1-78b" / "rules_78b.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(settings_dir: Path, name: str) -> dict:
    return json.loads((Path(settings_dir) / name).read_bytes())


def copy_settings(tmp_path: Path) -> Path:
    """A settings folder holding Track O's O-ext files (the maker reads them), for a derivation on a copy."""
    out = tmp_path / "settings"
    out.mkdir(parents=True)
    for family in mk.FAMILIES:
        for role in mk.OEXT_FILES:
            shutil.copy(mk.SETTINGS_DIR / mk.file_name(role, family), out)
    return out


def make(tmp_path: Path, pins: dict, settings_dir: Path | None = None) -> Path:
    settings_dir = settings_dir or copy_settings(tmp_path)
    path = tmp_path / "pins.json"
    path.write_bytes(mk.dumps(pins))
    code, _, err = rf.call(mk.main, ["--pins", str(path), "--settings-dir", str(settings_dir)])
    assert code == 0, err[-300:]
    return settings_dir


def check(settings_dir: Path, family: str, seed: int) -> tuple[int, dict | None, str]:
    path = Path(settings_dir) / mk.index_name(family, seed)
    code, out, err = rf.call(rw.main, ["check", "--family", family, "--seed", str(seed), "--index", str(path),
                                       "--index-sha256", sha256_file(path)])
    return code, (json.loads(out) if code == 0 else None), err


def expected_waits(pins: dict, family: str, seed: int) -> dict:
    """{role: sorted pins} from the pins alone, written independently of the maker (a null pin waits)."""
    fam = pins["families"][family]
    out = {"eval_adapter": [], "safe_lora": []}
    for s in (mk.UNTUNED_SEED, seed):
        u = fam["units"][str(s)]
        if u["unit"] is None or u["complete_sha256"] is None or u["e1_fingerprint"] is None:
            out["eval_adapter"].append(f"REF_UNIT_{s}")
            if s == seed:
                out["safe_lora"].append(f"REF_UNIT_{s}")
    m = fam["models"]
    if any(m[r][k] is None for r in ("aligned", "unaligned") for k in ("revision", "dtype", "files")):
        out["safe_lora"].append("HUB_READ")
    return {r: sorted(v) for r, v in out.items()}


def consistency(settings_dir: Path, pins_path: Path) -> None:
    """Every committed-state check, on any settings folder and its pins file (the committed one or a fill's copy)."""
    pins, _ = mk.load_pins(pins_path)
    code, _, err = rf.call(mk.main, ["--pins", str(pins_path), "--settings-dir", str(settings_dir), "--check"])
    assert code == 0, err[-300:]
    kit, configs, manifests = rk().KIT, rk().CONFIGS, rk().MANIFESTS
    one_b = mk.load_base("eval_adapter")
    seeds = mk.REFERENCE_SETS[pins["reference_set"]]["seeds"]
    names = {n.name for n in Path(settings_dir).glob("REFS-78B__*.json")}
    assert names == {mk.index_name(f, s) for f in mk.FAMILIES for s in seeds}
    for family in mk.FAMILIES:
        fam = pins["families"][family]
        main_rel, main_sha = configs[family]["main"]
        rec = load_recipe(REPO / main_rel)
        lora = rec["model"]["lora"]
        oext = load(settings_dir, mk.file_name("oext_eval", family))
        assert fam["main"]["config_sha256"] == main_sha and fam["manifest_sha256"] == manifests[family]
        assert fam["untuned"] == {"unit": kit[family]["a0_units"]["untuned"]["path"],
                                  "complete_sha256": kit[family]["a0_units"]["untuned"]["complete_sha256"], "seed": 1101}
        for s_, unit in fam["units"].items():                             # GXB R-35
            assert unit["source"] == R35[family][s_]
            if unit["source"] == "side_unit":                              # the side units are RK KIT's
                assert (unit["unit"], unit["complete_sha256"]) == (kit[family]["a0_units"][int(s_)]["path"],
                                                                   kit[family]["a0_units"][int(s_)]["complete_sha256"])
        for key, prefix in P1_1101[family].items():                         # GXB R-36
            assert fam["units"]["1101"][key] is None or fam["units"]["1101"][key].startswith(prefix)
        assert fam["models"]["aligned"]["repo_id"] == kit[family]["instruct_model"]["repo_id"]
        untuned = {k: v for k, v in fam["untuned"].items()}
        assert fam["models"]["aligned"]["revision"] == kit[family]["instruct_model"]["revision"]
        assert fam["models"]["unaligned"]["repo_id"] == kit[family]["base_model"]["repo_id"]
        assert fam["models"]["unaligned"]["gated"] == kit[family]["base_model"]["gated"]
        for seed in seeds:
            index = load(settings_dir, mk.index_name(family, seed))
            assert (index["family"], index["seed"], index["version"]) == (family, seed, rw.INDEX_VERSION)
            assert sorted(index["files"]) == sorted(mk.ROLES)
            assert all(sha256_file(Path(settings_dir) / e["file"]) == e["sha256"] for e in index["files"].values())
            assert index["manifest_sha256"] == fam["manifest_sha256"] and index["branch"] == oext["cap"]["branch"]
            assert index["other_manifests"] == {o: p["manifest_sha256"] for o, p in pins["families"].items() if o != family}
            got = {r: sorted(w["pin"] for w in index["waits"] if r in w["roles"]) for r in ("eval_adapter", "safe_lora")}
            assert got == expected_waits(pins, family, seed)
            e = load(settings_dir, mk.file_name("eval_adapter", family, seed))
            s = load(settings_dir, mk.file_name("safe_lora", family, seed))
            # B10 (DES F2; GXB O2)
            assert (e["kind"], e["name"], e["owner"], e["version"]) == (one_b["kind"], "eval_adapter", ea.OWNER, 1)
            assert e["recipe"] == {"path": main_rel, "file_sha256": sha256_file(REPO / main_rel),
                                   "config_sha256": main_sha, "training_identity": training_identity(rec)}
            assert e["recipe"]["training_identity"] == kit[family]["training_identity"]
            assert e["prepared"] == {"manifest_sha256": manifests[family], "bank": "dev"}
            assert sorted(e["reference_units"]) == ["1101", str(seed)]
            assert e["certification"]["seed"] == seed and e["untuned_unit"]["seed"] == 1101
            assert (e["untuned_unit"]["unit"], e["untuned_unit"]["complete_sha256"], e["untuned_unit"]["checkpoint"]) == \
                (untuned["unit"], untuned["complete_sha256"], "init")
            for s_ in ("1101", str(seed)):
                u = fam["units"][s_]
                assert e["reference_units"][s_]["unit"] == u["unit"]
                assert e["reference_units"][s_]["complete_sha256"] == u["complete_sha256"]
                assert e["reference_units"][s_]["fingerprint_prefixes"] == {"e1": u["e1_fingerprint"],
                                                                            "q": u["q_fingerprint"]}
            assert e["certification"]["expected_sampled_answers"] == 200 * rec["generation"]["harm_samples"]["count"] == 600
            assert e["adapter_scale"]["allowed"] == ([1.0, 0.9, 0.75, 0.5, 0.0] if pins["reference_set"] == "six_seed"
                                                     else [1.0, 0.75, 0.5, 0.0])               # RRV-1: P2 3.1-3.2
            assert (e["adapter_scale"]["planned"], e["adapter_scale"]["curve"]) == (
                ([0.9, 0.75, 0.5], [1.0, 0.9, 0.75, 0.5, 0.0]) if pins["reference_set"] == "six_seed"
                else ([0.75, 0.5], [1.0, 0.75, 0.5, 0.0]))
            for key in ("text_sha256", "separator", "apply_to", "guard_sees", "length_rule"):
                assert e["prefix"][key] == one_b["prefix"][key]                     # the 1B text, a user-turn prefix
            for key in ("evaluation", "checkpoint", "engine_x"):
                assert e[key] == one_b[key]
            assert {k: v for k, v in e["regeneration"].items() if k != "rule"} == \
                {k: v for k, v in one_b["regeneration"].items() if k != "rule"}
            assert {k: v for k, v in e["exit_codes"].items() if k != "3"} == \
                {k: v for k, v in one_b["exit_codes"].items() if k != "3"}
            assert e["labels_sha256"] == s["labels_sha256"] == mk.s1.labels_sha256()          # RV-2
            prose = ("seed", "expected_sampled_answers", "gate", "reference_rule")
            assert {k: v for k, v in e["certification"].items() if k not in prose} == \
                {k: v for k, v in one_b["certification"].items() if k not in prose}
            for doc in (e, s):                                              # RV-3, GXB R-38: no 1B parameter or stage
                text = json.dumps(doc)
                assert "K = 39" not in text and "Gate A" not in text
            assert "GXB R-34" in e["untuned_unit"]["role"]
            for wait in index["waits"]:                                     # GXB R-35, R-36: each wait's event
                if wait["pin"].startswith("REF_UNIT_"):
                    s_ = wait["pin"][len("REF_UNIT_"):]
                    assert EVENT_WORDS[R35[family][s_]] in wait["event"]
                    assert ("GXB R-36" in wait["event"]) == (s_ == "1101")
            entry = e["external_transforms"]["safe_lora"]
            assert (entry["module"], entry["module_sha256"]) == ("scripts/stage1_s1/safe_lora.py", rw.CODE[rw.SL])
            assert entry["settings"] == {"path": mk.label(Path(settings_dir) / mk.file_name("safe_lora", family, seed)),
                                         "sha256": index["files"]["safe_lora"]["sha256"]}
            assert entry["record_keys"] == sl.B10_RECORD_KEYS
            assert e["oext"]["settings"] == {"path": mk.label(Path(settings_dir) / mk.file_name("oext_eval", family)),
                                             "sha256": index["files"]["oext_eval"]["sha256"]}
            assert e["oext"]["branch"] == oext["cap"]["branch"] and e["overrefusal_bank"]["status"] == "oext_pinned"
            # B11 (P2 section 3.2; DES F2)
            a = s["adapter"]
            assert (a["blocks"], a["matrices"], a["rank"], a["lora_alpha"]) == (32, 224, lora["r"], lora["alpha"])
            assert a["modules"] == lora["target_modules"] and len(a["modules"]) == 7
            assert a["parameters"] == lora["expected_trainable_parameters"]
            pts = s["transform"]["points"]
            assert (pts["default"]["k"], pts["conditional"]["k"], pts["certify"]["k"]) == (78, 0, 0)       # R-37
            assert 78 == 39 * 224 // 112 and 78 / 224 == 39 / 112
            assert sorted(a["accepted"]) == [str(seed)]
            assert a["accepted"][str(seed)]["fingerprint"] == fam["units"][str(seed)]["e1_fingerprint"]
            assert s["models"]["aligned"]["repo_id"] == fam["models"]["aligned"]["repo_id"]
            assert s["models"]["unaligned"]["repo_id"] == fam["models"]["unaligned"]["repo_id"]
            assert (s["owner"], s["name"]) == (sl.OWNER, "safe_lora")
            code, report, err = check(settings_dir, family, seed)
            assert code == 0, err[-300:]
            for role in ("eval_adapter", "safe_lora"):
                assert report["settings"][role] == ("waits" if got[role] else "valid")
            assert report["settings"]["oext_eval"] == "valid" and report["certification_seed"] == seed


def test_the_committed_files_are_consistent():
    consistency(mk.SETTINGS_DIR, mk.PINS_PATH)


def test_the_lora_count_is_32_blocks_of_the_rank_64_sums():
    """P2 section 3.2 (I there): both families adapt 7 modules x 32 blocks; the configs' trainable counts equal 32 x
    the per-block rank-64 sums of the models' shapes (OLMo-2-7B: hidden 4096, MLP 11008, full KV; Llama-3.1-8B: hidden
    4096, MLP 14336, 8 KV heads of 128; I: the public model configs)."""
    def per_block(hidden, mlp, kv):
        r = 64
        return r * (2 * (hidden + hidden) + 2 * (hidden + kv) + 2 * (hidden + mlp) + (mlp + hidden))
    shapes = {"olmo2-7b": (4096, 11008, 4096), "llama31-8b": (4096, 14336, 1024)}
    for family, configs in rk().CONFIGS.items():
        lora = load_recipe(REPO / configs["main"][0])["model"]["lora"]
        assert lora["expected_trainable_parameters"] == 32 * per_block(*shapes[family])


def fill(pins: dict, family: str, seed: str | None = None, hub: bool = False) -> dict:
    out = copy.deepcopy(pins)
    distinct = {k: FILLED[k][:-4] + seed for k in ("complete_sha256", "e1_fingerprint", "q_fingerprint")} if seed else {}
    unit = out["families"][family]["units"].get(seed) if seed else None
    if seed == "1101":                                   # P1 section 2.1's prefixes, the rest synthetic (R-36)
        unit.update({k: P1_1101[family][k] + distinct[k][16:] for k in ("e1_fingerprint", "q_fingerprint")})
    elif unit is not None and unit["source"] == "side_unit":       # the side unit's path and marker pin are RK KIT's
        unit.update(e1_fingerprint=distinct["e1_fingerprint"], q_fingerprint=distinct["q_fingerprint"])
    elif seed is not None:
        out["families"][family]["units"][seed] = {**unit, **FILLED, **distinct, "unit": f"tmp/fixture/{family}/{seed}"}
    if hub:
        for role in ("aligned", "unaligned"):
            out["families"][family]["models"][role].update(copy.deepcopy(HUB[role]))
    return out


def test_a_filled_family_passes_the_1b_validators_and_the_check_without_waits(tmp_path):
    pins, _ = mk.load_pins()
    for s in ("1101", "1102"):
        pins = fill(pins, "olmo2-7b", s)
    pins = fill(pins, "olmo2-7b", hub=True)
    sdir = make(tmp_path, pins)
    consistency(sdir, tmp_path / "pins.json")
    code, report, err = check(sdir, "olmo2-7b", 1102)
    assert code == 0 and report["settings"] == {"eval_adapter": "valid", "oext_eval": "valid", "safe_lora": "valid"}
    assert report["waits"] == {"eval_adapter": [], "safe_lora": []}
    e = load(sdir, mk.file_name("eval_adapter", "olmo2-7b", 1102))
    e_path = sdir / mk.file_name("eval_adapter", "olmo2-7b", 1102)
    with rf.ox.patched([(ea, "OEXT_SETTINGS_PATH", e["oext"]["settings"]["path"]),
                        (ea, "SETTINGS_SHA256", sha256_file(e_path))]):
        ea.load_pinned_settings(e_path)
    s_path = sdir / mk.file_name("safe_lora", "olmo2-7b", 1102)
    assert sl.load_pinned_settings(s_path, sha256_file(s_path)).points["default"] == 78
    assert check(sdir, "olmo2-7b", 1103)[1]["waits"]["eval_adapter"] == ["REF_UNIT_1103"]


def rewrite(sdir: Path, family: str, seed: int, role: str, change) -> dict:
    """Change one derived file in place, then re-pin it where it is pinned (B10's Safe LoRA pin, the index)."""
    name = mk.file_name(role, family, seed)
    doc = load(sdir, name)
    change(doc)
    (sdir / name).write_bytes(mk.dumps(doc))
    index_name = mk.index_name(family, seed)
    index = load(sdir, index_name)
    index["files"][role]["sha256"] = sha256_file(sdir / name)
    if role == "safe_lora":
        ea_name = mk.file_name("eval_adapter", family, seed)
        e = load(sdir, ea_name)
        e["external_transforms"]["safe_lora"]["settings"]["sha256"] = index["files"][role]["sha256"]
        (sdir / ea_name).write_bytes(mk.dumps(e))
        index["files"]["eval_adapter"]["sha256"] = sha256_file(sdir / ea_name)
    (sdir / index_name).write_bytes(mk.dumps(index))
    return index


@pytest.mark.parametrize("role, change, needle", [
    ("safe_lora", lambda d: d["transform"]["points"]["default"].update(k=225), "outside 0..224"),
    ("eval_adapter", lambda d: d["adapter_scale"].update(planned=[1.0, 0.5]), "lambda = 1 is the certification mode"),
    ("eval_adapter", lambda d: d["certification"].update(seed=1103), "certification runs the certify mode"),
])
def test_a_waiting_file_with_another_fault_exits_2(tmp_path, role, change, needle):
    """The placeholders stand only for the waiting fields: any other fault of the file refuses (W2-3's rule)."""
    sdir = make(tmp_path, mk.load_pins()[0])
    assert check(sdir, "llama31-8b", 1104)[0] == 0
    rewrite(sdir, "llama31-8b", 1104, role, change)
    code, _, err = check(sdir, "llama31-8b", 1104)
    assert code == 2 and needle in err, err[-300:]


@pytest.mark.parametrize("pin", ["HUB_READ", "REF_UNIT_1101", "REF_UNIT_1104"])
def test_a_null_that_no_wait_names_exits_2(tmp_path, pin):
    sdir = make(tmp_path, mk.load_pins()[0])
    index_name = mk.index_name("llama31-8b", 1104)
    index = load(sdir, index_name)
    index["waits"] = [w for w in index["waits"] if w["pin"] != pin]
    (sdir / index_name).write_bytes(mk.dumps(index))
    assert check(sdir, "llama31-8b", 1104)[0] == 2


def test_a_stale_wait_refuses(tmp_path):
    pins = fill(mk.load_pins()[0], "olmo2-7b", "1102")
    sdir = make(tmp_path, pins)
    index_name = mk.index_name("olmo2-7b", 1102)
    index = load(sdir, index_name)
    index["waits"].append({"pin": "REF_UNIT_1102", "event": "x", "where": ["x"], "roles": ["eval_adapter"],
                           "fields": {"eval_adapter": [{"path": "reference_units.1102.complete_sha256",
                                                        "kind": "sha256"}]}})
    (sdir / index_name).write_bytes(mk.dumps(index))
    code, _, err = check(sdir, "olmo2-7b", 1102)
    assert code == 2 and "but it is filled" in err


CASCADE = {
    "seed 1105 of OLMo": (lambda p: fill(p, "olmo2-7b", "1105"), {("olmo2-7b", 1105)}),
    "seed 1101 of Llama": (lambda p: fill(p, "llama31-8b", "1101"), {("llama31-8b", s) for s in range(1102, 1108)}),
    "Hub read of OLMo": (lambda p: fill(p, "olmo2-7b", hub=True), {("olmo2-7b", s) for s in range(1102, 1108)}),
}


@pytest.mark.parametrize("name", sorted(CASCADE))
def test_a_fill_reaches_only_the_indexes_whose_files_it_changes(tmp_path, name):
    change, allowed = CASCADE[name]
    pins, sdir = mk.load_pins()[0], copy_settings(tmp_path)
    before, after = mk.derive_all(pins, sdir), mk.derive_all(change(pins), sdir)
    changed = {(f, s) for f in mk.FAMILIES for s in range(1102, 1108)
               if before[mk.index_name(f, s)] != after[mk.index_name(f, s)]}
    assert changed == allowed
    if name == "seed 1101 of Llama":                    # 1101 is in every B10 file of the family, in no B11 file
        assert all(before[mk.file_name("safe_lora", "llama31-8b", s)] == after[mk.file_name("safe_lora", "llama31-8b", s)]
                   for s in range(1102, 1108))


def test_an_oext_fill_reaches_every_index_of_its_family_only(tmp_path):
    """Track O's branch fill changes oext_eval__F: every B10 file of F pins it, so every index of F changes."""
    pins, sdir = mk.load_pins()[0], copy_settings(tmp_path)
    before = mk.derive_all(pins, sdir)
    doc = load(sdir, mk.file_name("oext_eval", "llama31-8b"))
    doc["requirement"] += " (a fixture change)"
    (sdir / mk.file_name("oext_eval", "llama31-8b")).write_bytes(mk.dumps(doc))
    after = mk.derive_all(pins, sdir)
    changed = {(f, s) for f in mk.FAMILIES for s in range(1102, 1108)
               if before[mk.index_name(f, s)] != after[mk.index_name(f, s)]}
    assert changed == {("llama31-8b", s) for s in range(1102, 1108)}


def test_the_three_seed_fallback(tmp_path):
    pins = copy.deepcopy(mk.load_pins()[0])
    pins["reference_set"] = "three_seed"
    sdir = make(tmp_path, pins)
    consistency(sdir, tmp_path / "pins.json")
    assert {p.name for p in sdir.glob("eval_adapter__*.json")} == {
        mk.file_name("eval_adapter", f, s) for f in mk.FAMILIES for s in (1102, 1103, 1104)}


@pytest.mark.parametrize("change, needle", [
    (lambda p: p["families"]["olmo2-7b"]["main"].update(config_sha256="1" * 64), "hashes to"),
    (lambda p: p["families"]["olmo2-7b"]["units"].pop("1107"), "must name exactly the seeds"),
    (lambda p: p["families"]["olmo2-7b"]["untuned"].update(seed=1102), "untuned must be"),
    (lambda p: p["families"]["llama31-8b"]["units"]["1103"].update(e1_fingerprint="xyz"), "must be 64 lowercase hex"),
    (lambda p: p["families"]["llama31-8b"]["units"]["1103"].update(source="side_unit"), "GXB R-35 names 'block0_a0'"),
    (lambda p: p["families"]["olmo2-7b"]["units"]["1104"].pop("source"), "must be {complete_sha256"),
    (lambda p: p["families"]["olmo2-7b"]["units"]["1101"].update(e1_fingerprint="f" * 64),
     "e1_fingerprint does not start with P1 section 2.1's prefix"),
    (lambda p: p["families"]["llama31-8b"]["units"]["1101"].update(q_fingerprint="ee44580dfa016b67" + "0" * 48),
     "q_fingerprint does not start with P1 section 2.1's prefix"),
    (lambda p: p.update(reference_set="nine_seed"), "reference_set must be one of"),
    (lambda p: p["families"]["llama31-8b"].update(blocks=31), "do not keep 1B's share"),
])
def test_the_maker_refuses_bad_pins(tmp_path, change, needle):
    pins = copy.deepcopy(mk.load_pins()[0])
    change(pins)
    path = tmp_path / "pins.json"
    path.write_bytes(mk.dumps(pins))
    code, _, err = rf.call(mk.main, ["--pins", str(path), "--settings-dir", str(copy_settings(tmp_path))])
    assert code == 2 and needle in err, err[-300:]
    assert not list((tmp_path / "settings").glob("REFS-78B__*"))


def test_the_maker_refuses_a_changed_1b_file(monkeypatch, tmp_path):
    monkeypatch.setitem(mk.BASE, "safe_lora", (mk.BASE["safe_lora"][0], "0" * 64))
    code, _, err = rf.call(mk.main, ["--settings-dir", str(copy_settings(tmp_path))])
    assert code == 2 and "the 1B files stay byte for byte" in err


def test_the_kit_form(tmp_path):
    code, out, err = rf.call(mk.main, ["--refs-78b", "llama31-8b", "1105"])
    assert code == 0, err[-300:]
    form = json.loads(out)
    assert set(form) == {"files", "inputs"} and rk().oext_form_problem(form) is None
    files = form["files"]
    assert files["scripts/scale78b/refs_78b.py"] == sha256_file(mk.HERE / "refs_78b.py")
    assert files["scripts/stage1_s1/eval_adapter.py"] == rw.CODE[rw.EA] == sha256_file(REPO / "scripts/stage1_s1/eval_adapter.py")
    index = load(mk.SETTINGS_DIR, mk.index_name("llama31-8b", 1105))
    assert files["scripts/scale78b/settings/" + mk.index_name("llama31-8b", 1105)] == \
        sha256_file(mk.SETTINGS_DIR / mk.index_name("llama31-8b", 1105))
    for entry in index["files"].values():
        assert files["scripts/scale78b/settings/" + entry["file"]] == entry["sha256"]
    assert not any("1104" in k or "olmo2-7b" in k for k in files)
    assert rf.call(mk.main, ["--refs-78b", "llama31-8b", "1101"])[0] == 2


def test_the_kit_form_names_a_pinned_w1_18_record():
    files = mk.derive_all(mk.load_pins()[0])
    name = mk.index_name("olmo2-7b", 1102)
    index = json.loads(files[name])
    index["w1_18_record_sha256"] = "9" * 64
    files[name] = mk.dumps(index)
    rel = ".ai/inputs/stage1-post-w1-20261023/78b/w1-18/overrefusal_checks__olmo2-7b.json"
    form = mk.form("olmo2-7b", 1102, files, rw.code_pins(), mk.SETTINGS_DIR, rel)
    assert form["files"][rel] == "9" * 64 and rk().oext_form_problem(form) is None
    with pytest.raises(mk.s1.Refusal, match="R-21 path is needed"):
        mk.form("olmo2-7b", 1102, files, rw.code_pins(), mk.SETTINGS_DIR, None)


def test_the_1b_files_are_unchanged():
    """The 1B scripts and settings this layer runs or derives from are byte for byte (the wrapper's CODE, the maker's
    BASE), and git sees no change under scripts/stage1 and scripts/stage1_s1 (where the checkout has git)."""
    for name, digest in rw.CODE.items():
        assert sha256_file(REPO / (name.replace(".", "/") + ".py")) == digest
    for rel, digest in mk.BASE.values():
        assert sha256_file(REPO / rel) == digest
    if not (REPO / ".git").exists():
        pytest.skip("not a git checkout (a mutation copy): the hash checks above stand")
    done = subprocess.run(["git", "--no-optional-locks", "-C", str(REPO), "diff", "--stat", "--", "scripts/stage1",
                           "scripts/stage1_s1"], capture_output=True, text=True)
    assert done.returncode == 0 and done.stdout == ""


def test_the_maker_refuses_an_oext_file_off_its_w1_18_binding(tmp_path):
    sdir = copy_settings(tmp_path)
    name = mk.file_name("limits_overrefusal_checks", "olmo2-7b")
    (sdir / name).write_bytes((sdir / name).read_bytes() + b" ")
    code, _, err = rf.call(mk.main, ["--settings-dir", str(sdir)])
    assert code == 2 and "does not bind its W1-18 settings file" in err
    (sdir / name).unlink()
    code, _, err = rf.call(mk.main, ["--settings-dir", str(sdir)])
    assert code == 2 and "cannot be read" in err


def test_the_three_seed_fallback_in_place_removes_the_other_seeds_files(tmp_path):
    """RV-5: the documented fallback (one pins edit, one maker run) in the folder itself leaves no file for seeds
    1105-1107, and --check then reports the folder equal; a stale file left by hand makes --check fail."""
    sdir = make(tmp_path, mk.load_pins()[0])                           # the six-seed state in a folder
    assert (sdir / mk.index_name("olmo2-7b", 1105)).is_file()
    pins = copy.deepcopy(mk.load_pins()[0])
    pins["reference_set"] = "three_seed"
    path = tmp_path / "pins.json"
    path.write_bytes(mk.dumps(pins))
    code, out, err = rf.call(mk.main, ["--pins", str(path), "--settings-dir", str(sdir)])
    assert code == 0, err[-300:]
    assert not [p.name for p in sdir.iterdir() if any(f"__{s}." in p.name for s in (1105, 1106, 1107))]
    assert out.count("removed  ") == 18
    consistency(sdir, path)
    (sdir / mk.file_name("safe_lora", "olmo2-7b", 1106)).write_bytes(b"{}")
    code, _, err = rf.call(mk.main, ["--pins", str(path), "--settings-dir", str(sdir), "--check"])
    assert code == 1 and "safe_lora__olmo2-7b__1106.json" in err
    assert (sdir / mk.file_name("oext_eval", "olmo2-7b")).is_file()           # Track O's files are never removed


def test_a_wait_field_absent_from_its_file_exits_2(tmp_path):
    """RV-4: an index that lists a waiting field the file does not hold refuses with exit 2 (no traceback)."""
    sdir = make(tmp_path, mk.load_pins()[0])
    for path_ in ("reference_units.1102.nonesuch", "nonesuch.e1"):
        index_name = mk.index_name("olmo2-7b", 1102)
        index = load(sdir, index_name)
        next(w for w in index["waits"] if "eval_adapter" in w["fields"])["fields"]["eval_adapter"].append({"path": path_, "kind": "sha256"})
        (sdir / index_name).write_bytes(mk.dumps(index))
        code, out, err = check(sdir, "olmo2-7b", 1102)
        assert code == 2 and "which the file does not hold" in err and "Traceback" not in err
        make(tmp_path, mk.load_pins()[0], sdir)


def test_the_fallback_allows_no_scale_point_it_does_not_plan(tmp_path):
    """RRV-1 (GXB R-40 withdrawn; P2 sections 3.1-3.2): under the 3-seed fallback B10 refuses lambda 0.9, which only
    the 6-seed set plans; 0.75 and 0.5 still plan."""
    pins = copy.deepcopy(mk.load_pins()[0])
    pins["reference_set"] = "three_seed"
    sdir = make(tmp_path, pins)
    doc = load(sdir, mk.file_name("eval_adapter", "olmo2-7b", 1102))
    assert 0.9 not in doc["adapter_scale"]["allowed"]
    placeholder = copy.deepcopy(doc)
    placeholder["overrefusal_bank"]["status"] = "dev100_recipe_cap"   # the pending O-ext branch admits certify only
    for s_ in ("1101", "1102"):
        placeholder["reference_units"][s_].update(unit="x", complete_sha256="0" * 64,
                                                  fingerprint_prefixes={"e1": "0" * 64, "q": None})
    with rf.ox.patched([(ea, "OEXT_SETTINGS_PATH", doc["oext"]["settings"]["path"])]):
        settings = ea.settings_from_doc(placeholder)
        for lam in (0.75, 0.5):
            assert ea.make_plan(settings, "scale", adapter_scale=lam).mode == "scale"
        with pytest.raises(ea.Refusal):
            ea.make_plan(settings, "scale", adapter_scale=0.9)
