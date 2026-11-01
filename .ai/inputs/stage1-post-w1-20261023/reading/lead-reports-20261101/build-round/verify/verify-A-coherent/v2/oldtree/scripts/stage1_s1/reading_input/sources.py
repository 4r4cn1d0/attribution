"""The kit, its block seals and every verified folder the builder reads (addendum 33 point 5).

A kit folder (an engine unit, a B10 evaluation unit, an O-ext folder) is opened only after its COMPLETE.json bytes
hash to the SHA-256 that plan.json records for it AND to the block seal's entry for that file; only then is
COMPLETE.json parsed. Every later file is read through ``Folder.file``: it must be listed by COMPLETE.json, listed by
the seal at the same SHA-256 (kit folders), and hash to it on disk. A pinned folder outside the kit (block A's re-judged
Gate A and wave-0a units, stage1_rules.REJUDGED_PINS) is opened only when its COMPLETE.json and job.json hash to the
pins. Messages hold names, paths, counts and hashes only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from scripts.stage1_s1.reading.settings import Refusal, strict_json

HEX64 = re.compile(r"[0-9a-f]{64}")
SEAL_KIND = "stage1 block seal"
COMPLETE = "COMPLETE.json"
JOB = "job.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_hex64(value) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def plain(rel, what: str) -> str:
    """A plain relative POSIX path: no absolute path, no empty, '.' or '..' part, no backslash."""
    if not isinstance(rel, str) or not rel or "\\" in rel or rel.startswith("/"):
        raise Refusal(f"{what}: {str(rel)[:80]!r} is not a plain relative path")
    if any(part in ("", ".", "..") for part in rel.split("/")):
        raise Refusal(f"{what}: {rel[:80]!r} is not a plain relative path")
    return rel


def read_bytes(path: Path, what: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise Refusal(f"{what}: missing or not a regular file")
    return path.read_bytes()


def load_rules(path: Path):
    """The kit's rules module (stdlib only) by path, and its SHA-256. It is executed, never edited."""
    data = read_bytes(path, f"the rules module {path.name}")
    spec = importlib.util.spec_from_file_location("stage1_rules_for_reading_input", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("REJUDGED_PINS", "JUDGES", "JUDGE_INDEX", "JUDGE_INDEX_KIND", "JUDGE_INDEX_VERSION",
                 "JUDGE_INDEX_ENTRY_KEYS", "JUDGE_FILE_PATTERN", "JUDGE_NAMES", "REUSED_SEEDS", "block_runs"):
        if not hasattr(module, name):
            raise Refusal(f"the rules module {path.name} has no {name}")
    return module, sha256_bytes(data)


@dataclass
class Seal:
    block: str
    sha256: str
    doc: dict
    files: dict                                   # (host, path) -> SHA-256

    def under(self, host: str, prefix: str) -> dict:
        """rel -> SHA-256 of the sealed files of ``host`` under the folder ``prefix``."""
        cut = len(prefix) + 1
        return {p[cut:]: s for (h, p), s in self.files.items() if h == host and p.startswith(prefix + "/")}


@dataclass
class Folder:
    """One verified folder. ``file`` reads a listed file after its three checks; ``read`` keeps rel -> SHA-256."""
    label: str
    root: Path
    complete_sha256: str
    complete: dict
    sealed: dict | None                           # rel -> SHA-256 from the block seal (None: a pinned folder)
    read: dict = field(default_factory=dict)

    def file(self, rel: str) -> bytes:
        listed = (self.complete.get("files") or {}).get(rel)
        if not is_hex64(listed):
            raise Refusal(f"{self.label}: COMPLETE.json does not list {rel}")
        if self.sealed is not None and self.sealed.get(rel) != listed:
            raise Refusal(f"{self.label}: {rel} is not in the block seal at the SHA-256 COMPLETE.json lists")
        data = read_bytes(self.root / rel, f"{self.label}: {rel}")
        digest = sha256_bytes(data)
        if digest != listed:
            raise Refusal(f"{self.label}: {rel} hashes to {digest[:16]}, COMPLETE.json lists {listed[:16]}")
        self.read[rel] = digest
        return data

    def json(self, rel: str):
        return strict_json(self.file(rel))

    def job(self, marker: bool = True) -> dict:
        """job.json; with ``marker``, COMPLETE.json must name it by its SHA-256 (job_sha256)."""
        data = self.file(JOB)
        if marker and self.complete.get("job_sha256") != sha256_bytes(data):
            raise Refusal(f"{self.label}: COMPLETE.json's job_sha256 is not job.json's")
        doc = strict_json(data)
        if not isinstance(doc, dict):
            raise Refusal(f"{self.label}: job.json is not an object")
        return doc

    def record(self) -> dict:
        return {"folder": self.label, "complete_sha256": self.complete_sha256, "files": dict(sorted(self.read.items()))}


def _complete(data: bytes, label: str) -> dict:
    doc = strict_json(data)
    if not isinstance(doc, dict) or doc.get("complete") is not True or not isinstance(doc.get("files"), dict):
        raise Refusal(f"{label}: COMPLETE.json is not a complete marker with a file list")
    for rel, digest in doc["files"].items():
        plain(rel, f"{label}: a COMPLETE.json entry")
        if not is_hex64(digest):
            raise Refusal(f"{label}: COMPLETE.json lists {rel} without a SHA-256")
    return doc


class Kit:
    """plan.json, the block seals and the pulled trees of one kit folder (tmp/stage1-olmo)."""

    def __init__(self, root: Path):
        self.root = Path(root)
        data = read_bytes(self.root / "plan.json", "the kit's plan.json")
        self.plan_sha256 = sha256_bytes(data)
        self.plan = strict_json(data)
        if not isinstance(self.plan, dict) or not isinstance(self.plan.get("hosts"), dict) \
                or not isinstance(self.plan.get("records"), dict):
            raise Refusal("the kit's plan.json is not a stage-1 plan (hosts, records)")
        self._seals: dict = {}

    def plan_code(self) -> str:
        ab = self.plan["records"].get("plan_ab")
        code = ab.get("code") if isinstance(ab, dict) else None
        if code not in ("A", "B"):
            raise Refusal("plan.json records no plan-A/B code (A or B)")
        return code

    def seal(self, block: str) -> Seal:
        """Block BLOCK's seal (seal.py block): plan.json's seals entry, the file at its SHA-256, the record's kind,
        version and block, and every listed file once."""
        if block in self._seals:
            return self._seals[block]
        entry = (self.plan.get("seals") or {}).get(block)
        if not isinstance(entry, dict) or not is_hex64(entry.get("sha256")):
            raise Refusal(f"block {block} is not sealed in plan.json (seal.py block {block})")
        rel = plain(entry.get("path"), f"block {block}'s seal path")
        data = read_bytes(self.root / rel, f"block {block}'s seal {rel}")
        digest = sha256_bytes(data)
        if digest != entry["sha256"]:
            raise Refusal(f"block {block}'s seal hashes to {digest[:16]}, plan.json records {entry['sha256'][:16]}")
        doc = strict_json(data)
        if not isinstance(doc, dict) or doc.get("kind") != SEAL_KIND or doc.get("version") != 1 \
                or doc.get("block") != block or not isinstance(doc.get("files"), list):
            raise Refusal(f"block {block}'s seal is not a version-1 {SEAL_KIND!r} of block {block}")
        files = {}
        for f in doc["files"]:
            if not isinstance(f, dict) or not isinstance(f.get("host"), str) or not is_hex64(f.get("sha256")):
                raise Refusal(f"block {block}'s seal holds a file entry without a host and a SHA-256")
            key = (f["host"], plain(f.get("path"), f"block {block}'s seal entry"))
            if key in files:
                raise Refusal(f"block {block}'s seal lists {key[0]}/{key[1][:60]} twice")
            files[key] = f["sha256"]
        seal = Seal(block, digest, doc, files)
        self._seals[block] = seal
        return seal

    def hosts(self, block: str):
        """(host name, host record) of the block's hosts that are done. A host that is not done must be listed by
        the seal as moved (a deferral or requeue moved its jobs; seal.py, round 30 R6): its jobs are not inputs."""
        seal = self.seal(block)
        moved = {m.get("host") for m in seal.doc.get("moved") or [] if isinstance(m, dict)}
        for name, h in sorted(self.plan["hosts"].items()):
            if not isinstance(h, dict) or h.get("block") != block:
                continue
            if h.get("done") is not True:
                if name not in moved:
                    raise Refusal(f"{name} (block {block}) is not done and not listed as moved in the seal")
                continue
            if not isinstance(h.get("jobs"), list):
                raise Refusal(f"{name}: plan.json holds no job list")
            yield name, h

    def folder(self, block: str, host: str, rel: str, complete_sha256, label: str) -> Folder:
        """A kit folder of a done host: COMPLETE.json at plan.json's SHA-256 and at the seal's, then parsed."""
        rel = plain(rel, f"{label}: the folder")
        if not is_hex64(complete_sha256):
            raise Refusal(f"{label}: plan.json records no COMPLETE.json SHA-256")
        seal = self.seal(block)
        sealed = seal.files.get((host, f"{rel}/{COMPLETE}"))
        if sealed is None:
            raise Refusal(f"{label}: its COMPLETE.json is not in block {block}'s seal")
        if sealed != complete_sha256:
            raise Refusal(f"{label}: block {block}'s seal lists its COMPLETE.json at {sealed[:16]}, plan.json "
                          f"records {complete_sha256[:16]}")
        root = self.root / "retrieved" / host / "tree" / rel
        data = read_bytes(root / COMPLETE, f"{label}: COMPLETE.json")
        digest = sha256_bytes(data)
        if digest != complete_sha256:
            raise Refusal(f"{label}: COMPLETE.json hashes to {digest[:16]}, plan.json records {complete_sha256[:16]}")
        return Folder(label, root, digest, _complete(data, label), seal.under(host, rel))


def pinned_folder(repo: Path, pin: dict) -> Folder:
    """A pinned unit outside the kit (stage1_rules.REJUDGED_PINS): COMPLETE.json and job.json at their pins."""
    name = str(pin.get("name"))[:40]
    rel = plain(pin.get("path"), f"pinned unit {name}")
    if not is_hex64(pin.get("complete_sha256")) or not is_hex64(pin.get("job_sha256")):
        raise Refusal(f"pinned unit {name}: the pin has no COMPLETE.json or job.json SHA-256")
    root = Path(repo) / rel
    label = f"repo:{rel}"
    data = read_bytes(root / COMPLETE, f"{label}: COMPLETE.json")
    digest = sha256_bytes(data)
    if digest != pin["complete_sha256"]:
        raise Refusal(f"{label}: COMPLETE.json hashes to {digest[:16]}, the pin is {pin['complete_sha256'][:16]}")
    folder = Folder(label, root, digest, _complete(data, label), None)
    job = read_bytes(root / JOB, f"{label}: job.json")
    if sha256_bytes(job) != pin["job_sha256"]:
        raise Refusal(f"{label}: job.json differs from its pin")
    return folder
