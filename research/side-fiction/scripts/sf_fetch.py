"""Polite downloader for the side fiction study (rules-v1 source section).

Usage: python3 -I sf_fetch.py LOG_JSONL PAUSE_SECONDS URL OUTFILE [URL OUTFILE ...]

Downloads one file at a time with curl, pauses between requests, refuses to overwrite an
existing file, and appends one JSON record per file to LOG_JSONL: url, file, UTC start and
end, byte size, SHA-256 and curl's exit status. It prints ids, sizes and hashes only.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) < 5 or (len(argv) - 3) % 2:
        print(__doc__)
        return 2
    log, pause, pairs = argv[1], float(argv[2]), argv[3:]
    jobs = list(zip(pairs[0::2], pairs[1::2]))
    failures = 0
    for i, (url, out) in enumerate(jobs):
        if os.path.exists(out):
            print(f"refuse: {out} exists")
            failures += 1
            continue
        if i:
            time.sleep(pause)
        start = utc()
        proc = subprocess.run(["curl", "-fsSL", "--proto", "=https", "--max-time", "300",
                               "-o", out, url], capture_output=True)
        end = utc()
        rec = {"url": url, "file": out, "utc_start": start, "utc_end": end, "curl_exit": proc.returncode}
        if proc.returncode == 0 and os.path.exists(out):
            rec["bytes"] = os.path.getsize(out)
            rec["sha256"] = sha256_file(out)
        else:
            failures += 1
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        print(json.dumps({k: rec.get(k) for k in ("url", "curl_exit", "bytes", "sha256", "utc_end")}))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
