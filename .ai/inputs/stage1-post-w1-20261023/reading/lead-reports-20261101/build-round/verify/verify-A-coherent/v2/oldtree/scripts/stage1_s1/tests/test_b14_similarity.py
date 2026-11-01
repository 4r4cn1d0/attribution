"""B14 part 1, the similarity pass (ENGINEERING FIXTURES on CPU: the engine's tiny random Qwen2 + LoRA policy and its
byte codec, and a tiny random OLMo-2 built locally; nothing is downloaded). CUDA and the real OLMo-2-1B are UNTESTED."""

from __future__ import annotations

import dataclasses
import json
import math
import os
import stat

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import b14_fixtures as bf  # noqa: E402
import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection.common import sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1 import overlap_similarity as sim  # noqa: E402

PINNED = sim.SETTINGS_SHA256


def stable(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "costs"}


def run(env: bf.Env, out_name: str, loaders=None, settings=None, given=None):
    return sim.run(env.prepared, env.recipe, env.given() if given is None else given, env.root / out_name,
                   loaders or fx.fixture_loaders(), env.settings if settings is None else settings, PINNED)


class LazyEnv:
    """bf.Env, built at the first attribute read inside a test body: under a mutant, a failure there is a test
    failure, never a fixture error (the mutation runner counts errors as invalid runs)."""

    def __init__(self, root):
        self._root, self._env = root, None

    def __getattr__(self, name):
        if self._env is None:
            self._env = bf.Env(self._root)
        return getattr(self._env, name)


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    return LazyEnv(tmp_path_factory.mktemp("b14sim") / "env")


@pytest.fixture(scope="module")
def first(env):
    """The first pass, run once inside the first test body that asks for it (an exception is re-raised in each)."""
    cache: dict = {}

    def get():
        if "value" not in cache:
            try:
                cache["value"] = run(env, "out-first")
            except Exception as exc:                  # noqa: BLE001 - re-raised below, in each test that asks
                cache["value"] = exc
        if isinstance(cache["value"], Exception):
            raise cache["value"]
        return cache["value"]
    return get


def base_vectors(env: bf.Env, texts_ids: list[list[int]], index: int) -> list:
    """The fixture policy's base-model states, by a direct forward (the reference the pass must equal)."""
    model = fx.tiny_lora_model()
    model.eval()
    out = []
    with torch.no_grad(), model.disable_adapter():
        for ids in texts_ids:
            hidden = model(input_ids=torch.tensor([ids]), output_hidden_states=True).hidden_states
            out.append([float(x) for x in hidden[index][0, len(ids) - 1].to(torch.float64)])
    return out


def py_cos(a: list[float], b: list[float]) -> float:
    dot = math.fsum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(math.fsum(x * x for x in a)) * math.sqrt(math.fsum(y * y for y in b)))


def test_s_max_is_the_largest_cosine_of_the_last_prompt_state_at_the_pinned_index(env, first):
    doc, _ = first()
    codec = fx.fixture_codec()
    harm = sorted((i for i in env.items if i["kind"] == "harm"), key=lambda i: i["prompt_id"])
    e_ids = [sim.encode_eval(codec, item, 400) for item in harm]
    e_vec = base_vectors(env, e_ids, 2)
    for name, rows in env.rows.items():
        a_ids = [sim.encode_added(codec, rid, p, r, fx.recipe()) for rid, p, r in rows]
        a_vec = base_vectors(env, a_ids, 2)
        per = doc["add_sets"][name]["per_prompt"]
        assert sorted(per) == [i["prompt_id"] for i in harm]
        for item, ev in zip(harm, e_vec):
            cosines = [py_cos(ev, av) for av in a_vec]
            assert per[item["prompt_id"]]["s_max"] == pytest.approx(max(cosines), abs=1e-12)
            assert per[item["prompt_id"]]["nearest"] == rows[cosines.index(max(cosines))][0]
    # the summary block is consistent with the per-prompt values
    block = doc["add_sets"]["S1"]
    values = [v["s_max"] for v in block["per_prompt"].values()]
    assert block["summary"]["min"] == min(values) and block["summary"]["max"] == max(values)
    assert sum(block["summary"]["nearest_counts"].values()) == len(values)


def test_other_indices_and_positions_give_other_values(env, first):
    """The pinned cell is distinguishable: index 1, or the position len - 2, give other S values."""
    doc, _ = first()
    codec = fx.fixture_codec()
    harm = sorted((i for i in env.items if i["kind"] == "harm"), key=lambda i: i["prompt_id"])
    e_ids = [sim.encode_eval(codec, item, 400) for item in harm]
    a_ids = [sim.encode_added(codec, rid, p, r, fx.recipe()) for rid, p, r in env.rows["S1"]]
    for index in (0, 1):
        e_vec, a_vec = base_vectors(env, e_ids, index), base_vectors(env, a_ids, index)
        other = [max(py_cos(e, a) for a in a_vec) for e in e_vec]
        pinned = [doc["add_sets"]["S1"]["per_prompt"][i["prompt_id"]]["s_max"] for i in harm]
        assert max(abs(x - y) for x, y in zip(other, pinned)) > 1e-6


def test_the_pass_is_deterministic_and_text_free(env, first):
    doc, data = first()
    again, _ = run(env, "out-again")
    assert stable(again) == stable(doc)
    written = (env.root / "out-first" / sim.OUTPUT).read_bytes()
    assert written == data and sha256_bytes(written) == sha256_bytes(data)
    assert not [t for t in bf.SENTINELS if t.encode() in written]
    assert doc["provenance"]["settings_sha256"] == PINNED
    assert set(doc["provenance"]["inputs"]) == {"prepared/manifest.json", "prepared/banks/dev.jsonl", "recipe",
                                                "add/S1", "add/S3", "add/S4"}
    assert doc["eval"]["prompts"] == 12 and doc["eval"]["kinds"] == ["harm"]
    assert doc["model"]["hidden_state_index"] == 2 and doc["model"]["n_layers"] == 2
    assert doc["add_sets"]["S1"]["arm"] == "edit-" + env.edits["S1"][1]


def test_the_adapter_is_disabled(env, first):
    """A policy whose LoRA B matrices are non-zero gives the same S as the zero adapter (the base model's states),
    while its adapter-enabled states differ."""
    doc, _ = first()
    loaders = fx.fixture_loaders()
    original = loaders.policy

    def perturbed(recipe, ledger):
        policy = original(recipe, ledger)
        with torch.no_grad():
            for name, p in policy.model.named_parameters():
                if "lora_B" in name:
                    p.copy_(torch.randn_like(p))
        return policy

    loaders = dataclasses.replace(loaders, policy=perturbed)
    moved, _ = run(env, "out-perturbed", loaders=loaders)
    assert stable(moved) == stable(doc)
    probe = perturbed(fx.recipe(), type("L", (), {"stage": staticmethod(lambda *a, **k: _Null())})())
    ids = torch.tensor([sim.encode_eval(fx.fixture_codec(), env.items[0], 400)])
    with torch.no_grad():
        on = probe.model(input_ids=ids, output_hidden_states=True).hidden_states[2]
        with probe.model.disable_adapter():
            off = probe.model(input_ids=ids, output_hidden_states=True).hidden_states[2]
    assert not torch.equal(on, off)


class _Null:
    def __enter__(self):
        return {}

    def __exit__(self, *exc):
        return False


def test_an_added_rows_prompt_state_equals_its_training_state(env):
    """Causal masking: the state at the last prompt position does not depend on the response that follows."""
    from experiments.safety_selection.textproc import encode_train

    codec = fx.fixture_codec()
    model = fx.tiny_lora_model()
    model.eval()
    for rid, prompt, response in env.rows["S1"]:
        example = encode_train(codec, rid, prompt, response, 256)
        prompt_ids = sim.encode_added(codec, rid, prompt, response, fx.recipe())
        with torch.no_grad(), model.disable_adapter():
            alone = sim.prompt_vector(model, prompt_ids, 2, 2, "cpu")
            full = model(input_ids=torch.tensor([list(example.input_ids)]), output_hidden_states=True).hidden_states
        in_row = full[2][0, example.n_prompt - 1].to(torch.float64)
        assert torch.allclose(alone, in_row, atol=1e-5, rtol=0)


def test_nearest_ties_go_to_the_smallest_row_id(env, tmp_path):
    """Two prompts, each added twice (rows a and b share a prompt, so their cosines are exactly equal): every
    nearest row is an a row, the smaller id."""
    x, y = bf.add_prompt(40), bf.add_prompt(41)
    rows = [("add-a1", x, bf.add_response(1)), ("add-b1", x, bf.add_response(2)),
            ("add-a2", y, bf.add_response(3)), ("add-b2", y, bf.add_response(4))]
    edit, digest = bf.write_edit(tmp_path / "twin.edit.json", "twin", env.manifest, rows)
    doc, _ = sim.run(env.prepared, env.recipe, [("S1", edit, digest)], tmp_path / "out", fx.fixture_loaders(),
                     env.settings, PINNED)
    nearest = {v["nearest"] for v in doc["add_sets"]["S1"]["per_prompt"].values()}
    assert nearest and nearest <= {"add-a1", "add-a2"}
    assert doc["add_sets"]["S1"]["summary"]["nearest_counts"]["add-b1"] == 0


def test_only_the_dev_bank_is_read(tmp_path):
    env = bf.Env(tmp_path / "e", with_other_banks=True)
    locked = [env.prepared / "banks" / "selector.jsonl", env.prepared / "hidden" / "hidden.jsonl"]
    try:
        for path in locked:
            os.chmod(path, 0)
        doc, _ = run(env, "out")
        assert doc["eval"]["prompts"] == 12
    finally:
        for path in locked:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def test_the_kind_filter_keeps_only_harm_prompts(env, first):
    doc, _ = first()
    harm = sorted(i["prompt_id"] for i in env.items if i["kind"] == "harm")
    assert doc["eval"]["prompt_ids"] == harm
    assert all(not pid.startswith("p-0000000000000f0") for pid in doc["eval"]["prompt_ids"])


# ----- refusals before the model loads -------------------------------------------------------------------------------


def _loads():
    count = []
    return count, fx.fixture_loaders(on_policy_load=lambda: count.append(1))


@pytest.mark.parametrize("case", ["manifest", "recipe", "edit_sha", "unknown_set", "twice", "twice_other_file",
                                  "same_file", "not_add",
                                  "row_count", "prompt_count", "transformers", "out_exists", "empty"])
def test_input_refusals_happen_before_any_model_load(env, tmp_path, case):
    count, loaders = _loads()
    settings = json.loads(json.dumps(env.settings))
    given = env.given()
    out = tmp_path / "out"
    if case == "manifest":
        settings["prepared_manifest_sha256"] = "1" * 64
    elif case == "recipe":
        settings["recipe_sha256"] = "1" * 64
    elif case == "edit_sha":
        given[0] = (given[0][0], given[0][1], "2" * 64)
    elif case == "unknown_set":
        given[0] = ("S9", *given[0][1:])
    elif case == "twice":
        given = [given[0], given[0]]
    elif case == "twice_other_file":
        given = [given[0], ("S1", *given[1][1:])]
    elif case == "same_file":
        given = [given[0], ("S3", *given[0][1:])]
    elif case == "not_add":
        path, digest = bf.write_edit(tmp_path / "comb.edit.json", "comb", env.manifest, env.rows["S1"],
                                     edit_kind="combined", remove=["r-0000000000000001"])
        given = [("S1", path, digest)]
    elif case == "row_count":
        settings["add_sets"]["rows_each"] = 5
    elif case == "prompt_count":
        settings["eval"]["prompts"] = 13
    elif case == "transformers":
        settings["transformers_version"] = "0.0.0"
    elif case == "out_exists":
        out.mkdir()
    elif case == "empty":
        given = []
    with pytest.raises(s1.Refusal):
        sim.run(env.prepared, env.recipe, given, out, loaders, settings, PINNED)
    assert count == []
    assert case == "out_exists" or not out.exists()


def test_an_added_row_that_training_would_refuse_refuses(env, tmp_path):
    """encode_train runs on every added row: its prompt alone encodes, but prompt + response is longer than the
    fixture recipe's max_train_tokens (256; the byte codec), so the pass refuses (after the load; no record)."""
    long_response = "Synthetic long refusal: " + "no, I will not. " * 20
    bf.SENTINELS.append(long_response)
    rows = bf.add_rows(range(20, 24))
    rows[1] = (rows[1][0], rows[1][1], long_response)
    path, digest = bf.write_edit(tmp_path / "long.edit.json", "long", env.manifest, rows)
    with pytest.raises(s1.Refusal, match=f"added row {rows[1][0]} is refused by the codec \\(TooLong\\)"):
        sim.run(env.prepared, env.recipe, [("S1", path, digest)], tmp_path / "out", fx.fixture_loaders(),
                env.settings, PINNED)
    assert not (tmp_path / "out" / sim.OUTPUT).exists()


def test_the_record_lists_the_prompts_sorted_whatever_the_bank_order(tmp_path):
    """The engine writes the bank sorted by prompt id; the pass sorts again, so a bank in another order gives the same
    sorted prompt ids (the strata refuse unsorted ids)."""
    env = bf.Env(tmp_path / "e", reverse_bank=True)
    bank = (env.prepared / "banks" / "dev.jsonl").read_bytes().splitlines()
    assert json.loads(bank[0])["prompt_id"] > json.loads(bank[-1])["prompt_id"]
    doc, _ = run(env, "out")
    harm = sorted(i["prompt_id"] for i in env.items if i["kind"] == "harm")
    assert doc["eval"]["prompt_ids"] == harm and list(doc["add_sets"]["S1"]["per_prompt"]) == harm


def test_the_setup_peak_takes_the_ledger_stages_cuda_peaks(tmp_path):
    """The engine's memory probe resets the CUDA peak at the end of each ledger stage (the model load is one), so the
    setup peak is the larger of the script's own read and the stages' recorded peaks; None off CUDA."""
    from experiments.safety_selection.ledger import LEDGER

    assert sim._setup_peak(None, tmp_path) is None and sim._setup_peak(40, tmp_path) == 40      # no ledger yet
    (tmp_path / LEDGER).write_text("\n".join(json.dumps(r) for r in [
        {"stage": "load_policy", "memory": {"cuda_peak_allocated_bytes": 900}}, {"stage": "x", "memory": {}},
        {"stage": "y", "memory": None}, {"stage": "z", "memory": {"cuda_peak_allocated_bytes": 500}}]) + "\n")
    assert sim._setup_peak(100, tmp_path) == 900 and sim._setup_peak(None, tmp_path) == 900
    assert sim._setup_peak(1000, tmp_path) == 1000
    cpu = tmp_path / "cpu"
    cpu.mkdir()
    (cpu / LEDGER).write_text(json.dumps({"stage": "load_policy", "memory": {"peak_rss_bytes": 7}}) + "\n")
    assert sim._setup_peak(None, cpu) is None


def test_the_pass_records_the_setup_peak_from_the_helper(env, tmp_path, monkeypatch, first):
    first()
    seen = []

    def fake(peak, out):
        seen.append((peak, out))
        return 12345
    monkeypatch.setattr(sim, "_setup_peak", fake)
    doc, _ = run(env, "out-peak")
    assert doc["costs"]["setup"]["peak_memory_bytes"] == 12345
    assert seen == [(None, env.root / "out-peak")]                     # CPU: the script's own read is None


def test_a_prompt_that_differs_from_the_token_audit_refuses(tmp_path):
    env = bf.Env(tmp_path / "e", bad_audit=f"p-{3:016x}")
    with pytest.raises(s1.Refusal, match="token audit"):
        run(env, "out")


def test_a_model_with_another_block_count_refuses(env, tmp_path):
    settings = bf.sim_settings(env.recipe_sha, env.manifest, n_layers=3, index=3)
    with pytest.raises(s1.Refusal, match="blocks"):
        sim.run(env.prepared, env.recipe, env.given(), tmp_path / "out", fx.fixture_loaders(), settings, PINNED)


def test_a_wrong_hidden_state_count_refuses():
    class Fake:
        def __call__(self, input_ids, output_hidden_states):
            return type("O", (), {"hidden_states": (torch.zeros(1, 3, 4),) * 2})()
    with pytest.raises(s1.Refusal, match="hidden states"):
        sim.prompt_vector(Fake(), [1, 2, 3], 1, 2, "cpu")


def test_cosine_table_refuses_a_zero_vector_and_matches_the_definition():
    a = [torch.tensor([1.0, 0.0], dtype=torch.float64), torch.tensor([3.0, 4.0], dtype=torch.float64)]
    b = [torch.tensor([0.0, 2.0], dtype=torch.float64)]
    assert sim.cosine_table(a, b) == [[0.0], [pytest.approx(0.8, abs=1e-15)]]
    with pytest.raises(s1.Refusal, match="norm 0"):
        sim.cosine_table(a, [torch.zeros(2, dtype=torch.float64)])
    with pytest.raises(s1.Refusal, match="not finite"):
        sim.cosine_table([torch.tensor([float("nan"), 1.0], dtype=torch.float64)], b)


def test_highest_takes_the_max_and_the_smallest_tied_id():
    table = [[0.1, 0.5, 0.5], [0.9, -0.2, 0.3]]
    out = sim.highest(table, ["p1", "p2"], ["add-c", "add-b", "add-a"])
    assert out == {"p1": {"s_max": 0.5, "nearest": "add-a"}, "p2": {"s_max": 0.9, "nearest": "add-c"}}


def test_text_in_the_record_refuses(tmp_path):
    """The final bytes are scanned: an added row id that holds an evaluation prompt's exact text is never written."""
    env = bf.Env(tmp_path / "e")
    rows = bf.add_rows(range(0, 4))
    rows[0] = ("add-" + env.items[0]["prompt"], rows[0][1], rows[0][2])
    path, digest = bf.write_edit(tmp_path / "leak.edit.json", "leak", env.manifest, rows)
    with pytest.raises(s1.Refusal, match="text values"):
        sim.run(env.prepared, env.recipe, [("S1", path, digest)], tmp_path / "out", fx.fixture_loaders(),
                env.settings, PINNED)
    assert not (tmp_path / "out" / sim.OUTPUT).exists()


def test_an_edit_that_is_not_a_pure_add_refuses(env, tmp_path, monkeypatch):
    """parse_edit already refuses remove and rewrite rows that the stub does not hold; the explicit kind check is
    tested on an edit object that parse_edit would return for a combined edit."""
    from experiments.safety_selection import edits

    real = edits.parse_edit

    def combined(data, prepared):
        edit = real(data, prepared)
        return dataclasses.replace(edit, document={**edit.document, "edit_kind": "combined"})

    monkeypatch.setattr(edits, "parse_edit", combined)
    count, loaders = _loads()
    with pytest.raises(s1.Refusal, match="pure add"):
        sim.run(env.prepared, env.recipe, env.given(["S1"]), tmp_path / "out", loaders, env.settings, PINNED)
    assert count == []


# ----- the index convention on a tiny OLMo-2 (the pinned index 16 is the final-norm output) ---------------------------


def tiny_olmo2():
    import peft
    import transformers

    torch.manual_seed(3)
    config = transformers.Olmo2Config(vocab_size=260, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                                      num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=512,
                                      tie_word_embeddings=False, attn_implementation="eager", pad_token_id=258,
                                      bos_token_id=None, eos_token_id=257)
    base = transformers.Olmo2ForCausalLM(config).float()
    return peft.get_peft_model(base, peft.LoraConfig(r=2, lora_alpha=4, lora_dropout=0.0, bias="none",
                                                     target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"))


def test_olmo2_index_n_is_the_final_norm_output_and_index_0_the_embeddings():
    model = tiny_olmo2()
    inner = model.get_base_model().model
    seen = {}
    hooks = [inner.norm.register_forward_hook(lambda m, i, o: seen.__setitem__("norm", o)),
             inner.layers[-1].register_forward_hook(
                 lambda m, i, o: seen.__setitem__("last", o[0] if isinstance(o, tuple) else o))]
    ids = [5, 6, 7, 8, 9]
    try:
        with torch.no_grad(), model.disable_adapter():
            hidden = model(input_ids=torch.tensor([ids]), output_hidden_states=True).hidden_states
            vector = sim.prompt_vector(model, ids, 2, 2, "cpu")
    finally:
        for h in hooks:
            h.remove()
    assert len(hidden) == 3 and sim.layout(model) == {"model_type": "olmo2", "n_layers": 2, "hidden_size": 32}
    assert torch.equal(hidden[2], seen["norm"]) and not torch.equal(hidden[2], seen["last"])
    assert torch.equal(hidden[0], inner.embed_tokens(torch.tensor([ids])))
    assert torch.equal(vector, seen["norm"][0, len(ids) - 1].to(torch.float64))


def test_the_pass_runs_on_a_tiny_olmo2_policy(env, tmp_path):
    from experiments.safety_selection import engine as en
    from experiments.safety_selection.loaders import Policy

    def policy(recipe, ledger):
        model = tiny_olmo2()
        return Policy(model, en.lora_parameters(model), fx.fixture_codec(), "cpu", {"fixture": "olmo2"})

    loaders = dataclasses.replace(fx.fixture_loaders(), policy=policy)
    doc, data = sim.run(env.prepared, env.recipe, env.given(["S1"]), tmp_path / "out", loaders, env.settings, PINNED)
    assert doc["model"]["model_type"] == "olmo2"
    assert len(doc["add_sets"]["S1"]["per_prompt"]) == 12
    assert not [t for t in bf.SENTINELS if t.encode() in data]


# ----- the command line (the real loaders swapped for the fixture's; CUDA is untested) ------------------------------


def test_the_command_line_writes_the_record_and_prints_no_text(env, tmp_path, monkeypatch, capsys):
    from experiments.safety_selection import loaders as engine_loaders

    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(env.settings))
    monkeypatch.setattr(sim, "SETTINGS_SHA256", sha256_bytes(settings_path.read_bytes()))
    monkeypatch.setattr(engine_loaders, "real_loaders", fx.fixture_loaders)
    argv = ["--prepared", str(env.prepared), "--recipe", str(env.recipe), "--out", str(tmp_path / "out"),
            "--settings", str(settings_path)]
    for name, path, digest in env.given():
        argv += ["--add-set", name, str(path), digest]
    assert sim.main(argv) == 0
    printed = capsys.readouterr()
    record = (tmp_path / "out" / sim.OUTPUT).read_bytes()
    assert sha256_bytes(record) in printed.out and "S4: 4 rows, 12 prompts" in printed.out
    assert not [t for t in bf.SENTINELS if t in printed.out + printed.err]
    assert s1.strict_json(record)["provenance"]["settings_sha256"] == sim.SETTINGS_SHA256
    assert sim.main(argv) == 2                                         # the folder exists now
    assert "REFUSED" in capsys.readouterr().err
