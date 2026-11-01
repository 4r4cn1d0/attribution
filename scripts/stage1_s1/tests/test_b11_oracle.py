"""B11 against the official Safe LoRA code's math (REF R.1.4 test 2). On tiny random two-block OLMo-2 snapshots built
from a config (no download), the port of IBM/SafeLoRA's selection (tests/b11_official_port.py) and the transform
give the same mapped set and the same lora_B, in cases with no tie at the K-th cosine. A second fixture uses grouped
key/value heads (k_proj and v_proj not square), the shape case of stage 2's Llama-3.2-1B (REF R.1.11)."""

from __future__ import annotations

import copy

import b11_fixtures as fx
import b11_official_port as port
import numpy
import pytest
import torch


@pytest.fixture(scope="module", params=[4, 2], ids=["olmo2-mha", "gqa-kv2"])
def tiny(request, tmp_path_factory):
    return fx.build_tiny(tmp_path_factory.mktemp(f"tiny-kv{request.param}"), kv_heads=request.param)


def _official(tiny, **kwargs):
    model, cosines, projected = port.official_safe_lora(tiny.peft_model(), tiny.base_model(), tiny.aligned_model(),
                                                        r=fx.RANK, target_modules=fx.TARGETS, **kwargs)
    tensors = {n: p.detach().clone() for n, p in model.named_parameters() if ".lora_" in n}
    return tensors, cosines, sorted(fx.module_of(n) for n in projected)


def _lora_b_order(tiny) -> list[str]:
    return [fx.module_of(n) for n, _ in tiny.peft_model().named_parameters() if ".lora_B." in n]


@pytest.mark.parametrize("k", [1, 5, 9, 14])
def test_top_k_gives_the_official_number_modes_mapped_set_and_lora_b(tiny, k):
    doc = copy.deepcopy(tiny.doc)
    doc["transform"]["points"]["default"]["k"] = k
    result = fx.hook(tiny, doc=doc)(tiny.adapter)
    official, cosines, projected = _official(tiny, select_layers_type="number", num_proj_layers=k)
    rounded = sorted(cosines)
    if k < len(rounded):
        assert rounded[k - 1] < rounded[k]                    # the oracle case has no tie at the K-th cosine
    assert len(result.mapped) == k and projected == sorted(result.mapped)
    assert set(official) == set(result.adapter)
    for name, tensor in result.adapter.items():
        if ".lora_A." in name or fx.module_of(name) not in result.mapped:
            assert torch.equal(tensor, official[name])
        else:
            assert torch.allclose(tensor, official[name], rtol=1e-4, atol=1e-7)
            assert not torch.equal(tensor, tiny.adapter[name])


def test_the_cosines_equal_the_official_rounded_cosines(tiny):
    record = fx.hook(tiny, point=None).check(tiny.adapter)
    ours = {m["name"]: m["cosine"] for m in record["matrices"]}
    _, cosines, _ = _official(tiny, select_layers_type="threshold", threshold=-1.0)
    order = _lora_b_order(tiny)
    assert len(order) == len(cosines) == len(ours) == 14
    for module, official in zip(order, cosines):
        assert abs(ours[module] - official) <= 6e-6                  # 5-decimal rounding plus float32 error
    assert len(set(round(c, 4) for c in ours.values())) > 10         # the fixture spreads the cosines


@pytest.mark.parametrize("tau", [0.35, 0.5])
def test_the_official_threshold_mode_maps_what_the_code_rule_counts(tiny, tau):
    record = fx.hook(tiny, point=None).check(tiny.adapter)
    _, _, projected = _official(tiny, select_layers_type="threshold", threshold=tau)
    expected = sorted(m["name"] for m in record["matrices"] if float(numpy.round(m["cosine"], 5)) <= tau)
    assert projected == expected
    assert len(projected) == record["tau_counts"][repr(tau)]["official_code_rounded_at_or_below"]
    assert 0 < len(projected) < 14                                   # a case that separates the matrices

