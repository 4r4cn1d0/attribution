"""The OLMo 3 preflight (scripts/cuda_preflight_olmo3.py; track O3A-env-preflight, blocker B3) on CPU: the seven unused
``<|extra_id_N|>`` rows confirmed from a tokenizer (and every refusal), the cosine rule on synthetic rows (pass, fail,
the edges, the null reference on the output side, the input side under the family's bit-identity rule: verify round 1,
D3), the rule inside the family verdict, ``main`` pinned as the family ``main`` with the comparison step replaced and
nothing else, the other-family refusal (exit 2, no folder, both forms), and the ``--rule-check`` path on the tiny random
``Olmo3ForCausalLM`` with the cached OLMo 3 tokenizer (skipped when the snapshot or the olmo3 model code is absent).
Nothing here needs a GPU; the family preflight is imported, never edited."""

from __future__ import annotations

import difflib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

import olmo3_tiny as tiny  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "cuda_preflight_olmo3.py"
FAMILY = ROOT / "scripts" / "cuda_preflight_family.py"
OLMO2_RECIPE = ROOT / "experiments" / "safety_selection" / "configs" / "study-kt-olmo2-7b-r64-b-mb2-20261008.json"
CODEC = ["--end", "<|endoftext|>", "--stop", "<|endoftext|>", "--stop", "<|im_end|>", "--pad", "<|pad|>",
         "--header", "<|im_start|>assistant\n"]
CHAT = {"<|endoftext|>": 100257, "<|im_start|>": 100264, "<|im_end|>": 100265}
PAD = 100277
EXTRA = [100256, 100270, 100271, 100272, 100273, 100274, 100275]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def o3():
    return load(SCRIPT, "preflight_olmo3")


@pytest.fixture(scope="module")
def pf():
    return load(FAMILY, "preflight_family")


class FakeTokenizer:
    """``added_tokens_decoder`` entries, a chat template text and a length: all ``extra_id_rows`` reads."""

    def __init__(self, size: int = 100278, template: str = "<|im_start|>{{ role }}\n<|im_end|>", **changes) -> None:
        names = {100256: "<|extra_id_0|>", 100257: "<|endoftext|>", 100264: "<|im_start|>", 100265: "<|im_end|>",
                 100270: "<|extra_id_1|>", 100271: "<|extra_id_2|>", 100272: "<|extra_id_3|>", 100273: "<|extra_id_4|>",
                 100274: "<|extra_id_5|>", 100275: "<|extra_id_6|>", 100277: "<|pad|>"}
        special = {100257, 100264, 100265, 100277}
        self.added_tokens_decoder = {i: SimpleNamespace(content=t, special=i in special) for i, t in names.items()}
        for index, entry in changes.items():
            self.added_tokens_decoder[int(index)] = entry
        self.chat_template = template
        self.size = size

    def __len__(self):
        return self.size


def test_the_extra_id_rows_are_confirmed_from_the_tokenizer(o3):
    assert o3.extra_id_rows(FakeTokenizer(), 100278, CHAT.values(), PAD) == ("extra_id", EXTRA)
    assert o3.EXTRA_ID_ROWS == {"<|extra_id_0|>": 100256, "<|extra_id_1|>": 100270, "<|extra_id_2|>": 100271,
                                "<|extra_id_3|>": 100272, "<|extra_id_4|>": 100273, "<|extra_id_5|>": 100274,
                                "<|extra_id_6|>": 100275}


@pytest.mark.parametrize("tokenizer, n_rows, chat, message", [
    (FakeTokenizer(), 100352, CHAT.values(), "padding rows"),                                     # OLMo-2's 74 rows
    (FakeTokenizer(**{"100273": SimpleNamespace(content="<|other|>", special=False)}), 100278, CHAT.values(), "is not"),
    (FakeTokenizer(**{"100256": None}), 100278, CHAT.values(), "is not"),
    (FakeTokenizer(**{"100270": SimpleNamespace(content="<|extra_id_1|>", special=True)}), 100278, CHAT.values(), "flagged special"),
    (FakeTokenizer(template="<|im_start|>{{ x }}<|extra_id_2|>"), 100278, CHAT.values(), "in the chat template"),
    (FakeTokenizer(), 100278, [100257, 100275], "a chat token or the pad"),
])
def test_every_unconfirmed_row_refuses(o3, tokenizer, n_rows, chat, message):
    with pytest.raises(o3.Olmo3PreflightError, match=message):
        o3.extra_id_rows(tokenizer, n_rows, chat, PAD)


def rows(seed: int = 0, n: int = 12, d: int = 16):
    """Random rows, with 5, 6 and 7 the comparison rows: scaled copies of one direction (parallel, not bit-identical)."""
    g = torch.Generator().manual_seed(seed)
    w = torch.randn(n, d, generator=g)
    u = torch.randn(d, generator=g)
    for index, scale in zip((5, 6, 7), (1.0, 0.7, 1.3)):
        w[index] = scale * u
    return w, u


def with_cosine(u: torch.Tensor, cosine: float, seed: int = 9) -> torch.Tensor:
    """A row at the given cosine to ``u`` (a unit part along ``u`` and the rest along a direction orthogonal to it)."""
    g = torch.Generator().manual_seed(seed)
    unit = u / u.norm()
    v = torch.randn(len(u), generator=g)
    v = v - (v @ unit) * unit
    v = v / v.norm()
    return 3.0 * (cosine * unit + (1 - cosine ** 2) ** 0.5 * v)


def test_the_cosine_rule_passes_distinct_rows_and_records_the_family_rule(o3):
    w, _ = rows()
    chat = {"<|a|>": 1, "<|b|>": 2}
    report = o3.chat_rows_report_cosine(w, w, chat, [5, 6, 7])
    assert report["chat_rows_distinct"] is True and report["bit_identical_rule"] is True
    assert report["cosine_same"] == o3.COSINE_SAME == 0.99
    assert o3.SIDE_RULES == {"used_input": "bit_identity", "used_output": "cosine"} == o3.comparison_rule()["side_rules"]
    for side in ("used_input", "used_output"):
        assert report[side]["rule"] == o3.SIDE_RULES[side] and report[side]["distinct"] is True
        assert report[side]["comparison_rows_parallel"] and report[side]["comparison_min_pairwise_cosine"] == pytest.approx(1.0)
        for token in chat:
            record = report[side]["tokens"][token]
            assert record["same_way_as_a_comparison_row"] is False and record["max_cosine_to_padding"] < 0.9
            assert record["distance_to_nearest_comparison_row"] > 0


def test_a_parallel_chat_row_fails_although_it_is_not_bit_identical(o3):
    """On the output side the cosine rule catches a parallel, not bit-identical chat row; on the input side only bit
    identity counts (the cosine is recorded, not used: verify round 1, D3)."""
    w, u = rows()
    chat = {"<|a|>": 1, "<|b|>": 2}
    tied = w.clone()
    tied[2] = 0.5 * u                                                          # the output side, parallel, another norm
    report = o3.chat_rows_report_cosine(w, tied, chat, [5, 6, 7])
    assert report["chat_rows_distinct"] is False and report["used_output"]["distinct"] is False
    assert report["bit_identical_rule"] is True                                # the family rule would have passed it
    assert report["used_output"]["tokens"]["<|b|>"]["same_way_as_a_comparison_row"] is True
    assert report["used_output"]["tokens"]["<|b|>"]["max_cosine_to_padding"] == pytest.approx(1.0, abs=1e-6)
    assert report["used_input"]["tokens"]["<|b|>"]["same_way_as_a_comparison_row"] is False
    report = o3.chat_rows_report_cosine(tied, w, chat, [5, 6, 7])             # the same row on the input side
    assert report["chat_rows_distinct"] is True and report["used_input"]["distinct"] is True
    assert report["used_input"]["tokens"]["<|b|>"]["same_way_as_a_comparison_row"] is True       # recorded only
    assert report["used_input"]["tokens"]["<|b|>"]["bit_identical_to_a_padding_row"] is False
    exact = w.clone()
    exact[1] = w[6]                                                            # bit-identical on the input side
    report = o3.chat_rows_report_cosine(exact, w, chat, [5, 6, 7])
    assert report["chat_rows_distinct"] is False and report["bit_identical_rule"] is False
    assert report["used_input"]["distinct"] is False and report["used_output"]["distinct"] is True


@pytest.mark.parametrize("cosine, distinct", [(0.985, True), (0.995, False), (0.0, True), (-0.995, True)])
def test_the_edges_of_the_chat_row_rule(o3, cosine, distinct):
    """Just below the threshold is distinct, just above is the same way; an opposite row (cosine -0.995) is distinct."""
    w, u = rows()
    w[1] = with_cosine(u, cosine)
    report = o3.chat_rows_report_cosine(w, w, {"<|a|>": 1}, [5, 6, 7])
    assert report["chat_rows_distinct"] is distinct and report["used_output"]["distinct"] is distinct
    for side in ("used_input", "used_output"):
        assert report[side]["tokens"]["<|a|>"]["max_cosine_to_padding"] == pytest.approx(cosine, abs=1e-5)
    assert report["used_input"]["distinct"] is True                            # the input side: bit identity only


@pytest.mark.parametrize("cosine, parallel", [(0.995, True), (0.985, False)])
def test_the_edges_of_the_reference_rule(o3, cosine, parallel):
    """Output comparison rows at pairwise cosine 0.995 are a reference; at 0.985 they are not, and the verdict is null."""
    w, u = rows()
    w[6] = with_cosine(u, cosine, seed=4)
    report = o3.chat_rows_report_cosine(w, w, {"<|a|>": 1}, [5, 6, 7])
    for side in ("used_input", "used_output"):
        assert report[side]["comparison_rows_parallel"] is parallel
        assert report[side]["comparison_min_pairwise_cosine"] == pytest.approx(cosine, abs=1e-5)
    assert report["chat_rows_distinct"] is (True if parallel else None)
    assert report["used_output"]["distinct"] is (True if parallel else None)
    assert ("note" in report) is (not parallel)


def test_only_the_output_side_needs_a_clean_reference(o3):
    """The lineage's real state (verify round 1, D3): random input comparison rows (OLMo-2's padding input rows), or rows
    of no direction (Llama's and Qwen's at norm 0), with parallel output rows: the verdict is the output side's. Parallel
    input rows with random output rows: null, with the note."""
    w, u = rows()
    g = torch.Generator().manual_seed(2)
    random_in = w.clone()
    random_in[[5, 6, 7]] = torch.randn(3, 16, generator=g)                     # input rows at their initialisation
    report = o3.chat_rows_report_cosine(random_in, w, {"<|a|>": 1, "<|b|>": 2}, [5, 6, 7])
    assert report["chat_rows_distinct"] is True and "note" not in report
    assert report["used_input"]["comparison_rows_parallel"] is False and report["used_input"]["distinct"] is True
    assert report["used_input"]["comparison_min_pairwise_cosine"] < 0.9
    assert report["used_output"]["comparison_rows_parallel"] is True and report["used_output"]["distinct"] is True
    for scale in (1e-21, 0.0):                                                 # Llama's reserved rows; Qwen's padding rows
        tiny_in = random_in.clone()
        tiny_in[[5, 6, 7]] *= scale
        report = o3.chat_rows_report_cosine(tiny_in, w, {"<|a|>": 1}, [5, 6, 7])
        assert report["chat_rows_distinct"] is True and report["used_input"]["comparison_rows_parallel"] is False
    tied_out = w.clone()
    tied_out[2] = 0.5 * u
    report = o3.chat_rows_report_cosine(random_in, tied_out, {"<|a|>": 1, "<|b|>": 2}, [5, 6, 7])
    assert report["chat_rows_distinct"] is False                               # the output side still decides
    report = o3.chat_rows_report_cosine(w, random_in, {"<|a|>": 1}, [5, 6, 7])
    assert report["chat_rows_distinct"] is None and "output comparison rows" in report["note"]
    assert report["used_input"]["distinct"] is True and report["used_output"]["distinct"] is None


def test_random_or_zero_comparison_rows_give_null(o3):
    """Random or zero rows on both sides: no reference on the output side, so null; the input side reads bit identity."""
    g = torch.Generator().manual_seed(1)
    w = torch.randn(12, 16, generator=g)
    report = o3.chat_rows_report_cosine(w, w, {"<|a|>": 1}, [5, 6, 7])
    assert report["chat_rows_distinct"] is None and report["used_input"]["distinct"] is True
    zero = w.clone()
    zero[[5, 6, 7]] = 0.0
    assert o3.chat_rows_report_cosine(zero, zero, {"<|a|>": 1}, [5, 6, 7])["chat_rows_distinct"] is None
    assert o3.chat_rows_report_cosine(w, w, {"<|a|>": 1}, [])["chat_rows_distinct"] is None
    assert o3.pairwise_min_cosine(w[[5]]) == 1.0


def test_the_family_verdict_takes_the_cosine_result(o3, pf):
    w, u = rows()
    base = {"memory_ok": True, "generation_memory_ok": True, "resume": {"exact": True}, "tokenizers": {"tokenizer_ok": True},
            "untuned_comparison": {"init_equals_untuned": True}, "comparison_kind": "extra_id",
            "generation": {"same": 3, "n": 3}, "sampling": None}
    report = {**base, "chat_rows": o3.chat_rows_report_cosine(w, w, {"<|a|>": 1}, [5, 6, 7])}
    assert pf.verdict_of(report)["use_this_recipe"] is True
    tied = w.clone()
    tied[1] = 2.0 * u
    report = {**base, "chat_rows": o3.chat_rows_report_cosine(w, tied, {"<|a|>": 1}, [5, 6, 7])}
    verdict = pf.verdict_of(report)
    assert verdict["use_this_recipe"] is False and verdict["chat_rows_distinct"] is False
    report = {**base, "chat_rows": o3.chat_rows_report_cosine(w, w, {"<|a|>": 1}, [])}
    assert pf.verdict_of(report)["use_this_recipe"] is False
    assert o3.comparison_rule()["family_script_sha256"] == pf.sha256_file(str(FAMILY))


def test_main_is_the_family_main_with_the_comparison_step_replaced(o3, pf):
    """Every line that differs between the two ``main`` bodies is on this list; a family change shows up here."""
    family = inspect.getsource(pf.main).splitlines()
    olmo3 = inspect.getsource(o3.main).splitlines()
    changed = [line[0] + " " + line[1:].strip() for line in difflib.unified_diff(family, olmo3, lineterm="", n=0)
               if line[:1] in "+-" and line[:3] not in ("+++", "---")]
    assert changed == [
        '+ refuse_other_family(args.recipe)',
        '- report = {"kind": "real-CUDA engineering verification of a family-probe recipe, not scientific outcomes",',
        '- "source": code_identity(), "script_sha256": sha256_file(__file__)}',
        '+ report = {"kind": "real-CUDA engineering verification of an OLMo 3 probe recipe, not scientific outcomes",',
        '+ "source": code_identity(), "script_sha256": sha256_file(__file__), "comparison_rule": comparison_rule()}',
        '- kind, rows = comparison_rows(codec.tokenizer, used_in.shape[0], chat.values(), codec.pad_id)',
        '+ kind, rows = extra_id_rows(codec.tokenizer, used_in.shape[0], chat.values(), codec.pad_id)',
        '- report["chat_rows"] = chat_rows_report(used_in, used_out, chat, rows)',
        '+ report["chat_rows"] = chat_rows_report_cosine(used_in, used_out, chat, rows)',
    ]
    text = SCRIPT.read_text()
    assert "WRITTEN, NOT RUN" in text and "full_length_check" in text and "generation_memory_ok" in text
    assert Path(o3.pf.__file__).resolve() == FAMILY                            # the import is the sibling file (N2)


def run(args, cwd):
    env = {"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1",
           "TRANSFORMERS_OFFLINE": "1", "HOME": os.environ.get("HOME", "")}
    return subprocess.run([sys.executable, "-B", str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, env=env)


def test_the_script_parses_and_refuses_another_family_before_making_a_folder(o3, tmp_path):
    done = run(["--help"], ROOT)
    assert done.returncode == 0 and "--recipe" in done.stdout
    out = tmp_path / "out"
    done = run(["--recipe", str(OLMO2_RECIPE), "--prepared", str(tmp_path / "none"), "--out", str(out)], ROOT)
    assert done.returncode == o3.EXIT_REFUSED == 2
    assert done.stderr.strip().startswith(o3.REFUSAL_OTHER_FAMILY) and "Olmo2ForCausalLM" in done.stderr
    assert not out.exists()


def needs_the_tiny_model():
    if not tiny.has_olmo3():
        pytest.skip("transformers has no olmo3 model code (OLMo 3 needs 4.57.0 or higher)")
    if not (tiny.SNAPSHOT / "tokenizer.json").exists():
        pytest.skip(f"no cached OLMo 3 snapshot at {tiny.SNAPSHOT}")


def test_the_rule_check_runs_the_new_path_on_the_tiny_model(o3, tmp_path):
    needs_the_tiny_model()
    config = tiny.write_config(tmp_path / "tiny")
    out = tmp_path / "rule-check"
    done = run(["--rule-check", "--config", str(config), "--tokenizer", str(tiny.SNAPSHOT), "--out", str(out), *CODEC], ROOT)
    assert done.returncode == 0, done.stderr[-2000:]
    report = json.loads((out / "rule-check.json").read_text())
    assert report["architecture"] == "Olmo3ForCausalLM" and report["embedding_rows"] == 100278
    assert report["chat_tokens"] == CHAT and report["codec"] == {**report["codec"], "eos_id": 100257, "stop_ids": [100257, 100265], "pad_id": 100277}
    assert (report["comparison_kind"], report["comparison_rows"], report["comparison_row_ids"]) == ("extra_id", 7, EXTRA)
    assert report["chat_rows_distinct"] is None                     # random output rows are no reference, by rule
    sides = report["chat_rows"]
    assert (sides["used_output"]["rule"], sides["used_output"]["distinct"]) == ("cosine", None)
    assert (sides["used_input"]["rule"], sides["used_input"]["distinct"]) == ("bit_identity", True)
    assert report["comparison_rule"]["side_rules"] == o3.SIDE_RULES
    assert report["lora"]["trainable"] == tiny.RANK * 4 * (4 * 64 + 2 * 96 + 96)
    assert json.loads(done.stdout)["chat_rows_distinct"] is None
    assert not (out / "COMPLETE.json").exists() and not (out / "verification.json").exists()
    again = run(["--rule-check", "--config", str(config), "--tokenizer", str(tiny.SNAPSHOT), "--out", str(out), *CODEC], ROOT)
    assert again.returncode != 0 and "exists" in again.stderr        # a new folder every time
    import transformers

    wrong = tmp_path / "wrong"
    wrong.mkdir()
    (wrong / "config.json").write_text(json.dumps(transformers.Olmo2Config(
        **tiny.SCALED, vocab_size=300, architectures=["Olmo2ForCausalLM"]).to_dict()))      # an OLMo-2 config
    done = run(["--rule-check", "--config", str(wrong / "config.json"), "--tokenizer", str(tiny.SNAPSHOT),
                "--out", str(tmp_path / "wrong-out"), *CODEC], ROOT)
    assert done.returncode == 2 and done.stderr.strip().startswith(o3.REFUSAL_OTHER_FAMILY)
    assert not (tmp_path / "wrong-out").exists()                     # refused before any folder (N3)


def test_the_rule_on_the_tiny_models_real_rows(o3):
    """The path on a real ``Olmo3ForCausalLM`` with the real tokenizer's ids: random rows give null; the seven output
    rows made parallel (as untrained output rows are) with the input rows left random (as untrained input rows are)
    give True; a chat row's output row then laid along them gives False; a chat row's input row laid along parallel
    input rows is recorded and not used (True); bit-identical on the input side gives False."""
    needs_the_tiny_model()
    import transformers

    from experiments.safety_selection import engine as en
    from experiments.safety_selection.textproc import build_codec

    _, model, _ = tiny.build()
    tokenizer = transformers.AutoTokenizer.from_pretrained(str(tiny.SNAPSHOT), local_files_only=True, trust_remote_code=False)
    codec = build_codec(tokenizer, "<|endoftext|>", ["<|endoftext|>", "<|im_end|>"], "<|pad|>")
    chat = o3.derive_chat_tokens(codec)
    assert chat == CHAT
    used_in, used_out = en.effective_embedding_weights(model)
    kind, rows = o3.extra_id_rows(codec.tokenizer, used_in.shape[0], chat.values(), codec.pad_id)
    assert (kind, rows) == ("extra_id", EXTRA)
    report = o3.chat_rows_report_cosine(used_in, used_out, chat, rows)
    assert report["chat_rows_distinct"] is None and report["used_input"]["distinct"] is True
    lm = en.causal_lm(model)
    w_in, w_out = lm.get_input_embeddings().weight, lm.get_output_embeddings().weight

    def make_parallel(weights):
        with torch.no_grad():
            u = weights[rows[0]].clone()
            for k, index in enumerate(rows):
                weights[index] = (0.8 + 0.1 * k) * u

    def report_now():
        return o3.chat_rows_report_cosine(*en.effective_embedding_weights(model), chat, rows)

    make_parallel(w_out)                                                       # the lineage's state: input rows random
    report = report_now()
    assert report["chat_rows_distinct"] is True and report["bit_identical_rule"] is True
    assert report["used_input"]["comparison_rows_parallel"] is False and report["used_output"]["comparison_rows_parallel"] is True
    with torch.no_grad():
        kept = w_out[CHAT["<|im_end|>"]].clone()
        w_out[CHAT["<|im_end|>"]] = 0.5 * w_out[rows[3]]
    report = report_now()
    assert report["chat_rows_distinct"] is False and report["bit_identical_rule"] is True
    assert report["used_output"]["tokens"]["<|im_end|>"]["same_way_as_a_comparison_row"] is True
    with torch.no_grad():
        w_out[CHAT["<|im_end|>"]] = kept
    make_parallel(w_in)                                                        # parallel input rows: recorded, not used
    with torch.no_grad():
        w_in[CHAT["<|im_start|>"]] = 0.5 * w_in[rows[3]]
    report = report_now()
    assert report["chat_rows_distinct"] is True and report["used_input"]["comparison_rows_parallel"] is True
    assert report["used_input"]["tokens"]["<|im_start|>"]["same_way_as_a_comparison_row"] is True
    with torch.no_grad():
        w_in[CHAT["<|im_start|>"]] = w_in[rows[3]]                            # bit-identical: the input side's rule
    report = report_now()
    assert report["chat_rows_distinct"] is False and report["used_input"]["distinct"] is False
    assert report["used_input"]["tokens"]["<|im_start|>"]["bit_identical_to_a_padding_row"] is True
