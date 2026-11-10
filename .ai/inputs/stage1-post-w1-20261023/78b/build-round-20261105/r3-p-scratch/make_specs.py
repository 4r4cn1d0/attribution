"""Builds R3 Track P's mutation spec and appends R3's O-ext mutants (each find checked to occur exactly once)."""
import json, sys
from pathlib import Path

WS = Path(sys.argv[1])
PKG = WS / "scripts/scale78b"

P = [
 ("P-m-edit-pin", "an edit is read without its pin check", 'data = ec.read_pinned(path, pin, f"the edit {pin[:12]}...")', 'data = Path(path).read_bytes()'),
 ("P-m-edit-twice", "an edit SHA-256 named twice is accepted", '    if len(set(pins)) != len(pins):\n', '    if False:\n'),
 ("P-m-no-edits", "a record with no edit is written", '    if not edits:\n        raise Refusal("give every', '    if False:\n        raise Refusal("give every'),
 ("P-m-manifest", "P_F off the manifest pin is accepted", '    if prepared.manifest_sha256 != pin or ctx.manifest_sha256 != pin:\n', '    if False:\n'),
 ("P-m-ctx-manifest", "the tokenizer's manifest off the pin is accepted", 'if prepared.manifest_sha256 != pin or ctx.manifest_sha256 != pin:', 'if prepared.manifest_sha256 != pin:'),
 ("P-m-tokenizer", "the tokenizer is not checked against the recipe's", '    tokenizer = ec.check_tokenizer(recipe, ctx)\n', '    tokenizer = dict(ctx.tokenizer)\n'),
 ("P-m-recipe-pin", "MAIN_F is loaded without its config pin", '    recipe, digest, recipe_path, _limits = ec.load_recipe(family, recipe_arg)\n', '    from experiments.safety_selection.config import config_sha256, load_recipe as _lr\n    _p = Path(recipe_arg) if recipe_arg is not None else REPO / ec.RECIPES[family][0]\n    recipe = _lr(_p); digest, recipe_path = config_sha256(recipe), str(_p)\n'),
 ("P-m-batch-128", "a step of another size than 128 rows is accepted", '    if micro * accum != ROWS_PER_STEP:\n', '    if False:\n'),
 ("P-m-e1", "a recipe without e1 at one epoch is accepted", '    if table.get(TARGET) != Fraction(1):\n', '    if False:\n'),
 ("P-m-steps-floor", "steps = floor(rows / 128)", '    steps = -(-rows // ROWS_PER_STEP)\n', '    steps = rows // ROWS_PER_STEP\n'),
 ("P-m-steps-check", "the stream's steps are not checked against ceil(rows / 128)", '    if plan.steps_per_epoch != steps or plan.checkpoint(Fraction(1))["step"] != steps:\n', '    if False:\n'),
 ("P-m-steps-e1", "the e1 checkpoint's step is not checked", 'if plan.steps_per_epoch != steps or plan.checkpoint(Fraction(1))["step"] != steps:', 'if plan.steps_per_epoch != steps:'),
 ("P-m-last-step", "the epoch's final step is not counted", '    for step, _epoch, rows in plan.iterate(1, steps):\n', '    for step, _epoch, rows in plan.iterate(1, max(1, steps - 1)):\n'),
 ("P-m-no-padding", "a micro-batch counts its tokens, not its padded width", 'total += sum(len(mb) * max(len(e.input_ids) for e in mb) for mb in micro_batches(examples, micro_batch))', 'total += sum(sum(len(e.input_ids) for e in mb) for mb in micro_batches(examples, micro_batch))'),
 ("P-m-micro-1", "micro-batches of one row", 'for mb in micro_batches(examples, micro_batch))', 'for mb in micro_batches(examples, 1))'),
 ("P-m-micro-step", "the whole step padded as one batch", 'for mb in micro_batches(examples, micro_batch))', 'for mb in [examples])'),
 ("P-m-seed-min", "the smallest over seeds", '        top = max(totals.values())\n', '        top = min(totals.values())\n'),
 ("P-m-seed-first", "the first seed's value", '        top = max(totals.values())\n', '        top = totals[SEEDS[0]]\n'),
 ("P-m-seeds-six", "seeds 1101-1106 only", 'SEEDS = tuple(range(1101, 1108))', 'SEEDS = tuple(range(1101, 1107))'),
 ("P-m-seed-fixed", "every plan at seed 1101", '        plan = plan_for(prepared, settings, seed, edit)\n', '        plan = plan_for(prepared, settings, 1101, edit)\n'),
 ("P-m-seed-dependent", "seed_dependent always false (record)", '"seed_dependent": len(set(totals.values())) > 1}', '"seed_dependent": False}'),
 ("P-m-largest-seed", "largest_at_seed names the first seed", '"largest_at_seed": min(s for s, t in totals.items() if t == top),', '"largest_at_seed": SEEDS[0],'),
 ("P-m-removed", "the edit's removed rows are trained", '    return make_plan(prepared.corpus, sorted(edit.removed), seed,', '    return make_plan(prepared.corpus, [], seed,'),
 ("P-m-added", "the edit's added rows are not trained", '                     edit.added_ids, edit.sha256)\n', '                     (), edit.sha256)\n'),
 ("P-m-rewrite", "the corpus without the edit's rewrites and adds", '            mine = edited_corpus(corpus, edit, prepared, ctx.codec, settings["max_train_tokens"])\n', '            mine = {**corpus, **{r: e for r, e in edited_corpus(corpus, edit, prepared, ctx.codec, settings["max_train_tokens"]).items() if r not in corpus}}\n'),
 ("P-m-audit", "rows encoded without the prepared audit check", '        return {rid: _verified_example(codec, rid, row, recipe) for rid, row in sorted(prepared.train_rows.items())}\n', '        from experiments.safety_selection.textproc import encode_train\n        return {rid: encode_train(codec, rid, row["prompt"], row["response"], recipe["model"]["max_train_tokens"]) for rid, row in sorted(prepared.train_rows.items())}\n'),
 ("P-m-per-step", "the total, not per step", '        values[pin] = per_step(top, out["steps"])\n', '        values[pin] = float(top)\n'),
 ("P-m-per-step-div", "per step over steps + 1", '    return total / steps\n', '    return total / (steps + 1)\n'),
 ("P-m-kind", "another record kind", 'KIND = "stage1-78b padded tokens record"', 'KIND = "stage1-78b padded token record"'),
 ("P-m-version", "version 2", 'return {"kind": KIND, "version": 1, "family": family,', 'return {"kind": KIND, "version": 2, "family": family,'),
 ("P-m-extra-key", "an extra top-level key", '            "utc": utc_now(), "recorded_by": recorded_by}', '            "utc": utc_now(), "recorded_by": recorded_by, "rows": 0}'),
 ("P-m-check-seed", "the a0 check at the smallest seed total", '    total, steps = out["totals"][seed], out["steps"]\n', '    total, steps = min(out["totals"].values()), out["steps"]\n'),
 ("P-m-check-match", "the a0 check always matches", '    matches = total == basis_total and steps == basis_steps and round(value, 2) == basis_value\n', '    matches = True\n'),
 ("P-m-check-total", "the a0 check ignores the total", 'matches = total == basis_total and steps == basis_steps and', 'matches = steps == basis_steps and'),
 ("P-m-check-value", "the a0 check ignores the per-step value", 'and steps == basis_steps and round(value, 2) == basis_value\n', 'and steps == basis_steps\n'),
 ("P-m-check-exit", "a difference exits 0", '    if doc["kind"] == CHECK_KIND and not doc["matches"]:\n', '    if False:\n'),
 ("P-m-check-edit", "--check-a0 takes an edit", '        if args.check_a0 and args.edit:\n', '        if False:\n'),
 ("P-m-check-kind", "the check record has the record's kind", 'CHECK_KIND = "stage1-78b padded tokens a0 check"', 'CHECK_KIND = "stage1-78b padded tokens record"'),
 ("P-m-basis-olmo", "OLMo's a0 basis total", '"olmo2-7b": (1103, 1457026, 38, 38342.79)', '"olmo2-7b": (1103, 1457062, 38, 38342.79)'),
 ("P-m-basis-llama", "Llama's a0 basis value", '"llama31-8b": (1103, 1569846, 38, 41311.74)', '"llama31-8b": (1103, 1569846, 38, 41311.47)'),
 ("P-m-guard", "the record and printout are not scanned", '        if guard.hits(data) or any(guard.hits(line) for line in lines):\n', '        if False:\n'),
 ("P-m-guard-lines", "the printout is not scanned", 'if guard.hits(data) or any(guard.hits(line) for line in lines):', 'if guard.hits(data):'),
 ("P-m-guard-rows", "P_F's texts are not guarded", '        guard.add(row.get("prompt"), row.get("response"))\n', '        pass\n'),
 ("P-m-guard-added", "the edit's added texts are not guarded", '                guard.add(item.get("prompt"), item.get("response"))\n', '                pass\n'),
 ("P-m-out-folders", "--out may lie beside an edit", '        out = ec.out_ok(args.out, [Path(p).resolve().parent for p, _ in edits] + [args.prepared])\n', '        out = ec.out_ok(args.out, [args.prepared])\n'),
 ("P-m-out-prepared", "--out may lie inside P_F", '[Path(p).resolve().parent for p, _ in edits] + [args.prepared])', '[Path(p).resolve().parent for p, _ in edits])'),
 ("P-m-edit-message", "an engine refusal's message is printed raw", '        raise Refusal(f"the edit {pin[:12]}... is refused by the engine\'s parse_edit: {exc}") from None\n', '        raise\n'),
]

O = [
 ("R3-w-w1-engine-running", "W2-4: the W1-18 settings under the running engine's identity", 'oext_78b.py', '                engine = ENGINE_X_IDENTITY                # W2-4: W1-18 runs on engine X, whatever runs this check\n', '                engine = running\n'),
 ("R3-w-w1-engine-file", "W2-4: the W1-18 settings under their own engine_x", 'oext_78b.py', '                engine = ENGINE_X_IDENTITY                # W2-4: W1-18 runs on engine X, whatever runs this check\n', '                engine = doc.get("engine_x")\n'),
 ("R3-w-engine-x-literal", "W2-4: another engine X identity", 'oext_78b.py', 'ENGINE_X_IDENTITY = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"', 'ENGINE_X_IDENTITY = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded893"'),
 ("R3-m-readers-dropped", "W2-5: the frozen readers are not listed", 'make_oext_settings_78b.py', '        out.update(frozen_reader_pins(limits, family))', '        frozen_reader_pins(limits, family)'),
 ("R3-m-reader-hash", "W2-5: a reader off its pin is listed", 'make_oext_settings_78b.py', '        if not path.is_file() or sha256_file(path) != pin:\n', '        if not path.is_file():\n'),
 ("R3-m-reader-path", "W2-5: a reader path outside scripts/ is accepted", 'make_oext_settings_78b.py', 'and rel.startswith("scripts/") and rel.endswith(".py")\n                and all(q not in ("", ".", "..") for q in rel.split("/"))):', '):'),
 ("R3-m-reader-keys", "W2-5: the frozen_reader block's keys are not checked", 'make_oext_settings_78b.py', '    if not isinstance(spec, dict) or set(spec) != set(FROZEN_READERS):\n', '    if not isinstance(spec, dict):\n'),
]


def once(text, find, ident):
    n = text.count(find)
    if n != 1:
        raise SystemExit(f"{ident}: find occurs {n} times")


tool = (PKG / "padded_tokens_78b.py").read_text()
mutants = []
for ident, what, find, rep in P:
    once(tool, find, ident)
    mutants.append({"id": ident, "describes": what, "file": "padded_tokens_78b.py", "find": find, "replace": rep})
spec = {"kind": "scale78b track P mutation spec (R3: padded_tokens_78b.py)",
        "note": "each find occurs exactly once in its file (a path under scripts/scale78b); runner: "
                "tests/run_mutants_p_78b.py (tests/test_padded_tokens_78b.py)", "mutants": mutants}
(PKG / "tests/mutation_spec_p_78b.json").write_text(json.dumps(spec, indent=1) + "\n")
print("P mutants:", len(mutants))

opath = PKG / "tests/oext/mutation_spec_oext_78b.json"
odoc = json.loads(opath.read_text())
have = {m["id"] for m in odoc["mutants"]}
for ident, what, file, find, rep in O:
    once((PKG / file).read_text(), find, ident)
    if ident not in have:
        odoc["mutants"].append({"id": ident, "describes": what, "file": file, "find": find, "replace": rep})
if "R3 (Track P)" not in odoc["note"]:
    odoc["note"] += " R3 (Track P): 7 new (R3-*: W2-4, W2-5)."
opath.write_text(json.dumps(odoc, indent=1, ensure_ascii=False) + "\n")
print("O-ext mutants:", len(odoc["mutants"]))
