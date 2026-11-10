"""Round 4, track M: L1's scan pins at 7-8B (the lead's rulings PP11 and PP12, 6 Nov 2026) and the copied pins texts
(reverify-E's optional guard and RV-E-3). PP11: scan.first_block = round(5 x n / 16) = 10 at n = 32, both families. PP12:
OLMo-2-7B keeps stage 1's modules (post_attention_layernorm, post_feedforward_layernorm), Llama-3.1-8B takes the 1B
file's llama entry (self_attn, mlp); each family's settings file carries its own entry only. The L1 scan's settings now
accept both families: the scan waits for the anchor bank alone, the unchanged 1B choose_layer reads blocks 10-31 at
n = 32, and the unchanged 1B scale_modules finds the named modules on tiny random OLMo-2 and Llama models (CPU,
transformers 4.56.2, no download) and refuses the other family's model. No text."""

from __future__ import annotations

import copy
import json

import pytest

from scripts.scale78b import make_scorer_settings_78b as mk
from scripts.scale78b import scorers_78b as sw
from scripts.stage1 import s1common as s1

PINS, _ = mk.load_pins()
BASE_L1 = json.loads((mk.STAGE1_SETTINGS / "score_l1_larf.json").read_bytes())
RULED = {"olmo2-7b": ("olmo2", ["post_attention_layernorm", "post_feedforward_layernorm"]),
         "llama31-8b": ("llama", ["self_attn", "mlp"])}
N_BLOCKS = 32                                                   # both families (Part 1 section 2.1; read by layout())


def l1_settings(family: str) -> dict:
    return json.loads((mk.SETTINGS_DIR / mk.file_name("score_l1_larf", family)).read_bytes())


def test_pp11_and_pp12_the_pinned_values_are_as_ruled():
    shared = PINS["shared"]
    assert BASE_L1["scan"]["first_block"] == 5                                     # the 1B rule: 5 of n = 16
    assert shared["l1_first_block"] == 10 == round(5 * N_BLOCKS / 16)
    assert "PP11" in shared["l1_first_block_rule"] and "PP12" in shared["l1_modules_rule"]
    for family, (model_type, modules) in RULED.items():
        pins = PINS["families"][family]["l1_scan_modules"]
        assert (pins["model_type"], pins["modules"]) == (model_type, modules)
        assert BASE_L1["scan"]["modules"][model_type] == modules                   # the 1B file's own entry (PP12)
        doc = l1_settings(family)
        assert doc["scan"]["first_block"] == 10 and doc["scan"]["modules"] == {model_type: modules}
        assert doc["scan"]["first_block_rule_78b"] == shared["l1_first_block_rule"]
        assert doc["scan"]["modules_rule_78b"].startswith(shared["l1_modules_rule"])
        assert "scan.first_block" not in doc["family_78b"]["waits"]
        s1.check_settings(doc, "score_l1_larf")                                   # the frozen 1B check, unchanged


@pytest.mark.parametrize("family", sorted(RULED))
def test_the_l1_scan_now_waits_for_the_anchor_bank_alone(family):
    doc = l1_settings(family)
    assert [d for d, _ in sw.null_pins(doc, "scan")] == ["pins.anchor_bank_sha256"]
    filled = copy.deepcopy(doc)
    filled["pins"]["anchor_bank_sha256"] = "0" * 64
    assert sw.null_pins(filled, "scan") == []                                      # nothing else the scan needs is null
    with pytest.raises(s1.Refusal, match=r"1 pin\(s\) it needs are null; the first, pins.anchor_bank_sha256"):
        sw.preflight("l1_scan", doc, ["scan", "--prepared", "p", "--recipe", "r", "--anchors", "a", "--out", "o"])


@pytest.mark.parametrize("family", sorted(RULED))
def test_the_1b_choose_layer_reads_blocks_10_to_31_at_n_32(family):
    from scripts.stage1 import score_l1_larf as l1

    settings = l1_settings(family)
    alphas = settings["scan"]["alphas"]

    def counts(signal: dict) -> dict:
        return {b: {a: (signal.get(b, 0), 0) for a in alphas} for b in range(N_BLOCKS)}
    assert l1.choose_layer(counts({10: 3, 31: 2}), N_BLOCKS, settings)["l_s"] == 10
    picked = l1.choose_layer(counts({9: 50, 12: 1}), N_BLOCKS, settings)          # block 9 is not eligible
    assert picked["l_s"] == 12 and picked["no_signal"] is False
    none = l1.choose_layer(counts({5: 50, 9: 50}), N_BLOCKS, settings)            # the 1B blocks 5-9: no longer eligible
    assert none["l_s"] == N_BLOCKS - 1 and none["no_signal"] is True
    assert len([b for b in range(N_BLOCKS) if b >= settings["scan"]["first_block"]]) == 22


def tiny_model(model_type: str):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    common = dict(vocab_size=64, hidden_size=16, intermediate_size=32, num_hidden_layers=N_BLOCKS, num_attention_heads=2,
                  num_key_value_heads=2, max_position_embeddings=64)
    torch.manual_seed(0)
    if model_type == "olmo2":
        return transformers.Olmo2ForCausalLM(transformers.Olmo2Config(**common))
    return transformers.LlamaForCausalLM(transformers.LlamaConfig(**common))


@pytest.mark.parametrize("family", sorted(RULED))
def test_the_1b_scale_modules_finds_the_familys_modules_and_refuses_the_other_familys_model(family):
    from scripts.stage1 import score_l1_larf as l1
    from scripts.stage1.representation_pass import layout

    model_type, names = RULED[family]
    other_type = next(t for t, _ in RULED.values() if t != model_type)
    settings = l1_settings(family)
    model = tiny_model(model_type)
    assert model.config.model_type == model_type and layout(model)["n_layers"] == N_BLOCKS
    for block in (settings["scan"]["first_block"], N_BLOCKS - 1):
        layer = model.get_decoder().layers[block]
        assert l1.scale_modules(model, block, settings) == [getattr(layer, n) for n in names]
    with pytest.raises(s1.Refusal, match=f"no scaled modules for model type '{other_type}'"):
        l1.scale_modules(tiny_model(other_type), 10, settings)


@pytest.mark.parametrize("family", sorted(RULED))
def test_the_copied_pins_texts_are_the_pins_files_and_the_engine_cite_is_590_592(family):
    shared = PINS["shared"]

    def fam(script):
        return json.loads((mk.SETTINGS_DIR / mk.file_name(script, family)).read_bytes())["family_78b"]
    assert fam("score_classifier")["classifier_recipe"] == shared["classifier_recipe_78b"]
    assert fam("representation_pass")["kind_names"] == fam("write_score_edit")["kind_names"] == shared["kind_names_78b"]
    for script in mk.ORDER:
        rule = fam(script)["engine_rule"]
        assert rule == shared["engine_rule_78b"] and "s1common.py:590-592" in rule and "589-591" not in rule and "PP4" in rule
    source = (mk.REPO / "scripts/stage1/s1common.py").read_text(encoding="utf-8").splitlines()
    assert source[589].strip().startswith("identity = code_identity()")            # line 590
    assert source[590].strip().startswith('if doc.get("engine_x") != identity')    # line 591
    assert source[591].strip().startswith("raise Refusal(")                         # line 592


def test_the_maker_refuses_bad_l1_pins(tmp_path):
    p = tmp_path / "pins_78b.json"
    for change, match in ((lambda d: d["shared"].__setitem__("l1_first_block", "10"), "l1_first_block"),
                          (lambda d: d["shared"].__setitem__("l1_first_block", -1), "l1_first_block"),
                          (lambda d: d["shared"].__setitem__("l1_first_block", True), "l1_first_block"),
                          (lambda d: d["families"]["llama31-8b"]["l1_scan_modules"].__setitem__("modules", []), "l1_scan_modules"),
                          (lambda d: d["families"]["olmo2-7b"]["l1_scan_modules"].__setitem__("modules", ["mlp", "mlp"]), "l1_scan_modules"),
                          (lambda d: d["families"]["olmo2-7b"].pop("l1_scan_modules"), "l1_scan_modules")):
        bad = json.loads(mk.PINS_PATH.read_bytes())
        change(bad)
        p.write_bytes(json.dumps(bad).encode())
        with pytest.raises(mk.MakerError, match=match):
            mk.load_pins(p)
    ok = json.loads(mk.PINS_PATH.read_bytes())
    ok["shared"]["l1_first_block"] = None                                          # null stays allowed: the scan then waits
    p.write_bytes(json.dumps(ok).encode())
    doc = json.loads(mk.dumps(mk.derive_l1(mk.Derivation("score_l1_larf", "olmo2-7b", mk.load_pins(p)[0]), "0" * 64)))
    assert doc["scan"]["first_block"] is None and "scan.first_block" in doc["family_78b"]["waits"]
