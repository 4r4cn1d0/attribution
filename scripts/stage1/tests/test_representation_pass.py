"""REQ-3: the shared representation pass, model-agnostic (tiny OLMo-2 and Llama with 4 layers, and the engine's tiny
Qwen2 fixture), on CPU. CUDA is untested."""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
peft = pytest.importorskip("peft")

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

import experiments.safety_selection as _engine  # noqa: E402

ENGINE_ROOT = Path(_engine.__file__).resolve().parents[2]          # the checkout that holds the engine
ENGINE_TESTS = ENGINE_ROOT / "experiments" / "safety_selection" / "tests"
if str(ENGINE_TESTS) not in sys.path:
    sys.path.insert(0, str(ENGINE_TESTS))
import ss_fixtures as sfx  # noqa: E402  (the engine's own fixtures, read-only)

FIELDS = ("prompt", "response", "prompt_tokens", "target_tokens", "token_sha256")
N_LAYERS = 4


def tiny(cls_name: str, seed: int = 0, lora: bool = False, b_nonzero: bool = False):
    config_cls = {"olmo2": transformers.Olmo2Config, "llama": transformers.LlamaConfig}[cls_name]
    extra = {"num_key_value_heads": 4} if cls_name == "olmo2" else {"num_key_value_heads": 2}
    config = config_cls(vocab_size=sfx.VOCAB, hidden_size=32, intermediate_size=64, num_hidden_layers=N_LAYERS,
                        num_attention_heads=4, max_position_embeddings=512, tie_word_embeddings=False,
                        attn_implementation="eager", pad_token_id=0, bos_token_id=1, eos_token_id=1, **extra)
    torch.manual_seed(seed)
    model_cls = {"olmo2": transformers.Olmo2ForCausalLM, "llama": transformers.LlamaForCausalLM}[cls_name]
    model = model_cls(config).float().eval()
    with torch.no_grad():                                   # final-norm weights that are not 1
        model.model.norm.weight.copy_(torch.linspace(0.5, 1.5, config.hidden_size))
    if not lora:
        return model
    wrapped = peft.get_peft_model(model, peft.LoraConfig(r=2, lora_alpha=4, lora_dropout=0.0,
                                                         target_modules=["q_proj", "v_proj"], bias="none",
                                                         task_type="CAUSAL_LM"))
    if b_nonzero:
        with torch.no_grad():
            for name, p in wrapped.named_parameters():
                if "lora_B" in name:
                    p.copy_(torch.full_like(p, 0.3))
    return wrapped


FAMILIES = ["olmo2", "llama"]


# ----- the index convention (L4), model-agnostic -----------------------------------------------------


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("wrapped", [False, True])
def test_hidden_state_indices_follow_the_l4_convention(family, wrapped):
    model = tiny(family, lora=wrapped, b_nonzero=wrapped)
    base = rp.base_model(model)
    captured = {}
    hooks = [base.model.embed_tokens.register_forward_hook(lambda m, i, o: captured.__setitem__("embed", o))]
    for k, layer in enumerate(base.model.layers):
        hooks.append(layer.register_forward_hook(lambda m, i, o, k=k: captured.__setitem__(k, o[0] if isinstance(o, tuple) else o)))
    ids = torch.tensor([[5, 6, 7, 8, 9, 10]])
    try:
        ctx = model.disable_adapter() if wrapped else torch.no_grad()
        with torch.no_grad(), ctx:
            hs = model(input_ids=ids, output_hidden_states=True).hidden_states
    finally:
        for h in hooks:
            h.remove()
    lay = rp.layout(model)
    assert lay["n_layers"] == N_LAYERS and lay["hidden_size"] == 32 and len(hs) == N_LAYERS + 1
    assert torch.equal(hs[0], captured["embed"])
    for i in range(1, N_LAYERS):
        assert torch.equal(hs[i], captured[i - 1])
        assert rp.block_output_index(i - 1, N_LAYERS) == i
    assert torch.equal(hs[N_LAYERS], base.model.norm(captured[N_LAYERS - 1]))
    assert not torch.equal(hs[N_LAYERS], captured[N_LAYERS - 1])
    assert rp.block_output_index(N_LAYERS - 1, N_LAYERS) == N_LAYERS
    if wrapped:                                             # the adapter disabled gives the plain model's states
        plain = tiny(family)
        with torch.no_grad():
            hp = plain(input_ids=ids, output_hidden_states=True).hidden_states
        assert all(torch.equal(a, b) for a, b in zip(hs, hp))


def test_block_index_bounds():
    with pytest.raises(s1.Refusal):
        rp.block_output_index(4, 4)


# ----- reads, anchor means and CAS -------------------------------------------------------------------


def test_positions_of_the_four_reads():
    assert rp.positions((11, 12, 13, 21, 22, 99), 3, 99) == {"a": 5, "b": 4, "c": (3, 5), "d": 2}
    with pytest.raises(s1.Refusal):
        rp.positions((11, 12, 13, 21, 22, 98), 3, 99)                      # does not end with the end-of-turn id
    with pytest.raises(s1.Refusal):
        rp.positions((11, 12, 99), 2, 99)                                   # no response token


@pytest.mark.parametrize("family", FAMILIES)
def test_read_states_take_the_stated_positions(family):
    model = tiny(family)
    ids, n_prompt, eos = (5, 6, 7, 8, 9, 10, 99), 3, 99
    states = rp.read_states(model, ids, n_prompt, eos, "cpu", N_LAYERS)
    with torch.no_grad():
        hs = model(input_ids=torch.tensor([list(ids)]), output_hidden_states=True).hidden_states
    assert len(states) == N_LAYERS + 1
    for i, s in enumerate(states):
        h = hs[i][0].to(torch.float64)
        assert s["a"].dtype == torch.float64
        assert torch.equal(s["a"], h[6]) and torch.equal(s["b"], h[5]) and torch.equal(s["d"], h[2])
        assert torch.equal(s["c"], h[3:6].mean(dim=0))
    with pytest.raises(s1.Refusal):
        rp.read_states(model, ids, n_prompt, eos, "cpu", N_LAYERS + 1)      # a wrong layer count refuses


def test_anchor_means_sum_in_file_order():
    big = torch.tensor([1e16], dtype=torch.float64)
    one = torch.tensor([1.0], dtype=torch.float64)
    states = [[{r: big for r in rp.READS}], [{r: one for r in rp.READS}], [{r: -big for r in rp.READS}]]
    means = rp.anchor_means(states)
    assert means[0]["a"].item() == ((big + one) - big).item() / 3 == 0.0      # another order would give 1/3
    states2 = [states[0], states[2], states[1]]
    assert rp.anchor_means(states2)[0]["a"].item() == 1.0 / 3


def test_cas_bounds_scale_and_extremes():
    g = torch.Generator().manual_seed(3)
    h = [torch.randn(8, generator=g, dtype=torch.float64) + 1.0 for _ in range(6)]
    s = [torch.randn(8, generator=g, dtype=torch.float64) - 1.0 for _ in range(6)]
    v = torch.randn(8, generator=g, dtype=torch.float64)
    value = rp.cas(h, s, v)
    assert 0.0 <= value <= 1.0
    assert rp.cas(h, s, 7.5 * v) == pytest.approx(value, rel=1e-12)
    sep_h = [torch.tensor([1.0, 0.0], dtype=torch.float64) for _ in range(3)]
    sep_s = [torch.tensor([-1.0, 0.0], dtype=torch.float64) for _ in range(3)]
    assert rp.cas(sep_h, sep_s, torch.tensor([1.0, 0.0], dtype=torch.float64)) == pytest.approx(1.0)
    assert rp.cas(sep_h, sep_h, torch.tensor([1.0, 0.0], dtype=torch.float64)) is None   # a constant: no spread
    mixed_h = [torch.tensor([1.0, 0.0]), torch.tensor([-1.0, 0.0])]
    assert rp.cas([x.double() for x in mixed_h], [x.double() for x in mixed_h], torch.tensor([1.0, 0.0]).double()) == 0.0


def test_cas_uses_z_scored_states():
    """A direction that mixes two dimensions of very different scales: z-scoring changes CAS (0.4 here; 0.094 on raw
    states). An axis-aligned direction could not show it (CAS along one axis ignores that axis's scale)."""
    h = [torch.tensor(v, dtype=torch.float64) for v in ([10.0, 1.0], [30.0, 1.2], [20.0, 1.1])]
    s = [torch.tensor(v, dtype=torch.float64) for v in ([25.0, 0.9], [5.0, 0.7], [15.0, 0.8])]
    v = torch.tensor([1.0, 1.0], dtype=torch.float64)
    x = torch.stack(h + s)
    z = (x - x.mean(0)) / x.std(0, correction=0)
    zh, zs, grand = z[:len(h)], z[len(h):], z.mean(0)
    inter = sum(len(c) * float(torch.dot(c.mean(0) - grand, v)) ** 2 for c in (zh, zs))
    intra = sum(float(((c - c.mean(0)) @ v).pow(2).sum()) for c in (zh, zs))
    assert rp.cas(h, s, v) == pytest.approx(inter / (inter + intra), rel=1e-12) == pytest.approx(0.4, rel=1e-12)


# ----- the pass on the engine's fixture env -----------------------------------------------------------


def load_gate_c():
    spec = importlib.util.spec_from_file_location("pinned_gate_c_representation", ENGINE_ROOT / "scripts" / "gate_c_representation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    from experiments.safety_selection.prepare import load_prepared

    root = tmp_path_factory.mktemp("rp")
    prepared_dir, sha = sfx.prepare_dir(root / "prepared")
    view = load_prepared(prepared_dir, sha, banks=("dev",))
    base = sfx.recipe()
    rows = [view.train_rows[r] for r in sorted(view.train_rows)]
    doc = {"kind": "safety-selection anchor bank", "version": 1,
           "model": {"repo_id": base["model"]["repo_id"], "revision": base["model"]["revision"]},
           "harmful": [{"anchor_id": f"h-{k}", **{f: q[f] for f in FIELDS}} for k, q in enumerate(view.query_rows)],
           "safe": [{"anchor_id": f"s-{k}", **{f: r[f] for f in FIELDS}} for k, r in enumerate(rows[:3])],
           "counts": {"harmful": len(view.query_rows), "safe": 3}, "provenance": {"fixture": True}}
    data = canonical_json(doc)
    anchors = root / "anchors.json"
    anchors.write_bytes(data)
    recipe_doc = sfx.recipe(**{"attribution.query_bank": "anchors-" + hashlib.sha256(data).hexdigest()})
    recipe = root / "recipe.json"
    recipe.write_text(json.dumps(recipe_doc))
    groups = sorted(view.groups["dev"])
    texts = [t for name in ("harmful", "safe") for a in doc[name] for t in (a["prompt"], a["response"])] + \
        [t for gid in groups for rid in view.groups["dev"][gid] for t in (view.train_rows[rid]["prompt"],
                                                                         view.train_rows[rid]["response"])]
    settings = copy.deepcopy(json.loads(rp.SETTINGS_PATH.read_bytes()))
    settings["pins"] = {"recipe_sha256": config_sha256(recipe_doc),
                        "model": {"repo_id": recipe_doc["model"]["repo_id"], "revision": recipe_doc["model"]["revision"]},
                        "anchor_bank_sha256": hashlib.sha256(data).hexdigest(), "prepared_manifest_sha256": sha}
    return type("Env", (), dict(root=root, prepared=prepared_dir, view=view, anchors=anchors, recipe=recipe,
                                groups=groups, texts=[t for t in texts if len(t) > 3], settings=settings))


def loaders_with(model_fn):
    """The engine's fixture loaders with another tiny policy model (the fixture codec is kept)."""
    from experiments.safety_selection import engine as en
    from experiments.safety_selection.loaders import Policy

    base = sfx.fixture_loaders()

    def policy(recipe_, ledger):
        with ledger.stage("load_policy"):
            model = model_fn()
        return Policy(model, en.lora_parameters(model), sfx.fixture_codec(), "cpu", {"fixture": sfx.FIXTURE})
    return dataclasses.replace(base, policy=policy)


def run(env, loaders=None, pools=(), score_units=True, settings=None):
    return rp.run(env.prepared, env.recipe, env.anchors, loaders or sfx.fixture_loaders(), settings or env.settings,
                  "e" * 64, list(pools), score_units)


@pytest.fixture(scope="module")
def first(env):
    return {"files": None}


def files_of(env, first):
    if first["files"] is None:
        first["files"] = run(env)
    return first["files"]


def test_gate_c_is_reproduced_byte_for_byte(env, first):
    pinned = load_gate_c().run(env.prepared, env.recipe, env.anchors, env.groups, env.root / "gate-c",
                               sfx.fixture_loaders())
    summary = json.loads(files_of(env, first)[rp.SUMMARY_FILE])
    assert canonical_json(summary["gate_c"]["groups"]) == canonical_json(pinned["groups"])
    assert summary["gate_c"]["index"] == summary["layout"]["n_layers"]


@pytest.mark.parametrize("family", FAMILIES)
def test_the_pass_is_model_agnostic_and_reproduces_gate_c_on_each_family(env, family):
    loaders = loaders_with(lambda: tiny(family, lora=True))
    files = run(env, loaders)
    summary = json.loads(files[rp.SUMMARY_FILE])
    assert summary["layout"]["n_layers"] == N_LAYERS and summary["layout"]["model_type"] in ("olmo2", "llama")
    lines = [json.loads(l) for l in files[rp.ROWS_FILE].splitlines()]
    assert all(len(l["cos_harmful"]) == N_LAYERS + 1 and len(l["cos_harmful"][0]) == 4 for l in lines)
    assert len(summary["datashield"]["cas"]) == N_LAYERS + 1
    pinned = load_gate_c().run(env.prepared, env.recipe, env.anchors, env.groups, env.root / f"gate-c-{family}",
                               loaders_with(lambda: tiny(family, lora=True)))
    assert canonical_json(summary["gate_c"]["groups"]) == canonical_json(pinned["groups"])


def test_the_adapter_is_disabled(env):
    zero = run(env, loaders_with(lambda: tiny("olmo2", lora=True)))
    nonzero = run(env, loaders_with(lambda: tiny("olmo2", lora=True, b_nonzero=True)))
    assert zero[rp.ROWS_FILE] == nonzero[rp.ROWS_FILE]
    flags = []
    real = torch.nn.Module.__call__

    def spy(self, *args, **kwargs):
        if kwargs.get("output_hidden_states"):
            flags.append(all(m.disable_adapters for m in self.modules() if hasattr(m, "disable_adapters")))
        return real(self, *args, **kwargs)
    torch.nn.Module.__call__ = spy
    try:
        run(env)
    finally:
        torch.nn.Module.__call__ = real
    assert flags and all(flags)


def test_rows_hold_every_feature_and_css_matches_its_definition(env, first):
    files = files_of(env, first)
    lines = [json.loads(l) for l in files[rp.ROWS_FILE].splitlines()]
    summary = json.loads(files[rp.SUMMARY_FILE])
    assert len(lines) == sum(len(env.view.groups["dev"][g]) for g in env.groups)
    assert {l["source"] for l in lines} == {"dev"} and all(l["unit"] in env.groups for l in lines)
    n = summary["layout"]["n_layers"]
    b = rp.READS.index("b")
    for gid in env.groups:
        mine = [l for l in lines if l["unit"] == gid]
        assert summary["gate_c"]["groups"][gid]["rows"] == len(mine)
    assert all(-1.0 - 1e-12 <= x <= 1.0 + 1e-12 for l in lines for row in l["cos_harmful"] for x in row)
    assert all(len(l["css"]) == n + 1 for l in lines)
    assert all(0.0 <= c <= 1.0 for c in summary["datashield"]["cas"] if c is not None)


def test_deterministic_and_text_free(env, first):
    a = files_of(env, first)
    b = run(env)
    assert a[rp.ROWS_FILE] == b[rp.ROWS_FILE]
    sa, sb = json.loads(a[rp.SUMMARY_FILE]), json.loads(b[rp.SUMMARY_FILE])
    sa.pop("costs"), sb.pop("costs")
    assert sa == sb
    for data in a.values():
        for t in env.texts:
            assert t.encode() not in data


def pool_file(tmp_path, items, name="s3sub"):
    doc = {"kind": rp.POOL_KIND, "version": 1, "name": name, "items": items}
    path = tmp_path / f"{name}.json"
    path.write_bytes(canonical_json(doc))
    return path, sha256_file(path)


def test_pools_are_scored_and_refusals_counted(env, tmp_path):
    items = [{"id": "p-1", "prompt": "Synthetic question one about rivers?", "response": "Synthetic answer about deltas."},
             {"id": "p-2", "prompt": "Synthetic question two about hills?", "response": "Synthetic answer about slopes."},
             {"id": "p-3", "prompt": "Synthetic question three?", "response": ""}]
    path, digest = pool_file(tmp_path, items)
    files = run(env, pools=[(path, digest)], score_units=False)
    summary = json.loads(files[rp.SUMMARY_FILE])
    lines = [json.loads(l) for l in files[rp.ROWS_FILE].splitlines()]
    assert [l["id"] for l in lines] == ["p-1", "p-2"] and all(l["source"] == "s3sub" and l["unit"] is None for l in lines)
    assert summary["pools"][0]["refused_by_reason"] == {"NoTargets": 1} and summary["gate_c"]["groups"] == {}
    for data in files.values():
        assert b"Synthetic question" not in data and b"Synthetic answer" not in data
    with pytest.raises(s1.Refusal, match="hashes to"):
        run(env, pools=[(path, "0" * 64)], score_units=False)
    rid = sorted(env.view.groups["dev"][env.groups[0]])[0]
    clash, clash_sha = pool_file(tmp_path, [{"id": rid, "prompt": "Synthetic?", "response": "Synthetic."}], "clash")
    with pytest.raises(s1.Refusal, match="repeats a scored id"):
        run(env, pools=[(clash, clash_sha)])


@pytest.mark.parametrize("pin,value,match", [
    ("recipe_sha256", "0" * 64, "recipe hashes"), ("anchor_bank_sha256", "0" * 64, "anchor bank"),
    ("prepared_manifest_sha256", "0" * 64, "prepared manifest"), ("model", {"repo_id": "x", "revision": "y"}, "another model"),
])
def test_the_pins_refuse(env, pin, value, match):
    settings = copy.deepcopy(env.settings)
    settings["pins"][pin] = value
    with pytest.raises(s1.Refusal, match=match):
        run(env, settings=settings)


def test_another_transformers_version_refuses(env, monkeypatch):
    monkeypatch.setattr(rp, "installed_transformers_version", lambda: "4.57.0")
    with pytest.raises(s1.Refusal, match="transformers is"):
        run(env)


def test_the_settings_are_pinned_and_state_the_conventions():
    data = rp.SETTINGS_PATH.read_bytes()
    assert sha256_bytes(data) == rp.SETTINGS_SHA256 == "a555fd899bd2b5caf8d68fb62578ed2e943977341b5bf2dc2d688dcbd034600b"
    doc = s1.check_settings(json.loads(data), "representation_pass")
    assert doc["transformers_version"] == "4.56.2" and doc["label_entries"] == {}
    assert doc["pins"]["recipe_sha256"] == "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"
    assert doc["pins"]["anchor_bank_sha256"] == "2cf9633613e235d1f33deee3530c3e53b037845bd3979568887742457c1801ed"
    assert doc["index_convention"].startswith("index 0 = the embedding output; index i (1 <= i <= n - 1)")
    assert set(doc["reads"]) == set(rp.READS)


def test_css_and_cosines_match_an_independent_recomputation(env, first):
    """One dev row, recomputed from the encodings: its css at every index and its read (a) and (b) cosines."""
    from experiments.safety_selection import runner
    from experiments.safety_selection.config import load_recipe
    from experiments.safety_selection.jobs import read_anchor_bank

    recipe = load_recipe(env.recipe)
    anchors = read_anchor_bank(env.anchors, recipe["attribution"]["query_bank"], recipe)
    codec = sfx.fixture_codec()
    model = sfx.tiny_lora_model()
    sets = runner.anchor_examples(codec, anchors, recipe)
    rid = sorted(env.view.groups["dev"][env.groups[1]])[2]
    ex = runner._verified_example(codec, rid, env.view.train_rows[rid], recipe)
    lines = {json.loads(l)["id"]: json.loads(l) for l in files_of(env, first)[rp.ROWS_FILE].splitlines()}
    with torch.no_grad(), model.disable_adapter():
        n = rp.layout(model)["n_layers"]
        states = {s: [rp.read_states(model, e.input_ids, e.n_prompt, codec.eos_id, "cpu", n) for e in sets[s]] for s in ("harmful", "safe")}
        row = rp.read_states(model, ex.input_ids, ex.n_prompt, codec.eos_id, "cpu", n)
    for i in range(n + 1):
        mean_h = sum((st[i]["c"] for st in states["harmful"][1:]), states["harmful"][0][i]["c"]) / len(states["harmful"])
        mean_s = sum((st[i]["c"] for st in states["safe"][1:]), states["safe"][0][i]["c"]) / len(states["safe"])
        v = mean_h - mean_s
        expected = float(torch.dot(row[i]["c"] - row[i]["d"], v / v.norm()))
        assert lines[rid]["css"][i] == pytest.approx(expected, rel=1e-9, abs=1e-12)
        for r in ("a", "b"):
            mh = sum((st[i][r] for st in states["harmful"][1:]), states["harmful"][0][i][r]) / len(states["harmful"])
            got = lines[rid]["cos_harmful"][i][rp.READS.index(r)]
            assert got == pytest.approx(float(torch.nn.functional.cosine_similarity(row[i][r], mh, dim=0)), rel=1e-12)


# ----- batch 2 rev 2: the verifier's tests (independent recomputation, > 16 layers, final norm, forwards) --


def _independent_states(model, ex):
    """Reads (a)-(d) at every index from one unbatched forward, by position arithmetic only (no rp code)."""
    hs = model(input_ids=torch.tensor([list(ex.input_ids)]), output_hidden_states=True).hidden_states
    L, p = len(ex.input_ids), ex.n_prompt
    return [{"a": h[0, L - 1].double(), "b": h[0, L - 2].double(), "c": h[0, p:L - 1].double().mean(0),
             "d": h[0, p - 1].double()} for h in hs]


def test_v_every_read_cosine_and_cas_match_an_independent_recomputation(env, first):
    from experiments.safety_selection import runner
    from experiments.safety_selection.config import load_recipe
    from experiments.safety_selection.jobs import read_anchor_bank

    recipe = load_recipe(env.recipe)
    anchors = read_anchor_bank(env.anchors, recipe["attribution"]["query_bank"], recipe)
    codec = sfx.fixture_codec()
    model = sfx.tiny_lora_model()
    sets = runner.anchor_examples(codec, anchors, recipe)
    files = files_of(env, first)
    lines = {json.loads(l)["id"]: json.loads(l) for l in files[rp.ROWS_FILE].splitlines()}
    summary = json.loads(files[rp.SUMMARY_FILE])
    rids = [sorted(env.view.groups["dev"][g])[0] for g in env.groups[:2]]
    with torch.no_grad(), model.disable_adapter():
        st = {s: [_independent_states(model, e) for e in sets[s]] for s in ("harmful", "safe")}
        rows = {rid: _independent_states(model, runner._verified_example(codec, rid, env.view.train_rows[rid], recipe))
                for rid in rids}
    n = len(st["harmful"][0]) - 1
    cos = torch.nn.functional.cosine_similarity
    for i in range(n + 1):
        mean = {s: {r: sum((x[i][r] for x in st[s][1:]), st[s][0][i][r]) / len(st[s]) for r in "abcd"} for s in st}
        for rid, row in rows.items():
            for k, r in enumerate("abcd"):                                  # the documented column order
                assert lines[rid]["cos_harmful"][i][k] == pytest.approx(float(cos(row[i][r], mean["harmful"][r], dim=0)), rel=1e-9, abs=1e-12)
                assert lines[rid]["cos_safe"][i][k] == pytest.approx(float(cos(row[i][r], mean["safe"][r], dim=0)), rel=1e-9, abs=1e-12)
        v = mean["harmful"]["c"] - mean["safe"]["c"]
        x = torch.stack([s[i]["b"] for s in st["harmful"]] + [s[i]["b"] for s in st["safe"]])
        mu, sd = x.mean(0), x.std(0, correction=0)
        z = torch.where(sd > 0, (x - mu) / torch.where(sd > 0, sd, torch.ones_like(sd)), torch.zeros_like(x))
        nh = len(st["harmful"])
        zh, zs, g = z[:nh], z[nh:], z.mean(0)
        inter = sum(len(c) * float(torch.dot(c.mean(0) - g, v)) ** 2 for c in (zh, zs))
        intra = sum(float(((c - c.mean(0)) @ v).pow(2).sum()) for c in (zh, zs))
        expected = inter / (inter + intra) if inter + intra > 0 and float(v.norm()) > 0 else None
        got = summary["datashield"]["cas"][i]
        assert (got is None) == (expected is None)
        if got is not None:
            assert got == pytest.approx(expected, rel=1e-9, abs=1e-12)


def _deep_llama(n_layers=18):
    config = transformers.LlamaConfig(vocab_size=sfx.VOCAB, hidden_size=16, intermediate_size=32, num_hidden_layers=n_layers,
                                      num_attention_heads=2, num_key_value_heads=1, max_position_embeddings=512,
                                      tie_word_embeddings=False, attn_implementation="eager", pad_token_id=0,
                                      bos_token_id=1, eos_token_id=1)
    torch.manual_seed(1)
    model = transformers.LlamaForCausalLM(config).float().eval()
    with torch.no_grad():
        model.model.norm.weight.copy_(torch.linspace(0.5, 1.5, 16))
    return peft.get_peft_model(model, peft.LoraConfig(r=2, lora_alpha=4, lora_dropout=0.0, target_modules=["q_proj", "v_proj"],
                                                       bias="none", task_type="CAUSAL_LM"))


def test_v_the_pass_handles_more_than_16_layers(env):
    files = run(env, loaders_with(_deep_llama))
    summary = json.loads(files[rp.SUMMARY_FILE])
    assert summary["layout"]["n_layers"] == 18 and summary["gate_c"]["index"] == 18
    assert len(summary["datashield"]["cas"]) == 19
    pinned = load_gate_c().run(env.prepared, env.recipe, env.anchors, env.groups, env.root / "gate-c-deep",
                               loaders_with(_deep_llama))
    assert canonical_json(summary["gate_c"]["groups"]) == canonical_json(pinned["groups"])


@pytest.mark.parametrize("family,norm", [("olmo2", "Olmo2RMSNorm"), ("llama", "LlamaRMSNorm")])
def test_v_layout_names_the_final_norm_and_refuses_a_mismatch(family, norm):
    assert rp.layout(tiny(family))["final_norm"] == norm
    model = tiny(family)
    model.config.num_hidden_layers = N_LAYERS + 1
    with pytest.raises(s1.Refusal):
        rp.layout(model)
    model = tiny(family)
    del model.model.norm
    with pytest.raises(s1.Refusal):
        rp.layout(model)


def test_v_every_forward_is_one_unpadded_row(env):
    shapes = []
    real = torch.nn.Module.__call__

    def spy(self, *args, **kwargs):
        if kwargs.get("output_hidden_states") and kwargs.get("input_ids") is not None:
            mask = kwargs.get("attention_mask")
            shapes.append((tuple(kwargs["input_ids"].shape), mask is None or bool(mask.all())))
        return real(self, *args, **kwargs)
    torch.nn.Module.__call__ = spy
    try:
        run(env)
    finally:
        torch.nn.Module.__call__ = real
    assert shapes and all(s[0][0] == 1 and s[1] for s in shapes)


def test_fc_every_hidden_state_forward_runs_in_eval_mode(env):
    modes = []
    real = torch.nn.Module.__call__

    def spy(self, *args, **kwargs):
        if kwargs.get("output_hidden_states"):
            modes.append(self.training)
        return real(self, *args, **kwargs)
    torch.nn.Module.__call__ = spy
    try:
        run(env)
    finally:
        torch.nn.Module.__call__ = real
    assert modes and not any(modes)
