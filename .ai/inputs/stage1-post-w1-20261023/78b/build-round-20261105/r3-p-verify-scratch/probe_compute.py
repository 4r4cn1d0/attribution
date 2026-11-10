"""Verifier probe (R3 Track P): the padded-tokens tool against the ENGINE's own training loop on a synthetic fixture.

Run from the WS copy (argv[1]) with -B. Synthetic rows only. For each case and seed it compares four numbers:
  T = the tool's record (padded_tokens_by_seed), via padded_tokens_78b.main with a fake codec and fixture loader;
  L = runner._train_segment's steps.jsonl padded_tokens summed (the engine's loop, en.train_step stubbed);
  P = the real right-padded tensor size: en._right_padded(...).numel() per micro-batch, summed (inside the stub);
  Y = a pure-Python count written here from stream.py's documented order (no engine stream, no tool helper).
It also checks the steps (ceil(rows / 128)), the value (max over seeds / S), and that no sentinel reaches any output.
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import random
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

WSC = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(WSC))

from experiments.safety_selection import edits as E                          # noqa: E402
from experiments.safety_selection import engine as en                         # noqa: E402
from experiments.safety_selection import runner                              # noqa: E402
from experiments.safety_selection.common import derive_seed, ids_sha256       # noqa: E402
from experiments.safety_selection.config import tokenizer_of                  # noqa: E402
from experiments.safety_selection.prepare import Prepared                     # noqa: E402
from experiments.safety_selection.stream import make_plan                     # noqa: E402
from experiments.safety_selection.verify import STEPS                         # noqa: E402
from scripts.scale78b import encode_count_78b as ec                           # noqa: E402
from scripts.scale78b import padded_tokens_78b as pt                          # noqa: E402

SENT = "VRFY-sentinel-zq81"
FAM = "llama31-8b"
SEEDS = list(range(1101, 1108))


class Codec:
    eos_id = 2

    def encode(self, text):
        return [9] * len(text.split())

    def prompt_ids(self, text):
        return [4, 4, 4] + self.encode(text) + [8]        # three header ids and one closer (differs from the tests)

    def has_special(self, ids):
        return False


def n_tokens(prompt, response):
    return 3 + len(prompt.split()) + 1 + len(response.split()) + 1


def mkrow(prompt, response):
    c = Codec()
    ids = c.prompt_ids(prompt) + c.encode(response) + [c.eos_id]
    npr = len(c.prompt_ids(prompt))
    return {"prompt": prompt, "response": response, "prompt_tokens": npr, "target_tokens": len(ids) - npr,
            "token_sha256": ids_sha256(ids)}


def fixture(n):
    rows = {}
    for i in range(n):
        p = (i * i * 31 + 7) % 41
        r = (i * 13 + 5) % 57 + (90 if i % 97 == 0 else 0)       # a few long rows
        rows[f"row-{i:05d}"] = mkrow(f"{SENT} p " + " ".join(["a"] * p), f"{SENT} r " + " ".join(["b"] * r))
    return Prepared(Path("fx"), {"data_config": {}}, ec.MANIFESTS[FAM], rows, [], {"heldout": {"g": []}}, {}, {})


def edit_doc(remove=(), rewrite=(), add=()):
    add = [{"row_id": a, "prompt": p, "response": r} for a, p, r in add]
    rewrite = [{"row_id": a, "response": r} for a, r in rewrite]
    present = [k for k, v in (("remove", remove), ("rewrite", rewrite), ("add", add)) if v]
    return {"kind": E.EDIT_KIND, "version": E.EDIT_VERSION, "name": f"{SENT} name of the edit",
            "edit_kind": present[0] if len(present) == 1 else "combined", "manifest_sha256": ec.MANIFESTS[FAM],
            "remove": sorted(remove), "rewrite": rewrite, "add": add, "position_rule": E.POSITION_RULE,
            "counts": {"remove": len(remove), "rewrite": len(rewrite), "add": len(add)}, "provenance": {}}


def lengths(prep, doc):
    out = {k: n_tokens(v["prompt"], v["response"]) for k, v in prep.train_rows.items()}
    if doc:
        for it in doc["rewrite"]:
            out[it["row_id"]] = n_tokens(prep.train_rows[it["row_id"]]["prompt"], it["response"])
        for it in doc["add"]:
            out[it["row_id"]] = n_tokens(it["prompt"], it["response"])
    return out


def pure_python(prep, doc, seed):
    lens = lengths(prep, doc)
    order = sorted(prep.train_rows)
    random.Random(derive_seed(seed, "data-order", 0)).shuffle(order)
    gone = set(doc["remove"]) if doc else set()
    kept = [r for r in order if r not in gone]
    extra = sorted(it["row_id"] for it in doc["add"]) if doc else []
    if extra:
        random.Random(derive_seed(seed, "added-order", 0)).shuffle(extra)
        seq, s, n, m = [], 0, len(kept), len(extra)
        for j, rid in enumerate(extra):
            cut = (j + 1) * n // (m + 1)
            seq.extend(kept[s:cut]); seq.append(rid); s = cut
        seq.extend(kept[s:])
        kept = seq
    steps = math.ceil(len(kept) / 128)
    tot = 0
    for st in range(steps):
        b = kept[st * 128:(st + 1) * 128]
        for i in range(0, len(b), 2):
            mb = b[i:i + 2]
            tot += len(mb) * max(lens[x] for x in mb)
    return tot, len(kept), steps


class Ledger:
    def check(self, what):
        pass

    def elapsed(self):
        return 0.0

    def progress(self, *a, **k):
        pass

    @contextlib.contextmanager
    def stage(self, name, **keys):
        info = dict(keys)
        yield info
        info["seconds"] = 0.0


def engine_loop(prep, doc, edit_sha, seed, tmpdir):
    """The engine's own _train_segment over steps 1..S, en.train_step stubbed to count the real padded tensors."""
    lens = lengths(prep, doc)
    corpus = {k: SimpleNamespace(row_id=k, input_ids=tuple([1] * v), n_target=1) for k, v in lens.items()}
    removed = sorted(doc["remove"]) if doc else []
    if doc is None:
        plan = make_plan(sorted(prep.train_rows), [], seed, 2, 64)
    else:
        added = tuple(sorted(it["row_id"] for it in doc["add"]))
        plan = make_plan(sorted(prep.train_rows), removed, seed, 2, 64, added, edit_sha)
    S = plan.steps_per_epoch
    real = {"n": 0}

    def stub(model, named, optimizer, examples, micro_batch, max_grad_norm, pad_id, device, chunk, weighting=None):
        for i in range(0, len(examples), micro_batch):
            ids, _ = en._right_padded([e.input_ids for e in examples[i:i + micro_batch]], pad_id, "cpu")
            real["n"] += ids.numel()
        return {"loss": 0.0, "example_losses": [0.0] * len(examples), "grad_norm_preclip": 0.0}

    saved = en.train_step
    en.train_step = stub
    try:
        run_dir = Path(tempfile.mkdtemp(dir=tmpdir))
        policy = SimpleNamespace(model=None, named=[], codec=SimpleNamespace(pad_id=0), device="cpu")
        opt = SimpleNamespace(param_groups=[{"lr": 1e-4}])
        train = {"lr_schedule": "constant", "lr": 1e-4, "micro_batch": 2, "max_grad_norm": 1.0,
                 "lm_head_chunk_tokens": 0}
        counts = runner._train_segment(policy, opt, plan, corpus, 1, S, "e1", train, Ledger(), run_dir)
        lines = [json.loads(x) for x in (run_dir / STEPS).read_text().splitlines()]
    finally:
        en.train_step = saved
    return sum(x["padded_tokens"] for x in lines), counts["padded_tokens"], real["n"], plan.retained, S


def tool(prep, edits, tmp, check=False, name="rec.json"):
    out = tmp / "out" / name
    out.parent.mkdir(exist_ok=True)
    recipe = ec.load_recipe(FAM, None)[0]
    repo_id, rev = tokenizer_of(recipe)
    tk = {"repo_id": repo_id, "revision": rev, "end_of_turn_token": recipe["model"]["end_of_turn_token"]}
    argv = ["--family", FAM, "--prepared", str(tmp / "prep")] + (["--check-a0"] if check else []) + \
        sum((["--edit", f"{p}:{s}"] for p, s in edits), []) + ["--out", str(out)]
    o, e = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
        code = pt.main(argv, context=lambda f, p: ec.Context(Codec(), tk, ec.MANIFESTS[FAM]), loader=lambda p, s: prep)
    raw = out.read_text() if out.exists() else ""
    leak = any(SENT in t or " a a a" in t or " b b b" in t for t in (o.getvalue(), e.getvalue(), raw))
    return code, (json.loads(raw) if raw else None), o.getvalue(), e.getvalue(), leak


def main():
    results, ok = [], True
    with tempfile.TemporaryDirectory(dir=OUT.parent) as td:
        tmp = Path(td)
        prep = fixture(611)                                   # 611 rows: 5 steps, last step 99 rows (odd)
        ids = sorted(prep.train_rows)
        cases = {
            "combined": edit_doc(remove=ids[3:40], rewrite=[(ids[50], f"{SENT} " + " ".join(["c"] * 120)),
                                                             (ids[51], f"{SENT} short")],
                                 add=[(f"add-{j:03d}", f"{SENT} q " + " ".join(["d"] * (j % 9)),
                                       f"{SENT} s " + " ".join(["e"] * (5 + 3 * j))) for j in range(23)]),
            "remove_to_512": edit_doc(remove=ids[:99]),       # 512 rows: exactly 4 steps
            "remove_to_513": edit_doc(remove=ids[:98]),       # 513 rows: 5 steps, last step 1 row
            "add_odd": edit_doc(add=[(f"add-{j:03d}", f"{SENT} q x", f"{SENT} s " + " ".join(["f"] * (j + 1)))
                                     for j in range(20)]),   # 631 rows: last step 119 rows
        }
        edits = []
        for name, doc in cases.items():
            p = tmp / "edits" / f"{name}.json"
            p.parent.mkdir(exist_ok=True)
            data = E.edit_bytes(doc)
            p.write_bytes(data)
            edits.append((p, E.sha256_bytes(data), name, doc))
        code, rec, o, e, leak = tool(prep, [(p, s) for p, s, _, _ in edits], tmp)
        results.append({"what": "tool record exit", "code": code, "leak": leak, "stderr_head": e[:200]})
        ok &= code == 0 and not leak
        for p, sha, name, doc in edits:
            d = rec["source"]["edits"][sha]
            per = {}
            for seed in SEEDS:
                L, Lc, P, rows, S = engine_loop(prep, doc, sha, seed, tmp)
                Y, yrows, ysteps = pure_python(prep, doc, seed)
                T = d["padded_tokens_by_seed"][str(seed)]
                per[seed] = (T, L, Lc, P, Y)
                ok &= T == L == Lc == P == Y and rows == yrows == d["rows"] and S == ysteps == d["steps"] == \
                    math.ceil(d["rows"] / 128)
            top = max(v[1] for v in per.values())
            vok = rec["edits"][sha] == top / d["steps"]
            ok &= vok
            results.append({"case": name, "rows": d["rows"], "steps": d["steps"], "value": rec["edits"][sha],
                            "value_is_max_engine_over_S": vok, "seed_dependent": d["seed_dependent"],
                            "T_L_Lcounts_P_Y_by_seed": {str(k): v for k, v in per.items()}})
        # a0 check: tool vs engine loop at every seed
        code, chk, o, e, leak = tool(prep, [], tmp, check=True, name="check.json")
        a0 = {}
        for seed in SEEDS:
            L, Lc, P, rows, S = engine_loop(prep, None, None, seed, tmp)
            Y, _, _ = pure_python(prep, None, seed)
            a0[str(seed)] = (chk["a0"]["padded_tokens_by_seed"][str(seed)], L, P, Y)
            ok &= len(set(a0[str(seed)])) == 1
        results.append({"what": "a0 check (basis differs: exit 1 expected)", "code": code, "leak": leak,
                        "matches": chk["matches"], "rows": chk["a0"]["rows"], "steps": chk["a0"]["steps"],
                        "T_L_P_Y_by_seed": a0})
        ok &= code == 1 and chk["matches"] is False and not leak
    OUT.write_text(json.dumps({"all_equal": ok, "results": results}, indent=1, sort_keys=True))
    print("ALL EQUAL" if ok else "MISMATCH", OUT.name)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
