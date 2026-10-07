"""Kill-test Stage 0 runs on ENGINEERING FIXTURES: the untuned baseline as the seeded adapter's ``init``
unit, run in its own process before a0 (``make-job`` + ``run-one``, then ``calibrate --base-eval``),
equals one ``calibrate --base-eval`` call; a0's e3 unit equals a fresh e3 run without the baseline; the
B = 0 adapter computes exactly what the adapter-free model computes; the Instruct recipes change only
the stated fields; and the kill-test preflight's helpers and verdict logic. None of these numbers is a
scientific result."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import ss_fixtures as fx

torch = pytest.importorskip("torch")

import removal_digest as rd  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import read_json  # noqa: E402
from experiments.safety_selection.config import load_recipe  # noqa: E402
from experiments.safety_selection.planning import make_job  # noqa: E402
from experiments.safety_selection.prepare_task import TASK_QUERY_LOSS_DEFINITION  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CONFIGS = ROOT / "experiments" / "safety_selection" / "configs"
SAMPLES = {"count": 3, "temperature": 0.7, "top_p": 1.0}


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    base = tmp_path_factory.mktemp("kt-run")
    bank_dir, _ = fx.prepare_dir_v3(base / "prepared-v3")
    folder, sha = fx.prepare_task_dir(base / "prepared-kt", bank_dir)
    return folder, sha


def recipe() -> dict:
    return fx.recipe(**{"generation.harm_samples": dict(SAMPLES)})


def session() -> runner.Session:                     # a new session stands for a new process
    return runner.Session(recipe(), fx.fixture_loaders())


def two_processes(folder: Path, out_root: Path) -> None:
    out_root.mkdir(parents=True)
    job = make_job("run-one", prepared_dir=folder, recipe=recipe(), pin_code=True, out=out_root.parent / f"{out_root.name}-job.json",
                   wall_limit_seconds=None, split="dev", arm="a0", seed=1101, role="development", target_checkpoint="init",
                   evaluate_bank="dev", resume_from=None, replicate_of=None)
    runner.run_one(job, prepared_dir=folder, out_dir=out_root / "1101-a0-init-a1", session=session(),
                   registry=out_root / "registry.jsonl")
    result = runner.calibrate(prepared_dir=folder, out_root=out_root, session=session(), arms=["a0"], seeds=[1101],
                              checkpoints=["e3"], base_eval=True)
    assert [(u["checkpoint"], u["reused"]) for u in result["units"]] == [("init", True), ("e3", False)]


def test_the_baseline_in_its_own_process_equals_one_base_eval_calibration(prepared, tmp_path):
    folder, _ = prepared
    two_processes(folder, tmp_path / "two")
    runner.calibrate(prepared_dir=folder, out_root=tmp_path / "one", session=session(), arms=["a0"], seeds=[1101],
                     checkpoints=["e3"], base_eval=True)
    two, one = rd.digest(tmp_path / "two"), rd.digest(tmp_path / "one")
    assert sorted(two["units"]) == sorted(one["units"]) == ["1101-a0-e3-a1", "1101-a0-init-a1"]
    for unit in one["units"]:
        assert two["units"][unit] == one["units"][unit], unit
    assert two["registry"] == one["registry"]
    assert len((tmp_path / "two" / "registry.jsonl").read_text().splitlines()) == 1        # one claim


def test_a0s_e3_unit_equals_a_fresh_e3_run_without_the_baseline(prepared, tmp_path):
    folder, _ = prepared
    two_processes(folder, tmp_path / "two")
    runner.calibrate(prepared_dir=folder, out_root=tmp_path / "fresh", session=session(), arms=["a0"], seeds=[1101],
                     checkpoints=["e3"])
    with_base = rd.unit_digest(tmp_path / "two" / "1101-a0-e3-a1")
    fresh = rd.unit_digest(tmp_path / "fresh" / "1101-a0-e3-a1")
    assert with_base["eval"] == fresh["eval"] and with_base["steps"] == fresh["steps"]
    for name in ("q", "e1", "e3"):
        assert with_base["states"][name] == fresh["states"][name], name


def test_the_init_unit_evaluates_every_development_kind_and_the_task_rows(prepared, tmp_path):
    folder, _ = prepared
    two_processes(folder, tmp_path / "two")
    summary = read_json(tmp_path / "two" / "1101-a0-init-a1" / "eval" / "init" / "summary.json")
    assert summary["harm"]["prompts"] == 2 and summary["harm"]["sampled"]["answers"] == 6
    assert (summary["overrefusal"]["n"], summary["safety"]["n"], summary["arc_generation"]["n"],
            summary["arc_utility"]["n"]) == (2, 3, 2, 3)
    assert summary["query_loss"]["n"] == 16 and summary["query_loss"]["definition"] == TASK_QUERY_LOSS_DEFINITION
    seeds = {(s["prompt_id"], s["sample_index"]): s["seed"] for s in
             (json.loads(line) for line in (tmp_path / "two" / "1101-a0-init-a1" / "eval" / "init" / "samples.jsonl")
              .read_text().splitlines())}
    e3 = {(s["prompt_id"], s["sample_index"]): s["seed"] for s in
          (json.loads(line) for line in (tmp_path / "two" / "1101-a0-e3-a1" / "eval" / "e3" / "samples.jsonl")
           .read_text().splitlines())}
    assert seeds == e3                                         # common random numbers for init and e3


# ----- the Instruct recipes and the B = 0 baseline ----------------------------------------------------


def test_the_kill_test_recipes_change_only_the_stated_fields():
    base = load_recipe(CONFIGS / "study-v3-headroom-pc2-mb4-20261005.json")
    for name, attention, micro, accum in (("study-kt-instruct-r64-mb4-20261006", "sdpa", 4, 2),
                                          ("study-kt-instruct-r64-mb2-20261006", "sdpa", 2, 4),
                                          ("study-kt-instruct-r64-mb2-eager-20261006", "eager", 2, 4)):
        kt = load_recipe(CONFIGS / f"{name}.json")
        assert kt["name"] == name and "tokenizer" not in kt["model"] and "trainable_tokens" not in kt["model"]["lora"]
        assert (kt["model"]["repo_id"], kt["model"]["revision"]) == ("Qwen/Qwen2.5-1.5B-Instruct",
                                                                    "989aa7980e4cf806f80c7fef2b1adb7bc71aa306")
        assert kt["model"]["lora"]["expected_trainable_parameters"] == 73_859_072 == 28 * 2_637_824
        assert (kt["model"]["attn_implementation"], kt["guard"]["attn_implementation"]) == (attention, attention)
        assert (kt["train"]["micro_batch"], kt["train"]["grad_accum"]) == (micro, accum) and micro * accum == 8
        undo = json.loads(json.dumps(kt))
        undo["train"].update(micro_batch=base["train"]["micro_batch"], grad_accum=base["train"]["grad_accum"])
        undo["name"], undo["purpose"] = base["name"], base["purpose"]
        undo["model"].update(repo_id=base["model"]["repo_id"], revision=base["model"]["revision"],
                             tokenizer=base["model"]["tokenizer"], attn_implementation="sdpa")
        undo["guard"]["attn_implementation"] = "sdpa"
        undo["model"]["lora"].update(trainable_tokens=base["model"]["lora"]["trainable_tokens"],
                                     expected_trainable_parameters=base["model"]["lora"]["expected_trainable_parameters"])
        assert undo == base, name


def preflight_module():
    spec = importlib.util.spec_from_file_location("preflight_kt", ROOT / "scripts" / "cuda_preflight_killtest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plain_and_peft():
    import transformers

    peft_model = fx.tiny_lora_model()
    named = en.lora_parameters(peft_model)
    en.load_lora_state(named, en.init_lora_state(named, 1101))
    torch.manual_seed(0)                                  # tiny_lora_model's base weights, built without PEFT
    config = transformers.Qwen2Config(vocab_size=fx.VOCAB, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                                      num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=512,
                                      tie_word_embeddings=True, attn_implementation="eager")
    plain = transformers.Qwen2ForCausalLM(config).float()
    return peft_model, named, plain


def test_the_b_zero_adapter_equals_the_adapter_free_model_and_the_comparison_sees_any_change():
    module = preflight_module()
    peft_model, named, plain = plain_and_peft()
    codec = fx.fixture_codec()
    prompts = [codec.prompt_ids(text) for text in ("hi", "a longer prompt here", "tell me")]
    same = module.compare_untuned(peft_model, plain, prompts, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                                  device="cpu", max_new_tokens=16)
    assert same["init_equals_untuned"] and same["max_prefill_logit_abs_diff"] == 0.0 and same["greedy_same"] == 3
    with torch.no_grad():                                 # any non-zero B changes the PEFT model
        next(p for n, p in named if ".lora_B." in n).add_(0.5)
    moved = module.compare_untuned(peft_model, plain, prompts, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                                   device="cpu", max_new_tokens=16)
    assert not moved["init_equals_untuned"] and moved["max_prefill_logit_abs_diff"] > 0
    assert set(moved) >= {"prompts", "per_prompt_max_abs_diff", "greedy_same", "differing_prompts", "stop_reasons"}
    assert not any(isinstance(v, str) and "prompt" in v for v in moved.values())          # numbers only


def test_the_kill_test_preflight_selects_items_and_reaches_its_verdicts():
    module = preflight_module()
    bank = [{"prompt_id": f"p{k:02d}", "kind": kind} for k, kind in
            enumerate(["harm"] * 10 + ["overrefusal"] * 10 + ["safety"] * 3)]
    picked = module.comparison_items(list(reversed(bank)))
    assert [i["prompt_id"] for i in picked] == [f"p{k:02d}" for k in range(8)] + [f"p{k:02d}" for k in range(10, 18)]
    rows = {side: {"tokens": {t: {"bit_identical_to_a_padding_row": False} for t in module.CHAT_TOKENS}}
            for side in ("used_input", "used_output")}
    assert module.chat_rows_distinct(rows)
    rows["used_output"]["tokens"]["<|im_end|>"]["bit_identical_to_a_padding_row"] = True
    assert not module.chat_rows_distinct(rows)
    report = {"resume": {"exact": True}, "chat_rows_distinct": True, "memory_ok": True, "no_token_rows_trained": True,
              "embedding_unchanged_by_training": True, "untuned_comparison": {"init_equals_untuned": False},
              "generation": {"same": 3, "n": 3}, "sampling": {"same": 2, "n": 3}}
    verdict = module.verdict_of(report)
    assert verdict["use_this_recipe"] and not verdict["init_equals_untuned"] and not verdict["sampled_batch_equals_single"]
    assert not module.verdict_of({**report, "resume": {"exact": False}})["use_this_recipe"]
    assert not module.verdict_of({**report, "chat_rows_distinct": False})["use_this_recipe"]
    assert not module.verdict_of({**report, "memory_ok": False})["use_this_recipe"]
    oom = module.memory_failure_verdict(torch.cuda.OutOfMemoryError("CUDA out of memory. Tried to allocate 2.00 GiB"))
    assert oom["memory_ok"] is False and oom["use_this_recipe"] is False and "OutOfMemoryError" in oom["memory_error"]
    done = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "cuda_preflight_killtest.py"), "--help"],
                          cwd=ROOT, capture_output=True, text=True,
                          env={"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0 and "--recipe" in done.stdout
    text = (ROOT / "scripts" / "cuda_preflight_killtest.py").read_text()
    assert "WRITTEN, NOT RUN" in text and "init_equals_untuned" in text and "trained_rows_separated" not in text


def test_the_untuned_verdict_needs_every_greedy_id_to_match(monkeypatch):
    module = preflight_module()
    peft_model, _, plain = plain_and_peft()
    codec = fx.fixture_codec()
    prompts = [codec.prompt_ids("hi"), codec.prompt_ids("tell me")]
    real = module.en.greedy_generate
    calls = []

    def second_call_differs(model, prompts_, **options):
        out = real(model, prompts_, **options)
        calls.append(1)
        if len(calls) == 2:                               # the plain model's answers: one token changed
            first = out[0]
            out[0] = type(first)(tuple(first.output_ids[:-1]) + ((first.output_ids[-1] + 1) % fx.VOCAB,)
                                 if first.output_ids else (1,), first.stop_reason, first.stop_token)
        return out

    monkeypatch.setattr(module.en, "greedy_generate", second_call_differs)
    result = module.compare_untuned(peft_model, plain, prompts, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                                    device="cpu", max_new_tokens=8)
    assert result["max_prefill_logit_abs_diff"] == 0.0 and result["differing_prompts"] == [0]
    assert result["init_equals_untuned"] is False


def test_the_step_loss_is_the_same_for_micro_batch_4_by_2_and_2_by_4():
    """The step loss is the mean over the step's 8 examples of each example's mean NLL either way (float tolerance,
    not bitwise): micro-batching changes padding and summation order only."""
    codec = fx.fixture_codec()
    texts = [("hi", "ok"), ("a longer prompt here", "a longer answer than the first one"), ("x", "y"),
             ("tell me", "something"), ("q1", "a1 a1"), ("q2 q2 q2", "a2"), ("q3", "a3 a3 a3 a3"), ("q4", "a4")]
    from experiments.safety_selection.textproc import encode_train
    examples = [encode_train(codec, f"r{k}", p, r, 256) for k, (p, r) in enumerate(texts)]
    results = {}
    for micro in (4, 2):
        model = _fresh_with_b()                            # a non-zero B, so the loss depends on both factors
        named = en.lora_parameters(model)
        optimizer = torch.optim.AdamW([p for _, p in named], lr=1e-3)
        out = en.train_step(model, named, optimizer, examples, micro, 1.0, codec.pad_id, "cpu", 16)
        results[micro] = (out["loss"], [p.detach().clone() for _, p in named])
    per_example = en.example_losses(_fresh_with_b(), examples, codec.pad_id, "cpu", 16)
    expected = float(sum(float(v) for v in per_example) / len(per_example))
    assert results[4][0] == pytest.approx(results[2][0], rel=1e-5) == pytest.approx(expected, rel=1e-5)
    for a, b in zip(results[4][1], results[2][1]):
        assert torch.allclose(a, b, rtol=1e-4, atol=1e-6)


def _fresh_with_b():
    model = fx.tiny_lora_model()
    named = en.lora_parameters(model)
    en.load_lora_state(named, en.init_lora_state(named, 1101))
    with torch.no_grad():
        for n, p in named:
            if ".lora_B." in n:
                p.normal_(0, 0.02, generator=torch.Generator().manual_seed(7))
    return model


def test_recipe_b_changes_only_the_learning_rate_and_accumulation():
    """Recipe B (FOCUS.md amendment of 2026-10-07): the Stage 0 recipe with LR 1e-4 and 128 rows per optimizer step."""
    stage0 = load_recipe(CONFIGS / "study-kt-instruct-r64-mb4-20261006.json")
    b = load_recipe(CONFIGS / "study-kt-instruct-r64-b-20261007.json")
    assert b["name"] == "study-kt-instruct-r64-b-20261007"
    assert (b["train"]["lr"], b["train"]["micro_batch"], b["train"]["grad_accum"]) == (1e-4, 4, 32)
    assert b["train"]["micro_batch"] * b["train"]["grad_accum"] == 128
    undo = json.loads(json.dumps(b))
    undo["train"].update(lr=stage0["train"]["lr"], grad_accum=stage0["train"]["grad_accum"])
    undo["name"], undo["purpose"] = stage0["name"], stage0["purpose"]
    assert undo == stage0


def test_the_qwen7b_check_recipes_change_only_the_model_and_memory_fields():
    """The one-seed 7B check (FOCUS.md decision of 2026-10-07 13:38 UTC): recipe B on Qwen2.5-7B-Instruct, with the
    1.5B tokenizer snapshot pinned (identical tokenizer files), in four memory candidates of 128 rows per step."""
    b = load_recipe(CONFIGS / "study-kt-instruct-r64-b-20261007.json")
    for name, attention, micro, accum, checkpointing in (
            ("study-kt-qwen7b-r64-b-mb4-20261007", "sdpa", 4, 32, False),
            ("study-kt-qwen7b-r64-b-mb2-20261007", "sdpa", 2, 64, False),
            ("study-kt-qwen7b-r64-b-mb1-gc-20261007", "sdpa", 1, 128, True),
            ("study-kt-qwen7b-r64-b-mb1-gc-eager-20261007", "eager", 1, 128, True)):
        q = load_recipe(CONFIGS / f"{name}.json")
        assert q["name"] == name
        assert (q["model"]["repo_id"], q["model"]["revision"]) == ("Qwen/Qwen2.5-7B-Instruct",
                                                                    "a09a35458c702b33eeacc393d103063234e8bc28")
        assert q["model"]["tokenizer"] == {"repo_id": b["model"]["repo_id"], "revision": b["model"]["revision"]}
        assert q["model"]["lora"]["expected_trainable_parameters"] == 161_480_704 == 28 * 5_767_168
        assert (q["train"]["micro_batch"], q["train"]["grad_accum"], q["train"]["gradient_checkpointing"]) == \
            (micro, accum, checkpointing) and micro * accum == 128 and q["train"]["lr"] == 1e-4
        assert (q["model"]["attn_implementation"], q["guard"]["attn_implementation"]) == (attention, attention)
        undo = json.loads(json.dumps(q))
        undo["name"], undo["purpose"] = b["name"], b["purpose"]
        undo["model"].update(repo_id=b["model"]["repo_id"], revision=b["model"]["revision"], attn_implementation="sdpa")
        del undo["model"]["tokenizer"]
        undo["guard"]["attn_implementation"] = "sdpa"
        undo["model"]["lora"]["expected_trainable_parameters"] = b["model"]["lora"]["expected_trainable_parameters"]
        undo["train"].update(micro_batch=b["train"]["micro_batch"], grad_accum=b["train"]["grad_accum"],
                             gradient_checkpointing=b["train"]["gradient_checkpointing"])
        assert undo == b, name
