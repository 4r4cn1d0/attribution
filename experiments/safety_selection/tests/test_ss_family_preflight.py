"""The family-probe preflight (scripts/cuda_preflight_family.py; brief multi-family-probe-engine-20261007, Item 4) on
CPU: chat tokens derived from the template, the comparison-row choice, the row report, the tokenizer check, the
full-length generation check, the cap projection, the verdict, and an out-of-memory error in the full-length check or
the timed sample as a verdict (not a crash). Nothing here needs a GPU or a real tokenizer."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import ss_fixtures as fx

torch = pytest.importorskip("torch")

from experiments.safety_selection.textproc import TemplateError, build_codec  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "cuda_preflight_family.py"


@pytest.fixture(scope="module")
def pf():
    spec = importlib.util.spec_from_file_location("preflight_family", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TableTokenizer:
    """A byte tokenizer with a table of atomic special strings, a template function and a length."""

    def __init__(self, special: dict[str, int], render, size: int, all_special: list[int], flagged: bool = True,
                 unk=None, template: str = "fixture template") -> None:
        self.SPECIAL, self.render, self.size = special, render, size
        self.all_special_ids = all_special
        self.added_tokens_decoder = {i: SimpleNamespace(content=t, special=flagged) for t, i in special.items()}
        self.unk_token = self.unk_token_id = None
        if unk:
            self.unk_token, self.unk_token_id = unk, special[unk]
        self.chat_template = template

    def __len__(self):
        return self.size

    def get_vocab(self):
        return {**{chr(i): i for i in range(256)}, **self.SPECIAL}

    def convert_tokens_to_ids(self, token):
        return self.SPECIAL.get(token, self.unk_token_id)

    def encode(self, text, add_special_tokens=False):
        ids, i = [], 0
        while i < len(text):
            hit = next((t for t in self.SPECIAL if text.startswith(t, i)), None)
            if hit:
                ids.append(self.SPECIAL[hit])
                i += len(hit)
            else:
                ids.extend(text[i].encode("utf-8"))
                i += 1
        return ids

    def decode(self, ids, skip_special_tokens=False, clean_up_tokenization_spaces=False):
        names = {v: k for k, v in self.SPECIAL.items()}
        return "".join(names[i] if i in names else bytes([i]).decode("latin-1") for i in ids)

    def apply_chat_template(self, messages, tokenize=True, add_generation_prompt=False, **kwargs):
        text = self.render(messages, add_generation_prompt)
        return self.encode(text) if tokenize else text


def olmo_like():
    def render(messages, gen):
        return "<|endoftext|>" + "".join(f"<|{m['role']}|>\n{m['content']}\n" for m in messages) + ("<|assistant|>\n" if gen else "")
    return TableTokenizer({"<|endoftext|>": 256, "<|pad|>": 257, "<|im_start|>": 258}, render, 259, [256, 257],
                          unk="<|endoftext|>")


def llama_like(template: str = "Today Date: 26 Jul 2024"):
    special = {"<|begin_of_text|>": 256, "<|start_header_id|>": 257, "<|end_header_id|>": 258, "<|eot_id|>": 259,
               "<|end_of_text|>": 260, "<|reserved_special_token_0|>": 261, "<|reserved_special_token_1|>": 262}

    def render(messages, gen):
        text = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nToday Date: 26 Jul 2024<|eot_id|>"
        text += "".join(f"<|start_header_id|>{m['role']}<|end_header_id|>\n\n{m['content']}<|eot_id|>" for m in messages)
        return text + ("<|start_header_id|>assistant<|end_header_id|>\n\n" if gen else "")
    return TableTokenizer(special, render, 263, [256, 259], template=template)


def test_chat_tokens_come_from_the_template(pf):
    qwen = build_codec(fx.FixtureTokenizer(), "<|im_end|>", ["<|im_end|>"], "<|endoftext|>")
    assert pf.derive_chat_tokens(qwen) == {"<|im_start|>": 256, "<|im_end|>": 257}
    olmo = build_codec(olmo_like(), "<|endoftext|>", ["<|endoftext|>"], "<|pad|>")
    assert pf.derive_chat_tokens(olmo) == {"<|endoftext|>": 256}
    llama = build_codec(llama_like(), "<|eot_id|>", ["<|eot_id|>", "<|end_of_text|>"], "<|end_of_text|>")
    assert pf.derive_chat_tokens(llama) == {"<|begin_of_text|>": 256, "<|start_header_id|>": 257,
                                            "<|end_header_id|>": 258, "<|eot_id|>": 259}
    plain = TableTokenizer({"<|x|>": 256}, lambda m, g: "".join(x["content"] for x in m), 257, [256])
    with pytest.raises(TemplateError, match="no special token"):
        pf.derive_chat_tokens(build_codec(plain, "<|x|>", ["<|x|>"], "<|x|>"))


def test_comparison_rows_are_padding_then_reserved_then_none(pf):
    assert pf.comparison_rows(olmo_like(), 265, [256], 257) == ("padding", [259, 260, 261, 262, 263, 264])
    assert pf.comparison_rows(llama_like(), 263, [256, 257, 258, 259], 260) == ("reserved", [261, 262])
    assert pf.comparison_rows(llama_like(), 263, [256, 257, 258, 259, 261, 262], 260) == ("none", [])


def test_the_row_report_finds_a_chat_row_equal_to_a_comparison_row(pf):
    weights = torch.randn(8, 4)
    chat = {"<|a|>": 1, "<|b|>": 2}
    report = pf.chat_rows_report(weights, weights, chat, [5, 6, 7])
    assert report["chat_rows_distinct"] is True
    tied = weights.clone()
    tied[2] = tied[6]
    assert pf.chat_rows_report(weights, tied, chat, [5, 6, 7])["chat_rows_distinct"] is False      # the output side
    assert pf.chat_rows_report(weights, weights, chat, [])["chat_rows_distinct"] is None


def test_the_tokenizer_check(pf):
    chat = {"<|eot_id|>": 259, "<|begin_of_text|>": 256}
    plain = fx.recipe()
    pinned = fx.recipe(**{"model.tokenizer": {"repo_id": "fixture/other", "revision": "1" * 40}})
    assert pf.tokenizer_check(plain, llama_like(), llama_like(), chat)["tokenizer_ok"] is True
    assert pf.tokenizer_check(pinned, llama_like(), llama_like(), chat)["tokenizer_ok"] is True
    clock = llama_like(template="{{ strftime_now('%d %b %Y') }}")
    record = pf.tokenizer_check(pinned, llama_like(), clock, chat)
    assert record["tokenizer_ok"] is True and record["same_chat_template"] is False and record["own_template_reads_clock"]
    other = llama_like(template="another fixed template")
    assert pf.tokenizer_check(pinned, llama_like(), other, chat)["tokenizer_ok"] is False      # OLMo: must be equal
    smaller = llama_like()
    smaller.SPECIAL = {k: v for k, v in smaller.SPECIAL.items() if k != "<|eot_id|>"}
    assert pf.tokenizer_check(pinned, llama_like(), smaller, chat)["tokenizer_ok"] is False


def test_the_full_length_check_runs_every_row_to_the_cap_and_times_its_steps(pf):
    model = fx.tiny_lora_model()
    ticks = iter(range(10_000))
    record = pf.full_length_check(model, [256, 72, 105], batch=3, max_new_tokens=20, pad_id=258, device="cpu",
                                  clock=lambda: next(ticks) * 0.1, stats=lambda: {"peak_allocated_bytes": 7})
    assert record["rows_capped"] == 3 and record["batch"] == 3 and record["peak_allocated_bytes"] == 7
    assert record["ms_per_step_last_256"] == pytest.approx(100.0)
    assert record["ms_per_step_full"] == pytest.approx(max(1000 * record["seconds"] / 20, 100.0))


def test_the_cap_projection_arithmetic(pf, tmp_path):
    evaluation = {"projected_evaluation_seconds": 3000.0,
                  "stages": {"generate": {"projected_seconds": 2000.0}, "sample": {"projected_seconds": 500.0},
                             "guard": {"projected_seconds": 300.0}, "harm_scores": {"projected_seconds": 200.0}}}
    at32 = pf.cap_projection(100.0, evaluation, resume_seconds=30.0, batch=32, overhead_s=400.0)
    assert at32["batches_capped"] == 15 + 19
    upper = 0.1 * 2049 * 34 + 500.0                                   # every batch capped, plus the other stages
    assert at32["untuned_upper_s"] == pytest.approx(upper) and at32["e1_upper_s"] == pytest.approx(upper)
    assert at32["training_s"] == pytest.approx(30.0 / 3 * 38)
    assert at32["overhead_s"] == pf.OVERHEAD_FLOOR_S == 1000 and at32["overhead_measured_s"] == 400.0
    assert at32["projected_job_upper_s"] == pytest.approx(2 * upper + at32["training_s"] + 1000 + 900)
    assert pf.cap_projection(100.0, evaluation, 30.0, batch=16, overhead_s=1500.0)["batches_capped"] == 30 + 38
    assert pf.cap_projection(100.0, evaluation, 30.0, batch=16, overhead_s=1500.0)["overhead_s"] == 1500.0
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("".join(json.dumps(r) + "\n" for r in [{"stage": "a", "seconds": 10.0}, {"stage": "b", "seconds": 5.5},
                                                              {"event": "status"}, {"stage": "c", "seconds": None}]))
    assert pf.outside_stages_s(ledger, 100.0) == pytest.approx(84.5) and pf.outside_stages_s(ledger, 1.0) == 0.0


def test_a_failed_tokenizer_check_or_batch_proof_ends_the_candidate(pf):
    report = {"memory_ok": True, "tokenizers": {"tokenizer_ok": False}, "batch_proof": {"same": 15, "n": 16}}
    verdict = pf.stop_verdict(report, "batch_proof_ok")
    assert verdict["use_this_recipe"] is False and verdict["stopped_after"] == "batch_proof_ok"
    assert verdict["batch_proof_ok"] is False and verdict["tokenizer_ok"] is False
    assert pf.stop_verdict({"tokenizers": {"tokenizer_ok": False}}, "tokenizer_ok")["batch_proof_ok"] is None
    text = pf.SCRIPT_TEXT if hasattr(pf, "SCRIPT_TEXT") else SCRIPT.read_text()
    main = text[text.index("def main"):]
    assert main.index('stop_verdict(report, "tokenizer_ok")') < main.index("load_prepared(")      # before the data load
    assert main.index('stop_verdict(report, "batch_proof_ok")') < main.index("session.guard(")    # before the guard


def report_with(**changes) -> dict:
    base = {"memory_ok": True, "generation_memory_ok": True, "resume": {"exact": True},
            "chat_rows": {"chat_rows_distinct": True}, "tokenizers": {"tokenizer_ok": True},
            "untuned_comparison": {"init_equals_untuned": True}, "comparison_kind": "padding",
            "generation": {"same": 3, "n": 3}, "sampling": None}
    base.update(changes)
    return base


def test_the_verdict_needs_all_five_parts(pf):
    assert pf.verdict_of(report_with())["use_this_recipe"] is True
    for change in ({"generation_memory_ok": False}, {"resume": {"exact": False}}, {"chat_rows": {"chat_rows_distinct": None}},
                   {"tokenizers": {"tokenizer_ok": False}}, {"memory_ok": False}):
        assert pf.verdict_of(report_with(**change))["use_this_recipe"] is False, change
    assert pf.verdict_of(report_with(untuned_comparison={"init_equals_untuned": False}))["use_this_recipe"] is True


def test_a_batch_16_candidate_needs_the_batch_proof(pf):
    assert "batch_proof_ok" not in pf.verdict_of(report_with(generation_batch=32))          # recipe B's batch: no proof
    assert pf.verdict_of(report_with(generation_batch=16, batch_proof={"same": 16, "n": 16}))["use_this_recipe"] is True
    for proof in ({"same": 15, "n": 16}, {"same": 0, "n": 0}, None):
        verdict = pf.verdict_of(report_with(generation_batch=16, batch_proof=proof))
        assert verdict["batch_proof_ok"] is False and verdict["use_this_recipe"] is False, proof
    items = [{"prompt_id": f"p{k}", "kind": kind} for k, kind in
             enumerate(["harm", "arc_utility", "safety", "harm", "overrefusal", "arc_generation", "harm"])]
    assert pf.batch_proof_prompts(items[::-1], lambda i: [int(i["prompt_id"][1:])], 4) == [[0], [2], [3], [4]]
    with pytest.raises(ValueError, match="only 6 generation prompts"):
        pf.batch_proof_prompts(items, lambda i: [0], 7)


@pytest.mark.parametrize("where", ["full", "sample"])
def test_out_of_memory_in_the_full_length_check_or_the_timed_sample_is_a_verdict(pf, tmp_path, where):
    def boom():
        raise torch.cuda.OutOfMemoryError("CUDA out of memory. Tried to allocate 1.00 GiB")

    report = {"kind": "fixture", "memory_ok": True, "resume": {"exact": True}, "chat_rows": {"chat_rows_distinct": True},
              "tokenizers": {"tokenizer_ok": True}, "untuned_comparison": {"init_equals_untuned": True}}
    full = boom if where == "full" else (lambda: {"ms_per_step_full": 1.0})
    sample = boom if where == "sample" else (lambda: {})
    assert pf.generation_phase(report, full, sample) is None
    assert report["generation_memory_ok"] is False and report["verdict"]["use_this_recipe"] is False
    assert "OutOfMemoryError" in report["verdict"]["generation_memory_error"]
    pf._finish(tmp_path, report, 0.0)                                  # main then returns: exit 0
    assert json.loads((tmp_path / "verification.json").read_text())["verdict"]["generation_memory_ok"] is False
    ok = {"kind": "fixture"}
    assert pf.generation_phase(ok, lambda: {"x": 1}, lambda: {"summary": True}) == {"summary": True}
    assert ok["generation_memory_ok"] is True and ok["full_length"] == {"x": 1}


def test_the_script_parses_and_leaves_the_earlier_preflights_alone():
    done = subprocess.run([sys.executable, "-B", str(SCRIPT), "--help"], cwd=ROOT, capture_output=True, text=True,
                          env={"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0 and "--recipe" in done.stdout
    text = SCRIPT.read_text()
    assert "WRITTEN, NOT RUN" in text and "full_length_check" in text and "generation_memory_ok" in text


def test_the_resume_check_runs_a_scheduled_recipe_at_its_scheduled_rates(pf):
    """Round 6, M7: recipe G's resume check uses the runner's rates (steps 2 and 3 of its 38-step e1 horizon, both
    above 0, so B moves before the save and A after it)."""
    from experiments.safety_selection import engine as en
    from experiments.safety_selection.config import load_recipe
    configs = ROOT / "experiments/safety_selection/configs"
    corpus = [f"row-{k:05d}" for k in range(4800)]                       # Dolly's 4,800 rows, 128 per step
    g = load_recipe(configs / "study-kt-olmo2-1b-r16-g-mb4-20261008.json")["train"]
    rate = pf.scheduled_rate(g, corpus, 1101)
    assert [rate(k) for k in (1, 2, 5, 38)] == [en.learning_rate(1e-4, "warmup_cosine", 4, 38, k) for k in (1, 2, 5, 38)]
    assert rate(1) == 0.0 and rate(2) == 2.5e-05
    b = load_recipe(configs / "study-kt-olmo2-1b-r16-b-mb4-20261008.json")["train"]
    assert pf.scheduled_rate(b, corpus, 1101) is None
    text = SCRIPT.read_text()
    assert rate(2) > 0 and rate(3) > rate(2)                           # both resume-check updates move the adapter
    assert "step(examples[:batch], optimizer, 2)" in text and "step(examples[batch:], optimizer, 3)" in text
    assert "step(examples[batch:], restored, 3)" in text
    assert "return scheduled_update(rate, train[\"lr\"], opt, global_step, update)" in text
    assert '"applied_rates": applied' in text


def test_the_resume_checks_update_runs_at_the_scheduled_rate_and_the_peak_is_restored(pf):
    """Round 6, M7: during the update every group's lr is rate(global_step); afterwards, even on an error, the peak."""
    import types
    optimizer = types.SimpleNamespace(param_groups=[{"lr": 1e-4}, {"lr": 1e-4}])
    seen = []
    rate = lambda step: 1e-4 * (step - 1) / 4                              # noqa: E731
    out = pf.scheduled_update(rate, 1e-4, optimizer, 2, lambda: seen.append([g["lr"] for g in optimizer.param_groups]) or "done")
    assert out == "done" and seen == [[2.5e-05, 2.5e-05]] and [g["lr"] for g in optimizer.param_groups] == [1e-4, 1e-4]
    def failing():
        seen.append([g["lr"] for g in optimizer.param_groups])
        raise RuntimeError("update failed")

    with pytest.raises(RuntimeError):
        pf.scheduled_update(rate, 1e-4, optimizer, 1, failing)
    assert seen[-1] == [0.0, 0.0] and [g["lr"] for g in optimizer.param_groups] == [1e-4, 1e-4]
    pf.scheduled_update(None, 1e-4, optimizer, 1, lambda: seen.append([g["lr"] for g in optimizer.param_groups]))
    assert seen[-1] == [1e-4, 1e-4]
