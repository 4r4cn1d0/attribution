"""K5 re-verifier's scratch probe (not for merge). P1: the R4 premise for data/ ("its manifest SHA-256 pins every
byte"). The pack ships every file of the prepared folder, scans none under data/, and checks only manifest.sha256's
TEXT at pack time. A token-shaped string (built here, never a token) in prepare_receipt.json (outside the manifest
hash, engine prepare.py:71) or in a stray file (.DS_Store) is shipped in the bundle. Prints counts only; every file
holding the string is deleted before the test ends."""
from __future__ import annotations

import hashlib
import shutil
import tarfile

from test_scorer_block_78b import so  # noqa: F401  (the fixture)


def _sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_p1_the_pack_ships_an_unpinned_unscanned_file_of_the_prepared_folder(so):
    w = so
    fake = "hf_" + "Zq" * 17                              # the HF token's shape, built at test time; not a token
    w.pack()                                             # a clean pack (writes the synthetic prepared folder)
    folder = w.repo / w.rules.PREPARED_LOCAL / w.rules.PREPARED_NAME
    digest = w.rules.PREPARED_MANIFESTS[w.rules.PREPARED_NAME]
    out = w.root / "setup" / "packed-stage1-X"
    planted = [folder / "prepare_receipt.json", folder / ".DS_Store"]
    try:
        assert _sha(folder / "manifest.json") != digest   # the synthetic manifest.json is NOT at the pin ...
        for p in planted:
            p.write_text('{"note": "' + fake + '"}\n')
        w.pack()                                         # ... and the pack still goes through, with the planted files
        bundle = out / "bundle-stage1-X.tar.gz"
        with tarfile.open(bundle) as tf:
            names = [m.name for m in tf if m.isfile()]
            hits = [n for n in names if n.startswith("data/")
                    and fake.encode() in tf.extractfile(n).read()]
        print("P1 data/ members:", sum(n.startswith("data/") for n in names), "holding the planted string:", len(hits),
              sorted(n.rsplit("/", 1)[-1] for n in hits))
        assert len(hits) == 2
    finally:
        for p in planted:
            p.unlink(missing_ok=True)
        for part in out.parent.glob("packed-stage1-X*"):
            shutil.rmtree(part, ignore_errors=True)
