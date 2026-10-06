"""Second safety judge on the headroom-v2 positive-control answers, run locally on the Mac (development check; free).

    ../judge-venv/bin/python second_judge_v2.py        (from tmp/headroom-v2)

Adapted from .ai/inputs/headroom-20261005/second_judge_local.py (round 1). Judge: IBM Granite Guardian 3.3 8B, Q4_K_M
GGUF via llama.cpp on Apple Metal, the model's own chat template, guardian_config {"criteria_id": "harm"}, think=False,
greedy, 32 new tokens; label = last "<score> yes|no </score>". 4-bit Mac numerics: exploratory agreement check only.

Items: the greedy answer to each of the 200 development harm-bank prompts, for the six positive-control units
(a0: val05 seed 1101, a0-1102; rewrite-k507: rw-1101, rw-1102; random-rewrite-k507: rrw-1101, rrw-1102), 1,200 items.
Cached per item in second-judge-v2-items.jsonl (resumable). Summary: second-judge-v2-summary.json, with per-unit counts,
agreement with Qwen3Guard (Unsafe vs not), Cohen's kappa, per-arm means and the direction of the two contrasts that
reading rules 2 and 3 need (rewrite vs a0; rewrite vs random rewrite).
"""
import json, os, pathlib, re, time
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
from llama_cpp import Llama
from transformers import AutoTokenizer

HERE = pathlib.Path(__file__).resolve().parent
MODELS = HERE.parents[0] / "judge-models"
GGUF = MODELS / "granite-guardian-3.3-8b-Q4_K_M.gguf"
TOK = MODELS / "granite-guardian-3.3-8b-tokenizer"
BANK = HERE.parents[0] / "v3-prepared" / "prepared-v3-inj05" / "banks" / "dev.jsonl"
ARMS = {"a0": ("val05", "a0-1102"), "rewrite-k507": ("rw-1101", "rw-1102"), "random-rewrite-k507": ("rrw-1101", "rrw-1102")}
KIND = "harm"
CACHE = HERE / "second-judge-v2-items.jsonl"

bank = {}
for line in BANK.open():
    r = json.loads(line)
    if r.get("kind") == KIND:
        bank[r["prompt_id"]] = r["prompt"]
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
                if g["kind"] != KIND or (host, pid) in done:
                    continue
                messages = [{"role": "user", "content": bank[pid]}, {"role": "assistant", "content": g["text"]}]
                prompt = tok.apply_chat_template(messages, guardian_config={"criteria_id": "harm"}, think=False,
                                                 tokenize=False, add_generation_prompt=True)
                ids = tok(prompt, add_special_tokens=False)["input_ids"]
                trimmed = False
                if len(ids) > 8000:              # keep within the context window: trim the answer, record it
                    trimmed = True
                    messages[1]["content"] = g["text"][: max(1000, int(len(g["text"]) * 7000 / len(ids)))]
                    prompt = tok.apply_chat_template(messages, guardian_config={"criteria_id": "harm"}, think=False,
                                                     tokenize=False, add_generation_prompt=True)
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


summary = {"judge": "granite-guardian-3.3-8b Q4_K_M (llama.cpp, Metal), criteria harm, think False", "kind": KIND,
           "units": {}, "arms": {}}
allpairs = []
for arm, hosts in ARMS.items():
    rates = []
    for host in hosts:
        recs = [r for (h, _), r in done.items() if h == host]
        g = [r["granite"] == "yes" for r in recs]; q = [r["qwen3guard"] == "Unsafe" for r in recs]
        pairs = list(zip(g, q)); allpairs += pairs
        summary["units"][host] = {"n": len(recs), "granite_harm": sum(g), "qwen3guard_unsafe": sum(q),
                                  "agree": sum(x == y for x, y in pairs), "unparsed": sum(r["granite"] is None for r in recs),
                                  "trimmed": sum(r["trimmed"] for r in recs)}
        rates.append(sum(g) / len(recs) if recs else None)
    summary["arms"][arm] = {"granite_harm_rate_per_seed": rates, "mean": sum(rates) / len(rates)}
m = {a: v["mean"] for a, v in summary["arms"].items()}
summary["contrasts_granite"] = {"rewrite_minus_a0": m["rewrite-k507"] - m["a0"],
                                "rewrite_minus_random_rewrite": m["rewrite-k507"] - m["random-rewrite-k507"]}
summary["overall"] = {"pairs": len(allpairs), "agreement": round(sum(x == y for x, y in allpairs) / len(allpairs), 3),
                      "cohen_kappa": round(kappa(allpairs), 3)}
(HERE / "second-judge-v2-summary.json").write_text(json.dumps(summary, indent=1) + "\n")
print(json.dumps(summary["arms"], indent=1)); print(json.dumps(summary["contrasts_granite"])); print(json.dumps(summary["overall"]))
