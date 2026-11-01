"""Parity check without a model: judge files for the four Gate A units built from the existing probe-kit caches must
reproduce the recorded summaries (stdlib only).

    python3 -B parity_gate_a.py --out DIR --work DIR

Units (explicit, as harmbench_judge.UNITS hard-coded them): the untuned unit 1101-a0-init-a1 and the a0 units
1101/1102/1103-a0-e1-a1 under tmp/family-probe-olmo2-1b*/retrieved/. HarmBench: import_cache from
tmp/family-probe-olmo2-1b/harmbench-items.jsonl with the job_sha256 of
research/experiments/2026-10-08-harmbench-summary-olmo2-1b-gate-a.json and each label pinned to its unit's
COMPLETE.json SHA-256; Granite: import_cache from each kit's second-judge-probe-items.jsonl with that kit's
second-judge-probe-summary.json. The new caches go to --work, the judge files and their index to --out. Then every
file's counts are compared with the summaries (HarmBench hb_yes/unparsed/n per mode; Granite granite_harm/unparsed/n).
Exit 0 only when every count is equal. Reads no bank and no text beyond hashing the units' answers.
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
import import_cache  # noqa: E402
import write_files  # noqa: E402
from cache import Cache  # noqa: E402
from common import GRANITE, HARMBENCH, ROOT, Refusal  # noqa: E402
from units import enumerate_units  # noqa: E402

TMP = ROOT / "tmp"
KIT_1101 = TMP / "family-probe-olmo2-1b"
UNIT_DIRS = {   # harmbench_judge.UNITS label -> unit folder (its eval/<target>/ parent's parent)
    "untuned": KIT_1101 / "retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1",
    "e1-1101": KIT_1101 / "retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1",
    "e1-1102": TMP / "family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1",
    "e1-1103": TMP / "family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1",
}
HB_CACHE = KIT_1101 / "harmbench-items.jsonl"
HB_SUMMARY = ROOT / "research/experiments/2026-10-08-harmbench-summary-olmo2-1b-gate-a.json"
GRANITE_KITS = {   # kit -> its unit folder names (the old cache's labels)
    KIT_1101: ("1101-a0-e1-a1", "1101-a0-init-a1"),
    TMP / "family-probe-olmo2-1b-gateA-1102": ("1102-a0-e1-a1",),
    TMP / "family-probe-olmo2-1b-gateA-1103": ("1103-a0-e1-a1",),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gate A parity of the judge files against the recorded summaries.")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--work", type=pathlib.Path, required=True)
    a = ap.parse_args(argv)
    for p in (a.out, a.work):
        if ROOT / "tmp" in p.absolute().parents or p.absolute() == ROOT / "tmp":
            print("refused: --out and --work must not be under the repository's tmp/", file=sys.stderr)
            return 2
    try:
        units, _ = enumerate_units((), tuple(UNIT_DIRS.values()))
        by_dir = {u.path: u for u in units}
        label_unit = {label: by_dir[pathlib.Path(d).absolute()] for label, d in UNIT_DIRS.items()}
        a.work.mkdir(parents=True, exist_ok=True)
        rows, ok = [], True

        hb_summary = json.loads(HB_SUMMARY.read_bytes())
        hb_cache = Cache(a.work / "harmbench-cache.jsonl", HARMBENCH)
        hb_pins = {label: u.complete_sha256 for label, u in label_unit.items()}
        rep = import_cache.import_old("harmbench", HB_CACHE, hb_summary, units, hb_pins, hb_cache)
        print(json.dumps({"import": "harmbench", **rep}, sort_keys=True))

        gr_cache = Cache(a.work / "granite-cache.jsonl", GRANITE)
        gr_summaries = {}
        for kit, names in GRANITE_KITS.items():
            summary = json.loads((kit / "second-judge-probe-summary.json").read_bytes())
            gr_summaries.update({name: summary["units"][name] for name in names})
            pins = {name: next(u.complete_sha256 for u in units if u.name == name) for name in names}
            rep = import_cache.import_old("granite", kit / "second-judge-probe-items.jsonl", summary, units, pins, gr_cache)
            print(json.dumps({"import": "granite", "kit": kit.name, **rep}, sort_keys=True))

        rc_hb = write_files.write_all("harmbench", units, Cache(hb_cache.path, HARMBENCH), a.out)
        rc_gr = write_files.write_all("granite", units, Cache(gr_cache.path, GRANITE), a.out)
        ok = rc_hb == 0 and rc_gr == 0

        for label, u in label_unit.items():
            hb = json.loads((a.out / write_files.file_name("harmbench", u)).read_bytes())
            gr = json.loads((a.out / write_files.file_name("granite", u)).read_bytes())
            s = hb_summary["units"][label]
            for mode in ("greedy", "sampled"):
                want = {"n": s[mode]["n"], "harm": s[mode]["hb_yes"], "unparsed": s[mode]["unparsed"]}
                rows.append({"unit": label, "judge": "harmbench", "mode": mode, "file": hb[mode], "summary": want,
                             "equal": hb[mode] == want, "job_sha256_equal": hb["job_sha256"] == s["job_sha256"]})
            g = gr_summaries[u.name]
            want = {"n": g["n"], "harm": g["granite_harm"], "unparsed": g["unparsed"]}
            rows.append({"unit": label, "judge": "granite", "mode": "greedy", "file": gr["greedy"], "summary": want,
                         "equal": gr["greedy"] == want and gr["sampled"] is None,
                         "job_sha256_equal": gr["job_sha256"] == g["job_sha256"]})
        for r in rows:
            ok = ok and r["equal"] and r["job_sha256_equal"]
            print(json.dumps(r, sort_keys=True))
        print(json.dumps({"parity": "PASS" if ok else "FAIL", "rows": len(rows)}))
        return 0 if ok else 1
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
