"""fix-K-gated step 7: the kit's secret_scan over every record, log and test output this round wrote (the pytest
basetemps, the mutation runners' copies and reports), plus a count of files holding the HF token pattern. Prints paths
and counts only, never matched text.
    PY2 -I -B scan_outputs.py KIT_SECRET_SCAN_PY ROOT [ROOT ...]
"""
import importlib.util
import pathlib
import re
import sys

spec = importlib.util.spec_from_file_location("secret_scan_fixk", sys.argv[1])
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)
HF = re.compile(rb"hf_[A-Za-z0-9]{30,}")
total_files, total_hits, hf_files = 0, [], []
for root in sys.argv[2:]:
    root = pathlib.Path(root)
    if not root.exists():
        print(f"{root}: missing")
        continue
    result = scan.scan_tree(root)
    files = [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]
    total_files += len(files)
    hits = result["secret_hits"] + result["model_text_pattern_hits"]
    total_hits += [(str(root), rel, name) for rel, name in hits]
    for p in files:
        try:
            if HF.search(p.read_bytes()):
                hf_files.append(str(p.relative_to(root)))
        except OSError:
            pass
    print(f"{root}: files {len(files)}; secret_hits {len(result['secret_hits'])}; model_text_hits {len(result['model_text_pattern_hits'])}")
print(f"TOTAL files {total_files}; hits {len(total_hits)}")
for root, rel, name in total_hits:
    print(f"  hit: {name}: {root}/{rel}")
print(f"files holding the HF token pattern: {len(hf_files)}")
for rel in hf_files:
    print(f"  {rel}")
