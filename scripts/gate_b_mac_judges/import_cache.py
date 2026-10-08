"""Import an old probe-kit judge cache into the new cache, mapping its records by hash (stdlib only; no model).

    python3 -B import_cache.py --judge harmbench|granite --old-cache OLD.jsonl --old-summary OLD-SUMMARY.json \
        --cache NEW.jsonl (--run-root R)... (--unit U)... [--map OLD_LABEL=COMPLETE_SHA256]...

Old formats: tmp/family-probe-olmo2-1b/harmbench_judge.py writes {unit (a label such as "untuned" or "e1-1101"),
kind ("sampled"/"greedy"), prompt_id, sample_index, label, generation_sha256, input_tokens, generation_tokens,
clipped, ...}; second_judge_probe.py writes {unit (a unit folder name), target, prompt_id, granite, trimmed, ...}. Each
old summary carries every old label's job_sha256 (the SHA-256 of the judged unit's job.json).

Mapping: an old label goes to the one unit (among the given units) whose COMPLETE.json SHA-256 is the --map pin and
whose job.json SHA-256 is the old summary's job_sha256; without a pin, to the one unit with that job_sha256. Then
each record goes to its unit's item by (mode, prompt id, sample index); a HarmBench record must also carry that
answer's SHA-256 (generation_sha256). The old Granite cache holds no answer hash, so a Granite record is bound to its
attempt in three other ways: (1) the unit must lie under the old cache's own kit (OLD_CACHE's folder/retrieved/, where
second_judge_probe.py found the units it judged); (2) the old probe's own rule: exactly one folder named <label> (the
old cache's unit folder name) exists under <kit>/retrieved/*/tree/round1/, and it is the mapped unit's folder
(second_judge_probe.discover_units refused a unit name found on more than one host, so two copies in the kit refuse
here too, whatever their guard rows); (3) the record's (qwen3guard, qwen_refusal), which second_judge_probe.py copied
from the judged unit's guard.jsonl, must equal the unit's sealed guard.jsonl harm row for that prompt id (safety,
refusal); its target must also be the unit's. Refused, with nothing written: a label with no job_sha256 in the summary
or no matching unit (unmatched), more than one matching unit or two labels on one unit (ambiguous), a Granite unit
outside the old cache's kit, a kit with no folder of that name or a unit that is not it (unmatched), a kit with
several folders of that name (ambiguous), a record matching no answer of its unit, with another answer hash or
(Granite) other guard labels (unmatched), two old records of one item with different labels (ambiguous), or a
new-cache record of the item with another label. Residual limit: a kit whose one folder of that name was replaced,
after the old probe ran, by another attempt with identical guard.jsonl harm labels cannot be told apart by a Granite
record. Old lines that are not JSON are skipped and counted, as the old readers did. Labels: HarmBench's as
recorded; Granite's "yes"/"no" as recorded and anything else (None) "unparsed". The old Granite output tail ("raw") is
not imported. Each new record's source is "import:<SHA-256 of the old cache file>"; token counts are kept where the
old cache has them (HarmBench).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from cache import LABELS, Cache, make_record  # noqa: E402
from common import HEX64, JUDGES, Refusal, sha256_bytes  # noqa: E402
from units import Unit, add_unit_arguments, load_guard, load_items, units_from_args  # noqa: E402


def map_labels(labels, summary: dict, units: list[Unit], pins: dict) -> dict:
    """old label -> Unit, by job_sha256 (old summary) and complete_sha256 (pin)."""
    s_units = summary.get("units") if isinstance(summary, dict) else None
    if not isinstance(s_units, dict):
        raise Refusal("the old summary has no units block")
    for label in pins:
        if label not in labels:
            raise Refusal(f"pinned label {label!r} has no record in the old cache")
    mapping = {}
    for label in sorted(labels):
        job = (s_units.get(label) or {}).get("job_sha256")
        if not isinstance(job, str) or not HEX64.match(job):
            raise Refusal(f"unmatched: old label {label!r} has no job_sha256 in the old summary")
        pin = pins.get(label)
        cands = [u for u in units if u.job_sha256 == job and (pin is None or u.complete_sha256 == pin)]
        if not cands:
            raise Refusal(f"unmatched: no given unit has job.json {job[:16]}"
                          + (f" and COMPLETE.json {pin[:16]}" if pin else "") + f" (old label {label!r})")
        if len(cands) > 1:
            raise Refusal(f"ambiguous: {len(cands)} units have job.json {job[:16]} (old label {label!r}); "
                          f"pin one with --map {label}=COMPLETE_SHA256")
        mapping[label] = cands[0]
    seen = {}
    for label, unit in mapping.items():
        if unit.complete_sha256 in seen:
            raise Refusal(f"ambiguous: old labels {seen[unit.complete_sha256]!r} and {label!r} map to one unit {unit.label}")
        seen[unit.complete_sha256] = label
    return mapping


def _old_records(path: pathlib.Path):
    data = path.read_bytes()
    recs, undecodable = [], 0
    for lineno, line in enumerate(data.split(b"\n"), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            undecodable += 1
            continue
        if not isinstance(r, dict) or not isinstance(r.get("unit"), str):
            raise Refusal(f"{path.name} line {lineno}: not an old cache record")
        recs.append((lineno, r))
    return data, recs, undecodable


def check_kit(old_cache: pathlib.Path, mapping: dict) -> None:
    """Granite: every mapped unit lies under the old cache's own kit's retrieved/ tree, and it is the one folder named
    by its old label under <kit>/retrieved/*/tree/round1/ (second_judge_probe.discover_units refused a unit folder name
    found on more than one host; a kit with two folders of that name refuses here too)."""
    kit = pathlib.Path(old_cache).resolve().parent / "retrieved"
    for label, unit in sorted(mapping.items()):
        unit_dir = pathlib.Path(unit.path).resolve()
        if kit not in unit_dir.parents:
            raise Refusal(f"unmatched: old label {label!r} maps to {unit.label} at {unit.path}, which is not under the "
                          f"old cache's kit {kit}")
        if not label or label in (".", "..") or pathlib.PurePath(label).name != label:
            raise Refusal(f"unmatched: old label {label!r} is not a unit folder name")
        named = sorted(h / "tree" / "round1" / label for h in kit.iterdir()
                       if (h / "tree" / "round1" / label).is_dir()) if kit.is_dir() else []
        if not named:
            raise Refusal(f"unmatched: no folder named {label!r} under {kit}/*/tree/round1/ (old label {label!r} maps "
                          f"to {unit.label})")
        if len(named) > 1:
            raise Refusal(f"ambiguous: {len(named)} folders named {label!r} under {kit}/*/tree/round1/ (the old probe "
                          f"refused a unit name found on more than one host); exactly one may exist")
        if named[0].resolve() != unit_dir:
            raise Refusal(f"unmatched: old label {label!r} maps to {unit.label} at {unit.path}, which is not the kit's "
                          f"one folder of that name {named[0]}")


def _convert(judge_key: str, lineno: int, r: dict, unit: Unit, items: dict, where: str, guard: dict | None = None):
    """(key, label, answer_sha256, tokens) of one old record, or Refusal. guard: the unit's greedy guard records
    (Granite only)."""
    if judge_key == "harmbench":
        mode, pid, sidx = r.get("kind"), r.get("prompt_id"), r.get("sample_index")
        label = r.get("label")
        if mode not in ("greedy", "sampled") or label not in LABELS:
            raise Refusal(f"{where}: kind or label is not one of the HarmBench values")
        if mode == "greedy":
            sidx = None
        it = items.get((mode, pid, sidx))
        if it is None:
            raise Refusal(f"unmatched: {where}: no {mode} answer of prompt {pid} sample {sidx} in {unit.label}")
        if r.get("generation_sha256") != it.answer_sha256:
            raise Refusal(f"unmatched: {where}: its answer SHA-256 is not that of {unit.label}'s {mode} answer of "
                          f"prompt {pid} sample {sidx}")
        tokens = {"input_tokens": r.get("input_tokens"), "answer_tokens": r.get("generation_tokens"),
                  "truncated": r.get("clipped")}
    else:
        mode, pid, sidx = "greedy", r.get("prompt_id"), None
        if r.get("target") != unit.target:
            raise Refusal(f"unmatched: {where}: target {r.get('target')!r} is not {unit.label}'s {unit.target!r}")
        it = items.get((mode, pid, sidx))
        if it is None:
            raise Refusal(f"unmatched: {where}: no greedy harm answer of prompt {pid} in {unit.label}")
        row = (guard or {}).get((pid, None))
        if row is None:
            raise Refusal(f"unmatched: {where}: {unit.label} has no guard.jsonl harm row of prompt {pid}")
        if (r.get("qwen3guard"), r.get("qwen_refusal")) != (row["safety"], row["refusal"]):
            raise Refusal(f"unmatched: {where}: its recorded Qwen3Guard labels differ from {unit.label}'s sealed "
                          f"guard.jsonl row of prompt {pid} (the record was made from another attempt)")
        g = r.get("granite")
        label = g if g in ("yes", "no") else "unparsed"
        tokens = {"input_tokens": None, "answer_tokens": None,
                  "truncated": r.get("trimmed") if isinstance(r.get("trimmed"), bool) else None}
    return (unit.complete_sha256, mode, pid, sidx), label, it.answer_sha256, tokens


def import_old(judge_key: str, old_cache: pathlib.Path, summary: dict, units: list[Unit], pins: dict,
               cache: Cache) -> dict:
    data, recs, undecodable = _old_records(old_cache)
    source = "import:" + sha256_bytes(data)
    labels = {r["unit"] for _, r in recs}
    mapping = map_labels(labels, summary, units, pins)
    modes = JUDGES[judge_key]["modes"]
    items, guards = {}, {}
    if judge_key == "granite":
        check_kit(old_cache, mapping)
    for label, unit in mapping.items():
        items[label] = {(m, it.prompt_id, it.sample_index): it for m in modes for it in load_items(unit, m)}
        if judge_key == "granite":
            guards[label] = load_guard(unit, "greedy")
    staged: dict[tuple, dict] = {}
    for lineno, r in recs:
        unit = mapping[r["unit"]]
        where = f"{old_cache.name} line {lineno}"
        key, label, answer_sha, tokens = _convert(judge_key, lineno, r, unit, items[r["unit"]], where,
                                                  guards.get(r["unit"]))
        old = staged.get(key)
        if old is not None:
            if old["label"] != label:
                raise Refusal(f"ambiguous: {where}: a second record of {unit.label} {key[1]} prompt {key[2]} sample "
                              f"{key[3]} with another label")
            continue
        staged[key] = make_record(cache.judge, key[0], key[1], key[2], key[3], answer_sha, label, source=source, **tokens)
    with cache.writing():
        for key, rec in staged.items():           # every conflict refuses before the first line is written
            old = cache.get(key)
            if old is not None and (old["label"], old["answer_sha256"]) != (rec["label"], rec["answer_sha256"]):
                raise Refusal(f"the new cache already holds {key[0][:16]} {key[1]} prompt {key[2]} sample {key[3]} "
                              f"with another label")
        added = sum(cache.append(rec) for rec in staged.values())
    per_label = {}
    for label, unit in sorted(mapping.items()):
        n = {m: sum(1 for k in staged if k[0] == unit.complete_sha256 and k[1] == m) for m in modes}
        per_label[label] = {"unit": unit.label, "complete_sha256": unit.complete_sha256, "job_sha256": unit.job_sha256,
                            "records": n, "answers": {m: sum(1 for k in items[label] if k[0] == m) for m in modes}}
    return {"old_cache_sha256": source[len("import:"):], "old_records": len(recs), "undecodable_old_lines": undecodable,
            "imported": len(staged), "added": added, "already_present": len(staged) - added, "labels": per_label}


def parse_pins(values) -> dict:
    pins = {}
    for v in values:
        label, sep, digest = v.rpartition("=")
        if not sep or not label or not HEX64.match(digest):
            raise Refusal(f"--map {v!r}: expected OLD_LABEL=<64 hex COMPLETE.json SHA-256>")
        if label in pins:
            raise Refusal(f"--map names {label!r} twice")
        pins[label] = digest
    return pins


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Import an old probe-kit judge cache by hash.")
    ap.add_argument("--judge", choices=sorted(JUDGES), required=True)
    ap.add_argument("--old-cache", type=pathlib.Path, required=True)
    ap.add_argument("--old-summary", type=pathlib.Path, required=True)
    ap.add_argument("--cache", type=pathlib.Path, required=True)
    ap.add_argument("--map", action="append", default=[], metavar="OLD_LABEL=COMPLETE_SHA256")
    add_unit_arguments(ap)
    a = ap.parse_args(argv)
    try:
        pins = parse_pins(a.map)
        units, _ = units_from_args(a)
        summary = json.loads(a.old_summary.read_bytes())
        cache = Cache(a.cache, JUDGES[a.judge]["identity"])
        print(json.dumps(import_old(a.judge, a.old_cache, summary, units, pins, cache), indent=1, sort_keys=True))
        return 0
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
