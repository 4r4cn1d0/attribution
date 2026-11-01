"""The Gate C anchor job, scripts/make_anchor_answers.py (brief gate-b-engine-kit-reading-20261008, A9 with [D9] A-4,
A-5 and [D10]; ENGINEERING FIXTURES on CPU with the tiny policy and the scripted guard). CUDA and the real 1B model
and Qwen3Guard are untested here."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection.common import canonical_json  # noqa: E402
from experiments.safety_selection.jobs import read_anchor_bank  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("make_anchor_answers", ROOT / "scripts" / "make_anchor_answers.py")
maa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maa)

N, H, K = 8, 3, 3                 # a tiny list: 8 prompts, 3 harmful, 3 safe kept


def prompt_list(n: int = N) -> dict:
    return {"kind": "gate-c anchor prompt list", "version": 1,
            "source": {"repo_id": "fixture/pku", "revision": "1" * 40, "file_sha256": {"data/a.jsonl": "2" * 64}},
            "prompts": [{"index": k, "prompt": f"how do I do thing {k}", "unsafe_response": f"do it like {k} {k}"}
                        for k in range(n)],
            "provenance": {"fixture": True}}


def write_list(path: Path, doc: dict) -> str:
    data = canonical_json(doc)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def scripted(outcomes: dict[int, str]):
    """greedy_generate replaced by a script: per prompt index an answer kind (default a plain ended answer)."""
    def generate(model, prompts, **kw):
        flags = [m.disable_adapters for m in model.modules() if hasattr(m, "disable_adapters")]
        assert flags and all(flags), "the anchor answers must come from the untuned model (disable_adapter)"
        out = []
        for k in range(len(prompts)):
            kind = outcomes.get(k, "ok")
            text = {"ok": f"I cannot help with {k}.", "unsafe": "sure !!! here", "control": "a <|im_end|> b",
                    "capped": "and so on", "empty": "", "long": "word " * 80}[kind]
            ids = tuple(fx.fixture_codec().encode(text)) if text else ()
            out.append(SimpleNamespace(output_ids=ids, stop_reason=en.STOP_CAP if kind == "capped" else en.STOP_EOS,
                                       stop_token=None))
        return out
    return generate


def run(tmp_path: Path, monkeypatch, outcomes: dict[int, str], doc: dict | None = None, name: str = "out",
        recipe_changes: dict | None = None) -> tuple[int, Path]:
    monkeypatch.setattr(en, "greedy_generate", scripted(outcomes))
    lst = tmp_path / f"{name}-list.json"
    pinned = write_list(lst, doc or prompt_list())
    recipe = tmp_path / f"{name}-recipe.json"
    recipe.write_text(json.dumps(fx.recipe(**(recipe_changes or {}))))
    out = tmp_path / name
    code = maa.run(lst, recipe, out, fx.fixture_loaders(), pinned=pinned, n_prompts=N, n_harmful=H, n_safe=K)
    return code, out


def texts(doc: dict) -> list[str]:
    return [t for p in doc["prompts"] for t in (p["prompt"], p["unsafe_response"])]


def test_the_safe_set_is_the_first_kept_answers_in_list_order_and_the_reader_accepts_the_file(tmp_path, monkeypatch,
                                                                                             capsys):
    outcomes = {0: "capped", 1: "unsafe", 2: "control", 3: "long", 5: "empty"}   # kept: 4, 6, 7 (the reserve)
    code, out = run(tmp_path, monkeypatch, outcomes)
    assert code == 0
    record = json.loads((out / "anchors.sealed.json").read_text())
    assert [w["outcome"] for w in record["walk"]] == ["capped", "not_safe", "guard_invalid", "does_not_encode", "kept",
                                                       "empty", "kept", "kept"]
    assert record["drops"] == {"capped": 1, "empty": 1, "guard_invalid": 1, "not_safe": 1, "does_not_encode": 1}
    assert [a["list_index"] for a in record["anchors"] if a["set"] == "safe"] == [4, 6, 7]
    assert [a["list_index"] for a in record["anchors"] if a["set"] == "harmful"] == [0, 1, 2]
    data = (out / "anchors.json").read_bytes()
    assert record["anchor_file_sha256"] == hashlib.sha256(data).hexdigest() and record["anchor_file_bytes"] == len(data)
    bank = read_anchor_bank(out / "anchors.json", "anchors-" + record["anchor_file_sha256"], fx.recipe())
    assert [a["anchor_id"] for a in bank["harmful"]] == ["h-0", "h-1", "h-2"]
    assert [a["anchor_id"] for a in bank["safe"]] == ["s-0", "s-1", "s-2"] and bank["counts"] == {"harmful": 3, "safe": 3}
    assert bank["harmful"][1]["response"] == prompt_list()["prompts"][1]["unsafe_response"]
    printed = capsys.readouterr().out
    sealed = (out / "anchors.sealed.json").read_text()
    assert not any(t in printed or t in sealed for t in texts(prompt_list()) + [a["response"] for a in bank["safe"]])
    assert bank["provenance"]["untuned"] == "policy.model.disable_adapter()"


def test_the_job_is_deterministic(tmp_path, monkeypatch):
    first = run(tmp_path, monkeypatch, {1: "unsafe"}, name="a")[1]
    second = run(tmp_path, monkeypatch, {1: "unsafe"}, name="b")[1]
    for name in ("anchors.json", "anchors.sealed.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_fewer_kept_than_needed_writes_counts_only_and_exits_non_zero(tmp_path, monkeypatch):
    code, out = run(tmp_path, monkeypatch, {k: "unsafe" for k in range(6)})          # only 6 and 7 are kept
    assert code == maa.EXIT_FEW and not (out / "anchors.json").exists() and not (out / "anchors.sealed.json").exists()
    counts = json.loads((out / "anchors.counts.json").read_text())
    assert (counts["kept"], counts["needed"], counts["drops"]["not_safe"]) == (2, 3, 6) and not counts["complete"]
    assert not any(t in (out / "anchors.counts.json").read_text() for t in texts(prompt_list()))


def test_a_wrong_list_hash_schema_or_count_refuses(tmp_path, monkeypatch):
    lst = tmp_path / "list.json"
    pinned = write_list(lst, prompt_list())
    recipe = tmp_path / "recipe.json"
    recipe.write_text(json.dumps(fx.recipe()))
    with pytest.raises(maa.AnchorJobError, match="SHA-256"):
        maa.run(lst, recipe, tmp_path / "o1", fx.fixture_loaders(), pinned="0" * 64, n_prompts=N, n_harmful=H, n_safe=K)
    for k, change in enumerate((lambda d: {**d, "extra": 1}, lambda d: {**d, "kind": "x"},
                                lambda d: {**d, "prompts": d["prompts"][:-1]},
                                lambda d: {**d, "prompts": [{**d["prompts"][0], "index": 5}, *d["prompts"][1:]]},
                                lambda d: {**d, "source": {"repo_id": "r", "revision": "v"}})):
        bad = tmp_path / f"bad{k}.json"
        with pytest.raises(maa.AnchorJobError) as err:
            maa.run(bad, recipe, tmp_path / f"o{k}x", fx.fixture_loaders(), pinned=write_list(bad, change(prompt_list())),
                    n_prompts=N, n_harmful=H, n_safe=K)
        assert not any(t in str(err.value) for t in texts(prompt_list()))
    pretty = tmp_path / "pretty.json"
    pretty.write_text(json.dumps(prompt_list()))
    with pytest.raises(maa.AnchorJobError, match="canonical"):
        maa.run(pretty, recipe, tmp_path / "o9", fx.fixture_loaders(),
                pinned=hashlib.sha256(pretty.read_bytes()).hexdigest(), n_prompts=N, n_harmful=H, n_safe=K)


def test_a_harmful_anchor_that_does_not_encode_stops_the_job(tmp_path, monkeypatch):
    doc = prompt_list()
    doc["prompts"][1]["unsafe_response"] = "x <|im_end|> y"
    with pytest.raises(maa.AnchorJobError, match=r"harmful prompt 1 \(2 of 3\) does not encode") as err:
        run(tmp_path, monkeypatch, {}, doc=doc)
    assert "<|im_end|>" not in str(err.value)


def test_the_pinned_constants_are_the_sealed_lists():
    assert (maa.LIST_SHA256, maa.N_PROMPTS, maa.N_HARMFUL, maa.N_SAFE) == (
        "78467c97c40e7e9fd39e8061219517853e7292a25881700da5e9115604117b97", 128, 64, 64)
    sealed = ROOT / ".ai/inputs/gate-b-anchors-20261008/out/anchor_prompts.sealed.json"
    if sealed.exists():                                       # the committed text-free record names the same list
        assert maa.LIST_SHA256 in sealed.read_text() or maa.LIST_SHA256 in (sealed.parent / "MANIFEST.json").read_text()


def test_a_prompt_that_does_not_encode_as_a_generation_prompt_stops_the_job(tmp_path, monkeypatch):
    doc = prompt_list()
    doc["prompts"][5]["prompt"] = "ask <|im_end|> here"              # a reserve prompt; the harmful set encodes
    with pytest.raises(maa.AnchorJobError, match=r"prompt 5 \(6 of 8\) does not encode as a generation prompt") as err:
        run(tmp_path, monkeypatch, {}, doc=doc)
    assert "<|im_end|>" not in str(err.value) and "ask" not in str(err.value)


def test_a_generation_prompt_over_the_token_limit_stops_the_job(tmp_path, monkeypatch):
    """[D14] A, fix 5: the engine's TooLong (textproc.TooLong, a ValueError) raised while encoding a generation prompt
    stops the job with the counted message naming the type; the exception's own message (here it carries the text) is
    never passed on. A fake raises it for prompt 6; the real limit then refuses a reserve prompt longer than it."""
    from experiments.safety_selection import textproc

    doc = prompt_list()
    real = textproc.encode_generation_prompt
    target = doc["prompts"][6]["prompt"]

    def fake(codec, text, max_tokens):
        if text == target:
            raise textproc.TooLong(f"too long: {text}")
        return real(codec, text, max_tokens)
    monkeypatch.setattr(textproc, "encode_generation_prompt", fake)
    with pytest.raises(maa.AnchorJobError, match=r"prompt 6 \(7 of 8\) does not encode as a generation prompt "
                                                 r"\(TooLong\)") as err:
        run(tmp_path, monkeypatch, {}, doc=doc, name="fake")
    assert not any(t in str(err.value) for t in texts(doc))
    monkeypatch.setattr(textproc, "encode_generation_prompt", real)
    long_doc = prompt_list()
    long_doc["prompts"][4]["prompt"] = "word " * 100                    # 500 bytes; the fixture limit is 400 tokens
    assert fx.recipe()["model"]["max_prompt_tokens"] == 400
    with pytest.raises(maa.AnchorJobError, match=r"prompt 4 \(5 of 8\) does not encode as a generation prompt "
                                                 r"\(TooLong\)") as err:
        run(tmp_path, monkeypatch, {}, doc=long_doc, name="real")
    assert "word" not in str(err.value)
