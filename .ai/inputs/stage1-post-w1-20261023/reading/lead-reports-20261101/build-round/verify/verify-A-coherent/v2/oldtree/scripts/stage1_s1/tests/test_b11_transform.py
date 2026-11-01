"""B11 end to end on tiny synthetic snapshots (REF R.1.4 tests 3-8): K = 0 gives the source adapter byte for byte;
K = all replaces every lora_B and no lora_A; a shuffled tensor order and a scaled lora_B change nothing they should
not; two runs give identical bytes; ties follow the name order; the record (the $0 check) is complete; every input
check refuses; the hook's output loads into the engine's LoRA parameters; the command line writes only into a new
folder."""

from __future__ import annotations

import copy
import dataclasses
import json
import math
import shutil

import b11_fixtures as fx
import pytest
import torch
from safetensors.torch import load as safetensors_load
from safetensors.torch import save_file

from experiments.safety_selection import engine as en
from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.stage1_s1 import safe_lora as sl


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    return fx.build_tiny(tmp_path_factory.mktemp("tiny"))


def _doc(tiny, **points):
    doc = copy.deepcopy(tiny.doc)
    for point, k in points.items():
        doc["transform"]["points"][point]["k"] = k
    return doc


def _bytes(t: torch.Tensor) -> bytes:
    return t.contiguous().numpy().tobytes()


# ----- the transform ------------------------------------------------------------------------------------------


def test_k_zero_returns_the_source_adapter_byte_for_byte(tiny):
    source = sl.read_adapter(tiny.state_dir)
    result = fx.hook(tiny, doc=_doc(tiny, default=0))(source.tensors, source=source)
    assert result.mapped == [] and result.fingerprint == tiny.fingerprint
    assert result.adapter_bytes == tiny.adapter_file.read_bytes()
    assert result.record["output"]["identical_to_source_bytes"] is True
    assert result.record["points"]["default"]["kth_cosine"] is None


def test_k_all_replaces_every_lora_b_and_no_lora_a(tiny):
    source = sl.read_adapter(tiny.state_dir)
    result = fx.hook(tiny, doc=_doc(tiny, default=14))(source.tensors, source=source)
    assert result.record["output"]["identical_to_source_bytes"] is False
    assert len(result.mapped) == 14 and sorted(result.mapped) == sorted({fx.module_of(k) for k in tiny.adapter})
    for name, tensor in result.adapter.items():
        if ".lora_A." in name:
            assert _bytes(tensor) == _bytes(tiny.adapter[name])
        else:
            assert not torch.equal(tensor, tiny.adapter[name])
        assert tensor.dtype == torch.float32 and tuple(tensor.shape) == tuple(tiny.adapter[name].shape)
    assert result.record["points"]["default"]["next_cosine"] is None


def test_the_mapped_lora_b_is_v_times_v_transpose_b_over_the_v_norm_and_the_rest_is_kept(tiny):
    """An independent recomputation from the snapshot files (float64, the formed C)."""
    result = fx.hook(tiny)(tiny.adapter)
    aligned = sl.open_snapshot(tiny.aligned, tiny.settings.aligned, "aligned")
    base = sl.open_snapshot(tiny.base, tiny.settings.unaligned, "unaligned")
    assert len(result.mapped) == 5
    for module in sorted({fx.module_of(k) for k in tiny.adapter}):
        key_b, key_a = sl._b(module), sl._a(module)
        assert _bytes(result.adapter[key_a]) == _bytes(tiny.adapter[key_a])
        if module not in result.mapped:
            assert _bytes(result.adapter[key_b]) == _bytes(tiny.adapter[key_b])
            continue
        v = (aligned.weight(module).double() - base.weight(module).double())
        c = (v @ v.T) / torch.linalg.vector_norm(v)
        expected = (c @ tiny.adapter[key_b].double()).float()
        assert torch.allclose(result.adapter[key_b], expected, rtol=1e-5, atol=1e-9)


def test_the_mapped_set_is_the_k_lowest_cosines_and_the_record_agrees(tiny):
    result = fx.hook(tiny)(tiny.adapter)
    record = result.record
    cosines = {m["name"]: m["cosine"] for m in record["matrices"]}
    order = sorted(cosines, key=lambda m: (cosines[m], m))
    assert record["ranking"] == order and result.mapped == order[:5]
    assert record["output"]["replaced_lora_b"] == order[:5] and record["output"]["k"] == 5
    point = record["points"]["default"]
    assert point["mapped"] == order[:5] and point["kth_cosine"] == cosines[order[4]]
    assert point["next_cosine"] == cosines[order[5]] and point["boundary_ties"] == 0
    assert sum(point["module_mix"].values()) == 5 and sum(point["block_mix"].values()) == 5
    assert set(point["module_mix"]) == set(fx.TARGETS) and set(point["block_mix"]) == {"0", "1"}
    for m in record["matrices"]:
        assert m["rank"] == order.index(m["name"]) + 1
        assert m["mapped"] == {"default": m["name"] in order[:5]}
    assert record["output"]["fingerprint"] == result.fingerprint == sl.adapter_fingerprint(result.adapter)
    assert record["output"]["adapter_sha256"] == sha256_bytes(result.adapter_bytes)


def test_a_shuffled_tensor_order_gives_the_same_bytes_and_record(tiny):
    forward = fx.hook(tiny)(tiny.adapter)
    shuffled = {k: tiny.adapter[k] for k in reversed(list(tiny.adapter))}
    assert list(shuffled) != list(tiny.adapter)
    backward = fx.hook(tiny)(shuffled)
    assert backward.adapter_bytes == forward.adapter_bytes
    assert canonical_json(backward.record) == canonical_json(forward.record)


def test_scaling_every_lora_b_leaves_every_cosine_and_the_mapped_set_unchanged(tiny):
    aligned = sl.open_snapshot(tiny.aligned, tiny.settings.aligned, "aligned")
    base = sl.open_snapshot(tiny.base, tiny.settings.unaligned, "unaligned")
    one = sl.analyse(tiny.adapter, tiny.settings, aligned, base)
    for c, rel in ((4.0, 0.0), (3.0, 1e-6)):          # 4 B is exact in float32; 3 B rounds once
        scaled = sl.analyse({k: (c * t if ".lora_B." in k else t) for k, t in tiny.adapter.items()},
                            tiny.settings, aligned, base)
        for module, result in one.results.items():
            assert scaled.results[module].cosine == pytest.approx(result.cosine, rel=rel, abs=0.0)
            assert scaled.results[module].rho == pytest.approx(result.rho, rel=rel, abs=0.0)
        assert scaled.order == one.order and scaled.mapped(5) == one.mapped(5)


def test_two_runs_give_identical_bytes(tiny):
    first, second = fx.hook(tiny)(tiny.adapter), fx.hook(tiny)(tiny.adapter)
    assert first.adapter_bytes == second.adapter_bytes
    assert canonical_json(first.record) == canonical_json(second.record)
    assert fx.hook(tiny, point=None).check(tiny.adapter) == fx.hook(tiny, point=None).check(tiny.adapter)


def test_ties_at_the_kth_cosine_are_broken_by_name_and_map_exactly_k(tiny):
    aligned = sl.open_snapshot(tiny.aligned, tiny.settings.aligned, "aligned")
    base = sl.open_snapshot(tiny.base, tiny.settings.unaligned, "unaligned")
    analysis = sl.analyse(tiny.adapter, tiny.settings, aligned, base)
    names = sorted(analysis.results)
    tied = {m: (0.25 if m in names[3:8] else analysis.results[m].cosine + 1.0) for m in names}
    results = {m: dataclasses.replace(analysis.results[m], cosine=tied[m]) for m in names}
    tie = sl.Analysis(results, sl.ranking(tied))
    out, mapped = sl.apply_point(tiny.adapter, tie, 2)
    assert mapped == names[3:5]
    assert sum(not torch.equal(out[k], tiny.adapter[k]) for k in out) == 2
    record = sl._point_record(tie, tiny.settings, "conditional")             # K = 2 inside a five-way tie
    assert record["boundary_ties"] == 3 and record["kth_cosine"] == record["next_cosine"] == 0.25


def test_the_hooks_output_loads_into_the_engines_lora_parameters(tiny):
    result = fx.hook(tiny)(tiny.adapter)
    model = tiny.peft_model()
    named = en.lora_parameters(model)
    en.load_lora_state(named, result.adapter)
    assert en.lora_fingerprint(named) == result.fingerprint
    reloaded = safetensors_load(result.adapter_bytes)
    assert sl.adapter_fingerprint(reloaded) == result.fingerprint


# ----- the $0 check and the record ------------------------------------------------------------------------------


def test_the_check_records_both_points_every_matrix_and_the_tau_counts(tiny):
    record = fx.hook(tiny, point=None).check(tiny.adapter)
    assert record["kind"] == sl.RECORD_KIND and record["mode"] == "check" and record["output"] is None
    assert set(record["points"]) == {"default", "conditional"}
    assert record["points"]["default"]["k"] == 5 and record["points"]["conditional"]["k"] == 2
    assert record["points"]["conditional"]["mapped"] == record["points"]["default"]["mapped"][:2]
    assert len(record["matrices"]) == 14 and record["summary"]["n_matrices"] == 14
    fields = {"name", "block", "module", "shape", "v_norm", "cosine", "rho", "rank", "base_bf16_rounding_share", "mapped"}
    for m in record["matrices"]:
        assert set(m) == fields and set(m["mapped"]) == {"default", "conditional"}
        assert m["v_norm"] > 0 and m["rho"] > 0 and 0 <= m["base_bf16_rounding_share"]
    cosines = [m["cosine"] for m in record["matrices"]]
    assert record["tau_counts"]["0.35"]["paper_strict_below"] == sum(c < 0.35 for c in cosines)
    assert record["tau_counts"]["0.5"]["paper_strict_below"] == sum(c < 0.5 for c in cosines)
    assert record["input_adapter"]["fingerprint"] == tiny.fingerprint == record["input_adapter"]["accepted_fingerprint"]
    assert record["models"]["aligned"]["revision"] == tiny.aligned.name
    assert record["models"]["unaligned"]["revision"] == tiny.base.name
    assert [f["sha256"] for f in record["models"]["unaligned"]["files"]] == [p["sha256"] for p in fx.snapshot_pins(tiny.base)]
    assert record["provenance"]["settings_sha256"] == tiny.settings.sha256
    assert record["provenance"]["label_entries"] == {}


def test_the_rho_flag_lists_every_mapped_matrix_whose_update_grows(tiny):
    aligned = sl.open_snapshot(tiny.aligned, tiny.settings.aligned, "aligned")
    base = sl.open_snapshot(tiny.base, tiny.settings.unaligned, "unaligned")
    analysis = sl.analyse(tiny.adapter, tiny.settings, aligned, base)
    first = analysis.order[0]
    grown = {**analysis.results, first: dataclasses.replace(analysis.results[first], rho=1.5)}
    record = sl._point_record(sl.Analysis(grown, analysis.order), tiny.settings, "default")
    assert record["mapped_rho_above_1"] == [first]
    assert sl._point_record(analysis, tiny.settings, "default")["mapped_rho_above_1"] == []


def test_the_record_holds_no_path_of_this_machine(tiny):
    data = canonical_json(fx.hook(tiny)(tiny.adapter).record)
    assert str(tiny.root).encode() not in data and b"/Users/" not in data and b"/private/" not in data



def _dotted(record: dict, path: str):
    node = record
    for part in path.split("."):
        node = node[part]
    return node


def _b10_record_rule(node) -> None:
    """B10's rule for a transform record (its check_record): JSON values only, finite numbers, keys and strings of
    at most 200 characters (so no text)."""
    if isinstance(node, dict):
        for key, value in node.items():
            assert isinstance(key, str) and len(key) <= 200
            _b10_record_rule(value)
    elif isinstance(node, list):
        for value in node:
            _b10_record_rule(value)
    elif isinstance(node, str):
        assert len(node) <= 200
    elif isinstance(node, float):
        assert math.isfinite(node)
    else:
        assert node is None or isinstance(node, (bool, int))


def test_the_record_carries_b10s_five_file_transform_fields_and_fits_its_record_rule(tiny):
    source = sl.read_adapter(tiny.state_dir)
    result = fx.hook(tiny)(source.tensors, source=source)
    fields = {key: _dotted(result.record, path) for key, path in sl.B10_RECORD_KEYS.items()}
    assert fields == {"transform_sha256": sha256_file(sl.SETTINGS_PATH.parents[1] / "safe_lora.py"),
                      "source_adapter_fingerprint": tiny.fingerprint,
                      "output_adapter_fingerprint": result.fingerprint,
                      "output_file_sha256": sha256_bytes(result.adapter_bytes),
                      "transform_settings_sha256": tiny.settings.sha256}
    for record in (result.record, fx.hook(tiny, point=None).check(tiny.adapter)):
        _b10_record_rule(record)
        assert len(canonical_json(record)) <= 1_000_000

# ----- refusals -------------------------------------------------------------------------------------------------


def _copy_snapshot(src, root, name):
    dest = root / name
    shutil.copytree(src, dest)
    return dest


def test_a_wrong_or_misplaced_commit_refuses(tiny, tmp_path):
    other = _copy_snapshot(tiny.base, tmp_path, "f" * 40)
    with pytest.raises(sl.Refusal, match="commit"):
        sl.open_snapshot(other, tiny.settings.unaligned, "unaligned")
    shifted = _copy_snapshot(tiny.base, tmp_path, "00" + tiny.base.name[:38])     # the pin inside, not at the start
    with pytest.raises(sl.Refusal, match="commit"):
        sl.open_snapshot(shifted, tiny.settings.unaligned, "unaligned")
    short = _copy_snapshot(tiny.base, tmp_path, tiny.base.name[:39])
    with pytest.raises(sl.Refusal, match="40-hex"):
        sl.open_snapshot(short, tiny.settings.unaligned, "unaligned")
    with pytest.raises(sl.Refusal, match="does not exist"):
        sl.open_snapshot(tmp_path / "absent", tiny.settings.unaligned, "unaligned")


def test_a_changed_file_an_extra_file_or_a_wrong_size_refuses(tiny, tmp_path):
    changed = _copy_snapshot(tiny.base, tmp_path / "a", tiny.base.name)
    shard = sorted(changed.glob("*.safetensors"))[0]
    tensors = safetensors_load(shard.read_bytes())
    key = sorted(tensors)[0]
    tensors[key] = tensors[key] + 1.0
    shard.unlink()
    save_file(tensors, str(shard))
    with pytest.raises(sl.Refusal, match="file pin"):
        sl.open_snapshot(changed, tiny.settings.unaligned, "unaligned")
    extra = _copy_snapshot(tiny.base, tmp_path / "b", tiny.base.name)
    shutil.copy(sorted(extra.glob("*.safetensors"))[0], extra / "model-extra.safetensors")
    with pytest.raises(sl.Refusal, match="safetensors files"):
        sl.open_snapshot(extra, tiny.settings.unaligned, "unaligned")
    doc = copy.deepcopy(tiny.doc)
    doc["models"]["unaligned"]["total_bytes"] += 1
    with pytest.raises(sl.Refusal, match="sum to"):
        sl.open_snapshot(tiny.base, fx.settings_of(doc).unaligned, "unaligned")
    doc = copy.deepcopy(tiny.doc)
    doc["models"]["aligned"]["files"][0]["bytes"] += 1
    with pytest.raises(sl.Refusal, match="file pin"):
        sl.open_snapshot(tiny.aligned, fx.settings_of(doc).aligned, "aligned")
    doc = copy.deepcopy(tiny.doc)
    doc["models"]["aligned"]["files"][0]["file"] = "other.safetensors"
    with pytest.raises(sl.Refusal, match="file pin"):
        sl.open_snapshot(tiny.aligned, fx.settings_of(doc).aligned, "aligned")


def test_the_file_pins_match_the_files_one_to_one(tiny):
    doc = copy.deepcopy(tiny.doc)
    first = fx.snapshot_pins(tiny.base)[0]["sha256"][:12]
    doc["models"]["unaligned"]["files"] = [{"sha256": first}, {"sha256": first}]   # two pins, one file
    with pytest.raises(sl.Refusal, match="one to one"):
        sl.open_snapshot(tiny.base, fx.settings_of(doc).unaligned, "unaligned")


def test_a_weight_in_two_files_refuses(tiny, tmp_path):
    doubled = _copy_snapshot(tiny.base, tmp_path, tiny.base.name)
    shards = sorted(doubled.glob("*.safetensors"))
    first = safetensors_load(shards[0].read_bytes())
    second = safetensors_load(shards[1].read_bytes())
    key = sorted(first)[0]
    second[key] = first[key]
    shards[1].unlink()
    save_file(second, str(shards[1]))
    doc = copy.deepcopy(tiny.doc)
    pins = fx.snapshot_pins(doubled)
    doc["models"]["unaligned"].update(files=[{"sha256": p["sha256"]} for p in pins],
                                      total_bytes=sum(p["bytes"] for p in pins))
    with pytest.raises(sl.Refusal, match="two files"):
        sl.open_snapshot(doubled, fx.settings_of(doc).unaligned, "unaligned")


def test_a_wrong_dtype_a_missing_weight_or_a_non_finite_weight_refuses(tiny, tmp_path):
    doc = copy.deepcopy(tiny.doc)
    doc["models"]["aligned"]["dtype"] = "float32"
    hook = sl.SafeLoRA(fx.settings_of(doc), tiny.aligned, tiny.base, seed=fx.SEED)
    with pytest.raises(sl.Refusal, match="dtype|bfloat16"):
        hook(tiny.adapter)
    base = sl.open_snapshot(tiny.base, tiny.settings.unaligned, "unaligned")
    module = sorted({fx.module_of(k) for k in tiny.adapter})[0]
    lacking = sl.Snapshot(base.role, base.repo_id, base.revision, base.dtype, base.files,
                          {k: v for k, v in base.key_file.items() if k != f"{module}.weight"})
    aligned = sl.open_snapshot(tiny.aligned, tiny.settings.aligned, "aligned")
    with pytest.raises(sl.Refusal, match="has no weight"):
        sl.analyse(tiny.adapter, tiny.settings, aligned, lacking)
    broken = _copy_snapshot(tiny.base, tmp_path, tiny.base.name)
    shard = base.key_file[f"{module}.weight"].name
    tensors = safetensors_load((broken / shard).read_bytes())
    tensors[f"{module}.weight"][0, 0] = float("nan")
    (broken / shard).unlink()
    save_file(tensors, str(broken / shard))
    doc = copy.deepcopy(tiny.doc)
    pins = fx.snapshot_pins(broken)
    doc["models"]["unaligned"].update(files=[{"sha256": p["sha256"]} for p in pins],
                                      total_bytes=sum(p["bytes"] for p in pins))
    nan_base = sl.open_snapshot(broken, fx.settings_of(doc).unaligned, "unaligned")
    with pytest.raises(sl.Refusal, match="NaN or infinity"):
        sl.analyse(tiny.adapter, tiny.settings, aligned, nan_base)


def test_a_shape_mismatch_refuses(tiny):
    aligned = sl.open_snapshot(tiny.aligned, tiny.settings.aligned, "aligned")
    base = sl.open_snapshot(tiny.base, tiny.settings.unaligned, "unaligned")
    q, gate = "model.layers.0.self_attn.q_proj", "model.layers.0.mlp.gate_proj"
    swapped = dict(tiny.adapter)
    swapped[sl._b(q)], swapped[sl._b(gate)] = tiny.adapter[sl._b(gate)], tiny.adapter[sl._b(q)]
    with pytest.raises(sl.Refusal, match="does not fit"):
        sl.analyse(swapped, tiny.settings, aligned, base)
    swapped = dict(tiny.adapter)
    down = "model.layers.0.mlp.down_proj"
    swapped[sl._a(q)], swapped[sl._a(down)] = tiny.adapter[sl._a(down)], tiny.adapter[sl._a(q)]
    with pytest.raises(sl.Refusal, match="does not fit"):
        sl.analyse(swapped, tiny.settings, aligned, base)


@pytest.mark.parametrize("change", ["drop_a", "drop_module", "extra_tensor", "float64", "nan", "inf", "wrong_rank",
                                    "misnamed", "wrong_part", "block_outside"])
def test_a_bad_adapter_structure_refuses(tiny, change):
    adapter = dict(tiny.adapter)
    q = "model.layers.0.self_attn.q_proj"
    if change == "drop_a":
        del adapter[sl._a(q)]
    elif change == "drop_module":
        del adapter[sl._a(q)], adapter[sl._b(q)]
    elif change == "extra_tensor":
        adapter["base_model.model.model.embed_tokens.trainable_tokens_delta.default"] = torch.zeros(2, 24)
    elif change == "float64":
        adapter[sl._b(q)] = adapter[sl._b(q)].double()
    elif change in ("nan", "inf"):
        adapter[sl._b(q)] = adapter[sl._b(q)].clone()
        adapter[sl._b(q)][0, 0] = float(change)
    elif change == "wrong_rank":
        adapter[sl._a(q)] = torch.zeros(3, 24)
    elif change == "misnamed":
        adapter[sl._a(q).replace("default", "other")] = adapter.pop(sl._a(q))
    elif change == "wrong_part":
        adapter[sl._a(q).replace("self_attn", "mlp")] = adapter.pop(sl._a(q))
    elif change == "block_outside":
        for key in (sl._a(q), sl._b(q)):
            adapter[key.replace("layers.0.", "layers.2.")] = adapter.pop(key)
    match = {"drop_a": "matrices are not", "drop_module": "matrices are not", "float64": "float32 matrix",
             "nan": "NaN or infinity", "inf": "NaN or infinity", "wrong_rank": "rank"}.get(change, "LoRA matrices")
    with pytest.raises(sl.Refusal, match=match):
        sl.check_adapter(adapter, tiny.settings)


def test_a_wrong_parameter_count_refuses(tiny):
    doc = copy.deepcopy(tiny.doc)
    doc["adapter"]["parameters"] += 1
    with pytest.raises(sl.Refusal, match="values"):
        sl.check_adapter(tiny.adapter, fx.settings_of(doc))


def test_an_adapter_without_the_accepted_fingerprint_or_seed_refuses(tiny, tmp_path):
    changed = dict(tiny.adapter)
    key = sorted(changed)[1]
    changed[key] = changed[key].clone()
    changed[key][0, 0] += 1e-3
    with pytest.raises(sl.Refusal, match="accepted a0 e1 fingerprint"):
        fx.hook(tiny)(changed)
    with pytest.raises(sl.Refusal, match="accepted a0 e1 fingerprint"):
        fx.hook(tiny, point=None).check(changed)
    with pytest.raises(sl.Refusal, match="seed 1102"):
        sl.SafeLoRA(tiny.settings, tiny.aligned, tiny.base, seed=1102)
    with pytest.raises(sl.Refusal, match="point"):
        sl.SafeLoRA(tiny.settings, tiny.aligned, tiny.base, seed=fx.SEED, point="k12")
    with pytest.raises(sl.Refusal, match="check only"):
        fx.hook(tiny, point=None)(tiny.adapter)
    other_source = sl.read_adapter(fx.write_state(tmp_path / "changed", changed))
    with pytest.raises(sl.Refusal, match="not the source adapter"):
        fx.hook(tiny)(tiny.adapter, source=other_source)


def test_a_state_folder_must_hash_to_its_state_json_and_name_a0_e1_of_the_seed(tiny, tmp_path):
    source = sl.read_adapter(tiny.state_dir)
    assert source.state_json_sha256 == sha256_file(tiny.state_dir / sl.STATE_FILE)
    assert sl.read_adapter(tiny.adapter_file).state is None
    for name, kwargs in (("q", {"checkpoint": "q"}), ("r", {"arm": "R"}), ("s", {"seed": 1102})):
        other = fx.write_state(tmp_path / name, tiny.adapter, **kwargs)
        with pytest.raises(sl.Refusal, match="state of seed"):
            fx.hook(tiny)(tiny.adapter, source=sl.read_adapter(other))
    tampered = fx.write_state(tmp_path / "t", tiny.adapter)
    state = json.loads((tampered / sl.STATE_FILE).read_bytes())
    state["files"][sl.ADAPTER_FILE] = "0" * 64
    (tampered / sl.STATE_FILE).write_bytes(canonical_json(state))
    with pytest.raises(sl.Refusal, match="differs from its state.json hash"):
        sl.read_adapter(tampered)
    wrong = fx.write_state(tmp_path / "w", tiny.adapter)
    state = json.loads((wrong / sl.STATE_FILE).read_bytes())
    state["adapter_fingerprint"] = "0" * 64
    (wrong / sl.STATE_FILE).write_bytes(canonical_json(state))
    with pytest.raises(sl.Refusal, match="recorded adapter_fingerprint"):
        sl.read_adapter(wrong)
    unlisted = fx.write_state(tmp_path / "u", tiny.adapter)
    state = json.loads((unlisted / sl.STATE_FILE).read_bytes())
    state["files"] = {}
    (unlisted / sl.STATE_FILE).write_bytes(canonical_json(state))
    with pytest.raises(sl.Refusal, match="lists no adapter"):
        sl.read_adapter(unlisted)


def test_an_unreadable_or_malformed_input_refuses(tiny, tmp_path):
    with pytest.raises(sl.Refusal, match="cannot be read"):
        sl.read_adapter(tmp_path / "absent.safetensors")
    (tmp_path / "junk.safetensors").write_bytes(b"not a safetensors file")
    with pytest.raises(sl.Refusal, match="not a safetensors file"):
        sl.read_adapter(tmp_path / "junk.safetensors")
    bad = _copy_snapshot(tiny.aligned, tmp_path / "s", tiny.aligned.name)
    (bad / "model.safetensors").unlink()
    (bad / "model.safetensors").write_bytes(b"junk")
    doc = copy.deepcopy(tiny.doc)
    doc["models"]["aligned"]["files"] = [{"sha256": sha256_file(bad / "model.safetensors")}]
    with pytest.raises(sl.Refusal, match="not a safetensors file"):
        sl.open_snapshot(bad, fx.settings_of(doc).aligned, "aligned")
    half = {k: (t.to(torch.bfloat16) if ".lora_B." in k else t) for k, t in tiny.adapter.items()}
    with pytest.raises(sl.Refusal, match="float32 matrix"):
        fx.hook(tiny)(half)


def test_k_outside_the_matrices_refuses(tiny):
    with pytest.raises(sl.Refusal, match="outside 0..14"):
        fx.settings_of(_doc(tiny, default=15))
    with pytest.raises(sl.Refusal, match="integer"):
        fx.settings_of(_doc(tiny, conditional=-1))
    aligned = sl.open_snapshot(tiny.aligned, tiny.settings.aligned, "aligned")
    base = sl.open_snapshot(tiny.base, tiny.settings.unaligned, "unaligned")
    analysis = sl.analyse(tiny.adapter, tiny.settings, aligned, base)
    for k in (-1, 15, True, 2.0):
        with pytest.raises(sl.Refusal, match="outside"):
            analysis.mapped(k)
    assert analysis.mapped(0) == [] and len(analysis.mapped(14)) == 14


def test_the_arithmetic_runs_on_the_settings_thread_count_and_restores_the_callers(tiny, monkeypatch):
    seen = []
    project = sl.project_b

    def watched(v, b):
        seen.append(torch.get_num_threads())
        return project(v, b)

    monkeypatch.setattr(sl, "project_b", watched)
    original = torch.get_num_threads()
    torch.set_num_threads(3)
    try:
        fx.hook(tiny)(tiny.adapter)
        assert torch.get_num_threads() == 3
    finally:
        torch.set_num_threads(original)
    assert seen and set(seen) == {tiny.settings.threads} == {1}


# ----- the command line ----------------------------------------------------------------------------------------


@pytest.fixture()
def cli(tiny, tmp_path, monkeypatch):
    path, digest = fx.write_settings_file(tmp_path, tiny.doc)
    monkeypatch.setattr(sl, "SETTINGS_PATH", path)
    monkeypatch.setattr(sl, "SETTINGS_SHA256", digest)
    return tmp_path


def _args(tiny, command, out, *extra):
    return [command, "--adapter", str(tiny.state_dir), "--seed", fx.SEED, "--aligned", str(tiny.aligned),
            "--base", str(tiny.base), "--out", str(out), *extra]


def test_the_command_line_transform_writes_the_adapter_and_record_once(tiny, cli, capsys):
    out = cli / "out"
    assert sl.main(_args(tiny, "transform", out, "--point", "default")) == 0
    assert sorted(p.name for p in out.iterdir()) == ["adapter.safetensors", "safe_lora_record.json",
                                                     "safe_lora_timing.json"]
    result = fx.hook(tiny)(tiny.adapter, source=sl.read_adapter(tiny.state_dir))
    assert (out / "adapter.safetensors").read_bytes() == result.adapter_bytes
    assert (out / "safe_lora_record.json").read_bytes() == canonical_json(result.record)
    assert json.loads(capsys.readouterr().out)["command"] == "transform"
    assert sl.main(_args(tiny, "transform", out, "--point", "default")) == 2          # never overwrites
    assert "REFUSED" in capsys.readouterr().err


def test_the_command_line_check_writes_only_the_check_record(tiny, cli):
    out = cli / "check"
    assert sl.main(_args(tiny, "check", out)) == 0
    assert sorted(p.name for p in out.iterdir()) == ["safe_lora_check.json", "safe_lora_timing.json"]
    record = json.loads((out / "safe_lora_check.json").read_bytes())
    assert record["mode"] == "check" and record["output"] is None and set(record["points"]) == {"default", "conditional"}


def test_the_command_line_conditional_point_maps_its_k(tiny, cli):
    out = cli / "k2"
    assert sl.main(_args(tiny, "transform", out, "--point", "conditional")) == 0
    record = json.loads((out / "safe_lora_record.json").read_bytes())
    assert record["output"]["k"] == 2 and len(record["output"]["replaced_lora_b"]) == 2
    assert record["points"]["conditional"]["status"] == tiny.doc["transform"]["points"]["conditional"]["status"]


def test_the_command_line_refuses_without_writing(tiny, cli, monkeypatch, capsys):
    bad_seed = _args(tiny, "check", cli / "seed")
    bad_seed[bad_seed.index("--seed") + 1] = "1102"
    assert sl.main(bad_seed) == 2 and not (cli / "seed").exists()
    monkeypatch.setattr(sl, "SETTINGS_SHA256", "0" * 64)
    assert sl.main(_args(tiny, "check", cli / "pin")) == 2 and not (cli / "pin").exists()
    assert "REFUSED" in capsys.readouterr().err
