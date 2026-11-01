"""Per-arm Gate B judge files from a judge's cache (stdlib only; any Python 3.9+).

    python3 -B write_files.py --judge granite|harmbench --cache C --out DIR (--run-root R)... (--unit U)... \
        [--complete COMPLETE_SHA256]...

One file per (judge, unit), named JUDGE--HOST--UNIT--<first 12 hex of COMPLETE.json SHA-256>.json, in the schema of
BRIEF D9 C-9 / DRAFT §6, as canonical JSON (sorted keys, 2-space indent, ensure_ascii=False, final newline):

    {"kind": "gate-b judge file", "version": 1, "judge": {"name", "revision"}, "arm", "seed", "host",
     "complete_sha256", "job_sha256", "greedy": {"n", "harm", "unparsed"}, "sampled": {"n", "harm", "unparsed"} or null}

Granite writes greedy only (sampled null); HarmBench writes both. n = the unit's harm answers of that mode, harm = the
"yes" labels, unparsed = the "unparsed" labels. complete_sha256 and job_sha256 are those of the unit actually judged
(the cache key carries the COMPLETE.json SHA-256). A file is refused (not written; exit 1) when any answer of the unit
is missing from the cache, a cached record names another answer SHA-256, or the cache holds a record of that unit
and mode that matches no answer: no partial files. An existing file with other bytes is never overwritten (exit 1).

One --out holds at most one file per (judge, arm, seed, target): before anything is written, the given units and the
judge files already in --out are grouped by (judge, arm, seed, target), and a group with two attempts (two
COMPLETE.json SHA-256) refuses (exit 2), unless the repeatable --complete allowlist names exactly one attempt of that
group; then only that attempt gets a file, and a file of another attempt of the group already in --out still refuses
(move it aside). Every --complete value must be a given unit's or an existing file's COMPLETE.json SHA-256.

Then judge-files-index.json (kind "gate-b judge files index", version 2) lists every judge file in DIR with its SHA-256,
judge name, arm, seed, host, unit, target, completed_utc and complete_sha256, and the --complete allowlist. A file whose
unit is not among the given units keeps its entry from the previous index (matched by name and SHA-256), or refuses.
Files in DIR that are not named like judge files (a .DS_Store, for example) are ignored. Prints counts only.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import re
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from cache import Cache  # noqa: E402
from common import HEX64, JUDGES, Refusal, canonical_bytes, sha256_bytes  # noqa: E402
from units import Unit, add_unit_arguments, load_items, units_from_args  # noqa: E402

KIND = "gate-b judge file"
VERSION = 1
INDEX = "judge-files-index.json"
INDEX_KIND = "gate-b judge files index"
INDEX_VERSION = 2
FILE_KEYS = frozenset({"kind", "version", "judge", "arm", "seed", "host", "complete_sha256", "job_sha256", "greedy",
                       "sampled"})
ENTRY_KEYS = frozenset({"file", "sha256", "judge", "arm", "seed", "host", "unit", "target", "completed_utc",
                        "complete_sha256"})
FILE_NAME = re.compile(r"^(granite|harmbench)--.+--[0-9a-f]{12}\.json$")
NOT_NAMED = "not written: --complete names another attempt of this arm, seed and target"


def file_name(judge_key: str, unit: Unit) -> str:
    return f"{judge_key}--{unit.host}--{unit.name}--{unit.complete_sha256[:12]}.json"


def judge_key_of(doc: dict) -> str:
    return next(k for k, v in JUDGES.items() if doc["judge"] == v["identity"])


def _block_ok(b) -> bool:
    return (isinstance(b, dict) and set(b) == {"n", "harm", "unparsed"}
            and all(isinstance(b[k], int) and not isinstance(b[k], bool) and b[k] >= 0 for k in b)
            and b["harm"] + b["unparsed"] <= b["n"])


def check_judge_file(doc) -> None:
    """The exact schema: keys, types, the judge block, and greedy/sampled by judge (Granite: sampled null)."""
    if not isinstance(doc, dict) or set(doc) != FILE_KEYS:
        raise Refusal("judge file keys differ from the schema")
    judge = doc["judge"]
    known = {k: v["identity"] for k, v in JUDGES.items()}
    jkey = next((k for k, ident in known.items() if judge == ident), None)
    ok = (doc["kind"] == KIND and doc["version"] == VERSION and not isinstance(doc["version"], bool)
          and jkey is not None and isinstance(doc["arm"], str) and doc["arm"]
          and isinstance(doc["seed"], int) and not isinstance(doc["seed"], bool)
          and isinstance(doc["host"], str) and doc["host"]
          and isinstance(doc["complete_sha256"], str) and HEX64.match(doc["complete_sha256"])
          and isinstance(doc["job_sha256"], str) and HEX64.match(doc["job_sha256"])
          and _block_ok(doc["greedy"]))
    if ok:
        ok = (doc["sampled"] is None) if JUDGES[jkey]["modes"] == ("greedy",) else _block_ok(doc["sampled"])
    if not ok:
        raise Refusal("judge file does not match the schema")


def build_file(judge_key: str, unit: Unit, cache: Cache):
    """(document or None, per-mode report). None when any answer is missing, stale or extraneous in the cache."""
    modes = JUDGES[judge_key]["modes"]
    doc = {"kind": KIND, "version": VERSION, "judge": dict(JUDGES[judge_key]["identity"]), "arm": unit.arm,
           "seed": unit.seed, "host": unit.host, "complete_sha256": unit.complete_sha256, "job_sha256": unit.job_sha256,
           "greedy": None, "sampled": None}
    report, complete = {}, True
    for mode in modes:
        items = load_items(unit, mode)
        keys = set()
        n = harm = unparsed = missing = stale = 0
        for it in items:
            k = (unit.complete_sha256, mode, it.prompt_id, it.sample_index)
            keys.add(k)
            n += 1
            rec = cache.get(k)
            if rec is None:
                missing += 1
            elif rec["answer_sha256"] != it.answer_sha256:
                stale += 1
            else:
                harm += rec["label"] == "yes"
                unparsed += rec["label"] == "unparsed"
        extra = sum(1 for k in cache.entries if k[0] == unit.complete_sha256 and k[1] == mode and k not in keys)
        report[mode] = {"n": n, "harm": harm, "unparsed": unparsed, "missing": missing, "stale": stale, "extra": extra}
        if missing or stale or extra or n == 0:
            complete = False
        else:
            doc[mode] = {"n": n, "harm": harm, "unparsed": unparsed}
    if not complete:
        return None, report
    check_judge_file(doc)
    return doc, report


def _previous_index(out: pathlib.Path) -> dict:
    """{file name: entry} of the index already in out (version 2 entries only; none when there is no index)."""
    path = out / INDEX
    if not path.exists():
        return {}
    try:
        index = json.loads(path.read_bytes())
    except json.JSONDecodeError:
        raise Refusal(f"{INDEX}: not JSON") from None
    if not isinstance(index, dict) or index.get("kind") != INDEX_KIND or not isinstance(index.get("files"), list):
        raise Refusal(f"{INDEX}: not a judge files index")
    return {e["file"]: e for e in index["files"] if isinstance(e, dict) and set(e) == ENTRY_KEYS}


def index_entries(out: pathlib.Path, units: list[Unit]) -> list[dict]:
    """The index entries of every judge file in out. unit, target and completed_utc come from the given unit with the
    file's COMPLETE.json SHA-256 (whose host, arm, seed, job_sha256 and file name must agree), else from the previous
    index's entry of that file name and SHA-256, else the file refuses."""
    by_complete = {u.complete_sha256: u for u in units}
    previous = _previous_index(out)
    entries = []
    for p in sorted(out.iterdir()):
        if not FILE_NAME.match(p.name):
            continue
        data = p.read_bytes()
        try:
            doc = json.loads(data)
        except json.JSONDecodeError:
            raise Refusal(f"{p.name}: not JSON") from None
        check_judge_file(doc)
        if data != canonical_bytes(doc):
            raise Refusal(f"{p.name}: not canonical JSON")
        digest = sha256_bytes(data)
        unit = by_complete.get(doc["complete_sha256"])
        if unit is not None:
            if ((doc["host"], doc["arm"], doc["seed"], doc["job_sha256"]) != (unit.host, unit.arm, unit.seed, unit.job_sha256)
                    or p.name != file_name(judge_key_of(doc), unit)):
                raise Refusal(f"{p.name}: its name, host, arm, seed or job_sha256 differ from unit {unit.label}")
            info = {"unit": unit.unit, "target": unit.target, "completed_utc": unit.completed_utc}
        else:
            old = previous.get(p.name)
            if old is None or old["sha256"] != digest or old["complete_sha256"] != doc["complete_sha256"]:
                raise Refusal(f"{p.name}: its unit (COMPLETE.json {doc['complete_sha256'][:16]}) is not among the given "
                              f"units and the previous index has no entry of this file; give its unit or move it aside")
            info = {k: old[k] for k in ("unit", "target", "completed_utc")}
        entries.append({"file": p.name, "sha256": digest, "judge": doc["judge"]["name"], "arm": doc["arm"],
                        "seed": doc["seed"], "host": doc["host"], "complete_sha256": doc["complete_sha256"], **info})
    return entries


def select_units(judge_key: str, units: list[Unit], entries: list[dict], allow) -> tuple[list[Unit], list[Unit]]:
    """(units that get a file, units left out). Groups the given units and this judge's files in out by (arm, seed,
    target); a group with two attempts refuses unless allow names exactly one of them."""
    allow = set(allow)
    known = {u.complete_sha256 for u in units} | {e["complete_sha256"] for e in entries}
    unknown = sorted(allow - known)
    if unknown:
        raise Refusal(f"--complete {unknown[0][:16]}: no given unit and no file in --out has this COMPLETE.json SHA-256")
    name = JUDGES[judge_key]["identity"]["name"]
    groups = collections.defaultdict(dict)                  # (arm, seed, target) -> {complete_sha256: "file"|"unit"}
    for e in entries:
        if e["judge"] == name:
            groups[(e["arm"], e["seed"], e["target"])][e["complete_sha256"]] = "file"
    for u in units:
        groups[(u.arm, u.seed, u.target)].setdefault(u.complete_sha256, "unit")
    chosen = {}
    for (arm, seed, target), members in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], str(kv[0][2]))):
        if len(members) == 1:
            continue
        named = sorted(c for c in members if c in allow)
        where = f"{judge_key}: arm {arm} seed {seed} target {target}"
        if len(named) != 1:
            raise Refusal(f"{where} has {len(members)} attempts (COMPLETE.json "
                          f"{', '.join(sorted(c[:12] for c in members))}) for one --out; name exactly one accepted "
                          f"attempt with --complete (named now: {len(named)})")
        stray = sorted(c[:12] for c, source in members.items() if c != named[0] and source == "file")
        if stray:
            raise Refusal(f"{where}: --out already holds a file of another attempt ({stray[0]}); move it aside")
        chosen[(arm, seed, target)] = named[0]
    selected = [u for u in units if chosen.get((u.arm, u.seed, u.target), u.complete_sha256) == u.complete_sha256]
    left = [u for u in units if u not in selected]
    return selected, left


def write_index(out: pathlib.Path, units: list[Unit], allow=()) -> tuple[pathlib.Path, list]:
    entries = index_entries(out, units)
    keys = collections.Counter((e["judge"], e["arm"], e["seed"], e["target"]) for e in entries)
    dup = sorted(k for k, n in keys.items() if n > 1)
    if dup:
        raise Refusal(f"--out holds {keys[dup[0]]} files of judge {dup[0][0]} arm {dup[0][1]} seed {dup[0][2]} "
                      f"target {dup[0][3]}")
    index = {"kind": INDEX_KIND, "version": INDEX_VERSION, "complete_allowlist": sorted(set(allow)), "files": entries}
    path = out / INDEX
    _atomic_write(path, canonical_bytes(index))
    return path, entries


def _atomic_write(path: pathlib.Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def write_all(judge_key: str, units: list[Unit], cache: Cache, out: pathlib.Path, emit=print, allow=()) -> int:
    """Writes every selected unit's complete file and the index; returns 0 when every selected unit's file is written
    or unchanged, 1 when one is refused. A Refusal (two attempts of one group, a bad --complete, a foreign file in
    out) is raised before anything is written."""
    out.mkdir(parents=True, exist_ok=True)
    selected, left = select_units(judge_key, units, index_entries(out, units), allow)
    rc = 0
    for unit in left:
        emit(json.dumps({"file": file_name(judge_key, unit), "unit": unit.label, "arm": unit.arm, "seed": unit.seed,
                         "target": unit.target, "status": NOT_NAMED}, sort_keys=True))
    for unit in selected:
        name = file_name(judge_key, unit)
        doc, report = build_file(judge_key, unit, cache)
        status = "refused: answers missing, stale or extra in the cache"
        if doc is not None:
            data = canonical_bytes(doc)
            path = out / name
            if path.exists() and path.read_bytes() != data:
                status = "refused: a different file of this name exists (move it aside)"
                doc = None
            elif path.exists():
                status = "unchanged"
            else:
                _atomic_write(path, data)
                status = "written"
        if doc is None:
            rc = 1
        emit(json.dumps({"file": name, "unit": unit.label, "arm": unit.arm, "seed": unit.seed, "target": unit.target,
                         "status": status, **report}, sort_keys=True))
    index, files = write_index(out, units, allow)
    emit(json.dumps({"index": str(index), "files": len(files), "index_sha256": sha256_bytes(index.read_bytes())}))
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Per-arm Gate B judge files from a judge cache.")
    ap.add_argument("--judge", choices=sorted(JUDGES), required=True)
    ap.add_argument("--cache", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--complete", action="append", default=[], metavar="COMPLETE_SHA256",
                    help="the accepted attempt of an (arm, seed, target) with two attempts (repeatable)")
    add_unit_arguments(ap)
    a = ap.parse_args(argv)
    try:
        bad = [c for c in a.complete if not HEX64.match(c)]
        if bad:
            raise Refusal(f"--complete {bad[0][:16]!r}: expected 64 lowercase hex characters")
        if not a.cache.is_file():
            raise Refusal(f"no cache file {a.cache}")
        units, _ = units_from_args(a)
        cache = Cache(a.cache, JUDGES[a.judge]["identity"])
        if cache.undecodable:
            print(json.dumps({"undecodable_cache_lines": cache.undecodable}))
        return write_all(a.judge, units, cache, a.out, allow=a.complete)
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
