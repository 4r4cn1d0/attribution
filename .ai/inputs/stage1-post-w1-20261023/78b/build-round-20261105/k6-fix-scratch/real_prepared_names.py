"""K6 read-only probe of the two real 7-8B prepared folders: names only. Lists every file's relative name (no file
opened), reads manifest.json's "files" KEYS (names) and compares manifest.json's SHA-256 with manifest.sha256's text
and the kit's pin; runs the kit's secret scan (pattern names only) on the files the K6 rule would scan that are not
listed and not macOS metadata. Never opens a listed file (the engine's data, selector and hidden files).
Usage: PY -B -I real_prepared_names.py ROOT SECRET_SCAN_PY"""
import hashlib
import importlib.util
import json
import pathlib
import sys

root, scan_py = pathlib.Path(sys.argv[1]), sys.argv[2]
spec = importlib.util.spec_from_file_location("ss_k6", scan_py)
ss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ss)
PINS = {"prepared-kt-dolly-olmo2": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9",
        "prepared-kt-dolly-llama3": "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"}
META = {".DS_Store", ".localized", "Icon\r", ".Spotlight-V100", ".Trashes", ".fseventsd", ".TemporaryItems",
        ".DocumentRevisions-V100", ".VolumeIcon.icns", ".apdisk", ".com.apple.timemachine.donotpresent"}
for name, pin in PINS.items():
    folder = root / "tmp" / "kt-prepared" / name
    names = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file() and not p.is_symlink())
    links = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_symlink())
    man_bytes = (folder / "manifest.json").read_bytes()
    man_sha = hashlib.sha256(man_bytes).hexdigest()
    listed = set(json.loads(man_bytes)["files"])
    unlisted = [n for n in names if n not in listed]
    meta = [n for n in unlisted if any(part in META or part.startswith("._") for part in n.split("/"))]
    to_scan = [n for n in unlisted if n not in meta]
    hits = {n: ss.scan_text((folder / n).read_bytes().decode("utf-8", "ignore")) for n in to_scan}
    print(json.dumps({"folder": name, "files": len(names), "links": len(links), "listed": len(listed),
                      "listed_present": len(listed & set(names)), "manifest_at_sha256_file":
                      man_sha == (folder / "manifest.sha256").read_text().strip(), "manifest_at_kit_pin": man_sha == pin,
                      "unlisted_macos_metadata": meta, "unlisted_scanned": to_scan,
                      "scan_pattern_hits": {n: h for n, h in hits.items() if h}}))
