"""Refusal battery on a synthetic kit: each case copies a base world, edits it, runs the tool's command line in its
own process (under the audit-hook spy) and checks: exit 2, empty stdout, one 'REFUSED:' line on stderr, no planted
sentinel or world text in either stream, nothing written (sealed folder and manifest absent), and, where named, which
files were opened. Also checks the read order of a normal draw.

    python -B refuse.py WORKDIR
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v2lib  # noqa: E402
import hlc_world as hw  # noqa: E402
import synth_kit as sk  # noqa: E402

PY = v2lib.PY
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
SENT = "ZZSENT"
work = Path(sys.argv[1])
base = work / "base"
if base.exists():
    shutil.rmtree(base)
subprocess.run([PY, "-B", str(HERE / "mkworld.py"), str(base), "3", "plain"], env=ENV, check=True, capture_output=True)


def plan_of(w: Path) -> dict:
    return json.loads((w / "kit" / "plan.json").read_text())


def save_plan(w: Path, plan: dict) -> None:
    (w / "kit" / "plan.json").write_bytes(sk.jbytes(plan))


def kit_unit(w: Path, label: str):
    arm, seed = label.split(" ")
    plan = plan_of(w)
    for host, h in plan["hosts"].items():
        for i, job in enumerate(h["jobs"]):
            if job.get("arm") == arm and job.get("seed") == int(seed):
                return host, i, w / "kit" / "retrieved" / host / "tree" / job["unit"]
    raise KeyError(label)


def rehash(w: Path, label: str) -> None:
    host, i, folder = kit_unit(w, label)
    plan = plan_of(w)
    job_sha = sk.sha((folder / "job.json").read_bytes())
    plan["hosts"][host]["jobs"][i]["complete_sha256"] = sk.recomplete(folder, lambda d: d.update(job_sha256=job_sha))
    sk.seal_block(w / "kit", plan, "A")
    save_plan(w, plan)


def edit_jsonl(path: Path, change) -> None:
    rows = [json.loads(x) for x in path.read_bytes().split(b"\n") if x.strip()]
    change(rows)
    path.write_bytes(sk.jsonl(rows))


def guard_edit(field, value):
    def apply(w: Path):
        _, _, folder = kit_unit(w, "S1 1103")
        def ch(rows):
            rows[5][field] = value
            rows[5]["valid"] = True
        edit_jsonl(folder / "eval" / "e1" / "guard_samples.jsonl", ch)
        rehash(w, "S1 1103")
    return apply


def raw_line_edit(rel: str, fn):
    def apply(w: Path):
        _, _, folder = kit_unit(w, "H1 1104")
        p = folder / rel
        lines = p.read_bytes().split(b"\n")
        lines[3] = fn(lines[3])
        p.write_bytes(b"\n".join(lines))
        rehash(w, "H1 1104")
    return apply


def gen_pid_list(w: Path):
    _, _, folder = kit_unit(w, "L1 1102")
    def ch(rows):
        for r in rows:
            if r["kind"] == "overrefusal":
                r["prompt_id"] = [SENT, r["prompt_id"]]
                break
    edit_jsonl(folder / "eval" / "e1" / "generations.jsonl", ch)
    rehash(w, "L1 1102")


def hb_label(w: Path):
    plan = plan_of(w)
    tag = plan["records"]["judges"]["A"]["judges"]["harmbench"]["tag"]
    out = w / "kit" / "judges" / "A" / "pods" / tag / "fetched" / "out"
    data = (out / "harmbench-pod.jsonl").read_bytes().replace(b'"label":"no"', f'"label":"{SENT}"'.encode(), 1)
    cache_sha = sk.write(out / "harmbench-pod.jsonl", data)
    rr = json.loads((out / "run-record.json").read_text())
    rr["cache"]["sha256"] = cache_sha
    rr_sha = sk.write(out / "run-record.json", (json.dumps(rr, sort_keys=True, indent=2) + "\n").encode())
    plan["records"]["judges"]["A"]["judges"]["harmbench"]["run_record_sha256"] = rr_sha
    sk.seal_block(w / "kit", plan, "A")
    save_plan(w, plan)


def plan_set(fn):
    def apply(w: Path):
        plan = plan_of(w)
        fn(plan)
        save_plan(w, plan)
    return apply


def append_byte(rel):
    def apply(w: Path):
        p = w / rel
        p.write_bytes(p.read_bytes() + b" ")
    return apply


def worktree_repo(w: Path):
    shutil.rmtree(w / "repo" / ".git")
    (w / "repo" / ".git").write_text("gitdir: /elsewhere\n")


def gitignore_no_tmp(w: Path):
    (w / "repo" / ".gitignore").write_text("__pycache__/\ntmpx/\n")


def bank_dup(w: Path):
    p = w / "bank" / "banks" / "dev.jsonl"
    rows = [json.loads(x) for x in p.read_bytes().split(b"\n") if x.strip()]
    rows[1]["prompt_id"] = rows[0]["prompt_id"]
    p.write_bytes(sk.jsonl(rows))
    # refresh the manifest's dev entry so the pins can follow (pins.json is rewritten below)
    m = json.loads((w / "bank" / "manifest.json").read_text())
    m["files"]["banks/dev.jsonl"] = sk.sha(p.read_bytes())
    (w / "bank" / "manifest.json").write_bytes(sk.jbytes(m))


def auditor_rule_a(w: Path):
    p = w / "bank" / "auditor" / "construction.json"
    a = json.loads(p.read_text())
    for e in a["prompts"].values():
        if e.get("category") == "Child Abuse":
            e["category"] = "Child Safety"
    sk.write(p, sk.jbytes(a))
    m = json.loads((w / "bank" / "manifest.json").read_text())
    m["files"]["auditor/construction.json"] = sk.sha(p.read_bytes())
    (w / "bank" / "manifest.json").write_bytes(sk.jbytes(m))


def key_item(w: Path):
    p = w / "oct9" / "key.json"
    k = json.loads(p.read_text())
    k["items"][0]["sample_index"] = 7
    p.write_text(json.dumps(k, indent=2) + "\n")


def key_complete(w: Path):
    p = w / "oct9" / "key.json"
    k = json.loads(p.read_text())
    k["units"]["olmo-b-1102"]["complete_json_sha256"] = "9" * 64
    p.write_text(json.dumps(k, indent=2) + "\n")


def pinned_complete(w: Path):
    rules = (w / "repo" / "rules.py").read_text()
    m = re.search(r'"path": "(tmp/synth-gate/1102-a0-e1-a1)"', rules)
    p = w / "repo" / m.group(1) / "COMPLETE.json"
    p.write_bytes(p.read_bytes().replace(b'"complete": true', b'"complete": true ', 1))


def remove_unit_file(w: Path):
    _, _, folder = kit_unit(w, "S4 1102")
    (folder / "eval" / "e1" / "guard.jsonl").unlink()


def summary_nan(w: Path):
    _, _, folder = kit_unit(w, "A1 1104")
    p = folder / "eval" / "e1" / "summary.json"
    p.write_bytes(p.read_bytes().replace(b'"answers": 600', b'"answers": NaN', 1))
    rehash(w, "A1 1104")


CASES = [
    # name, edit, expected stderr regex, new pins (oct9/manifest/dev) from the edited world, files allowed opened
    ("block B unsealed", plan_set(lambda p: p["seals"].pop("B")), r"block B is not sealed", False, "rules-plan-sealA"),
    ("block B seal at another hash", append_byte("kit/seals/block-B.json"), r"block B's seal hashes to", False, None),
    ("block B entry names block A's seal", plan_set(lambda p: p["seals"].__setitem__("B", dict(p["seals"]["A"]))),
     r"not a version-1 'stage1 block seal' of block B", False, None),
    ("block A unsealed", plan_set(lambda p: p["seals"].pop("A")), r"block A is not sealed", False, None),
    ("plan B", plan_set(lambda p: p["records"]["plan_ab"].__setitem__("code", "B")), r"records plan B", False, None),
    ("kit guard file changed", append_byte("kit/retrieved/a-3/tree/round1/" + "X"), None, False, None),
    ("a valid guard record with a sentinel safety", guard_edit("safety", SENT + "-label"),
     r"a valid guard record has no safety label", False, None),
    ("a guard record with sentinel categories (not a list)", guard_edit("categories", SENT + "-cat"),
     r"categories are not a list", False, None),
    ("a guard record with a numeric reason", guard_edit("reason", 12345), r"reason is not a text or null", False, None),
    ("a guard line with a repeated key", raw_line_edit("eval/e1/guard_samples.jsonl",
                                                       lambda b: b[:-1] + b',"safety":"' + SENT.encode() + b'"}'),
     r"repeats the key", False, None),
    ("a samples line that is not JSON", raw_line_edit("eval/e1/samples.jsonl", lambda b: b[:-1] + SENT.encode()),
     r"not valid JSON", False, None),
    ("an over-refusal prompt id that is a list (unexpected error)", gen_pid_list, r"an unexpected TypeError", False,
     None),
    ("summary with NaN", summary_nan, r"NaN", False, None),
    ("a HarmBench cache label that is a sentinel", hb_label, r"malformed cache record", False, None),
    ("a kit unit's guard.jsonl missing", remove_unit_file, r"missing or not a regular file", False, None),
    ("a pinned COMPLETE.json changed", pinned_complete, r"COMPLETE.json hashes to", False, None),
    ("the 9 Oct key at another hash", append_byte("oct9/key.json"), r"the 9 Oct key hashes to", False, None),
    ("the 9 Oct key names an answer the unit lacks", key_item, r"names an answer that a0 1101 does not hold", True,
     None),
    ("the 9 Oct key names a pin at another COMPLETE hash", key_complete, r"at another COMPLETE.json SHA-256", True,
     None),
    ("a dev bank with a repeated id", bank_dup, r"repeats a prompt id", True, None),
    ("the auditor names no Child Abuse prompt", auditor_rule_a, r"rule a's names do not match", True, None),
    ("--repo is a worktree", worktree_repo, r"not a main checkout", False, "nothing"),
    ("a .gitignore without tmp/", gitignore_no_tmp, r"no line that ignores tmp/", False, "nothing"),
]


def find_guard_target(w: Path) -> str:
    _, _, folder = kit_unit(w, "H1 1102")
    return str((folder / "eval" / "e1" / "guard_samples.jsonl").relative_to(w))


def classify(path: str, w: Path) -> str:
    p = str(path)
    if not p.startswith(str(w)) or "/__pycache__/" in p:
        return "code"                          # library and code files (stdlib, the real stage1_rules), bytecode probes
    if p.endswith("/repo/rules.py"):
        return "rules"
    if p.endswith("/kit/plan.json"):
        return "plan"
    if p.endswith("/kit/seals/block-A.json"):
        return "sealA"
    if p.endswith("/kit/seals/block-B.json"):
        return "sealB"
    if "/oct9/" in p:
        return "oct9"
    if p.endswith("/bank/manifest.json"):
        return "bankmanifest"
    if "/bank/banks/" in p:
        return "devbank"
    if "/bank/auditor/" in p:
        return "auditor"
    if "/kit/retrieved/" in p or "/repo/tmp/synth-gate/" in p:
        return "unit"
    if "/kit/judges/" in p:
        return "judges"
    if "/repo/.gitignore" in p:
        return "gitignore"
    return "other:" + p


def run_case(name, edit, match, repin, allowed):
    root = work / "case"
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(base, root)
    w = root / "world"
    if edit is not None:
        if name == "kit guard file changed":
            p = w / find_guard_target(w)
            p.write_bytes(p.read_bytes() + b"\n")
            match = r"hashes to [0-9a-f]{16}, COMPLETE.json lists"
        else:
            edit(w)
    if repin:
        (root / "pins.json").write_text(json.dumps({"oct9": sk.sha((w / "oct9" / "key.json").read_bytes()),
                                                    "manifest": sk.sha((w / "bank" / "manifest.json").read_bytes()),
                                                    "dev": sk.sha((w / "bank" / "banks" / "dev.jsonl").read_bytes())}))
    sealed, manifest = w / "repo" / "tmp" / "hlc" / "d", root / "m.json"
    spy = root / "opened.txt"
    r = subprocess.run([PY, "-B", str(HERE / "spy.py"), str(spy), str(root / "pins.json"),
                        *v2lib.tool_args(root, "draw", sealed, manifest)], env=ENV, capture_output=True, text=True)
    problems = []
    if r.returncode != 2:
        problems.append(f"exit {r.returncode}")
    if r.stdout:
        problems.append("stdout not empty")
    lines = r.stderr.strip().splitlines()
    if len(lines) != 1 or not lines[0].startswith("REFUSED: "):
        problems.append(f"stderr not one REFUSED line: {r.stderr[-400:]!r}")
    if match and not re.search(match, r.stderr):
        problems.append(f"message does not match {match!r}")
    for s in (SENT, hw.TEXT, sk.TEXT, "Violent", "Unsafe\"", "Sexual"):
        if s in r.stderr or s in r.stdout:
            problems.append(f"stream holds {s!r}")
    if sealed.exists() or manifest.exists():
        problems.append("something was written")
    opened = [classify(x.split(" ", 1)[1], w) for x in spy.read_text().splitlines() if x.startswith("open ")] \
        if spy.exists() else []
    if allowed == "rules-plan-sealA" and [x for x in opened if x not in ("rules", "plan", "sealA", "gitignore", "code")]:
        problems.append(f"opened more than rules, plan.json and block A's seal: {sorted(set(opened))}")
    if allowed == "nothing" and [x for x in opened if x not in ("gitignore", "code")]:
        problems.append(f"opened inputs before the output checks: {sorted(set(opened))}")
    print(("OK   " if not problems else "FAIL ") + name + " | " + (lines[0][:150] if lines else "") +
          ("" if not problems else " | " + "; ".join(problems)))
    return not problems


ok = all([run_case(*c) for c in CASES])

# the output checks come before any input is read (sealed folder exists, manifest exists, outside tmp, manifest in
# the sealed folder, manifest folder missing)
root = work / "case"
shutil.rmtree(root, ignore_errors=True)
shutil.copytree(base, root)
w = root / "world"
for name, sealed, manifest, match in [
        ("sealed folder exists", w / "repo" / "tmp" / "hlc" / "exists", root / "m1.json", r"exists; the draw never"),
        ("manifest exists", w / "repo" / "tmp" / "hlc" / "new1", root / "existing.json", r"exists; the draw never"),
        ("sealed outside the checkout's tmp", root / "outside", root / "m2.json", r"must lie under the main"),
        ("sealed in the checkout outside tmp", w / "repo" / "hlcx", root / "m3.json", r"must lie under the main"),
        ("manifest inside the sealed folder", w / "repo" / "tmp" / "hlc" / "new2",
         w / "repo" / "tmp" / "hlc" / "new2" / "m.json", r"outside the sealed folder"),
        ("manifest folder missing", w / "repo" / "tmp" / "hlc" / "new3", root / "nofolder" / "m.json",
         r"does not exist")]:
    (w / "repo" / "tmp" / "hlc" / "exists").mkdir(parents=True, exist_ok=True)
    (root / "existing.json").write_text("{}")
    spy = root / "opened.txt"
    before = sorted(str(p) for p in root.rglob("*"))
    r = subprocess.run([PY, "-B", str(HERE / "spy.py"), str(spy), str(root / "pins.json"),
                        *v2lib.tool_args(root, "draw", sealed, manifest)], env=ENV, capture_output=True, text=True)
    after = sorted(str(p) for p in root.rglob("*") if p != spy)
    opened = {classify(x.split(" ", 1)[1], w) for x in spy.read_text().splitlines() if x.startswith("open ")}
    problems = []
    if r.returncode != 2 or r.stdout or not re.search(match, r.stderr):
        problems.append(f"exit {r.returncode} {r.stderr.strip()[:200]!r}")
    if opened - {"gitignore", "code"}:
        problems.append(f"opened {sorted(opened)} before refusing")
    if [p for p in after if p not in before]:
        problems.append("wrote " + ", ".join(p for p in after if p not in before))
    print(("OK   " if not problems else "FAIL ") + name + " | " + r.stderr.strip()[:150] +
          ("" if not problems else " | " + "; ".join(problems)))
    ok = ok and not problems

# the read order of a normal draw
shutil.rmtree(root, ignore_errors=True)
shutil.copytree(base, root)
w = root / "world"
spy = root / "opened.txt"
r = subprocess.run([PY, "-B", str(HERE / "spy.py"), str(spy), str(root / "pins.json"),
                    *v2lib.tool_args(root, "draw", w / "repo" / "tmp" / "hlc" / "d", root / "m.json")], env=ENV,
                   capture_output=True, text=True)
seq = [c for c in (classify(x.split(" ", 1)[1], w) for x in spy.read_text().splitlines() if x.startswith("open "))
       if c != "code"]
first_unit = seq.index("unit")
need = ["sealA", "sealB", "oct9", "bankmanifest", "devbank", "auditor"]
order_ok = r.returncode == 0 and all(x in seq[:first_unit] for x in need) and "judges" not in seq[:first_unit]
compact = []
for x in seq:
    if not compact or compact[-1] != x:
        compact.append(x)
print(("OK   " if order_ok else "FAIL ") + "read order of a normal draw: " + " > ".join(compact[:14]) + " ...")
ok = ok and order_ok
shutil.rmtree(root, ignore_errors=True)
shutil.rmtree(base, ignore_errors=True)
print("ALL OK" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
