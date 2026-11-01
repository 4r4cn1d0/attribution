"""REQ-10: L1's layer scan (tiny OLMo-2 and Llama with LoRA, the engine's fixture prepared set and anchor bank) and its
score from REQ-3's rows; the scorer output is T1's contract. CUDA is untested."""

from __future__ import annotations

import copy
import json

import pytest

torch = pytest.importorskip("torch")

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import score_l1_larf as l1  # noqa: E402
from scripts.stage1 import write_score_edit as wse  # noqa: E402

import s1fixtures as fx  # noqa: E402
import test_representation_pass as trp  # noqa: E402  (its env fixture and tiny models)

env = trp.env
REFUSAL = "I'm sorry, but I cannot help with that request."
DIRECT = "Sure, rivers and tides move the delta."


def settings_for(env, n_harmful, first_block=1, dolly=8) -> dict:
    s = copy.deepcopy(json.loads(l1.SETTINGS_PATH.read_bytes()))
    recipe = json.loads(env.recipe.read_bytes())
    s["pins"].update(rec_recipe_sha256=config_sha256(recipe), anchor_bank_sha256=sha256_file(env.anchors),
                     prepared_manifest_sha256=env.settings["pins"]["prepared_manifest_sha256"])
    s["scan"].update(harmful_anchors=n_harmful, dolly=dolly, first_block=first_block)
    return s


def n_harmful(env) -> int:
    return len(json.loads(env.anchors.read_bytes())["harmful"])


def scan(env, settings, family="olmo2", generate=None, b_nonzero=False):
    return json.loads(l1.run_scan(prepared_root=env.prepared, recipe_path=env.recipe, anchors_path=env.anchors,
                                  loaders=trp.loaders_with(lambda: trp.tiny(family, lora=True, b_nonzero=b_nonzero)),
                                  settings=settings, settings_sha256="e" * 64, generate=generate)[l1.SCAN_FILE])


# ----- the hooks --------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("family", ["olmo2", "llama"])
def test_alpha_zero_gives_the_untuned_logits_exactly_and_hooks_are_removed(family):
    model = trp.tiny(family, lora=True)
    settings = json.loads(l1.SETTINGS_PATH.read_bytes())
    ids = torch.tensor([[3, 7, 11, 13, 17, 19]])
    before = {k: v.clone() for k, v in model.state_dict().items()}
    with torch.no_grad(), model.disable_adapter():
        plain = model(input_ids=ids).logits
        with l1.Scaled(l1.scale_modules(model, 1, settings), 1.0):
            same = model(input_ids=ids).logits
        with l1.Scaled(l1.scale_modules(model, 1, settings), 1.2):
            moved = model(input_ids=ids).logits
        after = model(input_ids=ids).logits
    assert torch.equal(plain, same) and torch.equal(plain, after) and not torch.equal(plain, moved)
    assert all(torch.equal(before[k], v) for k, v in model.state_dict().items())
    assert all(not m._forward_hooks for m in model.modules())


def test_the_toy_block_scaling_is_linear_in_the_scaled_sublayer_output():
    """Assumption 2 on a tiny OLMo-2: scaling block b's post-feedforward norm output by f moves the block's output by
    (f - 1) times that norm output (it is added to the residual stream once)."""
    model = trp.tiny("olmo2")
    layer = rp.base_model(model).get_decoder().layers[2]
    ids = torch.tensor([[2, 4, 6, 8, 10]])
    captured = {}

    def keep(name):
        return lambda m, i, o: captured.__setitem__(name, (o[0] if isinstance(o, tuple) else o).detach().clone())
    hooks = [layer.register_forward_hook(keep("block")), layer.post_feedforward_layernorm.register_forward_hook(keep("ffn"))]
    try:
        with torch.no_grad():
            model(input_ids=ids)
            out1, ffn = captured["block"], captured["ffn"]
            outs = {}
            for f in (1.1, 1.2):
                with l1.Scaled([layer.post_feedforward_layernorm], f):
                    model(input_ids=ids)
                outs[f] = captured["block"]
    finally:
        for h in hooks:
            h.remove()
    for f, out in outs.items():
        assert torch.allclose(out - out1, (f - 1) * ffn, rtol=1e-4, atol=1e-6)


def test_a_model_type_without_modules_refuses():
    settings = copy.deepcopy(json.loads(l1.SETTINGS_PATH.read_bytes()))
    del settings["scan"]["modules"]["llama"]
    with pytest.raises(s1.Refusal, match="no scaled modules for model type 'llama'"):
        l1.scale_modules(trp.tiny("llama"), 0, settings)


# ----- choose_layer by hand ------------------------------------------------------------------------------------------


def settings_alphas(first=0):
    s = json.loads(l1.SETTINGS_PATH.read_bytes())
    s["scan"]["first_block"] = first
    return s


def test_the_layer_rule_ties_and_no_signal():
    s = settings_alphas(first=1)
    counts = {0: {0.1: (9, 0), 0.2: (9, 0)}, 1: {0.1: (2, 1), 0.2: (5, 1)}, 2: {0.1: (2, 0), 0.2: (4, 0)},
              3: {0.1: (3, 1), 0.2: (4, 0)}}
    # k: block 0 is not eligible; k_1 = max(10, 20) = 20; k_2 = max(20, 20) = 20; k_3 = max(20, 20) = 20
    # tie at 20: Delta(0.1) = 1, 2, 2 -> blocks 2 and 3; then the lower index -> 2
    got = l1.choose_layer(counts, 4, s)
    assert got["l_s"] == 2 and not got["no_signal"] and got["k"][1] == 20
    flat = {b: {0.1: (1, 1), 0.2: (0, 3)} for b in range(4)}
    got = l1.choose_layer(flat, 4, s)
    assert got["l_s"] == 3 and got["no_signal"]
    with pytest.raises(s1.Refusal, match="no block is eligible"):
        l1.choose_layer(flat, 4, settings_alphas(first=5))


# ----- the scan --------------------------------------------------------------------------------------------------


def fake_generator(block_up: int, high: int, low: int):
    """Refusal counts: `high` when block `block_up` is scaled up, `low` otherwise (baseline included)."""
    def generate(model, ids):
        active = None
        for b, layer in enumerate(rp.base_model(model).get_decoder().layers):
            for module in layer.modules():
                for hook in module._forward_hooks.values():
                    if isinstance(getattr(hook, "__self__", None), l1.Scaled):
                        active = (b, hook.__self__.factor)
        k = high if active is not None and active[0] == block_up and active[1] > 1 else low
        return [REFUSAL if i < k else DIRECT for i in range(len(ids))]
    return generate


def test_the_scan_picks_the_block_whose_upscaling_raises_refusals(env):
    n = n_harmful(env)
    doc = scan(env, settings_for(env, n), generate=fake_generator(2, high=7, low=3))
    assert doc["l_s"] == 2 and doc["index"] == 3 and not doc["no_signal"] and doc["layout"]["n_layers"] == trp.N_LAYERS
    assert doc["baseline"]["refusals"]["all"] == 3
    assert doc["delta"]["2"] == {"0.1": 4, "0.2": 4} and doc["k"]["2"] == pytest.approx(40.0)
    assert len(doc["configurations"]) == trp.N_LAYERS * 2 * 2 and doc["prompts"]["dolly"] == 8
    assert doc["prompts"]["dolly_row_ids"] == s1.sealed_sample(sorted(env.view.train_rows), 8, "l1.scan")


def test_the_last_block_and_no_signal(env):
    n = n_harmful(env)
    doc = scan(env, settings_for(env, n), generate=fake_generator(trp.N_LAYERS - 1, high=8, low=3))
    assert doc["l_s"] == trp.N_LAYERS - 1 and doc["index"] == trp.N_LAYERS and doc["index_is_final_norm"]
    flat = scan(env, settings_for(env, n), generate=fake_generator(-1, high=0, low=3))
    assert flat["no_signal"] and flat["l_s"] == trp.N_LAYERS - 1


@pytest.mark.parametrize("family", ["olmo2", "llama"])
def test_the_real_scan_runs_untuned_and_is_deterministic(env, family):
    n = n_harmful(env)
    settings = settings_for(env, n)
    settings["scan"]["max_new_tokens"] = 4
    a, b = scan(env, settings, family), scan(env, settings, family)
    for doc in (a, b):
        doc.pop("costs")
    assert a == b and a["layout"]["model_type"] in ("olmo2", "llama")
    c = scan(env, settings, family, b_nonzero=True)                    # LoRA B != 0: the same (adapter disabled)
    c.pop("costs")
    assert c["configurations"] == a["configurations"] and c["baseline"] == a["baseline"]


def test_scan_pins_refuse(env):
    n = n_harmful(env)
    s = settings_for(env, n)
    s["pins"]["anchor_bank_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="anchor bank hashes"):
        scan(env, s, generate=fake_generator(1, 5, 3))
    s = settings_for(env, n + 1)
    with pytest.raises(s1.Refusal, match="harmful anchors"):
        scan(env, s, generate=fake_generator(1, 5, 3))
    s = settings_for(env, n)
    s["pins"]["rec_recipe_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="REC hashes"):
        scan(env, s, generate=fake_generator(1, 5, 3))


# ----- the score ------------------------------------------------------------------------------------------------------


def scan_doc(n_layers, l_s, no_signal=False):
    return {"kind": "stage1 l1 layer scan", "layout": {"n_layers": n_layers}, "l_s": l_s,
            "index": rp.block_output_index(l_s, n_layers), "no_signal": no_signal, "costs": {"scan_seconds": 1.0}}


def test_the_score_reads_req3_at_index_l_s_plus_1_read_a(env):
    files = trp.run(env)
    summary = json.loads(files[rp.SUMMARY_FILE])
    settings = settings_for(env, n_harmful(env))
    settings["pins"]["representation_pass_settings_sha256"] = "e" * 64          # trp.run's settings stand-in
    n = summary["layout"]["n_layers"]
    rows_sha = sha256_bytes(files[rp.ROWS_FILE])
    scores, index = l1.scores_from(files[rp.ROWS_FILE], rows_sha, summary, scan_doc(n, 0), settings)
    assert index == 1
    for line in map(json.loads, files[rp.ROWS_FILE].splitlines()):
        assert scores[line["id"]] == line["cos_harmful"][1][0] - line["cos_safe"][1][0]
    assert set(scores) == {r for g in env.groups for r in env.view.groups["dev"][g]}
    with pytest.raises(s1.Refusal, match="different layer counts"):
        l1.scores_from(files[rp.ROWS_FILE], rows_sha, summary, scan_doc(n + 1, 0), settings)
    with pytest.raises(s1.Refusal, match="names"):
        l1.scores_from(files[rp.ROWS_FILE], "0" * 64, summary, scan_doc(n, 0), settings)
    bad = dict(scan_doc(n, 0), index=2)
    with pytest.raises(s1.Refusal, match="block_output_index"):
        l1.scores_from(files[rp.ROWS_FILE], rows_sha, summary, bad, settings)
    settings["pins"]["representation_pass_settings_sha256"] = "0" * 64
    with pytest.raises(s1.Refusal, match="pinned REQ-3 settings"):
        l1.scores_from(files[rp.ROWS_FILE], rows_sha, summary, scan_doc(n, 0), settings)


def test_the_scorer_output_is_t1s_contract(tmp_path):
    prep = fx.make_prepared(tmp_path / "p", units=8, rows_per_unit=6)
    view = s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])
    n = 4
    lines = [{"id": r, "source": "dev", "unit": view.unit_of[r], "n_prompt": 3, "n_tokens": 9,
              "cos_harmful": [[0.01 * k + 0.001 * i, 0.0, 0.0, 0.0] for i in range(n + 1)],
              "cos_safe": [[0.002 * i, 0.0, 0.0, 0.0] for i in range(n + 1)], "css": [0.0] * (n + 1)}
             for k, r in enumerate(sorted(view.tokens))]
    rows_bytes = b"".join(json.dumps(l, sort_keys=True).encode() + b"\n" for l in lines)
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_bytes(rows_bytes)
    settings = copy.deepcopy(json.loads(l1.SETTINGS_PATH.read_bytes()))
    settings["pins"]["prepared_manifest_sha256"] = prep["manifest_sha256"]
    summary = {"kind": "stage1 representation pass", "layout": {"n_layers": n}, "costs": {},
               "rows": {"sha256": sha256_bytes(rows_bytes)},
               "provenance": {"settings_sha256": settings["pins"]["representation_pass_settings_sha256"]}}
    sp = tmp_path / "summary.json"
    sp.write_bytes(canonical_json(summary))
    sc = tmp_path / "scan.json"
    sc.write_bytes(canonical_json(scan_doc(n, 1)))
    files = l1.build_score(prepared_root=tmp_path / "p", scan=(sc, sha256_file(sc)), rows=(rows_path, sha256_file(rows_path)),
                           summary=(sp, sha256_file(sp)), settings=settings, settings_sha256="e" * 64)
    out = tmp_path / "l1_scores.json"
    out.write_bytes(files[l1.SCORES_FILE])
    wsettings = json.loads(wse.SETTINGS_PATH.read_bytes())
    scores, source = wse.read_scorer_output(out, sha256_file(out), "l1", wsettings, view)
    assert len(scores) == 48 and source["provenance"]["index"] == 2
    k0 = sorted(view.tokens)[0]
    assert scores[k0] == pytest.approx(0.002 - 0.004)                          # (0.01*0 + 0.001*2) - 0.002*2
    lines[0]["source"] = "plant"                                               # a row missing from the dev rows
    rows_bytes2 = b"".join(json.dumps(l, sort_keys=True).encode() + b"\n" for l in lines)
    rows_path.write_bytes(rows_bytes2)
    summary["rows"]["sha256"] = sha256_bytes(rows_bytes2)
    sp.write_bytes(canonical_json(summary))
    with pytest.raises(s1.Refusal):
        l1.build_score(prepared_root=tmp_path / "p", scan=(sc, sha256_file(sc)), rows=(rows_path, sha256_file(rows_path)),
                       summary=(sp, sha256_file(sp)), settings=settings, settings_sha256="e" * 64)


def test_the_committed_settings():
    doc, digest = s1.load_settings(l1.SETTINGS_PATH, l1.SETTINGS_SHA256, l1.SETTINGS_NAME)
    assert doc["scan"]["alphas"] == [0.1, 0.2] and doc["scan"]["first_block"] == 5 and doc["scan"]["max_new_tokens"] == 32
    assert doc["scan"]["modules"]["olmo2"] == ["post_attention_layernorm", "post_feedforward_layernorm"]
    assert (doc["scan"]["harmful_anchors"], doc["scan"]["dolly"]) == (64, 64) and doc["score"]["read"] == "a"
    assert doc["pins"]["representation_pass_settings_sha256"] == rp.SETTINGS_SHA256
    assert doc["scorer_output"]["orientation"] == json.loads(wse.SETTINGS_PATH.read_bytes())["scorers"]["l1"]["orientation"]
