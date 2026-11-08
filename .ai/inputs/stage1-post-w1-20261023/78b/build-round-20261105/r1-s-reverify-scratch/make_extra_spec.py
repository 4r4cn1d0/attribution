"""Writes the re-verifier's extra mutants (RV-*) as a spec in the builder's form; checks each find text occurs once.
Usage: PY -B make_extra_spec.py WS OUT.json"""
import json, pathlib, sys
ws, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
M = []
def add(i, f, d, find, rep):
    M.append({"id": i, "file": f, "describes": d, "find": find, "replace": rep})
BS, SIM = "blinded_sigma.py", "sr2_simulation.py"
add("RV-bs-side-file-repo-root", BS, "every cell's U is written to a side file at the repository root (outside the snapshot folders)",
    "    sigma, df = pooled_sigma(clusters)\n",
    "    (ROOT / \"leak-cells.txt\").write_text(repr({k: {str(c): float(v) for c, v in t.items()} for k, t in clusters.items()}))\n    sigma, df = pooled_sigma(clusters)\n")
add("RV-bs-out-wb", BS, "--out is opened with wb, not the exclusive xb: a file made meanwhile is overwritten",
    'with open(out, "xb") as handle:', 'with open(out, "wb") as handle:')
add("RV-bs-engine-keyset-unchecked", BS, "the engine map's key set is not checked (extra or old-form keys pass the form check)",
    "if not isinstance(engine, dict) or set(engine) != set(ENGINE_ROLES) or not all(hex64(v) for v in engine.values()):",
    "if not isinstance(engine, dict) or not all(hex64(v) for v in engine.values()):")
add("RV-sim-run-ignores-family-sigmas", SIM, "simulate_row prints the per-family sigmas but runs both families at the grid's sigma",
    "            run_chunk(z, eta, sigmas, share, option, stopped, settings, tallies, plans, designs)",
    "            run_chunk(z, eta, {f: num(sigma_text) for f in FAMILIES}, share, option, stopped, settings, tallies, plans, designs)")
add("RV-sim-max-olmo-only", SIM, "the summary's largest familywise rate is taken over OLMo-2-7B only",
    "            for f, v in sc[\"families\"].items():\n                key = (v[\"familywise_count\"], -r[\"sigma_index\"], name, f)",
    "            for f, v in sc[\"families\"].items():\n                if f != \"olmo2-7b\":\n                    continue\n                key = (v[\"familywise_count\"], -r[\"sigma_index\"], name, f)")
add("RV-sim-max-skips-ratio-scenarios", SIM, "the summary's largest familywise rate skips the two family-ratio scenarios (R-12)",
    "        for name, sc in r[\"scenarios\"].items():\n            for f, v in sc[\"families\"].items():\n                key",
    "        for name, sc in r[\"scenarios\"].items():\n            if sc[\"llama_sigma_ratio\"] != \"1\":\n                continue\n            for f, v in sc[\"families\"].items():\n                key")
add("RV-sim-refused-total-zero", SIM, "the summary's refused-contrast total is always 0 (SV-7)",
    '"refused_contrasts_total": refused,', '"refused_contrasts_total": 0,')
add("RV-sim-n-plan-olmo-only", SIM, "N's printed plan pools OLMo-2-7B's cells for both families",
    "    n_plan = plan_of(sigma_pool_sq(n_prompt_values(y_all, eta,",
    "    n_plan = plan_of(sigma_pool_sq(n_prompt_values({f: y_all[\"olmo2-7b\"] for f in FAMILIES}, eta,")
add("RV-sim-threshold-ge", SIM, "the mechanical flag fires at a rate equal to the threshold, not only above it",
    '"max_above_threshold": bool(p > threshold),', '"max_above_threshold": bool(p >= threshold),')
add("RV-sim-sigma-a-on-other-draws", SIM, "sigma_A is computed on another replicate's cells (the claim test keeps its own)",
    "    a_plan = plan_of(sigma_a_sq(y_all, option, stopped)[0], settings)",
    "    a_plan = plan_of(sigma_a_sq({f: np.roll(v, 1, axis=0) for f, v in y_all.items()}, option, stopped)[0], settings)")
add("RV-sim-claim-rows-misindexed", SIM, "the claim test reads the first k replicates, not the plan's rows",
    "            res = claim_test(design, y_all[f][rows], settings)",
    "            res = claim_test(design, y_all[f][:rows.size], settings)")
add("RV-sim-claim-other-family", SIM, "each family's claim test reads the other family's cells",
    "            res = claim_test(design, y_all[f][rows], settings)",
    "            res = claim_test(design, y_all[FAMILIES[1 - FAMILIES.index(f)]][rows], settings)")
pkg = ws / "scripts/scale78b"
for m in M:
    n = (pkg / m["file"]).read_text().count(m["find"])
    assert n == 1, (m["id"], n)
out.write_text(json.dumps({"kind": "re-verifier extra mutants", "mutants": M}, indent=1) + "\n")
print(len(M), "mutants; each find text occurs once")
