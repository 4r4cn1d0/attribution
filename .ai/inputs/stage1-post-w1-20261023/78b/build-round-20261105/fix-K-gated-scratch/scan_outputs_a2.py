"""fix-K-gated (second attempt), step 7: the kit's secret_scan.scan_text over every regular file under the given roots
(the pytest basetemps, the mutation runners' outputs and kit copies, the .out/.json/.txt files). Symlinks are never
followed or read (a World may link a file of the main checkout); a mutation copy's repo/ is scanned at
repo/runkit/stage1-78b only (its other entries are links to the main checkout). Prints counts and relative paths of
hits only, never matched text.
    PY2 -I -B scan_outputs_a2.py KIT_SECRET_SCAN_PY ROOT [ROOT ...]
"""
import importlib.util, os, pathlib, re, sys
spec = importlib.util.spec_from_file_location("secret_scan_fixk2", sys.argv[1])
scan = importlib.util.module_from_spec(spec); spec.loader.exec_module(scan)
HF = re.compile(rb"hf_[A-Za-z0-9]{30,}")
files = links = 0
hits, hf = [], []
for root in map(pathlib.Path, sys.argv[2:]):
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        d = pathlib.Path(dirpath)
        if d.name == "repo" and (d / "runkit").is_dir() and not (d / "runkit").is_symlink():
            dirnames[:] = ["runkit"] if "runkit" in dirnames else []
        if d.name == "runkit" and d.parent.name == "repo":
            dirnames[:] = [n for n in dirnames if n == "stage1-78b"]
        dirnames[:] = [n for n in dirnames if not (d / n).is_symlink()]
        for name in filenames:
            p = d / name
            if p.is_symlink() or not p.is_file():
                links += 1
                continue
            files += 1
            data = p.read_bytes()
            for pat in scan.scan_text(data.decode("utf-8", "ignore")):
                hits.append((pat, str(p.relative_to(root.parent))))
            if HF.search(data):
                hf.append(str(p.relative_to(root.parent)))
print(f"files {files}; symlinks or non-regular skipped {links}; secret_scan hits {len(hits)}; files with the HF token pattern {len(hf)}")
for pat, rel in hits:
    print(f"  hit {pat}: {rel}")
