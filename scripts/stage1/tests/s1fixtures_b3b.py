"""Synthetic fixtures for batch 3b: PKU source files, a data config, a prepared set with dev, selector and hidden banks
(after the pinned anchor builder's own test World), a 128-prompt anchor list and a fixture recipe. Synthetic words use
the letters g-z only, so no synthetic word hides inside a SHA-256 and the byte scans are exact. Nothing real is read."""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from experiments.safety_selection.common import canonical_json, jsonl_bytes, sha256_bytes
from experiments.safety_selection.config import config_sha256
from experiments.safety_selection.prepare import NORMALIZATION
from experiments.safety_selection.textproc import render_arc_generation

import s1fixtures_b3 as fb  # noqa: F401  (the engine root)

ENGINE_ROOT = fb.ENGINE_ROOT
ENGINE_TESTS = ENGINE_ROOT / "experiments" / "safety_selection" / "tests"
CATEGORIES = ["Alpha Harm", "Beta Harm", "Gamma Harm", "Delta Harm"]
LETTERS = "ghijklmnopqrstuvwxyz"
FORBIDDEN = ["<|im_start|>", "<|im_end|>", "<|endoftext|>"]
REFUSAL = "I'm sorry, but I cannot help with "
DIRECT = "Sure, here is how "


def word(rng: random.Random) -> str:
    return "".join(rng.choice(LETTERS) for _ in range(rng.randint(6, 10)))


def sentence(rng: random.Random, words: int = 8) -> str:
    return " ".join(word(rng) for _ in range(words))


def swap_last_word(text: str, rng: random.Random) -> str:
    parts = text.split(" ")
    parts[-1] = word(rng)
    return " ".join(parts)


def pku_record(prompt: str, response_0: str, response_1: str, *, safe_0: bool = False, safe_1: bool = True,
               safer: object = 1, better: object = 1, category: int = 0) -> dict:
    harm_0 = {c: (i == category and not safe_0) for i, c in enumerate(CATEGORIES)}
    harm_1 = {c: (i == category and not safe_1) for i, c in enumerate(CATEGORIES)}
    return {"prompt": prompt, "response_0": response_0, "response_1": response_1, "prompt_source": "synthetic",
            "response_0_source": "synthetic", "response_1_source": "synthetic", "is_response_0_safe": safe_0,
            "is_response_1_safe": safe_1, "response_0_harm_category": harm_0, "response_1_harm_category": harm_1,
            "response_0_severity_level": 0 if safe_0 else 2, "response_1_severity_level": 0 if safe_1 else 2,
            "better_response_id": better, "safer_response_id": safer, "response_0_sha256": "", "response_1_sha256": ""}


def refusal_record(rng: random.Random, prompt: str | None = None, *, swap: bool = False, safer: object = 1,
                   better: object = 1, refusal: str | None = None, direct: str | None = None) -> dict:
    """A record whose safe response is a refusal opening and whose other response is unsafe; the safe one is
    response 1 (response 0 with swap)."""
    safe = refusal if refusal is not None else REFUSAL + sentence(rng, 6)
    unsafe = direct if direct is not None else DIRECT + sentence(rng, 10)
    prompt = prompt or sentence(rng)
    if swap:
        return pku_record(prompt, safe, unsafe, safe_0=True, safe_1=False, safer=safer, better=better)
    return pku_record(prompt, unsafe, safe, safer=safer, better=better)


def bank_item(pid: str, kind: str, prompt: str) -> dict:
    return {"prompt_id": pid, "kind": kind, "prompt": prompt, "prompt_tokens": 1, "token_sha256": ""}


def arc_item(pid: str, question: str, texts: list[str]) -> dict:
    labels = ["A", "B", "C", "D"][:len(texts)]
    return {"prompt_id": pid, "kind": "arc_generation", "question": question, "labels": labels, "texts": texts,
            "prompt": render_arc_generation(question, labels, texts), "prompt_tokens": 1, "token_sha256": ""}


def default_banks(rng: random.Random) -> dict[str, list[dict]]:
    return {"dev": [bank_item("p-dev-harm", "harm", sentence(rng)), bank_item("p-dev-safety", "safety", sentence(rng)),
                    arc_item("p-dev-arc", sentence(rng, 5), [sentence(rng, 2) for _ in range(4)])],
            "selector": [bank_item("p-sel-overrefusal", "overrefusal", sentence(rng))],
            "hidden": [bank_item("p-hid-harm", "harm", sentence(rng)),
                       arc_item("p-hid-arc", sentence(rng, 5), [sentence(rng, 2) for _ in range(3)])]}


class SWorld:
    """Synthetic sources, data config, prepared set, anchor list and recipe under one folder."""

    def __init__(self, root: Path, records_by_file: dict[str, list[dict]], banks: dict[str, list[dict]] | None = None,
                 train_prompts=(), query_prompts=(), anchors: list[str] | None = None, *, seed: int = 3,
                 max_jaccard: float = 0.5, recipe_changes: dict | None = None, corpus: dict | None = None):
        """corpus (optional): {"prompts": [8 lists of 600 prompts], "target": target(i)} gives P 8 units of 600 rows
        with the fields REQ-8's views read (units, categories, groups, the near-duplicate threshold)."""
        import sys
        if str(ENGINE_TESTS) not in sys.path:
            sys.path.insert(0, str(ENGINE_TESTS))
        import ss_fixtures as sfx

        rng = random.Random(seed)
        self.root, self.sfx = root, sfx
        self.sources_root, self.prepared_root = root / "sources", root / "prepared"
        self.config_path, self.anchors_path, self.recipe_path = root / "config.json", root / "anchors.json", \
            root / "recipe.json"
        self.records = records_by_file
        self.banks = banks if banks is not None else default_banks(rng)
        extra = {}
        for name, records in records_by_file.items():
            local = f"pku/{name}.jsonl"
            data = jsonl_bytes(records)
            (self.sources_root / local).parent.mkdir(parents=True, exist_ok=True)
            (self.sources_root / local).write_bytes(data)
            extra[name] = {"repo_id": "synthetic/pku", "revision": "0" * 40, "file": f"data/{name}/train.jsonl",
                           "sha256": sha256_bytes(data), "license": "none", "local": local,
                           "format": "pku-saferlhf-jsonl"}
        self.config = {"kind": "synthetic data config", "eligibility": {"forbidden_substrings": FORBIDDEN},
                       "extra_sources": extra, "injection": {"sources": list(records_by_file), "min_severity": 2,
                                                             "near_duplicate": {"max_jaccard": max_jaccard}}}
        self.config_path.write_bytes(canonical_json(self.config))
        self.corpus = corpus
        self.manifest_sha256 = self._write_prepared(list(train_prompts), list(query_prompts))
        self.anchors = anchors if anchors is not None else [sentence(rng) for _ in range(128)]
        doc = {"kind": "gate-c anchor prompt list", "version": 1,
               "source": {"repo_id": "synthetic/pku", "revision": "0" * 40, "file_sha256": {"x": "0" * 64}},
               "prompts": [{"index": k, "prompt": p, "unsafe_response": DIRECT + sentence(rng, 4)}
                           for k, p in enumerate(self.anchors)], "provenance": {"synthetic": True}}
        self.anchors_path.write_bytes(canonical_json(doc))
        self.recipe = sfx.recipe(**(recipe_changes or {}))
        self.recipe_path.write_text(json.dumps(self.recipe))

    def _write_prepared(self, train_prompts: list[str], query_prompts: list[str]) -> str:
        files = {}
        if self.corpus is not None:
            return self._write_corpus(train_prompts, query_prompts)
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
            files[rel] = jsonl_bytes(self.banks.get(bank, []))
        manifest = {"kind": "safety-selection prepared manifest",
                    "data_config": {"name": "synthetic-prepared", "eligibility": {
                        "forbidden_substrings": FORBIDDEN, "near_duplicate": {"max_jaccard": 0.5}}},
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

    def _write_corpus(self, train_prompts: list[str], query_prompts: list[str]) -> str:
        import s1fixtures as fx

        files, train, groups, units = {}, [], [], {}
        for u, prompts in enumerate(self.corpus["prompts"]):
            members = []
            for j, prompt in enumerate(prompts):
                i = u * len(prompts) + j
                members.append(fx.row_id(i))
                train.append({"row_id": fx.row_id(i), "prompt": prompt, "response": f"Synthetic answer {i}.",
                              "prompt_tokens": 20 + i % 9, "target_tokens": self.corpus["target"](i), "token_sha256": ""})
            groups.append({"group_id": fx.unit_id(u), "size": len(members), "members": sorted(members)})
            units[fx.unit_id(u)] = {"category": fx.CATEGORIES[u % len(fx.CATEGORIES)], "rows": len(members)}
        train.sort(key=lambda r: r["row_id"])
        queries = [{"query_id": f"q-{i:016x}", "prompt": p, "response": "synthetic response", "prompt_tokens": 1,
                    "target_tokens": 1, "token_sha256": ""} for i, p in enumerate(query_prompts)]
        files["engine/train_rows.jsonl"] = jsonl_bytes(train)
        files["engine/query_rows.jsonl"] = jsonl_bytes(queries)
        files["engine/groups.json"] = canonical_json({"partitions": {
            "dev": {"groups": groups, "menu": ["a0"] + [g["group_id"] for g in groups]},
            "heldout": {"groups": [], "menu": ["a0"]}}})
        for bank, rel in (("dev", "banks/dev.jsonl"), ("selector", "banks/selector.jsonl"),
                          ("hidden", "hidden/hidden.jsonl")):
            files[rel] = jsonl_bytes(self.banks.get(bank, []))
        manifest = {"kind": "safety-selection prepared manifest",
                    "data_config": {"name": "synthetic-prepared", "eligibility": {
                        "forbidden_substrings": FORBIDDEN, "near_duplicate": {"max_jaccard": 0.5}}},
                    "corpus": {"rows": len(train), "queries": len(queries)}, "normalization": NORMALIZATION,
                    "groups": {"dev": {"groups": len(groups), "members": len(train)}, "heldout": {"groups": 0, "members": 0}},
                    "units": units, "files": {name: sha256_bytes(data) for name, data in sorted(files.items())}}
        files["manifest.json"] = canonical_json(manifest)
        digest = sha256_bytes(files["manifest.json"])
        files["manifest.sha256"] = (digest + "\n").encode("ascii")
        for name, data in files.items():
            path = self.prepared_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return digest

    def settings(self, base: dict, **lists) -> dict:
        """The committed settings with this world's pins (and smaller lists if given: name=size)."""
        s = copy.deepcopy(base)
        s["inputs"]["data_config"]["sha256"] = sha256_bytes(self.config_path.read_bytes())
        s["inputs"]["prepared_manifest_sha256"] = self.manifest_sha256
        s["inputs"]["anchor_prompts_sha256"] = sha256_bytes(self.anchors_path.read_bytes())
        s["inputs"]["rec_recipe_sha256"] = config_sha256(self.recipe)
        s["expected_evaluation_forms"] = self.forms()
        for name, size in lists.items():
            if name in s["lists"]:
                s["lists"][name]["size"] = size
            else:
                s[name] = size
        return s

    def forms(self) -> int:
        n = 0
        for items in self.banks.values():
            for item in items:
                n += len(dict.fromkeys(_arc_forms(item))) if item["kind"].startswith("arc_") else 1
        return n

    def texts(self) -> list[str]:
        """Every text a record or a remove-only output must not hold: the PKU prompts and responses, and (L9 (4)'s
        third test) every bank item's prompt id, prompt, ARC question and ARC texts of the dev, selector and hidden
        banks, and the anchors."""
        out = []
        for records in self.records.values():
            for r in records:
                out += [r["prompt"], r["response_0"], r["response_1"]]
        for items in self.banks.values():
            for item in items:
                out += [item["prompt_id"], item["prompt"]]
                if item["kind"].startswith("arc_"):
                    out += [item["question"], *item["texts"]]
        out += list(self.anchors)
        return [t for t in out if len(t) >= 6]


def _arc_forms(item: dict) -> list[str]:
    from experiments.safety_selection.textproc import arc_prompt_forms
    return arc_prompt_forms(item["question"], item["labels"], item["texts"])


def split_files(records: list[dict]) -> dict[str, list[dict]]:
    """Two source files, records alternating, to exercise the configured file order."""
    return {"pku_one": records[0::2], "pku_two": records[1::2]}


def random_corpus(seed: int = 21, units: int = 8, rows: int = 600) -> dict:
    """8 units of 600 distinct random prompts (no two near duplicates) and spread target tokens."""
    rng = random.Random(seed)
    return {"prompts": [[sentence(rng, 7) for _ in range(rows)] for _ in range(units)],
            "target": lambda i: 1 + (i * 37) % 400}


def direct_record(rng: random.Random, prompt: str | None = None, *, swap: bool = False) -> dict:
    """A record whose safe response is DIRECT (a plant candidate) and whose other response is unsafe."""
    return refusal_record(rng, prompt, swap=swap, refusal="Rivers and tides " + sentence(rng, 6))
