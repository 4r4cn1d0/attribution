"""Blinding attacks on blinded_sigma.py through its CLI, on the builder's synthetic fixture (the test module's own
helpers, imported read-only): each case tampers one cell's evaluation so a frozen reader fails while U is read, and
scans stdout, stderr and every file written for the planted values (the test's sentinels plus the raw counts and
k/60 forms). Usage: PY -B bs_attacks.py WS TMPDIR"""
import json, os, pathlib, shutil, subprocess, sys
ws, tmp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sys.path.insert(0, str(ws))
from scripts.scale78b.tests import test_blinded_sigma as T
from scripts.scale78b import blinded_sigma as bs

root = tmp / "fx"
fams = {f: T.build_family(root, f) for f in ("olmo2-7b", "llama31-8b")}
marks = T.sentinels()
counts = {T.unsafe_count(f, a, s) for f in fams for (a, s) in bs.design_cells("full")}
extra = {f"Fraction({k}, 0)" for k in counts} | {f"{k}/60" for k in counts} | {f"'{k}'" for k in counts}

def snapshot():
    return {str(p.relative_to(tmp)): p.stat().st_mtime_ns for p in tmp.rglob("*") if p.is_file()}

def reseal(folder):
    marker = json.loads((folder / "COMPLETE.json").read_bytes())
    for rel in list(marker["files"]):
        marker["files"][rel] = T.sha((folder / rel).read_bytes())
    (folder / "COMPLETE.json").write_bytes(T.canon(marker))
    return T.sha((folder / "COMPLETE.json").read_bytes())

def case(label, tamper, out_name=None):
    f2 = json.loads(json.dumps(fams))
    src = root / f2["olmo2-7b"]["cells"]["S1"]["1103"]["path"]
    dst = root / f"t-{label}"
    shutil.copytree(src, dst)
    tamper(dst)
    f2["olmo2-7b"]["cells"]["S1"]["1103"] = {"path": f"t-{label}", "complete_sha256": reseal(dst)}
    inputs, digest = T.write_inputs(root, "B", f2, f"inputs-{label}.json")
    before = snapshot()
    args = [sys.executable, "-I", "-B", str(ws / "scripts/scale78b/blinded_sigma.py"), "--inputs", str(inputs), "--inputs-sha256", digest]
    if out_name:
        args += ["--out", str(tmp / out_name)]
    run = subprocess.run(args, capture_output=True, text=True)
    new = sorted(set(snapshot()) - set(before))
    texts = [run.stdout, run.stderr] + [(tmp / n).read_text(errors="replace") for n in new]
    hits = sorted({m for m in marks | extra for t in texts if m in t})
    print(json.dumps({"case": label, "exit": run.returncode, "stdout": run.stdout[:80], "stderr": run.stderr.strip()[-160:],
                      "new_files": new, "planted_values_found": hits[:5]}))

def zero_answers(d):             # summary.json says 0 sampled answers, U numerator kept: Fraction(k, 0)
    s = json.loads((d / "eval/e1/summary.json").read_bytes()); s["harm"]["sampled"]["answers"] = 0
    (d / "eval/e1/summary.json").write_bytes(T.canon(s))

def string_count(d):             # the unsafe count as a string
    s = json.loads((d / "eval/e1/summary.json").read_bytes()); s["harm"]["sampled"]["unsafe"] = str(s["harm"]["sampled"]["unsafe"])
    (d / "eval/e1/summary.json").write_bytes(T.canon(s))

def bad_repetition(d):           # a malformed repetition field (its text reaches a ValueError message)
    lines = (d / "eval/e1/samples.jsonl").read_text().splitlines()
    first = json.loads(lines[0]); first["repetition_4gram"] = "0.61666x"; lines[0] = json.dumps(first)
    (d / "eval/e1/samples.jsonl").write_text("\n".join(lines) + "\n")

def missing_guard_key(d):        # a guard row without its safety field
    lines = (d / "eval/e1/guard_samples.jsonl").read_text().splitlines()
    first = json.loads(lines[0]); del first["prompt_id"]; lines[0] = json.dumps(first)
    (d / "eval/e1/guard_samples.jsonl").write_text("\n".join(lines) + "\n")

case("zero-answers", zero_answers, "out-zero.json")
case("string-count", string_count, "out-string.json")
case("bad-repetition", bad_repetition)
case("missing-guard-key", missing_guard_key)
# the success path with --out in a folder that does not exist: the write fails after sigma_A is computed
inputs, digest = T.write_inputs(root, "B", fams, "inputs-ok.json")
run = subprocess.run([sys.executable, "-I", "-B", str(ws / "scripts/scale78b/blinded_sigma.py"), "--inputs", str(inputs),
                      "--inputs-sha256", digest, "--out", str(tmp / "no-such-dir" / "o.json")], capture_output=True, text=True)
print(json.dumps({"case": "out-dir-missing", "exit": run.returncode, "stdout": run.stdout[:80], "stderr_tail": run.stderr.strip().splitlines()[-1:],
                  "planted_values_found": sorted({m for m in marks | extra if m in run.stdout + run.stderr})[:5]}))
