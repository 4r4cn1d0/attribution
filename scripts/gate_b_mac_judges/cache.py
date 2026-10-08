"""Judge-agnostic item cache: JSONL, append-only, resumable (stdlib only).

One cache file per judge. Key: (complete_sha256, mode, prompt_id, sample_index or null), so two units with the same
folder name on two hosts (two attempts, two COMPLETE.json) never share an entry. A record holds the key, the judge
identity, the label ("yes", "no" or "unparsed"), token counts, a truncation flag, the answer's SHA-256 and its
source ("judged", or "import:<SHA-256 of the old cache file>"); never text:

    {"answer_sha256", "answer_tokens", "complete_sha256", "input_tokens", "judge": {"name", "revision"}, "label",
     "mode", "prompt_id", "sample_index", "source", "truncated"}

Reading: a line that is not JSON (one cut by a hard stop) is skipped and counted, so that item is judged again; a
record of another judge, a malformed record, or two records of one key with different labels or answer hashes refuse
(an identical repeat is ignored). Writing: one writer at a time (an exclusive lock on <cache>.lock), each record
flushed and fsynced; a cut last line gets a newline before the next record.
"""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
import pathlib
import re
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from common import HEX64, Refusal  # noqa: E402

MODES = ("greedy", "sampled")
LABELS = ("yes", "no", "unparsed")
RECORD_KEYS = frozenset({"answer_sha256", "answer_tokens", "complete_sha256", "input_tokens", "judge", "label", "mode",
                         "prompt_id", "sample_index", "source", "truncated"})
SOURCE = re.compile(r"^(judged|import:[0-9a-f]{64})$")


def key_of(rec: dict) -> tuple:
    return (rec["complete_sha256"], rec["mode"], rec["prompt_id"], rec["sample_index"])


def _count(v) -> bool:
    return v is None or (isinstance(v, int) and not isinstance(v, bool) and v >= 0)


def check_record(rec, where: str) -> None:
    if not isinstance(rec, dict) or set(rec) != RECORD_KEYS:
        raise Refusal(f"{where}: not a cache record (keys differ)")
    judge = rec["judge"]
    ok = (isinstance(judge, dict) and set(judge) == {"name", "revision"}
          and all(isinstance(judge[k], str) and judge[k] for k in judge)
          and isinstance(rec["complete_sha256"], str) and HEX64.match(rec["complete_sha256"])
          and isinstance(rec["answer_sha256"], str) and HEX64.match(rec["answer_sha256"])
          and rec["mode"] in MODES and rec["label"] in LABELS
          and isinstance(rec["prompt_id"], str) and rec["prompt_id"]
          and _count(rec["input_tokens"]) and _count(rec["answer_tokens"])
          and (rec["truncated"] is None or isinstance(rec["truncated"], bool))
          and isinstance(rec["source"], str) and SOURCE.match(rec["source"]))
    if ok:
        sidx = rec["sample_index"]
        ok = (sidx is None) if rec["mode"] == "greedy" else (isinstance(sidx, int) and not isinstance(sidx, bool) and sidx >= 0)
    if not ok:
        raise Refusal(f"{where}: malformed cache record")


def make_record(judge: dict, complete_sha256: str, mode: str, prompt_id: str, sample_index, answer_sha256: str,
                label: str, input_tokens=None, answer_tokens=None, truncated=None, source: str = "judged") -> dict:
    rec = {"answer_sha256": answer_sha256, "answer_tokens": answer_tokens, "complete_sha256": complete_sha256,
           "input_tokens": input_tokens, "judge": {"name": judge["name"], "revision": judge["revision"]}, "label": label,
           "mode": mode, "prompt_id": prompt_id, "sample_index": sample_index, "source": source, "truncated": truncated}
    check_record(rec, f"new record for prompt {prompt_id} sample {sample_index}")
    return rec


class Cache:
    def __init__(self, path: pathlib.Path, judge: dict):
        self.path = pathlib.Path(path)
        self.judge = {"name": judge["name"], "revision": judge["revision"]}
        self.entries: dict[tuple, dict] = {}
        self.undecodable = 0
        self._fh = None
        self._load()

    def _load(self) -> None:
        self.entries, self.undecodable = {}, 0
        if not self.path.exists():
            return
        for lineno, line in enumerate(self.path.read_bytes().split(b"\n"), 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:              # a line cut by a hard stop: that item is judged again
                self.undecodable += 1
                continue
            where = f"{self.path.name} line {lineno}"
            check_record(rec, where)
            if rec["judge"] != self.judge:
                raise Refusal(f"{where}: written by judge {rec['judge']['name']}@{rec['judge']['revision'][:12]}, "
                              f"not {self.judge['name']}@{self.judge['revision'][:12]}")
            self._put(rec, where)

    def _put(self, rec: dict, where: str) -> bool:
        k = key_of(rec)
        old = self.entries.get(k)
        if old is not None:
            if (old["label"], old["answer_sha256"]) != (rec["label"], rec["answer_sha256"]):
                raise Refusal(f"{where}: unit {k[0][:16]} {k[1]} prompt {k[2]} sample {k[3]} has two different records")
            return False
        self.entries[k] = rec
        return True

    def __contains__(self, k: tuple) -> bool:
        return k in self.entries

    def get(self, k: tuple):
        return self.entries.get(k)

    def __len__(self) -> int:
        return len(self.entries)

    @contextlib.contextmanager
    def writing(self):
        """Exclusive writer: takes <cache>.lock, re-reads the cache under the lock, and keeps the file open for append."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path.with_name(self.path.name + ".lock"), "a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refusal(f"another process is writing {self.path.name}") from None
            self._load()
            with open(self.path, "ab") as fh:
                if fh.tell() > 0:
                    with open(self.path, "rb") as rd:
                        rd.seek(-1, os.SEEK_END)
                        if rd.read(1) != b"\n":
                            fh.write(b"\n")
                self._fh = fh
                try:
                    yield self
                finally:
                    self._fh = None

    def append(self, rec: dict) -> bool:
        """Append one record (inside writing()); False when an identical record is already cached."""
        if self._fh is None:
            raise Refusal("Cache.append outside Cache.writing()")
        check_record(rec, "record to append")
        if rec["judge"] != self.judge:
            raise Refusal("record to append names another judge")
        k = key_of(rec)
        if k in self.entries:
            return self._put(rec, "record to append")
        line = json.dumps({f: rec[f] for f in RECORD_KEYS}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        self._fh.write((line + "\n").encode("utf-8"))      # the schema's fields only (check_record: exactly these)
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self.entries[k] = rec
        return True
