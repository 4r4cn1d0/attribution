"""Scan every file a test run left behind (and every member of every tarball there) for the kit's secret patterns.
Prints counts, relative paths and pattern names only, never the matched text. Usage: PY -B -I scan_left.py ROOT SCAN"""
import collections
import importlib.util
import pathlib
import sys
import tarfile

root, scan_py = pathlib.Path(sys.argv[1]), sys.argv[2]
spec = importlib.util.spec_from_file_location("ss_k5v", scan_py)
ss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ss)
MARKS = ("K5K5K5", "R5R5R5")                       # the fixer's two test-built fakes (counted, never printed)
files = hits = members = 0
by_pattern, where, marks = collections.Counter(), collections.Counter(), collections.Counter()
examples = collections.defaultdict(list)
for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
    files += 1
    data = path.read_bytes()
    text = data.decode("utf-8", "ignore")
    found = ss.scan_text(text)
    for m in MARKS:
        marks[m] += text.count(m)
    for name in found:
        hits += 1
        by_pattern[name] += 1
        rel = str(path.relative_to(root))
        where[rel.split("/")[0]] += 1
        if len(examples[name]) < 40:
            examples[name].append(rel)
    if path.name.endswith((".tar.gz", ".tgz", ".tar")):
        try:
            with tarfile.open(path) as tf:
                for info in tf:
                    if not info.isfile():
                        continue
                    members += 1
                    body = tf.extractfile(info).read().decode("utf-8", "ignore")
                    for m in MARKS:
                        marks[m] += body.count(m)
                    for name in ss.scan_text(body):
                        hits += 1
                        by_pattern[name] += 1
                        rel = f"{path.relative_to(root)}::{info.name}"
                        if len(examples[name]) < 40:
                            examples[name].append(rel)
        except (tarfile.TarError, OSError, EOFError) as exc:
            print("unreadable tar:", path.relative_to(root), type(exc).__name__)
print({"files": files, "tar_members": members, "hits": hits, "by_pattern": dict(by_pattern),
       "fake_marks": dict(marks)})
for name, rels in examples.items():
    print(name, len(rels), "example paths (up to 40):")
    for rel in rels:
        print("   ", rel)
