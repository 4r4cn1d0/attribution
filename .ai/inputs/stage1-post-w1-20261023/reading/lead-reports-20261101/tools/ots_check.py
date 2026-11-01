"""Check each completed OpenTimestamps proof without a Bitcoin node: for every Bitcoin attestation in the proof, the
commitment the proof computes from the file's SHA-256 must equal that block's merkle root, as two independent public
block explorers report it (blockstream.info and mempool.space). Prints JSON lines; writes a record (exclusive create).

    ots-venv/bin/python -I ots_check.py OUT_RECORD FILE [FILE ...]      (each FILE has FILE.ots beside it)
"""
import datetime as dt
import hashlib
import json
import sys
import urllib.request

from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
from opentimestamps.core.serialize import StreamDeserializationContext
from opentimestamps.core.timestamp import DetachedTimestampFile

SOURCES = {"blockstream.info": "https://blockstream.info/api", "mempool.space": "https://mempool.space/api"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "stage1-ots-check"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def block(source, height):
    base = SOURCES[source]
    block_hash = get(f"{base}/block-height/{height}").strip()
    info = json.loads(get(f"{base}/block/{block_hash}"))
    return {"hash": block_hash, "merkle_root": info["merkle_root"], "time": info["timestamp"]}


out, files = sys.argv[1], sys.argv[2:]
results = []
for name in files:
    data = open(name, "rb").read()
    with open(name + ".ots", "rb") as handle:
        detached = DetachedTimestampFile.deserialize(StreamDeserializationContext(handle))
    file_ok = detached.file_digest == hashlib.sha256(data).digest()
    for msg, attestation in sorted(detached.timestamp.all_attestations(), key=lambda x: str(x[1])):
        if not isinstance(attestation, BitcoinBlockHeaderAttestation):
            continue
        root = msg[::-1].hex()                      # explorers print the merkle root in reversed byte order
        seen = {src: block(src, attestation.height) for src in SOURCES}
        row = {"file": name.rsplit("/", 1)[-1], "file_sha256_matches_proof": file_ok, "height": attestation.height,
               "commitment": root,
               "sources": {src: dict(v, merkle_root_matches=(v["merkle_root"] == root)) for src, v in seen.items()},
               "same_block_hash_both_sources": len({v["hash"] for v in seen.values()}) == 1}
        times = {v["time"] for v in seen.values()}
        row["block_time_utc"] = (dt.datetime.fromtimestamp(times.pop(), dt.timezone.utc).isoformat()
                                 if len(times) == 1 else "sources differ")
        row["ok"] = (file_ok and row["same_block_hash_both_sources"]
                     and all(v["merkle_root_matches"] for v in row["sources"].values()))
        print(json.dumps(row))
        results.append(row)
doc = {"kind": "stage1 OpenTimestamps proof check (no node; two public block explorers)", "version": 1,
       "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
       "method": "commitment from the proof equals the block's merkle root at both sources; both sources agree on "
                 "the block hash; the proof's file digest equals the file's SHA-256",
       "results": results, "all_ok": bool(results) and all(r["ok"] for r in results)}
with open(out, "x") as handle:
    handle.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
print(json.dumps({"all_ok": doc["all_ok"], "attestations": len(results)}))
