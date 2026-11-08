"""Re-verifier scratch: hand mutants for the Track C fix round, written into the scratch source copy only (never WS)."""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1]) / "scripts/scale78b"
EC, TL = "encode_count_78b.py", "tau_l_78b.py"
BLOCK = ('        with open(partial, "xb") as handle:\n            created = True\n            handle.write(data)\n'
         '            handle.flush()\n            os.fsync(handle.fileno())\n        os.link(partial, out)\n')
LINK_FIRST = ('        with open(partial, "xb") as handle:\n            created = True\n            os.link(partial, out)\n'
              '            handle.write(data)\n            handle.flush()\n            os.fsync(handle.fileno())\n')
CREATED = ('    created = False\n    try:\n        with open(partial, "xb") as handle:\n            created = True\n')
CREATED_EARLY = ('    created = True\n    try:\n        with open(partial, "xb") as handle:\n            created = True\n')
M = [
    ("H-ec-link-first", EC, BLOCK, LINK_FIRST, "encode: --out is linked before the bytes are written (a failed write leaves a truncated --out)"),
    ("H-tl-link-first", TL, BLOCK, LINK_FIRST, "tau_L: --out is linked before the bytes are written"),
    ("H-ec-replace", EC, "        os.link(partial, out)\n", "        os.replace(partial, out)\n", "encode: rename over --out (an existing --out is overwritten)"),
    ("H-tl-replace", TL, "        os.link(partial, out)\n", "        os.replace(partial, out)\n", "tau_L: rename over --out"),
    ("H-ec-created-early", EC, CREATED, CREATED_EARLY, "encode: a pre-existing partial file (not this process's) is deleted"),
    ("H-tl-created-early", TL, CREATED, CREATED_EARLY, "tau_L: a pre-existing partial file is deleted"),
    ("H-ec-no-fsync", EC, "            os.fsync(handle.fileno())\n", "            pass\n", "encode: no fsync before the link"),
    ("H-ec-oserror-escapes", EC, "    except OSError as exc:\n        raise Refusal(f\"--out cannot be written ({type(exc).__name__})\") from None\n", "", "encode: an OSError of the write is not turned into a refusal"),
    ("H-anchor-no-unsafe", EC, "        guard.add(p[\"prompt\"], p[\"unsafe_response\"])\n", "        guard.add(p[\"prompt\"])\n", "anchor mode: unsafe responses never enter the guard"),
    ("H-lists-no-prompts", EC, "        guard.add(item.get(\"prompt\"), item.get(\"response\"))\n", "        guard.add(item.get(\"response\"))\n", "lists mode: prompts never enter the guard"),
    ("H-printout-unscanned", EC, "        if guard.hits(data) or any(guard.hits(line) for line in lines):\n", "        if guard.hits(data):\n", "the printout is not scanned"),
    ("H-tl-exit-message", TL, "        print(f\"REFUSED: {type(exc).__name__} (nothing written)\", file=sys.stderr)\n", "        print(f\"REFUSED: {exc} (nothing written)\", file=sys.stderr)\n", "tau_L: an unexpected exception's message is printed"),
    ("H-tl-write-bytes", TL, "            write_once(out, data)\n", "            out.write_bytes(data)\n", "tau_L: a direct write (no temporary file, overwrite)"),
    ("V-record-cmdline-pin", EC, "    pinned(record[1], record_pin, \"the s-pool record\")\n", "    pass\n", "lists: the s-pool record's command-line SHA-256 not checked (first verifier's survivor; C9)"),
    ("V-tl-ids-unsorted", TL, "            \"query_ids\": sorted(losses), \"mean\": mean}", "            \"query_ids\": list(losses), \"mean\": mean}", "tau_L: id sets compared in file order (first verifier's survivor; C9)"),
]
out = []
for mid, f, find, repl, desc in M:
    text = (src / f).read_text()
    n = text.count(find)
    assert n == 1, (mid, n)
    out.append({"id": mid, "part": "re-verify", "file": f, "find": find, "replace": repl, "describes": desc})
(src / "tests/mutation_spec_c_78b.json").write_text(json.dumps({"kind": "hand", "note": "re-verifier", "mutants": out}, indent=1) + "\n")
print(len(out), "hand mutants")
