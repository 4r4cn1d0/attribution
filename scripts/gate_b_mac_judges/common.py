"""Shared pins and helpers of the Gate B Mac judges (stdlib only; no package, no __init__).

The judge identities written into every judge file, canonical JSON, SHA-256 helpers and the dev-bank reader. Nothing
in this folder prints, logs or stores prompt or answer text: outputs hold ids, counts, labels and SHA-256 hashes only.
Every refusal is a `Refusal` whose message names ids, counts, paths and hashes, never text.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# The `judge` block of the judge files (BRIEF D9 C-9). The names are the frozen Gate B reading's constants exactly
# (gate_b_reading.py JUDGE_GRANITE, JUDGE_HARMBENCH); the reading selects a file's judge by name only, requires every
# file of one judge to carry one revision, and requires HarmBench's revision to start with HARMBENCH_REVISION_PREFIX
# ("51182c7c"). Granite: the judge is the official Q4_K_M GGUF of IBM Granite Guardian 3.3 8B (repository
# ibm-granite/granite-guardian-3.3-8b-GGUF at commit 8c87479a2dc329e4e362a6e5dda7e7de3e0372b2); since the reading
# compares the name only, `revision` carries the pinned GGUF FILE's SHA-256 (granite_files.check_pins verifies it before
# each load). HarmBench: the classifier at the revision pinned in tmp/family-probe-olmo2-1b/harmbench_judge.py.
GRANITE_GGUF_SHA256 = "b4fa861b5163373413d9659c22e344e6206baad824ead17226b2058e54d14587"     # = the Hub's LFS etag
GRANITE = {"name": "granite-guardian-3.3-8b", "revision": GRANITE_GGUF_SHA256}
HARMBENCH = {"name": "cais/HarmBench-Mistral-7b-val-cls", "revision": "51182c7cdaf9b2e5f05b745b81b047b67e7384a1"}
JUDGES = {"granite": {"identity": GRANITE, "modes": ("greedy",)},
          "harmbench": {"identity": HARMBENCH, "modes": ("greedy", "sampled")}}

# The prepared set whose dev bank holds the harm prompts (probe_constants / gateb_rules: prepared-kt-dolly-olmo2).
PREPARED_DIR = ROOT / "tmp/kt-prepared/prepared-kt-dolly-olmo2"
PREPARED_MANIFEST = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
BANK_KIND = "harm"

# One Metal/MPS judge at a time (judging.take_gpu_lock): an exclusive, non-blocking flock held for the judge's lifetime.
GPU_LOCK = ROOT / "tmp" / "mac-gpu.lock"


class Refusal(Exception):
    """A refused input or state. The message names ids, counts, paths and hashes only."""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    return sha256_bytes(s.encode("utf-8"))


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_bytes(obj) -> bytes:
    """Canonical JSON: sorted keys, 2-space indent, ensure_ascii=False, one final newline, UTF-8."""
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def jsonl_records(data: bytes, what: str):
    """Records of a JSONL byte string, split on b"\\n" only (str.splitlines would also split on U+2028 inside a
    string). Yields (line number, record). A line that is not JSON refuses, naming the line number only."""
    for lineno, line in enumerate(data.split(b"\n"), 1):
        if not line.strip():
            continue
        try:
            yield lineno, json.loads(line)
        except json.JSONDecodeError:
            raise Refusal(f"{what}: line {lineno} is not JSON") from None


def bank_prompts(prepared_dir: pathlib.Path = PREPARED_DIR, manifest_sha256: str = PREPARED_MANIFEST) -> dict[str, str]:
    """The harm prompts of the prepared dev bank, after its manifest hash is checked: the logic of
    second_judge_probe.bank_prompts (and harmbench_judge.bank_prompts), unchanged. Nothing prints what it reads."""
    prepared_dir = pathlib.Path(prepared_dir)
    if (prepared_dir / "manifest.sha256").read_text(encoding="utf-8").strip() != manifest_sha256:
        raise Refusal("the prepared set's manifest differs from the pinned manifest")
    prompts = {}
    with open(prepared_dir / "banks" / "dev.jsonl", encoding="utf-8") as fh:
        for line in fh:
            record = json.loads(line)
            if record.get("kind") == BANK_KIND:
                prompts[record["prompt_id"]] = record["prompt"]
    return prompts
