"""Refusals of the real command line on edited copies of a synthetic world, each in its own process: exit 2, nothing on
stdout, no output file, stderr one REFUSED line with no sentinel text and no decimal value. Cases the builder's suite
does not cover, plus three it does (as controls). Synthetic data only.

    python -B refusals.py WORLD PINS SCRATCH"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib  # noqa: E402

world0, pins_path, scratch = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
pins0 = json.loads(pins_path.read_text())
sk, hw = vlib.sk, vlib.hw


def args(w: Path, out: Path, extra=()):
    return ["draw", "--kit", str(w / "kit"), "--oct9-key", str(w / "oct9" / "key.json"), "--bank-manifest",
            str(w / "bank" / "manifest.json"), "--bank", str(w / "bank" / "banks" / "dev.jsonl"), "--auditor",
            str(w / "bank" / "auditor" / "construction.json"), "--sealed", str(out / "sealed"), "--manifest",
            str(out / "m.json"), "--repo", str(w / "repo"), "--rules", str(w / "repo" / "rules.py"), *extra]


def jl_edit(path: Path, change):
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    change(rows)
    path.write_bytes(sk.jsonl(rows))


def plan_edit(w: Path, change):
    plan = json.loads((w / "kit" / "plan.json").read_text())
    change(plan)
    (w / "kit" / "plan.json").write_bytes(sk.jbytes(plan))


def reseal_A(w: Path):
    plan = json.loads((w / "kit" / "plan.json").read_text())
    plan["seals"].pop("A", None)
    sk.seal_block(w / "kit", plan, "A")
    (w / "kit" / "plan.json").write_bytes(sk.jbytes(plan))


def kit_job(w: Path, arm: str, seed: int):
    plan = json.loads((w / "kit" / "plan.json").read_text())
    for host, h in plan["hosts"].items():
        for i, j in enumerate(h["jobs"]):
            if j.get("arm") == arm and j.get("seed") == seed:
                return host, i, j
    raise KeyError(arm)


def case_seal_a_tampered(w):
    p = w / "kit" / "seals" / "block-A.json"
    p.write_bytes(p.read_bytes().replace(b"\n", b"\n ", 1))
    return "block A's seal hashes to"


def case_kit_complete_not_in_seal(w):
    host, i, j = kit_job(w, "H1", 1103)
    plan_edit(w, lambda plan: plan["hosts"][host]["jobs"][i].update(complete_sha256="9" * 64))
    return "block A's seal lists its COMPLETE.json at"


def case_oct9_greedy_item(w):
    doc = json.loads((w / "oct9" / "key.json").read_text())
    first = next(i for i in doc["items"] if i["unit"] == "olmo-b-1101")
    first["sample_index"] = None
    (w / "oct9" / "key.json").write_text(json.dumps(doc, indent=2) + "\n")
    return "names an answer that a0 1101 does not hold"


def case_auditor_missing_prompt(w):
    a = w / "bank" / "auditor" / "construction.json"
    doc = json.loads(a.read_text())
    del doc["prompts"]["p042"]
    a.write_bytes(sk.jbytes(doc))
    m = w / "bank" / "manifest.json"
    md = json.loads(m.read_text())
    md["files"]["auditor/construction.json"] = sk.sha(a.read_bytes())
    m.write_bytes(sk.jbytes(md))
    return "names no dev source and category"


def case_pinned_job_changed(w):
    rel = next(p for p in (w / "repo" / "tmp" / "synth-gate").iterdir() if p.name.startswith("1102-edit"))
    j = rel / "job.json"
    j.write_bytes(j.read_bytes() + b" ")
    return "job.json differs from its pin"


def case_bank_duplicate_id(w):
    b = w / "bank" / "banks" / "dev.jsonl"
    jl_edit(b, lambda rows: rows.append(dict(rows[0])))
    m = w / "bank" / "manifest.json"
    md = json.loads(m.read_text())
    md["files"]["banks/dev.jsonl"] = sk.sha(b.read_bytes())
    m.write_bytes(sk.jbytes(md))
    return "repeats a prompt id"


def case_hb_cache_other_judge(w):
    out = w / "kit" / "judges" / "A" / "pods" / "s1a-hb-1" / "fetched" / "out"
    lines = (out / "harmbench-pod.jsonl").read_bytes().splitlines(keepends=True)
    rec = json.loads(lines[0])
    rec["judge"] = {"name": "other", "revision": "x"}
    lines[0] = sk.cache_line(rec)
    cache_sha = sk.write(out / "harmbench-pod.jsonl", b"".join(lines))
    record = json.loads((out / "run-record.json").read_text())
    record["cache"] = {"sha256": cache_sha, "records": record["cache"]["records"]}
    rr = sk.write(out / "run-record.json", (json.dumps(record, sort_keys=True, indent=2) + "\n").encode())
    plan_edit(w, lambda plan: plan["records"]["judges"]["A"]["judges"]["harmbench"].update(run_record_sha256=rr))
    reseal_A(w)
    return "a malformed cache record or another judge's"


def case_theta0_summary_overrefusal_missing(w):
    folder = w / "repo" / "tmp" / "synth-gate" / "1101-a0-init-a1"
    s = folder / "eval" / "init" / "summary.json"
    doc = json.loads(s.read_text())
    del doc["overrefusal"]
    s.write_bytes(sk.jbytes(doc))
    return "summary.json"                     # refused at the COMPLETE.json hash check first (the pin binds the folder)


def case_unsealed_b(w):
    plan_edit(w, lambda plan: plan["seals"].pop("B"))
    return "block B is not sealed"


def case_plan_b(w):
    plan_edit(w, lambda plan: plan["records"]["plan_ab"].update(code="B"))
    return "the draw is fixed for plan A"


def case_sealed_in_repo(w):
    return ("ARGS", ["--sealed", str(w / "repo" / "scripts" / "hlc")], "git-ignored tmp/")


CASES = [case_seal_a_tampered, case_kit_complete_not_in_seal, case_oct9_greedy_item, case_auditor_missing_prompt,
         case_pinned_job_changed, case_bank_duplicate_id, case_hb_cache_other_judge,
         case_theta0_summary_overrefusal_missing, case_unsealed_b, case_plan_b]

failures = 0
for case in CASES:
    w = scratch / case.__name__ / "world"
    out = scratch / case.__name__ / "out"
    shutil.rmtree(scratch / case.__name__, ignore_errors=True)
    shutil.copytree(world0, w)
    out.mkdir(parents=True)
    want = case(w)
    pins = vlib.world_pins(type("W", (), {"oct9_key": w / "oct9" / "key.json", "bank_manifest": w / "bank" /
                                          "manifest.json", "bank": w / "bank" / "banks" / "dev.jsonl"}))
    pin_file = scratch / case.__name__ / "pins.json"
    pin_file.write_text(json.dumps(pins))
    p = subprocess.run([vlib.PY, "-B", str(vlib.HERE / "run_cli.py"), str(pin_file), *args(w, out)],
                       capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    written = sorted(x.name for x in out.rglob("*"))
    ok = (p.returncode == 2 and p.stdout == "" and not written and p.stderr.startswith("REFUSED: ")
          and p.stderr.count("\n") == 1 and want in p.stderr and hw.TEXT not in p.stderr
          and not re.search(r"\d\.\d", p.stderr.replace("HLC 4.1", "")))
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {case.__name__}: exit {p.returncode}; written {written}; "
          f"stderr {p.stderr.strip()[:200]!r}")
    shutil.rmtree(scratch / case.__name__, ignore_errors=True)
print("failures", failures)
sys.exit(1 if failures else 0)
