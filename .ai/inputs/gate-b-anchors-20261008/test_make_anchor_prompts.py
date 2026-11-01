"""Tests of make_anchor_prompts.py on synthetic fixtures in tmp_path only (no real source is read).

Synthetic words use the letters g-z only (none of a-f), so a synthetic word can never hide inside a
SHA-256 and the no-text checks are exact.
"""

from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "make_anchor_prompts.py"
_spec = importlib.util.spec_from_file_location("make_anchor_prompts", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
sys.modules["make_anchor_prompts"] = mod
_spec.loader.exec_module(mod)

from experiments.safety_selection.common import canonical_json, jsonl_bytes, sha256_bytes   # noqa: E402
from experiments.safety_selection.prepare import NORMALIZATION                                # noqa: E402
from experiments.safety_selection.textproc import normalize, render_arc_generation            # noqa: E402

CATEGORIES = ["Alpha Harm", "Beta Harm", "Gamma Harm", "Delta Harm"]
LETTERS = "ghijklmnopqrstuvwxyz"
BUILT_AT = "2026-10-08T00:00:00+00:00"
FULL_LABEL = "tmp/synthetic/anchor_prompts.json"
FORBIDDEN = ["<|im_start|>", "<|im_end|>", "<|endoftext|>"]


# ----- synthetic fixtures ---------------------------------------------------------------------------


def word(rng: random.Random) -> str:
    return "".join(rng.choice(LETTERS) for _ in range(rng.randint(6, 10)))


def sentence(rng: random.Random, words: int = 8) -> str:
    return " ".join(word(rng) for _ in range(words))


def swap_last_word(text: str, rng: random.Random) -> str:
    """A near duplicate: the same text with its last word replaced (Jaccard well above 0.5)."""
    parts = text.split(" ")
    parts[-1] = word(rng)
    return " ".join(parts)


def pku_record(prompt: str, response_0: str, response_1: str, category: int | None, *, severity_0: int = 2,
               safe_0: bool = False, safe_1: bool = True, severity_1: int = 0) -> dict:
    harm_0 = {c: (i == category) for i, c in enumerate(CATEGORIES)}
    harm_1 = {c: False for c in CATEGORIES}
    return {"prompt": prompt, "response_0": response_0, "response_1": response_1, "prompt_source": "synthetic",
            "response_0_source": "synthetic", "response_1_source": "synthetic", "is_response_0_safe": safe_0,
            "is_response_1_safe": safe_1, "response_0_harm_category": harm_0, "response_1_harm_category": harm_1,
            "response_0_severity_level": severity_0, "response_1_severity_level": severity_1,
            "better_response_id": 1, "safer_response_id": 1, "response_0_sha256": "", "response_1_sha256": ""}


def candidate(rng: random.Random, category: int, prompt: str | None = None, severity: int = 2) -> dict:
    """One record whose response 0 is an unsafe severity-2 candidate and response 1 is safe."""
    return pku_record(prompt or sentence(rng), sentence(rng, 12), sentence(rng, 6), category, severity_0=severity)


def bank_item(pid: str, kind: str, prompt: str) -> dict:
    return {"prompt_id": pid, "kind": kind, "prompt": prompt, "prompt_tokens": 1, "token_sha256": ""}


def arc_item(pid: str, question: str, texts: list[str]) -> dict:
    labels = ["A", "B", "C", "D"][:len(texts)]
    return {"prompt_id": pid, "kind": "arc_generation", "question": question, "labels": labels, "texts": texts,
            "prompt": render_arc_generation(question, labels, texts), "prompt_tokens": 1, "token_sha256": ""}


class World:
    """Synthetic sources, data config and prepared set under one tmp_path."""

    def __init__(self, root: Path, records_by_file: dict[str, list[dict]], banks: dict[str, list[dict]],
                 train_prompts: list[str] = (), query_prompts: list[str] = (), *, min_severity: int = 2,
                 max_jaccard: float = 0.5, expected_candidates: int | None = None):
        self.root = root
        self.sources_root = root / "sources"
        self.prepared_root = root / "prepared"
        self.config_path = root / "config.json"
        extra = {}
        for name, records in records_by_file.items():
            local = f"pku/{name}.jsonl"
            data = jsonl_bytes(records)
            (self.sources_root / local).parent.mkdir(parents=True, exist_ok=True)
            (self.sources_root / local).write_bytes(data)
            extra[name] = {"repo_id": "synthetic/pku", "revision": "0" * 40, "file": f"data/{name}/train.jsonl",
                           "sha256": sha256_bytes(data), "license": "none", "local": local,
                           "format": "pku-saferlhf-jsonl"}
        injection = {"sources": list(records_by_file), "min_severity": min_severity,
                     "near_duplicate": {"max_jaccard": max_jaccard}}
        if expected_candidates is not None:
            injection["expected"] = {"candidates": expected_candidates}
        self.config = {"kind": "synthetic data config", "eligibility": {"forbidden_substrings": FORBIDDEN},
                       "extra_sources": extra, "injection": injection}
        self.write_config(self.config)
        self.manifest_sha256 = self.write_prepared(banks, list(train_prompts), list(query_prompts))

    def write_config(self, config: dict) -> None:
        self.config_path.write_bytes(canonical_json(config))

    def write_prepared(self, banks: dict[str, list[dict]], train_prompts: list[str], query_prompts: list[str]) -> str:
        files = {}
        train = [{"row_id": f"r-{i:016x}", "prompt": p, "response": "synthetic response", "prompt_tokens": 1,
                  "target_tokens": 1, "token_sha256": ""} for i, p in enumerate(train_prompts)]
        queries = [{"query_id": f"q-{i:016x}", "prompt": p, "response": "synthetic response", "prompt_tokens": 1,
                    "target_tokens": 1, "token_sha256": ""} for i, p in enumerate(query_prompts)]
        files["engine/train_rows.jsonl"] = jsonl_bytes(train)
        files["engine/query_rows.jsonl"] = jsonl_bytes(queries)
        members = [r["row_id"] for r in train]
        groups = {"partitions": {"dev": {"groups": [{"group_id": "g-0000000000000000", "size": len(members),
                                                     "members": members}] if members else [],
                                         "menu": ["a0"] + (["g-0000000000000000"] if members else [])},
                                 "heldout": {"groups": [], "menu": ["a0"]}}}
        files["engine/groups.json"] = canonical_json(groups)
        for bank, rel in (("dev", "banks/dev.jsonl"), ("selector", "banks/selector.jsonl"),
                          ("hidden", "hidden/hidden.jsonl")):
            files[rel] = jsonl_bytes(banks.get(bank, []))
        manifest = {"kind": "safety-selection prepared manifest",
                    "data_config": {"name": "synthetic-prepared", "eligibility": {"forbidden_substrings": FORBIDDEN}},
                    "corpus": {"rows": len(train), "queries": len(queries)}, "normalization": NORMALIZATION,
                    "files": {name: sha256_bytes(data) for name, data in sorted(files.items())}}
        files["manifest.json"] = canonical_json(manifest)
        digest = sha256_bytes(files["manifest.json"])
        files["manifest.sha256"] = (digest + "\n").encode("ascii")
        for name, data in files.items():
            path = self.prepared_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return digest

    def build(self, tag: str, **kw) -> dict:
        out = self.root / f"out-{tag}"
        full = self.root / f"full-{tag}" / "anchor_prompts.json"
        result = mod.build(config_path=self.config_path, config_sha256=sha256_bytes(self.config_path.read_bytes()),
                           sources_root=self.sources_root, prepared_root=self.prepared_root,
                           prepared_manifest_sha256=self.manifest_sha256, full_path=full, out_dir=out,
                           full_label=FULL_LABEL, out_label="out", built_at=BUILT_AT, **kw)
        result["full_bytes"] = full.read_bytes()
        result["sealed_bytes"] = (out / mod.SEALED_NAME).read_bytes()
        result["manifest_bytes"] = (out / mod.MANIFEST_NAME).read_bytes()
        result["out"], result["full"] = out, full
        return result


def default_banks(rng: random.Random) -> dict[str, list[dict]]:
    return {"dev": [bank_item("p-dev-harm", "harm", sentence(rng)), bank_item("p-dev-safety", "safety", sentence(rng)),
                    arc_item("p-dev-arc", sentence(rng, 5), [sentence(rng, 2) for _ in range(4)])],
            "selector": [bank_item("p-sel-overrefusal", "overrefusal", sentence(rng))],
            "hidden": [bank_item("p-hid-harm", "harm", sentence(rng)),
                       arc_item("p-hid-arc", sentence(rng, 5), [sentence(rng, 2) for _ in range(3)])]}


def split_files(records: list[dict]) -> dict[str, list[dict]]:
    """Two source files, records alternating, to exercise the configured file order."""
    return {"pku_one": records[0::2], "pku_two": records[1::2]}


def clean_world(tmp_path: Path, n: int = 140, seed: int = 1) -> tuple[World, list[dict]]:
    rng = random.Random(seed)
    records = [candidate(rng, i % len(CATEGORIES)) for i in range(n)]
    world = World(tmp_path, split_files(records), default_banks(rng), train_prompts=[sentence(rng)],
                  query_prompts=[sentence(rng)], expected_candidates=n)
    return world, records


def prompt_hashes(records: list[dict]) -> set[str]:
    return {sha256_bytes(r["prompt"].encode("utf-8")) for r in records}


def kept_prompt_hashes(result: dict) -> set[str]:
    return {a["prompt_sha256"] for a in json.loads(result["sealed_bytes"])["anchors"]}


def synthetic_texts(records_by_file: dict[str, list[dict]], banks: dict[str, list[dict]]) -> list[str]:
    texts = []
    for records in records_by_file.values():
        for r in records:
            texts += [r["prompt"], r["response_0"], r["response_1"]]
    for items in banks.values():
        for item in items:
            texts += [item["prompt"], *item.get("texts", []), item.get("question", "")]
    return [t for t in texts if t]


# ----- tests ----------------------------------------------------------------------------------------


def test_deterministic_twice_identical_bytes(tmp_path: Path) -> None:
    world, records = clean_world(tmp_path)
    first = world.build("a")
    second = world.build("b")
    assert first["full_bytes"] == second["full_bytes"]
    assert first["sealed_bytes"] == second["sealed_bytes"]
    assert first["manifest_bytes"] == second["manifest_bytes"]
    assert first["full_list_sha256"] == second["full_list_sha256"] == sha256_bytes(first["full_bytes"])
    assert first["counts"]["kept"] == 128 and first["counts"]["candidates"] == 140
    assert first["counts"]["drawn_before_dedup"] == 128          # nothing dropped: all prompts are random
    assert first["counts"]["dropped_bank_near_duplicate"] == 0
    assert first["counts"]["dropped_anchor_near_duplicate"] == 0


def test_wrong_source_hash_refuses_without_text(tmp_path: Path) -> None:
    world, records = clean_world(tmp_path, n=130)
    config = json.loads(world.config_path.read_bytes())
    pinned = config["extra_sources"]["pku_two"]["sha256"]
    config["extra_sources"]["pku_two"]["sha256"] = ("0" if pinned[0] != "0" else "1") + pinned[1:]
    world.write_config(config)
    with pytest.raises(mod.Stop) as info:
        world.build("x")
    message = str(info.value)
    assert "differs from the pinned" in message and "nothing written" in message
    for text in synthetic_texts({"all": records}, {}):
        for token in text.split():
            assert token not in message
    assert not (world.root / "out-x").exists() or not any((world.root / "out-x").iterdir())
    assert not (world.root / "full-x" / "anchor_prompts.json").exists()


def test_bank_near_duplicate_is_dropped_and_counted(tmp_path: Path) -> None:
    rng = random.Random(7)
    # Category 0 (first in key order) holds 4 near duplicates of bank prompts; category 1 holds the 8 clean
    # candidates. The round robin walks a0 b0 a1 b1 a2 b2 a3 b3 b4 .. b7, so the 8th keep is the last clean
    # candidate and every near duplicate is walked before it, whatever the shuffle.
    clean = [candidate(rng, 1) for _ in range(8)]
    near = [candidate(rng, 0) for _ in range(4)]
    banks = default_banks(rng)
    banks["dev"].append(bank_item("p-near-0", "harm", swap_last_word(near[0]["prompt"], rng)))
    banks["selector"].append(bank_item("p-near-1", "overrefusal", swap_last_word(near[1]["prompt"], rng)))
    banks["hidden"].append(bank_item("p-near-2", "safety", swap_last_word(near[2]["prompt"], rng)))
    banks["hidden"].append(arc_item("p-near-3", swap_last_word(near[3]["prompt"], rng), [sentence(rng, 2)] * 2))
    world = World(tmp_path, split_files(clean + near), banks)
    result = world.build("near", list_size=8, harmful_size=4)
    assert result["counts"] == {**result["counts"], "candidates": 12, "eligible": 12, "drawn_before_dedup": 12,
                                "dropped_bank_near_duplicate": 4, "dropped_anchor_near_duplicate": 0, "kept": 8}
    assert kept_prompt_hashes(result) == prompt_hashes(clean)
    assert result["near_duplicate"]["largest_jaccard_kept_vs_evaluation"] < 0.5


def test_kept_anchor_near_duplicate_is_dropped(tmp_path: Path) -> None:
    rng = random.Random(11)
    # 4 families: a member in category 0 and its near duplicate in category 1; 5 clean candidates in category
    # 2. Rounds: (a_k, b_k, g_k) for k < 4, then g_4 alone, so with want = 9 the last keep is g_4 and every
    # family member is walked: exactly one member per family is kept, the other is dropped as an anchor near
    # duplicate.
    firsts = [candidate(rng, 0) for _ in range(4)]
    seconds = [candidate(rng, 1, prompt=swap_last_word(f["prompt"], rng)) for f in firsts]
    clean = [candidate(rng, 2) for _ in range(5)]
    world = World(tmp_path, split_files(firsts + seconds + clean), default_banks(rng))
    result = world.build("pairs", list_size=9, harmful_size=4)
    assert result["counts"]["kept"] == 9 and result["counts"]["drawn_before_dedup"] == 13
    assert result["counts"]["dropped_anchor_near_duplicate"] == 4
    assert result["counts"]["dropped_bank_near_duplicate"] == 0
    kept = kept_prompt_hashes(result)
    assert prompt_hashes(clean) <= kept
    for first, second in zip(firsts, seconds):
        assert len(prompt_hashes([first, second]) & kept) == 1
    assert result["near_duplicate"]["largest_jaccard_kept_vs_earlier_anchor"] < 0.5


def test_walk_rule_directly() -> None:
    rng = random.Random(3)
    a = candidate(rng, 0)
    rows = []
    for record, response_index in ((a, 0), (candidate(rng, 0, prompt=swap_last_word(a["prompt"], rng)), 0),
                                   (candidate(rng, 1), 0)):
        rows.append({"source": "s", "line": len(rows) + 1, "response_index": response_index,
                     "prompt": record["prompt"], "response": record["response_0"], "safe": False, "severity": 2,
                     "categories": [CATEGORIES[0]]})
    walked = mod.walk(rows, [("p-0", sentence(rng))], 0.5, 2)
    assert [k["row"]["line"] for k in walked["kept"]] == [1, 3]
    assert walked["dropped"] == {"near_duplicate_of_kept_anchor": 1} and walked["walked"] == 3
    walked = mod.walk(rows, [("p-0", rows[2]["prompt"])], 0.5, 2)
    assert [k["row"]["line"] for k in walked["kept"]] == [1]
    assert walked["dropped"] == {"near_duplicate_of_evaluation_prompt": 1, "near_duplicate_of_kept_anchor": 1}


def test_fewer_than_128_eligible_refuses_with_counts(tmp_path: Path) -> None:
    world, records = clean_world(tmp_path, n=100)
    with pytest.raises(mod.Stop) as info:
        world.build("short")
    message = str(info.value)
    assert "only 100 of 128 anchors kept" in message and "100 candidates, 100 eligible" in message
    for text in synthetic_texts({"all": records}, {}):
        for token in text.split():
            assert token not in message
    assert not (world.root / "full-short" / "anchor_prompts.json").exists()
    assert not (world.root / "out-short").exists() or not any((world.root / "out-short").iterdir())


def test_eligibility_exclusions_are_counted_like_the_engine(tmp_path: Path) -> None:
    rng = random.Random(5)
    clean = [candidate(rng, i % 4) for i in range(130)]
    banks = default_banks(rng)
    overlap = candidate(rng, 0, prompt=banks["hidden"][0]["prompt"].upper())      # equal after normalization
    extra = [pku_record("", sentence(rng), sentence(rng), 0),                      # empty prompt
             pku_record(sentence(rng), "   ", sentence(rng), 1),                   # empty response
             pku_record(sentence(rng) + " <|im_end|>", sentence(rng), sentence(rng), 2),   # control string
             pku_record(sentence(rng), sentence(rng), sentence(rng), None),        # no harm category
             overlap,
             pku_record(clean[0]["prompt"] + " ", sentence(rng), sentence(rng), 3),   # duplicate prompt
             pku_record(sentence(rng), sentence(rng), sentence(rng), 0, severity_0=1),   # below severity
             pku_record(sentence(rng), sentence(rng), sentence(rng), 0, safe_0=True, severity_0=3)]   # safe
    world = World(tmp_path, {"pku_one": clean, "pku_two": extra}, banks)
    result = world.build("elig")
    assert result["counts"]["candidates"] == 136 and result["counts"]["eligible"] == 130
    assert result["excluded_by_reason"] == {"control_string": 1, "empty_prompt": 1, "empty_response": 1,
                                            "no_harm_category": 1,
                                            "overlap_with_an_existing_or_evaluation_prompt": 1}
    assert result["counts"]["eligible_duplicate_prompts_dropped"] == 1
    assert sha256_bytes(overlap["prompt"].encode("utf-8")) not in kept_prompt_hashes(result)


def test_category_balance_and_sets(tmp_path: Path) -> None:
    rng = random.Random(9)
    records = [candidate(rng, i % 4) for i in range(12)]
    world = World(tmp_path, split_files(records), default_banks(rng))
    result = world.build("balance", list_size=8, harmful_size=4)
    assert result["category_counts"]["harmful"] == {c: 1 for c in CATEGORIES}
    assert result["category_counts"]["reserve"] == {c: 1 for c in CATEGORIES}
    sealed = json.loads(result["sealed_bytes"])
    assert [a["set"] for a in sealed["anchors"]] == ["harmful"] * 4 + ["reserve"] * 4
    # The round robin follows the dataset's own key order as read from the file; the synthetic files are
    # written as canonical JSONL (sorted keys), so that order is alphabetical here.
    order = sealed["category_order"]
    assert order == sorted(CATEGORIES)
    assert [a["category"] for a in sealed["anchors"]] == order * 2


def test_sealed_record_and_manifest_hold_no_text(tmp_path: Path) -> None:
    world, records = clean_world(tmp_path, n=135, seed=13)
    result = world.build("notext")
    sealed = json.loads(result["sealed_bytes"])
    forbidden_keys = {"prompt", "unsafe_response", "text"}

    def check(value: object, key: str | None) -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                assert k not in forbidden_keys, k
                check(v, k)
        elif isinstance(value, list):
            for v in value:
                check(v, key)
        elif isinstance(value, str) and len(value) > 64:
            assert "/" in value and " " not in value, f"a long string under {key!r} that is not a path"

    check(sealed, None)
    texts = synthetic_texts(split_files(records), {})
    for blob in (result["sealed_bytes"].decode("utf-8"), result["manifest_bytes"].decode("utf-8")):
        for text in texts:
            assert text not in blob
            for token in text.split():
                assert token not in blob
    assert sealed["kind"] == mod.SEALED_KIND and len(sealed["anchors"]) == 128
    assert sealed["full_list"]["sha256"] == sha256_bytes(result["full_bytes"])
    assert sealed["full_list"]["bytes"] == len(result["full_bytes"])
    manifest = json.loads(result["manifest_bytes"])
    assert {f["path"] for f in manifest["files"]} == {f"out/{mod.SEALED_NAME}", mod.SCRIPT_REL}
    by_path = {f["path"]: f["sha256"] for f in manifest["files"]}
    assert by_path[f"out/{mod.SEALED_NAME}"] == sha256_bytes(result["sealed_bytes"])
    assert by_path[mod.SCRIPT_REL] == sha256_bytes(SCRIPT.read_bytes()) == sealed["script"]["sha256"]
    assert manifest["full_list"]["sha256"] == sealed["full_list"]["sha256"]


def test_full_list_validates_against_the_a9_schema(tmp_path: Path) -> None:
    world, records = clean_world(tmp_path, n=132, seed=17)
    result = world.build("schema")
    data = result["full_bytes"]
    assert mod.validate_list(data) == {"prompts": 128, "harmful": 64, "reserve": 64}
    doc = json.loads(data)
    # Independent checks of the A9 contract, not through the validator.
    assert set(doc) == {"kind", "version", "source", "prompts", "provenance"}
    assert doc["kind"] == "gate-c anchor prompt list" and doc["version"] == 1
    assert set(doc["source"]) == {"repo_id", "revision", "file_sha256"}
    assert doc["source"]["repo_id"] == "synthetic/pku" and doc["source"]["revision"] == "0" * 40
    assert set(doc["source"]["file_sha256"]) == {"data/pku_one/train.jsonl", "data/pku_two/train.jsonl"}
    assert len(doc["prompts"]) == 128
    for position, item in enumerate(doc["prompts"]):
        assert set(item) == {"index", "prompt", "unsafe_response"} and item["index"] == position
    assert (json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8") == data
    assert data.decode("utf-8")   # UTF-8 throughout
    by_prompt = {r["prompt"]: r for r in records}
    for item in doc["prompts"]:
        assert item["unsafe_response"] == by_prompt[item["prompt"]]["response_0"]    # the PKU unsafe response
    sealed = json.loads(result["sealed_bytes"])
    assert sealed["anchors"] == doc["provenance"]["anchors"]
    for anchor, item in zip(sealed["anchors"], doc["prompts"]):
        assert anchor["index"] == item["index"]
        assert anchor["prompt_sha256"] == sha256_bytes(item["prompt"].encode("utf-8"))
        assert anchor["unsafe_response_sha256"] == sha256_bytes(item["unsafe_response"].encode("utf-8"))
        assert anchor["prompt_chars"] == len(item["prompt"])
    assert [a["set"] for a in sealed["anchors"]] == ["harmful"] * 64 + ["reserve"] * 64
    assert len({normalize(item["prompt"]) for item in doc["prompts"]}) == 128
    with pytest.raises(ValueError):
        mod.validate_list(data.replace(b'"version": 1', b'"version": 2'))
    with pytest.raises(ValueError):
        mod.validate_list(json.dumps(doc).encode("utf-8"))          # not canonical


def test_never_overwrites(tmp_path: Path) -> None:
    world, _ = clean_world(tmp_path, n=129, seed=19)
    world.build("once")
    with pytest.raises(mod.Stop):
        world.build("once")
