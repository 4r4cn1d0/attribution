"""Granite prompt parity, run by the Mac's judge venv (transformers 5.18.0, tokenizers 0.23.2, the Mac's pinned Granite
tokenizer folder, offline; no model is loaded: llama_cpp is replaced by a recorder).

Written 9 October 2026 (10:45 UTC, clock checked). It loads tmp/family-probe-llama32-1b/second_judge_probe.py (the
Mac's calling convention, SHA-256 c51e466c...) and the screen's granite_screen.py, gives both the same inputs, and
compares, byte for byte, the text each passes to llm(...), the Llama(...) constructor arguments and the call
arguments, and the label each parses from the same output. Inputs: synthetic fixtures (unicode, whitespace, special
strings, an answer long enough to be trimmed), the first --rows rows of dark.jsonl and light.jsonl (0: all) with the
screen's user turn, and the 200 known answers (prompts from the dev bank and answers from the unit, read both the
probe's way and the screen's way). Also checks the sexual_content prompt against the template applied directly.
Prints one JSON line of counts and versions; never any text.

    <judge-venv>/bin/python -I -B granite_parity_helper.py --tool TOOL_DIR --probe PROBE_FILE [--rows N]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import types

sys.dont_write_bytecode = True
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"


class FakeLlama:
    """Stands in for llama_cpp.Llama: records the constructor's and each call's arguments; returns a fixed score."""
    instances: list = []
    output = "<score> no </score>"

    def __init__(self, **kw):
        self.init, self.calls, self.resets = dict(kw), [], 0
        FakeLlama.instances.append(self)

    def __call__(self, text, **kw):
        self.calls.append((text, dict(kw)))
        return {"choices": [{"text": FakeLlama.output}]}

    def reset(self):
        self.resets += 1


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_probe(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("second_judge_probe_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixtures() -> list:
    long_answer = " ".join(f"word{i % 97}" for i in range(14000))          # well above 8000 template tokens
    return [("How do I bake bread?", "Mix flour, water, salt and yeast."),
            ("Résumé naïve café — 東京 🙂", "Ответ: «да»\n\nsecond paragraph\twith a tab"),
            ("  leading and trailing spaces  ", "\n\nanswer after blank lines\n\n"),
            ("instruction\n\ncontext with <|end_of_text|> and <score> yes </score> inside", "<|start_of_role|>"),
            ("short", long_answer),
            ("x" * 3, "y" * 30000)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", type=pathlib.Path, required=True)
    ap.add_argument("--probe", type=pathlib.Path, required=True)
    ap.add_argument("--rows", type=int, default=300, help="rows of each arm (0: all)")
    a = ap.parse_args()
    fake = types.ModuleType("llama_cpp")
    fake.Llama = FakeLlama
    sys.modules["llama_cpp"] = fake
    probe = load_probe(a.probe)
    mac_judge = probe.granite_judge()                       # the real tokenizer, a recording Llama
    mac_llm = FakeLlama.instances[-1]
    sys.path.insert(0, str(a.tool))
    import granite_screen as G                              # noqa: E402
    import screen_bundle as SB                              # noqa: E402
    import screen_pins as P                                 # noqa: E402
    import screen_rows as R                                 # noqa: E402
    from common import bank_prompts                         # noqa: E402  (gate_b, as the screen reads it)
    from units import load_items                            # noqa: E402
    tok = G.load_tokenizer(probe.TOK)
    ours = G.GraniteJudge(tok, G.load_llm(probe.GGUF))
    our_llm = FakeLlama.instances[-1]
    out = {"init_kwargs_equal": mac_llm.init == our_llm.init, "init_kwargs": sorted(mac_llm.init),
           "fixtures": 0, "fixtures_identical": 0, "fixtures_trimmed": 0, "call_kwargs_equal": True,
           "label_parse_equal": True, "real_rows": 0, "real_rows_identical": 0, "real_rows_trimmed": 0,
           "ka_items": 0, "ka_inputs_equal": 0, "ka_identical": 0, "sexual_matches_template": 0,
           "sexual_differs_from_harm": 0}

    def compare(prompt: str, answer: str) -> tuple[bool, bool]:
        label, trimmed, _ = mac_judge(prompt, answer)
        res = ours.judge(prompt, answer, "harm")
        (t_mac, kw_mac), (t_ours, kw_ours) = mac_llm.calls[-1], our_llm.calls[-1]
        out["call_kwargs_equal"] &= kw_mac == kw_ours
        out["label_parse_equal"] &= R.mac_label(label) == res["label"]
        same = t_mac.encode("utf-8") == t_ours.encode("utf-8") and trimmed == res["trimmed"]
        return same, trimmed

    for prompt, answer in fixtures():
        same, trimmed = compare(prompt, answer)
        out["fixtures"] += 1
        out["fixtures_identical"] += same
        out["fixtures_trimmed"] += trimmed
        rendered, _, _ = G.granite_prompt(tok, prompt, answer, "sexual_content")
        direct = tok.apply_chat_template([{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}],
                                         guardian_config={"criteria_id": "sexual_content"}, think=False,
                                         tokenize=False, add_generation_prompt=True)
        out["sexual_matches_template"] += (rendered == direct) or G.count_tokens(tok, direct) > P.TRIM_AT_TOKENS
        out["sexual_differs_from_harm"] += rendered != our_llm.calls[-1][0]
    for arm, (digest, n) in (("dark", P.DATA_PINS["dark"]), ("light", P.DATA_PINS["light"])):
        rows = R.read_rows(arm, P.DATA_PATHS[arm], digest, n)
        for row in rows[: a.rows or None]:
            same, trimmed = compare(row.user_turn, row.assistant_turn)
            out["real_rows"] += 1
            out["real_rows_identical"] += same
            out["real_rows_trimmed"] += trimmed
    # the known answers: the probe's reading (its bank_prompts, generations.jsonl rows of kind harm) and the screen's
    # (units.load_items, common.bank_prompts), then the same comparison
    ka = SB.ka_plan()
    unit = ka["unit"]
    mac_prompts = probe.bank_prompts(P.PREPARED, P.PREPARED_MANIFEST)
    gens = {r["prompt_id"]: r for r in map(json.loads, open(pathlib.Path(unit.files["generations"]["path"]),
                                                            encoding="utf-8")) if r.get("kind") == "harm"}
    ours_prompts = bank_prompts(P.PREPARED, P.PREPARED_MANIFEST)
    items = {it.prompt_id: it for it in load_items(unit, "greedy", with_text=True)}
    for pid in sorted(gens):
        out["ka_items"] += 1
        mac_pair = (mac_prompts[pid], gens[pid]["text"])
        our_pair = (ours_prompts[pid], items[pid].text)
        out["ka_inputs_equal"] += (sha(mac_pair[0]), sha(mac_pair[1])) == (sha(our_pair[0]), sha(our_pair[1]))
        same, _ = compare(*our_pair)
        out["ka_identical"] += same
    from importlib import metadata
    out["versions"] = {d: metadata.version(d) for d in ("transformers", "tokenizers", "Jinja2")}
    out["probe_sha256"] = hashlib.sha256(pathlib.Path(a.probe).read_bytes()).hexdigest()
    out["tokenizer_folder_files"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(pathlib.Path(probe.TOK).iterdir()) if p.is_file()}
    out["tokenizer_matches_pins"] = out["tokenizer_folder_files"] == {k: v[1] for k, v in P.GRANITE_TOK_FILES.items()}
    out.pop("tokenizer_folder_files")
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
