"""Granite prompt parity of the triples path, run by the Mac's judge venv (transformers 5.18.0, tokenizers 0.23.2, the
Mac's pinned Granite tokenizer folder, offline; no model is loaded: llama_cpp is replaced by a recorder).

Written 9 October 2026 (10:45 UTC, clock checked); rewritten 9 October 2026 (17:25 UTC, clock checked) for the lead's
Granite backend. Three code paths get the same inputs and their texts are compared byte for byte:
  - the TRIPLES PATH, which the pod runs: the lead's granite_pod.judge_triples([(id, user_text, response)], C,
    session=...) through a real GraniteSession (the real tokenizer loader granite_pod.load_tokenizer_at, the Mac's
    tokenizer fingerprint required, the tokenizer folder checked against its ten pins; only the GGUF check and the
    model are replaced): the text its llm(...) call receives, and the input_sha256 it returns;
  - BEFORE: the screen's own prompt builder before the refactor (granite_screen.granite_prompt at commit e3ce85b,
    given by --before; its four functions are run from their syntax tree with the old trim constants);
  - the PROBE: tmp/family-probe-llama32-1b/second_judge_probe.py (the Mac's calling convention, SHA-256 c51e466c...),
    for criterion "harm" (the probe has no other).
Also compared: the Llama(...) constructor arguments (the probe's and granite_pod.load_model_at's), the call arguments,
and the label each side parses from the same outputs (the screen maps the lead's yes/no/unparsed to Yes/No/invalid).
Inputs: synthetic fixtures (unicode, whitespace, special strings, answers long enough to be trimmed), the first --rows
rows of dark.jsonl and light.jsonl (0: all) with the screen's user turn, and the 200 known answers of the lead's gate
(prompts from the dev bank and answers from the unit, read both the probe's way and the lead's way). Prints one JSON
line of counts and versions; never any text.

    <judge-venv>/bin/python -I -B granite_parity_helper.py --tool TOOL_DIR --probe PROBE_FILE --before OLD_FILE [--rows N]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys
import types

sys.dont_write_bytecode = True
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
OLD_FUNCTIONS = ("granite_messages", "render", "count_tokens", "granite_prompt")
OLD_TRIM = {"TRIM_AT_TOKENS": 8000, "TRIM_TO_TOKENS": 7000, "TRIM_MIN_CHARS": 1000}
LABEL_OUTPUTS = ("<score> yes </score>", "<score>No</score>", "<score> no </score> then <score> yes </score>",
                 "<score> maybe </score>", "no score", "", "<score>\n yes\n</score>", "<think>x</think><score> No </score>")


class FakeLlama:
    """Stands in for llama_cpp.Llama: records the constructor's and each call's arguments; returns a fixed score."""
    instances: list = []
    output = "<score> no </score>"

    def __init__(self, **kw):
        self.init, self.calls = dict(kw), []
        FakeLlama.instances.append(self)

    def __call__(self, text, **kw):
        self.calls.append((text, dict(kw)))
        return {"choices": [{"text": FakeLlama.output}]}


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_by_path(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def old_prompt_builder(path: pathlib.Path):
    """granite_screen.granite_prompt of the screen before the refactor, from its source (only its four functions)."""
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    keep = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in OLD_FUNCTIONS]
    assert sorted(n.name for n in keep) == sorted(OLD_FUNCTIONS)
    ns = {"P": types.SimpleNamespace(**OLD_TRIM)}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(path), "exec"), ns)
    return ns["granite_prompt"]


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
    ap.add_argument("--before", type=pathlib.Path, required=True)
    ap.add_argument("--rows", type=int, default=300, help="rows of each arm (0: all)")
    a = ap.parse_args()
    fake = types.ModuleType("llama_cpp")
    fake.Llama = FakeLlama
    sys.modules["llama_cpp"] = fake
    probe = load_by_path("second_judge_probe_under_test", a.probe)
    mac_judge = probe.granite_judge()                       # the real tokenizer, a recording Llama
    mac_llm = FakeLlama.instances[-1]
    sys.path.insert(0, str(a.tool))
    import screen_bundle as SB                              # noqa: E402  (puts the lead's modules on sys.path)
    import screen_pins as P                                 # noqa: E402
    import screen_rows as R                                 # noqa: E402
    import granite_files                                    # noqa: E402  (the lead's)
    import granite_pod                                      # noqa: E402  (the lead's)
    from pod_judge import tokenizer_fingerprint             # noqa: E402  (the lead's)
    from common import bank_prompts                         # noqa: E402
    from units import load_items                            # noqa: E402
    before = old_prompt_builder(a.before)
    pod_llm = granite_pod.load_model_at(pathlib.Path(probe.GGUF))    # the lead's constructor, recorded
    tokens = {"loads": 0}

    def load_tokenizer(folder):
        tokens["loads"] += 1
        tokens["tok"] = granite_pod.load_tokenizer_at(folder)
        return tokens["tok"]

    def check(tok_dir, gguf):                               # the tokenizer folder against its pins; no GGUF here
        return {"tokenizer_files": granite_pod.verify_tokenizer_dir(tok_dir), "gguf_sha256": None}
    session = granite_pod.GraniteSession(pathlib.Path(probe.TOK), pathlib.Path("/nonexistent/granite.gguf"),
                                         load_tokenizer=load_tokenizer, load_model=lambda path: pod_llm, check=check,
                                         require_fingerprint=granite_pod.MAC_TOKENIZER_FINGERPRINT)
    out = {"init_kwargs_equal": mac_llm.init == pod_llm.init,
           "init_kwargs": sorted(mac_llm.init), "call_kwargs_equal": True, "label_parse_equal": True,
           "ka_inputs_equal": 0}
    counter = {"id": 0}

    def triples_text(user: str, response: str, criteria: str):
        counter["id"] += 1
        ((_, label, input_sha256, n, trimmed),) = granite_pod.judge_triples([(f"t-{counter['id']}", user, response)],
                                                                             criteria, session=session)
        text, kw = pod_llm.calls[-1]
        return text, kw, input_sha256, trimmed, n

    def compare(case: str, user: str, response: str) -> None:
        c = out.setdefault(case, {"n": 0, "harm_vs_probe": 0, "harm_vs_before": 0, "sexual_vs_before": 0,
                                  "input_sha256_ok": 0, "trimmed_equal": 0, "trimmed": 0, "tokens_equal": 0})
        c["n"] += 1
        label, probe_trimmed, _ = mac_judge(user, response)
        probe_text, probe_kw = mac_llm.calls[-1]
        text, kw, input_sha256, trimmed, n = triples_text(user, response, "harm")
        old_text, old_n, old_trimmed = before(tokens["tok"], user, response, "harm")
        out["call_kwargs_equal"] &= probe_kw == kw == {"max_tokens": 32, "temperature": 0.0, "top_k": 1}
        c["harm_vs_probe"] += text.encode("utf-8") == probe_text.encode("utf-8")
        c["harm_vs_before"] += text.encode("utf-8") == old_text.encode("utf-8")
        c["input_sha256_ok"] += input_sha256 == sha(text)
        c["trimmed_equal"] += trimmed == probe_trimmed == old_trimmed
        c["trimmed"] += trimmed
        c["tokens_equal"] += n == old_n
        text, kw, input_sha256, trimmed, n = triples_text(user, response, "sexual_content")
        old_text, old_n, old_trimmed = before(tokens["tok"], user, response, "sexual_content")
        c["sexual_vs_before"] += (text.encode("utf-8") == old_text.encode("utf-8") and trimmed == old_trimmed
                                  and n == old_n and input_sha256 == sha(text))

    for user, response in fixtures():
        compare("fixtures", user, response)
    for arm in ("dark", "light"):
        digest, n = P.DATA_PINS[arm]
        for row in R.read_rows(arm, P.DATA_PATHS[arm], digest, n)[: a.rows or None]:
            compare("real_rows", row.user_turn, row.assistant_turn)
    # the lead's gate's 200 answers: the probe's reading (its bank_prompts, generations.jsonl rows of kind harm) and the
    # lead's (bundle.plan_known_answers: units.load_items, common.bank_prompts), then the same comparison
    plan = SB.lead_gate_plan()
    unit = plan["unit"]
    mac_prompts = probe.bank_prompts(plan["prepared"]["dir"], plan["prepared"]["manifest_sha256"])
    gens = {r["prompt_id"]: r for r in map(json.loads, open(pathlib.Path(unit.files["generations"]["path"]),
                                                            encoding="utf-8")) if r.get("kind") == "harm"}
    lead_prompts = bank_prompts(plan["prepared"]["dir"], plan["prepared"]["manifest_sha256"])
    items = {it.prompt_id: it for it in load_items(unit, "greedy", with_text=True)}
    for pid in sorted(gens):
        mac_pair = (mac_prompts[pid], gens[pid]["text"])
        lead_pair = (lead_prompts[pid], items[pid].text)
        out["ka_inputs_equal"] += (sha(mac_pair[0]), sha(mac_pair[1])) == (sha(lead_pair[0]), sha(lead_pair[1]))
        compare("ka", *lead_pair)
    for text in LABEL_OUTPUTS:                              # the probe's score rule and the lead's parse, mapped
        scores = re.findall(r"<score>(.*?)</score>", text, re.DOTALL)
        probe_label = scores[-1].strip().lower() if scores else None
        want = {"yes": "Yes", "no": "No"}.get(probe_label, "invalid")
        out["label_parse_equal"] &= R.granite_label(granite_files.parse_score(text)) == want
    from importlib import metadata
    out["versions"] = {d: metadata.version(d) for d in ("transformers", "tokenizers", "Jinja2")}
    out["probe_sha256"] = hashlib.sha256(pathlib.Path(a.probe).read_bytes()).hexdigest()
    out["before_sha256"] = hashlib.sha256(pathlib.Path(a.before).read_bytes()).hexdigest()
    out["tokenizer_matches_pins"] = bool(granite_pod.verify_tokenizer_dir(pathlib.Path(probe.TOK)))
    out["fingerprint_is_macs"] = tokenizer_fingerprint(tokens["tok"]) == granite_pod.MAC_TOKENIZER_FINGERPRINT
    out["tokenizer_loads"], out["probe_tok_is_lead_tok"] = tokens["loads"], pathlib.Path(probe.TOK) == granite_pod.MAC_TOKENIZER
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
