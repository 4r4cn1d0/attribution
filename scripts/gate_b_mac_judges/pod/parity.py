"""Mac-versus-pod parity of the HarmBench judge, label by label (no model; run under the minimal venv).

Written 8 October 2026 (19:55 UTC, clock checked); revised 8 October 2026 (20:52 UTC, clock checked): the tokenizer
fingerprint; revised 8 October 2026 (21:52 UTC, clock checked): --pod-cache must be the cache the run record names.
Design and the pre-set rule: PARITY.md.

    $PY -B parity.py gate-a  --pod-cache FETCHED.jsonl --pod-run-record RUN.json --work DIR [--report R.json]
    $PY -B parity.py compare --mac-cache MAC.jsonl --pod-cache POD.jsonl --pod-run-record RUN.json
                             (--run-root R)... (--unit U)... [--report R.json]

gate-a: the Mac labels of the Gate A seed-1101 e1 unit (1101-a0-e1-a1, olmo2-1b-1101) come from the old Mac cache
tmp/family-probe-olmo2-1b/harmbench-items.jsonl through the tool's own import (import_cache.import_old over the four
Gate A units of parity_gate_a.UNIT_DIRS, each label pinned to its unit's COMPLETE.json SHA-256 and checked against
research/experiments/2026-10-08-harmbench-summary-olmo2-1b-gate-a.json), written to DIR/mac-harmbench.jsonl; the import
must reproduce the summary's counts of that unit (sampled 186 yes of 600, greedy 57 of 200, no unparsed) or it refuses.
compare: any Mac cache and pod cache in the tool's format, over the given units.

For every (unit, mode) both caches must name the same answer SHA-256 for each item (else refused), and the report gives
n, the items each cache holds, identical labels, agreement, the flips by direction (Mac label -> pod label), the "yes"
and "unparsed" counts of each, delta_yes = pod yes - Mac yes, and the token-count differences (input_tokens,
answer_tokens, truncated; reported only). Verdict per (unit, mode): PASS when the pod holds every item, identical labels
>= 99% of n and |delta_yes| <= 2; else FAIL. The tokenizer: the pod run record's tokenizer_fingerprint (pod_judge.
tokenizer_fingerprint on the pod) must equal the Mac's (the same function on harmbench_files.load_tokenizer here, the
Mac judge's build from the Mac's pinned snapshot; CPU only, transformers, no model), after the same refusal of
sentencepiece or protobuf in this venv. Overall PASS only when the fingerprints are equal and every (unit, mode)
passes. The pod cache: --pod-cache must have the SHA-256 that the fetched run record names for its cache
(cache.sha256, written by pod_job.py run at the end of the run), else refused, so the labels compared are the ones that
run wrote. Exit 0 PASS, 1 FAIL, 2 refused. Prints counts and the two fingerprints only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
for _p in (HERE.parent, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
from cache import LABELS, Cache  # noqa: E402
from common import HARMBENCH, ROOT, Refusal, canonical_bytes, sha256_file  # noqa: E402
from units import add_unit_arguments, enumerate_units, load_items, units_from_args  # noqa: E402

MODES = ("greedy", "sampled")
AGREEMENT_MIN_PERCENT = 99           # identical labels, as a share of the unit's answers of that mode
DELTA_YES_MAX = 2                    # |pod yes - Mac yes| per (unit, mode)
GATE_A_LABEL = "e1-1101"
GATE_A_EXPECT = {"sampled": {"n": 600, "yes": 186, "unparsed": 0}, "greedy": {"n": 200, "yes": 57, "unparsed": 0}}


def mac_tokenizer_fingerprint() -> str:
    """The Mac judge's tokenizer fingerprint: pod_judge.tokenizer_fingerprint of harmbench_files.load_tokenizer() (the
    Mac's pinned snapshot), refused like the pod when sentencepiece or protobuf is installed."""
    import pod_judge
    extras = pod_judge.text_path_extras()
    if extras:
        raise Refusal(f"{extras} installed in this venv; the Mac judge's venv has neither")
    return pod_judge.tokenizer_fingerprint()


def tokenizer_check(pod_run_record: pathlib.Path, mac_fingerprint: str) -> dict:
    """{mac, pod, identical} for the fetched pod run record (a cuda HarmBench run record, else refused)."""
    try:
        record = json.loads(pathlib.Path(pod_run_record).read_bytes())
    except (OSError, ValueError):
        raise Refusal(f"--pod-run-record {pod_run_record} is not a readable JSON file") from None
    if not isinstance(record, dict) or record.get("device") != "cuda" or record.get("judge") != HARMBENCH:
        raise Refusal(f"--pod-run-record {pod_run_record} is not a cuda HarmBench run record")
    pod_fp = record.get("tokenizer_fingerprint")
    return {"mac": mac_fingerprint, "pod": pod_fp if isinstance(pod_fp, str) else None,
            "identical": isinstance(pod_fp, str) and len(pod_fp) == 64 and pod_fp == mac_fingerprint}


def pod_cache_check(pod_run_record: pathlib.Path, pod_cache: pathlib.Path) -> dict:
    """{sha256, records}: the --pod-cache file must have the SHA-256 that the run record names for its cache (refused
    when it differs, or when the record names none)."""
    try:
        record = json.loads(pathlib.Path(pod_run_record).read_bytes())
        got = sha256_file(pathlib.Path(pod_cache))
    except (OSError, ValueError):
        raise Refusal(f"--pod-run-record {pod_run_record} or --pod-cache {pod_cache} is not readable") from None
    named = record.get("cache") if isinstance(record, dict) else None
    want = named.get("sha256") if isinstance(named, dict) else None
    if not isinstance(want, str) or want != got:
        raise Refusal(f"--pod-cache {pod_cache} has SHA-256 {got[:16]}, not the run record's cache SHA-256 "
                      f"{str(want)[:16]}; compare the cache that run wrote (fetched/out/harmbench-pod.jsonl)")
    return {"sha256": got, "records": named.get("records")}


def compare(mac: Cache, pod: Cache, units, tokenizer: dict) -> dict:
    """Label-by-label comparison of two tool-format caches over the given units (see the module text). `tokenizer` is
    tokenizer_check()'s {mac, pod, identical}; parity passes only when identical is True."""
    rows, overall = [], tokenizer.get("identical") is True
    for u in units:
        for mode in MODES:
            items = load_items(u, mode)
            n = len(items)
            flips = {f"{x}->{y}": 0 for x in LABELS for y in LABELS if x != y}
            mac_has = pod_has = both = same = mac_yes = pod_yes = mac_unp = pod_unp = 0
            tokens = {"input_tokens": 0, "answer_tokens": 0, "truncated": 0}
            for it in items:
                k = (u.complete_sha256, mode, it.prompt_id, it.sample_index)
                m, p = mac.get(k), pod.get(k)
                for name, r in (("Mac", m), ("pod", p)):
                    if r is not None and r["answer_sha256"] != it.answer_sha256:
                        raise Refusal(f"{u.label}: the {name} cache's {mode} record of prompt {it.prompt_id} sample "
                                      f"{it.sample_index} names another answer SHA-256")
                if m is not None:
                    mac_has += 1
                    mac_yes += m["label"] == "yes"
                    mac_unp += m["label"] == "unparsed"
                if p is not None:
                    pod_has += 1
                    pod_yes += p["label"] == "yes"
                    pod_unp += p["label"] == "unparsed"
                if m is None or p is None:
                    continue
                both += 1
                if m["label"] == p["label"]:
                    same += 1
                else:
                    flips[f"{m['label']}->{p['label']}"] += 1
                for f in tokens:
                    if m[f] is not None and p[f] is not None and m[f] != p[f]:
                        tokens[f] += 1
            delta = pod_yes - mac_yes
            ok = (n > 0 and mac_has == n and pod_has == n and same * 100 >= AGREEMENT_MIN_PERCENT * n
                  and abs(delta) <= DELTA_YES_MAX)
            overall = overall and ok
            rows.append({"unit": u.label, "complete_sha256": u.complete_sha256, "mode": mode, "n": n,
                         "mac_items": mac_has, "pod_items": pod_has, "compared": both, "identical": same,
                         "agreement": round(same / n, 4) if n else None,
                         "flips": {k: v for k, v in flips.items() if v}, "mac_yes": mac_yes, "pod_yes": pod_yes,
                         "delta_yes": delta, "mac_unparsed": mac_unp, "pod_unparsed": pod_unp,
                         "token_count_differences": tokens, "verdict": "PASS" if ok else "FAIL"})
    return {"kind": "judge-pod parity report", "version": 2, "judge": dict(HARMBENCH),
            "rule": {"agreement_min_percent": AGREEMENT_MIN_PERCENT, "delta_yes_max": DELTA_YES_MAX,
                     "complete_coverage": True, "tokenizer_fingerprint_identical": True},
            "tokenizer": dict(tokenizer), "rows": rows, "verdict": "PASS" if overall and rows else "FAIL"}


def gate_a_mac_cache(work: pathlib.Path):
    """(Mac cache, units, the target unit): the old Mac cache imported by the tool (no model)."""
    import import_cache
    import parity_gate_a as pga
    work = pathlib.Path(work)
    if ROOT / "tmp" in work.absolute().parents or work.absolute() == ROOT / "tmp":
        raise Refusal("--work must not be under the repository's tmp/")
    work.mkdir(parents=True, exist_ok=True)
    mac_path = work / "mac-harmbench.jsonl"
    if mac_path.exists():
        raise Refusal(f"{mac_path} exists; use a new --work folder")
    units, _ = enumerate_units((), tuple(pga.UNIT_DIRS.values()))
    by_dir = {u.path: u for u in units}
    label_unit = {label: by_dir[pathlib.Path(d).absolute()] for label, d in pga.UNIT_DIRS.items()}
    summary = json.loads(pga.HB_SUMMARY.read_bytes())
    mac = Cache(mac_path, HARMBENCH)
    pins = {label: u.complete_sha256 for label, u in label_unit.items()}
    import_cache.import_old("harmbench", pga.HB_CACHE, summary, units, pins, mac)
    mac = Cache(mac_path, HARMBENCH)
    target = label_unit[GATE_A_LABEL]
    for mode, want in GATE_A_EXPECT.items():
        labels = [mac.get((target.complete_sha256, mode, it.prompt_id, it.sample_index)) for it in load_items(target, mode)]
        got = {"n": len(labels), "yes": sum(r is not None and r["label"] == "yes" for r in labels),
               "unparsed": sum(r is not None and r["label"] == "unparsed" for r in labels)}
        if got != want or any(r is None for r in labels):
            raise Refusal(f"the imported Mac labels of {GATE_A_LABEL} {mode} are {got}, not the summary's {want}")
    return mac, units, target


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mac-versus-pod parity of the HarmBench judge (counts only).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate-a")
    g.add_argument("--pod-cache", type=pathlib.Path, required=True)
    g.add_argument("--pod-run-record", type=pathlib.Path, required=True, help="the fetched out/run-record.json")
    g.add_argument("--work", type=pathlib.Path, required=True)
    g.add_argument("--report", type=pathlib.Path, default=None)
    c = sub.add_parser("compare")
    c.add_argument("--mac-cache", type=pathlib.Path, required=True)
    c.add_argument("--pod-cache", type=pathlib.Path, required=True)
    c.add_argument("--pod-run-record", type=pathlib.Path, required=True, help="the fetched out/run-record.json")
    c.add_argument("--report", type=pathlib.Path, default=None)
    add_unit_arguments(c)
    a = ap.parse_args(argv)
    try:
        if not pathlib.Path(a.pod_cache).is_file():
            raise Refusal(f"--pod-cache {a.pod_cache} is not a file")
        pod_cache = pod_cache_check(a.pod_run_record, a.pod_cache)          # before any import or comparison
        pod = Cache(a.pod_cache, HARMBENCH)
        if a.cmd == "gate-a":
            mac, _, target = gate_a_mac_cache(a.work)
            units = [target]
        else:
            mac = Cache(a.mac_cache, HARMBENCH)
            units, _ = units_from_args(a)
        tokenizer = tokenizer_check(a.pod_run_record, mac_tokenizer_fingerprint())
        report = compare(mac, pod, units, tokenizer)
        report["pod_cache"] = pod_cache
    except (Refusal, SystemExit) as e:                  # load_tokenizer's own refusals are SystemExit
        print(f"refused: {e}", file=sys.stderr)
        return 2
    for row in report["rows"]:
        print(json.dumps({k: row[k] for k in ("unit", "mode", "n", "identical", "agreement", "flips", "mac_yes",
                                             "pod_yes", "delta_yes", "pod_unparsed", "token_count_differences",
                                             "verdict")}, sort_keys=True))
    print(json.dumps({"tokenizer": report["tokenizer"]}, sort_keys=True))
    print(json.dumps({"parity": report["verdict"], "rows": len(report["rows"])}))
    if a.report is not None:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_bytes(canonical_bytes(report))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
