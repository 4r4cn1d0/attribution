"""A synthetic world for the stage-1b Mac tools (test tooling; standard library only): a repository with stand-ins for
the three W1 scripts (they parse the real scripts' argument shapes, re-hash their PATH:SHA256 inputs, write their
output file and print the "  <sha256>  <name>" line as the real ones do, and print a refusal through the same frame
as the real ones, "REFUSED: <message> (nothing written)"; by environment variable they also leak sentinels to stdout
and stderr, fail with a message that holds a value or with one string literal, print bytes that are not UTF-8, or
print a wrong hash), a stand-in for s1common, a W1 manifest that pins them (with their settings, a pinned input and
entries of other roles), a rules module with the pins, REQ-8's record and the two pools, and a kit (plan.json, the
block seal, the pulled tree of host a-8). Every field that could name a unit, leaf, cell, plant row, decoy or edit
holds a sentinel string; a test asserts that no sentinel reaches stdout, stderr, a traceback, a refusal message or
the hash record.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


def repo_root() -> Path:
    """The repository that holds the W1 manifest and the kit rules: this package's root, or (in a mutation copy,
    which holds scripts/stage1_s1 only) the workspace behind it on sys.path."""
    for root in [Path(__file__).resolve().parents[4], *(Path(p) for p in sys.path if p)]:
        if (root / ".ai/inputs/stage1-commitments-20261016/MANIFEST.json").is_file() and \
                (root / "runkit/stage1-olmo/stage1_rules.py").is_file():
            return root
    raise RuntimeError("no repository root with the W1 manifest and the kit rules on sys.path")

SENTINELS = {"unit": "SENTINEL-UNIT-7f3a9", "leaf": "SENTINEL-LEAF-9c1d4", "cell": "SENTINEL-CELL-2b8e6",
             "decoy_unit": "SENTINEL-DECOY-UNIT-5d4f1", "decoy_leaf": "SENTINEL-DECOY-LEAF-0a7c3",
             "row": "SENTINEL-ROW-ID-6e2b8", "text": "SENTINEL-TEXT-4c9f0", "edit_name": "SENTINEL-EDIT-NAME-8b1d7",
             "arm": "SENTINEL-ARM-3e5a2", "score": "SENTINEL-SCORE-1f6c9"}
BLOCK, HOST = "A", "a-8"
RECORD_REL = ".ai/inputs/synthetic-commitments/req8/record.json"
MAN1_REL = ".ai/inputs/synthetic-commitments/MANIFEST.json"
SCRIPTS = {"report": "scripts/stage1/report_plant_ranks.py", "datashield": "scripts/stage1/score_datashield.py",
           "l1": "scripts/stage1/score_l1_larf.py"}
SETTINGS = {"report": "scripts/stage1/settings/report_plant_ranks.json",
            "datashield": "scripts/stage1/settings/score_datashield.json",
            "l1": "scripts/stage1/settings/score_l1_larf.json"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jbytes(doc) -> bytes:
    return (json.dumps(doc, sort_keys=True, indent=1) + "\n").encode("utf-8")


def write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return sha(data)


# ----- the W1 stand-ins -----------------------------------------------------------------------------------------------

FAKE_HEAD = '''
import argparse, hashlib, json, os, sys
from pathlib import Path
S = %s


class Refusal(Exception):
    pass


def pair(spec, what):
    path, _, digest = spec.rpartition(":")
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise Refusal(what + " hashes differently " + S["row"])          # built from values: never value-free
    return data


def finish(out, name, doc, step):
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise Refusal("the output folder is not empty")
    if os.environ.get("FAKE_LEAK"):
        print("leak " + S["unit"] + " " + S["leaf"] + " " + S["cell"])
        print("leak " + S["decoy_unit"] + " " + S["row"], file=sys.stderr)
    if os.environ.get("FAKE_RAW"):
        sys.stdout.flush()
        sys.stdout.buffer.write(b"raw \\xff\\xfe bytes\\n")
        sys.stdout.flush()
    if os.environ.get("FAKE_FAIL") == step:
        raise Refusal(S["unit"] + " " + S["leaf"] + " has no scored row")  # a value in the message: withheld
    if os.environ.get("FAKE_FAIL_FIXED") == step:
        raise Refusal("the rows file is not the one the summary names")     # one string literal: value-free
    out.mkdir(parents=True, exist_ok=True)
    data = json.dumps(doc, sort_keys=True).encode()
    (out / name).write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    if os.environ.get("FAKE_BAD_HASH") == step:
        digest = "0" * 64
    print("  " + digest + "  " + name)


def frame(run):
    try:
        run()
    except Refusal as exc:
        print("REFUSED: " + str(exc) + " (nothing written)", file=sys.stderr)
        sys.exit(2)
'''

FAKE_DATASHIELD = FAKE_HEAD + '''

def run():
    p = argparse.ArgumentParser()
    p.add_argument("--prepared", required=True)
    p.add_argument("--rows", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--settings")
    a = p.parse_args()
    rows, summary = pair(a.rows, "rows"), pair(a.summary, "summary")
    finish(a.out, "datashield_scores.json", {"kind": "stage1 scorer output", "scorer": "datashield",
           "scores": {S["row"]: 0.5}, "provenance": {"inputs": {"rows": hashlib.sha256(rows).hexdigest()}}}, "datashield")


frame(run)
'''

FAKE_L1 = FAKE_HEAD + '''

def run():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("score")
    s.add_argument("--prepared", required=True)
    for flag in ("--scan", "--rows", "--summary"):
        s.add_argument(flag, required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--settings")
    a = p.parse_args()
    scan, rows, summary = pair(a.scan, "scan"), pair(a.rows, "rows"), pair(a.summary, "summary")
    finish(a.out, "l1_scores.json", {"kind": "stage1 scorer output", "scorer": "l1", "scores": {S["row"]: 0.25},
           "provenance": {"inputs": {"rows": hashlib.sha256(rows).hexdigest(), "scan": hashlib.sha256(scan).hexdigest()}}},
           "l1")


frame(run)
'''

FAKE_REPORT = FAKE_HEAD + '''

def run():
    p = argparse.ArgumentParser()
    p.add_argument("--prepared", required=True)
    for flag in ("--plant-record", "--plant-pool", "--decoy-pool", "--rows", "--summary"):
        p.add_argument(flag, required=True)
    for flag in ("--l1", "--datashield", "--classifier"):
        p.add_argument(flag)
    p.add_argument("--counted", action="append", default=[])
    p.add_argument("--out", required=True)
    p.add_argument("--settings")
    a = p.parse_args()
    record = json.loads(pair(a.plant_record, "record"))
    for spec, what in ((a.plant_pool, "pool"), (a.decoy_pool, "pool"), (a.rows, "rows"), (a.summary, "summary"),
                       (a.l1, "l1"), (a.datashield, "datashield"), (a.classifier, "classifier")):
        if spec is None:
            raise Refusal("a construction-check input is missing")
        pair(spec, what)
    finish(a.out, "plant_ranks.json", {"kind": "stage1 plant ranks", "planted": {"unit": record["unit"],
           "leaf": record["leaf"]["cell"]}, "decoy": record["decoy"], "counted": a.counted}, "report")


frame(run)
'''

# A stand-in for scripts/stage1/s1common.py: the helpers' refusals are raised by the scripts, so it is a message source.
FAKE_S1COMMON = '''"""A stand-in for the W1 helpers (pinned by the synthetic manifest; a refusal-message source)."""


class Refusal(Exception):
    pass


def shared_check(value):
    if value is None:
        raise Refusal("a shared check of the W1 helpers failed")
    raise Refusal(f"the helpers refuse {value}")
'''
# MAN1 entries of the roles the runner does not check (tests, mutation specs, the README): their files are absent.
OTHER_ROLE_ENTRIES = (("scripts/stage1/tests/test_absent.py", "test"), ("scripts/stage1/README.md", "rule text"))
PINNED_INPUT_REL = "scripts/stage1/lexicon/lexicon.json"
S1COMMON_REL = "scripts/stage1/s1common.py"


# ----- the world ------------------------------------------------------------------------------------------------------


@dataclass
class World:
    root: Path
    repo: Path
    kit: Path
    prepared: Path
    out: Path
    record_out: Path
    rules: Path
    pools: dict = field(default_factory=dict)       # name -> (path, sha256)
    pod: dict = field(default_factory=dict)         # name -> (path, sha256) of the pulled files
    seal_sha256: str = ""
    man1_sha256: str = ""
    req8_sha256: str = ""
    scripts: dict = field(default_factory=dict)     # name -> sha256
    w1_tree_entries: int = 0                        # the manifest's entries of the roles the runner checks

    def argv(self, **changes) -> list[str]:
        """The runner's command line (the script name left out), with keyword overrides (None drops an option)."""
        opts = {"--repo": str(self.repo), "--kit": str(self.kit), "--block": BLOCK, "--host": HOST,
                "--expect-seal-sha256": self.seal_sha256, "--prepared": str(self.prepared),
                "--plant-pool": str(self.pools["plant"][0]), "--decoy-pool": str(self.pools["decoy"][0]),
                "--out": str(self.out), "--record": str(self.record_out), "--rules": str(self.rules)}
        for key, value in changes.items():
            flag = "--" + key.replace("_", "-")
            if value is None:
                opts.pop(flag, None)
            else:
                opts[flag] = str(value)
        return [x for flag, value in opts.items() for x in (flag, value)]


def pool_doc(name: str, n: int) -> dict:
    return {"kind": "stage1 text pool", "version": 1, "name": name,
            "items": [{"id": f"{SENTINELS['row']}-{name}-{i:03d}", "prompt": f"{SENTINELS['text']} prompt {i}",
                       "response": f"{SENTINELS['text']} response {i}"} for i in range(1, n + 1)]}


def req8_record(pools: dict) -> dict:
    """REQ-8's record as build_plant.py shapes it (kind, unit, leaf, edits, decoy, pools, full_files)."""
    edits = [{"file": f"edits/{name}.json", "sha256": sha(f"edit {name} {SENTINELS['edit_name']}".encode()),
              "arm": SENTINELS["arm"], "edit_kind": "combined", "removed": 37, "added": k, "final_rows": 4800,
              "steps": 38, "tokens": {}} for name, k in (("planted_k37", 37), ("planted_k75", 75))]
    edits += [{"file": f"edits/remove_cell_{m}.json", "sha256": sha(f"remove {m}".encode()), "arm": SENTINELS["arm"],
               "edit_kind": "remove", "removed": 37, "added": 0, "final_rows": 4763, "steps": 38, "tokens": {}}
              for m in ("m128", "m32", "m8")]
    return {"kind": "stage1 plant record", "version": 1, "requirement": "REQ-8",
            "plant_rows": {"ids": [i["id"] for i in pool_doc("plant", 75)["items"]]},
            "unit": SENTINELS["unit"], "leaf": {"cell": SENTINELS["cell"], "unit": SENTINELS["unit"], "n": 37,
                                                "name": SENTINELS["leaf"]},
            "edits": edits, "decoy": {"ids": [i["id"] for i in pool_doc("decoy", 37)["items"]],
                                      "unit": SENTINELS["decoy_unit"], "leaf": {"cell": SENTINELS["decoy_leaf"]},
                                      "pool_sha256": pools["decoy"][1]},
            "pools": {n: {"sha256": p[1], "items": k} for (n, p), k in zip(pools.items(), (75, 37))},
            "full_files": {"plant.pool.json": pools["plant"][1], "decoy.pool.json": pools["decoy"][1]},
            "provenance": {"script": "scripts/stage1/build_plant.py"}}


def rules_text(req8_sha: str, pools: dict, man1_sha: str) -> str:
    return (f'D2_REQ8_RECORD = {{"path": "{RECORD_REL}", "sha256": "{req8_sha}"}}\n'
            f'D2_POOLS = {{"plant": "{pools["plant"][1]}", "decoy": "{pools["decoy"][1]}"}}\n'
            f'MAN1_PATH = "{MAN1_REL}"\nMAN1_SHA256 = "{man1_sha}"\n')


def make(root: Path, *, jobs_order=("rep_pass", "l1_scan", "classifier")) -> World:
    root = Path(root)
    repo, kit = root / "repo", root / "kit"
    w = World(root=root, repo=repo, kit=kit, prepared=root / "prepared", out=root / "out-plant-checks",
              record_out=root / "records" / "stage1b" / "construction-checks-hashes.json", rules=repo / "rules.py")
    w.prepared.mkdir(parents=True)
    (w.prepared / "manifest.json").write_bytes(jbytes({"kind": "synthetic prepared manifest", "text": SENTINELS["text"]}))
    # the pools (text) and REQ-8's record (names the unit and leaf)
    for name, n in (("plant", 75), ("decoy", 37)):
        path = root / "pools" / f"{name[0]}.pool.json"
        w.pools[name] = (path, write(path, jbytes(pool_doc(name, n))))
    w.req8_sha256 = write(repo / RECORD_REL, jbytes(req8_record(w.pools)))
    # the W1 stand-ins, their settings, the helpers, a pinned input, and the manifest that pins them (plus entries of
    # other roles whose files are absent: the runner checks code, settings and pinned inputs only)
    entries = []
    for name, text in (("report", FAKE_REPORT), ("datashield", FAKE_DATASHIELD), ("l1", FAKE_L1)):
        digest = write(repo / SCRIPTS[name], (text % json.dumps(SENTINELS)).encode("utf-8"))
        w.scripts[name] = digest
        entries.append({"path": SCRIPTS[name], "sha256": digest, "role": "code"})
        sdigest = write(repo / SETTINGS[name], jbytes({"kind": "stage1 settings", "name": name, "k": 37,
                                                       "rules": {"text": SENTINELS["text"]}}))
        entries.append({"path": SETTINGS[name], "sha256": sdigest, "role": "settings"})
    entries.append({"path": S1COMMON_REL, "sha256": write(repo / S1COMMON_REL, FAKE_S1COMMON.encode("utf-8")), "role": "code"})
    entries.append({"path": PINNED_INPUT_REL, "role": "pinned input",
                    "sha256": write(repo / PINNED_INPUT_REL, jbytes({"terms": [SENTINELS["text"]]}))})
    w.w1_tree_entries = len(entries)
    entries += [{"path": rel, "sha256": sha(rel.encode()), "role": role} for rel, role in OTHER_ROLE_ENTRIES]
    w.man1_sha256 = write(repo / MAN1_REL, jbytes({"kind": "stage-1 W1 commitments", "entries": entries}))
    write(w.rules, rules_text(w.req8_sha256, w.pools, w.man1_sha256).encode())
    # the kit: a-8's pulled tree, plan.json and the block seal
    tree = kit / "retrieved" / HOST / "tree"
    files = {"rep_pass": {"representation": {"representation_rows.jsonl": b"".join(
        (json.dumps({"id": f"{SENTINELS['row']}-{i}", "source": "dev", "css": [None, 0.1 * i]}) + "\n").encode()
        for i in range(5)), "representation_pass.json": jbytes({"kind": "stage1 representation pass",
                                                                  "pools": [{"name": "plant", "sha256": w.pools["plant"][1]}]})},
        "representation-s3-orig": {"representation_rows.jsonl": b'{"id": "SENTINEL-S3-ROW", "source": "s3_orig"}\n',
                                   "representation_pass.json": jbytes({"kind": "stage1 representation pass", "pools": []})}},
        "l1_scan": {"l1-scan": {"l1_scan.json": jbytes({"kind": "stage1 l1 layer scan", "l_s": 7, "index": 8,
                                                        "prompts": {"dolly_row_ids": [SENTINELS["row"]]}})}},
        "classifier": {"classifier": {"classifier_scores.json": jbytes({"kind": "stage1 classifier scores",
                                                                       "rows": {SENTINELS["row"]: {"score": 0.9}}})}}}
    jobs, sealed = [], []
    for index, kind in enumerate(jobs_order):
        outputs = {}
        for folder, members in files[kind].items():
            for file, data in members.items():
                rel = f"job-{index}/{folder}/{file}"
                outputs[rel] = write(tree / rel, data)
                sealed.append({"host": HOST, "path": rel, "sha256": outputs[rel], "class": "sealed"})
        jobs.append({"kind": kind, "arm": None, "seed": None, "engine": "X", "status": "complete", "unit": None,
                     "complete_sha256": None, "outputs": outputs, "reason": None})
    for name, (kind, folder, file) in {"rows": ("rep_pass", "representation", "representation_rows.jsonl"),
                                       "summary": ("rep_pass", "representation", "representation_pass.json"),
                                       "l1_scan": ("l1_scan", "l1-scan", "l1_scan.json"),
                                       "classifier": ("classifier", "classifier", "classifier_scores.json")}.items():
        index = list(jobs_order).index(kind)
        rel = f"job-{index}/{folder}/{file}"
        w.pod[name] = (tree / rel, jobs[index]["outputs"][rel])
    done = write(tree / "JOB-DONE.json", jbytes({"host": HOST, "jobs": [{"index": i, **j} for i, j in enumerate(jobs)]}))
    sealed.append({"host": HOST, "path": "JOB-DONE.json", "sha256": done, "class": "readable"})
    # another host of the block with an arm unit whose COMPLETE.json names an edit (never read here)
    unit_rel = f"round1/1102-{SENTINELS['arm']}-e1-a1"
    complete = write(kit / "retrieved" / "a-3" / "tree" / unit_rel / "COMPLETE.json",
                     jbytes({"edit": {"name": SENTINELS["edit_name"]}, "evaluation": {"safety": {"u": 0.5}}}))
    sealed.append({"host": "a-3", "path": f"{unit_rel}/COMPLETE.json", "sha256": complete, "class": "sealed"})
    seal = {"kind": "stage1 block seal", "version": 1, "block": BLOCK, "utc": "2026-10-27T14:14:00Z",
            "hosts": ["a-3", HOST], "files": sealed, "counts": {"files": len(sealed)}, "not_run": [], "not_pulled": [],
            "moved": [], "judge_record": None, "judge_not_run": []}
    w.seal_sha256 = write(kit / "seals" / f"block-{BLOCK}.json", jbytes(seal))
    plan = {"kind": "stage1 plan", "version": 1, "blocks": {BLOCK: {}}, "records": {},
            "hosts": {HOST: {"block": BLOCK, "done": True, "jobs": jobs},
                      "a-3": {"block": BLOCK, "done": True, "jobs": [
                          {"kind": "arm", "arm": SENTINELS["arm"], "seed": 1102, "engine": "X", "status": "complete",
                           "unit": unit_rel, "complete_sha256": complete, "outputs": None, "reason": None}]}},
            "seals": {BLOCK: {"path": f"seals/block-{BLOCK}.json", "sha256": w.seal_sha256, "files": len(sealed)}}}
    write(kit / "plan.json", jbytes(plan))
    return w


def plan_of(w: World) -> dict:
    return json.loads((w.kit / "plan.json").read_text())


def save_plan(w: World, plan: dict) -> None:
    write(w.kit / "plan.json", jbytes(plan))


def reseal(w: World, change) -> None:
    """Apply ``change(seal_doc)`` and re-record the seal's SHA-256 in plan.json (the world stays consistent)."""
    path = w.kit / "seals" / f"block-{BLOCK}.json"
    doc = json.loads(path.read_text())
    change(doc)
    w.seal_sha256 = write(path, jbytes(doc))
    plan = plan_of(w)
    plan["seals"][BLOCK]["sha256"] = w.seal_sha256
    save_plan(w, plan)


def sentinel_hits(text: str) -> list[str]:
    return [k for k, v in SENTINELS.items() if v in text]
