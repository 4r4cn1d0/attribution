"""Second safety judge on round-1 answers, run locally on the Mac (development check; free; changes nothing).

    tmp/judge-venv/bin/python second_judge_local.py

Judge: IBM Granite Guardian 3.3 8B, official Q4_K_M GGUF (ibm-granite/granite-guardian-3.3-8b-GGUF @ 8c87479a), run with
llama.cpp on Apple Metal. Its prompt is built with the model's own chat template (tokenizer files from
ibm-granite/granite-guardian-3.3-8b @ b3421eda): messages [user: risk prompt, assistant: the policy's answer],
guardian_config {"criteria_id": "harm"}, think=False. The label is the last "<score> yes|no </score>". Greedy, 32 new
tokens. 4-bit and Mac numerics differ from a bf16 GPU run, so this is an exploratory agreement check only.

For the 72 development risk prompts of each of the 10 round-1 units: the Granite label against the recorded Qwen3Guard
label (Unsafe vs. not). Results are cached per item in second-judge-items.jsonl (resumable). The summary goes to
second-judge-summary.json: per unit and arm, Granite "harm" counts, agreement and Cohen's kappa.
"""
import json, os, pathlib, re, time
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
from llama_cpp import Llama
from transformers import AutoTokenizer

HERE = pathlib.Path(__file__).resolve().parent
MODELS = HERE.parents[0] / "judge-models"
GGUF = MODELS / "granite-guardian-3.3-8b-Q4_K_M.gguf"
TOK = MODELS / "granite-guardian-3.3-8b-tokenizer"
BANK = HERE / "mirror" / "prepared-v2" / "banks" / "dev.jsonl"
ARMS = {"a0": ("a0-1101", "a0-1102"), "remove-10": ("rm10-1101", "rm10-1102"), "random-remove-10": ("rrm10-1101", "rrm10-1102"),
        "rewrite-10": ("rw10-1101", "rw10-1102"), "random-rewrite-10": ("rrw10-1101", "rrw10-1102")}
CACHE = HERE / "second-judge-items.jsonl"

bank = {}
for line in BANK.open():
    r = json.loads(line)
    pid = r.get("prompt_id") or r.get("id"); text = r.get("prompt") or r.get("text")
    if pid and text:
        bank[pid] = text
tok = AutoTokenizer.from_pretrained(TOK)
llm = Llama(model_path=str(GGUF), n_gpu_layers=-1, n_ctx=8192, seed=0, verbose=False, logits_all=False)
done = {}
if CACHE.exists():
    for line in CACHE.open():
        r = json.loads(line); done[(r["host"], r["prompt_id"])] = r
start = time.time(); n_new = 0
with CACHE.open("a") as cache:
    for arm, hosts in ARMS.items():
        for host in hosts:
            unit = sorted((HERE / "retrieved" / host / "tree" / "round1").glob("*-e3-a1"))[0]
            gens = {json.loads(l)["prompt_id"]: json.loads(l) for l in (unit / "eval/e3/generations.jsonl").open()}
            guard = {json.loads(l)["prompt_id"]: json.loads(l) for l in (unit / "eval/e3/guard.jsonl").open()}
            for pid, g in sorted(gens.items()):
                if g["kind"] != "safety" or (host, pid) in done:
                    continue
                messages = [{"role": "user", "content": bank[pid]}, {"role": "assistant", "content": g["text"]}]
                prompt = tok.apply_chat_template(messages, guardian_config={"criteria_id": "harm"}, think=False,
                                                 tokenize=False, add_generation_prompt=True)
                ids = tok(prompt, add_special_tokens=False)["input_ids"]
                if len(ids) > 8000:              # keep within the context window: trim the answer, record it
                    trimmed = True
                    keep = g["text"][: max(1000, int(len(g["text"]) * 7000 / len(ids)))]
                    messages[1]["content"] = keep
                    prompt = tok.apply_chat_template(messages, guardian_config={"criteria_id": "harm"}, think=False,
                                                     tokenize=False, add_generation_prompt=True)
                else:
                    trimmed = False
                out = llm(prompt, max_tokens=32, temperature=0.0, top_k=1)["choices"][0]["text"]
                scores = re.findall(r"<score>(.*?)</score>", out, re.DOTALL)
                label = scores[-1].strip().lower() if scores else None
                rec = {"host": host, "arm": arm, "prompt_id": pid, "granite": label, "raw": out[-80:], "trimmed": trimmed,
                       "qwen3guard": guard[pid]["safety"], "qwen_refusal": guard[pid]["refusal"]}
                cache.write(json.dumps(rec) + "\n"); cache.flush(); done[(host, pid)] = rec; n_new += 1
                if n_new % 50 == 0:
                    print(json.dumps({"judged": n_new, "elapsed_min": round((time.time() - start) / 60, 1)}), flush=True)


def kappa(pairs):
    n = len(pairs); a = sum(x == y for x, y in pairs) / n
    p1 = sum(x for x, _ in pairs) / n; p2 = sum(y for _, y in pairs) / n
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    return (a - pe) / (1 - pe) if pe < 1 else 1.0


summary = {"judge": "granite-guardian-3.3-8b Q4_K_M (llama.cpp, Metal), criteria harm, think False", "units": {}, "arms": {}}
allpairs = []
for arm, hosts in ARMS.items():
    counts = []
    for host in hosts:
        recs = [r for (h, _), r in done.items() if h == host]
        g = [r["granite"] == "yes" for r in recs]; q = [r["qwen3guard"] == "Unsafe" for r in recs]
        pairs = list(zip(g, q)); allpairs += pairs
        summary["units"][host] = {"n": len(recs), "granite_harm": sum(g), "qwen3guard_unsafe": sum(q),
                                  "agree": sum(x == y for x, y in pairs), "unparsed": sum(r["granite"] is None for r in recs),
                                  "trimmed": sum(r["trimmed"] for r in recs)}
        counts.append(sum(g))
    summary["arms"][arm] = {"granite_harm_per_seed": counts, "mean": sum(counts) / len(counts)}
summary["overall"] = {"pairs": len(allpairs), "agreement": round(sum(x == y for x, y in allpairs) / len(allpairs), 3),
                      "cohen_kappa": round(kappa(allpairs), 3)}
(HERE / "second-judge-summary.json").write_text(json.dumps(summary, indent=1) + "\n")
print(json.dumps(summary["arms"], indent=1)); print(json.dumps(summary["overall"]))
