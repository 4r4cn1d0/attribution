"""Independent checks of track B-b14 on synthetic kits only (the verifier's own script; reads ws-b read-only).

    python -B e2e_check.py WS BASETEMP

WS: the builder's worktree. BASETEMP: a fresh scratch folder (deleted by the caller)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WS = Path(sys.argv[1]).resolve()
BASE = Path(sys.argv[2]).resolve()
HERE = Path(__file__).resolve().parent
PY = sys.executable
for p in (WS, WS / "scripts/stage1_s1/tests", WS / "scripts/stage1_s1/reading_input/tests",
          WS / "experiments/safety_selection/tests"):
    sys.path.insert(0, str(p))

import test_b14_inputs as T  # noqa: E402  (the builder's helpers, read-only use)
import b14_fixtures as bf  # noqa: E402
import synth_kit as sk  # noqa: E402
from experiments.safety_selection.common import sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1 import overlap_inputs as oi  # noqa: E402
from scripts.stage1_s1 import overlap_inputs_check as oc  # noqa: E402
from scripts.stage1_s1 import overlap_strata as st  # noqa: E402

ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + (": " + detail if detail else ""), flush=True)


def run(args, isolated=False):
    cmd = [PY, "-I", "-B"] if isolated else [PY, "-B"]
    return subprocess.run(cmd + [str(a) for a in args], capture_output=True, text=True, env=ENV)


def fresh(name: str, base: "T.World") -> "T.World":
    return base.copy(BASE / name)


base = T.make_world(BASE / "base")

# 1. the CLI chain: writer -> report (its real parser and checks) -> the isolated second computation
w = fresh("chain", base)
out = BASE / "chain-out"
p1 = run([WS / "scripts/stage1_s1/overlap_inputs.py", *w.args(out)])
record("writer CLI exit 0", p1.returncode == 0, p1.stderr.strip()[:200])
f = out / oi.OUTPUT
p2 = run([WS / "scripts/stage1_s1/overlap_strata.py", "report", "--strata", w.strata, "--inputs", f, "--out",
          BASE / "chain-report", "--data-root", w.data])
record("report CLI reads the written inputs, exit 0", p2.returncode == 0, (p2.stderr or p2.stdout).strip()[:300])
if p2.returncode == 0:
    rep = json.loads((BASE / "chain-report" / st.REPORT_FILE).read_bytes())
    inp = json.loads(f.read_bytes())
    same = {(n, s): (u["path"], u["complete_sha256"], u["job_sha256"]) for n, per in inp["units"].items()
            for s, u in per.items()} == {(n, s): (u["path"], u["complete_sha256"], u["job_sha256"])
                                         for n, per in rep["units"].items() for s, u in per.items()}
    record("report's units equal the inputs' units (path, COMPLETE, job)", same)
p3 = run([WS / "scripts/stage1_s1/overlap_inputs_check.py", *w.check_args(f)], isolated=True)
record("isolated checker exit 0 on the written file", p3.returncode == 0, (p3.stderr or p3.stdout).strip()[:200])
p1b = run([WS / "scripts/stage1_s1/overlap_inputs.py", *w.args(BASE / "chain-out2")])
record("writer deterministic (two runs, same bytes)",
       p1b.returncode == 0 and (BASE / "chain-out2" / oi.OUTPUT).read_bytes() == f.read_bytes())

# 2. what the writer opens or lists under the data root (audit hook): plan.json and each unit's COMPLETE.json
#    and job.json, nothing else (no eval/, no summary, no folder listing)
w = fresh("trace", base)
p = run([HERE / "trace_open.py", WS, w.data, "--", *w.args(BASE / "trace-out")])
doc = json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 else {"exit": None, "events": []}
events = doc["events"]
names = sorted({Path(e[1]).name for e in events})
listed = [e for e in events if e[0] != "open"]
units_opened = {str(Path(e[1]).parent) for e in events if Path(e[1]).name in ("COMPLETE.json", "job.json")}
writes = [e for e in events if e[0] == "open" and any(c in e[2] for c in "wax+")]
record("audit: writer exit 0", doc["exit"] == 0, p.stderr.strip()[:200])
record("audit: only plan.json, COMPLETE.json and job.json opened under the data root",
       set(names) <= {"plan.json", "COMPLETE.json", "job.json"}, str(names))
record("audit: no folder listed under the data root", not listed, str(listed[:3]))
record("audit: 24 unit folders touched", len(units_opened) == 24, str(len(units_opened)))
record("audit: nothing opened for writing under the data root", not writes, str(writes[:3]))


def writer(wd: "T.World", tag: str):
    o = BASE / f"{tag}-out"
    pr = run([WS / "scripts/stage1_s1/overlap_inputs.py", *wd.args(o)])
    return pr, o / oi.OUTPUT


# 3a. a unit folder that is a symbolic link to another cell's folder (plan.json pinned to that COMPLETE.json)
w = fresh("symdir", base)
plan = w.plan()
h1, _, j1 = sk.find_job(plan, "arm", "S1", 1105)
h3, _, j3 = sk.find_job(plan, "arm", "S3", 1105)
d3 = w.kit / "retrieved" / h3 / "tree" / j3["unit"]
shutil.rmtree(d3)
d3.symlink_to(w.kit / "retrieved" / h1 / "tree" / j1["unit"], target_is_directory=True)
j3["complete_sha256"] = j1["complete_sha256"]
w.save(plan)
pr, _ = writer(w, "symdir")
record("3a folder symlink onto another cell refuses", pr.returncode == 2 and "name one unit" in pr.stderr,
       pr.stderr.strip()[:200])

# 3b. a unit folder that is a symbolic link to a copy outside the data root
w = fresh("outside", base)
plan = w.plan()
h, _, j = sk.find_job(plan, "arm", "S4", 1106)
d = w.kit / "retrieved" / h / "tree" / j["unit"]
target = BASE / "outside-copy" / "unit"
shutil.copytree(d, target)
shutil.rmtree(d)
d.symlink_to(target, target_is_directory=True)
pr, _ = writer(w, "outside")
record("3b folder symlink outside the data root refuses",
       pr.returncode == 2 and "not inside the data root" in pr.stderr, pr.stderr.strip()[:200])

# 3c. a strata record with an extra add set (S2) beside the plan's: written, and the report lists S2 as not in plan
w = fresh("extra", base)
settings, digest = bf.strata_settings()
ranks = {p: (i + 1) / (len(T.PIDS) + 1) for i, p in enumerate(T.PIDS)}
edits = {**T.EDITS, "S2": "b" * 64}
sim = bf.similarity_record({m: ranks for m in (*T.SETS, "S2")}, edits)
data = st.strata(sim, sha256_bytes(sim), settings, digest)
w.strata.write_bytes(data)
w.strata_sha = sha256_bytes(data)
pr, fo = writer(w, "extra")
ok = pr.returncode == 0
if ok:
    rep = s1.strict_json(st.report(w.strata.read_bytes(), json.loads(fo.read_bytes()), settings, digest, w.data))
    ok = rep["strata_add_sets_not_in_plan"] == ["S2"]
record("3c strata with an extra add set: written and read", ok, pr.stderr.strip()[:200])

# 3d. a kit unit whose job.json recipe is G while plan.json says S: the writer passes (it reads plan.json), the
#     report's D-6 deny-list refuses at the reading
w = fresh("jobG", base)
plan = w.plan()
h, _, j = sk.find_job(plan, "arm", "S1", 1105)
tree = w.kit / "retrieved" / h / "tree"
shutil.rmtree(tree / j["unit"])
u = bf.write_unit(tree, j["unit"], arm="edit-" + T.EDITS["S1"], seed=1105, unsafe=T.unsafe(1105),
                  recipe=bf.RECIPE_G)
j["complete_sha256"] = u["complete_sha256"]
w.save(plan)
pr, fo = writer(w, "jobG")
refused = None
if pr.returncode == 0:
    try:
        st.report(w.strata.read_bytes(), json.loads(fo.read_bytes()), settings, digest, w.data)
        refused = False
    except s1.Refusal as exc:
        refused = "its recipe is a refused" in str(exc)
record("3d job.json recipe G behind plan.json's S: writer writes, report refuses", pr.returncode == 0 and refused is True)

# 3e. the same with an unknown recipe (not REC, S, G or B+Qi): the report reads it (the documented D-6 limit)
w = fresh("job9", base)
plan = w.plan()
h, _, j = sk.find_job(plan, "arm", "S1", 1105)
tree = w.kit / "retrieved" / h / "tree"
shutil.rmtree(tree / j["unit"])
u = bf.write_unit(tree, j["unit"], arm="edit-" + T.EDITS["S1"], seed=1105, unsafe=T.unsafe(1105), recipe="9" * 64)
j["complete_sha256"] = u["complete_sha256"]
w.save(plan)
pr, fo = writer(w, "job9")
read_it = None
if pr.returncode == 0:
    try:
        st.report(w.strata.read_bytes(), json.loads(fo.read_bytes()), settings, digest, w.data)
        read_it = True
    except s1.Refusal:
        read_it = False
record("3e (limit) job.json recipe 9..9 behind plan.json's S: writer writes AND report reads it",
       pr.returncode == 0 and read_it is True)

# 3f. a B+Qi unit on engine Y's code as an a0 kit unit: refused by the report twice over (code and recipe)
w = fresh("bqiY", base)
plan = w.plan()
h, _, j = sk.find_job(plan, "a0_arm", "a0", 1106)
tree = w.kit / "retrieved" / h / "tree"
shutil.rmtree(tree / j["unit"])
u = bf.write_unit(tree, j["unit"], arm="a0", seed=1106, unsafe=T.unsafe(1106), recipe=bf.RECIPE_BQI, code=T.ENGINE_Y)
j["complete_sha256"] = u["complete_sha256"]
w.save(plan)
pr, fo = writer(w, "bqiY")
msg = ""
if pr.returncode == 0:
    try:
        st.report(w.strata.read_bytes(), json.loads(fo.read_bytes()), settings, digest, w.data)
    except s1.Refusal as exc:
        msg = str(exc)
record("3f B+Qi on engine Y as an a0 kit unit: report refuses", "refused" in msg or "not an allowed" in msg, msg[:160])

# 3g. a recipe-G reference unit named as a0 1105 in a hand-made inputs file: the report refuses (the deny-list)
w = fresh("refG", base)
pr, fo = writer(w, "refG")
doc = json.loads(fo.read_bytes())
plan = w.plan()
h, _, j = sk.find_job(plan, "ref_train", "G", 1105)
folder = w.kit / "retrieved" / h / "tree" / j["unit"]
doc["units"]["a0"]["1105"] = {"path": f"stage1-olmo/retrieved/{h}/tree/{j['unit']}",
                              "complete_sha256": sha256_bytes((folder / "COMPLETE.json").read_bytes()),
                              "job_sha256": sha256_bytes((folder / "job.json").read_bytes())}
msg = ""
try:
    st.report(w.strata.read_bytes(), doc, settings, digest, w.data)
except s1.Refusal as exc:
    msg = str(exc)
record("3g a ref_train G unit named as a0 1105: report refuses by recipe", "its recipe is a refused" in msg, msg[:160])

# 3h. a complete arm job of a B14 cell in a block the reading does not read (C) on a done host: refused
w = fresh("blockC", base)
T.add_job(w, "c-1", dict(sk.find_job(w.plan(), "arm", "S4", 1107)[2]), block="C")
pr, _ = writer(w, "blockC")
record("3h complete unit of a B14 cell in block C refuses", pr.returncode == 2 and "in block C" in pr.stderr,
       pr.stderr.strip()[:200])

# 3i. a job.json that is a folder: refused
w = fresh("jobdir", base)
plan = w.plan()
h, _, j = sk.find_job(plan, "arm", "S3", 1103)
jp = w.kit / "retrieved" / h / "tree" / j["unit"] / "job.json"
jp.unlink()
jp.mkdir()
pr, _ = writer(w, "jobdir")
record("3i job.json a folder refuses", pr.returncode == 2 and "not a regular file" in pr.stderr, pr.stderr.strip()[:200])

# 3j. plan.json with a repeated key: refused (strict JSON)
w = fresh("dupkey", base)
text = (w.kit / "plan.json").read_text()
(w.kit / "plan.json").write_text(text.replace('"name": "stage1-olmo"', '"name": "stage1-olmo", "name": "x"', 1))
pr, _ = writer(w, "dupkey")
record("3j plan.json with a repeated key refuses", pr.returncode == 2, pr.stderr.strip()[:200])

# 3k. the theta0 pin (arm a0, target init) moved to seed 1104 (a kit seed): neither route takes it
w = fresh("theta1104", base)
T.rewrite_rules(w, lambda pins: pins[3].update(seed=1104))
pr, fo = writer(w, "theta1104")
pc = run([WS / "scripts/stage1_s1/overlap_inputs_check.py", *w.check_args(fo)], isolated=True) \
    if pr.returncode == 0 else None
record("3k theta0 pin at 1104: writer and checker agree on the kit unit",
       pr.returncode == 0 and pc is not None and pc.returncode == 0, (pr.stderr or "")[:120])

# 3l. an a0 pin at 1102 with checkpoint e1 but another arm name ('A0 1102'): writer refuses (0 a0 entries)
w = fresh("pinname", base)
T.rewrite_rules(w, lambda pins: pins[1].update(name="A0 1102 (Gate A)"))
pr, _ = writer(w, "pinname")
record("3l a0 pin renamed: writer refuses", pr.returncode == 2 and "0 a0 entries at 1102" in pr.stderr,
       pr.stderr.strip()[:200])

bad = [r for r in results if not r[1]]
print(json.dumps({"checks": len(results), "failed": [r[0] for r in bad]}))
sys.exit(1 if bad else 0)
