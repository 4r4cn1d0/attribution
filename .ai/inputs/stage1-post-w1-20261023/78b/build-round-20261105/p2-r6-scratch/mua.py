"""REQ-9: the untuned model's answers with lexicon labels, and W1-06's per-row loss (RS B7; addendum L11, L14, section 5
item 3 (b); outside the engine identity; runs on a stage-1 pod; CPU-tested; CUDA paths UNTESTED). It generalizes
make_anchor_answers.py, which stays unchanged, and is model-agnostic (nothing assumes OLMo-2-1B's layers or sizes).

    python scripts/stage1/make_untuned_answers.py --recipe REC --recipe-s S --list s4=PATH:SHA256 [--list s3=…]
        [--list sd600=…] [--loss s1=PATH:SHA256 --loss s3_safe=PATH:SHA256] --out DIR

REC's policy is loaded through the engine's loaders and run UNTUNED (``policy.model.disable_adapter()``, no gradients).
Prompts are encoded with ``encode_generation_prompt`` under REC's max_prompt_tokens; answers come from the engine's
greedy generation with REC's stop tokens, in chunks of ``chunk`` consecutive list positions (REC's batch size, 32), each
chunk its own call (never one whole-list call: the engine sorts a call's prompts by length; L11 (1)). max_new_tokens per
list is the settings' (S3: 512; S4 and SD-600: REC's cap; L14). Each answer gets ``ended`` (it stopped at a stop token),
``capped``, its lexicon class (REQ-1) and whether ``encode_train`` accepts (prompt, answer) under recipe S's
max_train_tokens (read from the recipe; REC's must equal it).

Keep rules (L14):
- **S3** (the S3 subset and S1's rows outside it; L10 (2)): every answer is kept and capped ones are flagged. A y^orig that
  encode_train refuses leaves the SAS ranking and is counted. REQ-3's pool ``s3_orig`` holds the others, with ids
  ``<id>:orig`` so that it can run beside ``s3_safe``.
- **S4** (REQ-6's 512 candidates): an answer is kept only if it ended, is REFUSAL-OPENING, ``strip()`` is non-empty and
  encode_train accepts it; each failure is a counted reason. The first 48 kept in list order form S4; the job stops after
  the chunk that holds the 48th (later keeps in that chunk are counted, not used). Fewer than 48 after the whole list:
  counts only, exit 3. Per chunk: prompts answered, keeps, seconds and the SHA-256 of its answers.
- **SD-600** (REQ-15's list): every answer is kept; the capped count and per row ended, empty and encode_train's verdict
  are recorded (REQ-15 decides rewrite or remove).

W1-06 (``--loss``): the untuned model's mean per-token NLL over the response and end-of-turn targets (the engine's
``example_losses``, its training loss) and its exp, per row, for S1's 48 (prompt, PKU-safe response), the s3_safe pool
(prompt, PKU-safe response) and, when S4 ran, S4's 48 kept rows (prompt, untuned answer); encode_train refusals are
counted; forwards in batches of ``loss_batch`` rows.

Writes into --out (absent or empty): ``answers_<list>.json`` (with text; the kit pulls them to tmp/), ``s4.json`` (the 48
kept rows as a stage-1 prompt list, REQ-7's input), ``s3_orig.pool.json``, and the text-free ``untuned_answers_record.json``
(ids, flags, classes, token counts, answer SHA-256s, chunks, the loss table, costs, provenance). Prints counts and hashes.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import lexicon_pin  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "make_untuned_answers.json"
SETTINGS_SHA256 = "4bf2cc1a2493bc154d314105a085f0166933d1147a37e29fd42c7348ba9d9d8c"
SETTINGS_NAME = "make_untuned_answers"
RECORD = "untuned_answers_record.json"
EXIT_FEW = 3
LIST_KINDS = ("stage1 prompt list", "stage1 text pool")


def read_list(path: Path, digest: str, name: str, spec: dict) -> list[dict]:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"list {name} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"list {name} hashes to {sha256_bytes(data)}, expected {digest}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") not in LIST_KINDS or not isinstance(doc.get("items"), list):
        raise s1.Refusal(f"list {name} is not a stage-1 prompt list or text pool")
    items = doc["items"]
    if any(not isinstance(i, dict) or not isinstance(i.get("id"), str) or not s1.SAFE_VALUE.match(i["id"])
           or not isinstance(i.get("prompt"), str) for i in items) or len({i["id"] for i in items}) != len(items):
        raise s1.Refusal(f"list {name}: items need distinct short ids and a text prompt")
    if spec.get("size") is not None and len(items) != spec["size"]:
        raise s1.Refusal(f"list {name} holds {len(items)} items, the settings say {spec['size']}")
    return items


def recipes(rec_path: Path, s_path: Path, settings: dict) -> tuple[dict, dict]:
    from experiments.safety_selection.config import config_sha256, load_recipe

    rec, s = load_recipe(rec_path), load_recipe(s_path)
    for name, recipe, pin in (("REC", rec, settings["pins"]["rec_recipe_sha256"]),
                              ("recipe S", s, settings["pins"]["recipe_s_sha256"])):
        if config_sha256(recipe) != pin:
            raise s1.Refusal(f"{name} hashes to {config_sha256(recipe)}, the settings pin {pin}")
    for key in ("max_train_tokens", "max_prompt_tokens", "repo_id", "revision"):
        if rec["model"][key] != s["model"][key]:
            raise s1.Refusal(f"REC and recipe S disagree on model.{key}")
    return rec, s


class Answerer:
    """Chunked greedy answers of the untuned model: generate(ids) -> [Generation] for one chunk."""

    def __init__(self, generate, codec, classify, max_train_tokens: int, max_prompt_tokens: int, sync=None):
        self.generate, self.codec, self.classify = generate, codec, classify
        self.max_train, self.max_prompt, self.sync = max_train_tokens, max_prompt_tokens, sync or (lambda: None)

    def prompt_ids(self, items: list[dict], name: str) -> list[list[int]]:
        from experiments.safety_selection.textproc import encode_generation_prompt

        out = []
        for k, item in enumerate(items):
            try:
                out.append(encode_generation_prompt(self.codec, item["prompt"], self.max_prompt))
            except ValueError as exc:
                raise s1.Refusal(f"list {name} item {k} ({item['id']}) is not a generation prompt "
                                 f"({type(exc).__name__})") from None
        return out

    def chunk(self, items: list[dict], ids: list[list[int]], max_new_tokens: int) -> tuple[list[dict], float]:
        from experiments.safety_selection import engine as en
        from experiments.safety_selection.textproc import encode_train

        self.sync()
        started = time.monotonic()
        gens = self.generate(ids, max_new_tokens)
        self.sync()
        seconds = time.monotonic() - started
        if len(gens) != len(items):
            raise s1.Refusal("the generator returned another number of answers than prompts")
        rows = []
        for item, g in zip(items, gens):
            answer = self.codec.decode(g.output_ids)
            try:
                encode_train(self.codec, item["id"], item["prompt"], answer, self.max_train)
                encodes = None
            except ValueError as exc:
                encodes = type(exc).__name__
            rows.append({"id": item["id"], "prompt": item["prompt"], "answer": answer,
                         "ended": g.stop_reason == en.STOP_EOS, "capped": g.stop_reason == en.STOP_CAP,
                         "answer_tokens": len(g.output_ids), "lex_class": self.classify(answer),
                         "empty": not answer.strip(), "encode_train": encodes})
        return rows, seconds


def s4_reason(row: dict) -> str | None:
    """L14 (2): the S4 keep predicate; the first failing check is the drop reason."""
    if not row["ended"]:
        return "capped"
    if row["empty"]:
        return "empty"
    if row["lex_class"] != "REFUSAL-OPENING":
        return "not_refusal_opening"
    if row["encode_train"] is not None:
        return f"encode_train_{row['encode_train']}"
    return None


def answer_list(answerer: Answerer, name: str, items: list[dict], spec: dict, chunk: int) -> dict:
    """Every chunk of the list (S4: until the chunk that holds the 48th keep)."""
    ids = answerer.prompt_ids(items, name)
    rows, chunks, kept, keep_target = [], [], [], spec.get("keep")
    for start in range(0, len(items), chunk):
        part, seconds = answerer.chunk(items[start:start + chunk], ids[start:start + chunk], spec["max_new_tokens"])
        keeps = 0
        for row in part:
            if spec["kind"] == "s4":
                row["drop"] = s4_reason(row)
                if row["drop"] is None:
                    keeps += 1
                    if len(kept) < keep_target:
                        kept.append(row["id"])
                        row["kept"] = True
                    else:
                        row["kept"] = False
                        row["drop"] = "kept_after_the_48th"
                else:
                    row["kept"] = False
        rows += part
        chunks.append({"start": start, "prompts": len(part), "keeps": keeps, "seconds": seconds,
                       "answers_sha256": sha256_bytes(canonical_json([[r["id"], r["answer"]] for r in part]))})
        if spec["kind"] == "s4" and len(kept) == keep_target:
            break
    return {"rows": rows, "chunks": chunks, "kept": kept}


def loss_table(model_losses, codec, rows_by_list: dict[str, list[tuple[str, str, str]]], max_train_tokens: int,
               batch: int) -> dict:
    """W1-06: per list and row id, n_target, the mean NLL and its exp; encode_train refusals counted."""
    from experiments.safety_selection.textproc import encode_train

    out = {}
    for name, rows in rows_by_list.items():
        examples, refused = [], Counter()
        for row_id, prompt, response in rows:
            try:
                examples.append(encode_train(codec, row_id, prompt, response, max_train_tokens))
            except ValueError as exc:
                refused[type(exc).__name__] += 1
        values = {}
        for start in range(0, len(examples), batch):
            part = examples[start:start + batch]
            for ex, nll in zip(part, model_losses(part)):
                values[ex.row_id] = {"n_target": ex.n_target, "mean_nll": float(nll), "perplexity": math.exp(float(nll))}
        out[name] = {"rows": dict(sorted(values.items())), "refused_by_reason": dict(sorted(refused.items()))}
    return out


def run(*, rec_path: Path, s_path: Path, lists: dict[str, tuple[Path, str]], losses: dict[str, tuple[Path, str]],
        loaders, settings: dict, settings_sha256: str, generate=None) -> tuple[dict[str, bytes], int]:
    """Every output file and the exit code (0, or 3 for fewer than 48 S4 keeps); nothing is written here.
    ``generate`` (tests): a chunk generator (ids, max_new_tokens) -> [Generation]; by default the untuned model's."""
    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        return _run(rec_path, s_path, lists, losses, loaders, settings, settings_sha256, generate, Path(scratch))


def _run(rec_path, s_path, lists, losses, loaders, settings, settings_sha256, generate, scratch):
    import torch

    from experiments.safety_selection import engine as en
    from experiments.safety_selection import runner
    from experiments.safety_selection.common import code_identity
    from experiments.safety_selection.ledger import RunLedger

    s1.check_settings(settings, SETTINGS_NAME)
    if not lists:
        raise s1.Refusal("no list to answer")
    unknown = sorted(set(lists) - set(settings["lists"])) + sorted(set(losses) - set(settings["loss"]["lists"]))
    if unknown:
        raise s1.Refusal(f"the settings name no list {unknown[0]!r}")
    from scripts.stage1.representation_pass import check_transformers

    check_transformers(settings)
    rec, s = recipes(rec_path, s_path, settings)
    items = {name: read_list(*lists[name], name, settings["lists"][name]) for name in lists}
    loss_items = {name: read_list(*losses[name], name, {}) for name in losses}
    if any(not isinstance(i.get("response"), str) for rows in loss_items.values() for i in rows):
        raise s1.Refusal("a loss list's items need a text response")
    lexicon = lexicon_pin.load()
    session = runner.Session(rec, loaders)
    ledger = RunLedger(scratch, sync=session.sync, memory=session.memory)
    policy = session.policy(ledger, scratch)
    codec, model, device, gen = policy.codec, policy.model, policy.device, rec["generation"]
    chunk = settings["chunk"]
    if chunk != gen["batch_size"]:
        raise s1.Refusal(f"the settings' chunk {chunk} is not REC's generation batch size {gen['batch_size']}")

    def untuned(ids, max_new_tokens):
        with torch.no_grad(), model.disable_adapter():
            return en.greedy_generate(model, ids, max_new_tokens=max_new_tokens, stop_ids=codec.stop_ids,
                                      pad_id=codec.pad_id, device=device, batch_size=chunk)

    answerer = Answerer(generate or untuned, codec, lexicon.classify, s["model"]["max_train_tokens"],
                        rec["model"]["max_prompt_tokens"], session.sync)
    started = time.monotonic()
    results, full = {}, {}
    for name in settings["lists"]:
        if name not in lists:
            continue
        spec = {**settings["lists"][name]}
        spec["max_new_tokens"] = gen["max_new_tokens"] if spec["max_new_tokens"] == "rec" else spec["max_new_tokens"]
        results[name] = (spec, answer_list(answerer, name, items[name], spec, chunk))
    answer_seconds = time.monotonic() - started
    exit_code = 0
    record_lists = {}
    for name, (spec, res) in results.items():
        rows = res["rows"]
        full[f"answers_{name}.json"] = canonical_json({"kind": "stage1 untuned answers", "version": 1, "list": name,
                                                       "items": [{"id": r["id"], "prompt": r["prompt"], "answer": r["answer"],
                                                                  "ended": r["ended"]} for r in rows]})
        entry = {"list_sha256": lists[name][1], "items": len(items[name]), "answered": len(rows),
                 "max_new_tokens": spec["max_new_tokens"], "capped": sum(r["capped"] for r in rows),
                 "ended": sum(r["ended"] for r in rows), "empty": sum(r["empty"] for r in rows),
                 "lex_classes": dict(sorted(Counter(r["lex_class"] for r in rows).items())),
                 "encode_train_refused": dict(sorted(Counter(r["encode_train"] for r in rows if r["encode_train"]).items())),
                 "chunks": res["chunks"], "answers_file_sha256": sha256_bytes(full[f"answers_{name}.json"]),
                 "rows": [{"id": r["id"], "ended": r["ended"], "capped": r["capped"], "answer_tokens": r["answer_tokens"],
                           "lex_class": r["lex_class"], "empty": r["empty"], "encode_train": r["encode_train"],
                           **({"kept": r["kept"], "drop": r["drop"]} if spec["kind"] == "s4" else {}),
                           "answer_sha256": sha256_bytes(r["answer"].encode("utf-8"))} for r in rows]}
        if spec["kind"] == "s3":
            pool = [r for r in rows if r["encode_train"] is None]
            full["s3_orig.pool.json"] = canonical_json({"kind": "stage1 text pool", "version": 1, "name": "s3_orig",
                                                        "items": [{"id": f"{r['id']}:orig", "prompt": r["prompt"],
                                                                   "response": r["answer"]} for r in pool]})
            entry["y_orig_leaves_the_sas_ranking"] = len(rows) - len(pool)
            entry["s3_orig_pool_sha256"] = sha256_bytes(full["s3_orig.pool.json"])
        if spec["kind"] == "s4":
            entry["kept"] = len(res["kept"])
            entry["drops"] = dict(sorted(Counter(r["drop"] for r in rows if r["drop"]).items()))
            entry["chunks_run"] = len(res["chunks"])
            if len(res["kept"]) < spec["keep"]:
                exit_code = EXIT_FEW
            else:
                by_id = {r["id"]: r for r in rows}
                full["s4.json"] = canonical_json({"kind": "stage1 prompt list", "version": 1, "name": "s4",
                                                  "items": [{"id": i, "prompt": by_id[i]["prompt"],
                                                             "response": by_id[i]["answer"]} for i in res["kept"]]})
                entry["s4_list_sha256"] = sha256_bytes(full["s4.json"])
        record_lists[name] = entry
    started = time.monotonic()
    loss = None
    if losses or ("s4" in results and exit_code == 0 and settings["loss"]["include_s4"]):
        rows_by_list = {name: [(i["id"], i["prompt"], i["response"]) for i in loss_items[name]] for name in loss_items}
        if "s4" in results and exit_code == 0:
            by_id = {r["id"]: r for r in results["s4"][1]["rows"]}
            rows_by_list["s4"] = [(i, by_id[i]["prompt"], by_id[i]["answer"]) for i in results["s4"][1]["kept"]]
        head_chunk = rec["train"]["lm_head_chunk_tokens"]

        def losses_of(examples):
            with torch.no_grad(), model.disable_adapter():
                was = model.training
                model.eval()
                try:
                    return en.example_losses(model, examples, codec.pad_id, device, head_chunk).tolist()
                finally:
                    model.train(was)
        loss = loss_table(losses_of, codec, rows_by_list, s["model"]["max_train_tokens"], settings["loss"]["batch"])
    loss_seconds = time.monotonic() - started
    if exit_code == EXIT_FEW:
        full = {k: v for k, v in full.items() if k.startswith("answers_")}
    identity = code_identity()
    record = {"kind": "stage1 untuned answers record", "version": 1, "requirement": settings["requirement"],
              "complete": exit_code == 0, "untuned": "policy.model.disable_adapter() under torch.no_grad()",
              "chunk": chunk, "lists": record_lists, "loss": loss,
              "full_files": {n: sha256_bytes(d) for n, d in sorted(full.items())},
              "costs": {"device": device, "answer_seconds": answer_seconds, "loss_seconds": loss_seconds,
                        "peak_memory_bytes": int(torch.cuda.max_memory_allocated()) if device == "cuda" else None,
                        "gpu": (session.environment.get("cuda") or {}).get("name")},
              "provenance": {**s1.provenance(Path(__file__).resolve(), settings_sha256,
                                             {"rec_recipe": settings["pins"]["rec_recipe_sha256"],
                                              "recipe_s": settings["pins"]["recipe_s_sha256"],
                                              **{f"list_{n}": d for n, (_, d) in sorted(lists.items())},
                                              **{f"loss_{n}": d for n, (_, d) in sorted(losses.items())}},
                                             settings["label_entries"]),
                             "model": {"repo_id": rec["model"]["repo_id"], "revision": rec["model"]["revision"]},
                             "engine_code_sha256": identity["sha256"], "lock_sha256": lock_sha256(),
                             "lexicon": lexicon_pin.identity()}}
    record_bytes = canonical_json(record)
    texts = [t for _, (_, res) in results.items() for r in res["rows"] for t in (r["prompt"], r["answer"])]
    texts += [t for name in loss_items for i in loss_items[name] for t in (i["prompt"], i.get("response", ""))]
    if s1._text_hits(record_bytes, texts):
        raise s1.Refusal("the record would hold text")
    full[RECORD] = record_bytes
    return full, exit_code


def lock_sha256() -> str | None:
    lock = Path.cwd() / "environment-linux.lock"
    return sha256_bytes(lock.read_bytes()) if lock.is_file() else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--recipe", type=Path, required=True, help="REC")
    parser.add_argument("--recipe-s", type=Path, required=True, help="recipe S (max_train_tokens)")
    parser.add_argument("--list", action="append", default=[], help="NAME=PATH:SHA256 (s3, s4 or sd600)")
    parser.add_argument("--loss", action="append", default=[], help="NAME=PATH:SHA256 (s1 or s3_safe)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)

        def named(specs, what):
            out = {}
            for spec in specs:
                name, _, rest = spec.partition("=")
                path, _, sha = rest.rpartition(":")
                if not name or not path or not s1.HEX64.match(sha) or name in out:
                    raise s1.Refusal(f"each {what} is NAME=PATH:SHA256, each name once")
                out[name] = (Path(path), sha)
            return out
        lists, losses = named(args.list, "--list"), named(args.loss, "--loss")
        from experiments.safety_selection.loaders import real_loaders

        files, code = run(rec_path=args.recipe, s_path=args.recipe_s, lists=lists, losses=losses, loaders=real_loaders(),
                          settings=settings, settings_sha256=digest)
        written = s1.write_new_files(args.out.resolve(), files)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    rec = s1.strict_json(files[RECORD])
    for name, entry in rec["lists"].items():
        print(f"{name}: answered {entry['answered']} of {entry['items']}; capped {entry['capped']}; "
              f"kept {entry.get('kept', '-')}")
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return code


if __name__ == "__main__":
    sys.exit(main())
