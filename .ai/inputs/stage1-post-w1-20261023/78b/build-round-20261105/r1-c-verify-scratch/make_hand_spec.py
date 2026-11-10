"""Verifier scratch: hand mutants for Track C (written into the scratch source copy only, never into WS)."""
import json, sys
from pathlib import Path
src = Path(sys.argv[1]) / "scripts/scale78b"
EC, TL = "encode_count_78b.py", "tau_l_78b.py"
M = [
 ("V-bank-guard-add", EC, "    for _, prompt in loaded.rows:\n        guard.add(prompt)\n", "    for _, prompt in loaded.rows:\n        pass\n", "bank mode: bank prompts never enter the text guard"),
 ("V-anchor-guard-add", EC, "        guard.add(p[\"prompt\"], p[\"unsafe_response\"])\n", "        pass\n", "anchor mode: anchor texts never enter the text guard"),
 ("V-guard-no-responses", EC, "        guard.add(item.get(\"prompt\"), item.get(\"response\"))\n", "        guard.add(item.get(\"prompt\"))\n", "lists mode: responses never enter the text guard"),
 ("V-train-catch-all", EC, "            encode_train(codec, row_id, prompt, response, max_tokens)\n        except ValueError as exc:", "            encode_train(codec, row_id, prompt, response, max_tokens)\n        except Exception as exc:", "encode_train: any exception counted as a refusal"),
 ("V-s4-ids-unchecked", EC, "    for name in (\"s1\", \"s4_candidates\"):\n        if ids[name] != record_ids[name]:", "    for name in (\"s1\",):\n        if ids[name] != record_ids[name]:", "s4_candidates ids not checked against the record"),
 ("V-record-size", EC, "        if entry.get(\"sha256\") != digest or not isinstance(got, list) or len(got) != size:", "        if entry.get(\"sha256\") != digest or not isinstance(got, list):", "record list size not checked"),
 ("V-out-exists", EC, "    out = Path(out).resolve()\n    if out.exists() or out.is_symlink():\n        raise Refusal(f\"--out {out.name} exists: the record is created once\")\n    parent = out.parent\n    if not parent.is_dir():\n        raise Refusal(\"--out's folder does not exist\")\n    for folder in folders:", "    out = Path(out).resolve()\n    if False:\n        raise Refusal(f\"--out {out.name} exists: the record is created once\")\n    parent = out.parent\n    if not parent.is_dir():\n        raise Refusal(\"--out's folder does not exist\")\n    for folder in folders:", "encode out_ok: existing --out not refused before the run"),
 ("V-record-cmdline-pin", EC, "    pinned(record[1], record_pin, \"the s-pool record\")\n", "    pass\n", "lists: the s-pool record's command-line SHA-256 not checked"),
 ("V-hex-check", EC, "    if not sep or not path or len(digest) != 64 or any(c not in \"0123456789abcdef\" for c in digest):", "    if not sep or not path or len(digest) != 64:", "parse_spec accepts upper-case or non-hex digests"),
 ("V-bank-record-cmdline", EC, "    pinned(record[1], record_pin, \"the O-ext bank record\")\n", "    pass\n", "bank: the record's command-line SHA-256 not checked"),
 ("V-guard-min-chars", EC, "    def __init__(self, min_chars: int = 6):", "    def __init__(self, min_chars: int = 10**6):", "text guard scans nothing"),
 ("V-tl-sum", TL, "    mean = math.fsum(losses.values()) / len(losses)", "    mean = sum(losses.values()) / len(losses)", "tau_L: plain sum instead of math.fsum"),
 ("V-tl-pin-source", TL, "                                       \"pin_source\": (\"literal\" if pins[u[\"seed\"]] is not None", "                                       \"pin_source\": (\"literal\" if True", "tau_L: the record never marks a command-line pin"),
 ("V-tl-ids-unsorted", TL, "            \"query_ids\": sorted(losses), \"mean\": mean}", "            \"query_ids\": list(losses), \"mean\": mean}", "tau_L: the units' id sets compared in file order"),
 ("V-tl-out-exists", TL, "    out = Path(out).resolve()\n    if out.exists() or out.is_symlink():", "    out = Path(out).resolve()\n    if False:", "tau_L out_ok: existing --out not refused before the run"),
 ("V-tl-finite-loss", TL, "        if isinstance(loss, bool) or not isinstance(loss, (int, float)) or not math.isfinite(loss):", "        if isinstance(loss, bool) or not isinstance(loss, (int, float)):", "tau_L: non-finite loss accepted (strict_json rejects NaN/Infinity constants; 1e999 overflow?)"),
 ("V-tl-recorded-finite", TL, "    if isinstance(recorded, bool) or not isinstance(recorded, (int, float)) or not math.isfinite(recorded):", "    if isinstance(recorded, bool) or not isinstance(recorded, (int, float)):", "tau_L: non-finite recorded mean accepted"),
 ("V-tl-family-ti", TL, "    if identity.get(\"training_identity\") != TRAINING_IDENTITY[family]:", "    if identity.get(\"training_identity\") != TRAINING_IDENTITY[\"olmo2-7b\"]:", "tau_L: Llama units checked against OLMo's training identity"),
]
out = []
for mid, f, find, repl, desc in M:
    text = (src / f).read_text()
    n = text.count(find)
    assert n == 1, (mid, n)
    out.append({"id": mid, "file": f, "find": find, "replace": repl, "describes": desc})
(src / "tests/mutation_spec_c_78b.json").write_text(json.dumps({"mutants": out}, indent=1) + "\n")
print(len(out), "hand mutants")
