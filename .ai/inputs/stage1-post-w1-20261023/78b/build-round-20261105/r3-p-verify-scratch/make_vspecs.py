import json, sys, pathlib
V = pathlib.Path(sys.argv[1])
P = [
 ("V-guard-rewrite", "the rewritten responses are not guarded", "padded_tokens_78b.py",
  '                guard.add(item.get("response"))\n', '                pass\n'),
 ("V-largest-at-max", "largest_at_seed names the last tied seed", "padded_tokens_78b.py",
  '"largest_at_seed": min(s for s, t in totals.items() if t == top),', '"largest_at_seed": max(s for s, t in totals.items() if t == top),'),
 ("V-tool-sha", "source.tool_sha256 is a constant", "padded_tokens_78b.py",
  '"tool_sha256": sha256_file(Path(__file__)),', '"tool_sha256": "0" * 64,'),
 ("V-engine-files", "source.engine_files are constants", "padded_tokens_78b.py",
  '"engine_files": {p: sha256_file(REPO / p) for p in ENGINE_FILES},', '"engine_files": {p: "0" * 64 for p in ENGINE_FILES},'),
 ("V-seed-shift", "every seed's stream is another seed's", "padded_tokens_78b.py",
  '        plan = plan_for(prepared, settings, seed, edit)\n', '        plan = plan_for(prepared, settings, seed + 7, edit)\n'),
 ("V-div-fraction", "S = rows / 128 (no ceiling) as the divisor", "padded_tokens_78b.py",
  'values[pin] = per_step(top, out["steps"])', 'values[pin] = per_step(top, out["rows"] / 128)'),
 ("V-second-largest", "the second largest seed total", "padded_tokens_78b.py",
  '        top = max(totals.values())\n', '        top = sorted(totals.values())[-2]\n'),
 ("V-check-no-value", "the check ignores the per-step value", "padded_tokens_78b.py",
  'matches = total == basis_total and steps == basis_steps and round(value, 2) == basis_value',
  'matches = total == basis_total and steps == basis_steps'),
 ("V-check-no-steps", "the check ignores the steps", "padded_tokens_78b.py",
  'matches = total == basis_total and steps == basis_steps and round(value, 2) == basis_value',
  'matches = total == basis_total and round(value, 2) == basis_value'),
 ("V-check-exit", "a differing check exits 0", "padded_tokens_78b.py",
  '    if doc["kind"] == CHECK_KIND and not doc["matches"]:\n', '    if doc["kind"] == CHECK_KIND and doc["matches"] is None:\n'),
 ("V-mb-last-row", "each micro-batch padded to its last row", "padded_tokens_78b.py",
  'total += sum(len(mb) * max(len(e.input_ids) for e in mb) for mb in micro_batches(examples, micro_batch))',
  'total += sum(len(mb) * len(mb[-1].input_ids) for mb in micro_batches(examples, micro_batch))'),
 ("V-out-no-edit-folders", "--out may lie in an edit's folder", "padded_tokens_78b.py",
  'out = ec.out_ok(args.out, [Path(p).resolve().parent for p, _ in edits] + [args.prepared])',
  'out = ec.out_ok(args.out, [args.prepared])'),
 ("V-scan-lines-only", "the record bytes are not scanned", "padded_tokens_78b.py",
  '        if guard.hits(data) or any(guard.hits(line) for line in lines):\n',
  '        if any(guard.hits(line) for line in lines):\n'),
 ("V-guard-name", "the edit's name is not guarded", "padded_tokens_78b.py",
  '            guard.add(doc.get("name"))\n', '            pass\n'),
]
O = [
 ("V-m-dotdot", "W2-5: a reader path with a '..' or empty part under scripts/ is accepted", "make_oext_settings_78b.py",
  '                and all(q not in ("", ".", "..") for q in rel.split("/"))):', '                and True):'),
 ("V-m-py", "W2-5: a reader path that is not .py is accepted", "make_oext_settings_78b.py",
  'rel.startswith("scripts/") and rel.endswith(".py")\n', 'rel.startswith("scripts/")\n'),
 ("V-m-first-family", "W2-5: only the first family's readers are checked and listed", "make_oext_settings_78b.py",
  '        out.update(frozen_reader_pins(limits, family))', '        out.update(frozen_reader_pins(limits, family) if family == FAMILIES[0] else {})'),
 ("V-w-index-identity", "W2-4: the W1-18 settings under the index's identity", "oext_78b.py",
  '                engine = ENGINE_X_IDENTITY                # W2-4: W1-18 runs on engine X, whatever runs this check\n',
  '                engine = identity if identity is not None else running\n'),
]
def spec(ms, kind):
    out = []
    for i, d, f, a, b in ms:
        text = (V / "scripts/scale78b" / f).read_text()
        assert text.count(a) == 1, (i, text.count(a))
        out.append({"id": i, "describes": d, "file": f, "find": a, "replace": b})
    return {"kind": kind, "note": "R3 Track P verifier's own mutants", "mutants": out}
(V / "scripts/scale78b/tests/mutation_spec_p_78b.json").write_text(json.dumps(spec(P, "verifier P"), indent=1) + "\n")
(V / "scripts/scale78b/tests/oext/mutation_spec_oext_78b.json").write_text(json.dumps(spec(O, "verifier O"), indent=1) + "\n")
print(len(P), len(O), "each find once")
