"""B11 under the lead's S1 rulings (addendum section 11 points 5, 6 and 8; section 13 point 3), on tiny synthetic
snapshots and hand-made matrices (nothing is downloaded).

Point 6: the base model (allenai/OLMo-2-0425-1B) is pinned in full from the lead's Hub metadata record
(tmp/gi-vi-stage1/olmo2-0425-1b-base-pins.json, SHA-256 9bc9a9e9...): the commit, all 12 files with their sizes and
git blob ids, both LFS SHA-256 values, the licence and the stored dtype (F32 only); the kit downloads with
revision = the commit (download_pin).
Point 5: the record carries B10's fifth key (transform_settings_sha256 -> provenance.settings_sha256).
Point 8 with 13.3: the V/V' diagnostic (vcheck), run by the Safe LoRA pod job before the projection."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import b11_fixtures as fx
import pytest
import torch
from safetensors.torch import load_file, save_file

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.stage1_s1 import safe_lora as sl

# The lead's record (addendum 11.6; 9bc9a9e999dd752df1519d07e7c7c5a9f0f542284a2f3ad0b821347fbd466577), by file name:
# (size, git blob id, LFS SHA-256 or None).
BASE_COMMIT = "a1847dff35000b4271fa70afc5db10fd29fedbdf"
BASE_FILES = {
    ".gitattributes": (1519, "a6344aac8c09253b3b630fb776ae94478aa0275b", None),
    "README.md": (12892, "f4f00dd2b735b5127e40f54196d8ded341102da5", None),
    "config.json": (623, "0e6dffcd9b40b734014ef9909d6bc7b62c4c1fe1", None),
    "generation_config.json": (121, "5b349a5ba3b23008b50aaed4b394b269a138e6f8", None),
    "merges.txt": (916646, "354558edcdbd64ca7abd407b8be3d5d09d39d781", None),
    "model-00001-of-00002.safetensors": (4983360992, "b9ffb9d713594e086304ee87465d8486fd2f7e77",
                                         "c52e4ac8bf4867e698d908f9e8c2b84aa891b91dff066d46bf2a7cf453ad77fb"),
    "model-00002-of-00002.safetensors": (956326560, "ba23e835a4281771786fd8623cc5988f545014f3",
                                         "5f80762572fe28aca49b01b98895d96ca529b9792fc10925a977a161ad768d30"),
    "model.safetensors.index.json": (14873, "64893bc51d60e692025d2d041ac1d28a22284e2c", None),
    "special_tokens_map.json": (125, "68a9a42af03ba45d68358595d49dc70b10159c12", None),
    "tokenizer.json": (7137177, "5fe172127988c3709a49d8d2ce20e11bb266cd57", None),
    "tokenizer_config.json": (4345, "f9e5ee94cf605b587aa8021f7e27e7d5381c07b7", None),
    "vocab.json": (1611056, "51135344eec01a62fc4deaca39c72ac08f5b9709", None),
}


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    return fx.build_tiny(tmp_path_factory.mktemp("tiny-rulings"))


@pytest.fixture(scope="module")
def rounded(tmp_path_factory):
    """A tiny pair whose post-training change is small against one bfloat16 rounding (V is mostly rounding), so the
    V' ranking differs: with these seeds the mapped set changes at K = 2, 6 and 7, and not at K = 5."""
    return fx.build_tiny(tmp_path_factory.mktemp("tiny-rounded"), delta_scale=1e-4)


def _real() -> dict:
    return json.loads(sl.SETTINGS_PATH.read_bytes())


def _refuses(doc: dict, match: str) -> None:
    with pytest.raises(sl.Refusal, match=match):
        sl.validate_settings(doc, sha256_bytes(canonical_json(doc)))


# ----- point 6: the full base pins ------------------------------------------------------------------------------


def test_the_base_is_pinned_in_full_as_the_leads_hub_record():
    base = sl.load_pinned_settings().unaligned
    assert base["revision"] == BASE_COMMIT and base["repo_id"] == "allenai/OLMo-2-0425-1B"
    assert {f["rfilename"]: (f["size"], f["git_blob_id"], f["lfs_sha256"]) for f in base["hub_files"]} == BASE_FILES
    assert [f["rfilename"] for f in base["hub_files"]] == sorted(BASE_FILES)
    assert base["files"] == [{"file": n, "bytes": BASE_FILES[n][0], "sha256": BASE_FILES[n][2]}
                             for n in sorted(BASE_FILES) if n.endswith(".safetensors")]
    assert base["total_bytes"] == sum(v[0] for n, v in BASE_FILES.items() if n.endswith(".safetensors"))
    assert (base["licence"], base["gated"], base["stored_dtype"], base["dtype"]) == (
        "Apache-2.0", False, {"F32": 1484916736}, "float32")
    sources = _real()["sources"]
    assert sources["base_pins"] == {"path": "tmp/gi-vi-stage1/olmo2-0425-1b-base-pins.json",
                                    "sha256": "9bc9a9e999dd752df1519d07e7c7c5a9f0f542284a2f3ad0b821347fbd466577"}


def test_the_kit_downloads_each_model_at_its_full_pinned_commit():
    settings = sl.load_pinned_settings()
    assert sl.download_pin(settings, "unaligned") == {"repo_id": "allenai/OLMo-2-0425-1B", "revision": BASE_COMMIT}
    assert sl.download_pin(settings, "aligned") == {"repo_id": "allenai/OLMo-2-0425-1B-Instruct",
                                                    "revision": "48d788eca847d4d7548f375ad03d3c9312f6139e"}
    with pytest.raises(sl.Refusal, match="no model role"):
        sl.download_pin(settings, "base")


def test_a_prefix_pin_gives_no_download(tiny):
    assert len(tiny.settings.unaligned["revision"]) == 8                  # the fixture keeps the prefix rule
    with pytest.raises(sl.Refusal, match="full commit"):
        sl.download_pin(tiny.settings, "unaligned")
    assert sl.download_pin(fx.settings_of(fx.full_pins_doc(tiny)), "unaligned")["revision"] == tiny.base.name


def test_a_full_pin_of_the_tiny_base_is_accepted_and_recorded(tiny):
    settings = fx.settings_of(fx.full_pins_doc(tiny))
    snap = sl.open_snapshot(tiny.base, settings.unaligned, "unaligned")
    assert snap.revision == tiny.base.name and snap.stored_dtype == fx.stored_counts(tiny.base)
    assert snap.identity()["stored_dtype"] == {"F32": sum(t.numel() for p in sorted(tiny.base.glob("*.safetensors"))
                                                          for t in load_file(str(p)).values())}
    source = sl.read_adapter(tiny.state_dir)
    result = sl.SafeLoRA(settings, tiny.aligned, tiny.base, seed=fx.SEED)(source.tensors, source=source)
    reference = fx.hook(tiny)(source.tensors, source=source)
    assert result.adapter_bytes == reference.adapter_bytes and result.mapped == reference.mapped
    assert result.record["models"]["unaligned"]["stored_dtype"] == snap.stored_dtype


def test_the_stored_dtype_is_counted_from_the_headers():
    assert sl.stored_dtype_counts([], "unaligned") == {}


def test_a_stored_dtype_that_differs_refuses(tiny, tmp_path):
    doc = copy.deepcopy(tiny.doc)
    doc["models"]["unaligned"]["stored_dtype"] = {"F32": doc["models"]["unaligned"]["stored_dtype"]["F32"] + 1}
    with pytest.raises(sl.Refusal, match="snapshot stores"):
        sl.open_snapshot(tiny.base, fx.settings_of(doc).unaligned, "unaligned")
    # one extra bfloat16 tensor in a shard (outside the adapted weights) changes the stored dtype counts
    mixed = tmp_path / "snapshots" / tiny.base.name
    mixed.mkdir(parents=True)
    for path in sorted(tiny.base.glob("*.safetensors")):
        tensors = load_file(str(path))
        if path == sorted(tiny.base.glob("*.safetensors"))[-1]:
            tensors["extra.weight"] = torch.zeros(3, 2, dtype=torch.bfloat16)
        save_file(tensors, str(mixed / path.name))
    assert sl.stored_dtype_counts(sorted(mixed.glob("*.safetensors")), "unaligned") == {
        "BF16": 6, "F32": doc["models"]["unaligned"]["stored_dtype"]["F32"] - 1}
    pins = fx.snapshot_pins(mixed)
    doc = copy.deepcopy(tiny.doc)
    doc["models"]["unaligned"].update(files=[{"sha256": p["sha256"]} for p in pins], total_bytes=sum(p["bytes"] for p in pins))
    with pytest.raises(sl.Refusal, match="snapshot stores"):
        sl.open_snapshot(mixed, fx.settings_of(doc).unaligned, "unaligned")


def _hub(doc: dict) -> list:
    return doc["models"]["unaligned"]["hub_files"]


@pytest.mark.parametrize("change, match", [
    (lambda d: d["models"]["unaligned"].update(revision="a1847dff"), "full 40-hex commit"),
    (lambda d: _hub(d)[5].update(size=_hub(d)[5]["size"] + 1), "not the file pins"),
    (lambda d: _hub(d)[5].update(lfs_sha256="0" * 64), "not the file pins"),
    (lambda d: _hub(d)[6].update(lfs_sha256=None), "has no LFS SHA-256"),
    (lambda d: _hub(d)[5].update(lfs_sha256="C52E"), "64 hex"),
    (lambda d: _hub(d)[0].update(git_blob_id="a6344aac"), "git blob id"),
    (lambda d: _hub(d)[0].update(url="x"), "is not"),
    (lambda d: _hub(d).pop(0), None),                                  # a file fewer is still a valid full pin
    (lambda d: _hub(d).reverse(), "name order"),
    (lambda d: _hub(d).append(dict(_hub(d)[-1])), "name order"),
    (lambda d: _hub(d)[2].update(rfilename="../config.json"), "names no repository file"),
    (lambda d: _hub(d)[2].update(size=0), "size"),
    (lambda d: d["models"]["unaligned"].update(hub_files=[]), "non-empty"),
    (lambda d: d["models"]["unaligned"]["files"][0].update(sha256="c52e4ac8bf48"), "not the file pins"),
    (lambda d: d["models"]["unaligned"].update(total_bytes=1), "total_bytes"),
    (lambda d: d["models"]["unaligned"].update(stored_dtype={"BF16": 1484916736}), "stored_dtype"),
    (lambda d: d["models"]["unaligned"].update(stored_dtype={"F32": 0}), "stored_dtype"),
    (lambda d: d["models"]["unaligned"].update(stored_dtype={"F32": True}), "stored_dtype"),
    (lambda d: d["models"]["unaligned"].update(stored_dtype={"F32": 1, "BF16": 1}), "stored_dtype"),
])
def test_a_changed_full_pin_refuses(change, match):
    doc = _real()
    change(doc)
    if match is None:
        sl.validate_settings(doc, sha256_bytes(canonical_json(doc)))
    else:
        _refuses(doc, match)


def test_the_record_names_b10s_fifth_key():
    assert sl.B10_RECORD_KEYS["transform_settings_sha256"] == "provenance.settings_sha256"
    assert len(sl.B10_RECORD_KEYS) == 5


# ----- point 8 with 13.3: the V/V' diagnostic ---------------------------------------------------------------------


def test_v_prime_rounds_the_unaligned_weight_once_to_bfloat16():
    base = torch.tensor([[1.0 + 2 ** -10, 1.0], [3.0, 1.0 - 2 ** -12]], dtype=torch.float32)
    aligned = torch.tensor([[1.0078125, 1.0], [3.0, 1.0]], dtype=torch.bfloat16)
    v = sl.alignment_matrix(aligned, base)
    v_prime = sl.alignment_matrix_prime(aligned, base)
    assert v.dtype == v_prime.dtype == torch.float32
    assert torch.equal(v, torch.tensor([[2 ** -7 - 2 ** -10, 0.0], [0.0, 2 ** -12]]))
    assert torch.equal(v_prime, torch.tensor([[2 ** -7, 0.0], [0.0, 0.0]]))  # bf16(1 + 2^-10) = 1 = bf16(1 - 2^-12)
    expected = ((2 ** -10) ** 2 + (2 ** -12) ** 2) ** 0.5 / ((2 ** -7 - 2 ** -10) ** 2 + (2 ** -12) ** 2) ** 0.5
    assert sl.relative_difference(v, v_prime) == pytest.approx(expected, rel=1e-12)
    bf16_base = base.to(torch.bfloat16)
    assert torch.equal(sl.alignment_matrix_prime(aligned, bf16_base), sl.alignment_matrix(aligned, bf16_base))


def test_the_relative_difference_is_the_frobenius_ratio():
    v = torch.tensor([[3.0, 0.0], [0.0, 4.0]])
    assert sl.relative_difference(v, torch.tensor([[3.0, 0.0], [0.0, 1.0]])) == 0.6
    assert sl.relative_difference(v, v) == 0.0
    with pytest.raises(sl.Refusal, match="V is zero"):
        sl.relative_difference(torch.zeros(2, 2), v)


def _analysis(order: list[str]) -> sl.Analysis:
    return sl.Analysis({m: None for m in order}, list(order))


def test_compare_selection_reports_the_two_sets_and_their_change():
    a, b = _analysis(["m1", "m2", "m3", "m4"]), _analysis(["m2", "m1", "m4", "m3"])
    same = sl.compare_selection(a, b, 2)
    assert (same["set_changes"], same["same_order"], same["only_v"], same["only_v_prime"]) == (False, False, [], [])
    assert same["mapped_v"] == same["mapped_v_prime"] == ["m1", "m2"] and same["k"] == 2
    changed = sl.compare_selection(a, b, 3)
    assert (changed["set_changes"], changed["only_v"], changed["only_v_prime"]) == (True, ["m3"], ["m4"])
    assert changed["mapped_v"] == ["m1", "m2", "m3"] and changed["mapped_v_prime"] == ["m1", "m2", "m4"]
    assert sl.compare_selection(a, a, 3)["same_order"] is True
    assert sl.compare_selection(a, b, 0)["set_changes"] is False and sl.compare_selection(a, b, 4)["set_changes"] is False


def _independent(t: fx.Tiny, k: int) -> dict:
    """The diagnostic recomputed from the snapshot files with plain torch (the transform's own rule for the sets)."""
    def weights(folder: Path) -> dict:
        out = {}
        for path in sorted(folder.glob("*.safetensors")):
            out.update(load_file(str(path)))
        return out
    aligned, base = weights(t.aligned), weights(t.base)
    rel, cos_v, cos_vp = {}, {}, {}
    for key in sorted(t.adapter):
        if ".lora_B." not in key:
            continue
        module = fx.module_of(key)
        w_a, w_b = aligned[f"{module}.weight"].to(torch.float32), base[f"{module}.weight"]
        v = w_a - w_b
        v_prime = w_a - w_b.to(torch.bfloat16).to(torch.float32)
        rel[module] = float(torch.linalg.norm((v - v_prime).double())) / float(torch.linalg.norm(v.double()))
        a = t.adapter[key.replace(".lora_B.", ".lora_A.")].double()
        b = t.adapter[key].double()
        for target, mat in ((cos_v, v), (cos_vp, v_prime)):
            m64 = mat.double()
            b_new = m64 @ (m64.T @ b) / float(torch.linalg.norm(m64))
            target[module] = float(torch.nn.functional.cosine_similarity((b_new @ a).flatten(), (b @ a).flatten(), dim=0))
    rank = lambda c: sorted(c, key=lambda m: (c[m], m))
    return {"rel": rel, "cos_v": cos_v, "cos_vp": cos_vp, "set_v": sorted(rank(cos_v)[:k]),
            "set_vp": sorted(rank(cos_vp)[:k]),
            "rank_v": {m: i + 1 for i, m in enumerate(rank(cos_v))},
            "rank_vp": {m: i + 1 for i, m in enumerate(rank(cos_vp))}}


@pytest.mark.parametrize("which, k, changes", [("tiny", 5, False), ("rounded", 6, True), ("rounded", 5, False),
                                               ("rounded", 2, True)])
def test_the_diagnostic_equals_an_independent_recomputation(tiny, rounded, which, k, changes):
    t = {"tiny": tiny, "rounded": rounded}[which]
    doc = copy.deepcopy(t.doc)
    doc["transform"]["points"]["default"]["k"] = k
    record = fx.hook(t, doc=doc, point=None).vcheck(t.adapter)
    ref = _independent(t, k)
    rows = {r["name"]: r for r in record["matrices"]}
    assert sorted(rows) == sorted(ref["rel"]) and len(rows) == 14
    for module, row in rows.items():
        assert row["relative_difference"] == pytest.approx(ref["rel"][module], rel=1e-6, abs=1e-12)
        assert row["cosine_v"] == pytest.approx(ref["cos_v"][module], abs=1e-9)
        assert row["cosine_v_prime"] == pytest.approx(ref["cos_vp"][module], abs=1e-9)
        # S1 FIX round 2 (VERIFY-SUITES v2 gap NB11-vprime-rank-from-v): each matrix's rank under V and under V'
        assert (row["rank_v"], row["rank_v_prime"]) == (ref["rank_v"][module], ref["rank_vp"][module]), module
    if which == "rounded":                                # the fixture whose V' ranking differs from V's
        assert ref["rank_v"] != ref["rank_vp"]
    selection = record["selection"]
    assert (selection["k"], selection["mapped_v"], selection["mapped_v_prime"]) == (k, ref["set_v"], ref["set_vp"])
    assert selection["set_changes"] is changes is (ref["set_v"] != ref["set_vp"])
    outcomes = t.doc["v_diagnostic"]["outcomes"]
    assert record["outcome"] == (outcomes["changes"] if changes else outcomes["same"])
    assert record["point"] == "default" and record["kind"] == sl.VCHECK_KIND and record["mode"] == "vcheck"


def test_the_v_side_is_the_transforms_own_analysis(rounded):
    hook = fx.hook(rounded, point=None)
    record, check = hook.vcheck(rounded.adapter), hook.check(rounded.adapter)
    by_name = {m["name"]: m for m in check["matrices"]}
    for row in record["matrices"]:
        assert row["cosine_v"] == by_name[row["name"]]["cosine"] and row["rank_v"] == by_name[row["name"]]["rank"]
        assert row["v_norm"] == by_name[row["name"]]["v_norm"]
        # ||V - V'|| = ||W_base - bf16(W_base)||: the builder's report-only rounding share, up to float32 rounding of V
        assert row["relative_difference"] == pytest.approx(by_name[row["name"]]["base_bf16_rounding_share"], rel=1e-3)
    assert record["selection"]["mapped_v"] == sorted(check["points"]["default"]["mapped"])
    assert {r["rank_v_prime"] for r in record["matrices"]} == set(range(1, 15))
    assert record["summary"]["n_matrices"] == 14
    assert record["summary"]["relative_difference"]["max"] == max(r["relative_difference"] for r in record["matrices"])
    assert record["selection"]["same_order"] is False                   # the V' ranking differs at K = 5


def test_the_diagnostic_point_and_texts_are_the_rulings():
    settings = sl.load_pinned_settings()
    diag = settings.doc["v_diagnostic"]
    assert (settings.v_point, settings.v_output, settings.points[settings.v_point]) == (
        "default", "safe_lora_vcheck.json", 39)
    assert diag["v_prime"].startswith("V'_i = float32(W_i aligned) - float32(bfloat16(W_i unaligned))")
    assert "section 11 point 8" in diag["rule"] and "row 5 stands as primary" in diag["rule"]
    assert "section 13 point 3" in diag["when"] and "before the projection" in diag["when"]
    assert "report-only point at the Safe LoRA seeds (block B)" in diag["outcomes"]["changes"]
    assert "the question is closed" in diag["outcomes"]["same"]


@pytest.mark.parametrize("change, match", [
    (lambda d: d.pop("v_diagnostic"), "no v_diagnostic"),
    (lambda d: d["v_diagnostic"].update(point="certify"), "reference point"),
    (lambda d: d["v_diagnostic"].update(output="safe_lora_check.json"), "apart from the outputs"),
    (lambda d: d["v_diagnostic"].update(output="vcheck.safetensors"), "apart from the outputs"),
    (lambda d: d["v_diagnostic"].update(v_prime=""), "no v_diagnostic"),
    (lambda d: d["v_diagnostic"]["outcomes"].pop("same"), "outcomes"),
])
def test_a_changed_diagnostic_section_refuses(change, match):
    doc = _real()
    change(doc)
    _refuses(doc, match)


def test_the_diagnostic_refuses_what_the_check_refuses(tiny):
    other = {k: v.clone() for k, v in tiny.adapter.items()}
    first = sorted(k for k in other if ".lora_B." in k)[0]
    other[first] = other[first] * 2
    with pytest.raises(sl.Refusal, match="accepted a0 e1 fingerprint"):
        fx.hook(tiny, point=None).vcheck(other)


@pytest.fixture()
def cli(tiny, tmp_path, monkeypatch):
    path, digest = fx.write_settings_file(tmp_path, tiny.doc)
    monkeypatch.setattr(sl, "SETTINGS_PATH", path)
    monkeypatch.setattr(sl, "SETTINGS_SHA256", digest)
    return tmp_path


def _args(tiny, command, out, *extra):
    return [command, "--adapter", str(tiny.state_dir), "--seed", fx.SEED, "--aligned", str(tiny.aligned),
            "--base", str(tiny.base), "--out", str(out), *extra]


def test_the_command_line_vcheck_writes_the_diagnostic_and_its_timing(tiny, cli, capsys):
    out = cli / "vcheck"
    assert sl.main(_args(tiny, "vcheck", out)) == 0
    assert sorted(p.name for p in out.iterdir()) == ["safe_lora_timing.json", "safe_lora_vcheck.json"]
    data = (out / "safe_lora_vcheck.json").read_bytes()
    source = sl.read_adapter(tiny.state_dir)
    assert data == canonical_json(fx.hook(tiny, point=None).vcheck(source.tensors, source=source))
    record = json.loads(data)
    assert record["input_adapter"]["state_json_sha256"] == source.state_json_sha256
    assert record["provenance"]["settings_sha256"] == tiny.settings.sha256
    assert "adapter_state_json" in record["provenance"]["inputs"]
    timing = json.loads((out / "safe_lora_timing.json").read_bytes())
    assert (timing["command"], timing["point"]) == ("vcheck", None)
    assert timing["outputs"] == {"safe_lora_vcheck.json": sha256_bytes(data)}
    assert json.loads(capsys.readouterr().out)["command"] == "vcheck"
    assert sl.main(_args(tiny, "vcheck", out)) == 2                     # never overwrites
    bad = _args(tiny, "vcheck", cli / "seed")
    bad[bad.index("--seed") + 1] = "1102"
    assert sl.main(bad) == 2 and not (cli / "seed").exists()
