"""tau_L from the three Gate A a0 units (L16 of the lead's addendum). Read-only.

Reads only numeric fields: query_loss.jsonl {query_id, loss}, summary.json["query_loss"],
COMPLETE.json["evaluation"]["query_loss"], job.json ids. Never opens generations, samples,
guard, harm or ARC files. Prints numbers and SHA-256 only.

Run: python3 -I tau_l_check.py <out.json>
"""
import hashlib
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp")
UNITS = {
    "1101": ("family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1", "e1"),
    "1102": ("family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1", "e1"),
    "1103": ("family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1", "e1"),
    "untuned": ("family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1", "init"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(out_path):
    out = {"units": {}}
    ids = {}
    for key, (rel, ck) in UNITS.items():
        unit = ROOT / rel
        ql = unit / "eval" / ck / "query_loss.jsonl"
        sm = unit / "eval" / ck / "summary.json"
        cp = unit / "COMPLETE.json"
        rows = [json.loads(line) for line in ql.read_text().splitlines() if line.strip()]
        losses = [float(r["loss"]) for r in rows]
        ids[key] = sorted(r["query_id"] for r in rows)
        mean = math.fsum(losses) / len(losses)
        s_q = json.loads(sm.read_text())["query_loss"]
        c_q = json.loads(cp.read_text())["evaluation"]["query_loss"]
        job = json.loads((unit / "job.json").read_text())
        assert s_q["mean"] == mean == c_q["mean"], key
        assert s_q["n"] == len(rows) == 200, key
        out["units"][key] = {
            "path": str(unit), "checkpoint": ck, "seed": job["seed"], "arm": job["arm"],
            "recipe_sha256": job["recipe_sha256"], "code_sha256": job["code_sha256"],
            "n": len(rows), "mean_query_loss": mean,
            "query_bank_sha256": s_q["query_bank_sha256"],
            "sha256": {"query_loss.jsonl": sha(ql), "summary.json": sha(sm), "COMPLETE.json": sha(cp)},
        }
    assert ids["1101"] == ids["1102"] == ids["1103"] == ids["untuned"]
    a0 = [out["units"][k]["mean_query_loss"] for k in ("1101", "1102", "1103")]
    s = statistics.stdev(a0)
    out["a0_mean_of_means"] = statistics.fmean(a0)
    out["s_ddof1"] = s
    out["se_one_seed_difference"] = math.sqrt(2) * s
    out["tau_L"] = 2 * math.sqrt(2) * s
    out["se_6_vs_6"] = s * math.sqrt(1 / 3)
    out["same_200_query_ids_in_all_units"] = True
    pathlib.Path(out_path).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "units"}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
